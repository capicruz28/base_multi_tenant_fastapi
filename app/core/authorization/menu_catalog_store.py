"""F11-P1 / F13-C2 — resolución L6 del store para QUERY 1 catálogo menú + licencia."""
from __future__ import annotations

from typing import Optional, Tuple
from uuid import UUID

from app.core.tenant.operation_store_resolver import resolve_operation_store
from app.core.tenant.operation_store_types import OperationDescriptor, OperationPlane
from app.infrastructure.database.connection_async import DatabaseConnection


async def resolve_menu_catalog_query1_target(
    cliente_id: UUID,
) -> Tuple[DatabaseConnection, Optional[UUID]]:
    """
    Delega store routing en ``OperationStoreResolver`` (metadata del target, no Host).

    Shared → tenant_data / DEFAULT + ``client_id`` (F13-A1).
    Dedicated → tenant_data / DEFAULT + ``client_id`` explícito.
    """
    intent = await resolve_operation_store(
        OperationDescriptor(
            target_cliente_id=cliente_id,
            operation_plane=OperationPlane.TENANT_DATA,
        )
    )
    return intent.connection_type, intent.client_id


__all__ = ["resolve_menu_catalog_query1_target"]
