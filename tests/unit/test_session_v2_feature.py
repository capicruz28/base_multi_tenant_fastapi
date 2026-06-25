"""Tests mínimos — feature flag IAM Session Management V2 (F0)."""
from __future__ import annotations

from unittest.mock import patch
from uuid import UUID, uuid4

import pytest

from app.modules.auth.application.session.session_v2_feature import is_session_v2_enabled

_FEATURE_MODULE = "app.modules.auth.application.session.session_v2_feature.settings"

TENANT_A = UUID("11111111-1111-4111-8111-111111111111")
TENANT_B = UUID("22222222-2222-4222-8222-222222222222")


@pytest.mark.unit
def test_session_v2_default_global_false():
    with patch(_FEATURE_MODULE) as mock_settings:
        mock_settings.IAM_SESSION_MANAGEMENT_V2_ENABLED = False
        mock_settings.IAM_SESSION_V2_TENANT_ALLOWLIST = ""
        assert is_session_v2_enabled(TENANT_A) is False


@pytest.mark.unit
def test_session_v2_global_true_empty_allowlist_enables_all_tenants():
    with patch(_FEATURE_MODULE) as mock_settings:
        mock_settings.IAM_SESSION_MANAGEMENT_V2_ENABLED = True
        mock_settings.IAM_SESSION_V2_TENANT_ALLOWLIST = ""
        assert is_session_v2_enabled(TENANT_A) is True
        assert is_session_v2_enabled(TENANT_B) is True


@pytest.mark.unit
def test_session_v2_allowlist_filters_tenants():
    with patch(_FEATURE_MODULE) as mock_settings:
        mock_settings.IAM_SESSION_MANAGEMENT_V2_ENABLED = True
        mock_settings.IAM_SESSION_V2_TENANT_ALLOWLIST = f"{TENANT_A},{TENANT_B}"
        assert is_session_v2_enabled(TENANT_A) is True
        assert is_session_v2_enabled(TENANT_B) is True
        assert is_session_v2_enabled(uuid4()) is False


@pytest.mark.unit
def test_session_v2_none_cliente_id_returns_false_even_when_global_true():
    with patch(_FEATURE_MODULE) as mock_settings:
        mock_settings.IAM_SESSION_MANAGEMENT_V2_ENABLED = True
        mock_settings.IAM_SESSION_V2_TENANT_ALLOWLIST = ""
        assert is_session_v2_enabled(None) is False


@pytest.mark.unit
def test_session_v2_allowlist_ignores_invalid_uuids(caplog):
    other = uuid4()
    with patch(_FEATURE_MODULE) as mock_settings:
        mock_settings.IAM_SESSION_MANAGEMENT_V2_ENABLED = True
        mock_settings.IAM_SESSION_V2_TENANT_ALLOWLIST = f"{TENANT_A},not-a-uuid,{other}"
        assert is_session_v2_enabled(TENANT_A) is True
        assert is_session_v2_enabled(other) is True
        assert is_session_v2_enabled(uuid4()) is False
    assert any("UUID inválido" in record.message for record in caplog.records)
