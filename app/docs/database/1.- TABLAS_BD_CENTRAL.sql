-- ============================================================================
-- SCRIPT: TABLAS PARA BD CENTRAL
-- DESCRIPCIÓN: Estructura completa de tablas que deben crearse en BD CENTRAL
-- USO: Ejecutar UNA SOLA VEZ al crear bd_hybrid_sistema_central
-- NOTA: Este esquema usa UNIQUEIDENTIFIER (UUID) para todas las Primary Keys
-- ============================================================================

-- ============================================================================
-- SECCIÓN 1: ADMINISTRACIÓN DE CLIENTES
-- ============================================================================

-- Tabla: cliente
CREATE TABLE cliente (
    cliente_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    codigo_cliente NVARCHAR(20) NOT NULL UNIQUE,
    subdominio NVARCHAR(63) NOT NULL UNIQUE,
    razon_social NVARCHAR(200) NOT NULL,
    nombre_comercial NVARCHAR(150) NULL,
    ruc NVARCHAR(11) NULL,
    tipo_instalacion NVARCHAR(20) DEFAULT 'shared' NOT NULL,
    servidor_api_local NVARCHAR(255) NULL,
    modo_autenticacion NVARCHAR(20) DEFAULT 'local' NOT NULL,
    logo_url NVARCHAR(500) NULL,
    favicon_url NVARCHAR(500) NULL,
    color_primario NVARCHAR(7) DEFAULT '#1976D2',
    color_secundario NVARCHAR(7) DEFAULT '#424242',
    tema_personalizado NVARCHAR(MAX) NULL,
    plan_suscripcion NVARCHAR(30) DEFAULT 'trial',
    estado_suscripcion NVARCHAR(20) DEFAULT 'activo',
    fecha_inicio_suscripcion DATE NULL,
    fecha_fin_trial DATE NULL,
    contacto_nombre NVARCHAR(100) NULL,
    contacto_email NVARCHAR(100) NOT NULL,
    contacto_telefono NVARCHAR(20) NULL,
    es_activo BIT DEFAULT 1 NOT NULL,
    es_demo BIT DEFAULT 0,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    fecha_ultimo_acceso DATETIME NULL,
    api_key_sincronizacion NVARCHAR(255) NULL,
    sincronizacion_habilitada BIT DEFAULT 0,
    ultima_sincronizacion DATETIME NULL,
    metadata_json NVARCHAR(MAX) NULL
);

CREATE UNIQUE INDEX UQ_cliente_subdominio ON cliente(subdominio) WHERE es_activo = 1;
CREATE INDEX IDX_cliente_codigo ON cliente(codigo_cliente);
CREATE INDEX IDX_cliente_estado ON cliente(es_activo, estado_suscripcion);
CREATE INDEX IDX_cliente_tipo ON cliente(tipo_instalacion);

-- Tabla: cliente_conexion
CREATE TABLE cliente_conexion (
    conexion_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    servidor NVARCHAR(255) NOT NULL,
    puerto INT DEFAULT 1433,
    nombre_bd NVARCHAR(100) NOT NULL,
    usuario_encriptado NVARCHAR(500) NOT NULL,
    password_encriptado NVARCHAR(500) NOT NULL,
    connection_string_encriptado NVARCHAR(MAX) NULL,
    tipo_bd NVARCHAR(20) DEFAULT 'sqlserver',
    usa_ssl BIT DEFAULT 0,
    timeout_segundos INT DEFAULT 30,
    max_pool_size INT DEFAULT 100,
    es_solo_lectura BIT DEFAULT 0,
    es_conexion_principal BIT DEFAULT 0,
    es_activo BIT DEFAULT 1,
    ultima_conexion_exitosa DATETIME NULL,
    ultimo_error NVARCHAR(MAX) NULL,
    fecha_ultimo_error DATETIME NULL,
    fecha_creacion DATETIME DEFAULT GETDATE(),
    fecha_actualizacion DATETIME NULL,
    creado_por_usuario_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_conexion_cliente FOREIGN KEY (cliente_id) 
        REFERENCES cliente(cliente_id) ON DELETE CASCADE,
    CONSTRAINT UQ_conexion_principal_cliente UNIQUE (cliente_id, es_conexion_principal)
);

CREATE INDEX IDX_conexion_cliente ON cliente_conexion(cliente_id, es_activo);
CREATE INDEX IDX_conexion_principal ON cliente_conexion(cliente_id, es_conexion_principal);

-- Tabla: cliente_auth_config
CREATE TABLE cliente_auth_config (
    config_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL UNIQUE,
    password_min_length INT DEFAULT 8,
    password_require_uppercase BIT DEFAULT 1,
    password_require_lowercase BIT DEFAULT 1,
    password_require_number BIT DEFAULT 1,
    password_require_special BIT DEFAULT 0,
    password_expiry_days INT DEFAULT 90,
    password_history_count INT DEFAULT 3,
    max_login_attempts INT DEFAULT 5,
    lockout_duration_minutes INT DEFAULT 30,
    max_active_sessions INT DEFAULT 3,
    session_idle_timeout_minutes INT DEFAULT 60,
    access_token_minutes INT DEFAULT 15,
    refresh_token_days INT DEFAULT 30,
    allow_remember_me BIT DEFAULT 1,
    remember_me_days INT DEFAULT 30,
    require_email_verification BIT DEFAULT 0,
    allow_password_reset BIT DEFAULT 1,
    enable_2fa BIT DEFAULT 0,
    require_2fa_for_admins BIT DEFAULT 0,
    metodos_2fa_permitidos NVARCHAR(100) DEFAULT 'email,sms',
    ip_whitelist_enabled BIT DEFAULT 0,
    ip_whitelist NVARCHAR(MAX) NULL,
    ip_blacklist NVARCHAR(MAX) NULL,
    horario_acceso_enabled BIT DEFAULT 0,
    horario_acceso_config NVARCHAR(MAX) NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    
    CONSTRAINT FK_auth_config_cliente FOREIGN KEY (cliente_id) 
        REFERENCES cliente(cliente_id) ON DELETE CASCADE
);

-- Tabla: federacion_identidad
CREATE TABLE federacion_identidad (
    federacion_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    nombre_configuracion NVARCHAR(100) NOT NULL,
    proveedor NVARCHAR(30) NOT NULL,
    client_id NVARCHAR(255) NULL,
    client_secret_encrypted NVARCHAR(500) NULL,
    authority_url NVARCHAR(500) NULL,
    token_endpoint NVARCHAR(500) NULL,
    authorization_endpoint NVARCHAR(500) NULL,
    userinfo_endpoint NVARCHAR(500) NULL,
    redirect_uri NVARCHAR(500) NULL,
    scope NVARCHAR(200) DEFAULT 'openid profile email',
    entity_id NVARCHAR(500) NULL,
    sso_url NVARCHAR(500) NULL,
    slo_url NVARCHAR(500) NULL,
    certificate_x509 NVARCHAR(MAX) NULL,
    attribute_mapping NVARCHAR(MAX) NULL,
    es_activo BIT DEFAULT 1 NOT NULL,
    es_metodo_principal BIT DEFAULT 0,
    auto_provision_users BIT DEFAULT 1,
    sync_user_data BIT DEFAULT 1,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    ultimo_login_sso DATETIME NULL,
    
    CONSTRAINT FK_federacion_cliente FOREIGN KEY (cliente_id) 
        REFERENCES cliente(cliente_id) ON DELETE CASCADE
);

CREATE INDEX IDX_federacion_cliente ON federacion_identidad(cliente_id, es_activo);
CREATE INDEX IDX_federacion_proveedor ON federacion_identidad(proveedor);

-- ============================================================================
-- SECCIÓN 2: CATÁLOGO DE MÓDULOS ERP
-- ============================================================================

-- Tabla: modulo
CREATE TABLE modulo (
    modulo_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    codigo NVARCHAR(30) NOT NULL UNIQUE,
    nombre NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(500) NULL,
    icono NVARCHAR(50) NULL,
    color NVARCHAR(7) DEFAULT '#1976D2',
    categoria NVARCHAR(30) DEFAULT 'operaciones',
    es_core BIT DEFAULT 0,
    requiere_licencia BIT DEFAULT 1,
    precio_mensual DECIMAL(10,2) NULL,
    modulos_requeridos NVARCHAR(MAX) NULL,
    orden INT DEFAULT 0,
    es_activo BIT DEFAULT 1,
    fecha_creacion DATETIME DEFAULT GETDATE(),
    fecha_actualizacion DATETIME NULL,
    configuracion_defecto NVARCHAR(MAX) NULL
);

CREATE INDEX IDX_modulo_codigo ON modulo(codigo);
CREATE INDEX IDX_modulo_activo ON modulo(es_activo, orden);
CREATE INDEX IDX_modulo_categoria ON modulo(categoria, orden);

-- Tabla: modulo_seccion
CREATE TABLE modulo_seccion (
    seccion_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    modulo_id UNIQUEIDENTIFIER NOT NULL,
    codigo NVARCHAR(30) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(255) NULL,
    icono NVARCHAR(50) NULL,
    orden INT DEFAULT 0,
    es_seccion_sistema BIT DEFAULT 1,
    es_activo BIT DEFAULT 1,
    fecha_creacion DATETIME DEFAULT GETDATE(),
    
    CONSTRAINT FK_seccion_modulo FOREIGN KEY (modulo_id) 
        REFERENCES modulo(modulo_id) ON DELETE CASCADE,
    CONSTRAINT UQ_seccion_modulo_codigo UNIQUE (modulo_id, codigo)
);

CREATE INDEX IDX_seccion_modulo ON modulo_seccion(modulo_id, es_activo, orden);

-- Tabla: modulo_menu
CREATE TABLE modulo_menu (
    menu_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    modulo_id UNIQUEIDENTIFIER NOT NULL,
    seccion_id UNIQUEIDENTIFIER NULL,
    cliente_id UNIQUEIDENTIFIER NULL,
    codigo NVARCHAR(50) NULL,
    nombre NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(255) NULL,
    icono NVARCHAR(50) NULL,
    ruta NVARCHAR(255) NULL,
    menu_padre_id UNIQUEIDENTIFIER NULL,
    nivel INT DEFAULT 1,
    tipo_menu NVARCHAR(20) DEFAULT 'pantalla',
    orden INT DEFAULT 0,
    requiere_autenticacion BIT DEFAULT 1,
    es_visible BIT DEFAULT 1,
    es_menu_sistema BIT DEFAULT 1,
    es_activo BIT DEFAULT 1,
    fecha_creacion DATETIME DEFAULT GETDATE(),
    fecha_actualizacion DATETIME NULL,
    configuracion_json NVARCHAR(MAX) NULL,
    
    CONSTRAINT FK_menu_modulo FOREIGN KEY (modulo_id) 
        REFERENCES modulo(modulo_id) ON DELETE CASCADE,
    CONSTRAINT FK_menu_seccion FOREIGN KEY (seccion_id) 
        REFERENCES modulo_seccion(seccion_id) ON DELETE NO ACTION,
    CONSTRAINT FK_menu_cliente FOREIGN KEY (cliente_id) 
        REFERENCES cliente(cliente_id) ON DELETE CASCADE,
    CONSTRAINT FK_menu_padre FOREIGN KEY (menu_padre_id) 
        REFERENCES modulo_menu(menu_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_menu_modulo ON modulo_menu(modulo_id, es_activo, orden);
CREATE INDEX IDX_menu_seccion ON modulo_menu(seccion_id, orden);
CREATE INDEX IDX_menu_padre ON modulo_menu(menu_padre_id, orden);
CREATE INDEX IDX_menu_cliente ON modulo_menu(cliente_id, es_activo);
CREATE INDEX IDX_menu_ruta ON modulo_menu(ruta) WHERE ruta IS NOT NULL;

-- Tabla: modulo_rol_plantilla
CREATE TABLE modulo_rol_plantilla (
    plantilla_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    modulo_id UNIQUEIDENTIFIER NOT NULL,
    nombre_rol NVARCHAR(50) NOT NULL,
    descripcion NVARCHAR(255) NULL,
    nivel_acceso INT DEFAULT 1,
    permisos_json NVARCHAR(MAX) NULL,
    es_activo BIT DEFAULT 1,
    orden INT DEFAULT 0,
    fecha_creacion DATETIME DEFAULT GETDATE(),
    
    CONSTRAINT FK_plantilla_modulo FOREIGN KEY (modulo_id) 
        REFERENCES modulo(modulo_id) ON DELETE CASCADE
);

CREATE INDEX IDX_plantilla_modulo ON modulo_rol_plantilla(modulo_id, es_activo, orden);

-- Tabla: cliente_modulo
CREATE TABLE cliente_modulo (
    cliente_modulo_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    modulo_id UNIQUEIDENTIFIER NOT NULL,
    esta_activo BIT DEFAULT 1,
    fecha_activacion DATETIME DEFAULT GETDATE(),
    fecha_vencimiento DATETIME NULL,
    modo_prueba BIT DEFAULT 0,
    fecha_fin_prueba DATETIME NULL,
    configuracion_json NVARCHAR(MAX) NULL,
    limite_usuarios INT NULL,
    limite_registros INT NULL,
    limite_transacciones_mes INT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE(),
    fecha_actualizacion DATETIME NULL,
    activado_por_usuario_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_cliente_modulo_cliente FOREIGN KEY (cliente_id) 
        REFERENCES cliente(cliente_id) ON DELETE CASCADE,
    CONSTRAINT FK_cliente_modulo_modulo FOREIGN KEY (modulo_id) 
        REFERENCES modulo(modulo_id) ON DELETE CASCADE,
    CONSTRAINT UQ_cliente_modulo UNIQUE (cliente_id, modulo_id)
);

CREATE INDEX IDX_cliente_modulo_cliente ON cliente_modulo(cliente_id, esta_activo);
CREATE INDEX IDX_cliente_modulo_vencimiento ON cliente_modulo(fecha_vencimiento) 
    WHERE fecha_vencimiento IS NOT NULL;

-- ============================================================================
-- SECCIÓN 3: TABLAS OPERATIVAS (Para clientes con tipo_instalacion = 'shared')
-- ============================================================================
-- NOTA: Estas tablas también existen en BD dedicada para clientes con BD propia.
-- En BD central se usan cuando cliente.tipo_instalacion = 'shared'
-- ============================================================================

-- Tabla: usuario
CREATE TABLE usuario (
    usuario_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    nombre_usuario NVARCHAR(100) NOT NULL,
    contrasena NVARCHAR(255) NOT NULL,
    nombre NVARCHAR(100) NULL,
    apellido NVARCHAR(100) NULL,
    correo NVARCHAR(150) NULL,
    dni NVARCHAR(8) NULL,
    telefono NVARCHAR(20) NULL,
    proveedor_autenticacion NVARCHAR(30) DEFAULT 'local' NOT NULL,
    referencia_externa_id NVARCHAR(255) NULL,
    referencia_externa_email NVARCHAR(150) NULL,
    es_activo BIT DEFAULT 1 NOT NULL,
    correo_confirmado BIT DEFAULT 0,
    requiere_cambio_contrasena BIT DEFAULT 0,
    intentos_fallidos INT DEFAULT 0,
    fecha_bloqueo DATETIME NULL,
    fecha_ultimo_cambio_contrasena DATETIME NULL,
    ultimo_ip NVARCHAR(45) NULL,
    sincronizado_desde NVARCHAR(30) NULL,
    referencia_sincronizacion_id UNIQUEIDENTIFIER NULL,
    fecha_ultima_sincronizacion DATETIME NULL,
    hash_datos_sincronizado NVARCHAR(64) NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    fecha_ultimo_acceso DATETIME NULL,
    es_eliminado BIT DEFAULT 0,
    fecha_eliminacion DATETIME NULL,
    usuario_eliminacion_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_usuario_cliente FOREIGN KEY (cliente_id) 
        REFERENCES cliente(cliente_id) ON DELETE CASCADE,
    CONSTRAINT UQ_usuario_cliente_nombre UNIQUE (cliente_id, nombre_usuario)
);

-- Tabla: rol
CREATE TABLE rol (
    rol_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NULL,                          -- NULL = Rol global del sistema
    codigo_rol NVARCHAR(30) NULL,
    nombre NVARCHAR(50) NOT NULL,
    descripcion NVARCHAR(255) NULL,
    es_rol_sistema BIT DEFAULT 0,
    nivel_acceso INT DEFAULT 1,
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    
    CONSTRAINT FK_rol_cliente FOREIGN KEY (cliente_id) 
        REFERENCES cliente(cliente_id) ON DELETE CASCADE,
    CONSTRAINT UQ_rol_cliente_nombre UNIQUE (cliente_id, nombre)
);

-- Tabla: usuario_rol
CREATE TABLE usuario_rol (
    usuario_rol_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    usuario_id UNIQUEIDENTIFIER NOT NULL,
    rol_id UNIQUEIDENTIFIER NOT NULL,
    cliente_id UNIQUEIDENTIFIER NOT NULL,                      -- Desnormalizado para queries rápidas
    fecha_asignacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_expiracion DATETIME NULL,
    es_activo BIT DEFAULT 1 NOT NULL,
    asignado_por_usuario_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_usuario_rol_usuario FOREIGN KEY (usuario_id) 
        REFERENCES usuario(usuario_id) ON DELETE CASCADE,
    CONSTRAINT FK_usuario_rol_rol FOREIGN KEY (rol_id) 
        REFERENCES rol(rol_id) ON DELETE NO ACTION,
    CONSTRAINT FK_usuario_rol_cliente FOREIGN KEY (cliente_id) 
        REFERENCES cliente(cliente_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_usuario_rol UNIQUE (usuario_id, rol_id)
);

-- Tabla: rol_menu_permiso
CREATE TABLE rol_menu_permiso (
    permiso_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    rol_id UNIQUEIDENTIFIER NOT NULL,
    menu_id UNIQUEIDENTIFIER NOT NULL,
    puede_ver BIT DEFAULT 1 NOT NULL,
    puede_crear BIT DEFAULT 0,
    puede_editar BIT DEFAULT 0,
    puede_eliminar BIT DEFAULT 0,
    puede_exportar BIT DEFAULT 0,
    puede_imprimir BIT DEFAULT 0,
    puede_aprobar BIT DEFAULT 0,
    permisos_extra NVARCHAR(MAX) NULL,
    fecha_creacion DATETIME DEFAULT GETDATE(),
    fecha_actualizacion DATETIME NULL,
    
    CONSTRAINT FK_permiso_rol FOREIGN KEY (rol_id) 
        REFERENCES rol(rol_id) ON DELETE CASCADE,
    CONSTRAINT FK_permiso_menu FOREIGN KEY (menu_id) 
        REFERENCES modulo_menu(menu_id) ON DELETE NO ACTION,
    CONSTRAINT FK_permiso_cliente FOREIGN KEY (cliente_id) 
        REFERENCES cliente(cliente_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_rol_menu UNIQUE (cliente_id, rol_id, menu_id)
);

-- Tabla: refresh_tokens
CREATE TABLE refresh_tokens (
    token_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    usuario_id UNIQUEIDENTIFIER NOT NULL,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at DATETIME NOT NULL,
    is_revoked BIT DEFAULT 0 NOT NULL,
    revoked_at DATETIME NULL,
    revoked_reason NVARCHAR(100) NULL,
    client_type VARCHAR(10) DEFAULT 'web' NOT NULL,
    device_name NVARCHAR(100) NULL,
    device_id NVARCHAR(100) NULL,
    ip_address VARCHAR(45) NULL,
    user_agent VARCHAR(500) NULL,
    created_at DATETIME DEFAULT GETDATE() NOT NULL,
    last_used_at DATETIME NULL,
    uso_count INT DEFAULT 0,
    
    CONSTRAINT FK_refresh_token_cliente FOREIGN KEY (cliente_id) 
        REFERENCES cliente(cliente_id) ON DELETE CASCADE,
    CONSTRAINT FK_refresh_token_usuario FOREIGN KEY (usuario_id) 
        REFERENCES usuario(usuario_id) ON DELETE NO ACTION
);

-- Tabla: auth_audit_log
CREATE TABLE auth_audit_log (
    log_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    usuario_id UNIQUEIDENTIFIER NULL,
    evento NVARCHAR(50) NOT NULL,
    nombre_usuario_intento NVARCHAR(100) NULL,
    descripcion NVARCHAR(500) NULL,
    exito BIT NOT NULL,
    codigo_error NVARCHAR(50) NULL,
    ip_address VARCHAR(45) NULL,
    user_agent VARCHAR(500) NULL,
    device_info NVARCHAR(200) NULL,
    geolocation NVARCHAR(100) NULL,
    metadata_json NVARCHAR(MAX) NULL,
    fecha_evento DATETIME DEFAULT GETDATE() NOT NULL,
    
    CONSTRAINT FK_audit_cliente FOREIGN KEY (cliente_id) 
        REFERENCES cliente(cliente_id) ON DELETE CASCADE,
    CONSTRAINT FK_audit_usuario FOREIGN KEY (usuario_id) 
        REFERENCES usuario(usuario_id) ON DELETE NO ACTION
);

-- Índices para tablas operativas
CREATE INDEX IDX_usuario_cliente ON usuario(cliente_id, es_activo) WHERE es_eliminado = 0;
CREATE INDEX IDX_usuario_correo ON usuario(correo) WHERE correo IS NOT NULL;
CREATE INDEX IDX_usuario_dni ON usuario(dni) WHERE dni IS NOT NULL;
CREATE INDEX IDX_usuario_referencia_externa ON usuario(referencia_externa_id) WHERE referencia_externa_id IS NOT NULL;
CREATE INDEX IDX_usuario_sincronizacion ON usuario(sincronizado_desde, fecha_ultima_sincronizacion);

CREATE INDEX IDX_rol_cliente ON rol(cliente_id, es_activo);
CREATE INDEX IDX_rol_codigo ON rol(codigo_rol) WHERE codigo_rol IS NOT NULL;

CREATE INDEX IDX_usuario_rol_usuario ON usuario_rol(usuario_id, es_activo);
CREATE INDEX IDX_usuario_rol_rol ON usuario_rol(rol_id, es_activo);
CREATE INDEX IDX_usuario_rol_cliente ON usuario_rol(cliente_id);

CREATE INDEX IDX_permiso_rol ON rol_menu_permiso(rol_id, puede_ver);
CREATE INDEX IDX_permiso_menu ON rol_menu_permiso(menu_id);
CREATE INDEX IDX_permiso_cliente ON rol_menu_permiso(cliente_id);

CREATE INDEX IDX_refresh_token_usuario_cliente ON refresh_tokens(usuario_id, cliente_id);
CREATE INDEX IDX_refresh_token_active ON refresh_tokens(usuario_id, is_revoked, expires_at);
CREATE INDEX IDX_refresh_token_cleanup ON refresh_tokens(expires_at, is_revoked);
CREATE INDEX IDX_refresh_token_device ON refresh_tokens(device_id) WHERE device_id IS NOT NULL;

CREATE INDEX IDX_audit_cliente_fecha ON auth_audit_log(cliente_id, fecha_evento DESC);
CREATE INDEX IDX_audit_usuario_fecha ON auth_audit_log(usuario_id, fecha_evento DESC) WHERE usuario_id IS NOT NULL;
CREATE INDEX IDX_audit_evento ON auth_audit_log(evento, fecha_evento DESC);
CREATE INDEX IDX_audit_exito ON auth_audit_log(exito, fecha_evento DESC);
CREATE INDEX IDX_audit_ip ON auth_audit_log(ip_address, fecha_evento DESC) WHERE ip_address IS NOT NULL;

-- ============================================================================
-- SECCIÓN 4: AUDITORÍA Y SINCRONIZACIÓN
-- ============================================================================

-- Tabla: log_sincronizacion_usuario
CREATE TABLE log_sincronizacion_usuario (
    log_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_origen_id UNIQUEIDENTIFIER NULL,
    cliente_destino_id UNIQUEIDENTIFIER NULL,
    usuario_id UNIQUEIDENTIFIER NOT NULL,
    tipo_sincronizacion NVARCHAR(20) NOT NULL,
    direccion NVARCHAR(10) NOT NULL,
    operacion NVARCHAR(20) NOT NULL,
    estado NVARCHAR(20) NOT NULL,
    mensaje_error NVARCHAR(MAX) NULL,
    campos_sincronizados NVARCHAR(MAX) NULL,
    cambios_detectados NVARCHAR(MAX) NULL,
    hash_antes NVARCHAR(64) NULL,
    hash_despues NVARCHAR(64) NULL,
    fecha_sincronizacion DATETIME DEFAULT GETDATE() NOT NULL,
    usuario_ejecutor_id UNIQUEIDENTIFIER NULL,
    duracion_ms INT NULL,
    
    CONSTRAINT FK_log_sync_cliente_origen FOREIGN KEY (cliente_origen_id) 
        REFERENCES cliente(cliente_id) ON DELETE NO ACTION,
    CONSTRAINT FK_log_sync_cliente_destino FOREIGN KEY (cliente_destino_id) 
        REFERENCES cliente(cliente_id) ON DELETE NO ACTION
);

CREATE INDEX IDX_log_sync_origen ON log_sincronizacion_usuario(cliente_origen_id, estado);
CREATE INDEX IDX_log_sync_destino ON log_sincronizacion_usuario(cliente_destino_id, estado);
CREATE INDEX IDX_log_sync_fecha ON log_sincronizacion_usuario(fecha_sincronizacion DESC);

PRINT 'Estructura de BD central creada exitosamente';
GO

-- ============================================================================
-- NOTAS IMPORTANTES:
-- ============================================================================
-- 1. Esta BD contiene:
--    - Tablas GLOBALES (catálogos maestros, configuración)
--    - Tablas OPERATIVAS para clientes con tipo_instalacion = 'shared'
--
-- 2. Clientes con tipo_instalacion = 'shared':
--    - Sus datos operativos (usuario, rol, etc.) están en esta BD central
--    - Se filtran por cliente_id en todas las queries
--
-- 3. Clientes con tipo_instalacion = 'dedicated' o 'onpremise':
--    - Sus datos operativos están en su BD dedicada
--    - Ver: app/docs/database/TABLAS_BD_DEDICADA.sql
--
-- 4. modulo_menu.cliente_id puede ser NULL (menú global) o UUID (menú personalizado)
--
-- 5. rol.cliente_id puede ser NULL (rol global del sistema) o UUID (rol del cliente)
--
-- 6. Ver: app/docs/database/ORGANIZACION_TABLAS_CENTRAL_VS_DEDICADA.md
-- ============================================================================
