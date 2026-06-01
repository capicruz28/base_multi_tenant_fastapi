"""Tests PlanModuloResolver (M0)."""
from __future__ import annotations

import pytest

from app.modules.tenant.application.services.owner_sync_constants import TRIAL_MODULES
from app.modules.tenant.application.services.plan_modulo_resolver import (
    resolve_modulos_for_plan,
)


@pytest.mark.unit
def test_resolve_trial_modules():
    assert resolve_modulos_for_plan("trial") == list(TRIAL_MODULES)
    assert resolve_modulos_for_plan(None) == list(TRIAL_MODULES)
    assert "INV" in resolve_modulos_for_plan("trial")


@pytest.mark.unit
def test_resolve_unknown_plan_defaults_trial():
    mods = resolve_modulos_for_plan("plan_inexistente_xyz")
    assert mods == list(TRIAL_MODULES)
