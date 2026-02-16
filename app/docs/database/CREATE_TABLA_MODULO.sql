-- ============================================================================
-- SCRIPT: Crear tabla modulo
-- Propósito: Crear la tabla modulo que falta en la base de datos
-- Base de datos: bd_hybrid_sistema_central (o la BD central del sistema)
-- Fecha: 2024-12-19
-- ============================================================================

USE bd_hybrid_sistema_central;
GO

-- Verificar si la tabla ya existe
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'dbo.modulo') AND type in (N'U'))
BEGIN
    PRINT 'Creando tabla modulo...';
    
    -- ============================================================================
    -- TABLA: modulo
    -- Propósito: Catálogo maestro de módulos ERP disponibles en el sistema
    -- Alcance: GLOBAL (no por cliente)
    -- ============================================================================
    CREATE TABLE modulo (
        modulo_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        
        -- ======================================== 
        -- IDENTIFICACIÓN
        -- ======================================== 
        codigo NVARCHAR(30) NOT NULL UNIQUE,
        -- Código único para referencia en código
        -- Ejemplos: 'LOGISTICA', 'ALMACEN', 'VENTAS', 'CONTABILIDAD'
        
        nombre NVARCHAR(100) NOT NULL,
        -- Nombre descriptivo para mostrar en UI
        -- Ejemplo: 'Gestión Logística', 'Control de Almacén'
        
        descripcion NVARCHAR(500) NULL,
        -- Descripción detallada del módulo y sus funcionalidades
        
        icono NVARCHAR(50) NULL,
        -- Icono representativo (Material Icons, FontAwesome, etc.)
        -- Ejemplos: 'local_shipping', 'warehouse', 'point_of_sale'
        
        color NVARCHAR(7) DEFAULT '#1976D2',
        -- Color principal del módulo en HEX para UI
        
        -- ======================================== 
        -- CLASIFICACIÓN Y LICENCIAMIENTO
        -- ======================================== 
        categoria NVARCHAR(30) DEFAULT 'operaciones',
        -- Agrupa módulos por tipo: 'operaciones', 'finanzas', 'rrhh', 'produccion'
        
        es_core BIT DEFAULT 0,
        -- TRUE = Módulo esencial (siempre disponible, sin costo adicional)
        -- FALSE = Módulo opcional/premium
        
        requiere_licencia BIT DEFAULT 1,
        -- TRUE = Requiere contratación/pago adicional
        -- FALSE = Incluido en plan base
        
        precio_mensual DECIMAL(10,2) NULL,
        -- Precio mensual del módulo (NULL = sin costo)
        
        -- ======================================== 
        -- DEPENDENCIAS ENTRE MÓDULOS
        -- ======================================== 
        modulos_requeridos NVARCHAR(MAX) NULL,
        -- JSON array con códigos de módulos que deben estar activos
        -- Ejemplo: '["INVENTARIO", "CONTABILIDAD"]'
        
        -- ======================================== 
        -- CONTROL Y ORDEN
        -- ======================================== 
        orden INT DEFAULT 0,
        -- Orden de visualización en catálogos y menús
        
        es_activo BIT DEFAULT 1,
        -- Habilitar/deshabilitar módulo del catálogo
        
        fecha_creacion DATETIME DEFAULT GETDATE(),
        fecha_actualizacion DATETIME NULL,
        
        -- ======================================== 
        -- METADATA EXTENSIBLE
        -- ======================================== 
        configuracion_defecto NVARCHAR(MAX) NULL
        -- JSON con configuración por defecto al activar el módulo
    );
    
    -- Crear índices
    CREATE INDEX IDX_modulo_codigo ON modulo(codigo);
    CREATE INDEX IDX_modulo_activo ON modulo(es_activo, orden);
    CREATE INDEX IDX_modulo_categoria ON modulo(categoria, orden);
    
    PRINT 'Tabla modulo creada exitosamente.';
END
ELSE
BEGIN
    PRINT 'La tabla modulo ya existe.';
END
GO

-- Verificar creación
SELECT 
    TABLE_NAME,
    TABLE_SCHEMA
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_NAME = 'modulo';
GO
