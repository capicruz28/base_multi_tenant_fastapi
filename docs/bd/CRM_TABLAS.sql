-- ============================================================================
-- SECCIÓN 12: CRM - CUSTOMER RELATIONSHIP MANAGEMENT
-- ============================================================================
-- DESCRIPCIÓN: Gestión de relaciones con clientes, oportunidades, seguimiento
-- DEPENDENCIAS: ORG, SLS (clientes)
-- USADO POR: SLS (pipeline de ventas)
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: crm_campana
-- Descripción: Campañas de marketing/ventas
-- Uso: Organizar esfuerzos comerciales por campaña
-- Relaciones: Agrupa leads y oportunidades
-- -----------------------------------------------------------------------------
CREATE TABLE crm_campana (
    campana_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_campana NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(150) NOT NULL,
    descripcion NVARCHAR(500) NULL,
    
    -- Tipo y objetivo
    tipo_campana NVARCHAR(30) NOT NULL,                       -- 'email', 'telemarketing', 'evento', 'digital', 'mixta'
    objetivo NVARCHAR(500) NULL,
    
    -- Periodo
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NULL,
    
    -- Presupuesto
    presupuesto DECIMAL(18,2) NULL,
    gasto_real DECIMAL(18,2) DEFAULT 0,
    moneda_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Responsable
    responsable_usuario_id UNIQUEIDENTIFIER NULL,
    responsable_nombre NVARCHAR(150) NULL,
    
    -- Métricas
    total_contactos INT DEFAULT 0,
    total_leads_generados INT DEFAULT 0,
    total_oportunidades INT DEFAULT 0,
    total_ventas_cerradas INT DEFAULT 0,
    monto_ventas_cerradas DECIMAL(18,2) DEFAULT 0,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'planificada',                -- 'planificada', 'activa', 'pausada', 'completada', 'cancelada'
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_campana_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_campana_codigo UNIQUE (cliente_id, empresa_id, codigo_campana),
    CONSTRAINT FK_campana_moneda FOREIGN KEY (moneda_id)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_campana_empresa ON crm_campana(empresa_id, estado);
CREATE INDEX IDX_campana_fecha ON crm_campana(fecha_inicio DESC);

-- -----------------------------------------------------------------------------
-- Tabla: crm_lead
-- Descripción: Leads/Prospectos (clientes potenciales)
-- Uso: Contactos que aún no son clientes
-- Relaciones: Se convierte en cliente o se descarta
-- -----------------------------------------------------------------------------
CREATE TABLE crm_lead (
    lead_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Datos básicos
    nombre_completo NVARCHAR(200) NOT NULL,
    empresa_nombre NVARCHAR(200) NULL,
    cargo NVARCHAR(100) NULL,
    
    -- Contacto
    telefono NVARCHAR(20) NULL,
    telefono_movil NVARCHAR(20) NULL,
    email NVARCHAR(100) NULL,
    
    -- Dirección
    direccion NVARCHAR(255) NULL,
    ciudad NVARCHAR(100) NULL,
    pais_id UNIQUEIDENTIFIER NULL,
    
    -- Origen
    origen_lead NVARCHAR(30) NOT NULL,                        -- 'web', 'telefono', 'referido', 'evento', 'campana', 'redes_sociales'
    campana_id UNIQUEIDENTIFIER NULL,
    referido_por NVARCHAR(150) NULL,
    
    -- Calificación
    calificacion NVARCHAR(20) DEFAULT 'frio',                 -- 'caliente', 'tibio', 'frio'
    puntuacion INT DEFAULT 0,                                  -- Lead scoring (0-100)
    
    -- Asignación
    asignado_vendedor_usuario_id UNIQUEIDENTIFIER NULL,
    asignado_vendedor_nombre NVARCHAR(150) NULL,
    fecha_asignacion DATETIME NULL,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'nuevo',                      -- 'nuevo', 'contactado', 'calificado', 'convertido', 'descartado'
    fecha_primer_contacto DATETIME NULL,
    fecha_ultimo_contacto DATETIME NULL,
    
    -- Conversión
    convertido_cliente BIT DEFAULT 0,
    cliente_venta_id UNIQUEIDENTIFIER NULL,
    fecha_conversion DATETIME NULL,
    
    motivo_descarte NVARCHAR(500) NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_lead_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_lead_campana FOREIGN KEY (campana_id) 
        REFERENCES crm_campana(campana_id) ON DELETE NO ACTION,
    CONSTRAINT FK_lead_cliente FOREIGN KEY (cliente_venta_id) 
        REFERENCES sls_cliente(cliente_venta_id) ON DELETE NO ACTION,
    CONSTRAINT FK_lead_pais FOREIGN KEY (pais_id) 
        REFERENCES cat_pais(pais_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_lead_empresa ON crm_lead(empresa_id, estado);
CREATE INDEX IDX_lead_vendedor ON crm_lead(asignado_vendedor_usuario_id, estado) 
    WHERE asignado_vendedor_usuario_id IS NOT NULL;
CREATE INDEX IDX_lead_calificacion ON crm_lead(calificacion, puntuacion DESC);

-- -----------------------------------------------------------------------------
-- Tabla: crm_oportunidad
-- Descripción: Oportunidades de venta (pipeline comercial)
-- Uso: Seguimiento de potenciales ventas con etapas
-- Relaciones: Vinculada a cliente, puede generar cotización/pedido
-- -----------------------------------------------------------------------------
CREATE TABLE crm_oportunidad (
    oportunidad_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_oportunidad NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(200) NOT NULL,
    descripcion NVARCHAR(MAX) NULL,
    
    -- Cliente o Lead
    cliente_venta_id UNIQUEIDENTIFIER NULL,
    lead_id UNIQUEIDENTIFIER NULL,
    nombre_cliente_prospecto NVARCHAR(200) NULL,
    
    -- Vendedor
    vendedor_usuario_id UNIQUEIDENTIFIER NOT NULL,
    vendedor_nombre NVARCHAR(150) NULL,
    
    -- Campaña origen
    campana_id UNIQUEIDENTIFIER NULL,
    
    -- Valor estimado
    monto_estimado DECIMAL(18,2) NOT NULL,
    moneda_id UNIQUEIDENTIFIER NOT NULL,
    probabilidad_cierre DECIMAL(5,2) DEFAULT 50,              -- % probabilidad de ganar
    valor_ponderado AS (monto_estimado * probabilidad_cierre / 100) PERSISTED,
    
    -- Fechas
    fecha_apertura DATE DEFAULT GETDATE() NOT NULL,
    fecha_cierre_estimada DATE NULL,
    fecha_cierre_real DATE NULL,
    
    -- Etapa del pipeline
    etapa NVARCHAR(30) NOT NULL,                              -- 'calificacion', 'necesidad_analisis', 'propuesta', 'negociacion', 'cierre'
    etapa_anterior NVARCHAR(30) NULL,
    fecha_cambio_etapa DATETIME NULL,
    
    -- Tipo
    tipo_oportunidad NVARCHAR(30) NULL,                       -- 'nuevo_negocio', 'upselling', 'cross_selling', 'renovacion'
    
    -- Productos de interés
    productos_interes NVARCHAR(MAX) NULL,                     -- JSON con productos
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'abierta',                    -- 'abierta', 'ganada', 'perdida', 'cancelada'
    motivo_ganada NVARCHAR(500) NULL,
    motivo_perdida NVARCHAR(500) NULL,
    competidor NVARCHAR(150) NULL,                            -- Si se perdió contra competencia
    
    -- Conversión
    cotizacion_generada BIT DEFAULT 0,
    cotizacion_id UNIQUEIDENTIFIER NULL,
    pedido_generado BIT DEFAULT 0,
    pedido_id UNIQUEIDENTIFIER NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    proxima_accion NVARCHAR(500) NULL,
    fecha_proxima_accion DATE NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_opor_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_opor_cliente FOREIGN KEY (cliente_venta_id) 
        REFERENCES sls_cliente(cliente_venta_id) ON DELETE NO ACTION,
    CONSTRAINT FK_opor_lead FOREIGN KEY (lead_id) 
        REFERENCES crm_lead(lead_id) ON DELETE NO ACTION,
    CONSTRAINT FK_opor_campana FOREIGN KEY (campana_id) 
        REFERENCES crm_campana(campana_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_opor_numero UNIQUE (cliente_id, empresa_id, numero_oportunidad),
    CONSTRAINT FK_opor_moneda FOREIGN KEY (moneda_id)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_opor_empresa ON crm_oportunidad(empresa_id, estado);
CREATE INDEX IDX_opor_vendedor ON crm_oportunidad(vendedor_usuario_id, estado);
CREATE INDEX IDX_opor_etapa ON crm_oportunidad(etapa, estado);
CREATE INDEX IDX_opor_cierre ON crm_oportunidad(fecha_cierre_estimada, estado);

-- -----------------------------------------------------------------------------
-- Tabla: crm_actividad
-- Descripción: Actividades de seguimiento (llamadas, reuniones, emails)
-- Uso: Registro de interacciones con clientes/leads
-- Relaciones: Vinculada a leads, oportunidades, clientes
-- -----------------------------------------------------------------------------
CREATE TABLE crm_actividad (
    actividad_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Tipo de actividad
    tipo_actividad NVARCHAR(30) NOT NULL,                     -- 'llamada', 'reunion', 'email', 'visita', 'demo', 'cotizacion_enviada'
    asunto NVARCHAR(200) NOT NULL,
    descripcion NVARCHAR(MAX) NULL,
    
    -- Relación con entidades
    lead_id UNIQUEIDENTIFIER NULL,
    oportunidad_id UNIQUEIDENTIFIER NULL,
    cliente_venta_id UNIQUEIDENTIFIER NULL,
    
    -- Fechas
    fecha_actividad DATETIME NOT NULL,
    duracion_minutos INT NULL,
    
    -- Responsable
    usuario_responsable_id UNIQUEIDENTIFIER NOT NULL,
    responsable_nombre NVARCHAR(150) NULL,
    
    -- Resultado
    resultado NVARCHAR(30) NULL,                              -- 'exitosa', 'sin_respuesta', 'reagendar', 'no_interesado'
    
    -- Seguimiento
    requiere_seguimiento BIT DEFAULT 0,
    fecha_seguimiento DATE NULL,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'planificada',                -- 'planificada', 'completada', 'cancelada'
    fecha_completado DATETIME NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_activ_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_activ_lead FOREIGN KEY (lead_id) 
        REFERENCES crm_lead(lead_id) ON DELETE NO ACTION,
    CONSTRAINT FK_activ_opor FOREIGN KEY (oportunidad_id) 
        REFERENCES crm_oportunidad(oportunidad_id) ON DELETE NO ACTION,
    CONSTRAINT FK_activ_cliente FOREIGN KEY (cliente_venta_id) 
        REFERENCES sls_cliente(cliente_venta_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_activ_empresa ON crm_actividad(empresa_id, fecha_actividad DESC);
CREATE INDEX IDX_activ_responsable ON crm_actividad(usuario_responsable_id, estado, fecha_actividad);
CREATE INDEX IDX_activ_lead ON crm_actividad(lead_id) WHERE lead_id IS NOT NULL;
CREATE INDEX IDX_activ_opor ON crm_actividad(oportunidad_id) WHERE oportunidad_id IS NOT NULL;