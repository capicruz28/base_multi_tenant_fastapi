"""F12-E2B1 — tests de infraestructura de logging."""
from __future__ import annotations

import logging
import os
from unittest.mock import patch

import pytest

from app.core.logging_config import (
    get_uvicorn_log_level,
    normalize_log_level,
    resolve_log_level_numeric,
    setup_logging,
)


class TestNormalizeLogLevel:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("debug", "DEBUG"),
            ("INFO", "INFO"),
            ("warning", "WARNING"),
            ("error", "ERROR"),
            ("critical", "CRITICAL"),
            ("invalid", "INFO"),
            ("", "INFO"),
            (None, "INFO"),
        ],
    )
    def test_normalize(self, raw, expected):
        assert normalize_log_level(raw) == expected


class TestSetupLogging:
    def test_setup_logging_applies_level(self):
        applied = setup_logging("WARNING", force=True)
        assert applied == "WARNING"
        assert logging.getLogger().level == logging.WARNING

    def test_setup_logging_reads_env_when_no_arg(self):
        with patch.dict(os.environ, {"LOG_LEVEL": "ERROR"}, clear=False):
            applied = setup_logging(force=True)
        assert applied == "ERROR"
        assert logging.getLogger().level == logging.ERROR


class TestUvicornLogLevel:
    def test_get_uvicorn_log_level_lowercase(self):
        assert get_uvicorn_log_level("WARNING") == "warning"

    def test_settings_uvicorn_aligned(self):
        from app.core.config import Settings

        s = Settings(
            LOG_LEVEL="DEBUG",
            ENVIRONMENT="development",
            SECRET_KEY="x" * 32,
            REFRESH_SECRET_KEY="y" * 32,
        )
        assert s.UVICORN_LOG_LEVEL == "debug"
        assert s.NORMALIZED_LOG_LEVEL == "DEBUG"


class TestDiagnosticTraceFlags:
    def test_defaults_development_false(self):
        from app.core.config import Settings

        s = Settings(
            ENVIRONMENT="development",
            SECRET_KEY="x" * 32,
            REFRESH_SECRET_KEY="y" * 32,
        )
        assert s.ENABLE_REDIS_TRACE is False
        assert s.ENABLE_RBAC_TRACE is False
        assert s.ENABLE_QUERY_AUDITOR_VERBOSE is False
        assert s.ENABLE_HTTP_TRACE is False
        assert s.ENABLE_MIDDLEWARE_TRACE is False
        assert s.ENABLE_IMPERSONATE_DIAG is False
        assert s.ENABLE_AUTH_VERBOSE is False

    def test_defaults_production_false(self):
        from app.core.config import Settings

        s = Settings(
            ENVIRONMENT="production",
            SECRET_KEY="x" * 32,
            REFRESH_SECRET_KEY="y" * 32,
        )
        assert s.ENABLE_REDIS_TRACE is False
        assert s.ENABLE_RBAC_TRACE is False
        assert s.ENABLE_QUERY_AUDITOR_VERBOSE is False
        assert s.ENABLE_HTTP_TRACE is False
        assert s.ENABLE_MIDDLEWARE_TRACE is False
        assert s.ENABLE_IMPERSONATE_DIAG is False
        assert s.ENABLE_AUTH_VERBOSE is False

    def test_explicit_raw_override_on_instance(self):
        from app.core.config import Settings

        s = Settings(
            ENVIRONMENT="development",
            SECRET_KEY="x" * 32,
            REFRESH_SECRET_KEY="y" * 32,
        )
        s._enable_redis_trace_raw = "false"
        assert s.ENABLE_REDIS_TRACE is False
        s._enable_redis_trace_raw = "true"
        assert s.ENABLE_REDIS_TRACE is True


class TestResolveLogLevelNumeric:
    def test_numeric_matches_stdlib(self):
        assert resolve_log_level_numeric("INFO") == logging.INFO
        assert resolve_log_level_numeric("DEBUG") == logging.DEBUG
