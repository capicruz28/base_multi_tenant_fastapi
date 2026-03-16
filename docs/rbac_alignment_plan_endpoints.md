# Plan de alineación RBAC — Endpoints por módulo

**Fecha:** 2026-02-18  
**Objetivo:** Listar todos los endpoints no alineados al estándar RBAC con permiso sugerido y clasificación de riesgo para la FASE 3 (solo modificar riesgo BAJO).

**Criterios de riesgo:**
- **BAJO:** CRUD estándar, recurso claro, permiso derivable por convención. Modificación automática permitida.
- **MEDIO:** Endpoint no-CRUD o múltiples recursos en el mismo router. Revisión manual antes de decorar.
- **ALTO:** Cambio de modelo de seguridad (ej. usuario actual), solo rol admin sin permiso granular, o exclusión por diseño. No modificar automáticamente.

**Leyenda:**  
`[S]` = permiso existente en seed RBAC.  
`[C]` = candidato para alta en tabla `permiso` (convención coherente con seed).

---

## HCM (Planillas y RRHH)

| Archivo | Método | Ruta | Función | Permiso sugerido | Riesgo |
|---------|--------|------|---------|------------------|--------|
| endpoints_empleados.py | GET | /api/v1/hcm/empleados | get_empleados | hcm.empleado.leer [S] | BAJO |
| endpoints_empleados.py | GET | /api/v1/hcm/empleados/{id} | get_empleado | hcm.empleado.leer [S] | BAJO |
| endpoints_empleados.py | POST | /api/v1/hcm/empleados | post_empleado | hcm.empleado.crear [S] | BAJO |
| endpoints_empleados.py | PUT | /api/v1/hcm/empleados/{id} | put_empleado | hcm.empleado.actualizar [S] | BAJO |
| endpoints_contratos.py | GET | /api/v1/hcm/contratos | get_contratos | hcm.contrato.leer [C] | BAJO |
| endpoints_contratos.py | GET | /api/v1/hcm/contratos/{id} | get_contrato | hcm.contrato.leer [C] | BAJO |
| endpoints_contratos.py | POST | /api/v1/hcm/contratos | post_contrato | hcm.contrato.crear [C] | BAJO |
| endpoints_contratos.py | PUT | /api/v1/hcm/contratos/{id} | put_contrato | hcm.contrato.actualizar [C] | BAJO |
| endpoints_conceptos_planilla.py | GET | /api/v1/hcm/conceptos-planilla | get_conceptos_planilla | hcm.concepto_planilla.leer [C] | BAJO |
| endpoints_conceptos_planilla.py | GET | /api/v1/hcm/conceptos-planilla/{id} | get_concepto_planilla | hcm.concepto_planilla.leer [C] | BAJO |
| endpoints_conceptos_planilla.py | POST | /api/v1/hcm/conceptos-planilla | post_concepto_planilla | hcm.concepto_planilla.crear [C] | BAJO |
| endpoints_conceptos_planilla.py | PUT | /api/v1/hcm/conceptos-planilla/{id} | put_concepto_planilla | hcm.concepto_planilla.actualizar [C] | BAJO |
| endpoints_planillas.py | GET | /api/v1/hcm/planillas | get_planillas | hcm.planilla.leer [S] | BAJO |
| endpoints_planillas.py | GET | /api/v1/hcm/planillas/{id} | get_planilla | hcm.planilla.leer [S] | BAJO |
| endpoints_planillas.py | POST | /api/v1/hcm/planillas | post_planilla | hcm.planilla.crear [S] | BAJO |
| endpoints_planillas.py | PUT | /api/v1/hcm/planillas/{id} | put_planilla | hcm.planilla.actualizar [C] | BAJO |
| endpoints_planilla_empleados.py | GET | /api/v1/hcm/planilla-empleados | get_planilla_empleados | hcm.planilla_empleado.leer [C] | BAJO |
| endpoints_planilla_empleados.py | GET | /api/v1/hcm/planilla-empleados/{id} | get_planilla_empleado | hcm.planilla_empleado.leer [C] | BAJO |
| endpoints_planilla_empleados.py | POST | /api/v1/hcm/planilla-empleados | post_planilla_empleado | hcm.planilla_empleado.crear [C] | BAJO |
| endpoints_planilla_empleados.py | PUT | /api/v1/hcm/planilla-empleados/{id} | put_planilla_empleado | hcm.planilla_empleado.actualizar [C] | BAJO |
| endpoints_planilla_detalle.py | GET | /api/v1/hcm/planilla-detalle | get_planilla_detalles | hcm.planilla_detalle.leer [C] | BAJO |
| endpoints_planilla_detalle.py | GET | /api/v1/hcm/planilla-detalle/{id} | get_planilla_detalle | hcm.planilla_detalle.leer [C] | BAJO |
| endpoints_planilla_detalle.py | POST | /api/v1/hcm/planilla-detalle | post_planilla_detalle | hcm.planilla_detalle.crear [C] | BAJO |
| endpoints_planilla_detalle.py | PUT | /api/v1/hcm/planilla-detalle/{id} | put_planilla_detalle | hcm.planilla_detalle.actualizar [C] | BAJO |
| endpoints_asistencia.py | GET | /api/v1/hcm/asistencia | get_asistencias | hcm.asistencia.leer [C] | BAJO |
| endpoints_asistencia.py | GET | /api/v1/hcm/asistencia/{id} | get_asistencia | hcm.asistencia.leer [C] | BAJO |
| endpoints_asistencia.py | POST | /api/v1/hcm/asistencia | post_asistencia | hcm.asistencia.crear [C] | BAJO |
| endpoints_asistencia.py | PUT | /api/v1/hcm/asistencia/{id} | put_asistencia | hcm.asistencia.actualizar [C] | BAJO |
| endpoints_vacaciones.py | GET | /api/v1/hcm/vacaciones | get_vacaciones | hcm.vacaciones.leer [C] | BAJO |
| endpoints_vacaciones.py | GET | /api/v1/hcm/vacaciones/{id} | get_vacaciones_by_id_endpoint | hcm.vacaciones.leer [C] | BAJO |
| endpoints_vacaciones.py | POST | /api/v1/hcm/vacaciones | post_vacaciones | hcm.vacaciones.crear [C] | BAJO |
| endpoints_vacaciones.py | PUT | /api/v1/hcm/vacaciones/{id} | put_vacaciones | hcm.vacaciones.actualizar [C] | BAJO |
| endpoints_prestamos.py | GET | /api/v1/hcm/prestamos | get_prestamos | hcm.prestamo.leer [C] | BAJO |
| endpoints_prestamos.py | GET | /api/v1/hcm/prestamos/{id} | get_prestamo | hcm.prestamo.leer [C] | BAJO |
| endpoints_prestamos.py | POST | /api/v1/hcm/prestamos | post_prestamo | hcm.prestamo.crear [C] | BAJO |
| endpoints_prestamos.py | PUT | /api/v1/hcm/prestamos/{id} | put_prestamo | hcm.prestamo.actualizar [C] | BAJO |

---

## LOG (Logística)

| Archivo | Método | Ruta | Función | Permiso sugerido | Riesgo |
|---------|--------|------|---------|------------------|--------|
| endpoints_transportistas.py | GET | /api/v1/log/transportistas | (list) | log.transportista.leer [C] | BAJO |
| endpoints_transportistas.py | GET | /api/v1/log/transportistas/{id} | (detail) | log.transportista.leer [C] | BAJO |
| endpoints_transportistas.py | POST | /api/v1/log/transportistas | (create) | log.transportista.crear [C] | BAJO |
| endpoints_transportistas.py | PUT | /api/v1/log/transportistas/{id} | (update) | log.transportista.actualizar [C] | BAJO |
| endpoints_vehiculos.py | GET | /api/v1/log/vehiculos | (list) | log.vehiculo.leer [C] | BAJO |
| endpoints_vehiculos.py | GET | /api/v1/log/vehiculos/{id} | (detail) | log.vehiculo.leer [C] | BAJO |
| endpoints_vehiculos.py | POST | /api/v1/log/vehiculos | (create) | log.vehiculo.crear [C] | BAJO |
| endpoints_vehiculos.py | PUT | /api/v1/log/vehiculos/{id} | (update) | log.vehiculo.actualizar [C] | BAJO |
| endpoints_rutas.py | GET | /api/v1/log/rutas | get_rutas | log.ruta.leer [S] | BAJO |
| endpoints_rutas.py | GET | /api/v1/log/rutas/{id} | get_ruta | log.ruta.leer [S] | BAJO |
| endpoints_rutas.py | POST | /api/v1/log/rutas | post_ruta | log.ruta.crear [S] | BAJO |
| endpoints_rutas.py | PUT | /api/v1/log/rutas/{id} | put_ruta | log.ruta.actualizar [S] | BAJO |
| endpoints_guias_remision.py | GET | /api/v1/log/guias-remision | get_guias_remision | log.guia_remision.leer [C] | BAJO |
| endpoints_guias_remision.py | GET | /api/v1/log/guias-remision/{id} | get_guia_remision | log.guia_remision.leer [C] | BAJO |
| endpoints_guias_remision.py | POST | /api/v1/log/guias-remision | post_guia_remision | log.guia_remision.crear [C] | BAJO |
| endpoints_guias_remision.py | PUT | /api/v1/log/guias-remision/{id} | put_guia_remision | log.guia_remision.actualizar [C] | BAJO |
| endpoints_guias_remision.py | GET | /api/v1/log/guias-remision/{id}/detalles | get_guia_remision_detalles | log.guia_remision_detalle.leer [C] | MEDIO |
| endpoints_guias_remision.py | POST | /api/v1/log/guias-remision/{id}/detalles | post_guia_remision_detalle | log.guia_remision_detalle.crear [C] | MEDIO |
| endpoints_guias_remision.py | GET | /api/v1/log/guias-remision/detalles/{id} | get_guia_remision_detalle | log.guia_remision_detalle.leer [C] | MEDIO |
| endpoints_guias_remision.py | PUT | /api/v1/log/guias-remision/detalles/{id} | put_guia_remision_detalle | log.guia_remision_detalle.actualizar [C] | MEDIO |
| endpoints_despachos.py | GET | /api/v1/log/despachos | (list) | log.despacho.leer [C] | BAJO |
| endpoints_despachos.py | GET | /api/v1/log/despachos/{id} | (detail) | log.despacho.leer [C] | BAJO |
| endpoints_despachos.py | POST | /api/v1/log/despachos | (create) | log.despacho.crear [C] | BAJO |
| endpoints_despachos.py | PUT | /api/v1/log/despachos/{id} | (update) | log.despacho.actualizar [C] | BAJO |

---

## INV (Inventarios)

| Archivo | Método | Ruta | Función | Permiso sugerido | Riesgo |
|---------|--------|------|---------|------------------|--------|
| endpoints_categorias.py | GET | /api/v1/inv/categorias | listar_categorias | inv.categoria.leer [C] | BAJO |
| endpoints_categorias.py | GET | /api/v1/inv/categorias/{id} | detalle_categoria | inv.categoria.leer [C] | BAJO |
| endpoints_categorias.py | POST | /api/v1/inv/categorias | crear_categoria | inv.categoria.crear [C] | BAJO |
| endpoints_categorias.py | PUT | /api/v1/inv/categorias/{id} | actualizar_categoria | inv.categoria.actualizar [C] | BAJO |
| endpoints_unidades_medida.py | GET | /api/v1/inv/unidades-medida | listar_unidades_medida | inv.unidad_medida.leer [C] | BAJO |
| endpoints_unidades_medida.py | GET | /api/v1/inv/unidades-medida/{id} | detalle_unidad_medida | inv.unidad_medida.leer [C] | BAJO |
| endpoints_unidades_medida.py | POST | /api/v1/inv/unidades-medida | crear_unidad_medida | inv.unidad_medida.crear [C] | BAJO |
| endpoints_unidades_medida.py | PUT | /api/v1/inv/unidades-medida/{id} | actualizar_unidad_medida | inv.unidad_medida.actualizar [C] | BAJO |
| endpoints_productos.py | GET | /api/v1/inv/productos | listar_productos | inv.producto.leer [S] | BAJO |
| endpoints_productos.py | GET | /api/v1/inv/productos/{id} | detalle_producto | inv.producto.leer [S] | BAJO |
| endpoints_productos.py | POST | /api/v1/inv/productos | crear_producto | inv.producto.crear [S] | BAJO |
| endpoints_productos.py | PUT | /api/v1/inv/productos/{id} | actualizar_producto | inv.producto.actualizar [S] | BAJO |
| endpoints_almacenes.py | GET | /api/v1/inv/almacenes | listar_almacenes | inv.almacen.leer [C] | BAJO |
| endpoints_almacenes.py | GET | /api/v1/inv/almacenes/{id} | detalle_almacen | inv.almacen.leer [C] | BAJO |
| endpoints_almacenes.py | POST | /api/v1/inv/almacenes | crear_almacen | inv.almacen.crear [C] | BAJO |
| endpoints_almacenes.py | PUT | /api/v1/inv/almacenes/{id} | actualizar_almacen | inv.almacen.actualizar [C] | BAJO |
| endpoints_stock.py | GET | /api/v1/inv/stock | listar_stocks | inv.stock.leer [C] | BAJO |
| endpoints_stock.py | GET | /api/v1/inv/stock/{id} | detalle_stock | inv.stock.leer [C] | BAJO |
| endpoints_stock.py | GET | /api/v1/inv/stock/producto/{pid}/almacen/{aid} | stock_por_producto_almacen | inv.stock.leer [C] | MEDIO |
| endpoints_stock.py | POST | /api/v1/inv/stock | crear_stock | inv.stock.crear [C] | BAJO |
| endpoints_stock.py | PUT | /api/v1/inv/stock/{id} | actualizar_stock | inv.stock.actualizar [C] | BAJO |
| endpoints_tipos_movimiento.py | GET | /api/v1/inv/tipos-movimiento | listar_tipos_movimiento | inv.tipo_movimiento.leer [C] | BAJO |
| endpoints_tipos_movimiento.py | GET | /api/v1/inv/tipos-movimiento/{id} | detalle_tipo_movimiento | inv.tipo_movimiento.leer [C] | BAJO |
| endpoints_tipos_movimiento.py | POST | /api/v1/inv/tipos-movimiento | crear_tipo_movimiento | inv.tipo_movimiento.crear [C] | BAJO |
| endpoints_tipos_movimiento.py | PUT | /api/v1/inv/tipos-movimiento/{id} | actualizar_tipo_movimiento | inv.tipo_movimiento.actualizar [C] | BAJO |
| endpoints_movimientos.py | GET | /api/v1/inv/movimientos | listar_movimientos | inv.movimiento.leer [C] | BAJO |
| endpoints_movimientos.py | GET | /api/v1/inv/movimientos/{id} | detalle_movimiento | inv.movimiento.leer [C] | BAJO |
| endpoints_movimientos.py | POST | /api/v1/inv/movimientos | crear_movimiento | inv.movimiento.crear [C] | BAJO |
| endpoints_movimientos.py | PUT | /api/v1/inv/movimientos/{id} | actualizar_movimiento | inv.movimiento.actualizar [C] | BAJO |
| endpoints_inventario_fisico.py | GET | /api/v1/inv/inventario-fisico | listar_inventarios_fisicos | inv.inventario_fisico.leer [C] | BAJO |
| endpoints_inventario_fisico.py | GET | /api/v1/inv/inventario-fisico/{id} | detalle_inventario_fisico | inv.inventario_fisico.leer [C] | BAJO |
| endpoints_inventario_fisico.py | POST | /api/v1/inv/inventario-fisico | crear_inventario_fisico | inv.inventario_fisico.crear [C] | BAJO |
| endpoints_inventario_fisico.py | PUT | /api/v1/inv/inventario-fisico/{id} | actualizar_inventario_fisico | inv.inventario_fisico.actualizar [C] | BAJO |

---

## FIN (Finanzas)

| Archivo | Método | Ruta | Función | Permiso sugerido | Riesgo |
|---------|--------|------|---------|------------------|--------|
| endpoints_plan_cuentas.py | GET | /api/v1/fin/plan-cuentas | get_plan_cuentas | fin.plan_cuenta.leer [C] | BAJO |
| endpoints_plan_cuentas.py | GET | /api/v1/fin/plan-cuentas/{id} | get_cuenta | fin.plan_cuenta.leer [C] | BAJO |
| endpoints_plan_cuentas.py | POST | /api/v1/fin/plan-cuentas | post_cuenta | fin.plan_cuenta.crear [C] | BAJO |
| endpoints_plan_cuentas.py | PUT | /api/v1/fin/plan-cuentas/{id} | put_cuenta | fin.plan_cuenta.actualizar [C] | BAJO |
| endpoints_periodos.py | GET | /api/v1/fin/periodos | get_periodos_contables | fin.periodo.leer [C] | BAJO |
| endpoints_periodos.py | GET | /api/v1/fin/periodos/{id} | get_periodo_contable | fin.periodo.leer [C] | BAJO |
| endpoints_periodos.py | POST | /api/v1/fin/periodos | post_periodo_contable | fin.periodo.crear [C] | BAJO |
| endpoints_periodos.py | PUT | /api/v1/fin/periodos/{id} | put_periodo_contable | fin.periodo.actualizar [C] | BAJO |
| endpoints_asientos.py | GET | /api/v1/fin/asientos | get_asientos_contables | fin.asiento.leer [S] | BAJO |
| endpoints_asientos.py | GET | /api/v1/fin/asientos/{id} | get_asiento_contable | fin.asiento.leer [S] | BAJO |
| endpoints_asientos.py | POST | /api/v1/fin/asientos | post_asiento_contable | fin.asiento.crear [S] | BAJO |
| endpoints_asientos.py | PUT | /api/v1/fin/asientos/{id} | put_asiento_contable | fin.asiento.actualizar [S] | BAJO |
| endpoints_asientos.py | GET | /api/v1/fin/asientos/{id}/detalles | get_asiento_detalles | fin.asiento_detalle.leer [C] | MEDIO |
| endpoints_asientos.py | POST | /api/v1/fin/asientos/{id}/detalles | post_asiento_detalle | fin.asiento_detalle.crear [C] | MEDIO |
| endpoints_asientos.py | GET | /api/v1/fin/asientos/detalles/{id} | get_asiento_detalle | fin.asiento_detalle.leer [C] | MEDIO |
| endpoints_asientos.py | PUT | /api/v1/fin/asientos/detalles/{id} | put_asiento_detalle | fin.asiento_detalle.actualizar [C] | MEDIO |

---

## SVC (Órdenes de servicio) — Parcialmente decorado

| Archivo | Método | Ruta | Función | Permiso sugerido | Riesgo |
|---------|--------|------|---------|------------------|--------|
| endpoints_orden_servicio.py | POST | /api/v1/svc/orden-servicio | post_orden_servicio | svc.orden_servicio.crear [S] | BAJO |

---

## TKT (Tickets) — Parcialmente decorado

| Archivo | Método | Ruta | Función | Permiso sugerido | Riesgo |
|---------|--------|------|---------|------------------|--------|
| endpoints_ticket.py | POST | /api/v1/tkt/tickets | post_ticket | tkt.ticket.crear [S] | BAJO |

---

## USERS — Casos especiales (NO modificar en FASE 3)

| Archivo | Método | Ruta | Función | Permiso sugerido | Riesgo |
|---------|--------|------|---------|------------------|--------|
| endpoints.py | GET | /api/v1/usuarios/{id}/ | read_usuario | admin.usuario.leer (opcional; cambia modelo actual) | ALTO |
| endpoints.py | GET | /api/v1/usuarios/{id}/roles/ | read_usuario_roles | admin.rol.leer (opcional; idem) | ALTO |

---

## RBAC — Permisos (Rol-Menú)

| Archivo | Método | Ruta | Función | Permiso sugerido | Riesgo |
|---------|--------|------|---------|------------------|--------|
| endpoints_permisos.py | PUT | /api/v1/permisos/roles/{rid}/menus/{mid}/ | (asignar/actualizar) | admin.rol.actualizar [S] | MEDIO |
| endpoints_permisos.py | GET | /api/v1/permisos/roles/{rid}/permisos/ | (listar) | admin.rol.leer [S] | MEDIO |
| endpoints_permisos.py | GET | /api/v1/permisos/roles/{rid}/menus/{mid}/ | (detalle) | admin.rol.leer [S] | MEDIO |
| endpoints_permisos.py | DELETE | /api/v1/permisos/roles/{rid}/menus/{mid}/ | (revocar) | admin.rol.actualizar [S] | MEDIO |

---

## Menus (legacy) y Áreas

| Archivo | Método | Ruta | Función | Permiso sugerido | Riesgo |
|---------|--------|------|---------|------------------|--------|
| endpoints.py (menus) | GET | /api/v1/menus/getmenu/ | (getmenu) | modulos.menu.leer [S] | MEDIO |
| endpoints.py (menus) | GET | /api/v1/menus/all-structured/ | (all-structured) | modulos.menu.leer [S] | MEDIO |
| endpoints.py (menus) | POST | /api/v1/menus/ | (create) | modulos.menu.administrar [S] | MEDIO |
| endpoints.py (menus) | GET | /api/v1/menus/{id}/ | (detail) | modulos.menu.leer [S] | MEDIO |
| endpoints.py (menus) | PUT | /api/v1/menus/{id}/ | (update) | modulos.menu.administrar [S] | MEDIO |
| endpoints.py (menus) | DELETE | /api/v1/menus/{id}/ | (delete) | modulos.menu.administrar [S] | MEDIO |
| endpoints.py (menus) | PUT | /api/v1/menus/{id}/reactivate/ | (reactivate) | modulos.menu.administrar [S] | MEDIO |
| endpoints.py (menus) | GET | /api/v1/menus/area/{id}/tree/ | (tree) | modulos.menu.leer [S] | MEDIO |
| endpoints_areas.py | POST | /api/v1/areas/ | (create) | modulos.menu.administrar [S] | MEDIO |
| endpoints_areas.py | GET | /api/v1/areas/ | (list) | modulos.menu.leer [S] | MEDIO |
| endpoints_areas.py | GET | /api/v1/areas/list/ | (list simple) | modulos.menu.leer [S] | MEDIO |
| endpoints_areas.py | GET | /api/v1/areas/{id}/ | (detail) | modulos.menu.leer [S] | MEDIO |
| endpoints_areas.py | PUT | /api/v1/areas/{id}/ | (update) | modulos.menu.administrar [S] | MEDIO |
| endpoints_areas.py | DELETE | /api/v1/areas/{id}/ | (delete) | modulos.menu.administrar [S] | MEDIO |
| endpoints_areas.py | PUT | /api/v1/areas/{id}/reactivate/ | (reactivate) | modulos.menu.administrar [S] | MEDIO |

---

## Resumen para FASE 3

- **Modificar automáticamente (riesgo BAJO):** todos los listados como BAJO en HCM, LOG (excepto detalles guía), INV, FIN (excepto detalles asiento), SVC POST, TKT POST.
- **No modificar en FASE 3:** todos los MEDIO y ALTO (Users read_usuario/read_usuario_roles, RBAC permisos rol-menú, Menus/Áreas). Quedan documentados para revisión manual posterior.
- **Permisos [C]:** los marcados como [C] son coherentes con la convención; si no existen en `permiso`, deben darse de alta en seed o vía auto-registro antes o después de aplicar la decoración.

---

## Módulos adicionales (PUR, SLS, INVBILL, PRC, WMS, QMS, CRM, POS, MFG resto, MRP, MPS, MNT, CST, TAX, BDG, PM)

Los endpoints de estos módulos siguen la misma estructura CRUD por recurso. La convención de permiso se deriva del seed y del path:

- **PUR:** `pur.orden_compra.*` [S], más recursos proveedor, contacto, solicitud, cotización, recepción → pur.proveedor.*, pur.solicitud.*, etc. [C]. Riesgo mayoritario **BAJO** para CRUD estándar.
- **SLS:** `sls.venta.*` [S]; recursos cliente, contacto, direccion, cotizacion, pedido → sls.cliente.*, sls.pedido.*, etc. [C]. **BAJO** para CRUD.
- **INVBILL:** `inv_bill.comprobante.*` [S]; series, detalles → inv_bill.serie.*, inv_bill.comprobante_detalle.* [C]. **BAJO** para CRUD.
- **PRC:** `prc.precio.*` [S]; listas, promociones → prc.lista_precio.*, prc.promocion.* [C]. **BAJO**.
- **WMS:** `wms.almacen.*` [S]; zonas, ubicaciones, tareas → wms.zona.*, wms.ubicacion.*, wms.tarea.* [C]. **BAJO**.
- **QMS:** `qms.inspeccion.*` [S]; parametros, planes, no_conformidades → qms.parametro.*, qms.plan.*, qms.no_conformidad.* [C]. **BAJO**.
- **CRM:** `crm.oportunidad.*` [S]; campanas, leads, actividades → crm.campana.*, crm.lead.*, crm.actividad.* [C]. **BAJO**.
- **POS:** `pos.venta.*` [S]; puntos_venta, turnos_caja, ventas_detalle → pos.punto_venta.*, pos.turno_caja.*, pos.venta_detalle.* [C]. **BAJO**.
- **MFG (resto):** centros_trabajo, operaciones, listas_materiales, rutas_fabricacion, etc. → mfg.centro_trabajo.*, mfg.operacion.*, mfg.lista_materiales.*, etc. [C]. **BAJO** para CRUD; subrecursos **MEDIO**.
- **MRP:** `mrp.plan_materiales.*` [S]; plan_maestro, necesidad_bruta, explosion_materiales, orden_sugerida → mrp.plan_maestro.*, mrp.necesidad_bruta.*, etc. [C]. **BAJO**.
- **MPS:** `mps.plan_maestro.*` [S]; pronostico_demanda, plan_produccion, plan_produccion_detalle [C]. **BAJO**.
- **MNT:** `mnt.activo.*`, `mnt.orden_trabajo.*` [S]; plan_mantenimiento, historial_mantenimiento [C]. **BAJO**.
- **CST:** `cst.costo.*` [S]; tipos centro costo, producto_costo [C]. **BAJO**.
- **TAX:** `tax.libro.*` [S]. **BAJO**.
- **BDG:** `bdg.presupuesto.*` [S]; presupuesto_detalle [C]. **BAJO** (detalle **MEDIO** si se considera recurso anidado).
- **PM:** `pm.proyecto.*` [S]. **BAJO**.

Para aplicar FASE 3 de forma masiva en estos módulos, usar esta misma tabla por archivo (método, ruta, función, permiso sugerido, riesgo) y limitar los cambios automáticos a filas con riesgo **BAJO**.
