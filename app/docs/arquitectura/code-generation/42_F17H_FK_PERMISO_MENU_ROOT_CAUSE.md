# 42 — F17H: Causa raíz definitiva de `FK_permiso_menu`

> Fase **F17H**. Auditoría 100% de solo lectura. **No** se modificó código, SQL,
> bootstrap, catálogos, RBAC, V010, V020, manifests, onboarding ni tests. **No**
> se proponen soluciones. Toda afirmación cita `archivo:línea` o evidencia `git`.
>
> Matriz de datos completa: `43_F17H_GUID_ALIGNMENT_MATRIX.md`.

---

## 0. Causa raíz única (veredicto)

> **Desalineamiento de GUIDs de los menús INV entre el catálogo real
> `app/bootstrap_v2/02_catalog/S010__seed_modulo_menu_completo.sql` (el que S6
> aplica en la BD dedicada) y los `menu_id` hardcodeados de los bundles
> `manager_standard_constants.py` y `user_standard_constants.py`.**
>
> El bundle asocia `INV_CATEGORIAS` al GUID `E3020002-0000-4000-8000-000000000001`,
> pero en el catálogo real ese menú tiene el GUID `E3020001-0000-4000-8000-000000000001`,
> y `E3020002-…-000000000002` está asignado a `INV_UNIDADES`. Por tanto el literal
> `E3020002-0000-4000-8000-000000000001` **no existe** en `modulo_menu`, y el
> `INSERT INTO rol_menu_permiso` de MANAGER_STANDARD / USER_STANDARD viola la
> constraint `FK_permiso_menu`.
>
> Es un **defecto de datos preexistente** introducido el **2026-06-17** (commit
> `ecb640d`, renumeración del catálogo bootstrap_v2) **sin actualizar** los bundles
> (commit `469af23`, 2026-05-31). **No** fue introducido por F17. F17 (vía la
> corrección de checksum F17F) únicamente **volvió alcanzable** el tramo S6→S7
> donde este defecto se manifiesta.

---

## 1. ¿Qué representa exactamente el `menu_id` `E3020002-0000-4000-8000-000000000001`?

- **Nombre (según los bundles):** `INV_CATEGORIAS`.
- **Módulo:** INV (familia de GUID `E302xxxx`; `modulo_id = E1000002` = INV;
  `seccion_id = E2000002`).
- **Código:** `INV_CATEGORIAS`.
- **Origen:** GUID **hardcodeado** en las constantes de bundle, no generado en runtime.
- **Archivo donde se define:**
  - `app/modules/tenant/application/services/manager_standard_constants.py:31`
    → `(UUID("E3020002-0000-4000-8000-000000000001"), {...})  # INV_CATEGORIAS`
  - `app/modules/tenant/application/services/user_standard_constants.py:33`
    → mismo GUID, mismo comentario `INV_CATEGORIAS`.

**Matiz decisivo:** ese GUID representa `INV_CATEGORIAS` **solo en la definición
antigua** (bundles + seed de docs). En el catálogo **vigente** que se aplica a la
BD dedicada, `INV_CATEGORIAS` tiene **otro** GUID (ver §4).

---

## 2. ¿En qué archivo SQL/seed debería crearse?

En `app/bootstrap_v2/02_catalog/S010__seed_modulo_menu_completo.sql`
(`script_code = catalog_s010`), que es el seed de `modulo_menu` aplicado en el
paso **S6 APPLY_CATALOGS** del provisioning Dedicated.

---

## 3. ¿Ese archivo realmente se ejecutó durante S6? (demostrado, no asumido)

**Sí, S010 se ejecutó.** Evidencia:

1. `catalog_profiles.resolve_catalog_seed_profile` incluye **siempre**
   `catalog_s010` en el perfil Dedicated:
   `app/infrastructure/provisioning/catalog_profiles.py:292`
   → `script_codes = ["catalog_s010", "catalog_s020", "catalog_s030"]`.
2. `DedicatedCatalogSeedService.run_catalog_seed` aplica cada script del perfil y
   registra su marker (`dedicated_catalog_seed_service.py:87-119`).
3. **Prueba funcional en el propio log**: los **6 grants ORG** de MANAGER_STANDARD
   (menús `E3010001…E3010006`) se insertaron **sin** violar la FK. Esos menús ORG
   provienen del **mismo** S010 (`S010:98-103`). Si S010 no se hubiera ejecutado,
   los grants ORG también habrían fallado por FK. Su éxito **demuestra** que S010
   corrió y pobló `modulo_menu` con la sección ORG (y, con el mismo INSERT, la INV).

Es decir: el catálogo se aplicó; el problema no es "S010 no corrió", sino "S010
usa otros GUIDs para INV que los que el bundle espera" (§4).

---

## 4. ¿El `menu_id` existe en `modulo_menu`? — NO. Por qué.

**No existe.** El catálogo real asigna a INV **otro esquema de GUIDs**:

`app/bootstrap_v2/02_catalog/S010__seed_modulo_menu_completo.sql:106-115`
(sección `-- ----- INV (9 ítems) -----`):

| Línea | `menu_id` sembrado en `modulo_menu` | `codigo` |
|---|---|---|
| 107 | `E3020001-0000-4000-8000-000000000001` | **INV_CATEGORIAS** |
| 108 | `E3020002-0000-4000-8000-000000000002` | INV_UNIDADES |
| 109 | `E3020003-0000-4000-8000-000000000003` | INV_PRODUCTOS |
| 110 | `E3020004-0000-4000-8000-000000000004` | INV_ALMACENES |
| 111 | `E3020005-0000-4000-8000-000000000005` | INV_TIPOS_MOV |
| 112 | `E3020006-0000-4000-8000-000000000006` | INV_MOVIMIENTOS |
| 113 | `E3020007-0000-4000-8000-000000000007` | INV_INV_FISICO |
| 114 | `E3020008-0000-4000-8000-000000000008` | INV_STOCK |
| 115 | `E3020009-0000-4000-8000-000000000009` | INV_INV_KARDEX |

El literal buscado `E3020002-0000-4000-8000-000000000001` (sufijo `…001`) **no
aparece** en esa lista: el GUID que empieza por `E3020002` termina en `…002` y
corresponde a `INV_UNIDADES`. En consecuencia, cuando MANAGER/USER intentan
insertar `rol_menu_permiso.menu_id = E3020002-…001`, ese `menu_id` no está en
`modulo_menu` → **violación de `FK_permiso_menu`**
(`rol_menu_permiso.menu_id → modulo_menu(menu_id)`,
`app/bootstrap_v2/05_dedicated/V020__tenant_identity_rbac_store.sql:356`).

**Por qué falla en el primer grant INV y no antes:** el bundle procesa primero los
6 menús ORG (alineados, §7) y luego INV. El **primer** grant INV de MANAGER es
justamente `E3020002-…001` (`manager_standard_constants.py:31`) → primer FK. Esto
coincide exactamente con el log (`OwnerSync … OK`, `BASE_OPERATIVE OK`,
`MANAGER_STANDARD falla`, `USER_STANDARD falla`, `menu_id e3020002-…001`).

---

## 5. Búsqueda del GUID completo en TODO el proyecto

Búsqueda **case-insensitive** de `E3020002-0000-4000-8000-000000000001`
(en minúsculas el motor de BD lo devuelve como `e3020002…`; por eso una búsqueda
en minúsculas literal da 0 — la constante está en MAYÚSCULAS):

**Apariciones: 5 archivos.**

| Archivo:línea | Uso |
|---|---|
| `app/modules/tenant/application/services/manager_standard_constants.py:31` | Grant de menú hardcodeado (MANAGER_STANDARD) |
| `app/modules/tenant/application/services/user_standard_constants.py:33` | Grant de menú hardcodeado (USER_STANDARD) |
| `app/docs/database/4.- SEED_MODULO_MENU_COMPLETO.sql:102` | Seed **antiguo** (docs): INV_CATEGORIAS = este GUID |
| `app/docs/auditoria/MANAGER_STANDARD_BUNDLE_DESIGN.md:54,162,302` | Doc de diseño del bundle |
| `app/docs/auditoria/USER_STANDARD_BUNDLE_DESIGN.md:43,102` | Doc de diseño del bundle |

**Ausencia crítica:** el GUID **NO** aparece en
`app/bootstrap_v2/02_catalog/S010__seed_modulo_menu_completo.sql` (el catálogo que
realmente se aplica). Aparece en el seed **de docs** `4.- SEED_MODULO_MENU_COMPLETO.sql`
(no ejecutado por el provisioning) pero no en el catálogo activo → confirma la
divergencia entre "definición antigua" (docs + bundles) y "catálogo vigente".

---

## 6. ¿ManagerStandardService usa GUIDs hardcodeados o los obtiene de la BD?

**Hardcodeados.** Evidencia:

- Fuente de datos: tupla estática `MANAGER_STANDARD_MENU_GRANTS`
  (`manager_standard_constants.py:21-41`), lista de `(UUID(...), flags)`.
- Consumo: `ManagerStandardService._apply_rol_menu_permiso`
  (`manager_standard_service.py:188-226`) itera esa tupla y hace
  `INSERT INTO rol_menu_permiso (... menu_id ...) VALUES (... :menu_id ...)`
  con `menu_id = menu_id` del literal (`:214`). **No** hace `SELECT` contra
  `modulo_menu`; no valida existencia previa del `menu_id`.

Contraste — por qué OwnerSync y BASE_OPERATIVE **no** fallan:

- `OwnerSyncService` deriva el `menu_id` **de la BD**:
  `INSERT INTO rol_menu_permiso (...) SELECT ... mm.menu_id FROM modulo_menu mm
  INNER JOIN modulo m ... INNER JOIN cliente_modulo cm ...`
  (`owner_sync_service.py:298-310`). Solo concede menús **existentes** → imposible
  violar `FK_permiso_menu`.
- `BaseOperativeService` **solo** inserta en `rol_permiso` (nunca `menu_id`);
  deriva `permiso_id` de la tabla `permiso`
  (`base_operative_service.py:330-344`) → no toca `FK_permiso_menu`.

Esa diferencia (derivado-de-BD vs. hardcodeado) es exactamente por qué el log
muestra OwnerSync/BASE_OPERATIVE OK y Manager/User en fallo.

---

## 7. ¿UserStandardService usa el mismo GUID o uno distinto?

**El mismo.** `user_standard_constants.py:33`:
`(UUID("E3020002-0000-4000-8000-000000000001"), {...})  # INV_CATEGORIAS`,
consumido por `UserStandardService` con el mismo patrón hardcodeado. Por eso
USER_STANDARD falla con **idéntico** `menu_id` que MANAGER_STANDARD.

**Corroboración ORG (por qué ORG pasa):** los 6 GUIDs ORG de los bundles
(`E3010001-…001` … `E3010006-…006`, Manager `:23-28` / User `:25-30`) coinciden
**exactamente** con la sección ORG del catálogo real (`S010:98-103`). Alineados →
sin FK. Solo la sección INV está desalineada.

---

## 8. ¿El GUID pertenece al módulo correcto?

La **familia** del GUID (`E302xxxx`) es INV: el catálogo lo ancla a
`modulo_id = E1000002` (INV) y `seccion_id = E2000002` (`S010:107-115`). Por tanto
es un GUID del **módulo correcto (INV)**. El problema no es el módulo, sino que el
**valor exacto** `E3020002-…001` no está mapeado a ningún `modulo_menu` vigente
(el catálogo usa `E3020002-…002`). Es un desalineamiento **intra-módulo INV** de
la numeración de ítems, no un GUID de módulo equivocado.

---

## 9. ¿Fue eliminado por algún cambio previo?

**Sí — reasignado/renumerado por un cambio PRE-F17.** Cronología `git`:

| Fecha | Commit | Archivo | Estado del GUID INV_CATEGORIAS |
|---|---|---|---|
| 2026-05-03 | `851c6ba` | `app/docs/database/4.- SEED_MODULO_MENU_COMPLETO.sql` | `E3020002-…001` = INV_CATEGORIAS |
| 2026-05-31 | `469af23` | `manager_standard_constants.py` / `user_standard_constants.py` | bundles creados usando `E3020002-…001` = INV_CATEGORIAS → **alineados con el seed de esa época** |
| 2026-06-17 | `ecb640d` | `app/bootstrap_v2/02_catalog/S010__seed_modulo_menu_completo.sql` | **renumerado**: INV_CATEGORIAS pasa a `E3020001-…001`; `E3020002-…002` = INV_UNIDADES → **el GUID `E3020002-…001` deja de existir en el catálogo activo** |

El renumerado de `ecb640d` ("arquitentura mejorada") cambió el esquema INV **sin**
actualizar los bundles → a partir de ese commit, el `menu_id` que los bundles
esperan quedó huérfano. **Todo ocurre antes de F17** (F17 = cambios no
commiteados sobre `72ebaa1`, 2026-07-03; ninguno toca estos archivos —
ver `39_F17_DIFF_ANALYSIS.md`).

---

## 10. Desalineamiento entre S010 / modulo_menu / OwnerSync / ManagerStandard / UserStandard

**Existe y es la causa raíz.** Resumen (detalle en `43_...MATRIX.md`):

| Componente | Fuente de `menu_id` | Esquema INV | ¿Puede fallar FK? |
|---|---|---|---|
| `S010` → `modulo_menu` | catálogo (verdad en la BD) | CATEGORIAS=`…20001-001`, UNIDADES=`…20002-002`, PRODUCTOS=`…20003-003`, … | — (es la referencia) |
| OwnerSync | `SELECT FROM modulo_menu` (derivado) | el que exista en `modulo_menu` | **No** (solo inserta existentes) |
| BaseOperative | `permiso` (no usa `menu_id`) | n/a | **No** |
| ManagerStandard | **hardcodeado** | CATEGORIAS=`…20002-001`, PRODUCTOS=`…20001-002`, UNIDADES=`…20003-003`, … | **Sí** (desalineado) |
| UserStandard | **hardcodeado** | idéntico a Manager | **Sí** (desalineado) |

ORG está alineado en todos los componentes; **INV está desalineado** solo en los
dos bundles hardcodeados.

---

## 11. Segundo error: "No se puede mutar steps cuando el run no está en provisioning"

**Es consecuencia del primer error; NO es un bug independiente.** Evidencia:

- El literal se emite en
  `tenant_provisioning_state_service._transition_step`
  (`tenant_provisioning_state_service.py:485-490`,
  `internal_code = PROVISIONING_RUN_NOT_ACTIVE`), cuando se intenta `mark_step_*`
  sobre un run cuyo estado ≠ `PROVISIONING`. Es un **guard defensivo correcto**.
- Cadena causal:
  1. El fallo `FK_permiso_menu` ocurre dentro del **único** session/transacción de
     S7 (`dedicated_tenant_seed_service.py:78`). Aun cuando los bundles Manager/User
     están envueltos en `try/except` que **traga** la excepción
     (`onboarding_rbac_service.py:181-225`), el error de constraint deja la
     operación de S7 en fallo (transacción/estado de sesión comprometido), por lo
     que el paso S7 termina fallando.
  2. El orquestador marca S7 fallido y transiciona el run a `FAILED`
     (`dedicated_provisioning_orchestrator.py:296` → `_fail_step_and_run:678-685`).
  3. Un **reintento/redispatch** posterior (o entrega concurrente del job) intenta
     `mark_step_*` sobre ese run ya `FAILED` → se dispara
     `PROVISIONING_RUN_NOT_ACTIVE`.
- Por tanto: sin el `FK_permiso_menu` no habría run en `FAILED`, y sin run en
  `FAILED` no se dispararía el guard. Es un **síntoma secundario**.
- Fragilidad relacionada (no es un segundo bug del provisioning, sino de robustez
  del RBAC): el `try/except` que traga los fallos de Manager/User
  (`onboarding_rbac_service.py:182,201,205,224`) enmascara el `FK_permiso_menu` a
  nivel de bundle, lo que dificulta el diagnóstico; pero el origen sigue siendo el
  desalineamiento de GUIDs.

---

## 12. Relación con F17 (cierre)

- Ningún archivo implicado (`manager_standard_constants.py`,
  `user_standard_constants.py`, `S010`, `owner_sync_service.py`,
  `onboarding_rbac_service.py`, `tenant_provisioning_state_service.py`) está en el
  diff de F17 (ver `39_F17_DIFF_ANALYSIS.md`). Último cambio: `469af23` / `ecb640d`
  / `72ebaa1` — todos **pre-F17**.
- El defecto se volvió **observable** únicamente porque **F17F** realineó el
  checksum de V010 y reabrió el tramo S4→S6→S7 (ver `40_F17_ROOT_CAUSE.md`). Antes
  de F17, este camino real S6→S7 en Dedicated nunca se validó contra BD real (los
  e2e son mockeados: `test_f4_08_dedicated_orchestrator.py`,
  `test_hybrid_provisioning_e2e`).

**Causa raíz única (repetida):** desalineamiento de GUIDs de menús **INV** entre
el catálogo `bootstrap_v2/02_catalog/S010` y los GUIDs hardcodeados de
`manager_standard_constants.py` / `user_standard_constants.py`; el `menu_id`
`E3020002-0000-4000-8000-000000000001` no existe en `modulo_menu`, provocando la
violación de `FK_permiso_menu`.
