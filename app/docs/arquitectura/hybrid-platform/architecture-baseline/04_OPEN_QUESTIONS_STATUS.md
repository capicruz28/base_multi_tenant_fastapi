# 04 — Open Questions Status (Official)

**Etapa:** 5.6 — Architecture Baseline Freeze  
**Versión baseline:** BL-1.0  
**Fecha:** 2026-06-25  
**Estado:** **Normativo**

**SUPERSEDES:** `hybrid-platform/05_OPEN_QUESTIONS.md`

---

## 1. Leyenda

| Estado | Significado |
|--------|-------------|
| **Closed** | Resuelta BL-1.0 |
| **Closed (MVP)** | Resuelta para MVP; extensión post-MVP |
| **Open** | Pendiente — puede bloquear fase indicada |
| **Deferred** | P2/P3 — no bloquea F0–F3 |
| **Eliminated** | Fuera alcance BL-1.0 explícito |

---

## 2. P0 — Estado oficial

| ID | Pregunta | Estado E3/E1 | Estado BL-1.0 | Resolución |
|----|----------|--------------|---------------|------------|
| Q-001 | Control plane data | ✅ E3 | **Closed** | E3 §CP |
| Q-002 | Data plane data | ✅ E3 | **Closed** | E3 §DP |
| Q-010 | Session persist dedicated | 🟡 | **Closed (MVP)** | ADR-002-A central CP |
| Q-020 | Roles/grants location | ✅ E3 | **Closed** | ADR-003-A DP |
| Q-030 | Saga contract | P0 abierta | **Open** | Gate F4 — spec 1-pager requerida |
| Q-031 | Metadata installation timing | P0 abierta | **Closed** | Saga Step 1b post-registry |

---

## 3. Q-031 — Resolución BL-1.0 (cerrada)

**Contrato metadata installation (congela C-05):**

| Step | Acción | Almacén |
|------|--------|---------|
| 1a | Crear Tenant Registry entry | CP |
| 1b | Crear Installation Mode + Storage Metadata (shared default o dedicated endpoint) | CP |
| 2+ | Seed DP / DDL dedicated | DP resuelto |

**Reglas:**
- Metadata **debe existir** antes de primera operación tenant_data dedicated
- Onboarding shared: mode=shared; metadata mínima (implícita settings globales)
- Onboarding dedicated: mode=dedicated + Storage Endpoint row obligatoria antes Step 3

---

## 4. Q-030 — Open (gate F4)

Permanece **Open** para detalle implementación. **Behavioral** cerrado por ADR-004 + RD-12.

**Mínimo requerido pre-F4 (BL-PEND-01):**
- Lista pasos saga numerados
- Idempotency key por paso
- Estados Provisioning → Activo | Error
- Compensación semi-automática (TD-12)
- POST /clientes/ response invariant

**No bloquea F0–F3.**

---

## 5. P1 — Estado consolidado

| ID | Tema | BL-1.0 |
|----|------|--------|
| Q-003 | Catálogo módulos solo Platform | **Closed** — CP; réplica no requerida excepto ADR-011 cat_* |
| Q-004 | Auth config tenant | **Closed** — DP (E3) |
| Q-011 | Redis SoT | **Open** — SQL authoritative MVP; Redis acelerador |
| Q-012 | Impersonation dedicated unreachable | **Deferred** — ADR-009-A; ops Q-012 |
| Q-021 | Permission resolution | **Closed (behavioral)** — RD-15 |
| Q-032 | Company seed | **Closed** — E3 |
| Q-033 | Provisioning async | **Closed** — ADR-007-B |
| Q-040 | tenant id in dedicated data | **Closed** — ADR-006-A |
| Q-041 | Catálogos geo | **Closed** — ADR-011-A réplica |
| Q-050 | Migration allowed | **Closed (phased)** — ADR-008 |
| Q-060 | Monitor N dedicated | **Open** — gate F6 |
| Q-061 | DDL dedicated executor | **Open** — gate F4 |
| Q-063 | Cache invalidation | **Closed** — E5 TD-02, events §10 |
| Q-080 | Shared default forever | **Closed (MVP)** — sí default |
| Q-081 | Existing tenants unchanged | **Closed** — G-02 |

---

## 6. P2/P3 — Deferred / Eliminated

| ID | Estado BL-1.0 |
|----|---------------|
| Q-013 Session V1 removal | Deferred |
| Q-022 Custom permissions | Deferred |
| Q-034 Pre-provisioned pool | Deferred post-MVP |
| Q-051 Dedicated→Shared | Deferred |
| Q-052 Retention Retirado | Open ops — gate F7 |
| Q-053 Schema version drift | Deferred |
| Q-062 Backup responsibility | Deferred |
| Q-070–Q-072 Commercial | Deferred product |
| Q-082 database_type cleanup count | **Closed** — F3 scope |

---

## 7. Preguntas eliminadas del alcance BL-1.0

| Tema | Razón |
|------|-------|
| Multi-DB PostgreSQL/MySQL | Eliminated BL-1.0 — SQL Server only |
| Request-scoped SQL session | Eliminated — TD-05 rejected |
| Fork codebase dedicated | Eliminated — G-04 |

---

## 8. Resumen conteo

| Estado | P0 | P1 | Total aprox |
|--------|----|----|-------------|
| Closed | 5 | 12 | ~17 |
| Open | 1 | 3 | 4 |
| Deferred | 0 | 8+ | ~10 |

---

## 9. Bloqueantes por fase (post-freeze)

| Fase | Open Questions que bloquean |
|------|----------------------------|
| F0–F3 | **Ninguna P0** |
| F4 | Q-030 (spec), Q-061 |
| F6 | Q-060, Q-011 (operational hardening) |
| F7 | Q-052 |

---

## 10. Conclusión

**P0 ownership y routing:** cerradas. **Única P0 Open:** Q-030 detalle saga (gate F4, no F0). Documento `05_OPEN_QUESTIONS.md` queda **SUPERSEDED**.
