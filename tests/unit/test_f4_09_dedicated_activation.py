"""PR-F4-09 — tests unitarios DedicatedActivationService."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError
from app.infrastructure.provisioning.dedicated_activation_service import (
    DedicatedActivationService,
)
from app.infrastructure.provisioning.dedicated_activation_types import (
    DedicatedActivationRequest,
)
from app.infrastructure.provisioning.dedicated_storage_metadata_types import (
    DedicatedStorageMetadataResult,
)
from app.modules.tenant.application.provisioning import ProvisioningState
from app.modules.tenant.application.provisioning.provisioning_status_read import (
    DedicatedProvisioningStatusSnapshot,
)

CLIENTE_ID = uuid4()
RUN_ID = uuid4()
CONEXION_ID = uuid4()


def _activation_request() -> DedicatedActivationRequest:
    return DedicatedActivationRequest(
        cliente_id=CLIENTE_ID,
        provisioning_run_id=RUN_ID,
        database_name="erp_acme001",
        servidor="sql.local",
        app_login_name="erpapp_acme001",
        app_login_password="Secret123!",
    )


def _provisioning_status(*, state=ProvisioningState.PROVISIONING):
    return DedicatedProvisioningStatusSnapshot(
        cliente_id=CLIENTE_ID,
        tipo_instalacion="dedicated",
        provisioning_state=state,
        provisioning_run_id=RUN_ID,
        current_step="mark_ready",
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
def activation_mocks() -> dict[str, AsyncMock]:
    return {
        "metadata": AsyncMock(),
        "state": AsyncMock(),
        "query": AsyncMock(),
    }


@pytest.fixture
def activation_service(activation_mocks) -> DedicatedActivationService:
    mocks = activation_mocks
    mocks["metadata"].register_primary_connection.return_value = (
        DedicatedStorageMetadataResult(
            conexion_id=CONEXION_ID,
            created=True,
            idempotent=False,
        )
    )
    mocks["query"].get_provisioning_status.return_value = _provisioning_status()
    return DedicatedActivationService(
        metadata_service=mocks["metadata"],
        state_service=mocks["state"],
        query_service=mocks["query"],
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_09_s8_register_metadata_delegates(activation_service, activation_mocks):
    result = await activation_service.register_metadata(_activation_request())
    activation_mocks["metadata"].register_primary_connection.assert_called_once()
    assert result.idempotency_marker == str(CONEXION_ID)
    assert result.stub is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_09_s9_invalidates_cache_and_smoke_passes(
    activation_service,
    activation_mocks,
):
    metadata = {
        "database_type": "multi",
        "tipo_instalacion": "dedicated",
        "servidor": "sql.local",
        "nombre_bd": "erp_acme001",
        "usuario": "erpapp_acme001",
        "password": "Secret123!",
    }
    with patch(
        "app.infrastructure.provisioning.dedicated_activation_service.invalidate_client_connection_cache"
    ) as mock_invalidate:
        with patch(
            "app.infrastructure.provisioning.dedicated_activation_service.get_connection_metadata_async",
            new_callable=AsyncMock,
            return_value=metadata,
        ):
            result = await activation_service.activate_routing(_activation_request())

    mock_invalidate.assert_called_once_with(CLIENTE_ID)
    assert result.idempotency_marker.startswith("routing_smoke_v1:")
    activation_mocks["state"].transition_run_to_ready.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_09_s9_smoke_fail_closed_on_bad_database_type(activation_service):
    with patch(
        "app.infrastructure.provisioning.dedicated_activation_service.invalidate_client_connection_cache"
    ):
        with patch(
            "app.infrastructure.provisioning.dedicated_activation_service.get_connection_metadata_async",
            new_callable=AsyncMock,
            return_value={
                "database_type": "single",
                "tipo_instalacion": "dedicated",
                "servidor": "sql.local",
                "nombre_bd": "erp_acme001",
                "usuario": "u",
                "password": "p",
            },
        ):
            with pytest.raises(ConflictError) as exc_info:
                await activation_service.activate_routing(_activation_request())
    assert exc_info.value.internal_code == "PROVISIONING_ACTIVATION_FAILED"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_09_s10_returns_marker_without_run_transition(
    activation_service, activation_mocks
):
    result = await activation_service.mark_ready(_activation_request())
    # Opción B: la transición READY es acto terminal del Orchestrator, no del step.
    activation_mocks["state"].transition_run_to_ready.assert_not_called()
    assert result.idempotency_marker == f"ready_run:{RUN_ID}"
    assert result.idempotent is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_09_s10_idempotent_when_already_ready(activation_service, activation_mocks):
    activation_mocks["query"].get_provisioning_status.return_value = _provisioning_status(
        state=ProvisioningState.READY,
    )
    result = await activation_service.mark_ready(_activation_request())
    activation_mocks["state"].transition_run_to_ready.assert_not_called()
    assert result.idempotent is True
