-- ============================================================================
-- SCRIPT: 03_seed_bd_clientes.sql
-- DESCRIPCIÓN: Seed para BD de clientes (ACME e INNOVA)
-- USO: Ejecutar en cada BD cliente, ajustando @ClienteCodigo
-- NOTA: Este script usa UNIQUEIDENTIFIER (UUID) para todas las Primary Keys
--       Se identifica al cliente por código_cliente en lugar de ID numérico
-- ============================================================================

-- ============================================================================
-- CONFIGURACIÓN POR CLIENTE - ¡AJUSTAR ESTOS VALORES!
-- ============================================================================
DECLARE @ClienteCodigo NVARCHAR(20) = 'ACME001';  -- 'ACME001' para ACME, 'INNOVA002' para INNOVA
DECLARE @ClienteNombre NVARCHAR(50) = 'ACME Corp'; -- 'ACME Corp' o 'Innova Tech'

PRINT '============================================';
PRINT '   SEED BD CLIENTE: ' + @ClienteNombre;
PRINT '   Cliente Código: ' + @ClienteCodigo;
PRINT '============================================';
PRINT '';

-- ============================================================================
-- VARIABLES GLOBALES
-- ============================================================================
DECLARE @ClienteID UNIQUEIDENTIFIER;

DECLARE @RolAdminID UNIQUEIDENTIFIER;
DECLARE @RolSupervisorID UNIQUEIDENTIFIER;
DECLARE @RolUserID UNIQUEIDENTIFIER;

DECLARE @UsuarioAdminID UNIQUEIDENTIFIER;
DECLARE @UsuarioSupervisorID UNIQUEIDENTIFIER;
DECLARE @UsuarioUserID UNIQUEIDENTIFIER;

DECLARE @AreaPlanillasID UNIQUEIDENTIFIER;
DECLARE @AreaAlmacenID UNIQUEIDENTIFIER;

-- Hash bcrypt para 'Admin@2025'
DECLARE @HashedPassword NVARCHAR(255) = '$2b$12$CJrVD8JhQlIeZZyp64CZCubM1.vBF2V0ZyRJg2C3bcS7A8/mhi5xm';

-- ============================================================================
-- OBTENER CLIENTE_ID DESDE BD CENTRAL
-- NOTA: En una BD dedicada, el cliente_id debe ser el mismo UUID que en la BD central
-- ============================================================================
-- PASO 1: Ejecuta en la BD central para obtener el UUID del cliente:
--   SELECT cliente_id FROM cliente WHERE codigo_cliente = 'ACME001';  -- Para ACME
--   SELECT cliente_id FROM cliente WHERE codigo_cliente = 'INNOVA002'; -- Para INNOVA
--
-- PASO 2: Copia el UUID obtenido y configúralo aquí:
-- ============================================================================

-- ⚠️  CONFIGURAR MANUALMENTE EL UUID DEL CLIENTE AQUÍ:
-- Reemplaza el UUID de abajo con el UUID real obtenido de la BD central

IF @ClienteCodigo = 'ACME001'
BEGIN
    -- UUID para ACME - REEMPLAZAR con el UUID real de la BD central
    SET @ClienteID = '00000000-0000-0000-0000-000000000000'; -- ⚠️ REEMPLAZAR
END
ELSE IF @ClienteCodigo = 'INNOVA002'
BEGIN
    -- UUID para INNOVA - REEMPLAZAR con el UUID real de la BD central
    SET @ClienteID = '00000000-0000-0000-0000-000000000000'; -- ⚠️ REEMPLAZAR
END
ELSE
BEGIN
    PRINT 'ERROR: Código de cliente no reconocido: ' + @ClienteCodigo;
    PRINT 'Configura @ClienteID manualmente antes de continuar.';
    RETURN;
END

PRINT '⚠️  IMPORTANTE: Verifica que @ClienteID (' + CAST(@ClienteID AS NVARCHAR(36)) + ')';
PRINT '   coincida con el UUID de la BD central para el cliente: ' + @ClienteCodigo;
PRINT '';

-- ============================================================================
-- FASE 1: ROLES ESPECÍFICOS DEL CLIENTE
-- ============================================================================
PRINT 'FASE 1: Creando roles del cliente...';

SET @RolAdminID = NEWID();
SET @RolSupervisorID = NEWID();
SET @RolUserID = NEWID();

INSERT INTO rol (rol_id, cliente_id, codigo_rol, nombre, descripcion, es_rol_sistema, nivel_acceso, es_activo, fecha_creacion)
VALUES 
    (@RolAdminID, @ClienteID, 'ADMIN', 'Administrador', 'Administrador con acceso completo', 0, 4, 1, GETDATE()),
    (@RolSupervisorID, @ClienteID, 'SUPERVISOR', 'Supervisor', 'Supervisor de departamento', 0, 3, 1, GETDATE()),
    (@RolUserID, @ClienteID, 'USER', 'Usuario', 'Usuario estándar', 0, 1, 1, GETDATE());

PRINT '  ✓ Roles del cliente creados';

-- ============================================================================
-- FASE 2: USUARIOS DEL CLIENTE
-- ============================================================================
PRINT 'FASE 2: Creando usuarios del cliente...';

-- Usuario Admin
SET @UsuarioAdminID = NEWID();
INSERT INTO usuario (
    usuario_id, cliente_id, nombre_usuario, contrasena, nombre, apellido, correo,
    dni, telefono, proveedor_autenticacion, es_activo, correo_confirmado,
    requiere_cambio_contrasena, fecha_ultimo_cambio_contrasena,
    fecha_creacion
)
VALUES (
    @UsuarioAdminID, @ClienteID, 
    CASE WHEN @ClienteCodigo = 'ACME001' THEN 'admin_acme' ELSE 'admin_innova' END,
    @HashedPassword, 
    CASE WHEN @ClienteCodigo = 'ACME001' THEN 'Carlos' ELSE 'Ana' END,
    CASE WHEN @ClienteCodigo = 'ACME001' THEN 'Acme' ELSE 'Innovadora' END,
    CASE WHEN @ClienteCodigo = 'ACME001' THEN 'carlos.acme@empresa.com' ELSE 'ana.innova@tech.com' END,
    CASE WHEN @ClienteCodigo = 'ACME001' THEN '12345678' ELSE '87654321' END,
    CASE WHEN @ClienteCodigo = 'ACME001' THEN '+51 987 111 111' ELSE '+51 987 222 222' END,
    'local', 1, 1, 0, GETDATE(), GETDATE()
);

-- Usuario Supervisor
SET @UsuarioSupervisorID = NEWID();
INSERT INTO usuario (
    usuario_id, cliente_id, nombre_usuario, contrasena, nombre, apellido, correo,
    dni, telefono, proveedor_autenticacion, es_activo, correo_confirmado,
    fecha_creacion
)
VALUES (
    @UsuarioSupervisorID, @ClienteID, 
    CASE WHEN @ClienteCodigo = 'ACME001' THEN 'supervisor_acme' ELSE 'supervisor_innova' END,
    @HashedPassword, 
    CASE WHEN @ClienteCodigo = 'ACME001' THEN 'Laura' ELSE 'Pedro' END,
    CASE WHEN @ClienteCodigo = 'ACME001' THEN 'Gómez' ELSE 'Tecno' END,
    CASE WHEN @ClienteCodigo = 'ACME001' THEN 'laura.gomez@empresa.com' ELSE 'pedro.tecnologia@tech.com' END,
    CASE WHEN @ClienteCodigo = 'ACME001' THEN '22334455' ELSE '55443322' END,
    CASE WHEN @ClienteCodigo = 'ACME001' THEN '+51 987 333 333' ELSE '+51 987 444 444' END,
    'local', 1, 1, GETDATE()
);

-- Usuario Básico
SET @UsuarioUserID = NEWID();
INSERT INTO usuario (
    usuario_id, cliente_id, nombre_usuario, contrasena, nombre, apellido, correo,
    dni, telefono, proveedor_autenticacion, es_activo, correo_confirmado,
    fecha_creacion
)
VALUES (
    @UsuarioUserID, @ClienteID, 
    CASE WHEN @ClienteCodigo = 'ACME001' THEN 'usuario_acme' ELSE 'usuario_innova' END,
    @HashedPassword, 
    CASE WHEN @ClienteCodigo = 'ACME001' THEN 'Miguel' ELSE 'Sofía' END,
    CASE WHEN @ClienteCodigo = 'ACME001' THEN 'Rodríguez' ELSE 'Digital' END,
    CASE WHEN @ClienteCodigo = 'ACME001' THEN 'miguel.rodriguez@empresa.com' ELSE 'sofia.digital@tech.com' END,
    CASE WHEN @ClienteCodigo = 'ACME001' THEN '33445566' ELSE '66554433' END,
    CASE WHEN @ClienteCodigo = 'ACME001' THEN '+51 987 555 555' ELSE '+51 987 666 666' END,
    'local', 1, 1, GETDATE()
);

PRINT '  ✓ Usuarios del cliente creados';

-- ============================================================================
-- FASE 3: ASIGNAR ROLES A USUARIOS
-- ============================================================================
PRINT 'FASE 3: Asignando roles a usuarios...';

INSERT INTO usuario_rol (usuario_rol_id, usuario_id, rol_id, cliente_id, fecha_asignacion, es_activo)
VALUES 
    (NEWID(), @UsuarioAdminID, @RolAdminID, @ClienteID, GETDATE(), 1),
    (NEWID(), @UsuarioSupervisorID, @RolSupervisorID, @ClienteID, GETDATE(), 1),
    (NEWID(), @UsuarioUserID, @RolUserID, @ClienteID, GETDATE(), 1);

PRINT '  ✓ Roles asignados a usuarios';

-- ============================================================================
-- FASE 4: ÁREAS DE MENÚ DEL CLIENTE
-- ============================================================================
PRINT 'FASE 4: Creando áreas de menú...';

SET @AreaPlanillasID = NEWID();
SET @AreaAlmacenID = NEWID();

INSERT INTO area_menu (area_id, cliente_id, nombre, descripcion, icono, orden, es_area_sistema, es_activo, fecha_creacion)
VALUES 
    (@AreaPlanillasID, @ClienteID, 'Planillas', 'Gestión de planillas y personal', 'receipt_long', 1, 0, 1, GETDATE()),
    (@AreaAlmacenID, @ClienteID, 'Almacén', 'Control de inventarios', 'inventory_2', 2, 0, 1, GETDATE());

PRINT '  ✓ Áreas de menú creadas';

-- ============================================================================
-- FASE 5: MENÚS DEL CLIENTE
-- ============================================================================
PRINT 'FASE 5: Creando menús del cliente...';

DECLARE @MenuDashboardID UNIQUEIDENTIFIER, @MenuEmpleadosID UNIQUEIDENTIFIER, @MenuPlanillasID UNIQUEIDENTIFIER,
        @MenuProductosID UNIQUEIDENTIFIER, @MenuMovimientosID UNIQUEIDENTIFIER;

-- Menú Dashboard
SET @MenuDashboardID = NEWID();
INSERT INTO menu (menu_id, cliente_id, area_id, nombre, descripcion, icono, ruta, orden, es_menu_sistema, requiere_autenticacion, es_visible, es_activo, fecha_creacion)
VALUES (@MenuDashboardID, @ClienteID, NULL, 'Dashboard', 'Panel principal', 'dashboard', '/dashboard', 1, 0, 1, 1, 1, GETDATE());

-- Menús Planillas
SET @MenuEmpleadosID = NEWID();
SET @MenuPlanillasID = NEWID();
INSERT INTO menu (menu_id, cliente_id, area_id, nombre, descripcion, icono, ruta, orden, es_menu_sistema, requiere_autenticacion, es_visible, es_activo, fecha_creacion)
VALUES 
    (@MenuEmpleadosID, @ClienteID, @AreaPlanillasID, 'Empleados', 'Gestión de empleados', 'people', '/planillas/empleados', 1, 0, 1, 1, 1, GETDATE()),
    (@MenuPlanillasID, @ClienteID, @AreaPlanillasID, 'Planillas', 'Procesar planillas', 'calculate', '/planillas/procesar', 2, 0, 1, 1, 1, GETDATE());

-- Menús Almacén (solo para ACME)
IF @ClienteCodigo = 'ACME001'
BEGIN
    SET @MenuProductosID = NEWID();
    SET @MenuMovimientosID = NEWID();
    INSERT INTO menu (menu_id, cliente_id, area_id, nombre, descripcion, icono, ruta, orden, es_menu_sistema, requiere_autenticacion, es_visible, es_activo, fecha_creacion)
    VALUES 
        (@MenuProductosID, @ClienteID, @AreaAlmacenID, 'Productos', 'Gestión de productos', 'inventory', '/almacen/productos', 1, 0, 1, 1, 1, GETDATE()),
        (@MenuMovimientosID, @ClienteID, @AreaAlmacenID, 'Movimientos', 'Movimientos de stock', 'swap_horiz', '/almacen/movimientos', 2, 0, 1, 1, 1, GETDATE());
END

PRINT '  ✓ Menús del cliente creados';

-- ============================================================================
-- FASE 6: PERMISOS POR ROL
-- ============================================================================
PRINT 'FASE 6: Configurando permisos...';

-- Permisos para ADMIN (acceso completo)
INSERT INTO rol_menu_permiso (permiso_id, cliente_id, rol_id, menu_id, puede_ver, puede_crear, puede_editar, puede_eliminar, puede_exportar, puede_imprimir, fecha_creacion)
SELECT NEWID(), @ClienteID, @RolAdminID, menu_id, 1, 1, 1, 1, 1, 1, GETDATE()
FROM menu 
WHERE cliente_id = @ClienteID AND es_activo = 1;

-- Permisos para SUPERVISOR (solo ver y editar)
INSERT INTO rol_menu_permiso (permiso_id, cliente_id, rol_id, menu_id, puede_ver, puede_crear, puede_editar, puede_eliminar, puede_exportar, puede_imprimir, fecha_creacion)
SELECT NEWID(), @ClienteID, @RolSupervisorID, menu_id, 1, 0, 1, 0, 1, 1, GETDATE()
FROM menu 
WHERE cliente_id = @ClienteID AND es_activo = 1;

-- Permisos para USER (solo ver)
INSERT INTO rol_menu_permiso (permiso_id, cliente_id, rol_id, menu_id, puede_ver, puede_crear, puede_editar, puede_eliminar, puede_exportar, puede_imprimir, fecha_creacion)
SELECT NEWID(), @ClienteID, @RolUserID, menu_id, 1, 0, 0, 0, 1, 0, GETDATE()
FROM menu 
WHERE cliente_id = @ClienteID AND es_activo = 1;

PRINT '  ✓ Permisos configurados por rol';
/*
-- ============================================================================
-- FASE 7: DATOS DE NEGOCIO (EMPLEADOS)
-- ============================================================================
PRINT 'FASE 7: Insertando datos de negocio...';

-- Empleados para ACME
IF @ClienteCodigo = 'ACME001'
BEGIN
    INSERT INTO empleado (empleado_id, cliente_id, codigo_empleado, nombre, apellido, dni, fecha_ingreso, cargo, departamento, salario_base)
    VALUES 
        (NEWID(), @ClienteID, 'EMP001', 'Juan', 'Pérez', '11223344', '2020-03-15', 'Gerente General', 'Gerencia', 8500.00),
        (NEWID(), @ClienteID, 'EMP002', 'María', 'López', '22334455', '2021-06-20', 'Supervisor', 'Producción', 4500.00),
        (NEWID(), @ClienteID, 'EMP003', 'Carlos', 'Gómez', '33445566', '2022-01-10', 'Analista', 'TI', 3800.00),
        (NEWID(), @ClienteID, 'EMP004', 'Ana', 'Rodríguez', '44556677', '2023-08-05', 'Asistente', 'Administración', 2800.00);

    -- Productos para ACME
    INSERT INTO producto (producto_id, cliente_id, codigo_producto, nombre, descripcion, categoria, precio_unitario, stock_actual, stock_minimo)
    VALUES 
        (NEWID(), @ClienteID, 'PROD001', 'Laptop Dell XPS', 'Laptop empresarial i7 16GB RAM', 'Tecnología', 3500.00, 25, 5),
        (NEWID(), @ClienteID, 'PROD002', 'Mouse Inalámbrico', 'Mouse ergonómico inalámbrico', 'Accesorios', 45.00, 100, 20),
        (NEWID(), @ClienteID, 'PROD003', 'Monitor 24"', 'Monitor LED Full HD 24 pulgadas', 'Monitores', 280.00, 30, 8);

    PRINT '  ✓ 4 empleados y 3 productos creados para ACME';
END

-- Empleados para INNOVA
IF @ClienteCodigo = 'INNOVA002'
BEGIN
    INSERT INTO empleado (empleado_id, cliente_id, codigo_empleado, nombre, apellido, dni, fecha_ingreso, cargo, departamento, salario_base)
    VALUES 
        (NEWID(), @ClienteID, 'DEV001', 'Luis', 'Martínez', '55667788', '2021-02-10', 'Desarrollador Senior', 'Tecnología', 5200.00),
        (NEWID(), @ClienteID, 'DEV002', 'Elena', 'Silva', '66778899', '2022-05-15', 'Desarrollador Fullstack', 'Tecnología', 4200.00),
        (NEWID(), @ClienteID, 'DES003', 'Roberto', 'Castro', '77889900', '2023-03-20', 'Diseñador UI/UX', 'Diseño', 3800.00);

    PRINT '  ✓ 3 empleados creados para INNOVA';
END
*/
-- ============================================================================
-- FASE 8: AUDITORÍA INICIAL DEL CLIENTE
-- ============================================================================
PRINT 'FASE 8: Registrando auditoría del cliente...';

INSERT INTO auth_audit_log (
    log_id, cliente_id, usuario_id, evento, nombre_usuario_intento, descripcion,
    exito, ip_address, metadata_json, fecha_evento
)
VALUES (
    NEWID(), @ClienteID, @UsuarioAdminID, 'client_database_initialized', 
    CASE WHEN @ClienteCodigo = 'ACME001' THEN 'admin_acme' ELSE 'admin_innova' END,
    'Base de datos del cliente inicializada con datos seed',
    1, '127.0.0.1',
    CASE 
        WHEN @ClienteCodigo = 'ACME001' THEN '{"employees": 4, "products": 3, "users": 3}'
        ELSE '{"employees": 3, "users": 3}'
    END,
    GETDATE()
);

PRINT '  ✓ Auditoría inicial registrada';

-- ============================================================================
-- RESUMEN FINAL
-- ============================================================================
PRINT '';
PRINT '============================================';
PRINT '   SEED BD CLIENTE - COMPLETADO';
PRINT '============================================';
PRINT '';
PRINT '📊 RESUMEN PARA ' + @ClienteNombre + ':';
PRINT '----------------------------';
PRINT '✅ Usuarios creados:';
PRINT '   - ' + CASE WHEN @ClienteCodigo = 'ACME001' THEN 'admin_acme' ELSE 'admin_innova' END + ' (Admin)';
PRINT '   - ' + CASE WHEN @ClienteCodigo = 'ACME001' THEN 'supervisor_acme' ELSE 'supervisor_innova' END + ' (Supervisor)';
PRINT '   - ' + CASE WHEN @ClienteCodigo = 'ACME001' THEN 'usuario_acme' ELSE 'usuario_innova' END + ' (Usuario)';
PRINT '';
PRINT '✅ Datos de negocio:';
IF @ClienteCodigo = 'ACME001'
    PRINT '   - 4 empleados';
IF @ClienteCodigo = 'ACME001'
    PRINT '   - 3 productos';
IF @ClienteCodigo = 'INNOVA002'
    PRINT '   - 3 empleados';
PRINT '';
PRINT '🔐 CREDENCIALES:';
PRINT '   - Todos los usuarios: Admin@2025';
PRINT '';
PRINT '📝 CONFIGURACIÓN:';
PRINT '   - Roles: ADMIN, SUPERVISOR, USER';
PRINT '   - Menús personalizados del cliente';
PRINT '   - Permisos granulares por rol';
PRINT '';
PRINT '⚠️  IMPORTANTE:';
PRINT '   - El cliente_id usado (' + CAST(@ClienteID AS NVARCHAR(36)) + ')';
PRINT '     DEBE coincidir con el UUID de la BD central';
PRINT '';
PRINT 'Script finalizado: ' + CONVERT(NVARCHAR, GETDATE(), 120);
PRINT '';

-- Verificación final
DECLARE @TotalUsuarios INT = (SELECT COUNT(*) FROM usuario WHERE cliente_id = @ClienteID);
-- DECLARE @TotalEmpleados INT = (SELECT COUNT(*) FROM empleado WHERE cliente_id = @ClienteID);
-- DECLARE @TotalProductos INT = (SELECT COUNT(*) FROM producto WHERE cliente_id = @ClienteID);

PRINT 'VERIFICACIÓN: ' + CAST(@TotalUsuarios AS NVARCHAR) + ' usuarios';
-- + ', ' + CAST(@TotalEmpleados AS NVARCHAR) + ' empleados' + 
-- CASE WHEN @ClienteCodigo = 'ACME001' THEN ', ' + CAST(@TotalProductos AS NVARCHAR) + ' productos' ELSE '' END;
GO

