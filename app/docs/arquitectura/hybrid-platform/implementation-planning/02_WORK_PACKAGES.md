# 02 — Work Packages

**Etapa:** 5.7 — Implementation Planning  
**Versión:** IP-1.0  
**Baseline:** BL-1.0  
**Alcance:** F0–F3

---

## 1. Leyenda campos

Cada work package (WP) incluye: objetivo, alcance, archivos permitidos/prohibidos, dependencias, riesgos, validaciones, criterios salida.

---

## 2. Fase F0 — Test Harness

### F0-WP01 — Dedicated mock harness foundation

| Campo | Contenido |
|-------|-----------|
| **Objetivo** | Infraestructura test que simula tenant dedicated sin BD real |
| **Alcance** | conftest fixtures; metadata mock; engine key assertion |
| **Permitido** | `tests/integration/conftest*.py`, `tests/integration/helpers/`, `tests/unit/test_hybrid_*` |
| **Prohibido** | `app/modules/**`, `app/infrastructure/database/*.py` producción |
| **Dependencias** | BL-1.0 ack |
| **Riesgos** | Mock no representa producción → mitigar con metadata shape real |
| **Validaciones** | Fixture resuelve engine key `tenant_{id}`; CP lookup mock |
| **Salida** | PR-F0-01 merged; harness importable |
| **PR** | PR-F0-01 |
| **Trace** | G-02, G-16, TD-01, RI-36 |

---

### F0-WP02 — Wrong-route adversarial tests

| Campo | Contenido |
|-------|-----------|
| **Objetivo** | Detectar dedicated tenant routed to shared (RI-39) |
| **Alcance** | Tests fallan si fallback incorrecto; dedicated explicit fail |
| **Permitido** | `tests/integration/test_hybrid_wrong_route*.py` |
| **Prohibido** | Producción |
| **Dependencias** | F0-WP01 |
| **Riesgos** | Tests flaky sin mock estable |
| **Validaciones** | CI red en wrong route simulado |
| **Salida** | 3+ escenarios: missing metadata+dedicated, stale cache sim |
| **PR** | PR-F0-02 |
| **Trace** | RD-08, RI-39, AR-C02 |

---

### F0-WP03 — Tenant isolation harness tests

| Campo | Contenido |
|-------|-----------|
| **Objetivo** | Verificar tenant filter en shared path (G-20) |
| **Alcance** | Integration tests isolation; cross-tenant negative |
| **Permitido** | `tests/integration/test_hybrid_tenant_isolation*.py` |
| **Prohibido** | ERP query modifications |
| **Dependencias** | F0-WP01 |
| **Riesgos** | Duplicar tests existentes → reutilizar `test_tenant_isolation_comprehensive` si aplica |
| **Validaciones** | CI pass; no duplicate coverage sin valor |
| **Salida** | Isolation scenarios documented |
| **PR** | PR-F0-03 |
| **Trace** | G-20, RI-11, RI-40 |

---

### F0-WP04 — Impersonation harness tests

| Campo | Contenido |
|-------|-----------|
| **Objetivo** | Validar tenant operativo JWT target (RD-05) en harness |
| **Alcance** | Tests deps pattern; mock impersonation context |
| **Permitido** | `tests/integration/test_hybrid_impersonation*.py`, unit deps |
| **Prohibido** | ERP module changes |
| **Dependencias** | F0-WP01 |
| **Riesgos** | AR-C05 — solo harness, no fix deps ERP |
| **Validaciones** | Test documents expected behavior ORG/INV pattern |
| **Salida** | Harness impersonation green |
| **PR** | PR-F0-04 |
| **Trace** | RD-05, RI-18 |

---

### F0-WP05 — CI baseline artifact

| Campo | Contenido |
|-------|-----------|
| **Objetivo** | Capturar baseline shared suite pre-F1 |
| **Alcance** | CI job artifact; optional metrics stub |
| **Permitido** | `.github/workflows/ci.yml` (test jobs only), `scripts/` diagnostic |
| **Prohibido** | Production deploy changes |
| **Dependencias** | F0-WP01–04 |
| **Riesgos** | CI time increase → parallelize |
| **Validaciones** | Artifact stored; test count documented |
| **Salida** | Baseline report in PR description template |
| **PR** | PR-F0-05 |
| **Trace** | G-F0, C-08 |

---

## 3. Fase F1 — Gateway Consolidation

### F1-WP01 — Async engine shutdown

| Campo | Contenido |
|-------|-----------|
| **Objetivo** | Invocar `close_all_async_engines()` en shutdown |
| **Alcance** | `app/main.py` shutdown event only |
| **Permitido** | `app/main.py` |
| **Prohibido** | Otros archivos |
| **Dependencias** | G-F0 |
| **Riesgos** | Shutdown order → async before sync pools |
| **Validaciones** | Manual/log test; unit if exists |
| **Salida** | Engines closed on worker stop |
| **PR** | PR-F1-01 |
| **Trace** | EM-G01, TD-11 |

---

### F1-WP02 — Metadata cache TTL

| Campo | Contenido |
|-------|-----------|
| **Objetivo** | Formalizar TTL 300–900s configurable (TD-02) |
| **Alcance** | `core/tenant/cache.py`; settings |
| **Permitido** | `cache.py`, `core/config.py` (setting only) |
| **Prohibido** | L5 services |
| **Dependencias** | G-F0 |
| **Riesgos** | Stale cache → invalidation in WP07 |
| **Validaciones** | Unit test TTL expiry |
| **Salida** | Setting documented `.env.example` |
| **PR** | PR-F1-02 |
| **Trace** | TD-02, G-13, RI-38 |

---

### F1-WP03 — Intra-request route cache L-A

| Campo | Contenido |
|-------|-----------|
| **Objetivo** | Cache `(tenant_id, operation_class)` per request (TD-01) |
| **Alcance** | ContextVar or request-scoped dict in gateway path |
| **Permitido** | `routing.py`, `queries_async.py` |
| **Prohibido** | ERP |
| **Dependencias** | F1-WP02 |
| **Riesgos** | Context leak → teardown mandatory |
| **Validaciones** | Test: N execute_* = 1 metadata lookup |
| **Salida** | Route cache hit metric optional |
| **PR** | PR-F1-03 |
| **Trace** | RD-01, TD-01, RI-09 |

---

### F1-WP04 — Connection resolution hardening

| Campo | Contenido |
|-------|-----------|
| **Objetivo** | Fail-closed dedicated; fallback rules RD-08 |
| **Alcance** | `routing.py`, `connection_async.py` |
| **Permitido** | Whitelist infra |
| **Prohibido** | New public APIs |
| **Dependencias** | F1-WP02–03 |
| **Riesgos** | Break shared tenants → F0 regression |
| **Validaciones** | F0 wrong-route tests pass |
| **Salida** | Dedicated mock resolves correct engine |
| **PR** | PR-F1-04 |
| **Trace** | RD-08, RI-39, ADR-001 |

---

### F1-WP05 — Defensive tenant filter

| Campo | Contenido |
|-------|-----------|
| **Objetivo** | TD-08 filter en dedicated path |
| **Alcance** | `query_helpers.py` apply_tenant_filter policy |
| **Permitido** | `query_helpers.py` |
| **Prohibido** | 153 query files |
| **Dependencias** | F1-WP04 |
| **Riesgos** | Performance negligible |
| **Validaciones** | Unit test filter applied dedicated mock |
| **Salida** | Policy documented in module docstring |
| **PR** | PR-F1-05 |
| **Trace** | TD-08, ADR-006, RI-40 |

---

### F1-WP06 — queries_async pipeline alignment

| Campo | Contenido |
|-------|-----------|
| **Objetivo** | Unificar pipeline resolution → execute |
| **Alcance** | `queries_async.py` internal only |
| **Permitido** | `queries_async.py` |
| **Prohibido** | Signature changes execute_* |
| **Dependencias** | F1-WP03–05 |
| **Riesgos** | Critical path — small diff |
| **Validaciones** | All integration tests; QueryAuditor |
| **Salida** | `_get_connection_context` uses unified path |
| **PR** | PR-F1-06 |
| **Trace** | RD-06, G-07, G-09 |

---

### F1-WP07 — Fallback shared observability

| Campo | Contenido |
|-------|-----------|
| **Objetivo** | Log + metric on fallback (RD-08 amended) |
| **Alcance** | routing/cache on fallback path |
| **Permitido** | `routing.py`, `cache.py` |
| **Prohibido** | Alert to client |
| **Dependencias** | F1-WP04 |
| **Riesgos** | Log noise → rate limit |
| **Validaciones** | Test triggers metric |
| **Salida** | `metadata_fallback_shared_total` defined |
| **PR** | PR-F1-07 |
| **Trace** | RD-08 amended |

---

### F1-WP08 — Dedicated routing integration tests

| Campo | Contenido |
|-------|-----------|
| **Objetivo** | E2E harness con cambios F1 reales |
| **Alcance** | Extend F0 tests against prod infra code |
| **Permitido** | `tests/integration/test_hybrid_*` |
| **Prohibido** | Real dedicated DB |
| **Dependencias** | F1-WP04–06 |
| **Riesgos** | None — mock only |
| **Validaciones** | CI green |
| **Salida** | G-F1 dedicated mock criteria met |
| **PR** | PR-F1-08 |
| **Trace** | G-F1 |

---

### F1-WP09 — Repository delegation audit

| Campo | Contenido |
|-------|-----------|
| **Objetivo** | Fix repositories bypassing gateway (RD-06-E) |
| **Alcance** | Minimal fixes platform repositories only |
| **Permitido** | `infrastructure/database/repositories/**` |
| **Prohibido** | ERP modules |
| **Dependencias** | F1-WP06 |
| **Riesgos** | Scope creep → max 2 files |
| **Validaciones** | Grep no raw connection outside whitelist |
| **Salida** | Audit report in PR |
| **PR** | PR-F1-09 |
| **Trace** | RD-06-E02, G-09 |

---

## 4. Fase F2 — Shared Regression

### F2-WP01 — Performance benchmark baseline

| Campo | Contenido |
|-------|-----------|
| **Objetivo** | Document latency execute_* pre/post F1 |
| **Alcance** | Benchmark script or pytest-benchmark |
| **Permitido** | `tests/perf/` or `scripts/benchmark_*`, docs |
| **Prohibido** | Production code unless hooks |
| **Dependencias** | G-F1 |
| **Riesgos** | Environment variance → staging numbers |
| **Validaciones** | Report committed docs/implementation |
| **Salida** | Threshold agreed ±10% p95 |
| **PR** | PR-F2-01 |
| **Trace** | G-F2, AR-M01 |

---

### F2-WP02 — G-02 CI gate formalization

| Campo | Contenido |
|-------|-----------|
| **Objetivo** | CI job `shared-regression` required |
| **Alcance** | `.github/workflows/ci.yml` |
| **Permitido** | CI config, pytest markers |
| **Prohibido** | Skip tests |
| **Dependencias** | G-F1 |
| **Riesgos** | CI duration |
| **Validaciones** | Required check on main |
| **Salida** | G-02 checklist signed |
| **PR** | PR-F2-02 |
| **Trace** | G-02, G-F2 |

---

## 5. Fase F3 — L5 Cleanup

### F3-WP01 — Middleware TenantContext cleanup

| Campo | Contenido |
|-------|-----------|
| **Objetivo** | No exponer Installation Mode a L5 (RD-03) |
| **Alcance** | `core/tenant/middleware.py`, `context.py` |
| **Permitido** | middleware, context (remove public database_type accessor if any) |
| **Prohibido** | ERP |
| **Dependencias** | G-F2 |
| **Riesgos** | Break IAM if still reads → coordinate WP02–03 |
| **Validaciones** | Grep L5 database_type |
| **Salida** | TenantContext sin mode consumible L5 |
| **PR** | PR-F3-01 |
| **Trace** | RD-03, ADR-005, RI-32 |

---

### F3-WP02 — user_context cleanup

| Campo | Contenido |
|-------|-----------|
| **Objetivo** | Eliminar branches database_type |
| **Alcance** | `core/auth/user_context.py` |
| **Permitido** | user_context.py |
| **Prohibido** | Other IAM presentation |
| **Dependencias** | F3-WP01 |
| **Riesgos** | IAM regression → full auth test suite |
| **Validaciones** | Unit + integration auth |
| **Salida** | Zero database_type in file |
| **PR** | PR-F3-02 |
| **Trace** | G-05, G-10, ADR-005 |

---

### F3-WP03 — rol_service cleanup

| Campo | Contenido |
|-------|-----------|
| **Objetivo** | Eliminar branches database_type RBAC |
| **Alcance** | `modules/rbac/application/services/rol_service.py` |
| **Permitido** | rol_service.py only |
| **Prohibido** | RBAC endpoints/schemas |
| **Dependencias** | F3-WP01 |
| **Riesgos** | Permission tests |
| **Validaciones** | RBAC unit tests |
| **Salida** | Zero database_type in file |
| **PR** | PR-F3-03 |
| **Trace** | G-05, ADR-003 |

---

### F3-WP04 — CI grep gate whitelist

| Campo | Contenido |
|-------|-----------|
| **Objetivo** | Fail CI if database_type outside whitelist |
| **Alcance** | CI script + documented whitelist |
| **Permitido** | `.github/workflows/`, `scripts/check_database_type_whitelist.py` |
| **Prohibido** | — |
| **Dependencias** | F3-WP01–03 |
| **Riesgos** | False positives → explicit whitelist |
| **Validaciones** | CI fails on injected violation test |
| **Salida** | G-F3 grep criteria met |
| **PR** | PR-F3-04 |
| **Trace** | G-05, G-10, G-F3 |

---

## 6. Resumen work packages

| Fase | WPs | PRs |
|------|-----|-----|
| F0 | 5 | 5 |
| F1 | 9 | 9 |
| F2 | 2 | 2 |
| F3 | 4 | 4 |
| **Total** | **20** | **20** |

*Nota: 18 PRs en plan consolidado `03` (WP05 F0 puede merge con WP04 si equipo acuerda).*

---

## 7. Conclusión

22 work packages atómicos con archivos, riesgos y validaciones explícitas. Ninguno modifica ERP ni contratos.
