# Baseline V010 — Estado actual del Core

**Documento:** 04  
**Fuente:** `app/bootstrap_v2/01_schema/V010__tablas_bd_erp_completo.sql`  
**Tablas:** ~116 `CREATE TABLE` | **Módulos indexados:** 27 + CFG al final

---

## 1. Arquitectura declarada

- Multi-tenant SaaS con BD dedicada por cliente.
- `cliente_id` + `empresa_id` (Fase 4) en tablas operativas.
- PKs `UNIQUEIDENTIFIER`.
- Soft delete `es_activo` predominante.
- Auditoría básica (`fecha_creacion`, `usuario_creacion_id`, …) en maestros.

---

## 2. Inventario de módulos y tablas

| # | Módulo | Tablas |
|---|--------|--------|
| 1 | ORG (+ cat_*) | `cat_moneda`, `cat_pais`, `cat_departamento`, `cat_provincia`, `cat_distrito`, `org_empresa`, `org_centro_costo`, `org_sucursal`, `org_departamento`, `org_cargo`, `org_parametro_sistema` |
| 2 | INV | `inv_categoria_producto`, `inv_unidad_medida`, `inv_producto`, `inv_almacen`, `inv_stock`, `inv_tipo_movimiento`, `inv_movimiento`, `inv_movimiento_detalle`, `inv_inventario_fisico`, `inv_inventario_fisico_detalle` |
| 3 | WMS | `wms_zona_almacen`, `wms_ubicacion`, `wms_stock_ubicacion`, `wms_tarea` |
| 4 | QMS | `qms_parametro_calidad`, `qms_plan_inspeccion`, `qms_plan_inspeccion_detalle`, `qms_inspeccion`, `qms_inspeccion_detalle`, `qms_no_conformidad` |
| 5 | PUR | `pur_proveedor`, `pur_proveedor_contacto`, `pur_producto_proveedor`, `pur_solicitud_compra`, `pur_solicitud_compra_detalle`, `pur_cotizacion`, `pur_cotizacion_detalle`, `pur_orden_compra`, `pur_orden_compra_detalle`, `pur_recepcion`, `pur_recepcion_detalle` |
| 6 | LOG | `log_transportista`, `log_vehiculo`, `log_ruta`, `log_guia_remision`, `log_guia_remision_detalle`, `log_despacho`, `log_despacho_guia` |
| 7 | MFG | `mfg_centro_trabajo`, `mfg_operacion`, `mfg_lista_materiales`, `mfg_lista_materiales_detalle`, `mfg_ruta_fabricacion`, `mfg_ruta_fabricacion_detalle`, `mfg_orden_produccion`, `mfg_orden_produccion_operacion`, `mfg_consumo_materiales` |
| 8 | MRP | `mrp_plan_maestro`, `mrp_necesidad_bruta`, `mrp_explosion_materiales`, `mrp_orden_sugerida` |
| 9 | MPS | `mps_pronostico_demanda`, `mps_plan_produccion`, `mps_plan_produccion_detalle` |
| 10 | MNT | `mnt_activo`, `mnt_plan_mantenimiento`, `mnt_orden_trabajo`, `mnt_historial_mantenimiento` |
| 11 | SLS | `sls_cliente`, `sls_cliente_contacto`, `sls_cliente_direccion`, `sls_cotizacion`, `sls_cotizacion_detalle`, `sls_pedido`, `sls_pedido_detalle` |
| 12 | CRM | `crm_campana`, `crm_lead`, `crm_oportunidad`, `crm_actividad` |
| 13 | PRC | `prc_lista_precio`, `prc_lista_precio_detalle`, `prc_promocion` |
| 14 | INV_BILL | `invbill_serie_comprobante`, `invbill_comprobante`, `invbill_comprobante_detalle` |
| 15 | POS | `pos_punto_venta`, `pos_turno_caja`, `pos_venta`, `pos_venta_detalle` |
| 16 | HCM | `hcm_empleado`, `hcm_contrato`, `hcm_concepto_planilla`, `hcm_planilla`, `hcm_planilla_empleado`, `hcm_planilla_detalle`, `hcm_asistencia`, `hcm_vacaciones`, `hcm_prestamo` |
| 17 | FIN | `fin_plan_cuentas`, `fin_periodo_contable`, `fin_asiento_contable`, `fin_asiento_detalle` |
| 18 | TAX | `tax_libro_electronico` |
| 19 | BDG | `bdg_presupuesto`, `bdg_presupuesto_detalle` |
| 20 | CST | `cst_centro_costo_tipo`, `cst_producto_costo` |
| 21–27 | PM/SVC/TKT/BI/DMS/WFL/AUD | 1 tabla cada uno (placeholders o mínimos) |
| — | CFG | `cfg_codigo_secuencia` (fuera del índice) |

**Ausentes:** MES, APS, PLN, ALR, RPT, Event Bus, `cfg_vertical*`, `inv_lote`, `inv_producto_variante`, `wms_oleada`.

---

## 3. Madurez por módulo

| Módulo | Madurez | Nota |
|--------|---------|------|
| ORG | Maduro | Gap documental “1 empresa/BD” vs multiempresa en schema |
| INV | Maduro (no enterprise) | Sin lote AR ni variantes |
| PUR / SLS / INV_BILL / HCM | Maduro | Ciclos completos a nivel tablas |
| WMS / QMS / MFG / LOG / MRP / MPS / MNT / CRM / PRC / POS / FIN / BDG | Básico | Gaps estructurales claros |
| TAX / CST / CFG / WFL / DMS / BI / PM / SVC / TKT | Embrionario | Placeholders o metadata |
| MES / PLN / APS / ALR / RPT / EVT | N/A | No existen |

**Ningún módulo es Enterprise-ready** solo con V010.

---

## 4. Gaps estructurales críticos (industriales)

1. **Lote como string** en movimiento, físico, WMS stock, QMS, recepción, consumo, factura, POS — sin `inv_lote`.
2. **`inv_stock` no lotificado** — FEFO/FIFO operativo imposible.
3. **Variantes** = campos planos `color`/`talla` + JSON.
4. **Sin estrategia de salida** en almacén/ubicación.
5. **Sin oleadas WMS**.
6. **Sin calendario de capacidad** (solo campos estáticos en CT / número en MPS).
7. **Sin MES / OEE**.
8. **Sin Event Bus / ALR**.
9. **Sin control-plane de verticales**.
10. **MRP:** `mrp_necesidad_bruta` y `mrp_explosion_materiales` sin `empresa_id` (inconsistencia Fase 4).

---

## 5. Spillover detectado

| Tipo | Evidencia | Severidad |
|------|-----------|-----------|
| Textil cosmético | Comentarios “Textil…”, ejemplo jerarquía telas; `color`/`talla` | Baja — no hay tablas textiles |
| Fiscal Perú | Ubigeo, SUNAT, PLE, IGV, series | Media — localización, no vertical industrial |
| JSON abuse | BOM sustitutos, WFL, promo, horarios, atributos | Media — deuda de modelado |

El Core **no** es un ERP Textil disfrazado. El riesgo mayor es **sub-modelado industrial genérico**, no spillover de rubro.

---

## 6. Fortalezas a preservar en CORE V2

- Mapa modular amplio (no empezar de cero).
- Consistencia tenant/empresa y soft delete.
- Cabecera-detalle en INV/PUR/SLS/MFG/QMS.
- Flags `maneja_lotes` / `maneja_series` / `maneja_vencimiento` ya anticipan el AR de lote.
- `cfg_codigo_secuencia` como semilla de gobernanza de códigos.
- Separación WMS vs INV ya iniciada.

---

## 7. Implicación para CORE V2

V010 es la **base correcta para extender**, no para reemplazar. El upgrade debe:

1. Formalizar aggregates faltantes (lote, variante).
2. Completar WMS/QMS/MFG→MES/PLN.
3. Añadir infraestructura EVT+ALR y CFG vertical limpio.
4. Corregir inconsistencias (`empresa_id` en MRP, naming).
5. **No** reescribir módulos maduros (ORG, PUR, SLS, HCM) salvo extensión puntual.
