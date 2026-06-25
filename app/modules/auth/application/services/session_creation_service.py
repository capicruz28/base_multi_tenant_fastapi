"""
Orquestación de creación de sesión IAM V2 (C01).

Secuencia: política → evicción (si aplica) → create_session_with_token_tx
→ Redis → auditoría → SessionCreationResult.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from app.core.application.unit_of_work import UnitOfWork
from app.core.exceptions import ValidationError
from app.infrastructure.database.queries.auth.session import session_transaction_core as stx
from app.infrastructure.database.queries.auth.session import user_session_queries_core as usq
from app.modules.auth.application.services.auth_config_service import (
    leer_expiracion_tokens_cliente,
)
from app.modules.auth.application.services.session_audit_emitter import SessionAuditEmitter
from app.modules.auth.application.services.session_policy_service import SessionPolicyService
from app.modules.auth.application.services.session_query_service import SessionQueryService
from app.modules.auth.application.services.session_redis_bridge import SessionRedisBridge
from app.modules.auth.application.session.revoked_reason import RevokedReason
from app.modules.auth.application.session.revoked_reason_mappers import (
    to_family_reason,
    to_session_reason,
    to_token_reason,
)
from app.modules.auth.application.session.session_creation_result import SessionCreationResult

logger = logging.getLogger(__name__)

_VALID_PLATFORMS = frozenset({"web", "mobile", "desktop", "api"})
_VALID_LOGIN_METHODS = frozenset({"password", "sso", "2fa", "api_key"})


@dataclass(frozen=True)
class DeviceContext:
    """Metadata de dispositivo para user_session."""

    platform: str
    device_name: Optional[str] = None
    device_id: Optional[str] = None
    device_fingerprint: Optional[str] = None
    user_agent: Optional[str] = None
    login_ip: Optional[str] = None


def _hash_device_fingerprint(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


async def _resolve_token_expires_at(
    cliente_id: UUID,
    token_expires_at: Optional[datetime],
    refresh_token_days: Optional[int],
) -> datetime:
    if token_expires_at is not None:
        return token_expires_at
    days = refresh_token_days
    if days is None:
        exp = await leer_expiracion_tokens_cliente(cliente_id)
        days = exp["refresh_token_days"]
    return datetime.utcnow() + timedelta(days=max(int(days), 1))


class SessionCreationService:
    """Creación atómica de sesión lógica + familia + primer refresh token."""

    @staticmethod
    def _validate_device_context(device_context: DeviceContext) -> None:
        if not device_context or not device_context.platform:
            raise ValidationError(
                detail="device_context.platform es obligatorio",
                internal_code="INVALID_DEVICE_CONTEXT",
            )
        if device_context.platform not in _VALID_PLATFORMS:
            raise ValidationError(
                detail=f"platform inválida: {device_context.platform}",
                internal_code="INVALID_PLATFORM",
            )

    @staticmethod
    def _validate_login_method(login_method: str) -> None:
        if login_method not in _VALID_LOGIN_METHODS:
            raise ValidationError(
                detail=f"login_method inválido: {login_method}",
                internal_code="INVALID_LOGIN_METHOD",
            )

    @staticmethod
    async def _evict_session_for_limit(
        *,
        session_id: UUID,
        family_id: UUID,
        usuario_id: UUID,
        cliente_id: UUID,
    ) -> None:
        reason = RevokedReason.SESSION_LIMIT
        token_reason = to_token_reason(reason)
        async with UnitOfWork(client_id=cliente_id) as uow:
            await stx.revoke_session_tx(
                uow,
                session_id=session_id,
                family_id=family_id,
                cliente_id=cliente_id,
                session_revoked_reason=to_session_reason(reason),
                family_invalidation_reason=to_family_reason(reason),
                token_revoked_reason=token_reason or "family_compromised",
            )
        await SessionRedisBridge.blacklist_session(session_id)
        await SessionAuditEmitter.emit_session_limit_evicted(
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            session_id=session_id,
        )

    @staticmethod
    async def create(
        *,
        usuario_id: UUID,
        cliente_id: UUID,
        token_hash: str,
        device_context: DeviceContext,
        remember_me: bool = False,
        login_method: str = "password",
        empresa_id: Optional[UUID] = None,
        selection_token_completed: bool = False,
        token_expires_at: Optional[datetime] = None,
        refresh_token_days: Optional[int] = None,
        access_jti: Optional[str] = None,
        access_exp: Optional[int] = None,
    ) -> SessionCreationResult:
        """
        Crea sesión completa respetando políticas C04.
        Persistencia exclusiva vía create_session_with_token_tx.
        """
        if not token_hash or not token_hash.strip():
            raise ValidationError(
                detail="token_hash es obligatorio",
                internal_code="EMPTY_TOKEN_HASH",
            )
        SessionCreationService._validate_device_context(device_context)
        SessionCreationService._validate_login_method(login_method)

        limit_decision = await SessionPolicyService.plan_session_limit_evictions(
            usuario_id,
            cliente_id,
        )
        for session_row in limit_decision.sessions_to_evict:
            evict_session_id = UUID(str(session_row["session_id"]))
            family_row = await SessionQueryService.get_family_for_session(
                evict_session_id,
                cliente_id,
            )
            if not family_row:
                logger.warning(
                    "[SESSION-CREATE] Evicción omitida: sin familia session_id=%s",
                    evict_session_id,
                )
                continue
            await SessionCreationService._evict_session_for_limit(
                session_id=evict_session_id,
                family_id=UUID(str(family_row["family_id"])),
                usuario_id=usuario_id,
                cliente_id=cliente_id,
            )

        session_expires_at = await SessionPolicyService.compute_session_expires_at(
            cliente_id,
            remember_me,
        )
        resolved_token_expires = await _resolve_token_expires_at(
            cliente_id,
            token_expires_at,
            refresh_token_days,
        )

        fingerprint_hash: Optional[str] = None
        if device_context.device_fingerprint:
            fingerprint_hash = _hash_device_fingerprint(device_context.device_fingerprint)

        async with UnitOfWork(client_id=cliente_id) as uow:
            tx_result = await stx.create_session_with_token_tx(
                uow,
                usuario_id=usuario_id,
                cliente_id=cliente_id,
                session_expires_at=session_expires_at,
                token_hash=token_hash,
                token_expires_at=resolved_token_expires,
                platform=device_context.platform,
                login_method=login_method,
                selection_token_completed=selection_token_completed,
                empresa_id=empresa_id,
                device_name=device_context.device_name,
                device_id=device_context.device_id,
                device_fingerprint=fingerprint_hash,
                user_agent=device_context.user_agent,
                login_ip=device_context.login_ip,
            )

        session_id = UUID(str(tx_result["session_id"]))
        family_id = UUID(str(tx_result["family_id"]))
        token_id = UUID(str(tx_result["token_id"]))

        if access_jti:
            await SessionRedisBridge.link_access(
                session_id,
                access_jti,
                access_exp,
                token_id=token_id,
            )

        await SessionAuditEmitter.emit_login_success(
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            session_id=session_id,
            platform=device_context.platform,
            login_method=login_method,
            device_id=device_context.device_id,
            ip_address=device_context.login_ip,
            user_agent=device_context.user_agent,
        )

        return SessionCreationResult(
            session_id=session_id,
            family_id=family_id,
            token_id=token_id,
            expires_at=session_expires_at,
        )

    @staticmethod
    async def update_empresa(
        *,
        session_id: UUID,
        cliente_id: UUID,
        empresa_id: UUID,
        selection_token_completed: bool = True,
    ) -> None:
        """Actualiza empresa en sesión post selection_token (sin rotación)."""
        rows = await usq.update_session_empresa_core(
            session_id,
            cliente_id,
            empresa_id=empresa_id,
            selection_token_completed=selection_token_completed,
        )
        if rows != 1:
            raise ValidationError(
                detail="No se pudo actualizar empresa en la sesión",
                internal_code="SESSION_EMPRESA_UPDATE_FAILED",
            )


__all__ = ["DeviceContext", "SessionCreationService"]
