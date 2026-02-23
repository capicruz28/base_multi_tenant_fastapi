# app/infrastructure/database/queries/invbill/__init__.py
"""
Queries para el módulo INV_BILL (Facturación Electrónica).
"""

from app.infrastructure.database.queries.invbill.serie_queries import (
    list_series,
    get_serie_by_id,
    create_serie,
    update_serie,
)
from app.infrastructure.database.queries.invbill.comprobante_queries import (
    list_comprobantes,
    get_comprobante_by_id,
    create_comprobante,
    update_comprobante,
)
from app.infrastructure.database.queries.invbill.comprobante_detalle_queries import (
    list_comprobante_detalles,
    get_comprobante_detalle_by_id,
    create_comprobante_detalle,
    update_comprobante_detalle,
)

__all__ = [
    # Series
    "list_series",
    "get_serie_by_id",
    "create_serie",
    "update_serie",
    # Comprobantes
    "list_comprobantes",
    "get_comprobante_by_id",
    "create_comprobante",
    "update_comprobante",
    # Detalles
    "list_comprobante_detalles",
    "get_comprobante_detalle_by_id",
    "create_comprobante_detalle",
    "update_comprobante_detalle",
]
