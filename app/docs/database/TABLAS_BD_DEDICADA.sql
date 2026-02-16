-- ============================================================================
-- SCRIPT: TABLAS PARA BD DEDICADA DE CLIENTE
-- DESCRIPCIÓN: Estructura completa de tablas que deben crearse en cada BD dedicada
-- USO: Ejecutar en cada BD cliente (bd_cliente_acme, bd_cliente_innova, etc.)
-- NOTA: Este esquema usa UNIQUEIDENTIFIER (UUID) para todas las Primary Keys
-- ============================================================================

-- ============================================================================
-- SECCIÓN 1: AUTENTICACIÓN Y SEGURIDAD
-- ============================================================================

-- Tabla: usuario
CREATE TABLE usuario (
    usuario_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,                      -- Siempre el mismo para toda la BD
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
    
    CONSTRAINT UQ_usuario_cliente_nombre UNIQUE (cliente_id, nombre_usuario)
);

-- Tabla: rol
CREATE TABLE rol (
    rol_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,                      -- Siempre el mismo para toda la BD
    codigo_rol NVARCHAR(30) NULL,
    nombre NVARCHAR(50) NOT NULL,
    descripcion NVARCHAR(255) NULL,
    es_rol_sistema BIT DEFAULT 0,
    nivel_acceso INT DEFAULT 1,
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_actualizacion DATETIME NULL,
    
    CONSTRAINT UQ_rol_cliente_nombre UNIQUE (cliente_id, nombre)
);

-- Tabla: usuario_rol
CREATE TABLE usuario_rol (
    usuario_rol_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    usuario_id UNIQUEIDENTIFIER NOT NULL,
    rol_id UNIQUEIDENTIFIER NOT NULL,
    cliente_id UNIQUEIDENTIFIER NOT NULL,                      -- Siempre el mismo para toda la BD
    fecha_asignacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_expiracion DATETIME NULL,
    es_activo BIT DEFAULT 1 NOT NULL,
    asignado_por_usuario_id UNIQUEIDENTIFIER NULL,
    
    CONSTRAINT FK_usuario_rol_usuario FOREIGN KEY (usuario_id) 
        REFERENCES usuario(usuario_id) ON DELETE CASCADE,
    CONSTRAINT FK_usuario_rol_rol FOREIGN KEY (rol_id) 
        REFERENCES rol(rol_id) ON DELETE NO ACTION,
    CONSTRAINT UQ_usuario_rol UNIQUE (usuario_id, rol_id)
);

-- Tabla: rol_menu_permiso
-- ⚠️ NOTA: menu_id referencia modulo_menu en BD CENTRAL (cross-database)
CREATE TABLE rol_menu_permiso (
    permiso_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,                      -- Siempre el mismo para toda la BD
    rol_id UNIQUEIDENTIFIER NOT NULL,
    menu_id UNIQUEIDENTIFIER NOT NULL,                         -- FK a modulo_menu en BD CENTRAL
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
    CONSTRAINT UQ_rol_menu UNIQUE (cliente_id, rol_id, menu_id)
    -- ⚠️ NO se puede crear FK a modulo_menu porque está en otra BD
    -- Validar existencia de menu_id en aplicación o usar cross-database query
);

-- Tabla: refresh_tokens
CREATE TABLE refresh_tokens (
    token_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,                      -- Siempre el mismo para toda la BD
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
    
    CONSTRAINT FK_refresh_token_usuario FOREIGN KEY (usuario_id) 
        REFERENCES usuario(usuario_id) ON DELETE CASCADE
);

-- Tabla: auth_audit_log
CREATE TABLE auth_audit_log (
    log_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,                      -- Siempre el mismo para toda la BD
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
    
    CONSTRAINT FK_audit_usuario FOREIGN KEY (usuario_id) 
        REFERENCES usuario(usuario_id) ON DELETE SET NULL
);

-- ============================================================================
-- ÍNDICES OPTIMIZADOS
-- ============================================================================

CREATE INDEX IDX_usuario_cliente ON usuario(cliente_id, es_activo) WHERE es_eliminado = 0;
CREATE INDEX IDX_usuario_correo ON usuario(correo) WHERE correo IS NOT NULL;
CREATE INDEX IDX_usuario_dni ON usuario(dni) WHERE dni IS NOT NULL;
CREATE INDEX IDX_usuario_referencia_externa ON usuario(referencia_externa_id) WHERE referencia_externa_id IS NOT NULL;

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

PRINT 'Estructura de BD dedicada creada exitosamente';
GO

-- ============================================================================
-- NOTAS IMPORTANTES:
-- ============================================================================
-- 1. Todas las tablas tienen cliente_id para mantener consistencia
-- 2. cliente_id siempre será el mismo valor en toda la BD dedicada
-- 3. rol_menu_permiso.menu_id referencia modulo_menu en BD CENTRAL
--    - Requiere validación en aplicación o cross-database query
-- 4. Las tablas de negocio (empleado, planilla, producto, etc.) se crean
--    cuando el cliente activa el módulo correspondiente
-- 5. Ver: app/docs/database/ORGANIZACION_TABLAS_CENTRAL_VS_DEDICADA.md
-- ============================================================================
