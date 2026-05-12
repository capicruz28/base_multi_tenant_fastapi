-- ============================================================================
-- SECCIÓN 5: PUR - COMPRAS Y ABASTECIMIENTO
-- ============================================================================
-- DESCRIPCIÓN: Gestión de compras, proveedores, órdenes de compra, cotizaciones
-- DEPENDENCIAS: ORG, INV
-- USADO POR: INV (recepción de mercadería), FIN (cuentas por pagar), CST (costos)
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: pur_proveedor
-- Descripción: Catálogo de proveedores
-- Uso: Maestro de proveedores de bienes y servicios
-- Relaciones: Usado por órdenes de compra, cotizaciones
-- -----------------------------------------------------------------------------
CREATE TABLE pur_proveedor (
    proveedor_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Identificación
    codigo_proveedor NVARCHAR(20) NOT NULL,
    razon_social NVARCHAR(200) NOT NULL,
    nombre_comercial NVARCHAR(150) NULL,
    
    -- Documento tributario
    tipo_documento NVARCHAR(10) DEFAULT 'RUC',                -- 'RUC', 'DNI', 'CE', 'PASAPORTE'
    numero_documento NVARCHAR(20) NOT NULL,
    
    -- Clasificación
    tipo_proveedor NVARCHAR(30) DEFAULT 'bienes',             -- 'bienes', 'servicios', 'mixto'
    categoria_proveedor NVARCHAR(50) NULL,                    -- 'materia_prima', 'insumos', 'servicios_generales', etc
    
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
    email_cotizaciones NVARCHAR(100) NULL,
    sitio_web NVARCHAR(255) NULL,
    
    -- Condiciones comerciales
    condicion_pago_defecto NVARCHAR(50) NULL,                 -- 'contado', '15_dias', '30_dias', '60_dias'
    dias_credito_defecto INT DEFAULT 0,
    moneda_preferida UNIQUEIDENTIFIER NOT NULL,
    
    -- Datos bancarios
    banco NVARCHAR(100) NULL,
    numero_cuenta NVARCHAR(30) NULL,
    tipo_cuenta NVARCHAR(20) NULL,                            -- 'ahorro', 'corriente', 'interbancaria'
    cci NVARCHAR(20) NULL,                                    -- Código de Cuenta Interbancaria
    
    -- Calificación y evaluación
    calificacion DECIMAL(3,2) NULL,                           -- 0.00 a 5.00
    nivel_confianza NVARCHAR(20) DEFAULT 'medio',             -- 'alto', 'medio', 'bajo'
    es_proveedor_homologado BIT DEFAULT 0,                    -- Si pasó proceso de homologación
    fecha_homologacion DATE NULL,
    
    -- Límites
    limite_credito DECIMAL(18,2) NULL,
    saldo_pendiente DECIMAL(18,2) DEFAULT 0,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'activo',                     -- 'activo', 'inactivo', 'bloqueado', 'evaluacion'
    motivo_bloqueo NVARCHAR(255) NULL,
    es_activo BIT DEFAULT 1 NOT NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    usuario_actualizacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_prov_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_prov_codigo UNIQUE (cliente_id, empresa_id, codigo_proveedor),
    CONSTRAINT UQ_prov_documento UNIQUE (cliente_id, empresa_id, tipo_documento, numero_documento),
    CONSTRAINT FK_prov_pais FOREIGN KEY (pais_id) 
        REFERENCES cat_pais(pais_id) ON DELETE NO ACTION,
    CONSTRAINT FK_prov_departamento FOREIGN KEY (departamento_id) 
        REFERENCES cat_departamento(departamento_id) ON DELETE NO ACTION,
    CONSTRAINT FK_prov_provincia FOREIGN KEY (provincia_id) 
        REFERENCES cat_provincia(provincia_id) ON DELETE NO ACTION,
    CONSTRAINT FK_prov_distrito FOREIGN KEY (distrito_id) 
        REFERENCES cat_distrito(distrito_id) ON DELETE NO ACTION,
    CONSTRAINT FK_prov_moneda FOREIGN KEY (moneda_preferida)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_prov_empresa ON pur_proveedor(empresa_id, es_activo);
CREATE INDEX IDX_prov_documento ON pur_proveedor(numero_documento);
CREATE INDEX IDX_prov_razon_social ON pur_proveedor(razon_social);
CREATE INDEX IDX_prov_categoria ON pur_proveedor(categoria_proveedor) WHERE categoria_proveedor IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Tabla: pur_proveedor_contacto
-- Descripción: Contactos adicionales del proveedor
-- Uso: Múltiples personas de contacto por proveedor
-- Relaciones: Detalle de pur_proveedor
-- -----------------------------------------------------------------------------
CREATE TABLE pur_proveedor_contacto (
    contacto_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    proveedor_id UNIQUEIDENTIFIER NOT NULL,
    
    nombre_completo NVARCHAR(150) NOT NULL,
    cargo NVARCHAR(100) NULL,
    area NVARCHAR(100) NULL,
    
    telefono NVARCHAR(20) NULL,
    telefono_movil NVARCHAR(20) NULL,
    email NVARCHAR(100) NULL,
    
    es_contacto_principal BIT DEFAULT 0,
    es_contacto_cotizaciones BIT DEFAULT 0,
    es_contacto_cobranzas BIT DEFAULT 0,
    
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_provcon_proveedor FOREIGN KEY (proveedor_id) 
        REFERENCES pur_proveedor(proveedor_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_provcon_proveedor ON pur_proveedor_contacto(proveedor_id, es_activo);

-- -----------------------------------------------------------------------------
-- Tabla: pur_producto_proveedor
-- Descripción: Relación producto-proveedor con precios y condiciones
-- Uso: Catálogo de productos que ofrece cada proveedor
-- Relaciones: Vincula inv_producto con pur_proveedor
-- -----------------------------------------------------------------------------
CREATE TABLE pur_producto_proveedor (
    producto_proveedor_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    proveedor_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Identificación del producto en proveedor
    codigo_proveedor NVARCHAR(50) NULL,                       -- SKU/código del proveedor
    descripcion_proveedor NVARCHAR(200) NULL,
    
    -- Precio y condiciones
    precio_unitario DECIMAL(18,4) NOT NULL,
    moneda_id UNIQUEIDENTIFIER NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Compra
    cantidad_minima DECIMAL(18,4) NULL,
    multiplo_compra DECIMAL(18,4) NULL,
    tiempo_entrega_dias INT NULL,
    
    -- Vigencia
    fecha_vigencia_desde DATE NULL,
    fecha_vigencia_hasta DATE NULL,
    
    -- Prioridad
    es_proveedor_preferido BIT DEFAULT 0,
    prioridad INT DEFAULT 3,                                   -- 1=Primera opción, 2=Segunda, etc
    
    -- Estado
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    
    CONSTRAINT FK_prodprov_proveedor FOREIGN KEY (proveedor_id) 
        REFERENCES pur_proveedor(proveedor_id) ON DELETE NO ACTION,
    CONSTRAINT FK_prodprov_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_prodprov_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_prodprov UNIQUE (cliente_id, proveedor_id, producto_id),
    CONSTRAINT FK_prodprov_moneda FOREIGN KEY (moneda_id)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_prodprov_proveedor ON pur_producto_proveedor(proveedor_id, es_activo);
CREATE INDEX IDX_prodprov_producto ON pur_producto_proveedor(producto_id, es_activo);
CREATE INDEX IDX_prodprov_preferido ON pur_producto_proveedor(producto_id, es_proveedor_preferido) 
    WHERE es_proveedor_preferido = 1;

-- -----------------------------------------------------------------------------
-- Tabla: pur_solicitud_compra
-- Descripción: Requerimientos internos de compra (requisiciones)
-- Uso: Solicitudes de compra generadas por áreas/usuarios
-- Relaciones: Antecede a pur_orden_compra
-- -----------------------------------------------------------------------------
CREATE TABLE pur_solicitud_compra (
    solicitud_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_solicitud NVARCHAR(20) NOT NULL,
    fecha_solicitud DATE DEFAULT GETDATE() NOT NULL,
    fecha_requerida DATE NOT NULL,                            -- Fecha en que se necesita
    
    -- Solicitante
    departamento_solicitante_id UNIQUEIDENTIFIER NULL,
    usuario_solicitante_id UNIQUEIDENTIFIER NOT NULL,
    solicitante_nombre NVARCHAR(150) NULL,
    
    -- Destino
    almacen_destino_id UNIQUEIDENTIFIER NULL,
    centro_costo_id UNIQUEIDENTIFIER NULL,
    
    -- Tipo
    tipo_solicitud NVARCHAR(30) DEFAULT 'normal',             -- 'normal', 'urgente', 'proyecto'
    motivo_solicitud NVARCHAR(30) NULL,                       -- 'reposicion', 'nuevo_proyecto', 'mantenimiento', etc
    
    -- Totales
    total_items INT DEFAULT 0,
    total_estimado DECIMAL(18,2) DEFAULT 0,
    moneda_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Estado y aprobación
    estado NVARCHAR(20) DEFAULT 'borrador',                   -- 'borrador', 'pendiente_aprobacion', 'aprobada', 'rechazada', 'procesada', 'anulada'
    requiere_aprobacion BIT DEFAULT 1,
    aprobado_por_usuario_id UNIQUEIDENTIFIER NULL,
    fecha_aprobacion DATETIME NULL,
    
    -- Orden de compra generada
    orden_compra_generada BIT DEFAULT 0,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    motivo_rechazo NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_solcomp_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_solcomp_dpto FOREIGN KEY (departamento_solicitante_id) 
        REFERENCES org_departamento(departamento_id) ON DELETE NO ACTION,
    CONSTRAINT FK_solcomp_almacen FOREIGN KEY (almacen_destino_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION,
    CONSTRAINT FK_solcomp_cc FOREIGN KEY (centro_costo_id) 
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_solcomp_numero UNIQUE (cliente_id, empresa_id, numero_solicitud),
    CONSTRAINT FK_solcomp_moneda FOREIGN KEY (moneda_id)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_solcomp_empresa ON pur_solicitud_compra(empresa_id, fecha_solicitud DESC);
CREATE INDEX IDX_solcomp_estado ON pur_solicitud_compra(estado, fecha_solicitud DESC);
CREATE INDEX IDX_solcomp_solicitante ON pur_solicitud_compra(usuario_solicitante_id);
CREATE INDEX IDX_solcomp_dpto ON pur_solicitud_compra(departamento_solicitante_id) WHERE departamento_solicitante_id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Tabla: pur_solicitud_compra_detalle
-- Descripción: Items solicitados en la requisición
-- Uso: Detalle de productos a comprar
-- Relaciones: Detalle de pur_solicitud_compra
-- -----------------------------------------------------------------------------
CREATE TABLE pur_solicitud_compra_detalle (
    solicitud_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    solicitud_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    cantidad_solicitada DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    precio_referencial DECIMAL(18,4) NULL,
    total_referencial AS (cantidad_solicitada * precio_referencial) PERSISTED,
    
    -- Procesamiento
    cantidad_atendida DECIMAL(18,4) DEFAULT 0,
    cantidad_pendiente AS (cantidad_solicitada - cantidad_atendida) PERSISTED,
    
    observaciones NVARCHAR(500) NULL,
    
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_solcompdet_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_solcompdet_solicitud FOREIGN KEY (solicitud_id) 
        REFERENCES pur_solicitud_compra(solicitud_id) ON DELETE NO ACTION,
    CONSTRAINT FK_solcompdet_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_solcompdet_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_solcompdet_empresa ON pur_solicitud_compra_detalle(empresa_id);
CREATE INDEX IDX_solcompdet_solicitud ON pur_solicitud_compra_detalle(solicitud_id);
CREATE INDEX IDX_solcompdet_producto ON pur_solicitud_compra_detalle(producto_id);

-- -----------------------------------------------------------------------------
-- Tabla: pur_cotizacion
-- Descripción: Cotizaciones solicitadas a proveedores
-- Uso: Proceso de comparación de precios
-- Relaciones: Puede originarse de solicitud de compra
-- -----------------------------------------------------------------------------
CREATE TABLE pur_cotizacion (
    cotizacion_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_cotizacion NVARCHAR(20) NOT NULL,
    fecha_cotizacion DATE DEFAULT GETDATE() NOT NULL,
    fecha_vencimiento DATE NULL,
    
    -- Proveedor
    proveedor_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Referencia
    solicitud_compra_id UNIQUEIDENTIFIER NULL,
    
    -- Condiciones
    condicion_pago NVARCHAR(50) NULL,
    dias_credito INT NULL,
    tiempo_entrega_dias INT NULL,
    lugar_entrega NVARCHAR(255) NULL,
    
    -- Totales
    moneda_id UNIQUEIDENTIFIER NOT NULL,                      -- FK a cat_moneda (CAMBIADO de moneda a moneda_id)
    tipo_cambio DECIMAL(10,4) DEFAULT 1,                      -- NUEVO
    subtotal DECIMAL(18,2) DEFAULT 0,
    descuento DECIMAL(18,2) DEFAULT 0,
    igv DECIMAL(18,2) DEFAULT 0,
    total DECIMAL(18,2) DEFAULT 0,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'pendiente',                  -- 'pendiente', 'recibida', 'evaluada', 'aceptada', 'rechazada', 'vencida'
    es_ganadora BIT DEFAULT 0,                                -- Si fue seleccionada
    
    observaciones NVARCHAR(MAX) NULL,
    motivo_rechazo NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_cotiz_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cotiz_proveedor FOREIGN KEY (proveedor_id) 
        REFERENCES pur_proveedor(proveedor_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cotiz_solicitud FOREIGN KEY (solicitud_compra_id) 
        REFERENCES pur_solicitud_compra(solicitud_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cotiz_moneda FOREIGN KEY (moneda_id)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_cotiz_numero UNIQUE (cliente_id, empresa_id, numero_cotizacion)
);

CREATE INDEX IDX_cotiz_empresa ON pur_cotizacion(empresa_id, fecha_cotizacion DESC);
CREATE INDEX IDX_cotiz_proveedor ON pur_cotizacion(proveedor_id, estado);
CREATE INDEX IDX_cotiz_estado ON pur_cotizacion(estado);
CREATE INDEX IDX_cotiz_ganadora ON pur_cotizacion(es_ganadora) WHERE es_ganadora = 1;

-- -----------------------------------------------------------------------------
-- Tabla: pur_cotizacion_detalle
-- Descripción: Items cotizados
-- Uso: Productos y precios ofrecidos por proveedor
-- Relaciones: Detalle de pur_cotizacion
-- -----------------------------------------------------------------------------
CREATE TABLE pur_cotizacion_detalle (
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
    total AS (cantidad * precio_unitario * (1 - descuento_porcentaje / 100)) PERSISTED,
    
    tiempo_entrega_dias INT NULL,
    observaciones NVARCHAR(500) NULL,
    
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_cotizdet_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cotizdet_cotizacion FOREIGN KEY (cotizacion_id) 
        REFERENCES pur_cotizacion(cotizacion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cotizdet_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cotizdet_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_cotizdet_empresa ON pur_cotizacion_detalle(empresa_id);
CREATE INDEX IDX_cotizdet_cotizacion ON pur_cotizacion_detalle(cotizacion_id);
CREATE INDEX IDX_cotizdet_producto ON pur_cotizacion_detalle(producto_id);

-- -----------------------------------------------------------------------------
-- Tabla: pur_orden_compra
-- Descripción: Orden de compra (documento contractual con proveedor)
-- Uso: Formalización de compra de bienes o servicios
-- Relaciones: Genera movimientos de inventario al recepcionar
-- -----------------------------------------------------------------------------
CREATE TABLE pur_orden_compra (
    orden_compra_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_oc NVARCHAR(20) NOT NULL,
    fecha_emision DATE DEFAULT GETDATE() NOT NULL,
    fecha_requerida DATE NOT NULL,                            -- Fecha esperada de entrega
    
    -- Proveedor
    proveedor_id UNIQUEIDENTIFIER NOT NULL,
    proveedor_razon_social NVARCHAR(200) NULL,                -- Desnormalizado
    proveedor_ruc NVARCHAR(20) NULL,
    
    -- Destino
    almacen_destino_id UNIQUEIDENTIFIER NULL,
    direccion_entrega NVARCHAR(255) NULL,
    
    -- Referencias
    solicitud_compra_id UNIQUEIDENTIFIER NULL,
    cotizacion_id UNIQUEIDENTIFIER NULL,
    
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
    
    -- Control de recepción
    total_items INT DEFAULT 0,
    items_recepcionados INT DEFAULT 0,
    porcentaje_recepcion DECIMAL(5,2) DEFAULT 0,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'borrador',                   -- 'borrador', 'emitida', 'aprobada', 'parcial', 'completa', 'anulada'
    requiere_aprobacion BIT DEFAULT 1,
    aprobado_por_usuario_id UNIQUEIDENTIFIER NULL,
    fecha_aprobacion DATETIME NULL,
    
    -- Centro de costo
    centro_costo_id UNIQUEIDENTIFIER NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    terminos_condiciones NVARCHAR(MAX) NULL,
    motivo_anulacion NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    fecha_anulacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    usuario_aprobacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_oc_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_oc_proveedor FOREIGN KEY (proveedor_id) 
        REFERENCES pur_proveedor(proveedor_id) ON DELETE NO ACTION,
    CONSTRAINT FK_oc_almacen FOREIGN KEY (almacen_destino_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION,
    CONSTRAINT FK_oc_solicitud FOREIGN KEY (solicitud_compra_id) 
        REFERENCES pur_solicitud_compra(solicitud_id) ON DELETE NO ACTION,
    CONSTRAINT FK_oc_cotizacion FOREIGN KEY (cotizacion_id) 
        REFERENCES pur_cotizacion(cotizacion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_oc_cc FOREIGN KEY (centro_costo_id) 
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE NO ACTION,
    CONSTRAINT FK_oc_moneda FOREIGN KEY (moneda_id)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_oc_numero UNIQUE (cliente_id, empresa_id, numero_oc)
);

CREATE INDEX IDX_oc_empresa ON pur_orden_compra(empresa_id, fecha_emision DESC);
CREATE INDEX IDX_oc_proveedor ON pur_orden_compra(proveedor_id, estado);
CREATE INDEX IDX_oc_estado ON pur_orden_compra(estado, fecha_emision DESC);
CREATE INDEX IDX_oc_fecha_requerida ON pur_orden_compra(fecha_requerida, estado);
CREATE INDEX IDX_oc_solicitud ON pur_orden_compra(solicitud_compra_id) WHERE solicitud_compra_id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Tabla: pur_orden_compra_detalle
-- Descripción: Items de la orden de compra
-- Uso: Productos o servicios a comprar
-- Relaciones: Detalle de pur_orden_compra
-- -----------------------------------------------------------------------------
CREATE TABLE pur_orden_compra_detalle (
    orden_compra_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    orden_compra_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Cantidad y unidad
    cantidad_ordenada DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Precios
    precio_unitario DECIMAL(18,4) NOT NULL,
    descuento_porcentaje DECIMAL(5,2) DEFAULT 0,
    precio_neto AS (precio_unitario * (1 - descuento_porcentaje / 100)) PERSISTED,
    subtotal AS (cantidad_ordenada * precio_unitario * (1 - descuento_porcentaje / 100)) PERSISTED,
    igv AS (cantidad_ordenada * precio_unitario * (1 - descuento_porcentaje / 100) * 0.18) PERSISTED,
    total AS (cantidad_ordenada * precio_unitario * (1 - descuento_porcentaje / 100) * 1.18) PERSISTED,
    
    -- Control de recepción
    cantidad_recepcionada DECIMAL(18,4) DEFAULT 0,
    cantidad_pendiente AS (cantidad_ordenada - cantidad_recepcionada) PERSISTED,
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    especificaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_ocdet_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_ocdet_oc FOREIGN KEY (orden_compra_id) 
        REFERENCES pur_orden_compra(orden_compra_id) ON DELETE NO ACTION,
    CONSTRAINT FK_ocdet_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_ocdet_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_ocdet_empresa ON pur_orden_compra_detalle(empresa_id);
CREATE INDEX IDX_ocdet_oc ON pur_orden_compra_detalle(orden_compra_id);
CREATE INDEX IDX_ocdet_producto ON pur_orden_compra_detalle(producto_id);
CREATE INDEX IDX_ocdet_pendiente ON pur_orden_compra_detalle(orden_compra_id, cantidad_ordenada) 
    WHERE cantidad_ordenada > 0;

-- -----------------------------------------------------------------------------
-- Tabla: pur_recepcion
-- Descripción: Recepción de mercadería
-- Uso: Registro de entrada física de productos comprados
-- Relaciones: Vinculada a OC, genera movimiento de inventario
-- -----------------------------------------------------------------------------
CREATE TABLE pur_recepcion (
    recepcion_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_recepcion NVARCHAR(20) NOT NULL,
    fecha_recepcion DATETIME DEFAULT GETDATE() NOT NULL,
    
    -- Orden de compra
    orden_compra_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Proveedor
    proveedor_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Almacén
    almacen_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Documento de transporte
    guia_remision_numero NVARCHAR(30) NULL,
    guia_remision_fecha DATE NULL,
    transportista NVARCHAR(150) NULL,
    placa_vehiculo NVARCHAR(15) NULL,
    
    -- Responsable recepción
    recepcionado_por_usuario_id UNIQUEIDENTIFIER NULL,
    recepcionado_por_nombre NVARCHAR(150) NULL,
    
    -- Totales
    total_items INT DEFAULT 0,
    total_cantidad DECIMAL(18,4) DEFAULT 0,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'borrador',                   -- 'borrador', 'procesada', 'inspeccion', 'aprobada', 'anulada'
    requiere_inspeccion BIT DEFAULT 0,                        -- Si requiere QMS
    inspeccion_id UNIQUEIDENTIFIER NULL,                      -- FK a qms_inspeccion
    
    -- Movimiento de inventario generado
    movimiento_inventario_id UNIQUEIDENTIFIER NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    incidencias NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_procesado DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    usuario_procesado_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_recep_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_recep_oc FOREIGN KEY (orden_compra_id) 
        REFERENCES pur_orden_compra(orden_compra_id) ON DELETE NO ACTION,
    CONSTRAINT FK_recep_proveedor FOREIGN KEY (proveedor_id) 
        REFERENCES pur_proveedor(proveedor_id) ON DELETE NO ACTION,
    CONSTRAINT FK_recep_almacen FOREIGN KEY (almacen_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_recep_numero UNIQUE (cliente_id, empresa_id, numero_recepcion)
);

CREATE INDEX IDX_recep_empresa ON pur_recepcion(empresa_id, fecha_recepcion DESC);
CREATE INDEX IDX_recep_oc ON pur_recepcion(orden_compra_id);
CREATE INDEX IDX_recep_estado ON pur_recepcion(estado);
CREATE INDEX IDX_recep_almacen ON pur_recepcion(almacen_id);

-- -----------------------------------------------------------------------------
-- Tabla: pur_recepcion_detalle
-- Descripción: Items recepcionados
-- Uso: Productos recibidos con cantidades
-- Relaciones: Detalle de pur_recepcion
-- -----------------------------------------------------------------------------
CREATE TABLE pur_recepcion_detalle (
    recepcion_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    recepcion_id UNIQUEIDENTIFIER NOT NULL,
    orden_compra_detalle_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Cantidad
    cantidad_ordenada DECIMAL(18,4) NOT NULL,                 -- Según OC
    cantidad_recepcionada DECIMAL(18,4) NOT NULL,             -- Real recibida
    diferencia AS (cantidad_recepcionada - cantidad_ordenada) PERSISTED,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Lote y vencimiento
    lote NVARCHAR(50) NULL,
    fecha_vencimiento DATE NULL,
    
    -- Costeo
    precio_unitario DECIMAL(18,4) DEFAULT 0,
    total AS (cantidad_recepcionada * precio_unitario) PERSISTED,
    
    -- Ubicación
    ubicacion_almacen NVARCHAR(50) NULL,
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    motivo_diferencia NVARCHAR(255) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_recepdet_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_recepdet_recepcion FOREIGN KEY (recepcion_id) 
        REFERENCES pur_recepcion(recepcion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_recepdet_ocdet FOREIGN KEY (orden_compra_detalle_id) 
        REFERENCES pur_orden_compra_detalle(orden_compra_detalle_id) ON DELETE NO ACTION,
    CONSTRAINT FK_recepdet_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_recepdet_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_recepdet_empresa ON pur_recepcion_detalle(empresa_id);
CREATE INDEX IDX_recepdet_recepcion ON pur_recepcion_detalle(recepcion_id);
CREATE INDEX IDX_recepdet_ocdet ON pur_recepcion_detalle(orden_compra_detalle_id);
CREATE INDEX IDX_recepdet_producto ON pur_recepcion_detalle(producto_id);
