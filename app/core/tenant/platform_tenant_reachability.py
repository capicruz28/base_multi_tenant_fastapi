"""
F13-J1 — Preflight de reachability tenant_data para operaciones Platform (F13-F1 §7).

Envuelve ``get_connection_metadata_async`` sin relajar RI-39 ni modificar routing/OSR.
Clasifica únicamente fallos de resolución/validación de metadata (fail-soft L6).

No captura errores de negocio, SQL de aplicación ni RBAC — esos se propagan.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from app.core.exceptions import DatabaseError
from app.core.tenant.routing import (
    DEDICATED_ROUTE_FAIL_CLOSED,
    OPERATION_CLASS_TENANT_DATA,
    get_connection_metadata_async,
)

logger = logging.getLogger(__name__)


class ReachabilityStatus(str, Enum):
    """Estado de alcanzabilidad tenant_data para proyección Platform."""

    REACHABLE = "reachable"
    METADATA_INCOMPLETE = "metadata_incomplete"
    NOT_CONFIGURED = "not_configured"
    UNEXPECTED_ERROR = "unexpected_error"


@dataclass(frozen=True, slots=True)
class ReachabilityResult:
    """Resultado de preflight — sin abrir sesión tenant_data si no es REACHABLE."""

    cliente_id: UUID
    status: ReachabilityStatus
    metadata: Optional[Dict[str, Any]] = None
    internal_code: Optional[str] = None
    message: Optional[str] = None


def _classify_dedicated_route_fail_closed(exc: DatabaseError) -> ReachabilityStatus:
    """Mapea RI-39 ``DEDICATED_ROUTE_FAIL_CLOSED`` a status fail-soft."""
    detail = (exc.detail or "").lower()
    if any(
        token in detail
        for token in (
            "storage endpoint ausente",
            "no disponible para installation mode dedicated",
            "credenciales inválidas",
            "credenciales invalidas",
        )
    ):
        return ReachabilityStatus.NOT_CONFIGURED
    if any(
        token in detail
        for token in (
            "campos ausentes",
            "database_type=",
            "no puede enrutar",
        )
    ):
        return ReachabilityStatus.METADATA_INCOMPLETE
    return ReachabilityStatus.METADATA_INCOMPLETE


async def check_platform_tenant_reachability(
    cliente_id: UUID,
    *,
    operation_class: str = OPERATION_CLASS_TENANT_DATA,
) -> ReachabilityResult:
    """
    Evalúa si el target puede resolver metadata tenant_data vía routing (RI-39 intacto).

    Returns:
        ReachabilityResult con ``metadata`` poblado solo si status == REACHABLE.

    Raises:
        DatabaseError: Errores de BD distintos de ``DEDICATED_ROUTE_FAIL_CLOSED``.
        CustomException / demás: no capturados (negocio, RBAC, SQL app).
    """
    try:
        metadata = await get_connection_metadata_async(cliente_id, operation_class)
        return ReachabilityResult(
            cliente_id=cliente_id,
            status=ReachabilityStatus.REACHABLE,
            metadata=dict(metadata),
        )
    except DatabaseError as exc:
        if exc.internal_code != DEDICATED_ROUTE_FAIL_CLOSED:
            raise
        status = _classify_dedicated_route_fail_closed(exc)
        logger.debug(
            "[PLATFORM_REACHABILITY] cliente_id=%s status=%s code=%s",
            cliente_id,
            status.value,
            exc.internal_code,
        )
        return ReachabilityResult(
            cliente_id=cliente_id,
            status=status,
            internal_code=exc.internal_code,
            message=exc.detail,
        )
    except Exception as exc:
        if isinstance(exc, DatabaseError):
            raise
        logger.warning(
            "[PLATFORM_REACHABILITY] Unexpected error cliente_id=%s: %s",
            cliente_id,
            exc,
            exc_info=False,
        )
        return ReachabilityResult(
            cliente_id=cliente_id,
            status=ReachabilityStatus.UNEXPECTED_ERROR,
            message=str(exc),
        )


__all__ = [
    "ReachabilityResult",
    "ReachabilityStatus",
    "check_platform_tenant_reachability",
]
