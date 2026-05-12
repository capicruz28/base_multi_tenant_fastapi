-- ============================================================================
-- SCRIPT: SEED permisos AUD (Auditoría y Trazabilidad)
-- DESCRIPCIÓN:
--   - Inserta/asegura el catálogo de permisos RBAC para el módulo AUD
--     según los recursos usados por el backend: aud.log.*
-- NOTAS:
--   - Usa MERGE por codigo para ser idempotente.
--   - modulo_id AUD: E100001B-0000-4000-8000-00000000001B
-- DEPENDENCIAS:
--   - Tablas RBAC (permiso, rol_permiso) ya creadas.
--   - Módulo AUD ya creado en catálogo de módulos/menús (SEED_MODULO_MENU_COMPLETO.sql).
-- ============================================================================

DECLARE @modulo_aud_id UNIQUEIDENTIFIER = CAST('E100001B-0000-4000-8000-00000000001B' AS UNIQUEIDENTIFIER);

-- --------------------------------------------------------------------------
-- AUD - Log de auditoría
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'aud.log.leer'  AS codigo, N'Leer log de auditoría'  AS nombre, N'Listar y consultar eventos del log de auditoría' AS descripcion, @modulo_aud_id AS modulo_id, 'log' AS recurso, 'leer'  AS accion UNION ALL
    SELECT 'aud.log.crear' AS codigo, N'Crear log de auditoría' AS nombre, N'Registrar eventos en el log de auditoría'         AS descripcion, @modulo_aud_id AS modulo_id, 'log' AS recurso, 'crear' AS accion
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

PRINT 'Seed permisos RBAC AUD completado.';

