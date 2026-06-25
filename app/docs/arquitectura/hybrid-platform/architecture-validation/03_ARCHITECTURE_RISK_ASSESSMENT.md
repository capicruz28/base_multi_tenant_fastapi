# 03 — Architecture Risk Assessment

**Etapa:** 5.5 — Architecture Validation  
**Fecha:** 2026-06-25  
**Metodología:** Evaluación adversarial post-diseño E0–E5

---

## 1. Propósito

Evaluación crítica consolidada. Clasificación: Critical / High / Medium / Low.

---

## 2. Riesgos Critical

### AR-C01 — Session store sin decisión (RD-11)

| Campo | Valor |
|-------|-------|
| Descripción | Ubicación persistencia sesiones IAM no cerrada; ADR-002 pendiente |
| Impacto | Login/refresh/probe/revocación inconsistentes en dedicated |
| Probabilidad | **Alta** — bloqueante si se implementa dedicated sin ADR |
| Mitigación diseño | TD-13 gate Fase 5; cerrar ADR-002 antes dedicated prod |
| Estado | **Abierto** |

---

### AR-C02 — Wrong route dedicated → shared data

| Campo | Valor |
|-------|-------|
| Descripción | Cache stale o fallback incorrecto expone datos cross-tenant |
| Impacto | Violación aislamiento; compliance; RI-39 |
| Probabilidad | Media en migración; Baja steady-state |
| Mitigación | Fail-closed dedicated; invalidación L-B+L-C; TD-08 defensive filter |
| Estado | Mitigado en diseño; **requiere tests F0** |

---

### AR-C03 — Onboarding single-TX AS-IS en producción

| Campo | Valor |
|-------|-------|
| Descripción | Código actual mezcla CP+DP; dedicated imposible sin saga |
| Impacto | Alta dedicated falla o corrupción datos |
| Probabilidad | **Alta** si se activa dedicated antes Fase 4 |
| Mitigación | Fase 4 obligatoria; feature flag dedicated |
| Estado | Conocido; no mitigado en código |

---

### AR-C04 — Tenant filter miss en shared

| Campo | Valor |
|-------|-------|
| Descripción | Query sin filter en almacén compartido |
| Impacto | Data leak entre tenants |
| Probabilidad | Baja con auditor; Media en queries nuevas |
| Mitigación | QueryAuditor; G-20; tests isolation |
| Estado | Vigente AS-IS |

---

### AR-C05 — Impersonation context incorrecto

| Campo | Valor |
|-------|-------|
| Descripción | Módulos ERP sin `{cod}_deps` usan `current_user.cliente_id` |
| Impacto | Datos tenant incorrecto bajo impersonation |
| Probabilidad | **Alta** en módulos sin deps (E0 R-I03) |
| Mitigación | **No en roadmap E5** — gap |
| Estado | **Abierto — no trazado** |

---

## 3. Riesgos High

### AR-H01 — Catálogos CP inaccesibles en dedicated

| Campo | Valor |
|-------|-------|
| Descripción | GLOBAL_TABLES asume catálogos en tenant store; E3 los clasifica CP |
| Impacto | ERP queries fallan o retornan vacío |
| Probabilidad | **Alta** primer dedicated tenant |
| Mitigación | Réplica catálogos en provisioning O ruta CP read — **no diseñado** |
| Estado | **Abierto** |

---

### AR-H02 — Multi-worker metadata stale post-migration

| Campo | Valor |
|-------|-------|
| Descripción | TD-09 acepta eventual consistency |
| Impacto | Requests a worker con cache viejo post-cutover |
| Probabilidad | Media en deploy rolling |
| Mitigación | TTL corto migración; flush manual; pub/sub F8 |
| Estado | Parcialmente mitigado |

---

### AR-H03 — Engine pool exhaustion (N dedicated)

| Campo | Valor |
|-------|-------|
| Descripción | Un engine/pool por tenant dedicated por worker |
| Impacto | OOM, connection limits, latency |
| Probabilidad | Alta >50 dedicated/worker |
| Mitigación | Max engines limit; LRU dispose; horizontal scale |
| Estado | Documentado; no dimensionado |

---

### AR-H04 — Saga onboarding partial failure

| Campo | Valor |
|-------|-------|
| Descripción | TD-12 semi-auto; compensación incompleta |
| Impacto | Tenants huérfanos Provisioning |
| Probabilidad | Media |
| Mitigación | Runbooks; dashboard state; idempotency |
| Estado | Parcial |

---

### AR-H05 — Permission resolution cross-plane

| Campo | Valor |
|-------|-------|
| Descripción | Catálogo CP + grants DP sin servicio técnico detallado |
| Impacto | RBAC incorrecto o latencia |
| Probabilidad | Media dedicated |
| Mitigación | RD-15 L4 pre-compute; cache Redis |
| Estado | Behavioral only |

---

### AR-H06 — IAM/database_type branches L5

| Campo | Valor |
|-------|-------|
| Descripción | Violación RI-32 en código AS-IS |
| Impacto | Comportamiento heterogéneo dedicated |
| Probabilidad | Alta si Fase 3 retrasa |
| Mitigación | Fase 3; grep gate |
| Estado | Mitigación planificada F3 |

---

### AR-H07 — Redis loss / desync

| Campo | Valor |
|-------|-------|
| Descripción | Q-011 abierta — Redis acelerador vs SoT |
| Impacto | Tokens revocados aceptados; session bridge fail |
| Probabilidad | Baja evento; Alto impacto |
| Mitigación | Fail-closed blacklist; persistencia SQL authoritative |
| Estado | Parcial AS-IS |

---

## 4. Riesgos Medium

| ID | Descripción | Prob | Impacto | Mitigación | Estado |
|----|-------------|------|---------|------------|--------|
| AR-M01 | N sessions/request performance | Alta | Medio | UoW; pool tune | AS-IS |
| AR-M02 | Repository bypass auditor | Media | Alto | Audit repos F? | Abierto |
| AR-M03 | auth_audit_log hybrid routing | Media | Medio | Decisión operation class | Abierto |
| AR-M04 | Async engine no shutdown | Alta | Bajo | Fase 1 fix | Planificado |
| AR-M05 | ADR borrador sin aprobación formal | Alta | Medio | Acta aprobación | Proceso |
| AR-M06 | Schema version drift dedicated | Media | Alto | Q-053 abierta | Abierto |
| AR-M07 | Sequence race concurrent | Media | Alto | Locking INV pattern | AS-IS ERP |
| AR-M08 | Noisy neighbor shared | Media | Medio | Scale shared DB | Ops |

---

## 5. Riesgos Low

| ID | Descripción | Estado |
|----|-------------|--------|
| AR-L01 | DatabaseConnection enum duplicado deprecated | Deuda menor |
| AR-L02 | sessionmaker recreado cada open | Performance minor |
| AR-L03 | SQL Server version cache | Edge case |
| AR-L04 | On-premise extensibility | P3 future |

---

## 6. Matriz probabilidad × impacto

```
Impacto →
         Critical    High      Medium    Low
Prob ↓
Alta     C03,C05     H01,H06   M01,M04   
Media    C02         H02-H05   M02-M08   
Baja     C04         H07       L01-L04   
```

---

## 7. Riesgos por intentar "romper" la arquitectura

| Escenario ataque | ¿Se rompe? | Evidencia |
|------------------|------------|-----------|
| Tenant A token en Host B | Parcialmente mitigado | RI-17; refresh RD-04 |
| Dedicated tenant forced shared via cache | Mitigado fail-closed | RI-39 |
| ERP service imports routing | Prohibido G-09; no enforced aún | Grep CI needed |
| Skip tenant filter dedicated "safe" | **Riesgo** — TD-08 mantiene filter | Defense depth |
| 1000 dedicated one worker | **Se rompe** | AR-H03 |
| Migration + live ERP | Mitigado RD-13 | Block ERP |
| Onboarding double-click | Parcial | RR-41; idempotency TBD |
| Superadmin reads tenant without audit | **Riesgo** | RR-12; gate exists? verify impl |

---

## 8. Resumen por severidad

| Severidad | Count | Abiertos |
|-----------|-------|----------|
| Critical | 5 | 3 |
| High | 7 | 4 |
| Medium | 8 | 5 |
| Low | 4 | 4 |

---

## 9. Conclusión

El diseño **mitiga bien** riesgos de encapsulación infra y regresión shared. Permanece **exposición critical** en session store (AR-C01), catálogos dedicated (AR-H01), impersonation deps (AR-C05), y orden implementación vs activación dedicated (AR-C03).
