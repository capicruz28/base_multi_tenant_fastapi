"""
Orquestación RTR y detección de replay IAM Session V2 (C02).

Secuencia: probe → validate → rotate_refresh_token_tx | handle_replay_attack_tx
→ Redis → auditoría.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from app.core.application.unit_of_work import UnitOfWork
from app.core.exceptions import ValidationError
from app.infrastructure.database.queries.auth.session import session_transaction_core as stx
from app.modules.auth.application.services.session_audit_emitter import SessionAuditEmitter
from app.modules.auth.application.services.session_policy_service import SessionPolicyService
from app.modules.auth.application.services.session_probe_service import SessionProbeService
from app.modules.auth.application.services.session_query_service import SessionQueryService
from app.modules.auth.application.services.session_redis_bridge import SessionRedisBridge
from app.modules.auth.application.services.session_revocation_service import SessionRevocationService
from app.modules.auth.application.session.replay_detection_result import ReplayDetectionResult
from app.modules.auth.application.session.revoked_reason import RevokedReason
from app.modules.auth.application.session.rotate_result import RotateOutcome, RotateResult
from app.modules.auth.application.session.token_context import TokenContext

logger = logging.getLogger(__name__)

_REPLAY_MARK_USED_ERROR = "MARK token used"
_TOKEN_ALREADY_USED_ERROR = "TOKEN_ALREADY_USED"


def _is_replay_tx_error(exc: RuntimeError) -> bool:
    message = str(exc)
    return _REPLAY_MARK_USED_ERROR in message or _TOKEN_ALREADY_USED_ERROR in message


def _resolve_empresa_id_for_rotation(
    context: TokenContext,
    empresa_id: Optional[UUID],
) -> Optional[UUID]:
    if empresa_id is not None:
        return empresa_id
    return _coerce_uuid(
        context.session_row.get("empresa_id") or context.token_row.get("empresa_id")
    )


def _coerce_uuid(value: Any) -> Optional[UUID]:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return None


def _usuario_id_from_context(context: TokenContext) -> Optional[UUID]:
    return _coerce_uuid(
        context.session_row.get("usuario_id") or context.token_row.get("usuario_id")
    )


class SessionRotationService:
    """RTR atómico + replay — sin JWT ni capa HTTP auth."""

    @staticmethod
    def _rotate_result_from_context(
        *,
        outcome: RotateOutcome,
        cliente_id: UUID,
        context: Optional[TokenContext] = None,
        old_token_id: Optional[UUID] = None,
        new_token_id: Optional[UUID] = None,
    ) -> RotateResult:
        session_id = context.session_id if context else None
        family_id = context.family_id if context else None
        usuario_id = _usuario_id_from_context(context) if context else None
        if old_token_id is None and context is not None:
            old_token_id = context.token_id
        return RotateResult(
            outcome=outcome,
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            session_id=session_id,
            family_id=family_id,
            old_token_id=old_token_id,
            new_token_id=new_token_id,
            old_token_row=dict(context.token_row) if context else None,
        )

    @staticmethod
    def _rotate_result_from_replay(
        *,
        cliente_id: UUID,
        replay: ReplayDetectionResult,
    ) -> RotateResult:
        return RotateResult(
            outcome=RotateOutcome.COMPROMISED,
            cliente_id=cliente_id,
            usuario_id=replay.usuario_id,
            session_id=replay.session_id,
            family_id=replay.family_id,
            old_token_id=replay.token_id,
        )

    @staticmethod
    async def _handle_idle_timeout(
        *,
        context: TokenContext,
        cliente_id: UUID,
        request_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> RotateResult:
        ctx_usuario = _usuario_id_from_context(context)
        await SessionRevocationService.revoke_session(
            session_id=context.session_id,
            cliente_id=cliente_id,
            reason=RevokedReason.IDLE_TIMEOUT,
            usuario_id=ctx_usuario,
            ip_address=request_ip,
            user_agent=user_agent,
        )
        return SessionRotationService._rotate_result_from_context(
            outcome=RotateOutcome.IDLE_TIMEOUT,
            cliente_id=cliente_id,
            context=context,
        )

    @staticmethod
    async def handle_replay(
        *,
        token_hash: str,
        cliente_id: UUID,
        request_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ReplayDetectionResult:
        """
        Compromiso atómico de familia + cierre sesión + revoke tokens (DESIGN §7.3).
        Persistencia exclusiva vía handle_replay_attack_tx.
        """
        context = await SessionQueryService.get_by_hash_any_state(token_hash, cliente_id)
        if context is None:
            raise ValidationError(
                detail="Token no encontrado para replay",
                internal_code="REPLAY_TOKEN_NOT_FOUND",
            )

        usuario_id = _usuario_id_from_context(context)
        if usuario_id is None:
            raise ValidationError(
                detail="usuario_id no resoluble para replay",
                internal_code="REPLAY_USER_UNRESOLVABLE",
            )

        async with UnitOfWork(client_id=cliente_id) as uow:
            await stx.handle_replay_attack_tx(
                uow,
                session_id=context.session_id,
                family_id=context.family_id,
                token_id=context.token_id,
                cliente_id=cliente_id,
                usuario_id=usuario_id,
            )

        await SessionRedisBridge.blacklist_session(context.session_id)
        await SessionAuditEmitter.emit_replay_detected(
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            session_id=context.session_id,
            family_id=context.family_id,
            token_id=context.token_id,
            ip_address=request_ip,
            user_agent=user_agent,
        )

        return ReplayDetectionResult(
            session_id=context.session_id,
            family_id=context.family_id,
            token_id=context.token_id,
            cliente_id=cliente_id,
            usuario_id=usuario_id,
        )

    @staticmethod
    async def rotate(
        *,
        refresh_token: str,
        new_refresh_token: str,
        cliente_id: UUID,
        new_token_expires_at: datetime,
        usuario_id: Optional[UUID] = None,
        empresa_id: Optional[UUID] = None,
        request_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        access_jti: Optional[str] = None,
        access_exp: Optional[int] = None,
    ) -> RotateResult:
        """
        Refresh Token Rotation completo (DESIGN §7.2).
        """
        if not refresh_token or not refresh_token.strip():
            raise ValidationError(
                detail="refresh_token es obligatorio",
                internal_code="EMPTY_REFRESH_TOKEN",
            )
        if not new_refresh_token or not new_refresh_token.strip():
            raise ValidationError(
                detail="new_refresh_token es obligatorio",
                internal_code="EMPTY_NEW_REFRESH_TOKEN",
            )

        await SessionProbeService.resolve_context(
            cliente_id,
            refresh_token=refresh_token,
        )

        old_token_hash = SessionQueryService.hash_token(refresh_token)
        new_token_hash = SessionQueryService.hash_token(new_refresh_token)

        validation = await SessionQueryService.validate_for_rotation(
            old_token_hash,
            cliente_id,
        )

        if validation.outcome == RotateOutcome.ALREADY_USED:
            replay = await SessionRotationService.handle_replay(
                token_hash=old_token_hash,
                cliente_id=cliente_id,
                request_ip=request_ip,
                user_agent=user_agent,
            )
            return SessionRotationService._rotate_result_from_replay(
                cliente_id=cliente_id,
                replay=replay,
            )

        if not validation.is_valid:
            return SessionRotationService._rotate_result_from_context(
                outcome=validation.outcome,
                cliente_id=cliente_id,
                context=validation.context,
            )

        context = validation.context
        assert context is not None

        ctx_usuario = _usuario_id_from_context(context)
        if usuario_id is not None and ctx_usuario is not None and usuario_id != ctx_usuario:
            return SessionRotationService._rotate_result_from_context(
                outcome=RotateOutcome.USER_MISMATCH,
                cliente_id=cliente_id,
                context=context,
            )

        if await SessionPolicyService.check_idle(context.session_id, cliente_id):
            return await SessionRotationService._handle_idle_timeout(
                context=context,
                cliente_id=cliente_id,
                request_ip=request_ip,
                user_agent=user_agent,
            )

        effective_empresa_id = _resolve_empresa_id_for_rotation(context, empresa_id)

        try:
            async with UnitOfWork(client_id=cliente_id) as uow:
                tx_kwargs: Dict[str, Any] = {
                    "uow": uow,
                    "old_token_hash": old_token_hash,
                    "new_token_hash": new_token_hash,
                    "cliente_id": cliente_id,
                    "token_expires_at": new_token_expires_at,
                    "last_seen_ip": request_ip,
                }
                if effective_empresa_id is not None:
                    tx_kwargs["empresa_id"] = effective_empresa_id
                tx_result = await stx.rotate_refresh_token_tx(**tx_kwargs)
        except RuntimeError as exc:
            if _is_replay_tx_error(exc):
                logger.warning(
                    "[SESSION-ROTATE] Replay detectado en tx hash=%s... (%s)",
                    old_token_hash[:8],
                    exc,
                )
                replay = await SessionRotationService.handle_replay(
                    token_hash=old_token_hash,
                    cliente_id=cliente_id,
                    request_ip=request_ip,
                    user_agent=user_agent,
                )
                return SessionRotationService._rotate_result_from_replay(
                    cliente_id=cliente_id,
                    replay=replay,
                )
            raise

        session_id = UUID(str(tx_result["session_id"]))
        family_id = UUID(str(tx_result["family_id"]))
        old_token_id = UUID(str(tx_result["old_token_id"]))
        new_token_id = UUID(str(tx_result["new_token_id"]))

        if access_jti:
            await SessionRedisBridge.link_access(
                session_id,
                access_jti,
                access_exp,
                token_id=new_token_id,
            )

        await SessionAuditEmitter.emit_refresh_success(
            cliente_id=cliente_id,
            usuario_id=ctx_usuario or usuario_id,
            session_id=session_id,
            token_id=new_token_id,
            family_id=family_id,
            ip_address=request_ip,
            user_agent=user_agent,
        )

        return RotateResult(
            outcome=RotateOutcome.ROTATED,
            cliente_id=cliente_id,
            usuario_id=ctx_usuario or usuario_id,
            session_id=session_id,
            family_id=family_id,
            old_token_id=old_token_id,
            new_token_id=new_token_id,
        )


__all__ = ["SessionRotationService"]
