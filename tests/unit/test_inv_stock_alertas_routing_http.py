"""
Tests BLK-001 — precedencia HTTP /inv/stock/alertas vs /inv/stock/{stock_id}.

Montaje: mismo orden que endpoints.py (alertas antes que stock).
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_active_user
from app.core.exceptions import configure_exception_handlers
from app.core.tenant.empresa_context import reset_current_empresa_id, set_current_empresa_id
from app.modules.inv.presentation.endpoints import router as inv_router
from app.modules.inv.presentation.endpoints_stock import router as stock_router
from app.modules.inv.presentation.endpoints_stock_alertas import router as stock_alertas_router
from app.modules.users.presentation.schemas import UsuarioReadWithRoles

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
USUARIO_ID = uuid4()
STOCK_ID = uuid4()
PRODUCTO_ID = uuid4()
ALMACEN_ID = uuid4()
MONEDA_ID = uuid4()


def _usuario() -> UsuarioReadWithRoles:
    return UsuarioReadWithRoles(
        usuario_id=USUARIO_ID,
        cliente_id=CLIENT_ID,
        nombre_usuario="stock_alertas_routing_test",
        fecha_creacion=datetime.utcnow(),
        permisos=["inv.stock.leer"],
    )


def _stock_row() -> dict:
    return {
        "stock_id": STOCK_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "producto_id": PRODUCTO_ID,
        "almacen_id": ALMACEN_ID,
        "cantidad_actual": Decimal("5"),
        "cantidad_reservada": Decimal("0"),
        "moneda_id": MONEDA_ID,
        "stock_minimo": Decimal("10"),
        "cantidad_disponible": Decimal("5"),
    }


def _mount_stock_routers_blk001_order(app: FastAPI) -> None:
    """Replica el orden corregido en endpoints.py (alertas antes que stock)."""
    app.include_router(stock_alertas_router, prefix="/inv/stock/alertas")
    app.include_router(stock_router, prefix="/inv/stock")


@pytest.fixture
def stock_routing_client():
    app = FastAPI()
    configure_exception_handlers(app)
    _mount_stock_routers_blk001_order(app)
    app.dependency_overrides[get_current_active_user] = lambda: _usuario()
    return TestClient(app)


@pytest.fixture
def inv_openapi_client():
    app = FastAPI()
    configure_exception_handlers(app)
    app.include_router(inv_router, prefix="/inv")
    return TestClient(app)


@pytest.mark.unit
def test_blk001_stock_alertas_legacy_no_uuid_path_collision(stock_routing_client):
    """GET /inv/stock/alertas no debe interpretarse como /inv/stock/{stock_id}."""
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        with patch(
            "app.modules.inv.presentation.endpoints_stock_alertas.stock_service.list_stock_alertas_servicio",
            new=AsyncMock(return_value=[_stock_row()]),
        ) as mock_alertas:
            resp = stock_routing_client.get("/inv/stock/alertas")

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) == 1
        mock_alertas.assert_awaited_once()
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
def test_blk001_stock_alertas_paginated_envelope(stock_routing_client):
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        envelope = {
            "items": [_stock_row()],
            "total": 1,
            "pagina_actual": 1,
            "total_paginas": 1,
            "limit": 50,
        }
        with patch(
            "app.modules.inv.presentation.endpoints_stock_alertas.stock_service.list_stock_alertas_servicio",
            new=AsyncMock(return_value=envelope),
        ):
            resp = stock_routing_client.get("/inv/stock/alertas?page=1&limit=50")

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["total"] == 1
        assert body["pagina_actual"] == 1
        assert body["limit"] == 50
        assert len(body["items"]) == 1
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
def test_blk001_stock_alertas_limit_without_page_stays_legacy(stock_routing_client):
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        with patch(
            "app.modules.inv.presentation.endpoints_stock_alertas.stock_service.list_stock_alertas_servicio",
            new=AsyncMock(return_value=[]),
        ):
            resp = stock_routing_client.get("/inv/stock/alertas?limit=50")

        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.parametrize(
    "query,expected_fragment",
    [
        ("page=0", "query.page"),
        ("page=1&limit=101", "query.limit"),
    ],
)
def test_blk001_stock_alertas_invalid_pagination_returns_422(
    stock_routing_client, query: str, expected_fragment: str
):
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        resp = stock_routing_client.get(f"/inv/stock/alertas?{query}")
        assert resp.status_code == 422, resp.text
        detail = resp.json().get("detail", "")
        if isinstance(detail, list):
            joined = " ".join(str(x) for x in detail)
        else:
            joined = str(detail)
        assert expected_fragment in joined
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
def test_blk001_stock_detail_by_uuid_still_resolves(stock_routing_client):
    """Regresión: /inv/stock/{stock_id} sigue operativo tras el fix de precedencia."""
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        with patch(
            "app.modules.inv.presentation.endpoints_stock.stock_service.get_stock_servicio",
            new=AsyncMock(return_value=_stock_row()),
        ) as mock_detail:
            resp = stock_routing_client.get(f"/inv/stock/{STOCK_ID}")

        assert resp.status_code == 200, resp.text
        assert resp.json()["stock_id"] == str(STOCK_ID)
        mock_detail.assert_awaited_once()
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
def test_blk001_openapi_stock_alertas_and_stock_detail_paths(inv_openapi_client):
    schema = inv_openapi_client.app.openapi()
    paths = schema["paths"]

    assert "/inv/stock/alertas" in paths
    alertas_get = paths["/inv/stock/alertas"]["get"]
    assert alertas_get.get("operationId")
    assert "alertas_stock_bajo_minimo" in alertas_get["operationId"]
    param_names = [p["name"] for p in alertas_get.get("parameters", [])]
    assert "page" in param_names
    assert "limit" in param_names

    response_schema = (
        alertas_get.get("responses", {})
        .get("200", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {})
    )
    assert "anyOf" in response_schema

    assert "/inv/stock/{stock_id}" in paths
    assert "get" in paths["/inv/stock/{stock_id}"]
