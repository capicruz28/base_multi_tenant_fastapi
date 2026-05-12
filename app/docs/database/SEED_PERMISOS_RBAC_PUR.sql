-- ============================================================================
-- SCRIPT: SEED permisos PUR (Compras) - Fase 4
-- DESCRIPCIÓN:
--   - Completa el catálogo de permisos para el módulo PUR según los recursos
--     usados por el backend: pur.proveedor.*, pur.contacto.*,
--     pur.producto_proveedor.*, pur.solicitud.*, pur.cotizacion.*,
--     pur.orden_compra.*, pur.recepcion.*
--   - No reemplaza SEED_PERMISOS_RBAC.sql general; se ejecuta como
--     complemento específico para PUR.
-- DEPENDENCIAS:
--   - SCRIPT_RBAC_TABLAS_CENTRAL.sql (tablas permiso y rol_permiso)
--   - SEED_MODULO_MENU_COMPLETO.sql (módulo PUR ya creado)
-- NOTAS:
--   - Usa MERGE por código para ser seguro ante múltiples ejecuciones.
--   - modulo_id corresponde al módulo PUR: E1000005-0000-4000-8000-000000000005
-- ============================================================================

DECLARE @modulo_pur_id UNIQUEIDENTIFIER = CAST('E1000005-0000-4000-8000-000000000005' AS UNIQUEIDENTIFIER);

-- --------------------------------------------------------------------------
-- PUR - Proveedores
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'pur.proveedor.leer'       AS codigo, 'Leer proveedores'        AS nombre, 'Listar y ver proveedores'                    AS descripcion, @modulo_pur_id AS modulo_id, 'proveedor'         AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'pur.proveedor.crear',                  'Crear proveedores',                  'Crear proveedores y datos fiscales'              , @modulo_pur_id          , 'proveedor'         , 'crear'                  UNION ALL
    SELECT 'pur.proveedor.actualizar',             'Actualizar proveedores',             'Editar proveedores'                             , @modulo_pur_id          , 'proveedor'         , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- PUR - Contactos de Proveedor
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'pur.contacto.leer'        AS codigo, 'Leer contactos de proveedor' AS nombre, 'Listar y ver contactos de proveedores' AS descripcion, @modulo_pur_id AS modulo_id, 'contacto'          AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'pur.contacto.crear',                   'Crear contactos',                   'Crear contactos de proveedores'                    , @modulo_pur_id          , 'contacto'          , 'crear'                  UNION ALL
    SELECT 'pur.contacto.actualizar',              'Actualizar contactos',              'Editar contactos de proveedores'                  , @modulo_pur_id          , 'contacto'          , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- PUR - Productos por Proveedor
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'pur.producto_proveedor.leer'   AS codigo, 'Leer productos por proveedor'   AS nombre, 'Listar y ver productos asociados a proveedores' AS descripcion, @modulo_pur_id AS modulo_id, 'producto_proveedor' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'pur.producto_proveedor.crear',            'Crear productos por proveedor',            'Asociar productos a proveedores'                        , @modulo_pur_id          , 'producto_proveedor' , 'crear'                  UNION ALL
    SELECT 'pur.producto_proveedor.actualizar',       'Actualizar productos por proveedor',       'Editar asociación producto-proveedor'                   , @modulo_pur_id          , 'producto_proveedor' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- PUR - Solicitudes de Compra
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'pur.solicitud.leer'      AS codigo, 'Leer solicitudes de compra' AS nombre, 'Listar y ver solicitudes de compra'     AS descripcion, @modulo_pur_id AS modulo_id, 'solicitud'         AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'pur.solicitud.crear',                 'Crear solicitudes',                 'Crear solicitudes de compra y detalle'            , @modulo_pur_id          , 'solicitud'         , 'crear'                  UNION ALL
    SELECT 'pur.solicitud.actualizar',             'Actualizar solicitudes',             'Editar solicitudes de compra'                     , @modulo_pur_id          , 'solicitud'         , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- PUR - Cotizaciones
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'pur.cotizacion.leer'     AS codigo, 'Leer cotizaciones'        AS nombre, 'Listar y ver cotizaciones y detalle'     AS descripcion, @modulo_pur_id AS modulo_id, 'cotizacion'        AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'pur.cotizacion.crear',                'Crear cotizaciones',                'Crear cotizaciones y líneas'                      , @modulo_pur_id          , 'cotizacion'        , 'crear'                  UNION ALL
    SELECT 'pur.cotizacion.actualizar',           'Actualizar cotizaciones',           'Editar cotizaciones y detalle'                    , @modulo_pur_id          , 'cotizacion'        , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- PUR - Órdenes de Compra
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'pur.orden_compra.leer'   AS codigo, 'Leer órdenes de compra'   AS nombre, 'Listar y ver órdenes de compra y detalle' AS descripcion, @modulo_pur_id AS modulo_id, 'orden_compra'      AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'pur.orden_compra.crear',              'Crear órdenes de compra',              'Crear órdenes de compra y líneas'                 , @modulo_pur_id          , 'orden_compra'      , 'crear'                  UNION ALL
    SELECT 'pur.orden_compra.actualizar',         'Actualizar órdenes de compra',         'Editar órdenes de compra y detalle'                , @modulo_pur_id          , 'orden_compra'      , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- PUR - Recepciones
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'pur.recepcion.leer'       AS codigo, 'Leer recepciones'         AS nombre, 'Listar y ver recepciones y detalle'       AS descripcion, @modulo_pur_id AS modulo_id, 'recepcion'          AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'pur.recepcion.crear',                 'Crear recepciones',                 'Crear recepciones y líneas'                        , @modulo_pur_id          , 'recepcion'          , 'crear'                  UNION ALL
    SELECT 'pur.recepcion.actualizar',            'Actualizar recepciones',            'Editar recepciones y detalle'                      , @modulo_pur_id          , 'recepcion'          , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

PRINT 'Seed permisos RBAC PUR (FASE 4) completado.';

-- Nota (Fase 3 API): rutas nuevas POST …/anular, …/emitir, …/reactivar, …/aceptar, …/rechazar, …/aprobar
-- reutilizan los mismos códigos pur.*.actualizar o pur.*.crear ya sembrados arriba; no se requieren permisos adicionales.
