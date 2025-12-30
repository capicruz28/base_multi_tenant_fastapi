-- ============================================================================
-- STORED PROCEDURE: sp_validar_acceso_menu
-- Propósito: Validar si un usuario tiene acceso a un menú específico
-- Uso: Backend lo llama para validar acceso antes de mostrar contenido
-- ============================================================================
-- IMPORTANTE: Este SP debe ejecutarse en CADA base de datos de cliente (Multi-DB)
-- y también en la base de datos central (Single-DB)
-- ============================================================================

IF OBJECT_ID('sp_validar_acceso_menu', 'P') IS NOT NULL
    DROP PROCEDURE sp_validar_acceso_menu;
GO

CREATE PROCEDURE sp_validar_acceso_menu
    @usuario_id UNIQUEIDENTIFIER,
    @menu_id UNIQUEIDENTIFIER,
    @cliente_id UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @tiene_acceso BIT = 0;
    DECLARE @permisos_json NVARCHAR(MAX) = NULL;
    
    -- Verificar si el usuario tiene acceso al menú
    SELECT TOP 1
        @tiene_acceso = 1,
        @permisos_json = (
            SELECT 
                p.puede_ver,
                p.puede_crear,
                p.puede_editar,
                p.puede_eliminar,
                p.puede_exportar,
                p.puede_imprimir,
                p.puede_aprobar,
                p.permisos_extra
            FROM rol_menu_permiso p
            INNER JOIN usuario_rol ur ON p.rol_id = ur.rol_id
            WHERE p.menu_id = @menu_id
                AND p.cliente_id = @cliente_id
                AND ur.usuario_id = @usuario_id
                AND ur.cliente_id = @cliente_id
                AND ur.es_activo = 1
                AND (ur.fecha_expiracion IS NULL OR ur.fecha_expiracion > GETDATE())
                AND p.puede_ver = 1
            FOR JSON PATH
        )
    FROM modulo_menu m
    INNER JOIN modulo mod ON m.modulo_id = mod.modulo_id
    INNER JOIN cliente_modulo cm ON mod.modulo_id = cm.modulo_id
        AND cm.cliente_id = @cliente_id
        AND cm.esta_activo = 1
        AND (cm.fecha_vencimiento IS NULL OR cm.fecha_vencimiento > GETDATE())
    INNER JOIN rol_menu_permiso p ON m.menu_id = p.menu_id
        AND p.cliente_id = @cliente_id
    INNER JOIN usuario_rol ur ON p.rol_id = ur.rol_id
        AND ur.usuario_id = @usuario_id
        AND ur.cliente_id = @cliente_id
        AND ur.es_activo = 1
        AND (ur.fecha_expiracion IS NULL OR ur.fecha_expiracion > GETDATE())
    WHERE m.menu_id = @menu_id
        AND m.es_activo = 1
        AND m.es_visible = 1
        AND mod.es_activo = 1
        AND (m.cliente_id IS NULL OR m.cliente_id = @cliente_id)
        AND p.puede_ver = 1;
    
    -- Retornar resultado
    SELECT 
        @tiene_acceso AS tiene_acceso,
        @permisos_json AS permisos_json;
END;
GO

-- ============================================================================
-- NOTAS IMPORTANTES:
-- ============================================================================
-- 1. Este SP valida acceso a un menú específico
-- 2. Retorna 1 si tiene acceso, 0 si no
-- 3. También retorna los permisos en formato JSON
-- 4. Debe ejecutarse en cada BD de cliente y en la BD central
-- ============================================================================

