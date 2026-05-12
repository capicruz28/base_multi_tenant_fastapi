-- ============================================================================
-- SECCIÓN 9: MPS - MASTER PRODUCTION SCHEDULE (PLAN MAESTRO DE PRODUCCIÓN)
-- ============================================================================
-- DESCRIPCIÓN: Planificación agregada de producción
-- DEPENDENCIAS: ORG, INV, MFG
-- USADO POR: MRP (entrada para explosión de materiales)
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: mps_pronostico_demanda
-- Descripción: Pronósticos de ventas/demanda
-- Uso: Estimación de demanda futura para planificar producción
-- Relaciones: Base para el MPS
-- -----------------------------------------------------------------------------
CREATE TABLE mps_pronostico_demanda (
    pronostico_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Periodo
    año INT NOT NULL,
    mes INT NOT NULL,
    semana INT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    
    -- Demanda pronosticada
    cantidad_pronosticada DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Método de pronóstico
    metodo_pronostico NVARCHAR(30) NULL,                      -- 'historico', 'tendencia', 'estacional', 'manual'
    confiabilidad_porcentaje DECIMAL(5,2) NULL,               -- % de confianza en el pronóstico
    
    -- Demanda real (para análisis posterior)
    cantidad_real DECIMAL(18,4) NULL,
    desviacion AS (cantidad_real - cantidad_pronosticada) PERSISTED,
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_pronos_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_pronos_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_pronos_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_pronos_empresa ON mps_pronostico_demanda(empresa_id, año DESC, mes DESC);
CREATE INDEX IDX_pronos_producto ON mps_pronostico_demanda(producto_id, fecha_inicio);

-- -----------------------------------------------------------------------------
-- Tabla: mps_plan_produccion
-- Descripción: Plan maestro de producción (MPS)
-- Uso: Qué, cuánto y cuándo producir a nivel agregado
-- Relaciones: Entrada principal para MRP
-- -----------------------------------------------------------------------------
CREATE TABLE mps_plan_produccion (
    plan_produccion_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_plan NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    
    -- Periodo
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'borrador',                   -- 'borrador', 'aprobado', 'ejecutado', 'cerrado'
    fecha_aprobacion DATETIME NULL,
    aprobado_por_usuario_id UNIQUEIDENTIFIER NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_planprod_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_planprod_codigo UNIQUE (cliente_id, empresa_id, codigo_plan)
);

CREATE INDEX IDX_planprod_empresa ON mps_plan_produccion(empresa_id, fecha_inicio DESC);
CREATE INDEX IDX_planprod_estado ON mps_plan_produccion(estado);

-- -----------------------------------------------------------------------------
-- Tabla: mps_plan_produccion_detalle
-- Descripción: Detalle del MPS por producto y periodo
-- Uso: Cantidades específicas a producir por periodo
-- Relaciones: Detalle de plan de producción
-- -----------------------------------------------------------------------------
CREATE TABLE mps_plan_produccion_detalle (
    plan_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    plan_produccion_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Periodo
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    
    -- Cantidades
    pronostico_demanda DECIMAL(18,4) DEFAULT 0,               -- Demanda esperada
    pedidos_firmes DECIMAL(18,4) DEFAULT 0,                   -- Pedidos confirmados
    stock_inicial DECIMAL(18,4) DEFAULT 0,
    stock_seguridad DECIMAL(18,4) DEFAULT 0,
    cantidad_planificada DECIMAL(18,4) NOT NULL,              -- Cantidad a producir
    cantidad_producida DECIMAL(18,4) DEFAULT 0,               -- Real producido
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Capacidad
    capacidad_disponible DECIMAL(18,4) NULL,
    porcentaje_uso_capacidad AS (
        CASE 
            WHEN capacidad_disponible > 0 
            THEN (cantidad_planificada / capacidad_disponible) * 100
            ELSE 0
        END
    ) PERSISTED,
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_planproddet_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_planproddet_plan FOREIGN KEY (plan_produccion_id) 
        REFERENCES mps_plan_produccion(plan_produccion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_planproddet_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_planproddet_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_planproddet_empresa ON mps_plan_produccion_detalle(empresa_id);
CREATE INDEX IDX_planproddet_plan ON mps_plan_produccion_detalle(plan_produccion_id, fecha_inicio);
CREATE INDEX IDX_planproddet_producto ON mps_plan_produccion_detalle(producto_id, fecha_inicio);