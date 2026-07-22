# 02 — Matriz de responsabilidades (Platform / Tenant / Empresa)

**Etapa:** Auditoría bootstrap-v2 — AS-IS  
**Leyenda:** **O** = owner actual · **C** = colabora · **—** = no participa · **⚠** = mezclado / acoplamiento incorrecto

---

## 1. Matriz por responsabilidad

| ID | Responsabilidad | Platform | Tenant | Empresa | Evidencia (archivo:método) |
|----|-----------------|----------|--------|---------|----------------------------|
| R01 | DDL esquema ERP/CP (tablas vacías) | **O** | — | — | `BootstrapScriptRunner` / SQL `V010`; Dedicated S4/S5 |
| R02 | Catálogo global `permiso` / `modulo_menu` | **O** | — | — | SQL `S010`; startup `permission_sync`; Dedicated S6 |
| R03 | Identidad superadmin (cliente platform) | **O** | — | — | `PlatformIdentityBootstrapService._ensure_cliente` |
| R04 | Rol/usuario platform (`ADMIN_PLATFORM`) | **O** | — | — | `PlatformIdentityBootstrapService._ensure_rol/_ensure_usuario` |
| R05 | Auth config platform | **O** | — | — | `PlatformIdentityBootstrapService._ensure_auth_config` |
| R06 | RBAC platform (`SYS_ADMIN`, grants CP) | **O** | — | — | `PlatformRbacBootstrapService.bootstrap_platform_rbac` |
| R07 | Registro `cliente` operativo | — | **O** | — | `ClienteOnboardingService._insertar_cliente` |
| R08 | Roles base tenant (`ADMIN/MANAGER/USER_TENANT`) | — | **O** | — | `_insertar_roles_base` (`empresa_id=NULL`) |
| R09 | Usuario admin tenant | — | **O** | — | `_insertar_usuario_admin` |
| R10 | Activación módulos por plan | — | **O** | — | `OnboardingRbacService.activar_modulos_base_cliente` |
| R11 | Grants RBAC tenant (OwnerSync, bundles) | — | **O** | — | `bootstrap_cliente_rbac` |
| R12 | Auth config tenant (CP) | — | **O** ⚠ | — | `_insertar_auth_config_si_no_existe` (Shared only) |
| R13 | Provisioning saga Dedicated (S1–S3, S8–S10) | **C** | **O** | — | `DedicatedProvisioningOrchestrator` |
| R14 | Crear `org_empresa` inicial | — | **O** ⚠ | **(debería O)** | `MinimalErpTenantBootstrapService.ensure_empresa_inicial` |
| R15 | Vínculo admin → empresa default | — | **O** ⚠ | **(debería O)** | `vincular_admin_empresa` |
| R16 | Seed `cfg_codigo_secuencia` TENANT (1 fila) | — | **O** | — | `_insertar_secuencias_codigo` scope TENANT |
| R17 | Seed `cfg_codigo_secuencia` EMPRESA (56 filas) | — | **O** ⚠ | **(debería O)** | `_insertar_secuencias_codigo` scope EMPRESA |
| R18 | Metadatos secuencia (prefijos, scope) | — | **C** | **C** | `SequenceCatalog` + `onboarding_seed.py` (motor) |
| R19 | Lazy secuencias ALMACEN/PV | — | — | **C** | `AllocationCoordinator.ensure_row` (runtime) |
| R20 | Verificación conteos seed Dedicated | — | **O** | **C** | `tenant_seed_profiles.row_expectations` |

**⚠** = hoy el Tenant Bootstrap **ejecuta** responsabilidades que conceptualmente son de Empresa.

---

## 2. Matriz por componente (ownership de archivos)

| Componente | Capa dominante AS-IS | Consumidores | Reutilizable |
|------------|---------------------|--------------|--------------|
| `platform_identity_bootstrap_service.py` | Platform | CLI only | No (SUPERADMIN fijo) |
| `platform_rbac_bootstrap_service.py` | Platform | CLI + audit | Parcial (`activar_modulos_base_cliente`) |
| `platform_bootstrap_service.py` | Platform | CLI | Orquestador platform |
| `cliente_onboarding_service.py` | Tenant (+ Empresa mezclado) | Shared API, Dedicated adapters | Parcial (métodos estáticos) |
| `minimal_erp_tenant_bootstrap_service.py` | **Empresa** (mal ubicado en nombre) | Shared onboarding, Dedicated S7 | **Sí** — candidato Empresa Bootstrap |
| `onboarding_rbac_service.py` | Tenant | Shared, Dedicated, Platform (subset) | **Sí** |
| `onboarding_seed.py` / motor | Contrato datos | onboarding + profiles | **Sí** (con split TENANT/EMPRESA) |
| `dedicated_tenant_seed_adapters.py` | Tenant orchestration | Dedicated S7 only | Parcial |
| `dedicated_tenant_seed_service.py` | Tenant orchestration | Dedicated S7 | Dedicated-specific |
| `tenant_seed_profiles.py` | Tenant config | Dedicated S7 | Dedicated-specific |
| `bootstrap_script_runner.py` | Platform/DB provision | Dedicated S4/S5 | Dedicated-specific |
| `dedicated_catalog_seed_service.py` | Platform catalog replica | Dedicated S6 | Dedicated-specific |
| `auth_config_gateway.py` | Tenant (CP) | onboarding, platform identity | **Sí** |

---

## 3. Matriz por dependencia de scope

| Artefacto | Solo `cliente_id` | Requiere `empresa_id` | Fuente |
|-----------|-------------------|----------------------|--------|
| `cliente` | PK | — | onboarding paso 1 |
| `rol` (base) | FK | NULL fijo | `_insertar_roles_base:262` |
| `org_empresa` | FK | PK creado | `ensure_empresa_inicial` |
| `usuario` | FK | `empresa_default_id` opcional | `_insertar_usuario_admin:326` |
| `usuario_rol` (ADMIN) | FK | NULL (tenant-wide) | `vincular_admin_empresa:151` |
| `cliente_modulo` | FK | — | RBAC |
| `rol_permiso` / `rol_menu_permiso` | FK | NULL en onboarding | bundles |
| `cliente_auth_config` | FK | — | auth gateway |
| `cfg_codigo_secuencia` TENANT | FK | NULL | `onboarding_seed` scope TENANT |
| `cfg_codigo_secuencia` EMPRESA | FK | **requerido** | `_insertar_secuencias_codigo:409-410` |

---

## 4. Flujos de ejecución — quién invoca qué

### Platform (una vez por instalación)

```
scripts/bootstrap_platform.py
  → PlatformBootstrapService.bootstrap
    → PlatformIdentityBootstrapService.bootstrap_platform_identity
    → PlatformRbacBootstrapService.bootstrap_platform_rbac
```

### Tenant Shared (una vez por cliente)

```
ClienteService.crear_cliente (:132)
  → ClienteOnboardingService.crear_cliente_con_onboarding (:95)
    → pasos 1–8 (ver 01)
```

### Tenant Dedicated (una vez por cliente + BD)

```
ClienteService._crear_cliente_dedicated_provisioning (:142)
  → DedicatedProvisioningOrchestrator.handle_job
    → S7 DedicatedTenantSeedService.run_tenant_seed
      → execute_tenant_seed_step (6 sub-pasos)
```

---

## 5. Respuestas directas a preguntas 1–3 (matriz)

**1. Platform Bootstrap hoy:** R01–R06 (instalación global, identidad superadmin, RBAC CP). No crea tenants operativos.

**2. Tenant Bootstrap hoy:** R07–R13, R16, **más** R14, R15, R17 ejecutados dentro del mismo flujo (mezcla).

**3. Empresa Bootstrap (responsabilidades reales, aunque no exista como capa):** R14 (`org_empresa`), R15 (preferencia login admin), R17 (56 secuencias EMPRESA), y en runtime futuro R19 por entidad.

---

*Componentes reutilizables y acoplamientos: `04`. Riesgos: `05`.*
