# 01 — Impacto Arquitectónico por Componente

**Etapa:** 2 — Architectural Impact Assessment  
**Fecha:** 2026-06-25  
**Estado:** Borrador para revisión  
**Prerequisitos:** Auditoría AS-IS (`01–06`), Modelo conceptual (`hybrid-platform/01–05`)  
**Restricción:** Análisis de impacto. Sin implementación.

---

## 1. Propósito

Determinar el **impacto real** que la incorporación de Dedicated Database tendría sobre cada componente del backend existente, bajo el principio de **mínima disrupción** y **backward compatibility first**.

Este documento responde: *¿Qué tocar y qué no tocar?*

---

## 2. Inventario de componentes (Sección A)

### 2.1 Capa de entrada

| Componente | Ubicación | Cantidad / alcance |
|------------|-----------|---------------------|
| FastAPI Application Factory | `app/main.py` | 1 |
| API Router agregador | `app/api/v1/api.py` | ~48 `include_router` |
| Health / metrics | `app/main.py`, `app/api/metrics_endpoint.py` | 2 |
| Middleware stack | CORS, TenantMiddleware, rate limiting | 3+ |
| Exception handlers | `app/core/exceptions.py` | Global |

### 2.2 Dependencias globales (Controllers / DI)

| Componente | Ubicación |
|------------|-----------|
| Auth deps | `app/api/deps.py` |
| Session contract deps | `app/api/deps_auth.py` |
| Module session deps | `org_deps.py`, `inv_deps.py`, `rbac_deps.py` |
| RBAC gate | `app/core/authorization/rbac.py` |

**Nota:** El proyecto no usa capa "Controller" separada; los endpoints FastAPI actúan como controllers.

### 2.3 Presentación (Routers + Schemas)

| Familia | Módulos | Endpoints |
|---------|---------|-----------|
| Platform | tenant, superadmin, modulos | ~15 grupos |
| IAM | auth, users, rbac, menus | ~10 grupos |
| ERP operativo | org, inv, pur, sls, wms, mfg, … | ~30+ grupos |
| **Total routers montados** | 35 módulos | ~48 en `api.py` |

Schemas: `presentation/schemas.py` y `schemas_*.py` por módulo (~35+ archivos).

### 2.4 Application Services

| Familia | Cantidad aprox. | Patrón |
|---------|-----------------|--------|
| ERP services | ~120+ archivos | `*_service.py`, `*_servicio` |
| Platform services | ~40+ archivos | Clases + `@BaseService` |
| IAM services | ~25+ archivos | Auth, sessions V2, impersonation |
| Core transversal | permission_resolver, menu_resolver | Singletons |

### 2.5 Infraestructura de datos

| Componente | Ubicación | Cantidad |
|------------|-----------|----------|
| Query functions | `app/infrastructure/database/queries/` | ~153 archivos |
| Query executor | `queries_async.py` | 1 (punto central) |
| Query helpers | `query_helpers.py` | Filtro tenant |
| SQLAlchemy tables (central) | `tables.py`, `tables_modulos.py` | 2 |
| Repositories (legacy) | auth, users, rbac, cfg | ~6 |
| Connection async | `connection_async.py` | Canónico |
| Connection routing | `core/tenant/routing.py` | Router tenant |
| Connection pool (legacy sync) | `connection_pool.py` | Deprecated activo en shutdown |
| Unit of Work | `core/application/unit_of_work.py` | 1 clase |

### 2.6 Tenant & Context

| Componente | Ubicación |
|------------|-----------|
| TenantMiddleware | `core/tenant/middleware.py` |
| TenantContext / ContextVar | `core/tenant/context.py` |
| Session scope | `core/tenant/session_scope.py` |
| Company scope | `core/tenant/company_scope.py` |
| Empresa context | `core/tenant/empresa_context.py` |
| Connection metadata cache | `core/tenant/cache.py` |

### 2.7 IAM completo

| Componente | Ubicación |
|------------|-----------|
| JWT | `core/security/jwt.py` |
| Auth service | `modules/auth/application/services/auth_service.py` |
| Session V2 services | `session_*_service.py` (6+) |
| Session V2 feature flag | `session/session_v2_feature.py` |
| Impersonation | `impersonation_service.py`, `core/auth/impersonation*.py` |
| Refresh token V1/V2 | `refresh_token_*`, queries auth/session |
| Redis bridge | `session_redis_bridge.py` |
| Password / SSO | `password_change_service`, `endpoints_sso` |

### 2.8 Redis & Cache

| Componente | Uso |
|------------|-----|
| Token blacklist | Revocación access JWT |
| Session Redis bridge | Mapeo session ↔ jti |
| Impersonation parent store | Restore post-impersonación |
| Permission resolver cache | Permisos por usuario/tenant |

### 2.9 Background Jobs

| Job | Ubicación |
|-----|-----------|
| Refresh token cleanup | `refresh_token_cleanup_job.py` |
| Permission sync (startup) | `permission_sync_service.py` |
| Lifespan startup/shutdown | `main.py` |

### 2.10 Onboarding & Provisioning

| Componente | Ubicación |
|------------|-----------|
| Cliente onboarding | `cliente_onboarding_service.py` |
| Onboarding RBAC | `onboarding_rbac_service.py` |
| ERP seed mínimo | `minimal_erp_tenant_bootstrap_service.py` |
| Owner sync / bundles | `owner_sync_service.py`, `*_standard_service.py` |
| Conexiones tenant | `conexion_service.py` |
| Platform bootstrap | `platform_bootstrap_service.py` |

### 2.11 Bootstrap & DDL

| Componente | Ubicación |
|------------|-----------|
| Schema versionado | `app/bootstrap_v2/01_schema/` (V010, V020, V030, V031) |
| Seeds catálogo | `app/bootstrap_v2/02_catalog/` |
| Manifest orden | `bootstrap_v2/00_manifest/` |
| Apply script | `scripts/bootstrap_v2_sql_apply.ps1` |

### 2.12 ERP Modules (operativos)

35 módulos bajo `app/modules/` — ORG, INV, PUR, SLS, WMS, MFG, MRP, MPS, FIN, HCM, CRM, LOG, POS, PRC, QMS, INV_BILL, CST, TAX, MNT, PM, SVC, TKT, DMS, WFL, BI, BDG, AUD.

### 2.13 Platform Modules

tenant, superadmin, modulos, catalogos, menus (legacy).

### 2.14 Tenant Admin vs Platform Admin

| Rol | Endpoints típicos | Módulos |
|-----|-------------------|---------|
| Platform Admin | `/clientes`, `/superadmin/*`, `/modulos-v2` | tenant, superadmin, modulos |
| Tenant Admin | `/usuarios`, `/roles`, `/org/empresa`, config auth | users, rbac, org, auth-config |

---

## 3. Análisis de impacto por componente (Sección B)

Escala: **Nulo | Muy Bajo | Bajo | Medio | Alto | Crítico**

### 3.1 Capa de presentación — ERP

| Componente | Impacto | Intacto | Justificación |
|------------|---------|---------|---------------|
| ERP endpoints (`endpoints_*.py`) | **Nulo** | Sí | No resuelven conexión; delegan a services |
| ERP schemas / DTOs | **Nulo** | Sí | Sin referencia a modo instalación |
| ERP `{cod}_deps` (org, inv, rbac) | **Nulo** | Sí | Resuelven tenant context, no almacén |
| OpenAPI / response models | **Nulo** | Sí | Contratos estables |

**Riesgo:** Bajo. **Dependencias:** Session context, RBAC.

---

### 3.2 Capa de aplicación — ERP Services

| Componente | Impacto | Intacto | Justificación |
|------------|---------|---------|---------------|
| Services ERP (~120 archivos) | **Nulo – Muy Bajo** | Sí | Invocan queries vía `execute_*` o UoW; no eligen conexión |
| INV transaccional (UoW) | **Muy Bajo** | Sí | UoW ya acepta `client_id`; resolución delegada |
| PUR/MNT transaccional | **Muy Bajo** | Sí | Idem |
| Workflow enforcement | **Nulo** | Sí | Reglas de negocio puras |

**Riesgo:** Bajo si infraestructura resuelve correctamente. **Dependencias:** `queries_async`, UoW.

---

### 3.3 Queries ERP

| Componente | Impacto | Intacto | Justificación |
|------------|---------|---------|---------------|
| Query functions (~140 ERP) | **Nulo** | Sí | SQL + filtros explícitos; sin routing |
| Auth/session queries | **Bajo – Medio** | Parcial | Algunas asumen ADMIN; evaluar en etapa IAM |
| RBAC queries | **Bajo** | Mayormente | Grants por tenant; catálogo central |

**Riesgo:** Medio solo si se exige cambio de SQL por modo (no recomendado — ADR-006).

---

### 3.4 Repositories legacy

| Componente | Impacto | Intacto | Justificación |
|------------|---------|---------|---------------|
| BaseRepository | **Muy Bajo** | Sí | Delega a `execute_*` |
| Usuario/User/Rol repos | **Muy Bajo** | Sí | Platform/IAM; conexión vía executor |
| CfgCodigoSecuenciaRepository | **Medio** | No | Acepta sesión externa; usado en onboarding cross-boundary |

**Riesgo:** Medio en onboarding seed. **Dependencias:** Onboarding refactor.

---

### 3.5 SQLAlchemy / conexión

| Componente | Impacto | Intacto | Justificación |
|------------|---------|---------|---------------|
| `connection_async.py` | **Crítico** | No | Engine cache, connection string, metadata |
| `routing.py` | **Crítico** | No | `get_connection_for_tenant`, multi/single |
| `queries_async.py` | **Alto** | No | Punto central `_get_connection_context` |
| `query_helpers.py` | **Alto** | No | `apply_tenant_filter`, GLOBAL_TABLES |
| `connection_pool.py` (legacy) | **Bajo** | Sí | Sync deprecated; shutdown only |
| `connection.py` (deprecated) | **Nulo** | Sí | No usar |
| Session factory efímera | **Alto** | Evoluciona | Dentro de `get_db_connection`; sin API pública |
| Engine lifecycle | **Medio** | No | Cache invalidation, shutdown |
| UnitOfWork | **Muy Bajo** | Sí | Wrapper sobre `get_db_connection`; transparente |

**Riesgo:** Crítico si mal diseñado — afecta todo el sistema. **Dependencias:** Metadata tenant, cache.

---

### 3.6 Middleware & Context

| Componente | Impacto | Intacto | Justificación |
|------------|---------|---------|---------------|
| TenantMiddleware | **Bajo – Medio** | Mayormente | Ya carga metadata y `database_type`; puede necesitar enriquecer metadata |
| TenantContext | **Muy Bajo** | Sí | Ya tiene `database_type`; negocio no debe leerlo |
| session_scope.py | **Nulo** | Sí | Resuelve tenant lógico, no almacén |
| company_scope.py | **Nulo** | Sí | Scope empresa |
| deps.py / deps_auth.py | **Nulo – Muy Bajo** | Sí | JWT, sesión, RBAC — sin routing BD |

**Riesgo:** Bajo. Cambios en middleware deben ser aditivos, no breaking.

---

### 3.7 IAM

| Componente | Impacto | Intacto | Justificación |
|------------|---------|---------|---------------|
| JWT claims / contrato | **Nulo** | Sí | Frontend depende de claims actuales |
| Auth endpoints | **Nulo** | Sí | Rutas y payloads estables |
| AuthService orquestación | **Bajo** | Sí | Delega a session services |
| Session V2 services | **Bajo – Medio** | Mayormente | UoW + queries; conexión vía infra |
| Session V1 legacy | **Bajo** | Sí | Coexistencia hasta cutover |
| Impersonation | **Muy Bajo** | Sí | Contexto JWT; infra resuelve almacén target |
| user_context.py | **Medio** | No | Ramas `database_type == "multi"` — deuda a eliminar de negocio |
| rol_service.py | **Medio** | No | Idem ramas multi |
| Redis bridge / blacklist | **Muy Bajo** | Sí | Agnóstico al modo |

**Riesgo:** Medio en servicios con ramas `database_type`. **Dependencias:** ADR-002 sesiones.

---

### 3.8 Onboarding & Provisioning

| Componente | Impacto | Intacto | Justificación |
|------------|---------|---------|---------------|
| `cliente_onboarding_service.py` | **Crítico** | No | TX única cross-boundary (Platform + ERP) |
| `onboarding_rbac_service.py` | **Medio** | Parcial | Lógica RBAC reusable; orquestación cambia |
| `minimal_erp_tenant_bootstrap` | **Alto** | No | Debe ejecutar en almacén tenant, no central |
| `conexion_service.py` | **Alto** | Evoluciona | CRUD metadata; integrar en provisioning |
| `cliente_service.py` (pre-validación) | **Muy Bajo** | Sí | Validaciones de negocio |
| Platform bootstrap | **Bajo** | Sí | Solo cliente SYSTEM |

**Riesgo:** Crítico — mayor superficie de regresión en alta de tenant. **Dependencias:** Saga ADR-004.

---

### 3.9 Bootstrap & DDL

| Componente | Impacto | Intacto | Justificación |
|------------|---------|---------|---------------|
| V010 ERP DDL | **Medio** | Contenido sí | Debe aplicarse también a almacenes dedicated |
| V020 central DDL | **Nulo** | Sí | Control plane |
| Seeds S010/S020/S030 | **Nulo** | Sí | Catálogo central |
| Pipeline apply script | **Medio** | Evoluciona | Extensión per-tenant dedicated |
| BOOTSTRAP_ORDER.md | **Bajo** | Doc evoluciona | Nuevo flujo dedicated |

**Riesgo:** Medio operacional (N almacenes). **Dependencias:** Provisioning.

---

### 3.10 Platform modules

| Componente | Impacto | Intacto | Justificación |
|------------|---------|---------|---------------|
| superadmin endpoints/services | **Nulo – Muy Bajo** | Sí | ADMIN central |
| modulos / cliente_modulo | **Nulo** | Sí | Catálogo central |
| tenant endpoints clientes | **Bajo** | Mayormente | POST /clientes dispara onboarding |
| tenant endpoints conexiones | **Medio** | Evoluciona | Metadata dedicated |

---

### 3.11 Background jobs & startup

| Componente | Impacto | Intacto | Justificación |
|------------|---------|---------|---------------|
| permission_sync startup | **Nulo** | Sí | Catálogo central |
| refresh_token_cleanup | **Muy Bajo** | Sí | Puede seguir en central |
| shutdown engines | **Medio** | No | `close_all_async_engines` faltante |
| Health check | **Muy Bajo** | Sí | Verifica conexión contextual |

---

### 3.12 Tests

| Componente | Impacto | Intacto | Justificación |
|------------|---------|---------|---------------|
| Unit tests ERP | **Nulo** | Sí | Mock execute_* |
| Integration tests IAM | **Medio** | Nuevos casos | Dedicated harness |
| conftest / fixtures | **Medio** | Extensión | Multi-almacén test |

**Nota:** Tests no son objetivo de protección contractual pero sí de regresión.

---

## 4. Resumen por nivel de impacto

| Nivel | Cantidad aprox. | Componentes representativos |
|-------|-----------------|----------------------------|
| **Nulo** | ~70% del código ERP | Endpoints, schemas, services, queries ERP |
| **Muy Bajo** | ~10% | UoW, deps, impersonation, repositories wrapper |
| **Bajo** | ~8% | Middleware, auth orquestación, platform admin |
| **Medio** | ~7% | Bootstrap pipeline, conexion_service, IAM ramas multi |
| **Alto** | ~3% | queries_async, query_helpers, ERP seed onboarding |
| **Crítico** | ~2% | connection_async, routing, cliente_onboarding_service |

---

## 5. Conclusión del análisis

La arquitectura actual **concentra el acoplamiento al modo de instalación en menos del 5% de los componentes**, principalmente en la capa de infraestructura de persistencia y en onboarding.

El **~70% del backend ERP puede permanecer intacto** si la resolución de conexión se encapsula correctamente (principio P5 del modelo conceptual).

El mayor riesgo de regresión no está en ERP sino en **onboarding** y **IAM services con ramas `database_type`**.
