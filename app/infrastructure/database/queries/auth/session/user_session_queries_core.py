"""
Queries SQLAlchemy Core — tabla user_session (IAM Session V3, C15).

Operaciones atómicas por fila; sin orquestación multi-tabla (C18).
Siempre filtra cliente_id en WHERE.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, delete, func, insert, not_, select, text, update

from app.core.exceptions import ValidationError
from app.infrastructure.database.tables import (
    RefreshTokensTable,
    TokenFamilyTable,
    UserSessionTable,
)

logger = logging.getLogger(__name__)

_SESSION_COLUMNS = {c.name for c in UserSessionTable.c}

_SESSION_REVOKED_REASONS = frozenset(
    {"logout", "admin_force", "security", "expired", "password_reset"}
)

_LOGIN_METHODS = frozenset({"password", "sso", "2fa", "api_key"})
_PLATFORMS = frozenset({"web", "mobile", "desktop", "api"})

_DEFAULT_SESSION_RETENTION_DAYS = 90
_DEFAULT_COMPROMISED_RETENTION_DAYS = 365


def _retention_cutoff(retention_days: int):
    return func.dateadd(text("day"), -retention_days, func.getdate())


def _assert_session_revoked_reason(revoked_reason: str) -> None:
    if revoked_reason not in _SESSION_REVOKED_REASONS:
        raise ValidationError(
            detail=f"revoked_reason inválido para user_session: '{revoked_reason}'",
            internal_code="INVALID_SESSION_REVOKED_REASON",
        )


def _assert_login_method(login_method: str) -> None:
    if login_method not in _LOGIN_METHODS:
        raise ValidationError(
            detail=f"login_method inválido: '{login_method}'",
            internal_code="INVALID_SESSION_LOGIN_METHOD",
        )


def _assert_platform(platform: str) -> None:
    if platform not in _PLATFORMS:
        raise ValidationError(
            detail=f"platform inválido: '{platform}'",
            internal_code="INVALID_SESSION_PLATFORM",
        )


def _tenant_session_where(session_id: UUID, cliente_id: UUID):
    return and_(
        UserSessionTable.c.session_id == session_id,
        UserSessionTable.c.cliente_id == cliente_id,
    )


def _active_session_conditions(cliente_id: UUID, usuario_id: Optional[UUID] = None):
    conditions = [
        UserSessionTable.c.cliente_id == cliente_id,
        UserSessionTable.c.is_active == True,  # noqa: E712
        UserSessionTable.c.expires_at > func.getdate(),
    ]
    if usuario_id is not None:
        conditions.append(UserSessionTable.c.usuario_id == usuario_id)
    return and_(*conditions)


async def insert_user_session_core(
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
) -> Dict[str, Any]:
    """INSERT sesión nueva. login_ip es inmutable post-create."""
    from app.infrastructure.database.queries_async import execute_insert

    _assert_login_method(login_method)
    _assert_platform(platform)

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
        **{k: v for k, v in payload.items() if k in _SESSION_COLUMNS}
    )
    await execute_insert(stmt, client_id=cliente_id)
    row = await get_active_session_by_id_core(new_session_id, cliente_id)
    if row is None:
        raise ValidationError(
            detail="No se pudo leer la sesión recién insertada",
            internal_code="SESSION_INSERT_READBACK_FAILED",
        )
    return row


async def update_session_empresa_core(
    session_id: UUID,
    cliente_id: UUID,
    *,
    empresa_id: UUID,
    selection_token_completed: bool,
) -> int:
    """SET empresa_id y selection_token_completed. No modifica login_ip."""
    from app.infrastructure.database.queries_async import execute_update

    stmt = (
        update(UserSessionTable)
        .where(_tenant_session_where(session_id, cliente_id))
        .values(
            empresa_id=empresa_id,
            selection_token_completed=selection_token_completed,
        )
    )
    result = await execute_update(stmt, client_id=cliente_id)
    return int(result.get("rows_affected", 0))


async def update_session_on_refresh_core(
    session_id: UUID,
    cliente_id: UUID,
    *,
    last_seen_ip: Optional[str] = None,
) -> int:
    """SET last_refresh_at y last_seen_ip tras POST /auth/refresh."""
    from app.infrastructure.database.queries_async import execute_update

    values: Dict[str, Any] = {"last_refresh_at": func.getdate()}
    if last_seen_ip is not None:
        values["last_seen_ip"] = last_seen_ip

    stmt = (
        update(UserSessionTable)
        .where(
            and_(
                _tenant_session_where(session_id, cliente_id),
                UserSessionTable.c.is_active == True,  # noqa: E712
            )
        )
        .values(**values)
    )
    result = await execute_update(stmt, client_id=cliente_id)
    return int(result.get("rows_affected", 0))


async def touch_business_activity_core(
    session_id: UUID,
    cliente_id: UUID,
) -> int:
    """SET last_business_activity_at = GETDATE(). Throttle en capa service (C05)."""
    from app.infrastructure.database.queries_async import execute_update

    stmt = (
        update(UserSessionTable)
        .where(
            and_(
                _tenant_session_where(session_id, cliente_id),
                UserSessionTable.c.is_active == True,  # noqa: E712
            )
        )
        .values(last_business_activity_at=func.getdate())
    )
    result = await execute_update(stmt, client_id=cliente_id)
    return int(result.get("rows_affected", 0))


async def close_session_core(
    session_id: UUID,
    cliente_id: UUID,
    *,
    revoked_reason: str,
) -> int:
    """Cierra sesión activa. Idempotente: ya cerrada → 0 filas."""
    from app.infrastructure.database.queries_async import execute_update

    _assert_session_revoked_reason(revoked_reason)
    stmt = (
        update(UserSessionTable)
        .where(
            and_(
                _tenant_session_where(session_id, cliente_id),
                UserSessionTable.c.is_active == True,  # noqa: E712
            )
        )
        .values(
            is_active=False,
            revoked_at=func.getdate(),
            revoked_reason=revoked_reason,
        )
    )
    result = await execute_update(stmt, client_id=cliente_id)
    return int(result.get("rows_affected", 0))


async def close_all_user_sessions_core(
    usuario_id: UUID,
    cliente_id: UUID,
    *,
    revoked_reason: str,
) -> int:
    """Bulk close sesiones activas del usuario en el tenant."""
    from app.infrastructure.database.queries_async import execute_update

    _assert_session_revoked_reason(revoked_reason)
    stmt = (
        update(UserSessionTable)
        .where(
            and_(
                _active_session_conditions(cliente_id, usuario_id),
            )
        )
        .values(
            is_active=False,
            revoked_at=func.getdate(),
            revoked_reason=revoked_reason,
        )
    )
    result = await execute_update(stmt, client_id=cliente_id)
    return int(result.get("rows_affected", 0))


async def get_active_session_by_id_core(
    session_id: UUID,
    cliente_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Sesión activa no expirada por session_id + tenant."""
    from app.infrastructure.database.queries_async import execute_query

    query = select(UserSessionTable).where(
        and_(
            _tenant_session_where(session_id, cliente_id),
            UserSessionTable.c.is_active == True,  # noqa: E712
            UserSessionTable.c.expires_at > func.getdate(),
        )
    )
    rows = await execute_query(query, client_id=cliente_id)
    return rows[0] if rows else None


async def count_active_sessions_core(
    usuario_id: UUID,
    cliente_id: UUID,
) -> int:
    """Cuenta sesiones activas no expiradas (session limit)."""
    from app.infrastructure.database.queries_async import execute_query

    query = select(func.count(UserSessionTable.c.session_id).label("total")).where(
        _active_session_conditions(cliente_id, usuario_id)
    )
    rows = await execute_query(query, client_id=cliente_id)
    if not rows:
        return 0
    return int(rows[0].get("total", 0))


async def list_active_sessions_oldest_first_core(
    usuario_id: UUID,
    cliente_id: UUID,
    *,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Lista sesiones activas ordenadas por created_at ASC (eviction)."""
    from app.infrastructure.database.queries_async import execute_query

    query = (
        select(UserSessionTable)
        .where(_active_session_conditions(cliente_id, usuario_id))
        .order_by(UserSessionTable.c.created_at.asc(), UserSessionTable.c.session_id.asc())
    )
    if limit is not None:
        query = query.limit(limit)
    return await execute_query(query, client_id=cliente_id)


async def is_session_idle_expired_core(
    session_id: UUID,
    cliente_id: UUID,
    idle_timeout_minutes: int,
) -> bool:
    """
    Evalúa idle auth timeout sobre last_refresh_at (fallback created_at).
    Usa GETDATE() en SQL Server — sin comparar datetimes Python.
    """
    if not idle_timeout_minutes or idle_timeout_minutes <= 0:
        return False

    from app.infrastructure.database.queries_async import execute_query
    from sqlalchemy import text

    query = text(
        """
        SELECT CASE
            WHEN COALESCE(last_refresh_at, created_at) IS NULL THEN 0
            WHEN DATEDIFF(
                minute,
                COALESCE(last_refresh_at, created_at),
                GETDATE()
            ) > :idle_timeout_minutes THEN 1
            ELSE 0
        END AS idle_expired
        FROM user_session
        WHERE session_id = :session_id
          AND cliente_id = :cliente_id
        """
    ).bindparams(
        session_id=session_id,
        cliente_id=cliente_id,
        idle_timeout_minutes=idle_timeout_minutes,
    )
    rows = await execute_query(query, client_id=cliente_id)
    if not rows:
        return False
    return bool(rows[0].get("idle_expired", 0))


async def is_session_absolute_expired_core(
    session_id: UUID,
    cliente_id: UUID,
) -> bool:
    """True si expires_at <= GETDATE()."""
    from app.infrastructure.database.queries_async import execute_query
    from sqlalchemy import text

    query = text(
        """
        SELECT CASE
            WHEN expires_at IS NULL THEN 0
            WHEN expires_at <= GETDATE() THEN 1
            ELSE 0
        END AS absolute_expired
        FROM user_session
        WHERE session_id = :session_id
          AND cliente_id = :cliente_id
        """
    ).bindparams(session_id=session_id, cliente_id=cliente_id)
    rows = await execute_query(query, client_id=cliente_id)
    if not rows:
        return False
    return bool(rows[0].get("absolute_expired", 0))


async def find_session_by_device_core(
    usuario_id: UUID,
    cliente_id: UUID,
    *,
    device_id: str,
) -> Optional[Dict[str, Any]]:
    """Lookup sesión activa por device_id + usuario (futuro device reuse)."""
    if not device_id or not device_id.strip():
        return None

    from app.infrastructure.database.queries_async import execute_query

    query = (
        select(UserSessionTable)
        .where(
            and_(
                _active_session_conditions(cliente_id, usuario_id),
                UserSessionTable.c.device_id == device_id,
            )
        )
        .order_by(UserSessionTable.c.created_at.desc())
        .limit(1)
    )
    rows = await execute_query(query, client_id=cliente_id)
    return rows[0] if rows else None


async def purge_closed_sessions_core(
    cliente_id: UUID,
    *,
    retention_days: int = _DEFAULT_SESSION_RETENTION_DAYS,
    compromised_retention_days: int = _DEFAULT_COMPROMISED_RETENTION_DAYS,
) -> int:
    """
    DELETE sesiones cerradas fuera de retención forense (D-04).

  - Sesiones inactivas con revoked_at anterior al cutoff (90d por defecto).
  - Excluye sesiones con familia comprometida aún dentro de retención SIEM
    (365d por defecto); token_family se elimina en cascada al purgar la sesión.
    """
    if retention_days <= 0:
        raise ValidationError(
            detail="retention_days debe ser mayor que cero",
            internal_code="INVALID_SESSION_PURGE_RETENTION",
        )
    if compromised_retention_days <= 0:
        raise ValidationError(
            detail="compromised_retention_days debe ser mayor que cero",
            internal_code="INVALID_COMPROMISED_PURGE_RETENTION",
        )

    from app.infrastructure.database.queries_async import execute_query

    session_cutoff = _retention_cutoff(retention_days)
    compromised_cutoff = _retention_cutoff(compromised_retention_days)
    protected_sessions = (
        select(TokenFamilyTable.c.session_id)
        .where(
            and_(
                TokenFamilyTable.c.cliente_id == cliente_id,
                TokenFamilyTable.c.is_compromised == True,  # noqa: E712
                TokenFamilyTable.c.compromised_at >= compromised_cutoff,
            )
        )
        .scalar_subquery()
    )
    remaining_tokens = (
        select(RefreshTokensTable.c.token_id)
        .where(
            and_(
                RefreshTokensTable.c.session_id == UserSessionTable.c.session_id,
                RefreshTokensTable.c.cliente_id == cliente_id,
            )
        )
        .correlate(UserSessionTable)
        .exists()
    )
    stmt = delete(UserSessionTable).where(
        and_(
            UserSessionTable.c.cliente_id == cliente_id,
            UserSessionTable.c.is_active == False,  # noqa: E712
            UserSessionTable.c.revoked_at.isnot(None),
            UserSessionTable.c.revoked_at < session_cutoff,
            not_(UserSessionTable.c.session_id.in_(protected_sessions)),
            not_(remaining_tokens),
        )
    )
    result = await execute_query(stmt, client_id=cliente_id)
    if result and len(result) > 0:
        return int(result[0].get("rows_affected", 0))
    return 0


__all__ = [
    "close_all_user_sessions_core",
    "close_session_core",
    "count_active_sessions_core",
    "find_session_by_device_core",
    "get_active_session_by_id_core",
    "insert_user_session_core",
    "is_session_absolute_expired_core",
    "is_session_idle_expired_core",
    "list_active_sessions_oldest_first_core",
    "purge_closed_sessions_core",
    "touch_business_activity_core",
    "update_session_empresa_core",
    "update_session_on_refresh_core",
]
