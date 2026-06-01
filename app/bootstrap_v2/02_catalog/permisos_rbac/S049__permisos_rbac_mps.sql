-- ============================================================================
-- bootstrap_v2 | official bootstrap line (copy; do not edit logic here)
-- Source (legacy, immutable): (see BOOTSTRAP_MANIFEST.md)
-- Layer: catalog
-- ============================================================================
-- ============================================================================
-- SCRIPT: SEED permisos MPS (Plan Maestro de Producción) - Fase 4
-- DESCRIPCIÓN:
--   - Completa el catálogo de permisos para el módulo MPS según recursos usados
--     por el backend: mps.pronostico_demanda.*, mps.plan_produccion.*,
--     mps.plan_produccion_detalle.*
--   - Incluye acciones transaccionales nuevas del flujo:
--       plan_produccion: aprobar, ejecutar, cerrar, anular
-- NOTAS:
--   - Usa MERGE por codigo para ser idempotente (seguro ante múltiples ejecuciones).
--   - modulo_id corresponde al módulo MPS: E1000009-0000-4000-8000-000000000009
-- DEPENDENCIAS:
--   - SCRIPT_RBAC_TABLAS_CENTRAL.sql (tabla permiso)
--   - SEED_MODULO_MENU.SQL (módulo MPS ya creado)
-- ============================================================================

DECLARE @modulo_mps_id UNIQUEIDENTIFIER = CAST('E1000009-0000-4000-8000-000000000009' AS UNIQUEIDENTIFIER);

-- --------------------------------------------------------------------------
-- MPS - Pronóstico Demanda
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'mps.pronostico_demanda.leer'       AS codigo, 'Leer pronóstico demanda MPS'       AS nombre, 'Listar y ver pronósticos de demanda (MPS)'                AS descripcion, @modulo_mps_id AS modulo_id, 'pronostico_demanda' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'mps.pronostico_demanda.crear',                  'Crear pronóstico demanda MPS',                  'Crear pronósticos de demanda para planificación'                   , @modulo_mps_id               , 'pronostico_demanda' , 'crear'                  UNION ALL
    SELECT 'mps.pronostico_demanda.actualizar',             'Actualizar pronóstico demanda MPS',             'Editar pronósticos de demanda'                                     , @modulo_mps_id               , 'pronostico_demanda' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- MPS - Plan de Producción (workflow)
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'mps.plan_produccion.leer'       AS codigo, 'Leer plan producción MPS'       AS nombre, 'Listar y ver planes de producción (MPS)'                       AS descripcion, @modulo_mps_id AS modulo_id, 'plan_produccion' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'mps.plan_produccion.crear',                  'Crear plan producción MPS',                  'Crear planes de producción (estado borrador)'                       , @modulo_mps_id               , 'plan_produccion' , 'crear'                  UNION ALL
    SELECT 'mps.plan_produccion.actualizar',             'Actualizar plan producción MPS',             'Editar planes de producción (solo borrador)'                         , @modulo_mps_id               , 'plan_produccion' , 'actualizar'             UNION ALL
    SELECT 'mps.plan_produccion.aprobar',                'Aprobar plan producción MPS',                'Aprobar plan de producción (borrador → aprobado)'                    , @modulo_mps_id               , 'plan_produccion' , 'aprobar'                UNION ALL
    SELECT 'mps.plan_produccion.ejecutar',               'Ejecutar plan producción MPS',               'Ejecutar plan de producción (aprobado → ejecutado)'                  , @modulo_mps_id               , 'plan_produccion' , 'ejecutar'               UNION ALL
    SELECT 'mps.plan_produccion.cerrar',                 'Cerrar plan producción MPS',                 'Cerrar plan de producción (ejecutado → cerrado)'                     , @modulo_mps_id               , 'plan_produccion' , 'cerrar'                 UNION ALL
    SELECT 'mps.plan_produccion.anular',                 'Anular plan producción MPS',                 'Anular plan de producción (según reglas de transición)'              , @modulo_mps_id               , 'plan_produccion' , 'anular'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- MPS - Plan de Producción Detalle
-- Nota: el detalle se edita solo cuando el plan está en borrador (en backend).
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'mps.plan_produccion_detalle.leer'       AS codigo, 'Leer detalle plan producción MPS'       AS nombre, 'Listar y ver detalles del plan de producción (MPS)'             AS descripcion, @modulo_mps_id AS modulo_id, 'plan_produccion_detalle' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'mps.plan_produccion_detalle.crear',                  'Crear detalle plan producción MPS',                  'Crear líneas del detalle del plan de producción (solo borrador)'         , @modulo_mps_id               , 'plan_produccion_detalle' , 'crear'                  UNION ALL
    SELECT 'mps.plan_produccion_detalle.actualizar',             'Actualizar detalle plan producción MPS',             'Editar líneas del detalle del plan de producción (solo borrador)'        , @modulo_mps_id               , 'plan_produccion_detalle' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

PRINT 'Seed permisos RBAC MPS (FASE 4) completado.';

