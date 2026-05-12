-- ============================================================================
-- SECCIÓN 13: PRC - GESTIÓN DE PRECIOS Y TARIFAS
-- ============================================================================
-- DESCRIPCIÓN: Gestión de listas de precios, descuentos, promociones
-- DEPENDENCIAS: ORG, INV (productos)
-- USADO POR: SLS (cotizaciones, pedidos), POS
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: prc_lista_precio
-- Descripción: Listas de precios (tarifarios)
-- Uso: Diferentes estructuras de precios por segmento/canal
-- Relaciones: Asignada a clientes, usada en ventas
-- -----------------------------------------------------------------------------
CREATE TABLE prc_lista_precio (
    lista_precio_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_lista NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(255) NULL,
    
    -- Aplicabilidad
    tipo_lista NVARCHAR(30) DEFAULT 'general',                -- 'general', 'mayorista', 'minorista', 'distribuidor', 'corporativo'
    moneda_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Vigencia
    fecha_vigencia_desde DATE NOT NULL,
    fecha_vigencia_hasta DATE NULL,
    
    -- Configuración de precios
    incluye_igv BIT DEFAULT 1,                                -- Si precios incluyen IGV
    permite_descuentos BIT DEFAULT 1,
    descuento_maximo_porcentaje DECIMAL(5,2) DEFAULT 10,
    
    -- Estado
    es_lista_defecto BIT DEFAULT 0,
    es_activo BIT DEFAULT 1 NOT NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_listaprc_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_listaprc_codigo UNIQUE (cliente_id, empresa_id, codigo_lista),
    CONSTRAINT FK_listaprc_moneda FOREIGN KEY (moneda_id)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_listaprc_empresa ON prc_lista_precio(empresa_id, es_activo);
CREATE INDEX IDX_listaprc_vigencia ON prc_lista_precio(fecha_vigencia_desde, fecha_vigencia_hasta);

-- -----------------------------------------------------------------------------
-- Tabla: prc_lista_precio_detalle
-- Descripción: Precios por producto en cada lista
-- Uso: Precio específico de cada producto en la lista
-- Relaciones: Detalle de prc_lista_precio
-- -----------------------------------------------------------------------------
CREATE TABLE prc_lista_precio_detalle (
    lista_precio_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    lista_precio_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Precio
    precio_unitario DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Precio escalonado (por cantidad)
    cantidad_minima DECIMAL(18,4) DEFAULT 1,
    cantidad_maxima DECIMAL(18,4) NULL,
    
    -- Descuento máximo permitido para este producto
    descuento_maximo_porcentaje DECIMAL(5,2) NULL,
    
    -- Vigencia específica del producto (puede diferir de la lista)
    fecha_vigencia_desde DATE NULL,
    fecha_vigencia_hasta DATE NULL,
    
    -- Estado
    es_activo BIT DEFAULT 1 NOT NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    
    CONSTRAINT FK_listadet_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_listadet_lista FOREIGN KEY (lista_precio_id) 
        REFERENCES prc_lista_precio(lista_precio_id) ON DELETE NO ACTION,
    CONSTRAINT FK_listadet_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_listadet_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_listadet_empresa ON prc_lista_precio_detalle(empresa_id);
CREATE INDEX IDX_listadet_lista ON prc_lista_precio_detalle(lista_precio_id, es_activo);
CREATE INDEX IDX_listadet_producto ON prc_lista_precio_detalle(producto_id, lista_precio_id);

-- -----------------------------------------------------------------------------
-- Tabla: prc_promocion
-- Descripción: Promociones y ofertas especiales
-- Uso: Descuentos temporales por campaña
-- Relaciones: Aplicable a productos, categorías o toda la venta
-- -----------------------------------------------------------------------------
CREATE TABLE prc_promocion (
    promocion_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_promocion NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(500) NULL,
    
    -- Tipo de promoción
    tipo_promocion NVARCHAR(30) NOT NULL,                     -- 'descuento_porcentaje', 'descuento_monto', '2x1', '3x2', 'producto_gratis'
    
    -- Aplicabilidad
    aplica_a NVARCHAR(20) NOT NULL,                           -- 'producto', 'categoria', 'marca', 'toda_venta'
    producto_id UNIQUEIDENTIFIER NULL,
    categoria_id UNIQUEIDENTIFIER NULL,
    marca NVARCHAR(100) NULL,
    
    -- Descuento
    descuento_porcentaje DECIMAL(5,2) NULL,
    descuento_monto DECIMAL(18,2) NULL,
    
    -- Reglas (JSON para configuraciones complejas)
    reglas_aplicacion NVARCHAR(MAX) NULL,                     -- Ej: {"cantidad_minima": 3, "producto_gratis_id": "xxx"}
    
    -- Vigencia
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    
    -- Límites
    cantidad_maxima_usos INT NULL,                            -- Máximo de veces que se puede usar
    cantidad_usos_actuales INT DEFAULT 0,
    monto_maximo_descuento DECIMAL(18,2) NULL,
    
    -- Combinable con otras promociones
    es_combinable BIT DEFAULT 0,
    
    -- Canales
    aplica_canal_venta NVARCHAR(MAX) NULL,                    -- JSON: ["tienda", "online", "telefono"]
    
    -- Estado
    es_activo BIT DEFAULT 1 NOT NULL,
    requiere_codigo_cupon BIT DEFAULT 0,
    codigo_cupon NVARCHAR(30) NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_promo_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_promo_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_promo_categoria FOREIGN KEY (categoria_id) 
        REFERENCES inv_categoria_producto(categoria_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_promo_codigo UNIQUE (cliente_id, empresa_id, codigo_promocion)
);

CREATE INDEX IDX_promo_empresa ON prc_promocion(empresa_id, es_activo);
CREATE INDEX IDX_promo_vigencia ON prc_promocion(fecha_inicio, fecha_fin, es_activo);
CREATE INDEX IDX_promo_producto ON prc_promocion(producto_id) WHERE producto_id IS NOT NULL;