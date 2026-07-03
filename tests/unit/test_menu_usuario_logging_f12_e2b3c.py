"""F12-E2B3C — tests de política de logging MENU_USUARIO."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.modules.modulos.application.services import modulo_menu_service as svc
from app.modules.modulos.application.services.modulo_menu_service import ModuloMenuService
from app.modules.modulos.presentation.schemas import MenuUsuarioResponse


@pytest.mark.unit
class TestMenuUsuarioLoggingPolicy:
    @pytest.mark.asyncio
    async def test_obtener_menu_usuario_emits_start_finish_only(self):
        usuario_id = uuid4()
        cliente_id = uuid4()

        with patch(
            "app.modules.modulos.application.services.modulo_menu_service.settings"
        ) as mock_settings:
            mock_settings.ENABLE_AUTH_VERBOSE = False
            with patch(
                "app.modules.modulos.application.services.modulo_menu_service.execute_query",
                new=AsyncMock(return_value=[]),
            ), patch.object(
                ModuloMenuService,
                "_get_required_permissions_by_modulo",
                new=AsyncMock(return_value={}),
            ):
                with patch.object(svc.logger, "info") as mock_info:
                    with patch.object(svc.logger, "warning") as mock_warn:
                        with patch.object(svc.logger, "debug") as mock_debug:
                            result = await ModuloMenuService.obtener_menu_usuario(
                                usuario_id,
                                cliente_id,
                                is_super_admin=False,
                            )

        assert result == MenuUsuarioResponse(modulos=[])
        info_msgs = [str(c.args[0]) for c in mock_info.call_args_list]
        assert any("[MENU_USUARIO] Inicio" in m for m in info_msgs)
        finish_calls = [
            c for c in mock_info.call_args_list
            if "[MENU_USUARIO] Fin modulos=" in str(c.args[0])
        ]
        assert finish_calls
        assert finish_calls[0].args[1] == 0
        assert not any("INCLUIDO" in m for m in info_msgs)
        assert not any("Contexto is_super_admin" in m for m in info_msgs)
        mock_warn.assert_not_called()
        mock_debug.assert_not_called()

    @pytest.mark.asyncio
    async def test_obtener_menu_usuario_diagnostic_when_auth_verbose(self):
        usuario_id = uuid4()
        cliente_id = uuid4()

        with patch(
            "app.modules.modulos.application.services.modulo_menu_service.settings"
        ) as mock_settings:
            mock_settings.ENABLE_AUTH_VERBOSE = True
            with patch(
                "app.modules.modulos.application.services.modulo_menu_service.execute_query",
                new=AsyncMock(return_value=[]),
            ), patch.object(
                ModuloMenuService,
                "_get_required_permissions_by_modulo",
                new=AsyncMock(return_value={}),
            ):
                with patch.object(svc.logger, "info") as mock_info:
                    await ModuloMenuService.obtener_menu_usuario(
                        usuario_id,
                        cliente_id,
                        is_super_admin=False,
                    )

        info_msgs = [str(c.args[0]) for c in mock_info.call_args_list]
        assert any("Contexto is_super_admin" in m for m in info_msgs)
