# Auditoría — Módulo WMS (Warehouse Management System)

**Código:** WMS  
**Fuente de modelo de datos:** `docs/bd/WMS_TABLAS.sql` (tablas `wms_*`).  
**Metodología:** `docs/prompts/PROMPT_MODULO_MAESTRO.md` — Fase 2.

**Inventario de código WMS**

| Capa | Ubicación |
|------|-----------|
| Routers (presentation) | `app/modules/wms/presentation/endpoints.py` (agregador), `endpoints_zonas.py`, `endpoints_ubicaciones.py`, `endpoints_stock.py`, `endpoints_tareas.py` |
| Schemas | `app/modules/wms/presentation/schemas.py` |
| Servicios (application) | `app/modules/wms/application/services/zona_almacen_service.py`, `ubicacion_service.py`, `stock_ubicacion_service.py`, `tarea_service.py`, `__init__.py` |
| Consultas SQL (infraestructura) | `app/infrastructure/database/queries/wms/zona_almacen_queries.py`, `ubicacion_queries.py`, `stock_ubicacion_queries.py`, `tarea_queries.py`, `__init__.py` |
| Tablas Core (ORM metadata) | `app/infrastructure/database/tables_erp/tables_wms.py` |
| Repositories dedicados en `app/modules/wms/` | No hay carpeta `repositories`; persistencia vía queries en infraestructura |

Prefijo API registrado: **`/wms`** (`app/api/v1/api.py`).

---

## 1. Tablas detectadas y su tipo

| Tabla | Tipo (prompt) |
|-------|----------------|
| `wms_zona_almacen` | Maestro |
| `wms_ubicacion` | Maestro |
| `wms_stock_ubicacion` | Derivada / analítica-operativa (stock por ubicación) |
| `wms_tarea` | Transaccional |

---

## 2. Endpoints existentes

Criterios: **tenant** = uso de `cliente_id` del usuario autenticado en servicio/query y, cuando la tabla lo tiene, filtro/validación de `empresa_id`. **RBAC** = presencia de `Depends(require_permission(...))` en la ruta.

Rutas relativas a **`/wms`** (el router agregador monta `zonas`, `ubicaciones`, `stock-ubicacion`, `tareas`).

### 2.1 Zonas (`/wms/zonas`) — `wms_zona_almacen`

| Ruta | Método | Entidad (tabla) | Tenant (`cliente_id`) | `empresa_id` (tabla lo requiere) | RBAC |
|------|--------|-----------------|------------------------|----------------------------------|------|
| `/zonas` | GET | `wms_zona_almacen` | Sí (service + queries filtran `cliente_id`) | **No** (no se filtra/valida) | `wms.zona.leer` |
| `/zonas/{zona_id}` | GET | `wms_zona_almacen` | Sí | **No** | `wms.zona.leer` |
| `/zonas` | POST | `wms_zona_almacen` | Sí (`cliente_id` forzado en query) | **No se asigna desde contexto** (y no existe en schema Create) | `wms.zona.crear` |
| `/zonas/{zona_id}` | PUT | `wms_zona_almacen` | Sí | **No** | `wms.zona.actualizar` |

### 2.2 Ubicaciones (`/wms/ubicaciones`) — `wms_ubicacion`

| Ruta | Método | Entidad (tabla) | Tenant (`cliente_id`) | `empresa_id` (tabla lo requiere) | RBAC |
|------|--------|-----------------|------------------------|----------------------------------|------|
| `/ubicaciones` | GET | `wms_ubicacion` | Sí | **No** | `wms.ubicacion.leer` |
| `/ubicaciones/{ubicacion_id}` | GET | `wms_ubicacion` | Sí | **No** | `wms.ubicacion.leer` |
| `/ubicaciones` | POST | `wms_ubicacion` | Sí | **No se asigna desde contexto** (y no existe en schema Create) | `wms.ubicacion.crear` |
| `/ubicaciones/{ubicacion_id}` | PUT | `wms_ubicacion` | Sí | **No** | `wms.ubicacion.actualizar` |

### 2.3 Stock por Ubicación (`/wms/stock-ubicacion`) — `wms_stock_ubicacion`

| Ruta | Método | Entidad (tabla) | Tenant (`cliente_id`) | `empresa_id` (tabla lo requiere) | RBAC |
|------|--------|-----------------|------------------------|----------------------------------|------|
| `/stock-ubicacion` | GET | `wms_stock_ubicacion` | Sí | **No** | `wms.stock_ubicacion.leer` |
| `/stock-ubicacion/{stock_ubicacion_id}` | GET | `wms_stock_ubicacion` | Sí | **No** | `wms.stock_ubicacion.leer` |
| `/stock-ubicacion` | POST | `wms_stock_ubicacion` | Sí | **No se asigna desde contexto** (y no existe en schema Create) | `wms.stock_ubicacion.crear` |
| `/stock-ubicacion/{stock_ubicacion_id}` | PUT | `wms_stock_ubicacion` | Sí | **No** | `wms.stock_ubicacion.actualizar` |

### 2.4 Tareas (`/wms/tareas`) — `wms_tarea`

| Ruta | Método | Entidad (tabla) | Tenant (`cliente_id`) | `empresa_id` (tabla lo requiere) | RBAC |
|------|--------|-----------------|------------------------|----------------------------------|------|
| `/tareas` | GET | `wms_tarea` | Sí | **No** | `wms.tarea.leer` |
| `/tareas/{tarea_id}` | GET | `wms_tarea` | Sí | **No** | **No** ⚠ (falta `require_permission`) |
| `/tareas` | POST | `wms_tarea` | Sí | **No se asigna desde contexto** (y no existe en schema Create) | `wms.tarea.crear` |
| `/tareas/{tarea_id}` | PUT | `wms_tarea` | Sí | **No** | `wms.tarea.actualizar` |

---

## 3. Brechas frente al estándar del prompt

### 3.1 Brechas estándar MAESTRO (zonas, ubicaciones)

Estándar del prompt: crear, listar, detalle, actualizar, **activar/desactivar**.

| Tabla | Crear | Listar | Detalle | Actualizar | Activar/desactivar explícito |
|-------|-------|--------|---------|------------|------------------------------|
| `wms_zona_almacen` | Sí | Sí | Sí | Sí | **No** (solo se expone `es_activo` vía PUT; no hay endpoint dedicado) |
| `wms_ubicacion` | Sí | Sí | Sí | Sí | **No** (mismo patrón) |

### 3.2 Brechas estándar TRANSACCIONAL (tareas)

Estándar del prompt: crear (borrador), actualizar (solo borrador), aprobar/procesar/anular, listar, detalle.

| Tabla | Crear | Listar | Detalle | Actualizar | Acciones (aprobar/procesar/anular) |
|-------|-------|--------|---------|------------|------------------------------------|
| `wms_tarea` | Sí | Sí | Sí | Sí | **No** (no hay endpoints de transición de estado) |

### 3.3 Brechas estándar DERIVADA / ANALÍTICA (stock por ubicación)

Estándar del prompt: **solo lectura**.

| Tabla | Lectura | Escritura detectada | Observación |
|-------|---------|----------------------|------------|
| `wms_stock_ubicacion` | Sí (GET) | **Sí** (POST/PUT) ⚠ | Según el propio SQL: “detalle de ubicación de stock de inv_stock”. Se recomienda tratarla como derivada y restringir escritura a procesos controlados (no CRUD manual). **Decisión Fase 3:** mantener POST/PUT por compatibilidad, pero marcar endpoints como **internos** (`deprecated=True`) y documentar su uso interno. |

---

## 4. Endpoints faltantes o sugeridos (Fase 3)

Sugerencias enfocadas en paridad con el prompt y refuerzo multi-tenant/multi-empresa.

| Ruta sugerida (bajo `/wms`) | Método | Motivo |
|-----------------------------|--------|--------|
| `/tareas/{tarea_id}` | GET | Agregar RBAC faltante (`wms.tarea.leer`). |
| Endpoints de activar/desactivar (p.ej. `/zonas/{id}/activar`, `/zonas/{id}/desactivar`; idem ubicaciones) | POST | Alinear “maestros” al estándar del prompt sin depender de updates parciales. |
| Acciones transaccionales explícitas para tareas (p.ej. `/tareas/{id}/asignar`, `/iniciar`, `/completar`, `/cancelar`) | POST | Alinear `wms_tarea` al patrón transaccional del prompt (hoy todo se resuelve vía `PUT`). |
| Revisión de escritura en `wms_stock_ubicacion` | — | Si se confirma como derivada, retirar/limitar POST/PUT a uso interno (sin romper contrato, podría restringirse por permisos/rol o marcar endpoints como administrativos). |

---

## 5. Campos en BD (`WMS_TABLAS.sql`) no reflejados o divergentes en schemas

Comparación contra columnas del script de referencia del módulo.

### 5.1 `wms_zona_almacen` ↔ `ZonaAlmacenCreate/Update/Read`

| Columna BD | Presente en schema | Observación |
|------------|---------------------|-------------|
| `empresa_id` (NOT NULL) | **No** (Create/Update/Read) ⚠ | La tabla lo requiere. No se ve asignación desde contexto; las inserciones quedarían incompletas. |
| `usuario_creacion_id` | Solo en Read | No se asigna en Create (podría asignarse desde usuario autenticado). |

### 5.2 `wms_ubicacion` ↔ `UbicacionCreate/Update/Read`

| Columna BD | Presente en schema | Observación |
|------------|---------------------|-------------|
| `empresa_id` (NOT NULL) | **No** (Create/Update/Read) ⚠ | La tabla lo requiere. No se ve asignación desde contexto. |
| `usuario_creacion_id` | Solo en Read | No se asigna en Create (podría asignarse desde usuario autenticado). |

### 5.3 `wms_stock_ubicacion` ↔ `StockUbicacionCreate/Update/Read`

| Columna BD | Presente en schema | Observación |
|------------|---------------------|-------------|
| `empresa_id` (NOT NULL) | **No** (Create/Update/Read) ⚠ | La tabla lo requiere. No se ve asignación desde contexto. |

### 5.4 `wms_tarea` ↔ `TareaCreate/Update/Read`

| Columna BD | Presente en schema | Observación |
|------------|---------------------|-------------|
| `empresa_id` (NOT NULL) | **No** (Create/Update/Read) ⚠ | La tabla lo requiere. No se ve asignación desde contexto. |
| `fecha_asignacion`, `fecha_inicio`, `fecha_completado` | En Update/Read | Ausentes en Create (ok si se gestionan por workflow). |

---

## 6. Problemas de tenant o RBAC (resumen)

| Problema | Severidad | Ubicación / notas |
|----------|-----------|-------------------|
| Falta de manejo de `empresa_id` (tabla lo exige) en Create/queries y schemas | **Alta** | `schemas.py` no incluye `empresa_id`; services/queries solo fuerzan `cliente_id`. En DDL y `tables_wms.py` `empresa_id` es NOT NULL en todas las tablas WMS. |
| Falta RBAC en `GET /wms/tareas/{tarea_id}` | **Alta** | `app/modules/wms/presentation/endpoints_tareas.py` no declara `require_permission` en ese endpoint. |
| `empresa_id` no se filtra/valida en list/get | Media | Todas las queries WMS filtran solo por `cliente_id`; esto debilita el aislamiento multi-empresa cuando el cliente tiene múltiples empresas. |
| Escritura sobre tabla potencialmente derivada `wms_stock_ubicacion` | Media/Alta | Existen `POST/PUT` y queries de inserción/actualización para stock por ubicación. |

---

## 7. Código marcado como revisión (no eliminar en esta fase)

- `app/modules/wms/presentation/schemas.py`: falta `empresa_id` en modelos Read y en Create/Update (si el backend debe persistirlo).  
- `app/infrastructure/database/queries/wms/*.py`: ninguna operación filtra/valida `empresa_id` a pesar de existir en las tablas.  
- `app/modules/wms/presentation/endpoints_tareas.py`: endpoint `GET /{tarea_id}` sin RBAC.

---

## 8. Checkpoint Fase 2 (respuestas cortas)

1. **Routers / services / queries:** Existe el módulo WMS completo por patrón (presentation + application + queries + tables).  
2. **Endpoints:** 16 rutas CRUD base bajo `/wms` (4 por entidad).  
3. **Brechas maestro/transaccional:** No hay endpoints explícitos de activar/desactivar; tampoco acciones transaccionales de cambio de estado.  
4. **Schemas vs BD:** Brecha crítica: `empresa_id` (NOT NULL en BD) no se expone ni se asigna desde contexto en las capas revisadas.  
5. **Tenant/RBAC:** `cliente_id` está aplicado; `empresa_id` no. Falta RBAC en `GET /wms/tareas/{id}`.

⛔ **Fin Fase 2.** Continuar con Fase 3 solo tras confirmación explícita.

