"""IAM-BE-ME-CURRENT-TOKEN-ID-01: integración GET /auth/me + current_token_id."""
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.auth.application.services.refresh_token_service import RefreshTokenService
from app.modules.auth.presentation.endpoints import get_me
from app.modules.auth.presentation.schemas import MeResponse

CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()
TOKEN_ID = uuid4()
REFRESH_JWT = "integration-refresh-jwt"


def _mock_user():
    user = MagicMock()
    user.usuario_id = USUARIO_ID
    user.cliente_id = CLIENTE_ID
    user.nombre_usuario = "tenant_user"
    user.correo = "user@test.com"
    user.nombre = "Tenant"
    user.apellido = "User"
    user.es_activo = True
    user.roles = []
    user.access_level = 2
    user.is_super_admin = False
    user.user_type = "user"
    return user


def _payload():
    return {
        "sub": "tenant_user",
        "cliente_id": str(CLIENTE_ID),
        "empresa_id": str(uuid4()),
        "access_level": 2,
        "is_super_admin": False,
        "user_type": "user",
        "es_admin_cliente": False,
    }


def _profile_query_result():
    return [
        {
            "usuario_id": USUARIO_ID,
            "cliente_id": CLIENTE_ID,
            "nombre_usuario": "tenant_user",
            "correo": "user@test.com",
            "nombre": "Tenant",
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


def _web_request(refresh_cookie: str | None = REFRESH_JWT):
    request = MagicMock()
    request.cookies.get.return_value = refresh_cookie
    return request


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_me_integration_resolves_token_id_via_any_state_core():
    token_hash = RefreshTokenService.hash_token(REFRESH_JWT)

    with patch(
        "app.modules.auth.presentation.endpoints.get_client_type",
        return_value="web",
    ), patch(
        "app.modules.auth.presentation.endpoints.AuthService.usuario_tiene_es_admin_cliente",
        AsyncMock(return_value=False),
    ), patch(
        "app.modules.users.application.services.user_service.execute_query",
        AsyncMock(return_value=_profile_query_result()),
    ), patch(
        "app.modules.auth.presentation.endpoints.UsuarioService.get_user_level_info",
        AsyncMock(
            return_value={
                "access_level": 2,
                "is_super_admin": False,
                "user_type": "user",
            }
        ),
    ), patch(
        "app.core.tenant.context.try_get_tenant_context",
        return_value=None,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.get_refresh_token_by_hash_any_state_core",
        new=AsyncMock(
            return_value={
                "token_id": TOKEN_ID,
                "token_hash": token_hash,
                "is_revoked": False,
            }
        ),
    ) as mock_any_state, patch.object(
        RefreshTokenService,
        "validate_refresh_token",
        new=AsyncMock(),
    ) as mock_validate:
        response = await get_me(
            request=_web_request(),
            _payload_ok=_payload(),
            current_user=_mock_user(),
        )

    assert isinstance(response, MeResponse)
    assert response.current_token_id == TOKEN_ID
    mock_any_state.assert_awaited_once_with(token_hash, CLIENTE_ID)
    mock_validate.assert_not_awaited()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_me_integration_revoked_session_still_exposes_token_id():
    token_hash = RefreshTokenService.hash_token(REFRESH_JWT)

    with patch(
        "app.modules.auth.presentation.endpoints.get_client_type",
        return_value="web",
    ), patch(
        "app.modules.auth.presentation.endpoints.AuthService.usuario_tiene_es_admin_cliente",
        AsyncMock(return_value=False),
    ), patch(
        "app.modules.users.application.services.user_service.execute_query",
        AsyncMock(return_value=_profile_query_result()),
    ), patch(
        "app.modules.auth.presentation.endpoints.UsuarioService.get_user_level_info",
        AsyncMock(
            return_value={
                "access_level": 2,
                "is_super_admin": False,
                "user_type": "user",
            }
        ),
    ), patch(
        "app.core.tenant.context.try_get_tenant_context",
        return_value=None,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.get_refresh_token_by_hash_any_state_core",
        new=AsyncMock(
            return_value={
                "token_id": TOKEN_ID,
                "token_hash": token_hash,
                "is_revoked": True,
                "revoked_reason": "ADMIN_REVOKE",
            }
        ),
    ):
        response = await get_me(
            request=_web_request(),
            _payload_ok=_payload(),
            current_user=_mock_user(),
        )

    assert response.current_token_id == TOKEN_ID


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_me_integration_fail_soft_no_row():
    with patch(
        "app.modules.auth.presentation.endpoints.get_client_type",
        return_value="web",
    ), patch(
        "app.modules.auth.presentation.endpoints.AuthService.usuario_tiene_es_admin_cliente",
        AsyncMock(return_value=False),
    ), patch(
        "app.modules.users.application.services.user_service.execute_query",
        AsyncMock(return_value=_profile_query_result()),
    ), patch(
        "app.modules.auth.presentation.endpoints.UsuarioService.get_user_level_info",
        AsyncMock(
            return_value={
                "access_level": 2,
                "is_super_admin": False,
                "user_type": "user",
            }
        ),
    ), patch(
        "app.core.tenant.context.try_get_tenant_context",
        return_value=None,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.get_refresh_token_by_hash_any_state_core",
        new=AsyncMock(return_value=None),
    ):
        response = await get_me(
            request=_web_request(),
            _payload_ok=_payload(),
            current_user=_mock_user(),
        )

    assert response.current_token_id is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_me_integration_openapi_field_on_schema():
    schema = MeResponse.model_json_schema()
    props = schema.get("properties", {})
    assert "current_token_id" in props
    assert props["current_token_id"].get("type") in ("string", "null", None)
