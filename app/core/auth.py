# app/core/auth.py
from datetime import datetime, timedelta
from typing import Optional, Dict
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


def create_access_token(data: dict) -> str:
    """
    Crea un token JWT de acceso con iat, exp y type='access'
    - Usa SECRET_KEY específica
    - Tiempo de expiración reducido (15 min por defecto)
    """
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "iat": now,
        "type": "access",
    })
    # Usa SECRET_KEY para access tokens
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """
    Crea un token JWT de refresh con iat, exp y type='refresh'
    - Usa REFRESH_SECRET_KEY separada (mayor seguridad)
    - Tiempo de expiración largo (7 días por defecto)
    """
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "iat": now,
        "type": "refresh",
    })
    # Usa REFRESH_SECRET_KEY separada
    return jwt.encode(to_encode, settings.REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_refresh_token(token: str) -> dict:
    """
    Decodifica y valida un refresh token (type='refresh')
    - Usa REFRESH_SECRET_KEY para validación
    - Verifica que el tipo sea 'refresh'
    """
    try:
        # Usa REFRESH_SECRET_KEY para decodificar
        payload = jwt.decode(token, settings.REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            raise JWTError("Token type is not refresh")
        return payload
    except JWTError as e:
        logger.error(f"Error decodificando refresh token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def authenticate_user(username: str, password: str) -> Dict:
    """
    Autentica un usuario y retorna sus datos (sin contraseña) si las credenciales son correctas
    """
    try:
        query = """
        SELECT usuario_id, nombre_usuario, correo, contrasena,
               nombre, apellido, es_activo
        FROM usuario
        WHERE nombre_usuario = ? AND es_eliminado = 0
        """
        user = execute_auth_query(query, (username,))

        if not user or not verify_password(password, user['contrasena']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas"
            )

        if not user['es_activo']:
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

        # Eliminar la contraseña del resultado
        user.pop('contrasena', None)
        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en autenticación: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en el proceso de autenticación"
        )


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    """
    Obtiene el usuario actual basado en el access token (Bearer).
    - Valida algoritmo, firma y expiración
    - Requiere type='access'
    - Usa claim estándar 'sub' como nombre de usuario
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

    except JWTError as e:
        logger.error(f"Error decodificando token: {str(e)}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Error procesando payload del token: {str(e)}")
        raise credentials_exception

    query = """
    SELECT usuario_id, nombre_usuario, correo, nombre, apellido, es_activo
    FROM usuario
    WHERE nombre_usuario = ? AND es_eliminado = 0
    """
    user = execute_auth_query(query, (username,))

    if not user:
        raise credentials_exception

    if not user['es_activo']:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo"
        )

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
        SELECT usuario_id, nombre_usuario, correo, nombre, apellido, es_activo
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

        logger.info(f"[REFRESH] Token validado exitosamente (BD OK) para usuario: {username} (Cliente: {client_type})")
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
