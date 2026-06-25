# 14 — Executive Summary: Technical Infrastructure Design

**Etapa:** 5 — Technical Infrastructure Design  
**Fecha:** 2026-06-25  
**Estado:** Borrador para revisión y aprobación  
**Audiencia:** Arquitecto Principal, Tech Lead, SRE, Backend Lead

---

## 1. Objetivo cumplido

Se diseñó **completamente la infraestructura técnica** que implementará el runtime híbrido aprobado en Etapa 4 — respondiendo cómo se resuelven conexiones, engines, sesiones, transacciones, cache y recovery — **sin escribir código ni modificar el backend**.

---

## 2. Infraestructura en una frase

> El **Persistence Gateway** evoluciona el pipeline AS-IS (`execute_*` + UoW + routing) para resolver Storage Metadata por operación, cachear bindings intra-request, y enrutar transparentemente a Shared o Dedicated — manteniendo L5 completamente agnóstico.

---

## 3. Documentos creados

| # | Documento | Contenido |
|---|-----------|-----------|
| 01 | [PERSISTENCE_GATEWAY](./01_PERSISTENCE_GATEWAY.md) | Facade L6, pipeline, contrato L5 |
| 02 | [STORAGE_METADATA_RESOLUTION](./02_STORAGE_METADATA_RESOLUTION.md) | Metadata CP, cache, fallback |
| 03 | [CONNECTION_RESOLUTION](./03_CONNECTION_RESOLUTION.md) | Árbol decisión, binding |
| 04 | [ENGINE_MANAGEMENT](./04_ENGINE_MANAGEMENT.md) | AsyncEngine lifecycle |
| 05 | [SESSION_LIFECYCLE](./05_SESSION_LIFECYCLE.md) | AsyncSession per-op / UoW |
| 06 | [UNIT_OF_WORK_DESIGN](./06_UNIT_OF_WORK_DESIGN.md) | Atomicidad multi-paso |
| 07 | [TRANSACTION_BOUNDARIES](./07_TRANSACTION_BOUNDARIES.md) | T1–T5 boundaries, saga |
| 08 | [QUERY_EXECUTION_MODEL](./08_QUERY_EXECUTION_MODEL.md) | Pipeline execute_* |
| 09 | [REPOSITORY_INTERACTION](./09_REPOSITORY_INTERACTION.md) | Legacy convivencia |
| 10 | [ENGINE_CACHE_POLICY](./10_ENGINE_CACHE_POLICY.md) | L-A, L-B, L-C cache |
| 11 | [FAILURE_RECOVERY](./11_FAILURE_RECOVERY.md) | Fail-closed, saga recovery |
| 12 | [IMPLEMENTATION_ROADMAP](./12_IMPLEMENTATION_ROADMAP.md) | Fases 0–8 Etapa 6 |
| 13 | [TECHNICAL_DECISIONS](./13_TECHNICAL_DECISIONS.md) | TD-01 a TD-13 |
| 14 | [EXECUTIVE_SUMMARY](./14_EXECUTIVE_SUMMARY.md) | Este documento |

**Total:** 14 documentos en `app/docs/arquitectura/hybrid-platform/technical-infrastructure/`

---

## 4. Decisiones técnicas clave

| ID | Decisión |
|----|----------|
| TD-01 | Cache intra-request route binding |
| TD-05 | **No** request-scoped SQL session — preservar AS-IS |
| TD-08 | Tenant filter defensivo también en dedicated |
| TD-11 | Evolucionar pipeline existente, no reescribir gateway |
| TD-12 | Saga onboarding semi-automática MVP |
| TD-13 | Block dedicated prod IAM hasta cerrar RD-11 |

**13 decisiones cerradas** — ver `13_TECHNICAL_DECISIONS.md`.

---

## 5. Alineación etapas previas

| Etapa | Cómo se respeta |
|-------|-----------------|
| E0 AS-IS | Baseline connection_async, queries_async, UoW documentado |
| E1 Conceptual | P5 invisible L5; single codebase |
| E2 Impact | ~5–8% change surface; ERP untouched |
| E3 Canonical | CP metadata; DP tenant data; operation class |
| E4 Runtime | RD-01 per-op; RD-06 gateway; RD-08 fallback |

---

## 6. Gaps AS-IS documentados (no auto-corregidos)

| Gap | Documento |
|-----|-----------|
| Gateway disperso, no módulo único | 01 |
| database_type en TenantContext L5 | 02, 03 |
| Onboarding single TX cross-plane | 07 |
| Async engines no shutdown | 04 |
| Repositories bypass parcial | 09 |
| IAM services read mode L5 | 03, roadmap F3 |

---

## 7. Preguntas abiertas

| ID | Pregunta | Bloqueante |
|----|----------|------------|
| RD-11 / Q-010 | Session store: CP vs tenant DP | **Sí** — dedicated IAM prod |
| O-E5-01 | Metadata cache Redis distribuido | No MVP |
| O-E5-04 | Compensación saga full-auto | No MVP |
| O-E5-05 | Outbox post-commit | No MVP |
| TD-03 | Consolidar engine key shared | Post-MVP F8 |

---

## 8. Riesgos identificados

| Prioridad | Riesgo | Mitigación diseño |
|-----------|--------|-------------------|
| **Crítico** | Wrong dedicated route | RI-39 fail explicit; TD-08 defensive filter |
| **Crítico** | Stale cache post-migration | Event invalidation L-B + L-C |
| **Alto** | Onboarding saga partial failure | TD-12 semi-auto + runbooks |
| **Alto** | Multi-worker stale metadata | TD-09 TTL + ops flush |
| **Medio** | N sessions per endpoint perf | Monitoreo; UoW donde aplique |
| **Medio** | Repository bypass auditor | Fase 3 audit repositories |

---

## 9. Nivel de madurez

| Área | Madurez |
|------|---------|
| Persistence Gateway design | **Alta** |
| Connection / Engine / Session | **Alta** |
| Query execution path | **Alta** |
| Transaction boundaries | **Alta** |
| Cache policy | **Alta** |
| Failure recovery | **Media-Alta** |
| Provisioning saga mechanics | **Media** |
| Session store (RD-11) | **Baja** |
| Migration tooling | **Media** (MVP offline) |

**Madurez global Etapa 5:** **Alta** para implementación core infra (Fases 0–3); **Media** para dedicated production end-to-end (Fases 4–6).

---

## 10. Preparación Etapa 6 (Implementación)

### Listo para implementar tras aprobación

- Fase 0: Test harness dedicated
- Fase 1: Gateway consolidation (connection_async, routing, queries_async)
- Fase 2: Shared regression gate
- Fase 3: L5 database_type cleanup

### Requiere decisión previa

- Fase 5: RD-11 session store ADR
- Fase 4: O-E5-04 compensación saga (semi-auto acordada TD-12)

### Criterios go Etapa 6

| # | Criterio |
|---|----------|
| 1 | Aprobación formal Etapa 5 |
| 2 | Guardrails G-01–G-20 acknowledged |
| 3 | Plan Fase 0–2 asignado |
| 4 | ADR session store scheduled (parallel track) |

---

## 11. Estimación implementación MVP

| Scope | Esfuerzo | Riesgo |
|-------|----------|--------|
| F0–F3 Infra + cleanup | M | Medio |
| F4 Provisioning saga | L | Alto |
| F5 Session store | M | Medio |
| F6 Dedicated prod | M | Alto |
| **Total MVP** | **L** | **Medio-Alto** |

ERP modules: **0 archivos** en scope MVP.

---

## 12. Conclusión

Etapa 5 entrega una **especificación técnica implementable** de la infraestructura híbrida: el Persistence Gateway como evolución del stack AS-IS, tres capas de cache, boundaries transaccionales claros, y roadmap en 8 fases.

**Recomendación:** Aprobar Etapa 5 e iniciar Etapa 6 por **Fase 0–1** (harness + gateway), en paralelo con **ADR session store (RD-11)** para desbloquear Fase 5.

**No se modificó código fuente** — únicamente documentación oficial.
