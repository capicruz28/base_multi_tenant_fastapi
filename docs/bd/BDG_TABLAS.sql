-- ============================================================================
-- SECCIÓN 19: BDG - PRESUPUESTOS
-- ============================================================================
-- DESCRIPCIÓN: Gestión de presupuestos por centro de costo y cuenta
-- DEPENDENCIAS: ORG, FIN
-- USADO POR: Control presupuestario
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: bdg_presupuesto
-- Descripción: Presupuesto anual o por periodo
-- Uso: Cabecera de presupuesto
-- Relaciones: Control financiero
-- -----------------------------------------------------------------------------
CREATE TABLE bdg_presupuesto (
    presupuesto_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_presupuesto NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    
    año INT NOT NULL,
    tipo_presupuesto NVARCHAR(20) DEFAULT 'anual',            -- 'anual', 'mensual', 'trimestral'
    
    -- Montos
    monto_total_presupuestado DECIMAL(18,2) DEFAULT 0,
    monto_total_ejecutado DECIMAL(18,2) DEFAULT 0,
    porcentaje_ejecucion AS (
        CASE 
            WHEN monto_total_presupuestado > 0 
            THEN (monto_total_ejecutado / monto_total_presupuestado) * 100
            ELSE 0
        END
    ) PERSISTED,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'borrador',                   -- 'borrador', 'aprobado', 'vigente', 'cerrado'
    fecha_aprobacion DATETIME NULL,
    
    observaciones NVARCHAR(MAX) NULL,
    
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_bdg_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_bdg_codigo UNIQUE (cliente_id, empresa_id, codigo_presupuesto)
);

CREATE INDEX IDX_bdg_empresa ON bdg_presupuesto(empresa_id, año DESC);

-- -----------------------------------------------------------------------------
-- Tabla: bdg_presupuesto_detalle
-- Descripción: Presupuesto por cuenta contable y centro de costo
-- Uso: Asignación presupuestal detallada
-- Relaciones: Detalle de bdg_presupuesto
-- -----------------------------------------------------------------------------
CREATE TABLE bdg_presupuesto_detalle (
    presupuesto_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    presupuesto_id UNIQUEIDENTIFIER NOT NULL,
    
    cuenta_id UNIQUEIDENTIFIER NOT NULL,
    centro_costo_id UNIQUEIDENTIFIER NULL,
    
    mes INT NULL,                                              -- NULL si es anual consolidado
    
    monto_presupuestado DECIMAL(18,2) NOT NULL,
    monto_ejecutado DECIMAL(18,2) DEFAULT 0,
    monto_disponible AS (monto_presupuestado - monto_ejecutado) PERSISTED,
    
    observaciones NVARCHAR(255) NULL,
    
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_bdgdet_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_bdgdet_presupuesto FOREIGN KEY (presupuesto_id) 
        REFERENCES bdg_presupuesto(presupuesto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_bdgdet_cuenta FOREIGN KEY (cuenta_id) 
        REFERENCES fin_plan_cuentas(cuenta_id) ON DELETE NO ACTION,
    CONSTRAINT FK_bdgdet_cc FOREIGN KEY (centro_costo_id) 
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_bdgdet_empresa ON bdg_presupuesto_detalle(empresa_id);
CREATE INDEX IDX_bdgdet_presupuesto ON bdg_presupuesto_detalle(presupuesto_id);