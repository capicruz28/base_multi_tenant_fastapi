-- ============================================================================
-- SCRIPT: SEED permisos MNT (Mantenimiento de Activos) - Fase 4
-- DESCRIPCIÓN:
--   - Completa el catálogo de permisos para el módulo MNT según recursos usados
--     por el backend:
--       mnt.activo.*, mnt.plan_mantenimiento.*,
--       mnt.orden_trabajo.*, mnt.historial_mantenimiento.*
--   - Incluye permisos legacy ya referenciados en routers existentes
--     (leer / crear / actualizar para las 4 entidades).
--   - Incluye acciones de activar/desactivar para maestros (activo, plan_mantenimiento).
--   - Incluye workflow de Órdenes de Trabajo:
--       programar / iniciar / pausar / reanudar / completar / cerrar / cancelar
-- NOTAS:
--   - Usa MERGE por codigo para ser idempotente (seguro ante múltiples ejecuciones).
--   - modulo_id corresponde al módulo MNT: E100000A-0000-4000-8000-00000000000A
--     (definido en 4.- SEED_MODULO_MENU_COMPLETO.sql)
--   - Los permisos legacy de mnt_historial_mantenimiento (crear/actualizar) se
--     conservan por compatibilidad aunque la tabla es bitácora derivada — la
--     operación de cierre transaccional las usa internamente desde el servicio.
-- DEPENDENCIAS:
--   - 5.- SCRIPT_RBAC_TABLAS_CENTRAL.sql (tabla permiso)
--   - 4.- SEED_MODULO_MENU_COMPLETO.sql (módulo MNT ya creado)
-- ============================================================================

DECLARE @modulo_mnt_id UNIQUEIDENTIFIER = CAST('E100000A-0000-4000-8000-00000000000A' AS UNIQUEIDENTIFIER);

-- --------------------------------------------------------------------------
-- MNT - Activos (maestro + activar/desactivar)
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'mnt.activo.leer'        AS codigo, 'Leer activos'        AS nombre, 'Listar y ver activos físicos (MNT)'                 AS descripcion, @modulo_mnt_id AS modulo_id, 'activo' AS recurso, 'leer'        AS accion UNION ALL
    SELECT 'mnt.activo.crear',                   'Crear activos',                   'Crear activos físicos (MNT)'                                 , @modulo_mnt_id               , 'activo' , 'crear'                  UNION ALL
    SELECT 'mnt.activo.actualizar',              'Actualizar activos',              'Editar activos físicos (MNT)'                                , @modulo_mnt_id               , 'activo' , 'actualizar'             UNION ALL
    SELECT 'mnt.activo.activar',                 'Activar activo',                  'Activar activo (alta lógica es_activo=1)'                    , @modulo_mnt_id               , 'activo' , 'activar'                UNION ALL
    SELECT 'mnt.activo.desactivar',              'Desactivar activo',               'Desactivar activo (baja lógica es_activo=0)'                 , @modulo_mnt_id               , 'activo' , 'desactivar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- MNT - Planes de Mantenimiento (maestro + activar/desactivar)
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'mnt.plan_mantenimiento.leer'        AS codigo, 'Leer planes de mantenimiento'        AS nombre, 'Listar y ver planes de mantenimiento (preventivo/predictivo)'   AS descripcion, @modulo_mnt_id AS modulo_id, 'plan_mantenimiento' AS recurso, 'leer'        AS accion UNION ALL
    SELECT 'mnt.plan_mantenimiento.crear',                   'Crear plan de mantenimiento',                   'Crear plan de mantenimiento por activo (MNT)'                            , @modulo_mnt_id               , 'plan_mantenimiento' , 'crear'                  UNION ALL
    SELECT 'mnt.plan_mantenimiento.actualizar',              'Actualizar plan de mantenimiento',              'Editar plan de mantenimiento (MNT)'                                       , @modulo_mnt_id               , 'plan_mantenimiento' , 'actualizar'             UNION ALL
    SELECT 'mnt.plan_mantenimiento.activar',                 'Activar plan de mantenimiento',                 'Activar plan (alta lógica es_activo=1)'                                   , @modulo_mnt_id               , 'plan_mantenimiento' , 'activar'                UNION ALL
    SELECT 'mnt.plan_mantenimiento.desactivar',              'Desactivar plan de mantenimiento',              'Desactivar plan (baja lógica es_activo=0)'                                , @modulo_mnt_id               , 'plan_mantenimiento' , 'desactivar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- MNT - Órdenes de Trabajo (transaccional + workflow)
--   Estados: solicitada -> programada -> en_proceso -> completada -> cerrada
--                                            ^   |
--                                            |   v
--                                          pausada
--   Transversal: cualquier estado salvo cerrada/cancelada -> cancelada
--   Cierre (completada -> cerrada) ejecuta una transacción atómica que actualiza
--   la OT, inserta en mnt_historial_mantenimiento y refresca fechas del plan.
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'mnt.orden_trabajo.leer'        AS codigo, 'Leer órdenes de trabajo'        AS nombre, 'Listar y ver órdenes de trabajo (OT) de mantenimiento'                AS descripcion, @modulo_mnt_id AS modulo_id, 'orden_trabajo' AS recurso, 'leer'        AS accion UNION ALL
    SELECT 'mnt.orden_trabajo.crear',                   'Crear orden de trabajo',                   'Crear OT (estado inicial: solicitada)'                                          , @modulo_mnt_id               , 'orden_trabajo' , 'crear'                  UNION ALL
    SELECT 'mnt.orden_trabajo.actualizar',              'Actualizar orden de trabajo',              'Editar OT (solo en estado solicitada o programada)'                              , @modulo_mnt_id               , 'orden_trabajo' , 'actualizar'             UNION ALL
    SELECT 'mnt.orden_trabajo.programar',               'Programar orden de trabajo',               'Transición OT: solicitada → programada'                                          , @modulo_mnt_id               , 'orden_trabajo' , 'programar'              UNION ALL
    SELECT 'mnt.orden_trabajo.iniciar',                 'Iniciar orden de trabajo',                 'Transición OT: programada → en_proceso (setea fecha_inicio_real)'                , @modulo_mnt_id               , 'orden_trabajo' , 'iniciar'                UNION ALL
    SELECT 'mnt.orden_trabajo.pausar',                  'Pausar orden de trabajo',                  'Transición OT: en_proceso → pausada'                                              , @modulo_mnt_id               , 'orden_trabajo' , 'pausar'                 UNION ALL
    SELECT 'mnt.orden_trabajo.reanudar',                'Reanudar orden de trabajo',                'Transición OT: pausada → en_proceso'                                              , @modulo_mnt_id               , 'orden_trabajo' , 'reanudar'               UNION ALL
    SELECT 'mnt.orden_trabajo.completar',               'Completar orden de trabajo',               'Transición OT: en_proceso → completada (setea fecha_fin_real)'                  , @modulo_mnt_id               , 'orden_trabajo' , 'completar'              UNION ALL
    SELECT 'mnt.orden_trabajo.cerrar',                  'Cerrar orden de trabajo',                  'Transición OT transaccional: completada → cerrada (genera historial y refresca plan)' , @modulo_mnt_id               , 'orden_trabajo' , 'cerrar'                 UNION ALL
    SELECT 'mnt.orden_trabajo.cancelar',                'Cancelar orden de trabajo',                'Transición OT: cualquier estado salvo cerrada/cancelada → cancelada'             , @modulo_mnt_id               , 'orden_trabajo' , 'cancelar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- MNT - Historial de Mantenimiento (bitácora derivada — solo lectura desde API)
--   Nota: las acciones 'crear' y 'actualizar' se conservan como permisos
--   legacy porque los endpoints existentes (POST/PUT) NO se eliminaron por
--   compatibilidad. Quedan referenciados por el código pero la ruta natural
--   de inserción es la transición transaccional 'cerrar OT'.
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'mnt.historial_mantenimiento.leer'        AS codigo, 'Leer historial de mantenimiento'        AS nombre, 'Listar y ver historial / bitácora de mantenimientos por activo' AS descripcion, @modulo_mnt_id AS modulo_id, 'historial_mantenimiento' AS recurso, 'leer'        AS accion UNION ALL
    SELECT 'mnt.historial_mantenimiento.crear',                   'Crear historial de mantenimiento (legacy)',     'Insertar entrada manual en historial (legacy; uso recomendado: transición cerrar OT)' , @modulo_mnt_id               , 'historial_mantenimiento' , 'crear'                  UNION ALL
    SELECT 'mnt.historial_mantenimiento.actualizar',              'Actualizar historial de mantenimiento (legacy)','Editar entrada de historial (legacy; bitácora normalmente inmutable)'                  , @modulo_mnt_id               , 'historial_mantenimiento' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

PRINT 'Seed permisos RBAC MNT (FASE 3) completado.';
