# 07 — Diagramas de Secuencia

**Fecha:** 2026-07-02  
**Estado:** Diseño oficial — **sin implementación**  
**Referencia:** `05_IMPLEMENTATION_ARCHITECTURE.md`, `06_API_CONTRACT.md`

---

## 1. Sync Individual (Modalidad A)

Sincronización de **un catálogo** hacia **un cliente Dedicated**.

```mermaid
sequenceDiagram
    autonumber
    actor Op as Platform Admin
    participant API as endpoints_catalog_sync
    participant Orch as CatalogSyncOrchestrator
    participant CP as BD Central
    participant Svc as CatalogSyncService
    participant Reader as PlatformCatalogReader
    participant Core as catalog_sync_core
    participant Writer as DedicatedCatalogWriter
    participant Plat as BD ERP Shared
    participant Ded as BD Dedicated

    Op->>API: POST /catalogos-globales/{recurso}/sync/{cliente_id}
    API->>API: @require_super_admin()
    API->>Orch: sync_one(cliente_id, catalog)

    Orch->>CP: SELECT cliente, cliente_conexion
    alt cliente no existe
        Orch-->>API: 404
        API-->>Op: Cliente no encontrado
    else no dedicated / inactivo / sin conexión
        Orch-->>API: 422
        API-->>Op: Error validación
    else prerequisito FK no cumplido
        Orch-->>API: 422 CATALOG_SYNC_FK_PREREQUISITE
        API-->>Op: Faltan padres en dedicated
    end

    Orch->>Svc: run(cliente_id, catalog, database_name)

    Svc->>Reader: fetch_all(catalog)
    Reader->>Plat: SELECT cat_*
    Plat-->>Reader: rows_platform[]
    Reader-->>Svc: rows_platform[]

    Svc->>Writer: fetch_all(catalog, database_name)
    Writer->>Ded: SELECT cat_*
    Ded-->>Writer: rows_dedicated[]
    Writer-->>Svc: rows_dedicated[]

    Svc->>Core: compute_sync_plan(platform, dedicated, catalog)
    Core-->>Svc: plan[] (INSERT|UPDATE|SKIP|SOFT_DEACTIVATE)

    Svc->>Writer: apply_plan(plan) [BEGIN TX]
    loop cada entrada del plan
        Writer->>Ded: INSERT / UPDATE
    end
    Writer->>Ded: COMMIT
    Ded-->>Writer: OK
    Writer-->>Svc: counts

    Svc-->>Orch: CatalogSyncResult
    Orch-->>API: CatalogSyncResult
    API-->>Op: 200 JSON
```

---

## 2. Sync Todos (Modalidad B)

Sincronización del **mismo catálogo** hacia **todos** los clientes Dedicated. Sin lógica de diff propia — solo iteración.

```mermaid
sequenceDiagram
    autonumber
    actor Op as Platform Admin
    participant API as endpoints_catalog_sync
    participant Orch as CatalogSyncOrchestrator
    participant CP as BD Central
    participant Svc as CatalogSyncService
    participant Ded as BD Dedicated

    Op->>API: POST /catalogos-globales/{recurso}/sync
    API->>API: @require_super_admin()
    API->>Orch: sync_all(catalog)

    Orch->>CP: SELECT clientes dedicated activos + conexión
    CP-->>Orch: tenants[]

    alt tenants vacío
        Orch-->>API: CatalogSyncBatchResult tenants_total=0
        API-->>Op: 200 completed
    end

    loop for each tenant in tenants
        Orch->>Orch: validar tenant (V1–V6)
        alt validación falla
            Orch->>Orch: append outcome status=failed
        else OK
            Orch->>Svc: run(tenant.cliente_id, catalog, tenant.database_name)
            Note over Svc,Ded: Mismo flujo que Modalidad A
            alt sync OK
                Svc-->>Orch: CatalogSyncResult completed
                Orch->>Orch: append outcome + acumular counts
            else sync error
                Svc-->>Orch: CatalogSyncResult failed
                Orch->>Orch: append outcome failed
            end
        end
    end

    Orch->>Orch: agregar aggregated_counts + status batch
    Orch-->>API: CatalogSyncBatchResult
    API-->>Op: 200 JSON (completed | partial | failed)
```

---

## 3. Flow INSERT

PK existe en Platform, ausente en Dedicated.

```mermaid
sequenceDiagram
    participant Core as catalog_sync_core
    participant Writer as DedicatedCatalogWriter
    participant Ded as BD Dedicated

    Note over Core: platform_row[pk] presente<br/>dedicated_row[pk] ausente

    Core->>Core: acción = INSERT
    Core->>Core: payload = columnas compare + pk Platform

    Core->>Writer: plan_entry(INSERT, pk, payload)
    Writer->>Ded: BEGIN TRANSACTION
    Writer->>Ded: INSERT INTO cat_* (pk, col1, …) VALUES (:platform_pk, …)
    Ded-->>Writer: 1 row affected
    Writer->>Ded: COMMIT
    Writer-->>Core: inserted += 1
```

**Invariante:** `:platform_pk` es el UUID de Platform — nunca `NEWID()` / `uuid4()` en destino.

---

## 4. Flow UPDATE

PK en ambos lados; al menos una columna compare difiere.

```mermaid
sequenceDiagram
    participant Core as catalog_sync_core
    participant Writer as DedicatedCatalogWriter
    participant Ded as BD Dedicated

    Note over Core: normalize(platform_row) ≠ normalize(dedicated_row)

    Core->>Core: acción = UPDATE
    Core->>Core: diff_fields = columnas compare distintas

    Core->>Writer: plan_entry(UPDATE, pk, diff_fields)
    Writer->>Ded: BEGIN TRANSACTION
    Writer->>Ded: UPDATE cat_* SET col1=:v1, … WHERE pk = :platform_pk
    Ded-->>Writer: 1 row affected
    Writer->>Ded: COMMIT
    Writer-->>Core: updated += 1
```

**Nota:** Si solo `es_activo` difiere (Platform activo, dedicated inactivo), cuenta como UPDATE.

---

## 5. Flow SKIP

PK en ambos lados; todas las columnas compare iguales tras normalización.

```mermaid
sequenceDiagram
    participant Core as catalog_sync_core
    participant Writer as DedicatedCatalogWriter

    Note over Core: normalize(platform_row) = normalize(dedicated_row)

    Core->>Core: acción = SKIP
    Core->>Writer: plan_entry(SKIP, pk)

    Note over Writer: Sin SQL — no mutación
    Writer-->>Core: skipped += 1
```

**Idempotencia:** Re-ejecución completa con datos estables produce `skipped = platform_total` (asumiendo sin huérfanas).

---

## 6. Flow SOFT DEACTIVATE

Dos sub-casos con la misma acción SQL.

### 6a. Fila huérfana — PK solo en Dedicated

```mermaid
sequenceDiagram
    participant Core as catalog_sync_core
    participant Writer as DedicatedCatalogWriter
    participant Ded as BD Dedicated

    Note over Core: dedicated_row[pk] presente<br/>platform_row[pk] ausente

    Core->>Core: acción = SOFT_DEACTIVATE
    Core->>Writer: plan_entry(SOFT_DEACTIVATE, pk)
    Writer->>Ded: BEGIN TRANSACTION
    Writer->>Ded: UPDATE cat_* SET es_activo = 0 WHERE pk = :pk
    Ded-->>Writer: 1 row affected
    Writer->>Ded: COMMIT
    Writer-->>Core: deactivated += 1
```

### 6b. Dedicated ya inactivo — SKIP en lugar de UPDATE redundante

```mermaid
sequenceDiagram
    participant Core as catalog_sync_core

    Note over Core: platform es_activo = 0<br/>dedicated es_activo = 0<br/>resto columnas iguales

    Core->>Core: acción = SKIP (no SQL)
```

Si Platform `es_activo=0` y dedicated `es_activo=1` con resto igual → **UPDATE** (no SOFT_DEACTIVATE separado).

---

## 7. Rollback ante error (transacción dedicated)

```mermaid
sequenceDiagram
    participant Svc as CatalogSyncService
    participant Writer as DedicatedCatalogWriter
    participant Ded as BD Dedicated

    Svc->>Writer: apply_plan(plan)
    Writer->>Ded: BEGIN TRANSACTION
    Writer->>Ded: INSERT / UPDATE (fila 1..N)
    Writer->>Ded: INSERT / UPDATE (fila N+1)
    Ded-->>Writer: ERROR (FK / UNIQUE / timeout)

    Writer->>Ded: ROLLBACK
    Writer-->>Svc: CATALOG_SYNC_APPLY_FAILED
    Svc-->>Svc: counts no aplicados — dedicated sin cambios parciales
```

**Contrato:** Ninguna fila del plan se persiste si falla una mutación dentro de la TX.

---

## 8. Validación FK prerequisito (pre-motor)

Ejemplo: sync `departamentos` sin `paises` previo.

```mermaid
sequenceDiagram
    participant Orch as CatalogSyncOrchestrator
    participant Reader as PlatformCatalogReader
    participant Writer as DedicatedCatalogWriter
    participant Plat as BD ERP Shared
    participant Ded as BD Dedicated

    Orch->>Reader: fetch_distinct_fk_ids(DEPARTAMENTO, pais_id)
    Reader->>Plat: SELECT DISTINCT pais_id FROM cat_departamento
    Plat-->>Reader: pais_ids_platform[]

    Orch->>Writer: exists_pks(PAIS, pais_ids_platform, database_name)
    Writer->>Ded: SELECT pais_id FROM cat_pais WHERE pais_id IN (…)
    Ded-->>Writer: pais_ids_found[]

    Orch->>Orch: missing = platform - found
    alt missing no vacío
        Orch-->>Orch: 422 CATALOG_SYNC_FK_PREREQUISITE
        Note over Orch: CatalogSyncService NO invocado
    end
```

---

## 9. Leyenda de actores

| Actor | Rol |
|-------|-----|
| `PlatformCatalogReader` | Lectura SSOT — BD ERP shared |
| `DedicatedCatalogWriter` | Lectura snapshot + escritura TX — BD dedicated |
| `catalog_sync_core` | Diff puro — sin SQL |
| `CatalogSyncService` | Compone reader + core + writer |
| `CatalogSyncOrchestrator` | Validación CP + loop modalidad B |
