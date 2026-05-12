-- -----------------------------------------------------------------------------
-- Tabla: bi_reporte (Business Intelligence - Reportes Personalizados)
-- -----------------------------------------------------------------------------
CREATE TABLE bi_reporte (
    reporte_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_reporte NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(150) NOT NULL,
    descripcion NVARCHAR(500) NULL,
    
    modulo_origen NVARCHAR(10) NULL,                          -- Módulo al que pertenece
    categoria NVARCHAR(50) NULL,                              -- 'ventas', 'inventarios', 'finanzas', etc
    
    tipo_reporte NVARCHAR(20) DEFAULT 'sql',                  -- 'sql', 'olap', 'dashboard'
    
    query_sql NVARCHAR(MAX) NULL,                             -- Query personalizado
    configuracion_json NVARCHAR(MAX) NULL,                    -- Configuración de gráficos, filtros
    
    es_publico BIT DEFAULT 0,                                 -- Si está disponible para todos
    creado_por_usuario_id UNIQUEIDENTIFIER NULL,
    
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_bi_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_bi_codigo UNIQUE (cliente_id, empresa_id, codigo_reporte)
);