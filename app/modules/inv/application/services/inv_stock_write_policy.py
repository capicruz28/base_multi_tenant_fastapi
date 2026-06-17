"""
Política de escritura sobre inv_stock — tabla derivada (INV-P0-002).

La mutación canónica de stock ocurre solo vía procesar_movimiento_servicio / _apply_delta.
"""
from __future__ import annotations

from app.core.config import settings
from app.core.exceptions import ConflictError

STOCK_DERIVED_WRITE_FORBIDDEN_CODE = "STOCK_DERIVED_WRITE_FORBIDDEN"

_MSG_STOCK_DERIVED_WRITE = (
    "La escritura directa de stock está deshabilitada. "
    "Use movimientos de inventario procesados."
)


def is_stock_direct_write_allowed() -> bool:
    """True solo si INV_ALLOW_STOCK_DIRECT_WRITE está habilitado en settings (singleton)."""
    return settings.INV_ALLOW_STOCK_DIRECT_WRITE


def assert_stock_direct_write_allowed() -> None:
    """Rechaza escritura directa externa sobre inv_stock cuando la política está activa."""
    if not is_stock_direct_write_allowed():
        raise ConflictError(
            detail=_MSG_STOCK_DERIVED_WRITE,
            internal_code=STOCK_DERIVED_WRITE_FORBIDDEN_CODE,
        )
