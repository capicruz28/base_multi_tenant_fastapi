# Evolución modular — INV

**Fase D1 · modules**  
**Prioridad ola:** **P0**  
**Madurez código V1:** ~99% (en prueba) — máxima preservación

---

## Tablas V1

`inv_categoria_producto`, `inv_unidad_medida`, `inv_producto`, `inv_almacen`, `inv_stock`, `inv_tipo_movimiento`, `inv_movimiento`, `inv_movimiento_detalle`, `inv_inventario_fisico`, `inv_inventario_fisico_detalle`

---

## Conservar sin cambios

| Tabla | Nota |
|-------|------|
| `inv_categoria_producto` | Intacta |
| `inv_unidad_medida` | Intacta |
| `inv_tipo_movimiento` | Intacta |
| `inv_movimiento` (cabecera) | Flujo borrador→procesar→estornar se preserva |
| `inv_inventario_fisico` (cabecera) | Flujo de conteo se preserva |

---

## Extender

| Tabla | Extensión conceptual | Criterio |
|-------|----------------------|----------|
| `inv_almacen` | Estrategia de salida default | C3 capacidad FEFO/FIFO |
| `inv_movimiento_detalle` | `lote_id` (FK a AR Lote) | Extensión; no tabla nueva |
| `inv_inventario_fisico_detalle` | `lote_id` | Extensión |
| `inv_producto` | Padre SKU + ejes genéricos de variante (si no hay tabla variante) | Preferencia evolución D-EVO-03 |
| `inv_producto` | Mantener `color`/`talla` temporalmente (compat) | Preservación código |

Política `lote` NVARCHAR: **no borrar** en el primer corte de diseño; coexistir con `lote_id` hasta enforcement.

---

## Rediseño importante

| Tabla | Qué cambia | Por qué |
|-------|------------|---------|
| `inv_stock` | Unicidad/dimensión pasa a incluir **Lote** (cuando el producto maneja lotes) | Sin esto FEFO y cantidades de lote son mentira |

**Preferencia:** rediseñar `inv_stock` existente (extensión estructural), **no** crear `inv_stock_lote`.

Impacto código: **alto** (endpoints stock, reservas futuras, movimientos).

---

## Tablas nuevas obligatorias

| Tabla | Criterio | Justificación |
|-------|----------|---------------|
| `inv_lote` | C1+C3 | AR Lote; imposible con NVARCHAR |

| Tabla | Estado |
|-------|--------|
| `inv_producto_variante` | **Condicional** — preferir extensión `inv_producto` |
| `inv_serie` | Diferir (P2/P3) |
| `inv_reserva` | Diferir a D1.1; intentar modelo en stock/movimiento primero |

---

## Impacto código V1

| Componente | Impacto | Acción evolutiva |
|------------|---------|------------------|
| Schemas producto (`color`/`talla`) | Medio | Deprecar semántica; ejes nuevos aditivos |
| Schemas movimiento/físico (`lote`) | Alto | Añadir `lote_id` |
| `movimiento_service` / estorno | Alto | Propagar `lote_id`; no reescribir pipeline |
| Stock endpoints | Alto | Nueva dimensión; tests a rehacer |
| Código generación INV | Bajo | Intactos scopes |

---

## Prioridad

| Ítem | P |
|------|---|
| `inv_lote` + `lote_id` en detalles INV | P0 |
| `inv_stock` lotificado | P0 |
| Estrategia en `inv_almacen` | P0 |
| Variante (extensión producto) | P0 |
| Serie / reserva tabla | P2+ |
