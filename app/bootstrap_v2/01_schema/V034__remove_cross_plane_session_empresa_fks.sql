-- ============================================================================
-- bootstrap_v2 | schema layer — Control Plane
-- V034 — Remove cross-plane Session Store FKs to Company (org_empresa)
--
-- Normativa: ADR-001-A (Company / org_empresa en Data Plane)
--            ADR-002-A (Session Store IAM en Control Plane)
--            F9 Baseline — empresa_id referencia lógica cross-plane
--
-- Decisión:  Extensión F6-P2b Alternativa 1 (post-V033)
-- Alcance:   Eliminar FKs CP → dbo.org_empresa en tablas Session Store
-- PREREQ:    V033 aplicada (FKs CP → usuario ya eliminadas)
-- Fuera:     Índices, columnas, datos — sin cambios
--
-- TARGET BD: Control Plane (DatabaseConnection.ADMIN)
-- ============================================================================

SET NOCOUNT ON;
GO

PRINT 'V034 — Remove cross-plane Session Store FKs (CP session → DP company)';
GO

-- ── 1/2 FK_session_empresa ──────────────────────────────────────────────────
IF EXISTS (
    SELECT 1
    FROM sys.foreign_keys fk
    INNER JOIN sys.tables t ON fk.parent_object_id = t.object_id
    WHERE fk.name = N'FK_session_empresa'
      AND t.name = N'user_session'
      AND SCHEMA_NAME(t.schema_id) = N'dbo'
)
BEGIN
    ALTER TABLE dbo.user_session DROP CONSTRAINT FK_session_empresa;
    PRINT 'Dropped FK_session_empresa on dbo.user_session';
END
ELSE
BEGIN
    PRINT 'Skip: FK_session_empresa not found on dbo.user_session';
END
GO

-- ── 2/2 FK_token_empresa ────────────────────────────────────────────────────
IF EXISTS (
    SELECT 1
    FROM sys.foreign_keys fk
    INNER JOIN sys.tables t ON fk.parent_object_id = t.object_id
    WHERE fk.name = N'FK_token_empresa'
      AND t.name = N'refresh_tokens'
      AND SCHEMA_NAME(t.schema_id) = N'dbo'
)
BEGIN
    ALTER TABLE dbo.refresh_tokens DROP CONSTRAINT FK_token_empresa;
    PRINT 'Dropped FK_token_empresa on dbo.refresh_tokens';
END
ELSE
BEGIN
    PRINT 'Skip: FK_token_empresa not found on dbo.refresh_tokens';
END
GO

-- ── Verificación post-migración ─────────────────────────────────────────────
IF EXISTS (
    SELECT 1
    FROM sys.foreign_keys fk
    INNER JOIN sys.tables tp ON fk.parent_object_id = tp.object_id
    INNER JOIN sys.tables tr ON fk.referenced_object_id = tr.object_id
    WHERE tp.name IN (N'user_session', N'token_family', N'refresh_tokens')
      AND tr.name = N'org_empresa'
      AND SCHEMA_NAME(tp.schema_id) = N'dbo'
)
BEGIN
    RAISERROR(
        'V034 VERIFICATION FAILED: FK from session tables to dbo.org_empresa still exists.',
        16, 1
    );
END
ELSE
BEGIN
    PRINT 'V034 VERIFICATION OK: no FK from session tables to dbo.org_empresa';
END
GO

-- ── Verificación: no FK cross-plane residuales (usuario + org_empresa) ───────
IF EXISTS (
    SELECT 1
    FROM sys.foreign_keys fk
    INNER JOIN sys.tables tp ON fk.parent_object_id = tp.object_id
    INNER JOIN sys.tables tr ON fk.referenced_object_id = tr.object_id
    WHERE tp.name IN (N'user_session', N'token_family', N'refresh_tokens')
      AND tr.name IN (N'usuario', N'org_empresa')
      AND SCHEMA_NAME(tp.schema_id) = N'dbo'
)
BEGIN
    RAISERROR(
        'V034 VERIFICATION FAILED: cross-plane FK from session tables still exists.',
        16, 1
    );
END
ELSE
BEGIN
    PRINT 'V034 VERIFICATION OK: session store free of CP→DP identity/company FKs';
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

PRINT 'V034 completed — remove_cross_plane_session_empresa_fks';
GO

-- ============================================================================
-- ROLLBACK MANUAL (referencia — no ejecutar en deploy automático)
--
-- ALTER TABLE dbo.user_session ADD CONSTRAINT FK_session_empresa
--     FOREIGN KEY (empresa_id) REFERENCES dbo.org_empresa(empresa_id) ON DELETE NO ACTION;
-- ALTER TABLE dbo.refresh_tokens ADD CONSTRAINT FK_token_empresa
--     FOREIGN KEY (empresa_id) REFERENCES dbo.org_empresa(empresa_id) ON DELETE NO ACTION;
-- ============================================================================
