"""Tests P1-INV-08 — listas globales detalle deprecated en OpenAPI."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions import configure_exception_handlers
from app.modules.inv.presentation.endpoints import router as inv_router


def test_movimientos_detalle_list_deprecated_in_openapi():
    app = FastAPI()
    configure_exception_handlers(app)
    app.include_router(inv_router, prefix="/inv")
    schema = TestClient(app).get("/openapi.json").json()
    get_op = schema["paths"]["/inv/movimientos-detalle"]["get"]
    assert get_op.get("deprecated") is True


def test_inventario_fisico_detalle_list_deprecated_in_openapi():
    app = FastAPI()
    configure_exception_handlers(app)
    app.include_router(inv_router, prefix="/inv")
    schema = TestClient(app).get("/openapi.json").json()
    get_op = schema["paths"]["/inv/inventario-fisico-detalle"]["get"]
    assert get_op.get("deprecated") is True
