# app/modules/auth/application/use_cases/refresh_token_use_case.py
"""
RefreshTokenUseCase: Caso de uso para renovación de tokens.

✅ FASE 3: ARQUITECTURA - Use Case para Refresh Token
"""

from typing import Optional, Dict, Any
import logging

from app.modules.auth.domain.entities.usuario import Usuario
from app.modules.auth.infrastructure.repositories.usuario_repository import UsuarioRepository
from app.modules.auth.application.services.refresh_token_service import RefreshTokenService
from app.core.auth import create_access_token, create_refresh_token, get_user_access_level_info
from app.core.exceptions import ValidationError, NotFoundError, AuthenticationError
from app.core.tenant.context import get_current_client_id

logger = logging.getLogger(__name__)


class RefreshTokenUseCase:
    """
    Caso de uso para renovación de tokens de acceso.
    
    Maneja la lógica de negocio para:
    - Validar refresh token
    - Generar nuevos tokens
    - Rotar refresh tokens de forma segura
    """
    
    def __init__(
        self,
        usuario_repository: Optional[UsuarioRepository] = None,
        refresh_token_service: Optional[RefreshTokenService] = None
    ):
        """
        Inicializa el caso de uso.
        
        Args:
            usuario_repository: Repositorio de usuarios (opcional)
            refresh_token_service: Servicio de refresh tokens (opcional)
        """
        self.usuario_repository = usuario_repository or UsuarioRepository()
        self.refresh_token_service = refresh_token_service or RefreshTokenService()
    
    async def execute(
        self,
        old_refresh_token: str,
        current_user_data: Dict[str, Any],
        client_type: str = "web",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta el caso de uso de refresh token.
        
        Args:
            old_refresh_token: Refresh token actual a rotar
            current_user_data: Datos del usuario del token actual
            client_type: Tipo de cliente (web/mobile)
            ip_address: IP del cliente
            user_agent: User agent del navegador
        
        Returns:
            Diccionario con nuevos tokens (access_token, refresh_token)
        
        Raises:
            ValidationError: Si el token es inválido
            AuthenticationError: Si la autenticación falla
        """
        # 1. Validar datos del usuario
        username = current_user_data.get("nombre_usuario")
        cliente_id = current_user_data.get("cliente_id")
        usuario_id = current_user_data.get("usuario_id")
        
        if not username or not cliente_id or not usuario_id:
            raise ValidationError(
                detail="Datos de usuario inválidos en el refresh token",
                internal_code="INVALID_REFRESH_TOKEN_DATA"
            )
        
        # 2. Obtener información de niveles de acceso
        level_info = get_user_access_level_info(usuario_id, cliente_id)
        
        # 3. Preparar datos para nuevos tokens
        token_data = {
            "sub": username,
            "cliente_id": cliente_id,
            "level_info": level_info
        }
        
        # 4. Generar nuevos tokens
        new_access_token = create_access_token(data=token_data)
        new_refresh_token = create_refresh_token(data=token_data)
        
        # 5. Almacenar nuevo refresh token con rotación
        try:
            stored = await self.refresh_token_service.store_refresh_token(
                cliente_id=cliente_id,
                usuario_id=usuario_id,
                token=new_refresh_token,
                client_type=client_type,
                ip_address=ip_address,
                user_agent=user_agent,
                is_rotation=True  # Es una rotación
            )
            
            # 6. Revocar token antiguo solo si el nuevo se guardó correctamente
            if stored and not stored.get('duplicate_ignored'):
                try:
                    await self.refresh_token_service.revoke_token(
                        cliente_id=cliente_id,
                        usuario_id=usuario_id,
                        token=old_refresh_token
                    )
                    logger.info(f"[REFRESH] Token antiguo revocado después de rotación exitosa")
                except Exception as revoke_err:
                    logger.warning(f"[REFRESH] Error revocando token antiguo (no crítico): {str(revoke_err)}")
            
            logger.info(f"Refresh token exitoso para usuario: {username} (ID: {usuario_id})")
            
            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            logger.error(f"Error en refresh token: {str(e)}")
            raise AuthenticationError(
                detail="Error al renovar el token",
                internal_code="REFRESH_TOKEN_ERROR"
            )

