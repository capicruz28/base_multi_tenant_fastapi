-- ============================================================================
-- SCRIPT: 04_seed_bd_central_hibrido.sql
-- DESCRIPCIÓN: Seed para BD Central con arquitectura HÍBRIDA
--              2 clientes Multi-DB + 2 clientes Single-DB
-- USO: Ejecutar en bd_sistema después de crear la estructura central
-- ============================================================================

PRINT '============================================';
PRINT '   SEED BD CENTRAL - ARQUITECTURA HÍBRIDA';
PRINT '   (2 Multi-DB + 2 Single-DB)';
PRINT '============================================';
PRINT '';

-- ============================================================================
-- VARIABLES GLOBALES
-- ============================================================================
DECLARE @ClienteSystemID INT;
DECLARE @ClienteAcmeID INT;          -- Multi-DB
DECLARE @ClienteInnovaID INT;        -- Multi-DB  
DECLARE @ClienteTechCorpID INT;      -- Single-DB
DECLARE @ClienteGlobalID INT;        -- Single-DB

DECLARE @RolSuperAdminID INT;
DECLARE @RolAdminID INT;
DECLARE @RolSupervisorID INT;
DECLARE @RolUserID INT;

DECLARE @UsuarioSuperAdminID INT;

DECLARE @ModuloPlanillasID INT;
DECLARE @ModuloLogisticaID INT;
DECLARE @ModuloAlmacenID INT;
DECLARE @ModuloFacturacionID INT;

-- Hash bcrypt para 'Admin@2025'
DECLARE @HashedPassword NVARCHAR(255) = '$2b$12$CJrVD8JhQlIeZZyp64CZCubM1.vBF2V0ZyRJg2C3bcS7A8/mhi5xm';

-- ============================================================================
-- FASE 1: CLIENTES (HÍBRIDO - MULTI-DB + SINGLE-DB)
-- ============================================================================
PRINT 'FASE 1: Creando clientes en arquitectura híbrida...';

-- CLIENTE SYSTEM (Super Admin - Siempre en BD Central)
INSERT INTO cliente (
    codigo_cliente, subdominio, razon_social, nombre_comercial, ruc,
    tipo_instalacion, modo_autenticacion, logo_url, color_primario, color_secundario,
    plan_suscripcion, estado_suscripcion, fecha_inicio_suscripcion,
    contacto_nombre, contacto_email, contacto_telefono,
    es_activo, es_demo, fecha_creacion, metadata_json
)
VALUES (
    'SYSTEM', 'admin', 'SYSTEM ADMINISTRATION', 'System Admin', NULL,
    'cloud', 'local', '/static/logos/system-logo.png', '#1976D2', '#424242',
    'enterprise', 'activo', GETDATE(),
    'System Administrator', 'admin@sistema.local', '+51 999 999 999',
    1, 0, GETDATE(),
    '{"system_version": "2.0.0", "is_superadmin": true, "architecture": "hybrid", "multi_db_clients": 2, "single_db_clients": 2}'
);
SET @ClienteSystemID = SCOPE_IDENTITY();
PRINT '  ✓ Cliente SYSTEM: ' + CAST(@ClienteSystemID AS NVARCHAR);

-- ============================================================================
-- CLIENTES MULTI-DATABASE (BD Separada)
-- ============================================================================

-- CLIENTE ACME (Multi-Database - BD separada)
INSERT INTO cliente (
    codigo_cliente, subdominio, razon_social, nombre_comercial, ruc,
    tipo_instalacion, modo_autenticacion, logo_url, color_primario, color_secundario,
    plan_suscripcion, estado_suscripcion, fecha_inicio_suscripcion,
    contacto_nombre, contacto_email, contacto_telefono,
    es_activo, es_demo, fecha_creacion, metadata_json
)
VALUES (
    'ACME001', 'acme', 'ACME Corporation S.A.C.', 'ACME Corp', '20123456789',
    'cloud', 'local', '/static/logos/acme-logo.png', '#FF6B6B', '#4ECDC4',
    'profesional', 'activo', GETDATE(),
    'Juan Carlos Acme', 'juan.acme@empresa.com', '+51 987 654 321',
    1, 0, GETDATE(),
    '{"industry": "manufacturing", "employees": 150, "database": "bd_cliente_acme", "database_isolation": true, "architecture": "multi_db", "modules": ["PLANILLAS", "ALMACEN"]}'
);
SET @ClienteAcmeID = SCOPE_IDENTITY();
PRINT '  ✓ Cliente ACME (Multi-DB): ' + CAST(@ClienteAcmeID AS NVARCHAR) + ' → bd_cliente_acme';

-- CLIENTE INNOVA (Multi-Database - BD separada)
INSERT INTO cliente (
    codigo_cliente, subdominio, razon_social, nombre_comercial, ruc,
    tipo_instalacion, modo_autenticacion, logo_url, color_primario, color_secundario,
    plan_suscripcion, estado_suscripcion, fecha_inicio_suscripcion,
    contacto_nombre, contacto_email, contacto_telefono,
    es_activo, es_demo, fecha_creacion, metadata_json
)
VALUES (
    'INNOVA002', 'innova', 'Innova Solutions E.I.R.L.', 'Innova Tech', '20234567890',
    'cloud', 'local', '/static/logos/innova-logo.png', '#9C27B0', '#00BCD4',
    'basico', 'activo', GETDATE(),
    'Maria Innovadora', 'maria.innova@tech.com', '+51 987 123 456',
    1, 0, GETDATE(),
    '{"industry": "technology", "employees": 50, "database": "bd_cliente_innova", "database_isolation": true, "architecture": "multi_db", "modules": ["PLANILLAS"]}'
);
SET @ClienteInnovaID = SCOPE_IDENTITY();
PRINT '  ✓ Cliente INNOVA (Multi-DB): ' + CAST(@ClienteInnovaID AS NVARCHAR) + ' → bd_cliente_innova';

-- ============================================================================
-- CLIENTES SINGLE-DATABASE (Misma BD Central)
-- ============================================================================

-- CLIENTE TECH CORP (Single-Database - BD Central)
INSERT INTO cliente (
    codigo_cliente, subdominio, razon_social, nombre_comercial, ruc,
    tipo_instalacion, modo_autenticacion, logo_url, color_primario, color_secundario,
    plan_suscripcion, estado_suscripcion, fecha_inicio_suscripcion,
    contacto_nombre, contacto_email, contacto_telefono,
    es_activo, es_demo, fecha_creacion, metadata_json
)
VALUES (
    'TECH003', 'techcorp', 'Technology Corp S.A.', 'Tech Corp', '20345678901',
    'cloud', 'local', '/static/logos/techcorp-logo.png', '#4CAF50', '#FFC107',
    'profesional', 'activo', GETDATE(),
    'Roberto Tecnología', 'roberto.tech@corp.com', '+51 987 333 333',
    1, 0, GETDATE(),
    '{"industry": "software", "employees": 75, "database": "bd_sistema", "database_isolation": false, "architecture": "single_db", "modules": ["PLANILLAS", "FACTURACION"]}'
);
SET @ClienteTechCorpID = SCOPE_IDENTITY();
PRINT '  ✓ Cliente TECH CORP (Single-DB): ' + CAST(@ClienteTechCorpID AS NVARCHAR) + ' → bd_sistema';

-- CLIENTE GLOBAL SOLUTIONS (Single-Database - BD Central)
INSERT INTO cliente (
    codigo_cliente, subdominio, razon_social, nombre_comercial, ruc,
    tipo_instalacion, modo_autenticacion, logo_url, color_primario, color_secundario,
    plan_suscripcion, estado_suscripcion, fecha_inicio_suscripcion,
    contacto_nombre, contacto_email, contacto_telefono,
    es_activo, es_demo, fecha_creacion, metadata_json
)
VALUES (
    'GLOBAL004', 'global', 'Global Solutions E.I.R.L.', 'Global Solutions', '20456789012',
    'cloud', 'local', '/static/logos/global-logo.png', '#2196F3', '#FF5722',
    'basico', 'activo', GETDATE(),
    'Laura Global', 'laura.global@solutions.com', '+51 987 444 444',
    1, 0, GETDATE(),
    '{"industry": "consulting", "employees": 30, "database": "bd_sistema", "database_isolation": false, "architecture": "single_db", "modules": ["PLANILLAS"]}'
);
SET @ClienteGlobalID = SCOPE_IDENTITY();
PRINT '  ✓ Cliente GLOBAL (Single-DB): ' + CAST(@ClienteGlobalID AS NVARCHAR) + ' → bd_sistema';

-- ============================================================================
-- FASE 2: CONFIGURACIÓN DE AUTENTICACIÓN
-- ============================================================================
PRINT 'FASE 2: Configurando políticas de autenticación...';

INSERT INTO cliente_auth_config (
    cliente_id, password_min_length, password_require_uppercase,
    password_require_lowercase, password_require_number, password_require_special,
    password_expiry_days, password_history_count, max_login_attempts,
    lockout_duration_minutes, max_active_sessions, session_idle_timeout_minutes,
    access_token_minutes, refresh_token_days, allow_remember_me,
    remember_me_days, require_email_verification, allow_password_reset,
    enable_2fa, require_2fa_for_admins, metodos_2fa_permitidos,
    fecha_creacion
)
VALUES 
    (@ClienteSystemID, 10, 1, 1, 1, 1, 90, 5, 3, 30, 5, 120, 15, 7, 1, 30, 1, 1, 1, 1, 'email,totp', GETDATE()),
    (@ClienteAcmeID, 8, 1, 1, 1, 1, 180, 3, 5, 15, 3, 60, 30, 14, 1, 30, 0, 1, 0, 0, 'email', GETDATE()),
    (@ClienteInnovaID, 8, 1, 1, 1, 0, 180, 3, 5, 15, 3, 60, 30, 14, 1, 30, 0, 1, 0, 0, 'email', GETDATE()),
    (@ClienteTechCorpID, 8, 1, 1, 1, 1, 180, 3, 5, 15, 3, 60, 30, 14, 1, 30, 0, 1, 0, 0, 'email', GETDATE()),
    (@ClienteGlobalID, 8, 1, 1, 1, 0, 180, 3, 5, 15, 3, 60, 30, 14, 1, 30, 0, 1, 0, 0, 'email', GETDATE());

PRINT '  ✓ Configuraciones de autenticación creadas para 5 clientes';

-- ============================================================================
-- FASE 3: ROLES GLOBALES DEL SISTEMA
-- ============================================================================
PRINT 'FASE 3: Creando roles globales del sistema...';

INSERT INTO rol (cliente_id, codigo_rol, nombre, descripcion, es_rol_sistema, nivel_acceso, es_activo, fecha_creacion)
VALUES 
    (NULL, 'SUPER_ADMIN', 'Super Administrador', 'Acceso completo al sistema multi-tenant. Nivel LBAC 5.', 1, 5, 1, GETDATE()),
    (NULL, 'ADMIN', 'Administrador', 'Administrador de cliente. Nivel LBAC 4.', 1, 4, 1, GETDATE()),
    (NULL, 'SUPERVISOR', 'Supervisor', 'Supervisor con gestión de equipos. Nivel LBAC 3.', 1, 3, 1, GETDATE()),
    (NULL, 'USER', 'Usuario', 'Usuario estándar. Nivel LBAC 1.', 1, 1, 1, GETDATE());

SELECT @RolSuperAdminID = rol_id FROM rol WHERE codigo_rol = 'SUPER_ADMIN';
SELECT @RolAdminID = rol_id FROM rol WHERE codigo_rol = 'ADMIN';
SELECT @RolSupervisorID = rol_id FROM rol WHERE codigo_rol = 'SUPERVISOR';
SELECT @RolUserID = rol_id FROM rol WHERE codigo_rol = 'USER';

PRINT '  ✓ Roles globales creados: SUPER_ADMIN(5), ADMIN(4), SUPERVISOR(3), USER(1)';

-- ============================================================================
-- FASE 4: USUARIO SUPER ADMIN (SOLO EN BD CENTRAL)
-- ============================================================================
PRINT 'FASE 4: Creando usuario super admin...';

INSERT INTO usuario (
    cliente_id, nombre_usuario, contrasena, nombre, apellido, correo,
    dni, telefono, proveedor_autenticacion, es_activo, correo_confirmado,
    requiere_cambio_contrasena, intentos_fallidos, fecha_ultimo_cambio_contrasena,
    fecha_creacion
)
VALUES (
    @ClienteSystemID, 'superadmin', @HashedPassword, 'System', 'Administrator',
    'admin@sistema.local', NULL, '+51 999 999 999', 'local', 1, 1, 0, 0,
    GETDATE(), GETDATE()
);
SET @UsuarioSuperAdminID = SCOPE_IDENTITY();

INSERT INTO usuario_rol (usuario_id, rol_id, cliente_id, fecha_asignacion, es_activo)
VALUES (@UsuarioSuperAdminID, @RolSuperAdminID, @ClienteSystemID, GETDATE(), 1);

PRINT '  ✓ Usuario superadmin creado: ' + CAST(@UsuarioSuperAdminID AS NVARCHAR);

-- ============================================================================
-- FASE 5: USUARIOS PARA CLIENTES SINGLE-DB (EN BD CENTRAL)
-- ============================================================================
PRINT 'FASE 5: Creando usuarios para clientes Single-DB...';

-- Usuarios para TECH CORP (Single-DB)
INSERT INTO usuario (
    cliente_id, nombre_usuario, contrasena, nombre, apellido, correo,
    dni, telefono, proveedor_autenticacion, es_activo, correo_confirmado,
    fecha_creacion
)
VALUES 
    (@ClienteTechCorpID, 'admin_tech', @HashedPassword, 'Roberto', 'Tecnología', 'roberto.tech@corp.com', '11223344', '+51 987 555 555', 'local', 1, 1, GETDATE()),
    (@ClienteTechCorpID, 'user_tech', @HashedPassword, 'Carmen', 'Digital', 'carmen.digital@corp.com', '22334455', '+51 987 666 666', 'local', 1, 1, GETDATE());

-- Usuarios para GLOBAL SOLUTIONS (Single-DB)
INSERT INTO usuario (
    cliente_id, nombre_usuario, contrasena, nombre, apellido, correo,
    dni, telefono, proveedor_autenticacion, es_activo, correo_confirmado,
    fecha_creacion
)
VALUES 
    (@ClienteGlobalID, 'admin_global', @HashedPassword, 'Laura', 'Global', 'laura.global@solutions.com', '33445566', '+51 987 777 777', 'local', 1, 1, GETDATE()),
    (@ClienteGlobalID, 'user_global', @HashedPassword, 'Pedro', 'Mundial', 'pedro.mundial@solutions.com', '44556677', '+51 987 888 888', 'local', 1, 1, GETDATE());

PRINT '  ✓ 4 usuarios creados para clientes Single-DB';

-- ============================================================================
-- FASE 6: ASIGNAR ROLES A USUARIOS SINGLE-DB
-- ============================================================================
PRINT 'FASE 6: Asignando roles a usuarios Single-DB...';

-- TECH CORP
INSERT INTO usuario_rol (usuario_id, rol_id, cliente_id, fecha_asignacion, es_activo)
SELECT u.usuario_id, @RolAdminID, @ClienteTechCorpID, GETDATE(), 1
FROM usuario u WHERE u.cliente_id = @ClienteTechCorpID AND u.nombre_usuario = 'admin_tech';

INSERT INTO usuario_rol (usuario_id, rol_id, cliente_id, fecha_asignacion, es_activo)
SELECT u.usuario_id, @RolUserID, @ClienteTechCorpID, GETDATE(), 1
FROM usuario u WHERE u.cliente_id = @ClienteTechCorpID AND u.nombre_usuario = 'user_tech';

-- GLOBAL SOLUTIONS
INSERT INTO usuario_rol (usuario_id, rol_id, cliente_id, fecha_asignacion, es_activo)
SELECT u.usuario_id, @RolAdminID, @ClienteGlobalID, GETDATE(), 1
FROM usuario u WHERE u.cliente_id = @ClienteGlobalID AND u.nombre_usuario = 'admin_global';

INSERT INTO usuario_rol (usuario_id, rol_id, cliente_id, fecha_asignacion, es_activo)
SELECT u.usuario_id, @RolUserID, @ClienteGlobalID, GETDATE(), 1
FROM usuario u WHERE u.cliente_id = @ClienteGlobalID AND u.nombre_usuario = 'user_global';

PRINT '  ✓ Roles asignados a usuarios Single-DB';

-- ============================================================================
-- FASE 7: MÓDULOS DEL SISTEMA
-- ============================================================================
PRINT 'FASE 7: Creando catálogo de módulos...';

INSERT INTO cliente_modulo (codigo_modulo, nombre, descripcion, icono, es_modulo_core, requiere_licencia, orden, es_activo, fecha_creacion)
VALUES 
    ('PLANILLAS', 'Planillas y RRHH', 'Gestión completa de planillas, nóminas y recursos humanos', 'receipt_long', 1, 0, 1, 1, GETDATE()),
    ('LOGISTICA', 'Logística', 'Gestión de logística, transporte y distribución', 'local_shipping', 0, 1, 2, 1, GETDATE()),
    ('ALMACEN', 'Almacén e Inventarios', 'Control de almacenes, inventarios y stock', 'inventory_2', 0, 1, 3, 1, GETDATE()),
    ('FACTURACION', 'Facturación', 'Facturación electrónica y comprobantes de pago', 'receipt', 0, 1, 4, 1, GETDATE());

SELECT @ModuloPlanillasID = modulo_id FROM cliente_modulo WHERE codigo_modulo = 'PLANILLAS';
SELECT @ModuloLogisticaID = modulo_id FROM cliente_modulo WHERE codigo_modulo = 'LOGISTICA';
SELECT @ModuloAlmacenID = modulo_id FROM cliente_modulo WHERE codigo_modulo = 'ALMACEN';
SELECT @ModuloFacturacionID = modulo_id FROM cliente_modulo WHERE codigo_modulo = 'FACTURACION';

PRINT '  ✓ Módulos creados: PLANILLAS, LOGÍSTICA, ALMACÉN, FACTURACIÓN';

-- ============================================================================
-- FASE 8: ACTIVAR MÓDULOS PARA CLIENTES
-- ============================================================================
PRINT 'FASE 8: Activando módulos por cliente...';

-- SYSTEM: Todos los módulos
INSERT INTO cliente_modulo_activo (cliente_id, modulo_id, esta_activo, fecha_activacion, configuracion_json)
SELECT @ClienteSystemID, modulo_id, 1, GETDATE(), '{"full_access": true}'
FROM cliente_modulo;

-- ACME (Multi-DB): Planillas y Almacén
INSERT INTO cliente_modulo_activo (cliente_id, modulo_id, esta_activo, fecha_activacion, configuracion_json, limite_usuarios, limite_registros)
VALUES 
    (@ClienteAcmeID, @ModuloPlanillasID, 1, GETDATE(), '{"plan": "profesional", "empleados_max": 200}', 25, 5000),
    (@ClienteAcmeID, @ModuloAlmacenID, 1, GETDATE(), '{"plan": "profesional", "productos_max": 1000}', 10, 10000);

-- INNOVA (Multi-DB): Solo Planillas
INSERT INTO cliente_modulo_activo (cliente_id, modulo_id, esta_activo, fecha_activacion, configuracion_json, limite_usuarios, limite_registros)
VALUES 
    (@ClienteInnovaID, @ModuloPlanillasID, 1, GETDATE(), '{"plan": "basico", "empleados_max": 50}', 10, 1000);

-- TECH CORP (Single-DB): Planillas y Facturación
INSERT INTO cliente_modulo_activo (cliente_id, modulo_id, esta_activo, fecha_activacion, configuracion_json, limite_usuarios, limite_registros)
VALUES 
    (@ClienteTechCorpID, @ModuloPlanillasID, 1, GETDATE(), '{"plan": "profesional", "empleados_max": 100}', 15, 2000),
    (@ClienteTechCorpID, @ModuloFacturacionID, 1, GETDATE(), '{"plan": "profesional", "comprobantes_mensuales": 500}', 8, 5000);

-- GLOBAL SOLUTIONS (Single-DB): Solo Planillas
INSERT INTO cliente_modulo_activo (cliente_id, modulo_id, esta_activo, fecha_activacion, configuracion_json, limite_usuarios, limite_registros)
VALUES 
    (@ClienteGlobalID, @ModuloPlanillasID, 1, GETDATE(), '{"plan": "basico", "empleados_max": 40}', 8, 800);

PRINT '  ✓ Módulos activados por cliente';

-- ============================================================================
-- FASE 9: CONFIGURACIÓN DE CONEXIONES HÍBRIDAS
-- ============================================================================
PRINT 'FASE 9: Configurando conexiones híbridas...';

-- CONEXIONES MULTI-DB (BD Separada)
INSERT INTO cliente_modulo_conexion (
    cliente_id, modulo_id, servidor, puerto, nombre_bd,
    usuario_encriptado, password_encriptado, connection_string_encriptado,
    tipo_bd, usa_ssl, timeout_segundos, max_pool_size,
    es_solo_lectura, es_conexion_principal, es_activo,
    fecha_creacion, creado_por_usuario_id
)
VALUES 
    -- ACME (Multi-DB)
    (@ClienteAcmeID, @ModuloPlanillasID, 'localhost', 1433, 'bd_cliente_acme', 'ENCRYPTED_USER_ACME', 'ENCRYPTED_PASSWORD_ACME', NULL, 'sqlserver', 1, 30, 50, 0, 1, 1, GETDATE(), @UsuarioSuperAdminID),
    (@ClienteAcmeID, @ModuloAlmacenID, 'localhost', 1433, 'bd_cliente_acme', 'ENCRYPTED_USER_ACME', 'ENCRYPTED_PASSWORD_ACME', NULL, 'sqlserver', 1, 30, 50, 0, 1, 1, GETDATE(), @UsuarioSuperAdminID),
    -- INNOVA (Multi-DB)
    (@ClienteInnovaID, @ModuloPlanillasID, 'localhost', 1433, 'bd_cliente_innova', 'ENCRYPTED_USER_INNOVA', 'ENCRYPTED_PASSWORD_INNOVA', NULL, 'sqlserver', 1, 30, 30, 0, 1, 1, GETDATE(), @UsuarioSuperAdminID);

-- CONEXIONES SINGLE-DB (BD Central)
INSERT INTO cliente_modulo_conexion (
    cliente_id, modulo_id, servidor, puerto, nombre_bd,
    usuario_encriptado, password_encriptado, connection_string_encriptado,
    tipo_bd, usa_ssl, timeout_segundos, max_pool_size,
    es_solo_lectura, es_conexion_principal, es_activo,
    fecha_creacion, creado_por_usuario_id
)
SELECT 
    c.cliente_id, 
    cma.modulo_id,
    'localhost', 
    1433, 
    'bd_sistema',
    'ENCRYPTED_USER_CENTRAL', 
    'ENCRYPTED_PASSWORD_CENTRAL', 
    NULL,
    'sqlserver', 
    1, 
    30, 
    100,
    0, 
    1, 
    1,
    GETDATE(), 
    @UsuarioSuperAdminID
FROM cliente_modulo_activo cma
INNER JOIN cliente c ON cma.cliente_id = c.cliente_id
WHERE c.cliente_id IN (@ClienteTechCorpID, @ClienteGlobalID)
AND cma.esta_activo = 1;

PRINT '  ✓ Conexiones híbridas configuradas (2 Multi-DB + 2 Single-DB)';
PRINT '  ⚠️  RECORDATORIO: Encriptar credenciales en producción';

/*
-- ============================================================================
-- FASE 10: DATOS DE NEGOCIO PARA CLIENTES SINGLE-DB
-- ============================================================================
PRINT 'FASE 10: Insertando datos de negocio para clientes Single-DB...';

-- Empleados para TECH CORP (Single-DB)
INSERT INTO empleado (cliente_id, codigo_empleado, nombre, apellido, dni, fecha_ingreso, cargo, departamento, salario_base)
VALUES 
    (@ClienteTechCorpID, 'TECH001', 'Ana', 'Programadora', '55667788', '2020-08-12', 'Desarrollador Senior', 'Tecnología', 5200.00),
    (@ClienteTechCorpID, 'TECH002', 'Luis', 'DevOps', '66778899', '2021-11-25', 'Ingeniero DevOps', 'Infraestructura', 4800.00),
    (@ClienteTechCorpID, 'TECH003', 'Sofia', 'Diseñadora', '77889900', '2022-03-18', 'Diseñadora UI/UX', 'Diseño', 3800.00);

-- Empleados para GLOBAL SOLUTIONS (Single-DB)
INSERT INTO empleado (cliente_id, codigo_empleado, nombre, apellido, dni, fecha_ingreso, cargo, departamento, salario_base)
VALUES 
    (@ClienteGlobalID, 'GLOB001', 'Carlos', 'Consultor', '88990011', '2021-05-30', 'Consultor Senior', 'Consultoría', 4500.00),
    (@ClienteGlobalID, 'GLOB002', 'Elena', 'Asesora', '99001122', '2022-09-14', 'Asesora Comercial', 'Ventas', 3200.00);

PRINT '  ✓ 5 empleados creados para clientes Single-DB';
*/
-- ============================================================================
-- FASE 11: ÁREAS Y MENÚS GLOBALES
-- ============================================================================
PRINT 'FASE 11: Creando áreas y menús globales...';

DECLARE @AreaSistemaID INT, @AreaPlanillasID INT, @AreaAlmacenID INT, @AreaFacturacionID INT;

INSERT INTO area_menu (cliente_id, nombre, descripcion, icono, orden, es_area_sistema, es_activo, fecha_creacion)
VALUES 
    (NULL, 'Sistema', 'Administración del sistema multi-tenant', 'settings', 1, 1, 1, GETDATE()),
    (NULL, 'Planillas', 'Gestión de planillas y RRHH', 'receipt_long', 2, 1, 1, GETDATE()),
    (NULL, 'Almacén', 'Control de inventarios', 'inventory_2', 3, 1, 1, GETDATE()),
    (NULL, 'Facturación', 'Facturación electrónica', 'receipt', 4, 1, 1, GETDATE());

SELECT @AreaSistemaID = area_id FROM area_menu WHERE nombre = 'Sistema';
SELECT @AreaPlanillasID = area_id FROM area_menu WHERE nombre = 'Planillas';
SELECT @AreaAlmacenID = area_id FROM area_menu WHERE nombre = 'Almacén';
SELECT @AreaFacturacionID = area_id FROM area_menu WHERE nombre = 'Facturación';

-- Menús globales
INSERT INTO menu (cliente_id, area_id, nombre, descripcion, icono, ruta, orden, es_menu_sistema, requiere_autenticacion, es_visible, es_activo, fecha_creacion)
VALUES 
    (NULL, @AreaSistemaID, 'Gestión de Clientes', 'Administrar clientes multi-tenant', 'business', '/sistema/clientes', 1, 1, 1, 1, 1, GETDATE()),
    (NULL, @AreaPlanillasID, 'Empleados', 'Gestión de empleados', 'people', '/planillas/empleados', 1, 1, 1, 1, 1, GETDATE()),
    (NULL, @AreaPlanillasID, 'Procesar Planilla', 'Procesar planillas de pago', 'calculate', '/planillas/procesar', 2, 1, 1, 1, 1, GETDATE()),
    (NULL, @AreaAlmacenID, 'Productos', 'Gestión de productos', 'inventory', '/almacen/productos', 1, 1, 1, 1, 1, GETDATE()),
    (NULL, @AreaFacturacionID, 'Comprobantes', 'Gestión de comprobantes', 'receipt', '/facturacion/comprobantes', 1, 1, 1, 1, 1, GETDATE());

PRINT '  ✓ Áreas y menús globales creados';

-- ============================================================================
-- FASE 12: PERMISOS PARA USUARIOS SINGLE-DB
-- ============================================================================
PRINT 'FASE 12: Configurando permisos para usuarios Single-DB...';

-- Permisos para admin_tech (TECH CORP)
INSERT INTO rol_menu_permiso (cliente_id, rol_id, menu_id, puede_ver, puede_crear, puede_editar, puede_eliminar, puede_exportar, puede_imprimir, fecha_creacion)
SELECT 
    @ClienteTechCorpID, 
    @RolAdminID, 
    menu_id, 
    1, 1, 1, 1, 1, 1, 
    GETDATE()
FROM menu 
WHERE es_activo = 1;

-- Permisos para user_tech (TECH CORP)
INSERT INTO rol_menu_permiso (cliente_id, rol_id, menu_id, puede_ver, puede_crear, puede_editar, puede_eliminar, puede_exportar, puede_imprimir, fecha_creacion)
SELECT 
    @ClienteTechCorpID, 
    @RolUserID, 
    menu_id, 
    1, 0, 0, 0, 1, 0, 
    GETDATE()
FROM menu 
WHERE es_activo = 1 AND area_id IN (@AreaPlanillasID, @AreaFacturacionID);

-- Permisos para admin_global (GLOBAL SOLUTIONS)
INSERT INTO rol_menu_permiso (cliente_id, rol_id, menu_id, puede_ver, puede_crear, puede_editar, puede_eliminar, puede_exportar, puede_imprimir, fecha_creacion)
SELECT 
    @ClienteGlobalID, 
    @RolAdminID, 
    menu_id, 
    1, 1, 1, 1, 1, 1, 
    GETDATE()
FROM menu 
WHERE es_activo = 1;

-- Permisos para user_global (GLOBAL SOLUTIONS)
INSERT INTO rol_menu_permiso (cliente_id, rol_id, menu_id, puede_ver, puede_crear, puede_editar, puede_eliminar, puede_exportar, puede_imprimir, fecha_creacion)
SELECT 
    @ClienteGlobalID, 
    @RolUserID, 
    menu_id, 
    1, 0, 0, 0, 1, 0, 
    GETDATE()
FROM menu 
WHERE es_activo = 1 AND area_id = @AreaPlanillasID;

PRINT '  ✓ Permisos configurados para usuarios Single-DB';

-- ============================================================================
-- FASE 13: AUDITORÍA INICIAL
-- ============================================================================
PRINT 'FASE 13: Registrando auditoría inicial...';

INSERT INTO auth_audit_log (
    cliente_id, usuario_id, evento, nombre_usuario_intento, descripcion,
    exito, ip_address, user_agent, metadata_json, fecha_evento
)
VALUES (
    @ClienteSystemID, @UsuarioSuperAdminID, 'system_initialization', 'superadmin',
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
PRINT '   • ACME Corp (ID: ' + CAST(@ClienteAcmeID AS NVARCHAR) + ') → bd_cliente_acme';
PRINT '   • Innova Tech (ID: ' + CAST(@ClienteInnovaID AS NVARCHAR) + ') → bd_cliente_innova';
PRINT '';
PRINT '🔶 CLIENTES SINGLE-DATABASE (BD Central):';
PRINT '   • Tech Corp (ID: ' + CAST(@ClienteTechCorpID AS NVARCHAR) + ') → bd_sistema';
PRINT '   • Global Solutions (ID: ' + CAST(@ClienteGlobalID AS NVARCHAR) + ') → bd_sistema';
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
PRINT '   2. Ejecutar 03_seed_bd_clientes.sql en bd_cliente_acme (@ClienteID = 2)';
PRINT '   3. Ejecutar 03_seed_bd_clientes.sql en bd_cliente_innova (@ClienteID = 3)';
PRINT '   4. Sistema listo para operar en modo híbrido';
PRINT '';
PRINT 'Script finalizado: ' + CONVERT(NVARCHAR, GETDATE(), 120);
GO