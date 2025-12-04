-- ============================================================================
-- FASE 3: MIGRACIÓN DE PRIMARY KEYS A UUID
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
--   1. Agregar columna UUID temporal
--   2. Generar UUIDs para registros existentes
--   3. Eliminar FKs
--   4. Eliminar PKs INT
--   5. Renombrar columna UUID a nombre original
--   6. Recrear PKs como UNIQUEIDENTIFIER
--   7. Recrear FKs
--   8. Recrear índices
--
-- ORDEN DE MIGRACIÓN (respetar dependencias):
--   1. cliente (tabla raíz, sin dependencias)
--   2. usuario, rol, area_menu, menu, cliente_modulo (dependen de cliente)
--   3. usuario_rol, rol_menu_permiso, cliente_conexion, cliente_modulo_activo,
--      cliente_auth_config, federacion_identidad (dependen de tablas anteriores)
--   4. refresh_tokens, log_sincronizacion_usuario, auth_audit_log (dependen de usuario/cliente)
--
-- ============================================================================

USE [tu_base_de_datos]; -- ⚠️ CAMBIAR POR EL NOMBRE DE TU BD
GO

BEGIN TRANSACTION;
GO

-- ============================================================================
-- PASO 1: TABLA cliente (raíz, sin dependencias)
-- ============================================================================

PRINT 'Migrando tabla: cliente';

-- 1.1. Agregar columna UUID temporal
ALTER TABLE cliente
ADD cliente_id_uuid UNIQUEIDENTIFIER NULL;
GO

-- 1.2. Generar UUIDs para registros existentes
UPDATE cliente
SET cliente_id_uuid = NEWID();
GO

-- 1.3. Hacer la columna NOT NULL
ALTER TABLE cliente
ALTER COLUMN cliente_id_uuid UNIQUEIDENTIFIER NOT NULL;
GO

-- 1.4. Eliminar FKs que referencian cliente_id
-- (Se recrearán después con UUID)
ALTER TABLE usuario DROP CONSTRAINT FK_usuario_cliente;
ALTER TABLE rol DROP CONSTRAINT FK_rol_cliente;
ALTER TABLE usuario_rol DROP CONSTRAINT FK_usuario_rol_cliente;
ALTER TABLE area_menu DROP CONSTRAINT FK_area_menu_cliente;
ALTER TABLE menu DROP CONSTRAINT FK_menu_cliente;
ALTER TABLE rol_menu_permiso DROP CONSTRAINT FK_permiso_cliente;
ALTER TABLE refresh_tokens DROP CONSTRAINT FK_refresh_token_cliente;
ALTER TABLE cliente_conexion DROP CONSTRAINT FK_conexion_cliente_;
ALTER TABLE cliente_modulo_activo DROP CONSTRAINT FK_modulo_activo_cliente;
ALTER TABLE cliente_auth_config DROP CONSTRAINT FK_auth_config_cliente;
ALTER TABLE federacion_identidad DROP CONSTRAINT FK_federacion_cliente;
ALTER TABLE log_sincronizacion_usuario DROP CONSTRAINT FK_log_sync_cliente_origen;
ALTER TABLE log_sincronizacion_usuario DROP CONSTRAINT FK_log_sync_cliente_destino;
ALTER TABLE auth_audit_log DROP CONSTRAINT FK_audit_cliente;
GO

-- 1.5. Eliminar PK INT
ALTER TABLE cliente DROP CONSTRAINT PK__cliente__[hash]; -- ⚠️ Ajustar nombre real
GO

-- 1.6. Eliminar columna INT antigua
ALTER TABLE cliente DROP COLUMN cliente_id;
GO

-- 1.7. Renombrar columna UUID
EXEC sp_rename 'cliente.cliente_id_uuid', 'cliente_id', 'COLUMN';
GO

-- 1.8. Recrear PK como UNIQUEIDENTIFIER
ALTER TABLE cliente
ADD CONSTRAINT PK_cliente PRIMARY KEY (cliente_id);
GO

-- 1.9. Agregar DEFAULT para nuevos registros
ALTER TABLE cliente
ADD CONSTRAINT DF_cliente_id DEFAULT NEWID() FOR cliente_id;
GO

PRINT 'Tabla cliente migrada exitosamente';
GO

-- ============================================================================
-- PASO 2: TABLA usuario
-- ============================================================================

PRINT 'Migrando tabla: usuario';

-- 2.1. Agregar columna UUID temporal
ALTER TABLE usuario
ADD usuario_id_uuid UNIQUEIDENTIFIER NULL;
GO

-- 2.2. Generar UUIDs para registros existentes
UPDATE usuario
SET usuario_id_uuid = NEWID();
GO

-- 2.3. Actualizar FK cliente_id a UUID (usando tabla temporal de mapeo)
-- Crear tabla temporal de mapeo
CREATE TABLE #cliente_id_map (
    cliente_id_int INT,
    cliente_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #cliente_id_map
SELECT cliente_id, cliente_id_uuid FROM cliente;
GO

-- Actualizar usuario.cliente_id a UUID
UPDATE u
SET u.cliente_id = m.cliente_id_uuid
FROM usuario u
INNER JOIN #cliente_id_map m ON u.cliente_id = m.cliente_id_int;
GO

-- 2.4. Cambiar tipo de cliente_id a UNIQUEIDENTIFIER
ALTER TABLE usuario
ALTER COLUMN cliente_id UNIQUEIDENTIFIER NOT NULL;
GO

-- 2.5. Eliminar FKs que referencian usuario_id
ALTER TABLE usuario_rol DROP CONSTRAINT FK_usuario_rol_usuario;
ALTER TABLE refresh_tokens DROP CONSTRAINT FK_refresh_token_usuario;
ALTER TABLE log_sincronizacion_usuario DROP CONSTRAINT FK_log_sync_usuario;
ALTER TABLE auth_audit_log DROP CONSTRAINT FK_audit_usuario;
GO

-- 2.6. Eliminar PK INT
ALTER TABLE usuario DROP CONSTRAINT PK__usuario__[hash];
GO

-- 2.7. Eliminar columna INT antigua
ALTER TABLE usuario DROP COLUMN usuario_id;
GO

-- 2.8. Renombrar columna UUID
EXEC sp_rename 'usuario.usuario_id_uuid', 'usuario_id', 'COLUMN';
GO

-- 2.9. Recrear PK
ALTER TABLE usuario
ADD CONSTRAINT PK_usuario PRIMARY KEY (usuario_id);
GO

-- 2.10. Agregar DEFAULT
ALTER TABLE usuario
ADD CONSTRAINT DF_usuario_id DEFAULT NEWID() FOR usuario_id;
GO

-- 2.11. Recrear FK a cliente
ALTER TABLE usuario
ADD CONSTRAINT FK_usuario_cliente FOREIGN KEY (cliente_id)
    REFERENCES cliente(cliente_id) ON DELETE CASCADE;
GO

DROP TABLE #cliente_id_map;
GO

PRINT 'Tabla usuario migrada exitosamente';
GO

-- ============================================================================
-- PASO 3: TABLA rol
-- ============================================================================

PRINT 'Migrando tabla: rol';

ALTER TABLE rol ADD rol_id_uuid UNIQUEIDENTIFIER NULL;
UPDATE rol SET rol_id_uuid = NEWID();
ALTER TABLE rol ALTER COLUMN rol_id_uuid UNIQUEIDENTIFIER NOT NULL;

-- Actualizar cliente_id a UUID
CREATE TABLE #cliente_id_map2 (
    cliente_id_int INT,
    cliente_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #cliente_id_map2
SELECT cliente_id, cliente_id FROM cliente; -- Ya es UUID ahora
GO

UPDATE r
SET r.cliente_id = m.cliente_id_uuid
FROM rol r
INNER JOIN #cliente_id_map2 m ON r.cliente_id = m.cliente_id_int;
GO

ALTER TABLE rol ALTER COLUMN cliente_id UNIQUEIDENTIFIER NULL;

ALTER TABLE usuario_rol DROP CONSTRAINT FK_usuario_rol_rol;
ALTER TABLE rol_menu_permiso DROP CONSTRAINT FK_permiso_rol;

ALTER TABLE rol DROP CONSTRAINT PK__rol__[hash];
ALTER TABLE rol DROP COLUMN rol_id;
EXEC sp_rename 'rol.rol_id_uuid', 'rol_id', 'COLUMN';

ALTER TABLE rol ADD CONSTRAINT PK_rol PRIMARY KEY (rol_id);
ALTER TABLE rol ADD CONSTRAINT DF_rol_id DEFAULT NEWID() FOR rol_id;

ALTER TABLE rol
ADD CONSTRAINT FK_rol_cliente FOREIGN KEY (cliente_id)
    REFERENCES cliente(cliente_id) ON DELETE CASCADE;

DROP TABLE #cliente_id_map2;
GO

PRINT 'Tabla rol migrada exitosamente';
GO

-- ============================================================================
-- PASO 4: TABLA area_menu
-- ============================================================================

PRINT 'Migrando tabla: area_menu';

ALTER TABLE area_menu ADD area_id_uuid UNIQUEIDENTIFIER NULL;
UPDATE area_menu SET area_id_uuid = NEWID();
ALTER TABLE area_menu ALTER COLUMN area_id_uuid UNIQUEIDENTIFIER NOT NULL;

-- Actualizar cliente_id a UUID
CREATE TABLE #cliente_id_map3 (
    cliente_id_int INT,
    cliente_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #cliente_id_map3
SELECT cliente_id, cliente_id FROM cliente;
GO

UPDATE a
SET a.cliente_id = m.cliente_id_uuid
FROM area_menu a
INNER JOIN #cliente_id_map3 m ON a.cliente_id = m.cliente_id_int;
GO

ALTER TABLE area_menu ALTER COLUMN cliente_id UNIQUEIDENTIFIER NULL;

ALTER TABLE menu DROP CONSTRAINT FK_menu_area;

ALTER TABLE area_menu DROP CONSTRAINT PK__area_menu__[hash];
ALTER TABLE area_menu DROP COLUMN area_id;
EXEC sp_rename 'area_menu.area_id_uuid', 'area_id', 'COLUMN';

ALTER TABLE area_menu ADD CONSTRAINT PK_area_menu PRIMARY KEY (area_id);
ALTER TABLE area_menu ADD CONSTRAINT DF_area_id DEFAULT NEWID() FOR area_id;

ALTER TABLE area_menu
ADD CONSTRAINT FK_area_menu_cliente FOREIGN KEY (cliente_id)
    REFERENCES cliente(cliente_id) ON DELETE CASCADE;

DROP TABLE #cliente_id_map3;
GO

PRINT 'Tabla area_menu migrada exitosamente';
GO

-- ============================================================================
-- PASO 5: TABLA menu
-- ============================================================================

PRINT 'Migrando tabla: menu';

ALTER TABLE menu ADD menu_id_uuid UNIQUEIDENTIFIER NULL;
UPDATE menu SET menu_id_uuid = NEWID();
ALTER TABLE menu ALTER COLUMN menu_id_uuid UNIQUEIDENTIFIER NOT NULL;

-- Actualizar cliente_id, area_id, padre_menu_id a UUID
CREATE TABLE #menu_id_map (
    menu_id_int INT,
    menu_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #menu_id_map
SELECT menu_id, menu_id_uuid FROM menu;
GO

CREATE TABLE #area_id_map (
    area_id_int INT,
    area_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #area_id_map
SELECT area_id, area_id FROM area_menu;
GO

CREATE TABLE #cliente_id_map4 (
    cliente_id_int INT,
    cliente_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #cliente_id_map4
SELECT cliente_id, cliente_id FROM cliente;
GO

UPDATE m
SET m.cliente_id = c.cliente_id_uuid,
    m.area_id = a.area_id_uuid,
    m.padre_menu_id = p.menu_id_uuid
FROM menu m
LEFT JOIN #cliente_id_map4 c ON m.cliente_id = c.cliente_id_int
LEFT JOIN #area_id_map a ON m.area_id = a.area_id_int
LEFT JOIN #menu_id_map p ON m.padre_menu_id = p.menu_id_int;
GO

ALTER TABLE menu ALTER COLUMN cliente_id UNIQUEIDENTIFIER NULL;
ALTER TABLE menu ALTER COLUMN area_id UNIQUEIDENTIFIER NULL;
ALTER TABLE menu ALTER COLUMN padre_menu_id UNIQUEIDENTIFIER NULL;

ALTER TABLE rol_menu_permiso DROP CONSTRAINT FK_permiso_menu;

ALTER TABLE menu DROP CONSTRAINT PK__menu__[hash];
ALTER TABLE menu DROP COLUMN menu_id;
EXEC sp_rename 'menu.menu_id_uuid', 'menu_id', 'COLUMN';

ALTER TABLE menu ADD CONSTRAINT PK_menu PRIMARY KEY (menu_id);
ALTER TABLE menu ADD CONSTRAINT DF_menu_id DEFAULT NEWID() FOR menu_id;

ALTER TABLE menu
ADD CONSTRAINT FK_menu_cliente FOREIGN KEY (cliente_id)
    REFERENCES cliente(cliente_id) ON DELETE CASCADE;
ALTER TABLE menu
ADD CONSTRAINT FK_menu_area FOREIGN KEY (area_id)
    REFERENCES area_menu(area_id) ON DELETE SET NULL;
ALTER TABLE menu
ADD CONSTRAINT FK_menu_padre FOREIGN KEY (padre_menu_id)
    REFERENCES menu(menu_id) ON DELETE NO ACTION;

DROP TABLE #menu_id_map;
DROP TABLE #area_id_map;
DROP TABLE #cliente_id_map4;
GO

PRINT 'Tabla menu migrada exitosamente';
GO

-- ============================================================================
-- PASO 6: TABLA cliente_modulo
-- ============================================================================

PRINT 'Migrando tabla: cliente_modulo';

ALTER TABLE cliente_modulo ADD modulo_id_uuid UNIQUEIDENTIFIER NULL;
UPDATE cliente_modulo SET modulo_id_uuid = NEWID();
ALTER TABLE cliente_modulo ALTER COLUMN modulo_id_uuid UNIQUEIDENTIFIER NOT NULL;

ALTER TABLE cliente_modulo_activo DROP CONSTRAINT FK_modulo_activo_modulo;

ALTER TABLE cliente_modulo DROP CONSTRAINT PK__cliente_modulo__[hash];
ALTER TABLE cliente_modulo DROP COLUMN modulo_id;
EXEC sp_rename 'cliente_modulo.modulo_id_uuid', 'modulo_id', 'COLUMN';

ALTER TABLE cliente_modulo ADD CONSTRAINT PK_cliente_modulo PRIMARY KEY (modulo_id);
ALTER TABLE cliente_modulo ADD CONSTRAINT DF_modulo_id DEFAULT NEWID() FOR modulo_id;

PRINT 'Tabla cliente_modulo migrada exitosamente';
GO

-- ============================================================================
-- PASO 7: TABLA usuario_rol
-- ============================================================================

PRINT 'Migrando tabla: usuario_rol';

ALTER TABLE usuario_rol ADD usuario_rol_id_uuid UNIQUEIDENTIFIER NULL;
UPDATE usuario_rol SET usuario_rol_id_uuid = NEWID();
ALTER TABLE usuario_rol ALTER COLUMN usuario_rol_id_uuid UNIQUEIDENTIFIER NOT NULL;

-- Actualizar usuario_id, rol_id, cliente_id, asignado_por_usuario_id a UUID
CREATE TABLE #usuario_id_map (
    usuario_id_int INT,
    usuario_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #usuario_id_map
SELECT usuario_id, usuario_id FROM usuario;
GO

CREATE TABLE #rol_id_map (
    rol_id_int INT,
    rol_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #rol_id_map
SELECT rol_id, rol_id FROM rol;
GO

CREATE TABLE #cliente_id_map5 (
    cliente_id_int INT,
    cliente_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #cliente_id_map5
SELECT cliente_id, cliente_id FROM cliente;
GO

UPDATE ur
SET ur.usuario_id = u.usuario_id_uuid,
    ur.rol_id = r.rol_id_uuid,
    ur.cliente_id = c.cliente_id_uuid,
    ur.asignado_por_usuario_id = a.usuario_id_uuid
FROM usuario_rol ur
INNER JOIN #usuario_id_map u ON ur.usuario_id = u.usuario_id_int
INNER JOIN #rol_id_map r ON ur.rol_id = r.rol_id_int
INNER JOIN #cliente_id_map5 c ON ur.cliente_id = c.cliente_id_int
LEFT JOIN #usuario_id_map a ON ur.asignado_por_usuario_id = a.usuario_id_int;
GO

ALTER TABLE usuario_rol ALTER COLUMN usuario_id UNIQUEIDENTIFIER NOT NULL;
ALTER TABLE usuario_rol ALTER COLUMN rol_id UNIQUEIDENTIFIER NOT NULL;
ALTER TABLE usuario_rol ALTER COLUMN cliente_id UNIQUEIDENTIFIER NOT NULL;
ALTER TABLE usuario_rol ALTER COLUMN asignado_por_usuario_id UNIQUEIDENTIFIER NULL;

ALTER TABLE usuario_rol DROP CONSTRAINT PK__usuario_rol__[hash];
ALTER TABLE usuario_rol DROP COLUMN usuario_rol_id;
EXEC sp_rename 'usuario_rol.usuario_rol_id_uuid', 'usuario_rol_id', 'COLUMN';

ALTER TABLE usuario_rol ADD CONSTRAINT PK_usuario_rol PRIMARY KEY (usuario_rol_id);
ALTER TABLE usuario_rol ADD CONSTRAINT DF_usuario_rol_id DEFAULT NEWID() FOR usuario_rol_id;

ALTER TABLE usuario_rol
ADD CONSTRAINT FK_usuario_rol_usuario FOREIGN KEY (usuario_id)
    REFERENCES usuario(usuario_id) ON DELETE CASCADE;
ALTER TABLE usuario_rol
ADD CONSTRAINT FK_usuario_rol_rol FOREIGN KEY (rol_id)
    REFERENCES rol(rol_id) ON DELETE CASCADE;
ALTER TABLE usuario_rol
ADD CONSTRAINT FK_usuario_rol_cliente FOREIGN KEY (cliente_id)
    REFERENCES cliente(cliente_id) ON DELETE NO ACTION;

DROP TABLE #usuario_id_map;
DROP TABLE #rol_id_map;
DROP TABLE #cliente_id_map5;
GO

PRINT 'Tabla usuario_rol migrada exitosamente';
GO

-- ============================================================================
-- PASO 8: TABLA rol_menu_permiso
-- ============================================================================

PRINT 'Migrando tabla: rol_menu_permiso';

ALTER TABLE rol_menu_permiso ADD permiso_id_uuid UNIQUEIDENTIFIER NULL;
UPDATE rol_menu_permiso SET permiso_id_uuid = NEWID();
ALTER TABLE rol_menu_permiso ALTER COLUMN permiso_id_uuid UNIQUEIDENTIFIER NOT NULL;

-- Actualizar rol_id, menu_id, cliente_id a UUID
CREATE TABLE #rol_id_map2 (
    rol_id_int INT,
    rol_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #rol_id_map2
SELECT rol_id, rol_id FROM rol;
GO

CREATE TABLE #menu_id_map2 (
    menu_id_int INT,
    menu_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #menu_id_map2
SELECT menu_id, menu_id FROM menu;
GO

CREATE TABLE #cliente_id_map6 (
    cliente_id_int INT,
    cliente_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #cliente_id_map6
SELECT cliente_id, cliente_id FROM cliente;
GO

UPDATE rmp
SET rmp.rol_id = r.rol_id_uuid,
    rmp.menu_id = m.menu_id_uuid,
    rmp.cliente_id = c.cliente_id_uuid
FROM rol_menu_permiso rmp
INNER JOIN #rol_id_map2 r ON rmp.rol_id = r.rol_id_int
INNER JOIN #menu_id_map2 m ON rmp.menu_id = m.menu_id_int
INNER JOIN #cliente_id_map6 c ON rmp.cliente_id = c.cliente_id_int;
GO

ALTER TABLE rol_menu_permiso ALTER COLUMN rol_id UNIQUEIDENTIFIER NOT NULL;
ALTER TABLE rol_menu_permiso ALTER COLUMN menu_id UNIQUEIDENTIFIER NOT NULL;
ALTER TABLE rol_menu_permiso ALTER COLUMN cliente_id UNIQUEIDENTIFIER NOT NULL;

ALTER TABLE rol_menu_permiso DROP CONSTRAINT PK__rol_menu_permiso__[hash];
ALTER TABLE rol_menu_permiso DROP COLUMN permiso_id;
EXEC sp_rename 'rol_menu_permiso.permiso_id_uuid', 'permiso_id', 'COLUMN';

ALTER TABLE rol_menu_permiso ADD CONSTRAINT PK_rol_menu_permiso PRIMARY KEY (permiso_id);
ALTER TABLE rol_menu_permiso ADD CONSTRAINT DF_permiso_id DEFAULT NEWID() FOR permiso_id;

ALTER TABLE rol_menu_permiso
ADD CONSTRAINT FK_permiso_rol FOREIGN KEY (rol_id)
    REFERENCES rol(rol_id) ON DELETE CASCADE;
ALTER TABLE rol_menu_permiso
ADD CONSTRAINT FK_permiso_menu FOREIGN KEY (menu_id)
    REFERENCES menu(menu_id) ON DELETE CASCADE;
ALTER TABLE rol_menu_permiso
ADD CONSTRAINT FK_permiso_cliente FOREIGN KEY (cliente_id)
    REFERENCES cliente(cliente_id) ON DELETE NO ACTION;

DROP TABLE #rol_id_map2;
DROP TABLE #menu_id_map2;
DROP TABLE #cliente_id_map6;
GO

PRINT 'Tabla rol_menu_permiso migrada exitosamente';
GO

-- ============================================================================
-- PASO 9: TABLA refresh_tokens
-- ============================================================================

PRINT 'Migrando tabla: refresh_tokens';

ALTER TABLE refresh_tokens ADD token_id_uuid UNIQUEIDENTIFIER NULL;
UPDATE refresh_tokens SET token_id_uuid = NEWID();
ALTER TABLE refresh_tokens ALTER COLUMN token_id_uuid UNIQUEIDENTIFIER NOT NULL;

-- Actualizar usuario_id, cliente_id a UUID
CREATE TABLE #usuario_id_map2 (
    usuario_id_int INT,
    usuario_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #usuario_id_map2
SELECT usuario_id, usuario_id FROM usuario;
GO

CREATE TABLE #cliente_id_map7 (
    cliente_id_int INT,
    cliente_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #cliente_id_map7
SELECT cliente_id, cliente_id FROM cliente;
GO

UPDATE rt
SET rt.usuario_id = u.usuario_id_uuid,
    rt.cliente_id = c.cliente_id_uuid
FROM refresh_tokens rt
INNER JOIN #usuario_id_map2 u ON rt.usuario_id = u.usuario_id_int
INNER JOIN #cliente_id_map7 c ON rt.cliente_id = c.cliente_id_int;
GO

ALTER TABLE refresh_tokens ALTER COLUMN usuario_id UNIQUEIDENTIFIER NOT NULL;
ALTER TABLE refresh_tokens ALTER COLUMN cliente_id UNIQUEIDENTIFIER NOT NULL;

ALTER TABLE refresh_tokens DROP CONSTRAINT PK__refresh_tokens__[hash];
ALTER TABLE refresh_tokens DROP COLUMN token_id;
EXEC sp_rename 'refresh_tokens.token_id_uuid', 'token_id', 'COLUMN';

ALTER TABLE refresh_tokens ADD CONSTRAINT PK_refresh_tokens PRIMARY KEY (token_id);
ALTER TABLE refresh_tokens ADD CONSTRAINT DF_token_id DEFAULT NEWID() FOR token_id;

ALTER TABLE refresh_tokens
ADD CONSTRAINT FK_refresh_token_cliente FOREIGN KEY (cliente_id)
    REFERENCES cliente(cliente_id) ON DELETE CASCADE;
ALTER TABLE refresh_tokens
ADD CONSTRAINT FK_refresh_token_usuario FOREIGN KEY (usuario_id)
    REFERENCES usuario(usuario_id) ON DELETE CASCADE;

DROP TABLE #usuario_id_map2;
DROP TABLE #cliente_id_map7;
GO

PRINT 'Tabla refresh_tokens migrada exitosamente';
GO

-- ============================================================================
-- PASO 10: TABLA cliente_conexion
-- ============================================================================

PRINT 'Migrando tabla: cliente_conexion';

ALTER TABLE cliente_conexion ADD conexion_id_uuid UNIQUEIDENTIFIER NULL;
UPDATE cliente_conexion SET conexion_id_uuid = NEWID();
ALTER TABLE cliente_conexion ALTER COLUMN conexion_id_uuid UNIQUEIDENTIFIER NOT NULL;

-- Actualizar cliente_id a UUID
CREATE TABLE #cliente_id_map8 (
    cliente_id_int INT,
    cliente_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #cliente_id_map8
SELECT cliente_id, cliente_id FROM cliente;
GO

UPDATE cc
SET cc.cliente_id = c.cliente_id_uuid
FROM cliente_conexion cc
INNER JOIN #cliente_id_map8 c ON cc.cliente_id = c.cliente_id_int;
GO

ALTER TABLE cliente_conexion ALTER COLUMN cliente_id UNIQUEIDENTIFIER NOT NULL;

ALTER TABLE cliente_conexion DROP CONSTRAINT PK__cliente_conexion__[hash];
ALTER TABLE cliente_conexion DROP COLUMN conexion_id;
EXEC sp_rename 'cliente_conexion.conexion_id_uuid', 'conexion_id', 'COLUMN';

ALTER TABLE cliente_conexion ADD CONSTRAINT PK_cliente_conexion PRIMARY KEY (conexion_id);
ALTER TABLE cliente_conexion ADD CONSTRAINT DF_conexion_id DEFAULT NEWID() FOR conexion_id;

ALTER TABLE cliente_conexion
ADD CONSTRAINT FK_conexion_cliente FOREIGN KEY (cliente_id)
    REFERENCES cliente(cliente_id) ON DELETE CASCADE;

DROP TABLE #cliente_id_map8;
GO

PRINT 'Tabla cliente_conexion migrada exitosamente';
GO

-- ============================================================================
-- PASO 11: TABLA cliente_modulo_activo
-- ============================================================================

PRINT 'Migrando tabla: cliente_modulo_activo';

ALTER TABLE cliente_modulo_activo ADD cliente_modulo_activo_id_uuid UNIQUEIDENTIFIER NULL;
UPDATE cliente_modulo_activo SET cliente_modulo_activo_id_uuid = NEWID();
ALTER TABLE cliente_modulo_activo ALTER COLUMN cliente_modulo_activo_id_uuid UNIQUEIDENTIFIER NOT NULL;

-- Actualizar cliente_id, modulo_id a UUID
CREATE TABLE #cliente_id_map9 (
    cliente_id_int INT,
    cliente_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #cliente_id_map9
SELECT cliente_id, cliente_id FROM cliente;
GO

CREATE TABLE #modulo_id_map (
    modulo_id_int INT,
    modulo_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #modulo_id_map
SELECT modulo_id, modulo_id FROM cliente_modulo;
GO

UPDATE cma
SET cma.cliente_id = c.cliente_id_uuid,
    cma.modulo_id = m.modulo_id_uuid
FROM cliente_modulo_activo cma
INNER JOIN #cliente_id_map9 c ON cma.cliente_id = c.cliente_id_int
INNER JOIN #modulo_id_map m ON cma.modulo_id = m.modulo_id_int;
GO

ALTER TABLE cliente_modulo_activo ALTER COLUMN cliente_id UNIQUEIDENTIFIER NOT NULL;
ALTER TABLE cliente_modulo_activo ALTER COLUMN modulo_id UNIQUEIDENTIFIER NOT NULL;

ALTER TABLE cliente_modulo_activo DROP CONSTRAINT PK__cliente_modulo_activo__[hash];
ALTER TABLE cliente_modulo_activo DROP COLUMN cliente_modulo_activo_id;
EXEC sp_rename 'cliente_modulo_activo.cliente_modulo_activo_id_uuid', 'cliente_modulo_activo_id', 'COLUMN';

ALTER TABLE cliente_modulo_activo ADD CONSTRAINT PK_cliente_modulo_activo PRIMARY KEY (cliente_modulo_activo_id);
ALTER TABLE cliente_modulo_activo ADD CONSTRAINT DF_cliente_modulo_activo_id DEFAULT NEWID() FOR cliente_modulo_activo_id;

ALTER TABLE cliente_modulo_activo
ADD CONSTRAINT FK_modulo_activo_cliente FOREIGN KEY (cliente_id)
    REFERENCES cliente(cliente_id) ON DELETE CASCADE;
ALTER TABLE cliente_modulo_activo
ADD CONSTRAINT FK_modulo_activo_modulo FOREIGN KEY (modulo_id)
    REFERENCES cliente_modulo(modulo_id) ON DELETE CASCADE;

DROP TABLE #cliente_id_map9;
DROP TABLE #modulo_id_map;
GO

PRINT 'Tabla cliente_modulo_activo migrada exitosamente';
GO

-- ============================================================================
-- PASO 12: TABLA cliente_auth_config
-- ============================================================================

PRINT 'Migrando tabla: cliente_auth_config';

ALTER TABLE cliente_auth_config ADD config_id_uuid UNIQUEIDENTIFIER NULL;
UPDATE cliente_auth_config SET config_id_uuid = NEWID();
ALTER TABLE cliente_auth_config ALTER COLUMN config_id_uuid UNIQUEIDENTIFIER NOT NULL;

-- Actualizar cliente_id a UUID
CREATE TABLE #cliente_id_map10 (
    cliente_id_int INT,
    cliente_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #cliente_id_map10
SELECT cliente_id, cliente_id FROM cliente;
GO

UPDATE cac
SET cac.cliente_id = c.cliente_id_uuid
FROM cliente_auth_config cac
INNER JOIN #cliente_id_map10 c ON cac.cliente_id = c.cliente_id_int;
GO

ALTER TABLE cliente_auth_config ALTER COLUMN cliente_id UNIQUEIDENTIFIER NOT NULL;

ALTER TABLE cliente_auth_config DROP CONSTRAINT PK__cliente_auth_config__[hash];
ALTER TABLE cliente_auth_config DROP COLUMN config_id;
EXEC sp_rename 'cliente_auth_config.config_id_uuid', 'config_id', 'COLUMN';

ALTER TABLE cliente_auth_config ADD CONSTRAINT PK_cliente_auth_config PRIMARY KEY (config_id);
ALTER TABLE cliente_auth_config ADD CONSTRAINT DF_config_id DEFAULT NEWID() FOR config_id;

ALTER TABLE cliente_auth_config
ADD CONSTRAINT FK_auth_config_cliente FOREIGN KEY (cliente_id)
    REFERENCES cliente(cliente_id) ON DELETE CASCADE;

DROP TABLE #cliente_id_map10;
GO

PRINT 'Tabla cliente_auth_config migrada exitosamente';
GO

-- ============================================================================
-- PASO 13: TABLA federacion_identidad
-- ============================================================================

PRINT 'Migrando tabla: federacion_identidad';

ALTER TABLE federacion_identidad ADD federacion_id_uuid UNIQUEIDENTIFIER NULL;
UPDATE federacion_identidad SET federacion_id_uuid = NEWID();
ALTER TABLE federacion_identidad ALTER COLUMN federacion_id_uuid UNIQUEIDENTIFIER NOT NULL;

-- Actualizar cliente_id a UUID
CREATE TABLE #cliente_id_map11 (
    cliente_id_int INT,
    cliente_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #cliente_id_map11
SELECT cliente_id, cliente_id FROM cliente;
GO

UPDATE fi
SET fi.cliente_id = c.cliente_id_uuid
FROM federacion_identidad fi
INNER JOIN #cliente_id_map11 c ON fi.cliente_id = c.cliente_id_int;
GO

ALTER TABLE federacion_identidad ALTER COLUMN cliente_id UNIQUEIDENTIFIER NOT NULL;

ALTER TABLE federacion_identidad DROP CONSTRAINT PK__federacion_identidad__[hash];
ALTER TABLE federacion_identidad DROP COLUMN federacion_id;
EXEC sp_rename 'federacion_identidad.federacion_id_uuid', 'federacion_id', 'COLUMN';

ALTER TABLE federacion_identidad ADD CONSTRAINT PK_federacion_identidad PRIMARY KEY (federacion_id);
ALTER TABLE federacion_identidad ADD CONSTRAINT DF_federacion_id DEFAULT NEWID() FOR federacion_id;

ALTER TABLE federacion_identidad
ADD CONSTRAINT FK_federacion_cliente FOREIGN KEY (cliente_id)
    REFERENCES cliente(cliente_id) ON DELETE CASCADE;

DROP TABLE #cliente_id_map11;
GO

PRINT 'Tabla federacion_identidad migrada exitosamente';
GO

-- ============================================================================
-- PASO 14: TABLA log_sincronizacion_usuario
-- ============================================================================

PRINT 'Migrando tabla: log_sincronizacion_usuario';

ALTER TABLE log_sincronizacion_usuario ADD log_id_uuid UNIQUEIDENTIFIER NULL;
UPDATE log_sincronizacion_usuario SET log_id_uuid = NEWID();
ALTER TABLE log_sincronizacion_usuario ALTER COLUMN log_id_uuid UNIQUEIDENTIFIER NOT NULL;

-- Actualizar usuario_id, cliente_origen_id, cliente_destino_id, usuario_ejecutor_id a UUID
CREATE TABLE #usuario_id_map3 (
    usuario_id_int INT,
    usuario_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #usuario_id_map3
SELECT usuario_id, usuario_id FROM usuario;
GO

CREATE TABLE #cliente_id_map12 (
    cliente_id_int INT,
    cliente_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #cliente_id_map12
SELECT cliente_id, cliente_id FROM cliente;
GO

UPDATE lsu
SET lsu.usuario_id = u.usuario_id_uuid,
    lsu.cliente_origen_id = co.cliente_id_uuid,
    lsu.cliente_destino_id = cd.cliente_id_uuid,
    lsu.usuario_ejecutor_id = ue.usuario_id_uuid
FROM log_sincronizacion_usuario lsu
LEFT JOIN #usuario_id_map3 u ON lsu.usuario_id = u.usuario_id_int
LEFT JOIN #cliente_id_map12 co ON lsu.cliente_origen_id = co.cliente_id_int
LEFT JOIN #cliente_id_map12 cd ON lsu.cliente_destino_id = cd.cliente_id_int
LEFT JOIN #usuario_id_map3 ue ON lsu.usuario_ejecutor_id = ue.usuario_id_int;
GO

ALTER TABLE log_sincronizacion_usuario ALTER COLUMN usuario_id UNIQUEIDENTIFIER NULL;
ALTER TABLE log_sincronizacion_usuario ALTER COLUMN cliente_origen_id UNIQUEIDENTIFIER NULL;
ALTER TABLE log_sincronizacion_usuario ALTER COLUMN cliente_destino_id UNIQUEIDENTIFIER NULL;
ALTER TABLE log_sincronizacion_usuario ALTER COLUMN usuario_ejecutor_id UNIQUEIDENTIFIER NULL;

ALTER TABLE log_sincronizacion_usuario DROP CONSTRAINT PK__log_sincronizacion_usuario__[hash];
ALTER TABLE log_sincronizacion_usuario DROP COLUMN log_id;
EXEC sp_rename 'log_sincronizacion_usuario.log_id_uuid', 'log_id', 'COLUMN';

ALTER TABLE log_sincronizacion_usuario ADD CONSTRAINT PK_log_sincronizacion_usuario PRIMARY KEY (log_id);
ALTER TABLE log_sincronizacion_usuario ADD CONSTRAINT DF_log_id DEFAULT NEWID() FOR log_id;

ALTER TABLE log_sincronizacion_usuario
ADD CONSTRAINT FK_log_sync_usuario FOREIGN KEY (usuario_id)
    REFERENCES usuario(usuario_id) ON DELETE CASCADE;
ALTER TABLE log_sincronizacion_usuario
ADD CONSTRAINT FK_log_sync_cliente_origen FOREIGN KEY (cliente_origen_id)
    REFERENCES cliente(cliente_id) ON DELETE NO ACTION;
ALTER TABLE log_sincronizacion_usuario
ADD CONSTRAINT FK_log_sync_cliente_destino FOREIGN KEY (cliente_destino_id)
    REFERENCES cliente(cliente_id) ON DELETE NO ACTION;

DROP TABLE #usuario_id_map3;
DROP TABLE #cliente_id_map12;
GO

PRINT 'Tabla log_sincronizacion_usuario migrada exitosamente';
GO

-- ============================================================================
-- PASO 15: TABLA auth_audit_log
-- ============================================================================

PRINT 'Migrando tabla: auth_audit_log';

ALTER TABLE auth_audit_log ADD log_id_uuid UNIQUEIDENTIFIER NULL;
UPDATE auth_audit_log SET log_id_uuid = NEWID();
ALTER TABLE auth_audit_log ALTER COLUMN log_id_uuid UNIQUEIDENTIFIER NOT NULL;

-- Actualizar cliente_id, usuario_id a UUID
CREATE TABLE #cliente_id_map13 (
    cliente_id_int INT,
    cliente_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #cliente_id_map13
SELECT cliente_id, cliente_id FROM cliente;
GO

CREATE TABLE #usuario_id_map4 (
    usuario_id_int INT,
    usuario_id_uuid UNIQUEIDENTIFIER
);
INSERT INTO #usuario_id_map4
SELECT usuario_id, usuario_id FROM usuario;
GO

UPDATE aal
SET aal.cliente_id = c.cliente_id_uuid,
    aal.usuario_id = u.usuario_id_uuid
FROM auth_audit_log aal
LEFT JOIN #cliente_id_map13 c ON aal.cliente_id = c.cliente_id_int
LEFT JOIN #usuario_id_map4 u ON aal.usuario_id = u.usuario_id_int;
GO

ALTER TABLE auth_audit_log ALTER COLUMN cliente_id UNIQUEIDENTIFIER NULL;
ALTER TABLE auth_audit_log ALTER COLUMN usuario_id UNIQUEIDENTIFIER NULL;

ALTER TABLE auth_audit_log DROP CONSTRAINT PK__auth_audit_log__[hash];
ALTER TABLE auth_audit_log DROP COLUMN log_id;
EXEC sp_rename 'auth_audit_log.log_id_uuid', 'log_id', 'COLUMN';

ALTER TABLE auth_audit_log ADD CONSTRAINT PK_auth_audit_log PRIMARY KEY (log_id);
ALTER TABLE auth_audit_log ADD CONSTRAINT DF_log_id DEFAULT NEWID() FOR log_id;

ALTER TABLE auth_audit_log
ADD CONSTRAINT FK_audit_cliente FOREIGN KEY (cliente_id)
    REFERENCES cliente(cliente_id) ON DELETE CASCADE;
ALTER TABLE auth_audit_log
ADD CONSTRAINT FK_audit_usuario FOREIGN KEY (usuario_id)
    REFERENCES usuario(usuario_id) ON DELETE SET NULL;

DROP TABLE #cliente_id_map13;
DROP TABLE #usuario_id_map4;
GO

PRINT 'Tabla auth_audit_log migrada exitosamente';
GO

-- ============================================================================
-- FINALIZACIÓN
-- ============================================================================

PRINT '========================================';
PRINT 'Migración a UUID completada exitosamente';
PRINT '========================================';
PRINT '';
PRINT '⚠️ IMPORTANTE:';
PRINT '1. Verificar integridad de datos';
PRINT '2. Recrear índices si es necesario';
PRINT '3. Actualizar código de aplicación';
PRINT '4. Testing exhaustivo';
PRINT '';

-- ⚠️ DESCOMENTAR PARA COMMIT:
-- COMMIT;
-- GO

-- ⚠️ SI HAY ERRORES, DESCOMENTAR PARA ROLLBACK:
-- ROLLBACK;
-- GO




