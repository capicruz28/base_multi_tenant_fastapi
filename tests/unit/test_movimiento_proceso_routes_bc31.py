"""
Tests RC1.1 / BC-31 — equivalencia rutas legacy vs canónicas de proceso movimiento.

Montaje: doble include_router del mismo movimientos_proceso_router (patrón endpoints.py).
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
from app.modules.inv.presentation.endpoints import router as inv_router
from app.modules.inv.presentation.endpoints_movimientos_proceso import (
    router as movimientos_proceso_router,
)
from app.modules.users.presentation.schemas import UsuarioReadWithRoles

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
USUARIO_ID = uuid4()
MOVIMIENTO_ID = uuid4()
MONEDA_ID = uuid4()
TIPO_MOVIMIENTO_ID = uuid4()

_LEGACY_PREFIX = ""
_CANONICAL_PREFIX = "/movimientos"

_PROCESO_ACCIONES = (
    ("procesar", "inv.movimiento.procesar", "procesar_movimiento_servicio", None),
    ("autorizar", "inv.movimiento.autorizar", "autorizar_movimiento_servicio", None),
    ("anular", "inv.movimiento.anular", "anular_movimiento_servicio", {"motivo": "Anulación test"}),
    (
        "estornar",
        "inv.movimiento.estornar",
        "estornar_movimiento_servicio",
        {"motivo": "Estorno test"},
    ),
)

_LEGACY_OPENAPI_PATHS = (
    "/inv/{movimiento_id}/procesar",
    "/inv/{movimiento_id}/autorizar",
    "/inv/{movimiento_id}/anular",
    "/inv/{movimiento_id}/estornar",
)

_CANONICAL_OPENAPI_PATHS = (
    "/inv/movimientos/{movimiento_id}/procesar",
    "/inv/movimientos/{movimiento_id}/autorizar",
    "/inv/movimientos/{movimiento_id}/anular",
    "/inv/movimientos/{movimiento_id}/estornar",
)


def _usuario(*, permisos: list[str]) -> UsuarioReadWithRoles:
    return UsuarioReadWithRoles(
        usuario_id=USUARIO_ID,
        cliente_id=CLIENT_ID,
        nombre_usuario="usuario_bc31_test",
        fecha_creacion=datetime.utcnow(),
        permisos=permisos,
    )


def _movimiento_respuesta(*, estado: str = "procesado") -> dict:
    return {
        "movimiento_id": MOVIMIENTO_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "numero_movimiento": "MOV-BC31",
        "tipo_movimiento_id": TIPO_MOVIMIENTO_ID,
        "fecha_movimiento": datetime.utcnow().isoformat(),
        "fecha_contable": datetime.utcnow().date().isoformat(),
        "estado": estado,
        "moneda_id": MONEDA_ID,
        "total_items": 1,
        "total_cantidad": str(Decimal("10")),
        "total_costo": str(Decimal("50")),
    }


@pytest.fixture
def bc31_proceso_client():
    """Doble include del router de proceso (legacy + canónico)."""
    app = FastAPI()
    configure_exception_handlers(app)
    app.include_router(movimientos_proceso_router, tags=["INV - Movimientos Proceso"])
    app.include_router(
        movimientos_proceso_router,
        prefix=_CANONICAL_PREFIX,
        tags=["INV - Movimientos Proceso"],
    )
    return TestClient(app)


@pytest.fixture
def bc31_inv_openapi_client():
    """Router INV completo para validación OpenAPI (RC1.1)."""
    app = FastAPI()
    configure_exception_handlers(app)
    app.include_router(inv_router, prefix="/inv")
    return TestClient(app)


def _ruta(prefix: str, accion: str) -> str:
    return f"{prefix}/{MOVIMIENTO_ID}/{accion}"


@pytest.mark.unit
@pytest.mark.parametrize(
    "accion,permiso,servicio_attr,body",
    _PROCESO_ACCIONES,
    ids=["BC31-01-procesar", "BC31-02-autorizar", "BC31-03-anular", "BC31-04-estornar"],
)
def test_bc31_legacy_y_canonica_equivalentes(
    bc31_proceso_client,
    accion: str,
    permiso: str,
    servicio_attr: str,
    body: dict | None,
):
    """BC31-01..04: misma respuesta HTTP y misma delegación al servicio."""
    bc31_proceso_client.app.dependency_overrides[get_current_active_user] = (
        lambda: _usuario(permisos=[permiso])
    )
    payload = body if body is not None else {}
    estado = "estornado" if accion == "estornar" else "procesado"
    if accion == "autorizar":
        estado = "autorizado"
    if accion == "anular":
        estado = "anulado"
    respuesta = _movimiento_respuesta(estado=estado)
    patch_target = (
        f"app.modules.inv.presentation.endpoints_movimientos_proceso"
        f".movimiento_proceso_service.{servicio_attr}"
    )

    try:
        with patch(patch_target, new=AsyncMock(return_value=respuesta)) as servicio_mock:
            legacy = bc31_proceso_client.post(
                _ruta(_LEGACY_PREFIX, accion),
                json=payload,
            )
            canonical = bc31_proceso_client.post(
                _ruta(_CANONICAL_PREFIX, accion),
                json=payload,
            )

        assert legacy.status_code == 200, legacy.text
        assert canonical.status_code == 200, canonical.text
        assert legacy.json() == canonical.json()
        assert servicio_mock.await_count == 2
    finally:
        bc31_proceso_client.app.dependency_overrides.clear()


@pytest.mark.unit
def test_bc31_05_openapi_rutas_canonicas_presentes(bc31_inv_openapi_client):
    """BC31-05: OpenAPI expone las 4 rutas canónicas bajo /inv/movimientos/."""
    schema = bc31_inv_openapi_client.app.openapi()
    paths = schema["paths"]

    for ruta in _CANONICAL_OPENAPI_PATHS:
        assert ruta in paths, f"Falta ruta canónica: {ruta}"
        assert "post" in paths[ruta]


@pytest.mark.unit
def test_bc31_06_openapi_rutas_legacy_y_operation_ids_unicos(bc31_inv_openapi_client):
    """BC31-06: rutas legacy conservadas; operationId sin colisiones."""
    schema = bc31_inv_openapi_client.app.openapi()
    paths = schema["paths"]

    for ruta in _LEGACY_OPENAPI_PATHS:
        assert ruta in paths, f"Falta ruta legacy: {ruta}"
        assert "post" in paths[ruta]

    operation_ids: list[str] = []
    for path, methods in paths.items():
        if not (
            path.startswith("/inv/movimientos/{movimiento_id}/")
            or path.startswith("/inv/{movimiento_id}/")
        ):
            continue
        if path.endswith(("/procesar", "/autorizar", "/anular", "/estornar")):
            op_id = methods["post"].get("operationId")
            assert op_id, f"operationId ausente en {path}"
            operation_ids.append(op_id)

    assert len(operation_ids) == 8
    assert len(set(operation_ids)) == 8, (
        f"Colisión operationId: {operation_ids}"
    )
