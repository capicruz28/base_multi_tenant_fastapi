-- ============================================================================
-- SCRIPT PARA CREAR STORED PROCEDURES EN TODAS LAS BASES DE DATOS
-- ============================================================================
-- Este script ayuda a crear los SPs necesarios en todas las BDs del sistema
-- ============================================================================

-- ============================================================================
-- PASO 1: Crear SP en Base de Datos Central
-- ============================================================================
USE [bd_hybrid_sistema_central];  -- ⚠️ CAMBIAR por el nombre real de tu BD central
GO

-- Ejecutar SP_OBTENER_MENU_USUARIO.sql aquí
-- (Copiar contenido de SP_OBTENER_MENU_USUARIO.sql)

-- Ejecutar SP_VALIDAR_ACCESO_MENU.sql aquí
-- (Copiar contenido de SP_VALIDAR_ACCESO_MENU.sql)

GO

-- ============================================================================
-- PASO 2: Crear SP en Cada Base de Datos de Cliente (Multi-DB)
-- ============================================================================
-- Para cada cliente con BD dedicada, ejecutar:

-- Cliente 1: ACME
USE [bd_cliente_acme];  -- ⚠️ CAMBIAR por el nombre real de la BD del cliente
GO

-- Ejecutar SP_OBTENER_MENU_USUARIO.sql aquí
-- (Copiar contenido de SP_OBTENER_MENU_USUARIO.sql)

-- Ejecutar SP_VALIDAR_ACCESO_MENU.sql aquí
-- (Copiar contenido de SP_VALIDAR_ACCESO_MENU.sql)

GO

-- ============================================================================
-- PASO 3: Verificar que los SPs fueron creados
-- ============================================================================
-- Ejecutar en cada BD:

SELECT 
    ROUTINE_SCHEMA,
    ROUTINE_NAME,
    ROUTINE_TYPE,
    CREATED,
    LAST_ALTERED
FROM INFORMATION_SCHEMA.ROUTINES
WHERE ROUTINE_NAME IN ('sp_obtener_menu_usuario', 'sp_validar_acceso_menu')
ORDER BY ROUTINE_NAME;

-- Debe retornar 2 filas (uno por cada SP) en cada BD

-- ============================================================================
-- NOTAS:
-- ============================================================================
-- 1. Este script es una guía. Debes ejecutar los SPs en cada BD manualmente
-- 2. Para automatizar, puedes crear un script PowerShell o Python que:
--    - Obtenga lista de todas las BDs de clientes
--    - Ejecute los scripts SQL en cada una
-- 3. Los SPs deben crearse también cuando se crea un nuevo cliente con BD dedicada
-- ============================================================================

