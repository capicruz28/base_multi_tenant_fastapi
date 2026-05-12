# app/modules/mnt/application/services/__init__.py
from app.modules.mnt.application.services.activo_service import (
    list_activo,
    get_activo_by_id,
    create_activo,
    update_activo,
    activar_activo,
    desactivar_activo,
)
from app.modules.mnt.application.services.plan_mantenimiento_service import (
    list_plan_mantenimiento,
    get_plan_mantenimiento_by_id,
    create_plan_mantenimiento,
    update_plan_mantenimiento,
    activar_plan_mantenimiento,
    desactivar_plan_mantenimiento,
)
from app.modules.mnt.application.services.orden_trabajo_service import (
    list_orden_trabajo,
    get_orden_trabajo_by_id,
    create_orden_trabajo,
    update_orden_trabajo,
    programar_orden_trabajo,
    iniciar_orden_trabajo,
    pausar_orden_trabajo,
    reanudar_orden_trabajo,
    completar_orden_trabajo,
    cancelar_orden_trabajo,
    cerrar_orden_trabajo,
)
from app.modules.mnt.application.services.historial_mantenimiento_service import (
    list_historial_mantenimiento,
    get_historial_mantenimiento_by_id,
    create_historial_mantenimiento,
    update_historial_mantenimiento,
)

__all__ = [
    # mnt_activo
    "list_activo",
    "get_activo_by_id",
    "create_activo",
    "update_activo",
    "activar_activo",
    "desactivar_activo",
    # mnt_plan_mantenimiento
    "list_plan_mantenimiento",
    "get_plan_mantenimiento_by_id",
    "create_plan_mantenimiento",
    "update_plan_mantenimiento",
    "activar_plan_mantenimiento",
    "desactivar_plan_mantenimiento",
    # mnt_orden_trabajo
    "list_orden_trabajo",
    "get_orden_trabajo_by_id",
    "create_orden_trabajo",
    "update_orden_trabajo",
    "programar_orden_trabajo",
    "iniciar_orden_trabajo",
    "pausar_orden_trabajo",
    "reanudar_orden_trabajo",
    "completar_orden_trabajo",
    "cancelar_orden_trabajo",
    "cerrar_orden_trabajo",
    # mnt_historial_mantenimiento (legacy: write conservado por compatibilidad)
    "list_historial_mantenimiento",
    "get_historial_mantenimiento_by_id",
    "create_historial_mantenimiento",
    "update_historial_mantenimiento",
]
