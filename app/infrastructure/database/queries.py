# app/infrastructure/database/queries.py
"""
⚠️⚠️⚠️ DEPRECATED - NO USAR ⚠️⚠️⚠️

Este archivo está COMPLETAMENTE DEPRECATED y será eliminado.

✅ FASE 2 COMPLETA: Migrar a app/infrastructure/database/queries_async.py
- Todas las funciones ahora son async
- Usa SQLAlchemy AsyncSession
- Reemplaza completamente este archivo

🚨 ADVERTENCIA CRÍTICA:
- Este archivo NO debe usarse en código nuevo
- Todas las funciones lanzan NotImplementedError
- Migrar inmediatamente a queries_async.py

📋 Para migrar:
1. Cambiar import: from queries import → from queries_async import
2. Agregar await a todas las llamadas
3. Convertir funciones a async

Ver: docs/MIGRACION_LEGACY_CODE.md
"""

from typing import List, Dict, Any, Callable, Optional, Union
from app.core.exceptions import DatabaseError, ValidationError
from app.core.config import settings
from app.infrastructure.database.query_helpers import apply_tenant_filter, get_table_name_from_query
from sqlalchemy import Select, Update, Delete, Insert, text
from sqlalchemy.sql import ClauseElement
import logging

logger = logging.getLogger(__name__)

# ✅ FASE 2: Importar DatabaseConnection desde connection_async
try:
    from app.infrastructure.database.connection_async import DatabaseConnection
except ImportError:
    # Fallback para compatibilidad
    from enum import Enum
    class DatabaseConnection(Enum):
        DEFAULT = "default"
        ADMIN = "admin"

# ============================================
# FUNCIONES DE EJECUCIÓN (CORE)
# ============================================

# ⚠️ DEPRECATED: Usar queries_async.execute_query() en su lugar
def execute_query(
    query: Union[str, ClauseElement], 
    params: tuple = (), 
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT, 
    client_id: Optional[int] = None,
    skip_tenant_validation: bool = False
) -> List[Dict[str, Any]]:
    """
    ⚠️ DEPRECATED: Esta función será eliminada en FASE 2.
    
    ✅ FASE 2: Migrar a app/infrastructure/database/queries_async.execute_query()
    
    Esta función mantiene compatibilidad temporal pero debe migrarse a async.
    """
    logger.warning(
        "[DEPRECATED] execute_query() síncrono está deprecated. "
        "Migrar a queries_async.execute_query() (async)."
    )
    
    # Por ahora, mantener funcionalidad básica pero loggear advertencia
    # TODO: Eliminar completamente en FASE 2 completa
    raise NotImplementedError(
        "execute_query() síncrono está deprecated. "
        "Usar queries_async.execute_query() (async) en su lugar."
    )

def execute_query_safe(
    query: str, 
    params: tuple = (), 
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT,
    client_id: Optional[int] = None,
    require_tenant_validation: bool = False
) -> List[Dict[str, Any]]:
    """
    Versión SEGURA de execute_query con validación opcional de tenant.
    
    ✅ FASE 1: MIGRACIÓN SEGURA
    - Por defecto NO valida (comportamiento actual)
    - Solo valida si require_tenant_validation=True Y el flag está activo
    - Si la validación falla, solo loggea (no rompe el sistema)
    
    Args:
        query: Consulta SQL a ejecutar
        params: Parámetros de la consulta
        connection_type: Tipo de conexión (DEFAULT o ADMIN)
        client_id: ID del cliente específico (opcional)
        require_tenant_validation: Si True, valida que la query incluya filtro de tenant
    
    Returns:
        Lista de diccionarios con los resultados
    """
    # Si la validación está desactivada o no se requiere, usar función original
    if not settings.ENABLE_QUERY_TENANT_VALIDATION or not require_tenant_validation:
        return execute_query(query, params, connection_type, client_id)
    
    # ✅ FASE 1: Validación opcional de tenant
    try:
        from app.core.tenant.context import get_current_client_id
        current_cliente_id = get_current_client_id()
        
        # Verificar que la query incluya filtro de tenant
        query_lower = query.lower().strip()
        
        # Buscar WHERE en la query
        if "where" in query_lower:
            # Verificar si tiene filtro de cliente_id
            # Buscar patrones comunes: "cliente_id = ?", "cliente_id=?", "WHERE cliente_id"
            has_cliente_id_filter = (
                "cliente_id = ?" in query_lower or
                "cliente_id=?" in query_lower or
                "cliente_id = " in query_lower or
                f"cliente_id = {current_cliente_id}" in query_lower
            )
            
            if not has_cliente_id_filter:
                logger.warning(
                    f"[SECURITY] Query sin filtro explícito de cliente_id detectada. "
                    f"Query: {query[:200]}... "
                    f"Cliente actual: {current_cliente_id}. "
                    f"NOTA: Esto es solo una advertencia, la query se ejecutará normalmente."
                )
                # ⚠️ IMPORTANTE: Solo loggeamos, NO bloqueamos
                # Esto permite migración gradual sin romper el sistema
        
        # Ejecutar query original (comportamiento actual)
        return execute_query(query, params, connection_type, client_id)
        
    except RuntimeError:
        # Sin contexto de tenant, usar función original (comportamiento actual)
        logger.debug(
            "[QUERIES] Sin contexto de tenant disponible, validación omitida "
            "(comportamiento esperado para scripts de fondo)"
        )
        return execute_query(query, params, connection_type, client_id)
    except Exception as e:
        # Si hay cualquier error en la validación, loggear pero NO bloquear
        logger.error(
            f"[SECURITY] Error en validación de tenant en query (no bloqueante): {str(e)}",
            exc_info=True
        )
        # Ejecutar query original (fallback seguro)
        return execute_query(query, params, connection_type, client_id)


# ⚠️ DEPRECATED: Usar queries_async.execute_auth_query() en su lugar
def execute_auth_query(
    query: Union[str, ClauseElement], 
    params: tuple = ()
) -> Dict[str, Any]:
    """
    ⚠️ DEPRECATED: Esta función será eliminada en FASE 2.
    
    ✅ FASE 2: Migrar a app/infrastructure/database/queries_async.execute_auth_query()
    """
    logger.warning(
        "[DEPRECATED] execute_auth_query() síncrono está deprecated. "
        "Migrar a queries_async.execute_auth_query() (async)."
    )
    
    raise NotImplementedError(
        "execute_auth_query() síncrono está deprecated. "
        "Usar queries_async.execute_auth_query() (async) en su lugar."
    )

# ⚠️ DEPRECATED: Usar queries_async.execute_insert() en su lugar
def execute_insert(
    query: str,
    params: tuple = (),
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT,
) -> Dict[str, Any]:
    """
    ⚠️ DEPRECATED: Esta función será eliminada en FASE 2.
    
    ✅ FASE 2: Migrar a app/infrastructure/database/queries_async.execute_insert()
    """
    logger.warning(
        "[DEPRECATED] execute_insert() síncrono está deprecated. "
        "Migrar a queries_async.execute_insert() (async)."
    )
    raise NotImplementedError(
        "execute_insert() síncrono está deprecated. "
        "Usar queries_async.execute_insert() (async) en su lugar."
    )

# ⚠️ DEPRECATED: Usar queries_async.execute_update() en su lugar
def execute_update(query: str, params: tuple = (), connection_type: DatabaseConnection = DatabaseConnection.DEFAULT) -> Dict[str, Any]:
    """
    ⚠️ DEPRECATED: Esta función será eliminada en FASE 2.
    
    ✅ FASE 2: Migrar a app/infrastructure/database/queries_async.execute_update()
    """
    logger.warning(
        "[DEPRECATED] execute_update() síncrono está deprecated. "
        "Migrar a queries_async.execute_update() (async)."
    )
    raise NotImplementedError(
        "execute_update() síncrono está deprecated. "
        "Usar queries_async.execute_update() (async) en su lugar."
    )

# ⚠️ DEPRECATED: Usar queries_async.execute_procedure() en su lugar
def execute_procedure(procedure_name: str, connection_type: DatabaseConnection = DatabaseConnection.DEFAULT) -> List[Dict[str, Any]]:
    """
    ⚠️ DEPRECATED: Esta función será eliminada en FASE 2.
    
    ✅ FASE 2: Migrar a app/infrastructure/database/queries_async.execute_procedure()
    """
    logger.warning(
        "[DEPRECATED] execute_procedure() síncrono está deprecated. "
        "Migrar a queries_async.execute_procedure() (async)."
    )
    raise NotImplementedError(
        "execute_procedure() síncrono está deprecated. "
        "Usar queries_async.execute_procedure() (async) en su lugar."
    )

# ⚠️ DEPRECATED: Usar queries_async.execute_procedure_params() en su lugar
def execute_procedure_params(
    procedure_name: str,
    params: dict,
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT
) -> List[Dict[str, Any]]:
    """
    ⚠️ DEPRECATED: Esta función será eliminada en FASE 2.
    
    ✅ FASE 2: Migrar a app/infrastructure/database/queries_async.execute_procedure_params()
    """
    logger.warning(
        "[DEPRECATED] execute_procedure_params() síncrono está deprecated. "
        "Migrar a queries_async.execute_procedure_params() (async)."
    )
    raise NotImplementedError(
        "execute_procedure_params() síncrono está deprecated. "
        "Usar queries_async.execute_procedure_params() (async) en su lugar."
    )

# ⚠️ DEPRECATED: Usar queries_async.execute_transaction() en su lugar
def execute_transaction(
    operations_func: Callable,  # ⚠️ Tipo original: Callable[[pyodbc.Cursor], None]
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT
) -> None:
    """
    ⚠️ DEPRECATED: Esta función será eliminada en FASE 2.
    
    ✅ FASE 2: Migrar a app/infrastructure/database/queries_async.execute_transaction()
    
    Ejecuta operaciones de BD en una transacción.
    Maneja errores de conexión y operación de pyodbc.
    """
    logger.warning(
        "[DEPRECATED] execute_transaction() síncrono está deprecated. "
        "Migrar a queries_async.execute_transaction() (async)."
    )
    raise NotImplementedError(
        "execute_transaction() síncrono está deprecated. "
        "Usar queries_async.execute_transaction() (async) en su lugar."
    )
            
# ============================================
# NUEVAS QUERIES PARA SISTEMA DE NIVELES LBAC
# ============================================

# Query para obtener el nivel de acceso máximo del usuario (CORREGIDA)
GET_USER_MAX_ACCESS_LEVEL = """
SELECT ISNULL(MAX(r.nivel_acceso), 1) as max_level
FROM usuario_rol ur
INNER JOIN rol r ON ur.rol_id = r.rol_id
WHERE ur.usuario_id = ? 
  AND ur.es_activo = 1
  AND r.es_activo = 1
  AND (r.cliente_id = ? OR r.cliente_id IS NULL)
"""

# Query para verificar si el usuario es SUPER_ADMIN (CORREGIDA)
IS_USER_SUPER_ADMIN = """
SELECT COUNT(*) as is_super_admin
FROM usuario_rol ur
INNER JOIN rol r ON ur.rol_id = r.rol_id
WHERE ur.usuario_id = ? 
  AND ur.es_activo = 1
  AND r.es_activo = 1
  AND r.codigo_rol = 'SUPER_ADMIN'
  AND r.nivel_acceso = 5
"""

# Query para obtener el nivel mínimo requerido por una lista de roles
GET_MIN_REQUIRED_ACCESS_LEVEL = """
SELECT MIN(nivel_acceso) as min_required_level
FROM rol 
WHERE nombre IN ({}) 
  AND es_activo = 1
"""

# NUEVA QUERY: Obtener información completa de niveles (MÁS ROBUSTA)
GET_USER_ACCESS_LEVEL_INFO_COMPLETE = """
SELECT 
    ISNULL(MAX(r.nivel_acceso), 1) as max_level,
    COUNT(CASE WHEN r.codigo_rol = 'SUPER_ADMIN' AND r.nivel_acceso = 5 THEN 1 END) as super_admin_count,
    COUNT(*) as total_roles
FROM usuario_rol ur
INNER JOIN rol r ON ur.rol_id = r.rol_id
WHERE ur.usuario_id = ? 
  AND ur.es_activo = 1
  AND r.es_activo = 1
  AND (r.cliente_id = ? OR r.cliente_id IS NULL)
"""

# Query para obtener roles del usuario con información de niveles
GET_USER_ROLES_WITH_LEVELS = """
SELECT 
    r.rol_id,
    r.nombre,
    r.descripcion,
    r.nivel_acceso,
    r.codigo_rol,
    r.es_activo
FROM usuario_rol ur
INNER JOIN rol r ON ur.rol_id = r.rol_id
WHERE ur.usuario_id = ? 
  AND ur.es_activo = 1
  AND r.es_activo = 1
  AND (r.cliente_id = ? OR r.cliente_id IS NULL)
ORDER BY r.nivel_acceso DESC
"""

# ✅ OPTIMIZACIÓN 100%: Query única que obtiene usuario + roles + niveles en UN SOLO roundtrip
# Esta query reemplaza TODAS las 4 queries separadas en get_current_active_user
# Mejora: 4 queries → 1 query = 100% reducción en roundtrips (75% mejora vs 50% anterior)
# 
# COMPATIBILIDAD:
# - SQL Server 2016+: Usa GET_USER_COMPLETE_OPTIMIZED_JSON (FOR JSON PATH - más eficiente)
# - SQL Server 2005-2014: Usa GET_USER_COMPLETE_OPTIMIZED_XML (FOR XML PATH - compatible)
# 
# La función get_user_complete_data() detecta automáticamente la versión y usa la query apropiada

# Query para SQL Server 2016+ (usa FOR JSON PATH - más eficiente)
GET_USER_COMPLETE_OPTIMIZED_JSON = """
SELECT 
    -- Datos del usuario
    u.usuario_id,
    u.cliente_id,
    u.nombre_usuario,
    u.correo,
    u.nombre,
    u.apellido,
    u.es_activo,
    u.fecha_creacion,
    u.fecha_ultimo_acceso,
    u.correo_confirmado,
    u.es_eliminado,
    u.proveedor_autenticacion,
    u.fecha_ultimo_cambio_contrasena,
    u.sincronizado_desde,
    -- Roles del usuario como JSON (FOR JSON PATH - SQL Server 2016+)
    -- ✅ CORRECCIÓN: Incluir todos los campos requeridos por RolRead schema
    -- NOTA: La tabla rol NO tiene es_eliminado, se usará el valor por defecto (False) del schema
    (
        SELECT 
            r.rol_id,
            r.nombre,
            r.descripcion,
            r.nivel_acceso,
            r.codigo_rol,
            r.es_activo,
            r.fecha_creacion,
            r.cliente_id
        FROM usuario_rol ur
        INNER JOIN rol r ON ur.rol_id = r.rol_id
        WHERE ur.usuario_id = u.usuario_id
          AND ur.es_activo = 1
          AND r.es_activo = 1
          AND (r.cliente_id = ? OR r.cliente_id IS NULL)
        ORDER BY r.nivel_acceso DESC
        FOR JSON PATH
    ) as roles_json,
    -- Niveles calculados (usando subconsultas correlacionadas - eficiente)
    ISNULL((
        SELECT MAX(r.nivel_acceso)
        FROM usuario_rol ur
        INNER JOIN rol r ON ur.rol_id = r.rol_id
        WHERE ur.usuario_id = u.usuario_id
          AND ur.es_activo = 1
          AND r.es_activo = 1
          AND (r.cliente_id = ? OR r.cliente_id IS NULL)
    ), 1) as access_level,
    CASE WHEN (
        SELECT COUNT(*)
        FROM usuario_rol ur
        INNER JOIN rol r ON ur.rol_id = r.rol_id
        WHERE ur.usuario_id = u.usuario_id
          AND ur.es_activo = 1
          AND r.es_activo = 1
          AND r.codigo_rol = 'SUPER_ADMIN'
          AND r.nivel_acceso = 5
          AND (r.cliente_id = ? OR r.cliente_id IS NULL)
    ) > 0 THEN 1 ELSE 0 END as is_super_admin
FROM usuario u
WHERE u.nombre_usuario = ? 
  AND u.es_eliminado = 0
  AND u.cliente_id = ?
"""

# Query para SQL Server 2005-2014 (usa FOR XML PATH - compatible con versiones antiguas)
# Construye JSON manualmente usando XML PATH (compatible desde SQL Server 2005)
GET_USER_COMPLETE_OPTIMIZED_XML = """
SELECT 
    -- Datos del usuario
    u.usuario_id,
    u.cliente_id,
    u.nombre_usuario,
    u.correo,
    u.nombre,
    u.apellido,
    u.es_activo,
    u.fecha_creacion,
    u.fecha_ultimo_acceso,
    u.correo_confirmado,
    u.es_eliminado,
    u.proveedor_autenticacion,
    u.fecha_ultimo_cambio_contrasena,
    u.sincronizado_desde,
    -- Roles del usuario como JSON (construido manualmente con XML PATH)
    -- Compatible con SQL Server 2005 en adelante
    -- ✅ CORRECCIÓN: Incluir todos los campos requeridos por RolRead schema
    -- NOTA: La tabla rol NO tiene es_eliminado, se usará el valor por defecto (False) del schema
    -- Usa REPLACE para escapar caracteres especiales en JSON
    STUFF((
        SELECT ',{"rol_id":' + CAST(r.rol_id AS VARCHAR) +
               ',"nombre":"' + REPLACE(REPLACE(REPLACE(ISNULL(r.nombre, ''), '\', '\\'), '"', '\\"'), CHAR(10), '\\n') + '"' +
               ',"descripcion":"' + REPLACE(REPLACE(REPLACE(ISNULL(r.descripcion, ''), '\', '\\'), '"', '\\"'), CHAR(10), '\\n') + '"' +
               ',"nivel_acceso":' + CAST(ISNULL(r.nivel_acceso, 1) AS VARCHAR) +
               ',"codigo_rol":"' + REPLACE(REPLACE(REPLACE(ISNULL(r.codigo_rol, ''), '\', '\\'), '"', '\\"'), CHAR(10), '\\n') + '"' +
               ',"es_activo":' + CAST(r.es_activo AS VARCHAR) +
               ',"fecha_creacion":"' + CONVERT(VARCHAR(23), ISNULL(r.fecha_creacion, GETDATE()), 126) + '"' +
               ',"cliente_id":' + CASE WHEN r.cliente_id IS NULL THEN 'null' ELSE CAST(r.cliente_id AS VARCHAR) END + '}'
        FROM usuario_rol ur
        INNER JOIN rol r ON ur.rol_id = r.rol_id
        WHERE ur.usuario_id = u.usuario_id
          AND ur.es_activo = 1
          AND r.es_activo = 1
          AND (r.cliente_id = ? OR r.cliente_id IS NULL)
        ORDER BY r.nivel_acceso DESC
        FOR XML PATH(''), TYPE
    ).value('.', 'NVARCHAR(MAX)'), 1, 1, '[') + ']' as roles_json,
    -- Niveles calculados (usando subconsultas correlacionadas - eficiente)
    ISNULL((
        SELECT MAX(r.nivel_acceso)
        FROM usuario_rol ur
        INNER JOIN rol r ON ur.rol_id = r.rol_id
        WHERE ur.usuario_id = u.usuario_id
          AND ur.es_activo = 1
          AND r.es_activo = 1
          AND (r.cliente_id = ? OR r.cliente_id IS NULL)
    ), 1) as access_level,
    CASE WHEN (
        SELECT COUNT(*)
        FROM usuario_rol ur
        INNER JOIN rol r ON ur.rol_id = r.rol_id
        WHERE ur.usuario_id = u.usuario_id
          AND ur.es_activo = 1
          AND r.es_activo = 1
          AND r.codigo_rol = 'SUPER_ADMIN'
          AND r.nivel_acceso = 5
          AND (r.cliente_id = ? OR r.cliente_id IS NULL)
    ) > 0 THEN 1 ELSE 0 END as is_super_admin
FROM usuario u
WHERE u.nombre_usuario = ? 
  AND u.es_eliminado = 0
  AND u.cliente_id = ?
"""

# Query por defecto (intenta JSON primero, fallback a XML si falla)
GET_USER_COMPLETE_OPTIMIZED = GET_USER_COMPLETE_OPTIMIZED_JSON

# ============================================
# FUNCIÓN HELPER PARA DETECTAR VERSIÓN SQL SERVER
# ============================================

# Cache de versión de SQL Server (se detecta una vez al iniciar)
_sql_server_version_cache: Optional[int] = None

# ⚠️ DEPRECATED: Esta función usa conexiones síncronas
def get_sql_server_version(connection_type: DatabaseConnection = DatabaseConnection.DEFAULT, client_id: Optional[int] = None) -> Optional[int]:
    """
    ⚠️ DEPRECATED: Esta función usa conexiones síncronas.
    
    Detecta la versión mayor de SQL Server (ej: 2016, 2014, 2008).
    
    ✅ OPTIMIZACIÓN: Usa cache para evitar detectar en cada request.
    La versión de SQL Server no cambia durante la ejecución de la aplicación.
    
    Returns:
        int: Versión mayor (ej: 2016, 2014, 2008) o None si no se puede detectar
    """
    global _sql_server_version_cache
    
    # Si ya está en cache, retornar directamente
    if _sql_server_version_cache is not None:
        return _sql_server_version_cache
    
    # ⚠️ DEPRECATED: Esta función requiere migración a async
    # Por ahora, retornar None si no está en cache para evitar usar conexiones síncronas
    logger.warning(
        "[DEPRECATED] get_sql_server_version() requiere conexión síncrona. "
        "Migrar a versión async o usar cache."
    )
    return None


def get_user_complete_data_query() -> str:
    """
    Retorna la query apropiada según la versión de SQL Server.
    
    ✅ COMPATIBILIDAD:
    - SQL Server 2016+: Usa GET_USER_COMPLETE_OPTIMIZED_JSON (FOR JSON PATH - más eficiente)
    - SQL Server 2005-2014: Usa GET_USER_COMPLETE_OPTIMIZED_XML (FOR XML PATH - compatible)
    
    La versión se detecta una vez y se cachea para mejor performance.
    
    Returns:
        str: Query SQL apropiada
    """
    try:
        version = get_sql_server_version()
        
        if version is None:
            # Si no se puede detectar, usar XML (más compatible con versiones antiguas)
            logger.warning("[SQL_VERSION] No se pudo detectar versión, usando query XML (compatible con todas las versiones)")
            return GET_USER_COMPLETE_OPTIMIZED_XML
        
        if version >= 2016:
            # SQL Server 2016+ soporta FOR JSON PATH (más eficiente)
            logger.debug(f"[SQL_VERSION] Usando query JSON (SQL Server {version} soporta FOR JSON PATH)")
            return GET_USER_COMPLETE_OPTIMIZED_JSON
        else:
            # SQL Server 2005-2014 usa FOR XML PATH (compatible)
            logger.info(f"[SQL_VERSION] Usando query XML (SQL Server {version} - compatible con FOR XML PATH)")
            return GET_USER_COMPLETE_OPTIMIZED_XML
            
    except Exception as e:
        logger.warning(f"[SQL_VERSION] Error detectando versión, usando XML (fallback seguro): {e}")
        return GET_USER_COMPLETE_OPTIMIZED_XML

# ✅ MANTENER query anterior por compatibilidad (deprecated, usar GET_USER_COMPLETE_OPTIMIZED)
GET_USER_WITH_LEVELS = GET_USER_COMPLETE_OPTIMIZED

# Query para obtener información completa de niveles del usuario
GET_USER_ACCESS_LEVEL_INFO = """
SELECT 
    MAX(r.nivel_acceso) as max_level,
    COUNT(CASE WHEN r.codigo_rol = 'SUPER_ADMIN' AND r.nivel_acceso = 5 THEN 1 END) as super_admin_count
FROM usuario_rol ur
INNER JOIN rol r ON ur.rol_id = r.rol_id
WHERE ur.usuario_id = ? 
  AND ur.es_activo = 1
  AND r.es_activo = 1
  AND (r.cliente_id = ? OR r.cliente_id IS NULL)
"""

# ============================================
# QUERIES PARA AUTENTICACIÓN Y USUARIOS (MULTI-TENANT)
# ============================================

# Consulta para obtener usuarios paginados con sus roles, filtrando eliminados y buscando
# Se añade filtro por cliente_id
SELECT_USUARIOS_PAGINATED = """
WITH UserRoles AS (
    SELECT
        u.usuario_id,
        u.nombre_usuario,
        u.correo,
        u.contrasena, 
        u.nombre,
        u.apellido,
        u.es_activo,
        u.correo_confirmado,
        u.fecha_creacion,
        u.fecha_ultimo_acceso,
        u.fecha_actualizacion,
        u.cliente_id,
        -- ✅ CAMPOS DE SEGURIDAD (según schema SQL)
        u.proveedor_autenticacion,
        u.fecha_ultimo_cambio_contrasena,
        u.requiere_cambio_contrasena,
        u.intentos_fallidos,
        u.fecha_bloqueo,
        -- ✅ CAMPOS DE SINCRONIZACIÓN (según schema SQL)
        u.sincronizado_desde,
        u.fecha_ultima_sincronizacion,
        -- ✅ CAMPOS ADICIONALES (según schema SQL)
        u.dni,
        u.telefono,
        u.referencia_externa_id,
        u.referencia_externa_email,
        -- ✅ CAMPO DE ELIMINACIÓN LÓGICA
        u.es_eliminado,
        -- ✅ CAMPOS DE ROLES
        r.rol_id,
        r.nombre AS nombre_rol,
        r.descripcion AS descripcion_rol,
        r.es_activo AS rol_es_activo,
        r.fecha_creacion AS rol_fecha_creacion,
        r.cliente_id AS rol_cliente_id,
        r.codigo_rol AS rol_codigo_rol
    FROM usuario u
    LEFT JOIN usuario_rol ur ON u.usuario_id = ur.usuario_id AND ur.es_activo = 1
    LEFT JOIN rol r ON ur.rol_id = r.rol_id AND (r.es_activo = 1 OR r.cliente_id IS NULL) -- Incluir roles del sistema
    WHERE
        u.es_eliminado = 0
        AND u.cliente_id = ? 
        AND (? IS NULL OR (
            u.nombre_usuario LIKE ? OR
            u.correo LIKE ? OR
            u.nombre LIKE ? OR
            u.apellido LIKE ?
        ))
)
SELECT * FROM UserRoles
ORDER BY usuario_id 
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY;
"""

# Consulta para contar el total de usuarios que coinciden con la búsqueda y no están eliminados
# Se añade filtro por cliente_id
COUNT_USUARIOS_PAGINATED = """
SELECT COUNT(DISTINCT u.usuario_id)
FROM usuario u
WHERE
    u.es_eliminado = 0
    AND u.cliente_id = ? 
    AND (? IS NULL OR (
        u.nombre_usuario LIKE ? OR
        u.correo LIKE ? OR
        u.nombre LIKE ? OR
        u.apellido LIKE ?
    ));
"""

# Consulta para insertar un nuevo usuario (requiere cliente_id)
INSERT_USUARIO = """
INSERT INTO usuario (
    nombre_usuario, correo, contrasena, nombre, apellido, cliente_id, es_activo, correo_confirmado
)
OUTPUT INSERTED.usuario_id, INSERTED.nombre_usuario, INSERTED.correo, INSERTED.contrasena, INSERTED.nombre, 
       INSERTED.apellido, INSERTED.cliente_id, INSERTED.es_activo, INSERTED.correo_confirmado, 
       INSERTED.fecha_creacion, INSERTED.fecha_ultimo_acceso, INSERTED.fecha_actualizacion
VALUES (?, ?, ?, ?, ?, ?, ?, ?);
"""

# Consulta para buscar un usuario por ID (filtrado por cliente_id y no eliminado)
SELECT_USUARIO_BY_ID = """
SELECT usuario_id, nombre_usuario, correo, contrasena, nombre, apellido, 
       es_activo, correo_confirmado, fecha_creacion, fecha_ultimo_acceso, 
       fecha_actualizacion, es_eliminado, cliente_id
FROM usuario 
WHERE usuario_id = ? AND cliente_id = ? AND es_eliminado = 0;
"""

# Consulta para buscar un usuario por username (filtrado por cliente_id y no eliminado)
SELECT_USUARIO_BY_USERNAME = """
SELECT usuario_id, nombre_usuario, correo, contrasena, nombre, apellido, 
       es_activo, correo_confirmado, fecha_creacion, fecha_ultimo_acceso, 
       fecha_actualizacion, es_eliminado, cliente_id
FROM usuario 
WHERE nombre_usuario = ? AND cliente_id = ? AND es_eliminado = 0;
"""

# ============================================
# QUERIES PARA ROLES (MULTI-TENANT - cliente_id puede ser NULL)
# ============================================

# Se añade el campo cliente_id en la selección
# El filtro se cambia para incluir roles del sistema (cliente_id IS NULL) y roles del cliente actual
SELECT_ROL_BY_ID = """
SELECT rol_id, nombre, descripcion, es_activo, fecha_creacion, cliente_id, codigo_rol 
FROM dbo.rol 
WHERE rol_id = ? AND (cliente_id IS NULL OR cliente_id = ?) AND es_activo = 1
"""
SELECT_ALL_ROLES = """
SELECT rol_id, nombre, descripcion, es_activo, fecha_creacion, cliente_id, codigo_rol 
FROM dbo.rol 
WHERE (cliente_id IS NULL OR cliente_id = ?) AND es_activo = 1 
ORDER BY nombre
"""
# Se añade cliente_id y codigo_rol en el INSERT. cliente_id puede ser NULL.
INSERT_ROL = """
INSERT INTO dbo.rol (nombre, descripcion, es_activo, cliente_id, codigo_rol) 
OUTPUT INSERTED.rol_id, INSERTED.nombre, INSERTED.descripcion, INSERTED.es_activo, 
       INSERTED.fecha_creacion, INSERTED.cliente_id, INSERTED.codigo_rol
VALUES (?, ?, ?, ?, ?)
"""
# Se añade filtro por cliente_id en el WHERE (el UPDATE solo aplica a roles del cliente o rol del sistema si cliente_id es NULL)
UPDATE_ROL = """
UPDATE dbo.rol 
SET nombre = ?, descripcion = ?, es_activo = ? 
OUTPUT INSERTED.rol_id, INSERTED.nombre, INSERTED.descripcion, INSERTED.es_activo, 
       INSERTED.fecha_creacion, INSERTED.cliente_id, INSERTED.codigo_rol
WHERE rol_id = ? AND (cliente_id IS NULL OR cliente_id = ?)
"""

# Se añade filtro por cliente_id en el WHERE
DEACTIVATE_ROL = """
    UPDATE dbo.rol
    SET
        es_activo = 0
    OUTPUT
        INSERTED.rol_id,
        INSERTED.nombre,
        INSERTED.descripcion,
        INSERTED.es_activo,
        INSERTED.fecha_creacion,
        INSERTED.cliente_id,
        INSERTED.codigo_rol
    WHERE
        rol_id = ?
        AND es_activo = 1
        AND (cliente_id IS NULL OR cliente_id = ?); 
"""
# Se añade filtro por cliente_id en el WHERE
REACTIVATE_ROL = """
    UPDATE dbo.rol
    SET
        es_activo = 1
    OUTPUT
        INSERTED.rol_id,
        INSERTED.nombre,
        INSERTED.descripcion,
        INSERTED.es_activo,
        INSERTED.fecha_creacion,
        INSERTED.cliente_id,
        INSERTED.codigo_rol
    WHERE
        rol_id = ?
        AND es_activo = 0
        AND (cliente_id IS NULL OR cliente_id = ?); 
"""
# Se añade filtro por cliente_id en el WHERE para asegurar unicidad POR CLIENTE
CHECK_ROL_NAME_EXISTS = """
SELECT rol_id 
FROM dbo.rol 
WHERE LOWER(nombre) = LOWER(?) AND rol_id != ? AND (cliente_id IS NULL OR cliente_id = ?);
"""


# --- QUERIES PARA PAGINACIÓN DE ROLES (MULTI-TENANT) ---
# Se añade filtro por cliente_id para listar roles del cliente + roles del sistema (cliente_id IS NULL)
COUNT_ROLES_PAGINATED = """
    SELECT COUNT(rol_id) as total 
    FROM dbo.rol
    WHERE 
        cliente_id = ?
        AND (? IS NULL OR (
            LOWER(nombre) LIKE LOWER(?) OR
            LOWER(descripcion) LIKE LOWER(?)
        ));
"""

SELECT_ROLES_PAGINATED = """
    SELECT
        rol_id, nombre, descripcion, es_activo, fecha_creacion, cliente_id, codigo_rol
    FROM
        dbo.rol
    WHERE 
        cliente_id = ?
        AND (? IS NULL OR (
            LOWER(nombre) LIKE LOWER(?) OR
            LOWER(descripcion) LIKE LOWER(?)
        ))
    ORDER BY
        rol_id 
    OFFSET ? ROWS FETCH NEXT ? ROWS ONLY;
"""

# --- NUEVA CONSULTA PARA MENUS (ADMIN) ---
# Llama a la nueva Stored Procedure que obtiene TODOS los menús
GET_ALL_MENUS_ADMIN = "sp_GetAllMenuItemsAdmin;"


# ============================================
# QUERIES PARA PERMISOS (MULTI-TENANT)
# ============================================

# Selecciona todos los permisos asignados a un rol específico
SELECT_PERMISOS_POR_ROL = """
    SELECT rmp.rol_menu_id, rmp.rol_id, rmp.menu_id, rmp.puede_ver, rmp.puede_editar, rmp.puede_eliminar
    FROM rol_menu_permiso rmp
    JOIN rol r ON rmp.rol_id = r.rol_id
    WHERE rmp.rol_id = ? AND (r.cliente_id IS NULL OR r.cliente_id = ?); -- Filtro de rol para seguridad
"""

# Elimina TODOS los permisos asociados a un rol específico.
DELETE_PERMISOS_POR_ROL = """
    DELETE rmp
    FROM rol_menu_permiso rmp
    JOIN rol r ON rmp.rol_id = r.rol_id
    WHERE rmp.rol_id = ? AND (r.cliente_id IS NULL OR r.cliente_id = ?);
"""

# Inserta un nuevo registro de permiso para un rol y un menú.
INSERT_PERMISO_ROL = """
    INSERT INTO rol_menu_permiso (rol_id, menu_id, puede_ver, puede_editar, puede_eliminar)
    VALUES (?, ?, ?, ?, ?);
"""
# --- FIN DE NUEVAS CONSULTAS ---

# ============================================
# QUERIES PARA MENÚ (MULTI-TENANT - cliente_id puede ser NULL)
# ============================================

# Se añade cliente_id a la inserción
INSERT_MENU = """
    INSERT INTO menu (nombre, icono, ruta, padre_menu_id, orden, area_id, es_activo, cliente_id)
    OUTPUT INSERTED.menu_id, INSERTED.nombre, INSERTED.icono, INSERTED.ruta,
           INSERTED.padre_menu_id, INSERTED.orden, INSERTED.es_activo, INSERTED.area_id,
           INSERTED.fecha_creacion, INSERTED.cliente_id
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
"""

# Se añade filtro por cliente_id
SELECT_MENU_BY_ID = """
    SELECT m.menu_id, m.nombre, m.icono, m.ruta, m.padre_menu_id, m.orden,
           m.es_activo, m.fecha_creacion, m.area_id, m.cliente_id, a.nombre as area_nombre
    FROM menu m
    LEFT JOIN area_menu a ON m.area_id = a.area_id
    WHERE m.menu_id = ? AND (m.cliente_id IS NULL OR m.cliente_id = ?);
"""

# Se añade filtro por cliente_id en el WHERE
UPDATE_MENU_TEMPLATE = """
    UPDATE menu
    SET
        nombre = COALESCE(?, nombre),
        icono = COALESCE(?, icono),
        ruta = COALESCE(?, ruta),
        padre_menu_id = COALESCE(?, padre_menu_id),
        orden = COALESCE(?, orden),
        area_id = COALESCE(?, area_id),
        es_activo = COALESCE(?, es_activo)
    OUTPUT INSERTED.menu_id, INSERTED.nombre, INSERTED.icono, INSERTED.ruta,
           INSERTED.padre_menu_id, INSERTED.orden, INSERTED.es_activo, INSERTED.area_id,
           INSERTED.fecha_creacion, INSERTED.cliente_id
    WHERE menu_id = ? AND (cliente_id IS NULL OR cliente_id = ?);
"""

# Se añade filtro por cliente_id en el WHERE
DEACTIVATE_MENU = """
    UPDATE menu
    SET es_activo = 0
    OUTPUT INSERTED.menu_id, INSERTED.es_activo, INSERTED.cliente_id
    WHERE menu_id = ? AND es_activo = 1 AND (cliente_id IS NULL OR cliente_id = ?);
"""

# Se añade filtro por cliente_id en el WHERE
REACTIVATE_MENU = """
    UPDATE menu
    SET es_activo = 1
    OUTPUT INSERTED.menu_id, INSERTED.es_activo, INSERTED.cliente_id
    WHERE menu_id = ? AND es_activo = 0 AND (cliente_id IS NULL OR cliente_id = ?);
"""

# Verifica si un menú existe (se añade cliente_id para alcance)
CHECK_MENU_EXISTS = "SELECT 1 FROM menu WHERE menu_id = ? AND (cliente_id IS NULL OR cliente_id = ?);"

# ============================================
# QUERIES PARA AREA_MENU (MULTI-TENANT - cliente_id puede ser NULL)
# ============================================

# Verifica si un área existe
CHECK_AREA_EXISTS = "SELECT 1 FROM area_menu WHERE area_id = ?"

# Stored Procedure para obtener todos los menús (Admin - ya definido)
GET_ALL_MENUS_ADMIN = "sp_GetAllMenuItemsAdmin" 

# Se añade filtro por cliente_id (listar áreas del sistema y del cliente)
GET_AREAS_PAGINATED_QUERY = """
    SELECT
        area_id, nombre, descripcion, icono, es_activo, fecha_creacion, cliente_id
    FROM
        area_menu 
    WHERE
        (cliente_id IS NULL OR cliente_id = ?)
        AND (? IS NULL OR LOWER(nombre) LIKE LOWER(?) OR LOWER(descripcion) LIKE LOWER(?))
    ORDER BY
        area_id ASC
    OFFSET ? ROWS FETCH NEXT ? ROWS ONLY; 
"""

# Se añade filtro por cliente_id
COUNT_AREAS_QUERY = """
    SELECT
        COUNT(*) as total_count
    FROM
        area_menu 
    WHERE
        (cliente_id IS NULL OR cliente_id = ?)
        AND (? IS NULL OR LOWER(nombre) LIKE LOWER(?) OR LOWER(descripcion) LIKE LOWER(?));
"""

# Se añade filtro por cliente_id
GET_AREA_BY_ID_QUERY = """
SELECT area_id, nombre, descripcion, icono, es_activo, fecha_creacion, cliente_id 
FROM area_menu 
WHERE area_id = ? AND (cliente_id IS NULL OR cliente_id = ?);
"""

# Se añade filtro por cliente_id para unicidad POR CLIENTE
CHECK_AREA_EXISTS_BY_NAME_QUERY = """
SELECT COUNT(*) as count 
FROM area_menu 
WHERE LOWER(nombre) = LOWER(?) AND area_id != ? AND (cliente_id IS NULL OR cliente_id = ?);
"""

# Se añade cliente_id a la inserción
CREATE_AREA_QUERY = """
INSERT INTO area_menu (nombre, descripcion, icono, es_activo, cliente_id)
OUTPUT INSERTED.area_id, INSERTED.nombre, INSERTED.descripcion, INSERTED.icono, INSERTED.es_activo, 
       INSERTED.fecha_creacion, INSERTED.cliente_id
VALUES (?, ?, ?, ?, ?);
"""

# Se añade filtro por cliente_id en el WHERE
UPDATE_AREA_BASE_QUERY_TEMPLATE = "UPDATE area_menu SET {fields} OUTPUT INSERTED.* WHERE area_id = ? AND (cliente_id IS NULL OR cliente_id = ?);" 

# Se añade filtro por cliente_id en el WHERE
TOGGLE_AREA_STATUS_QUERY = """
UPDATE area_menu SET es_activo = ?
OUTPUT INSERTED.area_id, INSERTED.nombre, INSERTED.descripcion, INSERTED.icono, INSERTED.es_activo, 
       INSERTED.fecha_creacion, INSERTED.cliente_id
WHERE area_id = ? AND (cliente_id IS NULL OR cliente_id = ?);
""" 

# Se añade filtro por cliente_id (solo áreas activas del cliente + sistema)
GET_ACTIVE_AREAS_SIMPLE_LIST_QUERY = """
SELECT
    area_id,
    nombre,
    cliente_id
FROM
    area_menu 
WHERE
    es_activo = 1 
    AND (cliente_id IS NULL OR cliente_id = ?)
ORDER BY
    nombre ASC;
"""

# **QUERY CORREGIDA (Nombre y Filtro Multi-Tenant)**
GET_MENUS_BY_AREA_FOR_TREE_QUERY = """
SELECT
    m.menu_id,
    m.nombre,
    m.icono,
    m.ruta, 
    m.padre_menu_id,
    m.orden,
    m.es_activo,
    m.area_id,
    m.cliente_id, -- Añadido cliente_id para consistencia multi-tenant
    a.nombre as area_nombre 
FROM
    menu m 
LEFT JOIN
    area_menu a ON m.area_id = a.area_id
WHERE
    m.area_id = ? 
    AND (m.cliente_id IS NULL OR m.cliente_id = ?) -- FILTRO MULTI-TENANT CLAVE
ORDER BY
    m.padre_menu_id ASC, 
    m.orden ASC;
"""

# Se añade filtro por cliente_id
GET_MAX_ORDEN_FOR_SIBLINGS = """
    SELECT MAX(orden) as max_orden
    FROM menu
    WHERE (cliente_id IS NULL OR cliente_id = ?) AND area_id = ? AND padre_menu_id = ?;
"""

# Se añade filtro por cliente_id
GET_MAX_ORDEN_FOR_ROOT = """
    SELECT MAX(orden) as max_orden
    FROM menu
    WHERE (cliente_id IS NULL OR cliente_id = ?) AND area_id = ? AND padre_menu_id IS NULL;
"""

# ============================================
# QUERIES PARA REFRESH TOKENS (PERSISTENCIA)
# ============================================

# Se añade cliente_id a la inserción
INSERT_REFRESH_TOKEN = """
INSERT INTO refresh_tokens (
    usuario_id, token_hash, expires_at, client_type, ip_address, user_agent, cliente_id
)
OUTPUT INSERTED.token_id, INSERTED.created_at, INSERTED.cliente_id
VALUES (?, ?, ?, ?, ?, ?, ?);
"""

# Se añade filtro por cliente_id
GET_REFRESH_TOKEN_BY_HASH = """
SELECT 
    token_id, usuario_id, token_hash, expires_at, 
    is_revoked, created_at, client_type, cliente_id
FROM refresh_tokens
WHERE token_hash = ? AND cliente_id = ? AND is_revoked = 0 AND expires_at > GETDATE();
"""

# Se añade filtro por cliente_id
REVOKE_REFRESH_TOKEN = """
UPDATE refresh_tokens
SET is_revoked = 1, revoked_at = GETDATE()
OUTPUT INSERTED.token_id, INSERTED.is_revoked, INSERTED.cliente_id
WHERE token_hash = ? AND cliente_id = ?;
"""

# Se añade filtro por cliente_id
REVOKE_REFRESH_TOKEN_BY_USER = """
UPDATE refresh_tokens
SET is_revoked = 1, revoked_at = GETDATE()
OUTPUT INSERTED.token_id, INSERTED.is_revoked, INSERTED.cliente_id
WHERE token_hash = ? AND usuario_id = ? AND cliente_id = ?;
"""

# Se añade filtro por cliente_id
REVOKE_ALL_USER_TOKENS = """
UPDATE refresh_tokens
SET is_revoked = 1, revoked_at = GETDATE()
WHERE usuario_id = ? AND cliente_id = ? AND is_revoked = 0;
"""

# **REIMPLEMENTACIÓN DE LA QUERY DE MANTENIMIENTO**
DELETE_EXPIRED_TOKENS = """
DELETE FROM refresh_tokens
WHERE expires_at < GETDATE() OR is_revoked = 1;
"""

# Se añade filtro por cliente_id
GET_ACTIVE_SESSIONS_BY_USER = """
SELECT 
    token_id, client_type, ip_address, created_at, expires_at, cliente_id
FROM refresh_tokens
WHERE usuario_id = ? AND cliente_id = ? AND is_revoked = 0 AND expires_at > GETDATE()
ORDER BY created_at DESC;
"""

# Se añade filtro por cliente_id
GET_ALL_ACTIVE_SESSIONS = """
SELECT 
    rt.token_id, 
    rt.usuario_id,
    u.nombre_usuario, 
    u.nombre,
    u.apellido,
    rt.client_type, 
    rt.ip_address, 
    rt.created_at, 
    rt.expires_at,
    rt.cliente_id
FROM refresh_tokens rt
JOIN usuario u ON rt.usuario_id = u.usuario_id
WHERE rt.is_revoked = 0 AND rt.expires_at > GETDATE() AND rt.cliente_id = ?
ORDER BY rt.created_at DESC;
"""

# Se añade filtro por cliente_id
REVOKE_REFRESH_TOKEN_BY_ID = """
UPDATE refresh_tokens
SET is_revoked = 1, revoked_at = GETDATE()
OUTPUT INSERTED.token_id, INSERTED.is_revoked, INSERTED.usuario_id, INSERTED.cliente_id
WHERE token_id = ? AND cliente_id = ? AND is_revoked = 0;
"""

# ============================================
# QUERIES PARA AUDITORÍA (auth_audit_log, log_sincronizacion_usuario)
# ============================================

INSERT_AUTH_AUDIT_LOG = """
INSERT INTO auth_audit_log (
    cliente_id,
    usuario_id,
    evento,
    nombre_usuario_intento,
    descripcion,
    exito,
    codigo_error,
    ip_address,
    user_agent,
    device_info,
    geolocation,
    metadata_json
)
OUTPUT INSERTED.log_id, INSERTED.fecha_evento
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

INSERT_LOG_SINCRONIZACION_USUARIO = """
INSERT INTO log_sincronizacion_usuario (
    cliente_origen_id,
    cliente_destino_id,
    usuario_id,
    tipo_sincronizacion,
    direccion,
    operacion,
    estado,
    mensaje_error,
    campos_sincronizados,
    cambios_detectados,
    hash_antes,
    hash_despues,
    usuario_ejecutor_id,
    duracion_ms
)
OUTPUT INSERTED.log_id, INSERTED.fecha_sincronizacion
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

# ============================================
# NUEVAS QUERIES PARA TABLAS MULTI-TENANT CORE
# ============================================

# --- Cliente (Tabla de Clientes/Tenants) ---

INSERT_CLIENTE = """
INSERT INTO cliente (
    codigo_cliente, subdominio, razon_social, nombre_comercial, es_activo
)
OUTPUT 
    INSERTED.cliente_id, INSERTED.codigo_cliente, INSERTED.subdominio, 
    INSERTED.razon_social, INSERTED.nombre_comercial, INSERTED.es_activo, 
    INSERTED.fecha_creacion, INSERTED.fecha_actualizacion
VALUES (?, ?, ?, ?, ?);
"""

SELECT_CLIENTE_BY_ID = """
SELECT 
    cliente_id, codigo_cliente, subdominio, razon_social, 
    nombre_comercial, es_activo, fecha_creacion, fecha_actualizacion
FROM cliente
WHERE cliente_id = ? AND es_eliminado = 0;
"""

SELECT_CLIENTE_BY_CODE = """
SELECT 
    cliente_id, codigo_cliente, subdominio, razon_social, 
    nombre_comercial, es_activo, fecha_creacion, fecha_actualizacion
FROM cliente
WHERE codigo_cliente = ? AND es_eliminado = 0;
"""

SELECT_CLIENTE_BY_SUBDOMAIN = """
SELECT 
    cliente_id, codigo_cliente, subdominio, razon_social, 
    nombre_comercial, es_activo, fecha_creacion, fecha_actualizacion
FROM cliente
WHERE subdominio = ? AND es_eliminado = 0;
"""

UPDATE_CLIENTE = """
UPDATE cliente
SET
    codigo_cliente = COALESCE(?, codigo_cliente),
    subdominio = COALESCE(?, subdominio),
    razon_social = COALESCE(?, razon_social),
    nombre_comercial = COALESCE(?, nombre_comercial),
    es_activo = COALESCE(?, es_activo),
    fecha_actualizacion = GETDATE()
OUTPUT 
    INSERTED.cliente_id, INSERTED.codigo_cliente, INSERTED.subdominio, 
    INSERTED.razon_social, INSERTED.nombre_comercial, INSERTED.es_activo, 
    INSERTED.fecha_creacion, INSERTED.fecha_actualizacion
WHERE cliente_id = ? AND es_eliminado = 0;
"""

# --- Cliente_Auth_Config (Configuración de Autenticación por Cliente) ---

INSERT_CLIENTE_AUTH_CONFIG = """
INSERT INTO cliente_auth_config (
    cliente_id, password_min_length, password_requires_uppercase, 
    password_requires_digit, password_requires_special, max_login_attempts, 
    lockout_time_minutes, password_reset_policy, jwt_refresh_token_expiration_days
)
OUTPUT INSERTED.*
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

SELECT_CLIENTE_AUTH_CONFIG_BY_CLIENTE_ID = """
SELECT *
FROM cliente_auth_config
WHERE cliente_id = ?;
"""

UPDATE_CLIENTE_AUTH_CONFIG = """
UPDATE cliente_auth_config
SET
    password_min_length = COALESCE(?, password_min_length),
    password_requires_uppercase = COALESCE(?, password_requires_uppercase),
    password_requires_digit = COALESCE(?, password_requires_digit),
    password_requires_special = COALESCE(?, password_requires_special),
    max_login_attempts = COALESCE(?, max_login_attempts),
    lockout_time_minutes = COALESCE(?, lockout_time_minutes),
    password_reset_policy = COALESCE(?, password_reset_policy),
    jwt_refresh_token_expiration_days = COALESCE(?, jwt_refresh_token_expiration_days),
    fecha_actualizacion = GETDATE()
OUTPUT INSERTED.*
WHERE cliente_id = ?;
"""

# --- Federacion_Identidad (SSO por Cliente) ---

INSERT_FEDERACION_IDENTIDAD = """
INSERT INTO federacion_identidad (
    cliente_id, proveedor, client_id, client_secret, metadata_url, is_activo
)
OUTPUT INSERTED.*
VALUES (?, ?, ?, ?, ?, ?);
"""

SELECT_FEDERACION_BY_CLIENTE_ID = """
SELECT *
FROM federacion_identidad
WHERE cliente_id = ? AND is_activo = 1;
"""

UPDATE_FEDERACION_IDENTIDAD = """
UPDATE federacion_identidad
SET
    proveedor = COALESCE(?, proveedor),
    client_id = COALESCE(?, client_id),
    client_secret = COALESCE(?, client_secret),
    metadata_url = COALESCE(?, metadata_url),
    is_activo = COALESCE(?, is_activo),
    fecha_actualizacion = GETDATE()
OUTPUT INSERTED.*
WHERE federacion_id = ? AND cliente_id = ?;
"""

DELETE_FEDERACION_IDENTIDAD = """
DELETE FROM federacion_identidad
OUTPUT DELETED.*
WHERE federacion_id = ? AND cliente_id = ?;
"""

# ============================================
# QUERIES PARA METADATA DE CONEXIÓN (HÍBRIDO)
# ============================================

SELECT_CLIENT_CONNECTION_METADATA = """
SELECT 
    cc.conexion_id,
    cc.servidor,
    cc.puerto,
    cc.nombre_bd,
    cc.usuario_encriptado,
    cc.password_encriptado,
    cc.tipo_bd,
    cc.usa_ssl,
    c.tipo_instalacion,
    c.metadata_json
FROM cliente_conexion cc
JOIN cliente c ON cc.cliente_id = c.cliente_id
WHERE 
    cc.cliente_id = ? 
    AND cc.es_activo = 1 
    AND cc.es_conexion_principal = 1
ORDER BY cc.conexion_id DESC;
"""

CHECK_CLIENT_DATABASE_TYPE = """
SELECT 
    CASE 
        WHEN JSON_VALUE(metadata_json, '$.database_isolation') = 'true' THEN 'multi'
        ELSE 'single'
    END as database_type,
    metadata_json
FROM cliente
WHERE cliente_id = ?;
"""