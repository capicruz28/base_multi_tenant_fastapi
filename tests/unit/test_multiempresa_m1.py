"""
Tests unitarios Fase M1 multiempresa (MULTIEMPRESA_OFFICIAL_MODEL.md).
"""
from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.core.exceptions import AuthorizationError
from app.core.tenant.empresa_preference import USER_WITHOUT_COMPANY


def _empresa_row(empresa_id, nombre="Empresa"):
    return {
        "empresa_id": empresa_id,
        "razon_social": nombre,
        "nombre_comercial": None,
    }


def _login_query_side_effect(
    empresas_rol,
    admin_count=0,
    empresa_default_id=None,
):
    """Side effect para execute_query en get_empresa_activa_para_login."""
    calls = {"n": 0}

    async def _side_effect(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return empresas_rol
        if calls["n"] == 2:
            return [{"admin_sin_empresa_count": admin_count}]
        if calls["n"] == 3:
            return [{"empresa_default_id": empresa_default_id}]
        return []

    return _side_effect


@pytest.mark.unit
@pytest.mark.asyncio
async def test_caso_a_una_empresa_sesion_directa():
    from app.modules.auth.application.services.auth_service import AuthService

    usuario_id = uuid4()
    cliente_id = uuid4()
    emp1 = uuid4()

    with patch(
        "app.modules.auth.application.services.auth_service.execute_query",
        new=AsyncMock(
            side_effect=_login_query_side_effect([_empresa_row(emp1, "Unica")])
        ),
    ):
        result = await AuthService.get_empresa_activa_para_login(
            usuario_id, cliente_id
        )

    assert result["requiere_seleccion"] is False
    assert result["empresa_activa"] == emp1
    assert len(result["empresas_disponibles"]) == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_caso_b_multiples_con_default_valido():
    from app.modules.auth.application.services.auth_service import AuthService

    usuario_id = uuid4()
    cliente_id = uuid4()
    emp1, emp2 = uuid4(), uuid4()

    with patch(
        "app.modules.auth.application.services.auth_service.execute_query",
        new=AsyncMock(
            side_effect=_login_query_side_effect(
                [_empresa_row(emp1, "A"), _empresa_row(emp2, "B")],
                empresa_default_id=emp2,
            )
        ),
    ):
        result = await AuthService.get_empresa_activa_para_login(
            usuario_id, cliente_id
        )

    assert result["requiere_seleccion"] is False
    assert result["empresa_activa"] == emp2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_caso_c_multiples_sin_default_requiere_seleccion():
    from app.modules.auth.application.services.auth_service import AuthService

    usuario_id = uuid4()
    cliente_id = uuid4()
    emp1, emp2 = uuid4(), uuid4()

    with patch(
        "app.modules.auth.application.services.auth_service.execute_query",
        new=AsyncMock(
            side_effect=_login_query_side_effect(
                [_empresa_row(emp1), _empresa_row(emp2)],
                empresa_default_id=None,
            )
        ),
    ):
        result = await AuthService.get_empresa_activa_para_login(
            usuario_id, cliente_id
        )

    assert result["requiere_seleccion"] is True
    assert result["empresa_activa"] is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_caso_d_operativo_sin_empresa_rechazado():
    from app.modules.auth.application.services.auth_service import AuthService

    ctx = {
        "empresas_disponibles": [],
        "es_admin_sin_empresa": False,
    }
    with pytest.raises(AuthorizationError) as exc:
        AuthService.assert_operational_login_allowed(ctx)
    assert exc.value.internal_code == USER_WITHOUT_COMPANY
    assert exc.value.status_code == 403


@pytest.mark.unit
@pytest.mark.asyncio
async def test_caso_d_admin_onboarding_permitido():
    from app.modules.auth.application.services.auth_service import AuthService

    ctx = {
        "empresas_disponibles": [],
        "es_admin_sin_empresa": True,
    }
    AuthService.assert_operational_login_allowed(ctx)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_platform_admin_sin_rechazo():
    from app.modules.auth.application.services.auth_service import AuthService

    ctx = {"empresas_disponibles": [], "es_admin_sin_empresa": False}
    AuthService.assert_operational_login_allowed(
        ctx, user_type="platform_admin"
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_m1_6_default_invalida_se_limpia():
    from app.modules.auth.application.services.auth_service import AuthService

    usuario_id = uuid4()
    cliente_id = uuid4()
    emp1, emp2 = uuid4(), uuid4()
    invalid_default = uuid4()

    with patch(
        "app.modules.auth.application.services.auth_service.execute_query",
        new=AsyncMock(
            side_effect=_login_query_side_effect(
                [_empresa_row(emp1), _empresa_row(emp2)],
                empresa_default_id=invalid_default,
            )
        ),
    ), patch(
        "app.core.tenant.empresa_preference.execute_update",
        new=AsyncMock(),
    ) as mock_clear:
        result = await AuthService.get_empresa_activa_para_login(
            usuario_id, cliente_id
        )

    mock_clear.assert_awaited_once()
    assert result["requiere_seleccion"] is True
    assert result["empresa_activa"] is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_admin_global_una_org_sesion_directa_m1_4():
    from app.modules.auth.application.services.auth_service import AuthService

    usuario_id = uuid4()
    cliente_id = uuid4()
    emp1 = uuid4()

    with patch.object(
        AuthService,
        "_listar_empresas_activas_org",
        new=AsyncMock(return_value=[_empresa_row(emp1, "Org Unica")]),
    ), patch(
        "app.modules.auth.application.services.auth_service.execute_query",
        new=AsyncMock(
            side_effect=_login_query_side_effect([], admin_count=1)
        ),
    ):
        result = await AuthService.get_empresa_activa_para_login(
            usuario_id, cliente_id
        )

    assert result["requiere_seleccion"] is False
    assert result["empresa_activa"] == emp1
    assert result["es_admin_sin_empresa"] is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_seleccionar_persiste_empresa_default_m1_1():
    from app.modules.auth.application.services.auth_service import AuthService

    usuario_id = uuid4()
    cliente_id = uuid4()
    empresa_id = uuid4()
    payload = {
        "sub": "testuser",
        "cliente_id": str(cliente_id),
        "empresa_selection_pending": True,
        "jti": "jti-1",
        "exp": 9999999999,
        "type": "access",
    }

    session_out = {
        "access_token": "access",
        "refresh_token": "refresh",
        "user_data": {},
        "refresh_expire_days": 7,
    }

    mock_context = AsyncMock(
        return_value=type(
            "Ctx",
            (),
            {"usuario_id": usuario_id, "cliente_id": cliente_id, "es_activo": True},
        )()
    )

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
    ) as mock_persist, patch.object(
        AuthService,
        "emitir_sesion_completa_con_empresa",
        new=AsyncMock(return_value=session_out),
    ), patch(
        "app.modules.auth.application.services.auth_service.RefreshTokenService.store_refresh_token",
        new=AsyncMock(return_value={"token_id": "tid"}),
    ), patch.object(
        AuthService, "blacklist_access_token_jti", new=AsyncMock()
    ), patch(
        "app.modules.auth.application.services.auth_service.AuditService.registrar_auth_event",
        new=AsyncMock(),
    ):
        await AuthService.seleccionar_empresa_post_login(
            payload=payload,
            empresa_id=empresa_id,
            client_type="web",
            ip_address="127.0.0.1",
            user_agent="pytest",
        )

    mock_persist.assert_awaited_once_with(usuario_id, cliente_id, empresa_id)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cambiar_persiste_empresa_default_m1_2():
    from app.modules.auth.application.services.auth_service import AuthService

    usuario_id = uuid4()
    cliente_id = uuid4()
    empresa_anterior = uuid4()
    empresa_nueva = uuid4()
    payload = {
        "sub": "testuser",
        "cliente_id": str(cliente_id),
        "empresa_id": str(empresa_anterior),
        "empresa_selection_pending": False,
        "type": "access",
    }

    session_out = {
        "access_token": "access",
        "refresh_token": "refresh",
        "user_data": {},
        "refresh_expire_days": 7,
    }

    mock_context = AsyncMock(
        return_value=type(
            "Ctx",
            (),
            {"usuario_id": usuario_id, "cliente_id": cliente_id, "es_activo": True},
        )()
    )

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
    ) as mock_persist, patch.object(
        AuthService,
        "emitir_sesion_completa_con_empresa",
        new=AsyncMock(return_value=session_out),
    ), patch(
        "app.modules.auth.application.services.auth_service.RefreshTokenService.store_refresh_token",
        new=AsyncMock(return_value={"token_id": "tid"}),
    ), patch(
        "app.modules.auth.application.services.auth_service.AuditService.registrar_auth_event",
        new=AsyncMock(),
    ):
        await AuthService.cambiar_empresa_sesion(
            payload=payload,
            empresa_id=empresa_nueva,
            client_type="web",
            ip_address="127.0.0.1",
            user_agent="pytest",
            old_refresh_token=None,
        )

    mock_persist.assert_awaited_once_with(usuario_id, cliente_id, empresa_nueva)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_asignar_rol_set_default_mono_empresa_m1_3():
    from app.modules.users.application.services.user_service import UsuarioService

    cliente_id = uuid4()
    usuario_id = uuid4()
    rol_id = uuid4()
    empresa_id = uuid4()

    usuario = {"usuario_id": usuario_id, "cliente_id": cliente_id}
    rol = {"rol_id": rol_id, "es_activo": True}
    assignment = {
        "usuario_rol_id": uuid4(),
        "usuario_id": usuario_id,
        "rol_id": rol_id,
        "cliente_id": cliente_id,
        "empresa_id": empresa_id,
        "es_activo": True,
    }

    with patch.object(
        UsuarioService,
        "obtener_usuario_por_id",
        new=AsyncMock(return_value=usuario),
    ), patch(
        "app.modules.users.application.services.user_service.RolService.obtener_rol_por_id",
        new=AsyncMock(return_value=rol),
    ), patch(
        "app.modules.users.application.services.user_service.execute_query",
        new=AsyncMock(
            side_effect=[
                [],  # no existing assignment
                [{"empresa_default_id": None}],  # default null check
            ]
        ),
    ), patch(
        "app.modules.users.application.services.user_service.execute_insert",
        new=AsyncMock(return_value=assignment),
    ), patch(
        "app.core.authorization.permission_resolver.get_permission_resolver",
    ) as mock_resolver, patch.object(
        UsuarioService,
        "_maybe_set_empresa_default_after_role_assign",
        new=AsyncMock(),
    ) as mock_maybe:
        mock_resolver.return_value.invalidate_for_user = lambda *a, **k: None
        await UsuarioService.asignar_rol_a_usuario(
            cliente_id, usuario_id, rol_id, target_empresa_id=empresa_id
        )

    mock_maybe.assert_awaited_once_with(cliente_id, usuario_id)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_maybe_set_default_llama_persist_si_una_elegible():
    from app.modules.users.application.services.user_service import UsuarioService

    cliente_id = uuid4()
    usuario_id = uuid4()
    empresa_id = uuid4()

    with patch(
        "app.modules.users.application.services.user_service.execute_query",
        new=AsyncMock(return_value=[{"empresa_default_id": None}]),
    ), patch(
        "app.modules.auth.application.services.auth_service.AuthService.get_empresa_activa_para_login",
        new=AsyncMock(
            return_value={
                "empresas_disponibles": [_empresa_row(empresa_id)],
            }
        ),
    ), patch(
        "app.core.tenant.empresa_preference.persist_usuario_empresa_default_id",
        new=AsyncMock(),
    ) as mock_persist:
        await UsuarioService._maybe_set_empresa_default_after_role_assign(
            cliente_id, usuario_id
        )

    mock_persist.assert_awaited_once_with(usuario_id, cliente_id, empresa_id)
