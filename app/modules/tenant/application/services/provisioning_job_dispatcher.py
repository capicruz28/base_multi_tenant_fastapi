"""
Dispatcher in-process — Dedicated provisioning jobs (PR-F4-03).

Encola ejecución async sin bloquear al caller. Integración con
``TenantProvisioningStateService`` vía ``dispatch_after_initialize``.

La saga S1–S10 se conectará en F4-08 como ``ProvisioningJobHandler``.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Optional, Set
from uuid import UUID

from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.modules.tenant.application.provisioning import ProvisioningState
from app.modules.tenant.application.provisioning.provisioning_job_contracts import (
    ProvisioningJobDispatchResult,
    ProvisioningJobHandlerCallable,
    ProvisioningJobRequest,
)
from app.modules.tenant.application.provisioning.provisioning_saga_ephemeral_context import (
    ProvisioningSagaEphemeralContext,
)
from app.modules.tenant.application.provisioning.provisioning_state_result import (
    ProvisioningRunInitializedResult,
)
from app.modules.tenant.application.services.dedicated_provisioning_query_service import (
    DedicatedProvisioningQueryService,
)
from app.modules.tenant.application.services.tenant_provisioning_state_service import (
    TenantProvisioningStateService,
)

logger = logging.getLogger(__name__)

_active_tasks: Set[asyncio.Task] = set()
_active_run_ids: Set[UUID] = set()


async def _default_provisioning_job_handler(job: ProvisioningJobRequest) -> None:
    from app.modules.tenant.application.services.dedicated_provisioning_orchestrator import (
        create_default_provisioning_job_handler,
    )

    handler = create_default_provisioning_job_handler()
    await handler(job)


def _track_task(task: asyncio.Task, *, provisioning_run_id: UUID) -> None:
    _active_tasks.add(task)
    _active_run_ids.add(provisioning_run_id)

    def _done_callback(finished: asyncio.Task) -> None:
        _active_tasks.discard(finished)
        _active_run_ids.discard(provisioning_run_id)
        try:
            finished.result()
        except asyncio.CancelledError:
            logger.debug("Provisioning job task cancelled run_id=%s", finished.get_name())
        except Exception:
            logger.exception(
                "[F4-DIAG] ProvisioningJobDispatcher task excepcion_completa "
                "task_name=%s run_id=%s",
                finished.get_name(),
                provisioning_run_id,
            )
            logger.exception(
                "Unhandled error in provisioning job task name=%s",
                finished.get_name(),
            )

    task.add_done_callback(_done_callback)


class ProvisioningJobDispatcher:
    """Despacho in-process post-inicialización de run (ADR-F4-05)."""

    def __init__(
        self,
        *,
        query_service: Optional[DedicatedProvisioningQueryService] = None,
        state_service: Optional[TenantProvisioningStateService] = None,
        default_handler: Optional[ProvisioningJobHandlerCallable] = None,
    ) -> None:
        self._query = query_service or DedicatedProvisioningQueryService()
        self._state = state_service or TenantProvisioningStateService()
        self._default_handler = default_handler or _default_provisioning_job_handler

    @staticmethod
    def pending_task_count() -> int:
        return len(_active_tasks)

    @staticmethod
    def active_run_count() -> int:
        return len(_active_run_ids)

    @staticmethod
    async def drain_pending_jobs(timeout_seconds: float = 5.0) -> None:
        """Espera tasks in-process — uso tests/diagnostics."""
        if not _active_tasks:
            return
        pending = list(_active_tasks)
        await asyncio.wait(pending, timeout=timeout_seconds)

    async def dispatch(
        self,
        job: ProvisioningJobRequest,
        *,
        handler: Optional[ProvisioningJobHandlerCallable] = None,
    ) -> ProvisioningJobDispatchResult:
        """
        Encola job sin bloquear al caller.

        Valida que el run exista y esté en ``provisioning`` antes de encolar.
        """
        logger.warning(
            "[F4-DIAG] ProvisioningJobDispatcher.dispatch solicitado "
            "cliente_id=%s run_id=%s trigger_source=%s "
            "PROVISIONING_DISPATCHER_ENABLED=%s PROVISIONING_DISPATCHER_SYNC=%s "
            "active_run_ids=%s",
            job.cliente_id,
            job.provisioning_run_id,
            job.trigger_source,
            settings.PROVISIONING_DISPATCHER_ENABLED,
            settings.PROVISIONING_DISPATCHER_SYNC,
            sorted(str(rid) for rid in _active_run_ids),
        )
        if not job.cliente_id or not job.provisioning_run_id:
            raise ValidationError(
                detail="cliente_id y provisioning_run_id son obligatorios para despacho.",
                internal_code="INVALID_PROVISIONING_JOB",
            )

        await self._assert_run_dispatchable(
            job.cliente_id,
            job.provisioning_run_id,
        )

        if job.provisioning_run_id in _active_run_ids:
            logger.warning(
                "[F4-DIAG] ProvisioningJobDispatcher.dispatch dispatched=false "
                "motivo=active_run_ids_dedupe run_id=%s active_run_ids=%s",
                job.provisioning_run_id,
                sorted(str(rid) for rid in _active_run_ids),
            )
            logger.info(
                "Provisioning job deduped — run already active run_id=%s",
                job.provisioning_run_id,
            )
            return ProvisioningJobDispatchResult(
                cliente_id=job.cliente_id,
                provisioning_run_id=job.provisioning_run_id,
                dispatched=False,
                sync_execution=False,
                dispatcher_enabled=True,
                enqueued_at=job.enqueued_at or datetime.utcnow(),
            )

        enqueued_at = job.enqueued_at or datetime.utcnow()
        normalized = ProvisioningJobRequest(
            cliente_id=job.cliente_id,
            provisioning_run_id=job.provisioning_run_id,
            idempotency_key=job.idempotency_key,
            enqueued_at=enqueued_at,
            trigger_source=job.trigger_source,
            ephemeral_context=job.ephemeral_context,
        )

        if not settings.PROVISIONING_DISPATCHER_ENABLED:
            logger.warning(
                "[F4-DIAG] ProvisioningJobDispatcher.dispatch dispatched=false "
                "motivo=PROVISIONING_DISPATCHER_ENABLED_false run_id=%s",
                normalized.provisioning_run_id,
            )
            logger.info(
                "Provisioning dispatcher disabled — job not enqueued run_id=%s",
                normalized.provisioning_run_id,
            )
            return ProvisioningJobDispatchResult(
                cliente_id=normalized.cliente_id,
                provisioning_run_id=normalized.provisioning_run_id,
                dispatched=False,
                sync_execution=False,
                dispatcher_enabled=False,
                enqueued_at=enqueued_at,
            )

        job_handler = handler or self._default_handler
        sync_mode = settings.PROVISIONING_DISPATCHER_SYNC

        if sync_mode:
            logger.warning(
                "[F4-DIAG] ProvisioningJobDispatcher.dispatch sync_mode=true "
                "run_id=%s — ejecutando handler inline",
                normalized.provisioning_run_id,
            )
            _active_run_ids.add(normalized.provisioning_run_id)
            try:
                await job_handler(normalized)
            finally:
                _active_run_ids.discard(normalized.provisioning_run_id)
            result = ProvisioningJobDispatchResult(
                cliente_id=normalized.cliente_id,
                provisioning_run_id=normalized.provisioning_run_id,
                dispatched=True,
                sync_execution=True,
                dispatcher_enabled=True,
                enqueued_at=enqueued_at,
            )
            logger.warning(
                "[F4-DIAG] ProvisioningJobDispatcher.dispatch result "
                "dispatched=%s sync_execution=%s run_id=%s",
                result.dispatched,
                result.sync_execution,
                result.provisioning_run_id,
            )
            return result

        logger.warning(
            "[F4-DIAG] ProvisioningJobDispatcher.dispatch antes create_task "
            "run_id=%s",
            normalized.provisioning_run_id,
        )
        task = asyncio.create_task(
            job_handler(normalized),
            name=f"provisioning-{normalized.provisioning_run_id}",
        )
        logger.warning(
            "[F4-DIAG] ProvisioningJobDispatcher.dispatch despues create_task "
            "task_name=%s task_done=%s run_id=%s",
            task.get_name(),
            task.done(),
            normalized.provisioning_run_id,
        )
        if task.done():
            try:
                task.result()
            except Exception:
                logger.exception(
                    "[F4-DIAG] ProvisioningJobDispatcher.dispatch excepcion_inmediata "
                    "task_name=%s run_id=%s",
                    task.get_name(),
                    normalized.provisioning_run_id,
                )
        _track_task(task, provisioning_run_id=normalized.provisioning_run_id)

        result = ProvisioningJobDispatchResult(
            cliente_id=normalized.cliente_id,
            provisioning_run_id=normalized.provisioning_run_id,
            dispatched=True,
            sync_execution=False,
            dispatcher_enabled=True,
            enqueued_at=enqueued_at,
        )
        logger.warning(
            "[F4-DIAG] ProvisioningJobDispatcher.dispatch result "
            "dispatched=%s sync_execution=%s run_id=%s active_run_ids=%s",
            result.dispatched,
            result.sync_execution,
            result.provisioning_run_id,
            sorted(str(rid) for rid in _active_run_ids),
        )
        return result

    async def dispatch_for_run(
        self,
        *,
        cliente_id: UUID,
        provisioning_run_id: UUID,
        idempotency_key: Optional[str] = None,
        trigger_source: str = "internal",
        handler: Optional[ProvisioningJobHandlerCallable] = None,
    ) -> ProvisioningJobDispatchResult:
        job = ProvisioningJobRequest(
            cliente_id=cliente_id,
            provisioning_run_id=provisioning_run_id,
            idempotency_key=idempotency_key,
            trigger_source=trigger_source,
        )
        return await self.dispatch(job, handler=handler)

    async def dispatch_after_initialize(
        self,
        init_result: ProvisioningRunInitializedResult,
        *,
        handler: Optional[ProvisioningJobHandlerCallable] = None,
        trigger_source: str = "post_initialize",
        ephemeral_context: Optional[ProvisioningSagaEphemeralContext] = None,
    ) -> ProvisioningJobDispatchResult:
        """Integración F4-02 → F4-03: despacha tras ``initialize_provisioning_run``."""
        job = ProvisioningJobRequest(
            cliente_id=init_result.cliente_id,
            provisioning_run_id=init_result.provisioning_run_id,
            idempotency_key=init_result.idempotency_key,
            trigger_source=trigger_source,
            ephemeral_context=ephemeral_context,
        )
        return await self.dispatch(job, handler=handler)

    async def initialize_and_dispatch(
        self,
        *,
        cliente_id: UUID,
        idempotency_key: Optional[str] = None,
        created_by_usuario_id: Optional[UUID] = None,
        handler: Optional[ProvisioningJobHandlerCallable] = None,
        trigger_source: str = "initialize_and_dispatch",
    ) -> tuple[ProvisioningRunInitializedResult, ProvisioningJobDispatchResult]:
        """
        Atajo interno: crea run vía state service y encola job.

        **No** invocar desde HTTP — wiring HTTP queda en F4-08.
        """
        init_result = await self._state.initialize_provisioning_run(
            cliente_id=cliente_id,
            idempotency_key=idempotency_key,
            created_by_usuario_id=created_by_usuario_id,
        )
        dispatch_result = await self.dispatch_after_initialize(
            init_result,
            handler=handler,
            trigger_source=trigger_source,
        )
        return init_result, dispatch_result

    async def _assert_run_dispatchable(
        self,
        cliente_id: UUID,
        provisioning_run_id: UUID,
    ) -> None:
        status = await self._query.get_provisioning_status(cliente_id)
        if status is None:
            raise NotFoundError(
                detail=f"Cliente {cliente_id} no encontrado.",
                internal_code="CLIENTE_NOT_FOUND",
            )
        if status.provisioning_run_id != provisioning_run_id:
            raise NotFoundError(
                detail=(
                    f"Provisioning run {provisioning_run_id} no es el run "
                    f"activo del tenant."
                ),
                internal_code="PROVISIONING_RUN_NOT_FOUND",
            )
        if status.provisioning_state != ProvisioningState.PROVISIONING:
            raise ConflictError(
                detail=(
                    "Solo se pueden despachar jobs cuando "
                    f"provisioning_state='{ProvisioningState.PROVISIONING.value}'."
                ),
                internal_code="PROVISIONING_RUN_NOT_DISPATCHABLE",
            )


__all__ = [
    "ProvisioningJobDispatcher",
    "drain_pending_jobs",
    "pending_task_count",
]

# Re-export helpers for tests
drain_pending_jobs = ProvisioningJobDispatcher.drain_pending_jobs
pending_task_count = ProvisioningJobDispatcher.pending_task_count
