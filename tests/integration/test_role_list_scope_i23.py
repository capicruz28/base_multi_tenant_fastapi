"""
I2.3 integración: endpoints admin + coherencia scope.
"""
from __future__ import annotations

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.tenant.company_scope import RoleListScope
from app.modules.users.presentation.endpoints import read_usuario_roles, revoke_rol_from_usuario
from app.modules.rbac.presentation.schemas import RolRead

CLIENT_ID = uuid4()
USER_ID = uuid4()
ROL_ID = uuid4()
EMPRESA_A = uuid4()


def _payload():
    return {"cliente_id": str(CLIENT_ID), "empresa_id": str(EMPRESA_A), "user_type": "tenant_admin"}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_read_usuario_roles_passes_list_scope():
    mock_user = MagicMock()
    mock_user.cliente_id = CLIENT_ID
    mock_user.user_type = "tenant_admin"
    mock_user.is_super_admin = False

    captured_scope = None

    async def fake_roles(*, list_scope=None, **kwargs):
        nonlocal captured_scope
        captured_scope = list_scope
        return [
            {
                "rol_id": ROL_ID,
                "cliente_id": CLIENT_ID,
                "codigo_rol": None,
                "nombre": "Operador",
                "descripcion": None,
                "es_activo": True,
                "fecha_creacion": "2025-01-01T00:00:00",
                "asignacion_empresa_id": EMPRESA_A,
            }
        ]

    with patch(
        "app.modules.users.presentation.endpoints.resolve_role_list_scope",
        new=AsyncMock(return_value=RoleListScope(tenant_wide=False, empresa_id=EMPRESA_A)),
    ), patch(
        "app.modules.users.presentation.endpoints.UsuarioService.obtener_roles_de_usuario",
        new=AsyncMock(side_effect=fake_roles),
    ):
        result = await read_usuario_roles(
            usuario_id=USER_ID,
            current_user=mock_user,
            payload=_payload(),
        )

    assert captured_scope is not None
    assert captured_scope.empresa_id == EMPRESA_A
    assert isinstance(result[0], RolRead)
    assert result[0].asignacion_empresa_id == EMPRESA_A


@pytest.mark.integration
@pytest.mark.asyncio
async def test_revoke_endpoint_passes_list_scope():
    mock_user = MagicMock()
    mock_user.cliente_id = CLIENT_ID
    captured: Dict[str, Any] = {}

    async def fake_revoke(**kwargs):
        captured.update(kwargs)
        return {
            "usuario_rol_id": uuid4(),
            "usuario_id": USER_ID,
            "rol_id": ROL_ID,
            "cliente_id": CLIENT_ID,
            "empresa_id": EMPRESA_A,
            "fecha_asignacion": "2025-01-01T00:00:00",
            "es_activo": False,
        }

    with patch(
        "app.modules.users.presentation.endpoints.resolve_role_list_scope",
        new=AsyncMock(return_value=RoleListScope(tenant_wide=False, empresa_id=EMPRESA_A)),
    ), patch(
        "app.modules.users.presentation.endpoints.UsuarioService.revocar_rol_de_usuario",
        new=AsyncMock(side_effect=fake_revoke),
    ):
        await revoke_rol_from_usuario(
            usuario_id=USER_ID,
            rol_id=ROL_ID,
            current_user=mock_user,
            payload=_payload(),
        )

    assert captured["list_scope"].empresa_id == EMPRESA_A


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_me_tenant_admin_with_empresa_returns_profile():
    from app.modules.auth.presentation.endpoints import get_me
    from app.modules.users.application.services.user_service import UsuarioService

    user_id = uuid4()
    mock_user = MagicMock()
    mock_user.usuario_id = user_id
    mock_user.cliente_id = CLIENT_ID
    mock_user.nombre_usuario = "tenant_admin"
    mock_user.correo = "admin@test.com"
    mock_user.nombre = "Admin"
    mock_user.apellido = "Tenant"
    mock_user.es_activo = True
    mock_user.roles = []
    mock_user.access_level = 3
    mock_user.is_super_admin = False
    mock_user.user_type = "tenant_admin"

    payload = {
        "sub": "tenant_admin",
        "cliente_id": str(CLIENT_ID),
        "empresa_id": str(EMPRESA_A),
        "access_level": 3,
        "is_super_admin": False,
        "user_type": "tenant_admin",
        "es_admin_cliente": True,
    }

    captured: Dict[str, Any] = {}

    async def fake_query(query, params=None):
        captured["params"] = params
        return [
            {
                "usuario_id": user_id,
                "cliente_id": CLIENT_ID,
                "nombre_usuario": "tenant_admin",
                "correo": "admin@test.com",
                "nombre": "Admin",
                "apellido": "Tenant",
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

    with patch(
        "app.modules.auth.presentation.endpoints.AuthService.usuario_tiene_es_admin_cliente",
        new=AsyncMock(return_value=True),
    ), patch(
        "app.modules.users.application.services.user_service.execute_query",
        new=AsyncMock(side_effect=fake_query),
    ), patch.object(
        UsuarioService,
        "get_user_level_info",
        new=AsyncMock(
            return_value={
                "access_level": 3,
                "is_super_admin": False,
                "user_type": "tenant_admin",
            }
        ),
    ), patch(
        "app.core.tenant.context.try_get_tenant_context",
        return_value=None,
    ), patch(
        "app.modules.auth.presentation.endpoints.get_client_type",
        return_value="web",
    ):
        request = MagicMock()
        request.cookies.get.return_value = None
        response = await get_me(
            request=request,
            _payload_ok=payload,
            current_user=mock_user,
        )

    assert response is not None
    assert response.nombre_usuario == "tenant_admin"
    assert captured["params"] == (str(EMPRESA_A), user_id, CLIENT_ID)
