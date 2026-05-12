-- ============================================================================
-- SCRIPT: SEED permisos DMS (Gestión Documental) - Fase 4
-- DESCRIPCIÓN:
--   - Completa el catálogo de permisos para el módulo DMS según los recursos
--     usados por el backend: dms.documento.*
--   - Seguro para múltiples ejecuciones (MERGE por codigo).
-- DEPENDENCIAS:
--   - SCRIPT_RBAC_TABLAS_CENTRAL.sql (tablas permiso y rol_permiso)
--   - SEED_MODULO_MENU.SQL / SEED_MODULO_MENU_COMPLETO.sql (módulo DMS ya creado)
-- NOTAS:
--   - modulo_id corresponde al módulo DMS: E1000019-0000-4000-8000-000000000019
-- ============================================================================

DECLARE @modulo_dms_id UNIQUEIDENTIFIER = CAST('E1000019-0000-4000-8000-000000000019' AS UNIQUEIDENTIFIER);

-- --------------------------------------------------------------------------
-- DMS - Documentos
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'dms.documento.leer'       AS codigo, N'Leer documentos'       AS nombre, N'Listar y ver documentos'                      AS descripcion, @modulo_dms_id AS modulo_id, 'documento' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'dms.documento.crear',                  N'Crear documentos',                  N'Crear documentos y metadatos'                         , @modulo_dms_id              , 'documento'          , 'crear'                  UNION ALL
    SELECT 'dms.documento.actualizar',             N'Actualizar documentos',             N'Editar metadatos y transiciones (archivar/restaurar)'   , @modulo_dms_id              , 'documento'          , 'actualizar'             UNION ALL
    SELECT 'dms.documento.eliminar',               N'Eliminar documentos',               N'Eliminación lógica (estado = eliminado)'                , @modulo_dms_id              , 'documento'          , 'eliminar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1)
WHEN MATCHED AND t.es_activo = 0 THEN
    UPDATE SET t.es_activo = 1, t.fecha_actualizacion = GETDATE();
GO

PRINT 'Seed permisos RBAC DMS completado.';
GO

