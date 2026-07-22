# 43 — F17H: Matriz de alineación de GUIDs (evidencia de datos)

> Anexo de datos de `42_F17H_FK_PERMISO_MENU_ROOT_CAUSE.md`. Solo lectura.
> Todos los valores son textuales de los archivos citados.

## 1. Fuentes comparadas

| Fuente | Rol | Archivo | Commit |
|---|---|---|---|
| Catálogo vigente (S6) | verdad en `modulo_menu` de la BD dedicada | `app/bootstrap_v2/02_catalog/S010__seed_modulo_menu_completo.sql` | `ecb640d` (2026-06-17) |
| Bundle MANAGER | grants hardcodeados | `app/modules/tenant/application/services/manager_standard_constants.py` | `469af23` (2026-05-31) |
| Bundle USER | grants hardcodeados | `app/modules/tenant/application/services/user_standard_constants.py` | `469af23` (2026-05-31) |
| Seed antiguo (docs) | referencia histórica (no ejecutado) | `app/docs/database/4.- SEED_MODULO_MENU_COMPLETO.sql` | `851c6ba` (2026-05-03) |

## 2. Sección INV — comparación por `codigo`

`✔` = el GUID que el bundle usa para ese código EXISTE en `modulo_menu` (S010).
`✘` = NO existe → FK.

| codigo | S010 vigente (modulo_menu) | Bundle MANAGER/USER | ¿Bundle GUID existe en S010? |
|---|---|---|---|
| INV_CATEGORIAS | `E3020001-…-000000000001` (L107) | `E3020002-…-000000000001` | **✘ FK** (S010 no tiene `E3020002-…001`) |
| INV_PRODUCTOS  | `E3020003-…-000000000003` (L109) | `E3020001-…-000000000002` | ✘ (existe otro `…001` distinto; `E3020001-…002` no está) |
| INV_UNIDADES   | `E3020002-…-000000000002` (L108) | `E3020003-…-000000000003` | ✘ (`E3020003-…003` existe pero es PRODUCTOS) |
| INV_ALMACENES  | `E3020004-…-000000000004` (L110) | `E3020004-…-000000000004` | ✔ (coincide por casualidad de sufijo) |
| INV_TIPOS_MOV  | `E3020005-…-000000000005` (L111) | `E3020006-…-000000000006` (Mgr) | ✔ existe pero apunta a MOVIMIENTOS |
| INV_STOCK      | `E3020008-…-000000000008` (L114) | `E3020005-…-000000000005` (Mgr) | ✔ existe pero apunta a TIPOS_MOV |
| INV_MOVIMIENTOS| `E3020006-…-000000000006` (L112) | `E3020007-…-000000000007` (Mgr) | ✔ existe pero apunta a INV_FISICO |
| INV_INV_FISICO | `E3020007-…-000000000007` (L113) | `E3020008-…-000000000008` (Mgr) | ✔ existe pero apunta a STOCK |

> Nota: varios GUIDs "existen" pero apuntan a un menú distinto del que el bundle
> cree; la FK solo se dispara cuando el GUID literal **no existe en absoluto**. El
> **primer** literal inexistente en el orden del bundle es
> `E3020002-…-000000000001` (primer grant INV de MANAGER,
> `manager_standard_constants.py:31`), que es exactamente el `menu_id` del log.

### Conjunto de GUIDs INV que SÍ existen en `modulo_menu` (S010:107-115)

```
E3020001-…001  INV_CATEGORIAS
E3020002-…002  INV_UNIDADES
E3020003-…003  INV_PRODUCTOS
E3020004-…004  INV_ALMACENES
E3020005-…005  INV_TIPOS_MOV
E3020006-…006  INV_MOVIMIENTOS
E3020007-…007  INV_INV_FISICO
E3020008-…008  INV_STOCK
E3020009-…009  INV_INV_KARDEX
```

### GUIDs INV que el bundle intenta insertar y NO existen en S010

```
E3020002-…001   (bundle: INV_CATEGORIAS)  → ✘  ← primer fallo (log)
E3020001-…002   (bundle: INV_PRODUCTOS)   → ✘
E3020003-…003   está en S010 pero como INV_PRODUCTOS (bundle lo cree UNIDADES)
```

## 3. Sección ORG — comparación (alineada → no falla)

| codigo | S010 (L98-103) | Bundle MANAGER/USER | ¿Coincide? |
|---|---|---|---|
| ORG_MI_EMPRESA    | `E3010001-…001` | `E3010001-…001` | ✔ |
| ORG_SUCURSALES    | `E3010002-…002` | `E3010002-…002` | ✔ |
| ORG_DEPARTAMENTOS | `E3010003-…003` | `E3010003-…003` | ✔ |
| ORG_CARGOS        | `E3010004-…004` | `E3010004-…004` | ✔ |
| ORG_CENTROS_COSTO | `E3010005-…005` | `E3010005-…005` | ✔ |
| ORG_PARAMETROS    | `E3010006-…006` | `E3010006-…006` | ✔ |

ORG 100% alineado → los 6 grants ORG pasan; el fallo empieza en el primer INV.
Esto reproduce el log: `OwnerSync ORG/INV/SYS_ADMIN OK`, `BASE_OPERATIVE OK`,
`MANAGER_STANDARD` y `USER_STANDARD` fallan en `E3020002-…001`.

## 4. Comparación bundle ↔ seed de docs antiguo (por qué "antes cuadraba")

`app/docs/database/4.- SEED_MODULO_MENU_COMPLETO.sql:102-103`:

```
E3020002-…001  INV_CATEGORIAS   ← coincide con el bundle
E3020001-…002  INV_PRODUCTOS    ← coincide con el bundle
```

Los bundles (`469af23`, 2026-05-31) se escribieron contra este seed antiguo
(`851c6ba`, 2026-05-03). El catálogo bootstrap_v2 (`ecb640d`, 2026-06-17)
renumeró INV y dejó los bundles desactualizados. La divergencia es **anterior a
F17** y afecta solo a la ruta que crea `modulo_menu` desde cero (Dedicated S6).

## 5. Patrón de inserción por componente (por qué unos fallan y otros no)

| Componente | SQL (archivo:línea) | Fuente `menu_id` | Riesgo FK |
|---|---|---|---|
| OwnerSync | `owner_sync_service.py:298-310` `INSERT ... SELECT mm.menu_id FROM modulo_menu mm ...` | BD | Nulo |
| BaseOperative | `base_operative_service.py:330-344` `INSERT INTO rol_permiso ... SELECT ... FROM permiso` | BD (permiso) | Nulo (no usa menu_id) |
| ManagerStandard | `manager_standard_service.py:198-221` `INSERT INTO rol_menu_permiso (... menu_id ...) VALUES (:menu_id)` | Constante | **Alto** |
| UserStandard | `user_standard_service.py:180-197` (itera `USER_STANDARD_MENU_GRANTS`, `INSERT INTO rol_menu_permiso ... VALUES (:menu_id)`) | Constante | **Alto** |
