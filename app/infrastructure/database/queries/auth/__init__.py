"""
Queries de autenticación y gestión de usuarios.

✅ FASE 2: Queries migradas desde sql_constants.py
✅ FASE 1 SEGURIDAD: Funciones SQLAlchemy Core agregadas

Este módulo contiene:
- Queries de autenticación (login, refresh tokens)
- Queries de niveles de acceso (LBAC)
- Queries de usuarios relacionadas con auth
- Funciones SQLAlchemy Core para refresh tokens (recomendadas)
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

# ✅ FASE 1 SEGURIDAD: Exportar funciones SQLAlchemy Core (recomendadas)
from .refresh_token_queries_core import (
    get_refresh_token_by_hash_core,
    insert_refresh_token_core,
    revoke_refresh_token_core,
    revoke_all_user_tokens_core,
    get_active_sessions_by_user_core,
    delete_expired_tokens_core,
)

__all__ = [
    # TextClause queries (legacy, aún soportadas)
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
    # SQLAlchemy Core functions (recomendadas)
    "get_refresh_token_by_hash_core",
    "insert_refresh_token_core",
    "revoke_refresh_token_core",
    "revoke_all_user_tokens_core",
    "get_active_sessions_by_user_core",
    "delete_expired_tokens_core",
]
