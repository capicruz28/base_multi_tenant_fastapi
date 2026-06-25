# 05 — Validation Matrix

**Etapa:** 5.7 — Implementation Planning  
**Versión:** IP-1.0  
**Baseline:** BL-1.0

---

## 1. Propósito

Estrategia de validación por fase: automática, manual, benchmarks, smoke, regresión, performance, seguridad.

---

## 2. Matriz por fase

### F0 — Test Harness

| Tipo | Validación | Automática | Manual | Criterio pass |
|------|------------|------------|--------|---------------|
| Unit | Harness fixtures load | ✅ pytest | — | 100% pass |
| Integration | Dedicated mock engine key | ✅ | — | Assert key |
| Adversarial | Wrong-route failure | ✅ | — | Must fail on bad route |
| Isolation | Cross-tenant negative | ✅ | — | 403/404/empty |
| Impersonation | JWT target tenant | ✅ | — | Per RD-05 |
| Regression | Full existing suite | ✅ CI | — | No new failures |
| Security | No prod code change | ✅ diff gate | Review | Zero app/ changes |
| Baseline | Test count artifact | ✅ CI | — | Stored |

---

### F1 — Gateway Consolidation

| Tipo | Validación | Automática | Manual | Criterio pass |
|------|------------|------------|--------|---------------|
| Unit | Cache TTL expiry | ✅ | — | TTL works |
| Unit | Route cache hit | ✅ | — | 1 lookup/N ops |
| Integration | Dedicated mock path | ✅ | — | F1-08 green |
| Integration | Shared path identical | ✅ | Compare F0 baseline | Same results |
| Regression | Full pytest | ✅ CI | — | 100% |
| Security | QueryAuditor | ✅ prod rules | — | No violations |
| Security | Tenant filter | ✅ isolation tests | — | G-20 |
| Security | Fail-closed dedicated | ✅ F0-02 | — | RI-39 |
| Performance | Smoke latency | ⚠️ optional | Staging spot | No >2x p95 |
| OpenAPI | Schema diff | ✅ CI | — | Zero breaking |
| Grep | No ERP diff | ✅ script | — | Zero modules |
| Grep | create_async_engine whitelist | ✅ | — | G-09 |
| Manual | Shutdown engines | — | ✅ deploy restart | No leak warning |
| Manual | `.env.example` TTL | — | ✅ review | Documented |

---

### F2 — Shared Regression

| Tipo | Validación | Automática | Manual | Criterio pass |
|------|------------|------------|--------|---------------|
| Benchmark | execute_* p50/p95 | ✅ script | Review report | ±10% baseline |
| Regression | shared-regression job | ✅ required | — | 100% |
| Integration | IAM auth flows | ✅ | — | Pass |
| Integration | ERP smoke subset | ✅ markers | — | Pass |
| Smoke | Staging shared tenant | — | ✅ SRE | Login+ORG list |
| OpenAPI | Diff | ✅ | — | Clean |
| Performance | Pool metrics | — | ✅ optional | No saturation |
| Security | Pen test delta | — | — | N/A F2 |

---

### F3 — L5 Cleanup

| Tipo | Validación | Automática | Manual | Criterio pass |
|------|------------|------------|--------|---------------|
| Grep | database_type whitelist | ✅ CI script | — | Pass |
| Unit | user_context | ✅ | — | Pass |
| Unit | rol_service | ✅ | — | Pass |
| Integration | Auth login/refresh | ✅ | — | Pass |
| Integration | RBAC permission check | ✅ | — | Pass |
| Integration | Middleware tenant resolve | ✅ | — | Host→tenant |
| Regression | Full suite | ✅ | — | 100% |
| Security | RI-32 L5 no mode | ✅ grep + review | Architect | Pass |
| OpenAPI | Diff | ✅ | — | Clean |
| Manual | Impersonation smoke | — | ✅ if available | No regression |

---

## 3. Validaciones transversales (todo PR)

| ID | Validación | Tool |
|----|------------|------|
| V-X01 | pytest | CI |
| V-X02 | ruff/linter | CI |
| V-X03 | OpenAPI diff | CI script |
| V-X04 | ERP path guard | `git diff --name-only` script |
| V-X05 | PR size warning | >500 LOC warn |
| V-X06 | Secret scan | gitleaks optional |

---

## 4. Benchmarks — protocolo F2

| Parámetro | Valor |
|-----------|-------|
| Endpoint sample | 3 read endpoints ORG/INV list |
| Iterations | 100 per endpoint |
| Environment | Staging shared tenant |
| Metrics | p50, p95, p99 latency |
| Threshold | **±10% p95** vs F0 baseline |
| Fail action | Block F3; investigate F1 PR |

---

## 5. Smoke tests — protocolo manual

| Step | Acción | Expected |
|------|--------|----------|
| S-01 | Login shared tenant | 200 + JWT |
| S-02 | GET /me | 200 session valid |
| S-03 | ORG empresa list | 200 paginated |
| S-04 | INV producto list | 200 |
| S-05 | Refresh token | 200 new access |
| S-06 | Logout | 200 idempotent |

Ejecutar: post-F2, pre-F3, post-F3.

---

## 6. Seguridad — checklist

| ID | Check | Fase |
|----|-------|------|
| SEC-01 | Tenant isolation | F0,F1 |
| SEC-02 | Wrong dedicated route | F0,F1 |
| SEC-03 | QueryAuditor | F1 |
| SEC-04 | No skip tenant filter prod | F1 |
| SEC-05 | No mode leak API response | F1,F3 |
| SEC-06 | database_type L5 grep | F3 |

---

## 7. Regresión — suites

| Suite | Cuándo | Required |
|-------|--------|----------|
| Full pytest | Every PR | ✅ |
| hybrid-* markers | F0+ | ✅ |
| IAM sessions v2 | F1,F3 | ✅ |
| test_tenant_isolation_comprehensive | F1 | ✅ |
| shared-regression marker | F2+ | ✅ required check |

---

## 8. Conclusión

Validación **automática-first**; manual solo smoke/benchmark/shutdown. Umbrales numéricos explícitos.
