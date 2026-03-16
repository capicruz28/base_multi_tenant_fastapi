-- ============================================================================
-- SCRIPT: MÓDULOS ERP COMPLETO - BD DEDICADA
-- DESCRIPCIÓN: Estructura completa de tablas para todos los módulos ERP
-- ARQUITECTURA: Multi-tenant SaaS (cada cliente con BD dedicada)
-- USO: Ejecutar en BD dedicada del cliente al activar módulos
-- NOTA: Todas las PKs son UNIQUEIDENTIFIER (UUID)
-- VERSIÓN: 1.0
-- FECHA: Febrero 2026
-- ============================================================================

-- ============================================================================
-- ÍNDICE DE MÓDULOS
-- ============================================================================
-- SECCIÓN 1: ORG - Organización (CORE - Obligatorio)
-- SECCIÓN 2: INV - Inventarios y Almacenes
-- SECCIÓN 3: WMS - Warehouse Management System
-- SECCIÓN 4: QMS - Gestión de Calidad
-- SECCIÓN 5: PUR - Compras y Abastecimiento
-- SECCIÓN 6: LOG - Logística y Distribución
-- SECCIÓN 7: MFG - Manufactura y Producción
-- SECCIÓN 8: MRP - Planeamiento de Materiales
-- SECCIÓN 9: MPS - Plan Maestro de Producción
-- SECCIÓN 10: MNT - Mantenimiento de Activos
-- SECCIÓN 11: SLS - Ventas
-- SECCIÓN 12: CRM - Customer Relationship Management
-- SECCIÓN 13: PRC - Gestión de Precios
-- SECCIÓN 14: INV_BILL - Facturación Electrónica
-- SECCIÓN 15: POS - Punto de Venta
-- SECCIÓN 16: HCM - Human Capital Management (Planillas y RRHH)
-- SECCIÓN 17: FIN - Finanzas y Contabilidad
-- SECCIÓN 18: TAX - Gestión Tributaria
-- SECCIÓN 19: BDG - Presupuestos
-- SECCIÓN 20: CST - Costos y Costeo
-- SECCIÓN 21: PM - Gestión de Proyectos
-- SECCIÓN 22: SVC - Gestión de Servicios
-- SECCIÓN 23: TKT - Mesa de Ayuda (Ticketing)
-- SECCIÓN 24: BI - Business Intelligence
-- SECCIÓN 25: DMS - Gestión Documental
-- SECCIÓN 26: WFL - Motor de Flujos (Workflow)
-- SECCIÓN 27: AUD - Auditoría y Trazabilidad
-- ============================================================================

-- ============================================================================
-- SECCIÓN 1: ORG - ORGANIZACIÓN (MÓDULO CORE - OBLIGATORIO)
-- ============================================================================
-- DESCRIPCIÓN: Módulo fundamental que define la estructura organizacional
--              de la empresa. Es prerequisito para todos los demás módulos.
-- DEPENDENCIAS: Ninguna (es el módulo base)
-- USADO POR: Todos los módulos del sistema
-- ============================================================================

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
    pais NVARCHAR(50) DEFAULT 'Perú',
    departamento NVARCHAR(50) NULL,
    provincia NVARCHAR(50) NULL,
    distrito NVARCHAR(50) NULL,
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
    
    -- Configuración
    moneda_base NVARCHAR(3) DEFAULT 'PEN',                    -- PEN, USD, EUR, etc (ISO 4217)
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
    CONSTRAINT UQ_org_empresa_ruc UNIQUE (cliente_id, ruc)
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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
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
    pais NVARCHAR(50) DEFAULT 'Perú',
    departamento NVARCHAR(50) NULL,
    provincia NVARCHAR(50) NULL,
    distrito NVARCHAR(50) NULL,
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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_sucursal_cc FOREIGN KEY (centro_costo_id) 
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE SET NULL,
    CONSTRAINT UQ_sucursal_codigo UNIQUE (cliente_id, empresa_id, codigo)
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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_dpto_padre FOREIGN KEY (departamento_padre_id) 
        REFERENCES org_departamento(departamento_id) ON DELETE NO ACTION,
    CONSTRAINT FK_dpto_cc FOREIGN KEY (centro_costo_id) 
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE SET NULL,
    CONSTRAINT FK_dpto_sucursal FOREIGN KEY (sucursal_id) 
        REFERENCES org_sucursal(sucursal_id) ON DELETE SET NULL,
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
    moneda_salarial NVARCHAR(3) DEFAULT 'PEN',
    
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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_cargo_dpto FOREIGN KEY (departamento_id) 
        REFERENCES org_departamento(departamento_id) ON DELETE SET NULL,
    CONSTRAINT FK_cargo_jefe FOREIGN KEY (cargo_jefe_id) 
        REFERENCES org_cargo(cargo_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_cargo_codigo UNIQUE (cliente_id, empresa_id, codigo)
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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT UQ_parametro UNIQUE (cliente_id, empresa_id, modulo_codigo, codigo_parametro)
);

CREATE INDEX IDX_parametro_empresa ON org_parametro_sistema(empresa_id, modulo_codigo);
CREATE INDEX IDX_parametro_modulo ON org_parametro_sistema(modulo_codigo, codigo_parametro);

-- ============================================================================
-- SECCIÓN 2: INV - INVENTARIOS Y ALMACENES
-- ============================================================================
-- DESCRIPCIÓN: Gestión de productos, almacenes, movimientos de stock
-- DEPENDENCIAS: ORG (empresa, sucursal)
-- USADO POR: PUR (compras), SLS (ventas), MFG (producción), CST (costos)
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: inv_categoria_producto
-- Descripción: Categorización jerárquica de productos
-- Uso: Clasificar productos para reportes, búsquedas y análisis
-- Relaciones: Usado por inv_producto
-- -----------------------------------------------------------------------------
CREATE TABLE inv_categoria_producto (
    categoria_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    codigo NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(255) NULL,
    
    -- Jerarquía
    categoria_padre_id UNIQUEIDENTIFIER NULL,                 -- Para sub-categorías
    nivel INT DEFAULT 1,
    ruta_jerarquica NVARCHAR(500) NULL,                       -- Ej: "Textiles/Telas/Algodón"
    
    -- Configuración contable (usado por FIN y CST)
    cuenta_contable_inventario NVARCHAR(20) NULL,             -- Cuenta contable para inventarios de esta categoría
    cuenta_contable_costo_venta NVARCHAR(20) NULL,            -- Cuenta contable para costo de ventas
    
    -- Configuración de costeo
    metodo_costeo_defecto NVARCHAR(20) NULL,                  -- 'promedio', 'fifo', 'lifo', 'estandar'
    
    -- Estado y auditoría
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_cat_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_cat_padre FOREIGN KEY (categoria_padre_id) 
        REFERENCES inv_categoria_producto(categoria_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_cat_codigo UNIQUE (cliente_id, empresa_id, codigo)
);

CREATE INDEX IDX_cat_empresa ON inv_categoria_producto(empresa_id, es_activo);
CREATE INDEX IDX_cat_padre ON inv_categoria_producto(categoria_padre_id);

-- -----------------------------------------------------------------------------
-- Tabla: inv_unidad_medida
-- Descripción: Unidades de medida y conversiones
-- Uso: Manejo de múltiples unidades (kg, unidad, caja, etc)
-- Relaciones: Usado por inv_producto, pur_orden_compra, sls_pedido
-- -----------------------------------------------------------------------------
CREATE TABLE inv_unidad_medida (
    unidad_medida_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    codigo NVARCHAR(10) NOT NULL,                             -- Ej: "UN", "KG", "MT", "LT"
    nombre NVARCHAR(50) NOT NULL,                             -- Ej: "Unidad", "Kilogramo", "Metro", "Litro"
    simbolo NVARCHAR(10) NULL,                                -- Ej: "kg", "m", "L"
    tipo_unidad NVARCHAR(20) NOT NULL,                        -- 'cantidad', 'peso', 'volumen', 'longitud', 'area', 'tiempo'
    
    -- Unidad base (para conversiones)
    es_unidad_base BIT DEFAULT 0,                             -- Si es la unidad base del tipo (ej: kg para peso)
    factor_conversion_base DECIMAL(18,6) NULL,                -- Factor para convertir a unidad base
    
    -- Configuración
    decimales_permitidos INT DEFAULT 2,                       -- Decimales permitidos para esta unidad
    
    -- Estado y auditoría
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_um_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT UQ_um_codigo UNIQUE (cliente_id, empresa_id, codigo)
);

CREATE INDEX IDX_um_empresa ON inv_unidad_medida(empresa_id, es_activo);
CREATE INDEX IDX_um_tipo ON inv_unidad_medida(tipo_unidad);

-- -----------------------------------------------------------------------------
-- Tabla: inv_producto
-- Descripción: Catálogo maestro de productos/artículos
-- Uso: Productos que se compran, venden, producen o almacenan
-- Relaciones: Base para todo el sistema de inventarios
-- -----------------------------------------------------------------------------
CREATE TABLE inv_producto (
    producto_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Identificación
    codigo_sku NVARCHAR(50) NOT NULL,                         -- SKU único del producto
    codigo_barra NVARCHAR(50) NULL,                           -- Código de barras EAN/UPC
    codigo_interno NVARCHAR(30) NULL,                         -- Código interno adicional
    codigo_fabricante NVARCHAR(50) NULL,                      -- Part number del fabricante
    
    -- Datos básicos
    nombre NVARCHAR(200) NOT NULL,
    nombre_corto NVARCHAR(100) NULL,
    descripcion NVARCHAR(MAX) NULL,
    descripcion_corta NVARCHAR(500) NULL,
    
    -- Clasificación
    categoria_id UNIQUEIDENTIFIER NULL,
    subcategoria_id UNIQUEIDENTIFIER NULL,
    marca NVARCHAR(100) NULL,
    modelo NVARCHAR(100) NULL,
    linea_producto NVARCHAR(100) NULL,                        -- Línea de producto (ej: "Premium", "Económica")
    
    -- Tipo de producto (flexible para todas las industrias)
    tipo_producto NVARCHAR(30) NOT NULL,                      -- 'bien', 'servicio', 'materia_prima', 'producto_terminado', 'semi_elaborado', 'insumo'
    subtipo_producto NVARCHAR(50) NULL,                       -- Personalizable según industria
    
    -- Unidades de medida
    unidad_medida_base_id UNIQUEIDENTIFIER NOT NULL,          -- Unidad base (ej: "UN", "KG")
    unidad_medida_compra_id UNIQUEIDENTIFIER NULL,            -- Unidad en que se compra (puede diferir de la base)
    unidad_medida_venta_id UNIQUEIDENTIFIER NULL,             -- Unidad en que se vende
    factor_conversion_compra DECIMAL(18,6) DEFAULT 1,         -- Factor de conversión compra -> base
    factor_conversion_venta DECIMAL(18,6) DEFAULT 1,          -- Factor de conversión venta -> base
    
    -- Características físicas (adaptable según industria)
    peso_kg DECIMAL(12,4) NULL,                               -- Peso en kilogramos
    volumen_m3 DECIMAL(12,6) NULL,                            -- Volumen en metros cúbicos
    largo_cm DECIMAL(10,2) NULL,
    ancho_cm DECIMAL(10,2) NULL,
    alto_cm DECIMAL(10,2) NULL,
    color NVARCHAR(50) NULL,
    talla NVARCHAR(20) NULL,
    
    -- Características específicas (JSON flexible para atributos personalizados por industria)
    atributos_personalizados NVARCHAR(MAX) NULL,              -- JSON: {"dureza":"HRC 58-62", "acabado":"cromado", etc}
    especificaciones_tecnicas NVARCHAR(MAX) NULL,             -- JSON o texto con especificaciones
    
    -- Configuración de inventario
    maneja_inventario BIT DEFAULT 1,                          -- Si controla stock (servicios pueden ser 0)
    maneja_lotes BIT DEFAULT 0,                               -- Si maneja lotes de producción
    maneja_series BIT DEFAULT 0,                              -- Si maneja números de serie
    maneja_vencimiento BIT DEFAULT 0,                         -- Si tiene fecha de vencimiento
    dias_vida_util INT NULL,                                  -- Días de vida útil del producto
    requiere_refrigeracion BIT DEFAULT 0,                     -- Si requiere cadena de frío
    es_perecible BIT DEFAULT 0,
    
    -- Stock mínimos y máximos (por producto, luego se detalla por almacén)
    stock_minimo DECIMAL(18,4) NULL,
    stock_maximo DECIMAL(18,4) NULL,
    punto_reorden DECIMAL(18,4) NULL,                         -- Cuando llega a este stock, se debe reordenar
    
    -- Configuración de compras
    es_comprable BIT DEFAULT 1,
    tiempo_entrega_dias INT NULL,                             -- Lead time de compra
    cantidad_minima_compra DECIMAL(18,4) NULL,
    multiplo_compra DECIMAL(18,4) NULL,                       -- Debe comprarse en múltiplos de esta cantidad
    
    -- Configuración de ventas
    es_vendible BIT DEFAULT 1,
    requiere_autorizacion_venta BIT DEFAULT 0,
    
    -- Configuración de producción (MFG)
    es_fabricable BIT DEFAULT 0,                              -- Si se produce internamente
    tiene_lista_materiales BIT DEFAULT 0,                     -- Si tiene BOM (Bill of Materials)
    
    -- Costos (CST)
    metodo_costeo NVARCHAR(20) DEFAULT 'promedio',            -- 'promedio', 'fifo', 'lifo', 'estandar'
    costo_estandar DECIMAL(18,4) NULL,
    costo_ultima_compra DECIMAL(18,4) NULL,
    costo_promedio DECIMAL(18,4) NULL,
    moneda_costo NVARCHAR(3) DEFAULT 'PEN',
    
    -- Precios (PRC)
    precio_base_venta DECIMAL(18,4) NULL,
    moneda_venta NVARCHAR(3) DEFAULT 'PEN',
    afecto_igv BIT DEFAULT 1,                                 -- Si está afecto a impuestos
    porcentaje_igv DECIMAL(5,2) DEFAULT 18.00,
    
    -- Tributario (TAX)
    codigo_sunat NVARCHAR(10) NULL,                           -- Código SUNAT para facturación electrónica
    tipo_afectacion_igv NVARCHAR(2) NULL,                     -- '10' = Gravado, '20' = Exonerado, etc
    
    -- Imágenes y archivos
    imagen_principal_url NVARCHAR(500) NULL,
    imagenes_adicionales NVARCHAR(MAX) NULL,                  -- JSON array de URLs
    ficha_tecnica_url NVARCHAR(500) NULL,
    
    -- Proveedor habitual (PUR)
    proveedor_habitual_id UNIQUEIDENTIFIER NULL,              -- FK a pur_proveedor (se creará en módulo PUR)
    
    -- Estado y auditoría
    estado NVARCHAR(20) DEFAULT 'activo',                     -- 'activo', 'inactivo', 'descontinuado', 'en_desarrollo'
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    usuario_actualizacion_id UNIQUEIDENTIFIER NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    CONSTRAINT FK_prod_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_prod_categoria FOREIGN KEY (categoria_id) 
        REFERENCES inv_categoria_producto(categoria_id) ON DELETE SET NULL,
    CONSTRAINT FK_prod_um_base FOREIGN KEY (unidad_medida_base_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT FK_prod_um_compra FOREIGN KEY (unidad_medida_compra_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT FK_prod_um_venta FOREIGN KEY (unidad_medida_venta_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_prod_sku UNIQUE (cliente_id, empresa_id, codigo_sku)
);

CREATE INDEX IDX_prod_empresa ON inv_producto(empresa_id, es_activo);
CREATE INDEX IDX_prod_categoria ON inv_producto(categoria_id) WHERE categoria_id IS NOT NULL;
CREATE INDEX IDX_prod_tipo ON inv_producto(tipo_producto, es_activo);
CREATE INDEX IDX_prod_codigo_barra ON inv_producto(codigo_barra) WHERE codigo_barra IS NOT NULL;
CREATE INDEX IDX_prod_nombre ON inv_producto(nombre);
CREATE INDEX IDX_prod_comprable ON inv_producto(es_comprable) WHERE es_comprable = 1;
CREATE INDEX IDX_prod_vendible ON inv_producto(es_vendible) WHERE es_vendible = 1;

-- -----------------------------------------------------------------------------
-- Tabla: inv_almacen
-- Descripción: Almacenes físicos donde se almacena inventario
-- Uso: Control de stock por ubicación física
-- Relaciones: Vinculado a org_sucursal, usado por movimientos de inventario
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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_alm_sucursal FOREIGN KEY (sucursal_id) 
        REFERENCES org_sucursal(sucursal_id) ON DELETE SET NULL,
    CONSTRAINT FK_alm_cc FOREIGN KEY (centro_costo_id) 
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE SET NULL,
    CONSTRAINT UQ_alm_codigo UNIQUE (cliente_id, empresa_id, codigo)
);

CREATE INDEX IDX_alm_empresa ON inv_almacen(empresa_id, es_activo);
CREATE INDEX IDX_alm_sucursal ON inv_almacen(sucursal_id) WHERE sucursal_id IS NOT NULL;
CREATE INDEX IDX_alm_tipo ON inv_almacen(tipo_almacen);

-- -----------------------------------------------------------------------------
-- Tabla: inv_stock
-- Descripción: Stock actual de productos por almacén
-- Uso: Consulta rápida de stock disponible
-- Relaciones: Actualizado por inv_movimiento
-- -----------------------------------------------------------------------------
CREATE TABLE inv_stock (
    stock_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    almacen_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Cantidades
    cantidad_actual DECIMAL(18,4) DEFAULT 0 NOT NULL,         -- Stock físico actual
    cantidad_reservada DECIMAL(18,4) DEFAULT 0,               -- Reservado para pedidos/producción
    cantidad_disponible AS (cantidad_actual - cantidad_reservada) PERSISTED,  -- Stock disponible = actual - reservado
    cantidad_transito DECIMAL(18,4) DEFAULT 0,                -- En tránsito (compras pendientes)
    
    -- Valores
    costo_promedio DECIMAL(18,4) DEFAULT 0,                   -- Costo promedio unitario
    valor_total AS (cantidad_actual * costo_promedio) PERSISTED, -- Valor total del stock
    moneda NVARCHAR(3) DEFAULT 'PEN',
    
    -- Control
    stock_minimo DECIMAL(18,4) NULL,                          -- Mínimo específico para este almacén
    stock_maximo DECIMAL(18,4) NULL,
    punto_reorden DECIMAL(18,4) NULL,
    
    -- Ubicación física (WMS)
    ubicacion_almacen NVARCHAR(50) NULL,                      -- Ej: "Pasillo 3-Rack A-Nivel 2"
    
    -- Auditoría
    fecha_ultimo_movimiento DATETIME NULL,
    fecha_ultima_compra DATETIME NULL,
    fecha_ultima_venta DATETIME NULL,
    fecha_actualizacion DATETIME DEFAULT GETDATE(),
    
    CONSTRAINT FK_stock_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE CASCADE,
    CONSTRAINT FK_stock_almacen FOREIGN KEY (almacen_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE CASCADE,
    CONSTRAINT UQ_stock_prod_alm UNIQUE (cliente_id, producto_id, almacen_id)
);

CREATE INDEX IDX_stock_producto ON inv_stock(producto_id);
CREATE INDEX IDX_stock_almacen ON inv_stock(almacen_id);
CREATE INDEX IDX_stock_disponible ON inv_stock(cantidad_disponible) WHERE cantidad_disponible > 0;
CREATE INDEX IDX_stock_bajo ON inv_stock(producto_id, almacen_id) 
    WHERE cantidad_disponible <= ISNULL(stock_minimo, 0);

-- -----------------------------------------------------------------------------
-- Tabla: inv_tipo_movimiento
-- Descripción: Catálogo de tipos de movimientos de inventario
-- Uso: Clasificar entradas, salidas, ajustes, transferencias
-- Relaciones: Usado por inv_movimiento
-- -----------------------------------------------------------------------------
CREATE TABLE inv_tipo_movimiento (
    tipo_movimiento_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo NVARCHAR(20) NOT NULL,                             -- Ej: "COMP", "VENT", "AJUS", "TRANS"
    nombre NVARCHAR(100) NOT NULL,                            -- Ej: "Compra", "Venta", "Ajuste de Inventario"
    descripcion NVARCHAR(255) NULL,
    
    -- Clasificación
    clase_movimiento NVARCHAR(20) NOT NULL,                   -- 'entrada', 'salida', 'transferencia', 'ajuste'
    afecta_costo BIT DEFAULT 1,                               -- Si afecta el costo del producto
    requiere_autorizacion BIT DEFAULT 0,
    
    -- Contabilización
    genera_asiento_contable BIT DEFAULT 0,                    -- Si genera movimiento contable (FIN)
    cuenta_contable_debito NVARCHAR(20) NULL,
    cuenta_contable_credito NVARCHAR(20) NULL,
    
    -- Configuración
    requiere_documento_referencia BIT DEFAULT 0,              -- Si requiere documento (OC, factura, etc)
    tipo_documento_referencia NVARCHAR(50) NULL,              -- Tipos permitidos
    
    -- Estado y auditoría
    es_activo BIT DEFAULT 1 NOT NULL,
    es_tipo_sistema BIT DEFAULT 0,                            -- Si es tipo predefinido del sistema
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_tm_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT UQ_tm_codigo UNIQUE (cliente_id, empresa_id, codigo)
);

CREATE INDEX IDX_tm_empresa ON inv_tipo_movimiento(empresa_id, es_activo);
CREATE INDEX IDX_tm_clase ON inv_tipo_movimiento(clase_movimiento);

-- -----------------------------------------------------------------------------
-- Tabla: inv_movimiento
-- Descripción: Cabecera de movimientos de inventario
-- Uso: Registro de todas las transacciones que afectan el stock
-- Relaciones: Relacionado con PUR, SLS, MFG según el origen del movimiento
-- -----------------------------------------------------------------------------
CREATE TABLE inv_movimiento (
    movimiento_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Identificación
    numero_movimiento NVARCHAR(20) NOT NULL,                  -- Número correlativo único
    tipo_movimiento_id UNIQUEIDENTIFIER NOT NULL,
    fecha_movimiento DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_contable DATE NOT NULL,                             -- Fecha para contabilización
    
    -- Almacenes (origen y destino para transferencias)
    almacen_origen_id UNIQUEIDENTIFIER NULL,
    almacen_destino_id UNIQUEIDENTIFIER NULL,
    
    -- Referencias
    modulo_origen NVARCHAR(10) NULL,                          -- 'PUR', 'SLS', 'MFG', 'INV' (manual)
    documento_referencia_tipo NVARCHAR(20) NULL,              -- 'orden_compra', 'factura_venta', 'orden_produccion'
    documento_referencia_id UNIQUEIDENTIFIER NULL,            -- ID del documento origen
    documento_referencia_numero NVARCHAR(30) NULL,            -- Número del documento
    
    -- Tercero (proveedor/cliente según tipo movimiento)
    tercero_tipo NVARCHAR(20) NULL,                           -- 'proveedor', 'cliente', 'empleado'
    tercero_id UNIQUEIDENTIFIER NULL,                         -- ID del tercero
    tercero_nombre NVARCHAR(200) NULL,
    
    -- Totales
    total_items INT DEFAULT 0,
    total_cantidad DECIMAL(18,4) DEFAULT 0,
    total_costo DECIMAL(18,4) DEFAULT 0,
    moneda NVARCHAR(3) DEFAULT 'PEN',
    
    -- Estado y control
    estado NVARCHAR(20) DEFAULT 'borrador',                   -- 'borrador', 'autorizado', 'procesado', 'anulado'
    requiere_autorizacion BIT DEFAULT 0,
    autorizado_por_usuario_id UNIQUEIDENTIFIER NULL,
    fecha_autorizacion DATETIME NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    motivo_anulacion NVARCHAR(500) NULL,
    
    -- Centro de costo
    centro_costo_id UNIQUEIDENTIFIER NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    fecha_procesado DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    usuario_procesado_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_mov_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_mov_tipo FOREIGN KEY (tipo_movimiento_id) 
        REFERENCES inv_tipo_movimiento(tipo_movimiento_id) ON DELETE NO ACTION,
    CONSTRAINT FK_mov_alm_origen FOREIGN KEY (almacen_origen_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION,
    CONSTRAINT FK_mov_alm_destino FOREIGN KEY (almacen_destino_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION,
    CONSTRAINT FK_mov_cc FOREIGN KEY (centro_costo_id) 
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE SET NULL,
    CONSTRAINT UQ_mov_numero UNIQUE (cliente_id, empresa_id, numero_movimiento)
);

CREATE INDEX IDX_mov_empresa ON inv_movimiento(empresa_id, fecha_movimiento DESC);
CREATE INDEX IDX_mov_tipo ON inv_movimiento(tipo_movimiento_id, estado);
CREATE INDEX IDX_mov_fecha ON inv_movimiento(fecha_movimiento DESC);
CREATE INDEX IDX_mov_estado ON inv_movimiento(estado);
CREATE INDEX IDX_mov_almacen_origen ON inv_movimiento(almacen_origen_id) WHERE almacen_origen_id IS NOT NULL;
CREATE INDEX IDX_mov_almacen_destino ON inv_movimiento(almacen_destino_id) WHERE almacen_destino_id IS NOT NULL;
CREATE INDEX IDX_mov_referencia ON inv_movimiento(modulo_origen, documento_referencia_id) 
    WHERE documento_referencia_id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Tabla: inv_movimiento_detalle
-- Descripción: Detalle de productos en cada movimiento
-- Uso: Items específicos del movimiento con cantidades y costos
-- Relaciones: Detalle de inv_movimiento, actualiza inv_stock
-- -----------------------------------------------------------------------------
CREATE TABLE inv_movimiento_detalle (
    movimiento_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    movimiento_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Cantidad y unidad
    cantidad DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    cantidad_base DECIMAL(18,4) NOT NULL,                     -- Cantidad convertida a unidad base
    
    -- Costos
    costo_unitario DECIMAL(18,4) DEFAULT 0,                   -- Costo por unidad
    costo_total AS (cantidad * costo_unitario) PERSISTED,
    moneda NVARCHAR(3) DEFAULT 'PEN',
    
    -- Lote y vencimiento (si aplica)
    lote NVARCHAR(50) NULL,
    fecha_vencimiento DATE NULL,
    numero_serie NVARCHAR(100) NULL,
    
    -- Ubicación (WMS)
    ubicacion_almacen NVARCHAR(50) NULL,
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_movdet_movimiento FOREIGN KEY (movimiento_id) 
        REFERENCES inv_movimiento(movimiento_id) ON DELETE CASCADE,
    CONSTRAINT FK_movdet_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_movdet_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_movdet_movimiento ON inv_movimiento_detalle(movimiento_id);
CREATE INDEX IDX_movdet_producto ON inv_movimiento_detalle(producto_id);
CREATE INDEX IDX_movdet_lote ON inv_movimiento_detalle(lote) WHERE lote IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Tabla: inv_inventario_fisico
-- Descripción: Tomas de inventario físico (conteos)
-- Uso: Auditorías y ajustes de stock por conteo físico
-- Relaciones: Genera movimientos de ajuste en inv_movimiento
-- -----------------------------------------------------------------------------
CREATE TABLE inv_inventario_fisico (
    inventario_fisico_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_inventario NVARCHAR(20) NOT NULL,
    fecha_inventario DATE NOT NULL,
    almacen_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Alcance
    tipo_inventario NVARCHAR(20) NOT NULL,                    -- 'total', 'ciclico', 'selectivo'
    descripcion NVARCHAR(255) NULL,
    
    -- Filtros (si es inventario selectivo)
    categoria_id UNIQUEIDENTIFIER NULL,
    ubicacion_almacen NVARCHAR(50) NULL,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'en_proceso',                 -- 'en_proceso', 'finalizado', 'ajustado', 'anulado'
    
    -- Responsables
    supervisor_usuario_id UNIQUEIDENTIFIER NULL,
    supervisor_nombre NVARCHAR(150) NULL,
    
    -- Resultados
    total_productos_contados INT DEFAULT 0,
    total_diferencias INT DEFAULT 0,
    valor_diferencias DECIMAL(18,4) DEFAULT 0,
    movimiento_ajuste_id UNIQUEIDENTIFIER NULL,               -- FK al movimiento de ajuste generado
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_finalizacion DATETIME NULL,
    fecha_ajuste DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_invfis_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_invfis_almacen FOREIGN KEY (almacen_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION,
    CONSTRAINT FK_invfis_categoria FOREIGN KEY (categoria_id) 
        REFERENCES inv_categoria_producto(categoria_id) ON DELETE SET NULL,
    CONSTRAINT UQ_invfis_numero UNIQUE (cliente_id, empresa_id, numero_inventario)
);

CREATE INDEX IDX_invfis_empresa ON inv_inventario_fisico(empresa_id, fecha_inventario DESC);
CREATE INDEX IDX_invfis_almacen ON inv_inventario_fisico(almacen_id, estado);
CREATE INDEX IDX_invfis_estado ON inv_inventario_fisico(estado);

-- -----------------------------------------------------------------------------
-- Tabla: inv_inventario_fisico_detalle
-- Descripción: Detalle de conteos por producto
-- Uso: Registro de cantidades contadas vs sistema
-- Relaciones: Detalle de inv_inventario_fisico
-- -----------------------------------------------------------------------------
CREATE TABLE inv_inventario_fisico_detalle (
    inventario_fisico_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    inventario_fisico_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Cantidades
    cantidad_sistema DECIMAL(18,4) NOT NULL,                  -- Stock según sistema
    cantidad_contada DECIMAL(18,4) NULL,                      -- Stock contado físicamente
    diferencia AS (cantidad_contada - cantidad_sistema) PERSISTED,
    
    -- Lote (si maneja)
    lote NVARCHAR(50) NULL,
    fecha_vencimiento DATE NULL,
    
    -- Ubicación
    ubicacion_almacen NVARCHAR(50) NULL,
    
    -- Costeo
    costo_unitario DECIMAL(18,4) DEFAULT 0,
    valor_diferencia AS ((cantidad_contada - cantidad_sistema) * costo_unitario) PERSISTED,
    
    -- Control de conteo
    estado_conteo NVARCHAR(20) DEFAULT 'pendiente',           -- 'pendiente', 'contado', 'recontado', 'ajustado'
    contador_usuario_id UNIQUEIDENTIFIER NULL,
    contador_nombre NVARCHAR(150) NULL,
    fecha_conteo DATETIME NULL,
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    motivo_diferencia NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_invfisdet_invfis FOREIGN KEY (inventario_fisico_id) 
        REFERENCES inv_inventario_fisico(inventario_fisico_id) ON DELETE CASCADE,
    CONSTRAINT FK_invfisdet_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_invfisdet_invfis ON inv_inventario_fisico_detalle(inventario_fisico_id);
CREATE INDEX IDX_invfisdet_producto ON inv_inventario_fisico_detalle(producto_id);
CREATE INDEX IDX_invfisdet_diferencias ON inv_inventario_fisico_detalle(inventario_fisico_id) 
    WHERE ABS(cantidad_contada - cantidad_sistema) > 0.01;

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
    
    CONSTRAINT FK_zona_almacen FOREIGN KEY (almacen_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE CASCADE,
    CONSTRAINT UQ_zona_codigo UNIQUE (cliente_id, almacen_id, codigo)
);

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
    
    CONSTRAINT FK_ubic_almacen FOREIGN KEY (almacen_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE CASCADE,
    CONSTRAINT FK_ubic_zona FOREIGN KEY (zona_id) 
        REFERENCES wms_zona_almacen(zona_id) ON DELETE SET NULL,
    CONSTRAINT UQ_ubic_codigo UNIQUE (cliente_id, almacen_id, codigo_ubicacion)
);

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
    
    CONSTRAINT FK_stockubic_almacen FOREIGN KEY (almacen_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE CASCADE,
    CONSTRAINT FK_stockubic_ubicacion FOREIGN KEY (ubicacion_id) 
        REFERENCES wms_ubicacion(ubicacion_id) ON DELETE CASCADE,
    CONSTRAINT FK_stockubic_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_stockubic_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

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
    
    CONSTRAINT FK_tarea_almacen FOREIGN KEY (almacen_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE CASCADE,
    CONSTRAINT FK_tarea_ubic_origen FOREIGN KEY (ubicacion_origen_id) 
        REFERENCES wms_ubicacion(ubicacion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_tarea_ubic_destino FOREIGN KEY (ubicacion_destino_id) 
        REFERENCES wms_ubicacion(ubicacion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_tarea_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_tarea_numero UNIQUE (cliente_id, almacen_id, numero_tarea)
);

CREATE INDEX IDX_tarea_almacen ON wms_tarea(almacen_id, estado, prioridad);
CREATE INDEX IDX_tarea_asignado ON wms_tarea(asignado_usuario_id, estado) WHERE asignado_usuario_id IS NOT NULL;
CREATE INDEX IDX_tarea_estado ON wms_tarea(estado, fecha_creacion DESC);
CREATE INDEX IDX_tarea_tipo ON wms_tarea(tipo_tarea, estado);

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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_qms_param_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE SET NULL,
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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_qms_plan_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE CASCADE,
    CONSTRAINT FK_qms_plan_categoria FOREIGN KEY (categoria_id) 
        REFERENCES inv_categoria_producto(categoria_id) ON DELETE CASCADE,
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
    
    CONSTRAINT FK_qms_plandet_plan FOREIGN KEY (plan_inspeccion_id) 
        REFERENCES qms_plan_inspeccion(plan_inspeccion_id) ON DELETE CASCADE,
    CONSTRAINT FK_qms_plandet_param FOREIGN KEY (parametro_calidad_id) 
        REFERENCES qms_parametro_calidad(parametro_id) ON DELETE NO ACTION
);

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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_qms_insp_plan FOREIGN KEY (plan_inspeccion_id) 
        REFERENCES qms_plan_inspeccion(plan_inspeccion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_qms_insp_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_qms_insp_almacen FOREIGN KEY (almacen_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE SET NULL,
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
    
    CONSTRAINT FK_qms_inspdet_insp FOREIGN KEY (inspeccion_id) 
        REFERENCES qms_inspeccion(inspeccion_id) ON DELETE CASCADE,
    CONSTRAINT FK_qms_inspdet_param FOREIGN KEY (parametro_calidad_id) 
        REFERENCES qms_parametro_calidad(parametro_id) ON DELETE NO ACTION
);

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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_qms_nc_insp FOREIGN KEY (inspeccion_id) 
        REFERENCES qms_inspeccion(inspeccion_id) ON DELETE SET NULL,
    CONSTRAINT FK_qms_nc_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE SET NULL,
    CONSTRAINT UQ_qms_nc_numero UNIQUE (cliente_id, empresa_id, numero_nc)
);

CREATE INDEX IDX_qms_nc_empresa ON qms_no_conformidad(empresa_id, fecha_deteccion DESC);
CREATE INDEX IDX_qms_nc_estado ON qms_no_conformidad(estado, fecha_deteccion DESC);
CREATE INDEX IDX_qms_nc_tipo ON qms_no_conformidad(tipo_nc);
CREATE INDEX IDX_qms_nc_producto ON qms_no_conformidad(producto_id) WHERE producto_id IS NOT NULL;

-- ============================================================================
-- SECCIÓN 5: PUR - COMPRAS Y ABASTECIMIENTO
-- ============================================================================
-- DESCRIPCIÓN: Gestión de compras, proveedores, órdenes de compra, cotizaciones
-- DEPENDENCIAS: ORG, INV
-- USADO POR: INV (recepción de mercadería), FIN (cuentas por pagar), CST (costos)
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: pur_proveedor
-- Descripción: Catálogo de proveedores
-- Uso: Maestro de proveedores de bienes y servicios
-- Relaciones: Usado por órdenes de compra, cotizaciones
-- -----------------------------------------------------------------------------
CREATE TABLE pur_proveedor (
    proveedor_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Identificación
    codigo_proveedor NVARCHAR(20) NOT NULL,
    razon_social NVARCHAR(200) NOT NULL,
    nombre_comercial NVARCHAR(150) NULL,
    
    -- Documento tributario
    tipo_documento NVARCHAR(10) DEFAULT 'RUC',                -- 'RUC', 'DNI', 'CE', 'PASAPORTE'
    numero_documento NVARCHAR(20) NOT NULL,
    
    -- Clasificación
    tipo_proveedor NVARCHAR(30) DEFAULT 'bienes',             -- 'bienes', 'servicios', 'mixto'
    categoria_proveedor NVARCHAR(50) NULL,                    -- 'materia_prima', 'insumos', 'servicios_generales', etc
    
    -- Dirección fiscal
    direccion NVARCHAR(255) NULL,
    pais NVARCHAR(50) DEFAULT 'Perú',
    departamento NVARCHAR(50) NULL,
    provincia NVARCHAR(50) NULL,
    distrito NVARCHAR(50) NULL,
    ubigeo NVARCHAR(6) NULL,
    
    -- Contacto principal
    contacto_nombre NVARCHAR(150) NULL,
    contacto_cargo NVARCHAR(100) NULL,
    telefono_principal NVARCHAR(20) NULL,
    telefono_secundario NVARCHAR(20) NULL,
    email_principal NVARCHAR(100) NULL,
    email_cotizaciones NVARCHAR(100) NULL,
    sitio_web NVARCHAR(255) NULL,
    
    -- Condiciones comerciales
    condicion_pago_defecto NVARCHAR(50) NULL,                 -- 'contado', '15_dias', '30_dias', '60_dias'
    dias_credito_defecto INT DEFAULT 0,
    moneda_preferida NVARCHAR(3) DEFAULT 'PEN',
    
    -- Datos bancarios
    banco NVARCHAR(100) NULL,
    numero_cuenta NVARCHAR(30) NULL,
    tipo_cuenta NVARCHAR(20) NULL,                            -- 'ahorro', 'corriente', 'interbancaria'
    cci NVARCHAR(20) NULL,                                    -- Código de Cuenta Interbancaria
    
    -- Calificación y evaluación
    calificacion DECIMAL(3,2) NULL,                           -- 0.00 a 5.00
    nivel_confianza NVARCHAR(20) DEFAULT 'medio',             -- 'alto', 'medio', 'bajo'
    es_proveedor_homologado BIT DEFAULT 0,                    -- Si pasó proceso de homologación
    fecha_homologacion DATE NULL,
    
    -- Límites
    limite_credito DECIMAL(18,2) NULL,
    saldo_pendiente DECIMAL(18,2) DEFAULT 0,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'activo',                     -- 'activo', 'inactivo', 'bloqueado', 'evaluacion'
    motivo_bloqueo NVARCHAR(255) NULL,
    es_activo BIT DEFAULT 1 NOT NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    usuario_actualizacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_prov_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT UQ_prov_codigo UNIQUE (cliente_id, empresa_id, codigo_proveedor),
    CONSTRAINT UQ_prov_documento UNIQUE (cliente_id, empresa_id, tipo_documento, numero_documento)
);

CREATE INDEX IDX_prov_empresa ON pur_proveedor(empresa_id, es_activo);
CREATE INDEX IDX_prov_documento ON pur_proveedor(numero_documento);
CREATE INDEX IDX_prov_razon_social ON pur_proveedor(razon_social);
CREATE INDEX IDX_prov_categoria ON pur_proveedor(categoria_proveedor) WHERE categoria_proveedor IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Tabla: pur_proveedor_contacto
-- Descripción: Contactos adicionales del proveedor
-- Uso: Múltiples personas de contacto por proveedor
-- Relaciones: Detalle de pur_proveedor
-- -----------------------------------------------------------------------------
CREATE TABLE pur_proveedor_contacto (
    contacto_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    proveedor_id UNIQUEIDENTIFIER NOT NULL,
    
    nombre_completo NVARCHAR(150) NOT NULL,
    cargo NVARCHAR(100) NULL,
    area NVARCHAR(100) NULL,
    
    telefono NVARCHAR(20) NULL,
    telefono_movil NVARCHAR(20) NULL,
    email NVARCHAR(100) NULL,
    
    es_contacto_principal BIT DEFAULT 0,
    es_contacto_cotizaciones BIT DEFAULT 0,
    es_contacto_cobranzas BIT DEFAULT 0,
    
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_provcon_proveedor FOREIGN KEY (proveedor_id) 
        REFERENCES pur_proveedor(proveedor_id) ON DELETE CASCADE
);

CREATE INDEX IDX_provcon_proveedor ON pur_proveedor_contacto(proveedor_id, es_activo);

-- -----------------------------------------------------------------------------
-- Tabla: pur_producto_proveedor
-- Descripción: Relación producto-proveedor con precios y condiciones
-- Uso: Catálogo de productos que ofrece cada proveedor
-- Relaciones: Vincula inv_producto con pur_proveedor
-- -----------------------------------------------------------------------------
CREATE TABLE pur_producto_proveedor (
    producto_proveedor_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    proveedor_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Identificación del producto en proveedor
    codigo_proveedor NVARCHAR(50) NULL,                       -- SKU/código del proveedor
    descripcion_proveedor NVARCHAR(200) NULL,
    
    -- Precio y condiciones
    precio_unitario DECIMAL(18,4) NOT NULL,
    moneda NVARCHAR(3) DEFAULT 'PEN',
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Compra
    cantidad_minima DECIMAL(18,4) NULL,
    multiplo_compra DECIMAL(18,4) NULL,
    tiempo_entrega_dias INT NULL,
    
    -- Vigencia
    fecha_vigencia_desde DATE NULL,
    fecha_vigencia_hasta DATE NULL,
    
    -- Prioridad
    es_proveedor_preferido BIT DEFAULT 0,
    prioridad INT DEFAULT 3,                                   -- 1=Primera opción, 2=Segunda, etc
    
    -- Estado
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    
    CONSTRAINT FK_prodprov_proveedor FOREIGN KEY (proveedor_id) 
        REFERENCES pur_proveedor(proveedor_id) ON DELETE CASCADE,
    CONSTRAINT FK_prodprov_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE CASCADE,
    CONSTRAINT FK_prodprov_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_prodprov UNIQUE (cliente_id, proveedor_id, producto_id)
);

CREATE INDEX IDX_prodprov_proveedor ON pur_producto_proveedor(proveedor_id, es_activo);
CREATE INDEX IDX_prodprov_producto ON pur_producto_proveedor(producto_id, es_activo);
CREATE INDEX IDX_prodprov_preferido ON pur_producto_proveedor(producto_id, es_proveedor_preferido) 
    WHERE es_proveedor_preferido = 1;

-- -----------------------------------------------------------------------------
-- Tabla: pur_solicitud_compra
-- Descripción: Requerimientos internos de compra (requisiciones)
-- Uso: Solicitudes de compra generadas por áreas/usuarios
-- Relaciones: Antecede a pur_orden_compra
-- -----------------------------------------------------------------------------
CREATE TABLE pur_solicitud_compra (
    solicitud_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_solicitud NVARCHAR(20) NOT NULL,
    fecha_solicitud DATE DEFAULT GETDATE() NOT NULL,
    fecha_requerida DATE NOT NULL,                            -- Fecha en que se necesita
    
    -- Solicitante
    departamento_solicitante_id UNIQUEIDENTIFIER NULL,
    usuario_solicitante_id UNIQUEIDENTIFIER NOT NULL,
    solicitante_nombre NVARCHAR(150) NULL,
    
    -- Destino
    almacen_destino_id UNIQUEIDENTIFIER NULL,
    centro_costo_id UNIQUEIDENTIFIER NULL,
    
    -- Tipo
    tipo_solicitud NVARCHAR(30) DEFAULT 'normal',             -- 'normal', 'urgente', 'proyecto'
    motivo_solicitud NVARCHAR(30) NULL,                       -- 'reposicion', 'nuevo_proyecto', 'mantenimiento', etc
    
    -- Totales
    total_items INT DEFAULT 0,
    total_estimado DECIMAL(18,2) DEFAULT 0,
    moneda NVARCHAR(3) DEFAULT 'PEN',
    
    -- Estado y aprobación
    estado NVARCHAR(20) DEFAULT 'borrador',                   -- 'borrador', 'pendiente_aprobacion', 'aprobada', 'rechazada', 'procesada', 'anulada'
    requiere_aprobacion BIT DEFAULT 1,
    aprobado_por_usuario_id UNIQUEIDENTIFIER NULL,
    fecha_aprobacion DATETIME NULL,
    
    -- Orden de compra generada
    orden_compra_generada BIT DEFAULT 0,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    motivo_rechazo NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_solcomp_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_solcomp_dpto FOREIGN KEY (departamento_solicitante_id) 
        REFERENCES org_departamento(departamento_id) ON DELETE SET NULL,
    CONSTRAINT FK_solcomp_almacen FOREIGN KEY (almacen_destino_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE SET NULL,
    CONSTRAINT FK_solcomp_cc FOREIGN KEY (centro_costo_id) 
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE SET NULL,
    CONSTRAINT UQ_solcomp_numero UNIQUE (cliente_id, empresa_id, numero_solicitud)
);

CREATE INDEX IDX_solcomp_empresa ON pur_solicitud_compra(empresa_id, fecha_solicitud DESC);
CREATE INDEX IDX_solcomp_estado ON pur_solicitud_compra(estado, fecha_solicitud DESC);
CREATE INDEX IDX_solcomp_solicitante ON pur_solicitud_compra(usuario_solicitante_id);
CREATE INDEX IDX_solcomp_dpto ON pur_solicitud_compra(departamento_solicitante_id) WHERE departamento_solicitante_id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Tabla: pur_solicitud_compra_detalle
-- Descripción: Items solicitados en la requisición
-- Uso: Detalle de productos a comprar
-- Relaciones: Detalle de pur_solicitud_compra
-- -----------------------------------------------------------------------------
CREATE TABLE pur_solicitud_compra_detalle (
    solicitud_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    solicitud_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    cantidad_solicitada DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    precio_referencial DECIMAL(18,4) NULL,
    total_referencial AS (cantidad_solicitada * precio_referencial) PERSISTED,
    
    -- Procesamiento
    cantidad_atendida DECIMAL(18,4) DEFAULT 0,
    cantidad_pendiente AS (cantidad_solicitada - cantidad_atendida) PERSISTED,
    
    observaciones NVARCHAR(500) NULL,
    
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_solcompdet_solicitud FOREIGN KEY (solicitud_id) 
        REFERENCES pur_solicitud_compra(solicitud_id) ON DELETE CASCADE,
    CONSTRAINT FK_solcompdet_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_solcompdet_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_solcompdet_solicitud ON pur_solicitud_compra_detalle(solicitud_id);
CREATE INDEX IDX_solcompdet_producto ON pur_solicitud_compra_detalle(producto_id);

-- -----------------------------------------------------------------------------
-- Tabla: pur_cotizacion
-- Descripción: Cotizaciones solicitadas a proveedores
-- Uso: Proceso de comparación de precios
-- Relaciones: Puede originarse de solicitud de compra
-- -----------------------------------------------------------------------------
CREATE TABLE pur_cotizacion (
    cotizacion_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_cotizacion NVARCHAR(20) NOT NULL,
    fecha_cotizacion DATE DEFAULT GETDATE() NOT NULL,
    fecha_vencimiento DATE NULL,
    
    -- Proveedor
    proveedor_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Referencia
    solicitud_compra_id UNIQUEIDENTIFIER NULL,
    
    -- Condiciones
    condicion_pago NVARCHAR(50) NULL,
    dias_credito INT NULL,
    tiempo_entrega_dias INT NULL,
    lugar_entrega NVARCHAR(255) NULL,
    
    -- Totales
    moneda NVARCHAR(3) DEFAULT 'PEN',
    subtotal DECIMAL(18,2) DEFAULT 0,
    descuento DECIMAL(18,2) DEFAULT 0,
    igv DECIMAL(18,2) DEFAULT 0,
    total DECIMAL(18,2) DEFAULT 0,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'pendiente',                  -- 'pendiente', 'recibida', 'evaluada', 'aceptada', 'rechazada', 'vencida'
    es_ganadora BIT DEFAULT 0,                                -- Si fue seleccionada
    
    observaciones NVARCHAR(MAX) NULL,
    motivo_rechazo NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_cotiz_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_cotiz_proveedor FOREIGN KEY (proveedor_id) 
        REFERENCES pur_proveedor(proveedor_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cotiz_solicitud FOREIGN KEY (solicitud_compra_id) 
        REFERENCES pur_solicitud_compra(solicitud_id) ON DELETE SET NULL,
    CONSTRAINT UQ_cotiz_numero UNIQUE (cliente_id, empresa_id, numero_cotizacion)
);

CREATE INDEX IDX_cotiz_empresa ON pur_cotizacion(empresa_id, fecha_cotizacion DESC);
CREATE INDEX IDX_cotiz_proveedor ON pur_cotizacion(proveedor_id, estado);
CREATE INDEX IDX_cotiz_estado ON pur_cotizacion(estado);
CREATE INDEX IDX_cotiz_ganadora ON pur_cotizacion(es_ganadora) WHERE es_ganadora = 1;

-- -----------------------------------------------------------------------------
-- Tabla: pur_cotizacion_detalle
-- Descripción: Items cotizados
-- Uso: Productos y precios ofrecidos por proveedor
-- Relaciones: Detalle de pur_cotizacion
-- -----------------------------------------------------------------------------
CREATE TABLE pur_cotizacion_detalle (
    cotizacion_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    cotizacion_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    cantidad DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    precio_unitario DECIMAL(18,4) NOT NULL,
    descuento_porcentaje DECIMAL(5,2) DEFAULT 0,
    precio_neto AS (precio_unitario * (1 - descuento_porcentaje / 100)) PERSISTED,
    total AS (cantidad * precio_unitario * (1 - descuento_porcentaje / 100)) PERSISTED,
    
    tiempo_entrega_dias INT NULL,
    observaciones NVARCHAR(500) NULL,
    
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_cotizdet_cotizacion FOREIGN KEY (cotizacion_id) 
        REFERENCES pur_cotizacion(cotizacion_id) ON DELETE CASCADE,
    CONSTRAINT FK_cotizdet_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cotizdet_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_cotizdet_cotizacion ON pur_cotizacion_detalle(cotizacion_id);
CREATE INDEX IDX_cotizdet_producto ON pur_cotizacion_detalle(producto_id);

-- -----------------------------------------------------------------------------
-- Tabla: pur_orden_compra
-- Descripción: Orden de compra (documento contractual con proveedor)
-- Uso: Formalización de compra de bienes o servicios
-- Relaciones: Genera movimientos de inventario al recepcionar
-- -----------------------------------------------------------------------------
CREATE TABLE pur_orden_compra (
    orden_compra_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_oc NVARCHAR(20) NOT NULL,
    fecha_emision DATE DEFAULT GETDATE() NOT NULL,
    fecha_requerida DATE NOT NULL,                            -- Fecha esperada de entrega
    
    -- Proveedor
    proveedor_id UNIQUEIDENTIFIER NOT NULL,
    proveedor_razon_social NVARCHAR(200) NULL,                -- Desnormalizado
    proveedor_ruc NVARCHAR(20) NULL,
    
    -- Destino
    almacen_destino_id UNIQUEIDENTIFIER NULL,
    direccion_entrega NVARCHAR(255) NULL,
    
    -- Referencias
    solicitud_compra_id UNIQUEIDENTIFIER NULL,
    cotizacion_id UNIQUEIDENTIFIER NULL,
    
    -- Condiciones comerciales
    condicion_pago NVARCHAR(50) NOT NULL,
    dias_credito INT DEFAULT 0,
    moneda NVARCHAR(3) DEFAULT 'PEN',
    tipo_cambio DECIMAL(10,4) DEFAULT 1,
    
    -- Totales
    subtotal DECIMAL(18,2) DEFAULT 0,
    descuento_global DECIMAL(18,2) DEFAULT 0,
    igv DECIMAL(18,2) DEFAULT 0,
    total DECIMAL(18,2) DEFAULT 0,
    
    -- Control de recepción
    total_items INT DEFAULT 0,
    items_recepcionados INT DEFAULT 0,
    porcentaje_recepcion DECIMAL(5,2) DEFAULT 0,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'borrador',                   -- 'borrador', 'emitida', 'aprobada', 'parcial', 'completa', 'anulada'
    requiere_aprobacion BIT DEFAULT 1,
    aprobado_por_usuario_id UNIQUEIDENTIFIER NULL,
    fecha_aprobacion DATETIME NULL,
    
    -- Centro de costo
    centro_costo_id UNIQUEIDENTIFIER NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    terminos_condiciones NVARCHAR(MAX) NULL,
    motivo_anulacion NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    fecha_anulacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    usuario_aprobacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_oc_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_oc_proveedor FOREIGN KEY (proveedor_id) 
        REFERENCES pur_proveedor(proveedor_id) ON DELETE NO ACTION,
    CONSTRAINT FK_oc_almacen FOREIGN KEY (almacen_destino_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE SET NULL,
    CONSTRAINT FK_oc_solicitud FOREIGN KEY (solicitud_compra_id) 
        REFERENCES pur_solicitud_compra(solicitud_id) ON DELETE SET NULL,
    CONSTRAINT FK_oc_cotizacion FOREIGN KEY (cotizacion_id) 
        REFERENCES pur_cotizacion(cotizacion_id) ON DELETE SET NULL,
    CONSTRAINT FK_oc_cc FOREIGN KEY (centro_costo_id) 
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE SET NULL,
    CONSTRAINT UQ_oc_numero UNIQUE (cliente_id, empresa_id, numero_oc)
);

CREATE INDEX IDX_oc_empresa ON pur_orden_compra(empresa_id, fecha_emision DESC);
CREATE INDEX IDX_oc_proveedor ON pur_orden_compra(proveedor_id, estado);
CREATE INDEX IDX_oc_estado ON pur_orden_compra(estado, fecha_emision DESC);
CREATE INDEX IDX_oc_fecha_requerida ON pur_orden_compra(fecha_requerida, estado);
CREATE INDEX IDX_oc_solicitud ON pur_orden_compra(solicitud_compra_id) WHERE solicitud_compra_id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Tabla: pur_orden_compra_detalle
-- Descripción: Items de la orden de compra
-- Uso: Productos o servicios a comprar
-- Relaciones: Detalle de pur_orden_compra
-- -----------------------------------------------------------------------------
CREATE TABLE pur_orden_compra_detalle (
    orden_compra_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    orden_compra_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Cantidad y unidad
    cantidad_ordenada DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Precios
    precio_unitario DECIMAL(18,4) NOT NULL,
    descuento_porcentaje DECIMAL(5,2) DEFAULT 0,
    precio_neto AS (precio_unitario * (1 - descuento_porcentaje / 100)) PERSISTED,
    subtotal AS (cantidad_ordenada * precio_unitario * (1 - descuento_porcentaje / 100)) PERSISTED,
    igv AS (cantidad_ordenada * precio_unitario * (1 - descuento_porcentaje / 100) * 0.18) PERSISTED,
    total AS (cantidad_ordenada * precio_unitario * (1 - descuento_porcentaje / 100) * 1.18) PERSISTED,
    
    -- Control de recepción
    cantidad_recepcionada DECIMAL(18,4) DEFAULT 0,
    cantidad_pendiente AS (cantidad_ordenada - cantidad_recepcionada) PERSISTED,
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    especificaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_ocdet_oc FOREIGN KEY (orden_compra_id) 
        REFERENCES pur_orden_compra(orden_compra_id) ON DELETE CASCADE,
    CONSTRAINT FK_ocdet_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_ocdet_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_ocdet_oc ON pur_orden_compra_detalle(orden_compra_id);
CREATE INDEX IDX_ocdet_producto ON pur_orden_compra_detalle(producto_id);
CREATE INDEX IDX_ocdet_pendiente ON pur_orden_compra_detalle(orden_compra_id) 
    WHERE cantidad_pendiente > 0;

-- -----------------------------------------------------------------------------
-- Tabla: pur_recepcion
-- Descripción: Recepción de mercadería
-- Uso: Registro de entrada física de productos comprados
-- Relaciones: Vinculada a OC, genera movimiento de inventario
-- -----------------------------------------------------------------------------
CREATE TABLE pur_recepcion (
    recepcion_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_recepcion NVARCHAR(20) NOT NULL,
    fecha_recepcion DATETIME DEFAULT GETDATE() NOT NULL,
    
    -- Orden de compra
    orden_compra_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Proveedor
    proveedor_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Almacén
    almacen_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Documento de transporte
    guia_remision_numero NVARCHAR(30) NULL,
    guia_remision_fecha DATE NULL,
    transportista NVARCHAR(150) NULL,
    placa_vehiculo NVARCHAR(15) NULL,
    
    -- Responsable recepción
    recepcionado_por_usuario_id UNIQUEIDENTIFIER NULL,
    recepcionado_por_nombre NVARCHAR(150) NULL,
    
    -- Totales
    total_items INT DEFAULT 0,
    total_cantidad DECIMAL(18,4) DEFAULT 0,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'borrador',                   -- 'borrador', 'procesada', 'inspeccion', 'aprobada', 'anulada'
    requiere_inspeccion BIT DEFAULT 0,                        -- Si requiere QMS
    inspeccion_id UNIQUEIDENTIFIER NULL,                      -- FK a qms_inspeccion
    
    -- Movimiento de inventario generado
    movimiento_inventario_id UNIQUEIDENTIFIER NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    incidencias NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_procesado DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    usuario_procesado_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_recep_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_recep_oc FOREIGN KEY (orden_compra_id) 
        REFERENCES pur_orden_compra(orden_compra_id) ON DELETE NO ACTION,
    CONSTRAINT FK_recep_proveedor FOREIGN KEY (proveedor_id) 
        REFERENCES pur_proveedor(proveedor_id) ON DELETE NO ACTION,
    CONSTRAINT FK_recep_almacen FOREIGN KEY (almacen_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_recep_numero UNIQUE (cliente_id, empresa_id, numero_recepcion)
);

CREATE INDEX IDX_recep_empresa ON pur_recepcion(empresa_id, fecha_recepcion DESC);
CREATE INDEX IDX_recep_oc ON pur_recepcion(orden_compra_id);
CREATE INDEX IDX_recep_estado ON pur_recepcion(estado);
CREATE INDEX IDX_recep_almacen ON pur_recepcion(almacen_id);

-- -----------------------------------------------------------------------------
-- Tabla: pur_recepcion_detalle
-- Descripción: Items recepcionados
-- Uso: Productos recibidos con cantidades
-- Relaciones: Detalle de pur_recepcion
-- -----------------------------------------------------------------------------
CREATE TABLE pur_recepcion_detalle (
    recepcion_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    recepcion_id UNIQUEIDENTIFIER NOT NULL,
    orden_compra_detalle_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Cantidad
    cantidad_ordenada DECIMAL(18,4) NOT NULL,                 -- Según OC
    cantidad_recepcionada DECIMAL(18,4) NOT NULL,             -- Real recibida
    diferencia AS (cantidad_recepcionada - cantidad_ordenada) PERSISTED,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Lote y vencimiento
    lote NVARCHAR(50) NULL,
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
    
    CONSTRAINT FK_recepdet_recepcion FOREIGN KEY (recepcion_id) 
        REFERENCES pur_recepcion(recepcion_id) ON DELETE CASCADE,
    CONSTRAINT FK_recepdet_ocdet FOREIGN KEY (orden_compra_detalle_id) 
        REFERENCES pur_orden_compra_detalle(orden_compra_detalle_id) ON DELETE NO ACTION,
    CONSTRAINT FK_recepdet_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_recepdet_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_recepdet_recepcion ON pur_recepcion_detalle(recepcion_id);
CREATE INDEX IDX_recepdet_ocdet ON pur_recepcion_detalle(orden_compra_detalle_id);
CREATE INDEX IDX_recepdet_producto ON pur_recepcion_detalle(producto_id);

PRINT 'SECCIÓN 1-5 creada: ORG, INV, WMS, QMS, PUR';
GO

-- ============================================================================
-- SCRIPT: MÓDULOS ERP COMPLETO - PARTE 2
-- DESCRIPCIÓN: Continuación de módulos (LOG, MFG, MRP, MPS, MNT)
-- DEPENDENCIAS: Ejecutar después de PARTE 1 (ORG, INV, WMS, QMS, PUR)
-- ============================================================================

-- ============================================================================
-- SECCIÓN 6: LOG - LOGÍSTICA Y DISTRIBUCIÓN
-- ============================================================================
-- DESCRIPCIÓN: Gestión de transporte, rutas, despachos, distribución
-- DEPENDENCIAS: ORG, INV, PUR (compras con transporte), SLS (ventas con despacho)
-- USADO POR: Control de flota, entregas, seguimiento de envíos
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: log_transportista
-- Descripción: Catálogo de empresas transportistas
-- Uso: Terceros que realizan transporte de mercadería
-- Relaciones: Usado en log_guia_remision, log_despacho
-- -----------------------------------------------------------------------------
CREATE TABLE log_transportista (
    transportista_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_transportista NVARCHAR(20) NOT NULL,
    razon_social NVARCHAR(200) NOT NULL,
    nombre_comercial NVARCHAR(150) NULL,
    
    tipo_documento NVARCHAR(10) DEFAULT 'RUC',
    numero_documento NVARCHAR(20) NOT NULL,
    
    -- Licencias y permisos
    numero_mtc NVARCHAR(30) NULL,                             -- Registro MTC (Ministerio de Transportes)
    licencia_tipo NVARCHAR(50) NULL,
    
    -- Contacto
    telefono NVARCHAR(20) NULL,
    email NVARCHAR(100) NULL,
    direccion NVARCHAR(255) NULL,
    
    -- Tarifas
    tarifa_km DECIMAL(10,2) NULL,
    tarifa_hora DECIMAL(10,2) NULL,
    moneda_tarifa NVARCHAR(3) DEFAULT 'PEN',
    
    -- Calificación
    calificacion DECIMAL(3,2) NULL,
    
    -- Estado
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_transp_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT UQ_transp_codigo UNIQUE (cliente_id, empresa_id, codigo_transportista)
);

CREATE INDEX IDX_transp_empresa ON log_transportista(empresa_id, es_activo);

-- -----------------------------------------------------------------------------
-- Tabla: log_vehiculo
-- Descripción: Flota de vehículos (propios o de transportistas)
-- Uso: Control de vehículos para despacho y transporte
-- Relaciones: Asignados a transportistas o empresa propia
-- -----------------------------------------------------------------------------
CREATE TABLE log_vehiculo (
    vehiculo_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    placa NVARCHAR(15) NOT NULL,
    marca NVARCHAR(50) NULL,
    modelo NVARCHAR(50) NULL,
    año INT NULL,
    color NVARCHAR(30) NULL,
    
    -- Tipo
    tipo_vehiculo NVARCHAR(30) NOT NULL,                      -- 'camion', 'camioneta', 'furgon', 'moto', 'trailer'
    categoria_vehiculo NVARCHAR(20) NULL,                     -- 'ligero', 'mediano', 'pesado'
    
    -- Capacidad
    capacidad_kg DECIMAL(12,2) NULL,
    capacidad_m3 DECIMAL(12,2) NULL,
    
    -- Propietario
    tipo_propiedad NVARCHAR(20) NOT NULL,                     -- 'propio', 'tercero'
    transportista_id UNIQUEIDENTIFIER NULL,                   -- Si es de tercero
    
    -- Conductor habitual
    conductor_nombre NVARCHAR(150) NULL,
    conductor_licencia NVARCHAR(20) NULL,
    conductor_telefono NVARCHAR(20) NULL,
    
    -- Documentos
    tarjeta_propiedad NVARCHAR(30) NULL,
    soat_numero NVARCHAR(30) NULL,
    soat_vencimiento DATE NULL,
    revision_tecnica_vencimiento DATE NULL,
    
    -- GPS/Rastreo
    tiene_gps BIT DEFAULT 0,
    codigo_gps NVARCHAR(50) NULL,
    
    -- Estado
    estado_vehiculo NVARCHAR(20) DEFAULT 'disponible',        -- 'disponible', 'en_ruta', 'mantenimiento', 'inactivo'
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_vehiculo_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_vehiculo_transp FOREIGN KEY (transportista_id) 
        REFERENCES log_transportista(transportista_id) ON DELETE SET NULL,
    CONSTRAINT UQ_vehiculo_placa UNIQUE (cliente_id, empresa_id, placa)
);

CREATE INDEX IDX_vehiculo_empresa ON log_vehiculo(empresa_id, es_activo);
CREATE INDEX IDX_vehiculo_estado ON log_vehiculo(estado_vehiculo);
CREATE INDEX IDX_vehiculo_transp ON log_vehiculo(transportista_id) WHERE transportista_id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Tabla: log_ruta
-- Descripción: Rutas de distribución predefinidas
-- Uso: Rutas frecuentes origen-destino
-- Relaciones: Usado en planificación de despachos
-- -----------------------------------------------------------------------------
CREATE TABLE log_ruta (
    ruta_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_ruta NVARCHAR(20) NOT NULL,
    nombre_ruta NVARCHAR(100) NOT NULL,
    
    -- Origen-Destino
    origen_sucursal_id UNIQUEIDENTIFIER NULL,
    origen_descripcion NVARCHAR(255) NULL,
    destino_descripcion NVARCHAR(255) NULL,
    
    -- Datos geográficos
    departamento_origen NVARCHAR(50) NULL,
    departamento_destino NVARCHAR(50) NULL,
    
    -- Características
    distancia_km DECIMAL(10,2) NULL,
    tiempo_estimado_horas DECIMAL(5,2) NULL,
    tipo_carretera NVARCHAR(30) NULL,                         -- 'asfalto', 'trocha', 'mixta'
    
    -- Costos
    costo_estimado DECIMAL(12,2) NULL,
    moneda NVARCHAR(3) DEFAULT 'PEN',
    
    -- Peajes y paradas
    cantidad_peajes INT DEFAULT 0,
    costo_peajes DECIMAL(10,2) DEFAULT 0,
    puntos_intermedios NVARCHAR(MAX) NULL,                    -- JSON con paradas
    
    -- Estado
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_ruta_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_ruta_origen_suc FOREIGN KEY (origen_sucursal_id) 
        REFERENCES org_sucursal(sucursal_id) ON DELETE SET NULL,
    CONSTRAINT UQ_ruta_codigo UNIQUE (cliente_id, empresa_id, codigo_ruta)
);

CREATE INDEX IDX_ruta_empresa ON log_ruta(empresa_id, es_activo);

-- -----------------------------------------------------------------------------
-- Tabla: log_guia_remision
-- Descripción: Guías de remisión (documento de transporte)
-- Uso: Documento legal para traslado de mercadería
-- Relaciones: Vinculada a ventas, transferencias, compras
-- -----------------------------------------------------------------------------
CREATE TABLE log_guia_remision (
    guia_remision_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Numeración
    serie NVARCHAR(4) NOT NULL,
    numero NVARCHAR(10) NOT NULL,
    numero_completo AS (serie + '-' + numero) PERSISTED,
    
    fecha_emision DATE DEFAULT GETDATE() NOT NULL,
    fecha_traslado DATE NOT NULL,
    
    -- Tipo de guía
    tipo_guia NVARCHAR(30) NOT NULL,                          -- 'remitente', 'transportista'
    motivo_traslado NVARCHAR(30) NOT NULL,                    -- 'venta', 'compra', 'transferencia', 'consignacion', 'devolucion'
    
    -- Remitente
    remitente_razon_social NVARCHAR(200) NOT NULL,
    remitente_ruc NVARCHAR(11) NOT NULL,
    remitente_direccion NVARCHAR(255) NULL,
    
    -- Destinatario
    destinatario_razon_social NVARCHAR(200) NOT NULL,
    destinatario_documento_tipo NVARCHAR(10) NULL,
    destinatario_documento_numero NVARCHAR(20) NULL,
    destinatario_direccion NVARCHAR(255) NULL,
    
    -- Punto de partida y llegada
    punto_partida NVARCHAR(255) NOT NULL,
    punto_partida_ubigeo NVARCHAR(6) NULL,
    punto_llegada NVARCHAR(255) NOT NULL,
    punto_llegada_ubigeo NVARCHAR(6) NULL,
    
    -- Transporte
    modalidad_transporte NVARCHAR(20) NOT NULL,               -- 'publico', 'privado'
    transportista_id UNIQUEIDENTIFIER NULL,
    transportista_razon_social NVARCHAR(200) NULL,
    transportista_ruc NVARCHAR(11) NULL,
    
    -- Vehículo y conductor
    vehiculo_id UNIQUEIDENTIFIER NULL,
    vehiculo_placa NVARCHAR(15) NULL,
    conductor_nombre NVARCHAR(150) NULL,
    conductor_documento_tipo NVARCHAR(10) NULL,
    conductor_documento_numero NVARCHAR(20) NULL,
    conductor_licencia NVARCHAR(20) NULL,
    
    -- Bultos
    total_bultos INT DEFAULT 0,
    peso_total_kg DECIMAL(12,2) DEFAULT 0,
    
    -- Documento sustento
    documento_sustento_tipo NVARCHAR(20) NULL,                -- 'factura', 'boleta', 'orden_compra'
    documento_sustento_serie NVARCHAR(4) NULL,
    documento_sustento_numero NVARCHAR(10) NULL,
    
    -- Referencia interna
    movimiento_inventario_id UNIQUEIDENTIFIER NULL,
    venta_id UNIQUEIDENTIFIER NULL,                           -- FK a sls_venta (módulo SLS)
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'emitida',                    -- 'borrador', 'emitida', 'en_transito', 'entregada', 'anulada'
    fecha_entrega DATETIME NULL,
    
    -- Firma digital (SUNAT Perú)
    codigo_hash NVARCHAR(100) NULL,
    codigo_qr NVARCHAR(MAX) NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_anulacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_guia_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_guia_transp FOREIGN KEY (transportista_id) 
        REFERENCES log_transportista(transportista_id) ON DELETE SET NULL,
    CONSTRAINT FK_guia_vehiculo FOREIGN KEY (vehiculo_id) 
        REFERENCES log_vehiculo(vehiculo_id) ON DELETE SET NULL,
    CONSTRAINT UQ_guia_numero UNIQUE (cliente_id, empresa_id, serie, numero)
);

CREATE INDEX IDX_guia_empresa ON log_guia_remision(empresa_id, fecha_emision DESC);
CREATE INDEX IDX_guia_estado ON log_guia_remision(estado);
CREATE INDEX IDX_guia_numero ON log_guia_remision(numero_completo);

-- -----------------------------------------------------------------------------
-- Tabla: log_guia_remision_detalle
-- Descripción: Items transportados en la guía
-- Uso: Productos y cantidades en el traslado
-- Relaciones: Detalle de log_guia_remision
-- -----------------------------------------------------------------------------
CREATE TABLE log_guia_remision_detalle (
    guia_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    guia_remision_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    cantidad DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    descripcion NVARCHAR(255) NULL,
    peso_kg DECIMAL(12,2) NULL,
    
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_guiadet_guia FOREIGN KEY (guia_remision_id) 
        REFERENCES log_guia_remision(guia_remision_id) ON DELETE CASCADE,
    CONSTRAINT FK_guiadet_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_guiadet_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_guiadet_guia ON log_guia_remision_detalle(guia_remision_id);

-- -----------------------------------------------------------------------------
-- Tabla: log_despacho
-- Descripción: Planificación y ejecución de despachos
-- Uso: Agrupar pedidos para una misma ruta/vehículo
-- Relaciones: Agrupa múltiples guías de remisión
-- -----------------------------------------------------------------------------
CREATE TABLE log_despacho (
    despacho_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_despacho NVARCHAR(20) NOT NULL,
    fecha_programada DATE NOT NULL,
    hora_salida_programada TIME NULL,
    
    -- Ruta
    ruta_id UNIQUEIDENTIFIER NULL,
    origen_sucursal_id UNIQUEIDENTIFIER NULL,
    
    -- Vehículo y conductor
    vehiculo_id UNIQUEIDENTIFIER NULL,
    conductor_nombre NVARCHAR(150) NULL,
    conductor_telefono NVARCHAR(20) NULL,
    
    -- Detalles de ejecución
    fecha_salida_real DATETIME NULL,
    fecha_retorno DATETIME NULL,
    km_inicial DECIMAL(10,2) NULL,
    km_final DECIMAL(10,2) NULL,
    km_recorrido AS (km_final - km_inicial) PERSISTED,
    
    -- Totales
    total_guias INT DEFAULT 0,
    total_peso_kg DECIMAL(12,2) DEFAULT 0,
    total_bultos INT DEFAULT 0,
    
    -- Costos
    costo_combustible DECIMAL(12,2) NULL,
    costo_peajes DECIMAL(12,2) NULL,
    otros_gastos DECIMAL(12,2) NULL,
    costo_total AS (ISNULL(costo_combustible,0) + ISNULL(costo_peajes,0) + ISNULL(otros_gastos,0)) PERSISTED,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'planificado',                -- 'planificado', 'en_ruta', 'completado', 'cancelado'
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    incidencias NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_desp_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_desp_ruta FOREIGN KEY (ruta_id) 
        REFERENCES log_ruta(ruta_id) ON DELETE SET NULL,
    CONSTRAINT FK_desp_vehiculo FOREIGN KEY (vehiculo_id) 
        REFERENCES log_vehiculo(vehiculo_id) ON DELETE SET NULL,
    CONSTRAINT FK_desp_origen FOREIGN KEY (origen_sucursal_id) 
        REFERENCES org_sucursal(sucursal_id) ON DELETE SET NULL,
    CONSTRAINT UQ_desp_numero UNIQUE (cliente_id, empresa_id, numero_despacho)
);

CREATE INDEX IDX_desp_empresa ON log_despacho(empresa_id, fecha_programada DESC);
CREATE INDEX IDX_desp_estado ON log_despacho(estado);
CREATE INDEX IDX_desp_vehiculo ON log_despacho(vehiculo_id, fecha_programada);

-- -----------------------------------------------------------------------------
-- Tabla: log_despacho_guia
-- Descripción: Guías de remisión incluidas en un despacho
-- Uso: Relación muchos a muchos entre despachos y guías
-- Relaciones: Vincula log_despacho con log_guia_remision
-- -----------------------------------------------------------------------------
CREATE TABLE log_despacho_guia (
    despacho_guia_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    despacho_id UNIQUEIDENTIFIER NOT NULL,
    guia_remision_id UNIQUEIDENTIFIER NOT NULL,
    
    orden_entrega INT NULL,                                    -- Secuencia de entrega
    fecha_entrega DATETIME NULL,
    estado_entrega NVARCHAR(20) DEFAULT 'pendiente',          -- 'pendiente', 'entregado', 'no_entregado'
    observaciones_entrega NVARCHAR(500) NULL,
    
    receptor_nombre NVARCHAR(150) NULL,
    receptor_documento NVARCHAR(20) NULL,
    
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_despguia_desp FOREIGN KEY (despacho_id) 
        REFERENCES log_despacho(despacho_id) ON DELETE CASCADE,
    CONSTRAINT FK_despguia_guia FOREIGN KEY (guia_remision_id) 
        REFERENCES log_guia_remision(guia_remision_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_desp_guia UNIQUE (cliente_id, despacho_id, guia_remision_id)
);

CREATE INDEX IDX_despguia_desp ON log_despacho_guia(despacho_id, orden_entrega);
CREATE INDEX IDX_despguia_guia ON log_despacho_guia(guia_remision_id);

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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_ct_sucursal FOREIGN KEY (sucursal_id) 
        REFERENCES org_sucursal(sucursal_id) ON DELETE SET NULL,
    CONSTRAINT FK_ct_cc FOREIGN KEY (centro_costo_id) 
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE SET NULL,
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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_oper_ct FOREIGN KEY (centro_trabajo_id) 
        REFERENCES mfg_centro_trabajo(centro_trabajo_id) ON DELETE SET NULL,
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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_bom_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE CASCADE,
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
    
    CONSTRAINT FK_bomdet_bom FOREIGN KEY (bom_id) 
        REFERENCES mfg_lista_materiales(bom_id) ON DELETE CASCADE,
    CONSTRAINT FK_bomdet_componente FOREIGN KEY (producto_componente_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_bomdet_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

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
    
    CONSTRAINT FK_ruta_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_ruta_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE CASCADE,
    CONSTRAINT FK_ruta_bom FOREIGN KEY (bom_id) 
        REFERENCES mfg_lista_materiales(bom_id) ON DELETE SET NULL,
    CONSTRAINT UQ_ruta_codigo UNIQUE (cliente_id, empresa_id, codigo_ruta)
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
    
    CONSTRAINT FK_rutadet_ruta FOREIGN KEY (ruta_id) 
        REFERENCES mfg_ruta_fabricacion(ruta_id) ON DELETE CASCADE,
    CONSTRAINT FK_rutadet_oper FOREIGN KEY (operacion_id) 
        REFERENCES mfg_operacion(operacion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_rutadet_ct FOREIGN KEY (centro_trabajo_id) 
        REFERENCES mfg_centro_trabajo(centro_trabajo_id) ON DELETE NO ACTION
);

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
    moneda NVARCHAR(3) DEFAULT 'PEN',
    
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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_op_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_op_bom FOREIGN KEY (bom_id) 
        REFERENCES mfg_lista_materiales(bom_id) ON DELETE NO ACTION,
    CONSTRAINT FK_op_ruta FOREIGN KEY (ruta_fabricacion_id) 
        REFERENCES mfg_ruta_fabricacion(ruta_id) ON DELETE SET NULL,
    CONSTRAINT FK_op_almacen FOREIGN KEY (almacen_destino_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE SET NULL,
    CONSTRAINT FK_op_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT FK_op_cc FOREIGN KEY (centro_costo_id) 
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE SET NULL,
    CONSTRAINT UQ_op_numero UNIQUE (cliente_id, empresa_id, numero_op)
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
    
    CONSTRAINT FK_opoper_op FOREIGN KEY (orden_produccion_id) 
        REFERENCES mfg_orden_produccion(orden_produccion_id) ON DELETE CASCADE,
    CONSTRAINT FK_opoper_rutadet FOREIGN KEY (ruta_detalle_id) 
        REFERENCES mfg_ruta_fabricacion_detalle(ruta_detalle_id) ON DELETE SET NULL,
    CONSTRAINT FK_opoper_oper FOREIGN KEY (operacion_id) 
        REFERENCES mfg_operacion(operacion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_opoper_ct FOREIGN KEY (centro_trabajo_id) 
        REFERENCES mfg_centro_trabajo(centro_trabajo_id) ON DELETE NO ACTION
);

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
    
    CONSTRAINT FK_consumo_op FOREIGN KEY (orden_produccion_id) 
        REFERENCES mfg_orden_produccion(orden_produccion_id) ON DELETE CASCADE,
    CONSTRAINT FK_consumo_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_consumo_almacen FOREIGN KEY (almacen_origen_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE SET NULL,
    CONSTRAINT FK_consumo_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_consumo_op ON mfg_consumo_materiales(orden_produccion_id);
CREATE INDEX IDX_consumo_producto ON mfg_consumo_materiales(producto_id, fecha_consumo DESC);

-- ============================================================================
-- SECCIÓN 8: MRP - MATERIAL REQUIREMENTS PLANNING (PLANEAMIENTO DE MATERIALES)
-- ============================================================================
-- DESCRIPCIÓN: Planificación de necesidades de materiales
-- DEPENDENCIAS: ORG, INV, MFG (BOM, órdenes producción)
-- USADO POR: PUR (generación automática de requisiciones)
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: mrp_plan_maestro
-- Descripción: Plan maestro de producción (MPS agregado con MRP)
-- Uso: Horizonte de planificación de necesidades
-- Relaciones: Base para ejecutar explosión de materiales
-- -----------------------------------------------------------------------------
CREATE TABLE mrp_plan_maestro (
    plan_maestro_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_plan NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(255) NULL,
    
    -- Periodo de planificación
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    tipo_periodo NVARCHAR(20) DEFAULT 'semanal',              -- 'diario', 'semanal', 'mensual'
    
    -- Configuración
    horizonte_planificacion_dias INT DEFAULT 90,
    punto_reorden_dias INT DEFAULT 15,                        -- Cuándo generar orden de compra
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'borrador',                   -- 'borrador', 'calculado', 'aprobado', 'ejecutado', 'cerrado'
    fecha_calculo DATETIME NULL,
    fecha_aprobacion DATETIME NULL,
    
    -- Resultados
    total_productos_planificados INT DEFAULT 0,
    total_requisiciones_generadas INT DEFAULT 0,
    total_ordenes_sugeridas INT DEFAULT 0,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_planmrp_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT UQ_planmrp_codigo UNIQUE (cliente_id, empresa_id, codigo_plan)
);

CREATE INDEX IDX_planmrp_empresa ON mrp_plan_maestro(empresa_id, fecha_inicio DESC);
CREATE INDEX IDX_planmrp_estado ON mrp_plan_maestro(estado);

-- -----------------------------------------------------------------------------
-- Tabla: mrp_necesidad_bruta
-- Descripción: Necesidades brutas de productos (demanda + stock seguridad)
-- Uso: Entrada del MRP - qué se necesita y cuándo
-- Relaciones: Puede originarse de pedidos de venta, pronósticos, reposición
-- -----------------------------------------------------------------------------
CREATE TABLE mrp_necesidad_bruta (
    necesidad_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    plan_maestro_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    fecha_requerida DATE NOT NULL,
    cantidad_requerida DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Origen de la necesidad
    origen NVARCHAR(30) NOT NULL,                             -- 'pedido_venta', 'pronostico', 'stock_seguridad', 'orden_produccion'
    documento_origen_id UNIQUEIDENTIFIER NULL,
    documento_origen_numero NVARCHAR(30) NULL,
    
    -- Prioridad
    prioridad INT DEFAULT 3,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_necbruta_plan FOREIGN KEY (plan_maestro_id) 
        REFERENCES mrp_plan_maestro(plan_maestro_id) ON DELETE CASCADE,
    CONSTRAINT FK_necbruta_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_necbruta_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_necbruta_plan ON mrp_necesidad_bruta(plan_maestro_id, fecha_requerida);
CREATE INDEX IDX_necbruta_producto ON mrp_necesidad_bruta(producto_id, fecha_requerida);

-- -----------------------------------------------------------------------------
-- Tabla: mrp_explosion_materiales
-- Descripción: Resultado de la explosión de BOM (necesidades de componentes)
-- Uso: Cálculo de qué materiales se necesitan para producir
-- Relaciones: Generado automáticamente desde BOM y necesidades brutas
-- -----------------------------------------------------------------------------
CREATE TABLE mrp_explosion_materiales (
    explosion_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    plan_maestro_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Producto padre (lo que se va a producir)
    producto_padre_id UNIQUEIDENTIFIER NOT NULL,
    necesidad_padre_id UNIQUEIDENTIFIER NULL,                 -- FK a mrp_necesidad_bruta
    
    -- Componente (material que se necesita)
    producto_componente_id UNIQUEIDENTIFIER NOT NULL,
    bom_detalle_id UNIQUEIDENTIFIER NULL,                     -- De dónde salió la necesidad
    
    -- Nivel en BOM
    nivel_bom INT DEFAULT 1,                                   -- 1=componente directo, 2=sub-componente, etc
    
    -- Cantidad
    cantidad_necesaria DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Fecha requerida
    fecha_requerida DATE NOT NULL,
    
    -- Stock disponible
    stock_actual DECIMAL(18,4) DEFAULT 0,
    stock_reservado DECIMAL(18,4) DEFAULT 0,
    stock_transito DECIMAL(18,4) DEFAULT 0,
    stock_disponible AS (stock_actual - stock_reservado + stock_transito) PERSISTED,
    
    -- Necesidad neta
    cantidad_a_ordenar AS (
        CASE 
            WHEN cantidad_necesaria > (stock_actual - stock_reservado + stock_transito)
            THEN cantidad_necesaria - (stock_actual - stock_reservado + stock_transito)
            ELSE 0
        END
    ) PERSISTED,
    
    -- Auditoría
    fecha_calculo DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_explosion_plan FOREIGN KEY (plan_maestro_id) 
        REFERENCES mrp_plan_maestro(plan_maestro_id) ON DELETE CASCADE,
    CONSTRAINT FK_explosion_padre FOREIGN KEY (producto_padre_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_explosion_componente FOREIGN KEY (producto_componente_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_explosion_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_explosion_plan ON mrp_explosion_materiales(plan_maestro_id, nivel_bom);
CREATE INDEX IDX_explosion_componente ON mrp_explosion_materiales(producto_componente_id, fecha_requerida);

-- -----------------------------------------------------------------------------
-- Tabla: mrp_orden_sugerida
-- Descripción: Órdenes de compra o producción sugeridas por MRP
-- Uso: Recomendaciones del sistema para cubrir necesidades
-- Relaciones: Se pueden convertir en órdenes de compra o producción reales
-- -----------------------------------------------------------------------------
CREATE TABLE mrp_orden_sugerida (
    orden_sugerida_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    plan_maestro_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    tipo_orden NVARCHAR(20) NOT NULL,                         -- 'compra', 'produccion', 'transferencia'
    
    cantidad_sugerida DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    fecha_requerida DATE NOT NULL,
    fecha_orden_sugerida DATE NOT NULL,                       -- Cuándo se debe ordenar (considerando lead time)
    
    -- Origen de la sugerencia
    explosion_materiales_id UNIQUEIDENTIFIER NULL,
    
    -- Proveedor sugerido (si es compra)
    proveedor_sugerido_id UNIQUEIDENTIFIER NULL,
    
    -- Lead time
    lead_time_dias INT NULL,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'sugerida',                   -- 'sugerida', 'aprobada', 'convertida', 'rechazada'
    
    -- Conversión a documento real
    documento_generado_tipo NVARCHAR(20) NULL,                -- 'orden_compra', 'orden_produccion'
    documento_generado_id UNIQUEIDENTIFIER NULL,
    fecha_conversion DATETIME NULL,
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_ordsug_plan FOREIGN KEY (plan_maestro_id) 
        REFERENCES mrp_plan_maestro(plan_maestro_id) ON DELETE CASCADE,
    CONSTRAINT FK_ordsug_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_ordsug_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT FK_ordsug_prov FOREIGN KEY (proveedor_sugerido_id) 
        REFERENCES pur_proveedor(proveedor_id) ON DELETE SET NULL
);

CREATE INDEX IDX_ordsug_plan ON mrp_orden_sugerida(plan_maestro_id, estado);
CREATE INDEX IDX_ordsug_producto ON mrp_orden_sugerida(producto_id, fecha_requerida);
CREATE INDEX IDX_ordsug_estado ON mrp_orden_sugerida(estado, tipo_orden);

-- ============================================================================
-- SECCIÓN 9: MPS - MASTER PRODUCTION SCHEDULE (PLAN MAESTRO DE PRODUCCIÓN)
-- ============================================================================
-- DESCRIPCIÓN: Planificación agregada de producción
-- DEPENDENCIAS: ORG, INV, MFG
-- USADO POR: MRP (entrada para explosión de materiales)
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: mps_pronostico_demanda
-- Descripción: Pronósticos de ventas/demanda
-- Uso: Estimación de demanda futura para planificar producción
-- Relaciones: Base para el MPS
-- -----------------------------------------------------------------------------
CREATE TABLE mps_pronostico_demanda (
    pronostico_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Periodo
    año INT NOT NULL,
    mes INT NOT NULL,
    semana INT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    
    -- Demanda pronosticada
    cantidad_pronosticada DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Método de pronóstico
    metodo_pronostico NVARCHAR(30) NULL,                      -- 'historico', 'tendencia', 'estacional', 'manual'
    confiabilidad_porcentaje DECIMAL(5,2) NULL,               -- % de confianza en el pronóstico
    
    -- Demanda real (para análisis posterior)
    cantidad_real DECIMAL(18,4) NULL,
    desviacion AS (cantidad_real - cantidad_pronosticada) PERSISTED,
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_pronos_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_pronos_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_pronos_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_pronos_empresa ON mps_pronostico_demanda(empresa_id, año DESC, mes DESC);
CREATE INDEX IDX_pronos_producto ON mps_pronostico_demanda(producto_id, fecha_inicio);

-- -----------------------------------------------------------------------------
-- Tabla: mps_plan_produccion
-- Descripción: Plan maestro de producción (MPS)
-- Uso: Qué, cuánto y cuándo producir a nivel agregado
-- Relaciones: Entrada principal para MRP
-- -----------------------------------------------------------------------------
CREATE TABLE mps_plan_produccion (
    plan_produccion_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_plan NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    
    -- Periodo
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'borrador',                   -- 'borrador', 'aprobado', 'ejecutado', 'cerrado'
    fecha_aprobacion DATETIME NULL,
    aprobado_por_usuario_id UNIQUEIDENTIFIER NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_planprod_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT UQ_planprod_codigo UNIQUE (cliente_id, empresa_id, codigo_plan)
);

CREATE INDEX IDX_planprod_empresa ON mps_plan_produccion(empresa_id, fecha_inicio DESC);
CREATE INDEX IDX_planprod_estado ON mps_plan_produccion(estado);

-- -----------------------------------------------------------------------------
-- Tabla: mps_plan_produccion_detalle
-- Descripción: Detalle del MPS por producto y periodo
-- Uso: Cantidades específicas a producir por periodo
-- Relaciones: Detalle de plan de producción
-- -----------------------------------------------------------------------------
CREATE TABLE mps_plan_produccion_detalle (
    plan_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    plan_produccion_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Periodo
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    
    -- Cantidades
    pronostico_demanda DECIMAL(18,4) DEFAULT 0,               -- Demanda esperada
    pedidos_firmes DECIMAL(18,4) DEFAULT 0,                   -- Pedidos confirmados
    stock_inicial DECIMAL(18,4) DEFAULT 0,
    stock_seguridad DECIMAL(18,4) DEFAULT 0,
    cantidad_planificada DECIMAL(18,4) NOT NULL,              -- Cantidad a producir
    cantidad_producida DECIMAL(18,4) DEFAULT 0,               -- Real producido
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Capacidad
    capacidad_disponible DECIMAL(18,4) NULL,
    porcentaje_uso_capacidad AS (
        CASE 
            WHEN capacidad_disponible > 0 
            THEN (cantidad_planificada / capacidad_disponible) * 100
            ELSE 0
        END
    ) PERSISTED,
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_planproddet_plan FOREIGN KEY (plan_produccion_id) 
        REFERENCES mps_plan_produccion(plan_produccion_id) ON DELETE CASCADE,
    CONSTRAINT FK_planproddet_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_planproddet_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_planproddet_plan ON mps_plan_produccion_detalle(plan_produccion_id, fecha_inicio);
CREATE INDEX IDX_planproddet_producto ON mps_plan_produccion_detalle(producto_id, fecha_inicio);

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
    moneda NVARCHAR(3) DEFAULT 'PEN',
    
    -- Estado
    estado_activo NVARCHAR(20) DEFAULT 'operativo',           -- 'operativo', 'mantenimiento', 'averiado', 'baja'
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_activo_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_activo_sucursal FOREIGN KEY (sucursal_id) 
        REFERENCES org_sucursal(sucursal_id) ON DELETE SET NULL,
    CONSTRAINT FK_activo_ct FOREIGN KEY (centro_trabajo_id) 
        REFERENCES mfg_centro_trabajo(centro_trabajo_id) ON DELETE SET NULL,
    CONSTRAINT FK_activo_vehiculo FOREIGN KEY (vehiculo_id) 
        REFERENCES log_vehiculo(vehiculo_id) ON DELETE SET NULL,
    CONSTRAINT FK_activo_prov FOREIGN KEY (proveedor_id) 
        REFERENCES pur_proveedor(proveedor_id) ON DELETE SET NULL,
    CONSTRAINT UQ_activo_codigo UNIQUE (cliente_id, empresa_id, codigo_activo)
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
    moneda NVARCHAR(3) DEFAULT 'PEN',
    
    -- Estado
    es_activo BIT DEFAULT 1 NOT NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_planmnt_activo FOREIGN KEY (activo_id) 
        REFERENCES mnt_activo(activo_id) ON DELETE CASCADE,
    CONSTRAINT UQ_planmnt_codigo UNIQUE (cliente_id, codigo_plan)
);

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
    moneda NVARCHAR(3) DEFAULT 'PEN',
    
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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_ot_activo FOREIGN KEY (activo_id) 
        REFERENCES mnt_activo(activo_id) ON DELETE NO ACTION,
    CONSTRAINT FK_ot_plan FOREIGN KEY (plan_mantenimiento_id) 
        REFERENCES mnt_plan_mantenimiento(plan_mantenimiento_id) ON DELETE SET NULL,
    CONSTRAINT UQ_ot_numero UNIQUE (cliente_id, empresa_id, numero_ot)
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
    activo_id UNIQUEIDENTIFIER NOT NULL,
    orden_trabajo_id UNIQUEIDENTIFIER NULL,
    
    fecha_mantenimiento DATE NOT NULL,
    tipo_mantenimiento NVARCHAR(20) NOT NULL,
    
    descripcion_trabajo NVARCHAR(MAX) NULL,
    tecnico_nombre NVARCHAR(150) NULL,
    
    horas_uso_activo DECIMAL(12,2) NULL,                      -- Lectura del horómetro/odómetro
    kilometraje DECIMAL(12,2) NULL,
    
    costo_total DECIMAL(18,2) DEFAULT 0,
    moneda NVARCHAR(3) DEFAULT 'PEN',
    
    observaciones NVARCHAR(500) NULL,
    
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_histmnt_activo FOREIGN KEY (activo_id) 
        REFERENCES mnt_activo(activo_id) ON DELETE CASCADE,
    CONSTRAINT FK_histmnt_ot FOREIGN KEY (orden_trabajo_id) 
        REFERENCES mnt_orden_trabajo(orden_trabajo_id) ON DELETE SET NULL
);

CREATE INDEX IDX_histmnt_activo ON mnt_historial_mantenimiento(activo_id, fecha_mantenimiento DESC);
CREATE INDEX IDX_histmnt_fecha ON mnt_historial_mantenimiento(fecha_mantenimiento DESC);

PRINT 'SECCIÓN 6-10 completada: LOG, MFG, MRP, MPS, MNT';
GO

-- ============================================================================
-- SCRIPT: MÓDULOS ERP COMPLETO - PARTE 3
-- DESCRIPCIÓN: Módulos Comerciales (SLS, CRM, PRC, INV_BILL, POS)
-- DEPENDENCIAS: Ejecutar después de PARTE 1 y PARTE 2
-- ============================================================================

-- ============================================================================
-- SECCIÓN 11: SLS - VENTAS
-- ============================================================================
-- DESCRIPCIÓN: Gestión de ventas, pedidos, cotizaciones a clientes
-- DEPENDENCIAS: ORG, INV (productos, stock)
-- USADO POR: INV (salidas), FIN (cuentas por cobrar), LOG (despachos)
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: sls_cliente
-- Descripción: Catálogo de clientes
-- Uso: Maestro de clientes que compran productos/servicios
-- Relaciones: Usado en cotizaciones, pedidos, facturas
-- -----------------------------------------------------------------------------
CREATE TABLE sls_cliente (
    cliente_venta_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,                     -- Tenant
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Identificación
    codigo_cliente NVARCHAR(20) NOT NULL,
    tipo_cliente NVARCHAR(20) DEFAULT 'empresa',              -- 'empresa', 'persona'
    razon_social NVARCHAR(200) NOT NULL,
    nombre_comercial NVARCHAR(150) NULL,
    
    -- Documento tributario
    tipo_documento NVARCHAR(10) DEFAULT 'RUC',                -- 'RUC', 'DNI', 'CE', 'PASAPORTE'
    numero_documento NVARCHAR(20) NOT NULL,
    
    -- Clasificación
    categoria_cliente NVARCHAR(50) NULL,                      -- 'mayorista', 'minorista', 'corporativo', 'gobierno'
    segmento NVARCHAR(50) NULL,                               -- 'A', 'B', 'C' o personalizado
    canal_venta NVARCHAR(30) NULL,                            -- 'directo', 'distribuidor', 'online', 'retail'
    
    -- Dirección fiscal
    direccion NVARCHAR(255) NULL,
    pais NVARCHAR(50) DEFAULT 'Perú',
    departamento NVARCHAR(50) NULL,
    provincia NVARCHAR(50) NULL,
    distrito NVARCHAR(50) NULL,
    ubigeo NVARCHAR(6) NULL,
    
    -- Contacto principal
    contacto_nombre NVARCHAR(150) NULL,
    contacto_cargo NVARCHAR(100) NULL,
    telefono_principal NVARCHAR(20) NULL,
    telefono_secundario NVARCHAR(20) NULL,
    email_principal NVARCHAR(100) NULL,
    email_facturacion NVARCHAR(100) NULL,
    sitio_web NVARCHAR(255) NULL,
    
    -- Condiciones comerciales
    condicion_pago_defecto NVARCHAR(50) DEFAULT 'contado',    -- 'contado', '15_dias', '30_dias', '60_dias'
    dias_credito_defecto INT DEFAULT 0,
    moneda_preferida NVARCHAR(3) DEFAULT 'PEN',
    lista_precio_id UNIQUEIDENTIFIER NULL,                    -- FK a prc_lista_precio
    
    -- Límites
    limite_credito DECIMAL(18,2) NULL,
    saldo_pendiente DECIMAL(18,2) DEFAULT 0,
    saldo_vencido DECIMAL(18,2) DEFAULT 0,
    
    -- Vendedor asignado
    vendedor_usuario_id UNIQUEIDENTIFIER NULL,
    vendedor_nombre NVARCHAR(150) NULL,
    
    -- Datos bancarios (para devoluciones)
    banco NVARCHAR(100) NULL,
    numero_cuenta NVARCHAR(30) NULL,
    
    -- Calificación
    calificacion DECIMAL(3,2) NULL,                           -- 0.00 a 5.00
    nivel_riesgo NVARCHAR(20) DEFAULT 'bajo',                 -- 'bajo', 'medio', 'alto'
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'activo',                     -- 'prospecto', 'activo', 'inactivo', 'bloqueado'
    motivo_bloqueo NVARCHAR(255) NULL,
    es_activo BIT DEFAULT 1 NOT NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    fecha_primera_compra DATE NULL,
    fecha_ultima_compra DATE NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_cltvta_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT UQ_cltvta_codigo UNIQUE (cliente_id, empresa_id, codigo_cliente),
    CONSTRAINT UQ_cltvta_documento UNIQUE (cliente_id, empresa_id, tipo_documento, numero_documento)
);

CREATE INDEX IDX_cltvta_empresa ON sls_cliente(empresa_id, es_activo);
CREATE INDEX IDX_cltvta_documento ON sls_cliente(numero_documento);
CREATE INDEX IDX_cltvta_razon_social ON sls_cliente(razon_social);
CREATE INDEX IDX_cltvta_vendedor ON sls_cliente(vendedor_usuario_id) WHERE vendedor_usuario_id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Tabla: sls_cliente_contacto
-- Descripción: Contactos del cliente
-- Uso: Múltiples personas de contacto por cliente
-- Relaciones: Detalle de sls_cliente
-- -----------------------------------------------------------------------------
CREATE TABLE sls_cliente_contacto (
    contacto_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    cliente_venta_id UNIQUEIDENTIFIER NOT NULL,
    
    nombre_completo NVARCHAR(150) NOT NULL,
    cargo NVARCHAR(100) NULL,
    area NVARCHAR(100) NULL,
    
    telefono NVARCHAR(20) NULL,
    telefono_movil NVARCHAR(20) NULL,
    email NVARCHAR(100) NULL,
    
    es_contacto_principal BIT DEFAULT 0,
    es_contacto_comercial BIT DEFAULT 0,
    es_contacto_cobranzas BIT DEFAULT 0,
    
    fecha_nacimiento DATE NULL,
    observaciones NVARCHAR(500) NULL,
    
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_cltcon_cliente FOREIGN KEY (cliente_venta_id) 
        REFERENCES sls_cliente(cliente_venta_id) ON DELETE CASCADE
);

CREATE INDEX IDX_cltcon_cliente ON sls_cliente_contacto(cliente_venta_id, es_activo);

-- -----------------------------------------------------------------------------
-- Tabla: sls_cliente_direccion
-- Descripción: Direcciones de entrega del cliente
-- Uso: Múltiples puntos de entrega por cliente
-- Relaciones: Detalle de sls_cliente
-- -----------------------------------------------------------------------------
CREATE TABLE sls_cliente_direccion (
    direccion_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    cliente_venta_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_direccion NVARCHAR(20) NULL,
    nombre_direccion NVARCHAR(100) NOT NULL,                  -- Ej: "Almacén Principal", "Tienda Centro"
    
    direccion NVARCHAR(255) NOT NULL,
    referencia NVARCHAR(255) NULL,
    pais NVARCHAR(50) DEFAULT 'Perú',
    departamento NVARCHAR(50) NULL,
    provincia NVARCHAR(50) NULL,
    distrito NVARCHAR(50) NULL,
    ubigeo NVARCHAR(6) NULL,
    codigo_postal NVARCHAR(10) NULL,
    
    contacto_nombre NVARCHAR(150) NULL,
    contacto_telefono NVARCHAR(20) NULL,
    
    es_direccion_fiscal BIT DEFAULT 0,
    es_direccion_entrega_defecto BIT DEFAULT 0,
    
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_cltdir_cliente FOREIGN KEY (cliente_venta_id) 
        REFERENCES sls_cliente(cliente_venta_id) ON DELETE CASCADE
);

CREATE INDEX IDX_cltdir_cliente ON sls_cliente_direccion(cliente_venta_id, es_activo);

-- -----------------------------------------------------------------------------
-- Tabla: sls_cotizacion
-- Descripción: Cotizaciones/Presupuestos a clientes
-- Uso: Propuesta de venta antes del pedido
-- Relaciones: Puede convertirse en pedido de venta
-- -----------------------------------------------------------------------------
CREATE TABLE sls_cotizacion (
    cotizacion_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_cotizacion NVARCHAR(20) NOT NULL,
    fecha_cotizacion DATE DEFAULT GETDATE() NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    
    -- Cliente
    cliente_venta_id UNIQUEIDENTIFIER NOT NULL,
    cliente_razon_social NVARCHAR(200) NULL,
    cliente_ruc NVARCHAR(20) NULL,
    contacto_nombre NVARCHAR(150) NULL,
    
    -- Vendedor
    vendedor_usuario_id UNIQUEIDENTIFIER NULL,
    vendedor_nombre NVARCHAR(150) NULL,
    
    -- Oportunidad CRM (si existe)
    oportunidad_id UNIQUEIDENTIFIER NULL,                     -- FK a crm_oportunidad
    
    -- Condiciones comerciales
    condicion_pago NVARCHAR(50) NOT NULL,
    dias_credito INT DEFAULT 0,
    tiempo_entrega_dias INT NULL,
    moneda NVARCHAR(3) DEFAULT 'PEN',
    tipo_cambio DECIMAL(10,4) DEFAULT 1,
    
    -- Totales
    subtotal DECIMAL(18,2) DEFAULT 0,
    descuento_global DECIMAL(18,2) DEFAULT 0,
    igv DECIMAL(18,2) DEFAULT 0,
    total DECIMAL(18,2) DEFAULT 0,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'borrador',                   -- 'borrador', 'enviada', 'aceptada', 'rechazada', 'vencida', 'convertida'
    fecha_envio DATETIME NULL,
    fecha_respuesta DATETIME NULL,
    motivo_rechazo NVARCHAR(500) NULL,
    
    -- Conversión
    convertida_pedido BIT DEFAULT 0,
    pedido_venta_id UNIQUEIDENTIFIER NULL,
    fecha_conversion DATETIME NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    terminos_condiciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_cotvta_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_cotvta_cliente FOREIGN KEY (cliente_venta_id) 
        REFERENCES sls_cliente(cliente_venta_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_cotvta_numero UNIQUE (cliente_id, empresa_id, numero_cotizacion)
);

CREATE INDEX IDX_cotvta_empresa ON sls_cotizacion(empresa_id, fecha_cotizacion DESC);
CREATE INDEX IDX_cotvta_cliente ON sls_cotizacion(cliente_venta_id, estado);
CREATE INDEX IDX_cotvta_estado ON sls_cotizacion(estado, fecha_vencimiento);
CREATE INDEX IDX_cotvta_vendedor ON sls_cotizacion(vendedor_usuario_id) WHERE vendedor_usuario_id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Tabla: sls_cotizacion_detalle
-- Descripción: Items cotizados
-- Uso: Productos y precios ofrecidos al cliente
-- Relaciones: Detalle de sls_cotizacion
-- -----------------------------------------------------------------------------
CREATE TABLE sls_cotizacion_detalle (
    cotizacion_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    cotizacion_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    cantidad DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    precio_unitario DECIMAL(18,4) NOT NULL,
    descuento_porcentaje DECIMAL(5,2) DEFAULT 0,
    precio_neto AS (precio_unitario * (1 - descuento_porcentaje / 100)) PERSISTED,
    subtotal AS (cantidad * precio_unitario * (1 - descuento_porcentaje / 100)) PERSISTED,
    igv AS (cantidad * precio_unitario * (1 - descuento_porcentaje / 100) * 0.18) PERSISTED,
    total AS (cantidad * precio_unitario * (1 - descuento_porcentaje / 100) * 1.18) PERSISTED,
    
    tiempo_entrega_dias INT NULL,
    observaciones NVARCHAR(500) NULL,
    
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_cotvtadet_cotizacion FOREIGN KEY (cotizacion_id) 
        REFERENCES sls_cotizacion(cotizacion_id) ON DELETE CASCADE,
    CONSTRAINT FK_cotvtadet_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_cotvtadet_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_cotvtadet_cotizacion ON sls_cotizacion_detalle(cotizacion_id);

-- -----------------------------------------------------------------------------
-- Tabla: sls_pedido
-- Descripción: Pedido/Orden de venta (documento de compromiso)
-- Uso: Formalización de venta, genera obligación de entrega
-- Relaciones: Genera salidas de inventario, facturas
-- -----------------------------------------------------------------------------
CREATE TABLE sls_pedido (
    pedido_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_pedido NVARCHAR(20) NOT NULL,
    fecha_pedido DATE DEFAULT GETDATE() NOT NULL,
    fecha_entrega_prometida DATE NOT NULL,
    
    -- Cliente
    cliente_venta_id UNIQUEIDENTIFIER NOT NULL,
    cliente_razon_social NVARCHAR(200) NULL,
    cliente_ruc NVARCHAR(20) NULL,
    
    -- Dirección de entrega
    direccion_entrega_id UNIQUEIDENTIFIER NULL,
    direccion_entrega_texto NVARCHAR(255) NULL,
    
    -- Referencia
    cotizacion_id UNIQUEIDENTIFIER NULL,
    orden_compra_cliente NVARCHAR(30) NULL,                   -- OC del cliente
    
    -- Vendedor
    vendedor_usuario_id UNIQUEIDENTIFIER NULL,
    vendedor_nombre NVARCHAR(150) NULL,
    
    -- Condiciones comerciales
    condicion_pago NVARCHAR(50) NOT NULL,
    dias_credito INT DEFAULT 0,
    moneda NVARCHAR(3) DEFAULT 'PEN',
    tipo_cambio DECIMAL(10,4) DEFAULT 1,
    
    -- Totales
    subtotal DECIMAL(18,2) DEFAULT 0,
    descuento_global DECIMAL(18,2) DEFAULT 0,
    igv DECIMAL(18,2) DEFAULT 0,
    total DECIMAL(18,2) DEFAULT 0,
    
    -- Control de despacho
    total_items INT DEFAULT 0,
    items_despachados INT DEFAULT 0,
    porcentaje_despacho DECIMAL(5,2) DEFAULT 0,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'borrador',                   -- 'borrador', 'confirmado', 'aprobado', 'parcial', 'completo', 'facturado', 'anulado'
    requiere_aprobacion BIT DEFAULT 0,
    aprobado_por_usuario_id UNIQUEIDENTIFIER NULL,
    fecha_aprobacion DATETIME NULL,
    
    -- Prioridad
    prioridad INT DEFAULT 3,                                   -- 1=Urgente, 2=Alta, 3=Normal, 4=Baja
    
    -- Centro de costo (para análisis)
    centro_costo_id UNIQUEIDENTIFIER NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    instrucciones_despacho NVARCHAR(MAX) NULL,
    motivo_anulacion NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    fecha_anulacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_pedido_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_pedido_cliente FOREIGN KEY (cliente_venta_id) 
        REFERENCES sls_cliente(cliente_venta_id) ON DELETE NO ACTION,
    CONSTRAINT FK_pedido_direccion FOREIGN KEY (direccion_entrega_id) 
        REFERENCES sls_cliente_direccion(direccion_id) ON DELETE SET NULL,
    CONSTRAINT FK_pedido_cotizacion FOREIGN KEY (cotizacion_id) 
        REFERENCES sls_cotizacion(cotizacion_id) ON DELETE SET NULL,
    CONSTRAINT FK_pedido_cc FOREIGN KEY (centro_costo_id) 
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE SET NULL,
    CONSTRAINT UQ_pedido_numero UNIQUE (cliente_id, empresa_id, numero_pedido)
);

CREATE INDEX IDX_pedido_empresa ON sls_pedido(empresa_id, fecha_pedido DESC);
CREATE INDEX IDX_pedido_cliente ON sls_pedido(cliente_venta_id, estado);
CREATE INDEX IDX_pedido_estado ON sls_pedido(estado, fecha_entrega_prometida);
CREATE INDEX IDX_pedido_vendedor ON sls_pedido(vendedor_usuario_id) WHERE vendedor_usuario_id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Tabla: sls_pedido_detalle
-- Descripción: Items del pedido de venta
-- Uso: Productos vendidos con cantidades y precios
-- Relaciones: Detalle de sls_pedido
-- -----------------------------------------------------------------------------
CREATE TABLE sls_pedido_detalle (
    pedido_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    pedido_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Cantidad
    cantidad_pedida DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Precios
    precio_unitario DECIMAL(18,4) NOT NULL,
    descuento_porcentaje DECIMAL(5,2) DEFAULT 0,
    precio_neto AS (precio_unitario * (1 - descuento_porcentaje / 100)) PERSISTED,
    subtotal AS (cantidad_pedida * precio_unitario * (1 - descuento_porcentaje / 100)) PERSISTED,
    igv AS (cantidad_pedida * precio_unitario * (1 - descuento_porcentaje / 100) * 0.18) PERSISTED,
    total AS (cantidad_pedida * precio_unitario * (1 - descuento_porcentaje / 100) * 1.18) PERSISTED,
    
    -- Control de despacho
    cantidad_despachada DECIMAL(18,4) DEFAULT 0,
    cantidad_pendiente AS (cantidad_pedida - cantidad_despachada) PERSISTED,
    cantidad_facturada DECIMAL(18,4) DEFAULT 0,
    
    -- Almacén de origen
    almacen_origen_id UNIQUEIDENTIFIER NULL,
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_pedidodet_pedido FOREIGN KEY (pedido_id) 
        REFERENCES sls_pedido(pedido_id) ON DELETE CASCADE,
    CONSTRAINT FK_pedidodet_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_pedidodet_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT FK_pedidodet_almacen FOREIGN KEY (almacen_origen_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE SET NULL
);

CREATE INDEX IDX_pedidodet_pedido ON sls_pedido_detalle(pedido_id);
CREATE INDEX IDX_pedidodet_producto ON sls_pedido_detalle(producto_id);
CREATE INDEX IDX_pedidodet_pendiente ON sls_pedido_detalle(pedido_id) 
    WHERE cantidad_pendiente > 0;

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
    moneda NVARCHAR(3) DEFAULT 'PEN',
    
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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT UQ_campana_codigo UNIQUE (cliente_id, empresa_id, codigo_campana)
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
    pais NVARCHAR(50) DEFAULT 'Perú',
    
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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_lead_campana FOREIGN KEY (campana_id) 
        REFERENCES crm_campana(campana_id) ON DELETE SET NULL,
    CONSTRAINT FK_lead_cliente FOREIGN KEY (cliente_venta_id) 
        REFERENCES sls_cliente(cliente_venta_id) ON DELETE SET NULL
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
    moneda NVARCHAR(3) DEFAULT 'PEN',
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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_opor_cliente FOREIGN KEY (cliente_venta_id) 
        REFERENCES sls_cliente(cliente_venta_id) ON DELETE SET NULL,
    CONSTRAINT FK_opor_lead FOREIGN KEY (lead_id) 
        REFERENCES crm_lead(lead_id) ON DELETE SET NULL,
    CONSTRAINT FK_opor_campana FOREIGN KEY (campana_id) 
        REFERENCES crm_campana(campana_id) ON DELETE SET NULL,
    CONSTRAINT UQ_opor_numero UNIQUE (cliente_id, empresa_id, numero_oportunidad)
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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_activ_lead FOREIGN KEY (lead_id) 
        REFERENCES crm_lead(lead_id) ON DELETE CASCADE,
    CONSTRAINT FK_activ_opor FOREIGN KEY (oportunidad_id) 
        REFERENCES crm_oportunidad(oportunidad_id) ON DELETE CASCADE,
    CONSTRAINT FK_activ_cliente FOREIGN KEY (cliente_venta_id) 
        REFERENCES sls_cliente(cliente_venta_id) ON DELETE CASCADE
);

CREATE INDEX IDX_activ_empresa ON crm_actividad(empresa_id, fecha_actividad DESC);
CREATE INDEX IDX_activ_responsable ON crm_actividad(usuario_responsable_id, estado, fecha_actividad);
CREATE INDEX IDX_activ_lead ON crm_actividad(lead_id) WHERE lead_id IS NOT NULL;
CREATE INDEX IDX_activ_opor ON crm_actividad(oportunidad_id) WHERE oportunidad_id IS NOT NULL;

PRINT 'SECCIÓN 11-12 creada: SLS, CRM';
GO

-- ============================================================================
-- SCRIPT: MÓDULOS ERP COMPLETO - PARTE 4
-- DESCRIPCIÓN: Pricing, Facturación y POS (PRC, INV_BILL, POS)
-- DEPENDENCIAS: Ejecutar después de PARTE 1, 2 y 3
-- ============================================================================

-- ============================================================================
-- SECCIÓN 13: PRC - GESTIÓN DE PRECIOS Y TARIFAS
-- ============================================================================
-- DESCRIPCIÓN: Gestión de listas de precios, descuentos, promociones
-- DEPENDENCIAS: ORG, INV (productos)
-- USADO POR: SLS (cotizaciones, pedidos), POS
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: prc_lista_precio
-- Descripción: Listas de precios (tarifarios)
-- Uso: Diferentes estructuras de precios por segmento/canal
-- Relaciones: Asignada a clientes, usada en ventas
-- -----------------------------------------------------------------------------
CREATE TABLE prc_lista_precio (
    lista_precio_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_lista NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(255) NULL,
    
    -- Aplicabilidad
    tipo_lista NVARCHAR(30) DEFAULT 'general',                -- 'general', 'mayorista', 'minorista', 'distribuidor', 'corporativo'
    moneda NVARCHAR(3) DEFAULT 'PEN',
    
    -- Vigencia
    fecha_vigencia_desde DATE NOT NULL,
    fecha_vigencia_hasta DATE NULL,
    
    -- Configuración de precios
    incluye_igv BIT DEFAULT 1,                                -- Si precios incluyen IGV
    permite_descuentos BIT DEFAULT 1,
    descuento_maximo_porcentaje DECIMAL(5,2) DEFAULT 10,
    
    -- Estado
    es_lista_defecto BIT DEFAULT 0,
    es_activo BIT DEFAULT 1 NOT NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_listaprc_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT UQ_listaprc_codigo UNIQUE (cliente_id, empresa_id, codigo_lista)
);

CREATE INDEX IDX_listaprc_empresa ON prc_lista_precio(empresa_id, es_activo);
CREATE INDEX IDX_listaprc_vigencia ON prc_lista_precio(fecha_vigencia_desde, fecha_vigencia_hasta);

-- -----------------------------------------------------------------------------
-- Tabla: prc_lista_precio_detalle
-- Descripción: Precios por producto en cada lista
-- Uso: Precio específico de cada producto en la lista
-- Relaciones: Detalle de prc_lista_precio
-- -----------------------------------------------------------------------------
CREATE TABLE prc_lista_precio_detalle (
    lista_precio_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    lista_precio_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Precio
    precio_unitario DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Precio escalonado (por cantidad)
    cantidad_minima DECIMAL(18,4) DEFAULT 1,
    cantidad_maxima DECIMAL(18,4) NULL,
    
    -- Descuento máximo permitido para este producto
    descuento_maximo_porcentaje DECIMAL(5,2) NULL,
    
    -- Vigencia específica del producto (puede diferir de la lista)
    fecha_vigencia_desde DATE NULL,
    fecha_vigencia_hasta DATE NULL,
    
    -- Estado
    es_activo BIT DEFAULT 1 NOT NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    
    CONSTRAINT FK_listadet_lista FOREIGN KEY (lista_precio_id) 
        REFERENCES prc_lista_precio(lista_precio_id) ON DELETE CASCADE,
    CONSTRAINT FK_listadet_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE CASCADE,
    CONSTRAINT FK_listadet_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_listadet_lista ON prc_lista_precio_detalle(lista_precio_id, es_activo);
CREATE INDEX IDX_listadet_producto ON prc_lista_precio_detalle(producto_id, lista_precio_id);

-- -----------------------------------------------------------------------------
-- Tabla: prc_promocion
-- Descripción: Promociones y ofertas especiales
-- Uso: Descuentos temporales por campaña
-- Relaciones: Aplicable a productos, categorías o toda la venta
-- -----------------------------------------------------------------------------
CREATE TABLE prc_promocion (
    promocion_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_promocion NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(500) NULL,
    
    -- Tipo de promoción
    tipo_promocion NVARCHAR(30) NOT NULL,                     -- 'descuento_porcentaje', 'descuento_monto', '2x1', '3x2', 'producto_gratis'
    
    -- Aplicabilidad
    aplica_a NVARCHAR(20) NOT NULL,                           -- 'producto', 'categoria', 'marca', 'toda_venta'
    producto_id UNIQUEIDENTIFIER NULL,
    categoria_id UNIQUEIDENTIFIER NULL,
    marca NVARCHAR(100) NULL,
    
    -- Descuento
    descuento_porcentaje DECIMAL(5,2) NULL,
    descuento_monto DECIMAL(18,2) NULL,
    
    -- Reglas (JSON para configuraciones complejas)
    reglas_aplicacion NVARCHAR(MAX) NULL,                     -- Ej: {"cantidad_minima": 3, "producto_gratis_id": "xxx"}
    
    -- Vigencia
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    
    -- Límites
    cantidad_maxima_usos INT NULL,                            -- Máximo de veces que se puede usar
    cantidad_usos_actuales INT DEFAULT 0,
    monto_maximo_descuento DECIMAL(18,2) NULL,
    
    -- Combinable con otras promociones
    es_combinable BIT DEFAULT 0,
    
    -- Canales
    aplica_canal_venta NVARCHAR(MAX) NULL,                    -- JSON: ["tienda", "online", "telefono"]
    
    -- Estado
    es_activo BIT DEFAULT 1 NOT NULL,
    requiere_codigo_cupon BIT DEFAULT 0,
    codigo_cupon NVARCHAR(30) NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_promo_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_promo_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE CASCADE,
    CONSTRAINT FK_promo_categoria FOREIGN KEY (categoria_id) 
        REFERENCES inv_categoria_producto(categoria_id) ON DELETE CASCADE,
    CONSTRAINT UQ_promo_codigo UNIQUE (cliente_id, empresa_id, codigo_promocion)
);

CREATE INDEX IDX_promo_empresa ON prc_promocion(empresa_id, es_activo);
CREATE INDEX IDX_promo_vigencia ON prc_promocion(fecha_inicio, fecha_fin, es_activo);
CREATE INDEX IDX_promo_producto ON prc_promocion(producto_id) WHERE producto_id IS NOT NULL;

-- ============================================================================
-- SECCIÓN 14: INV_BILL - FACTURACIÓN ELECTRÓNICA
-- ============================================================================
-- DESCRIPCIÓN: Emisión de comprobantes electrónicos (facturas, boletas, NC, ND)
-- DEPENDENCIAS: ORG, SLS (pedidos), INV
-- USADO POR: FIN (cuentas por cobrar), obligaciones tributarias
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: invbill_serie_comprobante
-- Descripción: Series de comprobantes electrónicos
-- Uso: Control de numeración de facturas, boletas, NC, ND
-- Relaciones: Asignada por sucursal/punto de venta
-- -----------------------------------------------------------------------------
CREATE TABLE invbill_serie_comprobante (
    serie_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    tipo_comprobante NVARCHAR(2) NOT NULL,                    -- '01'=Factura, '03'=Boleta, '07'=NC, '08'=ND
    serie NVARCHAR(4) NOT NULL,                               -- 'F001', 'B001', etc
    
    -- Numeración
    numero_actual INT DEFAULT 0,
    numero_inicial INT DEFAULT 1,
    numero_final INT NULL,                                    -- Límite autorizado (si aplica)
    
    -- Asociación
    sucursal_id UNIQUEIDENTIFIER NULL,
    punto_venta_id UNIQUEIDENTIFIER NULL,                     -- FK a pos_punto_venta
    
    -- Configuración
    es_electronica BIT DEFAULT 1,
    requiere_autorizacion_sunat BIT DEFAULT 1,
    
    -- Estado
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_activacion DATE NULL,
    fecha_baja DATE NULL,
    motivo_baja NVARCHAR(255) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_serie_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_serie_sucursal FOREIGN KEY (sucursal_id) 
        REFERENCES org_sucursal(sucursal_id) ON DELETE SET NULL,
    CONSTRAINT UQ_serie UNIQUE (cliente_id, empresa_id, tipo_comprobante, serie)
);

CREATE INDEX IDX_serie_empresa ON invbill_serie_comprobante(empresa_id, es_activo);
CREATE INDEX IDX_serie_tipo ON invbill_serie_comprobante(tipo_comprobante, serie);

-- -----------------------------------------------------------------------------
-- Tabla: invbill_comprobante
-- Descripción: Comprobantes de pago (facturas, boletas)
-- Uso: Documento fiscal de venta
-- Relaciones: Vinculado a pedidos de venta, genera cuentas por cobrar
-- -----------------------------------------------------------------------------
CREATE TABLE invbill_comprobante (
    comprobante_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Identificación
    tipo_comprobante NVARCHAR(2) NOT NULL,                    -- '01', '03', '07', '08'
    serie NVARCHAR(4) NOT NULL,
    numero NVARCHAR(10) NOT NULL,
    numero_completo AS (serie + '-' + numero) PERSISTED,
    
    fecha_emision DATE DEFAULT GETDATE() NOT NULL,
    fecha_vencimiento DATE NULL,                              -- Para crédito
    hora_emision TIME DEFAULT CONVERT(TIME, GETDATE()),
    
    -- Cliente
    cliente_venta_id UNIQUEIDENTIFIER NULL,
    cliente_tipo_documento NVARCHAR(2) NOT NULL,              -- '6'=RUC, '1'=DNI, etc
    cliente_numero_documento NVARCHAR(20) NOT NULL,
    cliente_razon_social NVARCHAR(200) NOT NULL,
    cliente_direccion NVARCHAR(255) NULL,
    
    -- Referencia
    pedido_id UNIQUEIDENTIFIER NULL,
    venta_id UNIQUEIDENTIFIER NULL,                           -- FK a pos_venta (si es de POS)
    
    -- Guía de remisión relacionada
    guia_remision_id UNIQUEIDENTIFIER NULL,
    
    -- Documento relacionado (para NC, ND)
    comprobante_referencia_id UNIQUEIDENTIFIER NULL,
    tipo_nota NVARCHAR(2) NULL,                               -- Tipo de NC o ND (códigos SUNAT)
    motivo_nota NVARCHAR(500) NULL,
    
    -- Montos
    moneda NVARCHAR(3) DEFAULT 'PEN',
    tipo_cambio DECIMAL(10,4) DEFAULT 1,
    
    subtotal_gravado DECIMAL(18,2) DEFAULT 0,
    subtotal_exonerado DECIMAL(18,2) DEFAULT 0,
    subtotal_inafecto DECIMAL(18,2) DEFAULT 0,
    subtotal_gratuito DECIMAL(18,2) DEFAULT 0,
    descuento_global DECIMAL(18,2) DEFAULT 0,
    igv DECIMAL(18,2) DEFAULT 0,
    total DECIMAL(18,2) DEFAULT 0,
    
    -- Detracción (si aplica)
    aplica_detraccion BIT DEFAULT 0,
    porcentaje_detraccion DECIMAL(5,2) NULL,
    monto_detraccion DECIMAL(18,2) NULL,
    
    -- Retención/Percepción
    aplica_retencion BIT DEFAULT 0,
    monto_retencion DECIMAL(18,2) NULL,
    aplica_percepcion BIT DEFAULT 0,
    monto_percepcion DECIMAL(18,2) NULL,
    
    -- Condición de pago
    condicion_pago NVARCHAR(50) NULL,
    forma_pago NVARCHAR(30) DEFAULT 'contado',                -- 'contado', 'credito'
    
    -- Firma digital SUNAT
    codigo_hash NVARCHAR(100) NULL,
    firma_digital NVARCHAR(MAX) NULL,
    codigo_qr NVARCHAR(MAX) NULL,
    
    -- Estado SUNAT
    estado_sunat NVARCHAR(20) DEFAULT 'pendiente',            -- 'pendiente', 'aceptado', 'rechazado', 'baja'
    codigo_respuesta_sunat NVARCHAR(10) NULL,
    mensaje_respuesta_sunat NVARCHAR(500) NULL,
    fecha_envio_sunat DATETIME NULL,
    fecha_respuesta_sunat DATETIME NULL,
    
    -- CDR (Constancia de Recepción)
    cdr_xml NVARCHAR(MAX) NULL,
    cdr_fecha DATETIME NULL,
    
    -- Archivos
    xml_comprobante NVARCHAR(MAX) NULL,
    pdf_url NVARCHAR(500) NULL,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'emitido',                    -- 'borrador', 'emitido', 'anulado', 'dado_baja'
    fecha_anulacion DATETIME NULL,
    motivo_anulacion NVARCHAR(500) NULL,
    
    -- Observaciones
    observaciones NVARCHAR(MAX) NULL,
    
    -- Vendedor
    vendedor_usuario_id UNIQUEIDENTIFIER NULL,
    vendedor_nombre NVARCHAR(150) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_comp_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_comp_cliente FOREIGN KEY (cliente_venta_id) 
        REFERENCES sls_cliente(cliente_venta_id) ON DELETE SET NULL,
    CONSTRAINT FK_comp_pedido FOREIGN KEY (pedido_id) 
        REFERENCES sls_pedido(pedido_id) ON DELETE SET NULL,
    CONSTRAINT FK_comp_guia FOREIGN KEY (guia_remision_id) 
        REFERENCES log_guia_remision(guia_remision_id) ON DELETE SET NULL,
    CONSTRAINT FK_comp_referencia FOREIGN KEY (comprobante_referencia_id) 
        REFERENCES invbill_comprobante(comprobante_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_comp_numero UNIQUE (cliente_id, empresa_id, tipo_comprobante, serie, numero)
);

CREATE INDEX IDX_comp_empresa ON invbill_comprobante(empresa_id, fecha_emision DESC);
CREATE INDEX IDX_comp_cliente ON invbill_comprobante(cliente_venta_id, estado);
CREATE INDEX IDX_comp_numero ON invbill_comprobante(numero_completo);
CREATE INDEX IDX_comp_estado_sunat ON invbill_comprobante(estado_sunat);
CREATE INDEX IDX_comp_fecha ON invbill_comprobante(fecha_emision DESC);

-- -----------------------------------------------------------------------------
-- Tabla: invbill_comprobante_detalle
-- Descripción: Items del comprobante
-- Uso: Productos facturados con precios y tributos
-- Relaciones: Detalle de invbill_comprobante
-- -----------------------------------------------------------------------------
CREATE TABLE invbill_comprobante_detalle (
    comprobante_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
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
    
    -- Lote (si aplica)
    lote NVARCHAR(50) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_compdet_comp FOREIGN KEY (comprobante_id) 
        REFERENCES invbill_comprobante(comprobante_id) ON DELETE CASCADE,
    CONSTRAINT FK_compdet_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE SET NULL,
    CONSTRAINT FK_compdet_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE SET NULL
);

CREATE INDEX IDX_compdet_comprobante ON invbill_comprobante_detalle(comprobante_id, item);
CREATE INDEX IDX_compdet_producto ON invbill_comprobante_detalle(producto_id) WHERE producto_id IS NOT NULL;

-- ============================================================================
-- SECCIÓN 15: POS - PUNTO DE VENTA
-- ============================================================================
-- DESCRIPCIÓN: Sistema de punto de venta (tiendas, retail)
-- DEPENDENCIAS: ORG, INV, SLS, PRC, INV_BILL
-- USADO POR: Ventas al mostrador, retail
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: pos_punto_venta
-- Descripción: Puntos de venta físicos (cajas registradoras)
-- Uso: Configuración de terminales POS
-- Relaciones: Ubicados en sucursales
-- -----------------------------------------------------------------------------
CREATE TABLE pos_punto_venta (
    punto_venta_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_punto_venta NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    
    -- Ubicación
    sucursal_id UNIQUEIDENTIFIER NOT NULL,
    ubicacion_fisica NVARCHAR(100) NULL,                      -- Ej: "Caja 1", "Caja Express"
    
    -- Configuración
    tipo_punto_venta NVARCHAR(30) DEFAULT 'caja',             -- 'caja', 'autoservicio', 'movil'
    
    -- Series de comprobantes asignadas
    serie_factura_id UNIQUEIDENTIFIER NULL,
    serie_boleta_id UNIQUEIDENTIFIER NULL,
    serie_nota_credito_id UNIQUEIDENTIFIER NULL,
    
    -- Almacén asociado
    almacen_id UNIQUEIDENTIFIER NULL,
    
    -- Lista de precios por defecto
    lista_precio_id UNIQUEIDENTIFIER NULL,
    
    -- Configuración de pagos
    acepta_efectivo BIT DEFAULT 1,
    acepta_tarjeta BIT DEFAULT 1,
    acepta_transferencia BIT DEFAULT 1,
    acepta_yape_plin BIT DEFAULT 0,
    
    -- Terminal física
    codigo_terminal NVARCHAR(50) NULL,
    ip_terminal NVARCHAR(45) NULL,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'cerrado',                    -- 'abierto', 'cerrado', 'bloqueado'
    es_activo BIT DEFAULT 1 NOT NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_pv_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_pv_sucursal FOREIGN KEY (sucursal_id) 
        REFERENCES org_sucursal(sucursal_id) ON DELETE CASCADE,
    CONSTRAINT FK_pv_almacen FOREIGN KEY (almacen_id) 
        REFERENCES inv_almacen(almacen_id) ON DELETE SET NULL,
    CONSTRAINT FK_pv_listaprecio FOREIGN KEY (lista_precio_id) 
        REFERENCES prc_lista_precio(lista_precio_id) ON DELETE SET NULL,
    CONSTRAINT UQ_pv_codigo UNIQUE (cliente_id, empresa_id, codigo_punto_venta)
);

CREATE INDEX IDX_pv_empresa ON pos_punto_venta(empresa_id, es_activo);
CREATE INDEX IDX_pv_sucursal ON pos_punto_venta(sucursal_id, estado);

-- -----------------------------------------------------------------------------
-- Tabla: pos_turno_caja
-- Descripción: Turnos de apertura y cierre de caja
-- Uso: Control de efectivo y transacciones por turno
-- Relaciones: Asociado a punto de venta y cajero
-- -----------------------------------------------------------------------------
CREATE TABLE pos_turno_caja (
    turno_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    punto_venta_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_turno NVARCHAR(20) NOT NULL,
    
    -- Cajero
    cajero_usuario_id UNIQUEIDENTIFIER NOT NULL,
    cajero_nombre NVARCHAR(150) NULL,
    
    -- Apertura
    fecha_apertura DATETIME DEFAULT GETDATE() NOT NULL,
    monto_apertura DECIMAL(18,2) NOT NULL,                    -- Efectivo inicial
    
    -- Cierre
    fecha_cierre DATETIME NULL,
    monto_cierre_esperado DECIMAL(18,2) NULL,                 -- Según ventas
    monto_cierre_real DECIMAL(18,2) NULL,                     -- Efectivo contado
    diferencia AS (monto_cierre_real - monto_cierre_esperado) PERSISTED,
    
    -- Totales del turno
    total_ventas INT DEFAULT 0,
    total_ventas_efectivo DECIMAL(18,2) DEFAULT 0,
    total_ventas_tarjeta DECIMAL(18,2) DEFAULT 0,
    total_ventas_transferencia DECIMAL(18,2) DEFAULT 0,
    total_ventas_otros DECIMAL(18,2) DEFAULT 0,
    total_ingresos AS (total_ventas_efectivo + total_ventas_tarjeta + total_ventas_transferencia + total_ventas_otros) PERSISTED,
    
    total_egresos DECIMAL(18,2) DEFAULT 0,                    -- Gastos, retiros
    
    -- Comprobantes emitidos
    total_facturas INT DEFAULT 0,
    total_boletas INT DEFAULT 0,
    total_notas_credito INT DEFAULT 0,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'abierto',                    -- 'abierto', 'cerrado'
    
    -- Observaciones
    observaciones_apertura NVARCHAR(500) NULL,
    observaciones_cierre NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    cerrado_por_usuario_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_turno_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_turno_pv FOREIGN KEY (punto_venta_id) 
        REFERENCES pos_punto_venta(punto_venta_id) ON DELETE CASCADE,
    CONSTRAINT UQ_turno_numero UNIQUE (cliente_id, empresa_id, punto_venta_id, numero_turno)
);

CREATE INDEX IDX_turno_empresa ON pos_turno_caja(empresa_id, fecha_apertura DESC);
CREATE INDEX IDX_turno_pv ON pos_turno_caja(punto_venta_id, estado);
CREATE INDEX IDX_turno_cajero ON pos_turno_caja(cajero_usuario_id, estado);

-- -----------------------------------------------------------------------------
-- Tabla: pos_venta
-- Descripción: Ventas realizadas en POS
-- Uso: Transacción de venta al mostrador
-- Relaciones: Genera comprobante, actualiza inventario
-- -----------------------------------------------------------------------------
CREATE TABLE pos_venta (
    venta_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_venta NVARCHAR(20) NOT NULL,
    fecha_venta DATETIME DEFAULT GETDATE() NOT NULL,
    
    -- Punto de venta y turno
    punto_venta_id UNIQUEIDENTIFIER NOT NULL,
    turno_caja_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Cajero/Vendedor
    vendedor_usuario_id UNIQUEIDENTIFIER NOT NULL,
    vendedor_nombre NVARCHAR(150) NULL,
    
    -- Cliente (opcional en retail)
    cliente_venta_id UNIQUEIDENTIFIER NULL,
    cliente_nombre NVARCHAR(200) NULL,
    cliente_documento_tipo NVARCHAR(10) NULL,
    cliente_documento_numero NVARCHAR(20) NULL,
    
    -- Totales
    moneda NVARCHAR(3) DEFAULT 'PEN',
    subtotal DECIMAL(18,2) DEFAULT 0,
    descuento_global DECIMAL(18,2) DEFAULT 0,
    igv DECIMAL(18,2) DEFAULT 0,
    total DECIMAL(18,2) DEFAULT 0,
    
    -- Redondeo (común en efectivo)
    redondeo DECIMAL(18,2) DEFAULT 0,
    total_cobrar AS (total + redondeo) PERSISTED,
    
    -- Forma de pago
    forma_pago NVARCHAR(30) NOT NULL,                         -- 'efectivo', 'tarjeta', 'transferencia', 'mixto'
    
    -- Montos por forma de pago
    monto_efectivo DECIMAL(18,2) DEFAULT 0,
    monto_tarjeta DECIMAL(18,2) DEFAULT 0,
    monto_transferencia DECIMAL(18,2) DEFAULT 0,
    monto_otros DECIMAL(18,2) DEFAULT 0,
    
    -- Cambio (si es efectivo)
    monto_recibido DECIMAL(18,2) NULL,
    monto_cambio AS (
        CASE 
            WHEN forma_pago = 'efectivo' AND monto_recibido > total_cobrar
            THEN monto_recibido - total_cobrar
            ELSE 0
        END
    ) PERSISTED,
    
    -- Comprobante generado
    comprobante_id UNIQUEIDENTIFIER NULL,
    tipo_comprobante NVARCHAR(2) NULL,
    numero_comprobante NVARCHAR(20) NULL,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'completada',                 -- 'borrador', 'completada', 'anulada'
    fecha_anulacion DATETIME NULL,
    motivo_anulacion NVARCHAR(500) NULL,
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_posvta_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_posvta_pv FOREIGN KEY (punto_venta_id) 
        REFERENCES pos_punto_venta(punto_venta_id) ON DELETE NO ACTION,
    CONSTRAINT FK_posvta_turno FOREIGN KEY (turno_caja_id) 
        REFERENCES pos_turno_caja(turno_id) ON DELETE NO ACTION,
    CONSTRAINT FK_posvta_cliente FOREIGN KEY (cliente_venta_id) 
        REFERENCES sls_cliente(cliente_venta_id) ON DELETE SET NULL,
    CONSTRAINT FK_posvta_comp FOREIGN KEY (comprobante_id) 
        REFERENCES invbill_comprobante(comprobante_id) ON DELETE SET NULL,
    CONSTRAINT UQ_posvta_numero UNIQUE (cliente_id, empresa_id, punto_venta_id, numero_venta)
);

CREATE INDEX IDX_posvta_empresa ON pos_venta(empresa_id, fecha_venta DESC);
CREATE INDEX IDX_posvta_pv ON pos_venta(punto_venta_id, estado, fecha_venta DESC);
CREATE INDEX IDX_posvta_turno ON pos_venta(turno_caja_id);
CREATE INDEX IDX_posvta_comprobante ON pos_venta(comprobante_id) WHERE comprobante_id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Tabla: pos_venta_detalle
-- Descripción: Items de la venta POS
-- Uso: Productos vendidos en el mostrador
-- Relaciones: Detalle de pos_venta
-- -----------------------------------------------------------------------------
CREATE TABLE pos_venta_detalle (
    venta_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    venta_id UNIQUEIDENTIFIER NOT NULL,
    
    item INT NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    descripcion NVARCHAR(200) NULL,
    
    cantidad DECIMAL(18,4) NOT NULL,
    unidad_medida_id UNIQUEIDENTIFIER NOT NULL,
    
    precio_unitario DECIMAL(18,4) NOT NULL,
    descuento_porcentaje DECIMAL(5,2) DEFAULT 0,
    descuento_monto AS (precio_unitario * cantidad * descuento_porcentaje / 100) PERSISTED,
    precio_neto AS (precio_unitario * (1 - descuento_porcentaje / 100)) PERSISTED,
    
    subtotal AS (cantidad * precio_unitario * (1 - descuento_porcentaje / 100)) PERSISTED,
    igv AS (cantidad * precio_unitario * (1 - descuento_porcentaje / 100) * 0.18) PERSISTED,
    total AS (cantidad * precio_unitario * (1 - descuento_porcentaje / 100) * 1.18) PERSISTED,
    
    -- Promoción aplicada
    promocion_id UNIQUEIDENTIFIER NULL,
    
    -- Lote (si aplica)
    lote NVARCHAR(50) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_posvtadet_venta FOREIGN KEY (venta_id) 
        REFERENCES pos_venta(venta_id) ON DELETE CASCADE,
    CONSTRAINT FK_posvtadet_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE NO ACTION,
    CONSTRAINT FK_posvtadet_um FOREIGN KEY (unidad_medida_id) 
        REFERENCES inv_unidad_medida(unidad_medida_id) ON DELETE NO ACTION,
    CONSTRAINT FK_posvtadet_promo FOREIGN KEY (promocion_id) 
        REFERENCES prc_promocion(promocion_id) ON DELETE SET NULL
);

CREATE INDEX IDX_posvtadet_venta ON pos_venta_detalle(venta_id, item);
CREATE INDEX IDX_posvtadet_producto ON pos_venta_detalle(producto_id);

PRINT 'SECCIÓN 13-15 creada: PRC, INV_BILL, POS';
GO

-- ============================================================================
-- SCRIPT: MÓDULOS ERP COMPLETO - PARTE 5
-- DESCRIPCIÓN: HCM - Human Capital Management (Planillas y RRHH)
-- DEPENDENCIAS: Ejecutar después de PARTE 1-4
-- ============================================================================

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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_emp_dpto FOREIGN KEY (departamento_id) 
        REFERENCES org_departamento(departamento_id) ON DELETE SET NULL,
    CONSTRAINT FK_emp_cargo FOREIGN KEY (cargo_id) 
        REFERENCES org_cargo(cargo_id) ON DELETE SET NULL,
    CONSTRAINT FK_emp_sucursal FOREIGN KEY (sucursal_id) 
        REFERENCES org_sucursal(sucursal_id) ON DELETE SET NULL,
    CONSTRAINT FK_emp_cc FOREIGN KEY (centro_costo_id) 
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE SET NULL,
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
    moneda NVARCHAR(3) DEFAULT 'PEN',
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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_contrato_empleado FOREIGN KEY (empleado_id) 
        REFERENCES hcm_empleado(empleado_id) ON DELETE CASCADE,
    CONSTRAINT FK_contrato_cargo FOREIGN KEY (cargo_id) 
        REFERENCES org_cargo(cargo_id) ON DELETE SET NULL,
    CONSTRAINT FK_contrato_renovado FOREIGN KEY (contrato_renovado_desde_id) 
        REFERENCES hcm_contrato(contrato_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_contrato_numero UNIQUE (cliente_id, empresa_id, numero_contrato)
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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_planilla_cc FOREIGN KEY (centro_costo_id) 
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE SET NULL,
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
    
    CONSTRAINT FK_planemp_planilla FOREIGN KEY (planilla_id) 
        REFERENCES hcm_planilla(planilla_id) ON DELETE CASCADE,
    CONSTRAINT FK_planemp_empleado FOREIGN KEY (empleado_id) 
        REFERENCES hcm_empleado(empleado_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_planemp UNIQUE (cliente_id, planilla_id, empleado_id)
);

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
    
    CONSTRAINT FK_plandet_planemp FOREIGN KEY (planilla_empleado_id) 
        REFERENCES hcm_planilla_empleado(planilla_empleado_id) ON DELETE CASCADE,
    CONSTRAINT FK_plandet_concepto FOREIGN KEY (concepto_id) 
        REFERENCES hcm_concepto_planilla(concepto_id) ON DELETE NO ACTION
);

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
    dia_semana INT AS (DATEPART(WEEKDAY, fecha)) PERSISTED,   -- 1=Domingo, 7=Sábado
    
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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_asist_empleado FOREIGN KEY (empleado_id) 
        REFERENCES hcm_empleado(empleado_id) ON DELETE CASCADE,
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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_vac_empleado FOREIGN KEY (empleado_id) 
        REFERENCES hcm_empleado(empleado_id) ON DELETE CASCADE,
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
    moneda NVARCHAR(3) DEFAULT 'PEN',
    
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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_prestamo_empleado FOREIGN KEY (empleado_id) 
        REFERENCES hcm_empleado(empleado_id) ON DELETE CASCADE,
    CONSTRAINT UQ_prestamo_numero UNIQUE (cliente_id, empresa_id, numero_prestamo)
);

CREATE INDEX IDX_prestamo_empresa ON hcm_prestamo(empresa_id, fecha_prestamo DESC);
CREATE INDEX IDX_prestamo_empleado ON hcm_prestamo(empleado_id, estado);

PRINT 'SECCIÓN 16 creada: HCM (Human Capital Management)';
GO

-- ============================================================================
-- SCRIPT: MÓDULOS ERP COMPLETO - PARTE 6 FINAL
-- DESCRIPCIÓN: FIN, TAX, BDG, CST, PM, SVC, TKT, BI, DMS, WFL, AUD
-- DEPENDENCIAS: Ejecutar después de PARTE 1-5
-- NOTA: Esta es la última parte que completa todos los módulos del sistema
-- ============================================================================

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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
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
    moneda NVARCHAR(3) DEFAULT 'PEN',
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
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_asiento_periodo FOREIGN KEY (periodo_id) 
        REFERENCES fin_periodo_contable(periodo_id) ON DELETE NO ACTION,
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
    
    CONSTRAINT FK_asientodet_asiento FOREIGN KEY (asiento_id) 
        REFERENCES fin_asiento_contable(asiento_id) ON DELETE CASCADE,
    CONSTRAINT FK_asientodet_cuenta FOREIGN KEY (cuenta_id) 
        REFERENCES fin_plan_cuentas(cuenta_id) ON DELETE NO ACTION,
    CONSTRAINT FK_asientodet_cc FOREIGN KEY (centro_costo_id) 
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE SET NULL
);

CREATE INDEX IDX_asientodet_asiento ON fin_asiento_detalle(asiento_id, item);
CREATE INDEX IDX_asientodet_cuenta ON fin_asiento_detalle(cuenta_id);
CREATE INDEX IDX_asientodet_cc ON fin_asiento_detalle(centro_costo_id) WHERE centro_costo_id IS NOT NULL;

-- ============================================================================
-- SECCIÓN 18: TAX - GESTIÓN TRIBUTARIA
-- ============================================================================
-- DESCRIPCIÓN: Obligaciones tributarias, declaraciones, libros electrónicos
-- DEPENDENCIAS: FIN, INV_BILL
-- USADO POR: Reportes a SUNAT, cumplimiento tributario
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: tax_libro_electronico
-- Descripción: Libros electrónicos (ventas, compras, diario, mayor)
-- Uso: Generación de libros para PLE SUNAT
-- Relaciones: Consolida información contable y tributaria
-- -----------------------------------------------------------------------------
CREATE TABLE tax_libro_electronico (
    libro_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    tipo_libro NVARCHAR(30) NOT NULL,                         -- 'ventas', 'compras', 'diario', 'mayor', 'inventarios'
    periodo_id UNIQUEIDENTIFIER NOT NULL,
    
    año INT NOT NULL,
    mes INT NOT NULL,
    
    fecha_generacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    -- Archivo PLE
    nombre_archivo NVARCHAR(255) NULL,
    ruta_archivo NVARCHAR(500) NULL,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'generado',                   -- 'generado', 'enviado', 'aceptado', 'rechazado'
    fecha_envio_sunat DATETIME NULL,
    codigo_respuesta_sunat NVARCHAR(10) NULL,
    
    -- Totales (para validación)
    total_registros INT DEFAULT 0,
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    generado_por_usuario_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_libro_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_libro_periodo FOREIGN KEY (periodo_id) 
        REFERENCES fin_periodo_contable(periodo_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_libro_empresa ON tax_libro_electronico(empresa_id, año DESC, mes DESC);
CREATE INDEX IDX_libro_tipo ON tax_libro_electronico(tipo_libro, año, mes);

-- ============================================================================
-- SECCIÓN 19: BDG - PRESUPUESTOS
-- ============================================================================
-- DESCRIPCIÓN: Gestión de presupuestos por centro de costo y cuenta
-- DEPENDENCIAS: ORG, FIN
-- USADO POR: Control presupuestario
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: bdg_presupuesto
-- Descripción: Presupuesto anual o por periodo
-- Uso: Cabecera de presupuesto
-- Relaciones: Control financiero
-- -----------------------------------------------------------------------------
CREATE TABLE bdg_presupuesto (
    presupuesto_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_presupuesto NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    
    año INT NOT NULL,
    tipo_presupuesto NVARCHAR(20) DEFAULT 'anual',            -- 'anual', 'mensual', 'trimestral'
    
    -- Montos
    monto_total_presupuestado DECIMAL(18,2) DEFAULT 0,
    monto_total_ejecutado DECIMAL(18,2) DEFAULT 0,
    porcentaje_ejecucion AS (
        CASE 
            WHEN monto_total_presupuestado > 0 
            THEN (monto_total_ejecutado / monto_total_presupuestado) * 100
            ELSE 0
        END
    ) PERSISTED,
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'borrador',                   -- 'borrador', 'aprobado', 'vigente', 'cerrado'
    fecha_aprobacion DATETIME NULL,
    
    observaciones NVARCHAR(MAX) NULL,
    
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_creacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_bdg_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT UQ_bdg_codigo UNIQUE (cliente_id, empresa_id, codigo_presupuesto)
);

CREATE INDEX IDX_bdg_empresa ON bdg_presupuesto(empresa_id, año DESC);

-- -----------------------------------------------------------------------------
-- Tabla: bdg_presupuesto_detalle
-- Descripción: Presupuesto por cuenta contable y centro de costo
-- Uso: Asignación presupuestal detallada
-- Relaciones: Detalle de bdg_presupuesto
-- -----------------------------------------------------------------------------
CREATE TABLE bdg_presupuesto_detalle (
    presupuesto_detalle_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    presupuesto_id UNIQUEIDENTIFIER NOT NULL,
    
    cuenta_id UNIQUEIDENTIFIER NOT NULL,
    centro_costo_id UNIQUEIDENTIFIER NULL,
    
    mes INT NULL,                                              -- NULL si es anual consolidado
    
    monto_presupuestado DECIMAL(18,2) NOT NULL,
    monto_ejecutado DECIMAL(18,2) DEFAULT 0,
    monto_disponible AS (monto_presupuestado - monto_ejecutado) PERSISTED,
    
    observaciones NVARCHAR(255) NULL,
    
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_bdgdet_presupuesto FOREIGN KEY (presupuesto_id) 
        REFERENCES bdg_presupuesto(presupuesto_id) ON DELETE CASCADE,
    CONSTRAINT FK_bdgdet_cuenta FOREIGN KEY (cuenta_id) 
        REFERENCES fin_plan_cuentas(cuenta_id) ON DELETE NO ACTION,
    CONSTRAINT FK_bdgdet_cc FOREIGN KEY (centro_costo_id) 
        REFERENCES org_centro_costo(centro_costo_id) ON DELETE SET NULL
);

CREATE INDEX IDX_bdgdet_presupuesto ON bdg_presupuesto_detalle(presupuesto_id);

-- ============================================================================
-- SECCIÓN 20: CST - COSTOS Y COSTEO
-- ============================================================================
-- DESCRIPCIÓN: Costeo de productos, centros de costo, distribución de gastos
-- DEPENDENCIAS: ORG, INV, MFG, HCM, FIN
-- USADO POR: Análisis de rentabilidad, toma de decisiones
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: cst_centro_costo_tipo
-- Descripción: Tipos de centros de costo para distribución
-- Uso: Clasificación para distribución de costos indirectos
-- Relaciones: Extiende org_centro_costo
-- -----------------------------------------------------------------------------
CREATE TABLE cst_centro_costo_tipo (
    cc_tipo_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    
    tipo_clasificacion NVARCHAR(30) NOT NULL,                 -- 'productivo', 'servicio', 'administrativo'
    
    -- Distribución
    base_distribucion NVARCHAR(30) NULL,                      -- 'horas_hombre', 'unidades_producidas', 'ventas', 'area_m2'
    
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_cctipo_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT UQ_cctipo_codigo UNIQUE (cliente_id, empresa_id, codigo)
);

CREATE INDEX IDX_cctipo_empresa ON cst_centro_costo_tipo(empresa_id, es_activo);

-- -----------------------------------------------------------------------------
-- Tabla: cst_producto_costo
-- Descripción: Costeo detallado de productos
-- Uso: Cálculo de costo por producto (materiales, mano de obra, CIF)
-- Relaciones: Vinculado a productos, órdenes de producción
-- -----------------------------------------------------------------------------
CREATE TABLE cst_producto_costo (
    producto_costo_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    producto_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Periodo
    año INT NOT NULL,
    mes INT NOT NULL,
    
    -- Costos
    costo_material_directo DECIMAL(18,4) DEFAULT 0,
    costo_mano_obra_directa DECIMAL(18,4) DEFAULT 0,
    costo_indirecto_fabricacion DECIMAL(18,4) DEFAULT 0,
    costo_total AS (costo_material_directo + costo_mano_obra_directa + costo_indirecto_fabricacion) PERSISTED,
    
    -- Cantidad producida
    cantidad_producida DECIMAL(18,4) DEFAULT 0,
    costo_unitario AS (
        CASE 
            WHEN cantidad_producida > 0 
            THEN (costo_material_directo + costo_mano_obra_directa + costo_indirecto_fabricacion) / cantidad_producida
            ELSE 0
        END
    ) PERSISTED,
    
    -- Referencia
    orden_produccion_id UNIQUEIDENTIFIER NULL,
    
    -- Método de costeo
    metodo_costeo NVARCHAR(20) DEFAULT 'real',                -- 'real', 'estandar', 'promedio'
    
    -- Observaciones
    observaciones NVARCHAR(500) NULL,
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_calculo DATETIME DEFAULT GETDATE(),
    
    CONSTRAINT FK_prodcst_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_prodcst_producto FOREIGN KEY (producto_id) 
        REFERENCES inv_producto(producto_id) ON DELETE CASCADE
);

CREATE INDEX IDX_prodcst_producto ON cst_producto_costo(producto_id, año DESC, mes DESC);

-- ============================================================================
-- SECCIÓN 21-24: MÓDULOS COMPLEMENTARIOS (PM, SVC, TKT, BI)
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: pm_proyecto (Gestión de Proyectos)
-- -----------------------------------------------------------------------------
CREATE TABLE pm_proyecto (
    proyecto_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_proyecto NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(150) NOT NULL,
    descripcion NVARCHAR(MAX) NULL,
    
    cliente_venta_id UNIQUEIDENTIFIER NULL,
    
    fecha_inicio DATE NOT NULL,
    fecha_fin_estimada DATE NULL,
    fecha_fin_real DATE NULL,
    
    presupuesto DECIMAL(18,2) NULL,
    costo_real DECIMAL(18,2) DEFAULT 0,
    
    responsable_usuario_id UNIQUEIDENTIFIER NULL,
    
    estado NVARCHAR(20) DEFAULT 'planificado',                -- 'planificado', 'en_curso', 'pausado', 'completado', 'cancelado'
    
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_proy_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT UQ_proy_codigo UNIQUE (cliente_id, empresa_id, codigo_proyecto)
);

-- -----------------------------------------------------------------------------
-- Tabla: svc_orden_servicio (Gestión de Servicios)
-- -----------------------------------------------------------------------------
CREATE TABLE svc_orden_servicio (
    orden_servicio_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_os NVARCHAR(20) NOT NULL,
    fecha_solicitud DATETIME DEFAULT GETDATE() NOT NULL,
    
    cliente_venta_id UNIQUEIDENTIFIER NULL,
    tipo_servicio NVARCHAR(50) NOT NULL,
    descripcion_servicio NVARCHAR(MAX) NULL,
    
    tecnico_asignado_usuario_id UNIQUEIDENTIFIER NULL,
    
    fecha_inicio_programada DATETIME NULL,
    fecha_inicio_real DATETIME NULL,
    fecha_fin_real DATETIME NULL,
    
    estado NVARCHAR(20) DEFAULT 'solicitada',                 -- 'solicitada', 'asignada', 'en_proceso', 'completada', 'cancelada'
    
    monto_servicio DECIMAL(18,2) NULL,
    
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_os_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT UQ_os_numero UNIQUE (cliente_id, empresa_id, numero_os)
);

-- -----------------------------------------------------------------------------
-- Tabla: tkt_ticket (Mesa de Ayuda / Ticketing)
-- -----------------------------------------------------------------------------
CREATE TABLE tkt_ticket (
    ticket_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    numero_ticket NVARCHAR(20) NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    solicitante_usuario_id UNIQUEIDENTIFIER NULL,
    solicitante_nombre NVARCHAR(150) NULL,
    solicitante_email NVARCHAR(100) NULL,
    
    asunto NVARCHAR(200) NOT NULL,
    descripcion NVARCHAR(MAX) NULL,
    
    categoria NVARCHAR(50) NULL,                              -- 'soporte_tecnico', 'consulta', 'incidencia', 'requerimiento'
    prioridad NVARCHAR(20) DEFAULT 'media',                   -- 'urgente', 'alta', 'media', 'baja'
    
    asignado_usuario_id UNIQUEIDENTIFIER NULL,
    fecha_asignacion DATETIME NULL,
    
    estado NVARCHAR(20) DEFAULT 'abierto',                    -- 'abierto', 'asignado', 'en_proceso', 'resuelto', 'cerrado'
    
    fecha_resolucion DATETIME NULL,
    tiempo_resolucion_horas AS (
        CASE 
            WHEN fecha_resolucion IS NOT NULL 
            THEN DATEDIFF(HOUR, fecha_creacion, fecha_resolucion)
            ELSE NULL
        END
    ) PERSISTED,
    
    solucion NVARCHAR(MAX) NULL,
    
    CONSTRAINT FK_tkt_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT UQ_tkt_numero UNIQUE (cliente_id, empresa_id, numero_ticket)
);

CREATE INDEX IDX_tkt_empresa ON tkt_ticket(empresa_id, fecha_creacion DESC);
CREATE INDEX IDX_tkt_estado ON tkt_ticket(estado, prioridad);

-- -----------------------------------------------------------------------------
-- Tabla: bi_reporte (Business Intelligence - Reportes Personalizados)
-- -----------------------------------------------------------------------------
CREATE TABLE bi_reporte (
    reporte_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_reporte NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(150) NOT NULL,
    descripcion NVARCHAR(500) NULL,
    
    modulo_origen NVARCHAR(10) NULL,                          -- Módulo al que pertenece
    categoria NVARCHAR(50) NULL,                              -- 'ventas', 'inventarios', 'finanzas', etc
    
    tipo_reporte NVARCHAR(20) DEFAULT 'sql',                  -- 'sql', 'olap', 'dashboard'
    
    query_sql NVARCHAR(MAX) NULL,                             -- Query personalizado
    configuracion_json NVARCHAR(MAX) NULL,                    -- Configuración de gráficos, filtros
    
    es_publico BIT DEFAULT 0,                                 -- Si está disponible para todos
    creado_por_usuario_id UNIQUEIDENTIFIER NULL,
    
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_bi_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT UQ_bi_codigo UNIQUE (cliente_id, empresa_id, codigo_reporte)
);

-- ============================================================================
-- SECCIÓN 25-27: MÓDULOS DE GESTIÓN DOCUMENTAL Y AUDITORÍA
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: dms_documento (Document Management System)
-- -----------------------------------------------------------------------------
CREATE TABLE dms_documento (
    documento_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_documento NVARCHAR(20) NULL,
    nombre_archivo NVARCHAR(255) NOT NULL,
    descripcion NVARCHAR(500) NULL,
    
    tipo_documento NVARCHAR(50) NOT NULL,                     -- 'contrato', 'factura', 'reporte', 'certificado', etc
    categoria NVARCHAR(50) NULL,
    
    ruta_archivo NVARCHAR(500) NOT NULL,
    tamaño_bytes BIGINT NULL,
    extension NVARCHAR(10) NULL,
    mime_type NVARCHAR(100) NULL,
    
    -- Clasificación
    carpeta NVARCHAR(255) NULL,
    tags NVARCHAR(MAX) NULL,                                  -- JSON array
    
    -- Relación con entidades
    entidad_tipo NVARCHAR(30) NULL,                           -- 'cliente', 'empleado', 'producto', 'proyecto'
    entidad_id UNIQUEIDENTIFIER NULL,
    
    -- Versionamiento
    version NVARCHAR(10) DEFAULT '1.0',
    documento_padre_id UNIQUEIDENTIFIER NULL,                 -- Si es versión de otro
    
    -- Seguridad
    es_confidencial BIT DEFAULT 0,
    nivel_acceso NVARCHAR(20) DEFAULT 'general',              -- 'publico', 'general', 'restringido', 'confidencial'
    
    -- Estado
    estado NVARCHAR(20) DEFAULT 'activo',                     -- 'activo', 'archivado', 'eliminado'
    
    -- Auditoría
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_modificacion DATETIME NULL,
    subido_por_usuario_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_dms_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT FK_dms_padre FOREIGN KEY (documento_padre_id) 
        REFERENCES dms_documento(documento_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_dms_empresa ON dms_documento(empresa_id, fecha_creacion DESC);
CREATE INDEX IDX_dms_tipo ON dms_documento(tipo_documento, categoria);

-- -----------------------------------------------------------------------------
-- Tabla: wfl_flujo_trabajo (Workflow Engine)
-- -----------------------------------------------------------------------------
CREATE TABLE wfl_flujo_trabajo (
    flujo_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    codigo_flujo NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(150) NOT NULL,
    descripcion NVARCHAR(500) NULL,
    
    tipo_flujo NVARCHAR(30) NOT NULL,                         -- 'aprobacion', 'revision', 'notificacion'
    modulo_aplicable NVARCHAR(10) NULL,                       -- Módulo donde aplica
    
    -- Definición del flujo (JSON)
    definicion_pasos NVARCHAR(MAX) NULL,                      -- JSON con pasos del workflow
    
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_wfl_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE,
    CONSTRAINT UQ_wfl_codigo UNIQUE (cliente_id, empresa_id, codigo_flujo)
);

-- -----------------------------------------------------------------------------
-- Tabla: aud_log_auditoria (Sistema de Auditoría)
-- -----------------------------------------------------------------------------
CREATE TABLE aud_log_auditoria (
    log_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id UNIQUEIDENTIFIER NOT NULL,
    
    fecha_evento DATETIME DEFAULT GETDATE() NOT NULL,
    
    usuario_id UNIQUEIDENTIFIER NULL,
    usuario_nombre NVARCHAR(150) NULL,
    
    -- Acción
    modulo NVARCHAR(10) NOT NULL,
    tabla NVARCHAR(100) NOT NULL,
    accion NVARCHAR(20) NOT NULL,                             -- 'INSERT', 'UPDATE', 'DELETE', 'SELECT'
    
    -- Registro afectado
    registro_id UNIQUEIDENTIFIER NULL,
    registro_descripcion NVARCHAR(255) NULL,
    
    -- Valores
    valores_anteriores NVARCHAR(MAX) NULL,                    -- JSON
    valores_nuevos NVARCHAR(MAX) NULL,                        -- JSON
    
    -- Metadata
    ip_address NVARCHAR(45) NULL,
    user_agent NVARCHAR(500) NULL,
    
    observaciones NVARCHAR(500) NULL,
    
    CONSTRAINT FK_aud_empresa FOREIGN KEY (empresa_id) 
        REFERENCES org_empresa(empresa_id) ON DELETE CASCADE
);

CREATE INDEX IDX_aud_empresa ON aud_log_auditoria(empresa_id, fecha_evento DESC);
CREATE INDEX IDX_aud_modulo ON aud_log_auditoria(modulo, tabla, fecha_evento DESC);
CREATE INDEX IDX_aud_usuario ON aud_log_auditoria(usuario_id, fecha_evento DESC) WHERE usuario_id IS NOT NULL;
CREATE INDEX IDX_aud_accion ON aud_log_auditoria(accion, fecha_evento DESC);

-- ============================================================================
-- FIN DEL SCRIPT - TODOS LOS MÓDULOS COMPLETADOS
-- ============================================================================

PRINT '============================================================================';
PRINT 'MÓDULOS ERP COMPLETADOS - PARTE 6 FINAL';
PRINT 'Secciones creadas: FIN, TAX, BDG, CST, PM, SVC, TKT, BI, DMS, WFL, AUD';
PRINT '============================================================================';
PRINT 'SISTEMA ERP COMPLETO - TODOS LOS MÓDULOS CREADOS EXITOSAMENTE';
PRINT '============================================================================';
GO