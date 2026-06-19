"""IAM-SESSIONS-PA-001: listado admin sesiones activas paginado."""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.core.exceptions import CustomException
from app.modules.auth.application.services.admin_sessions_service import (
    ADMIN_SESSIONS_SORT_COLUMNS,
    AdminSessionsService,
)
from app.modules.auth.presentation.schemas_admin_sessions import AdminSessionRead
from app.shared.pagination.params import ErpPaginationParams

CLIENTE_ID = UUID("e4c8e906-0e64-4f4e-a04d-8daee57dc7f8")
TOKEN_ID = uuid4()
USUARIO_ID = uuid4()
NOW = datetime(2026, 6, 18, 12, 0, 0)


def _session_row() -> dict:
    return {
        "token_id": TOKEN_ID,
        "usuario_id": USUARIO_ID,
        "cliente_id": CLIENTE_ID,
        "created_at": NOW,
        "last_used_at": NOW,
        "expires_at": NOW,
        "device_name": "Chrome",
        "device_id": "dev-1",
        "ip_address": "10.0.0.1",
        "user_agent": "Mozilla/5.0",
        "client_type": "web",
        "nombre_usuario": "admin",
        "nombre": "Admin",
        "apellido": "User",
    }


@pytest.mark.asyncio
async def test_legacy_mode_returns_list_without_count():
    mock_query = AsyncMock(return_value=[_session_row()])
    with patch(
        "app.modules.auth.application.services.admin_sessions_service.execute_query",
        mock_query,
    ):
        result = await AdminSessionsService.list_admin_active_sessions(
            CLIENTE_ID,
            pagination=ErpPaginationParams(page=None, limit=50),
        )

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].token_id == TOKEN_ID
    assert mock_query.await_count == 1


@pytest.mark.asyncio
async def test_paginated_mode_returns_envelope():
    mock_query = AsyncMock(side_effect=[[{"count_1": 1}], [_session_row()]])
    with patch(
        "app.modules.auth.application.services.admin_sessions_service.execute_query",
        mock_query,
    ):
        result = await AdminSessionsService.list_admin_active_sessions(
            CLIENTE_ID,
            pagination=ErpPaginationParams(page=1, limit=10),
        )

    assert result.total_sesiones == 1
    assert result.pagina_actual == 1
    assert len(result.sessions) == 1
    assert mock_query.await_count == 2


@pytest.mark.asyncio
async def test_invalid_sort_by_raises_422():
    with pytest.raises(CustomException) as exc:
        await AdminSessionsService.list_admin_active_sessions(
            CLIENTE_ID,
            pagination=ErpPaginationParams(page=None, limit=50),
            sort_by="token_hash",
        )
    assert exc.value.internal_code == "INVALID_SORT_COLUMN"


def test_sort_whitelist_includes_domain_columns():
    assert "nombre_usuario" in ADMIN_SESSIONS_SORT_COLUMNS
    assert "last_used_at" in ADMIN_SESSIONS_SORT_COLUMNS
    assert "token_hash" not in ADMIN_SESSIONS_SORT_COLUMNS


def test_admin_session_read_includes_enriched_fields():
    item = AdminSessionRead.model_validate(_session_row())
    assert item.expires_at == NOW
    assert item.user_agent == "Mozilla/5.0"
    assert item.nombre_usuario == "admin"


def test_openapi_admin_sessions_includes_new_params():
    from fastapi.testclient import TestClient
    from app.main import app

    schema = TestClient(app).get("/openapi.json").json()
    params = {
        p["name"]
        for p in schema["paths"]["/api/v1/auth/sessions/admin/"]["get"]["parameters"]
        if p.get("in") == "query"
    }
    assert "page" in params
    assert "limit" in params
    assert "search" in params
    assert "sort_by" in params
    assert "sort_order" in params
    assert "client_type" in params
    assert "usuario_id" in params
