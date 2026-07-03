-- ============================================================================
-- bootstrap_v2 | official bootstrap line — Dedicated Tenant Store Profile (DTSP)
-- PR-F4-05b — Identity + RBAC + Menú store en Data Plane (sin registry CP)
-- PREREQUISITO: 01_schema/V010__tablas_bd_erp_completo.sql (org_empresa)
-- FUENTE DERIVADA: V020 §2–§3 subset + V030 permiso (sin FK → cliente)
-- ============================================================================

-- ---------------------------------------------------------------------------
-- modulo
-- ---------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'modulo')
BEGIN
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
    PRINT 'Tabla modulo creada en BD dedicada (DTSP).';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_modulo_codigo' AND object_id = OBJECT_ID(N'dbo.modulo'))
    CREATE INDEX IDX_modulo_codigo ON modulo(codigo);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_modulo_activo' AND object_id = OBJECT_ID(N'dbo.modulo'))
    CREATE INDEX IDX_modulo_activo ON modulo(es_activo, orden);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_modulo_categoria' AND object_id = OBJECT_ID(N'dbo.modulo'))
    CREATE INDEX IDX_modulo_categoria ON modulo(categoria, orden);
GO

-- ---------------------------------------------------------------------------
-- modulo_seccion
-- ---------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'modulo_seccion')
BEGIN
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
    PRINT 'Tabla modulo_seccion creada en BD dedicada (DTSP).';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_seccion_modulo' AND object_id = OBJECT_ID(N'dbo.modulo_seccion'))
    CREATE INDEX IDX_seccion_modulo ON modulo_seccion(modulo_id, es_activo, orden);
GO

-- ---------------------------------------------------------------------------
-- modulo_menu (sin FK → cliente — referencia lógica cliente_id)
-- ---------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'modulo_menu')
BEGIN
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
        CONSTRAINT FK_menu_padre FOREIGN KEY (menu_padre_id)
            REFERENCES modulo_menu(menu_id) ON DELETE NO ACTION
    );
    PRINT 'Tabla modulo_menu creada en BD dedicada (DTSP).';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_menu_modulo' AND object_id = OBJECT_ID(N'dbo.modulo_menu'))
    CREATE INDEX IDX_menu_modulo ON modulo_menu(modulo_id, es_activo, orden);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_menu_seccion' AND object_id = OBJECT_ID(N'dbo.modulo_menu'))
    CREATE INDEX IDX_menu_seccion ON modulo_menu(seccion_id, orden);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_menu_padre' AND object_id = OBJECT_ID(N'dbo.modulo_menu'))
    CREATE INDEX IDX_menu_padre ON modulo_menu(menu_padre_id, orden);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_menu_cliente' AND object_id = OBJECT_ID(N'dbo.modulo_menu'))
    CREATE INDEX IDX_menu_cliente ON modulo_menu(cliente_id, es_activo);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_menu_ruta' AND object_id = OBJECT_ID(N'dbo.modulo_menu'))
    CREATE INDEX IDX_menu_ruta ON modulo_menu(ruta) WHERE ruta IS NOT NULL;
GO

-- ---------------------------------------------------------------------------
-- permiso (V030 — catálogo permisos en tenant store dedicated)
-- ---------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'permiso')
BEGIN
    CREATE TABLE permiso (
        permiso_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        codigo NVARCHAR(100) NOT NULL UNIQUE,
        nombre NVARCHAR(150) NOT NULL,
        descripcion NVARCHAR(500) NULL,
        modulo_id UNIQUEIDENTIFIER NULL,
        recurso NVARCHAR(80) NOT NULL,
        accion NVARCHAR(30) NOT NULL,
        es_activo BIT DEFAULT 1 NOT NULL,
        fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
        fecha_actualizacion DATETIME NULL,
        CONSTRAINT FK_permiso_modulo FOREIGN KEY (modulo_id)
            REFERENCES modulo(modulo_id) ON DELETE SET NULL
    );
    PRINT 'Tabla permiso creada en BD dedicada (DTSP).';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'UQ_permiso_codigo' AND object_id = OBJECT_ID(N'dbo.permiso'))
    CREATE UNIQUE INDEX UQ_permiso_codigo ON permiso(codigo);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_permiso_modulo' AND object_id = OBJECT_ID(N'dbo.permiso'))
    CREATE INDEX IDX_permiso_modulo ON permiso(modulo_id);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_permiso_activo' AND object_id = OBJECT_ID(N'dbo.permiso'))
    CREATE INDEX IDX_permiso_activo ON permiso(es_activo);
GO

-- ---------------------------------------------------------------------------
-- rol (sin FK → cliente)
-- ---------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'rol')
BEGIN
    CREATE TABLE rol (
        rol_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        cliente_id UNIQUEIDENTIFIER NULL,
        empresa_id UNIQUEIDENTIFIER NULL,
        codigo_rol NVARCHAR(30) NULL,
        nombre NVARCHAR(50) NOT NULL,
        descripcion NVARCHAR(255) NULL,
        es_rol_sistema BIT DEFAULT 0,
        nivel_acceso INT DEFAULT 1,
        es_activo BIT DEFAULT 1 NOT NULL,
        es_admin_cliente BIT DEFAULT 0 NOT NULL,
        fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
        fecha_actualizacion DATETIME NULL,
        CONSTRAINT FK_rol_empresa FOREIGN KEY (empresa_id)
            REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
        CONSTRAINT UQ_rol_cliente_empresa_nombre UNIQUE (cliente_id, empresa_id, nombre)
    );
    PRINT 'Tabla rol creada en BD dedicada (DTSP).';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_rol_cliente' AND object_id = OBJECT_ID(N'dbo.rol'))
    CREATE INDEX IDX_rol_cliente ON rol(cliente_id, es_activo);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_rol_empresa' AND object_id = OBJECT_ID(N'dbo.rol'))
    CREATE INDEX IDX_rol_empresa ON rol(empresa_id, es_activo) WHERE empresa_id IS NOT NULL;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_rol_codigo' AND object_id = OBJECT_ID(N'dbo.rol'))
    CREATE INDEX IDX_rol_codigo ON rol(codigo_rol) WHERE codigo_rol IS NOT NULL;
GO

-- ---------------------------------------------------------------------------
-- usuario (sin FK → cliente)
-- ---------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'usuario')
BEGIN
    CREATE TABLE usuario (
        usuario_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        cliente_id UNIQUEIDENTIFIER NOT NULL,
        empresa_default_id UNIQUEIDENTIFIER NULL,
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
        CONSTRAINT FK_usuario_empresa_default FOREIGN KEY (empresa_default_id)
            REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
        CONSTRAINT UQ_usuario_cliente_nombre UNIQUE (cliente_id, nombre_usuario)
    );
    PRINT 'Tabla usuario creada en BD dedicada (DTSP).';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_usuario_cliente' AND object_id = OBJECT_ID(N'dbo.usuario'))
    CREATE INDEX IDX_usuario_cliente ON usuario(cliente_id, es_activo) WHERE es_eliminado = 0;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_usuario_correo' AND object_id = OBJECT_ID(N'dbo.usuario'))
    CREATE INDEX IDX_usuario_correo ON usuario(correo) WHERE correo IS NOT NULL;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_usuario_dni' AND object_id = OBJECT_ID(N'dbo.usuario'))
    CREATE INDEX IDX_usuario_dni ON usuario(dni) WHERE dni IS NOT NULL;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_usuario_referencia_externa' AND object_id = OBJECT_ID(N'dbo.usuario'))
    CREATE INDEX IDX_usuario_referencia_externa ON usuario(referencia_externa_id) WHERE referencia_externa_id IS NOT NULL;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_usuario_sincronizacion' AND object_id = OBJECT_ID(N'dbo.usuario'))
    CREATE INDEX IDX_usuario_sincronizacion ON usuario(sincronizado_desde, fecha_ultima_sincronizacion);
GO

-- ---------------------------------------------------------------------------
-- usuario_rol (sin FK → cliente)
-- ---------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'usuario_rol')
BEGIN
    CREATE TABLE usuario_rol (
        usuario_rol_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        usuario_id UNIQUEIDENTIFIER NOT NULL,
        rol_id UNIQUEIDENTIFIER NOT NULL,
        cliente_id UNIQUEIDENTIFIER NOT NULL,
        empresa_id UNIQUEIDENTIFIER NULL,
        es_empresa_default BIT DEFAULT 0 NOT NULL,
        fecha_asignacion DATETIME DEFAULT GETDATE() NOT NULL,
        fecha_expiracion DATETIME NULL,
        es_activo BIT DEFAULT 1 NOT NULL,
        asignado_por_usuario_id UNIQUEIDENTIFIER NULL,
        CONSTRAINT FK_usuario_rol_usuario FOREIGN KEY (usuario_id)
            REFERENCES usuario(usuario_id) ON DELETE CASCADE,
        CONSTRAINT FK_usuario_rol_rol FOREIGN KEY (rol_id)
            REFERENCES rol(rol_id) ON DELETE NO ACTION,
        CONSTRAINT FK_usuario_rol_empresa FOREIGN KEY (empresa_id)
            REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
        CONSTRAINT UQ_usuario_rol_empresa UNIQUE (usuario_id, rol_id, empresa_id)
    );
    PRINT 'Tabla usuario_rol creada en BD dedicada (DTSP).';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_usuario_rol_usuario' AND object_id = OBJECT_ID(N'dbo.usuario_rol'))
    CREATE INDEX IDX_usuario_rol_usuario ON usuario_rol(usuario_id, es_activo);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_usuario_rol_rol' AND object_id = OBJECT_ID(N'dbo.usuario_rol'))
    CREATE INDEX IDX_usuario_rol_rol ON usuario_rol(rol_id, es_activo);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_usuario_rol_cliente' AND object_id = OBJECT_ID(N'dbo.usuario_rol'))
    CREATE INDEX IDX_usuario_rol_cliente ON usuario_rol(cliente_id);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_usuario_rol_empresa' AND object_id = OBJECT_ID(N'dbo.usuario_rol'))
    CREATE INDEX IDX_usuario_rol_empresa ON usuario_rol(empresa_id, es_activo) WHERE empresa_id IS NOT NULL;
GO

-- ---------------------------------------------------------------------------
-- cliente_modulo (sin FK → cliente)
-- ---------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'cliente_modulo')
BEGIN
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
        CONSTRAINT FK_cliente_modulo_modulo FOREIGN KEY (modulo_id)
            REFERENCES modulo(modulo_id) ON DELETE CASCADE,
        CONSTRAINT UQ_cliente_modulo UNIQUE (cliente_id, modulo_id)
    );
    PRINT 'Tabla cliente_modulo creada en BD dedicada (DTSP).';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_cliente_modulo_cliente' AND object_id = OBJECT_ID(N'dbo.cliente_modulo'))
    CREATE INDEX IDX_cliente_modulo_cliente ON cliente_modulo(cliente_id, esta_activo);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_cliente_modulo_vencimiento' AND object_id = OBJECT_ID(N'dbo.cliente_modulo'))
    CREATE INDEX IDX_cliente_modulo_vencimiento ON cliente_modulo(fecha_vencimiento)
        WHERE fecha_vencimiento IS NOT NULL;
GO

-- ---------------------------------------------------------------------------
-- rol_menu_permiso (sin FK → cliente)
-- ---------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'rol_menu_permiso')
BEGIN
    CREATE TABLE rol_menu_permiso (
        permiso_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        cliente_id UNIQUEIDENTIFIER NOT NULL,
        empresa_id UNIQUEIDENTIFIER NULL,
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
        CONSTRAINT FK_permiso_empresa FOREIGN KEY (empresa_id)
            REFERENCES org_empresa(empresa_id) ON DELETE NO ACTION,
        CONSTRAINT UQ_rol_menu_empresa UNIQUE (cliente_id, empresa_id, rol_id, menu_id)
    );
    PRINT 'Tabla rol_menu_permiso creada en BD dedicada (DTSP).';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_permiso_rol' AND object_id = OBJECT_ID(N'dbo.rol_menu_permiso'))
    CREATE INDEX IDX_permiso_rol ON rol_menu_permiso(rol_id, puede_ver);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_permiso_menu' AND object_id = OBJECT_ID(N'dbo.rol_menu_permiso'))
    CREATE INDEX IDX_permiso_menu ON rol_menu_permiso(menu_id);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_permiso_cliente' AND object_id = OBJECT_ID(N'dbo.rol_menu_permiso'))
    CREATE INDEX IDX_permiso_cliente ON rol_menu_permiso(cliente_id);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IDX_permiso_empresa' AND object_id = OBJECT_ID(N'dbo.rol_menu_permiso'))
    CREATE INDEX IDX_permiso_empresa ON rol_menu_permiso(empresa_id) WHERE empresa_id IS NOT NULL;
GO

PRINT 'DTSP V020 tenant identity rbac store completado.';
GO
