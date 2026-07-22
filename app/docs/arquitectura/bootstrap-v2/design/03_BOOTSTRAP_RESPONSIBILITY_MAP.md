# 03 — Bootstrap V2: Mapa de responsabilidades definitivas

**Etapa:** Diseño TO-BE — respuestas a preguntas 1–6, 9–10

---

## 1. Platform Bootstrap — división oficial

| Subdominio | Responsabilidades | Frecuencia |
|------------|-------------------|------------|
| **P-SCH** Schema global | DDL CP + ERP vacío (`V010`–`V030`) | 1× instalación |
| **P-CAT** Catálogo global | `permiso`, `modulo`, `modulo_menu` (`S010`–`S020`) | 1× instalación |
| **P-SYNC** Sync runtime | `permission_sync` en startup | Cada arranque |
| **P-ID** Identidad platform | Cliente superadmin, rol `ADMIN_PLATFORM`, usuario, auth config | 1× CLI |
| **P-RBAC** RBAC platform | Módulo `SYS_ADMIN`, grants CP | 1× CLI |
| **P-AUD** Auditoría | `audit_platform_ready` | On-demand |

**Exclusiones explícitas:** `cliente` operativo SaaS, `org_empresa`, RBAC tenant, cfg por tenant, provisioning Dedicated.

**Excepción DA-04-E1 — componentes RBAC compartidos:** ciertos componentes de RBAC (`OnboardingRbacService`, `permission_sync`, catálogo `permiso`/`modulo_menu`) son **compartidos** entre Platform y Tenant Bootstrap. Platform los inicializa globalmente (P-CAT, P-SYNC); Tenant los consume en onboarding (T-RBAC). Esto **no viola** el aislamiento DA-04: Platform no orquesta onboarding tenant; Tenant no modifica catálogos globales. La frontera es **ownership de escritura**, no duplicación de lectura.

---

## 2. Tenant Bootstrap — división oficial

| Subdominio | Responsabilidades | Frecuencia |
|------------|-------------------|------------|
| **T-REG** Registro tenant | INSERT `cliente` | 1× por tenant |
| **T-ROL** Roles sistema | `ADMIN_TENANT`, `MANAGER_TENANT`, `USER_TENANT` | 1× por tenant |
| **T-USR** Usuario admin inicial | INSERT `usuario`, `usuario_rol` (tenant-wide) | 1× por tenant |
| **T-RBAC** RBAC tenant | Plan modules, OwnerSync, bundles (BASE/MANAGER/USER) | 1× por tenant |
| **T-AUTH** Auth config | `cliente_auth_config` (CP) | 1× por tenant |
| **T-CFG-T** Secuencia TENANT | 1 fila `cfg_codigo_secuencia` scope TENANT | 1× por tenant |
| **T-ORCH** Orquestación | Coordinar T-* + invocar Empresa Bootstrap | 1× por tenant |
| **T-DED** Provisioning Dedicated | Saga S1–S10 wrapper (Dedicated only) | 1× por tenant dedicated |
| **T-DED-CAT** Catálogo Dedicated S6 | Seed SQL `permiso`, `modulo_menu` en BD tenant vacía | 1× por tenant dedicated (paso S6) |

**Owner S6 Dedicated Catalog (T-DED-CAT):** `DedicatedCatalogSeedService` invocado por saga paso S6 vía `BootstrapScriptRunner`. Responsabilidad: ejecutar scripts catálogo tenant-local (`S010`–`S020` subset) sobre BD dedicada recién creada. **No es** Tenant Bootstrap seed ERP (eso es S7). **No es** Platform Bootstrap (catálogo global CP ya existe). Orquestador saga (T-DED) invoca; servicio ejecuta.

**Exclusiones explícitas (pasan a Empresa Bootstrap):** creación `org_empresa`, cfg EMPRESA×56, preferencia `empresa_default_id` admin.

---

## 3. Empresa Bootstrap — división oficial

| Subdominio | Responsabilidades | Frecuencia |
|------------|-------------------|------------|
| **E-ORG** Organización | INSERT/ensure `org_empresa` | 1× por empresa |
| **E-LNK** Preferencias usuario | `usuario.empresa_default_id` (cuando aplica) | Por vínculo admin o runtime |
| **E-CFG** Secuencias EMPRESA | 56 filas `cfg_codigo_secuencia` scope EMPRESA | 1× por empresa |
| **E-IDEM** Idempotencia | Reutilizar empresa existente si aplica | Por invocación |

**Exclusiones explícitas:** roles tenant, RBAC, auth config, secuencia TENANT, registro `cliente`.

---

## 4. Matriz responsabilidad → capa (definitiva V2)

| ID | Responsabilidad | Platform | Tenant | Empresa |
|----|-----------------|----------|--------|---------|
| R01 | DDL esquema | ● | ○ | ○ |
| R02 | Catálogo permiso/menu global | ● | ○ | ○ |
| R03 | Identidad superadmin | ● | — | — |
| R04 | RBAC platform | ● | — | — |
| R05 | Registro `cliente` | — | ● | — |
| R06 | Roles base tenant | — | ● | — |
| R07 | Usuario admin | — | ● | — |
| R08 | RBAC tenant + bundles | — | ● | — |
| R09 | Auth config tenant | — | ● | — |
| R10 | cfg TENANT (1 fila) | — | ● | — |
| R11 | Orquestación onboarding | — | ● | — |
| R12 | Provisioning Dedicated saga | — | ● | — |
| R12a | Catálogo Dedicated S6 (T-DED-CAT) | — | ● | — |
| R13 | `org_empresa` | — | ○ | ● |
| R14 | Preferencia admin↔empresa | — | ○ | ● |
| R15 | cfg EMPRESA (56 filas) | — | ○ | ● |
| R16 | Metadatos secuencia (motor) | ○ | ○ | ○ |

● = owner · ○ = colabora / prerequisito · — = no participa

---

## 5. Responsabilidades que **dejan** Tenant Bootstrap → Empresa Bootstrap

| AS-IS (en Tenant) | TO-BE (Empresa Bootstrap) | Motivo |
|-------------------|---------------------------|--------|
| `ensure_empresa_inicial` | E-ORG | Crea entidad empresa, no tenant |
| `vincular_admin_empresa` | E-LNK | Artefacto de preferencia por empresa |
| 56 filas cfg scope EMPRESA en `_insertar_secuencias_codigo` | E-CFG | Counter por `empresa_id` |
| Lógica EMP001 / primera empresa | E-ORG (modo `INITIAL`) | Reutilizable para empresa N |

**Permanece en Tenant Bootstrap:** invocación automática de Empresa Bootstrap en el momento correcto del flujo.

---

## 6. Responsabilidades **exclusivas** de Tenant Bootstrap

| Responsabilidad | Razón de exclusividad |
|-----------------|----------------------|
| Registro `cliente` | Define el tenant |
| Roles `*_TENANT` | Scope tenant-wide (`empresa_id=NULL`) |
| Usuario admin | Identidad tenant inicial |
| RBAC plan + bundles | `cliente_modulo`, grants sin `empresa_id` |
| Auth config | Config CP por `cliente_id` |
| 1 fila cfg TENANT | Counter global tenant |
| Orquestación TX / saga | Atomicidad onboarding |
| Dedicated S1–S6, S8–S10 | Infraestructura no-empresa |

---

## 7. Componentes reutilizables **sin modificaciones** (pregunta 9)

En fase incremental inicial, estos componentes pueden **delegarse tal cual** detrás de facades V2:

| Componente AS-IS | Uso V2 |
|------------------|--------|
| `PlatformIdentityBootstrapService` | Platform Bootstrap (sin cambio) |
| `PlatformRbacBootstrapService` | Platform Bootstrap (sin cambio) |
| `OnboardingRbacService.bootstrap_cliente_rbac` | Tenant T-RBAC |
| `OnboardingRbacService.activar_modulos_base_cliente` | Tenant + Platform subset |
| `AuthConfigGateway` | Tenant T-AUTH |
| `SequenceCatalog` / `onboarding_seed.py` | Motor — metadatos |
| `CfgCodigoSecuenciaRepository.insert_secuencia(session=...)` | Tenant T-CFG-T + Empresa E-CFG |
| `DedicatedProvisioningOrchestrator` | Tenant T-DED wrapper |
| `BootstrapScriptRunner` / `DedicatedCatalogSeedService` | Platform/DB provision Dedicated |

---

## 8. Componentes que se convierten en **orquestadores** (pregunta 10)

| Componente AS-IS | Rol V2 |
|------------------|--------|
| `ClienteOnboardingService.crear_cliente_con_onboarding` | **Tenant Bootstrap Orchestrator (Shared)** — delega, no implementa E-* |
| `DedicatedTenantSeedService.run_tenant_seed` | **Tenant Bootstrap Orchestrator (Dedicated S7)** |
| `dedicated_tenant_seed_adapters.execute_tenant_seed_step` | Router interno → Tenant/Empresa facades |
| `PlatformBootstrapService` | **Platform Bootstrap Orchestrator** (ya lo es) |

**Dejan de ser orquestadores mixtos (pasan a Empresa Bootstrap facade):**
- `MinimalErpTenantBootstrapService` → lógica E-ORG + E-LNK (invocada, no orquestada por sí misma en onboarding)

---

## 9. Servicios nuevos — solo conceptual (pregunta 11)

| Servicio | Responsabilidad | Público |
|----------|-----------------|---------|
| `EmpresaBootstrapService` | Facade E-ORG, E-LNK, E-CFG | **Interno** |
| `TenantBootstrapOrchestrator` (Shared) | Secuencia T1–T7 + invocaciones E | Interno (detrás de `ClienteOnboardingService`) |
| `TenantBootstrapOrchestrator` (Dedicated) | Secuencia S7 sub-pasos | Interno (detrás de `DedicatedTenantSeedService`) |
| `BootstrapExtensionRegistry` | Registro plug-ins dominio | Interno (futuro) |

**No se crean endpoints nuevos** para estos servicios en onboarding inicial.

---

## 10. Consumidores secundarios de Empresa Bootstrap

Además del onboarding inicial (Tenant Bootstrap modo `INITIAL`), `EmpresaBootstrapService` puede ser invocado por:

| Consumidor | Modo | Contexto |
|------------|------|----------|
| **Repair scripts** | `ENSURE` | Soporte operacional: re-seed cfg EMPRESA faltante, verificar EMP001 |
| **Redispatch saga** | `ENSURE` | Re-ejecución idempotente sub-paso S7 Dedicated tras fallo parcial |
| **Legacy repair** | `ENSURE` | Scripts one-off migración/reparación tenants pre-V2 |

**Reglas consumidores secundarios:**

| Regla | Descripción |
|-------|-------------|
| CS-01 | Nunca invocan modo `INITIAL` en tenant ya onboarded (riesgo duplicación) |
| CS-02 | Deben propagar `session` existente (P2) |
| CS-03 | No alteran contratos API ni UX |
| CS-04 | Idempotencia obligatoria (modo `ENSURE`) |
| CS-05 | Fuera alcance Fases 1–4 salvo wiring explícito en script existente |

---

*Extensión multi-empresa y dominio: `04`. Estrategia incremental: `05`.*
