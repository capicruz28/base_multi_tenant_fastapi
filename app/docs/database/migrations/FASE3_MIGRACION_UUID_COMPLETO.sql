-- ============================================================================
-- FASE 3: MIGRACIÓN COMPLETA DE PRIMARY KEYS A UUID
-- ============================================================================
-- 
-- Este script migra todas las Primary Keys de INT IDENTITY a UNIQUEIDENTIFIER
-- para habilitar sincronización escalable híbrida multi-tenant.
--
-- ⚠️ IMPORTANTE: Este script NO debe ejecutarse en producción sin:
--   1. Backup completo de la base de datos
--   2. Testing exhaustivo en ambiente de desarrollo
--   3. Plan de rollback documentado
--   4. Ventana de mantenimiento programada
--
-- ESTRATEGIA DE MIGRACIÓN:
--   1. Crear tablas de mapeo INT->UUID ANTES de eliminar columnas
--   2. Agregar columna UUID temporal
--   3. Generar UUIDs para registros existentes
--   4. Actualizar FKs usando tablas de mapeo
--   5. Eliminar FKs
--   6. Eliminar PKs INT
--   7. Eliminar columna INT antigua
--   8. Renombrar columna UUID a nombre original
--   9. Recrear PKs como UNIQUEIDENTIFIER
--   10. Recrear FKs
--   11. Agregar DEFAULT para nuevos registros
--
-- ORDEN DE MIGRACIÓN (respetar dependencias):
--   1. cliente (tabla raíz, sin dependencias)
--   2. usuario, rol, area_menu, menu, cliente_modulo (dependen de cliente)
--   3. usuario_rol, rol_menu_permiso, cliente_conexion, cliente_modulo_activo,
--      cliente_auth_config, federacion_identidad (dependen de tablas anteriores)
--   4. refresh_tokens, log_sincronizacion_usuario, auth_audit_log (dependen de usuario/cliente)
--
-- ============================================================================

-- ⚠️ CAMBIAR POR EL NOMBRE DE TU BASE DE DATOS
USE [tu_base_de_datos];
GO

BEGIN TRANSACTION;
GO

-- Variables para scripts dinámicos
DECLARE @sql NVARCHAR(MAX);
DECLARE @pk_name NVARCHAR(255);
DECLARE @fk_name NVARCHAR(255);
DECLARE @table_name NVARCHAR(255);

-- ============================================================================
-- PASO 1: TABLA cliente (raíz, sin dependencias)
-- ============================================================================

PRINT '========================================';
PRINT 'PASO 1: Migrando tabla: cliente';
PRINT '========================================';

-- 1.1. Crear tabla de mapeo INT->UUID ANTES de modificar
IF OBJECT_ID('tempdb..#cliente_id_map') IS NOT NULL DROP TABLE #cliente_id_map;
CREATE TABLE #cliente_id_map (
    cliente_id_int INT PRIMARY KEY,
    cliente_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #cliente_id_map (cliente_id_int, cliente_id_uuid)
SELECT cliente_id, NEWID() FROM cliente;
GO

-- 1.2. Agregar columna UUID temporal
ALTER TABLE cliente
ADD cliente_id_uuid UNIQUEIDENTIFIER NULL;
GO

-- 1.3. Actualizar con UUIDs del mapeo
UPDATE c
SET c.cliente_id_uuid = m.cliente_id_uuid
FROM cliente c
INNER JOIN #cliente_id_map m ON c.cliente_id = m.cliente_id_int;
GO

-- 1.4. Hacer la columna NOT NULL
ALTER TABLE cliente
ALTER COLUMN cliente_id_uuid UNIQUEIDENTIFIER NOT NULL;
GO

-- 1.5. Eliminar FKs que referencian cliente_id (dinámico)
DECLARE fk_cursor CURSOR FOR
SELECT fk.name, OBJECT_NAME(fk.parent_object_id)
FROM sys.foreign_keys fk
WHERE fk.referenced_object_id = OBJECT_ID('cliente');

OPEN fk_cursor;
FETCH NEXT FROM fk_cursor INTO @fk_name, @table_name;
WHILE @@FETCH_STATUS = 0
BEGIN
    SET @sql = 'ALTER TABLE ' + @table_name + ' DROP CONSTRAINT ' + @fk_name;
    EXEC sp_executesql @sql;
    PRINT '  FK eliminada: ' + @table_name + '.' + @fk_name;
    FETCH NEXT FROM fk_cursor INTO @fk_name, @table_name;
END
CLOSE fk_cursor;
DEALLOCATE fk_cursor;
GO

-- 1.6. Eliminar PK INT
SELECT @pk_name = name
FROM sys.key_constraints
WHERE type = 'PK' AND parent_object_id = OBJECT_ID('cliente');

IF @pk_name IS NOT NULL
BEGIN
    SET @sql = 'ALTER TABLE cliente DROP CONSTRAINT ' + @pk_name;
    EXEC sp_executesql @sql;
    PRINT '  PK eliminada: ' + @pk_name;
END
GO

-- 1.7. Eliminar columna INT antigua
ALTER TABLE cliente DROP COLUMN cliente_id;
GO

-- 1.8. Renombrar columna UUID
EXEC sp_rename 'cliente.cliente_id_uuid', 'cliente_id', 'COLUMN';
GO

-- 1.9. Recrear PK como UNIQUEIDENTIFIER
ALTER TABLE cliente
ADD CONSTRAINT PK_cliente PRIMARY KEY (cliente_id);
GO

-- 1.10. Agregar DEFAULT para nuevos registros
ALTER TABLE cliente
ADD CONSTRAINT DF_cliente_id DEFAULT NEWID() FOR cliente_id;
GO

PRINT '✅ Tabla cliente migrada exitosamente';
GO

-- ============================================================================
-- PASO 2: TABLA usuario
-- ============================================================================

PRINT '========================================';
PRINT 'PASO 2: Migrando tabla: usuario';
PRINT '========================================';

-- 2.1. Crear tabla de mapeo INT->UUID
IF OBJECT_ID('tempdb..#usuario_id_map') IS NOT NULL DROP TABLE #usuario_id_map;
CREATE TABLE #usuario_id_map (
    usuario_id_int INT PRIMARY KEY,
    usuario_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #usuario_id_map (usuario_id_int, usuario_id_uuid)
SELECT usuario_id, NEWID() FROM usuario;
GO

-- 2.2. Agregar columna UUID temporal
ALTER TABLE usuario
ADD usuario_id_uuid UNIQUEIDENTIFIER NULL;
GO

-- 2.3. Actualizar con UUIDs del mapeo
UPDATE u
SET u.usuario_id_uuid = m.usuario_id_uuid
FROM usuario u
INNER JOIN #usuario_id_map m ON u.usuario_id = m.usuario_id_int;
GO

-- 2.4. Actualizar FK cliente_id a UUID usando tabla de mapeo
UPDATE u
SET u.cliente_id = c.cliente_id_uuid
FROM usuario u
INNER JOIN #cliente_id_map c ON u.cliente_id = c.cliente_id_int;
GO

-- 2.5. Cambiar tipo de cliente_id a UNIQUEIDENTIFIER
ALTER TABLE usuario
ALTER COLUMN cliente_id UNIQUEIDENTIFIER NOT NULL;
GO

-- 2.6. Eliminar FKs que referencian usuario_id
DECLARE fk_cursor CURSOR FOR
SELECT fk.name, OBJECT_NAME(fk.parent_object_id)
FROM sys.foreign_keys fk
WHERE fk.referenced_object_id = OBJECT_ID('usuario');

OPEN fk_cursor;
FETCH NEXT FROM fk_cursor INTO @fk_name, @table_name;
WHILE @@FETCH_STATUS = 0
BEGIN
    SET @sql = 'ALTER TABLE ' + @table_name + ' DROP CONSTRAINT ' + @fk_name;
    EXEC sp_executesql @sql;
    PRINT '  FK eliminada: ' + @table_name + '.' + @fk_name;
    FETCH NEXT FROM fk_cursor INTO @fk_name, @table_name;
END
CLOSE fk_cursor;
DEALLOCATE fk_cursor;
GO

-- 2.7. Eliminar PK INT
SELECT @pk_name = name
FROM sys.key_constraints
WHERE type = 'PK' AND parent_object_id = OBJECT_ID('usuario');

IF @pk_name IS NOT NULL
BEGIN
    SET @sql = 'ALTER TABLE usuario DROP CONSTRAINT ' + @pk_name;
    EXEC sp_executesql @sql;
    PRINT '  PK eliminada: ' + @pk_name;
END
GO

-- 2.8. Eliminar columna INT antigua
ALTER TABLE usuario DROP COLUMN usuario_id;
GO

-- 2.9. Renombrar columna UUID
EXEC sp_rename 'usuario.usuario_id_uuid', 'usuario_id', 'COLUMN';
GO

-- 2.10. Recrear PK
ALTER TABLE usuario
ADD CONSTRAINT PK_usuario PRIMARY KEY (usuario_id);
GO

-- 2.11. Agregar DEFAULT
ALTER TABLE usuario
ADD CONSTRAINT DF_usuario_id DEFAULT NEWID() FOR usuario_id;
GO

-- 2.12. Recrear FK a cliente
ALTER TABLE usuario
ADD CONSTRAINT FK_usuario_cliente FOREIGN KEY (cliente_id)
    REFERENCES cliente(cliente_id) ON DELETE CASCADE;
GO

PRINT '✅ Tabla usuario migrada exitosamente';
GO

-- ============================================================================
-- PASO 3: TABLA rol
-- ============================================================================

PRINT '========================================';
PRINT 'PASO 3: Migrando tabla: rol';
PRINT '========================================';

-- 3.1. Crear tabla de mapeo INT->UUID
IF OBJECT_ID('tempdb..#rol_id_map') IS NOT NULL DROP TABLE #rol_id_map;
CREATE TABLE #rol_id_map (
    rol_id_int INT PRIMARY KEY,
    rol_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #rol_id_map (rol_id_int, rol_id_uuid)
SELECT rol_id, NEWID() FROM rol;
GO

-- 3.2. Agregar columna UUID temporal
ALTER TABLE rol
ADD rol_id_uuid UNIQUEIDENTIFIER NULL;
GO

-- 3.3. Actualizar con UUIDs del mapeo
UPDATE r
SET r.rol_id_uuid = m.rol_id_uuid
FROM rol r
INNER JOIN #rol_id_map m ON r.rol_id = m.rol_id_int;
GO

-- 3.4. Actualizar FK cliente_id a UUID
UPDATE r
SET r.cliente_id = c.cliente_id_uuid
FROM rol r
INNER JOIN #cliente_id_map c ON r.cliente_id = c.cliente_id_int;
GO

-- 3.5. Cambiar tipo de cliente_id a UNIQUEIDENTIFIER (puede ser NULL)
ALTER TABLE rol
ALTER COLUMN cliente_id UNIQUEIDENTIFIER NULL;
GO

-- 3.6. Eliminar FKs que referencian rol_id
DECLARE fk_cursor CURSOR FOR
SELECT fk.name, OBJECT_NAME(fk.parent_object_id)
FROM sys.foreign_keys fk
WHERE fk.referenced_object_id = OBJECT_ID('rol');

OPEN fk_cursor;
FETCH NEXT FROM fk_cursor INTO @fk_name, @table_name;
WHILE @@FETCH_STATUS = 0
BEGIN
    SET @sql = 'ALTER TABLE ' + @table_name + ' DROP CONSTRAINT ' + @fk_name;
    EXEC sp_executesql @sql;
    PRINT '  FK eliminada: ' + @table_name + '.' + @fk_name;
    FETCH NEXT FROM fk_cursor INTO @fk_name, @table_name;
END
CLOSE fk_cursor;
DEALLOCATE fk_cursor;
GO

-- 3.7. Eliminar PK INT
SELECT @pk_name = name
FROM sys.key_constraints
WHERE type = 'PK' AND parent_object_id = OBJECT_ID('rol');

IF @pk_name IS NOT NULL
BEGIN
    SET @sql = 'ALTER TABLE rol DROP CONSTRAINT ' + @pk_name;
    EXEC sp_executesql @sql;
    PRINT '  PK eliminada: ' + @pk_name;
END
GO

-- 3.8. Eliminar columna INT antigua
ALTER TABLE rol DROP COLUMN rol_id;
GO

-- 3.9. Renombrar columna UUID
EXEC sp_rename 'rol.rol_id_uuid', 'rol_id', 'COLUMN';
GO

-- 3.10. Recrear PK
ALTER TABLE rol
ADD CONSTRAINT PK_rol PRIMARY KEY (rol_id);
GO

-- 3.11. Agregar DEFAULT
ALTER TABLE rol
ADD CONSTRAINT DF_rol_id DEFAULT NEWID() FOR rol_id;
GO

-- 3.12. Recrear FK a cliente
ALTER TABLE rol
ADD CONSTRAINT FK_rol_cliente FOREIGN KEY (cliente_id)
    REFERENCES cliente(cliente_id) ON DELETE CASCADE;
GO

PRINT '✅ Tabla rol migrada exitosamente';
GO

-- ============================================================================
-- PASO 4: TABLA area_menu
-- ============================================================================

PRINT '========================================';
PRINT 'PASO 4: Migrando tabla: area_menu';
PRINT '========================================';

-- 4.1. Crear tabla de mapeo INT->UUID
IF OBJECT_ID('tempdb..#area_id_map') IS NOT NULL DROP TABLE #area_id_map;
CREATE TABLE #area_id_map (
    area_id_int INT PRIMARY KEY,
    area_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #area_id_map (area_id_int, area_id_uuid)
SELECT area_id, NEWID() FROM area_menu;
GO

-- 4.2. Agregar columna UUID temporal
ALTER TABLE area_menu
ADD area_id_uuid UNIQUEIDENTIFIER NULL;
GO

-- 4.3. Actualizar con UUIDs del mapeo
UPDATE a
SET a.area_id_uuid = m.area_id_uuid
FROM area_menu a
INNER JOIN #area_id_map m ON a.area_id = m.area_id_int;
GO

-- 4.4. Actualizar FK cliente_id a UUID
UPDATE a
SET a.cliente_id = c.cliente_id_uuid
FROM area_menu a
INNER JOIN #cliente_id_map c ON a.cliente_id = c.cliente_id_int;
GO

-- 4.5. Cambiar tipo de cliente_id a UNIQUEIDENTIFIER
ALTER TABLE area_menu
ALTER COLUMN cliente_id UNIQUEIDENTIFIER NULL;
GO

-- 4.6. Eliminar FKs que referencian area_id
DECLARE fk_cursor CURSOR FOR
SELECT fk.name, OBJECT_NAME(fk.parent_object_id)
FROM sys.foreign_keys fk
WHERE fk.referenced_object_id = OBJECT_ID('area_menu');

OPEN fk_cursor;
FETCH NEXT FROM fk_cursor INTO @fk_name, @table_name;
WHILE @@FETCH_STATUS = 0
BEGIN
    SET @sql = 'ALTER TABLE ' + @table_name + ' DROP CONSTRAINT ' + @fk_name;
    EXEC sp_executesql @sql;
    PRINT '  FK eliminada: ' + @table_name + '.' + @fk_name;
    FETCH NEXT FROM fk_cursor INTO @fk_name, @table_name;
END
CLOSE fk_cursor;
DEALLOCATE fk_cursor;
GO

-- 4.7. Eliminar PK INT
SELECT @pk_name = name
FROM sys.key_constraints
WHERE type = 'PK' AND parent_object_id = OBJECT_ID('area_menu');

IF @pk_name IS NOT NULL
BEGIN
    SET @sql = 'ALTER TABLE area_menu DROP CONSTRAINT ' + @pk_name;
    EXEC sp_executesql @sql;
    PRINT '  PK eliminada: ' + @pk_name;
END
GO

-- 4.8. Eliminar columna INT antigua
ALTER TABLE area_menu DROP COLUMN area_id;
GO

-- 4.9. Renombrar columna UUID
EXEC sp_rename 'area_menu.area_id_uuid', 'area_id', 'COLUMN';
GO

-- 4.10. Recrear PK
ALTER TABLE area_menu
ADD CONSTRAINT PK_area_menu PRIMARY KEY (area_id);
GO

-- 4.11. Agregar DEFAULT
ALTER TABLE area_menu
ADD CONSTRAINT DF_area_id DEFAULT NEWID() FOR area_id;
GO

-- 4.12. Recrear FK a cliente
ALTER TABLE area_menu
ADD CONSTRAINT FK_area_menu_cliente FOREIGN KEY (cliente_id)
    REFERENCES cliente(cliente_id) ON DELETE CASCADE;
GO

PRINT '✅ Tabla area_menu migrada exitosamente';
GO

-- ============================================================================
-- PASO 5: TABLA menu
-- ============================================================================

PRINT '========================================';
PRINT 'PASO 5: Migrando tabla: menu';
PRINT '========================================';

-- 5.1. Crear tabla de mapeo INT->UUID
IF OBJECT_ID('tempdb..#menu_id_map') IS NOT NULL DROP TABLE #menu_id_map;
CREATE TABLE #menu_id_map (
    menu_id_int INT PRIMARY KEY,
    menu_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #menu_id_map (menu_id_int, menu_id_uuid)
SELECT menu_id, NEWID() FROM menu;
GO

-- 5.2. Agregar columna UUID temporal
ALTER TABLE menu
ADD menu_id_uuid UNIQUEIDENTIFIER NULL;
GO

-- 5.3. Actualizar con UUIDs del mapeo
UPDATE m
SET m.menu_id_uuid = map.menu_id_uuid
FROM menu m
INNER JOIN #menu_id_map map ON m.menu_id = map.menu_id_int;
GO

-- 5.4. Actualizar FKs: cliente_id, area_id, padre_menu_id
UPDATE m
SET m.cliente_id = c.cliente_id_uuid,
    m.area_id = a.area_id_uuid,
    m.padre_menu_id = p.menu_id_uuid
FROM menu m
LEFT JOIN #cliente_id_map c ON m.cliente_id = c.cliente_id_int
LEFT JOIN #area_id_map a ON m.area_id = a.area_id_int
LEFT JOIN #menu_id_map p ON m.padre_menu_id = p.menu_id_int;
GO

-- 5.5. Cambiar tipos a UNIQUEIDENTIFIER
ALTER TABLE menu
ALTER COLUMN cliente_id UNIQUEIDENTIFIER NULL;
GO

ALTER TABLE menu
ALTER COLUMN area_id UNIQUEIDENTIFIER NULL;
GO

ALTER TABLE menu
ALTER COLUMN padre_menu_id UNIQUEIDENTIFIER NULL;
GO

-- 5.6. Eliminar FKs que referencian menu_id
DECLARE fk_cursor CURSOR FOR
SELECT fk.name, OBJECT_NAME(fk.parent_object_id)
FROM sys.foreign_keys fk
WHERE fk.referenced_object_id = OBJECT_ID('menu');

OPEN fk_cursor;
FETCH NEXT FROM fk_cursor INTO @fk_name, @table_name;
WHILE @@FETCH_STATUS = 0
BEGIN
    SET @sql = 'ALTER TABLE ' + @table_name + ' DROP CONSTRAINT ' + @fk_name;
    EXEC sp_executesql @sql;
    PRINT '  FK eliminada: ' + @table_name + '.' + @fk_name;
    FETCH NEXT FROM fk_cursor INTO @fk_name, @table_name;
END
CLOSE fk_cursor;
DEALLOCATE fk_cursor;
GO

-- 5.7. Eliminar PK INT
SELECT @pk_name = name
FROM sys.key_constraints
WHERE type = 'PK' AND parent_object_id = OBJECT_ID('menu');

IF @pk_name IS NOT NULL
BEGIN
    SET @sql = 'ALTER TABLE menu DROP CONSTRAINT ' + @pk_name;
    EXEC sp_executesql @sql;
    PRINT '  PK eliminada: ' + @pk_name;
END
GO

-- 5.8. Eliminar columna INT antigua
ALTER TABLE menu DROP COLUMN menu_id;
GO

-- 5.9. Renombrar columna UUID
EXEC sp_rename 'menu.menu_id_uuid', 'menu_id', 'COLUMN';
GO

-- 5.10. Recrear PK
ALTER TABLE menu
ADD CONSTRAINT PK_menu PRIMARY KEY (menu_id);
GO

-- 5.11. Agregar DEFAULT
ALTER TABLE menu
ADD CONSTRAINT DF_menu_id DEFAULT NEWID() FOR menu_id;
GO

-- 5.12. Recrear FKs
ALTER TABLE menu
ADD CONSTRAINT FK_menu_cliente FOREIGN KEY (cliente_id)
    REFERENCES cliente(cliente_id) ON DELETE CASCADE;
GO

ALTER TABLE menu
ADD CONSTRAINT FK_menu_area FOREIGN KEY (area_id)
    REFERENCES area_menu(area_id) ON DELETE SET NULL;
GO

ALTER TABLE menu
ADD CONSTRAINT FK_menu_padre FOREIGN KEY (padre_menu_id)
    REFERENCES menu(menu_id) ON DELETE NO ACTION;
GO

PRINT '✅ Tabla menu migrada exitosamente';
GO

-- ============================================================================
-- PASO 6: TABLA cliente_modulo
-- ============================================================================

PRINT '========================================';
PRINT 'PASO 6: Migrando tabla: cliente_modulo';
PRINT '========================================';

-- 6.1. Crear tabla de mapeo INT->UUID
IF OBJECT_ID('tempdb..#modulo_id_map') IS NOT NULL DROP TABLE #modulo_id_map;
CREATE TABLE #modulo_id_map (
    modulo_id_int INT PRIMARY KEY,
    modulo_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #modulo_id_map (modulo_id_int, modulo_id_uuid)
SELECT modulo_id, NEWID() FROM cliente_modulo;
GO

-- 6.2. Agregar columna UUID temporal
ALTER TABLE cliente_modulo
ADD modulo_id_uuid UNIQUEIDENTIFIER NULL;
GO

-- 6.3. Actualizar con UUIDs del mapeo
UPDATE cm
SET cm.modulo_id_uuid = m.modulo_id_uuid
FROM cliente_modulo cm
INNER JOIN #modulo_id_map m ON cm.modulo_id = m.modulo_id_int;
GO

-- 6.4. Eliminar FKs que referencian modulo_id
DECLARE fk_cursor CURSOR FOR
SELECT fk.name, OBJECT_NAME(fk.parent_object_id)
FROM sys.foreign_keys fk
WHERE fk.referenced_object_id = OBJECT_ID('cliente_modulo');

OPEN fk_cursor;
FETCH NEXT FROM fk_cursor INTO @fk_name, @table_name;
WHILE @@FETCH_STATUS = 0
BEGIN
    SET @sql = 'ALTER TABLE ' + @table_name + ' DROP CONSTRAINT ' + @fk_name;
    EXEC sp_executesql @sql;
    PRINT '  FK eliminada: ' + @table_name + '.' + @fk_name;
    FETCH NEXT FROM fk_cursor INTO @fk_name, @table_name;
END
CLOSE fk_cursor;
DEALLOCATE fk_cursor;
GO

-- 6.5. Eliminar PK INT
SELECT @pk_name = name
FROM sys.key_constraints
WHERE type = 'PK' AND parent_object_id = OBJECT_ID('cliente_modulo');

IF @pk_name IS NOT NULL
BEGIN
    SET @sql = 'ALTER TABLE cliente_modulo DROP CONSTRAINT ' + @pk_name;
    EXEC sp_executesql @sql;
    PRINT '  PK eliminada: ' + @pk_name;
END
GO

-- 6.6. Eliminar columna INT antigua
ALTER TABLE cliente_modulo DROP COLUMN modulo_id;
GO

-- 6.7. Renombrar columna UUID
EXEC sp_rename 'cliente_modulo.modulo_id_uuid', 'modulo_id', 'COLUMN';
GO

-- 6.8. Recrear PK
ALTER TABLE cliente_modulo
ADD CONSTRAINT PK_cliente_modulo PRIMARY KEY (modulo_id);
GO

-- 6.9. Agregar DEFAULT
ALTER TABLE cliente_modulo
ADD CONSTRAINT DF_modulo_id DEFAULT NEWID() FOR modulo_id;
GO

PRINT '✅ Tabla cliente_modulo migrada exitosamente';
GO

-- ============================================================================
-- PASO 7: TABLA usuario_rol
-- ============================================================================

PRINT '========================================';
PRINT 'PASO 7: Migrando tabla: usuario_rol';
PRINT '========================================';

-- 7.1. Crear tabla de mapeo INT->UUID
IF OBJECT_ID('tempdb..#usuario_rol_id_map') IS NOT NULL DROP TABLE #usuario_rol_id_map;
CREATE TABLE #usuario_rol_id_map (
    usuario_rol_id_int INT PRIMARY KEY,
    usuario_rol_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #usuario_rol_id_map (usuario_rol_id_int, usuario_rol_id_uuid)
SELECT usuario_rol_id, NEWID() FROM usuario_rol;
GO

-- 7.2. Agregar columna UUID temporal
ALTER TABLE usuario_rol
ADD usuario_rol_id_uuid UNIQUEIDENTIFIER NULL;
GO

-- 7.3. Actualizar con UUIDs del mapeo
UPDATE ur
SET ur.usuario_rol_id_uuid = m.usuario_rol_id_uuid
FROM usuario_rol ur
INNER JOIN #usuario_rol_id_map m ON ur.usuario_rol_id = m.usuario_rol_id_int;
GO

-- 7.4. Actualizar FKs: usuario_id, rol_id, cliente_id, asignado_por_usuario_id
UPDATE ur
SET ur.usuario_id = u.usuario_id_uuid,
    ur.rol_id = r.rol_id_uuid,
    ur.cliente_id = c.cliente_id_uuid,
    ur.asignado_por_usuario_id = a.usuario_id_uuid
FROM usuario_rol ur
INNER JOIN #usuario_id_map u ON ur.usuario_id = u.usuario_id_int
INNER JOIN #rol_id_map r ON ur.rol_id = r.rol_id_int
INNER JOIN #cliente_id_map c ON ur.cliente_id = c.cliente_id_int
LEFT JOIN #usuario_id_map a ON ur.asignado_por_usuario_id = a.usuario_id_int;
GO

-- 7.5. Cambiar tipos a UNIQUEIDENTIFIER
ALTER TABLE usuario_rol
ALTER COLUMN usuario_id UNIQUEIDENTIFIER NOT NULL;
GO

ALTER TABLE usuario_rol
ALTER COLUMN rol_id UNIQUEIDENTIFIER NOT NULL;
GO

ALTER TABLE usuario_rol
ALTER COLUMN cliente_id UNIQUEIDENTIFIER NOT NULL;
GO

ALTER TABLE usuario_rol
ALTER COLUMN asignado_por_usuario_id UNIQUEIDENTIFIER NULL;
GO

-- 7.6. Eliminar PK INT
SELECT @pk_name = name
FROM sys.key_constraints
WHERE type = 'PK' AND parent_object_id = OBJECT_ID('usuario_rol');

IF @pk_name IS NOT NULL
BEGIN
    SET @sql = 'ALTER TABLE usuario_rol DROP CONSTRAINT ' + @pk_name;
    EXEC sp_executesql @sql;
    PRINT '  PK eliminada: ' + @pk_name;
END
GO

-- 7.7. Eliminar columna INT antigua
ALTER TABLE usuario_rol DROP COLUMN usuario_rol_id;
GO

-- 7.8. Renombrar columna UUID
EXEC sp_rename 'usuario_rol.usuario_rol_id_uuid', 'usuario_rol_id', 'COLUMN';
GO

-- 7.9. Recrear PK
ALTER TABLE usuario_rol
ADD CONSTRAINT PK_usuario_rol PRIMARY KEY (usuario_rol_id);
GO

-- 7.10. Agregar DEFAULT
ALTER TABLE usuario_rol
ADD CONSTRAINT DF_usuario_rol_id DEFAULT NEWID() FOR usuario_rol_id;
GO

-- 7.11. Recrear FKs
ALTER TABLE usuario_rol
ADD CONSTRAINT FK_usuario_rol_usuario FOREIGN KEY (usuario_id)
    REFERENCES usuario(usuario_id) ON DELETE CASCADE;
GO

ALTER TABLE usuario_rol
ADD CONSTRAINT FK_usuario_rol_rol FOREIGN KEY (rol_id)
    REFERENCES rol(rol_id) ON DELETE CASCADE;
GO

ALTER TABLE usuario_rol
ADD CONSTRAINT FK_usuario_rol_cliente FOREIGN KEY (cliente_id)
    REFERENCES cliente(cliente_id) ON DELETE NO ACTION;
GO

PRINT '✅ Tabla usuario_rol migrada exitosamente';
GO

-- ============================================================================
-- PASO 8: TABLA rol_menu_permiso
-- ============================================================================

PRINT '========================================';
PRINT 'PASO 8: Migrando tabla: rol_menu_permiso';
PRINT '========================================';

-- 8.1. Crear tabla de mapeo INT->UUID
IF OBJECT_ID('tempdb..#permiso_id_map') IS NOT NULL DROP TABLE #permiso_id_map;
CREATE TABLE #permiso_id_map (
    permiso_id_int INT PRIMARY KEY,
    permiso_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #permiso_id_map (permiso_id_int, permiso_id_uuid)
SELECT permiso_id, NEWID() FROM rol_menu_permiso;
GO

-- 8.2. Agregar columna UUID temporal
ALTER TABLE rol_menu_permiso
ADD permiso_id_uuid UNIQUEIDENTIFIER NULL;
GO

-- 8.3. Actualizar con UUIDs del mapeo
UPDATE rmp
SET rmp.permiso_id_uuid = m.permiso_id_uuid
FROM rol_menu_permiso rmp
INNER JOIN #permiso_id_map m ON rmp.permiso_id = m.permiso_id_int;
GO

-- 8.4. Actualizar FKs: rol_id, menu_id, cliente_id
UPDATE rmp
SET rmp.rol_id = r.rol_id_uuid,
    rmp.menu_id = m.menu_id_uuid,
    rmp.cliente_id = c.cliente_id_uuid
FROM rol_menu_permiso rmp
INNER JOIN #rol_id_map r ON rmp.rol_id = r.rol_id_int
INNER JOIN #menu_id_map m ON rmp.menu_id = m.menu_id_int
INNER JOIN #cliente_id_map c ON rmp.cliente_id = c.cliente_id_int;
GO

-- 8.5. Cambiar tipos a UNIQUEIDENTIFIER
ALTER TABLE rol_menu_permiso
ALTER COLUMN rol_id UNIQUEIDENTIFIER NOT NULL;
GO

ALTER TABLE rol_menu_permiso
ALTER COLUMN menu_id UNIQUEIDENTIFIER NOT NULL;
GO

ALTER TABLE rol_menu_permiso
ALTER COLUMN cliente_id UNIQUEIDENTIFIER NOT NULL;
GO

-- 8.6. Eliminar PK INT
SELECT @pk_name = name
FROM sys.key_constraints
WHERE type = 'PK' AND parent_object_id = OBJECT_ID('rol_menu_permiso');

IF @pk_name IS NOT NULL
BEGIN
    SET @sql = 'ALTER TABLE rol_menu_permiso DROP CONSTRAINT ' + @pk_name;
    EXEC sp_executesql @sql;
    PRINT '  PK eliminada: ' + @pk_name;
END
GO

-- 8.7. Eliminar columna INT antigua
ALTER TABLE rol_menu_permiso DROP COLUMN permiso_id;
GO

-- 8.8. Renombrar columna UUID
EXEC sp_rename 'rol_menu_permiso.permiso_id_uuid', 'permiso_id', 'COLUMN';
GO

-- 8.9. Recrear PK
ALTER TABLE rol_menu_permiso
ADD CONSTRAINT PK_rol_menu_permiso PRIMARY KEY (permiso_id);
GO

-- 8.10. Agregar DEFAULT
ALTER TABLE rol_menu_permiso
ADD CONSTRAINT DF_permiso_id DEFAULT NEWID() FOR permiso_id;
GO

-- 8.11. Recrear FKs
ALTER TABLE rol_menu_permiso
ADD CONSTRAINT FK_permiso_rol FOREIGN KEY (rol_id)
    REFERENCES rol(rol_id) ON DELETE CASCADE;
GO

ALTER TABLE rol_menu_permiso
ADD CONSTRAINT FK_permiso_menu FOREIGN KEY (menu_id)
    REFERENCES menu(menu_id) ON DELETE CASCADE;
GO

ALTER TABLE rol_menu_permiso
ADD CONSTRAINT FK_permiso_cliente FOREIGN KEY (cliente_id)
    REFERENCES cliente(cliente_id) ON DELETE NO ACTION;
GO

PRINT '✅ Tabla rol_menu_permiso migrada exitosamente';
GO

-- ============================================================================
-- PASO 9: TABLA refresh_tokens
-- ============================================================================

PRINT '========================================';
PRINT 'PASO 9: Migrando tabla: refresh_tokens';
PRINT '========================================';

-- 9.1. Crear tabla de mapeo INT->UUID
IF OBJECT_ID('tempdb..#token_id_map') IS NOT NULL DROP TABLE #token_id_map;
CREATE TABLE #token_id_map (
    token_id_int INT PRIMARY KEY,
    token_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #token_id_map (token_id_int, token_id_uuid)
SELECT token_id, NEWID() FROM refresh_tokens;
GO

-- 9.2. Agregar columna UUID temporal
ALTER TABLE refresh_tokens
ADD token_id_uuid UNIQUEIDENTIFIER NULL;
GO

-- 9.3. Actualizar con UUIDs del mapeo
UPDATE rt
SET rt.token_id_uuid = m.token_id_uuid
FROM refresh_tokens rt
INNER JOIN #token_id_map m ON rt.token_id = m.token_id_int;
GO

-- 9.4. Actualizar FKs: usuario_id, cliente_id
UPDATE rt
SET rt.usuario_id = u.usuario_id_uuid,
    rt.cliente_id = c.cliente_id_uuid
FROM refresh_tokens rt
INNER JOIN #usuario_id_map u ON rt.usuario_id = u.usuario_id_int
INNER JOIN #cliente_id_map c ON rt.cliente_id = c.cliente_id_int;
GO

-- 9.5. Cambiar tipos a UNIQUEIDENTIFIER
ALTER TABLE refresh_tokens
ALTER COLUMN usuario_id UNIQUEIDENTIFIER NOT NULL;
GO

ALTER TABLE refresh_tokens
ALTER COLUMN cliente_id UNIQUEIDENTIFIER NOT NULL;
GO

-- 9.6. Eliminar PK INT
SELECT @pk_name = name
FROM sys.key_constraints
WHERE type = 'PK' AND parent_object_id = OBJECT_ID('refresh_tokens');

IF @pk_name IS NOT NULL
BEGIN
    SET @sql = 'ALTER TABLE refresh_tokens DROP CONSTRAINT ' + @pk_name;
    EXEC sp_executesql @sql;
    PRINT '  PK eliminada: ' + @pk_name;
END
GO

-- 9.7. Eliminar columna INT antigua
ALTER TABLE refresh_tokens DROP COLUMN token_id;
GO

-- 9.8. Renombrar columna UUID
EXEC sp_rename 'refresh_tokens.token_id_uuid', 'token_id', 'COLUMN';
GO

-- 9.9. Recrear PK
ALTER TABLE refresh_tokens
ADD CONSTRAINT PK_refresh_tokens PRIMARY KEY (token_id);
GO

-- 9.10. Agregar DEFAULT
ALTER TABLE refresh_tokens
ADD CONSTRAINT DF_token_id DEFAULT NEWID() FOR token_id;
GO

-- 9.11. Recrear FKs
ALTER TABLE refresh_tokens
ADD CONSTRAINT FK_refresh_token_cliente FOREIGN KEY (cliente_id)
    REFERENCES cliente(cliente_id) ON DELETE CASCADE;
GO

ALTER TABLE refresh_tokens
ADD CONSTRAINT FK_refresh_token_usuario FOREIGN KEY (usuario_id)
    REFERENCES usuario(usuario_id) ON DELETE CASCADE;
GO

PRINT '✅ Tabla refresh_tokens migrada exitosamente';
GO

-- ============================================================================
-- PASO 10: TABLA cliente_conexion
-- ============================================================================

PRINT '========================================';
PRINT 'PASO 10: Migrando tabla: cliente_conexion';
PRINT '========================================';

-- 10.1. Crear tabla de mapeo INT->UUID
IF OBJECT_ID('tempdb..#conexion_id_map') IS NOT NULL DROP TABLE #conexion_id_map;
CREATE TABLE #conexion_id_map (
    conexion_id_int INT PRIMARY KEY,
    conexion_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #conexion_id_map (conexion_id_int, conexion_id_uuid)
SELECT conexion_id, NEWID() FROM cliente_conexion;
GO

-- 10.2. Agregar columna UUID temporal
ALTER TABLE cliente_conexion
ADD conexion_id_uuid UNIQUEIDENTIFIER NULL;
GO

-- 10.3. Actualizar con UUIDs del mapeo
UPDATE cc
SET cc.conexion_id_uuid = m.conexion_id_uuid
FROM cliente_conexion cc
INNER JOIN #conexion_id_map m ON cc.conexion_id = m.conexion_id_int;
GO

-- 10.4. Actualizar FK cliente_id
UPDATE cc
SET cc.cliente_id = c.cliente_id_uuid
FROM cliente_conexion cc
INNER JOIN #cliente_id_map c ON cc.cliente_id = c.cliente_id_int;
GO

-- 10.5. Cambiar tipo a UNIQUEIDENTIFIER
ALTER TABLE cliente_conexion
ALTER COLUMN cliente_id UNIQUEIDENTIFIER NOT NULL;
GO

-- 10.6. Eliminar PK INT
SELECT @pk_name = name
FROM sys.key_constraints
WHERE type = 'PK' AND parent_object_id = OBJECT_ID('cliente_conexion');

IF @pk_name IS NOT NULL
BEGIN
    SET @sql = 'ALTER TABLE cliente_conexion DROP CONSTRAINT ' + @pk_name;
    EXEC sp_executesql @sql;
    PRINT '  PK eliminada: ' + @pk_name;
END
GO

-- 10.7. Eliminar columna INT antigua
ALTER TABLE cliente_conexion DROP COLUMN conexion_id;
GO

-- 10.8. Renombrar columna UUID
EXEC sp_rename 'cliente_conexion.conexion_id_uuid', 'conexion_id', 'COLUMN';
GO

-- 10.9. Recrear PK
ALTER TABLE cliente_conexion
ADD CONSTRAINT PK_cliente_conexion PRIMARY KEY (conexion_id);
GO

-- 10.10. Agregar DEFAULT
ALTER TABLE cliente_conexion
ADD CONSTRAINT DF_conexion_id DEFAULT NEWID() FOR conexion_id;
GO

-- 10.11. Recrear FK
ALTER TABLE cliente_conexion
ADD CONSTRAINT FK_conexion_cliente FOREIGN KEY (cliente_id)
    REFERENCES cliente(cliente_id) ON DELETE CASCADE;
GO

PRINT '✅ Tabla cliente_conexion migrada exitosamente';
GO

-- ============================================================================
-- PASO 11: TABLA cliente_modulo_activo
-- ============================================================================

PRINT '========================================';
PRINT 'PASO 11: Migrando tabla: cliente_modulo_activo';
PRINT '========================================';

-- 11.1. Crear tabla de mapeo INT->UUID
IF OBJECT_ID('tempdb..#cliente_modulo_activo_id_map') IS NOT NULL DROP TABLE #cliente_modulo_activo_id_map;
CREATE TABLE #cliente_modulo_activo_id_map (
    cliente_modulo_activo_id_int INT PRIMARY KEY,
    cliente_modulo_activo_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #cliente_modulo_activo_id_map (cliente_modulo_activo_id_int, cliente_modulo_activo_id_uuid)
SELECT cliente_modulo_activo_id, NEWID() FROM cliente_modulo_activo;
GO

-- 11.2. Agregar columna UUID temporal
ALTER TABLE cliente_modulo_activo
ADD cliente_modulo_activo_id_uuid UNIQUEIDENTIFIER NULL;
GO

-- 11.3. Actualizar con UUIDs del mapeo
UPDATE cma
SET cma.cliente_modulo_activo_id_uuid = m.cliente_modulo_activo_id_uuid
FROM cliente_modulo_activo cma
INNER JOIN #cliente_modulo_activo_id_map m ON cma.cliente_modulo_activo_id = m.cliente_modulo_activo_id_int;
GO

-- 11.4. Actualizar FKs: cliente_id, modulo_id
UPDATE cma
SET cma.cliente_id = c.cliente_id_uuid,
    cma.modulo_id = m.modulo_id_uuid
FROM cliente_modulo_activo cma
INNER JOIN #cliente_id_map c ON cma.cliente_id = c.cliente_id_int
INNER JOIN #modulo_id_map m ON cma.modulo_id = m.modulo_id_int;
GO

-- 11.5. Cambiar tipos a UNIQUEIDENTIFIER
ALTER TABLE cliente_modulo_activo
ALTER COLUMN cliente_id UNIQUEIDENTIFIER NOT NULL;
GO

ALTER TABLE cliente_modulo_activo
ALTER COLUMN modulo_id UNIQUEIDENTIFIER NOT NULL;
GO

-- 11.6. Eliminar PK INT
SELECT @pk_name = name
FROM sys.key_constraints
WHERE type = 'PK' AND parent_object_id = OBJECT_ID('cliente_modulo_activo');

IF @pk_name IS NOT NULL
BEGIN
    SET @sql = 'ALTER TABLE cliente_modulo_activo DROP CONSTRAINT ' + @pk_name;
    EXEC sp_executesql @sql;
    PRINT '  PK eliminada: ' + @pk_name;
END
GO

-- 11.7. Eliminar columna INT antigua
ALTER TABLE cliente_modulo_activo DROP COLUMN cliente_modulo_activo_id;
GO

-- 11.8. Renombrar columna UUID
EXEC sp_rename 'cliente_modulo_activo.cliente_modulo_activo_id_uuid', 'cliente_modulo_activo_id', 'COLUMN';
GO

-- 11.9. Recrear PK
ALTER TABLE cliente_modulo_activo
ADD CONSTRAINT PK_cliente_modulo_activo PRIMARY KEY (cliente_modulo_activo_id);
GO

-- 11.10. Agregar DEFAULT
ALTER TABLE cliente_modulo_activo
ADD CONSTRAINT DF_cliente_modulo_activo_id DEFAULT NEWID() FOR cliente_modulo_activo_id;
GO

-- 11.11. Recrear FKs
ALTER TABLE cliente_modulo_activo
ADD CONSTRAINT FK_modulo_activo_cliente FOREIGN KEY (cliente_id)
    REFERENCES cliente(cliente_id) ON DELETE CASCADE;
GO

ALTER TABLE cliente_modulo_activo
ADD CONSTRAINT FK_modulo_activo_modulo FOREIGN KEY (modulo_id)
    REFERENCES cliente_modulo(modulo_id) ON DELETE CASCADE;
GO

PRINT '✅ Tabla cliente_modulo_activo migrada exitosamente';
GO

-- ============================================================================
-- PASO 12: TABLA cliente_auth_config
-- ============================================================================

PRINT '========================================';
PRINT 'PASO 12: Migrando tabla: cliente_auth_config';
PRINT '========================================';

-- 12.1. Crear tabla de mapeo INT->UUID
IF OBJECT_ID('tempdb..#config_id_map') IS NOT NULL DROP TABLE #config_id_map;
CREATE TABLE #config_id_map (
    config_id_int INT PRIMARY KEY,
    config_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #config_id_map (config_id_int, config_id_uuid)
SELECT config_id, NEWID() FROM cliente_auth_config;
GO

-- 12.2. Agregar columna UUID temporal
ALTER TABLE cliente_auth_config
ADD config_id_uuid UNIQUEIDENTIFIER NULL;
GO

-- 12.3. Actualizar con UUIDs del mapeo
UPDATE cac
SET cac.config_id_uuid = m.config_id_uuid
FROM cliente_auth_config cac
INNER JOIN #config_id_map m ON cac.config_id = m.config_id_int;
GO

-- 12.4. Actualizar FK cliente_id
UPDATE cac
SET cac.cliente_id = c.cliente_id_uuid
FROM cliente_auth_config cac
INNER JOIN #cliente_id_map c ON cac.cliente_id = c.cliente_id_int;
GO

-- 12.5. Cambiar tipo a UNIQUEIDENTIFIER
ALTER TABLE cliente_auth_config
ALTER COLUMN cliente_id UNIQUEIDENTIFIER NOT NULL;
GO

-- 12.6. Eliminar PK INT
SELECT @pk_name = name
FROM sys.key_constraints
WHERE type = 'PK' AND parent_object_id = OBJECT_ID('cliente_auth_config');

IF @pk_name IS NOT NULL
BEGIN
    SET @sql = 'ALTER TABLE cliente_auth_config DROP CONSTRAINT ' + @pk_name;
    EXEC sp_executesql @sql;
    PRINT '  PK eliminada: ' + @pk_name;
END
GO

-- 12.7. Eliminar columna INT antigua
ALTER TABLE cliente_auth_config DROP COLUMN config_id;
GO

-- 12.8. Renombrar columna UUID
EXEC sp_rename 'cliente_auth_config.config_id_uuid', 'config_id', 'COLUMN';
GO

-- 12.9. Recrear PK
ALTER TABLE cliente_auth_config
ADD CONSTRAINT PK_cliente_auth_config PRIMARY KEY (config_id);
GO

-- 12.10. Agregar DEFAULT
ALTER TABLE cliente_auth_config
ADD CONSTRAINT DF_config_id DEFAULT NEWID() FOR config_id;
GO

-- 12.11. Recrear FK
ALTER TABLE cliente_auth_config
ADD CONSTRAINT FK_auth_config_cliente FOREIGN KEY (cliente_id)
    REFERENCES cliente(cliente_id) ON DELETE CASCADE;
GO

PRINT '✅ Tabla cliente_auth_config migrada exitosamente';
GO

-- ============================================================================
-- PASO 13: TABLA federacion_identidad
-- ============================================================================

PRINT '========================================';
PRINT 'PASO 13: Migrando tabla: federacion_identidad';
PRINT '========================================';

-- 13.1. Crear tabla de mapeo INT->UUID
IF OBJECT_ID('tempdb..#federacion_id_map') IS NOT NULL DROP TABLE #federacion_id_map;
CREATE TABLE #federacion_id_map (
    federacion_id_int INT PRIMARY KEY,
    federacion_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #federacion_id_map (federacion_id_int, federacion_id_uuid)
SELECT federacion_id, NEWID() FROM federacion_identidad;
GO

-- 13.2. Agregar columna UUID temporal
ALTER TABLE federacion_identidad
ADD federacion_id_uuid UNIQUEIDENTIFIER NULL;
GO

-- 13.3. Actualizar con UUIDs del mapeo
UPDATE fi
SET fi.federacion_id_uuid = m.federacion_id_uuid
FROM federacion_identidad fi
INNER JOIN #federacion_id_map m ON fi.federacion_id = m.federacion_id_int;
GO

-- 13.4. Actualizar FK cliente_id
UPDATE fi
SET fi.cliente_id = c.cliente_id_uuid
FROM federacion_identidad fi
INNER JOIN #cliente_id_map c ON fi.cliente_id = c.cliente_id_int;
GO

-- 13.5. Cambiar tipo a UNIQUEIDENTIFIER
ALTER TABLE federacion_identidad
ALTER COLUMN cliente_id UNIQUEIDENTIFIER NOT NULL;
GO

-- 13.6. Eliminar PK INT
SELECT @pk_name = name
FROM sys.key_constraints
WHERE type = 'PK' AND parent_object_id = OBJECT_ID('federacion_identidad');

IF @pk_name IS NOT NULL
BEGIN
    SET @sql = 'ALTER TABLE federacion_identidad DROP CONSTRAINT ' + @pk_name;
    EXEC sp_executesql @sql;
    PRINT '  PK eliminada: ' + @pk_name;
END
GO

-- 13.7. Eliminar columna INT antigua
ALTER TABLE federacion_identidad DROP COLUMN federacion_id;
GO

-- 13.8. Renombrar columna UUID
EXEC sp_rename 'federacion_identidad.federacion_id_uuid', 'federacion_id', 'COLUMN';
GO

-- 13.9. Recrear PK
ALTER TABLE federacion_identidad
ADD CONSTRAINT PK_federacion_identidad PRIMARY KEY (federacion_id);
GO

-- 13.10. Agregar DEFAULT
ALTER TABLE federacion_identidad
ADD CONSTRAINT DF_federacion_id DEFAULT NEWID() FOR federacion_id;
GO

-- 13.11. Recrear FK
ALTER TABLE federacion_identidad
ADD CONSTRAINT FK_federacion_cliente FOREIGN KEY (cliente_id)
    REFERENCES cliente(cliente_id) ON DELETE CASCADE;
GO

PRINT '✅ Tabla federacion_identidad migrada exitosamente';
GO

-- ============================================================================
-- PASO 14: TABLA log_sincronizacion_usuario
-- ============================================================================

PRINT '========================================';
PRINT 'PASO 14: Migrando tabla: log_sincronizacion_usuario';
PRINT '========================================';

-- 14.1. Crear tabla de mapeo INT->UUID
IF OBJECT_ID('tempdb..#log_sync_id_map') IS NOT NULL DROP TABLE #log_sync_id_map;
CREATE TABLE #log_sync_id_map (
    log_id_int INT PRIMARY KEY,
    log_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #log_sync_id_map (log_id_int, log_id_uuid)
SELECT log_id, NEWID() FROM log_sincronizacion_usuario;
GO

-- 14.2. Agregar columna UUID temporal
ALTER TABLE log_sincronizacion_usuario
ADD log_id_uuid UNIQUEIDENTIFIER NULL;
GO

-- 14.3. Actualizar con UUIDs del mapeo
UPDATE lsu
SET lsu.log_id_uuid = m.log_id_uuid
FROM log_sincronizacion_usuario lsu
INNER JOIN #log_sync_id_map m ON lsu.log_id = m.log_id_int;
GO

-- 14.4. Actualizar FKs: usuario_id, cliente_origen_id, cliente_destino_id, usuario_ejecutor_id
UPDATE lsu
SET lsu.usuario_id = u.usuario_id_uuid,
    lsu.cliente_origen_id = co.cliente_id_uuid,
    lsu.cliente_destino_id = cd.cliente_id_uuid,
    lsu.usuario_ejecutor_id = ue.usuario_id_uuid
FROM log_sincronizacion_usuario lsu
LEFT JOIN #usuario_id_map u ON lsu.usuario_id = u.usuario_id_int
LEFT JOIN #cliente_id_map co ON lsu.cliente_origen_id = co.cliente_id_int
LEFT JOIN #cliente_id_map cd ON lsu.cliente_destino_id = cd.cliente_id_int
LEFT JOIN #usuario_id_map ue ON lsu.usuario_ejecutor_id = ue.usuario_id_int;
GO

-- 14.5. Cambiar tipos a UNIQUEIDENTIFIER
ALTER TABLE log_sincronizacion_usuario
ALTER COLUMN usuario_id UNIQUEIDENTIFIER NULL;
GO

ALTER TABLE log_sincronizacion_usuario
ALTER COLUMN cliente_origen_id UNIQUEIDENTIFIER NULL;
GO

ALTER TABLE log_sincronizacion_usuario
ALTER COLUMN cliente_destino_id UNIQUEIDENTIFIER NULL;
GO

ALTER TABLE log_sincronizacion_usuario
ALTER COLUMN usuario_ejecutor_id UNIQUEIDENTIFIER NULL;
GO

-- 14.6. Eliminar PK INT
SELECT @pk_name = name
FROM sys.key_constraints
WHERE type = 'PK' AND parent_object_id = OBJECT_ID('log_sincronizacion_usuario');

IF @pk_name IS NOT NULL
BEGIN
    SET @sql = 'ALTER TABLE log_sincronizacion_usuario DROP CONSTRAINT ' + @pk_name;
    EXEC sp_executesql @sql;
    PRINT '  PK eliminada: ' + @pk_name;
END
GO

-- 14.7. Eliminar columna INT antigua
ALTER TABLE log_sincronizacion_usuario DROP COLUMN log_id;
GO

-- 14.8. Renombrar columna UUID
EXEC sp_rename 'log_sincronizacion_usuario.log_id_uuid', 'log_id', 'COLUMN';
GO

-- 14.9. Recrear PK
ALTER TABLE log_sincronizacion_usuario
ADD CONSTRAINT PK_log_sincronizacion_usuario PRIMARY KEY (log_id);
GO

-- 14.10. Agregar DEFAULT
ALTER TABLE log_sincronizacion_usuario
ADD CONSTRAINT DF_log_sync_id DEFAULT NEWID() FOR log_id;
GO

-- 14.11. Recrear FKs
ALTER TABLE log_sincronizacion_usuario
ADD CONSTRAINT FK_log_sync_usuario FOREIGN KEY (usuario_id)
    REFERENCES usuario(usuario_id) ON DELETE CASCADE;
GO

ALTER TABLE log_sincronizacion_usuario
ADD CONSTRAINT FK_log_sync_cliente_origen FOREIGN KEY (cliente_origen_id)
    REFERENCES cliente(cliente_id) ON DELETE NO ACTION;
GO

ALTER TABLE log_sincronizacion_usuario
ADD CONSTRAINT FK_log_sync_cliente_destino FOREIGN KEY (cliente_destino_id)
    REFERENCES cliente(cliente_id) ON DELETE NO ACTION;
GO

PRINT '✅ Tabla log_sincronizacion_usuario migrada exitosamente';
GO

-- ============================================================================
-- PASO 15: TABLA auth_audit_log
-- ============================================================================

PRINT '========================================';
PRINT 'PASO 15: Migrando tabla: auth_audit_log';
PRINT '========================================';

-- 15.1. Crear tabla de mapeo INT->UUID
IF OBJECT_ID('tempdb..#audit_log_id_map') IS NOT NULL DROP TABLE #audit_log_id_map;
CREATE TABLE #audit_log_id_map (
    log_id_int INT PRIMARY KEY,
    log_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #audit_log_id_map (log_id_int, log_id_uuid)
SELECT log_id, NEWID() FROM auth_audit_log;
GO

-- 15.2. Agregar columna UUID temporal
ALTER TABLE auth_audit_log
ADD log_id_uuid UNIQUEIDENTIFIER NULL;
GO

-- 15.3. Actualizar con UUIDs del mapeo
UPDATE aal
SET aal.log_id_uuid = m.log_id_uuid
FROM auth_audit_log aal
INNER JOIN #audit_log_id_map m ON aal.log_id = m.log_id_int;
GO

-- 15.4. Actualizar FKs: cliente_id, usuario_id
UPDATE aal
SET aal.cliente_id = c.cliente_id_uuid,
    aal.usuario_id = u.usuario_id_uuid
FROM auth_audit_log aal
LEFT JOIN #cliente_id_map c ON aal.cliente_id = c.cliente_id_int
LEFT JOIN #usuario_id_map u ON aal.usuario_id = u.usuario_id_int;
GO

-- 15.5. Cambiar tipos a UNIQUEIDENTIFIER
ALTER TABLE auth_audit_log
ALTER COLUMN cliente_id UNIQUEIDENTIFIER NULL;
GO

ALTER TABLE auth_audit_log
ALTER COLUMN usuario_id UNIQUEIDENTIFIER NULL;
GO

-- 15.6. Eliminar PK INT
SELECT @pk_name = name
FROM sys.key_constraints
WHERE type = 'PK' AND parent_object_id = OBJECT_ID('auth_audit_log');

IF @pk_name IS NOT NULL
BEGIN
    SET @sql = 'ALTER TABLE auth_audit_log DROP CONSTRAINT ' + @pk_name;
    EXEC sp_executesql @sql;
    PRINT '  PK eliminada: ' + @pk_name;
END
GO

-- 15.7. Eliminar columna INT antigua
ALTER TABLE auth_audit_log DROP COLUMN log_id;
GO

-- 15.8. Renombrar columna UUID
EXEC sp_rename 'auth_audit_log.log_id_uuid', 'log_id', 'COLUMN';
GO

-- 15.9. Recrear PK
ALTER TABLE auth_audit_log
ADD CONSTRAINT PK_auth_audit_log PRIMARY KEY (log_id);
GO

-- 15.10. Agregar DEFAULT
ALTER TABLE auth_audit_log
ADD CONSTRAINT DF_audit_log_id DEFAULT NEWID() FOR log_id;
GO

-- 15.11. Recrear FKs
ALTER TABLE auth_audit_log
ADD CONSTRAINT FK_audit_cliente FOREIGN KEY (cliente_id)
    REFERENCES cliente(cliente_id) ON DELETE CASCADE;
GO

ALTER TABLE auth_audit_log
ADD CONSTRAINT FK_audit_usuario FOREIGN KEY (usuario_id)
    REFERENCES usuario(usuario_id) ON DELETE SET NULL;
GO

PRINT '✅ Tabla auth_audit_log migrada exitosamente';
GO

-- ============================================================================
-- LIMPIEZA DE TABLAS TEMPORALES
-- ============================================================================

PRINT '========================================';
PRINT 'Limpiando tablas temporales...';
PRINT '========================================';

IF OBJECT_ID('tempdb..#cliente_id_map') IS NOT NULL DROP TABLE #cliente_id_map;
IF OBJECT_ID('tempdb..#usuario_id_map') IS NOT NULL DROP TABLE #usuario_id_map;
IF OBJECT_ID('tempdb..#rol_id_map') IS NOT NULL DROP TABLE #rol_id_map;
IF OBJECT_ID('tempdb..#area_id_map') IS NOT NULL DROP TABLE #area_id_map;
IF OBJECT_ID('tempdb..#menu_id_map') IS NOT NULL DROP TABLE #menu_id_map;
IF OBJECT_ID('tempdb..#modulo_id_map') IS NOT NULL DROP TABLE #modulo_id_map;
IF OBJECT_ID('tempdb..#usuario_rol_id_map') IS NOT NULL DROP TABLE #usuario_rol_id_map;
IF OBJECT_ID('tempdb..#permiso_id_map') IS NOT NULL DROP TABLE #permiso_id_map;
IF OBJECT_ID('tempdb..#token_id_map') IS NOT NULL DROP TABLE #token_id_map;
IF OBJECT_ID('tempdb..#conexion_id_map') IS NOT NULL DROP TABLE #conexion_id_map;
IF OBJECT_ID('tempdb..#cliente_modulo_activo_id_map') IS NOT NULL DROP TABLE #cliente_modulo_activo_id_map;
IF OBJECT_ID('tempdb..#config_id_map') IS NOT NULL DROP TABLE #config_id_map;
IF OBJECT_ID('tempdb..#federacion_id_map') IS NOT NULL DROP TABLE #federacion_id_map;
IF OBJECT_ID('tempdb..#log_sync_id_map') IS NOT NULL DROP TABLE #log_sync_id_map;
IF OBJECT_ID('tempdb..#audit_log_id_map') IS NOT NULL DROP TABLE #audit_log_id_map;
GO

-- ============================================================================
-- FINALIZACIÓN
-- ============================================================================

PRINT '========================================';
PRINT '========================================';
PRINT 'Migración a UUID completada exitosamente';
PRINT '========================================';
PRINT '========================================';
PRINT '';
PRINT '✅ Todas las tablas han sido migradas:';
PRINT '   1. cliente';
PRINT '   2. usuario';
PRINT '   3. rol';
PRINT '   4. area_menu';
PRINT '   5. menu';
PRINT '   6. cliente_modulo';
PRINT '   7. usuario_rol';
PRINT '   8. rol_menu_permiso';
PRINT '   9. refresh_tokens';
PRINT '   10. cliente_conexion';
PRINT '   11. cliente_modulo_activo';
PRINT '   12. cliente_auth_config';
PRINT '   13. federacion_identidad';
PRINT '   14. log_sincronizacion_usuario';
PRINT '   15. auth_audit_log';
PRINT '';
PRINT '⚠️ IMPORTANTE - PRÓXIMOS PASOS:';
PRINT '1. Verificar integridad de datos con queries de validación';
PRINT '2. Recrear índices si es necesario';
PRINT '3. Verificar que todas las FKs estén correctamente recreadas';
PRINT '4. Actualizar código de aplicación (ya está hecho)';
PRINT '5. Testing exhaustivo de todas las funcionalidades';
PRINT '6. Verificar que los nuevos registros generen UUIDs correctamente';
PRINT '';
PRINT '⚠️ DESCOMENTAR PARA COMMIT (solo después de verificar todo):';
PRINT '-- COMMIT;';
PRINT '-- GO';
PRINT '';
PRINT '⚠️ SI HAY ERRORES, DESCOMENTAR PARA ROLLBACK:';
PRINT '-- ROLLBACK;';
PRINT '-- GO';
PRINT '';

-- ⚠️ DESCOMENTAR PARA COMMIT (solo después de verificar):
-- COMMIT;
-- GO

-- ⚠️ SI HAY ERRORES, DESCOMENTAR PARA ROLLBACK:
-- ROLLBACK;
-- GO


