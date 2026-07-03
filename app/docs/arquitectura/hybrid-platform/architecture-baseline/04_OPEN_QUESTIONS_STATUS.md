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
| Q-030 | Saga contract | P0 abierta | **Closed** | Spec pública: `docs/contracts/DEDICATED_PROVISIONING_API_CONTRACT.md` + IP-2.0.1 §8 saga S1–S10; ver §4 |
| Q-031 | Metadata installation timing | P0 abierta | **Closed** | Saga F4: `cliente_conexion` en S8 post seed S7; ver §3 |

---

## 3. Q-031 — Resolución BL-1.0 (cerrada; alineada saga F4 S1–S10)

**Contrato metadata installation (congela C-05):**

| Paso saga F4 | Acción | Almacén | Notas |
|--------------|--------|---------|-------|
| S1 | Registry tenant | CP | Tras `POST /clientes/` dedicated |
| S2–S7 | Allocate, DDL, bootstrap, catálogos, seed tenant | DP | Seed S7 usa conexión DP directa de provisioning (no requiere `cliente_conexion` en CP) |
| **S8** | Registrar `cliente_conexion` (metadata routing) | CP | **Automático** — no `POST /conexiones/` en happy path |
| S9–S10 | Invalidación cache, smoke, `provisioning_state=ready` | CP | Tráfico ERP vía Gateway solo post-Ready |

**Reglas (sin contradicción con Q-030 / contrato provisioning):**

- Metadata (`cliente_conexion` principal activa) **debe existir** antes de la primera operación **tenant_data vía Hybrid Gateway** en runtime (post S10 Ready).
- **No** exige metadata CP antes del seed interno S7: el provisioning accede al Data Plane con credenciales de plataforma durante la saga.
- Onboarding **shared:** mode=shared; metadata mínima (implícita settings globales); conexión opcional vía `POST /conexiones/`.
- Onboarding **dedicated F4+:** metadata se crea en **S8**, después de S7 — conforme `DEDICATED_PROVISIONING_API_CONTRACT.md` RN-03.

**Referencia cruzada:** IP-2.0.1 PA-16, BLF4-R05; ADR-F4-02 (pendiente versionado repo — ver §11).

---

## 4. Q-030 — Closed (spec pública F4)

**Estado:** **Closed** — spec de saga disponible para implementación F4.

**Fuentes normativas vigentes (en repo):**

| Documento | Ruta | Contenido |
|-----------|------|-----------|
| Contrato API provisioning | `docs/contracts/DEDICATED_PROVISIONING_API_CONTRACT.md` | Flujo producto, estados, endpoints, saga S1–S10 expuesta al FE |
| Plan implementación | `app/docs/arquitectura/hybrid-platform/implementation-planning/IP-2.0_F4_IMPLEMENTATION_PLAN.md` | WPs, 12 PRs, DoD, gates |
| Contrato conexión manual | `docs/contracts/CONNECTION_CREATION_API_CONTRACT.md` | Legacy/manual Dedicated; Shared opcional |

**Saga F4 (resumen alineado Q-031):** S1 registry CP → S2 allocate → S3 CREATE DATABASE → S4–S5 bootstrap → S6 catálogos → S7 seed DP → **S8 `cliente_conexion` automático CP** → S9 cache/smoke → S10 Ready.

**Criterios Q-030 satisfechos:**

| Requisito BL-PEND-01 | Resolución |
|----------------------|------------|
| Lista pasos saga numerados | S1–S10 en contrato provisioning §3 y IP-2.0.1 §8 |
| Idempotency key por paso | Contrato provisioning §6; IP-2.0.1 PA-09 |
| Estados Provisioning → Ready \| Failed | Contrato provisioning §7–8 |
| Compensación semi-automática | IP-2.0.1 F4-10; ADR-F4-04 (pendiente versionado) |
| POST /clientes/ response invariant | Contrato provisioning §4–5; IP-2.0.1 BLF4-R02 |

**No bloquea F0–F3.** **No bloquea PR-F4-01** — spec pública cerrada.

**Comportamiento behavioral** previamente cerrado por ADR-004 + RD-12 (BL-1.0).

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
| Closed | 6 | 12 | ~18 |
| Open | 0 | 3 | 3 |
| Deferred | 0 | 8+ | ~10 |

---

## 9. Bloqueantes por fase (post-freeze)

| Fase | Open Questions que bloquean |
|------|----------------------------|
| F0–F3 | **Ninguna P0** |
| F4 | Q-061 |
| F6 | Q-060, Q-011 (operational hardening) |
| F7 | Q-052 |

---

## 10. Conclusión

**P0 ownership y routing:** cerradas. **Q-030** cerrada — spec saga en contrato provisioning + IP-2.0.1. **Q-031** alineada saga S8 post S7. Documento `05_OPEN_QUESTIONS.md` queda **SUPERSEDED**.

---

## 11. Artefactos arquitectura F4 — referencias (sin crear nuevas arquitecturas)

Artefactos citados en IP-2.0.1 y contratos F4 **pendientes de versionado físico en repo**. La implementación F4 debe seguir los documentos versionados listados en §4 Q-030 hasta que existan.

| ID | Artefacto | Estado repo | Referencia vigente mientras tanto |
|----|-----------|-------------|-----------------------------------|
| BL-F4-1.0 | Baseline arquitectónico F4 (saga, CP/DP, compensación) | **Pendiente** — no existe archivo `BL-F4-*.md` | IP-2.0.1; `HYBRID_F4_HANDOFF.md`; contrato provisioning |
| AR-F01 | Decisión flujo canónico Dedicated (`POST /clientes/` → S1–S10) | **Pendiente** — no existe acta archivada | Incorporada en `DEDICATED_PROVISIONING_API_CONTRACT.md` §3, §23 |
| ADR-F4-01 | Credenciales DDL platform segregadas | **Pendiente** | IP-2.0.1 PA-14, F4-04 |
| ADR-F4-02 | Seed tenant en Data Plane | **Pendiente** | IP-2.0.1 F4-07; Q-031 §3 |
| ADR-F4-03 | OpenAPI stability POST /clientes/ | **Pendiente** | IP-2.0.1 PA-07; contrato provisioning §19 |
| ADR-F4-04 | Compensación semi-automática | **Pendiente** | IP-2.0.1 F4-10 |
| ADR-F4-05 | Job dispatcher async in-process | **Pendiente** | IP-2.0.1 F4-03 |
| ADR-F4-06 | Flujo canónico vs legacy conexión manual | **Pendiente** | `CONNECTION_CREATION_API_CONTRACT.md` banner; contrato provisioning §1 |

**Acción futura (fuera alcance P0):** versionar BL-F4-1.0, AR-F01 y ADR-F4-01…06 en `architecture-baseline/` sin alterar decisiones ya incorporadas en contratos e IP-2.0.1.
