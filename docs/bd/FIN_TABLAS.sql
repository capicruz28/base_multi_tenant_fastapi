-- ============================================================================
-- SECCIÓN 17: FIN - FINANZAS Y CONTABILIDAD
-- ============================================================================
-- DESCRIPCIÓN: Contabilidad general, plan de cuentas, asientos contables
-- DEPENDENCIAS: ORG
-- USADO POR: Todos los módulos operativos generan movimientos contables
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: fin_plan_cuentas
-- Descripción: Plan contable de cuentas
-- Uso: Catálogo de cuentas contables (activo, pasivo, patrimonio, ingresos, gastos)
-- Relaciones: Base de la contabilidad
-- -----------------------------------------------------------------------------
CREATE TABLE fin_plan_cuentas (
    cuenta_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_cuenta NVARCHAR(20) NOT NULL,                      -- Ej: "101", "4011", "60111"
    nombre_cuenta NVARCHAR(200) NOT NULL,
    descripcion NVARCHAR(500) NULL,
    
    -- Jerarquía
    cuenta_padre_id UNIQUEIDENTIFIER NULL,
    nivel INT DEFAULT 1,                                       -- 1=Clase, 2=Grupo, 3=Subcuenta, etc
    ruta_jerarquica NVARCHAR(500) NULL,
    
    -- Clasificación
    tipo_cuenta NVARCHAR(20) NOT NULL,                        -- 'activo', 'pasivo', 'patrimonio', 'ingreso', 'gasto'
    categoria NVARCHAR(30) NULL,                              -- 'corriente', 'no_corriente', 'fijo', etc
    naturaleza NVARCHAR(10) NOT NULL,                         -- 'deudora', 'acreedora'
    
    -- Configuración
    acepta_movimientos BIT DEFAULT 1,                         -- Si acepta registros directos (detalle) o solo agrupación
    requiere_centro_costo BIT DEFAULT 0,
    requiere_documento_referencia BIT DEFAULT 0,
    requiere_tercero BIT DEFAULT 0,
    
    -- Moneda
    acepta_moneda_extranjera BIT DEFAULT 1,
    
    -- Estado Financiero
    aparece_balance BIT DEFAULT 1,
    aparece_pyg BIT DEFAULT 0,                                -- Estado de Resultados (P&G)
    
    -- Código SUNAT (para reportes tributarios)
    codigo_sunat NVARCHAR(10) NULL,
    
    -- Estado
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_cuenta_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cuenta_padre FOREIGN KEY (cuenta_padre_id) 
        REFERENCES fin_plan_cuentas(cuenta_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_cuenta_codigo UNIQUE (cliente_id, empresa_id, codigo_cuenta)
);

CREATE INDEX IDX_cuenta_empresa ON fin_plan_cuentas(empresa_id, es_activo);
CREATE INDEX IDX_cuenta_padre ON fin_plan_cuentas(cuenta_padre_id);
CREATE INDEX IDX_cuenta_tipo ON fin_plan_cuentas(tipo_cuenta, nivel);

-- -----------------------------------------------------------------------------
-- Tabla: fin_periodo_contable
-- Descripción: Periodos contables (meses/años)
-- Uso: Control de apertura/cierre de periodos
-- Relaciones: Controla en qué periodos se puede contabilizar
-- -----------------------------------------------------------------------------
CREATE TABLE fin_periodo_contable (
    periodo_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    año INT NOT NULL,
    mes INT NOT NULL,
    nombre_periodo AS (
        CAST(año AS NVARCHAR) + '-' + 
        RIGHT('0' + CAST(mes AS NVARCHAR), 2)
    ) PERSISTED,
    
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    
    estado NVARCHAR(20) DEFAULT 'abierto',                    -- 'abierto', 'cerrado', 'bloqueado'
    fecha_cierre DATETIME NULL,
    cerrado_por_usuario_id UNIQUEIDENTIFIER NULL,
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_periodo_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_periodo UNIQUE (cliente_id, empresa_id, año, mes)
);

CREATE INDEX IDX_periodo_empresa ON fin_periodo_contable(empresa_id, año DESC, mes DESC);

-- -----------------------------------------------------------------------------
-- Tabla: fin_asiento_contable
-- Descripción: Asientos contables (cabecera)
-- Uso: Registro de transacciones contables
-- Relaciones: Generado por módulos operativos o manual
-- -----------------------------------------------------------------------------
CREATE TABLE fin_asiento_contable (
    asiento_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_asiento NVARCHAR(20) NOT NULL,
    fecha_asiento DATE NOT NULL,
    periodo_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Tipo
    tipo_asiento NVARCHAR(30) NOT NULL,                       -- 'apertura', 'diario', 'ajuste', 'cierre', 'provision'
    
    -- Origen
    modulo_origen NVARCHAR(10) NULL,                          -- 'PUR', 'SLS', 'HCM', 'INV', 'FIN' (manual)
    documento_origen_tipo NVARCHAR(30) NULL,
    documento_origen_id UNIQUEIDENTIFIER NULL,
    documento_origen_numero NVARCHAR(30) NULL,
    
    -- Descripción
    glosa NVARCHAR(500) NOT NULL,
    
    -- Montos
    moneda_id UNIQUEIDENTIFIER NOT NULL,                      -- FK a cat_moneda (CAMBIADO)
    tipo_cambio DECIMAL(10,4) DEFAULT 1,
    total_debe DECIMAL(18,2) DEFAULT 0,
    total_haber DECIMAL(18,2) DEFAULT 0,
    diferencia AS (ABS(total_debe - total_haber)) PERSISTED,
    esta_cuadrado AS (
        CASE WHEN ABS(total_debe - total_haber) < 0.01 THEN 1 ELSE 0 END
    ) PERSISTED,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'borrador',                   -- 'borrador', 'registrado', 'aprobado', 'anulado'
    requiere_aprobacion BIT DEFAULT 0,
    aprobado_por_usuario_id UNIQUEIDENTIFIER NULL,
    fecha_aprobacion DATETIME NULL,
    
    -- Anulación
    fecha_anulacion DATETIME NULL,
    motivo_anulacion NVARCHAR(500) NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_asiento_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_asiento_periodo FOREIGN KEY (periodo_id) 
        REFERENCES fin_periodo_contable(periodo_id) ON DELETE NO ACTION,
    CONSTRAINT FK_asiento_moneda FOREIGN KEY (moneda_id)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_asiento_numero UNIQUE (cliente_id, empresa_id, numero_asiento)
);

CREATE INDEX IDX_asiento_empresa ON fin_asiento_contable(empresa_id, fecha_asiento DESC);
CREATE INDEX IDX_asiento_periodo ON fin_asiento_contable(periodo_id, estado);
CREATE INDEX IDX_asiento_estado ON fin_asiento_contable(estado, fecha_asiento DESC);

-- -----------------------------------------------------------------------------
-- Tabla: fin_asiento_detalle
-- Descripción: Detalle de asientos (debe y haber por cuenta)
-- Uso: Movimientos individuales del asiento
-- Relaciones: Detalle de fin_asiento_contable
-- -----------------------------------------------------------------------------
CREATE TABLE fin_asiento_detalle (
    asiento_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    asiento_id UNIQUEIDENTIFIER NOT NULL,
    
    item INT NOT NULL,
    cuenta_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Montos
    debe DECIMAL(18,2) DEFAULT 0,
    haber DECIMAL(18,2) DEFAULT 0,
    
    -- Moneda extranjera (si aplica)
    debe_me DECIMAL(18,2) DEFAULT 0,                          -- Moneda extranjera
    haber_me DECIMAL(18,2) DEFAULT 0,
    
    -- Glosa específica de la línea
    glosa NVARCHAR(500) NULL,
    
    -- Referencias
    centro_costo_id UNIQUEIDENTIFIER NULL,
    documento_referencia NVARCHAR(50) NULL,
    
    -- Tercero (cliente/proveedor/empleado)
    tercero_tipo NVARCHAR(20) NULL,                           -- 'cliente', 'proveedor', 'empleado'
    tercero_id UNIQUEIDENTIFIER NULL,
    tercero_nombre NVARCHAR(200) NULL,
    tercero_documento NVARCHAR(20) NULL,
    
    -- Fecha de vencimiento (para cuentas por cobrar/pagar)
    fecha_vencimiento DATE NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_asientodet_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_asientodet_asiento FOREIGN KEY (asiento_id) 
        REFERENCES fin_asiento_contable(asiento_id) ON DELETE NO ACTION,
    CONSTRAINT FK_asientodet_cuenta FOREIGN KEY (cuenta_id) 
        REFERENCES fin_plan_cuentas(cuenta_id) ON DELETE NO ACTION,
    CONSTRAINT FK_asientodet_cc FOREIGN KEY (centro_costo_id) 
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_asientodet_empresa ON fin_asiento_detalle(empresa_id);
CREATE INDEX IDX_asientodet_asiento ON fin_asiento_detalle(asiento_id, item);
CREATE INDEX IDX_asientodet_cuenta ON fin_asiento_detalle(cuenta_id);
CREATE INDEX IDX_asientodet_cc ON fin_asiento_detalle(centro_costo_id) WHERE centro_costo_id IS NOT NULL;