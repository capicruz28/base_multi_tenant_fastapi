-- ============================================================================
-- bootstrap_v2 | official bootstrap line (copy; do not edit logic here)
-- Source (legacy, immutable): (see BOOTSTRAP_MANIFEST.md)
-- Layer: catalog
-- ============================================================================
---------------------------------------------------------------------------
-- SCRIPT: Migración de menús hardcodeados (admin / superadmin) a RBAC BD
-- BD: CENTRAL (SQL Server)
-- Idempotente: usa IF/EXISTS y NOT EXISTS
---------------------------------------------------------------------------

SET NOCOUNT ON;
GO

---------------------------------------------------------------------------
-- 1. Crear módulo SYS_ADMIN si no existe
---------------------------------------------------------------------------

DECLARE @modulo_sys_admin_id UNIQUEIDENTIFIER;

SELECT @modulo_sys_admin_id = modulo_id
FROM modulo
WHERE codigo = 'SYS_ADMIN';

IF @modulo_sys_admin_id IS NULL
BEGIN
    SET @modulo_sys_admin_id = NEWID();

    INSERT INTO modulo (
        modulo_id,
        codigo,
        nombre,
        descripcion,
        icono,
        color,
        categoria,
        es_core,
        requiere_licencia,
        precio_mensual,
        modulos_requeridos,
        orden,
        es_activo,
        fecha_creacion
    )
    VALUES (
        @modulo_sys_admin_id,
        'SYS_ADMIN',
        N'Administración del Sistema',
        N'Módulo de administración global y de tenant (usuarios, clientes, módulos).',
        N'Settings',
        N'#374151',
        N'sistema',
        1,          -- es_core
        0,          -- requiere_licencia
        NULL,       -- precio_mensual
        NULL,       -- modulos_requeridos
        100,        -- orden (al final)
        1,          -- es_activo
        GETDATE()
    );
END;
GO

---------------------------------------------------------------------------
-- 2. Crear secciones del módulo SYS_ADMIN (Tenant / Global)
---------------------------------------------------------------------------

DECLARE @modulo_sys_admin_id UNIQUEIDENTIFIER;
DECLARE @seccion_tenant_admin_id UNIQUEIDENTIFIER;
DECLARE @seccion_super_admin_id UNIQUEIDENTIFIER;
DECLARE @seccion_catalogos_globales_id UNIQUEIDENTIFIER;

SELECT @modulo_sys_admin_id = modulo_id
FROM modulo
WHERE codigo = 'SYS_ADMIN';

-- Sección: Administración del Tenant
SELECT @seccion_tenant_admin_id = seccion_id
FROM modulo_seccion
WHERE modulo_id = @modulo_sys_admin_id
  AND codigo = 'TENANT_ADMIN';

IF @seccion_tenant_admin_id IS NULL
BEGIN
    SET @seccion_tenant_admin_id = NEWID();

    INSERT INTO modulo_seccion (
        seccion_id,
        modulo_id,
        codigo,
        nombre,
        descripcion,
        icono,
        orden,
        es_seccion_sistema,
        es_activo,
        fecha_creacion
    )
    VALUES (
        @seccion_tenant_admin_id,
        @modulo_sys_admin_id,
        N'TENANT_ADMIN',
        N'Administración',
        N'Gestión de usuarios, roles y sesiones dentro de un tenant.',
        N'Users',
        1,
        1,
        1,
        GETDATE()
    );
END;

-- Sección: Administración Global
SELECT @seccion_super_admin_id = seccion_id
FROM modulo_seccion
WHERE modulo_id = @modulo_sys_admin_id
  AND codigo = 'SUPER_ADMIN';

IF @seccion_super_admin_id IS NULL
BEGIN
    SET @seccion_super_admin_id = NEWID();

    INSERT INTO modulo_seccion (
        seccion_id,
        modulo_id,
        codigo,
        nombre,
        descripcion,
        icono,
        orden,
        es_seccion_sistema,
        es_activo,
        fecha_creacion
    )
    VALUES (
        @seccion_super_admin_id,
        @modulo_sys_admin_id,
        N'SUPER_ADMIN',
        N'Administración',
        N'Gestión de clientes, módulos y auditoría a nivel plataforma.',
        N'Shield',
        2,
        1,
        1,
        GETDATE()
    );
END;

-- Sección: Catálogos Globales (Super Admin)
SELECT @seccion_catalogos_globales_id = seccion_id
FROM modulo_seccion
WHERE modulo_id = @modulo_sys_admin_id
  AND codigo = 'GLOBAL_CATALOGS';

IF @seccion_catalogos_globales_id IS NULL
BEGIN
    SET @seccion_catalogos_globales_id = NEWID();

    INSERT INTO modulo_seccion (
        seccion_id,
        modulo_id,
        codigo,
        nombre,
        descripcion,
        icono,
        orden,
        es_seccion_sistema,
        es_activo,
        fecha_creacion
    )
    VALUES (
        @seccion_catalogos_globales_id,
        @modulo_sys_admin_id,
        N'GLOBAL_CATALOGS',
        N'Catalogos',
        N'Administración de catálogos globales (países y ubigeo) por Superadmin.',
        N'Globe',
        3,
        1,
        1,
        GETDATE()
    );
END;
GO

---------------------------------------------------------------------------
-- 3. Crear menús equivalentes en modulo_menu (cliente_id = NULL)
--    a) Administración del Tenant (adminMenu.ts)
---------------------------------------------------------------------------

DECLARE @modulo_sys_admin_id UNIQUEIDENTIFIER;
DECLARE @seccion_tenant_admin_id UNIQUEIDENTIFIER;

SELECT @modulo_sys_admin_id = modulo_id
FROM modulo
WHERE codigo = 'SYS_ADMIN';

SELECT @seccion_tenant_admin_id = seccion_id
FROM modulo_seccion
WHERE modulo_id = @modulo_sys_admin_id
  AND codigo = 'TENANT_ADMIN';

-- Menú: Gestión de Usuarios (/admin/usuarios)
IF NOT EXISTS (
    SELECT 1
    FROM modulo_menu
    WHERE codigo = N'SYS_ADMIN.TENANT.USERS'
      AND cliente_id IS NULL
)
BEGIN
    INSERT INTO modulo_menu (
        menu_id,
        modulo_id,
        seccion_id,
        cliente_id,
        codigo,
        nombre,
        descripcion,
        icono,
        ruta,
        menu_padre_id,
        nivel,
        tipo_menu,
        orden,
        requiere_autenticacion,
        es_visible,
        es_menu_sistema,
        es_activo,
        fecha_creacion
    )
    VALUES (
        NEWID(),
        @modulo_sys_admin_id,
        @seccion_tenant_admin_id,
        NULL,
        N'SYS_ADMIN.TENANT.USERS',
        N'Gestión de Usuarios',
        N'Administración de usuarios del tenant.',
        N'Users',
        N'/admin/usuarios',
        NULL,
        1,
        N'pantalla',
        1,
        1,
        1,
        1,
        1,
        GETDATE()
    );
END;

-- Menú: Roles y Permisos (/admin/roles)
IF NOT EXISTS (
    SELECT 1
    FROM modulo_menu
    WHERE codigo = N'SYS_ADMIN.TENANT.ROLES'
      AND cliente_id IS NULL
)
BEGIN
    INSERT INTO modulo_menu (
        menu_id,
        modulo_id,
        seccion_id,
        cliente_id,
        codigo,
        nombre,
        descripcion,
        icono,
        ruta,
        menu_padre_id,
        nivel,
        tipo_menu,
        orden,
        requiere_autenticacion,
        es_visible,
        es_menu_sistema,
        es_activo,
        fecha_creacion
    )
    VALUES (
        NEWID(),
        @modulo_sys_admin_id,
        @seccion_tenant_admin_id,
        NULL,
        N'SYS_ADMIN.TENANT.ROLES',
        N'Roles y Permisos',
        N'Administración de roles y permisos del tenant.',
        N'ShieldCheck',
        N'/admin/roles',
        NULL,
        1,
        N'pantalla',
        2,
        1,
        1,
        1,
        1,
        GETDATE()
    );
END;

-- Menú: Sesiones Activas (/admin/sesiones)
IF NOT EXISTS (
    SELECT 1
    FROM modulo_menu
    WHERE codigo = N'SYS_ADMIN.TENANT.SESSIONS'
      AND cliente_id IS NULL
)
BEGIN
    INSERT INTO modulo_menu (
        menu_id,
        modulo_id,
        seccion_id,
        cliente_id,
        codigo,
        nombre,
        descripcion,
        icono,
        ruta,
        menu_padre_id,
        nivel,
        tipo_menu,
        orden,
        requiere_autenticacion,
        es_visible,
        es_menu_sistema,
        es_activo,
        fecha_creacion
    )
    VALUES (
        NEWID(),
        @modulo_sys_admin_id,
        @seccion_tenant_admin_id,
        NULL,
        N'SYS_ADMIN.TENANT.SESSIONS',
        N'Sesiones Activas',
        N'Monitoreo de sesiones activas de usuarios del tenant.',
        N'LogOut',
        N'/admin/sesiones',
        NULL,
        1,
        N'pantalla',
        3,
        1,
        1,
        1,
        1,
        GETDATE()
    );
END;
GO

---------------------------------------------------------------------------
-- 4. Crear menús de Administración Global (superAdminMenu.ts)
---------------------------------------------------------------------------

DECLARE @modulo_sys_admin_id UNIQUEIDENTIFIER;
DECLARE @seccion_super_admin_id UNIQUEIDENTIFIER;

SELECT @modulo_sys_admin_id = modulo_id
FROM modulo
WHERE codigo = 'SYS_ADMIN';

SELECT @seccion_super_admin_id = seccion_id
FROM modulo_seccion
WHERE modulo_id = @modulo_sys_admin_id
  AND codigo = 'SUPER_ADMIN';

-- Menú: Dashboard (/super-admin/dashboard)
IF NOT EXISTS (
    SELECT 1
    FROM modulo_menu
    WHERE codigo = N'SYS_ADMIN.PLATFORM.DASHBOARD'
      AND cliente_id IS NULL
)
BEGIN
    INSERT INTO modulo_menu (
        menu_id,
        modulo_id,
        seccion_id,
        cliente_id,
        codigo,
        nombre,
        descripcion,
        icono,
        ruta,
        menu_padre_id,
        nivel,
        tipo_menu,
        orden,
        requiere_autenticacion,
        es_visible,
        es_menu_sistema,
        es_activo,
        fecha_creacion
    )
    VALUES (
        NEWID(),
        @modulo_sys_admin_id,
        @seccion_super_admin_id,
        NULL,
        N'SYS_ADMIN.PLATFORM.DASHBOARD',
        N'Dashboard',
        N'Panel de control del Super Admin.',
        N'LayoutDashboard',
        N'/super-admin/dashboard',
        NULL,
        1,
        N'pantalla',
        1,
        1,
        1,
        1,
        1,
        GETDATE()
    );
END;

-- Menú: Gestión de Clientes (/super-admin/clientes)
IF NOT EXISTS (
    SELECT 1
    FROM modulo_menu
    WHERE codigo = N'SYS_ADMIN.PLATFORM.CLIENTS'
      AND cliente_id IS NULL
)
BEGIN
    INSERT INTO modulo_menu (
        menu_id,
        modulo_id,
        seccion_id,
        cliente_id,
        codigo,
        nombre,
        descripcion,
        icono,
        ruta,
        menu_padre_id,
        nivel,
        tipo_menu,
        orden,
        requiere_autenticacion,
        es_visible,
        es_menu_sistema,
        es_activo,
        fecha_creacion
    )
    VALUES (
        NEWID(),
        @modulo_sys_admin_id,
        @seccion_super_admin_id,
        NULL,
        N'SYS_ADMIN.PLATFORM.CLIENTS',
        N'Gestión de Clientes',
        N'Administración de clientes multi-tenant.',
        N'Building2',
        N'/super-admin/clientes',
        NULL,
        1,
        N'pantalla',
        2,
        1,
        1,
        1,
        1,
        GETDATE()
    );
END;

-- Menú: Módulos del Sistema (/super-admin/modulos)
IF NOT EXISTS (
    SELECT 1
    FROM modulo_menu
    WHERE codigo = N'SYS_ADMIN.PLATFORM.MODULES'
      AND cliente_id IS NULL
)
BEGIN
    INSERT INTO modulo_menu (
        menu_id,
        modulo_id,
        seccion_id,
        cliente_id,
        codigo,
        nombre,
        descripcion,
        icono,
        ruta,
        menu_padre_id,
        nivel,
        tipo_menu,
        orden,
        requiere_autenticacion,
        es_visible,
        es_menu_sistema,
        es_activo,
        fecha_creacion
    )
    VALUES (
        NEWID(),
        @modulo_sys_admin_id,
        @seccion_super_admin_id,
        NULL,
        N'SYS_ADMIN.PLATFORM.MODULES',
        N'Módulos del Sistema',
        N'Gestión de módulos y plantillas de roles.',
        N'Package',
        N'/super-admin/modulos',
        NULL,
        1,
        N'pantalla',
        3,
        1,
        1,
        1,
        1,
        GETDATE()
    );
END;

-- Menú: Auditoría Global (/super-admin/auditoria)
IF NOT EXISTS (
    SELECT 1
    FROM modulo_menu
    WHERE codigo = N'SYS_ADMIN.PLATFORM.AUDIT'
      AND cliente_id IS NULL
)
BEGIN
    INSERT INTO modulo_menu (
        menu_id,
        modulo_id,
        seccion_id,
        cliente_id,
        codigo,
        nombre,
        descripcion,
        icono,
        ruta,
        menu_padre_id,
        nivel,
        tipo_menu,
        orden,
        requiere_autenticacion,
        es_visible,
        es_menu_sistema,
        es_activo,
        fecha_creacion
    )
    VALUES (
        NEWID(),
        @modulo_sys_admin_id,
        @seccion_super_admin_id,
        NULL,
        N'SYS_ADMIN.PLATFORM.AUDIT',
        N'Auditoría Global',
        N'Log y auditoría de eventos de plataforma.',
        N'ClipboardList',
        N'/super-admin/auditoria',
        NULL,
        1,
        N'pantalla',
        5,  -- se respeta orden legado (salto intencional)
        1,
        1,
        1,
        1,
        GETDATE()
    );
END;
GO

---------------------------------------------------------------------------
-- 4B. Crear menús de Catálogos Globales (Super Admin)
---------------------------------------------------------------------------

DECLARE @modulo_sys_admin_id UNIQUEIDENTIFIER;
DECLARE @seccion_catalogos_globales_id UNIQUEIDENTIFIER;

SELECT @modulo_sys_admin_id = modulo_id
FROM modulo
WHERE codigo = 'SYS_ADMIN';

SELECT @seccion_catalogos_globales_id = seccion_id
FROM modulo_seccion
WHERE modulo_id = @modulo_sys_admin_id
  AND codigo = 'GLOBAL_CATALOGS';

-- Menú: Países (/super-admin/catalogos/paises)
IF NOT EXISTS (
    SELECT 1
    FROM modulo_menu
    WHERE codigo = N'SYS_ADMIN.CATALOGOS.PAISES'
      AND cliente_id IS NULL
)
BEGIN
    INSERT INTO modulo_menu (
        menu_id,
        modulo_id,
        seccion_id,
        cliente_id,
        codigo,
        nombre,
        descripcion,
        icono,
        ruta,
        menu_padre_id,
        nivel,
        tipo_menu,
        orden,
        requiere_autenticacion,
        es_visible,
        es_menu_sistema,
        es_activo,
        fecha_creacion
    )
    VALUES (
        NEWID(),
        @modulo_sys_admin_id,
        @seccion_catalogos_globales_id,
        NULL,
        N'SYS_ADMIN.CATALOGOS.PAISES',
        N'Países',
        N'Administración del catálogo global de países.',
        N'Flag',
        N'/super-admin/catalogos/paises',
        NULL,
        1,
        N'pantalla',
        1,
        1,
        1,
        1,
        1,
        GETDATE()
    );
END;

-- Menú: Departamentos (/super-admin/catalogos/departamentos)
IF NOT EXISTS (
    SELECT 1
    FROM modulo_menu
    WHERE codigo = N'SYS_ADMIN.CATALOGOS.DEPARTAMENTOS'
      AND cliente_id IS NULL
)
BEGIN
    INSERT INTO modulo_menu (
        menu_id,
        modulo_id,
        seccion_id,
        cliente_id,
        codigo,
        nombre,
        descripcion,
        icono,
        ruta,
        menu_padre_id,
        nivel,
        tipo_menu,
        orden,
        requiere_autenticacion,
        es_visible,
        es_menu_sistema,
        es_activo,
        fecha_creacion
    )
    VALUES (
        NEWID(),
        @modulo_sys_admin_id,
        @seccion_catalogos_globales_id,
        NULL,
        N'SYS_ADMIN.CATALOGOS.DEPARTAMENTOS',
        N'Departamentos',
        N'Administración del catálogo global de departamentos.',
        N'Map',
        N'/super-admin/catalogos/departamentos',
        NULL,
        1,
        N'pantalla',
        2,
        1,
        1,
        1,
        1,
        GETDATE()
    );
END;

-- Menú: Provincias (/super-admin/catalogos/provincias)
IF NOT EXISTS (
    SELECT 1
    FROM modulo_menu
    WHERE codigo = N'SYS_ADMIN.CATALOGOS.PROVINCIAS'
      AND cliente_id IS NULL
)
BEGIN
    INSERT INTO modulo_menu (
        menu_id,
        modulo_id,
        seccion_id,
        cliente_id,
        codigo,
        nombre,
        descripcion,
        icono,
        ruta,
        menu_padre_id,
        nivel,
        tipo_menu,
        orden,
        requiere_autenticacion,
        es_visible,
        es_menu_sistema,
        es_activo,
        fecha_creacion
    )
    VALUES (
        NEWID(),
        @modulo_sys_admin_id,
        @seccion_catalogos_globales_id,
        NULL,
        N'SYS_ADMIN.CATALOGOS.PROVINCIAS',
        N'Provincias',
        N'Administración del catálogo global de provincias.',
        N'MapPinned',
        N'/super-admin/catalogos/provincias',
        NULL,
        1,
        N'pantalla',
        3,
        1,
        1,
        1,
        1,
        GETDATE()
    );
END;

-- Menú: Distritos (/super-admin/catalogos/distritos)
IF NOT EXISTS (
    SELECT 1
    FROM modulo_menu
    WHERE codigo = N'SYS_ADMIN.CATALOGOS.DISTRITOS'
      AND cliente_id IS NULL
)
BEGIN
    INSERT INTO modulo_menu (
        menu_id,
        modulo_id,
        seccion_id,
        cliente_id,
        codigo,
        nombre,
        descripcion,
        icono,
        ruta,
        menu_padre_id,
        nivel,
        tipo_menu,
        orden,
        requiere_autenticacion,
        es_visible,
        es_menu_sistema,
        es_activo,
        fecha_creacion
    )
    VALUES (
        NEWID(),
        @modulo_sys_admin_id,
        @seccion_catalogos_globales_id,
        NULL,
        N'SYS_ADMIN.CATALOGOS.DISTRITOS',
        N'Distritos',
        N'Administración del catálogo global de distritos.',
        N'LocateFixed',
        N'/super-admin/catalogos/distritos',
        NULL,
        1,
        N'pantalla',
        4,
        1,
        1,
        1,
        1,
        GETDATE()
    );
END;
-- Menú: Monedas (/super-admin/catalogos/monedas)
IF NOT EXISTS (
    SELECT 1
    FROM modulo_menu
    WHERE codigo = N'SYS_ADMIN.CATALOGOS.MONEDAS'
      AND cliente_id IS NULL
)
BEGIN
    INSERT INTO modulo_menu (
        menu_id,
        modulo_id,
        seccion_id,
        cliente_id,
        codigo,
        nombre,
        descripcion,
        icono,
        ruta,
        menu_padre_id,
        nivel,
        tipo_menu,
        orden,
        requiere_autenticacion,
        es_visible,
        es_menu_sistema,
        es_activo,
        fecha_creacion
    )
    VALUES (
        NEWID(),
        @modulo_sys_admin_id,
        @seccion_catalogos_globales_id,
        NULL,
        N'SYS_ADMIN.CATALOGOS.MONEDAS',
        N'Monedas',
        N'Administración del catálogo global de monedas.',
        N'LocateFixed',
        N'/super-admin/catalogos/monedas',
        NULL,
        1,
        N'pantalla',
        5,
        1,
        1,
        1,
        1,
        GETDATE()
    );
END;
GO

---------------------------------------------------------------------------
-- 5. Crear permisos globales (permiso) para acceso a administración
---------------------------------------------------------------------------

DECLARE @modulo_sys_admin_id UNIQUEIDENTIFIER;
DECLARE @permiso_admin_tenant_id UNIQUEIDENTIFIER;
DECLARE @permiso_admin_platform_id UNIQUEIDENTIFIER;

SELECT @modulo_sys_admin_id = modulo_id
FROM modulo
WHERE codigo = 'SYS_ADMIN';

-- Permiso: admin.tenant.access
SELECT @permiso_admin_tenant_id = permiso_id
FROM permiso
WHERE codigo = N'admin.tenant.access';

IF @permiso_admin_tenant_id IS NULL
BEGIN
    SET @permiso_admin_tenant_id = NEWID();

    INSERT INTO permiso (
        permiso_id,
        codigo,
        nombre,
        descripcion,
        modulo_id,
        recurso,
        accion,
        es_activo,
        fecha_creacion
    )
    VALUES (
        @permiso_admin_tenant_id,
        N'admin.tenant.access',
        N'Acceso a Administración de Tenant',
        N'Permite acceder a las pantallas de administración del tenant (/admin/*).',
        @modulo_sys_admin_id,
        N'admin.tenant',
        N'acceder',
        1,
        GETDATE()
    );
END;

-- Permiso: admin.platform.access
SELECT @permiso_admin_platform_id = permiso_id
FROM permiso
WHERE codigo = N'admin.platform.access';

IF @permiso_admin_platform_id IS NULL
BEGIN
    SET @permiso_admin_platform_id = NEWID();

    INSERT INTO permiso (
        permiso_id,
        codigo,
        nombre,
        descripcion,
        modulo_id,
        recurso,
        accion,
        es_activo,
        fecha_creacion
    )
    VALUES (
        @permiso_admin_platform_id,
        N'admin.platform.access',
        N'Acceso a Administración de Plataforma',
        N'Permite acceder a las pantallas de administración global (/super-admin/*).',
        @modulo_sys_admin_id,
        N'admin.platform',
        N'acceder',
        1,
        GETDATE()
    );
END;
GO

---------------------------------------------------------------------------
-- 6. Asignar permisos a roles (ADMIN_TENANT / ADMIN_PLATFORM) vía rol_permiso
--    - ADMIN_TENANT  → código_rol = 'ADMIN_TENANT'
--    - ADMIN_PLATFORM → código_rol = 'ADMIN_PLATFORM'
--    Usa cliente_id del propio rol (solo si cliente_id NOT NULL)
---------------------------------------------------------------------------

DECLARE @permiso_admin_tenant_id UNIQUEIDENTIFIER;
DECLARE @permiso_admin_platform_id UNIQUEIDENTIFIER;

SELECT @permiso_admin_tenant_id = permiso_id
FROM permiso
WHERE codigo = N'admin.tenant.access';

SELECT @permiso_admin_platform_id = permiso_id
FROM permiso
WHERE codigo = N'admin.platform.access';

-- Asignar admin.tenant.access a roles con codigo_rol = 'ADMIN_TENANT'
INSERT INTO rol_permiso (
    rol_permiso_id,
    cliente_id,
    rol_id,
    permiso_id,
    fecha_creacion
)
SELECT
    NEWID(),
    r.cliente_id,
    r.rol_id,
    @permiso_admin_tenant_id,
    GETDATE()
FROM rol r
WHERE r.codigo_rol = N'ADMIN_TENANT'
  AND r.cliente_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM rol_permiso rp
      WHERE rp.rol_id = r.rol_id
        AND rp.permiso_id = @permiso_admin_tenant_id
        AND rp.cliente_id = r.cliente_id
  );

-- Asignar admin.platform.access a roles con codigo_rol = 'ADMIN_PLATFORM'
INSERT INTO rol_permiso (
    rol_permiso_id,
    cliente_id,
    rol_id,
    permiso_id,
    fecha_creacion
)
SELECT
    NEWID(),
    r.cliente_id,
    r.rol_id,
    @permiso_admin_platform_id,
    GETDATE()
FROM rol r
WHERE r.codigo_rol = N'ADMIN_PLATFORM'
  AND r.cliente_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM rol_permiso rp
      WHERE rp.rol_id = r.rol_id
        AND rp.permiso_id = @permiso_admin_platform_id
        AND rp.cliente_id = r.cliente_id
  );
GO

PRINT 'Migración de menús SYS_ADMIN y permisos admin.* completada correctamente.';