# app/modules/mfg/application/services/__init__.py
from app.modules.mfg.application.services.centro_trabajo_service import (
    list_centros_trabajo,
    get_centro_trabajo_by_id,
    create_centro_trabajo,
    update_centro_trabajo,
)
from app.modules.mfg.application.services.operacion_service import (
    list_operaciones,
    get_operacion_by_id,
    create_operacion,
    update_operacion,
)
from app.modules.mfg.application.services.lista_materiales_service import (
    list_listas_materiales,
    get_lista_materiales_by_id,
    create_lista_materiales,
    update_lista_materiales,
)
from app.modules.mfg.application.services.lista_materiales_detalle_service import (
    list_lista_materiales_detalles,
    get_lista_materiales_detalle_by_id,
    create_lista_materiales_detalle,
    update_lista_materiales_detalle,
)
from app.modules.mfg.application.services.ruta_fabricacion_service import (
    list_rutas_fabricacion,
    get_ruta_fabricacion_by_id,
    create_ruta_fabricacion,
    update_ruta_fabricacion,
)
from app.modules.mfg.application.services.ruta_fabricacion_detalle_service import (
    list_ruta_fabricacion_detalles,
    get_ruta_fabricacion_detalle_by_id,
    create_ruta_fabricacion_detalle,
    update_ruta_fabricacion_detalle,
)
from app.modules.mfg.application.services.orden_produccion_service import (
    list_ordenes_produccion,
    get_orden_produccion_by_id,
    create_orden_produccion,
    update_orden_produccion,
)
from app.modules.mfg.application.services.orden_produccion_operacion_service import (
    list_orden_produccion_operaciones,
    get_orden_produccion_operacion_by_id,
    create_orden_produccion_operacion,
    update_orden_produccion_operacion,
)
from app.modules.mfg.application.services.consumo_materiales_service import (
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
