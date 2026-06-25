# 10 — Engine Cache Policy

**Etapa:** 5 — Technical Infrastructure Design  
**Fecha:** 2026-06-25  
**Estado:** Borrador para revisión  
**Prerequisitos:** 02 Storage Metadata, 04 Engine Management  
**Restricción:** Políticas de cache infraestructura. Sin código.

---

## 1. Propósito

Unificar las políticas de **cache de metadata, route binding y engines** en un documento normativo — evitando inconsistencias entre workers y estados stale post-lifecycle.

---

## 2. Capas de cache (resumen)

| Capa | ID | Scope | Contenido | Doc detalle |
|------|----|-------|-----------|-------------|
| Intra-request | L-A | HTTP request | Route binding | 01, 03 |
| Metadata proceso | L-B | Worker | Storage Metadata | 02 |
| Engine pool | L-C | Worker | AsyncEngine + pool | 04 |
| Redis IAM | L-D | Cluster | Blacklist, permission cache | Fuera scope MVP dedicated |

---

## 3. Política L-A — Intra-request route cache

| Parámetro | Valor |
|-----------|-------|
| Key | `(tenant_id, operation_class)` |
| TTL | Vida del request |
| Invalidación | Request teardown automático |
| Obligatoriedad | **Recomendada** (TD-01) |

| Beneficio | Descripción |
|-----------|-------------|
| Reduce metadata lookups | Múltiples execute_* mismo request |
| Compatible RD-01 | Per-op resolution con cache |

---

## 4. Política L-B — Metadata cache proceso

| Parámetro | Valor MVP |
|-----------|-----------|
| Key | `tenant_id` |
| TTL default | 300–900 segundos (configurable) |
| Contenido | Installation Mode + Storage Endpoint (sin plaintext password en memoria extendida) |
| Max entries | LRU opcional post-MVP |

### 4.1 Invalidación obligatoria

| Evento | Acción |
|--------|--------|
| Provisioning dedicated complete | Invalidate tenant_id |
| Migration cutover | Invalidate + L-C dispose |
| Credential rotation | Invalidate + L-C dispose |
| Manual ops override | Admin hook invalidate |
| Tenant state → Retirado | Invalidate |

### 4.2 Invalidación NO automática

| Evento | Razón |
|--------|-------|
| ERP data mutation | Metadata no cambia |
| User login | Sin relación |

---

## 5. Política L-C — Engine cache

| Parámetro | Valor |
|-----------|-------|
| Key | Ver TD-03 (03_CONNECTION_RESOLUTION) |
| TTL | Vida del proceso — no TTL time-based MVP |
| Invalidación | Event-driven dispose |
| Max engines | Configurable limit per worker |

### 5.1 Coherencia metadata ↔ engine

```
Rule EC-01: Invalidar L-B implica evaluar L-C dispose para mismo tenant_id
Rule EC-02: Dispose L-C NO invalida L-B automáticamente (metadata puede ser válida)
Rule EC-03: Recreate engine usa metadata L-B post-invalidate
```

---

## 6. Multi-worker consistency

| Escenario | Comportamiento MVP |
|-----------|-------------------|
| Worker A invalida metadata local | Worker B mantiene cache hasta TTL |
| Migration cutover | **Requiere** broadcast invalidation o TTL corto |
| Credential rotation | Broadcast o TTL corto (< 60s) recomendado |

**Decisión TD-09:** MVP acepta eventual consistency entre workers vía TTL corto post-migration. Fase 2: Redis pub/sub invalidation (O-E5-01).

---

## 7. Cache warming

| Evento | Warming |
|--------|---------|
| Application startup | Admin engine only |
| First request tenant | Lazy metadata + engine |
| Deploy rolling | Gradual — no pre-warm all dedicated |

---

## 8. Métricas cache

| Métrica | Alerta |
|---------|--------|
| metadata_cache_hit_ratio | < 80% investigar |
| metadata_cache_stale_serving | > 0 post-migration |
| engine_dispose_rate | Spike post-deploy |
| route_cache_hit_per_request | Benchmark |

---

## 9. Failure modes

| Fallo | Efecto | Recovery |
|-------|--------|----------|
| Stale metadata post-migration | Wrong store route | Invalidate + dispose; RI-39 fail dedicated |
| Cache poison | Wrong engine | Process restart; invalidate all |
| TTL too long | Delayed credential rotation | Reduce TTL; broadcast invalidate |
| No cache | CP overload | Acceptable MVP; tune TTL |

---

## 10. Decisiones técnicas

| ID | Decisión |
|----|----------|
| TD-01 | L-A intra-request cache recomendada |
| TD-02 | L-B TTL 300–900s configurable |
| TD-03 | Engine key shared consolidation post-MVP |
| TD-09 | Eventual consistency multi-worker MVP via TTL |

---

## 11. Conclusión

Engine Cache Policy coordina **tres niveles** (request, metadata, engine) con invalidación event-driven en lifecycle transitions. Multi-worker strong consistency deferred post-MVP.

Documentos relacionados: `02_STORAGE_METADATA_RESOLUTION`, `04_ENGINE_MANAGEMENT`, `11_FAILURE_RECOVERY`.
