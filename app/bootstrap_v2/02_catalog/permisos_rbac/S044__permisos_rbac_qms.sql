-- ============================================================================
-- bootstrap_v2 | official bootstrap line (copy; do not edit logic here)
-- Source (legacy, immutable): (see BOOTSTRAP_MANIFEST.md)
-- Layer: catalog
-- ============================================================================
-- ============================================================================
-- SCRIPT: SEED permisos QMS (Control de Calidad) - Fase 4
-- DESCRIPCIÓN:
--   - Completa el catálogo de permisos para el módulo QMS según recursos
--     usados por el backend: qms.parametro_calidad.*, qms.plan_inspeccion.*,
--     qms.inspeccion.*, qms.no_conformidad.*
--   - Incluye acciones adicionales (activar/desactivar y transiciones).
--   - Seguro para múltiples ejecuciones (MERGE por codigo).
-- DEPENDENCIAS:
--   - SCRIPT_RBAC_TABLAS_CENTRAL.sql (tablas permiso y rol_permiso)
--   - 4.- SEED_MODULO_MENU_COMPLETO.sql (módulo QMS ya creado)
-- NOTAS:
--   - modulo_id corresponde al módulo QMS: E1000004-0000-4000-8000-000000000004
-- ============================================================================

DECLARE @modulo_qms_id UNIQUEIDENTIFIER = CAST('E1000004-0000-4000-8000-000000000004' AS UNIQUEIDENTIFIER);

-- --------------------------------------------------------------------------
-- QMS - Parámetros de Calidad
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'qms.parametro_calidad.leer'        AS codigo, N'Leer parámetros de calidad'        AS nombre, N'Listar y ver parámetros de calidad'                AS descripcion, @modulo_qms_id AS modulo_id, 'parametro_calidad' AS recurso, 'leer'        AS accion UNION ALL
    SELECT 'qms.parametro_calidad.crear',                   N'Crear parámetros de calidad',                   N'Crear parámetros de calidad'                               , @modulo_qms_id               , 'parametro_calidad'        , 'crear'                   UNION ALL
    SELECT 'qms.parametro_calidad.actualizar',              N'Actualizar parámetros de calidad',              N'Editar parámetros de calidad'                               , @modulo_qms_id               , 'parametro_calidad'        , 'actualizar'              UNION ALL
    SELECT 'qms.parametro_calidad.activar',                 N'Activar parámetros de calidad',                 N'Reactivar (lógica) parámetros de calidad'                    , @modulo_qms_id               , 'parametro_calidad'        , 'activar'                 UNION ALL
    SELECT 'qms.parametro_calidad.desactivar',              N'Desactivar parámetros de calidad',              N'Dar de baja (lógica) parámetros de calidad'                 , @modulo_qms_id               , 'parametro_calidad'        , 'desactivar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1)
WHEN MATCHED AND t.es_activo = 0 THEN
    UPDATE SET t.es_activo = 1, t.fecha_actualizacion = GETDATE();
GO

-- --------------------------------------------------------------------------
-- QMS - Planes de Inspección
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'qms.plan_inspeccion.leer'        AS codigo, N'Leer planes de inspección'        AS nombre, N'Listar y ver planes de inspección'                 AS descripcion, @modulo_qms_id AS modulo_id, 'plan_inspeccion' AS recurso, 'leer'        AS accion UNION ALL
    SELECT 'qms.plan_inspeccion.crear',                   N'Crear planes de inspección',                   N'Crear planes de inspección'                                , @modulo_qms_id               , 'plan_inspeccion'         , 'crear'                   UNION ALL
    SELECT 'qms.plan_inspeccion.actualizar',              N'Actualizar planes de inspección',              N'Editar planes de inspección y su detalle'                   , @modulo_qms_id               , 'plan_inspeccion'         , 'actualizar'              UNION ALL
    SELECT 'qms.plan_inspeccion.activar',                 N'Activar planes de inspección',                 N'Reactivar (lógica) planes de inspección'                    , @modulo_qms_id               , 'plan_inspeccion'         , 'activar'                 UNION ALL
    SELECT 'qms.plan_inspeccion.desactivar',              N'Desactivar planes de inspección',              N'Dar de baja (lógica) planes de inspección'                  , @modulo_qms_id               , 'plan_inspeccion'         , 'desactivar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1)
WHEN MATCHED AND t.es_activo = 0 THEN
    UPDATE SET t.es_activo = 1, t.fecha_actualizacion = GETDATE();
GO

-- --------------------------------------------------------------------------
-- QMS - Inspecciones (incluye transiciones)
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'qms.inspeccion.leer'        AS codigo, N'Leer inspecciones'        AS nombre, N'Listar y ver inspecciones y detalle'                  AS descripcion, @modulo_qms_id AS modulo_id, 'inspeccion' AS recurso, 'leer'        AS accion UNION ALL
    SELECT 'qms.inspeccion.crear',                   N'Crear inspecciones',                   N'Crear inspecciones (cabecera y detalle)'                   , @modulo_qms_id               , 'inspeccion'             , 'crear'                   UNION ALL
    SELECT 'qms.inspeccion.actualizar',              N'Actualizar inspecciones',              N'Editar inspecciones (solo en estado editable) y detalle'    , @modulo_qms_id               , 'inspeccion'             , 'actualizar'              UNION ALL
    SELECT 'qms.inspeccion.aprobar',                 N'Aprobar inspecciones',                 N'Aprobar inspecciones (setear aprobado_por y fecha)'         , @modulo_qms_id               , 'inspeccion'             , 'aprobar'                 UNION ALL
    SELECT 'qms.inspeccion.procesar',                N'Procesar inspecciones',                N'Procesar inspecciones aprobadas'                            , @modulo_qms_id               , 'inspeccion'             , 'procesar'                UNION ALL
    SELECT 'qms.inspeccion.anular',                  N'Anular inspecciones',                  N'Anular inspecciones (cuando aplique)'                       , @modulo_qms_id               , 'inspeccion'             , 'anular'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1)
WHEN MATCHED AND t.es_activo = 0 THEN
    UPDATE SET t.es_activo = 1, t.fecha_actualizacion = GETDATE();
GO

-- --------------------------------------------------------------------------
-- QMS - No Conformidades (incluye transiciones)
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'qms.no_conformidad.leer'        AS codigo, N'Leer no conformidades'        AS nombre, N'Listar y ver no conformidades'                         AS descripcion, @modulo_qms_id AS modulo_id, 'no_conformidad' AS recurso, 'leer'        AS accion UNION ALL
    SELECT 'qms.no_conformidad.crear',                   N'Crear no conformidades',                   N'Crear no conformidades'                                        , @modulo_qms_id               , 'no_conformidad'         , 'crear'                   UNION ALL
    SELECT 'qms.no_conformidad.actualizar',              N'Actualizar no conformidades',              N'Editar no conformidades (sin cierre/cancelación por PUT)'      , @modulo_qms_id               , 'no_conformidad'         , 'actualizar'              UNION ALL
    SELECT 'qms.no_conformidad.cerrar',                  N'Cerrar no conformidades',                  N'Cerrar no conformidades (setear cerrado_por y fecha_cierre)'   , @modulo_qms_id               , 'no_conformidad'         , 'cerrar'                  UNION ALL
    SELECT 'qms.no_conformidad.cancelar',                N'Cancelar no conformidades',                N'Cancelar no conformidades (setear cerrado_por y fecha_cierre)' , @modulo_qms_id               , 'no_conformidad'         , 'cancelar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1)
WHEN MATCHED AND t.es_activo = 0 THEN
    UPDATE SET t.es_activo = 1, t.fecha_actualizacion = GETDATE();
GO

PRINT 'Seed permisos RBAC QMS (FASE 4) completado.';
GO

