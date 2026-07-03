"""StorageAllocationService — identidad almacén S2 (PR-F4-08 / H-04)."""
from __future__ import annotations

from app.core.config import settings
from app.core.exceptions import ValidationError
from app.infrastructure.provisioning.dedicated_database_naming import (
    build_dedicated_app_login_name,
    build_dedicated_database_name,
)
from app.modules.tenant.application.services.storage_allocation_types import (
    StorageAllocationRequest,
    StorageAllocationResult,
)


class StorageAllocationService:
    """Asignación determinística servidor + nombres BD/login (CP lógico)."""

    def allocate(self, request: StorageAllocationRequest) -> StorageAllocationResult:
        servidor = settings.PROVISIONING_DDL_SERVER
        if not servidor:
            raise ValidationError(
                detail="servidor SQL no configurado para provisioning DDL.",
                internal_code="PROVISIONING_DDL_SERVER_MISSING",
            )
        database_name = build_dedicated_database_name(
            request.codigo_cliente,
            cliente_id=request.cliente_id,
        )
        app_login_name = build_dedicated_app_login_name(
            request.codigo_cliente,
            cliente_id=request.cliente_id,
        )
        return StorageAllocationResult(
            servidor=servidor,
            database_name=database_name,
            app_login_name=app_login_name,
        )


__all__ = ["StorageAllocationService"]
