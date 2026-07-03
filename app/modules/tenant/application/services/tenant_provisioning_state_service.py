"""
Servicio de mutación — estado provisioning Dedicated (PR-F4-02).

CRUD de estado, transiciones guardadas e historial de steps.
Sin orquestación saga, workers ni endpoints públicos.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.core.application.unit_of_work import UnitOfWork
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.queries.tenant.provisioning import (
    tenant_provisioning_run_queries_core as runq,
    tenant_provisioning_transaction_core as ptx,
)
from app.infrastructure.database.repositories.tenant_provisioning_repository import (
    TenantProvisioningRepository,
)
from app.modules.tenant.application.provisioning import (
    DEDICATED_INSTALLATION_TYPE,
    ProvisioningState,
    ProvisioningStepCode,
    ProvisioningStepStatus,
    assert_provisioning_state_transition,
    assert_step_status_transition,
)
from app.modules.tenant.application.provisioning.provisioning_state_result import (
    ProvisioningRunInitializedResult,
    ProvisioningStateTransitionResult,
    ProvisioningStepTransitionResult,
)

logger = logging.getLogger(__name__)


class TenantProvisioningStateService:
    """API interna de escritura — consumida por orchestrator F4-08+."""

    def __init__(
        self,
        repository: Optional[TenantProvisioningRepository] = None,
    ) -> None:
        self._repo = repository or TenantProvisioningRepository()

    @staticmethod
    def _parse_run_state(row: dict) -> ProvisioningState:
        return ProvisioningState(row["provisioning_state"])

    @staticmethod
    def _parse_step_status(row: dict) -> ProvisioningStepStatus:
        return ProvisioningStepStatus(row["step_status"])

    async def _get_cliente_or_raise(self, cliente_id: UUID) -> dict:
        snapshot = await self._repo.get_cliente_provisioning_snapshot(cliente_id)
        if not snapshot:
            raise NotFoundError(
                detail=f"Cliente {cliente_id} no encontrado.",
                internal_code="CLIENTE_NOT_FOUND",
            )
        return snapshot

    @staticmethod
    def _assert_dedicated_cliente(snapshot: dict) -> None:
        if snapshot["tipo_instalacion"] != DEDICATED_INSTALLATION_TYPE:
            raise ValidationError(
                detail=(
                    "Provisioning automático solo aplica a tenants "
                    f"tipo_instalacion='{DEDICATED_INSTALLATION_TYPE}'."
                ),
                internal_code="PROVISIONING_NOT_DEDICATED",
            )

    async def _assert_no_active_provisioning(self, cliente_id: UUID) -> None:
        current = await self._repo.get_current_run(cliente_id)
        if current and self._parse_run_state(current) == ProvisioningState.PROVISIONING:
            raise ConflictError(
                detail="Ya existe una saga de provisioning activa para este tenant.",
                internal_code="PROVISIONING_ALREADY_ACTIVE",
            )

    async def initialize_provisioning_run(
        self,
        *,
        cliente_id: UUID,
        idempotency_key: Optional[str] = None,
        created_by_usuario_id: Optional[UUID] = None,
    ) -> ProvisioningRunInitializedResult:
        """
        Crea run + 10 steps pending + denormaliza cliente en ``provisioning``.

        Idempotente por ``idempotency_key`` cuando se repite POST /clientes/.
        """
        snapshot = await self._get_cliente_or_raise(cliente_id)
        self._assert_dedicated_cliente(snapshot)

        if idempotency_key:
            existing = await self._repo.get_run_by_idempotency_key(
                cliente_id,
                idempotency_key,
            )
            if existing:
                return ProvisioningRunInitializedResult(
                    provisioning_run_id=existing["provisioning_run_id"],
                    cliente_id=cliente_id,
                    provisioning_state=self._parse_run_state(existing),
                    attempt_number=int(existing["attempt_number"]),
                    idempotency_key=idempotency_key,
                )

        current_state = snapshot.get("provisioning_state")
        if current_state == ProvisioningState.READY.value:
            raise ConflictError(
                detail="El tenant dedicated ya está en estado ready.",
                internal_code="PROVISIONING_ALREADY_READY",
            )
        if current_state == ProvisioningState.FAILED.value:
            raise ConflictError(
                detail=(
                    "El tenant está en failed. Use begin_retry_from_failed "
                    "en lugar de initialize_provisioning_run."
                ),
                internal_code="PROVISIONING_USE_RETRY",
            )
        await self._assert_no_active_provisioning(cliente_id)

        run_values = runq.build_run_insert_values(
            cliente_id=cliente_id,
            provisioning_state=ProvisioningState.PROVISIONING,
            idempotency_key=idempotency_key,
            created_by_usuario_id=created_by_usuario_id,
            current_step_code=ProvisioningStepCode.REGISTRY.value,
        )
        run_id = run_values["provisioning_run_id"]

        async with UnitOfWork(
            client_id=cliente_id,
            connection_type=DatabaseConnection.ADMIN,
        ) as uow:
            await self._repo.deactivate_current_runs(cliente_id, session=uow.session)
            await self._repo.insert_run(
                run_values,
                session=uow.session,
                cliente_id=cliente_id,
            )
            await self._repo.insert_initial_steps_for_run(
                run_id,
                cliente_id,
                session=uow.session,
            )
            await self._repo.update_cliente_provisioning_state(
                cliente_id=cliente_id,
                tipo_instalacion=snapshot["tipo_instalacion"],
                provisioning_state=ProvisioningState.PROVISIONING,
                current_provisioning_run_id=run_id,
                session=uow.session,
            )

        logger.info(
            "Provisioning run initialized cliente_id=%s run_id=%s",
            cliente_id,
            run_id,
        )
        return ProvisioningRunInitializedResult(
            provisioning_run_id=run_id,
            cliente_id=cliente_id,
            provisioning_state=ProvisioningState.PROVISIONING,
            attempt_number=int(run_values["attempt_number"]),
            idempotency_key=idempotency_key,
        )

    async def begin_retry_from_failed(
        self,
        *,
        cliente_id: UUID,
        provisioning_run_id: Optional[UUID] = None,
    ) -> ProvisioningStateTransitionResult:
        """Transición ``failed`` → ``provisioning`` con reset de steps incompletos."""
        snapshot = await self._get_cliente_or_raise(cliente_id)
        self._assert_dedicated_cliente(snapshot)

        run_id = provisioning_run_id or snapshot.get("current_provisioning_run_id")
        if not run_id:
            raise NotFoundError(
                detail="No hay provisioning run asociado al tenant.",
                internal_code="PROVISIONING_RUN_NOT_FOUND",
            )

        async with UnitOfWork(
            client_id=cliente_id,
            connection_type=DatabaseConnection.ADMIN,
        ) as uow:
            locked = await ptx.lock_provisioning_run_tx(
                uow,
                provisioning_run_id=run_id,
                cliente_id=cliente_id,
            )
            if not locked:
                raise NotFoundError(
                    detail=f"Provisioning run {run_id} no encontrado.",
                    internal_code="PROVISIONING_RUN_NOT_FOUND",
                )

            current = self._parse_run_state(locked)
            assert_provisioning_state_transition(
                current,
                ProvisioningState.PROVISIONING,
            )

            steps = await self._repo.list_steps_for_run(
                run_id,
                cliente_id,
                session=uow.session,
            )
            resume_order = _first_incomplete_saga_order(steps)
            if resume_order is not None:
                await self._repo.reset_steps_from_order(
                    provisioning_run_id=run_id,
                    cliente_id=cliente_id,
                    from_saga_order=resume_order,
                    session=uow.session,
                )

            next_attempt = int(locked["attempt_number"]) + 1
            await self._repo.increment_run_attempt(
                provisioning_run_id=run_id,
                cliente_id=cliente_id,
                attempt_number=next_attempt,
                session=uow.session,
            )
            affected = await self._repo.update_run_state(
                provisioning_run_id=run_id,
                cliente_id=cliente_id,
                current_state=current,
                target_state=ProvisioningState.PROVISIONING,
                session=uow.session,
            )
            if affected != 1:
                raise ConflictError(
                    detail="Conflicto concurrente al reintentar provisioning.",
                    internal_code="PROVISIONING_RETRY_CONFLICT",
                )
            await self._repo.update_cliente_provisioning_state(
                cliente_id=cliente_id,
                tipo_instalacion=snapshot["tipo_instalacion"],
                provisioning_state=ProvisioningState.PROVISIONING,
                current_provisioning_run_id=run_id,
                session=uow.session,
            )

        updated_at = datetime.utcnow()
        return ProvisioningStateTransitionResult(
            provisioning_run_id=run_id,
            cliente_id=cliente_id,
            previous_state=current,
            current_state=ProvisioningState.PROVISIONING,
            updated_at=updated_at,
        )

    async def transition_run_to_ready(
        self,
        *,
        cliente_id: UUID,
        provisioning_run_id: UUID,
    ) -> ProvisioningStateTransitionResult:
        """``provisioning`` → ``ready`` — guard único pre-Tenant Ready (F4-09)."""
        snapshot = await self._get_cliente_or_raise(cliente_id)
        ready_at = datetime.utcnow()

        async with UnitOfWork(
            client_id=cliente_id,
            connection_type=DatabaseConnection.ADMIN,
        ) as uow:
            locked = await ptx.lock_provisioning_run_tx(
                uow,
                provisioning_run_id=provisioning_run_id,
                cliente_id=cliente_id,
            )
            if not locked:
                raise NotFoundError(
                    detail=f"Provisioning run {provisioning_run_id} no encontrado.",
                    internal_code="PROVISIONING_RUN_NOT_FOUND",
                )

            current = self._parse_run_state(locked)
            assert_provisioning_state_transition(current, ProvisioningState.READY)

            affected = await self._repo.update_run_state(
                provisioning_run_id=provisioning_run_id,
                cliente_id=cliente_id,
                current_state=current,
                target_state=ProvisioningState.READY,
                ready_at=ready_at,
                current_step_code=ProvisioningStepCode.MARK_READY.value,
                session=uow.session,
            )
            if affected != 1:
                raise ConflictError(
                    detail="Conflicto concurrente al marcar provisioning ready.",
                    internal_code="PROVISIONING_READY_CONFLICT",
                )
            await self._repo.update_cliente_provisioning_state(
                cliente_id=cliente_id,
                tipo_instalacion=snapshot["tipo_instalacion"],
                provisioning_state=ProvisioningState.READY,
                current_provisioning_run_id=provisioning_run_id,
                session=uow.session,
            )

        return ProvisioningStateTransitionResult(
            provisioning_run_id=provisioning_run_id,
            cliente_id=cliente_id,
            previous_state=current,
            current_state=ProvisioningState.READY,
            updated_at=ready_at,
        )

    async def transition_run_to_failed(
        self,
        *,
        cliente_id: UUID,
        provisioning_run_id: UUID,
        error_code: str,
        error_message: str,
        current_step_code: Optional[ProvisioningStepCode] = None,
    ) -> ProvisioningStateTransitionResult:
        """``provisioning`` → ``failed``."""
        snapshot = await self._get_cliente_or_raise(cliente_id)
        failed_at = datetime.utcnow()

        async with UnitOfWork(
            client_id=cliente_id,
            connection_type=DatabaseConnection.ADMIN,
        ) as uow:
            locked = await ptx.lock_provisioning_run_tx(
                uow,
                provisioning_run_id=provisioning_run_id,
                cliente_id=cliente_id,
            )
            if not locked:
                raise NotFoundError(
                    detail=f"Provisioning run {provisioning_run_id} no encontrado.",
                    internal_code="PROVISIONING_RUN_NOT_FOUND",
                )

            current = self._parse_run_state(locked)
            assert_provisioning_state_transition(current, ProvisioningState.FAILED)

            affected = await self._repo.update_run_state(
                provisioning_run_id=provisioning_run_id,
                cliente_id=cliente_id,
                current_state=current,
                target_state=ProvisioningState.FAILED,
                failed_at=failed_at,
                last_error_code=error_code,
                last_error_message=error_message,
                current_step_code=(
                    current_step_code.value if current_step_code else locked.get("current_step_code")
                ),
                session=uow.session,
            )
            if affected != 1:
                raise ConflictError(
                    detail="Conflicto concurrente al marcar provisioning failed.",
                    internal_code="PROVISIONING_FAILED_CONFLICT",
                )
            await self._repo.update_cliente_provisioning_state(
                cliente_id=cliente_id,
                tipo_instalacion=snapshot["tipo_instalacion"],
                provisioning_state=ProvisioningState.FAILED,
                current_provisioning_run_id=provisioning_run_id,
                session=uow.session,
            )

        return ProvisioningStateTransitionResult(
            provisioning_run_id=provisioning_run_id,
            cliente_id=cliente_id,
            previous_state=current,
            current_state=ProvisioningState.FAILED,
            updated_at=failed_at,
        )

    async def mark_step_running(
        self,
        *,
        cliente_id: UUID,
        provisioning_run_id: UUID,
        step_code: ProvisioningStepCode,
    ) -> ProvisioningStepTransitionResult:
        return await self._transition_step(
            cliente_id=cliente_id,
            provisioning_run_id=provisioning_run_id,
            step_code=step_code,
            target_status=ProvisioningStepStatus.RUNNING,
            started_at=datetime.utcnow(),
            update_run_current_step=step_code,
        )

    async def mark_step_completed(
        self,
        *,
        cliente_id: UUID,
        provisioning_run_id: UUID,
        step_code: ProvisioningStepCode,
        idempotency_marker: Optional[str] = None,
    ) -> ProvisioningStepTransitionResult:
        return await self._transition_step(
            cliente_id=cliente_id,
            provisioning_run_id=provisioning_run_id,
            step_code=step_code,
            target_status=ProvisioningStepStatus.COMPLETED,
            completed_at=datetime.utcnow(),
            idempotency_marker=idempotency_marker,
            update_run_current_step=step_code,
        )

    async def mark_step_failed(
        self,
        *,
        cliente_id: UUID,
        provisioning_run_id: UUID,
        step_code: ProvisioningStepCode,
        error_code: str,
        error_message: str,
    ) -> ProvisioningStepTransitionResult:
        return await self._transition_step(
            cliente_id=cliente_id,
            provisioning_run_id=provisioning_run_id,
            step_code=step_code,
            target_status=ProvisioningStepStatus.FAILED,
            completed_at=datetime.utcnow(),
            error_code=error_code,
            error_message=error_message,
            update_run_current_step=step_code,
        )

    async def mark_step_skipped(
        self,
        *,
        cliente_id: UUID,
        provisioning_run_id: UUID,
        step_code: ProvisioningStepCode,
    ) -> ProvisioningStepTransitionResult:
        return await self._transition_step(
            cliente_id=cliente_id,
            provisioning_run_id=provisioning_run_id,
            step_code=step_code,
            target_status=ProvisioningStepStatus.SKIPPED,
            completed_at=datetime.utcnow(),
            update_run_current_step=step_code,
        )

    async def _transition_step(
        self,
        *,
        cliente_id: UUID,
        provisioning_run_id: UUID,
        step_code: ProvisioningStepCode,
        target_status: ProvisioningStepStatus,
        update_run_current_step: Optional[ProvisioningStepCode] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        idempotency_marker: Optional[str] = None,
    ) -> ProvisioningStepTransitionResult:
        async with UnitOfWork(
            client_id=cliente_id,
            connection_type=DatabaseConnection.ADMIN,
        ) as uow:
            locked = await ptx.lock_provisioning_run_tx(
                uow,
                provisioning_run_id=provisioning_run_id,
                cliente_id=cliente_id,
            )
            if not locked:
                raise NotFoundError(
                    detail=f"Provisioning run {provisioning_run_id} no encontrado.",
                    internal_code="PROVISIONING_RUN_NOT_FOUND",
                )
            if self._parse_run_state(locked) != ProvisioningState.PROVISIONING:
                raise ConflictError(
                    detail=(
                        "No se puede mutar steps cuando el run no está en provisioning."
                    ),
                    internal_code="PROVISIONING_RUN_NOT_ACTIVE",
                )

            step_row = await self._repo.get_step_by_code(
                provisioning_run_id,
                cliente_id,
                step_code.value,
                session=uow.session,
            )
            if not step_row:
                raise NotFoundError(
                    detail=f"Step '{step_code.value}' no encontrado en el run.",
                    internal_code="PROVISIONING_STEP_NOT_FOUND",
                )

            current_status = self._parse_step_status(step_row)
            assert_step_status_transition(current_status, target_status)

            affected = await self._repo.update_step_status(
                provisioning_step_id=step_row["provisioning_step_id"],
                provisioning_run_id=provisioning_run_id,
                cliente_id=cliente_id,
                target_status=target_status,
                expected_status=current_status,
                started_at=started_at,
                completed_at=completed_at,
                error_code=error_code,
                error_message=error_message,
                idempotency_marker=idempotency_marker,
                session=uow.session,
            )
            if affected != 1:
                raise ConflictError(
                    detail=(
                        f"Conflicto concurrente al actualizar step '{step_code.value}'."
                    ),
                    internal_code="PROVISIONING_STEP_CONFLICT",
                )

            if update_run_current_step is not None:
                step_affected = await self._repo.update_run_current_step(
                    provisioning_run_id=provisioning_run_id,
                    cliente_id=cliente_id,
                    current_step_code=update_run_current_step.value,
                    session=uow.session,
                )
                if step_affected != 1:
                    raise ConflictError(
                        detail="Run no está activo para actualizar current_step.",
                        internal_code="PROVISIONING_RUN_STEP_POINTER_CONFLICT",
                    )

        updated_at = datetime.utcnow()
        return ProvisioningStepTransitionResult(
            provisioning_run_id=provisioning_run_id,
            cliente_id=cliente_id,
            step_code=step_code,
            previous_status=current_status.value,
            current_status=target_status.value,
            updated_at=updated_at,
        )


def _first_incomplete_saga_order(steps: list[dict]) -> Optional[int]:
    for step in sorted(steps, key=lambda row: int(row["saga_order"])):
        status = ProvisioningStepStatus(step["step_status"])
        if status not in {
            ProvisioningStepStatus.COMPLETED,
            ProvisioningStepStatus.SKIPPED,
        }:
            return int(step["saga_order"])
    return None


__all__ = ["TenantProvisioningStateService"]
