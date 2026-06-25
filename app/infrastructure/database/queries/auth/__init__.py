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

from .refresh_token_rotate_queries_core import (
    SQL_LOCK_REFRESH_TOKEN_BY_HASH,
    rotate_refresh_token_core,
)

from .session import (
    close_all_user_sessions_core,
    close_session_core,
    count_active_sessions_core,
    create_session_with_token_tx,
    find_session_by_device_core,
    get_active_session_by_id_core,
    get_family_by_current_token_id_core,
    get_family_by_id_core,
    get_family_by_session_id_core,
    handle_replay_attack_tx,
    insert_token_family_core,
    insert_user_session_core,
    is_session_absolute_expired_core,
    is_session_idle_expired_core,
    list_active_sessions_oldest_first_core,
    mark_family_compromised_core,
    mark_token_used_core,
    purge_expired_tokens_core,
    revoke_token_core,
    revoke_tokens_by_session_core,
    revoke_all_user_sessions_tx,
    revoke_session_tx,
    rotate_refresh_token_tx,
    touch_business_activity_core,
    update_current_token_id_core,
    update_session_empresa_core,
    update_session_on_refresh_core,
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
    "SQL_LOCK_REFRESH_TOKEN_BY_HASH",
    "rotate_refresh_token_core",
    "insert_user_session_core",
    "update_session_empresa_core",
    "update_session_on_refresh_core",
    "touch_business_activity_core",
    "close_session_core",
    "close_all_user_sessions_core",
    "get_active_session_by_id_core",
    "count_active_sessions_core",
    "create_session_with_token_tx",
    "list_active_sessions_oldest_first_core",
    "is_session_idle_expired_core",
    "is_session_absolute_expired_core",
    "find_session_by_device_core",
    "get_family_by_current_token_id_core",
    "get_family_by_id_core",
    "get_family_by_session_id_core",
    "handle_replay_attack_tx",
    "insert_token_family_core",
    "mark_family_compromised_core",
    "mark_token_used_core",
    "purge_expired_tokens_core",
    "revoke_token_core",
    "revoke_tokens_by_session_core",
    "revoke_all_user_sessions_tx",
    "revoke_session_tx",
    "rotate_refresh_token_tx",
    "update_current_token_id_core",
]
