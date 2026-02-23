# app/infrastructure/database/queries/svc/__init__.py
from app.infrastructure.database.queries.svc.orden_servicio_queries import (
    list_orden_servicio,
    get_orden_servicio_by_id,
    create_orden_servicio,
    update_orden_servicio,
)

__all__ = [
    "list_orden_servicio",
    "get_orden_servicio_by_id",
    "create_orden_servicio",
    "update_orden_servicio",
]
