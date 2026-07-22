# 01 — Bootstrap AS-IS (estado actual)

**Etapa:** Auditoría arquitectónica pre-separación Platform / Tenant / Empresa  
**Fecha:** 2026-07-09  
**Alcance:** Solo inventario del bootstrap existente. Sin propuestas de implementación.

---

## 1. Capas actuales (sin separación formal)

Hoy el sistema no distingue explícitamente tres capas nombradas. En la práctica coexisten **cuatro ejes operativos**:

| Eje | Qué es hoy | Dónde vive |
|-----|------------|------------|
| **Instalación plataforma** | DDL + catálogos globales + identidad superadmin | SQL `bootstrap_v2`, startup `permission_sync`, CLI `bootstrap_platform.py` |
| **Onboarding tenant (Shared)** | Creación atómica de un cliente en BD única | `ClienteOnboardingService.crear_cliente_con_onboarding` |
| **Provisioning Dedicated** | Saga S1–S10 + seed sobre BD dedicada | `DedicatedProvisioningOrchestrator`, `DedicatedTenantSeedService` |
| **Bootstrap ERP mínimo** | Primera `org_empresa` + vínculo admin | `MinimalErpTenantBootstrapService` (embebido en onboarding) |

---

## 2. Platform Bootstrap (instalación / CP global)

### 2.1 SQL — esquema y catálogos globales

| Fase | Scripts | Efecto | Evidencia |
|------|---------|--------|-----------|
| Schema CP + ERP | `bootstrap_v2/01_schema/V010` → `V030` | Tablas vacías (incl. `permiso`, `modulo_menu`, `cfg_codigo_secuencia` DDL) | `V010:6809` `CREATE TABLE cfg_codigo_secuencia` |
| Catálogos | `bootstrap_v2/02_catalog/S010` → `S020` | `modulo`, `modulo_menu`, `permiso` globales | Referenciado en guías de instalación |

**No crea:** ningún `cliente` operativo ni filas tenant-scoped.

### 2.2 Startup — sincronización de permisos

| Componente | Archivo | Qué hace |
|------------|---------|----------|
| `run_rbac_startup` | `app/main.py` (lifespan) | Invoca `permission_sync` |
| `permission_sync` | `app/core/authorization/permission_startup.py` | `PermissionRegistry` → tabla `permiso` (catálogo global) |

**No crea:** identidad platform ni tenants.

### 2.3 CLI — identidad y RBAC platform

| Orquestador | Archivo | Transacción |
|-------------|---------|-------------|
| `PlatformBootstrapService.bootstrap` | `platform_bootstrap_service.py:95-158` | `get_db_connection(ADMIN)` + `session.begin()` |

**Fase identidad** — `PlatformIdentityBootstrapService.bootstrap_platform_identity` (`platform_identity_bootstrap_service.py:387-467`):

| Paso | Método | Tablas | Scope |
|------|--------|--------|-------|
| A | `_ensure_cliente` | `cliente` | `SUPERADMIN_CLIENTE_ID` fijo |
| B | `_ensure_rol` | `rol` (`ADMIN_PLATFORM`) | `cliente_id` platform |
| C | `_ensure_usuario` | `usuario` (`SUPERADMIN_USERNAME`) | `cliente_id` platform |
| D | `_ensure_usuario_rol` | `usuario_rol` | `empresa_id = NULL` (`:355`) |
| E | `_ensure_auth_config` | `cliente_auth_config` | `cliente_id` platform |

**Fase RBAC** — `PlatformRbacBootstrapService.bootstrap_platform_rbac` (`platform_rbac_bootstrap_service.py:53-91`):

| Paso | Efecto | Scope |
|------|--------|-------|
| Validar catálogo | `_validar_catalogo_permiso` (reuso onboarding) | Global |
| Activar módulo | `cliente_modulo` → `SYS_ADMIN` only | `cliente_id` platform |
| Grants | `rol_permiso` para `ADMIN_PLATFORM` | `cliente_id` platform |

**Auditoría:** `audit_platform_ready` (`platform_bootstrap_audit.py:23-178`) — read-only.

**Entry point:** `scripts/bootstrap_platform.py` (`--audit-only`, `--dry-run`, `--apply`, `--rbac-only`).

---

## 3. Tenant Bootstrap — Shared (onboarding atómico)

**Entry:** `ClienteService.crear_cliente` → rama shared (`cliente_service.py:132`)  
**Orquestador:** `ClienteOnboardingService.crear_cliente_con_onboarding` (`cliente_onboarding_service.py:95-165`)  
**TX:** `get_db_connection(DatabaseConnection.ADMIN)` + `session.begin()` (`:99-100`)

| # | Paso | Método | Archivo | Tablas principales |
|---|------|--------|---------|-------------------|
| 1 | Registro tenant | `_insertar_cliente` | `cliente_onboarding_service.py:168-246` | `cliente` |
| 2 | Roles base | `_insertar_roles_base` | `:249-283` | `rol` (`empresa_id=NULL`) |
| 3 | **Empresa inicial** | `ensure_empresa_inicial` | `minimal_erp_tenant_bootstrap_service.py:39-115` | `org_empresa` EMP001 |
| 4 | Usuario admin | `_insertar_usuario_admin` | `cliente_onboarding_service.py:286-389` | `usuario`, `usuario_rol` |
| 5 | **Vínculo admin↔empresa** | `vincular_admin_empresa` | `minimal_erp_tenant_bootstrap_service.py:118-193` | `usuario.empresa_default_id` |
| 6 | RBAC tenant | `bootstrap_cliente_rbac` | `onboarding_rbac_service.py:87-239` | `cliente_modulo`, `rol_permiso`, bundles |
| 7 | Auth config | `_insertar_auth_config_si_no_existe` | `cliente_onboarding_service.py:392-401` | `cliente_auth_config` |
| 8 | **Secuencias código** | `_insertar_secuencias_codigo` | `cliente_onboarding_service.py:404-423` | `cfg_codigo_secuencia` (57 filas) |

**Post-commit:** invalidación cache permisos (`:153-158`).

**Observación AS-IS:** los pasos 3, 5 y 8 (parcial) son responsabilidades de **empresa** mezcladas en el flujo de **tenant onboarding**.

---

## 4. Tenant Bootstrap — Dedicated (saga + S7)

### 4.1 CP — creación mínima

**Entry:** `ClienteService._crear_cliente_dedicated_provisioning` (`cliente_service.py:142-195`)

| Paso | Efecto | BD |
|------|--------|-----|
| `_insertar_cliente` | Solo `cliente` en CP | ADMIN |
| `initialize_provisioning_run` | Estado saga | ADMIN |
| `dispatch_after_initialize` | Job async S1–S10 | — |

**No ejecuta:** roles, usuario, RBAC, auth config, secuencias en CP.

### 4.2 Saga S1–S10

**Orquestador:** `DedicatedProvisioningOrchestrator._handle_job_inner` (`dedicated_provisioning_orchestrator.py:164-325`)  
**Orden:** `provisioning_step_code.py:SAGA_STEP_ORDER`

| Step | Código | Servicio | BD | Rol bootstrap |
|------|--------|----------|-----|---------------|
| S1 | `registry` | orchestrator | CP | Metadatos run |
| S2 | `storage_allocation` | `StorageAllocationService` | CP | Asignación storage |
| S3 | `create_database` | `DedicatedDatabaseExecutor` | SQL Server | BD física |
| S4/S5 | `apply_schema_*` | `BootstrapScriptRunner` | Dedicated | **DDL vacío** (V010, V020, RBAC) |
| S6 | `apply_catalogs` | `DedicatedCatalogSeedService` | Dedicated | **Catálogos globales replicados** (permiso, modulo_menu) |
| **S7** | **`seed_tenant`** | **`DedicatedTenantSeedService`** | Dedicated | **≈ pasos 2–8 Shared** |
| S8 | `register_metadata` | `DedicatedActivationService` | CP | Routing metadata |
| S9 | `activate_routing` | `DedicatedActivationService` | CP | Smoke routing |
| S10 | `mark_ready` + terminal | orchestrator + activation | CP | Run READY |

### 4.3 S7 — sub-pasos tenant seed

**Perfil:** `tenant_seed_profiles.py:38-45` (`_TENANT_SEED_STEPS`)  
**Ejecutor:** `execute_tenant_seed_step` (`dedicated_tenant_seed_adapters.py:115-205`)  
**Sesión:** `provisioning_dedicated_session` (`dedicated_tenant_seed_service.py:78`)

| Orden | `step_code` | Método reutilizado | Scope mixto |
|-------|-------------|-------------------|-------------|
| 1 | `seed_base_roles` | `_insertar_roles_base` | Tenant |
| 2 | `seed_org_empresa` | `ensure_empresa_inicial` | **Empresa** |
| 3 | `seed_admin_user` | `_insertar_usuario_admin` | Tenant (+ default empresa) |
| 4 | `seed_admin_empresa_link` | `vincular_admin_empresa` | **Empresa (preferencia)** |
| 5 | `seed_tenant_rbac` | `bootstrap_cliente_rbac` | Tenant |
| 6 | `seed_codigo_secuencias` | `_insertar_secuencias_codigo` | **Tenant + Empresa** |

**Gap documentado:** Dedicated S7 **no** incluye `_insertar_auth_config_si_no_existe` (`28_BOOTSTRAP_INTEGRATION_AUDIT.md`, ADJ-07).

---

## 5. Diagrama AS-IS (Shared)

```
POST /clientes/  (Shared)
    │
    ▼
ClienteOnboardingService.crear_cliente_con_onboarding  [TX ADMIN única]
    ├── 1. cliente                    (Tenant / CP)
    ├── 2. roles base                 (Tenant)
    ├── 3. org_empresa EMP001         (Empresa)  ← mezclado
    ├── 4. usuario admin              (Tenant)
    ├── 5. vincular_admin_empresa     (Empresa)  ← mezclado
    ├── 6. RBAC + bundles             (Tenant)
    ├── 7. cliente_auth_config        (Tenant / CP)
    └── 8. cfg_codigo_secuencia ×57   (1 TENANT + 56 EMPRESA) ← mezclado
```

---

## 6. Diagrama AS-IS (Dedicated)

```
POST /clientes/  (Dedicated)
    │
    ├── CP: cliente + provisioning_run
    │
    └── Saga async
         S4/S5: DDL (tablas vacías)
         S6:    catálogos SQL (permiso, modulo_menu)
         S7:    DedicatedTenantSeedService
                ├── roles, org_empresa, admin, RBAC, cfg (reusa onboarding)
                └── (sin auth_config CP)
         S8–S10: activación CP
```

---

## 7. Componentes auxiliares (fuera del flujo principal)

| Componente | Archivo | Rol actual |
|------------|---------|------------|
| `OnboardingMenuBootstrapService` | `onboarding_menu_bootstrap_service.py` | Legacy repair; delega a `OwnerSyncService` |
| `legacy_tenant_rbac_repair_service` | `legacy_tenant_rbac_repair_service.py` | Reparación tenants existentes |
| `DedicatedPermissionCatalogSyncService` | S6 post-sync | Alineación permisos en BD dedicada |
| `AllocationCoordinator.ensure_row` | `app/core/codigo/coordinator/` | Lazy creation secuencias ALMACEN/PV (runtime, no onboarding) |

---

*Matriz de responsabilidades: `02`. Separación Tenant vs Empresa: `03`.*
