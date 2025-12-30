-- ============================================================================
-- STORED PROCEDURE: sp_obtener_menu_usuario
-- Propósito: Obtener el menú completo de un usuario con todos sus permisos
-- Uso: Backend lo llama para construir el sidebar/navegación del frontend
-- ============================================================================
-- IMPORTANTE: Este SP debe ejecutarse en CADA base de datos de cliente (Multi-DB)
-- y también en la base de datos central (Single-DB)
-- ============================================================================

IF OBJECT_ID('sp_obtener_menu_usuario', 'P') IS NOT NULL
    DROP PROCEDURE sp_obtener_menu_usuario;
GO

CREATE PROCEDURE sp_obtener_menu_usuario
    @usuario_id UNIQUEIDENTIFIER,
    @cliente_id UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Obtener menús con permisos agregados del usuario
    SELECT 
        -- Datos del módulo
        mod.modulo_id,
        mod.codigo AS modulo_codigo,
        mod.nombre AS modulo_nombre,
        mod.descripcion AS modulo_descripcion,
        mod.icono AS modulo_icono,
        mod.color AS modulo_color,
        mod.categoria AS modulo_categoria,
        mod.orden AS modulo_orden,
        
        -- Datos de la sección
        sec.seccion_id,
        sec.codigo AS seccion_codigo,
        sec.nombre AS seccion_nombre,
        sec.descripcion AS seccion_descripcion,
        sec.icono AS seccion_icono,
        sec.orden AS seccion_orden,
        
        -- Datos del menú
        m.menu_id,
        m.codigo AS menu_codigo,
        m.nombre AS menu_nombre,
        m.descripcion AS menu_descripcion,
        m.icono AS menu_icono,
        m.ruta,
        m.menu_padre_id,
        m.nivel,
        m.tipo_menu,
        m.orden AS menu_orden,
        m.requiere_autenticacion,
        m.configuracion_json AS menu_configuracion,
        
        -- Permisos agregados (MAX = si tiene el permiso en al menos 1 rol)
        MAX(CAST(p.puede_ver AS INT)) AS puede_ver,
        MAX(CAST(p.puede_crear AS INT)) AS puede_crear,
        MAX(CAST(p.puede_editar AS INT)) AS puede_editar,
        MAX(CAST(p.puede_eliminar AS INT)) AS puede_eliminar,
        MAX(CAST(p.puede_exportar AS INT)) AS puede_exportar,
        MAX(CAST(p.puede_imprimir AS INT)) AS puede_imprimir,
        MAX(CAST(p.puede_aprobar AS INT)) AS puede_aprobar,
        
        -- Permisos extra en JSON (combinar de todos los roles)
        -- Nota: Si múltiples roles tienen permisos_extra, se toma el último
        -- Una mejor implementación podría mergear los JSONs
        (
            SELECT TOP 1 p2.permisos_extra 
            FROM rol_menu_permiso p2
            INNER JOIN usuario_rol ur2 ON p2.rol_id = ur2.rol_id
            WHERE p2.menu_id = m.menu_id 
                AND ur2.usuario_id = @usuario_id
                AND ur2.cliente_id = @cliente_id
                AND ur2.es_activo = 1
                AND p2.permisos_extra IS NOT NULL
            ORDER BY p2.fecha_creacion DESC
        ) AS permisos_extra,
        
        -- Información del cliente-módulo
        cm.fecha_vencimiento,
        cm.modo_prueba,
        cm.limite_usuarios,
        cm.limite_registros
        
    FROM modulo_menu m
    
    -- JOIN con módulo (OBLIGATORIO - todo menú pertenece a un módulo)
    INNER JOIN modulo mod ON m.modulo_id = mod.modulo_id
    
    -- JOIN con sección (OPCIONAL - algunos menús no tienen sección)
    LEFT JOIN modulo_seccion sec ON m.seccion_id = sec.seccion_id
    
    -- JOIN con permisos del menú
    INNER JOIN rol_menu_permiso p ON m.menu_id = p.menu_id 
        AND p.cliente_id = @cliente_id
    
    -- JOIN con roles del usuario
    INNER JOIN usuario_rol ur ON p.rol_id = ur.rol_id 
        AND ur.usuario_id = @usuario_id 
        AND ur.cliente_id = @cliente_id
        AND ur.es_activo = 1
        AND (ur.fecha_expiracion IS NULL OR ur.fecha_expiracion > GETDATE())
    
    -- JOIN con módulos activos del cliente
    INNER JOIN cliente_modulo cm ON mod.modulo_id = cm.modulo_id 
        AND cm.cliente_id = @cliente_id
        AND cm.esta_activo = 1
        AND (cm.fecha_vencimiento IS NULL OR cm.fecha_vencimiento > GETDATE())
    
    WHERE 
        -- Filtros básicos
        m.es_activo = 1
        AND m.es_visible = 1
        AND mod.es_activo = 1
        AND (sec.es_activo = 1 OR sec.seccion_id IS NULL)
        
        -- Menú debe ser global O del cliente específico
        AND (m.cliente_id IS NULL OR m.cliente_id = @cliente_id)
        
        -- Usuario debe tener permiso de ver
        AND p.puede_ver = 1
        
    GROUP BY 
        -- Módulo
        mod.modulo_id, mod.codigo, mod.nombre, mod.descripcion, 
        mod.icono, mod.color, mod.categoria, mod.orden,
        
        -- Sección
        sec.seccion_id, sec.codigo, sec.nombre, sec.descripcion,
        sec.icono, sec.orden,
        
        -- Menú
        m.menu_id, m.codigo, m.nombre, m.descripcion, m.icono, 
        m.ruta, m.menu_padre_id, m.nivel, m.tipo_menu, m.orden,
        m.requiere_autenticacion, m.configuracion_json,
        
        -- Cliente-módulo
        cm.fecha_vencimiento, cm.modo_prueba, 
        cm.limite_usuarios, cm.limite_registros
        
    ORDER BY 
        mod.orden ASC,                    -- Ordenar módulos
        ISNULL(sec.orden, 999) ASC,       -- Ordenar secciones (NULL al final)
        m.nivel ASC,                      -- Ordenar por nivel (padres primero)
        m.orden ASC;                      -- Ordenar menús dentro de sección
END;
GO

-- ============================================================================
-- NOTAS IMPORTANTES:
-- ============================================================================
-- 1. Este SP debe ejecutarse en CADA base de datos de cliente (Multi-DB)
-- 2. También debe ejecutarse en la base de datos central (Single-DB)
-- 3. El SP filtra por módulos activos del cliente
-- 4. Agrega permisos de múltiples roles (MAX)
-- 5. Respeta la jerarquía: módulo → sección → menú → submenú
-- ============================================================================

