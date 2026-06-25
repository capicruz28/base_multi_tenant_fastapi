# 07 — Resumen Ejecutivo: Impact Assessment

**Etapa:** 2 — Architectural Impact Assessment  
**Fecha:** 2026-06-25  
**Estado:** Borrador para revisión y aprobación  
**Audiencia:** Arquitecto Principal, Tech Lead, Producto

---

## 1. Pregunta central

> ¿Cuál es el impacto REAL de incorporar Dedicated Database sobre la arquitectura existente?

### Respuesta

**El impacto es acotado y concentrado.** Aproximadamente **65–70% del backend puede permanecer intacto**, incluyendo toda la lógica ERP, contratos Frontend, JWT, sesiones IAM y endpoints REST. El cambio real afecta **menos del 8% de los componentes**, principalmente infraestructura de persistencia y orquestación de onboarding.

Dedicated Database **no requiere** un segundo backend, fork de código, ni modificaciones en módulos ERP.

---

## 2. Hallazgos clave

### 2.1 Lo que NO debe modificarse

| Categoría | Alcance | Confianza |
|-----------|---------|-----------|
| **Módulos ERP completos** | Endpoints, services, queries, schemas (~290 archivos) | Alta |
| **Contratos Frontend** | JWT, session, REST paths, pagination, errors | Alta |
| **OpenAPI existente** | Sin breaking changes | Alta |
| **Global deps** | deps.py, deps_auth.py, org/inv/rbac_deps | Alta |
| **Lógica de workflow ERP** | INV procesos, PUR transaccional, etc. | Alta |
| **UnitOfWork** | Semántica commit/rollback | Alta |
| **Platform admin** (excl. onboarding internals) | Superadmin, modulos | Alta |
| **Tenant admin** | Users, RBAC, ORG | Alta |

### 2.2 Lo que debe evolucionar (existente)

| Componente | Motivo | Prioridad |
|------------|--------|-----------|
| `connection_async.py` | Resolución engine por tenant/modo | P0 |
| `routing.py` | Router multi-DB incompleto en operación | P0 |
| `queries_async.py` | Punto central de acceso a datos | P0 |
| `query_helpers.py` | Encapsular tenant filter | P0 |
| `cliente_onboarding_service.py` | Transacción cross-boundary AS-IS | P0 |
| `minimal_erp_tenant_bootstrap_service.py` | ERP seed en almacén incorrecto | P0 |
| `conexion_service.py` | Metadata dedicated no integrada en alta | P0 |
| `user_context.py`, `rol_service.py` | Ramas `database_type` en negocio | P1 |
| Bootstrap apply pipeline | DDL per dedicated store | P0 |
| `main.py` shutdown | Engine dispose | P1 |

### 2.3 Componentes nuevos esperados (conceptuales)

| Componente | Rol |
|------------|-----|
| **Provisioning Orchestrator** | Coordina saga de alta tenant |
| **Onboarding Saga Coordinator** | Estados, idempotencia, compensación |
| **Installation Metadata Registry** | Registro modo + almacén (extensión conexion) |
| **Dedicated Schema Applicator** | Pipeline V010 a almacenes nuevos |
| **Integration test harness dedicated** | Regresión multi-almacén |

**Nota:** Estos no duplican lógica ERP; orquestan infraestructura.

---

## 3. Estrategia de menor riesgo (Sección I)

### 3.1 Recomendación

**Infrastructure Encapsulation First** — Extender la resolución de conexión existente (`get_connection_for_tenant`) y el executor (`queries_async`) sin tocar ERP, priorizando regresión Shared en cada fase.

### 3.2 Por qué es la de menor riesgo

| Criterio | Evaluación |
|----------|------------|
| Modifica menos componentes | ~12–18 archivos vs ~300+ si se tocara ERP |
| Preserva contratos FE | JWT, session, REST unchanged |
| Preserva Shared | Default path idéntico a AS-IS |
| Reutiliza código | UoW, execute_*, middleware, IAM V2 |
| Sin forks | Single codebase |
| Incremental | Fases 0→6 del change surface |
| Rollback | Desactivar metadata dedicated → fallback Shared |

### 3.3 Alternativas descartadas (mayor riesgo)

| Alternativa | Por qué mayor riesgo |
|-------------|---------------------|
| Duplicar services ERP para dedicated | Fork, deuda permanente, viola G-04/G-06 |
| Nuevo middleware de routing | Cambio transversal innecesario |
| JWT con `database_type` claim | Rompe FE, acopla infra a auth |
| Dos executors `execute_*` | Duplicación, regresión Shared |
| Migrar ERP a Repository pattern | Refactor masivo sin beneficio |
| Dedicated primero, Shared después | Rompe principio backward first |

### 3.4 Preservación de inversión

| Inversión existente | Preservada |
|--------------------|------------|
| ~35 módulos ERP V4 | Sí — 100% |
| IAM V2 sessions | Sí — contrato intacto |
| Session scope ORG/INV | Sí |
| Paginación ORG/INV | Sí |
| Onboarding funcional Shared | Sí — externamente |
| Bootstrap v2 DDL/seeds | Sí — central; extensión dedicated |
| Tests unit ERP | Sí |
| Certificaciones FE auth | Sí |

### 3.5 Escalabilidad a largo plazo

La estrategia recomendada:

- Soporta **On-Premise / Cloud privada** vía nuevos modos en metadata (P7)
- No acumula deuda en ERP
- Concentra complejidad en provisioning (crecimiento lineal con modos, no exponencial con módulos)
- Permite migración Shared→Dedicated como fase separada (ADR-008)

---

## 4. Compatibilidad hacia atrás

| Dimensión | Veredicto |
|-----------|-----------|
| Tenants Shared existentes | **Sí** — sin cambio requerido |
| Frontend | **Sí** — transparency |
| OpenAPI | **Sí** — aditivo only |
| Endpoints | **Sí** |
| JWT | **Sí** |
| IAM/Session | **Sí** |
| Lógica ERP | **Sí** |
| Onboarding (externo) | **Sí** |
| Onboarding (interno) | **Parcial** — saga sin cambiar response |

**Nivel de compatibilidad esperado: 95%+** del contrato observable. El 5% restante es latencia dedicated, endpoints aditivos Platform, y estados Provisioning opcionales.

---

## 5. Riesgos críticos

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| R1 | Regresión Shared en refactor infra | Media | Crítico | Gate tests; fase 2 obligatoria |
| R2 | Onboarding saga mal compensada | Media | Crítico | Idempotencia; estados explícitos |
| R3 | Decisión sesiones IAM (ADR-002) incorrecta | Media | Alto | Cerrar P0 antes de implementar |
| R4 | Scope creep a módulos ERP | Alta | Alto | Guardrails G-01, G-04 |
| R5 | Frontend breaking change accidental | Baja | Crítico | OpenAPI diff CI |
| R6 | Engine cache stale post-migración | Media | Alto | Invalidación hook |
| R7 | Fork de código por presión delivery | Media | Crítico | ADR obligatorio G-11 |

### Decisiones que provocarían refactor innecesario

- Eliminar `cliente_id` de schema dedicated en ERP queries
- Duplicar onboarding por modo
- Introducir `DatabaseConnection.DEDICATED`
- Mover sesiones a almacén tenant sin ADR
- Refactor ERP a Repository pattern

### Decisiones que romperían Frontend

- Nuevos claims JWT obligatorios
- Cambiar paths `/auth/*`
- Cambiar envelope paginación
- Cambiar selection token flow
- Exponer errores de conexión SQL al cliente

### Decisiones que romperían Shared

- Cambiar default path single-DB
- Eliminar tenant filter en Shared
- Requerir `cliente_conexion` para todos los tenants
- Cambiar ADMIN semantics sin fallback

---

## 6. Estimación cualitativa de esfuerzo

| Fase | Esfuerzo | Dependencias |
|------|----------|--------------|
| Cierre P0 abiertos (Etapa 1) | 1–2 workshops | ADR-002, ADR-003, ADR-004 |
| Infra resolución (Capa 1–2) | **M** (1–2 semanas) | ADR aprobados |
| Regresión Shared gate | **S** (3–5 días) | Infra |
| Provisioning + onboarding saga | **L** (2–4 semanas) | Infra estable |
| Dedicated DDL pipeline | **L** (2–3 semanas) | Ops |
| Deuda multi cleanup | **S** (2–3 días) | Infra |
| Integration tests dedicated | **M** (1 semana) | Harness |
| Migración Shared→Dedicated | **XL** (fase separada) | MVP dedicated |

### Esfuerzo total MVP Dedicated (sin migración)

**Estimación: L–XL (6–10 semanas)** con 1–2 desarrolladores backend + arquitecto part-time, asumiendo ADRs P0 cerrados.

**Esfuerzo ERP: Nulo.** No cuenta en estimación.

---

## 7. Documentación entregada (Etapa 2)

| Documento | Contenido |
|-----------|-----------|
| [01_ARCHITECTURAL_IMPACT.md](./01_ARCHITECTURAL_IMPACT.md) | Inventario + impacto por componente |
| [02_PROTECTED_COMPONENTS.md](./02_PROTECTED_COMPONENTS.md) | Componentes que no deben modificarse |
| [03_CHANGE_SURFACE.md](./03_CHANGE_SURFACE.md) | Dónde concentrar cambios |
| [04_BACKWARD_COMPATIBILITY.md](./04_BACKWARD_COMPATIBILITY.md) | Evaluación compatibilidad |
| [05_IMPLEMENTATION_GUARDRAILS.md](./05_IMPLEMENTATION_GUARDRAILS.md) | 20 guardrails obligatorios |
| [06_IMPACT_MATRIX.md](./06_IMPACT_MATRIX.md) | Matriz completa |
| [07_EXECUTIVE_SUMMARY.md](./07_EXECUTIVE_SUMMARY.md) | Este documento |

---

## 8. Criterios de aprobación para avanzar a Etapa 3 (diseño técnico)

- [ ] Aprobación formal de este impact assessment
- [ ] ADR-001, 002, 004, 005 aprobados (Etapa 1)
- [ ] P0 open questions cerradas (`05_OPEN_QUESTIONS.md`)
- [ ] Acuerdo Producto: MVP = nuevos tenants dedicated only (sin migración)
- [ ] Acuerdo FE: sin cambios requeridos; endpoints aditivos OK
- [ ] Gate Shared regression definido en CI

---

## 9. Conclusión ejecutiva

La plataforma CAXIS ERP **puede evolucionar a híbrida Shared + Dedicated** con:

- **Cero cambios** en lógica ERP y contratos Frontend
- **Impacto concentrado** en ~12–18 archivos de infraestructura y onboarding
- **4–6 componentes nuevos** de orquestación (no duplicación)
- **Backward compatibility** preservada para todos los tenants Shared
- **Inversión existente** (~70% del codebase) completamente protegida

La estrategia de **Infrastructure Encapsulation First** es la de **menor riesgo**, **menor superficie de cambio**, y **mayor preservación de inversión**, alineada con los principios arquitectónicos de las Etapas 0 y 1.

**Recomendación:** Aprobar este análisis y proceder a cerrar ADRs P0 antes de cualquier implementación.

---

## 10. Próximo paso (fuera de alcance actual)

Etapa 3 — Diseño técnico de:

- Contrato de resolución de persistencia (sin implementar aún)
- Saga de onboarding (diagrama de estados)
- Política de sesiones IAM
- Pipeline DDL dedicated

**No iniciar Etapa 3 hasta aprobación de este documento.**
