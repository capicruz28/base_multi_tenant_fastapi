"""
DedicatedProvisioningOrchestrator — saga S1–S10 (PR-F4-08 / F4-09 / F4-10).

Coordinador delgado: estado CP vía TenantProvisioningStateService;
ejecución DP vía servicios F4-04…F4-07; activación S8–S10; compensación F4-10.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import text

from app.core.config import settings
from app.core.exceptions import ConflictError, CustomException, NotFoundError, ValidationError
from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.queries_async import execute_query
from app.infrastructure.database.repositories.tenant_provisioning_repository import (
    TenantProvisioningRepository,
)
from app.infrastructure.provisioning.bootstrap_applied_reader import BootstrapAppliedReader
from app.infrastructure.provisioning.bootstrap_script_runner import BootstrapScriptRunner
from app.infrastructure.provisioning.bootstrap_script_types import BootstrapScriptRunRequest
from app.infrastructure.provisioning.dedicated_activation_service import (
    DedicatedActivationService,
)
from app.infrastructure.provisioning.dedicated_activation_types import (
    DedicatedActivationRequest,
)
from app.infrastructure.provisioning.dedicated_catalog_seed_service import (
    DedicatedCatalogSeedService,
)
from app.infrastructure.provisioning.dedicated_catalog_seed_types import (
    DedicatedCatalogSeedRequest,
)
from app.infrastructure.provisioning.dedicated_provisioning_compensation_service import (
    DedicatedProvisioningCompensationService,
)
from app.infrastructure.provisioning.dedicated_provisioning_compensation_types import (
    ProvisioningAbortResult,
    ProvisioningCompensationResult,
)
from app.infrastructure.provisioning.dedicated_database_executor import (
    DedicatedDatabaseExecutor,
)
from app.infrastructure.provisioning.dedicated_database_types import (
    DedicatedDatabaseProvisionRequest,
)
from app.infrastructure.provisioning.dedicated_tenant_seed_service import (
    DedicatedTenantSeedService,
)
from app.infrastructure.provisioning.dedicated_tenant_seed_types import (
    DedicatedTenantSeedRequest,
)
from app.modules.tenant.application.provisioning import (
    DEDICATED_INSTALLATION_TYPE,
    ProvisioningJobRequest,
    ProvisioningState,
    ProvisioningStepCode,
    ProvisioningStepStatus,
    SAGA_STEP_ORDER,
)
from app.modules.tenant.application.provisioning.provisioning_state_result import (
    ProvisioningStateTransitionResult,
)
from app.modules.tenant.application.services.dedicated_provisioning_query_service import (
    DedicatedProvisioningQueryService,
)
from app.modules.tenant.application.services.storage_allocation_service import (
    StorageAllocationService,
)
from app.modules.tenant.application.services.storage_allocation_types import (
    StorageAllocationRequest,
    StorageAllocationResult,
    parse_storage_allocation_marker,
    serialize_storage_allocation_marker,
)
from app.modules.tenant.application.services.tenant_provisioning_state_service import (
    TenantProvisioningStateService,
)

logger = logging.getLogger(__name__)

_BOOTSTRAP_ERP_SCRIPT = "apply_schema_erp_v010"
_BOOTSTRAP_DTSP_SCRIPT = "apply_schema_tenant_store_v020"
_BOOTSTRAP_RBAC_SCRIPT = "apply_schema_rbac_v010"


@dataclass
class _SagaRuntimeContext:
    allocation: Optional[StorageAllocationResult] = None
    admin_password: Optional[str] = None
    app_login_password: Optional[str] = None

    @classmethod
    def from_job(cls, job: ProvisioningJobRequest) -> "_SagaRuntimeContext":
        ephemeral = job.ephemeral_context
        if ephemeral is None:
            return cls()
        return cls(
            admin_password=ephemeral.admin_password,
            app_login_password=ephemeral.app_login_password,
        )


class DedicatedProvisioningOrchestrator:
    """Handler saga provisioning dedicated — consumo ProvisioningJobDispatcher."""

    def __init__(
        self,
        *,
        state_service: Optional[TenantProvisioningStateService] = None,
        query_service: Optional[DedicatedProvisioningQueryService] = None,
        repository: Optional[TenantProvisioningRepository] = None,
        allocation_service: Optional[StorageAllocationService] = None,
        database_executor: Optional[DedicatedDatabaseExecutor] = None,
        bootstrap_runner: Optional[BootstrapScriptRunner] = None,
        bootstrap_reader: Optional[BootstrapAppliedReader] = None,
        catalog_seed_service: Optional[DedicatedCatalogSeedService] = None,
        tenant_seed_service: Optional[DedicatedTenantSeedService] = None,
        activation_service: Optional[DedicatedActivationService] = None,
        compensation_service: Optional[DedicatedProvisioningCompensationService] = None,
    ) -> None:
        self._state = state_service or TenantProvisioningStateService()
        self._query = query_service or DedicatedProvisioningQueryService()
        self._repo = repository or TenantProvisioningRepository()
        self._allocation = allocation_service or StorageAllocationService()
        self._database_executor = database_executor or DedicatedDatabaseExecutor()
        self._bootstrap = bootstrap_runner or BootstrapScriptRunner()
        self._bootstrap_reader = bootstrap_reader or BootstrapAppliedReader()
        self._catalog_seed = catalog_seed_service or DedicatedCatalogSeedService()
        self._tenant_seed = tenant_seed_service or DedicatedTenantSeedService()
        self._activation = activation_service or DedicatedActivationService()
        self._compensation = compensation_service or DedicatedProvisioningCompensationService(
            state_service=self._state,
            query_service=self._query,
            repository=self._repo,
            database_executor=self._database_executor,
        )

    async def handle_job(self, job: ProvisioningJobRequest) -> None:
        logger.warning(
            "[F4-DIAG] DedicatedProvisioningOrchestrator.handle_job entrada "
            "cliente_id=%s provisioning_run_id=%s DEDICATED_ENABLED=%s "
            "trigger_source=%s",
            job.cliente_id,
            job.provisioning_run_id,
            settings.DEDICATED_ENABLED,
            job.trigger_source,
        )
        try:
            await self._handle_job_inner(job)
        except Exception:
            logger.exception(
                "[F4-DIAG] DedicatedProvisioningOrchestrator.handle_job "
                "excepcion_completa cliente_id=%s run_id=%s",
                job.cliente_id,
                job.provisioning_run_id,
            )
            raise

    async def _handle_job_inner(self, job: ProvisioningJobRequest) -> None:
        if not settings.DEDICATED_ENABLED:
            logger.warning(
                "[F4-DIAG] DedicatedProvisioningOrchestrator early_return "
                "guard=disabled run_id=%s",
                job.provisioning_run_id,
            )
            logger.info(
                "Dedicated provisioning disabled — saga skipped run_id=%s",
                job.provisioning_run_id,
            )
            return

        status = await self._query.get_provisioning_status(job.cliente_id)
        if status is None:
            logger.warning(
                "[F4-DIAG] DedicatedProvisioningOrchestrator early_return "
                "guard=status_null cliente_id=%s run_id=%s",
                job.cliente_id,
                job.provisioning_run_id,
            )
            logger.warning("Saga abort — cliente no encontrado %s", job.cliente_id)
            return
        if status.provisioning_run_id != job.provisioning_run_id:
            logger.warning(
                "[F4-DIAG] DedicatedProvisioningOrchestrator early_return "
                "guard=run_mismatch job_run_id=%s status_run_id=%s cliente_id=%s",
                job.provisioning_run_id,
                status.provisioning_run_id,
                job.cliente_id,
            )
            logger.warning(
                "Saga abort — run_id %s no es activo para cliente %s",
                job.provisioning_run_id,
                job.cliente_id,
            )
            return
        if status.provisioning_state != ProvisioningState.PROVISIONING:
            logger.warning(
                "[F4-DIAG] DedicatedProvisioningOrchestrator early_return "
                "guard=provisioning_state_invalid state=%s run_id=%s",
                status.provisioning_state,
                job.provisioning_run_id,
            )
            logger.info(
                "Saga noop — run %s en estado %s",
                job.provisioning_run_id,
                status.provisioning_state,
            )
            return

        runtime = _SagaRuntimeContext.from_job(job)
        steps = await self._repo.list_steps_for_run(
            job.provisioning_run_id,
            job.cliente_id,
        )
        steps_by_code = {row["step_code"]: row for row in steps}
        logger.warning(
            "[F4-DIAG] DedicatedProvisioningOrchestrator steps_loaded "
            "run_id=%s step_codes=%s count=%s",
            job.provisioning_run_id,
            sorted(steps_by_code.keys()),
            len(steps_by_code),
        )

        for step_code in SAGA_STEP_ORDER:
            step_row = steps_by_code.get(step_code.value)
            if step_row is None:
                logger.warning(
                    "[F4-DIAG] DedicatedProvisioningOrchestrator step_inexistente "
                    "step_code=%s run_id=%s — continue",
                    step_code.value,
                    job.provisioning_run_id,
                )
                continue
            current_status = ProvisioningStepStatus(step_row["step_status"])
            if current_status in {
                ProvisioningStepStatus.COMPLETED,
                ProvisioningStepStatus.SKIPPED,
            }:
                await self._hydrate_runtime_from_completed_step(
                    step_code,
                    step_row,
                    runtime,
                )
                continue

            if step_code == ProvisioningStepCode.APPLY_SCHEMA_RBAC:
                erp_row = steps_by_code.get(ProvisioningStepCode.APPLY_SCHEMA_ERP.value)
                if erp_row and ProvisioningStepStatus(erp_row["step_status"]) not in {
                    ProvisioningStepStatus.COMPLETED,
                    ProvisioningStepStatus.SKIPPED,
                }:
                    continue

            if step_code in {
                ProvisioningStepCode.APPLY_SCHEMA_ERP,
                ProvisioningStepCode.APPLY_SCHEMA_RBAC,
            }:
                aborted = await self._run_bootstrap_block(
                    job=job,
                    runtime=runtime,
                    steps_by_code=steps_by_code,
                )
                if aborted:
                    return
                steps = await self._repo.list_steps_for_run(
                    job.provisioning_run_id,
                    job.cliente_id,
                )
                steps_by_code = {row["step_code"]: row for row in steps}
                continue

            if step_code == ProvisioningStepCode.REGISTRY:
                logger.warning(
                    "[F4-DIAG] DedicatedProvisioningOrchestrator "
                    "Entrando a registry run_id=%s",
                    job.provisioning_run_id,
                )

            await self._state.mark_step_running(
                cliente_id=job.cliente_id,
                provisioning_run_id=job.provisioning_run_id,
                step_code=step_code,
            )
            try:
                marker = await self._execute_step(
                    job=job,
                    step_code=step_code,
                    runtime=runtime,
                )
            except Exception as exc:
                await self._fail_step_and_run(job, step_code, exc)
                return

            await self._state.mark_step_completed(
                cliente_id=job.cliente_id,
                provisioning_run_id=job.provisioning_run_id,
                step_code=step_code,
                idempotency_marker=marker,
            )

        logger.info(
            "Saga completed S1–S10 cliente_id=%s run_id=%s",
            job.cliente_id,
            job.provisioning_run_id,
        )

    async def abort_provisioning_run(
        self,
        *,
        cliente_id: UUID,
        provisioning_run_id: UUID,
        reason: Optional[str] = None,
    ) -> ProvisioningAbortResult:
        """Abort interno F4-10 — sin endpoint HTTP (F4-11)."""
        return await self._compensation.abort_provisioning_run(
            cliente_id=cliente_id,
            provisioning_run_id=provisioning_run_id,
            reason=reason,
        )

    async def compensate_failed_run(
        self,
        *,
        cliente_id: UUID,
        provisioning_run_id: UUID,
    ) -> ProvisioningCompensationResult:
        """Compensación on-demand para run ``failed``."""
        return await self._compensation.compensate_for_failed_run(
            cliente_id=cliente_id,
            provisioning_run_id=provisioning_run_id,
        )

    async def retry_provisioning_run(
        self,
        *,
        cliente_id: UUID,
        provisioning_run_id: Optional[UUID] = None,
    ) -> tuple[ProvisioningStateTransitionResult, object]:
        """Retry interno F4-10 — reanuda saga desde último step incompleto."""
        return await self._compensation.retry_provisioning_run(
            cliente_id=cliente_id,
            provisioning_run_id=provisioning_run_id,
        )

    async def _hydrate_runtime_from_completed_step(
        self,
        step_code: ProvisioningStepCode,
        step_row: dict[str, Any],
        runtime: _SagaRuntimeContext,
    ) -> None:
        if (
            step_code == ProvisioningStepCode.STORAGE_ALLOCATION
            and step_row.get("idempotency_marker")
            and runtime.allocation is None
        ):
            runtime.allocation = parse_storage_allocation_marker(
                step_row["idempotency_marker"],
            )

    async def _execute_step(
        self,
        *,
        job: ProvisioningJobRequest,
        step_code: ProvisioningStepCode,
        runtime: _SagaRuntimeContext,
    ) -> Optional[str]:
        if step_code == ProvisioningStepCode.REGISTRY:
            await self._step_registry(job)
            return None

        if step_code == ProvisioningStepCode.STORAGE_ALLOCATION:
            return await self._step_storage_allocation(job, runtime)

        if step_code == ProvisioningStepCode.CREATE_DATABASE:
            return await self._step_create_database(job, runtime)

        if step_code == ProvisioningStepCode.APPLY_CATALOGS:
            return await self._step_apply_catalogs(job, runtime)

        if step_code == ProvisioningStepCode.SEED_TENANT:
            return await self._step_seed_tenant(job, runtime)

        if step_code == ProvisioningStepCode.REGISTER_METADATA:
            return await self._step_activation(job, runtime, step_code)

        if step_code == ProvisioningStepCode.ACTIVATE_ROUTING:
            return await self._step_activation(job, runtime, step_code)

        if step_code == ProvisioningStepCode.MARK_READY:
            return await self._step_activation(job, runtime, step_code)

        raise ValidationError(
            detail=f"Step saga no implementado: {step_code.value}.",
            internal_code="PROVISIONING_STEP_UNSUPPORTED",
        )

    async def _step_registry(self, job: ProvisioningJobRequest) -> None:
        snapshot = await self._repo.get_cliente_provisioning_snapshot(job.cliente_id)
        if snapshot is None:
            raise NotFoundError(
                detail=f"Cliente {job.cliente_id} no encontrado.",
                internal_code="CLIENTE_NOT_FOUND",
            )
        if snapshot["tipo_instalacion"] != DEDICATED_INSTALLATION_TYPE:
            raise ValidationError(
                detail="Registry saga solo aplica a tenants dedicated.",
                internal_code="PROVISIONING_NOT_DEDICATED",
            )

    async def _step_storage_allocation(
        self,
        job: ProvisioningJobRequest,
        runtime: _SagaRuntimeContext,
    ) -> str:
        profile = await self._load_cliente_profile(job.cliente_id)
        result = self._allocation.allocate(
            StorageAllocationRequest(
                cliente_id=job.cliente_id,
                codigo_cliente=profile["codigo_cliente"],
            ),
        )
        runtime.allocation = result
        return serialize_storage_allocation_marker(result)

    async def _step_create_database(
        self,
        job: ProvisioningJobRequest,
        runtime: _SagaRuntimeContext,
    ) -> str:
        allocation = self._require_allocation(runtime)
        profile = await self._load_cliente_profile(job.cliente_id)
        provision = await self._database_executor.provision_physical_database(
            DedicatedDatabaseProvisionRequest(
                cliente_id=job.cliente_id,
                codigo_cliente=profile["codigo_cliente"],
                servidor=allocation.servidor,
                database_name=allocation.database_name,
                app_login_name=allocation.app_login_name,
                app_login_password=runtime.app_login_password,
            ),
        )
        runtime.app_login_password = provision.app_login_password
        return allocation.database_name

    async def _run_bootstrap_block(
        self,
        *,
        job: ProvisioningJobRequest,
        runtime: _SagaRuntimeContext,
        steps_by_code: dict[str, dict[str, Any]],
    ) -> bool:
        """Ejecuta bootstrap S4/S5. Retorna True si la saga debe abortar."""
        erp_row = steps_by_code[ProvisioningStepCode.APPLY_SCHEMA_ERP.value]
        rbac_row = steps_by_code[ProvisioningStepCode.APPLY_SCHEMA_RBAC.value]
        erp_status = ProvisioningStepStatus(erp_row["step_status"])
        rbac_status = ProvisioningStepStatus(rbac_row["step_status"])
        if erp_status in {
            ProvisioningStepStatus.COMPLETED,
            ProvisioningStepStatus.SKIPPED,
        } and rbac_status in {
            ProvisioningStepStatus.COMPLETED,
            ProvisioningStepStatus.SKIPPED,
        }:
            return False

        running_step = (
            ProvisioningStepCode.APPLY_SCHEMA_RBAC
            if erp_status
            in {ProvisioningStepStatus.COMPLETED, ProvisioningStepStatus.SKIPPED}
            else ProvisioningStepCode.APPLY_SCHEMA_ERP
        )
        await self._state.mark_step_running(
            cliente_id=job.cliente_id,
            provisioning_run_id=job.provisioning_run_id,
            step_code=running_step,
        )
        try:
            allocation = self._require_allocation(runtime)
            result = await self._bootstrap.run_dedicated_schema_bootstrap(
                BootstrapScriptRunRequest(
                    database_name=allocation.database_name,
                    cliente_id=job.cliente_id,
                    provisioning_run_id=job.provisioning_run_id,
                ),
            )
            scripts = set(result.scripts_executed) | set(result.scripts_skipped)
            if _BOOTSTRAP_ERP_SCRIPT not in scripts:
                raise ConflictError(
                    detail="Bootstrap ERP no aplicado.",
                    internal_code="PROVISIONING_SCHEMA_FAILED",
                )
            if not {_BOOTSTRAP_DTSP_SCRIPT, _BOOTSTRAP_RBAC_SCRIPT}.issubset(scripts):
                raise ConflictError(
                    detail="Bootstrap RBAC/DTSP incompleto.",
                    internal_code="PROVISIONING_SCHEMA_FAILED",
                )
            await self._mark_bootstrap_saga_steps(job, scripts)
        except Exception as exc:
            await self._reconcile_bootstrap_failure(job=job, runtime=runtime)
            fail_step = ProvisioningStepCode.APPLY_SCHEMA_ERP
            if runtime.allocation is not None:
                applied = await self._bootstrap_reader.list_applied_script_codes(
                    runtime.allocation.database_name,
                )
                if _BOOTSTRAP_ERP_SCRIPT in applied:
                    fail_step = ProvisioningStepCode.APPLY_SCHEMA_RBAC
            await self._fail_step_and_run(job, fail_step, exc)
            return True
        return False

    async def _mark_bootstrap_saga_steps(
        self,
        job: ProvisioningJobRequest,
        scripts: set[str],
    ) -> None:
        steps = await self._repo.list_steps_for_run(
            job.provisioning_run_id,
            job.cliente_id,
        )
        steps_by_code = {row["step_code"]: row for row in steps}

        if _BOOTSTRAP_ERP_SCRIPT in scripts:
            erp_status = ProvisioningStepStatus(
                steps_by_code[ProvisioningStepCode.APPLY_SCHEMA_ERP.value]["step_status"],
            )
            if erp_status == ProvisioningStepStatus.PENDING:
                await self._state.mark_step_running(
                    cliente_id=job.cliente_id,
                    provisioning_run_id=job.provisioning_run_id,
                    step_code=ProvisioningStepCode.APPLY_SCHEMA_ERP,
                )
            if erp_status in {
                ProvisioningStepStatus.PENDING,
                ProvisioningStepStatus.RUNNING,
            }:
                await self._state.mark_step_completed(
                    cliente_id=job.cliente_id,
                    provisioning_run_id=job.provisioning_run_id,
                    step_code=ProvisioningStepCode.APPLY_SCHEMA_ERP,
                    idempotency_marker=_BOOTSTRAP_ERP_SCRIPT,
                )

        if {_BOOTSTRAP_DTSP_SCRIPT, _BOOTSTRAP_RBAC_SCRIPT}.issubset(scripts):
            rbac_status = ProvisioningStepStatus(
                steps_by_code[ProvisioningStepCode.APPLY_SCHEMA_RBAC.value]["step_status"],
            )
            if rbac_status == ProvisioningStepStatus.PENDING:
                await self._state.mark_step_running(
                    cliente_id=job.cliente_id,
                    provisioning_run_id=job.provisioning_run_id,
                    step_code=ProvisioningStepCode.APPLY_SCHEMA_RBAC,
                )
            if rbac_status in {
                ProvisioningStepStatus.PENDING,
                ProvisioningStepStatus.RUNNING,
            }:
                await self._state.mark_step_completed(
                    cliente_id=job.cliente_id,
                    provisioning_run_id=job.provisioning_run_id,
                    step_code=ProvisioningStepCode.APPLY_SCHEMA_RBAC,
                    idempotency_marker=(
                        f"{_BOOTSTRAP_DTSP_SCRIPT}+{_BOOTSTRAP_RBAC_SCRIPT}"
                    ),
                )

    async def _reconcile_bootstrap_failure(
        self,
        *,
        job: ProvisioningJobRequest,
        runtime: _SagaRuntimeContext,
    ) -> None:
        allocation = runtime.allocation
        if allocation is None:
            return
        applied = await self._bootstrap_reader.list_applied_script_codes(
            allocation.database_name,
        )
        await self._mark_bootstrap_saga_steps(job, set(applied))

    async def _step_apply_catalogs(
        self,
        job: ProvisioningJobRequest,
        runtime: _SagaRuntimeContext,
    ) -> str:
        allocation = self._require_allocation(runtime)
        profile = await self._load_cliente_profile(job.cliente_id)
        result = await self._catalog_seed.run_catalog_seed(
            DedicatedCatalogSeedRequest(
                database_name=allocation.database_name,
                cliente_id=job.cliente_id,
                plan_suscripcion=profile.get("plan_suscripcion"),
                provisioning_run_id=job.provisioning_run_id,
            ),
        )
        return result.profile_code

    async def _step_seed_tenant(
        self,
        job: ProvisioningJobRequest,
        runtime: _SagaRuntimeContext,
    ) -> str:
        allocation = self._require_allocation(runtime)
        profile = await self._load_cliente_profile(job.cliente_id)
        admin_password = runtime.admin_password
        result = await self._tenant_seed.run_tenant_seed(
            DedicatedTenantSeedRequest(
                database_name=allocation.database_name,
                cliente_id=job.cliente_id,
                codigo_cliente=profile["codigo_cliente"],
                subdominio=profile["subdominio"],
                razon_social=profile["razon_social"],
                contacto_email=profile["contacto_email"],
                plan_suscripcion=profile.get("plan_suscripcion"),
                nombre_comercial=profile.get("nombre_comercial"),
                ruc=profile.get("ruc"),
                contacto_nombre=profile.get("contacto_nombre"),
                provisioning_run_id=job.provisioning_run_id,
                admin_password=admin_password,
            ),
        )
        return str(result.admin_usuario_id)

    async def _step_activation(
        self,
        job: ProvisioningJobRequest,
        runtime: _SagaRuntimeContext,
        step_code: ProvisioningStepCode,
    ) -> str:
        allocation = self._require_allocation(runtime)
        password = runtime.app_login_password
        if not password:
            raise ValidationError(
                detail="Credencial login app no disponible para activación.",
                internal_code="PROVISIONING_ACTIVATION_CONTEXT_MISSING",
            )
        request = DedicatedActivationRequest(
            cliente_id=job.cliente_id,
            provisioning_run_id=job.provisioning_run_id,
            database_name=allocation.database_name,
            servidor=allocation.servidor,
            app_login_name=allocation.app_login_name,
            app_login_password=password,
        )
        if step_code == ProvisioningStepCode.REGISTER_METADATA:
            result = await self._activation.register_metadata(request)
            return result.idempotency_marker
        if step_code == ProvisioningStepCode.ACTIVATE_ROUTING:
            result = await self._activation.activate_routing(request)
            return result.idempotency_marker
        if step_code == ProvisioningStepCode.MARK_READY:
            result = await self._activation.mark_ready(request)
            return result.idempotency_marker
        raise ValidationError(
            detail=f"Step activación no soportado: {step_code.value}.",
            internal_code="PROVISIONING_STEP_UNSUPPORTED",
        )

    async def _fail_step_and_run(
        self,
        job: ProvisioningJobRequest,
        step_code: ProvisioningStepCode,
        exc: Exception,
    ) -> None:
        error_code, error_message = _map_provisioning_error(exc, step_code)
        logger.warning(
            "Saga step failed cliente_id=%s run_id=%s step=%s code=%s",
            job.cliente_id,
            job.provisioning_run_id,
            step_code.value,
            error_code,
        )
        try:
            await self._state.mark_step_failed(
                cliente_id=job.cliente_id,
                provisioning_run_id=job.provisioning_run_id,
                step_code=step_code,
                error_code=error_code,
                error_message=error_message,
            )
            await self._state.transition_run_to_failed(
                cliente_id=job.cliente_id,
                provisioning_run_id=job.provisioning_run_id,
                error_code=error_code,
                error_message=error_message,
                current_step_code=step_code,
            )
        except Exception:
            logger.exception(
                "No se pudo persistir estado failed run_id=%s",
                job.provisioning_run_id,
            )

    async def _load_cliente_profile(self, cliente_id: UUID) -> dict[str, Any]:
        rows = await execute_query(
            text(
                """
                SELECT codigo_cliente, subdominio, razon_social, nombre_comercial, ruc,
                       plan_suscripcion, contacto_email, contacto_nombre
                FROM cliente
                WHERE cliente_id = :cliente_id
                """
            ).bindparams(cliente_id=cliente_id),
            connection_type=DatabaseConnection.ADMIN,
            client_id=cliente_id,
        )
        if not rows:
            raise NotFoundError(
                detail=f"Cliente {cliente_id} no encontrado.",
                internal_code="CLIENTE_NOT_FOUND",
            )
        return rows[0]

    @staticmethod
    def _require_allocation(runtime: _SagaRuntimeContext) -> StorageAllocationResult:
        if runtime.allocation is None:
            raise ValidationError(
                detail="Storage allocation no disponible en contexto saga.",
                internal_code="STORAGE_ALLOCATION_MISSING",
            )
        return runtime.allocation


def _map_provisioning_error(
    exc: Exception,
    step_code: ProvisioningStepCode,
) -> tuple[str, str]:
    if isinstance(exc, CustomException):
        code = exc.internal_code or "PROVISIONING_STEP_FAILED"
        message = str(exc.detail) if exc.detail else "Error en provisioning dedicated."
        return code, message[:500]

    defaults = {
        ProvisioningStepCode.CREATE_DATABASE: "PROVISIONING_CREATE_DATABASE_FAILED",
        ProvisioningStepCode.APPLY_SCHEMA_ERP: "PROVISIONING_SCHEMA_FAILED",
        ProvisioningStepCode.APPLY_SCHEMA_RBAC: "PROVISIONING_SCHEMA_FAILED",
        ProvisioningStepCode.APPLY_CATALOGS: "PROVISIONING_CATALOG_FAILED",
        ProvisioningStepCode.SEED_TENANT: "PROVISIONING_SEED_FAILED",
        ProvisioningStepCode.REGISTER_METADATA: "PROVISIONING_METADATA_FAILED",
        ProvisioningStepCode.ACTIVATE_ROUTING: "PROVISIONING_ACTIVATION_FAILED",
        ProvisioningStepCode.MARK_READY: "PROVISIONING_ACTIVATION_FAILED",
    }
    return (
        defaults.get(step_code, "PROVISIONING_STEP_FAILED"),
        "Error en provisioning dedicated.",
    )


def create_default_provisioning_job_handler():
    orchestrator = DedicatedProvisioningOrchestrator()
    return orchestrator.handle_job


__all__ = [
    "DedicatedProvisioningOrchestrator",
    "create_default_provisioning_job_handler",
]
