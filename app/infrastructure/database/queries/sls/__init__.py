# app/infrastructure/database/queries/sls/__init__.py
"""
Queries para el módulo SLS (Ventas).
"""

from app.infrastructure.database.queries.sls.cliente_queries import (
    list_clientes,
    get_cliente_by_id,
    create_cliente,
    update_cliente,
    set_cliente_activo,
)
from app.infrastructure.database.queries.sls.contacto_queries import (
    list_contactos,
    get_contacto_by_id,
    create_contacto,
    update_contacto,
)
from app.infrastructure.database.queries.sls.direccion_queries import (
    list_direcciones,
    get_direccion_by_id,
    create_direccion,
    update_direccion,
)
from app.infrastructure.database.queries.sls.cotizacion_queries import (
    list_cotizaciones,
    get_cotizacion_by_id,
    create_cotizacion,
    update_cotizacion,
)
from app.infrastructure.database.queries.sls.cotizacion_detalle_queries import (
    list_detalle_by_cotizacion_id,
    replace_detalle_cotizacion,
)
from app.infrastructure.database.queries.sls.pedido_queries import (
    list_pedidos,
    get_pedido_by_id,
    create_pedido,
    update_pedido,
)
from app.infrastructure.database.queries.sls.pedido_detalle_queries import (
    list_detalle_by_pedido_id,
    replace_detalle_pedido,
)

__all__ = [
    # Clientes
    "list_clientes",
    "get_cliente_by_id",
    "create_cliente",
    "update_cliente",
    "set_cliente_activo",
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
    "list_detalle_by_cotizacion_id",
    "replace_detalle_cotizacion",
    # Pedidos
    "list_pedidos",
    "get_pedido_by_id",
    "create_pedido",
    "update_pedido",
    "list_detalle_by_pedido_id",
    "replace_detalle_pedido",
]
