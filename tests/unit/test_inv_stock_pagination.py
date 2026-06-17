"""Tests P0 — paginación stock y alertas SQL INV."""
from __future__ import annotations

from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest

from app.core.tenant.empresa_context import set_current_empresa_id, reset_current_empresa_id
from app.shared.pagination.params import ErpPaginationParams
from app.shared.pagination.schemas import ErpPaginatedResponse
from app.modules.inv.application.services import stock_service

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
STOCK_ID = uuid4()
PRODUCTO_ID = uuid4()
ALMACEN_ID = uuid4()
MONEDA_ID = uuid4()


def _stock_row(stock_minimo="10", actual="5", reservada="0"):
    return {
        "stock_id": STOCK_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "producto_id": PRODUCTO_ID,
        "almacen_id": ALMACEN_ID,
        "cantidad_actual": Decimal(actual),
        "cantidad_reservada": Decimal(reservada),
        "moneda_id": MONEDA_ID,
        "stock_minimo": Decimal(stock_minimo),
    }


@pytest.mark.asyncio
async def test_list_stocks_legacy_no_count():
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        with (
            patch(
                "app.modules.inv.application.services.stock_service._validate_optional_filtro_empresa",
                new_callable=AsyncMock,
            ),
            patch(
                "app.modules.inv.application.services.stock_service.list_stocks",
                new_callable=AsyncMock,
                return_value=[_stock_row()],
            ) as mock_list,
            patch(
                "app.modules.inv.application.services.stock_service.count_stocks",
                new_callable=AsyncMock,
            ) as mock_count,
        ):
            result = await stock_service.list_stocks_servicio(client_id=CLIENT_ID)
            assert isinstance(result, list)
            mock_count.assert_not_awaited()
            assert "pagination" not in (mock_list.await_args.kwargs or {})
    finally:
        reset_current_empresa_id(token)


@pytest.mark.asyncio
async def test_list_stocks_paginated():
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        pagination = ErpPaginationParams(page=1, limit=50)
        with (
            patch(
                "app.modules.inv.application.services.stock_service._validate_optional_filtro_empresa",
                new_callable=AsyncMock,
            ),
            patch(
                "app.modules.inv.application.services.stock_service.count_stocks",
                new_callable=AsyncMock,
                return_value=100,
            ),
            patch(
                "app.modules.inv.application.services.stock_service.list_stocks",
                new_callable=AsyncMock,
                return_value=[_stock_row()],
            ),
        ):
            result = await stock_service.list_stocks_servicio(
                client_id=CLIENT_ID,
                pagination=pagination,
            )
            assert isinstance(result, ErpPaginatedResponse)
            assert result.total == 100
    finally:
        reset_current_empresa_id(token)


@pytest.mark.asyncio
async def test_list_stock_alertas_legacy():
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        row = _stock_row()
        row["cantidad_disponible"] = Decimal("5")
        with (
            patch(
                "app.modules.inv.application.services.stock_service.list_stock_alertas_bajo_minimo",
                new_callable=AsyncMock,
                return_value=[row],
            ) as mock_list,
            patch(
                "app.modules.inv.application.services.stock_service.count_stock_alertas_bajo_minimo",
                new_callable=AsyncMock,
            ) as mock_count,
        ):
            result = await stock_service.list_stock_alertas_servicio(client_id=CLIENT_ID)
            assert isinstance(result, list)
            assert len(result) == 1
            mock_count.assert_not_awaited()
            assert "pagination" not in (mock_list.await_args.kwargs or {})
    finally:
        reset_current_empresa_id(token)


@pytest.mark.asyncio
async def test_stock_alertas_sql_equivalence_logic():
    """Verifica que filas bajo mínimo incluyen cantidad_disponible calculada."""
    from app.infrastructure.database.queries.inv.stock_queries import (
        list_stock_alertas_bajo_minimo,
    )

    rows = [_stock_row(stock_minimo="10", actual="8", reservada="3")]
    with patch(
        "app.infrastructure.database.queries.inv.stock_queries.execute_query",
        new_callable=AsyncMock,
        return_value=rows,
    ):
        alerts = await list_stock_alertas_bajo_minimo(
            client_id=CLIENT_ID,
            empresa_id=EMPRESA_ID,
        )
    assert len(alerts) == 1
    assert alerts[0]["cantidad_disponible"] == Decimal("5")


@pytest.mark.unit
def test_stock_alertas_query_uses_producto_fallback_coalesce():
    """Alertas deben evaluar COALESCE(inv_stock.stock_minimo, inv_producto.stock_minimo)."""
    from sqlalchemy import and_, select
    from sqlalchemy.dialects import mssql

    from app.infrastructure.database.tables_erp import InvStockTable
    from app.infrastructure.database.queries.inv.stock_queries import (
        _build_stock_alerta_conditions,
        _stock_alerta_from_clause,
    )

    conditions = _build_stock_alerta_conditions(CLIENT_ID, EMPRESA_ID)
    query = (
        select(InvStockTable)
        .select_from(_stock_alerta_from_clause())
        .where(and_(*conditions))
    )
    compiled = str(
        query.compile(dialect=mssql.dialect(), compile_kwargs={"literal_binds": False})
    ).lower()
    assert "inv_producto" in compiled
    assert "coalesce" in compiled
    assert "stock_minimo" in compiled
