# Permission Resolver — Resumen de implementación y guía de pruebas

**Estado:** Stage 1 y Stage 2 implementados. Listo para pruebas.

---

## 1. Resumen de lo implementado

### Stage 1 (Fase A) – Resolver y cache

| Componente | Descripción |
|------------|-------------|
| **Config** | `USE_PERMISSION_RESOLVER`, `PERMISSION_RESOLVER_CACHE_ENABLED`, `PERMISSION_RESOLVER_FILTER_BY_SUBSCRIPTION`, `PERMISSION_RESOLVER_CACHE_TTL` |
| **EffectivePermissions** | DTO con `codes`, `is_super_admin`, `cliente_id`, `usuario_id`, `active_module_codes`, `source`; serializable para cache |
| **PermissionCache** | Cache en memoria con TTL; claves `permissions:{cliente_id}:{usuario_id}` |
| **PermissionResolverService** | `get_effective_permissions()`, `invalidate_for_user()`, `invalidate_for_tenant()`, `get_active_module_codes()` |
| **build_user_with_roles** | Si `USE_PERMISSION_RESOLVER=true`, usa el resolver y asigna `effective.codes` a `permisos`; en error hace **fallback** a `obtener_codigos_permiso_usuario` |
| **Invalidación** | Tras `set_permisos_negocio_rol` → `invalidate_for_tenant`. Tras asignar/revocar rol o eliminar usuario (desactivar roles) → `invalidate_for_user` |

**Filtro por módulos contratados (cliente_modulo):** El resolver y `obtener_codigos_permiso_usuario` devuelven **solo** permisos cuyo `permiso.modulo_id` es NULL (globales: admin, modulos) o pertenece a un módulo activo del tenant en `cliente_modulo` (esta_activo=1, fecha_vencimiento vigente). Flujo: Usuario → Roles → Permisos → Módulos contratados → Permisos finales.

### Stage 2 – Menú y cliente_modulo

| Componente | Descripción |
|------------|-------------|
| **Config** | `USE_MENU_EFFECTIVE_PERMISSIONS` (por defecto `false`) |
| **ModuloMenuService.obtener_menu_usuario** | Parámetro opcional `effective_permission_codes: Optional[List[str]] = None`. Por ahora la lógica del menú no cambia (sigue `rol_menu_permiso`). |
| **GET /modulos-menus/me/** | Si `USE_MENU_EFFECTIVE_PERMISSIONS=true`, pasa `current_user.permisos` al servicio |
| **get_active_module_codes** | Método del resolver para obtener códigos de módulos activos del tenant (billing/feature-flags pueden consumirlo) |
| **Invalidación cliente_modulo** | Tras `activar_modulo_cliente`, `desactivar_modulo_cliente`, `extender_vencimiento` → `invalidate_for_tenant(cliente_id)` |

---

## 2. Variables de entorno (.env)

**Comprobar:** En `.env` y `.env.docker` las líneas deben ser exactamente:

```env
USE_PERMISSION_RESOLVER=true
PERMISSION_RESOLVER_CACHE_ENABLED=true
```

Sin espacios alrededor del `=`, valores `true` en minúsculas. Con eso el resolver y el cache están activos.

Por defecto (si no las pones) todo sigue igual (flags en `false`). Para probar el resolver:

```env
# Activar Permission Resolver en build_user_with_roles (fallback a BD si falla)
USE_PERMISSION_RESOLVER=true

# Opcional: cache en memoria de permisos (recomendado probar primero sin cache)
PERMISSION_RESOLVER_CACHE_ENABLED=false

# Opcional: filtrar permisos por módulos contratados del tenant
PERMISSION_RESOLVER_FILTER_BY_SUBSCRIPTION=false

# TTL del cache de permisos (segundos), solo si CACHE_ENABLED=true
# PERMISSION_RESOLVER_CACHE_TTL=300

# Stage 2: pasar user.permisos al servicio de menú (el servicio aún no los usa para filtrar)
USE_MENU_EFFECTIVE_PERMISSIONS=false
```

---

## 3. Cómo asegurarse de que toda la implementación está bien

### Resumen

- **Tu prueba de GET `/api/v1/modulos-menus/me/` es correcta.** Ese endpoint ya usa el resolver porque depende de `get_current_active_user` → `build_user_with_roles` → resolver (o fallback). Si responde 200 y ves tu menú, el flujo está funcionando.
- Para **confirmar que es el resolver** (y no el fallback) y que el **cache e invalidación** funcionan, sigue los pasos siguientes.

### Paso 1: Ver que el resolver se usa (logs)

1. Pon en `.env`: `LOG_LEVEL=DEBUG` (o al menos asegúrate de que los logs del servidor se vean).
2. Reinicia la API y llama de nuevo a GET `/api/v1/modulos-menus/me/` con un token válido.
3. En los logs del servidor busca:
   - `[PERMISSION_RESOLVER]` → el resolver se ejecutó.
   - `[PERMISSION_RESOLVER] cache hit for ...` → en la **segunda** petición con el mismo usuario, el cache respondió.

Si ves `[USER_BUILDER] Permission resolver falló, usando fallback` entonces se usó el fallback (BD); en ese caso el endpoint sigue funcionando pero el resolver falló (revisar excepción en logs).

### Paso 2: Probar un endpoint que exija un permiso

Así compruebas que `user.permisos` (llenado por el resolver) se usa en autorización:

1. Login (POST login) y guarda el `access_token`.
2. Llama a un endpoint protegido con `require_permission`, por ejemplo:
   - `GET /api/v1/modulos-menus/me/` (requiere `modulos.menu.leer`).
   - O cualquier otro que uses con `require_permission("algo.recurso.accion")`.
3. Debe devolver 200 si el usuario tiene el permiso, o 403 si no. Mismo comportamiento que antes de activar el resolver.

### Paso 3: Probar invalidación del cache (opcional pero recomendado)

Con `PERMISSION_RESOLVER_CACHE_ENABLED=true`:

1. Login con un usuario que tenga un rol R.
2. Llama dos veces a GET `/api/v1/modulos-menus/me/` (o a otro endpoint que use el usuario). La segunda puede ser cache hit (ver logs).
3. **Cambia los permisos del rol R** (PUT al endpoint de permisos-negocio del rol, o asigna/revoca otro rol a ese usuario).
4. Vuelve a llamar a GET `/api/v1/modulos-menus/me/` con el mismo token. Debe seguir respondiendo 200 y, si el cambio afecta al menú o a algún `require_permission`, debe reflejar los **nuevos** permisos (no los cacheados). Eso confirma que la invalidación funcionó.

### Paso 4: Script rápido de verificación (opcional)

Puedes ejecutar esto en la raíz del proyecto (con la app levantada o no; si no está levantada solo verifica imports y config):

```bash
cd d:\base_multi_tenant_fastapi
python -c "
from app.core.config import settings
assert getattr(settings, 'USE_PERMISSION_RESOLVER') == True, 'USE_PERMISSION_RESOLVER debe ser True'
assert getattr(settings, 'PERMISSION_RESOLVER_CACHE_ENABLED') == True, 'PERMISSION_RESOLVER_CACHE_ENABLED debe ser True'
from app.core.authorization.permission_resolver import get_permission_resolver
from app.core.auth.user_builder import build_user_with_roles
print('Config y imports OK. Resolver activo. build_user_with_roles usa el resolver cuando se llama con usuario válido.')
"
```

Si no hay excepción, la config y los módulos están bien.

---

## 4. Checklist de pruebas sugeridas

### 4.1 Sin activar flags (comportamiento actual)

- [ ] Login con usuario normal y con super_admin: correcto.
- [ ] Endpoints protegidos con `require_permission("x.y.z")`: permiten o deniegan según roles/permisos actuales.
- [ ] GET `/api/v1/modulos-menus/me/`: menú correcto según `rol_menu_permiso`.
- [ ] Asignar/revocar rol a un usuario: menú y permisos se actualizan en el siguiente request (sin cache de permisos).

### 4.2 Con USE_PERMISSION_RESOLVER=true (sin cache)

- [ ] Login: mismo resultado que sin flag (permisos desde BD vía resolver).
- [ ] Endpoints con `require_permission`: mismo comportamiento.
- [ ] Super_admin: no se consulta BD ni cache; `permisos` puede ser `[]` y el bypass en `has_permission` sigue funcionando.
- [ ] Forzar un error en el resolver (ej. BD caída o timeout): debe hacerse fallback a `obtener_codigos_permiso_usuario` y no romper el login (revisar logs de fallback).

### 4.3 Con USE_PERMISSION_RESOLVER=true y PERMISSION_RESOLVER_CACHE_ENABLED=true

- [ ] Primer login de un usuario: permisos desde BD.
- [ ] Segundo request con el mismo usuario/tenant: mismo resultado (puede comprobarse log de cache hit si está en DEBUG).
- [ ] Cambiar permisos de un rol (PUT permisos-negocio del rol): siguiente request del usuario con ese rol debe reflejar los nuevos permisos (invalidación por tenant).
- [ ] Asignar o revocar un rol a un usuario: siguiente request de ese usuario debe reflejar el cambio (invalidación por usuario).

### 4.4 Invalidación al actualizar cliente_modulo

- [ ] Con `PERMISSION_RESOLVER_FILTER_BY_SUBSCRIPTION=true` y cache activo: activar o desactivar un módulo para el tenant; siguiente resolución de permisos para ese tenant debe usar datos actualizados (cache de permisos invalidado por tenant).

### 4.5 Stage 2 – USE_MENU_EFFECTIVE_PERMISSIONS=true

- [ ] GET `/modulos-menus/me/`: respuesta igual que con el flag en `false` (el servicio recibe `effective_permission_codes` pero aún no filtra por ellos).
- [ ] Verificar en logs o debug que el servicio recibe la lista de códigos cuando el flag está activo.

### 3.6 get_active_module_codes (opcional)

- [ ] Llamar desde un script o endpoint de prueba: `resolver = get_permission_resolver(); codes = await resolver.get_active_module_codes(cliente_id)` y comprobar que devuelve los códigos de módulos activos del tenant (según `cliente_modulo` + `modulo`).

---

## 5. Archivos tocados (referencia)

- `app/core/config.py` – Flags.
- `app/core/authorization/effective_permissions.py` – DTO.
- `app/core/authorization/permission_cache.py` – Cache en memoria.
- `app/core/authorization/permission_resolver.py` – Servicio y `get_active_module_codes`.
- `app/core/auth/user_builder.py` – Integración con fallback.
- `app/modules/rbac/application/services/permisos_negocio_service.py` – Invalidación tras `set_permisos_negocio_rol`.
- `app/modules/users/application/services/user_service.py` – Invalidación tras asignar/revocar rol y tras eliminar usuario.
- `app/modules/modulos/application/services/modulo_menu_service.py` – Parámetro `effective_permission_codes`.
- `app/modules/modulos/application/services/cliente_modulo_service.py` – Invalidación tras activar/desactivar/extender vencimiento.
- `app/modules/modulos/presentation/endpoints_menus.py` – Paso de `permisos` a `obtener_menu_usuario` cuando el flag está activo.

---

## 6. Cuándo considerar listo para producción

- Todas las pruebas del checklist pasan con flags activados en entorno de staging.
- Fallback verificado ante fallo del resolver o del cache.
- Invalidaciones comprobadas (cambio de rol, de permisos de rol, activar/desactivar módulo).
- Sin regresiones en menú ni en endpoints protegidos por `require_permission`.

Cuando esté validado, se puede dejar `USE_PERMISSION_RESOLVER=true` (y opcionalmente `PERMISSION_RESOLVER_CACHE_ENABLED=true`) en producción. `USE_MENU_EFFECTIVE_PERMISSIONS` puede activarse cuando se implemente el filtro por permiso en ítems de menú (p. ej. con `permiso_requerido_id` en `modulo_menu`).
