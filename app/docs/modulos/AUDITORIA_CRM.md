# Auditoría — Módulo CRM (Customer Relationship Management)

**Código:** CRM  
**Fuente de modelo de datos:** `docs/bd/CRM_TABLAS.sql` (tablas `crm_*`).  
**Metodología:** `docs/prompts/PROMPT_MODULO_MAESTRO.md` — Fase 2.

**Inventario de código CRM**

| Capa | Ubicación |
|------|-----------|
| Routers (presentation) | `app/modules/crm/presentation/endpoints.py` (agregador), `endpoints_campanas.py`, `endpoints_leads.py`, `endpoints_oportunidades.py`, `endpoints_actividades.py` |
| Schemas | `app/modules/crm/presentation/schemas.py` |
| Servicios (application) | `app/modules/crm/application/services/campana_service.py`, `lead_service.py`, `oportunidad_service.py`, `actividad_service.py`, `__init__.py` |
| Consultas SQL (infraestructura) | `app/infrastructure/database/queries/crm/campana_queries.py`, `lead_queries.py`, `oportunidad_queries.py`, `actividad_queries.py`, `__init__.py` |
| Tablas Core (ORM metadata) | `app/infrastructure/database/tables_erp/tables_crm.py` |
| Repositories dedicados en `app/modules/crm/` | No hay carpeta `repositories`; persistencia vía queries en infraestructura |

Prefijo API registrado: **`/crm`** (`app/api/v1/api.py`).

---

## 1. Tablas detectadas y su tipo

| Tabla | Tipo (prompt) |
|-------|----------------|
| `crm_campana` | Maestro |
| `crm_lead` | Maestro |
| `crm_oportunidad` | Transaccional (pipeline comercial) |
| `crm_actividad` | Transaccional (seguimiento/bitácora) |

No se observan tablas derivadas/analíticas (solo una columna calculada `valor_ponderado` en `crm_oportunidad`).

**Nota de consistencia modelo código vs SQL de referencia:** En `docs/bd/CRM_TABLAS.sql` (y también en `app/docs/database/3.- TABLAS_BD_ERP_COMPLETO_FASE4.sql`) las tablas `crm_campana` y `crm_oportunidad` definen **`moneda_id`** (UUID, FK `cat_moneda`). En el código actual (`tables_crm.py` + `schemas.py`) se usa **`moneda`** (`String(3)` / texto ISO). La auditoría de campos contrasta contra el **SQL de referencia del módulo**; si la base desplegada coincide con ese script, hay desalineación a corregir en la capa de aplicación (sin cambiar DDL).

---

## 2. Endpoints existentes

Criterios: **tenant** = uso de `cliente_id` del usuario autenticado en servicio/query (y, cuando aplica, filtro o validación de `empresa_id`). **RBAC** = presencia de `Depends(require_permission(...))` en la ruta.

Rutas relativas a **`/crm`** (el router agregador monta `campanas`, `leads`, `oportunidades`, `actividades`).

### 2.1 Campañas (`/crm/campanas`)

| Ruta | Método | Entidad (tabla) | Tenant (`cliente_id`) | `empresa_id` | RBAC |
|------|--------|-----------------|------------------------|--------------|------|
| `/campanas` | GET | `crm_campana` | Sí (servicio + queries) | Opcional por query | `crm.campana.leer` |
| `/campanas/{campana_id}` | GET | `crm_campana` | Sí | No valida explícito (depende del row) | `crm.campana.leer` |
| `/campanas` | POST | `crm_campana` | Sí | En body (`CampanaCreate.empresa_id`) | `crm.campana.crear` |
| `/campanas/{campana_id}` | PUT | `crm_campana` | Sí | No valida explícito (depende del row) | `crm.campana.actualizar` |

### 2.2 Leads (`/crm/leads`)

| Ruta | Método | Entidad (tabla) | Tenant (`cliente_id`) | `empresa_id` | RBAC |
|------|--------|-----------------|------------------------|--------------|------|
| `/leads` | GET | `crm_lead` | Sí | Opcional por query | `crm.lead.leer` |
| `/leads/{lead_id}` | GET | `crm_lead` | Sí | No valida explícito (depende del row) | `crm.lead.leer` |
| `/leads` | POST | `crm_lead` | Sí | En body (`LeadCreate.empresa_id`) | `crm.lead.crear` |
| `/leads/{lead_id}` | PUT | `crm_lead` | Sí | No valida explícito (depende del row) | `crm.lead.actualizar` |

### 2.3 Oportunidades (`/crm/oportunidades`)

| Ruta | Método | Entidad (tabla) | Tenant (`cliente_id`) | `empresa_id` | RBAC |
|------|--------|-----------------|------------------------|--------------|------|
| `/oportunidades` | GET | `crm_oportunidad` | Sí | Opcional por query | `crm.oportunidad.leer` |
| `/oportunidades/{oportunidad_id}` | GET | `crm_oportunidad` | Sí | No valida explícito (depende del row) | `crm.oportunidad.leer` |
| `/oportunidades` | POST | `crm_oportunidad` | Sí | En body (`OportunidadCreate.empresa_id`) | `crm.oportunidad.crear` |
| `/oportunidades/{oportunidad_id}` | PUT | `crm_oportunidad` | Sí | No valida explícito (depende del row) | `crm.oportunidad.actualizar` |

### 2.4 Actividades (`/crm/actividades`)

| Ruta | Método | Entidad (tabla) | Tenant (`cliente_id`) | `empresa_id` | RBAC |
|------|--------|-----------------|------------------------|--------------|------|
| `/actividades` | GET | `crm_actividad` | Sí | Opcional por query | `crm.actividad.leer` |
| `/actividades/{actividad_id}` | GET | `crm_actividad` | Sí | No valida explícito (depende del row) | `crm.actividad.leer` |
| `/actividades` | POST | `crm_actividad` | Sí | En body (`ActividadCreate.empresa_id`) | `crm.actividad.crear` |
| `/actividades/{actividad_id}` | PUT | `crm_actividad` | Sí | No valida explícito (depende del row) | `crm.actividad.actualizar` |

---

## 3. Brechas frente al estándar del prompt

### 3.1 Brechas estándar MAESTRO (campañas, leads)

Estándar del prompt: crear, listar, detalle, actualizar, **activar/desactivar**.

| Tabla | Crear | Listar | Detalle | Actualizar | Activar/desactivar explícito |
|-------|-------|--------|---------|------------|------------------------------|
| `crm_campana` | Sí | Sí | Sí | Sí | **No aplicable con el SQL de referencia:** no existe `es_activo` en tabla; solo puede gestionarse “estado” (`planificada/activa/…`). |
| `crm_lead` | Sí | Sí | Sí | Sí | **No aplicable con el SQL de referencia:** no existe `es_activo`; el ciclo de vida está en `estado` (`nuevo/contactado/…`). |

### 3.2 Brechas estándar TRANSACCIONAL (oportunidades, actividades)

Estándar del prompt: crear (borrador), actualizar (solo borrador), aprobar/procesar/anular, listar, detalle.

| Tabla | Crear | Listar | Detalle | Actualizar | Acciones (aprobar/procesar/anular) |
|-------|-------|--------|---------|------------|------------------------------------|
| `crm_oportunidad` | Sí (`POST`) | Sí (`GET`) | Sí | Sí (`PUT`) | **No** (no existen endpoints de transición; se modifica `estado/etapa` vía `PUT`) |
| `crm_actividad` | Sí | Sí | Sí | Sí | **No** (solo `PUT` para estado/fecha_completado, etc.) |

---

## 4. Endpoints faltantes o sugeridos (Fase 3)

Sin asumir requerimientos funcionales adicionales, las sugerencias se enfocan en **paridad con el prompt** y **refuerzo multi-tenant/multi-empresa**:

| Ruta sugerida (bajo `/crm`) | Método | Motivo |
|-----------------------------|--------|--------|
| `/campanas/{campana_id}` con validación opcional `empresa_id` (query) | GET | Refuerzo de alcance por empresa (patrón visto en otros módulos), sin cambiar contrato base (solo parámetro opcional). |
| `/leads/{lead_id}` con validación opcional `empresa_id` (query) | GET | Igual criterio. |
| `/oportunidades/{oportunidad_id}` con validación opcional `empresa_id` (query) | GET | Igual criterio. |
| `/actividades/{actividad_id}` con validación opcional `empresa_id` (query) | GET | Igual criterio. |
| Acciones transaccionales explícitas (p.ej. `/oportunidades/{id}/marcar-ganada`, `/marcar-perdida`, `/cancelar`) | POST | Si se decide alinear CRM al patrón transaccional del prompt, hoy no existe capa de endpoints de transición; actualmente todo se hace con `PUT`. |

> Nota: activar/desactivar estilo `es_activo` no aplica a CRM según el SQL de referencia (no existe columna). No se sugiere inventar endpoints que dependan de `es_activo`.

---

## 5. Campos en BD (`CRM_TABLAS.sql`) no reflejados o divergentes en schemas

Comparación explícita contra columnas del script de referencia del módulo.

### 5.1 `crm_campana` ↔ `CampanaCreate` / `Update` / `Read`

| Columna / contrato BD | Observación |
|------------------------|-------------|
| `moneda_id (UNIQUEIDENTIFIER)` | En el SQL de referencia existe **`moneda_id`** (FK `cat_moneda`). Los schemas y ORM usan **`moneda`** (`str` de 3 chars). Hay **divergencia nombre/tipo** respecto al script. |
| `gasto_real`, métricas (`total_*`, `monto_ventas_cerradas`) | En BD existen; `CampanaRead` los incluye. En `CampanaCreate` no están (correcto si se calculan/actualizan). |

### 5.2 `crm_lead` ↔ `LeadCreate` / `Update` / `Read`

No se detectan brechas fuertes de columnas (nombres y tipos son consistentes a nivel schema), salvo validaciones que dependen del dominio (p.ej. rangos/enum).

### 5.3 `crm_oportunidad` ↔ `OportunidadCreate` / `Update` / `Read`

| Columna / contrato BD | Observación |
|------------------------|-------------|
| `moneda_id (UNIQUEIDENTIFIER)` | Igual problema que campañas: en BD referencia es `moneda_id`; en código es `moneda` texto. |
| `valor_ponderado (AS … PERSISTED)` | Existe en BD como columna calculada; **no está en `OportunidadRead`** (lectura incompleta frente a la tabla). |

### 5.4 `crm_actividad` ↔ `ActividadCreate` / `Update` / `Read`

No se detectan brechas fuertes de columnas (nombres y tipos son consistentes a nivel schema).

---

## 6. Problemas de tenant o RBAC (resumen)

| Problema | Severidad | Ubicación / notas |
|----------|-----------|-------------------|
| Divergencia `moneda` vs `moneda_id` (BD referencia) | Alta (si BD = script) | `docs/bd/CRM_TABLAS.sql` vs `app/infrastructure/database/tables_erp/tables_crm.py` + `app/modules/crm/presentation/schemas.py` + queries CRM. |
| Validación explícita de `empresa_id` en endpoints `GET /{id}` | Media | `GET /campanas/{id}`, `GET /leads/{id}`, `GET /oportunidades/{id}`, `GET /actividades/{id}` no aceptan/validan `empresa_id`; el aislamiento recae en `cliente_id` y en el valor guardado en la fila. |
| RBAC | Baja | En CRM todos los endpoints revisados aplican `require_permission` con patrón `crm.<recurso>.<accion>`. |
| Tenant (`cliente_id`) | Baja | Las queries CRM filtran por `cliente_id` en todas las operaciones (list/get/create/update). |

---

## 7. Código marcado como revisión (no eliminar en esta fase)

- `app/infrastructure/database/tables_erp/tables_crm.py` define `moneda` como `String(3)` y omite `moneda_id`; esto contradice el SQL de referencia del módulo. Si la BD real del entorno sigue `CRM_TABLAS.sql`, la capa de aplicación/ORM/schemas requiere ajuste en Fase 3 (sin tocar DDL).
- `schemas.py` usa `moneda: str` y default `"PEN"` en create; esto no existe como columna en el SQL de referencia (allí es `moneda_id`).

---

## 8. Checkpoint Fase 2 (respuestas cortas)

1. **Routers / services / queries:** Existe el módulo CRM completo por patrón (presentation + application + queries + tables).  
2. **Endpoints:** 16 rutas CRUD base bajo `/crm` (4 por entidad).  
3. **Brechas maestro/transaccional:** No hay endpoints explícitos de activar/desactivar (no existe `es_activo`), ni transiciones tipo “aprobar/procesar/anular” para oportunidades/actividades (todo vía `PUT`).  
4. **Schemas vs BD:** Principal brecha: `moneda_id` (BD referencia) vs `moneda` (código). Adicional: `valor_ponderado` (BD) no está en `OportunidadRead`.  
5. **Tenant/RBAC:** `cliente_id` aplicado en queries; RBAC presente en todos los endpoints CRM revisados.

⛔ **Fin Fase 2.** Continuar con Fase 3 solo tras confirmación explícita.

