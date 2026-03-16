# Validación alineación RBAC — Módulo CST (Costeo)

**Fecha:** 2026-02-18  
**Estado:** Completado

---

## 1. Endpoints encontrados

| Archivo | Router prefix | Handler | Método | Path | Recurso |
|---------|----------------|---------|--------|------|---------|
| endpoints_centro_costo_tipo.py | /tipos-centro-costo | get_tipos_centro_costo | GET | "" | centro_costo_tipo |
| endpoints_centro_costo_tipo.py | /tipos-centro-costo | get_tipo_centro_costo | GET | /{cc_tipo_id} | centro_costo_tipo |
| endpoints_centro_costo_tipo.py | /tipos-centro-costo | post_tipo_centro_costo | POST | "" | centro_costo_tipo |
| endpoints_centro_costo_tipo.py | /tipos-centro-costo | put_tipo_centro_costo | PUT | /{cc_tipo_id} | centro_costo_tipo |
| endpoints_producto_costo.py | /producto-costo | get_productos_costo | GET | "" | producto_costo |
| endpoints_producto_costo.py | /producto-costo | get_producto_costo | GET | /{producto_costo_id} | producto_costo |
| endpoints_producto_costo.py | /producto-costo | post_producto_costo | POST | "" | producto_costo |
| endpoints_producto_costo.py | /producto-costo | put_producto_costo | PUT | /{producto_costo_id} | producto_costo |

**Total endpoints CST:** 8

---

## 2. Endpoints decorados

Todos los endpoints listados han sido decorados con Patrón A:

- `MODULE_CODE = "cst"`
- `RESOURCE_CODE` por archivo: `centro_costo_tipo` | `producto_costo`
- Dependencia: `Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.<accion>"))` con `<accion>` según método: leer (GET), crear (POST), actualizar (PUT).

**Endpoints decorados:** 8/8 (100 %)

---

## 3. Permisos generados (detectables por auto-registro)

| Código permiso | Recurso | Acción |
|----------------|---------|--------|
| cst.centro_costo_tipo.leer | centro_costo_tipo | leer |
| cst.centro_costo_tipo.crear | centro_costo_tipo | crear |
| cst.centro_costo_tipo.actualizar | centro_costo_tipo | actualizar |
| cst.producto_costo.leer | producto_costo | leer |
| cst.producto_costo.crear | producto_costo | crear |
| cst.producto_costo.actualizar | producto_costo | actualizar |

**Total permisos únicos CST:** 6

---

## 4. Inconsistencias detectadas

- Ninguna. No hay DELETE en los routers actuales; si se añaden en el futuro, se debe usar la acción `eliminar`.

---

## 5. Confirmación introspección para auto-registro

- Todos los handlers incluyen una dependencia `require_permission(...)` con string estático (f-string con constantes `MODULE_CODE` y `RESOURCE_CODE` evaluadas en tiempo de carga).
- El callable devuelto por `require_permission` tiene el atributo `__permission_codigo__` que el scanner de `permission_startup.ensure_registry_from_routes` puede leer.
- **Conclusión:** Los 6 permisos CST serán detectados en el startup y registrados en el registry; el sync los insertará/actualizará en la tabla `permiso`.
