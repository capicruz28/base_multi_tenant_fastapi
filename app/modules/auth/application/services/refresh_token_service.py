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

# ✅ FASE 2: Migrar a queries_async (Core queries exclusivamente)
from app.infrastructure.database.queries.auth.refresh_token_queries_core import (
    record_refresh_token_activity_core,
    is_refresh_token_session_idle_expired_core,
    get_refresh_token_by_hash_core,
    insert_refresh_token_core,
    revoke_refresh_token_core,
    revoke_all_user_tokens_core,
    get_active_sessions_by_user_core,
    get_active_sessions_by_user_oldest_first_core,
    delete_expired_tokens_core,
    revoke_refresh_token_by_id_core,
)
from app.modules.auth.application.session.revoked_reason import RevokedReason
from app.modules.auth.application.services.auth_config_service import (
    leer_session_idle_timeout_minutos,
    leer_max_active_sessions,
)
from app.core.config import settings
from app.core.exceptions import DatabaseError, AuthenticationError, CustomException, ValidationError 
from app.core.application.base_service import BaseService
from app.core.tenant.context import get_current_client_id
from app.modules.superadmin.application.services.audit_service import AuditService

logger = logging.getLogger(__name__)

SESSION_ACCESS_JTI_PREFIX = "session:access_jti:"

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
    def _session_access_redis_key(token_id: UUID) -> str:
        return f"{SESSION_ACCESS_JTI_PREFIX}{token_id}"

    @staticmethod
    async def link_session_access_jti(
        token_id: UUID,
        access_jti: str,
        access_exp: Optional[int] = None,
        access_expire_minutes: Optional[int] = None,
    ) -> None:
        """Vincula el jti del access token emitido con la fila refresh_tokens (Redis, fail-soft)."""
        if not token_id or not access_jti:
            return
        try:
            from app.infrastructure.redis.client import RedisService
            from app.core.config import settings

            now_ts = int(datetime.utcnow().timestamp())
            if access_exp is None and access_expire_minutes is not None:
                access_exp = int(
                    (
                        datetime.utcnow()
                        + timedelta(minutes=access_expire_minutes)
                    ).timestamp()
                )
            ttl = 900
            if access_exp is not None:
                ttl = max(int(access_exp) - now_ts, 60)
            elif access_expire_minutes is not None:
                ttl = max(access_expire_minutes * 60, 60)
            else:
                ttl = max(settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, 60)
            await RedisService.set_json(
                RefreshTokenService._session_access_redis_key(token_id),
                {"jti": access_jti, "exp": access_exp},
                ttl,
            )
        except Exception as e:
            logger.warning(
                "[SESSION-ACCESS] No se pudo vincular access jti token_id=%s (fail-soft): %s",
                token_id,
                e,
            )

    @staticmethod
    async def blacklist_access_for_token_id(token_id: UUID) -> bool:
        """Blacklistea el access token vinculado a token_id, si existe en Redis."""
        if not token_id:
            return False
        try:
            from app.infrastructure.redis.client import RedisService
            from app.modules.auth.application.services.auth_service import AuthService

            key = RefreshTokenService._session_access_redis_key(token_id)
            payload = await RedisService.get_json(key)
            if not payload or not payload.get("jti"):
                return False
            await AuthService.blacklist_access_token_jti(
                payload["jti"], payload.get("exp")
            )
            await RedisService.delete_key(key)
            return True
        except Exception as e:
            logger.warning(
                "[SESSION-ACCESS] Error blacklist access token_id=%s (fail-soft): %s",
                token_id,
                e,
            )
            return False

    @staticmethod
    async def blacklist_access_for_user_active_sessions(
        cliente_id: UUID,
        usuario_id: UUID,
    ) -> int:
        """Blacklistea access tokens vinculados a sesiones activas del usuario."""
        blacklisted = 0
        try:
            sessions = await get_active_sessions_by_user_core(usuario_id, cliente_id)
            for session in sessions:
                token_id = session.get("token_id")
                if token_id and await RefreshTokenService.blacklist_access_for_token_id(
                    token_id
                ):
                    blacklisted += 1
        except Exception as e:
            logger.warning(
                "[SESSION-ACCESS] Error blacklist sesiones usuario=%s (fail-soft): %s",
                usuario_id,
                e,
            )
        return blacklisted

    @staticmethod
    async def handle_revoked_refresh_reuse(
        *,
        cliente_id: UUID,
        usuario_id: UUID,
        username: Optional[str],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        context: str = "refresh",
    ) -> None:
        """
        Reutilización de refresh revocado: auditoría + revoke_all + error de seguridad.
        """
        logger.critical(
            "[SECURITY ALERT - TOKEN REUSE] Refresh revocado reutilizado (%s) "
            "cliente=%s usuario=%s",
            context,
            cliente_id,
            usuario_id,
        )
        try:
            await AuditService.registrar_auth_event(
                cliente_id=cliente_id,
                usuario_id=usuario_id,
                evento="token_reuse_detected",
                nombre_usuario_intento=username,
                descripcion=(
                    "Reutilización de refresh token previamente revocado detectada"
                ),
                exito=False,
                codigo_error="REFRESH_TOKEN_REUSE_DETECTED",
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={"context": context},
            )
        except Exception:
            logger.exception(
                "[AUDIT] Error registrando token_reuse_detected (no crítico)"
            )

        await RefreshTokenService.blacklist_access_for_user_active_sessions(
            cliente_id, usuario_id
        )
        await RefreshTokenService.revoke_all_user_tokens(
            cliente_id, usuario_id, revoked_reason=RevokedReason.TOKEN_REUSE
        )

        raise AuthenticationError(
            detail=(
                "Error de seguridad: Posible reuso de token detectado. "
                "Todas las sesiones han sido cerradas."
            ),
            internal_code="REFRESH_TOKEN_REUSE_DETECTED",
        )
    
    @staticmethod
    def _sessions_to_revoke_for_limit(active_count: int, max_active: int) -> int:
        if max_active <= 0:
            return 0
        return max(0, active_count - max_active + 1)

    @staticmethod
    @BaseService.handle_service_errors
    async def enforce_max_active_sessions(
        cliente_id: UUID,
        usuario_id: UUID,
    ) -> int:
        """
        Revoca las sesiones más antiguas si se superaría max_active_sessions
        al insertar una nueva sesión.
        """
        max_sessions = await leer_max_active_sessions(cliente_id)
        if not max_sessions:
            return 0

        active_sessions = await get_active_sessions_by_user_oldest_first_core(
            usuario_id, cliente_id
        )
        revoke_count = RefreshTokenService._sessions_to_revoke_for_limit(
            len(active_sessions), max_sessions
        )
        if revoke_count <= 0:
            return 0

        revoked = 0
        for session in active_sessions[:revoke_count]:
            token_id = session.get("token_id")
            if not token_id:
                continue
            result = await revoke_refresh_token_by_id_core(
                token_id,
                cliente_id,
                revoked_reason=str(RevokedReason.SESSION_LIMIT),
            )
            if result:
                revoked += 1
                logger.info(
                    "[SESSION-LIMIT] Sesión antigua revocada token_id=%s "
                    "cliente=%s usuario=%s",
                    token_id,
                    cliente_id,
                    usuario_id,
                )

        if revoked:
            logger.info(
                "[SESSION-LIMIT] %s sesión(es) revocada(s) por límite (%s max) "
                "cliente=%s usuario=%s",
                revoked,
                max_sessions,
                cliente_id,
                usuario_id,
            )
        return revoked

    @staticmethod
    @BaseService.handle_service_errors 
    async def store_refresh_token(
        cliente_id: UUID,
        usuario_id: UUID,
        token: str,
        client_type: str = "web",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        is_rotation: bool = False,  # ✅ NUEVO: Indica si es una rotación (refresh)
        empresa_id: Optional[UUID] = None,
        refresh_token_expire_days: Optional[int] = None,
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
            refresh_days = (
                refresh_token_expire_days
                if refresh_token_expire_days is not None
                else settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
            expires_at = datetime.utcnow() + timedelta(days=refresh_days)
            
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

            if not is_rotation:
                await RefreshTokenService.enforce_max_active_sessions(
                    cliente_id, usuario_id
                )
            
            # ✅ FASE 1 SEGURIDAD: Usar función SQLAlchemy Core para inserción segura
            result = await insert_refresh_token_core(
                usuario_id=usuario_id,
                token_hash=token_hash,
                expires_at=expires_at,
                cliente_id=cliente_id,
                client_type=client_type,
                ip_address=ip_address,
                user_agent=user_agent,
                empresa_id=empresa_id,
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
                    await RefreshTokenService.revoke_all_user_tokens(
                        cliente_id,
                        usuario_id,
                        revoked_reason=RevokedReason.TOKEN_REUSE,
                    )

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
    def is_revoked_refresh_reuse_candidate(revoked_row: Optional[Dict]) -> bool:
        """
        Indica si un refresh revocado debe evaluarse como posible reuso malicioso.

        Solo aplica a rotaciones (SESSION_ROTATED) o filas legacy sin motivo.
        Idle timeout, logout u otras revocaciones legítimas no disparan reuse.
        """
        if not revoked_row or not revoked_row.get("is_revoked"):
            return False
        reason = revoked_row.get("revoked_reason")
        if reason is None:
            return True
        return str(reason) == RevokedReason.SESSION_ROTATED

    @staticmethod
    @BaseService.handle_service_errors
    async def validate_refresh_token(
        token: str,
        cliente_id: Optional[UUID] = None,
    ) -> Optional[Dict]:
        """
        Valida un refresh token contra la base de datos.
        
        Verifica que el token:
        - Exista en la BD
        - No esté revocado (is_revoked = 0)
        - No haya expirado (expires_at > NOW)

        Args:
            token: JWT refresh sin hashear (cookie/body).
            cliente_id: Tenant donde se persistió el token. Si se omite, se usa
                el contexto del request (puede fallar en platform si Host=backend
                y Origin no viaja). Preferir el claim ``cliente_id`` del JWT.
        """
        try:
            resolved_cliente_id = cliente_id
            if resolved_cliente_id is None:
                try:
                    resolved_cliente_id = get_current_client_id()
                except RuntimeError:
                    logger.warning(
                        "[VALIDATE-TOKEN] Sin cliente_id en JWT ni contexto de tenant"
                    )
                    return None

            token_hash = RefreshTokenService.hash_token(token)
            # ✅ FASE 1 SEGURIDAD: Usar función SQLAlchemy Core para máxima seguridad
            token_data = await get_refresh_token_by_hash_core(
                token_hash, resolved_cliente_id
            )
            
            if not token_data:
                logger.warning(
                    "[VALIDATE-TOKEN] Token no encontrado, revocado o expirado - "
                    "Cliente %s (contexto request puede diferir del JWT en platform)",
                    resolved_cliente_id,
                )
                return None

            is_logout_context = RefreshTokenService._call_stack_contains(
                "perform_logout"
            )

            if not is_logout_context:
                idle_timeout = await leer_session_idle_timeout_minutos(
                    resolved_cliente_id
                )
                token_id = token_data.get("token_id")
                idle_expired = (
                    bool(token_id)
                    and idle_timeout
                    and await is_refresh_token_session_idle_expired_core(
                        token_id,
                        resolved_cliente_id,
                        idle_timeout,
                    )
                )
                if idle_expired:
                    usuario_id = token_data.get("usuario_id")
                    if usuario_id:
                        await RefreshTokenService.revoke_token(
                            resolved_cliente_id,
                            usuario_id,
                            token,
                            revoked_reason=RevokedReason.IDLE_TIMEOUT,
                        )
                    logger.info(
                        "[IDLE-TIMEOUT] Sesión revocada por inactividad - "
                        "Cliente %s, Usuario %s, Token %s, límite %s min",
                        resolved_cliente_id,
                        token_data.get("usuario_id"),
                        token_data.get("token_id"),
                        idle_timeout,
                    )
                    return None
            
            logger.info(
                f"[VALIDATE-TOKEN] Token válido - Cliente {token_data['cliente_id']}, "
                f"Usuario {token_data['usuario_id']}, Tipo: {token_data.get('client_type', 'unknown')}, "
                f"Empresa: {token_data.get('empresa_id')}"
            )

            # Activity tracking: solo tras validación exitosa; excluir contexto logout.
            if not is_logout_context:
                token_id = token_data.get("token_id")
                if token_id:
                    await record_refresh_token_activity_core(
                        token_id, resolved_cliente_id
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
    def _call_stack_contains(*function_names: str) -> bool:
        import inspect

        return any(
            frame.function in function_names
            for frame in inspect.stack()[1:]
        )

    @staticmethod
    @BaseService.handle_service_errors
    async def revoke_token(
        cliente_id: UUID,
        usuario_id: UUID,
        token: str,
        *,
        revoked_reason: RevokedReason = RevokedReason.USER_LOGOUT,
    ) -> bool:
        """
        Revoca un refresh token específico por su hash.
        
        ✅ CORRECCIÓN CRÍTICA: Revoca un token específico por hash (no todos los del usuario).
        """
        try:
            token_hash = RefreshTokenService.hash_token(token)
            # ✅ FASE 1 SEGURIDAD: Usar función SQLAlchemy Core para máxima seguridad
            result = await revoke_refresh_token_core(
                token_hash, cliente_id, revoked_reason=str(revoked_reason)
            )
            
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
    async def revoke_all_user_tokens(
        cliente_id: UUID,
        usuario_id: UUID,
        *,
        revoked_reason: RevokedReason = RevokedReason.LOGOUT_ALL,
    ) -> int:
        """
        Revoca todos los tokens activos de un usuario (logout global).
        """
        try:
            # ✅ FASE 1 SEGURIDAD: Usar función SQLAlchemy Core para máxima seguridad
            rows_affected = await revoke_all_user_tokens_core(
                usuario_id, cliente_id, revoked_reason=str(revoked_reason)
            )
            
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
    async def revoke_refresh_token_by_id(
        token_id: UUID,
        *,
        revoked_reason: RevokedReason = RevokedReason.ADMIN_REVOKE,
    ) -> bool:
        """
        [ADMIN] Revoca un refresh token específico utilizando su ID (PK).
        
        ✅ FASE 2: Requiere contexto de tenant para asegurar que solo se revoquen
        tokens del tenant actual.
        """
        try:
            cliente_id = get_current_client_id()

            result = await revoke_refresh_token_by_id_core(
                token_id, cliente_id, revoked_reason=str(revoked_reason)
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