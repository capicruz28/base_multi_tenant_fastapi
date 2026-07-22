# 01 — Cambios contractuales OpenAPI

**Fuente:** `app/docs/openapi_snapshot.json` vigente.  
**Alcance:** exclusivamente el delta producido por el Motor de Códigos.

---

## 1. Reglas comunes

| Operación | Antes | Contrato vigente |
|-----------|-------|------------------|
| CREATE maestro AUTO_DEFAULT | Código requerido | Código opcional (`string | null`) |
| CREATE documento AUTO_REQUIRED | Número requerido | Campo número ausente |
| UPDATE | Campo código/número presente | Campo Motor ausente |
| READ / LIST / respuesta 201 | Código/número requerido | Sin cambio |

Readonly significa: presente en schemas Read, ausente de schemas Update y, para
documentos AUTO_REQUIRED, también ausente de Create.

Los schemas Pydantic actuales ignoran propiedades extra. Esto no convierte esas
propiedades en contrato soportado:

- un código Motor enviado en UPDATE se ignora y el valor persistido no cambia;
- `numero_movimiento` o `numero_inventario` enviado en CREATE se ignora y el
  Backend genera otro valor.

El Frontend debe eliminar esas propiedades, no depender de la tolerancia a extras.

---

## 2. Categoría

Campo Motor: `codigo`.

| Endpoint | Request anterior | Request vigente | Response | Delta / compatibilidad |
|----------|------------------|-----------------|----------|------------------------|
| `POST /api/v1/inv/categorias` | `CategoriaCreate.codigo: string` requerido | `codigo?: string \| null` | `201 CategoriaRead`; `codigo: string` requerido | Compatible con FE manual; nuevo FE puede omitir. |
| `PUT /api/v1/inv/categorias/{categoria_id}` | `CategoriaUpdate` incluía `codigo` | `codigo` eliminado | `200 CategoriaRead`, código original | FE anterior puede enviarlo como extra, pero no se modifica. Debe retirarse. |
| `GET /api/v1/inv/categorias` | Sin cambio | Sin cambio | lista/envelope con `CategoriaRead.codigo` | Columna código continúa. |
| `GET /api/v1/inv/categorias/{categoria_id}` | Sin cambio | Sin cambio | `CategoriaRead` | Código readonly. |
| `DELETE .../{categoria_id}` / `POST .../{categoria_id}/reactivar` | Sin cambio | Sin cambio | 204 / `CategoriaRead` | Soft-delete/reactivar preserva código. |

Campos Create requeridos vigentes: `empresa_id`, `nombre`.

---

## 3. Unidad de medida

Campo Motor: `codigo`.

| Endpoint | Request anterior | Request vigente | Response | Delta / compatibilidad |
|----------|------------------|-----------------|----------|------------------------|
| `POST /api/v1/inv/unidades-medida` | `codigo: string` requerido | `codigo?: string \| null` | `201 UnidadMedidaRead`; código requerido | Compatible con manual u omisión. |
| `PUT /api/v1/inv/unidades-medida/{unidad_medida_id}` | Update incluía `codigo` | `codigo` eliminado | `200 UnidadMedidaRead` | Código original readonly. |
| GET colección / detalle | Sin cambio | Sin cambio | `UnidadMedidaRead` | Código sigue disponible. |
| DELETE / reactivar | Sin cambio | Sin cambio | 204 / `UnidadMedidaRead` | Código preservado. |

Campos Create requeridos vigentes: `empresa_id`, `nombre`, `tipo_unidad`.

---

## 4. Tipo de movimiento

Campo Motor: `codigo`.

| Endpoint | Request anterior | Request vigente | Response | Delta / compatibilidad |
|----------|------------------|-----------------|----------|------------------------|
| `POST /api/v1/inv/tipos-movimiento` | `codigo: string` requerido | `codigo?: string \| null` | `201 TipoMovimientoRead`; código requerido | Compatible con manual u omisión. |
| `PUT /api/v1/inv/tipos-movimiento/{tipo_movimiento_id}` | Update incluía `codigo` | `codigo` eliminado | `200 TipoMovimientoRead` | Código original readonly. |
| GET colección / detalle | Sin cambio | Sin cambio | `TipoMovimientoRead` | Código sigue disponible. |
| DELETE / reactivar | Sin cambio | Sin cambio | 204 / `TipoMovimientoRead` | Código preservado. |

Campos Create requeridos vigentes:
`empresa_id`, `nombre`, `clase_movimiento`.

---

## 5. Almacén

Campo Motor: `codigo`.

| Endpoint | Request anterior | Request vigente | Response | Delta / compatibilidad |
|----------|------------------|-----------------|----------|------------------------|
| `POST /api/v1/inv/almacenes` | `codigo: string` requerido | `codigo?: string \| null` | `201 AlmacenRead`; código requerido | Compatible con manual u omisión. |
| `PUT /api/v1/inv/almacenes/{almacen_id}` | Update incluía `codigo` | `codigo` eliminado | `200 AlmacenRead` | Código original readonly. |
| GET colección / detalle | Sin cambio | Sin cambio | `AlmacenRead` | Código sigue disponible. |
| DELETE / reactivar | Sin cambio | Sin cambio | 204 / `AlmacenRead` | Código preservado. |

Campos Create requeridos vigentes: `empresa_id`, `nombre`, `tipo_almacen`.

---

## 6. Producto

Campo Motor: únicamente `codigo_sku`.

| Endpoint | Request anterior | Request vigente | Response | Delta / compatibilidad |
|----------|------------------|-----------------|----------|------------------------|
| `POST /api/v1/inv/productos` | `codigo_sku: string` requerido | `codigo_sku?: string \| null` | `201 ProductoRead`; SKU requerido | Compatible con SKU manual u omisión. |
| `PUT /api/v1/inv/productos/{producto_id}` | Update incluía `codigo_sku` | `codigo_sku` eliminado | `200 ProductoRead` | SKU original readonly. |
| GET colección / detalle | Sin cambio | Sin cambio | `ProductoRead` | SKU sigue disponible en grillas y detalle. |
| DELETE / reactivar | Sin cambio | Sin cambio | 204 / `ProductoRead` | SKU preservado. |

Campos Create requeridos vigentes:
`empresa_id`, `nombre`, `tipo_producto`, `unidad_medida_base_id`,
`moneda_costo`, `moneda_venta`.

No fueron eliminados ni hechos readonly por BR-IMM:
`codigo_barra`, `codigo_interno`, `codigo_fabricante`. Continúan en Create,
Update y Read.

---

## 7. Movimiento

Campo Motor: `numero_movimiento` (AUTO_REQUIRED).

| Endpoint | Request anterior | Request vigente | Response | Delta / compatibilidad |
|----------|------------------|-----------------|----------|------------------------|
| `POST /api/v1/inv/movimientos` | `numero_movimiento: string` requerido | Campo eliminado de `MovimientoCreate` | `201 MovimientoRead`; número requerido | FE anterior compila solo si actualiza tipos; un extra enviado se ignora. |
| `POST /api/v1/inv/movimientos/con-detalle` | Número requerido heredado | Campo ausente de `MovimientoConDetalleCreate` | `201 MovimientoConDetalleRead` | Igual; `detalles` continúa requerido, mínimo 1. |
| `PUT /api/v1/inv/movimientos/{movimiento_id}` | Update incluía número | Campo eliminado de `MovimientoUpdate` | `200 MovimientoRead` | Número original readonly. |
| `PUT /api/v1/inv/movimientos/{movimiento_id}/con-detalle` | Update embebido incluía número | Campo ausente de `MovimientoConDetalleUpdate` | `200 MovimientoConDetalleRead` | Número original readonly. |
| GET colección / detalle / `con-detalle` | Sin cambio | Sin cambio | Read con `numero_movimiento: string` requerido | Mostrar número retornado. |

Campos Create requeridos vigentes:
`empresa_id`, `tipo_movimiento_id`, `fecha_contable`.
En `MovimientoConDetalleCreate`, también `detalles`.

Acciones de proceso:

El snapshot publica las rutas canónicas bajo `/api/v1/inv/movimientos/{id}/*`
y sus aliases legacy `/api/v1/inv/{id}/*`. El contrato Motor descrito abajo es
idéntico en ambos montajes; el Frontend nuevo debe usar la ruta canónica.

| Endpoint | Request Motor | Response Motor | Cambio |
|----------|---------------|----------------|--------|
| `POST .../{id}/procesar` | Ningún número | `MovimientoRead.numero_movimiento` | Sin cambio |
| `POST .../{id}/autorizar` | Ningún número | `MovimientoRead.numero_movimiento` | Sin cambio |
| `POST .../{id}/anular` | Solo motivo opcional | `MovimientoRead.numero_movimiento` | Sin cambio |
| `POST .../{id}/estornar` | Solo motivo opcional | Movimiento original actualizado a `estornado`, con su número original | El compensatorio se numera internamente; no forma parte directa del response |

---

## 8. Inventario físico

Campo Motor: `numero_inventario` (AUTO_REQUIRED).

| Endpoint | Request anterior | Request vigente | Response | Delta / compatibilidad |
|----------|------------------|-----------------|----------|------------------------|
| `POST /api/v1/inv/inventario-fisico` | `numero_inventario: string` requerido | Campo eliminado de `InventarioFisicoCreate` | `201 InventarioFisicoRead`; número requerido | FE debe retirar campo; extra legacy se ignora. |
| `POST /api/v1/inv/inventario-fisico/con-detalle` | Número requerido heredado | Campo ausente de `InventarioFisicoConDetalleCreate` | `201 InventarioFisicoConDetalleRead` | `detalles` permanece opcional. |
| `PUT /api/v1/inv/inventario-fisico/{inventario_fisico_id}` | Update incluía número | Campo eliminado de `InventarioFisicoUpdate` | `200 InventarioFisicoRead` | Número original readonly. |
| `PUT .../{inventario_fisico_id}/con-detalle` | Update embebido incluía número | Campo ausente de `InventarioFisicoConDetalleUpdate` | `200 InventarioFisicoConDetalleRead` | Número original readonly. |
| GET colección / detalle / `con-detalle` | Sin cambio | Sin cambio | Read con `numero_inventario: string` requerido | Mostrar número retornado. |

Campos Create requeridos vigentes:
`empresa_id`, `fecha_inventario`, `almacen_id`, `tipo_inventario`.

Acciones `anular`, `finalizar` y `aprobar` no aceptan
`numero_inventario`; sus responses conservan el número original. La aprobación
puede generar internamente un movimiento de ajuste con su propio
`numero_movimiento`; el Frontend no lo calcula.

---

## 9. Errores relevantes

| HTTP | Caso | Acción Frontend |
|------|------|-----------------|
| 403 | Sin permiso o `empresa_id` distinto de sesión | Corregir sesión/payload o informar permisos |
| 404 | Configuración de secuencia ausente | Mensaje técnico; no reintentar con número local |
| 409 | Código/SKU manual duplicado | Asociar `detail` al campo manual |
| 422 | Validación de request/formato | Mostrar errores de campo |

Mensajes 409 vigentes:

- `Ya existe una categoría con el código '{codigo}' en esta empresa.`
- `Ya existe una unidad de medida con el código '{codigo}' en esta empresa.`
- `Ya existe un tipo de movimiento con el código '{codigo}' en esta empresa.`
- `Ya existe un almacén con el código '{codigo}' en esta empresa.`
- `Ya existe un producto con SKU '{codigo}' en esta empresa.`
