"""
⚠️ DEPRECATED: Este archivo está siendo refactorizado.

✅ FASE 2: Migrar a app/infrastructure/database/queries/{modulo}/{modulo}_queries.py

IMPORTS DEPRECADOS (mantener por compatibilidad durante migración):
- GET_USER_ACCESS_LEVEL_INFO_COMPLETE → queries.auth.auth_queries
- SELECT_USUARIOS_PAGINATED → queries.users.user_queries
- SELECT_ROLES_PAGINATED → queries.rbac.rbac_queries
- GET_AREAS_PAGINATED_QUERY → queries.menus.menu_queries
- INSERT_AUTH_AUDIT_LOG → queries.audit.audit_queries
- ... (ver docs/MIGRACION_QUERIES.md para mapeo completo)

Este archivo será eliminado en FASE 3 después de migración completa.

Constantes SQL para queries comunes.

FASE 4B: Modulo centralizado para constantes SQL.
Este modulo contiene todas las queries SQL como strings que se usan en el sistema.
Las queries deben usarse con text().bindparams() para seguridad y validacion de tenant.
"""

import warnings

# ✅ FASE 2: Deprecation warning para alertar sobre migración
warnings.warn(
    "sql_constants.py está deprecated. "
    "Usar app.infrastructure.database.queries.{modulo}.{modulo}_queries en su lugar. "
    "Ver docs/MIGRACION_QUERIES.md para guía de migración.",
    DeprecationWarning,
    stacklevel=2
)

# ============================================
# ✅ FASE 2: RE-EXPORTS DESDE MÓDULOS NUEVOS (COMPATIBILIDAD)
# ============================================
# Las queries ahora están en módulos específicos, pero re-exportamos
# desde aquí para mantener compatibilidad durante migración

from app.infrastructure.database.queries.auth import (
    GET_USER_MAX_ACCESS_LEVEL,
    IS_USER_SUPER_ADMIN,
    GET_USER_ACCESS_LEVEL_INFO_COMPLETE,
)

# Mantener definiciones originales comentadas para referencia durante migración
# GET_USER_MAX_ACCESS_LEVEL = """..."""  # → queries.auth.auth_queries
# IS_USER_SUPER_ADMIN = """..."""  # → queries.auth.auth_queries
# GET_USER_ACCESS_LEVEL_INFO_COMPLETE = """..."""  # → queries.auth.auth_queries

# ============================================
# ✅ FASE 2: RE-EXPORTS DESDE queries.users (COMPATIBILIDAD)
# ============================================

from app.infrastructure.database.queries.users import (
    SELECT_USUARIOS_PAGINATED,
    COUNT_USUARIOS_PAGINATED,
    SELECT_USUARIOS_PAGINATED_MULTI_DB,
    COUNT_USUARIOS_PAGINATED_MULTI_DB,
    GET_USER_COMPLETE_OPTIMIZED_JSON,
    GET_USER_COMPLETE_OPTIMIZED_XML,
)

# ============================================
# ✅ FASE 2: RE-EXPORTS DESDE queries.rbac (COMPATIBILIDAD)
# ============================================

from app.infrastructure.database.queries.rbac import (
    SELECT_ROLES_PAGINATED,
    COUNT_ROLES_PAGINATED,
    SELECT_PERMISOS_POR_ROL,
    DEACTIVATE_ROL,
    REACTIVATE_ROL,
    DELETE_PERMISOS_POR_ROL,
    INSERT_PERMISO_ROL,
)

# ============================================
# ✅ FASE 2: RE-EXPORTS DESDE queries.auth (REFRESH TOKENS)
# ============================================

from app.infrastructure.database.queries.auth import (
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

# ============================================
# ✅ FASE 2: RE-EXPORTS DESDE queries.audit (COMPATIBILIDAD)
# ============================================

from app.infrastructure.database.queries.audit import (
    INSERT_AUTH_AUDIT_LOG,
    INSERT_LOG_SINCRONIZACION_USUARIO,
)

# ============================================
# ✅ FASE 2: RE-EXPORTS DESDE queries.menus (COMPATIBILIDAD)
# ============================================

from app.infrastructure.database.queries.menus import (
    GET_AREAS_PAGINATED_QUERY,
    COUNT_AREAS_QUERY,
    GET_AREA_BY_ID_QUERY,
    CHECK_AREA_EXISTS_BY_NAME_QUERY,
    CREATE_AREA_QUERY,
    UPDATE_AREA_BASE_QUERY_TEMPLATE,
    TOGGLE_AREA_STATUS_QUERY,
    GET_ACTIVE_AREAS_SIMPLE_LIST_QUERY,
    INSERT_MENU,
    SELECT_MENU_BY_ID,
    UPDATE_MENU_TEMPLATE,
    DEACTIVATE_MENU,
    REACTIVATE_MENU,
    CHECK_MENU_EXISTS,
    CHECK_AREA_EXISTS,
    GET_MENUS_BY_AREA_FOR_TREE_QUERY,
    GET_MAX_ORDEN_FOR_SIBLINGS,
    GET_MAX_ORDEN_FOR_ROOT,
    GET_ALL_MENUS_ADMIN,
)

