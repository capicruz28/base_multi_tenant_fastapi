-- ============================================================================
-- SCRIPT: SEED permisos CRM (Customer Relationship Management) - Fase 4
-- DESCRIPCIÓN:
--   - Completa el catálogo de permisos para el módulo CRM según los recursos
--     usados por el backend: crm.campana.*, crm.lead.*, crm.oportunidad.*, crm.actividad.*
--   - Seguro para múltiples ejecuciones (MERGE por codigo).
-- DEPENDENCIAS:
--   - SCRIPT_RBAC_TABLAS_CENTRAL.sql (tablas permiso y rol_permiso)
--   - SEED_MODULO_MENU_COMPLETO.sql (módulo CRM ya creado)
-- NOTAS:
--   - modulo_id corresponde al módulo CRM: E100000C-0000-4000-8000-00000000000C
--   - Endpoints de transiciones de oportunidad reutilizan crm.oportunidad.actualizar.
-- ============================================================================

DECLARE @modulo_crm_id UNIQUEIDENTIFIER = CAST('E100000C-0000-4000-8000-00000000000C' AS UNIQUEIDENTIFIER);

-- --------------------------------------------------------------------------
-- CRM - Campañas
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'crm.campana.leer'       AS codigo, N'Leer campañas'       AS nombre, N'Listar y ver campañas'                AS descripcion, @modulo_crm_id AS modulo_id, 'campana'    AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'crm.campana.crear',                  N'Crear campañas',                  N'Crear campañas'                         , @modulo_crm_id              , 'campana'    , 'crear'                  UNION ALL
    SELECT 'crm.campana.actualizar',             N'Actualizar campañas',             N'Editar campañas'                         , @modulo_crm_id              , 'campana'    , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1)
WHEN MATCHED AND t.es_activo = 0 THEN
    UPDATE SET t.es_activo = 1, t.fecha_actualizacion = GETDATE();
GO

-- --------------------------------------------------------------------------
-- CRM - Leads
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'crm.lead.leer'       AS codigo, N'Leer leads'       AS nombre, N'Listar y ver leads'                    AS descripcion, @modulo_crm_id AS modulo_id, 'lead'       AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'crm.lead.crear',                  N'Crear leads',                  N'Crear leads'                             , @modulo_crm_id              , 'lead'       , 'crear'                  UNION ALL
    SELECT 'crm.lead.actualizar',             N'Actualizar leads',             N'Editar leads'                             , @modulo_crm_id              , 'lead'       , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1)
WHEN MATCHED AND t.es_activo = 0 THEN
    UPDATE SET t.es_activo = 1, t.fecha_actualizacion = GETDATE();
GO

-- --------------------------------------------------------------------------
-- CRM - Oportunidades
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'crm.oportunidad.leer'       AS codigo, N'Leer oportunidades'       AS nombre, N'Listar y ver oportunidades'                     AS descripcion, @modulo_crm_id AS modulo_id, 'oportunidad' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'crm.oportunidad.crear',                  N'Crear oportunidades',                  N'Crear oportunidades'                              , @modulo_crm_id              , 'oportunidad' , 'crear'                  UNION ALL
    SELECT 'crm.oportunidad.actualizar',             N'Actualizar oportunidades',             N'Editar oportunidades y transiciones de cierre'     , @modulo_crm_id              , 'oportunidad' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1)
WHEN MATCHED AND t.es_activo = 0 THEN
    UPDATE SET t.es_activo = 1, t.fecha_actualizacion = GETDATE();
GO

-- --------------------------------------------------------------------------
-- CRM - Actividades
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'crm.actividad.leer'       AS codigo, N'Leer actividades'       AS nombre, N'Listar y ver actividades'                 AS descripcion, @modulo_crm_id AS modulo_id, 'actividad'  AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'crm.actividad.crear',                  N'Crear actividades',                  N'Crear actividades de seguimiento'            , @modulo_crm_id              , 'actividad'  , 'crear'                  UNION ALL
    SELECT 'crm.actividad.actualizar',             N'Actualizar actividades',             N'Editar actividades (estado y seguimiento)'    , @modulo_crm_id              , 'actividad'  , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1)
WHEN MATCHED AND t.es_activo = 0 THEN
    UPDATE SET t.es_activo = 1, t.fecha_actualizacion = GETDATE();
GO

PRINT 'Seed permisos RBAC CRM completado.';
GO

