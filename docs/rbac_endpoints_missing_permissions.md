# Auditoría RBAC – Endpoints sin Decorador

**Fecha de análisis:** 2026-02-18 (generado automáticamente)

**Criterio:** Se consideran "sin permiso" los endpoints que **no** declaran `@RequirePermission`, `require_permission(...)` ni `Depends(RequirePermission(...))` en el decorator o en `dependencies`.

**Convención del permiso sugerido:** `{modulo}.{recurso}.{accion}`  
- **modulo:** primer segmento del path (ej. `hcm`, `log`, `org`).  
- **recurso:** último segmento de ruta en snake_case, singularizado si aplica (ej. `planilla_detalle`, `guia_remision`).  
- **accion:** `read` | `create` | `update` | `delete` según método HTTP (GET→read, POST→create, PUT/PATCH→update, DELETE→delete).

---

## Resumen ejecutivo

| Métrica | Valor |
|--------|--------|
| Módulos con al menos un endpoint sin permiso | 25+ |
| Routers/archivos con endpoints sin permiso | 80+ |
| Endpoints sin permiso (estimado) | 350+ |
| Endpoints ya protegidos (org, modulos-menus, rbac roles/permisos-catalogo, aud log, svc/tkt/dms/wfl/mfg/bi/users con admin) | ~80+ |
| Endpoints excluidos por diseño (auth, health, docs) | No contabilizados |

---

## Endpoints excluidos por diseño (no requieren decorador RBAC)

- **`/api/v1/auth/*`** — Login, refresh, logout, sessions, SSO. Protegidos por autenticación y flujo propio.
- **`/health`**, **`/docs`**, **`/redoc`**, **`/openapi.json`** — Infraestructura y documentación.
- **`/`** — Raíz del servicio.

Estos **no** se listan como "faltantes" en las tablas siguientes.

---

## 📦 Módulo: HCM (Planillas y RRHH)

Prefijo API: `/api/v1/hcm`. Sub-routers: empleados, contratos, conceptos-planilla, planillas, planilla-empleados, planilla-detalle, asistencia, vacaciones, prestamos.

### Router: endpoints_empleados.py (prefix /empleados)

| Método | Endpoint | Función | Decorador sugerido | Nivel confianza |
|--------|----------|---------|--------------------|-----------------|
| GET | /api/v1/hcm/empleados | get_empleados | RequirePermission("hcm.empleado.read") | ALTO |
| GET | /api/v1/hcm/empleados/{empleado_id} | get_empleado | RequirePermission("hcm.empleado.read") | ALTO |
| POST | /api/v1/hcm/empleados | post_empleado | RequirePermission("hcm.empleado.create") | ALTO |
| PUT | /api/v1/hcm/empleados/{empleado_id} | put_empleado | RequirePermission("hcm.empleado.update") | ALTO |

*Recurso deducido del segmento de ruta `empleados` → singular `empleado`.*

### Router: endpoints_contratos.py (prefix /contratos)

| Método | Endpoint | Función | Decorador sugerido | Nivel confianza |
|--------|----------|---------|--------------------|-----------------|
| GET | /api/v1/hcm/contratos | get_contratos | RequirePermission("hcm.contrato.read") | ALTO |
| GET | /api/v1/hcm/contratos/{contrato_id} | get_contrato | RequirePermission("hcm.contrato.read") | ALTO |
| POST | /api/v1/hcm/contratos | post_contrato | RequirePermission("hcm.contrato.create") | ALTO |
| PUT | /api/v1/hcm/contratos/{contrato_id} | put_contrato | RequirePermission("hcm.contrato.update") | ALTO |

### Router: endpoints_conceptos_planilla.py (prefix /conceptos-planilla)

| Método | Endpoint | Función | Decorador sugerido | Nivel confianza |
|--------|----------|---------|--------------------|-----------------|
| GET | /api/v1/hcm/conceptos-planilla | get_conceptos_planilla | RequirePermission("hcm.concepto_planilla.read") | ALTO |
| GET | /api/v1/hcm/conceptos-planilla/{concepto_id} | get_concepto_planilla | RequirePermission("hcm.concepto_planilla.read") | ALTO |
| POST | /api/v1/hcm/conceptos-planilla | post_concepto_planilla | RequirePermission("hcm.concepto_planilla.create") | ALTO |
| PUT | /api/v1/hcm/conceptos-planilla/{concepto_id} | put_concepto_planilla | RequirePermission("hcm.concepto_planilla.update") | ALTO |

### Router: endpoints_planillas.py (prefix /planillas)

| Método | Endpoint | Función | Decorador sugerido | Nivel confianza |
|--------|----------|---------|--------------------|-----------------|
| GET | /api/v1/hcm/planillas | get_planillas | RequirePermission("hcm.planilla.read") | ALTO |
| GET | /api/v1/hcm/planillas/{planilla_id} | get_planilla | RequirePermission("hcm.planilla.read") | ALTO |
| POST | /api/v1/hcm/planillas | post_planilla | RequirePermission("hcm.planilla.create") | ALTO |
| PUT | /api/v1/hcm/planillas/{planilla_id} | put_planilla | RequirePermission("hcm.planilla.update") | ALTO |

### Router: endpoints_planilla_empleados.py (prefix /planilla-empleados)

| Método | Endpoint | Función | Decorador sugerido | Nivel confianza |
|--------|----------|---------|--------------------|-----------------|
| GET | /api/v1/hcm/planilla-empleados | get_planilla_empleados | RequirePermission("hcm.planilla_empleado.read") | ALTO |
| GET | /api/v1/hcm/planilla-empleados/{planilla_empleado_id} | get_planilla_empleado | RequirePermission("hcm.planilla_empleado.read") | ALTO |
| POST | /api/v1/hcm/planilla-empleados | post_planilla_empleado | RequirePermission("hcm.planilla_empleado.create") | ALTO |
| PUT | /api/v1/hcm/planilla-empleados/{planilla_empleado_id} | put_planilla_empleado | RequirePermission("hcm.planilla_empleado.update") | ALTO |

### Router: endpoints_planilla_detalle.py (prefix /planilla-detalle)

| Método | Endpoint | Función | Decorador sugerido | Nivel confianza |
|--------|----------|---------|--------------------|-----------------|
| GET | /api/v1/hcm/planilla-detalle | get_planilla_detalles | RequirePermission("hcm.planilla_detalle.read") | ALTO |
| GET | /api/v1/hcm/planilla-detalle/{planilla_detalle_id} | get_planilla_detalle | RequirePermission("hcm.planilla_detalle.read") | ALTO |
| POST | /api/v1/hcm/planilla-detalle | post_planilla_detalle | RequirePermission("hcm.planilla_detalle.create") | ALTO |
| PUT | /api/v1/hcm/planilla-detalle/{planilla_detalle_id} | put_planilla_detalle | RequirePermission("hcm.planilla_detalle.update") | ALTO |

### Router: endpoints_asistencia.py (prefix /asistencia)

| Método | Endpoint | Función | Decorador sugerido | Nivel confianza |
|--------|----------|---------|--------------------|-----------------|
| GET | /api/v1/hcm/asistencia | get_asistencias | RequirePermission("hcm.asistencia.read") | ALTO |
| GET | /api/v1/hcm/asistencia/{asistencia_id} | get_asistencia | RequirePermission("hcm.asistencia.read") | ALTO |
| POST | /api/v1/hcm/asistencia | post_asistencia | RequirePermission("hcm.asistencia.create") | ALTO |
| PUT | /api/v1/hcm/asistencia/{asistencia_id} | put_asistencia | RequirePermission("hcm.asistencia.update") | ALTO |

### Router: endpoints_vacaciones.py (prefix /vacaciones)

| Método | Endpoint | Función | Decorador sugerido | Nivel confianza |
|--------|----------|---------|--------------------|-----------------|
| GET | /api/v1/hcm/vacaciones | get_vacaciones | RequirePermission("hcm.vacaciones.read") | ALTO |
| GET | /api/v1/hcm/vacaciones/{vacaciones_id} | get_vacaciones_by_id_endpoint | RequirePermission("hcm.vacaciones.read") | ALTO |
| POST | /api/v1/hcm/vacaciones | post_vacaciones | RequirePermission("hcm.vacaciones.create") | ALTO |
| PUT | /api/v1/hcm/vacaciones/{vacaciones_id} | put_vacaciones | RequirePermission("hcm.vacaciones.update") | ALTO |

### Router: endpoints_prestamos.py (prefix /prestamos)

| Método | Endpoint | Función | Decorador sugerido | Nivel confianza |
|--------|----------|---------|--------------------|-----------------|
| GET | /api/v1/hcm/prestamos | get_prestamos | RequirePermission("hcm.prestamo.read") | ALTO |
| GET | /api/v1/hcm/prestamos/{prestamo_id} | get_prestamo | RequirePermission("hcm.prestamo.read") | ALTO |
| POST | /api/v1/hcm/prestamos | post_prestamo | RequirePermission("hcm.prestamo.create") | ALTO |
| PUT | /api/v1/hcm/prestamos/{prestamo_id} | put_prestamo | RequirePermission("hcm.prestamo.update") | ALTO |

---

## 📦 Módulo: LOG (Logística y Distribución)

Prefijo API: `/api/v1/log`. Sub-routers: transportistas, vehiculos, rutas, guias-remision, despachos.

### Router: endpoints_transportistas.py (prefix /transportistas)

| Método | Endpoint | Función | Decorador sugerido | Nivel confianza |
|--------|----------|---------|--------------------|-----------------|
| GET | /api/v1/log/transportistas | (list) | RequirePermission("log.transportista.read") | ALTO |
| GET | /api/v1/log/transportistas/{id} | (detail) | RequirePermission("log.transportista.read") | ALTO |
| POST | /api/v1/log/transportistas | (create) | RequirePermission("log.transportista.create") | ALTO |
| PUT | /api/v1/log/transportistas/{id} | (update) | RequirePermission("log.transportista.update") | ALTO |

### Router: endpoints_vehiculos.py (prefix /vehiculos)

| Método | Endpoint | Función | Decorador sugerido | Nivel confianza |
|--------|----------|---------|--------------------|-----------------|
| GET | /api/v1/log/vehiculos | (list) | RequirePermission("log.vehiculo.read") | ALTO |
| GET | /api/v1/log/vehiculos/{id} | (detail) | RequirePermission("log.vehiculo.read") | ALTO |
| POST | /api/v1/log/vehiculos | (create) | RequirePermission("log.vehiculo.create") | ALTO |
| PUT | /api/v1/log/vehiculos/{id} | (update) | RequirePermission("log.vehiculo.update") | ALTO |

### Router: endpoints_rutas.py (prefix /rutas)

| Método | Endpoint | Función | Decorador sugerido | Nivel confianza |
|--------|----------|---------|--------------------|-----------------|
| GET | /api/v1/log/rutas | get_rutas | RequirePermission("log.ruta.read") | ALTO |
| GET | /api/v1/log/rutas/{ruta_id} | get_ruta | RequirePermission("log.ruta.read") | ALTO |
| POST | /api/v1/log/rutas | post_ruta | RequirePermission("log.ruta.create") | ALTO |
| PUT | /api/v1/log/rutas/{ruta_id} | put_ruta | RequirePermission("log.ruta.update") | ALTO |

### Router: endpoints_guias_remision.py (prefix /guias-remision)

| Método | Endpoint | Función | Decorador sugerido | Nivel confianza |
|--------|----------|---------|--------------------|-----------------|
| GET | /api/v1/log/guias-remision | get_guias_remision | RequirePermission("log.guia_remision.read") | ALTO |
| GET | /api/v1/log/guias-remision/{guia_remision_id} | get_guia_remision | RequirePermission("log.guia_remision.read") | ALTO |
| POST | /api/v1/log/guias-remision | post_guia_remision | RequirePermission("log.guia_remision.create") | ALTO |
| PUT | /api/v1/log/guias-remision/{guia_remision_id} | put_guia_remision | RequirePermission("log.guia_remision.update") | ALTO |
| GET | /api/v1/log/guias-remision/{guia_remision_id}/detalles | get_guia_remision_detalles | RequirePermission("log.guia_remision_detalle.read") | ALTO |
| POST | /api/v1/log/guias-remision/{guia_remision_id}/detalles | post_guia_remision_detalle | RequirePermission("log.guia_remision_detalle.create") | ALTO |
| GET | /api/v1/log/guias-remision/detalles/{guia_detalle_id} | get_guia_remision_detalle | RequirePermission("log.guia_remision_detalle.read") | ALTO |
| PUT | /api/v1/log/guias-remision/detalles/{guia_detalle_id} | put_guia_remision_detalle | RequirePermission("log.guia_remision_detalle.update") | ALTO |

### Router: endpoints_despachos.py (prefix /despachos)

| Método | Endpoint | Función | Decorador sugerido | Nivel confianza |
|--------|----------|---------|--------------------|-----------------|
| GET | /api/v1/log/despachos | (list) | RequirePermission("log.despacho.read") | ALTO |
| GET | /api/v1/log/despachos/{id} | (detail) | RequirePermission("log.despacho.read") | ALTO |
| POST | /api/v1/log/despachos | (create) | RequirePermission("log.despacho.create") | ALTO |
| PUT | /api/v1/log/despachos/{id} | (update) | RequirePermission("log.despacho.update") | ALTO |

---

## 📦 Módulo: INV (Inventarios)

Prefijo API: `/api/v1/inv`. Sub-routers: categorias, unidades-medida, productos, almacenes, stock, tipos-movimiento, movimientos, inventario-fisico.

### Router: endpoints_categorias.py (prefix /categorias)

| Método | Endpoint | Función | Decorador sugerido | Nivel confianza |
|--------|----------|---------|--------------------|-----------------|
| GET | /api/v1/inv/categorias | listar_categorias | RequirePermission("inv.categoria.read") | ALTO |
| GET | /api/v1/inv/categorias/{categoria_id} | detalle_categoria | RequirePermission("inv.categoria.read") | ALTO |
| POST | /api/v1/inv/categorias | crear_categoria | RequirePermission("inv.categoria.create") | ALTO |
| PUT | /api/v1/inv/categorias/{categoria_id} | actualizar_categoria | RequirePermission("inv.categoria.update") | ALTO |

### Router: endpoints_unidades_medida.py (prefix /unidades-medida)

| Método | Endpoint | Función | Decorador sugerido | Nivel confianza |
|--------|----------|---------|--------------------|-----------------|
| GET | /api/v1/inv/unidades-medida | listar_unidades_medida | RequirePermission("inv.unidad_medida.read") | ALTO |
| GET | /api/v1/inv/unidades-medida/{unidad_medida_id} | detalle_unidad_medida | RequirePermission("inv.unidad_medida.read") | ALTO |
| POST | /api/v1/inv/unidades-medida | crear_unidad_medida | RequirePermission("inv.unidad_medida.create") | ALTO |
| PUT | /api/v1/inv/unidades-medida/{unidad_medida_id} | actualizar_unidad_medida | RequirePermission("inv.unidad_medida.update") | ALTO |

### Router: endpoints_productos.py (prefix /productos)

| Método | Endpoint | Función | Decorador sugerido | Nivel confianza |
|--------|----------|---------|--------------------|-----------------|
| GET | /api/v1/inv/productos | listar_productos | RequirePermission("inv.producto.read") | ALTO |
| GET | /api/v1/inv/productos/{producto_id} | detalle_producto | RequirePermission("inv.producto.read") | ALTO |
| POST | /api/v1/inv/productos | crear_producto | RequirePermission("inv.producto.create") | ALTO |
| PUT | /api/v1/inv/productos/{producto_id} | actualizar_producto | RequirePermission("inv.producto.update") | ALTO |

### Router: endpoints_almacenes.py (prefix /almacenes)

| Método | Endpoint | Función | Decorador sugerido | Nivel confianza |
|--------|----------|---------|--------------------|-----------------|
| GET | /api/v1/inv/almacenes | listar_almacenes | RequirePermission("inv.almacen.read") | ALTO |
| GET | /api/v1/inv/almacenes/{almacen_id} | detalle_almacen | RequirePermission("inv.almacen.read") | ALTO |
| POST | /api/v1/inv/almacenes | crear_almacen | RequirePermission("inv.almacen.create") | ALTO |
| PUT | /api/v1/inv/almacenes/{almacen_id} | actualizar_almacen | RequirePermission("inv.almacen.update") | ALTO |

### Router: endpoints_stock.py (prefix /stock)

| Método | Endpoint | Función | Decorador sugerido | Nivel confianza |
|--------|----------|---------|--------------------|-----------------|
| GET | /api/v1/inv/stock | listar_stocks | RequirePermission("inv.stock.read") | ALTO |
| GET | /api/v1/inv/stock/{stock_id} | detalle_stock | RequirePermission("inv.stock.read") | ALTO |
| GET | /api/v1/inv/stock/producto/{producto_id}/almacen/{almacen_id} | stock_por_producto_almacen | RequirePermission("inv.stock.read") | ALTO |
| POST | /api/v1/inv/stock | crear_stock | RequirePermission("inv.stock.create") | ALTO |
| PUT | /api/v1/inv/stock/{stock_id} | actualizar_stock | RequirePermission("inv.stock.update") | ALTO |

### Router: endpoints_tipos_movimiento.py (prefix /tipos-movimiento)

| Método | Endpoint | Función | Decorador sugerido | Nivel confianza |
|--------|----------|---------|--------------------|-----------------|
| GET | /api/v1/inv/tipos-movimiento | listar_tipos_movimiento | RequirePermission("inv.tipo_movimiento.read") | ALTO |
| GET | /api/v1/inv/tipos-movimiento/{tipo_movimiento_id} | detalle_tipo_movimiento | RequirePermission("inv.tipo_movimiento.read") | ALTO |
| POST | /api/v1/inv/tipos-movimiento | crear_tipo_movimiento | RequirePermission("inv.tipo_movimiento.create") | ALTO |
| PUT | /api/v1/inv/tipos-movimiento/{tipo_movimiento_id} | actualizar_tipo_movimiento | RequirePermission("inv.tipo_movimiento.update") | ALTO |

### Router: endpoints_movimientos.py (prefix /movimientos)

| Método | Endpoint | Función | Decorador sugerido | Nivel confianza |
|--------|----------|---------|--------------------|-----------------|
| GET | /api/v1/inv/movimientos | listar_movimientos | RequirePermission("inv.movimiento.read") | ALTO |
| GET | /api/v1/inv/movimientos/{movimiento_id} | detalle_movimiento | RequirePermission("inv.movimiento.read") | ALTO |
| POST | /api/v1/inv/movimientos | crear_movimiento | RequirePermission("inv.movimiento.create") | ALTO |
| PUT | /api/v1/inv/movimientos/{movimiento_id} | actualizar_movimiento | RequirePermission("inv.movimiento.update") | ALTO |

### Router: endpoints_inventario_fisico.py (prefix /inventario-fisico)

| Método | Endpoint | Función | Decorador sugerido | Nivel confianza |
|--------|----------|---------|--------------------|-----------------|
| GET | /api/v1/inv/inventario-fisico | listar_inventarios_fisicos | RequirePermission("inv.inventario_fisico.read") | ALTO |
| GET | /api/v1/inv/inventario-fisico/{inventario_fisico_id} | detalle_inventario_fisico | RequirePermission("inv.inventario_fisico.read") | ALTO |
| POST | /api/v1/inv/inventario-fisico | crear_inventario_fisico | RequirePermission("inv.inventario_fisico.create") | ALTO |
| PUT | /api/v1/inv/inventario-fisico/{inventario_fisico_id} | actualizar_inventario_fisico | RequirePermission("inv.inventario_fisico.update") | ALTO |

---

## 📦 Módulo: FIN (Finanzas y Contabilidad)

Prefijo API: `/api/v1/fin`. Sub-routers: plan-cuentas, periodos, asientos.

### Router: endpoints_plan_cuentas.py (prefix /plan-cuentas)

| Método | Endpoint | Función | Decorador sugerido | Nivel confianza |
|--------|----------|---------|--------------------|-----------------|
| GET | /api/v1/fin/plan-cuentas | get_plan_cuentas | RequirePermission("fin.plan_cuenta.read") | ALTO |
| GET | /api/v1/fin/plan-cuentas/{cuenta_id} | get_cuenta | RequirePermission("fin.plan_cuenta.read") | ALTO |
| POST | /api/v1/fin/plan-cuentas | post_cuenta | RequirePermission("fin.plan_cuenta.create") | ALTO |
| PUT | /api/v1/fin/plan-cuentas/{cuenta_id} | put_cuenta | RequirePermission("fin.plan_cuenta.update") | ALTO |

### Router: endpoints_periodos.py (prefix /periodos)

| Método | Endpoint | Función | Decorador sugerido | Nivel confianza |
|--------|----------|---------|--------------------|-----------------|
| GET | /api/v1/fin/periodos | get_periodos_contables | RequirePermission("fin.periodo.read") | ALTO |
| GET | /api/v1/fin/periodos/{periodo_id} | get_periodo_contable | RequirePermission("fin.periodo.read") | ALTO |
| POST | /api/v1/fin/periodos | post_periodo_contable | RequirePermission("fin.periodo.create") | ALTO |
| PUT | /api/v1/fin/periodos/{periodo_id} | put_periodo_contable | RequirePermission("fin.periodo.update") | ALTO |

### Router: endpoints_asientos.py (prefix /asientos)

| Método | Endpoint | Función | Decorador sugerido | Nivel confianza |
|--------|----------|---------|--------------------|-----------------|
| GET | /api/v1/fin/asientos | get_asientos_contables | RequirePermission("fin.asiento.read") | ALTO |
| GET | /api/v1/fin/asientos/{asiento_id} | get_asiento_contable | RequirePermission("fin.asiento.read") | ALTO |
| POST | /api/v1/fin/asientos | post_asiento_contable | RequirePermission("fin.asiento.create") | ALTO |
| PUT | /api/v1/fin/asientos/{asiento_id} | put_asiento_contable | RequirePermission("fin.asiento.update") | ALTO |
| GET | /api/v1/fin/asientos/{asiento_id}/detalles | get_asiento_detalles | RequirePermission("fin.asiento_detalle.read") | ALTO |
| POST | /api/v1/fin/asientos/{asiento_id}/detalles | post_asiento_detalle | RequirePermission("fin.asiento_detalle.create") | ALTO |
| GET | /api/v1/fin/asientos/detalles/{asiento_detalle_id} | get_asiento_detalle | RequirePermission("fin.asiento_detalle.read") | ALTO |
| PUT | /api/v1/fin/asientos/detalles/{asiento_detalle_id} | put_asiento_detalle | RequirePermission("fin.asiento_detalle.update") | ALTO |

---

## 📦 Módulo: SVC (Órdenes de Servicio) — Parcialmente protegido

Prefijo API: `/api/v1/svc`. El router `endpoints_orden_servicio.py` ya tiene `require_permission` en GET (list/detail) y PUT; **falta** en POST.

### Router: endpoints_orden_servicio.py

| Método | Endpoint | Función | Decorador sugerido | Nivel confianza |
|--------|----------|---------|--------------------|-----------------|
| POST | /api/v1/svc/orden-servicio | post_orden_servicio | RequirePermission("svc.orden_servicio.create") | ALTO |

*Nota: GET y PUT ya usan `require_permission("svc.orden_servicio.leer")` y `require_permission("svc.orden_servicio.actualizar")` respectivamente.*

---

## 📦 Módulo: RBAC – Permisos Rol-Menú

Prefijo API: `/api/v1/permisos`. El archivo `endpoints_permisos.py` (permisos rol-menú) **no** declara `require_permission` ni `RequirePermission`.

### Router: endpoints_permisos.py (prefix /permisos)

| Método | Endpoint | Función | Decorador sugerido | Nivel confianza |
|--------|----------|---------|--------------------|-----------------|
| GET | /api/v1/permisos/... | (list/CRUD rol-menu) | RequirePermission("admin.rol.leer") o permiso específico rol-menu | MEDIO |

*Recurso: permisos rol-menú; módulo sugerido `admin` o `rbac` según convención interna.*

---

## 📦 Módulo: Menus (Navegación legacy)

Prefijo API: `/api/v1/menus`. Los endpoints en `menus/presentation/endpoints.py` y relacionados **no** declaran permiso explícito en el código analizado.

| Método | Endpoint | Decorador sugerido | Nivel confianza |
|--------|----------|--------------------|-----------------|
| (según rutas en router /menus) | /api/v1/menus/... | RequirePermission("admin.menu.read") o similar | MEDIO |

---

## 📦 Módulos con todos los endpoints sin decorador RBAC

Para los siguientes módulos, **todos** los endpoints de los archivos listados carecen de `RequirePermission` / `require_permission` en el análisis estático. La convención del permiso sugerido es la misma: `{modulo}.{recurso}.{accion}`. *(INV y FIN tienen tablas detalladas en secciones anteriores.)*

- **PUR** (prefix `/api/v1/pur`): recepciones, ordenes-compra, cotizaciones, solicitudes.
- **SLS** (prefix `/api/v1/sls`): clientes, contactos, direcciones, cotizaciones, pedidos.
- **INVBILL** (prefix `/api/v1/inv-bill`): series, comprobantes, comprobantes-detalles.
- **PRC** (prefix `/api/v1/prc`): listas-precio, promociones.
- **WMS** (prefix `/api/v1/wms`): zonas, ubicaciones, stock-ubicacion, tareas.
- **QMS** (prefix `/api/v1/qms`): parametros-calidad, planes-inspeccion, inspecciones, no-conformidades.
- **CRM** (prefix `/api/v1/crm`): campanas, leads, oportunidades, actividades.
- **POS** (prefix `/api/v1/pos`): puntos-venta, turnos-caja, ventas, ventas-detalle.
- **MFG** (prefix `/api/v1/mfg`): centros-trabajo, operaciones, listas-materiales, lista-materiales-detalle, rutas-fabricacion, ruta-fabricacion-detalle, orden-produccion-operaciones, consumo-materiales. *(ordenes-produccion sí tiene permiso.)*
- **MRP** (prefix `/api/v1/mrp`): plan-maestro, necesidades-brutas, explosion-materiales, ordenes-sugeridas.
- **MPS** (prefix `/api/v1/mps`): pronostico-demanda, plan-produccion, plan-produccion-detalle.
- **MNT** (prefix `/api/v1/mnt`): activos, planes-mantenimiento, ordenes-trabajo, historial-mantenimiento.
- **CST** (prefix `/api/v1/cst`): tipos-centro-costo, producto-costo.
- **TAX** (prefix `/api/v1/tax`): libros-electronicos.
- **BDG** (prefix `/api/v1/bdg`): presupuestos, presupuesto-detalle.
- **PM** (prefix `/api/v1/pm`): proyectos.
- **Tenant / Super Admin:** clientes, conexiones, superadmin/usuarios, superadmin/auditoria, modulos-v2, cliente-modulo, secciones, plantillas-roles, areas.
- **Métricas:** router de métricas (tags ["Métricas y Monitoreo"]) — valorar si debe quedar sin RBAC o con permiso de monitoreo.

---

## 📦 Usuarios (GET por ID sin permiso explícito)

Prefijo: `/api/v1/usuarios`. La mayoría de los endpoints tienen `require_permission` (admin.usuario.*, admin.rol.asignar). El **GET /api/v1/usuarios/{usuario_id}/** usa solo `Depends(get_current_active_user)`; la autorización (propio usuario o admin) se hace en lógica interna.

| Método | Endpoint | Decorador sugerido | Nivel confianza |
|--------|----------|--------------------|-----------------|
| GET | /api/v1/usuarios/{usuario_id}/ | RequirePermission("admin.usuario.read") o mantener lógica interna | MEDIO |

*Si se desea homogeneidad con el resto de admin, se puede añadir el mismo permiso que el listado; si se desea que el usuario pueda ver su propio perfil sin rol admin, el diseño actual puede ser intencional.*

---

## Niveles de confianza — Criterios

- **ALTO:** Prefijo de módulo claro en `api.py`, recurso deducible del path del router (ej. `/hcm/planilla-detalle` → `planilla_detalle`), método HTTP estándar CRUD.
- **MEDIO:** Router anidado con prefijo compuesto o recurso que requiere interpretación (ej. permisos rol-menú, menus legacy).
- **BAJO:** Path ambiguo, rutas con parámetros que cambian el recurso, o endpoints no estándar (ej. acciones custom tipo `reordenar`, `duplicar`).

---

## Notas para la implementación

1. **Inserción:** Añadir el permiso en `dependencies=[Depends(RequirePermission({...}))]` del decorator del endpoint, o como dependencia adicional si ya existe `dependencies`.
2. **Formato RequirePermission:** Se puede usar `RequirePermission({"codigo": "modulo.recurso.accion", "nombre": "...", "recurso": "recurso", "accion": "accion", "modulo_codigo": "MOD"})` o, si el sistema lo admite, `require_permission("modulo.recurso.accion")` manteniendo la convención anterior (leer/actualizar/crear/eliminar según SEED).
3. **Acciones en español:** En el proyecto existen permisos con acciones en español (`leer`, `crear`, `actualizar`, `eliminar`). Los sugeridos en este documento usan `read`/`create`/`update`/`delete`; al implementar, alinear con la tabla `permiso` (p. ej. `leer` en lugar de `read`).
4. **No se ha modificado ningún archivo:** Esta auditoría es solo documentación previa a la aprobación humana y aplicación de cambios.
