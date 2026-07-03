"""
DedicatedProvisioningCompensationService — compensación saga S10→S3 (PR-F4-10).

Semi-automática: DROP DATABASE (S3), cleanup ``cliente_conexion`` (S8),
invalidación cache (S9). Abort y retry internos — sin HTTP (F4-11).
"""
from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from app.core.application.unit_of_work import UnitOfWork
from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.tenant.routing import invalidate_client_connection_cache
from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.repositories.tenant_provisioning_repository import (
    TenantProvisioningRepository,
)
from app.infrastructure.provisioning.dedicated_database_executor import (
    DedicatedDatabaseExecutor,
)
from app.infrastructure.provisioning.dedicated_database_types import (
    DedicatedDatabaseDropRequest,
)
from app.infrastructure.provisioning.dedicated_provisioning_compensation_types import (
    ProvisioningAbortResult,
    ProvisioningCompensationResult,
)
from app.infrastructure.provisioning.dedicated_storage_metadata_service import (
    DedicatedStorageMetadataService,
)
from app.modules.tenant.application.provisioning import (
    DEDICATED_INSTALLATION_TYPE,
    ProvisioningState,
    ProvisioningStepCode,
    ProvisioningStepStatus,
    SAGA_ORDER_BY_CODE,
)
from app.modules.tenant.application.provisioning.provisioning_state_result import (
    ProvisioningStateTransitionResult,
)
from app.modules.tenant.application.services.dedicated_provisioning_query_service import (
    DedicatedProvisioningQueryService,
)
from app.modules.tenant.application.services.provisioning_job_dispatcher import (
    ProvisioningJobDispatcher,
)
from app.modules.tenant.application.services.storage_allocation_types import (
    parse_storage_allocation_marker,
)
from app.modules.tenant.application.services.tenant_provisioning_state_service import (
    TenantProvisioningStateService,
)

logger = logging.getLogger(__name__)

_COMPENSATION_STEP_ORDER: tuple[ProvisioningStepCode, ...] = (
    ProvisioningStepCode.MARK_READY,
    ProvisioningStepCode.ACTIVATE_ROUTING,
    ProvisioningStepCode.REGISTER_METADATA,
    ProvisioningStepCode.SEED_TENANT,
    ProvisioningStepCode.APPLY_CATALOGS,
    ProvisioningStepCode.APPLY_SCHEMA_RBAC,
    ProvisioningStepCode.APPLY_SCHEMA_ERP,
    ProvisioningStepCode.CREATE_DATABASE,
)


class DedicatedProvisioningCompensationService:
    """Compensación fail-safe — solo tenants dedicated en ``failed``."""

    def __init__(
        self,
        *,
        state_service: Optional[TenantProvisioningStateService] = None,
        query_service: Optional[DedicatedProvisioningQueryService] = None,
        repository: Optional[TenantProvisioningRepository] = None,
        database_executor: Optional[DedicatedDatabaseExecutor] = None,
        metadata_service: Optional[DedicatedStorageMetadataService] = None,
        dispatcher: Optional[ProvisioningJobDispatcher] = None,
    ) -> None:
        self._state = state_service or TenantProvisioningStateService()
        self._query = query_service or DedicatedProvisioningQueryService()
        self._repo = repository or TenantProvisioningRepository()
        self._database_executor = database_executor or DedicatedDatabaseExecutor()
        self._metadata = metadata_service or DedicatedStorageMetadataService()
        self._dispatcher = dispatcher

    async def abort_provisioning_run(
        self,
        *,
        cliente_id: UUID,
        provisioning_run_id: UUID,
        reason: Optional[str] = None,
    ) -> ProvisioningAbortResult:
        """Abort seguro: ``provisioning`` → ``failed`` + compensación semi-auto."""
        if not settings.DEDICATED_ENABLED:
            raise ValidationError(
                detail="Dedicated provisioning deshabilitado en plataforma.",
                internal_code="PROVISIONING_DISABLED",
            )

        snapshot = await self._repo.get_cliente_provisioning_snapshot(cliente_id)
        if snapshot is None:
            raise NotFoundError(
                detail=f"Cliente {cliente_id} no encontrado.",
                internal_code="CLIENTE_NOT_FOUND",
            )
        self._assert_dedicated(snapshot)
        if snapshot.get("provisioning_state") == ProvisioningState.READY.value:
            raise ConflictError(
                detail="No se puede abortar un tenant dedicated en estado ready.",
                internal_code="PROVISIONING_COMPENSATION_NOT_ALLOWED",
            )
        if snapshot.get("provisioning_state") != ProvisioningState.PROVISIONING.value:
            raise ConflictError(
                detail=(
                    "Abort solo permitido cuando provisioning_state='provisioning'."
                ),
                internal_code="INVALID_PROVISIONING_STATE",
            )
        if snapshot.get("current_provisioning_run_id") != provisioning_run_id:
            raise NotFoundError(
                detail=f"Provisioning run {provisioning_run_id} no es el run activo.",
                internal_code="PROVISIONING_RUN_NOT_FOUND",
            )

        error_message = reason or "Provisioning abortado por operación interna."
        await self._state.transition_run_to_failed(
            cliente_id=cliente_id,
            provisioning_run_id=provisioning_run_id,
            error_code="PROVISIONING_ABORTED",
            error_message=error_message[:500],
        )
        compensation = await self.compensate_for_failed_run(
            cliente_id=cliente_id,
            provisioning_run_id=provisioning_run_id,
        )
        return ProvisioningAbortResult(
            cliente_id=cliente_id,
            provisioning_run_id=provisioning_run_id,
            compensation=compensation,
        )

    async def compensate_for_failed_run(
        self,
        *,
        cliente_id: UUID,
        provisioning_run_id: UUID,
    ) -> ProvisioningCompensationResult:
        """
        Compensación idempotente S10→S3 para runs ``failed`` / abortados.

        No afecta tenants shared ni runs ``ready``.
        """
        snapshot = await self._repo.get_cliente_provisioning_snapshot(cliente_id)
        if snapshot is None:
            raise NotFoundError(
                detail=f"Cliente {cliente_id} no encontrado.",
                internal_code="CLIENTE_NOT_FOUND",
            )
        self._assert_dedicated(snapshot)

        state_value = snapshot.get("provisioning_state")
        if state_value == ProvisioningState.READY.value:
            raise ConflictError(
                detail="Compensación prohibida para tenants en estado ready.",
                internal_code="PROVISIONING_COMPENSATION_NOT_ALLOWED",
            )
        if state_value != ProvisioningState.FAILED.value:
            raise ConflictError(
                detail=(
                    "Compensación solo permitida cuando provisioning_state='failed'."
                ),
                internal_code="INVALID_PROVISIONING_STATE",
            )
        if snapshot.get("current_provisioning_run_id") != provisioning_run_id:
            raise NotFoundError(
                detail=f"Provisioning run {provisioning_run_id} no es el run activo.",
                internal_code="PROVISIONING_RUN_NOT_FOUND",
            )

        steps = await self._repo.list_steps_for_run(provisioning_run_id, cliente_id)
        completed = self._completed_step_codes(steps)
        if not completed:
            return ProvisioningCompensationResult(
                cliente_id=cliente_id,
                provisioning_run_id=provisioning_run_id,
                steps_compensated=(),
                database_dropped=False,
                connection_deactivated=False,
                cache_invalidated=False,
                steps_reset_from_order=None,
                idempotent=True,
            )

        allocation = self._resolve_allocation_from_steps(steps)
        compensated: list[str] = []
        cache_invalidated = False
        connection_deactivated = False
        database_dropped = False
        reset_from_order: Optional[int] = None

        for step_code in _COMPENSATION_STEP_ORDER:
            if step_code not in completed:
                continue

            if step_code == ProvisioningStepCode.MARK_READY:
                compensated.append(step_code.value)
                continue

            if step_code == ProvisioningStepCode.ACTIVATE_ROUTING:
                invalidate_client_connection_cache(cliente_id)
                cache_invalidated = True
                compensated.append(step_code.value)
                reset_from_order = self._min_reset_order(
                    reset_from_order,
                    SAGA_ORDER_BY_CODE[step_code],
                )
                continue

            if step_code == ProvisioningStepCode.REGISTER_METADATA:
                deactivated = await self._metadata.cleanup_primary_connection(
                    cliente_id,
                )
                connection_deactivated = connection_deactivated or deactivated
                invalidate_client_connection_cache(cliente_id)
                cache_invalidated = True
                compensated.append(step_code.value)
                reset_from_order = self._min_reset_order(
                    reset_from_order,
                    SAGA_ORDER_BY_CODE[step_code],
                )
                continue

            if step_code == ProvisioningStepCode.CREATE_DATABASE:
                if allocation is None:
                    logger.warning(
                        "Compensación S3 omitida — allocation marker ausente run_id=%s",
                        provisioning_run_id,
                    )
                    continue
                drop_result = await self._database_executor.drop_physical_database(
                    DedicatedDatabaseDropRequest(
                        cliente_id=cliente_id,
                        database_name=allocation.database_name,
                        app_login_name=allocation.app_login_name,
                    ),
                )
                database_dropped = drop_result.database_dropped or drop_result.login_dropped
                compensated.append(step_code.value)
                reset_from_order = self._min_reset_order(
                    reset_from_order,
                    SAGA_ORDER_BY_CODE[step_code],
                )
                continue

            if step_code in {
                ProvisioningStepCode.APPLY_SCHEMA_ERP,
                ProvisioningStepCode.APPLY_SCHEMA_RBAC,
                ProvisioningStepCode.APPLY_CATALOGS,
                ProvisioningStepCode.SEED_TENANT,
            }:
                compensated.append(step_code.value)

        if reset_from_order is not None:
            await self._reset_provisioning_steps(
                cliente_id=cliente_id,
                provisioning_run_id=provisioning_run_id,
                from_saga_order=reset_from_order,
            )

        logger.info(
            "Compensación completed cliente_id=%s run_id=%s steps=%s reset_from=%s",
            cliente_id,
            provisioning_run_id,
            compensated,
            reset_from_order,
        )
        return ProvisioningCompensationResult(
            cliente_id=cliente_id,
            provisioning_run_id=provisioning_run_id,
            steps_compensated=tuple(compensated),
            database_dropped=database_dropped,
            connection_deactivated=connection_deactivated,
            cache_invalidated=cache_invalidated,
            steps_reset_from_order=reset_from_order,
            idempotent=not compensated,
        )

    async def retry_provisioning_run(
        self,
        *,
        cliente_id: UUID,
        provisioning_run_id: Optional[UUID] = None,
    ) -> tuple[ProvisioningStateTransitionResult, object]:
        """Retry seguro: ``failed`` → ``provisioning`` + dispatch saga."""
        if not settings.DEDICATED_ENABLED:
            raise ValidationError(
                detail="Dedicated provisioning deshabilitado en plataforma.",
                internal_code="PROVISIONING_DISABLED",
            )

        snapshot = await self._repo.get_cliente_provisioning_snapshot(cliente_id)
        if snapshot is None:
            raise NotFoundError(
                detail=f"Cliente {cliente_id} no encontrado.",
                internal_code="CLIENTE_NOT_FOUND",
            )
        self._assert_dedicated(snapshot)
        if snapshot.get("provisioning_state") == ProvisioningState.READY.value:
            raise ConflictError(
                detail="No se puede reintentar un tenant dedicated en estado ready.",
                internal_code="PROVISIONING_COMPENSATION_NOT_ALLOWED",
            )

        run_id = provisioning_run_id or snapshot.get("current_provisioning_run_id")
        if not run_id:
            raise NotFoundError(
                detail="No hay provisioning run asociado al tenant.",
                internal_code="PROVISIONING_RUN_NOT_FOUND",
            )

        transition = await self._state.begin_retry_from_failed(
            cliente_id=cliente_id,
            provisioning_run_id=run_id,
        )
        dispatcher = self._dispatcher or ProvisioningJobDispatcher(
            state_service=self._state,
            query_service=self._query,
        )
        dispatch_result = await dispatcher.dispatch_for_run(
            cliente_id=cliente_id,
            provisioning_run_id=run_id,
            trigger_source="retry",
        )
        return transition, dispatch_result

    async def _reset_provisioning_steps(
        self,
        *,
        cliente_id: UUID,
        provisioning_run_id: UUID,
        from_saga_order: int,
    ) -> None:
        async with UnitOfWork(
            client_id=cliente_id,
            connection_type=DatabaseConnection.ADMIN,
        ) as uow:
            await self._repo.reset_steps_from_order(
                provisioning_run_id=provisioning_run_id,
                cliente_id=cliente_id,
                from_saga_order=from_saga_order,
                session=uow.session,
            )

    @staticmethod
    def _assert_dedicated(snapshot: dict) -> None:
        if snapshot.get("tipo_instalacion") != DEDICATED_INSTALLATION_TYPE:
            raise ValidationError(
                detail="Compensación solo aplica a tenants dedicated.",
                internal_code="PROVISIONING_NOT_DEDICATED",
            )

    @staticmethod
    def _completed_step_codes(steps: list[dict]) -> set[ProvisioningStepCode]:
        completed: set[ProvisioningStepCode] = set()
        for row in steps:
            status = ProvisioningStepStatus(row["step_status"])
            if status in {
                ProvisioningStepStatus.COMPLETED,
                ProvisioningStepStatus.SKIPPED,
            }:
                completed.add(ProvisioningStepCode(row["step_code"]))
        return completed

    @staticmethod
    def _resolve_allocation_from_steps(steps: list[dict]):
        for row in steps:
            if row["step_code"] != ProvisioningStepCode.STORAGE_ALLOCATION.value:
                continue
            marker = row.get("idempotency_marker")
            if not marker:
                return None
            return parse_storage_allocation_marker(marker)
        return None

    @staticmethod
    def _min_reset_order(
        current: Optional[int],
        candidate: int,
    ) -> int:
        if current is None:
            return candidate
        return min(current, candidate)


__all__ = ["DedicatedProvisioningCompensationService"]
