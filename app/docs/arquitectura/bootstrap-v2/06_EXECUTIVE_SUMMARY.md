# 06 — Resumen ejecutivo (auditoría bootstrap-v2)

**Etapa:** Auditoría arquitectónica — preparación separación Platform / Tenant / Empresa  
**Fecha:** 2026-07-09  
**Estado:** Solo documentación. **Sin implementación. Sin refactors propuestos.**

---

## Respuestas a las 12 preguntas (con evidencia)

### 1. ¿Qué responsabilidades tiene actualmente Platform Bootstrap?

| Ámbito | Responsabilidades | Evidencia |
|--------|-------------------|-----------|
| **Instalación SQL** | DDL CP/ERP (`V010`–`V030`); catálogos globales (`S010`–`S020`) | `bootstrap_v2/`; `BootstrapScriptRunner` Dedicated S4/S5 |
| **Startup** | Sync `PermissionRegistry` → `permiso` | `permission_startup.py`; `main.py` lifespan |
| **CLI platform** | Cliente superadmin, rol `ADMIN_PLATFORM`, usuario, auth config, módulo `SYS_ADMIN`, grants CP | `PlatformBootstrapService` → `PlatformIdentityBootstrapService` + `PlatformRbacBootstrapService` |
| **Auditoría** | Snapshot readiness platform | `audit_platform_ready` |

**No incluye:** creación de tenants operativos ni `org_empresa`. Ver `01` §2, `02` R01–R06.

---

### 2. ¿Qué responsabilidades tiene actualmente Tenant Bootstrap?

**Shared** — `ClienteOnboardingService.crear_cliente_con_onboarding` (8 pasos, TX única ADMIN):

1. `cliente` · 2. roles base · 3. **`org_empresa`** · 4. admin · 5. **vínculo empresa** · 6. RBAC · 7. auth config · 8. **`cfg_codigo_secuencia` (57 filas)**

**Dedicated** — CP: solo `cliente` + saga; **S7** replica pasos 2–8 (sin auth config) vía `DedicatedTenantSeedService` + adapters.

**Incluye indebidamente (mezcla):** pasos 3, 5 y 56 filas EMPRESA del paso 8. Ver `03` §2.

---

### 3. ¿Qué responsabilidades realmente pertenecen a Empresa Bootstrap?

| ID | Responsabilidad | Componente actual |
|----|-----------------|-------------------|
| E1 | Crear `org_empresa` | `MinimalErpTenantBootstrapService.ensure_empresa_inicial` |
| E2 | Preferencia login admin por empresa | `vincular_admin_empresa` |
| E3 | Secuencias CFG scope EMPRESA (56 filas / empresa) | `_insertar_secuencias_codigo` (subset EMPRESA) |
| E4 | Lazy ALMACEN/PV (runtime, no onboarding) | `AllocationCoordinator.ensure_row` |

**Hoy no existe capa nombrada "Empresa Bootstrap"** — estas responsabilidades se ejecutan dentro del Tenant Bootstrap. Ver `03` §3.

---

### 4. ¿Qué componentes ya son reutilizables?

**Sí — lista completa en `04` §1.** Destacados:

- `_insertar_roles_base`, `_insertar_usuario_admin`, `_insertar_secuencias_codigo`
- `ensure_empresa_inicial`, `vincular_admin_empresa`
- `bootstrap_cliente_rbac`, `AuthConfigGateway`
- `ONBOARDING_SEQUENCE_SEEDS` / `SequenceCatalog`

Dedicated S7 **ya reutiliza** los mismos métodos (`dedicated_tenant_seed_adapters.py:123-199`; audit `28` AI-D1).

---

### 5. ¿Qué componentes están acoplados incorrectamente?

Ver `04` §3. Principales:

- **A1:** Empresa embebida en `crear_cliente_con_onboarding` (`cliente_onboarding_service.py:111-145`)
- **A3:** 56 cfg EMPRESA en paso tenant
- **A4:** Asunción EMP001 / primera empresa única
- **A6:** Auth config Dedicated omitido (ADJ-07)
- **A7:** Orquestador monolítico Shared

---

### 6. ¿Qué componentes dependen de `empresa_id`?

`ensure_empresa_inicial`, `vincular_admin_empresa`, `_insertar_usuario_admin` (default), `_insertar_secuencias_codigo` (56 filas), `CfgCodigoSecuenciaRepository.insert_secuencia` (scope EMPRESA), hydrate Dedicated. Tabla completa: `04` §5.

---

### 7. ¿Qué componentes dependen solamente de `cliente_id`?

`_insertar_cliente`, `_insertar_roles_base`, RBAC (`cliente_modulo`, bundles), `AuthConfigGateway`, secuencia CFG TENANT (1 fila), Platform RBAC. Tabla completa: `04` §4.

---

### 8. ¿Qué debería ejecutarse únicamente al crear una nueva empresa?

**Target conceptual:** E1–E3 (`org_empresa`, cfg EMPRESA×56, preferencia usuario si aplica).

**AS-IS:** solo ocurre en onboarding tenant (EMP001). **No hay** flujo para empresa N>1. Ver `04` §6.

---

### 9. ¿Qué debería ejecutarse únicamente una vez por Tenant?

T1–T7: `cliente`, roles base, admin, RBAC, auth config, 1 cfg TENANT, provisioning Dedicated. Ver `03` §4.

---

### 10. ¿Qué podría reutilizarse Shared y Dedicated?

Todo el seed Python de pasos 2–8 (excepto auth config en Dedicated hoy). Mecanismo: métodos estáticos + `session` explícita. Ver `04` §2.

---

### 11. ¿Existe código que asuma una única empresa?

**Sí.** Evidencia:

- `CODIGO_EMPRESA_INICIAL = "EMP001"` (`minimal_erp_tenant_bootstrap_service.py:21`)
- `_get_primera_empresa_activa` + idempotencia "si existe, no crear" (`:49-51`, `:224-230`)
- Un solo `empresa_id` en onboarding (`cliente_onboarding_service.py:116,143-144`)
- Docstring "una org_empresa" (`minimal_erp_tenant_bootstrap_service.py:2-4`)

**Excepción:** RBAC grants usan `empresa_id=NULL` (tenant-wide) — no asumen single-company para permisos.

---

### 12. ¿Qué riesgos existirían al separar Bootstrap Tenant y Empresa Bootstrap?

Doce riesgos inventariados en `05` (R-T1–R-T12). Críticos:

- **Orden FK** cfg ↔ org_empresa (R-T1)
- **Atomicidad TX Shared** (R-T2)
- **Markers y row_expectations Dedicated** (R-T3, R-T4)
- **Admin sin default si tenant corre primero** (R-T5)
- **Multi-empresa sin hook ORG→cfg** (R-T11)

---

## Conclusión arquitectónica (AS-IS)

1. **Platform Bootstrap** está **razonablemente separado** (CLI + SQL + startup).
2. **Tenant Bootstrap** concentra responsabilidades de **tenant y primera empresa** en un solo flujo monolítico (Shared TX única; Dedicated S7 con reutilización intencional).
3. **Empresa Bootstrap** no existe como capa — sus responsabilidades están **embebidas** en tenant onboarding y **hardcoded** a EMP001 / primera empresa.
4. La base de **reutilización** (métodos estáticos compartidos Shared/Dedicated) es sólida; el **acoplamiento** está en el **orquestador** y en el **momento** de ejecución, no en la lógica de bajo nivel.
5. Separar capas es **viable** pero con riesgos transaccionales, de paridad Dedicated y multi-empresa documentados en `05`.

---

## Entregables generados

| Documento | Contenido |
|-----------|-----------|
| `01_BOOTSTRAP_AS_IS.md` | Inventario flujos Platform / Shared / Dedicated |
| `02_RESPONSIBILITY_MATRIX.md` | Matriz R01–R20 Platform / Tenant / Empresa |
| `03_TENANT_VS_EMPRESA.md` | Mezcla actual vs target conceptual |
| `04_REUSABLE_COMPONENTS.md` | Reutilización, acoplamientos, dependencias scope |
| `05_RISKS_AND_GAPS.md` | Riesgos separación + gaps ADJ-07, multi-empresa |
| `06_EXECUTIVE_SUMMARY.md` | Este documento |

---

## Próximo paso (fuera de alcance)

Esperar **revisión arquitectónica** antes de definir diseño target (Platform / Tenant / Empresa) o implementación.

**Confirmación:** no se modificó código, SQL, migraciones, tests ni contratos en esta etapa.
