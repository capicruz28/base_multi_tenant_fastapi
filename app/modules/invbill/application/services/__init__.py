# app/modules/invbill/application/services/__init__.py
"""
Servicios de aplicación para el módulo INV_BILL (Facturación Electrónica).
"""

from app.modules.invbill.application.services.serie_service import (
    list_series,
    get_serie_by_id,
    create_serie,
    update_serie,
)
from app.modules.invbill.application.services.comprobante_service import (
    list_comprobantes,
    get_comprobante_by_id,
    create_comprobante,
    update_comprobante,
)
from app.modules.invbill.application.services.comprobante_detalle_service import (
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
