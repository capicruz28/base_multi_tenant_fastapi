"""
Reset administrativo de contraseña — orquestación IAM (PR1).

Fuente normativa: ADMIN_PASSWORD_RESET_FUNCTIONAL_SPEC.md,
ADMIN_PASSWORD_RESET_TECHNICAL_SPEC.md
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import func, update

from app.core.application.base_service import BaseService
from app.core.exceptions import NotFoundError, ServiceError, ValidationError
from app.core.security.password import get_password_hash
from app.core.security.password_generator import generar_contrasena_segura
from app.infrastructure.database.tables import UsuarioTable
from app.infrastructure.database.queries_async import execute_update
from app.modules.auth.application.session.revoked_reason import RevokedReason
from app.modules.auth.application.session.session_v2_feature import is_session_v2_enabled
from app.modules.users.application.services.user_service import UsuarioService
from app.modules.superadmin.application.services.audit_service import AuditService

logger = logging.getLogger(__name__)

_RESET_SUCCESS_MESSAGE = (
    "Contraseña restablecida exitosamente. La contraseña temporal solo se muestra una vez; "
    "el usuario deberá cambiarla en su próximo acceso."
)


class AdminPasswordResetService:
    """Orquesta reset administrativo reutilizando infraestructura IAM existente."""

    @staticmethod
    async def _audit_reset_event(
        *,
        cliente_id: UUID,
        target_usuario_id: Optional[UUID],
        admin_usuario_id: UUID,
        target_nombre_usuario: Optional[str],
        exito: bool,
        ip_address: Optional[str],
        user_agent: Optional[str],
        sessions_revoked_count: Optional[int] = None,
        codigo_error: Optional[str] = None,
    ) -> None:
        metadata: Dict[str, Any] = {
            "admin_usuario_id": str(admin_usuario_id),
            "initiator": "admin",
        }
        if target_usuario_id is not None:
            metadata["target_usuario_id"] = str(target_usuario_id)
        if target_nombre_usuario:
            metadata["target_nombre_usuario"] = target_nombre_usuario
        if sessions_revoked_count is not None:
            metadata["sessions_revoked_count"] = sessions_revoked_count
        if codigo_error:
            metadata["rejection_reason"] = codigo_error

        try:
            await AuditService.registrar_auth_event(
                cliente_id=cliente_id,
                usuario_id=target_usuario_id,
                evento="admin_password_reset",
                exito=exito,
                nombre_usuario_intento=target_nombre_usuario,
                descripcion=(
                    "Reset administrativo de contraseña ejecutado"
                    if exito
                    else "Intento de reset administrativo de contraseña rechazado"
                ),
                codigo_error=codigo_error,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata,
            )
        except Exception:
            logger.exception(
                "[ADMIN_PASSWORD_RESET] Error de auditoría (fail-soft) target=%s",
                target_usuario_id,
            )

    @staticmethod
    async def _revoke_sessions_after_reset(
        *,
        cliente_id: UUID,
        usuario_id: UUID,
        ip_address: Optional[str],
        user_agent: Optional[str],
    ) -> int:
        if is_session_v2_enabled(cliente_id):
            from app.modules.auth.application.services.session_revocation_service import (
                SessionRevocationService,
            )

            return await SessionRevocationService.revoke_due_to_password_change(
                usuario_id=usuario_id,
                cliente_id=cliente_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )

        from app.modules.auth.application.services.refresh_token_service import (
            RefreshTokenService,
        )

        await RefreshTokenService.blacklist_access_for_user_active_sessions(
            cliente_id,
            usuario_id,
        )
        return await RefreshTokenService.revoke_all_user_tokens(
            cliente_id,
            usuario_id,
            revoked_reason=RevokedReason.PASSWORD_CHANGE,
        )

    @staticmethod
    @BaseService.handle_service_errors
    async def reset_password_admin(
        *,
        cliente_id: UUID,
        admin_usuario_id: UUID,
        target_usuario_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        if target_usuario_id == admin_usuario_id:
            await AdminPasswordResetService._audit_reset_event(
                cliente_id=cliente_id,
                target_usuario_id=target_usuario_id,
                admin_usuario_id=admin_usuario_id,
                target_nombre_usuario=None,
                exito=False,
                ip_address=ip_address,
                user_agent=user_agent,
                codigo_error="SELF_PASSWORD_RESET_NOT_ALLOWED",
            )
            raise ValidationError(
                detail=(
                    "No puede restablecer su propia contraseña por esta vía. "
                    "Use el cambio de contraseña o solicítelo a otro administrador"
                ),
                internal_code="SELF_PASSWORD_RESET_NOT_ALLOWED",
            )

        target_row = await UsuarioService.obtener_usuario_por_id(
            cliente_id, target_usuario_id
        )
        if not target_row:
            await AdminPasswordResetService._audit_reset_event(
                cliente_id=cliente_id,
                target_usuario_id=target_usuario_id,
                admin_usuario_id=admin_usuario_id,
                target_nombre_usuario=None,
                exito=False,
                ip_address=ip_address,
                user_agent=user_agent,
                codigo_error="USER_NOT_FOUND",
            )
            raise NotFoundError(
                detail="Usuario no encontrado en este cliente",
                internal_code="USER_NOT_FOUND",
            )

        nombre_usuario = target_row.get("nombre_usuario") or ""
        proveedor = (target_row.get("proveedor_autenticacion") or "local").strip().lower()
        if proveedor != "local":
            await AdminPasswordResetService._audit_reset_event(
                cliente_id=cliente_id,
                target_usuario_id=target_usuario_id,
                admin_usuario_id=admin_usuario_id,
                target_nombre_usuario=nombre_usuario,
                exito=False,
                ip_address=ip_address,
                user_agent=user_agent,
                codigo_error="USER_SSO_PASSWORD_NOT_MANAGED",
            )
            raise ValidationError(
                detail=(
                    "El restablecimiento de contraseña no está disponible "
                    "para usuarios SSO externos"
                ),
                internal_code="USER_SSO_PASSWORD_NOT_MANAGED",
            )

        contrasena_plana = generar_contrasena_segura(12)
        contrasena_hash = get_password_hash(contrasena_plana)

        update_query = (
            update(UsuarioTable)
            .where(
                UsuarioTable.c.usuario_id == target_usuario_id,
                UsuarioTable.c.cliente_id == cliente_id,
                UsuarioTable.c.es_eliminado == False,  # noqa: E712
            )
            .values(
                contrasena=contrasena_hash,
                requiere_cambio_contrasena=True,
                intentos_fallidos=0,
                fecha_bloqueo=None,
                fecha_actualizacion=func.getdate(),
            )
        )
        updated = await execute_update(update_query, client_id=cliente_id)
        rows_affected = (updated or {}).get("rows_affected", 0)
        if rows_affected == 0:
            raise ServiceError(
                status_code=500,
                detail="Error interno al restablecer la contraseña del usuario",
                internal_code="PASSWORD_RESET_FAILED",
            )

        try:
            sesiones_revocadas = await AdminPasswordResetService._revoke_sessions_after_reset(
                cliente_id=cliente_id,
                usuario_id=target_usuario_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        except Exception as exc:
            logger.exception(
                "[ADMIN_PASSWORD_RESET] Fallo revocación sesiones usuario=%s cliente=%s",
                target_usuario_id,
                cliente_id,
            )
            await AdminPasswordResetService._audit_reset_event(
                cliente_id=cliente_id,
                target_usuario_id=target_usuario_id,
                admin_usuario_id=admin_usuario_id,
                target_nombre_usuario=nombre_usuario,
                exito=False,
                ip_address=ip_address,
                user_agent=user_agent,
                codigo_error="PASSWORD_RESET_SESSION_REVOKE_FAILED",
            )
            raise ServiceError(
                status_code=500,
                detail="Error interno al invalidar sesiones del usuario",
                internal_code="PASSWORD_RESET_SESSION_REVOKE_FAILED",
            ) from exc

        await AdminPasswordResetService._audit_reset_event(
            cliente_id=cliente_id,
            target_usuario_id=target_usuario_id,
            admin_usuario_id=admin_usuario_id,
            target_nombre_usuario=nombre_usuario,
            exito=True,
            ip_address=ip_address,
            user_agent=user_agent,
            sessions_revoked_count=sesiones_revocadas,
        )

        logger.info(
            "[ADMIN_PASSWORD_RESET] admin=%s target=%s cliente=%s sesiones=%s",
            admin_usuario_id,
            target_usuario_id,
            cliente_id,
            sesiones_revocadas,
        )

        return {
            "success": True,
            "message": _RESET_SUCCESS_MESSAGE,
            "usuario_id": target_usuario_id,
            "credenciales_temporales": {
                "nombre_usuario": nombre_usuario,
                "contrasena": contrasena_plana,
                "requiere_cambio": True,
            },
            "sesiones_revocadas": sesiones_revocadas,
        }


__all__ = ["AdminPasswordResetService"]
