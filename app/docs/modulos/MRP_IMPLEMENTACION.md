# IMPLEMENTACIÓN — MRP (Planeamiento de Materiales)

Fecha: 2026-05-07

Este documento describe la implementación realizada para el módulo **MRP** siguiendo el flujo transaccional y las reglas multi-tenant/RBAC del proyecto, **sin modificar estructura de BD** ni romper contratos existentes.

## Alcance

Tablas del módulo (`mrp_*`):
- **`mrp_plan_maestro`** (transaccional)
- **`mrp_necesidad_bruta`** (transaccional sin workflow en BD)
- **`mrp_explosion_materiales`** (derivada / read-only)
- **`mrp_orden_sugerida`** (operacional / workflow controlado)

## Arquitectura aplicada (patrón del repo)

- **Routers**: `app/modules/mrp/presentation/endpoints_*.py`
- **Services**: `app/modules/mrp/application/services/*_service.py`
- **Queries**: `app/infrastructure/database/queries/mrp/*_queries.py`
- **Tenant**: `cliente_id` siempre proviene de `current_user.cliente_id`. `empresa_id` se filtra cuando la tabla lo incluye.
- **RBAC**: `require_permission("mrp.<recurso>.<accion>")`

## Cambios realizados (resumen)

### 1) Plan Maestro (`mrp_plan_maestro`) — flujo transaccional

#### Validación en `PUT`
- `PUT /mrp/plan-maestro/{id}` queda **permitido solo** si el plan está en estado **`borrador`** o **`inicial`**.
- Se bloquea el cambio de `estado` por `PUT`; los cambios de estado se realizan mediante **acciones explícitas**.

#### Transiciones explícitas (workflow)
Se implementaron transiciones con validación de estado previo:
- **Calcular**: `borrador|inicial → calculado` (persiste `fecha_calculo`)
- **Aprobar**: `calculado → aprobado` (persiste `fecha_aprobacion`)
- **Ejecutar**: `aprobado → ejecutado`
- **Cerrar**: `ejecutado → cerrado`
- **Anular**: `borrador|inicial|calculado|aprobado → anulado`

Persistencia de fechas:
- `fecha_calculo` se setea con `GETDATE()` cuando el estado pasa a `calculado`.
- `fecha_aprobacion` se setea con `GETDATE()` cuando el estado pasa a `aprobado`.

### 2) Endpoints nuevos — Plan Maestro

Se agregaron (sin modificar rutas existentes):
- `POST /mrp/plan-maestro/{id}/calcular` (permiso `mrp.plan_maestro.calcular`)
- `POST /mrp/plan-maestro/{id}/aprobar` (permiso `mrp.plan_maestro.aprobar`)
- `POST /mrp/plan-maestro/{id}/ejecutar` (permiso `mrp.plan_maestro.ejecutar`)
- `POST /mrp/plan-maestro/{id}/cerrar` (permiso `mrp.plan_maestro.cerrar`)
- `POST /mrp/plan-maestro/{id}/anular` (permiso `mrp.plan_maestro.anular`)

### 3) Explosión de materiales (`mrp_explosion_materiales`) — derivada/read-only

Para mantener compatibilidad:
- **Se mantienen endpoints existentes** `POST` y `PUT` (no se eliminan).

Endurecimiento:
- En service, `create/update` devuelven error de validación indicando que es una tabla **derivada read-only** y que la escritura está reservada a **procesos internos controlados**.

### 4) Órdenes sugeridas (`mrp_orden_sugerida`) — workflow controlado

Endurecimiento:
- Se bloquea **creación manual** por `POST /mrp/ordenes-sugeridas` (manteniendo endpoint por compatibilidad).
- `PUT /mrp/ordenes-sugeridas/{id}` queda **restringido**:
  - Solo editable en estado **`sugerida`**
  - Campos permitidos por PUT: `proveedor_sugerido_id`, `lead_time_dias`, `fecha_orden_sugerida`, `observaciones`
  - No permite cambiar `estado` ni setear `documento_generado_*` por PUT

Workflow implementado:
- **Aprobar**: `sugerida → aprobada`
- **Rechazar**: `sugerida|aprobada → rechazada`
- **Convertir**: `aprobada → convertida`
  - Requiere `documento_generado_tipo` y `documento_generado_id`
  - Persiste `fecha_conversion=GETDATE()`

### 5) Endpoints nuevos — Órdenes sugeridas

Se agregaron:
- `POST /mrp/ordenes-sugeridas/{id}/aprobar` (permiso `mrp.orden_sugerida.aprobar`)
- `POST /mrp/ordenes-sugeridas/{id}/rechazar` (permiso `mrp.orden_sugerida.rechazar`)
- `POST /mrp/ordenes-sugeridas/{id}/convertir` (permiso `mrp.orden_sugerida.convertir`)
  - Body requerido:
    - `documento_generado_tipo` (string, max 20)
    - `documento_generado_id` (UUID)

### 6) Necesidades brutas (`mrp_necesidad_bruta`)

Se mantiene CRUD sin workflow (la tabla no tiene `estado` ni `es_activo` en BD).

Validaciones añadidas:
- En `create` y `update`: `plan_maestro_id` debe existir para el mismo `cliente_id`.
- En `update`: si se envía `cantidad_requerida`, debe ser `> 0`; si se envía `prioridad`, debe ser `> 0`.

## RBAC (permisos) — Seed

Se agregó el script:
- `app/docs/database/SEED_PERMISOS_RBAC_MRP.sql`

Incluye los permisos solicitados:
- `mrp.plan_maestro.calcular`
- `mrp.plan_maestro.aprobar`
- `mrp.plan_maestro.ejecutar`
- `mrp.plan_maestro.cerrar`
- `mrp.plan_maestro.anular`
- `mrp.orden_sugerida.aprobar`
- `mrp.orden_sugerida.rechazar`
- `mrp.orden_sugerida.convertir`

## Archivos principales modificados/creados

- **Services/Queries**
  - `app/infrastructure/database/queries/mrp/plan_maestro_queries.py`
  - `app/modules/mrp/application/services/plan_maestro_service.py`
  - `app/infrastructure/database/queries/mrp/orden_sugerida_queries.py`
  - `app/modules/mrp/application/services/orden_sugerida_service.py`
  - `app/modules/mrp/application/services/explosion_materiales_service.py`
  - `app/modules/mrp/application/services/necesidad_bruta_service.py`
  - `app/modules/mrp/application/services/__init__.py`
- **Routers**
  - `app/modules/mrp/presentation/endpoints_plan_maestro.py`
  - `app/modules/mrp/presentation/endpoints_orden_sugerida.py`
- **Docs**
  - `app/docs/database/SEED_PERMISOS_RBAC_MRP.sql` (**nuevo**)
  - `app/docs/modulos/AUDITORIA_MRP.md` (**nuevo**)
  - `app/docs/modulos/MRP_IMPLEMENTACION.md` (**este documento**)

## Notas finales

- No se modificó estructura de BD.
- No se eliminaron endpoints existentes; los endurecimientos se implementaron en **services** para mantener compatibilidad.
- Todas las operaciones mantienen el filtro por **`cliente_id`** y validan consistencia de referencias críticas (`plan_maestro_id`).

