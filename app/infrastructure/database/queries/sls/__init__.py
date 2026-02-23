# app/infrastructure/database/queries/sls/__init__.py
"""
Queries para el módulo SLS (Ventas).
"""

from app.infrastructure.database.queries.sls.cliente_queries import (
    list_clientes,
    get_cliente_by_id,
    create_cliente,
    update_cliente,
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
from app.infrastructure.database.queries.sls.pedido_queries import (
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
