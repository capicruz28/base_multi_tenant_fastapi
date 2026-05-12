-- ============================================================================
-- SECCIÓN 8: MRP - MATERIAL REQUIREMENTS PLANNING (PLANEAMIENTO DE MATERIALES)
-- ============================================================================
-- DESCRIPCIÓN: Planificación de necesidades de materiales
-- DEPENDENCIAS: ORG, INV, MFG (BOM, órdenes producción)
-- USADO POR: PUR (generación automática de requisiciones)
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: mrp_plan_maestro
-- Descripción: Plan maestro de producción (MPS agregado con MRP)
-- Uso: Horizonte de planificación de necesidades
-- Relaciones: Base para ejecutar explosión de materiales
-- -----------------------------------------------------------------------------
CREATE TABLE mrp_plan_maestro (
    plan_maestro_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_plan NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(255) NULL,
    
    -- Periodo de planificación
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    tipo_periodo NVARCHAR(20) DEFAULT 'semanal',              -- 'diario', 'semanal', 'mensual'
    
    -- Configuración
    horizonte_planificacion_dias INT DEFAULT 90,
    punto_reorden_dias INT DEFAULT 15,                        -- Cuándo generar orden de compra
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'borrador',                   -- 'borrador', 'calculado', 'aprobado', 'ejecutado', 'cerrado'
    fecha_calculo DATETIME NULL,
    fecha_aprobacion DATETIME NULL,
    
    -- Resultados
    total_productos_planificados INT DEFAULT 0,
    total_requisiciones_generadas INT DEFAULT 0,
    total_ordenes_sugeridas INT DEFAULT 0,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_planmrp_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_planmrp_codigo UNIQUE (cliente_id, empresa_id, codigo_plan)
);

CREATE INDEX IDX_planmrp_empresa ON mrp_plan_maestro(empresa_id, fecha_inicio DESC);
CREATE INDEX IDX_planmrp_estado ON mrp_plan_maestro(estado);

-- -----------------------------------------------------------------------------
-- Tabla: mrp_necesidad_bruta
-- Descripción: Necesidades brutas de productos (demanda + stock seguridad)
-- Uso: Entrada del MRP - qué se necesita y cuándo
-- Relaciones: Puede originarse de pedidos de venta, pronósticos, reposición
-- -----------------------------------------------------------------------------
CREATE TABLE mrp_necesidad_bruta (
    necesidad_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    plan_maestro_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    fecha_requerida DATE NOT NULL,
    cantidad_requerida DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Origen de la necesidad
    origen NVARCHAR(30) NOT NULL,                             -- 'pedido_venta', 'pronostico', 'stock_seguridad', 'orden_produccion'
    documento_origen_id UNIQUEIDENTIFIER NULL,
    documento_origen_numero NVARCHAR(30) NULL,
    
    -- Prioridad
    prioridad INT DEFAULT 3,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_necbruta_plan FOREIGN KEY (plan_maestro_id) 
        REFERENCES mrp_plan_maestro(plan_maestro_id) ON DELETE NO ACTION,
    CONSTRAINT FK_necbruta_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_necbruta_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_necbruta_plan ON mrp_necesidad_bruta(plan_maestro_id, fecha_requerida);
CREATE INDEX IDX_necbruta_producto ON mrp_necesidad_bruta(producto_id, fecha_requerida);

-- -----------------------------------------------------------------------------
-- Tabla: mrp_explosion_materiales
-- Descripción: Resultado de la explosión de BOM (necesidades de componentes)
-- Uso: Cálculo de qué materiales se necesitan para producir
-- Relaciones: Generado automáticamente desde BOM y necesidades brutas
-- -----------------------------------------------------------------------------
CREATE TABLE mrp_explosion_materiales (
    explosion_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    plan_maestro_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Producto padre (lo que se va a producir)
    producto_padre_id UNIQUEIDENTIFIER NOT NULL,
    necesidad_padre_id UNIQUEIDENTIFIER NULL,                 -- FK a mrp_necesidad_bruta
    
    -- Componente (material que se necesita)
    producto_componente_id UNIQUEIDENTIFIER NOT NULL,
    bom_detalle_id UNIQUEIDENTIFIER NULL,                     -- De dónde salió la necesidad
    
    -- Nivel en BOM
    nivel_bom INT DEFAULT 1,                                   -- 1=componente directo, 2=sub-componente, etc
    
    -- Cantidad
    cantidad_necesaria DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Fecha requerida
    fecha_requerida DATE NOT NULL,
    
    -- Stock disponible
    stock_actual DECIMAL(18,4) DEFAULT 0,
    stock_reservado DECIMAL(18,4) DEFAULT 0,
    stock_transito DECIMAL(18,4) DEFAULT 0,
    stock_disponible AS (stock_actual - stock_reservado + stock_transito) PERSISTED,
    
    -- Necesidad neta
    cantidad_a_ordenar AS (
        CASE 
            WHEN cantidad_necesaria > (stock_actual - stock_reservado + stock_transito)
            THEN cantidad_necesaria - (stock_actual - stock_reservado + stock_transito)
            ELSE 0
        END
    ) PERSISTED,
    
    -- Auditoría
    fecha_calculo DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_explosion_plan FOREIGN KEY (plan_maestro_id) 
        REFERENCES mrp_plan_maestro(plan_maestro_id) ON DELETE NO ACTION,
    CONSTRAINT FK_explosion_padre FOREIGN KEY (producto_padre_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_explosion_componente FOREIGN KEY (producto_componente_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_explosion_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_explosion_plan ON mrp_explosion_materiales(plan_maestro_id, nivel_bom);
CREATE INDEX IDX_explosion_componente ON mrp_explosion_materiales(producto_componente_id, fecha_requerida);

-- -----------------------------------------------------------------------------
-- Tabla: mrp_orden_sugerida
-- Descripción: Órdenes de compra o producción sugeridas por MRP
-- Uso: Recomendaciones del sistema para cubrir necesidades
-- Relaciones: Se pueden convertir en órdenes de compra o producción reales
-- -----------------------------------------------------------------------------
CREATE TABLE mrp_orden_sugerida (
    orden_sugerida_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    plan_maestro_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    tipo_orden NVARCHAR(20) NOT NULL,                         -- 'compra', 'produccion', 'transferencia'
    
    cantidad_sugerida DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    fecha_requerida DATE NOT NULL,
    fecha_orden_sugerida DATE NOT NULL,                       -- Cuándo se debe ordenar (considerando lead time)
    
    -- Origen de la sugerencia
    explosion_materiales_id UNIQUEIDENTIFIER NULL,
    
    -- Proveedor sugerido (si es compra)
    proveedor_sugerido_id UNIQUEIDENTIFIER NULL,
    
    -- Lead time
    lead_time_dias INT NULL,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'sugerida',                   -- 'sugerida', 'aprobada', 'convertida', 'rechazada'
    
    -- Conversión a documento real
    documento_generado_tipo NVARCHAR(20) NULL,                -- 'orden_compra', 'orden_produccion'
    documento_generado_id UNIQUEIDENTIFIER NULL,
    fecha_conversion DATETIME NULL,
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_ordsug_plan FOREIGN KEY (plan_maestro_id) 
        REFERENCES mrp_plan_maestro(plan_maestro_id) ON DELETE NO ACTION,
    CONSTRAINT FK_ordsug_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_ordsug_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT FK_ordsug_prov FOREIGN KEY (proveedor_sugerido_id) 
        REFERENCES pur_proveedor(proveedor_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_ordsug_plan ON mrp_orden_sugerida(plan_maestro_id, estado);
CREATE INDEX IDX_ordsug_producto ON mrp_orden_sugerida(producto_id, fecha_requerida);
CREATE INDEX IDX_ordsug_estado ON mrp_orden_sugerida(estado, tipo_orden);