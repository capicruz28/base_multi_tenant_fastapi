"""
Tests unitarios — INV-P0-001 + P0-005: helpers (C-01–C-08) y servicio procesar (Etapas 2–6).
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import ValidationError
from app.core.tenant.empresa_context import reset_current_empresa_id, set_current_empresa_id
from app.modules.inv.application.services import movimiento_proceso_service
from app.modules.inv.application.services.inv_costeo_proceso import (
    apply_if_zero_costo_policy,
    calc_ppm_entrada,
    calc_ppm_transferencia_destino,
    is_primera_entrada_costeable,
    requires_costo_unitario_line,
    round_costo,
    validate_costo_unitario_for_process,
)

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
MOVIMIENTO_ID = uuid4()
TIPO_MOVIMIENTO_ID = uuid4()
PRODUCTO_ID = uuid4()
ALMACEN_ID = uuid4()
ALMACEN_ORIGEN_ID = uuid4()
MONEDA_ID = uuid4()


class _FakeUowContext:
    def __init__(self, uow):
        self._uow = uow

    async def __aenter__(self):
        return self._uow

    async def __aexit__(self, *args):
        return False


def _extract_insert_values(stmt) -> dict:
    return {
        key: (param.value if hasattr(param, "value") else param)
        for key, param in stmt._values.items()
    }


def _extract_update_values(stmt) -> dict:
    return {
        key: (param.value if hasattr(param, "value") else param)
        for key, param in stmt._values.items()
    }


def _mov_borrador(
    *,
    clase_movimiento: str,
    almacen_origen_id=None,
    almacen_destino_id=None,
    mov_extra: dict | None = None,
) -> dict:
    base = {
        "movimiento_id": MOVIMIENTO_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "estado": "borrador",
        "tipo_movimiento_id": TIPO_MOVIMIENTO_ID,
        "moneda_id": MONEDA_ID,
        "requiere_autorizacion": False,
    }
    if clase_movimiento == "salida":
        base["almacen_origen_id"] = almacen_origen_id or ALMACEN_ORIGEN_ID
        base["almacen_destino_id"] = almacen_destino_id
    elif clase_movimiento == "transferencia":
        base["almacen_origen_id"] = almacen_origen_id or ALMACEN_ORIGEN_ID
        base["almacen_destino_id"] = almacen_destino_id or ALMACEN_ID
    else:
        base["almacen_origen_id"] = almacen_origen_id
        base["almacen_destino_id"] = almacen_destino_id or ALMACEN_ID
    if mov_extra:
        base.update(mov_extra)
    return base


def _tipo_movimiento(*, clase_movimiento: str, afecta_costo: bool) -> dict:
    return {
        "tipo_movimiento_id": TIPO_MOVIMIENTO_ID,
        "clase_movimiento": clase_movimiento,
        "afecta_costo": afecta_costo,
    }


def _detalle_linea(*, cantidad_base: Decimal, costo_unitario: Decimal) -> dict:
    return {
        "producto_id": PRODUCTO_ID,
        "cantidad_base": cantidad_base,
        "costo_unitario": costo_unitario,
        "fecha_creacion": datetime.utcnow(),
    }


def _build_procesar_uow_mock(
    *,
    clase_movimiento: str = "entrada",
    afecta_costo: bool,
    cantidad_base: Decimal,
    costo_unitario: Decimal,
    stock_existing: dict | None = None,
    mov_extra: dict | None = None,
    capture_stock_updates: list | None = None,
) -> tuple[AsyncMock, dict]:
    mov = _mov_borrador(
        clase_movimiento=clase_movimiento,
        mov_extra=mov_extra,
    )
    tipo = _tipo_movimiento(clase_movimiento=clase_movimiento, afecta_costo=afecta_costo)
    det = _detalle_linea(cantidad_base=cantidad_base, costo_unitario=costo_unitario)
    mov_procesado = {**mov, "estado": "procesado", "fecha_procesado": datetime.utcnow()}
    inserted_stock: dict = {}
    mov_select_count = 0

    async def _fake_execute(stmt):
        nonlocal mov_select_count
        if hasattr(stmt, "table") and getattr(stmt.table, "name", None) == "inv_stock":
            cls = stmt.__class__.__name__
            if cls == "Insert":
                inserted_stock.update(_extract_insert_values(stmt))
                return {"rows_affected": 1}
            if cls == "Update":
                if capture_stock_updates is not None:
                    capture_stock_updates.append(_extract_update_values(stmt))
                return {"rows_affected": 1}
        compiled = str(stmt)
        if "inv_movimiento" in compiled and "inv_movimiento_detalle" not in compiled:
            if "UPDATE" in compiled.upper():
                return {"rows_affected": 1}
            mov_select_count += 1
            if mov_select_count == 1:
                return [mov]
            return [mov_procesado]
        if "inv_tipo_movimiento" in compiled:
            return [tipo]
        if "inv_movimiento_detalle" in compiled:
            return [det]
        if "inv_stock" in compiled:
            return [stock_existing] if stock_existing else []
        return []

    mock_uow = AsyncMock()
    mock_uow.execute = AsyncMock(side_effect=_fake_execute)
    return mock_uow, inserted_stock


def _build_transferencia_uow_mock(
    *,
    afecta_costo: bool,
    cantidad_base: Decimal,
    stock_orig: dict,
    stock_dest: dict | None = None,
    capture_operations: list | None = None,
    capture_updates_by_rol: dict | None = None,
    capture_dest_insert: dict | None = None,
) -> AsyncMock:
    mov = _mov_borrador(clase_movimiento="transferencia")
    tipo = _tipo_movimiento(clase_movimiento="transferencia", afecta_costo=afecta_costo)
    det = _detalle_linea(cantidad_base=cantidad_base, costo_unitario=Decimal("0"))
    mov_procesado = {**mov, "estado": "procesado", "fecha_procesado": datetime.utcnow()}
    mov_select_count = 0
    stock_select_count = 0
    stock_update_count = 0

    def _record(op: str, rol: str) -> None:
        if capture_operations is not None:
            capture_operations.append((op, rol))

    async def _fake_execute(stmt):
        nonlocal mov_select_count, stock_select_count, stock_update_count
        if hasattr(stmt, "table") and getattr(stmt.table, "name", None) == "inv_stock":
            cls = stmt.__class__.__name__
            if cls == "Insert":
                values = _extract_insert_values(stmt)
                _record("insert", "destino")
                if capture_dest_insert is not None:
                    capture_dest_insert.update(values)
                return {"rows_affected": 1}
            if cls == "Update":
                stock_update_count += 1
                rol = "origen" if stock_update_count == 1 else "destino"
                values = _extract_update_values(stmt)
                _record("update", rol)
                if capture_updates_by_rol is not None:
                    capture_updates_by_rol.setdefault(rol, []).append(values)
                return {"rows_affected": 1}
        compiled = str(stmt)
        if "inv_movimiento" in compiled and "inv_movimiento_detalle" not in compiled:
            if "UPDATE" in compiled.upper():
                return {"rows_affected": 1}
            mov_select_count += 1
            if mov_select_count == 1:
                return [mov]
            return [mov_procesado]
        if "inv_tipo_movimiento" in compiled:
            return [tipo]
        if "inv_movimiento_detalle" in compiled:
            return [det]
        if "inv_stock" in compiled:
            stock_select_count += 1
            if stock_select_count in (1, 2):
                _record("select", "origen")
                return [stock_orig]
            _record("select", "destino")
            return [stock_dest] if stock_dest is not None else []
        return []

    mock_uow = AsyncMock()
    mock_uow.execute = AsyncMock(side_effect=_fake_execute)
    return mock_uow


@pytest.mark.unit
def test_c01_calc_ppm_entrada_ppm_sobre_stock_existente():
    result = calc_ppm_entrada(
        Decimal("10"),
        Decimal("5"),
        Decimal("10"),
        Decimal("8"),
        stock_exists=True,
    )
    assert result == Decimal("6.5")


@pytest.mark.unit
def test_c02_calc_ppm_entrada_primera_entrada_costeable_q_cero():
    result = calc_ppm_entrada(
        Decimal("0"),
        Decimal("0"),
        Decimal("10"),
        Decimal("5"),
        stock_exists=True,
    )
    assert result == Decimal("5")


@pytest.mark.unit
def test_c03_calc_ppm_transferencia_destino_ppm_mezcla():
    result = calc_ppm_transferencia_destino(
        Decimal("5"),
        Decimal("4"),
        Decimal("4"),
        Decimal("6.5"),
        stock_exists=True,
    )
    assert result == Decimal("46") / Decimal("9")


@pytest.mark.unit
def test_c04_apply_if_zero_costo_policy_conserva_c_positivo():
    result = apply_if_zero_costo_policy(Decimal("4"))
    assert result == Decimal("4")


@pytest.mark.unit
def test_c05_apply_if_zero_costo_policy_sin_costo_previo():
    result = apply_if_zero_costo_policy(Decimal("0"))
    assert result == Decimal("0")


@pytest.mark.unit
def test_c06_validate_costo_unitario_pur_entrada_cu_cero_lanza_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        validate_costo_unitario_for_process(
            afecta_costo=True,
            costo_unitario=Decimal("0"),
            es_movimiento_if=False,
            clase="entrada",
            delta=Decimal("10"),
        )
    assert "costo_unitario > 0" in exc_info.value.detail


@pytest.mark.unit
def test_c07_validate_costo_unitario_if_cu_cero_no_lanza():
    validate_costo_unitario_for_process(
        afecta_costo=True,
        costo_unitario=Decimal("0"),
        es_movimiento_if=True,
        clase="ajuste",
        delta=Decimal("5"),
    )


@pytest.mark.unit
def test_c08_requires_costo_unitario_line_ajuste_positivo_y_negativo():
    assert requires_costo_unitario_line("ajuste", Decimal("3")) is True
    assert requires_costo_unitario_line("ajuste", Decimal("-3")) is False
    assert requires_costo_unitario_line("entrada", Decimal("1")) is True
    assert requires_costo_unitario_line("salida", Decimal("1")) is False
    assert requires_costo_unitario_line("transferencia", Decimal("1")) is False


@pytest.mark.unit
def test_c02b_calc_ppm_entrada_legacy_q_negativo_asigna_cu():
    assert is_primera_entrada_costeable(Decimal("-5"), stock_exists=True) is True
    result = calc_ppm_entrada(
        Decimal("-5"),
        Decimal("0"),
        Decimal("3"),
        Decimal("10"),
        stock_exists=True,
    )
    assert result == Decimal("10")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_c10_procesar_entrada_ac1_stock_nuevo_costo_promedio_igual_cu():
    """C-10: AC=1 entrada sin stock → costo_promedio inicial = costo_unitario."""
    token = set_current_empresa_id(EMPRESA_ID)
    mock_uow, inserted = _build_procesar_uow_mock(
        afecta_costo=True,
        cantidad_base=Decimal("10"),
        costo_unitario=Decimal("5"),
    )
    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service._validate_proceso_referencias",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ):
            await movimiento_proceso_service.procesar_movimiento_servicio(
                client_id=CLIENT_ID,
                movimiento_id=MOVIMIENTO_ID,
            )
        assert inserted["cantidad_actual"] == Decimal("10")
        assert inserted["costo_promedio"] == Decimal("5.0000")
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_c10b_procesar_entrada_propaga_umbrales_desde_producto():
    """Stock nuevo debe heredar stock_minimo/maximo/punto_reorden del producto."""
    token = set_current_empresa_id(EMPRESA_ID)
    mock_uow, inserted = _build_procesar_uow_mock(
        afecta_costo=True,
        cantidad_base=Decimal("10"),
        costo_unitario=Decimal("5"),
    )
    producto = {
        "producto_id": PRODUCTO_ID,
        "stock_minimo": Decimal("230"),
        "stock_maximo": Decimal("500"),
        "punto_reorden": Decimal("250"),
    }
    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service._validate_proceso_referencias",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.get_producto_by_id",
            new=AsyncMock(return_value=producto),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ):
            await movimiento_proceso_service.procesar_movimiento_servicio(
                client_id=CLIENT_ID,
                movimiento_id=MOVIMIENTO_ID,
            )
        assert inserted["stock_minimo"] == Decimal("230")
        assert inserted["stock_maximo"] == Decimal("500")
        assert inserted["punto_reorden"] == Decimal("250")
    finally:
        reset_current_empresa_id(token)
@pytest.mark.unit
@pytest.mark.asyncio
async def test_c10b_procesar_entrada_ac1_crea_stock_cantidad_y_costo_explicitos():
    """Alta automática: stock inexistente + AC=1 + entrada costeable."""
    token = set_current_empresa_id(EMPRESA_ID)
    mock_uow, inserted = _build_procesar_uow_mock(
        afecta_costo=True,
        cantidad_base=Decimal("7"),
        costo_unitario=Decimal("12.5"),
    )
    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service._validate_proceso_referencias",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ):
            await movimiento_proceso_service.procesar_movimiento_servicio(
                client_id=CLIENT_ID,
                movimiento_id=MOVIMIENTO_ID,
            )
        assert inserted["cantidad_actual"] == Decimal("7")
        assert inserted["costo_promedio"] == round_costo(Decimal("12.5"))
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_c16_procesar_entrada_ac0_stock_nuevo_costo_promedio_cero():
    """C-16: AC=0 → solo cantidad; costo_promedio permanece en 0 al crear."""
    token = set_current_empresa_id(EMPRESA_ID)
    mock_uow, inserted = _build_procesar_uow_mock(
        afecta_costo=False,
        cantidad_base=Decimal("10"),
        costo_unitario=Decimal("99"),
    )
    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service._validate_proceso_referencias",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ):
            await movimiento_proceso_service.procesar_movimiento_servicio(
                client_id=CLIENT_ID,
                movimiento_id=MOVIMIENTO_ID,
            )
        assert inserted["cantidad_actual"] == Decimal("10")
        assert inserted["costo_promedio"] == Decimal("0")
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_c16b_procesar_entrada_ac0_stock_existente_no_altera_costo():
    """AC=0 con stock previo: cantidad suma; costo_promedio no se escribe en UPDATE."""
    token = set_current_empresa_id(EMPRESA_ID)
    stock_existing = {
        "stock_id": uuid4(),
        "cantidad_actual": Decimal("4"),
        "costo_promedio": Decimal("3.2500"),
    }
    update_payloads: list[dict] = []
    mock_uow, _ = _build_procesar_uow_mock(
        afecta_costo=False,
        cantidad_base=Decimal("6"),
        costo_unitario=Decimal("50"),
        stock_existing=stock_existing,
        capture_stock_updates=update_payloads,
    )

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service._validate_proceso_referencias",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ):
            await movimiento_proceso_service.procesar_movimiento_servicio(
                client_id=CLIENT_ID,
                movimiento_id=MOVIMIENTO_ID,
            )
        assert len(update_payloads) == 1
        assert update_payloads[0]["cantidad_actual"] == Decimal("10")
        assert "costo_promedio" not in update_payloads[0]
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_c11_procesar_entrada_ac1_stock_existente_ppm():
    """C-11: §6.2 — Q=10, C=5, δ=10, cu=8 → C_new=6.5000, Q_new=20."""
    token = set_current_empresa_id(EMPRESA_ID)
    stock_existing = {
        "stock_id": uuid4(),
        "cantidad_actual": Decimal("10"),
        "costo_promedio": Decimal("5.0000"),
    }
    update_payloads: list[dict] = []
    mock_uow, inserted = _build_procesar_uow_mock(
        clase_movimiento="entrada",
        afecta_costo=True,
        cantidad_base=Decimal("10"),
        costo_unitario=Decimal("8"),
        stock_existing=stock_existing,
        capture_stock_updates=update_payloads,
    )
    q_prev = stock_existing["cantidad_actual"]
    c_prev = stock_existing["costo_promedio"]
    delta = Decimal("10")
    cu = Decimal("8")
    c_esperado = round_costo((q_prev * c_prev + delta * cu) / (q_prev + delta))

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service._validate_proceso_referencias",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ):
            await movimiento_proceso_service.procesar_movimiento_servicio(
                client_id=CLIENT_ID,
                movimiento_id=MOVIMIENTO_ID,
            )
        assert not inserted
        assert len(update_payloads) == 1
        assert update_payloads[0]["cantidad_actual"] == Decimal("20")
        assert update_payloads[0]["costo_promedio"] == c_esperado
        assert c_esperado == Decimal("6.5000")
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_c12_procesar_salida_ac1_no_altera_costo_promedio():
    """C-12: §6.4 — Q=20, C=6.5000, δ=3 → Q_new=17, C sin cambio."""
    token = set_current_empresa_id(EMPRESA_ID)
    stock_existing = {
        "stock_id": uuid4(),
        "cantidad_actual": Decimal("20"),
        "costo_promedio": Decimal("6.5000"),
    }
    update_payloads: list[dict] = []
    mock_uow, inserted = _build_procesar_uow_mock(
        clase_movimiento="salida",
        afecta_costo=True,
        cantidad_base=Decimal("3"),
        costo_unitario=Decimal("0"),
        stock_existing=stock_existing,
        capture_stock_updates=update_payloads,
    )

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service._validate_proceso_referencias",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ):
            await movimiento_proceso_service.procesar_movimiento_servicio(
                client_id=CLIENT_ID,
                movimiento_id=MOVIMIENTO_ID,
            )
        assert not inserted
        assert len(update_payloads) == 1
        assert update_payloads[0]["cantidad_actual"] == Decimal("17")
        assert "costo_promedio" not in update_payloads[0]
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_c17_procesar_entrada_ac1_cu_cero_pur_validation_error_sin_stock():
    """C-17: §6.3 — AC=1, entrada PUR, cu=0 → ValidationError; sin mutar stock."""
    token = set_current_empresa_id(EMPRESA_ID)
    update_payloads: list[dict] = []
    mock_uow, inserted = _build_procesar_uow_mock(
        clase_movimiento="entrada",
        afecta_costo=True,
        cantidad_base=Decimal("10"),
        costo_unitario=Decimal("0"),
        mov_extra={"documento_referencia_tipo": "RECEPCION"},
        capture_stock_updates=update_payloads,
    )

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service._validate_proceso_referencias",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ):
            with pytest.raises(ValidationError) as exc_info:
                await movimiento_proceso_service.procesar_movimiento_servicio(
                    client_id=CLIENT_ID,
                    movimiento_id=MOVIMIENTO_ID,
                )
        assert "costo_unitario > 0" in exc_info.value.detail
        assert not inserted
        assert not update_payloads
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_c13_procesar_transferencia_ac1_destino_stock_existente_ppm_con_c_orig():
    """C-13: §6.6 — AC=1, cu_eff=C_orig; origen sin costo; destino PP."""
    token = set_current_empresa_id(EMPRESA_ID)
    q_orig = Decimal("10")
    c_orig = Decimal("6.5000")
    q_dest = Decimal("5")
    c_dest = Decimal("4.0000")
    delta = Decimal("4")
    c_dest_esperado = round_costo(
        calc_ppm_transferencia_destino(
            q_dest, c_dest, delta, c_orig, stock_exists=True
        )
    )
    stock_orig = {
        "stock_id": uuid4(),
        "cantidad_actual": q_orig,
        "costo_promedio": c_orig,
    }
    stock_dest = {
        "stock_id": uuid4(),
        "cantidad_actual": q_dest,
        "costo_promedio": c_dest,
    }
    updates: dict = {}
    mock_uow = _build_transferencia_uow_mock(
        afecta_costo=True,
        cantidad_base=delta,
        stock_orig=stock_orig,
        stock_dest=stock_dest,
        capture_updates_by_rol=updates,
    )

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service._validate_proceso_referencias",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ):
            await movimiento_proceso_service.procesar_movimiento_servicio(
                client_id=CLIENT_ID,
                movimiento_id=MOVIMIENTO_ID,
            )
        assert updates["origen"][0]["cantidad_actual"] == Decimal("6")
        assert "costo_promedio" not in updates["origen"][0]
        assert updates["destino"][0]["cantidad_actual"] == Decimal("9")
        assert updates["destino"][0]["costo_promedio"] == c_dest_esperado
        assert c_dest_esperado == Decimal("5.1111")
        assert (q_dest * c_dest + delta * c_orig) / (q_dest + delta) == Decimal("46") / Decimal("9")
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_c20_procesar_transferencia_lectura_c_orig_antes_decremento_origen():
    """C-20: primer SELECT origen (captura C_orig) ocurre antes del UPDATE origen."""
    token = set_current_empresa_id(EMPRESA_ID)
    stock_orig = {
        "stock_id": uuid4(),
        "cantidad_actual": Decimal("10"),
        "costo_promedio": Decimal("6.5000"),
    }
    stock_dest = {
        "stock_id": uuid4(),
        "cantidad_actual": Decimal("5"),
        "costo_promedio": Decimal("4.0000"),
    }
    operations: list[tuple[str, str]] = []
    mock_uow = _build_transferencia_uow_mock(
        afecta_costo=True,
        cantidad_base=Decimal("4"),
        stock_orig=stock_orig,
        stock_dest=stock_dest,
        capture_operations=operations,
    )

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service._validate_proceso_referencias",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ):
            await movimiento_proceso_service.procesar_movimiento_servicio(
                client_id=CLIENT_ID,
                movimiento_id=MOVIMIENTO_ID,
            )
        first_select_origen = next(
            i for i, (op, rol) in enumerate(operations) if op == "select" and rol == "origen"
        )
        first_update_origen = next(
            i for i, (op, rol) in enumerate(operations) if op == "update" and rol == "origen"
        )
        assert first_select_origen < first_update_origen
        assert operations[0] == ("select", "origen")
        assert not any(
            op == "select" and rol == "origen" and idx > first_update_origen
            for idx, (op, rol) in enumerate(operations)
        )
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_c14_procesar_ajuste_positivo_ac1_ppm():
    """C-14: §6.7 — ajuste+ AC=1, Q=10, C=5, δ=3, cu=7 → C_new=5.4615, Q_new=13."""
    token = set_current_empresa_id(EMPRESA_ID)
    q_prev = Decimal("10")
    c_prev = Decimal("5.0000")
    delta = Decimal("3")
    cu = Decimal("7")
    stock_existing = {
        "stock_id": uuid4(),
        "cantidad_actual": q_prev,
        "costo_promedio": c_prev,
    }
    update_payloads: list[dict] = []
    mock_uow, inserted = _build_procesar_uow_mock(
        clase_movimiento="ajuste",
        afecta_costo=True,
        cantidad_base=delta,
        costo_unitario=cu,
        stock_existing=stock_existing,
        capture_stock_updates=update_payloads,
    )
    c_esperado = round_costo((q_prev * c_prev + delta * cu) / (q_prev + delta))

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service._validate_proceso_referencias",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ):
            await movimiento_proceso_service.procesar_movimiento_servicio(
                client_id=CLIENT_ID,
                movimiento_id=MOVIMIENTO_ID,
            )
        assert not inserted
        assert len(update_payloads) == 1
        assert update_payloads[0]["cantidad_actual"] == Decimal("13")
        assert update_payloads[0]["costo_promedio"] == c_esperado
        assert c_esperado == Decimal("5.4615")
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_c15_procesar_ajuste_negativo_ac1_no_altera_costo_promedio():
    """C-15: §6.8 — ajuste− AC=1, Q=10, C=5, δ=-3 → Q_new=7, C sin cambio."""
    token = set_current_empresa_id(EMPRESA_ID)
    stock_existing = {
        "stock_id": uuid4(),
        "cantidad_actual": Decimal("10"),
        "costo_promedio": Decimal("5.0000"),
    }
    update_payloads: list[dict] = []
    mock_uow, inserted = _build_procesar_uow_mock(
        clase_movimiento="ajuste",
        afecta_costo=True,
        cantidad_base=Decimal("-3"),
        costo_unitario=Decimal("0"),
        stock_existing=stock_existing,
        capture_stock_updates=update_payloads,
    )

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service._validate_proceso_referencias",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ):
            await movimiento_proceso_service.procesar_movimiento_servicio(
                client_id=CLIENT_ID,
                movimiento_id=MOVIMIENTO_ID,
            )
        assert not inserted
        assert len(update_payloads) == 1
        assert update_payloads[0]["cantidad_actual"] == Decimal("7")
        assert "costo_promedio" not in update_payloads[0]
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_c18_procesar_if_ajuste_positivo_cu_cero_conserva_costo():
    """C-18: §6.9 — IF, AC=1, cu=0, Q=10, C=4 → Q_new=15, C_new=4.0000."""
    token = set_current_empresa_id(EMPRESA_ID)
    stock_existing = {
        "stock_id": uuid4(),
        "cantidad_actual": Decimal("10"),
        "costo_promedio": Decimal("4.0000"),
    }
    update_payloads: list[dict] = []
    mock_uow, inserted = _build_procesar_uow_mock(
        clase_movimiento="ajuste",
        afecta_costo=True,
        cantidad_base=Decimal("5"),
        costo_unitario=Decimal("0"),
        stock_existing=stock_existing,
        mov_extra={"documento_referencia_tipo": "inventario_fisico"},
        capture_stock_updates=update_payloads,
    )

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service._validate_proceso_referencias",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ):
            await movimiento_proceso_service.procesar_movimiento_servicio(
                client_id=CLIENT_ID,
                movimiento_id=MOVIMIENTO_ID,
            )
        assert not inserted
        assert len(update_payloads) == 1
        assert update_payloads[0]["cantidad_actual"] == Decimal("15")
        assert update_payloads[0]["costo_promedio"] == Decimal("4.0000")
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_c19_procesar_if_ajuste_positivo_cu_cero_stock_nuevo_costo_cero():
    """C-19: §6.10 — IF, AC=1, cu=0, sin stock → Q_new=5, C_new=0.0000."""
    token = set_current_empresa_id(EMPRESA_ID)
    mock_uow, inserted = _build_procesar_uow_mock(
        clase_movimiento="ajuste",
        afecta_costo=True,
        cantidad_base=Decimal("5"),
        costo_unitario=Decimal("0"),
        mov_extra={"documento_referencia_tipo": "inventario_fisico"},
    )

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service._validate_proceso_referencias",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ):
            await movimiento_proceso_service.procesar_movimiento_servicio(
                client_id=CLIENT_ID,
                movimiento_id=MOVIMIENTO_ID,
            )
        assert inserted["cantidad_actual"] == Decimal("5")
        assert inserted["costo_promedio"] == Decimal("0")
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_c21_procesar_transferencia_ac0_destino_vacio_hereda_c_orig():
    """C-21: §6.12 — AC=0, destino vacío → C_dest = C_orig (AD-01)."""
    token = set_current_empresa_id(EMPRESA_ID)
    c_orig = Decimal("6.5000")
    delta = Decimal("4")
    stock_orig = {
        "stock_id": uuid4(),
        "cantidad_actual": Decimal("20"),
        "costo_promedio": c_orig,
    }
    updates: dict = {}
    dest_insert: dict = {}
    mock_uow = _build_transferencia_uow_mock(
        afecta_costo=False,
        cantidad_base=delta,
        stock_orig=stock_orig,
        stock_dest=None,
        capture_updates_by_rol=updates,
        capture_dest_insert=dest_insert,
    )

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service._validate_proceso_referencias",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ):
            await movimiento_proceso_service.procesar_movimiento_servicio(
                client_id=CLIENT_ID,
                movimiento_id=MOVIMIENTO_ID,
            )
        assert updates["origen"][0]["cantidad_actual"] == Decimal("16")
        assert "costo_promedio" not in updates["origen"][0]
        assert dest_insert["cantidad_actual"] == delta
        assert dest_insert["costo_promedio"] == c_orig
        assert dest_insert["costo_promedio"] != Decimal("0")
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_c22_procesar_entrada_legacy_q_cero_c_new_igual_cu():
    """C-22: §6.13 — stock legacy Q=0, C=0 → primera entrada costeable, C_new=cu."""
    token = set_current_empresa_id(EMPRESA_ID)
    cu = Decimal("5")
    delta = Decimal("10")
    stock_existing = {
        "stock_id": uuid4(),
        "cantidad_actual": Decimal("0"),
        "costo_promedio": Decimal("0"),
    }
    update_payloads: list[dict] = []
    mock_uow, inserted = _build_procesar_uow_mock(
        clase_movimiento="entrada",
        afecta_costo=True,
        cantidad_base=delta,
        costo_unitario=cu,
        stock_existing=stock_existing,
        capture_stock_updates=update_payloads,
    )

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service._validate_proceso_referencias",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ):
            await movimiento_proceso_service.procesar_movimiento_servicio(
                client_id=CLIENT_ID,
                movimiento_id=MOVIMIENTO_ID,
            )
        assert not inserted
        assert len(update_payloads) == 1
        assert update_payloads[0]["cantidad_actual"] == delta
        assert update_payloads[0]["costo_promedio"] == round_costo(cu)
        assert is_primera_entrada_costeable(Decimal("0"), stock_exists=True)
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
def test_c23_calc_intermedio_sin_redondeo_persist_con_cuatro_decimales():
    """C-23: §15.3 / AD-03 — helper sin quantize; round_costo solo al persistir."""
    c_intermedio = calc_ppm_transferencia_destino(
        Decimal("5"),
        Decimal("4"),
        Decimal("4"),
        Decimal("6.5"),
        stock_exists=True,
    )
    assert c_intermedio == Decimal("46") / Decimal("9")
    assert c_intermedio != round_costo(c_intermedio)
    assert round_costo(c_intermedio) == Decimal("5.1111")
    assert len(str(c_intermedio).split(".")[1]) > 4


@pytest.mark.unit
@pytest.mark.asyncio
async def test_c23b_procesar_transferencia_persiste_costo_redondeado_ad03():
    """C-23 servicio: valor persistido en procesar coincide con round_costo del helper."""
    token = set_current_empresa_id(EMPRESA_ID)
    q_dest = Decimal("5")
    c_dest = Decimal("4")
    c_orig = Decimal("6.5")
    delta = Decimal("4")
    c_helper = calc_ppm_transferencia_destino(
        q_dest, c_dest, delta, c_orig, stock_exists=True
    )
    stock_orig = {
        "stock_id": uuid4(),
        "cantidad_actual": Decimal("10"),
        "costo_promedio": c_orig,
    }
    stock_dest = {
        "stock_id": uuid4(),
        "cantidad_actual": q_dest,
        "costo_promedio": c_dest,
    }
    updates: dict = {}
    mock_uow = _build_transferencia_uow_mock(
        afecta_costo=True,
        cantidad_base=delta,
        stock_orig=stock_orig,
        stock_dest=stock_dest,
        capture_updates_by_rol=updates,
    )

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service._validate_proceso_referencias",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ):
            await movimiento_proceso_service.procesar_movimiento_servicio(
                client_id=CLIENT_ID,
                movimiento_id=MOVIMIENTO_ID,
            )
        assert c_helper == Decimal("46") / Decimal("9")
        assert updates["destino"][0]["costo_promedio"] == round_costo(c_helper)
        assert updates["destino"][0]["costo_promedio"] == Decimal("5.1111")
    finally:
        reset_current_empresa_id(token)
