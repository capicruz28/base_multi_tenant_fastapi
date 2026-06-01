-- ============================================================================
-- bootstrap_v2 | official bootstrap line (copy; do not edit logic here)
-- Source (legacy, immutable): (see BOOTSTRAP_MANIFEST.md)
-- Layer: catalog
-- ============================================================================
-- ============================================================================
-- SCRIPT: SEED permisos WMS (Warehouse Management System) - Fase 4+
-- DESCRIPCIÓN:
--   - Completa el catálogo de permisos para el módulo WMS según los recursos
--     usados por el backend: wms.zona.*, wms.ubicacion.*, wms.stock_ubicacion.*, wms.tarea.*
--   - Seguro para múltiples ejecuciones (MERGE por codigo).
-- DEPENDENCIAS:
--   - SCRIPT_RBAC_TABLAS_CENTRAL.sql (tabla permiso)
--   - 4.- SEED_MODULO_MENU_COMPLETO.sql (módulo WMS ya creado)
-- NOTAS:
--   - modulo_id corresponde al módulo WMS: E1000003-0000-4000-8000-000000000003
--   - Endpoints de workflow de tareas (asignar/iniciar/completar/cancelar) reutilizan wms.tarea.actualizar.
--   - Endpoints activar/desactivar (zonas/ubicaciones) reutilizan *.actualizar.
--   - Stock por ubicación (derivado) mantiene crear/actualizar por compatibilidad, pero puede ser uso interno.
-- ============================================================================

DECLARE @modulo_wms_id UNIQUEIDENTIFIER = CAST('E1000003-0000-4000-8000-000000000003' AS UNIQUEIDENTIFIER);

-- --------------------------------------------------------------------------
-- WMS - Zonas
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'wms.zona.leer'       AS codigo, N'Leer zonas de almacén'       AS nombre, N'Listar y ver zonas de almacén'            AS descripcion, @modulo_wms_id AS modulo_id, 'zona'            AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'wms.zona.crear',                  N'Crear zonas de almacén',                  N'Crear zonas de almacén'                         , @modulo_wms_id              , 'zona'            , 'crear'                  UNION ALL
    SELECT 'wms.zona.actualizar',             N'Actualizar zonas de almacén',             N'Editar / activar / desactivar zonas de almacén' , @modulo_wms_id              , 'zona'            , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1)
WHEN MATCHED AND t.es_activo = 0 THEN
    UPDATE SET t.es_activo = 1, t.fecha_actualizacion = GETDATE();
GO

-- --------------------------------------------------------------------------
-- WMS - Ubicaciones
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'wms.ubicacion.leer'       AS codigo, N'Leer ubicaciones'       AS nombre, N'Listar y ver ubicaciones'                 AS descripcion, @modulo_wms_id AS modulo_id, 'ubicacion'       AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'wms.ubicacion.crear',                  N'Crear ubicaciones',                  N'Crear ubicaciones'                             , @modulo_wms_id              , 'ubicacion'       , 'crear'                  UNION ALL
    SELECT 'wms.ubicacion.actualizar',             N'Actualizar ubicaciones',             N'Editar / activar / desactivar ubicaciones'      , @modulo_wms_id              , 'ubicacion'       , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1)
WHEN MATCHED AND t.es_activo = 0 THEN
    UPDATE SET t.es_activo = 1, t.fecha_actualizacion = GETDATE();
GO

-- --------------------------------------------------------------------------
-- WMS - Stock por ubicación
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'wms.stock_ubicacion.leer'       AS codigo, N'Leer stock por ubicación'       AS nombre, N'Listar y ver stock por ubicación'     AS descripcion, @modulo_wms_id AS modulo_id, 'stock_ubicacion' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'wms.stock_ubicacion.crear',                  N'Crear stock por ubicación',                  N'Crear stock por ubicación (uso interno)'  , @modulo_wms_id              , 'stock_ubicacion' , 'crear'                  UNION ALL
    SELECT 'wms.stock_ubicacion.actualizar',             N'Actualizar stock por ubicación',             N'Ajustar stock por ubicación (uso interno)' , @modulo_wms_id              , 'stock_ubicacion' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1)
WHEN MATCHED AND t.es_activo = 0 THEN
    UPDATE SET t.es_activo = 1, t.fecha_actualizacion = GETDATE();
GO

-- --------------------------------------------------------------------------
-- WMS - Tareas
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'wms.tarea.leer'       AS codigo, N'Leer tareas de almacén'       AS nombre, N'Listar y ver tareas de almacén'                     AS descripcion, @modulo_wms_id AS modulo_id, 'tarea' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'wms.tarea.crear',                  N'Crear tareas de almacén',                  N'Crear tareas de almacén'                              , @modulo_wms_id              , 'tarea' , 'crear'                  UNION ALL
    SELECT 'wms.tarea.actualizar',             N'Actualizar tareas de almacén',             N'Editar (borrador) y ejecutar workflow (asignar/iniciar/completar/cancelar)' , @modulo_wms_id              , 'tarea' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1)
WHEN MATCHED AND t.es_activo = 0 THEN
    UPDATE SET t.es_activo = 1, t.fecha_actualizacion = GETDATE();
GO

PRINT 'Seed permisos RBAC WMS completado.';
GO

