"""
Servicio de rotación atómica de refresh tokens (IAM-BE-SESSIONS-P1-04).

Infraestructura de rotación atómica; conectada a POST /auth/refresh/ (P1-04-IMPL-02)
y AuthService.cambiar_empresa_sesion() (P1-04-IMPL-03).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
import logging

from app.core.application.unit_of_work import UnitOfWork
from app.core.config import settings
from app.core.exceptions import DatabaseError
from app.infrastructure.database.queries.auth.refresh_token_rotate_queries_core import (
    rotate_refresh_token_core,
)
from app.modules.auth.application.services.auth_config_service import (
    leer_session_idle_timeout_minutos,
)
from app.modules.auth.application.services.refresh_token_service import RefreshTokenService
from app.modules.auth.application.session.rotate_result import RotateOutcome, RotateResult

logger = logging.getLogger(__name__)


def _coerce_uuid(value) -> Optional[UUID]:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (ValueError, TypeError):
        return None


def build_rotate_result(
    *,
    cliente_id: UUID,
    core_result: dict,
) -> RotateResult:
    """Construye RotateResult desde el dict retornado por rotate_refresh_token_core."""
    outcome = core_result.get("outcome", RotateOutcome.NOT_FOUND)
    if isinstance(outcome, str):
        outcome = RotateOutcome(outcome)

    return RotateResult(
        outcome=outcome,
        cliente_id=cliente_id,
        usuario_id=_coerce_uuid(
            (core_result.get("new_token_row") or core_result.get("old_token_row") or {}).get(
                "usuario_id"
            )
        ),
        old_token_id=_coerce_uuid(core_result.get("old_token_id")),
        new_token_id=_coerce_uuid(core_result.get("new_token_id")),
        revoked_reason=core_result.get("revoked_reason"),
        old_token_row=core_result.get("old_token_row"),
        new_token_row=core_result.get("new_token_row"),
    )


async def rotate_refresh_token_service(
    *,
    old_refresh_token: str,
    new_refresh_token: str,
    cliente_id: UUID,
    usuario_id: UUID,
    client_type: str = "web",
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    empresa_id: Optional[UUID] = None,
    refresh_token_expire_days: Optional[int] = None,
    idle_timeout_minutes: Optional[int] = None,
    device_name: Optional[str] = None,
    device_id: Optional[str] = None,
) -> RotateResult:
    """
    Rotación atómica de refresh token en una única transacción (UnitOfWork).

    Compatible con idle P1-02 (GETDATE en SQL), activity tracking y SESSION_ROTATED.
    No aplica session limit (igual que store is_rotation=True legacy).

    Raises:
        DatabaseError: error de persistencia (rollback automático vía UoW).
    """
    old_token_hash = RefreshTokenService.hash_token(old_refresh_token)
    new_token_hash = RefreshTokenService.hash_token(new_refresh_token)

    refresh_days = (
        refresh_token_expire_days
        if refresh_token_expire_days is not None
        else settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    expires_at = datetime.utcnow() + timedelta(days=refresh_days)

    if idle_timeout_minutes is None:
        idle_timeout_minutes = await leer_session_idle_timeout_minutos(cliente_id)

    try:
        async with UnitOfWork(client_id=cliente_id) as uow:
            core_result = await rotate_refresh_token_core(
                uow,
                old_token_hash=old_token_hash,
                new_token_hash=new_token_hash,
                cliente_id=cliente_id,
                usuario_id=usuario_id,
                expires_at=expires_at,
                idle_timeout_minutes=idle_timeout_minutes,
                client_type=client_type,
                ip_address=ip_address,
                user_agent=user_agent,
                empresa_id=empresa_id,
                device_name=device_name,
                device_id=device_id,
            )
            result = build_rotate_result(cliente_id=cliente_id, core_result=core_result)
            logger.debug(
                "[ROTATE-SERVICE] outcome=%s cliente=%s uow_ops=%s committed=%s",
                result.outcome,
                cliente_id,
                uow.get_operations_count(),
                uow.is_committed(),
            )
            return result
    except DatabaseError:
        raise
    except Exception as exc:
        logger.exception(
            "[ROTATE-SERVICE] Error en rotación atómica cliente=%s usuario=%s",
            cliente_id,
            usuario_id,
        )
        raise DatabaseError(
            detail="Error en rotación atómica de refresh token",
            internal_code="REFRESH_TOKEN_ROTATE_ATOMIC_ERROR",
        ) from exc


__all__ = [
    "build_rotate_result",
    "rotate_refresh_token_service",
]
