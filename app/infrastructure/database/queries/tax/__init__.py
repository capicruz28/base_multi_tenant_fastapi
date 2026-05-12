# app/infrastructure/database/queries/tax/__init__.py
from app.infrastructure.database.queries.tax.libro_electronico_queries import (
    list_libro_electronico,
    get_libro_electronico_by_id,
    create_libro_electronico,
    update_libro_electronico,
    transition_libro_electronico_estado,
)

__all__ = [
    "list_libro_electronico",
    "get_libro_electronico_by_id",
    "create_libro_electronico",
    "update_libro_electronico",
    "transition_libro_electronico_estado",
]
