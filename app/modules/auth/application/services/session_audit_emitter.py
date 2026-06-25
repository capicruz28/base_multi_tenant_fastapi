"""
Emisor de auditoría de sesiones IAM V2 (C07).

Wrapper tipado sobre AuditService.registrar_auth_event.
Fail-soft: errores de auditoría nunca interrumpen el flujo auth.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from app.modules.superadmin.application.services.audit_service import AuditService

logger = logging.getLogger(__name__)


def _build_metadata(**fields: Any) -> Dict[str, Any]:
    """Construye metadata_json sin datos sensibles (sin hash refresh ni tokens)."""
    metadata: Dict[str, Any] = {}
    for key, value in fields.items():
        if value is None:
            continue
        if isinstance(value, UUID):
            metadata[key] = str(value)
        else:
            metadata[key] = value
    return metadata


async def _emit(
    *,
    cliente_id: UUID,
    evento: str,
    exito: bool,
    usuario_id: Optional[UUID] = None,
    nombre_usuario_intento: Optional[str] = None,
    descripcion: Optional[str] = None,
    codigo_error: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    try:
        await AuditService.registrar_auth_event(
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            evento=evento,
            exito=exito,
            nombre_usuario_intento=nombre_usuario_intento,
            descripcion=descripcion,
            codigo_error=codigo_error,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata,
        )
    except Exception as exc:
        logger.error(
            "[SESSION-AUDIT] fail-soft evento=%s cliente_id=%s: %s",
            evento,
            cliente_id,
            exc,
            exc_info=True,
        )


class SessionAuditEmitter:
    """Adaptador audit sesión — catálogo DESIGN-01 §10.2."""

    @staticmethod
    async def emit_login_success(
        *,
        cliente_id: UUID,
        usuario_id: UUID,
        session_id: UUID,
        platform: str,
        login_method: str,
        device_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        await _emit(
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            evento="login_success",
            exito=True,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=_build_metadata(
                session_id=session_id,
                platform=platform,
                login_method=login_method,
                device_id=device_id,
            ),
        )

    @staticmethod
    async def emit_login_failed(
        *,
        cliente_id: UUID,
        nombre_usuario_intento: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        codigo_error: Optional[str] = None,
    ) -> None:
        await _emit(
            cliente_id=cliente_id,
            evento="login_failed",
            exito=False,
            nombre_usuario_intento=nombre_usuario_intento,
            codigo_error=codigo_error,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=_build_metadata(nombre_usuario_intento=nombre_usuario_intento),
        )

    @staticmethod
    async def emit_refresh_success(
        *,
        cliente_id: UUID,
        usuario_id: UUID,
        session_id: UUID,
        token_id: UUID,
        family_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        await _emit(
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            evento="refresh_success",
            exito=True,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=_build_metadata(
                session_id=session_id,
                token_id=token_id,
                family_id=family_id,
            ),
        )

    @staticmethod
    async def emit_logout(
        *,
        cliente_id: UUID,
        usuario_id: UUID,
        session_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        await _emit(
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            evento="logout",
            exito=True,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=_build_metadata(session_id=session_id),
        )

    @staticmethod
    async def emit_logout_all(
        *,
        cliente_id: UUID,
        usuario_id: UUID,
        sessions_revoked_count: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        await _emit(
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            evento="logout_all",
            exito=True,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=_build_metadata(sessions_revoked_count=sessions_revoked_count),
        )

    @staticmethod
    async def emit_session_revoked(
        *,
        cliente_id: UUID,
        usuario_id: UUID,
        session_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        await _emit(
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            evento="session_revoked",
            exito=True,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=_build_metadata(session_id=session_id, initiator="user"),
        )

    @staticmethod
    async def emit_session_admin_revoked(
        *,
        cliente_id: UUID,
        session_id: UUID,
        admin_usuario_id: UUID,
        target_usuario_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        await _emit(
            cliente_id=cliente_id,
            usuario_id=admin_usuario_id,
            evento="session_admin_revoked",
            exito=True,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=_build_metadata(
                session_id=session_id,
                admin_usuario_id=admin_usuario_id,
                target_usuario_id=target_usuario_id,
            ),
        )

    @staticmethod
    async def emit_replay_detected(
        *,
        cliente_id: UUID,
        usuario_id: UUID,
        session_id: UUID,
        family_id: UUID,
        token_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        await _emit(
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            evento="replay_detected",
            exito=False,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=_build_metadata(
                session_id=session_id,
                family_id=family_id,
                token_id=token_id,
                ip=ip_address,
            ),
        )

    @staticmethod
    async def emit_family_compromised(
        *,
        cliente_id: UUID,
        usuario_id: Optional[UUID],
        family_id: UUID,
        invalidation_reason: str,
        session_id: Optional[UUID] = None,
    ) -> None:
        await _emit(
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            evento="family_compromised",
            exito=False,
            metadata=_build_metadata(
                family_id=family_id,
                invalidation_reason=invalidation_reason,
                session_id=session_id,
            ),
        )

    @staticmethod
    async def emit_session_limit_evicted(
        *,
        cliente_id: UUID,
        usuario_id: UUID,
        session_id: UUID,
    ) -> None:
        await _emit(
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            evento="session_limit_evicted",
            exito=True,
            metadata=_build_metadata(session_id=session_id),
        )

    @staticmethod
    async def emit_idle_timeout(
        *,
        cliente_id: UUID,
        usuario_id: UUID,
        session_id: UUID,
        idle_minutes: int,
    ) -> None:
        await _emit(
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            evento="idle_timeout",
            exito=True,
            metadata=_build_metadata(session_id=session_id, idle_minutes=idle_minutes),
        )

    @staticmethod
    async def emit_password_change(
        *,
        cliente_id: UUID,
        usuario_id: UUID,
        sessions_revoked_count: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        await _emit(
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            evento="password_change",
            exito=True,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=_build_metadata(sessions_revoked_count=sessions_revoked_count),
        )

    @staticmethod
    async def emit_session_expired(
        *,
        cliente_id: UUID,
        usuario_id: UUID,
        session_id: UUID,
    ) -> None:
        await _emit(
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            evento="session_expired",
            exito=True,
            metadata=_build_metadata(session_id=session_id),
        )

    @staticmethod
    async def emit_empresa_selected(
        *,
        cliente_id: UUID,
        usuario_id: UUID,
        session_id: UUID,
        empresa_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        await _emit(
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            evento="empresa_selected",
            exito=True,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=_build_metadata(session_id=session_id, empresa_id=empresa_id),
        )

    @staticmethod
    async def emit_empresa_changed(
        *,
        cliente_id: UUID,
        usuario_id: UUID,
        session_id: UUID,
        old_empresa_id: Optional[UUID],
        new_empresa_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        await _emit(
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            evento="empresa_changed",
            exito=True,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=_build_metadata(
                session_id=session_id,
                old_empresa_id=old_empresa_id,
                new_empresa_id=new_empresa_id,
            ),
        )


__all__ = ["SessionAuditEmitter"]
