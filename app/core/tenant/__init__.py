# app/core/tenant/__init__.py
"""
Módulo de multi-tenant: contexto, routing, cache, middleware
"""

from app.core.tenant.context import (
    TenantContext,
    get_current_client_id,
    get_tenant_context,
    try_get_current_client_id,
    try_get_tenant_context,
    get_database_type,
    get_database_name,
    set_tenant_context,
    reset_tenant_context
)

__all__ = [
    "TenantContext",
    "get_current_client_id",
    "get_tenant_context",
    "try_get_current_client_id",
    "try_get_tenant_context",
    "get_database_type",
    "get_database_name",
    "set_tenant_context",
    "reset_tenant_context"
]



