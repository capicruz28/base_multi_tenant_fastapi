# app/infrastructure/database/queries/inv/__init__.py
"""
Queries para el módulo INV (Inventarios).
"""

from app.infrastructure.database.queries.inv.categoria_queries import (
    list_categorias,
    get_categoria_by_id,
    create_categoria,
    update_categoria,
)
from app.infrastructure.database.queries.inv.unidad_medida_queries import (
    list_unidades_medida,
    get_unidad_medida_by_id,
    create_unidad_medida,
    update_unidad_medida,
)
from app.infrastructure.database.queries.inv.producto_queries import (
    list_productos,
    get_producto_by_id,
    create_producto,
    update_producto,
)
from app.infrastructure.database.queries.inv.almacen_queries import (
    list_almacenes,
    get_almacen_by_id,
    create_almacen,
    update_almacen,
)
from app.infrastructure.database.queries.inv.stock_queries import (
    list_stocks,
    get_stock_by_id,
    get_stock_by_producto_almacen,
    create_stock,
    update_stock,
)
from app.infrastructure.database.queries.inv.tipo_movimiento_queries import (
    list_tipos_movimiento,
    get_tipo_movimiento_by_id,
    create_tipo_movimiento,
    update_tipo_movimiento,
)
from app.infrastructure.database.queries.inv.movimiento_queries import (
    list_movimientos,
    get_movimiento_by_id,
    create_movimiento,
    update_movimiento,
)
from app.infrastructure.database.queries.inv.inventario_fisico_queries import (
    list_inventarios_fisicos,
    get_inventario_fisico_by_id,
    create_inventario_fisico,
    update_inventario_fisico,
)

__all__ = [
    # Categorías
    "list_categorias",
    "get_categoria_by_id",
    "create_categoria",
    "update_categoria",
    # Unidades de medida
    "list_unidades_medida",
    "get_unidad_medida_by_id",
    "create_unidad_medida",
    "update_unidad_medida",
    # Productos
    "list_productos",
    "get_producto_by_id",
    "create_producto",
    "update_producto",
    # Almacenes
    "list_almacenes",
    "get_almacen_by_id",
    "create_almacen",
    "update_almacen",
    # Stock
    "list_stocks",
    "get_stock_by_id",
    "get_stock_by_producto_almacen",
    "create_stock",
    "update_stock",
    # Tipos de movimiento
    "list_tipos_movimiento",
    "get_tipo_movimiento_by_id",
    "create_tipo_movimiento",
    "update_tipo_movimiento",
    # Movimientos
    "list_movimientos",
    "get_movimiento_by_id",
    "create_movimiento",
    "update_movimiento",
    # Inventario físico
    "list_inventarios_fisicos",
    "get_inventario_fisico_by_id",
    "create_inventario_fisico",
    "update_inventario_fisico",
]
