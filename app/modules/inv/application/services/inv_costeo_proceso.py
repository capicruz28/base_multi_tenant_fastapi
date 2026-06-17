"""
Helpers de costeo al procesar movimientos (INV-P0-001 + INV-P0-005).

Promedio Ponderado Móvil (PPM), gate ``afecta_costo`` y excepción inventario físico.
Los resultados de ``calc_*`` no redondean; usar ``round_costo`` solo al persistir (AD-03).
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from app.core.exceptions import ValidationError

COSTO_QUANT = Decimal("0.0001")

_MSG_COSTO_REQUERIDO = (
    "No se puede procesar: la línea requiere costo_unitario > 0 "
    "cuando el tipo de movimiento afecta costo."
)


def _to_decimal(value: Any, default: str = "0") -> Decimal:
    if value is None:
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def is_movimiento_inventario_fisico(mov: dict) -> bool:
    ref = (mov.get("documento_referencia_tipo") or "").lower()
    return ref == "inventario_fisico"


def requires_costo_unitario_line(clase: str, delta: Decimal) -> bool:
    clase_norm = (clase or "").lower()
    if clase_norm == "entrada":
        return True
    if clase_norm == "ajuste":
        return delta > 0
    return False


def validate_costo_unitario_for_process(
    *,
    afecta_costo: bool,
    costo_unitario: Decimal,
    es_movimiento_if: bool,
    clase: str,
    delta: Decimal,
) -> None:
    if not afecta_costo:
        return
    if es_movimiento_if:
        return
    if not requires_costo_unitario_line(clase, delta):
        return
    if costo_unitario <= 0:
        raise ValidationError(detail=_MSG_COSTO_REQUERIDO)


def is_primera_entrada_costeable(q: Decimal, stock_exists: bool) -> bool:
    if not stock_exists:
        return True
    return q <= 0


def calc_ppm_entrada(
    q: Decimal,
    c: Decimal,
    delta: Decimal,
    cu: Decimal,
    *,
    stock_exists: bool,
) -> Decimal:
    """Retorna ``C_new`` sin redondear (§5.5 / AD-02)."""
    if is_primera_entrada_costeable(q, stock_exists):
        return cu
    q_new = q + delta
    return (q * c + delta * cu) / q_new


def calc_ppm_transferencia_destino(
    q_dest: Decimal,
    c_dest: Decimal,
    delta: Decimal,
    cu_eff: Decimal,
    *,
    stock_exists: bool,
) -> Decimal:
    """Retorna ``C_dest_new`` sin redondear para AC=1 (§5.7 paso B)."""
    if not stock_exists or q_dest <= 0:
        return cu_eff
    q_new = q_dest + delta
    return (q_dest * c_dest + delta * cu_eff) / q_new


def calc_costo_transferencia_destino_propagacion(cu_eff: Decimal) -> Decimal:
    """AD-01: destino sin stock hereda ``C_origen`` (AC=0 o AC=1)."""
    return cu_eff


def apply_if_zero_costo_policy(c: Decimal) -> Decimal:
    """Excepción IF §5.4 cuando ``cu <= 0``: conservar C o 0."""
    if c > 0:
        return c
    return Decimal("0")


def round_costo(val: Decimal) -> Decimal:
    """Único punto de redondeo al persistir (AD-03)."""
    return val.quantize(COSTO_QUANT, rounding=ROUND_HALF_UP)
