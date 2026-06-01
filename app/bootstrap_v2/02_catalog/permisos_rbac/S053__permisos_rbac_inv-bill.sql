-- ============================================================================
-- bootstrap_v2 | official bootstrap line (copy; do not edit logic here)
-- Source (legacy, immutable): (see BOOTSTRAP_MANIFEST.md)
-- Layer: catalog
-- ============================================================================
-- ============================================================================
-- SCRIPT: SEED permisos RBAC INV_BILL (Facturación electrónica)
-- DESCRIPCIÓN:
--   - Catálogo de permisos alineado con los endpoints FastAPI:
--     inv_bill.serie.*, inv_bill.comprobante.*, inv_bill.comprobante_detalle.*
--   - Seguro para múltiples ejecuciones (MERGE por codigo).
-- DEPENDENCIAS:
--   - SCRIPT_RBAC_TABLAS_CENTRAL.sql (tablas permiso y rol_permiso)
--   - SEED_MODULO_MENU.SQL / SEED_MODULO_MENU_COMPLETO*.sql (módulo INV_BILL)
-- NOTAS:
--   - modulo_id del módulo INV_BILL: E100000E-0000-4000-8000-00000000000E
--   - El código de permiso usa guión bajo inv_bill (igual que MODULE_CODE en routers).
-- ============================================================================

DECLARE @modulo_inv_bill_id UNIQUEIDENTIFIER = CAST('E100000E-0000-4000-8000-00000000000E' AS UNIQUEIDENTIFIER);

-- --------------------------------------------------------------------------
-- INV_BILL - Series de comprobantes
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'inv_bill.serie.leer'       AS codigo, N'Leer series de comprobantes'     AS nombre, N'Listar y ver series de comprobantes'              AS descripcion, @modulo_inv_bill_id AS modulo_id, 'serie' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'inv_bill.serie.crear',                  N'Crear series',                    N'Crear series de comprobantes'                         , @modulo_inv_bill_id              , 'serie' , 'crear'                  UNION ALL
    SELECT 'inv_bill.serie.actualizar',             N'Actualizar series',               N'Editar series de comprobantes'                        , @modulo_inv_bill_id              , 'serie' , 'actualizar'             UNION ALL
    SELECT 'inv_bill.serie.activar',                N'Activar series',                  N'Reactivar series (es_activo = 1)'                     , @modulo_inv_bill_id              , 'serie' , 'activar'                UNION ALL
    SELECT 'inv_bill.serie.desactivar',             N'Desactivar series',               N'Baja lógica de series (es_activo = 0)'                , @modulo_inv_bill_id              , 'serie' , 'desactivar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1)
WHEN MATCHED AND t.es_activo = 0 THEN
    UPDATE SET t.es_activo = 1, t.fecha_actualizacion = GETDATE();
GO

-- --------------------------------------------------------------------------
-- INV_BILL - Comprobantes
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'inv_bill.comprobante.leer'       AS codigo, N'Leer comprobantes'       AS nombre, N'Listar y ver comprobantes'                    AS descripcion, @modulo_inv_bill_id AS modulo_id, 'comprobante' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'inv_bill.comprobante.crear',                  N'Crear comprobantes',                 N'Crear comprobantes'                          , @modulo_inv_bill_id              , 'comprobante' , 'crear'                  UNION ALL
    SELECT 'inv_bill.comprobante.actualizar',             N'Actualizar comprobantes',            N'Editar comprobantes en borrador'             , @modulo_inv_bill_id              , 'comprobante' , 'actualizar'             UNION ALL
    SELECT 'inv_bill.comprobante.anular',                 N'Anular comprobantes',                N'Anular comprobantes (motivo obligatorio)'     , @modulo_inv_bill_id              , 'comprobante' , 'anular'                 UNION ALL
    SELECT 'inv_bill.comprobante.procesar',               N'Procesar comprobantes',              N'Borrador → emitido (emisión interna)'       , @modulo_inv_bill_id              , 'comprobante' , 'procesar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1)
WHEN MATCHED AND t.es_activo = 0 THEN
    UPDATE SET t.es_activo = 1, t.fecha_actualizacion = GETDATE();
GO

-- --------------------------------------------------------------------------
-- INV_BILL - Detalle de comprobante (líneas)
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'inv_bill.comprobante_detalle.leer'       AS codigo, N'Leer detalle de comprobantes' AS nombre, N'Listar y ver líneas de comprobante' AS descripcion, @modulo_inv_bill_id AS modulo_id, 'comprobante_detalle' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'inv_bill.comprobante_detalle.crear',                  N'Crear líneas de comprobante',                 N'Agregar ítems al comprobante'           , @modulo_inv_bill_id              , 'comprobante_detalle' , 'crear'                  UNION ALL
    SELECT 'inv_bill.comprobante_detalle.actualizar',             N'Actualizar líneas de comprobante',            N'Editar ítems del comprobante'           , @modulo_inv_bill_id              , 'comprobante_detalle' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1)
WHEN MATCHED AND t.es_activo = 0 THEN
    UPDATE SET t.es_activo = 1, t.fecha_actualizacion = GETDATE();
GO

PRINT 'Seed permisos RBAC INV_BILL completado.';
GO
