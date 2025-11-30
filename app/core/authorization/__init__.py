# app/core/authorization/__init__.py
"""
Módulo de autorización: RBAC y LBAC
"""

from app.core.authorization.rbac import (
    AuthorizationError,
    get_user_type,
    has_role,
    has_any_role,
    has_permission,
    has_any_permission,
    require_super_admin,
    require_tenant_admin,
    require_permission,
    require_any_permission,
    require_any_role
)

from app.core.authorization.lbac import (
    InsufficientAccessLevelError,
    SuperAdminRequiredError,
    TenantAccessError,
    require_access_level,
    require_super_admin as require_super_admin_lbac,
    require_tenant_admin as require_tenant_admin_lbac,
    validate_user_level,
    validate_tenant_access
)

__all__ = [
    # RBAC
    "AuthorizationError",
    "get_user_type",
    "has_role",
    "has_any_role",
    "has_permission",
    "has_any_permission",
    "require_super_admin",
    "require_tenant_admin",
    "require_permission",
    "require_any_permission",
    "require_any_role",
    # LBAC
    "InsufficientAccessLevelError",
    "SuperAdminRequiredError",
    "TenantAccessError",
    "require_access_level",
    "require_super_admin_lbac",
    "require_tenant_admin_lbac",
    "validate_user_level",
    "validate_tenant_access"
]



