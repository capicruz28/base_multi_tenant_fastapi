# Fase Final — Alineación RBAC Global — Estado y siguientes pasos

**Objetivo:** 100 % de endpoints con RBAC (Patrón A) para que el auto-registro popule la tabla `permiso`.

---

## Completado en esta sesión

| # | Módulo | Archivos decorados | Permisos únicos | Validación |
|---|--------|--------------------|-----------------|------------|
| 1 | **CST** | endpoints_centro_costo_tipo, endpoints_producto_costo | 6 | [rbac_cst_alignment_validation.md](rbac_cst_alignment_validation.md) |
| 2 | **MNT** | endpoints_activo, orden_trabajo, plan_mantenimiento, historial_mantenimiento | 12 | [rbac_mnt_alignment_validation.md](rbac_mnt_alignment_validation.md) |
| 3 | **PUR** | proveedores, contactos, productos_proveedor, solicitudes, cotizaciones, ordenes_compra, recepciones | 21 | [rbac_pur_alignment_validation.md](rbac_pur_alignment_validation.md) |
| 4 | **SLS** | clientes, contactos, direcciones, cotizaciones, pedidos | 15 | [rbac_sls_alignment_validation.md](rbac_sls_alignment_validation.md) |
| 5 | **WMS** | zonas, ubicaciones, tareas, stock | 12 | [rbac_wms_alignment_validation.md](rbac_wms_alignment_validation.md) |
| 6 | **QMS** | parametros, no_conformidades, inspecciones, planes | 12 | [rbac_qms_alignment_validation.md](rbac_qms_alignment_validation.md) |
| 7 | **CRM** | oportunidades, leads, actividades, campanas | 12 | Pendiente doc validación |
| 8 | **POS** | ventas, ventas_detalle, turnos_caja, puntos_venta | 12 | Pendiente doc validación |
| 9 | **TAX** | libro_electronico (libro) | 4 | Pendiente doc validación |
| 10 | **BDG** | presupuesto, presupuesto_detalle | 8 | Pendiente doc validación |
| 11 | **PM** | proyecto | 4 | Pendiente doc validación |
| 12 | **MRP** | plan_maestro, orden_sugerida, explosion_materiales, necesidad_bruta | 16 | Pendiente doc validación |
| 13 | **MPS** | plan_produccion, plan_produccion_detalle, pronostico_demanda | 12 | Pendiente doc validación |
| 14 | **INV_BILL** | comprobantes, series, comprobante_detalles | 12 | Pendiente doc validación |
| 15 | **PRC** | listas_precio, promociones | 7 | Pendiente doc validación |

**Total ya alineados:** 15 módulos, ~163 permisos únicos (aprox.), todos con Patrón A e introspección válida. Reporte global: [rbac_global_alignment_report.md](rbac_global_alignment_report.md).

---

## Pendientes (opcional)

Aplicar en cada archivo de presentación:

1. **Import:** `from app.core.authorization.rbac import require_permission`
2. **Constantes:** `MODULE_CODE = "<modulo>"` y `RESOURCE_CODE = "<recurso>"` (una por router/archivo).
3. **En cada handler:** añadir  
   `_: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.<accion>"))`  
   con `<accion>` = `leer` (GET), `crear` (POST), `actualizar` (PUT/PATCH), `eliminar` (DELETE).

### Módulos ya decorados (lista de referencia)

Los módulos CRM, POS, TAX, BDG, PM, MRP, MPS, INV_BILL y PRC ya tienen todos sus archivos de endpoints decorados con Patrón A. Opcional: generar para cada uno `docs/rbac_<modulo>_alignment_validation.md` con: endpoints encontrados, decorados, permisos generados, inconsistencias, confirmación de introspección.

---

## Reporte global final

Cuando **todos** los módulos (1–15) estén alineados, generar:

**`docs/rbac_global_alignment_report.md`**

con:

- Total endpoints del sistema
- Total endpoints con RBAC
- Total permisos detectables por auto-registro
- Número esperado de registros en tabla `permiso` (tras sync)

---

## Convenciones (recordatorio)

- **Sin tocar:** lógica de negocio, paths, `response_model`, validaciones, servicios.
- **Solo añadir:** decoración RBAC (import + constantes + `Depends(require_permission(...))`).
- Código fuente = **única fuente de verdad** del catálogo de permisos; no depender de seed para permisos de negocio nuevos.
