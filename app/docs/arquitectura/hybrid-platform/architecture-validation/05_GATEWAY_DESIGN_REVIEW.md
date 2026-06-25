# 05 — Gateway Design Review

**Etapa:** 5.5 — Architecture Validation  
**Fecha:** 2026-06-25  
**Alcance:** Persistence Gateway exclusivamente (E5 01 + relacionados)

---

## 1. Propósito

Evaluación adversarial del diseño del Persistence Gateway: acoplamientos, responsabilidades, extensibilidad, riesgos futuros. **Sin proponer implementación.**

---

## 2. Evaluación general

| Criterio | Score 1–5 | Comentario |
|----------|-----------|------------|
| Coherencia con runtime RD-06 | 5 | Alineado |
| Minimal change / evolve AS-IS | 4 | TD-11 sensato |
| Separación responsabilidades | 3 | Gateway "disperso" — riesgo God pipeline |
| Testabilidad | 4 | Pipeline lineal testeable |
| Extensibilidad multi-DB | 2 | Acoplado SQL Server |
| Extensibilidad multi-region | 3 | Metadata hook existe |
| Operational clarity | 3 | Métricas definidas; runbooks thin |

**Score medio: 3.4/5** — Adecuado para MVP SQL Server; extensibilidad limitada.

---

## 3. Acoplamientos identificados

### 3.1 Acoplamientos aceptables (by design)

| Acoplamiento | Justificación |
|--------------|---------------|
| Gateway ↔ Tenant ContextVar | Necesario resolver client_id |
| Gateway ↔ SQLAlchemy Core | Stack elegido AS-IS |
| Gateway ↔ QueryAuditor | Seguridad transversal G-20 |
| execute_* ↔ tenant filter | Aislamiento shared |

### 3.2 Acoplamientos problemáticos

| ID | Acoplamiento | Riesgo |
|----|--------------|--------|
| GW-A01 | Pipeline mezcla resolución + ejecución + commit policy | Cambio en uno afecta todo |
| GW-A02 | GLOBAL_TABLES en query_helpers acoplado a clasificación E3 | Dedicated catálogos |
| GW-A03 | Middleware precarga metadata acoplado a gateway cache | Duplicación lógica |
| GW-A04 | IAM session route TBD acoplado a gateway sin interfaz estable | RD-11 |
| GW-A05 | Repositories legacy acoplados indirectamente sin contrato único | Bypass paths |

---

## 4. Responsabilidades excesivas (SOLID adversarial)

| Principio | Evaluación |
|-----------|------------|
| **S** Single Responsibility | ⚠️ Gateway pipeline hace: classify, resolve, filter, audit, execute, commit, close — **6+ responsabilidades** |
| **O** Open/Closed | ⚠️ Nuevos storage providers requieren tocar routing + connection_async |
| **L** Liskov | N/A conceptual |
| **I** Interface Segregation | ✅ L5 ve API mínima execute_* |
| **D** Dependency Inversion | ⚠️ L5 depende de funciones concretas infra, no abstracción — aceptable en monolito |

**Veredicto SOLID:** No es un diseño SOLID clásico — es **pipeline procedural encapsulado**. Aceptable para ERP monolito; **deuda** si se busca multi-engine.

**Posible simplificación futura (conceptual):** Separar **Resolution Subpipeline** de **Execution Subpipeline** sin cambiar API L5 — no requerido MVP.

---

## 5. Riesgos futuros del gateway

| ID | Riesgo | Horizonte |
|----|--------|-----------|
| GW-R01 | God pipeline difícil de test unitario granular | MVP |
| GW-R02 | Fork accidental `execute_*_v2` bajo presión | 6 meses |
| GW-R03 | Feature flags installation mode fil          gateway | Violación G-10 |
| GW-R04 | Read replica routing mezclado en execute_query | 12 meses |
| GW-R05 | Cross-plane join temptation in gateway | Permanente |

---

## 6. Compatibilidad PostgreSQL / MySQL / Oracle

| Motor | Preparación actual | Gap |
|-------|-------------------|-----|
| **SQL Server** | ✅ Nativo AS-IS | — |
| **PostgreSQL** | ❌ Bajo | Driver async; dialect; UPDLOCK semantics INV |
| **MySQL** | ❌ Bajo | Locking; DDL differences |
| **Oracle** | ❌ Muy bajo | Sequences; ROWNUM; licensing |

**Evaluación:** El gateway está **conceptualmente** desacoplado de negocio (bien), pero **técnicamente acoplado** a:
- `mssql+aioodbc`
- SQL Server locking patterns en queries ERP
- DDL bootstrap_v2 SQL Server specific

**Extensibilidad multi-DB:** Metadata podría incluir `engine_type`, pero **100% queries ERP** deberían revisarse — contradice G-01 "0 ERP changes". **Conclusión:** Multi-DB engine es **roadmap mayor**, no extensión del gateway alone.

---

## 7. Read Replica

| Aspecto | Preparación |
|---------|-------------|
| Metadata hint read-only | Mencionado E5 01 §11 — no diseñado |
| execute_query routing RO | No existe |
| UoW en replica | **Problemático** — writes mezclados |
| Session stickiness | No requerido |

**Veredicto:** **No preparado.** Requiere operation hint + separación read/write en API gateway (breaking si no opt-in).

---

## 8. Multi-Region

| Aspecto | Preparación |
|---------|-------------|
| Region en Storage Metadata | Hook futuro E5 02 |
| Engine key con region | Documentado |
| Tenant affinity region | No diseñado |
| Cross-region CP lookup | Latency risk |

**Veredicto:** **Parcialmente preparado** a nivel metadata; runtime no diseñado.

---

## 9. On-Premise

| Aspecto | Preparación |
|---------|-------------|
| External endpoint metadata | ✅ Installation mode hook |
| VPN/tunnel config | O-E5-03 abierta |
| Platform reachability | Q-012 impersonation |
| Customer-managed backup | Q-062 abierta |

**Veredicto:** **Metadata-ready; ops-not-ready.**

---

## 10. Storage Providers futuros (S3, Cosmos, etc.)

Gateway diseñado para **relational SQL stores** únicamente. No hay abstracción blob/document. **Fuera de alcance** — correcto para ERP actual.

---

## 11. Fortalezas del diseño gateway

1. API estable hacia L5 — máxima protección E2.
2. Per-op resolution + L-A cache — pragmático AS-IS.
3. Fail-closed dedicated — seguridad priorizada.
4. UoW unchanged — procesos transaccionales protegidos.
5. Evolución vs rewrite — reduce riesgo regresión.

---

## 12. Debilidades críticas

1. Pipeline monolítico con 6+ responsabilidades.
2. Catálogos / tablas híbridas sin reglas cerradas.
3. Multi-engine SQL no viable sin ERP query review masivo.
4. Repository second path sin enforcement.
5. Session IAM route undecided inside same pipeline.

---

## 13. Conclusión gateway

El Persistence Gateway es **suficiente y bien orientado para MVP SQL Server Shared→Dedicated**. No es un **gateway genérico multi-provider**. Extensibilidad PostgreSQL/Read Replica/Multi-Region requiere **etapas arquitectónicas adicionales**, no solo implementación E5.

**Recomendación:** Aprobar diseño gateway para Fase 1; registrar GW-A01/GW-A02 como deuda estructural post-MVP.
