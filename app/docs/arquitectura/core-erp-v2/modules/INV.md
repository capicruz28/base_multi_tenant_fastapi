# Auditoría modular — INV (Inventarios)

**Módulo:** INV  
**Prioridad global:** P0

---

## Estado actual (V010)

Maduro a nivel de ciclo inventario (producto, almacén, stock, movimientos, físico), **no enterprise** en trazabilidad.

Tablas: `inv_categoria_producto`, `inv_unidad_medida`, `inv_producto`, `inv_almacen`, `inv_stock`, `inv_tipo_movimiento`, `inv_movimiento`, `inv_movimiento_detalle`, `inv_inventario_fisico`, `inv_inventario_fisico_detalle`.

## Fortalezas

- Cabecera-detalle de movimientos e inventario físico.
- Flags `maneja_lotes` / `maneja_series` / `maneja_vencimiento`.
- Tenant/empresa, soft delete, auditoría en maestros.
- Separación conceptual INV vs WMS ya iniciada.

## Debilidades

- Lote como `NVARCHAR(50)` en detalle/físico; sin `inv_lote`.
- `inv_stock` agregado solo por producto+almacén (no lote).
- Variantes: `color`/`talla` + JSON; sin modelo genérico.
- Sin estrategia de salida en `inv_almacen`.
- `ubicacion_almacen` texto duplica WMS.
- Costeo `fifo` textual sin capas.

## Cambios recomendados (CORE V2)

1. Introducir **`inv_lote` Aggregate Root** (ADR-04).
2. `lote_id` FK en `inv_movimiento_detalle`, `inv_inventario_fisico_detalle` (y consumidores cruzados).
3. Rediseñar **`inv_stock`** para dimensión lote (y alinear con WMS).
4. **`inv_producto_variante`** genérico (ADR-05); deprecar semántica fija color/talla.
5. `estrategia_salida` en `inv_almacen` con CHECK (ADR-06).
6. JSON solo en atributos no transaccionales.

## Justificación

Sin lote/variantes/FEFO el Core no soporta alimentos, farma, metal, agro ni distribución seria. Es el gap #1 industrial.

## Prioridad

**P0**

## Impacto

Alto — toca WMS, QMS, PUR, MFG, INV_BILL, POS. Desbloquea recall y compliance.

## Riesgos

- Doble verdad stock agregado vs lotificado.
- Variantes mal integradas → dos maestros.
- Sobreuso de `atributos_lote` JSON para estados.
