from app.core.identity.identity_context import IdentityContext
from app.core.identity.identity_scope import IdentityScope
from app.core.identity.identity_store_connection import OPERATION_CLASS_TENANT_IDENTITY

__all__ = [
    "IdentityContext",
    "IdentityGateway",
    "IdentityScope",
    "OPERATION_CLASS_TENANT_IDENTITY",
]


def __getattr__(name: str):
    if name == "IdentityGateway":
        from app.core.identity.identity_gateway import IdentityGateway

        return IdentityGateway
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
