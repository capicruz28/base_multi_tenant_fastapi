-- ============================================================================
-- SCRIPT: SEED COMPLETO PARA modulo, modulo_seccion y modulo_menu
-- DESCRIPCIÓN: Pobla las tablas de catálogo de menú según MENU_NAVEGACION.md
-- DEPENDENCIAS: Ejecutar después de TABLAS_BD_CENTRAL.sql
-- USO: Ejecutar UNA SOLA VEZ. modulo_menu depende de modulo y modulo_seccion.
--      Si ya tiene datos en modulo (ej. SEED_BD_CENTRAL con ALMACEN/LOGISTICA/
--      PLANILLAS), no hay conflicto de codigo; este script agrega los 27
--      módulos del menú (ORG, INV, WMS, ...). Para BD nueva: ejecutar este
--      script completo.
-- ============================================================================

-- Descomentar y ajustar nombre de BD si es distinto al tuyo:
-- USE bd_hybrid_sistema_central;
-- GO

-- ============================================================================
-- SECCIÓN 1: MÓDULOS ERP (27 módulos según MENU_NAVEGACION.md)
-- ============================================================================

INSERT INTO modulo (modulo_id, codigo, nombre, descripcion, icono, color, categoria, es_core, requiere_licencia, orden, es_activo) VALUES
('E1000001-0000-4000-8000-000000000001', 'ORG', 'Organización', 'Mi Empresa, Sucursales, Departamentos, Cargos, Centros de Costo, Parámetros', 'building-2', '#1976D2', 'operaciones', 1, 0, 1, 1),
('E1000002-0000-4000-8000-000000000002', 'INV', 'Inventarios', 'Productos, Categorías, Unidades, Almacenes, Stock, Movimientos, Inventario Físico', 'inventory_2', '#4CAF50', 'operaciones', 0, 1, 2, 1),
('E1000003-0000-4000-8000-000000000003', 'WMS', 'Gestión de Almacenes', 'Zonas, Ubicaciones, Stock por Ubicación, Tareas de Almacén', 'warehouse', '#8BC34A', 'operaciones', 0, 1, 3, 1),
('E1000004-0000-4000-8000-000000000004', 'QMS', 'Control de Calidad', 'Parámetros de Calidad, Planes de Inspección, Inspecciones, No Conformidades', 'verified', '#009688', 'operaciones', 0, 1, 4, 1),
('E1000005-0000-4000-8000-000000000005', 'PUR', 'Compras', 'Proveedores, Contactos, Productos por Proveedor, Solicitudes, Cotizaciones, OC, Recepción', 'shopping_cart', '#FF9800', 'operaciones', 0, 1, 5, 1),
('E1000006-0000-4000-8000-000000000006', 'LOG', 'Logística y Distribución', 'Transportistas, Vehículos, Rutas, Guías de Remisión, Despachos', 'local_shipping', '#2196F3', 'operaciones', 0, 1, 6, 1),
('E1000007-0000-4000-8000-000000000007', 'MFG', 'Producción y Manufactura', 'Centros de Trabajo, Operaciones, BOM, Rutas de Fabricación, Órdenes de Producción', 'precision_manufacturing', '#673AB7', 'operaciones', 0, 1, 7, 1),
('E1000008-0000-4000-8000-000000000008', 'MRP', 'Planeamiento de Materiales', 'Plan Maestro MRP, Necesidades Brutas, Explosión de Materiales, Órdenes Sugeridas', 'account_tree', '#3F51B5', 'operaciones', 0, 1, 8, 1),
('E1000009-0000-4000-8000-000000000009', 'MPS', 'Plan Maestro de Producción', 'Pronóstico de Demanda, Plan de Producción', 'timeline', '#3F51B5', 'operaciones', 0, 1, 9, 1),
('E100000A-0000-4000-8000-00000000000A', 'MNT', 'Mantenimiento', 'Activos, Planes de Mantenimiento, Órdenes de Trabajo, Historial', 'build', '#795548', 'operaciones', 0, 1, 10, 1),
('E100000B-0000-4000-8000-00000000000B', 'SLS', 'Ventas', 'Clientes, Contactos, Direcciones de Entrega, Cotizaciones, Pedidos de Venta', 'store', '#E91E63', 'ventas', 0, 1, 11, 1),
('E100000C-0000-4000-8000-00000000000C', 'CRM', 'Gestión de Clientes', 'Campañas, Leads, Oportunidades, Actividades', 'group', '#9C27B0', 'ventas', 0, 1, 12, 1),
('E100000D-0000-4000-8000-00000000000D', 'PRC', 'Precios y Promociones', 'Listas de Precios, Promociones', 'local_offer', '#E91E63', 'ventas', 0, 1, 13, 1),
('E100000E-0000-4000-8000-00000000000E', 'INV_BILL', 'Facturación Electrónica', 'Series de Comprobantes, Comprobantes, Registro de Ventas', 'receipt', '#F44336', 'ventas', 0, 1, 14, 1),
('E100000F-0000-4000-8000-00000000000F', 'POS', 'Punto de Venta', 'Puntos de Venta, Turnos de Caja, Ventas Rápidas', 'point_of_sale', '#FF5722', 'ventas', 0, 1, 15, 1),
('E1000010-0000-4000-8000-000000000010', 'HCM', 'Planillas y RRHH', 'Empleados, Contratos, Conceptos de Planilla, Planillas, Asistencia, Vacaciones, Préstamos', 'payments', '#FF9800', 'rrhh', 0, 1, 16, 1),
('E1000011-0000-4000-8000-000000000011', 'FIN', 'Contabilidad', 'Plan de Cuentas, Periodos Contables, Asientos, Libros Mayores, Estados Financieros', 'account_balance', '#4CAF50', 'finanzas', 0, 1, 17, 1),
('E1000012-0000-4000-8000-000000000012', 'TAX', 'Libros Electrónicos', 'PLE SUNAT', 'description', '#607D8B', 'finanzas', 0, 1, 18, 1),
('E1000013-0000-4000-8000-000000000013', 'BDG', 'Presupuestos', 'Presupuestos, Ejecución Presupuestal', 'savings', '#009688', 'finanzas', 0, 1, 19, 1),
('E1000014-0000-4000-8000-000000000014', 'CST', 'Costeo de Productos', 'Tipos de Centro de Costo, Costo de Productos, Análisis de Variaciones', 'analytics', '#00BCD4', 'finanzas', 0, 1, 20, 1),
('E1000015-0000-4000-8000-000000000015', 'PM', 'Gestión de Proyectos', 'Proyectos, Seguimiento', 'folder', '#8BC34A', 'proyectos', 0, 1, 21, 1),
('E1000016-0000-4000-8000-000000000016', 'SVC', 'Órdenes de Servicio', 'Órdenes de Servicio, Envío a Talleres, Stock en Terceros', 'build_circle', '#FF9800', 'servicios', 0, 1, 22, 1),
('E1000017-0000-4000-8000-000000000017', 'TKT', 'Mesa de Ayuda', 'Tickets', 'confirmation_number', '#9E9E9E', 'soporte', 0, 1, 23, 1),
('E1000018-0000-4000-8000-000000000018', 'BI', 'Reportes y Analytics', 'Reportes Configurables, Dashboards', 'bar_chart', '#2196F3', 'reportes', 0, 1, 24, 1),
('E1000019-0000-4000-8000-000000000019', 'DMS', 'Gestión Documental', 'Documentos, Búsqueda', 'folder_open', '#795548', 'documentos', 0, 1, 25, 1),
('E100001A-0000-4000-8000-00000000001A', 'WFL', 'Flujos de Trabajo', 'Workflows, Seguimiento', 'account_tree', '#673AB7', 'configuracion', 0, 1, 26, 1),
('E100001B-0000-4000-8000-00000000001B', 'AUD', 'Auditoría', 'Log de Auditoría, Reportes de Trazabilidad', 'history', '#607D8B', 'auditoria', 0, 1, 27, 1);

-- ============================================================================
-- SECCIÓN 2: SECCIONES (una por módulo, para agrupar menús)
-- ============================================================================

INSERT INTO modulo_seccion (seccion_id, modulo_id, codigo, nombre, descripcion, icono, orden, es_seccion_sistema, es_activo) VALUES
('E2000001-0000-4000-8000-000000000001', 'E1000001-0000-4000-8000-000000000001', 'PRINCIPAL', 'Principal', 'Opciones del módulo Organización', 'building-2', 1, 1, 1),
('E2000002-0000-4000-8000-000000000002', 'E1000002-0000-4000-8000-000000000002', 'PRINCIPAL', 'Principal', 'Opciones del módulo Inventarios', 'inventory_2', 1, 1, 1),
('E2000003-0000-4000-8000-000000000003', 'E1000003-0000-4000-8000-000000000003', 'PRINCIPAL', 'Principal', 'Opciones WMS', 'warehouse', 1, 1, 1),
('E2000004-0000-4000-8000-000000000004', 'E1000004-0000-4000-8000-000000000004', 'PRINCIPAL', 'Principal', 'Opciones QMS', 'verified', 1, 1, 1),
('E2000005-0000-4000-8000-000000000005', 'E1000005-0000-4000-8000-000000000005', 'PRINCIPAL', 'Principal', 'Opciones Compras', 'shopping_cart', 1, 1, 1),
('E2000006-0000-4000-8000-000000000006', 'E1000006-0000-4000-8000-000000000006', 'PRINCIPAL', 'Principal', 'Opciones Logística', 'local_shipping', 1, 1, 1),
('E2000007-0000-4000-8000-000000000007', 'E1000007-0000-4000-8000-000000000007', 'PRINCIPAL', 'Principal', 'Opciones Producción', 'precision_manufacturing', 1, 1, 1),
('E2000008-0000-4000-8000-000000000008', 'E1000008-0000-4000-8000-000000000008', 'PRINCIPAL', 'Principal', 'Opciones MRP', 'account_tree', 1, 1, 1),
('E2000009-0000-4000-8000-000000000009', 'E1000009-0000-4000-8000-000000000009', 'PRINCIPAL', 'Principal', 'Opciones MPS', 'timeline', 1, 1, 1),
('E200000A-0000-4000-8000-00000000000A', 'E100000A-0000-4000-8000-00000000000A', 'PRINCIPAL', 'Principal', 'Opciones Mantenimiento', 'build', 1, 1, 1),
('E200000B-0000-4000-8000-00000000000B', 'E100000B-0000-4000-8000-00000000000B', 'PRINCIPAL', 'Principal', 'Opciones Ventas', 'store', 1, 1, 1),
('E200000C-0000-4000-8000-00000000000C', 'E100000C-0000-4000-8000-00000000000C', 'PRINCIPAL', 'Principal', 'Opciones CRM', 'group', 1, 1, 1),
('E200000D-0000-4000-8000-00000000000D', 'E100000D-0000-4000-8000-00000000000D', 'PRINCIPAL', 'Principal', 'Opciones Precios', 'local_offer', 1, 1, 1),
('E200000E-0000-4000-8000-00000000000E', 'E100000E-0000-4000-8000-00000000000E', 'PRINCIPAL', 'Principal', 'Opciones Facturación', 'receipt', 1, 1, 1),
('E200000F-0000-4000-8000-00000000000F', 'E100000F-0000-4000-8000-00000000000F', 'PRINCIPAL', 'Principal', 'Opciones POS', 'point_of_sale', 1, 1, 1),
('E2000010-0000-4000-8000-000000000010', 'E1000010-0000-4000-8000-000000000010', 'PRINCIPAL', 'Principal', 'Opciones RRHH', 'payments', 1, 1, 1),
('E2000011-0000-4000-8000-000000000011', 'E1000011-0000-4000-8000-000000000011', 'PRINCIPAL', 'Principal', 'Opciones Contabilidad', 'account_balance', 1, 1, 1),
('E2000012-0000-4000-8000-000000000012', 'E1000012-0000-4000-8000-000000000012', 'PRINCIPAL', 'Principal', 'Opciones Libros Electrónicos', 'description', 1, 1, 1),
('E2000013-0000-4000-8000-000000000013', 'E1000013-0000-4000-8000-000000000013', 'PRINCIPAL', 'Principal', 'Opciones Presupuestos', 'savings', 1, 1, 1),
('E2000014-0000-4000-8000-000000000014', 'E1000014-0000-4000-8000-000000000014', 'PRINCIPAL', 'Principal', 'Opciones Costeo', 'analytics', 1, 1, 1),
('E2000015-0000-4000-8000-000000000015', 'E1000015-0000-4000-8000-000000000015', 'PRINCIPAL', 'Principal', 'Opciones Proyectos', 'folder', 1, 1, 1),
('E2000016-0000-4000-8000-000000000016', 'E1000016-0000-4000-8000-000000000016', 'PRINCIPAL', 'Principal', 'Opciones Servicio', 'build_circle', 1, 1, 1),
('E2000017-0000-4000-8000-000000000017', 'E1000017-0000-4000-8000-000000000017', 'PRINCIPAL', 'Principal', 'Opciones Mesa de Ayuda', 'confirmation_number', 1, 1, 1),
('E2000018-0000-4000-8000-000000000018', 'E1000018-0000-4000-8000-000000000018', 'PRINCIPAL', 'Principal', 'Opciones Reportes', 'bar_chart', 1, 1, 1),
('E2000019-0000-4000-8000-000000000019', 'E1000019-0000-4000-8000-000000000019', 'PRINCIPAL', 'Principal', 'Opciones Documentos', 'folder_open', 1, 1, 1),
('E200001A-0000-4000-8000-00000000001A', 'E100001A-0000-4000-8000-00000000001A', 'PRINCIPAL', 'Principal', 'Opciones Workflows', 'account_tree', 1, 1, 1),
('E200001B-0000-4000-8000-00000000001B', 'E100001B-0000-4000-8000-00000000001B', 'PRINCIPAL', 'Principal', 'Opciones Auditoría', 'history', 1, 1, 1);

-- ============================================================================
-- SECCIÓN 3: MENÚS POR MÓDULO (modulo_menu) — Según MENU_NAVEGACION.md
-- Rutas alineadas con API: /org/..., /inv/..., etc.
-- ============================================================================

-- ----- ORG (6 ítems) -----
INSERT INTO modulo_menu (menu_id, modulo_id, seccion_id, cliente_id, codigo, nombre, descripcion, icono, ruta, menu_padre_id, nivel, tipo_menu, orden, requiere_autenticacion, es_visible, es_menu_sistema, es_activo) VALUES
('E3010001-0000-4000-8000-000000000001', 'E1000001-0000-4000-8000-000000000001', 'E2000001-0000-4000-8000-000000000001', NULL, 'ORG_MI_EMPRESA', 'Mi Empresa', 'Ver y editar datos de la empresa (RUC, razón social, logo, moneda)', 'building-2', '/org/empresa', NULL, 1, 'pantalla', 1, 1, 1, 1, 1),
('E3010002-0000-4000-8000-000000000002', 'E1000001-0000-4000-8000-000000000001', 'E2000001-0000-4000-8000-000000000001', NULL, 'ORG_SUCURSALES', 'Sucursales', 'Gestionar sucursales con dirección, teléfono, responsable', 'apartment', '/org/sucursales', NULL, 1, 'pantalla', 2, 1, 1, 1, 1),
('E3010003-0000-4000-8000-000000000003', 'E1000001-0000-4000-8000-000000000001', 'E2000001-0000-4000-8000-000000000001', NULL, 'ORG_DEPARTAMENTOS', 'Departamentos', 'Crear estructura organizacional jerárquica por áreas', 'corporate_fare', '/org/departamentos', NULL, 1, 'pantalla', 3, 1, 1, 1, 1),
('E3010004-0000-4000-8000-000000000004', 'E1000001-0000-4000-8000-000000000001', 'E2000001-0000-4000-8000-000000000001', NULL, 'ORG_CARGOS', 'Cargos', 'Definir puestos de trabajo (gerente, operario, vendedor, etc.)', 'badge', '/org/cargos', NULL, 1, 'pantalla', 4, 1, 1, 1, 1),
('E3010005-0000-4000-8000-000000000005', 'E1000001-0000-4000-8000-000000000001', 'E2000001-0000-4000-8000-000000000001', NULL, 'ORG_CENTROS_COSTO', 'Centros de Costo', 'Configurar centros para control de gastos por área', 'account_balance_wallet', '/org/centros-costo', NULL, 1, 'pantalla', 5, 1, 1, 1, 1),
('E3010006-0000-4000-8000-000000000006', 'E1000001-0000-4000-8000-000000000001', 'E2000001-0000-4000-8000-000000000001', NULL, 'ORG_PARAMETROS', 'Parámetros del Sistema', 'Configuración global (métodos costeo, afectación IGV, decimales)', 'settings', '/org/parametros', NULL, 1, 'pantalla', 6, 1, 1, 1, 1);

-- ----- INV (9 ítems) -----
INSERT INTO modulo_menu (menu_id, modulo_id, seccion_id, cliente_id, codigo, nombre, descripcion, icono, ruta, menu_padre_id, nivel, tipo_menu, orden, requiere_autenticacion, es_visible, es_menu_sistema, es_activo) VALUES
('E3020001-0000-4000-8000-000000000001', 'E1000002-0000-4000-8000-000000000002', 'E2000002-0000-4000-8000-000000000002', NULL, 'INV_PRODUCTOS', 'Productos', 'Catálogo completo con SKU, código de barras, categoría, precio', 'inventory_2', '/inv/productos', NULL, 1, 'pantalla', 1, 1, 1, 1, 1),
('E3020002-0000-4000-8000-000000000002', 'E1000002-0000-4000-8000-000000000002', 'E2000002-0000-4000-8000-000000000002', NULL, 'INV_CATEGORIAS', 'Categorías', 'Organizar productos en categorías y subcategorías', 'category', '/inv/categorias', NULL, 1, 'pantalla', 2, 1, 1, 1, 1),
('E3020003-0000-4000-8000-000000000003', 'E1000002-0000-4000-8000-000000000002', 'E2000002-0000-4000-8000-000000000002', NULL, 'INV_UNIDADES', 'Unidades de Medida', 'Gestionar UND, KG, MT, LT con factores de conversión', 'straighten', '/inv/unidades-medida', NULL, 1, 'pantalla', 3, 1, 1, 1, 1),
('E3020004-0000-4000-8000-000000000004', 'E1000002-0000-4000-8000-000000000002', 'E2000002-0000-4000-8000-000000000002', NULL, 'INV_ALMACENES', 'Almacenes', 'Configurar almacenes físicos y virtuales', 'warehouse', '/inv/almacenes', NULL, 1, 'pantalla', 4, 1, 1, 1, 1),
('E3020005-0000-4000-8000-000000000005', 'E1000002-0000-4000-8000-000000000002', 'E2000002-0000-4000-8000-000000000002', NULL, 'INV_STOCK', 'Consulta de Stock', 'Ver stock actual, reservado y disponible por almacén', 'assessment', '/inv/stock', NULL, 1, 'pantalla', 5, 1, 1, 1, 1),
('E3020006-0000-4000-8000-000000000006', 'E1000002-0000-4000-8000-000000000002', 'E2000002-0000-4000-8000-000000000002', NULL, 'INV_TIPOS_MOV', 'Tipos de Movimiento', 'Definir tipos: compra, venta, ajuste, transferencia', 'swap_horiz', '/inv/tipos-movimiento', NULL, 1, 'pantalla', 6, 1, 1, 1, 1),
('E3020007-0000-4000-8000-000000000007', 'E1000002-0000-4000-8000-000000000002', 'E2000002-0000-4000-8000-000000000002', NULL, 'INV_MOVIMIENTOS', 'Movimientos de Inventario', 'Registrar entradas, salidas, transferencias', 'input', '/inv/movimientos', NULL, 1, 'pantalla', 7, 1, 1, 1, 1),
('E3020008-0000-4000-8000-000000000008', 'E1000002-0000-4000-8000-000000000002', 'E2000002-0000-4000-8000-000000000002', NULL, 'INV_INV_FISICO', 'Inventario Físico', 'Toma de inventario y ajuste de diferencias', 'checklist', '/inv/inventario-fisico', NULL, 1, 'pantalla', 8, 1, 1, 1, 1);

-- ----- WMS (4) -----
INSERT INTO modulo_menu (menu_id, modulo_id, seccion_id, cliente_id, codigo, nombre, descripcion, icono, ruta, menu_padre_id, nivel, tipo_menu, orden, requiere_autenticacion, es_visible, es_menu_sistema, es_activo) VALUES
('E3030001-0000-4000-8000-000000000001', 'E1000003-0000-4000-8000-000000000003', 'E2000003-0000-4000-8000-000000000003', NULL, 'WMS_ZONAS', 'Zonas de Almacén', 'Dividir almacén en zonas (recepción, picking, despacho)', 'grid_on', '/wms/zonas', NULL, 1, 'pantalla', 1, 1, 1, 1, 1),
('E3030002-0000-4000-8000-000000000002', 'E1000003-0000-4000-8000-000000000003', 'E2000003-0000-4000-8000-000000000003', NULL, 'WMS_UBICACIONES', 'Ubicaciones', 'Definir pasillo-rack-nivel-posición', 'place', '/wms/ubicaciones', NULL, 1, 'pantalla', 2, 1, 1, 1, 1),
('E3030003-0000-4000-8000-000000000003', 'E1000003-0000-4000-8000-000000000003', 'E2000003-0000-4000-8000-000000000003', NULL, 'WMS_STOCK_UBIC', 'Stock por Ubicación', 'Ver qué hay en cada ubicación', 'view_list', '/wms/stock-ubicacion', NULL, 1, 'pantalla', 3, 1, 1, 1, 1),
('E3030004-0000-4000-8000-000000000004', 'E1000003-0000-4000-8000-000000000003', 'E2000003-0000-4000-8000-000000000003', NULL, 'WMS_TAREAS', 'Tareas de Almacén', 'Picking, Putaway, Reabastecimiento', 'task_alt', '/wms/tareas', NULL, 1, 'pantalla', 4, 1, 1, 1, 1);

-- ----- QMS (4) -----
INSERT INTO modulo_menu (menu_id, modulo_id, seccion_id, cliente_id, codigo, nombre, descripcion, icono, ruta, menu_padre_id, nivel, tipo_menu, orden, requiere_autenticacion, es_visible, es_menu_sistema, es_activo) VALUES
('E3040001-0000-4000-8000-000000000001', 'E1000004-0000-4000-8000-000000000004', 'E2000004-0000-4000-8000-000000000004', NULL, 'QMS_PARAMETROS', 'Parámetros de Calidad', 'Definir qué medir (peso, dimensiones, color)', 'tune', '/qms/parametros', NULL, 1, 'pantalla', 1, 1, 1, 1, 1),
('E3040002-0000-4000-8000-000000000002', 'E1000004-0000-4000-8000-000000000004', 'E2000004-0000-4000-8000-000000000004', NULL, 'QMS_PLANES', 'Planes de Inspección', 'Planes con muestreo AQL', 'assignment', '/qms/planes-inspeccion', NULL, 1, 'pantalla', 2, 1, 1, 1, 1),
('E3040003-0000-4000-8000-000000000003', 'E1000004-0000-4000-8000-000000000004', 'E2000004-0000-4000-8000-000000000004', NULL, 'QMS_INSPECCIONES', 'Inspecciones', 'Registrar resultados aprobado/rechazado', 'search', '/qms/inspecciones', NULL, 1, 'pantalla', 3, 1, 1, 1, 1),
('E3040004-0000-4000-8000-000000000004', 'E1000004-0000-4000-8000-000000000004', 'E2000004-0000-4000-8000-000000000004', NULL, 'QMS_NO_CONFORMIDADES', 'No Conformidades', 'Defectos, causas raíz, acciones correctivas', 'warning', '/qms/no-conformidades', NULL, 1, 'pantalla', 4, 1, 1, 1, 1);

-- ----- PUR (7) -----
INSERT INTO modulo_menu (menu_id, modulo_id, seccion_id, cliente_id, codigo, nombre, descripcion, icono, ruta, menu_padre_id, nivel, tipo_menu, orden, requiere_autenticacion, es_visible, es_menu_sistema, es_activo) VALUES
('E3050001-0000-4000-8000-000000000001', 'E1000005-0000-4000-8000-000000000005', 'E2000005-0000-4000-8000-000000000005', NULL, 'PUR_PROVEEDORES', 'Proveedores', 'Catálogo con RUC, contactos, condiciones de pago', 'building-2', '/pur/proveedores', NULL, 1, 'pantalla', 1, 1, 1, 1, 1),
('E3050002-0000-4000-8000-000000000002', 'E1000005-0000-4000-8000-000000000005', 'E2000005-0000-4000-8000-000000000005', NULL, 'PUR_CONTACTOS', 'Contactos de Proveedor', 'Vendedores y contactos del proveedor', 'contacts', '/pur/contactos-proveedor', NULL, 1, 'pantalla', 2, 1, 1, 1, 1),
('E3050003-0000-4000-8000-000000000003', 'E1000005-0000-4000-8000-000000000005', 'E2000005-0000-4000-8000-000000000005', NULL, 'PUR_PRODUCTOS_PROV', 'Productos por Proveedor', 'Qué productos vende cada proveedor', 'list', '/pur/productos-proveedor', NULL, 1, 'pantalla', 3, 1, 1, 1, 1),
('E3050004-0000-4000-8000-000000000004', 'E1000005-0000-4000-8000-000000000005', 'E2000005-0000-4000-8000-000000000005', NULL, 'PUR_SOLICITUDES', 'Solicitudes de Compra', 'Requisiciones internas', 'request_quote', '/pur/solicitudes-compra', NULL, 1, 'pantalla', 4, 1, 1, 1, 1),
('E3050005-0000-4000-8000-000000000005', 'E1000005-0000-4000-8000-000000000005', 'E2000005-0000-4000-8000-000000000005', NULL, 'PUR_COTIZACIONES', 'Cotizaciones', 'Solicitar cotizaciones a proveedores', 'request_quote', '/pur/cotizaciones', NULL, 1, 'pantalla', 5, 1, 1, 1, 1),
('E3050006-0000-4000-8000-000000000006', 'E1000005-0000-4000-8000-000000000005', 'E2000005-0000-4000-8000-000000000005', NULL, 'PUR_ORDENES', 'Órdenes de Compra', 'Generar OC con numeración automática', 'shopping_cart', '/pur/ordenes-compra', NULL, 1, 'pantalla', 6, 1, 1, 1, 1),
('E3050007-0000-4000-8000-000000000007', 'E1000005-0000-4000-8000-000000000005', 'E2000005-0000-4000-8000-000000000005', NULL, 'PUR_RECEPCION', 'Recepción de Mercadería', 'Registrar cantidades recibidas vs ordenadas', 'local_shipping', '/pur/recepcion', NULL, 1, 'pantalla', 7, 1, 1, 1, 1);

-- ----- LOG (5) -----
INSERT INTO modulo_menu (menu_id, modulo_id, seccion_id, cliente_id, codigo, nombre, descripcion, icono, ruta, menu_padre_id, nivel, tipo_menu, orden, requiere_autenticacion, es_visible, es_menu_sistema, es_activo) VALUES
('E3060001-0000-4000-8000-000000000001', 'E1000006-0000-4000-8000-000000000006', 'E2000006-0000-4000-8000-000000000006', NULL, 'LOG_TRANSPORTISTAS', 'Transportistas', 'Empresas de transporte con RUC y certificados', 'local_shipping', '/log/transportistas', NULL, 1, 'pantalla', 1, 1, 1, 1, 1),
('E3060002-0000-4000-8000-000000000002', 'E1000006-0000-4000-8000-000000000006', 'E2000006-0000-4000-8000-000000000006', NULL, 'LOG_VEHICULOS', 'Vehículos', 'Flota con placas, capacidad, GPS', 'directions_car', '/log/vehiculos', NULL, 1, 'pantalla', 2, 1, 1, 1, 1),
('E3060003-0000-4000-8000-000000000003', 'E1000006-0000-4000-8000-000000000006', 'E2000006-0000-4000-8000-000000000006', NULL, 'LOG_RUTAS', 'Rutas', 'Rutas predefinidas con puntos de entrega', 'route', '/log/rutas', NULL, 1, 'pantalla', 3, 1, 1, 1, 1),
('E3060004-0000-4000-8000-000000000004', 'E1000006-0000-4000-8000-000000000006', 'E2000006-0000-4000-8000-000000000006', NULL, 'LOG_GUIAS', 'Guías de Remisión', 'Generar GR electrónicas (SUNAT)', 'description', '/log/guias-remision', NULL, 1, 'pantalla', 4, 1, 1, 1, 1),
('E3060005-0000-4000-8000-000000000005', 'E1000006-0000-4000-8000-000000000006', 'E2000006-0000-4000-8000-000000000006', NULL, 'LOG_DESPACHOS', 'Despachos', 'Programar entregas con transportista y ruta', 'delivery_dining', '/log/despachos', NULL, 1, 'pantalla', 5, 1, 1, 1, 1);

-- ----- MFG (7) -----
INSERT INTO modulo_menu (menu_id, modulo_id, seccion_id, cliente_id, codigo, nombre, descripcion, icono, ruta, menu_padre_id, nivel, tipo_menu, orden, requiere_autenticacion, es_visible, es_menu_sistema, es_activo) VALUES
('E3070001-0000-4000-8000-000000000001', 'E1000007-0000-4000-8000-000000000007', 'E2000007-0000-4000-8000-000000000007', NULL, 'MFG_CENTROS', 'Centros de Trabajo', 'Máquinas y estaciones de trabajo', 'precision_manufacturing', '/mfg/centros-trabajo', NULL, 1, 'pantalla', 1, 1, 1, 1, 1),
('E3070002-0000-4000-8000-000000000002', 'E1000007-0000-4000-8000-000000000007', 'E2000007-0000-4000-8000-000000000007', NULL, 'MFG_OPERACIONES', 'Operaciones', 'Procesos individuales (corte, armado, empaque)', 'settings', '/mfg/operaciones', NULL, 1, 'pantalla', 2, 1, 1, 1, 1),
('E3070003-0000-4000-8000-000000000003', 'E1000007-0000-4000-8000-000000000007', 'E2000007-0000-4000-8000-000000000007', NULL, 'MFG_BOM', 'Lista de Materiales (BOM)', 'Ficha técnica con componentes multinivel', 'account_tree', '/mfg/listas-materiales', NULL, 1, 'pantalla', 3, 1, 1, 1, 1),
('E3070004-0000-4000-8000-000000000004', 'E1000007-0000-4000-8000-000000000007', 'E2000007-0000-4000-8000-000000000007', NULL, 'MFG_RUTAS', 'Rutas de Fabricación', 'Secuencia de operaciones por producto', 'timeline', '/mfg/rutas-fabricacion', NULL, 1, 'pantalla', 4, 1, 1, 1, 1),
('E3070005-0000-4000-8000-000000000005', 'E1000007-0000-4000-8000-000000000007', 'E2000007-0000-4000-8000-000000000007', NULL, 'MFG_OP', 'Órdenes de Producción', 'Programar producción con cantidad y fecha', 'assignment', '/mfg/ordenes-produccion', NULL, 1, 'pantalla', 5, 1, 1, 1, 1),
('E3070006-0000-4000-8000-000000000006', 'E1000007-0000-4000-8000-000000000007', 'E2000007-0000-4000-8000-000000000007', NULL, 'MFG_CONSUMO', 'Consumo de Materiales', 'Registrar materiales consumidos en cada OP', 'input', '/mfg/consumo-materiales', NULL, 1, 'pantalla', 6, 1, 1, 1, 1),
('E3070007-0000-4000-8000-000000000007', 'E1000007-0000-4000-8000-000000000007', 'E2000007-0000-4000-8000-000000000007', NULL, 'MFG_OP_OPER', 'Operaciones de OP', 'Registrar avance por operación', 'build', '/mfg/operaciones-op', NULL, 1, 'pantalla', 7, 1, 1, 1, 1);

-- ----- MRP (3), MPS (2), MNT (4), SLS (6), CRM (4), PRC (2), INV_BILL (3), POS (3) -----
INSERT INTO modulo_menu (menu_id, modulo_id, seccion_id, cliente_id, codigo, nombre, descripcion, icono, ruta, menu_padre_id, nivel, tipo_menu, orden, requiere_autenticacion, es_visible, es_menu_sistema, es_activo) VALUES
('E3080001-0000-4000-8000-000000000001', 'E1000008-0000-4000-8000-000000000008', 'E2000008-0000-4000-8000-000000000008', NULL, 'MRP_PLAN', 'Plan Maestro MRP', 'Horizonte de planeamiento', 'timeline', '/mrp/plan-maestro', NULL, 1, 'pantalla', 1, 1, 1, 1, 1),
('E3080002-0000-4000-8000-000000000002', 'E1000008-0000-4000-8000-000000000008', 'E2000008-0000-4000-8000-000000000008', NULL, 'MRP_NECESIDADES', 'Necesidades Brutas', 'Demanda calculada', 'assessment', '/mrp/necesidades-brutas', NULL, 1, 'pantalla', 2, 1, 1, 1, 1),
('E3080003-0000-4000-8000-000000000003', 'E1000008-0000-4000-8000-000000000008', 'E2000008-0000-4000-8000-000000000008', NULL, 'MRP_ORDENES', 'Órdenes Sugeridas', 'Qué comprar y cuándo', 'shopping_cart', '/mrp/ordenes-sugeridas', NULL, 1, 'pantalla', 3, 1, 1, 1, 1),
('E3090001-0000-4000-8000-000000000001', 'E1000009-0000-4000-8000-000000000009', 'E2000009-0000-4000-8000-000000000009', NULL, 'MPS_PRONOSTICO', 'Pronóstico de Demanda', 'Estimación de ventas futuras', 'trending_up', '/mps/pronostico-demanda', NULL, 1, 'pantalla', 1, 1, 1, 1, 1),
('E3090002-0000-4000-8000-000000000002', 'E1000009-0000-4000-8000-000000000009', 'E2000009-0000-4000-8000-000000000009', NULL, 'MPS_PLAN', 'Plan de Producción', 'Qué producir cada periodo', 'calendar_today', '/mps/plan-produccion', NULL, 1, 'pantalla', 2, 1, 1, 1, 1),
('E30A0001-0000-4000-8000-000000000001', 'E100000A-0000-4000-8000-00000000000A', 'E200000A-0000-4000-8000-00000000000A', NULL, 'MNT_ACTIVOS', 'Activos', 'Maquinaria y equipos con criticidad', 'build', '/mnt/activos', NULL, 1, 'pantalla', 1, 1, 1, 1, 1),
('E30A0002-0000-4000-8000-000000000002', 'E100000A-0000-4000-8000-00000000000A', 'E200000A-0000-4000-8000-00000000000A', NULL, 'MNT_PLANES', 'Planes de Mantenimiento', 'Preventivo y predictivo', 'schedule', '/mnt/planes-mantenimiento', NULL, 1, 'pantalla', 2, 1, 1, 1, 1),
('E30A0003-0000-4000-8000-000000000003', 'E100000A-0000-4000-8000-00000000000A', 'E200000A-0000-4000-8000-00000000000A', NULL, 'MNT_OT', 'Órdenes de Trabajo', 'Programar mantenimientos', 'assignment', '/mnt/ordenes-trabajo', NULL, 1, 'pantalla', 3, 1, 1, 1, 1),
('E30A0004-0000-4000-8000-000000000004', 'E100000A-0000-4000-8000-00000000000A', 'E200000A-0000-4000-8000-00000000000A', NULL, 'MNT_HISTORIAL', 'Historial de Mantenimiento', 'Trazabilidad de intervenciones', 'history', '/mnt/historial-mantenimiento', NULL, 1, 'pantalla', 4, 1, 1, 1, 1),
('E30B0001-0000-4000-8000-000000000001', 'E100000B-0000-4000-8000-00000000000B', 'E200000B-0000-4000-8000-00000000000B', NULL, 'SLS_CLIENTES', 'Clientes', 'Catálogo con RUC, límite de crédito', 'people', '/sls/clientes', NULL, 1, 'pantalla', 1, 1, 1, 1, 1),
('E30B0002-0000-4000-8000-000000000002', 'E100000B-0000-4000-8000-00000000000B', 'E200000B-0000-4000-8000-00000000000B', NULL, 'SLS_CONTACTOS', 'Contactos de Cliente', 'Personas de contacto', 'contacts', '/sls/contactos-cliente', NULL, 1, 'pantalla', 2, 1, 1, 1, 1),
('E30B0003-0000-4000-8000-000000000003', 'E100000B-0000-4000-8000-00000000000B', 'E200000B-0000-4000-8000-00000000000B', NULL, 'SLS_DIRECCIONES', 'Direcciones de Entrega', 'Múltiples direcciones por cliente', 'place', '/sls/direcciones-entrega', NULL, 1, 'pantalla', 3, 1, 1, 1, 1),
('E30B0004-0000-4000-8000-000000000004', 'E100000B-0000-4000-8000-00000000000B', 'E200000B-0000-4000-8000-00000000000B', NULL, 'SLS_COTIZACIONES', 'Cotizaciones', 'Generar cotizaciones con vigencia', 'request_quote', '/sls/cotizaciones', NULL, 1, 'pantalla', 4, 1, 1, 1, 1),
('E30B0005-0000-4000-8000-000000000005', 'E100000B-0000-4000-8000-00000000000B', 'E200000B-0000-4000-8000-00000000000B', NULL, 'SLS_PEDIDOS', 'Pedidos de Venta', 'Crear pedidos que reservan stock', 'shopping_cart', '/sls/pedidos', NULL, 1, 'pantalla', 5, 1, 1, 1, 1),
('E30C0001-0000-4000-8000-000000000001', 'E100000C-0000-4000-8000-00000000000C', 'E200000C-0000-4000-8000-00000000000C', NULL, 'CRM_CAMPANAS', 'Campañas', 'Campañas de marketing con métricas', 'campaign', '/crm/campanas', NULL, 1, 'pantalla', 1, 1, 1, 1, 1),
('E30C0002-0000-4000-8000-000000000002', 'E100000C-0000-4000-8000-00000000000C', 'E200000C-0000-4000-8000-00000000000C', NULL, 'CRM_LEADS', 'Leads', 'Prospectos con lead scoring', 'person_search', '/crm/leads', NULL, 1, 'pantalla', 2, 1, 1, 1, 1),
('E30C0003-0000-4000-8000-000000000003', 'E100000C-0000-4000-8000-00000000000C', 'E200000C-0000-4000-8000-00000000000C', NULL, 'CRM_OPORTUNIDADES', 'Oportunidades', 'Pipeline de ventas por etapa', 'trending_up', '/crm/oportunidades', NULL, 1, 'pantalla', 3, 1, 1, 1, 1),
('E30C0004-0000-4000-8000-000000000004', 'E100000C-0000-4000-8000-00000000000C', 'E200000C-0000-4000-8000-00000000000C', NULL, 'CRM_ACTIVIDADES', 'Actividades', 'Llamadas, emails, reuniones', 'event', '/crm/actividades', NULL, 1, 'pantalla', 4, 1, 1, 1, 1),
('E30D0001-0000-4000-8000-000000000001', 'E100000D-0000-4000-8000-00000000000D', 'E200000D-0000-4000-8000-00000000000D', NULL, 'PRC_LISTAS', 'Listas de Precios', 'Listas por cliente, canal, región', 'attach_money', '/prc/listas-precios', NULL, 1, 'pantalla', 1, 1, 1, 1, 1),
('E30D0002-0000-4000-8000-000000000002', 'E100000D-0000-4000-8000-00000000000D', 'E200000D-0000-4000-8000-00000000000D', NULL, 'PRC_PROMOCIONES', 'Promociones', 'Descuentos, 2x1, vigencia', 'local_offer', '/prc/promociones', NULL, 1, 'pantalla', 2, 1, 1, 1, 1),
('E30E0001-0000-4000-8000-000000000001', 'E100000E-0000-4000-8000-00000000000E', 'E200000E-0000-4000-8000-00000000000E', NULL, 'INV_BILL_SERIES', 'Series de Comprobantes', 'F001, B001, NC01, ND01', 'tag', '/facturacion/series', NULL, 1, 'pantalla', 1, 1, 1, 1, 1),
('E30E0002-0000-4000-8000-000000000002', 'E100000E-0000-4000-8000-00000000000E', 'E200000E-0000-4000-8000-00000000000E', NULL, 'INV_BILL_COMPROBANTES', 'Comprobantes', 'Facturas, boletas, NC, ND', 'receipt', '/facturacion/comprobantes', NULL, 1, 'pantalla', 2, 1, 1, 1, 1),
('E30E0003-0000-4000-8000-000000000003', 'E100000E-0000-4000-8000-00000000000E', 'E200000E-0000-4000-8000-00000000000E', NULL, 'INV_BILL_REGISTRO', 'Registro de Ventas', 'Libro de ventas automático', 'book', '/facturacion/registro-ventas', NULL, 1, 'pantalla', 3, 1, 1, 1, 1),
('E30F0001-0000-4000-8000-000000000001', 'E100000F-0000-4000-8000-00000000000F', 'E200000F-0000-4000-8000-00000000000F', NULL, 'POS_PUNTOS', 'Puntos de Venta', 'Configurar terminales/cajas', 'storefront', '/pos/puntos-venta', NULL, 1, 'pantalla', 1, 1, 1, 1, 1),
('E30F0002-0000-4000-8000-000000000002', 'E100000F-0000-4000-8000-00000000000F', 'E200000F-0000-4000-8000-00000000000F', NULL, 'POS_TURNOS', 'Turnos de Caja', 'Apertura con fondo inicial', 'schedule', '/pos/turnos-caja', NULL, 1, 'pantalla', 2, 1, 1, 1, 1),
('E30F0003-0000-4000-8000-000000000003', 'E100000F-0000-4000-8000-00000000000F', 'E200000F-0000-4000-8000-00000000000F', NULL, 'POS_VENTAS', 'Ventas Rápidas', 'Interfaz ágil con búsqueda de productos', 'point_of_sale', '/pos/ventas', NULL, 1, 'pantalla', 3, 1, 1, 1, 1);

-- ----- HCM (7), FIN (5), TAX (1), BDG (2), CST (3), PM (2), SVC (3), TKT (1), BI (2), DMS (2), WFL (2), AUD (2) -----
INSERT INTO modulo_menu (menu_id, modulo_id, seccion_id, cliente_id, codigo, nombre, descripcion, icono, ruta, menu_padre_id, nivel, tipo_menu, orden, requiere_autenticacion, es_visible, es_menu_sistema, es_activo) VALUES
('E3100001-0000-4000-8000-000000000001', 'E1000010-0000-4000-8000-000000000010', 'E2000010-0000-4000-8000-000000000010', NULL, 'HCM_EMPLEADOS', 'Empleados', 'Datos personales, AFP/ONP, cuenta bancaria', 'people', '/hcm/empleados', NULL, 1, 'pantalla', 1, 1, 1, 1, 1),
('E3100002-0000-4000-8000-000000000002', 'E1000010-0000-4000-8000-000000000010', 'E2000010-0000-4000-8000-000000000010', NULL, 'HCM_CONTRATOS', 'Contratos', 'Plazo fijo, indeterminado, part-time', 'description', '/hcm/contratos', NULL, 1, 'pantalla', 2, 1, 1, 1, 1),
('E3100003-0000-4000-8000-000000000003', 'E1000010-0000-4000-8000-000000000010', 'E2000010-0000-4000-8000-000000000010', NULL, 'HCM_CONCEPTOS', 'Conceptos de Planilla', 'Ingresos, descuentos, aportes', 'list_alt', '/hcm/conceptos-planilla', NULL, 1, 'pantalla', 3, 1, 1, 1, 1),
('E3100004-0000-4000-8000-000000000004', 'E1000010-0000-4000-8000-000000000010', 'E2000010-0000-4000-8000-000000000010', NULL, 'HCM_PLANILLAS', 'Planillas', 'Generar planilla mensual, gratificación, CTS', 'receipt', '/hcm/planillas', NULL, 1, 'pantalla', 4, 1, 1, 1, 1),
('E3100005-0000-4000-8000-000000000005', 'E1000010-0000-4000-8000-000000000010', 'E2000010-0000-4000-8000-000000000010', NULL, 'HCM_ASISTENCIA', 'Asistencia', 'Marcaciones de entrada/salida', 'schedule', '/hcm/asistencia', NULL, 1, 'pantalla', 5, 1, 1, 1, 1),
('E3100006-0000-4000-8000-000000000006', 'E1000010-0000-4000-8000-000000000010', 'E2000010-0000-4000-8000-000000000010', NULL, 'HCM_VACACIONES', 'Vacaciones', 'Días ganados/tomados/pendientes', 'beach_access', '/hcm/vacaciones', NULL, 1, 'pantalla', 6, 1, 1, 1, 1),
('E3100007-0000-4000-8000-000000000007', 'E1000010-0000-4000-8000-000000000010', 'E2000010-0000-4000-8000-000000000010', NULL, 'HCM_PRESTAMOS', 'Préstamos', 'Adelantos y préstamos con descuento en planilla', 'money', '/hcm/prestamos', NULL, 1, 'pantalla', 7, 1, 1, 1, 1),
('E3110001-0000-4000-8000-000000000001', 'E1000011-0000-4000-8000-000000000011', 'E2000011-0000-4000-8000-000000000011', NULL, 'FIN_PLAN_CUENTAS', 'Plan de Cuentas', 'PCGE Perú o plan personalizado', 'account_tree', '/fin/plan-cuentas', NULL, 1, 'pantalla', 1, 1, 1, 1, 1),
('E3110002-0000-4000-8000-000000000002', 'E1000011-0000-4000-8000-000000000011', 'E2000011-0000-4000-8000-000000000011', NULL, 'FIN_PERIODOS', 'Periodos Contables', 'Apertura y cierre de meses/años', 'calendar_today', '/fin/periodos', NULL, 1, 'pantalla', 2, 1, 1, 1, 1),
('E3110003-0000-4000-8000-000000000003', 'E1000011-0000-4000-8000-000000000011', 'E2000011-0000-4000-8000-000000000011', NULL, 'FIN_ASIENTOS', 'Asientos Contables', 'Registro manual o automático', 'edit_note', '/fin/asientos', NULL, 1, 'pantalla', 3, 1, 1, 1, 1),
('E3110004-0000-4000-8000-000000000004', 'E1000011-0000-4000-8000-000000000011', 'E2000011-0000-4000-8000-000000000011', NULL, 'FIN_MAYORES', 'Libros Mayores', 'Libro mayor por cuenta', 'menu_book', '/fin/libros-mayores', NULL, 1, 'pantalla', 4, 1, 1, 1, 1),
('E3110005-0000-4000-8000-000000000005', 'E1000011-0000-4000-8000-000000000011', 'E2000011-0000-4000-8000-000000000011', NULL, 'FIN_ESTADOS', 'Estados Financieros', 'Balance general, estado de resultados', 'bar_chart', '/fin/estados-financieros', NULL, 1, 'pantalla', 5, 1, 1, 1, 1),
('E3120001-0000-4000-8000-000000000001', 'E1000012-0000-4000-8000-000000000012', 'E2000012-0000-4000-8000-000000000012', NULL, 'TAX_PLE', 'PLE SUNAT', 'Generar TXT automático para SUNAT', 'description', '/tax/ple', NULL, 1, 'pantalla', 1, 1, 1, 1, 1),
('E3130001-0000-4000-8000-000000000001', 'E1000013-0000-4000-8000-000000000013', 'E2000013-0000-4000-8000-000000000013', NULL, 'BDG_PRESUPUESTOS', 'Presupuestos', 'Presupuesto anual por cuenta y centro de costo', 'savings', '/bdg/presupuestos', NULL, 1, 'pantalla', 1, 1, 1, 1, 1),
('E3130002-0000-4000-8000-000000000002', 'E1000013-0000-4000-8000-000000000013', 'E2000013-0000-4000-8000-000000000013', NULL, 'BDG_EJECUCION', 'Ejecución Presupuestal', 'Comparar real vs presupuestado', 'assessment', '/bdg/ejecucion', NULL, 1, 'pantalla', 2, 1, 1, 1, 1),
('E3140001-0000-4000-8000-000000000001', 'E1000014-0000-4000-8000-000000000014', 'E2000014-0000-4000-8000-000000000014', NULL, 'CST_TIPOS_CC', 'Tipos de Centro de Costo', 'Clasificar centros productivos y no productivos', 'category', '/cst/tipos-cc', NULL, 1, 'pantalla', 1, 1, 1, 1, 1),
('E3140002-0000-4000-8000-000000000002', 'E1000014-0000-4000-8000-000000000014', 'E2000014-0000-4000-8000-000000000014', NULL, 'CST_COSTO', 'Costo de Productos', 'Costo estándar vs real', 'analytics', '/cst/costo-productos', NULL, 1, 'pantalla', 2, 1, 1, 1, 1),
('E3140003-0000-4000-8000-000000000003', 'E1000014-0000-4000-8000-000000000014', 'E2000014-0000-4000-8000-000000000014', NULL, 'CST_VARIACIONES', 'Análisis de Variaciones', 'Variación real vs estándar', 'trending_down', '/cst/variaciones', NULL, 1, 'pantalla', 3, 1, 1, 1, 1),
('E3150001-0000-4000-8000-000000000001', 'E1000015-0000-4000-8000-000000000015', 'E2000015-0000-4000-8000-000000000015', NULL, 'PM_PROYECTOS', 'Proyectos', 'Crear proyectos con presupuesto asignado', 'folder', '/pm/proyectos', NULL, 1, 'pantalla', 1, 1, 1, 1, 1),
('E3150002-0000-4000-8000-000000000002', 'E1000015-0000-4000-8000-000000000015', 'E2000015-0000-4000-8000-000000000015', NULL, 'PM_SEGUIMIENTO', 'Seguimiento', 'Presupuesto vs costo real, % avance', 'trending_up', '/pm/seguimiento', NULL, 1, 'pantalla', 2, 1, 1, 1, 1),
('E3160001-0000-4000-8000-000000000001', 'E1000016-0000-4000-8000-000000000016', 'E2000016-0000-4000-8000-000000000016', NULL, 'SVC_OS', 'Órdenes de Servicio', 'Servicios internos y externos', 'build_circle', '/svc/ordenes-servicio', NULL, 1, 'pantalla', 1, 1, 1, 1, 1),
('E3160002-0000-4000-8000-000000000002', 'E1000016-0000-4000-8000-000000000016', 'E2000016-0000-4000-8000-000000000016', NULL, 'SVC_ENVIO', 'Envío a Talleres', 'Materiales enviados a proveedores externos', 'send', '/svc/envio-talleres', NULL, 1, 'pantalla', 2, 1, 1, 1, 1),
('E3160003-0000-4000-8000-000000000003', 'E1000016-0000-4000-8000-000000000016', 'E2000016-0000-4000-8000-000000000016', NULL, 'SVC_STOCK_TERCEROS', 'Stock en Terceros', 'Material en poder de talleres', 'inventory', '/svc/stock-terceros', NULL, 1, 'pantalla', 3, 1, 1, 1, 1),
('E3170001-0000-4000-8000-000000000001', 'E1000017-0000-4000-8000-000000000017', 'E2000017-0000-4000-8000-000000000017', NULL, 'TKT_TICKETS', 'Tickets', 'Tickets de soporte interno, prioridad, SLA', 'confirmation_number', '/tkt/tickets', NULL, 1, 'pantalla', 1, 1, 1, 1, 1),
('E3180001-0000-4000-8000-000000000001', 'E1000018-0000-4000-8000-000000000018', 'E2000018-0000-4000-8000-000000000018', NULL, 'BI_REPORTES', 'Reportes Configurables', 'Reportes personalizados con SQL', 'assessment', '/bi/reportes', NULL, 1, 'pantalla', 1, 1, 1, 1, 1),
('E3180002-0000-4000-8000-000000000002', 'E1000018-0000-4000-8000-000000000018', 'E2000018-0000-4000-8000-000000000018', NULL, 'BI_DASHBOARDS', 'Dashboards', 'KPIs y gráficos interactivos', 'dashboard', '/bi/dashboards', NULL, 1, 'pantalla', 2, 1, 1, 1, 1),
('E3190001-0000-4000-8000-000000000001', 'E1000019-0000-4000-8000-000000000019', 'E2000019-0000-4000-8000-000000000019', NULL, 'DMS_DOCUMENTOS', 'Documentos', 'Subir PDFs, Word, Excel, versionamiento', 'folder_open', '/dms/documentos', NULL, 1, 'pantalla', 1, 1, 1, 1, 1),
('E3190002-0000-4000-8000-000000000002', 'E1000019-0000-4000-8000-000000000019', 'E2000019-0000-4000-8000-000000000019', NULL, 'DMS_BUSQUEDA', 'Búsqueda', 'Buscar por nombre, tipo, fecha, etiquetas', 'search', '/dms/busqueda', NULL, 1, 'pantalla', 2, 1, 1, 1, 1),
('E31A0001-0000-4000-8000-000000000001', 'E100001A-0000-4000-8000-00000000001A', 'E200001A-0000-4000-8000-00000000001A', NULL, 'WFL_WORKFLOWS', 'Workflows', 'Flujos de aprobación personalizados', 'account_tree', '/wfl/workflows', NULL, 1, 'pantalla', 1, 1, 1, 1, 1),
('E31A0002-0000-4000-8000-000000000002', 'E100001A-0000-4000-8000-00000000001A', 'E200001A-0000-4000-8000-00000000001A', NULL, 'WFL_SEGUIMIENTO', 'Seguimiento', 'Estado de aprobaciones pendientes', 'pending_actions', '/wfl/seguimiento', NULL, 1, 'pantalla', 2, 1, 1, 1, 1),
('E31B0001-0000-4000-8000-000000000001', 'E100001B-0000-4000-8000-00000000001B', 'E200001B-0000-4000-8000-00000000001B', NULL, 'AUD_LOG', 'Log de Auditoría', 'Registro de todos los cambios', 'history', '/aud/log', NULL, 1, 'pantalla', 1, 1, 1, 1, 1),
('E31B0002-0000-4000-8000-000000000002', 'E100001B-0000-4000-8000-00000000001B', 'E200001B-0000-4000-8000-00000000001B', NULL, 'AUD_TRAZABILIDAD', 'Reportes de Trazabilidad', 'Rastrear cambios en documentos críticos', 'track_changes', '/aud/trazabilidad', NULL, 1, 'pantalla', 2, 1, 1, 1, 1);

PRINT 'Seed modulo, modulo_seccion y modulo_menu completado.';
GO
