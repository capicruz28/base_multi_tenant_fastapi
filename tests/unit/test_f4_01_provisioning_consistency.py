"""PR-F4-01 — validaciones de consistencia perfil cliente."""
from __future__ import annotations

import pytest

from app.core.exceptions import ValidationError
from app.modules.tenant.application.provisioning import (
    SHARED_INSTALLATION_TYPE,
    assert_cliente_provisioning_profile,
)


@pytest.mark.unit
def test_f4_01_shared_cliente_must_not_have_provisioning_state():
    with pytest.raises(ValidationError) as exc:
        assert_cliente_provisioning_profile(
            tipo_instalacion=SHARED_INSTALLATION_TYPE,
            provisioning_state="provisioning",
        )
    assert exc.value.internal_code == "SHARED_PROVISIONING_STATE_FORBIDDEN"


@pytest.mark.unit
def test_f4_01_dedicated_cliente_allows_null_provisioning_state():
    assert_cliente_provisioning_profile(
        tipo_instalacion="dedicated",
        provisioning_state=None,
    )


@pytest.mark.unit
@pytest.mark.parametrize("state", ["provisioning", "ready", "failed"])
def test_f4_01_dedicated_cliente_accepts_official_states(state: str):
    assert_cliente_provisioning_profile(
        tipo_instalacion="dedicated",
        provisioning_state=state,
    )


@pytest.mark.unit
def test_f4_01_invalid_provisioning_state_rejected():
    with pytest.raises(ValidationError) as exc:
        assert_cliente_provisioning_profile(
            tipo_instalacion="dedicated",
            provisioning_state="activo",
        )
    assert exc.value.internal_code == "INVALID_CLIENTE_PROVISIONING_STATE"
