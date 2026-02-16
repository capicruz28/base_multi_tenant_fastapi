"""
Queries de autenticación y gestión de usuarios.

✅ FASE 2: Queries migradas desde sql_constants.py

Este módulo contiene:
- Queries de autenticación (login, refresh tokens)
- Queries de niveles de acceso (LBAC)
- Queries de usuarios relacionadas con auth
"""

from .auth_queries import (
    GET_USER_MAX_ACCESS_LEVEL,
    IS_USER_SUPER_ADMIN,
    GET_USER_ACCESS_LEVEL_INFO_COMPLETE,
    INSERT_REFRESH_TOKEN,
    GET_REFRESH_TOKEN_BY_HASH,
    REVOKE_REFRESH_TOKEN,
    REVOKE_REFRESH_TOKEN_BY_USER,
    REVOKE_ALL_USER_TOKENS,
    DELETE_EXPIRED_TOKENS,
    GET_ACTIVE_SESSIONS_BY_USER,
    GET_ALL_ACTIVE_SESSIONS,
    REVOKE_REFRESH_TOKEN_BY_ID,
)

__all__ = [
    "GET_USER_MAX_ACCESS_LEVEL",
    "IS_USER_SUPER_ADMIN",
    "GET_USER_ACCESS_LEVEL_INFO_COMPLETE",
    "INSERT_REFRESH_TOKEN",
    "GET_REFRESH_TOKEN_BY_HASH",
    "REVOKE_REFRESH_TOKEN",
    "REVOKE_REFRESH_TOKEN_BY_USER",
    "REVOKE_ALL_USER_TOKENS",
    "DELETE_EXPIRED_TOKENS",
    "GET_ACTIVE_SESSIONS_BY_USER",
    "GET_ALL_ACTIVE_SESSIONS",
    "REVOKE_REFRESH_TOKEN_BY_ID",
]
