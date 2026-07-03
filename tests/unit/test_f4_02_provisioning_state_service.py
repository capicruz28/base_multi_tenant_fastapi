"""PR-F4-02 — tests unitarios TenantProvisioningStateService."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.modules.tenant.application.provisioning import (
    ProvisioningState,
    ProvisioningStepCode,
    ProvisioningStepStatus,
)
from app.modules.tenant.application.services.tenant_provisioning_state_service import (
    TenantProvisioningStateService,
    _first_incomplete_saga_order,
)

CLIENTE_ID = uuid4()
RUN_ID = uuid4()
STEP_ID = uuid4()
USUARIO_ID = uuid4()


def _dedicated_snapshot(
    *,
    provisioning_state: str | None = None,
    run_id=RUN_ID,
) -> dict:
    return {
        "cliente_id": CLIENTE_ID,
        "tipo_instalacion": "dedicated",
        "provisioning_state": provisioning_state,
        "current_provisioning_run_id": run_id,
    }


def _run_row(state: ProvisioningState, *, attempt_number: int = 1) -> dict:
    return {
        "provisioning_run_id": RUN_ID,
        "cliente_id": CLIENTE_ID,
        "provisioning_state": state.value,
        "is_current": True,
        "attempt_number": attempt_number,
        "idempotency_key": None,
        "current_step_code": ProvisioningStepCode.REGISTRY.value,
        "started_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "ready_at": None,
        "failed_at": None,
        "last_error_code": None,
        "last_error_message": None,
        "created_by_usuario_id": USUARIO_ID,
    }


def _step_row(
    code: ProvisioningStepCode,
    status: ProvisioningStepStatus,
    saga_order: int,
) -> dict:
    return {
        "provisioning_step_id": STEP_ID,
        "provisioning_run_id": RUN_ID,
        "cliente_id": CLIENTE_ID,
        "step_code": code.value,
        "saga_order": saga_order,
        "step_status": status.value,
        "started_at": None,
        "completed_at": None,
        "error_code": None,
        "error_message": None,
        "idempotency_marker": None,
    }


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def service(repo: AsyncMock) -> TenantProvisioningStateService:
    return TenantProvisioningStateService(repository=repo)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_02_initialize_rejects_shared_tenant(service: TenantProvisioningStateService, repo: AsyncMock):
    repo.get_cliente_provisioning_snapshot.return_value = {
        "cliente_id": CLIENTE_ID,
        "tipo_instalacion": "shared",
        "provisioning_state": None,
        "current_provisioning_run_id": None,
    }

    with pytest.raises(ValidationError) as exc:
        await service.initialize_provisioning_run(cliente_id=CLIENTE_ID)

    assert exc.value.internal_code == "PROVISIONING_NOT_DEDICATED"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_02_initialize_rejects_ready_tenant(service: TenantProvisioningStateService, repo: AsyncMock):
    repo.get_cliente_provisioning_snapshot.return_value = _dedicated_snapshot(
        provisioning_state=ProvisioningState.READY.value,
    )

    with pytest.raises(ConflictError) as exc:
        await service.initialize_provisioning_run(cliente_id=CLIENTE_ID)

    assert exc.value.internal_code == "PROVISIONING_ALREADY_READY"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_02_initialize_idempotency_returns_existing(service: TenantProvisioningStateService, repo: AsyncMock):
    repo.get_cliente_provisioning_snapshot.return_value = _dedicated_snapshot(provisioning_state=None)
    repo.get_run_by_idempotency_key.return_value = _run_row(ProvisioningState.PROVISIONING)

    result = await service.initialize_provisioning_run(
        cliente_id=CLIENTE_ID,
        idempotency_key="idem-123",
    )

    assert result.provisioning_run_id == RUN_ID
    assert result.provisioning_state == ProvisioningState.PROVISIONING
    repo.insert_run.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_02_initialize_creates_run_and_steps(
    service: TenantProvisioningStateService,
    repo: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
):
    repo.get_cliente_provisioning_snapshot.return_value = _dedicated_snapshot(provisioning_state=None)
    repo.get_run_by_idempotency_key.return_value = None
    repo.get_current_run.return_value = None

    mock_uow = MagicMock()
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=False)
    mock_uow.session = MagicMock()

    monkeypatch.setattr(
        "app.modules.tenant.application.services.tenant_provisioning_state_service.UnitOfWork",
        lambda **kwargs: mock_uow,
    )
    result = await service.initialize_provisioning_run(cliente_id=CLIENTE_ID)

    assert result.provisioning_state == ProvisioningState.PROVISIONING
    repo.deactivate_current_runs.assert_awaited_once()
    repo.insert_run.assert_awaited_once()
    repo.insert_initial_steps_for_run.assert_awaited_once()
    repo.update_cliente_provisioning_state.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_02_illegal_run_transition_when_already_ready(
    service: TenantProvisioningStateService,
    repo: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
):
    repo.get_cliente_provisioning_snapshot.return_value = _dedicated_snapshot(
        provisioning_state=ProvisioningState.READY.value,
    )

    mock_uow = MagicMock()
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=False)
    mock_uow.execute = AsyncMock(return_value=[_run_row(ProvisioningState.READY)])

    monkeypatch.setattr(
        "app.modules.tenant.application.services.tenant_provisioning_state_service.UnitOfWork",
        lambda **kwargs: mock_uow,
    )
    with pytest.raises(ValidationError) as exc:
        await service.transition_run_to_ready(
            cliente_id=CLIENTE_ID,
            provisioning_run_id=RUN_ID,
        )
    assert exc.value.internal_code == "PROVISIONING_STATE_NOOP"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_02_mark_step_completed_persists_history(
    service: TenantProvisioningStateService,
    repo: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
):
    repo.get_step_by_code.return_value = _step_row(
        ProvisioningStepCode.REGISTRY,
        ProvisioningStepStatus.RUNNING,
        1,
    )

    mock_uow = MagicMock()
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=False)
    mock_uow.execute = AsyncMock(return_value=[_run_row(ProvisioningState.PROVISIONING)])
    repo.update_step_status.return_value = 1
    repo.update_run_current_step.return_value = 1

    monkeypatch.setattr(
        "app.modules.tenant.application.services.tenant_provisioning_state_service.UnitOfWork",
        lambda **kwargs: mock_uow,
    )
    result = await service.mark_step_completed(
        cliente_id=CLIENTE_ID,
        provisioning_run_id=RUN_ID,
        step_code=ProvisioningStepCode.REGISTRY,
        idempotency_marker="registry:v1",
    )

    assert result.current_status == ProvisioningStepStatus.COMPLETED.value
    repo.update_step_status.assert_awaited_once()
    repo.update_run_current_step.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_02_mark_step_illegal_transition_rejected(
    service: TenantProvisioningStateService,
    repo: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
):
    repo.get_step_by_code.return_value = _step_row(
        ProvisioningStepCode.REGISTRY,
        ProvisioningStepStatus.PENDING,
        1,
    )

    mock_uow = MagicMock()
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=False)
    mock_uow.execute = AsyncMock(return_value=[_run_row(ProvisioningState.PROVISIONING)])

    monkeypatch.setattr(
        "app.modules.tenant.application.services.tenant_provisioning_state_service.UnitOfWork",
        lambda **kwargs: mock_uow,
    )
    with pytest.raises(ValidationError):
        await service.mark_step_completed(
            cliente_id=CLIENTE_ID,
            provisioning_run_id=RUN_ID,
            step_code=ProvisioningStepCode.REGISTRY,
        )


@pytest.mark.unit
def test_f4_02_first_incomplete_saga_order():
    steps = [
        _step_row(ProvisioningStepCode.REGISTRY, ProvisioningStepStatus.COMPLETED, 1),
        _step_row(
            ProvisioningStepCode.STORAGE_ALLOCATION,
            ProvisioningStepStatus.FAILED,
            2,
        ),
        _step_row(ProvisioningStepCode.CREATE_DATABASE, ProvisioningStepStatus.PENDING, 3),
    ]
    assert _first_incomplete_saga_order(steps) == 2
