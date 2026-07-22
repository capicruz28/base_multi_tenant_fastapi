"""
DedicatedActivationService — S8–S10 activación real (PR-F4-09).

S8: metadata CP vía DedicatedStorageMetadataService.
S9: invalidación cache + smoke routing fail-closed.
S10: marker del step (la transición READY es acto terminal del Orchestrator).
"""
from __future__ import annotations

import logging
from typing import Optional

from app.core.exceptions import ConflictError, CustomException, DatabaseError
from app.core.tenant.routing import (
    DEDICATED_ROUTE_FAIL_CLOSED,
    get_connection_metadata_async,
    invalidate_client_connection_cache,
)
from app.infrastructure.provisioning.dedicated_activation_types import (
    DedicatedActivationRequest,
    DedicatedActivationStepResult,
)
from app.infrastructure.provisioning.dedicated_storage_metadata_service import (
    DedicatedStorageMetadataService,
)
from app.infrastructure.provisioning.dedicated_storage_metadata_types import (
    DedicatedStorageMetadataRequest,
)
from app.modules.tenant.application.provisioning import ProvisioningState, ProvisioningStepCode
from app.modules.tenant.application.services.dedicated_provisioning_query_service import (
    DedicatedProvisioningQueryService,
)
from app.modules.tenant.application.services.tenant_provisioning_state_service import (
    TenantProvisioningStateService,
)

logger = logging.getLogger(__name__)

_S9_MARKER_PREFIX = "routing_smoke_v1"
_S10_MARKER_PREFIX = "ready_run"


class DedicatedActivationService:
    """Activación dedicated — metadata, routing smoke y Tenant Ready."""

    def __init__(
        self,
        *,
        metadata_service: Optional[DedicatedStorageMetadataService] = None,
        state_service: Optional[TenantProvisioningStateService] = None,
        query_service: Optional[DedicatedProvisioningQueryService] = None,
    ) -> None:
        self._metadata = metadata_service or DedicatedStorageMetadataService()
        self._state = state_service or TenantProvisioningStateService()
        self._query = query_service or DedicatedProvisioningQueryService()

    async def register_metadata(
        self,
        request: DedicatedActivationRequest,
    ) -> DedicatedActivationStepResult:
        try:
            result = await self._metadata.register_primary_connection(
                DedicatedStorageMetadataRequest(
                    cliente_id=request.cliente_id,
                    provisioning_run_id=request.provisioning_run_id,
                    servidor=request.servidor,
                    database_name=request.database_name,
                    app_login_name=request.app_login_name,
                    app_login_password=request.app_login_password,
                ),
            )
        except CustomException:
            raise
        except Exception as exc:
            raise ConflictError(
                detail="Error al registrar metadata de conexión dedicated.",
                internal_code="PROVISIONING_METADATA_FAILED",
            ) from exc

        return DedicatedActivationStepResult(
            step_code=ProvisioningStepCode.REGISTER_METADATA.value,
            idempotency_marker=str(result.conexion_id),
            idempotent=result.idempotent,
        )

    async def activate_routing(
        self,
        request: DedicatedActivationRequest,
    ) -> DedicatedActivationStepResult:
        try:
            invalidate_client_connection_cache(request.cliente_id)
            await self._smoke_validate_routing(request)
        except CustomException:
            raise
        except Exception as exc:
            raise ConflictError(
                detail="Smoke routing dedicated falló.",
                internal_code="PROVISIONING_ACTIVATION_FAILED",
            ) from exc

        marker = f"{_S9_MARKER_PREFIX}:{request.cliente_id}"
        return DedicatedActivationStepResult(
            step_code=ProvisioningStepCode.ACTIVATE_ROUTING.value,
            idempotency_marker=marker,
            idempotent=True,
        )

    async def mark_ready(
        self,
        request: DedicatedActivationRequest,
    ) -> DedicatedActivationStepResult:
        """S10 step body — no muta el estado del provisioning_run.

        La transición ``provisioning`` → ``ready`` es acto terminal del
        Orchestrator (simétrico con ``transition_run_to_failed``). Este step se
        limita a producir el marker idempotente del paso.
        """
        status = await self._query.get_provisioning_status(request.cliente_id)
        already_ready = (
            status is not None
            and status.provisioning_state == ProvisioningState.READY
            and status.provisioning_run_id == request.provisioning_run_id
        )
        if already_ready:
            logger.info(
                "S10 mark_ready idempotent skip cliente_id=%s run_id=%s",
                request.cliente_id,
                request.provisioning_run_id,
            )
        return DedicatedActivationStepResult(
            step_code=ProvisioningStepCode.MARK_READY.value,
            idempotency_marker=self._ready_marker(request),
            idempotent=already_ready,
        )

    async def _smoke_validate_routing(
        self,
        request: DedicatedActivationRequest,
    ) -> None:
        try:
            metadata = await get_connection_metadata_async(request.cliente_id)
        except DatabaseError as exc:
            if exc.internal_code == DEDICATED_ROUTE_FAIL_CLOSED:
                raise ConflictError(
                    detail=str(exc.detail),
                    internal_code="PROVISIONING_ACTIVATION_FAILED",
                ) from exc
            raise ConflictError(
                detail="Metadata de routing no disponible para smoke dedicated.",
                internal_code="PROVISIONING_ACTIVATION_FAILED",
            ) from exc

        if metadata.get("database_type") != "multi":
            raise ConflictError(
                detail=(
                    f"Smoke routing esperaba database_type=multi; "
                    f"recibido {metadata.get('database_type')!r}."
                ),
                internal_code="PROVISIONING_ACTIVATION_FAILED",
            )
        if metadata.get("tipo_instalacion") != "dedicated":
            raise ConflictError(
                detail="Smoke routing requiere tipo_instalacion=dedicated.",
                internal_code="PROVISIONING_ACTIVATION_FAILED",
            )

        for field, expected in (
            ("servidor", request.servidor),
            ("nombre_bd", request.database_name),
        ):
            actual = metadata.get(field)
            if actual != expected:
                raise ConflictError(
                    detail=(
                        f"Smoke routing mismatch en {field}: "
                        f"esperado {expected!r}, actual {actual!r}."
                    ),
                    internal_code="PROVISIONING_ACTIVATION_FAILED",
                )

        if not metadata.get("usuario") or not metadata.get("password"):
            raise ConflictError(
                detail="Smoke routing: credenciales Storage Endpoint incompletas.",
                internal_code="PROVISIONING_ACTIVATION_FAILED",
            )

    @staticmethod
    def _ready_marker(request: DedicatedActivationRequest) -> str:
        return f"{_S10_MARKER_PREFIX}:{request.provisioning_run_id}"


__all__ = ["DedicatedActivationService"]
