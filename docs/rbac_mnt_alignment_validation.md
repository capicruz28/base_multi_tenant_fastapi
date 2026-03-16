# Validación alineación RBAC — Módulo MNT (Mantenimiento)

**Fecha:** 2026-02-18  
**Estado:** Completado

---

## 1. Endpoints encontrados

| Archivo | Router prefix | Handler | Método | Path | Recurso |
|---------|----------------|---------|--------|------|---------|
| endpoints_activo.py | /activos | get_activos, get_activo, post_activo, put_activo | GET/POST/PUT | "", /{activo_id} | activo |
| endpoints_orden_trabajo.py | /ordenes-trabajo | get_ordenes_trabajo, get_orden_trabajo, post_orden_trabajo, put_orden_trabajo | GET/POST/PUT | "", /{orden_trabajo_id} | orden_trabajo |
| endpoints_plan_mantenimiento.py | /planes-mantenimiento | get_planes_mantenimiento, get_plan_mantenimiento, post_plan_mantenimiento, put_plan_mantenimiento | GET/POST/PUT | "", /{plan_mantenimiento_id} | plan_mantenimiento |
| endpoints_historial_mantenimiento.py | /historial-mantenimiento | get_historiales_mantenimiento, get_historial_mantenimiento, post_historial_mantenimiento, put_historial_mantenimiento | GET/POST/PUT | "", /{historial_id} | historial_mantenimiento |

**Total endpoints MNT:** 16

---

## 2. Endpoints decorados

Todos los endpoints han sido decorados con Patrón A: `MODULE_CODE = "mnt"`, `RESOURCE_CODE` por archivo (activo, orden_trabajo, plan_mantenimiento, historial_mantenimiento), `Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.<accion>"))`.

**Endpoints decorados:** 16/16 (100 %)

---

## 3. Permisos generados (detectables por auto-registro)

| Código permiso | Recurso | Acción |
|----------------|---------|--------|
| mnt.activo.leer | activo | leer |
| mnt.activo.crear | activo | crear |
| mnt.activo.actualizar | activo | actualizar |
| mnt.orden_trabajo.leer | orden_trabajo | leer |
| mnt.orden_trabajo.crear | orden_trabajo | crear |
| mnt.orden_trabajo.actualizar | orden_trabajo | actualizar |
| mnt.plan_mantenimiento.leer | plan_mantenimiento | leer |
| mnt.plan_mantenimiento.crear | plan_mantenimiento | crear |
| mnt.plan_mantenimiento.actualizar | plan_mantenimiento | actualizar |
| mnt.historial_mantenimiento.leer | historial_mantenimiento | leer |
| mnt.historial_mantenimiento.crear | historial_mantenimiento | crear |
| mnt.historial_mantenimiento.actualizar | historial_mantenimiento | actualizar |

**Total permisos únicos MNT:** 12

---

## 4. Inconsistencias detectadas

Ninguna.

---

## 5. Confirmación introspección para auto-registro

Todos los handlers incluyen dependencia con string estático (f-string con constantes). Los 12 permisos serán detectados en startup y sincronizados a la tabla `permiso`.
