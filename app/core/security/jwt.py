# app/core/security/jwt.py
"""
Utilidades para creación y decodificación de tokens JWT.

✅ ARQUITECTURA: Contiene utilidades de seguridad relacionadas con JWT.
✅ REVOCACIÓN: Incluye jti (JWT ID) para revocación de tokens con Redis.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, List
import logging
from uuid import uuid4, UUID
from jose import JWTError, jwt
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings

logger = logging.getLogger(__name__)

# Swagger/OpenAPI: flujo password con tokenUrl en /api/v1
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login/")


def create_access_token(data: dict) -> Tuple[str, str]:
    """
    Crea un token JWT de acceso con iat, exp, type='access' y jti (JWT ID).
    - Usa SECRET_KEY específica
    - Tiempo de expiración reducido (15 min por defecto)
    - AHORA INCLUYE: access_level, is_super_admin, user_type
    - ✅ REVOCACIÓN: Incluye jti (UUID único) para blacklist
    
    Returns:
        Tuple[str, str]: (token, jti) - Token JWT y su identificador único
    """
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # ✅ REVOCACIÓN: Generar jti (JWT ID) único para cada token
    jti = str(uuid4())
    
    # ✅ AGREGAR CAMPOS DE NIVEL AL PAYLOAD
    level_info = to_encode.get('level_info', {})
    
    to_encode.update({
        "exp": expire,
        "iat": now,
        "type": "access",
        "jti": jti,  # ✅ REVOCACIÓN: JWT ID para blacklist
        "access_level": level_info.get('access_level', 1),
        "is_super_admin": level_info.get('is_super_admin', False),
        "user_type": level_info.get('user_type', 'user')
    })
    
    # Remover level_info temporal del payload
    to_encode.pop('level_info', None)
    
    # Usa SECRET_KEY para access tokens
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return (token, jti)


def create_refresh_token(data: dict) -> Tuple[str, str]:
    """
    Crea un token JWT de refresh con iat, exp, type='refresh' y jti (JWT ID).
    - Usa REFRESH_SECRET_KEY separada (mayor seguridad)
    - Tiempo de expiración largo (7 días por defecto)
    - AHORA INCLUYE: access_level, is_super_admin, user_type
    - ✅ REVOCACIÓN: Incluye jti (UUID único) para blacklist
    
    Returns:
        Tuple[str, str]: (token, jti) - Token JWT y su identificador único
    """
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # ✅ REVOCACIÓN: Generar jti (JWT ID) único para cada token
    jti = str(uuid4())
    
    # ✅ AGREGAR CAMPOS DE NIVEL AL PAYLOAD
    level_info = to_encode.get('level_info', {})
    
    to_encode.update({
        "exp": expire,
        "iat": now,
        "type": "refresh",
        "jti": jti,  # ✅ REVOCACIÓN: JWT ID para blacklist
        "access_level": level_info.get('access_level', 1),
        "is_super_admin": level_info.get('is_super_admin', False),
        "user_type": level_info.get('user_type', 'user')
    })
    
    # Remover level_info temporal del payload
    to_encode.pop('level_info', None)
    
    # Usa REFRESH_SECRET_KEY separada
    token = jwt.encode(to_encode, settings.REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return (token, jti)


async def build_token_payload_for_sso(
    user_full_data: Dict[str, Any],
    cliente_id: UUID,
    user_role_names: List[str]
) -> Dict[str, Any]:
    """
    Construye el payload del token JWT para flujos SSO.
    
    ✅ FASE 1: Incluye cliente_id y level_info igual que login password.
    Esto asegura que la validación de tenant funcione correctamente para SSO.
    
    Args:
        user_full_data: Datos completos del usuario (debe incluir 'usuario_id' y 'nombre_usuario')
        cliente_id: ID del cliente/tenant (UUID)
        user_role_names: Lista de nombres de roles del usuario
    
    Returns:
        Dict con payload completo para JWT, incluyendo:
        - sub: nombre de usuario
        - cliente_id: ID del cliente (string)
        - level_info: Dict con access_level, is_super_admin, user_type
        - es_superadmin: bool (si aplica)
    
    Example:
        ```python
        payload = await build_token_payload_for_sso(
            user_full_data={"usuario_id": uuid, "nombre_usuario": "user"},
            cliente_id=cliente_uuid,
            user_role_names=["Administrador"]
        )
        access_token, jti = create_access_token(data=payload)
        ```
    """
    from app.modules.auth.application.services.auth_service import AuthService
    
    user_id = user_full_data.get('usuario_id')
    if not user_id:
        raise ValueError("user_full_data debe incluir 'usuario_id'")
    
    nombre_usuario = user_full_data.get('nombre_usuario')
    if not nombre_usuario:
        raise ValueError("user_full_data debe incluir 'nombre_usuario'")
    
    # Obtener access_level (igual que en login password)
    level_info = await AuthService.get_user_access_level_info(user_id, cliente_id)
    
    # Determinar si es super admin
    is_super_admin = level_info.get('is_super_admin', False)
    user_type = level_info.get('user_type', 'user')
    
    # Construir payload igual que en login password
    payload = {
        "sub": nombre_usuario,
        "cliente_id": str(cliente_id),  # Convertir UUID a string para JSON serialization
        "level_info": level_info
    }
    
    # Añadir flag de superadmin si aplica
    if is_super_admin:
        payload["es_superadmin"] = True
    
    return payload


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



