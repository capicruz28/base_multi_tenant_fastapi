# app/core/security/jwt.py
"""
Utilidades para creación y decodificación de tokens JWT.
"""
from datetime import datetime, timedelta
from typing import Dict, Any
import logging
from jose import JWTError, jwt
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)


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



