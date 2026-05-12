-- -----------------------------------------------------------------------------
-- Tabla: tkt_ticket (Mesa de Ayuda / Ticketing)
-- -----------------------------------------------------------------------------
CREATE TABLE tkt_ticket (
    ticket_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_ticket NVARCHAR(20) NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    solicitante_usuario_id UNIQUEIDENTIFIER NULL,
    solicitante_nombre NVARCHAR(150) NULL,
    solicitante_email NVARCHAR(100) NULL,
    
    asunto NVARCHAR(200) NOT NULL,
    descripcion NVARCHAR(MAX) NULL,
    
    categoria NVARCHAR(50) NULL,                              -- 'soporte_tecnico', 'consulta', 'incidencia', 'requerimiento'
    prioridad NVARCHAR(20) DEFAULT 'media',                   -- 'urgente', 'alta', 'media', 'baja'
    
    asignado_usuario_id UNIQUEIDENTIFIER NULL,
    fecha_asignacion DATETIME NULL,
    
    estado NVARCHAR(20) DEFAULT 'abierto',                    -- 'abierto', 'asignado', 'en_proceso', 'resuelto', 'cerrado'
    
    fecha_resolucion DATETIME NULL,
    tiempo_resolucion_horas AS (
        CASE 
            WHEN fecha_resolucion IS NOT NULL 
            THEN DATEDIFF(HOUR, fecha_creacion, fecha_resolucion)
            ELSE NULL
        END
    ) PERSISTED,
    
    solucion NVARCHAR(MAX) NULL,
    
    CONSTRAINT FK_tkt_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_tkt_numero UNIQUE (cliente_id, empresa_id, numero_ticket)
);

CREATE INDEX IDX_tkt_empresa ON tkt_ticket(empresa_id, fecha_creacion DESC);
CREATE INDEX IDX_tkt_estado ON tkt_ticket(estado, prioridad);