-- ============================================================================
-- SCRIPT: Asignar permiso CORE 'core.app.acceder' a todos los roles activos
-- TABLAS: permiso, rol, rol_permiso
-- DESCRIPCIÓN:
--   - Asegura que TODOS los roles activos tengan asignado el permiso base
--     de acceso al ERP (core.app.acceder).
--   - Respeta el modelo RBAC existente: rol → rol_permiso → permiso.
-- DEPENDENCIAS:
--   - SCRIPT_RBAC_TABLAS_CENTRAL.sql
--   - SEED_PERMISOS_CORE.sql  (debe haber creado core.app.acceder en permiso)
-- USO:
--   - Seguro para múltiples ejecuciones (usa NOT EXISTS por combinación única).
--   - No modifica otras relaciones ni borra datos.
-- ============================================================================

DECLARE @permiso_core_id UNIQUEIDENTIFIER;

SELECT @permiso_core_id = p.permiso_id
FROM permiso p
WHERE p.codigo = 'core.app.acceder';

IF @permiso_core_id IS NULL
BEGIN
    PRINT 'WARN: Permiso core.app.acceder no encontrado en tabla permiso. Ejecute primero SEED_PERMISOS_CORE.sql.';
    RETURN;
END;

-- --------------------------------------------------------------------------
-- Parte 1: Roles con cliente_id (roles por tenant)
-- --------------------------------------------------------------------------
INSERT INTO rol_permiso (rol_permiso_id, cliente_id, rol_id, permiso_id)
SELECT
    NEWID()          AS rol_permiso_id,
    r.cliente_id     AS cliente_id,
    r.rol_id         AS rol_id,
    @permiso_core_id AS permiso_id
FROM rol r
WHERE r.es_activo = 1
  AND r.cliente_id IS NOT NULL
  AND NOT EXISTS (
        SELECT 1
        FROM rol_permiso rp
        WHERE rp.cliente_id = r.cliente_id
          AND rp.rol_id     = r.rol_id
          AND rp.permiso_id = @permiso_core_id
  );

-- --------------------------------------------------------------------------
-- Parte 2: Roles de sistema (cliente_id NULL) → asignar por cada cliente
-- --------------------------------------------------------------------------
INSERT INTO rol_permiso (rol_permiso_id, cliente_id, rol_id, permiso_id)
SELECT
    NEWID()          AS rol_permiso_id,
    c.cliente_id     AS cliente_id,
    r.rol_id         AS rol_id,
    @permiso_core_id AS permiso_id
FROM (SELECT cliente_id FROM cliente) c
CROSS JOIN rol r
WHERE r.es_activo = 1
  AND r.cliente_id IS NULL
  AND NOT EXISTS (
        SELECT 1
        FROM rol_permiso rp
        WHERE rp.cliente_id = c.cliente_id
          AND rp.rol_id     = r.rol_id
          AND rp.permiso_id = @permiso_core_id
  );

PRINT 'Seed rol_permiso: permiso CORE core.app.acceder asignado a roles activos.';
GO

