## Diagnóstico runtime RBAC — `core.app.acceder`

### 1. Flujo completo de autorización (de token a `has_permission`)

1. **`get_current_user_data` (`app/api/deps.py`)**
   - Decodifica el JWT (`sub`, `jti`, `access_level`, `is_super_admin`, `user_type`, etc.).
   - Verifica revocación en Redis (blacklist por `jti`).
2. **Resolución de tenant (`TenantMiddleware`)**
   - `TenantMiddleware.dispatch` (`app/core/tenant/middleware.py`) resuelve:
     - `client_id` a partir del subdominio (`cliente.cliente_id` o `SUPERADMIN_CLIENTE_ID`).
     - Crea un `TenantContext` con `client_id`, `database_type` (`single`/`multi`), `nombre_bd`, etc.
   - Contexto se expone vía `set_tenant_context(tenant_ctx)` y `get_current_client_id()`.
3. **`get_current_active_user` (`app/api/deps.py`)**
   - Obtiene `request_cliente_id`:
     - Primero con `get_current_client_id()` (desde `TenantContext`).
     - Fallback a `request.state.cliente_id` si no hay contexto.
   - Llama a `get_user_auth_context(username, request_cliente_id)` para contexto mínimo (sin permisos aún).
   - Valida:
     - Usuario activo (`context.es_activo`).
     - Acceso al tenant (`validate_tenant_access(context, request_cliente_id)`).
   - Llama a `build_user_with_roles(username, request_cliente_id)` para construir `UsuarioReadWithRoles` completo.
   - Sincroniza `access_level`, `is_super_admin` y `user_type` con los valores del token si existen.
4. **`build_user_with_roles` (`app/core/auth/user_builder.py`)**
   - Determina `database_type` desde `TenantContext` (`try_get_tenant_context()`).
   - Carga usuario base desde `UsuarioTable`:
     - **Single DB**: filtra por `nombre_usuario`, `es_eliminado=0` y `cliente_id=request_cliente_id` con fallback sin filtro de cliente para casos como superadmin.
     - **Multi DB**: filtra solo por `nombre_usuario` (todos los usuarios pertenecen al tenant actual).
   - Ajusta `cliente_id` del usuario:
     - En BD dedicada, si `cliente_id` del usuario es `NULL` / UUID nulo, lo sustituye por `request_cliente_id` o por el cliente del contexto.
   - Carga roles (`UsuarioRolTable ⋈ RolTable`), respetando:
     - En single DB: filtros por `cliente_id` (tenant actual o roles globales con `cliente_id IS NULL`).
     - En multi DB: sin filtro de cliente (todos los roles son del mismo tenant).
   - Calcula `access_level` máximo de los roles y si es `SUPER_ADMIN` (`nivel_acceso=5`).
   - Determina `user_type` (`super_admin` / `tenant_admin` / `user`).
   - **Carga permisos RBAC de negocio**:
     - Bajo flag `USE_PERMISSION_RESOLVER`:
       - Intenta usar `permission_resolver.get_effective_permissions(...)` → `effective.codes`.
       - Si falla, hace **fallback** a `permisos_usuario_service.obtener_codigos_permiso_usuario(...)`.
     - Sin flag / flag desactivado:
       - Llama directamente a `obtener_codigos_permiso_usuario(usuario_id, cliente_id, database_type)`.
     - Resultado (`List[str]`) se asigna a `usuario_pydantic.permisos`.
5. **`has_permission` y `require_permission` (`app/core/authorization/rbac.py`)**
   - `require_permission("core.app.acceder")` inyecta `current_user = get_current_active_user(...)` y luego:

     ```python
     if not has_permission(current_user, permission):
         # 403 PERMISSION_DENIED
     ```

   - `has_permission(user, permission)`:
     - Si `get_user_type(user) == "super_admin"` → **True** (bypass completo).
     - Obtiene `permisos_usuario = user.permisos`:
       - Lista de `str`, o bien lista de objetos con `.nombre`, que se normaliza a lista de `str`.
     - Hace comparación **exacta**:

       ```python
       if permission in permisos_usuario:
           return True
       ```

     - Si no está, devuelve `False`.

   - No hay normalización (`lower()`, `strip()`) en `has_permission`; se asume que los códigos vienen ya correctos (como en BD).

### 2. Carga de permisos del usuario: SQL y joins

La carga de permisos efectivos se hace en `permisos_usuario_service.obtener_codigos_permiso_usuario`  
(`app/modules/rbac/application/services/permisos_usuario_service.py`), llamada desde `build_user_with_roles`.

#### 2.1. Single DB (`_permisos_single`)

Para BD compartida, la query es:

```sql
SELECT DISTINCT p.codigo
FROM usuario_rol ur
INNER JOIN rol_permiso rp 
    ON rp.rol_id = ur.rol_id 
   AND rp.cliente_id = ur.cliente_id
INNER JOIN permiso p 
    ON p.permiso_id = rp.permiso_id 
   AND p.es_activo = 1
WHERE ur.usuario_id = :usuario_id
  AND ur.cliente_id = :cliente_id
  AND ur.es_activo = 1
  AND (ur.fecha_expiracion IS NULL OR ur.fecha_expiracion > GETDATE())
  -- Filtro opcional por módulos activos del tenant:
  AND (
      p.modulo_id IS NULL
      OR EXISTS (
          SELECT 1 FROM cliente_modulo cm
          WHERE cm.modulo_id = p.modulo_id
            AND cm.cliente_id = :cliente_id
            AND cm.esta_activo = 1
            AND (cm.fecha_vencimiento IS NULL OR cm.fecha_vencimiento > CAST(GETDATE() AS DATE))
      )
  )
```

- **Joins clave:**
  - `usuario_rol` → `rol` (implícito por `rol_id` en `usuario_rol` y `rol_permiso`).
  - `rol_permiso` enlaza `rol_id` y `cliente_id` al permiso.
  - `permiso` se une por `permiso_id` y `es_activo = 1`.
- **Filtros:**
  - `ur.usuario_id = :usuario_id` → usuario actual.
  - `ur.cliente_id = :cliente_id` → tenant actual.
  - `ur.es_activo = 1` y `fecha_expiracion` vigente.
  - `_CLIENTE_MODULO_FILTER` filtra por módulos contratados (tabla `cliente_modulo`).
- **Contexto tenant:** `:cliente_id` es el `request_cliente_id` que viene desde `TenantContext`/`request.state.cliente_id`.

#### 2.2. Multi DB (`_permisos_dedicated`)

Para BD dedicada (multi-DB):

1. En BD del tenant:

```sql
SELECT DISTINCT rp.permiso_id
FROM usuario_rol ur
INNER JOIN rol_permiso rp 
    ON rp.rol_id = ur.rol_id 
   AND rp.cliente_id = ur.cliente_id
WHERE ur.usuario_id = :usuario_id
  AND ur.cliente_id = :cliente_id
  AND ur.es_activo = 1
  AND (ur.fecha_expiracion IS NULL OR ur.fecha_expiracion > GETDATE())
```

2. En BD central (ADMIN), para obtener los códigos:

```sql
SELECT codigo 
FROM permiso p
WHERE p.es_activo = 1 
  AND p.permiso_id IN (:p0, :p1, ...)
  AND (
      p.modulo_id IS NULL
      OR EXISTS (
          SELECT 1 FROM cliente_modulo cm
          WHERE cm.modulo_id = p.modulo_id
            AND cm.cliente_id = :cliente_id
            AND cm.esta_activo = 1
            AND (cm.fecha_vencimiento IS NULL OR cm.fecha_vencimiento > CAST(GETDATE() AS DATE))
      )
  )
```

- **Contexto tenant:** `:cliente_id` es el mismo `cliente_id` con el que se resolvió el tenant.
- **Observación importante:** En ambos modos (`single` y `multi`), el filtro por `cliente_modulo` se aplica igual.

### 3. Verificación del contexto tenant (`cliente_id`)

Revisión de flujo de `cliente_id`:

- `TenantMiddleware`:
  - Resuelve `client_id` desde:
    - Subdominio (`cliente.cliente_id`).
    - O `SUPERADMIN_CLIENTE_ID` para el subdominio superadmin.
  - Crea `TenantContext(client_id=client_id, ...)` y lo establece con `set_tenant_context`.
- `get_current_active_user`:

```python
from app.core.tenant.context import get_current_client_id
try:
    request_cliente_id = get_current_client_id()
except RuntimeError:
    request_cliente_id = getattr(request.state, 'cliente_id', None)
```

- `build_user_with_roles(username, request_cliente_id)`:
  - Usa `request_cliente_id` tanto para:
    - Filtrar el usuario en `UsuarioTable` (single DB).
    - Ajustar `cliente_id` del usuario (multi DB).
  - Pasa ese `cliente_id` a `obtener_codigos_permiso_usuario(usuario_id, cliente_id, database_type)`.

**Conclusión:** el `cliente_id` usado para cargar permisos **sí viene del contexto de tenant** (`TenantContext`/`request.state.cliente_id`); no depende solo del `cliente_id` almacenado en el usuario.

### 4. Comparación `core.app.acceder` vs permisos cargados

- El permiso **CORE** se crea en BD central por `SEED_PERMISOS_CORE.sql`:

```sql
MERGE INTO permiso AS t
USING (
    SELECT
        'core.app.acceder' AS codigo,
        N'Acceder a la aplicación' AS nombre,
        N'Permite iniciar sesión y acceder al sistema ERP' AS descripcion,
        CAST('E1000001-0000-4000-8000-000000000001' AS UNIQUEIDENTIFIER) AS modulo_id,
        'app' AS recurso,
        'acceder' AS accion
) AS s
ON t.codigo = s.codigo
...
```

- La asignación rol → permiso se hace en `SEED_ASIGNAR_CORE_APP_A_ROLES.sql`:
  - Parte 1: para roles con `cliente_id` no nulo.
  - Parte 2: para roles de sistema (`rol.cliente_id IS NULL`) cruzados con todos los clientes.
  - Resultado: **todos los roles activos** deberían tener `rol_permiso` hacia `core.app.acceder` para cada `cliente_id`.
- `build_user_with_roles` pobla `user.permisos` con la lista de `p.codigo` devuelta por `obtener_codigos_permiso_usuario`.
- `has_permission(current_user, "core.app.acceder")` compara literalmente contra esa lista:

```python
permisos_usuario = user.permisos  # List[str]
if permission in permisos_usuario:
    return True
```

**Punto crítico:** aunque `core.app.acceder` exista en `permiso` y `rol_permiso`, puede **no aparecer** en `user.permisos` si la query de permisos lo filtra.

### 5. Punto exacto donde se pierden los permisos

El punto donde se “pierde” `core.app.acceder` es el **filtro por módulos activos del tenant** en `permisos_usuario_service`:

- `_CLIENTE_MODULO_FILTER` se añade siempre que `filter_by_active_modules=True` (valor por defecto):

```sql
AND (
    p.modulo_id IS NULL
    OR EXISTS (
        SELECT 1 FROM cliente_modulo cm
        WHERE cm.modulo_id = p.modulo_id
          AND cm.cliente_id = :cliente_id
          AND cm.esta_activo = 1
          AND (cm.fecha_vencimiento IS NULL OR cm.fecha_vencimiento > CAST(GETDATE() AS DATE))
    )
)
```

- El permiso `core.app.acceder` tiene `modulo_id = <ORG>` (no es NULL).
- Por tanto, para que `core.app.acceder` aparezca en la lista de permisos efectivos del usuario, **deben cumplirse todas**:
  1. El usuario tiene al menos un rol activo (`usuario_rol`) para ese `cliente_id`.
  2. Ese rol tiene asignado `rol_permiso` hacia `core.app.acceder` para ese `cliente_id` (lo hace el seed).
  3. En `cliente_modulo` existe una fila con:
     - `cliente_id = :cliente_id` (el tenant actual),
     - `modulo_id = <ORG>`,
     - `esta_activo = 1`,
     - y `fecha_vencimiento` nula o futura.

Si el tenant **no tiene el módulo ORG marcado como activo en `cliente_modulo`**, el filtro `_CLIENTE_MODULO_FILTER` **excluye** el permiso `core.app.acceder` de la lista final, aunque:

- el permiso exista en `permiso`,
- y la asignación rol_permiso exista para ese cliente.

En consecuencia:

- `build_user_with_roles` construye `user.permisos` **sin** `core.app.acceder`.
- `has_permission(current_user, "core.app.acceder")` devuelve `False`.
- `require_permission("core.app.acceder")` (o el chequeo en `/auth/me/`) responde 403, aunque los datos de catálogo estén correctos.

### 6. Cache y normalización

- **Cache de permisos:**
  - `permisos_usuario_service.obtener_codigos_permiso_usuario` **no** está cacheado (`lru_cache` ni Redis); cada request ejecuta las queries.
  - El `permission_resolver` (si está activado) delega en `obtener_codigos_permiso_usuario` o lógica equivalente; no hay caches globales críticos visibles en este flujo.
  - Por tanto, el problema no parece deberse a **datos antiguos en cache**, sino al filtro aplicado en cada request.

- **Normalización de códigos de permiso:**
  - `SEED_PERMISOS_CORE.sql` crea `codigo = 'core.app.acceder'` en minúsculas sin espacios extra.
  - `has_permission` compara el string recibido (`"core.app.acceder"`) con los strings de `user.permisos` **sin** usar `lower()` ni `strip()`.
  - No se observa transformación de código en `permisos_usuario_service` (se devuelven los `codigo` tal cual se almacenan en `permiso`).
  - No hay evidencia de que el problema venga de diferencias de mayúsculas/minúsculas o espacios.

### 7. Logging recomendado (sin aplicar aún)

Para diagnosticar en entorno real (cuando decidas habilitarlo), se recomienda añadir temporalmente logging en:

- **Después de cargar permisos en `build_user_with_roles`:**

```python
logger.info(
    "[RBAC_DEBUG] Permisos cargados para usuario '%s' en cliente %s (db_type=%s): %s",
    username,
    cliente_id,
    database_type,
    permisos_codigos,
)
```

- **En `has_permission`:**

```python
logger.info(
    "[RBAC_DEBUG] has_permission: usuario=%s, tipo=%s, permiso='%s', permisos=%s",
    getattr(user, "nombre_usuario", "?"),
    get_user_type(user),
    permission,
    getattr(user, "permisos", []),
)
```

Esto permitiría confirmar en logs, para un usuario concreto, **qué permisos efectivos** se están cargando antes de evaluar `core.app.acceder`.

### 8. Causa raíz y fix recomendado (sin aplicar)

**Causa raíz principal:**

- El permiso `core.app.acceder`:
  - Está correctamente definido en `permiso` con código `'core.app.acceder'`.
  - Se asigna a todos los roles activos y clientes vía `rol_permiso` (`SEED_ASIGNAR_CORE_APP_A_ROLES.sql`).
- Sin embargo, la capa de resolución de permisos (`obtener_codigos_permiso_usuario`) filtra **todos los permisos de negocio** por módulos activos (`cliente_modulo`) incluyendo `core.app.acceder`, cuyo `modulo_id` es el del módulo ORG.
- Si el módulo ORG no está activo para el `cliente_id` del request en `cliente_modulo`, `core.app.acceder` nunca llega a `user.permisos`, y `has_permission("core.app.acceder")` devuelve False aunque los datos de catálogo estén bien.

**Fix recomendado (conceptual, sin aplicar todavía):**

1. **Tratar `core.app.acceder` como permiso global no filtrable por módulos:**
   - Opción A (SQL): en `_CLIENTE_MODULO_FILTER`, excluir explícitamente este permiso del filtro:

     ```sql
     AND (
         p.modulo_id IS NULL
         OR p.codigo = 'core.app.acceder'
         OR EXISTS ( ... cliente_modulo ... )
     )
     ```

   - Opción B (semántica): cambiar el seed para que `core.app.acceder` tenga `modulo_id = NULL`, de modo que pase siempre por la rama `p.modulo_id IS NULL` sin depender de `cliente_modulo`.
2. **Verificar que el módulo ORG esté activo en `cliente_modulo`** para los tenants que deban tener acceso al ERP, si se prefiere mantener el filtro actual.
3. **Mantener el contrato actual:**
   - No cambiar la firma de `has_permission` ni `require_permission`.
   - Seguir usando `user.permisos: List[str]` como fuente de verdad, asegurando que `core.app.acceder` llega a esa lista para los usuarios que deben tener acceso.

Con este ajuste, el flujo quedaría:

- Seeds + `rol_permiso` siguen como hoy.
- `obtener_codigos_permiso_usuario` devolvería siempre `core.app.acceder` para los roles que lo tengan asignado, independientemente de la tabla `cliente_modulo` (o asegurando que ORG esté marcada como activa).
- `has_permission(current_user, "core.app.acceder")` reflejaría correctamente la asignación de permisos en BD y `require_permission("core.app.acceder")` dejaría de bloquear a usuarios que sí lo tienen asignado.

