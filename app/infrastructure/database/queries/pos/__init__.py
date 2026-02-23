# app/infrastructure/database/queries/pos/__init__.py
"""
Queries para el módulo POS (Punto de Venta).
"""

from app.infrastructure.database.queries.pos.punto_venta_queries import (
    list_puntos_venta,
    get_punto_venta_by_id,
    create_punto_venta,
    update_punto_venta,
)
from app.infrastructure.database.queries.pos.turno_caja_queries import (
    list_turnos_caja,
    get_turno_caja_by_id,
    create_turno_caja,
    update_turno_caja,
)
from app.infrastructure.database.queries.pos.venta_queries import (
    list_ventas,
    get_venta_by_id,
    create_venta,
    update_venta,
)
from app.infrastructure.database.queries.pos.venta_detalle_queries import (
    list_venta_detalles,
    get_venta_detalle_by_id,
    create_venta_detalle,
    update_venta_detalle,
)

__all__ = [
    # Punto de venta
    "list_puntos_venta",
    "get_punto_venta_by_id",
    "create_punto_venta",
    "update_punto_venta",
    # Turno caja
    "list_turnos_caja",
    "get_turno_caja_by_id",
    "create_turno_caja",
    "update_turno_caja",
    # Venta
    "list_ventas",
    "get_venta_by_id",
    "create_venta",
    "update_venta",
    # Venta detalle
    "list_venta_detalles",
    "get_venta_detalle_by_id",
    "create_venta_detalle",
    "update_venta_detalle",
]
