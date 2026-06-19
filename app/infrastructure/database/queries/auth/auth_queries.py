"""
Queries SQL para autenticación y gestión de usuarios.

✅ FASE 2: Queries migradas desde sql_constants.py

QUERIES INCLUIDAS:
- GET_USER_MAX_ACCESS_LEVEL
- IS_USER_SUPER_ADMIN
- GET_USER_ACCESS_LEVEL_INFO_COMPLETE

Refresh tokens: usar refresh_token_queries_core (SQLAlchemy Core).

TODAS LAS QUERIES USAN:
- Parámetros nombrados (:param) para seguridad
- text().bindparams() para ejecución
- Filtros de tenant automáticos
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
  AND (ur.empresa_id IS NULL OR ur.empresa_id = :empresa_id)
"""

__all__ = [
    "GET_USER_MAX_ACCESS_LEVEL",
    "IS_USER_SUPER_ADMIN",
    "GET_USER_ACCESS_LEVEL_INFO_COMPLETE",
]
