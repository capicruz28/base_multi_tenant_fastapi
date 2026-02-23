-- ============================================================================
-- SCRIPT: TABLAS RBAC - BD CENTRAL (permiso + rol_permiso)
-- DESCRIPCIÓN: Catálogo de permisos de negocio y asignación rol → permiso.
-- USO: Ejecutar UNA SOLA VEZ en bd_hybrid_sistema_central (después de TABLAS_BD_CENTRAL.sql).
-- NO ROMPE: No modifica tablas existentes; solo añade tablas nuevas.
-- ============================================================================

-- ============================================================================
-- Tabla: permiso (catálogo global, solo en BD central)
-- ============================================================================
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'permiso')
BEGIN
    CREATE TABLE permiso (
        permiso_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        codigo NVARCHAR(100) NOT NULL UNIQUE,
        nombre NVARCHAR(150) NOT NULL,
        descripcion NVARCHAR(500) NULL,
        modulo_id UNIQUEIDENTIFIER NULL,
        recurso NVARCHAR(80) NOT NULL,
        accion NVARCHAR(30) NOT NULL,
        es_activo BIT DEFAULT 1 NOT NULL,
        fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
        fecha_actualizacion DATETIME NULL,
        CONSTRAINT FK_permiso_modulo FOREIGN KEY (modulo_id)
            REFERENCES modulo(modulo_id) ON DELETE SET NULL
    );
    CREATE UNIQUE INDEX UQ_permiso_codigo ON permiso(codigo);
    CREATE INDEX IDX_permiso_modulo ON permiso(modulo_id);
    CREATE INDEX IDX_permiso_activo ON permiso(es_activo);
    PRINT 'Tabla permiso creada.';
END
ELSE
    PRINT 'Tabla permiso ya existe.';
GO

-- ============================================================================
-- Tabla: rol_permiso (asignación rol → permiso por tenant, en central)
-- ============================================================================
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'rol_permiso')
BEGIN
    CREATE TABLE rol_permiso (
        rol_permiso_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        cliente_id UNIQUEIDENTIFIER NOT NULL,
        rol_id UNIQUEIDENTIFIER NOT NULL,
        permiso_id UNIQUEIDENTIFIER NOT NULL,
        fecha_creacion DATETIME DEFAULT GETDATE() NOT NULL,
        CONSTRAINT FK_rol_permiso_rol FOREIGN KEY (rol_id)
            REFERENCES rol(rol_id) ON DELETE CASCADE,
        CONSTRAINT FK_rol_permiso_permiso FOREIGN KEY (permiso_id)
            REFERENCES permiso(permiso_id) ON DELETE CASCADE,
        CONSTRAINT FK_rol_permiso_cliente FOREIGN KEY (cliente_id)
            REFERENCES cliente(cliente_id) ON DELETE CASCADE,
        CONSTRAINT UQ_rol_permiso UNIQUE (cliente_id, rol_id, permiso_id)
    );
    CREATE INDEX IDX_rol_permiso_rol ON rol_permiso(rol_id);
    CREATE INDEX IDX_rol_permiso_permiso ON rol_permiso(permiso_id);
    CREATE INDEX IDX_rol_permiso_cliente ON rol_permiso(cliente_id);
    PRINT 'Tabla rol_permiso creada.';
END
ELSE
    PRINT 'Tabla rol_permiso ya existe.';
GO

PRINT 'Script RBAC tablas central completado.';
