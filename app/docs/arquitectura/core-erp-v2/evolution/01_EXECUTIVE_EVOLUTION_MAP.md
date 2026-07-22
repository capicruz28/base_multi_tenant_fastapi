# Mapa ejecutivo de evolución CORE V1 → CORE V2

**Documento:** Fase D1 · 01  
**Serie:** CORE ERP V2 — Auditoría de evolución  
**Estado:** Definitivo para gate D1 (evolución)

---

## 1. Veredicto

El Core V2 **no** reemplaza el mapa V1. Evoluciona V1 así:

| Estrategia | Alcance aproximado |
|------------|-------------------|
| Conservar sin cambios | ~70% de tablas V010 + IAM/plataforma |
| Extender tablas existentes | ~20% (lote_id, estrategia, stock, MRP empresa_id, producto) |
| Rediseño importante de existentes | ~3–5% (principalmente `inv_stock` y contratos `lote` string en INV maduro) |
| Tablas nuevas obligatorias | **pocas** (Lote, Oleada, MES, PLN, CFG vertical, EVT, ALR; Variante preferible por extensión) |
| Diferir | APS, RPT semántica, Series AR, CAPA/SPC, WMS slotting, FIN subledgers |

---

## 2. Tablas nuevas obligatorias (resumen)

Justificación detallada: `02_MANDATORY_NEW_TABLES.md`.

| Tabla nueva propuesta | Criterio | Prioridad | ¿Inevitable? |
|-----------------------|----------|-----------|--------------|
| `inv_lote` | C1 AR Lote | P0 | **Sí** |
| `wms_oleada` | C1 AR Oleada | P1 | **Sí** |
| `cfg_vertical_empresa` | C1 AR + relación N verticales/empresa | P1 | **Sí** |
| `mes_ejecucion_operacion` | C2 BC MES | P1 | **Sí** |
| `mes_parada_maquina` | C2 + relación a ejecución | P1 | **Sí** |
| `mes_motivo_parada` | C4 catálogo OEE del BC MES | P1 | **Sí** (catálogo propio MES) |
| `pln_calendario_capacidad` (o nombre bajo PLN) | C2 BC PLN | P1 | **Sí** |
| `evt_*` (outbox/evento mínimo) | C2 BC EVT | P1 | **Sí** (mínimo viable) |
| `alr_regla_alerta` | C2 BC ALR | P1 | **Sí** |
| `alr_alerta_generada` | C1/C4 instancia de alerta | P1 | **Sí** |
| `inv_producto_variante` | C1 AR Variante | P0 | **Condicional** — preferir extensión de `inv_producto` si cubre el AR |

**No obligatorias en ola V2 industrial:** `aps_*`, `rpt_*`, tablas Series, CAPA, slotting.

---

## 3. Extensiones obligatorias a tablas V1

| Tabla V1 | Extensión conceptual | Prioridad |
|----------|----------------------|-----------|
| `inv_almacen` | Estrategia de salida default | P0 |
| `wms_ubicacion` | Override estrategia de salida | P0 |
| `inv_stock` | Dimensión lote (rediseño de unicidad) | P0 |
| `inv_movimiento_detalle` | `lote_id` (+ política sobre `lote` texto) | P0 |
| `inv_inventario_fisico_detalle` | `lote_id` | P0 |
| `wms_stock_ubicacion` | `lote_id` | P0 |
| `wms_tarea` | `oleada_id` | P1 |
| `qms_inspeccion` | `lote_id` | P0 |
| `qms_no_conformidad` | `lote_id` | P0 |
| `pur_recepcion_detalle` | `lote_id` | P0 |
| `mfg_consumo_materiales` | `lote_id` | P0 |
| `invbill_comprobante_detalle` | `lote_id` | P0 |
| `pos_venta_detalle` | `lote_id` | P1 |
| `inv_producto` | Ejes de variante / padre SKU (si no hay tabla variante) | P0 |
| `mrp_necesidad_bruta` | `empresa_id` | P1 |
| `mrp_explosion_materiales` | `empresa_id` | P1 |

---

## 4. Mapa por módulo (vista rápida)

| Módulo | Madurez código V1 | Conservar | Extender | Rediseñar | Nuevas | Prioridad ola |
|--------|-------------------|-----------|----------|-----------|--------|---------------|
| IAM/Auth/RBAC/Users/Tenant | Muy alta | Casi todo | — | — | — | — |
| CFG | ~99% | `cfg_codigo_secuencia` | — | — | `cfg_vertical_empresa` | P1 |
| ORG / CAT | ~99% | Todo | Opcional doc multiempresa | — | — | — |
| INV | ~99% | Maestros/movimientos base | Detalles + almacén + producto | `inv_stock` | `inv_lote` (+ variante condicional) | **P0** |
| WMS | Media | Zona/ubicación/tarea base | ubicación, stock_ubic, tarea | — | `wms_oleada` | P0–P1 |
| QMS | Media | Planes/inspección/NC | lote_id | — | — | P0 |
| PUR | Alta | Pipeline completo | recepción detalle | — | — | P0 |
| SLS/PRC/CRM | Media | Todo | Lectura variante/SKU | — | — | P2 |
| LOG | Media | Todo | Integración eventos | — | — | P2 |
| MFG | Media | BOM/ruta/OP | consumo lote_id | — | — | P0–P1 |
| MES | Ausente | — | — | — | 3 tablas MES | P1 |
| PLN | Ausente | — | — | — | calendario | P1 |
| MRP/MPS | Media | Estructura | MRP empresa_id | — | — | P1 |
| MNT/HCM/FIN/… | Variable | Todo | Puntual | — | — | P2–P3 |
| EVT/ALR | Ausente | — | — | — | mínimas | P1 |
| APS/RPT | — | — | — | — | **ninguna ahora** | Diferir |
| Stubs | Baja | Namespace | — | — | — | Diferir |

Detalle: `modules/*`.

---

## 5. Impacto de código (síntesis)

| Área | Impacto | Notas |
|------|---------|-------|
| INV schemas/services (`lote` string, `color`/`talla`) | **Alto** | Módulo en prueba; cambios deben ser aditivos (`lote_id` nullable → luego enforcement) |
| WMS | Medio | Añadir oleada y FKs; endpoints de tarea existentes se extienden |
| PUR/QMS/MFG/INV_BILL | Medio | Detalles con `lote_id`; servicios de recepción/consumo/factura |
| ORG/CFG/IAM | Bajo | Solo alta de vertical CFG; IAM intacto |
| MES/PLN/EVT/ALR | Alto en *código nuevo* | No reescribe V1; módulos nuevos o casi nuevos |
| SLS/POS | Bajo–medio | Referencia SKU/lote en líneas |

Detalle: `03_CODE_IMPACT_SUMMARY.md`.

---

## 6. Decisiones de evolución clave (sin columnas)

### D-EVO-01 — Lote
`inv_lote` es tabla nueva **obligatoria** (C1). El campo `lote` NVARCHAR de V1 se trata como legado a extinguir vía extensión (`lote_id`), no como AR.

### D-EVO-02 — Stock
`inv_stock` se **rediseña por extensión** (añadir dimensión lote a la unicidad). No se crea `inv_stock_lote` separado salvo que el diseño físico D1.1 demuestre imposibilidad — preferencia: **una tabla stock extendida**.

### D-EVO-03 — Variante
Preferencia de evolución: **extender `inv_producto`** (producto padre + ejes) para materializar el AR Variante sin tabla nueva.  
Tabla `inv_producto_variante` solo si D1.1 demuestra que la extensión rompe unicidad/SKU/precios.

### D-EVO-04 — MES / PLN / EVT / ALR
Nuevos BC → tablas nuevas mínimas. No meter OEE dentro de `mfg_*` ni alertas dentro de `aud_*`.

### D-EVO-05 — APS / RPT
Cero tablas. Solo puntos de extensión ya definidos en 0.5.

### D-EVO-06 — Preservación INV
Todo cambio P0 en INV debe ser **aditivo** respecto a contratos en prueba (campos nuevos, flags, FKs nullable al inicio del diseño), evitando rewrite de flujos de movimiento/estorno ya existentes.

---

## 7. Criterio de cierre D1 (evolución)

- [x] Principio de evolución mínima documentado
- [x] Mapa por módulo
- [x] Lista de tablas nuevas con criterio C1–C4
- [x] Lista de extensiones/rediseños
- [x] Impacto de código y prioridades

**Siguiente:** D1.1 diseño físico (columnas) **solo** de ítems P0 aprobados en este mapa.
