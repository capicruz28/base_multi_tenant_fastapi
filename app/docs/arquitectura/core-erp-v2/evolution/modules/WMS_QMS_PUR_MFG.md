# Evolución modular — WMS / QMS / PUR / MFG

**Fase D1 · modules**

---

## WMS

| Campo | Contenido |
|-------|-----------|
| Estado V1 | Medio — zonas, ubicaciones, stock ubicación, tareas |
| Conservar | `wms_zona_almacen`; base de `wms_ubicacion`, `wms_stock_ubicacion`, `wms_tarea` |
| Extender | `wms_ubicacion` ← estrategia override; `wms_stock_ubicacion` ← `lote_id`; `wms_tarea` ← `oleada_id` |
| Rediseñar | — (no rehacer modelo de tareas monolineales en esta ola) |
| Tablas nuevas | **`wms_oleada`** (C1) |
| Justificación | Oleada es AR; estrategia/lote son extensiones |
| Impacto código | Medio — schemas/endpoints tarea; servicio oleada nuevo |
| Prioridad | P0 (estrategia + lote_id) · **P1** (oleada) |

**Rechazado:** tablas de slotting/yard/putaway rules (P2+).

---

## QMS

| Campo | Contenido |
|-------|-----------|
| Estado V1 | Medio |
| Conservar | Parámetro, plan, inspección, NC (estructura) |
| Extender | `qms_inspeccion` + `qms_no_conformidad` ← `lote_id` |
| Rediseñar | — |
| Tablas nuevas | — en ola P0/P1 |
| Justificación | Calidad enterprise CAPA/SPC es evolución posterior; vínculo a Lote basta ahora |
| Impacto código | Medio |
| Prioridad | **P0** (`lote_id`) · P2 (CAPA) |

**Rechazado:** FK circular lote↔inspección como dueño dual; dirección QMS→efecto en Lote vía INV.

---

## PUR

| Campo | Contenido |
|-------|-----------|
| Estado V1 | Alto — pipeline completo |
| Conservar | Proveedor, solicitud, cotización, OC, recepción cabecera, contactos, producto-proveedor |
| Extender | `pur_recepcion_detalle` ← `lote_id` |
| Rediseñar | — |
| Tablas nuevas | — |
| Justificación | Recepción ya es el documento; Lote es AR de INV creado desde recepción |
| Impacto código | Medio — detalle recepción + posible orquestación creación lote |
| Prioridad | **P0** |

**Preservar:** no reescribir flujo solicitud→OC.

---

## MFG

| Campo | Contenido |
|-------|-----------|
| Estado V1 | Medio |
| Conservar | CT, operación, BOM, ruta, OP, OP-operación |
| Extender | `mfg_consumo_materiales` ← `lote_id` |
| Rediseñar | — |
| Tablas nuevas | — dentro de MFG |
| Justificación | MES/PLN son BC nuevos (tablas fuera de `mfg_*` o calendario con dueño PLN) |
| Impacto código | Medio en consumo; bajo en BOM/OP |
| Prioridad | **P0** (lote en consumo) · P1 (integración MES por eventos) |

**Prohibido:** meter OEE/paradas dentro de tablas MFG existentes “para no crear MES”.
