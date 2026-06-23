"""IAM-SESSIONS-V1 Enterprise — mapper, servicio y contratos."""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import Request

from app.core.exceptions import CustomException
from app.modules.auth.application.services.active_sessions_read_service import (
    ADMIN_SESSIONS_SORT_COLUMNS,
    ActiveSessionsReadService,
)
from app.modules.auth.application.session.session_read_mapper import (
    map_row_to_admin_session,
    map_row_to_user_session,
)
from app.modules.auth.presentation.schemas_admin_sessions import AdminSessionRead
from app.modules.auth.presentation.schemas_sessions import UserSessionRead
from app.shared.pagination.params import ErpPaginationParams

CLIENTE_ID = UUID("e4c8e906-0e64-4f4e-a04d-8daee57dc7f8")
TOKEN_ID = uuid4()
OTHER_TOKEN_ID = uuid4()
USUARIO_ID = uuid4()
NOW = datetime(2026, 6, 18, 12, 0, 0)


def _session_row(**overrides) -> dict:
    base = {
        "token_id": TOKEN_ID,
        "usuario_id": USUARIO_ID,
        "cliente_id": CLIENTE_ID,
        "empresa_id": uuid4(),
        "created_at": NOW,
        "last_used_at": NOW,
        "expires_at": NOW + timedelta(days=7),
        "device_name": "Chrome",
        "device_id": "dev-1",
        "ip_address": "10.0.0.1",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        "client_type": "web",
        "empresa_nombre": "ACME SA",
        "nombre_usuario": "admin",
        "nombre": "Admin",
        "apellido": "User",
    }
    base.update(overrides)
    return base


def test_mapper_chrome_windows_device_label():
    dto = map_row_to_user_session(_session_row())
    assert dto.device.browser == "Chrome"
    assert dto.device.os == "Windows"
    assert dto.device.platform == "desktop"
    assert "Chrome" in dto.device.device_label


def test_mapper_is_current_when_token_matches():
    dto = map_row_to_user_session(
        _session_row(), current_token_id=TOKEN_ID
    )
    assert dto.is_current is True


def test_mapper_is_current_false_for_other_token():
    dto = map_row_to_user_session(
        _session_row(), current_token_id=OTHER_TOKEN_ID
    )
    assert dto.is_current is False


def test_mapper_expiring_soon_status():
    dto = map_row_to_user_session(
        _session_row(expires_at=NOW + timedelta(hours=2)),
        now=NOW,
    )
    assert dto.status == "expiring_soon"


def test_mapper_legacy_alias_fields():
    dto = map_row_to_user_session(_session_row(), now=NOW)
    assert dto.created_at == dto.issued_at
    assert dto.last_used_at == dto.last_refresh_at
    assert dto.expires_at is not None
    assert dto.empresa_id is not None
    assert dto.ip_address == "10.0.0.1"
    assert dto.ip_address == dto.device.ip_address


def test_admin_mapper_includes_user_fields():
    dto = map_row_to_admin_session(_session_row())
    assert dto.nombre_usuario == "admin"
    assert dto.user_agent is not None
    assert dto.empresa_nombre == "ACME SA"


@pytest.mark.asyncio
async def test_list_user_sessions_enriched():
    with patch(
        "app.modules.auth.application.services.active_sessions_read_service.get_active_sessions_by_user_core",
        AsyncMock(return_value=[_session_row()]),
    ):
        items = await ActiveSessionsReadService.list_user_sessions(
            CLIENTE_ID, USUARIO_ID, current_token_id=TOKEN_ID
        )
    assert len(items) == 1
    assert isinstance(items[0], UserSessionRead)
    assert items[0].device.device_label


@pytest.mark.asyncio
async def test_admin_legacy_mode_returns_list():
    mock_query = AsyncMock(return_value=[_session_row()])
    with patch(
        "app.modules.auth.application.services.active_sessions_read_service.execute_query",
        mock_query,
    ):
        result = await ActiveSessionsReadService.list_admin_sessions(
            CLIENTE_ID,
            pagination=ErpPaginationParams(page=None, limit=50),
        )
    assert isinstance(result, list)
    assert isinstance(result[0], AdminSessionRead)


@pytest.mark.asyncio
async def test_admin_paginated_dual_envelope():
    mock_query = AsyncMock(side_effect=[[{"count_1": 1}], [_session_row()]])
    with patch(
        "app.modules.auth.application.services.active_sessions_read_service.execute_query",
        mock_query,
    ):
        result = await ActiveSessionsReadService.list_admin_sessions(
            CLIENTE_ID,
            pagination=ErpPaginationParams(page=1, limit=10),
        )
    assert result.total == 1
    assert result.total_sesiones == 1
    assert len(result.items) == 1
    assert len(result.sessions) == 1
    assert result.items[0].token_id == result.sessions[0].token_id


@pytest.mark.asyncio
async def test_invalid_sort_by_raises_422():
    with pytest.raises(CustomException) as exc:
        await ActiveSessionsReadService.list_admin_sessions(
            CLIENTE_ID,
            pagination=ErpPaginationParams(page=None, limit=50),
            sort_by="token_hash",
        )
    assert exc.value.internal_code == "INVALID_SORT_COLUMN"


def test_sort_whitelist_includes_domain_columns():
    assert "nombre_usuario" in ADMIN_SESSIONS_SORT_COLUMNS
    assert "token_hash" not in ADMIN_SESSIONS_SORT_COLUMNS


@pytest.mark.asyncio
async def test_resolve_current_token_id_delegates_read_only():
    request = MagicMock(spec=Request)
    request.cookies = {"refresh_token": "jwt"}
    with patch(
        "app.modules.auth.application.services.active_sessions_read_service.RefreshTokenService.resolve_current_token_id_from_refresh",
        AsyncMock(return_value=TOKEN_ID),
    ) as mock_resolve:
        result = await ActiveSessionsReadService.resolve_current_token_id(
            request, "web", CLIENTE_ID
        )
    assert result == TOKEN_ID
    mock_resolve.assert_awaited_once()


def test_openapi_user_sessions_typed_schema():
    from fastapi.testclient import TestClient
    from app.main import app

    schema = TestClient(app).get("/openapi.json").json()
    ref = schema["paths"]["/api/v1/auth/sessions/"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]
    assert ref.get("type") == "array"
    item_ref = ref["items"].get("$ref", "")
    assert "UserSessionRead" in item_ref


def test_openapi_self_revoke_path_exists():
    from fastapi.testclient import TestClient
    from app.main import app

    schema = TestClient(app).get("/openapi.json").json()
    assert "/api/v1/auth/sessions/{token_id}/revoke/" in schema["paths"]
