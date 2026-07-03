"""PR-F4-09 — orchestrator wiring activation real markers."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.infrastructure.provisioning.dedicated_activation_types import (
    DedicatedActivationStepResult,
)
from app.modules.tenant.application.provisioning import (
    ProvisioningJobRequest,
    ProvisioningState,
    ProvisioningStepCode,
    ProvisioningStepStatus,
    SAGA_STEP_ORDER,
)
from app.modules.tenant.application.provisioning.provisioning_status_read import (
    DedicatedProvisioningStatusSnapshot,
)
from app.modules.tenant.application.services.dedicated_provisioning_orchestrator import (
    DedicatedProvisioningOrchestrator,
)

CLIENTE_ID = uuid4()
RUN_ID = uuid4()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_09_orchestrator_persists_activation_markers():
    activation = AsyncMock()
    activation.register_metadata.return_value = DedicatedActivationStepResult(
        step_code="register_metadata",
        idempotency_marker="conexion-uuid",
    )
    activation.activate_routing.return_value = DedicatedActivationStepResult(
        step_code="activate_routing",
        idempotency_marker="routing_smoke_v1:tenant",
    )
    activation.mark_ready.return_value = DedicatedActivationStepResult(
        step_code="mark_ready",
        idempotency_marker=f"ready_run:{RUN_ID}",
    )

    state = AsyncMock()
    query = AsyncMock()
    query.get_provisioning_status.return_value = DedicatedProvisioningStatusSnapshot(
        cliente_id=CLIENTE_ID,
        tipo_instalacion="dedicated",
        provisioning_state=ProvisioningState.PROVISIONING,
        provisioning_run_id=RUN_ID,
        current_step="register_metadata",
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

    steps = [
        {
            "step_code": code.value,
            "step_status": ProvisioningStepStatus.COMPLETED.value,
            "saga_order": idx,
            "idempotency_marker": "done",
        }
        for idx, code in enumerate(SAGA_STEP_ORDER[:-3], start=1)
    ]
    for idx, code in enumerate(SAGA_STEP_ORDER[-3:], start=len(SAGA_STEP_ORDER) - 2):
        steps.append(
            {
                "step_code": code.value,
                "step_status": ProvisioningStepStatus.PENDING.value,
                "saga_order": idx,
                "idempotency_marker": None,
            }
        )

    repo = AsyncMock()
    repo.list_steps_for_run.return_value = steps
    allocation = MagicMock()
    allocation.servidor = "srv"
    allocation.database_name = "erp_acme001"
    allocation.app_login_name = "erpapp_acme001"

    orch = DedicatedProvisioningOrchestrator(
        state_service=state,
        query_service=query,
        repository=repo,
        allocation_service=MagicMock(),
        database_executor=AsyncMock(),
        bootstrap_runner=AsyncMock(),
        bootstrap_reader=AsyncMock(),
        catalog_seed_service=AsyncMock(),
        tenant_seed_service=AsyncMock(),
        activation_service=activation,
    )

    with patch(
        "app.modules.tenant.application.services.dedicated_provisioning_orchestrator.settings"
    ) as mock_settings:
        mock_settings.DEDICATED_ENABLED = True
        job = ProvisioningJobRequest(
            cliente_id=CLIENTE_ID,
            provisioning_run_id=RUN_ID,
        )
        runtime_allocation = allocation
        with patch.object(orch, "_hydrate_runtime_from_completed_step") as mock_hydrate:
            async def _hydrate(step_code, step_row, runtime):
                runtime.allocation = runtime_allocation
                runtime.app_login_password = "pwd"

            mock_hydrate.side_effect = _hydrate
            await orch.handle_job(job)

    state.mark_step_completed.assert_any_call(
        cliente_id=CLIENTE_ID,
        provisioning_run_id=RUN_ID,
        step_code=ProvisioningStepCode.REGISTER_METADATA,
        idempotency_marker="conexion-uuid",
    )
    state.mark_step_completed.assert_any_call(
        cliente_id=CLIENTE_ID,
        provisioning_run_id=RUN_ID,
        step_code=ProvisioningStepCode.MARK_READY,
        idempotency_marker=f"ready_run:{RUN_ID}",
    )
