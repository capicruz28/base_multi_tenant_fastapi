# app/infrastructure/database/queries/mfg/__init__.py
"""Queries para el módulo MFG (Manufactura y Producción)."""
from app.infrastructure.database.queries.mfg.centro_trabajo_queries import (
    list_centros_trabajo,
    get_centro_trabajo_by_id,
    create_centro_trabajo,
    update_centro_trabajo,
)
from app.infrastructure.database.queries.mfg.operacion_queries import (
    list_operaciones,
    get_operacion_by_id,
    create_operacion,
    update_operacion,
)
from app.infrastructure.database.queries.mfg.lista_materiales_queries import (
    list_listas_materiales,
    get_lista_materiales_by_id,
    create_lista_materiales,
    update_lista_materiales,
)
from app.infrastructure.database.queries.mfg.lista_materiales_detalle_queries import (
    list_lista_materiales_detalles,
    get_lista_materiales_detalle_by_id,
    create_lista_materiales_detalle,
    update_lista_materiales_detalle,
)
from app.infrastructure.database.queries.mfg.ruta_fabricacion_queries import (
    list_rutas_fabricacion,
    get_ruta_fabricacion_by_id,
    create_ruta_fabricacion,
    update_ruta_fabricacion,
)
from app.infrastructure.database.queries.mfg.ruta_fabricacion_detalle_queries import (
    list_ruta_fabricacion_detalles,
    get_ruta_fabricacion_detalle_by_id,
    create_ruta_fabricacion_detalle,
    update_ruta_fabricacion_detalle,
)
from app.infrastructure.database.queries.mfg.orden_produccion_queries import (
    list_ordenes_produccion,
    get_orden_produccion_by_id,
    create_orden_produccion,
    update_orden_produccion,
)
from app.infrastructure.database.queries.mfg.orden_produccion_operacion_queries import (
    list_orden_produccion_operaciones,
    get_orden_produccion_operacion_by_id,
    create_orden_produccion_operacion,
    update_orden_produccion_operacion,
)
from app.infrastructure.database.queries.mfg.consumo_materiales_queries import (
    list_consumo_materiales,
    get_consumo_materiales_by_id,
    create_consumo_materiales,
    update_consumo_materiales,
)

__all__ = [
    "list_centros_trabajo",
    "get_centro_trabajo_by_id",
    "create_centro_trabajo",
    "update_centro_trabajo",
    "list_operaciones",
    "get_operacion_by_id",
    "create_operacion",
    "update_operacion",
    "list_listas_materiales",
    "get_lista_materiales_by_id",
    "create_lista_materiales",
    "update_lista_materiales",
    "list_lista_materiales_detalles",
    "get_lista_materiales_detalle_by_id",
    "create_lista_materiales_detalle",
    "update_lista_materiales_detalle",
    "list_rutas_fabricacion",
    "get_ruta_fabricacion_by_id",
    "create_ruta_fabricacion",
    "update_ruta_fabricacion",
    "list_ruta_fabricacion_detalles",
    "get_ruta_fabricacion_detalle_by_id",
    "create_ruta_fabricacion_detalle",
    "update_ruta_fabricacion_detalle",
    "list_ordenes_produccion",
    "get_orden_produccion_by_id",
    "create_orden_produccion",
    "update_orden_produccion",
    "list_orden_produccion_operaciones",
    "get_orden_produccion_operacion_by_id",
    "create_orden_produccion_operacion",
    "update_orden_produccion_operacion",
    "list_consumo_materiales",
    "get_consumo_materiales_by_id",
    "create_consumo_materiales",
    "update_consumo_materiales",
]
