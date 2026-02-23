# app/modules/wms/application/services/__init__.py
"""
Servicios de aplicación para el módulo WMS (Warehouse Management System).
"""

from app.modules.wms.application.services.zona_almacen_service import (
    list_zonas_almacen,
    get_zona_almacen_by_id,
    create_zona_almacen,
    update_zona_almacen,
)
from app.modules.wms.application.services.ubicacion_service import (
    list_ubicaciones,
    get_ubicacion_by_id,
    create_ubicacion,
    update_ubicacion,
)
from app.modules.wms.application.services.stock_ubicacion_service import (
    list_stock_ubicaciones,
    get_stock_ubicacion_by_id,
    create_stock_ubicacion,
    update_stock_ubicacion,
)
from app.modules.wms.application.services.tarea_service import (
    list_tareas,
    get_tarea_by_id,
    create_tarea,
    update_tarea,
)

__all__ = [
    # Zonas de Almacén
    "list_zonas_almacen",
    "get_zona_almacen_by_id",
    "create_zona_almacen",
    "update_zona_almacen",
    # Ubicaciones
    "list_ubicaciones",
    "get_ubicacion_by_id",
    "create_ubicacion",
    "update_ubicacion",
    # Stock por Ubicación
    "list_stock_ubicaciones",
    "get_stock_ubicacion_by_id",
    "create_stock_ubicacion",
    "update_stock_ubicacion",
    # Tareas
    "list_tareas",
    "get_tarea_by_id",
    "create_tarea",
    "update_tarea",
]
