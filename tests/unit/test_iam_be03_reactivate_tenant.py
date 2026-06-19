"""IAM-BE-03: POST reactivate sin falso 403 por comparación tenant en endpoint."""
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest

from app.modules.users.application.services.user_service import UsuarioService
from app.modules.users.presentation.endpoints import reactivate_usuario
from app.modules.users.presentation.schemas import UsuarioReadWithRoles

CLIENTE_ID = UUID("e4c8e906-0e64-4f4e-a04d-8daee57dc7f8")
USUARIO_ID = uuid4()


def _admin_user() -> UsuarioReadWithRoles:
    return UsuarioReadWithRoles(
        usuario_id=uuid4(),
        cliente_id=CLIENTE_ID,
        nombre_usuario="admin",
        correo="admin@test.com",
        es_activo=True,
        correo_confirmado=True,
        fecha_creacion="2026-01-01T00:00:00",
        roles=[],
        access_level=4,
        is_super_admin=False,
        user_type="tenant_admin",
        permisos=["admin.usuario.actualizar"],
    )


def test_uuid_vs_str_comparison_is_root_cause_of_false_403():
    """Documenta la causa: cliente_id string (BD) != UUID (JWT/schema)."""
    assert str(CLIENTE_ID) != CLIENTE_ID


@pytest.mark.asyncio
async def test_reactivate_endpoint_delegates_to_service_like_delete():
    with patch.object(
        UsuarioService,
        "reactivar_usuario",
        new_callable=AsyncMock,
        return_value={
            "usuario_id": USUARIO_ID,
            "cliente_id": CLIENTE_ID,
            "nombre_usuario": "restored",
            "correo": "r@test.com",
            "es_activo": True,
            "correo_confirmado": True,
            "fecha_creacion": "2026-01-01T00:00:00",
        },
    ) as mock_reactivar:
        result = await reactivate_usuario(
            usuario_id=USUARIO_ID,
            current_user=_admin_user(),
        )

    assert result["es_activo"] is True
    mock_reactivar.assert_awaited_once_with(
        cliente_id=CLIENTE_ID,
        usuario_id=USUARIO_ID,
    )


@pytest.mark.asyncio
async def test_reactivate_endpoint_does_not_prefetch_for_tenant_check():
    """Sin pre-check en endpoint: obtener_usuario_incluyendo_eliminados solo en servicio."""
    with (
        patch.object(
            UsuarioService,
            "obtener_usuario_incluyendo_eliminados",
            new_callable=AsyncMock,
        ) as mock_fetch,
        patch.object(
            UsuarioService,
            "reactivar_usuario",
            new_callable=AsyncMock,
            return_value={
                "usuario_id": USUARIO_ID,
                "cliente_id": CLIENTE_ID,
                "nombre_usuario": "restored",
                "correo": "r@test.com",
                "es_activo": True,
                "correo_confirmado": True,
                "fecha_creacion": "2026-01-01T00:00:00",
            },
        ),
    ):
        await reactivate_usuario(
            usuario_id=USUARIO_ID,
            current_user=_admin_user(),
        )

    mock_fetch.assert_not_called()
