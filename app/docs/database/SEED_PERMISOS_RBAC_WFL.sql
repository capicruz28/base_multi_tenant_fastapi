-- ============================================================================
-- SCRIPT: SEED permisos WFL (Motor de Flujos / Workflow)
-- DESCRIPCION:
--   - Completa el catalogo de permisos para el modulo WFL segun los recursos
--     usados por el backend: wfl.flujo.*
--   - Seguro para multiples ejecuciones (MERGE por codigo).
-- DEPENDENCIAS:
--   - SCRIPT_RBAC_TABLAS_CENTRAL.sql (tablas permiso y rol_permiso)
--   - SEED_MODULO_MENU.SQL / SEED_MODULO_MENU_COMPLETO.sql (modulo WFL ya creado)
-- NOTAS:
--   - modulo_id corresponde al modulo WFL: E100001A-0000-4000-8000-00000000001A
-- ============================================================================

DECLARE @modulo_wfl_id UNIQUEIDENTIFIER = CAST('E100001A-0000-4000-8000-00000000001A' AS UNIQUEIDENTIFIER);

-- --------------------------------------------------------------------------
-- WFL - Flujos de trabajo
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'wfl.flujo.leer'       AS codigo, N'Leer flujos de trabajo'       AS nombre, N'Listar y consultar flujos de trabajo'                  AS descripcion, @modulo_wfl_id AS modulo_id, 'flujo' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'wfl.flujo.crear',                  N'Crear flujos de trabajo',                  N'Crear configuraciones de flujos de trabajo'             , @modulo_wfl_id              , 'flujo'         , 'crear'                  UNION ALL
    SELECT 'wfl.flujo.actualizar',             N'Actualizar flujos de trabajo',             N'Editar y reactivar configuraciones de flujos de trabajo', @modulo_wfl_id              , 'flujo'         , 'actualizar'             UNION ALL
    SELECT 'wfl.flujo.eliminar',               N'Desactivar flujos de trabajo',             N'Baja logica (es_activo = 0) de flujos de trabajo'        , @modulo_wfl_id              , 'flujo'         , 'eliminar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1)
WHEN MATCHED AND t.es_activo = 0 THEN
    UPDATE SET t.es_activo = 1, t.fecha_actualizacion = GETDATE();
GO

PRINT 'Seed permisos RBAC WFL completado.';
GO
