-- ============================================================================
-- SCRIPT: 04_seed_bd_central_hibrido.sql
-- DESCRIPCIÓN: Seed para BD Central con arquitectura HÍBRIDA
--              2 clientes Multi-DB + 2 clientes Single-DB
-- USO: Ejecutar en bd_sistema después de crear la estructura central
-- NOTA: Este script usa UNIQUEIDENTIFIER (UUID) para todas las Primary Keys
-- ============================================================================

PRINT '============================================';
PRINT '   SEED BD CENTRAL - ARQUITECTURA HÍBRIDA';
PRINT '   (2 Multi-DB + 2 Single-DB)';
PRINT '============================================';
PRINT '';

-- ============================================================================
-- VARIABLES GLOBALES
-- ============================================================================
DECLARE @ClienteSystemID UNIQUEIDENTIFIER;
DECLARE @ClienteAcmeID UNIQUEIDENTIFIER;          -- Multi-DB
DECLARE @ClienteInnovaID UNIQUEIDENTIFIER;        -- Multi-DB  
DECLARE @ClienteTechCorpID UNIQUEIDENTIFIER;      -- Single-DB
DECLARE @ClienteGlobalID UNIQUEIDENTIFIER;        -- Single-DB

DECLARE @RolSuperAdminID UNIQUEIDENTIFIER;
DECLARE @RolAdminID UNIQUEIDENTIFIER;
DECLARE @RolSupervisorID UNIQUEIDENTIFIER;
DECLARE @RolUserID UNIQUEIDENTIFIER;

DECLARE @UsuarioSuperAdminID UNIQUEIDENTIFIER;

DECLARE @ModuloPlanillasID UNIQUEIDENTIFIER;
DECLARE @ModuloLogisticaID UNIQUEIDENTIFIER;
DECLARE @ModuloAlmacenID UNIQUEIDENTIFIER;
DECLARE @ModuloFacturacionID UNIQUEIDENTIFIER;

-- Hash bcrypt para 'Admin@2025'
DECLARE @HashedPassword NVARCHAR(255) = '$2b$12$CJrVD8JhQlIeZZyp64CZCubM1.vBF2V0ZyRJg2C3bcS7A8/mhi5xm';

-- ============================================================================
-- FASE 1: CLIENTES (HÍBRIDO - MULTI-DB + SINGLE-DB)
-- ============================================================================
PRINT 'FASE 1: Creando clientes en arquitectura híbrida...';

-- CLIENTE SYSTEM (Super Admin - Siempre en BD Central)
SET @ClienteSystemID = NEWID();
INSERT INTO cliente (
    cliente_id, codigo_cliente, subdominio, razon_social, nombre_comercial, ruc,
    tipo_instalacion, modo_autenticacion, logo_url, color_primario, color_secundario,
    plan_suscripcion, estado_suscripcion, fecha_inicio_suscripcion,
    contacto_nombre, contacto_email, contacto_telefono,
    es_activo, es_demo, fecha_creacion, metadata_json
)
VALUES (
    @ClienteSystemID, 'SYSTEM', 'admin', 'SYSTEM ADMINISTRATION', 'System Admin', NULL,
    'cloud', 'local', '/static/logos/system-logo.png', '#1976D2', '#424242',
    'enterprise', 'activo', GETDATE(),
    'System Administrator', 'admin@sistema.local', '+51 999 999 999',
    1, 0, GETDATE(),
    '{"system_version": "2.0.0", "is_superadmin": true, "architecture": "hybrid", "multi_db_clients": 2, "single_db_clients": 2}'
);
PRINT '  ✓ Cliente SYSTEM: ' + CAST(@ClienteSystemID AS NVARCHAR(36));

-- ============================================================================
-- CLIENTES MULTI-DATABASE (BD Separada)
-- ============================================================================

-- CLIENTE ACME (Multi-Database - BD separada)
SET @ClienteAcmeID = NEWID();
INSERT INTO cliente (
    cliente_id, codigo_cliente, subdominio, razon_social, nombre_comercial, ruc,
    tipo_instalacion, modo_autenticacion, logo_url, color_primario, color_secundario,
    plan_suscripcion, estado_suscripcion, fecha_inicio_suscripcion,
    contacto_nombre, contacto_email, contacto_telefono,
    es_activo, es_demo, fecha_creacion, metadata_json
)
VALUES (
    @ClienteAcmeID, 'ACME001', 'acme', 'ACME Corporation S.A.C.', 'ACME Corp', '20123456789',
    'cloud', 'local', '/static/logos/acme-logo.png', '#FF6B6B', '#4ECDC4',
    'profesional', 'activo', GETDATE(),
    'Juan Carlos Acme', 'juan.acme@empresa.com', '+51 987 654 321',
    1, 0, GETDATE(),
    '{"industry": "manufacturing", "employees": 150, "database": "bd_cliente_acme", "database_isolation": true, "architecture": "multi_db", "modules": ["PLANILLAS", "ALMACEN"]}'
);
PRINT '  ✓ Cliente ACME (Multi-DB): ' + CAST(@ClienteAcmeID AS NVARCHAR(36)) + ' → bd_cliente_acme';

-- CLIENTE INNOVA (Multi-Database - BD separada)
SET @ClienteInnovaID = NEWID();
INSERT INTO cliente (
    cliente_id, codigo_cliente, subdominio, razon_social, nombre_comercial, ruc,
    tipo_instalacion, modo_autenticacion, logo_url, color_primario, color_secundario,
    plan_suscripcion, estado_suscripcion, fecha_inicio_suscripcion,
    contacto_nombre, contacto_email, contacto_telefono,
    es_activo, es_demo, fecha_creacion, metadata_json
)
VALUES (
    @ClienteInnovaID, 'INNOVA002', 'innova', 'Innova Solutions E.I.R.L.', 'Innova Tech', '20234567890',
    'cloud', 'local', '/static/logos/innova-logo.png', '#9C27B0', '#00BCD4',
    'basico', 'activo', GETDATE(),
    'Maria Innovadora', 'maria.innova@tech.com', '+51 987 123 456',
    1, 0, GETDATE(),
    '{"industry": "technology", "employees": 50, "database": "bd_cliente_innova", "database_isolation": true, "architecture": "multi_db", "modules": ["PLANILLAS"]}'
);
PRINT '  ✓ Cliente INNOVA (Multi-DB): ' + CAST(@ClienteInnovaID AS NVARCHAR(36)) + ' → bd_cliente_innova';

-- ============================================================================
-- CLIENTES SINGLE-DATABASE (Misma BD Central)
-- ============================================================================

-- CLIENTE TECH CORP (Single-Database - BD Central)
SET @ClienteTechCorpID = NEWID();
INSERT INTO cliente (
    cliente_id, codigo_cliente, subdominio, razon_social, nombre_comercial, ruc,
    tipo_instalacion, modo_autenticacion, logo_url, color_primario, color_secundario,
    plan_suscripcion, estado_suscripcion, fecha_inicio_suscripcion,
    contacto_nombre, contacto_email, contacto_telefono,
    es_activo, es_demo, fecha_creacion, metadata_json
)
VALUES (
    @ClienteTechCorpID, 'TECH003', 'techcorp', 'Technology Corp S.A.', 'Tech Corp', '20345678901',
    'cloud', 'local', '/static/logos/techcorp-logo.png', '#4CAF50', '#FFC107',
    'profesional', 'activo', GETDATE(),
    'Roberto Tecnología', 'roberto.tech@corp.com', '+51 987 333 333',
    1, 0, GETDATE(),
    '{"industry": "software", "employees": 75, "database": "bd_sistema", "database_isolation": false, "architecture": "single_db", "modules": ["PLANILLAS", "FACTURACION"]}'
);
PRINT '  ✓ Cliente TECH CORP (Single-DB): ' + CAST(@ClienteTechCorpID AS NVARCHAR(36)) + ' → bd_sistema';

-- CLIENTE GLOBAL SOLUTIONS (Single-Database - BD Central)
SET @ClienteGlobalID = NEWID();
INSERT INTO cliente (
    cliente_id, codigo_cliente, subdominio, razon_social, nombre_comercial, ruc,
    tipo_instalacion, modo_autenticacion, logo_url, color_primario, color_secundario,
    plan_suscripcion, estado_suscripcion, fecha_inicio_suscripcion,
    contacto_nombre, contacto_email, contacto_telefono,
    es_activo, es_demo, fecha_creacion, metadata_json
)
VALUES (
    @ClienteGlobalID, 'GLOBAL004', 'global', 'Global Solutions E.I.R.L.', 'Global Solutions', '20456789012',
    'cloud', 'local', '/static/logos/global-logo.png', '#2196F3', '#FF5722',
    'basico', 'activo', GETDATE(),
    'Laura Global', 'laura.global@solutions.com', '+51 987 444 444',
    1, 0, GETDATE(),
    '{"industry": "consulting", "employees": 30, "database": "bd_sistema", "database_isolation": false, "architecture": "single_db", "modules": ["PLANILLAS"]}'
);
PRINT '  ✓ Cliente GLOBAL (Single-DB): ' + CAST(@ClienteGlobalID AS NVARCHAR(36)) + ' → bd_sistema';

-- ============================================================================
-- FASE 2: CONFIGURACIÓN DE AUTENTICACIÓN
-- ============================================================================
PRINT 'FASE 2: Configurando políticas de autenticación...';

INSERT INTO cliente_auth_config (
    config_id, cliente_id, password_min_length, password_require_uppercase,
    password_require_lowercase, password_require_number, password_require_special,
    password_expiry_days, password_history_count, max_login_attempts,
    lockout_duration_minutes, max_active_sessions, session_idle_timeout_minutes,
    access_token_minutes, refresh_token_days, allow_remember_me,
    remember_me_days, require_email_verification, allow_password_reset,
    enable_2fa, require_2fa_for_admins, metodos_2fa_permitidos,
    fecha_creacion
)
VALUES 
    (NEWID(), @ClienteSystemID, 10, 1, 1, 1, 1, 90, 5, 3, 30, 5, 120, 15, 7, 1, 30, 1, 1, 1, 1, 'email,totp', GETDATE()),
    (NEWID(), @ClienteAcmeID, 8, 1, 1, 1, 1, 180, 3, 5, 15, 3, 60, 30, 14, 1, 30, 0, 1, 0, 0, 'email', GETDATE()),
    (NEWID(), @ClienteInnovaID, 8, 1, 1, 1, 0, 180, 3, 5, 15, 3, 60, 30, 14, 1, 30, 0, 1, 0, 0, 'email', GETDATE()),
    (NEWID(), @ClienteTechCorpID, 8, 1, 1, 1, 1, 180, 3, 5, 15, 3, 60, 30, 14, 1, 30, 0, 1, 0, 0, 'email', GETDATE()),
    (NEWID(), @ClienteGlobalID, 8, 1, 1, 1, 0, 180, 3, 5, 15, 3, 60, 30, 14, 1, 30, 0, 1, 0, 0, 'email', GETDATE());

PRINT '  ✓ Configuraciones de autenticación creadas para 5 clientes';

-- ============================================================================
-- FASE 3: ROLES GLOBALES DEL SISTEMA
-- ============================================================================
PRINT 'FASE 3: Creando roles globales del sistema...';

SET @RolSuperAdminID = NEWID();
SET @RolAdminID = NEWID();
SET @RolSupervisorID = NEWID();
SET @RolUserID = NEWID();

INSERT INTO rol (rol_id, cliente_id, codigo_rol, nombre, descripcion, es_rol_sistema, nivel_acceso, es_activo, fecha_creacion)
VALUES 
    (@RolSuperAdminID, NULL, 'SUPER_ADMIN', 'Super Administrador', 'Acceso completo al sistema multi-tenant. Nivel LBAC 5.', 1, 5, 1, GETDATE()),
    (@RolAdminID, NULL, 'ADMIN', 'Administrador', 'Administrador de cliente. Nivel LBAC 4.', 1, 4, 1, GETDATE()),
    (@RolSupervisorID, NULL, 'SUPERVISOR', 'Supervisor', 'Supervisor con gestión de equipos. Nivel LBAC 3.', 1, 3, 1, GETDATE()),
    (@RolUserID, NULL, 'USER', 'Usuario', 'Usuario estándar. Nivel LBAC 1.', 1, 1, 1, GETDATE());

PRINT '  ✓ Roles globales creados: SUPER_ADMIN(5), ADMIN(4), SUPERVISOR(3), USER(1)';

-- ============================================================================
-- FASE 4: USUARIO SUPER ADMIN (SOLO EN BD CENTRAL)
-- ============================================================================
PRINT 'FASE 4: Creando usuario super admin...';

SET @UsuarioSuperAdminID = NEWID();
INSERT INTO usuario (
    usuario_id, cliente_id, nombre_usuario, contrasena, nombre, apellido, correo,
    dni, telefono, proveedor_autenticacion, es_activo, correo_confirmado,
    requiere_cambio_contrasena, intentos_fallidos, fecha_ultimo_cambio_contrasena,
    fecha_creacion
)
VALUES (
    @UsuarioSuperAdminID, @ClienteSystemID, 'superadmin', @HashedPassword, 'System', 'Administrator',
    'admin@sistema.local', NULL, '+51 999 999 999', 'local', 1, 1, 0, 0,
    GETDATE(), GETDATE()
);

INSERT INTO usuario_rol (usuario_rol_id, usuario_id, rol_id, cliente_id, fecha_asignacion, es_activo)
VALUES (NEWID(), @UsuarioSuperAdminID, @RolSuperAdminID, @ClienteSystemID, GETDATE(), 1);

PRINT '  ✓ Usuario superadmin creado: ' + CAST(@UsuarioSuperAdminID AS NVARCHAR(36));

-- ============================================================================
-- FASE 5: USUARIOS PARA CLIENTES SINGLE-DB (EN BD CENTRAL)
-- ============================================================================
PRINT 'FASE 5: Creando usuarios para clientes Single-DB...';

-- Usuarios para TECH CORP (Single-DB)
INSERT INTO usuario (
    usuario_id, cliente_id, nombre_usuario, contrasena, nombre, apellido, correo,
    dni, telefono, proveedor_autenticacion, es_activo, correo_confirmado,
    fecha_creacion
)
VALUES 
    (NEWID(), @ClienteTechCorpID, 'admin_tech', @HashedPassword, 'Roberto', 'Tecnología', 'roberto.tech@corp.com', '11223344', '+51 987 555 555', 'local', 1, 1, GETDATE()),
    (NEWID(), @ClienteTechCorpID, 'user_tech', @HashedPassword, 'Carmen', 'Digital', 'carmen.digital@corp.com', '22334455', '+51 987 666 666', 'local', 1, 1, GETDATE());

-- Usuarios para GLOBAL SOLUTIONS (Single-DB)
INSERT INTO usuario (
    usuario_id, cliente_id, nombre_usuario, contrasena, nombre, apellido, correo,
    dni, telefono, proveedor_autenticacion, es_activo, correo_confirmado,
    fecha_creacion
)
VALUES 
    (NEWID(), @ClienteGlobalID, 'admin_global', @HashedPassword, 'Laura', 'Global', 'laura.global@solutions.com', '33445566', '+51 987 777 777', 'local', 1, 1, GETDATE()),
    (NEWID(), @ClienteGlobalID, 'user_global', @HashedPassword, 'Pedro', 'Mundial', 'pedro.mundial@solutions.com', '44556677', '+51 987 888 888', 'local', 1, 1, GETDATE());

PRINT '  ✓ 4 usuarios creados para clientes Single-DB';

-- ============================================================================
-- FASE 6: ASIGNAR ROLES A USUARIOS SINGLE-DB
-- ============================================================================
PRINT 'FASE 6: Asignando roles a usuarios Single-DB...';

-- TECH CORP
INSERT INTO usuario_rol (usuario_rol_id, usuario_id, rol_id, cliente_id, fecha_asignacion, es_activo)
SELECT NEWID(), u.usuario_id, @RolAdminID, @ClienteTechCorpID, GETDATE(), 1
FROM usuario u WHERE u.cliente_id = @ClienteTechCorpID AND u.nombre_usuario = 'admin_tech';

INSERT INTO usuario_rol (usuario_rol_id, usuario_id, rol_id, cliente_id, fecha_asignacion, es_activo)
SELECT NEWID(), u.usuario_id, @RolUserID, @ClienteTechCorpID, GETDATE(), 1
FROM usuario u WHERE u.cliente_id = @ClienteTechCorpID AND u.nombre_usuario = 'user_tech';

-- GLOBAL SOLUTIONS
INSERT INTO usuario_rol (usuario_rol_id, usuario_id, rol_id, cliente_id, fecha_asignacion, es_activo)
SELECT NEWID(), u.usuario_id, @RolAdminID, @ClienteGlobalID, GETDATE(), 1
FROM usuario u WHERE u.cliente_id = @ClienteGlobalID AND u.nombre_usuario = 'admin_global';

INSERT INTO usuario_rol (usuario_rol_id, usuario_id, rol_id, cliente_id, fecha_asignacion, es_activo)
SELECT NEWID(), u.usuario_id, @RolUserID, @ClienteGlobalID, GETDATE(), 1
FROM usuario u WHERE u.cliente_id = @ClienteGlobalID AND u.nombre_usuario = 'user_global';

PRINT '  ✓ Roles asignados a usuarios Single-DB';

-- ============================================================================
-- FASE 7: MÓDULOS DEL SISTEMA
-- ============================================================================
PRINT 'FASE 7: Creando catálogo de módulos...';

SET @ModuloPlanillasID = NEWID();
SET @ModuloLogisticaID = NEWID();
SET @ModuloAlmacenID = NEWID();
SET @ModuloFacturacionID = NEWID();

INSERT INTO cliente_modulo (modulo_id, codigo_modulo, nombre, descripcion, icono, es_modulo_core, requiere_licencia, orden, es_activo, fecha_creacion)
VALUES 
    (@ModuloPlanillasID, 'PLANILLAS', 'Planillas y RRHH', 'Gestión completa de planillas, nóminas y recursos humanos', 'receipt_long', 1, 0, 1, 1, GETDATE()),
    (@ModuloLogisticaID, 'LOGISTICA', 'Logística', 'Gestión de logística, transporte y distribución', 'local_shipping', 0, 1, 2, 1, GETDATE()),
    (@ModuloAlmacenID, 'ALMACEN', 'Almacén e Inventarios', 'Control de almacenes, inventarios y stock', 'inventory_2', 0, 1, 3, 1, GETDATE()),
    (@ModuloFacturacionID, 'FACTURACION', 'Facturación', 'Facturación electrónica y comprobantes de pago', 'receipt', 0, 1, 4, 1, GETDATE());

PRINT '  ✓ Módulos creados: PLANILLAS, LOGÍSTICA, ALMACÉN, FACTURACIÓN';

-- ============================================================================
-- FASE 8: ACTIVAR MÓDULOS PARA CLIENTES
-- ============================================================================
PRINT 'FASE 8: Activando módulos por cliente...';

-- SYSTEM: Todos los módulos
INSERT INTO cliente_modulo_activo (cliente_modulo_activo_id, cliente_id, modulo_id, esta_activo, fecha_activacion, configuracion_json)
SELECT NEWID(), @ClienteSystemID, modulo_id, 1, GETDATE(), '{"full_access": true}'
FROM cliente_modulo;

-- ACME (Multi-DB): Planillas y Almacén
INSERT INTO cliente_modulo_activo (cliente_modulo_activo_id, cliente_id, modulo_id, esta_activo, fecha_activacion, configuracion_json, limite_usuarios, limite_registros)
VALUES 
    (NEWID(), @ClienteAcmeID, @ModuloPlanillasID, 1, GETDATE(), '{"plan": "profesional", "empleados_max": 200}', 25, 5000),
    (NEWID(), @ClienteAcmeID, @ModuloAlmacenID, 1, GETDATE(), '{"plan": "profesional", "productos_max": 1000}', 10, 10000);

-- INNOVA (Multi-DB): Solo Planillas
INSERT INTO cliente_modulo_activo (cliente_modulo_activo_id, cliente_id, modulo_id, esta_activo, fecha_activacion, configuracion_json, limite_usuarios, limite_registros)
VALUES 
    (NEWID(), @ClienteInnovaID, @ModuloPlanillasID, 1, GETDATE(), '{"plan": "basico", "empleados_max": 50}', 10, 1000);

-- TECH CORP (Single-DB): Planillas y Facturación
INSERT INTO cliente_modulo_activo (cliente_modulo_activo_id, cliente_id, modulo_id, esta_activo, fecha_activacion, configuracion_json, limite_usuarios, limite_registros)
VALUES 
    (NEWID(), @ClienteTechCorpID, @ModuloPlanillasID, 1, GETDATE(), '{"plan": "profesional", "empleados_max": 100}', 15, 2000),
    (NEWID(), @ClienteTechCorpID, @ModuloFacturacionID, 1, GETDATE(), '{"plan": "profesional", "comprobantes_mensuales": 500}', 8, 5000);

-- GLOBAL SOLUTIONS (Single-DB): Solo Planillas
INSERT INTO cliente_modulo_activo (cliente_modulo_activo_id, cliente_id, modulo_id, esta_activo, fecha_activacion, configuracion_json, limite_usuarios, limite_registros)
VALUES 
    (NEWID(), @ClienteGlobalID, @ModuloPlanillasID, 1, GETDATE(), '{"plan": "basico", "empleados_max": 40}', 8, 800);

PRINT '  ✓ Módulos activados por cliente';

-- ============================================================================
-- FASE 9: CONFIGURACIÓN DE CONEXIONES HÍBRIDAS
-- ============================================================================
PRINT 'FASE 9: Configurando conexiones híbridas...';

-- CONEXIONES MULTI-DB (BD Separada)
-- NOTA: La tabla cliente_conexion reemplaza a cliente_modulo_conexion
-- Se usa una conexión principal por cliente, no por módulo
INSERT INTO cliente_conexion (
    conexion_id, cliente_id, servidor, puerto, nombre_bd,
    usuario_encriptado, password_encriptado, connection_string_encriptado,
    tipo_bd, usa_ssl, timeout_segundos, max_pool_size,
    es_solo_lectura, es_conexion_principal, es_activo,
    fecha_creacion, creado_por_usuario_id
)
VALUES 
    -- ACME (Multi-DB) - Conexión principal
    (NEWID(), @ClienteAcmeID, 'localhost', 1433, 'bd_cliente_acme', 'ENCRYPTED_USER_ACME', 'ENCRYPTED_PASSWORD_ACME', NULL, 'sqlserver', 1, 30, 50, 0, 1, 1, GETDATE(), @UsuarioSuperAdminID),
    -- INNOVA (Multi-DB) - Conexión principal
    (NEWID(), @ClienteInnovaID, 'localhost', 1433, 'bd_cliente_innova', 'ENCRYPTED_USER_INNOVA', 'ENCRYPTED_PASSWORD_INNOVA', NULL, 'sqlserver', 1, 30, 30, 0, 1, 1, GETDATE(), @UsuarioSuperAdminID);

-- CONEXIONES SINGLE-DB (BD Central)
-- Los clientes Single-DB no necesitan conexión separada, usan la BD central
-- Pero podemos crear una entrada para consistencia si se requiere

PRINT '  ✓ Conexiones híbridas configuradas (2 Multi-DB + 2 Single-DB)';
PRINT '  ⚠️  RECORDATORIO: Encriptar credenciales en producción';

/*
-- ============================================================================
-- FASE 10: DATOS DE NEGOCIO PARA CLIENTES SINGLE-DB
-- ============================================================================
PRINT 'FASE 10: Insertando datos de negocio para clientes Single-DB...';

-- Empleados para TECH CORP (Single-DB)
INSERT INTO empleado (empleado_id, cliente_id, codigo_empleado, nombre, apellido, dni, fecha_ingreso, cargo, departamento, salario_base)
VALUES 
    (NEWID(), @ClienteTechCorpID, 'TECH001', 'Ana', 'Programadora', '55667788', '2020-08-12', 'Desarrollador Senior', 'Tecnología', 5200.00),
    (NEWID(), @ClienteTechCorpID, 'TECH002', 'Luis', 'DevOps', '66778899', '2021-11-25', 'Ingeniero DevOps', 'Infraestructura', 4800.00),
    (NEWID(), @ClienteTechCorpID, 'TECH003', 'Sofia', 'Diseñadora', '77889900', '2022-03-18', 'Diseñadora UI/UX', 'Diseño', 3800.00);

-- Empleados para GLOBAL SOLUTIONS (Single-DB)
INSERT INTO empleado (empleado_id, cliente_id, codigo_empleado, nombre, apellido, dni, fecha_ingreso, cargo, departamento, salario_base)
VALUES 
    (NEWID(), @ClienteGlobalID, 'GLOB001', 'Carlos', 'Consultor', '88990011', '2021-05-30', 'Consultor Senior', 'Consultoría', 4500.00),
    (NEWID(), @ClienteGlobalID, 'GLOB002', 'Elena', 'Asesora', '99001122', '2022-09-14', 'Asesora Comercial', 'Ventas', 3200.00);

PRINT '  ✓ 5 empleados creados para clientes Single-DB';
*/
-- ============================================================================
-- FASE 11: ÁREAS Y MENÚS GLOBALES
-- ============================================================================
PRINT 'FASE 11: Creando áreas y menús globales...';

DECLARE @AreaSistemaID UNIQUEIDENTIFIER, @AreaPlanillasID UNIQUEIDENTIFIER, @AreaAlmacenID UNIQUEIDENTIFIER, @AreaFacturacionID UNIQUEIDENTIFIER;

SET @AreaSistemaID = NEWID();
SET @AreaPlanillasID = NEWID();
SET @AreaAlmacenID = NEWID();
SET @AreaFacturacionID = NEWID();

INSERT INTO area_menu (area_id, cliente_id, nombre, descripcion, icono, orden, es_area_sistema, es_activo, fecha_creacion)
VALUES 
    (@AreaSistemaID, NULL, 'Sistema', 'Administración del sistema multi-tenant', 'settings', 1, 1, 1, GETDATE()),
    (@AreaPlanillasID, NULL, 'Planillas', 'Gestión de planillas y RRHH', 'receipt_long', 2, 1, 1, GETDATE()),
    (@AreaAlmacenID, NULL, 'Almacén', 'Control de inventarios', 'inventory_2', 3, 1, 1, GETDATE()),
    (@AreaFacturacionID, NULL, 'Facturación', 'Facturación electrónica', 'receipt', 4, 1, 1, GETDATE());

-- Menús globales
INSERT INTO menu (menu_id, cliente_id, area_id, nombre, descripcion, icono, ruta, orden, es_menu_sistema, requiere_autenticacion, es_visible, es_activo, fecha_creacion)
VALUES 
    (NEWID(), NULL, @AreaSistemaID, 'Gestión de Clientes', 'Administrar clientes multi-tenant', 'business', '/sistema/clientes', 1, 1, 1, 1, 1, GETDATE()),
    (NEWID(), NULL, @AreaPlanillasID, 'Empleados', 'Gestión de empleados', 'people', '/planillas/empleados', 1, 1, 1, 1, 1, GETDATE()),
    (NEWID(), NULL, @AreaPlanillasID, 'Procesar Planilla', 'Procesar planillas de pago', 'calculate', '/planillas/procesar', 2, 1, 1, 1, 1, GETDATE()),
    (NEWID(), NULL, @AreaAlmacenID, 'Productos', 'Gestión de productos', 'inventory', '/almacen/productos', 1, 1, 1, 1, 1, GETDATE()),
    (NEWID(), NULL, @AreaFacturacionID, 'Comprobantes', 'Gestión de comprobantes', 'receipt', '/facturacion/comprobantes', 1, 1, 1, 1, 1, GETDATE());

PRINT '  ✓ Áreas y menús globales creados';

-- ============================================================================
-- FASE 12: PERMISOS PARA USUARIOS SINGLE-DB
-- ============================================================================
PRINT 'FASE 12: Configurando permisos para usuarios Single-DB...';

-- Permisos para admin_tech (TECH CORP)
INSERT INTO rol_menu_permiso (permiso_id, cliente_id, rol_id, menu_id, puede_ver, puede_crear, puede_editar, puede_eliminar, puede_exportar, puede_imprimir, fecha_creacion)
SELECT 
    NEWID(), @ClienteTechCorpID, @RolAdminID, menu_id, 1, 1, 1, 1, 1, 1, GETDATE()
FROM menu 
WHERE es_activo = 1;

-- Permisos para user_tech (TECH CORP)
INSERT INTO rol_menu_permiso (permiso_id, cliente_id, rol_id, menu_id, puede_ver, puede_crear, puede_editar, puede_eliminar, puede_exportar, puede_imprimir, fecha_creacion)
SELECT 
    NEWID(), @ClienteTechCorpID, @RolUserID, menu_id, 1, 0, 0, 0, 1, 0, GETDATE()
FROM menu 
WHERE es_activo = 1 AND area_id IN (@AreaPlanillasID, @AreaFacturacionID);

-- Permisos para admin_global (GLOBAL SOLUTIONS)
INSERT INTO rol_menu_permiso (permiso_id, cliente_id, rol_id, menu_id, puede_ver, puede_crear, puede_editar, puede_eliminar, puede_exportar, puede_imprimir, fecha_creacion)
SELECT 
    NEWID(), @ClienteGlobalID, @RolAdminID, menu_id, 1, 1, 1, 1, 1, 1, GETDATE()
FROM menu 
WHERE es_activo = 1;

-- Permisos para user_global (GLOBAL SOLUTIONS)
INSERT INTO rol_menu_permiso (permiso_id, cliente_id, rol_id, menu_id, puede_ver, puede_crear, puede_editar, puede_eliminar, puede_exportar, puede_imprimir, fecha_creacion)
SELECT 
    NEWID(), @ClienteGlobalID, @RolUserID, menu_id, 1, 0, 0, 0, 1, 0, GETDATE()
FROM menu 
WHERE es_activo = 1 AND area_id = @AreaPlanillasID;

PRINT '  ✓ Permisos configurados para usuarios Single-DB';

-- ============================================================================
-- FASE 13: AUDITORÍA INICIAL
-- ============================================================================
PRINT 'FASE 13: Registrando auditoría inicial...';

INSERT INTO auth_audit_log (
    log_id, cliente_id, usuario_id, evento, nombre_usuario_intento, descripcion,
    exito, ip_address, user_agent, metadata_json, fecha_evento
)
VALUES (
    NEWID(), @ClienteSystemID, @UsuarioSuperAdminID, 'system_initialization', 'superadmin',
    'Sistema multi-tenant inicializado en arquitectura híbrida (2 Multi-DB + 2 Single-DB)',
    1, '127.0.0.1', 'Seed Script', 
    '{"version": "2.0.0", "architecture": "hybrid", "multi_db_clients": 2, "single_db_clients": 2, "total_clients": 5}',
    GETDATE()
);

PRINT '  ✓ Auditoría inicial registrada';

-- ============================================================================
-- RESUMEN FINAL
-- ============================================================================
PRINT '';
PRINT '============================================';
PRINT '   SEED BD CENTRAL HÍBRIDO - COMPLETADO';
PRINT '============================================';
PRINT '';
PRINT '🏗️  ARQUITECTURA HÍBRIDA IMPLEMENTADA:';
PRINT '--------------------------------------';
PRINT '🔷 CLIENTES MULTI-DATABASE (BD Separada):';
PRINT '   • ACME Corp (ID: ' + CAST(@ClienteAcmeID AS NVARCHAR(36)) + ') → bd_cliente_acme';
PRINT '   • Innova Tech (ID: ' + CAST(@ClienteInnovaID AS NVARCHAR(36)) + ') → bd_cliente_innova';
PRINT '';
PRINT '🔶 CLIENTES SINGLE-DATABASE (BD Central):';
PRINT '   • Tech Corp (ID: ' + CAST(@ClienteTechCorpID AS NVARCHAR(36)) + ') → bd_sistema';
PRINT '   • Global Solutions (ID: ' + CAST(@ClienteGlobalID AS NVARCHAR(36)) + ') → bd_sistema';
PRINT '';
PRINT '👥 USUARIOS CREADOS:';
PRINT '-------------------';
PRINT '✅ BD Central:';
PRINT '   - superadmin (SYSTEM)';
PRINT '   - admin_tech + user_tech (TECH CORP)';
PRINT '   - admin_global + user_global (GLOBAL SOLUTIONS)';
PRINT '';
PRINT '✅ BD Clientes (por ejecutar 03_seed_bd_clientes.sql):';
PRINT '   - admin_acme + supervisor_acme + usuario_acme (ACME)';
PRINT '   - admin_innova + supervisor_innova + usuario_innova (INNOVA)';
PRINT '';
PRINT '🔐 CREDENCIALES TEMPORALES:';
PRINT '   - Todos los usuarios: Admin@2025';
PRINT '';
PRINT '📊 MÓDULOS ACTIVADOS:';
PRINT '   • ACME: Planillas, Almacén';
PRINT '   • INNOVA: Planillas';
PRINT '   • TECH CORP: Planillas, Facturación';
PRINT '   • GLOBAL: Planillas';
PRINT '';
PRINT '📝 PRÓXIMOS PASOS:';
PRINT '   1. BD Clientes Multi-DB ya deben estar creadas';
PRINT '   2. Ejecutar 03_seed_bd_clientes_UUID.sql en bd_cliente_acme (usar @ClienteCodigo = ''ACME001'')';
PRINT '   3. Ejecutar 03_seed_bd_clientes_UUID.sql en bd_cliente_innova (usar @ClienteCodigo = ''INNOVA002'')';
PRINT '   4. Sistema listo para operar en modo híbrido';
PRINT '';
PRINT 'Script finalizado: ' + CONVERT(NVARCHAR, GETDATE(), 120);
GO


