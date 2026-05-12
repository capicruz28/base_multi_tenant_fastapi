-- ============================================================================
-- SCRIPT: SEED permisos módulo PRC (Gestión de precios)
-- DESCRIPCIÓN: Crea/actualiza en la tabla permiso los códigos
--              prc.lista_precio.* y prc.promocion.* usados por el backend.
-- DEPENDENCIAS:
--   - Tabla permiso, modulo (BD central RBAC)
--   - Módulo PRC con modulo_id E100000D-0000-4000-8000-00000000000D
--       (p. ej. SEED_MODULO_MENU.SQL / 4.- SEED_MODULO_MENU_COMPLETO.sql)
-- USO:
--   - Ejecutar en bd_hybrid_sistema_central (BD central de RBAC).
--   - Idempotente: MERGE por codigo.
--   - No elimina permisos existentes.
-- ============================================================================

-- USE bd_hybrid_sistema_central;
-- GO

DECLARE @ModuloPrc UNIQUEIDENTIFIER = CAST('E100000D-0000-4000-8000-00000000000D' AS UNIQUEIDENTIFIER);

MERGE INTO permiso AS t
USING (
    SELECT 'prc.lista_precio.leer'       AS codigo, 'Leer listas de precio'        AS nombre, 'Listar y ver listas de precio y sus detalles' AS descripcion, @ModuloPrc AS modulo_id, 'lista_precio' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'prc.lista_precio.crear',                    'Crear listas de precio',                    'Crear listas de precio y líneas de detalle',                              @ModuloPrc,                 'lista_precio',                    'crear'                  UNION ALL
    SELECT 'prc.lista_precio.actualizar',             'Actualizar listas de precio',               'Editar listas de precio, detalles y reactivar listas',                    @ModuloPrc,                 'lista_precio',                    'actualizar'             UNION ALL
    SELECT 'prc.lista_precio.eliminar',                'Desactivar listas de precio',               'Baja lógica de listas de precio (es_activo = 0)',                        @ModuloPrc,                 'lista_precio',                    'eliminar'               UNION ALL

    SELECT 'prc.promocion.leer',                       'Leer promociones',                          'Listar y ver promociones',                                                @ModuloPrc,                 'promocion',                       'leer'                   UNION ALL
    SELECT 'prc.promocion.crear',                      'Crear promociones',                         'Crear promociones y ofertas',                                             @ModuloPrc,                 'promocion',                       'crear'                  UNION ALL
    SELECT 'prc.promocion.actualizar',               'Actualizar promociones',                    'Editar promociones y reactivar promociones',                              @ModuloPrc,                 'promocion',                       'actualizar'             UNION ALL
    SELECT 'prc.promocion.eliminar',                  'Desactivar promociones',                    'Baja lógica de promociones (es_activo = 0)',                              @ModuloPrc,                 'promocion',                       'eliminar'
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
