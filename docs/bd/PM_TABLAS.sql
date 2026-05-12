-- -----------------------------------------------------------------------------
-- Tabla: pm_proyecto (Gestión de Proyectos)
-- -----------------------------------------------------------------------------
CREATE TABLE pm_proyecto (
    proyecto_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_proyecto NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(150) NOT NULL,
    descripcion NVARCHAR(MAX) NULL,
    
    cliente_venta_id UNIQUEIDENTIFIER NULL,
    
    fecha_inicio DATE NOT NULL,
    fecha_fin_estimada DATE NULL,
    fecha_fin_real DATE NULL,
    
    presupuesto DECIMAL(18,2) NULL,
    costo_real DECIMAL(18,2) DEFAULT 0,
    
    responsable_usuario_id UNIQUEIDENTIFIER NULL,
    
    estado NVARCHAR(20) DEFAULT 'planificado',                -- 'planificado', 'en_curso', 'pausado', 'completado', 'cancelado'
    
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_proy_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_proy_codigo UNIQUE (cliente_id, empresa_id, codigo_proyecto)
);
