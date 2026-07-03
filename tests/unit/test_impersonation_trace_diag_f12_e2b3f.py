"""F12-E2B3F — política ENABLE_IMPERSONATE_DIAG en impersonation_trace_diag."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.auth import impersonation_trace_diag as trace_diag


_SAMPLE_PAYLOAD = {
    "is_impersonation": False,
    "impersonated_by": None,
    "sub": "admin",
    "cliente_id": "557928aa-05a8-468b-b746-c8c84e2ef384",
    "empresa_id": "895d1616-3e3e-416e-b4a0-d148f588feda",
}


@pytest.mark.unit
class TestImpersonationTraceDiagFlagPolicy:
    def test_request_no_log_when_flag_off(self):
        with patch.object(trace_diag, "_impersonate_trace_diag_enabled", return_value=False):
            with patch.object(trace_diag.logger, "info") as mock_info:
                trace_diag.log_impersonation_trace_request(
                    endpoint="POST /auth/refresh/",
                    payload=_SAMPLE_PAYLOAD,
                    jwt_kind="refresh",
                )
        mock_info.assert_not_called()

    def test_response_no_log_when_flag_off(self):
        with patch.object(trace_diag, "_impersonate_trace_diag_enabled", return_value=False):
            with patch.object(trace_diag.logger, "info") as mock_info:
                trace_diag.log_impersonation_trace_response(
                    endpoint="POST /auth/empresa/cambiar/",
                    http_status=400,
                    request_payload=_SAMPLE_PAYLOAD,
                    emission_reason="rejected:test",
                )
        mock_info.assert_not_called()

    def test_request_emits_info_when_flag_on(self):
        with patch.object(trace_diag, "_impersonate_trace_diag_enabled", return_value=True):
            with patch.object(trace_diag.logger, "info") as mock_info:
                trace_diag.log_impersonation_trace_request(
                    endpoint="POST /auth/refresh/",
                    payload=_SAMPLE_PAYLOAD,
                    jwt_kind="refresh",
                )
        mock_info.assert_called_once()
        assert mock_info.call_args[0][1] == trace_diag.TRACE_PREFIX

    def test_response_emits_info_when_flag_on(self):
        with patch.object(trace_diag, "_impersonate_trace_diag_enabled", return_value=True):
            with patch.object(trace_diag.logger, "info") as mock_info:
                trace_diag.log_impersonation_trace_response(
                    endpoint="POST /auth/empresa/cambiar/",
                    http_status=400,
                    request_payload=_SAMPLE_PAYLOAD,
                    emission_reason="rejected:test",
                )
        mock_info.assert_called_once()
        assert mock_info.call_args[0][1] == trace_diag.TRACE_PREFIX
