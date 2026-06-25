# 01 — Runtime Architecture Overview

**Etapa:** 4 — Runtime Architecture & Request Execution Model  
**Fecha:** 2026-06-25  
**Estado:** Borrador para revisión  
**Prerequisitos:** AS-IS audit, Modelo conceptual (E1), Impact Assessment (E2), Canonical Data Model (E3)  
**Restricción:** Comportamiento del sistema. Sin implementación, clases, SQL ni pseudocódigo.

---

## 1. Propósito

Describir **cómo opera la plataforma durante la ejecución**: participantes, capas, responsabilidades, flujo general e invariantes del runtime híbrido (Shared y Dedicated).

Este documento define **comportamiento**, no componentes de código.

---

## 2. Visión del runtime

La plataforma procesa cada petición HTTP como un **pipeline determinista** que:

1. Identifica el tenant de entrada (Host)
2. Establece contextos de ejecución (tenant, identidad, empresa, autorización)
3. Autentica y autoriza al actor
4. Ejecuta lógica de negocio agnóstica al modo de instalación
5. Resuelve almacenamiento solo en el momento de acceso a datos
6. Retorna respuesta sin exponer infraestructura al cliente

**Principio rector:** El runtime separa **contexto de negocio** (visible a application layer) de **contexto de persistencia** (visible solo a infrastructure layer).

---

## 3. Participantes del runtime

| Participante | Rol en ejecución |
|--------------|------------------|
| **Cliente** | Browser, mobile app, integración externa |
| **Edge (Nginx / reverse proxy)** | TLS termination, routing a backend, preservación Host |
| **FastAPI Application** | Orquestador HTTP, routing a handlers |
| **Ingress Pipeline** | Middleware stack pre-handler |
| **Tenant Resolution** | Subdominio → Tenant Registry lookup |
| **Context Registry** | Almacén request-scoped de contextos lógicos |
| **Authentication Gate** | Validación JWT, sesión, blacklist |
| **Authorization Gate** | RBAC, session contract, ERP scope |
| **Application Layer** | Platform, IAM orchestration, ERP services |
| **Persistence Gateway** | Único punto de resolución almacén + acceso datos |
| **Control Plane Store** | Almacén metadata Platform |
| **Tenant Data Store** | Almacén data plane (shared lógico o dedicated físico) |
| **Cache Layer (Redis)** | Estado efímero: blacklist, session bridge, permission cache |
| **Background Scheduler** | Jobs fuera del ciclo request HTTP |

---

## 4. Capas de ejecución (top-down)

```
┌─────────────────────────────────────────────────────────┐
│  L0 — Edge / Transport                                   │
├─────────────────────────────────────────────────────────┤
│  L1 — HTTP Ingress (FastAPI routing)                     │
├─────────────────────────────────────────────────────────┤
│  L2 — Cross-Cutting Pipeline (middleware, exceptions)    │
├─────────────────────────────────────────────────────────┤
│  L3 — Context Establishment (tenant, identity, company)  │
├─────────────────────────────────────────────────────────┤
│  L4 — Security Gates (authn, authz, session contract)    │
├─────────────────────────────────────────────────────────┤
│  L5 — Application (Platform | IAM | ERP)                 │
├─────────────────────────────────────────────────────────┤
│  L6 — Persistence Gateway (resolution + data access)     │
├─────────────────────────────────────────────────────────┤
│  L7 — Stores (Control Plane | Tenant Data | Cache)       │
└─────────────────────────────────────────────────────────┘
```

### 4.1 Responsabilidades por capa

| Capa | Responsabilidad | Conoce modo instalación |
|------|-----------------|-------------------------|
| L0–L1 | Transporte HTTP | No |
| L2 | Pipeline transversal | No |
| L3 | Contextos lógicos | No (tenant sí; mode no en L5) |
| L4 | Seguridad | No |
| L5 | Reglas de negocio | **No** |
| L6 | Resolución almacén | **Sí (única capa)** |
| L7 | Persistencia física | N/A |

---

## 5. Flujo general (happy path ERP)

```
Cliente
  → Edge (preserva Host)
  → FastAPI match route
  → Middleware: Tenant Resolution → Tenant Context
  → Middleware: cleanup registration
  → Security Gates: JWT → Identity Context
  → Security Gates: RBAC → Authorization Context
  → Security Gates: ERP session → Company Context
  → Application: ERP service (recibe contextos)
  → Persistence Gateway: resolve store → execute
  → Tenant Data Store
  → Application: map result
  → Response JSON
  → Middleware: destroy contexts
  → Cliente
```

---

## 6. Dos planos de ejecución

### 6.1 Plano de control (runtime)

Operaciones que **solo** leen/escriben Control Plane:

- Lookup tenant por subdominio
- Login validation contra Tenant Registry (activo)
- Platform admin endpoints
- Module catalog reads
- Provisioning orchestration (evento especial)

**Resolución:** siempre Control Plane Store.

### 6.2 Plano de datos (runtime)

Operaciones ERP, tenant admin, IAM identity (data plane):

- CRUD ERP
- Users/RBAC tenant
- Onboarding seed data plane

**Resolución:** Persistence Gateway consulta Installation Mode metadata → Tenant Data Store (shared o dedicated).

---

## 7. Modos de instalación en runtime

| Modo | Comportamiento observable L5 | Comportamiento L6 |
|------|------------------------------|-------------------|
| **Shared** | Idéntico | Tenant Data Store compartido; aislamiento lógico |
| **Dedicated** | Idéntico | Tenant Data Store exclusivo |
| **On-Premise / Cloud privada** | Idéntico | Metadata apunta a endpoint externo |

**Invariante:** L5 no branch por modo.

---

## 8. Contextos vs almacenes

| Concepto | Naturaleza | Scope |
|----------|------------|-------|
| Tenant Context | Lógico | Request |
| Identity Context | Lógico | Request |
| Company Context | Lógico | Request |
| Authorization Context | Lógico | Request / cache proceso |
| Persistence Context | Infraestructura | Operación de datos |
| Request Context | Meta | Request |

Detalle: `03_CONTEXT_PROPAGATION.md`.

---

## 9. Invariantes del runtime (resumen)

1. Toda request HTTP productiva tiene Tenant Context (salvo health público).
2. ERP nunca resuelve almacén.
3. Frontend nunca recibe Installation Mode.
4. Tenant Context se establece antes de autenticación.
5. Identity Context requiere Tenant Context coherente.
6. Company Context requerido para operaciones ERP operativas.
7. Persistence resolution ocurre en L6, no en L5.
8. Control Plane Store y Tenant Data Store son rutas distintas.
9. Respuesta HTTP no expone errores de infraestructura crudos.
10. Contextos se destruyen al finalizar request.

Lista completa: `06_RUNTIME_INVARIANTS.md` (40+).

---

## 10. Eventos fuera del ciclo request

| Evento | Trigger | Runtime especial |
|--------|---------|------------------|
| Application startup | Process boot | Catalog sync, permission sync |
| Background job | Scheduler | Contexto sintético tenant |
| Onboarding saga | Platform API | Multi-fase; estados Provisioning |
| Migration | Platform ops | Tenant estado Migrando; sin requests ERP |
| Health check | Probe | Tenant Context opcional / default |

Detalle: `04_RUNTIME_FLOWS.md`.

---

## 11. Relación con etapas anteriores

| Etapa | Aporta al runtime |
|-------|-------------------|
| AS-IS | Pipeline actual: Host→Middleware→deps→execute_* |
| E1 Conceptual | Fronteras Platform/IAM/ERP |
| E2 Impact | L5 protegido; L6 superficie de cambio |
| E3 Canonical | CP/DP/TR; ownership; SSOT |

**Nota AS-IS vs canónico:** Hoy la resolución ocurre por operación de datos, no una vez por request. Documentado como gap en `08_RUNTIME_RISKS.md` y decisión RD-01 en `09_RUNTIME_DECISIONS.md`.

---

## 12. Documentos relacionados

| Documento | Contenido |
|-----------|-----------|
| `02_REQUEST_LIFECYCLE.md` | Ciclo paso a paso |
| `03_CONTEXT_PROPAGATION.md` | Contextos canónicos |
| `04_RUNTIME_FLOWS.md` | Flujos específicos |
| `05_RUNTIME_BOUNDARIES.md` | Dependencias entre capas |
| `07_RUNTIME_SEQUENCE_DIAGRAMS.md` | Diagramas conceptuales |

---

## 13. Conclusión

El runtime híbrido es un **pipeline de contextos** seguido de **acceso a datos mediado**. La variación Shared/Dedicated es invisible para application layer y transparente para Frontend.

La especificación completa del comportamiento se detalla en los documentos 02–09 de esta carpeta.
