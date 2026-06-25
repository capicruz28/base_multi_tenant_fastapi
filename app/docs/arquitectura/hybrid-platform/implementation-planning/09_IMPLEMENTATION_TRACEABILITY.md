# 09 — Implementation Traceability

**Etapa:** 5.7 — Implementation Planning  
**Versión:** IP-1.0  
**Baseline:** BL-1.0

---

## 1. Propósito

Matriz completa: cada work package / PR → ADR, RD, Guardrails, Invariantes, TD, docs, tests.

---

## 2. Matriz F0

| WP / PR | ADR | RD | Guardrails | Invariantes | TD | Docs ref | Tests requeridos |
|---------|-----|----|-----------|-----------|----|----------|------------------|
| F0-WP01 PR-F0-01 | 001 | RD-06, RD-07 | G-02, G-16 | RI-36 | TD-01 | E5-01 Gateway, BL-05 §F0 | conftest hybrid fixtures |
| F0-WP02 PR-F0-02 | 001, 006 | RD-08 | G-20 | RI-39, RI-11 | TD-08 | BL-03 RD-08, E4-08 RR-30 | test_hybrid_wrong_route |
| F0-WP03 PR-F0-03 | 006 | RD-06 | G-20 | RI-11, RI-40 | TD-08 | E5-08 Query exec | test_hybrid_tenant_isolation |
| F0-WP04 PR-F0-04 | 009 | RD-05 | G-08 | RI-18 | — | E4 impersonation flow | test_hybrid_impersonation |
| F0-WP05 PR-F0-05 | — | — | G-02 | — | — | BL-05 C-08 | CI baseline artifact |

---

## 3. Matriz F1

| WP / PR | ADR | RD | Guardrails | Invariantes | TD | Docs ref | Tests requeridos |
|---------|-----|----|-----------|-----------|----|----------|------------------|
| F1-WP01 PR-F1-01 | — | RD-06 | G-01 | — | TD-11 | E5-04 Engine | shutdown smoke |
| F1-WP02 PR-F1-02 | 001 | RD-08 | G-13 | RI-38 | TD-02 | E5-02 Metadata, E5-10 Cache | test cache TTL |
| F1-WP03 PR-F1-03 | 001 | RD-01, RD-06 | G-05 | RI-36 | TD-01 | E5-10 L-A | test route cache hits |
| F1-WP04 PR-F1-04 | 001, 006 | RD-08, RD-07 | G-05, G-09, G-10 | RI-39, RI-35, RI-36 | TD-03, TD-04 | E5-03 Connection | F0-02 + mock dedicated |
| F1-WP05 PR-F1-05 | 006 | RD-06 | G-20 | RI-40 | TD-08 | E5-08 | unit filter policy |
| F1-WP06 PR-F1-06 | 001 | RD-06, RD-07 | G-07, G-09 | RI-31 | TD-06, TD-07 | E5-01, E5-08 | full integration |
| F1-WP07 PR-F1-07 | — | RD-08 amended | G-15 | RI-38 | — | BL-03 RD-08 | metric assertion |
| F1-WP08 PR-F1-08 | 001 | RD-06 | G-02 | RI-36, RI-37 | TD-01 | G-F1 BL-05 | test_hybrid_gateway_* |
| F1-WP09 PR-F1-09 | — | RD-06-E | G-09 | RI-31 | — | E5-09 Repository | grep + repo tests |

---

## 4. Matriz F2

| WP / PR | ADR | RD | Guardrails | Invariantes | TD | Docs ref | Tests requeridos |
|---------|-----|----|-----------|-----------|----|----------|------------------|
| F2-WP01 PR-F2-01 | — | RD-01 | G-02 | — | TD-05 | E5-08 perf | benchmark script |
| F2-WP02 PR-F2-02 | — | — | G-02 | RI-37 | — | BL-05 G-F2 | shared-regression CI |

---

## 5. Matriz F3

| WP / PR | ADR | RD | Guardrails | Invariantes | TD | Docs ref | Tests requeridos |
|---------|-----|----|-----------|-----------|----|----------|------------------|
| F3-WP01 PR-F3-01 | 005 | RD-03 | G-05, G-10 | RI-32 | — | BL-03, E4-03 | middleware/auth integration |
| F3-WP02 PR-F3-02 | 005 | RD-03 | G-05, G-10 | RI-32 | — | E0 user_context | IAM unit+integration |
| F3-WP03 PR-F3-03 | 003, 005 | RD-03, RD-15 | G-05, G-10 | RI-32, RI-07 | — | ADR-003 | RBAC tests |
| F3-WP04 PR-F3-04 | 005 | RD-03 | G-05, G-10 | RI-32 | — | G-10 whitelist | CI grep self-test |

---

## 6. Trazabilidad ADR → PRs

| ADR | PRs que implementan |
|-----|---------------------|
| ADR-001 | F1-02,03,04,06,08 |
| ADR-002 | (F5b blocked) — F1 ensures CP route compatible |
| ADR-003 | F3-03 |
| ADR-005 | F3-01,02,03,04 |
| ADR-006 | F0-02,03, F1-04,05 |
| ADR-009 | F0-04 |
| ADR-011 | (F3.5 gate — not IP-1.0) |

---

## 7. Trazabilidad RD → PRs

| RD | PRs |
|----|-----|
| RD-01 | F1-03, F2-01 |
| RD-03 | F3-* |
| RD-05 | F0-04 |
| RD-06 | F0-01,03, F1-03,04,06,08,09 |
| RD-07 | F1-04,06 |
| RD-08 | F0-02, F1-02,04,07 |
| RD-11 | (Closed BL) — F1 routing CP-compatible |

---

## 8. Trazabilidad Guardrails → PRs

| Guardrail | Enforcement PRs |
|-----------|-----------------|
| G-01 | All — erp-guard CI |
| G-02 | F0-05, F1-08, F2-* |
| G-05 | F1-03–06, F3-* |
| G-07 | All — openapi CI |
| G-09 | F1-04,06,09 |
| G-10 | F1 whitelist only, F3 grep |
| G-17 | No PR violates (TD-05) |
| G-20 | F0-03, F1-05 |

---

## 9. Trazabilidad Invariantes críticos

| Invariante | Validado en |
|------------|-------------|
| RI-11 | F0-03, F1-05 |
| RI-18 | F0-04 |
| RI-31 | F1-06, F1-09 |
| RI-32 | F3-* |
| RI-36 | F0-01, F1-03,08 |
| RI-39 | F0-02, F1-04 |
| RI-40 | F0-03, F1-05 |

---

## 10. Tests requeridos — inventario acumulado

| Test file / job | Introducido | Mantenido |
|-----------------|-------------|-----------|
| `conftest_hybrid.py` | F0-01 | All |
| `test_hybrid_wrong_route.py` | F0-02 | All |
| `test_hybrid_tenant_isolation.py` | F0-03 | All |
| `test_hybrid_impersonation_harness.py` | F0-04 | All |
| CI baseline artifact | F0-05 | F2+ compare |
| `test_hybrid_gateway_*.py` | F1-08 | All |
| Benchmark script | F2-01 | — |
| `shared-regression` job | F2-02 | All |
| `check_database_type_whitelist.py` | F3-04 | All |

---

## 11. Documentos referencia por fase

| Fase | Lectura obligatoria pre-inicio |
|------|-------------------------------|
| F0 | BL-01, BL-05 §2, `05_VALIDATION_MATRIX` §F0 |
| F1 | E5-01–04,08,10, BL-03, `06_ROLLBACK` §F1 |
| F2 | BL-05 G-F2, `04_DOD` §F2 |
| F3 | BL-03 RD-03, ADR-005, `08_CHECKLISTS` §F3 |

---

## 12. Conclusión

Trazabilidad **100%** WP→artefactos BL-1.0. PR body debe citar fila de esta matriz.
