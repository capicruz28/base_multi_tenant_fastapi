# 03 — Runtime Decision Status (Official)

**Etapa:** 5.6 — Architecture Baseline Freeze  
**Versión baseline:** BL-1.0  
**Fecha:** 2026-06-25  
**Estado:** **Normativo**

**SUPERSEDES:** Tabla resumen en `runtime-architecture/09_RUNTIME_DECISIONS.md` §2  
**Detalle histórico:** `runtime-architecture/09_RUNTIME_DECISIONS.md` (texto RD-01–15 permanece referencia)

---

## 1. Leyenda

| Estado | Significado |
|--------|-------------|
| **Closed** | Decisión final BL-1.0 |
| **Closed (MVP)** | Válida MVP; reevaluación documentada |
| **Amended** | Modificada respecto borrador E4 |
| **Superseded** | Reemplazada |

---

## 2. Estado oficial RD-01 a RD-15

| ID | Tema | Estado E4 | Estado BL-1.0 | Cambio freeze |
|----|------|-----------|---------------|---------------|
| RD-01 | Resolution per operation | Closed | **Closed** | Sin cambio |
| RD-02 | Tenant before auth | Closed | **Closed** | Sin cambio |
| RD-03 | Mode invisible L5 | Closed | **Closed** | Sin cambio |
| RD-04 | Refresh tenant from token | Closed | **Closed** | Sin cambio |
| RD-05 | Impersonation JWT tenant | Closed | **Closed** | Sin cambio |
| RD-06 | Single L6 gateway | Closed | **Closed** | Ampliación: repository audit pre-F1 |
| RD-07 | Operation class | Closed | **Closed (Amended)** | Matriz entidad→class §3 |
| RD-08 | Shared fallback | Closed | **Closed (Amended)** | Alert obligatorio en fallback |
| RD-09 | Request-scoped context | Closed | **Closed** | Sin cambio |
| RD-10 | ERP session gate | Closed | **Closed** | Sin cambio |
| RD-11 | Session store | **Abierta** | **Closed (MVP)** | → ADR-002-A central CP |
| RD-12 | Onboarding saga | Closed behavioral | **Closed** | Spec Q-030 = gate F4 |
| RD-13 | Migration block ERP | Closed MVP | **Closed** | Sin cambio |
| RD-14 | Health minimal | Closed | **Closed** | Sin cambio |
| RD-15 | Permission resolution | Closed behavioral | **Closed** | Sin cambio |

**Resultado: 15/15 Closed** (14 sin cambio material; RD-07, RD-08, RD-11 amended)

---

## 3. RD-07 Amended — Matriz operation_class (BL-1.0)

Resuelve contradicción C-04 y gap validation 5.5.

| Entidad / operación | Plano E3 | operation_class | Notas |
|---------------------|----------|-----------------|-------|
| Tenant Registry lookup | CP | control_plane | |
| Installation Mode / Storage Metadata | CP | control_plane | |
| Product Module/Menu/Permission catalog | CP | control_plane | Read from L5 via platform services |
| User Session V2 / Refresh Token / Token Family | Transversal | **control_plane** | ADR-002-A MVP |
| Access Token Blacklist (Redis) | Transversal | N/A cache | Fuera SQL gateway |
| User Identity (perfil) | DP | tenant_data | |
| Role / Grant / User-Role | DP | tenant_data | ADR-003-A |
| Company / Org / ERP all | DP | tenant_data | |
| Auth Config tenant | DP | tenant_data | |
| auth_audit_log | Transversal | **tenant_data** | Resuelve C-04; store según tenant mode |
| Product Reference catalogs (`cat_*`) | CP definición | tenant_data read | Réplica local dedicated ADR-011-A |
| Provisioning state | CP | control_plane | |
| IAM Audit (platform) | CP/Transversal | control_plane | |

---

## 4. RD-08 Amended — Fallback policy

| Condición | Acción BL-1.0 |
|-----------|---------------|
| Metadata ausente + mode implicit shared/legacy | Fallback shared (G-13) |
| Metadata ausente + Installation Mode = dedicated | **Fail** (RI-39) |
| Fallback shared ejecutado | **Log + metric `metadata_fallback_shared_total`** obligatorio |
| Dedicated explicit sin Storage Endpoint row | **Fail** — no fallback |

---

## 5. RD-11 — Cambio material (Abierta → Closed)

| Campo | Borrador E4 | BL-1.0 |
|-------|-------------|--------|
| Decisión | Diferida | **Sesiones IAM en Control Plane Store (ADR-002-A)** |
| L5 impact | Idéntico | Idéntico |
| L6 impact | TBD | Session IAM ops → control_plane route |
| Reevaluación | — | BL-PEND-04 post-MVP (tenant DP option) |

---

## 6. RD-06 Ampliación — Gateway enforcement

| Regla BL-1.0 | Descripción |
|--------------|-------------|
| RD-06-E01 | 100% SQL vía execute_* / UoW / get_db_connection whitelist |
| RD-06-E02 | Audit repositories legacy pre-F1 (validation R-02) |
| RD-06-E03 | CI grep: `create_async_engine` fuera whitelist = fail |

---

## 7. Validación Etapa 5.5 — veredicto final

| RD | Validación 5.5 | Post-freeze |
|----|----------------|-------------|
| RD-01 | Correcta | Closed |
| RD-06 | Correcta + ampliar | Closed + enforcement |
| RD-07 | Incompleta | Closed + matriz §3 |
| RD-08 | Correcta + ampliar | Closed + alerting |
| RD-11 | Debe cerrarse | **Closed** ADR-002-A |
| RD-12 | Correcta + ampliar | Closed; Q-030 gate F4 |
| RD-13 | Correcta | Closed |

---

## 8. Decisiones técnicas TD vinculadas (E5)

| TD | RD relacionada | Estado |
|----|----------------|--------|
| TD-01 | RD-01 | Closed |
| TD-05 | RD-01 | Closed — no request session |
| TD-08 | RD-06, ADR-006 | Closed |
| TD-11 | RD-06 | Closed |
| TD-13 | RD-11 | **Obsoleto** — RD-11 cerrada BL-1.0 |

---

## 9. Conclusión

Todas las Runtime Decisions están **Closed** en BL-1.0. Cambios material: **RD-11** (cierre ADR-002-A), **RD-07** (matriz), **RD-08** (alerting).

Implementación Etapa 6 **no puede** contradecir ninguna RD Closed sin nueva ADR.
