# app/infrastructure/database/queries/dms/__init__.py
from app.infrastructure.database.queries.dms.documento_queries import (
    list_documento,
    get_documento_by_id,
    create_documento,
    update_documento,
)

__all__ = [
    "list_documento",
    "get_documento_by_id",
    "create_documento",
    "update_documento",
]
