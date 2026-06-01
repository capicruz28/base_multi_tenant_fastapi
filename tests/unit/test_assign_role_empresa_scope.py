"""
I2.2: assign_role multi-empresa (target resolution + matriz de conflictos).
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import AuthorizationError, ConflictError, ValidationError
from app.core.tenant.company_scope import (
    RoleAssignTarget,
    assignment_scope_matches,
    resolve_role_assign_target,
)
from app.modules.users.application.services.user_service import UsuarioService

CLIENT_ID = uuid4()
USER_ID = uuid4()
ROL_ID = uuid4()
EMPRESA_A = uuid4()
EMPRESA_B = uuid4()


def _payload(*, empresa_id=None, user_type="user", is_super_admin=False, es_superadmin=False):
    p: Dict[str, Any] = {
        "sub": "admin",
        "cliente_id": str(CLIENT_ID),
        "user_type": user_type,
        "is_super_admin": is_super_admin,
    }
    if empresa_id is not None:
        p["empresa_id"] = str(empresa_id)
    if es_superadmin:
        p["es_superadmin"] = True
    return p


@pytest.mark.unit
def test_assignment_scope_matches_global_and_scoped():
    assert assignment_scope_matches(None, None) is True
    assert assignment_scope_matches(EMPRESA_A, EMPRESA_A) is True
    assert assignment_scope_matches(None, EMPRESA_A) is False
    assert assignment_scope_matches(EMPRESA_A, EMPRESA_B) is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_target_defaults_to_session_empresa():
    with patch(
        "app.core.tenant.company_scope.resolve_empresa_id_for_rbac",
        return_value=EMPRESA_A,
    ):
        target = await resolve_role_assign_target(
            cliente_id=CLIENT_ID,
            payload=_payload(empresa_id=EMPRESA_A),
        )
    assert target.empresa_id == EMPRESA_A
    assert target.is_global is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tenant_admin_without_session_empresa_forbidden():
    with patch(
        "app.core.tenant.company_scope.resolve_empresa_id_for_rbac",
        return_value=None,
    ):
        with pytest.raises(AuthorizationError) as exc:
            await resolve_role_assign_target(
                cliente_id=CLIENT_ID,
                payload=_payload(),
            )
    assert exc.value.internal_code == "MISSING_SESSION_EMPRESA"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tenant_admin_cannot_assign_global():
    with pytest.raises(AuthorizationError) as exc:
        await resolve_role_assign_target(
            cliente_id=CLIENT_ID,
            scope_global=True,
            payload=_payload(empresa_id=EMPRESA_A),
        )
    assert exc.value.internal_code == "GLOBAL_ASSIGN_FORBIDDEN"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_platform_admin_scope_global():
    target = await resolve_role_assign_target(
        cliente_id=CLIENT_ID,
        scope_global=True,
        payload=_payload(user_type="platform_admin", is_super_admin=True),
        user_type="platform_admin",
        is_super_admin=True,
    )
    assert target.is_global is True
    assert target.empresa_id is None


@pytest.mark.unit
def test_validate_conflict_global_existing_scoped_request():
    with pytest.raises(ConflictError) as exc:
        UsuarioService._validate_assign_scope_conflict(None, EMPRESA_A)
    assert exc.value.internal_code == "ROLE_ALREADY_GLOBAL"


@pytest.mark.unit
def test_validate_conflict_scoped_other_empresa():
    with pytest.raises(ConflictError) as exc:
        UsuarioService._validate_assign_scope_conflict(EMPRESA_A, EMPRESA_B)
    assert exc.value.internal_code == "ROLE_ASSIGNED_OTHER_EMPRESA"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_asignar_rol_insert_includes_empresa_id():
    captured: Dict[str, Any] = {}

    async def fake_insert(query, params):
        captured["sql"] = query
        captured["params"] = params
        return {
            "usuario_rol_id": uuid4(),
            "usuario_id": USER_ID,
            "rol_id": ROL_ID,
            "cliente_id": CLIENT_ID,
            "empresa_id": EMPRESA_A,
            "fecha_asignacion": "2025-01-01",
            "es_activo": True,
        }

    with patch.object(
        UsuarioService,
        "obtener_usuario_por_id",
        new=AsyncMock(return_value={"usuario_id": USER_ID}),
    ), patch(
        "app.modules.rbac.application.services.rol_service.RolService.obtener_rol_por_id",
        new=AsyncMock(return_value={"rol_id": ROL_ID, "es_activo": True}),
    ), patch(
        "app.modules.users.application.services.user_service.execute_query",
        new=AsyncMock(return_value=[]),
    ), patch(
        "app.modules.users.application.services.user_service.execute_insert",
        new=AsyncMock(side_effect=fake_insert),
    ), patch(
        "app.core.authorization.permission_resolver.get_permission_resolver",
    ) as mock_resolver:
        mock_resolver.return_value.invalidate_for_user = MagicMock()
        result = await UsuarioService.asignar_rol_a_usuario(
            CLIENT_ID,
            USER_ID,
            ROL_ID,
            target_empresa_id=EMPRESA_A,
        )

    assert "empresa_id" in captured["sql"]
    assert captured["params"][3] == EMPRESA_A
    assert result["empresa_id"] == EMPRESA_A


@pytest.mark.unit
@pytest.mark.asyncio
async def test_asignar_rol_active_global_request_scoped_raises():
    with patch.object(
        UsuarioService,
        "obtener_usuario_por_id",
        new=AsyncMock(return_value={"usuario_id": USER_ID}),
    ), patch(
        "app.modules.rbac.application.services.rol_service.RolService.obtener_rol_por_id",
        new=AsyncMock(return_value={"rol_id": ROL_ID, "es_activo": True}),
    ), patch(
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
            await UsuarioService.asignar_rol_a_usuario(
                CLIENT_ID,
                USER_ID,
                ROL_ID,
                target_empresa_id=EMPRESA_A,
            )
    assert exc.value.internal_code == "ROLE_ALREADY_GLOBAL"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_asignar_rol_active_other_empresa_raises():
    with patch.object(
        UsuarioService,
        "obtener_usuario_por_id",
        new=AsyncMock(return_value={"usuario_id": USER_ID}),
    ), patch(
        "app.modules.rbac.application.services.rol_service.RolService.obtener_rol_por_id",
        new=AsyncMock(return_value={"rol_id": ROL_ID, "es_activo": True}),
    ), patch(
        "app.modules.users.application.services.user_service.execute_query",
        new=AsyncMock(
            return_value=[
                {
                    "usuario_rol_id": uuid4(),
                    "es_activo": True,
                    "empresa_id": EMPRESA_A,
                }
            ]
        ),
    ):
        with pytest.raises(ConflictError) as exc:
            await UsuarioService.asignar_rol_a_usuario(
                CLIENT_ID,
                USER_ID,
                ROL_ID,
                target_empresa_id=EMPRESA_B,
            )
    assert exc.value.internal_code == "ROLE_ASSIGNED_OTHER_EMPRESA"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_asignar_rol_idempotent_same_scope():
    ur_id = uuid4()
    row = {
        "usuario_rol_id": ur_id,
        "usuario_id": USER_ID,
        "rol_id": ROL_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_A,
        "fecha_asignacion": "2025-01-01",
        "es_activo": True,
    }

    async def fake_query(query, params=None):
        q = query if isinstance(query, str) else str(query)
        if "usuario_rol_id" in q and "SELECT" in q.upper():
            return [row]
        return [
            {"usuario_rol_id": ur_id, "es_activo": True, "empresa_id": EMPRESA_A}
        ]

    with patch.object(
        UsuarioService,
        "obtener_usuario_por_id",
        new=AsyncMock(return_value={"usuario_id": USER_ID}),
    ), patch(
        "app.modules.rbac.application.services.rol_service.RolService.obtener_rol_por_id",
        new=AsyncMock(return_value={"rol_id": ROL_ID, "es_activo": True}),
    ), patch(
        "app.modules.users.application.services.user_service.execute_query",
        new=AsyncMock(side_effect=fake_query),
    ), patch(
        "app.modules.users.application.services.user_service.execute_insert",
        new=AsyncMock(),
    ) as mock_insert:
        result = await UsuarioService.asignar_rol_a_usuario(
            CLIENT_ID,
            USER_ID,
            ROL_ID,
            target_empresa_id=EMPRESA_A,
        )
    mock_insert.assert_not_called()
    assert result["empresa_id"] == EMPRESA_A
