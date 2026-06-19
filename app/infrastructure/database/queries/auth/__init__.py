"""
Queries de autenticación y gestión de usuarios.

✅ FASE 2: Queries migradas desde sql_constants.py
✅ FASE 1 SEGURIDAD: Funciones SQLAlchemy Core para refresh tokens

Este módulo contiene:
- Queries de autenticación (login, niveles de acceso)
- Funciones SQLAlchemy Core para refresh tokens (canónicas)
"""

from .auth_queries import (
    GET_USER_MAX_ACCESS_LEVEL,
    IS_USER_SUPER_ADMIN,
    GET_USER_ACCESS_LEVEL_INFO_COMPLETE,
)

from .refresh_token_queries_core import (
    record_refresh_token_activity_core,
    is_refresh_token_session_idle_expired_core,
    get_refresh_token_by_hash_any_state_core,
    get_refresh_token_by_hash_core,
    insert_refresh_token_core,
    revoke_refresh_token_core,
    revoke_all_user_tokens_core,
    get_active_sessions_by_user_core,
    get_active_sessions_by_user_oldest_first_core,
    delete_expired_tokens_core,
    revoke_refresh_token_by_id_core,
)

__all__ = [
    "GET_USER_MAX_ACCESS_LEVEL",
    "IS_USER_SUPER_ADMIN",
    "GET_USER_ACCESS_LEVEL_INFO_COMPLETE",
    "record_refresh_token_activity_core",
    "is_refresh_token_session_idle_expired_core",
    "get_refresh_token_by_hash_any_state_core",
    "get_refresh_token_by_hash_core",
    "insert_refresh_token_core",
    "revoke_refresh_token_core",
    "revoke_all_user_tokens_core",
    "get_active_sessions_by_user_core",
    "get_active_sessions_by_user_oldest_first_core",
    "delete_expired_tokens_core",
    "revoke_refresh_token_by_id_core",
]
