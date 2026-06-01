-- ============================================================================
-- bootstrap_v2 | official bootstrap line (copy; do not edit logic here)
-- Source (legacy, immutable): (see BOOTSTRAP_MANIFEST.md)
-- Layer: catalog
-- ============================================================================
-- ============================================================================
-- SCRIPT: Permisos RBAC — modulo BDG (Presupuestos)
-- DESCRIPCION: Alta idempotente (MERGE por codigo) de permisos transaccionales
--              para bdg.presupuesto.*.
-- DEPENDENCIAS: Ejecutar despues de SEED_PERMISOS_RBAC.sql (o equivalente base)
--               y existencia del modulo BDG en tabla modulo.
-- BDG modulo_id: E1000013-0000-4000-8000-000000000013
-- USO: Ejecutar en entornos donde falten estos codigos; seguro re-ejecutar (MERGE).
-- ============================================================================

DECLARE @modulo_bdg UNIQUEIDENTIFIER = CAST('E1000013-0000-4000-8000-000000000013' AS UNIQUEIDENTIFIER);

MERGE INTO permiso AS t
USING (
    SELECT 'bdg.presupuesto.aprobar' AS codigo, N'Aprobar presupuesto' AS nombre, N'Transicion de presupuesto: borrador a aprobado' AS descripcion, @modulo_bdg AS modulo_id, 'presupuesto' AS recurso, 'aprobar' AS accion UNION ALL
    SELECT 'bdg.presupuesto.procesar', N'Procesar presupuesto', N'Transicion de presupuesto: aprobado a vigente', @modulo_bdg, 'presupuesto', 'procesar' UNION ALL
    SELECT 'bdg.presupuesto.anular', N'Anular presupuesto', N'Transicion de presupuesto: borrador o aprobado a anulado', @modulo_bdg, 'presupuesto', 'anular'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO
