"""
Dedicated Provisioning E2E harness — PR-F4-12 (F4-WP12).

Capa pura + factories para tests integration mock E2E S1→S10.
Sin SQL Server; sin create_async_engine.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

from app.infrastructure.provisioning.bootstrap_script_types import BootstrapScriptRunResult
from app.infrastructure.provisioning.dedicated_activation_types import (
    DedicatedActivationStepResult,
)
from app.infrastructure.provisioning.dedicated_catalog_seed_types import (
    DedicatedCatalogSeedResult,
)
from app.infrastructure.provisioning.dedicated_database_types import (
    DedicatedDatabaseDropResult,
    DedicatedDatabaseProvisionResult,
)
from app.infrastructure.provisioning.dedicated_provisioning_compensation_service import (
    DedicatedProvisioningCompensationService,
)
from app.infrastructure.provisioning.dedicated_tenant_seed_types import (
    DedicatedTenantSeedResult,
)
from app.infrastructure.provisioning.dedicated_storage_metadata_types import (
    DedicatedStorageMetadataResult,
)
from app.modules.tenant.application.provisioning import (
    ProvisioningJobRequest,
    ProvisioningState,
    ProvisioningStepCode,
    ProvisioningStepStatus,
    SAGA_STEP_ORDER,
)
from app.modules.tenant.application.provisioning.provisioning_saga_ephemeral_context import (
    ProvisioningSagaEphemeralContext,
)
from app.modules.tenant.application.provisioning.provisioning_status_read import (
    DedicatedProvisioningStatusSnapshot,
)
from app.modules.tenant.application.services.dedicated_provisioning_orchestrator import (
    DedicatedProvisioningOrchestrator,
)
from app.modules.tenant.application.services.provisioning_job_dispatcher import (
    ProvisioningJobDispatcher,
)
from app.modules.tenant.application.services.storage_allocation_types import (
    StorageAllocationResult,
    serialize_storage_allocation_marker,
)

# UUID determinístico E2E — namespace distinto de hybrid F0 fixtures
E2E_CLIENTE_ID = UUID("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee")
E2E_RUN_ID = UUID("ffffffff-ffff-4fff-8fff-ffffffffffff")
E2E_ADMIN_USER_ID = UUID("11111111-1111-4111-8111-111111111111")
E2E_CONEXION_ID = UUID("22222222-2222-4222-8222-222222222222")


def build_cliente_profile() -> list[dict]:
    return [
        {
            "codigo_cliente": "E2E001",
            "subdominio": "e2e001",
            "razon_social": "E2E Dedicated Corp",
            "nombre_comercial": None,
            "ruc": None,
            "plan_suscripcion": "trial",
            "contacto_email": "admin@e2e.test",
            "contacto_nombre": None,
        }
    ]


def build_step_rows(
    *,
    completed_through: Optional[ProvisioningStepCode] = None,
    all_pending: bool = False,
) -> list[dict]:
    rows: list[dict] = []
    completed_codes: set[str] = set()
    if all_pending:
        completed_codes = set()
    elif completed_through is not None:
        for code in SAGA_STEP_ORDER:
            completed_codes.add(code.value)
            if code == completed_through:
                break

    for order, code in enumerate(SAGA_STEP_ORDER, start=1):
        if all_pending:
            status = ProvisioningStepStatus.PENDING
            marker = None
        elif code.value in completed_codes:
            status = ProvisioningStepStatus.COMPLETED
            marker = "e2e-marker"
            if code == ProvisioningStepCode.STORAGE_ALLOCATION:
                marker = serialize_storage_allocation_marker(default_allocation())
        else:
            status = ProvisioningStepStatus.PENDING
            marker = None
        rows.append(
            {
                "step_code": code.value,
                "step_status": status.value,
                "saga_order": order,
                "idempotency_marker": marker,
            }
        )
    return rows


def default_allocation() -> StorageAllocationResult:
    return StorageAllocationResult(
        servidor="e2e-sql.local",
        database_name="erp_e2e001",
        app_login_name="erpapp_e2e001",
    )


def build_provisioning_status(
    *,
    cliente_id: UUID = E2E_CLIENTE_ID,
    run_id: UUID = E2E_RUN_ID,
    state: ProvisioningState = ProvisioningState.PROVISIONING,
    current_step: str = ProvisioningStepCode.REGISTRY.value,
) -> DedicatedProvisioningStatusSnapshot:
    return DedicatedProvisioningStatusSnapshot(
        cliente_id=cliente_id,
        tipo_instalacion="dedicated",
        provisioning_state=state,
        provisioning_run_id=run_id,
        current_step=current_step,
        steps=[],
        started_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        ready_at=datetime.utcnow() if state == ProvisioningState.READY else None,
        failed_at=datetime.utcnow() if state == ProvisioningState.FAILED else None,
        last_error_code=None,
        last_error_message=None,
        retry_allowed=state == ProvisioningState.FAILED,
        abort_allowed=state == ProvisioningState.PROVISIONING,
    )


@dataclass
class ProvisioningE2EAuditRecorder:
    """Registro de eventos BL-F4 §16 / contrato §16 para evidencia G-F4-03."""

    events: List[Dict[str, Any]] = field(default_factory=list)

    def record(self, event_type: str, **payload: Any) -> None:
        self.events.append(
            {
                "event": event_type,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                **payload,
            }
        )

    def metric_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for item in self.events:
            key = item["event"]
            counts[key] = counts.get(key, 0) + 1
        return counts

    def lifecycle_metrics_manifest(self) -> Dict[str, Any]:
        """Cinco señales mínimas DOD-F4-10 / contrato §16."""
        counts = self.metric_counts()
        return {
            "artifact_type": "f4_provisioning_metrics",
            "signals": {
                "dedicated.provisioning.started": counts.get(
                    "dedicated.provisioning.started", 0
                ),
                "dedicated.provisioning.step.completed": counts.get(
                    "dedicated.provisioning.step.completed", 0
                ),
                "dedicated.provisioning.ready": counts.get(
                    "dedicated.provisioning.ready", 0
                ),
                "dedicated.provisioning.failed": counts.get(
                    "dedicated.provisioning.failed", 0
                ),
                "dedicated.provisioning.retry": counts.get(
                    "dedicated.provisioning.retry", 0
                ),
            },
            "events_total": len(self.events),
        }


@dataclass
class ProvisioningE2EStack:
    cliente_id: UUID
    run_id: UUID
    orchestrator: DedicatedProvisioningOrchestrator
    compensation: DedicatedProvisioningCompensationService
    dispatcher: ProvisioningJobDispatcher
    mocks: Dict[str, Any]
    audit: ProvisioningE2EAuditRecorder
    completed_steps: List[str] = field(default_factory=list)

    def job_request(
        self,
        *,
        admin_password: str = "E2eAdminPass123!",
    ) -> ProvisioningJobRequest:
        return ProvisioningJobRequest(
            cliente_id=self.cliente_id,
            provisioning_run_id=self.run_id,
            ephemeral_context=ProvisioningSagaEphemeralContext(
                admin_password=admin_password,
            ),
            trigger_source="e2e_harness",
        )


def _wire_step_tracking(
    stack: ProvisioningE2EStack,
    state_mock: AsyncMock,
) -> None:
    async def _mark_completed(**kwargs: Any) -> None:
        code = kwargs.get("step_code")
        if code is not None:
            step_value = code.value if hasattr(code, "value") else str(code)
            stack.completed_steps.append(step_value)
            stack.audit.record(
                "dedicated.provisioning.step.completed",
                cliente_id=str(stack.cliente_id),
                run_id=str(stack.run_id),
                step_code=step_value,
            )

    state_mock.mark_step_completed.side_effect = _mark_completed


def build_provisioning_e2e_stack(
    *,
    cliente_id: UUID = E2E_CLIENTE_ID,
    run_id: UUID = E2E_RUN_ID,
    provisioning_state: ProvisioningState = ProvisioningState.PROVISIONING,
    step_rows: Optional[list[dict]] = None,
    use_real_activation: bool = False,
) -> ProvisioningE2EStack:
    audit = ProvisioningE2EAuditRecorder()
    audit.record(
        "dedicated.provisioning.started",
        cliente_id=str(cliente_id),
        run_id=str(run_id),
    )

    allocation = default_allocation()
    state = AsyncMock()
    query = AsyncMock()
    repo = AsyncMock()
    allocation_service = MagicMock()
    allocation_service.allocate.return_value = allocation
    database_executor = AsyncMock()
    bootstrap = AsyncMock()
    bootstrap_reader = AsyncMock()
    catalog_seed = AsyncMock()
    tenant_seed = AsyncMock()

    if use_real_activation:
        from app.infrastructure.provisioning.dedicated_activation_service import (
            DedicatedActivationService,
        )

        metadata_svc = AsyncMock()
        metadata_svc.register_primary_connection.return_value = (
            DedicatedStorageMetadataResult(
                conexion_id=E2E_CONEXION_ID,
                created=True,
                idempotent=False,
            )
        )
        activation_state = AsyncMock()
        activation_query = AsyncMock()
        activation_query.get_provisioning_status.return_value = (
            build_provisioning_status(
                cliente_id=cliente_id,
                run_id=run_id,
                state=provisioning_state,
            )
        )
        activation = DedicatedActivationService(
            metadata_service=metadata_svc,
            state_service=activation_state,
            query_service=activation_query,
        )
        activation_mocks = {
            "metadata": metadata_svc,
            "activation_state": activation_state,
            "activation_query": activation_query,
        }
    else:
        activation = AsyncMock()

        async def _register_metadata(_request):
            return DedicatedActivationStepResult(
                step_code="register_metadata",
                idempotency_marker=str(E2E_CONEXION_ID),
            )

        async def _activate_routing(_request):
            return DedicatedActivationStepResult(
                step_code="activate_routing",
                idempotency_marker=f"routing_smoke_v1:{cliente_id}",
            )

        async def _mark_ready(request):
            await state.transition_run_to_ready(
                cliente_id=request.cliente_id,
                provisioning_run_id=request.provisioning_run_id,
            )
            return DedicatedActivationStepResult(
                step_code="mark_ready",
                idempotency_marker=f"ready_run:{run_id}",
            )

        activation.register_metadata.side_effect = _register_metadata
        activation.activate_routing.side_effect = _activate_routing
        activation.mark_ready.side_effect = _mark_ready
        activation_mocks = {}

    query.get_provisioning_status.return_value = build_provisioning_status(
        cliente_id=cliente_id,
        run_id=run_id,
        state=provisioning_state,
    )
    repo.list_steps_for_run.return_value = step_rows or build_step_rows(all_pending=True)
    repo.get_cliente_provisioning_snapshot.return_value = {
        "cliente_id": cliente_id,
        "tipo_instalacion": "dedicated",
        "provisioning_state": provisioning_state.value,
        "current_provisioning_run_id": run_id,
    }

    database_executor.provision_physical_database.return_value = (
        DedicatedDatabaseProvisionResult(
            cliente_id=cliente_id,
            servidor=allocation.servidor,
            database_name=allocation.database_name,
            app_login_name=allocation.app_login_name,
            app_login_password="e2e-login-secret",
            database_created=True,
            login_created=True,
            database_already_existed=False,
            login_already_existed=False,
        )
    )
    database_executor.drop_physical_database.return_value = (
        DedicatedDatabaseDropResult(
            cliente_id=cliente_id,
            database_name=allocation.database_name,
            app_login_name=allocation.app_login_name,
            database_existed=True,
            database_dropped=True,
            login_existed=True,
            login_dropped=True,
        )
    )
    bootstrap.run_dedicated_schema_bootstrap.return_value = BootstrapScriptRunResult(
        database_name=allocation.database_name,
        cliente_id=cliente_id,
        profile="dedicated_schema_v2",
        scripts_executed=(
            "apply_schema_erp_v010",
            "apply_schema_tenant_store_v020",
            "apply_schema_rbac_v010",
        ),
        scripts_skipped=(),
        batches_executed=5,
    )
    catalog_seed.run_catalog_seed.return_value = DedicatedCatalogSeedResult(
        database_name=allocation.database_name,
        cliente_id=cliente_id,
        plan_suscripcion="trial",
        profile_code="trial",
        scripts_executed=("seed_catalogs",),
        scripts_skipped=(),
        batches_executed=1,
        row_verifications=(),
    )
    tenant_seed.run_tenant_seed.return_value = DedicatedTenantSeedResult(
        database_name=allocation.database_name,
        cliente_id=cliente_id,
        plan_suscripcion="trial",
        profile_code="trial",
        admin_username="admin",
        admin_usuario_id=E2E_ADMIN_USER_ID,
        admin_rol_id=uuid4(),
        empresa_id=uuid4(),
        steps_executed=("seed_tenant",),
        steps_skipped=(),
        row_verifications=(),
    )

    orchestrator = DedicatedProvisioningOrchestrator(
        state_service=state,
        query_service=query,
        repository=repo,
        allocation_service=allocation_service,
        database_executor=database_executor,
        bootstrap_runner=bootstrap,
        bootstrap_reader=bootstrap_reader,
        catalog_seed_service=catalog_seed,
        tenant_seed_service=tenant_seed,
        activation_service=activation,
    )

    metadata_cleanup = AsyncMock()
    metadata_cleanup.cleanup_primary_connection.return_value = True
    metadata_cleanup.register_primary_connection.return_value = (
        DedicatedStorageMetadataResult(
            conexion_id=E2E_CONEXION_ID,
            created=True,
            idempotent=False,
        )
    )

    dispatcher_mock = AsyncMock()
    dispatcher_mock.dispatch_for_run.return_value = MagicMock(dispatched=True)

    compensation = DedicatedProvisioningCompensationService(
        state_service=state,
        query_service=query,
        repository=repo,
        database_executor=database_executor,
        metadata_service=metadata_cleanup,
        dispatcher=dispatcher_mock,
    )
    orchestrator_with_comp = DedicatedProvisioningOrchestrator(
        state_service=state,
        query_service=query,
        repository=repo,
        allocation_service=allocation_service,
        database_executor=database_executor,
        bootstrap_runner=bootstrap,
        bootstrap_reader=bootstrap_reader,
        catalog_seed_service=catalog_seed,
        tenant_seed_service=tenant_seed,
        activation_service=activation,
        compensation_service=compensation,
    )

    dispatcher = ProvisioningJobDispatcher(
        query_service=query,
        state_service=state,
        default_handler=orchestrator_with_comp.handle_job,
    )

    mocks: Dict[str, Any] = {
        "state": state,
        "query": query,
        "repo": repo,
        "allocation": allocation_service,
        "database_executor": database_executor,
        "bootstrap": bootstrap,
        "catalog_seed": catalog_seed,
        "tenant_seed": tenant_seed,
        "activation": activation,
        "metadata_cleanup": metadata_cleanup,
        "dispatcher_mock": dispatcher_mock,
        "allocation_result": allocation,
        **activation_mocks,
    }

    stack = ProvisioningE2EStack(
        cliente_id=cliente_id,
        run_id=run_id,
        orchestrator=orchestrator_with_comp,
        compensation=compensation,
        dispatcher=dispatcher,
        mocks=mocks,
        audit=audit,
    )
    _wire_step_tracking(stack, state)

    async def _transition_ready(**kwargs: Any) -> None:
        stack.audit.record(
            "dedicated.provisioning.ready",
            cliente_id=str(kwargs.get("cliente_id", cliente_id)),
            run_id=str(kwargs.get("provisioning_run_id", run_id)),
            duration_seconds=1.0,
        )

    state.transition_run_to_ready.side_effect = _transition_ready

    async def _transition_failed(**kwargs: Any) -> None:
        stack.audit.record(
            "dedicated.provisioning.failed",
            cliente_id=str(kwargs.get("cliente_id", cliente_id)),
            run_id=str(kwargs.get("provisioning_run_id", run_id)),
            error_code=kwargs.get("error_code", "PROVISIONING_ABORTED"),
        )

    state.transition_run_to_failed.side_effect = _transition_failed

    return stack


def steps_through_s3_marker() -> list[dict]:
    """Steps completados hasta S2 para escenarios abort/compensation."""
    rows = build_step_rows(all_pending=True)
    for row in rows:
        if row["step_code"] in {
            ProvisioningStepCode.REGISTRY.value,
            ProvisioningStepCode.STORAGE_ALLOCATION.value,
            ProvisioningStepCode.CREATE_DATABASE.value,
        }:
            row["step_status"] = ProvisioningStepStatus.COMPLETED.value
            if row["step_code"] == ProvisioningStepCode.STORAGE_ALLOCATION.value:
                row["idempotency_marker"] = serialize_storage_allocation_marker(
                    default_allocation(),
                )
    return rows


def steps_through_s8() -> list[dict]:
    rows = build_step_rows(all_pending=True)
    for row in rows:
        code = row["step_code"]
        if code in {
            ProvisioningStepCode.REGISTRY.value,
            ProvisioningStepCode.STORAGE_ALLOCATION.value,
            ProvisioningStepCode.CREATE_DATABASE.value,
            ProvisioningStepCode.APPLY_SCHEMA_ERP.value,
            ProvisioningStepCode.APPLY_SCHEMA_RBAC.value,
            ProvisioningStepCode.APPLY_CATALOGS.value,
            ProvisioningStepCode.SEED_TENANT.value,
            ProvisioningStepCode.REGISTER_METADATA.value,
        }:
            row["step_status"] = ProvisioningStepStatus.COMPLETED.value
            if code == ProvisioningStepCode.STORAGE_ALLOCATION.value:
                row["idempotency_marker"] = serialize_storage_allocation_marker(
                    default_allocation(),
                )
    return rows
