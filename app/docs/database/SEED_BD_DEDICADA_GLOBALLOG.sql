-- ============================================================================
-- SCRIPT: SEED DATA PARA BD DEDICADA - GLOBALLOG
-- DESCRIPCIÓN: Datos iniciales para poblar la BD dedicada de GlobalLog
-- USO: Ejecutar en la BD dedicada de GlobalLog (bd_cliente_globallog)
-- NOTA: Cliente con tipo_instalacion = 'dedicated'
-- Módulos activos: ALMACEN, LOGISTICA (NO tiene PLANILLAS)
-- ============================================================================

-- ⚠️ IMPORTANTE: Cambiar el nombre de la BD según tu configuración
-- USE bd_cliente_globallog;
-- GO

-- ============================================================================
-- SECCIÓN 1: USUARIOS Y ROLES
-- ============================================================================

-- Cliente ID de GlobalLog (debe coincidir con BD central)
DECLARE @cliente_id UNIQUEIDENTIFIER = '44444444-4444-4444-4444-444444444444';

-- Rol ADMIN
INSERT INTO rol (
    rol_id,
    cliente_id,
    codigo_rol,
    nombre,
    descripcion,
    es_rol_sistema,
    nivel_acceso,
    es_activo
) VALUES (
    '44444444-4444-4444-4444-444444444410',  -- ADMIN (UUID válido)
    @cliente_id,
    'ADMIN',
    'Administrador',
    'Rol de administrador con acceso completo',
    1,
    5,
    1
);

-- Rol USER
INSERT INTO rol (
    rol_id,
    cliente_id,
    codigo_rol,
    nombre,
    descripcion,
    es_rol_sistema,
    nivel_acceso,
    es_activo
) VALUES (
    '44444444-4444-4444-4444-444444444420',  -- USER (UUID válido)
    @cliente_id,
    'USER',
    'Usuario',
    'Rol de usuario estándar',
    1,
    1,
    1
);

-- Usuario admin
-- Password: admin123
INSERT INTO usuario (
    usuario_id,
    cliente_id,
    nombre_usuario,
    contrasena,
    nombre,
    apellido,
    correo,
    es_activo,
    correo_confirmado
) VALUES (
    '44444444-4444-4444-4444-444444444100',  -- admin (UUID válido)
    @cliente_id,
    'admin',
    '$2b$12$6J/bWiSYNFHFblxoVot4Je2HyWGU.QyFxtPdpsAMP2hz4fGid5WQu',  -- admin123
    'Administrador',
    'GlobalLog',
    'admin@globallog.com',
    1,
    1
);

-- Usuario user
-- Password: user123
INSERT INTO usuario (
    usuario_id,
    cliente_id,
    nombre_usuario,
    contrasena,
    nombre,
    apellido,
    correo,
    es_activo,
    correo_confirmado
) VALUES (
    '44444444-4444-4444-4444-444444444200',  -- user (UUID válido)
    @cliente_id,
    'user',
    '$2b$12$ZvpoS9E0eMe6pbxGNoho1eN8hMbeTCkAE5Fyztm1N.51jxcqVYW86',  -- user123
    'Usuario',
    'GlobalLog',
    'user@globallog.com',
    1,
    1
);

-- Asignar roles a usuarios
INSERT INTO usuario_rol (
    usuario_rol_id,
    usuario_id,
    rol_id,
    cliente_id,
    es_activo
) VALUES
(
    NEWID(),
    '44444444-4444-4444-4444-444444444100',  -- admin (UUID válido)  -- admin
    '44444444-4444-4444-4444-444444444410',  -- ADMIN (UUID válido)  -- ADMIN
    @cliente_id,
    1
),
(
    NEWID(),
    '44444444-4444-4444-4444-444444444200',  -- user (UUID válido)  -- user
    '44444444-4444-4444-4444-444444444420',  -- USER (UUID válido)  -- USER
    @cliente_id,
    1
);

-- ============================================================================
-- SECCIÓN 2: PERMISOS (Solo para módulos activos: ALMACEN y LOGISTICA)
-- ============================================================================

-- Permisos para ADMIN (acceso completo)
-- Solo menús de ALMACEN y LOGISTICA (NO PLANILLAS)

-- Menús de ALMACEN
INSERT INTO rol_menu_permiso (
    permiso_id,
    cliente_id,
    rol_id,
    menu_id,
    puede_ver,
    puede_crear,
    puede_editar,
    puede_eliminar,
    puede_exportar,
    puede_imprimir
) VALUES
-- Listar Productos
(
    NEWID(),
    @cliente_id,
    '44444444-4444-4444-4444-444444444410',  -- ADMIN (UUID válido)  -- ADMIN
    'AA11AA11-AA11-AA11-AA11-AA11AA11AA11',  -- ALMACEN_PRODUCTOS_LISTAR
    1, 1, 1, 1, 1, 1
),
-- Crear Producto
(
    NEWID(),
    @cliente_id,
    '44444444-4444-4444-4444-444444444410',  -- ADMIN (UUID válido)  -- ADMIN
    'AA12AA12-AA12-AA12-AA12-AA12AA12AA12',  -- ALMACEN_PRODUCTOS_CREAR
    1, 1, 1, 1, 1, 1
),
-- Categorías
(
    NEWID(),
    @cliente_id,
    '44444444-4444-4444-4444-444444444410',  -- ADMIN (UUID válido)  -- ADMIN
    'AA13AA13-AA13-AA13-AA13-AA13AA13AA13',  -- ALMACEN_PRODUCTOS_CATEGORIAS
    1, 1, 1, 1, 1, 1
),
-- Movimientos
(
    NEWID(),
    @cliente_id,
    '44444444-4444-4444-4444-444444444410',  -- ADMIN (UUID válido)  -- ADMIN
    'AA21AA21-AA21-AA21-AA21-AA21AA21AA21',  -- ALMACEN_MOVIMIENTOS_LISTAR
    1, 1, 1, 1, 1, 1
),
-- Entrada
(
    NEWID(),
    @cliente_id,
    '44444444-4444-4444-4444-444444444410',  -- ADMIN (UUID válido)  -- ADMIN
    'AA22AA22-AA22-AA22-AA22-AA22AA22AA22',  -- ALMACEN_MOVIMIENTOS_ENTRADA
    1, 1, 1, 1, 1, 1
),
-- Salida
(
    NEWID(),
    @cliente_id,
    '44444444-4444-4444-4444-444444444410',  -- ADMIN (UUID válido)  -- ADMIN
    'AA23AA23-AA23-AA23-AA23-AA23AA23AA23',  -- ALMACEN_MOVIMIENTOS_SALIDA
    1, 1, 1, 1, 1, 1
),
-- Menús de LOGISTICA
-- Rutas
(
    NEWID(),
    @cliente_id,
    '44444444-4444-4444-4444-444444444410',  -- ADMIN (UUID válido)  -- ADMIN
    'BB11BB11-BB11-BB11-BB11-BB11BB11BB11',  -- LOGISTICA_RUTAS_LISTAR
    1, 1, 1, 1, 1, 1
),
-- Nueva Ruta
(
    NEWID(),
    @cliente_id,
    '44444444-4444-4444-4444-444444444410',  -- ADMIN (UUID válido)  -- ADMIN
    'BB12BB12-BB12-BB12-BB12-BB12BB12BB12',  -- LOGISTICA_RUTAS_CREAR
    1, 1, 1, 1, 1, 1
),
-- Vehículos
(
    NEWID(),
    @cliente_id,
    '44444444-4444-4444-4444-444444444410',  -- ADMIN (UUID válido)  -- ADMIN
    'BB21BB21-BB21-BB21-BB21-BB21BB21BB21',  -- LOGISTICA_VEHICULOS_LISTAR
    1, 1, 1, 1, 1, 1
),
-- Nuevo Vehículo
(
    NEWID(),
    @cliente_id,
    '44444444-4444-4444-4444-444444444410',  -- ADMIN (UUID válido)  -- ADMIN
    'BB22BB22-BB22-BB22-BB22-BB22BB22BB22',  -- LOGISTICA_VEHICULOS_CREAR
    1, 1, 1, 1, 1, 1
);

-- Permisos para USER (solo lectura)
INSERT INTO rol_menu_permiso (
    permiso_id,
    cliente_id,
    rol_id,
    menu_id,
    puede_ver,
    puede_crear,
    puede_editar,
    puede_eliminar,
    puede_exportar,
    puede_imprimir
) VALUES
-- Menús de ALMACEN
(
    NEWID(),
    @cliente_id,
    '44444444-4444-4444-4444-444444444420',  -- USER (UUID válido)  -- USER
    'AA11AA11-AA11-AA11-AA11-AA11AA11AA11',  -- ALMACEN_PRODUCTOS_LISTAR
    1, 0, 0, 0, 0, 0
),
(
    NEWID(),
    @cliente_id,
    '44444444-4444-4444-4444-444444444420',  -- USER (UUID válido)  -- USER
    'AA21AA21-AA21-AA21-AA21-AA21AA21AA21',  -- ALMACEN_MOVIMIENTOS_LISTAR
    1, 0, 0, 0, 0, 0
),
-- Menús de LOGISTICA
(
    NEWID(),
    @cliente_id,
    '44444444-4444-4444-4444-444444444420',  -- USER (UUID válido)  -- USER
    'BB11BB11-BB11-BB11-BB11-BB11BB11BB11',  -- LOGISTICA_RUTAS_LISTAR
    1, 0, 0, 0, 0, 0
),
(
    NEWID(),
    @cliente_id,
    '44444444-4444-4444-4444-444444444420',  -- USER (UUID válido)  -- USER
    'BB21BB21-BB21-BB21-BB21-BB21BB21BB21',  -- LOGISTICA_VEHICULOS_LISTAR
    1, 0, 0, 0, 0, 0
);

PRINT 'Seed de BD dedicada GlobalLog completado exitosamente';
PRINT 'Usuarios creados: admin (ADMIN), user (USER)';
PRINT 'Permisos configurados para módulos: ALMACEN, LOGISTICA (NO PLANILLAS)';
GO
