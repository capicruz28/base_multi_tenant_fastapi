-- ============================================================================
-- SCRIPT: SEED DATA PARA BD CENTRAL
-- DESCRIPCIÓN: Datos iniciales para poblar la BD central
-- USO: Ejecutar DESPUÉS de crear las tablas (TABLAS_BD_CENTRAL.sql)
-- NOTA: Usa UUIDs fijos para mantener coherencia entre scripts
-- ============================================================================

USE bd_hybrid_sistema_central;
GO

-- ============================================================================
-- SECCIÓN 1: CLIENTES
-- ============================================================================

-- Cliente SUPERADMIN (plataforma)
INSERT INTO cliente (
    cliente_id,
    codigo_cliente,
    subdominio,
    razon_social,
    nombre_comercial,
    tipo_instalacion,
    modo_autenticacion,
    plan_suscripcion,
    estado_suscripcion,
    contacto_email,
    es_activo,
    es_demo
) VALUES (
    '00000000-0000-0000-0000-000000000001',  -- UUID fijo para superadmin
    'SUPERADMIN',
    'platform',
    'Sistema ERP Multi-Tenant',
    'Plataforma Admin',
    'shared',
    'local',
    'enterprise',
    'activo',
    'admin@plataforma.local',
    1,
    0
);

-- Cliente 1: Centralizado (shared)
INSERT INTO cliente (
    cliente_id,
    codigo_cliente,
    subdominio,
    razon_social,
    nombre_comercial,
    ruc,
    tipo_instalacion,
    modo_autenticacion,
    plan_suscripcion,
    estado_suscripcion,
    contacto_email,
    contacto_nombre,
    contacto_telefono,
    es_activo,
    es_demo
) VALUES (
    '11111111-1111-1111-1111-111111111111',  -- UUID fijo
    'CLI001',
    'acme',
    'ACME Corporation S.A.C.',
    'ACME',
    '20123456789',
    'shared',
    'local',
    'profesional',
    'activo',
    'admin@acme.com',
    'Juan Pérez',
    '987654321',
    1,
    0
);

-- Cliente 2: Centralizado (shared)
INSERT INTO cliente (
    cliente_id,
    codigo_cliente,
    subdominio,
    razon_social,
    nombre_comercial,
    ruc,
    tipo_instalacion,
    modo_autenticacion,
    plan_suscripcion,
    estado_suscripcion,
    contacto_email,
    contacto_nombre,
    contacto_telefono,
    es_activo,
    es_demo
) VALUES (
    '22222222-2222-2222-2222-222222222222',  -- UUID fijo
    'CLI002',
    'innova',
    'Innova Solutions S.A.',
    'Innova',
    '20234567890',
    'shared',
    'local',
    'basico',
    'activo',
    'admin@innova.com',
    'María González',
    '987654322',
    1,
    0
);

-- Cliente 3: Dedicado (dedicated)
INSERT INTO cliente (
    cliente_id,
    codigo_cliente,
    subdominio,
    razon_social,
    nombre_comercial,
    ruc,
    tipo_instalacion,
    modo_autenticacion,
    plan_suscripcion,
    estado_suscripcion,
    contacto_email,
    contacto_nombre,
    contacto_telefono,
    es_activo,
    es_demo
) VALUES (
    '33333333-3333-3333-3333-333333333333',  -- UUID fijo
    'CLI003',
    'techcorp',
    'TechCorp Industries S.A.',
    'TechCorp',
    '20345678901',
    'dedicated',
    'local',
    'enterprise',
    'activo',
    'admin@techcorp.com',
    'Carlos Rodríguez',
    '987654323',
    1,
    0
);

-- Cliente 4: Dedicado (dedicated)
INSERT INTO cliente (
    cliente_id,
    codigo_cliente,
    subdominio,
    razon_social,
    nombre_comercial,
    ruc,
    tipo_instalacion,
    modo_autenticacion,
    plan_suscripcion,
    estado_suscripcion,
    contacto_email,
    contacto_nombre,
    contacto_telefono,
    es_activo,
    es_demo
) VALUES (
    '44444444-4444-4444-4444-444444444444',  -- UUID fijo
    'CLI004',
    'global',
    'Global Logistics S.A.',
    'GlobalLog',
    '20456789012',
    'dedicated',
    'local',
    'enterprise',
    'activo',
    'admin@globallog.com',
    'Ana Martínez',
    '987654324',
    1,
    0
);

-- ============================================================================
-- SECCIÓN 2: MÓDULOS ERP
-- ============================================================================

-- Módulo: ALMACEN
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
    orden,
    es_activo
) VALUES (
    'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA',  -- UUID fijo
    'ALMACEN',
    'Control de Almacén',
    'Gestión completa de inventario, productos, movimientos y stock',
    'warehouse',
    '#4CAF50',
    'operaciones',
    0,
    1,
    500.00,
    1,
    1
);

-- Módulo: LOGISTICA
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
    es_activo
) VALUES (
    'BBBBBBBB-BBBB-BBBB-BBBB-BBBBBBBBBBBB',  -- UUID fijo
    'LOGISTICA',
    'Gestión Logística',
    'Rutas, vehículos, conductores y distribución',
    'local_shipping',
    '#2196F3',
    'operaciones',
    0,
    1,
    800.00,
    '["ALMACEN"]',  -- Requiere ALMACEN activo
    2,
    1
);

-- Módulo: PLANILLAS
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
    orden,
    es_activo
) VALUES (
    'CCCCCCCC-CCCC-CCCC-CCCC-CCCCCCCCCCCC',  -- UUID fijo
    'PLANILLAS',
    'Gestión de Planillas',
    'Cálculo de planillas, remuneraciones, descuentos y beneficios',
    'payments',
    '#FF9800',
    'rrhh',
    0,
    1,
    1200.00,
    3,
    1
);

-- ============================================================================
-- SECCIÓN 3: SECCIONES DE MÓDULOS
-- ============================================================================

-- Secciones para ALMACEN
INSERT INTO modulo_seccion (
    seccion_id,
    modulo_id,
    codigo,
    nombre,
    descripcion,
    icono,
    orden,
    es_seccion_sistema,
    es_activo
) VALUES
-- Sección: Productos
(
    'A1A1A1A1-A1A1-A1A1-A1A1-A1A1A1A1A1A1',
    'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA',  -- ALMACEN
    'PRODUCTOS',
    'Productos',
    'Catálogo de productos e inventario',
    'inventory_2',
    1,
    1,
    1
),
-- Sección: Movimientos
(
    'A2A2A2A2-A2A2-A2A2-A2A2-A2A2A2A2A2A2',
    'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA',  -- ALMACEN
    'MOVIMIENTOS',
    'Movimientos de Inventario',
    'Registro de entradas y salidas de inventario',
    'swap_horiz',
    2,
    1,
    1
),
-- Sección: Reportes
(
    'A3A3A3A3-A3A3-A3A3-A3A3-A3A3A3A3A3A3',
    'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA',  -- ALMACEN
    'REPORTES',
    'Reportes de Almacén',
    'Reportes y consultas de inventario',
    'assessment',
    3,
    1,
    1
);

-- Secciones para LOGISTICA
INSERT INTO modulo_seccion (
    seccion_id,
    modulo_id,
    codigo,
    nombre,
    descripcion,
    icono,
    orden,
    es_seccion_sistema,
    es_activo
) VALUES
-- Sección: Rutas
(
    'B1B1B1B1-B1B1-B1B1-B1B1-B1B1B1B1B1B1',
    'BBBBBBBB-BBBB-BBBB-BBBB-BBBBBBBBBBBB',  -- LOGISTICA
    'RUTAS',
    'Rutas de Distribución',
    'Gestión de rutas y recorridos de distribución',
    'route',
    1,
    1,
    1
),
-- Sección: Vehículos
(
    'B2B2B2B2-B2B2-B2B2-B2B2-B2B2B2B2B2B2',
    'BBBBBBBB-BBBB-BBBB-BBBB-BBBBBBBBBBBB',  -- LOGISTICA
    'VEHICULOS',
    'Vehículos',
    'Flota de vehículos',
    'directions_car',
    2,
    1,
    1
),
-- Sección: Conductores
(
    'B3B3B3B3-B3B3-B3B3-B3B3-B3B3B3B3B3B3',
    'BBBBBBBB-BBBB-BBBB-BBBB-BBBBBBBBBBBB',  -- LOGISTICA
    'CONDUCTORES',
    'Conductores',
    'Gestión de conductores',
    'person',
    3,
    1,
    1
);

-- Secciones para PLANILLAS
INSERT INTO modulo_seccion (
    seccion_id,
    modulo_id,
    codigo,
    nombre,
    descripcion,
    icono,
    orden,
    es_seccion_sistema,
    es_activo
) VALUES
-- Sección: Empleados
(
    'C1C1C1C1-C1C1-C1C1-C1C1-C1C1C1C1C1C1',
    'CCCCCCCC-CCCC-CCCC-CCCC-CCCCCCCCCCCC',  -- PLANILLAS
    'EMPLEADOS',
    'Empleados',
    'Gestión de empleados',
    'people',
    1,
    1,
    1
),
-- Sección: Planillas
(
    'C2C2C2C2-C2C2-C2C2-C2C2-C2C2C2C2C2C2',
    'CCCCCCCC-CCCC-CCCC-CCCC-CCCCCCCCCCCC',  -- PLANILLAS
    'PLANILLAS',
    'Planillas',
    'Cálculo y procesamiento de planillas',
    'receipt',
    2,
    1,
    1
),
-- Sección: Reportes
(
    'C3C3C3C3-C3C3-C3C3-C3C3-C3C3C3C3C3C3',
    'CCCCCCCC-CCCC-CCCC-CCCC-CCCCCCCCCCCC',  -- PLANILLAS
    'REPORTES',
    'Reportes de Planillas',
    'Reportes y consultas',
    'assessment',
    3,
    1,
    1
);

-- ============================================================================
-- SECCIÓN 4: MENÚS DE MÓDULOS
-- ============================================================================

-- Menús para ALMACEN - Sección PRODUCTOS
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
    es_menu_sistema,
    es_activo
) VALUES
-- Listar Productos
(
    'AA11AA11-AA11-AA11-AA11-AA11AA11AA11',
    'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA',  -- ALMACEN
    'A1A1A1A1-A1A1-A1A1-A1A1-A1A1A1A1A1A1',  -- PRODUCTOS
    NULL,  -- Menú global
    'ALMACEN_PRODUCTOS_LISTAR',
    'Listar Productos',
    'Ver catálogo de productos',
    'list',
    '/almacen/productos',
    NULL,
    1,
    'pantalla',
    1,
    1,
    1
),
-- Crear Producto
(
    'AA12AA12-AA12-AA12-AA12-AA12AA12AA12',
    'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA',  -- ALMACEN
    'A1A1A1A1-A1A1-A1A1-A1A1-A1A1A1A1A1A1',  -- PRODUCTOS
    NULL,
    'ALMACEN_PRODUCTOS_CREAR',
    'Nuevo Producto',
    'Crear nuevo producto',
    'add',
    '/almacen/productos/nuevo',
    NULL,
    1,
    'pantalla',
    2,
    1,
    1
),
-- Categorías
(
    'AA13AA13-AA13-AA13-AA13-AA13AA13AA13',
    'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA',  -- ALMACEN
    'A1A1A1A1-A1A1-A1A1-A1A1-A1A1A1A1A1A1',  -- PRODUCTOS
    NULL,
    'ALMACEN_PRODUCTOS_CATEGORIAS',
    'Categorías',
    'Gestión de categorías',
    'category',
    '/almacen/productos/categorias',
    NULL,
    1,
    'pantalla',
    3,
    1,
    1
);

-- Menús para ALMACEN - Sección MOVIMIENTOS
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
    es_menu_sistema,
    es_activo
) VALUES
-- Listar Movimientos
(
    'AA21AA21-AA21-AA21-AA21-AA21AA21AA21',
    'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA',  -- ALMACEN
    'A2A2A2A2-A2A2-A2A2-A2A2-A2A2A2A2A2A2',  -- MOVIMIENTOS
    NULL,
    'ALMACEN_MOVIMIENTOS_LISTAR',
    'Movimientos',
    'Ver movimientos de inventario',
    'swap_horiz',
    '/almacen/movimientos',
    NULL,
    1,
    'pantalla',
    1,
    1,
    1
),
-- Entrada de Mercancía
(
    'AA22AA22-AA22-AA22-AA22-AA22AA22AA22',
    'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA',  -- ALMACEN
    'A2A2A2A2-A2A2-A2A2-A2A2-A2A2A2A2A2A2',  -- MOVIMIENTOS
    NULL,
    'ALMACEN_MOVIMIENTOS_ENTRADA',
    'Entrada',
    'Registrar entrada de mercancía',
    'input',
    '/almacen/movimientos/entrada',
    NULL,
    1,
    'pantalla',
    2,
    1,
    1
),
-- Salida de Mercancía
(
    'AA23AA23-AA23-AA23-AA23-AA23AA23AA23',
    'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA',  -- ALMACEN
    'A2A2A2A2-A2A2-A2A2-A2A2-A2A2A2A2A2A2',  -- MOVIMIENTOS
    NULL,
    'ALMACEN_MOVIMIENTOS_SALIDA',
    'Salida',
    'Registrar salida de mercancía',
    'output',
    '/almacen/movimientos/salida',
    NULL,
    1,
    'pantalla',
    3,
    1,
    1
);

-- Menús para LOGISTICA - Sección RUTAS
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
    es_menu_sistema,
    es_activo
) VALUES
-- Listar Rutas
(
    'BB11BB11-BB11-BB11-BB11-BB11BB11BB11',
    'BBBBBBBB-BBBB-BBBB-BBBB-BBBBBBBBBBBB',  -- LOGISTICA
    'B1B1B1B1-B1B1-B1B1-B1B1-B1B1B1B1B1B1',  -- RUTAS
    NULL,
    'LOGISTICA_RUTAS_LISTAR',
    'Rutas',
    'Ver rutas de distribución',
    'route',
    '/logistica/rutas',
    NULL,
    1,
    'pantalla',
    1,
    1,
    1
),
-- Nueva Ruta
(
    'BB12BB12-BB12-BB12-BB12-BB12BB12BB12',
    'BBBBBBBB-BBBB-BBBB-BBBB-BBBBBBBBBBBB',  -- LOGISTICA
    'B1B1B1B1-B1B1-B1B1-B1B1-B1B1B1B1B1B1',  -- RUTAS
    NULL,
    'LOGISTICA_RUTAS_CREAR',
    'Nueva Ruta',
    'Crear nueva ruta',
    'add',
    '/logistica/rutas/nueva',
    NULL,
    1,
    'pantalla',
    2,
    1,
    1
);

-- Menús para LOGISTICA - Sección VEHICULOS
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
    es_menu_sistema,
    es_activo
) VALUES
-- Listar Vehículos
(
    'BB21BB21-BB21-BB21-BB21-BB21BB21BB21',
    'BBBBBBBB-BBBB-BBBB-BBBB-BBBBBBBBBBBB',  -- LOGISTICA
    'B2B2B2B2-B2B2-B2B2-B2B2-B2B2B2B2B2B2',  -- VEHICULOS
    NULL,
    'LOGISTICA_VEHICULOS_LISTAR',
    'Vehículos',
    'Ver flota de vehículos',
    'directions_car',
    '/logistica/vehiculos',
    NULL,
    1,
    'pantalla',
    1,
    1,
    1
),
-- Nuevo Vehículo
(
    'BB22BB22-BB22-BB22-BB22-BB22BB22BB22',
    'BBBBBBBB-BBBB-BBBB-BBBB-BBBBBBBBBBBB',  -- LOGISTICA
    'B2B2B2B2-B2B2-B2B2-B2B2-B2B2B2B2B2B2',  -- VEHICULOS
    NULL,
    'LOGISTICA_VEHICULOS_CREAR',
    'Nuevo Vehículo',
    'Registrar nuevo vehículo',
    'add',
    '/logistica/vehiculos/nuevo',
    NULL,
    1,
    'pantalla',
    2,
    1,
    1
);

-- Menús para PLANILLAS - Sección EMPLEADOS
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
    es_menu_sistema,
    es_activo
) VALUES
-- Listar Empleados
(
    'CC11CC11-CC11-CC11-CC11-CC11CC11CC11',
    'CCCCCCCC-CCCC-CCCC-CCCC-CCCCCCCCCCCC',  -- PLANILLAS
    'C1C1C1C1-C1C1-C1C1-C1C1-C1C1C1C1C1C1',  -- EMPLEADOS
    NULL,
    'PLANILLAS_EMPLEADOS_LISTAR',
    'Empleados',
    'Ver lista de empleados',
    'people',
    '/planillas/empleados',
    NULL,
    1,
    'pantalla',
    1,
    1,
    1
),
-- Nuevo Empleado
(
    'CC12CC12-CC12-CC12-CC12-CC12CC12CC12',
    'CCCCCCCC-CCCC-CCCC-CCCC-CCCCCCCCCCCC',  -- PLANILLAS
    'C1C1C1C1-C1C1-C1C1-C1C1-C1C1C1C1C1C1',  -- EMPLEADOS
    NULL,
    'PLANILLAS_EMPLEADOS_CREAR',
    'Nuevo Empleado',
    'Registrar nuevo empleado',
    'person_add',
    '/planillas/empleados/nuevo',
    NULL,
    1,
    'pantalla',
    2,
    1,
    1
);

-- Menús para PLANILLAS - Sección PLANILLAS
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
    es_menu_sistema,
    es_activo
) VALUES
-- Listar Planillas
(
    'CC21CC21-CC21-CC21-CC21-CC21CC21CC21',
    'CCCCCCCC-CCCC-CCCC-CCCC-CCCCCCCCCCCC',  -- PLANILLAS
    'C2C2C2C2-C2C2-C2C2-C2C2-C2C2C2C2C2C2',  -- PLANILLAS
    NULL,
    'PLANILLAS_PLANILLAS_LISTAR',
    'Planillas',
    'Ver planillas procesadas',
    'receipt',
    '/planillas/planillas',
    NULL,
    1,
    'pantalla',
    1,
    1,
    1
),
-- Procesar Planilla
(
    'CC22CC22-CC22-CC22-CC22-CC22CC22CC22',
    'CCCCCCCC-CCCC-CCCC-CCCC-CCCCCCCCCCCC',  -- PLANILLAS
    'C2C2C2C2-C2C2-C2C2-C2C2-C2C2C2C2C2C2',  -- PLANILLAS
    NULL,
    'PLANILLAS_PLANILLAS_PROCESAR',
    'Procesar Planilla',
    'Calcular y procesar planilla',
    'calculate',
    '/planillas/planillas/procesar',
    NULL,
    1,
    'pantalla',
    2,
    1,
    1
);

-- ============================================================================
-- SECCIÓN 5: ACTIVACIÓN DE MÓDULOS POR CLIENTE
-- ============================================================================

-- Activar módulos para SUPERADMIN (todos)
INSERT INTO cliente_modulo (
    cliente_modulo_id,
    cliente_id,
    modulo_id,
    esta_activo,
    fecha_activacion
) VALUES
(
    NEWID(),
    '00000000-0000-0000-0000-000000000001',  -- SUPERADMIN
    'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA',  -- ALMACEN
    1,
    GETDATE()
),
(
    NEWID(),
    '00000000-0000-0000-0000-000000000001',  -- SUPERADMIN
    'BBBBBBBB-BBBB-BBBB-BBBB-BBBBBBBBBBBB',  -- LOGISTICA
    1,
    GETDATE()
),
(
    NEWID(),
    '00000000-0000-0000-0000-000000000001',  -- SUPERADMIN
    'CCCCCCCC-CCCC-CCCC-CCCC-CCCCCCCCCCCC',  -- PLANILLAS
    1,
    GETDATE()
);

-- Activar módulos para ACME (shared) - todos
INSERT INTO cliente_modulo (
    cliente_modulo_id,
    cliente_id,
    modulo_id,
    esta_activo,
    fecha_activacion
) VALUES
(
    NEWID(),
    '11111111-1111-1111-1111-111111111111',  -- ACME
    'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA',  -- ALMACEN
    1,
    GETDATE()
),
(
    NEWID(),
    '11111111-1111-1111-1111-111111111111',  -- ACME
    'BBBBBBBB-BBBB-BBBB-BBBB-BBBBBBBBBBBB',  -- LOGISTICA
    1,
    GETDATE()
),
(
    NEWID(),
    '11111111-1111-1111-1111-111111111111',  -- ACME
    'CCCCCCCC-CCCC-CCCC-CCCC-CCCCCCCCCCCC',  -- PLANILLAS
    1,
    GETDATE()
);

-- Activar módulos para INNOVA (shared) - solo ALMACEN y PLANILLAS
INSERT INTO cliente_modulo (
    cliente_modulo_id,
    cliente_id,
    modulo_id,
    esta_activo,
    fecha_activacion
) VALUES
(
    NEWID(),
    '22222222-2222-2222-2222-222222222222',  -- INNOVA
    'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA',  -- ALMACEN
    1,
    GETDATE()
),
(
    NEWID(),
    '22222222-2222-2222-2222-222222222222',  -- INNOVA
    'CCCCCCCC-CCCC-CCCC-CCCC-CCCCCCCCCCCC',  -- PLANILLAS
    1,
    GETDATE()
);

-- Activar módulos para TECHCORP (dedicated) - todos
INSERT INTO cliente_modulo (
    cliente_modulo_id,
    cliente_id,
    modulo_id,
    esta_activo,
    fecha_activacion
) VALUES
(
    NEWID(),
    '33333333-3333-3333-3333-333333333333',  -- TECHCORP
    'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA',  -- ALMACEN
    1,
    GETDATE()
),
(
    NEWID(),
    '33333333-3333-3333-3333-333333333333',  -- TECHCORP
    'BBBBBBBB-BBBB-BBBB-BBBB-BBBBBBBBBBBB',  -- LOGISTICA
    1,
    GETDATE()
),
(
    NEWID(),
    '33333333-3333-3333-3333-333333333333',  -- TECHCORP
    'CCCCCCCC-CCCC-CCCC-CCCC-CCCCCCCCCCCC',  -- PLANILLAS
    1,
    GETDATE()
);

-- Activar módulos para GLOBALLOG (dedicated) - ALMACEN y LOGISTICA
INSERT INTO cliente_modulo (
    cliente_modulo_id,
    cliente_id,
    modulo_id,
    esta_activo,
    fecha_activacion
) VALUES
(
    NEWID(),
    '44444444-4444-4444-4444-444444444444',  -- GLOBALLOG
    'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA',  -- ALMACEN
    1,
    GETDATE()
),
(
    NEWID(),
    '44444444-4444-4444-4444-444444444444',  -- GLOBALLOG
    'BBBBBBBB-BBBB-BBBB-BBBB-BBBBBBBBBBBB',  -- LOGISTICA
    1,
    GETDATE()
);

-- ============================================================================
-- SECCIÓN 6: USUARIOS Y ROLES (Para clientes con tipo_instalacion = 'shared')
-- ============================================================================

-- Usuarios y roles para SUPERADMIN (shared)
-- Nota: Estos usuarios se crean en BD central porque tipo_instalacion = 'shared'

-- Rol ADMIN para SUPERADMIN
INSERT INTO rol (
    rol_id,
    cliente_id,
    codigo_rol,
    nombre,
    descripcion,
    es_rol_sistema,
    nivel_acceso,
    es_activo
) VALUES (
    '00000000-0000-0000-0000-000000000010',  -- ADMIN (UUID válido)
    '00000000-0000-0000-0000-000000000001',  -- SUPERADMIN
    'SUPER_ADMIN',
    'Administrador',
    'Rol de administrador con acceso completo',
    1,
    5,
    1
);

-- Rol USER para SUPERADMIN
INSERT INTO rol (
    rol_id,
    cliente_id,
    codigo_rol,
    nombre,
    descripcion,
    es_rol_sistema,
    nivel_acceso,
    es_activo
) VALUES (
    '00000000-0000-0000-0000-000000000020',  -- USER (UUID válido)
    '00000000-0000-0000-0000-000000000001',  -- SUPERADMIN
    'SUPER_ADMIN',
    'Usuario',
    'Rol de usuario estándar',
    1,
    1,
    1
);

-- Usuario admin para SUPERADMIN
-- Password: admin123
INSERT INTO usuario (
    usuario_id,
    cliente_id,
    nombre_usuario,
    contrasena,
    nombre,
    apellido,
    correo,
    es_activo,
    correo_confirmado
) VALUES (
    '00000000-0000-0000-0000-000000000100',  -- admin (UUID válido)
    '00000000-0000-0000-0000-000000000001',  -- SUPERADMIN
    'superadmin',
    '$2b$12$6J/bWiSYNFHFblxoVot4Je2HyWGU.QyFxtPdpsAMP2hz4fGid5WQu',  -- admin123
    'Administrador',
    'Sistema',
    'admin@plataforma.local',
    1,
    1
);

-- Usuario user para SUPERADMIN
-- Password: user123
INSERT INTO usuario (
    usuario_id,
    cliente_id,
    nombre_usuario,
    contrasena,
    nombre,
    apellido,
    correo,
    es_activo,
    correo_confirmado
) VALUES (
    '00000000-0000-0000-0000-000000000200',  -- user (UUID válido)
    '00000000-0000-0000-0000-000000000001',  -- SUPERADMIN
    'user',
    '$2b$12$ZvpoS9E0eMe6pbxGNoho1eN8hMbeTCkAE5Fyztm1N.51jxcqVYW86',  -- user123
    'Usuario',
    'Prueba',
    'user@plataforma.local',
    1,
    1
);

-- Asignar roles a usuarios SUPERADMIN
INSERT INTO usuario_rol (
    usuario_rol_id,
    usuario_id,
    rol_id,
    cliente_id,
    es_activo
) VALUES
(
    NEWID(),
    '00000000-0000-0000-0000-000000000100',  -- admin (UUID válido)  -- admin
    '00000000-0000-0000-0000-000000000010',  -- ADMIN
    '00000000-0000-0000-0000-000000000001',  -- SUPERADMIN
    1
),
(
    NEWID(),
    '00000000-0000-0000-0000-000000000200',  -- user (UUID válido)  -- user
    '00000000-0000-0000-0000-000000000020',  -- USER
    '00000000-0000-0000-0000-000000000001',  -- SUPERADMIN
    1
);

-- Usuarios y roles para ACME (shared)
-- Rol ADMIN
INSERT INTO rol (
    rol_id,
    cliente_id,
    codigo_rol,
    nombre,
    descripcion,
    es_rol_sistema,
    nivel_acceso,
    es_activo
) VALUES (
    '11111111-1111-1111-1111-111111111110',  -- ADMIN (UUID válido)
    '11111111-1111-1111-1111-111111111111',  -- ACME
    'ADMIN',
    'Administrador',
    'Rol de administrador',
    1,
    4,
    1
);

-- Rol USER
INSERT INTO rol (
    rol_id,
    cliente_id,
    codigo_rol,
    nombre,
    descripcion,
    es_rol_sistema,
    nivel_acceso,
    es_activo
) VALUES (
    '11111111-1111-1111-1111-111111111120',  -- USER (UUID válido)
    '11111111-1111-1111-1111-111111111111',  -- ACME
    'USER',
    'Usuario',
    'Rol de usuario',
    1,
    1,
    1
);

-- Usuario admin
INSERT INTO usuario (
    usuario_id,
    cliente_id,
    nombre_usuario,
    contrasena,
    nombre,
    apellido,
    correo,
    es_activo,
    correo_confirmado
) VALUES (
    '11111111-1111-1111-1111-111111111100',  -- admin (UUID válido)
    '11111111-1111-1111-1111-111111111111',  -- ACME
    'admin',
    '$2b$12$6J/bWiSYNFHFblxoVot4Je2HyWGU.QyFxtPdpsAMP2hz4fGid5WQu',  -- admin123
    'Admin',
    'ACME',
    'admin@acme.com',
    1,
    1
);

-- Usuario user
INSERT INTO usuario (
    usuario_id,
    cliente_id,
    nombre_usuario,
    contrasena,
    nombre,
    apellido,
    correo,
    es_activo,
    correo_confirmado
) VALUES (
    '11111111-1111-1111-1111-111111111200',  -- user (UUID válido)
    '11111111-1111-1111-1111-111111111111',  -- ACME
    'user',
    '$2b$12$ZvpoS9E0eMe6pbxGNoho1eN8hMbeTCkAE5Fyztm1N.51jxcqVYW86',  -- user123
    'Usuario',
    'ACME',
    'user@acme.com',
    1,
    1
);

-- Asignar roles
INSERT INTO usuario_rol (
    usuario_rol_id,
    usuario_id,
    rol_id,
    cliente_id,
    es_activo
) VALUES
(
    NEWID(),
    '11111111-1111-1111-1111-111111111100',  -- admin (UUID válido)  -- admin
    '11111111-1111-1111-1111-111111111110',  -- ADMIN
    '11111111-1111-1111-1111-111111111111',  -- ACME
    1
),
(
    NEWID(),
    '11111111-1111-1111-1111-111111111200',  -- user (UUID válido)  -- user
    '11111111-1111-1111-1111-111111111120',  -- USER
    '11111111-1111-1111-1111-111111111111',  -- ACME
    1
);

-- Usuarios y roles para INNOVA (shared)
-- Rol ADMIN
INSERT INTO rol (
    rol_id,
    cliente_id,
    codigo_rol,
    nombre,
    descripcion,
    es_rol_sistema,
    nivel_acceso,
    es_activo
) VALUES (
    '22222222-2222-2222-2222-222222222210',  -- ADMIN (UUID válido)
    '22222222-2222-2222-2222-222222222222',  -- INNOVA
    'ADMIN',
    'Administrador',
    'Rol de administrador',
    1,
    4,
    1
);

-- Rol USER
INSERT INTO rol (
    rol_id,
    cliente_id,
    codigo_rol,
    nombre,
    descripcion,
    es_rol_sistema,
    nivel_acceso,
    es_activo
) VALUES (
    '22222222-2222-2222-2222-222222222220',  -- USER (UUID válido)
    '22222222-2222-2222-2222-222222222222',  -- INNOVA
    'USER',
    'Usuario',
    'Rol de usuario',
    1,
    1,
    1
);

-- Usuario admin
INSERT INTO usuario (
    usuario_id,
    cliente_id,
    nombre_usuario,
    contrasena,
    nombre,
    apellido,
    correo,
    es_activo,
    correo_confirmado
) VALUES (
    '22222222-2222-2222-2222-222222222100',  -- admin (UUID válido)
    '22222222-2222-2222-2222-222222222222',  -- INNOVA
    'admin',
    '$2b$12$6J/bWiSYNFHFblxoVot4Je2HyWGU.QyFxtPdpsAMP2hz4fGid5WQu',  -- admin123
    'Admin',
    'INNOVA',
    'admin@innova.com',
    1,
    1
);

-- Usuario user
INSERT INTO usuario (
    usuario_id,
    cliente_id,
    nombre_usuario,
    contrasena,
    nombre,
    apellido,
    correo,
    es_activo,
    correo_confirmado
) VALUES (
    '22222222-2222-2222-2222-222222222200',  -- user (UUID válido)
    '22222222-2222-2222-2222-222222222222',  -- INNOVA
    'user',
    '$2b$12$ZvpoS9E0eMe6pbxGNoho1eN8hMbeTCkAE5Fyztm1N.51jxcqVYW86',  -- user123
    'Usuario',
    'INNOVA',
    'user@innova.com',
    1,
    1
);

-- Asignar roles
INSERT INTO usuario_rol (
    usuario_rol_id,
    usuario_id,
    rol_id,
    cliente_id,
    es_activo
) VALUES
(
    NEWID(),
    '22222222-2222-2222-2222-222222222100',  -- admin (UUID válido)  -- admin
    '22222222-2222-2222-2222-222222222210',  -- ADMIN
    '22222222-2222-2222-2222-222222222222',  -- INNOVA
    1
),
(
    NEWID(),
    '22222222-2222-2222-2222-222222222200',  -- user (UUID válido)  -- user
    '22222222-2222-2222-2222-222222222220',  -- USER
    '22222222-2222-2222-2222-222222222222',  -- INNOVA
    1
);

-- ============================================================================
-- SECCIÓN 7: PERMISOS BÁSICOS (Para roles ADMIN y USER)
-- ============================================================================

-- Permisos para ADMIN de SUPERADMIN (acceso completo a todos los menús)
-- Nota: Se insertan permisos para los menús principales creados
INSERT INTO rol_menu_permiso (
    permiso_id,
    cliente_id,
    rol_id,
    menu_id,
    puede_ver,
    puede_crear,
    puede_editar,
    puede_eliminar,
    puede_exportar,
    puede_imprimir
) 
SELECT 
    NEWID(),
    '00000000-0000-0000-0000-000000000001',  -- SUPERADMIN
    '00000000-0000-0000-0000-000000000010',  -- ADMIN
    menu_id,
    1,  -- puede_ver
    1,  -- puede_crear
    1,  -- puede_editar
    1,  -- puede_eliminar
    1,  -- puede_exportar
    1   -- puede_imprimir
FROM modulo_menu
WHERE cliente_id IS NULL OR cliente_id = '00000000-0000-0000-0000-000000000001';

-- Permisos para USER de SUPERADMIN (solo lectura)
INSERT INTO rol_menu_permiso (
    permiso_id,
    cliente_id,
    rol_id,
    menu_id,
    puede_ver,
    puede_crear,
    puede_editar,
    puede_eliminar,
    puede_exportar,
    puede_imprimir
) 
SELECT 
    NEWID(),
    '00000000-0000-0000-0000-000000000001',  -- SUPERADMIN
    '00000000-0000-0000-0000-000000000020',  -- USER
    menu_id,
    1,  -- puede_ver
    0,  -- puede_crear
    0,  -- puede_editar
    0,  -- puede_eliminar
    0,  -- puede_exportar
    0   -- puede_imprimir
FROM modulo_menu
WHERE cliente_id IS NULL OR cliente_id = '00000000-0000-0000-0000-000000000001';

-- Permisos para ADMIN de ACME (acceso completo)
INSERT INTO rol_menu_permiso (
    permiso_id,
    cliente_id,
    rol_id,
    menu_id,
    puede_ver,
    puede_crear,
    puede_editar,
    puede_eliminar,
    puede_exportar,
    puede_imprimir
) 
SELECT 
    NEWID(),
    '11111111-1111-1111-1111-111111111111',  -- ACME
    '11111111-1111-1111-1111-111111111110',  -- ADMIN
    menu_id,
    1, 1, 1, 1, 1, 1
FROM modulo_menu
WHERE cliente_id IS NULL OR cliente_id = '11111111-1111-1111-1111-111111111111';

-- Permisos para USER de ACME (solo lectura)
INSERT INTO rol_menu_permiso (
    permiso_id,
    cliente_id,
    rol_id,
    menu_id,
    puede_ver,
    puede_crear,
    puede_editar,
    puede_eliminar,
    puede_exportar,
    puede_imprimir
) 
SELECT 
    NEWID(),
    '11111111-1111-1111-1111-111111111111',  -- ACME
    '11111111-1111-1111-1111-111111111120',  -- USER
    menu_id,
    1, 0, 0, 0, 0, 0
FROM modulo_menu
WHERE cliente_id IS NULL OR cliente_id = '11111111-1111-1111-1111-111111111111';

-- Permisos para ADMIN de INNOVA (acceso completo)
INSERT INTO rol_menu_permiso (
    permiso_id,
    cliente_id,
    rol_id,
    menu_id,
    puede_ver,
    puede_crear,
    puede_editar,
    puede_eliminar,
    puede_exportar,
    puede_imprimir
) 
SELECT 
    NEWID(),
    '22222222-2222-2222-2222-222222222222',  -- INNOVA
    '22222222-2222-2222-2222-222222222210',  -- ADMIN
    menu_id,
    1, 1, 1, 1, 1, 1
FROM modulo_menu
WHERE cliente_id IS NULL OR cliente_id = '22222222-2222-2222-2222-222222222222';

-- Permisos para USER de INNOVA (solo lectura)
INSERT INTO rol_menu_permiso (
    permiso_id,
    cliente_id,
    rol_id,
    menu_id,
    puede_ver,
    puede_crear,
    puede_editar,
    puede_eliminar,
    puede_exportar,
    puede_imprimir
) 
SELECT 
    NEWID(),
    '22222222-2222-2222-2222-222222222222',  -- INNOVA
    '22222222-2222-2222-2222-222222222220',  -- USER
    menu_id,
    1, 0, 0, 0, 0, 0
FROM modulo_menu
WHERE cliente_id IS NULL OR cliente_id = '22222222-2222-2222-2222-222222222222';

PRINT 'Seed de BD central completado exitosamente';
PRINT 'Clientes creados: SUPERADMIN, ACME (shared), INNOVA (shared), TECHCORP (dedicated), GLOBALLOG (dedicated)';
PRINT 'Módulos creados: ALMACEN, LOGISTICA, PLANILLAS';
PRINT 'Usuarios creados para clientes shared: admin y user en cada uno';
GO
