# Implementación — Módulo CRM (Customer Relationship Management)

**Código:** CRM  
**Stack:** FastAPI + SQL Server (multi-tenant)  
**Modelo de datos (referencia):** `docs/bd/CRM_TABLAS.sql` (tablas `crm_*`)  
**Auditoría:** `app/docs/modulos/AUDITORIA_CRM.md`

---

## 1) Alcance del módulo (tablas `CRM_`)

Tablas del módulo (prefijo `crm_`):

- `crm_campana` (maestro)
- `crm_lead` (maestro)
- `crm_oportunidad` (pipeline comercial)
- `crm_actividad` (seguimiento/bitácora)

Notas BD relevantes:
- Todas las tablas tienen `cliente_id` y `empresa_id`.
- `crm_campana.moneda_id` y `crm_oportunidad.moneda_id` existen como FK a `cat_moneda(moneda_id)`.
- `crm_oportunidad.valor_ponderado` es columna calculada persistida: `monto_estimado * probabilidad_cierre / 100`.

---

## 2) Routers / prefijos / endpoints

Prefijo API:
- `/crm` en `app/api/v1/api.py`

Agregador:
- `app/modules/crm/presentation/endpoints.py` incluye:
  - `/campanas`
  - `/leads`
  - `/oportunidades`
  - `/actividades`

### 2.1 Endpoints existentes (sin cambio de contrato)

Para cada recurso (`campana`, `lead`, `oportunidad`, `actividad`):
- `GET /crm/<recurso>` (listado con filtros)
- `GET /crm/<recurso>/{id}` (detalle)
- `POST /crm/<recurso>` (creación)
- `PUT /crm/<recurso>/{id}` (actualización)

### 2.2 Endpoints nuevos (lifecycle de oportunidades)

Se añadieron endpoints **sin modificar ni eliminar** rutas existentes:

- `POST /crm/oportunidades/{oportunidad_id}/marcar-ganada`
- `POST /crm/oportunidades/{oportunidad_id}/marcar-perdida`
- `POST /crm/oportunidades/{oportunidad_id}/cancelar`

Reglas aplicadas:
- Solo permiten transición si `estado` actual es `abierta` (409 si no).
- Idempotentes: si ya está en el estado destino, retornan la oportunidad actual.
- Actualizan `fecha_cierre_real` (por defecto hoy), `fecha_cambio_etapa` y llevan `etapa` a `cierre` preservando `etapa_anterior` cuando corresponde.
- Reutilizan permiso RBAC existente `crm.oportunidad.actualizar`.

---

## 3) Multi-tenant (cliente_id / empresa_id)

### 3.1 cliente_id (obligatorio)

- Todas las operaciones en queries filtran por `cliente_id` (tenant estricto).
- En `POST`, `cliente_id` se asigna desde `current_user.cliente_id` (no desde body).

### 3.2 empresa_id (validación opcional en GET por ID)

Se incorporó `empresa_id` como filtro **opcional** en los endpoints `GET /{id}` para:
- campañas, leads, oportunidades, actividades

Comportamiento:
- Si `empresa_id` se envía, el recurso debe pertenecer a esa empresa (además de `cliente_id`).
- Si no se envía, se mantiene el comportamiento existente (solo `cliente_id` + id).

---

## 4) RBAC (permisos)

Patrón aplicado en endpoints:
- `Depends(require_permission("crm.<recurso>.<accion>"))`

### 4.1 Seed de permisos CRM

Se agregó script idempotente (MERGE por código) para entornos limpios:
- `app/docs/database/SEED_PERMISOS_RBAC_CRM.sql`

Permisos incluidos (los usados por endpoints del backend CRM):
- `crm.campana.{leer,crear,actualizar}`
- `crm.lead.{leer,crear,actualizar}`
- `crm.oportunidad.{leer,crear,actualizar}`
- `crm.actividad.{leer,crear,actualizar}`

Nota:
- Los endpoints nuevos de lifecycle reutilizan `crm.oportunidad.actualizar`, por lo que **no** se crearon permisos adicionales.

---

## 5) Alineación BD ↔ ORM ↔ Schemas

### 5.1 Corrección `moneda` vs `moneda_id` (sin modificar DDL)

Se alineó el backend a `CRM_TABLAS.sql`:
- `crm_campana`: se usa `moneda_id: UUID`
- `crm_oportunidad`: se usa `moneda_id: UUID`

Impacto:
- ORM (`tables_crm.py`) y schemas (`schemas.py`) quedaron consistentes con la BD de referencia.

### 5.2 `valor_ponderado`

- Se expone en `OportunidadRead` como `valor_ponderado`.
- En ORM se modela como `Computed(..., persisted=True)` (columna calculada persistida).

---

## 6) Archivos creados / modificados

### 6.1 Creados

- `app/docs/modulos/AUDITORIA_CRM.md`
- `app/docs/database/SEED_PERMISOS_RBAC_CRM.sql`
- `app/docs/modulos/CRM_IMPLEMENTACION.md`

### 6.2 Modificados

- `app/infrastructure/database/tables_erp/tables_crm.py`
- `app/modules/crm/presentation/schemas.py`
- `app/infrastructure/database/queries/crm/campana_queries.py`
- `app/infrastructure/database/queries/crm/lead_queries.py`
- `app/infrastructure/database/queries/crm/oportunidad_queries.py`
- `app/infrastructure/database/queries/crm/actividad_queries.py`
- `app/modules/crm/application/services/campana_service.py`
- `app/modules/crm/application/services/lead_service.py`
- `app/modules/crm/application/services/oportunidad_service.py`
- `app/modules/crm/application/services/actividad_service.py`
- `app/modules/crm/application/services/__init__.py`
- `app/modules/crm/presentation/endpoints_campanas.py`
- `app/modules/crm/presentation/endpoints_leads.py`
- `app/modules/crm/presentation/endpoints_oportunidades.py`
- `app/modules/crm/presentation/endpoints_actividades.py`

---

## 7) Verificación final (checklist)

- **Contratos existentes**: no se eliminaron rutas ni se cambiaron métodos existentes; se agregaron rutas nuevas para lifecycle y se añadió `empresa_id` como query param opcional en `GET /{id}`.
- **Tenant**: `cliente_id` aplicado en todas las queries.
- **Empresa**: `empresa_id` validable opcionalmente en `GET /{id}`.
- **RBAC**: todos los endpoints CRM revisados usan `require_permission` con patrón `crm.<recurso>.<accion>`.
- **DDL**: no se modificó estructura de BD; cambios solo en capa aplicación (schemas/ORM/queries/routers) y seeds RBAC.

