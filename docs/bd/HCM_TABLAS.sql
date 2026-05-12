-- ============================================================================
-- SECCIÓN 16: HCM - HUMAN CAPITAL MANAGEMENT (PLANILLAS Y RRHH)
-- ============================================================================
-- DESCRIPCIÓN: Gestión de empleados, contratos, planillas, asistencia
-- DEPENDENCIAS: ORG (departamentos, cargos, centros de costo)
-- USADO POR: FIN (contabilidad de planilla), CST (costos laborales)
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: hcm_empleado
-- Descripción: Maestro de empleados
-- Uso: Datos personales y laborales del personal
-- Relaciones: Base del módulo HCM
-- -----------------------------------------------------------------------------
CREATE TABLE hcm_empleado (
    empleado_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Identificación
    codigo_empleado NVARCHAR(20) NOT NULL,
    
    -- Datos personales
    tipo_documento NVARCHAR(10) DEFAULT 'DNI',                -- 'DNI', 'CE', 'PASAPORTE'
    numero_documento NVARCHAR(20) NOT NULL,
    apellido_paterno NVARCHAR(100) NOT NULL,
    apellido_materno NVARCHAR(100) NOT NULL,
    nombres NVARCHAR(150) NOT NULL,
    nombre_completo AS (apellido_paterno + ' ' + apellido_materno + ', ' + nombres) PERSISTED,
    
    fecha_nacimiento DATE NOT NULL,
    sexo NVARCHAR(1) NOT NULL,                                -- 'M', 'F'
    estado_civil NVARCHAR(20) NULL,                           -- 'soltero', 'casado', 'divorciado', 'viudo'
    nacionalidad NVARCHAR(50) DEFAULT 'Peruana',
    
    -- Dirección
    direccion NVARCHAR(255) NULL,
    departamento NVARCHAR(50) NULL,
    provincia NVARCHAR(50) NULL,
    distrito NVARCHAR(50) NULL,
    ubigeo NVARCHAR(6) NULL,
    
    -- Contacto
    telefono_fijo NVARCHAR(20) NULL,
    telefono_movil NVARCHAR(20) NULL,
    email_personal NVARCHAR(100) NULL,
    email_corporativo NVARCHAR(100) NULL,
    
    -- Contacto de emergencia
    contacto_emergencia_nombre NVARCHAR(150) NULL,
    contacto_emergencia_relacion NVARCHAR(50) NULL,
    contacto_emergencia_telefono NVARCHAR(20) NULL,
    
    -- Datos laborales
    fecha_ingreso DATE NOT NULL,
    fecha_cese DATE NULL,
    motivo_cese NVARCHAR(500) NULL,
    
    -- Organización
    departamento_id UNIQUEIDENTIFIER NULL,
    cargo_id UNIQUEIDENTIFIER NULL,
    sucursal_id UNIQUEIDENTIFIER NULL,
    centro_costo_id UNIQUEIDENTIFIER NULL,
    
    -- Jefe directo
    jefe_inmediato_empleado_id UNIQUEIDENTIFIER NULL,
    jefe_inmediato_nombre NVARCHAR(150) NULL,
    
    -- Tipo de empleado
    tipo_empleado NVARCHAR(30) DEFAULT 'empleado',            -- 'empleado', 'obrero', 'practicante', 'tercero'
    categoria NVARCHAR(30) NULL,                              -- Personalizable
    
    -- Datos bancarios
    banco NVARCHAR(100) NULL,
    tipo_cuenta NVARCHAR(20) NULL,                            -- 'ahorro', 'corriente'
    numero_cuenta NVARCHAR(30) NULL,
    cci NVARCHAR(20) NULL,
    
    -- AFP/ONP
    sistema_pensionario NVARCHAR(10) NOT NULL,                -- 'AFP', 'ONP'
    afp_nombre NVARCHAR(50) NULL,
    cuspp NVARCHAR(12) NULL,                                  -- Código único AFP
    fecha_afiliacion_afp DATE NULL,
    tipo_comision_afp NVARCHAR(20) NULL,                      -- 'flujo', 'mixta'
    
    -- Seguro de salud
    essalud BIT DEFAULT 1,
    eps_nombre NVARCHAR(100) NULL,
    
    -- SCTR (Seguro Complementario de Trabajo de Riesgo)
    tiene_sctr BIT DEFAULT 0,
    sctr_pension BIT DEFAULT 0,
    sctr_salud BIT DEFAULT 0,
    
    -- Datos adicionales
    nivel_educacion NVARCHAR(50) NULL,                        -- 'secundaria', 'tecnico', 'universitario', 'posgrado'
    profesion NVARCHAR(100) NULL,
    tiene_hijos BIT DEFAULT 0,
    numero_hijos INT DEFAULT 0,
    
    -- Discapacidad
    tiene_discapacidad BIT DEFAULT 0,
    tipo_discapacidad NVARCHAR(100) NULL,
    
    -- Foto
    foto_url NVARCHAR(500) NULL,
    
    -- Usuario del sistema (si tiene acceso)
    usuario_id UNIQUEIDENTIFIER NULL,                         -- FK a usuario (tabla de autenticación)
    
    -- Estado
    estado_empleado NVARCHAR(20) DEFAULT 'activo',            -- 'activo', 'inactivo', 'suspendido', 'cesado'
    es_activo BIT DEFAULT 1 NOT NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_emp_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_emp_dpto FOREIGN KEY (departamento_id) 
        REFERENCES org_departamento(departamento_id) ON DELETE NO ACTION,
    CONSTRAINT FK_emp_cargo FOREIGN KEY (cargo_id) 
        REFERENCES org_cargo(cargo_id) ON DELETE NO ACTION,
    CONSTRAINT FK_emp_sucursal FOREIGN KEY (sucursal_id) 
        REFERENCES org_sucursal(sucursal_id) ON DELETE NO ACTION,
    CONSTRAINT FK_emp_cc FOREIGN KEY (centro_costo_id) 
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE NO ACTION,
    CONSTRAINT FK_emp_jefe FOREIGN KEY (jefe_inmediato_empleado_id) 
        REFERENCES hcm_empleado(empleado_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_emp_codigo UNIQUE (cliente_id, empresa_id, codigo_empleado),
    CONSTRAINT UQ_emp_documento UNIQUE (cliente_id, empresa_id, tipo_documento, numero_documento)
);

CREATE INDEX IDX_emp_empresa ON hcm_empleado(empresa_id, es_activo);
CREATE INDEX IDX_emp_documento ON hcm_empleado(numero_documento);
CREATE INDEX IDX_emp_nombre ON hcm_empleado(apellido_paterno, apellido_materno, nombres);
CREATE INDEX IDX_emp_dpto ON hcm_empleado(departamento_id) WHERE departamento_id IS NOT NULL;
CREATE INDEX IDX_emp_cargo ON hcm_empleado(cargo_id) WHERE cargo_id IS NOT NULL;
CREATE INDEX IDX_emp_estado ON hcm_empleado(estado_empleado, fecha_ingreso);

-- -----------------------------------------------------------------------------
-- Tabla: hcm_contrato
-- Descripción: Contratos laborales de empleados
-- Uso: Historial de contratos (puede tener múltiples contratos)
-- Relaciones: Asociado a empleado
-- -----------------------------------------------------------------------------
CREATE TABLE hcm_contrato (
    contrato_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    empleado_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_contrato NVARCHAR(20) NOT NULL,
    
    -- Tipo de contrato
    tipo_contrato NVARCHAR(30) NOT NULL,                      -- 'plazo_indeterminado', 'plazo_fijo', 'part_time', 'locacion_servicios', 'practicas'
    modalidad_contrato NVARCHAR(50) NULL,                     -- 'tiempo_completo', 'tiempo_parcial', 'por_horas'
    
    -- Vigencia
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NULL,                                      -- NULL si es indeterminado
    duracion_meses INT NULL,
    es_contrato_vigente BIT DEFAULT 1,
    
    -- Cargo y remuneración
    cargo_id UNIQUEIDENTIFIER NULL,
    cargo_descripcion NVARCHAR(150) NULL,
    
    remuneracion_basica DECIMAL(12,2) NOT NULL,
    moneda_id UNIQUEIDENTIFIER NOT NULL,
    tipo_remuneracion NVARCHAR(20) DEFAULT 'mensual',         -- 'mensual', 'quincenal', 'semanal', 'diario', 'por_hora'
    
    -- Jornada laboral
    horas_semanales DECIMAL(5,2) DEFAULT 48,
    dias_laborables INT DEFAULT 6,                            -- Días por semana
    
    -- Periodo de prueba
    tiene_periodo_prueba BIT DEFAULT 1,
    duracion_prueba_meses INT DEFAULT 3,
    fecha_fin_prueba DATE NULL,
    
    -- Beneficios
    tiene_cts BIT DEFAULT 1,
    tiene_gratificacion BIT DEFAULT 1,
    tiene_asignacion_familiar BIT DEFAULT 0,
    tiene_movilidad BIT DEFAULT 0,
    monto_movilidad DECIMAL(10,2) NULL,
    
    -- Renovaciones
    contrato_renovado_desde_id UNIQUEIDENTIFIER NULL,         -- Si es renovación
    numero_renovaciones INT DEFAULT 0,
    
    -- Documentos
    archivo_contrato_url NVARCHAR(500) NULL,
    
    -- Estado
    estado_contrato NVARCHAR(20) DEFAULT 'vigente',           -- 'borrador', 'vigente', 'vencido', 'rescindido'
    fecha_rescision DATE NULL,
    motivo_rescision NVARCHAR(500) NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    clausulas_especiales NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_contrato_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_contrato_empleado FOREIGN KEY (empleado_id) 
        REFERENCES hcm_empleado(empleado_id) ON DELETE NO ACTION,
    CONSTRAINT FK_contrato_cargo FOREIGN KEY (cargo_id) 
        REFERENCES org_cargo(cargo_id) ON DELETE NO ACTION,
    CONSTRAINT FK_contrato_renovado FOREIGN KEY (contrato_renovado_desde_id) 
        REFERENCES hcm_contrato(contrato_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_contrato_numero UNIQUE (cliente_id, empresa_id, numero_contrato),
    CONSTRAINT FK_contrato_moneda FOREIGN KEY (moneda_id)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_contrato_empresa ON hcm_contrato(empresa_id, fecha_inicio DESC);
CREATE INDEX IDX_contrato_empleado ON hcm_contrato(empleado_id, es_contrato_vigente);
CREATE INDEX IDX_contrato_vigencia ON hcm_contrato(fecha_inicio, fecha_fin, estado_contrato);

-- -----------------------------------------------------------------------------
-- Tabla: hcm_concepto_planilla
-- Descripción: Catálogo de conceptos (ingresos, descuentos, aportes)
-- Uso: Define qué conceptos se pueden usar en planilla
-- Relaciones: Usado en hcm_planilla_detalle
-- -----------------------------------------------------------------------------
CREATE TABLE hcm_concepto_planilla (
    concepto_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_concepto NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(255) NULL,
    
    -- Clasificación
    tipo_concepto NVARCHAR(20) NOT NULL,                      -- 'ingreso', 'descuento', 'aporte_empleador'
    categoria NVARCHAR(50) NULL,                              -- 'remuneracion', 'bonificacion', 'aporte_afp', 'aporte_essalud', etc
    
    -- Configuración
    es_fijo BIT DEFAULT 0,                                    -- Si es monto fijo o variable
    monto_fijo DECIMAL(12,2) NULL,
    
    es_porcentaje BIT DEFAULT 0,                              -- Si se calcula como %
    porcentaje_base DECIMAL(5,2) NULL,
    base_calculo NVARCHAR(30) NULL,                           -- 'remuneracion_basica', 'total_ingresos', 'rem_minima_vital'
    
    -- Afectaciones
    afecto_renta_quinta BIT DEFAULT 1,                        -- Si afecta al cálculo de renta 5ta
    afecto_essalud BIT DEFAULT 1,
    afecto_cts BIT DEFAULT 1,
    afecto_gratificacion BIT DEFAULT 1,
    afecto_vacaciones BIT DEFAULT 1,
    
    -- PLAME (T-Registro)
    codigo_plame NVARCHAR(10) NULL,                           -- Código para reporte PLAME
    
    -- Contable
    cuenta_contable NVARCHAR(20) NULL,                        -- Para integración con FIN
    
    -- Estado
    es_concepto_sistema BIT DEFAULT 0,                        -- Si es concepto predefinido
    es_activo BIT DEFAULT 1 NOT NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_concepto_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_concepto_codigo UNIQUE (cliente_id, empresa_id, codigo_concepto)
);

CREATE INDEX IDX_concepto_empresa ON hcm_concepto_planilla(empresa_id, es_activo);
CREATE INDEX IDX_concepto_tipo ON hcm_concepto_planilla(tipo_concepto, categoria);

-- -----------------------------------------------------------------------------
-- Tabla: hcm_planilla
-- Descripción: Planilla mensual de remuneraciones
-- Uso: Cabecera de planilla por periodo
-- Relaciones: Agrupa conceptos de empleados
-- -----------------------------------------------------------------------------
CREATE TABLE hcm_planilla (
    planilla_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_planilla NVARCHAR(20) NOT NULL,
    
    -- Periodo
    año INT NOT NULL,
    mes INT NOT NULL,
    periodo_descripcion NVARCHAR(50) NULL,                    -- Ej: "Enero 2026", "Quincena 1 Feb 2026"
    
    -- Tipo de planilla
    tipo_planilla NVARCHAR(20) DEFAULT 'mensual',             -- 'mensual', 'quincenal', 'gratificacion', 'cts', 'utilidades'
    
    -- Fechas
    fecha_inicio_periodo DATE NOT NULL,
    fecha_fin_periodo DATE NOT NULL,
    fecha_pago DATE NULL,

    -- Totales MULTI-MONEDA (OPCIONAL - MODIFICADO)
    moneda_id UNIQUEIDENTIFIER NULL,                          -- FK a cat_moneda (NUEVO - opcional)
    tipo_cambio DECIMAL(10,4) DEFAULT 1,                      -- NUEVO
    
    -- Totales
    total_empleados INT DEFAULT 0,
    total_ingresos DECIMAL(18,2) DEFAULT 0,
    total_descuentos DECIMAL(18,2) DEFAULT 0,
    total_neto DECIMAL(18,2) DEFAULT 0,
    total_aportes_empleador DECIMAL(18,2) DEFAULT 0,
    total_planilla AS (total_neto + total_aportes_empleador) PERSISTED,
    
    -- Centro de costo (si aplica a nivel planilla)
    centro_costo_id UNIQUEIDENTIFIER NULL,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'borrador',                   -- 'borrador', 'calculada', 'aprobada', 'pagada', 'cerrada'
    fecha_aprobacion DATETIME NULL,
    aprobado_por_usuario_id UNIQUEIDENTIFIER NULL,
    
    -- PLAME
    generado_plame BIT DEFAULT 0,
    fecha_generacion_plame DATETIME NULL,
    archivo_plame_url NVARCHAR(500) NULL,
    
    -- Asiento contable
    asiento_contable_generado BIT DEFAULT 0,
    asiento_contable_id UNIQUEIDENTIFIER NULL,                -- FK a fin_asiento_contable
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_planilla_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_planilla_cc FOREIGN KEY (centro_costo_id) 
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE NO ACTION,
    CONSTRAINT FK_planilla_moneda FOREIGN KEY (moneda_id)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_planilla_numero UNIQUE (cliente_id, empresa_id, numero_planilla),
    CONSTRAINT UQ_planilla_periodo UNIQUE (cliente_id, empresa_id, tipo_planilla, año, mes)
);

CREATE INDEX IDX_planilla_empresa ON hcm_planilla(empresa_id, año DESC, mes DESC);
CREATE INDEX IDX_planilla_estado ON hcm_planilla(estado, fecha_pago);

-- -----------------------------------------------------------------------------
-- Tabla: hcm_planilla_empleado
-- Descripción: Resumen de planilla por empleado
-- Uso: Boleta de pago de cada empleado
-- Relaciones: Empleados incluidos en la planilla
-- -----------------------------------------------------------------------------
CREATE TABLE hcm_planilla_empleado (
    planilla_empleado_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    planilla_id UNIQUEIDENTIFIER NOT NULL,
    empleado_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Datos laborales del periodo
    cargo_descripcion NVARCHAR(150) NULL,
    departamento_nombre NVARCHAR(100) NULL,
    
    -- Días trabajados
    dias_laborados INT DEFAULT 30,
    dias_subsidio INT DEFAULT 0,                              -- Por enfermedad, etc
    dias_vacaciones INT DEFAULT 0,
    dias_faltas INT DEFAULT 0,
    
    -- Horas (si aplica)
    horas_ordinarias DECIMAL(10,2) DEFAULT 0,
    horas_extras_25 DECIMAL(10,2) DEFAULT 0,                  -- 25% adicional
    horas_extras_35 DECIMAL(10,2) DEFAULT 0,                  -- 35% adicional
    horas_extras_100 DECIMAL(10,2) DEFAULT 0,                 -- 100% adicional (feriados)
    
    -- Remuneración base
    remuneracion_basica DECIMAL(12,2) NOT NULL,
    
    -- Totales
    total_ingresos DECIMAL(12,2) DEFAULT 0,
    total_descuentos DECIMAL(12,2) DEFAULT 0,
    total_neto DECIMAL(12,2) DEFAULT 0,
    total_aportes_empleador DECIMAL(12,2) DEFAULT 0,
    
    -- Neto a pagar
    neto_pagar AS (total_ingresos - total_descuentos) PERSISTED,
    
    -- Pagado
    fecha_pago DATETIME NULL,
    pagado BIT DEFAULT 0,
    metodo_pago NVARCHAR(30) NULL,                            -- 'transferencia', 'cheque', 'efectivo'
    numero_operacion NVARCHAR(50) NULL,
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_planemp_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_planemp_planilla FOREIGN KEY (planilla_id) 
        REFERENCES hcm_planilla(planilla_id) ON DELETE NO ACTION,
    CONSTRAINT FK_planemp_empleado FOREIGN KEY (empleado_id) 
        REFERENCES hcm_empleado(empleado_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_planemp UNIQUE (cliente_id, planilla_id, empleado_id)
);

CREATE INDEX IDX_planemp_empresa ON hcm_planilla_empleado(empresa_id);
CREATE INDEX IDX_planemp_planilla ON hcm_planilla_empleado(planilla_id);
CREATE INDEX IDX_planemp_empleado ON hcm_planilla_empleado(empleado_id);

-- -----------------------------------------------------------------------------
-- Tabla: hcm_planilla_detalle
-- Descripción: Conceptos aplicados a cada empleado en planilla
-- Uso: Detalle de ingresos, descuentos y aportes
-- Relaciones: Detalle de hcm_planilla_empleado
-- -----------------------------------------------------------------------------
CREATE TABLE hcm_planilla_detalle (
    planilla_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    planilla_empleado_id UNIQUEIDENTIFIER NOT NULL,
    concepto_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Tipo
    tipo_concepto NVARCHAR(20) NOT NULL,                      -- 'ingreso', 'descuento', 'aporte_empleador'
    
    -- Cálculo
    base_calculo DECIMAL(12,2) NULL,                          -- Base sobre la que se calculó
    cantidad DECIMAL(10,2) DEFAULT 1,                         -- Ej: días, horas
    tasa_porcentaje DECIMAL(5,2) NULL,                        -- Si es %
    monto DECIMAL(12,2) NOT NULL,                             -- Monto final
    
    -- Observaciones
    observaciones NVARCHAR(255) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_plandet_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_plandet_planemp FOREIGN KEY (planilla_empleado_id) 
        REFERENCES hcm_planilla_empleado(planilla_empleado_id) ON DELETE NO ACTION,
    CONSTRAINT FK_plandet_concepto FOREIGN KEY (concepto_id) 
        REFERENCES hcm_concepto_planilla(concepto_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_plandet_empresa ON hcm_planilla_detalle(empresa_id);
CREATE INDEX IDX_plandet_planemp ON hcm_planilla_detalle(planilla_empleado_id, tipo_concepto);
CREATE INDEX IDX_plandet_concepto ON hcm_planilla_detalle(concepto_id);

-- -----------------------------------------------------------------------------
-- Tabla: hcm_asistencia
-- Descripción: Control de asistencia diaria
-- Uso: Registro de marcaciones de entrada/salida
-- Relaciones: Por empleado y fecha
-- -----------------------------------------------------------------------------
CREATE TABLE hcm_asistencia (
    asistencia_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    empleado_id UNIQUEIDENTIFIER NOT NULL,
    
    fecha DATE NOT NULL,
    dia_semana AS DATEPART(WEEKDAY, fecha),   -- 1=Domingo, 7=Sábado (no persisted - non-deterministic)
    
    -- Marcaciones
    hora_entrada TIME NULL,
    hora_salida TIME NULL,
    hora_entrada_refrigerio TIME NULL,
    hora_salida_refrigerio TIME NULL,
    
    -- Horas trabajadas
    horas_trabajadas DECIMAL(5,2) NULL,
    horas_extras DECIMAL(5,2) DEFAULT 0,
    
    -- Estado
    tipo_asistencia NVARCHAR(20) DEFAULT 'presente',          -- 'presente', 'falta', 'tardanza', 'licencia', 'vacaciones', 'descanso_medico'
    minutos_tardanza INT DEFAULT 0,
    
    -- Justificación
    tiene_justificacion BIT DEFAULT 0,
    justificacion NVARCHAR(500) NULL,
    archivo_justificacion_url NVARCHAR(500) NULL,
    
    -- Incidencias
    incidencias NVARCHAR(MAX) NULL,
    
    -- Dispositivo (si es reloj biométrico)
    dispositivo_marcacion NVARCHAR(50) NULL,
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    
    CONSTRAINT FK_asist_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_asist_empleado FOREIGN KEY (empleado_id) 
        REFERENCES hcm_empleado(empleado_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_asist_empleado_fecha UNIQUE (cliente_id, empleado_id, fecha)
);

CREATE INDEX IDX_asist_empresa ON hcm_asistencia(empresa_id, fecha DESC);
CREATE INDEX IDX_asist_empleado ON hcm_asistencia(empleado_id, fecha DESC);
CREATE INDEX IDX_asist_fecha ON hcm_asistencia(fecha DESC);
CREATE INDEX IDX_asist_tipo ON hcm_asistencia(tipo_asistencia, fecha);

-- -----------------------------------------------------------------------------
-- Tabla: hcm_vacaciones
-- Descripción: Registro de vacaciones
-- Uso: Control de vacaciones ganadas, programadas y tomadas
-- Relaciones: Por empleado y periodo
-- -----------------------------------------------------------------------------
CREATE TABLE hcm_vacaciones (
    vacaciones_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    empleado_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Periodo
    año_periodo INT NOT NULL,
    fecha_inicio_periodo DATE NOT NULL,                       -- Desde cuándo se computa
    fecha_fin_periodo DATE NOT NULL,
    
    -- Días
    dias_ganados INT DEFAULT 30,
    dias_tomados INT DEFAULT 0,
    dias_pendientes AS (dias_ganados - dias_tomados) PERSISTED,
    
    -- Programación
    fecha_inicio_programada DATE NULL,
    fecha_fin_programada DATE NULL,
    fecha_inicio_real DATE NULL,
    fecha_fin_real DATE NULL,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'pendiente',                  -- 'pendiente', 'programada', 'aprobada', 'en_curso', 'completada', 'vencida'
    fecha_aprobacion DATETIME NULL,
    aprobado_por_usuario_id UNIQUEIDENTIFIER NULL,
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_vac_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_vac_empleado FOREIGN KEY (empleado_id) 
        REFERENCES hcm_empleado(empleado_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_vac_empleado_periodo UNIQUE (cliente_id, empleado_id, año_periodo)
);

CREATE INDEX IDX_vac_empresa ON hcm_vacaciones(empresa_id, año_periodo DESC);
CREATE INDEX IDX_vac_empleado ON hcm_vacaciones(empleado_id, estado);

-- -----------------------------------------------------------------------------
-- Tabla: hcm_prestamo
-- Descripción: Préstamos a empleados
-- Uso: Control de adelantos y préstamos con descuento en planilla
-- Relaciones: Por empleado, se descuenta en planilla
-- -----------------------------------------------------------------------------
CREATE TABLE hcm_prestamo (
    prestamo_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    empleado_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_prestamo NVARCHAR(20) NOT NULL,
    
    tipo_prestamo NVARCHAR(30) NOT NULL,                      -- 'adelanto_sueldo', 'prestamo', 'adelanto_gratificacion'
    
    monto_prestamo DECIMAL(12,2) NOT NULL,
    moneda_id UNIQUEIDENTIFIER NOT NULL,
    
    fecha_prestamo DATE DEFAULT GETDATE() NOT NULL,
    
    -- Devolución
    numero_cuotas INT NOT NULL,
    monto_cuota DECIMAL(12,2) NOT NULL,
    cuotas_pagadas INT DEFAULT 0,
    cuotas_pendientes AS (numero_cuotas - cuotas_pagadas) PERSISTED,
    saldo_pendiente DECIMAL(12,2) NULL,
    
    -- Tasa de interés (si aplica)
    aplica_interes BIT DEFAULT 0,
    tasa_interes_mensual DECIMAL(5,2) NULL,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'activo',                     -- 'activo', 'pagado', 'cancelado'
    fecha_pago_completo DATE NULL,
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    motivo_prestamo NVARCHAR(255) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    aprobado_por_usuario_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_prestamo_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_prestamo_empleado FOREIGN KEY (empleado_id) 
        REFERENCES hcm_empleado(empleado_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_prestamo_numero UNIQUE (cliente_id, empresa_id, numero_prestamo),
    CONSTRAINT FK_prestamo_moneda FOREIGN KEY (moneda_id)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_prestamo_empresa ON hcm_prestamo(empresa_id, fecha_prestamo DESC);
CREATE INDEX IDX_prestamo_empleado ON hcm_prestamo(empleado_id, estado);