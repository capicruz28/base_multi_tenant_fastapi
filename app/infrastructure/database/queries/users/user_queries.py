"""
Queries SQL para gestión de usuarios.

✅ FASE 2: Queries migradas desde sql_constants.py

QUERIES INCLUIDAS:
- SELECT_USUARIOS_PAGINATED
- COUNT_USUARIOS_PAGINATED
- SELECT_USUARIOS_PAGINATED_MULTI_DB
- COUNT_USUARIOS_PAGINATED_MULTI_DB
- GET_USER_COMPLETE_OPTIMIZED_JSON
- GET_USER_COMPLETE_OPTIMIZED_XML
"""

# ============================================
# QUERIES PARA USUARIOS (MULTI-TENANT)
# ============================================

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
        u.proveedor_autenticacion,
        u.fecha_ultimo_cambio_contrasena,
        u.requiere_cambio_contrasena,
        u.intentos_fallidos,
        u.fecha_bloqueo,
        u.sincronizado_desde,
        u.fecha_ultima_sincronizacion,
        u.dni,
        u.telefono,
        u.referencia_externa_id,
        u.referencia_externa_email,
        u.es_eliminado,
        r.rol_id,
        r.nombre AS nombre_rol,
        r.descripcion AS descripcion_rol,
        r.es_activo AS rol_es_activo,
        r.fecha_creacion AS rol_fecha_creacion,
        r.cliente_id AS rol_cliente_id,
        r.codigo_rol AS rol_codigo_rol
    FROM usuario u
    LEFT JOIN usuario_rol ur ON u.usuario_id = ur.usuario_id AND ur.es_activo = 1
    LEFT JOIN rol r ON ur.rol_id = r.rol_id AND (r.es_activo = 1 OR r.cliente_id IS NULL)
    WHERE
        u.es_eliminado = 0
        AND u.cliente_id = :cliente_id 
        AND (:buscar IS NULL OR (
            u.nombre_usuario LIKE :buscar_pattern OR
            u.correo LIKE :buscar_pattern OR
            u.nombre LIKE :buscar_pattern OR
            u.apellido LIKE :buscar_pattern
        ))
)
SELECT * FROM UserRoles
ORDER BY usuario_id 
OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY;
"""

COUNT_USUARIOS_PAGINATED = """
SELECT COUNT(DISTINCT u.usuario_id)
FROM usuario u
WHERE
    u.es_eliminado = 0
    AND u.cliente_id = :cliente_id 
    AND (:buscar IS NULL OR (
        u.nombre_usuario LIKE :buscar_pattern OR
        u.correo LIKE :buscar_pattern OR
        u.nombre LIKE :buscar_pattern OR
        u.apellido LIKE :buscar_pattern
    ));
"""

# Query para BD dedicadas (multi-DB) - no filtra por cliente_id
SELECT_USUARIOS_PAGINATED_MULTI_DB = """
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
        u.proveedor_autenticacion,
        u.fecha_ultimo_cambio_contrasena,
        u.requiere_cambio_contrasena,
        u.intentos_fallidos,
        u.fecha_bloqueo,
        u.sincronizado_desde,
        u.fecha_ultima_sincronizacion,
        u.dni,
        u.telefono,
        u.referencia_externa_id,
        u.referencia_externa_email,
        u.es_eliminado,
        r.rol_id,
        r.nombre AS nombre_rol,
        r.descripcion AS descripcion_rol,
        r.es_activo AS rol_es_activo,
        r.fecha_creacion AS rol_fecha_creacion,
        r.cliente_id AS rol_cliente_id,
        r.codigo_rol AS rol_codigo_rol
    FROM usuario u
    LEFT JOIN usuario_rol ur ON u.usuario_id = ur.usuario_id AND ur.es_activo = 1
    LEFT JOIN rol r ON ur.rol_id = r.rol_id AND r.es_activo = 1
    WHERE
        u.es_eliminado = 0
        AND (:buscar IS NULL OR (
            u.nombre_usuario LIKE :buscar_pattern OR
            u.correo LIKE :buscar_pattern OR
            u.nombre LIKE :buscar_pattern OR
            u.apellido LIKE :buscar_pattern
        ))
)
SELECT * FROM UserRoles
ORDER BY usuario_id 
OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY;
"""

# Count para BD dedicadas (multi-DB) - no filtra por cliente_id
COUNT_USUARIOS_PAGINATED_MULTI_DB = """
SELECT COUNT(DISTINCT u.usuario_id)
FROM usuario u
WHERE
    u.es_eliminado = 0
    AND (:buscar IS NULL OR (
        u.nombre_usuario LIKE :buscar_pattern OR
        u.correo LIKE :buscar_pattern OR
        u.nombre LIKE :buscar_pattern OR
        u.apellido LIKE :buscar_pattern
    ));
"""

# ============================================
# QUERIES OPTIMIZADAS: Usuario Completo con Roles (JSON/XML)
# ============================================

# Query para SQL Server 2016+ (usa FOR JSON PATH - más eficiente)
GET_USER_COMPLETE_OPTIMIZED_JSON = """
SELECT 
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
          AND (r.cliente_id = :cliente_id_roles OR r.cliente_id IS NULL)
        ORDER BY r.nivel_acceso DESC
        FOR JSON PATH
    ) as roles_json,
    ISNULL((
        SELECT MAX(r.nivel_acceso)
        FROM usuario_rol ur
        INNER JOIN rol r ON ur.rol_id = r.rol_id
        WHERE ur.usuario_id = u.usuario_id
          AND ur.es_activo = 1
          AND r.es_activo = 1
          AND (r.cliente_id = :cliente_id_levels OR r.cliente_id IS NULL)
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
          AND (r.cliente_id = :cliente_id_super OR r.cliente_id IS NULL)
    ) > 0 THEN 1 ELSE 0 END as is_super_admin
FROM usuario u
WHERE u.nombre_usuario = :nombre_usuario 
  AND u.es_eliminado = 0
  AND u.cliente_id = :cliente_id_usuario
"""

# Query para SQL Server 2005-2014 (usa FOR XML PATH - compatible)
GET_USER_COMPLETE_OPTIMIZED_XML = """
SELECT 
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
          AND (r.cliente_id = :cliente_id_roles OR r.cliente_id IS NULL)
        ORDER BY r.nivel_acceso DESC
        FOR XML PATH(''), TYPE
    ).value('.', 'NVARCHAR(MAX)'), 1, 1, '[') + ']' as roles_json,
    ISNULL((
        SELECT MAX(r.nivel_acceso)
        FROM usuario_rol ur
        INNER JOIN rol r ON ur.rol_id = r.rol_id
        WHERE ur.usuario_id = u.usuario_id
          AND ur.es_activo = 1
          AND r.es_activo = 1
          AND (r.cliente_id = :cliente_id_levels OR r.cliente_id IS NULL)
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
          AND (r.cliente_id = :cliente_id_super OR r.cliente_id IS NULL)
    ) > 0 THEN 1 ELSE 0 END as is_super_admin
FROM usuario u
WHERE u.nombre_usuario = :nombre_usuario 
  AND u.es_eliminado = 0
  AND u.cliente_id = :cliente_id_usuario
"""

__all__ = [
    "SELECT_USUARIOS_PAGINATED",
    "COUNT_USUARIOS_PAGINATED",
    "SELECT_USUARIOS_PAGINATED_MULTI_DB",
    "COUNT_USUARIOS_PAGINATED_MULTI_DB",
    "GET_USER_COMPLETE_OPTIMIZED_JSON",
    "GET_USER_COMPLETE_OPTIMIZED_XML",
]
