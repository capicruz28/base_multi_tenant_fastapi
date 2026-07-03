# F15 — Clasificación funcional de entidades con códigos

**Fase:** F15 — Auditoría arquitectónica  
**Fuente:** `01_CODE_FIELDS_INVENTORY.md` + verificación de uso en servicios  
**Fecha:** 2026-07-02

---

## 1. Criterios de clasificación

| Grupo | Definición | Motor centralizado (Fase 2) |
|-------|------------|----------------------------|
| **A. Catálogo oficial** | Datos de referencia estandarizados (ISO, SUNAT catálogo, geografía). Gestionados por plataforma o sincronización global. | **No** |
| **B. Maestro ERP** | Entidades de configuración/maestro del tenant con código interno persistente y UNIQUE de negocio. | **Sí** (con políticas por subtipo) |
| **C. Documento** | Transacciones o registros de proceso con correlativo (`numero_*`, `serie`+`numero`). | **Sí** (prioridad alta) |
| **D. No aplica** | Técnicos, regulatorios externos, snapshots, direcciones, trazabilidad física. | **No** |

---

## 2. Clasificación por tabla (V010)

### A — Catálogo oficial

| Tabla | Campo(s) código | Justificación |
|-------|-----------------|---------------|
| `cat_moneda` | `codigo` | Código ISO 4217; catálogo global sincronizable (`catalog_sync`). |
| `cat_pais` | `codigo_iso2`, `codigo_iso3` | Estándares ISO 3166; no generados por tenant. |
| `cat_departamento` | `codigo` | División política oficial (INEI/ubigeo); seed plataforma. |
| `cat_provincia` | `codigo` | Idem. |
| `cat_distrito` | `codigo` | Idem. |

**Anexo V020 (plataforma):** `modulo.codigo`, `modulo_seccion.codigo`, `permiso.codigo` — catálogo IAM, no ERP.

---

### B — Maestro ERP

| Tabla | Campo(s) | Subtipo | Justificación |
|-------|----------|---------|---------------|
| `org_empresa` | `codigo_empresa` | Estructura | Identificador interno de empresa dentro del tenant; UNIQUE por `cliente_id`. |
| `org_sucursal` | `codigo` | Estructura | Punto operativo; referenciado en POS, series fiscales. |
| `org_centro_costo` | `codigo` | Estructura | Imputación contable/operativa. |
| `org_departamento` | `codigo` | RRHH/estructura | Área organizacional (distinto de `cat_departamento` geográfico). |
| `org_cargo` | `codigo` | RRHH | Puesto de trabajo. |
| `inv_categoria_producto` | `codigo` | INV | Clasificación de productos. |
| `inv_unidad_medida` | `codigo` | INV | UM interna (puede alinearse a SUNAT pero es maestro tenant). |
| `inv_producto` | `codigo_sku` | INV | Identificador principal del producto en el ERP. |
| `inv_almacen` | `codigo` | INV | Almacén físico/lógico. |
| `inv_tipo_movimiento` | `codigo` | INV/config | Catálogo operativo del tenant (COMP, VENT, etc.). |
| `wms_zona_almacen` | `codigo` | WMS | Subdivisión de almacén. |
| `wms_ubicacion` | `codigo_ubicacion` | WMS | Slot físico (pasillo-rack-nivel). |
| `pur_proveedor` | `codigo_proveedor` | PUR | Código interno del proveedor (≠ RUC). |
| `sls_cliente` | `codigo_cliente` | SLS | Código interno del cliente de venta (≠ RUC/DNI). |
| `hcm_empleado` | `codigo_empleado` | HCM | Identificador interno de empleado. |
| `log_transportista` | `codigo_transportista` | LOG | Maestro transportista. |
| `log_ruta` | `codigo_ruta` | LOG | Maestro de ruta de distribución. |
| `mfg_centro_trabajo` | `codigo` | MFG | Recurso productivo. |
| `mfg_operacion` | `codigo` | MFG | Operación estándar. |
| `mfg_lista_materiales` | `codigo_bom` | MFG | BOM maestro. |
| `mfg_ruta_fabricacion` | `codigo_ruta` | MFG | Ruta de fabricación. |
| `mnt_activo` | `codigo_activo` | MNT | Activo mantenible. |
| `mnt_plan_mantenimiento` | `codigo_plan` | MNT | Plan preventivo. |
| `mrp_plan_maestro` | `codigo_plan` | MRP | Plan maestro (cabecera de planificación). |
| `mps_plan_produccion` | `codigo_plan` | MPS | Plan de producción. |
| `crm_campana` | `codigo_campana` | CRM | Campaña comercial. |
| `prc_lista_precio` | `codigo_lista` | PRC | Lista de precios. |
| `prc_promocion` | `codigo_promocion` | PRC | Promoción. |
| `fin_plan_cuentas` | `codigo_cuenta` | FIN | Cuenta del plan contable (jerárquica). |
| `hcm_concepto_planilla` | `codigo_concepto` | HCM | Concepto de planilla. |
| `qms_parametro_calidad` | `codigo` | QMS | Parámetro de calidad. |
| `qms_plan_inspeccion` | `codigo` | QMS | Plan de inspección. |
| `pos_punto_venta` | `codigo_punto_venta` | POS | Terminal/caja. |
| `invbill_serie_comprobante` | `serie` | Fiscal/config | Serie autorizada; maestro de numeración fiscal. |
| `bdg_presupuesto` | `codigo_presupuesto` | BDG | Presupuesto. |
| `cst_centro_costo_tipo` | `codigo` | CST | Tipo analítico de costo. |
| `pm_proyecto` | `codigo_proyecto` | PM | Proyecto. |
| `bi_reporte` | `codigo_reporte` | BI | Definición de reporte. |
| `wfl_flujo_trabajo` | `codigo_flujo` | WFL | Definición de flujo. |
| `dms_documento` | `codigo_documento` | DMS | Documento gestionado (opcional). |

**Campos maestro con semántica mixta en `inv_producto`:**

| Campo | Clasificación | Nota |
|-------|---------------|------|
| `codigo_sku` | B — Maestro | Candidato principal al motor. |
| `codigo_interno` | B — Maestro opcional | Alias interno; puede ser manual o derivado. |
| `codigo_barra` | D — Externo | EAN/UPC del fabricante; no secuencial. |
| `codigo_fabricante` | D — Externo | Part number proveedor. |

---

### C — Documento (correlativo de proceso)

| Tabla | Campo(s) | Justificación |
|-------|----------|---------------|
| `inv_movimiento` | `numero_movimiento` | Documento de inventario; flujo transaccional INV. |
| `inv_inventario_fisico` | `numero_inventario` | Conteo físico; proceso con estados. |
| `pur_solicitud_compra` | `numero_solicitud` | Documento de compras. |
| `pur_cotizacion` | `numero_cotizacion` | Cotización proveedor. |
| `pur_orden_compra` | `numero_oc` | Orden de compra. |
| `pur_recepcion` | `numero_recepcion` | Recepción de mercancía. |
| `log_guia_remision` | `serie`, `numero` | Guía de remisión electrónica. |
| `log_despacho` | `numero_despacho` | Despacho logístico. |
| `mfg_orden_produccion` | `numero_op` | Orden de producción. |
| `mnt_orden_trabajo` | `numero_ot` | Orden de mantenimiento. |
| `sls_cotizacion` | `numero_cotizacion` | Cotización de venta. |
| `sls_pedido` | `numero_pedido` | Pedido de venta. |
| `crm_oportunidad` | `numero_oportunidad` | Oportunidad CRM. |
| `invbill_comprobante` | `serie`, `numero` | Comprobante fiscal electrónico. |
| `pos_turno_caja` | `numero_turno` | Turno de caja. |
| `pos_venta` | `numero_venta` | Transacción POS. |
| `hcm_contrato` | `numero_contrato` | Contrato laboral. |
| `hcm_planilla` | `numero_planilla` | Periodo de planilla. |
| `hcm_prestamo` | `numero_prestamo` | Préstamo al empleado. |
| `fin_asiento_contable` | `numero_asiento` | Asiento contable. |
| `qms_inspeccion` | `numero_inspeccion` | Inspección de calidad. |
| `qms_no_conformidad` | `numero_nc` | No conformidad. |
| `wms_tarea` | `numero_tarea` | Tarea de almacén. |
| `svc_orden_servicio` | `numero_os` | Orden de servicio. |
| `tkt_ticket` | `numero_ticket` | Ticket de soporte. |

---

### D — No aplica (excluidos del motor)

| Tabla | Campo(s) | Motivo de exclusión |
|-------|----------|---------------------|
| `org_empresa` | `codigo_ciiu`, `codigo_postal` | Taxonomía/dirección externa. |
| `org_sucursal` | `codigo_postal` | Dirección. |
| `org_parametro_sistema` | `modulo_codigo`, `codigo_parametro` | Clave de configuración técnica, no entidad de negocio. |
| `inv_producto` | `codigo_sunat`, `codigo_barra`, `codigo_fabricante` | Códigos regulatorios o del fabricante. |
| `inv_movimiento_detalle` | `numero_serie` | Serie/lote de producto físico. |
| `wms_stock_ubicacion` | `numero_serie` | Trazabilidad de inventario. |
| `mnt_activo` | `numero_serie` | Serie del fabricante del activo. |
| `pur_proveedor`, `sls_cliente`, `hcm_empleado`, `log_transportista` | `numero_documento` | RUC/DNI/CE — identidad legal, no correlativo. |
| `pur_proveedor`, `sls_cliente`, `hcm_empleado` | `numero_cuenta` | Cuenta bancaria. |
| `pur_producto_proveedor` | `codigo_proveedor` | SKU del proveedor (referencia cruzada). |
| `sls_cliente_direccion` | `codigo_direccion`, `codigo_postal` | Dirección de entrega. |
| `log_transportista` | `numero_mtc` | Registro regulatorio MTC. |
| `log_vehiculo` | `codigo_gps` | Identificador de dispositivo GPS. |
| `log_guia_remision`, `invbill_comprobante` | `codigo_hash`, `codigo_qr` | Artefactos de firma/OSE. |
| `invbill_comprobante`, `tax_libro_electronico` | `codigo_respuesta_sunat` | Respuesta de API SUNAT. |
| `invbill_comprobante_detalle` | `codigo_producto`, `codigo_producto_sunat` | Snapshot en línea de factura. |
| `fin_plan_cuentas` | `codigo_sunat` | Código PCGE/SUNAT de referencia. |
| `hcm_concepto_planilla` | `codigo_plame` | Código PLAME oficial. |
| `hcm_planilla_empleado` | `numero_operacion` | Referencia bancaria de pago. |
| `hcm_prestamo` | `numero_cuotas` | Cantidad entera, no código. |
| `pos_punto_venta` | `codigo_terminal` | ID de hardware. |
| `pos_venta` | `numero_comprobante` | Referencia al comprobante fiscal (derivado). |
| `prc_promocion` | `codigo_cupon` | Cupón promocional (puede ser campaña externa). |
| `invbill_serie_comprobante` | `numero_final` | Límite autorizado SUNAT, no correlativo. |
| `cfg_codigo_secuencia` | (todos) | Tabla de estado del motor, no entidad de negocio. |

**Anexo V020:** `cliente.codigo_cliente` — identificador SaaS del tenant (onboarding manual/plataforma), **fuera** del motor ERP por empresa.

---

## 3. Resumen cuantitativo

| Grupo | Tablas distintas | Campos |
|-------|------------------|--------|
| A — Catálogo oficial | 5 (+ IAM V020) | 7 |
| B — Maestro ERP | 38 | ~42 |
| C — Documento | 24 | ~27 |
| D — No aplica | 22 | ~37 |

> Un mismo campo puede aparecer en análisis de inventario y clasificarse D aunque el nombre contenga `codigo_`.

---

## 4. Módulos implementados vs. modelo completo

| Módulo | Maestros con servicio + validación UNIQUE | Documentos con generación |
|--------|-------------------------------------------|----------------------------|
| ORG | empresa, sucursal, centro_costo, departamento, cargo | — |
| INV | producto (SKU) | movimiento (manual), estorno (timestamp), inv. físico aprobación (timestamp) |
| PUR | — | recepción → deriva movimiento por concatenación |
| SLS | — | pedido derivado de cotización (`PED-{cot}`) |
| Resto V010 | Sin servicios auditados en runtime | Sin generación |

---

## 5. Implicancia para el estándar F15

1. **Separar tres familias:** catálogo global (A), código maestro (B), correlativo documental (C).
2. **No unificar** identidad legal (`numero_documento`) con correlativos internos (`numero_oc`).
3. **Tratar fiscal** (`invbill_*`, `log_guia_remision`) como subfamilia C con reglas de serie y numeración legal, no como maestro B.
4. **WMS** introduce scope por `almacen_id` — clasificación B/C pero dimensión de secuencia distinta a `empresa_id`.

---

*Ver alcance del motor en decisión de secuencia: `03_SEQUENCE_SCOPE.md`.*
