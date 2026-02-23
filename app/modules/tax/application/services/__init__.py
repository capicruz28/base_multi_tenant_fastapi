# app/modules/tax/application/services/__init__.py
from app.modules.tax.application.services.libro_electronico_service import (
    list_libro_electronico,
    get_libro_electronico_by_id,
    create_libro_electronico,
    update_libro_electronico,
)

__all__ = [
    "list_libro_electronico",
    "get_libro_electronico_by_id",
    "create_libro_electronico",
    "update_libro_electronico",
]
