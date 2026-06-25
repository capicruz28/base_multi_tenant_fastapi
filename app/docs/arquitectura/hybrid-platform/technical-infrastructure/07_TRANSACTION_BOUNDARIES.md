# 07 — Transaction Boundaries

**Etapa:** 5 — Technical Infrastructure Design  
**Fecha:** 2026-06-25  
**Estado:** Borrador para revisión  
**Prerequisitos:** E3 lifecycle, RD-12, AS-IS SQLAlchemy audit  
**Restricción:** Fronteras transaccionales conceptuales. Sin SQL ni pseudocódigo.

---

## 1. Propósito

Definir **dónde empiezan y terminan** las transacciones SQL, qué garantías ACID aplican, y cómo se manejan operaciones que cruzan planos o almacenes.

---

## 2. Tipos de boundary

| Tipo | Scope ACID | Mecanismo |
|------|------------|-----------|
| **T1 — Operación atómica** | Una sentencia / execute_* | Auto-commit mutación |
| **T2 — Unit of Work** | Múltiples sentencias, un almacén | Commit al exit UoW |
| **T3 — Explicit begin** | Caller-controlled | session.begin() onboarding |
| **T4 — Saga step** | Un paso lógico = 1..n T1/T2/T3 | Coordinación externa |
| **T5 — Cross-plane compuesto** | **No ACID global MVP** | Secuencia saga |

---

## 3. Matriz de boundaries AS-IS

| Mecanismo | SELECT | Mutación | Error | ACID |
|-----------|--------|----------|-------|------|
| execute_query SELECT | Sin commit | — | Rollback | N/A |
| execute_query mutación | — | Commit inmediato | Rollback | Single-op |
| execute_insert/update | — | Commit inmediato | Rollback | Single-op |
| get_db_connection raw | Sin commit default | Caller commit | Rollback | Caller-defined |
| UnitOfWork | Sin commit intermedio | Commit exit | Rollback exit | Multi-op |
| session.begin() onboarding | — | Commit exit begin | Rollback auto | Block scope |

---

## 4. Reglas normativas

| ID | Regla |
|----|-------|
| TB-01 | Toda mutación tenant_data pasa por gateway con boundary explícito |
| TB-02 | Prohibido commit parcial silencioso en procesos multi-paso ERP |
| TB-03 | SELECT nunca inicia transacción implícita durable |
| TB-04 | Side effects externos (Redis, email) **fuera** boundary SQL |
| TB-05 | Cross-plane requiere saga — no distributed transaction MVP |
| TB-06 | Migración Shared→Dedicated no usa transacción única cross-store |
| TB-07 | Dedicated provisioning DDL es boundary separado de seed data |

---

## 5. Boundaries por dominio

### 5.1 ERP transaccional (INV, PUR)

```
Boundary T2 (UoW):
  cabecera INSERT + detalle INSERT(s) + stock effects
  → commit único
  → post-commit: auditoría async si aplica
```

### 5.2 IAM Session V2

```
Boundary T2 (UoW):
  user_session + refresh_token + token_family
  → commit único
  → post-commit: Redis bridge
```

### 5.3 Onboarding AS-IS (problemático)

```
Boundary T3 actual:
  CP writes + DP seed en single session ADMIN
  → Violación TB-05
```

### 5.3 Onboarding canónico (target)

```
Saga T5:
  Step 1 (T2 CP): Tenant Registry + metadata
  Step 2 (T4): Dedicated DDL apply (ops)
  Step 3 (T2 DP): Seed ERP en tenant store resuelto
  Step 4 (T2 CP): Provisioning state = Activo
  → Compensación por step fallido
```

### 5.4 Platform read-only

```
Boundary T1:
  execute_query SELECT control_plane
  → sin transacción durable
```

---

## 6. Aislamiento y locking

| Escenario | Policy |
|-----------|--------|
| Procesos concurrentes misma entidad ERP | Locking row-level (UPDLOCK AS-IS INV) |
| Concurrent onboarding mismo subdominio | Unique constraint + idempotency key |
| Migración + ERP | ERP bloqueado (RD-13) — no concurrent boundary |
| Dos requests mismo tenant dedicated | SQL Server default isolation |

**No diseñar** niveles aislamiento custom en MVP.

---

## 7. Idempotencia en boundaries saga

| Step saga | Idempotency |
|-----------|-------------|
| Create tenant registry | subdominio unique |
| Apply DDL dedicated | schema version marker |
| Seed ERP | tenant_id + step marker table |
| Activate tenant | state transition guard |

Detalle compensación: `11_FAILURE_RECOVERY.md`.

---

## 8. Boundaries Shared vs Dedicated

| Aspecto | Shared | Dedicated |
|---------|--------|-----------|
| ACID scope | Igual — single SQL Server | Igual — tenant SQL Server |
| Tenant filter | Enforced en shared | Encapsulado L6 |
| Cross-tenant leak | Riesgo filter miss | Riesgo wrong route |
| UoW | Mismo boundary T2 | Mismo boundary T2 |

**Invariante:** Boundary type no depende de installation mode.

---

## 9. Anti-patterns prohibidos

| Anti-pattern | Violación |
|--------------|-----------|
| Distributed 2PC SQL Server cross-store | TB-05 |
| execute_* loop sin UoW en proceso multi-paso | TB-02 |
| Redis write antes commit SQL | TB-04 |
| Onboarding single TX CP+DP | TB-05 |
| Long-running transaction (>30s) | Performance / deadlock |

---

## 10. Preguntas abiertas

| ID | Pregunta |
|----|----------|
| O-E5-04 | ¿Compensation onboarding automática o manual ops MVP? |
| O-E5-05 | ¿Outbox pattern para post-commit events? |

---

## 11. Conclusión

Transaction Boundaries preservan **ACID local por almacén**. Cross-plane operations migran a **saga multi-step** con boundaries T1–T3 por paso. El onboarding AS-IS single-TX es deuda crítica documentada.

Documentos relacionados: `06_UNIT_OF_WORK_DESIGN`, `11_FAILURE_RECOVERY`, `12_IMPLEMENTATION_ROADMAP`.
