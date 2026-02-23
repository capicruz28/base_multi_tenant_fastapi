# Análisis arquitectónico: Permission Resolver Centralizado + Cache

**Rol:** Software Architect Senior (SaaS multi-tenant, RBAC, permisos enterprise)  
**Objetivo:** Identificar el patrón actual de permisos e evaluar la introducción de un **Permission Resolver Centralizado + Cache** sin romper la funcionalidad existente.  
**Restricción:** Análisis sin modificación de código; no refactorizar ni cambiar contratos.

---

## 1. Patrón actual detectado

### 1.1 Resumen ejecutivo

El sistema implementa un **RBAC híbrido con LBAC (Level-Based Access Control)** y **dos fuentes de permisos separadas**:

- **Permisos de menú (UI):** `rol_menu_permiso` + `cliente_modulo` → controlan qué módulos/pantallas ve el usuario y con qué acciones por ítem (puede_ver, puede_crear, etc.).
- **Permisos de negocio (API):** `permiso` (catálogo) + `rol_permiso` → controlan acciones reales en backend (ej. `org.area.actualizar`, `admin.usuario.leer`).

La validación de permisos **no está centralizada**: se reparte entre construcción del usuario en cada request, dependencias por endpoint y lógica de menú en un servicio específico. **No existe hoy un único “resolver” que calcule permisos efectivos**; cada capa obtiene o calcula lo que necesita.

**Términos arquitectónicos aplicables:**

- **RBAC distribuido:** permisos se validan en múltiples puntos (deps, rbac.has_permission, modulo_menu_service, permisos_usuario_service).
- **Policy-based checks en capa de presentación:** cada endpoint declara `Depends(require_permission("modulo.accion.verbo"))`.
- **Dual permission model:** menú (rol_menu_permiso) vs negocio (rol_permiso + permiso) sin unión formal en un solo modelo.
- **Request-scoped user build:** el usuario completo (con roles y permisos de negocio) se construye en cada request vía `get_current_active_user` → `build_user_with_roles`, sin cache de permisos.

---

### 1.2 Carga de permisos al iniciar sesión / en cada request

- **Login (AuthService.authenticate_user):**
  - Valida credenciales y tenant.
  - Calcula **nivel de acceso** (`get_user_access_level_info`: max nivel de roles, si es super_admin) y lo devuelve en el payload del usuario.
  - **No** carga la lista de códigos de permiso de negocio en el login; esa lista **no** va en el token.
- **Cada request (get_current_active_user en deps.py):**
  1. Decodifica JWT y verifica revocación (Redis blacklist).
  2. Obtiene contexto mínimo: `get_user_auth_context(username, request_cliente_id)` → usuario, roles (nombres), nivel_acceso, is_superadmin. **Sin permisos de negocio.**
  3. Valida tenant: `validate_tenant_access(context, request_cliente_id)`.
  4. Construye usuario completo: `build_user_with_roles(username, request_cliente_id)`:
     - Lee usuario + roles (RolRead) desde BD.
     - **Carga permisos de negocio:** `permisos_usuario_service.obtener_codigos_permiso_usuario(usuario_id, cliente_id, database_type)` → `usuario_rol` ⋈ `rol_permiso` ⋈ `permiso` (single) o dos pasos (dedicada: rol_permiso en tenant, permiso en central).
     - Devuelve `UsuarioReadWithRoles` con `roles` y `permisos: List[str]` (códigos).
  5. Sobrescribe nivel/tipo desde token si existe (`access_level`, `is_super_admin`, `user_type`).

**Conclusión:** Los permisos de negocio se cargan **en cada request**, en `build_user_with_roles`, no en el login. No hay cache de permisos por usuario/tenant.

---

### 1.3 Dónde se validan permisos

| Dónde | Qué se valida | Fuente de datos |
|-------|----------------|------------------|
| **Backend – Endpoints** | Permisos de negocio (ej. `org.area.actualizar`) | `require_permission(perm)` → `has_permission(user, perm)` → `user.permisos` (lista ya cargada en el mismo request) |
| **Backend – RBAC** | `has_permission(user, permission)` | 1) Super Admin → True. 2) `permission in user.permisos`. 3) (Antes tenant_admin bypass; actualmente eliminado) |
| **Backend – Menú** | Qué ítems de menú ver y con qué acciones | `ModuloMenuService.get_menu_usuario`: 1) Módulos activos (ClienteModuloTable) + menús desde BD central. 2) Si no super_admin/tenant_admin: permisos por ítem desde `rol_menu_permiso` (BD tenant). Super_admin/tenant_admin reciben todos los menús con permisos completos sin consultar rol_menu_permiso |
| **Frontend** | Visibilidad de módulos/pantallas y botones | Menú devuelto por API (`GET /modulos-menus/me/` o equivalente) y/o datos de usuario (roles/permisos si se exponen). No hay un “resolver” centralizado en backend que el frontend consulte aparte del menú y del usuario |

No hay un único punto que “resuelva” permisos efectivos; la validación está **distribuida** entre dependencias de FastAPI, módulo RBAC y servicio de menú.

---

### 1.4 Relación entre entidades

```
cliente (tenant)
  ├── cliente_modulo (módulos contratados por tenant; fecha_vencimiento, esta_activo)
  ├── usuario (cliente_id)
  │     └── usuario_rol (usuario_id, rol_id, cliente_id, es_activo, fecha_expiracion)
  ├── rol (cliente_id nullable para roles sistema)
  │     ├── rol_permiso (rol_id, cliente_id, permiso_id)  → permisos de NEGOCIO
  │     └── rol_menu_permiso (rol_id, cliente_id, menu_id, puede_ver, puede_crear, ...)  → permisos de MENÚ
  └── (conexión BD dedicada opcional)

permiso (catálogo global, BD central)
  └── codigo (ej. org.area.actualizar)

modulo (catálogo global, BD central)
  └── modulo_menu (menús por módulo)
        └── Referenciado por rol_menu_permiso.menu_id (en tenant o central según arquitectura)
```

- **subscription_modules:** módulos que el tenant tiene activos = `ClienteModuloTable` (cliente_id, modulo_id, esta_activo, fecha_vencimiento).
- **role_permissions (negocio):** `rol_permiso` + `permiso.codigo` por los roles del usuario en ese tenant.
- **menu_permissions:** por ítem de menú, qué puede hacer el rol = `rol_menu_permiso` (puede_ver, puede_crear, etc.).

No hay una tabla única “effective_permissions”; la “intersección” es implícita en el código (menú filtrado por módulos activos + permisos de menú por rol; API por lista de códigos de permiso del usuario).

---

### 1.5 Lógica duplicada y verificaciones distribuidas

- **Duplicación:**
  - **Nivel de acceso / tipo de usuario:** calculado en login (`get_user_access_level_info`), en `get_user_auth_context` (roles + nivel + is_superadmin), y en `build_user_with_roles` (nivel desde roles). El token puede llevar level/type y sobrescribir en deps.
  - **Permisos de negocio:** solo se calculan en `build_user_with_roles` vía `obtener_codigos_permiso_usuario`. No hay otra fuente, pero **cada request** vuelve a ejecutar esa ruta (y las queries asociadas).
- **Verificaciones distribuidas:**
  - **Auth/tenant:** deps (`get_user_auth_context`, `validate_tenant_access`), y en rutas que comparan `rol_cliente_id` con `current_user.cliente_id`.
  - **Autorización de negocio:** en cada endpoint que usa `Depends(require_permission("x.y.z"))` → `has_permission(current_user, "x.y.z")` (mismo usuario ya cargado).
  - **Menú:** en `ModuloMenuService.get_menu_usuario` (módulos activos + rol_menu_permiso o atajo super_admin/tenant_admin).

No hay un “single source of truth” en runtime para “effective_permissions”; el único conjunto explícito de códigos de permiso es `user.permisos` construido una vez por request.

---

### 1.6 Diagrama conceptual (texto)

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │                        REQUEST                               │
                    │  JWT (sub, cliente_id, access_level, is_super_admin, ...)    │
                    └───────────────────────────┬─────────────────────────────────┘
                                                 │
     ┌───────────────────────────────────────────▼───────────────────────────────────────────┐
     │  get_current_active_user (deps.py)                                                     │
     │  1. get_user_auth_context(username, request_cliente_id)  → usuario, roles, nivel       │
     │  2. validate_tenant_access(context, request_cliente_id)                               │
     │  3. build_user_with_roles(username, request_cliente_id)                               │
     │        ├── Usuario + Roles (UsuarioRol ⋈ Rol)                                         │
     │        └── permisos_usuario_service.obtener_codigos_permiso_usuario()                 │
     │             → usuario_rol ⋈ rol_permiso ⋈ permiso  → List[str] códigos               │
     │  4. UsuarioReadWithRoles(roles=..., permisos=permisos_codigos)                         │
     └───────────────────────────┬───────────────────────────────────────────────────────────┘
                                  │
     ┌────────────────────────────▼─────────────────────────────────────────────────────────┐
     │  Endpoint con Depends(require_permission("org.area.actualizar"))                       │
     │  → has_permission(current_user, "org.area.actualizar")                                 │
     │       → super_admin? True | permission in user.permisos? True/False                    │
     └────────────────────────────────────────────────────────────────────────────────────────┘

     Menú (paralelo, no usa user.permisos):
     ┌───────────────────────────────────────────────────────────────────────────────────────┐
     │  GET /modulos-menus/me/  (ModuloMenuService.get_menu_usuario)                        │
     │  1. BD central: módulos activos (ClienteModulo) + modulo_menu                         │
     │  2. Si super_admin o tenant_admin → todos los ítems con permisos true                 │
     │  3. Si no: BD tenant → rol_menu_permiso ⋈ usuario_rol → permisos por menu_id          │
     │  4. Combinar menús + permisos por ítem → respuesta jerárquica                         │
     └───────────────────────────────────────────────────────────────────────────────────────┘

     effective_permissions (conceptual) hoy:
       = (permisos por rol_permiso del usuario en el tenant)  ← solo negocio
       Menú = f(cliente_modulo, rol_menu_permiso, usuario_rol)  ← separado
     No hay: effective = (subscription_modules) AND (role_permissions) AND (menu_permissions)
```

---

## 2. Compatibilidad con Permission Resolver centralizado

### 2.1 Fórmula objetivo

```text
effective_permissions = (subscription_modules) AND (role_permissions) AND (menu_permissions)
```

- **subscription_modules:** módulos activos para el cliente (ClienteModuloTable).
- **role_permissions:** códigos de permiso de negocio del usuario (rol_permiso ⋈ permiso) por sus roles en el tenant.
- **menu_permissions:** en el sistema actual son por ítem de menú (puede_ver, puede_crear, etc.), no por código de permiso; se podría definir “menu_permissions” como el conjunto de códigos o ítems a los que el usuario tiene acceso según rol_menu_permiso.

Para un resolver “centralizado” útil para la API, la parte crítica es **role_permissions** ya acotada por **subscription_modules** (solo permisos de módulos que el cliente tiene contratados). La parte de menú puede seguir siendo un flujo separado (construcción de árbol de menú) o integrarse en el resolver como una vista “qué ítems/acciones de menú tiene”.

### 2.2 Qué partes ya existen y son compatibles

- **role_permissions:** ya se calculan en `permisos_usuario_service.obtener_codigos_permiso_usuario` y se exponen en `user.permisos`. El resolver puede reutilizar esta lógica o llamar al mismo servicio.
- **subscription_modules:** ya se usan en `ModuloMenuService.get_menu_usuario` (ClienteModuloTable con cliente_id, esta_activo, fecha_vencimiento). No hay hoy un “set de códigos de módulo activos” reutilizable; se puede extraer o replicar sin tocar el flujo actual.
- **Usuario y tenant:** ya están resueltos en el request (context, cliente_id, usuario_id). Un resolver puede recibir (usuario_id, cliente_id) y opcionalmente (database_type) y devolver permisos efectivos.
- **RBAC:** `has_permission(user, permission)` recibe un usuario con `user.permisos`. Si el resolver devuelve la misma lista (o un subconjunto filtrado por módulos activos), la interfaz “lista de códigos” se mantiene.
- **Redis/cache:** ya existe infraestructura (revocación de tokens, cache de metadata de conexión, redis_cache con get_cached/set_cached). Se puede añadir cache de “permisos por usuario/tenant” sin cambiar contratos.

### 2.3 Qué piezas faltan

- **Un único punto de cálculo “effective_permissions”:** no existe. Hay que añadir un componente (Permission Resolver) que:
  - Entrada: usuario_id, cliente_id, tenant context/database_type.
  - Salida: lista de códigos de permiso efectivos (y opcionalmente metadatos de menú o módulos activos).
  - Internamente: (opcional) filtrar permisos de negocio por “módulo del permiso pertenece a cliente_modulo activo”. Hoy permiso tiene modulo_id; cliente_modulo tiene modulo_id; se puede hacer el AND.
- **Filtro explícito subscription ∩ role_permissions:** hoy no se aplica: un usuario puede tener en `user.permisos` un código de un módulo que el tenant no tiene activo. Si se desea “solo permisos de módulos contratados”, hay que añadir ese filtro en el resolver.
- **Cache de permisos por (usuario_id, cliente_id):** no existe. Cada request reconstruye el usuario y vuelve a llamar a `obtener_codigos_permiso_usuario`. Añadir cache es nuevo comportamiento detrás del mismo contrato (lista de códigos en el usuario).
- **Integración menú ↔ permisos de negocio:** hoy están separados. Un resolver podría además exponer “permisos de menú” (o ítems visibles) para el frontend, pero no es obligatorio para la primera versión.

### 2.4 Dependencias que podrían romperse

- **build_user_with_roles** y **get_current_active_user:** si el resolver sustituye la llamada a `obtener_codigos_permiso_usuario` por “resolver.get_effective_permissions(usuario_id, cliente_id)”, hay que mantener la misma forma de salida (List[str]) para no romper UsuarioReadWithRoles ni has_permission.
- **ModuloMenuService.get_menu_usuario:** si en el futuro el menú se alimenta desde el resolver (p.ej. “solo ítems cuyos permisos están en effective_permissions”), hay que mantener compatibilidad con la respuesta actual (estructura jerárquica, puede_ver, etc.) o añadir un camino alternativo con feature flag.
- **Permisos por rol en BD dedicada:** hoy `obtener_codigos_permiso_usuario` hace 2 pasos (rol_permiso en tenant, permiso en central). El resolver debe reutilizar esa lógica o abstraerla para no duplicar conexiones ni reglas de tenant/central.
- **Super Admin:** hoy tiene acceso total sin mirar `user.permisos`. El resolver puede devolver “todos” los códigos para super_admin o un flag “bypass”; has_permission debe seguir tratando super_admin igual que ahora.

---

## 3. Estrategia incremental y backward-compatible

Principios: **no eliminar lógica actual**, **no cambiar contratos API**, **no romper frontend**, **no alterar flujos actuales**. Sí: **añadir capa nueva**, **adapters**, **cache**, **middleware o dependencia opcional**, **feature flag**.

### 3.1 Dónde viviría el Permission Resolver

- **Ubicación sugerida:** `app/core/authorization/permission_resolver.py` (o `app/modules/rbac/application/services/permission_resolver_service.py` si se prefiere dentro de RBAC).
- **Responsabilidad única:** dado (usuario_id, cliente_id, opciones), devolver:
  - `effective_permissions: List[str]` (códigos),
  - opcional: `active_module_codes: Set[str]`, `metadata` (para cache y auditoría).
- **Dependencias:** reutilizar `permisos_usuario_service.obtener_codigos_permiso_usuario`, y opcionalmente un servicio que devuelva “módulos activos del cliente”. No sustituir esos servicios en el primer paso; el resolver los usa como fuentes.

### 3.2 Integración progresiva

1. **Fase 1 – Solo lectura:** implementar el resolver que calcula `effective_permissions` (y si se desea, subscription_filter). Nadie lo usa aún en producción; solo tests o un endpoint de diagnóstico (ej. `GET /me/permissions`) protegido por admin.
2. **Fase 2 – Cache:** el resolver consulta primero cache (Redis o memoria) por clave `permissions:{cliente_id}:{usuario_id}`; si no hay hit, calcula y guarda con TTL. Invalidez: al cambiar rol_permiso o cliente_modulo, invalidar esa clave (o patrón).
3. **Fase 3 – Sustitución opcional en build_user_with_roles:** detrás de un feature flag (ej. `USE_PERMISSION_RESOLVER`), en `build_user_with_roles` llamar al resolver en lugar de `obtener_codigos_permiso_usuario`. Misma firma de salida (`List[str]`). Si el flag está en False, comportamiento actual.
4. **Fase 4 – Filtro por suscripción (opcional):** en el resolver, aplicar AND con módulos activos del cliente (permiso.modulo_id ∈ cliente_modulo activos). Activable con otro flag para no cambiar comportamiento hasta validar.

### 3.3 Coexistencia con el sistema actual

- **Sin flags:** todo sigue igual; deps → build_user_with_roles → permisos_usuario_service.
- **Con flag USE_PERMISSION_RESOLVER=True:** build_user_with_roles obtiene permisos del resolver (que internamente puede usar el mismo servicio + cache + filtro). `user.permisos` sigue siendo List[str]; require_permission y has_permission no cambian.
- **Menú:** sigue igual; get_menu_usuario no depende del resolver en la primera implementación. Más adelante se puede añadir “menú basado en resolver” con otro flag.

### 3.4 Activación por feature flag

- `USE_PERMISSION_RESOLVER` (default False): usar resolver en build_user_with_roles.
- `PERMISSION_RESOLVER_CACHE_ENABLED` (default False): resolver usa cache.
- `PERMISSION_RESOLVER_FILTER_BY_SUBSCRIPTION` (default False): effective = role_permissions ∩ subscription_modules.

Configuración en `app/core/config.py` sin alterar comportamiento por defecto.

---

## 4. Evaluación de riesgo por cambio

| Cambio | Clasificación | Notas |
|--------|----------------|-------|
| Añadir módulo `permission_resolver.py` que solo calcula permisos (llamando a servicios existentes) | 🟢 Seguro | No toca flujos actuales; solo código nuevo y tests. |
| Añadir cache de permisos por (usuario_id, cliente_id) en Redis/memoria con TTL | 🟢 Seguro | Si se usa solo dentro del resolver y el resolver no está en camino crítico todavía, riesgo bajo. Al activar resolver + cache, invalidez correcta evita datos obsoletos. |
| Feature flag para obtener permisos vía resolver en build_user_with_roles | 🟡 Riesgo moderado | Mismo contrato (List[str]); riesgo de fallos en resolver (excepciones, timeouts) o diferencias sutiles (orden, duplicados). Mitigación: fallback a obtener_codigos_permiso_usuario si el resolver falla; tests A/B. |
| Filtrar effective_permissions por subscription (módulos activos) | 🟡 Riesgo moderado | Puede quitar permisos que hoy tiene el usuario (ej. módulo desactivado pero rol_permiso sigue). Riesgo funcional si el frontend o integraciones asumen que user.permisos incluye todos los del rol. Mitigación: flag y comunicación. |
| Exponer GET /me/permissions o similar desde el resolver | 🟢 Seguro | Solo añade endpoint; no cambia comportamiento de los existentes. |
| Cambiar get_menu_usuario para usar resolver como fuente de “quién puede ver qué” | 🔴 Riesgo alto | Cambia la forma en que se construye el menú; posibles diferencias con rol_menu_permiso actual. Solo recomendable en fase posterior, con flag y pruebas exhaustivas. |

---

## 5. Plan de implementación por fases

### Fase 1 — Observación (read-only resolver)

- **Objetivo:** Tener un resolver que calcule effective_permissions sin usarlo en el flujo principal.
- **Archivos nuevos:** `app/core/authorization/permission_resolver.py` (o bajo rbac/application/services). Opcional: endpoint `GET /api/v1/me/permissions` que llame al resolver (leyendo usuario del token).
- **Archivos tocados:** ninguno en el flujo de login/request (solo config si se añade flag sin uso).
- **Impacto:** Cero en producción mientras no se llame al resolver desde build_user_with_roles.
- **Rollback:** Eliminar el módulo y el endpoint; no hay dependientes.

### Fase 2 — Cache de permisos

- **Objetivo:** Dentro del resolver, cachear resultado por (cliente_id, usuario_id) con TTL (ej. 5–15 min).
- **Archivos nuevos:** ninguno obligatorio si el resolver usa `app/infrastructure/cache/redis_cache` o el patrón existente.
- **Archivos tocados:** permission_resolver (lógica de get/set/invalidación). Puntos de invalidación: donde se actualice rol_permiso o usuario_rol (y si se aplica filtro por suscripción, cliente_modulo).
- **Impacto:** Menor latencia y menos carga en BD para permisos cuando el resolver esté activo.
- **Rollback:** Desactivar cache (flag o TTL=0); resolver sigue calculando en frío.

### Fase 3 — Validación central opcional

- **Objetivo:** Usar el resolver en get_current_active_user cuando USE_PERMISSION_RESOLVER=True; mantener mismo contrato user.permisos.
- **Archivos tocados:** `app/core/auth/user_builder.py` (build_user_with_roles): si flag, llamar resolver en lugar de obtener_codigos_permiso_usuario; en caso de error, fallback a obtener_codigos_permiso_usuario. `app/core/config.py`: flags.
- **Impacto:** Un solo camino de verdad para “permisos del usuario” en cada request cuando el flag está activo; posibilidad de filtro por suscripción en el mismo resolver.
- **Rollback:** Flag a False; vuelta al comportamiento actual.

### Fase 4 — Migración gradual

- **Objetivo:** Activar resolver + cache en entornos (dev → staging → producción) y opcionalmente activar filtro por suscripción.
- **Archivos tocados:** Config por entorno; documentación y operación (invalidación de cache si se cambian roles/permisos).
- **Impacto:** Mejor rendimiento y base para futuras extensiones (menú desde resolver, auditoría de permisos).
- **Rollback:** Flags a False; posible limpieza de claves de cache si se desactiva definitivamente.

---

## 6. Diagrama conceptual del estado objetivo (resolver integrado)

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │                        REQUEST                               │
                    └───────────────────────────┬─────────────────────────────────┘
                                                 │
     ┌───────────────────────────────────────────▼───────────────────────────────────────────┐
     │  get_current_active_user                                                              │
     │  1. get_user_auth_context(...)                                                        │
     │  2. validate_tenant_access(...)                                                       │
     │  3. build_user_with_roles(...)                                                        │
     │        ┌─ if USE_PERMISSION_RESOLVER:                                                 │
     │        │     resolver.get_effective_permissions(usuario_id, cliente_id)                │
     │        │        ├─ cache.get(key) ??                                                  │
     │        │        ├─ subscription_modules (opcional)                                    │
     │        │        ├─ role_permissions (permisos_usuario_service o mismo cálculo)         │
     │        │        └─ cache.set(key, result, ttl)                                         │
     │        └─ else: obtener_codigos_permiso_usuario(...)  [actual]                        │
     │  4. UsuarioReadWithRoles(roles=..., permisos=effective_permissions)                  │
     └───────────────────────────┬───────────────────────────────────────────────────────────┘
                                  │
     ┌────────────────────────────▼─────────────────────────────────────────────────────────┐
     │  require_permission / has_permission  (sin cambios)                                   │
     │  → permission in user.permisos                                                        │
     └──────────────────────────────────────────────────────────────────────────────────────┘
```

---

**Documento generado como auditoría arquitectónica; sin generación de código ni refactorización. Compatible con evolución tipo Salesforce/Atlassian/Notion: capa nueva, flags y rollout gradual.**
