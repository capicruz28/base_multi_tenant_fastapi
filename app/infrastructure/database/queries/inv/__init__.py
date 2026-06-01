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
    get_producto_by_sku,
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
    list_stock_alertas_bajo_minimo,
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
    get_movimiento_con_detalles,
)
from app.infrastructure.database.queries.inv.movimiento_detalle_queries import (
    list_movimientos_detalle,
    get_movimiento_detalle_by_id,
    create_movimiento_detalle,
    update_movimiento_detalle,
)
from app.infrastructure.database.queries.inv.inventario_fisico_queries import (
    list_inventarios_fisicos,
    get_inventario_fisico_by_id,
    create_inventario_fisico,
    update_inventario_fisico,
    get_inventario_fisico_con_detalles,
)
from app.infrastructure.database.queries.inv.inventario_fisico_detalle_queries import (
    list_inventarios_fisicos_detalle,
    get_inventario_fisico_detalle_by_id,
    create_inventario_fisico_detalle,
    update_inventario_fisico_detalle,
)
from app.infrastructure.database.queries.inv.kardex_queries import (
    list_kardex,
)
from app.infrastructure.database.queries.inv.moneda_queries import (
    get_moneda_by_codigo,
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
    "get_producto_by_sku",
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
    "list_stock_alertas_bajo_minimo",
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
    "get_movimiento_con_detalles",
    # Movimientos detalle
    "list_movimientos_detalle",
    "get_movimiento_detalle_by_id",
    "create_movimiento_detalle",
    "update_movimiento_detalle",
    # Inventario físico
    "list_inventarios_fisicos",
    "get_inventario_fisico_by_id",
    "create_inventario_fisico",
    "update_inventario_fisico",
    "get_inventario_fisico_con_detalles",
    # Inventario físico detalle
    "list_inventarios_fisicos_detalle",
    "get_inventario_fisico_detalle_by_id",
    "create_inventario_fisico_detalle",
    "update_inventario_fisico_detalle",
    # Kardex
    "list_kardex",
    # Moneda (cat_moneda)
    "get_moneda_by_codigo",
]
