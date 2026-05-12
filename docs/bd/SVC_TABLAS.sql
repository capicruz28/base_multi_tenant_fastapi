-- -----------------------------------------------------------------------------
-- Tabla: svc_orden_servicio (Gestión de Servicios)
-- -----------------------------------------------------------------------------
CREATE TABLE svc_orden_servicio (
    orden_servicio_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_os NVARCHAR(20) NOT NULL,
    fecha_solicitud DATETIME DEFAULT GETDATE() NOT NULL,
    
    cliente_venta_id UNIQUEIDENTIFIER NULL,
    tipo_servicio NVARCHAR(50) NOT NULL,
    descripcion_servicio NVARCHAR(MAX) NULL,
    
    tecnico_asignado_usuario_id UNIQUEIDENTIFIER NULL,
    
    fecha_inicio_programada DATETIME NULL,
    fecha_inicio_real DATETIME NULL,
    fecha_fin_real DATETIME NULL,
    
    estado NVARCHAR(20) DEFAULT 'solicitada',                 -- 'solicitada', 'asignada', 'en_proceso', 'completada', 'cancelada'
    
    monto_servicio DECIMAL(18,2) NULL,
    
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_os_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_os_numero UNIQUE (cliente_id, empresa_id, numero_os)
);