# app/modules/auth/application/services/auth_service.py
"""
AuthService: Servicio de autenticación.

✅ ARQUITECTURA: Movido desde app/core/auth.py para corregir violación de capas.
La lógica de autenticación pertenece al módulo Auth, no a Core.

Este servicio maneja:
- Autenticación de usuarios (credenciales)
- Autenticación SSO (Azure AD, Google)
- Validación de tokens (access y refresh)
- Gestión de sesiones
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
import logging

from fastapi import Depends, HTTPException, status, Cookie, Request, Body
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings
from app.core.security.password import verify_password
from app.core.security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token
)
# ✅ FASE 2: Migrar a queries_async
from app.infrastructure.database.queries_async import execute_auth_query, execute_query, execute_update
from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.tables import UsuarioTable
from sqlalchemy import update, func, text
from app.modules.auth.presentation.schemas import TokenPayload
from app.modules.auth.application.services.refresh_token_service import RefreshTokenService
from app.modules.superadmin.application.services.audit_service import AuditService
from app.core.tenant.context import get_current_client_id

logger = logging.getLogger(__name__)


# Schema para recibir refresh token en el body (móvil)
class RefreshTokenBody(BaseModel):
    refresh_token: Optional[str] = None


class AuthService:
    """
    Servicio de autenticación.
    
    Maneja toda la lógica de autenticación de usuarios, incluyendo:
    - Autenticación con credenciales
    - Autenticación SSO
    - Validación de tokens
    - Gestión de sesiones
    """
    
    @staticmethod
    async def get_user_access_level_info(usuario_id: UUID, cliente_id: UUID) -> Dict[str, Any]:
        """
        Obtiene información de niveles de acceso del usuario.
        
        ✅ FASE 2: Refactorizado para usar async.
        """
        try:
            from app.infrastructure.database.queries import GET_USER_ACCESS_LEVEL_INFO_COMPLETE
            from sqlalchemy import text
            from app.core.tenant.context import try_get_tenant_context
            
            # ✅ Obtener database_type del contexto para determinar si es BD dedicada
            tenant_context = try_get_tenant_context()
            database_type = tenant_context.database_type if tenant_context else "single"
            
            # ✅ Para BD dedicadas, no filtrar por cliente_id (todos los roles pertenecen al mismo tenant)
            if database_type == "multi":
                query = """
                SELECT 
                    ISNULL(MAX(r.nivel_acceso), 1) as max_level,
                    COUNT(CASE WHEN r.codigo_rol = 'SUPER_ADMIN' AND r.nivel_acceso = 5 THEN 1 END) as super_admin_count,
                    COUNT(*) as total_roles
                FROM usuario_rol ur
                INNER JOIN rol r ON ur.rol_id = r.rol_id
                WHERE ur.usuario_id = :usuario_id 
                  AND ur.es_activo = 1
                  AND r.es_activo = 1
                """
                # ✅ FASE 2: Usar execute_query async con text().bindparams() - solo usuario_id para BD dedicadas
                result = await execute_query(
                    text(query).bindparams(usuario_id=usuario_id),
                    connection_type=DatabaseConnection.DEFAULT,
                    client_id=cliente_id
                )
            else:
                # BD compartida: filtrar por cliente_id
                query = GET_USER_ACCESS_LEVEL_INFO_COMPLETE.replace("?", ":usuario_id", 1) \
                                                           .replace("?", ":cliente_id", 1)
                
                # ✅ FASE 2: Usar execute_query async con text().bindparams()
                result = await execute_query(
                    text(query).bindparams(usuario_id=usuario_id, cliente_id=cliente_id),
                    connection_type=DatabaseConnection.DEFAULT,
                    client_id=cliente_id
                )
            
            if result and len(result) > 0:
                level_data = result[0]
                access_level = level_data.get('max_level', 1)
                is_super_admin = level_data.get('super_admin_count', 0) > 0
                
                # Determinar tipo de usuario
                if is_super_admin:
                    user_type = 'super_admin'
                elif access_level >= 4:
                    user_type = 'tenant_admin'
                else:
                    user_type = 'user'
                    
                logger.info(f"Niveles calculados - Usuario {usuario_id}: level={access_level}, super_admin={is_super_admin}, type={user_type}")
                
                return {
                    'access_level': access_level,
                    'is_super_admin': is_super_admin,
                    'user_type': user_type
                }
            else:
                logger.warning(f"No se pudieron calcular niveles para usuario {usuario_id}, usando valores por defecto")
                return {
                    'access_level': 1,
                    'is_super_admin': False,
                    'user_type': 'user'
                }
                
        except Exception as e:
            logger.error(f"Error al obtener niveles de acceso para usuario {usuario_id}: {e}")
            # Valores por defecto en caso de error
            return {
                'access_level': 1,
                'is_super_admin': False,
                'user_type': 'user'
            }
    
    @staticmethod
    async def authenticate_user(cliente_id: UUID, username: str, password: str) -> Dict:
        """
        Autentica un usuario **dentro de un cliente específico**.
        
        ✅ CORRECCIÓN MULTI-TENANT HÍBRIDO: 
        - Si es el Super Admin: Busca en BD ADMIN (donde está el cliente SYSTEM)
        - Si es un usuario regular: Busca en la BD del cliente (compartida o separada)
        
        AHORA INCLUYE: access_level, is_super_admin, user_type en la respuesta
        """
        
        # ✅ LOGGING CRÍTICO: Verificar qué cliente_id llegó
        logger.info(f"[AUTH] Intento de login: username='{username}', cliente_id_destino={cliente_id}")
        
        # 1. Detectar si es superadmin
        is_superadmin = (username == settings.SUPERADMIN_USERNAME)
        
        # 2. Determinar dónde buscar y en qué BD
        if is_superadmin:
            # SUPERADMIN: Buscar en cliente SYSTEM, usando BD ADMIN
            search_cliente_id = settings.SUPERADMIN_CLIENTE_ID
            target_cliente_id = cliente_id  # Cliente al que quiere acceder
            
            logger.info(
                f"[AUTH] SUPERADMIN detectado. "
                f"Buscando en BD ADMIN (cliente_id={search_cliente_id}), "
                f"accediendo a cliente_id={target_cliente_id}"
            )
        else:
            # USUARIO REGULAR: Buscar en su cliente, usando BD del contexto
            search_cliente_id = cliente_id
            target_cliente_id = cliente_id
            
            logger.info(
                f"[AUTH] Usuario regular. "
                f"Buscando en BD del cliente_id={search_cliente_id}"
            )

        try:
            # ✅ Obtener database_type del contexto para determinar si es BD dedicada
            from app.core.tenant.context import get_tenant_context, try_get_tenant_context
            from sqlalchemy import text
            
            tenant_context = None
            database_type = "single"
            try:
                tenant_context = get_tenant_context()
                database_type = tenant_context.database_type if tenant_context else "single"
            except RuntimeError:
                # Sin contexto, intentar obtener sin lanzar excepción
                tenant_context = try_get_tenant_context()
                database_type = tenant_context.database_type if tenant_context else "single"
            
            # ✅ CORRECCIÓN: Para BD dedicadas (multi), no filtrar por cliente_id
            # porque todos los usuarios en esa BD pertenecen al mismo cliente
            if database_type == "multi":
                query = """
                SELECT usuario_id, cliente_id, nombre_usuario, correo, contrasena,
                       nombre, apellido, es_activo
                FROM usuario
                WHERE nombre_usuario = :nombre_usuario AND es_eliminado = 0
                """
                logger.debug(
                    f"[AUTH] BD dedicada detectada. Buscando usuario sin filtrar por cliente_id: "
                    f"username='{username}'"
                )
            else:
                query = """
                SELECT usuario_id, cliente_id, nombre_usuario, correo, contrasena,
                       nombre, apellido, es_activo
                FROM usuario
                WHERE cliente_id = :cliente_id AND nombre_usuario = :nombre_usuario AND es_eliminado = 0
                """
                logger.debug(
                    f"[AUTH] BD compartida. Buscando usuario con cliente_id: "
                    f"cliente_id={search_cliente_id}, username='{username}'"
                )
            
            # ✅ CORRECCIÓN CRÍTICA: Usar BD apropiada según tipo de usuario
            # ✅ FASE 2: Usar execute_query async con text().bindparams()
            
            if is_superadmin:
                # Superadmin: SIEMPRE usar BD ADMIN
                logger.debug(f"[AUTH] Ejecutando en BD ADMIN: cliente_id={search_cliente_id}, username='{username}'")
                
                result = await execute_query(
                    text(query).bindparams(cliente_id=search_cliente_id, nombre_usuario=username),
                    connection_type=DatabaseConnection.ADMIN,
                    client_id=None
                )
                user = result[0] if result else None
            else:
                # Usuario regular: Usar BD del contexto (tenant-aware)
                logger.debug(f"[AUTH] Ejecutando en BD tenant: cliente_id={search_cliente_id}, username='{username}'")
                
                if database_type == "multi":
                    # BD dedicada: no pasar cliente_id en bindparams
                    result = await execute_query(
                        text(query).bindparams(nombre_usuario=username),
                        connection_type=DatabaseConnection.DEFAULT,
                        client_id=search_cliente_id
                    )
                else:
                    # BD compartida: pasar cliente_id en bindparams
                    result = await execute_query(
                        text(query).bindparams(cliente_id=search_cliente_id, nombre_usuario=username),
                        connection_type=DatabaseConnection.DEFAULT,
                        client_id=search_cliente_id
                    )
                user = result[0] if result else None

            if not user:
                logger.warning(
                    f"[AUTH] Usuario NO ENCONTRADO: "
                    f"username='{username}', "
                    f"cliente_id_buscado={search_cliente_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciales incorrectas"
                )
            
            # ✅ CORRECCIÓN CRÍTICA: Para BD dedicadas, el cliente_id del usuario puede ser NULL o UUID nulo
            # Usar el cliente_id del contexto del tenant en su lugar
            # IMPORTANTE: Hacer esto ANTES del log para que el log muestre el valor correcto
            if database_type == "multi":
                # Convertir cliente_id a UUID si es string para comparar
                user_cliente_id = user.get('cliente_id')
                if user_cliente_id:
                    if isinstance(user_cliente_id, str):
                        try:
                            user_cliente_id = UUID(user_cliente_id)
                        except (ValueError, AttributeError):
                            user_cliente_id = None
                    elif not isinstance(user_cliente_id, UUID):
                        user_cliente_id = None
                
                # Verificar si es None o UUID nulo
                if not user_cliente_id or (isinstance(user_cliente_id, UUID) and user_cliente_id == UUID('00000000-0000-0000-0000-000000000000')):
                    user['cliente_id'] = search_cliente_id
                    logger.debug(
                        f"[AUTH] BD dedicada: cliente_id del usuario era NULL/nulo, "
                        f"usando cliente_id del contexto: {search_cliente_id}"
                    )
                else:
                    user['cliente_id'] = user_cliente_id
            
            # ✅ LOGGING: Usuario encontrado (después de la corrección)
            logger.debug(f"[AUTH] Usuario encontrado: usuario_id={user['usuario_id']}, cliente_id={user['cliente_id']}")
            
            if not verify_password(password, user['contrasena']):
                logger.warning(
                    f"[AUTH] Contraseña incorrecta para: "
                    f"username='{username}', "
                    f"usuario_id={user['usuario_id']}"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciales incorrectas"
                )

            if not user['es_activo']:
                logger.warning(f"[AUTH] Usuario inactivo: usuario_id={user['usuario_id']}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario inactivo"
                )

            # Actualizar fecha último acceso
            # ✅ FASE 2: Usar execute_query async para UPDATE
            from app.infrastructure.database.tables import UsuarioTable
            from sqlalchemy import update, func, text
            
            update_query = update(UsuarioTable).where(
                UsuarioTable.c.usuario_id == user['usuario_id']
            ).values(fecha_ultimo_acceso=func.getdate())
            
            await execute_update(update_query)

            # ✅ CALCULAR NIVELES DE ACCESO (NUEVO)
            # ✅ FASE 2: Usar await
            level_info = await AuthService.get_user_access_level_info(user['usuario_id'], user['cliente_id'])
            
            # Agregar niveles al usuario
            user['access_level'] = level_info['access_level']
            user['is_super_admin'] = level_info['is_super_admin']
            user['user_type'] = level_info['user_type']
            
            # Eliminar la contraseña del resultado
            user.pop('contrasena', None)
            
            # ✅ AGREGAR contexto multi-tenant al resultado
            if is_superadmin:
                user['target_cliente_id'] = target_cliente_id
                user['es_superadmin'] = True
            else:
                # Para usuarios regulares, asegurar que target_cliente_id sea el cliente_id correcto
                # En BD dedicadas, usar search_cliente_id (del contexto) en lugar del cliente_id del usuario
                if database_type == "multi":
                    user['target_cliente_id'] = search_cliente_id
                else:
                    user['target_cliente_id'] = user['cliente_id']
            
            logger.info(
                f"[AUTH] Login exitoso: "
                f"username='{username}', "
                f"usuario_id={user['usuario_id']}, "
                f"cliente_origen={user['cliente_id']}, "
                f"cliente_destino={target_cliente_id if is_superadmin else 'N/A'}, "
                f"access_level={user['access_level']}, "
                f"user_type={user['user_type']}"
            )
            
            return user

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"[AUTH] Error en autenticación: "
                f"username='{username}', "
                f"cliente_id={cliente_id}, "
                f"error={str(e)}", 
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error en el proceso de autenticación"
            )
    
    @staticmethod
    async def authenticate_user_sso_azure_ad(cliente_id: UUID, token: str) -> Dict:
        """
        Autentica un usuario utilizando un token de Azure AD.
        """
        # Esta es una implementación placeholder. En la práctica, deberías:
        # 1. Validar el token JWT contra el tenant de Azure del cliente.
        # 2. Extraer el `oid` (Object ID) del usuario.
        # 3. Buscar en la tabla `usuario` con `proveedor_autenticacion = 'azure_ad'` y `referencia_externa_id = <oid>`.
        logger.info(f"Autenticando usuario SSO (Azure AD) para cliente {cliente_id}")
        raise NotImplementedError("Autenticación SSO con Azure AD no implementada.")
    
    @staticmethod
    async def authenticate_user_sso_google(cliente_id: UUID, token: str) -> Dict:
        """
        Autentica un usuario utilizando un token de Google Workspace.
        """
        # Esta es una implementación placeholder. En la práctica, deberías:
        # 1. Validar el token JWT contra Google.
        # 2. Extraer el `sub` (Subject) del usuario.
        # 3. Buscar en la tabla `usuario` con `proveedor_autenticacion = 'google'` y `referencia_externa_id = <sub>`.
        logger.info(f"Autenticando usuario SSO (Google) para cliente {cliente_id}")
        raise NotImplementedError("Autenticación SSO con Google no implementada.")
    
    @staticmethod
    async def get_current_user(token: str) -> Dict:
        """
        Obtiene el usuario actual basado en el access token (Bearer).
        
        ✅ CORRECCIÓN MULTI-TENANT HÍBRIDO:
        - Superadmin: Busca en BD ADMIN
        - Usuario regular: Busca en BD del contexto
        
        AHORA INCLUYE: access_level, is_super_admin, user_type del token
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudieron validar las credenciales",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            # Usa SECRET_KEY para validar access tokens
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            token_data = TokenPayload(**payload)

            if not token_data.sub or token_data.type != "access":
                raise credentials_exception

            username = token_data.sub
            es_superadmin = payload.get("es_superadmin", False)
            target_cliente_id = payload.get("cliente_id")  # Cliente al que accede
            token_cliente_id = payload.get("cliente_id")  # Cliente del token
            
            # ✅ EXTRAER CAMPOS DE NIVEL DEL TOKEN
            access_level = payload.get("access_level", 1)
            is_super_admin = payload.get("is_super_admin", False)
            user_type = payload.get("user_type", "user")
            
            # ============================================
            # ✅ FASE 1: VALIDACIÓN DE TENANT EN TOKEN (CON FEATURE FLAG)
            # ============================================
            # IMPORTANTE: Solo se valida si el flag está activo
            # Por defecto está desactivado (comportamiento actual)
            if settings.ENABLE_TENANT_TOKEN_VALIDATION:
                try:
                    current_cliente_id = get_current_client_id()
                    
                    # ✅ Convertir token_cliente_id a UUID si es string
                    token_cliente_id_uuid = None
                    if token_cliente_id is not None:
                        if isinstance(token_cliente_id, str):
                            try:
                                token_cliente_id_uuid = UUID(token_cliente_id)
                            except (ValueError, AttributeError):
                                logger.warning(
                                    f"[SECURITY] token_cliente_id inválido en token: {token_cliente_id}"
                                )
                                token_cliente_id_uuid = None
                        elif isinstance(token_cliente_id, UUID):
                            token_cliente_id_uuid = token_cliente_id
                    
                    # Superadmin puede cambiar de tenant (comportamiento actual)
                    # Solo validamos para usuarios regulares
                    if not es_superadmin and token_cliente_id_uuid is not None:
                        if token_cliente_id_uuid != current_cliente_id:
                            logger.warning(
                                f"[SECURITY] Token de tenant {token_cliente_id_uuid} usado en tenant {current_cliente_id}. "
                                f"Usuario: {username}"
                            )
                            raise HTTPException(
                                status_code=status.HTTP_403_FORBIDDEN,
                                detail="Token no válido para este tenant. Por favor, inicie sesión nuevamente."
                            )
                        logger.debug(
                            f"[SECURITY] Validación de tenant exitosa: token_cliente_id={token_cliente_id_uuid}, "
                            f"current_cliente_id={current_cliente_id}"
                        )
                except RuntimeError:
                    # Si no hay contexto (script de fondo, inicialización), permitir
                    # Esto mantiene compatibilidad con código que no tiene contexto
                    logger.debug(
                        "[AUTH] Sin contexto de tenant disponible, validación omitida "
                        "(comportamiento esperado para scripts de fondo)"
                    )
                except HTTPException:
                    # Re-lanzar excepciones HTTP (como la de validación de tenant)
                    raise
                except Exception as e:
                    # Si hay cualquier otro error en la validación, loggear pero NO bloquear
                    # Esto previene que errores en la validación rompan el sistema
                    logger.error(
                        f"[SECURITY] Error en validación de tenant (no bloqueante): {str(e)}",
                        exc_info=True
                    )

        except JWTError as e:
            logger.error(f"Error decodificando token: {str(e)}")
            raise credentials_exception
        except Exception as e:
            logger.error(f"Error procesando payload del token: {str(e)}")
            raise credentials_exception

        # ✅ CORRECCIÓN: Buscar usuario en BD apropiada
        # ✅ Obtener database_type del contexto para determinar si es BD dedicada
        from app.core.tenant.context import try_get_tenant_context
        
        tenant_context = try_get_tenant_context()
        database_type = tenant_context.database_type if tenant_context else "single"
        
        # Query base (sin filtro de cliente_id para BD dedicadas)
        query = """
        SELECT usuario_id, cliente_id, nombre_usuario, correo, nombre, apellido, es_activo
        FROM usuario
        WHERE nombre_usuario = ? AND es_eliminado = 0
        """
        
        # ✅ FASE 2: Usar await
        if es_superadmin:
            # Superadmin: Buscar en BD ADMIN
            result = await execute_query(
                text(query.replace("?", ":username")).bindparams(username=username),
                connection_type=DatabaseConnection.ADMIN,
                client_id=None
            )
            user = result[0] if result else None
            
            # Agregar contexto multi-tenant
            if user:
                user['target_cliente_id'] = target_cliente_id
                user['es_superadmin'] = True
        else:
            # Usuario regular: Buscar en BD del contexto
            # ✅ Para BD dedicadas, execute_auth_query ya busca sin cliente_id
            user = await execute_auth_query(query, (username,))

        if not user:
            raise credentials_exception

        if not user['es_activo']:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario inactivo"
            )
        
        # ✅ CORRECCIÓN CRÍTICA: Para BD dedicadas, el cliente_id del usuario puede ser NULL o UUID nulo
        # Usar el cliente_id del token o del contexto en su lugar
        if database_type == "multi":
            # Convertir cliente_id del usuario a UUID si es string para comparar
            user_cliente_id = user.get('cliente_id')
            if user_cliente_id:
                if isinstance(user_cliente_id, str):
                    try:
                        user_cliente_id = UUID(user_cliente_id)
                    except (ValueError, AttributeError):
                        user_cliente_id = None
                elif not isinstance(user_cliente_id, UUID):
                    user_cliente_id = None
            
            # Verificar si es None o UUID nulo
            if not user_cliente_id or (isinstance(user_cliente_id, UUID) and user_cliente_id == UUID('00000000-0000-0000-0000-000000000000')):
                if token_cliente_id:
                    # Convertir token_cliente_id a UUID si es string
                    if isinstance(token_cliente_id, str):
                        try:
                            user['cliente_id'] = UUID(token_cliente_id)
                        except (ValueError, AttributeError):
                            # Si falla, usar el contexto actual
                            from app.core.tenant.context import try_get_current_client_id
                            user['cliente_id'] = try_get_current_client_id()
                    else:
                        user['cliente_id'] = token_cliente_id
                    logger.debug(
                        f"[AUTH] BD dedicada: cliente_id del usuario era NULL/nulo, "
                        f"usando cliente_id del token: {user['cliente_id']}"
                    )
                else:
                    # Si no hay cliente_id en el token, usar el contexto actual
                    from app.core.tenant.context import try_get_current_client_id
                    user['cliente_id'] = try_get_current_client_id()
                    logger.debug(
                        f"[AUTH] BD dedicada: cliente_id del usuario y token eran NULL/nulo, "
                        f"usando cliente_id del contexto: {user['cliente_id']}"
                    )
            else:
                user['cliente_id'] = user_cliente_id
        
        # ✅ AGREGAR CAMPOS DE NIVEL AL USUARIO
        user['access_level'] = access_level
        user['is_super_admin'] = is_super_admin
        user['user_type'] = user_type

        return user
    
    @staticmethod
    async def get_current_user_from_refresh(
        request: Request,
        refresh_token_cookie: Optional[str] = None,
        refresh_token_body: Optional[str] = None
    ) -> Dict:
        """
        Obtiene el usuario actual validando el refresh token.
        
        ✅ CORRECCIÓN: **Verifica el estado de revocación del token en la BD** antes de retornar, previniendo el reuso de tokens cerrados o expirados.
        
        - WEB: Lee desde cookie HttpOnly
        - MÓVIL: Lee desde body JSON (con el header X-Client-Type: mobile)
        - Usa REFRESH_SECRET_KEY para validación JWT
        - AHORA INCLUYE: access_level, is_super_admin, user_type del token
        """
        # Detectar tipo de cliente
        client_type = request.headers.get("X-Client-Type", "web").lower()
        
        # Obtener el refresh token según el tipo de cliente
        refresh_token = None
        if client_type == "web":
            refresh_token = refresh_token_cookie
            logger.debug("[REFRESH] Leyendo token desde cookie (WEB)")
        else:  # mobile
            refresh_token = refresh_token_body
            logger.debug("[REFRESH] Leyendo token desde body (MOBILE)")
        
        if not refresh_token:
            logger.warning(f"[REFRESH] No se proporcionó refresh token. Cliente: {client_type}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No refresh token provided"
            )

        try:
            # 1. Validación JWT (firma y expiración de 7 días)
            payload = decode_refresh_token(refresh_token)
            
            # 2. ✅ CRÍTICO: VALIDACIÓN DE ESTADO EN BASE DE DATOS
            # Verifica si el token existe, no está revocado y no ha expirado
            db_token_data = await RefreshTokenService.validate_refresh_token(refresh_token)

            if not db_token_data:
                # Si el servicio retorna None, significa que está revocado, expirado, o no existe
                username = payload.get("sub")
                logger.warning(
                    f"[REFRESH] Token JWT válido, pero inactivo/revocado en BD. Usuario: {username}"
                )
                # Registrar evento de token inválido/expirado en auditoría
                try:
                    # ✅ registrar_auth_event ahora maneja la conversión automáticamente
                    await AuditService.registrar_auth_event(
                        cliente_id=payload.get("cliente_id"),
                        usuario_id=None,
                        evento="token_invalid_or_revoked",
                        nombre_usuario_intento=username,
                        descripcion="Refresh token inválido, expirado o revocado en base de datos",
                        exito=False,
                        codigo_error="REFRESH_TOKEN_INVALID_DB",
                        ip_address=request.client.host if request.client else None,
                        user_agent=request.headers.get("user-agent"),
                        metadata={"client_type": client_type},
                    )
                except Exception:
                    logger.exception(
                        "[AUDIT] Error registrando evento token_invalid_or_revoked (no crítico)"
                    )

                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Sesión expirada o cerrada remotamente. Por favor, vuelva a iniciar sesión."
                )
            
            # 3. Obtener datos del usuario
            token_data = TokenPayload(**payload)
            
            if not token_data.sub:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token payload"
                )

            username = token_data.sub

            # ✅ Obtener database_type del contexto para determinar si es BD dedicada
            from app.core.tenant.context import try_get_tenant_context
            
            tenant_context = try_get_tenant_context()
            database_type = tenant_context.database_type if tenant_context else "single"
            
            # Query base (sin filtro de cliente_id para BD dedicadas)
            query = """
            SELECT usuario_id, cliente_id, nombre_usuario, correo, nombre, apellido, es_activo
            FROM usuario
            WHERE nombre_usuario = ? AND es_eliminado = 0
            """
            # ✅ FASE 2: Usar await
            # ✅ Para BD dedicadas, execute_auth_query ya busca sin cliente_id
            user = await execute_auth_query(query, (username,))

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario no encontrado"
                )

            if not user['es_activo']:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario inactivo"
                )
            
            # ✅ CORRECCIÓN CRÍTICA: Para BD dedicadas, el cliente_id del usuario puede ser NULL o UUID nulo
            # Usar el cliente_id del token o del contexto en su lugar
            token_cliente_id = payload.get("cliente_id")
            if database_type == "multi":
                # Convertir cliente_id del usuario a UUID si es string para comparar
                user_cliente_id = user.get('cliente_id')
                if user_cliente_id:
                    if isinstance(user_cliente_id, str):
                        try:
                            user_cliente_id = UUID(user_cliente_id)
                        except (ValueError, AttributeError):
                            user_cliente_id = None
                    elif not isinstance(user_cliente_id, UUID):
                        user_cliente_id = None
                
                # Verificar si es None o UUID nulo
                if not user_cliente_id or (isinstance(user_cliente_id, UUID) and user_cliente_id == UUID('00000000-0000-0000-0000-000000000000')):
                    if token_cliente_id:
                        # Convertir token_cliente_id a UUID si es string
                        if isinstance(token_cliente_id, str):
                            try:
                                user['cliente_id'] = UUID(token_cliente_id)
                            except (ValueError, AttributeError):
                                # Si falla, usar el contexto actual
                                from app.core.tenant.context import try_get_current_client_id
                                user['cliente_id'] = try_get_current_client_id()
                        else:
                            user['cliente_id'] = token_cliente_id
                        logger.debug(
                            f"[REFRESH] BD dedicada: cliente_id del usuario era NULL/nulo, "
                            f"usando cliente_id del token: {user['cliente_id']}"
                        )
                    else:
                        # Si no hay cliente_id en el token, usar el contexto actual
                        from app.core.tenant.context import try_get_current_client_id
                        user['cliente_id'] = try_get_current_client_id()
                        logger.debug(
                            f"[REFRESH] BD dedicada: cliente_id del usuario y token eran NULL/nulo, "
                            f"usando cliente_id del contexto: {user['cliente_id']}"
                        )
                else:
                    user['cliente_id'] = user_cliente_id
                
            # ✅ AGREGAR CAMPOS DE NIVEL AL USUARIO DESDE EL TOKEN
            user['access_level'] = payload.get('access_level', 1)
            user['is_super_admin'] = payload.get('is_super_admin', False)
            user['user_type'] = payload.get('user_type', 'user')

            logger.info(f"[REFRESH] Token validado exitosamente (BD OK) para usuario: {username} "
                       f"(Cliente: {user['cliente_id']}, Level: {user['access_level']}, Type: {user['user_type']})")
            return user

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error validando refresh token: {str(e)}", exc_info=True)
            # Aseguramos que cualquier error de validación retorne 401
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
    
    @staticmethod
    async def revoke_session_by_token_id(token_id: str) -> None:
        """
        Revoca un refresh token específico en la base de datos por su ID (jti).
        Esta función es utilizada por los endpoints de cierre de sesión/revocación.
        """
        try:
            await RefreshTokenService.revoke_refresh_token_by_id(token_id)
            logger.info(f"Sesión con ID '{token_id}' revocada exitosamente.")
        except Exception as e:
            logger.error(f"Error al revocar sesión con ID '{token_id}': {str(e)}", exc_info=True)
            # La lógica de la ruta debe manejar el error, aquí solo loggeamos.
            # No levantamos HTTPException aquí.
    
    @staticmethod
    async def get_all_active_sessions(user_id: int) -> list[Dict]:
        """
        Obtiene todas las sesiones (refresh tokens) activas para un usuario.
        Retorna los datos de la BD listos para ser usados en la capa de API.
        """
        try:
            return await RefreshTokenService.get_all_active_sessions(user_id)
        except Exception as e:
            logger.error(f"Error al obtener sesiones activas para usuario {user_id}: {str(e)}", exc_info=True)
            # En caso de error, retornamos lista vacía.
            return []


# ✅ FUNCIONES DE COMPATIBILIDAD: Mantener funciones globales para no romper imports existentes
# Estas funciones son wrappers que llaman a AuthService

async def authenticate_user(cliente_id: int, username: str, password: str) -> Dict:
    """Wrapper para mantener compatibilidad."""
    return await AuthService.authenticate_user(cliente_id, username, password)

async def authenticate_user_sso_azure_ad(cliente_id: int, token: str) -> Dict:
    """Wrapper para mantener compatibilidad."""
    return await AuthService.authenticate_user_sso_azure_ad(cliente_id, token)

async def authenticate_user_sso_google(cliente_id: int, token: str) -> Dict:
    """Wrapper para mantener compatibilidad."""
    return await AuthService.authenticate_user_sso_google(cliente_id, token)

async def get_user_access_level_info(usuario_id: int, cliente_id: int) -> Dict[str, Any]:
    """Wrapper para mantener compatibilidad."""
    # ✅ FASE 2: Usar await
    return await AuthService.get_user_access_level_info(usuario_id, cliente_id)

async def revoke_session_by_token_id(token_id: str) -> None:
    """Wrapper para mantener compatibilidad."""
    return await AuthService.revoke_session_by_token_id(token_id)

async def get_all_active_sessions(user_id: int) -> list[Dict]:
    """Wrapper para mantener compatibilidad."""
    return await AuthService.get_all_active_sessions(user_id)

