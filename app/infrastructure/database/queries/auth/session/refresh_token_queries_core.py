"""
Queries SQLAlchemy Core — tabla refresh_tokens v3 (IAM Session V3, C17).

Operaciones atómicas por fila; sin orquestación multi-tabla (C18).
Siempre filtra cliente_id en WHERE.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, delete, func, insert, or_, select, text, update

from app.core.exceptions import ValidationError
from app.infrastructure.database.tables import RefreshTokensTable

logger = logging.getLogger(__name__)

_TOKEN_COLUMNS = {c.name for c in RefreshTokensTable.c}

_DEFAULT_RETENTION_DAYS = 90

_TOKEN_REVOKED_REASONS = frozenset(
    {
        "logout",
        "replay_detected",
        "admin_force",
        "password_reset",
        "family_compromised",
    }
)


def _assert_token_revoked_reason(revoked_reason: str) -> None:
    if revoked_reason not in _TOKEN_REVOKED_REASONS:
        raise ValidationError(
            detail=f"revoked_reason inválido para refresh_tokens: '{revoked_reason}'",
            internal_code="INVALID_TOKEN_REVOKED_REASON",
        )


def _tenant_token_where(token_id: UUID, cliente_id: UUID):
    return and_(
        RefreshTokensTable.c.token_id == token_id,
        RefreshTokensTable.c.cliente_id == cliente_id,
    )


def _usable_token_where(token_id: UUID, cliente_id: UUID):
    return and_(
        _tenant_token_where(token_id, cliente_id),
        RefreshTokensTable.c.is_used == False,  # noqa: E712
        RefreshTokensTable.c.is_revoked == False,  # noqa: E712
    )


def _retention_cutoff(retention_days: int):
    return func.dateadd(text("day"), -retention_days, func.getdate())


async def _get_token_by_id_core(
    token_id: UUID,
    cliente_id: UUID,
) -> Optional[Dict[str, Any]]:
    from app.infrastructure.database.queries_async import execute_query

    query = select(RefreshTokensTable).where(_tenant_token_where(token_id, cliente_id))
    rows = await execute_query(query, client_id=cliente_id)
    return rows[0] if rows else None


async def insert_refresh_token_core(
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
) -> Dict[str, Any]:
    """INSERT credencial v3. parent_token_id=NULL solo en primer token de la familia."""
    from app.infrastructure.database.queries_async import execute_insert

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
        **{k: v for k, v in payload.items() if k in _TOKEN_COLUMNS}
    )
    await execute_insert(stmt, client_id=cliente_id)
    row = await _get_token_by_id_core(new_token_id, cliente_id)
    if row is None:
        raise ValidationError(
            detail="No se pudo leer el refresh token recién insertado",
            internal_code="REFRESH_TOKEN_INSERT_READBACK_FAILED",
        )
    return row


async def get_refresh_token_by_hash_core(
    token_hash: str,
    cliente_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Hot path: activo, no usado, no revocado, no expirado."""
    from app.infrastructure.database.queries_async import execute_query

    query = select(RefreshTokensTable).where(
        and_(
            RefreshTokensTable.c.token_hash == token_hash,
            RefreshTokensTable.c.cliente_id == cliente_id,
            RefreshTokensTable.c.is_used == False,  # noqa: E712
            RefreshTokensTable.c.is_revoked == False,  # noqa: E712
            RefreshTokensTable.c.expires_at > func.getdate(),
        )
    )
    rows = await execute_query(query, client_id=cliente_id)
    return rows[0] if rows else None


async def get_refresh_token_by_hash_any_state_core(
    token_hash: str,
    cliente_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Probe / replay: incluye usado, revocado y expirado."""
    from app.infrastructure.database.queries_async import execute_query

    query = select(RefreshTokensTable).where(
        and_(
            RefreshTokensTable.c.token_hash == token_hash,
            RefreshTokensTable.c.cliente_id == cliente_id,
        )
    )
    rows = await execute_query(query, client_id=cliente_id)
    return rows[0] if rows else None


async def mark_token_used_core(
    token_id: UUID,
    cliente_id: UUID,
) -> int:
    """
    Marca token consumido en rotación. Ya usado o revocado → 0 filas (señal replay en C18).
    """
    from app.infrastructure.database.queries_async import execute_update

    stmt = (
        update(RefreshTokensTable)
        .where(_usable_token_where(token_id, cliente_id))
        .values(
            is_used=True,
            used_at=func.getdate(),
            last_used_at=func.getdate(),
        )
    )
    result = await execute_update(stmt, client_id=cliente_id)
    return int(result.get("rows_affected", 0))


async def revoke_token_core(
    token_id: UUID,
    cliente_id: UUID,
    *,
    revoked_reason: str,
) -> int:
    """Revocación forzada de un token. Idempotente si ya está revocado."""
    from app.infrastructure.database.queries_async import execute_update

    _assert_token_revoked_reason(revoked_reason)
    stmt = (
        update(RefreshTokensTable)
        .where(
            and_(
                _tenant_token_where(token_id, cliente_id),
                RefreshTokensTable.c.is_revoked == False,  # noqa: E712
            )
        )
        .values(
            is_revoked=True,
            revoked_at=func.getdate(),
            revoked_reason=revoked_reason,
        )
    )
    result = await execute_update(stmt, client_id=cliente_id)
    return int(result.get("rows_affected", 0))


async def revoke_tokens_by_session_core(
    session_id: UUID,
    cliente_id: UUID,
    *,
    revoked_reason: str,
) -> int:
    """Bulk revoke de tokens no revocados de una sesión."""
    from app.infrastructure.database.queries_async import execute_update

    _assert_token_revoked_reason(revoked_reason)
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
    result = await execute_update(stmt, client_id=cliente_id)
    return int(result.get("rows_affected", 0))


async def purge_expired_tokens_core(
    cliente_id: UUID,
    *,
    retention_days: int = _DEFAULT_RETENTION_DAYS,
) -> int:
    """
    DELETE con política de retención forense (D-04: 90 días usados/revocados).
    También elimina tokens expirados nunca consumidos.
    """
    if retention_days <= 0:
        raise ValidationError(
            detail="retention_days debe ser mayor que cero",
            internal_code="INVALID_TOKEN_PURGE_RETENTION",
        )

    from app.infrastructure.database.queries_async import execute_query

    cutoff = _retention_cutoff(retention_days)
    stmt = delete(RefreshTokensTable).where(
        and_(
            RefreshTokensTable.c.cliente_id == cliente_id,
            or_(
                and_(
                    RefreshTokensTable.c.is_used == True,  # noqa: E712
                    RefreshTokensTable.c.used_at < cutoff,
                ),
                and_(
                    RefreshTokensTable.c.is_revoked == True,  # noqa: E712
                    RefreshTokensTable.c.revoked_at < cutoff,
                ),
                and_(
                    RefreshTokensTable.c.is_used == False,  # noqa: E712
                    RefreshTokensTable.c.is_revoked == False,  # noqa: E712
                    RefreshTokensTable.c.expires_at < func.getdate(),
                ),
            ),
        )
    )
    result = await execute_query(stmt, client_id=cliente_id)
    if result and len(result) > 0:
        return int(result[0].get("rows_affected", 0))
    return 0


__all__ = [
    "get_refresh_token_by_hash_any_state_core",
    "get_refresh_token_by_hash_core",
    "insert_refresh_token_core",
    "mark_token_used_core",
    "purge_expired_tokens_core",
    "revoke_token_core",
    "revoke_tokens_by_session_core",
]
