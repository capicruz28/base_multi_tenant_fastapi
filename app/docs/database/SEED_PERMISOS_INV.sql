-- ============================================================================
-- SCRIPT: SEED permisos módulo INV (Inventarios)
-- DESCRIPCIÓN: Crea/actualiza en la tabla permiso todos los códigos
--              inv.<recurso>.<accion> usados por el backend.
-- DEPENDENCIAS:
--   - TABLAS_BD_CENTRAL.sql (tabla permiso, modulo)
--   - 4.- SEED_MODULO_MENU_COMPLETO.sql (módulo INV con modulo_id E1000002-...)
-- USO:
--   - Ejecutar en bd_hybrid_sistema_central (BD central de RBAC).
--   - Idempotente: usa MERGE por codigo.
--   - No elimina permisos existentes.
-- ============================================================================

-- Descomentar y ajustar si es necesario:
-- USE bd_hybrid_sistema_central;
-- GO

DECLARE @ModuloInv UNIQUEIDENTIFIER = CAST('E1000002-0000-4000-8000-000000000002' AS UNIQUEIDENTIFIER);

MERGE INTO permiso AS t
USING (
    -- Categorías
    SELECT 'inv.categoria.leer'          AS codigo, 'Leer categorías'              AS nombre, 'Listar y ver categorías de productos'                   AS descripcion, @ModuloInv AS modulo_id, 'categoria'          AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'inv.categoria.crear',                     'Crear categorías',                      'Crear categorías de productos',                              @ModuloInv,                 'categoria',                    'crear'                  UNION ALL
    SELECT 'inv.categoria.actualizar',                'Actualizar categorías',                 'Editar categorías de productos',                             @ModuloInv,                 'categoria',                    'actualizar'             UNION ALL

    -- Unidades de medida
    SELECT 'inv.unidad_medida.leer',                  'Leer unidades de medida',               'Listar y ver unidades de medida'                            @ModuloInv,                 'unidad_medida',                'leer'                   UNION ALL
    SELECT 'inv.unidad_medida.crear',                 'Crear unidades de medida',              'Crear unidades de medida'                                   @ModuloInv,                 'unidad_medida',                'crear'                  UNION ALL
    SELECT 'inv.unidad_medida.actualizar',            'Actualizar unidades de medida',         'Editar unidades de medida'                                  @ModuloInv,                 'unidad_medida',                'actualizar'             UNION ALL

    -- Productos (complementa seed global si existe)
    SELECT 'inv.producto.leer',                       'Leer productos',                        'Listar y ver productos, categorías, stock'                  @ModuloInv,                 'producto',                     'leer'                   UNION ALL
    SELECT 'inv.producto.crear',                      'Crear productos',                       'Crear productos y categorías'                               @ModuloInv,                 'producto',                     'crear'                  UNION ALL
    SELECT 'inv.producto.actualizar',                 'Actualizar productos',                  'Editar productos e inventario'                              @ModuloInv,                 'producto',                     'actualizar'             UNION ALL
    SELECT 'inv.producto.eliminar',                   'Eliminar productos',                    'Dar de baja productos (baja lógica recomendada)'            @ModuloInv,                 'producto',                     'eliminar'               UNION ALL

    -- Almacenes
    SELECT 'inv.almacen.leer',                        'Leer almacenes',                        'Listar y ver almacenes'                                     @ModuloInv,                 'almacen',                      'leer'                   UNION ALL
    SELECT 'inv.almacen.crear',                       'Crear almacenes',                       'Crear almacenes físicos y virtuales'                        @ModuloInv,                 'almacen',                      'crear'                  UNION ALL
    SELECT 'inv.almacen.actualizar',                  'Actualizar almacenes',                  'Editar datos de almacenes'                                  @ModuloInv,                 'almacen',                      'actualizar'             UNION ALL

    -- Stock
    SELECT 'inv.stock.leer',                          'Leer stock',                            'Consultar stock por producto y almacén'                     @ModuloInv,                 'stock',                        'leer'                   UNION ALL
    SELECT 'inv.stock.crear',                         'Crear registros de stock',              'Crear registros de stock inicial u operaciones especiales'  @ModuloInv,                 'stock',                        'crear'                  UNION ALL
    SELECT 'inv.stock.actualizar',                    'Actualizar stock',                      'Actualizar registros de stock'                              @ModuloInv,                 'stock',                        'actualizar'             UNION ALL

    -- Tipos de movimiento
    SELECT 'inv.tipo_movimiento.leer',                'Leer tipos de movimiento',              'Listar y ver tipos de movimiento de inventario'             @ModuloInv,                 'tipo_movimiento',              'leer'                   UNION ALL
    SELECT 'inv.tipo_movimiento.crear',               'Crear tipos de movimiento',             'Crear tipos de movimiento de inventario'                    @ModuloInv,                 'tipo_movimiento',              'crear'                  UNION ALL
    SELECT 'inv.tipo_movimiento.actualizar',          'Actualizar tipos de movimiento',        'Editar tipos de movimiento de inventario'                   @ModuloInv,                 'tipo_movimiento',              'actualizar'             UNION ALL

    -- Movimientos (cabecera)
    SELECT 'inv.movimiento.leer',                     'Leer movimientos',                      'Listar y ver movimientos de inventario'                     @ModuloInv,                 'movimiento',                   'leer'                   UNION ALL
    SELECT 'inv.movimiento.crear',                    'Crear movimientos',                     'Crear movimientos de inventario'                            @ModuloInv,                 'movimiento',                   'crear'                  UNION ALL
    SELECT 'inv.movimiento.actualizar',               'Actualizar movimientos',                'Editar movimientos de inventario'                           @ModuloInv,                 'movimiento',                   'actualizar'             UNION ALL

    -- Inventario físico (cabecera)
    SELECT 'inv.inventario_fisico.leer',              'Leer inventarios físicos',              'Listar y ver tomas de inventario físico'                    @ModuloInv,                 'inventario_fisico',            'leer'                   UNION ALL
    SELECT 'inv.inventario_fisico.crear',             'Crear inventarios físicos',             'Crear tomas de inventario físico'                           @ModuloInv,                 'inventario_fisico',            'crear'                  UNION ALL
    SELECT 'inv.inventario_fisico.actualizar',        'Actualizar inventarios físicos',        'Editar tomas de inventario físico'                          @ModuloInv,                 'inventario_fisico',            'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo, fecha_creacion)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1, GETDATE())
WHEN MATCHED THEN
    UPDATE SET
        t.nombre       = s.nombre,
        t.descripcion  = s.descripcion,
        t.modulo_id    = s.modulo_id,
        t.recurso      = s.recurso,
        t.accion       = s.accion,
        t.es_activo    = 1,
        t.fecha_actualizacion = GETDATE();
GO

