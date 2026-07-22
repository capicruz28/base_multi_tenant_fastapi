# F17B — Auditoría de integración del Motor de Códigos con el Bootstrap oficial

**Fase:** F17B — Integración con bootstrap (auditoría, solo documentación)
**Fecha:** 2026-07-03
**Base congelada:** F15–F17A + F17 Ola 0 (código existente)
**Alcance:** Verificar que el motor sea **una etapa más** del bootstrap y no un flujo paralelo. No se modifica código.

---

## 1. Componentes del bootstrap auditados

| Componente | Archivo | Rol |
|-----------|---------|-----|
| `ClienteOnboardingService` | `app/modules/tenant/application/services/cliente_onboarding_service.py` | Onboarding Shared (TX única ADMIN) |
| `MinimalErpTenantBootstrapService` | `.../minimal_erp_tenant_bootstrap_service.py` | Empresa sede + vínculo admin |
| `OnboardingRbacService` | `.../onboarding_rbac_service.py` | RBAC base del tenant |
| `DedicatedTenantSeedService` | `app/infrastructure/provisioning/dedicated_tenant_seed_service.py` | Orquestador seed Dedicated (por pasos + markers) |
| `dedicated_tenant_seed_adapters` | `.../dedicated_tenant_seed_adapters.py` | Ejecución de cada paso Dedicated (reusa onboarding) |
| `tenant_seed_profiles` | `.../tenant_seed_profiles.py` | Perfil de pasos + `row_expectations` |
| `onboarding_seed.py` | `app/core/codigo/onboarding_seed.py` | Subconjunto eager de secuencias (motor) |
| `SequenceCatalog` | `app/core/codigo/sequence_catalog.py` | Fuente única de metadatos (63 entradas) |
| `AllocationCoordinator.ensure_row` | `app/core/codigo/coordinator/...` | Lazy creation en runtime |
| `CfgSequenceStore` | `app/core/codigo/stores/cfg_sequence_store.py` | Store runtime (session-driven) |
| `CfgCodigoSecuenciaRepository` | `app/infrastructure/database/repositories/...` | Persistencia usada por el seed onboarding |

---

## 2. Cómo está integrado hoy (F17 Ola 0)

### 2.1 Shared — `ClienteOnboardingService.crear_cliente_con_onboarding`

Todo dentro de **una sola transacción** (`get_db_connection(ADMIN)` + `session.begin()`):

| Orden | Paso | Produce |
|-------|------|---------|
| 1 | `_insertar_cliente` | `cliente_id` |
| 2 | `_insertar_roles_base` | `admin_rol_id` |
| 3 | `MinimalErpTenantBootstrapService.ensure_empresa_inicial` | `empresa_id` (sede `EMP001`) |
| 4 | `_insertar_usuario_admin` | `usuario_id` |
| 5 | `vincular_admin_empresa` | admin tenant-wide |
| 6 | `OnboardingRbacService.bootstrap_cliente_rbac` | permisos/roles |
| 7 | `_insertar_auth_config_si_no_existe` | auth config |
| 8 | **`_insertar_secuencias_codigo(session, cliente_id, empresa_id)`** | **57 filas cfg** (1 TENANT + 56 EMPRESA sede; derivado del catálogo, F17D) |

**Hallazgo AI-S1:** el motor ya es el **paso 8**, dentro de la misma TX. No abre conexión propia ni crea flujo paralelo. ✅

### 2.2 Dedicated — `DedicatedTenantSeedService.run_tenant_seed`

Pasos declarados en `tenant_seed_profiles._TENANT_SEED_STEPS`, ejecutados por `execute_tenant_seed_step` sobre la **BD dedicada** (`provisioning_dedicated_session`):

| Orden | step_code | Reusa |
|-------|-----------|-------|
| 1 | `seed_base_roles` | `ClienteOnboardingService._insertar_roles_base` |
| 2 | `seed_org_empresa` | `MinimalErpTenantBootstrapService.ensure_empresa_inicial` |
| 3 | `seed_admin_user` | `ClienteOnboardingService._insertar_usuario_admin` |
| 4 | `seed_admin_empresa_link` | `MinimalErpTenantBootstrapService.vincular_admin_empresa` |
| 5 | `seed_tenant_rbac` | `OnboardingRbacService.bootstrap_cliente_rbac` |
| 6 | **`seed_codigo_secuencias`** | **`ClienteOnboardingService._insertar_secuencias_codigo`** |

**Hallazgo AI-D1:** Dedicated **reutiliza exactamente** las mismas funciones de onboarding; el motor es el **paso 6**. No hay duplicación de lógica de seed entre Shared y Dedicated. ✅

**Hallazgo AI-D2:** el paso 6 exige `empresa_id` (validación `TENANT_SEED_SECUENCIAS_PREREQ`) y en re-ejecución lo rehidrata vía `_get_primera_empresa_activa` (`hydrate_tenant_seed_state`). Idempotente y resumible por markers `bootstrap_applied`. ✅

### 2.3 Runtime — lazy creation

Fuera del onboarding, `AllocationCoordinator.ensure_row` → `CfgSequenceStore.ensure_row` crea la fila faltante con defaults del `SequenceCatalog`, **usando la sesión del UoW del servicio ERP** (nunca abre conexión propia).

**Hallazgo AI-R1:** el store runtime es **session-driven** y agnóstico de ubicación física; sigue el store del módulo invocador (TA-06). ✅

---

## 3. Ubicación física de `cfg_codigo_secuencia` (Shared vs Dedicated)

| Modo | Onboarding escribe en | Runtime lee/crea en | ¿Misma BD? |
|------|----------------------|---------------------|------------|
| **Shared (single-DB)** | Sesión `ADMIN` (BD única) | UoW ERP `DEFAULT` (misma BD única) | ✅ Sí |
| **Dedicated** | `provisioning_dedicated_session` (BD del tenant) | UoW ERP `DEFAULT` → BD del tenant (routing) | ✅ Sí |

`cfg_codigo_secuencia` está en `DEDICATED_RUNTIME_REQUIRED_TABLES` (confirmado en `test_f12_g3`), por lo que existe físicamente en la BD dedicada. En Shared vive en la BD única.

**Hallazgo AI-X1 (riesgo latente INC-09):** `CfgCodigoSecuenciaRepository` fija `connection_type=DatabaseConnection.ADMIN` para su **ruta sin `session`**. En Dedicated, un caller que use el repositorio **sin pasar sesión** apuntaría al control-plane (que **no** tiene el cfg del tenant). El onboarding evita esto porque **siempre** pasa `session=`. El motor en runtime lo evita porque usa `CfgSequenceStore` con la sesión del UoW. ⚠️ Debe blindarse antes de ORG/INV (ver `31`).

---

## 4. Respuestas explícitas a la auditoría

### 4.1 ¿El nuevo bootstrap del motor duplica responsabilidades?

**Parcialmente, solo en datos de configuración — no en flujo.**

- ✅ **Flujo:** no hay bootstrap paralelo; el seed es un paso más (Shared paso 8, Dedicated paso 6) y reutiliza las funciones existentes.
- ⚠️ **Datos:** `onboarding_seed.py` **re-declara** `prefijo`, `longitud_numero`, `separador` y `scope_type` que **ya viven en el `SequenceCatalog`**. Es una duplicación de valores que puede divergir (mismo prefijo definido en dos lugares).

### 4.2 ¿Puede simplificarse reutilizando el bootstrap existente?

**Sí, y ya lo hace en gran medida.** El seed Shared y Dedicated invocan la **misma** `_insertar_secuencias_codigo`. La simplificación pendiente es de **datos**: que `onboarding_seed.py` **derive** los defaults del `SequenceCatalog` en lugar de re-declararlos (ver `31` ADJ-01).

### 4.3 ¿Existen pasos redundantes?

- **En el orquestador:** no. Cada paso produce artefactos distintos.
- **Conceptual:** las 56 secuencias EMPRESA del eager (F17D) **también** se crearían lazy al primer uso. El eager es una conveniencia (el admin ve todos los prefijos configurables de inmediato), no una redundancia dañina. Se conserva por UX; criterio en `bootstrap/03` §2.

### 4.4 ¿La secuencia de ejecución es la correcta?

**Sí.** El seed de secuencias es el **último** paso en ambos modos, después de crear la empresa sede (necesita `empresa_id` para las secuencias EMPRESA-scoped y `NULL` para `org_empresa` TENANT). Dependencias respetadas: cliente → roles → empresa → usuario → vínculo → RBAC → (auth config) → secuencias.

### 4.5 ¿Existen riesgos para futuras ampliaciones?

| Riesgo | Detalle | Mitigación (`31`) |
|--------|---------|-------------------|
| Drift catálogo↔seed | Prefijos duplicados en dos archivos | ADJ-01 derivar del catálogo |
| INC-09 repo ADMIN | Ruta sin sesión apunta control-plane en Dedicated | ADJ-03 blindar repo a onboarding/UoW |
| Alta de empresa posterior | Solo la sede recibe eager; nuevas empresas dependen de lazy | ADJ-04 documentar/hook provisioning |
| Ampliar eager | ~~Requiere editar 3 lugares~~ **Resuelto (F17D):** el eager se **deriva** del catálogo (store CFG + scope TENANT/EMPRESA); agregar una CFG resoluble la incorpora automáticamente | ADJ-05 (superado por criterio F17D) |
| Paridad auth_config | Shared llama `_insertar_auth_config`; el perfil Dedicated no lista ese paso | ADJ-07 verificar paridad (fuera motor) |

### 4.6 ¿Qué partes deben permanecer en el bootstrap existente?

- Creación de `cliente`, `org_empresa`, `usuario` admin, roles, RBAC, auth config.
- Gestión de **transacción** (Shared: TX única; Dedicated: pasos + markers + `row_expectations`).
- **Invocación** del paso de secuencias y el `empresa_id` de contexto.
- Idempotencia/resumibilidad del onboarding.

### 4.7 ¿Qué partes deben pertenecer exclusivamente al Motor?

- `SequenceCatalog` (metadatos: prefijo, padding, scope, policy, family).
- `compute_scope_fingerprint`.
- `CodeFormatter` / `CodeParser` / `CodeValidator`.
- `allocate` / `preview` / `align` y `ensure_row` (lazy).
- **El bootstrap NO debe conocer prefijo/padding**: debe pedírselos al catálogo/motor.

---

## 5. Veredicto de la auditoría

| Criterio | Resultado |
|----------|-----------|
| ¿Flujo único de onboarding (Shared + Dedicated)? | ✅ Sí |
| ¿El motor es una etapa del bootstrap, no un flujo paralelo? | ✅ Sí |
| ¿Reutiliza el bootstrap existente? | ✅ Sí (misma función en ambos modos) |
| ¿Duplicación de responsabilidades de flujo? | ✅ No |
| ¿Duplicación de datos de configuración? | ✅ Resuelto en F17C (ADJ-01: `onboarding_seed` deriva del catálogo) |
| ¿Riesgo de ubicación física (INC-09)? | ✅ Blindado en F17C (ADJ-03: escritura exige sesión) |
| ¿Bloquea el inicio de ORG/INV? | ❌ No — ajustes son de robustez, no arquitectura |

**Conclusión:** la integración es **correcta en flujo**; quedan **ajustes de robustez** (deduplicar datos y blindar el repositorio) documentados en `31`, no bloqueantes para arquitectura.

---

*Flujos detallados en `29`. Matriz de responsabilidades en `30`. Ajustes en `31`. Aprobación en `32`.*
