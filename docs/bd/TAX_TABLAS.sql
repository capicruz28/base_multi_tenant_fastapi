-- ============================================================================
-- SECCIÓN 18: TAX - GESTIÓN TRIBUTARIA
-- ============================================================================
-- DESCRIPCIÓN: Obligaciones tributarias, declaraciones, libros electrónicos
-- DEPENDENCIAS: FIN, INV_BILL
-- USADO POR: Reportes a SUNAT, cumplimiento tributario
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: tax_libro_electronico
-- Descripción: Libros electrónicos (ventas, compras, diario, mayor)
-- Uso: Generación de libros para PLE SUNAT
-- Relaciones: Consolida información contable y tributaria
-- -----------------------------------------------------------------------------
CREATE TABLE tax_libro_electronico (
    libro_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    tipo_libro NVARCHAR(30) NOT NULL,                         -- 'ventas', 'compras', 'diario', 'mayor', 'inventarios'
    periodo_id UNIQUEIDENTIFIER NOT NULL,
    
    año INT NOT NULL,
    mes INT NOT NULL,
    
    fecha_generacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    -- Archivo PLE
    nombre_archivo NVARCHAR(255) NULL,
    ruta_archivo NVARCHAR(500) NULL,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'generado',                   -- 'generado', 'enviado', 'aceptado', 'rechazado'
    fecha_envio_sunat DATETIME NULL,
    codigo_respuesta_sunat NVARCHAR(10) NULL,
    
    -- Totales (para validación)
    total_registros INT DEFAULT 0,
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    generado_por_usuario_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_libro_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_libro_periodo FOREIGN KEY (periodo_id) 
        REFERENCES fin_periodo_contable(periodo_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_libro_empresa ON tax_libro_electronico(empresa_id, año DESC, mes DESC);
CREATE INDEX IDX_libro_tipo ON tax_libro_electronico(tipo_libro, año, mes);