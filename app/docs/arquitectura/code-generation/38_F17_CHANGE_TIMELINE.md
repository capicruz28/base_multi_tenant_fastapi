# 38 — F17 Change Timeline (Línea temporal de cambios)

> Fase **F17G** — auditoría forense. Documento de solo lectura. No se modificó código.
> Objetivo de este archivo: enumerar **exactamente** qué cambió en cada sub‑fase de F17.

## 0. Método

La totalidad del trabajo F17 vive como **cambios NO commiteados sobre `HEAD`**
(no hubo commits en ninguna sub‑fase, por instrucción explícita del usuario).
Por tanto, el conjunto completo de cambios F17 es reproducible con:

```
git diff --stat HEAD          # archivos rastreados modificados por F17
git status --porcelain        # archivos nuevos (untracked) creados por F17
```

`HEAD` = `72ebaa1  2026-07-03  "bd shared/dedicated completado"`.

Ese commit ya contenía **todo** el stack de provisioning Dedicated
(orchestrator, catalog seed, tenant seed, state service, runner, manifest, V020,
compensación). Es decir: el "estado funcional anterior" que el usuario describe
= árbol de trabajo en `72ebaa1` **sin** los cambios F17.

## 1. Conjunto completo de cambios F17 (evidencia `git`)

### Archivos rastreados modificados por F17 (`git diff --stat HEAD`)

| Archivo | Δ | Sub‑fase que lo tocó |
|---|---|---|
| `app/bootstrap_v2/01_schema/V010__tablas_bd_erp_completo.sql` | +35 / −10 | F17 (OLA‑0) |
| `app/infrastructure/database/tables.py` | +31 | F17 (OLA‑0) |
| `app/infrastructure/database/repositories/cfg_codigo_secuencia_repository.py` | +207 / −… | F17C |
| `app/modules/tenant/application/services/cliente_onboarding_service.py` | ~36 | F17C / F17D |
| `app/infrastructure/provisioning/dedicated_tenant_seed_adapters.py` | +6 | F17D |
| `app/infrastructure/provisioning/tenant_seed_profiles.py` | +6 / −… | F17C / F17D |
| `app/infrastructure/provisioning/script_manifest.py` | 1 línea | **F17F** |
| `tests/unit/test_f4_07_dedicated_tenant_seed_service.py` | +6 | F17C |

### Archivos nuevos creados por F17 (`git status` untracked)

- `app/core/codigo/**` — motor de generación de códigos (paquete completo, OLA‑0).
- `app/docs/arquitectura/code-generation/28..36_*.md` — documentación F17B/F17E.
- `app/docs/arquitectura/code-generation/bootstrap/**` — documentación F17A/F17D.
- `tests/unit/test_codigo_engine_ola0.py`, `test_codigo_engine_p1_consolidation.py`,
  `test_codigo_engine_f17d_full_cfg_seed.py`.

### Hecho crítico

Los archivos que el brief F17G pide auditar con "especial atención" y que
gobiernan el RBAC / catálogos / estado del run **NO aparecen** en el conjunto de
cambios F17:

| Archivo señalado en el brief | ¿En el diff F17? | Último commit que lo tocó |
|---|---|---|
| `onboarding_rbac_service.py` | **NO** | `469af23` (RBAC V1 STABLE) |
| `manager_standard_service.py` | **NO** | `469af23` |
| `user_standard_service.py` | **NO** | `469af23` |
| `dedicated_tenant_seed_service.py` | **NO** | `72ebaa1` |
| `bootstrap_script_runner.py` | **NO** | `72ebaa1` |
| `dedicated_catalog_seed_service.py` | **NO** | `72ebaa1` |
| `catalog_profiles.py` | **NO** | `72ebaa1` |
| `tenant_provisioning_state_service.py` | **NO** | `72ebaa1` |
| `dedicated_provisioning_orchestrator.py` | **NO** | `72ebaa1` |
| `dedicated_provisioning_compensation_service.py` | **NO** | `72ebaa1` |
| `provisioning_step_code.py` (SAGA_STEP_ORDER) | **NO** | (pre‑F17) |
| `S010__seed_modulo_menu_completo.sql` (catálogo `modulo_menu`) | **NO** | `ecb640d` |
| `V020__tenant_identity_rbac_store.sql` (FK_permiso_menu) | **NO** | `72ebaa1` |
| `V020__tablas_bd_central.sql` (FK_permiso_menu shared) | **NO** | `72ebaa1` |

`dedicated_tenant_seed_adapters.py` **sí** fue tocado por F17, pero **solo** el
sub‑paso `seed_codigo_secuencias` (ver `39_F17_DIFF_ANALYSIS.md`). El sub‑paso
`seed_tenant_rbac` (origen de `FK_permiso_menu`) **no** fue tocado.

## 2. Línea temporal sub‑fase por sub‑fase

```
ESTADO FUNCIONAL ANTERIOR  (árbol = HEAD 72ebaa1, sin cambios F17)
   cfg_codigo_secuencia = esquema viejo (entidad/prefijo, SIN FKs)
   V010 SHA-256 = 78733886…  ==  _V010_ERP_SHA256 (manifest)  → checksum OK
   Dedicated: S1..S10 alcanzables (validados solo con tests mockeados)
        │
        ▼
F17 (OLA‑0)  — infraestructura del motor
   + app/core/codigo/**  (nuevo)
   ~ V010: cfg_codigo_secuencia reescrita  → sequence_key/scope_*/FKs nuevas
   ~ tables.py: ORM cfg alineado a la nueva tabla
   ⇒ Cambia SHA-256 de V010 → 5f81e8c3…   ≠ _V010_ERP_SHA256 (78733886…)
   ⇒ (checksum del manifest queda desalineado, aún no observado)
        │
        ▼
F17A  — Bootstrap oficial de cfg_codigo_secuencia   (SOLO documentación)
   (sin cambios de código)
        │
        ▼
F17B  — Auditoría de integración bootstrap          (SOLO documentación)
   + 28..32_*.md
        │
        ▼
F17C  — Consolidación P1 del motor
   ~ cfg_codigo_secuencia_repository.py (hardening _assert_write_session)
   ~ onboarding_seed.py / sequence_catalog.py (fuente única)
   ~ tenant_seed_profiles.py (row_expectations = len(EAGER_SEQUENCE_KEYS))
   ~ cliente_onboarding_service.py (importa desde onboarding_seed)
   ~ tests
        │
        ▼
F17D  — Expansión bootstrap (57 CFG: TENANT+EMPRESA)
   ~ onboarding_seed.py (derivación desde catálogo)
   ~ cliente_onboarding_service.py (_insertar_secuencias_codigo recibe empresa_id)
   ~ dedicated_tenant_seed_adapters.py (pasa state.empresa_id + prereq)
   ~ tenant_seed_profiles.py
   + tests F17D
        │
        ▼
F17E  — Forense de "Invalid object name 'bootstrap_applied'"  (SOLO documentación)
   + 33..36_*.md
   Diagnóstico: V010 divergió → checksum del manifest falla en S4 →
   nunca se crea bootstrap_applied → reconciliación choca contra tabla ausente.
        │
        ▼
F17F  — Corrección del checksum V010
   ~ script_manifest.py: _V010_ERP_SHA256 = 5f81e8c3…  (1 línea)
   ⇒ S4 vuelve a pasar → la saga AVANZA por primera vez desde el inicio de F17
     hacia S6 (APPLY_CATALOGS) y S7 (SEED_TENANT).
        │
        ▼
POST‑F17F  — aparecen los errores objeto de F17G:
   • FK_permiso_menu           (en S7 seed_tenant_rbac)
   • "run no está en provisioning" (guard de estado; cascada/retry)
```

## 3. Observación temporal clave para F17G

Durante **toda** la ventana F17 (desde el reshape de V010 en OLA‑0 hasta F17F),
Dedicated **abortaba en S4** por checksum. En consecuencia **S6 y S7 nunca se
ejecutaron** en ese período. `FK_permiso_menu` (S7) y el guard de estado
(cascada de S7/retry) **no podían observarse** hasta que **F17F** re‑abrió el
paso de S4. Es decir: F17F no *introdujo* código RBAC nuevo — **destapó** el
tramo S6→S7 que llevaba toda la fase F17 bloqueado.

Ver `40_F17_ROOT_CAUSE.md` para la causa raíz formal y `39_F17_DIFF_ANALYSIS.md`
para el diff funcional archivo por archivo.
