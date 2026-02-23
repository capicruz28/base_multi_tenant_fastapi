# app/infrastructure/database/queries/pm/__init__.py
from app.infrastructure.database.queries.pm.proyecto_queries import (
    list_proyecto,
    get_proyecto_by_id,
    create_proyecto,
    update_proyecto,
)

__all__ = [
    "list_proyecto",
    "get_proyecto_by_id",
    "create_proyecto",
    "update_proyecto",
]
