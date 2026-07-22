"""Queries SQLAlchemy Core — cliente_auth_config (ADR-012, CP SSOT)."""
from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.queries.auth.auth_config_connection import (
    AUTH_CONFIG_STORE_CONNECTION,
)
from app.infrastructure.database.tables import ClienteAuthConfigTable

_CONFIG_COLUMNS = {c.name for c in ClienteAuthConfigTable.c}


def _row_to_dict(row) -> Dict[str, Any]:
    if row is None:
        return {}
    if hasattr(row, "_mapping"):
        return dict(row._mapping)
    if isinstance(row, dict):
        return row
    return dict(row)


async def select_config_by_cliente_id_core(
    cliente_id: UUID,
) -> Optional[Dict[str, Any]]:
    from app.infrastructure.database.queries_async import execute_query

    query = select(ClienteAuthConfigTable).where(
        ClienteAuthConfigTable.c.cliente_id == cliente_id
    )
    rows = await execute_query(
        query,
        connection_type=AUTH_CONFIG_STORE_CONNECTION,
        client_id=cliente_id,
    )
    return rows[0] if rows else None


def _coerce_config_id(config_id: Any) -> Optional[UUID]:
    if config_id is None:
        return None
    if isinstance(config_id, UUID):
        return config_id
    return UUID(str(config_id))


async def select_config_id_by_cliente_id_core(
    cliente_id: UUID,
    session: Optional[AsyncSession] = None,
) -> Optional[UUID]:
    query = select(ClienteAuthConfigTable.c.config_id).where(
        ClienteAuthConfigTable.c.cliente_id == cliente_id
    )

    if session is not None:
        result = await session.execute(query)
        return _coerce_config_id(result.scalar_one_or_none())

    from app.infrastructure.database.queries_async import execute_query

    rows = await execute_query(
        query,
        connection_type=AUTH_CONFIG_STORE_CONNECTION,
        client_id=cliente_id,
    )
    if not rows:
        return None
    return _coerce_config_id(rows[0].get("config_id"))


async def insert_config_core(
    values: Dict[str, Any],
    session: Optional[AsyncSession] = None,
) -> Dict[str, Any]:
    payload = {k: v for k, v in values.items() if k in _CONFIG_COLUMNS and k != "config_id"}
    stmt = (
        insert(ClienteAuthConfigTable)
        .values(**payload)
        .returning(*ClienteAuthConfigTable.c)
    )

    if session is not None:
        result = await session.execute(stmt)
        row = result.first()
        return _row_to_dict(row) if row is not None else {}

    from app.infrastructure.database.queries_async import execute_insert

    result = await execute_insert(
        stmt,
        connection_type=AUTH_CONFIG_STORE_CONNECTION,
    )
    if not result:
        return {}
    return _row_to_dict(result)


async def update_config_core(
    cliente_id: UUID,
    values: Dict[str, Any],
) -> Dict[str, Any]:
    from app.infrastructure.database.queries_async import execute_update

    payload = {
        k: v
        for k, v in values.items()
        if k in _CONFIG_COLUMNS and k not in ("config_id", "cliente_id", "fecha_creacion")
    }
    if not payload:
        return {}
    payload["fecha_actualizacion"] = func.getdate()
    stmt = (
        update(ClienteAuthConfigTable)
        .where(ClienteAuthConfigTable.c.cliente_id == cliente_id)
        .values(**payload)
        .returning(*ClienteAuthConfigTable.c)
    )
    result = await execute_update(
        stmt,
        connection_type=AUTH_CONFIG_STORE_CONNECTION,
        client_id=cliente_id,
    )
    if not result:
        return {}
    return _row_to_dict(result)


__all__ = [
    "insert_config_core",
    "select_config_by_cliente_id_core",
    "select_config_id_by_cliente_id_core",
    "update_config_core",
]
