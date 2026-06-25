# 08 — Runtime Risks

**Etapa:** 4 — Runtime Architecture  
**Fecha:** 2026-06-25  
**Estado:** Borrador para revisión  
**Restricción:** Análisis de riesgos. Sin propuestas de implementación.

---

## 1. Propósito

Identificar riesgos del modelo runtime: propagación de contexto, leaks, resolución incorrecta, cache, concurrencia, y contradicciones con etapas anteriores o AS-IS.

---

## 2. Riesgos de propagación de contexto

| ID | Riesgo | Descripción | Severidad |
|----|--------|-------------|-----------|
| RR-01 | Tenant Context missing | Handler ejecuta sin middleware | Crítico |
| RR-02 | Host/JWT tenant mismatch | Token de tenant A en Host tenant B | Alto |
| RR-03 | Impersonation context confusion | ERP usa fila SYSTEM en vez JWT target | Crítico |
| RR-04 | Company Context stale | JWT no actualizado post switch | Alto |
| RR-05 | Async context bleed | Task hijo hereda ContextVar | Alto |
| RR-06 | Background job sin scope | Job accede tenant incorrecto | Crítico |
| RR-07 | request.state vs ContextVar drift | Fuentes tenant divergentes AS-IS | Medio |

---

## 3. Tenant leaks

| ID | Riesgo | Descripción | Severidad |
|----|--------|-------------|-----------|
| RR-10 | Missing tenant filter shared | Query sin filter en shared store | Crítico |
| RR-11 | Wrong Persistence Context | Dedicated tenant routed to shared | Crítico |
| RR-12 | Superadmin cross-tenant sin audit | Data leak compliance | Crítico |
| RR-13 | Cache key sin tenant | Permission cache cross-tenant | Alto |
| RR-14 | Engine cache wrong tenant | Stale engine after mode change | Alto |

---

## 4. Cache inválida

| ID | Riesgo | Descripción | Severidad |
|----|--------|-------------|-----------|
| RR-20 | Permission cache stale | Grant change no invalida | Alto |
| RR-21 | Storage metadata cache stale | Post-migration wrong route | Crítico |
| RR-22 | Redis blacklist fail-open | Revoked token accepted AS-IS | Alto |
| RR-23 | Session bridge desync | Redis vs session store | Medio |
| RR-24 | SQL Server version cache | Wrong query path | Bajo |

---

## 5. Errores de resolución

| ID | Riesgo | Descripción | Severidad |
|----|--------|-------------|-----------|
| RR-30 | Dedicated fallback silent | Dedicated tenant reads shared | Crítico |
| RR-31 | Metadata missing misread | New tenant wrong mode | Alto |
| RR-32 | Control/data route inversion | ERP write to control plane | Crítico |
| RR-33 | IAM session store unreachable | Login ok ERP fail dedicated | Crítico |
| RR-34 | Chicken-egg metadata lookup | Bootstrap failure | Medio |

---

## 6. Race conditions (conceptuales)

| ID | Riesgo | Descripción | Severidad |
|----|--------|-------------|-----------|
| RR-40 | Migration concurrent requests | Read during copy | Crítico |
| RR-41 | Onboarding double submit | Duplicate tenant | Alto |
| RR-42 | Refresh rotation race | Double refresh replay | Medio |
| RR-43 | Sequence increment race | Duplicate document codes | Alto |
| RR-44 | Mode change during request | Mid-flight route change | Alto |

---

## 7. Engine reuse & recursos

| ID | Riesgo | Descripción | Severidad |
|----|--------|-------------|-----------|
| RR-50 | Engine pool exhaustion | N dedicated tenants | Alto |
| RR-51 | Connection leak | Session not closed per op AS-IS | Medio |
| RR-52 | No async engine dispose shutdown | Worker restart leak | Medio |
| RR-53 | Noisy neighbor shared | Latency tenant ERP | Medio |

---

## 8. Deadlocks conceptuales

| ID | Riesgo | Descripción | Severidad |
|----|--------|-------------|-----------|
| RR-60 | Cross-store wait | Future: CP lock waiting DP | Medio |
| RR-61 | Long UoW + row lock | INV concurrent process | Medio |
| RR-62 | Migration lock tenant | All ERP blocked | Esperado |

---

## 9. Cuellos de botella

| ID | Cuello | Impacto |
|----|--------|---------|
| RR-70 | Control Plane lookup every request | Latency tenant resolution |
| RR-71 | Metadata lookup per data op | Multiply ERP list endpoints |
| RR-72 | Permission resolver cold | First request slow |
| RR-73 | N dedicated engines memory | Scale limit workers |
| RR-74 | Central session store | IAM hotspot all tenants |

---

## 10. Contradicciones con etapas anteriores

| ID | Contradicción | Etapas | Descripción |
|----|---------------|--------|-------------|
| RR-80 | Per-op vs per-request resolution | E2 invariant example vs AS-IS | E2 sugiere once/request; AS-IS per execute_*; canonical accepts per-op with same route |
| RR-81 | database_type in TenantContext | E1 P5 vs AS-IS middleware | Middleware enriches mode; L5 must not read |
| RR-82 | IAM services branch on mode | E3 ownership vs AS-IS user_context | Violates RI-32 |
| RR-83 | Session SSOT IAM, store TBD | E3 vs runtime | RR-33 until Q-010 closed |
| RR-84 | Grants SSOT tenant DP | E3 vs AS-IS central | Resolution cross-store RR-33 |

**Acción:** Documentadas; no auto-corregidas. Revisión en RD-01–RD-04.

---

## 11. Riesgos por flujo

| Flujo | Top risk |
|-------|----------|
| Login | RR-02 tenant mismatch |
| Refresh | RR-23 store split |
| ERP Shared | RR-10 filter miss |
| ERP Dedicated | RR-11 wrong route |
| Impersonation | RR-03 context |
| Onboarding | RR-41 duplicate |
| Migration | RR-40 concurrent |
| Background | RR-06 scope |

---

## 12. Matriz probabilidad × impacto

| | Bajo impacto | Alto impacto |
|---|-------------|--------------|
| **Alta prob** | RR-51, RR-70 | RR-10, RR-02 |
| **Media prob** | RR-24 | RR-21, RR-40 |
| **Baja prob** | RR-52 | RR-11, RR-32 |

---

## 13. Mitigaciones conceptuales (no implementación)

| Riesgo | Dirección mitigación |
|--------|---------------------|
| RR-10 | Mandatory L6 tenant filter policy |
| RR-11 | Explicit dedicated no-fallback RI-39 |
| RR-03 | Session scope resolver canonical |
| RR-21 | Metadata cache invalidation event |
| RR-40 | Tenant Migrando blocks ERP |
| RR-06 | Synthetic context contract jobs |

---

## 14. Conclusión

El runtime canónico **concentra riesgos en L6 y L4**. L5 protegido reduce superficie. Principales gaps AS-IS: mode branches L5, per-op resolution caching, session store undecided.

Prioridad revisión: RR-11, RR-10, RR-03, RR-33, RR-80.
