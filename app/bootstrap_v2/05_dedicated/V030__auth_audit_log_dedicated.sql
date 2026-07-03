-- ============================================================================
-- bootstrap_v2 | official bootstrap line — Dedicated Tenant Audit Store
-- PR-F12-G3 — auth_audit_log en Data Plane (paridad V020 §3, sin FK → cliente CP)
-- PREREQUISITO: V010 ERP (org_empresa) + V020 DTSP (usuario)
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'auth_audit_log')
BEGIN
    CREATE TABLE auth_audit_log (
        log_id UNIQUEIDENTIFIER NOT NULL
            CONSTRAINT PK_auth_audit_log PRIMARY KEY DEFAULT NEWID(),
        cliente_id UNIQUEIDENTIFIER NOT NULL,
        empresa_id UNIQUEIDENTIFIER NULL,
        usuario_id UNIQUEIDENTIFIER NULL,
        evento NVARCHAR(50) NOT NULL,
        nombre_usuario_intento NVARCHAR(100) NULL,
        descripcion NVARCHAR(500) NULL,
        exito BIT NOT NULL,
        codigo_error NVARCHAR(50) NULL,
        ip_address VARCHAR(45) NULL,
        user_agent VARCHAR(500) NULL,
        device_info NVARCHAR(200) NULL,
        geolocation NVARCHAR(100) NULL,
        metadata_json NVARCHAR(MAX) NULL,
        fecha_evento DATETIME NOT NULL CONSTRAINT DF_auth_audit_log_fecha_evento
            DEFAULT GETDATE(),
        CONSTRAINT FK_audit_usuario FOREIGN KEY (usuario_id)
            REFERENCES usuario(usuario_id) ON DELETE NO ACTION,
        CONSTRAINT FK_audit_empresa FOREIGN KEY (empresa_id)
            REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION
    );
    PRINT 'Tabla auth_audit_log creada en BD dedicada (runtime audit store).';
END
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IDX_audit_cliente_fecha' AND object_id = OBJECT_ID(N'dbo.auth_audit_log')
)
    CREATE INDEX IDX_audit_cliente_fecha ON auth_audit_log(cliente_id, fecha_evento DESC);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IDX_audit_usuario_fecha' AND object_id = OBJECT_ID(N'dbo.auth_audit_log')
)
    CREATE INDEX IDX_audit_usuario_fecha ON auth_audit_log(usuario_id, fecha_evento DESC)
        WHERE usuario_id IS NOT NULL;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IDX_audit_evento' AND object_id = OBJECT_ID(N'dbo.auth_audit_log')
)
    CREATE INDEX IDX_audit_evento ON auth_audit_log(evento, fecha_evento DESC);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IDX_audit_exito' AND object_id = OBJECT_ID(N'dbo.auth_audit_log')
)
    CREATE INDEX IDX_audit_exito ON auth_audit_log(exito, fecha_evento DESC);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IDX_audit_ip' AND object_id = OBJECT_ID(N'dbo.auth_audit_log')
)
    CREATE INDEX IDX_audit_ip ON auth_audit_log(ip_address, fecha_evento DESC)
        WHERE ip_address IS NOT NULL;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IDX_audit_empresa' AND object_id = OBJECT_ID(N'dbo.auth_audit_log')
)
    CREATE INDEX IDX_audit_empresa ON auth_audit_log(empresa_id, fecha_evento DESC)
        WHERE empresa_id IS NOT NULL;
GO
