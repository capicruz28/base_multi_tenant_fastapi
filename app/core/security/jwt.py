# app/core/security/jwt.py
"""
Utilidades para creación y decodificación de tokens JWT.

✅ ARQUITECTURA: Contiene utilidades de seguridad relacionadas con JWT.
✅ REVOCACIÓN: Incluye jti (JWT ID) para revocación de tokens con Redis.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
import logging
from uuid import uuid4
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



