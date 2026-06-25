# 10 — Executive Summary: Runtime Architecture

**Etapa:** 4 — Runtime Architecture & Request Execution Model  
**Fecha:** 2026-06-25  
**Estado:** Borrador para revisión y aprobación  
**Audiencia:** Arquitecto Principal, Tech Lead, SRE, Security

---

## 1. Objetivo cumplido

Se especificó **completamente el comportamiento en tiempo de ejecución** de la plataforma híbrida: cómo entra una request, cómo se identifica el tenant, cómo fluyen los contextos, cómo se resuelve el almacén, y cómo retorna la respuesta — **sin diseñar implementación**.

**10 documentos** en `app/docs/arquitectura/hybrid-platform/runtime-architecture/`.

---

## 2. Runtime en una frase

> Cada request establece **contextos lógicos** (tenant, identidad, empresa, autorización) en capas superiores; la **lógica de negocio** opera sin conocer el modo de instalación; el **Persistence Gateway** resuelve el almacén correcto solo al acceder datos.

---

## 3. Pipeline canónico

```
Cliente → Edge → FastAPI → Middleware (Tenant Context)
→ Security Gates (Identity, Authorization, Company)
→ Application (Platform | IAM | ERP)
→ Persistence Gateway (resolve store)
→ Control Plane Store | Tenant Data Store
→ Response → Teardown
```

---

## 4. Nivel de madurez

| Área | Madurez | Notas |
|------|---------|-------|
| Request lifecycle | **Alta** | 10 fases documentadas |
| Context model | **Alta** | 6 contextos + reglas |
| ERP flow | **Alta** | Shared = Dedicated L5 |
| IAM flows | **Alta** | Login/refresh/logout/impersonation |
| Platform flow | **Alta** | Control plane route |
| Onboarding runtime | **Media** | Saga behavioral; mechanics Etapa 5 |
| Migration runtime | **Media** | MVP offline block |
| Session store route | **Baja** | RD-11 abierta |
| AS-IS alignment | **Media** | Gaps documentados |

**Madurez global Etapa 4:** **Alta** para request execution; **Media** para provisioning/migration mechanics.

---

## 5. Decisiones runtime clave

| Decisión | Resumen |
|----------|---------|
| RD-01 | Resolución almacén **por operación** L6 (route cache intra-request) |
| RD-03 | Installation Mode **invisible L5** |
| RD-04 | Refresh/logout tenant desde **token**, no Host |
| RD-05 | Impersonation usa **JWT target tenant** operativo |
| RD-06 | **Persistence Gateway** único punto L6 |
| RD-08 | Fallback Shared si metadata ausente (not dedicated) |
| RD-13 | Migración **bloquea ERP** (MVP) |

---

## 6. Invariantes

**62 invariantes** definidos (`06_RUNTIME_INVARIANTS.md`), incluyendo:

- Toda request tiene Tenant Context
- ERP nunca resuelve conexiones
- Frontend nunca conoce Installation Mode
- No branch Shared/Dedicated en ERP
- Teardown siempre

---

## 7. Riesgos restantes

| Prioridad | Riesgo |
|-----------|--------|
| **Crítico** | Wrong dedicated route (RR-11) |
| **Crítico** | Tenant filter miss shared (RR-10) |
| **Crítico** | Impersonation context error (RR-03) |
| **Alto** | Session store split undecided (RR-33) |
| **Alto** | Metadata cache stale post-migration (RR-21) |
| **Medio** | AS-IS mode branches L5 (RR-82) |
| **Medio** | Per-request vs per-op caching (RR-80) |

---

## 8. Preguntas abiertas (para Etapa 5)

| # | Pregunta | Origen |
|---|----------|--------|
| O-01 | Session store: central vs tenant DP | RD-11, Q-010 |
| O-02 | Route cache intra-request: obligatorio u opcional | RD-01 técnico |
| O-03 | Saga onboarding step definitions | RD-12 |
| O-04 | Dedicated async UX (polling vs sync wait) | E1 Q-033 |
| O-05 | Online migration future | RD-13 extensión |

**Ninguna reabre ownership E3 ni fronteras E1.**

---

## 9. Contradicciones documentadas (no auto-corregidas)

| ID | Descripción | Ubicación |
|----|-------------|-----------|
| RR-80 | Per-op resolution vs once-per-request wording E2 | RD-01 resuelve |
| RR-81 | database_type en TenantContext AS-IS | RD-03 |
| RR-82 | IAM services read mode L5 | RI-32 gap |
| RR-84 | Grants physical location vs SSOT E3 | Etapa 5 alignment |

---

## 10. Conformidad etapas previas

| Etapa | Construido sobre | Sin replantear |
|-------|------------------|----------------|
| AS-IS | Pipeline Host→Middleware→execute_* | ✅ |
| E1 Conceptual | Platform/IAM/ERP, P5 | ✅ |
| E2 Impact | L5 protegido, L6 change | ✅ |
| E3 Canonical | CP/DP/TR ownership | ✅ |

---

## 11. Preparación Etapa 5 (Diseño técnico infraestructura)

Tras aprobación Etapa 4, Etapa 5 puede abordar:

1. **Persistence Gateway** — contrato técnico (sin implementar aún en código)
2. **Route resolution algorithm** — metadata lookup, cache, invalidation
3. **Session store decision** — cerrar RD-11 / Q-010
4. **Saga onboarding** — steps, idempotency keys
5. **AS-IS gap closure plan** — mode branches L5, grants location
6. **Integration test scenarios** — from runtime flows §04

**Prerrequisitos Etapa 5:**

- [ ] Aprobación formal Etapa 4
- [ ] Cierre RD-11 (session store)
- [ ] Aprobación RD-01 route caching policy

---

## 12. Documentación entregada

| # | Documento |
|---|-----------|
| 01 | [RUNTIME_ARCHITECTURE_OVERVIEW.md](./01_RUNTIME_ARCHITECTURE_OVERVIEW.md) |
| 02 | [REQUEST_LIFECYCLE.md](./02_REQUEST_LIFECYCLE.md) |
| 03 | [CONTEXT_PROPAGATION.md](./03_CONTEXT_PROPAGATION.md) |
| 04 | [RUNTIME_FLOWS.md](./04_RUNTIME_FLOWS.md) |
| 05 | [RUNTIME_BOUNDARIES.md](./05_RUNTIME_BOUNDARIES.md) |
| 06 | [RUNTIME_INVARIANTS.md](./06_RUNTIME_INVARIANTS.md) |
| 07 | [RUNTIME_SEQUENCE_DIAGRAMS.md](./07_RUNTIME_SEQUENCE_DIAGRAMS.md) |
| 08 | [RUNTIME_RISKS.md](./08_RUNTIME_RISKS.md) |
| 09 | [RUNTIME_DECISIONS.md](./09_RUNTIME_DECISIONS.md) |
| 10 | [EXECUTIVE_SUMMARY.md](./10_EXECUTIVE_SUMMARY.md) |

---

## 13. Conclusión

La plataforma tiene ahora una **especificación runtime completa**: participantes, capas, lifecycle, contextos, flujos, fronteras, 62 invariantes, diagramas, riesgos y 15 decisiones.

**Shared y Dedicated son indistinguibles para Application Layer y Frontend.** Toda variación ocurre en **Persistence Gateway (L6)**.

**Recomendación:** Aprobar Etapa 4 y proceder a Etapa 5 cerrando **RD-11 (session store)** como primera decisión técnica.

---

## 14. Estimación cualitativa

| Trabajo post-aprobación | Esfuerzo |
|-------------------------|----------|
| Diseño técnico Persistence Gateway | M |
| Session store ADR final | S |
| Runtime test scenario catalog | S |
| AS-IS gap remediation plan | S |
| Implementación (Etapa 6+, fuera alcance) | L–XL |

**Etapa 4 no añade scope implementación** — reduce ambigüedad operativa antes de codificar.
