# app/infrastructure/database/queries/prc/__init__.py
"""
Queries para el módulo PRC (Gestión de Precios y Promociones).
"""

from app.infrastructure.database.queries.prc.lista_precio_queries import (
    list_listas_precio,
    get_lista_precio_by_id,
    create_lista_precio,
    update_lista_precio,
    list_lista_precio_detalles,
    get_lista_precio_detalle_by_id,
    create_lista_precio_detalle,
    update_lista_precio_detalle,
)
from app.infrastructure.database.queries.prc.promocion_queries import (
    list_promociones,
    get_promocion_by_id,
    create_promocion,
    update_promocion,
)

__all__ = [
    # Listas de Precio
    "list_listas_precio",
    "get_lista_precio_by_id",
    "create_lista_precio",
    "update_lista_precio",
    # Detalles de Lista de Precio
    "list_lista_precio_detalles",
    "get_lista_precio_detalle_by_id",
    "create_lista_precio_detalle",
    "update_lista_precio_detalle",
    # Promociones
    "list_promociones",
    "get_promocion_by_id",
    "create_promocion",
    "update_promocion",
]
