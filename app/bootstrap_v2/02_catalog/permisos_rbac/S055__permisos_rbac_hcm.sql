-- ============================================================================
-- bootstrap_v2 | official bootstrap line (copy; do not edit logic here)
-- Source (legacy, immutable): (see BOOTSTRAP_MANIFEST.md)
-- Layer: catalog
-- ============================================================================
-- ============================================================================
-- SCRIPT: SEED permisos RBAC HCM (Human Capital Management / Planillas y RRHH)
-- DESCRIPCIÓN:
--   - Catálogo de permisos alineado con los routers del backend (require_permission).
--   - Incluye acciones CRUD legacy (leer / crear / actualizar) por recurso.
--   - Incluye activar / desactivar empleado (PATCH dedicados).
--   - Incluye workflow de planilla: calcular, aprobar, marcar-pagada, cerrar.
--   - Incluye rescisión de contrato (POST dedicado).
-- NOTAS:
--   - MERGE por codigo: idempotente (seguro ante re-ejecución).
--   - modulo_id HCM: E1000010-0000-4000-8000-000000000010
--     (4.- SEED_MODULO_MENU_COMPLETO.sql).
-- DEPENDENCIAS:
--   - Script RBAC / tabla permiso (proyecto base).
--   - Módulo HCM registrado en catálogo de módulos.
-- ============================================================================

DECLARE @modulo_hcm_id UNIQUEIDENTIFIER = CAST('E1000010-0000-4000-8000-000000000010' AS UNIQUEIDENTIFIER);

-- --------------------------------------------------------------------------
-- HCM - Empleados (maestro + activar / desactivar)
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'hcm.empleado.leer'        AS codigo, 'Leer empleados'        AS nombre, 'Listar y ver empleados (HCM)'                         AS descripcion, @modulo_hcm_id AS modulo_id, 'empleado' AS recurso, 'leer'        AS accion UNION ALL
    SELECT 'hcm.empleado.crear',                   'Crear empleados',                   'Alta de empleado (HCM)'                                   , @modulo_hcm_id               , 'empleado' , 'crear'                  UNION ALL
    SELECT 'hcm.empleado.actualizar',              'Actualizar empleados',              'Editar datos de empleado (HCM)'                           , @modulo_hcm_id               , 'empleado' , 'actualizar'             UNION ALL
    SELECT 'hcm.empleado.activar',                 'Activar empleado',                  'Activar empleado (es_activo = 1)'                         , @modulo_hcm_id               , 'empleado' , 'activar'                UNION ALL
    SELECT 'hcm.empleado.desactivar',              'Desactivar empleado',               'Desactivar empleado (es_activo = 0)'                      , @modulo_hcm_id               , 'empleado' , 'desactivar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- HCM - Contratos (transaccional + rescindir)
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'hcm.contrato.leer'        AS codigo, 'Leer contratos'        AS nombre, 'Listar y ver contratos laborales (HCM)'                  AS descripcion, @modulo_hcm_id AS modulo_id, 'contrato' AS recurso, 'leer'        AS accion UNION ALL
    SELECT 'hcm.contrato.crear',                   'Crear contratos',                   'Alta de contrato (HCM)'                                   , @modulo_hcm_id               , 'contrato' , 'crear'                  UNION ALL
    SELECT 'hcm.contrato.actualizar',              'Actualizar contratos',              'Editar contrato (HCM)'                                    , @modulo_hcm_id               , 'contrato' , 'actualizar'             UNION ALL
    SELECT 'hcm.contrato.rescindir',               'Rescindir contrato',               'Rescisión: estado rescindido y fechas (HCM)'              , @modulo_hcm_id               , 'contrato' , 'rescindir'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- HCM - Conceptos de planilla (catálogo maestro)
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'hcm.concepto_planilla.leer'        AS codigo, 'Leer conceptos de planilla'        AS nombre, 'Listar y ver conceptos de ingreso/descuento/aporte (HCM)' AS descripcion, @modulo_hcm_id AS modulo_id, 'concepto_planilla' AS recurso, 'leer'        AS accion UNION ALL
    SELECT 'hcm.concepto_planilla.crear',                   'Crear conceptos de planilla',                   'Alta de concepto de planilla (HCM)'                       , @modulo_hcm_id               , 'concepto_planilla' , 'crear'                  UNION ALL
    SELECT 'hcm.concepto_planilla.actualizar',              'Actualizar conceptos de planilla',              'Editar concepto de planilla (HCM)'                        , @modulo_hcm_id               , 'concepto_planilla' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- HCM - Planillas (cabecera transaccional + workflow de estados)
--   borrador → calculada → aprobada → pagada → cerrada
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'hcm.planilla.leer'        AS codigo, 'Leer planillas'        AS nombre, 'Listar y ver planillas de remuneraciones (HCM)'           AS descripcion, @modulo_hcm_id AS modulo_id, 'planilla' AS recurso, 'leer'        AS accion UNION ALL
    SELECT 'hcm.planilla.crear',                   'Crear planillas',                   'Alta de planilla en borrador (HCM)'                       , @modulo_hcm_id               , 'planilla' , 'crear'                  UNION ALL
    SELECT 'hcm.planilla.actualizar',              'Actualizar planillas',              'Editar planilla solo en borrador (HCM)'                   , @modulo_hcm_id               , 'planilla' , 'actualizar'             UNION ALL
    SELECT 'hcm.planilla.calcular',                'Calcular planilla',                 'Transición: borrador → calculada (HCM)'                  , @modulo_hcm_id               , 'planilla' , 'calcular'               UNION ALL
    SELECT 'hcm.planilla.aprobar',                 'Aprobar planilla',                  'Transición: calculada → aprobada (HCM)'                   , @modulo_hcm_id               , 'planilla' , 'aprobar'                UNION ALL
    SELECT 'hcm.planilla.marcar-pagada',           'Marcar planilla como pagada',       'Transición: aprobada → pagada (HCM)'                      , @modulo_hcm_id               , 'planilla' , 'marcar-pagada'          UNION ALL
    SELECT 'hcm.planilla.cerrar',                  'Cerrar planilla',                   'Transición: pagada → cerrada (HCM)'                       , @modulo_hcm_id               , 'planilla' , 'cerrar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- HCM - Planilla por empleado (líneas)
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'hcm.planilla_empleado.leer'        AS codigo, 'Leer planilla empleado'        AS nombre, 'Listar y ver líneas de planilla por empleado (HCM)'      AS descripcion, @modulo_hcm_id AS modulo_id, 'planilla_empleado' AS recurso, 'leer'        AS accion UNION ALL
    SELECT 'hcm.planilla_empleado.crear',                   'Crear planilla empleado',                   'Agregar empleado a planilla (solo borrador) (HCM)'      , @modulo_hcm_id               , 'planilla_empleado' , 'crear'                  UNION ALL
    SELECT 'hcm.planilla_empleado.actualizar',              'Actualizar planilla empleado',              'Editar línea de planilla empleado (solo borrador) (HCM)'  , @modulo_hcm_id               , 'planilla_empleado' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- HCM - Detalle de planilla (conceptos por empleado)
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'hcm.planilla_detalle.leer'        AS codigo, 'Leer detalle de planilla'        AS nombre, 'Listar y ver conceptos aplicados en planilla (HCM)'     AS descripcion, @modulo_hcm_id AS modulo_id, 'planilla_detalle' AS recurso, 'leer'        AS accion UNION ALL
    SELECT 'hcm.planilla_detalle.crear',                   'Crear detalle de planilla',                   'Agregar concepto a línea de empleado (solo borrador)'     , @modulo_hcm_id               , 'planilla_detalle' , 'crear'                  UNION ALL
    SELECT 'hcm.planilla_detalle.actualizar',              'Actualizar detalle de planilla',              'Editar monto/concepto en detalle (solo borrador) (HCM)'   , @modulo_hcm_id               , 'planilla_detalle' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- HCM - Asistencia
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'hcm.asistencia.leer'        AS codigo, 'Leer asistencia'        AS nombre, 'Listar y ver registros de asistencia (HCM)'             AS descripcion, @modulo_hcm_id AS modulo_id, 'asistencia' AS recurso, 'leer'        AS accion UNION ALL
    SELECT 'hcm.asistencia.crear',                   'Crear asistencia',                   'Registrar marcación / día (HCM)'                          , @modulo_hcm_id               , 'asistencia' , 'crear'                  UNION ALL
    SELECT 'hcm.asistencia.actualizar',              'Actualizar asistencia',              'Editar registro de asistencia (HCM)'                      , @modulo_hcm_id               , 'asistencia' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- HCM - Vacaciones
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'hcm.vacaciones.leer'        AS codigo, 'Leer vacaciones'        AS nombre, 'Listar y ver periodos de vacaciones (HCM)'               AS descripcion, @modulo_hcm_id AS modulo_id, 'vacaciones' AS recurso, 'leer'        AS accion UNION ALL
    SELECT 'hcm.vacaciones.crear',                   'Crear vacaciones',                   'Registrar periodo / solicitud de vacaciones (HCM)'        , @modulo_hcm_id               , 'vacaciones' , 'crear'                  UNION ALL
    SELECT 'hcm.vacaciones.actualizar',              'Actualizar vacaciones',              'Editar vacaciones (HCM)'                                  , @modulo_hcm_id               , 'vacaciones' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

-- --------------------------------------------------------------------------
-- HCM - Préstamos
-- --------------------------------------------------------------------------
MERGE INTO permiso AS t
USING (
    SELECT 'hcm.prestamo.leer'        AS codigo, 'Leer préstamos'        AS nombre, 'Listar y ver préstamos / adelantos a empleados (HCM)'    AS descripcion, @modulo_hcm_id AS modulo_id, 'prestamo' AS recurso, 'leer'        AS accion UNION ALL
    SELECT 'hcm.prestamo.crear',                   'Crear préstamos',                   'Alta de préstamo o adelanto (HCM)'                        , @modulo_hcm_id               , 'prestamo' , 'crear'                  UNION ALL
    SELECT 'hcm.prestamo.actualizar',              'Actualizar préstamos',              'Editar préstamo (HCM)'                                    , @modulo_hcm_id               , 'prestamo' , 'actualizar'
) AS s
ON t.codigo = s.codigo
WHEN NOT MATCHED BY TARGET THEN
    INSERT (permiso_id, codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo)
    VALUES (NEWID(), s.codigo, s.nombre, s.descripcion, s.modulo_id, s.recurso, s.accion, 1);
GO

PRINT 'Seed permisos RBAC HCM completado.';
GO
