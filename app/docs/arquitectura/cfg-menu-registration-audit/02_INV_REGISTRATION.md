# INV — Registro en el menú (inventario)

---

## 1. Resumen del patrón

**INV = módulo comercial propio** (mismo patrón estructural que ORG).  
Diferencias: no es core, requiere licencia, más pantallas, rutas `/inv` → `/app/inv`.

---

## 2. Registros por tabla

### 2.1 `modulo`

| Campo | Valor |
|-------|--------|
| `modulo_id` | `E1000002-0000-4000-8000-000000000002` |
| `codigo` | `INV` |
| `nombre` | Inventarios |
| `categoria` | `operaciones` |
| `es_core` | `0` |
| `requiere_licencia` | `1` |
| `orden` | `2` |
| `es_activo` | `1` |

**Fuente:** `S010` §1.

### 2.2 `modulo_seccion`

| Campo | Valor |
|-------|--------|
| `seccion_id` | `E2000002-0000-4000-8000-000000000002` |
| `modulo_id` | `E1000002-…-0002` (INV) |
| `codigo` | `PRINCIPAL` |
| `nombre` | Principal |
| `es_activo` | `1` |

**Fuente:** `S010` §2.

### 2.3 `modulo_menu` (9 pantallas)

| menu_id | codigo | nombre | ruta seed | ruta FE |
|---------|--------|--------|-----------|---------|
| `E3020001-…-0001` | `INV_CATEGORIAS` | Categorías | `/inv/categorias` | `/app/inv/categorias` |
| `E3020002-…-0002` | `INV_UNIDADES` | Unidades de Medida | `/inv/unidades-medida` | `/app/inv/unidades-medida` |
| `E3020003-…-0003` | `INV_PRODUCTOS` | Productos | `/inv/productos` | `/app/inv/productos` |
| `E3020004-…-0004` | `INV_ALMACENES` | Almacenes | `/inv/almacenes` | `/app/inv/almacenes` |
| `E3020005-…-0005` | `INV_TIPOS_MOV` | Tipos de Movimiento | `/inv/tipos-movimiento` | `/app/inv/tipos-movimiento` |
| `E3020006-…-0006` | `INV_MOVIMIENTOS` | Movimientos de Inventario | `/inv/movimientos` | `/app/inv/movimientos` |
| `E3020007-…-0007` | `INV_INV_FISICO` | Inventario Físico | `/inv/inventario-fisico` | `/app/inv/inventario-fisico` |
| `E3020008-…-0008` | `INV_STOCK` | Consulta de Stock | `/inv/stock` | `/app/inv/stock` |
| `E3020009-…-0009` | `INV_INV_KARDEX` | Kardex | `/inv/kardex` | `/app/inv/kardex` |

Común: `cliente_id=NULL`, `tipo_menu=pantalla`, activos/visibles.

**Fuentes:** `S010` §3 INV; `S021` / normalizer.

### 2.4 `cliente_modulo`

| Qué | Cómo |
|-----|------|
| Contenido | `cliente_id` + `modulo_id` INV, activo |
| Creación | Mismo onboarding trial: `TRIAL_MODULES` incluye `"INV"` |
| Seed SQL catalog | No crea filas por tenant para INV |

### 2.5 `rol_menu_permiso`

| Qué | Cómo |
|-----|------|
| Owner (`ADMIN_TENANT`) | `OwnerSyncService` con `modulo_codigo="INV"` → los 9 menús |
| Manager Standard | Subconjunto de IDs E302… (sin Kardex en constants documentadas) |
| User Standard | Bundle operativo reducido |

Expectativa trial owner: **9** grants INV (parte de `MIN_HEALTHY_TRIAL_OWNER_MENU_GRANTS = 18` = 6 ORG + 3 SYS_ADMIN.TENANT + 9 INV).

---

## 3. Archivos bootstrap / runtime

| Capa | Archivo / componente |
|------|----------------------|
| Catálogo | `S010__seed_modulo_menu_completo.sql` |
| Rutas `/app` | `S021__menu_routes_saas_alignment.sql` |
| Suscripción | Onboarding `TRIAL_MODULES` / activación comercial |
| RMP | `OwnerSyncService` (+ Manager/User Standard) |

---

## 4. Condición de aparición

Idéntica a ORG, sustituyendo código `INV` y sus `menu_id`.
