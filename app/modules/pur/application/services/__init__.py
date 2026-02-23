# app/modules/pur/application/services/__init__.py
"""
Servicios del módulo PUR (Compras).
"""

from app.modules.pur.application.services.proveedor_service import (
    list_proveedores_servicio,
    get_proveedor_servicio,
    create_proveedor_servicio,
    update_proveedor_servicio,
)
from app.modules.pur.application.services.contacto_service import (
    list_contactos_servicio,
    get_contacto_servicio,
    create_contacto_servicio,
    update_contacto_servicio,
)
from app.modules.pur.application.services.producto_proveedor_service import (
    list_productos_proveedor_servicio,
    get_producto_proveedor_servicio,
    create_producto_proveedor_servicio,
    update_producto_proveedor_servicio,
)
from app.modules.pur.application.services.solicitud_service import (
    list_solicitudes_servicio,
    get_solicitud_servicio,
    create_solicitud_servicio,
    update_solicitud_servicio,
)
from app.modules.pur.application.services.cotizacion_service import (
    list_cotizaciones_servicio,
    get_cotizacion_servicio,
    create_cotizacion_servicio,
    update_cotizacion_servicio,
)
from app.modules.pur.application.services.orden_compra_service import (
    list_ordenes_compra_servicio,
    get_orden_compra_servicio,
    create_orden_compra_servicio,
    update_orden_compra_servicio,
)
from app.modules.pur.application.services.recepcion_service import (
    list_recepciones_servicio,
    get_recepcion_servicio,
    create_recepcion_servicio,
    update_recepcion_servicio,
)

# Re-exportar como módulos para facilitar imports
from app.modules.pur.application.services import proveedor_service
from app.modules.pur.application.services import contacto_service
from app.modules.pur.application.services import producto_proveedor_service
from app.modules.pur.application.services import solicitud_service
from app.modules.pur.application.services import cotizacion_service
from app.modules.pur.application.services import orden_compra_service
from app.modules.pur.application.services import recepcion_service

__all__ = [
    # Proveedores
    "list_proveedores_servicio",
    "get_proveedor_servicio",
    "create_proveedor_servicio",
    "update_proveedor_servicio",
    # Contactos
    "list_contactos_servicio",
    "get_contacto_servicio",
    "create_contacto_servicio",
    "update_contacto_servicio",
    # Productos por proveedor
    "list_productos_proveedor_servicio",
    "get_producto_proveedor_servicio",
    "create_producto_proveedor_servicio",
    "update_producto_proveedor_servicio",
    # Solicitudes
    "list_solicitudes_servicio",
    "get_solicitud_servicio",
    "create_solicitud_servicio",
    "update_solicitud_servicio",
    # Cotizaciones
    "list_cotizaciones_servicio",
    "get_cotizacion_servicio",
    "create_cotizacion_servicio",
    "update_cotizacion_servicio",
    # Órdenes de compra
    "list_ordenes_compra_servicio",
    "get_orden_compra_servicio",
    "create_orden_compra_servicio",
    "update_orden_compra_servicio",
    # Recepciones
    "list_recepciones_servicio",
    "get_recepcion_servicio",
    "create_recepcion_servicio",
    "update_recepcion_servicio",
    # Módulos
    "proveedor_service",
    "contacto_service",
    "producto_proveedor_service",
    "solicitud_service",
    "cotizacion_service",
    "orden_compra_service",
    "recepcion_service",
]
