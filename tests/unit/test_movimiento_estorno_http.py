"""
Tests HTTP — INV-P0-003 Etapa 4: POST /{movimiento_id}/estornar (BC-31).
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
from app.core.exceptions import ConflictError, NotFoundError, configure_exception_handlers
from app.modules.inv.application.services.inv_estorno_proceso import (
    ESTORNO_INTEGRACION_NO_MVP_CODE,
    MOVIMIENTO_YA_ESTORNADO_CODE,
)
from app.modules.inv.presentation.endpoints_movimientos_proceso import router
from app.modules.inv.presentation.inv_deps import get_inv_session_client_id
from app.modules.users.presentation.schemas import UsuarioReadWithRoles

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
USUARIO_ID = uuid4()
MOVIMIENTO_ID = uuid4()
MONEDA_ID = uuid4()
TIPO_MOVIMIENTO_ID = uuid4()


def _usuario(*, permisos: list[str]) -> UsuarioReadWithRoles:
    return UsuarioReadWithRoles(
        usuario_id=USUARIO_ID,
        cliente_id=CLIENT_ID,
        nombre_usuario="usuario_estorno_test",
        fecha_creacion=datetime.utcnow(),
        permisos=permisos,
    )


@pytest.fixture
def estorno_http_client():
    app = FastAPI()
    configure_exception_handlers(app)
    app.include_router(router)
    return TestClient(app)


def _url(movimiento_id=MOVIMIENTO_ID) -> str:
    return f"/{movimiento_id}/estornar"


def _movimiento_estornado() -> dict:
    return {
        "movimiento_id": MOVIMIENTO_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "numero_movimiento": "MOV-001",
        "tipo_movimiento_id": TIPO_MOVIMIENTO_ID,
        "fecha_movimiento": datetime.utcnow(),
        "fecha_contable": datetime.utcnow().date(),
        "estado": "estornado",
        "moneda_id": MONEDA_ID,
        "total_items": 1,
        "total_cantidad": Decimal("10"),
        "total_costo": Decimal("50"),
    }


def _override_inv_session(client: TestClient, *, permisos: list[str]) -> None:
    client.app.dependency_overrides[get_current_active_user] = (
        lambda: _usuario(permisos=permisos)
    )
    client.app.dependency_overrides[get_inv_session_client_id] = lambda: CLIENT_ID


@pytest.mark.unit
def test_h01_estorno_exitoso(estorno_http_client):
    """H-01: POST estornar → 200; delega a estornar_movimiento_servicio."""
    _override_inv_session(estorno_http_client, permisos=["inv.movimiento.estornar"])
    servicio_mock = AsyncMock(return_value=_movimiento_estornado())

    try:
        with patch(
            "app.modules.inv.presentation.endpoints_movimientos_proceso.movimiento_proceso_service.estornar_movimiento_servicio",
            servicio_mock,
        ):
            response = estorno_http_client.post(
                _url(),
                json={"motivo": "Corrección operativa"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["estado"] == "estornado"
        servicio_mock.assert_awaited_once_with(
            client_id=CLIENT_ID,
            movimiento_id=MOVIMIENTO_ID,
            motivo="Corrección operativa",
            usuario_estorno_id=USUARIO_ID,
        )
    finally:
        estorno_http_client.app.dependency_overrides.clear()


@pytest.mark.unit
def test_h02_doble_estorno_409(estorno_http_client):
    """H-02: doble estorno → 409 MOVIMIENTO_YA_ESTORNADO."""
    _override_inv_session(estorno_http_client, permisos=["inv.movimiento.estornar"])

    try:
        with patch(
            "app.modules.inv.presentation.endpoints_movimientos_proceso.movimiento_proceso_service.estornar_movimiento_servicio",
            new=AsyncMock(
                side_effect=ConflictError(
                    detail="El movimiento ya fue estornado.",
                    internal_code=MOVIMIENTO_YA_ESTORNADO_CODE,
                )
            ),
        ):
            response = estorno_http_client.post(_url(), json={})

        assert response.status_code == 409
        assert response.json()["error_code"] == MOVIMIENTO_YA_ESTORNADO_CODE
    finally:
        estorno_http_client.app.dependency_overrides.clear()


@pytest.mark.unit
def test_h03_inventario_fisico_409(estorno_http_client):
    """H-03: origen inventario_fisico → 409 ESTORNO_INTEGRACION_NO_MVP."""
    _override_inv_session(estorno_http_client, permisos=["inv.movimiento.estornar"])

    try:
        with patch(
            "app.modules.inv.presentation.endpoints_movimientos_proceso.movimiento_proceso_service.estornar_movimiento_servicio",
            new=AsyncMock(
                side_effect=ConflictError(
                    detail="Bloqueo MVP inventario físico",
                    internal_code=ESTORNO_INTEGRACION_NO_MVP_CODE,
                )
            ),
        ):
            response = estorno_http_client.post(_url(), json={})

        assert response.status_code == 409
        assert response.json()["error_code"] == ESTORNO_INTEGRACION_NO_MVP_CODE
    finally:
        estorno_http_client.app.dependency_overrides.clear()


@pytest.mark.unit
def test_h04_recepcion_409(estorno_http_client):
    """H-04: origen RECEPCION → 409 ESTORNO_INTEGRACION_NO_MVP."""
    _override_inv_session(estorno_http_client, permisos=["inv.movimiento.estornar"])

    try:
        with patch(
            "app.modules.inv.presentation.endpoints_movimientos_proceso.movimiento_proceso_service.estornar_movimiento_servicio",
            new=AsyncMock(
                side_effect=ConflictError(
                    detail="Bloqueo MVP recepción",
                    internal_code=ESTORNO_INTEGRACION_NO_MVP_CODE,
                )
            ),
        ):
            response = estorno_http_client.post(_url(), json={})

        assert response.status_code == 409
        assert response.json()["error_code"] == ESTORNO_INTEGRACION_NO_MVP_CODE
    finally:
        estorno_http_client.app.dependency_overrides.clear()


@pytest.mark.unit
def test_h05_permiso_denegado_403(estorno_http_client):
    """H-05: sin inv.movimiento.estornar → 403."""
    _override_inv_session(estorno_http_client, permisos=[])
    servicio_mock = AsyncMock()

    try:
        with patch(
            "app.modules.inv.presentation.endpoints_movimientos_proceso.movimiento_proceso_service.estornar_movimiento_servicio",
            servicio_mock,
        ):
            response = estorno_http_client.post(_url(), json={})

        assert response.status_code == 403
        servicio_mock.assert_not_awaited()
    finally:
        estorno_http_client.app.dependency_overrides.clear()


@pytest.mark.unit
def test_h06_movimiento_inexistente_404(estorno_http_client):
    """H-06: movimiento inexistente → 404."""
    _override_inv_session(estorno_http_client, permisos=["inv.movimiento.estornar"])

    try:
        with patch(
            "app.modules.inv.presentation.endpoints_movimientos_proceso.movimiento_proceso_service.estornar_movimiento_servicio",
            new=AsyncMock(
                side_effect=NotFoundError(detail="Movimiento no encontrado")
            ),
        ):
            response = estorno_http_client.post(_url(), json={})

        assert response.status_code == 404
    finally:
        estorno_http_client.app.dependency_overrides.clear()


@pytest.mark.unit
def test_openapi_solo_agrega_estornar(estorno_http_client):
    """OpenAPI: endpoint nuevo; contratos procesar/autorizar/anular intactos."""
    schema = estorno_http_client.app.openapi()
    paths = schema["paths"]

    assert "/{movimiento_id}/estornar" in paths
    assert "post" in paths["/{movimiento_id}/estornar"]
    assert paths["/{movimiento_id}/estornar"]["post"]["summary"].startswith(
        "Estornar movimiento"
    )

    for ruta in ("/{movimiento_id}/procesar", "/{movimiento_id}/autorizar", "/{movimiento_id}/anular"):
        assert ruta in paths
        assert "post" in paths[ruta]

    estornar_refs = schema["components"]["schemas"].get("MotivoEstorno")
    assert estornar_refs is not None
    assert "motivo" in estornar_refs.get("properties", {})
