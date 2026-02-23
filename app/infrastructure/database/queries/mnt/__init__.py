# app/infrastructure/database/queries/mnt/__init__.py
from app.infrastructure.database.queries.mnt.activo_queries import (
    list_activo,
    get_activo_by_id,
    create_activo,
    update_activo,
)
from app.infrastructure.database.queries.mnt.plan_mantenimiento_queries import (
    list_plan_mantenimiento,
    get_plan_mantenimiento_by_id,
    create_plan_mantenimiento,
    update_plan_mantenimiento,
)
from app.infrastructure.database.queries.mnt.orden_trabajo_queries import (
    list_orden_trabajo,
    get_orden_trabajo_by_id,
    create_orden_trabajo,
    update_orden_trabajo,
)
from app.infrastructure.database.queries.mnt.historial_mantenimiento_queries import (
    list_historial_mantenimiento,
    get_historial_mantenimiento_by_id,
    create_historial_mantenimiento,
    update_historial_mantenimiento,
)

__all__ = [
    "list_activo",
    "get_activo_by_id",
    "create_activo",
    "update_activo",
    "list_plan_mantenimiento",
    "get_plan_mantenimiento_by_id",
    "create_plan_mantenimiento",
    "update_plan_mantenimiento",
    "list_orden_trabajo",
    "get_orden_trabajo_by_id",
    "create_orden_trabajo",
    "update_orden_trabajo",
    "list_historial_mantenimiento",
    "get_historial_mantenimiento_by_id",
    "create_historial_mantenimiento",
    "update_historial_mantenimiento",
]
