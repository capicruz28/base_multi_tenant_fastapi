"""Tests P0 — paginación inventario físico INV."""
from __future__ import annotations

from datetime import datetime, date
from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest

from app.core.tenant.empresa_context import set_current_empresa_id, reset_current_empresa_id
from app.shared.pagination.params import ErpPaginationParams
from app.shared.pagination.schemas import ErpPaginatedResponse
from app.modules.inv.application.services import inventario_fisico_service

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()


def _inv_row():
    return {
        "inventario_fisico_id": uuid4(),
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "almacen_id": uuid4(),
        "numero_inventario": "INV-001",
        "fecha_inventario": date.today(),
        "tipo_inventario": "general",
        "estado": "borrador",
        "fecha_creacion": datetime.utcnow(),
    }


@pytest.mark.asyncio
async def test_list_inventario_fisico_legacy():
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        with (
            patch(
                "app.modules.inv.application.services.inventario_fisico_service._validate_optional_list_filtros",
                new_callable=AsyncMock,
            ),
            patch(
                "app.modules.inv.application.services.inventario_fisico_service.list_inventarios_fisicos",
                new_callable=AsyncMock,
                return_value=[_inv_row()],
            ) as mock_list,
            patch(
                "app.modules.inv.application.services.inventario_fisico_service.count_inventarios_fisicos",
                new_callable=AsyncMock,
            ) as mock_count,
        ):
            result = await inventario_fisico_service.list_inventarios_fisicos_servicio(
                client_id=CLIENT_ID
            )
            assert isinstance(result, list)
            mock_count.assert_not_awaited()
            assert "pagination" not in (mock_list.await_args.kwargs or {})
    finally:
        reset_current_empresa_id(token)


@pytest.mark.asyncio
async def test_list_inventario_fisico_paginated():
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        pagination = ErpPaginationParams(page=1, limit=50)
        with (
            patch(
                "app.modules.inv.application.services.inventario_fisico_service._validate_optional_list_filtros",
                new_callable=AsyncMock,
            ),
            patch(
                "app.modules.inv.application.services.inventario_fisico_service.count_inventarios_fisicos",
                new_callable=AsyncMock,
                return_value=5,
            ),
            patch(
                "app.modules.inv.application.services.inventario_fisico_service.list_inventarios_fisicos",
                new_callable=AsyncMock,
                return_value=[_inv_row()],
            ),
        ):
            result = await inventario_fisico_service.list_inventarios_fisicos_servicio(
                client_id=CLIENT_ID,
                pagination=pagination,
            )
            assert isinstance(result, ErpPaginatedResponse)
            assert result.total == 5
    finally:
        reset_current_empresa_id(token)
