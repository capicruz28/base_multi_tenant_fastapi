"""F-004: listar_modulos uses contar_modulos for pagination total."""
from unittest.mock import AsyncMock, patch

import pytest

from app.modules.modulos.application.services.modulo_service import ModuloService


@pytest.mark.asyncio
async def test_contar_modulos_uses_same_filters_as_list():
    with patch(
        "app.modules.modulos.application.services.modulo_service.execute_query",
        new_callable=AsyncMock,
        return_value=[{"count_1": 42}],
    ) as mock_query:
        total = await ModuloService.contar_modulos(solo_activos=True, categoria="core")

    assert total == 42
    mock_query.assert_awaited_once()
    compiled = str(mock_query.await_args[0][0])
    assert "modulo" in compiled.lower()


@pytest.mark.asyncio
async def test_listar_modulos_endpoint_uses_contar_not_len():
    from app.modules.modulos.presentation import endpoints_modulos

    with (
        patch.object(
            ModuloService,
            "obtener_modulos",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch.object(
            ModuloService,
            "contar_modulos",
            new_callable=AsyncMock,
            return_value=100,
        ) as mock_count,
    ):
        user = object()
        result = await endpoints_modulos.listar_modulos(
            skip=10,
            limit=25,
            solo_activos=False,
            categoria=None,
            current_user=user,
        )

    mock_count.assert_awaited_once_with(solo_activos=False, categoria=None)
    assert result["pagination"]["total"] == 100
    assert result["pagination"]["has_next"] is True
