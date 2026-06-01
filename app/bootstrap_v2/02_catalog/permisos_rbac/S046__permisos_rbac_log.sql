-- ============================================================================
-- bootstrap_v2 | official bootstrap line (copy; do not edit logic here)
-- Source (legacy, immutable): (see BOOTSTRAP_MANIFEST.md)
-- Layer: catalog
-- ============================================================================
-- ============================================================================
-- SCRIPT: SEED permisos LOG (Logística y Distribución) - Fase 4
-- DESCRIPCIÓN:
--   - Inserta/asegura el catálogo de permisos RBAC para el módulo LOG
--     según los recursos usados por el backend:
--       log.transportista.*, log.vehiculo.*, log.ruta.*,
--       log.guia_remision.*, log.guia_remision_detalle.*,
--       log.despacho.*, log.despacho_guia.*
-- NOTAS:
--   - Usa MERGE por codigo para ser idempotente.
--   - modulo_id LOG: E1000006-0000-4000-8000-000000000006
-- DEPENDENCIAS:
--   - Tablas RBAC (permiso, rol_permiso) ya creadas.
--   - Módulo LOG ya creado en catálogo de módulos/menús.
-- ============================================================================

DECLARE @modulo_log_id UNIQUEIDENTIFIER = CAST('E1000006-0000-4000-8000-000000000006' AS UNIQUEIDENTIFIER);

-- --------------------------------------------------------------------------
-- LOG - Transportistas
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'log.transportista.leer'       AS codigo, 'Leer transportistas'       AS nombre, 'Listar y ver transportistas'                          AS descripcion, @modulo_log_id AS modulo_id, 'transportista' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'log.transportista.crear',                  'Crear transportistas',                  'Crear transportistas (catálogo)'                         , @modulo_log_id          , 'transportista' , 'crear'                  UNION ALL
    SELECT 'log.transportista.actualizar',             'Actualizar transportistas',             'Editar transportistas (catálogo)'                         , @modulo_log_id          , 'transportista' , 'actualizar'             UNION ALL
    SELECT 'log.transportista.eliminar',               'Eliminar transportistas',               'Dar de baja lógica transportistas (es_activo = 0)'        , @modulo_log_id          , 'transportista' , 'eliminar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- LOG - Vehículos
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'log.vehiculo.leer'       AS codigo, 'Leer vehículos'        AS nombre, 'Listar y ver vehículos'                             AS descripcion, @modulo_log_id AS modulo_id, 'vehiculo' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'log.vehiculo.crear',                  'Crear vehículos',                  'Crear vehículos (flota)'                              , @modulo_log_id          , 'vehiculo' , 'crear'                  UNION ALL
    SELECT 'log.vehiculo.actualizar',             'Actualizar vehículos',             'Editar vehículos (flota)'                              , @modulo_log_id          , 'vehiculo' , 'actualizar'             UNION ALL
    SELECT 'log.vehiculo.eliminar',               'Eliminar vehículos',               'Dar de baja lógica vehículos (es_activo = 0)'         , @modulo_log_id          , 'vehiculo' , 'eliminar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- LOG - Rutas
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'log.ruta.leer'       AS codigo, 'Leer rutas'        AS nombre, 'Listar y ver rutas de distribución'                        AS descripcion, @modulo_log_id AS modulo_id, 'ruta' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'log.ruta.crear',                  'Crear rutas',                  'Crear rutas de distribución'                             , @modulo_log_id          , 'ruta' , 'crear'                  UNION ALL
    SELECT 'log.ruta.actualizar',             'Actualizar rutas',             'Editar rutas de distribución'                             , @modulo_log_id          , 'ruta' , 'actualizar'             UNION ALL
    SELECT 'log.ruta.eliminar',               'Eliminar rutas',               'Dar de baja lógica rutas (es_activo = 0)'                , @modulo_log_id          , 'ruta' , 'eliminar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- LOG - Guías de Remisión
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'log.guia_remision.leer'       AS codigo, 'Leer guías de remisión'        AS nombre, 'Listar y ver guías de remisión'             AS descripcion, @modulo_log_id AS modulo_id, 'guia_remision' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'log.guia_remision.crear',                  'Crear guías de remisión',                  'Crear guías de remisión (cabecera)'               , @modulo_log_id          , 'guia_remision' , 'crear'                  UNION ALL
    SELECT 'log.guia_remision.actualizar',             'Actualizar guías de remisión',             'Editar/anular guías de remisión según estado'     , @modulo_log_id          , 'guia_remision' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- LOG - Detalles de Guía (sub-recurso)
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'log.guia_remision_detalle.leer'       AS codigo, 'Leer detalles de guía de remisión'       AS nombre, 'Listar y ver líneas de guía de remisión' AS descripcion, @modulo_log_id AS modulo_id, 'guia_remision_detalle' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'log.guia_remision_detalle.crear',                  'Crear detalle de guía de remisión',                  'Añadir líneas a guía de remisión'                    , @modulo_log_id          , 'guia_remision_detalle' , 'crear'                  UNION ALL
    SELECT 'log.guia_remision_detalle.actualizar',             'Actualizar detalle de guía de remisión',             'Editar líneas de guía de remisión'                    , @modulo_log_id          , 'guia_remision_detalle' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- LOG - Despachos
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'log.despacho.leer'       AS codigo, 'Leer despachos'        AS nombre, 'Listar y ver despachos'                                AS descripcion, @modulo_log_id AS modulo_id, 'despacho' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'log.despacho.crear',                  'Crear despachos',                  'Crear despachos (planificación)'                         , @modulo_log_id          , 'despacho' , 'crear'                  UNION ALL
    SELECT 'log.despacho.actualizar',             'Actualizar despachos',             'Editar/completar/anular despachos según estado'           , @modulo_log_id          , 'despacho' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- LOG - Despacho-Guía (sub-recurso)
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'log.despacho_guia.leer'       AS codigo, 'Leer despacho-guía'        AS nombre, 'Listar y ver relaciones despacho-guía'       AS descripcion, @modulo_log_id AS modulo_id, 'despacho_guia' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'log.despacho_guia.crear',                  'Crear despacho-guía',                  'Asignar guías a despacho'                          , @modulo_log_id          , 'despacho_guia' , 'crear'                  UNION ALL
    SELECT 'log.despacho_guia.actualizar',             'Actualizar despacho-guía',             'Editar relación despacho-guía'                      , @modulo_log_id          , 'despacho_guia' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

PRINT 'Seed permisos RBAC LOG completado.';

