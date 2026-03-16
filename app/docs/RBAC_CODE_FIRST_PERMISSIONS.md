# RBAC Code-First Permissions

Sistema enterprise de auto-registro de permisos RBAC basado en código. La tabla SQL `permiso` se sincroniza al iniciar la aplicación.

## Orden de ejecución al startup

1. **include_router** ya ha registrado todas las rutas al crear la app.
2. **@app.on_event("startup")** se ejecuta después; en ese momento el scanner recorre todas las rutas.
3. **ensure_registry_from_routes(app)** → detecta `Depends(RequirePermission(...))` y `Depends(require_permission(...))`.
4. **PermissionSyncService.sync()** → UPSERT en tabla `permiso`.
5. **MenuPermissionBinder.bind()** → vincula menús tipo "pantalla" con permiso `*.leer` y actualiza `modulo_menu.permiso_codigo_requerido`.
6. **warn_routes_without_permission(app)** → advierte endpoints sin permiso.

Asegurar **RBAC_PERMISSION_SYNC_ENABLED=true** (default) en configuración.

## Columna modulo_menu.permiso_codigo_requerido

Para que los menús devuelvan `required_permission` automáticamente, ejecutar en BD central:

- `app/docs/database/MIGRATION_permiso_codigo_requerido_modulo_menu.sql`

El binder rellena esta columna solo cuando está NULL (no sobrescribe valores manuales).

## Uso

### Declarar permiso con metadata (recomendado)

```python
from fastapi import APIRouter, Depends
from app.core.authorization.rbac import RequirePermission

@router.post(
    "/orden-servicio",
    dependencies=[Depends(RequirePermission({
        "codigo": "log.orden_servicio.crear",
        "nombre": "Crear orden de servicio",
        "descripcion": "Permite crear órdenes de servicio",
        "recurso": "orden_servicio",
        "accion": "crear",
        "modulo_codigo": "LOG",
    }))]
)
async def crear_orden_servicio(...):
    ...
```

### Compatibilidad con código existente

Seguir usando `require_permission("codigo")` sigue siendo válido. Esos permisos se registran en el startup con metadata mínima (`nombre=codigo`, `recurso`/`accion` vacíos) y se sincronizan igual.

## Comportamiento al startup

1. Se recorren todos los endpoints y se recogen permisos de `RequirePermission(metadata)` y de `require_permission(perm)`.
2. **PermissionSyncService.sync()**:
   - Si `codigo` no existe en BD → INSERT.
   - Si existe → UPDATE (nombre, descripcion, recurso, accion, modulo_id, es_activo=1).
   - Si existe en BD pero no en código → es_activo=0.
3. Se muestra **warning** por cada endpoint que no declara permiso (rutas públicas excluidas).

## Configuración

- `RBAC_PERMISSION_SYNC_ENABLED` (env, default `true`): activa/desactiva el sync al startup.

## Logs

- `[RBAC] Permission synced: log.orden_servicio.crear`
- `[RBAC] Permission disabled: old.permission`
- `[RBAC] Endpoint sin @RequirePermission ni require_permission: GET /api/v1/...`

## Tabla permiso (BD central)

Compatible con `SCRIPT_RBAC_TABLAS_CENTRAL.sql`: `permiso_id`, `codigo`, `nombre`, `descripcion`, `modulo_id`, `recurso`, `accion`, `es_activo`, `fecha_creacion`, `fecha_actualizacion`. `modulo_id` se resuelve por `modulo_codigo` desde la tabla `modulo`.
