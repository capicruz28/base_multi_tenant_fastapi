# 06 — Document Traceability

**Etapa:** 5.6 — Architecture Baseline Freeze  
**Versión baseline:** BL-1.0  
**Fecha:** 2026-06-25

---

## 1. Propósito

Mapa completo de trazabilidad desde AS-IS hasta Architecture Baseline. Cada etapa alimenta la siguiente; BL-1.0 consolida y resuelve contradicciones.

---

## 2. Cadena de etapas

```
Etapa 0 — AS-IS Audit
    ↓ hallazgos, riesgos, baseline código
Etapa 1 — Conceptual Architecture
    ↓ principios P1–P7, ADR draft, open questions
Etapa 2 — Impact Assessment
    ↓ change surface, guardrails, protected components
Etapa 3 — Canonical Data Model
    ↓ CP/DP ownership, P0 resolution
Etapa 4 — Runtime Architecture
    ↓ RD-01–15, invariantes, flows
Etapa 5 — Technical Infrastructure
    ↓ TD-01–13, gateway, roadmap
Etapa 5.5 — Architecture Validation
    ↓ adversarial review, GO WITH CONDITIONS
Etapa 5.6 — Architecture Baseline Freeze  ← BL-1.0
    ↓
Etapa 6 — Implementation (F0–F3 authorized)
```

---

## 3. Etapa 0 — AS-IS Audit

| Documento | Path | Rol | → Baseline |
|-----------|------|-----|------------|
| Backend AS-IS | `01_BACKEND_AS_IS.md` | Mapa módulos | Change surface input |
| SQLAlchemy Audit | `02_SQLALCHEMY_AUDIT.md` | execute_*, UoW | E5 session/engine design |
| Onboarding Audit | `03_ONBOARDING_AUDIT.md` | Single TX | ADR-004, RD-12 |
| IAM Dependencies | `04_IAM_DEPENDENCIES.md` | Tenant resolution | RD-02, RD-04 |
| Database Usage | `05_DATABASE_USAGE.md` | Tablas/módulos | E3 ownership |
| Risks Dedicated | `06_RISKS_FOR_DEDICATED_DB.md` | R-C*, R-I* | ADR mapping, risks 5.5 |

---

## 4. Etapa 1 — Conceptual

| Documento | Path | Rol | → Baseline |
|-----------|------|-----|------------|
| Conceptual Model | `01_CONCEPTUAL_MODEL.md` | P1–P7 | BL-P01–P08 |
| Platform Boundaries | `02_PLATFORM_BOUNDARIES.md` | Fronteras | ADR-001 |
| Domain Responsibilities | `03_DOMAIN_RESPONSIBILITIES.md` | Platform/IAM/ERP | E4 layers |
| ADR Draft | `04_ARCHITECTURE_DECISIONS_DRAFT.md` | **SUPERSEDED** | `02_ADR_STATUS.md` |
| Open Questions | `05_OPEN_QUESTIONS.md` | **SUPERSEDED** | `04_OPEN_QUESTIONS_STATUS.md` |

---

## 5. Etapa 2 — Impact

| Documento | Path | Rol | → Baseline |
|-----------|------|-----|------------|
| Architectural Impact | `impact-analysis/01_*.md` | Encapsulation | BL-P01 |
| Protected Components | `02_*.md` | ERP/API protected | §3 PROHIBIDO |
| Change Surface | `03_*.md` | 5–8% files | §9 whitelist |
| Backward Compatibility | `04_*.md` | G-02 | RD-08 |
| Guardrails | `05_*.md` | G-01–G-20 | Normative tier 2 |
| Impact Matrix | `06_*.md` | Risk matrix | 5.5 risks |
| Executive Summary | `07_*.md` | E2 summary | — |

---

## 6. Etapa 3 — Canonical Data Model

| Documento | Path | Rol | → Baseline |
|-----------|------|-----|------------|
| Canonical Model | `canonical-data-model/01_*.md` | Entidades | E4 contexts |
| Data Ownership | `02_*.md` | Dueños | ADR-001, 003 |
| SSOT | `03_*.md` | Autoridad | RD-15 |
| CP vs DP | `04_*.md` | Clasificación | RD-07 matrix |
| Lifecycle | `05_*.md` | Estados tenant | RD-13 |
| Dependencies | `06_*.md` | Dependencias datos | Saga F4 |
| Ownership Matrix | `07_*.md` | Matriz | ADR-003 |
| Data Risks | `08_*.md` | Riesgos | 5.5 AR-* |
| P0 Resolution | `09_*.md` | Q-001,002,020,032 | Closed BL |
| Executive Summary | `10_*.md` | E3 summary | — |

---

## 7. Etapa 4 — Runtime

| Documento | Path | Rol | → Baseline |
|-----------|------|-----|------------|
| Overview | `runtime-architecture/01_*.md` | L0–L7 | Gateway |
| Request Lifecycle | `02_*.md` | Pipeline | F1 |
| Context Propagation | `03_*.md` | 6 contextos | RD-09 |
| Runtime Flows | `04_*.md` | 12 flows | Tests F0 |
| Boundaries | `05_*.md` | Layer deps | G-08 |
| Invariants | `06_*.md` | RI-01–62 | Tier 3 normative |
| Sequence Diagrams | `07_*.md` | Diagrams | Reference |
| Runtime Risks | `08_*.md` | RR-* | 5.5 AR-* |
| Runtime Decisions | `09_*.md` | RD detail | `03_RUNTIME_DECISION_STATUS` |
| Executive Summary | `10_*.md` | E4 summary | — |

---

## 8. Etapa 5 — Technical Infrastructure

| Documento | Path | Rol | → Baseline |
|-----------|------|-----|------------|
| Persistence Gateway | `technical-infrastructure/01_*.md` | L6 design | F1 |
| Storage Metadata | `02_*.md` | Cache | F1 |
| Connection Resolution | `03_*.md` | Routing | F1 |
| Engine Management | `04_*.md` | Engines | F1 |
| Session Lifecycle | `05_*.md` | AsyncSession | TD-05 |
| Unit of Work | `06_*.md` | UoW | Protected |
| Transaction Boundaries | `07_*.md` | Saga | F4 blocked |
| Query Execution | `08_*.md` | execute_* | F1 |
| Repository Interaction | `09_*.md` | Legacy | F0 audit |
| Engine Cache Policy | `10_*.md` | L-A/B/C | F1 |
| Failure Recovery | `11_*.md` | Recovery | F6 ops |
| Implementation Roadmap | `12_*.md` | **Partial SUPERSEDED** | `05_IMPLEMENTATION_BASELINE` |
| Technical Decisions | `13_*.md` | TD-01–13 | Linked RD |
| Executive Summary | `14_*.md` | E5 summary | — |

---

## 9. Etapa 5.5 — Validation

| Documento | Input → Baseline resolution |
|-----------|----------------------------|
| 01 Consistency | C-01–C-07 → §4 baseline |
| 02 Traceability | H-01–H-10 → closed/open |
| 03 Risk Assessment | AR-* → gates |
| 04 Readiness | 58% → 65% post-freeze |
| 05 Gateway Review | GW-* → accepted debt |
| 06 RD Validation | RD amendments |
| 07 Scalability | Scope limits §2.2 |
| 08 Operational | C-06 pending F6 |
| 09 Strategy | Roadmap §6 |
| 10 Go/No-Go | GO WITH CONDITIONS |

---

## 10. Decision traceability matrix

| Decisión | E0 | E1 | E2 | E3 | E4 | E5 | E5.5 | BL-1.0 |
|----------|----|----|----|----|----|----|------|--------|
| CP/DP split | R-C02 | ADR-001 | G-08 | Q-001 | RI-35 | op_class | ✅ | ADR-001 Approved |
| Mode invisible L5 | R-I02 | P5 | G-05 | — | RD-03 | TD-08 | C-01 | F3 |
| Gateway unique | — | — | Capa1-2 | — | RD-06 | 01 | GW review | F1 |
| Session central | R-C05 | ADR-002 | — | Q-010 | RD-11 open | TD-13 | AR-C01 | **ADR-002-A Closed** |
| Saga onboarding | R-C01 | ADR-004 | Capa3 | Q-032 | RD-12 | 07 | AR-C03 | F4 blocked |
| Catalog replica | R-I04 | — | — | Q-041 | — | 08 gap | AR-H01 | **ADR-011-A** |
| Migration offline | — | ADR-008 | — | — | RD-13 | F7 | ✅ | ADR-008 |

---

## 11. Implementación futura → documentos fuente

| Implementación Fase | Documentos obligatorios |
|---------------------|-------------------------|
| F0 | `05_IMPLEMENTATION_BASELINE`, `06_RUNTIME_INVARIANTS`, validation 03 |
| F1 | `technical-infrastructure/01–04,08,10`, `03_RUNTIME_DECISION_STATUS`, G-05 |
| F2 | `impact-analysis/04`, `05` |
| F3 | `03_RUNTIME_DECISION_STATUS` RD-03, ADR-005 |
| F4 (post-gate) | ADR-004, `04_OPEN_QUESTIONS` Q-030 spec, ADR-011 |
| F6 (post-gate) | `08_OPERATIONAL_READINESS`, ADR-002-A |

---

## 12. Conclusión

Trazabilidad **completa** E0→BL-1.0. Decisiones huérfanas E5.5 **resueltas** en baseline (session, catalogs, Q-031). **Q-030 spec** única trazabilidad abierta P0 pre-F4.
