# 08 — Query Execution Model

**Etapa:** 5 — Technical Infrastructure Design  
**Fecha:** 2026-06-25  
**Estado:** Borrador para revisión  
**Prerequisitos:** AS-IS queries_async, G-09, G-20, E4 RI-40  
**Restricción:** Modelo de ejecución queries. Sin código.

---

## 1. Propósito

Especificar el **pipeline técnico de ejecución de queries** SQLAlchemy Core como vía principal del Persistence Gateway hacia Tenant Data Store y Control Plane Store.

---

## 2. Punto central AS-IS

**Archivo:** `app/infrastructure/database/queries_async.py`

Funciones públicas:

| Función | Rol |
|---------|-----|
| `execute_query` | SELECT y mutaciones detectadas |
| `execute_insert` | INSERT con commit |
| `execute_update` | UPDATE con commit |

**153+ archivos queries** en `infrastructure/database/queries/{cod}/` consumen estas funciones — **superficie protegida E2**.

---

## 3. Pipeline de ejecución

```
Caller (service → query function)
  → [1] Invocar execute_* con query + params
  → [2] Resolver client_id (param > ContextVar)
  → [3] Clasificar operation_class (DEFAULT→tenant_data, ADMIN→control_plane)
  → [4] apply_tenant_filter (si tenant_data + tabla no global)
  → [5] QueryAuditor (producción)
  → [6] Connection Resolution → Session open
  → [7] session.execute(query)
  → [8] Map results (SELECT → list[dict])
  → [9] Commit if mutation / skip if SELECT
  → [10] Session close
  → Return
```

---

## 4. Tenant filter policy

**Archivo AS-IS:** `query_helpers.py`

| Condición | Acción |
|-----------|--------|
| Tabla en GLOBAL_TABLES whitelist | Skip filter |
| `skip_tenant_validation=True` | Skip (scripts only) |
| tenant_data + shared | Enforce `cliente_id` filter |
| tenant_data + dedicated | Policy encapsulada — filter aplicado por contrato defensivo |
| control_plane | Skip tenant filter |
| ALLOW_TENANT_FILTER_BYPASS env | Solo non-prod scripts |

**Decisión TD-08:** Mantener tenant filter en shared **siempre**. En dedicated, filter defensivo no sustituye aislamiento físico pero previene regresiones si route incorrecto.

---

## 5. GLOBAL_TABLES y dedicated

| Aspecto | Regla |
|---------|-------|
| Tablas catálogo CP en GLOBAL_TABLES | No accedidas vía tenant_data path |
| Tablas ERP | Nunca en GLOBAL_TABLES |
| Dedicated tenant | GLOBAL_TABLES list **revisada** — catálogos solo vía control_plane |

**Gap:** Algunos catálogos hoy en shared físico accesibles sin filter — clasificar en E3 antes de implementar.

---

## 6. Query Auditor

**Archivo:** `query_auditor.py`

| Regla producción | Propósito |
|------------------|-----------|
| Detectar SELECT sin tenant filter | Prevenir leak shared |
| Detectar bypass no autorizado | Seguridad |
| Dedicated | Mismas reglas — defense in depth |

Auditor opera **antes** de execute — no sustituye filter.

---

## 7. Parámetros de invocación

| Parámetro | Semántica |
|-----------|-----------|
| `query` | SQLAlchemy Core construct |
| `client_id` | Override tenant explícito (impersonation-safe services) |
| `connection_type` | ADMIN \| DEFAULT |
| `skip_tenant_validation` | Bypass filter — restringido |
| `connection_metadata` | Optimización skip metadata lookup |

**Firma pública:** **inmutable** (G-07, E2 protected).

---

## 8. Result mapping

| Tipo query | Resultado |
|------------|-----------|
| SELECT | `list[dict]` — column keys from Result |
| INSERT returning | dict o list según query |
| UPDATE/DELETE | rowcount vía execute_* |

Sin ORM entities — Core-only pattern preserved.

---

## 9. Performance considerations

| Patrón | Estado | Recomendación |
|--------|--------|---------------|
| N execute_* por endpoint | AS-IS común | UoW donde atomicidad requerida |
| Batch queries | Queries layer JOINs | Sin cambio |
| Metadata lookup per execute | Mitigado L-A cache | TD-02 TTL |
| Connection checkout per execute | AS-IS | Monitorear pool metrics |

**No introducir** batch execute API en MVP.

---

## 10. Queries layer (153 files)

| Regla | Descripción |
|-------|-------------|
| QL-01 | Queries viven en `infrastructure/database/queries/{cod}/` |
| QL-02 | Queries **no** resuelven conexión |
| QL-03 | Queries reciben params; services pasan client_id |
| QL-04 | **Cero cambios** queries ERP para dedicated MVP |
| QL-05 | Nuevo código queries usa execute_* exclusivamente |

---

## 11. Dedicated execution path

```
execute_query(..., client_id=tenant_x)
  → metadata: dedicated
  → engine: tenant_x dedicated
  → tenant filter: defensive cliente_id
  → same SQL query text
  → same result shape
```

**Verificación:** Integration test dedicated debe producir mismos contratos que shared.

---

## 12. Gap AS-IS

| ID | Gap |
|----|-----|
| QE-G01 | execute_query auto-commit mutaciones sorpresa en callers |
| QE-G02 | auth_audit_log routing híbrido en services |
| QE-G03 | GLOBAL_TABLES puede incluir tablas mal clasificadas |
| QE-G04 | Query auditor rules pueden necesitar ajuste dedicated |

---

## 13. Conclusión

Query Execution Model preserva **execute_* como API estable** con pipeline enriquecido internamente para metadata resolution. Queries ERP permanecen untouched.

Documentos relacionados: `01_PERSISTENCE_GATEWAY`, `09_REPOSITORY_INTERACTION`, `03_CONNECTION_RESOLUTION`.
