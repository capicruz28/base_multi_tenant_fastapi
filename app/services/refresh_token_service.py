# app/services/refresh_token_service.py
"""
Servicio para gestión de refresh tokens persistentes en base de datos.

Este servicio maneja el ciclo de vida completo de los refresh tokens:
- Almacenamiento seguro con hash SHA-256
- Validación contra base de datos
- Revocación individual y masiva
- Auditoría de sesiones activas
- Limpieza de tokens expirados

Características principales:
- **Seguridad:** Los tokens se almacenan hasheados (SHA-256), nunca en texto plano
- **Rotación:** Soporte para rotación automática de tokens
- **Auditoría:** Registro de IP, user-agent y tipo de cliente
- **Revocación:** Capacidad de invalidar tokens inmediatamente
- **Limpieza:** Eliminación automática de tokens expirados
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
import hashlib
import logging

# Se asume la existencia de estos módulos y constantes en la estructura del proyecto
from app.db.queries import (
    execute_insert, execute_query, execute_update,
    INSERT_REFRESH_TOKEN, GET_REFRESH_TOKEN_BY_HASH,
    REVOKE_REFRESH_TOKEN, REVOKE_REFRESH_TOKEN_BY_USER, REVOKE_ALL_USER_TOKENS,
    DELETE_EXPIRED_TOKENS, GET_ACTIVE_SESSIONS_BY_USER,
    GET_ALL_ACTIVE_SESSIONS, REVOKE_REFRESH_TOKEN_BY_ID
)
from app.core.config import settings
# Importamos las excepciones personalizadas para un manejo de errores consistente
from app.core.exceptions import DatabaseError, AuthenticationError, CustomException 
from app.services.base_service import BaseService # Asumimos la clase base para el decorador handle_service_errors
from app.core.tenant_context import get_current_client_id

logger = logging.getLogger(__name__)

class RefreshTokenService(BaseService):
    """
    Servicio para gestión de refresh tokens persistentes.
    
    Implementa el patrón de almacenamiento seguro de tokens y la mitigación
    de ataques de reuso de token (Token Reuse Detection).
    """
    
    @staticmethod
    def hash_token(token: str) -> str:
        """
        Genera hash SHA-256 del token para almacenamiento seguro.
        """
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    @BaseService.handle_service_errors 
    async def store_refresh_token(
        cliente_id: int,
        usuario_id: int,
        token: str,
        client_type: str = "web",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict:
        """
        Almacena un nuevo refresh token en la base de datos **para un cliente específico**.
        
        **MITIGACIÓN DE SEGURIDAD CLAVE:** Si la inserción falla por llave duplicada
        (el `token_hash` ya existe), revoca todas las sesiones del usuario y lanza
        AuthenticationError (HTTP 401).
        """
        # Intentamos el bloque principal para capturar errores de servicio/base de datos
        try:
            # 1) Hashear el token y calcular expiración
            token_hash = RefreshTokenService.hash_token(token)
            expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            
            # 2) Preparar parámetros
            params = (                
                usuario_id,
                token_hash,
                expires_at,
                client_type,
                ip_address,
                user_agent[:500] if user_agent else None, 
                cliente_id,
            )
            
            # 3) Intentar insertar en BD
            result = execute_insert(INSERT_REFRESH_TOKEN, params)
            
            logger.info(
                f"[STORE-TOKEN] Cliente {cliente_id}, Usuario {usuario_id} - Cliente: {client_type} - "
                f"Token ID: {result.get('token_id')}"
            )
            
            return result
        
        # 4) MANEJO DE ERROR DE LLAVE DUPLICADA (SOLUCIÓN DE SEGURIDAD)
        except DatabaseError as db_err:
            # Detectar la colisión de llave única (por token_hash)
            # Buscamos patrones comunes de error de llave duplicada en el detalle
            err_detail = str(db_err.detail).lower()
            if "unique key constraint" in err_detail or "duplicate key" in err_detail or "violación de la restricción unique" in err_detail:
                
                # 🚨 MEDIDA DE SEGURIDAD CRÍTICA: REVOCACIÓN MASIVA 
                logger.critical(
                    f"[SECURITY ALERT - TOKEN REUSE] Colisión de Refresh Token (hash) detectada para cliente {cliente_id}, usuario {usuario_id}. "
                    "Revocando todas las sesiones del usuario para mitigar el riesgo."
                )
                
                # Ejecutar revocación global (logout de emergencia)
                await RefreshTokenService.revoke_all_user_tokens(cliente_id, usuario_id)
                
                # Lanzar AuthenticationError para forzar un 401 en el endpoint
                raise AuthenticationError(
                    detail="Error de seguridad: Posible reuso de token detectado. Todas las sesiones han sido cerradas.",
                    internal_code="REFRESH_TOKEN_REUSE_DETECTED"
                )
            
            # Si es otro error de base de datos, re-lanzar el error original
            raise

        except AuthenticationError:
            # Propagar la excepción de seguridad (Token Reuse)
            raise 
        except CustomException:
            # Propagar otros errores personalizados
            raise
        except Exception as e:
            # Para errores inesperados que no sean CustomException
            logger.exception(f"Error inesperado almacenando refresh token para cliente {cliente_id}: {str(e)}")
            raise DatabaseError(
                detail="Error no manejado al almacenar el refresh token",
                internal_code="REFRESH_TOKEN_STORE_UNHANDLED_ERROR"
            )
    
    @staticmethod
    @BaseService.handle_service_errors
    async def validate_refresh_token(token: str) -> Optional[Dict]:
        """
        Valida un refresh token contra la base de datos.
        
        Verifica que el token:
        - Exista en la BD
        - No esté revocado (is_revoked = 0)
        - No haya expirado (expires_at > NOW)
        """
        try:
            cliente_id = get_current_client_id()
            token_hash = RefreshTokenService.hash_token(token)
            result = execute_query(GET_REFRESH_TOKEN_BY_HASH, (token_hash,cliente_id))
            
            if not result:
                logger.warning("[VALIDATE-TOKEN] Token no encontrado, revocado o expirado")
                return None
            
            token_data = result[0]
            logger.info(
                f"[VALIDATE-TOKEN] Token válido para cliente {token_data['cliente_id']}, usuario {token_data['usuario_id']} - "
                f"Cliente: {token_data.get('client_type', 'unknown')}"
            )
            
            return token_data
        
        except CustomException:
            raise
        except Exception as e:
            logger.exception(f"Error inesperado validando refresh token: {str(e)}")
            raise DatabaseError(
                detail="Error al validar el refresh token",
                internal_code="REFRESH_TOKEN_VALIDATE_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def revoke_token(cliente_id: int, usuario_id: int, token: str) -> bool:
        """
        Revoca un refresh token específico **para un cliente y usuario**.
        Utiliza la versión segura `REVOKE_REFRESH_TOKEN_BY_USER` para evitar ataques de revocación cruzada.
        """
        try:
            token_hash = RefreshTokenService.hash_token(token)
            result = execute_update(REVOKE_REFRESH_TOKEN_BY_USER, (token_hash, usuario_id, cliente_id))
            
            rows_affected = result.get('rows_affected', 0)
            
            if rows_affected > 0:
                logger.info(f"[REVOKE-TOKEN] Token revocado exitosamente para cliente {cliente_id}, usuario {usuario_id}")
                return True
            
            logger.warning(f"[REVOKE-TOKEN] Token no encontrado o ya estaba revocado para cliente {cliente_id}, usuario {usuario_id}")
            return False
        
        except CustomException:
            raise
        except Exception as e:
            logger.exception(f"Error inesperado revocando token para cliente {cliente_id}, usuario {usuario_id}: {str(e)}")
            raise DatabaseError(
                detail="Error al revocar el refresh token",
                internal_code="REFRESH_TOKEN_REVOKE_ERROR"
            )


    @staticmethod
    @BaseService.handle_service_errors
    async def revoke_all_user_tokens(cliente_id: int, usuario_id: int) -> int:
        """
        Revoca todos los tokens activos de un usuario **en un cliente específico** (logout global).
        """
        try:
            # Pasar ambos IDs para mayor seguridad y precisión
            result = execute_update(REVOKE_ALL_USER_TOKENS, (cliente_id, usuario_id))
            rows_affected = result.get('rows_affected', 0)
            
            logger.info(
                f"[REVOKE-ALL] {rows_affected} tokens revocados para cliente {cliente_id}, usuario {usuario_id}"
            )
            
            return rows_affected
        
        except CustomException:
            raise
        except Exception as e:
            logger.exception(f"Error inesperado revocando tokens del usuario para cliente {cliente_id}: {str(e)}")
            raise DatabaseError(
                detail="Error al revocar los tokens del usuario",
                internal_code="REFRESH_TOKEN_REVOKE_ALL_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def get_active_sessions(cliente_id: int, usuario_id: int) -> List[Dict]:
        """
        Obtiene todas las sesiones activas de un usuario **en un cliente específico**.
        """
        try:
            sessions = execute_query(GET_ACTIVE_SESSIONS_BY_USER, (cliente_id, usuario_id))
            
            logger.info(
                f"[SESSIONS] Cliente {cliente_id}, Usuario {usuario_id} tiene {len(sessions)} sesiones activas"
            )
            
            return sessions
        
        except CustomException:
            raise
        except Exception as e:
            logger.exception(f"Error inesperado obteniendo sesiones para cliente {cliente_id}, usuario {usuario_id}: {str(e)}")
            raise DatabaseError(
                detail="Error al obtener las sesiones activas",
                internal_code="REFRESH_TOKEN_SESSIONS_ERROR"
            )
    
    @staticmethod
    @BaseService.handle_service_errors
    async def cleanup_expired_tokens() -> int:
        """
        Limpia tokens expirados y revocados de la base de datos.
        Esta operación no necesita cliente_id porque es global.
        """
        try:
            result = execute_update(DELETE_EXPIRED_TOKENS, ())
            rows_affected = result.get('rows_affected', 0)
            
            logger.info(f"[CLEANUP] {rows_affected} tokens expirados/revocados eliminados")
            
            return rows_affected
        
        except CustomException:
            raise
        except Exception as e:
            logger.exception(f"Error inesperado limpiando tokens: {str(e)}")
            raise DatabaseError(
                detail="Error al limpiar tokens expirados",
                internal_code="REFRESH_TOKEN_CLEANUP_ERROR"
            )

    # =========================================================================
    # --- MÉTODOS DE ADMINISTRACIÓN DE SESIONES (NUEVOS) ---
    # =========================================================================

    @staticmethod
    @BaseService.handle_service_errors
    async def get_all_active_sessions_for_admin(cliente_id: int) -> List[Dict]:
        """
        [ADMIN] Obtiene todas las sesiones activas en el sistema para auditoría
        y administración.
        
        Nota: Esta operación debe ser restringida a administradores en el endpoint.
        """
        try:
            # La consulta no requiere parámetros
            sessions = execute_query(GET_ALL_ACTIVE_SESSIONS, (cliente_id))
            
            logger.info(
                f"[ADMIN-SESSIONS] Se recuperaron {len(sessions)} sesiones activas totales."
            )
            
            return sessions
        
        except CustomException:
            raise
        except Exception as e:
            logger.exception(f"[ADMIN-SESSIONS] Error inesperado obteniendo todas las sesiones: {str(e)}")
            raise DatabaseError(
                detail="Error al obtener la lista global de sesiones activas (Admin)",
                internal_code="ADMIN_SESSIONS_LIST_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def revoke_refresh_token_by_id(token_id: int) -> bool:
        """
        [ADMIN] Revoca un refresh token específico utilizando su ID (PK).
        """
        try:
            result = execute_update(REVOKE_REFRESH_TOKEN_BY_ID, (token_id,))
            
            # ✅ Validar por OUTPUT en lugar de rows_affected
            if result and result.get('token_id'):
                logger.info(
                    f"[ADMIN-REVOKE] Token ID {token_id} revocado - Cliente: {result.get('cliente_id')}, Usuario: {result.get('usuario_id')}"
                )
                return True
            
            logger.warning(f"[ADMIN-REVOKE] Token ID {token_id} no encontrado o ya revocado")
            return False
        
        except CustomException:
            raise
        except Exception as e:
            logger.exception(f"[ADMIN-REVOKE] Error revocando token ID {token_id}: {str(e)}")
            raise DatabaseError(
                detail=f"Error al revocar el refresh token con ID {token_id}",
                internal_code="ADMIN_REFRESH_TOKEN_REVOKE_BY_ID_ERROR"
            )