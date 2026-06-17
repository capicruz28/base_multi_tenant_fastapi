# app/modules/inv/application/services/__init__.py
"""
Servicios del módulo INV (Inventarios).
"""

from app.modules.inv.application.services.categoria_service import (
    list_categorias_servicio,
    get_categoria_servicio,
    create_categoria_servicio,
    update_categoria_servicio,
)
from app.modules.inv.application.services.unidad_medida_service import (
    list_unidades_medida_servicio,
    get_unidad_medida_servicio,
    create_unidad_medida_servicio,
    update_unidad_medida_servicio,
)
from app.modules.inv.application.services.producto_service import (
    list_productos_servicio,
    get_producto_servicio,
    create_producto_servicio,
    update_producto_servicio,
)
from app.modules.inv.application.services.almacen_service import (
    list_almacenes_servicio,
    get_almacen_servicio,
    create_almacen_servicio,
    update_almacen_servicio,
)
from app.modules.inv.application.services.stock_service import (
    list_stocks_servicio,
    get_stock_servicio,
    get_stock_by_producto_almacen_servicio,
    create_stock_servicio,
    update_stock_servicio,
)
from app.modules.inv.application.services.tipo_movimiento_service import (
    list_tipos_movimiento_servicio,
    get_tipo_movimiento_servicio,
    create_tipo_movimiento_servicio,
    update_tipo_movimiento_servicio,
)
from app.modules.inv.application.services.movimiento_service import (
    list_movimientos_servicio,
    get_movimiento_servicio,
    create_movimiento_servicio,
    update_movimiento_servicio,
    get_movimiento_con_detalles_servicio,
    create_movimiento_con_detalles_servicio,
    update_movimiento_con_detalles_servicio,
)
from app.modules.inv.application.services.inventario_fisico_service import (
    list_inventarios_fisicos_servicio,
    get_inventario_fisico_servicio,
    create_inventario_fisico_servicio,
    update_inventario_fisico_servicio,
    anular_inventario_fisico_servicio,
    finalizar_inventario_fisico_servicio,
    get_inventario_fisico_con_detalles_servicio,
    create_inventario_fisico_con_detalles_servicio,
    update_inventario_fisico_con_detalles_servicio,
)
from app.modules.inv.application.services.movimiento_detalle_service import (
    list_movimientos_detalle_servicio,
    get_movimiento_detalle_servicio,
    create_movimiento_detalle_servicio,
    update_movimiento_detalle_servicio,
)
from app.modules.inv.application.services.inventario_fisico_detalle_service import (
    list_inventarios_fisicos_detalle_servicio,
    get_inventario_fisico_detalle_servicio,
    create_inventario_fisico_detalle_servicio,
    update_inventario_fisico_detalle_servicio,
)
from app.modules.inv.application.services.movimiento_proceso_service import (
    procesar_movimiento_servicio,
    autorizar_movimiento_servicio,
    anular_movimiento_servicio,
    estornar_movimiento_servicio,
)
from app.modules.inv.application.services.inventario_fisico_aprobacion_service import (
    aprobar_inventario_fisico_servicio,
)

# Re-exportar como módulos para facilitar imports
from app.modules.inv.application.services import categoria_service
from app.modules.inv.application.services import unidad_medida_service
from app.modules.inv.application.services import producto_service
from app.modules.inv.application.services import almacen_service
from app.modules.inv.application.services import stock_service
from app.modules.inv.application.services import tipo_movimiento_service
from app.modules.inv.application.services import movimiento_service
from app.modules.inv.application.services import inventario_fisico_service
from app.modules.inv.application.services import movimiento_detalle_service
from app.modules.inv.application.services import inventario_fisico_detalle_service
from app.modules.inv.application.services import movimiento_proceso_service
from app.modules.inv.application.services import inventario_fisico_aprobacion_service

__all__ = [
    # Categorías
    "list_categorias_servicio",
    "get_categoria_servicio",
    "create_categoria_servicio",
    "update_categoria_servicio",
    # Unidades de medida
    "list_unidades_medida_servicio",
    "get_unidad_medida_servicio",
    "create_unidad_medida_servicio",
    "update_unidad_medida_servicio",
    # Productos
    "list_productos_servicio",
    "get_producto_servicio",
    "create_producto_servicio",
    "update_producto_servicio",
    # Almacenes
    "list_almacenes_servicio",
    "get_almacen_servicio",
    "create_almacen_servicio",
    "update_almacen_servicio",
    # Stock
    "list_stocks_servicio",
    "get_stock_servicio",
    "get_stock_by_producto_almacen_servicio",
    "create_stock_servicio",
    "update_stock_servicio",
    # Tipos de movimiento
    "list_tipos_movimiento_servicio",
    "get_tipo_movimiento_servicio",
    "create_tipo_movimiento_servicio",
    "update_tipo_movimiento_servicio",
    # Movimientos
    "list_movimientos_servicio",
    "get_movimiento_servicio",
    "create_movimiento_servicio",
    "update_movimiento_servicio",
    # Movimientos con detalle embebido
    "get_movimiento_con_detalles_servicio",
    "create_movimiento_con_detalles_servicio",
    "update_movimiento_con_detalles_servicio",
    # Inventario físico
    "list_inventarios_fisicos_servicio",
    "get_inventario_fisico_servicio",
    "create_inventario_fisico_servicio",
    "update_inventario_fisico_servicio",
    "anular_inventario_fisico_servicio",
    "finalizar_inventario_fisico_servicio",
    # Inventario físico con detalle embebido
    "get_inventario_fisico_con_detalles_servicio",
    "create_inventario_fisico_con_detalles_servicio",
    "update_inventario_fisico_con_detalles_servicio",
    # Movimiento detalle
    "list_movimientos_detalle_servicio",
    "get_movimiento_detalle_servicio",
    "create_movimiento_detalle_servicio",
    "update_movimiento_detalle_servicio",
    # Inventario físico detalle
    "list_inventarios_fisicos_detalle_servicio",
    "get_inventario_fisico_detalle_servicio",
    "create_inventario_fisico_detalle_servicio",
    "update_inventario_fisico_detalle_servicio",
    # Proceso movimiento
    "procesar_movimiento_servicio",
    "autorizar_movimiento_servicio",
    "anular_movimiento_servicio",
    "estornar_movimiento_servicio",
    # Aprobación inventario físico
    "aprobar_inventario_fisico_servicio",
    # Módulos
    "categoria_service",
    "unidad_medida_service",
    "producto_service",
    "almacen_service",
    "stock_service",
    "tipo_movimiento_service",
    "movimiento_service",
    "inventario_fisico_service",
    "movimiento_detalle_service",
    "inventario_fisico_detalle_service",
    "movimiento_proceso_service",
    "inventario_fisico_aprobacion_service",
]
