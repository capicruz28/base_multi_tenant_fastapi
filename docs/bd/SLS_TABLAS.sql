-- ============================================================================
-- SECCIÓN 11: SLS - VENTAS
-- ============================================================================
-- DESCRIPCIÓN: Gestión de ventas, pedidos, cotizaciones a clientes
-- DEPENDENCIAS: ORG, INV (productos, stock)
-- USADO POR: INV (salidas), FIN (cuentas por cobrar), LOG (despachos)
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: sls_cliente
-- Descripción: Catálogo de clientes
-- Uso: Maestro de clientes que compran productos/servicios
-- Relaciones: Usado en cotizaciones, pedidos, facturas
-- -----------------------------------------------------------------------------
CREATE TABLE sls_cliente (
    cliente_venta_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,                     -- Tenant
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Identificación
    codigo_cliente NVARCHAR(20) NOT NULL,
    tipo_cliente NVARCHAR(20) DEFAULT 'empresa',              -- 'empresa', 'persona'
    razon_social NVARCHAR(200) NOT NULL,
    nombre_comercial NVARCHAR(150) NULL,
    
    -- Documento tributario
    tipo_documento NVARCHAR(10) DEFAULT 'RUC',                -- 'RUC', 'DNI', 'CE', 'PASAPORTE'
    numero_documento NVARCHAR(20) NOT NULL,
    
    -- Clasificación
    categoria_cliente NVARCHAR(50) NULL,                      -- 'mayorista', 'minorista', 'corporativo', 'gobierno'
    segmento NVARCHAR(50) NULL,                               -- 'A', 'B', 'C' o personalizado
    canal_venta NVARCHAR(30) NULL,                            -- 'directo', 'distribuidor', 'online', 'retail'
    
    -- Dirección fiscal
    direccion NVARCHAR(255) NULL,
    pais_id UNIQUEIDENTIFIER NULL,
    departamento_id UNIQUEIDENTIFIER NULL,
    provincia_id UNIQUEIDENTIFIER NULL,
    distrito_id UNIQUEIDENTIFIER NULL,
    ubigeo NVARCHAR(6) NULL,
    
    -- Contacto principal
    contacto_nombre NVARCHAR(150) NULL,
    contacto_cargo NVARCHAR(100) NULL,
    telefono_principal NVARCHAR(20) NULL,
    telefono_secundario NVARCHAR(20) NULL,
    email_principal NVARCHAR(100) NULL,
    email_facturacion NVARCHAR(100) NULL,
    sitio_web NVARCHAR(255) NULL,
    
    -- Condiciones comerciales
    condicion_pago_defecto NVARCHAR(50) DEFAULT 'contado',    -- 'contado', '15_dias', '30_dias', '60_dias'
    dias_credito_defecto INT DEFAULT 0,
    moneda_preferida UNIQUEIDENTIFIER NOT NULL,
    lista_precio_id UNIQUEIDENTIFIER NULL,                    -- FK a prc_lista_precio
    
    -- Límites
    limite_credito DECIMAL(18,2) NULL,
    saldo_pendiente DECIMAL(18,2) DEFAULT 0,
    saldo_vencido DECIMAL(18,2) DEFAULT 0,
    
    -- Vendedor asignado
    vendedor_usuario_id UNIQUEIDENTIFIER NULL,
    vendedor_nombre NVARCHAR(150) NULL,
    
    -- Datos bancarios (para devoluciones)
    banco NVARCHAR(100) NULL,
    numero_cuenta NVARCHAR(30) NULL,
    
    -- Calificación
    calificacion DECIMAL(3,2) NULL,                           -- 0.00 a 5.00
    nivel_riesgo NVARCHAR(20) DEFAULT 'bajo',                 -- 'bajo', 'medio', 'alto'
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'activo',                     -- 'prospecto', 'activo', 'inactivo', 'bloqueado'
    motivo_bloqueo NVARCHAR(255) NULL,
    es_activo BIT DEFAULT 1 NOT NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    fecha_primera_compra DATE NULL,
    fecha_ultima_compra DATE NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_cltvta_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_cltvta_codigo UNIQUE (cliente_id, empresa_id, codigo_cliente),
    CONSTRAINT UQ_cltvta_documento UNIQUE (cliente_id, empresa_id, tipo_documento, numero_documento),
    CONSTRAINT FK_cltvta_pais FOREIGN KEY (pais_id) 
        REFERENCES cat_pais(pais_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cltvta_departamento FOREIGN KEY (departamento_id) 
        REFERENCES cat_departamento(departamento_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cltvta_provincia FOREIGN KEY (provincia_id) 
        REFERENCES cat_provincia(provincia_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cltvta_distrito FOREIGN KEY (distrito_id) 
        REFERENCES cat_distrito(distrito_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cltvta_moneda FOREIGN KEY (moneda_preferida)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_cltvta_empresa ON sls_cliente(empresa_id, es_activo);
CREATE INDEX IDX_cltvta_documento ON sls_cliente(numero_documento);
CREATE INDEX IDX_cltvta_razon_social ON sls_cliente(razon_social);
CREATE INDEX IDX_cltvta_vendedor ON sls_cliente(vendedor_usuario_id) WHERE vendedor_usuario_id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Tabla: sls_cliente_contacto
-- Descripción: Contactos del cliente
-- Uso: Múltiples personas de contacto por cliente
-- Relaciones: Detalle de sls_cliente
-- -----------------------------------------------------------------------------
CREATE TABLE sls_cliente_contacto (
    contacto_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    cliente_venta_id UNIQUEIDENTIFIER NOT NULL,
    
    nombre_completo NVARCHAR(150) NOT NULL,
    cargo NVARCHAR(100) NULL,
    area NVARCHAR(100) NULL,
    
    telefono NVARCHAR(20) NULL,
    telefono_movil NVARCHAR(20) NULL,
    email NVARCHAR(100) NULL,
    
    es_contacto_principal BIT DEFAULT 0,
    es_contacto_comercial BIT DEFAULT 0,
    es_contacto_cobranzas BIT DEFAULT 0,
    
    fecha_nacimiento DATE NULL,
    observaciones NVARCHAR(500) NULL,
    
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_cltcon_cliente FOREIGN KEY (cliente_venta_id) 
        REFERENCES sls_cliente(cliente_venta_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_cltcon_cliente ON sls_cliente_contacto(cliente_venta_id, es_activo);

-- -----------------------------------------------------------------------------
-- Tabla: sls_cliente_direccion
-- Descripción: Direcciones de entrega del cliente
-- Uso: Múltiples puntos de entrega por cliente
-- Relaciones: Detalle de sls_cliente
-- -----------------------------------------------------------------------------
CREATE TABLE sls_cliente_direccion (
    direccion_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    cliente_venta_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_direccion NVARCHAR(20) NULL,
    nombre_direccion NVARCHAR(100) NOT NULL,                  -- Ej: "Almacén Principal", "Tienda Centro"
    
    direccion NVARCHAR(255) NOT NULL,
    referencia NVARCHAR(255) NULL,
    pais_id UNIQUEIDENTIFIER NULL,
    departamento_id UNIQUEIDENTIFIER NULL,
    provincia_id UNIQUEIDENTIFIER NULL,
    distrito_id UNIQUEIDENTIFIER NULL,
    ubigeo NVARCHAR(6) NULL,
    codigo_postal NVARCHAR(10) NULL,
    
    contacto_nombre NVARCHAR(150) NULL,
    contacto_telefono NVARCHAR(20) NULL,
    
    es_direccion_fiscal BIT DEFAULT 0,
    es_direccion_entrega_defecto BIT DEFAULT 0,
    
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_cltdir_cliente FOREIGN KEY (cliente_venta_id) 
        REFERENCES sls_cliente(cliente_venta_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cltdir_pais FOREIGN KEY (pais_id) 
        REFERENCES cat_pais(pais_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cltdir_departamento FOREIGN KEY (departamento_id) 
        REFERENCES cat_departamento(departamento_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cltdir_provincia FOREIGN KEY (provincia_id) 
        REFERENCES cat_provincia(provincia_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cltdir_distrito FOREIGN KEY (distrito_id) 
        REFERENCES cat_distrito(distrito_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_cltdir_cliente ON sls_cliente_direccion(cliente_venta_id, es_activo);

-- -----------------------------------------------------------------------------
-- Tabla: sls_cotizacion
-- Descripción: Cotizaciones/Presupuestos a clientes
-- Uso: Propuesta de venta antes del pedido
-- Relaciones: Puede convertirse en pedido de venta
-- -----------------------------------------------------------------------------
CREATE TABLE sls_cotizacion (
    cotizacion_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_cotizacion NVARCHAR(20) NOT NULL,
    fecha_cotizacion DATE DEFAULT GETDATE() NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    
    -- Cliente
    cliente_venta_id UNIQUEIDENTIFIER NOT NULL,
    cliente_razon_social NVARCHAR(200) NULL,
    cliente_ruc NVARCHAR(20) NULL,
    contacto_nombre NVARCHAR(150) NULL,
    
    -- Vendedor
    vendedor_usuario_id UNIQUEIDENTIFIER NULL,
    vendedor_nombre NVARCHAR(150) NULL,
    
    -- Oportunidad CRM (si existe)
    oportunidad_id UNIQUEIDENTIFIER NULL,                     -- FK a crm_oportunidad
    
    -- Condiciones comerciales
    condicion_pago NVARCHAR(50) NOT NULL,
    dias_credito INT DEFAULT 0,
    tiempo_entrega_dias INT NULL,
    moneda_id UNIQUEIDENTIFIER NOT NULL,                      -- FK a cat_moneda (CAMBIADO)
    tipo_cambio DECIMAL(10,4) DEFAULT 1,
    
    -- Totales
    subtotal DECIMAL(18,2) DEFAULT 0,
    descuento_global DECIMAL(18,2) DEFAULT 0,
    igv DECIMAL(18,2) DEFAULT 0,
    total DECIMAL(18,2) DEFAULT 0,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'borrador',                   -- 'borrador', 'enviada', 'aceptada', 'rechazada', 'vencida', 'convertida'
    fecha_envio DATETIME NULL,
    fecha_respuesta DATETIME NULL,
    motivo_rechazo NVARCHAR(500) NULL,
    
    -- Conversión
    convertida_pedido BIT DEFAULT 0,
    pedido_venta_id UNIQUEIDENTIFIER NULL,
    fecha_conversion DATETIME NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    terminos_condiciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_cotvta_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cotvta_cliente FOREIGN KEY (cliente_venta_id) 
        REFERENCES sls_cliente(cliente_venta_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cotvta_moneda FOREIGN KEY (moneda_id)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_cotvta_numero UNIQUE (cliente_id, empresa_id, numero_cotizacion)
);

CREATE INDEX IDX_cotvta_empresa ON sls_cotizacion(empresa_id, fecha_cotizacion DESC);
CREATE INDEX IDX_cotvta_cliente ON sls_cotizacion(cliente_venta_id, estado);
CREATE INDEX IDX_cotvta_estado ON sls_cotizacion(estado, fecha_vencimiento);
CREATE INDEX IDX_cotvta_vendedor ON sls_cotizacion(vendedor_usuario_id) WHERE vendedor_usuario_id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Tabla: sls_cotizacion_detalle
-- Descripción: Items cotizados
-- Uso: Productos y precios ofrecidos al cliente
-- Relaciones: Detalle de sls_cotizacion
-- -----------------------------------------------------------------------------
CREATE TABLE sls_cotizacion_detalle (
    cotizacion_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    cotizacion_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    cantidad DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    precio_unitario DECIMAL(18,4) NOT NULL,
    descuento_porcentaje DECIMAL(5,2) DEFAULT 0,
    precio_neto AS (precio_unitario * (1 - descuento_porcentaje / 100)) PERSISTED,
    subtotal AS (cantidad * precio_unitario * (1 - descuento_porcentaje / 100)) PERSISTED,
    igv AS (cantidad * precio_unitario * (1 - descuento_porcentaje / 100) * 0.18) PERSISTED,
    total AS (cantidad * precio_unitario * (1 - descuento_porcentaje / 100) * 1.18) PERSISTED,
    
    tiempo_entrega_dias INT NULL,
    observaciones NVARCHAR(500) NULL,
    
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_cotvtadet_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cotvtadet_cotizacion FOREIGN KEY (cotizacion_id) 
        REFERENCES sls_cotizacion(cotizacion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cotvtadet_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cotvtadet_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_cotvtadet_empresa ON sls_cotizacion_detalle(empresa_id);
CREATE INDEX IDX_cotvtadet_cotizacion ON sls_cotizacion_detalle(cotizacion_id);

-- -----------------------------------------------------------------------------
-- Tabla: sls_pedido
-- Descripción: Pedido/Orden de venta (documento de compromiso)
-- Uso: Formalización de venta, genera obligación de entrega
-- Relaciones: Genera salidas de inventario, facturas
-- -----------------------------------------------------------------------------
CREATE TABLE sls_pedido (
    pedido_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_pedido NVARCHAR(20) NOT NULL,
    fecha_pedido DATE DEFAULT GETDATE() NOT NULL,
    fecha_entrega_prometida DATE NOT NULL,
    
    -- Cliente
    cliente_venta_id UNIQUEIDENTIFIER NOT NULL,
    cliente_razon_social NVARCHAR(200) NULL,
    cliente_ruc NVARCHAR(20) NULL,
    
    -- Dirección de entrega
    direccion_entrega_id UNIQUEIDENTIFIER NULL,
    direccion_entrega_texto NVARCHAR(255) NULL,
    
    -- Referencia
    cotizacion_id UNIQUEIDENTIFIER NULL,
    orden_compra_cliente NVARCHAR(30) NULL,                   -- OC del cliente
    
    -- Vendedor
    vendedor_usuario_id UNIQUEIDENTIFIER NULL,
    vendedor_nombre NVARCHAR(150) NULL,
    
    -- Condiciones comerciales
    condicion_pago NVARCHAR(50) NOT NULL,
    dias_credito INT DEFAULT 0,
    moneda_id UNIQUEIDENTIFIER NOT NULL,                      -- FK a cat_moneda (CAMBIADO)
    tipo_cambio DECIMAL(10,4) DEFAULT 1,
    
    -- Totales
    subtotal DECIMAL(18,2) DEFAULT 0,
    descuento_global DECIMAL(18,2) DEFAULT 0,
    igv DECIMAL(18,2) DEFAULT 0,
    total DECIMAL(18,2) DEFAULT 0,
    
    -- Control de despacho
    total_items INT DEFAULT 0,
    items_despachados INT DEFAULT 0,
    porcentaje_despacho DECIMAL(5,2) DEFAULT 0,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'borrador',                   -- 'borrador', 'confirmado', 'aprobado', 'parcial', 'completo', 'facturado', 'anulado'
    requiere_aprobacion BIT DEFAULT 0,
    aprobado_por_usuario_id UNIQUEIDENTIFIER NULL,
    fecha_aprobacion DATETIME NULL,
    
    -- Prioridad
    prioridad INT DEFAULT 3,                                   -- 1=Urgente, 2=Alta, 3=Normal, 4=Baja
    
    -- Centro de costo (para análisis)
    centro_costo_id UNIQUEIDENTIFIER NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    instrucciones_despacho NVARCHAR(MAX) NULL,
    motivo_anulacion NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    fecha_anulacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_pedido_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_pedido_cliente FOREIGN KEY (cliente_venta_id) 
        REFERENCES sls_cliente(cliente_venta_id) ON DELETE NO ACTION,
    CONSTRAINT FK_pedido_direccion FOREIGN KEY (direccion_entrega_id) 
        REFERENCES sls_cliente_direccion(direccion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_pedido_cotizacion FOREIGN KEY (cotizacion_id) 
        REFERENCES sls_cotizacion(cotizacion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_pedido_cc FOREIGN KEY (centro_costo_id) 
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE NO ACTION,
    CONSTRAINT FK_pedido_moneda FOREIGN KEY (moneda_id)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_pedido_numero UNIQUE (cliente_id, empresa_id, numero_pedido)
);

CREATE INDEX IDX_pedido_empresa ON sls_pedido(empresa_id, fecha_pedido DESC);
CREATE INDEX IDX_pedido_cliente ON sls_pedido(cliente_venta_id, estado);
CREATE INDEX IDX_pedido_estado ON sls_pedido(estado, fecha_entrega_prometida);
CREATE INDEX IDX_pedido_vendedor ON sls_pedido(vendedor_usuario_id) WHERE vendedor_usuario_id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Tabla: sls_pedido_detalle
-- Descripción: Items del pedido de venta
-- Uso: Productos vendidos con cantidades y precios
-- Relaciones: Detalle de sls_pedido
-- -----------------------------------------------------------------------------
CREATE TABLE sls_pedido_detalle (
    pedido_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    pedido_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Cantidad
    cantidad_pedida DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Precios
    precio_unitario DECIMAL(18,4) NOT NULL,
    descuento_porcentaje DECIMAL(5,2) DEFAULT 0,
    precio_neto AS (precio_unitario * (1 - descuento_porcentaje / 100)) PERSISTED,
    subtotal AS (cantidad_pedida * precio_unitario * (1 - descuento_porcentaje / 100)) PERSISTED,
    igv AS (cantidad_pedida * precio_unitario * (1 - descuento_porcentaje / 100) * 0.18) PERSISTED,
    total AS (cantidad_pedida * precio_unitario * (1 - descuento_porcentaje / 100) * 1.18) PERSISTED,
    
    -- Control de despacho
    cantidad_despachada DECIMAL(18,4) DEFAULT 0,
    cantidad_pendiente AS (cantidad_pedida - cantidad_despachada) PERSISTED,
    cantidad_facturada DECIMAL(18,4) DEFAULT 0,
    
    -- Almacén de origen
    almacen_origen_id UNIQUEIDENTIFIER NULL,
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_pedidodet_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_pedidodet_pedido FOREIGN KEY (pedido_id) 
        REFERENCES sls_pedido(pedido_id) ON DELETE NO ACTION,
    CONSTRAINT FK_pedidodet_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_pedidodet_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT FK_pedidodet_almacen FOREIGN KEY (almacen_origen_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_pedidodet_empresa ON sls_pedido_detalle(empresa_id);
CREATE INDEX IDX_pedidodet_pedido ON sls_pedido_detalle(pedido_id);
CREATE INDEX IDX_pedidodet_producto ON sls_pedido_detalle(producto_id);
CREATE INDEX IDX_pedidodet_pendiente ON sls_pedido_detalle(pedido_id, cantidad_pedida) 
    WHERE cantidad_pedida > 0;