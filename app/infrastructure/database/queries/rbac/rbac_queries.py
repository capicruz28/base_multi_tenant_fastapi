"""
Queries SQL para RBAC (Roles y Permisos).

✅ FASE 2: Queries migradas desde sql_constants.py

QUERIES INCLUIDAS:
- SELECT_ROLES_PAGINATED
- COUNT_ROLES_PAGINATED
- SELECT_PERMISOS_POR_ROL
- DEACTIVATE_ROL
- REACTIVATE_ROL
- DELETE_PERMISOS_POR_ROL
- INSERT_PERMISO_ROL
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
SELECT COUNT(*) as total
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

__all__ = [
    "SELECT_ROLES_PAGINATED",
    "COUNT_ROLES_PAGINATED",
    "SELECT_PERMISOS_POR_ROL",
    "DEACTIVATE_ROL",
    "REACTIVATE_ROL",
    "DELETE_PERMISOS_POR_ROL",
    "INSERT_PERMISO_ROL",
]
