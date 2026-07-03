# Hybrid Platform — Technical Debt Register

**Documento:** HYBRID_TECHNICAL_DEBT_REGISTER  
**Versión:** 1.0  
**Fecha:** 2026-06-25  
**Baseline:** BL-1.0  
**Post-Etapa:** F0–F3 cerrada  
**Sucesor:** IP-2.0.1 (F4 puede introducir deuda nueva — registrar aquí)

---

## 1. Propósito

Registro normativo de **deuda técnica deliberada** y **gaps conocidos** al cierre de Etapa 6. Toda deuda P0 bloquea merge sin ADR de excepción.

**Trazabilidad:** BL-1.0 `01_ARCHITECTURE_BASELINE.md` §4 (C-01…C-08), `04_OPEN_QUESTIONS_STATUS.md`, IP-1.0 F3 scope.

---

## 2. Leyenda

| Prioridad | Significado |
|-----------|-------------|
| **P0** | Bloqueante producción dedicated o regresión shared |
| **P1** | Debe resolverse antes F6 (production dedicated) |
| **P2** | Mejora; post-MVP / F8 |
| **P3** | Cosmético / documentación |

| Estado | Significado |
|--------|-------------|
| **OPEN** | Pendiente |
| **FROZEN** | Conocida; gate CI impide empeoramiento |
| **DEFERRED** | BL-1.0 explícito post-MVP |
| **CLOSED** | Resuelta |

---

## 3. Deuda L5 — `database_type` (FROZEN)

**Origen:** BL-1.0 C-01; F3-WP04 PR-F3-04  
**Gate:** `scripts/check_database_type_whitelist.py` — baseline 16 archivos congelada

| ID | Archivo | Ocurrencias | Prioridad | Target fase |
|----|---------|-------------|-----------|-------------|
| TD-L5-01 | `app/api/deps.py` | 3 | P2 | Post-F4 / IAM hardening |
| TD-L5-02 | `app/core/auth/impersonation_rbac.py` | 4 | P2 | F5b |
| TD-L5-03 | `app/core/auth/user_builder.py` | 8 | P2 | F5b |
| TD-L5-04 | `app/core/authorization/menu_resolver.py` | 2 | P2 | F5b |
| TD-L5-05 | `app/core/authorization/permission_resolver.py` | 3 | P2 | F5b |
| TD-L5-06 | `app/core/tenant/__init__.py` | 2 | P3 | F8 |
| TD-L5-07 | `app/core/tenant/empresa_preference.py` | 4 | P2 | F5b |
| TD-L5-08 | `app/infrastructure/database/queries.py` | 1 | P1 | Evaluar gateway sync path |
| TD-L5-09 | `app/modules/auth/application/services/auth_service.py` | 16 | P1 | F5b |
| TD-L5-10 | `app/modules/auth/application/services/refresh_token_cleanup_job.py` | 5 | P2 | F5b |
| TD-L5-11 | `app/modules/auth/presentation/endpoints.py` | 4 | P2 | F5b |
| TD-L5-12 | `app/modules/rbac/application/services/permisos_negocio_service.py` | 2 | P2 | Post-F4 |
| TD-L5-13 | `app/modules/rbac/application/services/permisos_usuario_service.py` | 2 | P2 | Post-F4 |
| TD-L5-14 | `app/modules/superadmin/application/services/audit_service.py` | 1 | P3 | — |
| TD-L5-15 | `app/modules/superadmin/application/services/superadmin_usuario_service.py` | 9 | P2 | — |
| TD-L5-16 | `app/modules/users/application/services/user_service.py` | 12 | P2 | — |

**Regla:** F4 **prohibido** añadir archivos a `KNOWN_L5_DEBT_BASELINE` sin ADR-012+.

**Resueltos en F3 (CLOSED):**

| Archivo | Fase |
|---------|------|
| `app/core/auth/user_context.py` | F3-WP02 |
| `app/modules/rbac/application/services/rol_service.py` | F3-WP03 |

---

## 4. RD-03 parcial — TenantContext legacy interno

| ID | Descripción | Prioridad | Estado |
|----|-------------|-----------|--------|
| TD-RD03-01 | `TenantContext` conserva atributos legacy internos (`database_type` en context.py whitelist) no consumibles L5 vía API pública | P2 | OPEN |
| TD-RD03-02 | Shims deprecated `get_database_type()` en `core/tenant/__init__.py` | P3 | OPEN |

**Mitigación F3:** middleware no expone Installation Mode a L5.  
**Target:** eliminación completa post-F5b o F8.

---

## 5. Provisioning & Dedicated — gaps pre-F4

| ID | Descripción | Prioridad | Estado | Resolución |
|----|-------------|-----------|--------|------------|
| TD-PROV-01 | No existe motor saga provisioning | P0 | OPEN → **F4** | IP-2.0.1 PR-F4-08 |
| TD-PROV-02 | No CREATE DATABASE en Python | P0 | OPEN → **F4** | PR-F4-04 |
| TD-PROV-03 | `POST /clientes/` seed en CP aunque `tipo_instalacion=dedicated` | P0 | OPEN → **F4** | PR-F4-07 ADR-F4-02 |
| TD-PROV-04 | `invalidate_client_connection_cache()` no invocado desde `crear_conexion` | P1 | OPEN → **F4** | PR-F4-09 |
| TD-PROV-05 | `test_conexion` simula éxito (no conectividad real) | P2 | OPEN | F6 ops |
| TD-PROV-06 | Sin estados `provisioning/ready/failed` en CP | P0 | OPEN → **F4** | PR-F4-01 |
| TD-PROV-07 | `dedicated_enabled` flag no existe | P1 | OPEN → **F4** | PR-F4-08 |
| TD-PROV-08 | Credenciales DDL platform no segregadas en config | P1 | OPEN → **F4** | PR-F4-04 ADR-F4-01 |

**Referencia:** BL-F4-1.0; auditoría provisioning pre-F4.

---

## 6. Cache & routing

| ID | Descripción | Prioridad | Estado |
|----|-------------|-----------|--------|
| TD-CACHE-01 | Invalidación cache depende de TTL 300s si no se invoca hook explícito | P1 | OPEN → F4-09 |
| TD-CACHE-02 | Redis distributed invalidation (TD-09) | P2 | DEFERRED F8 |
| TD-CACHE-03 | Engine key consolidation (TD-03) | P2 | DEFERRED F8 |

---

## 7. Catálogos dedicated (ADR-011)

| ID | Descripción | Prioridad | Estado |
|----|-------------|-----------|--------|
| TD-CAT-01 | F3.5 lista operativa catálogos S010–S066 no firmada como artefacto gate | P1 | OPEN → F4-06 |
| TD-CAT-02 | Sync catálogo CP→DP post-provisioning MVP | P2 | DEFERRED post-MVP |
| TD-CAT-03 | Read-through CP para cat_* (ADR-011-B rejected MVP) | P3 | DEFERRED |

---

## 8. Open Questions residuales (BL-1.0)

| ID | Tema | BL-1.0 estado | Post-F3 acción |
|----|------|---------------|----------------|
| Q-030 | Saga spec detalle | Cerrado behavioral; spec en BL-F4-1.0 | Implementar F4 |
| Q-011 | Redis SoT sesiones | Open | F6 hardening |
| Q-034 | Pool pre-provisionado | Deferred | Post-MVP |
| Q-060 | Monitoring dedicated | Open | F6 |
| Q-061 | DDL executor | Open → F4 | PR-F4-04 |
| C-06 | Ops runbooks | Pending | F6 |

---

## 9. CI / proceso

| ID | Descripción | Prioridad | Estado |
|----|-------------|-----------|--------|
| TD-CI-01 | `SHARED_ONBOARDING_REQUIRED_CHECK` no job CI dedicado (solo IP-2.0.1 §10.1) | P1 | OPEN → PRE-F4 / F4-07 |
| TD-CI-02 | Benchmark F2 cold-path metadata varianza local alta | P2 | OPEN — umbral ±10% staging |
| TD-CI-03 | Branch protection `shared-regression` required — verificar GitHub settings | P1 | OPEN — SRE |

---

## 10. ERP / session scope (fuera Hybrid Etapa 6)

| ID | Descripción | Prioridad | Estado |
|----|-------------|-----------|--------|
| TD-ERP-01 | `{cod}_deps` rollout módulos ERP impersonation-safe | P1 | BL-PEND-03 |
| TD-ERP-02 | Tests legacy rotos fuera scope Hybrid | P2 | Backlog QA |

---

## 11. Matriz deuda → plan F4 (IP-2.0.1)

| Deuda ID | PR F4 | BL-F4 ref |
|----------|-------|-----------|
| TD-PROV-01,06 | F4-01, F4-08 | §8 Saga |
| TD-PROV-02,08 | F4-04 | §11 S3, ADR-F4-01 |
| TD-PROV-03 | F4-07 | §12 ADR-F4-02 |
| TD-PROV-04, TD-CACHE-01 | F4-09 | §10 |
| TD-PROV-07 | F4-08 | IP-2.0.1 §7 |
| TD-CAT-01 | F4-06 | ADR-011 |
| TD-CI-01 | PRE-F4 PF4-11 | §10.1 |

---

## 12. Reglas de gobernanza de deuda

| Regla | Descripción |
|-------|-------------|
| DG-01 | Nueva deuda P0 requiere ADR-012+ |
| DG-02 | F4 no incrementa L5 debt baseline |
| DG-03 | Cierre deuda L5 masiva requiere fase dedicada (no mezclar con F4 provisioning) |
| DG-04 | Registrar cierre en changelog de este documento |

---

## 13. Referencias

| Documento | Ruta |
|-----------|------|
| BL-1.0 Open Questions | `architecture-baseline/04_OPEN_QUESTIONS_STATUS.md` |
| Risk Register | `repository-readiness/05_RISK_REGISTER.md` |
| F4 Handoff | `HYBRID_F4_HANDOFF.md` |
| IP-2.0.1 | `implementation-planning/IP-2.0_F4_IMPLEMENTATION_PLAN.md` |
