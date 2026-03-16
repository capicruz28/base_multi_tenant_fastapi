# Análisis de endpoints sin decorador RBAC

**Fecha:** 2026-02-18  
**Objetivo:** Diagnóstico de todos los endpoints que no tienen `@RequirePermission` ni `require_permission`, y por qué no pudieron ser decorados automáticamente durante el proceso RBAC.  
**Uso:** Base para una futura decoración automática segura. No se modifica código.

---

## 1. Resumen general

| Métrica | Valor |
|--------|--------|
| **Total de endpoints** (API v1, excl. health/docs/openapi) | **~430** |
| **Endpoints con decorador RBAC** (require_permission / RequirePermission) | **~78** |
| **Endpoints sin decorador de permiso** | **~352** |
| **Porcentaje de cobertura RBAC** | **~18 %** |
| **Endpoints excluidos por diseño** (auth login/refresh/logout/sessions, SSO, health, docs) | No contabilizados en total |

**Desglose de decorados:**

- **ORG** (empresa, departamentos, parametros, centros_costo, cargos, sucursales): ~24 endpoints con `require_permission("org.area.*")`.
- **Modulos** (menus, plantillas, secciones, cliente_modulo, modulos): ~55 endpoints con `require_permission("modulos.menu.leer|administrar")`.
- **RBAC** (roles, permisos-catalogo): ~14 endpoints con `require_admin` + `require_permission("admin.rol.*")` o solo `require_permission`.
- **AUD** (log auditoría): 3 con `require_permission("aud.log.leer")`.
- **SVC** (orden servicio): 3 de 4 (GET list, GET by id, PUT); POST sin permiso.
- **TKT, DMS, WFL, MFG** (ordenes_produccion), **BI**: 4 cada uno con permiso.
- **Users**: 6 con `require_admin` + `require_permission`; 2 (GET by id, GET roles) solo `get_current_active_user`.

**Excluidos de la auditoría RBAC (no requieren permiso por diseño):**

- `/auth/*` (login, refresh, logout, sessions, SSO, me, permissions/me, menu).
- `/health`, `/docs`, `/redoc`, `/openapi.json`, `/`.

---

## 2. Lista completa de endpoints SIN decorador

Organizada por **módulo** → **router (archivo)** → **archivo fuente**. Para cada endpoint: método HTTP, ruta completa (base `/api/v1`), función, archivo y **motivo técnico** (categoría A–H) por el cual no puede inferirse automáticamente el permiso.

**Leyenda de categorías:**

- **A** Recurso ambiguo  
- **B** Naming inconsistente  
- **C** Endpoint no-CRUD (acción)  
- **D** Router sin metadata de recurso  
- **E** Múltiples recursos involucrados  
- **F** Decorador custom no reconocido  
- **G** Prefijo mal estructurado  
- **H** Otro (explicar)

---

### 2.1 Módulo: HCM (Planillas y RRHH)

Prefijo API: `/api/v1/hcm`. Routers: empleados, contratos, conceptos-planilla, planillas, planilla-empleados, planilla-detalle, asistencia, vacaciones, prestamos.

| Método | Ruta | Función | Archivo fuente | Motivo |
|--------|------|---------|----------------|--------|
| GET | /api/v1/hcm/empleados | get_empleados | endpoints_empleados.py | D |
| GET | /api/v1/hcm/empleados/{id} | get_empleado | endpoints_empleados.py | D |
| POST | /api/v1/hcm/empleados | post_empleado | endpoints_empleados.py | D |
| PUT | /api/v1/hcm/empleados/{id} | put_empleado | endpoints_empleados.py | D |
| GET | /api/v1/hcm/contratos | get_contratos | endpoints_contratos.py | D |
| GET | /api/v1/hcm/contratos/{id} | get_contrato | endpoints_contratos.py | D |
| POST | /api/v1/hcm/contratos | post_contrato | endpoints_contratos.py | D |
| PUT | /api/v1/hcm/contratos/{id} | put_contrato | endpoints_contratos.py | D |
| GET | /api/v1/hcm/conceptos-planilla | get_conceptos_planilla | endpoints_conceptos_planilla.py | D |
| GET | /api/v1/hcm/conceptos-planilla/{id} | get_concepto_planilla | endpoints_conceptos_planilla.py | D |
| POST | /api/v1/hcm/conceptos-planilla | post_concepto_planilla | endpoints_conceptos_planilla.py | D |
| PUT | /api/v1/hcm/conceptos-planilla/{id} | put_concepto_planilla | endpoints_conceptos_planilla.py | D |
| GET | /api/v1/hcm/planillas | get_planillas | endpoints_planillas.py | D |
| GET | /api/v1/hcm/planillas/{id} | get_planilla | endpoints_planillas.py | D |
| POST | /api/v1/hcm/planillas | post_planilla | endpoints_planillas.py | D |
| PUT | /api/v1/hcm/planillas/{id} | put_planilla | endpoints_planillas.py | D |
| GET | /api/v1/hcm/planilla-empleados | get_planilla_empleados | endpoints_planilla_empleados.py | D |
| GET | /api/v1/hcm/planilla-empleados/{id} | get_planilla_empleado | endpoints_planilla_empleados.py | D |
| POST | /api/v1/hcm/planilla-empleados | post_planilla_empleado | endpoints_planilla_empleados.py | D |
| PUT | /api/v1/hcm/planilla-empleados/{id} | put_planilla_empleado | endpoints_planilla_empleados.py | D |
| GET | /api/v1/hcm/planilla-detalle | get_planilla_detalles | endpoints_planilla_detalle.py | D |
| GET | /api/v1/hcm/planilla-detalle/{id} | get_planilla_detalle | endpoints_planilla_detalle.py | D |
| POST | /api/v1/hcm/planilla-detalle | post_planilla_detalle | endpoints_planilla_detalle.py | D |
| PUT | /api/v1/hcm/planilla-detalle/{id} | put_planilla_detalle | endpoints_planilla_detalle.py | D |
| GET | /api/v1/hcm/asistencia | get_asistencias | endpoints_asistencia.py | D |
| GET | /api/v1/hcm/asistencia/{id} | get_asistencia | endpoints_asistencia.py | D |
| POST | /api/v1/hcm/asistencia | post_asistencia | endpoints_asistencia.py | D |
| PUT | /api/v1/hcm/asistencia/{id} | put_asistencia | endpoints_asistencia.py | D |
| GET | /api/v1/hcm/vacaciones | get_vacaciones | endpoints_vacaciones.py | D |
| GET | /api/v1/hcm/vacaciones/{id} | get_vacaciones_by_id_endpoint | endpoints_vacaciones.py | D |
| POST | /api/v1/hcm/vacaciones | post_vacaciones | endpoints_vacaciones.py | D |
| PUT | /api/v1/hcm/vacaciones/{id} | put_vacaciones | endpoints_vacaciones.py | D |
| GET | /api/v1/hcm/prestamos | get_prestamos | endpoints_prestamos.py | D |
| GET | /api/v1/hcm/prestamos/{id} | get_prestamo | endpoints_prestamos.py | D |
| POST | /api/v1/hcm/prestamos | post_prestamo | endpoints_prestamos.py | D |
| PUT | /api/v1/hcm/prestamos/{id} | put_prestamo | endpoints_prestamos.py | D |

---

### 2.2 Módulo: LOG (Logística)

Prefijo: `/api/v1/log`. Routers: transportistas, vehiculos, rutas, guias-remision, despachos.

| Método | Ruta | Función | Archivo fuente | Motivo |
|--------|------|---------|----------------|--------|
| GET | /api/v1/log/transportistas | (list) | endpoints_transportistas.py | D |
| GET | /api/v1/log/transportistas/{id} | (detail) | endpoints_transportistas.py | D |
| POST | /api/v1/log/transportistas | (create) | endpoints_transportistas.py | D |
| PUT | /api/v1/log/transportistas/{id} | (update) | endpoints_transportistas.py | D |
| GET | /api/v1/log/vehiculos | (list) | endpoints_vehiculos.py | D |
| GET | /api/v1/log/vehiculos/{id} | (detail) | endpoints_vehiculos.py | D |
| POST | /api/v1/log/vehiculos | (create) | endpoints_vehiculos.py | D |
| PUT | /api/v1/log/vehiculos/{id} | (update) | endpoints_vehiculos.py | D |
| GET | /api/v1/log/rutas | get_rutas | endpoints_rutas.py | D |
| GET | /api/v1/log/rutas/{id} | get_ruta | endpoints_rutas.py | D |
| POST | /api/v1/log/rutas | post_ruta | endpoints_rutas.py | D |
| PUT | /api/v1/log/rutas/{id} | put_ruta | endpoints_rutas.py | D |
| GET | /api/v1/log/guias-remision | get_guias_remision | endpoints_guias_remision.py | D |
| GET | /api/v1/log/guias-remision/{id} | get_guia_remision | endpoints_guias_remision.py | D |
| POST | /api/v1/log/guias-remision | post_guia_remision | endpoints_guias_remision.py | D |
| PUT | /api/v1/log/guias-remision/{id} | put_guia_remision | endpoints_guias_remision.py | D |
| GET | /api/v1/log/guias-remision/{id}/detalles | get_guia_remision_detalles | endpoints_guias_remision.py | A, E |
| POST | /api/v1/log/guias-remision/{id}/detalles | post_guia_remision_detalle | endpoints_guias_remision.py | A, E |
| GET | /api/v1/log/guias-remision/detalles/{id} | get_guia_remision_detalle | endpoints_guias_remision.py | A, E |
| PUT | /api/v1/log/guias-remision/detalles/{id} | put_guia_remision_detalle | endpoints_guias_remision.py | A, E |
| GET | /api/v1/log/despachos | (list) | endpoints_despachos.py | D |
| GET | /api/v1/log/despachos/{id} | (detail) | endpoints_despachos.py | D |
| POST | /api/v1/log/despachos | (create) | endpoints_despachos.py | D |
| PUT | /api/v1/log/despachos/{id} | (update) | endpoints_despachos.py | D |

---

### 2.3 Módulo: INV (Inventarios)

Prefijo: `/api/v1/inv`. Routers: categorias, unidades-medida, productos, almacenes, stock, tipos-movimiento, movimientos, inventario-fisico.

| Método | Ruta | Función | Archivo fuente | Motivo |
|--------|------|---------|----------------|--------|
| GET | /api/v1/inv/categorias | listar_categorias | endpoints_categorias.py | D |
| GET | /api/v1/inv/categorias/{id} | detalle_categoria | endpoints_categorias.py | D |
| POST | /api/v1/inv/categorias | crear_categoria | endpoints_categorias.py | D |
| PUT | /api/v1/inv/categorias/{id} | actualizar_categoria | endpoints_categorias.py | D |
| GET | /api/v1/inv/unidades-medida | listar_unidades_medida | endpoints_unidades_medida.py | D |
| GET | /api/v1/inv/unidades-medida/{id} | detalle_unidad_medida | endpoints_unidades_medida.py | D |
| POST | /api/v1/inv/unidades-medida | crear_unidad_medida | endpoints_unidades_medida.py | D |
| PUT | /api/v1/inv/unidades-medida/{id} | actualizar_unidad_medida | endpoints_unidades_medida.py | D |
| GET | /api/v1/inv/productos | listar_productos | endpoints_productos.py | D |
| GET | /api/v1/inv/productos/{id} | detalle_producto | endpoints_productos.py | D |
| POST | /api/v1/inv/productos | crear_producto | endpoints_productos.py | D |
| PUT | /api/v1/inv/productos/{id} | actualizar_producto | endpoints_productos.py | D |
| GET | /api/v1/inv/almacenes | listar_almacenes | endpoints_almacenes.py | D |
| GET | /api/v1/inv/almacenes/{id} | detalle_almacen | endpoints_almacenes.py | D |
| POST | /api/v1/inv/almacenes | crear_almacen | endpoints_almacenes.py | D |
| PUT | /api/v1/inv/almacenes/{id} | actualizar_almacen | endpoints_almacenes.py | D |
| GET | /api/v1/inv/stock | listar_stocks | endpoints_stock.py | D |
| GET | /api/v1/inv/stock/{id} | detalle_stock | endpoints_stock.py | D |
| GET | /api/v1/inv/stock/producto/{pid}/almacen/{aid} | stock_por_producto_almacen | endpoints_stock.py | E |
| POST | /api/v1/inv/stock | crear_stock | endpoints_stock.py | D |
| PUT | /api/v1/inv/stock/{id} | actualizar_stock | endpoints_stock.py | D |
| GET | /api/v1/inv/tipos-movimiento | listar_tipos_movimiento | endpoints_tipos_movimiento.py | D |
| GET | /api/v1/inv/tipos-movimiento/{id} | detalle_tipo_movimiento | endpoints_tipos_movimiento.py | D |
| POST | /api/v1/inv/tipos-movimiento | crear_tipo_movimiento | endpoints_tipos_movimiento.py | D |
| PUT | /api/v1/inv/tipos-movimiento/{id} | actualizar_tipo_movimiento | endpoints_tipos_movimiento.py | D |
| GET | /api/v1/inv/movimientos | listar_movimientos | endpoints_movimientos.py | D |
| GET | /api/v1/inv/movimientos/{id} | detalle_movimiento | endpoints_movimientos.py | D |
| POST | /api/v1/inv/movimientos | crear_movimiento | endpoints_movimientos.py | D |
| PUT | /api/v1/inv/movimientos/{id} | actualizar_movimiento | endpoints_movimientos.py | D |
| GET | /api/v1/inv/inventario-fisico | listar_inventarios_fisicos | endpoints_inventario_fisico.py | D |
| GET | /api/v1/inv/inventario-fisico/{id} | detalle_inventario_fisico | endpoints_inventario_fisico.py | D |
| POST | /api/v1/inv/inventario-fisico | crear_inventario_fisico | endpoints_inventario_fisico.py | D |
| PUT | /api/v1/inv/inventario-fisico/{id} | actualizar_inventario_fisico | endpoints_inventario_fisico.py | D |

---

### 2.4 Módulo: FIN (Finanzas)

Prefijo: `/api/v1/fin`. Routers: plan-cuentas, periodos, asientos.

| Método | Ruta | Función | Archivo fuente | Motivo |
|--------|------|---------|----------------|--------|
| GET | /api/v1/fin/plan-cuentas | get_plan_cuentas | endpoints_plan_cuentas.py | D |
| GET | /api/v1/fin/plan-cuentas/{id} | get_cuenta | endpoints_plan_cuentas.py | D |
| POST | /api/v1/fin/plan-cuentas | post_cuenta | endpoints_plan_cuentas.py | D |
| PUT | /api/v1/fin/plan-cuentas/{id} | put_cuenta | endpoints_plan_cuentas.py | D |
| GET | /api/v1/fin/periodos | get_periodos_contables | endpoints_periodos.py | D |
| GET | /api/v1/fin/periodos/{id} | get_periodo_contable | endpoints_periodos.py | D |
| POST | /api/v1/fin/periodos | post_periodo_contable | endpoints_periodos.py | D |
| PUT | /api/v1/fin/periodos/{id} | put_periodo_contable | endpoints_periodos.py | D |
| GET | /api/v1/fin/asientos | get_asientos_contables | endpoints_asientos.py | D |
| GET | /api/v1/fin/asientos/{id} | get_asiento_contable | endpoints_asientos.py | D |
| POST | /api/v1/fin/asientos | post_asiento_contable | endpoints_asientos.py | D |
| PUT | /api/v1/fin/asientos/{id} | put_asiento_contable | endpoints_asientos.py | D |
| GET | /api/v1/fin/asientos/{id}/detalles | get_asiento_detalles | endpoints_asientos.py | A, E |
| POST | /api/v1/fin/asientos/{id}/detalles | post_asiento_detalle | endpoints_asientos.py | A, E |
| GET | /api/v1/fin/asientos/detalles/{id} | get_asiento_detalle | endpoints_asientos.py | A, E |
| PUT | /api/v1/fin/asientos/detalles/{id} | put_asiento_detalle | endpoints_asientos.py | A, E |

---

### 2.5 Módulos con decoración parcial (1–2 endpoints sin permiso)

**SVC (Órdenes de servicio)**

| Método | Ruta | Función | Archivo fuente | Motivo |
|--------|------|---------|----------------|--------|
| POST | /api/v1/svc/orden-servicio | post_orden_servicio | endpoints_orden_servicio.py | H (omisión manual; GET/PUT sí tienen permiso) |

**TKT (Tickets)**

| Método | Ruta | Función | Archivo fuente | Motivo |
|--------|------|---------|----------------|--------|
| POST | /api/v1/tkt/tickets | post_ticket | endpoints_ticket.py | H (omisión manual; GET/PUT sí tienen permiso) |

---

### 2.6 Módulo: Users — 2 endpoints sin permiso explícito

| Método | Ruta | Función | Archivo fuente | Motivo |
|--------|------|---------|----------------|--------|
| GET | /api/v1/usuarios/{id}/ | read_usuario | endpoints.py | H (diseño: usuario puede ver su perfil o admin; validación por cliente en lógica) |
| GET | /api/v1/usuarios/{id}/roles/ | read_usuario_roles | endpoints.py | H (idem) |

---

### 2.7 Módulo: RBAC — Permisos (Rol-Menú)

Prefijo: `/api/v1/permisos`. Archivo: endpoints_permisos.py. Usan solo `require_admin`, no `require_permission`.

| Método | Ruta | Función | Archivo fuente | Motivo |
|--------|------|---------|----------------|--------|
| PUT | /api/v1/permisos/roles/{rol_id}/menus/{menu_id}/ | (asignar/actualizar) | endpoints_permisos.py | F |
| GET | /api/v1/permisos/roles/{rol_id}/permisos/ | (listar permisos rol) | endpoints_permisos.py | F |
| GET | /api/v1/permisos/roles/{rol_id}/menus/{menu_id}/ | (detalle) | endpoints_permisos.py | F |
| DELETE | /api/v1/permisos/roles/{rol_id}/menus/{menu_id}/ | (revocar) | endpoints_permisos.py | F |

---

### 2.8 Módulo: Menus (legacy) y Áreas

Prefijos: `/api/v1/menus`, `/api/v1/areas`. Solo `require_admin`, sin permiso RBAC por código.

| Método | Ruta | Función | Archivo fuente | Motivo |
|--------|------|---------|----------------|--------|
| GET | /api/v1/menus/getmenu/ | (getmenu) | endpoints.py | F |
| GET | /api/v1/menus/all-structured/ | (all-structured) | endpoints.py | F |
| POST | /api/v1/menus/ | (create) | endpoints.py | F |
| GET | /api/v1/menus/{id}/ | (detail) | endpoints.py | F |
| PUT | /api/v1/menus/{id}/ | (update) | endpoints.py | F |
| DELETE | /api/v1/menus/{id}/ | (delete) | endpoints.py | F |
| PUT | /api/v1/menus/{id}/reactivate/ | (reactivate) | endpoints.py | C, F |
| GET | /api/v1/menus/area/{id}/tree/ | (tree) | endpoints.py | F |
| POST | /api/v1/areas/ | (create) | endpoints_areas.py | F |
| GET | /api/v1/areas/ | (list) | endpoints_areas.py | F |
| GET | /api/v1/areas/list/ | (list simple) | endpoints_areas.py | F |
| GET | /api/v1/areas/{id}/ | (detail) | endpoints_areas.py | F |
| PUT | /api/v1/areas/{id}/ | (update) | endpoints_areas.py | F |
| DELETE | /api/v1/areas/{id}/ | (delete) | endpoints_areas.py | F |
| PUT | /api/v1/areas/{id}/reactivate/ | (reactivate) | endpoints_areas.py | C, F |

---

### 2.9 Módulos: PUR, SLS, INVBILL, PRC, WMS, QMS, CRM, POS, MFG (resto), MRP, MPS, MNT, CST, TAX, BDG, PM

Todos los endpoints de estos módulos carecen de decorador de permiso. La estructura es análoga: CRUD por router con path relativo `""` o `"/{id}"`; el prefijo de módulo y de recurso está en `api.py` y en el `endpoints.py` del módulo. Por tanto, el motivo predominante es **D** (router sin metadata de recurso en el archivo que define la ruta). Donde haya subrecursos (detalles, operaciones anidadas) o acciones no CRUD (reactivate, aprobar, etc.) aplican además **A**, **E** o **C**.

**Resumen por módulo (todos los endpoints sin decorador, motivo principal D salvo indicación):**

- **PUR** (proveedores, contactos, productos-proveedor, solicitudes, cotizaciones, ordenes-compra, recepciones): ~28 endpoints.  
- **SLS** (clientes, contactos, direcciones, cotizaciones, pedidos): ~20 endpoints.  
- **INVBILL** (series, comprobantes, comprobantes-detalles): ~12+ endpoints.  
- **PRC** (listas-precio, promociones): ~8+ endpoints.  
- **WMS** (zonas, ubicaciones, stock-ubicacion, tareas): ~16+ endpoints.  
- **QMS** (parametros-calidad, planes-inspeccion, inspecciones, no-conformidades): ~16+ endpoints.  
- **CRM** (campanas, leads, oportunidades, actividades): ~16+ endpoints.  
- **POS** (puntos-venta, turnos-caja, ventas, ventas-detalle): ~16+ endpoints.  
- **MFG** (centros-trabajo, operaciones, listas-materiales, lista-materiales-detalle, rutas-fabricacion, ruta-fabricacion-detalle, orden-produccion-operaciones, consumo-materiales): ~36+ endpoints (ordenes-produccion ya decorado).  
- **MRP** (plan-maestro, necesidades-brutas, explosion-materiales, ordenes-sugeridas): ~16+ endpoints.  
- **MPS** (pronostico-demanda, plan-produccion, plan-produccion-detalle): ~12+ endpoints.  
- **MNT** (activos, planes-mantenimiento, ordenes-trabajo, historial-mantenimiento): ~16+ endpoints.  
- **CST** (tipos-centro-costo, producto-costo): ~8+ endpoints.  
- **TAX** (libros-electronicos): ~4+ endpoints.  
- **BDG** (presupuestos, presupuesto-detalle): ~8+ (E donde hay detalle).  
- **PM** (proyectos): ~4+ endpoints.

**Tenant / Super Admin** (clientes, modulos deprecated, conexiones, superadmin/usuarios, superadmin/auditoria): todos sin `require_permission`; motivo **G** (prefijo o contexto super-admin) o **F** (solo rol/admin).  
**Métricas:** endpoint(s) de monitoreo; **H** (excluido o permiso de sistema).

---

## 3. Motivo técnico por el cual NO puede inferirse automáticamente el permiso

Criterio aplicado: un endpoint “no puede inferirse automáticamente” si **no existe en el código** una regla o metadata que permita a una herramienta genérica derivar de forma segura y única el string `modulo.recurso.accion` (o equivalente) sin conocimiento de negocio ni de convenciones por módulo.

---

## 4. Explicación por categoría y cambio mínimo para automatizar

### A. Recurso ambiguo

**Qué impide la decoración automática:** En un mismo router coexisten rutas de un recurso principal y de un subrecurso (ej. asiento vs detalle de asiento, guía vs detalle de guía). El path literal (`/detalles`, `/{id}/detalles`) no tiene una convención única en el proyecto para asignar recurso (asiento_detalle vs asiento). Un inferidor por “último segmento” o “path completo” puede equivocar el recurso o la acción.

**Cambio mínimo para automatizarla:** Definir una convención estable: por ejemplo “si el path contiene el segmento literal `detalles` (o `detalle`) y hay un `{id}` padre, el recurso es `<recurso_padre>_detalle`”. Documentarla y que la herramienta de decoración la aplique; opcionalmente anotar en el router (o en un registro) el recurso por ruta.

---

### B. Naming inconsistente

**Qué impide la decoración automática:** El proyecto usa en algunos módulos un permiso que no sigue `modulo.recurso.accion` derivado del path. Ejemplo: ORG usa `org.area.leer` para empresa, departamentos, parametros, cargos, sucursales, centros_costo. Un auto-decorador que infiera por path generaría `org.empresa.leer`, `org.departamento.leer`, etc., que no existen en el catálogo y romperían el modelo acordado.

**Cambio mínimo para automatizarla:** Mantener un mapa de excepciones (por módulo o por path): “para prefijo `/org` (o para estos routers) usar siempre recurso `area`”. La herramienta consulta ese mapa antes de generar el código de permiso.

---

### C. Endpoint no-CRUD (acción)

**Qué impide la decoración automática:** Acciones como activar, desactivar, reordenar, duplicar, reactivate, validar-json, preview-aplicacion no se mapean 1:1 con GET/POST/PUT/DELETE. El proyecto ya usa acciones como `administrar` o `actualizar` para varias de ellas. Sin reglas explícitas, no se puede saber qué acción de permiso asignar.

**Cambio mínimo para automatizarla:** Definir un mapeo path→accion (ej. `/activar/`, `/desactivar/`, `/reordenar/`, `/reactivate/` → `administrar` o `actualizar`) o permitir anotar la acción por ruta. Incluir ese mapeo en la configuración de la herramienta de auto-decoración.

---

### D. Router sin metadata de recurso

**Qué impide la decoración automática:** El archivo que define el endpoint (ej. `endpoints_empleados.py`) solo ve path `""` o `"/{empleado_id}"`. El módulo (`hcm`) y el recurso (`empleados`) vienen del `include_router` en `api.py` y en `hcm/presentation/endpoints.py`. Un analizador que solo lee ese archivo no tiene forma de saber el permiso sin resolver el árbol de routers.

**Cambio mínimo para automatizarla:** (1) Construir el grafo de routers (api.py + cada `modules/<mod>/presentation/endpoints.py`) y, para cada handler, resolver el path completo y el prefijo de recurso; o (2) exigir metadata explícita en cada router (ej. variable `RESOURCE_NAME = "empleado"`, `MODULE_TAG = "hcm"`) y que la herramienta la lea. La opción (1) permite no tocar archivos existentes; la (2) requiere un cambio mínimo por router (una constante o decorador con metadata).

---

### E. Múltiples recursos involucrados

**Qué impide la decoración automática:** Una misma ruta o un mismo router maneja dos recursos (ej. guía + detalle de guía, presupuesto + presupuesto_detalle, stock por producto y almacén). No hay una regla única para elegir un solo `recurso` para el permiso.

**Cambio mínimo para automatizarla:** Reglas por patrón de path (ej. “`/detalles` o `/{id}/detalles` → recurso `<padre>_detalle`”) o anotación explícita por ruta indicando el recurso (y opcionalmente la acción) del permiso.

---

### F. Decorador custom no reconocido

**Qué impide la decoración automática:** Algunos endpoints usan solo `require_admin` (RoleChecker) o lógica de rol en lugar de `require_permission(...)`. Para el proceso RBAC que distingue “decorado” por permiso, no cuentan como decorados; además, una herramienta que solo busque `require_permission` no los reconocería como protegidos por RBAC granular.

**Cambio mínimo para automatizarla:** Decidir si esos endpoints deben tener también un permiso RBAC (ej. `admin.permiso_rol_menu.leer`). Si sí, añadir la dependencia `require_permission(...)` además de (o sustituyendo según diseño) el rol. La herramienta podría tener un listado de “rutas que usan solo rol” y proponer un permiso por convención para revisión humana.

---

### G. Prefijo mal estructurado

**Qué impide la decoración automática:** Prefijos como `/superadmin/usuarios`, `/clientes`, `/conexiones`, `/modulos` (deprecated) no siguen el patrón `/api/v1/<modulo>/<recurso>`. El “módulo” o el “recurso” no se obtienen por el primer/segundo segmento de forma uniforme.

**Cambio mínimo para automatizarla:** Mapa de prefijos completos a (modulo, recurso) o a permiso sugerido (ej. `superadmin/usuarios` → `superadmin.usuario.*`). La herramienta usa ese mapa al resolver el path completo.

---

### H. Otro

**Qué impide la decoración automática:** Casos concretos: (1) Omisión manual (ej. POST orden-servicio sin permiso mientras GET/PUT sí lo tienen). (2) Diseño intencional (GET usuario por id y GET roles de usuario: solo auth, autorización por cliente en lógica). (3) Endpoints de sistema (métricas, health) que se excluyen del RBAC de negocio.

**Cambio mínimo para automatizarla:** (1) Añadir el permiso faltante manualmente o incluir la ruta en la herramienta con el permiso correcto. (2) Si se desea homogeneidad, añadir `require_permission` con la misma política que el listado (o documentar que se mantiene la lógica actual). (3) Mantener excepciones en la herramienta para no decorar esas rutas.

---

## 5. Algoritmo lógico uniforme para decoración automática al 100%

Objetivo: que el sistema pueda, en el futuro, decorar automáticamente el 100% de los endpoints con un permiso RBAC correcto y comprobable, sin romper convenciones ni diseño existente.

### 5.1 Fase 1: Resolución de ruta completa

1. **Construir grafo de routers**
   - Entrada: `app/api/v1/api.py` y cada `app/modules/<modulo>/presentation/endpoints.py`.
   - Por cada `include_router(router_x, prefix=P, ...)`, registrar: (router_x, P, módulo si se puede inferir del tag o del prefijo de api.py).
   - Asociar cada `router_x` al archivo fuente donde se define (p. ej. import de `endpoints_empleados` → `endpoints_empleados.py`).

2. **Obtener rutas montadas**
   - Tras cargar la aplicación FastAPI, recorrer las rutas registradas (p. ej. `app.routes`) y para cada ruta anotar: path completo, método HTTP, función handler (y su archivo y nombre de función).
   - Alternativa: simular el montaje con el grafo de (1) y construir path = prefix_api + prefix_modulo + prefix_recurso + path_decorator.

3. **Resultado:** Por cada endpoint, tupla (path_completo, método, handler, archivo, modulo_resuelto, recurso_resuelto).  
   modulo_resuelto = primer segmento del path tras `/api/v1` (o el que corresponda).  
   recurso_resuelto = segundo segmento (o el definido por la convención de subpaths en 5.2).

### 5.2 Fase 2: Reglas de recurso y acción

4. **Recurso**
   - Por defecto: recurso = último segmento literal del path (antes de parámetros) en snake_case, singularizado si es plural estándar.
   - Si el path contiene un segmento de subrecurso (ej. `detalles`, `detalle`) con parámetro padre: recurso = `<recurso_del_prefijo_padre>_detalle` (ej. `asiento_detalle`, `guia_remision_detalle`).
   - Excepciones por mapa: path o prefijo → recurso fijo (ej. todo `/org` → recurso `area`; paths con `producto/{}/almacen/{}` → recurso `stock`).

5. **Acción**
   - Mapeo por defecto: GET → leer, POST → crear, PUT/PATCH → actualizar, DELETE → eliminar.
   - Mapeo por segmento de path: si el path contiene `/activar/`, `/desactivar/`, `/reordenar/`, `/duplicar/`, `/reactivate/`, `/validar-json/`, etc., usar acción definida en configuración (ej. `administrar` o `actualizar`).
   - Excepciones por mapa: (path, método) → acción.

6. **Catálogo**
   - Cargar permisos existentes (modulo.recurso.accion) desde BD o desde un archivo de seed/registro.
   - Validar que el permiso generado exista en el catálogo; si no, marcar para revisión humana o usar permiso por defecto configurado para ese módulo.

### 5.3 Fase 3: Generación e inyección

7. **Generar permiso**
   - Para cada endpoint: permiso = f"{modulo}.{recurso}.{accion}" (en español si el catálogo usa español).
   - Aplicar mapa de excepciones antes de generar.

8. **Inyección**
   - No eliminar ni reordenar dependencias existentes (get_current_active_user, require_admin, etc.).
   - Añadir una dependencia: `Depends(require_permission("<permiso>"))` en el decorator (`dependencies=[...]`) o como parámetro del handler, según convención del archivo/módulo.
   - Si el endpoint ya tiene `require_permission`, no duplicar; opcionalmente verificar que el permiso coincida con el generado.

9. **Exclusiones**
   - Lista de prefijos o paths excluidos: `/auth`, `/health`, `/docs`, `/openapi`, `/sso`, etc. No decorar esos endpoints con permiso RBAC de negocio.

### 5.4 Fase 4: Validación y revisión

10. **Validación**
    - Comprobar que todo permiso inyectado exista en el catálogo.
    - Tests de integración: por ruta, usuario con permiso → 200 (o el código esperado); usuario sin permiso → 403.

11. **Revisión humana**
    - Generar reporte: endpoint, permiso generado, nivel de confianza (ALTO/MEDIO/BAJO según si hubo excepciones o heurísticas). Los de confianza BAJA o que usaron excepciones se revisan manualmente antes de dar por cerrada la decoración.

Con este algoritmo, la decoración automática puede cubrir el 100% de los endpoints que deban tener permiso RBAC, siempre que se mantengan actualizados el grafo de routers, el mapa de excepciones (naming, acciones no CRUD, prefijos especiales) y el catálogo de permisos. Los casos “H” (omisión o diseño intencional) se tratan como excepciones en el mapa o en la lista de exclusión.

---

**Fin del documento.** No se ha modificado ningún archivo del proyecto; solo se ha generado este análisis como base para una futura decoración automática segura.
