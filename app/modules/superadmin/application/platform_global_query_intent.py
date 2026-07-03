"""
Platform Admin — explicit global Control Plane query intent (F12-E2B3N).

Superadmin services operate on cross-tenant / CP data. They must not inherit
automatic ``cliente_id`` filtering from TenantMiddleware ContextVar (SYSTEM).

Contract (RD-07 / 08_QUERY_EXECUTION_MODEL):
- Platform global reads declare ``identity_scope=ENGINE_SCOPED`` so the existing
  tenant-filter layer omits row-level ``cliente_id`` injection.
- CP-only tables use ``connection_type=ADMIN`` + ``operation_class=control_plane``.
- Tenant-targeted reads pass explicit ``client_id`` for routing only (same scope).

This module does NOT bypass tenant validation globally — it is the service-layer
declaration of operational intent for Superadmin global operations.
"""
from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from app.core.identity.identity_scope import IdentityScope
from app.core.tenant.routing import OPERATION_CLASS_CONTROL_PLANE
from app.infrastructure.database.connection_async import DatabaseConnection

# Re-export for call sites: Platform global = non-row-scoped SQL (no ContextVar filter).
PLATFORM_GLOBAL_IDENTITY_SCOPE = IdentityScope.ENGINE_SCOPED


def kwargs_platform_global_read(
    *,
    client_id: Optional[UUID] = None,
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT,
) -> dict[str, Any]:
    """
    Kwargs for ``execute_query`` — Platform Admin global read.

    Use when SQL scope is defined in the query (or is a CP-wide listing) and
    must not receive automatic ``cliente_id = ContextVar`` injection.

    ``client_id`` when provided is used only for connection routing / explicit
    service filters, not for middleware-derived tenant enforcement.
    """
    kwargs: dict[str, Any] = {
        "identity_scope": PLATFORM_GLOBAL_IDENTITY_SCOPE,
        "client_id": client_id,
        "connection_type": connection_type,
    }
    if connection_type == DatabaseConnection.ADMIN:
        kwargs["operation_class"] = OPERATION_CLASS_CONTROL_PLANE
    return kwargs


def kwargs_platform_global_user_lookup(
    *,
    client_id: Optional[UUID] = None,
) -> dict[str, Any]:
    """
    Resolve ``usuario`` row for Platform Admin (identity store / shared tenant DB).

    ``usuario`` lives in tenant_data store, not CP ``cliente`` catalog — use DEFAULT
    routing with platform-global scope (no ContextVar filter).
    """
    return kwargs_platform_global_read(client_id=client_id)


def kwargs_control_plane_read(
    *,
    client_id: Optional[UUID] = None,
) -> dict[str, Any]:
    """Kwargs for queries against Control Plane store only (central BD / ADMIN)."""
    return kwargs_platform_global_read(
        client_id=client_id,
        connection_type=DatabaseConnection.ADMIN,
    )


def kwargs_control_plane_read(
    *,
    client_id: Optional[UUID] = None,
) -> dict[str, Any]:
    """Kwargs for queries against Control Plane store only (central BD / ADMIN)."""
    return kwargs_platform_global_read(
        client_id=client_id,
        connection_type=DatabaseConnection.ADMIN,
    )

