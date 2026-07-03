"""F12-E2B3G — política ENABLE_AUTH_VERBOSE en logs ORG session scope."""
from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import pytest

from app.core.tenant import session_scope as scope


_CLIENTE_ID = uuid4()
_EMPRESA_ID = uuid4()


@pytest.mark.unit
class TestOrgSessionScopeLoggingPolicy:
    def test_session_scope_no_log_when_verbose_off(self):
        with patch.object(scope, "_org_scope_diag_enabled", return_value=False):
            with patch.object(scope.logger, "info") as mock_info:
                scope._log_org_session_scope(
                    endpoint="GET /org/empresa",
                    cliente_id=_CLIENTE_ID,
                    source="request_tenant",
                    is_impersonation=False,
                    payload={"empresa_id": str(_EMPRESA_ID)},
                )
        mock_info.assert_not_called()

    def test_scope_policy_no_log_when_verbose_off(self):
        with patch.object(scope, "_org_scope_diag_enabled", return_value=False):
            with patch.object(scope.logger, "info") as mock_info:
                scope._log_org_scope_policy(
                    endpoint="GET /org/sucursales",
                    policy=scope.OrgScopePolicy.COMPANY,
                    cliente_id=_CLIENTE_ID,
                    empresa_id=_EMPRESA_ID,
                    is_impersonation=False,
                    empresa_selection_pending=False,
                )
        mock_info.assert_not_called()

    def test_erp_session_no_log_when_verbose_off(self):
        with patch.object(scope, "_org_scope_diag_enabled", return_value=False):
            with patch.object(scope.logger, "info") as mock_info:
                scope.log_org_erp_session(
                    endpoint="GET /org/empresa",
                    scope_kind="tenant",
                    payload={"cliente_id": str(_CLIENTE_ID), "empresa_id": str(_EMPRESA_ID)},
                    session_cliente_id=_CLIENTE_ID,
                )
        mock_info.assert_not_called()

    def test_tenant_scope_no_log_when_verbose_off(self):
        with patch.object(scope, "_org_scope_diag_enabled", return_value=False):
            with patch.object(scope.logger, "info") as mock_info:
                scope.log_org_tenant_scope(
                    operation="list",
                    client_id=_CLIENTE_ID,
                    resource="empresa",
                    empresa_id=_EMPRESA_ID,
                )
        mock_info.assert_not_called()

    def test_session_scope_emits_info_when_verbose_on(self):
        with patch.object(scope, "_org_scope_diag_enabled", return_value=True):
            with patch.object(scope.logger, "info") as mock_info:
                scope._log_org_session_scope(
                    endpoint="GET /org/empresa",
                    cliente_id=_CLIENTE_ID,
                    source="request_tenant",
                    is_impersonation=False,
                    payload={"empresa_id": str(_EMPRESA_ID)},
                )
        mock_info.assert_called_once()
        assert mock_info.call_args[0][0].startswith("[ORG-SESSION-SCOPE]")

    def test_tenant_scope_emits_info_when_verbose_on(self):
        with patch.object(scope, "_org_scope_diag_enabled", return_value=True):
            with patch.object(scope.logger, "info") as mock_info:
                scope.log_org_tenant_scope(
                    operation="list",
                    client_id=_CLIENTE_ID,
                    resource="empresa",
                )
        mock_info.assert_called_once()
        assert mock_info.call_args[0][0].startswith("[ORG-TENANT-SCOPE]")
