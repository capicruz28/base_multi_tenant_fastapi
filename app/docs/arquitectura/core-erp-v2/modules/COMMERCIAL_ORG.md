# Auditoría modular — ORG / CAT / PUR / SLS / LOG / INV_BILL / PRC / CRM / POS

**Prioridad global:** P2 (extensiones puntuales) — preservar V010

---

## ORG / CAT

| Campo | Contenido |
|-------|-----------|
| Estado actual | Maduro (ORG) / Básico (CAT ubigeo+moneda) |
| Fortalezas | Jerarquía org, multiempresa en schema, parámetros |
| Debilidades | Comentario legacy “1 empresa/BD”; `rubro` NVARCHAR libre; JSON en horarios/parámetros |
| Cambios recomendados | Aclarar multiempresa como norma; `rubro` no reemplaza `cfg_vertical_empresa`; no meter vertical en ORG |
| Prioridad | P2 |
| Impacto | Bajo en esta ola (ya usable) |
| Riesgos | Confundir `rubro` texto con control-plane de verticales |

---

## PUR

| Campo | Contenido |
|-------|-----------|
| Estado actual | Maduro (solicitud→OC→recepción) |
| Fortalezas | Pipeline completo, detalle, estados |
| Debilidades | Lote string en recepción; sin 3-way match formal; sin factura compra/CxP |
| Cambios recomendados | `lote_id` en `pur_recepcion_detalle`; CxP fasear con FIN |
| Prioridad | P0 (lote_id) / P2 (match/CxP) |
| Impacto | Alto en trazabilidad de ingreso |
| Riesgos | Crear lote en recepción sin reglas de identidad claras |

---

## SLS / PRC / CRM

| Campo | Contenido |
|-------|-----------|
| Estado actual | SLS maduro; PRC/CRM básicos |
| Fortalezas | Quote-to-order; listas de precio |
| Debilidades | Variantes no integradas a precio; JSON en promo/CRM |
| Cambios recomendados | Asegurar que pedidos referencien SKU variante (`inv_producto`); no rediseñar CRM ahora |
| Prioridad | P2 |
| Impacto | Medio cuando existan variantes |
| Riesgos | Precio duplicado en variante vs PRC |

---

## LOG

| Campo | Contenido |
|-------|-----------|
| Estado actual | Básico (guías/despacho Perú) |
| Fortalezas | Remisión + despacho |
| Debilidades | Sin eventos de tracking; JSON paradas; vínculo débil a picking WMS |
| Cambios recomendados | Integrar despacho con oleadas/tareas vía EVT; diferir TMS enterprise |
| Prioridad | P2 |
| Impacto | Medio |
| Riesgos | Localización Perú vs logística genérica |

---

## INV_BILL / POS

| Campo | Contenido |
|-------|-----------|
| Estado actual | INV_BILL maduro (SUNAT); POS básico |
| Fortalezas | Comprobante electrónico modelado |
| Debilidades | Lote string en detalle; sesgo fiscal local |
| Cambios recomendados | `lote_id` en detalle factura/POS; localización fiscal permanece (no es vertical industrial) |
| Prioridad | P0 (lote_id) |
| Impacto | Alto en trazabilidad salida |
| Riesgos | Mezclar compliance fiscal con diseño de lote |

---

## Síntesis

Estos módulos **no requieren rediseño estructural** en CORE V2 industrial. Requieren **extensión de lote/variante** y alineación con Event Bus donde haya handoff (recepción→lote, pedido→oleada→despacho→factura).
