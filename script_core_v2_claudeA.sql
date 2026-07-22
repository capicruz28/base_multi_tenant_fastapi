-- ============================================================================
-- SCRIPT: CORE UPGRADE - FORTALECIMIENTO PLATAFORMA MULTI-RUBRO
-- DESCRIPCIÓN: Nuevas tablas Core + tablas modificadas (en CREATE completo).
--              No usar ALTER — reemplazar tablas existentes con este script.
--              Identifica campos nuevos con el comentario: -- [NUEVO]
-- ARQUITECTURA: Multi-tenant SaaS (BD dedicada por cliente)
-- PREREQUISITO: V010__tablas_bd_erp_completo.sql
-- VERSIÓN: 1.0
-- FECHA: Julio 2026
-- ============================================================================

-- ============================================================================
-- ÍNDICE DE CAMBIOS
-- ============================================================================
-- SECCIÓN A: CFG  - Control-plane de verticales por empresa      [NUEVA]
-- SECCIÓN B: INV  - inv_lote formal                              [NUEVA]
--                   inv_producto_variante                        [NUEVA]
--                   inv_almacen          + estrategia salida     [MODIFICADA]
--                   inv_movimiento_detalle + lote_id FK          [MODIFICADA]
-- SECCIÓN C: WMS  - wms_ubicacion        + estrategia salida     [MODIFICADA]
--                   wms_stock_ubicacion   + lote_id FK           [MODIFICADA]
--                   wms_oleada                                   [NUEVA]
--                   wms_tarea             + oleada_id FK         [MODIFICADA]
-- SECCIÓN D: QMS  - qms_inspeccion       + lote_id FK           [MODIFICADA]
--                   qms_no_conformidad    + lote_id FK           [MODIFICADA]
-- SECCIÓN E: PUR  - pur_recepcion_detalle + lote_id FK          [MODIFICADA]
-- SECCIÓN F: MFG  - mfg_consumo_materiales + lote_id FK         [MODIFICADA]
--                   mfg_calendario_capacidad                     [NUEVA]
-- SECCIÓN G: MES  - Manufacturing Execution System               [NUEVO]
--                   mes_ejecucion_operacion
--                   mes_parada_maquina
-- SECCIÓN H: APS  - Advanced Planning & Scheduling               [NUEVO]
--                   aps_escenario
--                   aps_carga_centro_trabajo
--                   aps_secuencia_operacion
--                   aps_simulacion_impacto
-- SECCIÓN I: ALR  - Motor de Alertas                             [NUEVO]
--                   alr_regla_alerta
--                   alr_alerta_generada
-- SECCIÓN J: FACT - invbill_comprobante_detalle + lote_id FK    [MODIFICADA]
-- SECCIÓN K: RPT  - Capa semántica de reportes                  [NUEVO]
--                   rpt_metrica
--                   rpt_dimension
-- ============================================================================


-- ============================================================================
-- SECCIÓN A: CFG - CONTROL-PLANE DE VERTICALES
-- ============================================================================
-- DESCRIPCIÓN: Controla qué módulos verticales (TXT, FOD, MET, DIS, SRV)
--              están activos por empresa/tenant. Permite que la app muestre
--              solo las opciones del rubro del cliente sin lógica hardcodeada.
-- DEPENDENCIAS: ORG
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: cfg_vertical_empresa
-- Descripción: Verticales industriales habilitadas por empresa. Una empresa
--              puede tener más de una vertical activa (ej: textil + servicios).
-- Uso: La capa de aplicación consulta esta tabla al cargar el menú y los
--      módulos específicos de cada cliente.
-- Relaciones: org_empresa
-- -----------------------------------------------------------------------------
CREATE TABLE cfg_vertical_empresa (
    vertical_empresa_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id          UNIQUEIDENTIFIER NOT NULL,
    empresa_id          UNIQUEIDENTIFIER NOT NULL,

    -- Vertical habilitada
    codigo_vertical     NVARCHAR(10)     NOT NULL,            -- 'TXT','FOD','MET','DIS','SRV','FAR','AGR'
    nombre_vertical     NVARCHAR(100)    NOT NULL,            -- Nombre legible de la vertical
    descripcion         NVARCHAR(255)    NULL,

    -- Control de activación
    fecha_activacion    DATE             NOT NULL DEFAULT GETDATE(),
    fecha_desactivacion DATE             NULL,
    activado_por_usuario_id UNIQUEIDENTIFIER NULL,

    -- Estado
    es_activo           BIT              DEFAULT 1 NOT NULL,

    -- Auditoría
    fecha_creacion      DATETIME         DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME         NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,

    -- Observaciones
    observaciones       NVARCHAR(500)    NULL,

    CONSTRAINT FK_cfgvert_empresa FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_cfgvert_empresa_vertical UNIQUE (cliente_id, empresa_id, codigo_vertical),
    CONSTRAINT CK_cfgvert_codigo CHECK (codigo_vertical IN (
        'TXT','FOD','MET','DIS','SRV','FAR','AGR','MIN','CON','AUTO'
        -- TXT=Textil, FOD=Alimentos, MET=Metalmecánica, DIS=Distribución,
        -- SRV=Servicios, FAR=Farmacéutica, AGR=Agroindustria,
        -- MIN=Minería, CON=Construcción, AUTO=Automotriz
    ))
);

CREATE INDEX IDX_cfgvert_empresa     ON cfg_vertical_empresa(empresa_id);
CREATE INDEX IDX_cfgvert_codigo      ON cfg_vertical_empresa(codigo_vertical);
CREATE INDEX IDX_cfgvert_activo      ON cfg_vertical_empresa(es_activo);


-- ============================================================================
-- SECCIÓN B: INV - INVENTARIOS (NUEVAS + MODIFICADAS)
-- ============================================================================
-- DESCRIPCIÓN: Se agrega inv_lote como entidad formal (reemplaza el campo
--              lote NVARCHAR suelto en 7 tablas), inv_producto_variante como
--              capacidad Core (no vertical), y se extiende inv_almacen con
--              estrategia de salida de stock (FIFO/FEFO/LEFO).
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: inv_lote  [NUEVA]
-- Descripción: Entidad formal de lote/partida de producción o recepción.
--              Centraliza toda la información del lote en un solo lugar.
--              Las tablas que antes tenían lote NVARCHAR(50) pasan a referenciar
--              lote_id (FK nullable para compatibilidad retroactiva).
-- Uso: Trazabilidad completa hacia atrás (de qué compra/OP viene) y hacia
--      adelante (a qué despachos/facturas fue). Aplica a todos los rubros.
-- Relaciones: inv_producto, pur_recepcion, mfg_orden_produccion
-- -----------------------------------------------------------------------------
CREATE TABLE inv_lote (
    lote_id             UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id          UNIQUEIDENTIFIER NOT NULL,
    empresa_id          UNIQUEIDENTIFIER NOT NULL,

    -- Identificación
    numero_lote         NVARCHAR(50)     NOT NULL,            -- Código único del lote
    producto_id         UNIQUEIDENTIFIER NOT NULL,

    -- Origen del lote
    origen              NVARCHAR(20)     NOT NULL,            -- 'compra','produccion','devolucion','apertura'
    recepcion_id        UNIQUEIDENTIFIER NULL,                -- Si origen='compra' -> pur_recepcion
    orden_produccion_id UNIQUEIDENTIFIER NULL,                -- Si origen='produccion' -> mfg_orden_produccion

    -- Proveedor (si aplica)
    proveedor_id        UNIQUEIDENTIFIER NULL,
    lote_proveedor      NVARCHAR(50)     NULL,                -- Número de lote del proveedor

    -- Fechas críticas
    fecha_fabricacion   DATE             NULL,
    fecha_vencimiento   DATE             NULL,
    fecha_ingreso       DATE             NOT NULL DEFAULT GETDATE(),

    -- Cantidades
    cantidad_inicial    DECIMAL(18,4)    NOT NULL,
    cantidad_disponible DECIMAL(18,4)    NOT NULL,
    unidad_medida_id    UNIQUEIDENTIFIER NOT NULL,

    -- Estado del lote
    estado              NVARCHAR(20)     DEFAULT 'disponible', -- 'disponible','cuarentena','bloqueado','vencido','agotado'
    motivo_bloqueo      NVARCHAR(255)    NULL,
    aprobado_por_usuario_id UNIQUEIDENTIFIER NULL,
    fecha_aprobacion    DATETIME         NULL,

    -- Atributos extendidos (JSON para datos de lote específicos por industria)
    -- Ejemplos: {"temperatura_almacenamiento":"-18","numero_colada":"C-2024-001"}
    atributos_lote      NVARCHAR(MAX)    NULL,

    -- Estado y auditoría
    es_activo           BIT              DEFAULT 1 NOT NULL,
    fecha_creacion      DATETIME         DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME         NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,

    observaciones       NVARCHAR(MAX)    NULL,

    CONSTRAINT FK_lote_empresa FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_lote_producto FOREIGN KEY (producto_id)
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_lote_um FOREIGN KEY (unidad_medida_id)
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT FK_lote_proveedor FOREIGN KEY (proveedor_id)
        REFERENCES pur_proveedor(proveedor_id) ON DELETE NO ACTION,
    CONSTRAINT FK_lote_op FOREIGN KEY (orden_produccion_id)
        REFERENCES mfg_orden_produccion(orden_produccion_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_lote_numero UNIQUE (cliente_id, empresa_id, producto_id, numero_lote)
);

CREATE INDEX IDX_lote_empresa         ON inv_lote(empresa_id);
CREATE INDEX IDX_lote_producto        ON inv_lote(producto_id);
CREATE INDEX IDX_lote_estado          ON inv_lote(estado);
CREATE INDEX IDX_lote_vencimiento     ON inv_lote(fecha_vencimiento) WHERE fecha_vencimiento IS NOT NULL;
CREATE INDEX IDX_lote_numero          ON inv_lote(numero_lote);


-- -----------------------------------------------------------------------------
-- Tabla: inv_producto_variante  [NUEVA]
-- Descripción: Variantes de un producto base (color/talla en ropa, voltaje/
--              color en electrónica, medida/acabado en ferreterÍa, etc.).
--              Es capacidad Core — no pertenece a ninguna vertical.
--              Cada variante puede tener su propio SKU en inv_producto (opcional).
-- Uso: Reportes consolidados por "modelo padre", listas de precio por variante,
--      explosión de materiales por talla/color.
-- Relaciones: inv_producto (padre), inv_producto (SKU variante)
-- -----------------------------------------------------------------------------
CREATE TABLE inv_producto_variante (
    variante_id             UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id              UNIQUEIDENTIFIER NOT NULL,
    empresa_id              UNIQUEIDENTIFIER NOT NULL,

    -- Producto padre (modelo/artículo base)
    producto_padre_id       UNIQUEIDENTIFIER NOT NULL,

    -- SKU concreto de esta variante (opcional: si ya existe en inv_producto)
    producto_variante_id    UNIQUEIDENTIFIER NULL,

    -- Código de la variante
    codigo_variante         NVARCHAR(50)     NOT NULL,        -- Ej: "POLO-BL-M" (padre POLO, blanco, talla M)

    -- Dimensiones de variación (genéricas para cualquier industria)
    dimension_1_nombre      NVARCHAR(30)     NULL,            -- Ej: 'Color', 'Voltaje', 'Talla', 'Medida'
    dimension_1_valor       NVARCHAR(50)     NULL,            -- Ej: 'Blanco', '220V', 'M', '3/4"'

    dimension_2_nombre      NVARCHAR(30)     NULL,            -- Ej: 'Talla', 'Amperaje', 'Acabado'
    dimension_2_valor       NVARCHAR(50)     NULL,            -- Ej: 'M', '16A', 'Satinado'

    dimension_3_nombre      NVARCHAR(30)     NULL,            -- Ej: 'Largo', 'Versión'
    dimension_3_valor       NVARCHAR(50)     NULL,

    -- Atributos adicionales específicos de la variante (JSON)
    -- Ejemplos textil: {"pantone":"PMS 286 C","tono":"aprobado"}
    -- Ejemplos electrónica: {"compatibilidad":"iPhone 14"}
    atributos_variante      NVARCHAR(MAX)    NULL,

    -- Estado
    estado                  NVARCHAR(20)     DEFAULT 'activo', -- 'activo','inactivo','descontinuado'
    es_activo               BIT              DEFAULT 1 NOT NULL,

    -- Auditoría
    fecha_creacion          DATETIME         DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion     DATETIME         NULL,
    usuario_creacion_id     UNIQUEIDENTIFIER NULL,

    CONSTRAINT FK_pvar_empresa FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_pvar_padre FOREIGN KEY (producto_padre_id)
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_pvar_sku FOREIGN KEY (producto_variante_id)
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_pvar_codigo UNIQUE (cliente_id, empresa_id, producto_padre_id, codigo_variante)
);

CREATE INDEX IDX_pvar_padre           ON inv_producto_variante(producto_padre_id);
CREATE INDEX IDX_pvar_sku             ON inv_producto_variante(producto_variante_id) WHERE producto_variante_id IS NOT NULL;
CREATE INDEX IDX_pvar_dim1            ON inv_producto_variante(dimension_1_valor);


-- -----------------------------------------------------------------------------
-- Tabla: inv_almacen  [MODIFICADA]
-- Cambio: + estrategia_salida_stock (FIFO/FEFO/LEFO) para control de WMS.
--           FEFO es obligatorio en alimentos y farma; FIFO en general;
--           LEFO en algunos casos de materiales especiales.
-- -----------------------------------------------------------------------------
CREATE TABLE inv_almacen (
    almacen_id              UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id              UNIQUEIDENTIFIER NOT NULL,
    empresa_id              UNIQUEIDENTIFIER NOT NULL,
    sucursal_id             UNIQUEIDENTIFIER NULL,            -- Sucursal a la que pertenece

    codigo                  NVARCHAR(20)     NOT NULL,
    nombre                  NVARCHAR(100)    NOT NULL,
    descripcion             NVARCHAR(255)    NULL,

    -- Tipo y clasificación
    tipo_almacen            NVARCHAR(30)     NOT NULL,        -- 'general','materia_prima','producto_terminado',
                                                               -- 'transito','consignacion','cuarentena'

    -- Estrategia de salida de stock [NUEVO]
    estrategia_salida       NVARCHAR(10)     DEFAULT 'fifo',  -- [NUEVO] 'fifo','fefo','lefo','manual'
                                                               -- FIFO = First In First Out (general)
                                                               -- FEFO = First Expired First Out (alimentos/farma)
                                                               -- LEFO = Last Expired First Out (casos especiales)
                                                               -- MANUAL = el operador decide

    -- Ubicación
    direccion               NVARCHAR(255)    NULL,
    responsable_usuario_id  UNIQUEIDENTIFIER NULL,
    responsable_nombre      NVARCHAR(150)    NULL,

    -- Configuración
    es_almacen_principal    BIT              DEFAULT 0,
    permite_ventas          BIT              DEFAULT 0,        -- Si se puede vender desde este almacén
    permite_compras         BIT              DEFAULT 1,        -- Si se reciben compras
    permite_produccion      BIT              DEFAULT 0,        -- Si recibe/despacha producción

    -- Capacidad
    capacidad_m3            DECIMAL(12,2)    NULL,             -- Capacidad en metros cúbicos
    capacidad_kg            DECIMAL(12,2)    NULL,             -- Capacidad en kilogramos
    capacidad_unidades      INT              NULL,             -- Capacidad en unidades/pallets

    -- Centro de costo
    centro_costo_id         UNIQUEIDENTIFIER NULL,

    -- Estado y auditoría
    es_activo               BIT              DEFAULT 1 NOT NULL,
    fecha_creacion          DATETIME         DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion     DATETIME         NULL,
    usuario_creacion_id     UNIQUEIDENTIFIER NULL,

    CONSTRAINT FK_alm_empresa  FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_alm_sucursal FOREIGN KEY (sucursal_id)
        REFERENCES org_sucursal(sucursal_id) ON DELETE NO ACTION,
    CONSTRAINT FK_alm_cc       FOREIGN KEY (centro_costo_id)
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_alm_codigo   UNIQUE (cliente_id, empresa_id, codigo),
    CONSTRAINT CK_alm_estrategia CHECK (estrategia_salida IN ('fifo','fefo','lefo','manual'))
);

CREATE INDEX IDX_alm_empresa          ON inv_almacen(empresa_id);
CREATE INDEX IDX_alm_tipo             ON inv_almacen(tipo_almacen);


-- -----------------------------------------------------------------------------
-- Tabla: inv_movimiento_detalle  [MODIFICADA]
-- Cambio: + lote_id FK nullable a inv_lote (reemplaza lote NVARCHAR suelto).
--           Se mantiene lote NVARCHAR como fallback para datos históricos.
-- -----------------------------------------------------------------------------
CREATE TABLE inv_movimiento_detalle (
    movimiento_detalle_id   UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id              UNIQUEIDENTIFIER NOT NULL,
    empresa_id              UNIQUEIDENTIFIER NOT NULL,
    movimiento_id           UNIQUEIDENTIFIER NOT NULL,
    producto_id             UNIQUEIDENTIFIER NOT NULL,

    -- Cantidad y unidad
    cantidad                DECIMAL(18,4)    NOT NULL,
    unidad_medida_id        UNIQUEIDENTIFIER NOT NULL,
    cantidad_base           DECIMAL(18,4)    NOT NULL,        -- Cantidad convertida a unidad base

    -- Costos
    costo_unitario          DECIMAL(18,4)    DEFAULT 0,       -- Costo por unidad
    costo_total             AS (cantidad * costo_unitario) PERSISTED,
    moneda_id               UNIQUEIDENTIFIER NOT NULL,

    -- Lote y vencimiento
    lote_id                 UNIQUEIDENTIFIER NULL,            -- [NUEVO] FK formal a inv_lote
    lote                    NVARCHAR(50)     NULL,            -- Mantener para retrocompatibilidad / datos históricos
    fecha_vencimiento       DATE             NULL,
    numero_serie            NVARCHAR(100)    NULL,

    -- Ubicación (WMS)
    ubicacion_almacen       NVARCHAR(50)     NULL,

    -- Observaciones
    observaciones           NVARCHAR(500)    NULL,

    -- Auditoría
    fecha_creacion          DATETIME         DEFAULT GETDATE() NOT NULL,

    CONSTRAINT FK_movdet_empresa    FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_movdet_movimiento FOREIGN KEY (movimiento_id)
        REFERENCES inv_movimiento(movimiento_id) ON DELETE NO ACTION,
    CONSTRAINT FK_movdet_producto   FOREIGN KEY (producto_id)
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_movdet_um         FOREIGN KEY (unidad_medida_id)
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT FK_movdet_moneda     FOREIGN KEY (moneda_id)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION,
    CONSTRAINT FK_movdet_lote       FOREIGN KEY (lote_id)    -- [NUEVO]
        REFERENCES inv_lote(lote_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_movdet_movimiento   ON inv_movimiento_detalle(movimiento_id);
CREATE INDEX IDX_movdet_producto     ON inv_movimiento_detalle(producto_id);
CREATE INDEX IDX_movdet_lote_id      ON inv_movimiento_detalle(lote_id) WHERE lote_id IS NOT NULL;
CREATE INDEX IDX_movdet_lote         ON inv_movimiento_detalle(lote) WHERE lote IS NOT NULL;


-- ============================================================================
-- SECCIÓN C: WMS - WAREHOUSE MANAGEMENT SYSTEM (MODIFICADAS + NUEVA)
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: wms_ubicacion  [MODIFICADA]
-- Cambio: + estrategia_salida_override para sobreescribir la estrategia del
--           almacén a nivel de ubicación específica (ej: zona de cuarentena
--           siempre manual, zona de congelados siempre FEFO).
-- -----------------------------------------------------------------------------
CREATE TABLE wms_ubicacion (
    ubicacion_id            UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id              UNIQUEIDENTIFIER NOT NULL,
    empresa_id              UNIQUEIDENTIFIER NOT NULL,
    almacen_id              UNIQUEIDENTIFIER NOT NULL,
    zona_id                 UNIQUEIDENTIFIER NULL,

    -- Codificación jerárquica
    codigo_ubicacion        NVARCHAR(30)     NOT NULL,        -- Ej: "A-01-03" (Pasillo A - Rack 01 - Nivel 03)
    pasillo                 NVARCHAR(10)     NULL,             -- A, B, C
    rack                    NVARCHAR(10)     NULL,             -- 01, 02, 03
    nivel                   INT              NULL,             -- 1, 2, 3, 4
    posicion                NVARCHAR(10)     NULL,             -- A, B, C (posición en el nivel)

    -- Descripción
    nombre                  NVARCHAR(100)    NULL,

    -- Características físicas
    tipo_ubicacion          NVARCHAR(30)     DEFAULT 'rack',  -- 'rack','piso','estanteria','caja','pallet'
    capacidad_kg            DECIMAL(12,2)    NULL,
    capacidad_m3            DECIMAL(12,4)    NULL,
    capacidad_pallets       INT              NULL,
    alto_cm                 DECIMAL(10,2)    NULL,
    ancho_cm                DECIMAL(10,2)    NULL,
    profundidad_cm          DECIMAL(10,2)    NULL,

    -- Control
    permite_multiples_productos BIT          DEFAULT 1,       -- Si permite más de un producto
    permite_multiples_lotes BIT              DEFAULT 1,
    es_ubicacion_picking    BIT              DEFAULT 0,        -- Si es zona de picking

    -- Estrategia de salida (override por ubicación) [NUEVO]
    estrategia_salida_override NVARCHAR(10)  NULL,            -- [NUEVO] NULL = hereda del almacén
                                                               -- 'fifo','fefo','lefo','manual'

    -- Estado
    estado_ubicacion        NVARCHAR(20)     DEFAULT 'disponible', -- 'disponible','ocupada','bloqueada','mantenimiento'
    es_activo               BIT              DEFAULT 1 NOT NULL,

    -- Auditoría
    fecha_creacion          DATETIME         DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id     UNIQUEIDENTIFIER NULL,

    CONSTRAINT FK_ubic_empresa  FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_ubic_almacen  FOREIGN KEY (almacen_id)
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION,
    CONSTRAINT FK_ubic_zona     FOREIGN KEY (zona_id)
        REFERENCES wms_zona_almacen(zona_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_ubic_codigo   UNIQUE (cliente_id, almacen_id, codigo_ubicacion),
    CONSTRAINT CK_ubic_estrategia CHECK (
        estrategia_salida_override IS NULL OR
        estrategia_salida_override IN ('fifo','fefo','lefo','manual')
    )
);

CREATE INDEX IDX_ubic_almacen        ON wms_ubicacion(almacen_id);
CREATE INDEX IDX_ubic_zona           ON wms_ubicacion(zona_id);
CREATE INDEX IDX_ubic_picking        ON wms_ubicacion(es_ubicacion_picking);


-- -----------------------------------------------------------------------------
-- Tabla: wms_stock_ubicacion  [MODIFICADA]
-- Cambio: + lote_id FK nullable a inv_lote (reemplaza lote NVARCHAR suelto).
-- -----------------------------------------------------------------------------
CREATE TABLE wms_stock_ubicacion (
    stock_ubicacion_id      UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id              UNIQUEIDENTIFIER NOT NULL,
    empresa_id              UNIQUEIDENTIFIER NOT NULL,
    almacen_id              UNIQUEIDENTIFIER NOT NULL,
    ubicacion_id            UNIQUEIDENTIFIER NOT NULL,
    producto_id             UNIQUEIDENTIFIER NOT NULL,

    -- Cantidad
    cantidad                DECIMAL(18,4)    NOT NULL,
    unidad_medida_id        UNIQUEIDENTIFIER NOT NULL,

    -- Lote y serie
    lote_id                 UNIQUEIDENTIFIER NULL,            -- [NUEVO] FK formal a inv_lote
    lote                    NVARCHAR(50)     NULL,            -- Retrocompatibilidad / datos históricos
    numero_serie            NVARCHAR(100)    NULL,
    fecha_vencimiento       DATE             NULL,

    -- Estado del stock
    estado_stock            NVARCHAR(20)     DEFAULT 'disponible', -- 'disponible','reservado','bloqueado','cuarentena'
    motivo_bloqueo          NVARCHAR(255)    NULL,

    -- Auditoría
    fecha_ingreso           DATETIME         DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion     DATETIME         NULL,

    CONSTRAINT FK_stockubic_empresa   FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_stockubic_almacen   FOREIGN KEY (almacen_id)
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION,
    CONSTRAINT FK_stockubic_ubicacion FOREIGN KEY (ubicacion_id)
        REFERENCES wms_ubicacion(ubicacion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_stockubic_producto  FOREIGN KEY (producto_id)
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_stockubic_um        FOREIGN KEY (unidad_medida_id)
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT FK_stockubic_lote      FOREIGN KEY (lote_id)   -- [NUEVO]
        REFERENCES inv_lote(lote_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_stockubic_ubicacion  ON wms_stock_ubicacion(ubicacion_id);
CREATE INDEX IDX_stockubic_producto   ON wms_stock_ubicacion(producto_id);
CREATE INDEX IDX_stockubic_lote_id    ON wms_stock_ubicacion(lote_id) WHERE lote_id IS NOT NULL;
CREATE INDEX IDX_stockubic_lote       ON wms_stock_ubicacion(lote) WHERE lote IS NOT NULL;
CREATE INDEX IDX_stockubic_venc       ON wms_stock_ubicacion(fecha_vencimiento) WHERE fecha_vencimiento IS NOT NULL;


-- -----------------------------------------------------------------------------
-- Tabla: wms_oleada  [NUEVA]
-- Descripción: Agrupación de tareas de picking/despacho en una oleada de
--              trabajo (wave picking). Permite asignar un conjunto de tareas
--              a un turno/operario y ejecutarlas de forma eficiente.
-- Uso: Picking por lotes para múltiples pedidos en un solo recorrido.
-- Relaciones: inv_almacen, wms_tarea
-- -----------------------------------------------------------------------------
CREATE TABLE wms_oleada (
    oleada_id               UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id              UNIQUEIDENTIFIER NOT NULL,
    empresa_id              UNIQUEIDENTIFIER NOT NULL,
    almacen_id              UNIQUEIDENTIFIER NOT NULL,

    numero_oleada           NVARCHAR(20)     NOT NULL,
    tipo_oleada             NVARCHAR(30)     DEFAULT 'picking', -- 'picking','reabastecimiento','inventario'
    descripcion             NVARCHAR(255)    NULL,

    -- Asignación
    responsable_usuario_id  UNIQUEIDENTIFIER NULL,
    turno                   NVARCHAR(20)     NULL,             -- 'mañana','tarde','noche'
    fecha_programada        DATE             NOT NULL,

    -- Totales (calculados al generar la oleada)
    total_tareas            INT              DEFAULT 0,
    total_lineas            INT              DEFAULT 0,
    total_unidades          DECIMAL(18,4)    DEFAULT 0,

    -- Ejecución
    fecha_inicio_real       DATETIME         NULL,
    fecha_fin_real          DATETIME         NULL,

    -- Estado
    estado                  NVARCHAR(20)     DEFAULT 'pendiente', -- 'pendiente','en_proceso','completada','cancelada'

    -- Auditoría
    fecha_creacion          DATETIME         DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id     UNIQUEIDENTIFIER NULL,

    observaciones           NVARCHAR(500)    NULL,

    CONSTRAINT FK_oleada_empresa  FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_oleada_almacen  FOREIGN KEY (almacen_id)
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_oleada_numero   UNIQUE (cliente_id, almacen_id, numero_oleada)
);

CREATE INDEX IDX_oleada_almacen_fecha ON wms_oleada(almacen_id, fecha_programada);
CREATE INDEX IDX_oleada_estado        ON wms_oleada(estado);


-- -----------------------------------------------------------------------------
-- Tabla: wms_tarea  [MODIFICADA]
-- Cambio: + oleada_id FK nullable a wms_oleada para agrupar tareas en oleadas.
-- -----------------------------------------------------------------------------
CREATE TABLE wms_tarea (
    tarea_id                UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id              UNIQUEIDENTIFIER NOT NULL,
    empresa_id              UNIQUEIDENTIFIER NOT NULL,
    almacen_id              UNIQUEIDENTIFIER NOT NULL,

    numero_tarea            NVARCHAR(20)     NOT NULL,
    tipo_tarea              NVARCHAR(30)     NOT NULL,         -- 'picking','putaway','reabastecimiento','conteo','reubicacion'
    prioridad               INT              DEFAULT 3,        -- 1=Urgente, 2=Alta, 3=Normal, 4=Baja

    -- Oleada (agrupación de tareas) [NUEVO]
    oleada_id               UNIQUEIDENTIFIER NULL,            -- [NUEVO] FK a wms_oleada

    -- Ubicaciones
    ubicacion_origen_id     UNIQUEIDENTIFIER NULL,
    ubicacion_destino_id    UNIQUEIDENTIFIER NULL,

    -- Producto
    producto_id             UNIQUEIDENTIFIER NULL,
    cantidad_planeada       DECIMAL(18,4)    NULL,
    cantidad_completada     DECIMAL(18,4)    DEFAULT 0,
    unidad_medida_id        UNIQUEIDENTIFIER NULL,

    -- Referencia
    documento_referencia_tipo NVARCHAR(30)   NULL,            -- 'orden_venta','orden_produccion', etc.
    documento_referencia_id UNIQUEIDENTIFIER NULL,

    -- Asignación
    asignado_usuario_id     UNIQUEIDENTIFIER NULL,
    asignado_nombre         NVARCHAR(150)    NULL,
    fecha_asignacion        DATETIME         NULL,

    -- Estado
    estado                  NVARCHAR(20)     DEFAULT 'pendiente', -- 'pendiente','asignada','en_proceso','completada','cancelada'
    fecha_inicio            DATETIME         NULL,
    fecha_completado        DATETIME         NULL,

    -- Observaciones
    instrucciones           NVARCHAR(MAX)    NULL,
    observaciones           NVARCHAR(500)    NULL,

    -- Auditoría
    fecha_creacion          DATETIME         DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id     UNIQUEIDENTIFIER NULL,

    CONSTRAINT FK_tarea_empresa        FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_tarea_almacen        FOREIGN KEY (almacen_id)
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION,
    CONSTRAINT FK_tarea_ubic_origen    FOREIGN KEY (ubicacion_origen_id)
        REFERENCES wms_ubicacion(ubicacion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_tarea_ubic_destino   FOREIGN KEY (ubicacion_destino_id)
        REFERENCES wms_ubicacion(ubicacion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_tarea_producto       FOREIGN KEY (producto_id)
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_tarea_oleada         FOREIGN KEY (oleada_id)  -- [NUEVO]
        REFERENCES wms_oleada(oleada_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_tarea_numero         UNIQUE (cliente_id, almacen_id, numero_tarea)
);

CREATE INDEX IDX_tarea_almacen        ON wms_tarea(almacen_id);
CREATE INDEX IDX_tarea_oleada         ON wms_tarea(oleada_id) WHERE oleada_id IS NOT NULL;
CREATE INDEX IDX_tarea_estado         ON wms_tarea(estado);
CREATE INDEX IDX_tarea_asignado       ON wms_tarea(asignado_usuario_id) WHERE asignado_usuario_id IS NOT NULL;


-- ============================================================================
-- SECCIÓN D: QMS - QUALITY MANAGEMENT (MODIFICADAS)
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: qms_inspeccion  [MODIFICADA]
-- Cambio: + lote_id FK nullable a inv_lote.
-- -----------------------------------------------------------------------------
CREATE TABLE qms_inspeccion (
    inspeccion_id           UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id              UNIQUEIDENTIFIER NOT NULL,
    empresa_id              UNIQUEIDENTIFIER NOT NULL,

    numero_inspeccion       NVARCHAR(20)     NOT NULL,
    fecha_inspeccion        DATETIME         DEFAULT GETDATE() NOT NULL,
    plan_inspeccion_id      UNIQUEIDENTIFIER NOT NULL,

    -- Producto inspeccionado
    producto_id             UNIQUEIDENTIFIER NOT NULL,
    lote_id                 UNIQUEIDENTIFIER NULL,            -- [NUEVO] FK formal a inv_lote
    lote                    NVARCHAR(50)     NULL,            -- Retrocompatibilidad

    -- Referencia documento
    tipo_documento_origen   NVARCHAR(30)     NULL,            -- 'orden_compra','orden_produccion','movimiento_inventario'
    documento_origen_id     UNIQUEIDENTIFIER NULL,

    -- Almacén/ubicación
    almacen_id              UNIQUEIDENTIFIER NULL,
    ubicacion_almacen       NVARCHAR(50)     NULL,

    -- Cantidad inspeccionada
    cantidad_total          DECIMAL(18,4)    NOT NULL,
    cantidad_inspeccionada  DECIMAL(18,4)    NOT NULL,
    unidad_medida_id        UNIQUEIDENTIFIER NOT NULL,

    -- Resultados
    cantidad_aprobada       DECIMAL(18,4)    DEFAULT 0,
    cantidad_rechazada      DECIMAL(18,4)    DEFAULT 0,
    cantidad_observada      DECIMAL(18,4)    DEFAULT 0,       -- Con observaciones menores

    defectos_criticos       INT              DEFAULT 0,
    defectos_mayores        INT              DEFAULT 0,
    defectos_menores        INT              DEFAULT 0,

    -- Resultado final
    resultado               NVARCHAR(20)     DEFAULT 'pendiente', -- 'aprobado','rechazado','aprobado_condicional','pendiente'

    -- Inspector
    inspector_usuario_id    UNIQUEIDENTIFIER NULL,
    inspector_nombre        NVARCHAR(150)    NULL,

    -- Observaciones
    observaciones           NVARCHAR(MAX)    NULL,
    acciones_correctivas    NVARCHAR(MAX)    NULL,

    -- Aprobación
    aprobado_por_usuario_id UNIQUEIDENTIFIER NULL,
    fecha_aprobacion        DATETIME         NULL,

    -- Auditoría
    fecha_creacion          DATETIME         DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id     UNIQUEIDENTIFIER NULL,

    CONSTRAINT FK_qms_insp_empresa  FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_qms_insp_plan     FOREIGN KEY (plan_inspeccion_id)
        REFERENCES qms_plan_inspeccion(plan_inspeccion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_qms_insp_producto FOREIGN KEY (producto_id)
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_qms_insp_almacen  FOREIGN KEY (almacen_id)
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION,
    CONSTRAINT FK_qms_insp_um       FOREIGN KEY (unidad_medida_id)
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT FK_qms_insp_lote     FOREIGN KEY (lote_id)    -- [NUEVO]
        REFERENCES inv_lote(lote_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_qms_insp_numero   UNIQUE (cliente_id, empresa_id, numero_inspeccion)
);

CREATE INDEX IDX_qms_insp_empresa    ON qms_inspeccion(empresa_id, fecha_inspeccion DESC);
CREATE INDEX IDX_qms_insp_producto   ON qms_inspeccion(producto_id);
CREATE INDEX IDX_qms_insp_lote       ON qms_inspeccion(lote_id) WHERE lote_id IS NOT NULL;
CREATE INDEX IDX_qms_insp_lote_txt   ON qms_inspeccion(lote) WHERE lote IS NOT NULL;


-- -----------------------------------------------------------------------------
-- Tabla: qms_no_conformidad  [MODIFICADA]
-- Cambio: + lote_id FK nullable a inv_lote.
-- -----------------------------------------------------------------------------
CREATE TABLE qms_no_conformidad (
    no_conformidad_id       UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id              UNIQUEIDENTIFIER NOT NULL,
    empresa_id              UNIQUEIDENTIFIER NOT NULL,

    numero_nc               NVARCHAR(20)     NOT NULL,
    fecha_deteccion         DATETIME         DEFAULT GETDATE() NOT NULL,

    -- Origen
    origen                  NVARCHAR(30)     NOT NULL,        -- 'inspeccion','reclamo_cliente','auditoria','proceso'
    inspeccion_id           UNIQUEIDENTIFIER NULL,            -- Si se origina de inspección
    documento_referencia    NVARCHAR(50)     NULL,

    -- Producto afectado
    producto_id             UNIQUEIDENTIFIER NULL,
    lote_id                 UNIQUEIDENTIFIER NULL,            -- [NUEVO] FK formal a inv_lote
    lote                    NVARCHAR(50)     NULL,            -- Retrocompatibilidad
    cantidad_afectada       DECIMAL(18,4)    NULL,

    -- Descripción
    descripcion_nc          NVARCHAR(MAX)    NOT NULL,        -- Descripción de la no conformidad
    tipo_nc                 NVARCHAR(30)     NOT NULL,        -- 'critica','mayor','menor'

    -- Responsables
    area_responsable        NVARCHAR(100)    NULL,
    responsable_usuario_id  UNIQUEIDENTIFIER NULL,

    -- Análisis de causa raíz
    analisis_causa_raiz     NVARCHAR(MAX)    NULL,            -- 5 Porqués, Ishikawa, etc.
    causa_raiz_identificada NVARCHAR(500)    NULL,

    -- Acciones (CAPA completo)
    accion_inmediata        NVARCHAR(MAX)    NULL,            -- Acción de contención
    accion_correctiva       NVARCHAR(MAX)    NULL,            -- Acción correctiva
    accion_preventiva       NVARCHAR(MAX)    NULL,            -- Acción preventiva

    responsable_accion_usuario_id UNIQUEIDENTIFIER NULL,
    fecha_compromiso_cierre DATE             NULL,

    -- Estado y cierre
    estado                  NVARCHAR(20)     DEFAULT 'abierta', -- 'abierta','en_analisis','en_accion','cerrada','cancelada'
    fecha_cierre            DATETIME         NULL,
    cerrado_por_usuario_id  UNIQUEIDENTIFIER NULL,
    verificacion_eficacia   NVARCHAR(MAX)    NULL,            -- Verificación de que la acción funcionó

    -- Auditoría
    fecha_creacion          DATETIME         DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id     UNIQUEIDENTIFIER NULL,

    CONSTRAINT FK_qms_nc_empresa  FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_qms_nc_insp     FOREIGN KEY (inspeccion_id)
        REFERENCES qms_inspeccion(inspeccion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_qms_nc_producto FOREIGN KEY (producto_id)
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_qms_nc_lote     FOREIGN KEY (lote_id)      -- [NUEVO]
        REFERENCES inv_lote(lote_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_qms_nc_numero   UNIQUE (cliente_id, empresa_id, numero_nc)
);

CREATE INDEX IDX_qms_nc_empresa      ON qms_no_conformidad(empresa_id, fecha_deteccion DESC);
CREATE INDEX IDX_qms_nc_estado       ON qms_no_conformidad(estado, fecha_deteccion DESC);
CREATE INDEX IDX_qms_nc_tipo         ON qms_no_conformidad(tipo_nc);
CREATE INDEX IDX_qms_nc_producto     ON qms_no_conformidad(producto_id) WHERE producto_id IS NOT NULL;
CREATE INDEX IDX_qms_nc_lote         ON qms_no_conformidad(lote_id) WHERE lote_id IS NOT NULL;


-- ============================================================================
-- SECCIÓN E: PUR - COMPRAS (MODIFICADA)
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: pur_recepcion_detalle  [MODIFICADA]
-- Cambio: + lote_id FK nullable a inv_lote. La recepción de compra es el
--           punto de entrada donde normalmente se crea el lote en inv_lote.
-- -----------------------------------------------------------------------------
CREATE TABLE pur_recepcion_detalle (
    recepcion_detalle_id    UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id              UNIQUEIDENTIFIER NOT NULL,
    empresa_id              UNIQUEIDENTIFIER NOT NULL,
    recepcion_id            UNIQUEIDENTIFIER NOT NULL,
    orden_compra_detalle_id UNIQUEIDENTIFIER NOT NULL,
    producto_id             UNIQUEIDENTIFIER NOT NULL,

    -- Cantidad
    cantidad_ordenada       DECIMAL(18,4)    NOT NULL,        -- Según OC
    cantidad_recepcionada   DECIMAL(18,4)    NOT NULL,        -- Real recibida
    diferencia              AS (cantidad_recepcionada - cantidad_ordenada) PERSISTED,
    unidad_medida_id        UNIQUEIDENTIFIER NOT NULL,

    -- Lote y vencimiento
    lote_id                 UNIQUEIDENTIFIER NULL,            -- [NUEVO] FK formal a inv_lote
    lote                    NVARCHAR(50)     NULL,            -- Retrocompatibilidad
    fecha_vencimiento       DATE             NULL,

    -- Costeo
    precio_unitario         DECIMAL(18,4)    DEFAULT 0,
    total                   AS (cantidad_recepcionada * precio_unitario) PERSISTED,

    -- Ubicación
    ubicacion_almacen       NVARCHAR(50)     NULL,

    -- Observaciones
    observaciones           NVARCHAR(500)    NULL,
    motivo_diferencia       NVARCHAR(255)    NULL,

    -- Auditoría
    fecha_creacion          DATETIME         DEFAULT GETDATE() NOT NULL,

    CONSTRAINT FK_recepdet_empresa  FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_recepdet_recepcion FOREIGN KEY (recepcion_id)
        REFERENCES pur_recepcion(recepcion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_recepdet_ocdet    FOREIGN KEY (orden_compra_detalle_id)
        REFERENCES pur_orden_compra_detalle(orden_compra_detalle_id) ON DELETE NO ACTION,
    CONSTRAINT FK_recepdet_producto FOREIGN KEY (producto_id)
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_recepdet_um       FOREIGN KEY (unidad_medida_id)
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT FK_recepdet_lote     FOREIGN KEY (lote_id)    -- [NUEVO]
        REFERENCES inv_lote(lote_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_recepdet_recepcion   ON pur_recepcion_detalle(recepcion_id);
CREATE INDEX IDX_recepdet_producto    ON pur_recepcion_detalle(producto_id);
CREATE INDEX IDX_recepdet_lote        ON pur_recepcion_detalle(lote_id) WHERE lote_id IS NOT NULL;


-- ============================================================================
-- SECCIÓN F: MFG - MANUFACTURA (MODIFICADA + NUEVA)
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: mfg_consumo_materiales  [MODIFICADA]
-- Cambio: + lote_id FK nullable a inv_lote para trazabilidad completa de
--           qué lote de material fue consumido en qué orden de producción.
-- -----------------------------------------------------------------------------
CREATE TABLE mfg_consumo_materiales (
    consumo_id              UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id              UNIQUEIDENTIFIER NOT NULL,
    empresa_id              UNIQUEIDENTIFIER NOT NULL,
    orden_produccion_id     UNIQUEIDENTIFIER NOT NULL,
    producto_id             UNIQUEIDENTIFIER NOT NULL,        -- Material consumido

    -- Cantidad
    cantidad_planificada    DECIMAL(18,4)    NOT NULL,        -- Según BOM
    cantidad_consumida      DECIMAL(18,4)    NOT NULL,        -- Real consumido
    diferencia              AS (cantidad_consumida - cantidad_planificada) PERSISTED,
    unidad_medida_id        UNIQUEIDENTIFIER NOT NULL,

    -- Lote y trazabilidad
    lote_id                 UNIQUEIDENTIFIER NULL,            -- [NUEVO] FK formal a inv_lote
    lote                    NVARCHAR(50)     NULL,            -- Retrocompatibilidad
    almacen_origen_id       UNIQUEIDENTIFIER NULL,

    -- Costo
    costo_unitario          DECIMAL(18,4)    DEFAULT 0,
    costo_total             AS (cantidad_consumida * costo_unitario) PERSISTED,

    -- Movimiento de inventario asociado
    movimiento_inventario_id UNIQUEIDENTIFIER NULL,

    -- Observaciones
    observaciones           NVARCHAR(500)    NULL,

    -- Auditoría
    fecha_consumo           DATETIME         DEFAULT GETDATE() NOT NULL,
    usuario_registro_id     UNIQUEIDENTIFIER NULL,

    CONSTRAINT FK_consumo_empresa   FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_consumo_op        FOREIGN KEY (orden_produccion_id)
        REFERENCES mfg_orden_produccion(orden_produccion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_consumo_producto  FOREIGN KEY (producto_id)
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_consumo_almacen   FOREIGN KEY (almacen_origen_id)
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION,
    CONSTRAINT FK_consumo_um        FOREIGN KEY (unidad_medida_id)
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT FK_consumo_lote      FOREIGN KEY (lote_id)    -- [NUEVO]
        REFERENCES inv_lote(lote_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_consumo_op           ON mfg_consumo_materiales(orden_produccion_id);
CREATE INDEX IDX_consumo_producto     ON mfg_consumo_materiales(producto_id);
CREATE INDEX IDX_consumo_lote         ON mfg_consumo_materiales(lote_id) WHERE lote_id IS NOT NULL;


-- -----------------------------------------------------------------------------
-- Tabla: mfg_calendario_capacidad  [NUEVA]
-- Descripción: Capacidad disponible planificada por centro de trabajo y día.
--              Considera turnos, mantenimientos programados y feriados.
--              Es la base para que APS haga scheduling con capacidad finita.
-- Uso: PLN/APS consulta esta tabla para no sobre-cargar máquinas/centros.
-- Relaciones: mfg_centro_trabajo
-- -----------------------------------------------------------------------------
CREATE TABLE mfg_calendario_capacidad (
    calendario_id           UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id              UNIQUEIDENTIFIER NOT NULL,
    empresa_id              UNIQUEIDENTIFIER NOT NULL,
    centro_trabajo_id       UNIQUEIDENTIFIER NOT NULL,

    fecha                   DATE             NOT NULL,
    turno                   NVARCHAR(20)     DEFAULT 'dia',   -- 'dia','tarde','noche','completo'

    -- Capacidad planificada
    horas_disponibles       DECIMAL(8,2)     NOT NULL,        -- Horas productivas disponibles
    horas_planificadas      DECIMAL(8,2)     DEFAULT 0,       -- Horas ya asignadas a OPs
    horas_reserva           DECIMAL(8,2)     DEFAULT 0,       -- Colchón para imprevistos
    horas_disponibles_netas AS (
        CASE WHEN horas_disponibles - horas_planificadas - horas_reserva > 0
             THEN horas_disponibles - horas_planificadas - horas_reserva
             ELSE 0 END
    ) PERSISTED,

    porcentaje_carga        AS (
        CASE WHEN horas_disponibles > 0
             THEN (horas_planificadas / horas_disponibles) * 100
             ELSE 0 END
    ) PERSISTED,

    -- Tipo de día
    tipo_dia                NVARCHAR(20)     DEFAULT 'laborable', -- 'laborable','feriado','mantenimiento','parada_programada'
    motivo_no_laborable     NVARCHAR(100)    NULL,

    -- Auditoría
    fecha_creacion          DATETIME         DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id     UNIQUEIDENTIFIER NULL,

    CONSTRAINT FK_cal_empresa     FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cal_ct          FOREIGN KEY (centro_trabajo_id)
        REFERENCES mfg_centro_trabajo(centro_trabajo_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_cal_ct_fecha    UNIQUE (cliente_id, centro_trabajo_id, fecha, turno)
);

CREATE INDEX IDX_cal_ct_fecha         ON mfg_calendario_capacidad(centro_trabajo_id, fecha);
CREATE INDEX IDX_cal_empresa_fecha    ON mfg_calendario_capacidad(empresa_id, fecha);
CREATE INDEX IDX_cal_carga            ON mfg_calendario_capacidad(porcentaje_carga);


-- ============================================================================
-- SECCIÓN G: MES - MANUFACTURING EXECUTION SYSTEM
-- ============================================================================
-- DESCRIPCIÓN: Captura de lo que realmente pasa en el piso de producción.
--              Complementa MFG (planificación) con la ejecución real.
--              Aplica a cualquier industria manufacturera — es 100% Core.
-- DEPENDENCIAS: MFG
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: mes_ejecucion_operacion  [NUEVA]
-- Descripción: Registro real de ejecución de cada operación de una OP.
--              Puede haber múltiples registros por operación (pausas, reanudaciones).
-- Uso: OEE, eficiencia por operario, tiempo real vs. planificado.
-- Relaciones: mfg_orden_produccion_operacion, hcm_empleado
-- -----------------------------------------------------------------------------
CREATE TABLE mes_ejecucion_operacion (
    ejecucion_id            UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id              UNIQUEIDENTIFIER NOT NULL,
    empresa_id              UNIQUEIDENTIFIER NOT NULL,
    op_operacion_id         UNIQUEIDENTIFIER NOT NULL,        -- mfg_orden_produccion_operacion

    -- Operario que ejecutó
    operario_usuario_id     UNIQUEIDENTIFIER NULL,
    operario_nombre         NVARCHAR(150)    NULL,

    -- Tiempos reales
    fecha_inicio            DATETIME         NOT NULL,
    fecha_fin               DATETIME         NULL,
    duracion_minutos        AS (
        CASE WHEN fecha_fin IS NOT NULL
             THEN DATEDIFF(MINUTE, fecha_inicio, fecha_fin)
             ELSE NULL END
    ) PERSISTED,

    -- Producción real en este tramo
    cantidad_producida      DECIMAL(18,4)    DEFAULT 0,
    cantidad_aprobada       DECIMAL(18,4)    DEFAULT 0,
    cantidad_rechazada      DECIMAL(18,4)    DEFAULT 0,
    unidad_medida_id        UNIQUEIDENTIFIER NULL,

    -- Tipo de registro
    tipo_evento             NVARCHAR(20)     DEFAULT 'produccion', -- 'produccion','setup','pausa','reanudacion','cierre'

    -- Estado
    estado                  NVARCHAR(20)     DEFAULT 'en_curso',   -- 'en_curso','completado','anulado'

    -- Auditoría
    fecha_creacion          DATETIME         DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id     UNIQUEIDENTIFIER NULL,

    observaciones           NVARCHAR(500)    NULL,

    CONSTRAINT FK_mesejec_empresa    FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_mesejec_opoper     FOREIGN KEY (op_operacion_id)
        REFERENCES mfg_orden_produccion_operacion(op_operacion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_mesejec_um         FOREIGN KEY (unidad_medida_id)
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_mesejec_opoper       ON mes_ejecucion_operacion(op_operacion_id);
CREATE INDEX IDX_mesejec_operario     ON mes_ejecucion_operacion(operario_usuario_id) WHERE operario_usuario_id IS NOT NULL;
CREATE INDEX IDX_mesejec_fecha        ON mes_ejecucion_operacion(fecha_inicio);
CREATE INDEX IDX_mesejec_estado       ON mes_ejecucion_operacion(estado);


-- -----------------------------------------------------------------------------
-- Tabla: mes_parada_maquina  [NUEVA]
-- Descripción: Registro de paradas no planificadas de un centro de trabajo.
--              Con causa categorizada para análisis OEE (disponibilidad).
-- Uso: OEE, análisis de causas de parada, mantenimiento predictivo.
-- Relaciones: mfg_centro_trabajo, mfg_orden_produccion_operacion
-- -----------------------------------------------------------------------------
CREATE TABLE mes_parada_maquina (
    parada_id               UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id              UNIQUEIDENTIFIER NOT NULL,
    empresa_id              UNIQUEIDENTIFIER NOT NULL,
    centro_trabajo_id       UNIQUEIDENTIFIER NOT NULL,
    op_operacion_id         UNIQUEIDENTIFIER NULL,            -- OP que estaba corriendo (si aplica)

    -- Tiempos
    fecha_inicio            DATETIME         NOT NULL,
    fecha_fin               DATETIME         NULL,
    duracion_minutos        AS (
        CASE WHEN fecha_fin IS NOT NULL
             THEN DATEDIFF(MINUTE, fecha_inicio, fecha_fin)
             ELSE NULL END
    ) PERSISTED,

    -- Categorización (base para OEE)
    categoria               NVARCHAR(30)     NOT NULL,        -- 'falla_equipo','mantenimiento','falta_material',
                                                               -- 'falta_operario','cambio_producto','calidad','setup',
                                                               -- 'fuerza_mayor','programada'
    causa_descripcion       NVARCHAR(255)    NULL,
    requiere_mantenimiento  BIT              DEFAULT 0,
    orden_trabajo_id        UNIQUEIDENTIFIER NULL,            -- FK a mnt_orden_trabajo si genera OT

    -- Responsable del reporte
    reportado_por_usuario_id UNIQUEIDENTIFIER NULL,

    -- Estado
    estado                  NVARCHAR(20)     DEFAULT 'abierta', -- 'abierta','cerrada'

    -- Auditoría
    fecha_creacion          DATETIME         DEFAULT GETDATE() NOT NULL,

    observaciones           NVARCHAR(500)    NULL,

    CONSTRAINT FK_parada_empresa    FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_parada_ct         FOREIGN KEY (centro_trabajo_id)
        REFERENCES mfg_centro_trabajo(centro_trabajo_id) ON DELETE NO ACTION,
    CONSTRAINT FK_parada_opoper     FOREIGN KEY (op_operacion_id)
        REFERENCES mfg_orden_produccion_operacion(op_operacion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_parada_ot         FOREIGN KEY (orden_trabajo_id)
        REFERENCES mnt_orden_trabajo(orden_trabajo_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_parada_ct_fecha      ON mes_parada_maquina(centro_trabajo_id, fecha_inicio);
CREATE INDEX IDX_parada_categoria     ON mes_parada_maquina(categoria);
CREATE INDEX IDX_parada_estado        ON mes_parada_maquina(estado);


-- ============================================================================
-- SECCIÓN H: APS - ADVANCED PLANNING & SCHEDULING
-- ============================================================================
-- DESCRIPCIÓN: Motor de programación detallada con restricciones de capacidad
--              finita. Responde preguntas como "¿qué pasa si atraso esta OP?",
--              permite simular escenarios antes de comprometer cambios, y
--              propaga impactos automáticamente a toda la cadena.
--              Aplica a cualquier industria manufacturera — es 100% Core.
-- DEPENDENCIAS: MFG, MES, PLN (MRP/MPS)
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: aps_escenario  [NUEVA]
-- Descripción: Escenario de simulación de programación. Permite explorar
--              "¿qué pasa si...?" antes de comprometer cambios al plan real.
--              El escenario 'base' es el plan activo; los demás son simulaciones.
-- Uso: Simular atraso de una OP, cambio de prioridad, falla de máquina, etc.
-- Relaciones: org_empresa
-- -----------------------------------------------------------------------------
CREATE TABLE aps_escenario (
    escenario_id            UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id              UNIQUEIDENTIFIER NOT NULL,
    empresa_id              UNIQUEIDENTIFIER NOT NULL,

    codigo                  NVARCHAR(20)     NOT NULL,
    nombre                  NVARCHAR(100)    NOT NULL,
    descripcion             NVARCHAR(500)    NULL,

    tipo                    NVARCHAR(20)     DEFAULT 'simulacion', -- 'base','simulacion','aprobado'
                                                               -- 'base' = plan vigente
                                                               -- 'simulacion' = borrador de evaluación
                                                               -- 'aprobado' = se convierte en nuevo 'base'

    -- Si es una simulación, a partir de qué escenario se creó
    escenario_padre_id      UNIQUEIDENTIFIER NULL,

    -- Horizonte del escenario
    fecha_inicio_horizonte  DATE             NOT NULL,
    fecha_fin_horizonte     DATE             NOT NULL,

    -- Resultado del cálculo
    fecha_calculo           DATETIME         NULL,
    estado_calculo          NVARCHAR(20)     DEFAULT 'pendiente', -- 'pendiente','calculando','calculado','error'
    mensaje_calculo         NVARCHAR(500)    NULL,

    -- Métricas del escenario (resumen del resultado)
    ops_en_tiempo           INT              DEFAULT 0,        -- OPs que cumplen su fecha compromiso
    ops_atrasadas           INT              DEFAULT 0,
    utilizacion_promedio_pct DECIMAL(5,2)    DEFAULT 0,       -- % utilización promedio de centros de trabajo

    -- Estado
    estado                  NVARCHAR(20)     DEFAULT 'activo', -- 'activo','archivado','descartado'
    es_plan_activo          BIT              DEFAULT 0,        -- Solo uno puede ser 1 a la vez

    -- Auditoría
    fecha_creacion          DATETIME         DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id     UNIQUEIDENTIFIER NULL,

    observaciones           NVARCHAR(MAX)    NULL,

    CONSTRAINT FK_apsesc_empresa  FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_apsesc_padre    FOREIGN KEY (escenario_padre_id)
        REFERENCES aps_escenario(escenario_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_apsesc_codigo   UNIQUE (cliente_id, empresa_id, codigo)
);

CREATE INDEX IDX_apsesc_empresa       ON aps_escenario(empresa_id);
CREATE INDEX IDX_apsesc_tipo          ON aps_escenario(tipo);
CREATE INDEX IDX_apsesc_activo        ON aps_escenario(es_plan_activo);


-- -----------------------------------------------------------------------------
-- Tabla: aps_carga_centro_trabajo  [NUEVA]
-- Descripción: Carga planificada de un centro de trabajo en un escenario y
--              horizonte dado. Resultado del cálculo APS: cuántas horas ocupadas
--              vs. disponibles tiene cada máquina por día/turno.
-- Uso: Detectar cuellos de botella, sobre-carga, slots libres para insertar OPs.
-- Relaciones: aps_escenario, mfg_centro_trabajo, mfg_calendario_capacidad
-- -----------------------------------------------------------------------------
CREATE TABLE aps_carga_centro_trabajo (
    carga_id                UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id              UNIQUEIDENTIFIER NOT NULL,
    empresa_id              UNIQUEIDENTIFIER NOT NULL,
    escenario_id            UNIQUEIDENTIFIER NOT NULL,
    centro_trabajo_id       UNIQUEIDENTIFIER NOT NULL,

    fecha                   DATE             NOT NULL,
    turno                   NVARCHAR(20)     DEFAULT 'dia',

    -- Carga calculada
    horas_disponibles       DECIMAL(8,2)     NOT NULL,
    horas_cargadas          DECIMAL(8,2)     DEFAULT 0,
    horas_libres            AS (
        CASE WHEN horas_disponibles - horas_cargadas > 0
             THEN horas_disponibles - horas_cargadas
             ELSE 0 END
    ) PERSISTED,
    porcentaje_utilizacion  AS (
        CASE WHEN horas_disponibles > 0
             THEN (horas_cargadas / horas_disponibles) * 100
             ELSE 0 END
    ) PERSISTED,

    es_cuello_botella       BIT              DEFAULT 0,       -- TRUE si porcentaje_utilizacion > umbral configurado

    -- Auditoría
    fecha_creacion          DATETIME         DEFAULT GETDATE() NOT NULL,

    CONSTRAINT FK_apscarga_empresa  FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_apscarga_esc      FOREIGN KEY (escenario_id)
        REFERENCES aps_escenario(escenario_id) ON DELETE NO ACTION,
    CONSTRAINT FK_apscarga_ct       FOREIGN KEY (centro_trabajo_id)
        REFERENCES mfg_centro_trabajo(centro_trabajo_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_apscarga          UNIQUE (escenario_id, centro_trabajo_id, fecha, turno)
);

CREATE INDEX IDX_apscarga_esc_ct      ON aps_carga_centro_trabajo(escenario_id, centro_trabajo_id);
CREATE INDEX IDX_apscarga_fecha       ON aps_carga_centro_trabajo(fecha);
CREATE INDEX IDX_apscarga_cuello      ON aps_carga_centro_trabajo(es_cuello_botella) WHERE es_cuello_botella = 1;


-- -----------------------------------------------------------------------------
-- Tabla: aps_secuencia_operacion  [NUEVA]
-- Descripción: Programación detallada de cada operación de cada OP en un
--              escenario APS. Define cuándo exactamente empieza y termina
--              cada operación en cada máquina.
-- Uso: Gantt de producción, detección de conflictos, propagación de atrasos.
-- Relaciones: aps_escenario, mfg_orden_produccion_operacion, mfg_centro_trabajo
-- -----------------------------------------------------------------------------
CREATE TABLE aps_secuencia_operacion (
    secuencia_id            UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id              UNIQUEIDENTIFIER NOT NULL,
    empresa_id              UNIQUEIDENTIFIER NOT NULL,
    escenario_id            UNIQUEIDENTIFIER NOT NULL,
    op_operacion_id         UNIQUEIDENTIFIER NOT NULL,        -- mfg_orden_produccion_operacion
    centro_trabajo_id       UNIQUEIDENTIFIER NOT NULL,

    -- Programación calculada por APS
    fecha_inicio_aps        DATETIME         NOT NULL,        -- Inicio calculado
    fecha_fin_aps           DATETIME         NOT NULL,        -- Fin calculado
    duracion_minutos        AS (DATEDIFF(MINUTE, fecha_inicio_aps, fecha_fin_aps)) PERSISTED,

    -- Comparación vs. plan original
    fecha_inicio_original   DATETIME         NULL,            -- Fecha planificada original
    fecha_fin_original      DATETIME         NULL,
    dias_atraso             AS (
        CASE WHEN fecha_fin_aps > fecha_fin_original AND fecha_fin_original IS NOT NULL
             THEN DATEDIFF(DAY, fecha_fin_original, fecha_fin_aps)
             ELSE 0 END
    ) PERSISTED,

    -- Prioridad en la cola de la máquina
    prioridad_secuencia     INT              DEFAULT 50,      -- 1=más urgente, 100=menos urgente
    es_critica              BIT              DEFAULT 0,        -- Si es operación en ruta crítica

    -- Estado
    estado                  NVARCHAR(20)     DEFAULT 'programada', -- 'programada','confirmada','ejecutando','completada'

    -- Auditoría
    fecha_creacion          DATETIME         DEFAULT GETDATE() NOT NULL,

    CONSTRAINT FK_apssec_empresa  FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_apssec_esc      FOREIGN KEY (escenario_id)
        REFERENCES aps_escenario(escenario_id) ON DELETE NO ACTION,
    CONSTRAINT FK_apssec_opoper   FOREIGN KEY (op_operacion_id)
        REFERENCES mfg_orden_produccion_operacion(op_operacion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_apssec_ct       FOREIGN KEY (centro_trabajo_id)
        REFERENCES mfg_centro_trabajo(centro_trabajo_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_apssec_esc_ct        ON aps_secuencia_operacion(escenario_id, centro_trabajo_id);
CREATE INDEX IDX_apssec_opoper        ON aps_secuencia_operacion(op_operacion_id);
CREATE INDEX IDX_apssec_fecha         ON aps_secuencia_operacion(fecha_inicio_aps);
CREATE INDEX IDX_apssec_critica       ON aps_secuencia_operacion(es_critica) WHERE es_critica = 1;
CREATE INDEX IDX_apssec_atraso        ON aps_secuencia_operacion(dias_atraso) WHERE dias_atraso > 0;


-- -----------------------------------------------------------------------------
-- Tabla: aps_simulacion_impacto  [NUEVA]
-- Descripción: Resultado de simular un cambio puntual: "¿qué pasa si atraso
--              la OP-X 3 días?" -> esta tabla registra todas las OPs/despachos
--              impactados en cadena, con su nuevo estado calculado.
-- Uso: Presentar al planificador el impacto completo ANTES de confirmar el cambio.
-- Relaciones: aps_escenario
-- -----------------------------------------------------------------------------
CREATE TABLE aps_simulacion_impacto (
    impacto_id              UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id              UNIQUEIDENTIFIER NOT NULL,
    empresa_id              UNIQUEIDENTIFIER NOT NULL,
    escenario_id            UNIQUEIDENTIFIER NOT NULL,

    -- Entidad impactada
    entidad_tipo            NVARCHAR(30)     NOT NULL,        -- 'orden_produccion','pedido_venta',
                                                               -- 'despacho','compra_sugerida'
    entidad_id              UNIQUEIDENTIFIER NOT NULL,
    entidad_codigo          NVARCHAR(50)     NULL,            -- Número legible de la entidad

    -- Impacto calculado
    fecha_compromiso_original DATE           NULL,            -- Fecha prometida antes del cambio
    fecha_nueva_estimada    DATE             NULL,            -- Fecha estimada con el cambio
    dias_impacto            INT              DEFAULT 0,       -- Positivo = atraso, negativo = adelanto
    tipo_impacto            NVARCHAR(20)     NULL,            -- 'atraso','adelanto','sin_cambio','cancelacion'

    -- Gravedad
    nivel_criticidad        NVARCHAR(10)     DEFAULT 'medio', -- 'alto','medio','bajo'
    cliente_afectado_id     UNIQUEIDENTIFIER NULL,            -- Si impacta un pedido de cliente

    -- Auditoría
    fecha_creacion          DATETIME         DEFAULT GETDATE() NOT NULL,

    CONSTRAINT FK_apsimx_empresa FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_apsimx_esc     FOREIGN KEY (escenario_id)
        REFERENCES aps_escenario(escenario_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_apsimx_esc           ON aps_simulacion_impacto(escenario_id);
CREATE INDEX IDX_apsimx_entidad       ON aps_simulacion_impacto(entidad_tipo, entidad_id);
CREATE INDEX IDX_apsimx_criticidad    ON aps_simulacion_impacto(nivel_criticidad);


-- ============================================================================
-- SECCIÓN I: ALR - MOTOR DE ALERTAS
-- ============================================================================
-- DESCRIPCIÓN: Motor genérico de alertas y notificaciones. Una sola definición
--              de regla puede disparar alertas para stock bajo, OPs atrasadas,
--              lotes por vencer, pagos pendientes — cualquier módulo.
--              Evita que cada módulo implemente sus propias alertas inconsistentes.
-- DEPENDENCIAS: ORG (las reglas se configuran por empresa)
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: alr_regla_alerta  [NUEVA]
-- Descripción: Definición de una regla de alerta: qué monitorear, bajo qué
--              condición dispararla y a quién notificar.
-- Uso: Configuración de umbrales por cliente sin tocar código.
-- Relaciones: org_empresa
-- -----------------------------------------------------------------------------
CREATE TABLE alr_regla_alerta (
    regla_id                UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id              UNIQUEIDENTIFIER NOT NULL,
    empresa_id              UNIQUEIDENTIFIER NOT NULL,

    codigo                  NVARCHAR(30)     NOT NULL,
    nombre                  NVARCHAR(100)    NOT NULL,
    descripcion             NVARCHAR(500)    NULL,

    -- Qué monitorear
    modulo                  NVARCHAR(10)     NOT NULL,        -- 'INV','MFG','PUR','SLS','FIN','QMS','MES','APS'
    entidad                 NVARCHAR(50)     NOT NULL,        -- Nombre de la tabla/entidad a monitorear
    campo_evaluado          NVARCHAR(100)    NULL,            -- Campo que se evalúa (ej: 'cantidad_disponible')

    -- Condición de disparo
    tipo_condicion          NVARCHAR(20)     NOT NULL,        -- 'menor_que','mayor_que','igual_a',
                                                               -- 'porcentaje_menor','dias_para_fecha',
                                                               -- 'estado_es','sin_movimiento_dias'
    umbral_valor            DECIMAL(18,4)    NULL,            -- Valor numérico del umbral
    umbral_texto            NVARCHAR(100)    NULL,            -- Valor texto (para tipo_condicion='estado_es')

    -- Severidad
    severidad               NVARCHAR(10)     DEFAULT 'media', -- 'critica','alta','media','baja'
                                                               -- 'critica' = bloquea operación (ej: stock negativo)
                                                               -- 'alta' = requiere acción inmediata
                                                               -- 'media' = revisar en el día
                                                               -- 'baja' = informativa

    -- Canal de notificación (JSON: {"email":true,"inapp":true,"sms":false,"webhook":"url"})
    canales_notificacion    NVARCHAR(500)    NULL,

    -- Destinatarios (JSON: ["rol:gerente_produccion","usuario_id:xxx","email:x@y.com"])
    destinatarios           NVARCHAR(MAX)    NULL,

    -- Frecuencia de re-notificación
    renotificar_cada_minutos INT             NULL,            -- NULL = notifica solo 1 vez hasta que se resuelva

    -- Estado
    es_activo               BIT              DEFAULT 1 NOT NULL,
    fecha_creacion          DATETIME         DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id     UNIQUEIDENTIFIER NULL,

    observaciones           NVARCHAR(500)    NULL,

    CONSTRAINT FK_alrregla_empresa FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_alrregla_codigo  UNIQUE (cliente_id, empresa_id, codigo)
);

CREATE INDEX IDX_alrregla_empresa     ON alr_regla_alerta(empresa_id);
CREATE INDEX IDX_alrregla_modulo      ON alr_regla_alerta(modulo);
CREATE INDEX IDX_alrregla_activo      ON alr_regla_alerta(es_activo);


-- -----------------------------------------------------------------------------
-- Tabla: alr_alerta_generada  [NUEVA]
-- Descripción: Evento de alerta disparado cuando una regla se cumple.
--              Registro histórico de todas las alertas generadas.
-- Uso: Bandeja de alertas del usuario, histórico, análisis de recurrencia.
-- Relaciones: alr_regla_alerta
-- -----------------------------------------------------------------------------
CREATE TABLE alr_alerta_generada (
    alerta_id               UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id              UNIQUEIDENTIFIER NOT NULL,
    empresa_id              UNIQUEIDENTIFIER NOT NULL,
    regla_id                UNIQUEIDENTIFIER NOT NULL,

    -- Contexto de la alerta
    entidad_tipo            NVARCHAR(50)     NULL,            -- Tabla que generó la alerta
    entidad_id              UNIQUEIDENTIFIER NULL,            -- ID del registro que la generó
    entidad_descripcion     NVARCHAR(255)    NULL,            -- Descripción legible (ej: "Producto HILO-001")

    -- Mensaje
    titulo                  NVARCHAR(200)    NOT NULL,
    mensaje                 NVARCHAR(MAX)    NOT NULL,
    valor_detectado         NVARCHAR(100)    NULL,            -- Valor que disparó la alerta (ej: "stock = 5")
    severidad               NVARCHAR(10)     NOT NULL,        -- Heredada de la regla al momento de disparar

    -- Estado
    estado                  NVARCHAR(20)     DEFAULT 'pendiente', -- 'pendiente','leida','atendida','descartada'
    fecha_generacion        DATETIME         DEFAULT GETDATE() NOT NULL,
    fecha_lectura           DATETIME         NULL,
    leida_por_usuario_id    UNIQUEIDENTIFIER NULL,
    fecha_atencion          DATETIME         NULL,
    atendida_por_usuario_id UNIQUEIDENTIFIER NULL,
    nota_atencion           NVARCHAR(500)    NULL,

    -- Control de re-notificación
    notificaciones_enviadas INT              DEFAULT 1,
    fecha_ultima_notificacion DATETIME       NULL,

    CONSTRAINT FK_alrgen_empresa FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_alrgen_regla   FOREIGN KEY (regla_id)
        REFERENCES alr_regla_alerta(regla_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_alrgen_empresa_estado ON alr_alerta_generada(empresa_id, estado, fecha_generacion DESC);
CREATE INDEX IDX_alrgen_regla          ON alr_alerta_generada(regla_id);
CREATE INDEX IDX_alrgen_entidad        ON alr_alerta_generada(entidad_tipo, entidad_id) WHERE entidad_id IS NOT NULL;
CREATE INDEX IDX_alrgen_severidad      ON alr_alerta_generada(severidad, estado);


-- ============================================================================
-- SECCIÓN J: FACTURACIÓN (MODIFICADA)
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: invbill_comprobante_detalle  [MODIFICADA]
-- Cambio: + lote_id FK nullable a inv_lote para trazabilidad en factura.
-- -----------------------------------------------------------------------------
CREATE TABLE invbill_comprobante_detalle (
    comprobante_detalle_id  UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id              UNIQUEIDENTIFIER NOT NULL,
    empresa_id              UNIQUEIDENTIFIER NOT NULL,
    comprobante_id          UNIQUEIDENTIFIER NOT NULL,

    item                    INT              NOT NULL,
    producto_id             UNIQUEIDENTIFIER NULL,
    codigo_producto         NVARCHAR(50)     NULL,
    descripcion             NVARCHAR(500)    NOT NULL,

    -- Cantidad
    cantidad                DECIMAL(18,4)    NOT NULL,
    unidad_medida_codigo    NVARCHAR(10)     NOT NULL,        -- Código SUNAT (NIU, ZZ, etc.)
    unidad_medida_id        UNIQUEIDENTIFIER NULL,

    -- Precios
    precio_unitario         DECIMAL(18,4)    NOT NULL,
    descuento_unitario      DECIMAL(18,4)    DEFAULT 0,
    precio_venta_unitario   AS (precio_unitario - descuento_unitario) PERSISTED,

    -- Totales
    valor_venta             AS (cantidad * (precio_unitario - descuento_unitario)) PERSISTED,

    -- Tributos
    tipo_afectacion_igv     NVARCHAR(2)      NOT NULL,        -- '10'=Gravado, '20'=Exonerado, etc.
    porcentaje_igv          DECIMAL(5,2)     DEFAULT 18,
    igv                     AS (
        CASE
            WHEN tipo_afectacion_igv = '10'
            THEN cantidad * (precio_unitario - descuento_unitario) * (porcentaje_igv / 100)
            ELSE 0
        END
    ) PERSISTED,
    total_item              AS (
        cantidad * (precio_unitario - descuento_unitario) *
        (1 + CASE WHEN tipo_afectacion_igv = '10' THEN porcentaje_igv / 100 ELSE 0 END)
    ) PERSISTED,

    -- Código SUNAT
    codigo_producto_sunat   NVARCHAR(10)     NULL,

    -- Lote
    lote_id                 UNIQUEIDENTIFIER NULL,            -- [NUEVO] FK formal a inv_lote
    lote                    NVARCHAR(50)     NULL,            -- Retrocompatibilidad

    -- Auditoría
    fecha_creacion          DATETIME         DEFAULT GETDATE() NOT NULL,

    CONSTRAINT FK_compdet_empresa   FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_compdet_comp      FOREIGN KEY (comprobante_id)
        REFERENCES invbill_comprobante(comprobante_id) ON DELETE NO ACTION,
    CONSTRAINT FK_compdet_producto  FOREIGN KEY (producto_id)
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_compdet_um        FOREIGN KEY (unidad_medida_id)
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT FK_compdet_lote      FOREIGN KEY (lote_id)    -- [NUEVO]
        REFERENCES inv_lote(lote_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_compdet_comprobante  ON invbill_comprobante_detalle(comprobante_id);
CREATE INDEX IDX_compdet_producto     ON invbill_comprobante_detalle(producto_id) WHERE producto_id IS NOT NULL;
CREATE INDEX IDX_compdet_lote         ON invbill_comprobante_detalle(lote_id) WHERE lote_id IS NOT NULL;


-- ============================================================================
-- SECCIÓN K: RPT - CAPA SEMÁNTICA DE REPORTES
-- ============================================================================
-- DESCRIPCIÓN: Metadatos de reportes que permiten al cliente configurar sus
--              propios KPIs y dimensiones de análisis sin tocar código.
--              El motor de reportes consume estas tablas para construir queries
--              dinámicos. Escala a 10 años sin necesidad de programar un
--              reporte nuevo por cada solicitud de cliente.
-- DEPENDENCIAS: ORG
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: rpt_metrica  [NUEVA]
-- Descripción: Definición de una métrica de negocio (KPI) con su origen de
--              datos, tipo de agregación y dimensiones válidas.
-- Uso: El cliente selecciona las métricas que quiere ver en su dashboard.
-- Relaciones: org_empresa
-- -----------------------------------------------------------------------------
CREATE TABLE rpt_metrica (
    metrica_id              UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id              UNIQUEIDENTIFIER NOT NULL,
    empresa_id              UNIQUEIDENTIFIER NULL,            -- NULL = disponible para todos los tenants

    codigo                  NVARCHAR(50)     NOT NULL,
    nombre                  NVARCHAR(150)    NOT NULL,
    descripcion             NVARCHAR(500)    NULL,

    -- Origen de datos
    modulo                  NVARCHAR(10)     NOT NULL,        -- 'INV','MFG','SLS','PUR','FIN','QMS','MES','APS'
    tabla_origen            NVARCHAR(100)    NOT NULL,        -- Tabla SQL que contiene el dato
    campo_valor             NVARCHAR(100)    NOT NULL,        -- Campo a agregar (ej: 'cantidad_disponible')
    tipo_agregacion         NVARCHAR(20)     DEFAULT 'sum',   -- 'sum','count','avg','min','max','count_distinct'

    -- Filtros base (JSON: {"es_activo":1,"tipo_producto":"bien"})
    filtros_base            NVARCHAR(MAX)    NULL,

    -- Formato de presentación
    unidad                  NVARCHAR(20)     NULL,            -- 'KG','USD','%','unidades','horas'
    decimales               INT              DEFAULT 2,
    formato_visualizacion   NVARCHAR(20)     DEFAULT 'numero', -- 'numero','moneda','porcentaje','tiempo'

    -- Dimensiones válidas para cruzar esta métrica (JSON array de codigo_dimension)
    dimensiones_validas     NVARCHAR(MAX)    NULL,

    -- Vertical a la que aplica (NULL = todas)
    vertical                NVARCHAR(10)     NULL,            -- 'TXT','FOD','MET',NULL

    -- Estado
    es_activo               BIT              DEFAULT 1 NOT NULL,
    es_sistema              BIT              DEFAULT 0,        -- TRUE = no se puede eliminar (viene de fábrica)
    fecha_creacion          DATETIME         DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id     UNIQUEIDENTIFIER NULL,

    CONSTRAINT FK_rptmet_empresa   FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_rptmet_codigo    UNIQUE (cliente_id, codigo)
);

CREATE INDEX IDX_rptmet_modulo        ON rpt_metrica(modulo);
CREATE INDEX IDX_rptmet_activo        ON rpt_metrica(es_activo);
CREATE INDEX IDX_rptmet_vertical      ON rpt_metrica(vertical);


-- -----------------------------------------------------------------------------
-- Tabla: rpt_dimension  [NUEVA]
-- Descripción: Dimensión de análisis reutilizable (producto, almacén, período,
--              cliente, centro de trabajo, etc.). Define cómo "cortar" una
--              métrica para obtener distintas vistas.
-- Uso: El cliente elige métrica + dimensiones para construir su reporte.
-- Relaciones: org_empresa
-- -----------------------------------------------------------------------------
CREATE TABLE rpt_dimension (
    dimension_id            UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id              UNIQUEIDENTIFIER NOT NULL,
    empresa_id              UNIQUEIDENTIFIER NULL,            -- NULL = disponible para todos los tenants

    codigo                  NVARCHAR(50)     NOT NULL,
    nombre                  NVARCHAR(150)    NOT NULL,
    descripcion             NVARCHAR(500)    NULL,

    -- Origen de la dimensión
    tabla_origen            NVARCHAR(100)    NOT NULL,        -- Tabla que provee los valores
    campo_id                NVARCHAR(100)    NOT NULL,        -- Campo clave (ej: 'producto_id')
    campo_etiqueta          NVARCHAR(100)    NOT NULL,        -- Campo legible (ej: 'nombre')
    campo_jerarquia_padre   NVARCHAR(100)    NULL,            -- Para dimensiones jerárquicas (categoría -> subcategoría)

    -- Tipo de dimensión
    tipo_dimension          NVARCHAR(20)     DEFAULT 'catalogo', -- 'catalogo','fecha','jerarquia','geografica'

    -- Estado
    es_activo               BIT              DEFAULT 1 NOT NULL,
    es_sistema              BIT              DEFAULT 0,
    fecha_creacion          DATETIME         DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id     UNIQUEIDENTIFIER NULL,

    CONSTRAINT FK_rptdim_empresa   FOREIGN KEY (empresa_id)
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_rptdim_codigo    UNIQUE (cliente_id, codigo)
);

CREATE INDEX IDX_rptdim_tipo          ON rpt_dimension(tipo_dimension);
CREATE INDEX IDX_rptdim_activo        ON rpt_dimension(es_activo);