"""F6-P1 — executor Identity Store sobre Persistence Gateway."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy.sql import ClauseElement

from app.core.identity.identity_scope import IdentityScope
from app.core.identity.identity_store_connection import OPERATION_CLASS_TENANT_IDENTITY
from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.queries_async import execute_query, execute_update


async def execute_identity_query(
    query: ClauseElement,
    *,
    cliente_id: UUID,
    identity_scope: IdentityScope,
) -> List[Dict[str, Any]]:
    """SELECT identity — tenant_data route + política scope."""
    return await execute_query(
        query,
        client_id=cliente_id,
        connection_type=DatabaseConnection.DEFAULT,
        identity_scope=identity_scope,
        operation_class=OPERATION_CLASS_TENANT_IDENTITY,
    )


async def execute_identity_update(
    query: ClauseElement,
    *,
    cliente_id: UUID,
    identity_scope: IdentityScope,
) -> Dict[str, Any]:
    """UPDATE identity — tenant_data route + política scope."""
    return await execute_update(
        query,
        client_id=cliente_id,
        connection_type=DatabaseConnection.DEFAULT,
        identity_scope=identity_scope,
        operation_class=OPERATION_CLASS_TENANT_IDENTITY,
    )


async def execute_platform_identity_query(
    query: ClauseElement,
    *,
    platform_cliente_id: UUID,
) -> List[Dict[str, Any]]:
    """Platform superadmin lookup — ADMIN + ROW_SCOPED explícito en SQL."""
    return await execute_query(
        query,
        client_id=platform_cliente_id,
        connection_type=DatabaseConnection.ADMIN,
        identity_scope=IdentityScope.ROW_SCOPED,
    )


__all__ = [
    "execute_identity_query",
    "execute_identity_update",
    "execute_platform_identity_query",
]
