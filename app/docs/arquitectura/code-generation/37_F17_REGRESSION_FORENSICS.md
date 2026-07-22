# 37 — F17 Regression Forensics (Investigación forense)

> Fase **F17G**. Auditoría 100% de solo lectura. **No** se modificó código, V010,
> bootstrap, onboarding, RBAC, catálogos, manifests ni tests. **No** se proponen
> soluciones aquí (ver `41_F17_REMEDIATION_OPTIONS.md`).

Documentos hermanos:
`38_F17_CHANGE_TIMELINE.md` · `39_F17_DIFF_ANALYSIS.md` · `40_F17_ROOT_CAUSE.md` ·
`41_F17_REMEDIATION_OPTIONS.md`.

---

## 1. Resumen ejecutivo (con evidencia)

1. El conjunto **completo** de cambios F17 es el `git diff HEAD` (8 archivos
   rastreados) + `app/core/codigo/**` nuevo. **Ninguno** de los archivos que
   *emiten* los dos errores nuevos (`FK_permiso_menu`, "run no está en
   provisioning") está en ese conjunto. Ver `38`/`39`.
2. Los dos errores ocurren en **S6→S7** del provisioning Dedicated. Durante
   **toda** la ventana F17, Dedicated **abortaba en S4** (checksum V010), por lo
   que S6/S7 **nunca se ejecutaron**. **F17F** realineó el checksum y **re‑abrió**
   S4; a partir de ahí la saga llega a S6/S7 **por primera vez desde el inicio de
   F17** y quedan expuestos comportamientos de ese tramo.
3. `FK_permiso_menu` se origina en el sub‑paso **S7 `seed_tenant_rbac`** →
   `OnboardingRbacService.bootstrap_cliente_rbac` → inserts en `rol_menu_permiso`
   cuyo `menu_id` referencia `modulo_menu` (constraint `FK_permiso_menu`,
   `V020__tenant_identity_rbac_store.sql:356`). Ese código y sus catálogos **no
   fueron modificados por F17** (git: `469af23` / `ecb640d`).
4. "No se puede mutar steps cuando el run no está en provisioning" se emite en
   `tenant_provisioning_state_service._transition_step:485` cuando se intenta
   `mark_step_*` sobre un run cuyo estado ≠ `PROVISIONING`. Es una **cascada /
   condición de retry**, secundaria a un fallo previo. Código **no modificado por
   F17** (git: `72ebaa1`).

> Conclusión anticipada: **el cambio F17 con nexo causal es el reshape de V010 +
> su checksum (F17E → F17F)**. No hay un cambio F17 sobre RBAC/estado; F17F
> *destapó* fallos del tramo S6→S7 que estaban ocultos tras el aborto de S4.
> La causa raíz formal está en `40_F17_ROOT_CAUSE.md`.

---

## 2. Método de investigación

- `git diff --stat HEAD` + `git status --porcelain` → superficie exacta de F17.
- `git log -1 -- <archivo>` sobre cada componente del camino Dedicated → fechar
  el último cambio y demostrar que no pertenece a F17.
- Lectura directa (`Read`) de: orquestador, state service, seed service, seed
  adapters, catalog seed, catalog profiles, onboarding_rbac, bootstrap_applied_reader,
  compensation service.
- Localización de los literales de error con `Grep`.

Toda afirmación cita `archivo:línea`.

---

## 3. Reconstrucción del flujo Dedicated (antes vs. después de F17)

Orden de la saga (invariante, `provisioning_step_code.py:22` `SAGA_STEP_ORDER`):

```
S1 REGISTRY → S2 STORAGE_ALLOCATION → S3 CREATE_DATABASE
→ S4 APPLY_SCHEMA_ERP → S5 APPLY_SCHEMA_RBAC
→ S6 APPLY_CATALOGS → S7 SEED_TENANT
→ S8 REGISTER_METADATA → S9 ACTIVATE_ROUTING → S10 MARK_READY
```

| Paso | Tablas afectadas | Datos creados | Dependencias |
|---|---|---|---|
| S3 CREATE_DATABASE | (BD nueva) | BD dedicada vacía | — |
| S4/S5 APPLY_SCHEMA | esquema ERP (V010) + RBAC/DTSP (V020) + `bootstrap_applied` | todas las tablas, incl. `modulo_menu`, `rol_menu_permiso`, `cfg_codigo_secuencia` (vacías) | `validate_manifest_integrity` (checksum) |
| S6 APPLY_CATALOGS | `modulo`, `modulo_menu`, `permiso`, … | filas de catálogo (S010/S020/S030 + permisos por módulo) | `bootstrap_applied` existente |
| S7 SEED_TENANT | `rol`, `org_empresa`, `usuario`, `rol_menu_permiso`, `rol_permiso`, `cfg_codigo_secuencia` | roles, empresa, admin, **grants RBAC**, 57 secuencias | catálogos de S6 (FK a `modulo_menu`/`permiso`) |

### Antes de F17 (árbol = `72ebaa1`)

- `cfg_codigo_secuencia` = esquema viejo; `SHA-256(V010)=78733886…` **==**
  `_V010_ERP_SHA256`. **S4 pasa** → S5 → S6 → S7 → … → READY.
- (El "funcionaba" Dedicated está validado por tests **mockeados**:
  `test_f4_08_dedicated_orchestrator.py`, `test_hybrid_provisioning_e2e`. No hay
  un test que ejerza el FK real de S7 contra SQL Server.)

### Durante F17 (OLA‑0 → F17E)

- V010 reescrita → `SHA-256=5f81e8c3…` **≠** `_V010_ERP_SHA256 (78733886…)`.
- **S4 aborta** en `validate_manifest_integrity`. La saga **no** crea
  `bootstrap_applied`; la reconciliación
  (`orchestrator:504 _reconcile_bootstrap_failure` →
  `bootstrap_applied_reader.py:42`) choca contra la tabla ausente →
  "Invalid object name 'bootstrap_applied'" (síntoma F17E).
- **S6 y S7 nunca se ejecutan** durante toda esta ventana.

### Después de F17F (checksum realineado)

- `_V010_ERP_SHA256 = 5f81e8c3…` **==** `SHA-256(V010)`. **S4 vuelve a pasar**.
- La saga alcanza **S6 y S7 por primera vez desde el inicio de F17**.
- Aquí se hacen observables `FK_permiso_menu` (S7) y, por cascada/retry, el guard
  `PROVISIONING_RUN_NOT_ACTIVE`.

**Punto de divergencia exacto**: `SHA-256(V010)` vs `_V010_ERP_SHA256`
(`script_manifest.py`), evaluado en `validate_manifest_integrity` durante S4.

---

## 4. Error `FK_permiso_menu` — respuestas puntuales

Constraint (dedicado): `rol_menu_permiso.menu_id → modulo_menu(menu_id)`,
`app/bootstrap_v2/05_dedicated/V020__tenant_identity_rbac_store.sql:356`
(equivalente shared en `V020__tablas_bd_central.sql:405`).

| Pregunta | Respuesta con evidencia |
|---|---|
| ¿Qué registro intenta insertar? | Una fila en `rol_menu_permiso` (grant rol↔menu↔permiso). |
| ¿Qué `menu_id` usa? | El `menu_id` de un bundle RBAC: `OwnerSyncService.sync_modules_for_owner` y `BaseOperativeService.apply_to_operative_roles` (invocados sin try/except en `onboarding_rbac_service.py:137` y `:163`), y `Manager/UserStandardService` (invocados **con** try/except, `onboarding_rbac_service.py:181‑225` → sus FK se **tragan** y loguean, no propagan). |
| ¿Quién genera ese `menu_id`? | Catálogo `modulo_menu`, poblado por `S010__seed_modulo_menu_completo.sql` (+ S020) y referenciado por los bundles. |
| ¿Quién debía crear el menu antes? | **S6 APPLY_CATALOGS** (`DedicatedCatalogSeedService.run_catalog_seed`), que **siempre** incluye `catalog_s010` (`catalog_profiles.py:292`). |
| ¿En qué paso se crea el menu? | S6 (antes de S7, orden invariante `SAGA_STEP_ORDER`). |
| ¿Ese paso cambió durante F17? | **NO**. `dedicated_catalog_seed_service.py`, `catalog_profiles.py`, `S010`, `onboarding_rbac_service.py`, bundles: ausentes del diff F17 (git: `72ebaa1`/`ecb640d`/`469af23`). |
| ¿Se dejó de ejecutar? | El orden y la inclusión de S6 son invariantes; F17 no elimina S6. (Un salto de S6 solo sería posible por *marker* de un run parcial previo — estado, no código F17; ver `40` §4.) |
| ¿Se ejecutó en otro orden? | **NO** (`SAGA_STEP_ORDER` sin cambios). |
| ¿Se modificó algún catálogo? | **NO** (`S010`/`S020`/`S030` y `catalog_profiles.py` sin cambios F17). |
| ¿Se modificó alguna consulta / filtro? | **NO** en el camino RBAC. Los únicos SQL cambiados por F17 son los de `cfg_codigo_secuencia` (repo + `_insertar_secuencias_codigo`), ejecutados en el sub‑paso **posterior** `seed_codigo_secuencias`. |

**Detalle relevante**: la verificación de catálogos S6
(`catalog_profiles._row_expectations_for_plan:321‑335`) exige `modulo>=27` y
`permiso>=…`, pero **no verifica `modulo_menu`**. Por tanto un déficit de filas
en `modulo_menu` **pasa S6 en silencio** y solo revienta en S7 con
`FK_permiso_menu`. Esta laguna de verificación **es anterior a F17** (código no
tocado por F17), pero es la que hace que el síntoma aparezca en S7 y no en S6.

**Camino de propagación del literal**: la FK (pyodbc) sube como `DatabaseError`
y `DedicatedTenantSeedService` la re‑lanza como
`ConflictError PROVISIONING_SEED_FAILED` con `from exc`
(`dedicated_tenant_seed_service.py:105‑116`); el texto `FK_permiso_menu` queda en
la cadena de excepción.

---

## 5. Error "run no está en provisioning" — respuestas puntuales

Literal: `tenant_provisioning_state_service.py:488`, internal_code
`PROVISIONING_RUN_NOT_ACTIVE`, dentro de `_transition_step` (línea 457), guard en
la línea **485** (`if self._parse_run_state(locked) != ProvisioningState.PROVISIONING`).
Lo invocan `mark_step_running/completed/failed/skipped`.

| Pregunta | Respuesta con evidencia |
|---|---|
| ¿Antes de F17 existía? | **Sí, el código existe** desde `72ebaa1` (no F17). Lo que no ocurría era la **condición** que lo dispara. |
| ¿Qué archivo lo dispara? | `dedicated_provisioning_orchestrator.py` al llamar `mark_step_*`: bucle principal (`:284`, `:299`), bloque bootstrap (`:477`, `_mark_bootstrap_saga_steps:532‑569`), `_fail_step_and_run:678‑685`. También `compensation.retry_provisioning_run:326` (`begin_retry_from_failed`). |
| ¿Qué condición dejó de cumplirse? | Que el run esté en `PROVISIONING` al mutar un step. Se rompe cuando un fallo previo ya transicionó el run a `FAILED` (o `READY`) y otra ruta/entrega concurrente intenta marcar steps. |
| ¿Qué cambio de F17 puede provocarlo? | **Indirecto**: F17F re‑abre S4 y la saga avanza; un fallo real en S7 (`FK_permiso_menu`) transiciona el run a `FAILED` (`_fail_step_and_run`). Reintentos/redispatch de runs (manuales o de cola) sobre runs ya no‑`PROVISIONING`, o entregas duplicadas del job, disparan el guard. La ventana F17E además dejó runs en estado inconsistente (la reconciliación reventaba **antes** de `_fail_step_and_run`, `orchestrator:504` vs `:512`), aumentando la probabilidad de esta cascada al reintentar tras F17F. |

Es, por tanto, un **síntoma secundario** (cascada de un fallo primario y/o de
ciclos de retry), no un fallo introducido por código F17.

---

## 6. Cambios indirectos revisados (checklist del brief)

| Categoría | Hallazgo |
|---|---|
| Orden de ejecución | `SAGA_STEP_ORDER` sin cambios; sub‑pasos S7 sin reordenar (solo `seed_codigo_secuencias` modificado). |
| Commits intermedios | Ninguno: todo F17 es árbol de trabajo sobre `72ebaa1`. |
| Rollback parcial | S7 corre en **una sola sesión** (`dedicated_tenant_seed_service.py:78`); un fallo revierte todo el S7 (incluidos markers de sub‑paso). Comportamiento pre‑F17. |
| Nuevas validaciones | F17 añade prereq `state.empresa_id` en `seed_codigo_secuencias` (adapters:190‑194) → sub‑paso **posterior** a RBAC; no afecta el FK. |
| Nuevos filtros / consultas | Solo en SQL de `cfg_codigo_secuencia`. |
| Nuevas dependencias (imports) | `cliente_onboarding_service`/`tenant_seed_profiles` ahora importan `app.core.codigo.*`. Import resuelto OK (107 tests verdes) → sin ImportError en runtime. |
| Transacción / sesión | Sin cambios en el modelo de sesión de S7 ni en el UoW del state service. |
| Conexión | Sin cambios (ADMIN para control plane; sesión dedicada para data plane). |
| Catálogo | Sin cambios (`S010/S020/S030`, `catalog_profiles.py`). |

---

## 7. Respuestas directas del brief

**A) ¿Los errores nuevos provienen de un cambio de código F17 sobre RBAC/estado?**
**NO.** Todo el código que los emite (RBAC bundles, catalog seed, orquestador,
state service, V020, S010) está **ausente del diff F17** (evidencia git en `38`/`39`).

**B) Entonces, ¿qué cambio F17 hace que ahora aparezcan?**
El reshape de `V010` (OLA‑0) rompió el checksum y **F17F** lo realineó
(`script_manifest.py:_V010_ERP_SHA256`). Ese realineo **re‑abre S4** y permite que
la saga alcance **S6/S7 por primera vez desde el inicio de F17**, exponiendo:
`FK_permiso_menu` (laguna de acoplamiento catálogo↔bundle en S7) y el guard de
estado (cascada/retry).

**C) ¿Es "un problema previo"?**
El **código** que falla es previo a F17 (no lo modificó F17). Su **observabilidad**
es consecuencia directa de la secuencia F17 (V010 → checksum → F17F). Ambas cosas
se demuestran con git + lectura de código; no es una afirmación sin evidencia.

Causa raíz formal y formato solicitado: `40_F17_ROOT_CAUSE.md`.
