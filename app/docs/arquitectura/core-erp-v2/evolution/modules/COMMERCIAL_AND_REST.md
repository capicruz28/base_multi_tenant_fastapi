# Evolución modular — Comercial / Logística / Facturación / Resto

**Fase D1 · modules**

---

## SLS / PRC / CRM

| Campo | Contenido |
|-------|-----------|
| Estado V1 | Medio |
| Conservar | Clientes, cotizaciones, pedidos, listas precio, CRM |
| Extender | Detalles pueden referenciar SKU variante (`producto_id` hijo) cuando exista; sin rediseño de cabeceras |
| Rediseñar | — |
| Tablas nuevas | — |
| Justificación | Pedido ya es AR; variantes se resuelven en INV |
| Impacto código | Bajo–medio (validar producto stockeable) |
| Prioridad | **P2** (tras P0 variante/SKU) |

---

## LOG

| Campo | Contenido |
|-------|-----------|
| Conservar | Transportista, vehículo, ruta, guía, despacho |
| Extender | Integración por eventos con WMS/SLS (código); sin tablas nuevas P0 |
| Tablas nuevas | — |
| Prioridad | **P2** |

---

## BILL (`invbill`) / POS

| Campo | Contenido |
|-------|-----------|
| Conservar | Series, comprobantes, POS turno/venta |
| Extender | `invbill_comprobante_detalle` ← `lote_id`; `pos_venta_detalle` ← `lote_id` |
| Rediseñar | — |
| Tablas nuevas | — |
| Impacto código | Medio (schemas/detalle) |
| Prioridad | **P0** (factura) · **P1** (POS) |

---

## HCM / MNT

| Campo | Contenido |
|-------|-----------|
| Conservar | Todo el modelo V1 |
| Extender | HCM: exponer empleado a MES (lectura); MNT: eventos de OT (código) |
| Tablas nuevas | — |
| Prioridad | **P2** |

---

## FIN / TAX / BDG / CST

| Campo | Contenido |
|-------|-----------|
| Conservar | Plan cuentas, periodos, asientos, presupuesto, costo snapshot, tax metadata |
| Extender | — en ola industrial |
| Rediseñar | — |
| Tablas nuevas | Subledgers CxC/CxP **diferidos** (deuda Core, no P0) |
| Prioridad | **P3** |

---

## Stubs: PM / SVC / TKT / BI / DMS / WFL / AUD

| Campo | Contenido |
|-------|-----------|
| Conservar | Tablas placeholder / AUD log |
| Extender | — |
| Rediseñar | — |
| Tablas nuevas | — (WFL runtime / RPT semántica diferidos) |
| Justificación | No bloquean Core industrial; evitar scope creep |
| Prioridad | Diferir |

**AUD:** no convertir en Event Bus.
