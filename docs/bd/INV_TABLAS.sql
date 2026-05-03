-- ============================================================================
-- SECCIÓN 2: INV - INVENTARIOS Y ALMACENES
-- ============================================================================
-- DESCRIPCIÓN: Gestión de productos, almacenes, movimientos de stock
-- DEPENDENCIAS: ORG (empresa, sucursal)
-- USADO POR: PUR (compras), SLS (ventas), MFG (producción), CST (costos)
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: inv_categoria_producto
-- Descripción: Categorización jerárquica de productos
-- Uso: Clasificar productos para reportes, búsquedas y análisis
-- Relaciones: Usado por inv_producto
-- -----------------------------------------------------------------------------
CREATE TABLE inv_categoria_producto (
    categoria_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    codigo NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(255) NULL,
    
    -- Jerarquía
    categoria_padre_id UNIQUEIDENTIFIER NULL,                 -- Para sub-categorías
    nivel INT DEFAULT 1,
    ruta_jerarquica NVARCHAR(500) NULL,                       -- Ej: "Textiles/Telas/Algodón"
    
    -- Configuración contable (usado por FIN y CST)
    cuenta_contable_inventario NVARCHAR(20) NULL,             -- Cuenta contable para inventarios de esta categoría
    cuenta_contable_costo_venta NVARCHAR(20) NULL,            -- Cuenta contable para costo de ventas
    
    -- Configuración de costeo
    metodo_costeo_defecto NVARCHAR(20) NULL,                  -- 'promedio', 'fifo', 'lifo', 'estandar'
    
    -- Estado y auditoría
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_cat_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cat_padre FOREIGN KEY (categoria_padre_id) 
        REFERENCES inv_categoria_producto(categoria_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_cat_codigo UNIQUE (cliente_id, empresa_id, codigo)
);

CREATE INDEX IDX_cat_empresa ON inv_categoria_producto(empresa_id, es_activo);
CREATE INDEX IDX_cat_padre ON inv_categoria_producto(categoria_padre_id);

-- -----------------------------------------------------------------------------
-- Tabla: inv_unidad_medida
-- Descripción: Unidades de medida y conversiones
-- Uso: Manejo de múltiples unidades (kg, unidad, caja, etc)
-- Relaciones: Usado por inv_producto, pur_orden_compra, sls_pedido
-- -----------------------------------------------------------------------------
CREATE TABLE inv_unidad_medida (
    unidad_medida_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    codigo NVARCHAR(10) NOT NULL,                             -- Ej: "UN", "KG", "MT", "LT"
    nombre NVARCHAR(50) NOT NULL,                             -- Ej: "Unidad", "Kilogramo", "Metro", "Litro"
    simbolo NVARCHAR(10) NULL,                                -- Ej: "kg", "m", "L"
    tipo_unidad NVARCHAR(20) NOT NULL,                        -- 'cantidad', 'peso', 'volumen', 'longitud', 'area', 'tiempo'
    
    -- Unidad base (para conversiones)
    es_unidad_base BIT DEFAULT 0,                             -- Si es la unidad base del tipo (ej: kg para peso)
    factor_conversion_base DECIMAL(18,6) NULL,                -- Factor para convertir a unidad base
    
    -- Configuración
    decimales_permitidos INT DEFAULT 2,                       -- Decimales permitidos para esta unidad
    
    -- Estado y auditoría
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_um_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_um_codigo UNIQUE (cliente_id, empresa_id, codigo)
);

CREATE INDEX IDX_um_empresa ON inv_unidad_medida(empresa_id, es_activo);
CREATE INDEX IDX_um_tipo ON inv_unidad_medida(tipo_unidad);

-- -----------------------------------------------------------------------------
-- Tabla: inv_producto
-- Descripción: Catálogo maestro de productos/artículos
-- Uso: Productos que se compran, venden, producen o almacenan
-- Relaciones: Base para todo el sistema de inventarios
-- -----------------------------------------------------------------------------
CREATE TABLE inv_producto (
    producto_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Identificación
    codigo_sku NVARCHAR(50) NOT NULL,                         -- SKU único del producto
    codigo_barra NVARCHAR(50) NULL,                           -- Código de barras EAN/UPC
    codigo_interno NVARCHAR(30) NULL,                         -- Código interno adicional
    codigo_fabricante NVARCHAR(50) NULL,                      -- Part number del fabricante
    
    -- Datos básicos
    nombre NVARCHAR(200) NOT NULL,
    nombre_corto NVARCHAR(100) NULL,
    descripcion NVARCHAR(MAX) NULL,
    descripcion_corta NVARCHAR(500) NULL,
    
    -- Clasificación
    categoria_id UNIQUEIDENTIFIER NULL,
    subcategoria_id UNIQUEIDENTIFIER NULL,
    marca NVARCHAR(100) NULL,
    modelo NVARCHAR(100) NULL,
    linea_producto NVARCHAR(100) NULL,                        -- Línea de producto (ej: "Premium", "Económica")
    
    -- Tipo de producto (flexible para todas las industrias)
    tipo_producto NVARCHAR(30) NOT NULL,                      -- 'bien', 'servicio', 'materia_prima', 'producto_terminado', 'semi_elaborado', 'insumo'
    subtipo_producto NVARCHAR(50) NULL,                       -- Personalizable según industria
    
    -- Unidades de medida
    unidad_medida_base_id UNIQUEIDENTIFIER NOT NULL,          -- Unidad base (ej: "UN", "KG")
    unidad_medida_compra_id UNIQUEIDENTIFIER NULL,            -- Unidad en que se compra (puede diferir de la base)
    unidad_medida_venta_id UNIQUEIDENTIFIER NULL,             -- Unidad en que se vende
    factor_conversion_compra DECIMAL(18,6) DEFAULT 1,         -- Factor de conversión compra -> base
    factor_conversion_venta DECIMAL(18,6) DEFAULT 1,          -- Factor de conversión venta -> base
    
    -- Características físicas (adaptable según industria)
    peso_kg DECIMAL(12,4) NULL,                               -- Peso en kilogramos
    volumen_m3 DECIMAL(12,6) NULL,                            -- Volumen en metros cúbicos
    largo_cm DECIMAL(10,2) NULL,
    ancho_cm DECIMAL(10,2) NULL,
    alto_cm DECIMAL(10,2) NULL,
    color NVARCHAR(50) NULL,
    talla NVARCHAR(20) NULL,
    
    -- Características específicas (JSON flexible para atributos personalizados por industria)
    atributos_personalizados NVARCHAR(MAX) NULL,              -- JSON: {"dureza":"HRC 58-62", "acabado":"cromado", etc}
    especificaciones_tecnicas NVARCHAR(MAX) NULL,             -- JSON o texto con especificaciones
    
    -- Configuración de inventario
    maneja_inventario BIT DEFAULT 1,                          -- Si controla stock (servicios pueden ser 0)
    maneja_lotes BIT DEFAULT 0,                               -- Si maneja lotes de producción
    maneja_series BIT DEFAULT 0,                              -- Si maneja números de serie
    maneja_vencimiento BIT DEFAULT 0,                         -- Si tiene fecha de vencimiento
    dias_vida_util INT NULL,                                  -- Días de vida útil del producto
    requiere_refrigeracion BIT DEFAULT 0,                     -- Si requiere cadena de frío
    es_perecible BIT DEFAULT 0,
    
    -- Stock mínimos y máximos (por producto, luego se detalla por almacén)
    stock_minimo DECIMAL(18,4) NULL,
    stock_maximo DECIMAL(18,4) NULL,
    punto_reorden DECIMAL(18,4) NULL,                         -- Cuando llega a este stock, se debe reordenar
    
    -- Configuración de compras
    es_comprable BIT DEFAULT 1,
    tiempo_entrega_dias INT NULL,                             -- Lead time de compra
    cantidad_minima_compra DECIMAL(18,4) NULL,
    multiplo_compra DECIMAL(18,4) NULL,                       -- Debe comprarse en múltiplos de esta cantidad
    
    -- Configuración de ventas
    es_vendible BIT DEFAULT 1,
    requiere_autorizacion_venta BIT DEFAULT 0,
    
    -- Configuración de producción (MFG)
    es_fabricable BIT DEFAULT 0,                              -- Si se produce internamente
    tiene_lista_materiales BIT DEFAULT 0,                     -- Si tiene BOM (Bill of Materials)
    
    -- Costos (CST)
    metodo_costeo NVARCHAR(20) DEFAULT 'promedio',            -- 'promedio', 'fifo', 'lifo', 'estandar'
    costo_estandar DECIMAL(18,4) NULL,
    costo_ultima_compra DECIMAL(18,4) NULL,
    costo_promedio DECIMAL(18,4) NULL,
    moneda_costo NVARCHAR(3) DEFAULT 'PEN',
    
    -- Precios (PRC)
    precio_base_venta DECIMAL(18,4) NULL,
    moneda_venta NVARCHAR(3) DEFAULT 'PEN',
    afecto_igv BIT DEFAULT 1,                                 -- Si está afecto a impuestos
    porcentaje_igv DECIMAL(5,2) DEFAULT 18.00,
    
    -- Tributario (TAX)
    codigo_sunat NVARCHAR(10) NULL,                           -- Código SUNAT para facturación electrónica
    tipo_afectacion_igv NVARCHAR(2) NULL,                     -- '10' = Gravado, '20' = Exonerado, etc
    
    -- Imágenes y archivos
    imagen_principal_url NVARCHAR(500) NULL,
    imagenes_adicionales NVARCHAR(MAX) NULL,                  -- JSON array de URLs
    ficha_tecnica_url NVARCHAR(500) NULL,
    
    -- Proveedor habitual (PUR)
    proveedor_habitual_id UNIQUEIDENTIFIER NULL,              -- FK a pur_proveedor (se creará en módulo PUR)
    
    -- Estado y auditoría
    estado NVARCHAR(20) DEFAULT 'activo',                     -- 'activo', 'inactivo', 'descontinuado', 'en_desarrollo'
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    usuario_actualizacion_id UNIQUEIDENTIFIER NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    CONSTRAINT FK_prod_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_prod_categoria FOREIGN KEY (categoria_id) 
        REFERENCES inv_categoria_producto(categoria_id) ON DELETE NO ACTION,
    CONSTRAINT FK_prod_um_base FOREIGN KEY (unidad_medida_base_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT FK_prod_um_compra FOREIGN KEY (unidad_medida_compra_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT FK_prod_um_venta FOREIGN KEY (unidad_medida_venta_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_prod_sku UNIQUE (cliente_id, empresa_id, codigo_sku)
);

CREATE INDEX IDX_prod_empresa ON inv_producto(empresa_id, es_activo);
CREATE INDEX IDX_prod_categoria ON inv_producto(categoria_id) WHERE categoria_id IS NOT NULL;
CREATE INDEX IDX_prod_tipo ON inv_producto(tipo_producto, es_activo);
CREATE INDEX IDX_prod_codigo_barra ON inv_producto(codigo_barra) WHERE codigo_barra IS NOT NULL;
CREATE INDEX IDX_prod_nombre ON inv_producto(nombre);
CREATE INDEX IDX_prod_comprable ON inv_producto(es_comprable) WHERE es_comprable = 1;
CREATE INDEX IDX_prod_vendible ON inv_producto(es_vendible) WHERE es_vendible = 1;

-- -----------------------------------------------------------------------------
-- Tabla: inv_almacen
-- Descripción: Almacenes físicos donde se almacena inventario
-- Uso: Control de stock por ubicación física
-- Relaciones: Vinculado a org_sucursal, usado por movimientos de inventario
-- -----------------------------------------------------------------------------
CREATE TABLE inv_almacen (
    almacen_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    sucursal_id UNIQUEIDENTIFIER NULL,                        -- Sucursal a la que pertenece
    
    codigo NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(255) NULL,
    
    -- Tipo y clasificación
    tipo_almacen NVARCHAR(30) NOT NULL,                       -- 'general', 'materia_prima', 'producto_terminado', 'transito', 'consignacion', 'cuarentena'
    
    -- Ubicación
    direccion NVARCHAR(255) NULL,
    responsable_usuario_id UNIQUEIDENTIFIER NULL,
    responsable_nombre NVARCHAR(150) NULL,
    
    -- Configuración
    es_almacen_principal BIT DEFAULT 0,
    permite_ventas BIT DEFAULT 0,                             -- Si se puede vender desde este almacén
    permite_compras BIT DEFAULT 1,                            -- Si se reciben compras
    permite_produccion BIT DEFAULT 0,                         -- Si recibe/despacha producción
    
    -- Capacidad
    capacidad_m3 DECIMAL(12,2) NULL,                          -- Capacidad en metros cúbicos
    capacidad_kg DECIMAL(12,2) NULL,                          -- Capacidad en kilogramos
    capacidad_unidades INT NULL,                              -- Capacidad en unidades/pallets
    
    -- Centro de costo
    centro_costo_id UNIQUEIDENTIFIER NULL,
    
    -- Estado y auditoría
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_alm_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_alm_sucursal FOREIGN KEY (sucursal_id) 
        REFERENCES org_sucursal(sucursal_id) ON DELETE NO ACTION,
    CONSTRAINT FK_alm_cc FOREIGN KEY (centro_costo_id) 
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_alm_codigo UNIQUE (cliente_id, empresa_id, codigo)
);

CREATE INDEX IDX_alm_empresa ON inv_almacen(empresa_id, es_activo);
CREATE INDEX IDX_alm_sucursal ON inv_almacen(sucursal_id) WHERE sucursal_id IS NOT NULL;
CREATE INDEX IDX_alm_tipo ON inv_almacen(tipo_almacen);

-- -----------------------------------------------------------------------------
-- Tabla: inv_stock
-- Descripción: Stock actual de productos por almacén
-- Uso: Consulta rápida de stock disponible
-- Relaciones: Actualizado por inv_movimiento
-- -----------------------------------------------------------------------------
CREATE TABLE inv_stock (
    stock_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    almacen_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Cantidades
    cantidad_actual DECIMAL(18,4) DEFAULT 0 NOT NULL,         -- Stock físico actual
    cantidad_reservada DECIMAL(18,4) DEFAULT 0,               -- Reservado para pedidos/producción
    cantidad_disponible AS (cantidad_actual - cantidad_reservada) PERSISTED,  -- Stock disponible = actual - reservado
    cantidad_transito DECIMAL(18,4) DEFAULT 0,                -- En tránsito (compras pendientes)
    
    -- Valores
    costo_promedio DECIMAL(18,4) DEFAULT 0,                   -- Costo promedio unitario
    valor_total AS (cantidad_actual * costo_promedio) PERSISTED, -- Valor total del stock
    moneda NVARCHAR(3) DEFAULT 'PEN',
    
    -- Control
    stock_minimo DECIMAL(18,4) NULL,                          -- Mínimo específico para este almacén
    stock_maximo DECIMAL(18,4) NULL,
    punto_reorden DECIMAL(18,4) NULL,
    
    -- Ubicación física (WMS)
    ubicacion_almacen NVARCHAR(50) NULL,                      -- Ej: "Pasillo 3-Rack A-Nivel 2"
    
    -- Auditoría
    fecha_ultimo_movimiento DATETIME NULL,
    fecha_ultima_compra DATETIME NULL,
    fecha_ultima_venta DATETIME NULL,
    fecha_actualizacion DATETIME DEFAULT GETDATE(),
    
    CONSTRAINT FK_stock_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_stock_almacen FOREIGN KEY (almacen_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_stock_prod_alm UNIQUE (cliente_id, producto_id, almacen_id)
);

CREATE INDEX IDX_stock_producto ON inv_stock(producto_id);
CREATE INDEX IDX_stock_almacen ON inv_stock(almacen_id);
CREATE INDEX IDX_stock_disponible ON inv_stock(cantidad_actual) WHERE cantidad_actual > 0;
CREATE INDEX IDX_stock_bajo ON inv_stock(producto_id, almacen_id, cantidad_disponible, stock_minimo);

-- -----------------------------------------------------------------------------
-- Tabla: inv_tipo_movimiento
-- Descripción: Catálogo de tipos de movimientos de inventario
-- Uso: Clasificar entradas, salidas, ajustes, transferencias
-- Relaciones: Usado por inv_movimiento
-- -----------------------------------------------------------------------------
CREATE TABLE inv_tipo_movimiento (
    tipo_movimiento_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo NVARCHAR(20) NOT NULL,                             -- Ej: "COMP", "VENT", "AJUS", "TRANS"
    nombre NVARCHAR(100) NOT NULL,                            -- Ej: "Compra", "Venta", "Ajuste de Inventario"
    descripcion NVARCHAR(255) NULL,
    
    -- Clasificación
    clase_movimiento NVARCHAR(20) NOT NULL,                   -- 'entrada', 'salida', 'transferencia', 'ajuste'
    afecta_costo BIT DEFAULT 1,                               -- Si afecta el costo del producto
    requiere_autorizacion BIT DEFAULT 0,
    
    -- Contabilización
    genera_asiento_contable BIT DEFAULT 0,                    -- Si genera movimiento contable (FIN)
    cuenta_contable_debito NVARCHAR(20) NULL,
    cuenta_contable_credito NVARCHAR(20) NULL,
    
    -- Configuración
    requiere_documento_referencia BIT DEFAULT 0,              -- Si requiere documento (OC, factura, etc)
    tipo_documento_referencia NVARCHAR(50) NULL,              -- Tipos permitidos
    
    -- Estado y auditoría
    es_activo BIT DEFAULT 1 NOT NULL,
    es_tipo_sistema BIT DEFAULT 0,                            -- Si es tipo predefinido del sistema
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_tm_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_tm_codigo UNIQUE (cliente_id, empresa_id, codigo)
);

CREATE INDEX IDX_tm_empresa ON inv_tipo_movimiento(empresa_id, es_activo);
CREATE INDEX IDX_tm_clase ON inv_tipo_movimiento(clase_movimiento);

-- -----------------------------------------------------------------------------
-- Tabla: inv_movimiento
-- Descripción: Cabecera de movimientos de inventario
-- Uso: Registro de todas las transacciones que afectan el stock
-- Relaciones: Relacionado con PUR, SLS, MFG según el origen del movimiento
-- -----------------------------------------------------------------------------
CREATE TABLE inv_movimiento (
    movimiento_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Identificación
    numero_movimiento NVARCHAR(20) NOT NULL,                  -- Número correlativo único
    tipo_movimiento_id UNIQUEIDENTIFIER NOT NULL,
    fecha_movimiento DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_contable DATE NOT NULL,                             -- Fecha para contabilización
    
    -- Almacenes (origen y destino para transferencias)
    almacen_origen_id UNIQUEIDENTIFIER NULL,
    almacen_destino_id UNIQUEIDENTIFIER NULL,
    
    -- Referencias
    modulo_origen NVARCHAR(10) NULL,                          -- 'PUR', 'SLS', 'MFG', 'INV' (manual)
    documento_referencia_tipo NVARCHAR(20) NULL,              -- 'orden_compra', 'factura_venta', 'orden_produccion'
    documento_referencia_id UNIQUEIDENTIFIER NULL,            -- ID del documento origen
    documento_referencia_numero NVARCHAR(30) NULL,            -- Número del documento
    
    -- Tercero (proveedor/cliente según tipo movimiento)
    tercero_tipo NVARCHAR(20) NULL,                           -- 'proveedor', 'cliente', 'empleado'
    tercero_id UNIQUEIDENTIFIER NULL,                         -- ID del tercero
    tercero_nombre NVARCHAR(200) NULL,
    
    -- Totales
    total_items INT DEFAULT 0,
    total_cantidad DECIMAL(18,4) DEFAULT 0,
    total_costo DECIMAL(18,4) DEFAULT 0,
    moneda NVARCHAR(3) DEFAULT 'PEN',
    
    -- Estado y control
    estado NVARCHAR(20) DEFAULT 'borrador',                   -- 'borrador', 'autorizado', 'procesado', 'anulado'
    requiere_autorizacion BIT DEFAULT 0,
    autorizado_por_usuario_id UNIQUEIDENTIFIER NULL,
    fecha_autorizacion DATETIME NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    motivo_anulacion NVARCHAR(500) NULL,
    
    -- Centro de costo
    centro_costo_id UNIQUEIDENTIFIER NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    fecha_procesado DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    usuario_procesado_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_mov_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_mov_tipo FOREIGN KEY (tipo_movimiento_id) 
        REFERENCES inv_tipo_movimiento(tipo_movimiento_id) ON DELETE NO ACTION,
    CONSTRAINT FK_mov_alm_origen FOREIGN KEY (almacen_origen_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION,
    CONSTRAINT FK_mov_alm_destino FOREIGN KEY (almacen_destino_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION,
    CONSTRAINT FK_mov_cc FOREIGN KEY (centro_costo_id) 
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_mov_numero UNIQUE (cliente_id, empresa_id, numero_movimiento)
);

CREATE INDEX IDX_mov_empresa ON inv_movimiento(empresa_id, fecha_movimiento DESC);
CREATE INDEX IDX_mov_tipo ON inv_movimiento(tipo_movimiento_id, estado);
CREATE INDEX IDX_mov_fecha ON inv_movimiento(fecha_movimiento DESC);
CREATE INDEX IDX_mov_estado ON inv_movimiento(estado);
CREATE INDEX IDX_mov_almacen_origen ON inv_movimiento(almacen_origen_id) WHERE almacen_origen_id IS NOT NULL;
CREATE INDEX IDX_mov_almacen_destino ON inv_movimiento(almacen_destino_id) WHERE almacen_destino_id IS NOT NULL;
CREATE INDEX IDX_mov_referencia ON inv_movimiento(modulo_origen, documento_referencia_id) 
    WHERE documento_referencia_id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Tabla: inv_movimiento_detalle
-- Descripción: Detalle de productos en cada movimiento
-- Uso: Items específicos del movimiento con cantidades y costos
-- Relaciones: Detalle de inv_movimiento, actualiza inv_stock
-- -----------------------------------------------------------------------------
CREATE TABLE inv_movimiento_detalle (
    movimiento_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    movimiento_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Cantidad y unidad
    cantidad DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    cantidad_base DECIMAL(18,4) NOT NULL,                     -- Cantidad convertida a unidad base
    
    -- Costos
    costo_unitario DECIMAL(18,4) DEFAULT 0,                   -- Costo por unidad
    costo_total AS (cantidad * costo_unitario) PERSISTED,
    moneda NVARCHAR(3) DEFAULT 'PEN',
    
    -- Lote y vencimiento (si aplica)
    lote NVARCHAR(50) NULL,
    fecha_vencimiento DATE NULL,
    numero_serie NVARCHAR(100) NULL,
    
    -- Ubicación (WMS)
    ubicacion_almacen NVARCHAR(50) NULL,
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_movdet_movimiento FOREIGN KEY (movimiento_id) 
        REFERENCES inv_movimiento(movimiento_id) ON DELETE NO ACTION,
    CONSTRAINT FK_movdet_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_movdet_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_movdet_movimiento ON inv_movimiento_detalle(movimiento_id);
CREATE INDEX IDX_movdet_producto ON inv_movimiento_detalle(producto_id);
CREATE INDEX IDX_movdet_lote ON inv_movimiento_detalle(lote) WHERE lote IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Tabla: inv_inventario_fisico
-- Descripción: Tomas de inventario físico (conteos)
-- Uso: Auditorías y ajustes de stock por conteo físico
-- Relaciones: Genera movimientos de ajuste en inv_movimiento
-- -----------------------------------------------------------------------------
CREATE TABLE inv_inventario_fisico (
    inventario_fisico_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_inventario NVARCHAR(20) NOT NULL,
    fecha_inventario DATE NOT NULL,
    almacen_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Alcance
    tipo_inventario NVARCHAR(20) NOT NULL,                    -- 'total', 'ciclico', 'selectivo'
    descripcion NVARCHAR(255) NULL,
    
    -- Filtros (si es inventario selectivo)
    categoria_id UNIQUEIDENTIFIER NULL,
    ubicacion_almacen NVARCHAR(50) NULL,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'en_proceso',                 -- 'en_proceso', 'finalizado', 'ajustado', 'anulado'
    
    -- Responsables
    supervisor_usuario_id UNIQUEIDENTIFIER NULL,
    supervisor_nombre NVARCHAR(150) NULL,
    
    -- Resultados
    total_productos_contados INT DEFAULT 0,
    total_diferencias INT DEFAULT 0,
    valor_diferencias DECIMAL(18,4) DEFAULT 0,
    movimiento_ajuste_id UNIQUEIDENTIFIER NULL,               -- FK al movimiento de ajuste generado
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_finalizacion DATETIME NULL,
    fecha_ajuste DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_invfis_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_invfis_almacen FOREIGN KEY (almacen_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION,
    CONSTRAINT FK_invfis_categoria FOREIGN KEY (categoria_id) 
        REFERENCES inv_categoria_producto(categoria_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_invfis_numero UNIQUE (cliente_id, empresa_id, numero_inventario)
);

CREATE INDEX IDX_invfis_empresa ON inv_inventario_fisico(empresa_id, fecha_inventario DESC);
CREATE INDEX IDX_invfis_almacen ON inv_inventario_fisico(almacen_id, estado);
CREATE INDEX IDX_invfis_estado ON inv_inventario_fisico(estado);

-- -----------------------------------------------------------------------------
-- Tabla: inv_inventario_fisico_detalle
-- Descripción: Detalle de conteos por producto
-- Uso: Registro de cantidades contadas vs sistema
-- Relaciones: Detalle de inv_inventario_fisico
-- -----------------------------------------------------------------------------
CREATE TABLE inv_inventario_fisico_detalle (
    inventario_fisico_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    inventario_fisico_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Cantidades
    cantidad_sistema DECIMAL(18,4) NOT NULL,                  -- Stock según sistema
    cantidad_contada DECIMAL(18,4) NULL,                      -- Stock contado físicamente
    diferencia AS (cantidad_contada - cantidad_sistema) PERSISTED,
    
    -- Lote (si maneja)
    lote NVARCHAR(50) NULL,
    fecha_vencimiento DATE NULL,
    
    -- Ubicación
    ubicacion_almacen NVARCHAR(50) NULL,
    
    -- Costeo
    costo_unitario DECIMAL(18,4) DEFAULT 0,
    valor_diferencia AS ((cantidad_contada - cantidad_sistema) * costo_unitario) PERSISTED,
    
    -- Control de conteo
    estado_conteo NVARCHAR(20) DEFAULT 'pendiente',           -- 'pendiente', 'contado', 'recontado', 'ajustado'
    contador_usuario_id UNIQUEIDENTIFIER NULL,
    contador_nombre NVARCHAR(150) NULL,
    fecha_conteo DATETIME NULL,
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    motivo_diferencia NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_invfisdet_invfis FOREIGN KEY (inventario_fisico_id) 
        REFERENCES inv_inventario_fisico(inventario_fisico_id) ON DELETE NO ACTION,
    CONSTRAINT FK_invfisdet_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_invfisdet_invfis ON inv_inventario_fisico_detalle(inventario_fisico_id);
CREATE INDEX IDX_invfisdet_producto ON inv_inventario_fisico_detalle(producto_id);
CREATE INDEX IDX_invfisdet_diferencias ON inv_inventario_fisico_detalle(inventario_fisico_id, cantidad_contada, cantidad_sistema);