# 04 — Definition of Done

**Etapa:** 5.7 — Implementation Planning  
**Versión:** IP-1.0  
**Baseline:** BL-1.0

---

## 1. Definition of Done — PR (obligatoria todo merge)

Un PR **solo** puede merge cuando **todas** las condiciones siguientes son verdaderas:

| # | Criterio | Verificación |
|---|----------|--------------|
| DOD-PR-01 | Scope dentro WP y `05_IMPLEMENTATION_BASELINE` whitelist | Reviewer checklist |
| DOD-PR-02 | Zero files under `app/modules/{org,inv,pur,...}/` modified | `git diff --name-only` |
| DOD-PR-03 | Zero OpenAPI breaking diff | CI artifact / manual diff |
| DOD-PR-04 | All CI checks green | GitHub |
| DOD-PR-05 | New/changed tests pass | pytest |
| DOD-PR-06 | Traceability row in PR body (`09`) | Template |
| DOD-PR-07 | Rollback note in PR body (`06`) | Template |
| DOD-PR-08 | Architect ack for F1+ infra PRs | Label `arch-approved` |
| DOD-PR-09 | No `database_type` new usages outside whitelist (F1+) | grep CI or manual |
| DOD-PR-10 | No secrets in diff | Review |

---

## 2. Definition of Done — Fase F0

F0 está **DONE** cuando:

| # | Criterio | Evidencia |
|---|----------|-----------|
| DOD-F0-01 | PR-F0-01 through PR-F0-05 merged to `main` | Git log |
| DOD-F0-02 | Dedicated mock harness resolves engine key in test | Test output |
| DOD-F0-03 | Wrong-route test **fails** on simulated violation | CI |
| DOD-F0-04 | Tenant isolation harness ≥3 scenarios green | Test report |
| DOD-F0-05 | Impersonation harness documents RD-05 behavior | Test + comment |
| DOD-F0-06 | CI baseline artifact published | Artifact URL |
| DOD-F0-07 | **Gate G-F0** checklist 100% (`08` §F0) | Signed checklist |
| DOD-F0-08 | Zero production code changed | Diff stat |

**No ambigüedad:** Si DOD-F0-08 false → F0 **NOT DONE** regardless of tests.

---

## 3. Definition of Done — Fase F1

F1 está **DONE** cuando:

| # | Criterio | Evidencia |
|---|----------|-----------|
| DOD-F1-01 | PR-F1-01 through PR-F1-09 merged | Git log |
| DOD-F1-02 | `close_all_async_engines()` called on shutdown | Code review + manual |
| DOD-F1-03 | Metadata TTL configurable via settings | `.env.example` + test |
| DOD-F1-04 | Intra-request cache: 2+ execute_* = 1 metadata lookup (test) | Test |
| DOD-F1-05 | Dedicated mock: correct engine; shared mock: unchanged | PR-F1-08 tests |
| DOD-F1-06 | Dedicated explicit missing metadata → error not shared | F0-02 still passes |
| DOD-F1-07 | Fallback shared emits metric/log | Test or log capture |
| DOD-F1-08 | `execute_*` / UoW signatures **unchanged** | diff grep |
| DOD-F1-09 | QueryAuditor production rules pass | CI |
| DOD-F1-10 | Shared integration suite **100%** pass vs F0 baseline | CI compare |
| DOD-F1-11 | **Gate G-F1** checklist 100% | Signed |

---

## 4. Definition of Done — Fase F2

F2 está **DONE** cuando:

| # | Criterio | Evidencia |
|---|----------|-----------|
| DOD-F2-01 | PR-F2-01, PR-F2-02 merged | Git log |
| DOD-F2-02 | Benchmark report: p95 execute_* within **±10%** of F0 baseline | Doc/table in PR |
| DOD-F2-03 | `shared-regression` CI job **required** on main | Branch protection |
| DOD-F2-04 | G-02 checklist all items checked | `08` §F2 |
| DOD-F2-05 | Staging smoke shared tenant manual pass | SRE sign-off |
| DOD-F2-06 | **Gate G-F2** checklist 100% | Signed |

---

## 5. Definition of Done — Fase F3

F3 está **DONE** cuando:

| # | Criterio | Evidencia |
|---|----------|-----------|
| DOD-F3-01 | PR-F3-01 through PR-F3-04 merged | Git log |
| DOD-F3-02 | `database_type` **absent** from `user_context.py`, `rol_service.py` | grep |
| DOD-F3-03 | TenantContext **no public** installation mode for L5 | Code review |
| DOD-F3-04 | CI grep gate passes; fails on intentional violation | CI test |
| DOD-F3-05 | Whitelist exactly: infra files per G-10 + middleware internal | Script config |
| DOD-F3-06 | Auth + RBAC full test suites pass | CI |
| DOD-F3-07 | OpenAPI diff clean | CI |
| DOD-F3-08 | **Gate G-F3** checklist 100% | Signed |
| DOD-F3-09 | Gate Review meeting scheduled | Calendar invite |

---

## 6. Definition of Done — Etapa 6 scope (F0–F3 completa)

Etapa 6 scope BL-1.0 está **DONE** cuando:

| # | Criterio |
|---|----------|
| DOD-E6-01 | DOD-F0 through DOD-F3 all satisfied |
| DOD-E6-02 | Tag `hybrid-bl10-f0-f3-complete` on main |
| DOD-E6-03 | Implementation summary doc in repo (optional `docs/implementation/F0-F3_REPORT.md`) |
| DOD-E6-04 | Zero ERP module production diffs cumulative |
| DOD-E6-05 | Gate Review completed — Go/No-Go F4 recorded |
| DOD-E6-06 | Q-030 spec 1-pager submitted (may be pending approval — not blocker for DOD-E6 if scheduled) |

---

## 7. Anti-patterns — NOT DONE

| Condición | Veredicto |
|-----------|-----------|
| "Tests pass but OpenAPI changed" | **NOT DONE** |
| "F1 merged without G-F0" | **NOT DONE** — revert |
| "database_type in new L5 file" | **NOT DONE** |
| "Skipped F2 benchmarks" | F3 **blocked** |
| "Single mega-PR F1" | **NOT DONE** — split required |

---

## 8. Plantilla PR (obligatoria)

```markdown
## Work Package
- ID: F?_WP??
- Phase: F?

## Traceability
- ADR: 
- RD: 
- Guardrails: 
- TD: 

## Rollback
- Risk: Low/Med/High
- Revert: 
- Re-test: 

## Checklist
- [ ] DOD-PR-01 … DOD-PR-10
```

---

## 9. Conclusión

DoD **binaria** — cumple todas las filas o la fase **no** está terminada.
