-- ============================================================================
-- SCRIPT: Permisos RBAC — módulo FIN (Finanzas y Contabilidad)
-- DESCRIPCIÓN: Alta idempotente (MERGE por codigo) de permisos fin.plan_cuenta.*,
--              fin.periodo.*, fin.asiento.* y fin.asiento_detalle.*.
-- DEPENDENCIAS: Ejecutar después de SEED_PERMISOS_RBAC.sql (o equivalente base)
--               y existencia del módulo FIN en tabla modulo.
-- FIN modulo_id: E1000011-0000-4000-8000-000000000011
-- USO: Ejecutar en entornos donde falten estos códigos; seguro re-ejecutar (MERGE).
-- ============================================================================

DECLARE @modulo_fin UNIQUEIDENTIFIER = CAST('E1000011-0000-4000-8000-000000000011' AS UNIQUEIDENTIFIER);

MERGE INTO permiso AS t
USING (
    SELECT 'fin.plan_cuenta.leer' AS codigo, N'Leer plan de cuentas' AS nombre, N'Listar y consultar cuentas contables del plan' AS descripcion, @modulo_fin AS modulo_id, 'plan_cuenta' AS recurso, 'leer' AS accion UNION ALL
    SELECT 'fin.plan_cuenta.crear', N'Crear cuenta en plan', N'Alta de cuentas en el plan contable', @modulo_fin, 'plan_cuenta', 'crear' UNION ALL
    SELECT 'fin.plan_cuenta.actualizar', N'Actualizar cuenta del plan', N'Modificar datos de cuentas y reactivar cuentas dadas de baja', @modulo_fin, 'plan_cuenta', 'actualizar' UNION ALL
    SELECT 'fin.plan_cuenta.eliminar', N'Desactivar cuenta del plan', N'Baja lógica (es_activo=0) de cuentas del plan', @modulo_fin, 'plan_cuenta', 'eliminar' UNION ALL

    SELECT 'fin.periodo.leer', N'Leer periodos contables', N'Listar y consultar periodos contables', @modulo_fin, 'periodo', 'leer' UNION ALL
    SELECT 'fin.periodo.crear', N'Crear periodo contable', N'Alta de periodos (mes/año)', @modulo_fin, 'periodo', 'crear' UNION ALL
    SELECT 'fin.periodo.actualizar', N'Actualizar periodo contable', N'Modificar datos de periodos abiertos', @modulo_fin, 'periodo', 'actualizar' UNION ALL
    SELECT 'fin.periodo.cerrar', N'Cerrar periodo contable', N'Cerrar periodo validando asientos en borrador', @modulo_fin, 'periodo', 'cerrar' UNION ALL

    SELECT 'fin.asiento.leer', N'Leer asientos contables', N'Listar y consultar asientos y cabeceras', @modulo_fin, 'asiento', 'leer' UNION ALL
    SELECT 'fin.asiento.crear', N'Crear asiento contable', N'Alta de asientos en borrador', @modulo_fin, 'asiento', 'crear' UNION ALL
    SELECT 'fin.asiento.actualizar', N'Actualizar asiento contable', N'Editar asiento solo en borrador', @modulo_fin, 'asiento', 'actualizar' UNION ALL
    SELECT 'fin.asiento.aprobar', N'Aprobar asiento', N'Transición borrador → aprobado', @modulo_fin, 'asiento', 'aprobar' UNION ALL
    SELECT 'fin.asiento.registrar', N'Registrar asiento', N'Transición aprobado → registrado', @modulo_fin, 'asiento', 'registrar' UNION ALL
    SELECT 'fin.asiento.anular', N'Anular asiento', N'Anular asiento (no registrado) con motivo', @modulo_fin, 'asiento', 'anular' UNION ALL

    SELECT 'fin.asiento_detalle.leer', N'Leer detalles de asiento', N'Listar y ver líneas de asiento contable', @modulo_fin, 'asiento_detalle', 'leer' UNION ALL
    SELECT 'fin.asiento_detalle.crear', N'Crear detalle de asiento', N'Añadir líneas a asiento contable', @modulo_fin, 'asiento_detalle', 'crear' UNION ALL
    SELECT 'fin.asiento_detalle.actualizar', N'Actualizar detalle de asiento', N'Editar líneas de asiento', @modulo_fin, 'asiento_detalle', 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO
