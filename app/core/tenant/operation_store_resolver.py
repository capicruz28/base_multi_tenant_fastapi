"""
F13-1 — OperationStoreResolver: algoritmo normativo de store (F13-A1 §8.3).

Resuelve ``ExecuteQueryIntent`` a partir de ``OperationDescriptor`` usando
``target_cliente_id`` + metadata CP — **sin** depender del Host HTTP.

Delegación obligatoria:
- ``get_connection_metadata_async`` (routing)
- ``_validate_dedicated_route_metadata`` (RI-39 fail-closed)
- Constantes ``OPERATION_CLASS_*``, ``DEDICATED_ROUTE_FAIL_CLOSED``

Sin wire-up productivo en F13-1.
"""
from __future__ import annotations

from uuid import UUID

from app.core.exceptions import DatabaseError, ValidationError
from app.core.identity.identity_scope import IdentityScope
from app.core.tenant.operation_store_types import (
    EngineKind,
    ExecuteQueryIntent,
    InstallationProfile,
    OperationDescriptor,
    OperationPlane,
)
from app.core.tenant.routing import (
    DEDICATED_ROUTE_FAIL_CLOSED,
    OPERATION_CLASS_CONTROL_PLANE,
    OPERATION_CLASS_TENANT_DATA,
    get_connection_metadata_async,
)
from app.infrastructure.database.connection_async import DatabaseConnection


def resolve_database_type(profile: InstallationProfile) -> str:
    """Legacy ``database_type`` para RBAC / menu resolver (F13-3)."""
    if profile.engine_kind == EngineKind.DEDICATED_MULTI:
        return "multi"
    return "single"


def _validate_descriptor(descriptor: OperationDescriptor) -> None:
    if descriptor.session_target_cliente_id is not None:
        if descriptor.session_target_cliente_id != descriptor.target_cliente_id:
            raise ValidationError(
                detail=(
                    "session_target_cliente_id debe coincidir con target_cliente_id "
                    f"({descriptor.session_target_cliente_id} != {descriptor.target_cliente_id})."
                ),
                internal_code="IMPERSONATION_TARGET_MISMATCH",
            )


def _control_plane_intent() -> ExecuteQueryIntent:
    return ExecuteQueryIntent(
        connection_type=DatabaseConnection.ADMIN,
        client_id=None,
        identity_scope=IdentityScope.ENGINE_SCOPED,
        operation_class=OPERATION_CLASS_CONTROL_PLANE,
        engine_kind=EngineKind.SHARED_SINGLE,
        database_type="single",
    )


def _tenant_data_intent(
    descriptor: OperationDescriptor,
    profile: InstallationProfile,
) -> ExecuteQueryIntent:
    if profile.engine_kind == EngineKind.SHARED_SINGLE:
        return ExecuteQueryIntent(
            connection_type=DatabaseConnection.DEFAULT,
            client_id=descriptor.target_cliente_id,
            identity_scope=IdentityScope.ROW_SCOPED,
            operation_class=OPERATION_CLASS_TENANT_DATA,
            engine_kind=EngineKind.SHARED_SINGLE,
            database_type="single",
        )

    if profile.engine_kind == EngineKind.DEDICATED_MULTI:
        return ExecuteQueryIntent(
            connection_type=DatabaseConnection.DEFAULT,
            client_id=descriptor.target_cliente_id,
            identity_scope=IdentityScope.ENGINE_SCOPED,
            operation_class=OPERATION_CLASS_TENANT_DATA,
            engine_kind=EngineKind.DEDICATED_MULTI,
            database_type="multi",
        )

    raise DatabaseError(
        detail=(
            f"Tenant {descriptor.target_cliente_id} sin engine_kind resoluble "
            f"(RI-39)."
        ),
        internal_code=DEDICATED_ROUTE_FAIL_CLOSED,
    )


async def resolve_operation_store(
    descriptor: OperationDescriptor,
) -> ExecuteQueryIntent:
    """
    Algoritmo F13-A1 §8.3 / F13-B1 §10.4.

    ``control_plane`` no consulta metadata; ``tenant_data`` delega en routing.
    """
    _validate_descriptor(descriptor)

    if descriptor.operation_plane == OperationPlane.CONTROL_PLANE:
        return _control_plane_intent()

    metadata = await get_connection_metadata_async(
        descriptor.target_cliente_id,
        OPERATION_CLASS_TENANT_DATA,
    )
    profile = InstallationProfile.from_metadata(descriptor.target_cliente_id, metadata)
    return _tenant_data_intent(descriptor, profile)


async def get_installation_profile(cliente_id: UUID) -> InstallationProfile:
    """Profile CP del target — consumo F13-3 (impersonation / deps)."""
    metadata = await get_connection_metadata_async(
        cliente_id,
        OPERATION_CLASS_TENANT_DATA,
    )
    return InstallationProfile.from_metadata(cliente_id, metadata)


class OperationStoreResolver:
    """Fachada normativa — sin estado."""

    resolve = staticmethod(resolve_operation_store)
    get_installation_profile = staticmethod(get_installation_profile)


__all__ = [
    "OperationStoreResolver",
    "get_installation_profile",
    "resolve_database_type",
    "resolve_operation_store",
]
