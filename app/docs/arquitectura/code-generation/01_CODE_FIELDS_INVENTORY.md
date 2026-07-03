# F15 — Inventario de campos de código (V010)

**Fase:** F15 — Auditoría arquitectónica del motor de generación de códigos ERP  
**Fuente canónica:** `app/bootstrap_v2/01_schema/V010__tablas_bd_erp_completo.sql`  
**Fecha:** 2026-07-02  
**Alcance:** Solo documentación. Sin cambios a BD, ORM ni código.

---

## 1. Resumen ejecutivo del inventario

| Métrica | Valor |
|---------|-------|
| Tablas ERP en V010 analizadas | 100 (+ `cfg_codigo_secuencia`) |
| Tablas con al menos un campo de código/número de negocio | 79 |
| Campos inventariados en V010 | 113 (111 automáticos + 2 `codigo_qr` NVARCHAR(MAX)) |
| Tabla de configuración de secuencias | `cfg_codigo_secuencia` (no es código de negocio) |

**Criterio de inclusión:** columnas cuyo nombre contiene `codigo_*`, `codigo` (identificador de entidad), `numero_*` (correlativo de documento/proceso), `serie` (numeración fiscal/logística), o `modulo_codigo` (clave compuesta de parámetros).

**Criterio de exclusión parcial:** campos con nombre `codigo_*` que representan **datos externos o técnicos** (SUNAT, QR, hash, GPS, postal, CIIU) se inventarian pero se marcan como *no candidatos al motor* en `02_ENTITY_CLASSIFICATION.md`.

---

## 2. Inventario completo V010

Leyenda columnas:

- **UNIQUE:** constraint que incluye el campo (puede ser compuesto).
- **Índice:** índice no clustered que referencia explícitamente la columna.

### 2.1 Catálogos globales (`cat_*`)

| Tabla | Columna | Tipo | Nullable | UNIQUE | Índice |
|-------|---------|------|----------|--------|--------|
| `cat_moneda` | `codigo` | NVARCHAR(3) | NOT NULL | `UQ_moneda_codigo` | — |
| `cat_pais` | `codigo_iso2` | NVARCHAR(2) | NOT NULL | `UQ_pais_iso2` | — |
| `cat_pais` | `codigo_iso3` | NVARCHAR(3) | NOT NULL | — | — |
| `cat_departamento` | `codigo` | NVARCHAR(10) | NOT NULL | — | — |
| `cat_provincia` | `codigo` | NVARCHAR(10) | NOT NULL | — | — |
| `cat_distrito` | `codigo` | NVARCHAR(10) | NOT NULL | — | — |

> Los catálogos geográficos no declaran UNIQUE global en V010; la unicidad operativa depende de la jerarquía padre (no modelada como UQ compuesta en el DDL auditado).

### 2.2 Organización (`org_*`)

| Tabla | Columna | Tipo | Nullable | UNIQUE | Índice |
|-------|---------|------|----------|--------|--------|
| `org_empresa` | `codigo_empresa` | NVARCHAR(20) | NOT NULL | `UQ_org_empresa_cliente` (cliente_id, codigo_empresa) | — |
| `org_empresa` | `codigo_ciiu` | NVARCHAR(10) | NULL | — | — |
| `org_empresa` | `codigo_postal` | NVARCHAR(10) | NULL | — | — |
| `org_centro_costo` | `codigo` | NVARCHAR(20) | NOT NULL | `UQ_cc_codigo` (cliente_id, empresa_id, codigo) | — |
| `org_sucursal` | `codigo` | NVARCHAR(20) | NOT NULL | `UQ_sucursal_codigo` | — |
| `org_sucursal` | `codigo_postal` | NVARCHAR(10) | NULL | — | — |
| `org_departamento` | `codigo` | NVARCHAR(20) | NOT NULL | `UQ_dpto_codigo` | — |
| `org_cargo` | `codigo` | NVARCHAR(20) | NOT NULL | `UQ_cargo_codigo` | — |
| `org_parametro_sistema` | `modulo_codigo` | NVARCHAR(10) | NOT NULL | `UQ_parametro` (cliente_id, empresa_id, modulo_codigo, codigo_parametro) | `IDX_parametro_empresa`, `IDX_parametro_modulo` |
| `org_parametro_sistema` | `codigo_parametro` | NVARCHAR(50) | NOT NULL | `UQ_parametro` | `IDX_parametro_modulo` |

### 2.3 Inventario (`inv_*`)

| Tabla | Columna | Tipo | Nullable | UNIQUE | Índice |
|-------|---------|------|----------|--------|--------|
| `inv_categoria_producto` | `codigo` | NVARCHAR(20) | NOT NULL | `UQ_cat_codigo` | — |
| `inv_unidad_medida` | `codigo` | NVARCHAR(10) | NOT NULL | `UQ_um_codigo` | — |
| `inv_producto` | `codigo_sku` | NVARCHAR(50) | NOT NULL | `UQ_prod_sku` | — |
| `inv_producto` | `codigo_barra` | NVARCHAR(50) | NULL | — | `IDX_prod_codigo_barra` (filtered) |
| `inv_producto` | `codigo_interno` | NVARCHAR(30) | NULL | — | — |
| `inv_producto` | `codigo_fabricante` | NVARCHAR(50) | NULL | — | — |
| `inv_producto` | `codigo_sunat` | NVARCHAR(10) | NULL | — | — |
| `inv_almacen` | `codigo` | NVARCHAR(20) | NOT NULL | `UQ_alm_codigo` | — |
| `inv_tipo_movimiento` | `codigo` | NVARCHAR(20) | NOT NULL | `UQ_tm_codigo` | — |
| `inv_movimiento` | `numero_movimiento` | NVARCHAR(20) | NOT NULL | `UQ_mov_numero` | — |
| `inv_movimiento_detalle` | `numero_serie` | NVARCHAR(100) | NULL | — | — |
| `inv_inventario_fisico` | `numero_inventario` | NVARCHAR(20) | NOT NULL | `UQ_invfis_numero` | — |

### 2.4 WMS (`wms_*`)

| Tabla | Columna | Tipo | Nullable | UNIQUE | Índice |
|-------|---------|------|----------|--------|--------|
| `wms_zona_almacen` | `codigo` | NVARCHAR(20) | NOT NULL | `UQ_zona_codigo` (cliente_id, almacen_id, codigo) | — |
| `wms_ubicacion` | `codigo_ubicacion` | NVARCHAR(30) | NOT NULL | `UQ_ubic_codigo` | — |
| `wms_stock_ubicacion` | `numero_serie` | NVARCHAR(100) | NULL | — | — |
| `wms_tarea` | `numero_tarea` | NVARCHAR(20) | NOT NULL | `UQ_tarea_numero` (cliente_id, almacen_id, numero_tarea) | — |

### 2.5 Calidad (`qms_*`)

| Tabla | Columna | Tipo | Nullable | UNIQUE | Índice |
|-------|---------|------|----------|--------|--------|
| `qms_parametro_calidad` | `codigo` | NVARCHAR(20) | NOT NULL | `UQ_qms_param_codigo` | — |
| `qms_plan_inspeccion` | `codigo` | NVARCHAR(20) | NOT NULL | `UQ_qms_plan_codigo` | — |
| `qms_inspeccion` | `numero_inspeccion` | NVARCHAR(20) | NOT NULL | `UQ_qms_insp_numero` | — |
| `qms_no_conformidad` | `numero_nc` | NVARCHAR(20) | NOT NULL | `UQ_qms_nc_numero` | — |

### 2.6 Compras (`pur_*`)

| Tabla | Columna | Tipo | Nullable | UNIQUE | Índice |
|-------|---------|------|----------|--------|--------|
| `pur_proveedor` | `codigo_proveedor` | NVARCHAR(20) | NOT NULL | `UQ_prov_codigo` | — |
| `pur_proveedor` | `numero_documento` | NVARCHAR(20) | NOT NULL | `UQ_prov_documento` (tipo_documento, numero_documento) | `IDX_prov_documento` |
| `pur_proveedor` | `numero_cuenta` | NVARCHAR(30) | NULL | — | — |
| `pur_producto_proveedor` | `codigo_proveedor` | NVARCHAR(50) | NULL | — | — |
| `pur_solicitud_compra` | `numero_solicitud` | NVARCHAR(20) | NOT NULL | `UQ_solcomp_numero` | — |
| `pur_cotizacion` | `numero_cotizacion` | NVARCHAR(20) | NOT NULL | `UQ_cotiz_numero` | — |
| `pur_orden_compra` | `numero_oc` | NVARCHAR(20) | NOT NULL | `UQ_oc_numero` | — |
| `pur_recepcion` | `numero_recepcion` | NVARCHAR(20) | NOT NULL | `UQ_recep_numero` | — |

### 2.7 Logística (`log_*`)

| Tabla | Columna | Tipo | Nullable | UNIQUE | Índice |
|-------|---------|------|----------|--------|--------|
| `log_transportista` | `codigo_transportista` | NVARCHAR(20) | NOT NULL | `UQ_transp_codigo` | — |
| `log_transportista` | `numero_documento` | NVARCHAR(20) | NOT NULL | — | — |
| `log_transportista` | `numero_mtc` | NVARCHAR(30) | NULL | — | — |
| `log_vehiculo` | `codigo_gps` | NVARCHAR(50) | NULL | — | — |
| `log_ruta` | `codigo_ruta` | NVARCHAR(20) | NOT NULL | `UQ_logruta_codigo` | — |
| `log_guia_remision` | `serie` | NVARCHAR(4) | NOT NULL | `UQ_guia_numero` (serie, numero) | — |
| `log_guia_remision` | `numero` | NVARCHAR(10) | NOT NULL | `UQ_guia_numero` | `IDX_guia_numero` (numero_completo computed) |
| `log_guia_remision` | `codigo_hash` | NVARCHAR(100) | NULL | — | — |
| `log_guia_remision` | `codigo_qr` | NVARCHAR(MAX) | NULL | — | — |
| `log_despacho` | `numero_despacho` | NVARCHAR(20) | NOT NULL | `UQ_desp_numero` | — |

### 2.8 Manufactura (`mfg_*`, `mrp_*`, `mps_*`)

| Tabla | Columna | Tipo | Nullable | UNIQUE | Índice |
|-------|---------|------|----------|--------|--------|
| `mfg_centro_trabajo` | `codigo` | NVARCHAR(20) | NOT NULL | `UQ_ct_codigo` | — |
| `mfg_operacion` | `codigo` | NVARCHAR(20) | NOT NULL | `UQ_oper_codigo` | — |
| `mfg_lista_materiales` | `codigo_bom` | NVARCHAR(20) | NOT NULL | `UQ_bom_codigo` | — |
| `mfg_ruta_fabricacion` | `codigo_ruta` | NVARCHAR(20) | NOT NULL | `UQ_rutafab_codigo` | — |
| `mfg_orden_produccion` | `numero_op` | NVARCHAR(20) | NOT NULL | `UQ_op_numero` | — |
| `mrp_plan_maestro` | `codigo_plan` | NVARCHAR(20) | NOT NULL | `UQ_planmrp_codigo` | — |
| `mps_plan_produccion` | `codigo_plan` | NVARCHAR(20) | NOT NULL | `UQ_planprod_codigo` | — |

### 2.9 Mantenimiento (`mnt_*`)

| Tabla | Columna | Tipo | Nullable | UNIQUE | Índice |
|-------|---------|------|----------|--------|--------|
| `mnt_activo` | `codigo_activo` | NVARCHAR(20) | NOT NULL | `UQ_activo_codigo` | — |
| `mnt_activo` | `numero_serie` | NVARCHAR(50) | NULL | — | — |
| `mnt_plan_mantenimiento` | `codigo_plan` | NVARCHAR(20) | NOT NULL | `UQ_planmnt_codigo` | — |
| `mnt_orden_trabajo` | `numero_ot` | NVARCHAR(20) | NOT NULL | `UQ_ot_numero` | — |

### 2.10 Ventas y CRM (`sls_*`, `crm_*`, `prc_*`)

| Tabla | Columna | Tipo | Nullable | UNIQUE | Índice |
|-------|---------|------|----------|--------|--------|
| `sls_cliente` | `codigo_cliente` | NVARCHAR(20) | NOT NULL | `UQ_cltvta_codigo` | — |
| `sls_cliente` | `numero_documento` | NVARCHAR(20) | NOT NULL | `UQ_cltvta_documento` | `IDX_cltvta_documento` |
| `sls_cliente` | `numero_cuenta` | NVARCHAR(30) | NULL | — | — |
| `sls_cliente_direccion` | `codigo_direccion` | NVARCHAR(20) | NULL | — | — |
| `sls_cliente_direccion` | `codigo_postal` | NVARCHAR(10) | NULL | — | — |
| `sls_cotizacion` | `numero_cotizacion` | NVARCHAR(20) | NOT NULL | `UQ_cotvta_numero` | — |
| `sls_pedido` | `numero_pedido` | NVARCHAR(20) | NOT NULL | `UQ_pedido_numero` | — |
| `crm_campana` | `codigo_campana` | NVARCHAR(20) | NOT NULL | `UQ_campana_codigo` | — |
| `crm_oportunidad` | `numero_oportunidad` | NVARCHAR(20) | NOT NULL | `UQ_opor_numero` | — |
| `prc_lista_precio` | `codigo_lista` | NVARCHAR(20) | NOT NULL | `UQ_listaprc_codigo` | — |
| `prc_promocion` | `codigo_promocion` | NVARCHAR(20) | NOT NULL | `UQ_promo_codigo` | — |
| `prc_promocion` | `codigo_cupon` | NVARCHAR(30) | NULL | — | — |

### 2.11 Facturación electrónica (`invbill_*`)

| Tabla | Columna | Tipo | Nullable | UNIQUE | Índice |
|-------|---------|------|----------|--------|--------|
| `invbill_serie_comprobante` | `serie` | NVARCHAR(4) | NOT NULL | `UQ_serie` (tipo_comprobante, serie) | `IDX_serie_tipo` |
| `invbill_serie_comprobante` | `numero_final` | INT | NULL | — | — |
| `invbill_comprobante` | `serie` | NVARCHAR(4) | NOT NULL | `UQ_comp_numero` (tipo, serie, numero) | — |
| `invbill_comprobante` | `numero` | NVARCHAR(10) | NOT NULL | `UQ_comp_numero` | `IDX_comp_numero` (numero_completo) |
| `invbill_comprobante` | `codigo_hash` | NVARCHAR(100) | NULL | — | — |
| `invbill_comprobante` | `codigo_qr` | NVARCHAR(MAX) | NULL | — | — |
| `invbill_comprobante` | `codigo_respuesta_sunat` | NVARCHAR(10) | NULL | — | — |
| `invbill_comprobante_detalle` | `codigo_producto` | NVARCHAR(50) | NULL | — | — |
| `invbill_comprobante_detalle` | `codigo_producto_sunat` | NVARCHAR(10) | NULL | — | — |

### 2.12 POS (`pos_*`)

| Tabla | Columna | Tipo | Nullable | UNIQUE | Índice |
|-------|---------|------|----------|--------|--------|
| `pos_punto_venta` | `codigo_punto_venta` | NVARCHAR(20) | NOT NULL | `UQ_pv_codigo` | — |
| `pos_punto_venta` | `codigo_terminal` | NVARCHAR(50) | NULL | — | — |
| `pos_turno_caja` | `numero_turno` | NVARCHAR(20) | NOT NULL | `UQ_turno_numero` (punto_venta_id) | — |
| `pos_venta` | `numero_venta` | NVARCHAR(20) | NOT NULL | `UQ_posvta_numero` | — |
| `pos_venta` | `numero_comprobante` | NVARCHAR(20) | NULL | — | — |

### 2.13 RRHH (`hcm_*`)

| Tabla | Columna | Tipo | Nullable | UNIQUE | Índice |
|-------|---------|------|----------|--------|--------|
| `hcm_empleado` | `codigo_empleado` | NVARCHAR(20) | NOT NULL | `UQ_emp_codigo` | — |
| `hcm_empleado` | `numero_documento` | NVARCHAR(20) | NOT NULL | `UQ_emp_documento` | `IDX_emp_documento` |
| `hcm_empleado` | `numero_cuenta` | NVARCHAR(30) | NULL | — | — |
| `hcm_contrato` | `numero_contrato` | NVARCHAR(20) | NOT NULL | `UQ_contrato_numero` | — |
| `hcm_concepto_planilla` | `codigo_concepto` | NVARCHAR(20) | NOT NULL | `UQ_concepto_codigo` | — |
| `hcm_concepto_planilla` | `codigo_plame` | NVARCHAR(10) | NULL | — | — |
| `hcm_planilla` | `numero_planilla` | NVARCHAR(20) | NOT NULL | `UQ_planilla_numero` | — |
| `hcm_planilla_empleado` | `numero_operacion` | NVARCHAR(50) | NULL | — | — |
| `hcm_prestamo` | `numero_prestamo` | NVARCHAR(20) | NOT NULL | `UQ_prestamo_numero` | — |
| `hcm_prestamo` | `numero_cuotas` | INT | NOT NULL | — | — |

### 2.14 Finanzas, impuestos, otros módulos

| Tabla | Columna | Tipo | Nullable | UNIQUE | Índice |
|-------|---------|------|----------|--------|--------|
| `fin_plan_cuentas` | `codigo_cuenta` | NVARCHAR(20) | NOT NULL | `UQ_cuenta_codigo` | — |
| `fin_plan_cuentas` | `codigo_sunat` | NVARCHAR(10) | NULL | — | — |
| `fin_asiento_contable` | `numero_asiento` | NVARCHAR(20) | NOT NULL | `UQ_asiento_numero` | — |
| `tax_libro_electronico` | `codigo_respuesta_sunat` | NVARCHAR(10) | NULL | — | — |
| `bdg_presupuesto` | `codigo_presupuesto` | NVARCHAR(20) | NOT NULL | `UQ_bdg_codigo` | — |
| `cst_centro_costo_tipo` | `codigo` | NVARCHAR(20) | NOT NULL | `UQ_cctipo_codigo` | — |
| `pm_proyecto` | `codigo_proyecto` | NVARCHAR(20) | NOT NULL | `UQ_proy_codigo` | — |
| `svc_orden_servicio` | `numero_os` | NVARCHAR(20) | NOT NULL | `UQ_os_numero` | — |
| `tkt_ticket` | `numero_ticket` | NVARCHAR(20) | NOT NULL | `UQ_tkt_numero` | — |
| `bi_reporte` | `codigo_reporte` | NVARCHAR(20) | NOT NULL | `UQ_bi_codigo` | — |
| `dms_documento` | `codigo_documento` | NVARCHAR(20) | NULL | — | — |
| `wfl_flujo_trabajo` | `codigo_flujo` | NVARCHAR(20) | NOT NULL | `UQ_wfl_codigo` | — |

### 2.15 Configuración de secuencias (tabla técnica)

| Tabla | Columna | Tipo | Nullable | UNIQUE | Índice |
|-------|---------|------|----------|--------|--------|
| `cfg_codigo_secuencia` | `entidad` | NVARCHAR(50) | NOT NULL | `UNIQUE(cliente_id, empresa_id, entidad)` | — |
| `cfg_codigo_secuencia` | `prefijo` | NVARCHAR(5) | NOT NULL | — | — |
| `cfg_codigo_secuencia` | `longitud_numero` | INT | NOT NULL | — | — |
| `cfg_codigo_secuencia` | `ultimo_numero` | INT | NOT NULL | — | — |
| `cfg_codigo_secuencia` | `separador` | NVARCHAR(2) | NULL | — | — |

> Esta tabla almacena **estado de secuencia**, no códigos de negocio en sí. Su diseño definitivo queda para Fase 2.

---

## 3. Anexo — Campos en BD central (V020, fuera de V010)

Relevantes para contexto multi-tenant; **no** forman parte del motor ERP operativo por empresa, pero comparten el concepto de “código”:

| Tabla (V020) | Columna | Tipo | Nullable | UNIQUE | Índice |
|--------------|---------|------|----------|--------|--------|
| `cliente` | `codigo_cliente` | NVARCHAR(20) | NOT NULL | UNIQUE global | `IDX_cliente_codigo` |
| `modulo` | `codigo` | NVARCHAR(30) | NOT NULL | UNIQUE global | `IDX_modulo_codigo` |
| `modulo_seccion` | `codigo` | NVARCHAR(30) | NOT NULL | `UQ_seccion_modulo_codigo` | — |
| `permiso` | `codigo` | NVARCHAR(50) | NULL | — | — |
| `rol` | `codigo_rol` | NVARCHAR(30) | NULL | — | `IDX_rol_codigo` (filtered) |

---

## 4. Patrones de unicidad detectados en V010

| Patrón UNIQUE | Ejemplos | Cantidad aprox. |
|---------------|----------|-----------------|
| `(cliente_id, empresa_id, codigo*)` | Maestros ORG, INV, PUR, SLS | Mayoría |
| `(cliente_id, codigo_empresa)` | `org_empresa` | 1 (scope tenant) |
| `(cliente_id, empresa_id, numero_*)` | Documentos transaccionales | ~25 |
| `(cliente_id, empresa_id, serie, numero)` | Guías, comprobantes | 2 |
| `(cliente_id, almacen_id, codigo*)` | WMS zona, ubicación | 2 |
| `(cliente_id, almacen_id, numero_tarea)` | WMS tarea | 1 |
| `(cliente_id, empresa_id, tipo_documento, numero_documento)` | Terceros (RUC/DNI) | 2 |
| Global catálogo | `cat_moneda`, `cat_pais` | 2 |

---

## 5. Longitudes predominantes

| Longitud | Uso típico |
|----------|------------|
| NVARCHAR(3) | Moneda ISO |
| NVARCHAR(10) | Unidad medida, números fiscales cortos, ubigeo |
| NVARCHAR(20) | **Estándar dominante** maestros y correlativos |
| NVARCHAR(30) | Ubicación WMS, cuentas bancarias |
| NVARCHAR(50) | SKU extendido, códigos proveedor en línea |
| NVARCHAR(100)+ | Series de lote, hashes |

---

## 6. Observaciones para fases posteriores

1. **Homogeneidad:** el 85% de correlativos de documento usan `NVARCHAR(20)`; comprobantes fiscales usan `serie` (4) + `numero` (10).
2. **Campos homónimos:** `codigo_proveedor` en `pur_proveedor` (maestro) vs `pur_producto_proveedor` (referencia cruzada SKU proveedor) tienen semántica distinta y longitudes distintas (20 vs 50).
3. **`numero_documento`:** en terceros es identidad legal (RUC/DNI), no correlativo interno.
4. **`numero_serie`:** en inventario es trazabilidad de lote/serie física, no numeración documental.

---

*Documento generado en auditoría F15. Próximo paso: clasificación funcional en `02_ENTITY_CLASSIFICATION.md`.*
