# 07 — Scalability Review

**Etapa:** 5.5 — Architecture Validation  
**Fecha:** 2026-06-25  
**Restricción:** Evaluación de preparación — sin diseñar soluciones

---

## 1. Propósito

Evaluar si la arquitectura E0–E5 soporta escalabilidad operativa y crecimiento tenant. Escala evaluada: 10 / 100 / 500 / 1000 tenants.

---

## 2. Dimensiones evaluadas

| Dimensión | Shared | Dedicated |
|-----------|--------|-----------|
| Routing metadata | CP lookup + cache | CP + engine per tenant |
| Data isolation | Logical filter | Physical |
| Connection pools | Shared pool | N pools |
| ERP queries | Unchanged | Unchanged |
| Session IAM | TBD RD-11 | TBD |

---

## 3. Shared Database

| Escala | ¿Soportada? | Riesgos | Preparación |
|--------|-------------|---------|-------------|
| **10 tenants** | ✅ Sí | Ninguno significativo | AS-IS operativo |
| **100 tenants** | ✅ Sí | Noisy neighbor AR-M08 | Pool tune; index |
| **500 tenants** | ⚠️ Con tuning | Shared DB size; backup window; CP metadata cache | Monitoreo; partición futura |
| **1000 tenants** | ⚠️ Límite práctico | Single DB bottleneck; migration blast radius | **No diseñado** sharding shared |

**Veredicto Shared:** Arquitectura **adecuada hasta ~500 tenants** en single shared SQL Server con ops maduras. 1000+ requiere **estrategia sharding** no documentada.

---

## 4. Dedicated Database

| Escala dedicated | Workers × engines | ¿Soportada? | Riesgos |
|------------------|-------------------|-------------|---------|
| **10** | ~10 engines/worker | ✅ Sí | Bajo |
| **100** | ~100 engines/worker | ⚠️ | AR-H03 pool exhaustion; memory |
| **500** | Impracticable 1 worker | ❌ | OOM; connection limits |
| **1000** | — | ❌ | Requiere arquitectura workers dedicada / engine LRU |

**Veredicto Dedicated:** Diseño **viable hasta ~50–100 dedicated tenants por cluster workers** con límites TD-04 y max engines. **500–1000 dedicated NO preparado** sin:
- Horizontal scaling agresivo
- Engine LRU / lazy dispose
- Posible worker pools por tenant tier

**Gap crítico:** E5 menciona max engines configurable pero **no dimensionamiento** ni modelo económico infra.

---

## 5. Mix Shared + Dedicated

| Mix | Preparación |
|-----|-------------|
| 950 shared + 50 dedicated | ✅ Target MVP |
| 800 shared + 200 dedicated | ⚠️ Engine pressure |
| 500 shared + 500 dedicated | ❌ Requiere redisign engine policy |

Gateway encapsulation **facilita mix** — el límite es **operacional**, no arquitectónico de L5.

---

## 6. Migraciones Shared → Dedicated

| Aspecto | Preparación |
|---------|-------------|
| Offline block ERP RD-13 | ✅ Diseñado |
| Online dual-write | ❌ Explícitamente fuera MVP |
| 100 concurrent migrations | ❌ No diseñado |
| Rollback | ⚠️ Manual runbooks |
| Data volume TB | ❌ No evaluado |

**Veredicto:** **1–5 migraciones simultáneas** viables con ops manual. Escala migration factory **no preparada**.

---

## 7. Read Replicas

| Aspecto | Preparación |
|---------|-------------|
| Gateway routing RO | ❌ |
| ERP read scaling | ❌ |
| Dedicated per-tenant replica | ❌ |

**Veredicto:** **No preparado.** Escalabilidad lectura depende de SQL Server vertical scale.

---

## 8. Geo Regions

| Aspecto | Preparación |
|---------|-------------|
| Metadata region field | Hook futuro |
| Tenant affinity | ❌ |
| Cross-region latency CP | ⚠️ Riesgo |
| Data residency compliance | ❌ No diseñado |

**Veredicto:** **No preparado** para multi-region activo.

---

## 9. Backups & Restore

| Modo | Preparación |
|------|-------------|
| Shared central backup | ✅ Ops estándar SQL Server |
| Dedicated per-tenant backup | ⚠️ Q-062 abierta — quién ejecuta |
| Point-in-time tenant | ⚠️ No procedimiento |
| Restore tenant sin afectar otros | ✅ Dedicated natural; ⚠️ Shared |

**Veredicto:** Dedicated **mejor** para backup aislado; **procedimientos no documentados** en E5.

---

## 10. Tenant Export / Import / Archive / Delete

| Operación | Diseño E0–E5 | Preparación |
|-----------|--------------|-------------|
| **Export** | Mencionado extensión E5 01 | ❌ Sin flujo |
| **Import** | — | ❌ |
| **Archive** | Lifecycle Retirado E3/E4 | ⚠️ Behavioral only |
| **Delete** | Soft-delete ERP; dedicated drop DB? | ❌ Q-052 parcial |

**Veredicto:** **No preparado** para operaciones tenant lifecycle beyond Activo/Suspendido/Migrando.

---

## 11. Disaster Recovery

| Escenario | Preparación |
|-----------|-------------|
| CP store loss | ❌ SPOF — ADR-001 Alt A risk |
| Shared DB loss | ⚠️ Restore full platform |
| Single dedicated loss | ✅ Isolated blast radius |
| Region loss | ❌ |
| Redis loss | ⚠️ Q-011 |

**Veredicto:** DR **tenant-level** mejor en dedicated; **platform-level DR** no diseñado.

---

## 12. Matriz resumen escalabilidad

| Capacidad | 10 | 100 | 500 | 1000 |
|-----------|----|----|-----|------|
| Shared tenants | ✅ | ✅ | ⚠️ | ⚠️ |
| Dedicated tenants | ✅ | ⚠️ | ❌ | ❌ |
| Mixed | ✅ | ⚠️ | ⚠️ | ❌ |
| Migration factory | ✅ | ⚠️ | ❌ | ❌ |
| Read replica | ❌ | ❌ | ❌ | ❌ |
| Multi-region | ❌ | ❌ | ❌ | ❌ |
| Tenant export/import | ❌ | ❌ | ❌ | ❌ |
| DR | ⚠️ | ⚠️ | ⚠️ | ⚠️ |

---

## 13. Conclusión

Arquitectura **escala bien** para el target comercial probable (**decenas a low hundreds tenants**, mix shared-heavy). **No escala** a 500+ dedicated sin trabajo adicional engine/worker policy. Capabilities avanzadas (read replica, geo, export) **no preparadas** — correcto para MVP si scope comercial acotado.
