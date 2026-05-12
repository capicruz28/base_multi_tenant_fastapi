-- ============================================================================
-- SECCIÓN 3: WMS - WAREHOUSE MANAGEMENT SYSTEM (GESTIÓN AVANZADA DE ALMACENES)
-- ============================================================================
-- DESCRIPCIÓN: Módulo avanzado para gestión detallada de almacenes
-- DEPENDENCIAS: ORG, INV
-- USADO POR: Empresas con almacenes complejos que requieren trazabilidad detallada
-- NOTA: Módulo opcional, activa funcionalidades avanzadas sobre INV
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: wms_zona_almacen
-- Descripción: Zonas dentro de un almacén (recepción, picking, despacho, etc)
-- Uso: Segmentación lógica del almacén
-- Relaciones: Hijo de inv_almacen
-- -----------------------------------------------------------------------------
CREATE TABLE wms_zona_almacen (
    zona_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    almacen_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(255) NULL,
    
    -- Tipo de zona
    tipo_zona NVARCHAR(30) NOT NULL,                          -- 'recepcion', 'almacenaje', 'picking', 'despacho', 'cuarentena', 'merma'
    
    -- Configuración
    temperatura_min DECIMAL(5,2) NULL,                        -- Para zonas refrigeradas
    temperatura_max DECIMAL(5,2) NULL,
    requiere_control_temperatura BIT DEFAULT 0,
    
    -- Capacidad
    capacidad_m3 DECIMAL(12,2) NULL,
    capacidad_kg DECIMAL(12,2) NULL,
    
    -- Estado
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_zona_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_zona_almacen FOREIGN KEY (almacen_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_zona_codigo UNIQUE (cliente_id, almacen_id, codigo)
);

CREATE INDEX IDX_zona_empresa ON wms_zona_almacen(empresa_id, es_activo);
CREATE INDEX IDX_zona_almacen ON wms_zona_almacen(almacen_id, es_activo);
CREATE INDEX IDX_zona_tipo ON wms_zona_almacen(tipo_zona);

-- -----------------------------------------------------------------------------
-- Tabla: wms_ubicacion
-- Descripción: Ubicaciones específicas dentro del almacén (rack, nivel, posición)
-- Uso: Control granular de dónde está físicamente cada producto
-- Relaciones: Detalle de zonas de almacén
-- -----------------------------------------------------------------------------
CREATE TABLE wms_ubicacion (
    ubicacion_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    almacen_id UNIQUEIDENTIFIER NOT NULL,
    zona_id UNIQUEIDENTIFIER NULL,
    
    -- Codificación jerárquica
    codigo_ubicacion NVARCHAR(30) NOT NULL,                   -- Ej: "A-01-03" (Pasillo A - Rack 01 - Nivel 03)
    pasillo NVARCHAR(10) NULL,                                -- A, B, C
    rack NVARCHAR(10) NULL,                                   -- 01, 02, 03
    nivel INT NULL,                                           -- 1, 2, 3, 4
    posicion NVARCHAR(10) NULL,                               -- A, B, C (posición en el nivel)
    
    -- Descripción
    nombre NVARCHAR(100) NULL,
    
    -- Características físicas
    tipo_ubicacion NVARCHAR(30) DEFAULT 'rack',               -- 'rack', 'piso', 'estanteria', 'caja', 'pallet'
    capacidad_kg DECIMAL(12,2) NULL,
    capacidad_m3 DECIMAL(12,4) NULL,
    capacidad_pallets INT NULL,
    alto_cm DECIMAL(10,2) NULL,
    ancho_cm DECIMAL(10,2) NULL,
    profundidad_cm DECIMAL(10,2) NULL,
    
    -- Control
    permite_multiples_productos BIT DEFAULT 1,                -- Si permite más de un producto
    permite_multiples_lotes BIT DEFAULT 1,
    es_ubicacion_picking BIT DEFAULT 0,                       -- Si es zona de picking
    
    -- Estado
    estado_ubicacion NVARCHAR(20) DEFAULT 'disponible',       -- 'disponible', 'ocupada', 'bloqueada', 'mantenimiento'
    es_activo BIT DEFAULT 1 NOT NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_ubic_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_ubic_almacen FOREIGN KEY (almacen_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION,
    CONSTRAINT FK_ubic_zona FOREIGN KEY (zona_id) 
        REFERENCES wms_zona_almacen(zona_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_ubic_codigo UNIQUE (cliente_id, almacen_id, codigo_ubicacion)
);

CREATE INDEX IDX_ubic_empresa ON wms_ubicacion(empresa_id, es_activo);
CREATE INDEX IDX_ubic_almacen ON wms_ubicacion(almacen_id, es_activo);
CREATE INDEX IDX_ubic_zona ON wms_ubicacion(zona_id) WHERE zona_id IS NOT NULL;
CREATE INDEX IDX_ubic_estado ON wms_ubicacion(estado_ubicacion);
CREATE INDEX IDX_ubic_pasillo_rack ON wms_ubicacion(almacen_id, pasillo, rack, nivel);

-- -----------------------------------------------------------------------------
-- Tabla: wms_stock_ubicacion
-- Descripción: Stock de productos por ubicación específica
-- Uso: Saber exactamente dónde está cada lote/serie en el almacén
-- Relaciones: Detalle de ubicación de stock de inv_stock
-- -----------------------------------------------------------------------------
CREATE TABLE wms_stock_ubicacion (
    stock_ubicacion_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    almacen_id UNIQUEIDENTIFIER NOT NULL,
    ubicacion_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Cantidad
    cantidad DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Lote y serie
    lote NVARCHAR(50) NULL,
    numero_serie NVARCHAR(100) NULL,
    fecha_vencimiento DATE NULL,
    
    -- Estado del stock
    estado_stock NVARCHAR(20) DEFAULT 'disponible',           -- 'disponible', 'reservado', 'bloqueado', 'cuarentena'
    motivo_bloqueo NVARCHAR(255) NULL,
    
    -- Auditoría
    fecha_ingreso DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    
    CONSTRAINT FK_stockubic_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_stockubic_almacen FOREIGN KEY (almacen_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION,
    CONSTRAINT FK_stockubic_ubicacion FOREIGN KEY (ubicacion_id) 
        REFERENCES wms_ubicacion(ubicacion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_stockubic_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_stockubic_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_stockubic_empresa ON wms_stock_ubicacion(empresa_id);
CREATE INDEX IDX_stockubic_ubicacion ON wms_stock_ubicacion(ubicacion_id);
CREATE INDEX IDX_stockubic_producto ON wms_stock_ubicacion(producto_id, almacen_id);
CREATE INDEX IDX_stockubic_lote ON wms_stock_ubicacion(lote) WHERE lote IS NOT NULL;
CREATE INDEX IDX_stockubic_disponible ON wms_stock_ubicacion(estado_stock) WHERE estado_stock = 'disponible';

-- -----------------------------------------------------------------------------
-- Tabla: wms_tarea
-- Descripción: Tareas de almacén (picking, putaway, reabastecimiento, etc)
-- Uso: Asignación y seguimiento de tareas operativas en almacén
-- Relaciones: Generadas por órdenes (ventas, producción, transferencias)
-- -----------------------------------------------------------------------------
CREATE TABLE wms_tarea (
    tarea_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    almacen_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_tarea NVARCHAR(20) NOT NULL,
    tipo_tarea NVARCHAR(30) NOT NULL,                         -- 'picking', 'putaway', 'reabastecimiento', 'conteo', 'reubicacion'
    prioridad INT DEFAULT 3,                                   -- 1=Urgente, 2=Alta, 3=Normal, 4=Baja
    
    -- Ubicaciones
    ubicacion_origen_id UNIQUEIDENTIFIER NULL,
    ubicacion_destino_id UNIQUEIDENTIFIER NULL,
    
    -- Producto
    producto_id UNIQUEIDENTIFIER NULL,
    cantidad_planeada DECIMAL(18,4) NULL,
    cantidad_completada DECIMAL(18,4) DEFAULT 0,
    unidad_medida_id UNIQUEIDENTIFIER NULL,
    
    -- Referencia
    documento_referencia_tipo NVARCHAR(30) NULL,              -- 'orden_venta', 'orden_produccion', etc
    documento_referencia_id UNIQUEIDENTIFIER NULL,
    
    -- Asignación
    asignado_usuario_id UNIQUEIDENTIFIER NULL,
    asignado_nombre NVARCHAR(150) NULL,
    fecha_asignacion DATETIME NULL,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'pendiente',                  -- 'pendiente', 'asignada', 'en_proceso', 'completada', 'cancelada'
    fecha_inicio DATETIME NULL,
    fecha_completado DATETIME NULL,
    
    -- Observaciones
    instrucciones NVARCHAR(MAX) NULL,
    observaciones NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_tarea_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_tarea_almacen FOREIGN KEY (almacen_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION,
    CONSTRAINT FK_tarea_ubic_origen FOREIGN KEY (ubicacion_origen_id) 
        REFERENCES wms_ubicacion(ubicacion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_tarea_ubic_destino FOREIGN KEY (ubicacion_destino_id) 
        REFERENCES wms_ubicacion(ubicacion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_tarea_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_tarea_numero UNIQUE (cliente_id, almacen_id, numero_tarea)
);

CREATE INDEX IDX_tarea_empresa ON wms_tarea(empresa_id, estado);
CREATE INDEX IDX_tarea_almacen ON wms_tarea(almacen_id, estado, prioridad);
CREATE INDEX IDX_tarea_asignado ON wms_tarea(asignado_usuario_id, estado) WHERE asignado_usuario_id IS NOT NULL;
CREATE INDEX IDX_tarea_estado ON wms_tarea(estado, fecha_creacion DESC);
CREATE INDEX IDX_tarea_tipo ON wms_tarea(tipo_tarea, estado);