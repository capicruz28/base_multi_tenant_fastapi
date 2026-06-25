# 05 — Implementation Baseline (Etapa 6)

**Etapa:** 5.6 — Architecture Baseline Freeze  
**Versión baseline:** BL-1.0  
**Fecha:** 2026-06-25  
**Estado:** **Normativo — autorización implementación acotada**

**Fuente autorización:** `architecture-validation/10_GO_NO_GO_REPORT.md` → **GO WITH CONDITIONS**  
**SUPERSEDES:** `technical-infrastructure/12_IMPLEMENTATION_ROADMAP.md` §3–4 (fases)

---

## 1. Decisión de implementación

| Aspecto | Decisión BL-1.0 |
|---------|-----------------|
| **Etapa 6 autorizada** | **Sí — scope F0–F3 únicamente** |
| **Dedicated production** | **No autorizada** hasta Gate Review post-F3 |
| **Modificación código** | Permitida solo conforme §3 |
| **Modificación contratos** | **Prohibida** |

---

## 2. PERMITIDO en Etapa 6 (BL-1.0)

### Fase F0 — Test harness

| Permitido |
|-----------|
| Nuevos tests integración dedicated mock |
| Tests adversariales: wrong-route, tenant isolation, impersonation harness |
| Métricas baseline cache/engine |
| Extensión `tests/integration/conftest` |
| Scripts diagnóstico **sin** cambio producción |

### Fase F1 — Gateway consolidation

| Permitido |
|-----------|
| Modificar `connection_async.py`, `routing.py`, `queries_async.py`, `query_helpers.py`, `core/tenant/cache.py` |
| Intra-request route cache (TD-01) |
| Metadata TTL + invalidation events (TD-02) |
| Defensive tenant filter dedicated (TD-08) |
| `close_all_async_engines()` en shutdown |
| Logging/metrics infra (sin secrets) |

### Fase F2 — Shared regression

| Permitido |
|-----------|
| Benchmarks execute_* |
| CI gates G-02 |
| Performance baseline documentación |

### Fase F3 — L5 cleanup

| Permitido |
|-----------|
| Eliminar `database_type` branches en `user_context.py`, `rol_service.py` |
| TenantMiddleware: no exponer mode a L5 (RD-03) |
| Grep gate database_type whitelist |

### Transversal F0–F3

| Permitido |
|-----------|
| Documentación implementación (no arquitectura — arquitectura requiere ADR) |
| Feature flag `dedicated_enabled` **solo** en config infra — default false |
| Audit repositories legacy (read-only análisis + fixes delegación gateway) |

---

## 3. PROHIBIDO en Etapa 6 (BL-1.0)

| Prohibido | Guardrail |
|-----------|-----------|
| Modificar módulos ERP (`modules/org`, `inv`, `pur`, …) | G-01 |
| Modificar 153+ query files ERP | G-01, QL-04 |
| Cambiar firmas `execute_*`, UoW API | G-07, TD-07 |
| Cambiar OpenAPI paths/schemas/status | G-03, G-07 |
| Cambiar JWT/session contracts | G-03 |
| Crear `execute_*_dedicated` / fork services | G-04 |
| `DatabaseConnection.DEDICATED` enum | G-05 |
| Introducir SessionLocal / Depends(get_db) | G-17 |
| Activar tenants dedicated producción | C-01 Go/No-Go |
| Merge F4 provisioning saga | Gate Review |
| Skip tenant filter production | G-20 |
| `if dedicated` / `if shared` en L5 | G-10 |
| Modificar DDL / migraciones schema | BL-R01 scope |
| Resolver RD/ADR Closed sin ADR nueva | BL-R02 |

---

## 4. Gates obligatorios

### Gate G-F0 — Entrada F1

| Criterio | Verificación |
|----------|--------------|
| F0 tests pass | CI |
| Harness dedicated mock resuelve engine | Integration |
| Shared suite baseline captured | CI artifact |
| Baseline BL-1.0 ack equipo | Checklist §8 |

### Gate G-F1 — Entrada F2

| Criterio | Verificación |
|----------|--------------|
| Dedicated mock route correct | Test |
| Shared tenants behavior identical | Regression |
| database_type no new L5 usages | Grep |
| close_all_async_engines shutdown | Test/manual |
| QueryAuditor pass | CI |

### Gate G-F2 — Entrada F3

| Criterio | Verificación |
|----------|--------------|
| G-02 checklist complete | Review |
| Latency baseline documented | Metrics |
| No perf regression > agreed threshold | Benchmark |

### Gate G-F3 — Gate Review (autorizar F4 o no)

| Criterio | Verificación |
|----------|--------------|
| F3 complete — database_type solo whitelist | Grep |
| Q-030 spec 1-pager approved | Doc |
| ADR-011 catalog list validated | F3.5 |
| Steering ack dedicated timeline | Product |
| **Nueva Go/No-Go** para F4+ | Arquitecto |

---

## 5. Condiciones GO WITH CONDITIONS (tracking)

| ID | Condición | Estado BL-1.0 |
|----|-----------|---------------|
| C-01 | Scope F0–F3 | **Active** |
| C-02 | RD-11 cerrada | **Done** — ADR-002-A |
| C-03 | Q-030/Q-031 | **Q-031 Done**; Q-030 Open gate F4 |
| C-04 | Catálogos dedicated | **Done** — ADR-011-A |
| C-05 | Roadmap reordenado | **Done** — §6 |
| C-06 | Ops runbooks pre-F6 | **Pending** |
| C-07 | ADR-001 formal | **Done** |
| C-08 | F0 tests ampliados | **Required** F0 |

---

## 6. Roadmap oficial congelado

```
┌─────────────────────────────────────────────────────────────┐
│  ETAPA 6 AUTORIZADA (BL-1.0)                                │
├─────────────────────────────────────────────────────────────┤
│  F0  Test harness adversarial                    [AUTO]     │
│  F1  Gateway consolidation                       [AUTO]     │
│  F2  Shared regression                             [AUTO]     │
│  F3  L5 database_type cleanup                      [AUTO]     │
│  F3.5 Catalog list validation (ADR-011)            [GATE F4]  │
├─────────────────────────────────────────────────────────────┤
│  ═══ GATE REVIEW — nueva Go/No-Go requerida ═══             │
├─────────────────────────────────────────────────────────────┤
│  F4  Provisioning saga                             [BLOCKED]│
│  F5b Session route (ADR-002-A hardening)           [BLOCKED]│
│  F6  Dedicated production + ops runbooks           [BLOCKED]│
│  F7  Migration offline                             [BLOCKED]│
│  F8  Optimizations                                 [BLOCKED]│
└─────────────────────────────────────────────────────────────┘
```

### Dependencias congeladas

```
F0 → F1 → F2 → F3 → F3.5 → [GATE] → F4 → F5b → F6 → F7 → F8
```

**Cambio vs E5 original:** F3 **antes** F4; eliminado F5 "decision" (RD-11 cerrada); F5b solo hardening; F3.5 añadida.

---

## 7. Criterios de entrada Etapa 6

| # | Criterio | Estado |
|---|----------|--------|
| 1 | Architecture Baseline BL-1.0 frozen | ✅ |
| 2 | Go/No-Go 5.5 acknowledged | ☐ equipo |
| 3 | Guardrails G-01–G-20 distribuidos | ☐ |
| 4 | Branch strategy acordada | ☐ |
| 5 | Feature flag dedicated=false prod | ☐ |

---

## 8. Criterios de salida Etapa 6 (scope F0–F3)

| # | Criterio |
|---|----------|
| 1 | Gates G-F0 through G-F3 passed |
| 2 | Zero ERP module diffs (except tests infra) |
| 3 | OpenAPI diff clean |
| 4 | Shared staging smoke pass |
| 5 | Gate Review scheduled with Q-030 spec |
| 6 | Documentación implementación F0–F3 en repo |

---

## 9. Componentes tocables (whitelist archivos)

| Archivo / zona | Fases |
|----------------|-------|
| `infrastructure/database/connection_async.py` | F1 |
| `core/tenant/routing.py` | F1 |
| `infrastructure/database/queries_async.py` | F1 |
| `infrastructure/database/query_helpers.py` | F1 |
| `core/tenant/cache.py` | F1 |
| `core/tenant/middleware.py` | F3 |
| `core/auth/user_context.py` | F3 |
| `modules/rbac/.../rol_service.py` | F3 |
| `app/main.py` (shutdown) | F1 |
| `tests/integration/*` | F0 |
| `modules/*/presentation`, `modules/*/queries` | **PROHIBIDO** |

---

## 10. Conclusión

Etapa 6 **inicia** con autorización **explícita y limitada**. Implementación fuera de §2 requiere **Gate Review** y posible **BL-1.1** o ADR-012+.

**Confianza F0–F3:** 75% (validación 5.5, mantenida post-freeze).
