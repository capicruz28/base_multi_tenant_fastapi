-- ============================================================================
-- SECCIÓN 6: LOG - LOGÍSTICA Y DISTRIBUCIÓN
-- ============================================================================
-- DESCRIPCIÓN: Gestión de transporte, rutas, despachos, distribución
-- DEPENDENCIAS: ORG, INV, PUR (compras con transporte), SLS (ventas con despacho)
-- USADO POR: Control de flota, entregas, seguimiento de envíos
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: log_transportista
-- Descripción: Catálogo de empresas transportistas
-- Uso: Terceros que realizan transporte de mercadería
-- Relaciones: Usado en log_guia_remision, log_despacho
-- -----------------------------------------------------------------------------
CREATE TABLE log_transportista (
    transportista_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_transportista NVARCHAR(20) NOT NULL,
    razon_social NVARCHAR(200) NOT NULL,
    nombre_comercial NVARCHAR(150) NULL,
    
    tipo_documento NVARCHAR(10) DEFAULT 'RUC',
    numero_documento NVARCHAR(20) NOT NULL,
    
    -- Licencias y permisos
    numero_mtc NVARCHAR(30) NULL,                             -- Registro MTC (Ministerio de Transportes)
    licencia_tipo NVARCHAR(50) NULL,
    
    -- Contacto
    telefono NVARCHAR(20) NULL,
    email NVARCHAR(100) NULL,
    direccion NVARCHAR(255) NULL,
    
    -- Tarifas
    tarifa_km DECIMAL(10,2) NULL,
    tarifa_hora DECIMAL(10,2) NULL,
    moneda_tarifa UNIQUEIDENTIFIER NOT NULL,
    
    -- Calificación
    calificacion DECIMAL(3,2) NULL,
    
    -- Estado
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_transp_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_transp_codigo UNIQUE (cliente_id, empresa_id, codigo_transportista),
    CONSTRAINT FK_transp_moneda FOREIGN KEY (moneda_tarifa)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_transp_empresa ON log_transportista(empresa_id, es_activo);

-- -----------------------------------------------------------------------------
-- Tabla: log_vehiculo
-- Descripción: Flota de vehículos (propios o de transportistas)
-- Uso: Control de vehículos para despacho y transporte
-- Relaciones: Asignados a transportistas o empresa propia
-- -----------------------------------------------------------------------------
CREATE TABLE log_vehiculo (
    vehiculo_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    placa NVARCHAR(15) NOT NULL,
    marca NVARCHAR(50) NULL,
    modelo NVARCHAR(50) NULL,
    año INT NULL,
    color NVARCHAR(30) NULL,
    
    -- Tipo
    tipo_vehiculo NVARCHAR(30) NOT NULL,                      -- 'camion', 'camioneta', 'furgon', 'moto', 'trailer'
    categoria_vehiculo NVARCHAR(20) NULL,                     -- 'ligero', 'mediano', 'pesado'
    
    -- Capacidad
    capacidad_kg DECIMAL(12,2) NULL,
    capacidad_m3 DECIMAL(12,2) NULL,
    
    -- Propietario
    tipo_propiedad NVARCHAR(20) NOT NULL,                     -- 'propio', 'tercero'
    transportista_id UNIQUEIDENTIFIER NULL,                   -- Si es de tercero
    
    -- Conductor habitual
    conductor_nombre NVARCHAR(150) NULL,
    conductor_licencia NVARCHAR(20) NULL,
    conductor_telefono NVARCHAR(20) NULL,
    
    -- Documentos
    tarjeta_propiedad NVARCHAR(30) NULL,
    soat_numero NVARCHAR(30) NULL,
    soat_vencimiento DATE NULL,
    revision_tecnica_vencimiento DATE NULL,
    
    -- GPS/Rastreo
    tiene_gps BIT DEFAULT 0,
    codigo_gps NVARCHAR(50) NULL,
    
    -- Estado
    estado_vehiculo NVARCHAR(20) DEFAULT 'disponible',        -- 'disponible', 'en_ruta', 'mantenimiento', 'inactivo'
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_vehiculo_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_vehiculo_transp FOREIGN KEY (transportista_id) 
        REFERENCES log_transportista(transportista_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_vehiculo_placa UNIQUE (cliente_id, empresa_id, placa)
);

CREATE INDEX IDX_vehiculo_empresa ON log_vehiculo(empresa_id, es_activo);
CREATE INDEX IDX_vehiculo_estado ON log_vehiculo(estado_vehiculo);
CREATE INDEX IDX_vehiculo_transp ON log_vehiculo(transportista_id) WHERE transportista_id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Tabla: log_ruta
-- Descripción: Rutas de distribución predefinidas
-- Uso: Rutas frecuentes origen-destino
-- Relaciones: Usado en planificación de despachos
-- -----------------------------------------------------------------------------
CREATE TABLE log_ruta (
    ruta_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_ruta NVARCHAR(20) NOT NULL,
    nombre_ruta NVARCHAR(100) NOT NULL,
    
    -- Origen-Destino
    origen_sucursal_id UNIQUEIDENTIFIER NULL,
    origen_descripcion NVARCHAR(255) NULL,
    destino_descripcion NVARCHAR(255) NULL,
    
    -- Datos geográficos
    departamento_origen NVARCHAR(50) NULL,
    departamento_destino NVARCHAR(50) NULL,
    
    -- Características
    distancia_km DECIMAL(10,2) NULL,
    tiempo_estimado_horas DECIMAL(5,2) NULL,
    tipo_carretera NVARCHAR(30) NULL,                         -- 'asfalto', 'trocha', 'mixta'
    
    -- Costos
    costo_estimado DECIMAL(12,2) NULL,
    moneda_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Peajes y paradas
    cantidad_peajes INT DEFAULT 0,
    costo_peajes DECIMAL(10,2) DEFAULT 0,
    puntos_intermedios NVARCHAR(MAX) NULL,                    -- JSON con paradas
    
    -- Estado
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_logruta_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_logruta_origen_suc FOREIGN KEY (origen_sucursal_id) 
        REFERENCES org_sucursal(sucursal_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_logruta_codigo UNIQUE (cliente_id, empresa_id, codigo_ruta),
    CONSTRAINT FK_logruta_moneda FOREIGN KEY (moneda_id)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_ruta_empresa ON log_ruta(empresa_id, es_activo);

-- -----------------------------------------------------------------------------
-- Tabla: log_guia_remision
-- Descripción: Guías de remisión (documento de transporte)
-- Uso: Documento legal para traslado de mercadería
-- Relaciones: Vinculada a ventas, transferencias, compras
-- -----------------------------------------------------------------------------
CREATE TABLE log_guia_remision (
    guia_remision_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Numeración
    serie NVARCHAR(4) NOT NULL,
    numero NVARCHAR(10) NOT NULL,
    numero_completo AS (serie + '-' + numero) PERSISTED,
    
    fecha_emision DATE DEFAULT GETDATE() NOT NULL,
    fecha_traslado DATE NOT NULL,
    
    -- Tipo de guía
    tipo_guia NVARCHAR(30) NOT NULL,                          -- 'remitente', 'transportista'
    motivo_traslado NVARCHAR(30) NOT NULL,                    -- 'venta', 'compra', 'transferencia', 'consignacion', 'devolucion'
    
    -- Remitente
    remitente_razon_social NVARCHAR(200) NOT NULL,
    remitente_ruc NVARCHAR(11) NOT NULL,
    remitente_direccion NVARCHAR(255) NULL,
    
    -- Destinatario
    destinatario_razon_social NVARCHAR(200) NOT NULL,
    destinatario_documento_tipo NVARCHAR(10) NULL,
    destinatario_documento_numero NVARCHAR(20) NULL,
    destinatario_direccion NVARCHAR(255) NULL,
    
    -- Punto de partida y llegada
    punto_partida NVARCHAR(255) NOT NULL,
    punto_partida_ubigeo NVARCHAR(6) NULL,
    punto_llegada NVARCHAR(255) NOT NULL,
    punto_llegada_ubigeo NVARCHAR(6) NULL,
    
    -- Transporte
    modalidad_transporte NVARCHAR(20) NOT NULL,               -- 'publico', 'privado'
    transportista_id UNIQUEIDENTIFIER NULL,
    transportista_razon_social NVARCHAR(200) NULL,
    transportista_ruc NVARCHAR(11) NULL,
    
    -- Vehículo y conductor
    vehiculo_id UNIQUEIDENTIFIER NULL,
    vehiculo_placa NVARCHAR(15) NULL,
    conductor_nombre NVARCHAR(150) NULL,
    conductor_documento_tipo NVARCHAR(10) NULL,
    conductor_documento_numero NVARCHAR(20) NULL,
    conductor_licencia NVARCHAR(20) NULL,
    
    -- Bultos
    total_bultos INT DEFAULT 0,
    peso_total_kg DECIMAL(12,2) DEFAULT 0,
    
    -- Documento sustento
    documento_sustento_tipo NVARCHAR(20) NULL,                -- 'factura', 'boleta', 'orden_compra'
    documento_sustento_serie NVARCHAR(4) NULL,
    documento_sustento_numero NVARCHAR(10) NULL,
    
    -- Referencia interna
    movimiento_inventario_id UNIQUEIDENTIFIER NULL,
    venta_id UNIQUEIDENTIFIER NULL,                           -- FK a sls_venta (módulo SLS)
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'emitida',                    -- 'borrador', 'emitida', 'en_transito', 'entregada', 'anulada'
    fecha_entrega DATETIME NULL,
    
    -- Firma digital (SUNAT Perú)
    codigo_hash NVARCHAR(100) NULL,
    codigo_qr NVARCHAR(MAX) NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_anulacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_guia_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_guia_transp FOREIGN KEY (transportista_id) 
        REFERENCES log_transportista(transportista_id) ON DELETE NO ACTION,
    CONSTRAINT FK_guia_vehiculo FOREIGN KEY (vehiculo_id) 
        REFERENCES log_vehiculo(vehiculo_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_guia_numero UNIQUE (cliente_id, empresa_id, serie, numero)
);

CREATE INDEX IDX_guia_empresa ON log_guia_remision(empresa_id, fecha_emision DESC);
CREATE INDEX IDX_guia_estado ON log_guia_remision(estado);
CREATE INDEX IDX_guia_numero ON log_guia_remision(numero_completo);

-- -----------------------------------------------------------------------------
-- Tabla: log_guia_remision_detalle
-- Descripción: Items transportados en la guía
-- Uso: Productos y cantidades en el traslado
-- Relaciones: Detalle de log_guia_remision
-- -----------------------------------------------------------------------------
CREATE TABLE log_guia_remision_detalle (
    guia_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    guia_remision_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    cantidad DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    descripcion NVARCHAR(255) NULL,
    peso_kg DECIMAL(12,2) NULL,
    
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_guiadet_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_guiadet_guia FOREIGN KEY (guia_remision_id) 
        REFERENCES log_guia_remision(guia_remision_id) ON DELETE NO ACTION,
    CONSTRAINT FK_guiadet_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_guiadet_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_guiadet_empresa ON log_guia_remision_detalle(empresa_id);
CREATE INDEX IDX_guiadet_guia ON log_guia_remision_detalle(guia_remision_id);

-- -----------------------------------------------------------------------------
-- Tabla: log_despacho
-- Descripción: Planificación y ejecución de despachos
-- Uso: Agrupar pedidos para una misma ruta/vehículo
-- Relaciones: Agrupa múltiples guías de remisión
-- -----------------------------------------------------------------------------
CREATE TABLE log_despacho (
    despacho_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_despacho NVARCHAR(20) NOT NULL,
    fecha_programada DATE NOT NULL,
    hora_salida_programada TIME NULL,
    
    -- Ruta
    ruta_id UNIQUEIDENTIFIER NULL,
    origen_sucursal_id UNIQUEIDENTIFIER NULL,
    
    -- Vehículo y conductor
    vehiculo_id UNIQUEIDENTIFIER NULL,
    conductor_nombre NVARCHAR(150) NULL,
    conductor_telefono NVARCHAR(20) NULL,
    
    -- Detalles de ejecución
    fecha_salida_real DATETIME NULL,
    fecha_retorno DATETIME NULL,
    km_inicial DECIMAL(10,2) NULL,
    km_final DECIMAL(10,2) NULL,
    km_recorrido AS (km_final - km_inicial) PERSISTED,
    
    -- Totales
    total_guias INT DEFAULT 0,
    total_peso_kg DECIMAL(12,2) DEFAULT 0,
    total_bultos INT DEFAULT 0,
    
    -- Costos
    costo_combustible DECIMAL(12,2) NULL,
    costo_peajes DECIMAL(12,2) NULL,
    otros_gastos DECIMAL(12,2) NULL,
    costo_total AS (ISNULL(costo_combustible,0) + ISNULL(costo_peajes,0) + ISNULL(otros_gastos,0)) PERSISTED,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'planificado',                -- 'planificado', 'en_ruta', 'completado', 'cancelado'
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    incidencias NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_desp_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_desp_ruta FOREIGN KEY (ruta_id) 
        REFERENCES log_ruta(ruta_id) ON DELETE NO ACTION,
    CONSTRAINT FK_desp_vehiculo FOREIGN KEY (vehiculo_id) 
        REFERENCES log_vehiculo(vehiculo_id) ON DELETE NO ACTION,
    CONSTRAINT FK_desp_origen FOREIGN KEY (origen_sucursal_id) 
        REFERENCES org_sucursal(sucursal_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_desp_numero UNIQUE (cliente_id, empresa_id, numero_despacho)
);

CREATE INDEX IDX_desp_empresa ON log_despacho(empresa_id, fecha_programada DESC);
CREATE INDEX IDX_desp_estado ON log_despacho(estado);
CREATE INDEX IDX_desp_vehiculo ON log_despacho(vehiculo_id, fecha_programada);

-- -----------------------------------------------------------------------------
-- Tabla: log_despacho_guia
-- Descripción: Guías de remisión incluidas en un despacho
-- Uso: Relación muchos a muchos entre despachos y guías
-- Relaciones: Vincula log_despacho con log_guia_remision
-- -----------------------------------------------------------------------------
CREATE TABLE log_despacho_guia (
    despacho_guia_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    despacho_id UNIQUEIDENTIFIER NOT NULL,
    guia_remision_id UNIQUEIDENTIFIER NOT NULL,
    
    orden_entrega INT NULL,                                    -- Secuencia de entrega
    fecha_entrega DATETIME NULL,
    estado_entrega NVARCHAR(20) DEFAULT 'pendiente',          -- 'pendiente', 'entregado', 'no_entregado'
    observaciones_entrega NVARCHAR(500) NULL,
    
    receptor_nombre NVARCHAR(150) NULL,
    receptor_documento NVARCHAR(20) NULL,
    
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_despguia_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_despguia_desp FOREIGN KEY (despacho_id) 
        REFERENCES log_despacho(despacho_id) ON DELETE NO ACTION,
    CONSTRAINT FK_despguia_guia FOREIGN KEY (guia_remision_id) 
        REFERENCES log_guia_remision(guia_remision_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_desp_guia UNIQUE (cliente_id, despacho_id, guia_remision_id)
);

CREATE INDEX IDX_despguia_empresa ON log_despacho_guia(empresa_id);
CREATE INDEX IDX_despguia_desp ON log_despacho_guia(despacho_id, orden_entrega);
CREATE INDEX IDX_despguia_guia ON log_despacho_guia(guia_remision_id);