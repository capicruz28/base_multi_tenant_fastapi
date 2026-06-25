# 11 — Failure Recovery

**Etapa:** 5 — Technical Infrastructure Design  
**Fecha:** 2026-06-25  
**Estado:** Borrador para revisión  
**Prerequisitos:** E4 RD-13, 07_TRANSACTION_BOUNDARIES, runtime risks  
**Restricción:** Estrategias de recuperación conceptual. Sin implementación saga.

---

## 1. Propósito

Definir cómo la infraestructura **detecta, contiene, recupera y compensa** fallos en resolución, conexión, ejecución y operaciones cross-plane.

---

## 2. Taxonomía de fallos

| Categoría | Ejemplos |
|-----------|----------|
| **F1 — Resolution** | Metadata missing, wrong mode, stale cache |
| **F2 — Connection** | Pool timeout, auth failure, network |
| **F3 — Execution** | SQL error, deadlock, constraint violation |
| **F4 — Boundary** | Partial saga step, post-commit side effect fail |
| **F5 — Lifecycle** | Migration interrupted, provisioning stuck |
| **F6 — Security** | Tenant leak attempt, auditor block |

---

## 3. F1 — Resolution failures

| Fallo | Detección | Respuesta inmediata | Recovery |
|-------|-----------|---------------------|----------|
| Metadata missing + shared legacy | Lookup empty | Fallback shared (RD-08) | Ops: backfill metadata |
| Metadata missing + dedicated | Lookup empty | Error 503/500 mapeado | Ops: fix cliente_conexion |
| Stale cache post-migration | Wrong data returned | Fail on validation; alert | Invalidate L-B + L-C |
| Tenant Migrando | State check | Block ERP 503 | Complete migration ops |
| Tenant Provisioning | State check | Limited ops | Resume saga |

**No retry automático** resolution en mismo request excepto 1 retry transiente CP lookup (opcional TD-10).

---

## 4. F2 — Connection failures

| Fallo | Respuesta | Recovery |
|-------|-----------|----------|
| Pool timeout | Error mapeado; métrica | Scale pool; investigate load |
| Auth failure dedicated | Error; alert ops | Rotate credentials; invalidate cache |
| Server unreachable | Error 503 | Failover DR (futuro); manual ops |
| pool_pre_ping failure | Recreate connection | Automatic SQLAlchemy |
| Engine disposed mid-request | Error | Client retry idempotent GET |

**Dedicated unreachable:** tenant puede transicionar a Suspendido automático (policy ops).

---

## 5. F3 — Execution failures

| Fallo | Mapeo HTTP | Recovery |
|-------|------------|----------|
| UNIQUE constraint | 409 ConflictError | User correction |
| FK violation | 422 ValidationError | User correction |
| Deadlock | 409/503 retry-safe | Client retry |
| Timeout query | 504/503 | Optimize query; index |
| Tenant filter auditor block | 500 internal — **fail closed** | Fix query |

**Regla:** Nunca exponer mensaje SQL Server raw al cliente (guardrail existente).

---

## 6. F4 — Saga / cross-plane failures

### 6.1 Onboarding saga (RD-12)

| Step fallido | Estado tenant | Compensación |
|--------------|---------------|--------------|
| 1 — Registry CP | Provisioning failed | Delete registry si orphan |
| 2 — DDL dedicated | Provisioning failed | Drop DB if created; registry Provisioning |
| 3 — Seed DP | Provisioning failed | Mark error; manual cleanup |
| 4 — Activate | Partial | Idempotent retry activate |

**MVP:** compensación **semi-automática** — ops dashboard (O-E5-04).

### 6.2 Post-commit side effect failure

| Escenario | Ejemplo | Recovery |
|-----------|---------|----------|
| SQL committed, Redis fail | Session bridge | Reconciliation job; user re-login |
| SQL committed, email fail | Notification | Retry queue |

**Patrón:** outbox deferred (O-E5-05).

---

## 7. F5 — Migration failures (RD-13)

| Fase | Fallo | Recovery |
|------|-------|----------|
| Copy data | Incomplete | Tenant stays Migrando; rollback copy |
| Cutover | Metadata update fail | Revert route; extend Migrando |
| Post-cutover | Validation fail | Rollback to shared (manual); RI-14 |

**MVP:** offline migration — no dual-write recovery complexity.

---

## 8. F6 — Security failures

| Evento | Respuesta |
|--------|-----------|
| Tenant filter miss detected | Block query; alert security |
| Cross-tenant data in result | Fail request; audit |
| Wrong dedicated route | Fail closed dedicated (RI-39) |

---

## 9. Failover (extensiones futuras)

| Escenario | Strategy |
|-----------|----------|
| CP store primary down | Read-only degrade; no new tenants |
| Dedicated tenant DB down | Tenant Suspendido; 503 tenant-scoped |
| Multi-Region DR | Metadata secondary endpoint; manual/automatic failover |
| On-Premise link down | Queue requests; tenant notification |

**No diseñar** automatic failover MVP.

---

## 10. Retry policy (client / infra)

| Operación | Idempotent retry |
|-----------|------------------|
| GET | Sí |
| POST create | Solo con idempotency key |
| UoW process | No — require business retry |
| Refresh token | Sí (limited) |
| Migration step | Ops-only |

---

## 11. Observability for recovery

| Signal | Uso |
|--------|-----|
| `resolution_failure_total` | F1 |
| `connection_error_total` by engine_key | F2 |
| `saga_step_failure` by step | F4 |
| `tenant_state_provisioning_stuck` | F5 |
| `security_auditor_block_total` | F6 |

Runbooks ops vinculados en Etapa 6 implementación.

---

## 12. Deadlock conceptual prevention

| Riesgo | Mitigación |
|--------|------------|
| UoW largo + external IO | TB-06 UoW corto |
| Cross-plane single TX | Eliminar — saga |
| Migration + live ERP | Block ERP RD-13 |
| Engine dispose during active session | Dispose solo idle engines |

---

## 13. Conclusión

Failure Recovery prioriza **fail-closed** en seguridad y dedicated routing, **fallback shared** solo legacy, y **saga compensation** semi-automática para onboarding. Automatic DR failover es extensión futura.

Documentos relacionados: `07_TRANSACTION_BOUNDARIES`, `12_IMPLEMENTATION_ROADMAP`.
