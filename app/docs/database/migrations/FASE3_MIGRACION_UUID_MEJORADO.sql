-- ============================================================================
-- FASE 3: MIGRACIÓN DE PRIMARY KEYS A UUID (VERSIÓN MEJORADA)
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
--   11. Recrear índices
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

-- ============================================================================
-- FUNCIÓN AUXILIAR: Obtener nombre de constraint PK
-- ============================================================================
-- Esta función ayuda a obtener el nombre real de las Primary Keys
-- que SQL Server genera automáticamente

DECLARE @sql NVARCHAR(MAX);
DECLARE @pk_name NVARCHAR(255);

-- ============================================================================
-- PASO 1: TABLA cliente (raíz, sin dependencias)
-- ============================================================================

PRINT '========================================';
PRINT 'Migrando tabla: cliente';
PRINT '========================================';

-- 1.1. Crear tabla de mapeo INT->UUID ANTES de modificar
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

-- 1.5. Obtener nombre real de PK y eliminar FKs que referencian cliente_id
-- Obtener nombre de PK
SELECT @pk_name = name
FROM sys.key_constraints
WHERE type = 'PK' AND parent_object_id = OBJECT_ID('cliente');

-- Eliminar FKs (ajustar nombres según tu esquema)
IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE parent_object_id = OBJECT_ID('usuario') AND referenced_object_id = OBJECT_ID('cliente'))
BEGIN
    SELECT @sql = 'ALTER TABLE usuario DROP CONSTRAINT ' + name
    FROM sys.foreign_keys
    WHERE parent_object_id = OBJECT_ID('usuario') AND referenced_object_id = OBJECT_ID('cliente');
    EXEC sp_executesql @sql;
END
GO

-- Eliminar todas las FKs que referencian cliente (usar script dinámico)
DECLARE @fk_name NVARCHAR(255);
DECLARE @table_name NVARCHAR(255);
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

PRINT 'Tabla cliente migrada exitosamente';
GO

-- ============================================================================
-- PASO 2: TABLA usuario
-- ============================================================================

PRINT '========================================';
PRINT 'Migrando tabla: usuario';
PRINT '========================================';

-- 2.1. Crear tabla de mapeo INT->UUID
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

DROP TABLE #usuario_id_map;
GO

PRINT 'Tabla usuario migrada exitosamente';
GO

-- ============================================================================
-- CONTINUAR CON LAS DEMÁS TABLAS SIGUIENDO EL MISMO PATRÓN
-- ============================================================================
-- Nota: El script completo sería muy largo. Este es el patrón a seguir
-- para las demás tablas. Puedes continuar con:
-- - rol
-- - area_menu
-- - menu
-- - cliente_modulo
-- - usuario_rol
-- - rol_menu_permiso
-- - refresh_tokens
-- - cliente_conexion
-- - cliente_modulo_activo
-- - cliente_auth_config
-- - federacion_identidad
-- - log_sincronizacion_usuario
-- - auth_audit_log

-- ============================================================================
-- FINALIZACIÓN
-- ============================================================================

PRINT '========================================';
PRINT 'Migración parcial completada';
PRINT '========================================';
PRINT '';
PRINT '⚠️ IMPORTANTE:';
PRINT '1. Este script migra solo cliente y usuario como ejemplo';
PRINT '2. Debes continuar con las demás tablas siguiendo el mismo patrón';
PRINT '3. Verificar integridad de datos después de cada tabla';
PRINT '4. Recrear índices si es necesario';
PRINT '5. Actualizar código de aplicación';
PRINT '6. Testing exhaustivo';
PRINT '';

-- ⚠️ DESCOMENTAR PARA COMMIT (solo después de verificar):
-- COMMIT;
-- GO

-- ⚠️ SI HAY ERRORES, DESCOMENTAR PARA ROLLBACK:
-- ROLLBACK;
-- GO

-- Limpiar tablas temporales
DROP TABLE #cliente_id_map;
GO


