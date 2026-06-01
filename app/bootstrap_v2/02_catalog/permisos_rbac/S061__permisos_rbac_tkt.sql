-- ============================================================================
-- bootstrap_v2 | official bootstrap line (copy; do not edit logic here)
-- Source (legacy, immutable): (see BOOTSTRAP_MANIFEST.md)
-- Layer: catalog
-- ============================================================================
-- ============================================================================
-- SCRIPT: SEED permisos TKT (Mesa de Ayuda / Ticketing)
-- DESCRIPCIÓN:
--   - Completa el catálogo de permisos para el módulo TKT según los recursos
--     usados por el backend: tkt.ticket.*
--   - No reemplaza SEED_PERMISOS_RBAC.sql general; se ejecuta como
--     complemento específico para TKT.
-- DEPENDENCIAS:
--   - SCRIPT_RBAC_TABLAS_CENTRAL.sql (tablas permiso y rol_permiso)
--   - SEED_MODULO_MENU_COMPLETO.sql (módulo TKT ya creado)
-- NOTAS:
--   - Usa MERGE por código para ser seguro ante múltiples ejecuciones.
--   - modulo_id corresponde al módulo TKT: E1000017-0000-4000-8000-000000000017
-- ============================================================================

DECLARE @modulo_tkt_id UNIQUEIDENTIFIER = CAST('E1000017-0000-4000-8000-000000000017' AS UNIQUEIDENTIFIER);

-- --------------------------------------------------------------------------
-- TKT - Tickets
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'tkt.ticket.leer'       AS codigo, 'Leer tickets'       AS nombre, 'Listar y ver tickets'                      AS descripcion, @modulo_tkt_id AS modulo_id, 'ticket' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'tkt.ticket.crear',                  'Crear tickets',                  'Crear tickets de mesa de ayuda'                      , @modulo_tkt_id             , 'ticket'          , 'crear'                  UNION ALL
    SELECT 'tkt.ticket.actualizar',             'Actualizar tickets',             'Editar tickets (solo estados editables)'             , @modulo_tkt_id             , 'ticket'          , 'actualizar'             UNION ALL
    SELECT 'tkt.ticket.asignar',                'Asignar tickets',                'Asignar tickets a un usuario responsable'            , @modulo_tkt_id             , 'ticket'          , 'asignar'                UNION ALL
    SELECT 'tkt.ticket.resolver',               'Resolver tickets',               'Registrar solución y marcar tickets como resueltos'  , @modulo_tkt_id             , 'ticket'          , 'resolver'               UNION ALL
    SELECT 'tkt.ticket.cerrar',                 'Cerrar tickets',                 'Cerrar tickets resueltos'                             , @modulo_tkt_id             , 'ticket'          , 'cerrar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

PRINT 'Seed permisos RBAC TKT completado.';

