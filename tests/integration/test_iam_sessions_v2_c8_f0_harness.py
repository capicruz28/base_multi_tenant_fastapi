"""Cluster 8 Fase 0 — validación harness QA (sin integration/E2E de negocio)."""
from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.modules.auth.application.session.session_v2_feature import is_session_v2_enabled
from tests.integration.conftest_iam_sessions_v2 import (
    IAM_V2_FIXTURE_TENANT_A,
    IAM_V2_FIXTURE_TENANT_B,
    iam_v2_flag_all_tenants_on,
    iam_v2_flag_allowlist_on,
    iam_v2_flag_off,
    skip_if_no_db,
    verify_feature_flag_env,
    verify_sqlserver_env,
)
from tests.integration.helpers.iam_v2_teardown import teardown_iam_v2_sessions

CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()


@pytest.mark.unit
def test_f0_skip_if_no_db_when_env_skip():
    with patch.dict(os.environ, {"SKIP_DB_INTEGRATION_TESTS": "1"}, clear=False):
        with pytest.raises(pytest.skip.Exception):
            skip_if_no_db()


@pytest.mark.unit
def test_f0_verify_sqlserver_env_reports_missing_credentials(monkeypatch):
    monkeypatch.delenv("SKIP_DB_INTEGRATION_TESTS", raising=False)
    with patch("app.core.config.settings") as mock_settings:
        mock_settings.DB_SERVER = ""
        mock_settings.DB_DATABASE = ""
        mock_settings.DB_USER = ""
        mock_settings.DB_PASSWORD = ""
        errors = verify_sqlserver_env()
    assert any("DB_SERVER" in err for err in errors)


@pytest.mark.unit
def test_f0_verify_feature_flag_env_rejects_invalid_allowlist_uuid(monkeypatch):
    monkeypatch.setenv("IAM_SESSION_V2_TENANT_ALLOWLIST", "not-a-uuid")
    errors = verify_feature_flag_env()
    assert any("IAM_SESSION_V2_TENANT_ALLOWLIST" in err for err in errors)


@pytest.mark.unit
def test_f0_flag_all_tenants_on_enables_v2_for_any_tenant():
    with iam_v2_flag_all_tenants_on():
        assert is_session_v2_enabled(IAM_V2_FIXTURE_TENANT_A) is True
        assert is_session_v2_enabled(IAM_V2_FIXTURE_TENANT_B) is True


@pytest.mark.unit
def test_f0_flag_allowlist_on_filters_other_tenants():
    with iam_v2_flag_allowlist_on(IAM_V2_FIXTURE_TENANT_A):
        assert is_session_v2_enabled(IAM_V2_FIXTURE_TENANT_A) is True
        assert is_session_v2_enabled(IAM_V2_FIXTURE_TENANT_B) is False


@pytest.mark.unit
def test_f0_flag_off_disables_v2():
    with iam_v2_flag_off():
        assert is_session_v2_enabled(IAM_V2_FIXTURE_TENANT_A) is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f0_teardown_executes_delete_in_fk_order():
    with patch(
        "app.infrastructure.database.queries_async.execute_query",
        new_callable=AsyncMock,
    ) as mock_query:
        mock_query.side_effect = [
            [{"rows_affected": 3}],
            [{"rows_affected": 1}],
            [{"rows_affected": 1}],
        ]
        result = await teardown_iam_v2_sessions(
            cliente_id=CLIENTE_ID,
            usuario_ids=[USUARIO_ID],
        )

    assert result == {
        "refresh_tokens": 3,
        "token_family": 1,
        "user_session": 1,
    }
    assert mock_query.await_count == 3
    table_names = [
        call.args[0].table.name for call in mock_query.await_args_list
    ]
    assert table_names == ["refresh_tokens", "token_family", "user_session"]


@pytest.mark.unit
def test_f0_pytest_markers_registered(pytestconfig):
    """Markers Cluster 8 declarados en pytest.ini."""
    lines = pytestconfig.getini("markers")
    marker_names = {line.split(":")[0].strip() for line in lines}
    assert "iam_v2_integration" in marker_names
    assert "requires_sqlserver" in marker_names
    assert "requires_redis" in marker_names
    assert "slow" in marker_names
