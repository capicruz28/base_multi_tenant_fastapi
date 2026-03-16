-- ============================================================================
-- SCRIPT: Asignar TODOS los permisos al rol "Administrador" por cliente
-- DESCRIPCIÓN: Para que el rol Administrador tenga acceso total (todos los
--              permisos de negocio activos en permiso) al usar require_permission.
-- DEPENDENCIAS: SCRIPT_RBAC_TABLAS_CENTRAL.sql + SEED_PERMISOS_RBAC.sql (27 módulos).
-- USO: Ejecutar después de SEED_PERMISOS_RBAC.sql. Idempotente (evita duplicados).
-- NOTA:
--   - Parte 1: Roles "Administrador" con cliente_id IS NOT NULL (un rol por tenant).
--   - Parte 2: Rol "Administrador" de SISTEMA (cliente_id IS NULL): inserta una fila
--     por cada (cliente_id, rol_id, permiso_id) usando todos los cliente de tabla cliente,
--     para que el GET /roles/{rol_id}/permisos-negocio/ devuelva los permisos cuando
--     el admin del tenant abre el modal (rol_permiso se filtra por cliente_id del usuario).
-- ============================================================================

-- Parte 1: Asignar cada permiso activo a cada rol activo 'Administrador' con cliente_id (rol por tenant)
INSERT INTO rol_permiso (rol_permiso_id, cliente_id, rol_id, permiso_id)
SELECT
    NEWID(),
    r.cliente_id,
    r.rol_id,
    p.permiso_id
FROM rol r
CROSS JOIN permiso p
WHERE r.nombre = N'Administrador'
  AND r.es_activo = 1
  AND r.cliente_id IS NOT NULL
  AND p.es_activo = 1
  AND NOT EXISTS (
      SELECT 1
      FROM rol_permiso rp
      WHERE rp.cliente_id = r.cliente_id
        AND rp.rol_id = r.rol_id
        AND rp.permiso_id = p.permiso_id
  );

-- Parte 2: Rol "Administrador" de SISTEMA (cliente_id NULL): asignar todos los permisos POR CADA CLIENTE
-- así el admin de cada tenant ve los checkboxes marcados al abrir "Permisos de negocio" para ese rol.
INSERT INTO rol_permiso (rol_permiso_id, cliente_id, rol_id, permiso_id)
SELECT
    NEWID(),
    c.cliente_id,
    r.rol_id,
    p.permiso_id
FROM (SELECT cliente_id FROM cliente) c
CROSS JOIN rol r
CROSS JOIN permiso p
WHERE r.nombre = N'Administrador'
  AND r.es_activo = 1
  AND r.cliente_id IS NULL
  AND p.es_activo = 1
  AND NOT EXISTS (
      SELECT 1
      FROM rol_permiso rp
      WHERE rp.cliente_id = c.cliente_id
        AND rp.rol_id = r.rol_id
        AND rp.permiso_id = p.permiso_id
  );

PRINT 'Seed rol_permiso para Administrador (por-tenant y sistema) completado.';
GO
