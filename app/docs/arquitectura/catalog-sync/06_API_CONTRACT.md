# 06 — Contrato API (OpenAPI Esperado)

**Fecha:** 2026-07-02  
**Estado:** Diseño oficial — **sin implementación**  
**Base path:** `/api/v1/catalogos-globales`  
**Tag OpenAPI:** `Catálogos Globales (Super Admin)`  
**Autenticación:** Bearer JWT — `user_type=platform_admin`

---

## 1. Resumen de endpoints

10 endpoints POST — 5 catálogos × 2 modalidades:

| # | Método | Path | Modalidad |
|---|--------|------|-----------|
| 1 | POST | `/monedas/sync/{cliente_id}` | A — Individual |
| 2 | POST | `/monedas/sync` | B — Todos |
| 3 | POST | `/paises/sync/{cliente_id}` | A — Individual |
| 4 | POST | `/paises/sync` | B — Todos |
| 5 | POST | `/departamentos/sync/{cliente_id}` | A — Individual |
| 6 | POST | `/departamentos/sync` | B — Todos |
| 7 | POST | `/provincias/sync/{cliente_id}` | A — Individual |
| 8 | POST | `/provincias/sync` | B — Todos |
| 9 | POST | `/distritos/sync/{cliente_id}` | A — Individual |
| 10 | POST | `/distritos/sync` | B — Todos |

**Montaje:** `endpoints_catalog_sync.py` incluido en `api_router` con prefix `/catalogos-globales` (mismo router padre que CRUD existente o sub-router dedicado).

---

## 2. RBAC y autorización

| Capa | Mecanismo |
|------|-----------|
| Decorador | `@require_super_admin()` |
| Tipo usuario | `platform_admin` |
| Permiso granular | **No requerido** en v1 — coherente con CRUD `/catalogos-globales/*` existente |
| Impersonación | **Bloqueada** — sync es operación CP; no ejecutar bajo contexto impersonation |

---

## 3. Schemas Pydantic

### 3.1 `CatalogSyncCounts`

```json
{
  "inserted": 0,
  "updated": 0,
  "skipped": 0,
  "deactivated": 0,
  "platform_total": 0,
  "dedicated_before": 0
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `inserted` | `int ≥ 0` | Filas INSERT con PK Platform |
| `updated` | `int ≥ 0` | Filas UPDATE por diff |
| `skipped` | `int ≥ 0` | Filas idénticas |
| `deactivated` | `int ≥ 0` | SOFT_DEACTIVATE (huérfanas o alineación `es_activo`) |
| `platform_total` | `int ≥ 0` | Filas leídas de Platform |
| `dedicated_before` | `int ≥ 0` | Filas en dedicated antes del sync |

### 3.2 `CatalogSyncResult` (Modalidad A)

```json
{
  "catalog": "moneda",
  "cliente_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "database_name": "erp_cliente_acme",
  "status": "completed",
  "counts": {
    "inserted": 3,
    "updated": 1,
    "skipped": 10,
    "deactivated": 0,
    "platform_total": 14,
    "dedicated_before": 11
  },
  "duration_ms": 245,
  "error": null
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `catalog` | `enum` | `moneda` \| `pais` \| `departamento` \| `provincia` \| `distrito` |
| `cliente_id` | `UUID` | Tenant dedicated objetivo |
| `database_name` | `string` | BD dedicada resuelta |
| `status` | `enum` | `completed` \| `failed` |
| `counts` | `CatalogSyncCounts` | Solo si `status=completed` |
| `duration_ms` | `int` | Duración ejecución |
| `error` | `CatalogSyncErrorDetail \| null` | Solo si `status=failed` |

### 3.3 `CatalogSyncTenantOutcome` (item batch)

```json
{
  "cliente_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "codigo_cliente": "ACME",
  "database_name": "erp_cliente_acme",
  "status": "completed",
  "counts": { "inserted": 3, "updated": 0, "skipped": 11, "deactivated": 0, "platform_total": 14, "dedicated_before": 11 },
  "duration_ms": 198,
  "error": null
}
```

### 3.4 `CatalogSyncBatchResult` (Modalidad B)

```json
{
  "catalog": "moneda",
  "status": "partial",
  "tenants_total": 5,
  "tenants_completed": 4,
  "tenants_failed": 1,
  "aggregated_counts": {
    "inserted": 12,
    "updated": 2,
    "skipped": 40,
    "deactivated": 1,
    "platform_total": 14,
    "dedicated_before": null
  },
  "outcomes": [
    {
      "cliente_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "codigo_cliente": "ACME",
      "database_name": "erp_cliente_acme",
      "status": "completed",
      "counts": { "inserted": 3, "updated": 0, "skipped": 11, "deactivated": 0, "platform_total": 14, "dedicated_before": 11 },
      "duration_ms": 198,
      "error": null
    }
  ],
  "duration_ms": 1024
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `status` | `enum` | `completed` \| `partial` \| `failed` |
| `tenants_total` | `int` | Dedicated elegibles |
| `tenants_completed` | `int` | Sync exitosos |
| `tenants_failed` | `int` | Sync fallidos |
| `aggregated_counts` | `CatalogSyncCounts` | Suma de conteos por tenant (`dedicated_before` = `null`) |
| `outcomes` | `list[CatalogSyncTenantOutcome]` | Detalle por tenant |
| `duration_ms` | `int` | Duración total batch |

**Semántica `status` batch:**

| Valor | Condición |
|-------|-----------|
| `completed` | `tenants_failed = 0` y `tenants_total > 0` |
| `partial` | `tenants_completed > 0` y `tenants_failed > 0` |
| `failed` | `tenants_completed = 0` y `tenants_total > 0` |
| `completed` | `tenants_total = 0` (sin dedicated — ver §5.4) |

### 3.5 `CatalogSyncErrorDetail`

```json
{
  "internal_code": "CATALOG_SYNC_FK_PREREQUISITE",
  "message": "Faltan registros padre en dedicated antes de sincronizar departamentos.",
  "details": {
    "missing_pais_ids": ["7c9e6679-7425-40de-944b-e07fc1f90ae7"]
  }
}
```

---

## 4. Contrato por endpoint

### 4.1 Monedas — Individual

```
POST /api/v1/catalogos-globales/monedas/sync/{cliente_id}
```

| Aspecto | Valor |
|---------|-------|
| `operationId` | `sync_monedas_dedicated_cliente` |
| Path params | `cliente_id: UUID` |
| Request body | **Vacío** — sin body |
| Response 200 | `CatalogSyncResult` |
| Tabla destino | `cat_moneda` |

**Ejemplo response 200:**

```json
{
  "catalog": "moneda",
  "cliente_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "database_name": "erp_cliente_demo",
  "status": "completed",
  "counts": {
    "inserted": 5,
    "updated": 0,
    "skipped": 0,
    "deactivated": 0,
    "platform_total": 5,
    "dedicated_before": 0
  },
  "duration_ms": 312,
  "error": null
}
```

---

### 4.2 Monedas — Todos

```
POST /api/v1/catalogos-globales/monedas/sync
```

| Aspecto | Valor |
|---------|-------|
| `operationId` | `sync_monedas_all_dedicated` |
| Request body | **Vacío** |
| Response 200 | `CatalogSyncBatchResult` |

---

### 4.3 Países — Individual

```
POST /api/v1/catalogos-globales/paises/sync/{cliente_id}
```

| Aspecto | Valor |
|---------|-------|
| `operationId` | `sync_paises_dedicated_cliente` |
| Response 200 | `CatalogSyncResult` (`catalog=pais`) |
| Tabla destino | `cat_pais` |

---

### 4.4 Países — Todos

```
POST /api/v1/catalogos-globales/paises/sync
```

| Aspecto | Valor |
|---------|-------|
| `operationId` | `sync_paises_all_dedicated` |
| Response 200 | `CatalogSyncBatchResult` (`catalog=pais`) |

---

### 4.5 Departamentos — Individual

```
POST /api/v1/catalogos-globales/departamentos/sync/{cliente_id}
```

| Aspecto | Valor |
|---------|-------|
| `operationId` | `sync_departamentos_dedicated_cliente` |
| Response 200 | `CatalogSyncResult` (`catalog=departamento`) |
| Tabla destino | `cat_departamento` |
| Prerequisito | `cat_pais` sincronizado en dedicated |

---

### 4.6 Departamentos — Todos

```
POST /api/v1/catalogos-globales/departamentos/sync
```

| Aspecto | Valor |
|---------|-------|
| `operationId` | `sync_departamentos_all_dedicated` |
| Response 200 | `CatalogSyncBatchResult` |

---

### 4.7 Provincias — Individual

```
POST /api/v1/catalogos-globales/provincias/sync/{cliente_id}
```

| Aspecto | Valor |
|---------|-------|
| `operationId` | `sync_provincias_dedicated_cliente` |
| Tabla destino | `cat_provincia` |
| Prerequisito | `cat_departamento` sincronizado |

---

### 4.8 Provincias — Todos

```
POST /api/v1/catalogos-globales/provincias/sync
```

| Aspecto | Valor |
|---------|-------|
| `operationId` | `sync_provincias_all_dedicated` |
| Response 200 | `CatalogSyncBatchResult` |

---

### 4.9 Distritos — Individual

```
POST /api/v1/catalogos-globales/distritos/sync/{cliente_id}
```

| Aspecto | Valor |
|---------|-------|
| `operationId` | `sync_distritos_dedicated_cliente` |
| Tabla destino | `cat_distrito` |
| Prerequisito | `cat_provincia` sincronizado |

---

### 4.10 Distritos — Todos

```
POST /api/v1/catalogos-globales/distritos/sync
```

| Aspecto | Valor |
|---------|-------|
| `operationId` | `sync_distritos_all_dedicated` |
| Response 200 | `CatalogSyncBatchResult` |

---

## 5. Códigos HTTP y errores

### 5.1 Modalidad A (individual)

| HTTP | Condición | `internal_code` | Body |
|------|-----------|-----------------|------|
| **200** | Sync completado | — | `CatalogSyncResult status=completed` |
| **200** | Sync falló en motor (opción A) | — | `CatalogSyncResult status=failed` + `error` |
| **403** | No superadmin | `AUTHORIZATION_ERROR` | `detail` estándar |
| **404** | `cliente_id` no existe | `NOT_FOUND` | Cliente no encontrado |
| **422** | Tenant no dedicated | `CLIENT_NOT_DEDICATED` | — |
| **422** | Cliente inactivo | `CLIENT_INACTIVE` | — |
| **422** | Sin `cliente_conexion` | `DEDICATED_CONNECTION_NOT_FOUND` | — |
| **422** | FK prerequisito | `CATALOG_SYNC_FK_PREREQUISITE` | `details.missing_*_ids` |
| **503** | Dedicated no alcanzable | `DEDICATED_UNREACHABLE` | — |
| **409** | Error SQL / UNIQUE en dedicated | `CATALOG_SYNC_APPLY_FAILED` | Mensaje mapeado — sin SQL crudo |

**Decisión contrato:** Preferir **422/404/503** para errores pre-sync (orchestrator) y **409** para fallos transaccionales dedicated. Si el motor captura error interno en modalidad A, puede retornar **200 + status=failed** (coherente con batch parcial) — implementación debe ser consistente en los 10 endpoints.

### 5.2 Modalidad B (todos)

| HTTP | Condición |
|------|-----------|
| **200** | Siempre que la orquestación batch termine (incluso con fallos parciales) |
| **403** | No superadmin |
| **200** + `tenants_total=0` | No hay clientes dedicated activos — no es error |

Errores por tenant se encapsulan en `outcomes[].error`; no elevan HTTP 4xx/5xx del request completo salvo 403.

### 5.3 Catálogo `CatalogSyncErrorDetail.internal_code`

| Código | Descripción |
|--------|-------------|
| `CLIENT_NOT_DEDICATED` | `tipo_instalacion != dedicated` |
| `CLIENT_INACTIVE` | `cliente.es_activo = 0` |
| `DEDICATED_CONNECTION_NOT_FOUND` | Sin conexión activa |
| `DEDICATED_UNREACHABLE` | Timeout / error conexión dedicated |
| `CATALOG_SYNC_FK_PREREQUISITE` | Padres ausentes en dedicated |
| `CATALOG_SYNC_APPLY_FAILED` | Rollback TX — error SQL mapeado |
| `PLATFORM_CATALOG_READ_FAILED` | Error lectura SSOT |
| `DEDICATED_CATALOG_READ_FAILED` | Error lectura snapshot dedicated |

### 5.4 Ejemplo error 422 — FK prerequisito

```json
{
  "detail": "No se puede sincronizar departamentos: faltan países referenciados en dedicated.",
  "internal_code": "CATALOG_SYNC_FK_PREREQUISITE",
  "details": {
    "catalog": "departamento",
    "missing_pais_ids": [
      "7c9e6679-7425-40de-944b-e07fc1f90ae7"
    ]
  }
}
```

### 5.5 Ejemplo batch parcial 200

```json
{
  "catalog": "distrito",
  "status": "partial",
  "tenants_total": 3,
  "tenants_completed": 2,
  "tenants_failed": 1,
  "aggregated_counts": {
    "inserted": 1872,
    "updated": 0,
    "skipped": 0,
    "deactivated": 0,
    "platform_total": 1872,
    "dedicated_before": null
  },
  "outcomes": [
    {
      "cliente_id": "aaa-bbb-ccc",
      "codigo_cliente": "TENANT_A",
      "database_name": "erp_tenant_a",
      "status": "completed",
      "counts": { "inserted": 936, "updated": 0, "skipped": 0, "deactivated": 0, "platform_total": 936, "dedicated_before": 0 },
      "duration_ms": 890,
      "error": null
    },
    {
      "cliente_id": "ddd-eee-fff",
      "codigo_cliente": "TENANT_B",
      "database_name": "erp_tenant_b",
      "status": "failed",
      "counts": null,
      "duration_ms": 45,
      "error": {
        "internal_code": "CATALOG_SYNC_FK_PREREQUISITE",
        "message": "Faltan provincias en dedicated.",
        "details": { "missing_provincia_ids": ["..."] }
      }
    }
  ],
  "duration_ms": 2100
}
```

---

## 6. OpenAPI — fragmento esperado

```yaml
paths:
  /api/v1/catalogos-globales/monedas/sync/{cliente_id}:
    post:
      tags: [Catálogos Globales (Super Admin)]
      operationId: sync_monedas_dedicated_cliente
      summary: Sincronizar cat_moneda hacia un cliente Dedicated
      parameters:
        - name: cliente_id
          in: path
          required: true
          schema: { type: string, format: uuid }
      responses:
        '200':
          description: Resultado de sincronización
          content:
            application/json:
              schema: { $ref: '#/components/schemas/CatalogSyncResult' }
        '403': { description: Sin permiso superadmin }
        '404': { description: Cliente no encontrado }
        '422': { description: Validación pre-sync }
        '503': { description: Dedicated no alcanzable }

  /api/v1/catalogos-globales/monedas/sync:
    post:
      tags: [Catálogos Globales (Super Admin)]
      operationId: sync_monedas_all_dedicated
      summary: Sincronizar cat_moneda hacia todos los clientes Dedicated
      responses:
        '200':
          content:
            application/json:
              schema: { $ref: '#/components/schemas/CatalogSyncBatchResult' }
```

*(Repetir patrón para `paises`, `departamentos`, `provincias`, `distritos`.)*

---

## 7. Idempotencia (contrato comportamental)

| Escenario | Resultado esperado HTTP 200 |
|-----------|----------------------------|
| Segunda ejecución sin cambios Platform | `inserted=0`, `updated=0`, `skipped=platform_total` |
| Platform añade fila | `inserted=1` |
| Platform modifica nombre | `updated=1` |
| Platform desactiva fila | `updated=1` (o `skipped` si dedicated ya `es_activo=0` y resto igual) |
| Dedicated tiene fila huérfana | `deactivated=1` |

Sin metadata persistente — idempotencia verificable solo por conteos de respuesta y estado DB.

---

## 8. Compatibilidad con CRUD existente

| Endpoint existente | Relación |
|--------------------|----------|
| `GET/POST/PUT/DELETE /catalogos-globales/monedas` | CRUD Platform SSOT — independiente |
| `POST …/monedas/sync*` | Réplica hacia dedicated — no modifica CRUD |

**Regla operativa:** Superadmin no debe usar CRUD `/catalogos-globales/*` con `cliente_id` de tenant dedicated para mutar `cat_*` — solo sync.
