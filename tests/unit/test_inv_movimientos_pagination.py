"""Tests P0 — paginación movimientos INV."""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest

from app.core.tenant.empresa_context import set_current_empresa_id, reset_current_empresa_id
from app.shared.pagination.params import ErpPaginationParams
from app.shared.pagination.schemas import ErpPaginatedResponse
from app.modules.inv.application.services import movimiento_service

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()


def _mov_row():
    return {
        "movimiento_id": uuid4(),
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "numero_movimiento": "MOV-001",
        "tipo_movimiento_id": uuid4(),
        "fecha_movimiento": datetime.utcnow(),
        "fecha_contable": datetime.utcnow().date(),
        "estado": "borrador",
        "es_activo": True,
    }


@pytest.mark.asyncio
async def test_list_movimientos_legacy_returns_list():
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        with (
            patch(
                "app.modules.inv.application.services.movimiento_service._validate_optional_list_filtros",
                new_callable=AsyncMock,
            ),
            patch(
                "app.modules.inv.application.services.movimiento_service.list_movimientos",
                new_callable=AsyncMock,
                return_value=[_mov_row()],
            ) as mock_list,
            patch(
                "app.modules.inv.application.services.movimiento_service.count_movimientos",
                new_callable=AsyncMock,
            ) as mock_count,
        ):
            result = await movimiento_service.list_movimientos_servicio(client_id=CLIENT_ID)
            assert isinstance(result, list)
            assert len(result) == 1
            mock_list.assert_awaited_once()
            mock_count.assert_not_awaited()
            assert "pagination" not in (mock_list.await_args.kwargs or {})
    finally:
        reset_current_empresa_id(token)


@pytest.mark.asyncio
async def test_list_movimientos_paginated_returns_envelope():
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        pagination = ErpPaginationParams(page=1, limit=50)
        with (
            patch(
                "app.modules.inv.application.services.movimiento_service._validate_optional_list_filtros",
                new_callable=AsyncMock,
            ),
            patch(
                "app.modules.inv.application.services.movimiento_service.count_movimientos",
                new_callable=AsyncMock,
                return_value=120,
            ) as mock_count,
            patch(
                "app.modules.inv.application.services.movimiento_service.list_movimientos",
                new_callable=AsyncMock,
                return_value=[_mov_row()],
            ) as mock_list,
        ):
            result = await movimiento_service.list_movimientos_servicio(
                client_id=CLIENT_ID,
                pagination=pagination,
            )
            assert isinstance(result, ErpPaginatedResponse)
            assert result.total == 120
            assert result.pagina_actual == 1
            assert result.limit == 50
            assert result.total_paginas == 3
            mock_count.assert_awaited_once()
            mock_list.assert_awaited_once()
            assert mock_list.await_args.kwargs.get("pagination") == pagination
    finally:
        reset_current_empresa_id(token)
