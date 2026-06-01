"""
Smoke tests: router legacy /api/v1/modulos eliminado; rutas vigentes siguen montadas.

No requiere JWT: solo verifica que el path existe (≠404) o fue retirado (404).
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

LEGACY_MODULOS_PATHS = [
    "/api/v1/modulos/",
    "/api/v1/modulos/search/",
    "/api/v1/modulos/00000000-0000-0000-0000-000000000001/",
    "/api/v1/modulos/clientes/00000000-0000-0000-0000-000000000001/modulos/",
    (
        "/api/v1/modulos/clientes/00000000-0000-0000-0000-000000000001/"
        "modulos/00000000-0000-0000-0000-000000000002/activar/"
    ),
]

ACTIVE_ROUTE_SAMPLES = [
    ("GET", "/api/v1/modulos-v2/"),
    ("GET", "/api/v1/cliente-modulo/cliente/00000000-0000-0000-0000-000000000001/"),
    ("GET", "/api/v1/conexiones/clientes/00000000-0000-0000-0000-000000000001/"),
]


@pytest.mark.parametrize("path", LEGACY_MODULOS_PATHS)
def test_legacy_modulos_routes_return_404(path: str):
    """El router deprecated no debe estar montado."""
    response = client.get(path) if path.endswith("/") and "activar" not in path else client.post(path, json={})
    assert response.status_code == 404, f"{path} should be removed, got {response.status_code}"


@pytest.mark.parametrize("method,path", ACTIVE_ROUTE_SAMPLES)
def test_current_modulos_routes_are_mounted(method: str, path: str):
    """Rutas vigentes existen (401/403/422/500 aceptables; no 404 por router ausente)."""
    if method == "GET":
        response = client.get(path)
    else:
        response = client.post(path, json={})
    assert response.status_code != 404, (
        f"{method} {path} should be mounted, got 404"
    )


def test_openapi_has_no_legacy_modulos_paths():
    """OpenAPI no debe listar /api/v1/modulos (sin sufijo -v2 ni -menus)."""
    schema = app.openapi()
    paths = schema.get("paths", {})
    legacy = [
        p
        for p in paths
        if p.startswith("/api/v1/modulos")
        and not p.startswith("/api/v1/modulos-v2")
        and not p.startswith("/api/v1/modulos-menus")
    ]
    assert legacy == [], f"Legacy paths still in OpenAPI: {legacy}"
