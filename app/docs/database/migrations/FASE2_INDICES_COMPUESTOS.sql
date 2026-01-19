-- ============================================================================
-- FASE 2: ÍNDICES COMPUESTOS CRÍTICOS PARA PERFORMANCE
-- ============================================================================
-- 
-- Este script agrega índices compuestos optimizados para queries frecuentes
-- que filtran por múltiples columnas simultáneamente.
--
-- ✅ FASE 2 PERFORMANCE: Mejora significativa en queries con múltiples filtros
--
-- IMPORTANTE:
-- - Ejecutar en horario de bajo tráfico
-- - Los índices se crean en background (no bloquean)
-- - Verificar espacio en disco antes de ejecutar
--
-- Tiempo estimado: 5-15 minutos dependiendo del tamaño de las tablas
-- ============================================================================

-- ⚠️ IMPORTANTE: Cambiar por el nombre real de tu base de datos
-- USE [tu_base_datos];  -- Descomentar y cambiar por el nombre real
GO

PRINT '========================================';
PRINT 'FASE 2: Creando índices compuestos críticos';
PRINT '========================================';
GO

-- ============================================================================
-- 1. ÍNDICE COMPUESTO: usuario (cliente_id + es_activo + fecha_creacion)
-- ============================================================================
-- Optimiza queries que:
-- - Listan usuarios activos de un cliente ordenados por fecha
-- - Filtran usuarios activos por cliente con paginación
-- - Reportes de usuarios por fecha de creación

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes 
    WHERE name = 'IDX_usuario_cliente_activo_fecha' 
    AND object_id = OBJECT_ID('usuario')
)
BEGIN
    PRINT 'Creando IDX_usuario_cliente_activo_fecha...';
    CREATE NONCLUSTERED INDEX IDX_usuario_cliente_activo_fecha 
    ON usuario(cliente_id, es_activo, fecha_creacion DESC)
    WHERE es_eliminado = 0;
    PRINT '✅ IDX_usuario_cliente_activo_fecha creado';
END
ELSE
BEGIN
    PRINT '⚠️ IDX_usuario_cliente_activo_fecha ya existe, omitiendo';
END
GO

-- ============================================================================
-- 2. ÍNDICE COMPUESTO: rol (cliente_id + es_activo + nivel_acceso)
-- ============================================================================
-- Optimiza queries que:
-- - Listan roles activos de un cliente ordenados por nivel
-- - Filtran roles por nivel de acceso
-- - Validaciones de permisos por nivel

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes 
    WHERE name = 'IDX_rol_cliente_activo_nivel' 
    AND object_id = OBJECT_ID('rol')
)
BEGIN
    PRINT 'Creando IDX_rol_cliente_activo_nivel...';
    CREATE NONCLUSTERED INDEX IDX_rol_cliente_activo_nivel 
    ON rol(cliente_id, es_activo, nivel_acceso);
    PRINT '✅ IDX_rol_cliente_activo_nivel creado';
END
ELSE
BEGIN
    PRINT '⚠️ IDX_rol_cliente_activo_nivel ya existe, omitiendo';
END
GO

-- ============================================================================
-- 3. ÍNDICE COMPUESTO: refresh_tokens (usuario_id + cliente_id + is_revoked + expires_at)
-- ============================================================================
-- Optimiza queries que:
-- - Validan tokens activos de un usuario
-- - Limpian tokens expirados/revocados
-- - Listan sesiones activas de un usuario

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes 
    WHERE name = 'IDX_refresh_token_usuario_cliente_revoked_expires' 
    AND object_id = OBJECT_ID('refresh_tokens')
)
BEGIN
    PRINT 'Creando IDX_refresh_token_usuario_cliente_revoked_expires...';
    CREATE NONCLUSTERED INDEX IDX_refresh_token_usuario_cliente_revoked_expires 
    ON refresh_tokens(usuario_id, cliente_id, is_revoked, expires_at);
    PRINT '✅ IDX_refresh_token_usuario_cliente_revoked_expires creado';
END
ELSE
BEGIN
    PRINT '⚠️ IDX_refresh_token_usuario_cliente_revoked_expires ya existe, omitiendo';
END
GO

-- ============================================================================
-- 4. ÍNDICE COMPUESTO: rol_menu_permiso (cliente_id + rol_id + menu_id)
-- ============================================================================
-- Optimiza queries que:
-- - Obtienen permisos de un rol en un menú específico
-- - Validan permisos granulares
-- - Listan permisos por rol y menú

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes 
    WHERE name = 'IDX_permiso_cliente_rol_menu' 
    AND object_id = OBJECT_ID('rol_menu_permiso')
)
BEGIN
    PRINT 'Creando IDX_permiso_cliente_rol_menu...';
    CREATE NONCLUSTERED INDEX IDX_permiso_cliente_rol_menu 
    ON rol_menu_permiso(cliente_id, rol_id, menu_id);
    PRINT '✅ IDX_permiso_cliente_rol_menu creado';
END
ELSE
BEGIN
    PRINT '⚠️ IDX_permiso_cliente_rol_menu ya existe, omitiendo';
END
GO

-- ============================================================================
-- 5. ÍNDICE COMPUESTO: usuario_rol (usuario_id + cliente_id + es_activo)
-- ============================================================================
-- Optimiza queries que:
-- - Obtienen roles activos de un usuario
-- - Validan asignaciones de roles
-- - Listan usuarios con sus roles

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes 
    WHERE name = 'IDX_usuario_rol_usuario_cliente_activo' 
    AND object_id = OBJECT_ID('usuario_rol')
)
BEGIN
    PRINT 'Creando IDX_usuario_rol_usuario_cliente_activo...';
    CREATE NONCLUSTERED INDEX IDX_usuario_rol_usuario_cliente_activo 
    ON usuario_rol(usuario_id, cliente_id, es_activo);
    PRINT '✅ IDX_usuario_rol_usuario_cliente_activo creado';
END
ELSE
BEGIN
    PRINT '⚠️ IDX_usuario_rol_usuario_cliente_activo ya existe, omitiendo';
END
GO

-- ============================================================================
-- 6. ÍNDICE COMPUESTO: auth_audit_log (cliente_id + evento + fecha_evento)
-- ============================================================================
-- Optimiza queries que:
-- - Reportes de eventos de autenticación por tipo
-- - Auditoría de eventos específicos por fecha
-- - Análisis de seguridad por evento

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes 
    WHERE name = 'IDX_audit_cliente_evento_fecha' 
    AND object_id = OBJECT_ID('auth_audit_log')
)
BEGIN
    PRINT 'Creando IDX_audit_cliente_evento_fecha...';
    CREATE NONCLUSTERED INDEX IDX_audit_cliente_evento_fecha 
    ON auth_audit_log(cliente_id, evento, fecha_evento DESC);
    PRINT '✅ IDX_audit_cliente_evento_fecha creado';
END
ELSE
BEGIN
    PRINT '⚠️ IDX_audit_cliente_evento_fecha ya existe, omitiendo';
END
GO

-- ============================================================================
-- VERIFICACIÓN FINAL
-- ============================================================================

PRINT '';
PRINT '========================================';
PRINT 'Verificando índices creados...';
PRINT '========================================';

SELECT 
    OBJECT_NAME(object_id) AS tabla,
    name AS indice,
    type_desc AS tipo
FROM sys.indexes
WHERE name IN (
    'IDX_usuario_cliente_activo_fecha',
    'IDX_rol_cliente_activo_nivel',
    'IDX_refresh_token_usuario_cliente_revoked_expires',
    'IDX_permiso_cliente_rol_menu',
    'IDX_usuario_rol_usuario_cliente_activo',
    'IDX_audit_cliente_evento_fecha'
)
AND OBJECT_NAME(object_id) IN (
    'usuario', 'rol', 'refresh_tokens', 
    'rol_menu_permiso', 'usuario_rol', 'auth_audit_log'
)
ORDER BY tabla, name;

PRINT '';
PRINT '========================================';
PRINT '✅ FASE 2: Índices compuestos completados';
PRINT '========================================';
PRINT '';
PRINT 'PRÓXIMOS PASOS:';
PRINT '1. Verificar que todos los índices se crearon correctamente';
PRINT '2. Monitorear performance de queries después de la creación';
PRINT '3. Ejecutar UPDATE STATISTICS si es necesario';
PRINT '4. Revisar uso de espacio en disco';
PRINT '';

