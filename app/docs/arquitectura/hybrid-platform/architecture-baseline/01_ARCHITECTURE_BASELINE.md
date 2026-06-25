# 01 — Architecture Baseline (Official)

**Etapa:** 5.6 — Architecture Baseline Freeze  
**Versión:** **BL-1.0**  
**Fecha congelamiento:** 2026-06-25  
**Estado:** **FROZEN — ARCHITECTURE BASELINE**  
**Decisión Etapa 5.5:** GO WITH CONDITIONS  
**Audiencia:** Todo el equipo; referencia obligatoria Etapa 6+

---

## 1. Declaración oficial

A partir de **2026-06-25**, la arquitectura **Hybrid Platform (Shared + Dedicated Database)** queda **congelada** en versión **BL-1.0**.

| Regla | Descripción |
|-------|-------------|
| **BL-R01** | Etapa 6 (Implementación) **solo** puede ejecutarse conforme a esta baseline |
| **BL-R02** | Cualquier cambio arquitectónico posterior requiere **nueva ADR** o **revisión arquitectónica formal** (Etapa 5.7+) |
| **BL-R03** | Documentos marcados SUPERSEDED conservan valor histórico; **no** son normativos |
| **BL-R04** | Contradicciones E0–E5 resueltas en baseline **prevalecen** sobre borradores anteriores |

---

## 2. Alcance definitivo

### 2.1 In scope BL-1.0

| Capacidad | Alcance |
|-----------|---------|
| Modelo conceptual | Platform / IAM / ERP; CP / DP / Transversal |
| Runtime | Pipeline L0–L7; 62 invariantes; 15 RD (+ ampliaciones) |
| Infraestructura | Persistence Gateway; metadata; engines; sessions SQL; UoW |
| Modos instalación | **Shared** (default) + **Dedicated** (per-tenant metadata) |
| Implementación Etapa 6 inicial | **Fases F0–F3 únicamente** (GO WITH CONDITIONS) |
| Onboarding target | Saga multi-fase (implementación F4+, post-gate) |
| Migración MVP | Offline; bloqueo ERP (RD-13); solo post-F6 |

### 2.2 Out of scope BL-1.0

| Capacidad | Estado |
|-----------|--------|
| Online migration dual-write | Post-MVP |
| Multi-Region activo | Extensión futura |
| Read replicas | Post-MVP |
| PostgreSQL / MySQL / Oracle | No soportado BL-1.0 |
| On-Premise operativo | Metadata-ready; ops post-MVP |
| 500+ dedicated tenants / worker | Fuera capacidad MVP |
| Request-scoped SQL session | Rechazado (TD-05) |
| Tenant export/import/archive | Sin diseño BL-1.0 |

---

## 3. Principios arquitectónicos congelados (invariantes de baseline)

| ID | Principio |
|----|-----------|
| BL-P01 | **Infrastructure Encapsulation First** — Shared/Dedicated solo en L6 |
| BL-P02 | **Single Codebase** — sin fork `*_dedicated` / `*_shared` |
| BL-P03 | **Frontend Transparency** — sin cambio contratos OpenAPI/JWT |
| BL-P04 | **ERP Protected** — 0 cambios queries ERP en MVP |
| BL-P05 | **Backward Compatibility Shared** — tenants existentes sin regresión |
| BL-P06 | **CP centralizado / DP por tenant** — ADR-001-A |
| BL-P07 | **Fail-closed dedicated** — RI-39; sin fallback silencioso |
| BL-P08 | **Saga cross-plane** — prohibido single-TX CP+DP (ADR-004-A) |

---

## 4. Resolución de contradicciones (Etapa 5.5 → Baseline)

| ID | Contradicción | Resolución BL-1.0 |
|----|---------------|-------------------|
| C-01 | `database_type` L5 vs RI-32 | **Target:** L5 no consume mode. **Deuda AS-IS:** F3 obligatoria pre-F4 |
| C-02 | RD-11 session store | **Cerrada:** ADR-002-A — sesiones IAM en CP (MVP) |
| C-03 | Catálogos CP vs GLOBAL_TABLES | **Cerrada:** ADR-011-A — réplica local en provisioning dedicated |
| C-04 | auth_audit_log routing | **Cerrada:** operation_class `tenant_data`; ruta vía gateway según tenant mode |
| C-05 | Q-031 metadata timing | **Cerrada:** metadata en saga Step 1b (ver 04_OPEN_QUESTIONS_STATUS) |
| C-06 | Repository auditor bypass | **Deuda:** audit pre-F1 merge (R-02 validation) |
| C-07 | Gate P0 E1 vs E4/E5 | **Resuelto:** P0 ownership cerrados; P0 implementación saga/catálogo cerrados en baseline; spec detalle Q-030 = gate F4 |

---

## 5. Documentos vigentes (normativos BL-1.0)

### 5.1 Baseline (autoridad máxima post-freeze)

| Documento | Rol |
|-----------|-----|
| `architecture-baseline/01_ARCHITECTURE_BASELINE.md` | **Este documento** — constitución |
| `architecture-baseline/02_ADR_STATUS.md` | ADRs oficiales |
| `architecture-baseline/03_RUNTIME_DECISION_STATUS.md` | RD oficiales |
| `architecture-baseline/04_OPEN_QUESTIONS_STATUS.md` | Preguntas abiertas/cerradas |
| `architecture-baseline/05_IMPLEMENTATION_BASELINE.md` | Alcance Etapa 6 |
| `architecture-baseline/06_DOCUMENT_TRACEABILITY.md` | Trazabilidad completa |
| `architecture-baseline/07_CHANGELOG_BASELINE_FREEZE.md` | Historial cambios freeze |

### 5.2 Etapas congeladas (referencia normativa)

| Etapa | Carpeta | Estado |
|-------|---------|--------|
| E0 AS-IS | `app/docs/arquitectura/0*.md` | Referencia histórica AS-IS |
| E1 Conceptual | `hybrid-platform/01–05` | Vigente (ver SUPERSEDED §6) |
| E2 Impact | `hybrid-platform/impact-analysis/` | Vigente |
| E3 Canonical | `hybrid-platform/canonical-data-model/` | Vigente |
| E4 Runtime | `hybrid-platform/runtime-architecture/` | Vigente (RD actualizadas en 03) |
| E5 Technical | `hybrid-platform/technical-infrastructure/` | Vigente (roadmap actualizado) |
| E5.5 Validation | `hybrid-platform/architecture-validation/` | Vigente — input del freeze |

### 5.3 Jerarquía normativa (mayor → menor)

```
1. architecture-baseline/ (BL-1.0)
2. Guardrails E2 (G-01–G-20)
3. Runtime Invariants E4 (RI-01–RI-62)
4. Etapas E1–E5 detalle
5. AS-IS E0 (solo donde baseline no contradice target)
```

---

## 6. Documentos SUPERSEDED

| Documento | Reemplazado por | Nota |
|-----------|-----------------|------|
| `hybrid-platform/04_ARCHITECTURE_DECISIONS_DRAFT.md` | `architecture-baseline/02_ADR_STATUS.md` | Borrador E1 |
| `hybrid-platform/05_OPEN_QUESTIONS.md` | `architecture-baseline/04_OPEN_QUESTIONS_STATUS.md` | Lista E1 |
| `runtime-architecture/09_RUNTIME_DECISIONS.md` §2 tabla | `architecture-baseline/03_RUNTIME_DECISION_STATUS.md` | RD-11 actualizada |
| `technical-infrastructure/12_IMPLEMENTATION_ROADMAP.md` §3–4 | `architecture-baseline/05_IMPLEMENTATION_BASELINE.md` §6 | Fases reordenadas |

**No eliminados** — conservar con banner SUPERSEDED.

---

## 7. Roadmap oficial congelado (resumen)

Ver detalle completo: `05_IMPLEMENTATION_BASELINE.md` §6.

```
F0  Test harness (ampliado adversarial)
F1  Gateway consolidation          ∥ F5a ADR-002 implementación route (si aplica)
F2  Shared regression
F3  L5 database_type cleanup        ← ANTES de F4
F3.5 Catalog policy validation     ← gate F4 (ADR-011 verificado en provisioning design)
[GATE REVIEW]
F4  Provisioning saga              ← requiere Q-030 spec 1-pager
F5b Session route hardening        ← ADR-002-A ya decidida BL-1.0
F6  Dedicated production           ← requiere ops runbooks C-06
F7  Migration offline
F8  Optimizations
```

---

## 8. Decisiones cerradas en freeze (resumen)

| Área | Decisión |
|------|----------|
| CP/DP | ADR-001 **Approved** |
| Session IAM MVP | ADR-002-A — Control Plane central |
| RBAC | ADR-003-A — catálogo CP; grants DP |
| Onboarding | ADR-004-A+C — saga + estados async |
| Mode encapsulation | ADR-005-A |
| Data model | ADR-006-A — modelo lógico unificado + filter defensivo |
| Catalogs dedicated | ADR-011-A — réplica local provisioning |
| RD-01 a RD-10, RD-12–RD-15 | Approved |
| RD-11 | **Closed** → ADR-002-A |

Ver `02_ADR_STATUS.md` y `03_RUNTIME_DECISION_STATUS.md`.

---

## 9. Decisiones pendientes post-freeze (no bloquean F0–F3)

| ID | Tema | Gate |
|----|------|------|
| BL-PEND-01 | Q-030 saga spec detallada (pasos, compensación) | Pre-F4 |
| BL-PEND-02 | Ops runbooks (C-06) | Pre-F6 |
| BL-PEND-03 | `{cod}_deps` rollout ERP modules | Pre-enterprise impersonation |
| BL-PEND-04 | ADR-002 fase 2 reevaluación (sessions tenant DP) | Post-MVP |
| BL-PEND-05 | Engine key consolidation TD-03 | F8 |
| BL-PEND-06 | Redis distributed invalidation TD-09 | F8 |

---

## 10. Métricas baseline

| Métrica | Valor BL-1.0 |
|---------|--------------|
| Preparación implementación global | 65% (↑ post-freeze cierres) |
| Confianza F0–F3 | 75% |
| Confianza dedicated prod | 45% (↑ RD-11, catálogos) |
| ADRs Approved | 11 |
| RD Closed | 15/15 |
| Open Questions P0 abiertas | 1 (Q-030 spec detalle) |

---

## 11. Declaración formal

```
╔══════════════════════════════════════════════════════════════╗
║  ARCHITECTURE BASELINE FROZEN                                ║
║  Version: BL-1.0                                             ║
║  Date: 2026-06-25                                            ║
║  Hybrid Platform — Shared + Dedicated Database               ║
║  Etapa 6 authorized: F0–F3 only (GO WITH CONDITIONS)         ║
╚══════════════════════════════════════════════════════════════╝
```

Cualquier modificación a BL-P01–BL-P08, ADRs Approved, o RD Closed requiere **ADR nueva** numerada ADR-012+ o revisión arquitectónica **Etapa 5.7**.

---

## 12. Referencias

| Documento | Path |
|-----------|------|
| Go/No-Go | `architecture-validation/10_GO_NO_GO_REPORT.md` |
| Guardrails | `impact-analysis/05_IMPLEMENTATION_GUARDRAILS.md` |
| Invariantes | `runtime-architecture/06_RUNTIME_INVARIANTS.md` |
