"""PR-F4-02 — tests unitarios DedicatedProvisioningQueryService."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.modules.tenant.application.provisioning import ProvisioningState
from app.modules.tenant.application.services.dedicated_provisioning_query_service import (
    DedicatedProvisioningQueryService,
)

CLIENTE_ID = uuid4()
RUN_ID = uuid4()


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def service(repo: AsyncMock) -> DedicatedProvisioningQueryService:
    return DedicatedProvisioningQueryService(repository=repo)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_02_query_status_none_when_cliente_missing(
    service: DedicatedProvisioningQueryService,
    repo: AsyncMock,
):
    repo.get_cliente_provisioning_snapshot.return_value = None
    assert await service.get_provisioning_status(CLIENTE_ID) is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_02_query_status_builds_contract_shape(
    service: DedicatedProvisioningQueryService,
    repo: AsyncMock,
):
    repo.get_cliente_provisioning_snapshot.return_value = {
        "cliente_id": CLIENTE_ID,
        "tipo_instalacion": "dedicated",
        "provisioning_state": ProvisioningState.PROVISIONING.value,
        "current_provisioning_run_id": RUN_ID,
    }
    repo.get_run_by_id.return_value = {
        "provisioning_run_id": RUN_ID,
        "current_step_code": "registry",
        "started_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "ready_at": None,
        "failed_at": None,
        "last_error_code": None,
        "last_error_message": None,
    }
    repo.list_steps_for_run.return_value = [
        {
            "step_code": "registry",
            "step_status": "running",
            "started_at": datetime.utcnow(),
            "completed_at": None,
        }
    ]

    status = await service.get_provisioning_status(CLIENTE_ID)

    assert status is not None
    assert status.provisioning_state == ProvisioningState.PROVISIONING
    assert status.provisioning_run_id == RUN_ID
    assert status.abort_allowed is True
    assert status.retry_allowed is False
    assert len(status.steps) == 1
    assert status.steps[0].code == "registry"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_02_query_retry_allowed_on_failed(
    service: DedicatedProvisioningQueryService,
    repo: AsyncMock,
):
    repo.get_cliente_provisioning_snapshot.return_value = {
        "cliente_id": CLIENTE_ID,
        "tipo_instalacion": "dedicated",
        "provisioning_state": ProvisioningState.FAILED.value,
        "current_provisioning_run_id": RUN_ID,
    }
    repo.get_run_by_id.return_value = {
        "provisioning_run_id": RUN_ID,
        "current_step_code": "create_database",
        "started_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "ready_at": None,
        "failed_at": datetime.utcnow(),
        "last_error_code": "DDL_FAILED",
        "last_error_message": "ops-safe",
    }
    repo.list_steps_for_run.return_value = []

    status = await service.get_provisioning_status(CLIENTE_ID)

    assert status is not None
    assert status.retry_allowed is True
    assert status.abort_allowed is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_02_has_active_provisioning(
    service: DedicatedProvisioningQueryService,
    repo: AsyncMock,
):
    repo.get_current_run.return_value = {
        "provisioning_state": ProvisioningState.PROVISIONING.value,
    }
    assert await service.has_active_provisioning(CLIENTE_ID) is True

    repo.get_current_run.return_value = {
        "provisioning_state": ProvisioningState.READY.value,
    }
    assert await service.has_active_provisioning(CLIENTE_ID) is False
