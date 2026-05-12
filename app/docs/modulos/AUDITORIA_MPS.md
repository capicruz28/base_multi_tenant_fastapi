# Auditoría módulo MPS — Plan Maestro de Producción

Fecha: 2026-05-07  
Código módulo: `MPS`  
Ruta base API v1: `/api/v1/mps` (router incluido en `app/api/v1/api.py`)

## 1) Tablas detectadas y tipo

Fuente: `docs/bd/MPS_TABLAS.sql` (prefijo `mps_` = `MPS_`).

### 1.1 `mps_pronostico_demanda` (transaccional)
- **PK**: `pronostico_id`
- **Tenant**: `cliente_id` (sí), `empresa_id` (sí), `es_activo` (no)
- **FKs**:
  - `empresa_id` → `org_empresa.empresa_id`
  - `producto_id` → `inv_producto.producto_id`
  - `unidad_medida_id` → `inv_unidad_medida.unidad_medida_id`

### 1.2 `mps_plan_produccion` (transaccional, cabecera)
- **PK**: `plan_produccion_id`
- **Tenant**: `cliente_id` (sí), `empresa_id` (sí), `es_activo` (no)
- **FKs**:
  - `empresa_id` → `org_empresa.empresa_id`
- **Unicidad**:
  - `UNIQUE (cliente_id, empresa_id, codigo_plan)`
- **Estado** (en BD): `estado` con default `borrador` (valores esperados en comentario: `borrador`, `aprobado`, `ejecutado`, `cerrado`)

### 1.3 `mps_plan_produccion_detalle` (transaccional, detalle)
- **PK**: `plan_detalle_id`
- **Tenant**: `cliente_id` (sí), `empresa_id` (sí), `es_activo` (no)
- **FKs**:
  - `empresa_id` → `org_empresa.empresa_id`
  - `plan_produccion_id` → `mps_plan_produccion.plan_produccion_id`
  - `producto_id` → `inv_producto.producto_id`
  - `unidad_medida_id` → `inv_unidad_medida.unidad_medida_id`
- **Columnas calculadas en BD** (no CRUD): `porcentaje_uso_capacidad` (calculada)

## 2) Endpoints existentes

Fuente: `app/modules/mps/presentation/`.

### 2.1 Pronóstico Demanda (`/pronostico-demanda`)
| Ruta | Método | Entidad | ¿Tiene tenant? | ¿Tiene RBAC? |
|---|---:|---|---|---|
| `/mps/pronostico-demanda` | GET | `mps_pronostico_demanda` | **Parcial**: filtra por `cliente_id` y opcional `empresa_id` | **Sí** `mps.pronostico_demanda.leer` |
| `/mps/pronostico-demanda/{pronostico_id}` | GET | `mps_pronostico_demanda` | **Parcial**: filtra por `cliente_id` | **Sí** `mps.pronostico_demanda.leer` |
| `/mps/pronostico-demanda` | POST | `mps_pronostico_demanda` | **Sí**: fuerza `cliente_id` (server-side) | **Sí** `mps.pronostico_demanda.crear` |
| `/mps/pronostico-demanda/{pronostico_id}` | PUT | `mps_pronostico_demanda` | **Sí**: fuerza `cliente_id` (server-side) | **Sí** `mps.pronostico_demanda.actualizar` |

Observación: el servicio mapea `anio` (API) ↔ `año` (BD).

### 2.2 Plan de Producción (`/plan-produccion`)
| Ruta | Método | Entidad | ¿Tiene tenant? | ¿Tiene RBAC? |
|---|---:|---|---|---|
| `/mps/plan-produccion` | GET | `mps_plan_produccion` | **Parcial**: filtra por `cliente_id` y opcional `empresa_id` | **Sí** `mps.plan_produccion.leer` |
| `/mps/plan-produccion/{plan_produccion_id}` | GET | `mps_plan_produccion` | **Parcial**: filtra por `cliente_id` | **Sí** `mps.plan_produccion.leer` |
| `/mps/plan-produccion` | POST | `mps_plan_produccion` | **Sí**: fuerza `cliente_id` (server-side) | **NO** (no tiene `require_permission`) |
| `/mps/plan-produccion/{plan_produccion_id}` | PUT | `mps_plan_produccion` | **Sí**: fuerza `cliente_id` (server-side) | **Sí** `mps.plan_produccion.actualizar` |

### 2.3 Plan Producción Detalle (`/plan-produccion-detalle`)
| Ruta | Método | Entidad | ¿Tiene tenant? | ¿Tiene RBAC? |
|---|---:|---|---|---|
| `/mps/plan-produccion-detalle` | GET | `mps_plan_produccion_detalle` | **Parcial**: filtra por `cliente_id` (no valida `empresa_id`) | **Sí** `mps.plan_produccion_detalle.leer` |
| `/mps/plan-produccion-detalle/{plan_detalle_id}` | GET | `mps_plan_produccion_detalle` | **Parcial**: filtra por `cliente_id` (no valida `empresa_id`) | **Sí** `mps.plan_produccion_detalle.leer` |
| `/mps/plan-produccion-detalle` | POST | `mps_plan_produccion_detalle` | **Parcial**: fuerza `cliente_id`; intenta **derivar `empresa_id`** desde cabecera | **Sí** `mps.plan_produccion_detalle.crear` |
| `/mps/plan-produccion-detalle/{plan_detalle_id}` | PUT | `mps_plan_produccion_detalle` | **Parcial**: fuerza `cliente_id`; no valida `empresa_id` | **Sí** `mps.plan_produccion_detalle.actualizar` |

## 3) Brechas funcionales (según patrón del prompt)

Regla del prompt para entidades **TRANSACCIONALES**: `crear (borrador)`, `actualizar (solo borrador)`, `aprobar`, `procesar/ejecutar`, `anular`, `listar`, `detalle`.

### 3.1 `mps_plan_produccion` (cabecera)
- **Existe**: listar, detalle, crear, actualizar.
- **Falta**:
  - endpoint de **aprobar** (e.g. `POST /mps/plan-produccion/{id}/aprobar`)
  - endpoint de **ejecutar/procesar** (e.g. `POST /mps/plan-produccion/{id}/ejecutar`)
  - endpoint de **cerrar** (si aplica al flujo de estado)
  - endpoint de **anular** (e.g. `POST /mps/plan-produccion/{id}/anular`)
  - reglas de negocio: **restringir actualización** a `estado = borrador`
- **RBAC**:
  - el `POST /mps/plan-produccion` está **sin RBAC** (debe exigir `mps.plan_produccion.crear`).

### 3.2 `mps_plan_produccion_detalle` (detalle)
- **Existe**: listar, detalle, crear, actualizar.
- **Falta** (si el detalle debe seguir el estado de cabecera):
  - validaciones para permitir cambios **solo en borrador** (derivado de cabecera)
  - operaciones masivas/embebidas: el prompt sugiere que “el detalle se maneja embebido en la cabecera” para transaccionales; aquí está expuesto como recurso separado.

### 3.3 `mps_pronostico_demanda`
- **Existe**: listar, detalle, crear, actualizar.
- **Falta**:
  - no hay “activar/desactivar” porque no existe `es_activo` en BD (no aplica al patrón maestro).
  - podría requerirse “eliminar lógico” si el negocio lo pide, pero la BD no lo soporta hoy.

## 4) Campos faltantes / inconsistencias en schemas vs BD

Fuente: `app/modules/mps/presentation/schemas.py` vs `docs/bd/MPS_TABLAS.sql` y `app/infrastructure/database/tables_erp/tables_mps.py`.

### 4.1 `PlanProduccionDetalleRead`
- **Falta** `empresa_id` (en BD es `NOT NULL` y existe en `MpsPlanProduccionDetalleTable`).

## 5) Problemas de tenant o RBAC

### 5.1 RBAC incompleto
- `POST /mps/plan-produccion` no aplica `require_permission(...)`.

### 5.2 Validación de `empresa_id` (regla absoluta del proyecto)
Regla: “**SIEMPRE validar `empresa_id` cuando la tabla lo tenga**”.

Hallazgos:
- `mps_plan_produccion`:
  - En `GET /mps/plan-produccion` `empresa_id` es **opcional** (puede listar múltiples empresas para un mismo `cliente_id`).
  - En `GET /mps/plan-produccion/{id}` no se valida `empresa_id` (solo `cliente_id`).
- `mps_plan_produccion_detalle`:
  - En `GET` list/detalle no se valida `empresa_id` (solo `cliente_id`).
  - En `POST` se intenta derivar `empresa_id` desde cabecera, pero si el `plan_produccion_id` no existe o no pertenece al tenant, el insert podría quedar inconsistente o fallar por `NOT NULL`/FK.

## 6) Observaciones de arquitectura (estructura técnica)

- El módulo sigue el patrón `presentation` → `application/services` → `infrastructure/database/queries`.
- No existe una capa explícita `repositories` para `MPS` (a diferencia de la guía “routers → services → repositories → schemas” del prompt).

## 7) Endpoints faltantes (propuesta de rutas sugeridas)

Sin implementar (solo sugerencia de auditoría):
- Para `mps_plan_produccion`:
  - `POST /mps/plan-produccion/{plan_produccion_id}/aprobar`
  - `POST /mps/plan-produccion/{plan_produccion_id}/ejecutar` (o `/procesar`)
  - `POST /mps/plan-produccion/{plan_produccion_id}/anular`
  - (opcional) `POST /mps/plan-produccion/{plan_produccion_id}/cerrar`

Cada uno debería incluir:
- validación `cliente_id` y `empresa_id`
- RBAC: `mps.plan_produccion.aprobar` / `mps.plan_produccion.ejecutar` / `mps.plan_produccion.anular` / `mps.plan_produccion.cerrar`

