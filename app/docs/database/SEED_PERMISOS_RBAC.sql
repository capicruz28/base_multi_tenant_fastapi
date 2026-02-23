-- ============================================================================
-- SCRIPT: SEED catálogo de permisos RBAC (tabla permiso)
-- DESCRIPCIÓN: Inserta permisos de negocio (modulo.recurso.accion) para los 27 módulos.
-- DEPENDENCIAS: Ejecutar después de SCRIPT_RBAC_TABLAS_CENTRAL.sql y SEED_MODULO_MENU_COMPLETO.sql (tabla modulo).
-- COHERENCIA: Los modulo_id deben coincidir con los de SEED_MODULO_MENU_COMPLETO.sql (INSERT INTO modulo ...).
-- USO: Ejecutar UNA SOLA VEZ en BD central. No asigna permisos a roles (Fase 1).
-- NO ROMPE: MERGE por codigo; si ya existe no inserta.
-- ============================================================================
-- Convención: modulo.recurso.accion (minúsculas). permiso.modulo_id = modulo.modulo_id del mismo módulo.
-- Admin y modulos: modulo_id NULL (no pertenecen a un módulo ERP).
--
-- Referencia modulo_id (de SEED_MODULO_MENU_COMPLETO):
--   ORG     E1000001-...001  INV E1000002-...002  WMS E1000003-...003  QMS E1000004-...004  PUR E1000005-...005
--   LOG     E1000006-...006  MFG E1000007-...007  MRP E1000008-...008  MPS E1000009-...009  MNT E100000A-...00A
--   SLS     E100000B-...00B  CRM E100000C-...00C  PRC E100000D-...00D  INV_BILL E100000E-...00E  POS E100000F-...00F
--   HCM     E1000010-...010  FIN E1000011-...011  TAX E1000012-...012  BDG E1000013-...013  CST E1000014-...014
--   PM      E1000015-...015  SVC E1000016-...016  TKT E1000017-...017  BI  E1000018-...018  DMS E1000019-...019
--   WFL     E100001A-...01A  AUD E100001B-...01B
-- ============================================================================

-- Admin: usuarios y roles (modulo_id NULL)
MERGE INTO permiso AS t
USING (SELECT 'admin.usuario.leer' AS codigo, 'Leer usuarios' AS nombre, 'Listar y ver usuarios' AS descripcion, NULL AS modulo_id, 'usuario' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'admin.usuario.crear', 'Crear usuarios', 'Crear nuevos usuarios', NULL, 'usuario', 'crear' UNION ALL
       SELECT 'admin.usuario.actualizar', 'Actualizar usuarios', 'Editar usuarios', NULL, 'usuario', 'actualizar' UNION ALL
       SELECT 'admin.usuario.eliminar', 'Eliminar usuarios', 'Dar de baja usuarios', NULL, 'usuario', 'eliminar' UNION ALL
       SELECT 'admin.rol.leer', 'Leer roles', 'Listar y ver roles', NULL, 'rol', 'leer' UNION ALL
       SELECT 'admin.rol.crear', 'Crear roles', 'Crear roles y asignar permisos', NULL, 'rol', 'crear' UNION ALL
       SELECT 'admin.rol.actualizar', 'Actualizar roles', 'Editar roles', NULL, 'rol', 'actualizar' UNION ALL
       SELECT 'admin.rol.eliminar', 'Eliminar roles', 'Eliminar roles', NULL, 'rol', 'eliminar' UNION ALL
       SELECT 'admin.rol.asignar', 'Asignar roles', 'Asignar roles a usuarios', NULL, 'rol', 'asignar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- Módulos y menú (catálogo central, modulo_id NULL)
MERGE INTO permiso AS t
USING (SELECT 'modulos.menu.leer' AS codigo, 'Ver menú' AS nombre, 'Ver opciones de menú según permisos' AS descripcion, NULL AS modulo_id, 'menu' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'modulos.menu.administrar', 'Administrar menú', 'Gestionar menús (SuperAdmin)', NULL, 'menu', 'administrar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- ORG (Organización) - modulo_id de SEED_MODULO_MENU_COMPLETO
MERGE INTO permiso AS t
USING (SELECT 'org.area.leer' AS codigo, 'Leer organización' AS nombre, 'Ver empresas, sucursales, áreas' AS descripcion, CAST('E1000001-0000-4000-8000-000000000001' AS UNIQUEIDENTIFIER) AS modulo_id, 'area' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'org.area.crear', 'Crear en organización', 'Crear sucursales, departamentos, cargos', CAST('E1000001-0000-4000-8000-000000000001' AS UNIQUEIDENTIFIER), 'area', 'crear' UNION ALL
       SELECT 'org.area.actualizar', 'Actualizar organización', 'Editar datos organizacionales', CAST('E1000001-0000-4000-8000-000000000001' AS UNIQUEIDENTIFIER), 'area', 'actualizar' UNION ALL
       SELECT 'org.area.eliminar', 'Eliminar en organización', 'Dar de baja ítems organizacionales', CAST('E1000001-0000-4000-8000-000000000001' AS UNIQUEIDENTIFIER), 'area', 'eliminar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- INV (Inventarios)
MERGE INTO permiso AS t
USING (SELECT 'inv.producto.leer' AS codigo, 'Leer productos' AS nombre, 'Listar y ver productos, categorías, stock' AS descripcion, CAST('E1000002-0000-4000-8000-000000000002' AS UNIQUEIDENTIFIER) AS modulo_id, 'producto' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'inv.producto.crear', 'Crear productos', 'Crear productos y categorías', CAST('E1000002-0000-4000-8000-000000000002' AS UNIQUEIDENTIFIER), 'producto', 'crear' UNION ALL
       SELECT 'inv.producto.actualizar', 'Actualizar productos', 'Editar productos e inventario', CAST('E1000002-0000-4000-8000-000000000002' AS UNIQUEIDENTIFIER), 'producto', 'actualizar' UNION ALL
       SELECT 'inv.producto.eliminar', 'Eliminar productos', 'Dar de baja productos', CAST('E1000002-0000-4000-8000-000000000002' AS UNIQUEIDENTIFIER), 'producto', 'eliminar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- WMS (Gestión de Almacenes)
MERGE INTO permiso AS t
USING (SELECT 'wms.almacen.leer' AS codigo, 'Leer almacenes' AS nombre, NULL AS descripcion, CAST('E1000003-0000-4000-8000-000000000003' AS UNIQUEIDENTIFIER) AS modulo_id, 'almacen' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'wms.almacen.crear', 'Crear en WMS', NULL, CAST('E1000003-0000-4000-8000-000000000003' AS UNIQUEIDENTIFIER), 'almacen', 'crear' UNION ALL
       SELECT 'wms.almacen.actualizar', 'Actualizar WMS', NULL, CAST('E1000003-0000-4000-8000-000000000003' AS UNIQUEIDENTIFIER), 'almacen', 'actualizar' UNION ALL
       SELECT 'wms.almacen.eliminar', 'Eliminar en WMS', NULL, CAST('E1000003-0000-4000-8000-000000000003' AS UNIQUEIDENTIFIER), 'almacen', 'eliminar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- QMS (Control de Calidad)
MERGE INTO permiso AS t
USING (SELECT 'qms.inspeccion.leer' AS codigo, 'Leer inspecciones' AS nombre, NULL AS descripcion, CAST('E1000004-0000-4000-8000-000000000004' AS UNIQUEIDENTIFIER) AS modulo_id, 'inspeccion' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'qms.inspeccion.crear', 'Crear inspecciones', NULL, CAST('E1000004-0000-4000-8000-000000000004' AS UNIQUEIDENTIFIER), 'inspeccion', 'crear' UNION ALL
       SELECT 'qms.inspeccion.actualizar', 'Actualizar inspecciones', NULL, CAST('E1000004-0000-4000-8000-000000000004' AS UNIQUEIDENTIFIER), 'inspeccion', 'actualizar' UNION ALL
       SELECT 'qms.inspeccion.eliminar', 'Eliminar inspecciones', NULL, CAST('E1000004-0000-4000-8000-000000000004' AS UNIQUEIDENTIFIER), 'inspeccion', 'eliminar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- PUR (Compras)
MERGE INTO permiso AS t
USING (SELECT 'pur.orden_compra.leer' AS codigo, 'Leer compras' AS nombre, NULL AS descripcion, CAST('E1000005-0000-4000-8000-000000000005' AS UNIQUEIDENTIFIER) AS modulo_id, 'orden_compra' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'pur.orden_compra.crear', 'Crear órdenes de compra', NULL, CAST('E1000005-0000-4000-8000-000000000005' AS UNIQUEIDENTIFIER), 'orden_compra', 'crear' UNION ALL
       SELECT 'pur.orden_compra.actualizar', 'Actualizar compras', NULL, CAST('E1000005-0000-4000-8000-000000000005' AS UNIQUEIDENTIFIER), 'orden_compra', 'actualizar' UNION ALL
       SELECT 'pur.orden_compra.eliminar', 'Eliminar órdenes de compra', NULL, CAST('E1000005-0000-4000-8000-000000000005' AS UNIQUEIDENTIFIER), 'orden_compra', 'eliminar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- LOG (Logística y Distribución)
MERGE INTO permiso AS t
USING (SELECT 'log.ruta.leer' AS codigo, 'Leer logística' AS nombre, NULL AS descripcion, CAST('E1000006-0000-4000-8000-000000000006' AS UNIQUEIDENTIFIER) AS modulo_id, 'ruta' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'log.ruta.crear', 'Crear rutas y despachos', NULL, CAST('E1000006-0000-4000-8000-000000000006' AS UNIQUEIDENTIFIER), 'ruta', 'crear' UNION ALL
       SELECT 'log.ruta.actualizar', 'Actualizar logística', NULL, CAST('E1000006-0000-4000-8000-000000000006' AS UNIQUEIDENTIFIER), 'ruta', 'actualizar' UNION ALL
       SELECT 'log.ruta.eliminar', 'Eliminar en logística', NULL, CAST('E1000006-0000-4000-8000-000000000006' AS UNIQUEIDENTIFIER), 'ruta', 'eliminar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- MFG (Producción)
MERGE INTO permiso AS t
USING (SELECT 'mfg.orden_produccion.leer' AS codigo, 'Leer órdenes de producción' AS nombre, NULL AS descripcion, CAST('E1000007-0000-4000-8000-000000000007' AS UNIQUEIDENTIFIER) AS modulo_id, 'orden_produccion' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'mfg.orden_produccion.crear', 'Crear órdenes de producción', NULL, CAST('E1000007-0000-4000-8000-000000000007' AS UNIQUEIDENTIFIER), 'orden_produccion', 'crear' UNION ALL
       SELECT 'mfg.orden_produccion.actualizar', 'Actualizar órdenes de producción', NULL, CAST('E1000007-0000-4000-8000-000000000007' AS UNIQUEIDENTIFIER), 'orden_produccion', 'actualizar' UNION ALL
       SELECT 'mfg.orden_produccion.eliminar', 'Eliminar órdenes de producción', NULL, CAST('E1000007-0000-4000-8000-000000000007' AS UNIQUEIDENTIFIER), 'orden_produccion', 'eliminar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- MRP (Planeamiento de Materiales)
MERGE INTO permiso AS t
USING (SELECT 'mrp.plan_materiales.leer' AS codigo, 'Leer plan de materiales' AS nombre, NULL AS descripcion, CAST('E1000008-0000-4000-8000-000000000008' AS UNIQUEIDENTIFIER) AS modulo_id, 'plan_materiales' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'mrp.plan_materiales.crear', 'Crear plan MRP', NULL, CAST('E1000008-0000-4000-8000-000000000008' AS UNIQUEIDENTIFIER), 'plan_materiales', 'crear' UNION ALL
       SELECT 'mrp.plan_materiales.actualizar', 'Actualizar plan de materiales', NULL, CAST('E1000008-0000-4000-8000-000000000008' AS UNIQUEIDENTIFIER), 'plan_materiales', 'actualizar' UNION ALL
       SELECT 'mrp.plan_materiales.eliminar', 'Eliminar plan MRP', NULL, CAST('E1000008-0000-4000-8000-000000000008' AS UNIQUEIDENTIFIER), 'plan_materiales', 'eliminar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- MPS (Plan Maestro de Producción)
MERGE INTO permiso AS t
USING (SELECT 'mps.plan_maestro.leer' AS codigo, 'Leer plan maestro' AS nombre, NULL AS descripcion, CAST('E1000009-0000-4000-8000-000000000009' AS UNIQUEIDENTIFIER) AS modulo_id, 'plan_maestro' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'mps.plan_maestro.crear', 'Crear plan maestro', NULL, CAST('E1000009-0000-4000-8000-000000000009' AS UNIQUEIDENTIFIER), 'plan_maestro', 'crear' UNION ALL
       SELECT 'mps.plan_maestro.actualizar', 'Actualizar plan maestro', NULL, CAST('E1000009-0000-4000-8000-000000000009' AS UNIQUEIDENTIFIER), 'plan_maestro', 'actualizar' UNION ALL
       SELECT 'mps.plan_maestro.eliminar', 'Eliminar plan maestro', NULL, CAST('E1000009-0000-4000-8000-000000000009' AS UNIQUEIDENTIFIER), 'plan_maestro', 'eliminar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- MNT (Mantenimiento)
MERGE INTO permiso AS t
USING (SELECT 'mnt.activo.leer' AS codigo, 'Leer activos' AS nombre, NULL AS descripcion, CAST('E100000A-0000-4000-8000-00000000000A' AS UNIQUEIDENTIFIER) AS modulo_id, 'activo' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'mnt.activo.crear', 'Crear activos', NULL, CAST('E100000A-0000-4000-8000-00000000000A' AS UNIQUEIDENTIFIER), 'activo', 'crear' UNION ALL
       SELECT 'mnt.activo.actualizar', 'Actualizar activos', NULL, CAST('E100000A-0000-4000-8000-00000000000A' AS UNIQUEIDENTIFIER), 'activo', 'actualizar' UNION ALL
       SELECT 'mnt.orden_trabajo.leer', 'Leer órdenes de trabajo', NULL, CAST('E100000A-0000-4000-8000-00000000000A' AS UNIQUEIDENTIFIER), 'orden_trabajo', 'leer' UNION ALL
       SELECT 'mnt.orden_trabajo.crear', 'Crear órdenes de trabajo', NULL, CAST('E100000A-0000-4000-8000-00000000000A' AS UNIQUEIDENTIFIER), 'orden_trabajo', 'crear') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- SLS (Ventas)
MERGE INTO permiso AS t
USING (SELECT 'sls.venta.leer' AS codigo, 'Leer ventas' AS nombre, NULL AS descripcion, CAST('E100000B-0000-4000-8000-00000000000B' AS UNIQUEIDENTIFIER) AS modulo_id, 'venta' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'sls.venta.crear', 'Crear pedidos y ventas', NULL, CAST('E100000B-0000-4000-8000-00000000000B' AS UNIQUEIDENTIFIER), 'venta', 'crear' UNION ALL
       SELECT 'sls.venta.actualizar', 'Actualizar ventas', NULL, CAST('E100000B-0000-4000-8000-00000000000B' AS UNIQUEIDENTIFIER), 'venta', 'actualizar' UNION ALL
       SELECT 'sls.venta.eliminar', 'Eliminar ventas', NULL, CAST('E100000B-0000-4000-8000-00000000000B' AS UNIQUEIDENTIFIER), 'venta', 'eliminar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- CRM (Gestión de Clientes)
MERGE INTO permiso AS t
USING (SELECT 'crm.oportunidad.leer' AS codigo, 'Leer CRM' AS nombre, NULL AS descripcion, CAST('E100000C-0000-4000-8000-00000000000C' AS UNIQUEIDENTIFIER) AS modulo_id, 'oportunidad' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'crm.oportunidad.crear', 'Crear oportunidades', NULL, CAST('E100000C-0000-4000-8000-00000000000C' AS UNIQUEIDENTIFIER), 'oportunidad', 'crear' UNION ALL
       SELECT 'crm.oportunidad.actualizar', 'Actualizar CRM', NULL, CAST('E100000C-0000-4000-8000-00000000000C' AS UNIQUEIDENTIFIER), 'oportunidad', 'actualizar' UNION ALL
       SELECT 'crm.oportunidad.eliminar', 'Eliminar en CRM', NULL, CAST('E100000C-0000-4000-8000-00000000000C' AS UNIQUEIDENTIFIER), 'oportunidad', 'eliminar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- PRC (Precios y Promociones)
MERGE INTO permiso AS t
USING (SELECT 'prc.precio.leer' AS codigo, 'Leer precios' AS nombre, NULL AS descripcion, CAST('E100000D-0000-4000-8000-00000000000D' AS UNIQUEIDENTIFIER) AS modulo_id, 'precio' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'prc.precio.crear', 'Crear listas y promociones', NULL, CAST('E100000D-0000-4000-8000-00000000000D' AS UNIQUEIDENTIFIER), 'precio', 'crear' UNION ALL
       SELECT 'prc.precio.actualizar', 'Actualizar precios', NULL, CAST('E100000D-0000-4000-8000-00000000000D' AS UNIQUEIDENTIFIER), 'precio', 'actualizar' UNION ALL
       SELECT 'prc.precio.eliminar', 'Eliminar precios/promociones', NULL, CAST('E100000D-0000-4000-8000-00000000000D' AS UNIQUEIDENTIFIER), 'precio', 'eliminar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- INV_BILL (Facturación Electrónica)
MERGE INTO permiso AS t
USING (SELECT 'inv_bill.comprobante.leer' AS codigo, 'Leer comprobantes' AS nombre, NULL AS descripcion, CAST('E100000E-0000-4000-8000-00000000000E' AS UNIQUEIDENTIFIER) AS modulo_id, 'comprobante' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'inv_bill.comprobante.crear', 'Crear comprobantes electrónicos', NULL, CAST('E100000E-0000-4000-8000-00000000000E' AS UNIQUEIDENTIFIER), 'comprobante', 'crear' UNION ALL
       SELECT 'inv_bill.comprobante.actualizar', 'Actualizar comprobantes', NULL, CAST('E100000E-0000-4000-8000-00000000000E' AS UNIQUEIDENTIFIER), 'comprobante', 'actualizar' UNION ALL
       SELECT 'inv_bill.comprobante.eliminar', 'Eliminar comprobantes', NULL, CAST('E100000E-0000-4000-8000-00000000000E' AS UNIQUEIDENTIFIER), 'comprobante', 'eliminar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- POS (Punto de Venta)
MERGE INTO permiso AS t
USING (SELECT 'pos.venta.leer' AS codigo, 'Leer punto de venta' AS nombre, NULL AS descripcion, CAST('E100000F-0000-4000-8000-00000000000F' AS UNIQUEIDENTIFIER) AS modulo_id, 'venta' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'pos.venta.crear', 'Registrar ventas POS', NULL, CAST('E100000F-0000-4000-8000-00000000000F' AS UNIQUEIDENTIFIER), 'venta', 'crear' UNION ALL
       SELECT 'pos.venta.actualizar', 'Actualizar ventas POS', NULL, CAST('E100000F-0000-4000-8000-00000000000F' AS UNIQUEIDENTIFIER), 'venta', 'actualizar' UNION ALL
       SELECT 'pos.venta.eliminar', 'Anular ventas POS', NULL, CAST('E100000F-0000-4000-8000-00000000000F' AS UNIQUEIDENTIFIER), 'venta', 'eliminar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- HCM (Planillas y RRHH)
MERGE INTO permiso AS t
USING (SELECT 'hcm.empleado.leer' AS codigo, 'Leer empleados' AS nombre, NULL AS descripcion, CAST('E1000010-0000-4000-8000-000000000010' AS UNIQUEIDENTIFIER) AS modulo_id, 'empleado' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'hcm.empleado.crear', 'Crear empleados', NULL, CAST('E1000010-0000-4000-8000-000000000010' AS UNIQUEIDENTIFIER), 'empleado', 'crear' UNION ALL
       SELECT 'hcm.empleado.actualizar', 'Actualizar empleados', NULL, CAST('E1000010-0000-4000-8000-000000000010' AS UNIQUEIDENTIFIER), 'empleado', 'actualizar' UNION ALL
       SELECT 'hcm.empleado.eliminar', 'Eliminar empleados', NULL, CAST('E1000010-0000-4000-8000-000000000010' AS UNIQUEIDENTIFIER), 'empleado', 'eliminar' UNION ALL
       SELECT 'hcm.planilla.leer', 'Leer planillas', NULL, CAST('E1000010-0000-4000-8000-000000000010' AS UNIQUEIDENTIFIER), 'planilla', 'leer' UNION ALL
       SELECT 'hcm.planilla.crear', 'Procesar planillas', NULL, CAST('E1000010-0000-4000-8000-000000000010' AS UNIQUEIDENTIFIER), 'planilla', 'crear') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- FIN (Finanzas y Contabilidad)
MERGE INTO permiso AS t
USING (SELECT 'fin.asiento.leer' AS codigo, 'Leer contabilidad' AS nombre, NULL AS descripcion, CAST('E1000011-0000-4000-8000-000000000011' AS UNIQUEIDENTIFIER) AS modulo_id, 'asiento' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'fin.asiento.crear', 'Crear asientos', NULL, CAST('E1000011-0000-4000-8000-000000000011' AS UNIQUEIDENTIFIER), 'asiento', 'crear' UNION ALL
       SELECT 'fin.asiento.actualizar', 'Actualizar asientos', NULL, CAST('E1000011-0000-4000-8000-000000000011' AS UNIQUEIDENTIFIER), 'asiento', 'actualizar' UNION ALL
       SELECT 'fin.asiento.eliminar', 'Eliminar asientos', NULL, CAST('E1000011-0000-4000-8000-000000000011' AS UNIQUEIDENTIFIER), 'asiento', 'eliminar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- TAX (Libros electrónicos)
MERGE INTO permiso AS t
USING (SELECT 'tax.libro.leer' AS codigo, 'Leer libros electrónicos' AS nombre, NULL AS descripcion, CAST('E1000012-0000-4000-8000-000000000012' AS UNIQUEIDENTIFIER) AS modulo_id, 'libro' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'tax.libro.exportar', 'Exportar libros', NULL, CAST('E1000012-0000-4000-8000-000000000012' AS UNIQUEIDENTIFIER), 'libro', 'exportar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- BDG (Presupuestos)
MERGE INTO permiso AS t
USING (SELECT 'bdg.presupuesto.leer' AS codigo, 'Leer presupuestos' AS nombre, NULL AS descripcion, CAST('E1000013-0000-4000-8000-000000000013' AS UNIQUEIDENTIFIER) AS modulo_id, 'presupuesto' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'bdg.presupuesto.crear', 'Crear presupuestos', NULL, CAST('E1000013-0000-4000-8000-000000000013' AS UNIQUEIDENTIFIER), 'presupuesto', 'crear' UNION ALL
       SELECT 'bdg.presupuesto.actualizar', 'Actualizar presupuestos', NULL, CAST('E1000013-0000-4000-8000-000000000013' AS UNIQUEIDENTIFIER), 'presupuesto', 'actualizar' UNION ALL
       SELECT 'bdg.presupuesto.eliminar', 'Eliminar presupuestos', NULL, CAST('E1000013-0000-4000-8000-000000000013' AS UNIQUEIDENTIFIER), 'presupuesto', 'eliminar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- CST (Costeo de Productos)
MERGE INTO permiso AS t
USING (SELECT 'cst.costo.leer' AS codigo, 'Leer costos' AS nombre, NULL AS descripcion, CAST('E1000014-0000-4000-8000-000000000014' AS UNIQUEIDENTIFIER) AS modulo_id, 'costo' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'cst.costo.crear', 'Crear costeo', NULL, CAST('E1000014-0000-4000-8000-000000000014' AS UNIQUEIDENTIFIER), 'costo', 'crear' UNION ALL
       SELECT 'cst.costo.actualizar', 'Actualizar costos', NULL, CAST('E1000014-0000-4000-8000-000000000014' AS UNIQUEIDENTIFIER), 'costo', 'actualizar' UNION ALL
       SELECT 'cst.costo.eliminar', 'Eliminar costeo', NULL, CAST('E1000014-0000-4000-8000-000000000014' AS UNIQUEIDENTIFIER), 'costo', 'eliminar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- PM (Proyectos)
MERGE INTO permiso AS t
USING (SELECT 'pm.proyecto.leer' AS codigo, 'Leer proyectos' AS nombre, NULL AS descripcion, CAST('E1000015-0000-4000-8000-000000000015' AS UNIQUEIDENTIFIER) AS modulo_id, 'proyecto' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'pm.proyecto.crear', 'Crear proyectos', NULL, CAST('E1000015-0000-4000-8000-000000000015' AS UNIQUEIDENTIFIER), 'proyecto', 'crear' UNION ALL
       SELECT 'pm.proyecto.actualizar', 'Actualizar proyectos', NULL, CAST('E1000015-0000-4000-8000-000000000015' AS UNIQUEIDENTIFIER), 'proyecto', 'actualizar' UNION ALL
       SELECT 'pm.proyecto.eliminar', 'Eliminar proyectos', NULL, CAST('E1000015-0000-4000-8000-000000000015' AS UNIQUEIDENTIFIER), 'proyecto', 'eliminar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- SVC (Órdenes de servicio)
MERGE INTO permiso AS t
USING (SELECT 'svc.orden_servicio.leer' AS codigo, 'Leer órdenes de servicio' AS nombre, NULL AS descripcion, CAST('E1000016-0000-4000-8000-000000000016' AS UNIQUEIDENTIFIER) AS modulo_id, 'orden_servicio' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'svc.orden_servicio.crear', 'Crear órdenes de servicio', NULL, CAST('E1000016-0000-4000-8000-000000000016' AS UNIQUEIDENTIFIER), 'orden_servicio', 'crear' UNION ALL
       SELECT 'svc.orden_servicio.actualizar', 'Actualizar órdenes de servicio', NULL, CAST('E1000016-0000-4000-8000-000000000016' AS UNIQUEIDENTIFIER), 'orden_servicio', 'actualizar' UNION ALL
       SELECT 'svc.orden_servicio.eliminar', 'Eliminar órdenes de servicio', NULL, CAST('E1000016-0000-4000-8000-000000000016' AS UNIQUEIDENTIFIER), 'orden_servicio', 'eliminar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- TKT (Mesa de ayuda)
MERGE INTO permiso AS t
USING (SELECT 'tkt.ticket.leer' AS codigo, 'Leer tickets' AS nombre, NULL AS descripcion, CAST('E1000017-0000-4000-8000-000000000017' AS UNIQUEIDENTIFIER) AS modulo_id, 'ticket' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'tkt.ticket.crear', 'Crear tickets', NULL, CAST('E1000017-0000-4000-8000-000000000017' AS UNIQUEIDENTIFIER), 'ticket', 'crear' UNION ALL
       SELECT 'tkt.ticket.actualizar', 'Actualizar tickets', NULL, CAST('E1000017-0000-4000-8000-000000000017' AS UNIQUEIDENTIFIER), 'ticket', 'actualizar' UNION ALL
       SELECT 'tkt.ticket.eliminar', 'Eliminar tickets', NULL, CAST('E1000017-0000-4000-8000-000000000017' AS UNIQUEIDENTIFIER), 'ticket', 'eliminar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- BI (Reportes)
MERGE INTO permiso AS t
USING (SELECT 'bi.reporte.leer' AS codigo, 'Leer reportes' AS nombre, NULL AS descripcion, CAST('E1000018-0000-4000-8000-000000000018' AS UNIQUEIDENTIFIER) AS modulo_id, 'reporte' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'bi.reporte.crear', 'Crear reportes', NULL, CAST('E1000018-0000-4000-8000-000000000018' AS UNIQUEIDENTIFIER), 'reporte', 'crear' UNION ALL
       SELECT 'bi.reporte.exportar', 'Exportar reportes', NULL, CAST('E1000018-0000-4000-8000-000000000018' AS UNIQUEIDENTIFIER), 'reporte', 'exportar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- DMS (Documentos)
MERGE INTO permiso AS t
USING (SELECT 'dms.documento.leer' AS codigo, 'Leer documentos' AS nombre, NULL AS descripcion, CAST('E1000019-0000-4000-8000-000000000019' AS UNIQUEIDENTIFIER) AS modulo_id, 'documento' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'dms.documento.crear', 'Crear documentos', NULL, CAST('E1000019-0000-4000-8000-000000000019' AS UNIQUEIDENTIFIER), 'documento', 'crear' UNION ALL
       SELECT 'dms.documento.actualizar', 'Actualizar documentos', NULL, CAST('E1000019-0000-4000-8000-000000000019' AS UNIQUEIDENTIFIER), 'documento', 'actualizar' UNION ALL
       SELECT 'dms.documento.eliminar', 'Eliminar documentos', NULL, CAST('E1000019-0000-4000-8000-000000000019' AS UNIQUEIDENTIFIER), 'documento', 'eliminar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- WFL (Flujos de trabajo)
MERGE INTO permiso AS t
USING (SELECT 'wfl.flujo.leer' AS codigo, 'Leer flujos' AS nombre, NULL AS descripcion, CAST('E100001A-0000-4000-8000-00000000001A' AS UNIQUEIDENTIFIER) AS modulo_id, 'flujo' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'wfl.flujo.crear', 'Crear flujos', NULL, CAST('E100001A-0000-4000-8000-00000000001A' AS UNIQUEIDENTIFIER), 'flujo', 'crear' UNION ALL
       SELECT 'wfl.flujo.actualizar', 'Actualizar flujos', NULL, CAST('E100001A-0000-4000-8000-00000000001A' AS UNIQUEIDENTIFIER), 'flujo', 'actualizar' UNION ALL
       SELECT 'wfl.flujo.eliminar', 'Eliminar flujos', NULL, CAST('E100001A-0000-4000-8000-00000000001A' AS UNIQUEIDENTIFIER), 'flujo', 'eliminar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- AUD (Auditoría)
MERGE INTO permiso AS t
USING (SELECT 'aud.log.leer' AS codigo, 'Leer log de auditoría' AS nombre, NULL AS descripcion, CAST('E100001B-0000-4000-8000-00000000001B' AS UNIQUEIDENTIFIER) AS modulo_id, 'log' AS recurso, 'leer' AS accion UNION ALL
       SELECT 'aud.log.exportar', 'Exportar log de auditoría', NULL, CAST('E100001B-0000-4000-8000-00000000001B' AS UNIQUEIDENTIFIER), 'log', 'exportar') AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

PRINT 'Seed permisos RBAC completado (27 módulos + admin + modulos).';
