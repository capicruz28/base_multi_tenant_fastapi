-- ============================================================================
-- bootstrap_v2 | official bootstrap line (copy; do not edit logic here)
-- Source (legacy, immutable): (see BOOTSTRAP_MANIFEST.md)
-- Layer: catalog
-- ============================================================================
-- ============================================================================
-- SCRIPT: SEED permisos MFG (Producción y Manufactura) - Fase 4
-- DESCRIPCIÓN:
--   - Completa el catálogo de permisos para el módulo MFG según recursos usados
--     por el backend:
--       mfg.centro_trabajo.*, mfg.operacion.*, mfg.lista_materiales.*,
--       mfg.lista_materiales_detalle.*, mfg.ruta_fabricacion.*,
--       mfg.ruta_fabricacion_detalle.*, mfg.orden_produccion.*,
--       mfg.orden_produccion_operacion.*, mfg.consumo_material.*
--   - Incluye acciones de workflow y de activación/desactivación.
-- NOTAS:
--   - Usa MERGE por codigo para ser idempotente (seguro ante múltiples ejecuciones).
--   - modulo_id corresponde al módulo MFG: E1000007-0000-4000-8000-000000000007
-- DEPENDENCIAS:
--   - 5.- SCRIPT_RBAC_TABLAS_CENTRAL.sql (tabla permiso)
--   - 4.- SEED_MODULO_MENU_COMPLETO.sql (módulo MFG ya creado)
-- ============================================================================

DECLARE @modulo_mfg_id UNIQUEIDENTIFIER = CAST('E1000007-0000-4000-8000-000000000007' AS UNIQUEIDENTIFIER);

-- --------------------------------------------------------------------------
-- MFG - Centros de Trabajo (maestro + activar/desactivar)
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'mfg.centro_trabajo.leer'        AS codigo, 'Leer centros de trabajo'        AS nombre, 'Listar y ver centros de trabajo (MFG)'                 AS descripcion, @modulo_mfg_id AS modulo_id, 'centro_trabajo' AS recurso, 'leer'        AS accion UNION ALL
    SELECT 'mfg.centro_trabajo.crear',                   'Crear centros de trabajo',                   'Crear centros de trabajo (MFG)'                                 , @modulo_mfg_id               , 'centro_trabajo' , 'crear'                  UNION ALL
    SELECT 'mfg.centro_trabajo.actualizar',              'Actualizar centros de trabajo',              'Editar centros de trabajo (MFG)'                                , @modulo_mfg_id               , 'centro_trabajo' , 'actualizar'             UNION ALL
    SELECT 'mfg.centro_trabajo.activar',                 'Activar centro de trabajo',                 'Activar centro de trabajo (baja lógica es_activo=1)'             , @modulo_mfg_id               , 'centro_trabajo' , 'activar'                UNION ALL
    SELECT 'mfg.centro_trabajo.desactivar',              'Desactivar centro de trabajo',              'Desactivar centro de trabajo (baja lógica es_activo=0)'          , @modulo_mfg_id               , 'centro_trabajo' , 'desactivar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- MFG - Operaciones (maestro + activar/desactivar)
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'mfg.operacion.leer'        AS codigo, 'Leer operaciones'        AS nombre, 'Listar y ver operaciones (MFG)'                    AS descripcion, @modulo_mfg_id AS modulo_id, 'operacion' AS recurso, 'leer'        AS accion UNION ALL
    SELECT 'mfg.operacion.crear',                   'Crear operaciones',                   'Crear operaciones (MFG)'                            , @modulo_mfg_id               , 'operacion' , 'crear'                  UNION ALL
    SELECT 'mfg.operacion.actualizar',              'Actualizar operaciones',              'Editar operaciones (MFG)'                           , @modulo_mfg_id               , 'operacion' , 'actualizar'             UNION ALL
    SELECT 'mfg.operacion.activar',                 'Activar operación',                  'Activar operación (baja lógica es_activo=1)'        , @modulo_mfg_id               , 'operacion' , 'activar'                UNION ALL
    SELECT 'mfg.operacion.desactivar',              'Desactivar operación',               'Desactivar operación (baja lógica es_activo=0)'     , @modulo_mfg_id               , 'operacion' , 'desactivar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- MFG - Listas de Materiales (BOM) (workflow)
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'mfg.lista_materiales.leer'        AS codigo, 'Leer BOM'        AS nombre, 'Listar y ver listas de materiales (BOM)'                         AS descripcion, @modulo_mfg_id AS modulo_id, 'lista_materiales' AS recurso, 'leer'        AS accion UNION ALL
    SELECT 'mfg.lista_materiales.crear',                   'Crear BOM',                   'Crear listas de materiales (BOM) (estado borrador)'                   , @modulo_mfg_id               , 'lista_materiales' , 'crear'                  UNION ALL
    SELECT 'mfg.lista_materiales.actualizar',              'Actualizar BOM',              'Editar listas de materiales (BOM) (solo borrador)'                     , @modulo_mfg_id               , 'lista_materiales' , 'actualizar'             UNION ALL
    SELECT 'mfg.lista_materiales.aprobar',                 'Aprobar BOM',                 'Aprobar BOM (borrador → aprobada)'                                     , @modulo_mfg_id               , 'lista_materiales' , 'aprobar'                UNION ALL
    SELECT 'mfg.lista_materiales.anular',                  'Anular BOM',                  'Anular BOM (borrador/aprobada → obsoleta)'                              , @modulo_mfg_id               , 'lista_materiales' , 'anular'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- MFG - BOM Detalle (edición solo cuando BOM está en borrador)
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'mfg.lista_materiales_detalle.leer'        AS codigo, 'Leer detalle BOM'        AS nombre, 'Listar y ver detalle de BOM'                              AS descripcion, @modulo_mfg_id AS modulo_id, 'lista_materiales_detalle' AS recurso, 'leer'        AS accion UNION ALL
    SELECT 'mfg.lista_materiales_detalle.crear',                   'Crear detalle BOM',                   'Crear líneas de detalle BOM (solo borrador)'                      , @modulo_mfg_id               , 'lista_materiales_detalle' , 'crear'                  UNION ALL
    SELECT 'mfg.lista_materiales_detalle.actualizar',              'Actualizar detalle BOM',              'Editar líneas de detalle BOM (solo borrador)'                     , @modulo_mfg_id               , 'lista_materiales_detalle' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- MFG - Rutas de Fabricación (workflow)
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'mfg.ruta_fabricacion.leer'        AS codigo, 'Leer rutas de fabricación'        AS nombre, 'Listar y ver rutas de fabricación'                         AS descripcion, @modulo_mfg_id AS modulo_id, 'ruta_fabricacion' AS recurso, 'leer'        AS accion UNION ALL
    SELECT 'mfg.ruta_fabricacion.crear',                   'Crear ruta de fabricación',                   'Crear rutas de fabricación (estado borrador)'                        , @modulo_mfg_id               , 'ruta_fabricacion' , 'crear'                  UNION ALL
    SELECT 'mfg.ruta_fabricacion.actualizar',              'Actualizar ruta de fabricación',              'Editar rutas de fabricación (solo borrador)'                          , @modulo_mfg_id               , 'ruta_fabricacion' , 'actualizar'             UNION ALL
    SELECT 'mfg.ruta_fabricacion.aprobar',                 'Aprobar ruta de fabricación',                 'Aprobar ruta (borrador → aprobada)'                                  , @modulo_mfg_id               , 'ruta_fabricacion' , 'aprobar'                UNION ALL
    SELECT 'mfg.ruta_fabricacion.anular',                  'Anular ruta de fabricación',                  'Anular ruta (borrador/aprobada → obsoleta)'                           , @modulo_mfg_id               , 'ruta_fabricacion' , 'anular'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- MFG - Ruta Fabricación Detalle (edición solo cuando ruta está en borrador)
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'mfg.ruta_fabricacion_detalle.leer'        AS codigo, 'Leer detalle ruta fabricación'        AS nombre, 'Listar y ver detalle de ruta de fabricación'               AS descripcion, @modulo_mfg_id AS modulo_id, 'ruta_fabricacion_detalle' AS recurso, 'leer'        AS accion UNION ALL
    SELECT 'mfg.ruta_fabricacion_detalle.crear',                   'Crear detalle ruta fabricación',                   'Crear operaciones de ruta (solo borrador)'                           , @modulo_mfg_id               , 'ruta_fabricacion_detalle' , 'crear'                  UNION ALL
    SELECT 'mfg.ruta_fabricacion_detalle.actualizar',              'Actualizar detalle ruta fabricación',              'Editar operaciones de ruta (solo borrador)'                          , @modulo_mfg_id               , 'ruta_fabricacion_detalle' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- MFG - Órdenes de Producción (workflow)
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'mfg.orden_produccion.leer'        AS codigo, 'Leer órdenes de producción'        AS nombre, 'Listar y ver órdenes de producción (OP)'                         AS descripcion, @modulo_mfg_id AS modulo_id, 'orden_produccion' AS recurso, 'leer'        AS accion UNION ALL
    SELECT 'mfg.orden_produccion.crear',                   'Crear orden de producción',                   'Crear OP (estado borrador)'                                                , @modulo_mfg_id               , 'orden_produccion' , 'crear'                  UNION ALL
    SELECT 'mfg.orden_produccion.actualizar',              'Actualizar orden de producción',              'Editar OP (solo borrador)'                                                 , @modulo_mfg_id               , 'orden_produccion' , 'actualizar'             UNION ALL
    SELECT 'mfg.orden_produccion.liberar',                 'Liberar orden de producción',                 'Liberar OP (borrador → liberada)'                                          , @modulo_mfg_id               , 'orden_produccion' , 'liberar'                UNION ALL
    SELECT 'mfg.orden_produccion.iniciar',                 'Iniciar orden de producción',                 'Iniciar OP (liberada/pausada → en_proceso)'                                 , @modulo_mfg_id               , 'orden_produccion' , 'iniciar'                UNION ALL
    SELECT 'mfg.orden_produccion.finalizar',               'Finalizar orden de producción',               'Finalizar OP (en_proceso/pausada → completada)'                              , @modulo_mfg_id               , 'orden_produccion' , 'finalizar'              UNION ALL
    SELECT 'mfg.orden_produccion.cerrar',                  'Cerrar orden de producción',                  'Cerrar OP (completada → cerrada)'                                          , @modulo_mfg_id               , 'orden_produccion' , 'cerrar'                 UNION ALL
    SELECT 'mfg.orden_produccion.anular',                  'Anular orden de producción',                  'Anular OP (borrador/liberada → anulada)'                                   , @modulo_mfg_id               , 'orden_produccion' , 'anular'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- MFG - OP Operaciones (seguimiento; edición solo cuando OP está en borrador)
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'mfg.orden_produccion_operacion.leer'        AS codigo, 'Leer operaciones de OP'        AS nombre, 'Listar y ver operaciones asociadas a una OP'                 AS descripcion, @modulo_mfg_id AS modulo_id, 'orden_produccion_operacion' AS recurso, 'leer'        AS accion UNION ALL
    SELECT 'mfg.orden_produccion_operacion.crear',                   'Crear operación de OP',                   'Crear operación asociada a una OP (solo borrador)'                 , @modulo_mfg_id               , 'orden_produccion_operacion' , 'crear'                  UNION ALL
    SELECT 'mfg.orden_produccion_operacion.actualizar',              'Actualizar operación de OP',              'Editar operación asociada a una OP (solo borrador)'                , @modulo_mfg_id               , 'orden_produccion_operacion' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- MFG - Consumo de Materiales (edición solo cuando OP está en borrador)
-- Nota: el recurso se llama "consumo_material" en RBAC del router.
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'mfg.consumo_material.leer'        AS codigo, 'Leer consumo de materiales'        AS nombre, 'Listar y ver consumos de materiales por OP'                      AS descripcion, @modulo_mfg_id AS modulo_id, 'consumo_material' AS recurso, 'leer'        AS accion UNION ALL
    SELECT 'mfg.consumo_material.crear',                   'Crear consumo de materiales',                   'Registrar consumo de materiales en producción (solo borrador)'            , @modulo_mfg_id               , 'consumo_material' , 'crear'                  UNION ALL
    SELECT 'mfg.consumo_material.actualizar',              'Actualizar consumo de materiales',              'Editar consumo de materiales (solo borrador)'                              , @modulo_mfg_id               , 'consumo_material' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

PRINT 'Seed permisos RBAC MFG (FASE 4) completado.';

