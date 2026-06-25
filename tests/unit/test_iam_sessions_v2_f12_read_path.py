"""F12 — read path V2: C09, C20, C21 y DTOs aditivos."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.modules.auth.application.services.active_sessions_read_service import (
    ADMIN_SESSIONS_SORT_COLUMNS,
    ActiveSessionsReadService,
)
from app.modules.auth.application.session.active_session_read_columns import (
    ADMIN_SESSIONS_SORT_COLUMNS_V2,
    admin_sessions_sort_columns,
    normalize_admin_sort_by,
)
from app.modules.auth.application.session.session_read_mapper import (
    map_row_to_admin_session,
    map_row_to_user_session,
)
from app.modules.auth.presentation.endpoints import revoke_own_session_by_id
from app.modules.auth.presentation.schemas_admin_sessions import AdminSessionRead
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.shared.pagination.params import ErpPaginationParams

CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()
SESSION_ID = uuid4()
TOKEN_ID = uuid4()
FAMILY_ID = uuid4()
NOW = datetime(2026, 6, 22, 12, 0, 0)

_READ = "app.modules.auth.application.services.active_sessions_read_service"
_FEATURE = f"{_READ}.is_session_v2_enabled"
_FEATURE_EP = "app.modules.auth.application.session.session_v2_feature.is_session_v2_enabled"


def _v2_session_row(**overrides) -> dict:
    base = {
        "session_id": SESSION_ID,
        "usuario_id": USUARIO_ID,
        "cliente_id": CLIENTE_ID,
        "empresa_id": uuid4(),
        "login_method": "password",
        "platform": "web",
        "device_name": "Chrome",
        "device_id": "dev-1",
        "user_agent": "Mozilla/5.0 Chrome/120.0.0.0",
        "login_ip": "10.0.0.1",
        "last_seen_ip": "10.0.0.2",
        "created_at": NOW,
        "last_refresh_at": NOW,
        "expires_at": NOW + timedelta(days=7),
        "token_id": TOKEN_ID,
        "family_id": FAMILY_ID,
        "client_type": "web",
        "ip_address": "10.0.0.2",
    }
    base.update(overrides)
    return base


def _v1_row(**overrides) -> dict:
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
        "user_agent": "Mozilla/5.0 Chrome/120.0.0.0",
        "client_type": "web",
    }
    base.update(overrides)
    return base


@pytest.mark.unit
def test_f12_mapper_v2_includes_session_id_login_ip_platform():
    dto = map_row_to_user_session(
        _v2_session_row(),
        current_session_id=SESSION_ID,
        v2=True,
    )
    assert dto.session_id == SESSION_ID
    assert dto.login_ip == "10.0.0.1"
    assert dto.platform == "web"
    assert dto.family_id == FAMILY_ID
    assert dto.is_current is True


@pytest.mark.unit
def test_f12_mapper_is_current_by_session_id():
    dto = map_row_to_user_session(
        _v2_session_row(),
        current_session_id=uuid4(),
        current_token_id=TOKEN_ID,
        v2=True,
    )
    assert dto.is_current is False

    dto_match = map_row_to_user_session(
        _v2_session_row(),
        current_session_id=SESSION_ID,
        current_token_id=uuid4(),
        v2=True,
    )
    assert dto_match.is_current is True


@pytest.mark.unit
def test_f12_mapper_v1_unchanged_without_v2_flag():
    dto = map_row_to_user_session(_v1_row(), current_token_id=TOKEN_ID)
    assert dto.session_id is None
    assert dto.login_ip is None
    assert dto.is_current is True


@pytest.mark.unit
def test_f12_c21_sort_whitelist_v2_superset():
    assert ADMIN_SESSIONS_SORT_COLUMNS.issubset(ADMIN_SESSIONS_SORT_COLUMNS_V2)
    assert "session_id" in admin_sessions_sort_columns(v2_enabled=True)
    assert "login_ip" in admin_sessions_sort_columns(v2_enabled=True)
    assert normalize_admin_sort_by("last_used_at", v2_enabled=True) == "last_refresh_at"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f12_list_user_sessions_v2_composes_c15_c16():
    session_row = {
        "session_id": SESSION_ID,
        "usuario_id": USUARIO_ID,
        "cliente_id": CLIENTE_ID,
        "platform": "mobile",
        "login_ip": "1.2.3.4",
        "last_seen_ip": "5.6.7.8",
        "created_at": NOW,
        "last_refresh_at": NOW,
        "expires_at": NOW + timedelta(days=1),
        "user_agent": "OkHttp",
        "device_name": None,
    }
    family_row = {
        "family_id": FAMILY_ID,
        "current_token_id": TOKEN_ID,
        "is_compromised": False,
    }
    with (
        patch(_FEATURE, return_value=True),
        patch(
            f"{_READ}.list_active_sessions_oldest_first_core",
            AsyncMock(return_value=[session_row]),
        ),
        patch(
            f"{_READ}.get_family_by_session_id_core",
            AsyncMock(return_value=family_row),
        ),
        patch(f"{_READ}.get_active_sessions_by_user_core", AsyncMock()),
    ):
        items = await ActiveSessionsReadService.list_user_sessions(
            CLIENTE_ID,
            USUARIO_ID,
            current_session_id=SESSION_ID,
        )
    assert len(items) == 1
    assert items[0].session_id == SESSION_ID
    assert items[0].login_ip == "1.2.3.4"
    assert items[0].platform == "mobile"
    assert items[0].is_current is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f12_list_user_sessions_v1_when_flag_off():
    with (
        patch(_FEATURE, return_value=False),
        patch(
            f"{_READ}.get_active_sessions_by_user_core",
            AsyncMock(return_value=[_v1_row()]),
        ),
        patch(f"{_READ}.list_active_sessions_oldest_first_core", AsyncMock()),
    ):
        items = await ActiveSessionsReadService.list_user_sessions(
            CLIENTE_ID,
            USUARIO_ID,
            current_token_id=TOKEN_ID,
        )
    assert len(items) == 1
    assert items[0].token_id == TOKEN_ID
    assert items[0].session_id is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f12_resolve_user_revoke_by_session_id_v2():
    with (
        patch(_FEATURE, return_value=True),
        patch(
            "app.modules.auth.application.services.session_query_service.SessionQueryService.get_session",
            AsyncMock(return_value={"usuario_id": USUARIO_ID, "session_id": SESSION_ID}),
        ),
        patch(
            "app.modules.auth.application.services.session_query_service.SessionQueryService.get_family_for_session",
            AsyncMock(return_value={"current_token_id": TOKEN_ID}),
        ),
    ):
        target = await ActiveSessionsReadService.resolve_user_revoke_target(
            SESSION_ID,
            CLIENTE_ID,
            USUARIO_ID,
        )
    assert target.session_id == SESSION_ID
    assert target.token_id == TOKEN_ID
    assert target.is_active is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f12_self_revoke_v2_uses_revocation_service():
    user = UsuarioReadWithRoles(
        usuario_id=USUARIO_ID,
        cliente_id=CLIENTE_ID,
        nombre_usuario="testuser",
        correo="u@t.com",
        nombre="U",
        apellido="T",
        es_activo=True,
        fecha_creacion=NOW.isoformat(),
        roles=[],
        permisos=[],
    )
    target = MagicMock(
        session_id=SESSION_ID,
        token_id=TOKEN_ID,
        row=_v2_session_row(),
        is_active=True,
    )
    request = MagicMock()
    request.client.host = "127.0.0.1"
    request.headers.get.return_value = "pytest"

    with (
        patch(_FEATURE_EP, return_value=True),
        patch(
            "app.modules.auth.presentation.endpoints.ActiveSessionsReadService.resolve_user_revoke_target",
            AsyncMock(return_value=target),
        ),
        patch(
            "app.modules.auth.application.services.session_revocation_service.SessionRevocationService.revoke_session",
            AsyncMock(),
        ) as mock_revoke,
        patch(
            "app.modules.auth.presentation.endpoints.RefreshTokenService.revoke_refresh_token_by_id",
            AsyncMock(),
        ) as mock_v1,
        patch(
            "app.modules.auth.presentation.endpoints.AuditService.registrar_auth_event",
            AsyncMock(),
        ),
    ):
        result = await revoke_own_session_by_id(request, SESSION_ID, user)

    mock_revoke.assert_awaited_once()
    mock_v1.assert_not_awaited()
    assert result["session_id"] == str(SESSION_ID)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f12_self_revoke_v1_by_token_id():
    user = UsuarioReadWithRoles(
        usuario_id=USUARIO_ID,
        cliente_id=CLIENTE_ID,
        nombre_usuario="testuser",
        correo="u@t.com",
        nombre="U",
        apellido="T",
        es_activo=True,
        fecha_creacion=NOW.isoformat(),
        roles=[],
        permisos=[],
    )
    from app.modules.auth.application.services.active_sessions_read_service import (
        SessionRevokeTarget,
    )

    target = SessionRevokeTarget(
        session_id=None,
        token_id=TOKEN_ID,
        usuario_id=USUARIO_ID,
        is_active=True,
        row=_v1_row(),
    )
    request = MagicMock()
    request.client.host = "127.0.0.1"
    request.headers.get.return_value = "pytest"

    with (
        patch(_FEATURE_EP, return_value=False),
        patch(
            "app.modules.auth.presentation.endpoints.ActiveSessionsReadService.resolve_user_revoke_target",
            AsyncMock(return_value=target),
        ),
        patch(
            "app.modules.auth.presentation.endpoints.RefreshTokenService.blacklist_access_for_token_id",
            AsyncMock(),
        ),
        patch(
            "app.modules.auth.presentation.endpoints.RefreshTokenService.revoke_refresh_token_by_id",
            AsyncMock(return_value=True),
        ) as mock_v1,
        patch(
            "app.modules.auth.application.services.session_revocation_service.SessionRevocationService.revoke_session",
            AsyncMock(),
        ) as mock_v2,
        patch(
            "app.modules.auth.presentation.endpoints.AuditService.registrar_auth_event",
            AsyncMock(),
        ),
    ):
        await revoke_own_session_by_id(request, TOKEN_ID, user)

    mock_v1.assert_awaited_once()
    mock_v2.assert_not_awaited()


@pytest.mark.unit
def test_f12_openapi_user_session_read_has_additive_fields():
    from fastapi.testclient import TestClient
    from app.main import app

    schema = TestClient(app).get("/openapi.json").json()
    components = schema["components"]["schemas"]
    props = components["UserSessionRead"]["properties"]
    assert "session_id" in props
    assert "login_ip" in props
    assert "platform" in props
    me_props = components["MeResponse"]["properties"]
    assert "current_session_id" in me_props


@pytest.mark.unit
def test_f12_admin_mapper_v2_fields():
    row = _v2_session_row(
        nombre_usuario="admin",
        nombre="A",
        apellido="B",
        empresa_nombre="ACME",
    )
    dto = map_row_to_admin_session(row, v2=True)
    assert isinstance(dto, AdminSessionRead)
    assert dto.session_id == SESSION_ID
    assert dto.nombre_usuario == "admin"
