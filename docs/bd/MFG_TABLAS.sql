-- ============================================================================
-- SECCIÓN 7: MFG - MANUFACTURA Y PRODUCCIÓN
-- ============================================================================
-- DESCRIPCIÓN: Gestión de producción, órdenes de fabricación, BOM
-- DEPENDENCIAS: ORG, INV (productos, stock)
-- USADO POR: CST (costeo de producción), MRP (planeamiento)
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: mfg_centro_trabajo
-- Descripción: Centros de trabajo o estaciones de producción
-- Uso: Áreas donde se ejecutan operaciones de manufactura
-- Relaciones: Pueden estar en sucursales, tienen capacidad productiva
-- -----------------------------------------------------------------------------
CREATE TABLE mfg_centro_trabajo (
    centro_trabajo_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(255) NULL,
    
    -- Ubicación
    sucursal_id UNIQUEIDENTIFIER NULL,
    ubicacion_fisica NVARCHAR(100) NULL,
    
    -- Tipo
    tipo_centro NVARCHAR(30) NOT NULL,                        -- 'maquina', 'linea_montaje', 'estacion_manual', 'celula_trabajo'
    
    -- Capacidad
    capacidad_horas_dia DECIMAL(8,2) NULL,                    -- Horas productivas por día
    capacidad_unidades_hora DECIMAL(12,2) NULL,               -- Unidades que puede producir por hora
    eficiencia_promedio DECIMAL(5,2) DEFAULT 85,              -- % eficiencia (típico 85%)
    
    -- Costos
    costo_hora_maquina DECIMAL(12,2) NULL,                    -- Costo por hora de uso
    costo_setup DECIMAL(12,2) NULL,                           -- Costo de preparación
    centro_costo_id UNIQUEIDENTIFIER NULL,
    
    -- Mantenimiento
    requiere_mantenimiento BIT DEFAULT 1,
    frecuencia_mantenimiento_dias INT NULL,
    ultima_fecha_mantenimiento DATE NULL,
    
    -- Estado
    estado_centro NVARCHAR(20) DEFAULT 'disponible',          -- 'disponible', 'produccion', 'mantenimiento', 'averiado', 'inactivo'
    es_activo BIT DEFAULT 1 NOT NULL,
    
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_ct_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_ct_sucursal FOREIGN KEY (sucursal_id) 
        REFERENCES org_sucursal(sucursal_id) ON DELETE NO ACTION,
    CONSTRAINT FK_ct_cc FOREIGN KEY (centro_costo_id) 
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_ct_codigo UNIQUE (cliente_id, empresa_id, codigo)
);

CREATE INDEX IDX_ct_empresa ON mfg_centro_trabajo(empresa_id, es_activo);
CREATE INDEX IDX_ct_estado ON mfg_centro_trabajo(estado_centro);

-- -----------------------------------------------------------------------------
-- Tabla: mfg_operacion
-- Descripción: Operaciones o pasos en un proceso productivo
-- Uso: Catálogo de actividades que se realizan en producción
-- Relaciones: Se asignan a rutas de fabricación
-- -----------------------------------------------------------------------------
CREATE TABLE mfg_operacion (
    operacion_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(500) NULL,
    
    -- Centro de trabajo donde se ejecuta típicamente
    centro_trabajo_id UNIQUEIDENTIFIER NULL,
    
    -- Tiempos estándar
    tiempo_setup_minutos DECIMAL(10,2) NULL,                  -- Tiempo de preparación
    tiempo_operacion_minutos DECIMAL(10,2) NULL,              -- Tiempo por unidad
    
    -- Recursos
    requiere_herramientas NVARCHAR(MAX) NULL,                 -- JSON o texto
    requiere_habilidad NVARCHAR(100) NULL,
    
    -- Calidad
    requiere_inspeccion BIT DEFAULT 0,
    plan_inspeccion_id UNIQUEIDENTIFIER NULL,                 -- FK a qms_plan_inspeccion
    
    -- Estado
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_oper_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_oper_ct FOREIGN KEY (centro_trabajo_id) 
        REFERENCES mfg_centro_trabajo(centro_trabajo_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_oper_codigo UNIQUE (cliente_id, empresa_id, codigo)
);

CREATE INDEX IDX_oper_empresa ON mfg_operacion(empresa_id, es_activo);
CREATE INDEX IDX_oper_ct ON mfg_operacion(centro_trabajo_id) WHERE centro_trabajo_id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Tabla: mfg_lista_materiales (BOM - Bill of Materials)
-- Descripción: Fórmula/receta de un producto (qué materiales se necesitan)
-- Uso: Define componentes para fabricar un producto
-- Relaciones: Producto padre (lo que se fabrica) y componentes (lo que se usa)
-- -----------------------------------------------------------------------------
CREATE TABLE mfg_lista_materiales (
    bom_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_bom NVARCHAR(20) NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,                    -- Producto que se fabrica
    
    -- Versión y vigencia
    version NVARCHAR(10) DEFAULT '1.0',
    fecha_vigencia_desde DATE NOT NULL,
    fecha_vigencia_hasta DATE NULL,
    
    -- Cantidad base
    cantidad_base DECIMAL(18,4) DEFAULT 1,                    -- Cantidad de producto que se obtiene con esta BOM
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Tipo de BOM
    tipo_bom NVARCHAR(20) DEFAULT 'produccion',               -- 'produccion', 'ingenieria', 'costeo'
    
    -- Rendimiento
    porcentaje_desperdicio DECIMAL(5,2) DEFAULT 0,            -- % de merma esperada
    
    -- Estado
    es_bom_activa BIT DEFAULT 1,                              -- Si es la BOM vigente para producción
    estado NVARCHAR(20) DEFAULT 'borrador',                   -- 'borrador', 'aprobada', 'obsoleta'
    aprobado_por_usuario_id UNIQUEIDENTIFIER NULL,
    fecha_aprobacion DATE NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_bom_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_bom_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_bom_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_bom_codigo UNIQUE (cliente_id, empresa_id, codigo_bom)
);

CREATE INDEX IDX_bom_empresa ON mfg_lista_materiales(empresa_id, es_bom_activa);
CREATE INDEX IDX_bom_producto ON mfg_lista_materiales(producto_id, es_bom_activa);

-- -----------------------------------------------------------------------------
-- Tabla: mfg_lista_materiales_detalle
-- Descripción: Componentes/materiales necesarios para fabricar
-- Uso: Lista de insumos con cantidades requeridas
-- Relaciones: Detalle de BOM, referencia a inv_producto (componentes)
-- -----------------------------------------------------------------------------
CREATE TABLE mfg_lista_materiales_detalle (
    bom_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    bom_id UNIQUEIDENTIFIER NOT NULL,
    
    producto_componente_id UNIQUEIDENTIFIER NOT NULL,         -- Producto que se consume
    
    -- Cantidad requerida
    cantidad DECIMAL(18,4) NOT NULL,                          -- Cantidad por unidad de producto padre
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Tipo de componente
    tipo_componente NVARCHAR(20) DEFAULT 'material',          -- 'material', 'subcomponente', 'empaque'
    es_critico BIT DEFAULT 0,                                 -- Si es componente crítico
    
    -- Desperdicio
    porcentaje_desperdicio DECIMAL(5,2) DEFAULT 0,
    
    -- Sustitutos
    tiene_sustitutos BIT DEFAULT 0,
    productos_sustitutos NVARCHAR(MAX) NULL,                  -- JSON con IDs de productos alternativos
    
    -- Secuencia
    secuencia INT DEFAULT 0,
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_bomdet_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_bomdet_bom FOREIGN KEY (bom_id) 
        REFERENCES mfg_lista_materiales(bom_id) ON DELETE NO ACTION,
    CONSTRAINT FK_bomdet_componente FOREIGN KEY (producto_componente_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_bomdet_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_bomdet_empresa ON mfg_lista_materiales_detalle(empresa_id);
CREATE INDEX IDX_bomdet_bom ON mfg_lista_materiales_detalle(bom_id, secuencia);
CREATE INDEX IDX_bomdet_componente ON mfg_lista_materiales_detalle(producto_componente_id);

-- -----------------------------------------------------------------------------
-- Tabla: mfg_ruta_fabricacion
-- Descripción: Secuencia de operaciones para fabricar un producto
-- Uso: Define el "cómo" se fabrica (la BOM define el "qué")
-- Relaciones: Vinculada a producto y BOM
-- -----------------------------------------------------------------------------
CREATE TABLE mfg_ruta_fabricacion (
    ruta_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_ruta NVARCHAR(20) NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    bom_id UNIQUEIDENTIFIER NULL,                             -- BOM asociada (opcional)
    
    nombre NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(255) NULL,
    
    -- Versión
    version NVARCHAR(10) DEFAULT '1.0',
    
    -- Tiempos totales (suma de operaciones)
    tiempo_total_setup_minutos DECIMAL(10,2) DEFAULT 0,
    tiempo_total_operacion_minutos DECIMAL(10,2) DEFAULT 0,
    
    -- Estado
    es_ruta_activa BIT DEFAULT 1,
    estado NVARCHAR(20) DEFAULT 'borrador',                   -- 'borrador', 'aprobada', 'obsoleta'
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_rutafab_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_rutafab_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_rutafab_bom FOREIGN KEY (bom_id) 
        REFERENCES mfg_lista_materiales(bom_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_rutafab_codigo UNIQUE (cliente_id, empresa_id, codigo_ruta)
);

CREATE INDEX IDX_ruta_empresa ON mfg_ruta_fabricacion(empresa_id, es_ruta_activa);
CREATE INDEX IDX_ruta_producto ON mfg_ruta_fabricacion(producto_id, es_ruta_activa);

-- -----------------------------------------------------------------------------
-- Tabla: mfg_ruta_fabricacion_detalle
-- Descripción: Operaciones que componen la ruta de fabricación
-- Uso: Secuencia paso a paso del proceso productivo
-- Relaciones: Detalle de ruta, referencia a operaciones y centros de trabajo
-- -----------------------------------------------------------------------------
CREATE TABLE mfg_ruta_fabricacion_detalle (
    ruta_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    ruta_id UNIQUEIDENTIFIER NOT NULL,
    
    secuencia INT NOT NULL,                                    -- Orden de ejecución
    operacion_id UNIQUEIDENTIFIER NOT NULL,
    centro_trabajo_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Tiempos
    tiempo_setup_minutos DECIMAL(10,2) DEFAULT 0,
    tiempo_operacion_minutos DECIMAL(10,2) DEFAULT 0,         -- Por unidad
    
    -- Control
    es_operacion_critica BIT DEFAULT 0,
    permite_operaciones_paralelas BIT DEFAULT 0,
    
    -- Observaciones
    instrucciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_rutadet_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_rutadet_ruta FOREIGN KEY (ruta_id) 
        REFERENCES mfg_ruta_fabricacion(ruta_id) ON DELETE NO ACTION,
    CONSTRAINT FK_rutadet_oper FOREIGN KEY (operacion_id) 
        REFERENCES mfg_operacion(operacion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_rutadet_ct FOREIGN KEY (centro_trabajo_id) 
        REFERENCES mfg_centro_trabajo(centro_trabajo_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_rutadet_empresa ON mfg_ruta_fabricacion_detalle(empresa_id);
CREATE INDEX IDX_rutadet_ruta ON mfg_ruta_fabricacion_detalle(ruta_id, secuencia);

-- -----------------------------------------------------------------------------
-- Tabla: mfg_orden_produccion
-- Descripción: Orden de fabricación (documento de producción)
-- Uso: Autorización para fabricar una cantidad de producto
-- Relaciones: Referencia producto, BOM, ruta; genera movimientos inventario
-- -----------------------------------------------------------------------------
CREATE TABLE mfg_orden_produccion (
    orden_produccion_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_op NVARCHAR(20) NOT NULL,
    fecha_emision DATE DEFAULT GETDATE() NOT NULL,
    fecha_inicio_programada DATE NOT NULL,
    fecha_fin_programada DATE NOT NULL,
    
    -- Producto a fabricar
    producto_id UNIQUEIDENTIFIER NOT NULL,
    bom_id UNIQUEIDENTIFIER NOT NULL,
    ruta_fabricacion_id UNIQUEIDENTIFIER NULL,
    
    -- Cantidad
    cantidad_planeada DECIMAL(18,4) NOT NULL,
    cantidad_producida DECIMAL(18,4) DEFAULT 0,
    cantidad_defectuosa DECIMAL(18,4) DEFAULT 0,
    cantidad_pendiente AS (cantidad_planeada - cantidad_producida - cantidad_defectuosa) PERSISTED,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Destino
    almacen_destino_id UNIQUEIDENTIFIER NULL,
    
    -- Prioridad
    prioridad INT DEFAULT 3,                                   -- 1=Urgente, 2=Alta, 3=Normal, 4=Baja
    tipo_orden NVARCHAR(20) DEFAULT 'normal',                 -- 'normal', 'urgente', 'maquila', 'muestra'
    
    -- Origen (si es para venta, proyecto, stock)
    documento_origen_tipo NVARCHAR(30) NULL,                  -- 'pedido_venta', 'proyecto', 'reposicion_stock'
    documento_origen_id UNIQUEIDENTIFIER NULL,
    
    -- Fechas de ejecución real
    fecha_inicio_real DATETIME NULL,
    fecha_fin_real DATETIME NULL,
    
    -- Costos
    costo_materiales DECIMAL(18,2) DEFAULT 0,
    costo_mano_obra DECIMAL(18,2) DEFAULT 0,
    costo_cif DECIMAL(18,2) DEFAULT 0,                        -- Costos indirectos fabricación
    costo_total AS (costo_materiales + costo_mano_obra + costo_cif) PERSISTED,
    moneda_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Centro de costo
    centro_costo_id UNIQUEIDENTIFIER NULL,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'borrador',                   -- 'borrador', 'liberada', 'en_proceso', 'pausada', 'completada', 'cerrada', 'anulada'
    
    -- Responsable
    responsable_usuario_id UNIQUEIDENTIFIER NULL,
    responsable_nombre NVARCHAR(150) NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_op_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_op_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_op_bom FOREIGN KEY (bom_id) 
        REFERENCES mfg_lista_materiales(bom_id) ON DELETE NO ACTION,
    CONSTRAINT FK_op_ruta FOREIGN KEY (ruta_fabricacion_id) 
        REFERENCES mfg_ruta_fabricacion(ruta_id) ON DELETE NO ACTION,
    CONSTRAINT FK_op_almacen FOREIGN KEY (almacen_destino_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION,
    CONSTRAINT FK_op_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT FK_op_cc FOREIGN KEY (centro_costo_id) 
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_op_numero UNIQUE (cliente_id, empresa_id, numero_op),
    CONSTRAINT FK_op_moneda FOREIGN KEY (moneda_id)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_op_empresa ON mfg_orden_produccion(empresa_id, fecha_emision DESC);
CREATE INDEX IDX_op_producto ON mfg_orden_produccion(producto_id, estado);
CREATE INDEX IDX_op_estado ON mfg_orden_produccion(estado, fecha_inicio_programada);
CREATE INDEX IDX_op_fecha_programada ON mfg_orden_produccion(fecha_inicio_programada, estado);

-- -----------------------------------------------------------------------------
-- Tabla: mfg_orden_produccion_operacion
-- Descripción: Seguimiento de operaciones dentro de una orden de producción
-- Uso: Control de avance por cada paso del proceso
-- Relaciones: Detalle de orden de producción basado en ruta de fabricación
-- -----------------------------------------------------------------------------
CREATE TABLE mfg_orden_produccion_operacion (
    op_operacion_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    orden_produccion_id UNIQUEIDENTIFIER NOT NULL,
    ruta_detalle_id UNIQUEIDENTIFIER NULL,                    -- Referencia a ruta_fabricacion_detalle
    operacion_id UNIQUEIDENTIFIER NOT NULL,
    centro_trabajo_id UNIQUEIDENTIFIER NOT NULL,
    
    secuencia INT NOT NULL,
    
    -- Tiempos planificados
    tiempo_setup_planificado_minutos DECIMAL(10,2) DEFAULT 0,
    tiempo_operacion_planificado_minutos DECIMAL(10,2) DEFAULT 0,
    
    -- Tiempos reales
    tiempo_setup_real_minutos DECIMAL(10,2) DEFAULT 0,
    tiempo_operacion_real_minutos DECIMAL(10,2) DEFAULT 0,
    
    -- Fechas
    fecha_inicio_programada DATETIME NULL,
    fecha_fin_programada DATETIME NULL,
    fecha_inicio_real DATETIME NULL,
    fecha_fin_real DATETIME NULL,
    
    -- Cantidad
    cantidad_procesada DECIMAL(18,4) DEFAULT 0,
    cantidad_aprobada DECIMAL(18,4) DEFAULT 0,
    cantidad_rechazada DECIMAL(18,4) DEFAULT 0,
    
    -- Personal asignado
    operario_usuario_id UNIQUEIDENTIFIER NULL,
    operario_nombre NVARCHAR(150) NULL,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'pendiente',                  -- 'pendiente', 'en_proceso', 'pausada', 'completada', 'cancelada'
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_opoper_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_opoper_op FOREIGN KEY (orden_produccion_id) 
        REFERENCES mfg_orden_produccion(orden_produccion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_opoper_rutadet FOREIGN KEY (ruta_detalle_id) 
        REFERENCES mfg_ruta_fabricacion_detalle(ruta_detalle_id) ON DELETE NO ACTION,
    CONSTRAINT FK_opoper_oper FOREIGN KEY (operacion_id) 
        REFERENCES mfg_operacion(operacion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_opoper_ct FOREIGN KEY (centro_trabajo_id) 
        REFERENCES mfg_centro_trabajo(centro_trabajo_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_opoper_empresa ON mfg_orden_produccion_operacion(empresa_id);
CREATE INDEX IDX_opoper_op ON mfg_orden_produccion_operacion(orden_produccion_id, secuencia);
CREATE INDEX IDX_opoper_estado ON mfg_orden_produccion_operacion(estado, fecha_inicio_programada);
CREATE INDEX IDX_opoper_ct ON mfg_orden_produccion_operacion(centro_trabajo_id, estado);

-- -----------------------------------------------------------------------------
-- Tabla: mfg_consumo_materiales
-- Descripción: Registro de materiales consumidos en producción
-- Uso: Trazabilidad de qué materiales se usaron en cada OP
-- Relaciones: Vinculado a orden de producción, actualiza inventario
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
    lote NVARCHAR(50) NULL,
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
);

CREATE INDEX IDX_consumo_empresa ON mfg_consumo_materiales(empresa_id);
CREATE INDEX IDX_consumo_op ON mfg_consumo_materiales(orden_produccion_id);
CREATE INDEX IDX_consumo_producto ON mfg_consumo_materiales(producto_id, fecha_consumo DESC);