"""
Tests unitarios: selección/cambio de empresa y dependencias de selection token.
"""
from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.api.deps_auth import (
    reject_selection_token_for_me,
    require_full_session_payload,
    require_selection_token_payload,
)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_require_selection_token_rejects_normal_session():
    payload = {"sub": "user1", "empresa_selection_pending": False, "type": "access"}
    with pytest.raises(HTTPException) as exc:
        await require_selection_token_payload(payload)
    assert exc.value.status_code == 409


@pytest.mark.unit
@pytest.mark.asyncio
async def test_require_selection_token_accepts_selection():
    payload = {"sub": "user1", "empresa_selection_pending": True, "type": "access"}
    result = await require_selection_token_payload(payload)
    assert result["sub"] == "user1"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_require_full_session_rejects_selection_pending():
    payload = {"sub": "user1", "empresa_selection_pending": True}
    with pytest.raises(HTTPException) as exc:
        await require_full_session_payload(payload)
    assert exc.value.status_code == 409


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validar_empresa_no_asignada_400():
    from app.modules.auth.application.services.auth_service import AuthService

    usuario_id = uuid4()
    cliente_id = uuid4()
    empresa_id = uuid4()
    otra = uuid4()

    with patch.object(
        AuthService,
        "get_empresa_activa_para_login",
        new=AsyncMock(
            return_value={
                "empresas_disponibles": [
                    {
                        "empresa_id": otra,
                        "razon_social": "Otra Empresa",
                        "nombre_comercial": None,
                    }
                ],
                "empresa_activa": None,
            }
        ),
    ):
        with pytest.raises(HTTPException) as exc:
            await AuthService.validar_empresa_para_sesion(
                usuario_id, cliente_id, empresa_id
            )
    assert exc.value.status_code == 400


@pytest.mark.unit
@pytest.mark.asyncio
async def test_seleccionar_blacklists_selection_jti():
    from app.modules.auth.application.services.auth_service import AuthService

    usuario_id = uuid4()
    cliente_id = uuid4()
    empresa_id = uuid4()
    payload = {
        "sub": "testuser",
        "cliente_id": str(cliente_id),
        "empresa_selection_pending": True,
        "jti": "selection-jti-123",
        "exp": 9999999999,
        "type": "access",
    }

    mock_context = AsyncMock(
        return_value=type(
            "Ctx",
            (),
            {
                "usuario_id": usuario_id,
                "cliente_id": cliente_id,
                "es_activo": True,
            },
        )()
    )

    session_out = {
        "access_token": "access",
        "refresh_token": "refresh",
        "user_data": {"nombre_usuario": "testuser"},
        "refresh_expire_days": 7,
    }

    with patch(
        "app.modules.auth.application.services.auth_service.get_current_client_id",
        return_value=cliente_id,
    ), patch(
        "app.core.auth.user_context.get_user_auth_context",
        mock_context,
    ), patch(
        "app.core.auth.user_context.validate_tenant_access",
        new=AsyncMock(return_value=True),
    ), patch.object(
        AuthService, "validar_empresa_para_sesion", new=AsyncMock()
    ), patch(
        "app.core.tenant.empresa_preference.persist_usuario_empresa_default_id",
        new=AsyncMock(),
    ), patch.object(
        AuthService,
        "emitir_sesion_completa_con_empresa",
        new=AsyncMock(return_value=session_out),
    ), patch(
        "app.modules.auth.application.services.auth_service.RefreshTokenService.store_refresh_token",
        new=AsyncMock(return_value={"token_id": "tid"}),
    ), patch.object(
        AuthService, "blacklist_access_token_jti", new=AsyncMock()
    ) as mock_bl, patch(
        "app.modules.auth.application.services.auth_service.AuditService.registrar_auth_event",
        new=AsyncMock(),
    ):
        result = await AuthService.seleccionar_empresa_post_login(
            payload=payload,
            empresa_id=empresa_id,
            client_type="web",
            ip_address="127.0.0.1",
            user_agent="pytest",
        )

    assert result["access_token"] == "access"
    mock_bl.assert_awaited_once_with("selection-jti-123", 9999999999)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_reject_selection_token_for_me_returns_409():
    payload = {"sub": "user1", "empresa_selection_pending": True, "type": "access"}
    with pytest.raises(HTTPException) as exc:
        await reject_selection_token_for_me(payload)
    assert exc.value.status_code == 409
    assert "seleccionar" in exc.value.detail.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_admin_sin_rol_empresa_con_org_empresas_requiere_seleccion():
    from app.modules.auth.application.services.auth_service import AuthService

    usuario_id = uuid4()
    cliente_id = uuid4()
    emp1, emp2 = uuid4(), uuid4()

    with patch.object(
        AuthService,
        "_listar_empresas_activas_org",
        new=AsyncMock(
            return_value=[
                {
                    "empresa_id": emp1,
                    "razon_social": "Empresa Uno",
                    "nombre_comercial": "EU",
                },
                {
                    "empresa_id": emp2,
                    "razon_social": "Empresa Dos",
                    "nombre_comercial": None,
                },
            ]
        ),
    ), patch(
        "app.modules.auth.application.services.auth_service.execute_query",
        new=AsyncMock(
            side_effect=[
                [],  # empresas usuario_rol
                [{"admin_sin_empresa_count": 1}],  # admin global
                [{"empresa_default_id": None}],  # usuario sin default
            ]
        ),
    ):
        result = await AuthService.get_empresa_activa_para_login(
            usuario_id, cliente_id
        )

    assert result["requiere_seleccion"] is True
    assert result["empresa_activa"] is None
    assert result["es_admin_sin_empresa"] is True
    ids = {e["empresa_id"] for e in result["empresas_disponibles"]}
    assert ids == {emp1, emp2}
    assert result["empresas_disponibles"][0]["razon_social"] == "Empresa Uno"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_admin_global_una_org_no_requiere_seleccion():
    from app.modules.auth.application.services.auth_service import AuthService

    usuario_id = uuid4()
    cliente_id = uuid4()
    emp1 = uuid4()

    with patch.object(
        AuthService,
        "_listar_empresas_activas_org",
        new=AsyncMock(
            return_value=[
                {
                    "empresa_id": emp1,
                    "razon_social": "Empresa Unica",
                    "nombre_comercial": None,
                },
            ]
        ),
    ), patch(
        "app.modules.auth.application.services.auth_service.execute_query",
        new=AsyncMock(
            side_effect=[
                [],
                [{"admin_sin_empresa_count": 1}],
                [{"empresa_default_id": None}],
            ]
        ),
    ):
        result = await AuthService.get_empresa_activa_para_login(
            usuario_id, cliente_id
        )

    assert result["requiere_seleccion"] is False
    assert result["empresa_activa"] == emp1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_empresa_activa_superadmin_sin_seleccion():
    from app.modules.auth.application.services.auth_service import AuthService

    usuario_id = uuid4()
    cliente_id = uuid4()

    result = await AuthService.get_empresa_activa_para_login(
        usuario_id,
        cliente_id,
        es_superadmin=True,
    )
    assert result["empresas_disponibles"] == []
    assert result["empresa_activa"] is None
    assert result["requiere_seleccion"] is False
    assert result["es_admin_sin_empresa"] is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_user_access_level_platform_superadmin_by_username():
    from app.modules.auth.application.services.auth_service import AuthService
    from app.core.config import settings

    with patch.object(
        AuthService,
        "_detect_platform_superadmin",
        new=AsyncMock(return_value=True),
    ):
        info = await AuthService.get_user_access_level_info(
            uuid4(),
            uuid4(),
            username=settings.SUPERADMIN_USERNAME,
        )

    assert info["user_type"] == "platform_admin"
    assert info["is_super_admin"] is True
    assert info["access_level"] == 5


@pytest.mark.unit
@pytest.mark.asyncio
async def test_usuario_tiene_es_admin_cliente_false_for_platform_superadmin():
    from app.modules.auth.application.services.auth_service import AuthService

    with patch.object(
        AuthService,
        "_detect_platform_superadmin",
        new=AsyncMock(return_value=True),
    ):
        result = await AuthService.usuario_tiene_es_admin_cliente(
            uuid4(), uuid4(), None, username="superadmin"
        )
    assert result is False


@pytest.mark.unit
def test_jwt_superadmin_claims_without_empresa_id():
    from app.core.security.jwt import create_access_token
    from jose import jwt
    from app.core.config import settings

    data = {
        "sub": "superadmin",
        "cliente_id": str(uuid4()),
        "es_superadmin": True,
        "level_info": {
            "access_level": 5,
            "is_super_admin": True,
            "user_type": "platform_admin",
        },
    }
    token, _jti = create_access_token(
        data=data,
        empresa_id=None,
        es_admin_cliente=False,
        access_token_expire_minutes=15,
    )
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload.get("user_type") == "platform_admin"
    assert payload.get("is_super_admin") is True
    assert payload.get("es_superadmin") is True
    assert payload.get("empresa_id") is None
    assert payload.get("es_admin_cliente") is False


@pytest.mark.unit
def test_jwt_access_includes_empresa_id_without_selection_pending():
    from app.core.security.jwt import create_access_token

    empresa_id = uuid4()
    data = {
        "sub": "user",
        "cliente_id": str(uuid4()),
        "level_info": {"access_level": 1, "is_super_admin": False, "user_type": "user"},
    }
    token, _jti = create_access_token(
        data=data,
        empresa_id=empresa_id,
        es_admin_cliente=False,
        access_token_expire_minutes=15,
    )
    from jose import jwt
    from app.core.config import settings

    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload.get("empresa_id") == str(empresa_id)
    assert payload.get("empresa_selection_pending") is not True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_refresh_token_uses_jwt_cliente_id_not_request_context():
    """Platform: token en SYSTEM; contexto request en tenant ACME → debe buscar por JWT."""
    from app.modules.auth.application.services.refresh_token_service import (
        RefreshTokenService,
    )

    system_id = uuid4()
    acme_id = uuid4()
    token = "fake.jwt.token"
    token_hash = RefreshTokenService.hash_token(token)
    db_row = {
        "token_id": uuid4(),
        "usuario_id": uuid4(),
        "cliente_id": system_id,
        "empresa_id": None,
    }

    with patch(
        "app.modules.auth.application.services.refresh_token_service.get_current_client_id",
        return_value=acme_id,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.get_refresh_token_by_hash_core",
        new=AsyncMock(return_value=None),
    ) as mock_by_hash:
        await RefreshTokenService.validate_refresh_token(token, cliente_id=system_id)

    mock_by_hash.assert_awaited_once_with(token_hash, system_id)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_level_info_refresh_preserves_platform_admin():
    from app.modules.auth.application.services.auth_service import AuthService

    refresh_payload = {
        "sub": "admin",
        "user_type": "platform_admin",
        "access_level": 5,
        "is_super_admin": True,
        "es_superadmin": True,
        "cliente_id": str(uuid4()),
    }
    info = await AuthService.resolve_level_info_for_token_refresh(
        refresh_payload=refresh_payload,
        username="admin",
        usuario_id=uuid4(),
        cliente_id=uuid4(),
    )
    assert info["user_type"] == "platform_admin"
    assert info["access_level"] == 5
    assert info["is_super_admin"] is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_level_info_refresh_does_not_downgrade_to_tenant_admin():
    from app.modules.auth.application.services.auth_service import AuthService

    refresh_payload = {
        "user_type": "platform_admin",
        "access_level": 5,
        "is_super_admin": True,
        "es_superadmin": True,
    }
    with patch.object(
        AuthService,
        "get_user_access_level_info",
        new=AsyncMock(
            return_value={
                "access_level": 4,
                "is_super_admin": False,
                "user_type": "tenant_admin",
            }
        ),
    ) as mock_levels:
        info = await AuthService.resolve_level_info_for_token_refresh(
            refresh_payload=refresh_payload,
            username="admin",
            usuario_id=uuid4(),
            cliente_id=uuid4(),
        )
    mock_levels.assert_not_awaited()
    assert info["user_type"] == "platform_admin"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_perform_logout_revokes_refresh_with_jwt_cliente_id():
    from unittest.mock import MagicMock
    from app.modules.auth.application.services.auth_service import AuthService
    from app.modules.auth.application.services.refresh_token_service import (
        RefreshTokenService,
    )

    system_id = uuid4()
    usuario_id = uuid4()
    refresh = "jwt.refresh.token"

    mock_request = MagicMock()
    mock_request.cookies = {"refresh_token": refresh}
    mock_request.headers = {}
    mock_request.client = None

    payload = {
        "sub": "admin",
        "cliente_id": str(system_id),
        "user_type": "platform_admin",
        "access_level": 5,
        "is_super_admin": True,
        "type": "refresh",
    }

    with patch(
        "app.modules.auth.application.services.auth_service.decode_refresh_token",
        return_value=payload,
    ), patch.object(
        RefreshTokenService,
        "validate_refresh_token",
        new=AsyncMock(
            return_value={
                "usuario_id": usuario_id,
                "cliente_id": system_id,
            }
        ),
    ), patch.object(
        RefreshTokenService,
        "revoke_token",
        new=AsyncMock(return_value=True),
    ) as mock_revoke, patch(
        "app.modules.auth.application.services.auth_service.AuditService.registrar_auth_event",
        new=AsyncMock(),
    ):
        outcome = await AuthService.perform_logout(
            request=mock_request, client_type="web"
        )

    assert outcome["refresh_revoked"] is True
    mock_revoke.assert_awaited_once()
    call = mock_revoke.await_args
    assert call.args[0] == system_id
    assert call.args[1] == usuario_id
    assert call.args[2] == refresh


@pytest.mark.unit
def test_token_payload_accepts_platform_admin_refresh_claims():
    from app.modules.auth.presentation.schemas import TokenPayload

    payload = TokenPayload(
        sub="admin",
        type="refresh",
        access_level=5,
        is_super_admin=True,
        user_type="platform_admin",
        es_superadmin=True,
        cliente_id=uuid4(),
    )
    assert payload.user_type == "platform_admin"
    assert payload.es_superadmin is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_user_for_refresh_platform_uses_admin_db():
    from app.core.config import settings
    from app.modules.auth.application.services.auth_service import AuthService

    system_id = uuid4()
    settings.SUPERADMIN_CLIENTE_ID = str(system_id)

    payload = {
        "sub": "superadmin",
        "user_type": "platform_admin",
        "is_super_admin": True,
        "cliente_id": str(system_id),
    }
    user_row = {
        "usuario_id": uuid4(),
        "cliente_id": system_id,
        "nombre_usuario": "superadmin",
        "correo": "a@b.com",
        "nombre": "S",
        "apellido": "A",
        "es_activo": True,
    }

    with patch(
        "app.modules.auth.application.services.auth_service.execute_query",
        new=AsyncMock(return_value=[user_row]),
    ) as mock_eq:
        result = await AuthService._fetch_user_row_for_refresh(
            "superadmin",
            payload=payload,
            token_cliente_id=system_id,
        )

    assert result == user_row
    mock_eq.assert_awaited_once()
    call_kwargs = mock_eq.await_args.kwargs
    assert call_kwargs["connection_type"].name == "DEFAULT"
