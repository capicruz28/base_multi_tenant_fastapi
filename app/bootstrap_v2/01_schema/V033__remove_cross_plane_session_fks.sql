-- ============================================================================
-- bootstrap_v2 | schema layer — Control Plane
-- V033 — Remove cross-plane Session Store FKs to Identity (usuario)
--
-- Normativa: ADR-001-A (Identity en Data Plane)
--            ADR-002-A (Session Store IAM en Control Plane)
--            F9 Baseline — referencias lógicas cross-plane en tablas session
--
-- Decisión:  F6-P2b Alternativa 1 — referencia lógica validada por IG
-- Alcance:   Eliminar FKs CP → dbo.usuario en tablas Session Store
-- Seguimiento: V034 elimina FKs CP → dbo.org_empresa (empresa_id lógico)
--             Índices, columnas, datos — sin cambios
--
-- PREREQUISITO: V020 y/o V031 aplicados en CP (tablas session existentes)
-- TARGET BD:    Control Plane (DatabaseConnection.ADMIN)
-- ============================================================================

SET NOCOUNT ON;
GO

PRINT 'V033 — Remove cross-plane Session Store FKs (CP session → DP identity)';
GO

-- ── 1/3 FK_session_usuario ──────────────────────────────────────────────────
IF EXISTS (
    SELECT 1
    FROM sys.foreign_keys fk
    INNER JOIN sys.tables t ON fk.parent_object_id = t.object_id
    WHERE fk.name = N'FK_session_usuario'
      AND t.name = N'user_session'
      AND SCHEMA_NAME(t.schema_id) = N'dbo'
)
BEGIN
    ALTER TABLE dbo.user_session DROP CONSTRAINT FK_session_usuario;
    PRINT 'Dropped FK_session_usuario on dbo.user_session';
END
ELSE
BEGIN
    PRINT 'Skip: FK_session_usuario not found on dbo.user_session';
END
GO

-- ── 2/3 FK_family_usuario ───────────────────────────────────────────────────
IF EXISTS (
    SELECT 1
    FROM sys.foreign_keys fk
    INNER JOIN sys.tables t ON fk.parent_object_id = t.object_id
    WHERE fk.name = N'FK_family_usuario'
      AND t.name = N'token_family'
      AND SCHEMA_NAME(t.schema_id) = N'dbo'
)
BEGIN
    ALTER TABLE dbo.token_family DROP CONSTRAINT FK_family_usuario;
    PRINT 'Dropped FK_family_usuario on dbo.token_family';
END
ELSE
BEGIN
    PRINT 'Skip: FK_family_usuario not found on dbo.token_family';
END
GO

-- ── 3/3 FK_token_usuario ────────────────────────────────────────────────────
IF EXISTS (
    SELECT 1
    FROM sys.foreign_keys fk
    INNER JOIN sys.tables t ON fk.parent_object_id = t.object_id
    WHERE fk.name = N'FK_token_usuario'
      AND t.name = N'refresh_tokens'
      AND SCHEMA_NAME(t.schema_id) = N'dbo'
)
BEGIN
    ALTER TABLE dbo.refresh_tokens DROP CONSTRAINT FK_token_usuario;
    PRINT 'Dropped FK_token_usuario on dbo.refresh_tokens';
END
ELSE
BEGIN
    PRINT 'Skip: FK_token_usuario not found on dbo.refresh_tokens';
END
GO

-- ── Verificación post-migración ─────────────────────────────────────────────
IF EXISTS (
    SELECT 1
    FROM sys.foreign_keys fk
    INNER JOIN sys.tables tp ON fk.parent_object_id = tp.object_id
    INNER JOIN sys.tables tr ON fk.referenced_object_id = tr.object_id
    WHERE tp.name IN (N'user_session', N'token_family', N'refresh_tokens')
      AND tr.name = N'usuario'
      AND SCHEMA_NAME(tp.schema_id) = N'dbo'
)
BEGIN
    RAISERROR(
        'V033 VERIFICATION FAILED: FK from session tables to dbo.usuario still exists.',
        16, 1
    );
END
ELSE
BEGIN
    PRINT 'V033 VERIFICATION OK: no FK from session tables to dbo.usuario';
END
GO

-- ── Sanity: FKs intra-CP conservadas ──────────────────────────────────────────
IF NOT EXISTS (
    SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_session_cliente'
)
    PRINT 'WARN: FK_session_cliente missing (expected present)';
IF NOT EXISTS (
    SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_family_session'
)
    PRINT 'WARN: FK_family_session missing (expected present)';
IF NOT EXISTS (
    SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_token_session'
)
    PRINT 'WARN: FK_token_session missing (expected present)';
GO

PRINT 'V033 completed — remove_cross_plane_session_fks';
GO

-- ============================================================================
-- ROLLBACK MANUAL (referencia — no ejecutar en deploy automático)
-- Precondición Shared: no filas huérfanas usuario_id en tablas session CP
--
-- ALTER TABLE dbo.user_session ADD CONSTRAINT FK_session_usuario
--     FOREIGN KEY (usuario_id) REFERENCES dbo.usuario(usuario_id) ON DELETE CASCADE;
-- ALTER TABLE dbo.token_family ADD CONSTRAINT FK_family_usuario
--     FOREIGN KEY (usuario_id) REFERENCES dbo.usuario(usuario_id) ON DELETE NO ACTION;
-- ALTER TABLE dbo.refresh_tokens ADD CONSTRAINT FK_token_usuario
--     FOREIGN KEY (usuario_id) REFERENCES dbo.usuario(usuario_id) ON DELETE NO ACTION;
-- ============================================================================
