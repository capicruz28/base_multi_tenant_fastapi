"""
I2.3: lecturas admin, /me y revoke alineados con empresa de sesión.
"""
from __future__ import annotations

from typing import Any, Dict
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import AuthorizationError, ConflictError, NotFoundError
from app.core.tenant.company_scope import (
    RoleListScope,
    assert_assignment_visible_in_scope,
    resolve_role_list_scope,
)
from app.modules.users.application.services.user_service import UsuarioService

CLIENT_ID = uuid4()
USER_ID = uuid4()
ROL_ID = uuid4()
EMPRESA_A = uuid4()
EMPRESA_B = uuid4()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_role_list_scope_tenant_requires_empresa():
    with patch(
        "app.core.tenant.company_scope.resolve_empresa_id_for_rbac",
        return_value=EMPRESA_A,
    ):
        scope = await resolve_role_list_scope(payload={"empresa_id": str(EMPRESA_A)})
    assert scope.tenant_wide is False
    assert scope.empresa_id == EMPRESA_A


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_role_list_scope_platform_tenant_wide():
    scope = await resolve_role_list_scope(
        payload={"user_type": "platform_admin"},
        user_type="platform_admin",
        is_super_admin=True,
    )
    assert scope.tenant_wide is True


@pytest.mark.unit
def test_assert_revoke_global_from_tenant_session():
    scope = RoleListScope(tenant_wide=False, empresa_id=EMPRESA_A)
    with pytest.raises(ConflictError) as exc:
        assert_assignment_visible_in_scope(None, scope)
    assert exc.value.internal_code == "ROLE_REVOKE_GLOBAL"


@pytest.mark.unit
def test_assert_revoke_other_empresa_is_404():
    scope = RoleListScope(tenant_wide=False, empresa_id=EMPRESA_A)
    with pytest.raises(NotFoundError) as exc:
        assert_assignment_visible_in_scope(EMPRESA_B, scope)
    assert exc.value.internal_code == "ASSIGNMENT_NOT_FOUND"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_obtener_roles_sql_filters_by_empresa():
    captured: Dict[str, Any] = {}

    async def fake_query(query, params=None):
        captured["sql"] = query
        captured["params"] = params
        return []

    scope = RoleListScope(tenant_wide=False, empresa_id=EMPRESA_A)
    with patch(
        "app.modules.users.application.services.user_service.execute_query",
        new=AsyncMock(side_effect=fake_query),
    ):
        await UsuarioService.obtener_roles_de_usuario(
            CLIENT_ID, USER_ID, list_scope=scope
        )

    assert "ur.empresa_id IS NULL" in captured["sql"]
    assert str(EMPRESA_A) in captured["params"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_obtener_roles_platform_no_empresa_filter():
    captured: Dict[str, Any] = {}

    async def fake_query(query, params=None):
        captured["sql"] = query
        return []

    scope = RoleListScope(tenant_wide=True)
    with patch(
        "app.modules.users.application.services.user_service.execute_query",
        new=AsyncMock(side_effect=fake_query),
    ):
        await UsuarioService.obtener_roles_de_usuario(
            CLIENT_ID, USER_ID, list_scope=scope
        )

    assert "ur.empresa_id IS NULL" not in captured["sql"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_revoke_global_from_tenant_raises():
    scope = RoleListScope(tenant_wide=False, empresa_id=EMPRESA_A)
    with patch(
        "app.modules.users.application.services.user_service.execute_query",
        new=AsyncMock(
            return_value=[
                {
                    "usuario_rol_id": uuid4(),
                    "es_activo": True,
                    "empresa_id": None,
                }
            ]
        ),
    ):
        with pytest.raises(ConflictError) as exc:
            await UsuarioService.revocar_rol_de_usuario(
                CLIENT_ID, USER_ID, ROL_ID, list_scope=scope
            )
    assert exc.value.internal_code == "ROLE_REVOKE_GLOBAL"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_revoke_other_empresa_raises_404():
    scope = RoleListScope(tenant_wide=False, empresa_id=EMPRESA_A)
    with patch(
        "app.modules.users.application.services.user_service.execute_query",
        new=AsyncMock(
            return_value=[
                {
                    "usuario_rol_id": uuid4(),
                    "es_activo": True,
                    "empresa_id": EMPRESA_B,
                }
            ]
        ),
    ):
        with pytest.raises(NotFoundError) as exc:
            await UsuarioService.revocar_rol_de_usuario(
                CLIENT_ID, USER_ID, ROL_ID, list_scope=scope
            )
    assert exc.value.internal_code == "ASSIGNMENT_NOT_FOUND"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_obtener_usuario_completo_join_includes_empresa_filter():
    captured: Dict[str, Any] = {}

    async def fake_query(query, params=None):
        captured["sql"] = query if isinstance(query, str) else str(query)
        captured["params"] = params
        return [
            {
                "usuario_id": USER_ID,
                "cliente_id": CLIENT_ID,
                "nombre_usuario": "u1",
                "correo": "a@b.com",
                "nombre": "A",
                "apellido": "B",
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

    scope = RoleListScope(tenant_wide=False, empresa_id=EMPRESA_A)
    with patch(
        "app.modules.users.application.services.user_service.execute_query",
        new=AsyncMock(side_effect=fake_query),
    ), patch.object(
        UsuarioService,
        "get_user_level_info",
        new=AsyncMock(
            return_value={
                "access_level": 2,
                "is_super_admin": False,
                "user_type": "user",
            }
        ),
    ), patch(
        "app.core.tenant.context.try_get_tenant_context",
        return_value=None,
    ):
        result = await UsuarioService.obtener_usuario_completo_por_id(
            CLIENT_ID, USER_ID, list_scope=scope
        )

    assert result is not None
    assert "ur.empresa_id IS NULL" in captured["sql"]
    assert captured["params"] == (str(EMPRESA_A), USER_ID, CLIENT_ID)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_obtener_usuario_completo_params_order_multi_db():
    captured: Dict[str, Any] = {}

    async def fake_query(query, params=None):
        captured["params"] = params
        return [
            {
                "usuario_id": USER_ID,
                "cliente_id": CLIENT_ID,
                "nombre_usuario": "u1",
                "correo": "a@b.com",
                "nombre": "A",
                "apellido": "B",
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

    scope = RoleListScope(tenant_wide=False, empresa_id=EMPRESA_A)
    tenant_ctx = type("TC", (), {"database_type": "multi"})()
    with patch(
        "app.modules.users.application.services.user_service.execute_query",
        new=AsyncMock(side_effect=fake_query),
    ), patch.object(
        UsuarioService,
        "get_user_level_info",
        new=AsyncMock(
            return_value={
                "access_level": 2,
                "is_super_admin": False,
                "user_type": "user",
            }
        ),
    ), patch(
        "app.core.tenant.context.try_get_tenant_context",
        return_value=tenant_ctx,
    ):
        result = await UsuarioService.obtener_usuario_completo_por_id(
            CLIENT_ID, USER_ID, list_scope=scope
        )

    assert result is not None
    assert captured["params"] == (str(EMPRESA_A), USER_ID)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_obtener_usuario_completo_platform_admin_params_without_empresa():
    captured: Dict[str, Any] = {}

    async def fake_query(query, params=None):
        captured["params"] = params
        return [
            {
                "usuario_id": USER_ID,
                "cliente_id": CLIENT_ID,
                "nombre_usuario": "u1",
                "correo": "a@b.com",
                "nombre": "A",
                "apellido": "B",
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

    scope = RoleListScope(tenant_wide=True)
    with patch(
        "app.modules.users.application.services.user_service.execute_query",
        new=AsyncMock(side_effect=fake_query),
    ), patch.object(
        UsuarioService,
        "get_user_level_info",
        new=AsyncMock(
            return_value={
                "access_level": 5,
                "is_super_admin": True,
                "user_type": "platform_admin",
            }
        ),
    ), patch(
        "app.core.tenant.context.try_get_tenant_context",
        return_value=None,
    ):
        result = await UsuarioService.obtener_usuario_completo_por_id(
            CLIENT_ID, USER_ID, list_scope=scope
        )

    assert result is not None
    assert captured["params"] == (USER_ID, CLIENT_ID)
