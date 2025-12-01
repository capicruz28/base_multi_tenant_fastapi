# app/services/refresh_token_service.py
"""
Servicio para gestión de refresh tokens persistentes en base de datos.

✅ CORRECCIÓN CRÍTICA: Implementa rotación segura de tokens sin falsos positivos.
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
import hashlib
import logging

from app.infrastructure.database.queries import (
    execute_insert, execute_query, execute_update,
    INSERT_REFRESH_TOKEN, GET_REFRESH_TOKEN_BY_HASH,
    REVOKE_REFRESH_TOKEN, REVOKE_REFRESH_TOKEN_BY_USER, REVOKE_ALL_USER_TOKENS,
    DELETE_EXPIRED_TOKENS, GET_ACTIVE_SESSIONS_BY_USER,
    GET_ALL_ACTIVE_SESSIONS, REVOKE_REFRESH_TOKEN_BY_ID
)
from app.core.config import settings
from app.core.exceptions import DatabaseError, AuthenticationError, CustomException 
from app.core.application.base_service import BaseService
from app.core.tenant.context import get_current_client_id
from app.modules.superadmin.application.services.audit_service import AuditService

logger = logging.getLogger(__name__)

class RefreshTokenService(BaseService):
    """
    Servicio para gestión de refresh tokens persistentes.
    
    ✅ Implementa rotación segura de tokens con detección real de reuso.
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
        user_agent: Optional[str] = None,
        is_rotation: bool = False  # ✅ NUEVO: Indica si es una rotación (refresh)
    ) -> Dict:
        """
        Almacena un nuevo refresh token en la base de datos.
        
        ✅ CORRECCIÓN CRÍTICA: Maneja rotación de tokens sin falsos positivos.
        
        Args:
            cliente_id: ID del cliente
            usuario_id: ID del usuario
            token: Token a almacenar (sin hashear)
            client_type: Tipo de cliente (web/mobile)
            ip_address: IP del cliente
            user_agent: User agent del navegador
            is_rotation: True si es una rotación (refresh), False si es nuevo (login)
        
        Returns:
            Dict con token_id y metadata
        """
        try:
            token_hash = RefreshTokenService.hash_token(token)
            expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            
            # ✅ CORRECCIÓN: Si es rotación, verificar si el token ya existe (doble refresh)
            if is_rotation:
                try:
                    # Verificar si este token exacto ya está en BD
                    existing = execute_query(GET_REFRESH_TOKEN_BY_HASH, (token_hash, cliente_id))
                    if existing and len(existing) > 0:
                        token_data = existing[0]
                        logger.info(
                            f"[STORE-TOKEN-ROTATION] Token ya existe en BD (doble refresh detectado) - "
                            f"Cliente {cliente_id}, Usuario {usuario_id}, Token ID: {token_data.get('token_id')}"
                        )
                        # Retornar el existente sin hacer nada
                        return {
                            "token_id": token_data.get("token_id"),
                            "duplicate_ignored": True,
                            "exists": True
                        }
                except Exception as check_err:
                    logger.warning(f"[STORE-TOKEN-ROTATION] Error verificando existencia: {check_err}")
                    # Continuar con la inserción si falla la verificación
            
            # Preparar parámetros para inserción
            params = (                
                usuario_id,
                token_hash,
                expires_at,
                client_type,
                ip_address,
                user_agent[:500] if user_agent else None, 
                cliente_id,
            )
            
            # Intentar insertar
            result = execute_insert(INSERT_REFRESH_TOKEN, params)
            
            logger.info(
                f"[STORE-TOKEN] Token insertado exitosamente - "
                f"Cliente {cliente_id}, Usuario {usuario_id}, Tipo: {client_type}, "
                f"Token ID: {result.get('token_id')}, Rotación: {is_rotation}"
            )
            
            return result
        
        except DatabaseError as db_err:
            err_detail = str(db_err.detail).lower()
            
            # Verificar si es un error de llave duplicada
            is_duplicate_error = (
                "unique key constraint" in err_detail or 
                "duplicate key" in err_detail or 
                "violación de la restricción unique" in err_detail or
                "unique constraint" in err_detail
            )
            
            if is_duplicate_error:
                # ✅ CORRECCIÓN CRÍTICA: Distinguir entre rotación normal y reuso malicioso
                if is_rotation:
                    # Esto es NORMAL en refresh - múltiples llamadas simultáneas
                    logger.info(
                        f"[STORE-TOKEN-ROTATION] Duplicado detectado durante rotación (esperado) - "
                        f"Cliente {cliente_id}, Usuario {usuario_id}. Ignorando."
                    )
                    return {
                        "token_id": -1,
                        "duplicate_ignored": True,
                        "is_rotation": True
                    }
                else:
                    # Esto es SOSPECHOSO - un login está intentando usar un token existente
                    logger.critical(
                        f"[SECURITY ALERT - TOKEN REUSE] Colisión de Refresh Token durante LOGIN para "
                        f"cliente {cliente_id}, usuario {usuario_id}. Revocando todas las sesiones."
                    )

                    # Registrar posible reuso malicioso de token en auditoría
                    try:
                        await AuditService.registrar_auth_event(
                            cliente_id=cliente_id,
                            usuario_id=usuario_id,
                            evento="token_reuse_detected",
                            nombre_usuario_intento=None,
                            descripcion="Posible reuso malicioso de refresh token detectado durante login",
                            exito=False,
                            codigo_error="REFRESH_TOKEN_REUSE_DETECTED",
                            ip_address=None,
                            user_agent=None,
                            metadata={"context": "login"},
                        )
                    except Exception:
                        logger.exception(
                            "[AUDIT] Error registrando evento token_reuse_detected (no crítico)"
                        )

                    # Revocar todas las sesiones como medida de seguridad
                    await RefreshTokenService.revoke_all_user_tokens(cliente_id, usuario_id)

                    raise AuthenticationError(
                        detail="Error de seguridad: Posible reuso de token detectado. Todas las sesiones han sido cerradas.",
                        internal_code="REFRESH_TOKEN_REUSE_DETECTED"
                    )
            
            # Si es otro tipo de error de BD, re-lanzar
            raise

        except AuthenticationError:
            raise 
        except CustomException:
            raise
        except Exception as e:
            logger.exception(
                f"[STORE-TOKEN] Error inesperado almacenando refresh token - "
                f"Cliente {cliente_id}, Usuario {usuario_id}: {str(e)}"
            )
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
            result = execute_query(GET_REFRESH_TOKEN_BY_HASH, (token_hash, cliente_id))
            
            if not result or len(result) == 0:
                logger.warning(
                    f"[VALIDATE-TOKEN] Token no encontrado, revocado o expirado - Cliente {cliente_id}"
                )
                return None
            
            token_data = result[0]
            logger.info(
                f"[VALIDATE-TOKEN] Token válido - Cliente {token_data['cliente_id']}, "
                f"Usuario {token_data['usuario_id']}, Tipo: {token_data.get('client_type', 'unknown')}"
            )
            
            return token_data
        
        except CustomException:
            raise
        except Exception as e:
            logger.exception(f"[VALIDATE-TOKEN] Error inesperado validando refresh token: {str(e)}")
            raise DatabaseError(
                detail="Error al validar el refresh token",
                internal_code="REFRESH_TOKEN_VALIDATE_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def revoke_token(cliente_id: int, usuario_id: int, token: str) -> bool:
        """
        Revoca un refresh token específico.
        """
        try:
            token_hash = RefreshTokenService.hash_token(token)
            result = execute_update(REVOKE_REFRESH_TOKEN_BY_USER, (token_hash, usuario_id, cliente_id))
            
            rows_affected = result.get('rows_affected', 0)
            
            if rows_affected > 0:
                logger.info(
                    f"[REVOKE-TOKEN] Token revocado exitosamente - Cliente {cliente_id}, Usuario {usuario_id}"
                )
                return True
            
            logger.warning(
                f"[REVOKE-TOKEN] Token no encontrado o ya revocado - Cliente {cliente_id}, Usuario {usuario_id}"
            )
            return False
        
        except CustomException:
            raise
        except Exception as e:
            logger.exception(
                f"[REVOKE-TOKEN] Error inesperado revocando token - Cliente {cliente_id}, Usuario {usuario_id}: {str(e)}"
            )
            raise DatabaseError(
                detail="Error al revocar el refresh token",
                internal_code="REFRESH_TOKEN_REVOKE_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def revoke_all_user_tokens(cliente_id: int, usuario_id: int) -> int:
        """
        Revoca todos los tokens activos de un usuario (logout global).
        """
        try:
            result = execute_update(REVOKE_ALL_USER_TOKENS, (cliente_id, usuario_id))
            rows_affected = result.get('rows_affected', 0)
            
            logger.info(
                f"[REVOKE-ALL] {rows_affected} tokens revocados - Cliente {cliente_id}, Usuario {usuario_id}"
            )
            
            return rows_affected
        
        except CustomException:
            raise
        except Exception as e:
            logger.exception(
                f"[REVOKE-ALL] Error inesperado revocando todos los tokens - Cliente {cliente_id}, Usuario {usuario_id}: {str(e)}"
            )
            raise DatabaseError(
                detail="Error al revocar los tokens del usuario",
                internal_code="REFRESH_TOKEN_REVOKE_ALL_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def get_active_sessions(cliente_id: int, usuario_id: int) -> List[Dict]:
        """
        Obtiene todas las sesiones activas de un usuario.
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
            logger.exception(
                f"[SESSIONS] Error obteniendo sesiones - Cliente {cliente_id}, Usuario {usuario_id}: {str(e)}"
            )
            raise DatabaseError(
                detail="Error al obtener las sesiones activas",
                internal_code="REFRESH_TOKEN_SESSIONS_ERROR"
            )
    
    @staticmethod
    @BaseService.handle_service_errors
    async def cleanup_expired_tokens() -> int:
        """
        Limpia tokens expirados y revocados de la base de datos.
        """
        try:
            result = execute_update(DELETE_EXPIRED_TOKENS, ())
            rows_affected = result.get('rows_affected', 0)
            
            logger.info(f"[CLEANUP] {rows_affected} tokens expirados/revocados eliminados")
            
            return rows_affected
        
        except CustomException:
            raise
        except Exception as e:
            logger.exception(f"[CLEANUP] Error limpiando tokens: {str(e)}")
            raise DatabaseError(
                detail="Error al limpiar tokens expirados",
                internal_code="REFRESH_TOKEN_CLEANUP_ERROR"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def get_all_active_sessions_for_admin(cliente_id: int) -> List[Dict]:
        """
        [ADMIN] Obtiene todas las sesiones activas en el sistema para auditoría.
        """
        try:
            sessions = execute_query(GET_ALL_ACTIVE_SESSIONS, (cliente_id,))
            
            logger.info(
                f"[ADMIN-SESSIONS] {len(sessions)} sesiones activas recuperadas - Cliente {cliente_id}"
            )
            
            return sessions
        
        except CustomException:
            raise
        except Exception as e:
            logger.exception(f"[ADMIN-SESSIONS] Error obteniendo todas las sesiones: {str(e)}")
            raise DatabaseError(
                detail="Error al obtener la lista global de sesiones activas",
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
            
            if result and result.get('token_id'):
                logger.info(
                    f"[ADMIN-REVOKE] Token ID {token_id} revocado - "
                    f"Cliente: {result.get('cliente_id')}, Usuario: {result.get('usuario_id')}"
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