"""Tests P1 — paginación ORG centros-costo y parámetros híbridos."""
from __future__ import annotations

from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions import configure_exception_handlers
from app.core.tenant.empresa_context import reset_current_empresa_id, set_current_empresa_id
from app.shared.pagination.params import ErpPaginationParams
from app.shared.pagination.schemas import ErpPaginatedResponse
from app.modules.org.application.services import centro_costo_service, parametro_service
from app.modules.org.presentation.endpoints import router as org_router

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()


def _centro_row():
    return {
        "centro_costo_id": uuid4(),
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo": "CC01",
        "nombre": "Centro 1",
        "tipo_centro_costo": "operativo",
        "es_activo": True,
    }


def _param_row(modulo="INV", codigo="X", empresa_id=None):
    return {
        "parametro_id": uuid4(),
        "cliente_id": CLIENT_ID,
        "empresa_id": empresa_id,
        "modulo_codigo": modulo,
        "codigo_parametro": codigo,
        "nombre_parametro": "Param",
        "tipo_dato": "texto",
        "es_activo": True,
    }


@pytest.mark.asyncio
async def test_centros_costo_paginated():
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        pagination = ErpPaginationParams(page=1, limit=50)
        with (
            patch(
                "app.modules.org.application.services.centro_costo_service.count_centros_costo",
                new_callable=AsyncMock,
                return_value=10,
            ),
            patch(
                "app.modules.org.application.services.centro_costo_service.list_centros_costo",
                new_callable=AsyncMock,
                return_value=[_centro_row()],
            ) as mock_list,
        ):
            result = await centro_costo_service.list_centros_costo_servicio(
                client_id=CLIENT_ID,
                pagination=pagination,
            )
        assert isinstance(result, ErpPaginatedResponse)
        assert result.total == 10
        assert mock_list.await_args.kwargs.get("pagination") == pagination
    finally:
        reset_current_empresa_id(token)


@pytest.mark.asyncio
async def test_parametros_hybrid_post_merge_pagination():
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        rows = [_param_row("INV", f"P{i}") for i in range(5)]
        pagination = ErpPaginationParams(page=2, limit=2)
        with patch(
            "app.modules.org.application.services.parametro_service.list_parametros_hybrid",
            new_callable=AsyncMock,
            return_value=rows,
        ):
            result = await parametro_service.list_parametros_servicio(
                client_id=CLIENT_ID,
                pagination=pagination,
            )
        assert isinstance(result, ErpPaginatedResponse)
        assert result.total == 5
        assert result.pagina_actual == 2
        assert len(result.items) == 2
    finally:
        reset_current_empresa_id(token)


def test_openapi_centros_costo_union_response():
    app = FastAPI()
    configure_exception_handlers(app)
    app.include_router(org_router, prefix="/org")
    schema = app.openapi()
    get_op = schema["paths"]["/org/centros-costo"]["get"]
    response_schema = (
        get_op["responses"]["200"]["content"]["application/json"]["schema"]
    )
    assert "anyOf" in response_schema
    param_names = [p["name"] for p in get_op.get("parameters", [])]
    assert "page" in param_names
    assert "buscar" in param_names
