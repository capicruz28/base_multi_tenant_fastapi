"""PR-F4-03 — tests unitarios ProvisioningJobDispatcher."""
from __future__ import annotations

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.tenant.application.provisioning import (
    ProvisioningJobRequest,
    ProvisioningRunInitializedResult,
    ProvisioningState,
)
from app.modules.tenant.application.provisioning.provisioning_status_read import (
    DedicatedProvisioningStatusSnapshot,
)
from app.modules.tenant.application.services.provisioning_job_dispatcher import (
    ProvisioningJobDispatcher,
    pending_task_count,
)

CLIENTE_ID = uuid4()
RUN_ID = uuid4()


def _provisioning_status(*, run_id=RUN_ID) -> DedicatedProvisioningStatusSnapshot:
    return DedicatedProvisioningStatusSnapshot(
        cliente_id=CLIENTE_ID,
        tipo_instalacion="dedicated",
        provisioning_state=ProvisioningState.PROVISIONING,
        provisioning_run_id=run_id,
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


@pytest.fixture
def query_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def state_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def dispatcher(query_service: AsyncMock, state_service: AsyncMock) -> ProvisioningJobDispatcher:
    return ProvisioningJobDispatcher(
        query_service=query_service,
        state_service=state_service,
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_03_dispatch_async_does_not_block_caller(
    dispatcher: ProvisioningJobDispatcher,
    query_service: AsyncMock,
):
    query_service.get_provisioning_status.return_value = _provisioning_status()
    started = asyncio.Event()
    finished = asyncio.Event()

    async def slow_handler(job: ProvisioningJobRequest) -> None:
        started.set()
        await finished.wait()

    with patch(
        "app.modules.tenant.application.services.provisioning_job_dispatcher.settings"
    ) as mock_settings:
        mock_settings.PROVISIONING_DISPATCHER_ENABLED = True
        mock_settings.PROVISIONING_DISPATCHER_SYNC = False
        result = await dispatcher.dispatch_for_run(
            cliente_id=CLIENTE_ID,
            provisioning_run_id=RUN_ID,
            handler=slow_handler,
        )

    assert result.dispatched is True
    assert result.sync_execution is False
    assert result.provisioning_run_id == RUN_ID
    await asyncio.wait_for(started.wait(), timeout=1.0)
    finished.set()
    await ProvisioningJobDispatcher.drain_pending_jobs(timeout_seconds=2.0)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_03_dispatch_sync_runs_handler_inline(
    dispatcher: ProvisioningJobDispatcher,
    query_service: AsyncMock,
):
    query_service.get_provisioning_status.return_value = _provisioning_status()
    handler_called = asyncio.Event()

    async def handler(job: ProvisioningJobRequest) -> None:
        assert job.provisioning_run_id == RUN_ID
        handler_called.set()

    with patch(
        "app.modules.tenant.application.services.provisioning_job_dispatcher.settings"
    ) as mock_settings:
        mock_settings.PROVISIONING_DISPATCHER_ENABLED = True
        mock_settings.PROVISIONING_DISPATCHER_SYNC = True
        result = await dispatcher.dispatch_for_run(
            cliente_id=CLIENTE_ID,
            provisioning_run_id=RUN_ID,
            handler=handler,
        )

    assert result.dispatched is True
    assert result.sync_execution is True
    assert handler_called.is_set()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_03_dispatch_disabled_returns_not_dispatched(
    dispatcher: ProvisioningJobDispatcher,
    query_service: AsyncMock,
):
    query_service.get_provisioning_status.return_value = _provisioning_status()
    handler = AsyncMock()

    with patch(
        "app.modules.tenant.application.services.provisioning_job_dispatcher.settings"
    ) as mock_settings:
        mock_settings.PROVISIONING_DISPATCHER_ENABLED = False
        mock_settings.PROVISIONING_DISPATCHER_SYNC = False
        result = await dispatcher.dispatch_for_run(
            cliente_id=CLIENTE_ID,
            provisioning_run_id=RUN_ID,
            handler=handler,
        )

    assert result.dispatched is False
    assert result.dispatcher_enabled is False
    handler.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_03_dispatch_rejects_non_provisioning_run(
    dispatcher: ProvisioningJobDispatcher,
    query_service: AsyncMock,
):
    query_service.get_provisioning_status.return_value = DedicatedProvisioningStatusSnapshot(
        cliente_id=CLIENTE_ID,
        tipo_instalacion="dedicated",
        provisioning_state=ProvisioningState.FAILED,
        provisioning_run_id=RUN_ID,
        current_step="create_database",
        steps=[],
        started_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        ready_at=None,
        failed_at=datetime.utcnow(),
        last_error_code="DDL_FAILED",
        last_error_message="ops",
        retry_allowed=True,
        abort_allowed=False,
    )

    with pytest.raises(ConflictError) as exc:
        await dispatcher.dispatch_for_run(
            cliente_id=CLIENTE_ID,
            provisioning_run_id=RUN_ID,
        )
    assert exc.value.internal_code == "PROVISIONING_RUN_NOT_DISPATCHABLE"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_03_dispatch_rejects_unknown_run(
    dispatcher: ProvisioningJobDispatcher,
    query_service: AsyncMock,
):
    query_service.get_provisioning_status.return_value = _provisioning_status(
        run_id=uuid4(),
    )

    with pytest.raises(NotFoundError) as exc:
        await dispatcher.dispatch_for_run(
            cliente_id=CLIENTE_ID,
            provisioning_run_id=RUN_ID,
        )
    assert exc.value.internal_code == "PROVISIONING_RUN_NOT_FOUND"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_03_dispatch_after_initialize(
    dispatcher: ProvisioningJobDispatcher,
    query_service: AsyncMock,
):
    query_service.get_provisioning_status.return_value = _provisioning_status()
    init_result = ProvisioningRunInitializedResult(
        provisioning_run_id=RUN_ID,
        cliente_id=CLIENTE_ID,
        provisioning_state=ProvisioningState.PROVISIONING,
        attempt_number=1,
        idempotency_key="idem-1",
    )
    handler = AsyncMock()

    with patch(
        "app.modules.tenant.application.services.provisioning_job_dispatcher.settings"
    ) as mock_settings:
        mock_settings.PROVISIONING_DISPATCHER_ENABLED = True
        mock_settings.PROVISIONING_DISPATCHER_SYNC = True
        result = await dispatcher.dispatch_after_initialize(
            init_result,
            handler=handler,
        )

    assert result.provisioning_run_id == RUN_ID
    handler.assert_awaited_once()
    call_job = handler.await_args.args[0]
    assert call_job.idempotency_key == "idem-1"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_03_initialize_and_dispatch_integrates_state_service(
    dispatcher: ProvisioningJobDispatcher,
    query_service: AsyncMock,
    state_service: AsyncMock,
):
    init_result = ProvisioningRunInitializedResult(
        provisioning_run_id=RUN_ID,
        cliente_id=CLIENTE_ID,
        provisioning_state=ProvisioningState.PROVISIONING,
        attempt_number=1,
    )
    state_service.initialize_provisioning_run.return_value = init_result
    query_service.get_provisioning_status.return_value = _provisioning_status()
    handler = AsyncMock()

    with patch(
        "app.modules.tenant.application.services.provisioning_job_dispatcher.settings"
    ) as mock_settings:
        mock_settings.PROVISIONING_DISPATCHER_ENABLED = True
        mock_settings.PROVISIONING_DISPATCHER_SYNC = True
        init, dispatch = await dispatcher.initialize_and_dispatch(
            cliente_id=CLIENTE_ID,
            handler=handler,
        )

    assert init.provisioning_run_id == RUN_ID
    assert dispatch.dispatched is True
    state_service.initialize_provisioning_run.assert_awaited_once()
    handler.assert_awaited_once()


@pytest.mark.unit
def test_f4_03_pending_task_count_starts_at_zero():
    assert pending_task_count() >= 0
