# 02 — ADR Status (Official)

**Etapa:** 5.6 — Architecture Baseline Freeze  
**Versión baseline:** BL-1.0  
**Fecha:** 2026-06-25  
**Estado:** **Normativo — reemplaza borrador E1**

**SUPERSEDES:** `hybrid-platform/04_ARCHITECTURE_DECISIONS_DRAFT.md`

---

## 1. Leyenda de estados

| Estado | Significado |
|--------|-------------|
| **Approved** | Decisión formal BL-1.0; obligatoria Etapa 6+ |
| **Approved (MVP)** | Válida para MVP; reevaluación explícita post-MVP |
| **Deferred** | Pospuesta; no bloquea F0–F3 |
| **Superseded** | Reemplazada por ADR posterior |
| **Draft** | No normativo — solo histórico |

---

## 2. ADRs oficiales BL-1.0

### ADR-001 — Separación Control Plane / Data Plane

| Campo | Valor |
|-------|-------|
| **Estado** | **Approved** |
| **Decisión** | **Alternativa A** — CP centralizado; DP en almacén tenant (shared o dedicated) |
| **Fecha aprobación** | 2026-06-25 (BL-1.0) |
| **Evidencia** | E3 ownership Q-001, Q-002; E5 operation_class |
| **Consecuencia** | Platform metadata siempre CP; ERP siempre tenant_data path |

---

### ADR-002 — Ubicación de sesiones IAM

| Campo | Valor |
|-------|-------|
| **Estado** | **Approved (MVP)** |
| **Decisión** | **Alternativa A** — Sesiones IAM persisten en **Control Plane Store** para todos los modos (MVP) |
| **Fecha aprobación** | 2026-06-25 (BL-1.0) |
| **Cierra** | RD-11, Q-010 (persistencia MVP) |
| **Redis** | Acelerador; SQL CP es authoritative MVP |
| **Reevaluación** | BL-PEND-04 — Alternativa B post-MVP si compliance/latencia |
| **Consecuencia** | IAM session ops usan operation_class según tabla RD-07 ampliada; persistencia sesión = control_plane route |

---

### ADR-003 — Catálogo de permisos RBAC

| Campo | Valor |
|-------|-------|
| **Estado** | **Approved** |
| **Decisión** | **Alternativa A** — Catálogo permisos CP; roles y grants DP tenant |
| **Fecha aprobación** | 2026-06-25 (BL-1.0) |
| **Evidencia** | E3 Q-020; RD-15 |
| **Consecuencia** | Permission resolution service L4; no join cross-plane en ERP |

---

### ADR-004 — Onboarding saga

| Campo | Valor |
|-------|-------|
| **Estado** | **Approved** |
| **Decisión** | **Alternativa A + C** — Saga orquestada + estados Provisioning async |
| **Fecha aprobación** | 2026-06-25 (BL-1.0) |
| **Alinea** | RD-12 |
| **Pendiente implementación** | Q-030 spec detallada (BL-PEND-01) — gate F4 |
| **Consecuencia** | Prohibido single-TX CP+DP; response POST /clientes/ unchanged |

---

### ADR-005 — Encapsulación Installation Mode

| Campo | Valor |
|-------|-------|
| **Estado** | **Approved** |
| **Decisión** | **Alternativa A** — Mode solo L6 Persistence Gateway |
| **Fecha aprobación** | 2026-06-25 (BL-1.0) |
| **Alinea** | RD-03, G-05, G-10 |
| **Deuda AS-IS** | F3 elimina branches L5 |
| **Whitelist infra** | `connection_async`, `routing`, `queries_async`, `query_helpers`, provisioning orchestrator |

---

### ADR-006 — Aislamiento datos Shared vs Dedicated

| Campo | Valor |
|-------|-------|
| **Estado** | **Approved** |
| **Decisión** | **Alternativa A** — Modelo lógico unificado; columna tenant identifier presente en ambos modos |
| **Fecha aprobación** | 2026-06-25 (BL-1.0) |
| **Refuerzo** | TD-08 tenant filter defensivo en dedicated |
| **Consecuencia** | Migración shared↔dedicated simplificada; queries ERP unchanged |

---

### ADR-007 — Provisioning almacén Dedicated

| Campo | Valor |
|-------|-------|
| **Estado** | **Approved (MVP)** |
| **Decisión** | **Alternativa B** — Provisioning **asíncrono**; tenant estado Provisioning |
| **Deferred** | Alternativa C pool pre-creado → post-MVP |
| **Fecha aprobación** | 2026-06-25 (BL-1.0) |
| **Alinea** | Q-033 orientación async |
| **Consecuencia** | UX polling/webhook; no timeout sync en DDL |

---

### ADR-008 — Migración Shared → Dedicated

| Campo | Valor |
|-------|-------|
| **Estado** | **Approved (phased)** |
| **Decisión** | **Fase 1:** solo nuevos tenants dedicated (C). **Fase 2:** migración offline (B). **Fase 3:** evaluar online (A) |
| **Fecha aprobación** | 2026-06-25 (BL-1.0) |
| **Alinea** | RD-13 |
| **Implementación** | F7 post-F6 |

---

### ADR-009 — Impersonación bajo Dedicated

| Campo | Valor |
|-------|-------|
| **Estado** | **Approved** |
| **Decisión** | **Alternativa A** — Impersonation resuelve almacén tenant target vía gateway |
| **Fecha aprobación** | 2026-06-25 (BL-1.0) |
| **Alinea** | RD-05 |
| **Requisito** | Auditoría reforzada; gate superadmin |

---

### ADR-010 — Extensibilidad On-Premise / modos futuros

| Campo | Valor |
|-------|-------|
| **Estado** | **Approved** |
| **Decisión** | **Alternativa A** — Installation Mode enum extensible en CP metadata |
| **Fecha aprobación** | 2026-06-25 (BL-1.0) |
| **Consecuencia** | on_premise = metadata endpoint; sin cambio L5 |

---

### ADR-011 — Catálogos Product Reference en Dedicated (NUEVA BL-1.0)

| Campo | Valor |
|-------|-------|
| **Estado** | **Approved** |
| **Problema** | AR-H01 / C-03 — catálogos CP (`cat_pais`, etc.) en GLOBAL_TABLES; dedicated sin réplica falla ERP |
| **Alternativas** | A) Réplica local en provisioning; B) Read-through CP en gateway |
| **Decisión** | **Alternativa A** — Réplica catálogos Product Reference en tenant store durante provisioning dedicated |
| **Fecha aprobación** | 2026-06-25 (BL-1.0) |
| **Alternativa rechazada MVP** | B read-through — complejidad gateway; diferir post-MVP evaluación |
| **Consecuencia** | F3.5 valida lista catálogos; seed en saga step dedicated; sync al actualizar producto = post-MVP |
| **Cierra** | C-03, AR-H01 |

---

## 3. Tabla resumen ADR

| ADR | Tema | Estado | Alternativa |
|-----|------|--------|-------------|
| 001 | CP/DP split | Approved | A |
| 002 | Session IAM | Approved (MVP) | A |
| 003 | RBAC catalog | Approved | A |
| 004 | Onboarding saga | Approved | A+C |
| 005 | Mode encapsulation | Approved | A |
| 006 | Data isolation model | Approved | A |
| 007 | Dedicated provisioning | Approved (MVP) | B |
| 008 | Migration | Approved (phased) | C→B→eval A |
| 009 | Impersonation | Approved | A |
| 010 | Extensibility | Approved | A |
| 011 | Catalogs dedicated | Approved | A (replica) |

---

## 4. ADRs Draft / Superseded

| Documento | Estado |
|-----------|--------|
| `04_ARCHITECTURE_DECISIONS_DRAFT.md` | **Superseded** → este documento |

---

## 5. Proceso de cambio post-BL-1.0

1. Proponer ADR-012+ con contexto, alternativas, impacto en RI/G guardrails  
2. Revisión Arquitecto Principal  
3. Actualizar este documento + `07_CHANGELOG_BASELINE_FREEZE.md`  
4. Si cambio material: incrementar baseline BL-1.1+

---

## 6. Conclusión

**11 ADRs Approved** (10 heredados E1 + ADR-011 nueva). Ningún ADR en Draft para implementación F0–F3.
