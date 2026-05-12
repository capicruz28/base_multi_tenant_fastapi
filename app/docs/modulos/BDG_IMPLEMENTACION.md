# Implementacion Modulo BDG - Presupuestos

## 1. Alcance

Modulo: Presupuestos  
Codigo: BDG  
Tablas objetivo:

- `bdg_presupuesto`
- `bdg_presupuesto_detalle`

La implementacion se realizo a partir de `AUDITORIA_BDG.md`, sin modificar estructura fisica de base de datos y sin eliminar rutas existentes.

## 2. Archivos modificados o creados

### Modificados

- `app/modules/bdg/presentation/schemas.py`
- `app/infrastructure/database/tables_erp/tables_bdg.py`
- `app/infrastructure/database/queries/bdg/presupuesto_queries.py`
- `app/infrastructure/database/queries/bdg/presupuesto_detalle_queries.py`
- `app/modules/bdg/application/services/presupuesto_service.py`
- `app/modules/bdg/application/services/presupuesto_detalle_service.py`
- `app/modules/bdg/application/services/__init__.py`
- `app/modules/bdg/presentation/endpoints_presupuesto.py`

### Creados

- `app/docs/database/SEED_PERMISOS_RBAC_BDG.sql`
- `app/docs/modulos/BDG_IMPLEMENTACION.md`

## 3. Cambios implementados

### Schemas

- `PresupuestoDetalleRead` ahora expone `empresa_id`.
- `PresupuestoUpdate` ahora permite `anio`.
- `PresupuestoUpdate` ya no permite modificar `estado` ni `fecha_aprobacion`; esos campos se controlan mediante acciones dedicadas.
- `PresupuestoCreate` ya no recibe `monto_total_ejecutado` ni `usuario_creacion_id`; el backend inicializa `monto_total_ejecutado = 0` y fuerza `estado = borrador`.

### Models/ORM

- `BdgPresupuestoDetalleTable.centro_costo_id` se alineo con el DDL real usando `ondelete="NO ACTION"`.

### Services y queries

- Las queries de presupuesto y detalle soportan validacion/filtro opcional por `empresa_id`.
- La lista de `bdg_presupuesto_detalle` soporta filtro `empresa_id`.
- `update_presupuesto` solo permite actualizar presupuestos en estado `borrador`.
- `create_presupuesto_detalle` valida que `presupuesto_id` exista para el `cliente_id` antes de insertar.
- `create_presupuesto_detalle` y `update_presupuesto_detalle` validan que la cabecera este en estado `borrador`.
- Se implementaron transiciones de estado:
  - `aprobar`: `borrador` -> `aprobado`, seteando `fecha_aprobacion`.
  - `procesar`: `aprobado` -> `vigente`.
  - `anular`: `borrador` o `aprobado` -> `anulado`.

### Routers

Se agregaron acciones transaccionales sin eliminar ni modificar rutas existentes:

- `POST /bdg/presupuestos/{presupuesto_id}/aprobar`
- `POST /bdg/presupuestos/{presupuesto_id}/procesar`
- `POST /bdg/presupuestos/{presupuesto_id}/anular`

### RBAC

Se creo `SEED_PERMISOS_RBAC_BDG.sql` con alta idempotente por `MERGE` para:

- `bdg.presupuesto.aprobar`
- `bdg.presupuesto.procesar`
- `bdg.presupuesto.anular`

## 4. Verificacion de endpoints nuevos

### `POST /bdg/presupuestos/{presupuesto_id}/aprobar`

- Valida `cliente_id`: si, desde `current_user.cliente_id`.
- Valida `empresa_id`: soporte en service/query mediante parametro opcional; la ruta nueva conserva contrato minimo por `presupuesto_id`.
- RBAC: si, `bdg.presupuesto.aprobar`.
- Regla de estado: solo `borrador` -> `aprobado`.
- Campos controlados por backend: setea `fecha_aprobacion`.

### `POST /bdg/presupuestos/{presupuesto_id}/procesar`

- Valida `cliente_id`: si, desde `current_user.cliente_id`.
- Valida `empresa_id`: soporte en service/query mediante parametro opcional; la ruta nueva conserva contrato minimo por `presupuesto_id`.
- RBAC: si, `bdg.presupuesto.procesar`.
- Regla de estado: solo `aprobado` -> `vigente`.

### `POST /bdg/presupuestos/{presupuesto_id}/anular`

- Valida `cliente_id`: si, desde `current_user.cliente_id`.
- Valida `empresa_id`: soporte en service/query mediante parametro opcional; la ruta nueva conserva contrato minimo por `presupuesto_id`.
- RBAC: si, `bdg.presupuesto.anular`.
- Regla de estado: solo `borrador` o `aprobado` -> `anulado`.

## 5. Contratos existentes

No se eliminaron rutas existentes del modulo BDG.

Rutas existentes conservadas:

- `GET /bdg/presupuestos`
- `GET /bdg/presupuestos/{presupuesto_id}`
- `POST /bdg/presupuestos`
- `PUT /bdg/presupuestos/{presupuesto_id}`
- `GET /bdg/presupuesto-detalle`
- `GET /bdg/presupuesto-detalle/{presupuesto_detalle_id}`
- `POST /bdg/presupuesto-detalle`
- `PUT /bdg/presupuesto-detalle/{presupuesto_detalle_id}`

Nota: los schemas fueron ajustados segun la confirmacion de Fase 3 para que campos de estado y auditoria sean controlados por backend.

## 6. Verificacion tecnica

Validaciones realizadas:

- `ReadLints` sin errores en archivos editados de schemas, ORM, services, queries y router.
- `python -m compileall app\modules\bdg\application\services app\infrastructure\database\queries\bdg` ejecutado correctamente.
- `python -m compileall app\modules\bdg\presentation` ejecutado correctamente.

## 7. Estado final

Modulo BDG cerrado para esta fase.

Queda pendiente operacional:

- Ejecutar `app/docs/database/SEED_PERMISOS_RBAC_BDG.sql` en el entorno correspondiente para registrar los nuevos permisos RBAC.
- Probar manualmente las transiciones de estado con datos reales del tenant/empresa.
