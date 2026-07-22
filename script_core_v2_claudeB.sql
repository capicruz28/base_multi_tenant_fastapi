-- ============================================================================
-- SCRIPT: V050__core_upgrade.sql
-- DESCRIPCIÓN: Upgrade del Core ERP - Tablas modificadas y nuevas capacidades
--              transversales a todos los rubros industriales.
-- IMPORTANTE: Este script NO usa ALTER TABLE. Todas las tablas modificadas
--             se recrean completas. Los campos NUEVOS están marcados con
--             el comentario: -- [NUEVO]
-- CUBRE:
--   PARTE A: TABLAS CORE MODIFICADAS (9 tablas recreadas)
--            inv_almacen, wms_ubicacion, wms_tarea,
--            inv_movimiento_detalle, wms_stock_ubicacion,
--            qms_inspeccion, qms_no_conformidad,
--            pur_recepcion_detalle, mfg_consumo_materiales,
--            invbill_comprobante_detalle
--   PARTE B: TABLAS CORE NUEVAS (13 tablas)
--            CFG: cfg_vertical_empresa
--            INV: inv_lote, inv_producto_variante
--            MES: mes_motivo_parada, mes_ejecucion_operacion, mes_parada_maquina
--            ALR: alr_regla_alerta, alr_alerta_generada
--            WMS: wms_oleada
--            PLN: mfg_calendario_capacidad
--            APS: aps_escenario, aps_tarea_programada, aps_restriccion_recurso
--            RPT: rpt_metrica, rpt_dimension
-- ARQUITECTURA: Multi-tenant SaaS | cliente_id + empresa_id en cada tabla
-- DEPENDENCIAS: V010__tablas_bd_erp_completo.sql (debe ejecutarse primero)
-- PKs: UNIQUEIDENTIFIER (UUID) - consistente con el ERP base
-- VERSIÓN: 1.0
-- FECHA: Julio 2026
-- ============================================================================

-- ============================================================================
-- ÍNDICE
-- ============================================================================
-- PARTE A — TABLAS MODIFICADAS
--   A01  inv_almacen                    (+estrategia_salida_default)
--   A02  wms_ubicacion                  (+estrategia_salida)
--   A03  wms_tarea                      (+oleada_id FK)
--   A04  inv_movimiento_detalle         (+lote_id FK, +lote_codigo renombrado)
--   A05  wms_stock_ubicacion            (+lote_id FK, +lote_codigo renombrado)
--   A06  qms_inspeccion                 (+lote_id FK)
--   A07  qms_no_conformidad             (+lote_id FK)
--   A08  pur_recepcion_detalle          (+lote_id FK)
--   A09  mfg_consumo_materiales         (+lote_id FK)
--   A10  invbill_comprobante_detalle    (+lote_id FK)
-- PARTE B — TABLAS NUEVAS
--   B01  cfg_vertical_empresa           Control-plane de verticales por tenant
--   B02  inv_lote                       Entidad formal de lote de inventario
--   B03  inv_producto_variante          Variantes Core (color/talla/voltaje/etc)
--   B04  mes_motivo_parada              Catálogo de motivos de parada (OEE)
--   B05  mes_ejecucion_operacion        Ejecución real de operaciones en piso
--   B06  mes_parada_maquina             Registro de paradas para OEE
--   B07  alr_regla_alerta               Motor de alertas - definición de regla
--   B08  alr_alerta_generada            Motor de alertas - instancias disparadas
--   B09  wms_oleada                     Agrupador de tareas WMS
--   B10  mfg_calendario_capacidad       Capacidad disponible por CT y fecha
--   B11  aps_escenario                  APS - escenario de simulación
--   B12  aps_tarea_programada           APS - tarea programada con precedencias
--   B13  aps_restriccion_recurso        APS - restricciones de recurso
--   B14  rpt_metrica                    RPT - métrica de autoservicio
--   B15  rpt_dimension                  RPT - dimensión reutilizable
-- ============================================================================

PRINT 'Iniciando V050__core_upgrade.sql';
GO

-- ============================================================================
-- PARTE A: TABLAS CORE MODIFICADAS
-- ============================================================================
-- CONVENCIÓN: Los campos NUEVOS están marcados con -- [NUEVO] al final de
--             la línea. Todo lo demás es idéntico a la versión original.
-- ============================================================================

-- ============================================================================
-- A01: inv_almacen
-- CAMBIO: +estrategia_salida_default — estrategia de salida de stock por
--         defecto para este almacén. Se hereda en wms_ubicacion cuando
--         la ubicación no tiene estrategia propia.
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: inv_almacen
-- Descripción: Almacenes físicos de la empresa
-- Uso: Definición de almacenes para control de inventario
-- Relaciones: Padre de inv_stock, wms_ubicacion, inv_movimiento
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

    -- Estrategia de salida de stock (NUEVO)
    estrategia_salida_default NVARCHAR(10) DEFAULT 'FEFO',    -- [NUEVO] 'FEFO', 'FIFO', 'LEFO', 'MANUAL'
                                                              -- [NUEVO] FEFO=primero en vencer, FIFO=primero en entrar,
                                                              -- [NUEVO] LEFO=último en entrar, MANUAL=el operario decide
                                                              -- [NUEVO] Se hereda en wms_ubicacion si no tiene estrategia propia

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

PRINT 'A01 inv_almacen OK';
GO

-- ============================================================================
-- A02: wms_ubicacion
-- CAMBIO: +estrategia_salida — estrategia propia de esta ubicación.
--         Si NULL hereda la del almacén. Permite granularidad por ubicación
--         (ej: zona de congelados usa FEFO, zona seca usa FIFO).
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: wms_ubicacion
-- Descripción: Ubicaciones físicas dentro de un almacén (rack, pasillo, nivel)
-- Uso: Control de posición exacta de productos en almacén
-- Relaciones: Hijo de inv_almacen y wms_zona_almacen, padre de wms_stock_ubicacion
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

    -- Estrategia de salida (NUEVO)
    estrategia_salida NVARCHAR(10) NULL,                      -- [NUEVO] 'FEFO', 'FIFO', 'LEFO', 'MANUAL'
                                                              -- [NUEVO] NULL = hereda estrategia_salida_default del almacén
                                                              -- [NUEVO] Permite granularidad: zona fría FEFO, zona seca FIFO

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
CREATE INDEX IDX_ubic_almacen ON wms_ubicacion(almacen_id, estado_ubicacion);
CREATE INDEX IDX_ubic_picking ON wms_ubicacion(almacen_id) WHERE es_ubicacion_picking = 1;
CREATE INDEX IDX_ubic_estrategia ON wms_ubicacion(almacen_id, estrategia_salida) WHERE estrategia_salida IS NOT NULL;

PRINT 'A02 wms_ubicacion OK';
GO

-- ============================================================================
-- A03: wms_tarea
-- CAMBIO: +oleada_id — permite agrupar tareas en oleadas de picking.
--         NULL = tarea suelta (compatible hacia atrás).
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: wms_tarea
-- Descripción: Tareas de almacén (picking, putaway, reabastecimiento, etc)
-- Uso: Asignación y seguimiento de tareas operativas en almacén
-- Relaciones: Generadas por órdenes (ventas, producción, transferencias)
--             Agrupadas opcionalmente en wms_oleada
-- -----------------------------------------------------------------------------
CREATE TABLE wms_tarea (
    tarea_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    almacen_id UNIQUEIDENTIFIER NOT NULL,

    numero_tarea NVARCHAR(20) NOT NULL,
    tipo_tarea NVARCHAR(30) NOT NULL,                         -- 'picking', 'putaway', 'reabastecimiento', 'conteo', 'reubicacion'
    prioridad INT DEFAULT 3,                                   -- 1=Urgente, 2=Alta, 3=Normal, 4=Baja

    -- Agrupación en oleada (NUEVO)
    oleada_id UNIQUEIDENTIFIER NULL,                          -- [NUEVO] FK a wms_oleada — NULL = tarea suelta

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
    -- FK a wms_oleada se agrega después de crear esa tabla (PARTE B09)
    CONSTRAINT UQ_tarea_numero UNIQUE (cliente_id, almacen_id, numero_tarea)
);

CREATE INDEX IDX_tarea_empresa ON wms_tarea(empresa_id, estado);
CREATE INDEX IDX_tarea_almacen ON wms_tarea(almacen_id, estado, prioridad);
CREATE INDEX IDX_tarea_asignado ON wms_tarea(asignado_usuario_id, estado) WHERE asignado_usuario_id IS NOT NULL;
CREATE INDEX IDX_tarea_estado ON wms_tarea(estado, fecha_creacion DESC);
CREATE INDEX IDX_tarea_tipo ON wms_tarea(tipo_tarea, estado);
CREATE INDEX IDX_tarea_oleada ON wms_tarea(oleada_id) WHERE oleada_id IS NOT NULL;     -- [NUEVO]

PRINT 'A03 wms_tarea OK';
GO

-- ============================================================================
-- A04: inv_movimiento_detalle
-- CAMBIO: +lote_id FK a inv_lote (entidad formal de lote).
--         El campo lote NVARCHAR(50) original se mantiene como lote_codigo
--         para compatibilidad y búsqueda rápida por texto.
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: inv_movimiento_detalle
-- Descripción: Detalle de cada movimiento de inventario (líneas de producto)
-- Uso: Registro de qué producto, cuánto y a qué costo se movió
-- Relaciones: Hijo de inv_movimiento; referencia inv_lote para trazabilidad
-- -----------------------------------------------------------------------------
CREATE TABLE inv_movimiento_detalle (
    movimiento_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    movimiento_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,

    -- Cantidad y unidad
    cantidad DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    cantidad_base DECIMAL(18,4) NOT NULL,                     -- Cantidad convertida a unidad base

    -- Costos
    costo_unitario DECIMAL(18,4) DEFAULT 0,                   -- Costo por unidad
    costo_total AS (cantidad * costo_unitario) PERSISTED,
    moneda_id UNIQUEIDENTIFIER NOT NULL,

    -- Lote y vencimiento (si aplica)
    lote_id UNIQUEIDENTIFIER NULL,                            -- [NUEVO] FK a inv_lote (entidad formal)
    lote_codigo NVARCHAR(50) NULL,                            -- Código de lote en texto (compatibilidad y búsqueda rápida)
                                                              -- Se mantiene sincronizado con inv_lote.codigo_lote
    fecha_vencimiento DATE NULL,                              -- Se puede heredar de inv_lote o sobreescribir
    numero_serie NVARCHAR(100) NULL,

    -- Ubicación (WMS)
    ubicacion_almacen NVARCHAR(50) NULL,

    -- Observaciones
    observaciones NVARCHAR(500) NULL,

    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,

    CONSTRAINT FK_movdet_empresa FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_movdet_movimiento FOREIGN KEY (movimiento_id)
        REFERENCES inv_movimiento(movimiento_id) ON DELETE NO ACTION,
    CONSTRAINT FK_movdet_producto FOREIGN KEY (producto_id)
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_movdet_um FOREIGN KEY (unidad_medida_id)
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT FK_movdet_moneda FOREIGN KEY (moneda_id)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION
    -- FK a inv_lote se agrega después de crear esa tabla (PARTE B02)
);

CREATE INDEX IDX_movdet_empresa ON inv_movimiento_detalle(empresa_id);
CREATE INDEX IDX_movdet_movimiento ON inv_movimiento_detalle(movimiento_id);
CREATE INDEX IDX_movdet_producto ON inv_movimiento_detalle(producto_id);
CREATE INDEX IDX_movdet_lote_codigo ON inv_movimiento_detalle(lote_codigo) WHERE lote_codigo IS NOT NULL;
CREATE INDEX IDX_movdet_lote_id ON inv_movimiento_detalle(lote_id) WHERE lote_id IS NOT NULL;   -- [NUEVO]

PRINT 'A04 inv_movimiento_detalle OK';
GO

-- ============================================================================
-- A05: wms_stock_ubicacion
-- CAMBIO: +lote_id FK a inv_lote. Se mantiene lote_codigo por compatibilidad.
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: wms_stock_ubicacion
-- Descripción: Stock exacto por ubicación física dentro del almacén
-- Uso: Saber exactamente dónde está cada lote/serie en el almacén
-- Relaciones: Cruce de wms_ubicacion × inv_producto × inv_lote
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
    lote_id UNIQUEIDENTIFIER NULL,                            -- [NUEVO] FK a inv_lote (entidad formal)
    lote_codigo NVARCHAR(50) NULL,                            -- Código lote texto (compatibilidad)
    numero_serie NVARCHAR(100) NULL,
    fecha_vencimiento DATE NULL,                              -- Heredada de inv_lote o sobreescrita

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
    -- FK a inv_lote se agrega después de crear esa tabla (PARTE B02)
);

CREATE INDEX IDX_stockubic_empresa ON wms_stock_ubicacion(empresa_id);
CREATE INDEX IDX_stockubic_ubicacion ON wms_stock_ubicacion(ubicacion_id);
CREATE INDEX IDX_stockubic_producto ON wms_stock_ubicacion(producto_id, almacen_id);
CREATE INDEX IDX_stockubic_lote_codigo ON wms_stock_ubicacion(lote_codigo) WHERE lote_codigo IS NOT NULL;
CREATE INDEX IDX_stockubic_lote_id ON wms_stock_ubicacion(lote_id) WHERE lote_id IS NOT NULL;  -- [NUEVO]
CREATE INDEX IDX_stockubic_disponible ON wms_stock_ubicacion(estado_stock) WHERE estado_stock = 'disponible';

PRINT 'A05 wms_stock_ubicacion OK';
GO

-- ============================================================================
-- A06: qms_inspeccion
-- CAMBIO: +lote_id FK a inv_lote.
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: qms_inspeccion
-- Descripción: Inspecciones de calidad de productos (entrada, proceso, salida)
-- Uso: Registro de inspecciones y resultados de calidad
-- Relaciones: Referencia plan_inspeccion, producto, lote e inv_lote
-- -----------------------------------------------------------------------------
CREATE TABLE qms_inspeccion (
    inspeccion_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,

    numero_inspeccion NVARCHAR(20) NOT NULL,
    fecha_inspeccion DATETIME DEFAULT GETDATE() NOT NULL,
    plan_inspeccion_id UNIQUEIDENTIFIER NOT NULL,

    -- Producto inspeccionado
    producto_id UNIQUEIDENTIFIER NOT NULL,
    lote_id UNIQUEIDENTIFIER NULL,                            -- [NUEVO] FK a inv_lote (entidad formal)
    lote NVARCHAR(50) NULL,                                   -- Código lote texto (compatibilidad)

    -- Referencia documento
    tipo_documento_origen NVARCHAR(30) NULL,                  -- 'orden_compra', 'orden_produccion', 'movimiento_inventario'
    documento_origen_id UNIQUEIDENTIFIER NULL,

    -- Almacén/ubicación
    almacen_id UNIQUEIDENTIFIER NULL,
    ubicacion_almacen NVARCHAR(50) NULL,

    -- Cantidad inspeccionada
    cantidad_total DECIMAL(18,4) NOT NULL,
    cantidad_inspeccionada DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,

    -- Resultados
    cantidad_aprobada DECIMAL(18,4) DEFAULT 0,
    cantidad_rechazada DECIMAL(18,4) DEFAULT 0,
    cantidad_observada DECIMAL(18,4) DEFAULT 0,               -- Con observaciones menores

    defectos_criticos INT DEFAULT 0,
    defectos_mayores INT DEFAULT 0,
    defectos_menores INT DEFAULT 0,

    -- Resultado final
    resultado NVARCHAR(20) DEFAULT 'pendiente',               -- 'aprobado', 'rechazado', 'aprobado_condicional', 'pendiente'

    -- Inspector
    inspector_usuario_id UNIQUEIDENTIFIER NULL,
    inspector_nombre NVARCHAR(150) NULL,

    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    acciones_correctivas NVARCHAR(MAX) NULL,

    -- Aprobación
    aprobado_por_usuario_id UNIQUEIDENTIFIER NULL,
    fecha_aprobacion DATETIME NULL,

    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,

    CONSTRAINT FK_qms_insp_empresa FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_qms_insp_plan FOREIGN KEY (plan_inspeccion_id)
        REFERENCES qms_plan_inspeccion(plan_inspeccion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_qms_insp_producto FOREIGN KEY (producto_id)
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_qms_insp_almacen FOREIGN KEY (almacen_id)
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_qms_insp_numero UNIQUE (cliente_id, empresa_id, numero_inspeccion)
    -- FK a inv_lote se agrega después de crear esa tabla (PARTE B02)
);

CREATE INDEX IDX_qms_insp_empresa ON qms_inspeccion(empresa_id, fecha_inspeccion DESC);
CREATE INDEX IDX_qms_insp_producto ON qms_inspeccion(producto_id);
CREATE INDEX IDX_qms_insp_resultado ON qms_inspeccion(resultado, fecha_inspeccion DESC);
CREATE INDEX IDX_qms_insp_lote ON qms_inspeccion(lote) WHERE lote IS NOT NULL;
CREATE INDEX IDX_qms_insp_lote_id ON qms_inspeccion(lote_id) WHERE lote_id IS NOT NULL;        -- [NUEVO]

PRINT 'A06 qms_inspeccion OK';
GO

-- ============================================================================
-- A07: qms_no_conformidad
-- CAMBIO: +lote_id FK a inv_lote.
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: qms_no_conformidad
-- Descripción: Registro de no conformidades con flujo CAPA completo
-- Uso: Gestión de no conformidades ISO 9001 (8D / CAPA)
-- Relaciones: Puede originarse de qms_inspeccion; referencia producto e inv_lote
-- -----------------------------------------------------------------------------
CREATE TABLE qms_no_conformidad (
    no_conformidad_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,

    numero_nc NVARCHAR(20) NOT NULL,
    fecha_deteccion DATETIME DEFAULT GETDATE() NOT NULL,

    -- Origen
    origen NVARCHAR(30) NOT NULL,                             -- 'inspeccion', 'reclamo_cliente', 'auditoria', 'proceso'
    inspeccion_id UNIQUEIDENTIFIER NULL,                      -- Si se origina de inspección
    documento_referencia NVARCHAR(50) NULL,

    -- Producto afectado
    producto_id UNIQUEIDENTIFIER NULL,
    lote_id UNIQUEIDENTIFIER NULL,                            -- [NUEVO] FK a inv_lote (entidad formal)
    lote NVARCHAR(50) NULL,                                   -- Código lote texto (compatibilidad)
    cantidad_afectada DECIMAL(18,4) NULL,

    -- Descripción
    descripcion_nc NVARCHAR(MAX) NOT NULL,                    -- Descripción de la no conformidad
    tipo_nc NVARCHAR(30) NOT NULL,                            -- 'critica', 'mayor', 'menor'

    -- Responsables
    area_responsable NVARCHAR(100) NULL,
    responsable_usuario_id UNIQUEIDENTIFIER NULL,

    -- Análisis de causa raíz
    analisis_causa_raiz NVARCHAR(MAX) NULL,                   -- 5 Porqués, Ishikawa, etc
    causa_raiz_identificada NVARCHAR(500) NULL,

    -- Acciones
    accion_inmediata NVARCHAR(MAX) NULL,                      -- Acción de contención
    accion_correctiva NVARCHAR(MAX) NULL,                     -- Acción correctiva
    accion_preventiva NVARCHAR(MAX) NULL,                     -- Acción preventiva

    responsable_accion_usuario_id UNIQUEIDENTIFIER NULL,
    fecha_compromiso_cierre DATE NULL,

    -- Estado y cierre
    estado NVARCHAR(20) DEFAULT 'abierta',                    -- 'abierta', 'en_analisis', 'en_accion', 'cerrada', 'cancelada'
    fecha_cierre DATETIME NULL,
    cerrado_por_usuario_id UNIQUEIDENTIFIER NULL,
    verificacion_eficacia NVARCHAR(MAX) NULL,                 -- Verificación de que la acción funcionó

    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,

    CONSTRAINT FK_qms_nc_empresa FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_qms_nc_insp FOREIGN KEY (inspeccion_id)
        REFERENCES qms_inspeccion(inspeccion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_qms_nc_producto FOREIGN KEY (producto_id)
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_qms_nc_numero UNIQUE (cliente_id, empresa_id, numero_nc)
    -- FK a inv_lote se agrega después de crear esa tabla (PARTE B02)
);

CREATE INDEX IDX_qms_nc_empresa ON qms_no_conformidad(empresa_id, fecha_deteccion DESC);
CREATE INDEX IDX_qms_nc_estado ON qms_no_conformidad(estado, fecha_deteccion DESC);
CREATE INDEX IDX_qms_nc_tipo ON qms_no_conformidad(tipo_nc);
CREATE INDEX IDX_qms_nc_producto ON qms_no_conformidad(producto_id) WHERE producto_id IS NOT NULL;
CREATE INDEX IDX_qms_nc_lote_id ON qms_no_conformidad(lote_id) WHERE lote_id IS NOT NULL;      -- [NUEVO]

PRINT 'A07 qms_no_conformidad OK';
GO

-- ============================================================================
-- A08: pur_recepcion_detalle
-- CAMBIO: +lote_id FK a inv_lote. Es aquí donde se CREA el lote al recibir
--         mercadería del proveedor.
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: pur_recepcion_detalle
-- Descripción: Detalle de recepción de compras por producto y lote
-- Uso: Registro de qué se recibió, cuánto y de qué lote — punto de creación del lote
-- Relaciones: Hijo de pur_recepcion; genera inv_lote al confirmar la recepción
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
    lote_id UNIQUEIDENTIFIER NULL,                            -- [NUEVO] FK a inv_lote — se asigna al confirmar recepción
    lote NVARCHAR(50) NULL,                                   -- Código lote texto del proveedor (compatibilidad)
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
    -- FK a inv_lote se agrega después de crear esa tabla (PARTE B02)
);

CREATE INDEX IDX_recepdet_empresa ON pur_recepcion_detalle(empresa_id);
CREATE INDEX IDX_recepdet_recepcion ON pur_recepcion_detalle(recepcion_id);
CREATE INDEX IDX_recepdet_ocdet ON pur_recepcion_detalle(orden_compra_detalle_id);
CREATE INDEX IDX_recepdet_producto ON pur_recepcion_detalle(producto_id);
CREATE INDEX IDX_recepdet_lote_id ON pur_recepcion_detalle(lote_id) WHERE lote_id IS NOT NULL; -- [NUEVO]

PRINT 'A08 pur_recepcion_detalle OK';
GO

-- ============================================================================
-- A09: mfg_consumo_materiales
-- CAMBIO: +lote_id FK a inv_lote. Trazabilidad de qué lote de material
--         se consumió en cada orden de producción.
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: mfg_consumo_materiales
-- Descripción: Consumo real de materiales en órdenes de producción
-- Uso: Trazabilidad material → producto terminado; costeo real de OP
-- Relaciones: Hijo de mfg_orden_produccion; consume inv_lote
-- -----------------------------------------------------------------------------
CREATE TABLE mfg_consumo_materiales (
    consumo_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    orden_produccion_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,                    -- Material consumido

    -- Cantidad
    cantidad_planificada DECIMAL(18,4) NOT NULL,              -- Según BOM
    cantidad_consumida DECIMAL(18,4) NOT NULL,                -- Real consumido
    diferencia AS (cantidad_consumida - cantidad_planificada) PERSISTED,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,

    -- Lote y trazabilidad
    lote_id UNIQUEIDENTIFIER NULL,                            -- [NUEVO] FK a inv_lote (entidad formal)
    lote NVARCHAR(50) NULL,                                   -- Código lote texto (compatibilidad)
    almacen_origen_id UNIQUEIDENTIFIER NULL,

    -- Costo
    costo_unitario DECIMAL(18,4) DEFAULT 0,
    costo_total AS (cantidad_consumida * costo_unitario) PERSISTED,

    -- Movimiento de inventario asociado
    movimiento_inventario_id UNIQUEIDENTIFIER NULL,

    -- Observaciones
    observaciones NVARCHAR(500) NULL,

    -- Auditoría
    fecha_consumo DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_registro_id UNIQUEIDENTIFIER NULL,

    CONSTRAINT FK_consumo_empresa FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_consumo_op FOREIGN KEY (orden_produccion_id)
        REFERENCES mfg_orden_produccion(orden_produccion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_consumo_producto FOREIGN KEY (producto_id)
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_consumo_almacen FOREIGN KEY (almacen_origen_id)
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION,
    CONSTRAINT FK_consumo_um FOREIGN KEY (unidad_medida_id)
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
    -- FK a inv_lote se agrega después de crear esa tabla (PARTE B02)
);

CREATE INDEX IDX_consumo_empresa ON mfg_consumo_materiales(empresa_id);
CREATE INDEX IDX_consumo_op ON mfg_consumo_materiales(orden_produccion_id);
CREATE INDEX IDX_consumo_producto ON mfg_consumo_materiales(producto_id, fecha_consumo DESC);
CREATE INDEX IDX_consumo_lote_id ON mfg_consumo_materiales(lote_id) WHERE lote_id IS NOT NULL; -- [NUEVO]

PRINT 'A09 mfg_consumo_materiales OK';
GO

-- ============================================================================
-- A10: invbill_comprobante_detalle
-- CAMBIO: +lote_id FK a inv_lote. Permite rastrear qué lote se vendió
--         en cada línea de comprobante (crítico para alimentos y farma).
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: invbill_comprobante_detalle
-- Descripción: Detalle de líneas de comprobante electrónico (factura, boleta, NC)
-- Uso: Registro fiscal de productos vendidos con trazabilidad de lote
-- Relaciones: Hijo de invbill_comprobante; referencia inv_producto e inv_lote
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

    -- Lote (trazabilidad en venta)
    lote_id UNIQUEIDENTIFIER NULL,                            -- [NUEVO] FK a inv_lote (entidad formal)
    lote NVARCHAR(50) NULL,                                   -- Código lote texto (compatibilidad)

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
    -- FK a inv_lote se agrega después de crear esa tabla (PARTE B02)
);

CREATE INDEX IDX_compdet_empresa ON invbill_comprobante_detalle(empresa_id);
CREATE INDEX IDX_compdet_comprobante ON invbill_comprobante_detalle(comprobante_id, item);
CREATE INDEX IDX_compdet_producto ON invbill_comprobante_detalle(producto_id) WHERE producto_id IS NOT NULL;
CREATE INDEX IDX_compdet_lote_id ON invbill_comprobante_detalle(lote_id) WHERE lote_id IS NOT NULL; -- [NUEVO]

PRINT 'A10 invbill_comprobante_detalle OK';
GO

PRINT 'PARTE A completada: 10 tablas modificadas';
GO

-- ============================================================================
-- PARTE B: TABLAS CORE NUEVAS
-- ============================================================================

-- ============================================================================
-- B01: cfg_vertical_empresa
-- DESCRIPCIÓN: Control-plane de verticales activas por empresa/tenant.
--              Define qué módulos verticales (TXT, FOD, MET, DIS, SRV)
--              tiene habilitados cada empresa. Sin esto no hay forma de
--              saber qué pantallas/reglas mostrar a cada cliente.
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: cfg_vertical_empresa
-- Descripción: Verticales de industria activas por empresa (control-plane)
-- Uso: Determinar qué módulos verticales están disponibles para cada tenant
-- Relaciones: Hijo de org_empresa; referenciado por todos los módulos verticales
-- -----------------------------------------------------------------------------
CREATE TABLE cfg_vertical_empresa (
    vertical_empresa_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,

    -- Vertical habilitada
    codigo_vertical NVARCHAR(10) NOT NULL,                    -- 'TXT', 'FOD', 'MET', 'DIS', 'SRV', 'FAR', 'AGR'
    nombre_vertical NVARCHAR(100) NOT NULL,                   -- 'Textil', 'Alimentos', 'Metalmecánica', etc.

    -- Sub-módulos activos dentro de la vertical (JSON)
    -- Ej: {"hilanderia":true,"tejeduria":true,"tintoreria":true,"confeccion":false}
    modulos_activos NVARCHAR(MAX) NULL,

    -- Configuración específica de la vertical (JSON)
    -- Cada vertical define sus propios parámetros aquí
    -- Ej TXT: {"unidad_tela":"metros","sistema_inspeccion":"4puntos","galgas_activas":[18,24,28]}
    configuracion_json NVARCHAR(MAX) NULL,

    -- Licencia y plan
    plan_vertical NVARCHAR(30) NULL,                          -- 'basico', 'profesional', 'enterprise'
    fecha_activacion DATE NOT NULL DEFAULT GETDATE(),
    fecha_vencimiento DATE NULL,                              -- NULL = sin vencimiento

    -- Estado
    es_activo BIT DEFAULT 1 NOT NULL,

    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    observaciones NVARCHAR(500) NULL,

    CONSTRAINT FK_cfgvert_empresa FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_cfgvert_empresa_vertical UNIQUE (cliente_id, empresa_id, codigo_vertical)
);

CREATE INDEX IDX_cfgvert_empresa ON cfg_vertical_empresa(empresa_id, es_activo);
CREATE INDEX IDX_cfgvert_vertical ON cfg_vertical_empresa(codigo_vertical, es_activo);

PRINT 'B01 cfg_vertical_empresa OK';
GO

-- ============================================================================
-- B02: inv_lote
-- DESCRIPCIÓN: Entidad formal de lote. Reemplaza al campo lote NVARCHAR(50)
--              que hoy existe suelto en 7 tablas. Centraliza: quién fabricó
--              el lote, cuándo, cuánto queda, estado y vencimiento.
--              Es transversal: alimentos, farma, textil, química, todos lo usan.
-- NOTA: Después de crear esta tabla se agregan las FKs pendientes en las
--       tablas de PARTE A mediante ALTER TABLE.
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: inv_lote
-- Descripción: Entidad formal de lote de inventario. Centraliza trazabilidad,
--              vencimiento y estado de cada lote desde su ingreso hasta agotamiento.
-- Uso: Trazabilidad completa compra/producción → consumo/venta por lote
-- Relaciones: Referenciado por inv_movimiento_detalle, wms_stock_ubicacion,
--             qms_inspeccion, qms_no_conformidad, pur_recepcion_detalle,
--             mfg_consumo_materiales, invbill_comprobante_detalle
-- -----------------------------------------------------------------------------
CREATE TABLE inv_lote (
    lote_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,

    -- Identificación
    codigo_lote NVARCHAR(50) NOT NULL,                        -- Código del lote (puede ser del proveedor o interno)
    codigo_lote_interno NVARCHAR(50) NULL,                    -- Código interno si difiere del del proveedor
    codigo_lote_proveedor NVARCHAR(50) NULL,                  -- Código original del proveedor

    -- Producto al que pertenece
    producto_id UNIQUEIDENTIFIER NOT NULL,                    -- FK a inv_producto

    -- Origen del lote
    tipo_origen NVARCHAR(20) NOT NULL,                        -- 'compra', 'produccion_propia', 'devolucion', 'apertura'
    proveedor_id UNIQUEIDENTIFIER NULL,                       -- FK a pur_proveedor (si origen = 'compra')
    orden_produccion_id UNIQUEIDENTIFIER NULL,                -- FK a mfg_orden_produccion (si origen = 'produccion_propia')
    documento_origen_tipo NVARCHAR(30) NULL,                  -- 'orden_compra', 'orden_produccion', 'ajuste'
    documento_origen_id UNIQUEIDENTIFIER NULL,
    documento_origen_numero NVARCHAR(30) NULL,

    -- Fechas críticas
    fecha_fabricacion DATE NULL,                              -- Fecha de fabricación (del proveedor o propia)
    fecha_vencimiento DATE NULL,                              -- Fecha de vencimiento (NULL = no vence)
    fecha_ingreso DATE NOT NULL DEFAULT GETDATE(),            -- Fecha de ingreso al sistema
    fecha_vencimiento_cuarentena DATE NULL,                   -- Hasta cuándo está en cuarentena

    -- Cantidades
    cantidad_inicial DECIMAL(18,4) NOT NULL,                  -- Cantidad con la que ingresó el lote
    cantidad_disponible DECIMAL(18,4) NOT NULL,               -- Cantidad actual disponible (se actualiza con movimientos)
    cantidad_reservada DECIMAL(18,4) DEFAULT 0,               -- Reservada para pedidos/OP
    cantidad_bloqueada DECIMAL(18,4) DEFAULT 0,               -- Bloqueada por calidad u otro motivo
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,               -- FK a inv_unidad_medida

    -- Estado
    estado NVARCHAR(20) DEFAULT 'disponible',                 -- 'disponible', 'cuarentena', 'bloqueado',
                                                              -- 'vencido', 'agotado', 'rechazado'
    motivo_bloqueo NVARCHAR(255) NULL,                        -- Razón si estado = 'bloqueado' o 'cuarentena'

    -- Control de calidad
    resultado_qc NVARCHAR(20) NULL,                           -- 'aprobado', 'condicional', 'rechazado', 'pendiente'
    inspeccion_id UNIQUEIDENTIFIER NULL,                      -- FK a qms_inspeccion (resultado del QC de ingreso)

    -- Almacén de ingreso (referencial; la ubicación exacta está en wms_stock_ubicacion)
    almacen_id UNIQUEIDENTIFIER NULL,                         -- FK a inv_almacen

    -- Atributos adicionales (JSON flexible para características por industria)
    -- Alimentos: {"temperatura_almacenamiento":"2-8°C","condicion":"refrigerado"}
    -- Textil:    {"color":"AZ001","partida_tintura":"TIN-2026-0312"}
    -- Química:   {"ficha_seguridad":"FDS-001","clase_peligro":"8"}
    atributos_lote NVARCHAR(MAX) NULL,

    -- Costo del lote
    costo_unitario DECIMAL(18,4) NULL,                        -- Costo unitario de este lote específico

    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    observaciones NVARCHAR(500) NULL,

    CONSTRAINT FK_lote_empresa FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_lote_producto FOREIGN KEY (producto_id)
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_lote_proveedor FOREIGN KEY (proveedor_id)
        REFERENCES pur_proveedor(proveedor_id) ON DELETE NO ACTION,
    CONSTRAINT FK_lote_op FOREIGN KEY (orden_produccion_id)
        REFERENCES mfg_orden_produccion(orden_produccion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_lote_almacen FOREIGN KEY (almacen_id)
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION,
    CONSTRAINT FK_lote_um FOREIGN KEY (unidad_medida_id)
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_lote_codigo UNIQUE (cliente_id, empresa_id, producto_id, codigo_lote)
);

CREATE INDEX IDX_lote_empresa ON inv_lote(empresa_id, estado);
CREATE INDEX IDX_lote_producto ON inv_lote(producto_id, estado);
CREATE INDEX IDX_lote_vencimiento ON inv_lote(fecha_vencimiento, estado) WHERE fecha_vencimiento IS NOT NULL;
CREATE INDEX IDX_lote_codigo ON inv_lote(codigo_lote, empresa_id);
CREATE INDEX IDX_lote_proveedor ON inv_lote(proveedor_id) WHERE proveedor_id IS NOT NULL;
CREATE INDEX IDX_lote_almacen ON inv_lote(almacen_id) WHERE almacen_id IS NOT NULL;
CREATE INDEX IDX_lote_disponible ON inv_lote(producto_id, fecha_vencimiento, cantidad_disponible)
    WHERE estado = 'disponible';                              -- Índice para estrategia FEFO

PRINT 'B02 inv_lote OK';
GO

-- Agregar FKs a inv_lote en tablas de PARTE A (ahora que inv_lote existe)
ALTER TABLE inv_movimiento_detalle
    ADD CONSTRAINT FK_movdet_lote FOREIGN KEY (lote_id)
        REFERENCES inv_lote(lote_id) ON DELETE NO ACTION;

ALTER TABLE wms_stock_ubicacion
    ADD CONSTRAINT FK_stockubic_lote FOREIGN KEY (lote_id)
        REFERENCES inv_lote(lote_id) ON DELETE NO ACTION;

ALTER TABLE qms_inspeccion
    ADD CONSTRAINT FK_qms_insp_lote FOREIGN KEY (lote_id)
        REFERENCES inv_lote(lote_id) ON DELETE NO ACTION;

ALTER TABLE qms_no_conformidad
    ADD CONSTRAINT FK_qms_nc_lote FOREIGN KEY (lote_id)
        REFERENCES inv_lote(lote_id) ON DELETE NO ACTION;

ALTER TABLE pur_recepcion_detalle
    ADD CONSTRAINT FK_recepdet_lote FOREIGN KEY (lote_id)
        REFERENCES inv_lote(lote_id) ON DELETE NO ACTION;

ALTER TABLE mfg_consumo_materiales
    ADD CONSTRAINT FK_consumo_lote FOREIGN KEY (lote_id)
        REFERENCES inv_lote(lote_id) ON DELETE NO ACTION;

ALTER TABLE invbill_comprobante_detalle
    ADD CONSTRAINT FK_compdet_lote FOREIGN KEY (lote_id)
        REFERENCES inv_lote(lote_id) ON DELETE NO ACTION;

PRINT 'B02 FKs a inv_lote agregadas en 7 tablas OK';
GO

-- ============================================================================
-- B03: inv_producto_variante
-- DESCRIPCIÓN: Variantes de producto (Core, no vertical).
--              Una variante es una combinación de atributos de un producto padre.
--              Textil: color + talla. Electrónica: voltaje + color. Calzado: número + color.
--              El producto padre vive en inv_producto. Cada variante tiene su propio
--              SKU, código de barras y puede tener precio diferenciado.
--              La vertical TXT extenderá esta tabla para agregar tono Pantone, etc.
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: inv_producto_variante
-- Descripción: Variantes Core de un producto padre (SKU por combinación de atributos)
-- Uso: Gestión de variantes multiindustria — es la unidad mínima vendible/producible
--      cuando el producto tiene combinaciones (color/talla, voltaje/color, etc.)
-- Relaciones: Hijo de inv_producto (producto padre); referenciado por pedidos y stock
-- -----------------------------------------------------------------------------
CREATE TABLE inv_producto_variante (
    variante_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,

    -- Producto padre
    producto_id UNIQUEIDENTIFIER NOT NULL,                    -- FK a inv_producto (el modelo base)

    -- Identificación de la variante
    sku_variante NVARCHAR(80) NOT NULL,                       -- SKU único de esta variante
    codigo_barra_variante NVARCHAR(50) NULL,                  -- EAN-13 o código propio
    codigo_interno_variante NVARCHAR(30) NULL,

    -- Atributos de la variante (genéricos — la vertical los interpreta)
    -- Textil:       atributo_1 = color_id (txt_cat_color), atributo_2 = talla_id (txt_cat_talla)
    -- Electrónica:  atributo_1 = voltaje,  atributo_2 = color
    -- Calzado:      atributo_1 = numero,   atributo_2 = color
    atributo_1_nombre NVARCHAR(30) NULL,                      -- Ej: 'color', 'voltaje', 'numero'
    atributo_1_valor NVARCHAR(100) NULL,                      -- Ej: 'Azul marino', '220V', '42'
    atributo_1_referencia_id UNIQUEIDENTIFIER NULL,           -- ID en tabla catálogo de la vertical (opcional)

    atributo_2_nombre NVARCHAR(30) NULL,                      -- Ej: 'talla', 'color', 'acabado'
    atributo_2_valor NVARCHAR(100) NULL,
    atributo_2_referencia_id UNIQUEIDENTIFIER NULL,

    atributo_3_nombre NVARCHAR(30) NULL,                      -- Tercer atributo si aplica
    atributo_3_valor NVARCHAR(100) NULL,
    atributo_3_referencia_id UNIQUEIDENTIFIER NULL,

    -- Atributos adicionales no estándar (JSON)
    atributos_extra NVARCHAR(MAX) NULL,                       -- JSON para atributos específicos de la vertical

    -- Precio diferenciado (NULL = usa precio del producto padre)
    precio_venta_variante DECIMAL(18,4) NULL,
    costo_variante DECIMAL(18,4) NULL,

    -- Imagen específica de esta variante
    imagen_url NVARCHAR(500) NULL,

    -- Orden de presentación
    orden_presentacion INT DEFAULT 0,
    es_variante_principal BIT DEFAULT 0,                      -- Si es la combinación por defecto del modelo

    -- Estado
    es_activo BIT DEFAULT 1 NOT NULL,

    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,

    CONSTRAINT FK_var_empresa FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_var_producto FOREIGN KEY (producto_id)
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_var_sku UNIQUE (cliente_id, empresa_id, sku_variante)
);

CREATE INDEX IDX_var_producto ON inv_producto_variante(producto_id, es_activo);
CREATE INDEX IDX_var_sku ON inv_producto_variante(sku_variante);
CREATE INDEX IDX_var_barra ON inv_producto_variante(codigo_barra_variante) WHERE codigo_barra_variante IS NOT NULL;
CREATE INDEX IDX_var_attr1 ON inv_producto_variante(producto_id, atributo_1_valor) WHERE atributo_1_valor IS NOT NULL;
CREATE INDEX IDX_var_attr2 ON inv_producto_variante(producto_id, atributo_2_valor) WHERE atributo_2_valor IS NOT NULL;

PRINT 'B03 inv_producto_variante OK';
GO

-- ============================================================================
-- B04: mes_motivo_parada
-- DESCRIPCIÓN: Catálogo de motivos de parada para OEE.
--              Las paradas se clasifican por categoría OEE:
--              - Disponibilidad: máquina no disponible (avería, setup)
--              - Rendimiento:    máquina lenta (ajustes menores, microstops)
--              - Calidad:        paradas por defectos de calidad
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: mes_motivo_parada
-- Descripción: Catálogo de motivos de parada de máquina para análisis OEE
-- Uso: Clasificar paradas en mes_parada_maquina para calcular disponibilidad,
--      rendimiento y calidad (OEE = D × R × C)
-- Relaciones: Referenciado por mes_parada_maquina
-- -----------------------------------------------------------------------------
CREATE TABLE mes_motivo_parada (
    motivo_parada_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,

    -- Identificación
    codigo NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(500) NULL,

    -- Clasificación OEE
    categoria_oee NVARCHAR(20) NOT NULL,                      -- 'disponibilidad', 'rendimiento', 'calidad'
    tipo_parada NVARCHAR(20) NOT NULL,                        -- 'planificada', 'no_planificada'

    -- Sub-categoría de análisis
    -- Disponibilidad: 'averia', 'mantenimiento_preventivo', 'setup', 'ajuste', 'falta_material',
    --                 'falta_operario', 'cambio_herramienta', 'espera_inspeccion'
    -- Rendimiento:    'velocidad_reducida', 'microstop', 'inestabilidad_proceso'
    -- Calidad:        'defecto_producto', 'rechazo_arranque', 'reproceso'
    subcategoria NVARCHAR(50) NULL,

    -- Si afecta el cálculo de tiempo productivo disponible
    descuenta_tiempo_disponible BIT DEFAULT 1,

    -- Estado
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,

    CONSTRAINT FK_motparada_empresa FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_motparada_codigo UNIQUE (cliente_id, empresa_id, codigo)
);

CREATE INDEX IDX_motparada_empresa ON mes_motivo_parada(empresa_id, es_activo);
CREATE INDEX IDX_motparada_oee ON mes_motivo_parada(categoria_oee, tipo_parada);

PRINT 'B04 mes_motivo_parada OK';
GO

-- ============================================================================
-- B05: mes_ejecucion_operacion
-- DESCRIPCIÓN: Registro de ejecución real de cada operación de una OP en piso.
--              Es el puente entre la planificación (mfg_orden_produccion_operacion)
--              y lo que realmente ocurrió. Alimenta el OEE y el costeo real.
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: mes_ejecucion_operacion
-- Descripción: Ejecución real de operaciones de producción en piso de fábrica
-- Uso: Captura inicio/fin real, cantidades reales, operario — alimenta OEE y costeo
-- Relaciones: Hijo de mfg_orden_produccion_operacion; genera mes_parada_maquina
-- -----------------------------------------------------------------------------
CREATE TABLE mes_ejecucion_operacion (
    ejecucion_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,

    -- Operación planificada que se está ejecutando
    op_operacion_id UNIQUEIDENTIFIER NOT NULL,                -- FK a mfg_orden_produccion_operacion
    orden_produccion_id UNIQUEIDENTIFIER NOT NULL,            -- FK a mfg_orden_produccion (desnormalizado para consultas)
    centro_trabajo_id UNIQUEIDENTIFIER NOT NULL,              -- FK a mfg_centro_trabajo

    -- Operario que ejecuta
    operario_id UNIQUEIDENTIFIER NULL,                        -- FK a hcm_empleado
    operario_nombre NVARCHAR(150) NULL,

    -- Tiempos reales de ejecución
    fecha_inicio_real DATETIME NOT NULL,
    fecha_fin_real DATETIME NULL,                             -- NULL si todavía está en proceso
    duracion_real_minutos AS (
        CASE WHEN fecha_fin_real IS NOT NULL
        THEN DATEDIFF(MINUTE, fecha_inicio_real, fecha_fin_real)
        ELSE NULL END
    ) PERSISTED,

    -- Cantidades reales producidas en esta ejecución
    cantidad_producida DECIMAL(18,4) DEFAULT 0,
    cantidad_aprobada DECIMAL(18,4) DEFAULT 0,
    cantidad_rechazada DECIMAL(18,4) DEFAULT 0,
    unidad_medida_id UNIQUEIDENTIFIER NULL,

    -- Estado de la ejecución
    estado NVARCHAR(20) DEFAULT 'en_proceso',                 -- 'en_proceso', 'pausada', 'completada', 'cancelada'

    -- Número de paradas registradas (referencial; el detalle en mes_parada_maquina)
    total_paradas INT DEFAULT 0,
    total_minutos_parada DECIMAL(10,2) DEFAULT 0,

    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,

    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,

    CONSTRAINT FK_mese_empresa FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_mese_op_op FOREIGN KEY (op_operacion_id)
        REFERENCES mfg_orden_produccion_operacion(op_operacion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_mese_op FOREIGN KEY (orden_produccion_id)
        REFERENCES mfg_orden_produccion(orden_produccion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_mese_ct FOREIGN KEY (centro_trabajo_id)
        REFERENCES mfg_centro_trabajo(centro_trabajo_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_mese_empresa ON mes_ejecucion_operacion(empresa_id, fecha_inicio_real DESC);
CREATE INDEX IDX_mese_op ON mes_ejecucion_operacion(orden_produccion_id);
CREATE INDEX IDX_mese_op_op ON mes_ejecucion_operacion(op_operacion_id);
CREATE INDEX IDX_mese_ct ON mes_ejecucion_operacion(centro_trabajo_id, fecha_inicio_real DESC);
CREATE INDEX IDX_mese_estado ON mes_ejecucion_operacion(estado, empresa_id);

PRINT 'B05 mes_ejecucion_operacion OK';
GO

-- ============================================================================
-- B06: mes_parada_maquina
-- DESCRIPCIÓN: Registro de cada parada individual durante una ejecución.
--              Cada parada tiene inicio, fin, motivo y duración.
--              La suma de paradas alimenta el cálculo de OEE por centro de trabajo.
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: mes_parada_maquina
-- Descripción: Registro de paradas de máquina durante la ejecución de operaciones
-- Uso: Análisis OEE — disponibilidad, rendimiento y calidad por centro de trabajo
-- Relaciones: Hijo de mes_ejecucion_operacion; usa catálogo mes_motivo_parada
-- -----------------------------------------------------------------------------
CREATE TABLE mes_parada_maquina (
    parada_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,

    -- Ejecución en la que ocurrió la parada
    ejecucion_id UNIQUEIDENTIFIER NOT NULL,                   -- FK a mes_ejecucion_operacion
    centro_trabajo_id UNIQUEIDENTIFIER NOT NULL,              -- Desnormalizado para consultas de OEE

    -- Motivo de la parada
    motivo_parada_id UNIQUEIDENTIFIER NULL,                   -- FK a mes_motivo_parada
    descripcion_parada NVARCHAR(500) NULL,                    -- Descripción libre si no hay motivo estándar

    -- Tiempos
    fecha_inicio_parada DATETIME NOT NULL,
    fecha_fin_parada DATETIME NULL,                           -- NULL si la parada sigue activa
    duracion_minutos AS (
        CASE WHEN fecha_fin_parada IS NOT NULL
        THEN DATEDIFF(MINUTE, fecha_inicio_parada, fecha_fin_parada)
        ELSE NULL END
    ) PERSISTED,

    -- Clasificación OEE (desnormalizada de mes_motivo_parada para consultas rápidas)
    categoria_oee NVARCHAR(20) NULL,                          -- 'disponibilidad', 'rendimiento', 'calidad'
    tipo_parada NVARCHAR(20) NULL,                            -- 'planificada', 'no_planificada'

    -- Quién registró
    registrado_por_usuario_id UNIQUEIDENTIFIER NULL,
    operario_id UNIQUEIDENTIFIER NULL,

    -- Estado
    estado NVARCHAR(20) DEFAULT 'activa',                     -- 'activa', 'cerrada'

    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    observaciones NVARCHAR(500) NULL,

    CONSTRAINT FK_parada_empresa FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_parada_ejecucion FOREIGN KEY (ejecucion_id)
        REFERENCES mes_ejecucion_operacion(ejecucion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_parada_motivo FOREIGN KEY (motivo_parada_id)
        REFERENCES mes_motivo_parada(motivo_parada_id) ON DELETE NO ACTION,
    CONSTRAINT FK_parada_ct FOREIGN KEY (centro_trabajo_id)
        REFERENCES mfg_centro_trabajo(centro_trabajo_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_parada_empresa ON mes_parada_maquina(empresa_id, fecha_inicio_parada DESC);
CREATE INDEX IDX_parada_ejecucion ON mes_parada_maquina(ejecucion_id);
CREATE INDEX IDX_parada_ct ON mes_parada_maquina(centro_trabajo_id, fecha_inicio_parada DESC);
CREATE INDEX IDX_parada_oee ON mes_parada_maquina(empresa_id, categoria_oee, fecha_inicio_parada DESC);
CREATE INDEX IDX_parada_motivo ON mes_parada_maquina(motivo_parada_id) WHERE motivo_parada_id IS NOT NULL;

PRINT 'B06 mes_parada_maquina OK';
GO

-- ============================================================================
-- B07: alr_regla_alerta
-- DESCRIPCIÓN: Definición de reglas del motor de alertas.
--              Una regla monitorea una entidad, evalúa una condición y
--              dispara una alerta cuando se cumple. Aplica a todos los módulos:
--              stock bajo (INV), OP atrasada (MFG), factura vencida (FIN),
--              lote por vencer (INV), parada larga (MES), etc.
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: alr_regla_alerta
-- Descripción: Definición de reglas del motor de alertas — qué monitorear y cuándo avisar
-- Uso: Configuración de alertas automáticas transversales a todos los módulos
-- Relaciones: Genera instancias en alr_alerta_generada cuando se dispara
-- -----------------------------------------------------------------------------
CREATE TABLE alr_regla_alerta (
    regla_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,

    -- Identificación
    codigo NVARCHAR(30) NOT NULL,
    nombre NVARCHAR(150) NOT NULL,
    descripcion NVARCHAR(500) NULL,

    -- Qué módulo y entidad monitorea
    modulo_origen NVARCHAR(10) NOT NULL,                      -- 'INV', 'MFG', 'FIN', 'PUR', 'SLS', 'MES', etc.
    entidad_monitoreada NVARCHAR(50) NOT NULL,                -- Nombre de la tabla: 'inv_stock', 'mfg_orden_produccion'
    campo_monitoreado NVARCHAR(50) NULL,                      -- Campo específico: 'cantidad_disponible', 'fecha_fin_programada'

    -- Tipo de condición
    tipo_alerta NVARCHAR(20) NOT NULL,                        -- 'umbral', 'vencimiento', 'inactividad', 'evento', 'delta'
    -- umbral:     campo > o < un valor
    -- vencimiento: fecha se acerca a hoy en N días
    -- inactividad: entidad sin movimiento en N días
    -- evento:     se inserta/actualiza un registro con estado específico
    -- delta:      el campo cambió más de N% respecto al período anterior

    -- Condición (para tipo 'umbral')
    operador NVARCHAR(10) NULL,                               -- '>', '<', '>=', '<=', '=', 'entre'
    valor_umbral DECIMAL(18,4) NULL,
    valor_umbral_superior DECIMAL(18,4) NULL,                 -- Para operador 'entre'

    -- Anticipación (para tipo 'vencimiento' e 'inactividad')
    dias_anticipacion INT NULL,                               -- Avisar N días antes del vencimiento

    -- Canales de notificación (JSON)
    -- Ej: ["sistema","email","push"]
    canales_notificacion NVARCHAR(500) NULL,

    -- Usuarios destino (JSON con lista de usuario_id o roles)
    -- Ej: {"usuarios":["uuid1","uuid2"],"roles":["JEFE_ALMACEN","GERENTE"]}
    destinatarios_json NVARCHAR(MAX) NULL,

    -- Frecuencia de evaluación
    frecuencia_evaluacion_min INT DEFAULT 60,                 -- Cada cuántos minutos se evalúa la regla

    -- Nivel de severidad
    severidad NVARCHAR(10) DEFAULT 'media',                   -- 'baja', 'media', 'alta', 'critica'

    -- Control de duplicados
    agrupar_alertas BIT DEFAULT 1,                            -- Si agrupa múltiples disparos en una alerta
    minutos_sin_repetir INT DEFAULT 1440,                     -- No repetir la alerta por N minutos (default: 24h)

    -- Estado
    es_activo BIT DEFAULT 1 NOT NULL,
    ultima_evaluacion DATETIME NULL,
    proxima_evaluacion DATETIME NULL,

    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,

    CONSTRAINT FK_alr_regla_empresa FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_alr_regla_codigo UNIQUE (cliente_id, empresa_id, codigo)
);

CREATE INDEX IDX_alr_regla_empresa ON alr_regla_alerta(empresa_id, es_activo);
CREATE INDEX IDX_alr_regla_modulo ON alr_regla_alerta(modulo_origen, es_activo);
CREATE INDEX IDX_alr_regla_eval ON alr_regla_alerta(proxima_evaluacion) WHERE es_activo = 1;

PRINT 'B07 alr_regla_alerta OK';
GO

-- ============================================================================
-- B08: alr_alerta_generada
-- DESCRIPCIÓN: Instancias disparadas por las reglas. Cada fila es una alerta
--              concreta: qué ocurrió, cuándo, sobre qué entidad y en qué estado.
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: alr_alerta_generada
-- Descripción: Instancias de alertas disparadas por las reglas del motor
-- Uso: Bandeja de alertas para usuarios — seguimiento hasta resolución
-- Relaciones: Hijo de alr_regla_alerta; apunta a la entidad que la disparó
-- -----------------------------------------------------------------------------
CREATE TABLE alr_alerta_generada (
    alerta_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,

    -- Regla que la generó
    regla_id UNIQUEIDENTIFIER NOT NULL,                       -- FK a alr_regla_alerta

    -- Qué disparó la alerta
    entidad_id UNIQUEIDENTIFIER NULL,                         -- ID del registro que disparó la alerta
    entidad_descripcion NVARCHAR(300) NULL,                   -- Descripción legible (ej: "Stock de POLO-V-AZ001-M: 2 uds")
    valor_detectado NVARCHAR(200) NULL,                       -- Valor que disparó la condición (ej: "2.00")

    -- Mensaje de la alerta
    titulo NVARCHAR(200) NOT NULL,
    mensaje NVARCHAR(MAX) NULL,

    -- Severidad (heredada de la regla en el momento del disparo)
    severidad NVARCHAR(10) NOT NULL,                          -- 'baja', 'media', 'alta', 'critica'

    -- Destino y estado por usuario
    usuario_destino_id UNIQUEIDENTIFIER NULL,                 -- FK a usuario (si es personal)
    -- Si es para varios usuarios se generan múltiples filas (una por usuario)

    -- Estado del ciclo de vida de la alerta
    estado NVARCHAR(20) DEFAULT 'nueva',                      -- 'nueva', 'vista', 'en_atencion', 'resuelta', 'ignorada'
    fecha_disparo DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_lectura DATETIME NULL,
    fecha_resolucion DATETIME NULL,
    resuelto_por_usuario_id UNIQUEIDENTIFIER NULL,
    nota_resolucion NVARCHAR(500) NULL,

    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,

    CONSTRAINT FK_alr_gen_empresa FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_alr_gen_regla FOREIGN KEY (regla_id)
        REFERENCES alr_regla_alerta(regla_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_alr_gen_empresa ON alr_alerta_generada(empresa_id, estado, fecha_disparo DESC);
CREATE INDEX IDX_alr_gen_regla ON alr_alerta_generada(regla_id, fecha_disparo DESC);
CREATE INDEX IDX_alr_gen_usuario ON alr_alerta_generada(usuario_destino_id, estado) WHERE usuario_destino_id IS NOT NULL;
CREATE INDEX IDX_alr_gen_estado ON alr_alerta_generada(estado, severidad, fecha_disparo DESC);
CREATE INDEX IDX_alr_gen_nueva ON alr_alerta_generada(empresa_id, fecha_disparo DESC) WHERE estado = 'nueva';

PRINT 'B08 alr_alerta_generada OK';
GO

-- ============================================================================
-- B09: wms_oleada
-- DESCRIPCIÓN: Agrupador de tareas WMS para picking por lotes/oleadas.
--              Permite procesar múltiples pedidos en una sola pasada por el almacén,
--              optimizando rutas y reduciendo tiempo de picking.
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: wms_oleada
-- Descripción: Agrupador de tareas WMS — permite procesar picking por lotes (oleadas)
-- Uso: Optimización de rutas de picking: agrupar tareas por zona, tipo o turno
-- Relaciones: Padre de wms_tarea (una oleada agrupa N tareas)
-- -----------------------------------------------------------------------------
CREATE TABLE wms_oleada (
    oleada_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    almacen_id UNIQUEIDENTIFIER NOT NULL,

    -- Identificación
    numero_oleada NVARCHAR(20) NOT NULL,

    -- Tipo de oleada
    tipo_oleada NVARCHAR(20) NOT NULL,                        -- 'picking', 'reposicion', 'inventario', 'mixta'

    -- Criterio de agrupación
    criterio_agrupacion NVARCHAR(50) NULL,                    -- 'zona', 'turno', 'transportista', 'prioridad', 'cliente'
    descripcion NVARCHAR(200) NULL,

    -- Totales (actualizados al agregar/completar tareas)
    total_tareas INT DEFAULT 0,
    tareas_completadas INT DEFAULT 0,
    tareas_canceladas INT DEFAULT 0,
    avance_pct AS (
        CASE WHEN total_tareas > 0
        THEN (CAST(tareas_completadas AS DECIMAL(5,2)) / total_tareas) * 100
        ELSE 0 END
    ) PERSISTED,

    -- Responsable
    responsable_usuario_id UNIQUEIDENTIFIER NULL,
    responsable_nombre NVARCHAR(150) NULL,

    -- Fechas
    fecha_programada DATE NOT NULL,
    fecha_inicio_real DATETIME NULL,
    fecha_fin_real DATETIME NULL,

    -- Estado
    estado NVARCHAR(20) DEFAULT 'creada',                     -- 'creada', 'asignada', 'en_proceso', 'completada', 'cancelada'

    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    observaciones NVARCHAR(500) NULL,

    CONSTRAINT FK_oleada_empresa FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_oleada_almacen FOREIGN KEY (almacen_id)
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_oleada_numero UNIQUE (cliente_id, almacen_id, numero_oleada)
);

CREATE INDEX IDX_oleada_empresa ON wms_oleada(empresa_id, estado);
CREATE INDEX IDX_oleada_almacen ON wms_oleada(almacen_id, fecha_programada DESC);
CREATE INDEX IDX_oleada_fecha ON wms_oleada(empresa_id, fecha_programada);

-- Ahora que wms_oleada existe, agregar la FK en wms_tarea
ALTER TABLE wms_tarea
    ADD CONSTRAINT FK_tarea_oleada FOREIGN KEY (oleada_id)
        REFERENCES wms_oleada(oleada_id) ON DELETE NO ACTION;

PRINT 'B09 wms_oleada OK + FK en wms_tarea agregada';
GO

-- ============================================================================
-- B10: mfg_calendario_capacidad
-- DESCRIPCIÓN: Capacidad disponible vs planificada por centro de trabajo y fecha.
--              Es la base del planeamiento de capacidad finita (CRP - Capacity
--              Requirements Planning). Sin esto, el MPS y el APS no pueden
--              detectar sobrecargas ni proponer reprogramaciones.
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: mfg_calendario_capacidad
-- Descripción: Horas disponibles y planificadas por centro de trabajo y fecha
-- Uso: Base de capacidad finita para MPS, MRP y APS — detectar sobrecargas
-- Relaciones: Por centro de trabajo (mfg_centro_trabajo) y período
-- -----------------------------------------------------------------------------
CREATE TABLE mfg_calendario_capacidad (
    calendario_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    centro_trabajo_id UNIQUEIDENTIFIER NOT NULL,              -- FK a mfg_centro_trabajo

    -- Período
    fecha DATE NOT NULL,
    turno NVARCHAR(20) NULL,                                  -- NULL = día completo; 'mañana', 'tarde', 'noche' si se divide

    -- Capacidad disponible (lo que puede producirse)
    horas_disponibles DECIMAL(8,2) NOT NULL,                  -- Horas teóricas del turno/día
    horas_no_productivas DECIMAL(8,2) DEFAULT 0,              -- Mantenimiento, limpieza, reuniones planificadas
    horas_efectivas AS (horas_disponibles - horas_no_productivas) PERSISTED,
    eficiencia_pct DECIMAL(5,2) DEFAULT 85,                   -- % de eficiencia esperada
    horas_capacidad_real AS (
        (horas_disponibles - horas_no_productivas) * (eficiencia_pct / 100)
    ) PERSISTED,

    -- Capacidad planificada (cargada por MPS/APS)
    horas_planificadas DECIMAL(8,2) DEFAULT 0,                -- Horas ya asignadas a OPs
    carga_pct AS (
        CASE WHEN horas_capacidad_real > 0
        THEN (horas_planificadas / horas_capacidad_real) * 100
        ELSE 0 END
    ) PERSISTED,
    sobrecargado AS (
        CASE WHEN horas_planificadas > horas_capacidad_real THEN 1 ELSE 0 END
    ) PERSISTED,

    -- Tipo de día
    tipo_dia NVARCHAR(20) DEFAULT 'laborable',                -- 'laborable', 'sabado', 'domingo', 'feriado', 'parada_programada'
    es_laborable BIT DEFAULT 1,

    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    observaciones NVARCHAR(200) NULL,

    CONSTRAINT FK_calcap_empresa FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_calcap_ct FOREIGN KEY (centro_trabajo_id)
        REFERENCES mfg_centro_trabajo(centro_trabajo_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_calcap_ct_fecha_turno UNIQUE (cliente_id, centro_trabajo_id, fecha, turno)
);

CREATE INDEX IDX_calcap_empresa ON mfg_calendario_capacidad(empresa_id, fecha);
CREATE INDEX IDX_calcap_ct ON mfg_calendario_capacidad(centro_trabajo_id, fecha);
CREATE INDEX IDX_calcap_sobrecarga ON mfg_calendario_capacidad(empresa_id, fecha)
    WHERE sobrecargado = 1;

PRINT 'B10 mfg_calendario_capacidad OK';
GO

-- ============================================================================
-- B11 / B12 / B13: APS — ADVANCED PLANNING AND SCHEDULING
-- DESCRIPCIÓN: Permite simular escenarios de programación y responder preguntas
--              como "¿qué pasa si atraso esta OP?" → recalcular automáticamente
--              → mover partidas → reprogramar máquinas → actualizar despachos.
--
--              ARQUITECTURA APS:
--              aps_escenario         → contenedor de una simulación o el plan activo
--              aps_tarea_programada  → cada OP/operación programada en tiempo/recurso
--              aps_restriccion_recurso → restricciones externas (mantenimiento, feriado, etc.)
--
--              El motor de scheduling (aplicación) lee estas tablas, aplica las
--              restricciones y escribe el resultado. Cuando el escenario se aprueba,
--              sus tareas actualizan mfg_orden_produccion y mfg_calendario_capacidad.
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: aps_escenario
-- Descripción: Contenedor de un escenario de planificación APS
-- Uso: Simular "qué pasa si" sin afectar el plan activo; aprobar para publicar
-- Relaciones: Padre de aps_tarea_programada y aps_restriccion_recurso
-- -----------------------------------------------------------------------------
CREATE TABLE aps_escenario (
    escenario_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,

    -- Identificación
    codigo NVARCHAR(30) NOT NULL,
    nombre NVARCHAR(150) NOT NULL,
    descripcion NVARCHAR(500) NULL,

    -- Tipo
    tipo_escenario NVARCHAR(20) NOT NULL,                     -- 'activo', 'simulacion', 'historico'
                                                              -- Solo uno puede ser 'activo' por empresa

    -- Horizonte de planificación
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,

    -- Parámetros del scheduler (JSON)
    -- Ej: {"algoritmo":"earliest_due_date","optimizar_por":"tardanza",
    --      "permitir_split_op":false,"considerar_setup":true}
    parametros_scheduler NVARCHAR(MAX) NULL,

    -- Si es simulación, de qué escenario parte
    escenario_base_id UNIQUEIDENTIFIER NULL,                  -- FK a aps_escenario (el activo que se clonó)
    descripcion_cambio NVARCHAR(500) NULL,                    -- Qué cambió respecto al base ("Atraso OP-2026-045")

    -- Resultado del scheduling
    fecha_ultimo_calculo DATETIME NULL,
    total_ops_programadas INT DEFAULT 0,
    total_ops_en_conflicto INT DEFAULT 0,                     -- OPs que no caben sin conflicto
    makespan_dias DECIMAL(10,2) NULL,                         -- Duración total del plan en días
    tardanza_total_dias DECIMAL(10,2) NULL,                   -- Suma de días de tardanza de todas las OPs

    -- Estado
    estado NVARCHAR(20) DEFAULT 'borrador',                   -- 'borrador', 'calculado', 'aprobado', 'publicado', 'archivado'
    aprobado_por_usuario_id UNIQUEIDENTIFIER NULL,
    fecha_aprobacion DATETIME NULL,
    publicado_por_usuario_id UNIQUEIDENTIFIER NULL,
    fecha_publicacion DATETIME NULL,

    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    observaciones NVARCHAR(MAX) NULL,

    CONSTRAINT FK_apsesc_empresa FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_apsesc_base FOREIGN KEY (escenario_base_id)
        REFERENCES aps_escenario(escenario_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_apsesc_codigo UNIQUE (cliente_id, empresa_id, codigo)
);

CREATE INDEX IDX_apsesc_empresa ON aps_escenario(empresa_id, tipo_escenario);
CREATE INDEX IDX_apsesc_estado ON aps_escenario(empresa_id, estado);
CREATE INDEX IDX_apsesc_activo ON aps_escenario(empresa_id)
    WHERE tipo_escenario = 'activo';                          -- Solo uno activo por empresa

PRINT 'B11 aps_escenario OK';
GO

-- -----------------------------------------------------------------------------
-- Tabla: aps_tarea_programada
-- Descripción: Cada OP u operación programada por el motor APS en un escenario.
--              Define cuándo empieza, cuándo termina, en qué recurso y con
--              qué precedencias. Es el "Gantt" en base de datos.
-- Uso: Visualización del Gantt; base para reprogramación automática en cascada
-- Relaciones: Hijo de aps_escenario; referencia mfg_orden_produccion y mfg_centro_trabajo
-- -----------------------------------------------------------------------------
CREATE TABLE aps_tarea_programada (
    aps_tarea_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    escenario_id UNIQUEIDENTIFIER NOT NULL,                   -- FK a aps_escenario

    -- Qué se programa
    tipo_tarea NVARCHAR(20) NOT NULL,                        -- 'op_completa', 'operacion', 'setup', 'mantenimiento'
    orden_produccion_id UNIQUEIDENTIFIER NULL,                -- FK a mfg_orden_produccion
    op_operacion_id UNIQUEIDENTIFIER NULL,                    -- FK a mfg_orden_produccion_operacion (si es por operación)

    -- En qué recurso
    centro_trabajo_id UNIQUEIDENTIFIER NOT NULL,              -- FK a mfg_centro_trabajo

    -- Cuándo (el scheduler decide estos valores)
    fecha_inicio_programada DATETIME NOT NULL,
    fecha_fin_programada DATETIME NOT NULL,
    duracion_horas AS (
        DATEDIFF(MINUTE, fecha_inicio_programada, fecha_fin_programada) / 60.0
    ) PERSISTED,

    -- Prioridad y urgencia
    prioridad INT DEFAULT 3,                                   -- 1=Urgente → 4=Baja
    fecha_entrega_comprometida DATE NULL,                      -- Fecha límite para completarse
    dias_tardanza AS (
        CASE
            WHEN fecha_entrega_comprometida IS NOT NULL
             AND CAST(fecha_fin_programada AS DATE) > fecha_entrega_comprometida
            THEN DATEDIFF(DAY, fecha_entrega_comprometida, CAST(fecha_fin_programada AS DATE))
            ELSE 0
        END
    ) PERSISTED,

    -- Precedencias (qué tareas deben terminar antes de que esta empiece)
    -- Se registran en una tabla de relaciones o en JSON simple
    -- Para el caso simple usamos JSON: ["aps_tarea_id_1", "aps_tarea_id_2"]
    predecessores_json NVARCHAR(MAX) NULL,

    -- Cantidades
    cantidad_programada DECIMAL(18,4) NULL,
    unidad_medida_id UNIQUEIDENTIFIER NULL,

    -- Estado de la tarea en el escenario
    estado_tarea NVARCHAR(20) DEFAULT 'programada',           -- 'programada', 'en_conflicto', 'fija', 'completada'
    -- 'fija': el usuario la ancló — el scheduler no la puede mover
    es_fija BIT DEFAULT 0,
    motivo_conflicto NVARCHAR(300) NULL,                      -- Si estado='en_conflicto', explica por qué

    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,

    CONSTRAINT FK_apstarea_empresa FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_apstarea_escenario FOREIGN KEY (escenario_id)
        REFERENCES aps_escenario(escenario_id) ON DELETE NO ACTION,
    CONSTRAINT FK_apstarea_op FOREIGN KEY (orden_produccion_id)
        REFERENCES mfg_orden_produccion(orden_produccion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_apstarea_op_op FOREIGN KEY (op_operacion_id)
        REFERENCES mfg_orden_produccion_operacion(op_operacion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_apstarea_ct FOREIGN KEY (centro_trabajo_id)
        REFERENCES mfg_centro_trabajo(centro_trabajo_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_apstarea_escenario ON aps_tarea_programada(escenario_id, fecha_inicio_programada);
CREATE INDEX IDX_apstarea_op ON aps_tarea_programada(orden_produccion_id) WHERE orden_produccion_id IS NOT NULL;
CREATE INDEX IDX_apstarea_ct ON aps_tarea_programada(centro_trabajo_id, escenario_id, fecha_inicio_programada);
CREATE INDEX IDX_apstarea_conflicto ON aps_tarea_programada(escenario_id)
    WHERE estado_tarea = 'en_conflicto';
CREATE INDEX IDX_apstarea_tardanza ON aps_tarea_programada(escenario_id, dias_tardanza DESC)
    WHERE dias_tardanza > 0;

PRINT 'B12 aps_tarea_programada OK';
GO

-- -----------------------------------------------------------------------------
-- Tabla: aps_restriccion_recurso
-- Descripción: Restricciones externas sobre recursos (centros de trabajo)
--              dentro de un escenario. El scheduler las respeta al programar.
--              Ejemplos: mantenimiento programado, feriado, reducción de turno,
--              materia prima no disponible hasta cierta fecha.
-- Uso: Informar al motor APS de períodos en que un recurso no está disponible
-- Relaciones: Hijo de aps_escenario; afecta a mfg_centro_trabajo
-- -----------------------------------------------------------------------------
CREATE TABLE aps_restriccion_recurso (
    restriccion_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    escenario_id UNIQUEIDENTIFIER NOT NULL,                   -- FK a aps_escenario

    -- Recurso afectado
    tipo_recurso NVARCHAR(20) NOT NULL,                       -- 'centro_trabajo', 'operario', 'material'
    recurso_id UNIQUEIDENTIFIER NOT NULL,                     -- ID del recurso según tipo_recurso

    -- Período de la restricción
    fecha_inicio DATETIME NOT NULL,
    fecha_fin DATETIME NOT NULL,

    -- Tipo de restricción
    tipo_restriccion NVARCHAR(30) NOT NULL,                   -- 'no_disponible', 'capacidad_reducida',
                                                              -- 'material_no_disponible', 'feriado',
                                                              -- 'mantenimiento', 'parada_planificada'
    -- Si es 'capacidad_reducida', en qué porcentaje
    capacidad_reducida_pct DECIMAL(5,2) NULL,                 -- Ej: 50 = solo el 50% de capacidad disponible

    -- Descripción
    descripcion NVARCHAR(300) NULL,

    -- Es fija (el APS no puede ignorarla) o es flexible
    es_fija BIT DEFAULT 1,

    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,

    CONSTRAINT FK_apsrest_empresa FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_apsrest_escenario FOREIGN KEY (escenario_id)
        REFERENCES aps_escenario(escenario_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_apsrest_escenario ON aps_restriccion_recurso(escenario_id, fecha_inicio);
CREATE INDEX IDX_apsrest_recurso ON aps_restriccion_recurso(escenario_id, tipo_recurso, recurso_id);
CREATE INDEX IDX_apsrest_periodo ON aps_restriccion_recurso(empresa_id, fecha_inicio, fecha_fin);

PRINT 'B13 aps_restriccion_recurso OK';
GO

-- ============================================================================
-- B14 / B15: RPT — CAPA SEMÁNTICA DE REPORTES
-- DESCRIPCIÓN: Permite que el cliente defina sus propios KPIs y reportes
--              sin que el equipo de desarrollo tenga que programar cada uno.
--              rpt_metrica:   define UNA métrica calculable (ej: "ventas del mes")
--              rpt_dimension: define UNA dimensión de análisis (ej: "por producto")
--              La capa de presentación combina métricas + dimensiones para
--              construir reportes dinámicos.
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: rpt_metrica
-- Descripción: Métrica de autoservicio — define cómo calcular un KPI
-- Uso: Base de la capa semántica para reportes dinámicos configurables por el cliente
-- Relaciones: Se combina con rpt_dimension para construir reportes
-- -----------------------------------------------------------------------------
CREATE TABLE rpt_metrica (
    metrica_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,

    -- Identificación
    codigo NVARCHAR(30) NOT NULL,
    nombre NVARCHAR(150) NOT NULL,
    descripcion NVARCHAR(500) NULL,

    -- Clasificación
    modulo NVARCHAR(10) NOT NULL,                             -- 'SLS', 'INV', 'MFG', 'FIN', 'PUR', 'MES', etc.
    categoria NVARCHAR(50) NULL,                              -- 'ventas', 'produccion', 'calidad', 'costos'

    -- Definición de la métrica
    tabla_origen NVARCHAR(100) NOT NULL,                      -- Tabla o vista principal (ej: 'sls_pedido_detalle')
    campo_valor NVARCHAR(100) NOT NULL,                       -- Campo a agregar (ej: 'total_item')
    tipo_agregacion NVARCHAR(20) NOT NULL,                    -- 'SUM', 'COUNT', 'AVG', 'MIN', 'MAX', 'COUNT_DISTINCT'
    filtro_base NVARCHAR(MAX) NULL,                           -- WHERE fijo de la métrica (ej: "estado = 'completado'")

    -- Formato de visualización
    tipo_dato NVARCHAR(20) DEFAULT 'decimal',                 -- 'decimal', 'entero', 'porcentaje', 'moneda', 'tiempo'
    decimales INT DEFAULT 2,
    prefijo NVARCHAR(10) NULL,                                -- Ej: 'S/.' para soles
    sufijo NVARCHAR(10) NULL,                                 -- Ej: '%', 'h', 'kg'

    -- Disponibilidad
    es_activo BIT DEFAULT 1 NOT NULL,
    es_sistema BIT DEFAULT 0,                                 -- Si fue creada por el sistema (no borrable)

    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,

    CONSTRAINT FK_rptmet_empresa FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_rptmet_codigo UNIQUE (cliente_id, empresa_id, codigo)
);

CREATE INDEX IDX_rptmet_empresa ON rpt_metrica(empresa_id, es_activo);
CREATE INDEX IDX_rptmet_modulo ON rpt_metrica(modulo, es_activo);

PRINT 'B14 rpt_metrica OK';
GO

-- -----------------------------------------------------------------------------
-- Tabla: rpt_dimension
-- Descripción: Dimensión de análisis reutilizable — define cómo agrupar/filtrar
--              una métrica (ej: por producto, por cliente, por fecha, por vendedor)
-- Uso: Combinada con rpt_metrica permite al cliente construir su propio reporte
-- Relaciones: Se usa en conjunto con rpt_metrica por la capa de presentación
-- -----------------------------------------------------------------------------
CREATE TABLE rpt_dimension (
    dimension_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,

    -- Identificación
    codigo NVARCHAR(30) NOT NULL,
    nombre NVARCHAR(150) NOT NULL,
    descripcion NVARCHAR(500) NULL,

    -- Clasificación
    modulo NVARCHAR(10) NOT NULL,                             -- Mismo módulo que las métricas con que se usa
    tipo_dimension NVARCHAR(20) NOT NULL,                     -- 'tiempo', 'entidad', 'geografica', 'categorica'

    -- Definición
    tabla_dimension NVARCHAR(100) NOT NULL,                   -- Tabla de la dimensión (ej: 'inv_producto')
    campo_join NVARCHAR(100) NOT NULL,                        -- Campo para hacer JOIN con la tabla origen (ej: 'producto_id')
    campo_etiqueta NVARCHAR(100) NOT NULL,                    -- Campo a mostrar como etiqueta (ej: 'nombre')
    campo_codigo NVARCHAR(100) NULL,                          -- Campo de código corto (ej: 'codigo_sku')

    -- Para dimensiones de tiempo
    -- tipo_periodo: 'dia', 'semana', 'mes', 'trimestre', 'año'
    tipo_periodo NVARCHAR(20) NULL,

    -- Jerarquía (ej: año → mes → semana → día)
    dimension_padre_id UNIQUEIDENTIFIER NULL,                 -- FK a sí misma para jerarquías

    -- Compatibilidad: qué módulos/métricas puede usar esta dimensión (JSON)
    -- Ej: ["SLS","INV","FIN"] — si NULL aplica a todos
    modulos_compatibles NVARCHAR(500) NULL,

    -- Disponibilidad
    es_activo BIT DEFAULT 1 NOT NULL,
    es_sistema BIT DEFAULT 0,

    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,

    CONSTRAINT FK_rptdim_empresa FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_rptdim_padre FOREIGN KEY (dimension_padre_id)
        REFERENCES rpt_dimension(dimension_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_rptdim_codigo UNIQUE (cliente_id, empresa_id, codigo)
);

CREATE INDEX IDX_rptdim_empresa ON rpt_dimension(empresa_id, es_activo);
CREATE INDEX IDX_rptdim_modulo ON rpt_dimension(modulo, es_activo);

PRINT 'B15 rpt_dimension OK';
GO

PRINT 'PARTE B completada: 15 tablas nuevas creadas';
GO

-- ============================================================================
-- RESUMEN FINAL
-- ============================================================================
PRINT '============================================================';
PRINT 'V050__core_upgrade.sql completado exitosamente';
PRINT '------------------------------------------------------------';
PRINT 'PARTE A - Tablas modificadas (10):';
PRINT '  A01 inv_almacen              +estrategia_salida_default';
PRINT '  A02 wms_ubicacion            +estrategia_salida';
PRINT '  A03 wms_tarea                +oleada_id FK';
PRINT '  A04 inv_movimiento_detalle   +lote_id FK, lote→lote_codigo';
PRINT '  A05 wms_stock_ubicacion      +lote_id FK, lote→lote_codigo';
PRINT '  A06 qms_inspeccion           +lote_id FK';
PRINT '  A07 qms_no_conformidad       +lote_id FK';
PRINT '  A08 pur_recepcion_detalle    +lote_id FK';
PRINT '  A09 mfg_consumo_materiales   +lote_id FK';
PRINT '  A10 invbill_comprobante_det  +lote_id FK';
PRINT '------------------------------------------------------------';
PRINT 'PARTE B - Tablas nuevas (15):';
PRINT '  B01 cfg_vertical_empresa     Control-plane de verticales';
PRINT '  B02 inv_lote                 Entidad formal de lote';
PRINT '  B03 inv_producto_variante    Variantes Core multiindustria';
PRINT '  B04 mes_motivo_parada        Catálogo OEE';
PRINT '  B05 mes_ejecucion_operacion  Ejecución real en piso';
PRINT '  B06 mes_parada_maquina       Paradas para OEE';
PRINT '  B07 alr_regla_alerta         Motor de alertas - reglas';
PRINT '  B08 alr_alerta_generada      Motor de alertas - instancias';
PRINT '  B09 wms_oleada               Agrupador de tareas WMS';
PRINT '  B10 mfg_calendario_capacidad Capacidad finita por CT';
PRINT '  B11 aps_escenario            APS - escenario simulación';
PRINT '  B12 aps_tarea_programada     APS - Gantt en base de datos';
PRINT '  B13 aps_restriccion_recurso  APS - restricciones externas';
PRINT '  B14 rpt_metrica              RPT - capa semántica métricas';
PRINT '  B15 rpt_dimension            RPT - dimensiones de análisis';
PRINT '------------------------------------------------------------';
PRINT 'SIGUIENTE: V060__tablas_verticales.sql (TXT, FOD, MET, DIS)';
PRINT '============================================================';
GO