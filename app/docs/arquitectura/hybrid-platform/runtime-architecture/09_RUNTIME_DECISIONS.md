# 09 — Runtime Decisions

> **Baseline BL-1.0 (2026-06-25):** Estado oficial RD → **`architecture-baseline/03_RUNTIME_DECISION_STATUS.md`**.  
> RD-11 cerrada (ADR-002-A). Detalle histórico RD-01–15 permanece en este documento.

**Etapa:** 4 — Runtime Architecture  
**Fecha:** 2026-06-25 (actualizado BL-1.0)  
**Estado:** Referencia detallada; tabla resumen **superseded** por baseline 03

---

## 1. Propósito

Registrar decisiones tomadas sobre comportamiento en ejecución. Formato: contexto, problema, alternativas, decisión, consecuencia, relación etapas previas.

---

## RD-01 — Resolución de persistencia por operación de datos

| Campo | Contenido |
|-------|-----------|
| **Contexto** | E2 mencionaba resolución once-per-request; AS-IS resuelve per execute_* |
| **Problema** | ¿Cuándo se resuelve almacén en el runtime canónico? |
| **Alternativas** | A) Una vez por request; B) Por operación de datos; C) Por handler explícito |
| **Decisión** | **B) Por operación de datos** en L6, con **cache de ruta intra-request** opcional |
| **Consecuencia** | Múltiples ops mismo request reusan route binding; compatible AS-IS; no requiere request-scoped session |
| **Relación** | E2 impact surface L6; RI-36; RR-80 mitigado por route cache conceptual |

---

## RD-02 — Tenant Context antes de autenticación

| Campo | Contenido |
|-------|-----------|
| **Contexto** | Login necesita tenant antes de validar user |
| **Problema** | Orden middleware vs auth |
| **Alternativas** | A) Auth first; B) Tenant first |
| **Decisión** | **B) Tenant Resolution precede Security Gates** |
| **Consecuencia** | Host obligatorio producción; alinea AS-IS TenantMiddleware |
| **Relación** | E1 Tenant; RI-01–05; CP-01 |

---

## RD-03 — Installation Mode invisible en L5

| Campo | Contenido |
|-------|-----------|
| **Contexto** | AS-IS middleware carga database_type en TenantContext |
| **Problema** | ¿Application layer conoce modo? |
| **Alternativas** | A) Exponer mode L5; B) Solo L6 |
| **Decisión** | **B) Installation Mode solo L6** via Storage Metadata lookup |
| **Consecuencia** | Middleware puede cargar metadata interna pero L5 no consume; refactor AS-IS branches |
| **Relación** | E1 P5; RI-32; RR-81 |

---

## RD-04 — Refresh token tenant desde token, no Host

| Campo | Contenido |
|-------|-----------|
| **Contexto** | Platform host + tenant refresh |
| **Problema** | Mismatch refresh en superadmin host |
| **Alternativas** | A) Host primary; B) Token primary |
| **Decisión** | **B) Token primary** para refresh/logout |
| **Consecuencia** | Preserva AS-IS correct behavior; RI-23 |
| **Relación** | E1 IAM; AS-IS audit |

---

## RD-05 — Identity operativo vs fila usuario bajo impersonation

| Campo | Contenido |
|-------|-----------|
| **Contexto** | Superadmin fila SYSTEM vs target tenant |
| **Problema** | ¿Qué tenant usa ERP data path? |
| **Alternativas** | A) current_user.cliente_id; B) JWT target tenant |
| **Decisión** | **B) JWT target tenant** para tenant operativo |
| **Consecuencia** | require_session_cliente_id pattern; RI-18 |
| **Relación** | E1 impersonation; E3 IAM |

---

## RD-06 — Persistence Gateway como único L6

| Campo | Contenido |
|-------|-----------|
| **Contexto** | Múltiples paths conexión AS-IS |
| **Problema** | ¿Quién accede stores? |
| **Alternativas** | A) Services direct; B) Single gateway |
| **Decisión** | **B) Todo acceso datos vía Persistence Gateway abstraction** |
| **Consecuencia** | execute_* / UoW son facades del gateway; RI-31 |
| **Relación** | E2 change surface; B-01 |

---

## RD-07 — Control vs Tenant data route explícito

| Campo | Contenido |
|-------|-----------|
| **Contexto** | ADMIN vs DEFAULT AS-IS |
| **Problema** | ¿Cómo distinguir planos en runtime? |
| **Alternativas** | A) Implicit table; B) Explicit operation class |
| **Decisión** | **B) Operation class** (control_plane | tenant_data) declarado en L6 call |
| **Consecuencia** | Semántica DatabaseConnection preservada conceptualmente |
| **Relación** | E3 CP/DP; RI-35, RI-36 |

---

## RD-08 — Fallback Shared si metadata ausente

| Campo | Contenido |
|-------|-----------|
| **Contexto** | Tenants legacy sin Storage Metadata |
| **Problema** | Routing sin metadata |
| **Alternativas** | A) Fail; B) Fallback Shared |
| **Decisión** | **B) Fallback Shared** solo si mode not dedicated |
| **Consecuencia** | Backward compat E2; RI-38; RI-39 dedicated explicit |
| **Relación** | E2 backward compat; AS-IS routing |

---

## RD-09 — Contextos request-scoped estrictos

| Campo | Contenido |
|-------|-----------|
| **Contexto** | ContextVar AS-IS |
| **Problema** | Scope de contextos |
| **Alternativas** | A) Request-scoped; B) Async task inherited |
| **Decisión** | **A) Request-scoped** con teardown obligatorio |
| **Consecuencia** | RI-09, RI-10; async must rehydrate |
| **Relación** | E4 context model |

---

## RD-10 — ERP session contract separado de Identity

| Campo | Contenido |
|-------|-----------|
| **Contexto** | Multiempresa, selection token |
| **Problema** | ¿Cuándo Company Context? |
| **Alternativas** | A) Siempre en JWT; B) Gate ERP separado |
| **Decisión** | **B) ERP session gate** (full session vs selection pending) |
| **Consecuencia** | Preserva AS-IS deps_auth; RI-30 |
| **Relación** | AS-IS deps_auth; E1 Empresa |

---

## RD-11 — Session store location

| Campo | Contenido |
|-------|-----------|
| **Contexto** | Q-010 E3; validación 5.5 AR-C01 |
| **Problema** | ¿Session en CP o DP? |
| **Alternativas** | A) Central; B) Tenant DP; C) Hybrid |
| **Decisión (BL-1.0)** | **A) Control Plane central** — ADR-002-A para MVP |
| **Consecuencia** | IAM session ops → operation_class control_plane; L5 sin cambio observable |
| **Reevaluación** | Post-MVP Alternativa B si compliance/latencia (BL-PEND-04) |
| **Relación** | E3 Q-010; `architecture-baseline/02_ADR_STATUS.md` ADR-002 |

---

## RD-12 — Onboarding como saga multi-fase runtime

| Campo | Contenido |
|-------|-----------|
| **Contexto** | Single TX AS-IS |
| **Problema** | Cross-plane onboarding |
| **Alternativas** | A) Single TX; B) Multi-phase saga |
| **Decisión** | **B) Saga** observable externally same response |
| **Consecuencia** | Provisioning state; dedicated async |
| **Relación** | E3 lifecycle; E2 onboarding surface |

---

## RD-13 — Migration blocks ERP traffic

| Campo | Contenido |
|-------|-----------|
| **Contexto** | Shared→Dedicated copy |
| **Problema** | Concurrent ERP during migration |
| **Alternativas** | A) Online dual-write; B) Offline block |
| **Decisión** | **B) Tenant Migrando blocks ERP** (MVP) |
| **Consecuencia** | RI-14; RR-40 mitigated |
| **Relación** | E1 lifecycle; ADR-008 E1 |

---

## RD-14 — Health check minimal exposure

| Campo | Contenido |
|-------|-----------|
| **Contexto** | K8s probes |
| **Problema** | ¿Cuánto validar? |
| **Alternativas** | A) Full tenant; B) Liveness only |
| **Decisión** | **B) Liveness + optional DB ping** sin auth |
| **Consecuencia** | RI-55; minimal Tenant Context |
| **Relación** | AS-IS /health |

---

## RD-15 — Permission resolution vía servicio, no join L5

| Campo | Contenido |
|-------|-----------|
| **Contexto** | Q-021 E3 |
| **Problema** | CP permission + DP grant |
| **Alternativas** | A) SQL join; B) Resolution service |
| **Decisión** | **B) Authorization Context pre-computed L4** from resolution service |
| **Consecuencia** | ERP receives gate result only; RI-07 |
| **Relación** | E3 SSOT split |

---

## 2. Tabla resumen decisiones

| ID | Tema | Estado |
|----|------|--------|
| RD-01 | Resolution per op | Cerrada |
| RD-02 | Tenant before auth | Cerrada |
| RD-03 | Mode invisible L5 | Cerrada |
| RD-04 | Refresh tenant source | Cerrada |
| RD-05 | Impersonation tenant | Cerrada |
| RD-06 | Single L6 gateway | Cerrada |
| RD-07 | Operation class | Cerrada |
| RD-08 | Shared fallback | Cerrada |
| RD-09 | Request-scoped context | Cerrada |
| RD-10 | ERP session gate | Cerrada |
| RD-11 | Session store | **Cerrada (MVP)** — ADR-002-A |
| RD-12 | Onboarding saga | Cerrada (behavioral) |
| RD-13 | Migration block | Cerrada (MVP) |
| RD-14 | Health minimal | Cerrada |
| RD-15 | Permission resolution | Cerrada (behavioral) |

---

## 3. Decisiones explícitamente NO tomadas (Etapa 5+)

- SQLAlchemy session factory shape
- Connection pool sizing
- Saga compensation steps detail
- Session central vs tenant store (RD-11)
- Online migration dual-write
- Request-scoped single DB session

---

## 4. Conclusión

15 decisiones runtime documentadas; **15 cerradas** en BL-1.0 (RD-11 vía ADR-002-A). Estado oficial: `architecture-baseline/03_RUNTIME_DECISION_STATUS.md`.
