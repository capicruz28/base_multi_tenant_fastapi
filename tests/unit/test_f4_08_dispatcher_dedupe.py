"""PR-F4-08 — tests dedupe dispatcher run_id."""
from __future__ import annotations

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.modules.tenant.application.provisioning import ProvisioningJobRequest
from app.modules.tenant.application.provisioning.provisioning_status_read import (
    DedicatedProvisioningStatusSnapshot,
)
from app.modules.tenant.application.services.provisioning_job_dispatcher import (
    ProvisioningJobDispatcher,
    _active_run_ids,
    drain_pending_jobs,
)

CLIENTE_ID = uuid4()
RUN_ID = uuid4()


def _status() -> DedicatedProvisioningStatusSnapshot:
    return DedicatedProvisioningStatusSnapshot(
        cliente_id=CLIENTE_ID,
        tipo_instalacion="dedicated",
        provisioning_state="provisioning",
        provisioning_run_id=RUN_ID,
        current_step="registry",
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


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_08_dispatcher_dedupes_active_run_id():
    _active_run_ids.clear()
    query = AsyncMock()
    query.get_provisioning_status.return_value = _status()
    dispatcher = ProvisioningJobDispatcher(query_service=query)

    started = asyncio.Event()

    async def slow_handler(job: ProvisioningJobRequest) -> None:
        started.set()
        await asyncio.sleep(0.2)

    with patch(
        "app.modules.tenant.application.services.provisioning_job_dispatcher.settings"
    ) as mock_settings:
        mock_settings.PROVISIONING_DISPATCHER_ENABLED = True
        mock_settings.PROVISIONING_DISPATCHER_SYNC = False
        first = await dispatcher.dispatch_for_run(
            cliente_id=CLIENTE_ID,
            provisioning_run_id=RUN_ID,
            handler=slow_handler,
        )
        second = await dispatcher.dispatch_for_run(
            cliente_id=CLIENTE_ID,
            provisioning_run_id=RUN_ID,
            handler=slow_handler,
        )

    assert first.dispatched is True
    assert second.dispatched is False
    await asyncio.wait_for(started.wait(), timeout=1.0)
    await drain_pending_jobs(timeout_seconds=2.0)
    _active_run_ids.clear()
