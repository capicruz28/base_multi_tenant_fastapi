# app/core/auth.py
"""
Módulo de compatibilidad para autenticación.

✅ ARQUITECTURA: Este archivo ahora es un módulo de compatibilidad que re-exporta
funciones desde sus nuevas ubicaciones correctas:
- Utilidades JWT → app.core.security.jwt
- Lógica de autenticación → app.modules.auth.application.services.auth_service

Este módulo se mantiene para no romper imports existentes, pero se recomienda
actualizar los imports para usar las nuevas ubicaciones directamente.
"""

# ✅ Re-exportar oauth2_scheme desde security/jwt
from app.core.security.jwt import oauth2_scheme

# ✅ Re-exportar funciones de autenticación desde auth_service
from app.modules.auth.application.services.auth_service import (
    authenticate_user,
    authenticate_user_sso_azure_ad,
    authenticate_user_sso_google,
    get_user_access_level_info,
    revoke_session_by_token_id,
    get_all_active_sessions,
    AuthService
)

# ✅ Re-exportar get_current_user (necesita oauth2_scheme como dependencia)
# Esta función necesita ser un wrapper porque usa Depends(oauth2_scheme)
from fastapi import Depends
from app.modules.auth.application.services.auth_service import AuthService as _AuthService

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Obtiene el usuario actual basado en el access token (Bearer).
    
    ✅ COMPATIBILIDAD: Wrapper que mantiene la firma original.
    """
    return await _AuthService.get_current_user(token)


# ✅ Re-exportar get_current_user_from_refresh (necesita Request, Cookie, Body)
from fastapi import Request, Cookie, Body
from typing import Optional
from pydantic import BaseModel

class RefreshTokenBody(BaseModel):
    """Schema para recibir refresh token en el body (móvil)."""
    refresh_token: Optional[str] = None

async def get_current_user_from_refresh(
    request: Request,
    refresh_token_cookie: Optional[str] = Cookie(None, alias="refresh_token"),
    body: RefreshTokenBody = Body(default=RefreshTokenBody())
):
    """
    Obtiene el usuario actual validando el refresh token.
    
    ✅ COMPATIBILIDAD: Wrapper que mantiene la firma original.
    """
    return await _AuthService.get_current_user_from_refresh(
        request,
        refresh_token_cookie,
        body.refresh_token
    )


__all__ = [
    'oauth2_scheme',
    'authenticate_user',
    'authenticate_user_sso_azure_ad',
    'authenticate_user_sso_google',
    'get_current_user',
    'get_current_user_from_refresh',
    'get_user_access_level_info',
    'revoke_session_by_token_id',
    'get_all_active_sessions',
    'AuthService',
    'RefreshTokenBody'
]
