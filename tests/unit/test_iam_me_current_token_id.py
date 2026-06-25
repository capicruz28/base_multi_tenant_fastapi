"""IAM-BE-ME-CURRENT-TOKEN-ID-01: current_token_id en GET /auth/me."""
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.auth.application.services.refresh_token_service import RefreshTokenService
from app.modules.auth.presentation.endpoints import get_me

CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()
TOKEN_ID = uuid4()
REFRESH_JWT = "test-refresh-jwt-value"


def _mock_user():
    user = MagicMock()
    user.usuario_id = USUARIO_ID
    user.cliente_id = CLIENTE_ID
    user.nombre_usuario = "admin"
    user.correo = "admin@test.com"
    user.nombre = "Admin"
    user.apellido = "User"
    user.es_activo = True
    user.roles = []
    user.access_level = 1
    user.is_super_admin = False
    user.user_type = "user"
    return user


def _payload(*, impersonation: bool = False):
    data = {
        "sub": "admin",
        "cliente_id": str(CLIENTE_ID),
        "empresa_id": str(uuid4()),
        "access_level": 1,
        "is_super_admin": False,
        "user_type": "user",
        "es_admin_cliente": False,
    }
    if impersonation:
        data["is_impersonation"] = True
        data["impersonated_by"] = str(uuid4())
    return data


def _request(*, refresh_cookie: str | None = REFRESH_JWT):
    request = MagicMock()
    request.cookies.get.return_value = refresh_cookie
    return request


def _profile_row():
    return [
        {
            "usuario_id": USUARIO_ID,
            "cliente_id": CLIENTE_ID,
            "nombre_usuario": "admin",
            "correo": "admin@test.com",
            "nombre": "Admin",
            "apellido": "User",
            "dni": None,
            "telefono": None,
            "proveedor_autenticacion": "local",
            "es_activo": True,
            "correo_confirmado": True,
            "fecha_creacion": "2025-01-01",
            "fecha_ultimo_acceso": None,
            "fecha_actualizacion": None,
            "rol_id": None,
        }
    ]



@pytest.mark.asyncio
async def test_get_me_populates_current_token_id_web_with_cookie():
    with patch(
        "app.modules.auth.presentation.endpoints.get_client_type",
        return_value="web",
    ), patch(
        "app.modules.auth.presentation.endpoints.AuthService.usuario_tiene_es_admin_cliente",
        AsyncMock(return_value=False),
    ), patch(
        "app.modules.users.application.services.user_service.execute_query",
        AsyncMock(return_value=_profile_row()),
    ), patch(
        "app.modules.auth.presentation.endpoints.UsuarioService.get_user_level_info",
        AsyncMock(
            return_value={
                "access_level": 1,
                "is_super_admin": False,
                "user_type": "user",
            }
        ),
    ), patch(
        "app.core.tenant.context.try_get_tenant_context",
        return_value=None,
    ), patch(
        "app.modules.auth.presentation.endpoints.ActiveSessionsReadService.resolve_current_token_id",
        AsyncMock(return_value=TOKEN_ID),
    ) as mock_resolve, patch(
        "app.modules.auth.presentation.endpoints.ActiveSessionsReadService.resolve_current_session_id",
        AsyncMock(return_value=None),
    ), patch.object(
        RefreshTokenService,
        "validate_refresh_token",
        new=AsyncMock(),
    ) as mock_validate:
        response = await get_me(
            request=_request(),
            payload=_payload(),
            current_user=_mock_user(),
        )
    assert response.current_token_id == TOKEN_ID
    mock_resolve.assert_awaited_once()
    mock_validate.assert_not_awaited()


@pytest.mark.asyncio
async def test_resolve_current_token_id_happy_path():
    token_hash = RefreshTokenService.hash_token(REFRESH_JWT)
    with patch(
        "app.modules.auth.application.services.refresh_token_service.get_refresh_token_by_hash_any_state_core",
        new=AsyncMock(
            return_value={"token_id": TOKEN_ID, "token_hash": token_hash}
        ),
    ) as mock_any_state:
        result = await RefreshTokenService.resolve_current_token_id_from_refresh(
            REFRESH_JWT, CLIENTE_ID
        )

    assert result == TOKEN_ID
    mock_any_state.assert_awaited_once_with(token_hash, CLIENTE_ID)


@pytest.mark.asyncio
async def test_resolve_current_token_id_no_refresh():
    with patch(
        "app.modules.auth.application.services.refresh_token_service.get_refresh_token_by_hash_any_state_core",
        new=AsyncMock(),
    ) as mock_any_state:
        assert await RefreshTokenService.resolve_current_token_id_from_refresh(
            None, CLIENTE_ID
        ) is None
        assert await RefreshTokenService.resolve_current_token_id_from_refresh(
            REFRESH_JWT, None
        ) is None
    mock_any_state.assert_not_awaited()


@pytest.mark.asyncio
async def test_resolve_current_token_id_row_not_found():
    with patch(
        "app.modules.auth.application.services.refresh_token_service.get_refresh_token_by_hash_any_state_core",
        new=AsyncMock(return_value=None),
    ):
        result = await RefreshTokenService.resolve_current_token_id_from_refresh(
            REFRESH_JWT, CLIENTE_ID
        )
    assert result is None


@pytest.mark.asyncio
async def test_resolve_current_token_id_admin_revoked_row_still_returns_id():
    """any_state: fila revocada sigue identificando token_id."""
    with patch(
        "app.modules.auth.application.services.refresh_token_service.get_refresh_token_by_hash_any_state_core",
        new=AsyncMock(
            return_value={
                "token_id": TOKEN_ID,
                "is_revoked": True,
                "revoked_reason": "ADMIN_REVOKE",
            }
        ),
    ):
        result = await RefreshTokenService.resolve_current_token_id_from_refresh(
            REFRESH_JWT, CLIENTE_ID
        )
    assert result == TOKEN_ID


@pytest.mark.asyncio
async def test_resolve_current_token_id_invalid_token_id_fail_soft():
    with patch(
        "app.modules.auth.application.services.refresh_token_service.get_refresh_token_by_hash_any_state_core",
        new=AsyncMock(return_value={"token_id": "not-a-uuid"}),
    ):
        result = await RefreshTokenService.resolve_current_token_id_from_refresh(
            REFRESH_JWT, CLIENTE_ID
        )
    assert result is None


@pytest.mark.asyncio
async def test_resolve_current_token_id_query_exception_fail_soft():
    with patch(
        "app.modules.auth.application.services.refresh_token_service.get_refresh_token_by_hash_any_state_core",
        new=AsyncMock(side_effect=RuntimeError("db down")),
    ):
        result = await RefreshTokenService.resolve_current_token_id_from_refresh(
            REFRESH_JWT, CLIENTE_ID
        )
    assert result is None


@pytest.mark.asyncio
async def test_resolve_does_not_call_validate_refresh_token():
    with patch(
        "app.modules.auth.application.services.refresh_token_service.get_refresh_token_by_hash_any_state_core",
        new=AsyncMock(return_value={"token_id": TOKEN_ID}),
    ), patch.object(
        RefreshTokenService,
        "validate_refresh_token",
        new=AsyncMock(),
    ) as mock_validate:
        await RefreshTokenService.resolve_current_token_id_from_refresh(
            REFRESH_JWT, CLIENTE_ID
        )
    mock_validate.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_me_no_cookie_current_token_id_null():
    with patch(
        "app.modules.auth.presentation.endpoints.get_client_type",
        return_value="web",
    ), patch(
        "app.modules.auth.presentation.endpoints.AuthService.usuario_tiene_es_admin_cliente",
        AsyncMock(return_value=False),
    ), patch(
        "app.modules.users.application.services.user_service.execute_query",
        AsyncMock(return_value=_profile_row()),
    ), patch(
        "app.modules.auth.presentation.endpoints.UsuarioService.get_user_level_info",
        AsyncMock(
            return_value={
                "access_level": 1,
                "is_super_admin": False,
                "user_type": "user",
            }
        ),
    ), patch(
        "app.core.tenant.context.try_get_tenant_context",
        return_value=None,
    ), patch(
        "app.modules.auth.presentation.endpoints.ActiveSessionsReadService.resolve_current_token_id",
        AsyncMock(return_value=None),
    ) as mock_resolve, patch(
        "app.modules.auth.presentation.endpoints.ActiveSessionsReadService.resolve_current_session_id",
        AsyncMock(return_value=None),
    ) as mock_session:
        response = await get_me(
            request=_request(refresh_cookie=None),
            payload=_payload(),
            current_user=_mock_user(),
        )
    assert response.current_token_id is None
    assert response.current_session_id is None
    mock_resolve.assert_awaited_once()
    mock_session.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_me_impersonation_current_token_id_null():
    with patch(
        "app.modules.auth.presentation.endpoints.get_client_type",
        return_value="web",
    ), patch(
        "app.modules.auth.presentation.endpoints.AuthService.usuario_tiene_es_admin_cliente",
        AsyncMock(return_value=False),
    ), patch(
        "app.modules.users.application.services.user_service.execute_query",
        AsyncMock(return_value=_profile_row()),
    ), patch(
        "app.modules.auth.presentation.endpoints.UsuarioService.get_user_level_info",
        AsyncMock(
            return_value={
                "access_level": 1,
                "is_super_admin": False,
                "user_type": "user",
            }
        ),
    ), patch(
        "app.core.tenant.context.try_get_tenant_context",
        return_value=None,
    ), patch(
        "app.modules.auth.presentation.endpoints.ActiveSessionsReadService.resolve_current_token_id",
        AsyncMock(return_value=TOKEN_ID),
    ) as mock_resolve, patch(
        "app.modules.auth.presentation.endpoints.ActiveSessionsReadService.resolve_current_session_id",
        AsyncMock(return_value=None),
    ):
        response = await get_me(
            request=_request(),
            payload=_payload(impersonation=True),
            current_user=_mock_user(),
        )
    assert response.current_token_id is None
    assert response.current_session_id is None
    mock_resolve.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_me_mobile_current_token_id_null():
    with patch(
        "app.modules.auth.presentation.endpoints.get_client_type",
        return_value="mobile",
    ), patch(
        "app.modules.auth.presentation.endpoints.AuthService.usuario_tiene_es_admin_cliente",
        AsyncMock(return_value=False),
    ), patch(
        "app.modules.users.application.services.user_service.execute_query",
        AsyncMock(return_value=_profile_row()),
    ), patch(
        "app.modules.auth.presentation.endpoints.UsuarioService.get_user_level_info",
        AsyncMock(
            return_value={
                "access_level": 1,
                "is_super_admin": False,
                "user_type": "user",
            }
        ),
    ), patch(
        "app.core.tenant.context.try_get_tenant_context",
        return_value=None,
    ), patch(
        "app.modules.auth.presentation.endpoints.ActiveSessionsReadService.resolve_current_token_id",
        AsyncMock(return_value=TOKEN_ID),
    ) as mock_resolve, patch(
        "app.modules.auth.presentation.endpoints.ActiveSessionsReadService.resolve_current_session_id",
        AsyncMock(return_value=None),
    ):
        response = await get_me(
            request=_request(),
            payload=_payload(),
            current_user=_mock_user(),
        )
    assert response.current_token_id is None
    assert response.current_session_id is None
    mock_resolve.assert_not_awaited()
