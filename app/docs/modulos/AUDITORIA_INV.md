# AUDITORÍA MÓDULO INV — Inventarios y Almacenes
**Fecha:** 2026-05-13
**Módulo:** INV — Inventarios y Almacenes
**Stack:** FastAPI + SQL Server · Multi-tenant SaaS

---

## DIAGNÓSTICO GENERAL

🟡 **AJUSTES** — El módulo cubre correctamente los 5 maestros (categoría, unidad de medida, producto, almacén, tipo de movimiento) con CRUD completo + reactivar, y tiene implementados los ciclos de vida transaccionales básicos para movimientos e inventario físico. Sin embargo, presenta brechas arquitectónicas que afectan la integridad del diseño ERP SaaS:

1. La creación de movimientos e inventarios físicos no incluye el detalle embebido en el body: el frontend debe hacer llamadas separadas al endpoint de detalle (anti-patrón cabecera+detalle).
2. Los endpoints de ciclo de vida (procesar, autorizar, anular, aprobar) reutilizan el permiso `actualizar` en lugar de permisos granulares propios.
3. La transición `finalizar` del inventario físico (`en_proceso → finalizado`) no tiene endpoint.
4. Dos campos calculados PERSISTED del detalle de inventario físico (`diferencia`, `valor_diferencia`) están ausentes del schema de respuesta.

**Alineación con ERP SaaS:** El módulo cubre 5 de 7 flujos principales (maestros OK, stock consulta OK, kardex OK). Los 2 flujos transaccionales funcionan operativamente pero con el anti-patrón de detalle separado.

---

## TABLAS CRÍTICAS FALTANTES

Ninguna. La BD cubre todos los flujos principales.

---

## ENTIDADES Y CLASIFICACIÓN

| Entidad | Tipo | Tabla BD | Endpoints propios |
|---|---|---|---|
| Categoría de Producto | maestro | `inv_categoria_producto` | ✅ Sí |
| Unidad de Medida | maestro | `inv_unidad_medida` | ✅ Sí |
| Producto | maestro | `inv_producto` | ✅ Sí |
| Almacén | maestro | `inv_almacen` | ✅ Sí |
| Tipo de Movimiento | maestro | `inv_tipo_movimiento` | ✅ Sí |
| Movimiento | transaccional-cabecera | `inv_movimiento` | ✅ Sí |
| Detalle de Movimiento | detalle-embebido | `inv_movimiento_detalle` | ❌ Solo lectura (escritura en cabecera) |
| Inventario Físico | transaccional-cabecera | `inv_inventario_fisico` | ✅ Sí |
| Detalle de Inventario Físico | detalle-embebido | `inv_inventario_fisico_detalle` | ❌ Solo lectura (escritura en cabecera) |
| Stock | derivada | `inv_stock` | ✅ Solo lectura |

---

## ENDPOINTS EXISTENTES

| Ruta | Método | Entidad | Tenant | RBAC | Clasificación | Motivo |
|---|---|---|---|---|---|---|
| `/inv/categorias` | GET | categoria | ✅ | ✅ `inv.categoria.leer` | ✅ CORRECTO | — |
| `/inv/categorias/{id}` | GET | categoria | ✅ | ✅ | ✅ CORRECTO | — |
| `/inv/categorias` | POST | categoria | ✅ | ✅ `inv.categoria.crear` | ✅ CORRECTO | — |
| `/inv/categorias/{id}` | PUT | categoria | ✅ | ✅ `inv.categoria.actualizar` | ✅ CORRECTO | — |
| `/inv/categorias/{id}` | DELETE | categoria | ✅ | ✅ `inv.categoria.eliminar` | ✅ CORRECTO | Baja lógica |
| `/inv/categorias/{id}/reactivar` | POST | categoria | ✅ | ✅ `inv.categoria.actualizar` | ✅ CORRECTO | — |
| `/inv/unidades-medida` | GET | unidad_medida | ✅ | ✅ `inv.unidad_medida.leer` | ✅ CORRECTO | — |
| `/inv/unidades-medida/{id}` | GET | unidad_medida | ✅ | ✅ | ✅ CORRECTO | — |
| `/inv/unidades-medida` | POST | unidad_medida | ✅ | ✅ `inv.unidad_medida.crear` | ✅ CORRECTO | — |
| `/inv/unidades-medida/{id}` | PUT | unidad_medida | ✅ | ✅ `inv.unidad_medida.actualizar` | ✅ CORRECTO | — |
| `/inv/unidades-medida/{id}` | DELETE | unidad_medida | ✅ | ✅ `inv.unidad_medida.eliminar` | ✅ CORRECTO | Baja lógica |
| `/inv/unidades-medida/{id}/reactivar` | POST | unidad_medida | ✅ | ✅ | ✅ CORRECTO | — |
| `/inv/productos` | GET | producto | ✅ | ✅ `inv.producto.leer` | ✅ CORRECTO | — |
| `/inv/productos/{id}` | GET | producto | ✅ | ✅ | ✅ CORRECTO | — |
| `/inv/productos` | POST | producto | ✅ | ✅ `inv.producto.crear` | ✅ CORRECTO | — |
| `/inv/productos/{id}` | PUT | producto | ✅ | ✅ `inv.producto.actualizar` | ✅ CORRECTO | — |
| `/inv/productos/{id}` | DELETE | producto | ✅ | ✅ `inv.producto.eliminar` | ✅ CORRECTO | Baja lógica |
| `/inv/productos/{id}/reactivar` | POST | producto | ✅ | ✅ | ✅ CORRECTO | — |
| `/inv/almacenes` | GET | almacen | ✅ | ✅ `inv.almacen.leer` | ✅ CORRECTO | — |
| `/inv/almacenes/{id}` | GET | almacen | ✅ | ✅ | ✅ CORRECTO | — |
| `/inv/almacenes` | POST | almacen | ✅ | ✅ `inv.almacen.crear` | ✅ CORRECTO | — |
| `/inv/almacenes/{id}` | PUT | almacen | ✅ | ✅ `inv.almacen.actualizar` | ✅ CORRECTO | — |
| `/inv/almacenes/{id}` | DELETE | almacen | ✅ | ✅ `inv.almacen.eliminar` | ✅ CORRECTO | Baja lógica |
| `/inv/almacenes/{id}/reactivar` | POST | almacen | ✅ | ✅ | ✅ CORRECTO | — |
| `/inv/tipos-movimiento` | GET | tipo_movimiento | ✅ | ✅ `inv.tipo_movimiento.leer` | ✅ CORRECTO | — |
| `/inv/tipos-movimiento/{id}` | GET | tipo_movimiento | ✅ | ✅ | ✅ CORRECTO | — |
| `/inv/tipos-movimiento` | POST | tipo_movimiento | ✅ | ✅ `inv.tipo_movimiento.crear` | ✅ CORRECTO | — |
| `/inv/tipos-movimiento/{id}` | PUT | tipo_movimiento | ✅ | ✅ `inv.tipo_movimiento.actualizar` | ✅ CORRECTO | — |
| `/inv/tipos-movimiento/{id}` | DELETE | tipo_movimiento | ✅ | ✅ `inv.tipo_movimiento.eliminar` | ✅ CORRECTO | Baja lógica |
| `/inv/tipos-movimiento/{id}/reactivar` | POST | tipo_movimiento | ✅ | ✅ | ✅ CORRECTO | — |
| `/inv/stock` | GET | stock | ✅ | ✅ `inv.stock.leer` | ✅ CORRECTO | Derivada, solo lectura |
| `/inv/stock/{id}` | GET | stock | ✅ | ✅ | ✅ CORRECTO | — |
| `/inv/stock/producto/{pid}/almacen/{aid}` | GET | stock | ✅ | ✅ | ✅ CORRECTO | Consulta por coordenadas |
| `/inv/stock/alertas` | GET | stock | ✅ | ✅ | ✅ CORRECTO | Stock bajo mínimo |
| `/inv/stock` | POST | stock | ✅ | ✅ | 🔴 DEPRECATED | Ya marcado `deprecated=True`. Escritura directa sobre tabla derivada |
| `/inv/stock/{id}` | PUT | stock | ✅ | ✅ | 🔴 DEPRECATED | Ya marcado `deprecated=True`. Escritura directa sobre tabla derivada |
| `/inv/movimientos` | GET | movimiento | ✅ | ✅ `inv.movimiento.leer` | ✅ CORRECTO | — |
| `/inv/movimientos/{id}` | GET | movimiento | ✅ | ✅ | ✅ CORRECTO | — |
| `/inv/movimientos` | POST | movimiento | ✅ | ✅ `inv.movimiento.crear` | ⚠ INCOMPLETO | Crea solo la cabecera. Falta `detalles: List[MovimientoDetalleCreate]` embebido en el body |
| `/inv/movimientos/{id}` | PUT | movimiento | ✅ | ✅ `inv.movimiento.actualizar` | ✅ CORRECTO | Service valida `estado == borrador` |
| `/inv/movimientos/{id}/procesar` | POST | movimiento | ✅ | ❌ usa `inv.movimiento.actualizar` | ⚠ INCOMPLETO | RBAC incorrecto: debería ser `inv.movimiento.procesar` |
| `/inv/movimientos/{id}/autorizar` | POST | movimiento | ✅ | ❌ usa `inv.movimiento.actualizar` | ⚠ INCOMPLETO | RBAC incorrecto: debería ser `inv.movimiento.autorizar` |
| `/inv/movimientos/{id}/anular` | POST | movimiento | ✅ | ❌ usa `inv.movimiento.actualizar` | ⚠ INCOMPLETO | RBAC incorrecto: debería ser `inv.movimiento.anular` |
| `/inv/movimientos-detalle` | GET | movimiento_detalle | ✅ | ✅ `inv.movimiento.leer` | ✅ CORRECTO | Lectura de líneas: válida para consultas del frontend |
| `/inv/movimientos-detalle/{id}` | GET | movimiento_detalle | ✅ | ✅ | ✅ CORRECTO | — |
| `/inv/movimientos-detalle` | POST | movimiento_detalle | ✅ | ✅ | 🔴 DEPRECATED | Escritura independiente para tabla detalle-embebido. El detalle va en el body de la cabecera |
| `/inv/movimientos-detalle/{id}` | PUT | movimiento_detalle | ✅ | ✅ | 🔴 DEPRECATED | Idem |
| `/inv/inventario-fisico` | GET | inventario_fisico | ✅ | ✅ `inv.inventario_fisico.leer` | ✅ CORRECTO | — |
| `/inv/inventario-fisico/{id}` | GET | inventario_fisico | ✅ | ✅ | ✅ CORRECTO | — |
| `/inv/inventario-fisico` | POST | inventario_fisico | ✅ | ✅ `inv.inventario_fisico.crear` | ⚠ INCOMPLETO | Crea solo la cabecera. Falta `detalles: List[InventarioFisicoDetalleCreate]` embebido |
| `/inv/inventario-fisico/{id}` | PUT | inventario_fisico | ✅ | ✅ `inv.inventario_fisico.actualizar` | ✅ CORRECTO | Service valida estado no sea ajustado/anulado |
| `/inv/inventario-fisico/{id}/anular` | POST | inventario_fisico | ✅ | ❌ usa `inv.inventario_fisico.actualizar` | ⚠ INCOMPLETO | RBAC incorrecto: debería ser `inv.inventario_fisico.anular` |
| `/inv/inventario-fisico/{id}/aprobar` | POST | inventario_fisico | ✅ | ❌ usa `inv.inventario_fisico.actualizar` | ⚠ INCOMPLETO | RBAC incorrecto: debería ser `inv.inventario_fisico.aprobar` |
| `/inv/inventario-fisico-detalle` | GET | inventario_fisico_detalle | ✅ | ✅ `inv.inventario_fisico.leer` | ✅ CORRECTO | Lectura de líneas: válida para consultas |
| `/inv/inventario-fisico-detalle/{id}` | GET | inventario_fisico_detalle | ✅ | ✅ | ✅ CORRECTO | — |
| `/inv/inventario-fisico-detalle` | POST | inventario_fisico_detalle | ✅ | ✅ | 🔴 DEPRECATED | Escritura independiente para tabla detalle-embebido |
| `/inv/inventario-fisico-detalle/{id}` | PUT | inventario_fisico_detalle | ✅ | ✅ | 🔴 DEPRECATED | Idem |
| `/inv/kardex` | GET | kardex | ✅ | ✅ `inv.movimiento.leer` | ✅ CORRECTO | Vista analítica, solo lectura |

**Totales:** ✅ CORRECTO: 34 · ⚠ INCOMPLETO: 7 · 🔴 DEPRECATED: 6

---

## ENDPOINTS A DEPRECAR

Los siguientes 4 endpoints deben marcarse con `deprecated=True` en sus routers. Los otros 2 (`POST /inv/stock` y `PUT /inv/stock/{id}`) ya están marcados correctamente.

| Ruta | Método | Motivo | Reemplaza con |
|---|---|---|---|
| `/inv/movimientos-detalle` | POST | Escritura independiente para tabla detalle-embebido (`inv_movimiento_detalle`). El detalle debe ir embebido en el body del `POST /inv/movimientos` | Nuevo `POST /inv/movimientos` con `detalles` embebidos |
| `/inv/movimientos-detalle/{id}` | PUT | Ídem | Nuevo `PUT /inv/movimientos/{id}` con `detalles` embebidos |
| `/inv/inventario-fisico-detalle` | POST | Escritura independiente para tabla detalle-embebido (`inv_inventario_fisico_detalle`) | Nuevo `POST /inv/inventario-fisico` con `detalles` embebidos |
| `/inv/inventario-fisico-detalle/{id}` | PUT | Ídem | Nuevo `PUT /inv/inventario-fisico/{id}` con `detalles` embebidos |

---

## ENDPOINTS FALTANTES A IMPLEMENTAR

| Ruta sugerida | Método | Entidad | Descripción funcional |
|---|---|---|---|
| `/inv/inventario-fisico/{id}/finalizar` | POST | inventario_fisico | Transición `en_proceso → finalizado`. Cierra el conteo sin generar ajuste todavía. Requiere permiso `inv.inventario_fisico.finalizar` |

**Correcciones RBAC en endpoints existentes (⚠ INCOMPLETO):**

Estos no son endpoints nuevos — son correcciones del permiso usado en endpoints ya existentes:

| Ruta | Permiso actual | Permiso correcto |
|---|---|---|
| `POST /inv/movimientos/{id}/procesar` | `inv.movimiento.actualizar` | `inv.movimiento.procesar` |
| `POST /inv/movimientos/{id}/autorizar` | `inv.movimiento.actualizar` | `inv.movimiento.autorizar` |
| `POST /inv/movimientos/{id}/anular` | `inv.movimiento.actualizar` | `inv.movimiento.anular` |
| `POST /inv/inventario-fisico/{id}/anular` | `inv.inventario_fisico.actualizar` | `inv.inventario_fisico.anular` |
| `POST /inv/inventario-fisico/{id}/aprobar` | `inv.inventario_fisico.actualizar` | `inv.inventario_fisico.aprobar` |

**Nuevos schemas requeridos (Fase 3):**

| Schema | Descripción |
|---|---|
| `MovimientoConDetalleCreate` | `MovimientoCreate` + `detalles: List[MovimientoDetalleCreate]` (obligatorio, mínimo 1 línea) |
| `MovimientoConDetalleUpdate` | `MovimientoUpdate` + `detalles: Optional[List[MovimientoDetalleUpdate]]` |
| `MovimientoConDetalleRead` | `MovimientoRead` + `detalles: List[MovimientoDetalleRead]` |
| `InventarioFisicoConDetalleCreate` | `InventarioFisicoCreate` + `detalles: List[InventarioFisicoDetalleCreate]` |
| `InventarioFisicoConDetalleUpdate` | `InventarioFisicoUpdate` + `detalles: Optional[List[InventarioFisicoDetalleUpdate]]` |
| `InventarioFisicoConDetalleRead` | `InventarioFisicoRead` + `detalles: List[InventarioFisicoDetalleRead]` |

---

## CAMPOS FALTANTES EN SCHEMAS

### `MovimientoDetalleRead` vs `inv_movimiento_detalle`

| Campo | Tipo BD | Prioridad | Acción |
|---|---|---|---|
| `costo_total` | `AS (cantidad * costo_unitario) PERSISTED` | ➕ MENOR | Añadir como `Optional[Decimal]` en `MovimientoDetalleRead`. El frontend puede calcularlo pero conviene recibirlo |

### `InventarioFisicoDetalleRead` vs `inv_inventario_fisico_detalle`

| Campo | Tipo BD | Prioridad | Acción |
|---|---|---|---|
| `diferencia` | `AS (cantidad_contada - cantidad_sistema) PERSISTED` | ⚠ IMPORTANTE | Añadir como `Optional[Decimal]`. El frontend necesita mostrarlas durante el proceso de aprobación |
| `valor_diferencia` | `AS ((cantidad_contada - cantidad_sistema) * costo_unitario) PERSISTED` | ⚠ IMPORTANTE | Añadir como `Optional[Decimal]`. Necesario para el impacto económico del ajuste |

---

## PROBLEMAS DE TENANT O RBAC

| Problema | Archivo | Detalle |
|---|---|---|
| RBAC coarse en `procesar` | `endpoints_movimientos_proceso.py` línea 27 | Usa `inv.movimiento.actualizar`. No permite diferenciar quién puede actualizar datos vs quién puede disparar el proceso de stock |
| RBAC coarse en `autorizar` | `endpoints_movimientos_proceso.py` línea 51 | Usa `inv.movimiento.actualizar`. La autorización debería ser un permiso diferenciado |
| RBAC coarse en `anular` (movimiento) | `endpoints_movimientos_proceso.py` línea 75 | Usa `inv.movimiento.actualizar`. Anular es una acción destructiva que requiere control separado |
| RBAC coarse en `anular` (inv. físico) | `endpoints_inventario_fisico.py` línea 98 | Usa `inv.inventario_fisico.actualizar` |
| RBAC coarse en `aprobar` (inv. físico) | `endpoints_inventario_fisico_aprobar.py` línea 29 | Usa `inv.inventario_fisico.actualizar`. Aprobar genera movimiento de ajuste y afecta stock: requiere permiso propio |

---

## SEEDS RBAC FALTANTES

Los siguientes permisos deben añadirse a la tabla de permisos (seed SQL):

| Permiso | Recurso | Acción | Módulo | Descripción |
|---|---|---|---|---|
| `inv.movimiento.procesar` | movimiento | procesar | INV | Permite procesar un movimiento y aplicar el impacto en stock |
| `inv.movimiento.autorizar` | movimiento | autorizar | INV | Permite autorizar un movimiento que requiere autorización previa |
| `inv.movimiento.anular` | movimiento | anular | INV | Permite anular un movimiento (no procesado) |
| `inv.inventario_fisico.finalizar` | inventario_fisico | finalizar | INV | Permite cerrar la toma de inventario físico (en_proceso → finalizado) |
| `inv.inventario_fisico.aprobar` | inventario_fisico | aprobar | INV | Permite aprobar el inventario físico y generar el movimiento de ajuste de stock |
| `inv.inventario_fisico.anular` | inventario_fisico | anular | INV | Permite anular un inventario físico no ajustado |
