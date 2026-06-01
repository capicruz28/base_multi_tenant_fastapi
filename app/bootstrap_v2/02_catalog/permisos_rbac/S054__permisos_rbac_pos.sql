-- ============================================================================
-- bootstrap_v2 | official bootstrap line (copy; do not edit logic here)
-- Source (legacy, immutable): (see BOOTSTRAP_MANIFEST.md)
-- Layer: catalog
-- ============================================================================
-- ============================================================================
-- SCRIPT: SEED permisos POS (Punto de Venta)
-- DESCRIPCIÓN:
--   Inserta/asegura el catálogo de permisos RBAC para el módulo POS según el backend.
-- NOTAS:
--   - MERGE por codigo (idempotente).
--   - modulo_id POS: E100000F-0000-4000-8000-00000000000F
-- DEPENDENCIAS:
--   - Tabla permiso y módulo POS en catálogo.
-- ============================================================================

DECLARE @modulo_pos_id UNIQUEIDENTIFIER = CAST('E100000F-0000-4000-8000-00000000000F' AS UNIQUEIDENTIFIER);

-- --------------------------------------------------------------------------
-- POS - Punto de venta (maestro)
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'pos.punto_venta.leer'         AS codigo, 'Leer puntos de venta'         AS nombre, 'Listar y ver terminales/cajas POS'                    AS descripcion, @modulo_pos_id AS modulo_id, 'punto_venta' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'pos.punto_venta.crear',                    'Crear puntos de venta',                    'Crear terminales/cajas POS'                             , @modulo_pos_id          , 'punto_venta' , 'crear'                  UNION ALL
    SELECT 'pos.punto_venta.actualizar',              'Actualizar puntos de venta',              'Editar terminales/cajas POS'                             , @modulo_pos_id          , 'punto_venta' , 'actualizar'             UNION ALL
    SELECT 'pos.punto_venta.eliminar',               'Eliminar puntos de venta',               'Baja lógica de puntos de venta (es_activo = 0)'      , @modulo_pos_id          , 'punto_venta' , 'eliminar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- POS - Turno de caja
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'pos.turno_caja.leer'         AS codigo, 'Leer turnos de caja'         AS nombre, 'Listar y ver aperturas/cierres de caja'              AS descripcion, @modulo_pos_id AS modulo_id, 'turno_caja' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'pos.turno_caja.crear',                    'Crear turnos de caja',                    'Abrir turno de caja'                                   , @modulo_pos_id          , 'turno_caja' , 'crear'                  UNION ALL
    SELECT 'pos.turno_caja.actualizar',              'Actualizar turnos de caja',              'Editar turno abierto (sin totales de sistema)'           , @modulo_pos_id          , 'turno_caja' , 'actualizar'             UNION ALL
    SELECT 'pos.turno_caja.cerrar',                   'Cerrar turnos de caja',                   'Cerrar turno y recalcular totales desde ventas'        , @modulo_pos_id          , 'turno_caja' , 'cerrar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- POS - Venta
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'pos.venta.leer'         AS codigo, 'Leer ventas POS'         AS nombre, 'Listar y ver ventas de mostrador'                         AS descripcion, @modulo_pos_id AS modulo_id, 'venta' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'pos.venta.crear',                    'Crear ventas POS',                    'Registrar ventas POS'                                      , @modulo_pos_id          , 'venta' , 'crear'                  UNION ALL
    SELECT 'pos.venta.actualizar',              'Actualizar ventas POS',              'Editar venta en borrador o pendiente'                      , @modulo_pos_id          , 'venta' , 'actualizar'             UNION ALL
    SELECT 'pos.venta.anular',                  'Anular ventas POS',                  'Anular venta POS con motivo'                               , @modulo_pos_id          , 'venta' , 'anular'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- POS - Detalle de venta
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'pos.venta_detalle.leer'         AS codigo, 'Leer detalle venta POS'         AS nombre, 'Listar y ver líneas de venta POS'            AS descripcion, @modulo_pos_id AS modulo_id, 'venta_detalle' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'pos.venta_detalle.crear',                    'Crear detalle venta POS',                    'Agregar líneas a venta POS'                 , @modulo_pos_id          , 'venta_detalle' , 'crear'                  UNION ALL
    SELECT 'pos.venta_detalle.actualizar',               'Actualizar detalle venta POS',               'Editar líneas (cabecera editable)'            , @modulo_pos_id          , 'venta_detalle' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO
