"""PR-F4-01 — tests unitarios tipos de dominio provisioning."""
from __future__ import annotations

from uuid import uuid4

import pytest

from app.core.exceptions import ValidationError
from app.modules.tenant.application.provisioning import (
    ALLOWED_PROVISIONING_STATE_TRANSITIONS,
    PROVISIONING_STATE_VALUES,
    PROVISIONING_STEP_CODE_VALUES,
    PROVISIONING_STEP_STATUS_VALUES,
    SAGA_ORDER_BY_CODE,
    SAGA_STEP_ORDER,
    ProvisioningState,
    ProvisioningStepCode,
    ProvisioningStepStatus,
    assert_provisioning_state_transition,
    parse_provisioning_state,
    parse_provisioning_step_code,
    parse_provisioning_step_status,
)
from app.infrastructure.database.queries.tenant.provisioning import (
    tenant_provisioning_step_queries_core as stepq,
)


@pytest.mark.unit
def test_f4_01_provisioning_state_values_match_contract():
    assert PROVISIONING_STATE_VALUES == {"provisioning", "ready", "failed"}


@pytest.mark.unit
def test_f4_01_step_codes_match_contract():
    expected = {
        "registry",
        "storage_allocation",
        "create_database",
        "apply_schema_erp",
        "apply_schema_rbac",
        "apply_catalogs",
        "seed_tenant",
        "register_metadata",
        "activate_routing",
        "mark_ready",
    }
    assert PROVISIONING_STEP_CODE_VALUES == expected


@pytest.mark.unit
def test_f4_01_step_status_values_match_contract():
    assert PROVISIONING_STEP_STATUS_VALUES == {
        "pending",
        "running",
        "completed",
        "failed",
        "skipped",
    }


@pytest.mark.unit
def test_f4_01_saga_step_order_is_s1_to_s10():
    assert len(SAGA_STEP_ORDER) == 10
    assert SAGA_STEP_ORDER[0] == ProvisioningStepCode.REGISTRY
    assert SAGA_STEP_ORDER[-1] == ProvisioningStepCode.MARK_READY
    assert list(SAGA_ORDER_BY_CODE.values()) == list(range(1, 11))


@pytest.mark.unit
def test_f4_01_initial_step_rows_materialize_ten_pending_steps():
    run_id = uuid4()
    cliente_id = uuid4()
    rows = stepq.build_initial_step_rows(
        provisioning_run_id=run_id,
        cliente_id=cliente_id,
    )
    assert len(rows) == 10
    assert {row["step_status"] for row in rows} == {"pending"}
    assert rows[0]["saga_order"] == 1
    assert rows[-1]["saga_order"] == 10
    assert rows[0]["step_code"] == ProvisioningStepCode.REGISTRY.value
    assert rows[-1]["step_code"] == ProvisioningStepCode.MARK_READY.value


@pytest.mark.unit
@pytest.mark.parametrize(
    ("current", "target"),
    [
        (None, ProvisioningState.PROVISIONING),
        (ProvisioningState.PROVISIONING, ProvisioningState.READY),
        (ProvisioningState.PROVISIONING, ProvisioningState.FAILED),
        (ProvisioningState.FAILED, ProvisioningState.PROVISIONING),
    ],
)
def test_f4_01_allowed_provisioning_transitions(
    current: ProvisioningState | None,
    target: ProvisioningState,
):
    assert_provisioning_state_transition(current, target)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("current", "target"),
    [
        (None, ProvisioningState.READY),
        (ProvisioningState.READY, ProvisioningState.PROVISIONING),
        (ProvisioningState.READY, ProvisioningState.FAILED),
        (ProvisioningState.FAILED, ProvisioningState.READY),
    ],
)
def test_f4_01_illegal_provisioning_transitions_raise(
    current: ProvisioningState | None,
    target: ProvisioningState,
):
    with pytest.raises(ValidationError):
        assert_provisioning_state_transition(current, target)


@pytest.mark.unit
def test_f4_01_ready_state_has_no_outgoing_transitions():
    assert ALLOWED_PROVISIONING_STATE_TRANSITIONS[ProvisioningState.READY] == frozenset()


@pytest.mark.unit
def test_f4_01_parse_helpers_reject_unknown_values():
    with pytest.raises(ValueError):
        parse_provisioning_state("active")
    with pytest.raises(ValueError):
        parse_provisioning_step_code("bootstrap")
    with pytest.raises(ValueError):
        parse_provisioning_step_status("done")
