# app/infrastructure/database/queries/dms/__init__.py
from app.infrastructure.database.queries.dms.documento_queries import (
    list_documento,
    get_documento_by_id,
    get_documento_by_id_empresa,
    create_documento,
    update_documento,
    update_documento_empresa,
    archivar_documento,
    restaurar_documento,
    eliminar_documento,
)

__all__ = [
    "list_documento",
    "get_documento_by_id",
    "get_documento_by_id_empresa",
    "create_documento",
    "update_documento",
    "update_documento_empresa",
    "archivar_documento",
    "restaurar_documento",
    "eliminar_documento",
]
