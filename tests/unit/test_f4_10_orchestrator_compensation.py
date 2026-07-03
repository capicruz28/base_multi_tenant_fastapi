"""PR-F4-10 — wiring compensación en orchestrator."""
from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.modules.tenant.application.services.dedicated_provisioning_orchestrator import (
    DedicatedProvisioningOrchestrator,
)

CLIENTE_ID = uuid4()
RUN_ID = uuid4()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_10_orchestrator_delegates_abort_and_retry():
    compensation = AsyncMock()
    orch = DedicatedProvisioningOrchestrator(compensation_service=compensation)

    await orch.abort_provisioning_run(
        cliente_id=CLIENTE_ID,
        provisioning_run_id=RUN_ID,
        reason="test",
    )
    await orch.compensate_failed_run(
        cliente_id=CLIENTE_ID,
        provisioning_run_id=RUN_ID,
    )
    await orch.retry_provisioning_run(
        cliente_id=CLIENTE_ID,
        provisioning_run_id=RUN_ID,
    )

    compensation.abort_provisioning_run.assert_called_once()
    compensation.compensate_for_failed_run.assert_called_once()
    compensation.retry_provisioning_run.assert_called_once()
