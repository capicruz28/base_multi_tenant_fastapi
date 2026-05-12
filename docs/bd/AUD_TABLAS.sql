-- -----------------------------------------------------------------------------
-- Tabla: aud_log_auditoria (Sistema de Auditoría)
-- -----------------------------------------------------------------------------
CREATE TABLE aud_log_auditoria (
    log_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    fecha_evento DATETIME DEFAULT GETDATE() NOT NULL,
    
    usuario_id UNIQUEIDENTIFIER NULL,
    usuario_nombre NVARCHAR(150) NULL,
    
    -- Acción
    modulo NVARCHAR(10) NOT NULL,
    tabla NVARCHAR(100) NOT NULL,
    accion NVARCHAR(20) NOT NULL,                             -- 'INSERT', 'UPDATE', 'DELETE', 'SELECT'
    
    -- Registro afectado
    registro_id UNIQUEIDENTIFIER NULL,
    registro_descripcion NVARCHAR(255) NULL,
    
    -- Valores
    valores_anteriores NVARCHAR(MAX) NULL,                    -- JSON
    valores_nuevos NVARCHAR(MAX) NULL,                        -- JSON
    
    -- Metadata
    ip_address NVARCHAR(45) NULL,
    user_agent NVARCHAR(500) NULL,
    
    observaciones NVARCHAR(500) NULL,
    
    CONSTRAINT FK_aud_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_aud_empresa ON aud_log_auditoria(empresa_id, fecha_evento DESC);
CREATE INDEX IDX_aud_modulo ON aud_log_auditoria(modulo, tabla, fecha_evento DESC);
CREATE INDEX IDX_aud_usuario ON aud_log_auditoria(usuario_id, fecha_evento DESC) WHERE usuario_id IS NOT NULL;
CREATE INDEX IDX_aud_accion ON aud_log_auditoria(accion, fecha_evento DESC);