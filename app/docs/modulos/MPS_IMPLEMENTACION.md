# Implementación módulo MPS — Plan Maestro de Producción

Fecha: 2026-05-07  
Código: `MPS`  
Stack: FastAPI + SQL Server (multi-tenant)  
Arquitectura mantenida: `presentation → application/services → infrastructure/database/queries`  

## 1) Alcance (tablas MPS_)

Fuente BD: `docs/bd/MPS_TABLAS.sql`.

- **`mps_pronostico_demanda`** (transaccional)
- **`mps_plan_produccion`** (transaccional, cabecera con estado)
- **`mps_plan_produccion_detalle`** (transaccional, detalle)

## 2) Endpoints del módulo

Base v1: `/api/v1/mps` (incluido en `app/api/v1/api.py`).

### 2.1 Pronóstico de demanda
- **GET** `/mps/pronostico-demanda` (RBAC `mps.pronostico_demanda.leer`)
- **GET** `/mps/pronostico-demanda/{pronostico_id}` (RBAC `mps.pronostico_demanda.leer`)
- **POST** `/mps/pronostico-demanda` (RBAC `mps.pronostico_demanda.crear`)
- **PUT** `/mps/pronostico-demanda/{pronostico_id}` (RBAC `mps.pronostico_demanda.actualizar`)

### 2.2 Plan de producción (cabecera)
CRUD existente (sin romper compatibilidad):
- **GET** `/mps/plan-produccion` (RBAC `mps.plan_produccion.leer`)
- **GET** `/mps/plan-produccion/{plan_produccion_id}` (RBAC `mps.plan_produccion.leer`)
- **POST** `/mps/plan-produccion` (**RBAC corregido**: `mps.plan_produccion.crear`)
- **PUT** `/mps/plan-produccion/{plan_produccion_id}` (RBAC `mps.plan_produccion.actualizar`)

Acciones transaccionales agregadas:
- **POST** `/mps/plan-produccion/{plan_produccion_id}/aprobar` (RBAC `mps.plan_produccion.aprobar`)
- **POST** `/mps/plan-produccion/{plan_produccion_id}/ejecutar` (RBAC `mps.plan_produccion.ejecutar`)
- **POST** `/mps/plan-produccion/{plan_produccion_id}/cerrar` (RBAC `mps.plan_produccion.cerrar`)
- **POST** `/mps/plan-produccion/{plan_produccion_id}/anular` (RBAC `mps.plan_produccion.anular`)

### 2.3 Plan de producción (detalle)
- **GET** `/mps/plan-produccion-detalle` (RBAC `mps.plan_produccion_detalle.leer`)
- **GET** `/mps/plan-produccion-detalle/{plan_detalle_id}` (RBAC `mps.plan_produccion_detalle.leer`)
- **POST** `/mps/plan-produccion-detalle` (RBAC `mps.plan_produccion_detalle.crear`)
- **PUT** `/mps/plan-produccion-detalle/{plan_detalle_id}` (RBAC `mps.plan_produccion_detalle.actualizar`)

## 3) Reglas implementadas (tenant + workflow)

### 3.1 Multi-tenant (cliente_id / empresa_id)
- **cliente_id**: todas las operaciones quedan aisladas por `cliente_id` (server-side).
- **empresa_id en detalle**:
  - en **POST/PUT** de detalle, `empresa_id` **no se toma del body**: se **deriva desde la cabecera** `mps_plan_produccion`.
  - se valida pertenencia tenant y coherencia: `plan_produccion_id` debe existir para el tenant y su `empresa_id` debe coincidir.
- **empresa_id en responses**:
  - se agregó `empresa_id` a `PlanProduccionDetalleRead`.

Limitación conocida (sin romper contratos):
- El `current_user` actual no expone una “empresa activa” (`empresa_id`) como parte del contexto de auth; por ello, el endurecimiento por “empresa actual del usuario” no se puede imponer globalmente en cabecera sin cambios adicionales de auth/contexto. Se compensó con validación cruzada cabecera→detalle y filtros por `cliente_id` existentes.

### 3.2 Workflow de `mps_plan_produccion`
- **PUT** solo editable en estado **`borrador`**.
- **Cambio de estado por PUT**: **no permitido** (transiciones solo por acciones).
- **Transiciones válidas**:
  - `borrador → aprobado → ejecutado → cerrado`
  - `anulado` permitido desde `borrador/aprobado/ejecutado`

### 3.3 Edición de detalle
- **POST/PUT** de detalle se bloquea si el plan cabecera no está en **`borrador`**.

## 4) RBAC (permisos)

- Se corrigió RBAC faltante en `POST /mps/plan-produccion` (`mps.plan_produccion.crear`).
- Se agregaron permisos del workflow:
  - `mps.plan_produccion.aprobar`
  - `mps.plan_produccion.ejecutar`
  - `mps.plan_produccion.cerrar`
  - `mps.plan_produccion.anular`

Seed SQL: `app/docs/database/SEED_PERMISOS_RBAC_MPS.sql` (MERGE idempotente).

## 5) Archivos relevantes modificados/creados (MPS)

- **Schemas**: `app/modules/mps/presentation/schemas.py`
- **Routers**: `app/modules/mps/presentation/endpoints_plan_produccion.py`
- **Services**:
  - `app/modules/mps/application/services/plan_produccion_service.py`
  - `app/modules/mps/application/services/plan_produccion_detalle_service.py`
  - `app/modules/mps/application/services/__init__.py`
- **Queries**:
  - `app/infrastructure/database/queries/mps/plan_produccion_queries.py`
  - `app/infrastructure/database/queries/mps/plan_produccion_detalle_queries.py`
- **Docs**:
  - `app/docs/modulos/AUDITORIA_MPS.md`
  - `app/docs/modulos/MPS_IMPLEMENTACION.md`
  - `app/docs/database/SEED_PERMISOS_RBAC_MPS.sql`

## 6) Test plan (manual)

- Crear plan en borrador:
  - `POST /api/v1/mps/plan-produccion` → estado inicial `borrador`.
- Editar plan:
  - `PUT /api/v1/mps/plan-produccion/{id}` funciona solo en `borrador`.
  - Intentar cambiar `estado` por PUT debe retornar 400.
- Workflow:
  - `POST /{id}/aprobar` (borrador→aprobado)
  - `POST /{id}/ejecutar` (aprobado→ejecutado)
  - `POST /{id}/cerrar` (ejecutado→cerrado)
  - `POST /{id}/anular` (según reglas)
- Detalle:
  - `POST /api/v1/mps/plan-produccion-detalle` deriva `empresa_id` desde cabecera y valida pertenencia tenant.
  - Tras aprobar el plan, `POST/PUT` de detalle debe retornar 400 (plan no editable).

