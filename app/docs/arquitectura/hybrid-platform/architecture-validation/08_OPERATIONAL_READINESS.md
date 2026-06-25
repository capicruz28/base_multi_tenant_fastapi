# 08 — Operational Readiness

**Etapa:** 5.5 — Architecture Validation  
**Fecha:** 2026-06-25  
**Alcance:** Preparación operacional SRE/ops para híbrido

---

## 1. Propósito

Evaluar si existen diseños operacionales suficientes para operar Shared + Dedicated en producción.

---

## 2. Evaluación por área

### 2.1 Monitoreo

| Aspecto | Diseño E5 | Gap |
|---------|-----------|-----|
| Engine metrics | ✅ 04 §8 | No dashboard spec |
| Cache hit ratio | ✅ 10 §8 | No thresholds prod |
| Resolution failures | ✅ 11 §11 | No runbook |
| Per-tenant dedicated health | ⚠️ Q-060 | **No diseñado** |
| Pool saturation | ✅ | — |

**Score: 55%** — Métricas listadas; **observability platform no especificada**.

---

### 2.2 Logs

| Aspecto | Diseño | Gap |
|---------|--------|-----|
| Installation mode in logs | ✅ G-15 | — |
| No secrets in logs | ✅ 02 TR-04 | — |
| Correlation request/tenant | ⚠️ E4 Request Context | No log schema |
| Saga step logging | ⚠️ | No format |

**Score: 60%**

---

### 2.3 Observabilidad

| Aspecto | Preparación |
|---------|-------------|
| Distributed tracing | ❌ No mencionado |
| Tenant-scoped dashboards | ❌ |
| Provisioning funnel | ❌ |
| Migration progress | ❌ |

**Score: 35%**

---

### 2.4 Runbooks

| Runbook | E5 referencia | Existe |
|---------|---------------|--------|
| Wrong dedicated route | 11 F1 | ❌ |
| Migration cutover | F7, RD-13 | ❌ |
| Provisioning stuck | TD-12 | ❌ |
| Credential rotation | 02 §7.3 | ❌ |
| Engine dispose all | 04 | ❌ |
| Tenant Suspendido | E4 lifecycle | ❌ |

**Score: 20%** — Failure recovery **conceptual**; runbooks **no producidos**.

---

### 2.5 Provisioning

| Aspecto | Preparación |
|---------|-------------|
| Saga states | ⚠️ Behavioral |
| DDL pipeline Q-061 | ❌ Abierta |
| Dedicated async UX Q-033 | ❌ |
| Idempotency | ⚠️ |
| Pool pre-created Q-034 | ❌ P2 |

**Score: 40%**

---

### 2.6 Rollback

| Escenario | Preparación |
|-----------|-------------|
| Fase 1 code rollback | ✅ Standard deploy |
| Migration rollback | ⚠️ Manual 11 §7 |
| Provisioning compensate | ⚠️ Semi-auto |
| Feature flag dedicated off | ✅ IR-05 |

**Score: 50%**

---

### 2.7 Recovery

| Escenario | Preparación |
|-----------|-------------|
| CP unavailable | ⚠️ Fail hard |
| Dedicated DB down | ⚠️ Suspend tenant policy |
| Redis loss | ⚠️ Q-011 |
| Partial saga | ⚠️ 11 §6 |

**Score: 45%**

---

### 2.8 Deploy

| Aspecto | Preparación |
|---------|-------------|
| Rolling deploy multi-worker | ⚠️ TD-09 cache stale |
| Schema migration shared | ✅ bootstrap_v2 |
| Schema migration dedicated N | ❌ Q-061 |
| Zero-downtime dedicated enable | ❌ |

**Score: 45%**

---

### 2.9 Health Checks

| Check | E4 RD-14 | Preparación |
|-------|----------|-------------|
| Liveness | ✅ | AS-IS /health |
| DB ping optional | ✅ | Exists |
| Per-tenant dedicated probe | ❌ | Q-060 |
| CP + sample dedicated | ❌ | |

**Score: 50%** — MVP health OK; **not sufficient for N dedicated**.

---

### 2.10 Métricas & Alertas

| Métrica | Alerta definida |
|---------|-----------------|
| resolution_failure_total | ❌ |
| engine_dispose_rate spike | ❌ |
| pool_overflow | ❌ |
| tenant_provisioning_stuck | ❌ |
| metadata_cache_stale_serving | ❌ |

**Score: 25%**

---

## 3. Scorecard operacional global

| Área | Score |
|------|-------|
| Monitoreo | 55% |
| Logs | 60% |
| Observabilidad | 35% |
| Runbooks | 20% |
| Provisioning ops | 40% |
| Rollback | 50% |
| Recovery | 45% |
| Deploy | 45% |
| Health | 50% |
| Alertas | 25% |
| **Promedio** | **42%** |

---

## 4. Bloqueantes operacionales pre-dedicated prod

| # | Bloqueante |
|---|------------|
| 1 | Runbook migration cutover |
| 2 | DDL pipeline dedicated (Q-061) |
| 3 | Dashboard provisioning states |
| 4 | Alerting wrong-route / isolation breach |
| 5 | Per-tenant dedicated health strategy |
| 6 | Credential rotation procedure |

---

## 5. Adecuado para F0–F3

Operaciones **shared-only infra changes** requieren solo:
- Métricas baseline F0
- Shared regression CI
- Rollback deploy estándar

**Score F0–F3 ops: 70%** — Suficiente con monitoring básico existente.

---

## 6. Conclusión

Preparación operacional **insuficiente para dedicated production** (42%). **Suficiente para iniciar implementación infra** en entornos dev/staging shared. Runbooks y alerting deben ser **entregables paralelos F4–F6**, no afterthought.
