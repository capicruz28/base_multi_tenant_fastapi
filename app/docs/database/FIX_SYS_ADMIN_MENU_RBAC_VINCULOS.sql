-- ============================================================================
-- SCRIPT: Vincular menús SYS_ADMIN a permisos RBAC (admin.tenant.access / admin.platform.access)
-- BD: CENTRAL (SQL Server)
-- Idempotente: seguro ejecutar varias veces.
-- NO crea permisos nuevos; solo relaciones faltantes.
-- ============================================================================
-- Causa: GET /auth/menu filtra por cliente_modulo (módulo contratado) y opcionalmente
--        por permiso; los ítems de modulo_menu no tenían permiso_codigo_requerido.
-- Acción:
--   A) Vincular menús TENANT_ADMIN → admin.tenant.access
--   B) Vincular menús SUPER_ADMIN → admin.platform.access
--   C) Asegurar que el módulo SYS_ADMIN esté en cliente_modulo para todos los clientes
--      (sin esto el JOIN en el backend no devuelve los menús).
-- ============================================================================

SET NOCOUNT ON;
GO

-- ----------------------------------------------------------------------------
-- 0. Asegurar que la columna permiso_codigo_requerido existe en modulo_menu
-- ----------------------------------------------------------------------------
IF NOT EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('modulo_menu') AND name = 'permiso_codigo_requerido'
)
BEGIN
    ALTER TABLE modulo_menu
    ADD permiso_codigo_requerido NVARCHAR(100) NULL;
    PRINT 'Columna modulo_menu.permiso_codigo_requerido creada.';
END;
GO

-- ----------------------------------------------------------------------------
-- 1. Vincular menús de la sección TENANT_ADMIN con admin.tenant.access
-- ----------------------------------------------------------------------------
UPDATE m
SET
    m.permiso_codigo_requerido = N'admin.tenant.access',
    m.fecha_actualizacion = GETDATE()
FROM modulo_menu m
INNER JOIN modulo_seccion ms ON m.seccion_id = ms.seccion_id
INNER JOIN modulo mod ON ms.modulo_id = mod.modulo_id
WHERE mod.codigo = N'SYS_ADMIN'
  AND ms.codigo = N'TENANT_ADMIN'
  AND (m.permiso_codigo_requerido IS NULL OR LTRIM(RTRIM(m.permiso_codigo_requerido)) = N'');

PRINT 'Menús TENANT_ADMIN vinculados a admin.tenant.access.';
GO

-- ----------------------------------------------------------------------------
-- 2. Vincular menús de la sección SUPER_ADMIN con admin.platform.access
-- ----------------------------------------------------------------------------
UPDATE m
SET
    m.permiso_codigo_requerido = N'admin.platform.access',
    m.fecha_actualizacion = GETDATE()
FROM modulo_menu m
INNER JOIN modulo_seccion ms ON m.seccion_id = ms.seccion_id
INNER JOIN modulo mod ON ms.modulo_id = mod.modulo_id
WHERE mod.codigo = N'SYS_ADMIN'
  AND ms.codigo = N'SUPER_ADMIN'
  AND (m.permiso_codigo_requerido IS NULL OR LTRIM(RTRIM(m.permiso_codigo_requerido)) = N'');

PRINT 'Menús SUPER_ADMIN vinculados a admin.platform.access.';
GO

-- ----------------------------------------------------------------------------
-- 3. Activar módulo SYS_ADMIN para todos los clientes (relación cliente_modulo)
--    Sin esto, el backend no incluye SYS_ADMIN en la query de menú (JOIN con cliente_modulo).
-- ----------------------------------------------------------------------------
DECLARE @modulo_sys_admin_id UNIQUEIDENTIFIER;

SELECT @modulo_sys_admin_id = modulo_id
FROM modulo
WHERE codigo = N'SYS_ADMIN';

IF @modulo_sys_admin_id IS NOT NULL
BEGIN
    INSERT INTO cliente_modulo (
        cliente_modulo_id,
        cliente_id,
        modulo_id,
        esta_activo,
        fecha_activacion
    )
    SELECT
        NEWID(),
        c.cliente_id,
        @modulo_sys_admin_id,
        1,
        GETDATE()
    FROM cliente c
    WHERE c.es_activo = 1
      AND NOT EXISTS (
          SELECT 1
          FROM cliente_modulo cm
          WHERE cm.cliente_id = c.cliente_id
            AND cm.modulo_id = @modulo_sys_admin_id
      );

    IF @@ROWCOUNT > 0
        PRINT 'Módulo SYS_ADMIN activado para clientes que no lo tenían.';
    ELSE
        PRINT 'Módulo SYS_ADMIN ya estaba activado para todos los clientes activos.';
END
ELSE
    PRINT 'WARN: Módulo SYS_ADMIN no encontrado. Ejecute antes SEED_ADMIN_MENU.sql.';
GO

PRINT 'Fix SYS_ADMIN menú RBAC vínculos completado.';
