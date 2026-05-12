-- -----------------------------------------------------------------------------
-- Tabla: dms_documento (Document Management System)
-- -----------------------------------------------------------------------------
CREATE TABLE dms_documento (
    documento_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_documento NVARCHAR(20) NULL,
    nombre_archivo NVARCHAR(255) NOT NULL,
    descripcion NVARCHAR(500) NULL,
    
    tipo_documento NVARCHAR(50) NOT NULL,                     -- 'contrato', 'factura', 'reporte', 'certificado', etc
    categoria NVARCHAR(50) NULL,
    
    ruta_archivo NVARCHAR(500) NOT NULL,
    tamaño_bytes BIGINT NULL,
    extension NVARCHAR(10) NULL,
    mime_type NVARCHAR(100) NULL,
    
    -- Clasificación
    carpeta NVARCHAR(255) NULL,
    tags NVARCHAR(MAX) NULL,                                  -- JSON array
    
    -- Relación con entidades
    entidad_tipo NVARCHAR(30) NULL,                           -- 'cliente', 'empleado', 'producto', 'proyecto'
    entidad_id UNIQUEIDENTIFIER NULL,
    
    -- Versionamiento
    version NVARCHAR(10) DEFAULT '1.0',
    documento_padre_id UNIQUEIDENTIFIER NULL,                 -- Si es versión de otro
    
    -- Seguridad
    es_confidencial BIT DEFAULT 0,
    nivel_acceso NVARCHAR(20) DEFAULT 'general',              -- 'publico', 'general', 'restringido', 'confidencial'
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'activo',                     -- 'activo', 'archivado', 'eliminado'
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_modificacion DATETIME NULL,
    subido_por_usuario_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_dms_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_dms_padre FOREIGN KEY (documento_padre_id) 
        REFERENCES dms_documento(documento_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_dms_empresa ON dms_documento(empresa_id, fecha_creacion DESC);
CREATE INDEX IDX_dms_tipo ON dms_documento(tipo_documento, categoria);