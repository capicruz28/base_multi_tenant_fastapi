"""
Orquestación de revocación de sesiones IAM V2 (C03).

Único punto de entrada para logout, revoke admin, evicción y bulk revoke.
Persistencia exclusiva vía C18; sin SQL directo.
"""
from __future__ import annotations

import logging
from typing import Any, Optional
from uuid import UUID

from app.core.application.unit_of_work import UnitOfWork
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.infrastructure.database.queries.auth.session import session_transaction_core as stx
from app.modules.auth.application.services.session_audit_emitter import SessionAuditEmitter
from app.modules.auth.application.services.session_probe_service import SessionProbeService
from app.modules.auth.application.services.session_query_service import SessionQueryService
from app.modules.auth.application.services.session_redis_bridge import SessionRedisBridge
from app.modules.auth.application.session.revoke_result import RevokeResult
from app.modules.auth.application.session.revoked_reason import RevokedReason
from app.modules.auth.application.session.revoked_reason_mappers import (
    to_family_reason,
    to_session_reason,
    to_token_reason,
)
from app.modules.auth.application.session.token_context import TokenContext

logger = logging.getLogger(__name__)

_NULL_SESSION_ID = UUID("00000000-0000-0000-0000-000000000000")

_BULK_REVOKE_REASONS = frozenset({
    RevokedReason.LOGOUT_ALL,
    RevokedReason.PASSWORD_CHANGE,
    RevokedReason.USER_DEACTIVATED,
    RevokedReason.USER_DELETED,
})


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


def _token_revoked_reason_for_tx(reason: RevokedReason) -> str:
    mapped = to_token_reason(reason)
    return mapped if mapped is not None else "logout"


class SessionRevocationService:
    """Revocación de sesiones lógicas — sin replay ni creación."""

    @staticmethod
    async def _emit_revoke_audit(
        *,
        reason: RevokedReason,
        cliente_id: UUID,
        session_id: UUID,
        usuario_id: Optional[UUID],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        admin_usuario_id: Optional[UUID] = None,
        target_usuario_id: Optional[UUID] = None,
        idle_minutes: Optional[int] = None,
        sessions_revoked_count: Optional[int] = None,
    ) -> None:
        if reason == RevokedReason.USER_LOGOUT:
            await SessionAuditEmitter.emit_logout(
                cliente_id=cliente_id,
                usuario_id=usuario_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        elif reason == RevokedReason.ADMIN_REVOKE:
            await SessionAuditEmitter.emit_session_admin_revoked(
                cliente_id=cliente_id,
                session_id=session_id,
                admin_usuario_id=admin_usuario_id or usuario_id,
                target_usuario_id=target_usuario_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        elif reason == RevokedReason.SESSION_LIMIT:
            await SessionAuditEmitter.emit_session_limit_evicted(
                cliente_id=cliente_id,
                usuario_id=usuario_id,
                session_id=session_id,
            )
        elif reason == RevokedReason.IDLE_TIMEOUT:
            await SessionAuditEmitter.emit_idle_timeout(
                cliente_id=cliente_id,
                usuario_id=usuario_id,
                session_id=session_id,
                idle_minutes=idle_minutes or 0,
            )
        elif reason == RevokedReason.ABSOLUTE_TTL:
            await SessionAuditEmitter.emit_session_expired(
                cliente_id=cliente_id,
                usuario_id=usuario_id,
                session_id=session_id,
            )
        elif reason == RevokedReason.LOGOUT_ALL:
            await SessionAuditEmitter.emit_logout_all(
                cliente_id=cliente_id,
                usuario_id=usuario_id,
                sessions_revoked_count=sessions_revoked_count or 0,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        elif reason == RevokedReason.PASSWORD_CHANGE:
            await SessionAuditEmitter.emit_password_change(
                cliente_id=cliente_id,
                usuario_id=usuario_id,
                sessions_revoked_count=sessions_revoked_count or 0,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        else:
            await SessionAuditEmitter.emit_session_revoked(
                cliente_id=cliente_id,
                usuario_id=usuario_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )

    @staticmethod
    async def _execute_single_revoke(
        *,
        session_id: UUID,
        family_id: UUID,
        cliente_id: UUID,
        reason: RevokedReason,
        usuario_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        admin_usuario_id: Optional[UUID] = None,
        target_usuario_id: Optional[UUID] = None,
        idle_minutes: Optional[int] = None,
    ) -> RevokeResult:
        async with UnitOfWork(client_id=cliente_id) as uow:
            await stx.revoke_session_tx(
                uow,
                session_id=session_id,
                family_id=family_id,
                cliente_id=cliente_id,
                session_revoked_reason=to_session_reason(reason),
                family_invalidation_reason=to_family_reason(reason),
                token_revoked_reason=_token_revoked_reason_for_tx(reason),
            )

        await SessionRedisBridge.blacklist_session(session_id)
        await SessionRevocationService._emit_revoke_audit(
            reason=reason,
            cliente_id=cliente_id,
            session_id=session_id,
            usuario_id=usuario_id,
            ip_address=ip_address,
            user_agent=user_agent,
            admin_usuario_id=admin_usuario_id,
            target_usuario_id=target_usuario_id,
            idle_minutes=idle_minutes,
        )

        return RevokeResult(
            session_id=session_id,
            was_active=True,
            already_revoked=False,
        )

    @staticmethod
    async def _resolve_family_for_session(
        session_id: UUID,
        cliente_id: UUID,
        *,
        idempotent: bool,
    ) -> Optional[dict]:
        family_row = await SessionQueryService.get_family_for_session(session_id, cliente_id)
        if family_row is None and not idempotent:
            raise NotFoundError(
                detail="Sesión no encontrada",
                internal_code="SESSION_NOT_FOUND",
            )
        return family_row

    @staticmethod
    async def revoke_session(
        *,
        session_id: UUID,
        cliente_id: UUID,
        reason: RevokedReason,
        usuario_id: Optional[UUID] = None,
        idempotent: bool = False,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> RevokeResult:
        """Revoca una sesión por session_id (DESIGN RevokeSessionCommand)."""
        session_row = await SessionQueryService.get_session(session_id, cliente_id)
        if session_row is None:
            if idempotent:
                return RevokeResult(
                    session_id=session_id,
                    was_active=False,
                    already_revoked=True,
                )
            raise NotFoundError(
                detail="Sesión no encontrada",
                internal_code="SESSION_NOT_FOUND",
            )

        if not session_row.get("is_active"):
            if idempotent:
                await SessionRedisBridge.blacklist_session(session_id)
                return RevokeResult(
                    session_id=session_id,
                    was_active=False,
                    already_revoked=True,
                )
            raise NotFoundError(
                detail="Sesión no encontrada",
                internal_code="SESSION_NOT_FOUND",
            )

        family_row = await SessionRevocationService._resolve_family_for_session(
            session_id,
            cliente_id,
            idempotent=idempotent,
        )
        if family_row is None:
            return RevokeResult(
                session_id=session_id,
                was_active=False,
                already_revoked=True,
            )

        resolved_usuario = usuario_id or _coerce_uuid(session_row.get("usuario_id"))
        return await SessionRevocationService._execute_single_revoke(
            session_id=session_id,
            family_id=_coerce_uuid(family_row["family_id"]),
            cliente_id=cliente_id,
            reason=reason,
            usuario_id=resolved_usuario,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    async def revoke_current_session(
        *,
        cliente_id: UUID,
        usuario_id: UUID,
        refresh_token: Optional[str] = None,
        token_hash: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> RevokeResult:
        """Logout idempotente de la sesión asociada al refresh token (DESIGN §7.4)."""
        if refresh_token:
            await SessionProbeService.resolve_context(
                cliente_id,
                refresh_token=refresh_token,
            )
            token_hash = SessionQueryService.hash_token(refresh_token)
        elif not token_hash or not token_hash.strip():
            return RevokeResult(
                session_id=_NULL_SESSION_ID,
                was_active=False,
                already_revoked=True,
            )

        context = await SessionQueryService.get_by_hash_any_state(token_hash, cliente_id)
        if context is None:
            return RevokeResult(
                session_id=_NULL_SESSION_ID,
                was_active=False,
                already_revoked=True,
            )

        ctx_usuario = _usuario_id_from_context(context)
        if ctx_usuario is not None and ctx_usuario != usuario_id:
            raise AuthorizationError(
                detail="No puede revocar la sesión de otro usuario",
                internal_code="SESSION_OWNERSHIP_MISMATCH",
            )

        if not context.session_row.get("is_active"):
            await SessionRedisBridge.blacklist_session(context.session_id)
            return RevokeResult(
                session_id=context.session_id,
                was_active=False,
                already_revoked=True,
            )

        return await SessionRevocationService._execute_single_revoke(
            session_id=context.session_id,
            family_id=context.family_id,
            cliente_id=cliente_id,
            reason=RevokedReason.USER_LOGOUT,
            usuario_id=ctx_usuario or usuario_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    async def revoke_all_sessions(
        *,
        usuario_id: UUID,
        cliente_id: UUID,
        reason: RevokedReason = RevokedReason.LOGOUT_ALL,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> int:
        """Cierra todas las sesiones activas del usuario (DESIGN §7.5)."""
        if reason not in _BULK_REVOKE_REASONS:
            raise ValidationError(
                detail=f"reason no válido para revoke_all: {reason}",
                internal_code="INVALID_REVOKE_ALL_REASON",
            )

        async with UnitOfWork(client_id=cliente_id) as uow:
            tx_result = await stx.revoke_all_user_sessions_tx(
                uow,
                usuario_id=usuario_id,
                cliente_id=cliente_id,
                session_revoked_reason=to_session_reason(reason),
                family_invalidation_reason=to_family_reason(reason),
                token_revoked_reason=_token_revoked_reason_for_tx(reason),
            )

        sessions_closed = int(tx_result.get("sessions_closed", 0))
        await SessionRedisBridge.blacklist_all_user_sessions(usuario_id, cliente_id)
        await SessionRevocationService._emit_revoke_audit(
            reason=reason,
            cliente_id=cliente_id,
            session_id=_NULL_SESSION_ID,
            usuario_id=usuario_id,
            ip_address=ip_address,
            user_agent=user_agent,
            sessions_revoked_count=sessions_closed,
        )
        return sessions_closed

    @staticmethod
    async def revoke_by_admin(
        *,
        session_id: UUID,
        cliente_id: UUID,
        admin_usuario_id: UUID,
        target_usuario_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> RevokeResult:
        """Revocación administrativa — no idempotente si la sesión ya está cerrada."""
        session_row = await SessionQueryService.get_session(session_id, cliente_id)
        if session_row is None:
            raise NotFoundError(
                detail="Sesión no encontrada",
                internal_code="SESSION_NOT_FOUND",
            )

        family_row = await SessionRevocationService._resolve_family_for_session(
            session_id,
            cliente_id,
            idempotent=False,
        )
        resolved_target = target_usuario_id or _coerce_uuid(session_row.get("usuario_id"))

        return await SessionRevocationService._execute_single_revoke(
            session_id=session_id,
            family_id=_coerce_uuid(family_row["family_id"]),
            cliente_id=cliente_id,
            reason=RevokedReason.ADMIN_REVOKE,
            usuario_id=resolved_target,
            ip_address=ip_address,
            user_agent=user_agent,
            admin_usuario_id=admin_usuario_id,
            target_usuario_id=resolved_target,
        )

    @staticmethod
    async def revoke_family(
        *,
        family_id: UUID,
        cliente_id: UUID,
        token_hash: str,
        reason: RevokedReason = RevokedReason.ADMIN_REVOKE,
        usuario_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> RevokeResult:
        """Revoca sesión resolviendo contexto por token y validando family_id."""
        if not token_hash or not token_hash.strip():
            raise ValidationError(
                detail="token_hash es obligatorio para revoke_family",
                internal_code="EMPTY_TOKEN_HASH",
            )

        context = await SessionQueryService.get_by_hash_any_state(token_hash, cliente_id)
        if context is None:
            raise NotFoundError(
                detail="Token no encontrado",
                internal_code="TOKEN_NOT_FOUND",
            )
        if context.family_id != family_id:
            raise NotFoundError(
                detail="Familia no encontrada",
                internal_code="FAMILY_NOT_FOUND",
            )
        if not context.session_row.get("is_active"):
            raise NotFoundError(
                detail="Sesión no encontrada",
                internal_code="SESSION_NOT_FOUND",
            )

        resolved_usuario = usuario_id or _usuario_id_from_context(context)
        return await SessionRevocationService._execute_single_revoke(
            session_id=context.session_id,
            family_id=context.family_id,
            cliente_id=cliente_id,
            reason=reason,
            usuario_id=resolved_usuario,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    async def revoke_due_to_password_change(
        *,
        usuario_id: UUID,
        cliente_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> int:
        """Revoca todas las sesiones por cambio de contraseña (DESIGN §7.6 paso 3)."""
        return await SessionRevocationService.revoke_all_sessions(
            usuario_id=usuario_id,
            cliente_id=cliente_id,
            reason=RevokedReason.PASSWORD_CHANGE,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    async def revoke_due_to_session_limit(
        *,
        session_id: UUID,
        cliente_id: UUID,
        usuario_id: UUID,
    ) -> RevokeResult:
        """Evicción por límite de sesiones (DESIGN §7.7)."""
        return await SessionRevocationService.revoke_session(
            session_id=session_id,
            cliente_id=cliente_id,
            reason=RevokedReason.SESSION_LIMIT,
            usuario_id=usuario_id,
            idempotent=False,
        )


__all__ = ["SessionRevocationService"]
