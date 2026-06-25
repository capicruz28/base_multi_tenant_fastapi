# 05 — Guardrails de Implementación

**Etapa:** 2 — Architectural Impact Assessment  
**Fecha:** 2026-06-25  
**Estado:** Normativo para futuras etapas técnicas  
**Alcance:** Principios obligatorios — no implementación

---

## 1. Propósito

Definir **reglas inviolables** que toda futura implementación de Dedicated Database debe cumplir, derivadas del modelo conceptual (Etapa 1) y del análisis de impacto (Etapa 2).

Violación de un guardrail **P0** bloquea merge sin ADR de excepción aprobado.

---

## 2. Principios obligatorios

### G-01 — Mínimo impacto arquitectónico

**Regla:** Modificar la menor cantidad de componentes posible. Preferir extensión interna de infraestructura sobre cambios en ERP.

**Verificación:** PR diff no toca `modules/{erp}/` salvo excepción ADR.

**Prioridad:** P0

---

### G-02 — Backward Compatibility First

**Regla:** Ningún cambio puede regresionar tenants Shared existentes.

**Verificación:** CI incluye suite Shared regression; smoke staging Shared.

**Prioridad:** P0

---

### G-03 — Frontend Transparency

**Regla:** Frontend no debe requerir cambios para soportar Dedicated. Mismos endpoints, JWT, session flows.

**Verificación:** Checklist certificación auth FE; OpenAPI diff clean.

**Prioridad:** P0

---

### G-04 — Single Codebase

**Regla:** Un solo repositorio, un solo despliegue, una sola lógica de negocio. Prohibido fork, duplicate services, `*_dedicated.py`.

**Verificación:** Code review; grep por anti-patterns (`_shared`, `_dedicated`, `if dedicated` en ERP).

**Prioridad:** P0

---

### G-05 — Infrastructure Encapsulation

**Regla:** Toda diferencia Shared/Dedicated vive en capa de infraestructura de persistencia (Capa 1–2 del change surface).

**Verificación:** `database_type` no aparece en módulos ERP; desaparece de services IAM/RBAC.

**Prioridad:** P0

---

### G-06 — Zero Business Logic Duplication

**Regla:** Prohibido duplicar reglas de negocio, validaciones ERP, o workflows por modo de instalación.

**Verificación:** Review arquitectónico; análisis diff.

**Prioridad:** P0

---

### G-07 — OpenAPI Stability

**Regla:** Sin breaking changes en endpoints existentes: paths, methods, required fields, status codes.

**Verificación:** OpenAPI diff en CI; contrato FE.

**Prioridad:** P0

---

### G-08 — Domain Isolation

**Regla:** Platform no opera datos ERP. ERP no gobierna Platform. IAM es transversal sin acoplar a modo.

**Verificación:** Dependencias import; services ERP no importan `routing.py`.

**Prioridad:** P0

---

### G-09 — Connection Resolution Transparency

**Regla:** Services obtienen datos vía `execute_*` / UoW; nunca construyen connection strings ni eligen almacén.

**Verificación:** Grep `create_async_engine`, `get_db_connection` fuera de infra permitida.

**Prioridad:** P0

---

### G-10 — No `if(shared)` / `if(dedicated)` en lógica de negocio

**Regla:** Prohibido condicionar reglas de negocio por modo. Permitido solo en infraestructura encapsulada (lista blanca de archivos).

**Lista blanca infra:** `connection_async.py`, `routing.py`, `queries_async.py`, `query_helpers.py`, provisioning orchestrator (futuro).

**Prioridad:** P0

---

### G-11 — ADR obligatorio para cambios transversales

**Regla:** Cualquier cambio fuera de la superficie delimitada (`03_CHANGE_SURFACE.md`) o a componente protegido (`02_PROTECTED_COMPONENTS.md`) requiere ADR aprobado.

**Verificación:** Template ADR en PR; revisión arquitecto.

**Prioridad:** P0

---

## 3. Principios adicionales

### G-12 — Staged rollout

**Regla:** Dedicated habilitado por tenant via metadata/flag; Shared default global.

**Prioridad:** P1

---

### G-13 — Fail-safe to Shared

**Regla:** Si metadata de conexión falta o es inválida, fallback a Shared (comportamiento AS-IS) salvo tenant explícitamente marcado Dedicated.

**Prioridad:** P1 — evita romper tenants existentes.

---

### G-14 — Idempotent provisioning

**Regla:** Pasos de alta/migración deben ser reintentables sin duplicar recursos.

**Prioridad:** P1

---

### G-15 — Observability without exposure

**Regla:** Logs/metrics pueden incluir modo de instalación; responses API al cliente ERP no.

**Prioridad:** P1

---

### G-16 — Test pyramid preserved

**Regla:** Unit tests ERP no requieren DB dedicated. Integration dedicated es capa adicional, no reemplazo.

**Prioridad:** P1

---

### G-17 — No new global session patterns

**Regla:** No introducir `SessionLocal`, `scoped_session`, ni `Depends(get_db)` — preservar patrón async context manager existente.

**Prioridad:** P1

---

### G-18 — Preserve UoW semantics

**Regla:** UnitOfWork mantiene commit/rollback automático; no crear UoW alternativo por modo.

**Prioridad:** P1

---

### G-19 — Migration is explicit

**Regla:** Cambio Shared→Dedicated requiere estado `Migrando`, nunca automático silencioso.

**Prioridad:** P1

---

### G-20 — Security boundary unchanged

**Regla:** Aislamiento tenant, RBAC, query auditor, tenant filter — vigentes en ambos modos.

**Prioridad:** P0

---

## 4. Reglas de branching / PR

| Tipo de PR | Scope permitido | Review requerido |
|------------|-----------------|------------------|
| Infra resolución | Capa 1–2 | Arquitecto + 2 devs |
| Provisioning | Capa 3 tenant/ | Arquitecto |
| ERP feature | Sin cambios infra | Normal |
| IAM fix | Sin ramas multi nuevas | IAM owner |
| Deuda multi cleanup | user_context, rol_service | Arquitecto |

---

## 5. Anti-patterns explícitamente prohibidos

| Anti-pattern | Guardrail violado |
|--------------|-------------------|
| `execute_query_dedicated()` | G-04, G-06 |
| `DatabaseConnection.DEDICATED` enum | G-05 (metadata suficiente) |
| ERP service importa `routing` | G-08, G-09 |
| JWT claim `database_type` | G-03, G-10 |
| Response field `installation_mode` en ERP | G-03, G-07 |
| Copy-paste onboarding para dedicated | G-04, G-06 |
| Skip tenant filter en dedicated | G-20 |
| Two FastAPI apps | G-04 |
| Feature branch permanente `dedicated-db` | G-04 |

---

## 6. Checklist pre-merge (futuro)

```markdown
- [ ] G-01: Diff mínimo; ERP modules untouched
- [ ] G-02: Shared regression tests pass
- [ ] G-03: No JWT/session/schema breaking changes
- [ ] G-04: No *_dedicated / *_shared files
- [ ] G-05: database_type only in whitelist files
- [ ] G-07: OpenAPI diff reviewed
- [ ] G-10: No business if(shared/dedicated)
- [ ] G-11: ADR linked if touching protected components
- [ ] G-20: Tenant isolation tests pass
```

---

## 7. Escalación de excepciones

| Nivel | Quién aprueba |
|-------|---------------|
| Guardrail P1 violado | Tech lead + arquitecto |
| Guardrail P0 violado | Arquitecto principal + ADR |
| Componente protegido modificado | Arquitecto principal + evidencia FE |

---

## 8. Relación con documentos previos

| Documento | Relación |
|-----------|----------|
| `hybrid-platform/01_CONCEPTUAL_MODEL.md` | Principios P1–P7 → G-01–G-10 |
| `02_PROTECTED_COMPONENTS.md` | Lista protegida → G-11 |
| `03_CHANGE_SURFACE.md` | Whitelist infra → G-05, G-10 |
| `04_BACKWARD_COMPATIBILITY.md` | G-02, G-03 |
| `04_ARCHITECTURE_DECISIONS_DRAFT.md` | ADRs pendientes → G-11 |

---

## 9. Conclusión

Estos guardrails convierten el modelo conceptual en **criterios verificables**. Toda etapa técnica posterior debe demostrar cumplimiento antes de avanzar a producción Dedicated.

**Regla de oro:** Si un cambio no cabe en la superficie delimitada y no tiene ADR, **no se implementa**.
