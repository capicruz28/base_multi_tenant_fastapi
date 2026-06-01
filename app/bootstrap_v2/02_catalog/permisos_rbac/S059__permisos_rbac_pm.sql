-- ============================================================================
-- bootstrap_v2 | official bootstrap line (copy; do not edit logic here)
-- Source (legacy, immutable): (see BOOTSTRAP_MANIFEST.md)
-- Layer: catalog
-- ============================================================================
-- ============================================================================
-- SCRIPT: SEED permisos RBAC — módulo PM (Gestión de Proyectos)
-- DESCRIPCIÓN:
--   Alta idempotente (MERGE por codigo) de permisos usados por el backend para
--   recurso proyecto: pm.proyecto.leer, crear, actualizar.
-- DEPENDENCIAS:
--   - Tabla permiso y estructura RBAC cargada (p. ej. SEED_PERMISOS_RBAC.sql)
--   - Módulo PM en tabla modulo / menú:
--       modulo_id: E1000015-0000-4000-8000-000000000015
-- USO: Seguro re-ejecutar (MERGE).
-- ============================================================================

DECLARE @modulo_pm_id UNIQUEIDENTIFIER = CAST('E1000015-0000-4000-8000-000000000015' AS UNIQUEIDENTIFIER);

MERGE INTO permiso AS t
USING (
    SELECT 'pm.proyecto.leer' AS codigo, N'Leer proyectos' AS nombre, N'Listar y ver proyectos' AS descripcion, @modulo_pm_id AS modulo_id, 'proyecto' AS recurso, 'leer' AS accion UNION ALL
    SELECT 'pm.proyecto.crear', N'Crear proyectos', N'Crear registros en pm_proyecto', @modulo_pm_id, 'proyecto', 'crear' UNION ALL
    SELECT 'pm.proyecto.actualizar', N'Actualizar proyectos', N'Actualizar registros en pm_proyecto', @modulo_pm_id, 'proyecto', 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1)
WHEN MATCHED AND t.es_activo = 0 THEN
    UPDATE SET t.es_activo = 1, t.fecha_actualizacion = GETDATE();
GO
