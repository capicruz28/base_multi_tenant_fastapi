"""
Constantes SQL para queries comunes.

FASE 4B: Modulo centralizado para constantes SQL.
Este modulo contiene todas las queries SQL como strings que se usan en el sistema.
Las queries deben usarse con text().bindparams() para seguridad y validacion de tenant.
"""

# ============================================
# QUERIES PARA SISTEMA DE NIVELES LBAC
# ============================================

GET_USER_MAX_ACCESS_LEVEL = """
SELECT ISNULL(MAX(r.nivel_acceso), 1) as max_level
FROM usuario_rol ur
INNER JOIN rol r ON ur.rol_id = r.rol_id
WHERE ur.usuario_id = :usuario_id 
  AND ur.es_activo = 1
  AND r.es_activo = 1
  AND (r.cliente_id = :cliente_id OR r.cliente_id IS NULL)
"""

IS_USER_SUPER_ADMIN = """
SELECT COUNT(*) as is_super_admin
FROM usuario_rol ur
INNER JOIN rol r ON ur.rol_id = r.rol_id
WHERE ur.usuario_id = :usuario_id 
  AND ur.es_activo = 1
  AND r.es_activo = 1
  AND r.codigo_rol = 'SUPER_ADMIN'
  AND r.nivel_acceso = 5
"""

GET_USER_ACCESS_LEVEL_INFO_COMPLETE = """
SELECT 
    ISNULL(MAX(r.nivel_acceso), 1) as max_level,
    COUNT(CASE WHEN r.codigo_rol = 'SUPER_ADMIN' AND r.nivel_acceso = 5 THEN 1 END) as super_admin_count,
    COUNT(*) as total_roles
FROM usuario_rol ur
INNER JOIN rol r ON ur.rol_id = r.rol_id
WHERE ur.usuario_id = :usuario_id 
  AND ur.es_activo = 1
  AND r.es_activo = 1
  AND (r.cliente_id = :cliente_id OR r.cliente_id IS NULL)
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

# ============================================
# QUERIES PARA ROLES (MULTI-TENANT)
# ============================================

SELECT_ROLES_PAGINATED = """
SELECT 
    r.rol_id,
    r.nombre,
    r.descripcion,
    r.es_activo,
    r.fecha_creacion,
    r.cliente_id,
    r.codigo_rol,
    r.nivel_acceso
FROM rol r
WHERE 
    (r.cliente_id = :cliente_id OR r.cliente_id IS NULL)
    AND r.es_activo = 1
    AND (:buscar IS NULL OR (
        r.nombre LIKE :buscar_pattern OR
        r.descripcion LIKE :buscar_pattern
    ))
ORDER BY r.nivel_acceso DESC, r.nombre
OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY;
"""

COUNT_ROLES_PAGINATED = """
SELECT COUNT(*)
FROM rol r
WHERE 
    (r.cliente_id = :cliente_id OR r.cliente_id IS NULL)
    AND r.es_activo = 1
    AND (:buscar IS NULL OR (
        r.nombre LIKE :buscar_pattern OR
        r.descripcion LIKE :buscar_pattern
    ));
"""

# ============================================
# QUERIES PARA PERMISOS
# ============================================

SELECT_PERMISOS_POR_ROL = """
SELECT 
    rmp.permiso_id,
    rmp.rol_id,
    rmp.menu_id,
    rmp.cliente_id,
    rmp.puede_ver,
    rmp.puede_crear,
    rmp.puede_editar,
    rmp.puede_eliminar,
    rmp.puede_exportar,
    rmp.puede_imprimir,
    m.nombre AS menu_nombre,
    m.ruta AS menu_ruta
FROM rol_menu_permiso rmp
INNER JOIN menu m ON rmp.menu_id = m.menu_id
WHERE 
    rmp.rol_id = :rol_id
    AND rmp.cliente_id = :cliente_id
ORDER BY m.orden;
"""

# ============================================
# QUERIES PARA DESACTIVACION/REACTIVACION
# ============================================

DEACTIVATE_ROL = """
UPDATE rol
SET es_activo = 0,
    fecha_actualizacion = GETDATE()
WHERE rol_id = :rol_id
  AND cliente_id = :cliente_id;
"""

REACTIVATE_ROL = """
UPDATE rol
SET es_activo = 1,
    fecha_actualizacion = GETDATE()
WHERE rol_id = :rol_id
  AND cliente_id = :cliente_id;
"""

# ============================================
# QUERIES PARA PERMISOS DE ROL
# ============================================

DELETE_PERMISOS_POR_ROL = """
DELETE FROM rol_menu_permiso
WHERE rol_id = :rol_id
  AND cliente_id = :cliente_id;
"""

INSERT_PERMISO_ROL = """
INSERT INTO rol_menu_permiso (
    cliente_id, rol_id, menu_id, 
    puede_ver, puede_crear, puede_editar, 
    puede_eliminar, puede_exportar, puede_imprimir
)
VALUES (
    :cliente_id, :rol_id, :menu_id,
    :puede_ver, :puede_crear, :puede_editar,
    :puede_eliminar, :puede_exportar, :puede_imprimir
);
"""

# ============================================
# QUERIES PARA REFRESH TOKENS
# ============================================

INSERT_REFRESH_TOKEN = """
INSERT INTO refresh_tokens (
    usuario_id, token_hash, expires_at, client_type, ip_address, user_agent, cliente_id
)
OUTPUT INSERTED.token_id, INSERTED.usuario_id, INSERTED.cliente_id, INSERTED.expires_at, INSERTED.created_at
VALUES (:usuario_id, :token_hash, :expires_at, :client_type, :ip_address, :user_agent, :cliente_id);
"""

GET_REFRESH_TOKEN_BY_HASH = """
SELECT 
    token_id, usuario_id, token_hash, expires_at, 
    is_revoked, created_at, client_type, cliente_id
FROM refresh_tokens
WHERE token_hash = :token_hash
  AND cliente_id = :cliente_id
  AND is_revoked = 0
  AND expires_at > GETDATE();
"""

REVOKE_REFRESH_TOKEN = """
UPDATE refresh_tokens
SET is_revoked = 1, revoked_at = GETDATE()
OUTPUT INSERTED.token_id, INSERTED.is_revoked, INSERTED.cliente_id
WHERE token_hash = :token_hash
  AND cliente_id = :cliente_id;
"""

REVOKE_REFRESH_TOKEN_BY_USER = """
UPDATE refresh_tokens
SET is_revoked = 1, revoked_at = GETDATE()
OUTPUT INSERTED.token_id, INSERTED.is_revoked, INSERTED.cliente_id
WHERE usuario_id = :usuario_id
  AND cliente_id = :cliente_id
  AND is_revoked = 0;
"""

REVOKE_ALL_USER_TOKENS = """
UPDATE refresh_tokens
SET is_revoked = 1, revoked_at = GETDATE()
WHERE usuario_id = :usuario_id
  AND cliente_id = :cliente_id;
"""

DELETE_EXPIRED_TOKENS = """
DELETE FROM refresh_tokens
WHERE expires_at < GETDATE()
  AND is_revoked = 1;
"""

GET_ACTIVE_SESSIONS_BY_USER = """
SELECT 
    token_id, usuario_id, cliente_id, created_at, last_used_at,
    device_name, device_id, ip_address, client_type
FROM refresh_tokens
WHERE usuario_id = :usuario_id
  AND cliente_id = :cliente_id
  AND is_revoked = 0
  AND expires_at > GETDATE()
ORDER BY last_used_at DESC;
"""

GET_ALL_ACTIVE_SESSIONS = """
SELECT 
    token_id, usuario_id, cliente_id, created_at, last_used_at,
    device_name, device_id, ip_address, client_type
FROM refresh_tokens
WHERE cliente_id = :cliente_id
  AND is_revoked = 0
  AND expires_at > GETDATE()
ORDER BY last_used_at DESC;
"""

REVOKE_REFRESH_TOKEN_BY_ID = """
UPDATE refresh_tokens
SET is_revoked = 1, revoked_at = GETDATE()
OUTPUT INSERTED.token_id, INSERTED.is_revoked, INSERTED.usuario_id, INSERTED.cliente_id
WHERE token_id = :token_id;
"""

# ============================================
# QUERIES PARA AUDITORIA
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
VALUES (
    :cliente_id,
    :usuario_id,
    :evento,
    :nombre_usuario_intento,
    :descripcion,
    :exito,
    :codigo_error,
    :ip_address,
    :user_agent,
    :device_info,
    :geolocation,
    :metadata_json
);
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
    duracion_ms,
    fecha_sincronizacion
)
OUTPUT INSERTED.log_id, INSERTED.fecha_sincronizacion
VALUES (
    :cliente_origen_id,
    :cliente_destino_id,
    :usuario_id,
    :tipo_sincronizacion,
    :direccion,
    :operacion,
    :estado,
    :mensaje_error,
    :campos_sincronizados,
    :cambios_detectados,
    :hash_antes,
    :hash_despues,
    :usuario_ejecutor_id,
    :duracion_ms,
    GETDATE()
);
"""

# ============================================
# QUERIES PARA AREAS DE MENU
# ============================================

GET_AREAS_PAGINATED_QUERY = """
SELECT
    area_id, nombre, descripcion, icono, es_activo, fecha_creacion, cliente_id
FROM area_menu 
WHERE
    (cliente_id IS NULL OR cliente_id = :cliente_id)
    AND (:buscar IS NULL OR LOWER(nombre) LIKE LOWER(:buscar_pattern) OR LOWER(descripcion) LIKE LOWER(:buscar_pattern))
ORDER BY area_id ASC
OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY;
"""

COUNT_AREAS_QUERY = """
SELECT COUNT(*) as total_count
FROM area_menu 
WHERE
    (cliente_id IS NULL OR cliente_id = :cliente_id)
    AND (:buscar IS NULL OR LOWER(nombre) LIKE LOWER(:buscar_pattern) OR LOWER(descripcion) LIKE LOWER(:buscar_pattern));
"""

GET_AREA_BY_ID_QUERY = """
SELECT area_id, nombre, descripcion, icono, es_activo, fecha_creacion, cliente_id 
FROM area_menu 
WHERE area_id = :area_id AND (cliente_id IS NULL OR cliente_id = :cliente_id);
"""

CHECK_AREA_EXISTS_BY_NAME_QUERY = """
SELECT COUNT(*) as count 
FROM area_menu 
WHERE LOWER(nombre) = LOWER(:nombre) AND area_id != :area_id AND (cliente_id IS NULL OR cliente_id = :cliente_id);
"""

CREATE_AREA_QUERY = """
INSERT INTO area_menu (nombre, descripcion, icono, es_activo, cliente_id)
OUTPUT INSERTED.area_id, INSERTED.nombre, INSERTED.descripcion, INSERTED.icono, INSERTED.es_activo, 
       INSERTED.fecha_creacion, INSERTED.cliente_id
VALUES (:nombre, :descripcion, :icono, :es_activo, :cliente_id);
"""

UPDATE_AREA_BASE_QUERY_TEMPLATE = """
UPDATE area_menu 
SET {fields} 
OUTPUT INSERTED.* 
WHERE area_id = :area_id AND (cliente_id IS NULL OR cliente_id = :cliente_id);
"""

TOGGLE_AREA_STATUS_QUERY = """
UPDATE area_menu
SET es_activo = CASE WHEN es_activo = 1 THEN 0 ELSE 1 END
OUTPUT INSERTED.area_id, INSERTED.es_activo, INSERTED.cliente_id
WHERE area_id = :area_id AND (cliente_id IS NULL OR cliente_id = :cliente_id);
"""

GET_ACTIVE_AREAS_SIMPLE_LIST_QUERY = """
SELECT area_id, nombre, icono
FROM area_menu
WHERE es_activo = 1 AND (cliente_id IS NULL OR cliente_id = :cliente_id)
ORDER BY nombre ASC;
"""

# ============================================
# QUERIES PARA MENUS
# ============================================

GET_ALL_MENUS_ADMIN = "sp_GetAllMenuItemsAdmin"

INSERT_MENU = """
INSERT INTO menu (nombre, icono, ruta, padre_menu_id, orden, area_id, es_activo, cliente_id)
OUTPUT INSERTED.menu_id, INSERTED.nombre, INSERTED.icono, INSERTED.ruta,
       INSERTED.padre_menu_id, INSERTED.orden, INSERTED.es_activo, INSERTED.area_id,
       INSERTED.fecha_creacion, INSERTED.cliente_id
VALUES (:nombre, :icono, :ruta, :padre_menu_id, :orden, :area_id, :es_activo, :cliente_id);
"""

SELECT_MENU_BY_ID = """
SELECT m.menu_id, m.nombre, m.icono, m.ruta, m.padre_menu_id, m.orden,
       m.es_activo, m.fecha_creacion, m.area_id, m.cliente_id, a.nombre as area_nombre
FROM menu m
LEFT JOIN area_menu a ON m.area_id = a.area_id
WHERE m.menu_id = :menu_id AND (m.cliente_id IS NULL OR m.cliente_id = :cliente_id);
"""

UPDATE_MENU_TEMPLATE = """
UPDATE menu
SET
    nombre = COALESCE(:nombre, nombre),
    icono = COALESCE(:icono, icono),
    ruta = COALESCE(:ruta, ruta),
    padre_menu_id = COALESCE(:padre_menu_id, padre_menu_id),
    orden = COALESCE(:orden, orden),
    area_id = COALESCE(:area_id, area_id),
    es_activo = COALESCE(:es_activo, es_activo)
OUTPUT INSERTED.menu_id, INSERTED.nombre, INSERTED.icono, INSERTED.ruta,
       INSERTED.padre_menu_id, INSERTED.orden, INSERTED.es_activo, INSERTED.area_id,
       INSERTED.fecha_creacion, INSERTED.cliente_id
WHERE menu_id = :menu_id AND (cliente_id IS NULL OR cliente_id = :cliente_id);
"""

DEACTIVATE_MENU = """
UPDATE menu
SET es_activo = 0
OUTPUT INSERTED.menu_id, INSERTED.es_activo, INSERTED.cliente_id
WHERE menu_id = :menu_id AND es_activo = 1 AND (cliente_id IS NULL OR cliente_id = :cliente_id);
"""

REACTIVATE_MENU = """
UPDATE menu
SET es_activo = 1
OUTPUT INSERTED.menu_id, INSERTED.es_activo, INSERTED.cliente_id
WHERE menu_id = :menu_id AND es_activo = 0 AND (cliente_id IS NULL OR cliente_id = :cliente_id);
"""

CHECK_MENU_EXISTS = """
SELECT 1 FROM menu WHERE menu_id = :menu_id AND (cliente_id IS NULL OR cliente_id = :cliente_id);
"""

CHECK_AREA_EXISTS = """
SELECT 1 FROM area_menu WHERE area_id = :area_id;
"""

GET_MENUS_BY_AREA_FOR_TREE_QUERY = """
SELECT 
    m.menu_id, m.nombre, m.icono, m.ruta, m.padre_menu_id, m.orden,
    m.es_activo, m.area_id, m.cliente_id
FROM menu m
WHERE m.area_id = :area_id 
  AND (m.cliente_id IS NULL OR m.cliente_id = :cliente_id)
  AND m.es_activo = 1
ORDER BY m.orden ASC;
"""

GET_MAX_ORDEN_FOR_SIBLINGS = """
SELECT ISNULL(MAX(orden), 0) + 1 as next_orden
FROM menu
WHERE padre_menu_id = :padre_menu_id
  AND (cliente_id IS NULL OR cliente_id = :cliente_id);
"""

GET_MAX_ORDEN_FOR_ROOT = """
SELECT ISNULL(MAX(orden), 0) + 1 as next_orden
FROM menu
WHERE padre_menu_id IS NULL
  AND area_id = :area_id
  AND (cliente_id IS NULL OR cliente_id = :cliente_id);
"""

