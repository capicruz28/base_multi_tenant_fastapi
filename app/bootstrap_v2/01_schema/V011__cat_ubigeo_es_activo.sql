-- -----------------------------------------------------------------------------
-- Migración: agregar es_activo a catálogos ubigeo (GLOBAL)
-- Tablas: cat_departamento, cat_provincia, cat_distrito
-- Objetivo: estandarizar soft delete y filtros solo_activos (alineado a cat_pais/cat_moneda)
-- -----------------------------------------------------------------------------

-- cat_departamento
IF COL_LENGTH('cat_departamento', 'es_activo') IS NULL
BEGIN
    ALTER TABLE cat_departamento
        ADD es_activo BIT NOT NULL
            CONSTRAINT DF_cat_departamento_es_activo DEFAULT (1);
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IDX_depto_activo' AND object_id = OBJECT_ID('cat_departamento')
)
BEGIN
    CREATE INDEX IDX_depto_activo ON cat_departamento(es_activo);
END;
GO

-- cat_provincia
IF COL_LENGTH('cat_provincia', 'es_activo') IS NULL
BEGIN
    ALTER TABLE cat_provincia
        ADD es_activo BIT NOT NULL
            CONSTRAINT DF_cat_provincia_es_activo DEFAULT (1);
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IDX_prov_activo' AND object_id = OBJECT_ID('cat_provincia')
)
BEGIN
    CREATE INDEX IDX_prov_activo ON cat_provincia(es_activo);
END;
GO

-- cat_distrito
IF COL_LENGTH('cat_distrito', 'es_activo') IS NULL
BEGIN
    ALTER TABLE cat_distrito
        ADD es_activo BIT NOT NULL
            CONSTRAINT DF_cat_distrito_es_activo DEFAULT (1);
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IDX_dist_activo' AND object_id = OBJECT_ID('cat_distrito')
)
BEGIN
    CREATE INDEX IDX_dist_activo ON cat_distrito(es_activo);
END;
GO

