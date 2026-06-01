-- ============================================================================
-- bootstrap_v2 | official bootstrap line (copy; do not edit logic here)
-- Source (legacy, immutable): (see BOOTSTRAP_MANIFEST.md)
-- Layer: catalog
-- ============================================================================
-- ============================================================================
-- SCRIPT: SEED permisos MRP (Planeamiento de Materiales) - Fase 4
-- DESCRIPCIÓN:
--   - Completa el catálogo de permisos para el módulo MRP según recursos usados
--     por el backend: mrp.plan_maestro.*, mrp.necesidad_bruta.*,
--     mrp.explosion_materiales.*, mrp.orden_sugerida.*
--   - Incluye acciones transaccionales nuevas del flujo:
--       plan_maestro: calcular, aprobar, ejecutar, cerrar, anular
--       orden_sugerida: aprobar, rechazar, convertir
-- NOTAS:
--   - Usa MERGE por codigo para ser idempotente (seguro ante múltiples ejecuciones).
--   - modulo_id corresponde al módulo MRP: E1000008-0000-4000-8000-000000000008
-- DEPENDENCIAS:
--   - SCRIPT_RBAC_TABLAS_CENTRAL.sql (tablas permiso y rol_permiso)
--   - SEED_MODULO_MENU_COMPLETO.sql (módulo MRP ya creado)
-- ============================================================================

DECLARE @modulo_mrp_id UNIQUEIDENTIFIER = CAST('E1000008-0000-4000-8000-000000000008' AS UNIQUEIDENTIFIER);

-- --------------------------------------------------------------------------
-- MRP - Plan Maestro
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'mrp.plan_maestro.leer'      AS codigo, 'Leer plan maestro MRP'      AS nombre, 'Listar y ver planes maestro MRP'                         AS descripcion, @modulo_mrp_id AS modulo_id, 'plan_maestro' AS recurso, 'leer'      AS accion UNION ALL
    SELECT 'mrp.plan_maestro.crear',                 'Crear plan maestro MRP',                 'Crear planes maestro MRP (borrador/inicial)'                 , @modulo_mrp_id               , 'plan_maestro' , 'crear'                  UNION ALL
    SELECT 'mrp.plan_maestro.actualizar',            'Actualizar plan maestro MRP',            'Editar planes maestro MRP (solo borrador/inicial)'            , @modulo_mrp_id               , 'plan_maestro' , 'actualizar'             UNION ALL
    SELECT 'mrp.plan_maestro.calcular',              'Calcular plan maestro MRP',              'Ejecutar cálculo MRP y marcar plan como calculado'            , @modulo_mrp_id               , 'plan_maestro' , 'calcular'               UNION ALL
    SELECT 'mrp.plan_maestro.aprobar',               'Aprobar plan maestro MRP',               'Aprobar plan maestro MRP (posterior a cálculo)'               , @modulo_mrp_id               , 'plan_maestro' , 'aprobar'                UNION ALL
    SELECT 'mrp.plan_maestro.ejecutar',              'Ejecutar plan maestro MRP',              'Ejecutar plan maestro MRP (posterior a aprobación)'           , @modulo_mrp_id               , 'plan_maestro' , 'ejecutar'               UNION ALL
    SELECT 'mrp.plan_maestro.cerrar',                'Cerrar plan maestro MRP',                'Cerrar plan maestro MRP (posterior a ejecución)'              , @modulo_mrp_id               , 'plan_maestro' , 'cerrar'                 UNION ALL
    SELECT 'mrp.plan_maestro.anular',                'Anular plan maestro MRP',                'Anular plan maestro MRP (según reglas de transición)'         , @modulo_mrp_id               , 'plan_maestro' , 'anular'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- MRP - Necesidades Brutas (sin workflow adicional)
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'mrp.necesidad_bruta.leer'      AS codigo, 'Leer necesidades brutas'      AS nombre, 'Listar y ver necesidades brutas'          AS descripcion, @modulo_mrp_id AS modulo_id, 'necesidad_bruta' AS recurso, 'leer'      AS accion UNION ALL
    SELECT 'mrp.necesidad_bruta.crear',                 'Crear necesidades brutas',                 'Crear necesidades brutas (entrada al MRP)'       , @modulo_mrp_id               , 'necesidad_bruta' , 'crear'                  UNION ALL
    SELECT 'mrp.necesidad_bruta.actualizar',            'Actualizar necesidades brutas',            'Editar necesidades brutas'                       , @modulo_mrp_id               , 'necesidad_bruta' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- MRP - Explosión de Materiales (derivada; lectura)
-- Nota: se mantienen permisos crear/actualizar por compatibilidad de endpoints,
-- pero el backend restringe escritura a procesos controlados.
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'mrp.explosion_materiales.leer'      AS codigo, 'Leer explosión de materiales'      AS nombre, 'Listar y ver explosión de materiales' AS descripcion, @modulo_mrp_id AS modulo_id, 'explosion_materiales' AS recurso, 'leer'      AS accion UNION ALL
    SELECT 'mrp.explosion_materiales.crear',                 'Crear explosión de materiales',                 'Crear explosión (solo procesos internos)'     , @modulo_mrp_id               , 'explosion_materiales' , 'crear'                  UNION ALL
    SELECT 'mrp.explosion_materiales.actualizar',            'Actualizar explosión de materiales',            'Actualizar explosión (solo procesos internos)' , @modulo_mrp_id              , 'explosion_materiales' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- MRP - Órdenes Sugeridas (workflow controlado)
-- Nota: se mantiene permiso actualizar por compatibilidad de endpoint PUT (edición limitada).
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'mrp.orden_sugerida.leer'       AS codigo, 'Leer órdenes sugeridas'       AS nombre, 'Listar y ver órdenes sugeridas'                    AS descripcion, @modulo_mrp_id AS modulo_id, 'orden_sugerida' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'mrp.orden_sugerida.crear',                  'Crear órdenes sugeridas',                  'Crear órdenes sugeridas (solo procesos internos)'          , @modulo_mrp_id               , 'orden_sugerida' , 'crear'                  UNION ALL
    SELECT 'mrp.orden_sugerida.actualizar',             'Actualizar órdenes sugeridas',             'Editar órdenes sugeridas (edición limitada en sugerida)'    , @modulo_mrp_id               , 'orden_sugerida' , 'actualizar'             UNION ALL
    SELECT 'mrp.orden_sugerida.aprobar',                'Aprobar orden sugerida',                  'Aprobar una orden sugerida (sugerida → aprobada)'           , @modulo_mrp_id               , 'orden_sugerida' , 'aprobar'                UNION ALL
    SELECT 'mrp.orden_sugerida.rechazar',               'Rechazar orden sugerida',                 'Rechazar una orden sugerida (→ rechazada)'                  , @modulo_mrp_id               , 'orden_sugerida' , 'rechazar'               UNION ALL
    SELECT 'mrp.orden_sugerida.convertir',              'Convertir orden sugerida',                'Convertir orden sugerida a documento real (→ convertida)'   , @modulo_mrp_id               , 'orden_sugerida' , 'convertir'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

PRINT 'Seed permisos RBAC MRP (FASE 4) completado.';

