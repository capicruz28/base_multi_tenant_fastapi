"""F8-A — Resolución de scope RBAC sin ramas database_type en auth runtime."""
from __future__ import annotations

from app.core.identity.identity_gateway import IdentityGateway
from app.core.identity.identity_scope import IdentityScope


def resolve_rbac_database_type() -> str:
    """Mapea IdentityScope → valor legacy esperado por Permission/Menu Resolver."""
    if IdentityGateway.resolve_identity_scope() == IdentityScope.ENGINE_SCOPED:
        return "multi"
    return "single"


__all__ = ["resolve_rbac_database_type"]
