"""PR-F4-11 — schemas públicos provisioning."""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pytest

from app.modules.tenant.application.provisioning import ProvisioningState
from app.modules.tenant.application.provisioning.provisioning_status_read import (
    DedicatedProvisioningStatusSnapshot,
    ProvisioningStepStatusRead,
)
from app.modules.tenant.presentation.schemas_provisioning import (
    build_legacy_ready_status_read,
    map_provisioning_status_to_read,
    sanitize_provisioning_error_message,
)

CLIENTE_ID = uuid4()
RUN_ID = uuid4()


@pytest.mark.unit
def test_f4_11_sanitize_strips_sensitive_error_message():
    assert sanitize_provisioning_error_message("password=Secret123!") == (
        "Error de provisioning. Consulte soporte con el código de error."
    )
    assert sanitize_provisioning_error_message("DDL timeout en step S4") == (
        "DDL timeout en step S4"
    )


@pytest.mark.unit
def test_f4_11_map_status_read_hides_sensitive_fields():
    snapshot = DedicatedProvisioningStatusSnapshot(
        cliente_id=CLIENTE_ID,
        tipo_instalacion="dedicated",
        provisioning_state=ProvisioningState.FAILED,
        provisioning_run_id=RUN_ID,
        current_step="create_database",
        steps=[
            ProvisioningStepStatusRead(
                code="create_database",
                status="failed",
                started_at=datetime.utcnow(),
                completed_at=None,
            ),
        ],
        started_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        ready_at=None,
        failed_at=datetime.utcnow(),
        last_error_code="PROVISIONING_CREATE_DATABASE_FAILED",
        last_error_message="Login failed for user sa password=xxx",
        retry_allowed=True,
        abort_allowed=False,
    )
    read = map_provisioning_status_to_read(snapshot)
    assert read.provisioning_state == "failed"
    assert read.retry_allowed is True
    assert "password" not in (read.last_error_message or "").lower()


@pytest.mark.unit
def test_f4_11_legacy_ready_synthetic_response():
    read = build_legacy_ready_status_read(CLIENTE_ID)
    assert read.provisioning_state == "ready"
    assert read.retry_allowed is False
    assert read.abort_allowed is False
