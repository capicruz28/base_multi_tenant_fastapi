# app/api/deps.py (SIMPLIFICADO - FASE 4)
"""
Dependencias de FastAPI simplificadas para autenticación y autorización.

✅ FASE 4: Simplificado para reducir acoplamiento.
- Solo funciones ligeras para decodificar tokens
- Lógica pesada movida a servicios dedicados
- get_user_auth_context() para contexto mínimo
- build_user_with_roles() para objetos completos cuando se necesiten
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import List, Dict, Any, AsyncGenerator

from app.core.config import settings
from app.core.auth import oauth2_scheme
from app.core.auth.user_context import get_user_auth_context, validate_tenant_access, CurrentUserContext
from app.core.auth.user_builder import build_user_with_roles
from app.modules.users.presentation.schemas import UsuarioReadWithRoles

import logging
logger = logging.getLogger(__name__)

# Excepciones
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="No se pudieron validar las credenciales",
    headers={"WWW-Authenticate": "Bearer"},
)
inactive_user_exception = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Usuario inactivo",
)
forbidden_exception = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Permisos insuficientes",
)


async def get_current_user_data(
    request: Request,
    token: str = Depends(oauth2_scheme),
) -> Dict[str, Any]:
    """
    Decodifica el token JWT y retorna el payload.
    
    ✅ REVOCACIÓN: Verifica que el token no esté en la blacklist de Redis.
    
    Función ligera que valida el token y verifica revocación, sin acceder a la BD.
    """
    from app.core.auth.impersonate_auth_diag import (
        is_impersonate_diag_request,
        log_impersonate_payload_summary,
    )
    from app.core.security.jwt import normalize_bearer_jwt_token

    if is_impersonate_diag_request():
        logger.info(
            "[IMPERSONATE-AUTH] get_current_user_data entry oauth2_scheme_ok "
            "token_len=%s",
            len(token) if token else 0,
        )

    try:
        token = normalize_bearer_jwt_token(token)
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Token JWT inválido: falta 'sub'.")
            raise credentials_exception
        
        # ✅ REVOCACIÓN: Verificar si el token está en la blacklist
        jti = payload.get("jti")
        if jti:
            try:
                from app.infrastructure.redis.client import RedisService
                is_blacklisted = await RedisService.is_token_blacklisted(jti)
                
                if is_blacklisted:
                    logger.warning(
                        f"[REVOCACIÓN] Token revocado detectado para usuario '{username}'. "
                        f"jti={jti}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token revocado",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
            except HTTPException:
                # Re-lanzar HTTPException (token revocado)
                raise
            except Exception as redis_error:
                # Fail-soft: Si Redis falla, loguear pero continuar (no bloquear acceso)
                logger.error(
                    f"[REVOCACIÓN] Error verificando blacklist en Redis (fail-soft): {redis_error}. "
                    f"Continuando sin verificación de revocación. jti={jti}",
                    exc_info=True
                )
                # NO bloquear acceso si Redis falla (fail-soft)
        else:
            logger.warning(
                f"[REVOCACIÓN] Token sin jti para usuario '{username}'. "
                "No se puede verificar revocación."
            )
        
        if is_impersonate_diag_request():
            log_impersonate_payload_summary(
                payload, phase="get_current_user_data_ok"
            )
        return payload
    except HTTPException as exc:
        if is_impersonate_diag_request():
            logger.warning(
                "[IMPERSONATE-AUTH] get_current_user_data HTTPException "
                "status=%s detail=%s",
                exc.status_code,
                exc.detail,
            )
        raise
    except JWTError as e:
        if is_impersonate_diag_request():
            logger.warning(
                "[IMPERSONATE-AUTH] get_current_user_data JWTError=%s token_len=%s "
                "→ credentials_exception",
                e,
                len(token) if token else 0,
            )
        logger.warning(
            "Error de validación JWT: %s (longitud token=%s)",
            e,
            len(token) if token else 0,
        )
        raise credentials_exception


async def get_current_active_user(
    request: Request,
    payload: Dict[str, Any] = Depends(get_current_user_data),
) -> AsyncGenerator[UsuarioReadWithRoles, None]:
    """
    Dependencia principal: Obtiene el usuario activo completo.

    I0: patrón yield para mantener empresa_context activo durante todo el
    request (handler + sub-dependencias), y limpiarlo solo al finalizar.
    """
    from app.core.tenant.empresa_context import (
        coerce_empresa_id,
        set_current_empresa_id,
        reset_current_empresa_id,
    )

    username = payload.get("sub")
    empresa_ctx_token = set_current_empresa_id(coerce_empresa_id(payload.get("empresa_id")))

    from app.core.auth.impersonate_auth_diag import (
        is_impersonate_diag_request,
        log_impersonate_payload_summary,
    )

    if is_impersonate_diag_request():
        log_impersonate_payload_summary(payload, phase="get_current_active_user_entry")
        logger.info(
            "[IMPERSONATE-AUTH] get_current_active_user username=%s",
            username,
        )

    from app.core.tenant.context import try_get_tenant_context

    try:
        # 1. Obtener cliente_id del contexto
        from app.core.tenant.context import get_current_client_id
        try:
            request_cliente_id = get_current_client_id()
        except RuntimeError:
            request_cliente_id = getattr(request.state, 'cliente_id', None)
            if request_cliente_id is None:
                logger.error(f"[SECURITY] No se pudo obtener cliente_id del contexto para usuario '{username}'")
                raise HTTPException(
                    status_code=500,
                    detail="Error interno: contexto de tenant no disponible"
                )
        
        # 2. Obtener contexto mínimo (validación rápida)
        context = await get_user_auth_context(username, request_cliente_id)
        
        if not context:
            if is_impersonate_diag_request():
                logger.warning(
                    "[IMPERSONATE-AUTH] get_current_active_user context=None "
                    "username=%s request_cliente_id=%s → credentials_exception",
                    username,
                    request_cliente_id,
                )
            logger.warning(f"Usuario '{username}' no encontrado o inactivo")
            raise credentials_exception
        
        if not context.es_activo:
            raise inactive_user_exception

        from app.core.auth.impersonation_rbac import is_impersonation_effective_tenant_session

        impersonation_tenant_session = is_impersonation_effective_tenant_session(payload)
        
        # 3. Validar acceso al tenant (impersonación usa JWT cliente_id del tenant impersonado)
        if not impersonation_tenant_session and not await validate_tenant_access(
            context, request_cliente_id
        ):
            logger.warning(
                f"[SECURITY] Acceso denegado: usuario '{username}' "
                f"(cliente {context.cliente_id}) intentó acceder a cliente {request_cliente_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado: token no válido para este tenant"
            )
        
        # 4. Registrar acceso cross-tenant si es SuperAdmin
        if context.is_superadmin and context.cliente_id != request_cliente_id:
            try:
                from app.modules.superadmin.application.services.audit_service import AuditService
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
                
                await AuditService.registrar_tenant_access(
                    usuario_id=context.usuario_id,
                    token_cliente_id=context.cliente_id,
                    request_cliente_id=request_cliente_id,
                    tipo_acceso="superadmin_cross_tenant",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata={
                        "username": username,
                        "access_level": context.nivel_acceso,
                    }
                )
            except Exception as audit_error:
                logger.warning(f"[AUDIT] Error registrando acceso cross-tenant: {audit_error}")
        
        # 5. Construir objeto completo (solo cuando se necesita)
        usuario_completo = await build_user_with_roles(username, request_cliente_id)
        
        if not usuario_completo:
            logger.error(
                "[ME-ENDPOINT] build_user_with_roles=None username=%s request_cliente_id=%s "
                "payload_user_type=%s es_superadmin=%s",
                username,
                request_cliente_id,
                payload.get("user_type"),
                payload.get("es_superadmin"),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno al procesar datos del usuario"
            )
        
        # ✅ CORRECCIÓN CRÍTICA: Usar nivel del token si está disponible (más confiable que recalcular)
        # El token ya tiene el nivel correcto calculado durante el login
        token_access_level = payload.get("access_level")
        if payload.get("is_impersonation"):
            token_is_super_admin = bool(payload.get("is_super_admin", False))
        else:
            token_is_super_admin = bool(
                payload.get("is_super_admin", False)
                or payload.get("es_superadmin", False)
            )
        token_user_type = payload.get("user_type", "user")
        
        if token_access_level is not None:
            # Si el token tiene nivel de acceso, usarlo (es más confiable)
            usuario_completo.access_level = token_access_level
            usuario_completo.is_super_admin = token_is_super_admin
            usuario_completo.user_type = token_user_type
            logger.debug(
                f"[DEPS] Usando nivel del token para usuario '{username}': "
                f"level={token_access_level}, super_admin={token_is_super_admin}, type={token_user_type}"
            )
        else:
            logger.debug(
                f"[DEPS] Token no tiene nivel de acceso, usando nivel calculado: "
                f"level={usuario_completo.access_level}"
            )

        from app.core.auth.impersonation_rbac import (
            apply_impersonation_effective_permissions_to_user,
            clear_impersonation_rbac_context,
            is_impersonation_effective_tenant_session,
        )

        if is_impersonation_effective_tenant_session(payload):
            tenant_context = try_get_tenant_context()
            database_type = (
                tenant_context.database_type if tenant_context else "single"
            )
            await apply_impersonation_effective_permissions_to_user(
                usuario_completo,
                cliente_id=usuario_completo.cliente_id,
                database_type=database_type,
                payload=payload,
                request_cliente_id=request_cliente_id,
            )

        from app.core.auth.password_change_enforcement import enforce_password_change_policy

        enforce_password_change_policy(
            request=request,
            payload=payload,
            usuario=usuario_completo,
            impersonation_tenant_session=impersonation_tenant_session,
        )

        if is_impersonate_diag_request():
            logger.info(
                "[IMPERSONATE-AUTH] get_current_active_user ok username=%s "
                "user_type=%s is_super_admin=%s access_level=%s",
                username,
                getattr(usuario_completo, "user_type", None),
                getattr(usuario_completo, "is_super_admin", None),
                getattr(usuario_completo, "access_level", None),
            )
        yield usuario_completo

    except HTTPException as exc:
        if is_impersonate_diag_request():
            logger.warning(
                "[IMPERSONATE-AUTH] get_current_active_user HTTPException "
                "status=%s detail=%s",
                exc.status_code,
                exc.detail,
            )
        raise
    except Exception as e:
        from app.core.exceptions import CustomException

        if is_impersonate_diag_request():
            logger.error(
                "[IMPERSONATE-AUTH] get_current_active_user exception=%s:%s",
                type(e).__name__,
                e,
                exc_info=True,
            )
        if isinstance(e, CustomException):
            raise
        logger.error(f"Error inesperado obteniendo usuario activo '{username}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al verificar el usuario",
        )
    finally:
        try:
            from app.core.auth.impersonation_rbac import clear_impersonation_rbac_context

            clear_impersonation_rbac_context()
        except Exception:
            pass
        reset_current_empresa_id(empresa_ctx_token)


# --- RoleChecker (SIMPLIFICADO) ---

class RoleChecker:
    """
    Clase para crear dependencias que verifican roles específicos.
    
    ✅ FASE 4: Simplificado para usar el contexto del usuario.
    """
    def __init__(self, required_roles: List[str]):
        self.required_roles = required_roles

    async def __call__(self,
        current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
    ):
        """
        Verifica si el nivel de acceso del usuario es suficiente.
        """
        from app.modules.rbac.application.services.rol_service import RolService
        
        try:
            from app.core.auth.impersonation_rbac import impersonation_passes_tenant_admin_gate

            if impersonation_passes_tenant_admin_gate(current_user):
                logger.debug(
                    "Acceso permitido (impersonation tenant_admin efectivo) para '%s'",
                    current_user.nombre_usuario,
                )
                return current_user

            # 1. Obtener nivel mínimo requerido
            min_required_level = await RolService.get_min_required_access_level(
                role_names=self.required_roles,
                cliente_id=current_user.cliente_id
            )
            
            # 2. Comparar con nivel del usuario (ya viene en current_user)
            if current_user.access_level < min_required_level:
                user_role_names = [role.nombre for role in current_user.roles]
                logger.warning(
                    f"Acceso denegado para usuario '{current_user.nombre_usuario}'. "
                    f"Roles: {user_role_names}. Nivel: {current_user.access_level}. "
                    f"Requerido: {min_required_level}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permisos insuficientes. Nivel de acceso del usuario ({current_user.access_level}) es menor al requerido ({min_required_level})."
                )
            
            logger.debug(
                f"Acceso permitido para usuario '{current_user.nombre_usuario}' "
                f"por LBAC (Nivel {current_user.access_level} >= {min_required_level})"
            )
            
            return current_user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error verificando roles: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno al verificar permisos"
            )
