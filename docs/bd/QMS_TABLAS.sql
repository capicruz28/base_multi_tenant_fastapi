-- ============================================================================
-- SECCIÓN 4: QMS - GESTIÓN DE CALIDAD
-- ============================================================================
-- DESCRIPCIÓN: Control de calidad de productos, inspecciones, no conformidades
-- DEPENDENCIAS: ORG, INV
-- USADO POR: PUR (inspección entrada), MFG (inspección producción), SLS (inspección salida)
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: qms_parametro_calidad
-- Descripción: Parámetros de calidad a inspeccionar (peso, dimensiones, color, etc)
-- Uso: Definir qué se va a medir en las inspecciones
-- Relaciones: Usado por qms_plan_inspeccion
-- -----------------------------------------------------------------------------
CREATE TABLE qms_parametro_calidad (
    parametro_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(255) NULL,
    
    -- Tipo de parámetro
    tipo_parametro NVARCHAR(30) NOT NULL,                     -- 'cuantitativo', 'cualitativo', 'pasa_no_pasa'
    
    -- Para parámetros cuantitativos
    unidad_medida_id UNIQUEIDENTIFIER NULL,
    valor_minimo DECIMAL(18,4) NULL,
    valor_maximo DECIMAL(18,4) NULL,
    valor_objetivo DECIMAL(18,4) NULL,
    
    -- Para parámetros cualitativos
    opciones_permitidas NVARCHAR(MAX) NULL,                   -- JSON: ["Excelente","Bueno","Regular","Malo"]
    
    -- Método de inspección
    metodo_inspeccion NVARCHAR(255) NULL,                     -- Instrucción de cómo inspeccionar
    requiere_equipo NVARCHAR(100) NULL,                       -- Equipo necesario (calibrador, balanza, etc)
    
    -- Estado
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_qms_param_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_qms_param_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_qms_param_codigo UNIQUE (cliente_id, empresa_id, codigo)
);

CREATE INDEX IDX_qms_param_empresa ON qms_parametro_calidad(empresa_id, es_activo);
CREATE INDEX IDX_qms_param_tipo ON qms_parametro_calidad(tipo_parametro);

-- -----------------------------------------------------------------------------
-- Tabla: qms_plan_inspeccion
-- Descripción: Planes de inspección por producto o familia de productos
-- Uso: Define qué parámetros inspeccionar y criterios de aceptación
-- Relaciones: Asignado a productos o categorías
-- -----------------------------------------------------------------------------
CREATE TABLE qms_plan_inspeccion (
    plan_inspeccion_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(255) NULL,
    
    -- Aplicabilidad
    aplica_a NVARCHAR(20) NOT NULL,                           -- 'producto', 'categoria', 'todos'
    producto_id UNIQUEIDENTIFIER NULL,                        -- Si aplica a producto específico
    categoria_id UNIQUEIDENTIFIER NULL,                       -- Si aplica a categoría
    
    -- Tipo de inspección
    tipo_inspeccion NVARCHAR(30) NOT NULL,                    -- 'recepcion', 'proceso', 'final', 'salida'
    
    -- Muestreo
    tipo_muestreo NVARCHAR(30) DEFAULT 'total',               -- 'total', 'aleatorio', 'estadistico'
    porcentaje_muestreo DECIMAL(5,2) NULL,                    -- % a inspeccionar si es aleatorio
    tabla_muestreo NVARCHAR(50) NULL,                         -- Referencia a tabla AQL, MIL-STD, etc
    
    -- Criterios de aceptación
    nivel_aceptacion_criticos DECIMAL(5,2) DEFAULT 0,         -- % defectos críticos aceptables
    nivel_aceptacion_mayores DECIMAL(5,2) DEFAULT 2.5,        -- % defectos mayores aceptables
    nivel_aceptacion_menores DECIMAL(5,2) DEFAULT 4.0,        -- % defectos menores aceptables
    
    -- Estado
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_vigencia_desde DATE NULL,
    fecha_vigencia_hasta DATE NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_qms_plan_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_qms_plan_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_qms_plan_categoria FOREIGN KEY (categoria_id) 
        REFERENCES inv_categoria_producto(categoria_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_qms_plan_codigo UNIQUE (cliente_id, empresa_id, codigo)
);

CREATE INDEX IDX_qms_plan_empresa ON qms_plan_inspeccion(empresa_id, es_activo);
CREATE INDEX IDX_qms_plan_producto ON qms_plan_inspeccion(producto_id) WHERE producto_id IS NOT NULL;
CREATE INDEX IDX_qms_plan_categoria ON qms_plan_inspeccion(categoria_id) WHERE categoria_id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Tabla: qms_plan_inspeccion_detalle
-- Descripción: Parámetros a inspeccionar dentro de un plan
-- Uso: Lista de checks a realizar en cada inspección
-- Relaciones: Detalle de qms_plan_inspeccion
-- -----------------------------------------------------------------------------
CREATE TABLE qms_plan_inspeccion_detalle (
    plan_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    plan_inspeccion_id UNIQUEIDENTIFIER NOT NULL,
    parametro_calidad_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Configuración
    orden INT DEFAULT 0,
    es_obligatorio BIT DEFAULT 1,
    criticidad NVARCHAR(20) DEFAULT 'menor',                  -- 'critico', 'mayor', 'menor'
    
    -- Valores específicos del plan (pueden sobrescribir los del parámetro)
    valor_minimo_plan DECIMAL(18,4) NULL,
    valor_maximo_plan DECIMAL(18,4) NULL,
    valor_objetivo_plan DECIMAL(18,4) NULL,
    
    -- Instrucciones
    instrucciones_especificas NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_qms_plandet_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_qms_plandet_plan FOREIGN KEY (plan_inspeccion_id) 
        REFERENCES qms_plan_inspeccion(plan_inspeccion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_qms_plandet_param FOREIGN KEY (parametro_calidad_id) 
        REFERENCES qms_parametro_calidad(parametro_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_qms_plandet_empresa ON qms_plan_inspeccion_detalle(empresa_id);
CREATE INDEX IDX_qms_plandet_plan ON qms_plan_inspeccion_detalle(plan_inspeccion_id, orden);

-- -----------------------------------------------------------------------------
-- Tabla: qms_inspeccion
-- Descripción: Cabecera de inspecciones realizadas
-- Uso: Registro de inspecciones de calidad ejecutadas
-- Relaciones: Vinculada a movimientos de inventario, órdenes de compra, producción
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
    lote NVARCHAR(50) NULL,
    
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
    cantidad_observada DECIMAL(18,4) DEFAULT 0,                -- Con observaciones menores
    
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
    CONSTRAINT FK_qms_insp_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_qms_insp_numero UNIQUE (cliente_id, empresa_id, numero_inspeccion)
);

CREATE INDEX IDX_qms_insp_empresa ON qms_inspeccion(empresa_id, fecha_inspeccion DESC);
CREATE INDEX IDX_qms_insp_producto ON qms_inspeccion(producto_id, resultado);
CREATE INDEX IDX_qms_insp_resultado ON qms_inspeccion(resultado, fecha_inspeccion DESC);
CREATE INDEX IDX_qms_insp_lote ON qms_inspeccion(lote) WHERE lote IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Tabla: qms_inspeccion_detalle
-- Descripción: Mediciones/observaciones por parámetro de calidad
-- Uso: Registro detallado de cada punto inspeccionado
-- Relaciones: Detalle de qms_inspeccion
-- -----------------------------------------------------------------------------
CREATE TABLE qms_inspeccion_detalle (
    inspeccion_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    inspeccion_id UNIQUEIDENTIFIER NOT NULL,
    parametro_calidad_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Valor medido/observado
    valor_medido DECIMAL(18,4) NULL,                          -- Para parámetros cuantitativos
    valor_cualitativo NVARCHAR(50) NULL,                      -- Para parámetros cualitativos
    resultado_pasa_no_pasa BIT NULL,                          -- Para pasa/no pasa
    
    -- Evaluación
    cumple_especificacion BIT DEFAULT 1,
    criticidad_defecto NVARCHAR(20) NULL,                     -- 'critico', 'mayor', 'menor' (si no cumple)
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_qms_inspdet_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_qms_inspdet_insp FOREIGN KEY (inspeccion_id) 
        REFERENCES qms_inspeccion(inspeccion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_qms_inspdet_param FOREIGN KEY (parametro_calidad_id) 
        REFERENCES qms_parametro_calidad(parametro_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_qms_inspdet_empresa ON qms_inspeccion_detalle(empresa_id);
CREATE INDEX IDX_qms_inspdet_insp ON qms_inspeccion_detalle(inspeccion_id);
CREATE INDEX IDX_qms_inspdet_no_conforme ON qms_inspeccion_detalle(inspeccion_id) 
    WHERE cumple_especificacion = 0;

-- -----------------------------------------------------------------------------
-- Tabla: qms_no_conformidad
-- Descripción: Registro de no conformidades y acciones correctivas
-- Uso: Seguimiento de problemas de calidad detectados
-- Relaciones: Puede originarse de inspecciones, quejas de clientes, auditorías
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
    lote NVARCHAR(50) NULL,
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
);

CREATE INDEX IDX_qms_nc_empresa ON qms_no_conformidad(empresa_id, fecha_deteccion DESC);
CREATE INDEX IDX_qms_nc_estado ON qms_no_conformidad(estado, fecha_deteccion DESC);
CREATE INDEX IDX_qms_nc_tipo ON qms_no_conformidad(tipo_nc);
CREATE INDEX IDX_qms_nc_producto ON qms_no_conformidad(producto_id) WHERE producto_id IS NOT NULL;