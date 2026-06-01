# RUNTIME RBAC AUDIT

**Fecha de auditoría:** 2026-05-21  
**Alcance:** onboarding, activación de módulos, startup RBAC, catálogo `02_catalog/`, runtime `03_runtime/`  
**Método:** lectura de imports, servicios invocados, `main.py` lifespan, endpoints con `require_permission`, scripts bootstrap. Sin suposiciones.

---

## 1. Resumen ejecutivo

| Pregunta | Respuesta basada en código |
|----------|---------------------------|
| ¿Onboarding reemplaza R010/R020/S030/S040–S066? | **No** |
| ¿`permission_sync_service` puede ser única fuente de `permiso`? | **Sí**, para códigos declarados en rutas (~113). Requiere exenciones/registry para permisos sin endpoint |
| ¿API autoriza con `rol_permiso`? | **Sí** (`permisos_usuario_service`, `has_permission`) |
| ¿Menú UI usa `rol_menu_permiso`? | **Sí** (`ModuloMenuService.obtener_menu_usuario`, salvo atajo `as_tenant_admin`) |
| ¿`MenuPermissionBinder` está activo? | **No** (no importado en `run_rbac_startup`) |
| ¿`menu_permission_resolver` activo? | **Sí** (`MenuResolverService.get_menu_for_user` → `resolve_required_permissions_for_menu_tree`) |

**Bloqueo operativo post-onboarding (sin SQL runtime):** usuario `admin` tiene roles pero **`rol_permiso` vacío** → `user.permisos = []` → fallan endpoints con `require_permission(...)`. Menú admin puede verse con `as_tenant_admin=True` pero APIs admin/tenant no.

---

## 2. Qué hace onboarding hoy (`ClienteOnboardingService`)

**Invocado desde:** `ClienteService` → `crear_cliente_con_onboarding` (único entrypoint encontrado en `app/modules/tenant`).

**Transacción ADMIN (tablas tocadas):**

| Paso | Tabla / acción | Archivo:línea |
|------|----------------|---------------|
| 1 | `INSERT cliente` | `cliente_onboarding_service.py` ~194–228 |
| 2 | `INSERT rol` ×3 (`ADMIN_TENANT`, `MANAGER_TENANT`, `USER_TENANT`) con `es_admin_cliente` | ~247–275 |
| 3 | `INSERT usuario` (`empresa_default_id = NULL`) | ~289–313 |
| 4 | `INSERT usuario_rol` (`empresa_id NULL`, `es_empresa_default=0`) | ~336–371 |
| 5 | `INSERT cliente_auth_config` si no existe | ~377–387 |
| 6 | `cfg_codigo_secuencia` vía `CfgCodigoSecuenciaRepository` | ~391–405 |

**NO hace (confirmado por ausencia en archivo):**

- `INSERT cliente_modulo` (ORG, SYS_ADMIN, INV, …)
- `INSERT rol_permiso`
- `INSERT permiso`
- `INSERT rol_menu_permiso`
- Llamada a `ClienteModuloService.activar_modulo_cliente`
- Llamada a `aplicar_plantillas_roles`
- Registro en `PermissionRegistry` / sync

---

## 3. Qué hacen los scripts SQL runtime/catalog (referencia)

### S030 — `core.app.acceder`

- MERGE en tabla `permiso` (`modulo_id` NULL).
- **No** asigna `rol_permiso` (eso es R010).

### R010 — asignar `core.app.acceder`

- `INSERT rol_permiso` para **todos** los roles activos (`cliente_id NOT NULL`) y roles sistema × clientes.
- **No** aparece `core.app.acceder` en ningún `require_permission` del repo (`app/modules`).

### R020 — SYS_ADMIN en `cliente_modulo`

- `INSERT cliente_modulo` para cada `cliente` activo + módulo `SYS_ADMIN`.
- Requiere que S020 haya creado módulo `SYS_ADMIN`.

### S020 — menú admin + permisos SQL

- Crea `SYS_ADMIN`, menús, `permiso` `admin.tenant.access` / `admin.platform.access`.
- `INSERT rol_permiso` solo para roles con `codigo_rol IN ('ADMIN_TENANT','ADMIN_PLATFORM')` **existentes al ejecutar el script**.

### S040–S066 — catálogo `permiso` por módulo

- MERGE ~377 códigos (medido con script de diff sobre `SELECT 'codigo'`).
- **20 códigos** usados en API **no** están en estos seeds: prefijos `admin.*`, `tenant.*`, `modulos.*`.
- **284 códigos** solo en SQL (módulos sin endpoint o acciones no implementadas).

---

## 4. Startup FastAPI RBAC (código ejecutado)

**Registro:** `app/main.py` → `app.router.lifespan_context = rbac_lifespan` → `run_rbac_startup(app)`.

**Orden real** (`permission_startup.py`):

1. `ensure_registry_from_routes(app)` — escanea `require_permission` / metadata en dependencias.
2. `apply_rbac_enforcement(app)` — añade dependencias a rutas sin permiso (heurística).
3. `sync_permissions()` — `permission_sync_service.sync()`:
   - INSERT/UPDATE `permiso` por registry.
   - **UPDATE `es_activo = 0`** para códigos en BD no presentes en registry.
4. `audit_routes_permissions` / `warn_routes_without_permission`.

**Config (`app/core/config.py`):**

- `RBAC_PERMISSION_SYNC_ENABLED` default **true**
- `USE_PERMISSION_RESOLVER` default **false** (user_builder usa `permisos_usuario_service` directo salvo flag)

**No ejecutado en startup:**

- `MenuPermissionBinder.bind()` — solo definido en `menu_permission_binder.py`.

---

## 5. Autorización API vs menú

### API (`require_permission` → `has_permission`)

- Fuente: `user.permisos` (lista de strings) cargada en `user_builder.py` ~337–382.
- Origen datos: `permisos_usuario_service.obtener_codigos_permiso_usuario` → SQL `usuario_rol` ⋈ `rol_permiso` ⋈ `permiso` (`es_activo = 1`).
- Comentario explícito en `rbac.py` ~219–221: **no hay bypass** por rol Administrador en permisos de negocio.
- `RoleChecker(["Administrador"])` valida **nombre de rol**, no `codigo_rol` (`ADMIN_TENANT` tiene `nombre = 'Administrador'` → coincide).

### Menú (`ModuloMenuService` + `MenuResolverService`)

- Filtra módulos por **`cliente_modulo`** activo (JOIN en query ~937–946).
- Permisos de pantalla (ver/crear/…): query **`rol_menu_permiso`** ~1056+ (salvo `is_super_admin` / `as_tenant_admin` → menú elevado sin `rol_menu_permiso`).
- `menu_permission_resolver`: enriquece `required_permission` **en memoria** desde `permiso` con `accion='leer'`; **no escribe BD**.
- `effective_permission_codes` del resolver se pasa al menú pero comentario ~870–873: **filtrado futuro**; hoy predomina `rol_menu_permiso`.

### `rol_plantilla_applier` (activación módulo)

- Invocado desde `ClienteModuloService.activar_modulo_cliente` ~406.
- Crea roles desde `modulo_rol_plantilla`.
- Permisos vía `PermisoService.asignar_o_actualizar_permiso` → tabla **`rol_menu_permiso`**, no `rol_permiso`.

**Conclusión dual-path:** operación API = `rol_permiso`; visibilidad/acciones UI menú = `rol_menu_permiso` (+ atajos admin).

---

## 6. `ClienteModuloService` (activación)

**Qué hace al activar** (`activar_modulo_cliente`):

1. `INSERT`/`UPDATE` `cliente_modulo`.
2. `aplicar_plantillas_roles` (opcional, no bloquea si falla).
3. `get_permission_resolver().invalidate_for_tenant`.

**Qué NO hace:**

- No inserta filas en `rol_permiso` para permisos de API del módulo.
- No ejecuta seeds S010/S040.

**Dependencia:** catálogo `modulo` debe existir (S010 en bootstrap global).

---

## 7. Matriz de capacidades: onboarding vs SQL runtime

| Capacidad | Onboarding | ClienteModuloService | permission_sync | R010 | R020 | S030 | S020 §6 | S040–S066 |
|-----------|------------|----------------------|-----------------|------|------|------|---------|-----------|
| Crear cliente | ✅ | — | — | — | — | — | — | — |
| Roles base ADMIN_TENANT | ✅ | — | — | — | — | — | — | — |
| Usuario admin | ✅ | — | — | — | — | — | — | — |
| `cliente_modulo` ORG | ❌ | ✅ (manual API) | — | — | — | — | — | — |
| `cliente_modulo` SYS_ADMIN | ❌ | ❌ | — | — | ✅ | — | — | — |
| Catálogo `permiso` | ❌ | — | ✅ (~113 códigos) | — | — | ✅ 1 código | ✅ 2 admin.* | ✅ ~377 |
| `rol_permiso` core.app | ❌ | ❌ | — | ✅ | — | — | — | — |
| `rol_permiso` admin/tenant/modulos | ❌ | ❌ | — | ❌ | ⚠️ solo admin.tenant/platform | — | ⚠️ códigos distintos a API | ❌ |
| `rol_menu_permiso` | ❌ | ⚠️ plantillas | — | — | — | — | — | — |
| Menús ERP visibles | ❌ | ✅ si módulo activo | — | — | — | — | — | — |

---

## 8. Diff permisos (medición en repo)

| Conjunto | Cantidad |
|----------|----------|
| Códigos en `require_permission` (`app/modules/**/*.py`) | **113** |
| Códigos en SQL `02_catalog` (S020+S030+S040–S066, sin S067) | **377** |
| Solo en código (sync los crea en startup) | **20** (`admin.*`, `tenant.*`, `modulos.*`) |
| Solo en SQL (sync puede desactivar tras startup) | **284** |
| Intersección código ∩ SQL | **93** |

**Permisos solo SQL relevantes para runtime actual:**

- `core.app.acceder` — R010 depende; **no** usado en `require_permission`.
- `admin.tenant.access`, `admin.platform.access` — S020; **no** usados en endpoints (API usa `admin.usuario.*`, `tenant.cliente.*`).

---

## 9. Riesgos confirmados

1. **Post-bootstrap + startup:** S040–S066 cargan 377 permisos; sync desactiva ~284 no declarados en rutas → ruido y posible confusión en catálogo UI.
2. **Post-onboarding sin R010/R020/S020§6:** admin sin `rol_permiso` → APIs protegidas fallan.
3. **R010 insuficiente:** solo `core.app.acceder`; no otorga los 20 códigos admin/tenant/modulos que la API exige.
4. **S020 desalineado:** asigna `admin.tenant.access`, no `admin.usuario.leer` ni `tenant.cliente.leer`.
5. **Doble modelo:** activar módulo llena `rol_menu_permiso`; API exige `rol_permiso` → tenant puede ver menú sin poder llamar API.
6. **MenuPermissionBinder muerto:** columna `permiso_codigo_requerido` no existe en V020; binder no corre en startup.

---

## 10. Veredicto: dependencia SQL runtime

| Script | ¿Eliminable solo con código actual? | Condición |
|--------|-------------------------------------|-----------|
| **S030** | ✅ Sí | Registrar `core.app.acceder` en registry estático + grant en onboarding |
| **R010** | ✅ Sí | Onboarding (o job post-create) inserta `rol_permiso` para roles nuevos |
| **R020** | ✅ Sí | Onboarding activa `cliente_modulo` SYS_ADMIN (+ ORG recomendado) |
| **S040–S066** | ✅ Sí (PROD) | Confiar en `permission_sync` tras arranque; cold-install opcional |
| **S010** | ❌ No | Catálogo menú sin generador en backend |
| **S020** (menús) | ❌ No (estructura) | Permisos/asignaciones S020 sí migrables |

---

## 11. Archivos backend auditados (lista)

| Componente | Ruta |
|------------|------|
| Onboarding | `app/modules/tenant/application/services/cliente_onboarding_service.py` |
| Activación módulos | `app/modules/modulos/application/services/cliente_modulo_service.py` |
| Plantillas rol | `app/modules/modulos/application/helpers/rol_plantilla_applier.py` |
| Sync permisos | `app/core/authorization/permission_sync_service.py` |
| Startup RBAC | `app/core/authorization/permission_startup.py` |
| Lifespan | `app/main.py` (`rbac_lifespan`) |
| Resolver | `app/core/authorization/permission_resolver.py` |
| Permisos usuario | `app/modules/rbac/application/services/permisos_usuario_service.py` |
| Permisos negocio / rol_permiso API | `app/modules/rbac/application/services/permisos_negocio_service.py` |
| Menú permisos UI | `app/modules/rbac/application/services/permiso_service.py` → `rol_menu_permiso` |
| Menú resolver | `app/core/authorization/menu_resolver.py`, `menu_permission_resolver.py` |
| AuthZ endpoint | `app/core/authorization/rbac.py` |
| User load | `app/core/auth/user_builder.py` |
| Registry | `app/core/authorization/permission_registry.py` |
