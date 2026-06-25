# 06 — Matriz de Impacto

**Etapa:** 2 — Architectural Impact Assessment  
**Fecha:** 2026-06-25  
**Estado:** Borrador para revisión

---

## 1. Leyenda

### Impacto
| Nivel | Significado |
|-------|-------------|
| Nulo | Sin cambio anticipado |
| Muy Bajo | Cambio cosmético o transparente |
| Bajo | Cambio menor, bajo riesgo |
| Medio | Cambio moderado, tests adicionales |
| Alto | Cambio significativo en componente core |
| Crítico | Componente central; error = fallo sistémico |

### ¿Debe cambiar?
| Valor | Significado |
|-------|-------------|
| No | Permanece intacto |
| No (API) | API intacta; internals pueden cambiar |
| Sí | Debe evolucionar |
| Sí (nuevo) | Componente nuevo |
| Parcial | Parte intacta, parte evoluciona |
| Eliminar deuda | Refactor localizado |

### Prioridad implementación
| P | Significado |
|---|-------------|
| P0 | Bloqueante MVP dedicated |
| P1 | Importante post-MVP o paralelo |
| P2 | Mejora / deuda |
| — | No aplica (sin cambio) |

### Complejidad
| Nivel | Significado |
|-------|-------------|
| XS | Horas – 1 día |
| S | 1–3 días |
| M | 1–2 semanas |
| L | 2–4 semanas |
| XL | > 1 mes |

---

## 2. Matriz principal — Infraestructura

| Componente | Impacto | Debe cambiar | Prioridad | Riesgo | Complejidad | Observaciones |
|------------|---------|--------------|-----------|--------|-------------|---------------|
| `connection_async.py` | Crítico | Sí | P0 | Crítico | L | Engine cache, metadata, invalidación |
| `routing.py` | Crítico | Sí | P0 | Crítico | M | `get_connection_for_tenant` path multi |
| `queries_async.py` | Alto | Sí | P0 | Alto | M | `_get_connection_context`; sin cambio firma pública |
| `query_helpers.py` | Alto | Sí | P0 | Alto | M | Tenant filter encapsulation |
| `core/tenant/cache.py` | Medio | Sí | P1 | Medio | S | Invalidación metadata |
| `connection_pool.py` (legacy) | Bajo | No | — | Bajo | — | Shutdown only; no bloqueante |
| `connection.py` (deprecated) | Nulo | No | — | — | — | No tocar |
| `unit_of_work.py` | Muy Bajo | No | — | Bajo | — | Transparente a resolución |
| `main.py` shutdown | Medio | Sí | P1 | Medio | XS | `close_all_async_engines` |
| `query_auditor.py` | Bajo | Parcial | P2 | Bajo | S | Reglas GLOBAL_TABLES |

---

## 3. Matriz — Tenant & Context

| Componente | Impacto | Debe cambiar | Prioridad | Riesgo | Complejidad | Observaciones |
|------------|---------|--------------|-----------|--------|-------------|---------------|
| `TenantMiddleware` | Bajo–Medio | Parcial | P1 | Medio | S | Enriquecer metadata; sin breaking |
| `TenantContext` | Muy Bajo | No | — | Bajo | — | Ya tiene `database_type` |
| `session_scope.py` | Nulo | No | — | — | — | Protegido |
| `company_scope.py` | Nulo | No | — | — | — | Protegido |
| `empresa_context.py` | Nulo | No | — | — | — | Protegido |
| `deps.py` | Nulo–Muy Bajo | No | — | Bajo | — | Protegido |
| `deps_auth.py` | Nulo | No | — | — | — | Protegido |
| `org/inv/rbac_deps` | Nulo | No | — | — | — | Protegido |

---

## 4. Matriz — IAM

| Componente | Impacto | Debe cambiar | Prioridad | Riesgo | Complejidad | Observaciones |
|------------|---------|--------------|-----------|--------|-------------|---------------|
| JWT / `jwt.py` | Nulo | No | — | — | — | Contrato FE protegido |
| Auth endpoints | Nulo | No | — | — | — | Protegido |
| `auth_service.py` | Bajo | No (API) | — | Bajo | — | Orquestación intacta |
| Session V2 services | Bajo–Medio | No (API) | P1 | Medio | S | Verificar conexión vía infra |
| Session V1 legacy | Bajo | No | — | Bajo | — | Coexistencia |
| `session_redis_bridge` | Muy Bajo | No | — | Bajo | — | Agnóstico modo |
| Impersonation | Muy Bajo | No | — | Medio | — | Infra resuelve target store |
| `user_context.py` | Medio | Eliminar deuda | P1 | Medio | S | Ramas `database_type` |
| `rol_service.py` | Medio | Eliminar deuda | P1 | Medio | S | Ramas `database_type` |
| Auth session queries | Bajo–Medio | Parcial | P1 | Medio | M | Según ADR-002 sesiones |
| `refresh_token_cleanup_job` | Muy Bajo | No | — | Bajo | — | |

---

## 5. Matriz — Onboarding & Provisioning

| Componente | Impacto | Debe cambiar | Prioridad | Riesgo | Complejidad | Observaciones |
|------------|---------|--------------|-----------|--------|-------------|---------------|
| `cliente_onboarding_service` | Crítico | Sí | P0 | Crítico | L | Saga; response protegido |
| `minimal_erp_tenant_bootstrap` | Alto | Sí | P0 | Alto | M | Seed en almacén tenant |
| `onboarding_rbac_service` | Medio | Parcial | P0 | Medio | S | Reutilizar lógica; cambiar sesión |
| `owner_sync_service` | Bajo | No | — | Bajo | — | Lógica intacta |
| `*_standard_service` | Bajo | No | — | Bajo | — | |
| `cliente_service` (pre-val) | Muy Bajo | No | — | — | — | |
| `conexion_service` | Medio–Alto | Sí | P0 | Alto | M | Integrar provisioning |
| **Provisioning Orchestrator** | — | Sí (nuevo) | P0 | Alto | L | Componente nuevo |
| **Saga Coordinator** | — | Sí (nuevo) | P0 | Alto | L | Componente nuevo |
| **Dedicated DDL Pipeline** | — | Sí (nuevo) | P0 | Alto | L | Ops / bootstrap ext |

---

## 6. Matriz — ERP (35 módulos)

| Componente | Impacto | Debe cambiar | Prioridad | Riesgo | Complejidad | Observaciones |
|------------|---------|--------------|-----------|--------|-------------|---------------|
| ERP endpoints (~130 files) | Nulo | No | — | — | — | **Protegido total** |
| ERP schemas | Nulo | No | — | — | — | **Protegido total** |
| ERP services (~120 files) | Nulo | No | — | — | — | **Protegido total** |
| ERP queries (~140 files) | Nulo | No | — | — | — | **Protegido total** |
| INV UoW procesos | Muy Bajo | No | — | Bajo | — | Transparente |
| PUR/MNT UoW | Muy Bajo | No | — | Bajo | — | |
| `shared/pagination` | Nulo | No | — | — | — | |
| Workflow enforcement | Nulo | No | — | — | — | |

---

## 7. Matriz — Platform Admin

| Componente | Impacto | Debe cambiar | Prioridad | Riesgo | Complejidad | Observaciones |
|------------|---------|--------------|-----------|--------|-------------|---------------|
| superadmin services | Nulo–Muy Bajo | No | — | — | — | ADMIN central |
| modulos services | Nulo | No | — | — | — | |
| `POST /clientes/` response | Nulo | No | — | — | — | Shape protegido |
| `endpoints_conexiones` | Medio | Parcial | P1 | Medio | S | Extensión aditiva |
| Platform bootstrap | Bajo | No | — | — | — | |

---

## 8. Matriz — Bootstrap & Ops

| Componente | Impacto | Debe cambiar | Prioridad | Riesgo | Complejidad | Observaciones |
|------------|---------|--------------|-----------|--------|-------------|---------------|
| V010 ERP DDL | Medio | No (contenido) | P0 | Medio | M | Aplicar a dedicated stores |
| V020 central DDL | Nulo | No | — | — | — | |
| Seeds S010/S020 | Nulo | No | — | — | — | |
| `bootstrap_v2_sql_apply` | Medio | Sí | P0 | Medio | M | Extensión per-tenant |
| Repair scripts | Medio | Parcial | P2 | Medio | M | Pueden asumir BD única |
| CI pipeline | Medio | Sí | P1 | Medio | M | Dedicated integration job |

---

## 9. Matriz — Contratos & FE

| Componente | Impacto | Debe cambiar | Prioridad | Riesgo | Complejidad | Observaciones |
|------------|---------|--------------|-----------|--------|-------------|---------------|
| OpenAPI spec | Nulo | No | — | — | — | Aditivo only |
| JWT contract | Nulo | No | — | Crítico si cambia | — | **Protegido** |
| Session contract | Nulo | No | — | Crítico si cambia | — | **Protegido** |
| Pagination envelope | Nulo | No | — | — | — | |
| Error format | Nulo | No | — | — | — | |
| Frontend | Nulo | No | — | — | — | Transparency |

---

## 10. Matriz — Repositories & Legacy

| Componente | Impacto | Debe cambiar | Prioridad | Riesgo | Complejidad | Observaciones |
|------------|---------|--------------|-----------|--------|-------------|---------------|
| `BaseRepository` | Muy Bajo | No | — | — | — | |
| Usuario/User repos | Muy Bajo | No | — | — | — | |
| `CfgCodigoSecuenciaRepository` | Medio | Parcial | P0 | Medio | S | Onboarding session target |
| `queries.py` (deprecated) | Nulo | No | — | — | — | |

---

## 11. Matriz consolidada por capa

| Capa | Componentes | Impacto medio | Debe cambiar | % codebase |
|------|-------------|---------------|--------------|------------|
| ERP presentation + app + queries | ~290 files | Nulo | No | ~65% |
| Contratos IAM/FE | ~15 files | Nulo | No | ~3% |
| Platform (excl. onboarding) | ~25 files | Muy Bajo | No | ~6% |
| IAM orquestación | ~20 files | Bajo | Parcial | ~5% |
| Infra persistencia | ~8 files | Crítico–Alto | Sí | ~2% |
| Onboarding/provisioning | ~10 files | Crítico | Sí | ~2% |
| Nuevos (conceptuales) | 4–6 | — | Sí (nuevo) | ~1% |
| Deuda multi | 2 files | Medio | Eliminar | <1% |
| Tests/CI/scripts | ~15 files | Medio | Sí | ~3% |

---

## 12. Top 10 componentes por riesgo × impacto

| Rank | Componente | Impacto | Riesgo | Acción |
|------|------------|---------|--------|--------|
| 1 | `connection_async.py` | Crítico | Crítico | Evolucionar P0 |
| 2 | `routing.py` | Crítico | Crítico | Evolucionar P0 |
| 3 | `cliente_onboarding_service` | Crítico | Crítico | Saga P0 |
| 4 | `queries_async.py` | Alto | Alto | Encapsular P0 |
| 5 | `query_helpers.py` | Alto | Alto | Encapsular P0 |
| 6 | Provisioning Orchestrator (nuevo) | — | Alto | Crear P0 |
| 7 | `minimal_erp_tenant_bootstrap` | Alto | Alto | Target store P0 |
| 8 | Dedicated DDL Pipeline (nuevo) | — | Alto | Crear P0 |
| 9 | `conexion_service` | Medio–Alto | Alto | Integrar P0 |
| 10 | `user_context.py` / `rol_service` | Medio | Medio | Deuda P1 |

---

## 13. Heatmap textual

```
Impacto →
         Nulo    M.Bajo   Bajo    Medio    Alto    Crítico
Capa ERP ████████████████████████████████████  (protegido)
Contratos ████████                              (protegido)
Platform  ██████████████                        (mayormente OK)
IAM       ████████████░░░░░░                    (deuda localizada)
Infra     ░░░░░░░░░░░░░░░░████████████████████  (foco cambio)
Onboard   ░░░░░░░░░░░░░░░░░░░░░░████████████  (foco cambio)
```

---

## 14. Conclusión de matriz

- **~65%** del codebase: impacto **Nulo**, sin cambios
- **~8%**: impacto **Bajo–Medio**, cambios menores o deuda
- **~5%**: impacto **Alto–Crítico**, superficie de cambio principal
- **~4–6 componentes nuevos** conceptuales, no duplicación de ERP

La matriz confirma que Dedicated Database es **viable con impacto acotado** si se respetan guardrails y superficie delimitada.
