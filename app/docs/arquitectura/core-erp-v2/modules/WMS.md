# Auditoría modular — WMS

**Módulo:** WMS  
**Prioridad global:** P0–P1

---

## Estado actual (V010)

Básico. Tablas: `wms_zona_almacen`, `wms_ubicacion`, `wms_stock_ubicacion`, `wms_tarea`.

## Fortalezas

- Jerarquía almacén → zona → ubicación.
- Stock por ubicación; tareas de picking/putaway.
- Flags multi-lote en ubicación.

## Debilidades

- Sin oleadas (wave).
- Sin estrategia FIFO/FEFO por ubicación.
- Lote NVARCHAR; tarea monolineal.
- Sin putaway rules / slotting / labor.

## Cambios recomendados

1. `estrategia_salida` (override) en `wms_ubicacion` con CHECK; hereda de almacén.
2. **`wms_oleada`** + `oleada_id` en `wms_tarea` (preferir modelo B: avance/criterio).
3. `lote_id` en `wms_stock_ubicacion`.
4. Fasear enterprise (ADR-06): putaway/slotting después.

## Justificación

Oleada + FEFO son multi-industria. Slotting no bloquea V2.0.

## Prioridad

**P0** (estrategia + lote_id) / **P1** (oleada) / **P2+** (slotting)

## Impacto

Alto en productividad de almacén y trazabilidad.

## Riesgos

- Tarea 1-línea limita oleadas densas (puede requerir detalle de tarea después).
- Divergencia INV stock vs WMS stock ubicación.
