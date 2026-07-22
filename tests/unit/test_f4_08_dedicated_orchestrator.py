"""PR-F4-08 — tests unitarios DedicatedProvisioningOrchestrator."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError
from app.infrastructure.provisioning.bootstrap_script_types import BootstrapScriptRunResult
from app.infrastructure.provisioning.dedicated_catalog_seed_types import (
    DedicatedCatalogSeedResult,
)
from app.infrastructure.provisioning.dedicated_activation_types import (
    DedicatedActivationStepResult,
)
from app.infrastructure.provisioning.dedicated_database_types import (
    DedicatedDatabaseProvisionResult,
)
from app.infrastructure.provisioning.dedicated_tenant_seed_types import (
    DedicatedTenantSeedResult,
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
from app.modules.tenant.application.services.storage_allocation_types import (
    StorageAllocationResult,
    serialize_storage_allocation_marker,
)

CLIENTE_ID = uuid4()
RUN_ID = uuid4()
ADMIN_USER_ID = uuid4()


def _cliente_profile() -> list[dict]:
    return [
        {
            "codigo_cliente": "ACME001",
            "subdominio": "acme",
            "razon_social": "ACME",
            "nombre_comercial": None,
            "ruc": None,
            "plan_suscripcion": "trial",
            "contacto_email": "a@acme.test",
            "contacto_nombre": None,
        }
    ]


def _step_rows(*, all_pending: bool = True) -> list[dict]:
    rows = []
    for order, code in enumerate(SAGA_STEP_ORDER, start=1):
        status = ProvisioningStepStatus.PENDING if all_pending else ProvisioningStepStatus.COMPLETED
        rows.append(
            {
                "step_code": code.value,
                "step_status": status.value,
                "saga_order": order,
                "idempotency_marker": None,
            }
        )
    return rows


def _provisioning_status() -> DedicatedProvisioningStatusSnapshot:
    return DedicatedProvisioningStatusSnapshot(
        cliente_id=CLIENTE_ID,
        tipo_instalacion="dedicated",
        provisioning_state=ProvisioningState.PROVISIONING,
        provisioning_run_id=RUN_ID,
        current_step=ProvisioningStepCode.REGISTRY.value,
        steps=[],
        started_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        ready_at=None,
        failed_at=None,
        last_error_code=None,
        last_error_message=None,
        retry_allowed=False,
        abort_allowed=True,
    )


@pytest.fixture
def orchestrator_mocks() -> dict[str, AsyncMock]:
    allocation = StorageAllocationResult(
        servidor="srv",
        database_name="erp_acme001",
        app_login_name="erpapp_acme001",
    )
    allocation_service = MagicMock()
    allocation_service.allocate.return_value = allocation
    return {
        "state": AsyncMock(),
        "query": AsyncMock(),
        "repo": AsyncMock(),
        "allocation": allocation_service,
        "database_executor": AsyncMock(),
        "bootstrap": AsyncMock(),
        "bootstrap_reader": AsyncMock(),
        "catalog_seed": AsyncMock(),
        "tenant_seed": AsyncMock(),
        "activation": AsyncMock(),
        "allocation_result": allocation,
    }


@pytest.fixture
def orchestrator(orchestrator_mocks) -> DedicatedProvisioningOrchestrator:
    mocks = orchestrator_mocks
    mocks["query"].get_provisioning_status.return_value = _provisioning_status()
    mocks["repo"].list_steps_for_run.return_value = _step_rows()
    mocks["repo"].get_cliente_provisioning_snapshot.return_value = {
        "cliente_id": CLIENTE_ID,
        "tipo_instalacion": "dedicated",
        "provisioning_state": ProvisioningState.PROVISIONING.value,
        "current_provisioning_run_id": RUN_ID,
    }
    mocks["allocation"].allocate.return_value = mocks["allocation_result"]
    mocks["database_executor"].provision_physical_database.return_value = (
        DedicatedDatabaseProvisionResult(
            cliente_id=CLIENTE_ID,
            servidor="srv",
            database_name="erp_acme001",
            app_login_name="erpapp_acme001",
            app_login_password="secret-login",
            database_created=True,
            login_created=True,
            database_already_existed=False,
            login_already_existed=False,
        )
    )
    mocks["bootstrap"].run_dedicated_schema_bootstrap.return_value = BootstrapScriptRunResult(
        database_name="erp_acme001",
        cliente_id=CLIENTE_ID,
        profile="dedicated_schema_v2",
        scripts_executed=(
            "apply_schema_erp_v010",
            "apply_schema_tenant_store_v020",
            "apply_schema_rbac_v010",
        ),
        scripts_skipped=(),
        batches_executed=5,
    )
    mocks["catalog_seed"].run_catalog_seed.return_value = DedicatedCatalogSeedResult(
        database_name="erp_acme001",
        cliente_id=CLIENTE_ID,
        plan_suscripcion="trial",
        profile_code="trial",
        scripts_executed=("seed_catalogs",),
        scripts_skipped=(),
        batches_executed=1,
        row_verifications=(),
    )
    mocks["tenant_seed"].run_tenant_seed.return_value = DedicatedTenantSeedResult(
        database_name="erp_acme001",
        cliente_id=CLIENTE_ID,
        plan_suscripcion="trial",
        profile_code="trial",
        admin_username="admin",
        admin_usuario_id=ADMIN_USER_ID,
        admin_rol_id=uuid4(),
        empresa_id=uuid4(),
        steps_executed=("seed_tenant",),
        steps_skipped=(),
        row_verifications=(),
    )
    mocks["activation"].register_metadata.return_value = DedicatedActivationStepResult(
        step_code="register_metadata",
        idempotency_marker="conexion-stub",
    )
    mocks["activation"].activate_routing.return_value = DedicatedActivationStepResult(
        step_code="activate_routing",
        idempotency_marker="routing-stub",
    )
    mocks["activation"].mark_ready.return_value = DedicatedActivationStepResult(
        step_code="mark_ready",
        idempotency_marker="ready-stub",
    )
    return DedicatedProvisioningOrchestrator(
        state_service=mocks["state"],
        query_service=mocks["query"],
        repository=mocks["repo"],
        allocation_service=mocks["allocation"],
        database_executor=mocks["database_executor"],
        bootstrap_runner=mocks["bootstrap"],
        bootstrap_reader=mocks["bootstrap_reader"],
        catalog_seed_service=mocks["catalog_seed"],
        tenant_seed_service=mocks["tenant_seed"],
        activation_service=mocks["activation"],
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_08_saga_runs_s1_through_s10_stub(orchestrator, orchestrator_mocks):
    mocks = orchestrator_mocks
    with patch(
        "app.modules.tenant.application.services.dedicated_provisioning_orchestrator.execute_query",
        new_callable=AsyncMock,
        return_value=_cliente_profile(),
    ):
        with patch(
            "app.modules.tenant.application.services.dedicated_provisioning_orchestrator.settings"
        ) as mock_settings:
            mock_settings.DEDICATED_ENABLED = True
            job = ProvisioningJobRequest(
                cliente_id=CLIENTE_ID,
                provisioning_run_id=RUN_ID,
                ephemeral_context=ProvisioningSagaEphemeralContext(
                    admin_password="AdminPass123!",
                ),
            )
            await orchestrator.handle_job(job)

    # Opción B: la transición READY es acto terminal del Orchestrator tras cerrar S10.
    mocks["state"].transition_run_to_ready.assert_called_once_with(
        cliente_id=CLIENTE_ID,
        provisioning_run_id=RUN_ID,
    )
    mocks["activation"].register_metadata.assert_called_once()
    mocks["activation"].activate_routing.assert_called_once()
    mocks["activation"].mark_ready.assert_called_once()
    assert mocks["bootstrap"].run_dedicated_schema_bootstrap.call_count == 1
    mocks["tenant_seed"].run_tenant_seed.assert_called_once()
    seed_request = mocks["tenant_seed"].run_tenant_seed.call_args.args[0]
    assert seed_request.admin_password == "AdminPass123!"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_08_disabled_flag_noops(orchestrator, orchestrator_mocks):
    mocks = orchestrator_mocks
    with patch(
        "app.modules.tenant.application.services.dedicated_provisioning_orchestrator.settings"
    ) as mock_settings:
        mock_settings.DEDICATED_ENABLED = False
        job = ProvisioningJobRequest(
            cliente_id=CLIENTE_ID,
            provisioning_run_id=RUN_ID,
        )
        await orchestrator.handle_job(job)
    mocks["state"].mark_step_running.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_08_bootstrap_failure_reconciles_and_fails(
    orchestrator,
    orchestrator_mocks,
):
    mocks = orchestrator_mocks
    mocks["bootstrap"].run_dedicated_schema_bootstrap.side_effect = ConflictError(
        detail="DDL failed",
        internal_code="PROVISIONING_SCHEMA_FAILED",
    )
    mocks["bootstrap_reader"].list_applied_script_codes.return_value = frozenset(
        {"apply_schema_erp_v010"},
    )

    with patch(
        "app.modules.tenant.application.services.dedicated_provisioning_orchestrator.execute_query",
        new_callable=AsyncMock,
        return_value=_cliente_profile(),
    ):
        with patch(
            "app.modules.tenant.application.services.dedicated_provisioning_orchestrator.settings"
        ) as mock_settings:
            mock_settings.DEDICATED_ENABLED = True
            job = ProvisioningJobRequest(
                cliente_id=CLIENTE_ID,
                provisioning_run_id=RUN_ID,
                ephemeral_context=ProvisioningSagaEphemeralContext(
                    admin_password="AdminPass123!",
                ),
            )
            await orchestrator.handle_job(job)

    mocks["state"].transition_run_to_failed.assert_called()
    mocks["state"].mark_step_completed.assert_any_call(
        cliente_id=CLIENTE_ID,
        provisioning_run_id=RUN_ID,
        step_code=ProvisioningStepCode.APPLY_SCHEMA_ERP,
        idempotency_marker="apply_schema_erp_v010",
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_08_storage_marker_persisted_on_s2(orchestrator, orchestrator_mocks):
    mocks = orchestrator_mocks
    allocation = mocks["allocation_result"]
    marker = serialize_storage_allocation_marker(allocation)
    captured_marker: list[str] = []

    async def _mark_completed(**kwargs):
        if kwargs.get("step_code") == ProvisioningStepCode.STORAGE_ALLOCATION:
            captured_marker.append(kwargs.get("idempotency_marker"))

    mocks["state"].mark_step_completed.side_effect = _mark_completed
    mocks["database_executor"].provision_physical_database.side_effect = ConflictError(
        detail="stop",
        internal_code="PROVISIONING_CREATE_DATABASE_FAILED",
    )

    with patch(
        "app.modules.tenant.application.services.dedicated_provisioning_orchestrator.execute_query",
        new_callable=AsyncMock,
        return_value=_cliente_profile(),
    ):
        with patch(
            "app.modules.tenant.application.services.dedicated_provisioning_orchestrator.settings"
        ) as mock_settings:
            mock_settings.DEDICATED_ENABLED = True
            job = ProvisioningJobRequest(
                cliente_id=CLIENTE_ID,
                provisioning_run_id=RUN_ID,
            )
            await orchestrator.handle_job(job)

    mocks["allocation"].allocate.assert_called_once()
    assert captured_marker == [marker]
