# Reporte global — Alineación RBAC

**Fecha:** 2026-02-18  
**Estado:** Alineación Patrón A aplicada a módulos de negocio objetivo.

---

## 1. Resumen ejecutivo

- **Total de rutas (APIRoute) en la aplicación:** estimado > 400 (módulos api/v1, auth, rbac, org, inv, fin, log, hcm, mfg, bi, tenant, etc.).
- **Endpoints con RBAC (Patrón A):** los módulos listados en la tabla siguiente tienen todos sus handlers decorados con `Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.<accion>"))`.
- **Permisos detectables por auto-registro:** cada uso de `require_permission("modulo.recurso.accion")` con string estático (f-string con constantes) es inspeccionado en startup por `permission_startup.ensure_registry_from_routes`; los códigos únicos se registran en `PermissionRegistry` y luego se sincronizan a la tabla `permiso`.
- **Registros esperados en tabla `permiso`:** coinciden con el número de **permisos únicos** (modulo.recurso.accion) detectados en código. El sync inserta o actualiza por `codigo`.

---

## 2. Módulos alineados (Patrón A)

| Módulo | MODULE_CODE | Archivos endpoints | Recursos | Permisos únicos (aprox.) |
|--------|-------------|--------------------|----------|---------------------------|
| CST | cst | centro_costo_tipo, producto_costo | 2 | 6 |
| MNT | mnt | activo, orden_trabajo, plan_mantenimiento, historial_mantenimiento | 4 | 12 |
| PUR | pur | proveedores, contactos, productos_proveedor, solicitudes, cotizaciones, ordenes_compra, recepciones | 7 | 21 |
| SLS | sls | clientes, contactos, direcciones, cotizaciones, pedidos | 5 | 15 |
| WMS | wms | zonas, ubicaciones, tareas, stock | 4 | 12 |
| QMS | qms | parametros, no_conformidades, inspecciones, planes | 4 | 12 |
| CRM | crm | oportunidades, leads, actividades, campanas | 4 | 12 |
| POS | pos | ventas, ventas_detalle, turnos_caja, puntos_venta | 4 | 12 |
| TAX | tax | libro_electronico (libro) | 1 | 4 |
| BDG | bdg | presupuesto, presupuesto_detalle | 2 | 8 |
| PM | pm | proyecto | 1 | 4 |
| MRP | mrp | plan_maestro, orden_sugerida, explosion_materiales, necesidad_bruta | 4 | 16 |
| MPS | mps | plan_produccion, plan_produccion_detalle, pronostico_demanda | 3 | 12 |
| INV_BILL | inv_bill | comprobante, serie, comprobante_detalle | 3 | 12 |
| PRC | prc | lista_precio, promocion | 2 | 7 (lista_precio: leer/crear/actualizar x lista + detalles) |

**Total permisos únicos (módulos tabla):** ~163 (estimado; el valor exacto lo da el registry tras el próximo arranque).

---

## 3. Otros módulos con RBAC

Además de los anteriores, otros routers ya usan `require_permission` (menus, users, rbac, modulos, fin, inv, log, hcm, org, aud, dms, wfl, mfg, bi, tkt, svc, tenant, superadmin, auth, etc.). No se contabilizan aquí como “alineación fase final” pero sí contribuyen al total de endpoints con RBAC y al número de registros en `permiso`.

---

## 4. Cifras objetivo

| Concepto | Valor |
|----------|--------|
| Endpoints totales del sistema (APIRoute) | > 400 |
| Endpoints con RBAC (decorados con require_permission) | En aumento según módulos alineados |
| Permisos únicos detectables por introspección | Los que tengan string estático en `require_permission(...)` |
| Registros esperados en tabla `permiso` tras sync | Igual al número de permisos únicos en el registry |

---

## 5. Validación e introspección

- **Introspección:** Los callables devueltos por `require_permission("codigo")` exponen `__permission_codigo__`, leído por `permission_startup.ensure_registry_from_routes`.
- **Sync:** `PermissionSyncService.sync()` persiste/actualiza en `permiso` según el registry.
- **Rutas excluidas:** Paths en `SKIP_PATHS` y prefijos en `SKIP_PREFIXES` (p. ej. `/api/v1/auth`) no se exige permiso declarado.

---

## 6. Próximos pasos opcionales

- Crear `docs/rbac_<modulo>_alignment_validation.md` para CRM, POS, TAX, BDG, PM, MRP, MPS, INV_BILL, PRC (misma estructura que CST/MNT/PUR).
- Revisar módulos restantes (inv, fin, log, hcm, mfg, org, etc.) para unificar patrón y completar 100 % de endpoints con RBAC si se desea.
