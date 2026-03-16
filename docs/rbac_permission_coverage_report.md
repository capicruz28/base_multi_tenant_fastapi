# Reporte de Cobertura RBAC — Endpoints sin `require_permission`

**Fecha:** 2026-02-18  
**Alcance:** Endpoints que usan `Depends(get_current_active_user)` y **no** tienen `require_permission(...)` (ni en parámetros del handler ni en `dependencies=[Depends(require_permission(...))]`).  
**Objetivo:** Auditoría y propuesta de alineación RBAC; no se modifica código.

---

## Resumen ejecutivo

| Categoría | Cantidad |
|-----------|----------|
| **Auth** | 3 |
| **Tenant (clientes)** | 11 |
| **Tenant (conexiones)** | 6 |
| **WMS** | 2 |
| **MFG** | 26 |
| **Users** | 2 |
| **Superadmin (usuarios)** | 5 |
| **Total** | **55** |

La mayoría de endpoints sin `require_permission` están protegidos por **LBAC** (Super Admin) o por **solo autenticado**; un conjunto relevante en **MFG** y **WMS** queda únicamente con “autenticado”, sin permiso RBAC explícito.

---

## 1. Módulo Auth

| Método | Path (prefijo `/auth`) | Handler | Protección actual | Riesgo | Permiso RBAC sugerido |
|--------|------------------------|--------|-------------------|--------|----------------------|
| GET | `/me/` | `get_me` | CORE (has_permission en handler: `core.app.acceder`) | BAJO | `core.app.acceder` (ya validado en código; opcional exponer como Depends) |
| GET | `/permissions/me` | `get_permissions_me` | Solo autenticado | MEDIO | `auth.permission.leer` o `core.app.acceder` |
| GET | `/menu` | `get_menu` | Solo autenticado | MEDIO | `auth.menu.leer` o `modulos.menu.leer` |

**Nota:** Los endpoints de sesiones (`/sessions/`, `/logout_all/`, `/sessions/admin/`, etc.) usan `get_current_user` o `require_admin`; no entran en este listado por no usar `get_current_active_user` sin `require_permission`.

**Archivo:** `app/modules/auth/presentation/endpoints.py`

---

## 2. Módulo Tenant (Clientes)

**Archivo:** `app/modules/tenant/presentation/endpoints_clientes.py`  
**Prefijo API:** `/clientes`

| Método | Path | Handler | Protección actual | Riesgo | Permiso RBAC sugerido |
|--------|------|--------|-------------------|--------|------------------------|
| POST | `/` | `crear_cliente` | LBAC (Super Admin) | ALTO | `tenant.cliente.crear` |
| GET | `/` | `listar_clientes` | LBAC (Super Admin) | ALTO | `tenant.cliente.leer` |
| GET | `/{cliente_id}/` | `obtener_cliente` | LBAC (Super Admin) | ALTO | `tenant.cliente.leer` |
| PUT | `/{cliente_id}/` | `actualizar_cliente` | LBAC (Super Admin) | ALTO | `tenant.cliente.actualizar` |
| DELETE | `/{cliente_id}/` | `eliminar_cliente` | LBAC (Super Admin) | ALTO | `tenant.cliente.eliminar` |
| PUT | `/{cliente_id}/suspender/` | `suspender_cliente` | LBAC (Super Admin) | ALTO | `tenant.cliente.actualizar` |
| PUT | `/{cliente_id}/activar/` | `activar_cliente` | LBAC (Super Admin) | ALTO | `tenant.cliente.actualizar` |
| GET | `/{cliente_id}/estadisticas/` | `obtener_estadisticas_cliente` | LBAC (Super Admin) | ALTO | `tenant.cliente.leer` |
| GET | `/debug/user-info` | `debug_user_info` | Solo autenticado | BAJO | Eliminar en prod o `auth.debug.leer` |
| GET | `/debug/access-levels` | `debug_access_levels` | Solo autenticado | BAJO | Eliminar en prod o `auth.debug.leer` |
| GET | `/tenant/branding` | `obtener_branding_tenant` | Solo autenticado | BAJO | `tenant.branding.leer` |

---

## 3. Módulo Tenant (Conexiones)

**Archivo:** `app/modules/tenant/presentation/endpoints_conexiones.py`  
**Prefijo API:** `/conexiones`

| Método | Path | Handler | Protección actual | Riesgo | Permiso RBAC sugerido |
|--------|------|--------|-------------------|--------|------------------------|
| GET | `/clientes/{cliente_id}/` | `listar_conexiones_cliente` | LBAC (Super Admin) | ALTO | `tenant.conexion.leer` |
| GET | `/clientes/{cliente_id}/principal/` | `obtener_conexion_principal` | LBAC (Super Admin) | ALTO | `tenant.conexion.leer` |
| POST | `/clientes/{cliente_id}/` | `crear_conexion` | LBAC (Super Admin) | ALTO | `tenant.conexion.crear` |
| PUT | `/{conexion_id}/` | `actualizar_conexion` | LBAC (Super Admin) | ALTO | `tenant.conexion.actualizar` |
| DELETE | `/{conexion_id}/` | `desactivar_conexion` | LBAC (Super Admin) | ALTO | `tenant.conexion.eliminar` |
| POST | `/test` | `test_conexion` | LBAC (Super Admin) | MEDIO | `tenant.conexion.leer` |

---

## 4. Módulo WMS

### 4.1 Zonas de almacén

**Archivo:** `app/modules/wms/presentation/endpoints_zonas.py`  
**Prefijo API:** `/wms/zonas`

| Método | Path | Handler | Protección actual | Riesgo | Permiso RBAC sugerido |
|--------|------|--------|-------------------|--------|------------------------|
| POST | `` | `post_zona_almacen` | Solo autenticado | ALTO | `wms.zona.crear` |

### 4.2 Ubicaciones

**Archivo:** `app/modules/wms/presentation/endpoints_ubicaciones.py`  
**Prefijo API:** `/wms/ubicaciones`

| Método | Path | Handler | Protección actual | Riesgo | Permiso RBAC sugerido |
|--------|------|--------|-------------------|--------|------------------------|
| POST | `` | `post_ubicacion` | Solo autenticado | ALTO | `wms.ubicacion.crear` |

---

## 5. Módulo MFG (Manufactura)

Todos los siguientes usan **solo** `get_current_active_user`; no tienen `require_permission`.  
Prefijo API: `/mfg`.

### 5.1 Orden producción – operaciones

**Archivo:** `app/modules/mfg/presentation/endpoints_orden_produccion_operaciones.py`  
**Sub-prefijo:** `/orden-produccion-operaciones`

| Método | Path | Handler | Protección actual | Riesgo | Permiso RBAC sugerido |
|--------|------|--------|-------------------|--------|------------------------|
| GET | `` | `get_orden_produccion_operaciones` | Solo autenticado | MEDIO | `mfg.orden_produccion_operacion.leer` |
| GET | `/{op_operacion_id}` | `get_orden_produccion_operacion` | Solo autenticado | MEDIO | `mfg.orden_produccion_operacion.leer` |
| POST | `` | `post_orden_produccion_operacion` | Solo autenticado | ALTO | `mfg.orden_produccion_operacion.crear` |
| PUT | `/{op_operacion_id}` | `put_orden_produccion_operacion` | Solo autenticado | ALTO | `mfg.orden_produccion_operacion.actualizar` |

### 5.2 Consumo materiales

**Archivo:** `app/modules/mfg/presentation/endpoints_consumo_materiales.py`  
**Sub-prefijo:** `/consumo-materiales`

| Método | Path | Handler | Protección actual | Riesgo | Permiso RBAC sugerido |
|--------|------|--------|-------------------|--------|------------------------|
| GET | (por id) | `get_consumo_materiales_by_id_endpoint` | Solo autenticado | MEDIO | `mfg.consumo_material.leer` |
| POST | `` | `post_consumo_materiales` | Solo autenticado | ALTO | `mfg.consumo_material.crear` |
| PUT | (por id) | `put_consumo_materiales` | Solo autenticado | ALTO | `mfg.consumo_material.actualizar` |

### 5.3 Ruta fabricación detalle

**Archivo:** `app/modules/mfg/presentation/endpoints_ruta_fabricacion_detalle.py`  
**Sub-prefijo:** `/ruta-fabricacion-detalle`

| Método | Path | Handler | Protección actual | Riesgo | Permiso RBAC sugerido |
|--------|------|--------|-------------------|--------|------------------------|
| GET | `/{ruta_detalle_id}` | `get_ruta_fabricacion_detalle` | Solo autenticado | MEDIO | `mfg.ruta_fabricacion_detalle.leer` |
| POST | `` | `post_ruta_fabricacion_detalle` | Solo autenticado | ALTO | `mfg.ruta_fabricacion_detalle.crear` |
| PUT | `/{ruta_detalle_id}` | `put_ruta_fabricacion_detalle` | Solo autenticado | ALTO | `mfg.ruta_fabricacion_detalle.actualizar` |

### 5.4 Rutas fabricación

**Archivo:** `app/modules/mfg/presentation/endpoints_rutas_fabricacion.py`  
**Sub-prefijo:** `/rutas-fabricacion`

| Método | Path | Handler | Protección actual | Riesgo | Permiso RBAC sugerido |
|--------|------|--------|-------------------|--------|------------------------|
| GET | `/{ruta_id}` | `get_ruta_fabricacion` | Solo autenticado | MEDIO | `mfg.ruta_fabricacion.leer` |
| POST | `` | `post_ruta_fabricacion` | Solo autenticado | ALTO | `mfg.ruta_fabricacion.crear` |
| PUT | `/{ruta_id}` | `put_ruta_fabricacion` | Solo autenticado | ALTO | `mfg.ruta_fabricacion.actualizar` |

### 5.5 Lista materiales detalle

**Archivo:** `app/modules/mfg/presentation/endpoints_lista_materiales_detalle.py`  
**Sub-prefijo:** `/lista-materiales-detalle`

| Método | Path | Handler | Protección actual | Riesgo | Permiso RBAC sugerido |
|--------|------|--------|-------------------|--------|------------------------|
| GET | `/{bom_detalle_id}` | `get_lista_materiales_detalle` | Solo autenticado | MEDIO | `mfg.lista_materiales_detalle.leer` |
| POST | `` | `post_lista_materiales_detalle` | Solo autenticado | ALTO | `mfg.lista_materiales_detalle.crear` |
| PUT | `/{bom_detalle_id}` | `put_lista_materiales_detalle` | Solo autenticado | ALTO | `mfg.lista_materiales_detalle.actualizar` |

### 5.6 Listas materiales (BOM)

**Archivo:** `app/modules/mfg/presentation/endpoints_listas_materiales.py`  
**Sub-prefijo:** `/listas-materiales`

| Método | Path | Handler | Protección actual | Riesgo | Permiso RBAC sugerido |
|--------|------|--------|-------------------|--------|------------------------|
| GET | `/{bom_id}` | `get_lista_materiales` | Solo autenticado | MEDIO | `mfg.lista_materiales.leer` |
| POST | `` | `post_lista_materiales` | Solo autenticado | ALTO | `mfg.lista_materiales.crear` |
| PUT | `/{bom_id}` | `put_lista_materiales` | Solo autenticado | ALTO | `mfg.lista_materiales.actualizar` |

### 5.7 Operaciones

**Archivo:** `app/modules/mfg/presentation/endpoints_operaciones.py`  
**Sub-prefijo:** `/operaciones`

| Método | Path | Handler | Protección actual | Riesgo | Permiso RBAC sugerido |
|--------|------|--------|-------------------|--------|------------------------|
| GET | `/{operacion_id}` | `get_operacion` | Solo autenticado | MEDIO | `mfg.operacion.leer` |
| POST | `` | `post_operacion` | Solo autenticado | ALTO | `mfg.operacion.crear` |
| PUT | `/{operacion_id}` | `put_operacion` | Solo autenticado | ALTO | `mfg.operacion.actualizar` |

### 5.8 Centros de trabajo

**Archivo:** `app/modules/mfg/presentation/endpoints_centros_trabajo.py`  
**Sub-prefijo:** `/centros-trabajo`

| Método | Path | Handler | Protección actual | Riesgo | Permiso RBAC sugerido |
|--------|------|--------|-------------------|--------|------------------------|
| GET | `` | `get_centros_trabajo` | Solo autenticado | MEDIO | `mfg.centro_trabajo.leer` |
| GET | `/{centro_trabajo_id}` | `get_centro_trabajo` | Solo autenticado | MEDIO | `mfg.centro_trabajo.leer` |
| POST | `` | `post_centro_trabajo` | Solo autenticado | ALTO | `mfg.centro_trabajo.crear` |
| PUT | `/{centro_trabajo_id}` | `put_centro_trabajo` | Solo autenticado | ALTO | `mfg.centro_trabajo.actualizar` |

---

## 6. Módulo Users

**Archivo:** `app/modules/users/presentation/endpoints.py`  
**Prefijo API:** `/usuarios`

| Método | Path | Handler | Protección actual | Riesgo | Permiso RBAC sugerido |
|--------|------|--------|-------------------|--------|------------------------|
| GET | `/{usuario_id}/` | `read_usuario` | Solo autenticado + has_permission en handler (self/otros) | MEDIO | `admin.usuario.leer` |
| GET | `/{usuario_id}/roles/` | `read_usuario_roles` | Solo autenticado + has_permission en handler (self/otros) | MEDIO | `admin.rol.leer` |

**Nota:** Hoy se valida con `has_permission(current_user, "admin.usuario.leer")` / `admin.rol.leer` dentro del handler; se sugiere unificar con `require_permission` en la ruta para consistencia RBAC.

---

## 7. Módulo Superadmin (Usuarios)

**Archivo:** `app/modules/superadmin/presentation/endpoints_usuarios.py`  
**Prefijo API:** `/superadmin/usuarios`

Todos protegidos por `@require_super_admin()` (LBAC); ninguno usa `require_permission`.

| Método | Path (relativo al prefijo) | Handler | Protección actual | Riesgo | Permiso RBAC sugerido |
|--------|----------------------------|--------|-------------------|--------|------------------------|
| GET | (listado global) | `list_usuarios_global` | LBAC (Super Admin) | ALTO | `superadmin.usuario.leer` |
| GET | (detalle) | `read_usuario_superadmin` | LBAC (Super Admin) | ALTO | `superadmin.usuario.leer` |
| GET | (actividad) | `read_usuario_actividad` | LBAC (Super Admin) | ALTO | `superadmin.usuario.leer` |
| GET | (sesiones) | `read_usuario_sesiones` | LBAC (Super Admin) | ALTO | `superadmin.usuario.leer` |
| GET | (por cliente) | `list_usuarios_por_cliente` | LBAC (Super Admin) | ALTO | `superadmin.usuario.leer` |

---

## 8. Criterios de riesgo

- **ALTO:** Mutaciones (crear/actualizar/eliminar) o lectura de datos sensibles/globales sin permiso RBAC explícito; o endpoints Super Admin sin permiso documentado.
- **MEDIO:** Lectura acotada al tenant o self-service con validación manual en handler; o debug con datos limitados.
- **BAJO:** Metadata del usuario actual, menú, permisos efectivos o branding del tenant; o endpoints de debug que conviene desactivar en producción.

---

## 9. Recomendaciones de alineación

1. **MFG y WMS:** Añadir `Depends(require_permission("modulo.recurso.accion"))` en cada handler según la tabla (crear/leer/actualizar/eliminar), siguiendo el patrón ya usado en `endpoints_ordenes_produccion.py` y en otros endpoints WMS (zonas GET/PUT, ubicaciones GET/PUT).
2. **Auth:** Valorar usar `require_permission("core.app.acceder")` en `/me/` y permisos explícitos para `/permissions/me` y `/menu` para homogeneizar con el resto de la API.
3. **Tenant y Superadmin:** Mantener LBAC para contexto Super Admin y, en paralelo, registrar en catálogo RBAC los permisos sugeridos (ej. `tenant.cliente.crear`, `superadmin.usuario.leer`) y, si se desea migrar luego, añadir `require_permission` además del decorador LBAC.
4. **Users:** Sustituir la comprobación manual con `has_permission` en `read_usuario` y `read_usuario_roles` por `dependencies=[Depends(require_permission("admin.usuario.leer"))]` y `require_permission("admin.rol.leer")` respectivamente, manteniendo la lógica de “ver propio vs otros” en servicio si aplica.
5. **Debug:** Los endpoints `/clientes/debug/user-info` y `/clientes/debug/access-levels` deberían deshabilitarse en producción o protegerlos con un permiso explícito (ej. `auth.debug.leer`) asignado solo a roles de soporte.

---

*Documento generado por auditoría estática; no se ha modificado código. Patrón de permiso: `<modulo>.<recurso>.<accion>` (leer, crear, actualizar, eliminar).*
