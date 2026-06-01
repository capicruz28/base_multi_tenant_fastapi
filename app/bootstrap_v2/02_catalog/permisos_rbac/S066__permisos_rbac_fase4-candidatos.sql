-- ============================================================================
-- bootstrap_v2 | official bootstrap line (copy; do not edit logic here)
-- Source (legacy, immutable): (see BOOTSTRAP_MANIFEST.md)
-- Layer: catalog
-- ============================================================================
-- ============================================================================
-- SCRIPT: Alta de permisos candidatos [C] — FASE 4 (sub-recursos LOG y FIN)
-- DESCRIPCIÓN: Inserta permisos para log.guia_remision_detalle, log.despacho_guia, fin.asiento_detalle.
-- DEPENDENCIAS: Ejecutar después de SEED_PERMISOS_RBAC.sql (y SEED_MODULO_MENU_COMPLETO.sql).
-- USO: Ejecutar UNA SOLA VEZ. MERGE por codigo; si ya existe no inserta.
-- ============================================================================
-- LOG modulo_id: E1000006-0000-4000-8000-000000000006
-- FIN modulo_id: E1000011-0000-4000-8000-000000000011
-- ============================================================================

-- LOG — guia_remision_detalle (sub-recurso)
MERGE INTO permiso AS t
USING (SELECT 'log.guia_remision_detalle.leer' AS codigo, 'Leer detalles de guía de remisión' AS nombre, 'Listar y ver líneas de guía de remisión' AS descripcion, CAST('E1000006-0000-4000-8000-000000000006' AS UNIQUEIDENTIFIER) AS modulo_id, 'guia_remision_detalle' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'log.guia_remision_detalle.crear', 'Crear detalle de guía de remisión', 'Añadir líneas a guía de remisión', CAST('E1000006-0000-4000-8000-000000000006' AS UNIQUEIDENTIFIER), 'guia_remision_detalle', 'crear' UNION ALL
       SELECT 'log.guia_remision_detalle.actualizar', 'Actualizar detalle de guía de remisión', 'Editar líneas de guía de remisión', CAST('E1000006-0000-4000-8000-000000000006' AS UNIQUEIDENTIFIER), 'guia_remision_detalle', 'actualizar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- LOG — despacho_guia (sub-recurso)
MERGE INTO permiso AS t
USING (SELECT 'log.despacho_guia.leer' AS codigo, 'Leer despacho-guía' AS nombre, 'Listar y ver relaciones despacho-guía' AS descripcion, CAST('E1000006-0000-4000-8000-000000000006' AS UNIQUEIDENTIFIER) AS modulo_id, 'despacho_guia' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'log.despacho_guia.crear', 'Crear despacho-guía', 'Asignar guías a despacho', CAST('E1000006-0000-4000-8000-000000000006' AS UNIQUEIDENTIFIER), 'despacho_guia', 'crear' UNION ALL
       SELECT 'log.despacho_guia.actualizar', 'Actualizar despacho-guía', 'Editar relación despacho-guía', CAST('E1000006-0000-4000-8000-000000000006' AS UNIQUEIDENTIFIER), 'despacho_guia', 'actualizar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- FIN — asiento_detalle (sub-recurso)
MERGE INTO permiso AS t
USING (SELECT 'fin.asiento_detalle.leer' AS codigo, 'Leer detalles de asiento' AS nombre, 'Listar y ver líneas de asiento contable' AS descripcion, CAST('E1000011-0000-4000-8000-000000000011' AS UNIQUEIDENTIFIER) AS modulo_id, 'asiento_detalle' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'fin.asiento_detalle.crear', 'Crear detalle de asiento', 'Añadir líneas a asiento contable', CAST('E1000011-0000-4000-8000-000000000011' AS UNIQUEIDENTIFIER), 'asiento_detalle', 'crear' UNION ALL
       SELECT 'fin.asiento_detalle.actualizar', 'Actualizar detalle de asiento', 'Editar líneas de asiento', CAST('E1000011-0000-4000-8000-000000000011' AS UNIQUEIDENTIFIER), 'asiento_detalle', 'actualizar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO
