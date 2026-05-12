-- ============================================================================
-- SCRIPT: SEED permisos SLS (Ventas) - Fase 4
-- DESCRIPCIÓN:
--   - Completa el catálogo de permisos para el módulo SLS según los recursos
--     usados por el backend: sls.cliente.*, sls.contacto.*, sls.direccion.*,
--     sls.cotizacion.*, sls.pedido.*
--   - Seguro para múltiples ejecuciones (MERGE por codigo).
-- DEPENDENCIAS:
--   - SCRIPT_RBAC_TABLAS_CENTRAL.sql (tablas permiso y rol_permiso)
--   - SEED_MODULO_MENU_COMPLETO.sql (módulo SLS ya creado)
-- NOTAS:
--   - modulo_id corresponde al módulo SLS: E100000B-0000-4000-8000-00000000000B
--   - Endpoints de detalle y transiciones reutilizan *.leer y *.actualizar.
-- ============================================================================

DECLARE @modulo_sls_id UNIQUEIDENTIFIER = CAST('E100000B-0000-4000-8000-00000000000B' AS UNIQUEIDENTIFIER);

-- --------------------------------------------------------------------------
-- SLS - Clientes
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'sls.cliente.leer'       AS codigo, N'Leer clientes'        AS nombre, N'Listar y ver clientes'                       AS descripcion, @modulo_sls_id AS modulo_id, 'cliente'   AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'sls.cliente.crear',                  N'Crear clientes',                  N'Crear clientes'                                  , @modulo_sls_id              , 'cliente'   , 'crear'                  UNION ALL
    SELECT 'sls.cliente.actualizar',             N'Actualizar clientes',             N'Editar, reactivar y dar de baja (lógica) clientes', @modulo_sls_id              , 'cliente'   , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1)
WHEN MATCHED AND t.es_activo = 0 THEN
    UPDATE SET t.es_activo = 1, t.fecha_actualizacion = GETDATE();
GO

-- --------------------------------------------------------------------------
-- SLS - Contactos (de cliente)
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'sls.contacto.leer'       AS codigo, N'Leer contactos de cliente'  AS nombre, N'Listar y ver contactos de clientes'   AS descripcion, @modulo_sls_id AS modulo_id, 'contacto'  AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'sls.contacto.crear',                  N'Crear contactos',                    N'Crear contactos de clientes'                        , @modulo_sls_id              , 'contacto'  , 'crear'                  UNION ALL
    SELECT 'sls.contacto.actualizar',             N'Actualizar contactos',               N'Editar contactos de clientes'                       , @modulo_sls_id              , 'contacto'  , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1)
WHEN MATCHED AND t.es_activo = 0 THEN
    UPDATE SET t.es_activo = 1, t.fecha_actualizacion = GETDATE();
GO

-- --------------------------------------------------------------------------
-- SLS - Direcciones (de entrega)
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'sls.direccion.leer'       AS codigo, N'Leer direcciones de entrega' AS nombre, N'Listar y ver direcciones de entrega' AS descripcion, @modulo_sls_id AS modulo_id, 'direccion' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'sls.direccion.crear',                  N'Crear direcciones',                     N'Crear direcciones de entrega'                   , @modulo_sls_id              , 'direccion' , 'crear'                  UNION ALL
    SELECT 'sls.direccion.actualizar',             N'Actualizar direcciones',                N'Editar direcciones de entrega'                  , @modulo_sls_id              , 'direccion' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1)
WHEN MATCHED AND t.es_activo = 0 THEN
    UPDATE SET t.es_activo = 1, t.fecha_actualizacion = GETDATE();
GO

-- --------------------------------------------------------------------------
-- SLS - Cotizaciones
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'sls.cotizacion.leer'       AS codigo, N'Leer cotizaciones'       AS nombre, N'Listar y ver cotizaciones y detalle'    AS descripcion, @modulo_sls_id AS modulo_id, 'cotizacion' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'sls.cotizacion.crear',                  N'Crear cotizaciones',                 N'Crear cotizaciones (cabecera y detalle)'         , @modulo_sls_id              , 'cotizacion' , 'crear'                  UNION ALL
    SELECT 'sls.cotizacion.actualizar',             N'Actualizar cotizaciones',            N'Editar cotizaciones, detalle y transiciones'     , @modulo_sls_id              , 'cotizacion' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1)
WHEN MATCHED AND t.es_activo = 0 THEN
    UPDATE SET t.es_activo = 1, t.fecha_actualizacion = GETDATE();
GO

-- --------------------------------------------------------------------------
-- SLS - Pedidos
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'sls.pedido.leer'       AS codigo, N'Leer pedidos'       AS nombre, N'Listar y ver pedidos y detalle'             AS descripcion, @modulo_sls_id AS modulo_id, 'pedido' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'sls.pedido.crear',                  N'Crear pedidos',                 N'Crear pedidos (cabecera y detalle)'          , @modulo_sls_id              , 'pedido' , 'crear'                  UNION ALL
    SELECT 'sls.pedido.actualizar',             N'Actualizar pedidos',            N'Editar pedidos, detalle y transiciones'      , @modulo_sls_id              , 'pedido' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1)
WHEN MATCHED AND t.es_activo = 0 THEN
    UPDATE SET t.es_activo = 1, t.fecha_actualizacion = GETDATE();
GO

PRINT 'Seed permisos RBAC SLS (FASE 4) completado.';
GO

