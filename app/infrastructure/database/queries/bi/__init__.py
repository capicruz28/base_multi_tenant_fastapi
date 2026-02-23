# app/infrastructure/database/queries/bi/__init__.py
from app.infrastructure.database.queries.bi.reporte_queries import (
    list_reporte,
    get_reporte_by_id,
    create_reporte,
    update_reporte,
)

__all__ = [
    "list_reporte",
    "get_reporte_by_id",
    "create_reporte",
    "update_reporte",
]
