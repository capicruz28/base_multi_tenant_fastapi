-- ============================================================================
-- SECCIÓN 14: INV_BILL - FACTURACIÓN ELECTRÓNICA
-- ============================================================================
-- DESCRIPCIÓN: Emisión de comprobantes electrónicos (facturas, boletas, NC, ND)
-- DEPENDENCIAS: ORG, SLS (pedidos), INV
-- USADO POR: FIN (cuentas por cobrar), obligaciones tributarias
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: invbill_serie_comprobante
-- Descripción: Series de comprobantes electrónicos
-- Uso: Control de numeración de facturas, boletas, NC, ND
-- Relaciones: Asignada por sucursal/punto de venta
-- -----------------------------------------------------------------------------
CREATE TABLE invbill_serie_comprobante (
    serie_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    tipo_comprobante NVARCHAR(2) NOT NULL,                    -- '01'=Factura, '03'=Boleta, '07'=NC, '08'=ND
    serie NVARCHAR(4) NOT NULL,                               -- 'F001', 'B001', etc
    
    -- Numeración
    numero_actual INT DEFAULT 0,
    numero_inicial INT DEFAULT 1,
    numero_final INT NULL,                                    -- Límite autorizado (si aplica)
    
    -- Asociación
    sucursal_id UNIQUEIDENTIFIER NULL,
    punto_venta_id UNIQUEIDENTIFIER NULL,                     -- FK a pos_punto_venta
    
    -- Configuración
    es_electronica BIT DEFAULT 1,
    requiere_autorizacion_sunat BIT DEFAULT 1,
    
    -- Estado
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_activacion DATE NULL,
    fecha_baja DATE NULL,
    motivo_baja NVARCHAR(255) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_serie_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_serie_sucursal FOREIGN KEY (sucursal_id) 
        REFERENCES org_sucursal(sucursal_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_serie UNIQUE (cliente_id, empresa_id, tipo_comprobante, serie)
);

CREATE INDEX IDX_serie_empresa ON invbill_serie_comprobante(empresa_id, es_activo);
CREATE INDEX IDX_serie_tipo ON invbill_serie_comprobante(tipo_comprobante, serie);

-- -----------------------------------------------------------------------------
-- Tabla: invbill_comprobante
-- Descripción: Comprobantes de pago (facturas, boletas)
-- Uso: Documento fiscal de venta
-- Relaciones: Vinculado a pedidos de venta, genera cuentas por cobrar
-- -----------------------------------------------------------------------------
CREATE TABLE invbill_comprobante (
    comprobante_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Identificación
    tipo_comprobante NVARCHAR(2) NOT NULL,                    -- '01', '03', '07', '08'
    serie NVARCHAR(4) NOT NULL,
    numero NVARCHAR(10) NOT NULL,
    numero_completo AS (serie + '-' + numero) PERSISTED,
    
    fecha_emision DATE DEFAULT GETDATE() NOT NULL,
    fecha_vencimiento DATE NULL,                              -- Para crédito
    hora_emision TIME DEFAULT CONVERT(TIME, GETDATE()),
    
    -- Cliente
    cliente_venta_id UNIQUEIDENTIFIER NULL,
    cliente_tipo_documento NVARCHAR(2) NOT NULL,              -- '6'=RUC, '1'=DNI, etc
    cliente_numero_documento NVARCHAR(20) NOT NULL,
    cliente_razon_social NVARCHAR(200) NOT NULL,
    cliente_direccion NVARCHAR(255) NULL,
    
    -- Referencia
    pedido_id UNIQUEIDENTIFIER NULL,
    venta_id UNIQUEIDENTIFIER NULL,                           -- FK a pos_venta (si es de POS)
    
    -- Guía de remisión relacionada
    guia_remision_id UNIQUEIDENTIFIER NULL,
    
    -- Documento relacionado (para NC, ND)
    comprobante_referencia_id UNIQUEIDENTIFIER NULL,
    tipo_nota NVARCHAR(2) NULL,                               -- Tipo de NC o ND (códigos SUNAT)
    motivo_nota NVARCHAR(500) NULL,
    
    -- Montos
    moneda_id UNIQUEIDENTIFIER NOT NULL,                      -- FK a cat_moneda (CAMBIADO)
    tipo_cambio DECIMAL(10,4) DEFAULT 1,
    
    subtotal_gravado DECIMAL(18,2) DEFAULT 0,
    subtotal_exonerado DECIMAL(18,2) DEFAULT 0,
    subtotal_inafecto DECIMAL(18,2) DEFAULT 0,
    subtotal_gratuito DECIMAL(18,2) DEFAULT 0,
    descuento_global DECIMAL(18,2) DEFAULT 0,
    igv DECIMAL(18,2) DEFAULT 0,
    total DECIMAL(18,2) DEFAULT 0,
    
    -- Detracción (si aplica)
    aplica_detraccion BIT DEFAULT 0,
    porcentaje_detraccion DECIMAL(5,2) NULL,
    monto_detraccion DECIMAL(18,2) NULL,
    
    -- Retención/Percepción
    aplica_retencion BIT DEFAULT 0,
    monto_retencion DECIMAL(18,2) NULL,
    aplica_percepcion BIT DEFAULT 0,
    monto_percepcion DECIMAL(18,2) NULL,
    
    -- Condición de pago
    condicion_pago NVARCHAR(50) NULL,
    forma_pago NVARCHAR(30) DEFAULT 'contado',                -- 'contado', 'credito'
    
    -- Firma digital SUNAT
    codigo_hash NVARCHAR(100) NULL,
    firma_digital NVARCHAR(MAX) NULL,
    codigo_qr NVARCHAR(MAX) NULL,
    
    -- Estado SUNAT
    estado_sunat NVARCHAR(20) DEFAULT 'pendiente',            -- 'pendiente', 'aceptado', 'rechazado', 'baja'
    codigo_respuesta_sunat NVARCHAR(10) NULL,
    mensaje_respuesta_sunat NVARCHAR(500) NULL,
    fecha_envio_sunat DATETIME NULL,
    fecha_respuesta_sunat DATETIME NULL,
    
    -- CDR (Constancia de Recepción)
    cdr_xml NVARCHAR(MAX) NULL,
    cdr_fecha DATETIME NULL,
    
    -- Archivos
    xml_comprobante NVARCHAR(MAX) NULL,
    pdf_url NVARCHAR(500) NULL,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'emitido',                    -- 'borrador', 'emitido', 'anulado', 'dado_baja'
    fecha_anulacion DATETIME NULL,
    motivo_anulacion NVARCHAR(500) NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Vendedor
    vendedor_usuario_id UNIQUEIDENTIFIER NULL,
    vendedor_nombre NVARCHAR(150) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_comp_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_comp_cliente FOREIGN KEY (cliente_venta_id) 
        REFERENCES sls_cliente(cliente_venta_id) ON DELETE NO ACTION,
    CONSTRAINT FK_comp_pedido FOREIGN KEY (pedido_id) 
        REFERENCES sls_pedido(pedido_id) ON DELETE NO ACTION,
    CONSTRAINT FK_comp_guia FOREIGN KEY (guia_remision_id) 
        REFERENCES log_guia_remision(guia_remision_id) ON DELETE NO ACTION,
    CONSTRAINT FK_comp_referencia FOREIGN KEY (comprobante_referencia_id) 
        REFERENCES invbill_comprobante(comprobante_id) ON DELETE NO ACTION,
    CONSTRAINT FK_comp_moneda FOREIGN KEY (moneda_id)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_comp_numero UNIQUE (cliente_id, empresa_id, tipo_comprobante, serie, numero)
);

CREATE INDEX IDX_comp_empresa ON invbill_comprobante(empresa_id, fecha_emision DESC);
CREATE INDEX IDX_comp_cliente ON invbill_comprobante(cliente_venta_id, estado);
CREATE INDEX IDX_comp_numero ON invbill_comprobante(numero_completo);
CREATE INDEX IDX_comp_estado_sunat ON invbill_comprobante(estado_sunat);
CREATE INDEX IDX_comp_fecha ON invbill_comprobante(fecha_emision DESC);

-- -----------------------------------------------------------------------------
-- Tabla: invbill_comprobante_detalle
-- Descripción: Items del comprobante
-- Uso: Productos facturados con precios y tributos
-- Relaciones: Detalle de invbill_comprobante
-- -----------------------------------------------------------------------------
CREATE TABLE invbill_comprobante_detalle (
    comprobante_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    comprobante_id UNIQUEIDENTIFIER NOT NULL,
    
    item INT NOT NULL,
    producto_id UNIQUEIDENTIFIER NULL,
    codigo_producto NVARCHAR(50) NULL,
    descripcion NVARCHAR(500) NOT NULL,
    
    -- Cantidad
    cantidad DECIMAL(18,4) NOT NULL,
    unidad_medida_codigo NVARCHAR(10) NOT NULL,               -- Código SUNAT (NIU, ZZ, etc)
    unidad_medida_id UNIQUEIDENTIFIER NULL,
    
    -- Precios
    precio_unitario DECIMAL(18,4) NOT NULL,
    descuento_unitario DECIMAL(18,4) DEFAULT 0,
    precio_venta_unitario AS (precio_unitario - descuento_unitario) PERSISTED,
    
    -- Totales
    valor_venta AS (cantidad * (precio_unitario - descuento_unitario)) PERSISTED,
    
    -- Tributos
    tipo_afectacion_igv NVARCHAR(2) NOT NULL,                 -- '10'=Gravado, '20'=Exonerado, etc
    porcentaje_igv DECIMAL(5,2) DEFAULT 18,
    igv AS (
        CASE 
            WHEN tipo_afectacion_igv = '10' 
            THEN cantidad * (precio_unitario - descuento_unitario) * (porcentaje_igv / 100)
            ELSE 0
        END
    ) PERSISTED,
    total_item AS (
        cantidad * (precio_unitario - descuento_unitario) * 
        (1 + CASE WHEN tipo_afectacion_igv = '10' THEN porcentaje_igv / 100 ELSE 0 END)
    ) PERSISTED,
    
    -- Código SUNAT
    codigo_producto_sunat NVARCHAR(10) NULL,
    
    -- Lote (si aplica)
    lote NVARCHAR(50) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_compdet_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_compdet_comp FOREIGN KEY (comprobante_id) 
        REFERENCES invbill_comprobante(comprobante_id) ON DELETE NO ACTION,
    CONSTRAINT FK_compdet_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_compdet_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_compdet_empresa ON invbill_comprobante_detalle(empresa_id);
CREATE INDEX IDX_compdet_comprobante ON invbill_comprobante_detalle(comprobante_id, item);
CREATE INDEX IDX_compdet_producto ON invbill_comprobante_detalle(producto_id) WHERE producto_id IS NOT NULL;