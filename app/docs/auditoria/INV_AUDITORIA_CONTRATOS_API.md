# INV — Auditoría Formal de Contratos API

**Fecha:** 2026-06-12  
**Estado:** Auditoría completada — **sin cambios de código**  
**Alcance:** Módulo `INV` (`/api/v1/inv/*`). Excluye `inv-bill`.  
**Fuentes:**
- OpenAPI real (`app.main:app.openapi()` — **65** rutas INV)
- `app/modules/inv/presentation/*.py` (endpoints + schemas)
- `INV_PLAN_CORRECCION.md` §6 (BC-01 a BC-30)
- `INV_PLAN_IMPLEMENTACION_P0.md`
- `INV_AUDITORIA_PERSISTENCIA.md`

**Metodología de consumidores:** Solo referencias **observables dentro de este repositorio backend** (tests HTTP, llamadas a servicios/queries, seeds de menú, bundles RBAC, documentación interna). **No se infieren** consumidores de frontend React, mobile ni integraciones externas.

**Dependencia global:** Todos los endpoints INV requieren `require_erp_session` (router padre en `endpoints.py`).

---

## 1. Resumen ejecutivo

### 1.1 Contrato canónico oficial INV (V4)

| Tipo entidad | Operaciones canónicas | Patrón write |
|--------------|----------------------|--------------|
| **Maestro** (categoría, UM, producto, almacén, tipo mov.) | GET list/detail, POST, PUT, DELETE (soft), POST reactivar | Body con `empresa_id`; `cliente_id` solo sesión |
| **Derivada** (stock) | GET list/detail/coordenadas, GET alertas | **Sin escritura** — mutación solo vía `procesar` movimiento |
| **Transaccional** (movimiento) | GET, GET/POST/PUT `/con-detalle`, POST proceso | Cabecera + `detalles[]` embebidos en create/update |
| **Transaccional** (inventario físico) | GET, GET/POST/PUT `/con-detalle`, POST finalizar/anular/aprobar | Ídem movimiento; aprobar genera movimiento ajuste |
| **Analítica** (kardex) | GET | Solo lectura |
| **Detalle standalone** | GET list/detail bajo filtros | POST/PUT **deprecated** — no usar para escritura |

### 1.2 Hallazgos críticos de contrato

| ID | Hallazgo | Severidad |
|----|----------|-----------|
| **BC-31** (nuevo) | Rutas proceso movimiento montadas en `/inv/{id}/procesar` en lugar de `/inv/movimientos/{id}/procesar` documentado en estándares | **Crítica** — 404 si cliente usa ruta documentada |
| BC-05/06 | POST/PUT stock activos con `deprecated=True` pero sin bloqueo runtime | **Alta** — escritura sobre tabla derivada |
| BC-20/22 | Campos workflow editables en Create/Update movimiento | **Alta** — bypass de transiciones |
| BC-01/02 | POST cabecera sin detalle sigue operativo | **Media** — flujo legacy paralelo |
| BC-30 | Campo `moneda` string legacy coexistiendo con `moneda_id` | **Media** |

### 1.3 Conteo de endpoints

| Estado | Cantidad |
|--------|----------|
| **Canónico** | 50 |
| **Legacy** (cabecera sin detalle) | 4 |
| **Deprecated** (OpenAPI `deprecated=true`) | 6 |
| **Redundante** (GET lista global detalle) | 2 |
| **Anomalía de ruta** (proceso movimiento — funcionalmente canónico) | 3 |
| **Total** | **65** |

---

## 2. Inventario completo de endpoints (65)

Prefijo base: `/api/v1/inv`. Columnas abreviadas en tablas; cada fila cumple los 10 campos solicitados.

**Leyenda estado:** CAN = Canónico · LEG = Legacy · DEP = Deprecated · RED = Redundante · PEL = Potencialmente peligroso · ANO = Anomalía de ruta

**Leyenda consumidores repo:** `—` = ninguno observable · `MENU` = pantalla en seed S010 · `RBAC` = bundle permisos · `SVC` = otro módulo vía servicio (no HTTP) · `TEST` = test unitario/HTTP

---

### 2.1 Categorías (`inv_categoria_producto`)

| # | Ruta | Método | Permiso | Servicio | Request | Response | Consumidores repo | Estado | Riesgo elim. | Recomendación |
|---|------|--------|---------|----------|---------|----------|-------------------|--------|--------------|---------------|
| 1 | `/categorias` | GET | `inv.categoria.leer` | `list_categorias_servicio` | Query: `solo_activos` | `list[CategoriaRead]` | MENU (`/inv/categorias`) | CAN | Bajo | Mantener |
| 2 | `/categorias/{categoria_id}` | GET | `inv.categoria.leer` | `get_categoria_servicio` | — | `CategoriaRead` | — | CAN | Bajo | Mantener |
| 3 | `/categorias` | POST | `inv.categoria.crear` | `create_categoria_servicio` | `CategoriaCreate` | `CategoriaRead` | — | CAN | Medio | Mantener; P0-004 auditoría usuario |
| 4 | `/categorias/{categoria_id}` | PUT | `inv.categoria.actualizar` | `update_categoria_servicio` | `CategoriaUpdate` | `CategoriaRead` | — | CAN | Medio | Mantener |
| 5 | `/categorias/{categoria_id}` | DELETE | `inv.categoria.eliminar` | `update_categoria_servicio` (es_activo=0) | — | 204 | — | CAN | Bajo | Mantener (soft delete V4) |
| 6 | `/categorias/{categoria_id}/reactivar` | POST | `inv.categoria.actualizar` | `update_categoria_servicio` | — | `CategoriaRead` | — | CAN | Bajo | Mantener |

---

### 2.2 Unidades de medida (`inv_unidad_medida`)

| # | Ruta | Método | Permiso | Servicio | Request | Response | Consumidores repo | Estado | Riesgo elim. | Recomendación |
|---|------|--------|---------|----------|---------|----------|-------------------|--------|--------------|---------------|
| 7 | `/unidades-medida` | GET | `inv.unidad_medida.leer` | `list_unidades_medida_servicio` | Query: `solo_activos` | `list[UnidadMedidaRead]` | MENU | CAN | Bajo | Mantener |
| 8 | `/unidades-medida/{unidad_medida_id}` | GET | `inv.unidad_medida.leer` | `get_unidad_medida_servicio` | — | `UnidadMedidaRead` | — | CAN | Bajo | Mantener |
| 9 | `/unidades-medida` | POST | `inv.unidad_medida.crear` | `create_unidad_medida_servicio` | `UnidadMedidaCreate` | `UnidadMedidaRead` | — | CAN | Medio | Mantener |
| 10 | `/unidades-medida/{unidad_medida_id}` | PUT | `inv.unidad_medida.actualizar` | `update_unidad_medida_servicio` | `UnidadMedidaUpdate` | `UnidadMedidaRead` | — | CAN | Medio | Mantener |
| 11 | `/unidades-medida/{unidad_medida_id}` | DELETE | `inv.unidad_medida.eliminar` | `update_unidad_medida_servicio` | — | 204 | — | CAN | Bajo | Mantener |
| 12 | `/unidades-medida/{unidad_medida_id}/reactivar` | POST | `inv.unidad_medida.actualizar` | `update_unidad_medida_servicio` | — | `UnidadMedidaRead` | — | CAN | Bajo | Mantener |

---

### 2.3 Productos (`inv_producto`)

| # | Ruta | Método | Permiso | Servicio | Request | Response | Consumidores repo | Estado | Riesgo elim. | Recomendación |
|---|------|--------|---------|----------|---------|----------|-------------------|--------|--------------|---------------|
| 13 | `/productos` | GET | `inv.producto.leer` | `list_productos_servicio` | Query: filtros | `list[ProductoRead]` | MENU; TEST (`test_force_password_change` whitelist GET) | CAN | Bajo | Mantener |
| 14 | `/productos/{producto_id}` | GET | `inv.producto.leer` | `get_producto_servicio` | — | `ProductoRead` | — | CAN | Bajo | Mantener |
| 15 | `/productos` | POST | `inv.producto.crear` | `create_producto_servicio` | `ProductoCreate` | `ProductoRead` | — | CAN | Alto | Mantener; revisar BC-11 campos E en write futuro |
| 16 | `/productos/{producto_id}` | PUT | `inv.producto.actualizar` | `update_producto_servicio` | `ProductoUpdate` | `ProductoRead` | — | CAN | Alto | Mantener |
| 17 | `/productos/{producto_id}` | DELETE | `inv.producto.eliminar` | `update_producto_servicio` | — | 204 | — | CAN | Bajo | Mantener |
| 18 | `/productos/{producto_id}/reactivar` | POST | `inv.producto.actualizar` | `update_producto_servicio` | — | `ProductoRead` | — | CAN | Bajo | Mantener |

---

### 2.4 Almacenes (`inv_almacen`)

| # | Ruta | Método | Permiso | Servicio | Request | Response | Consumidores repo | Estado | Riesgo elim. | Recomendación |
|---|------|--------|---------|----------|---------|----------|-------------------|--------|--------------|---------------|
| 19 | `/almacenes` | GET | `inv.almacen.leer` | `list_almacenes_servicio` | Query: filtros | `list[AlmacenRead]` | MENU | CAN | Bajo | Mantener |
| 20 | `/almacenes/{almacen_id}` | GET | `inv.almacen.leer` | `get_almacen_servicio` | — | `AlmacenRead` | — | CAN | Bajo | Mantener |
| 21 | `/almacenes` | POST | `inv.almacen.crear` | `create_almacen_servicio` | `AlmacenCreate` | `AlmacenRead` | — | CAN | Medio | Mantener |
| 22 | `/almacenes/{almacen_id}` | PUT | `inv.almacen.actualizar` | `update_almacen_servicio` | `AlmacenUpdate` | `AlmacenRead` | — | CAN | Medio | Mantener |
| 23 | `/almacenes/{almacen_id}` | DELETE | `inv.almacen.eliminar` | `update_almacen_servicio` | — | 204 | — | CAN | Bajo | Mantener |
| 24 | `/almacenes/{almacen_id}/reactivar` | POST | `inv.almacen.actualizar` | `update_almacen_servicio` | — | `AlmacenRead` | — | CAN | Bajo | Mantener |

---

### 2.5 Stock — tabla derivada (`inv_stock`)

| # | Ruta | Método | Permiso | Servicio | Request | Response | Consumidores repo | Estado | Riesgo elim. | Recomendación |
|---|------|--------|---------|----------|---------|----------|-------------------|--------|--------------|---------------|
| 25 | `/stock` | GET | `inv.stock.leer` | `list_stocks_servicio` | Query: producto, almacén | `list[StockRead]` | MENU; RBAC (`user_standard`, `manager_standard`); TEST (`test_inv_company_isolation` servicio) | CAN | Bajo | **Contrato canónico lectura** |
| 26 | `/stock/{stock_id}` | GET | `inv.stock.leer` | `get_stock_servicio` | — | `StockRead` | — | CAN | Bajo | Mantener |
| 27 | `/stock/producto/{producto_id}/almacen/{almacen_id}` | GET | `inv.stock.leer` | `get_stock_by_producto_almacen_servicio` | — | `Optional[StockRead]` | — | CAN | Bajo | Mantener — lookup por coordenadas |
| 28 | `/stock/alertas` | GET | `inv.stock.leer` | `list_stock_alertas_servicio` | Query: almacén | `list[StockRead]` | — | CAN | Bajo | Mantener |
| 29 | `/stock` | POST | `inv.stock.crear` | `create_stock_servicio` | `StockCreate` | `StockRead` | RBAC (`manager_standard`: `inv.stock.actualizar`) | **DEP** · PEL | **Alto** (BC-05) | No eliminar; P0-002 bloqueo runtime; candidato BC-27 |
| 30 | `/stock/{stock_id}` | PUT | `inv.stock.actualizar` | `update_stock_servicio` | `StockUpdate` | `StockRead` | RBAC (`manager_standard`) | **DEP** · PEL | **Alto** (BC-06) | Ídem BC-27 |

---

### 2.6 Tipos de movimiento (`inv_tipo_movimiento`)

| # | Ruta | Método | Permiso | Servicio | Request | Response | Consumidores repo | Estado | Riesgo elim. | Recomendación |
|---|------|--------|---------|----------|---------|----------|-------------------|--------|--------------|---------------|
| 31 | `/tipos-movimiento` | GET | `inv.tipo_movimiento.leer` | `list_tipos_movimiento_servicio` | Query: `solo_activos` | `list[TipoMovimientoRead]` | MENU | CAN | Bajo | Mantener |
| 32 | `/tipos-movimiento/{tipo_movimiento_id}` | GET | `inv.tipo_movimiento.leer` | `get_tipo_movimiento_servicio` | — | `TipoMovimientoRead` | — | CAN | Bajo | Mantener |
| 33 | `/tipos-movimiento` | POST | `inv.tipo_movimiento.crear` | `create_tipo_movimiento_servicio` | `TipoMovimientoCreate` | `TipoMovimientoRead` | — | CAN | Medio | Mantener |
| 34 | `/tipos-movimiento/{tipo_movimiento_id}` | PUT | `inv.tipo_movimiento.actualizar` | `update_tipo_movimiento_servicio` | `TipoMovimientoUpdate` | `TipoMovimientoRead` | — | CAN | Medio | Mantener |
| 35 | `/tipos-movimiento/{tipo_movimiento_id}` | DELETE | `inv.tipo_movimiento.eliminar` | `update_tipo_movimiento_servicio` | — | 204 | — | CAN | Bajo | Mantener |
| 36 | `/tipos-movimiento/{tipo_movimiento_id}/reactivar` | POST | `inv.tipo_movimiento.actualizar` | `update_tipo_movimiento_servicio` | — | `TipoMovimientoRead` | — | CAN | Bajo | Mantener |

---

### 2.7 Movimientos — cabecera (`inv_movimiento` + `inv_movimiento_detalle`)

| # | Ruta | Método | Permiso | Servicio | Request | Response | Consumidores repo | Estado | Riesgo elim. | Recomendación |
|---|------|--------|---------|----------|---------|----------|-------------------|--------|--------------|---------------|
| 37 | `/movimientos` | GET | `inv.movimiento.leer` | `list_movimientos_servicio` | Query: filtros | `list[MovimientoRead]` | MENU; RBAC | CAN | Bajo | Mantener |
| 38 | `/movimientos/{movimiento_id}` | GET | `inv.movimiento.leer` | `get_movimiento_servicio` | — | `MovimientoRead` | — | CAN | Bajo | Mantener |
| 39 | `/movimientos` | POST | `inv.movimiento.crear` | `create_movimiento_servicio` | `MovimientoCreate` | `MovimientoRead` | — | **LEG** (BC-01) | Medio | Mantener transitorio; preferir `/con-detalle`; candidato BC-29 |
| 40 | `/movimientos/{movimiento_id}` | PUT | `inv.movimiento.actualizar` | `update_movimiento_servicio` | `MovimientoUpdate` | `MovimientoRead` | — | LEG | Medio | Solo borrador; preferir `/con-detalle` |
| 41 | `/movimientos/{movimiento_id}/con-detalle` | GET | `inv.movimiento.leer` | `get_movimiento_con_detalles_servicio` | — | `MovimientoConDetalleRead` | — | **CAN** | Bajo | **Read canónico transaccional** |
| 42 | `/movimientos/con-detalle` | POST | `inv.movimiento.crear` | `create_movimiento_con_detalles_servicio` | `MovimientoConDetalleCreate` | `MovimientoConDetalleRead` | — | **CAN** | Medio | **Write canónico** — mín. 1 línea |
| 43 | `/movimientos/{movimiento_id}/con-detalle` | PUT | `inv.movimiento.actualizar` | `update_movimiento_con_detalles_servicio` | `MovimientoConDetalleUpdate` | `MovimientoConDetalleRead` | — | **CAN** | Medio | **Update canónico** borrador |

---

### 2.8 Movimientos — proceso (anomalía de montaje de router)

> **BC-31:** Router `endpoints_movimientos_proceso.py` montado **sin prefix** en `endpoints.py`. Rutas reales ≠ documentación estándar (`ERP_BACKEND_STANDARDS_V4.md`, `AUDITORIA_INV.md`).

| # | Ruta real OpenAPI | Ruta documentada (incorrecta) | Método | Permiso | Servicio | Request | Response | Consumidores repo | Estado | Riesgo elim. | Recomendación |
|---|-------------------|-------------------------------|--------|---------|----------|---------|----------|-------------------|--------|--------------|---------------|
| 44 | `/inv/{movimiento_id}/procesar` | `/inv/movimientos/{id}/procesar` | POST | `inv.movimiento.procesar` | `procesar_movimiento_servicio` | — | `MovimientoRead` | SVC (`pur/recepcion_service`, `inventario_fisico_aprobacion_service` vía servicio, no HTTP); TEST | **ANO** · PEL | **Crítico** | **Corregir montaje router** a prefix `/movimientos` sin eliminar rutas actuales hasta migración |
| 45 | `/inv/{movimiento_id}/autorizar` | `/inv/movimientos/{id}/autorizar` | POST | `inv.movimiento.autorizar` | `autorizar_movimiento_servicio` | — | `MovimientoRead` | — | **ANO** | Alto | Ídem BC-31 |
| 46 | `/inv/{movimiento_id}/anular` | `/inv/movimientos/{id}/anular` | POST | `inv.movimiento.anular` | `anular_movimiento_servicio` | `MotivoAnulacion` | `MovimientoRead` | — | **ANO** | Medio | Ídem BC-31 |

---

### 2.9 Movimientos — detalle standalone (`inv_movimiento_detalle`)

| # | Ruta | Método | Permiso | Servicio | Request | Response | Consumidores repo | Estado | Riesgo elim. | Recomendación |
|---|------|--------|---------|----------|---------|----------|-------------------|--------|--------------|---------------|
| 47 | `/movimientos-detalle` | GET | `inv.movimiento.leer` | `list_movimientos_detalle_servicio` | Query: movimiento, producto | `list[MovimientoDetalleRead]` | — | **RED** (BC-03) | Bajo | Mantener lectura; preferir GET `/con-detalle` |
| 48 | `/movimientos-detalle/{movimiento_detalle_id}` | GET | `inv.movimiento.leer` | `get_movimiento_detalle_servicio` | — | `MovimientoDetalleRead` | — | CAN | Bajo | Mantener |
| 49 | `/movimientos-detalle` | POST | `inv.movimiento.crear` | `create_movimiento_detalle_servicio` | `MovimientoDetalleCreate` | `MovimientoDetalleRead` | TEST (`test_inv_company_isolation` servicio) | **DEP** (BC-07) | Medio | No eliminar; candidato BC-28 |
| 50 | `/movimientos-detalle/{movimiento_detalle_id}` | PUT | `inv.movimiento.actualizar` | `update_movimiento_detalle_servicio` | `MovimientoDetalleUpdate` | `MovimientoDetalleRead` | — | **DEP** (BC-08) | Medio | Ídem BC-28 |

---

### 2.10 Inventario físico — cabecera (`inv_inventario_fisico` + detalle)

| # | Ruta | Método | Permiso | Servicio | Request | Response | Consumidores repo | Estado | Riesgo elim. | Recomendación |
|---|------|--------|---------|----------|---------|----------|-------------------|--------|--------------|---------------|
| 51 | `/inventario-fisico` | GET | `inv.inventario_fisico.leer` | `list_inventarios_fisicos_servicio` | Query: filtros | `list[InventarioFisicoRead]` | MENU | CAN | Bajo | Mantener |
| 52 | `/inventario-fisico/{inventario_fisico_id}` | GET | `inv.inventario_fisico.leer` | `get_inventario_fisico_servicio` | — | `InventarioFisicoRead` | — | CAN | Bajo | Mantener |
| 53 | `/inventario-fisico` | POST | `inv.inventario_fisico.crear` | `create_inventario_fisico_servicio` | `InventarioFisicoCreate` | `InventarioFisicoRead` | — | **LEG** (BC-02) | Bajo | Preferir `/con-detalle` |
| 54 | `/inventario-fisico/{inventario_fisico_id}` | PUT | `inv.inventario_fisico.actualizar` | `update_inventario_fisico_servicio` | `InventarioFisicoUpdate` | `InventarioFisicoRead` | — | LEG | Medio | Preferir `/con-detalle` |
| 55 | `/inventario-fisico/{inventario_fisico_id}/con-detalle` | GET | `inv.inventario_fisico.leer` | `get_inventario_fisico_con_detalles_servicio` | — | `InventarioFisicoConDetalleRead` | — | **CAN** | Bajo | Read canónico |
| 56 | `/inventario-fisico/con-detalle` | POST | `inv.inventario_fisico.crear` | `create_inventario_fisico_con_detalles_servicio` | `InventarioFisicoConDetalleCreate` | `InventarioFisicoConDetalleRead` | — | **CAN** | Medio | Write canónico |
| 57 | `/inventario-fisico/{inventario_fisico_id}/con-detalle` | PUT | `inv.inventario_fisico.actualizar` | `update_inventario_fisico_con_detalles_servicio` | `InventarioFisicoConDetalleUpdate` | `InventarioFisicoConDetalleRead` | TEST (`test_inventario_fisico_update_con_detalle` servicio) | **CAN** | Medio | Update canónico |
| 58 | `/inventario-fisico/{inventario_fisico_id}/finalizar` | POST | `inv.inventario_fisico.finalizar` | `finalizar_inventario_fisico_servicio` | — | `InventarioFisicoRead` | TEST (`test_inventario_fisico_finalizar_f4` servicio) | **CAN** | Medio | Mantener — transición workflow |
| 59 | `/inventario-fisico/{inventario_fisico_id}/anular` | POST | `inv.inventario_fisico.anular` | `anular_inventario_fisico_servicio` | — | `InventarioFisicoRead` | — | **CAN** | Medio | Mantener |
| 60 | `/inventario-fisico/{inventario_fisico_id}/aprobar` | POST | `inv.inventario_fisico.aprobar` | `aprobar_inventario_fisico_servicio` | `AprobarInventarioFisicoRequest` | `InventarioFisicoRead` | TEST (`test_inventario_fisico_aprobacion` servicio) | **CAN** | Alto | Mantener — genera movimiento + procesa |

Inventario físico: 10 endpoints (#51–60). **Total verificado OpenAPI: 65 rutas.**

---

### 2.11 Inventario físico — detalle standalone

| # | Ruta | Método | Permiso | Servicio | Request | Response | Consumidores repo | Estado | Riesgo elim. | Recomendación |
|---|------|--------|---------|----------|---------|----------|-------------------|--------|--------------|---------------|
| — | `/inventario-fisico-detalle` | GET | `inv.inventario_fisico.leer` | `list_inventarios_fisicos_detalle_servicio` | Query | `list[InventarioFisicoDetalleRead]` | — | **RED** (BC-04) | Bajo | Mantener lectura |
| — | `/inventario-fisico-detalle/{id}` | GET | `inv.inventario_fisico.leer` | `get_inventario_fisico_detalle_servicio` | — | `InventarioFisicoDetalleRead` | — | CAN | Bajo | Mantener |
| — | `/inventario-fisico-detalle` | POST | `inv.inventario_fisico.crear` | `create_inventario_fisico_detalle_servicio` | `InventarioFisicoDetalleCreate` | `InventarioFisicoDetalleRead` | — | **DEP** (BC-09) | Medio | BC-28 |
| — | `/inventario-fisico-detalle/{id}` | PUT | `inv.inventario_fisico.actualizar` | `update_inventario_fisico_detalle_servicio` | `InventarioFisicoDetalleUpdate` | `InventarioFisicoDetalleRead` | — | **DEP** (BC-10) | Medio | BC-28 |

---

### 2.12 Kardex (vista analítica)

| # | Ruta | Método | Permiso | Servicio | Request | Response | Consumidores repo | Estado | Riesgo elim. | Recomendación |
|---|------|--------|---------|----------|---------|----------|-------------------|--------|--------------|---------------|
| — | `/kardex` | GET | `inv.movimiento.leer` | `list_kardex_servicio` | Query: producto, almacén, fechas | `list[KardexLineaRead]` | MENU | **CAN** | Bajo | Mantener — solo lectura derivada |

---

## 3. Inventario completo de schemas

### 3.1 Schemas públicos (archivos)

| Archivo | Schemas |
|---------|---------|
| `schemas.py` | Maestros Read/Create/Update; transaccionales; embebidos; `KardexLineaRead` |
| `schemas_proceso.py` | `MotivoAnulacion`, `AprobarInventarioFisicoRequest` |

### 3.2 Catálogo por entidad

| Schema | Tipo | Uso en endpoints |
|--------|------|------------------|
| `CategoriaCreate/Update/Read` | Maestro | `/categorias` |
| `UnidadMedidaCreate/Update/Read` | Maestro | `/unidades-medida` |
| `ProductoCreate/Update/Read` | Maestro | `/productos` |
| `AlmacenCreate/Update/Read` | Maestro | `/almacenes` |
| `StockCreate/Update/Read` | Derivada | `/stock` (Create/Update solo deprecated) |
| `TipoMovimientoCreate/Update/Read` | Maestro | `/tipos-movimiento` |
| `MovimientoCreate/Update/Read` | Transaccional | `/movimientos` legacy |
| `MovimientoConDetalleCreate/Update/Read` | Transaccional **canónico** | `/movimientos/con-detalle` |
| `MovimientoDetalleCreate/Update/Read` | Detalle | standalone deprecated + embebido en Read |
| `MovimientoDetalleCreateEmbebido` | Embebido write | dentro de `MovimientoConDetalle*` |
| `InventarioFisicoCreate/Update/Read` | Transaccional | legacy cabecera |
| `InventarioFisicoConDetalleCreate/Update/Read` | Transaccional **canónico** | `/inventario-fisico/con-detalle` |
| `InventarioFisicoDetalleCreate/Update/Read` | Detalle | standalone deprecated |
| `InventarioFisicoDetalleCreateEmbebido` | Embebido write | dentro de `InventarioFisicoConDetalle*` |
| `KardexLineaRead` | Analítica | `/kardex` |
| `MotivoAnulacion` | Proceso | `POST /{id}/anular` |
| `AprobarInventarioFisicoRequest` | Proceso | `POST .../aprobar` |

---

## 4. Auditoría de schemas — campos por clasificación

### 4.1 `CategoriaCreate` / `CategoriaUpdate` / `CategoriaRead`

| Clasificación | Campos |
|---------------|--------|
| **Write** | `empresa_id`, `codigo`, `nombre`, `descripcion`, `categoria_padre_id`, `nivel`, `ruta_jerarquica`, `cuenta_contable_*`, `metodo_costeo_defecto`, `es_activo` |
| **Readonly (deberían)** | `nivel`, `ruta_jerarquica` (C — derivables de padre) |
| **Derivados (C)** | — en Read: ninguno computado BD |
| **Auditoría (B)** | Read: `fecha_creacion`, `fecha_actualizacion`, `usuario_creacion_id` (vacío hoy) |
| **E futuro** | `cuenta_contable_*` → FIN; `metodo_costeo_defecto` → CST |
| **Sobreexpuestos** | Contabilidad y costeo editables sin módulo consumidor en repo |

### 4.2 `UnidadMedidaCreate/Update/Read`

| Clasificación | Campos |
|---------------|--------|
| **Write** | `empresa_id`, `codigo`, `nombre`, `simbolo`, `tipo_unidad`, `es_unidad_base`, `factor_conversion_base`, `decimales_permitidos`, `es_activo` |
| **Readonly** | — |
| **Auditoría** | Read: `fecha_*`, `usuario_creacion_id` |
| **E** | — |
| **Sobreexpuestos** | Ninguno significativo |

### 4.3 `ProductoCreate/Update/Read` (BC-11)

| Clasificación | Campos |
|---------------|--------|
| **Write core INV** | `empresa_id`, identificadores (`codigo_sku`, códigos), `nombre*`, `categoria_id`, `tipo_producto`, UM IDs, flags inventario (`maneja_*`), `stock_minimo/maximo/punto_reorden`, `es_activo`, `observaciones` |
| **Write E — PUR** | `es_comprable`, `tiempo_entrega_dias`, `cantidad_minima_compra`, `multiplo_compra`, `proveedor_habitual_id`, `costo_ultima_compra`, `unidad_medida_compra_id`, `factor_conversion_compra` |
| **Write E — SLS** | `es_vendible`, `requiere_autorizacion_venta`, `precio_base_venta`, `moneda_venta`, `unidad_medida_venta_id`, `factor_conversion_venta` |
| **Write E — MFG** | `es_fabricable`, `tiene_lista_materiales` |
| **Write E — CST** | `metodo_costeo`, `costo_estandar`, `costo_promedio`, `moneda_costo` |
| **Write E — TAX** | `afecto_igv`, `porcentaje_igv`, `codigo_sunat`, `tipo_afectacion_igv` |
| **Write E — WMS/logística** | `peso_*`, `volumen_*`, dimensiones, `color`, `talla` |
| **Readonly (deberían)** | `costo_promedio`, `costo_ultima_compra` (derivados de movimientos PUR) |
| **Auditoría** | Read: `usuario_creacion_id`, `usuario_actualizacion_id`, `fecha_*` |
| **Sobreexpuestos** | ~30 campos E editables sin consumidor HTTP en repo |

### 4.4 `AlmacenCreate/Update/Read`

| Clasificación | Campos |
|---------------|--------|
| **Write** | `empresa_id`, `sucursal_id`, datos almacén, capacidades, flags operación, `centro_costo_id` |
| **Readonly** | — |
| **E** | `sucursal_id` → ORG; `centro_costo_id` → FIN/CST; `permite_*` → PUR/SLS/MFG |
| **Auditoría** | Read: `usuario_creacion_id`, `fecha_*` |

### 4.5 `StockCreate/Update/Read` (BC-12)

| Clasificación | Campos |
|---------------|--------|
| **Write (deprecated)** | `cantidad_actual`, `cantidad_reservada`, `cantidad_transito`, `costo_promedio`, `moneda_id`, umbrales, `ubicacion_almacen`, fechas último movimiento/compra/venta |
| **Readonly (deberían en Write)** | **Todos** — tabla derivada |
| **Derivados Read (C)** | `cantidad_disponible`, `valor_total` |
| **E** | `cantidad_reservada` → SLS/MFG; `cantidad_transito` → PUR; `fecha_ultima_compra/venta` → PUR/SLS |
| **Sobreexpuestos** | Schema Write completo para tabla que no debe mutarse por API |

### 4.6 `TipoMovimientoCreate/Update/Read`

| Clasificación | Campos |
|---------------|--------|
| **Write** | `empresa_id`, `codigo`, `nombre`, `clase_movimiento`, flags proceso, cuentas contables, referencia documento |
| **E** | `genera_asiento_contable`, `cuenta_contable_*` → FIN |
| **Auditoría** | Read: `usuario_creacion_id` |

### 4.7 `MovimientoCreate/Update/Read` y `MovimientoConDetalle*` (BC-14, BC-17, BC-20, BC-22, BC-30)

| Clasificación | Campos |
|---------------|--------|
| **Write negocio** | `empresa_id`, `numero_movimiento`, `tipo_movimiento_id`, fechas, almacenes, referencias documento/tercero, `observaciones`, `centro_costo_id`, `moneda_id` |
| **Write legacy** | `moneda` (string) — BC-30 |
| **Readonly (deberían)** | `total_items`, `total_cantidad`, `total_costo` (BC-17); `estado` (BC-20); `autorizado_por_usuario_id`, `fecha_autorizacion` (BC-22); `motivo_anulacion` (solo anular) |
| **Readonly response** | `fecha_procesado`, `usuario_procesado_id`, `cliente_id`, `movimiento_id` |
| **Auditoría** | `usuario_creacion_id` (vacío); `fecha_creacion/actualizacion` |
| **Embebido canónico** | `detalles[]` → `MovimientoDetalleCreateEmbebido` |

### 4.8 `MovimientoDetalleCreate/Update/Read` (BC-15)

| Clasificación | Campos |
|---------------|--------|
| **Write standalone (deprecated)** | `empresa_id`, `movimiento_id` + línea |
| **Write embebido** | Sin `movimiento_id`/`empresa_id` en embebido |
| **Derivados Read** | `costo_total` (C — BC-26) |
| **Legacy** | `moneda` string en Create |

### 4.9 `InventarioFisicoCreate/Update/Read` y `InventarioFisicoConDetalle*` (BC-13, BC-18, BC-19, BC-21)

| Clasificación | Campos |
|---------------|--------|
| **Write negocio** | `empresa_id`, `numero_inventario`, `fecha_inventario`, `almacen_id`, `tipo_inventario`, `descripcion`, `categoria_id`, `ubicacion_almacen`, supervisor, `observaciones` |
| **Readonly (deberían)** | `total_productos_contados`, `total_diferencias`, `valor_diferencias` (BC-18); `movimiento_ajuste_id` (BC-19); `estado` (BC-20); `fecha_finalizacion`, `fecha_ajuste` (BC-21) |
| **Derivados Read (detalle)** | `diferencia`, `valor_diferencia` |
| **Auditoría** | `usuario_creacion_id` |

### 4.10 `KardexLineaRead`

| Clasificación | Campos |
|---------------|--------|
| **Solo Read** | Proyección de `inv_movimiento` + `inv_movimiento_detalle` |
| **Legacy en Read** | `moneda` string (no `moneda_id`) |

### 4.11 `MotivoAnulacion` / `AprobarInventarioFisicoRequest`

| Schema | Write | Notas |
|--------|-------|-------|
| `MotivoAnulacion` | `motivo` opcional | Proceso anular movimiento |
| `AprobarInventarioFisicoRequest` | `tipo_movimiento_id` requerido, `observaciones` | Proceso aprobar IF |

---

## 5. Matriz endpoint → servicio → tabla

| Endpoint (representativo) | Servicio | Tabla(s) principal(es) |
|---------------------------|----------|------------------------|
| CRUD `/categorias` | `categoria_service.*` | `inv_categoria_producto` |
| CRUD `/unidades-medida` | `unidad_medida_service.*` | `inv_unidad_medida` |
| CRUD `/productos` | `producto_service.*` | `inv_producto` |
| CRUD `/almacenes` | `almacen_service.*` | `inv_almacen` |
| GET `/stock*` | `stock_service.*` | `inv_stock` |
| POST/PUT `/stock` | `stock_service.create/update` | `inv_stock` |
| GET `/stock/alertas` | `stock_service.list_stock_alertas` | `inv_stock` (+ cálculo disponible) |
| CRUD `/tipos-movimiento` | `tipo_movimiento_service.*` | `inv_tipo_movimiento` |
| `/movimientos` CRUD | `movimiento_service.*` | `inv_movimiento` |
| `/movimientos/con-detalle` | `movimiento_service.create/update_con_detalles` | `inv_movimiento` + `inv_movimiento_detalle` |
| `/inv/{id}/procesar` | `movimiento_proceso_service.procesar` | `inv_movimiento`, `inv_movimiento_detalle`, **`inv_stock`** |
| `/inv/{id}/autorizar` | `movimiento_proceso_service.autorizar` | `inv_movimiento` |
| `/inv/{id}/anular` | `movimiento_proceso_service.anular` | `inv_movimiento` |
| `/movimientos-detalle` | `movimiento_detalle_service.*` | `inv_movimiento_detalle` |
| `/inventario-fisico` CRUD | `inventario_fisico_service.*` | `inv_inventario_fisico` |
| `/inventario-fisico/con-detalle` | `inventario_fisico_service.*_con_detalles` | `inv_inventario_fisico` + `inv_inventario_fisico_detalle` |
| `.../finalizar` | `finalizar_inventario_fisico_servicio` | `inv_inventario_fisico` |
| `.../anular` | `anular_inventario_fisico_servicio` | `inv_inventario_fisico` |
| `.../aprobar` | `inventario_fisico_aprobacion_service.aprobar` | `inv_inventario_fisico`, `inv_inventario_fisico_detalle`, `inv_movimiento`, `inv_movimiento_detalle`, **`inv_stock`** |
| `/inventario-fisico-detalle` | `inventario_fisico_detalle_service.*` | `inv_inventario_fisico_detalle` |
| `/kardex` | `kardex_service.list_kardex` | `inv_movimiento` JOIN `inv_movimiento_detalle` (lectura) |

---

## 6. Matriz endpoint → consumidores observables (solo repo backend)

| Endpoint / Grupo | HTTP test | Servicio interno | Seed menú | RBAC bundle | Docs internas |
|------------------|-----------|------------------|-----------|-------------|---------------|
| GET `/productos` | `test_force_password_change` | — | S010 INV_PRODUCTOS | `user_standard` (no producto) | MANAGER_STANDARD_BUNDLE |
| GET `/stock` | — | — | S010 INV_STOCK | `user_standard`, `manager_standard` | — |
| POST/PUT `/stock` | — | — | — | `manager_standard` (`inv.stock.actualizar`) | ERP_STANDARDS (deprecated) |
| `/movimientos/con-detalle` | — | — | S010 INV_MOVIMIENTOS | `manager_standard` (movimiento.*) | ERP_STANDARDS |
| POST `/inv/{id}/procesar` | — | **PUR** `recepcion_service`; **IF** `aprobacion_service` | — | `manager_standard` | AUDITORIA_INV (ruta incorrecta) |
| `/inventario-fisico/.../aprobar` | — | TEST aprobacion (servicio) | S010 INV_INV_FISICO | — | — |
| `/inventario-fisico/.../finalizar` | — | TEST finalizar (servicio) | — | — | — |
| PUT `.../con-detalle` IF | — | TEST update (servicio) | — | — | — |
| POST `/movimientos-detalle` | — | TEST company isolation (servicio) | — | — | — |
| Demás maestros GET | — | — | S010 (cada pantalla) | Parcial | — |
| **Sin consumidor observable** | Mayoría POST/PUT maestros, legacy cabecera, detalle deprecated GET global, kardex, alertas, proceso HTTP | — | — | — | — |

**Conclusión consumidores:** En este repositorio **no hay cliente HTTP** que invoque la mayoría de endpoints de escritura INV. Los únicos usos productivos observables son **llamadas servicio→servicio** (PUR recepción, IF aprobación) que **bypasean** la capa HTTP. Los seeds de menú implican pantallas futuras/presentes pero **no constituyen consumo API verificable**.

---

## 7. Resolución backlog BC-01 a BC-30 (+ BC-31)

| ID | Estado auditoría | Consumidores repo | Decisión |
|----|------------------|-------------------|----------|
| BC-01 | Confirmado LEG | Ninguno HTTP | Mantener; marcar no canónico; BC-29 futuro |
| BC-02 | Confirmado LEG | Ninguno | Mantener; preferir con-detalle |
| BC-03 | Confirmado RED | Ninguno | Mantener GET; documentar alternativa |
| BC-04 | Confirmado RED | Ninguno | Ídem |
| BC-05 | Confirmado DEP+PEL | RBAC manager tiene permiso | No eliminar; P0-002 bloqueo |
| BC-06 | Confirmado DEP+PEL | RBAC manager | Ídem BC-27 |
| BC-07–10 | Confirmado DEP | TEST solo servicio detalle | BC-28 futuro |
| BC-11 | Confirmado | Ninguno HTTP | Mantener schema; grupos readonly futuros |
| BC-12 | Confirmado | RBAC implica uso potencial | Solo Read canónico a largo plazo |
| BC-13–15 | Confirmado | Ninguno | Restricción readonly en evolución contrato |
| BC-16 | OK | — | Correcto — no exponer `cliente_id` |
| BC-17–23 | Confirmado | Ninguno | Candidatos readonly; ver matriz §8 |
| BC-24–26 | Confirmado gap | — | P0-004 / datos BD |
| BC-27–30 | Pendiente condición | Sin evidencia HTTP en repo | No deprecar más hasta inventario FE |
| **BC-31** | **Nuevo — crítico** | Docs internas usan ruta incorrecta | Remontar router bajo `/movimientos` con alias temporal |

---

## 8. Matriz de riesgo de breaking changes

| Cambio propuesto | Endpoints afectados | Probabilidad impacto | Severidad | Mitigación |
|------------------|---------------------|----------------------|-----------|------------|
| Eliminar POST `/stock` | BC-05 | Desconocida (FE no en repo) | Alta | 410 tras telemetría; flag P0-002 primero |
| Eliminar POST cabecera movimiento | BC-01, BC-29 | Media | Media | Deprecar OpenAPI antes; mantener con-detalle |
| Mover `/inv/{id}/procesar` → `/movimientos/{id}/procesar` | BC-31 | Alta si FE usa ruta real actual | Alta | Publicar ambas rutas temporalmente |
| Restringir `estado` en Write | BC-20 | Baja en repo | Alta | Validación servidor sin quitar campo aún |
| Quitar `moneda` legacy | BC-30 | Desconocida | Media | Período dual `moneda` + `moneda_id` |
| Split `ProductoCreate` | BC-11 | Baja | Media | Versionado schema o campos opcionales |
| Readonly totales movimiento | BC-17 | Baja | Baja | Servidor ya recalcula en con-detalle |
| Eliminar POST detalle standalone | BC-07–10 | Baja (TEST usa servicio) | Media | BC-28 tras migración |

---

## 9. Lista priorizada — candidatos a deprecated (sin eliminación inmediata)

| Prioridad | Contrato | Justificación | Prerequisito |
|-----------|----------|---------------|--------------|
| **P0** | BC-31 rutas proceso en raíz `/inv/{id}/*` | Anomalía vs estándar; confusión documental | Alias bajo `/movimientos/{id}/*` |
| **P1** | BC-05, BC-06 POST/PUT `/stock` | Tabla derivada; OpenAPI ya deprecated | P0-002 bloqueo runtime |
| **P2** | BC-07–10 POST/PUT detalle standalone | V4 cabecera-detalle | BC-28; inventario FE |
| **P3** | BC-01 POST `/movimientos` cabecera vacía | Flujo incompleto | BC-29 política ≥1 línea |
| **P4** | BC-02 POST `/inventario-fisico` cabecera | Redundante con con-detalle | Migración FE |
| **P5** | BC-30 campo `moneda` string | Legacy duplicado | Migración a `moneda_id` |
| **P6** | BC-03, BC-04 GET detalle global | Redundante no dañino | Opcional; bajo valor |

**No candidatos a deprecated:** Maestros CRUD, GET stock/kardex, con-detalle canónico, workflow IF (finalizar/anular/aprobar), GET detalle por id.

---

## 10. Contratos potencialmente peligrosos — detalle

| Contrato | Riesgo | Mecanismo |
|----------|--------|-----------|
| POST/PUT `/stock` | Desincronización stock vs kardex | Escritura directa sobre derivada |
| `MovimientoCreate.estado` editable | Saltar workflow autorizar/procesar | Body acepta `procesado` teóricamente |
| `MovimientoCreate.autorizado_por_usuario_id` | Falsificación auditoría | Campo en write sin validación sesión |
| Rutas `/inv/{uuid}/procesar` | Colisión semántica con otros recursos UUID en raíz INV | Montaje router incorrecto |
| POST `/movimientos` sin líneas | Movimiento borrador huérfano | Sin detalle no hay impacto stock |
| `InventarioFisicoUpdate.movimiento_ajuste_id` | Enlace manual a movimiento ajeno | Bypass workflow aprobar |

---

## 11. Definición contrato canónico por entidad (oficial post-auditoría)

### 11.1 Producto

```
READ:  GET /productos, GET /productos/{id}  → ProductoRead
WRITE: POST /productos (ProductoCreate), PUT /productos/{id} (ProductoUpdate)
LIFE:  DELETE /productos/{id}, POST /productos/{id}/reactivar
```

### 11.2 Stock (derivada)

```
READ:  GET /stock, GET /stock/{id}, GET /stock/producto/{p}/almacen/{a}, GET /stock/alertas
WRITE: (ninguno público) — mutación vía POST /inv/{movimiento_id}/procesar*
       *Ruta canónica objetivo: POST /movimientos/{id}/procesar (BC-31)
ANTI:  POST/PUT /stock → deprecated, bloquear en P0-002
```

### 11.3 Movimiento (transaccional)

```
READ:  GET /movimientos, GET /movimientos/{id}/con-detalle
WRITE: POST /movimientos/con-detalle, PUT /movimientos/{id}/con-detalle
PROC:  POST /movimientos/{id}/autorizar|procesar|anular  ← objetivo BC-31
       (hoy: POST /inv/{id}/autorizar|procesar|anular)
ANTI:  POST /movimientos (solo cabecera), POST/PUT /movimientos-detalle
```

### 11.4 Inventario físico (transaccional)

```
READ:  GET /inventario-fisico, GET /inventario-fisico/{id}/con-detalle
WRITE: POST /inventario-fisico/con-detalle, PUT /inventario-fisico/{id}/con-detalle
PROC:  POST .../finalizar, POST .../anular, POST .../aprobar (AprobarInventarioFisicoRequest)
ANTI:  POST /inventario-fisico (solo cabecera), POST/PUT /inventario-fisico-detalle
```

### 11.5 Kardex

```
READ:  GET /kardex → list[KardexLineaRead]
WRITE: prohibido
```

---

## 12. Checklist BC §6.7 — resultado

| Ítem | Estado |
|------|--------|
| Inventariar consumo real por endpoint | ✅ Solo repo backend (§6) |
| Validar BC-05, BC-06 sin consumidor HTTP | ✅ Ninguno HTTP; RBAC sí asigna permiso |
| Confirmar flujo cabecera+detalle vs standalone | ✅ Canónico = con-detalle; standalone deprecated |
| Mapear campos Write vs servidor sobrescribe | ✅ §4 por schema |
| Matriz readonly por estado documento | ✅ BC-17–22 documentados |
| Evaluar breaking changes | ✅ §8 |
| Contrato canónico por entidad | ✅ §11 |
| Alinear permisos RBAC proceso | ✅ Código actual usa `procesar/autorizar/anular/aprobar/finalizar` granulares |

---

## 13. Referencias

| Documento | Uso en esta auditoría |
|-----------|----------------------|
| `INV_PLAN_CORRECCION.md` §6 | Backlog BC-01–30 |
| `INV_PLAN_IMPLEMENTACION_P0.md` | Impacto P0-002 stock, P0-003 estorno |
| `INV_AUDITORIA_PERSISTENCIA.md` | Campos B/C/E y gaps Read |
| `ERP_BACKEND_STANDARDS_V4.md` | Patrón V4 cabecera-detalle |
| `app/docs/modulos/AUDITORIA_INV.md` | Referencia histórica (**rutas proceso desactualizadas**) |

---

*Auditoría formal INV completada. El contrato canónico oficial queda definido en §1.1 y §11. Siguiente hito recomendado: corregir BC-31 (montaje router proceso) y ejecutar Fase 0 (`INV_PLAN_IMPLEMENTACION_P0.md`) antes de cualquier eliminación o restricción breaking de contratos.*
