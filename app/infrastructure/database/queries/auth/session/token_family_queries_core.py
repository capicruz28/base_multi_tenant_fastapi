"""
Queries SQLAlchemy Core — tabla token_family (IAM Session V3, C16).

Operaciones atómicas por fila; sin orquestación multi-tabla (C18).
Siempre filtra cliente_id en WHERE.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, func, insert, select, update

from app.core.exceptions import ValidationError
from app.infrastructure.database.tables import TokenFamilyTable

logger = logging.getLogger(__name__)

_FAMILY_COLUMNS = {c.name for c in TokenFamilyTable.c}

_INVALIDATION_REASONS = frozenset(
    {
        "replay_detected",
        "session_revoked",
        "admin_force",
        "password_reset",
        "security_policy",
    }
)


def _assert_invalidation_reason(invalidation_reason: str) -> None:
    if invalidation_reason not in _INVALIDATION_REASONS:
        raise ValidationError(
            detail=f"invalidation_reason inválido para token_family: '{invalidation_reason}'",
            internal_code="INVALID_FAMILY_INVALIDATION_REASON",
        )


def _tenant_family_where(family_id: UUID, cliente_id: UUID):
    return and_(
        TokenFamilyTable.c.family_id == family_id,
        TokenFamilyTable.c.cliente_id == cliente_id,
    )


def _non_compromised_family_where(family_id: UUID, cliente_id: UUID):
    return and_(
        _tenant_family_where(family_id, cliente_id),
        TokenFamilyTable.c.is_compromised == False,  # noqa: E712
    )


async def insert_token_family_core(
    *,
    session_id: UUID,
    usuario_id: UUID,
    cliente_id: UUID,
    family_id: Optional[UUID] = None,
) -> Dict[str, Any]:
    """INSERT familia nueva. current_token_id=NULL hasta emitir primer token."""
    from app.infrastructure.database.queries_async import execute_insert

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
        **{k: v for k, v in payload.items() if k in _FAMILY_COLUMNS}
    )
    await execute_insert(stmt, client_id=cliente_id)
    row = await get_family_by_id_core(new_family_id, cliente_id)
    if row is None:
        raise ValidationError(
            detail="No se pudo leer la familia recién insertada",
            internal_code="TOKEN_FAMILY_INSERT_READBACK_FAILED",
        )
    return row


async def update_current_token_id_core(
    family_id: UUID,
    cliente_id: UUID,
    *,
    current_token_id: UUID,
) -> int:
    """SET current_token_id en familia no comprometida (rotate tx — C18)."""
    from app.infrastructure.database.queries_async import execute_update

    stmt = (
        update(TokenFamilyTable)
        .where(_non_compromised_family_where(family_id, cliente_id))
        .values(current_token_id=current_token_id)
    )
    result = await execute_update(stmt, client_id=cliente_id)
    return int(result.get("rows_affected", 0))


async def mark_family_compromised_core(
    family_id: UUID,
    cliente_id: UUID,
    *,
    invalidation_reason: str,
) -> int:
    """
    Marca familia comprometida. Irreversible e idempotente:
    ya comprometida → 0 filas afectadas.
    """
    from app.infrastructure.database.queries_async import execute_update

    _assert_invalidation_reason(invalidation_reason)
    stmt = (
        update(TokenFamilyTable)
        .where(
            and_(
                _tenant_family_where(family_id, cliente_id),
                TokenFamilyTable.c.is_compromised == False,  # noqa: E712
            )
        )
        .values(
            is_compromised=True,
            compromised_at=func.getdate(),
            invalidation_reason=invalidation_reason,
        )
    )
    result = await execute_update(stmt, client_id=cliente_id)
    return int(result.get("rows_affected", 0))


async def get_family_by_id_core(
    family_id: UUID,
    cliente_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Lookup por family_id + tenant. Incluye is_compromised para validación caller."""
    from app.infrastructure.database.queries_async import execute_query

    query = select(TokenFamilyTable).where(_tenant_family_where(family_id, cliente_id))
    rows = await execute_query(query, client_id=cliente_id)
    return rows[0] if rows else None


async def get_family_by_session_id_core(
    session_id: UUID,
    cliente_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Familia no comprometida de la sesión (relación 1:1 activa)."""
    from app.infrastructure.database.queries_async import execute_query

    query = select(TokenFamilyTable).where(
        and_(
            TokenFamilyTable.c.session_id == session_id,
            TokenFamilyTable.c.cliente_id == cliente_id,
            TokenFamilyTable.c.is_compromised == False,  # noqa: E712
        )
    )
    rows = await execute_query(query, client_id=cliente_id)
    return rows[0] if rows else None


async def get_family_by_current_token_id_core(
    current_token_id: UUID,
    cliente_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Lookup O(1) por current_token_id + tenant."""
    from app.infrastructure.database.queries_async import execute_query

    query = select(TokenFamilyTable).where(
        and_(
            TokenFamilyTable.c.current_token_id == current_token_id,
            TokenFamilyTable.c.cliente_id == cliente_id,
        )
    )
    rows = await execute_query(query, client_id=cliente_id)
    return rows[0] if rows else None


__all__ = [
    "get_family_by_current_token_id_core",
    "get_family_by_id_core",
    "get_family_by_session_id_core",
    "insert_token_family_core",
    "mark_family_compromised_core",
    "update_current_token_id_core",
]
