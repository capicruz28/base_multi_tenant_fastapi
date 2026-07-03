"""F12-E2B3B — tests de política de logging QueryAuditor."""
from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.security.query_auditor import QueryAuditor
from app.infrastructure.database.tables import UsuarioTable


@pytest.mark.unit
class TestQueryAuditorLoggingPolicy:
    def test_missing_filter_silent_when_not_verbose_row_scoped(self):
        tenant_id = uuid4()
        query = select(UsuarioTable).where(UsuarioTable.c.es_activo == True)

        with patch("app.core.security.query_auditor.settings") as mock_settings:
            mock_settings.ENABLE_QUERY_AUDITOR_VERBOSE = False
            mock_settings.ENVIRONMENT = "development"
            mock_settings.ENABLE_QUERY_TENANT_VALIDATION = True
            with patch(
                "app.core.security.query_auditor._is_engine_scoped_identity",
                return_value=False,
            ):
                with patch(
                    "app.core.security.query_auditor.logger"
                ) as mock_logger:
                    result = QueryAuditor.validate_tenant_filter(
                        query=query,
                        table_name="usuario",
                        client_id=tenant_id,
                    )

        assert result is True
        mock_logger.warning.assert_not_called()

    def test_missing_filter_warns_when_verbose_row_scoped(self):
        tenant_id = uuid4()
        query = select(UsuarioTable).where(UsuarioTable.c.es_activo == True)

        with patch("app.core.security.query_auditor.settings") as mock_settings:
            mock_settings.ENABLE_QUERY_AUDITOR_VERBOSE = True
            mock_settings.ENVIRONMENT = "development"
            mock_settings.ENABLE_QUERY_TENANT_VALIDATION = True
            with patch(
                "app.core.security.query_auditor._is_engine_scoped_identity",
                return_value=False,
            ):
                with patch(
                    "app.core.security.query_auditor.logger"
                ) as mock_logger:
                    QueryAuditor.validate_tenant_filter(
                        query=query,
                        table_name="usuario",
                        client_id=tenant_id,
                    )

        assert mock_logger.warning.call_count >= 1
        assert "sin filtro explícito" in mock_logger.warning.call_args[0][0]

    def test_engine_scoped_missing_filter_debug_only_when_verbose(self):
        tenant_id = uuid4()
        query = select(UsuarioTable).where(UsuarioTable.c.es_activo == True)

        with patch("app.core.security.query_auditor.settings") as mock_settings:
            mock_settings.ENABLE_QUERY_AUDITOR_VERBOSE = True
            mock_settings.ENVIRONMENT = "development"
            mock_settings.ENABLE_QUERY_TENANT_VALIDATION = True
            with patch(
                "app.core.security.query_auditor._is_engine_scoped_identity",
                return_value=True,
            ):
                with patch(
                    "app.core.security.query_auditor.logger"
                ) as mock_logger:
                    QueryAuditor.validate_tenant_filter(
                        query=query,
                        table_name="usuario",
                        client_id=tenant_id,
                    )

        mock_logger.warning.assert_not_called()
        assert mock_logger.debug.call_count >= 1
        assert "ENGINE_SCOPED" in mock_logger.debug.call_args[0][0]

    def test_engine_scoped_missing_filter_silent_when_not_verbose(self):
        tenant_id = uuid4()
        query = select(UsuarioTable).where(UsuarioTable.c.es_activo == True)

        with patch("app.core.security.query_auditor.settings") as mock_settings:
            mock_settings.ENABLE_QUERY_AUDITOR_VERBOSE = False
            mock_settings.ENVIRONMENT = "development"
            mock_settings.ENABLE_QUERY_TENANT_VALIDATION = True
            with patch(
                "app.core.security.query_auditor._is_engine_scoped_identity",
                return_value=True,
            ):
                with patch(
                    "app.core.security.query_auditor.logger"
                ) as mock_logger:
                    QueryAuditor.validate_tenant_filter(
                        query=query,
                        table_name="usuario",
                        client_id=tenant_id,
                    )

        mock_logger.warning.assert_not_called()
        mock_logger.debug.assert_not_called()

    def test_production_block_unchanged_without_verbose(self):
        tenant_id = uuid4()
        query = select(UsuarioTable).where(UsuarioTable.c.es_activo == True)

        with patch("app.core.security.query_auditor.settings") as mock_settings:
            mock_settings.ENABLE_QUERY_AUDITOR_VERBOSE = False
            mock_settings.ENVIRONMENT = "production"
            mock_settings.ENABLE_QUERY_TENANT_VALIDATION = True
            mock_settings.ALLOW_TENANT_FILTER_BYPASS = False
            with patch(
                "app.core.security.query_auditor._is_engine_scoped_identity",
                return_value=False,
            ):
                from app.core.exceptions import SecurityError

                with pytest.raises(SecurityError):
                    QueryAuditor.validate_tenant_filter(
                        query=query,
                        table_name="usuario",
                        client_id=tenant_id,
                    )

    def test_bypass_warning_always_emitted(self):
        query = select(UsuarioTable).where(UsuarioTable.c.es_activo == True)

        with patch("app.core.security.query_auditor.settings") as mock_settings:
            mock_settings.ALLOW_TENANT_FILTER_BYPASS = True
            mock_settings.ENABLE_QUERY_AUDITOR_VERBOSE = False
            with patch("app.core.security.query_auditor.logger") as mock_logger:
                result = QueryAuditor.validate_tenant_filter(
                    query=query,
                    table_name="usuario",
                    client_id=uuid4(),
                    skip_validation=True,
                )

        assert result is True
        mock_logger.warning.assert_called_once()
        assert "ALLOW_TENANT_FILTER_BYPASS" in mock_logger.warning.call_args[0][0]
