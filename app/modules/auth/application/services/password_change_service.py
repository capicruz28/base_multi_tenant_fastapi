"""
Servicio de cambio de contraseña (FORCE PASSWORD CHANGE).
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, update

from app.core.security.password import get_password_hash, verify_password
from app.core.tenant.empresa_context import coerce_empresa_id
from app.infrastructure.database.tables import UsuarioTable
from app.modules.auth.application.services.auth_service import AuthService
from app.modules.auth.application.services.refresh_token_service import RefreshTokenService
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.infrastructure.database.queries_async import execute_update

import logging

logger = logging.getLogger(__name__)


class PasswordChangeService:
    @staticmethod
    async def change_password(
        *,
        current_user: UsuarioReadWithRoles,
        current_password: str,
        new_password: str,
        payload: Dict[str, Any],
        client_type: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
        old_refresh_token: Optional[str],
        access_jti: Optional[str],
        access_exp: Optional[int],
    ) -> Dict[str, Any]:
        """
        Valida contraseña actual, persiste hash nuevo, revoca refresh anteriores
        y emite nueva sesión (access + refresh).
        """
        proveedor = getattr(current_user, "proveedor_autenticacion", "local") or "local"
        if str(proveedor).strip().lower() != "local":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El cambio de contraseña no está disponible para usuarios SSO externos",
            )

        if current_password == new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La nueva contraseña debe ser diferente a la actual",
            )

        usuario_id = current_user.usuario_id
        cliente_id = current_user.cliente_id
        if not cliente_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contexto de tenant inválido para cambio de contraseña",
            )

        policy_row = await AuthService.fetch_user_password_policy_fields(
            usuario_id, cliente_id
        )
        if not policy_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )

        stored_hash = policy_row.get("contrasena")
        if not stored_hash or not verify_password(current_password, stored_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="La contraseña actual no es correcta",
            )

        new_hash = get_password_hash(new_password)
        update_query = (
            update(UsuarioTable)
            .where(UsuarioTable.c.usuario_id == usuario_id)
            .values(
                contrasena=new_hash,
                requiere_cambio_contrasena=False,
                fecha_ultimo_cambio_contrasena=func.getdate(),
            )
        )
        await execute_update(update_query, client_id=cliente_id)

        revoked_count = await RefreshTokenService.revoke_all_user_tokens(
            cliente_id, usuario_id
        )
        logger.info(
            "[PASSWORD_CHANGE] usuario=%s cliente=%s refresh_revocados=%s",
            current_user.nombre_usuario,
            cliente_id,
            revoked_count,
        )

        if old_refresh_token:
            try:
                await RefreshTokenService.revoke_token(
                    cliente_id, usuario_id, old_refresh_token
                )
            except Exception:
                pass

        if access_jti:
            await AuthService.blacklist_access_token_jti(access_jti, access_exp)

        empresa_id = coerce_empresa_id(payload.get("empresa_id"))
        es_superadmin = bool(payload.get("es_superadmin"))
        user_base = {
            "correo": getattr(current_user, "correo", ""),
            "nombre": getattr(current_user, "nombre", None),
            "apellido": getattr(current_user, "apellido", None),
            "es_activo": getattr(current_user, "es_activo", True),
            "requiere_cambio_contrasena": False,
            "proveedor_autenticacion": proveedor,
        }

        session = await AuthService.emitir_sesion_completa_con_empresa(
            username=current_user.nombre_usuario,
            usuario_id=usuario_id,
            cliente_id=cliente_id,
            empresa_id=empresa_id,
            es_superadmin=es_superadmin,
            user_base_data=user_base,
        )

        refresh_expire_days = session["refresh_expire_days"]
        stored = await RefreshTokenService.store_refresh_token(
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            token=session["refresh_token"],
            client_type=client_type,
            ip_address=ip_address,
            user_agent=user_agent,
            is_rotation=False,
            empresa_id=empresa_id,
            refresh_token_expire_days=refresh_expire_days,
        )
        if not stored or not stored.get("token_id"):
            logger.warning(
                "[PASSWORD_CHANGE] Refresh no almacenado usuario=%s",
                current_user.nombre_usuario,
            )

        return session
