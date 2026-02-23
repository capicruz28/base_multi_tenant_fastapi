# app/modules/dms/application/services/__init__.py
from app.modules.dms.application.services.documento_service import (
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
