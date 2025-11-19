# app/db/queries.py
from typing import List, Dict, Any, Callable
from app.db.connection import get_db_connection, DatabaseConnection
from app.core.exceptions import DatabaseError
import pyodbc
import logging

logger = logging.getLogger(__name__)

# ============================================
# FUNCIONES DE EJECUCIÓN (CORE)
# ============================================

def execute_query(query: str, params: tuple = (), connection_type: DatabaseConnection = DatabaseConnection.DEFAULT) -> List[Dict[str, Any]]:
    with get_db_connection(connection_type) as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error en execute_query: {str(e)}")
            raise DatabaseError(
                detail=f"Error en la consulta: {str(e)}",
                internal_code="DB_QUERY_ERROR"
            )
        finally:
            if cursor:
                cursor.close()

def execute_auth_query(query: str, params: tuple = ()) -> Dict[str, Any]:
    """
    Ejecuta una consulta específica para autenticación y retorna un único registro.
    Siempre usa la conexión DEFAULT para buscar el usuario y verificar el cliente (fase previa).
    """
    with get_db_connection(DatabaseConnection.DEFAULT) as conn:
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)

            if cursor.description is None:
                return None

            columns = [column[0] for column in cursor.description]
            row = cursor.fetchone()

            if row:
                return dict(zip(columns, row))
            return None

        except Exception as e:
            logger.error(f"Error en execute_auth_query: {str(e)}")
            raise DatabaseError(
                detail=f"Error en la autenticación: {str(e)}",
                internal_code="DB_AUTH_ERROR"
            )
        finally:
            if cursor:
                cursor.close()

def execute_insert(query: str, params: tuple = (), connection_type: DatabaseConnection = DatabaseConnection.DEFAULT) -> Dict[str, Any]:
    """
    Ejecuta una sentencia INSERT y retorna:
      - Los datos retornados por OUTPUT si existen
      - Siempre incluye 'rows_affected' en la respuesta
    """
    with get_db_connection(connection_type) as conn:
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)

            # Verificar OUTPUT
            if cursor.description:
                columns = [column[0] for column in cursor.description]
                output_data = cursor.fetchone()
                result = dict(zip(columns, output_data)) if output_data else {}
            else:
                result = {}

            # Importante: filas afectadas
            rows_affected = cursor.rowcount
            result["rows_affected"] = rows_affected

            conn.commit()
            logger.info(f"Inserción exitosa, filas afectadas: {rows_affected}")
            return result

        except Exception as e:
            conn.rollback()
            logger.error(f"Error en execute_insert: {str(e)}")
            raise DatabaseError(
                detail=f"Error en la inserción: {str(e)}",
                internal_code="DB_INSERT_ERROR"
            )
        finally:
            if cursor:
                cursor.close()

def execute_update(query: str, params: tuple = (), connection_type: DatabaseConnection = DatabaseConnection.DEFAULT) -> Dict[str, Any]:
    with get_db_connection(connection_type) as conn:
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)

            # Obtener número de filas afectadas
            rows_affected = cursor.rowcount

            # Si hay OUTPUT, obtener los datos
            if cursor.description:
                columns = [column[0] for column in cursor.description]
                output_data = cursor.fetchone()
                result = dict(zip(columns, output_data)) if output_data else {}
            else:
                result = {}

            conn.commit()

            # CAMBIO CLAVE: Siempre incluir rows_affected en la respuesta
            result['rows_affected'] = rows_affected

            logger.info(f"Actualización exitosa, filas afectadas: {rows_affected}")
            return result

        except Exception as e:
            conn.rollback()
            logger.error(f"Error en execute_update: {str(e)}")
            raise DatabaseError(
                detail=f"Error en la actualización: {str(e)}",
                internal_code="DB_UPDATE_ERROR"
            )
        finally:
            if cursor:
                cursor.close()

def execute_procedure(procedure_name: str, connection_type: DatabaseConnection = DatabaseConnection.DEFAULT) -> List[Dict[str, Any]]:
    with get_db_connection(connection_type) as conn:
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(f"EXEC {procedure_name}")

            results = []
            while True:
                if cursor.description:
                    columns = [column[0] for column in cursor.description]
                    results.extend([dict(zip(columns, row)) for row in cursor.fetchall()])
                if not cursor.nextset():
                    break
            return results
        except Exception as e:
            logger.error(f"Error en execute_procedure: {str(e)}")
            raise DatabaseError(
                detail=f"Error en el procedimiento: {str(e)}",
                internal_code="DB_PROCEDURE_ERROR"
            )
        finally:
            if cursor:
                cursor.close()

def execute_procedure_params(
    procedure_name: str,
    params: dict,
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT
) -> List[Dict[str, Any]]:
    with get_db_connection(connection_type) as conn:
        cursor = None
        try:
            cursor = conn.cursor()
            param_str = ", ".join([f"@{key} = ?" for key in params.keys()])
            query = f"EXEC {procedure_name} {param_str}"

            cursor.execute(query, tuple(params.values()))

            results = []
            while True:
                if cursor.description:
                    columns = [column[0] for column in cursor.description]
                    results.extend([dict(zip(columns, row)) for row in cursor.fetchall()])
                if not cursor.nextset():
                    break
            return results
        except Exception as e:
            logger.error(f"Error en execute_procedure_params: {str(e)}")
            raise DatabaseError(
                detail=f"Error en el procedimiento: {str(e)}",
                internal_code="DB_PROCEDURE_PARAMS_ERROR"
            )
        finally:
            if cursor:
                cursor.close()

def execute_transaction(
    operations_func: Callable[[pyodbc.Cursor], None],
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT
) -> None:
    """
    Ejecuta operaciones de BD en una transacción.
    Maneja errores de conexión y operación de pyodbc.
    """
    conn = None
    cursor = None
    try:
        with get_db_connection(connection_type) as conn:
            cursor = conn.cursor()
            operations_func(cursor)
            conn.commit()
            logger.debug("Transacción completada exitosamente.")

    except pyodbc.Error as db_err:
        if conn:
            conn.rollback() # Asegurar rollback en error pyodbc
        logger.error(f"Error de base de datos (pyodbc) en transacción: {db_err}", exc_info=True)
        raise DatabaseError(
            detail=f"Error DB en transacción: {str(db_err)}",
            internal_code="DB_TRANSACTION_ERROR"
        )

    except Exception as e:
        if conn:
            conn.rollback() # Asegurar rollback en cualquier otro error
        logger.error(f"Error inesperado (no pyodbc) en transacción: {e}", exc_info=True)
        raise DatabaseError(
            detail=f"Error inesperado en transacción: {str(e)}",
            internal_code="DB_TRANSACTION_UNEXPECTED_ERROR"
        )
    finally:
        if cursor:
            cursor.close()
            
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
        u.cliente_id, -- Añadir cliente_id
        r.rol_id,
        r.nombre AS nombre_rol
        -- Añade aquí otros campos de 'usuario' o 'rol' que necesites
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
        (cliente_id IS NULL OR cliente_id = ?)
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
        (cliente_id IS NULL OR cliente_id = ?)
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
    cmc.conexion_id,
    cmc.servidor,
    cmc.puerto,
    cmc.nombre_bd,
    cmc.usuario_encriptado,
    cmc.password_encriptado,
    cmc.tipo_bd,
    cmc.usa_ssl,
    c.tipo_instalacion,
    c.metadata_json
FROM cliente_modulo_conexion cmc
JOIN cliente c ON cmc.cliente_id = c.cliente_id
WHERE 
    cmc.cliente_id = ? 
    AND cmc.es_activo = 1 
    AND cmc.es_conexion_principal = 1
ORDER BY cmc.conexion_id DESC;
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