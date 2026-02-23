# app/infrastructure/database/queries/wfl/__init__.py
from app.infrastructure.database.queries.wfl.flujo_trabajo_queries import (
    list_flujo_trabajo,
    get_flujo_trabajo_by_id,
    create_flujo_trabajo,
    update_flujo_trabajo,
)

__all__ = [
    "list_flujo_trabajo",
    "get_flujo_trabajo_by_id",
    "create_flujo_trabajo",
    "update_flujo_trabajo",
]
