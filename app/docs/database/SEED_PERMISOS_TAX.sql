-- ============================================================================
-- SCRIPT: SEED permisos módulo TAX (Gestión tributaria / libros electrónicos)
-- DESCRIPCIÓN: Crea/actualiza en la tabla permiso los códigos tax.libro.*
--              usados por el backend.
-- DEPENDENCIAS:
--   - TABLAS_BD_CENTRAL.sql (tabla permiso, modulo)
--   - SEED_MODULO_MENU.SQL o equivalente (módulo TAX con modulo_id abajo)
-- USO:
--   - Ejecutar en bd_hybrid_sistema_central (BD central de RBAC).
--   - Idempotente: MERGE por codigo.
--   - No elimina permisos existentes.
-- ============================================================================

-- Descomentar y ajustar si es necesario:
-- USE bd_hybrid_sistema_central;
-- GO

DECLARE @ModuloTax UNIQUEIDENTIFIER = CAST('E1000012-0000-4000-8000-000000000012' AS UNIQUEIDENTIFIER);

MERGE INTO permiso AS t
USING (
    SELECT 'tax.libro.leer'          AS codigo, 'Leer libros electrónicos'       AS nombre, 'Listar y ver libros electrónicos (PLE)'              AS descripcion, @ModuloTax AS modulo_id, 'libro' AS recurso, 'leer'       AS accion UNION ALL
    SELECT 'tax.libro.crear',                     'Crear libros electrónicos',                      'Registrar borradores de libros electrónicos',                              @ModuloTax,                 'libro',                    'crear'                  UNION ALL
    SELECT 'tax.libro.actualizar',                'Actualizar libros electrónicos',                 'Editar borradores, marcar generado, registrar envío y anular',             @ModuloTax,                 'libro',                    'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo, fecha_creacion)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1, GETDATE())
WHEN MATCHED THEN
    UPDATE SET
        t.nombre       = s.nombre,
        t.descripcion  = s.descripcion,
        t.modulo_id    = s.modulo_id,
        t.recurso      = s.recurso,
        t.accion       = s.accion,
        t.es_activo    = 1,
        t.fecha_actualizacion = GETDATE();
GO
