"""
Tests unitarios — INV-P0-006: helpers (T-01 a T-07) y CREATE movimiento (T-10, T-12).
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import ConflictError, ValidationError
from app.core.tenant.empresa_context import reset_current_empresa_id, set_current_empresa_id
from app.modules.inv.application.services import (
    inventario_fisico_service,
    movimiento_proceso_service,
    movimiento_service,
)
from app.modules.inv.application.services.inv_workflow_enforcement import (
    MOVIMIENTO_WORKFLOW_READONLY_UPDATE,
    is_phantom_procesado,
    reject_inventario_fisico_workflow_in_update,
    reject_movimiento_workflow_in_update,
    sanitize_inventario_fisico_create_payload,
    sanitize_movimiento_create_payload,
)
from app.modules.inv.presentation.schemas import (
    InventarioFisicoConDetalleUpdate,
    InventarioFisicoCreate,
    InventarioFisicoUpdate,
    MovimientoConDetalleCreate,
    MovimientoConDetalleUpdate,
    MovimientoCreate,
    MovimientoDetalleCreateEmbebido,
    MovimientoUpdate,
)

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
USUARIO_ID = uuid4()
TIPO_MOVIMIENTO_ID = uuid4()
PRODUCTO_ID = uuid4()
UNIDAD_MEDIDA_ID = uuid4()
MONEDA_ID = uuid4()
ALMACEN_ID = uuid4()
INVENTARIO_FISICO_ID = uuid4()


class _FakeUowContext:
    def __init__(self, uow):
        self._uow = uow

    async def __aenter__(self):
        return self._uow

    async def __aexit__(self, *args):
        return False


def _movimiento_row_borrador(*, movimiento_id) -> dict:
    ahora = datetime.utcnow()
    return {
        "movimiento_id": movimiento_id,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "numero_movimiento": "MOV-WF-001",
        "tipo_movimiento_id": TIPO_MOVIMIENTO_ID,
        "fecha_movimiento": ahora,
        "fecha_contable": date(2026, 6, 12),
        "estado": "borrador",
        "moneda_id": MONEDA_ID,
        "total_items": 1,
        "total_cantidad": Decimal("5"),
        "total_costo": Decimal("50"),
    }


@pytest.mark.unit
def test_t01_sanitize_movimiento_create_fuerza_borrador():
    payload = {"estado": "procesado", "numero_movimiento": "MOV-001"}
    result = sanitize_movimiento_create_payload(payload)
    assert result["estado"] == "borrador"
    assert payload["estado"] == "procesado"


@pytest.mark.unit
def test_t02_sanitize_movimiento_create_elimina_campos_proceso():
    ahora = datetime.utcnow()
    payload = {
        "estado": "autorizado",
        "autorizado_por_usuario_id": USUARIO_ID,
        "fecha_autorizacion": ahora,
        "usuario_procesado_id": USUARIO_ID,
        "fecha_procesado": ahora,
        "motivo_anulacion": "test",
        "numero_movimiento": "MOV-002",
    }
    result = sanitize_movimiento_create_payload(payload)
    assert result["estado"] == "borrador"
    assert "autorizado_por_usuario_id" not in result
    assert "fecha_autorizacion" not in result
    assert "usuario_procesado_id" not in result
    assert "fecha_procesado" not in result
    assert "motivo_anulacion" not in result
    assert result["numero_movimiento"] == "MOV-002"


@pytest.mark.unit
def test_t03_reject_movimiento_workflow_in_update_rechaza_estado():
    with pytest.raises(ValidationError) as exc_info:
        reject_movimiento_workflow_in_update({"estado": "procesado"})
    assert "estado" in exc_info.value.detail.lower()


@pytest.mark.unit
def test_t04_is_phantom_procesado_true_sin_fecha_procesado():
    mov = {
        "estado": "procesado",
        "usuario_procesado_id": USUARIO_ID,
        "fecha_procesado": None,
    }
    assert is_phantom_procesado(mov) is True


@pytest.mark.unit
def test_t05_is_phantom_procesado_false_con_fecha_y_usuario():
    mov = {
        "estado": "procesado",
        "usuario_procesado_id": USUARIO_ID,
        "fecha_procesado": datetime.utcnow(),
    }
    assert is_phantom_procesado(mov) is False


@pytest.mark.unit
def test_t06_sanitize_inventario_fisico_create_fuerza_en_proceso():
    payload = {"estado": "ajustado", "numero_inventario": "IF-001"}
    result = sanitize_inventario_fisico_create_payload(payload)
    assert result["estado"] == "en_proceso"
    assert payload["estado"] == "ajustado"


@pytest.mark.unit
def test_t07_reject_inventario_fisico_workflow_in_update_rechaza_movimiento_ajuste_id():
    with pytest.raises(ValidationError) as exc_info:
        reject_inventario_fisico_workflow_in_update(
            {"movimiento_ajuste_id": uuid4()}
        )
    assert "movimiento_ajuste_id" in exc_info.value.detail


@pytest.mark.unit
@pytest.mark.asyncio
async def test_t10_create_movimiento_servicio_fuerza_borrador():
    """MovimientoCreate(estado=procesado) → persist y Read con estado=borrador."""
    token = set_current_empresa_id(EMPRESA_ID)
    movimiento_id = uuid4()
    ahora = datetime.utcnow()
    data = MovimientoCreate(
        empresa_id=EMPRESA_ID,
        numero_movimiento="MOV-WF-001",
        tipo_movimiento_id=TIPO_MOVIMIENTO_ID,
        fecha_contable=date(2026, 6, 12),
        estado="procesado",
        usuario_procesado_id=USUARIO_ID,
        fecha_procesado=ahora,
        autorizado_por_usuario_id=USUARIO_ID,
        fecha_autorizacion=ahora,
    )

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_service.ensure_empresa_in_tenant",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_service._validate_movimiento_cabecera_refs",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_service._resolve_moneda_id",
            new=AsyncMock(return_value=MONEDA_ID),
        ), patch(
            "app.modules.inv.application.services.movimiento_service.create_movimiento",
            new=AsyncMock(return_value=_movimiento_row_borrador(movimiento_id=movimiento_id)),
        ) as mock_create:
            result = await movimiento_service.create_movimiento_servicio(
                client_id=CLIENT_ID,
                data=data,
            )

        assert result.estado == "borrador"
        persist_payload = mock_create.await_args.kwargs["data"]
        assert persist_payload["estado"] == "borrador"
        assert "usuario_procesado_id" not in persist_payload
        assert "fecha_procesado" not in persist_payload
        assert "autorizado_por_usuario_id" not in persist_payload
        assert "fecha_autorizacion" not in persist_payload
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_t12_create_movimiento_con_detalles_servicio_fuerza_borrador():
    """create_movimiento_con_detalles_servicio con estado forjado → borrador."""
    token = set_current_empresa_id(EMPRESA_ID)
    movimiento_id = uuid4()
    ahora = datetime.utcnow()
    detalle = MovimientoDetalleCreateEmbebido(
        producto_id=PRODUCTO_ID,
        cantidad=Decimal("5"),
        unidad_medida_id=UNIDAD_MEDIDA_ID,
        cantidad_base=Decimal("5"),
        costo_unitario=Decimal("10"),
    )
    data = MovimientoConDetalleCreate(
        empresa_id=EMPRESA_ID,
        numero_movimiento="MOV-WF-002",
        tipo_movimiento_id=TIPO_MOVIMIENTO_ID,
        fecha_contable=date(2026, 6, 12),
        estado="autorizado",
        usuario_procesado_id=USUARIO_ID,
        fecha_procesado=ahora,
        detalles=[detalle],
    )
    cab_row = _movimiento_row_borrador(movimiento_id=movimiento_id)
    cab_row["numero_movimiento"] = "MOV-WF-002"
    det_row = {
        "movimiento_detalle_id": uuid4(),
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "movimiento_id": movimiento_id,
        "producto_id": PRODUCTO_ID,
        "cantidad": Decimal("5"),
        "unidad_medida_id": UNIDAD_MEDIDA_ID,
        "cantidad_base": Decimal("5"),
        "costo_unitario": Decimal("10"),
        "moneda_id": MONEDA_ID,
        "moneda": "PEN",
    }
    inserted_cabecera: dict = {}

    def _extract_insert_values(stmt) -> dict:
        return {
            key: (param.value if hasattr(param, "value") else param)
            for key, param in stmt._values.items()
        }

    async def _fake_execute(stmt):
        if (
            not inserted_cabecera
            and hasattr(stmt, "table")
            and stmt.table.name == "inv_movimiento"
        ):
            inserted_cabecera.update(_extract_insert_values(stmt))
            return {"rows_affected": 1}
        if hasattr(stmt, "table") and stmt.table.name == "inv_movimiento_detalle":
            return {"rows_affected": 1}
        compiled = str(stmt)
        if "inv_movimiento" in compiled and "inv_movimiento_detalle" not in compiled:
            return [cab_row]
        return [det_row]

    mock_uow = AsyncMock()
    mock_uow.execute = AsyncMock(side_effect=_fake_execute)

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_service.ensure_empresa_in_tenant",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_service._validate_movimiento_cabecera_refs",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_service._validate_detalle_embebido_line",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_service._resolve_moneda_id",
            new=AsyncMock(return_value=MONEDA_ID),
        ), patch(
            "app.modules.inv.application.services.movimiento_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ):
            result = await movimiento_service.create_movimiento_con_detalles_servicio(
                client_id=CLIENT_ID,
                data=data,
            )

        assert result.estado == "borrador"
        assert inserted_cabecera["estado"] == "borrador"
        assert "usuario_procesado_id" not in inserted_cabecera
        assert "fecha_procesado" not in inserted_cabecera
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_t11_update_movimiento_servicio_rechaza_estado_procesado():
    """PUT con estado=procesado → ValidationError; no persiste."""
    token = set_current_empresa_id(EMPRESA_ID)
    movimiento_id = uuid4()
    row = _movimiento_row_borrador(movimiento_id=movimiento_id)

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_service.get_movimiento_by_id",
            new=AsyncMock(return_value=row),
        ), patch(
            "app.modules.inv.application.services.movimiento_service.update_movimiento",
            new=AsyncMock(),
        ) as mock_update:
            with pytest.raises(ValidationError) as exc_info:
                await movimiento_service.update_movimiento_servicio(
                    client_id=CLIENT_ID,
                    movimiento_id=movimiento_id,
                    data=MovimientoUpdate(estado="procesado"),
                )

        assert "estado" in exc_info.value.detail.lower()
        assert exc_info.value.status_code == 400
        mock_update.assert_not_called()
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.parametrize(
    "campo,valor",
    [
        ("estado", "autorizado"),
        ("autorizado_por_usuario_id", USUARIO_ID),
        ("fecha_autorizacion", datetime.utcnow()),
        ("motivo_anulacion", "anulacion forjada"),
    ],
)
@pytest.mark.asyncio
async def test_update_movimiento_servicio_rechaza_campo_workflow(campo, valor):
    """Campos §6.1 expuestos en MovimientoUpdate → ValidationError en servicio."""
    token = set_current_empresa_id(EMPRESA_ID)
    movimiento_id = uuid4()
    row = _movimiento_row_borrador(movimiento_id=movimiento_id)

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_service.get_movimiento_by_id",
            new=AsyncMock(return_value=row),
        ), patch(
            "app.modules.inv.application.services.movimiento_service.update_movimiento",
            new=AsyncMock(),
        ) as mock_update:
            with pytest.raises(ValidationError) as exc_info:
                await movimiento_service.update_movimiento_servicio(
                    client_id=CLIENT_ID,
                    movimiento_id=movimiento_id,
                    data=MovimientoUpdate(**{campo: valor}),
                )

        assert campo in exc_info.value.detail or "estado" in exc_info.value.detail.lower()
        mock_update.assert_not_called()
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.parametrize(
    "campo,valor",
    [
        ("estado", "procesado"),
        ("autorizado_por_usuario_id", USUARIO_ID),
        ("fecha_autorizacion", datetime.utcnow()),
        ("usuario_procesado_id", USUARIO_ID),
        ("fecha_procesado", datetime.utcnow()),
        ("motivo_anulacion", "anulacion forjada"),
    ],
)
def test_reject_movimiento_workflow_in_update_rechaza_campos_6_1(campo, valor):
    """Cada campo §6.1 en payload UPDATE → ValidationError (helper)."""
    with pytest.raises(ValidationError) as exc_info:
        reject_movimiento_workflow_in_update({campo: valor})
    assert campo in exc_info.value.detail or "estado" in exc_info.value.detail.lower()


@pytest.mark.unit
def test_movimiento_workflow_readonly_update_incluye_campos_6_1():
    assert MOVIMIENTO_WORKFLOW_READONLY_UPDATE == frozenset(
        {
            "estado",
            "autorizado_por_usuario_id",
            "fecha_autorizacion",
            "usuario_procesado_id",
            "fecha_procesado",
            "motivo_anulacion",
        }
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_movimiento_con_detalles_servicio_rechaza_estado():
    """PUT con-detalle con estado en body → ValidationError."""
    token = set_current_empresa_id(EMPRESA_ID)
    movimiento_id = uuid4()
    row = _movimiento_row_borrador(movimiento_id=movimiento_id)

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_service.get_movimiento_by_id",
            new=AsyncMock(return_value=row),
        ), patch(
            "app.modules.inv.application.services.movimiento_service.unit_of_work",
            return_value=_FakeUowContext(AsyncMock()),
        ):
            with pytest.raises(ValidationError):
                await movimiento_service.update_movimiento_con_detalles_servicio(
                    client_id=CLIENT_ID,
                    movimiento_id=movimiento_id,
                    data=MovimientoConDetalleUpdate(estado="procesado"),
                )
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_movimiento_servicio_sin_campos_workflow_ok():
    """PUT sin campos de workflow → actualización normal."""
    token = set_current_empresa_id(EMPRESA_ID)
    movimiento_id = uuid4()
    row = _movimiento_row_borrador(movimiento_id=movimiento_id)
    updated_row = {**row, "observaciones": "nota actualizada"}

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_service.get_movimiento_by_id",
            new=AsyncMock(return_value=row),
        ), patch(
            "app.modules.inv.application.services.movimiento_service._validate_movimiento_cabecera_refs",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_service.update_movimiento",
            new=AsyncMock(return_value=updated_row),
        ) as mock_update:
            result = await movimiento_service.update_movimiento_servicio(
                client_id=CLIENT_ID,
                movimiento_id=movimiento_id,
                data=MovimientoUpdate(observaciones="nota actualizada"),
            )

        assert result.observaciones == "nota actualizada"
        mock_update.assert_called_once()
        persist_payload = mock_update.await_args.kwargs["data"]
        assert "estado" not in persist_payload
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_t13_procesar_movimiento_phantom_procesado_conflict_sin_stock():
    """Caso A: phantom procesado → ConflictError; una sola lectura, sin mutar stock."""
    token = set_current_empresa_id(EMPRESA_ID)
    movimiento_id = uuid4()
    phantom = {
        "movimiento_id": movimiento_id,
        "empresa_id": EMPRESA_ID,
        "estado": "procesado",
        "fecha_procesado": None,
        "usuario_procesado_id": None,
    }
    mock_uow = AsyncMock()
    mock_uow.execute = AsyncMock(return_value=[phantom])

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ):
            with pytest.raises(ConflictError) as exc_info:
                await movimiento_proceso_service.procesar_movimiento_servicio(
                    client_id=CLIENT_ID,
                    movimiento_id=movimiento_id,
                )

        assert exc_info.value.status_code == 409
        assert mock_uow.execute.call_count == 1
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_t14_procesar_movimiento_legitimo_procesado_idempotente():
    """Caso B: procesado legítimo → return OK sin reprocesar."""
    token = set_current_empresa_id(EMPRESA_ID)
    movimiento_id = uuid4()
    ahora = datetime.utcnow()
    legitimo = {
        "movimiento_id": movimiento_id,
        "empresa_id": EMPRESA_ID,
        "estado": "procesado",
        "fecha_procesado": ahora,
        "usuario_procesado_id": USUARIO_ID,
    }
    mock_uow = AsyncMock()
    mock_uow.execute = AsyncMock(return_value=[legitimo])

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ):
            result = await movimiento_proceso_service.procesar_movimiento_servicio(
                client_id=CLIENT_ID,
                movimiento_id=movimiento_id,
            )

        assert result == legitimo
        assert mock_uow.execute.call_count == 1
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_t15_autorizar_movimiento_phantom_autorizado_conflict():
    """Caso C: phantom autorizado → ConflictError; no actualiza."""
    token = set_current_empresa_id(EMPRESA_ID)
    movimiento_id = uuid4()
    phantom = {
        "movimiento_id": movimiento_id,
        "empresa_id": EMPRESA_ID,
        "estado": "autorizado",
        "fecha_autorizacion": None,
        "autorizado_por_usuario_id": None,
    }

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service.get_movimiento_by_id",
            new=AsyncMock(return_value=phantom),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.update_movimiento",
            new=AsyncMock(),
        ) as mock_update:
            with pytest.raises(ConflictError) as exc_info:
                await movimiento_proceso_service.autorizar_movimiento_servicio(
                    client_id=CLIENT_ID,
                    movimiento_id=movimiento_id,
                )

        assert exc_info.value.status_code == 409
        mock_update.assert_not_called()
    finally:
        reset_current_empresa_id(token)


def _inventario_fisico_row_en_proceso(*, inventario_fisico_id) -> dict:
    return {
        "inventario_fisico_id": inventario_fisico_id,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "numero_inventario": "INV-WF-001",
        "fecha_inventario": date(2026, 6, 12),
        "almacen_id": ALMACEN_ID,
        "tipo_inventario": "total",
        "estado": "en_proceso",
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_t16_create_inventario_fisico_servicio_fuerza_en_proceso():
    """InventarioFisicoCreate(estado=ajustado) → persist y Read con en_proceso."""
    token = set_current_empresa_id(EMPRESA_ID)
    inventario_id = uuid4()
    ahora = datetime.utcnow()
    data = InventarioFisicoCreate(
        empresa_id=EMPRESA_ID,
        numero_inventario="INV-WF-001",
        fecha_inventario=date(2026, 6, 12),
        almacen_id=ALMACEN_ID,
        tipo_inventario="total",
        estado="ajustado",
        movimiento_ajuste_id=uuid4(),
        fecha_finalizacion=ahora,
        fecha_ajuste=ahora,
        total_productos_contados=99,
        total_diferencias=5,
        valor_diferencias=Decimal("100"),
    )

    try:
        with patch(
            "app.modules.inv.application.services.inventario_fisico_service.ensure_empresa_in_tenant",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.inventario_fisico_service._validate_cabecera_refs",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.inventario_fisico_service.create_inventario_fisico",
            new=AsyncMock(
                return_value=_inventario_fisico_row_en_proceso(
                    inventario_fisico_id=inventario_id
                )
            ),
        ) as mock_create:
            result = await inventario_fisico_service.create_inventario_fisico_servicio(
                client_id=CLIENT_ID,
                data=data,
            )

        assert result.estado == "en_proceso"
        persist_payload = mock_create.await_args.kwargs["data"]
        assert persist_payload["estado"] == "en_proceso"
        assert "movimiento_ajuste_id" not in persist_payload
        assert "fecha_finalizacion" not in persist_payload
        assert "fecha_ajuste" not in persist_payload
        assert "total_productos_contados" not in persist_payload
        assert "total_diferencias" not in persist_payload
        assert "valor_diferencias" not in persist_payload
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_t17_update_inventario_fisico_servicio_rechaza_estado_finalizado():
    """PUT con estado=finalizado → ValidationError; no persiste."""
    token = set_current_empresa_id(EMPRESA_ID)
    row = _inventario_fisico_row_en_proceso(inventario_fisico_id=INVENTARIO_FISICO_ID)

    try:
        with patch(
            "app.modules.inv.application.services.inventario_fisico_service.get_inventario_fisico_by_id",
            new=AsyncMock(return_value=row),
        ), patch(
            "app.modules.inv.application.services.inventario_fisico_service.update_inventario_fisico",
            new=AsyncMock(),
        ) as mock_update:
            with pytest.raises(ValidationError) as exc_info:
                await inventario_fisico_service.update_inventario_fisico_servicio(
                    client_id=CLIENT_ID,
                    inventario_fisico_id=INVENTARIO_FISICO_ID,
                    data=InventarioFisicoUpdate(estado="finalizado"),
                )

        assert "estado" in exc_info.value.detail.lower()
        mock_update.assert_not_called()
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_t18_update_inventario_fisico_con_detalles_rechaza_movimiento_ajuste_id():
    """PUT con-detalle con movimiento_ajuste_id → ValidationError."""
    token = set_current_empresa_id(EMPRESA_ID)
    row = _inventario_fisico_row_en_proceso(inventario_fisico_id=INVENTARIO_FISICO_ID)

    try:
        with patch(
            "app.modules.inv.application.services.inventario_fisico_service.get_inventario_fisico_by_id",
            new=AsyncMock(return_value=row),
        ), patch(
            "app.modules.inv.application.services.inventario_fisico_service.unit_of_work",
            return_value=_FakeUowContext(AsyncMock()),
        ):
            with pytest.raises(ValidationError) as exc_info:
                await inventario_fisico_service.update_inventario_fisico_con_detalles_servicio(
                    client_id=CLIENT_ID,
                    inventario_fisico_id=INVENTARIO_FISICO_ID,
                    data=InventarioFisicoConDetalleUpdate(
                        movimiento_ajuste_id=uuid4()
                    ),
                )

        assert "movimiento_ajuste_id" in exc_info.value.detail
    finally:
        reset_current_empresa_id(token)


def _inventario_fisico_row_en_proceso(*, inventario_fisico_id) -> dict:
    return {
        "inventario_fisico_id": inventario_fisico_id,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "numero_inventario": "INV-WF-001",
        "fecha_inventario": date(2026, 6, 12),
        "almacen_id": ALMACEN_ID,
        "tipo_inventario": "total",
        "estado": "en_proceso",
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_t16_create_inventario_fisico_servicio_fuerza_en_proceso():
    """InventarioFisicoCreate(estado=ajustado) → persist y Read con en_proceso."""
    token = set_current_empresa_id(EMPRESA_ID)
    inventario_id = uuid4()
    ahora = datetime.utcnow()
    data = InventarioFisicoCreate(
        empresa_id=EMPRESA_ID,
        numero_inventario="INV-WF-001",
        fecha_inventario=date(2026, 6, 12),
        almacen_id=ALMACEN_ID,
        tipo_inventario="total",
        estado="ajustado",
        movimiento_ajuste_id=uuid4(),
        fecha_finalizacion=ahora,
        fecha_ajuste=ahora,
        total_productos_contados=99,
        total_diferencias=5,
        valor_diferencias=Decimal("100"),
    )

    try:
        with patch(
            "app.modules.inv.application.services.inventario_fisico_service.ensure_empresa_in_tenant",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.inventario_fisico_service._validate_cabecera_refs",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.inventario_fisico_service.create_inventario_fisico",
            new=AsyncMock(
                return_value=_inventario_fisico_row_en_proceso(
                    inventario_fisico_id=inventario_id
                )
            ),
        ) as mock_create:
            result = await inventario_fisico_service.create_inventario_fisico_servicio(
                client_id=CLIENT_ID,
                data=data,
            )

        assert result.estado == "en_proceso"
        persist_payload = mock_create.await_args.kwargs["data"]
        assert persist_payload["estado"] == "en_proceso"
        assert "movimiento_ajuste_id" not in persist_payload
        assert "fecha_finalizacion" not in persist_payload
        assert "fecha_ajuste" not in persist_payload
        assert "total_productos_contados" not in persist_payload
        assert "total_diferencias" not in persist_payload
        assert "valor_diferencias" not in persist_payload
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_t17_update_inventario_fisico_servicio_rechaza_estado_finalizado():
    """PUT con estado=finalizado → ValidationError; no persiste."""
    token = set_current_empresa_id(EMPRESA_ID)
    row = _inventario_fisico_row_en_proceso(inventario_fisico_id=INVENTARIO_FISICO_ID)

    try:
        with patch(
            "app.modules.inv.application.services.inventario_fisico_service.get_inventario_fisico_by_id",
            new=AsyncMock(return_value=row),
        ), patch(
            "app.modules.inv.application.services.inventario_fisico_service.update_inventario_fisico",
            new=AsyncMock(),
        ) as mock_update:
            with pytest.raises(ValidationError) as exc_info:
                await inventario_fisico_service.update_inventario_fisico_servicio(
                    client_id=CLIENT_ID,
                    inventario_fisico_id=INVENTARIO_FISICO_ID,
                    data=InventarioFisicoUpdate(estado="finalizado"),
                )

        assert "estado" in exc_info.value.detail.lower()
        mock_update.assert_not_called()
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_t18_update_inventario_fisico_con_detalles_rechaza_movimiento_ajuste_id():
    """PUT con-detalle con movimiento_ajuste_id → ValidationError."""
    token = set_current_empresa_id(EMPRESA_ID)
    row = _inventario_fisico_row_en_proceso(inventario_fisico_id=INVENTARIO_FISICO_ID)

    try:
        with patch(
            "app.modules.inv.application.services.inventario_fisico_service.get_inventario_fisico_by_id",
            new=AsyncMock(return_value=row),
        ), patch(
            "app.modules.inv.application.services.inventario_fisico_service.unit_of_work",
            return_value=_FakeUowContext(AsyncMock()),
        ):
            with pytest.raises(ValidationError) as exc_info:
                await inventario_fisico_service.update_inventario_fisico_con_detalles_servicio(
                    client_id=CLIENT_ID,
                    inventario_fisico_id=INVENTARIO_FISICO_ID,
                    data=InventarioFisicoConDetalleUpdate(
                        movimiento_ajuste_id=uuid4()
                    ),
                )

        assert "movimiento_ajuste_id" in exc_info.value.detail
    finally:
        reset_current_empresa_id(token)
