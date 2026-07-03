-- ============================================================================
-- bootstrap_v2 | official bootstrap line (copy; do not edit logic here)
-- Source (legacy, immutable): (see BOOTSTRAP_MANIFEST.md)
-- Layer: catalog
-- ============================================================================
-- ============================================================================
-- SCRIPT: SEED permisos CORE base del sistema (tabla permiso)
-- DESCRIPCIÓN: Inserta permisos globales transversales (core.app.acceder,
--              tenant.branding.leer) en la BD central / Dedicated S6.
-- DEPENDENCIAS: Ejecutar después de SCRIPT_RBAC_TABLAS_CENTRAL.sql
--               y SEED_MODULO_MENU_COMPLETO.sql (tabla modulo).
-- COHERENCIA: modulo_id debe corresponder al módulo ORG (es_core = 1).
-- USO: Seguro para múltiples ejecuciones (MERGE por codigo).
-- ============================================================================

MERGE INTO permiso AS t
USING (
    SELECT
        'core.app.acceder'                                                AS codigo,
        N'Acceder a la aplicación'                                       AS nombre,
        N'Permite iniciar sesión y acceder al sistema ERP'              AS descripcion,
        CAST(NULL AS UNIQUEIDENTIFIER)                                   AS modulo_id,
        'app'                                                            AS recurso,
        'acceder'                                                        AS accion
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1)
WHEN MATCHED AND t.es_activo = 0 THEN
    UPDATE SET t.es_activo = 1, t.fecha_actualizacion = GETDATE();
GO

PRINT 'Seed permiso CORE (core.app.acceder) completado.';
GO

MERGE INTO permiso AS t
USING (
    SELECT
        'tenant.branding.leer'                                            AS codigo,
        N'Leer branding'                                                 AS nombre,
        N'Obtiene la configuración de branding del cliente (tenant) actual.' AS descripcion,
        CAST(NULL AS UNIQUEIDENTIFIER)                                   AS modulo_id,
        'branding'                                                       AS recurso,
        'leer'                                                           AS accion
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1)
WHEN MATCHED AND t.es_activo = 0 THEN
    UPDATE SET t.es_activo = 1, t.fecha_actualizacion = GETDATE();
GO

PRINT 'Seed permiso CORE (tenant.branding.leer) completado.';
GO

