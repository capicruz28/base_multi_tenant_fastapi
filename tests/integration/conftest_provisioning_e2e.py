"""
Dedicated Provisioning E2E fixtures — PR-F4-12.

pytest_plugins = ("tests.integration.conftest_provisioning_e2e",)
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from tests.integration.helpers.provisioning_e2e_harness import (
    E2E_CLIENTE_ID,
    E2E_RUN_ID,
    ProvisioningE2EStack,
    build_provisioning_e2e_stack,
)


@pytest.fixture
def e2e_cliente_id():
    return E2E_CLIENTE_ID


@pytest.fixture
def e2e_run_id():
    return E2E_RUN_ID


@pytest.fixture
def provisioning_e2e_stack() -> ProvisioningE2EStack:
    return build_provisioning_e2e_stack()


@pytest.fixture
def dedicated_enabled_sync_dispatcher():
    """Dispatcher síncrono + DEDICATED_ENABLED para E2E determinista."""
    with patch(
        "app.modules.tenant.application.services.dedicated_provisioning_orchestrator.settings"
    ) as orch_settings:
        orch_settings.DEDICATED_ENABLED = True
        with patch(
            "app.infrastructure.provisioning.dedicated_provisioning_compensation_service.settings"
        ) as comp_settings:
            comp_settings.DEDICATED_ENABLED = True
            with patch(
                "app.modules.tenant.application.services.provisioning_job_dispatcher.settings"
            ) as disp_settings:
                disp_settings.PROVISIONING_DISPATCHER_ENABLED = True
                disp_settings.PROVISIONING_DISPATCHER_SYNC = True
                yield
