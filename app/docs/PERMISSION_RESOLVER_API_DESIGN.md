# Permission Resolver — API interna (diseño)

**Rol:** Staff Engineer de plataforma SaaS  
**Objetivo:** Definir la interfaz exacta (API interna) del Permission Resolver compatible con el sistema actual, sin implementar código.  
**Integración:** Plug-and-play con `build_user_with_roles()`.

---

## 1. Contrato principal: drop-in para `build_user_with_roles()`

El único consumidor actual de la lista de permisos es:

```python
# user_builder.py (actual)
permisos_codigos = await obtener_codigos_permiso_usuario(usuario_id=..., cliente_id=..., database_type=...)
UsuarioReadWithRoles(..., permisos=permisos_codigos)  # permisos: List[str]
```

El resolver debe poder sustituir esa llamada manteniendo el contrato:

- **Entrada:** `usuario_id`, `cliente_id`, y opcionalmente `database_type` y `is_super_admin`.
- **Salida para asignar a `user.permisos`:** algo que se pueda usar como **`List[str]`** (lista de códigos de permiso).  
  Por tanto el resolver puede devolver:
  - directamente `List[str]`, o
  - un objeto que implemente **duck typing** para ser equivalente a `List[str]` donde se use (p. ej. `permission in user.permisos` y construcción de `UsuarioReadWithRoles`).

Se define un tipo **EffectivePermissions** que expone esa lista y metadatos, y que es **serializable** para cache.

---

## 2. Métodos públicos del Permission Resolver

Se asume un **servicio/clase** con interfaz async. Nombre propuesto: `PermissionResolverService` (o `PermissionResolver`).

### 2.1 Método principal: `get_effective_permissions`

Único método que debe usar `build_user_with_roles()`.

**Firma:**

```
get_effective_permissions(
    usuario_id: UUID,
    cliente_id: UUID,
    *,
    database_type: Literal["single", "multi"] = "single",
    is_super_admin: bool = False,
    filter_by_subscription: bool = False,
) -> EffectivePermissions
```

**Semántica:**

- Calcula los permisos efectivos del usuario en el tenant dado.
- Si `is_super_admin=True`, devuelve un objeto que representa “todos los permisos” sin ejecutar queries de rol_permiso (ver sección Super Admin).
- Si `filter_by_subscription=True`, aplica la intersección con módulos activos del cliente (cliente_modulo); si no, solo role_permissions (comportamiento actual).
- `database_type` se usa igual que en `permisos_usuario_service` (single = una BD, multi = tenant + central para permiso).

**Uso desde `build_user_with_roles()`:**

- Se obtiene `EffectivePermissions` con esta llamada.
- Se asigna a `UsuarioReadWithRoles` usando la propiedad que expone la lista de códigos (p. ej. `.codes` o conversión a lista). Ver sección EffectivePermissions.

---

### 2.2 Método de invalidación (para uso desde servicios que escriben)

Para que los servicios que modifican `rol_permiso` o `usuario_rol` invaliden cache sin conocer la implementación interna del resolver.

**Firma:**

```
invalidate_for_user(usuario_id: UUID, cliente_id: UUID) -> None
invalidate_for_tenant(cliente_id: UUID) -> None
```

- **invalidate_for_user(usuario_id, cliente_id):** invalida la entrada de cache para ese par (usuario, tenant). Se llama tras cambios en `usuario_rol` o en `rol_permiso` que afecten a ese usuario en ese cliente.
- **invalidate_for_tenant(cliente_id):** invalida todas las entradas de cache del tenant (p. ej. al actualizar en masa permisos de un rol usado por muchos usuarios). Opcional; puede implementarse como “borrar por patrón de clave”.

Ambos son idempotentes y pueden ser no-op si el cache está desactivado.

---

### 2.3 Método opcional: batch (evitar N+1 en flujos futuros)

Si en el futuro se necesita resolver permisos para varios usuarios del mismo tenant en una sola operación (p. ej. listado de usuarios con columna “permisos” o auditoría):

**Firma:**

```
get_effective_permissions_batch(
    requests: Sequence[Tuple[UUID, UUID]],  # (usuario_id, cliente_id)
    *,
    database_type: Literal["single", "multi"] = "single",
    filter_by_subscription: bool = False,
) -> Dict[Tuple[UUID, UUID], EffectivePermissions]
```

- **Entrada:** lista de pares `(usuario_id, cliente_id)`.
- **Salida:** diccionario que mapea cada par al `EffectivePermissions` correspondiente.
- Implementación: una o pocas queries por tenant (p. ej. todos los usuario_id del mismo cliente_id en una sola consulta usuario_rol ⋈ rol_permiso ⋈ permiso), luego repartir resultados por usuario. No se define aquí el detalle SQL; la interfaz garantiza que el cliente no hace N llamadas a `get_effective_permissions`.

No es necesario para el plug-and-play con `build_user_with_roles()` (que solo pide un usuario por request).

---

## 3. Estructura del objeto `EffectivePermissions`

Objeto inmutable (o de solo lectura) que representa el resultado de resolver permisos para un usuario en un tenant.

### 3.1 Campos (atributos o propiedades)

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `codes` | `List[str]` | Sí | Lista de códigos de permiso (ej. `["org.area.leer", "admin.usuario.actualizar"]`). Es la única fuente de verdad para “qué permisos tiene el usuario” en ese tenant. |
| `is_super_admin` | `bool` | Sí | Si el resultado corresponde a un super admin (acceso total). Cuando True, `codes` puede ser la lista vacía y el consumidor debe tratar al usuario como “tiene todos los permisos”. |
| `cliente_id` | `UUID` | Sí | Tenant para el que se resolvieron los permisos. |
| `usuario_id` | `UUID` | Sí | Usuario resuelto. |
| `active_module_codes` | `Optional[Set[str]]` o `Optional[List[str]]` | No | Si `filter_by_subscription=True`, códigos de módulos activos del cliente usados en el filtro. Útil para auditoría o diagnóstico. |
| `source` | `Literal["cache", "database", "super_admin"]` | No | Origen del resultado (cache hit, cálculo desde BD, o atajo super_admin). Opcional, para métricas. |

### 3.2 Contrato para plug-and-play con `build_user_with_roles()`

- **Para asignar a `UsuarioReadWithRoles(permisos=...)`:**  
  El resolver debe exponer la lista de códigos de forma que se pueda usar como `List[str]`:

  - Opción A (recomendada): propiedad **`codes`** y que el consumidor haga `permisos=result.codes`.
  - Opción B: que `EffectivePermissions` sea iterable y que `list(result)` sea la lista de códigos (duck typing con `List[str]`).

- **Para `has_permission(user, permission)`:**  
  Hoy se hace `permission in user.permisos`. Por tanto `user.permisos` debe ser una secuencia de strings. Si `user.permisos = effective_permissions.codes`, no hay cambio. Si en el futuro se quisiera que `user.permisos` fuera el objeto EffectivePermissions, debería implementar `__contains__(self, code: str)` delegando en `code in self.codes` y, si `is_super_admin`, devolver True para cualquier código. Eso permite no tocar `has_permission`. Por ahora el diseño recomienda asignar `result.codes` a `user.permisos`.

### 3.3 Serialización para cache

El objeto debe ser **serializable a JSON** (y deserializable) para Redis/memoria:

- Formato sugerido:

```json
{
  "codes": ["org.area.leer", "admin.usuario.actualizar"],
  "is_super_admin": false,
  "cliente_id": "uuid-string",
  "usuario_id": "uuid-string",
  "active_module_codes": ["org", "admin"],
  "source": "database"
}
```

- Tipos: `codes` array de string; `active_module_codes` array de string (o null); UUIDs como string; `source` string opcional.
- Al deserializar se reconstruye una instancia de `EffectivePermissions` (o un DTO equivalente) con los mismos campos.

---

## 4. Estrategia de cache keys

- **Formato de clave:**  
  `permissions:{cliente_id}:{usuario_id}`  
  con `cliente_id` y `usuario_id` en representación canónica (mismo formato en toda la app, p. ej. UUID en minúsculas sin guiones o con guiones según estándar del proyecto).

- **Unicidad:**  
  Una entrada por (tenant, usuario). No incluir `database_type` ni `filter_by_subscription` en la clave si en la primera versión el resolver solo se usa con un valor por entorno; si más adelante se permiten varias combinaciones, se puede extender a algo como `permissions:{cliente_id}:{usuario_id}:{database_type}:{filter_by_subscription}`.

- **Namespace:**  
  Prefijo fijo `permissions:` para poder invalidar por patrón (ej. `permissions:{cliente_id}:*` en Redis SCAN o DELETE por patrón si la infra lo soporta).

- **Super admin:**  
  No cachear el resultado cuando `is_super_admin=True` (o cachear un objeto con `is_super_admin=True` y `codes=[]` con TTL muy bajo si se desea). Recomendación: no cachear; calcular en memoria y devolver sin leer/escribir cache.

---

## 5. Estrategia de invalidación

### 5.1 Eventos que deben invalidar

| Evento | Alcance | Método sugerido |
|--------|---------|------------------|
| Cambio en **rol_permiso** para un rol (asignar/quitar permisos a un rol) | Todos los usuarios que tienen ese rol en ese cliente | Por rol: no hay “invalidar por rol” en la API; se puede implementar como `invalidate_for_tenant(cliente_id)` o invalidez por lista de (usuario_id, cliente_id) si se conoce. Alternativa: invalidar solo los usuarios que tienen ese rol (requiere consultar usuario_rol). |
| Cambio en **usuario_rol** (asignar/quitar rol a usuario) | Ese usuario en ese cliente | `invalidate_for_user(usuario_id, cliente_id)` |
| Cambio en **cliente_modulo** (activar/desactivar módulo) solo si `filter_by_subscription=True` | Todos los usuarios del tenant | `invalidate_for_tenant(cliente_id)` |

### 5.2 Puntos de integración (quién llama a invalidación)

- **permisos_negocio_service** (o equivalente): tras `set_permisos_negocio_rol` (DELETE + INSERT en rol_permiso), llamar a invalidación por tenant o por lista de usuarios con ese rol. La API pública del resolver expone `invalidate_for_user` e `invalidate_for_tenant`; el servicio puede usar `invalidate_for_tenant(cliente_id)` como opción simple.
- **user_service** (o donde se asignen/desasignen roles a usuarios): tras crear/actualizar/desactivar filas en `usuario_rol`, llamar `invalidate_for_user(usuario_id, cliente_id)`.
- **Cliente_modulo:** si se activa filtro por suscripción, en el endpoint o servicio que actualice `cliente_modulo`, llamar `invalidate_for_tenant(cliente_id)`.

No se implementa código aquí; solo se define que la invalidación se invoca desde esos puntos y que el resolver expone los dos métodos anteriores.

### 5.3 Patrón de clave para invalidar por tenant

- Claves a borrar: `permissions:{cliente_id}:*`.  
- En Redis: usar SCAN + DELETE por patrón o el mecanismo que ofrezca la capa de cache (ej. `delete_pattern("permissions:{cliente_id}:*")`).  
- La API del resolver puede encapsular esto en `invalidate_for_tenant(cliente_id)`.

---

## 6. Manejo de super_admin

- **Entrada:** el resolver recibe `is_super_admin: bool`. Quién llama (p. ej. `build_user_with_roles`) ya tiene esta información (p. ej. por roles con codigo_rol SUPER_ADMIN y nivel 5).

- **Comportamiento cuando `is_super_admin=True`:**
  - No ejecutar queries a `usuario_rol`, `rol_permiso` ni `permiso`.
  - Devolver un `EffectivePermissions` con:
    - `codes = []` (o lista con un marcador si se prefiriera; el contrato con `has_permission` es que super_admin tiene todos los permisos sin mirar la lista).
    - `is_super_admin = True`.
    - `cliente_id` y `usuario_id` los recibidos.
  - No leer ni escribir cache (recomendado).

- **Consumidor (`has_permission`):**  
  Ya hace “si super_admin → return True”. Por tanto no es obligatorio que `user.permisos` contenga todos los códigos para super_admin; basta con que el usuario tenga `is_super_admin=True` y el resolver no rompa el contrato devolviendo un objeto con `.codes` y `.is_super_admin` coherentes.

- **Plug-and-play:**  
  `build_user_with_roles` asigna `permisos=result.codes`; para super_admin será `[]`, y en `has_permission` la comprobación de super_admin va antes de `permission in user.permisos`, así que no hay cambio de comportamiento.

---

## 7. Manejo multi-tenant

- **Cliente_id siempre presente:** toda llamada al resolver incluye `cliente_id`. No hay resolución “global” sin tenant.

- **Cache:** las claves incluyen `cliente_id`; no hay riesgo de mezclar permisos entre tenants.

- **Conexiones y database_type:**
  - El resolver recibe `database_type` y opcionalmente puede recibir el contexto de tenant ya resuelto (para no repetir lógica). Internamente usará la misma estrategia que `permisos_usuario_service`: single = una BD (DEFAULT); multi = tenant (DEFAULT) + central (ADMIN) para catálogo `permiso`.
  - No abrir conexiones en nombre del resolver; reutilizar el contexto de tenant ya establecido en el request (middleware/routing). El resolver llama a servicios que ya usan `execute_query(..., connection_type=..., client_id=...)`.

- **Aislamiento:** el resolver no expone datos de otros tenants; la lista de códigos es solo para el par (usuario_id, cliente_id) dado.

---

## 8. Cómo evitar N+1 queries

- **Un request, un usuario:** en el flujo actual, `get_current_active_user` → `build_user_with_roles` se ejecuta una vez por request y para un solo usuario. El resolver se llama una sola vez por request con un par (usuario_id, cliente_id). No hay N+1 en ese flujo si el resolver hace una (o dos en BD dedicada) consultas por llamada.

- **Dentro del resolver (una llamada a get_effective_permissions):**
  - **Single BD:** una única query: `usuario_rol` ⋈ `rol_permiso` ⋈ `permiso` filtrada por `usuario_id` y `cliente_id` (y condiciones de activo/expiracion). Misma estrategia que `_permisos_single`.
  - **Multi BD:** dos queries: (1) en BD tenant: usuario_rol ⋈ rol_permiso → permiso_ids; (2) en BD central: SELECT codigo FROM permiso WHERE permiso_id IN (...). Misma estrategia que `_permisos_dedicated`.
  - No hacer una query por permiso ni por rol; todo en una o dos consultas agregadas.

- **Batch opcional:** si se implementa `get_effective_permissions_batch`, para múltiples usuarios del mismo cliente se puede hacer una sola query que devuelva (usuario_id, codigo) y agrupar en memoria por usuario_id, evitando N llamadas a get_effective_permissions. La API interna del resolver no expone SQL; solo se garantiza que el número de round-trips a BD no sea proporcional al número de usuarios en el batch.

- **Cache:** en hits de cache no se ejecuta ninguna query; un solo get por clave `permissions:{cliente_id}:{usuario_id}`.

---

## 9. Resumen de integración con `build_user_with_roles()`

Pseudocódigo del cambio mínimo en `build_user_with_roles()`:

```
# Después de tener: usuario_id, cliente_id, database_type, is_superadmin

if USE_PERMISSION_RESOLVER:
    resolver = PermissionResolverService()
    effective = await resolver.get_effective_permissions(
        usuario_id=usuario_id,
        cliente_id=cliente_id,
        database_type=database_type,
        is_super_admin=is_superadmin,
        filter_by_subscription=PERMISSION_RESOLVER_FILTER_BY_SUBSCRIPTION,
    )
    permisos_codigos = effective.codes   # List[str]
else:
    permisos_codigos = await obtener_codigos_permiso_usuario(
        usuario_id=usuario_id,
        cliente_id=cliente_id,
        database_type=database_type,
    )

UsuarioReadWithRoles(..., permisos=permisos_codigos)
```

- No se cambia la firma de `build_user_with_roles` ni el schema `UsuarioReadWithRoles`.
- No se cambia `has_permission` ni `require_permission`.
- El resolver es plug-and-play mientras devuelva un objeto con `.codes` (o lista equivalente) y se respete super_admin sin queries ni cache.

---

## 10. Checklist de diseño

- Métodos públicos: `get_effective_permissions`, `invalidate_for_user`, `invalidate_for_tenant`, y opcionalmente `get_effective_permissions_batch`.
- Inputs/salidas: definidos por firma y por tipo `EffectivePermissions`.
- Estructura de `EffectivePermissions`: `codes`, `is_super_admin`, `cliente_id`, `usuario_id`, y opcionales `active_module_codes`, `source`; serializable a JSON.
- Cache keys: `permissions:{cliente_id}:{usuario_id}`; sin cache para super_admin.
- Invalidación: por usuario y por tenant; puntos de llamada en servicios que escriben rol_permiso, usuario_rol y (opcional) cliente_modulo.
- Super_admin: atajo sin queries y sin cache; `EffectivePermissions.is_super_admin=True` y `codes=[]`.
- Multi-tenant: cliente_id en todas las llamadas y en la clave de cache; uso de database_type y conexiones existentes.
- N+1: una o dos queries por llamada a `get_effective_permissions`; batch opcional para múltiples usuarios.

Este documento define únicamente la API interna y el contrato; la implementación queda para una siguiente fase.
