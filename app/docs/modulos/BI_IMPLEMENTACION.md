## BI — Implementación (Fase 3 completada)

Módulo: **Business Intelligence**  
Código: **BI**  
Alcance BD auditado: `docs/bd/BI_TABLAS.sql` (tabla `bi_reporte`)

### Resumen

- **Schemas**: sin cambios (ya estaban alineados con la BD del módulo).
- **Services/Queries**: se agregó **validación opcional de `empresa_id`** en operaciones por ID (GET/PUT) para `bi_reporte` (sin romper llamadas existentes).
- **Routers**:
  - se corrigió el permiso del `PUT /bi/reportes/{id}` a `bi.reporte.actualizar`
  - se agregaron endpoints `PATCH` para activar/desactivar (soft delete vía `es_activo`)
  - se habilitó `empresa_id` como **query param opcional** en GET/PUT por ID para activar la validación opcional.
- **RBAC**: se agregó seed idempotente para permisos `bi.reporte.*`.

### Tabla del módulo

- **`bi_reporte`** (maestro)
  - Multi-tenant: `cliente_id`, `empresa_id`
  - Soft delete: `es_activo`

### Endpoints (backend)

#### Existentes (se mantienen)

- **GET** `/bi/reportes`  
  - Permiso: `bi.reporte.leer`
- **GET** `/bi/reportes/{reporte_id}`  
  - Permiso: `bi.reporte.leer`  
  - Nuevo: `empresa_id` (query param opcional)
- **POST** `/bi/reportes`  
  - Permiso: `bi.reporte.crear`
- **PUT** `/bi/reportes/{reporte_id}`  
  - Permiso: **`bi.reporte.actualizar`** (corregido)  
  - Nuevo: `empresa_id` (query param opcional)

#### Nuevos (agregados)

- **PATCH** `/bi/reportes/{reporte_id}/activar`  
  - Permiso: `bi.reporte.actualizar`  
  - Efecto: `es_activo = 1` (soft activate)  
  - `empresa_id` opcional (query)
- **PATCH** `/bi/reportes/{reporte_id}/desactivar`  
  - Permiso: `bi.reporte.actualizar`  
  - Efecto: `es_activo = 0` (soft deactivate)  
  - `empresa_id` opcional (query)

### Multi-tenant y RBAC (verificación)

- **cliente_id**:
  - Se mantiene como filtro obligatorio en queries por ID y listados.
- **empresa_id**:
  - Se agregó filtro **opcional** en GET/PUT/PATCH por ID (aplica solo si se envía el parámetro).
- **RBAC**:
  - `bi.reporte.leer` aplicado en GET list/detalle
  - `bi.reporte.crear` aplicado en POST
  - `bi.reporte.actualizar` aplicado en PUT y PATCH activar/desactivar

### Seeds RBAC

Script agregado (idempotente por `MERGE`):

- `app/docs/database/SEED_PERMISOS_RBAC_BI.sql`
  - `bi.reporte.leer`
  - `bi.reporte.crear`
  - `bi.reporte.actualizar`

### Archivos modificados/creados

- Modificados:
  - `app/infrastructure/database/queries/bi/reporte_queries.py`
  - `app/modules/bi/application/services/reporte_service.py`
  - `app/modules/bi/presentation/endpoints_reporte.py`
- Creados:
  - `app/docs/modulos/AUDITORIA_BI.md`
  - `app/docs/database/SEED_PERMISOS_RBAC_BI.sql`
  - `app/docs/modulos/BI_IMPLEMENTACION.md`

