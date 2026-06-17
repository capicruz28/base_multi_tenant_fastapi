"""Tests P0 — paginación productos INV."""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest

from app.core.tenant.empresa_context import set_current_empresa_id, reset_current_empresa_id
from app.shared.pagination.params import ErpPaginationParams
from app.shared.pagination.schemas import ErpPaginatedResponse
from app.modules.inv.application.services import producto_service

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()


def _producto_row():
    return {
        "producto_id": uuid4(),
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo_sku": "SKU-001",
        "nombre": "Producto test",
        "tipo_producto": "bien",
        "unidad_medida_base_id": uuid4(),
        "moneda_costo": uuid4(),
        "moneda_venta": uuid4(),
        "es_activo": True,
        "fecha_creacion": datetime.utcnow(),
    }


@pytest.mark.asyncio
async def test_list_productos_legacy():
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        with (
            patch(
                "app.modules.inv.application.services.producto_service.list_productos",
                new_callable=AsyncMock,
                return_value=[_producto_row()],
            ) as mock_list,
            patch(
                "app.modules.inv.application.services.producto_service.count_productos",
                new_callable=AsyncMock,
            ) as mock_count,
        ):
            result = await producto_service.list_productos_servicio(
                client_id=CLIENT_ID,
                buscar="sku",
            )
            assert isinstance(result, list)
            mock_count.assert_not_awaited()
            assert "pagination" not in (mock_list.await_args.kwargs or {})
    finally:
        reset_current_empresa_id(token)


@pytest.mark.asyncio
async def test_list_productos_paginated_with_buscar():
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        pagination = ErpPaginationParams(page=1, limit=50)
        with (
            patch(
                "app.modules.inv.application.services.producto_service.count_productos",
                new_callable=AsyncMock,
                return_value=200,
            ) as mock_count,
            patch(
                "app.modules.inv.application.services.producto_service.list_productos",
                new_callable=AsyncMock,
                return_value=[_producto_row()],
            ) as mock_list,
        ):
            result = await producto_service.list_productos_servicio(
                client_id=CLIENT_ID,
                buscar="test",
                pagination=pagination,
            )
            assert isinstance(result, ErpPaginatedResponse)
            assert result.total == 200
            mock_count.assert_awaited_once_with(
                client_id=CLIENT_ID,
                empresa_id=EMPRESA_ID,
                categoria_id=None,
                tipo_producto=None,
                solo_activos=True,
                buscar="test",
            )
            assert mock_list.await_args.kwargs.get("pagination") == pagination
    finally:
        reset_current_empresa_id(token)
