# ORG — Registro en el menú (inventario)

---

## 1. Resumen del patrón

**ORG = módulo comercial propio.**  
Aparece en `GET /auth/menu` cuando existen las cinco capas: `modulo` → `modulo_seccion` → `modulo_menu` → `cliente_modulo` → `rol_menu_permiso`.

---

## 2. Registros por tabla

### 2.1 `modulo`

| Campo | Valor |
|-------|--------|
| `modulo_id` | `E1000001-0000-4000-8000-000000000001` |
| `codigo` | `ORG` |
| `nombre` | Organización |
| `categoria` | `operaciones` |
| `es_core` | `1` |
| `requiere_licencia` | `0` |
| `orden` | `1` |
| `es_activo` | `1` |

**Fuente:** `S010__seed_modulo_menu_completo.sql` §1.

### 2.2 `modulo_seccion`

| Campo | Valor |
|-------|--------|
| `seccion_id` | `E2000001-0000-4000-8000-000000000001` |
| `modulo_id` | `E1000001-…-0001` (ORG) |
| `codigo` | `PRINCIPAL` |
| `nombre` | Principal |
| `es_seccion_sistema` | `1` |
| `es_activo` | `1` |

**Fuente:** `S010` §2.

### 2.3 `modulo_menu` (6 pantallas)

| menu_id | codigo | nombre | ruta seed (S010) | ruta post-S021 / normalizer |
|---------|--------|--------|------------------|------------------------------|
| `E3010001-…-0001` | `ORG_MI_EMPRESA` | Mi Empresa | `/org/empresa` | `/app/org/empresa` |
| `E3010002-…-0002` | `ORG_SUCURSALES` | Sucursales | `/org/sucursales` | `/app/org/sucursales` |
| `E3010003-…-0003` | `ORG_DEPARTAMENTOS` | Departamentos | `/org/departamentos` | `/app/org/departamentos` |
| `E3010004-…-0004` | `ORG_CARGOS` | Cargos | `/org/cargos` | `/app/org/cargos` |
| `E3010005-…-0005` | `ORG_CENTROS_COSTO` | Centros de Costo | `/org/centros-costo` | `/app/org/centros-costo` |
| `E3010006-…-0006` | `ORG_PARAMETROS` | Parámetros del Sistema | `/org/parametros` | `/app/org/parametros` |

Común a todos:

- `seccion_id` = sección PRINCIPAL ORG  
- `cliente_id` = `NULL` (global)  
- `tipo_menu` = `pantalla`  
- `es_visible` = `1`, `es_activo` = `1`, `es_menu_sistema` = `1`

**Fuentes:** `S010` §3 ORG; alineación rutas `S021` / `normalize_menu_ruta_for_fe`.

### 2.4 `cliente_modulo`

| Qué | Cómo |
|-----|------|
| Contenido | Fila por tenant: `cliente_id` + `modulo_id` ORG, `esta_activo=1` |
| ¿Seed SQL estático por tenant? | **No** en bootstrap catalog para ORG |
| Creación runtime | Onboarding: `OnboardingRbacService` activa `TRIAL_MODULES` = `("ORG", "SYS_ADMIN", "INV")` → INSERT idempotente en `cliente_modulo` |
| Constante | `app/modules/tenant/application/services/owner_sync_constants.py` → `TRIAL_MODULES` |

Sin esta fila, Q1 de `/auth/menu` **excluye** todos los menús ORG.

### 2.5 `rol_menu_permiso`

| Qué | Cómo |
|-----|------|
| Destinatario tipico trial | Rol `ADMIN_TENANT` del tenant |
| Menús | Los 6 `menu_id` ORG anteriores |
| Flags owner | `puede_ver/crear/editar/eliminar/exportar/imprimir = 1`, `puede_aprobar = 0` (OwnerSync) |
| Creación | `OwnerSyncService.sync_module_for_owner(..., modulo_codigo="ORG")` durante onboarding / sync |
| Otros roles | Bundles Manager/User Standard insertan subconjuntos de menús ORG (IDs fijos E301…) |

Sin RMP con `puede_ver=1`, el usuario **no** ve ORG aunque el módulo esté contratado.

---

## 3. Archivos bootstrap / runtime que crean estos registros

| Capa | Archivo / componente |
|------|----------------------|
| Catálogo módulo/sección/menú | `bootstrap_v2/02_catalog/S010__seed_modulo_menu_completo.sql` |
| Prefijo `/app` | `bootstrap_v2/02_catalog/S021__menu_routes_saas_alignment.sql` |
| Suscripción tenant | Python onboarding (`OnboardingRbacService` + `TRIAL_MODULES`) |
| Visibilidad UI owner | `OwnerSyncService` |
| Visibilidad Manager/User | `ManagerStandardService` / `UserStandardService` (+ constants con UUIDs de menú) |

---

## 4. Condición de aparición en `/auth/menu`

```text
modulo ORG activo
  ∧ sección PRINCIPAL activa
  ∧ 1..n modulo_menu activos/visibles
  ∧ cliente_modulo(ORG) activo para el tenant
  ∧ rol_menu_permiso.puede_ver para el rol del usuario
```
