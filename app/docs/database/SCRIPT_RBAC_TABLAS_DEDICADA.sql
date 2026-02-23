-- ============================================================================
-- SCRIPT: TABLA RBAC - BD DEDICADA (solo rol_permiso)
-- DESCRIPCIÓN: Asignación rol → permiso por tenant. permiso_id referencia
--              tabla permiso en BD CENTRAL (sin FK; validar en aplicación).
-- USO: Ejecutar en cada BD dedicada de cliente (después de TABLAS_BD_DEDICADA.sql).
-- NO ROMPE: Solo añade tabla nueva.
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
        CONSTRAINT UQ_rol_permiso UNIQUE (cliente_id, rol_id, permiso_id)
    );
    CREATE INDEX IDX_rol_permiso_rol ON rol_permiso(rol_id);
    CREATE INDEX IDX_rol_permiso_permiso ON rol_permiso(permiso_id);
    CREATE INDEX IDX_rol_permiso_cliente ON rol_permiso(cliente_id);
    PRINT 'Tabla rol_permiso creada en BD dedicada.';
END
ELSE
    PRINT 'Tabla rol_permiso ya existe.';
GO

-- NOTA: No hay FK a permiso ni a cliente; permiso está en BD central.
-- La aplicación debe validar que permiso_id exista en central al asignar.
