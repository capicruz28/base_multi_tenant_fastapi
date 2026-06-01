-- ============================================================================
-- bootstrap_v2 | official bootstrap line (copy; do not edit logic here)
-- Source (legacy, immutable): (see BOOTSTRAP_MANIFEST.md)
-- Layer: catalog
-- ============================================================================
-- ============================================================================
-- SCRIPT: SEED permisos RBAC ORG (Organización)
-- DESCRIPCIÓN:
--   Crea/actualiza en la tabla permiso todos los códigos org.<recurso>.<accion>
--   usados por el backend (require_permission). Cubre las 6 entidades org_*.
-- DEPENDENCIAS:
--   - TABLAS_BD_CENTRAL.sql (tabla permiso, modulo)
--   - 4.- SEED_MODULO_MENU_COMPLETO.sql (módulo ORG con modulo_id E1000001-...)
-- USO:
--   - Ejecutar en bd_hybrid_sistema_central (BD central de RBAC).
--   - Idempotente: usa MERGE por codigo.
--   - No elimina permisos existentes.
-- ============================================================================

-- USE bd_hybrid_sistema_central;
-- GO

DECLARE @modulo_org_id UNIQUEIDENTIFIER = CAST('E1000001-0000-4000-8000-000000000001' AS UNIQUEIDENTIFIER);

-- --------------------------------------------------------------------------
-- ORG - Empresa (org_empresa)
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'org.empresa.leer'       AS codigo, N'Leer empresas'             AS nombre, N'Listar y ver empresas del tenant'                           AS descripcion, @modulo_org_id AS modulo_id, 'empresa' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'org.empresa.crear'             , N'Crear empresas'           , N'Crear nuevas empresas del tenant'                              , @modulo_org_id               , 'empresa' , 'crear'                  UNION ALL
    SELECT 'org.empresa.actualizar'        , N'Actualizar empresas'      , N'Editar y reactivar empresas del tenant'                        , @modulo_org_id               , 'empresa' , 'actualizar'             UNION ALL
    SELECT 'org.empresa.eliminar'          , N'Eliminar empresas'        , N'Dar de baja lógica empresas del tenant'                        , @modulo_org_id               , 'empresa' , 'eliminar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo, fecha_creacion)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1, GETDATE())
WHEN MATCHED THEN
    UPDATE SET
        t.nombre              = s.nombre,
        t.descripcion         = s.descripcion,
        t.modulo_id           = s.modulo_id,
        t.recurso             = s.recurso,
        t.accion              = s.accion,
        t.es_activo           = 1,
        t.fecha_actualizacion = GETDATE();
GO

-- --------------------------------------------------------------------------
-- ORG - Sucursal (org_sucursal)
-- --------------------------------------------------------------------------
DECLARE @modulo_org_id UNIQUEIDENTIFIER = CAST('E1000001-0000-4000-8000-000000000001' AS UNIQUEIDENTIFIER);

MERGE INTO permiso AS t
USING (
    SELECT 'org.sucursal.leer'      AS codigo, N'Leer sucursales'           AS nombre, N'Listar y ver sucursales de la empresa'                       AS descripcion, @modulo_org_id AS modulo_id, 'sucursal' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'org.sucursal.crear'            , N'Crear sucursales'         , N'Crear nuevas sucursales de la empresa'                          , @modulo_org_id               , 'sucursal' , 'crear'                  UNION ALL
    SELECT 'org.sucursal.actualizar'       , N'Actualizar sucursales'    , N'Editar y reactivar sucursales de la empresa'                    , @modulo_org_id               , 'sucursal' , 'actualizar'             UNION ALL
    SELECT 'org.sucursal.eliminar'         , N'Eliminar sucursales'      , N'Dar de baja lógica sucursales de la empresa'                    , @modulo_org_id               , 'sucursal' , 'eliminar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo, fecha_creacion)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1, GETDATE())
WHEN MATCHED THEN
    UPDATE SET
        t.nombre              = s.nombre,
        t.descripcion         = s.descripcion,
        t.modulo_id           = s.modulo_id,
        t.recurso             = s.recurso,
        t.accion              = s.accion,
        t.es_activo           = 1,
        t.fecha_actualizacion = GETDATE();
GO

-- --------------------------------------------------------------------------
-- ORG - Centro de Costo (org_centro_costo)
-- --------------------------------------------------------------------------
DECLARE @modulo_org_id UNIQUEIDENTIFIER = CAST('E1000001-0000-4000-8000-000000000001' AS UNIQUEIDENTIFIER);

MERGE INTO permiso AS t
USING (
    SELECT 'org.centro_costo.leer'  AS codigo, N'Leer centros de costo'     AS nombre, N'Listar y ver centros de costo de la empresa'                 AS descripcion, @modulo_org_id AS modulo_id, 'centro_costo' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'org.centro_costo.crear'        , N'Crear centros de costo'   , N'Crear nuevos centros de costo de la empresa'                    , @modulo_org_id               , 'centro_costo' , 'crear'                  UNION ALL
    SELECT 'org.centro_costo.actualizar'   , N'Actualizar centros de costo', N'Editar y reactivar centros de costo de la empresa'            , @modulo_org_id               , 'centro_costo' , 'actualizar'             UNION ALL
    SELECT 'org.centro_costo.eliminar'     , N'Eliminar centros de costo', N'Dar de baja lógica centros de costo de la empresa'              , @modulo_org_id               , 'centro_costo' , 'eliminar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo, fecha_creacion)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1, GETDATE())
WHEN MATCHED THEN
    UPDATE SET
        t.nombre              = s.nombre,
        t.descripcion         = s.descripcion,
        t.modulo_id           = s.modulo_id,
        t.recurso             = s.recurso,
        t.accion              = s.accion,
        t.es_activo           = 1,
        t.fecha_actualizacion = GETDATE();
GO

-- --------------------------------------------------------------------------
-- ORG - Departamento Organizacional (org_departamento)
-- --------------------------------------------------------------------------
DECLARE @modulo_org_id UNIQUEIDENTIFIER = CAST('E1000001-0000-4000-8000-000000000001' AS UNIQUEIDENTIFIER);

MERGE INTO permiso AS t
USING (
    SELECT 'org.departamento.leer'  AS codigo, N'Leer departamentos'        AS nombre, N'Listar y ver departamentos organizacionales de la empresa'    AS descripcion, @modulo_org_id AS modulo_id, 'departamento' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'org.departamento.crear'        , N'Crear departamentos'      , N'Crear departamentos organizacionales de la empresa'             , @modulo_org_id               , 'departamento' , 'crear'                  UNION ALL
    SELECT 'org.departamento.actualizar'   , N'Actualizar departamentos' , N'Editar y reactivar departamentos organizacionales'             , @modulo_org_id               , 'departamento' , 'actualizar'             UNION ALL
    SELECT 'org.departamento.eliminar'     , N'Eliminar departamentos'   , N'Dar de baja lógica departamentos organizacionales'             , @modulo_org_id               , 'departamento' , 'eliminar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo, fecha_creacion)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1, GETDATE())
WHEN MATCHED THEN
    UPDATE SET
        t.nombre              = s.nombre,
        t.descripcion         = s.descripcion,
        t.modulo_id           = s.modulo_id,
        t.recurso             = s.recurso,
        t.accion              = s.accion,
        t.es_activo           = 1,
        t.fecha_actualizacion = GETDATE();
GO

-- --------------------------------------------------------------------------
-- ORG - Cargo / Puesto de Trabajo (org_cargo)
-- --------------------------------------------------------------------------
DECLARE @modulo_org_id UNIQUEIDENTIFIER = CAST('E1000001-0000-4000-8000-000000000001' AS UNIQUEIDENTIFIER);

MERGE INTO permiso AS t
USING (
    SELECT 'org.cargo.leer'         AS codigo, N'Leer cargos'               AS nombre, N'Listar y ver cargos/puestos de trabajo de la empresa'         AS descripcion, @modulo_org_id AS modulo_id, 'cargo' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'org.cargo.crear'               , N'Crear cargos'             , N'Crear nuevos cargos/puestos de trabajo'                          , @modulo_org_id               , 'cargo' , 'crear'                  UNION ALL
    SELECT 'org.cargo.actualizar'          , N'Actualizar cargos'        , N'Editar y reactivar cargos/puestos de trabajo'                    , @modulo_org_id               , 'cargo' , 'actualizar'             UNION ALL
    SELECT 'org.cargo.eliminar'            , N'Eliminar cargos'          , N'Dar de baja lógica cargos/puestos de trabajo'                    , @modulo_org_id               , 'cargo' , 'eliminar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo, fecha_creacion)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1, GETDATE())
WHEN MATCHED THEN
    UPDATE SET
        t.nombre              = s.nombre,
        t.descripcion         = s.descripcion,
        t.modulo_id           = s.modulo_id,
        t.recurso             = s.recurso,
        t.accion              = s.accion,
        t.es_activo           = 1,
        t.fecha_actualizacion = GETDATE();
GO

-- --------------------------------------------------------------------------
-- ORG - Parámetro del Sistema (org_parametro_sistema)
-- --------------------------------------------------------------------------
DECLARE @modulo_org_id UNIQUEIDENTIFIER = CAST('E1000001-0000-4000-8000-000000000001' AS UNIQUEIDENTIFIER);

MERGE INTO permiso AS t
USING (
    SELECT 'org.parametro.leer'     AS codigo, N'Leer parámetros del sistema'  AS nombre, N'Consultar parámetros de configuración del sistema'             AS descripcion, @modulo_org_id AS modulo_id, 'parametro' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'org.parametro.crear'           , N'Crear parámetros del sistema', N'Crear nuevos parámetros de configuración del sistema'             , @modulo_org_id               , 'parametro' , 'crear'                  UNION ALL
    SELECT 'org.parametro.actualizar'      , N'Actualizar parámetros del sistema', N'Editar y reactivar parámetros de configuración del sistema'  , @modulo_org_id               , 'parametro' , 'actualizar'             UNION ALL
    SELECT 'org.parametro.eliminar'        , N'Eliminar parámetros del sistema', N'Dar de baja lógica parámetros de configuración del sistema'    , @modulo_org_id               , 'parametro' , 'eliminar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo, fecha_creacion)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1, GETDATE())
WHEN MATCHED THEN
    UPDATE SET
        t.nombre              = s.nombre,
        t.descripcion         = s.descripcion,
        t.modulo_id           = s.modulo_id,
        t.recurso             = s.recurso,
        t.accion              = s.accion,
        t.es_activo           = 1,
        t.fecha_actualizacion = GETDATE();
GO

PRINT 'Seed permisos RBAC ORG completado: 24 permisos (6 recursos x 4 acciones).';
GO
