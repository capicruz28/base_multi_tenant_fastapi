-- ============================================================================
-- SECCIÓN 10: MNT - MANTENIMIENTO DE ACTIVOS
-- ============================================================================
-- DESCRIPCIÓN: Gestión de mantenimiento preventivo y correctivo
-- DEPENDENCIAS: ORG, MFG (centros de trabajo, maquinaria)
-- USADO POR: Control de disponibilidad de equipos
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: mnt_activo
-- Descripción: Activos físicos sujetos a mantenimiento
-- Uso: Maquinaria, equipos, vehículos, instalaciones
-- Relaciones: Puede vincular a centros de trabajo, vehículos, etc
-- -----------------------------------------------------------------------------
CREATE TABLE mnt_activo (
    activo_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_activo NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(150) NOT NULL,
    descripcion NVARCHAR(500) NULL,
    
    -- Clasificación
    tipo_activo NVARCHAR(30) NOT NULL,                        -- 'maquinaria', 'vehiculo', 'equipo', 'instalacion', 'herramienta'
    categoria NVARCHAR(50) NULL,
    
    -- Identificación
    marca NVARCHAR(50) NULL,
    modelo NVARCHAR(50) NULL,
    numero_serie NVARCHAR(50) NULL,
    año_fabricacion INT NULL,
    
    -- Ubicación
    sucursal_id UNIQUEIDENTIFIER NULL,
    centro_trabajo_id UNIQUEIDENTIFIER NULL,                  -- Si es equipo de producción
    ubicacion_detalle NVARCHAR(100) NULL,
    
    -- Vinculación con otros módulos
    vehiculo_id UNIQUEIDENTIFIER NULL,                        -- Si es vehículo del módulo LOG
    
    -- Datos técnicos
    especificaciones_tecnicas NVARCHAR(MAX) NULL,             -- JSON o texto
    capacidad NVARCHAR(100) NULL,
    potencia NVARCHAR(50) NULL,
    
    -- Proveedor/Fabricante
    fabricante NVARCHAR(100) NULL,
    proveedor_id UNIQUEIDENTIFIER NULL,
    
    -- Fechas importantes
    fecha_adquisicion DATE NULL,
    fecha_puesta_operacion DATE NULL,
    vida_util_años INT NULL,
    
    -- Criticidad
    criticidad NVARCHAR(20) DEFAULT 'media',                  -- 'critica', 'alta', 'media', 'baja'
    
    -- Costo
    valor_adquisicion DECIMAL(18,2) NULL,
    valor_actual DECIMAL(18,2) NULL,
    moneda_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Estado
    estado_activo NVARCHAR(20) DEFAULT 'operativo',           -- 'operativo', 'mantenimiento', 'averiado', 'baja'
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_activo_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_activo_sucursal FOREIGN KEY (sucursal_id) 
        REFERENCES org_sucursal(sucursal_id) ON DELETE NO ACTION,
    CONSTRAINT FK_activo_ct FOREIGN KEY (centro_trabajo_id) 
        REFERENCES mfg_centro_trabajo(centro_trabajo_id) ON DELETE NO ACTION,
    CONSTRAINT FK_activo_vehiculo FOREIGN KEY (vehiculo_id) 
        REFERENCES log_vehiculo(vehiculo_id) ON DELETE NO ACTION,
    CONSTRAINT FK_activo_prov FOREIGN KEY (proveedor_id) 
        REFERENCES pur_proveedor(proveedor_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_activo_codigo UNIQUE (cliente_id, empresa_id, codigo_activo),
    CONSTRAINT FK_activo_moneda FOREIGN KEY (moneda_id)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_activo_empresa ON mnt_activo(empresa_id, es_activo);
CREATE INDEX IDX_activo_tipo ON mnt_activo(tipo_activo, estado_activo);
CREATE INDEX IDX_activo_criticidad ON mnt_activo(criticidad);

-- -----------------------------------------------------------------------------
-- Tabla: mnt_plan_mantenimiento
-- Descripción: Planes de mantenimiento preventivo
-- Uso: Programa de mantenimientos periódicos por activo
-- Relaciones: Asignado a activos
-- -----------------------------------------------------------------------------
CREATE TABLE mnt_plan_mantenimiento (
    plan_mantenimiento_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    activo_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_plan NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(500) NULL,
    
    tipo_mantenimiento NVARCHAR(20) NOT NULL,                 -- 'preventivo', 'predictivo'
    
    -- Frecuencia
    frecuencia_tipo NVARCHAR(20) NOT NULL,                    -- 'dias', 'horas_uso', 'kilometros', 'ciclos'
    frecuencia_valor INT NOT NULL,
    
    -- Siguiente mantenimiento
    fecha_ultimo_mantenimiento DATE NULL,
    fecha_proximo_mantenimiento DATE NULL,
    horas_uso_ultimo DECIMAL(12,2) NULL,
    horas_uso_proximo DECIMAL(12,2) NULL,
    
    -- Responsable
    responsable_usuario_id UNIQUEIDENTIFIER NULL,
    responsable_nombre NVARCHAR(150) NULL,
    
    -- Tareas a realizar
    tareas_mantenimiento NVARCHAR(MAX) NULL,                  -- JSON o checklist
    
    -- Costo estimado
    costo_estimado DECIMAL(18,2) NULL,
    moneda_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Estado
    es_activo BIT DEFAULT 1 NOT NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_planmnt_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_planmnt_activo FOREIGN KEY (activo_id) 
        REFERENCES mnt_activo(activo_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_planmnt_codigo UNIQUE (cliente_id, empresa_id, codigo_plan),
    CONSTRAINT FK_planmnt_moneda FOREIGN KEY (moneda_id)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_planmnt_empresa ON mnt_plan_mantenimiento(empresa_id, es_activo);
CREATE INDEX IDX_planmnt_activo ON mnt_plan_mantenimiento(activo_id, es_activo);
CREATE INDEX IDX_planmnt_proximo ON mnt_plan_mantenimiento(fecha_proximo_mantenimiento) 
    WHERE fecha_proximo_mantenimiento IS NOT NULL AND es_activo = 1;

-- -----------------------------------------------------------------------------
-- Tabla: mnt_orden_trabajo
-- Descripción: Órdenes de trabajo de mantenimiento
-- Uso: Registro de mantenimientos (preventivos y correctivos)
-- Relaciones: Vinculado a activos y planes
-- -----------------------------------------------------------------------------
CREATE TABLE mnt_orden_trabajo (
    orden_trabajo_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_ot NVARCHAR(20) NOT NULL,
    fecha_solicitud DATETIME DEFAULT GETDATE() NOT NULL,
    
    activo_id UNIQUEIDENTIFIER NOT NULL,
    plan_mantenimiento_id UNIQUEIDENTIFIER NULL,              -- Si es preventivo
    
    -- Tipo
    tipo_mantenimiento NVARCHAR(20) NOT NULL,                 -- 'preventivo', 'correctivo', 'predictivo', 'modificacion'
    prioridad NVARCHAR(20) DEFAULT 'media',                   -- 'urgente', 'alta', 'media', 'baja'
    
    -- Problema/Descripción
    problema_detectado NVARCHAR(MAX) NULL,
    trabajo_a_realizar NVARCHAR(MAX) NOT NULL,
    
    -- Asignación
    tecnico_asignado_usuario_id UNIQUEIDENTIFIER NULL,
    tecnico_nombre NVARCHAR(150) NULL,
    
    -- Programación
    fecha_programada DATETIME NULL,
    fecha_inicio_real DATETIME NULL,
    fecha_fin_real DATETIME NULL,
    duracion_horas AS (
        CASE 
            WHEN fecha_inicio_real IS NOT NULL AND fecha_fin_real IS NOT NULL
            THEN DATEDIFF(MINUTE, fecha_inicio_real, fecha_fin_real) / 60.0
            ELSE NULL
        END
    ) PERSISTED,
    
    -- Trabajo realizado
    trabajo_realizado NVARCHAR(MAX) NULL,
    repuestos_utilizados NVARCHAR(MAX) NULL,                  -- JSON con productos usados
    
    -- Costos
    costo_mano_obra DECIMAL(18,2) DEFAULT 0,
    costo_repuestos DECIMAL(18,2) DEFAULT 0,
    costo_servicios_terceros DECIMAL(18,2) DEFAULT 0,
    costo_total AS (costo_mano_obra + costo_repuestos + costo_servicios_terceros) PERSISTED,
    moneda_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'solicitada',                 -- 'solicitada', 'programada', 'en_proceso', 'pausada', 'completada', 'cerrada', 'cancelada'
    
    -- Cierre
    fecha_cierre DATETIME NULL,
    cerrado_por_usuario_id UNIQUEIDENTIFIER NULL,
    calificacion_trabajo DECIMAL(3,2) NULL,                   -- 1.00 a 5.00
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_ot_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_ot_activo FOREIGN KEY (activo_id) 
        REFERENCES mnt_activo(activo_id) ON DELETE NO ACTION,
    CONSTRAINT FK_ot_plan FOREIGN KEY (plan_mantenimiento_id) 
        REFERENCES mnt_plan_mantenimiento(plan_mantenimiento_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_ot_numero UNIQUE (cliente_id, empresa_id, numero_ot),
    CONSTRAINT FK_ot_moneda FOREIGN KEY (moneda_id)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_ot_empresa ON mnt_orden_trabajo(empresa_id, fecha_solicitud DESC);
CREATE INDEX IDX_ot_activo ON mnt_orden_trabajo(activo_id, estado);
CREATE INDEX IDX_ot_estado ON mnt_orden_trabajo(estado, prioridad, fecha_programada);
CREATE INDEX IDX_ot_tecnico ON mnt_orden_trabajo(tecnico_asignado_usuario_id, estado) 
    WHERE tecnico_asignado_usuario_id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Tabla: mnt_historial_mantenimiento
-- Descripción: Historial de mantenimientos realizados
-- Uso: Log de todos los mantenimientos por activo
-- Relaciones: Alimentado desde órdenes de trabajo completadas
-- -----------------------------------------------------------------------------
CREATE TABLE mnt_historial_mantenimiento (
    historial_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    activo_id UNIQUEIDENTIFIER NOT NULL,
    orden_trabajo_id UNIQUEIDENTIFIER NULL,
    
    fecha_mantenimiento DATE NOT NULL,
    tipo_mantenimiento NVARCHAR(20) NOT NULL,
    
    descripcion_trabajo NVARCHAR(MAX) NULL,
    tecnico_nombre NVARCHAR(150) NULL,
    
    horas_uso_activo DECIMAL(12,2) NULL,                      -- Lectura del horómetro/odómetro
    kilometraje DECIMAL(12,2) NULL,
    
    costo_total DECIMAL(18,2) DEFAULT 0,
    moneda_id UNIQUEIDENTIFIER NOT NULL,
    
    observaciones NVARCHAR(500) NULL,
    
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_histmnt_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_histmnt_activo FOREIGN KEY (activo_id) 
        REFERENCES mnt_activo(activo_id) ON DELETE NO ACTION,
    CONSTRAINT FK_histmnt_ot FOREIGN KEY (orden_trabajo_id) 
        REFERENCES mnt_orden_trabajo(orden_trabajo_id) ON DELETE NO ACTION,
    CONSTRAINT FK_histmnt_moneda FOREIGN KEY (moneda_id)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_histmnt_empresa ON mnt_historial_mantenimiento(empresa_id, fecha_mantenimiento DESC);
CREATE INDEX IDX_histmnt_activo ON mnt_historial_mantenimiento(activo_id, fecha_mantenimiento DESC);
CREATE INDEX IDX_histmnt_fecha ON mnt_historial_mantenimiento(fecha_mantenimiento DESC);