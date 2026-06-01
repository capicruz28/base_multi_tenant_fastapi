-- ============================================================================
-- bootstrap_v2 | official bootstrap line (copy; do not edit logic here)
-- Source (legacy, immutable): (see BOOTSTRAP_MANIFEST.md)
-- Layer: catalog
-- ============================================================================
-- ============================================================================
-- SCRIPT: SEED permisos RBAC — módulo SVC (Gestión de Servicios)
-- DESCRIPCIÓN:
--   Alta idempotente (MERGE por codigo) de permisos usados por el backend para
--   recurso orden_servicio: svc.orden_servicio.[leer|crear|actualizar|cancelar].
-- DEPENDENCIAS:
--   - Tabla permiso y estructura RBAC cargada (p. ej. SEED_PERMISOS_RBAC.sql)
--   - Módulo SVC en tabla modulo / menú:
--       modulo_id: E1000016-0000-4000-8000-000000000016
-- USO: Seguro re-ejecutar (MERGE).
-- ============================================================================

DECLARE @modulo_svc_id UNIQUEIDENTIFIER = CAST('E1000016-0000-4000-8000-000000000016' AS UNIQUEIDENTIFIER);

MERGE INTO permiso AS t
USING (
    SELECT 'svc.orden_servicio.leer' AS codigo, N'Leer órdenes de servicio' AS nombre, N'Listar y ver órdenes de servicio' AS descripcion, @modulo_svc_id AS modulo_id, 'orden_servicio' AS recurso, 'leer' AS accion UNION ALL
    SELECT 'svc.orden_servicio.crear', N'Crear órdenes de servicio', N'Crear registros en svc_orden_servicio', @modulo_svc_id, 'orden_servicio', 'crear' UNION ALL
    SELECT 'svc.orden_servicio.actualizar', N'Actualizar órdenes de servicio', N'Actualizar datos y transiciones operativas (asignar, iniciar, completar)', @modulo_svc_id, 'orden_servicio', 'actualizar' UNION ALL
    SELECT 'svc.orden_servicio.cancelar', N'Cancelar órdenes de servicio', N'Cancelar órdenes en estado solicitada o asignada', @modulo_svc_id, 'orden_servicio', 'cancelar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1)
WHEN MATCHED AND t.es_activo = 0 THEN
    UPDATE SET t.es_activo = 1, t.fecha_actualizacion = GETDATE();
GO
