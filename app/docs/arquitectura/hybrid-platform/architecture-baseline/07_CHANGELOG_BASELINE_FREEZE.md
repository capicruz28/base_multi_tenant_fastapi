# 07 — Changelog Baseline Freeze

**Etapa:** 5.6 — Architecture Baseline Freeze  
**Versión:** BL-1.0  
**Fecha:** 2026-06-25

---

## 1. Propósito

Registro completo de cambios respecto a documentación pre-freeze (E0–E5.5).

---

## 2. Documentos creados (nuevos)

| # | Archivo | Descripción |
|---|---------|-------------|
| 1 | `architecture-baseline/01_ARCHITECTURE_BASELINE.md` | Constitución BL-1.0 |
| 2 | `architecture-baseline/02_ADR_STATUS.md` | ADRs oficiales Approved |
| 3 | `architecture-baseline/03_RUNTIME_DECISION_STATUS.md` | RD 15/15 Closed |
| 4 | `architecture-baseline/04_OPEN_QUESTIONS_STATUS.md` | Preguntas consolidadas |
| 5 | `architecture-baseline/05_IMPLEMENTATION_BASELINE.md` | Alcance Etapa 6 |
| 6 | `architecture-baseline/06_DOCUMENT_TRACEABILITY.md` | Trazabilidad E0→BL |
| 7 | `architecture-baseline/07_CHANGELOG_BASELINE_FREEZE.md` | Este documento |

---

## 3. Documentos actualizados

### 3.1 `hybrid-platform/04_ARCHITECTURE_DECISIONS_DRAFT.md`

| Campo | Valor |
|-------|-------|
| **Sección** | Banner SUPERSEDED (cabecera) |
| **Por qué** | ADRs pasan de Draft a Approved en `02_ADR_STATUS.md` |
| **Qué cambió** | Estado documento → SUPERSEDED; pointer BL-1.0 |

### 3.2 `hybrid-platform/05_OPEN_QUESTIONS.md`

| Campo | Valor |
|-------|-------|
| **Sección** | Banner SUPERSEDED (cabecera) |
| **Por qué** | Consolidación post-validación 5.5 |
| **Qué cambió** | Reemplazado por `04_OPEN_QUESTIONS_STATUS.md` |

### 3.3 `runtime-architecture/09_RUNTIME_DECISIONS.md`

| Campo | Valor |
|-------|-------|
| **Sección** | RD-11; §2 tabla resumen; banner baseline |
| **Por qué** | RD-11 cerrada ADR-002-A; eliminar contradicción C-02 |
| **Qué cambió** | RD-11: Diferida → Closed (MVP) central CP; tabla 15/15 Closed |

### 3.4 `technical-infrastructure/12_IMPLEMENTATION_ROADMAP.md`

| Campo | Valor |
|-------|-------|
| **Sección** | §3 fases; §4 dependencias; §5 bloqueantes; banner |
| **Por qué** | Reordenación validation 5.5 doc 09; RD-11 cerrada |
| **Qué cambió** | F3 antes F4; F3.5 añadida; F5→F5b; partial SUPERSEDED |

---

## 4. Documentos reemplazados (contenido)

| Documento anterior | Reemplazado por | Tipo |
|--------------------|-----------------|------|
| ADR Draft E1 | `02_ADR_STATUS.md` | Contenido normativo |
| Open Questions E1 | `04_OPEN_QUESTIONS_STATUS.md` | Contenido normativo |
| RD summary E4 §2 | `03_RUNTIME_DECISION_STATUS.md` | Estado oficial |
| Roadmap E5 §3–4 | `05_IMPLEMENTATION_BASELINE.md` §6 | Fases autorizadas |

---

## 5. Documentos SUPERSEDED (no eliminados)

| Documento | Nuevo oficial |
|-----------|---------------|
| `04_ARCHITECTURE_DECISIONS_DRAFT.md` | `02_ADR_STATUS.md` |
| `05_OPEN_QUESTIONS.md` | `04_OPEN_QUESTIONS_STATUS.md` |
| `12_IMPLEMENTATION_ROADMAP.md` (fases) | `05_IMPLEMENTATION_BASELINE.md` |

---

## 6. Decisiones cerradas en freeze

| ID | Antes | Después BL-1.0 |
|----|-------|----------------|
| ADR-001 | Draft | **Approved** A |
| ADR-002 | Draft | **Approved (MVP)** A |
| ADR-003 | Draft | **Approved** A |
| ADR-004 | Draft | **Approved** A+C |
| ADR-005 | Draft | **Approved** A |
| ADR-006 | Draft | **Approved** A |
| ADR-007 | Draft | **Approved (MVP)** B |
| ADR-008 | Draft | **Approved (phased)** |
| ADR-009 | Draft | **Approved** A |
| ADR-010 | Draft | **Approved** A |
| ADR-011 | — | **Approved** A (nueva) |
| RD-11 | Abierta | **Closed** → ADR-002-A |
| Q-010 | Parcial | **Closed (MVP)** |
| Q-031 | Abierta | **Closed** saga Step 1b |
| Q-041 | Abierta | **Closed** ADR-011 |
| C-03 | Abierta | **Closed** ADR-011 |

---

## 7. Decisiones pendientes (sin cambio status)

| ID | Estado | Gate |
|----|--------|------|
| Q-030 saga spec detalle | Open | F4 |
| Q-011 Redis SoT | Open | F6 hardening |
| Q-060 dedicated monitoring | Open | F6 |
| Q-061 DDL executor | Open | F4 |
| C-06 ops runbooks | Pending | F6 |
| BL-PEND-04 ADR-002 reeval | Deferred | Post-MVP |

---

## 8. Contradicciones resueltas

| ID | Resolución |
|----|------------|
| C-01 | Target RD-03; F3 deuda AS-IS |
| C-02 | ADR-002-A |
| C-03 | ADR-011-A |
| C-04 | RD-07 matrix auth_audit_log |
| C-05 | Q-031 Step 1b |
| C-06 | R-02 audit repos — pendiente F0 |
| C-07 | P0 gate reclasificado en 04_OPEN_QUESTIONS_STATUS |

---

## 9. Métricas pre/post freeze

| Métrica | Pre-freeze (5.5) | Post-freeze (BL-1.0) |
|---------|------------------|----------------------|
| ADRs Approved | 0 | 11 |
| RD Closed | 14/15 | 15/15 |
| P0 Open | 3 | 1 (Q-030 spec) |
| Prep. implementación | 58% | 65% |
| Confianza dedicated prod | 35% | 45% |

---

## 10. Historial versiones baseline

| Versión | Fecha | Descripción |
|---------|-------|-------------|
| BL-1.0 | 2026-06-25 | Freeze inicial post E5.5 GO WITH CONDITIONS |

---

## 11. Próxima versión baseline

**BL-1.1** requerida si:
- Q-030 spec altera pasos saga materialmente
- Gate Review autoriza F4 con cambios arquitectónicos
- ADR-012+ aprobada

---

## 12. Autorización

| Rol | Acción | Fecha |
|-----|--------|-------|
| Etapa 5.6 Baseline Freeze | ARCHITECTURE BASELINE FROZEN BL-1.0 | 2026-06-25 |
