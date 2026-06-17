"""
Tests unitarios — aprobación de inventario físico (F1, F2, F3).

Casos CP-01 a CP-07 + reglas v1.0: aprobar solo desde finalizado y con diferencias.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.sql.dml import Insert
from sqlalchemy.sql.selectable import Select

from app.core.exceptions import NotFoundError
from app.core.tenant.empresa_context import reset_current_empresa_id, set_current_empresa_id
from app.infrastructure.database.tables_erp import (
    InvMovimientoDetalleTable,
    InvMovimientoTable,
)
from app.modules.inv.application.services import inventario_fisico_aprobacion_service
from app.modules.inv.application.services.inventario_fisico_aprobacion_service import (
    _clasificar_lineas_aprobacion,
)


CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
INVENTARIO_ID = uuid4()
ALMACEN_ID = uuid4()
TIPO_MOVIMIENTO_ID = uuid4()
MONEDA_ID = uuid4()
PRODUCTO_1 = uuid4()
PRODUCTO_2 = uuid4()
UM_ID = uuid4()
MOVIMIENTO_AJUSTE_ID = uuid4()


class _FakeUowContext:
    def __init__(self, uow):
        self._uow = uow

    async def __aenter__(self):
        return self._uow

    async def __aexit__(self, *args):
        return False


def _set_empresa_ctx(empresa_id):
    return set_current_empresa_id(empresa_id)


def _base_inv(*, estado: str = "en_proceso") -> dict:
    return {
        "inventario_fisico_id": INVENTARIO_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "numero_inventario": "INV-FIS-001",
        "fecha_inventario": date(2026, 3, 1),
        "almacen_id": ALMACEN_ID,
        "estado": estado,
        "movimiento_ajuste_id": None,
    }


def _detalle(producto_id, sistema, contada, *, costo=Decimal("10")) -> dict:
    return {
        "producto_id": producto_id,
        "cantidad_sistema": sistema,
        "cantidad_contada": contada,
        "costo_unitario": costo,
    }


def _count_inserts(mock_uow, table) -> int:
    count = 0
    for call in mock_uow.execute.call_args_list:
        query = call[0][0]
        if isinstance(query, Insert) and query.table.name == table.name:
            count += 1
    return count


def _common_patches(mock_uow):
    return (
        patch(
            "app.modules.inv.application.services.inventario_fisico_aprobacion_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ),
        patch(
            "app.modules.inv.application.services.inventario_fisico_aprobacion_service.get_moneda_by_codigo",
            new=AsyncMock(return_value={"moneda_id": MONEDA_ID}),
        ),
        patch(
            "app.modules.inv.application.services.inventario_fisico_aprobacion_service.get_tipo_movimiento_by_id",
            new=AsyncMock(return_value={"clase_movimiento": "ajuste"}),
        ),
        patch(
            "app.modules.inv.application.services.inventario_fisico_aprobacion_service.get_almacen_by_id",
            new=AsyncMock(return_value={"almacen_id": ALMACEN_ID}),
        ),
        patch(
            "app.modules.inv.application.services.inventario_fisico_aprobacion_service.get_producto_by_id",
            new=AsyncMock(
                return_value={
                    "producto_id": PRODUCTO_1,
                    "unidad_medida_base_id": UM_ID,
                }
            ),
        ),
        patch(
            "app.modules.inv.application.services.inventario_fisico_aprobacion_service.procesar_movimiento_servicio",
            new=AsyncMock(),
        ),
    )


def _make_uow(inv_row: dict, detalle_rows: list[dict], closed_row: dict | None = None):
    """Mock UoW: SELECT inv → SELECT det → mutaciones → SELECT cierre."""
    closed = closed_row or inv_row
    phase = {"step": 0}

    async def execute(query, *args, **kwargs):
        if isinstance(query, Insert):
            return {"rows_affected": 1}
        if phase["step"] == 0:
            phase["step"] = 1
            return [inv_row]
        if phase["step"] == 1:
            phase["step"] = 2
            return detalle_rows
        if isinstance(query, Select):
            return [closed]
        return {"rows_affected": 1}

    mock_uow = AsyncMock()
    mock_uow.execute = AsyncMock(side_effect=execute)
    return mock_uow


@pytest.mark.unit
def test_clasificar_lineas_sin_diferencias():
    detalles = [
        _detalle(PRODUCTO_1, Decimal("10"), Decimal("10")),
        _detalle(PRODUCTO_2, Decimal("5"), Decimal("5")),
    ]
    contados, items, cant_abs, lineas = _clasificar_lineas_aprobacion(detalles)
    assert contados == 2
    assert items == 0
    assert cant_abs == Decimal("0")
    assert lineas == []


@pytest.mark.unit
def test_clasificar_lineas_con_diferencias():
    detalles = [
        _detalle(PRODUCTO_1, Decimal("10"), Decimal("12")),
        _detalle(PRODUCTO_2, Decimal("5"), Decimal("5")),
    ]
    contados, items, cant_abs, lineas = _clasificar_lineas_aprobacion(detalles)
    assert contados == 2
    assert items == 1
    assert cant_abs == Decimal("2")
    assert len(lineas) == 1
    assert lineas[0].diferencia == Decimal("2")


@pytest.mark.unit
def test_clasificar_lineas_cantidad_cero_es_contada():
    detalles = [_detalle(PRODUCTO_1, Decimal("5"), Decimal("0"))]
    contados, items, cant_abs, lineas = _clasificar_lineas_aprobacion(detalles)
    assert contados == 1
    assert items == 1
    assert lineas[0].diferencia == Decimal("-5")


@pytest.mark.unit
def test_clasificar_lineas_null_es_pendiente_no_contada():
    detalles = [_detalle(PRODUCTO_1, Decimal("5"), None)]
    contados, items, cant_abs, lineas = _clasificar_lineas_aprobacion(detalles)
    assert contados == 0
    assert items == 0
    assert lineas == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cp01_aprobar_sin_diferencias_rechazado_f2():
    """CP-01 / F2: finalizado + dif. 0 → 422, sin inv_movimiento."""
    token = _set_empresa_ctx(EMPRESA_ID)
    inv = _base_inv(estado="finalizado")
    detalles = [
        _detalle(PRODUCTO_1, Decimal("10"), Decimal("10")),
        _detalle(PRODUCTO_2, Decimal("3"), Decimal("3")),
    ]
    mock_uow = _make_uow(inv, detalles)

    patches = _common_patches(mock_uow)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5] as mock_procesar:
        with pytest.raises(HTTPException) as exc:
            await inventario_fisico_aprobacion_service.aprobar_inventario_fisico_servicio(
                client_id=CLIENT_ID,
                inventario_fisico_id=INVENTARIO_ID,
                tipo_movimiento_id=TIPO_MOVIMIENTO_ID,
            )

    assert exc.value.status_code == 422
    assert "finalizar" in exc.value.detail.lower()
    assert _count_inserts(mock_uow, InvMovimientoTable) == 0
    mock_procesar.assert_not_called()
    reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cp02_aprobar_con_diferencias_flujo_completo():
    """CP-02: diferencias > 0 → movimiento, detalle, procesar, ajustado."""
    token = _set_empresa_ctx(EMPRESA_ID)
    inv = _base_inv(estado="finalizado")
    detalles = [
        _detalle(PRODUCTO_1, Decimal("10"), Decimal("12")),
        _detalle(PRODUCTO_2, Decimal("4"), Decimal("1")),
    ]
    closed = {
        **inv,
        "estado": "ajustado",
        "movimiento_ajuste_id": MOVIMIENTO_AJUSTE_ID,
    }
    mock_uow = _make_uow(inv, detalles, closed)

    patches = _common_patches(mock_uow)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5] as mock_procesar:
        result = await inventario_fisico_aprobacion_service.aprobar_inventario_fisico_servicio(
            client_id=CLIENT_ID,
            inventario_fisico_id=INVENTARIO_ID,
            tipo_movimiento_id=TIPO_MOVIMIENTO_ID,
        )

    assert result["estado"] == "ajustado"
    assert _count_inserts(mock_uow, InvMovimientoTable) == 1
    assert _count_inserts(mock_uow, InvMovimientoDetalleTable) == 2
    mock_procesar.assert_called_once()
    reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cp03_reaprobar_finalizado_sin_diferencias_rechazado_f2():
    """CP-03 / F2: inventario finalizado + dif. 0 → 422, sin movimiento."""
    token = _set_empresa_ctx(EMPRESA_ID)
    inv = _base_inv(estado="finalizado")
    detalles = [_detalle(PRODUCTO_1, Decimal("7"), Decimal("7"))]
    mock_uow = _make_uow(inv, detalles)

    patches = _common_patches(mock_uow)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5] as mock_procesar:
        with pytest.raises(HTTPException) as exc:
            await inventario_fisico_aprobacion_service.aprobar_inventario_fisico_servicio(
                client_id=CLIENT_ID,
                inventario_fisico_id=INVENTARIO_ID,
                tipo_movimiento_id=TIPO_MOVIMIENTO_ID,
            )

    assert exc.value.status_code == 422
    assert _count_inserts(mock_uow, InvMovimientoTable) == 0
    mock_procesar.assert_not_called()
    reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f1_aprobar_desde_en_proceso_rechazado_422():
    """F1: en_proceso + dif. > 0 → 422 antes de crear movimiento."""
    token = _set_empresa_ctx(EMPRESA_ID)
    inv = _base_inv(estado="en_proceso")
    detalles = [_detalle(PRODUCTO_1, Decimal("1"), Decimal("5"))]
    mock_uow = _make_uow(inv, detalles)

    patches = _common_patches(mock_uow)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5] as mock_procesar:
        with pytest.raises(HTTPException) as exc:
            await inventario_fisico_aprobacion_service.aprobar_inventario_fisico_servicio(
                client_id=CLIENT_ID,
                inventario_fisico_id=INVENTARIO_ID,
                tipo_movimiento_id=TIPO_MOVIMIENTO_ID,
            )

    assert exc.value.status_code == 422
    assert "finalizar" in exc.value.detail.lower()
    assert _count_inserts(mock_uow, InvMovimientoTable) == 0
    mock_procesar.assert_not_called()
    reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cp04_aprobar_inventario_ajustado_idempotente():
    """CP-04: inventario ajustado → retorno temprano, sin mutaciones."""
    token = _set_empresa_ctx(EMPRESA_ID)
    inv = _base_inv(estado="ajustado")
    inv["movimiento_ajuste_id"] = MOVIMIENTO_AJUSTE_ID
    mock_uow = AsyncMock()
    mock_uow.execute = AsyncMock(return_value=[inv])

    patches = _common_patches(mock_uow)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5] as mock_procesar:
        result = await inventario_fisico_aprobacion_service.aprobar_inventario_fisico_servicio(
            client_id=CLIENT_ID,
            inventario_fisico_id=INVENTARIO_ID,
            tipo_movimiento_id=TIPO_MOVIMIENTO_ID,
        )

    assert result["estado"] == "ajustado"
    assert mock_uow.execute.call_count == 1
    mock_procesar.assert_not_called()
    reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cp05_aprobar_finalizado_con_diferencias_genera_ajuste():
    """CP-05: finalizado + dif. > 0 → ajustado con movimiento."""
    token = _set_empresa_ctx(EMPRESA_ID)
    inv = _base_inv(estado="finalizado")
    detalles = [_detalle(PRODUCTO_1, Decimal("2"), Decimal("5"))]
    closed = {**inv, "estado": "ajustado", "movimiento_ajuste_id": MOVIMIENTO_AJUSTE_ID}
    mock_uow = _make_uow(inv, detalles, closed)

    patches = _common_patches(mock_uow)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5] as mock_procesar:
        result = await inventario_fisico_aprobacion_service.aprobar_inventario_fisico_servicio(
            client_id=CLIENT_ID,
            inventario_fisico_id=INVENTARIO_ID,
            tipo_movimiento_id=TIPO_MOVIMIENTO_ID,
        )

    assert result["estado"] == "ajustado"
    assert _count_inserts(mock_uow, InvMovimientoTable) == 1
    assert _count_inserts(mock_uow, InvMovimientoDetalleTable) == 1
    mock_procesar.assert_called_once()
    reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cp06_aprobar_sin_detalle_inventario_422():
    """CP-06: cabecera finalizada sin líneas → 422, sin movimiento."""
    token = _set_empresa_ctx(EMPRESA_ID)
    inv = _base_inv(estado="finalizado")
    mock_uow = AsyncMock()
    call_count = {"n": 0}

    async def execute(query, *args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return [inv]
        return []

    mock_uow.execute = AsyncMock(side_effect=execute)

    patches = _common_patches(mock_uow)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5] as mock_procesar:
        with pytest.raises(HTTPException) as exc:
            await inventario_fisico_aprobacion_service.aprobar_inventario_fisico_servicio(
                client_id=CLIENT_ID,
                inventario_fisico_id=INVENTARIO_ID,
                tipo_movimiento_id=TIPO_MOVIMIENTO_ID,
            )

    assert exc.value.status_code == 422
    assert _count_inserts(mock_uow, InvMovimientoTable) == 0
    mock_procesar.assert_not_called()
    reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cp07_producto_invalido_con_diferencias_not_found():
    """CP-07: dif. > 0 pero producto inexistente → NotFoundError, sin procesar."""
    token = _set_empresa_ctx(EMPRESA_ID)
    inv = _base_inv(estado="finalizado")
    detalles = [_detalle(PRODUCTO_1, Decimal("1"), Decimal("3"))]
    mock_uow = _make_uow(inv, detalles)

    patches = _common_patches(mock_uow)
    with patches[0], patches[1], patches[2], patches[3], patch(
        "app.modules.inv.application.services.inventario_fisico_aprobacion_service.get_producto_by_id",
        new=AsyncMock(return_value=None),
    ), patches[5] as mock_procesar:
        with pytest.raises(NotFoundError):
            await inventario_fisico_aprobacion_service.aprobar_inventario_fisico_servicio(
                client_id=CLIENT_ID,
                inventario_fisico_id=INVENTARIO_ID,
                tipo_movimiento_id=TIPO_MOVIMIENTO_ID,
            )

    mock_procesar.assert_not_called()
    assert _count_inserts(mock_uow, InvMovimientoDetalleTable) == 0
    reset_current_empresa_id(token)
