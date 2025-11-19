# app/core/auth.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from fastapi import Depends, HTTPException, status, Cookie, Request, Body
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings
from app.core.security import verify_password
from app.db.queries import execute_auth_query
from app.schemas.auth import TokenPayload
# ✅ IMPORTACIÓN NECESARIA: Para acceder a la lógica de revocación de BD
from app.services.refresh_token_service import RefreshTokenService

logger = logging.getLogger(__name__)

# Swagger/OpenAPI: flujo password con tokenUrl en /api/v1
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login/")


# Schema para recibir refresh token en el body (móvil)
class RefreshTokenBody(BaseModel):
    refresh_token: Optional[str] = None


# --- NUEVA FUNCIÓN PARA OBTENER NIVELES DE USUARIO ---

def get_user_access_level_info(usuario_id: int, cliente_id: int) -> Dict[str, Any]:
    """
    Obtiene información de niveles de acceso del usuario (CORREGIDA)
    """
    try:
        from app.db.queries import execute_query, GET_USER_ACCESS_LEVEL_INFO_COMPLETE
        
        # Usar execute_query para mayor control
        result = execute_query(GET_USER_ACCESS_LEVEL_INFO_COMPLETE, (usuario_id, cliente_id))
        
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


def create_access_token(data: dict) -> str:
    """
    Crea un token JWT de acceso con iat, exp y type='access'
    - Usa SECRET_KEY específica
    - Tiempo de expiración reducido (15 min por defecto)
    - AHORA INCLUYE: access_level, is_super_admin, user_type
    """
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # ✅ AGREGAR CAMPOS DE NIVEL AL PAYLOAD
    level_info = to_encode.get('level_info', {})
    
    to_encode.update({
        "exp": expire,
        "iat": now,
        "type": "access",
        "access_level": level_info.get('access_level', 1),
        "is_super_admin": level_info.get('is_super_admin', False),
        "user_type": level_info.get('user_type', 'user')
    })
    
    # Remover level_info temporal del payload
    to_encode.pop('level_info', None)
    
    # Usa SECRET_KEY para access tokens
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """
    Crea un token JWT de refresh con iat, exp y type='refresh'
    - Usa REFRESH_SECRET_KEY separada (mayor seguridad)
    - Tiempo de expiración largo (7 días por defecto)
    - AHORA INCLUYE: access_level, is_super_admin, user_type
    """
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # ✅ AGREGAR CAMPOS DE NIVEL AL PAYLOAD
    level_info = to_encode.get('level_info', {})
    
    to_encode.update({
        "exp": expire,
        "iat": now,
        "type": "refresh",
        "access_level": level_info.get('access_level', 1),
        "is_super_admin": level_info.get('is_super_admin', False),
        "user_type": level_info.get('user_type', 'user')
    })
    
    # Remover level_info temporal del payload
    to_encode.pop('level_info', None)
    
    # Usa REFRESH_SECRET_KEY separada
    return jwt.encode(to_encode, settings.REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_refresh_token(token: str) -> dict:
    """
    Decodifica y valida un refresh token (type='refresh')
    - Usa REFRESH_SECRET_KEY para validación
    - Verifica que el tipo sea 'refresh'
    - AHORA VALIDA: access_level, is_super_admin, user_type
    """
    try:
        # Usa REFRESH_SECRET_KEY para decodificar
        payload = jwt.decode(token, settings.REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            raise JWTError("Token type is not refresh")
        
        # ✅ VALIDAR QUE TENGA CAMPOS DE NIVEL
        if 'access_level' not in payload or 'user_type' not in payload:
            logger.warning("Refresh token no contiene campos de nivel de acceso")
            raise JWTError("Token missing access level fields")
            
        return payload
    except JWTError as e:
        logger.error(f"Error decodificando refresh token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def authenticate_user(cliente_id: int, username: str, password: str) -> Dict:
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
        query = """
        SELECT usuario_id, cliente_id, nombre_usuario, correo, contrasena,
               nombre, apellido, es_activo
        FROM usuario
        WHERE cliente_id = ? AND nombre_usuario = ? AND es_eliminado = 0
        """
        
        # ✅ CORRECCIÓN CRÍTICA: Usar BD apropiada según tipo de usuario
        if is_superadmin:
            # Superadmin: SIEMPRE usar BD ADMIN
            from app.db.connection import DatabaseConnection
            from app.db.queries import execute_query
            
            logger.debug(f"[AUTH] Ejecutando en BD ADMIN: cliente_id={search_cliente_id}, username='{username}'")
            
            result = execute_query(
                query, 
                (search_cliente_id, username),
                connection_type=DatabaseConnection.ADMIN
            )
            user = result[0] if result else None
        else:
            # Usuario regular: Usar BD del contexto (tenant-aware)
            logger.debug(f"[AUTH] Ejecutando en BD tenant: cliente_id={search_cliente_id}, username='{username}'")
            user = execute_auth_query(query, (search_cliente_id, username))

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
        
        # ✅ LOGGING: Usuario encontrado
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
        update_query = """
        UPDATE usuario
        SET fecha_ultimo_acceso = GETDATE()
        WHERE usuario_id = ?
        """
        execute_auth_query(update_query, (user['usuario_id'],))

        # ✅ CALCULAR NIVELES DE ACCESO (NUEVO)
        level_info = get_user_access_level_info(user['usuario_id'], user['cliente_id'])
        
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


# --- NUEVOS MÉTODOS PARA SSO ---
async def authenticate_user_sso_azure_ad(cliente_id: int, token: str) -> Dict:
    """
    Autentica un usuario utilizando un token de Azure AD.
    """
    # Esta es una implementación placeholder. En la práctica, deberías:
    # 1. Validar el token JWT contra el tenant de Azure del cliente.
    # 2. Extraer el `oid` (Object ID) del usuario.
    # 3. Buscar en la tabla `usuario` con `proveedor_autenticacion = 'azure_ad'` y `referencia_externa_id = <oid>`.
    logger.info(f"Autenticando usuario SSO (Azure AD) para cliente {cliente_id}")
    raise NotImplementedError("Autenticación SSO con Azure AD no implementada.")


async def authenticate_user_sso_google(cliente_id: int, token: str) -> Dict:
    """
    Autentica un usuario utilizando un token de Google Workspace.
    """
    # Esta es una implementación placeholder. En la práctica, deberías:
    # 1. Validar el token JWT contra Google.
    # 2. Extraer el `sub` (Subject) del usuario.
    # 3. Buscar en la tabla `usuario` con `proveedor_autenticacion = 'google'` y `referencia_externa_id = <sub>`.
    logger.info(f"Autenticando usuario SSO (Google) para cliente {cliente_id}")
    raise NotImplementedError("Autenticación SSO con Google no implementada.")
# --- FIN NUEVOS MÉTODOS PARA SSO ---


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
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
        
        # ✅ EXTRAER CAMPOS DE NIVEL DEL TOKEN
        access_level = payload.get("access_level", 1)
        is_super_admin = payload.get("is_super_admin", False)
        user_type = payload.get("user_type", "user")

    except JWTError as e:
        logger.error(f"Error decodificando token: {str(e)}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Error procesando payload del token: {str(e)}")
        raise credentials_exception

    # ✅ CORRECCIÓN: Buscar usuario en BD apropiada
    query = """
    SELECT usuario_id, cliente_id, nombre_usuario, correo, nombre, apellido, es_activo
    FROM usuario
    WHERE nombre_usuario = ? AND es_eliminado = 0
    """
    
    if es_superadmin:
        # Superadmin: Buscar en BD ADMIN
        from app.db.connection import DatabaseConnection
        from app.db.queries import execute_query
        
        result = execute_query(query, (username,), connection_type=DatabaseConnection.ADMIN)
        user = result[0] if result else None
        
        # Agregar contexto multi-tenant
        if user:
            user['target_cliente_id'] = target_cliente_id
            user['es_superadmin'] = True
    else:
        # Usuario regular: Buscar en BD del contexto
        user = execute_auth_query(query, (username,))

    if not user:
        raise credentials_exception

    if not user['es_activo']:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo"
        )
    
    # ✅ AGREGAR CAMPOS DE NIVEL AL USUARIO
    user['access_level'] = access_level
    user['is_super_admin'] = is_super_admin
    user['user_type'] = user_type

    return user


async def get_current_user_from_refresh(
    request: Request,
    refresh_token_cookie: Optional[str] = Cookie(None, alias=settings.REFRESH_COOKIE_NAME),
    body: RefreshTokenBody = Body(default=RefreshTokenBody())
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
        refresh_token = body.refresh_token
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
            logger.warning(f"[REFRESH] Token JWT válido, pero inactivo/revocado en BD. Usuario: {payload.get('sub')}")
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

        query = """
        SELECT usuario_id, cliente_id, nombre_usuario, correo, nombre, apellido, es_activo
        FROM usuario
        WHERE nombre_usuario = ? AND es_eliminado = 0
        """
        user = execute_auth_query(query, (username,))

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

# ✅ NUEVAS FUNCIONES PARA GESTIÓN DE SESIONES (REVOCACIÓN Y LISTADO)

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