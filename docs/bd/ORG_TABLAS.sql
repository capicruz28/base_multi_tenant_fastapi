-- ============================================================================
-- SECCIÓN 1: ORG - ORGANIZACIÓN (MÓDULO CORE - OBLIGATORIO)
-- ============================================================================
-- DESCRIPCIÓN: Módulo fundamental que define la estructura organizacional
--              de la empresa. Es prerequisito para todos los demás módulos.
-- DEPENDENCIAS: Ninguna (es el módulo base)
-- USADO POR: Todos los módulos del sistema
-- ============================================================================

-- -----------------------------------------------------------------------------    
-- Tabla: cat_moneda (GLOBAL)
-- Descripción: Catálogo de monedas soportadas por la empresa
-- Uso: Permite configurar diferentes monedas para operaciones financieras
-- Relaciones: Usado por la empresa
-- -----------------------------------------------------------------------------
CREATE TABLE cat_moneda (
    moneda_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    codigo NVARCHAR(3) NOT NULL,
    nombre NVARCHAR(50) NOT NULL,
    simbolo NVARCHAR(5) NOT NULL,
    decimales INT DEFAULT 2,
    es_activo BIT DEFAULT 1,
    CONSTRAINT UQ_moneda_codigo UNIQUE (codigo)
);

CREATE INDEX IDX_moneda_activo ON cat_moneda(es_activo);

-- -----------------------------------------------------------------------------    
-- Tabla: cat_pais (GLOBAL)
-- Descripción: Catálogo de países soportados por la empresa
-- Uso: Permite configurar diferentes países
-- Relaciones: Usado por la empresa
-- -----------------------------------------------------------------------------
CREATE TABLE cat_pais (
    pais_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    codigo_iso2 NVARCHAR(2) NOT NULL,
    codigo_iso3 NVARCHAR(3) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    es_activo BIT DEFAULT 1,
    CONSTRAINT UQ_pais_iso2 UNIQUE (codigo_iso2)
);

CREATE INDEX IDX_pais_activo ON cat_pais(es_activo);

-- -----------------------------------------------------------------------------    
-- Tabla: cat_departamento (GLOBAL)
-- Descripción: Catálogo de departamentos soportados por la empresa
-- Uso: Permite configurar diferentes departamentos
-- Relaciones: Usado por la empresa
-- -----------------------------------------------------------------------------
CREATE TABLE cat_departamento (
    departamento_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    pais_id UNIQUEIDENTIFIER NOT NULL,
    codigo NVARCHAR(10) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    CONSTRAINT FK_depto_pais FOREIGN KEY (pais_id) 
        REFERENCES cat_pais(pais_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_depto_pais ON cat_departamento(pais_id);

-- -----------------------------------------------------------------------------    
-- Tabla: cat_provincia (GLOBAL)
-- Descripción: Catálogo de provincias soportadas por la empresa
-- Uso: Permite configurar diferentes provincias
-- Relaciones: Usado por la empresa
-- -----------------------------------------------------------------------------
CREATE TABLE cat_provincia (
    provincia_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    departamento_id UNIQUEIDENTIFIER NOT NULL,
    codigo NVARCHAR(10) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    CONSTRAINT FK_prov_depto FOREIGN KEY (departamento_id) 
        REFERENCES cat_departamento(departamento_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_prov_depto ON cat_provincia(departamento_id);

-- -----------------------------------------------------------------------------    
-- Tabla: cat_distrito (GLOBAL)
-- Descripción: Catálogo de distritos soportados por la empresa
-- Uso: Permite configurar diferentes distritos
-- Relaciones: Usado por la empresa
-- -----------------------------------------------------------------------------
CREATE TABLE cat_distrito (
    distrito_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    provincia_id UNIQUEIDENTIFIER NOT NULL,
    codigo NVARCHAR(10) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    ubigeo NVARCHAR(6) NOT NULL,
    CONSTRAINT FK_dist_prov FOREIGN KEY (provincia_id) 
        REFERENCES cat_provincia(provincia_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_ubigeo UNIQUE (ubigeo)
);

CREATE INDEX IDX_dist_prov ON cat_distrito(provincia_id);
CREATE INDEX IDX_dist_ubigeo ON cat_distrito(ubigeo);

-- -----------------------------------------------------------------------------
-- Tabla: org_empresa
-- Descripción: Datos maestros de la empresa/organización del cliente
-- Uso: Una sola empresa por BD dedicada (cabecera organizacional)
-- Relaciones: Base para toda la jerarquía organizacional
-- -----------------------------------------------------------------------------
CREATE TABLE org_empresa (
    empresa_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,                     -- FK a cliente en BD central
    codigo_empresa NVARCHAR(20) NOT NULL,                     -- Código único de empresa (ej: "EMP001")
    razon_social NVARCHAR(200) NOT NULL,                      -- Razón social legal
    nombre_comercial NVARCHAR(150) NULL,                      -- Nombre comercial
    ruc NVARCHAR(11) NOT NULL,                                -- RUC/NIT/Tax ID
    tipo_documento_tributario NVARCHAR(10) DEFAULT 'RUC',     -- RUC, NIT, Tax ID, etc
    actividad_economica NVARCHAR(200) NULL,                   -- CIIU o descripción actividad
    codigo_ciiu NVARCHAR(10) NULL,                            -- Código CIIU
    rubro NVARCHAR(50) NULL,                                  -- Textil, Minería, Servicios, etc
    tipo_empresa NVARCHAR(30) NULL,                           -- SAC, SRL, SA, EIRL, etc
    
    -- Dirección fiscal
    direccion_fiscal NVARCHAR(255) NULL,
    pais_id UNIQUEIDENTIFIER NULL,
    departamento_id UNIQUEIDENTIFIER NULL,
    provincia_id UNIQUEIDENTIFIER NULL,
    distrito_id UNIQUEIDENTIFIER NULL,
    codigo_postal NVARCHAR(10) NULL,
    ubigeo NVARCHAR(6) NULL,                                  -- Código ubigeo INEI (Perú)
    
    -- Contacto
    telefono_principal NVARCHAR(20) NULL,
    telefono_secundario NVARCHAR(20) NULL,
    email_principal NVARCHAR(100) NULL,
    email_facturacion NVARCHAR(100) NULL,
    sitio_web NVARCHAR(255) NULL,
    
    -- Representante legal
    representante_legal_nombre NVARCHAR(150) NULL,
    representante_legal_dni NVARCHAR(20) NULL,
    representante_legal_cargo NVARCHAR(50) NULL,

    -- Multi-moneda
    moneda_base_id UNIQUEIDENTIFIER NULL,                     -- Se llena DESPUÉS de crear monedas
    maneja_multimoneda BIT DEFAULT 0,
    
    -- Configuración
    zona_horaria NVARCHAR(50) DEFAULT 'America/Lima',         -- Timezone
    idioma_sistema NVARCHAR(5) DEFAULT 'es-PE',               -- es-PE, en-US, etc
    formato_fecha NVARCHAR(20) DEFAULT 'dd/MM/yyyy',
    separador_miles NVARCHAR(1) DEFAULT ',',
    separador_decimales NVARCHAR(1) DEFAULT '.',
    decimales_moneda INT DEFAULT 2,
    
    -- Logo y branding
    logo_url NVARCHAR(500) NULL,
    logo_secundario_url NVARCHAR(500) NULL,
    favicon_url NVARCHAR(500) NULL,
    
    -- Estado y auditoría
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_constitucion DATE NULL,
    fecha_inicio_operaciones DATE NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    usuario_actualizacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT UQ_org_empresa_cliente UNIQUE (cliente_id, codigo_empresa),
    CONSTRAINT UQ_org_empresa_ruc UNIQUE (cliente_id, ruc),
    CONSTRAINT FK_empresa_moneda_base FOREIGN KEY (moneda_base_id)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION,
    CONSTRAINT FK_empresa_pais FOREIGN KEY (pais_id) 
        REFERENCES cat_pais(pais_id) ON DELETE NO ACTION,
    CONSTRAINT FK_empresa_depto FOREIGN KEY (departamento_id) 
        REFERENCES cat_departamento(departamento_id) ON DELETE NO ACTION,
    CONSTRAINT FK_empresa_prov FOREIGN KEY (provincia_id) 
        REFERENCES cat_provincia(provincia_id) ON DELETE NO ACTION,
    CONSTRAINT FK_empresa_dist FOREIGN KEY (distrito_id) 
        REFERENCES cat_distrito(distrito_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_org_empresa_cliente ON org_empresa(cliente_id, es_activo);
CREATE INDEX IDX_org_empresa_ruc ON org_empresa(ruc);

-- -----------------------------------------------------------------------------
-- Tabla: org_centro_costo
-- Descripción: Centros de costo para distribución contable y analítica
-- Uso: Permite segmentar costos por áreas, departamentos, proyectos, etc
-- Relaciones: Usado por FIN, CST, HCM, MFG para imputación de costos
-- -----------------------------------------------------------------------------
CREATE TABLE org_centro_costo (
    centro_costo_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    codigo NVARCHAR(20) NOT NULL,                             -- Código del centro de costo (ej: "CC-ADM", "CC-PROD-01")
    nombre NVARCHAR(100) NOT NULL,                            -- Nombre descriptivo
    descripcion NVARCHAR(255) NULL,
    
    -- Jerarquía
    centro_costo_padre_id UNIQUEIDENTIFIER NULL,              -- Para estructura jerárquica de centros de costo
    nivel INT DEFAULT 1,                                       -- Nivel en la jerarquía (1=raíz, 2=hijo, etc)
    ruta_jerarquica NVARCHAR(500) NULL,                       -- Path completo (ej: "CC-ADM/CC-ADM-CONT")
    
    -- Clasificación
    tipo_centro_costo NVARCHAR(30) NOT NULL,                  -- 'produccion', 'administrativo', 'ventas', 'servicio', etc
    categoria NVARCHAR(50) NULL,                              -- Clasificación adicional personalizable
    
    -- Configuración presupuestaria
    tiene_presupuesto BIT DEFAULT 0,                          -- Si se le asigna presupuesto
    permite_imputacion_directa BIT DEFAULT 1,                 -- Si permite cargar gastos directamente
    
    -- Responsable
    responsable_usuario_id UNIQUEIDENTIFIER NULL,             -- Usuario responsable del centro de costo
    responsable_nombre NVARCHAR(150) NULL,
    
    -- Estado y auditoría
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_inicio_vigencia DATE NULL,
    fecha_fin_vigencia DATE NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_cc_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cc_padre FOREIGN KEY (centro_costo_padre_id) 
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_cc_codigo UNIQUE (cliente_id, empresa_id, codigo)
);

CREATE INDEX IDX_cc_empresa ON org_centro_costo(empresa_id, es_activo);
CREATE INDEX IDX_cc_tipo ON org_centro_costo(tipo_centro_costo, es_activo);
CREATE INDEX IDX_cc_padre ON org_centro_costo(centro_costo_padre_id);

-- -----------------------------------------------------------------------------
-- Tabla: org_sucursal
-- Descripción: Sucursales, sedes, tiendas o puntos de operación
-- Uso: Localizaciones físicas donde opera la empresa
-- Relaciones: Usado por INV (almacenes), HCM (empleados), SLS (puntos venta)
-- -----------------------------------------------------------------------------
CREATE TABLE org_sucursal (
    sucursal_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    codigo NVARCHAR(20) NOT NULL,                             -- Código de sucursal (ej: "SUC-LIMA-01", "TDA-AREQUIPA")
    nombre NVARCHAR(100) NOT NULL,                            -- Nombre de la sucursal
    descripcion NVARCHAR(255) NULL,
    tipo_sucursal NVARCHAR(30) DEFAULT 'sede',                -- 'sede', 'tienda', 'almacen', 'planta', 'oficina', etc
    
    -- Dirección
    direccion NVARCHAR(255) NULL,
    referencia NVARCHAR(255) NULL,
    pais_id UNIQUEIDENTIFIER NULL,
    departamento_id UNIQUEIDENTIFIER NULL,
    provincia_id UNIQUEIDENTIFIER NULL,
    distrito_id UNIQUEIDENTIFIER NULL,
    ubigeo NVARCHAR(6) NULL,
    codigo_postal NVARCHAR(10) NULL,
    latitud DECIMAL(10,8) NULL,                               -- Para geolocalización
    longitud DECIMAL(11,8) NULL,
    
    -- Contacto
    telefono NVARCHAR(20) NULL,
    email NVARCHAR(100) NULL,
    
    -- Configuración operativa
    es_casa_matriz BIT DEFAULT 0,                             -- Si es la sede principal
    es_punto_venta BIT DEFAULT 0,                             -- Si realiza ventas directas
    es_almacen BIT DEFAULT 0,                                 -- Si tiene almacén
    es_planta_produccion BIT DEFAULT 0,                       -- Si es planta de producción
    
    -- Horarios
    horario_atencion NVARCHAR(MAX) NULL,                      -- JSON con horarios (ej: {"lun-vie":"8:00-18:00"})
    zona_horaria NVARCHAR(50) NULL,                           -- Si difiere de la empresa
    
    -- Responsable
    responsable_usuario_id UNIQUEIDENTIFIER NULL,
    responsable_nombre NVARCHAR(150) NULL,
    
    -- Centro de costo asociado
    centro_costo_id UNIQUEIDENTIFIER NULL,                    -- Centro de costo de la sucursal
    
    -- Estado y auditoría
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_apertura DATE NULL,
    fecha_cierre DATE NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_sucursal_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_sucursal_cc FOREIGN KEY (centro_costo_id) 
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_sucursal_codigo UNIQUE (cliente_id, empresa_id, codigo),
    CONSTRAINT FK_sucursal_pais FOREIGN KEY (pais_id) 
        REFERENCES cat_pais(pais_id) ON DELETE NO ACTION,
    CONSTRAINT FK_sucursal_depto FOREIGN KEY (departamento_id) 
        REFERENCES cat_departamento(departamento_id) ON DELETE NO ACTION,
    CONSTRAINT FK_sucursal_prov FOREIGN KEY (provincia_id) 
        REFERENCES cat_provincia(provincia_id) ON DELETE NO ACTION,
    CONSTRAINT FK_sucursal_dist FOREIGN KEY (distrito_id) 
        REFERENCES cat_distrito(distrito_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_sucursal_empresa ON org_sucursal(empresa_id, es_activo);
CREATE INDEX IDX_sucursal_tipo ON org_sucursal(tipo_sucursal, es_activo);
CREATE INDEX IDX_sucursal_ubigeo ON org_sucursal(ubigeo) WHERE ubigeo IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Tabla: org_departamento
-- Descripción: Departamentos o áreas organizacionales
-- Uso: Estructura funcional de la empresa (RRHH, Ventas, Producción, etc)
-- Relaciones: Usado por HCM para asignación de empleados
-- -----------------------------------------------------------------------------
CREATE TABLE org_departamento (
    departamento_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    codigo NVARCHAR(20) NOT NULL,                             -- Código del departamento (ej: "DPTO-RRHH", "DPTO-VENTAS")
    nombre NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(255) NULL,
    
    -- Jerarquía
    departamento_padre_id UNIQUEIDENTIFIER NULL,              -- Para sub-departamentos
    nivel INT DEFAULT 1,
    ruta_jerarquica NVARCHAR(500) NULL,
    
    -- Clasificación
    tipo_departamento NVARCHAR(30) NULL,                      -- 'operativo', 'administrativo', 'comercial', etc
    
    -- Responsable
    jefe_departamento_usuario_id UNIQUEIDENTIFIER NULL,       -- Usuario que dirige el departamento
    jefe_nombre NVARCHAR(150) NULL,
    
    -- Relación con otras estructuras
    centro_costo_id UNIQUEIDENTIFIER NULL,                    -- Centro de costo asociado
    sucursal_id UNIQUEIDENTIFIER NULL,                        -- Sucursal donde opera (NULL = todas)
    
    -- Estado y auditoría
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_dpto_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_dpto_padre FOREIGN KEY (departamento_padre_id) 
        REFERENCES org_departamento(departamento_id) ON DELETE NO ACTION,
    CONSTRAINT FK_dpto_cc FOREIGN KEY (centro_costo_id) 
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE NO ACTION,
    CONSTRAINT FK_dpto_sucursal FOREIGN KEY (sucursal_id) 
        REFERENCES org_sucursal(sucursal_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_dpto_codigo UNIQUE (cliente_id, empresa_id, codigo)
);

CREATE INDEX IDX_dpto_empresa ON org_departamento(empresa_id, es_activo);
CREATE INDEX IDX_dpto_padre ON org_departamento(departamento_padre_id);
CREATE INDEX IDX_dpto_sucursal ON org_departamento(sucursal_id) WHERE sucursal_id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Tabla: org_cargo
-- Descripción: Catálogo de cargos/puestos de trabajo
-- Uso: Posiciones laborales existentes en la organización
-- Relaciones: Usado por HCM para contratos y estructura salarial
-- -----------------------------------------------------------------------------
CREATE TABLE org_cargo (
    cargo_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    codigo NVARCHAR(20) NOT NULL,                             -- Código del cargo (ej: "CARG-GER-001")
    nombre NVARCHAR(100) NOT NULL,                            -- Ej: "Gerente de Ventas", "Operario de Producción"
    descripcion NVARCHAR(500) NULL,
    
    -- Clasificación
    nivel_jerarquico INT DEFAULT 1,                           -- 1=Directivo, 2=Gerencia, 3=Jefatura, 4=Analista, 5=Operativo
    categoria NVARCHAR(30) NULL,                              -- 'ejecutivo', 'profesional', 'tecnico', 'operativo'
    area_funcional NVARCHAR(50) NULL,                         -- 'ventas', 'produccion', 'administracion', etc
    
    -- Organización
    departamento_id UNIQUEIDENTIFIER NULL,                    -- Departamento típico (puede ser NULL si aplica a varios)
    cargo_jefe_id UNIQUEIDENTIFIER NULL,                      -- Cargo del jefe directo
    
    -- Configuración salarial
    rango_salarial_min DECIMAL(12,2) NULL,                    -- Salario mínimo del cargo
    rango_salarial_max DECIMAL(12,2) NULL,                    -- Salario máximo del cargo
    moneda_salarial UNIQUEIDENTIFIER NOT NULL,
    
    -- Requisitos (flexible para diferentes industrias)
    nivel_educacion_minimo NVARCHAR(50) NULL,                 -- 'secundaria', 'tecnico', 'universitario', 'posgrado'
    experiencia_minima_meses INT NULL,
    requisitos_especificos NVARCHAR(MAX) NULL,                -- JSON o texto libre
    
    -- Estado y auditoría
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_cargo_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cargo_dpto FOREIGN KEY (departamento_id) 
        REFERENCES org_departamento(departamento_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cargo_jefe FOREIGN KEY (cargo_jefe_id) 
        REFERENCES org_cargo(cargo_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_cargo_codigo UNIQUE (cliente_id, empresa_id, codigo),
    CONSTRAINT FK_cargo_moneda FOREIGN KEY (moneda_salarial)
        REFERENCES cat_moneda(moneda_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_cargo_empresa ON org_cargo(empresa_id, es_activo);
CREATE INDEX IDX_cargo_nivel ON org_cargo(nivel_jerarquico);
CREATE INDEX IDX_cargo_dpto ON org_cargo(departamento_id) WHERE departamento_id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Tabla: org_parametro_sistema
-- Descripción: Parámetros configurables del sistema por cliente
-- Uso: Valores de configuración que afectan el comportamiento de módulos
-- Relaciones: Consultado por todos los módulos para configuraciones específicas
-- -----------------------------------------------------------------------------
CREATE TABLE org_parametro_sistema (
    parametro_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NULL,                         -- NULL = aplica a todo el cliente
    modulo_codigo NVARCHAR(10) NOT NULL,                      -- 'ORG', 'INV', 'HCM', 'FIN', etc
    codigo_parametro NVARCHAR(50) NOT NULL,                   -- Código único del parámetro
    nombre_parametro NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(255) NULL,
    
    -- Valor
    tipo_dato NVARCHAR(20) NOT NULL,                          -- 'string', 'int', 'decimal', 'bool', 'date', 'json'
    valor_texto NVARCHAR(MAX) NULL,
    valor_numerico DECIMAL(18,4) NULL,
    valor_booleano BIT NULL,
    valor_fecha DATE NULL,
    valor_json NVARCHAR(MAX) NULL,
    
    -- Configuración
    valor_defecto NVARCHAR(500) NULL,                         -- Valor por defecto
    es_editable BIT DEFAULT 1,                                -- Si el usuario puede modificarlo
    es_obligatorio BIT DEFAULT 0,                             -- Si requiere tener un valor
    opciones_validas NVARCHAR(MAX) NULL,                      -- JSON con opciones permitidas (para combos)
    
    -- Validación
    expresion_validacion NVARCHAR(500) NULL,                  -- Regex o expresión de validación
    mensaje_validacion NVARCHAR(255) NULL,
    
    -- Estado y auditoría
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_actualizacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_parametro_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_parametro UNIQUE (cliente_id, empresa_id, modulo_codigo, codigo_parametro)
);

CREATE INDEX IDX_parametro_empresa ON org_parametro_sistema(empresa_id, modulo_codigo);
CREATE INDEX IDX_parametro_modulo ON org_parametro_sistema(modulo_codigo, codigo_parametro);
