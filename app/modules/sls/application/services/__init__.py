# app/modules/sls/application/services/__init__.py
"""
Servicios de aplicación para el módulo SLS (Ventas).
"""

from app.modules.sls.application.services.cliente_service import (
    list_clientes,
    get_cliente_by_id,
    create_cliente,
    update_cliente,
)
from app.modules.sls.application.services.contacto_service import (
    list_contactos,
    get_contacto_by_id,
    create_contacto,
    update_contacto,
)
from app.modules.sls.application.services.direccion_service import (
    list_direcciones,
    get_direccion_by_id,
    create_direccion,
    update_direccion,
)
from app.modules.sls.application.services.cotizacion_service import (
    list_cotizaciones,
    get_cotizacion_by_id,
    create_cotizacion,
    update_cotizacion,
)
from app.modules.sls.application.services.pedido_service import (
    list_pedidos,
    get_pedido_by_id,
    create_pedido,
    update_pedido,
)

__all__ = [
    # Clientes
    "list_clientes",
    "get_cliente_by_id",
    "create_cliente",
    "update_cliente",
    # Contactos
    "list_contactos",
    "get_contacto_by_id",
    "create_contacto",
    "update_contacto",
    # Direcciones
    "list_direcciones",
    "get_direccion_by_id",
    "create_direccion",
    "update_direccion",
    # Cotizaciones
    "list_cotizaciones",
    "get_cotizacion_by_id",
    "create_cotizacion",
    "update_cotizacion",
    # Pedidos
    "list_pedidos",
    "get_pedido_by_id",
    "create_pedido",
    "update_pedido",
]
