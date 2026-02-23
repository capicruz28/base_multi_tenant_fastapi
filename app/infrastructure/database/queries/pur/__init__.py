# app/infrastructure/database/queries/pur/__init__.py
"""
Queries para el módulo PUR (Compras).
"""

from app.infrastructure.database.queries.pur.proveedor_queries import (
    list_proveedores,
    get_proveedor_by_id,
    create_proveedor,
    update_proveedor,
)
from app.infrastructure.database.queries.pur.contacto_queries import (
    list_contactos,
    get_contacto_by_id,
    create_contacto,
    update_contacto,
)
from app.infrastructure.database.queries.pur.producto_proveedor_queries import (
    list_productos_proveedor,
    get_producto_proveedor_by_id,
    create_producto_proveedor,
    update_producto_proveedor,
)
from app.infrastructure.database.queries.pur.solicitud_queries import (
    list_solicitudes,
    get_solicitud_by_id,
    create_solicitud,
    update_solicitud,
)
from app.infrastructure.database.queries.pur.cotizacion_queries import (
    list_cotizaciones,
    get_cotizacion_by_id,
    create_cotizacion,
    update_cotizacion,
)
from app.infrastructure.database.queries.pur.orden_compra_queries import (
    list_ordenes_compra,
    get_orden_compra_by_id,
    create_orden_compra,
    update_orden_compra,
)
from app.infrastructure.database.queries.pur.recepcion_queries import (
    list_recepciones,
    get_recepcion_by_id,
    create_recepcion,
    update_recepcion,
)

__all__ = [
    # Proveedores
    "list_proveedores",
    "get_proveedor_by_id",
    "create_proveedor",
    "update_proveedor",
    # Contactos
    "list_contactos",
    "get_contacto_by_id",
    "create_contacto",
    "update_contacto",
    # Productos por proveedor
    "list_productos_proveedor",
    "get_producto_proveedor_by_id",
    "create_producto_proveedor",
    "update_producto_proveedor",
    # Solicitudes
    "list_solicitudes",
    "get_solicitud_by_id",
    "create_solicitud",
    "update_solicitud",
    # Cotizaciones
    "list_cotizaciones",
    "get_cotizacion_by_id",
    "create_cotizacion",
    "update_cotizacion",
    # Órdenes de compra
    "list_ordenes_compra",
    "get_orden_compra_by_id",
    "create_orden_compra",
    "update_orden_compra",
    # Recepciones
    "list_recepciones",
    "get_recepcion_by_id",
    "create_recepcion",
    "update_recepcion",
]
