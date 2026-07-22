-- ============================================================================
-- SCRIPT: SEED permisos RBAC CFG (Administrador del Motor de Códigos)
-- DESCRIPCIÓN:
--   Crea/actualiza cfg.secuencias.consultar y cfg.secuencias.actualizar
--   (spec cfg-implementation-spec v1.0 — Etapa 1).
--   Permisos transversales tenant: modulo_id IS NULL.
--   Asigna ambos a roles ADMIN_TENANT existentes (cliente_id NOT NULL).
-- FUENTE CANÓNICA bootstrap_v2:
--   app/bootstrap_v2/02_catalog/permisos_rbac/S068__permisos_rbac_cfg.sql
-- USO:
--   - Idempotente: MERGE por codigo + NOT EXISTS en rol_permiso.
-- ============================================================================

MERGE INTO permiso AS t
USING (
    SELECT
        N'cfg.secuencias.consultar' AS codigo,
        N'Consultar secuencias de código' AS nombre,
        N'Listar, ver detalle y previsualizar secuencias cfg_codigo_secuencia del tenant.' AS descripcion,
        CAST(NULL AS UNIQUEIDENTIFIER) AS modulo_id,
        N'secuencias' AS recurso,
        N'consultar' AS accion
    UNION ALL
    SELECT
        N'cfg.secuencias.actualizar',
        N'Actualizar secuencias de código',
        N'Editar formato (PATCH), desactivar (DELETE soft) y reactivar secuencias cfg del tenant.',
        CAST(NULL AS UNIQUEIDENTIFIER),
        N'secuencias',
        N'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo, fecha_creacion)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1, GETDATE())
WHEN MATCHED THEN
    UPDATE SET
        t.nombre              = s.nombre,
        t.descripcion         = s.descripcion,
        t.modulo_id           = s.modulo_id,
        t.recurso             = s.recurso,
        t.accion              = s.accion,
        t.es_activo           = 1,
        t.fecha_actualizacion = GETDATE();
GO

PRINT 'Seed permiso CFG (cfg.secuencias.*) completado.';
GO

INSERT INTO rol_permiso (
    rol_permiso_id,
    cliente_id,
    rol_id,
    permiso_id,
    fecha_creacion
)
SELECT
    NEWID(),
    r.cliente_id,
    r.rol_id,
    p.permiso_id,
    GETDATE()
FROM rol r
CROSS JOIN permiso p
WHERE r.codigo_rol = N'ADMIN_TENANT'
  AND r.cliente_id IS NOT NULL
  AND r.es_activo = 1
  AND p.es_activo = 1
  AND p.codigo IN (N'cfg.secuencias.consultar', N'cfg.secuencias.actualizar')
  AND NOT EXISTS (
      SELECT 1
      FROM rol_permiso rp
      WHERE rp.cliente_id = r.cliente_id
        AND rp.rol_id = r.rol_id
        AND rp.permiso_id = p.permiso_id
  );

PRINT 'Seed rol_permiso CFG → ADMIN_TENANT completado.';
GO
