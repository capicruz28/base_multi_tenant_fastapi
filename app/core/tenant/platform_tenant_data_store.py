"""F13-C4 — resolución L6 tenant_data para servicios Platform (F13-A1 §8)."""
from __future__ import annotations

from typing import Any, Optional, Tuple
from uuid import UUID

from app.core.tenant.operation_store_resolver import (
    get_installation_profile,
    resolve_operation_store,
)
from app.core.tenant.operation_store_types import (
    ExecuteQueryIntent,
    InstallationProfile,
    OperationDescriptor,
    OperationPlane,
)
from app.infrastructure.database.connection_async import DatabaseConnection


async def resolve_platform_tenant_data_intent(
    cliente_id: UUID,
) -> ExecuteQueryIntent:
    """Delega store routing en ``OperationStoreResolver`` (metadata del target, no Host)."""
    return await resolve_operation_store(
        OperationDescriptor(
            target_cliente_id=cliente_id,
            operation_plane=OperationPlane.TENANT_DATA,
        )
    )


async def resolve_platform_tenant_data_target(
    cliente_id: UUID,
) -> Tuple[DatabaseConnection, Optional[UUID]]:
    intent = await resolve_platform_tenant_data_intent(cliente_id)
    return intent.connection_type, intent.client_id


async def resolve_platform_tenant_data_database_type(cliente_id: UUID) -> str:
    profile = await get_installation_profile(cliente_id)
    return profile.database_type


async def resolve_platform_tenant_data_profile(
    cliente_id: UUID,
) -> InstallationProfile:
    return await get_installation_profile(cliente_id)


async def resolve_platform_tenant_data_execute_kwargs(
    cliente_id: UUID,
) -> dict[str, Any]:
    """Kwargs compatibles con ``execute_query`` / ``execute_update`` (tenant_data plane)."""
    intent = await resolve_platform_tenant_data_intent(cliente_id)
    return intent.to_execute_query_kwargs()


__all__ = [
    "resolve_platform_tenant_data_database_type",
    "resolve_platform_tenant_data_execute_kwargs",
    "resolve_platform_tenant_data_intent",
    "resolve_platform_tenant_data_profile",
    "resolve_platform_tenant_data_target",
]
