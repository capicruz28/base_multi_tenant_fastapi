"""
Queries SQL para menús y áreas de menú.

✅ FASE 2: Queries migradas desde sql_constants.py

QUERIES INCLUIDAS:
- GET_AREAS_PAGINATED_QUERY
- COUNT_AREAS_QUERY
- GET_AREA_BY_ID_QUERY
- CHECK_AREA_EXISTS_BY_NAME_QUERY
- CREATE_AREA_QUERY
- UPDATE_AREA_BASE_QUERY_TEMPLATE
- TOGGLE_AREA_STATUS_QUERY
- GET_ACTIVE_AREAS_SIMPLE_LIST_QUERY
- INSERT_MENU
- SELECT_MENU_BY_ID
- UPDATE_MENU_TEMPLATE
- DEACTIVATE_MENU
- REACTIVATE_MENU
- CHECK_MENU_EXISTS
- GET_MENUS_BY_AREA_FOR_TREE_QUERY
- GET_MAX_ORDEN_FOR_SIBLINGS
- GET_MAX_ORDEN_FOR_ROOT
- GET_ALL_MENUS_ADMIN
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

__all__ = [
    "GET_AREAS_PAGINATED_QUERY",
    "COUNT_AREAS_QUERY",
    "GET_AREA_BY_ID_QUERY",
    "CHECK_AREA_EXISTS_BY_NAME_QUERY",
    "CREATE_AREA_QUERY",
    "UPDATE_AREA_BASE_QUERY_TEMPLATE",
    "TOGGLE_AREA_STATUS_QUERY",
    "GET_ACTIVE_AREAS_SIMPLE_LIST_QUERY",
    "INSERT_MENU",
    "SELECT_MENU_BY_ID",
    "UPDATE_MENU_TEMPLATE",
    "DEACTIVATE_MENU",
    "REACTIVATE_MENU",
    "CHECK_MENU_EXISTS",
    "CHECK_AREA_EXISTS",
    "GET_MENUS_BY_AREA_FOR_TREE_QUERY",
    "GET_MAX_ORDEN_FOR_SIBLINGS",
    "GET_MAX_ORDEN_FOR_ROOT",
    "GET_ALL_MENUS_ADMIN",
]
