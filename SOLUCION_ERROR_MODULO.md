# 🔧 SOLUCIÓN: Error "Invalid object name 'modulo'"

## Problema

Al consumir el endpoint `/api/v1/modulos-v2/`, se produce el error:

```
Invalid object name 'modulo'. (208)
```

## Causa

La tabla `modulo` no existe en la base de datos `bd_hybrid_sistema_central`.

## Solución

### Opción 1: Ejecutar Script SQL (Recomendado)

Ejecuta el script SQL creado en:
```
app/docs/database/CREATE_TABLA_MODULO.sql
```

**Pasos:**

1. Conecta a tu base de datos SQL Server (bd_hybrid_sistema_central)
2. Ejecuta el script `CREATE_TABLA_MODULO.sql`
3. Verifica que la tabla se haya creado correctamente

### Opción 2: Ejecutar desde SQL Server Management Studio

```sql
USE bd_hybrid_sistema_central;
GO

-- Verificar si existe
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'dbo.modulo') AND type in (N'U'))
BEGIN
    CREATE TABLE modulo (
        modulo_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        codigo NVARCHAR(30) NOT NULL UNIQUE,
        nombre NVARCHAR(100) NOT NULL,
        descripcion NVARCHAR(500) NULL,
        icono NVARCHAR(50) NULL,
        color NVARCHAR(7) DEFAULT '#1976D2',
        categoria NVARCHAR(30) DEFAULT 'operaciones',
        es_core BIT DEFAULT 0,
        requiere_licencia BIT DEFAULT 1,
        precio_mensual DECIMAL(10,2) NULL,
        modulos_requeridos NVARCHAR(MAX) NULL,
        orden INT DEFAULT 0,
        es_activo BIT DEFAULT 1,
        fecha_creacion DATETIME DEFAULT GETDATE(),
        fecha_actualizacion DATETIME NULL,
        configuracion_defecto NVARCHAR(MAX) NULL
    );
    
    CREATE INDEX IDX_modulo_codigo ON modulo(codigo);
    CREATE INDEX IDX_modulo_activo ON modulo(es_activo, orden);
    CREATE INDEX IDX_modulo_categoria ON modulo(categoria, orden);
END
GO
```

### Opción 3: Usar Alembic o Migraciones

Si tienes un sistema de migraciones configurado, puedes crear una migración basada en la definición de `ModuloTable` en:
```
app/infrastructure/database/tables_modulos.py
```

## Verificación

Después de crear la tabla, verifica que existe:

```sql
SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'modulo';
```

O desde la aplicación, prueba nuevamente el endpoint:
```
GET /api/v1/modulos-v2/
```

## Nota Importante

Esta tabla es **GLOBAL** (no por tenant), por lo que debe estar en la base de datos central (`bd_hybrid_sistema_central`). El servicio `ModuloService` usa `DatabaseConnection.ADMIN` que apunta a esta base de datos central.

## Datos de Prueba (Opcional)

Si quieres insertar algunos módulos de ejemplo:

```sql
INSERT INTO modulo (codigo, nombre, descripcion, categoria, es_core, requiere_licencia, orden, es_activo)
VALUES 
    ('AUTH', 'Autenticación', 'Sistema de autenticación y autorización', 'core', 1, 0, 1, 1),
    ('USUARIOS', 'Gestión de Usuarios', 'Administración de usuarios del sistema', 'core', 1, 0, 2, 1),
    ('RBAC', 'Control de Accesos', 'Roles y permisos', 'core', 1, 0, 3, 1),
    ('MENUS', 'Gestión de Menús', 'Administración de menús y navegación', 'core', 1, 0, 4, 1);
```

---

**Creado:** 2024-12-19  
**Relacionado con:** Refactorización FASE 2 (SQL Modular)
