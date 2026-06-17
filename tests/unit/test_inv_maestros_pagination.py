"""Tests P1 — paginación maestros INV."""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest

from app.core.tenant.empresa_context import reset_current_empresa_id, set_current_empresa_id
from app.shared.pagination.params import ErpPaginationParams
from app.shared.pagination.schemas import ErpPaginatedResponse
from app.modules.inv.application.services import categoria_service, almacen_service

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()


def _categoria_row():
    return {
        "categoria_id": uuid4(),
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo": "CAT01",
        "nombre": "Categoria test",
        "es_activo": True,
        "fecha_creacion": datetime.utcnow(),
    }


@pytest.mark.asyncio
async def test_categorias_legacy_no_count():
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        with (
            patch(
                "app.modules.inv.application.services.categoria_service.list_categorias",
                new_callable=AsyncMock,
                return_value=[_categoria_row()],
            ),
            patch(
                "app.modules.inv.application.services.categoria_service.count_categorias",
                new_callable=AsyncMock,
            ) as mock_count,
        ):
            result = await categoria_service.list_categorias_servicio(client_id=CLIENT_ID)
        assert isinstance(result, list)
        mock_count.assert_not_awaited()
    finally:
        reset_current_empresa_id(token)


@pytest.mark.asyncio
async def test_categorias_paginated_envelope():
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        pagination = ErpPaginationParams(page=2, limit=10)
        with (
            patch(
                "app.modules.inv.application.services.categoria_service.count_categorias",
                new_callable=AsyncMock,
                return_value=25,
            ),
            patch(
                "app.modules.inv.application.services.categoria_service.list_categorias",
                new_callable=AsyncMock,
                return_value=[_categoria_row()],
            ) as mock_list,
        ):
            result = await categoria_service.list_categorias_servicio(
                client_id=CLIENT_ID,
                pagination=pagination,
            )
        assert isinstance(result, ErpPaginatedResponse)
        assert result.pagina_actual == 2
        assert result.total == 25
        assert mock_list.await_args.kwargs.get("pagination") == pagination
    finally:
        reset_current_empresa_id(token)


@pytest.mark.asyncio
async def test_almacenes_paginated_with_buscar():
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        pagination = ErpPaginationParams(page=1, limit=50)
        with (
            patch(
                "app.modules.inv.application.services.almacen_service.count_almacenes",
                new_callable=AsyncMock,
                return_value=3,
            ) as mock_count,
            patch(
                "app.modules.inv.application.services.almacen_service.list_almacenes",
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            result = await almacen_service.list_almacenes_servicio(
                client_id=CLIENT_ID,
                buscar="alm",
                pagination=pagination,
            )
        assert isinstance(result, ErpPaginatedResponse)
        mock_count.assert_awaited_once_with(
            client_id=CLIENT_ID,
            empresa_id=EMPRESA_ID,
            sucursal_id=None,
            solo_activos=True,
            buscar="alm",
        )
    finally:
        reset_current_empresa_id(token)
