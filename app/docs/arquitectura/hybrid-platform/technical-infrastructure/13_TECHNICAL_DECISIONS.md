# 13 — Technical Decisions

**Etapa:** 5 — Technical Infrastructure Design  
**Fecha:** 2026-06-25  
**Estado:** Decisiones técnicas de infraestructura  
**Formato:** Contexto, problema, alternativas, decisión, consecuencia, relación etapas previas

---

## TD-01 — Cache intra-request de route binding

| Campo | Contenido |
|-------|-----------|
| **Contexto** | RD-01 resolución per-op |
| **Problema** | N execute_* amplifican metadata lookups |
| **Alternativas** | A) Sin cache; B) Intra-request cache; C) Request-scoped binding global |
| **Decisión** | **B) Intra-request cache** `(tenant_id, operation_class)` |
| **Consecuencia** | Compatible AS-IS; reduce carga CP |
| **Relación** | RD-01; 10_ENGINE_CACHE_POLICY L-A |

---

## TD-02 — TTL metadata cache proceso

| Campo | Contenido |
|-------|-----------|
| **Contexto** | L-B cache en `core/tenant/cache.py` |
| **Problema** | Balance freshness vs load |
| **Alternativas** | A) 60s; B) 300–900s; C) Sin TTL event-only |
| **Decisión** | **B) 300–900s configurable** + invalidación event-driven |
| **Consecuencia** | Multi-worker eventual consistency aceptada MVP |
| **Relación** | G-13; 02_STORAGE_METADATA |

---

## TD-03 — Engine cache key shared

| Campo | Contenido |
|-------|-----------|
| **Contexto** | AS-IS `tenant_{id}` en shared |
| **Problema** | Engines redundantes mismo physical DB |
| **Alternativas** | A) Mantener AS-IS; B) `shared_default` único |
| **Decisión** | **A) MVP mantiene AS-IS**; B post-MVP Fase 8 |
| **Consecuencia** | Sin riesgo regresión pool sharing day-1 |
| **Relación** | 04_ENGINE_MANAGEMENT |

---

## TD-04 — Pool sizing uniforme

| Campo | Contenido |
|-------|-----------|
| **Contexto** | Settings globales DB_POOL_* |
| **Problema** | ¿Pool per-tenant dedicated? |
| **Alternativas** | A) Uniforme; B) Per metadata |
| **Decisión** | **A) Uniforme MVP** |
| **Consecuencia** | Simplicidad; tune post-production |
| **Relación** | 04_ENGINE_MANAGEMENT |

---

## TD-05 — No request-scoped SQL session

| Campo | Contenido |
|-------|-----------|
| **Contexto** | E4 RD-01 explícitamente no requiere |
| **Problema** | ¿Introducir session per HTTP request? |
| **Alternativas** | A) Introducir; B) Mantener per-op |
| **Decisión** | **B) Mantener per-op + UoW** |
| **Consecuencia** | G-17 preserved; N connections per endpoint |
| **Relación** | G-17; 05_SESSION_LIFECYCLE |

---

## TD-06 — Preservar auto-commit execute_*

| Campo | Contenido |
|-------|-----------|
| **Contexto** | AS-IS behavior |
| **Problema** | ¿Unificar commit semantics? |
| **Alternativas** | A) Cambiar a manual; B) Preservar |
| **Decisión** | **B) Preservar** |
| **Consecuencia** | Callers unchanged; UoW para multi-step |
| **Relación** | 08_QUERY_EXECUTION |

---

## TD-07 — UoW semantics unchanged

| Campo | Contenido |
|-------|-----------|
| **Contexto** | G-18 |
| **Problema** | ¿UoW variant dedicated? |
| **Alternativas** | A) Variant; B) Same |
| **Decisión** | **B) Same API and semantics** |
| **Consecuencia** | IAM/INV unchanged |
| **Relación** | 06_UNIT_OF_WORK |

---

## TD-08 — Tenant filter defensivo en dedicated

| Campo | Contenido |
|-------|-----------|
| **Contexto** | RI-40; wrong route risk |
| **Problema** | ¿Skip filter dedicated? |
| **Alternativas** | A) Skip; B) Defensive enforce |
| **Decisión** | **B) Defensive enforce** |
| **Consecuencia** | Overhead mínimo; fail-safe |
| **Relación** | G-20; 08_QUERY_EXECUTION |

---

## TD-09 — Multi-worker cache eventual consistency

| Campo | Contenido |
|-------|-----------|
| **Contexto** | L-B local per worker |
| **Problema** | Stale metadata cross-worker |
| **Alternativas** | A) Redis pub/sub day-1; B) TTL + event ops; C) Sticky sessions |
| **Decisión** | **B) MVP**; A en Fase 8 |
| **Consecuencia** | Migration requiere TTL corto o manual flush |
| **Relación** | 10_ENGINE_CACHE_POLICY |

---

## TD-10 — Single retry metadata CP lookup

| Campo | Contenido |
|-------|-----------|
| **Contexto** | Transient CP errors |
| **Problema** | ¿Retry resolution? |
| **Alternativas** | A) No retry; B) 1 retry; C) Exponential |
| **Decisión** | **B) 1 retry transiente opcional** |
| **Consecuencia** | Latencia +50ms worst case |
| **Relación** | 11_FAILURE_RECOVERY F1 |

---

## TD-11 — Persistence Gateway como evolución, no reescritura

| Campo | Contenido |
|-------|-----------|
| **Contexto** | Responsabilidades dispersas AS-IS |
| **Problema** | ¿Nuevo módulo vs refactor inline |
| **Alternativas** | A) Monolito nuevo; B) Evolucionar execute_* chain |
| **Decisión** | **B) Evolucionar pipeline existente** |
| **Consecuencia** | Diff mínimo G-01; misma API |
| **Relación** | E2 change surface |

---

## TD-12 — Saga onboarding semi-automática MVP

| Campo | Contenido |
|-------|-----------|
| **Contexto** | RD-12; O-E5-04 |
| **Problema** | Nivel compensación automática |
| **Alternativas** | A) Full auto; B) Semi-auto + ops; C) Manual |
| **Decisión** | **B) Semi-automática** |
| **Consecuencia** | Runbooks ops; dashboard provisioning state |
| **Relación** | 07_TRANSACTION_BOUNDARIES T5 |

---

## TD-13 — Cerrar RD-11 antes dedicated production IAM

| Campo | Contenido |
|-------|-----------|
| **Contexto** | Session store location open |
| **Problema** | IAM V2 route ambiguity |
| **Alternativas** | A) Parallel paths; B) Block dedicated until closed |
| **Decisión** | **B) Block dedicated prod IAM** hasta ADR session |
| **Consecuencia** | Fase 5 gate en roadmap |
| **Relación** | RD-11; Q-010 E3 |

---

## Tabla resumen

| ID | Tema | Estado |
|----|------|--------|
| TD-01 | Intra-request cache | Cerrada |
| TD-02 | Metadata TTL | Cerrada |
| TD-03 | Engine key shared | Cerrada (MVP=AS-IS) |
| TD-04 | Pool uniform | Cerrada |
| TD-05 | No request session | Cerrada |
| TD-06 | Auto-commit preserve | Cerrada |
| TD-07 | UoW unchanged | Cerrada |
| TD-08 | Defensive tenant filter | Cerrada |
| TD-09 | Eventual consistency MVP | Cerrada |
| TD-10 | 1 retry metadata | Cerrada |
| TD-11 | Evolve not rewrite | Cerrada |
| TD-12 | Saga semi-auto | Cerrada |
| TD-13 | RD-11 gate | Cerrada |

---

## Decisiones delegadas Etapa 6 / ADR

| Tema | Owner |
|------|-------|
| Session store CP vs DP | ADR-002 + Fase 5 |
| Redis invalidation broadcast | Fase 8 |
| Online migration | Post-MVP |
| Exact pool sizes production | SRE tuning |

---

## Conclusión

13 decisiones técnicas cerradas definen implementación sin ambigüedad en pipeline core. RD-11 permanece única decisión runtime abierta con gate explícito TD-13.
