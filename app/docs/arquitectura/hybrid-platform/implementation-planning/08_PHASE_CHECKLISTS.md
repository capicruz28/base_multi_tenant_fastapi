# 08 — Phase Checklists

**Etapa:** 5.7 — Implementation Planning  
**Versión:** IP-1.0  
**Baseline:** BL-1.0

---

## 1. Pre-flight — Antes de Etapa 6

| # | Item | Owner | ☐ |
|---|------|-------|---|
| PF-01 | BL-1.0 ack por Tech Lead | Tech Lead | |
| PF-02 | Guardrails G-01–G-20 distribuidos | Architect | |
| PF-03 | IP-1.0 docs ack equipo | All | |
| PF-04 | Branch protection configured | DevOps | |
| PF-05 | PR template con traceability | Tech Lead | |
| PF-06 | `dedicated_enabled=false` verified prod | SRE | |
| PF-07 | Staging shared tenant creds available | QA | |
| PF-08 | Architect reviewer assigned F1 | Architect | |

**Gate:** All PF-* checked → **Start F0**

---

## 2. Gate G-F0 — Entrada F1

| # | Item | Evidencia | ☐ |
|---|------|-----------|---|
| GF0-01 | PR-F0-01–05 merged | Git | |
| GF0-02 | DOD-F0 satisfied (`04`) | Review | |
| GF0-03 | Zero prod code in F0 diff | git stat | |
| GF0-04 | Harness dedicated mock green | CI | |
| GF0-05 | Wrong-route test fails on violation | CI log | |
| GF0-06 | Baseline artifact stored | CI artifact | |
| GF0-07 | Tag `hybrid-gate-f0` created | Git | |

**Sign-off:** Tech Lead + Architect → **F1 authorized**

---

## 3. Gate G-F1 — Entrada F2

| # | Item | Evidencia | ☐ |
|---|------|-----------|---|
| GF1-01 | PR-F1-01–09 merged | Git | |
| GF1-02 | DOD-F1 satisfied | Review | |
| GF1-03 | Shared suite = F0 baseline count pass | CI | |
| GF1-04 | Dedicated mock tests green | CI | |
| GF1-05 | close_all_async_engines verified | Manual/log | |
| GF1-06 | execute_* signatures unchanged | diff | |
| GF1-07 | QueryAuditor pass | CI | |
| GF1-08 | OpenAPI diff clean cumulative F1 | CI | |
| GF1-09 | No new database_type L5 | grep | |
| GF1-10 | Tag `hybrid-gate-f1` | Git | |

**Sign-off:** Tech Lead + Architect + QA → **F2 authorized**

---

## 4. Gate G-F2 — Entrada F3

| # | Item | Evidencia | ☐ |
|---|------|-----------|---|
| GF2-01 | PR-F2-01–02 merged | Git | |
| GF2-02 | DOD-F2 satisfied | Review | |
| GF2-03 | Benchmark p95 within ±10% | Report | |
| GF2-04 | shared-regression required on main | GitHub settings | |
| GF2-05 | G-02 checklist complete | Signed doc | |
| GF2-06 | Staging smoke S-01–S-06 pass | QA log | |
| GF2-07 | Tag `hybrid-gate-f2` | Git | |

**Sign-off:** Tech Lead + QA + SRE → **F3 authorized**

---

## 5. Gate G-F3 — Gate Review (F4)

| # | Item | Evidencia | ☐ |
|---|------|-----------|---|
| GF3-01 | PR-F3-01–04 merged | Git | |
| GF3-02 | DOD-F3 satisfied | Review | |
| GF3-03 | database_type grep CI green | CI | |
| GF3-04 | user_context + rol_service clean | grep | |
| GF3-05 | Auth + RBAC full pass | CI | |
| GF3-06 | RI-32 architect verification | Architect sign | |
| GF3-07 | OpenAPI diff clean cumulative | CI | |
| GF3-08 | Zero ERP modules diff cumulative E6 | git | |
| GF3-09 | Tag `hybrid-bl10-f0-f3-complete` | Git | |
| GF3-10 | Q-030 spec 1-pager submitted | Doc link | |
| GF3-11 | F3.5 catalog list draft (ADR-011) | Doc | |
| GF3-12 | Gate Review meeting held | Minutes | |
| GF3-13 | Go/No-Go F4 decision recorded | Doc | |

**Sign-off:** Architect Principal + Steering → **F4 or hold**

---

## 6. Revisión arquitectónica pre-merge (todo PR F1+)

| # | Verificar | Referencia |
|---|-----------|------------|
| AR-01 | Scope in whitelist | `05_IMPLEMENTATION_BASELINE` §9 |
| AR-02 | ADR compliance | `02_ADR_STATUS` |
| AR-03 | RD compliance | `03_RUNTIME_DECISION_STATUS` |
| AR-04 | Guardrails | `05_IMPLEMENTATION_GUARDRAILS` |
| AR-05 | No ERP diff | G-01 |
| AR-06 | OpenAPI | G-07 |
| AR-07 | Trace row complete | `09` |
| AR-08 | Rollback documented | `06` |

Label: `arch-approved`

---

## 7. Revisión pre-merge (todo PR)

| # | Verificar |
|---|-----------|
| R-01 | DOD-PR-01–10 |
| R-02 | CI green |
| R-03 | Tests added/updated |
| R-04 | No secrets |
| R-05 | PR size ≤500 LOC warn |

---

## 8. Post-merge monitor (F1 PRs alto riesgo)

| PR | Monitor 30 min |
|----|----------------|
| F1-04, F1-06 | Error rate, latency staging |
| F3-01 | Auth failures |

---

## 9. Conclusión

Checklists **binarios**. Gates **secuenciales**. Sin atajos F3 sin G-F2.
