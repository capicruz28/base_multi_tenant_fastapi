# 39 — F17 Diff Analysis (Diff funcional por archivo)

> Fase **F17G** — auditoría forense. Solo lectura. Para cada archivo modificado
> por F17: **qué cambió**, **por qué cambió**, **qué dependencias tiene** y
> **si toca el camino RBAC/estado** donde se observan los errores.

Fuente: `git diff HEAD` (todos los cambios F17 son no commiteados sobre `72ebaa1`).

---

## A. Archivos rastreados modificados por F17

### A.1 `app/bootstrap_v2/01_schema/V010__tablas_bd_erp_completo.sql`

**Qué cambió** — Reescritura de `CREATE TABLE cfg_codigo_secuencia` (≈ línea 6809):

- Columnas nuevas: `sequence_key`, `scope_type`, `scope_fingerprint`,
  `almacen_id`, `punto_venta_id`, `numero_inicial`, `fecha_creacion`,
  `fecha_actualizacion`, `usuario_actualizacion_id`.
- Se elimina `entidad`; `prefijo` pasa de `NVARCHAR(5)` a `NVARCHAR(10)`.
- **Constraints nuevas**: `UQ_cfg_scope`, `CK_cfg_scope_type`, `CK_cfg_numeros`,
  `CK_cfg_prefijo_len`, y **3 FKs nuevas**:
  - `FK_cfg_empresa → org_empresa(empresa_id)`
  - `FK_cfg_almacen → inv_almacen(almacen_id)`
  - `FK_cfg_punto_venta → pos_punto_venta(punto_venta_id)`
- Índices nuevos: `IDX_cfg_cliente_activo`, `IDX_cfg_empresa`, `IDX_cfg_almacen`.

**Por qué cambió** — Materializar el modelo de scopes del Motor de Generación de
Códigos (OLA‑0).

**Dependencias / impacto**

- V010 se aplica en **S4/S5 (APPLY_SCHEMA_ERP)** del provisioning Dedicated.
- Las 3 FKs nuevas referencian `org_empresa` (V010:156), `inv_almacen` (V010:746)
  y `pos_punto_venta` (V010:5154). Las tres tablas se crean **antes** de
  `cfg_codigo_secuencia` (V010:6809) → **el `CREATE TABLE` es válido**; V010 se
  aplica sin fallo por estas FKs. (Descartado como causa directa de `FK_permiso_menu`.)
- **Efecto real de este cambio**: cambia el SHA‑256 del archivo
  (`78733886… → 5f81e8c3…`). Ese es el eje de F17E/F17F.
- **No** toca `modulo_menu` ni `rol_menu_permiso` (no existen en V010; solo en
  V020 dedicado).

### A.2 `app/infrastructure/database/tables.py`

**Qué cambió** — `CfgCodigoSecuenciaTable` (≈ líneas 744‑780) alineada 1:1 con la
nueva `cfg_codigo_secuencia` (mismas columnas/constraints que A.1).

**Por qué** — Mantener el ORM sincronizado con el DDL.

**Dependencias** — ORM SQLAlchemy de `cfg_codigo_secuencia`. **No** modifica las
tablas `modulo_menu`, `rol_menu_permiso`, `permiso`, `rol`, `usuario`,
`provisioning_run`, `provisioning_step`. Sin impacto sobre el camino RBAC/estado.

### A.3 `app/infrastructure/database/repositories/cfg_codigo_secuencia_repository.py`

**Qué cambió** (F17C) — Endurecimiento de escrituras: nueva firma de
`insert_secuencia` (`sequence_key`, `scope_type`, `empresa_id`, `almacen_id`,
`punto_venta_id`, `numero_inicial`, `scope_fingerprint`), guard
`_assert_write_session` que exige `AsyncSession` explícita
(`ServiceError CFG_SECUENCIA_WRITE_REQUIRES_SESSION`).

**Por qué** — Fuente única + no permitir escrituras sin sesión/UoW.

**Dependencias** — Consumido por `ClienteOnboardingService._insertar_secuencias_codigo`
(A.4) y por el motor. **Solo** afecta a `cfg_codigo_secuencia`. Se ejecuta en el
sub‑paso S7 `seed_codigo_secuencias`, **posterior** a `seed_tenant_rbac`.

### A.4 `app/modules/tenant/application/services/cliente_onboarding_service.py`

**Qué cambió** (F17C/F17D):

- Elimina la lista literal `SECUENCIAS_CODIGO` (9 entradas) y la **importa** de
  `app.core.codigo.onboarding_seed` (fuente única).
- `_insertar_secuencias_codigo(session, cliente_id)` → **añade** parámetro
  `empresa_id`; itera `ONBOARDING_SEQUENCE_SEEDS` (57) y setea `empresa_id` solo
  cuando `scope_type != TENANT`.
- Nuevo import `from app.core.codigo.enums import ScopeType`.

**Por qué** — Sembrar 57 secuencias CFG (criterio F17D) desde el catálogo.

**Dependencias**

- Introduce acoplamiento de **import** a `app.core.codigo.*` en el módulo de
  onboarding (y transitivamente en `dedicated_tenant_seed_adapters.py`, que
  importa `SECUENCIAS_CODIGO` desde aquí). Los tests (107) confirman que el
  import resuelve sin error → no hay ImportError en runtime.
- El cambio afecta **exclusivamente** al sub‑paso S7 `seed_codigo_secuencias`
  (posterior a `seed_tenant_rbac`). **No** toca RBAC ni catálogos.

### A.5 `app/infrastructure/provisioning/dedicated_tenant_seed_adapters.py`

**Qué cambió** (F17D) — En `execute_tenant_seed_step`, rama
`seed_codigo_secuencias` (líneas 189‑200): valida `state.empresa_id`
(`ValidationError TENANT_SEED_SECUENCIAS_PREREQ`) y pasa `state.empresa_id` a
`_insertar_secuencias_codigo`.

**Por qué** — La siembra EMPRESA‑scope necesita `empresa_id`.

**Dependencias / límite exacto del cambio**

- **Solo** la rama `seed_codigo_secuencias`.
- La rama `seed_tenant_rbac` (líneas 174‑187), que invoca
  `OnboardingRbacService.bootstrap_cliente_rbac` (origen de `FK_permiso_menu`),
  **no fue tocada por F17** (idéntica a `HEAD`).

### A.6 `app/infrastructure/provisioning/tenant_seed_profiles.py`

**Qué cambió** (F17C/F17D) — `_row_expectations_for_profile`:
`("cfg_codigo_secuencia", len(SECUENCIAS_CODIGO))` →
`("cfg_codigo_secuencia", len(EAGER_SEQUENCE_KEYS))`; import de
`EAGER_SEQUENCE_KEYS` desde `app.core.codigo.onboarding_seed`.

**Por qué** — La verificación post‑seed pasa de esperar 9 a esperar 57 filas.

**Dependencias / impacto** — Alimenta `DedicatedTenantSeedService._verify_row_expectations`
(S7, **después** de ejecutar todos los sub‑pasos). Si el seed no llegara a crear
57 filas, el error sería `TENANT_SEED_ROW_COUNT_FAILED` — **distinto** de
`FK_permiso_menu`. No toca RBAC.

### A.7 `app/infrastructure/provisioning/script_manifest.py`

**Qué cambió** (F17F) — 1 línea:
`_V010_ERP_SHA256 = "5f81e8c3…"` (antes `"78733886…"`).

**Por qué** — Realinear el checksum congelado con el nuevo V010 (A.1) para que
`validate_manifest_integrity` (S4) vuelva a pasar.

**Dependencias / impacto** — Es el cambio que **re‑abre** S4 → la saga vuelve a
alcanzar S6/S7. No modifica orden, transacciones ni RBAC.

### A.8 `tests/unit/test_f4_07_dedicated_tenant_seed_service.py`

**Qué cambió** (F17C) — Import y `row_counts` usan `len(EAGER_SEQUENCE_KEYS)`.
Test; sin efecto en runtime de onboarding.

---

## B. Archivos NO modificados por F17 pero situados en el camino del fallo

> Evidencia: ausentes de `git diff HEAD`; `git log -1` los sitúa en commits
> pre‑F17 (`469af23` / `ecb640d` / `72ebaa1`).

| Archivo | Rol en el fallo | Último commit |
|---|---|---|
| `onboarding_rbac_service.py` | `bootstrap_cliente_rbac` → inserta `rol_menu_permiso` | `469af23` |
| `manager_standard_service.py` / `user_standard_service.py` | bundles `rol_menu_permiso` (envueltos en try/except) | `469af23` |
| `owner_sync_service.py` / `base_operative_service.py` | inserts `rol_menu_permiso` (NO envueltos) | `469af23` |
| `dedicated_catalog_seed_service.py` | S6, aplica catálogos (incl. `modulo_menu`) | `72ebaa1` |
| `catalog_profiles.py` | perfil S6 (incluye `catalog_s010`); `row_expectations` sin `modulo_menu` | `72ebaa1` |
| `S010__seed_modulo_menu_completo.sql` | siembra `modulo_menu` | `ecb640d` |
| `V020__tenant_identity_rbac_store.sql` | define `FK_permiso_menu` (dedicado) | `72ebaa1` |
| `dedicated_provisioning_orchestrator.py` | saga, `_fail_step_and_run`, reconciliación | `72ebaa1` |
| `tenant_provisioning_state_service.py` | guard `PROVISIONING_RUN_NOT_ACTIVE` (línea 485) | `72ebaa1` |
| `dedicated_provisioning_compensation_service.py` | retry `failed→provisioning` | `72ebaa1` |
| `provisioning_step_code.py` | `SAGA_STEP_ORDER` (orden S6 antes de S7) | pre‑F17 |
| `bootstrap_applied_reader.py` | `list_applied_script_codes` (lee `bootstrap_applied`) | `72ebaa1` |

**Conclusión de la sección B**: todo el código que **emite** `FK_permiso_menu` y
`PROVISIONING_RUN_NOT_ACTIVE` está en la columna "NO modificado por F17". El único
nexo F17 es de **alcanzabilidad** (A.1 + A.7), no de modificación de esas rutas.
