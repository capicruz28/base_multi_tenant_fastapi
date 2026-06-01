-- ============================================================================
-- bootstrap_v2 | official bootstrap line (copy; do not edit logic here)
-- Source (legacy, immutable): (see BOOTSTRAP_MANIFEST.md)
-- Layer: catalog
-- ============================================================================
-- ============================================================================
-- SCRIPT: SEED permisos BI (Business Intelligence) - Fase 4
-- DESCRIPCIÓN:
--   - Completa el catálogo de permisos para el módulo BI según los recursos
--     usados por el backend: bi.reporte.*
--   - Seguro para múltiples ejecuciones (MERGE por codigo).
-- DEPENDENCIAS:
--   - SCRIPT_RBAC_TABLAS_CENTRAL.sql (tablas permiso y rol_permiso)
--   - 4.- SEED_MODULO_MENU_COMPLETO.sql (módulo BI ya creado)
-- NOTAS:
--   - modulo_id del módulo BI: E1000018-0000-4000-8000-000000000018
-- ============================================================================

DECLARE @modulo_bi_id UNIQUEIDENTIFIER = CAST('E1000018-0000-4000-8000-000000000018' AS UNIQUEIDENTIFIER);

-- --------------------------------------------------------------------------
-- BI - Reportes
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'bi.reporte.leer'       AS codigo, N'Leer reportes'       AS nombre, N'Listar y ver reportes BI'              AS descripcion, @modulo_bi_id AS modulo_id, 'reporte' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'bi.reporte.crear',                  N'Crear reportes',                  N'Crear reportes BI'                        , @modulo_bi_id              , 'reporte'            , 'crear'                  UNION ALL
    SELECT 'bi.reporte.actualizar',             N'Actualizar reportes',             N'Editar/activar/desactivar reportes BI'      , @modulo_bi_id              , 'reporte'            , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1)
WHEN MATCHED AND t.es_activo = 0 THEN
    UPDATE SET t.es_activo = 1, t.fecha_actualizacion = GETDATE();
GO

PRINT 'Seed permisos RBAC BI completado.';
GO

