"""PR-F4-10 — tests unitarios DedicatedProvisioningCompensationService."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError
from app.infrastructure.provisioning.dedicated_database_types import (
    DedicatedDatabaseDropResult,
)
from app.infrastructure.provisioning.dedicated_provisioning_compensation_service import (
    DedicatedProvisioningCompensationService,
)
from app.modules.tenant.application.provisioning import ProvisioningState, ProvisioningStepCode
from app.modules.tenant.application.services.storage_allocation_types import (
    serialize_storage_allocation_marker,
    StorageAllocationResult,
)

CLIENTE_ID = uuid4()
RUN_ID = uuid4()
CONEXION_ID = uuid4()


def _snapshot(*, state: str = "failed") -> dict:
    return {
        "cliente_id": CLIENTE_ID,
        "tipo_instalacion": "dedicated",
        "provisioning_state": state,
        "current_provisioning_run_id": RUN_ID,
    }


def _allocation_marker() -> str:
    return serialize_storage_allocation_marker(
        StorageAllocationResult(
            servidor="sql.local",
            database_name="erp_acme001",
            app_login_name="erpapp_acme001",
        ),
    )


def _steps_through_s8() -> list[dict]:
    rows = []
    order = 1
    for code in ProvisioningStepCode:
        status = "pending"
        marker = None
        if code.value in {
            "registry",
            "storage_allocation",
            "create_database",
            "apply_schema_erp",
            "apply_schema_rbac",
            "apply_catalogs",
            "seed_tenant",
            "register_metadata",
        }:
            status = "completed"
            if code == ProvisioningStepCode.STORAGE_ALLOCATION:
                marker = _allocation_marker()
        rows.append(
            {
                "step_code": code.value,
                "step_status": status,
                "saga_order": order,
                "idempotency_marker": marker,
            }
        )
        order += 1
    return rows


@pytest.fixture
def compensation_mocks() -> dict[str, AsyncMock]:
    return {
        "state": AsyncMock(),
        "query": AsyncMock(),
        "repo": AsyncMock(),
        "database_executor": AsyncMock(),
        "metadata": AsyncMock(),
        "dispatcher": AsyncMock(),
    }


@pytest.fixture
def compensation_service(compensation_mocks) -> DedicatedProvisioningCompensationService:
    mocks = compensation_mocks
    mocks["repo"].get_cliente_provisioning_snapshot.return_value = _snapshot()
    mocks["repo"].list_steps_for_run.return_value = _steps_through_s8()
    mocks["database_executor"].drop_physical_database.return_value = (
        DedicatedDatabaseDropResult(
            cliente_id=CLIENTE_ID,
            database_name="erp_acme001",
            app_login_name="erpapp_acme001",
            database_existed=True,
            database_dropped=True,
            login_existed=True,
            login_dropped=True,
        )
    )
    mocks["metadata"].cleanup_primary_connection.return_value = True
    return DedicatedProvisioningCompensationService(
        state_service=mocks["state"],
        query_service=mocks["query"],
        repository=mocks["repo"],
        database_executor=mocks["database_executor"],
        metadata_service=mocks["metadata"],
        dispatcher=mocks["dispatcher"],
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_10_compensate_failed_run_s10_to_s3(compensation_service, compensation_mocks):
    mocks = compensation_mocks
    with patch(
        "app.infrastructure.provisioning.dedicated_provisioning_compensation_service.invalidate_client_connection_cache"
    ) as mock_invalidate:
        with patch.object(
            compensation_service,
            "_reset_provisioning_steps",
            new_callable=AsyncMock,
        ) as mock_reset:
            result = await compensation_service.compensate_for_failed_run(
                cliente_id=CLIENTE_ID,
                provisioning_run_id=RUN_ID,
            )

    mocks["metadata"].cleanup_primary_connection.assert_called_once_with(CLIENTE_ID)
    mocks["database_executor"].drop_physical_database.assert_called_once()
    mock_invalidate.assert_called()
    mock_reset.assert_called_once()
    assert result.database_dropped is True
    assert result.connection_deactivated is True
    assert ProvisioningStepCode.CREATE_DATABASE.value in result.steps_compensated
    assert result.steps_reset_from_order == 3


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_10_compensate_rejects_ready_tenant(compensation_service, compensation_mocks):
    compensation_mocks["repo"].get_cliente_provisioning_snapshot.return_value = _snapshot(
        state=ProvisioningState.READY.value,
    )
    with pytest.raises(ConflictError) as exc_info:
        await compensation_service.compensate_for_failed_run(
            cliente_id=CLIENTE_ID,
            provisioning_run_id=RUN_ID,
        )
    assert exc_info.value.internal_code == "PROVISIONING_COMPENSATION_NOT_ALLOWED"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_10_abort_transitions_failed_then_compensates(
    compensation_service,
    compensation_mocks,
):
    compensation_mocks["repo"].get_cliente_provisioning_snapshot.return_value = _snapshot(
        state=ProvisioningState.PROVISIONING.value,
    )
    with patch.object(
        compensation_service,
        "compensate_for_failed_run",
        new_callable=AsyncMock,
    ) as mock_compensate:
        mock_compensate.return_value = MagicMock()
        with patch(
            "app.infrastructure.provisioning.dedicated_provisioning_compensation_service.settings"
        ) as mock_settings:
            mock_settings.DEDICATED_ENABLED = True
            await compensation_service.abort_provisioning_run(
                cliente_id=CLIENTE_ID,
                provisioning_run_id=RUN_ID,
                reason="ops abort",
            )

    compensation_mocks["state"].transition_run_to_failed.assert_called_once()
    mock_compensate.assert_called_once_with(
        cliente_id=CLIENTE_ID,
        provisioning_run_id=RUN_ID,
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_10_retry_dispatches_after_begin_retry(compensation_service, compensation_mocks):
    transition = MagicMock()
    compensation_mocks["state"].begin_retry_from_failed.return_value = transition
    dispatch_result = MagicMock(dispatched=True)
    compensation_mocks["dispatcher"].dispatch_for_run.return_value = dispatch_result

    with patch(
        "app.infrastructure.provisioning.dedicated_provisioning_compensation_service.settings"
    ) as mock_settings:
        mock_settings.DEDICATED_ENABLED = True
        result = await compensation_service.retry_provisioning_run(
            cliente_id=CLIENTE_ID,
            provisioning_run_id=RUN_ID,
        )

    compensation_mocks["state"].begin_retry_from_failed.assert_called_once_with(
        cliente_id=CLIENTE_ID,
        provisioning_run_id=RUN_ID,
    )
    compensation_mocks["dispatcher"].dispatch_for_run.assert_called_once()
    assert result[0] is transition
    assert result[1] is dispatch_result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_10_compensate_idempotent_when_no_completed_steps(
    compensation_service,
    compensation_mocks,
):
    compensation_mocks["repo"].list_steps_for_run.return_value = [
        {
            "step_code": code.value,
            "step_status": "pending",
            "saga_order": idx,
            "idempotency_marker": None,
        }
        for idx, code in enumerate(ProvisioningStepCode, start=1)
    ]
    result = await compensation_service.compensate_for_failed_run(
        cliente_id=CLIENTE_ID,
        provisioning_run_id=RUN_ID,
    )
    assert result.idempotent is True
    assert result.steps_compensated == ()
