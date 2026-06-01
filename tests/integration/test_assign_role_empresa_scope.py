"""
I2.2 integración: endpoint assign role + resolución de empresa.
"""
from __future__ import annotations

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.tenant.company_scope import RoleAssignTarget
from app.modules.users.presentation.endpoints import assign_rol_to_usuario
from app.modules.users.presentation.schemas import UsuarioRolAssignBody

CLIENT_ID = uuid4()
USER_ID = uuid4()
ROL_ID = uuid4()
EMPRESA_A = uuid4()


def _payload(empresa_id=None) -> Dict[str, Any]:
    p: Dict[str, Any] = {
        "sub": "tenant_admin",
        "cliente_id": str(CLIENT_ID),
        "user_type": "tenant_admin",
        "access_level": 4,
    }
    if empresa_id is not None:
        p["empresa_id"] = str(empresa_id)
    return p


@pytest.mark.integration
@pytest.mark.asyncio
async def test_assign_endpoint_passes_target_empresa_to_service():
    captured: Dict[str, Any] = {}
    mock_user = MagicMock()
    mock_user.cliente_id = CLIENT_ID
    mock_user.user_type = "tenant_admin"
    mock_user.is_super_admin = False

    async def fake_assign(**kwargs):
        captured.update(kwargs)
        return {
            "usuario_rol_id": uuid4(),
            "usuario_id": USER_ID,
            "rol_id": ROL_ID,
            "cliente_id": CLIENT_ID,
            "empresa_id": EMPRESA_A,
            "fecha_asignacion": "2025-01-01T00:00:00",
            "es_activo": True,
        }

    with patch(
        "app.modules.users.presentation.endpoints.resolve_role_assign_target",
        new=AsyncMock(
            return_value=RoleAssignTarget(empresa_id=EMPRESA_A, is_global=False)
        ),
    ), patch(
        "app.modules.users.presentation.endpoints.is_platform_operator",
        return_value=False,
    ), patch(
        "app.modules.users.presentation.endpoints.UsuarioService.asignar_rol_a_usuario",
        new=AsyncMock(side_effect=fake_assign),
    ):
        response = await assign_rol_to_usuario(
            usuario_id=USER_ID,
            rol_id=ROL_ID,
            body=None,
            current_user=mock_user,
            payload=_payload(EMPRESA_A),
        )

    assert captured["target_empresa_id"] == EMPRESA_A
    assert response.empresa_id == EMPRESA_A


@pytest.mark.integration
@pytest.mark.asyncio
async def test_assign_endpoint_platform_global_flag():
    captured: Dict[str, Any] = {}
    mock_user = MagicMock()
    mock_user.cliente_id = CLIENT_ID
    mock_user.user_type = "platform_admin"
    mock_user.is_super_admin = True

    async def fake_assign(**kwargs):
        captured.update(kwargs)
        return {
            "usuario_rol_id": uuid4(),
            "usuario_id": USER_ID,
            "rol_id": ROL_ID,
            "cliente_id": CLIENT_ID,
            "empresa_id": None,
            "fecha_asignacion": "2025-01-01T00:00:00",
            "es_activo": True,
        }

    with patch(
        "app.modules.users.presentation.endpoints.resolve_role_assign_target",
        new=AsyncMock(
            return_value=RoleAssignTarget(empresa_id=None, is_global=True)
        ),
    ), patch(
        "app.modules.users.presentation.endpoints.is_platform_operator",
        return_value=True,
    ), patch(
        "app.modules.users.presentation.endpoints.UsuarioService.asignar_rol_a_usuario",
        new=AsyncMock(side_effect=fake_assign),
    ):
        await assign_rol_to_usuario(
            usuario_id=USER_ID,
            rol_id=ROL_ID,
            body=UsuarioRolAssignBody(scope_global=True),
            current_user=mock_user,
            payload={"user_type": "platform_admin", "es_superadmin": True},
        )

    assert captured["target_empresa_id"] is None
    assert captured["allow_global_promotion"] is True
