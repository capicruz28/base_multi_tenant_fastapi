# §2–§5 — Tablas, filtros y planos `/app` · `/admin` · `/super-admin`

---

## §2. Tablas que intervienen

### 2.1 Catálogo y contrato comercial

| Tabla | Rol en el menú |
|-------|----------------|
| `modulo` | Catálogo de módulos (`ORG`, `INV`, `SYS_ADMIN`, …) |
| `modulo_seccion` | Secciones (`TENANT_ADMIN`, `SUPER_ADMIN`, secciones ERP) |
| `modulo_menu` | Ítems (`ruta`, `codigo`, `tipo_menu`, jerarquía `menu_padre_id`) |
| `cliente_modulo` | Módulos contratados / activos del tenant |

### 2.2 Visibilidad UI (Modelo Owner)

| Tabla | Rol |
|-------|-----|
| `rol_menu_permiso` | Flags UI por rol+menú (`puede_ver`, crear, editar, …) — **gate principal de sidebar** |
| `usuario_rol` | Usuario → roles (tenant; opcional filtro `empresa_id`) |
| `rol` | Roles (`ADMIN_TENANT`, etc.) |

### 2.3 RBAC API (paralelo; no oculta menú por sí solo)

| Tabla | Rol |
|-------|-----|
| `permiso` | Códigos de negocio (`org.empresa.leer`, `cfg.secuencias.consultar`, …) |
| `rol_permiso` | Grants API por rol — fuente de `/auth/permissions/me` |

### 2.4 No son fuente del menú ERP moderno

| Tabla / área | Nota |
|--------------|------|
| `menu`, `area_menu` | Legacy `modules/menus` |
| `usuario` | Identidad; no define árbol de menú |

---

## §3. Cómo decide qué módulos mostrar — filtros

### 3.1 Query 1 — catálogo ∩ suscripción

Filtros aplicados en `obtener_menu_usuario`:

| Filtro | Condición |
|--------|-----------|
| **Tenant (cliente)** | `cliente_modulo.cliente_id == cliente_id` |
| **Módulo contratado activo** | `cliente_modulo.esta_activo == True` |
| **Vigencia comercial** | `fecha_vencimiento IS NULL OR > now` |
| **Menú activo** | `modulo_menu.es_activo` |
| **Menú visible** | `modulo_menu.es_visible` |
| **Módulo activo** | `modulo.es_activo` |
| **Sección** | sección activa **o** sin sección |
| **Menú global vs tenant** | `modulo_menu.cliente_id IS NULL OR == cliente_id` |

**Empresa:** no filtra Q1 (el catálogo no se recorta por `empresa_id`).

### 3.2 Query 2 — visibilidad por rol

| Filtro | Condición |
|--------|-----------|
| **Usuario** | `usuario_rol.usuario_id` (salvo impersonación con `permisos_rol_id`) |
| **Tenant** | `usuario_rol.cliente_id` + `rol_menu_permiso.cliente_id` |
| **Rol activo** | `usuario_rol.es_activo = 1` |
| **Expiración rol** | `fecha_expiracion` null o futura |
| **Empresa (opcional)** | `sql_empresa_filter_usuario_rol` cuando hay `empresa_id` resuelto |
| **Puede ver** | `rol_menu_permiso.puede_ver = 1` |
| **Intersección** | Solo `menu_id` presentes en Q2 se conservan |

### 3.3 Elevación

| Flag | Efecto |
|------|--------|
| `is_super_admin=True` | Omite Q2; todos los menús contratados (Q1) con flags UI completos |
| `as_tenant_admin` | **Ignorado** (Modelo Owner); el endpoint pasa siempre `False` |

### 3.4 Post-proceso (no filtra)

- Normalización de rutas legacy → `/app/...`
- Anotación `required_permission` (permisos `accion='leer'` ligados a `modulo_id`) — **no oculta** nodos
- `effective_permission_codes` aceptados pero **no usados** para hide/show en el service

### 3.5 Resumen de ejes

| Eje | ¿Filtra menú? |
|-----|---------------|
| `cliente_id` (tenant) | **Sí** (Q1 + Q2) |
| `empresa_id` | **Parcial** (solo scope de `usuario_rol` en Q2) |
| Roles | **Sí** (vía RMP) |
| Permisos API (`rol_permiso`) | **No** como gate de árbol (sí para FE `PermissionGuard`) |
| `es_activo` / `es_visible` / suscripción | **Sí** |

---

## §4. Distinción `/super-admin` · `/admin` · `/app`

### 4.1 ¿Existe separación en Backend?

**Sí, pero implícita.** El Backend **no** devuelve un campo tipo `sidebar_plane` / `contexto`.

La separación vive en **datos sembrados** + normalizador de rutas:

| Plano FE | Cómo se materializa | Seed |
|----------|---------------------|------|
| **App (ERP operativo)** | `modulo.codigo` = `ORG`, `INV`, …; rutas `/app/org/...`, `/app/inv/...` | `S010` + `S021` / normalizer |
| **Admin tenant** | Módulo `SYS_ADMIN`, sección `TENANT_ADMIN`, códigos `SYS_ADMIN.TENANT.*`, rutas `/admin/*` | `S020` |
| **Platform** | Mismo módulo `SYS_ADMIN`, sección `SUPER_ADMIN` / `GLOBAL_CATALOGS`, códigos `SYS_ADMIN.PLATFORM.*` / `SYS_ADMIN.CATALOGOS.*`, rutas `/super-admin/*` | `S020` |

### 4.2 Normalizador

`app/core/menu/menu_route_normalizer.py`:

- Prefijos reservados: `/app/`, `/admin/`, `/super-admin/`, `/api` → sin cambio
- Legacy `/org/...`, `/inv/...` → prefijo `/app`

`S021` alinea rutas ERP en BD; **no** reescribe `/admin` ni `/super-admin`.

### 4.3 Permisos de “acceso a plano” (API, no árbol)

Sembrados en `S020`:

| Código | Semántica |
|--------|-----------|
| `admin.tenant.access` | Pantallas `/admin/*` — grant a `ADMIN_TENANT` |
| `admin.platform.access` | Pantallas `/super-admin/*` — grant a `ADMIN_PLATFORM` |

Estos códigos refuerzan RBAC de acceso; el árbol sigue dependiendo de RMP + suscripción.

### 4.4 Responsabilidad FE

El Frontend debe particionar sidebars por **prefijo de `ruta`** y/o **códigos** de módulo/sección. El Backend entrega un único árbol filtrado.

---

## §5. Cómo determina el Backend que un módulo pertenece a Tenant Admin

### 5.1 En el árbol de menú (Modelo Owner)

**No** hay elevación “tenant admin” en `/auth/menu`.

Un ítem es “de administración de tenant” por **catálogo**:

1. Pertenece al módulo `SYS_ADMIN`
2. Sección `TENANT_ADMIN` (o código de menú `SYS_ADMIN.TENANT.%`)
3. Ruta bajo `/admin/...`
4. El rol del usuario tiene `rol_menu_permiso.puede_ver` para ese `menu_id`
5. El tenant tiene `SYS_ADMIN` activo en `cliente_modulo` (seed runtime `R020`)

### 5.2 Grants Owner (onboarding / sync)

`OwnerSyncService` al sincronizar `SYS_ADMIN` solo otorga menús:

```sql
mm.codigo LIKE N'SYS_ADMIN.TENANT.%'
-- excluye PLATFORM.% y CATALOGOS.%
```

Scope legacy documentado en `OnboardingMenuBootstrapService.TENANT_ADMIN_MENU_SCOPE_SQL`: `ORG` **o** `SYS_ADMIN.TENANT.%`.

### 5.3 Tipología de usuario (RBAC auth, no menú)

`get_user_type()` / JWT (`tenant_admin`, `super_admin`, …) gobierna gates de plataforma e impersonación; **no** sustituye RMP para armar el sidebar.

### 5.4 Implicación para CFG

CFG **no** está hoy bajo `SYS_ADMIN.TENANT.*`. Su pertenencia a “Tenant Admin” en producto es por **persona y permisos API** (`ADMIN_TENANT` + `cfg.secuencias.*`), no por una marca automática en el menú hasta que se registre catálogo.
