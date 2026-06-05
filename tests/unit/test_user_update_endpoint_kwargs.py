"""Regression: PUT /usuarios/{id} must call UsuarioService.actualizar_usuario(usuario_data=...)."""
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest

from app.modules.users.presentation.endpoints import actualizar_usuario
from app.modules.users.presentation.schemas import UsuarioUpdate


@pytest.mark.asyncio
async def test_actualizar_usuario_passes_usuario_data_kwarg():
    usuario_id = UUID("102fca1b-000f-42d6-8183-e5bd72ff607b")
    cliente_id = UUID("e4c8e906-0e64-4f4e-a04d-8daee57dc7f8")
    body = UsuarioUpdate(correo="test@example.com", nombre="Test", es_activo=True)

    class FakeUser:
        cliente_id = UUID("e4c8e906-0e64-4f4e-a04d-8daee57dc7f8")
        nombre_usuario = "admin"

    with patch(
        "app.modules.users.presentation.endpoints.UsuarioService.actualizar_usuario",
        new_callable=AsyncMock,
    ) as mock_update:
        mock_update.return_value = {
            "usuario_id": usuario_id,
            "cliente_id": cliente_id,
            "nombre_usuario": "qa",
            "correo": "test@example.com",
            "es_activo": True,
            "fecha_creacion": "2026-01-01T00:00:00",
        }
        await actualizar_usuario(
            usuario_id=usuario_id,
            usuario_in=body,
            current_user=FakeUser(),
        )

    mock_update.assert_awaited_once()
    _, kwargs = mock_update.call_args
    assert "usuario_data" in kwargs
    assert "update_data" not in kwargs
    assert kwargs["usuario_data"]["correo"] == "test@example.com"
