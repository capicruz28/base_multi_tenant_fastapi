"""Smoke HTTP + OpenAPI — certificación cfg MVP (T-I*)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_active_user
from app.core.exceptions import configure_exception_handlers
from app.modules.cfg.presentation.cfg_deps import (
    get_cfg_session_client_id,
    require_cfg_tenant_erp_session,
)
from app.modules.cfg.presentation.router import router as cfg_router
from app.modules.cfg.presentation.schemas import (
    CodigoSecuenciaPreviewResponse,
    CodigoSecuenciaRead,
)
from app.modules.users.presentation.schemas import UsuarioReadWithRoles

CLIENT_ID = uuid4()
SEQ_ID = uuid4()
USER_ID = uuid4()

_SPEC_OIDS = {
    "list_cfg_codigo_secuencias",
    "get_cfg_codigo_secuencia",
    "update_cfg_codigo_secuencia",
    "desactivar_cfg_codigo_secuencia",
    "reactivar_cfg_codigo_secuencia",
    "preview_cfg_codigo_secuencia",
}


def _usuario(*, permisos: list[str]) -> UsuarioReadWithRoles:
    return UsuarioReadWithRoles(
        usuario_id=USER_ID,
        cliente_id=CLIENT_ID,
        nombre_usuario="cfg_admin_test",
        fecha_creacion=datetime.utcnow(),
        permisos=permisos,
    )


def _read(**overrides) -> CodigoSecuenciaRead:
    data = {
        "secuencia_id": SEQ_ID,
        "sequence_key": "org_sucursal",
        "scope_type": "EMPRESA",
        "scope_fingerprint": "fp",
        "empresa_id": None,
        "almacen_id": None,
        "punto_venta_id": None,
        "prefijo": "SUC",
        "separador": "",
        "longitud_numero": 3,
        "numero_inicial": 1,
        "ultimo_numero": 1,
        "es_activo": True,
        "generation_policy": "AUTO_DEFAULT",
        "fecha_creacion": datetime(2026, 1, 1),
        "fecha_actualizacion": None,
        "usuario_actualizacion_id": None,
        "entity_table": "org_sucursal",
        "code_column": "codigo",
        "modulo_codigo": "ORG",
        "catalog_policy": "AUTO_DEFAULT",
        "supports_preview": True,
        "allow_manual": True,
        "sequence_family": "F1",
        "default_prefix": "SUC",
        "default_separator": "",
        "default_padding": 3,
        "config_locked": False,
        "policy_drift": False,
    }
    data.update(overrides)
    return CodigoSecuenciaRead.model_validate(data)


@pytest.fixture
def cfg_client():
    app = FastAPI()
    configure_exception_handlers(app)
    app.include_router(cfg_router, prefix="/cfg")
    client = TestClient(app)
    yield client
    client.app.dependency_overrides.clear()


def _override_session(client: TestClient, user: UsuarioReadWithRoles) -> None:
    client.app.dependency_overrides[get_current_active_user] = lambda: user
    client.app.dependency_overrides[get_cfg_session_client_id] = lambda: CLIENT_ID
    client.app.dependency_overrides[require_cfg_tenant_erp_session] = lambda: user


@pytest.mark.unit
def test_ti07_openapi_six_operation_ids():
    schema = json.loads(
        Path("app/docs/openapi_snapshot.json").read_text(encoding="utf-8")
    )
    found = set()
    for path, methods in schema.get("paths", {}).items():
        if "/cfg/secuencias" not in path:
            continue
        for body in methods.values():
            if isinstance(body, dict) and "operationId" in body:
                found.add(body["operationId"])
    assert found == _SPEC_OIDS
    cfg_blob = json.dumps(
        {p: m for p, m in schema["paths"].items() if "/cfg/secuencias" in p}
    )
    assert "/activar" not in cfg_blob
    assert "reactivar" in cfg_blob


@pytest.mark.unit
def test_ti01_list_403_sin_consultar(cfg_client):
    _override_session(cfg_client, _usuario(permisos=[]))
    resp = cfg_client.get("/cfg/secuencias")
    assert resp.status_code == 403


@pytest.mark.unit
def test_ti02_list_200_con_consultar(cfg_client):
    _override_session(cfg_client, _usuario(permisos=["cfg.secuencias.consultar"]))
    with patch(
        "app.modules.cfg.presentation.endpoints_codigo_secuencia.svc.list_codigo_secuencias_servicio",
        new_callable=AsyncMock,
        return_value=[_read()],
    ):
        resp = cfg_client.get("/cfg/secuencias")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.unit
def test_ti03_patch_403_solo_consultar(cfg_client):
    _override_session(cfg_client, _usuario(permisos=["cfg.secuencias.consultar"]))
    resp = cfg_client.patch(f"/cfg/secuencias/{SEQ_ID}", json={"prefijo": "ABC"})
    assert resp.status_code == 403


@pytest.mark.unit
def test_ti04_patch_200(cfg_client):
    _override_session(cfg_client, _usuario(permisos=["cfg.secuencias.actualizar"]))
    with patch(
        "app.modules.cfg.presentation.endpoints_codigo_secuencia.svc.update_codigo_secuencia_servicio",
        new_callable=AsyncMock,
        return_value=_read(prefijo="ABC"),
    ):
        resp = cfg_client.patch(
            f"/cfg/secuencias/{SEQ_ID}", json={"prefijo": "ABC"}
        )
    assert resp.status_code == 200
    assert resp.json()["prefijo"] == "ABC"


@pytest.mark.unit
def test_ti05_delete_reactivar_200(cfg_client):
    _override_session(cfg_client, _usuario(permisos=["cfg.secuencias.actualizar"]))
    with patch(
        "app.modules.cfg.presentation.endpoints_codigo_secuencia.svc.desactivar_codigo_secuencia_servicio",
        new_callable=AsyncMock,
        return_value=_read(es_activo=False),
    ):
        r1 = cfg_client.delete(f"/cfg/secuencias/{SEQ_ID}")
    with patch(
        "app.modules.cfg.presentation.endpoints_codigo_secuencia.svc.reactivar_codigo_secuencia_servicio",
        new_callable=AsyncMock,
        return_value=_read(es_activo=True),
    ):
        r2 = cfg_client.post(f"/cfg/secuencias/{SEQ_ID}/reactivar")
    assert r1.status_code == 200
    assert r1.json()["es_activo"] is False
    assert r2.status_code == 200
    assert r2.json()["es_activo"] is True


@pytest.mark.unit
def test_ti06_preview_200_disclaimer(cfg_client):
    _override_session(cfg_client, _usuario(permisos=["cfg.secuencias.consultar"]))
    preview = CodigoSecuenciaPreviewResponse(
        secuencia_id=SEQ_ID,
        sequence_key="org_sucursal",
        codigo_estimado="SUC002",
        ultimo_numero_actual=1,
        numero_inicial=1,
        consume_contador=False,
        es_activo=True,
        disclaimer="Estimación no vinculante.",
    )
    with patch(
        "app.modules.cfg.presentation.endpoints_codigo_secuencia.svc.preview_codigo_secuencia_servicio",
        new_callable=AsyncMock,
        return_value=preview,
    ):
        resp = cfg_client.post(f"/cfg/secuencias/{SEQ_ID}/preview")
    assert resp.status_code == 200
    body = resp.json()
    assert body["consume_contador"] is False
    assert body["disclaimer"]
