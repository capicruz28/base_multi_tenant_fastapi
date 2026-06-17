"""
Tests unitarios — INV-P0-003: Etapa 1 (builders/gates) + Etapa 2 (guards estornado).
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.core.exceptions import ConflictError
from app.core.tenant.empresa_context import reset_current_empresa_id, set_current_empresa_id
from app.modules.inv.application.services import inv_estorno_proceso as estorno
from app.modules.inv.application.services import movimiento_proceso_service

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
USUARIO_ID = uuid4()
MOVIMIENTO_ID = uuid4()
TIPO_MOVIMIENTO_ID = uuid4()
PRODUCTO_ID = uuid4()
UNIDAD_MEDIDA_ID = uuid4()
MONEDA_ID = uuid4()
ALMACEN_A = uuid4()
ALMACEN_B = uuid4()
ALMACEN_D = uuid4()
ALMACEN_O = uuid4()
ALMACEN_T = uuid4()


class _FakeUowContext:
    def __init__(self, uow):
        self._uow = uow

    async def __aenter__(self):
        return self._uow

    async def __aexit__(self, *args):
        return False


def _detalle(*, cantidad_base: Decimal, costo_unitario: Decimal = Decimal("5")) -> dict:
    return {
        "movimiento_detalle_id": uuid4(),
        "producto_id": PRODUCTO_ID,
        "cantidad": cantidad_base,
        "unidad_medida_id": UNIDAD_MEDIDA_ID,
        "cantidad_base": cantidad_base,
        "costo_unitario": costo_unitario,
        "moneda_id": MONEDA_ID,
        "moneda": "PEN",
    }


def _movimiento_base(**kwargs) -> dict:
    base = {
        "movimiento_id": MOVIMIENTO_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "numero_movimiento": "MOV-001",
        "tipo_movimiento_id": TIPO_MOVIMIENTO_ID,
        "fecha_contable": date(2026, 6, 12),
        "moneda_id": MONEDA_ID,
        "estado": "procesado",
        "requiere_autorizacion": False,
    }
    base.update(kwargs)
    return base


@pytest.mark.unit
def test_e05_espejo_entrada_cantidad_base_negada():
    detalles = estorno.build_compensatorio_detalles(
        [_detalle(cantidad_base=Decimal("10"))],
        "entrada",
    )
    assert len(detalles) == 1
    assert detalles[0]["cantidad_base"] == Decimal("-10")
    assert detalles[0]["costo_unitario"] == Decimal("5")


@pytest.mark.unit
def test_e06_espejo_salida_cantidad_base_negada():
    detalles = estorno.build_compensatorio_detalles(
        [_detalle(cantidad_base=Decimal("5"))],
        "salida",
    )
    assert detalles[0]["cantidad_base"] == Decimal("-5")


@pytest.mark.unit
def test_e07_espejo_transferencia_swap_almacenes_y_qty_positiva():
    original = _movimiento_base(
        almacen_origen_id=ALMACEN_A,
        almacen_destino_id=ALMACEN_B,
    )
    detalles = estorno.build_compensatorio_detalles(
        [_detalle(cantidad_base=Decimal("5"))],
        "transferencia",
    )
    assert detalles[0]["cantidad_base"] == Decimal("5")

    origen, destino = estorno.build_compensatorio_almacenes(original, "transferencia")
    assert origen == ALMACEN_B
    assert destino == ALMACEN_A


@pytest.mark.unit
def test_e08_espejo_ajuste_invierte_signo():
    det_pos = estorno.build_compensatorio_detalles(
        [_detalle(cantidad_base=Decimal("3"))],
        "ajuste",
    )
    assert det_pos[0]["cantidad_base"] == Decimal("-3")

    det_neg = estorno.build_compensatorio_detalles(
        [_detalle(cantidad_base=Decimal("-3"))],
        "ajuste",
    )
    assert det_neg[0]["cantidad_base"] == Decimal("3")

    original = _movimiento_base(almacen_destino_id=ALMACEN_T)
    origen, destino = estorno.build_compensatorio_almacenes(original, "ajuste")
    assert origen is None
    assert destino == ALMACEN_T


@pytest.mark.unit
@pytest.mark.asyncio
async def test_e08b_x08_entrada_ac1_reversion_total_lanza_conflict():
    mov = _movimiento_base(almacen_destino_id=ALMACEN_D)
    tipo = {"clase_movimiento": "entrada", "afecta_costo": True}
    detalles = [_detalle(cantidad_base=Decimal("10"))]

    with patch(
        "app.modules.inv.application.services.inv_estorno_proceso.get_stock_by_producto_almacen",
        new=AsyncMock(
            return_value={
                "cantidad_actual": Decimal("10"),
                "costo_promedio": Decimal("5"),
            }
        ),
    ):
        with pytest.raises(ConflictError) as exc_info:
            await estorno.assert_entrada_espejo_ppm_viable(
                client_id=CLIENT_ID,
                empresa_id=EMPRESA_ID,
                tipo_movimiento=tipo,
                movimiento=mov,
                detalles=detalles,
            )
    assert exc_info.value.internal_code == estorno.ESTORNO_ENTRADA_PPM_QNEW_CERO_CODE
    assert exc_info.value.status_code == 409


@pytest.mark.unit
@pytest.mark.asyncio
async def test_x08_no_lanza_si_stock_residual():
    mov = _movimiento_base(almacen_destino_id=ALMACEN_D)
    tipo = {"clase_movimiento": "entrada", "afecta_costo": True}
    detalles = [_detalle(cantidad_base=Decimal("10"))]

    with patch(
        "app.modules.inv.application.services.inv_estorno_proceso.get_stock_by_producto_almacen",
        new=AsyncMock(
            return_value={
                "cantidad_actual": Decimal("15"),
                "costo_promedio": Decimal("5"),
            }
        ),
    ):
        await estorno.assert_entrada_espejo_ppm_viable(
            client_id=CLIENT_ID,
            empresa_id=EMPRESA_ID,
            tipo_movimiento=tipo,
            movimiento=mov,
            detalles=detalles,
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_x08_no_lanza_si_afecta_costo_cero():
    mov = _movimiento_base(almacen_destino_id=ALMACEN_D)
    tipo = {"clase_movimiento": "entrada", "afecta_costo": False}
    detalles = [_detalle(cantidad_base=Decimal("10"))]

    with patch(
        "app.modules.inv.application.services.inv_estorno_proceso.get_stock_by_producto_almacen",
        new=AsyncMock(
            return_value={
                "cantidad_actual": Decimal("10"),
                "costo_promedio": Decimal("5"),
            }
        ),
    ):
        await estorno.assert_entrada_espejo_ppm_viable(
            client_id=CLIENT_ID,
            empresa_id=EMPRESA_ID,
            tipo_movimiento=tipo,
            movimiento=mov,
            detalles=detalles,
        )


@pytest.mark.unit
def test_gate_mvp_bloquea_inventario_fisico():
    with pytest.raises(ConflictError) as exc_info:
        estorno.assert_estorno_mvp_allowed(
            {"documento_referencia_tipo": "inventario_fisico"}
        )
    assert exc_info.value.internal_code == estorno.ESTORNO_INTEGRACION_NO_MVP_CODE


@pytest.mark.unit
def test_gate_mvp_bloquea_recepcion_case_insensitive():
    with pytest.raises(ConflictError) as exc_info:
        estorno.assert_estorno_mvp_allowed(
            {"documento_referencia_tipo": "RECEPCION"}
        )
    assert exc_info.value.internal_code == estorno.ESTORNO_INTEGRACION_NO_MVP_CODE


@pytest.mark.unit
def test_gate_estornado_rechaza_estado_terminal():
    with pytest.raises(ConflictError) as exc_info:
        estorno.assert_not_already_estornado({"estado": "estornado"})
    assert exc_info.value.internal_code == estorno.MOVIMIENTO_YA_ESTORNADO_CODE


@pytest.mark.unit
def test_x07_cabecera_autorizado_cuando_requiere_autorizacion():
    original = _movimiento_base(
        requiere_autorizacion=True,
        almacen_destino_id=ALMACEN_D,
    )
    detalles_espejo = estorno.build_compensatorio_detalles(
        [_detalle(cantidad_base=Decimal("10"))],
        "entrada",
    )
    now = datetime(2026, 6, 12, 10, 0, 0)
    cab = estorno.build_compensatorio_cabecera_espejo(
        original=original,
        clase_movimiento="entrada",
        motivo="Corrección",
        usuario_estorno=USUARIO_ID,
        compensatorio_movimiento_id=uuid4(),
        numero_movimiento="MOV-EST-001",
        detalles_espejo=detalles_espejo,
        now=now,
    )
    assert cab["estado"] == "autorizado"
    assert cab["fecha_autorizacion"] == now
    assert cab["autorizado_por_usuario_id"] == USUARIO_ID
    assert cab["requiere_autorizacion"] is True
    assert cab["documento_referencia_tipo"] == estorno.ESTORNO_REF_TIPO
    assert cab["documento_referencia_id"] == MOVIMIENTO_ID


@pytest.mark.unit
def test_cabecera_borrador_sin_requiere_autorizacion():
    original = _movimiento_base(
        requiere_autorizacion=False,
        almacen_origen_id=ALMACEN_O,
    )
    detalles_espejo = estorno.build_compensatorio_detalles(
        [_detalle(cantidad_base=Decimal("5"))],
        "salida",
    )
    cab = estorno.build_compensatorio_cabecera_espejo(
        original=original,
        clase_movimiento="salida",
        motivo=None,
        usuario_estorno=USUARIO_ID,
        compensatorio_movimiento_id=uuid4(),
        numero_movimiento="MOV-EST-002",
        detalles_espejo=detalles_espejo,
    )
    assert cab["estado"] == "borrador"
    assert cab["fecha_autorizacion"] is None
    assert cab["autorizado_por_usuario_id"] is None
    assert cab["almacen_origen_id"] == ALMACEN_O


@pytest.mark.unit
@pytest.mark.asyncio
async def test_find_compensatorio_by_original():
    comp_id = uuid4()
    mock_uow = AsyncMock()
    mock_uow.execute = AsyncMock(
        return_value=[
            {
                "movimiento_id": comp_id,
                "documento_referencia_tipo": estorno.ESTORNO_REF_TIPO,
                "documento_referencia_id": MOVIMIENTO_ID,
            }
        ]
    )
    row = await estorno.find_compensatorio_by_original(
        mock_uow,
        client_id=CLIENT_ID,
        empresa_id=EMPRESA_ID,
        original_movimiento_id=MOVIMIENTO_ID,
    )
    assert row is not None
    assert row["movimiento_id"] == comp_id


@pytest.mark.unit
def test_assert_compensatorio_no_existe_lanza_si_hay_compensatorio():
    with pytest.raises(ConflictError) as exc_info:
        estorno.assert_compensatorio_no_existe({"movimiento_id": uuid4()})
    assert exc_info.value.internal_code == estorno.MOVIMIENTO_YA_ESTORNADO_CODE


@pytest.mark.unit
@pytest.mark.asyncio
async def test_e09_estornado_no_procesable():
    """E-09: procesar sobre estornado → 409; una lectura, sin mutar stock."""
    token = set_current_empresa_id(EMPRESA_ID)
    movimiento_id = uuid4()
    row = {
        "movimiento_id": movimiento_id,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "estado": "estornado",
    }
    mock_uow = AsyncMock()
    mock_uow.execute = AsyncMock(return_value=[row])

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await movimiento_proceso_service.procesar_movimiento_servicio(
                    client_id=CLIENT_ID,
                    movimiento_id=movimiento_id,
                )
        assert exc_info.value.status_code == 409
        assert "estornado" in exc_info.value.detail.lower()
        assert mock_uow.execute.call_count == 1
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_e09b_estornado_no_autorizable():
    """Guard Etapa 2: autorizar sobre estornado → 409; sin update."""
    token = set_current_empresa_id(EMPRESA_ID)
    movimiento_id = uuid4()
    row = {
        "movimiento_id": movimiento_id,
        "empresa_id": EMPRESA_ID,
        "estado": "estornado",
    }

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service.get_movimiento_by_id",
            new=AsyncMock(return_value=row),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.update_movimiento",
            new=AsyncMock(),
        ) as mock_update:
            with pytest.raises(HTTPException) as exc_info:
                await movimiento_proceso_service.autorizar_movimiento_servicio(
                    client_id=CLIENT_ID,
                    movimiento_id=movimiento_id,
                )
        assert exc_info.value.status_code == 409
        assert "estornado" in exc_info.value.detail.lower()
        mock_update.assert_not_called()
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_e10_estornado_no_anulable():
    """E-10: anular sobre estornado → 409 (no idempotente como anulado)."""
    token = set_current_empresa_id(EMPRESA_ID)
    movimiento_id = uuid4()
    row = {
        "movimiento_id": movimiento_id,
        "empresa_id": EMPRESA_ID,
        "estado": "estornado",
    }

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service.get_movimiento_by_id",
            new=AsyncMock(return_value=row),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.update_movimiento",
            new=AsyncMock(),
        ) as mock_update:
            with pytest.raises(HTTPException) as exc_info:
                await movimiento_proceso_service.anular_movimiento_servicio(
                    client_id=CLIENT_ID,
                    movimiento_id=movimiento_id,
                )
        assert exc_info.value.status_code == 409
        assert "estornado" in exc_info.value.detail.lower()
        mock_update.assert_not_called()
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
def test_e11_estornado_no_reestornable():
    """E-11: gate pre-estorno rechaza estado estornado (assert_not_already_estornado)."""
    with pytest.raises(ConflictError) as exc_info:
        estorno.assert_not_already_estornado({"estado": "estornado"})
    assert exc_info.value.internal_code == estorno.MOVIMIENTO_YA_ESTORNADO_CODE


def _original_procesado_entrada(**extra) -> dict:
    base = {
        "movimiento_id": MOVIMIENTO_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "numero_movimiento": "MOV-001",
        "tipo_movimiento_id": TIPO_MOVIMIENTO_ID,
        "estado": "procesado",
        "fecha_procesado": datetime.utcnow(),
        "usuario_procesado_id": USUARIO_ID,
        "almacen_destino_id": ALMACEN_D,
        "moneda_id": MONEDA_ID,
        "requiere_autorizacion": False,
        "fecha_contable": date(2026, 6, 12),
    }
    base.update(extra)
    return base


def _tipo_entrada(*, afecta_costo: bool = False) -> dict:
    return {
        "tipo_movimiento_id": TIPO_MOVIMIENTO_ID,
        "clase_movimiento": "entrada",
        "afecta_costo": afecta_costo,
    }


def _detalle_original(*, cantidad_base: Decimal = Decimal("10")) -> dict:
    return {
        "producto_id": PRODUCTO_ID,
        "cantidad": cantidad_base,
        "unidad_medida_id": UNIDAD_MEDIDA_ID,
        "cantidad_base": cantidad_base,
        "costo_unitario": Decimal("5"),
        "moneda_id": MONEDA_ID,
        "fecha_creacion": datetime.utcnow(),
    }


def _is_lock_query(query) -> bool:
    text = query if isinstance(query, str) else str(query)
    return "UPDLOCK" in text and "ROWLOCK" in text


def _build_estorno_uow_mock(
    *,
    original: dict,
    tipo: dict,
    detalles: list[dict],
    compensatorio_existente: list | None = None,
    p5_rows_affected: int = 1,
) -> tuple[AsyncMock, list[str]]:
    """Mock UoW que simula P0–P5; retorna (uow, ops registradas)."""
    ops: list[str] = []
    original_estornado = {
        **original,
        "estado": "estornado",
        "motivo_anulacion": "Corrección test",
    }
    p5_done = False

    async def _fake_execute(query, params=None):
        nonlocal p5_done
        if _is_lock_query(query):
            ops.append("P0_lock")
            return [original]

        compiled = str(query)
        table_name = getattr(getattr(query, "table", None), "name", "")
        cls_name = query.__class__.__name__

        if table_name == "inv_movimiento" and cls_name == "Insert":
            ops.append("P2_insert_compensatorio")
            return {"rows_affected": 1}

        if table_name == "inv_movimiento_detalle" and cls_name == "Insert":
            ops.append("P3_insert_detalle")
            return {"rows_affected": 1}

        if table_name == "inv_movimiento" and cls_name == "Update":
            ops.append("P5_update_estornado")
            p5_done = True
            return {"rows_affected": p5_rows_affected}

        if "inv_tipo_movimiento" in compiled:
            ops.append("read_tipo")
            return [tipo]

        if "inv_movimiento_detalle" in compiled and cls_name != "Insert":
            ops.append("read_detalles")
            return detalles

        if (
            p5_done
            and cls_name == "Select"
            and "inv_movimiento" in compiled
            and "inv_movimiento_detalle" not in compiled
        ):
            ops.append("read_final")
            return [original_estornado]

        if (
            cls_name == "Select"
            and "inv_movimiento" in compiled
            and "inv_movimiento_detalle" not in compiled
            and "inv_tipo_movimiento" not in compiled
            and not p5_done
        ):
            ops.append("P1_idempotencia")
            return compensatorio_existente or []

        return []

    mock_uow = AsyncMock()
    mock_uow.execute = AsyncMock(side_effect=_fake_execute)
    return mock_uow, ops


@pytest.mark.unit
@pytest.mark.asyncio
async def test_e01_estornar_entrada_procesada_flujo_completo():
    """E-01: entrada procesada → estornar → original estornado; procesar en misma UoW."""
    token = set_current_empresa_id(EMPRESA_ID)
    original = _original_procesado_entrada()
    tipo = _tipo_entrada(afecta_costo=False)
    detalles = [_detalle_original()]
    mock_uow, ops = _build_estorno_uow_mock(
        original=original, tipo=tipo, detalles=detalles
    )
    procesar_mock = AsyncMock(return_value={"estado": "procesado"})

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.assert_entrada_espejo_ppm_viable",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.procesar_movimiento_servicio",
            procesar_mock,
        ):
            result = await movimiento_proceso_service.estornar_movimiento_servicio(
                client_id=CLIENT_ID,
                movimiento_id=MOVIMIENTO_ID,
                motivo="Corrección test",
                usuario_estorno_id=USUARIO_ID,
            )

        assert result["estado"] == "estornado"
        procesar_mock.assert_awaited_once()
        assert procesar_mock.await_args.kwargs["uow"] is mock_uow
        assert "P0_lock" in ops
        assert "P1_idempotencia" in ops
        assert "P2_insert_compensatorio" in ops
        assert "P3_insert_detalle" in ops
        assert "P5_update_estornado" in ops
        assert ops.index("P2_insert_compensatorio") < ops.index("P5_update_estornado")
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_e20_fallo_p4_sin_compensatorio_persistido_ni_original_estornado():
    """E-20: fallo en P4 → excepción; sin P5; rollback implícito (sin commit)."""
    token = set_current_empresa_id(EMPRESA_ID)
    original = _original_procesado_entrada()
    mock_uow, ops = _build_estorno_uow_mock(
        original=original,
        tipo=_tipo_entrada(),
        detalles=[_detalle_original()],
    )

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.assert_entrada_espejo_ppm_viable",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.procesar_movimiento_servicio",
            new=AsyncMock(
                side_effect=HTTPException(
                    status_code=409,
                    detail="Stock insuficiente para procesar el movimiento",
                )
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await movimiento_proceso_service.estornar_movimiento_servicio(
                    client_id=CLIENT_ID,
                    movimiento_id=MOVIMIENTO_ID,
                    motivo="Fallo P4",
                    usuario_estorno_id=USUARIO_ID,
                )

        assert exc_info.value.status_code == 409
        assert "P5_update_estornado" not in ops
        assert "P2_insert_compensatorio" in ops
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_e21_orden_p4_antes_p5_update_estornado_no_llamado_si_procesar_falla():
    """E-21: P5 no se ejecuta si P4 falla (orden estricto)."""
    token = set_current_empresa_id(EMPRESA_ID)
    mock_uow, ops = _build_estorno_uow_mock(
        original=_original_procesado_entrada(),
        tipo=_tipo_entrada(),
        detalles=[_detalle_original()],
    )

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.assert_entrada_espejo_ppm_viable",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.procesar_movimiento_servicio",
            new=AsyncMock(side_effect=HTTPException(status_code=409, detail="fallo P4")),
        ):
            with pytest.raises(HTTPException):
                await movimiento_proceso_service.estornar_movimiento_servicio(
                    client_id=CLIENT_ID,
                    movimiento_id=MOVIMIENTO_ID,
                    usuario_estorno_id=USUARIO_ID,
                )

        assert "P3_insert_detalle" in ops
        assert "P5_update_estornado" not in ops
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_e23_rollback_total_stock_intacto_original_procesado():
    """E-23: P4 falla → sin P5, procesar falla (stock intacto), original sigue procesado."""
    token = set_current_empresa_id(EMPRESA_ID)
    original = _original_procesado_entrada()
    mock_uow, ops = _build_estorno_uow_mock(
        original=original, tipo=_tipo_entrada(), detalles=[_detalle_original()]
    )
    procesar_mock = AsyncMock(
        side_effect=HTTPException(
            status_code=409,
            detail="Stock insuficiente para procesar el movimiento",
        )
    )

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.assert_entrada_espejo_ppm_viable",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.procesar_movimiento_servicio",
            procesar_mock,
        ):
            with pytest.raises(HTTPException):
                await movimiento_proceso_service.estornar_movimiento_servicio(
                    client_id=CLIENT_ID,
                    movimiento_id=MOVIMIENTO_ID,
                    usuario_estorno_id=USUARIO_ID,
                )

        procesar_mock.assert_awaited_once()
        assert "P5_update_estornado" not in ops
        assert original["estado"] == "procesado"
        assert "P2_insert_compensatorio" in ops
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
def test_sql_lock_movimiento_contiene_updlock_rowlock():
    assert "UPDLOCK" in estorno.SQL_LOCK_MOVIMIENTO_ORIGINAL
    assert "ROWLOCK" in estorno.SQL_LOCK_MOVIMIENTO_ORIGINAL
    assert ":movimiento_id" in estorno.SQL_LOCK_MOVIMIENTO_ORIGINAL


@pytest.mark.unit
@pytest.mark.asyncio
async def test_e02_doble_estorno_servicio_estado_estornado():
    """E-02: original ya estornado en P0 → 409 MOVIMIENTO_YA_ESTORNADO."""
    token = set_current_empresa_id(EMPRESA_ID)
    original = _original_procesado_entrada(estado="estornado")
    mock_uow, _ = _build_estorno_uow_mock(
        original=original,
        tipo=_tipo_entrada(),
        detalles=[_detalle_original()],
    )

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ):
            with pytest.raises(ConflictError) as exc_info:
                await movimiento_proceso_service.estornar_movimiento_servicio(
                    client_id=CLIENT_ID,
                    movimiento_id=MOVIMIENTO_ID,
                    usuario_estorno_id=USUARIO_ID,
                )
        assert exc_info.value.internal_code == estorno.MOVIMIENTO_YA_ESTORNADO_CODE
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_e03_inventario_fisico_bloqueado_mvp():
    """E-03: documento_referencia_tipo=inventario_fisico → 409 MVP."""
    token = set_current_empresa_id(EMPRESA_ID)
    original = _original_procesado_entrada(
        documento_referencia_tipo="inventario_fisico",
    )
    mock_uow, _ = _build_estorno_uow_mock(
        original=original,
        tipo=_tipo_entrada(),
        detalles=[_detalle_original()],
    )

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ):
            with pytest.raises(ConflictError) as exc_info:
                await movimiento_proceso_service.estornar_movimiento_servicio(
                    client_id=CLIENT_ID,
                    movimiento_id=MOVIMIENTO_ID,
                    usuario_estorno_id=USUARIO_ID,
                )
        assert exc_info.value.internal_code == estorno.ESTORNO_INTEGRACION_NO_MVP_CODE
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_e04_recepcion_bloqueado_mvp():
    """E-04: documento_referencia_tipo=RECEPCION → 409 MVP."""
    token = set_current_empresa_id(EMPRESA_ID)
    original = _original_procesado_entrada(documento_referencia_tipo="RECEPCION")
    mock_uow, _ = _build_estorno_uow_mock(
        original=original,
        tipo=_tipo_entrada(),
        detalles=[_detalle_original()],
    )

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ):
            with pytest.raises(ConflictError) as exc_info:
                await movimiento_proceso_service.estornar_movimiento_servicio(
                    client_id=CLIENT_ID,
                    movimiento_id=MOVIMIENTO_ID,
                    usuario_estorno_id=USUARIO_ID,
                )
        assert exc_info.value.internal_code == estorno.ESTORNO_INTEGRACION_NO_MVP_CODE
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
def test_e12_compensatorio_trazabilidad_movimiento_estorno():
    """E-12: cabecera espejo con documento_referencia_tipo y documento_referencia_id."""
    original = _original_procesado_entrada()
    detalles_espejo = estorno.build_compensatorio_detalles(
        [_detalle_original()],
        "entrada",
    )
    cab = estorno.build_compensatorio_cabecera_espejo(
        original=original,
        clase_movimiento="entrada",
        motivo="Trazabilidad",
        usuario_estorno=USUARIO_ID,
        compensatorio_movimiento_id=uuid4(),
        numero_movimiento="MOV-EST-TRZ",
        detalles_espejo=detalles_espejo,
    )
    assert cab["documento_referencia_tipo"] == estorno.ESTORNO_REF_TIPO
    assert cab["documento_referencia_id"] == MOVIMIENTO_ID
    assert cab["documento_referencia_numero"] == "MOV-001"


@pytest.mark.unit
def test_e14_x07_compensatorio_autorizado_cuando_requiere_autorizacion():
    """E-14: X-07 — INSERT cabecera con estado autorizado y campos de autorización."""
    original = _original_procesado_entrada(requiere_autorizacion=True)
    detalles_espejo = estorno.build_compensatorio_detalles(
        [_detalle_original()],
        "entrada",
    )
    now = datetime(2026, 6, 12, 12, 0, 0)
    cab = estorno.build_compensatorio_cabecera_espejo(
        original=original,
        clase_movimiento="entrada",
        motivo="Auth",
        usuario_estorno=USUARIO_ID,
        compensatorio_movimiento_id=uuid4(),
        numero_movimiento="MOV-EST-AUTH",
        detalles_espejo=detalles_espejo,
        now=now,
    )
    assert cab["estado"] == "autorizado"
    assert cab["fecha_autorizacion"] == now
    assert cab["autorizado_por_usuario_id"] == USUARIO_ID
    assert cab["requiere_autorizacion"] is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_e22_p5_rows_affected_distinto_de_uno_lanza_race():
    """E-22: P5 rows_affected≠1 → 409 ESTORNO_UPDATE_RACE."""
    token = set_current_empresa_id(EMPRESA_ID)
    mock_uow, ops = _build_estorno_uow_mock(
        original=_original_procesado_entrada(),
        tipo=_tipo_entrada(),
        detalles=[_detalle_original()],
        p5_rows_affected=0,
    )

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.assert_entrada_espejo_ppm_viable",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.procesar_movimiento_servicio",
            new=AsyncMock(return_value={"estado": "procesado"}),
        ):
            with pytest.raises(ConflictError) as exc_info:
                await movimiento_proceso_service.estornar_movimiento_servicio(
                    client_id=CLIENT_ID,
                    movimiento_id=MOVIMIENTO_ID,
                    usuario_estorno_id=USUARIO_ID,
                )
        assert exc_info.value.internal_code == estorno.ESTORNO_UPDATE_RACE_CODE
        assert "P5_update_estornado" in ops
    finally:
        reset_current_empresa_id(token)
