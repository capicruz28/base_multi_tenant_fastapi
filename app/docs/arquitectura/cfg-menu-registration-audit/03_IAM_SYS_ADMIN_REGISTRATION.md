# IAM (Tenant Admin) — Registro en el menú (inventario)

> En este documento, **IAM** = pantallas de administración de tenant (usuarios, roles, sesiones).  
> **No existe** `modulo.codigo = 'IAM'` en el catálogo.

---

## 1. Resumen del patrón

**IAM = menús embebidos en `SYS_ADMIN`, sección `TENANT_ADMIN`.**  
No es un módulo comercial propio. El contenedor de catálogo es `SYS_ADMIN`; el contrato comercial es `cliente_modulo(SYS_ADMIN)`; la visibilidad owner se limita a códigos `SYS_ADMIN.TENANT.%`.

---

## 2. Registros por tabla

### 2.1 `modulo`

| Campo | Valor |
|-------|--------|
| `codigo` | **`SYS_ADMIN`** (no `IAM`) |
| `nombre` | Administración del Sistema |
| `categoria` | `sistema` |
| `es_core` | `1` |
| `requiere_licencia` | `0` |
| `orden` | `100` |
| `es_activo` | `1` |
| `modulo_id` | Generado en seed (`NEWID()` si no existe) — **no** UUID fijo E100… |

**Fuente:** `S020__seed_admin_menu.sql` §1.

### 2.2 `modulo_seccion` (relevante a IAM / Tenant Admin)

| codigo | nombre | orden | Uso |
|--------|--------|-------|-----|
| **`TENANT_ADMIN`** | Administración | 1 | **IAM tenant** (usuarios, roles, sesiones) |
| `SUPER_ADMIN` | Administración | 2 | Platform (fuera de alcance IAM tenant) |
| `GLOBAL_CATALOGS` | Catalogos | 3 | Catálogos platform |

**Fuente:** `S020` §2.  
IDs de sección: `NEWID()` en insert (no UUIDs fijos E200…).

### 2.3 `modulo_menu` — solo Tenant Admin (IAM)

| codigo | nombre | ruta | orden |
|--------|--------|------|-------|
| `SYS_ADMIN.TENANT.USERS` | Gestión de Usuarios | `/admin/usuarios` | 1 |
| `SYS_ADMIN.TENANT.ROLES` | Roles y Permisos | `/admin/roles` | 2 |
| `SYS_ADMIN.TENANT.SESSIONS` | Sesiones Activas | `/admin/sesiones` | 3 |

Común:

- `modulo_id` = SYS_ADMIN  
- `seccion_id` = TENANT_ADMIN  
- `cliente_id` = NULL  
- `tipo_menu` = `pantalla`  
- `es_visible` / `es_activo` / `es_menu_sistema` = 1  
- `menu_id` = `NEWID()` (no UUID fijo)

**Fuente:** `S020` §3.  
**S021 no reescribe** estas rutas (ya están bajo `/admin/`).

> Menús `SYS_ADMIN.PLATFORM.*` y `SYS_ADMIN.CATALOGOS.*` existen en el mismo módulo pero **no** se otorgan al owner tenant (filtro OwnerSync).

### 2.4 `cliente_modulo`

| Qué | Cómo |
|-----|------|
| Módulo contratado | **`SYS_ADMIN`**, no `IAM` |
| Seed runtime | `R020__relacion_sys_admin_cliente_modulo.sql` — activa SYS_ADMIN para todos los `cliente` activos |
| Onboarding | También en `TRIAL_MODULES` → asegura `cliente_modulo` SYS_ADMIN en provisionamiento |

### 2.5 `rol_menu_permiso`

| Qué | Cómo |
|-----|------|
| Owner | `OwnerSyncService` con `modulo_codigo="SYS_ADMIN"` |
| Filtro especial | Solo menús `mm.codigo LIKE 'SYS_ADMIN.TENANT.%'` (excluye PLATFORM y CATALOGOS) |
| Resultado tipico trial | **3** grants (USERS, ROLES, SESSIONS) |
| Rol | `ADMIN_TENANT` |

Constante de filtro:

```text
_SYS_ADMIN_MENU_FILTER en owner_sync_service.py
```

---

## 3. Archivos bootstrap / runtime

| Capa | Archivo / componente |
|------|----------------------|
| Módulo + secciones + menús IAM | `S020__seed_admin_menu.sql` |
| Permisos de plano `admin.tenant.access` | `S020` (final del script) |
| `cliente_modulo` SYS_ADMIN | `R020` + onboarding trial |
| RMP TENANT only | `OwnerSyncService` (filtro SYS_ADMIN.TENANT) |

---

## 4. ¿Es un módulo propio?

| Pregunta | Respuesta |
|----------|-----------|
| ¿Existe `modulo.codigo = IAM`? | **No** |
| ¿Patrón real? | **Menús dentro de `SYS_ADMIN`** |
| ¿Plano FE? | `/admin/*` |
| ¿API de negocio “/iam”? | No aplica a este registro; las APIs viven en users/rbac/admin |

---

## 5. Condición de aparición (IAM tenant)

```text
modulo SYS_ADMIN activo
  ∧ sección TENANT_ADMIN activa
  ∧ modulo_menu SYS_ADMIN.TENANT.* activos/visibles
  ∧ cliente_modulo(SYS_ADMIN) activo
  ∧ rol_menu_permiso.puede_ver (owner sync solo TENANT.*)
```
