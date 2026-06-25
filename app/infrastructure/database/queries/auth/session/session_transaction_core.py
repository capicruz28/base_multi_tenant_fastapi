"""
Transacciones atómicas IAM Session V3 (C18).

Coordina C15 + C16 + C17 dentro de UnitOfWork. Sin reglas de negocio.
Único lugar con UPDLOCK en rotación de refresh token.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, func, insert, select, update

from app.core.application.unit_of_work import UnitOfWork
from app.infrastructure.database.queries.auth.session import (
    refresh_token_queries_core as rtq,
    token_family_queries_core as tfq,
    user_session_queries_core as usq,
)
from app.infrastructure.database.tables import (
    RefreshTokensTable,
    TokenFamilyTable,
    UserSessionTable,
)

logger = logging.getLogger(__name__)

SQL_LOCK_REFRESH_TOKEN_BY_HASH_V3 = """
SELECT
    token_id,
    family_id,
    session_id,
    usuario_id,
    token_hash,
    expires_at,
    is_used,
    is_revoked,
    parent_token_id,
    cliente_id,
    empresa_id
FROM refresh_tokens WITH (UPDLOCK, ROWLOCK)
WHERE token_hash = :token_hash
  AND cliente_id = :cliente_id
"""

SQL_LOCK_TOKEN_FAMILY_BY_ID = """
SELECT family_id, session_id, is_compromised, cliente_id
FROM token_family WITH (UPDLOCK, ROWLOCK)
WHERE family_id = :family_id
  AND cliente_id = :cliente_id
"""


async def _uow_rows_affected(uow: UnitOfWork, stmt) -> int:
    result = await uow.execute(stmt)
    if isinstance(result, dict):
        return int(result.get("rows_affected", 0))
    return 0


async def _uow_select(uow: UnitOfWork, stmt) -> List[Dict[str, Any]]:
    result = await uow.execute(stmt)
    return result if isinstance(result, list) else []


async def _uow_select_one(uow: UnitOfWork, stmt) -> Optional[Dict[str, Any]]:
    rows = await _uow_select(uow, stmt)
    return rows[0] if rows else None


async def _insert_user_session_uow(
    uow: UnitOfWork,
    *,
    usuario_id: UUID,
    cliente_id: UUID,
    expires_at: datetime,
    platform: str,
    login_method: str = "password",
    selection_token_completed: bool = False,
    empresa_id: Optional[UUID] = None,
    device_name: Optional[str] = None,
    device_id: Optional[str] = None,
    device_fingerprint: Optional[str] = None,
    user_agent: Optional[str] = None,
    login_ip: Optional[str] = None,
    session_id: Optional[UUID] = None,
) -> UUID:
    usq._assert_login_method(login_method)
    usq._assert_platform(platform)
    new_session_id = session_id or uuid4()
    payload = {
        "session_id": new_session_id,
        "usuario_id": usuario_id,
        "cliente_id": cliente_id,
        "empresa_id": empresa_id,
        "login_method": login_method,
        "selection_token_completed": selection_token_completed,
        "platform": platform,
        "device_name": device_name,
        "device_id": device_id,
        "device_fingerprint": device_fingerprint,
        "user_agent": user_agent[:1000] if user_agent else None,
        "login_ip": login_ip,
        "expires_at": expires_at,
        "is_active": True,
    }
    stmt = insert(UserSessionTable).values(
        **{k: v for k, v in payload.items() if k in usq._SESSION_COLUMNS}
    )
    affected = await _uow_rows_affected(uow, stmt)
    if affected != 1:
        raise RuntimeError("INSERT user_session no afectó exactamente 1 fila")
    return new_session_id


async def _insert_token_family_uow(
    uow: UnitOfWork,
    *,
    session_id: UUID,
    usuario_id: UUID,
    cliente_id: UUID,
    family_id: Optional[UUID] = None,
) -> UUID:
    new_family_id = family_id or uuid4()
    payload = {
        "family_id": new_family_id,
        "session_id": session_id,
        "usuario_id": usuario_id,
        "cliente_id": cliente_id,
        "current_token_id": None,
        "is_compromised": False,
    }
    stmt = insert(TokenFamilyTable).values(
        **{k: v for k, v in payload.items() if k in tfq._FAMILY_COLUMNS}
    )
    affected = await _uow_rows_affected(uow, stmt)
    if affected != 1:
        raise RuntimeError("INSERT token_family no afectó exactamente 1 fila")
    return new_family_id


async def _insert_refresh_token_uow(
    uow: UnitOfWork,
    *,
    family_id: UUID,
    session_id: UUID,
    usuario_id: UUID,
    cliente_id: UUID,
    token_hash: str,
    expires_at: datetime,
    parent_token_id: Optional[UUID] = None,
    empresa_id: Optional[UUID] = None,
    token_id: Optional[UUID] = None,
) -> UUID:
    new_token_id = token_id or uuid4()
    payload = {
        "token_id": new_token_id,
        "family_id": family_id,
        "session_id": session_id,
        "parent_token_id": parent_token_id,
        "cliente_id": cliente_id,
        "empresa_id": empresa_id,
        "usuario_id": usuario_id,
        "token_hash": token_hash,
        "expires_at": expires_at,
        "is_used": False,
        "is_revoked": False,
    }
    stmt = insert(RefreshTokensTable).values(
        **{k: v for k, v in payload.items() if k in rtq._TOKEN_COLUMNS}
    )
    affected = await _uow_rows_affected(uow, stmt)
    if affected != 1:
        raise RuntimeError("INSERT refresh_tokens no afectó exactamente 1 fila")
    return new_token_id


async def _update_family_current_token_uow(
    uow: UnitOfWork,
    family_id: UUID,
    cliente_id: UUID,
    *,
    current_token_id: UUID,
) -> int:
    stmt = (
        update(TokenFamilyTable)
        .where(tfq._non_compromised_family_where(family_id, cliente_id))
        .values(current_token_id=current_token_id)
    )
    return await _uow_rows_affected(uow, stmt)


async def _mark_family_compromised_uow(
    uow: UnitOfWork,
    family_id: UUID,
    cliente_id: UUID,
    *,
    invalidation_reason: str,
) -> int:
    tfq._assert_invalidation_reason(invalidation_reason)
    stmt = (
        update(TokenFamilyTable)
        .where(
            and_(
                tfq._tenant_family_where(family_id, cliente_id),
                TokenFamilyTable.c.is_compromised == False,  # noqa: E712
            )
        )
        .values(
            is_compromised=True,
            compromised_at=func.getdate(),
            invalidation_reason=invalidation_reason,
        )
    )
    return await _uow_rows_affected(uow, stmt)


async def _close_session_uow(
    uow: UnitOfWork,
    session_id: UUID,
    cliente_id: UUID,
    *,
    revoked_reason: str,
) -> int:
    usq._assert_session_revoked_reason(revoked_reason)
    stmt = (
        update(UserSessionTable)
        .where(
            and_(
                usq._tenant_session_where(session_id, cliente_id),
                UserSessionTable.c.is_active == True,  # noqa: E712
            )
        )
        .values(
            is_active=False,
            revoked_at=func.getdate(),
            revoked_reason=revoked_reason,
        )
    )
    return await _uow_rows_affected(uow, stmt)


async def _close_all_user_sessions_uow(
    uow: UnitOfWork,
    usuario_id: UUID,
    cliente_id: UUID,
    *,
    revoked_reason: str,
) -> int:
    usq._assert_session_revoked_reason(revoked_reason)
    stmt = (
        update(UserSessionTable)
        .where(usq._active_session_conditions(cliente_id, usuario_id))
        .values(
            is_active=False,
            revoked_at=func.getdate(),
            revoked_reason=revoked_reason,
        )
    )
    return await _uow_rows_affected(uow, stmt)


async def _mark_token_used_uow(
    uow: UnitOfWork,
    token_id: UUID,
    cliente_id: UUID,
) -> int:
    stmt = (
        update(RefreshTokensTable)
        .where(rtq._usable_token_where(token_id, cliente_id))
        .values(
            is_used=True,
            used_at=func.getdate(),
            last_used_at=func.getdate(),
        )
    )
    return await _uow_rows_affected(uow, stmt)


async def _compromise_all_families_for_user_uow(
    uow: UnitOfWork,
    usuario_id: UUID,
    cliente_id: UUID,
    *,
    invalidation_reason: str,
) -> int:
    tfq._assert_invalidation_reason(invalidation_reason)
    stmt = (
        update(TokenFamilyTable)
        .where(
            and_(
                TokenFamilyTable.c.usuario_id == usuario_id,
                TokenFamilyTable.c.cliente_id == cliente_id,
                TokenFamilyTable.c.is_compromised == False,  # noqa: E712
            )
        )
        .values(
            is_compromised=True,
            compromised_at=func.getdate(),
            invalidation_reason=invalidation_reason,
        )
    )
    return await _uow_rows_affected(uow, stmt)


async def _revoke_all_tokens_for_user_uow(
    uow: UnitOfWork,
    usuario_id: UUID,
    cliente_id: UUID,
    *,
    revoked_reason: str,
) -> int:
    rtq._assert_token_revoked_reason(revoked_reason)
    stmt = (
        update(RefreshTokensTable)
        .where(
            and_(
                RefreshTokensTable.c.usuario_id == usuario_id,
                RefreshTokensTable.c.cliente_id == cliente_id,
                RefreshTokensTable.c.is_revoked == False,  # noqa: E712
            )
        )
        .values(
            is_revoked=True,
            revoked_at=func.getdate(),
            revoked_reason=revoked_reason,
        )
    )
    return await _uow_rows_affected(uow, stmt)


async def _revoke_tokens_by_session_uow(
    uow: UnitOfWork,
    session_id: UUID,
    cliente_id: UUID,
    *,
    revoked_reason: str,
) -> int:
    rtq._assert_token_revoked_reason(revoked_reason)
    stmt = (
        update(RefreshTokensTable)
        .where(
            and_(
                RefreshTokensTable.c.session_id == session_id,
                RefreshTokensTable.c.cliente_id == cliente_id,
                RefreshTokensTable.c.is_revoked == False,  # noqa: E712
            )
        )
        .values(
            is_revoked=True,
            revoked_at=func.getdate(),
            revoked_reason=revoked_reason,
        )
    )
    return await _uow_rows_affected(uow, stmt)


async def _update_session_on_refresh_uow(
    uow: UnitOfWork,
    session_id: UUID,
    cliente_id: UUID,
    *,
    last_seen_ip: Optional[str] = None,
    empresa_id: Optional[UUID] = None,
) -> int:
    values: Dict[str, Any] = {"last_refresh_at": func.getdate()}
    if last_seen_ip is not None:
        values["last_seen_ip"] = last_seen_ip
    if empresa_id is not None:
        values["empresa_id"] = empresa_id
    stmt = (
        update(UserSessionTable)
        .where(
            and_(
                usq._tenant_session_where(session_id, cliente_id),
                UserSessionTable.c.is_active == True,  # noqa: E712
            )
        )
        .values(**values)
    )
    return await _uow_rows_affected(uow, stmt)


async def _list_active_sessions_uow(
    uow: UnitOfWork,
    usuario_id: UUID,
    cliente_id: UUID,
) -> List[Dict[str, Any]]:
    stmt = (
        select(UserSessionTable)
        .where(usq._active_session_conditions(cliente_id, usuario_id))
        .order_by(UserSessionTable.c.created_at.asc(), UserSessionTable.c.session_id.asc())
    )
    return await _uow_select(uow, stmt)


async def _get_family_by_session_uow(
    uow: UnitOfWork,
    session_id: UUID,
    cliente_id: UUID,
) -> Optional[Dict[str, Any]]:
    stmt = select(TokenFamilyTable).where(
        and_(
            TokenFamilyTable.c.session_id == session_id,
            TokenFamilyTable.c.cliente_id == cliente_id,
            TokenFamilyTable.c.is_compromised == False,  # noqa: E712
        )
    )
    return await _uow_select_one(uow, stmt)


async def create_session_with_token_tx(
    uow: UnitOfWork,
    *,
    usuario_id: UUID,
    cliente_id: UUID,
    session_expires_at: datetime,
    token_hash: str,
    token_expires_at: datetime,
    platform: str,
    login_method: str = "password",
    selection_token_completed: bool = False,
    empresa_id: Optional[UUID] = None,
    device_name: Optional[str] = None,
    device_id: Optional[str] = None,
    device_fingerprint: Optional[str] = None,
    user_agent: Optional[str] = None,
    login_ip: Optional[str] = None,
    session_id: Optional[UUID] = None,
    family_id: Optional[UUID] = None,
    token_id: Optional[UUID] = None,
) -> Dict[str, Any]:
    """
    INSERT user_session + token_family + refresh_token; UPDATE family.current_token_id.
    Orden: session → family → token → current_token_id.
    """
    new_session_id = await _insert_user_session_uow(
        uow,
        usuario_id=usuario_id,
        cliente_id=cliente_id,
        expires_at=session_expires_at,
        platform=platform,
        login_method=login_method,
        selection_token_completed=selection_token_completed,
        empresa_id=empresa_id,
        device_name=device_name,
        device_id=device_id,
        device_fingerprint=device_fingerprint,
        user_agent=user_agent,
        login_ip=login_ip,
        session_id=session_id,
    )
    new_family_id = await _insert_token_family_uow(
        uow,
        session_id=new_session_id,
        usuario_id=usuario_id,
        cliente_id=cliente_id,
        family_id=family_id,
    )
    new_token_id = await _insert_refresh_token_uow(
        uow,
        family_id=new_family_id,
        session_id=new_session_id,
        usuario_id=usuario_id,
        cliente_id=cliente_id,
        token_hash=token_hash,
        expires_at=token_expires_at,
        parent_token_id=None,
        empresa_id=empresa_id,
        token_id=token_id,
    )
    family_rows = await _update_family_current_token_uow(
        uow,
        new_family_id,
        cliente_id,
        current_token_id=new_token_id,
    )
    if family_rows != 1:
        raise RuntimeError(
            "UPDATE token_family.current_token_id falló tras crear sesión "
            f"(family_id={new_family_id})"
        )
    return {
        "session_id": new_session_id,
        "family_id": new_family_id,
        "token_id": new_token_id,
        "expires_at": session_expires_at,
    }


def _row_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return bool(int(value))


def _is_locked_token_expired(expires_at: Any) -> bool:
    if expires_at is None:
        return False
    if not isinstance(expires_at, datetime):
        return False
    now = datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        return expires_at <= now.replace(tzinfo=None)
    return expires_at <= now


async def rotate_refresh_token_tx(
    uow: UnitOfWork,
    *,
    old_token_hash: str,
    new_token_hash: str,
    cliente_id: UUID,
    token_expires_at: datetime,
    new_token_id: Optional[UUID] = None,
    last_seen_ip: Optional[str] = None,
    empresa_id: Optional[UUID] = None,
) -> Dict[str, Any]:
    """
    RTR atómico (DESIGN §9.2): lock → validate → INSERT sucesor → UPDATE family → MARK used → session.
    mark_used=0 filas → RuntimeError (rollback).
    """
    lock_rows = await uow.execute(
        SQL_LOCK_REFRESH_TOKEN_BY_HASH_V3,
        {"token_hash": old_token_hash, "cliente_id": cliente_id},
    )
    if not lock_rows:
        raise RuntimeError(f"Token no encontrado para rotación hash={old_token_hash[:8]}...")

    old_row = lock_rows[0]
    old_token_id = old_row["token_id"]
    family_id = old_row["family_id"]
    session_id = old_row["session_id"]
    usuario_id = old_row["usuario_id"]

    if _row_bool(old_row.get("is_used")):
        raise RuntimeError(f"TOKEN_ALREADY_USED token_id={old_token_id}")
    if _row_bool(old_row.get("is_revoked")):
        raise RuntimeError(f"TOKEN_REVOKED token_id={old_token_id}")

    locked_expires_at = old_row.get("expires_at")
    if _is_locked_token_expired(locked_expires_at):
        raise RuntimeError(f"TOKEN_EXPIRED token_id={old_token_id}")

    family_lock_rows = await uow.execute(
        SQL_LOCK_TOKEN_FAMILY_BY_ID,
        {"family_id": family_id, "cliente_id": cliente_id},
    )
    if not family_lock_rows:
        raise RuntimeError(f"Familia no encontrada para rotación family_id={family_id}")
    if _row_bool(family_lock_rows[0].get("is_compromised")):
        raise RuntimeError(f"FAMILY_COMPROMISED family_id={family_id}")

    effective_empresa_id = (
        empresa_id if empresa_id is not None else old_row.get("empresa_id")
    )

    successor_id = await _insert_refresh_token_uow(
        uow,
        family_id=family_id,
        session_id=session_id,
        usuario_id=usuario_id,
        cliente_id=cliente_id,
        token_hash=new_token_hash,
        expires_at=token_expires_at,
        parent_token_id=old_token_id,
        empresa_id=effective_empresa_id,
        token_id=new_token_id,
    )
    family_rows = await _update_family_current_token_uow(
        uow,
        family_id,
        cliente_id,
        current_token_id=successor_id,
    )
    if family_rows != 1:
        raise RuntimeError(
            f"UPDATE token_family.current_token_id falló en rotación family_id={family_id}"
        )

    used_rows = await _mark_token_used_uow(uow, old_token_id, cliente_id)
    if used_rows != 1:
        raise RuntimeError(
            f"MARK token used retornó {used_rows} filas token_id={old_token_id}"
        )

    session_rows = await _update_session_on_refresh_uow(
        uow,
        session_id,
        cliente_id,
        last_seen_ip=last_seen_ip,
        empresa_id=effective_empresa_id,
    )

    return {
        "old_token_id": old_token_id,
        "new_token_id": successor_id,
        "family_id": family_id,
        "session_id": session_id,
        "session_update_rows": session_rows,
        "empresa_id": effective_empresa_id,
    }


async def revoke_session_tx(
    uow: UnitOfWork,
    *,
    session_id: UUID,
    family_id: UUID,
    cliente_id: UUID,
    session_revoked_reason: str,
    family_invalidation_reason: str,
    token_revoked_reason: str,
) -> Dict[str, Any]:
    """Cierra sesión, invalida familia y revoca tokens de la sesión."""
    session_rows = await _close_session_uow(
        uow,
        session_id,
        cliente_id,
        revoked_reason=session_revoked_reason,
    )
    family_rows = await _mark_family_compromised_uow(
        uow,
        family_id,
        cliente_id,
        invalidation_reason=family_invalidation_reason,
    )
    token_rows = await _revoke_tokens_by_session_uow(
        uow,
        session_id,
        cliente_id,
        revoked_reason=token_revoked_reason,
    )
    return {
        "session_rows": session_rows,
        "family_rows": family_rows,
        "token_rows": token_rows,
    }


async def revoke_all_user_sessions_tx(
    uow: UnitOfWork,
    *,
    usuario_id: UUID,
    cliente_id: UUID,
    session_revoked_reason: str,
    family_invalidation_reason: str,
    token_revoked_reason: str,
) -> Dict[str, Any]:
    """Bulk close + invalidación familia + revoke tokens por usuario (sin depender de snapshot)."""
    active_sessions = await _list_active_sessions_uow(uow, usuario_id, cliente_id)
    sessions_closed = await _close_all_user_sessions_uow(
        uow,
        usuario_id,
        cliente_id,
        revoked_reason=session_revoked_reason,
    )
    families_compromised = await _compromise_all_families_for_user_uow(
        uow,
        usuario_id,
        cliente_id,
        invalidation_reason=family_invalidation_reason,
    )
    tokens_revoked = await _revoke_all_tokens_for_user_uow(
        uow,
        usuario_id,
        cliente_id,
        revoked_reason=token_revoked_reason,
    )

    return {
        "sessions_closed": sessions_closed,
        "families_compromised": families_compromised,
        "tokens_revoked": tokens_revoked,
        "session_count": len(active_sessions),
    }


async def handle_replay_attack_tx(
    uow: UnitOfWork,
    *,
    session_id: UUID,
    family_id: UUID,
    token_id: UUID,
    cliente_id: UUID,
    usuario_id: UUID,
    session_revoked_reason: str = "security",
    family_invalidation_reason: str = "replay_detected",
    token_revoked_reason: str = "replay_detected",
) -> Dict[str, Any]:
    """
    Compromiso familia + cierre sesión + revoke tokens (DESIGN §7.3).
    UPDLOCK en familia para serializar compromiso concurrente.
    """
    await uow.execute(
        SQL_LOCK_TOKEN_FAMILY_BY_ID,
        {"family_id": family_id, "cliente_id": cliente_id},
    )

    family_rows = await _mark_family_compromised_uow(
        uow,
        family_id,
        cliente_id,
        invalidation_reason=family_invalidation_reason,
    )
    session_rows = await _close_session_uow(
        uow,
        session_id,
        cliente_id,
        revoked_reason=session_revoked_reason,
    )
    token_rows = await _revoke_tokens_by_session_uow(
        uow,
        session_id,
        cliente_id,
        revoked_reason=token_revoked_reason,
    )

    return {
        "session_id": session_id,
        "family_id": family_id,
        "token_id": token_id,
        "cliente_id": cliente_id,
        "usuario_id": usuario_id,
        "family_rows": family_rows,
        "session_rows": session_rows,
        "token_rows": token_rows,
    }


__all__ = [
    "SQL_LOCK_REFRESH_TOKEN_BY_HASH_V3",
    "SQL_LOCK_TOKEN_FAMILY_BY_ID",
    "create_session_with_token_tx",
    "handle_replay_attack_tx",
    "revoke_all_user_sessions_tx",
    "revoke_session_tx",
    "rotate_refresh_token_tx",
]
