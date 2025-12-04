-- ============================================================================
-- SCRIPT: 01_estructura_bd_clientes.sql
-- DESCRIPCIÓN: Estructura de tablas OPERATIVAS para BD de clientes
-- USO: Ejecutar en cada BD cliente (bd_cliente_acme, bd_cliente_innova, etc.)
-- NOTA: Este esquema usa UNIQUEIDENTIFIER (UUID) para todas las Primary Keys
-- ============================================================================

-- Tablas de AUTENTICACIÓN y SEGURIDAD (específicas del cliente)
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
    usuario_eliminacion_id UNIQUEIDENTIFIER NULL
);

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
    fecha_actualizacion DATETIME NULL
);

CREATE TABLE usuario_rol (
    usuario_rol_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    usuario_id UNIQUEIDENTIFIER NOT NULL,
    rol_id UNIQUEIDENTIFIER NOT NULL,
    cliente_id UNIQUEIDENTIFIER NOT NULL,                      -- Siempre el mismo para toda la BD
    fecha_asignacion DATETIME DEFAULT GETDATE() NOT NULL,
    fecha_expiracion DATETIME NULL,
    es_activo BIT DEFAULT 1 NOT NULL,
    asignado_por_usuario_id UNIQUEIDENTIFIER NULL
);

CREATE TABLE area_menu (
    area_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,                      -- Siempre el mismo para toda la BD
    nombre NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(255) NULL,
    icono NVARCHAR(50) NULL,
    orden INT DEFAULT 0,
    es_area_sistema BIT DEFAULT 0,
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL
);

CREATE TABLE menu (
    menu_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,                      -- Siempre el mismo para toda la BD
    area_id UNIQUEIDENTIFIER NULL,
    nombre NVARCHAR(100) NOT NULL,
    descripcion NVARCHAR(255) NULL,
    icono NVARCHAR(50) NULL,
    ruta NVARCHAR(255) NULL,
    padre_menu_id UNIQUEIDENTIFIER NULL,
    orden INT DEFAULT 0,
    es_menu_sistema BIT DEFAULT 0,
    requiere_autenticacion BIT DEFAULT 1,
    es_visible BIT DEFAULT 1,
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL
);

CREATE TABLE rol_menu_permiso (
    permiso_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,                      -- Siempre el mismo para toda la BD
    rol_id UNIQUEIDENTIFIER NOT NULL,
    menu_id UNIQUEIDENTIFIER NOT NULL,
    puede_ver BIT DEFAULT 1 NOT NULL,
    puede_crear BIT DEFAULT 0,
    puede_editar BIT DEFAULT 0,
    puede_eliminar BIT DEFAULT 0,
    puede_exportar BIT DEFAULT 0,
    puede_imprimir BIT DEFAULT 0,
    permisos_extra NVARCHAR(MAX) NULL,
    fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL
);

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
    uso_count INT DEFAULT 0
);

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
    fecha_evento DATETIME DEFAULT GETDATE() NOT NULL
);
/*
-- ============================================================================
-- TABLAS DE NEGOCIO (EJEMPLO - AJUSTAR SEGÚN MÓDULOS)
-- ============================================================================

-- Módulo Planillas
CREATE TABLE empleado (
    empleado_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    codigo_empleado NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    apellido NVARCHAR(100) NOT NULL,
    dni NVARCHAR(8) NOT NULL,
    fecha_nacimiento DATE NULL,
    fecha_ingreso DATE NULL,
    cargo NVARCHAR(100) NULL,
    departamento NVARCHAR(100) NULL,
    salario_base DECIMAL(10,2) NULL,
    es_activo BIT DEFAULT 1,
    fecha_creacion DATETIME DEFAULT GETDATE(),
    fecha_actualizacion DATETIME NULL
);

CREATE TABLE planilla (
    planilla_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    periodo DATE NOT NULL,
    descripcion NVARCHAR(255) NULL,
    total_ingresos DECIMAL(12,2) DEFAULT 0,
    total_descuentos DECIMAL(12,2) DEFAULT 0,
    total_neto DECIMAL(12,2) DEFAULT 0,
    estado NVARCHAR(20) DEFAULT 'borrador',
    fecha_creacion DATETIME DEFAULT GETDATE(),
    creado_por_usuario_id UNIQUEIDENTIFIER NULL
);

-- Módulo Almacén
CREATE TABLE producto (
    producto_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    codigo_producto NVARCHAR(50) NOT NULL,
    nombre NVARCHAR(200) NOT NULL,
    descripcion NVARCHAR(500) NULL,
    categoria NVARCHAR(100) NULL,
    precio_unitario DECIMAL(10,2) NULL,
    stock_actual INT DEFAULT 0,
    stock_minimo INT DEFAULT 0,
    es_activo BIT DEFAULT 1,
    fecha_creacion DATETIME DEFAULT GETDATE()
);

CREATE TABLE movimiento_inventario (
    movimiento_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    tipo_movimiento NVARCHAR(20) NOT NULL, -- 'entrada', 'salida', 'ajuste'
    cantidad INT NOT NULL,
    fecha_movimiento DATETIME DEFAULT GETDATE(),
    motivo NVARCHAR(255) NULL,
    usuario_id UNIQUEIDENTIFIER NULL
);
*/
-- ============================================================================
-- CONSTRAINTS E ÍNDICES
-- ============================================================================

-- Constraints para usuario
ALTER TABLE usuario 
ADD CONSTRAINT UQ_usuario_cliente_nombre UNIQUE (cliente_id, nombre_usuario);

-- Constraints para rol
ALTER TABLE rol 
ADD CONSTRAINT UQ_rol_cliente_nombre UNIQUE (cliente_id, nombre);

-- Constraints para usuario_rol
ALTER TABLE usuario_rol 
ADD CONSTRAINT FK_usuario_rol_usuario FOREIGN KEY (usuario_id) REFERENCES usuario(usuario_id) ON DELETE CASCADE,
    CONSTRAINT FK_usuario_rol_rol FOREIGN KEY (rol_id) REFERENCES rol(rol_id) ON DELETE CASCADE,
    CONSTRAINT UQ_usuario_rol UNIQUE (usuario_id, rol_id);

-- Constraints para menu
ALTER TABLE menu 
ADD CONSTRAINT FK_menu_area FOREIGN KEY (area_id) REFERENCES area_menu(area_id) ON DELETE SET NULL,
    CONSTRAINT FK_menu_padre FOREIGN KEY (padre_menu_id) REFERENCES menu(menu_id) ON DELETE NO ACTION;

-- Constraints para rol_menu_permiso
ALTER TABLE rol_menu_permiso 
ADD CONSTRAINT FK_permiso_rol FOREIGN KEY (rol_id) REFERENCES rol(rol_id) ON DELETE CASCADE,
    CONSTRAINT FK_permiso_menu FOREIGN KEY (menu_id) REFERENCES menu(menu_id) ON DELETE CASCADE,
    CONSTRAINT UQ_rol_menu UNIQUE (rol_id, menu_id);

-- Constraints para refresh_token
ALTER TABLE refresh_tokens 
ADD CONSTRAINT FK_refresh_token_usuario FOREIGN KEY (usuario_id) REFERENCES usuario(usuario_id) ON DELETE CASCADE;

-- Constraints para auth_audit_log
ALTER TABLE auth_audit_log 
ADD CONSTRAINT FK_audit_usuario FOREIGN KEY (usuario_id) REFERENCES usuario(usuario_id) ON DELETE SET NULL;
/*
-- Constraints para tablas de negocio
ALTER TABLE empleado 
ADD CONSTRAINT UQ_empleado_cliente_codigo UNIQUE (cliente_id, codigo_empleado);

ALTER TABLE producto 
ADD CONSTRAINT UQ_producto_cliente_codigo UNIQUE (cliente_id, codigo_producto);

ALTER TABLE movimiento_inventario 
ADD CONSTRAINT FK_movimiento_producto FOREIGN KEY (producto_id) REFERENCES producto(producto_id);
*/
-- Índices optimizados
CREATE INDEX IDX_usuario_cliente ON usuario(cliente_id, es_activo) WHERE es_eliminado = 0;
CREATE INDEX IDX_rol_cliente ON rol(cliente_id, es_activo);
CREATE INDEX IDX_usuario_rol_usuario ON usuario_rol(usuario_id, es_activo);
CREATE INDEX IDX_menu_cliente ON menu(cliente_id, es_activo, orden);
CREATE INDEX IDX_permiso_rol ON rol_menu_permiso(rol_id, puede_ver);
CREATE INDEX IDX_refresh_token_usuario ON refresh_tokens(usuario_id, is_revoked, expires_at);
CREATE INDEX IDX_audit_cliente_fecha ON auth_audit_log(cliente_id, fecha_evento DESC);
/*
CREATE INDEX IDX_empleado_cliente ON empleado(cliente_id, es_activo);
CREATE INDEX IDX_planilla_cliente ON planilla(cliente_id, periodo);
CREATE INDEX IDX_producto_cliente ON producto(cliente_id, es_activo);
CREATE INDEX IDX_movimiento_cliente ON movimiento_inventario(cliente_id, fecha_movimiento);
*/
PRINT 'Estructura de BD cliente creada exitosamente';
GO


