-- ============================================================================
-- SECCIÓN 20: CST - COSTOS Y COSTEO
-- ============================================================================
-- DESCRIPCIÓN: Costeo de productos, centros de costo, distribución de gastos
-- DEPENDENCIAS: ORG, INV, MFG, HCM, FIN
-- USADO POR: Análisis de rentabilidad, toma de decisiones
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: cst_centro_costo_tipo
-- Descripción: Tipos de centros de costo para distribución
-- Uso: Clasificación para distribución de costos indirectos
-- Relaciones: Extiende org_centro_costo
-- -----------------------------------------------------------------------------
CREATE TABLE cst_centro_costo_tipo (
    cc_tipo_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    
    tipo_clasificacion NVARCHAR(30) NOT NULL,                 -- 'productivo', 'servicio', 'administrativo'
    
    -- Distribución
    base_distribucion NVARCHAR(30) NULL,                      -- 'horas_hombre', 'unidades_producidas', 'ventas', 'area_m2'
    
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_cctipo_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_cctipo_codigo UNIQUE (cliente_id, empresa_id, codigo)
);

CREATE INDEX IDX_cctipo_empresa ON cst_centro_costo_tipo(empresa_id, es_activo);

-- -----------------------------------------------------------------------------
-- Tabla: cst_producto_costo
-- Descripción: Costeo detallado de productos
-- Uso: Cálculo de costo por producto (materiales, mano de obra, CIF)
-- Relaciones: Vinculado a productos, órdenes de producción
-- -----------------------------------------------------------------------------
CREATE TABLE cst_producto_costo (
    producto_costo_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Periodo
    año INT NOT NULL,
    mes INT NOT NULL,
    
    -- Costos
    costo_material_directo DECIMAL(18,4) DEFAULT 0,
    costo_mano_obra_directa DECIMAL(18,4) DEFAULT 0,
    costo_indirecto_fabricacion DECIMAL(18,4) DEFAULT 0,
    costo_total AS (costo_material_directo + costo_mano_obra_directa + costo_indirecto_fabricacion) PERSISTED,
    
    -- Cantidad producida
    cantidad_producida DECIMAL(18,4) DEFAULT 0,
    costo_unitario AS (
        CASE 
            WHEN cantidad_producida > 0 
            THEN (costo_material_directo + costo_mano_obra_directa + costo_indirecto_fabricacion) / cantidad_producida
            ELSE 0
        END
    ) PERSISTED,
    
    -- Referencia
    orden_produccion_id UNIQUEIDENTIFIER NULL,
    
    -- Método de costeo
    metodo_costeo NVARCHAR(20) DEFAULT 'real',                -- 'real', 'estandar', 'promedio'
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_calculo DATETIME DEFAULT GETDATE(),
    
    CONSTRAINT FK_prodcst_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_prodcst_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_prodcst_producto ON cst_producto_costo(producto_id, año DESC, mes DESC);