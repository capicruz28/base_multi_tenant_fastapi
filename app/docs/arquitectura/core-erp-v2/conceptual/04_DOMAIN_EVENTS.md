# Eventos de Dominio oficiales del Core

**Documento:** Etapa 0.5 · 04  
**Serie:** CORE ERP V2 — Modelo Conceptual  
**Estado:** Definitivo (congelado a nivel conceptual)  
**Alcance:** Catálogo de eventos de negocio — **sin diseño del Event Bus**

---

## 1. Propósito

Definir el **catálogo oficial de Domain Events** del Core.

Este documento:

- Nombra eventos de negocio estables.
- Indica productor, consumidores esperados, motivo y payload mínimo.
- **No** diseña transporte, outbox, tablas ni brokers.

El Event Bus (EVT) implementará estos contratos después.

---

## 2. Convenciones

| Convención | Valor |
|------------|-------|
| Nombre | `PascalCase` en español de dominio + verbo en pasado (`PedidoConfirmado`) |
| Idempotencia | Cada evento lleva `event_id` y `occurred_at` |
| Scope | Siempre `cliente_id` + `empresa_id` |
| Aggregate | `aggregate_type` + `aggregate_id` |
| Correlation | `correlation_id` / `causation_id` cuando hay cadena |
| Version | `event_version` (semver mayor del contrato) |

**Payload mínimo común (todos):**

```
event_id, event_type, event_version,
cliente_id, empresa_id,
aggregate_type, aggregate_id,
occurred_at, correlation_id?
```

Los campos listados por evento son **adicionales** al mínimo común.

---

## 3. Catálogo por dominio productor

### 3.1 ORG / CFG

| Evento | Productor | Consumidores esperados | Motivo | Datos mínimos adicionales |
|--------|-----------|------------------------|--------|---------------------------|
| `EmpresaCreada` | ORG | CFG, ALR, Verticales | Alta de contexto multiempresa | `empresa_id`, `codigo_empresa` |
| `EmpresaDesactivada` | ORG | CFG, todos operativos (lectura) | Corte operativo | `empresa_id` |
| `VerticalEmpresaActivada` | CFG | UI/menú, Verticales, ALR | Habilitar industria | `codigo_vertical`, `empresa_id` |
| `VerticalEmpresaDesactivada` | CFG | UI/menú, Verticales | Retirar industria | `codigo_vertical`, `empresa_id` |

---

### 3.2 INV — Producto, Lote, Stock, Movimiento

| Evento | Productor | Consumidores esperados | Motivo | Datos mínimos adicionales |
|--------|-----------|------------------------|--------|---------------------------|
| `ProductoCreado` | INV | PRC, MFG, WMS, Verticales | Nuevo maestro | `producto_id`, `codigo`, flags lotes/series |
| `ProductoActualizado` | INV | PRC, MFG, WMS | Cambio maestro relevante | `producto_id`, campos cambiados (ids) |
| `VarianteCreada` | INV | PRC, SLS, WMS | Nuevo SKU | `variante_id`, `producto_id`, ejes |
| `LoteCreado` | INV | QMS, WMS, ALR, Verticales | Nace partida trazable | `lote_id`, `producto_id`, `codigo_lote`, `origen` |
| `LoteEstadoCambiado` | INV | WMS, QMS, ALR, SLS/LOG | Cuarentena/bloqueo/disponible/rechazo | `lote_id`, `estado_anterior`, `estado_nuevo`, `motivo?` |
| `LoteCantidadActualizada` | INV | WMS, ALR, CST | Cambio de disponible/reservada/bloqueada | `lote_id`, cantidades nuevas |
| `StockActualizado` | INV | WMS, ALR, MRP, CST | Saldo cambió | `producto_id`, `almacen_id`, `lote_id?`, `cantidad` |
| `ReservaCreada` | INV | WMS, SLS, ALR | Stock comprometido | `reserva_id`, `producto_id`, `lote_id?`, `cantidad`, `origen_doc` |
| `ReservaLiberada` | INV | WMS, SLS | Stock liberado | `reserva_id`, `cantidad` |
| `MovimientoProcesado` | INV | WMS, FIN/CST, ALR, AUD | Transacción de inventario aplicada | `movimiento_id`, `tipo`, líneas (producto/lote/cant) |
| `MovimientoAnulado` | INV | WMS, FIN/CST, ALR | Reverso | `movimiento_id`, `movimiento_compensatorio_id?` |
| `InventarioFisicoCerrado` | INV | ALR, AUD | Conteo cerrado / ajustes | `inventario_fisico_id` |

---

### 3.3 WMS

| Evento | Productor | Consumidores esperados | Motivo | Datos mínimos adicionales |
|--------|-----------|------------------------|--------|---------------------------|
| `OleadaCreada` | WMS | ALR, SLS | Wave planificada | `oleada_id`, `tipo`, `almacen_id` |
| `OleadaLiberada` | WMS | Operarios/UI, ALR | Trabajo liberado a piso | `oleada_id` |
| `OleadaCompletada` | WMS | LOG, SLS, ALR | Wave terminada | `oleada_id`, métricas avance |
| `TareaAlmacenAsignada` | WMS | ALR, UI | Asignación a operario | `tarea_id`, `usuario_asignado_id` |
| `TareaAlmacenCompletada` | WMS | INV (si confirma), LOG, SLS | Pick/putaway hecho | `tarea_id`, `tipo`, refs producto/lote/ubicación |
| `UbicacionBloqueada` | WMS | ALR, INV | Ubicación no operable | `ubicacion_id`, `motivo` |

---

### 3.4 QMS

| Evento | Productor | Consumidores esperados | Motivo | Datos mínimos adicionales |
|--------|-----------|------------------------|--------|---------------------------|
| `InspeccionIniciada` | QMS | ALR, INV | QC en curso | `inspeccion_id`, `lote_id?`, `producto_id` |
| `InspeccionFinalizada` | QMS | INV, ALR, PUR, MFG, Verticales | Resultado QC | `inspeccion_id`, `resultado`, `lote_id?` |
| `NoConformidadAbierta` | QMS | ALR, MFG, PUR, Verticales | Desviación | `nc_id`, `severidad`, refs |
| `NoConformidadCerrada` | QMS | ALR, AUD | Cierre NC | `nc_id`, `disposicion` |

---

### 3.5 PUR

| Evento | Productor | Consumidores esperados | Motivo | Datos mínimos adicionales |
|--------|-----------|------------------------|--------|---------------------------|
| `OrdenCompraEmitida` | PUR | ALR, MRP, FIN | Compromiso compra | `orden_compra_id`, `proveedor_id` |
| `OrdenCompraCerrada` | PUR | MRP, ALR | Fin ciclo OC | `orden_compra_id` |
| `RecepcionRegistrada` | PUR | INV, QMS, ALR, WMS | Mercancía ingresó | `recepcion_id`, `orden_compra_id?`, líneas (producto/cant) |
| `RecepcionCerrada` | PUR | INV, FIN | Recepción completa | `recepcion_id` |

---

### 3.6 SLS / PRC / CRM

| Evento | Productor | Consumidores esperados | Motivo | Datos mínimos adicionales |
|--------|-----------|------------------------|--------|---------------------------|
| `OportunidadGanada` | CRM | SLS, ALR | Conversión comercial | `oportunidad_id`, `cliente_id?` |
| `CotizacionAceptada` | SLS | ALR | Oferta aceptada | `cotizacion_id` |
| `PedidoCreado` | SLS | ALR, PRC (audit) | Alta pedido | `pedido_id`, `cliente_id` |
| `PedidoConfirmado` | SLS | INV (reserva), WMS, LOG, BILL, ALR, MFG | Demanda firme | `pedido_id`, líneas |
| `PedidoCancelado` | SLS | INV, WMS, LOG, ALR | Liberar fulfillment | `pedido_id`, `motivo` |
| `PedidoCerrado` | SLS | BILL, ALR | Ciclo comercial cerrado | `pedido_id` |
| `PrecioListaPublicada` | PRC | SLS, POS | Nueva vigencia | `lista_precio_id`, vigencia |

---

### 3.7 LOG

| Evento | Productor | Consumidores esperados | Motivo | Datos mínimos adicionales |
|--------|-----------|------------------------|--------|---------------------------|
| `DespachoCreado` | LOG | ALR, SLS | Preparación salida | `despacho_id`, `pedido_id?` |
| `DespachoConfirmado` | LOG | INV, SLS, BILL, ALR | Salida confirmada | `despacho_id`, guías, líneas |
| `GuiaRemisionEmitida` | LOG | ALR, TAX/AUD | Documento transporte | `guia_id`, `despacho_id` |

---

### 3.8 MFG / MES / PLN / MRP / MPS

| Evento | Productor | Consumidores esperados | Motivo | Datos mínimos adicionales |
|--------|-----------|------------------------|--------|---------------------------|
| `PlanMPSPublicado` | MPS | MRP, MFG, ALR | Plan agregado vigente | `plan_mps_id` |
| `PlanMRPCalculado` | MRP | PUR, MFG, ALR | Sugerencias listas | `plan_mrp_id` |
| `OrdenProduccionCreada` | MFG | PLN, MES, ALR | OP existe | `orden_produccion_id`, `producto_id`, `cantidad` |
| `OrdenProduccionLiberada` | MFG | MES, INV, WMS, PLN, ALR | OP ejecutable | `orden_produccion_id` |
| `OrdenProduccionTerminada` | MFG | INV, QMS, CST, ALR | OP concluida | `orden_produccion_id`, `cantidad_buena` |
| `OrdenProduccionAnulada` | MFG | MES, INV, ALR | Cancelación | `orden_produccion_id` |
| `ConsumoMaterialRegistrado` | MFG | INV, CST, ALR | Material consumido | `orden_produccion_id`, `producto_id`, `lote_id?`, `cantidad` |
| `ProduccionReportada` | MFG | INV, QMS, ALR | Entrada de producto terminado/semi | `orden_produccion_id`, `producto_id`, `lote_id?`, `cantidad` |
| `EjecucionIniciada` | MES | PLN, ALR, MFG | Piso arrancó operación | `ejecucion_id`, `orden_produccion_id`, `centro_trabajo_id` |
| `EjecucionCompletada` | MES | PLN, MFG, ALR, CST | Operación real terminada | `ejecucion_id`, tiempos |
| `ParadaRegistrada` | MES | PLN, MNT, ALR | Downtime | `parada_id`, `ejecucion_id`, `motivo_oee` |
| `CapacidadActualizada` | PLN | MFG, MRP, ALR, (futuro APS) | Cambio de disponibilidad | `centro_trabajo_id`, `fecha`, horas |

---

### 3.9 MNT / HCM

| Evento | Productor | Consumidores esperados | Motivo | Datos mínimos adicionales |
|--------|-----------|------------------------|--------|---------------------------|
| `OrdenTrabajoMantenimientoAbierta` | MNT | PLN, MES, ALR | Activo puede quedar indisponible | `ot_id`, `activo_id` |
| `OrdenTrabajoMantenimientoCerrada` | MNT | PLN, MES, ALR | Activo recuperado | `ot_id` |
| `EmpleadoActivado` | HCM | MES, ALR | Operario disponible | `empleado_id` |

---

### 3.10 BILL / POS / FIN

| Evento | Productor | Consumidores esperados | Motivo | Datos mínimos adicionales |
|--------|-----------|------------------------|--------|---------------------------|
| `FacturaEmitida` | BILL | FIN, SLS, ALR, TAX, AUD | Comprobante fiscal emitido | `comprobante_id`, `cliente_id`, totales, refs pedido |
| `FacturaAnulada` | BILL | FIN, SLS, ALR | Anulación fiscal | `comprobante_id` |
| `VentaPOSCerrada` | POS | INV, BILL?, ALR | Venta mostrador cerrada | `venta_pos_id`, líneas |
| `AsientoContabilizado` | FIN | ALR, AUD, BDG | Contabilización | `asiento_id`, `periodo_id` |
| `PeriodoContableCerrado` | FIN | BILL, ALR | Cierre periodo | `periodo_id` |

---

### 3.11 ALR (eventos de salida del propio consumidor)

| Evento | Productor | Consumidores esperados | Motivo | Datos mínimos adicionales |
|--------|-----------|------------------------|--------|---------------------------|
| `AlertaGenerada` | ALR | UI, notificaciones, WFL | Se disparó regla | `alerta_id`, `regla_id`, `severidad`, refs |
| `AlertaAtendida` | ALR | AUD | Cierre humano | `alerta_id` |

---

## 4. Cadenas típicas (correlación)

### Ingreso por compra
`RecepcionRegistrada` → `LoteCreado` → `InspeccionFinalizada` → `LoteEstadoCambiado` → `StockActualizado` → (`TareaAlmacenCompletada` putaway)

### Pedido a despacho
`PedidoConfirmado` → `ReservaCreada` → `OleadaLiberada` → `TareaAlmacenCompletada` → `DespachoConfirmado` → `MovimientoProcesado` / `StockActualizado` → `FacturaEmitida`

### Orden de producción
`OrdenProduccionLiberada` → `EjecucionIniciada` → (`ParadaRegistrada`*) → `EjecucionCompletada` → `ConsumoMaterialRegistrado` → `ProduccionReportada` → `LoteCreado` → `InspeccionFinalizada?` → `OrdenProduccionTerminada`

---

## 5. Reglas de evolución del catálogo

1. **No renombrar** eventos publicados; versionar contrato.
2. Campos nuevos = versión menor compatible; breaking = versión mayor + dual publish temporal.
3. Verticales pueden emitir eventos propios con prefijo de vertical (`Txt…`, `Fod…`); **no** reutilizar nombres Core con otra semántica.
4. Un evento Core no debe contener payload de semántica de industria.
5. ALR puede escuchar cualquier evento; no todos los eventos requieren regla.

---

## 6. Fuera de alcance de este documento

- Diseño de outbox / topics / retry
- Esquema físico de EVT
- Mapeo a colas externas
- APS events (se añadirán cuando exista el BC físico)

---

## 7. Criterio de cierre

El catálogo queda cerrado para ola conceptual cuando cubre los ciclos procure-to-stock, order-to-cash y plan-to-produce, más gobernanza y calidad.

**Estado:** cerrado (extensible solo por ADR de evento nuevo).
