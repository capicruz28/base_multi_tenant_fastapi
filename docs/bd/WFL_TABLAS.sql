-- -----------------------------------------------------------------------------
-- Tabla: wfl_flujo_trabajo (Workflow Engine)
-- -----------------------------------------------------------------------------
CREATE TABLE wfl_flujo_trabajo (
    flujo_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_flujo NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(150) NOT NULL,
    descripcion NVARCHAR(500) NULL,
    
    tipo_flujo NVARCHAR(30) NOT NULL,                         -- 'aprobacion', 'revision', 'notificacion'
    modulo_aplicable NVARCHAR(10) NULL,                       -- Módulo donde aplica
    
    -- Definición del flujo (JSON)
    definicion_pasos NVARCHAR(MAX) NULL,                      -- JSON con pasos del workflow
    
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_wfl_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_wfl_codigo UNIQUE (cliente_id, empresa_id, codigo_flujo)
);
