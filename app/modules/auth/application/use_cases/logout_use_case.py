# app/modules/auth/application/use_cases/logout_use_case.py
"""
LogoutUseCase: Caso de uso para cierre de sesión.

✅ FASE 3: ARQUITECTURA - Use Case para Logout
"""

from typing import Optional, Dict, Any
import logging

from app.modules.auth.application.services.refresh_token_service import RefreshTokenService
from app.modules.superadmin.application.services.audit_service import AuditService
from app.core.exceptions import ValidationError
from app.core.config import settings

logger = logging.getLogger(__name__)


class LogoutUseCase:
    """
    Caso de uso para cierre de sesión.
    
    Maneja la lógica de negocio para:
    - Revocar refresh token
    - Registrar evento de auditoría
    - Manejar diferentes tipos de cliente (web/mobile)
    """
    
    def __init__(
        self,
        refresh_token_service: Optional[RefreshTokenService] = None
    ):
        """
        Inicializa el caso de uso.
        
        Args:
            refresh_token_service: Servicio de refresh tokens (opcional)
        """
        self.refresh_token_service = refresh_token_service or RefreshTokenService()
    
    async def execute(
        self,
        current_user_data: Dict[str, Any],
        refresh_token: Optional[str] = None,
        client_type: str = "web",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta el caso de uso de logout.
        
        Args:
            current_user_data: Datos del usuario autenticado
            refresh_token: Refresh token a revocar (opcional)
            client_type: Tipo de cliente (web/mobile)
            ip_address: IP del cliente
            user_agent: User agent del navegador
        
        Returns:
            Diccionario con mensaje de éxito
        
        Raises:
            ValidationError: Si los datos del usuario son inválidos
        """
        # 1. Validar datos del usuario
        cliente_id = current_user_data.get("cliente_id")
        usuario_id = current_user_data.get("usuario_id")
        username = current_user_data.get("nombre_usuario")
        
        if not cliente_id or not usuario_id:
            raise ValidationError(
                detail="Contexto de usuario inválido",
                internal_code="INVALID_USER_CONTEXT"
            )
        
        # 2. Revocar refresh token si se proporciona
        if refresh_token:
            try:
                revoked = await self.refresh_token_service.revoke_token(
                    cliente_id=cliente_id,
                    usuario_id=usuario_id,
                    token=refresh_token
                )
                
                if revoked:
                    logger.info(
                        f"[LOGOUT-{client_type.upper()}] Token revocado exitosamente - "
                        f"Cliente: {cliente_id}, Usuario: {usuario_id} ({username})"
                    )
                else:
                    logger.warning(
                        f"[LOGOUT-{client_type.upper()}] Token no encontrado para revocar - "
                        f"Cliente: {cliente_id}, Usuario: {usuario_id} ({username})"
                    )
                
                # Registrar evento de auditoría
                try:
                    await AuditService.registrar_auth_event(
                        cliente_id=cliente_id,
                        usuario_id=usuario_id,
                        evento="logout",
                        nombre_usuario_intento=username,
                        descripcion=f"Logout de sesión ({client_type})",
                        exito=True,
                        codigo_error=None,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        metadata={
                            "client_type": client_type,
                            "token_revoked": revoked
                        },
                    )
                except Exception:
                    logger.exception("[AUDIT] Error registrando evento logout (no crítico)")
                    
            except Exception as revoke_err:
                logger.warning(
                    f"[LOGOUT-{client_type.upper()}] Error revocando token (no crítico): {str(revoke_err)}"
                )
                # No propagar el error, el logout sigue siendo exitoso
        else:
            # No se proporcionó refresh token - NO es error, logout válido
            logger.info(
                f"[LOGOUT-{client_type.upper()}] Logout sin refresh token proporcionado - "
                f"Cliente: {cliente_id}, Usuario: {usuario_id} ({username})"
            )
            
            # Registrar logout exitoso sin token
            try:
                await AuditService.registrar_auth_event(
                    cliente_id=cliente_id,
                    usuario_id=usuario_id,
                    evento="logout",
                    nombre_usuario_intento=username,
                    descripcion="Logout de sesión (sin refresh token)",
                    exito=True,
                    codigo_error=None,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata={
                        "client_type": client_type,
                        "no_token_provided": True,
                    },
                )
            except Exception:
                logger.exception("[AUDIT] Error registrando evento logout sin token (no crítico)")
        
        return {
            "message": f"Sesión cerrada exitosamente ({client_type})"
        }

