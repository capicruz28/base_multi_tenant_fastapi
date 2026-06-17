"""Tests P2-001 — ordenamiento server-side INV."""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions import CustomException, configure_exception_handlers
from app.core.tenant.empresa_context import reset_current_empresa_id, set_current_empresa_id
from app.shared.pagination.sort import ErpSortParams
from app.modules.inv.application.services import (
    categoria_service,
    movimiento_service,
    stock_service,
)
from app.modules.inv.presentation.endpoints import router as inv_router

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()


def _categoria_row(nombre="Zeta"):
    return {
        "categoria_id": uuid4(),
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo": "CAT01",
        "nombre": nombre,
        "es_activo": True,
        "fecha_creacion": datetime.utcnow(),
    }


@pytest.mark.asyncio
async def test_categorias_sort_propagated_to_query():
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        sort = ErpSortParams(sort_by="codigo", sort_dir="desc")
        with patch(
            "app.modules.inv.application.services.categoria_service.list_categorias",
            new_callable=AsyncMock,
            return_value=[_categoria_row()],
        ) as mock_list:
            await categoria_service.list_categorias_servicio(
                client_id=CLIENT_ID,
                sort=sort,
            )
        kwargs = mock_list.await_args.kwargs
        assert kwargs["sort_by"] == "codigo"
        assert kwargs["sort_dir"] == "desc"
    finally:
        reset_current_empresa_id(token)


@pytest.mark.asyncio
async def test_categorias_no_sort_preserves_legacy_kwargs():
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        with patch(
            "app.modules.inv.application.services.categoria_service.list_categorias",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_list:
            await categoria_service.list_categorias_servicio(client_id=CLIENT_ID)
        kwargs = mock_list.await_args.kwargs
        assert kwargs.get("sort_by") is None
        assert kwargs.get("sort_dir") is None
    finally:
        reset_current_empresa_id(token)


@pytest.mark.asyncio
async def test_movimientos_invalid_sort_raises_from_query_layer():
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        sort = ErpSortParams(sort_by="campo_inexistente", sort_dir="asc")
        with (
            patch(
                "app.modules.inv.application.services.movimiento_service._validate_optional_list_filtros",
                new_callable=AsyncMock,
            ),
            patch(
                "app.modules.inv.application.services.movimiento_service.list_movimientos",
                new_callable=AsyncMock,
                side_effect=CustomException(
                    status_code=422,
                    detail="sort_by 'campo_inexistente' no es una columna ordenable válida.",
                    internal_code="INVALID_SORT_COLUMN",
                ),
            ),
        ):
            with pytest.raises(CustomException) as exc:
                await movimiento_service.list_movimientos_servicio(
                    client_id=CLIENT_ID,
                    sort=sort,
                )
            assert exc.value.status_code == 422
    finally:
        reset_current_empresa_id(token)


@pytest.mark.asyncio
async def test_stock_sort_with_pagination():
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        from app.shared.pagination.params import ErpPaginationParams

        sort = ErpSortParams(sort_by="cantidad_actual", sort_dir="desc")
        pagination = ErpPaginationParams(page=1, limit=10)
        with (
            patch(
                "app.modules.inv.application.services.stock_service.count_stocks",
                new_callable=AsyncMock,
                return_value=5,
            ),
            patch(
                "app.modules.inv.application.services.stock_service.list_stocks",
                new_callable=AsyncMock,
                return_value=[],
            ) as mock_list,
        ):
            await stock_service.list_stocks_servicio(
                client_id=CLIENT_ID,
                pagination=pagination,
                sort=sort,
            )
        kwargs = mock_list.await_args.kwargs
        assert kwargs["sort_by"] == "cantidad_actual"
        assert kwargs["sort_dir"] == "desc"
        assert kwargs["pagination"] == pagination
    finally:
        reset_current_empresa_id(token)


def test_openapi_categorias_has_sort_params():
    app = FastAPI()
    configure_exception_handlers(app)
    app.include_router(inv_router, prefix="/inv")
    schema = app.openapi()
    get_op = schema["paths"]["/inv/categorias"]["get"]
    param_names = [p["name"] for p in get_op.get("parameters", [])]
    assert "sort_by" in param_names
    assert "sort_dir" in param_names
    assert "page" in param_names
