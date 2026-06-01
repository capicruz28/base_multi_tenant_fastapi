"""
Contexto de empresa activa (multi-empresa) por request.

Se establece desde el JWT (claim empresa_id) en las dependencias de FastAPI,
siguiendo el mismo patrón que cliente_id vía TenantMiddleware.
"""

from contextvars import ContextVar
from typing import Any, Optional
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

current_empresa_id: ContextVar[Optional[UUID]] = ContextVar(
    "current_empresa_id",
    default=None,
)


def coerce_empresa_id(value: Any) -> Optional[UUID]:
    """Normaliza empresa_id desde JWT, BD o parámetro explícito."""
    if value is None:
        return None
    if isinstance(value, UUID):
        null_uuid = UUID("00000000-0000-0000-0000-000000000000")
        return None if value == null_uuid else value
    try:
        parsed = UUID(str(value).strip())
        null_uuid = UUID("00000000-0000-0000-0000-000000000000")
        return None if parsed == null_uuid else parsed
    except (ValueError, AttributeError, TypeError):
        return None


def resolve_empresa_id(explicit: Optional[UUID] = None) -> Optional[UUID]:
    """Prioridad: parámetro explícito > ContextVar del request."""
    if explicit is not None:
        return coerce_empresa_id(explicit)
    return try_get_current_empresa_id()


def try_get_current_empresa_id() -> Optional[UUID]:
    return current_empresa_id.get()


def set_current_empresa_id(empresa_id: Optional[UUID]) -> Any:
    normalized = coerce_empresa_id(empresa_id)
    token = current_empresa_id.set(normalized)
    if normalized:
        logger.debug("[EMPRESA_CTX] empresa_id establecido: %s", normalized)
    return token


def reset_current_empresa_id(token: Any) -> None:
    current_empresa_id.reset(token)
    logger.debug("[EMPRESA_CTX] empresa_id limpiado")


def sql_empresa_filter_usuario_rol(alias: str = "ur") -> str:
    """
    Fragmento SQL: roles de la empresa activa o globales (empresa_id IS NULL).
    Requiere bindparam :empresa_id.
    """
    return f" AND ({alias}.empresa_id IS NULL OR {alias}.empresa_id = :empresa_id)"


def sql_empresa_filter_usuario_rol_qmark(alias: str = "ur") -> str:
    """
    Mismo criterio que sql_empresa_filter_usuario_rol para queries con placeholders ``?``.
    Añadir el UUID de empresa como bind adicional en el orden de la cláusula WHERE.
    """
    return f" AND ({alias}.empresa_id IS NULL OR {alias}.empresa_id = ?)"
