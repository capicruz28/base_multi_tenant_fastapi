"""Regression: eliminar_usuario must await execute_update (soft-delete)."""
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest

from app.modules.users.application.services.user_service import UsuarioService


@pytest.mark.asyncio
async def test_eliminar_usuario_awaits_execute_update_and_returns_dict():
    cliente_id = UUID("e4c8e906-0e64-4f4e-a04d-8daee57dc7f8")
    usuario_id = UUID("102fca1b-000f-42d6-8183-e5bd72ff607b")
    row = {"usuario_id": str(usuario_id), "es_eliminado": True, "nombre_usuario": "qa"}

    with (
        patch(
            "app.modules.users.application.services.user_service.execute_query",
            new_callable=AsyncMock,
            return_value=[{"es_eliminado": False}],
        ),
        patch(
            "app.modules.users.application.services.user_service.execute_update",
            new_callable=AsyncMock,
        ) as mock_update,
        patch(
            "app.modules.users.application.services.user_service.get_permission_resolver",
            create=True,
        ),
    ):
        mock_update.side_effect = [row, None]
        result = await UsuarioService.eliminar_usuario(
            cliente_id=cliente_id,
            usuario_id=usuario_id,
        )

    assert mock_update.await_count == 2
    first_call = mock_update.await_args_list[0]
    assert "UPDATE dbo.usuario" in first_call[0][0]
    assert result["usuario_id"] == row["usuario_id"]
    assert result["es_eliminado"] is True
