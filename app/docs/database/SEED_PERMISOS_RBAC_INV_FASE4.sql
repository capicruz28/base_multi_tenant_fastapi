-- ============================================================================
-- SCRIPT: SEED permisos INV (Inventarios) - FASE 4
-- DESCRIPCIÓN:
--   - Completa el catálogo de permisos para el módulo INV
--     según los recursos usados por el backend:
--       inv.categoria.*, inv.unidad_medida.*, inv.producto.*,
--       inv.almacen.*, inv.stock.*, inv.tipo_movimiento.*,
--       inv.movimiento.*, inv.inventario_fisico.*
--   - No reemplaza SEED_PERMISOS_RBAC.sql general; se ejecuta como
--     complemento específico para INV.
-- DEPENDENCIAS:
--   - SCRIPT_RBAC_TABLAS_CENTRAL.sql (tablas permiso y rol_permiso)
--   - SEED_MODULO_MENU_COMPLETO.sql (módulo INV ya creado)
-- NOTAS:
--   - Usa MERGE por código para ser seguro ante múltiples ejecuciones.
--   - modulo_id corresponde al módulo INV:
--       'E1000002-0000-4000-8000-000000000002'
-- ============================================================================

DECLARE @modulo_inv_id UNIQUEIDENTIFIER = CAST('E1000002-0000-4000-8000-000000000002' AS UNIQUEIDENTIFIER);

-- --------------------------------------------------------------------------
-- INV - Categorías
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'inv.categoria.leer'      AS codigo, 'Leer categorías'       AS nombre, 'Listar y ver categorías de productos'           AS descripcion, @modulo_inv_id AS modulo_id, 'categoria'        AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'inv.categoria.crear',                 'Crear categorías',                 'Crear categorías de productos'                         , @modulo_inv_id          , 'categoria'        , 'crear'                  UNION ALL
    SELECT 'inv.categoria.actualizar',            'Actualizar categorías',            'Editar categorías de productos'                         , @modulo_inv_id          , 'categoria'        , 'actualizar'             UNION ALL
    SELECT 'inv.categoria.eliminar',              'Eliminar categorías',              'Dar de baja lógica categorías de productos'              , @modulo_inv_id          , 'categoria'        , 'eliminar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- INV - Unidades de Medida
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'inv.unidad_medida.leer'  AS codigo, 'Leer unidades de medida' AS nombre, 'Listar y ver unidades de medida de inventario' AS descripcion, @modulo_inv_id AS modulo_id, 'unidad_medida'    AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'inv.unidad_medida.crear',              'Crear unidades de medida',              'Crear unidades de medida y conversiones'            , @modulo_inv_id          , 'unidad_medida'    , 'crear'                  UNION ALL
    SELECT 'inv.unidad_medida.actualizar',         'Actualizar unidades de medida',         'Editar unidades de medida y conversiones'           , @modulo_inv_id          , 'unidad_medida'    , 'actualizar'             UNION ALL
    SELECT 'inv.unidad_medida.eliminar',           'Eliminar unidades de medida',           'Dar de baja lógica unidades de medida'               , @modulo_inv_id          , 'unidad_medida'    , 'eliminar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- INV - Productos (complementa permisos base ya existentes)
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'inv.producto.leer'       AS codigo, 'Leer productos'        AS nombre, 'Listar y ver productos, categorías y stock'     AS descripcion, @modulo_inv_id AS modulo_id, 'producto'         AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'inv.producto.crear',                  'Crear productos',                  'Crear productos y categorías asociadas'              , @modulo_inv_id          , 'producto'         , 'crear'                  UNION ALL
    SELECT 'inv.producto.actualizar',             'Actualizar productos',             'Editar productos e inventario asociado'              , @modulo_inv_id          , 'producto'         , 'actualizar'             UNION ALL
    SELECT 'inv.producto.eliminar',               'Eliminar productos',               'Dar de baja lógica productos'                        , @modulo_inv_id          , 'producto'         , 'eliminar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- INV - Almacenes
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'inv.almacen.leer'        AS codigo, 'Leer almacenes'        AS nombre, 'Listar y ver almacenes físicos y virtuales'     AS descripcion, @modulo_inv_id AS modulo_id, 'almacen'          AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'inv.almacen.crear',                   'Crear almacenes',                   'Crear almacenes físicos y virtuales'                 , @modulo_inv_id          , 'almacen'          , 'crear'                  UNION ALL
    SELECT 'inv.almacen.actualizar',              'Actualizar almacenes',              'Editar datos de almacenes'                           , @modulo_inv_id          , 'almacen'          , 'actualizar'             UNION ALL
    SELECT 'inv.almacen.eliminar',                'Eliminar almacenes',                'Dar de baja lógica almacenes'                        , @modulo_inv_id          , 'almacen'          , 'eliminar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- INV - Stock
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'inv.stock.leer'          AS codigo, 'Leer stock'            AS nombre, 'Consultar stock actual, reservado y disponible' AS descripcion, @modulo_inv_id AS modulo_id, 'stock'            AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'inv.stock.crear',                     'Crear registros de stock',         'Crear registros de stock inicial'                    , @modulo_inv_id          , 'stock'            , 'crear'                  UNION ALL
    SELECT 'inv.stock.actualizar',                'Actualizar stock',                 'Ajustar stock y configuración por almacén'          , @modulo_inv_id          , 'stock'            , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- INV - Tipos de Movimiento
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'inv.tipo_movimiento.leer'   AS codigo, 'Leer tipos de movimiento'   AS nombre, 'Listar y ver tipos de movimiento de inventario'     AS descripcion, @modulo_inv_id AS modulo_id, 'tipo_movimiento'   AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'inv.tipo_movimiento.crear',              'Crear tipos de movimiento',              'Crear tipos de movimiento (entrada/salida/ajuste)', @modulo_inv_id          , 'tipo_movimiento'   , 'crear'                  UNION ALL
    SELECT 'inv.tipo_movimiento.actualizar',         'Actualizar tipos de movimiento',         'Editar tipos de movimiento'                         , @modulo_inv_id          , 'tipo_movimiento'   , 'actualizar'             UNION ALL
    SELECT 'inv.tipo_movimiento.eliminar',           'Eliminar tipos de movimiento',           'Dar de baja lógica tipos de movimiento'             , @modulo_inv_id          , 'tipo_movimiento'   , 'eliminar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- INV - Movimientos
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'inv.movimiento.leer'     AS codigo, 'Leer movimientos'      AS nombre, 'Listar y ver movimientos de inventario (kardex cabecera)' AS descripcion, @modulo_inv_id AS modulo_id, 'movimiento'       AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'inv.movimiento.crear',                'Crear movimientos',                'Crear movimientos de inventario (entradas/salidas/transferencias)' , @modulo_inv_id          , 'movimiento'       , 'crear'                  UNION ALL
    SELECT 'inv.movimiento.actualizar',           'Actualizar movimientos',           'Editar cabecera de movimientos de inventario'                       , @modulo_inv_id          , 'movimiento'       , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- INV - Inventario Físico
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'inv.inventario_fisico.leer'   AS codigo, 'Leer inventarios físicos'   AS nombre, 'Listar y ver tomas de inventario físico'                   AS descripcion, @modulo_inv_id AS modulo_id, 'inventario_fisico' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'inv.inventario_fisico.crear',              'Crear inventarios físicos',              'Crear tomas de inventario físico'                           , @modulo_inv_id          , 'inventario_fisico' , 'crear'                  UNION ALL
    SELECT 'inv.inventario_fisico.actualizar',         'Actualizar inventarios físicos',         'Editar tomas de inventario físico y su estado'              , @modulo_inv_id          , 'inventario_fisico' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

PRINT 'Seed permisos RBAC INV (FASE 4) completado.';

