# app/services/refresh_token_service.py
"""
Servicio para gestión de refresh tokens persistentes en base de datos.

✅ CORRECCIÓN CRÍTICA: Implementa rotación segura de tokens sin falsos positivos.
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
from uuid import UUID
import hashlib
import logging

# ✅ FASE 2: Migrar a queries_async
from app.infrastructure.database.queries_async import (
    execute_insert, execute_query, execute_update
)
from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.sql_constants import (
    INSERT_REFRESH_TOKEN, GET_REFRESH_TOKEN_BY_HASH,
    REVOKE_REFRESH_TOKEN_BY_USER, REVOKE_ALL_USER_TOKENS,
    DELETE_EXPIRED_TOKENS, GET_ACTIVE_SESSIONS_BY_USER,
    GET_ALL_ACTIVE_SESSIONS, REVOKE_REFRESH_TOKEN_BY_ID
)
# ✅ Importar REVOKE_REFRESH_TOKEN desde queries modulares (revoca token específico por hash)
from app.infrastructure.database.queries.auth.auth_queries import (
    REVOKE_REFRESH_TOKEN
)
# ✅ FASE 1 SEGURIDAD: Importar funciones SQLAlchemy Core para queries críticas
from app.infrastructure.database.queries.auth.refresh_token_queries_core import (
    get_refresh_token_by_hash_core,
    insert_refresh_token_core,
    revoke_refresh_token_core,
    revoke_all_user_tokens_core,
    get_active_sessions_by_user_core,
    delete_expired_tokens_core
)
from sqlalchemy import text
from app.core.config import settings
from app.core.exceptions import DatabaseError, AuthenticationError, CustomException, ValidationError 
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
        cliente_id: UUID,
        usuario_id: UUID,
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
            # ✅ FASE 1 SEGURIDAD: Usar función SQLAlchemy Core para máxima seguridad
            if is_rotation:
                try:
                    # Verificar si este token exacto ya está en BD usando SQLAlchemy Core
                    existing = await get_refresh_token_by_hash_core(token_hash, cliente_id)
                    if existing:
                        logger.info(
                            f"[STORE-TOKEN-ROTATION] Token ya existe en BD (doble refresh detectado) - "
                            f"Cliente {cliente_id}, Usuario {usuario_id}, Token ID: {existing.get('token_id')}"
                        )
                        # Retornar el existente sin hacer nada
                        return {
                            "token_id": existing.get("token_id"),
                            "duplicate_ignored": True,
                            "exists": True
                        }
                except Exception as check_err:
                    logger.warning(f"[STORE-TOKEN-ROTATION] Error verificando existencia: {check_err}")
                    # Continuar con la inserción si falla la verificación
            
            # ✅ FASE 1 SEGURIDAD: Usar función SQLAlchemy Core para inserción segura
            result = await insert_refresh_token_core(
                usuario_id=usuario_id,
                token_hash=token_hash,
                expires_at=expires_at,
                cliente_id=cliente_id,
                client_type=client_type,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
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
            # ✅ FASE 1 SEGURIDAD: Usar función SQLAlchemy Core para máxima seguridad
            token_data = await get_refresh_token_by_hash_core(token_hash, cliente_id)
            
            if not token_data:
                logger.warning(
                    f"[VALIDATE-TOKEN] Token no encontrado, revocado o expirado - Cliente {cliente_id}"
                )
                return None
            
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
    async def revoke_token(cliente_id: UUID, usuario_id: UUID, token: str) -> bool:
        """
        Revoca un refresh token específico por su hash.
        
        ✅ CORRECCIÓN CRÍTICA: Usa REVOKE_REFRESH_TOKEN (por hash) en lugar de 
        REVOKE_REFRESH_TOKEN_BY_USER (que revoca todos los tokens del usuario).
        """
        try:
            token_hash = RefreshTokenService.hash_token(token)
            # ✅ FASE 1 SEGURIDAD: Usar función SQLAlchemy Core para máxima seguridad
            result = await revoke_refresh_token_core(token_hash, cliente_id)
            
            if result and result.get('is_revoked'):
                logger.info(
                    f"[REVOKE-TOKEN] Token específico revocado exitosamente - "
                    f"Cliente {cliente_id}, Usuario {usuario_id}, Token ID: {result.get('token_id')}, Hash: {token_hash[:16]}..."
                )
                return True
            
            logger.warning(
                f"[REVOKE-TOKEN] Token no encontrado o ya revocado - "
                f"Cliente {cliente_id}, Usuario {usuario_id}, Hash: {token_hash[:16]}..."
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
    async def revoke_all_user_tokens(cliente_id: UUID, usuario_id: UUID) -> int:
        """
        Revoca todos los tokens activos de un usuario (logout global).
        """
        try:
            # ✅ FASE 1 SEGURIDAD: Usar función SQLAlchemy Core para máxima seguridad
            rows_affected = await revoke_all_user_tokens_core(usuario_id, cliente_id)
            
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
    async def get_active_sessions(cliente_id: UUID, usuario_id: UUID) -> List[Dict]:
        """
        Obtiene todas las sesiones activas de un usuario.
        """
        try:
            # ✅ FASE 1 SEGURIDAD: Usar función SQLAlchemy Core para máxima seguridad
            sessions = await get_active_sessions_by_user_core(usuario_id, cliente_id)
            
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
        
        ✅ FASE 2: Requiere contexto de tenant para funcionar correctamente.
        ✅ FASE 4: Para limpiar todos los tenants, usar RefreshTokenCleanupJob.cleanup_all_tenants()
        
        Funciona tanto para Single-DB como Multi-DB:
        - Single-DB: Limpia tokens del cliente_id en bd_sistema
        - Multi-DB: Limpia tokens del cliente_id en su BD dedicada
        """
        try:
            # ✅ FASE 2: Obtener cliente_id del contexto
            cliente_id = get_current_client_id()
            
            # ✅ FASE 1 SEGURIDAD: Usar función SQLAlchemy Core para máxima seguridad
            rows_affected = await delete_expired_tokens_core(cliente_id)
            
            logger.info(
                f"[CLEANUP] {rows_affected} tokens expirados/revocados eliminados "
                f"para cliente {cliente_id}"
            )
            
            return rows_affected
        
        except RuntimeError:
            # Sin contexto de tenant
            raise ValidationError(
                detail="cleanup_expired_tokens requiere contexto de tenant. "
                       "Use RefreshTokenCleanupJob.cleanup_all_tenants() para limpiar todos los tenants.",
                internal_code="TENANT_CONTEXT_REQUIRED"
            )
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
    async def get_all_active_sessions_for_admin(cliente_id: UUID) -> List[Dict]:
        """
        [ADMIN] Obtiene todas las sesiones activas en el sistema para auditoría.
        """
        try:
            # ✅ FASE 2: Usar await
            sessions = await execute_query(
                text(GET_ALL_ACTIVE_SESSIONS).bindparams(
                    cliente_id=cliente_id
                )
            )
            
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
    async def revoke_refresh_token_by_id(token_id: UUID) -> bool:
        """
        [ADMIN] Revoca un refresh token específico utilizando su ID (PK).
        
        ✅ FASE 2: Requiere contexto de tenant para asegurar que solo se revoquen
        tokens del tenant actual.
        """
        try:
            # ✅ FASE 2: Obtener cliente_id del contexto
            cliente_id = get_current_client_id()
            
            # ✅ FASE 2: Usar parámetros nombrados con cliente_id
            result = await execute_update(
                text(REVOKE_REFRESH_TOKEN_BY_ID).bindparams(
                    token_id=token_id,
                    cliente_id=cliente_id
                ),
                connection_type=DatabaseConnection.DEFAULT,
                client_id=cliente_id
            )
            
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