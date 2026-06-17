"""Tests P2-001 — ordenamiento server-side ORG."""
from __future__ import annotations

from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions import CustomException, configure_exception_handlers
from app.core.tenant.empresa_context import reset_current_empresa_id, set_current_empresa_id
from app.shared.pagination.params import ErpPaginationParams
from app.shared.pagination.sort import ErpSortParams
from app.modules.org.application.services import (
    empresa_service,
    centro_costo_service,
    parametro_service,
)
from app.modules.org.presentation.endpoints import router as org_router

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()


def _empresa_row(razon="Empresa B"):
    return {
        "empresa_id": uuid4(),
        "cliente_id": CLIENT_ID,
        "codigo_empresa": "E01",
        "razon_social": razon,
        "ruc": "20123456789",
        "es_activo": True,
    }


def _param_row(modulo="INV", codigo="B"):
    return {
        "parametro_id": uuid4(),
        "cliente_id": CLIENT_ID,
        "empresa_id": None,
        "modulo_codigo": modulo,
        "codigo_parametro": codigo,
        "nombre_parametro": f"Param {codigo}",
        "tipo_dato": "texto",
        "es_activo": True,
    }


@pytest.mark.asyncio
async def test_empresas_sort_propagated():
    with patch(
        "app.modules.org.application.services.empresa_service.list_empresas",
        new_callable=AsyncMock,
        return_value=[_empresa_row()],
    ) as mock_list:
        sort = ErpSortParams(sort_by="razon_social", sort_dir="asc")
        await empresa_service.list_empresas_servicio(client_id=CLIENT_ID, sort=sort)
    kwargs = mock_list.await_args.kwargs
    assert kwargs["sort_by"] == "razon_social"
    assert kwargs["sort_dir"] == "asc"


@pytest.mark.asyncio
async def test_centros_costo_sort_without_pagination():
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        sort = ErpSortParams(sort_by="nombre", sort_dir="desc")
        with patch(
            "app.modules.org.application.services.centro_costo_service.list_centros_costo",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_list:
            await centro_costo_service.list_centros_costo_servicio(
                client_id=CLIENT_ID,
                sort=sort,
            )
        kwargs = mock_list.await_args.kwargs
        assert kwargs["sort_by"] == "nombre"
        assert kwargs["sort_dir"] == "desc"
        assert "pagination" not in kwargs or kwargs.get("pagination") is None
    finally:
        reset_current_empresa_id(token)


@pytest.mark.asyncio
async def test_parametros_hybrid_sort_post_merge():
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        rows = [
            _param_row("ORG", "Z"),
            _param_row("ORG", "A"),
            _param_row("INV", "M"),
        ]
        sort = ErpSortParams(sort_by="codigo_parametro", sort_dir="asc")
        with patch(
            "app.modules.org.application.services.parametro_service.list_parametros_hybrid",
            new_callable=AsyncMock,
            return_value=rows,
        ):
            result = await parametro_service.list_parametros_servicio(
                client_id=CLIENT_ID,
                sort=sort,
            )
        assert [r.codigo_parametro for r in result] == ["A", "M", "Z"]
    finally:
        reset_current_empresa_id(token)


@pytest.mark.asyncio
async def test_parametros_invalid_sort_raises():
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        sort = ErpSortParams(sort_by="no_existe", sort_dir="asc")
        with patch(
            "app.modules.org.application.services.parametro_service.list_parametros_hybrid",
            new_callable=AsyncMock,
            return_value=[_param_row()],
        ):
            with pytest.raises(CustomException) as exc:
                await parametro_service.list_parametros_servicio(
                    client_id=CLIENT_ID,
                    sort=sort,
                )
            assert exc.value.status_code == 422
    finally:
        reset_current_empresa_id(token)


@pytest.mark.asyncio
async def test_parametros_sort_then_paginate():
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        rows = [_param_row("INV", f"P{i:02d}") for i in range(5)]
        pagination = ErpPaginationParams(page=2, limit=2)
        sort = ErpSortParams(sort_by="codigo_parametro", sort_dir="desc")
        with patch(
            "app.modules.org.application.services.parametro_service.list_parametros_hybrid",
            new_callable=AsyncMock,
            return_value=rows,
        ):
            result = await parametro_service.list_parametros_servicio(
                client_id=CLIENT_ID,
                pagination=pagination,
                sort=sort,
            )
        assert result.pagina_actual == 2
        assert len(result.items) == 2
        assert result.items[0].codigo_parametro == "P02"
    finally:
        reset_current_empresa_id(token)


def test_openapi_parametros_has_sort_params():
    app = FastAPI()
    configure_exception_handlers(app)
    app.include_router(org_router, prefix="/org")
    schema = app.openapi()
    get_op = schema["paths"]["/org/parametros"]["get"]
    param_names = [p["name"] for p in get_op.get("parameters", [])]
    assert "sort_by" in param_names
    assert "sort_dir" in param_names
