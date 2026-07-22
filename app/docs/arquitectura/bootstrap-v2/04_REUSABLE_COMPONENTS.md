# 04 — Componentes reutilizables y acoplamientos

**Etapa:** Auditoría bootstrap-v2 — preguntas 4, 5, 10

---

## 1. Componentes ya reutilizables (evidencia)

| Componente | Método(s) | Reutilizado por | Evidencia |
|------------|-----------|-----------------|-----------|
| `ClienteOnboardingService` | `_insertar_roles_base` | Shared paso 2; Dedicated S7-1 | `dedicated_tenant_seed_adapters.py:123-128` |
| `ClienteOnboardingService` | `_insertar_usuario_admin` | Shared paso 4; Dedicated S7-3 | `adapters.py:141-156` |
| `ClienteOnboardingService` | `_insertar_secuencias_codigo` | Shared paso 8; Dedicated S7-6 | `adapters.py:195-199` |
| `MinimalErpTenantBootstrapService` | `ensure_empresa_inicial` | Shared paso 3; Dedicated S7-2 | `adapters.py:131-138` |
| `MinimalErpTenantBootstrapService` | `vincular_admin_empresa` | Shared paso 5; Dedicated S7-4 | `adapters.py:159-171` |
| `OnboardingRbacService` | `bootstrap_cliente_rbac` | Shared paso 6; Dedicated S7-5; Platform (validación catálogo) | `adapters.py:180-186`; `platform_rbac_bootstrap_service.py:56` |
| `OnboardingRbacService` | `activar_modulos_base_cliente` | Tenant RBAC; Platform RBAC (módulo SYS_ADMIN) | `platform_rbac_bootstrap_service.py:67-72` |
| `AuthConfigGateway` | `config_exists`, `insert_config` | Shared onboarding; Platform identity | `cliente_onboarding_service.py:397-401`; `platform_identity_bootstrap_service.py:371-385` |
| `onboarding_seed.py` | `ONBOARDING_SEQUENCE_SEEDS`, `EAGER_SEQUENCE_KEYS` | Shared, Dedicated profiles, tests | `tenant_seed_profiles.py:84`; `cliente_onboarding_service.py:408` |
| `SequenceCatalog` | definiciones | Motor + seed derivado | `onboarding_seed.py:63-74` |
| `CfgCodigoSecuenciaRepository` | `insert_secuencia(session=...)` | Seed onboarding (session-driven) | `cfg_codigo_secuencia_repository.py:166-225` |

**Patrón intencional documentado:** Dedicated S7 **reutiliza exactamente** funciones de onboarding Shared (`28_BOOTSTRAP_INTEGRATION_AUDIT.md` AI-D1).

---

## 2. Componentes reutilizables Shared ↔ Dedicated (pregunta 10)

| Capacidad | Shared | Dedicated | Mecanismo reutilización |
|-----------|--------|-----------|-------------------------|
| Roles base | ✓ | ✓ | Mismo método estático + `session` DP |
| Empresa inicial | ✓ | ✓ | `MinimalErpTenantBootstrapService` |
| Admin user | ✓ | ✓ | `_insertar_usuario_admin` |
| RBAC bundles | ✓ | ✓ | `bootstrap_cliente_rbac` |
| Secuencias CFG | ✓ | ✓ | `_insertar_secuencias_codigo` |
| Auth config | ✓ | ✗ (gap) | Método existe; no invocado en Dedicated |
| Catálogo permiso | Preexistente | S6 SQL + sync | **No** reutiliza Python onboarding |
| DDL esquema | Preexistente | S4/S5 runner | Dedicated-only |

**Conclusión:** el **seed tenant Python** (pasos 2–8 Shared) es **100% reutilizable** vía adapters; Dedicated añade capas propias (DDL, catálogos SQL, saga, activación CP).

---

## 3. Componentes acoplados incorrectamente (pregunta 5)

| Acoplamiento | Descripción | Evidencia | Impacto |
|--------------|-------------|-----------|---------|
| **A1 — Empresa dentro de Tenant onboarding** | `crear_cliente_con_onboarding` mezcla tenant + empresa en una TX | `cliente_onboarding_service.py:111-145` | Imposible crear tenant sin EMP001; imposible bootstrap empresa sin tenant flow |
| **A2 — Nombre engañoso** | `MinimalErpTenantBootstrapService` crea **empresa**, no tenant | `minimal_erp_tenant_bootstrap_service.py:35-36` | Confusión de ownership |
| **A3 — Secuencias EMPRESA en tenant step** | 56/57 filas cfg dependen de `empresa_id` en paso tenant | `_insertar_secuencias_codigo:408-422` | Nueva empresa no recibe seed cfg automático |
| **A4 — Primera empresa hardcoded** | `EMP001` + `_get_primera_empresa_activa` | `minimal_erp_tenant_bootstrap_service.py:21,49-51,224-230` | Multi-empresa no modelado en bootstrap |
| **A5 — Perfil Dedicated mezcla scopes** | `tenant_seed_profiles` lista `seed_org_empresa` y `seed_codigo_secuencias` como pasos "tenant" | `tenant_seed_profiles.py:38-45,79-85` | Verificación `org_empresa≥1` en tenant seed |
| **A6 — Auth config paridad** | Shared paso 7; Dedicated omitido | `cliente_onboarding_service.py:140`; ausente en adapters | ADJ-07 |
| **A7 — Orquestador monolítico Shared** | `ClienteOnboardingService` conoce ERP, RBAC, auth, motor | Un solo método `:95-145` | Sin frontera tenant/empresa |
| **A8 — Repository ADMIN default** | `CfgCodigoSecuenciaRepository` sin session → ADMIN | `28_BOOTSTRAP_INTEGRATION_AUDIT.md` AI-X1 | Riesgo si caller Dedicated olvida `session=` |

---

## 4. Dependencias solo `cliente_id` (pregunta 7)

| Componente | Método | Tablas |
|------------|--------|--------|
| `ClienteOnboardingService` | `_insertar_cliente` | `cliente` |
| `ClienteOnboardingService` | `_insertar_roles_base` | `rol` |
| `OnboardingRbacService` | `activar_modulos_base_cliente` | `cliente_modulo` |
| `OnboardingRbacService` | `bootstrap_global_grants_admin_tenant` | `rol_permiso` |
| `OwnerSyncService` | `sync_modules_for_owner` | `rol_permiso`, `rol_menu_permiso` |
| `BaseOperativeService` | `apply_to_operative_roles` | `rol_permiso` |
| `ManagerStandardService` / `UserStandardService` | bundles | `rol_permiso`, `rol_menu_permiso` |
| `AuthConfigGateway` | `config_exists`, `insert_config` | `cliente_auth_config` |
| `PlatformRbacBootstrapService` | `bootstrap_platform_rbac` | `cliente_modulo`, `rol_permiso` |
| Secuencias CFG | scope TENANT (1 fila) | `cfg_codigo_secuencia` (`empresa_id=NULL`) |

---

## 5. Dependencias de `empresa_id` (pregunta 6)

| Componente | Método | Uso de `empresa_id` |
|------------|--------|---------------------|
| `MinimalErpTenantBootstrapService` | `ensure_empresa_inicial` | Crea PK `org_empresa` |
| `MinimalErpTenantBootstrapService` | `vincular_admin_empresa` | `usuario.empresa_default_id` |
| `ClienteOnboardingService` | `_insertar_usuario_admin` | Parámetro `empresa_id` → default usuario |
| `ClienteOnboardingService` | `_insertar_secuencias_codigo` | 56 inserts CFG scope EMPRESA |
| `CfgCodigoSecuenciaRepository` | `insert_secuencia` | Columna + fingerprint EMPRESA |
| `dedicated_tenant_seed_adapters` | `hydrate_tenant_seed_state` | Rehidrata desde `_get_primera_empresa_activa` |
| `tenant_seed_profiles` | `row_expectations` | Cuenta `org_empresa` |

---

## 6. Qué ejecutar solo al crear nueva empresa (pregunta 8) — AS-IS vs target

**Hoy se ejecuta solo en onboarding (primera empresa):**

- `ensure_empresa_inicial` (EMP001)
- 56 filas `cfg_codigo_secuencia` EMPRESA
- `vincular_admin_empresa` (admin)

**No existe hoy** un flujo separado para empresa N>1. Runtime ORG (fuera de bootstrap) crearía `org_empresa` vía módulo ERP — **sin** seed cfg documentado en bootstrap.

**Target conceptual (para etapa futura):** E1–E3 de `03_TENANT_VS_EMPRESA.md`.

---

## 7. Qué ejecutar una vez por tenant (pregunta 9)

Ver tabla T1–T7 en `03_TENANT_VS_EMPRESA.md` §4.

---

*Riesgos de separar: `05`. Resumen: `06`.*
