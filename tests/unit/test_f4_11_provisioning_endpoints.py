"""PR-F4-11 — endpoints provisioning operations API."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.modules.tenant.application.provisioning import ProvisioningState
from app.modules.tenant.application.provisioning.provisioning_state_result import (
    ProvisioningStateTransitionResult,
)
from app.modules.tenant.application.provisioning.provisioning_status_read import (
    DedicatedProvisioningStatusSnapshot,
)
from app.modules.tenant.presentation.schemas_provisioning import ProvisioningAbortRequest
from app.modules.tenant.presentation import endpoints_clientes

CLIENTE_ID = uuid4()
RUN_ID = uuid4()


def _unwrap(fn):
    while hasattr(fn, "__wrapped__"):
        fn = fn.__wrapped__
    return fn


get_status = _unwrap(endpoints_clientes.obtener_provisioning_status)
retry_provisioning = _unwrap(endpoints_clientes.reintentar_provisioning)
abort_provisioning = _unwrap(endpoints_clientes.abortar_provisioning)


def _fake_user():
    user = MagicMock()
    user.nombre_usuario = "pytest-superadmin"
    return user


def _snapshot(*, state: ProvisioningState) -> DedicatedProvisioningStatusSnapshot:
    return DedicatedProvisioningStatusSnapshot(
        cliente_id=CLIENTE_ID,
        tipo_instalacion="dedicated",
        provisioning_state=state,
        provisioning_run_id=RUN_ID,
        current_step="registry",
        steps=[],
        started_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        ready_at=None,
        failed_at=None,
        last_error_code=None,
        last_error_message=None,
        retry_allowed=state == ProvisioningState.FAILED,
        abort_allowed=state == ProvisioningState.PROVISIONING,
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_11_get_status_maps_dedicated_snapshot():
    with patch.object(
        endpoints_clientes._provisioning_query_service,
        "get_provisioning_status",
        new_callable=AsyncMock,
        return_value=_snapshot(state=ProvisioningState.PROVISIONING),
    ):
        response = await get_status(CLIENTE_ID, current_user=_fake_user())

    assert response.cliente_id == CLIENTE_ID
    assert response.provisioning_state == "provisioning"
    assert response.abort_allowed is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_11_get_status_404_when_missing():
    with patch.object(
        endpoints_clientes._provisioning_query_service,
        "get_provisioning_status",
        new_callable=AsyncMock,
        return_value=None,
    ):
        with pytest.raises(NotFoundError):
            await get_status(CLIENTE_ID, current_user=_fake_user())


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_11_get_status_rejects_shared_tenant():
    shared = DedicatedProvisioningStatusSnapshot(
        cliente_id=CLIENTE_ID,
        tipo_instalacion="shared",
        provisioning_state=None,
        provisioning_run_id=None,
        current_step=None,
        steps=[],
        started_at=None,
        updated_at=None,
        ready_at=None,
        failed_at=None,
        last_error_code=None,
        last_error_message=None,
        retry_allowed=False,
        abort_allowed=False,
    )
    with patch.object(
        endpoints_clientes._provisioning_query_service,
        "get_provisioning_status",
        new_callable=AsyncMock,
        return_value=shared,
    ):
        with pytest.raises(ValidationError) as exc_info:
            await get_status(CLIENTE_ID, current_user=_fake_user())
    assert exc_info.value.internal_code == "NOT_DEDICATED_TENANT"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_11_retry_only_when_failed():
    with patch.object(
        endpoints_clientes._provisioning_query_service,
        "get_provisioning_status",
        new_callable=AsyncMock,
        return_value=_snapshot(state=ProvisioningState.PROVISIONING),
    ):
        with pytest.raises(ConflictError) as exc_info:
            await retry_provisioning(CLIENTE_ID, current_user=_fake_user())
    assert exc_info.value.internal_code == "PROVISIONING_ALREADY_RUNNING"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_11_retry_dispatches_orchestrator():
    transition = ProvisioningStateTransitionResult(
        provisioning_run_id=RUN_ID,
        cliente_id=CLIENTE_ID,
        previous_state=ProvisioningState.FAILED,
        current_state=ProvisioningState.PROVISIONING,
        updated_at=datetime.utcnow(),
    )
    with patch.object(
        endpoints_clientes._provisioning_query_service,
        "get_provisioning_status",
        new_callable=AsyncMock,
        return_value=_snapshot(state=ProvisioningState.FAILED),
    ):
        with patch.object(
            endpoints_clientes._provisioning_orchestrator,
            "retry_provisioning_run",
            new_callable=AsyncMock,
            return_value=(transition, MagicMock()),
        ) as mock_retry:
            response = await retry_provisioning(CLIENTE_ID, current_user=_fake_user())

    mock_retry.assert_called_once_with(
        cliente_id=CLIENTE_ID,
        provisioning_run_id=RUN_ID,
    )
    assert response.provisioning_state == "provisioning"
    assert response.provisioning_run_id == RUN_ID


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_11_abort_only_when_provisioning():
    with patch.object(
        endpoints_clientes._provisioning_query_service,
        "get_provisioning_status",
        new_callable=AsyncMock,
        return_value=_snapshot(state=ProvisioningState.READY),
    ):
        with pytest.raises(ConflictError) as exc_info:
            await abort_provisioning(CLIENTE_ID, body=None, current_user=_fake_user())
    assert exc_info.value.internal_code == "INVALID_PROVISIONING_STATE"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_11_abort_idempotent_when_already_failed():
    with patch.object(
        endpoints_clientes._provisioning_query_service,
        "get_provisioning_status",
        new_callable=AsyncMock,
        return_value=_snapshot(state=ProvisioningState.FAILED),
    ):
        response = await abort_provisioning(CLIENTE_ID, body=None, current_user=_fake_user())
    assert response.provisioning_state == "failed"
    assert "abortado" in response.message.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_11_abort_invokes_orchestrator():
    with patch.object(
        endpoints_clientes._provisioning_query_service,
        "get_provisioning_status",
        new_callable=AsyncMock,
        return_value=_snapshot(state=ProvisioningState.PROVISIONING),
    ):
        with patch.object(
            endpoints_clientes._provisioning_orchestrator,
            "abort_provisioning_run",
            new_callable=AsyncMock,
        ) as mock_abort:
            response = await abort_provisioning(
                CLIENTE_ID,
                body=ProvisioningAbortRequest(reason="ops"),
                current_user=_fake_user(),
            )

    mock_abort.assert_called_once_with(
        cliente_id=CLIENTE_ID,
        provisioning_run_id=RUN_ID,
        reason="ops",
    )
    assert response.provisioning_state == "failed"
