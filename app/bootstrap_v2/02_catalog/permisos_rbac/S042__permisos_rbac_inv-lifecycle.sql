-- ============================================================================
-- bootstrap_v2 | official bootstrap line (copy; do not edit logic here)
-- Source (legacy, immutable): (see BOOTSTRAP_MANIFEST.md)
-- Layer: catalog
-- ============================================================================
-- ============================================================================
-- SCRIPT: SEED permisos INV (Inventarios) - Acciones lifecycle granulares
-- DESCRIPCIÓN:
--   Agrega los 6 permisos de ciclo de vida que faltaban en FASE4 y que
--   ahora tienen endpoints dedicados en el backend:
--
--   Movimientos:
--     inv.movimiento.procesar   → POST /{id}/procesar
--     inv.movimiento.autorizar  → POST /{id}/autorizar
--     inv.movimiento.anular     → POST /{id}/anular
--
--   Inventario Físico:
--     inv.inventario_fisico.finalizar → POST /{id}/finalizar
--     inv.inventario_fisico.aprobar   → POST /{id}/aprobar
--     inv.inventario_fisico.anular    → POST /{id}/anular
--
-- CONTEXTO:
--   Antes estos endpoints usaban el permiso genérico '.actualizar', lo que
--   impedía control granular por rol. Con este seed cada acción de ciclo de
--   vida tiene su propio permiso y puede asignarse independientemente.
--
-- DEPENDENCIAS:
--   - SEED_PERMISOS_RBAC_INV_FASE4.sql (debe ejecutarse primero)
--   - modulo_id INV: 'E1000002-0000-4000-8000-000000000002'
-- NOTAS:
--   - Usa MERGE por código → seguro ante múltiples ejecuciones (idempotente).
--   - Asignar estos permisos a los roles correspondientes según las políticas
--     de acceso del cliente (ver tabla rol_permiso).
-- ============================================================================

DECLARE @modulo_inv_id UNIQUEIDENTIFIER = CAST('E1000002-0000-4000-8000-000000000002' AS UNIQUEIDENTIFIER);

-- --------------------------------------------------------------------------
-- INV - Movimientos: acciones de ciclo de vida
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'inv.movimiento.procesar'  AS codigo,
           'Procesar movimiento'      AS nombre,
           'Ejecutar el procesamiento de un movimiento de inventario y aplicar impacto en stock'
                                      AS descripcion,
           @modulo_inv_id             AS modulo_id,
           'movimiento'               AS recurso,
           'procesar'                 AS accion
    UNION ALL
    SELECT 'inv.movimiento.autorizar',
           'Autorizar movimiento',
           'Autorizar un movimiento de inventario que requiere aprobación previa al proceso',
           @modulo_inv_id,
           'movimiento',
           'autorizar'
    UNION ALL
    SELECT 'inv.movimiento.anular',
           'Anular movimiento',
           'Anular un movimiento de inventario (solo si no está procesado)',
           @modulo_inv_id,
           'movimiento',
           'anular'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- INV - Inventario Físico: acciones de ciclo de vida
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'inv.inventario_fisico.finalizar' AS codigo,
           'Finalizar inventario físico'     AS nombre,
           'Cerrar el conteo de un inventario físico (en_proceso → finalizado) para dejarlo listo para aprobación'
                                             AS descripcion,
           @modulo_inv_id                    AS modulo_id,
           'inventario_fisico'               AS recurso,
           'finalizar'                       AS accion
    UNION ALL
    SELECT 'inv.inventario_fisico.aprobar',
           'Aprobar inventario físico',
           'Aprobar un inventario físico finalizado: genera el movimiento de ajuste y actualiza el stock',
           @modulo_inv_id,
           'inventario_fisico',
           'aprobar'
    UNION ALL
    SELECT 'inv.inventario_fisico.anular',
           'Anular inventario físico',
           'Anular un inventario físico (no permitido si ya está ajustado)',
           @modulo_inv_id,
           'inventario_fisico',
           'anular'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

PRINT 'Seed permisos RBAC INV - Acciones lifecycle granulares completado (6 permisos).';
GO
