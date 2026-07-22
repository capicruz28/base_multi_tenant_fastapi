"""Validación funcional Runtime Snapshot — Etapa 3.

Cubre Shared/Dedicated (vía get_connection_for_tenant), módulos contratados,
secuencias inactivas, multiempresa y SSOT cfg (policy/formato).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_active_user
from app.core.codigo.sequence_catalog import SequenceCatalog
from app.core.exceptions import configure_exception_handlers
from app.core.tenant.routing import OPERATION_CLASS_TENANT_DATA
from app.modules.cfg.application.services.codigo_runtime_snapshot_service import (
    CodigoRuntimeSnapshotService,
)
from app.modules.cfg.presentation.cfg_deps import (
    get_cfg_session_client_id,
    require_cfg_tenant_erp_session,
)
from app.modules.cfg.presentation.router import router as cfg_router
from app.modules.users.presentation.schemas import UsuarioReadWithRoles

CLIENT_ID = uuid4()
EMPRESA_A = uuid4()
EMPRESA_B = uuid4()
USER_ID = uuid4()

_SVC = (
    "app.modules.cfg.application.services.codigo_runtime_snapshot_service"
)


def _row(
    *,
    sequence_key: str,
    generation_policy: str = "AUTO_DEFAULT",
    prefijo: str = "SUC",
    separador: str = "",
    longitud_numero: int = 3,
    es_activo: bool = True,
    empresa_id: Any = None,
    scope_type: str = "EMPRESA",
) -> dict:
    return {
        "sequence_key": sequence_key,
        "scope_type": scope_type,
        "generation_policy": generation_policy,
        "es_activo": es_activo,
        "prefijo": prefijo,
        "separador": separador,
        "longitud_numero": longitud_numero,
        "empresa_id": empresa_id,
        "almacen_id": None,
        "punto_venta_id": None,
        "ultimo_numero": 999,
        "numero_inicial": 1,
        "secuencia_id": uuid4(),
    }


async def _build(
    *,
    modules: set[str],
    rows: list[dict],
    cliente_id=CLIENT_ID,
):
    class _Modulos:
        @staticmethod
        async def obtener_codigos_modulos_activos_cliente(_cid):
            return {m.upper() for m in modules}

    with (
        patch(f"{_SVC}.ClienteModuloService", _Modulos),
        patch(f"{_SVC}.get_connection_for_tenant") as mock_conn,
        patch(
            f"{_SVC}.list_codigo_secuencias",
            new=AsyncMock(return_value=rows),
        ) as mock_list,
    ):
        mock_conn.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_conn.return_value.__aexit__ = AsyncMock(return_value=None)
        snap = await CodigoRuntimeSnapshotService().build_snapshot(cliente_id)
        return snap, mock_conn, mock_list


@pytest.mark.unit
@pytest.mark.asyncio
async def test_e3_shared_tenant_uses_tenant_data_connection():
    """Shared: proyección vía get_connection_for_tenant(TENANT_DATA)."""
    snap, mock_conn, mock_list = await _build(
        modules={"ORG"},
        rows=[_row(sequence_key="org_sucursal", empresa_id=EMPRESA_A)],
    )
    mock_conn.assert_called_once_with(CLIENT_ID, OPERATION_CLASS_TENANT_DATA)
    mock_list.assert_awaited_once()
    assert snap.schema_version == "1.0"
    assert len(snap.items) == 1
    assert snap.items[0].sequence_key == "org_sucursal"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_e3_dedicated_tenant_same_builder_path():
    """Dedicated: mismo owner/builder; routing Dedicated ocurre dentro de get_connection_for_tenant."""
    dedicated_client = uuid4()
    snap, mock_conn, _ = await _build(
        modules={"ORG", "INV"},
        rows=[
            _row(sequence_key="org_cargo", empresa_id=EMPRESA_A, prefijo="CAR"),
            _row(
                sequence_key="inv_categoria_producto",
                empresa_id=EMPRESA_A,
                prefijo="CAT",
                generation_policy="AUTO_REQUIRED",
            ),
        ],
        cliente_id=dedicated_client,
    )
    mock_conn.assert_called_once_with(dedicated_client, OPERATION_CLASS_TENANT_DATA)
    keys = {i.sequence_key for i in snap.items}
    assert keys == {"org_cargo", "inv_categoria_producto"}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_e3_different_contracted_modules_filter():
    """Solo módulos contratados: ORG sí, INV no."""
    snap, _, _ = await _build(
        modules={"ORG"},
        rows=[
            _row(sequence_key="org_sucursal", empresa_id=EMPRESA_A),
            _row(sequence_key="inv_categoria_producto", empresa_id=EMPRESA_A),
            _row(sequence_key="org_empresa", scope_type="TENANT", prefijo="EMP"),
        ],
    )
    keys = {i.sequence_key for i in snap.items}
    assert keys == {"org_sucursal", "org_empresa"}
    assert all(i.modulo_codigo == "ORG" for i in snap.items)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_e3_inactive_sequences_included_with_flag():
    """Secuencia inactiva de módulo contratado aparece con es_activo=False."""
    snap, _, _ = await _build(
        modules={"ORG"},
        rows=[
            _row(
                sequence_key="org_departamento",
                empresa_id=EMPRESA_A,
                es_activo=False,
                prefijo="DEP",
            ),
        ],
    )
    assert len(snap.items) == 1
    assert snap.items[0].es_activo is False
    assert snap.items[0].sequence_key == "org_departamento"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_e3_multiempresa_same_sequence_key():
    """Multiempresa: un ítem por empresa_id para la misma sequence_key."""
    snap, _, _ = await _build(
        modules={"ORG"},
        rows=[
            _row(
                sequence_key="org_sucursal",
                empresa_id=EMPRESA_A,
                prefijo="SUA",
            ),
            _row(
                sequence_key="org_sucursal",
                empresa_id=EMPRESA_B,
                prefijo="SUB",
            ),
        ],
    )
    assert len(snap.items) == 2
    by_emp = {i.empresa_id: i for i in snap.items}
    assert by_emp[EMPRESA_A].prefijo == "SUA"
    assert by_emp[EMPRESA_B].prefijo == "SUB"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_e3_generation_policy_from_cfg_not_catalog():
    """generation_policy SSOT = fila cfg (puede diferir del catálogo)."""
    defn = SequenceCatalog.get("org_sucursal")
    assert defn.policy.value != "MANUAL_ONLY"
    snap, _, _ = await _build(
        modules={"ORG"},
        rows=[
            _row(
                sequence_key="org_sucursal",
                empresa_id=EMPRESA_A,
                generation_policy="MANUAL_ONLY",
            ),
        ],
    )
    assert snap.items[0].generation_policy == "MANUAL_ONLY"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_e3_effective_format_from_cfg():
    """prefijo / separador / longitud_numero = configuración efectiva cfg."""
    snap, _, _ = await _build(
        modules={"ORG"},
        rows=[
            _row(
                sequence_key="org_centro_costo",
                empresa_id=EMPRESA_A,
                prefijo="CCX",
                separador="-",
                longitud_numero=5,
            ),
        ],
    )
    item = snap.items[0]
    assert item.prefijo == "CCX"
    assert item.separador == "-"
    assert item.longitud_numero == 5
    # Capacidades de catálogo presentes; contador admin no proyectado
    assert item.supports_preview is True
    assert not hasattr(item, "ultimo_numero")


@pytest.mark.unit
def test_e3_http_endpoint_returns_service_snapshot():
    """GET /cfg/runtime/snapshot serializa el Snapshot del servicio Etapa 1."""
    app = FastAPI()
    configure_exception_handlers(app)
    app.include_router(cfg_router, prefix="/cfg")

    user = UsuarioReadWithRoles(
        usuario_id=USER_ID,
        cliente_id=CLIENT_ID,
        nombre_usuario="cfg_runtime_e3",
        fecha_creacion=datetime.utcnow(),
        permisos=[],
    )
    app.dependency_overrides[get_current_active_user] = lambda: user
    app.dependency_overrides[get_cfg_session_client_id] = lambda: CLIENT_ID
    app.dependency_overrides[require_cfg_tenant_erp_session] = lambda: user

    rows = [
        _row(
            sequence_key="org_sucursal",
            empresa_id=EMPRESA_A,
            generation_policy="AUTO_DEFAULT",
            prefijo="ZZZ",
            separador="-",
            longitud_numero=4,
            es_activo=False,
        ),
        _row(sequence_key="inv_categoria_producto", empresa_id=EMPRESA_A),
    ]

    class _Modulos:
        @staticmethod
        async def obtener_codigos_modulos_activos_cliente(_cid):
            return {"ORG"}

    with (
        patch(f"{_SVC}.ClienteModuloService", _Modulos),
        patch(f"{_SVC}.get_connection_for_tenant") as mock_conn,
        patch(
            f"{_SVC}.list_codigo_secuencias",
            new=AsyncMock(return_value=rows),
        ),
    ):
        mock_conn.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_conn.return_value.__aexit__ = AsyncMock(return_value=None)
        client = TestClient(app)
        resp = client.get("/cfg/runtime/snapshot")

    assert resp.status_code == 200
    body = resp.json()
    assert body["schema_version"] == "1.0"
    assert len(body["content_revision"]) == 64
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["sequence_key"] == "org_sucursal"
    assert item["generation_policy"] == "AUTO_DEFAULT"
    assert item["prefijo"] == "ZZZ"
    assert item["separador"] == "-"
    assert item["longitud_numero"] == 4
    assert item["es_activo"] is False
    assert "ultimo_numero" not in item
    assert "policy_drift" not in item
    assert "config_locked" not in item
