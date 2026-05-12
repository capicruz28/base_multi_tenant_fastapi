-- ============================================================================
-- SECCIÓN 15: POS - PUNTO DE VENTA
-- ============================================================================
-- DESCRIPCIÓN: Sistema de punto de venta (tiendas, retail)
-- DEPENDENCIAS: ORG, INV, SLS, PRC, INV_BILL
-- USADO POR: Ventas al mostrador, retail
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: pos_punto_venta
-- Descripción: Puntos de venta físicos (cajas registradoras)
-- Uso: Configuración de terminales POS
-- Relaciones: Ubicados en sucursales
-- -----------------------------------------------------------------------------
CREATE TABLE pos_punto_venta (
    punto_venta_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_punto_venta NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    
    -- Ubicación
    sucursal_id UNIQUEIDENTIFIER NOT NULL,
    ubicacion_fisica NVARCHAR(100) NULL,                      -- Ej: "Caja 1", "Caja Express"
    
    -- Configuración
    tipo_punto_venta NVARCHAR(30) DEFAULT 'caja',             -- 'caja', 'autoservicio', 'movil'
    
    -- Series de comprobantes asignadas
    serie_factura_id UNIQUEIDENTIFIER NULL,
    serie_boleta_id UNIQUEIDENTIFIER NULL,
    serie_nota_credito_id UNIQUEIDENTIFIER NULL,
    
    -- Almacén asociado
    almacen_id UNIQUEIDENTIFIER NULL,
    
    -- Lista de precios por defecto
    lista_precio_id UNIQUEIDENTIFIER NULL,
    
    -- Configuración de pagos
    acepta_efectivo BIT DEFAULT 1,
    acepta_tarjeta BIT DEFAULT 1,
    acepta_transferencia BIT DEFAULT 1,
    acepta_yape_plin BIT DEFAULT 0,
    
    -- Terminal física
    codigo_terminal NVARCHAR(50) NULL,
    ip_terminal NVARCHAR(45) NULL,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'cerrado',                    -- 'abierto', 'cerrado', 'bloqueado'
    es_activo BIT DEFAULT 1 NOT NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_pv_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_pv_sucursal FOREIGN KEY (sucursal_id) 
        REFERENCES org_sucursal(sucursal_id) ON DELETE NO ACTION,
    CONSTRAINT FK_pv_almacen FOREIGN KEY (almacen_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION,
    CONSTRAINT FK_pv_listaprecio FOREIGN KEY (lista_precio_id) 
        REFERENCES prc_lista_precio(lista_precio_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_pv_codigo UNIQUE (cliente_id, empresa_id, codigo_punto_venta)
);

CREATE INDEX IDX_pv_empresa ON pos_punto_venta(empresa_id, es_activo);
CREATE INDEX IDX_pv_sucursal ON pos_punto_venta(sucursal_id, estado);

-- -----------------------------------------------------------------------------
-- Tabla: pos_turno_caja
-- Descripción: Turnos de apertura y cierre de caja
-- Uso: Control de efectivo y transacciones por turno
-- Relaciones: Asociado a punto de venta y cajero
-- -----------------------------------------------------------------------------
CREATE TABLE pos_turno_caja (
    turno_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    punto_venta_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_turno NVARCHAR(20) NOT NULL,
    
    -- Cajero
    cajero_usuario_id UNIQUEIDENTIFIER NOT NULL,
    cajero_nombre NVARCHAR(150) NULL,
    
    -- Apertura
    fecha_apertura DATETIME DEFAULT GETDATE() NOT NULL,
    monto_apertura DECIMAL(18,2) NOT NULL,                    -- Efectivo inicial
    
    -- Cierre
    fecha_cierre DATETIME NULL,
    monto_cierre_esperado DECIMAL(18,2) NULL,                 -- Según ventas
    monto_cierre_real DECIMAL(18,2) NULL,                     -- Efectivo contado
    diferencia AS (monto_cierre_real - monto_cierre_esperado) PERSISTED,
    
    -- Totales del turno
    total_ventas INT DEFAULT 0,
    total_ventas_efectivo DECIMAL(18,2) DEFAULT 0,
    total_ventas_tarjeta DECIMAL(18,2) DEFAULT 0,
    total_ventas_transferencia DECIMAL(18,2) DEFAULT 0,
    total_ventas_otros DECIMAL(18,2) DEFAULT 0,
    total_ingresos AS (total_ventas_efectivo + total_ventas_tarjeta + total_ventas_transferencia + total_ventas_otros) PERSISTED,
    
    total_egresos DECIMAL(18,2) DEFAULT 0,                    -- Gastos, retiros
    
    -- Comprobantes emitidos
    total_facturas INT DEFAULT 0,
    total_boletas INT DEFAULT 0,
    total_notas_credito INT DEFAULT 0,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'abierto',                    -- 'abierto', 'cerrado'
    
    -- Observaciones
    observaciones_apertura NVARCHAR(500) NULL,
    observaciones_cierre NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    cerrado_por_usuario_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_turno_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_turno_pv FOREIGN KEY (punto_venta_id) 
        REFERENCES pos_punto_venta(punto_venta_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_turno_numero UNIQUE (cliente_id, empresa_id, punto_venta_id, numero_turno)
);

CREATE INDEX IDX_turno_empresa ON pos_turno_caja(empresa_id, fecha_apertura DESC);
CREATE INDEX IDX_turno_pv ON pos_turno_caja(punto_venta_id, estado);
CREATE INDEX IDX_turno_cajero ON pos_turno_caja(cajero_usuario_id, estado);

-- -----------------------------------------------------------------------------
-- Tabla: pos_venta
-- Descripción: Ventas realizadas en POS
-- Uso: Transacción de venta al mostrador
-- Relaciones: Genera comprobante, actualiza inventario
-- -----------------------------------------------------------------------------
CREATE TABLE pos_venta (
    venta_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_venta NVARCHAR(20) NOT NULL,
    fecha_venta DATETIME DEFAULT GETDATE() NOT NULL,
    
    -- Punto de venta y turno
    punto_venta_id UNIQUEIDENTIFIER NOT NULL,
    turno_caja_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Cajero/Vendedor
    vendedor_usuario_id UNIQUEIDENTIFIER NOT NULL,
    vendedor_nombre NVARCHAR(150) NULL,
    
    -- Cliente (opcional en retail)
    cliente_venta_id UNIQUEIDENTIFIER NULL,
    cliente_nombre NVARCHAR(200) NULL,
    cliente_documento_tipo NVARCHAR(10) NULL,
    cliente_documento_numero NVARCHAR(20) NULL,
    
    -- Totales
    moneda_id UNIQUEIDENTIFIER NOT NULL,
    subtotal DECIMAL(18,2) DEFAULT 0,
    descuento_global DECIMAL(18,2) DEFAULT 0,
    igv DECIMAL(18,2) DEFAULT 0,
    total DECIMAL(18,2) DEFAULT 0,
    
    -- Redondeo (común en efectivo)
    redondeo DECIMAL(18,2) DEFAULT 0,
    total_cobrar AS (total + redondeo) PERSISTED,
    
    -- Forma de pago
    forma_pago NVARCHAR(30) NOT NULL,                         -- 'efectivo', 'tarjeta', 'transferencia', 'mixto'
    
    -- Montos por forma de pago
    monto_efectivo DECIMAL(18,2) DEFAULT 0,
    monto_tarjeta DECIMAL(18,2) DEFAULT 0,
    monto_transferencia DECIMAL(18,2) DEFAULT 0,
    monto_otros DECIMAL(18,2) DEFAULT 0,
    
    -- Cambio (si es efectivo)
    monto_recibido DECIMAL(18,2) NULL,
    monto_cambio AS (
        CASE 
            WHEN forma_pago = 'efectivo' AND monto_recibido > (total + redondeo)
            THEN monto_recibido - (total + redondeo)
            ELSE 0
        END
    ) PERSISTED,
    
    -- Comprobante generado
    comprobante_id UNIQUEIDENTIFIER NULL,
    tipo_comprobante NVARCHAR(2) NULL,
    numero_comprobante NVARCHAR(20) NULL,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'completada',                 -- 'borrador', 'completada', 'anulada'
    fecha_anulacion DATETIME NULL,
    motivo_anulacion NVARCHAR(500) NULL,
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_posvta_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_posvta_pv FOREIGN KEY (punto_venta_id) 
        REFERENCES pos_punto_venta(punto_venta_id) ON DELETE NO ACTION,
    CONSTRAINT FK_posvta_turno FOREIGN KEY (turno_caja_id) 
        REFERENCES pos_turno_caja(turno_id) ON DELETE NO ACTION,
    CONSTRAINT FK_posvta_cliente FOREIGN KEY (cliente_venta_id) 
        REFERENCES sls_cliente(cliente_venta_id) ON DELETE NO ACTION,
    CONSTRAINT FK_posvta_comp FOREIGN KEY (comprobante_id) 
        REFERENCES invbill_comprobante(comprobante_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_posvta_numero UNIQUE (cliente_id, empresa_id, punto_venta_id, numero_venta),
    CONSTRAINT FK_posvta_moneda FOREIGN KEY (moneda_id)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_posvta_empresa ON pos_venta(empresa_id, fecha_venta DESC);
CREATE INDEX IDX_posvta_pv ON pos_venta(punto_venta_id, estado, fecha_venta DESC);
CREATE INDEX IDX_posvta_turno ON pos_venta(turno_caja_id);
CREATE INDEX IDX_posvta_comprobante ON pos_venta(comprobante_id) WHERE comprobante_id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Tabla: pos_venta_detalle
-- Descripción: Items de la venta POS
-- Uso: Productos vendidos en el mostrador
-- Relaciones: Detalle de pos_venta
-- -----------------------------------------------------------------------------
CREATE TABLE pos_venta_detalle (
    venta_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    venta_id UNIQUEIDENTIFIER NOT NULL,
    
    item INT NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    descripcion NVARCHAR(200) NULL,
    
    cantidad DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    precio_unitario DECIMAL(18,4) NOT NULL,
    descuento_porcentaje DECIMAL(5,2) DEFAULT 0,
    descuento_monto AS (precio_unitario * cantidad * descuento_porcentaje / 100) PERSISTED,
    precio_neto AS (precio_unitario * (1 - descuento_porcentaje / 100)) PERSISTED,
    
    subtotal AS (cantidad * precio_unitario * (1 - descuento_porcentaje / 100)) PERSISTED,
    igv AS (cantidad * precio_unitario * (1 - descuento_porcentaje / 100) * 0.18) PERSISTED,
    total AS (cantidad * precio_unitario * (1 - descuento_porcentaje / 100) * 1.18) PERSISTED,
    
    -- Promoción aplicada
    promocion_id UNIQUEIDENTIFIER NULL,
    
    -- Lote (si aplica)
    lote NVARCHAR(50) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_posvtadet_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_posvtadet_venta FOREIGN KEY (venta_id) 
        REFERENCES pos_venta(venta_id) ON DELETE NO ACTION,
    CONSTRAINT FK_posvtadet_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_posvtadet_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT FK_posvtadet_promo FOREIGN KEY (promocion_id) 
        REFERENCES prc_promocion(promocion_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_posvtadet_empresa ON pos_venta_detalle(empresa_id);
CREATE INDEX IDX_posvtadet_venta ON pos_venta_detalle(venta_id, item);
CREATE INDEX IDX_posvtadet_producto ON pos_venta_detalle(producto_id);