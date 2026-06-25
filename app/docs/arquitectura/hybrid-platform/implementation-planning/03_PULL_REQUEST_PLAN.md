# 03 — Pull Request Plan

**Etapa:** 5.7 — Implementation Planning  
**Versión:** IP-1.0  
**Baseline:** BL-1.0  
**Principio:** PRs pequeños — target **≤400 LOC** diff (excl. tests)

---

## 1. Mapa completo de PRs

| Orden | PR ID | Fase | WP | Título | Tamaño | Deps |
|-------|-------|------|-----|--------|--------|------|
| 1 | PR-F0-01 | F0 | WP01 | test: hybrid dedicated mock harness | S (~200) | — |
| 2 | PR-F0-02 | F0 | WP02 | test: hybrid wrong-route adversarial | S (~150) | PR-F0-01 |
| 3 | PR-F0-03 | F0 | WP03 | test: hybrid tenant isolation harness | S (~180) | PR-F0-01 |
| 4 | PR-F0-04 | F0 | WP04 | test: hybrid impersonation harness | S (~150) | PR-F0-01 |
| 5 | PR-F0-05 | F0 | WP05 | ci: shared baseline artifact + hybrid job | S (~100) | PR-F0-01–04 |
| 6 | PR-F1-01 | F1 | WP01 | infra: close async engines on shutdown | XS (~30) | G-F0 |
| 7 | PR-F1-02 | F1 | WP02 | infra: metadata cache TTL configurable | S (~120) | G-F0 |
| 8 | PR-F1-03 | F1 | WP03 | infra: intra-request route cache L-A | M (~250) | PR-F1-02 |
| 9 | PR-F1-04 | F1 | WP04 | infra: connection resolution fail-closed dedicated | M (~300) | PR-F1-02,03 |
| 10 | PR-F1-05 | F1 | WP05 | infra: defensive tenant filter dedicated | S (~100) | PR-F1-04 |
| 11 | PR-F1-06 | F1 | WP06 | infra: queries_async pipeline alignment | M (~280) | PR-F1-03–05 |
| 12 | PR-F1-07 | F1 | WP07 | infra: fallback shared metrics/logging | XS (~80) | PR-F1-04 |
| 13 | PR-F1-08 | F1 | WP08 | test: hybrid gateway integration post-F1 | S (~200) | PR-F1-04–06 |
| 14 | PR-F1-09 | F1 | WP09 | infra: repository gateway delegation fixes | S (~150) | PR-F1-06 |
| 15 | PR-F2-01 | F2 | WP01 | perf: execute_* benchmark baseline | S (~150) | G-F1 |
| 16 | PR-F2-02 | F2 | WP02 | ci: shared-regression required gate | S (~100) | G-F1 |
| 17 | PR-F3-01 | F3 | WP01 | refactor: middleware hide installation mode L5 | S (~120) | G-F2 |
| 18 | PR-F3-02 | F3 | WP02 | refactor: user_context remove database_type | S (~100) | PR-F3-01 |
| 19 | PR-F3-03 | F3 | WP03 | refactor: rol_service remove database_type | S (~100) | PR-F3-01 |
| 20 | PR-F3-04 | F3 | WP04 | ci: database_type whitelist grep gate | S (~120) | PR-F3-01–03 |

**Total: 20 PRs** | Est. LOC producción: ~1,400 | Est. LOC tests: ~1,100

---

## 2. Detalle por PR

### PR-F0-01 — test: hybrid dedicated mock harness

| Campo | Valor |
|-------|-------|
| **Objetivo** | Foundation fixtures dedicated tenant |
| **Archivos** | `tests/integration/conftest_hybrid.py`, `helpers/hybrid_mock_metadata.py` |
| **Prohibido** | `app/modules/**`, infra prod |
| **Rollback** | Revert commit — zero prod impact |
| **Tests repetir** | Full CI |
| **Review arch** | `05_IMPLEMENTATION_BASELINE` §2 F0 |

---

### PR-F0-02 — test: hybrid wrong-route adversarial

| Campo | Valor |
|-------|-------|
| **Objetivo** | Assert RI-39 fail-closed |
| **Archivos** | `tests/integration/test_hybrid_wrong_route.py` |
| **Dependencias** | PR-F0-01 |
| **Rollback** | Revert — tests only |
| **Tests repetir** | hybrid job + unit |
| **Review arch** | RD-08, RI-39 |

---

### PR-F0-03 — test: hybrid tenant isolation harness

| Campo | Valor |
|-------|-------|
| **Objetivo** | G-20 harness coverage |
| **Archivos** | `tests/integration/test_hybrid_tenant_isolation.py` |
| **Rollback** | Revert |
| **Review arch** | G-20, RI-11 |

---

### PR-F0-04 — test: hybrid impersonation harness

| Campo | Valor |
|-------|-------|
| **Objetivo** | RD-05 test contract |
| **Archivos** | `tests/integration/test_hybrid_impersonation_harness.py` |
| **Rollback** | Revert |
| **Review arch** | RD-05, RI-18 |

---

### PR-F0-05 — ci: shared baseline artifact

| Campo | Valor |
|-------|-------|
| **Objetivo** | G-F0 baseline capture |
| **Archivos** | `.github/workflows/ci.yml`, optional `scripts/capture_test_baseline.py` |
| **Rollback** | Revert CI job |
| **Tests repetir** | CI pipeline |
| **Review arch** | C-08 |

---

### PR-F1-01 — infra: close async engines on shutdown

| Campo | Valor |
|-------|-------|
| **Objetivo** | EM-G01 fix |
| **Archivos** | `app/main.py` |
| **Rollback** | Revert single file — safe |
| **Riesgos** | Low — additive shutdown call |
| **Tests repetir** | Smoke startup/shutdown |
| **Review arch** | TD-11, `04_ENGINE_MANAGEMENT` |

---

### PR-F1-02 — infra: metadata cache TTL

| Campo | Valor |
|-------|-------|
| **Objetivo** | TD-02 |
| **Archivos** | `app/core/tenant/cache.py`, `app/core/config.py`, `.env.example` |
| **Rollback** | Revert — restore default behavior |
| **Tests repetir** | cache unit + integration |
| **Review arch** | TD-02, G-13 |

---

### PR-F1-03 — infra: intra-request route cache

| Campo | Valor |
|-------|-------|
| **Objetivo** | TD-01 |
| **Archivos** | `app/core/tenant/routing.py`, `app/infrastructure/database/queries_async.py` |
| **Rollback** | Revert — perf degrades, func OK |
| **Riesgos** | Medium — core path |
| **Tests repetir** | F0 harness + shared integration |
| **Review arch** | RD-01, TD-01 |

---

### PR-F1-04 — infra: connection resolution fail-closed

| Campo | Valor |
|-------|-------|
| **Objetivo** | RD-08, RI-39 |
| **Archivos** | `routing.py`, `connection_async.py` |
| **Rollback** | **High care** — revert + run F0 wrong-route |
| **Riesgos** | **Critical** |
| **Tests repetir** | All hybrid + tenant isolation |
| **Review arch** | ADR-001, RD-08 |

---

### PR-F1-05 — infra: defensive tenant filter

| Campo | Valor |
|-------|-------|
| **Objetivo** | TD-08 |
| **Archivos** | `query_helpers.py` |
| **Rollback** | Revert single file |
| **Review arch** | ADR-006, TD-08 |

---

### PR-F1-06 — infra: queries_async pipeline

| Campo | Valor |
|-------|-------|
| **Objetivo** | RD-06 gateway |
| **Archivos** | `queries_async.py` |
| **Rollback** | Revert — **critical** |
| **Tests repetir** | Full regression |
| **Review arch** | RD-06, G-07, G-09 |

---

### PR-F1-07 — infra: fallback metrics

| Campo | Valor |
|-------|-------|
| **Objetivo** | RD-08 amended |
| **Archivos** | `routing.py` and/or `cache.py` |
| **Rollback** | Revert |
| **Review arch** | RD-08 amended |

---

### PR-F1-08 — test: gateway integration

| Campo | Valor |
|-------|-------|
| **Objetivo** | G-F1 evidence |
| **Archivos** | `tests/integration/test_hybrid_gateway_*.py` |
| **Rollback** | Revert |
| **Review arch** | G-F1 |

---

### PR-F1-09 — infra: repository fixes

| Campo | Valor |
|-------|-------|
| **Objetivo** | RD-06-E02 |
| **Archivos** | Max 2 files `repositories/` |
| **Rollback** | Revert per file |
| **Review arch** | `09_REPOSITORY_INTERACTION` |

---

### PR-F2-01 — perf: benchmark baseline

| Campo | Valor |
|-------|-------|
| **Objetivo** | G-F2 latency doc |
| **Archivos** | `tests/perf/` or `scripts/`, doc snippet |
| **Rollback** | Revert |
| **Review arch** | G-F2 |

---

### PR-F2-02 — ci: shared-regression gate

| Campo | Valor |
|-------|-------|
| **Objetivo** | G-02 required check |
| **Archivos** | `.github/workflows/ci.yml` |
| **Rollback** | Revert CI — restore optional |
| **Review arch** | G-02 |

---

### PR-F3-01 — refactor: middleware hide mode

| Campo | Valor |
|-------|-------|
| **Objetivo** | RD-03 |
| **Archivos** | `middleware.py`, `context.py` |
| **Rollback** | Revert — auth may break if incomplete |
| **Tests repetir** | Auth integration full |
| **Review arch** | RD-03, ADR-005, RI-32 |

---

### PR-F3-02 — refactor: user_context

| Campo | Valor |
|-------|-------|
| **Objetivo** | G-05 L5 cleanup |
| **Archivos** | `user_context.py` |
| **Rollback** | Revert |
| **Tests repetir** | IAM unit + integration |
| **Review arch** | G-10 |

---

### PR-F3-03 — refactor: rol_service

| Campo | Valor |
|-------|-------|
| **Objetivo** | G-05 RBAC |
| **Archivos** | `rol_service.py` |
| **Rollback** | Revert |
| **Tests repetir** | RBAC tests |
| **Review arch** | ADR-003 |

---

### PR-F3-04 — ci: database_type grep gate

| Campo | Valor |
|-------|-------|
| **Objetivo** | G-F3 enforcement |
| **Archivos** | `scripts/check_database_type_whitelist.py`, CI |
| **Rollback** | Revert script |
| **Review arch** | G-05, G-10, G-F3 |

---

## 3. Reglas de merge

| Regla | Descripción |
|-------|-------------|
| MR-01 | 1 approval infra + 1 architect for F1 PRs |
| MR-02 | QA sign-off on F2-02 |
| MR-03 | Squash merge preferido |
| MR-04 | PR title prefix: `test:` `infra:` `ci:` `refactor:` `perf:` |
| MR-05 | PR body MUST link WP + trace row from `09` |
| MR-06 | OpenAPI diff artifact attached |
| MR-07 | No merge Friday prod deploy window |

---

## 4. Rollback por PR (resumen)

| Riesgo rollback | PRs |
|-----------------|-----|
| **Bajo** (tests/CI only) | F0-*, F2-*, F1-01, F1-07, F3-04 |
| **Medio** | F1-02,03,05,09, F3-01,02,03 |
| **Alto** | F1-04, F1-06 |

Detalle: `06_ROLLBACK_STRATEGY.md`

---

## 5. Conclusión

20 PRs secuenciales, ninguno >400 LOC prod. Orden estricto en §1.
