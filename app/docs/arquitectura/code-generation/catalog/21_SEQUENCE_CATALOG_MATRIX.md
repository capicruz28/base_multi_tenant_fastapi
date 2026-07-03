# F16A — Matriz completa del SequenceCatalog

**Fase:** F16A  
**Fecha:** 2026-07-03  
**Versión catálogo:** `1.0.0`  
**Entradas activas:** 63  
**Base:** F15 `08`, F16 `13`, F15A políticas congeladas

---

## 1. Leyenda de columnas

| Columna | Significado |
|---------|-------------|
| **policy** | AUTO_REQUIRED / AUTO_DEFAULT |
| **scope** | TENANT, EMPRESA, ALMACEN, PUNTO_VENTA, SERIE_FISCAL |
| **family** | F1–F5 (`19`) |
| **store** | CFG / FISCAL |
| **fmt** | formatter_profile |
| **par** | parser_profile |
| **val** | validator_profile |
| **preview** | supports_preview |
| **manual** | allow_manual |
| **align** | align_on_manual / supports_high_water |

Perfiles: ver `20_SEQUENCE_COMPONENTS.md`.

---

## 2. F1 — Maestros (AUTO_DEFAULT)

| sequence_key | code_column | policy | scope | family | store | fmt | par | val | preview | manual | align | prefix | pad | max_len |
|--------------|-------------|--------|-------|--------|-------|-----|-----|-----|---------|--------|-------|--------|-----|---------|
| `org_empresa` | codigo_empresa | AUTO_DEFAULT | TENANT | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | EMP | 3 | 20 |
| `org_sucursal` | codigo | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | SUC | 3 | 20 |
| `org_centro_costo` | codigo | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | CC | 3 | 20 |
| `org_departamento` | codigo | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | DEP | 3 | 20 |
| `org_cargo` | codigo | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | CAR | 3 | 20 |
| `inv_categoria_producto` | codigo | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | CAT | 3 | 20 |
| `inv_unidad_medida` | codigo | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | UM | 3 | 10 |
| `inv_producto` | codigo_sku | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | P | 5 | 50 |
| `inv_almacen` | codigo | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | ALM | 3 | 20 |
| `inv_tipo_movimiento` | codigo | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | TM | 3 | 20 |
| `pur_proveedor` | codigo_proveedor | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | PROV | 4 | 20 |
| `sls_cliente` | codigo_cliente | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | CLI | 4 | 20 |
| `hcm_empleado` | codigo_empleado | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | EMP | 4 | 20 |
| `log_transportista` | codigo_transportista | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | TR | 4 | 20 |
| `log_ruta` | codigo_ruta | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | RUT | 4 | 20 |
| `mfg_centro_trabajo` | codigo | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | CT | 3 | 20 |
| `mfg_operacion` | codigo | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | OP | 3 | 20 |
| `mfg_lista_materiales` | codigo_bom | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | BOM | 4 | 20 |
| `mfg_ruta_fabricacion` | codigo_ruta | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | RF | 4 | 20 |
| `mnt_activo` | codigo_activo | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | ACT | 4 | 20 |
| `mnt_plan_mantenimiento` | codigo_plan | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | PM | 4 | 20 |
| `mrp_plan_maestro` | codigo_plan | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | MRP | 4 | 20 |
| `mps_plan_produccion` | codigo_plan | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | MPS | 4 | 20 |
| `crm_campana` | codigo_campana | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | CMP | 4 | 20 |
| `prc_lista_precio` | codigo_lista | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | LP | 4 | 20 |
| `prc_promocion` | codigo_promocion | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | PRM | 4 | 20 |
| `fin_plan_cuentas` | codigo_cuenta | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | — | 6 | 20 |
| `hcm_concepto_planilla` | codigo_concepto | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | CON | 4 | 20 |
| `qms_parametro_calidad` | codigo | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | QMP | 4 | 20 |
| `qms_plan_inspeccion` | codigo | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | QPL | 4 | 20 |
| `pos_punto_venta` | codigo_punto_venta | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | PV | 3 | 20 |
| `bdg_presupuesto` | codigo_presupuesto | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | PRE | 4 | 20 |
| `cst_centro_costo_tipo` | codigo | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | CCT | 3 | 20 |
| `pm_proyecto` | codigo_proyecto | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | PRY | 4 | 20 |
| `bi_reporte` | codigo_reporte | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | RPT | 4 | 20 |
| `wfl_flujo_trabajo` | codigo_flujo | AUTO_DEFAULT | EMPRESA | F1 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | WFL | 4 | 20 |

---

## 3. F4 — Maestros WMS (AUTO_DEFAULT, scope ALMACEN)

| sequence_key | code_column | policy | scope | family | store | fmt | par | val | preview | manual | align | prefix | pad | max_len |
|--------------|-------------|--------|-------|--------|-------|-----|-----|-----|---------|--------|-------|--------|-----|---------|
| `wms_zona_almacen` | codigo | AUTO_DEFAULT | ALMACEN | F4 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_MASTER | yes | yes | yes | ZON | 3 | 20 |
| `wms_ubicacion` | codigo_ubicacion | AUTO_DEFAULT | ALMACEN | F4 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_UBICACION | yes | yes | partial | — | — | 30 |

**Nota `wms_ubicacion`:** códigos semánticos tipo `A-01-03`; parser `partial` — high-water solo si parseable; manual libre predominante.

---

## 4. F2 — Documentos (AUTO_REQUIRED)

| sequence_key | code_column | policy | scope | family | store | fmt | par | val | preview | manual | align | prefix | pad | max_len |
|--------------|-------------|--------|-------|--------|-------|-----|-----|-----|---------|--------|-------|--------|-----|---------|
| `inv_movimiento` | numero_movimiento | AUTO_REQUIRED | EMPRESA | F2 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_DOCUMENT | no | no | import | MOV | 6 | 20 |
| `inv_inventario_fisico` | numero_inventario | AUTO_REQUIRED | EMPRESA | F2 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_DOCUMENT | no | no | import | IF | 5 | 20 |
| `pur_solicitud_compra` | numero_solicitud | AUTO_REQUIRED | EMPRESA | F2 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_DOCUMENT | no | no | import | SC | 6 | 20 |
| `pur_cotizacion` | numero_cotizacion | AUTO_REQUIRED | EMPRESA | F2 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_DOCUMENT | no | no | import | CC | 6 | 20 |
| `pur_orden_compra` | numero_oc | AUTO_REQUIRED | EMPRESA | F2 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_DOCUMENT | no | no | import | OC | 6 | 20 |
| `pur_recepcion` | numero_recepcion | AUTO_REQUIRED | EMPRESA | F2 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_DOCUMENT | no | no | import | REC | 6 | 20 |
| `log_despacho` | numero_despacho | AUTO_REQUIRED | EMPRESA | F2 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_DOCUMENT | no | no | import | DES | 6 | 20 |
| `mfg_orden_produccion` | numero_op | AUTO_REQUIRED | EMPRESA | F2 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_DOCUMENT | no | no | import | OP | 6 | 20 |
| `mnt_orden_trabajo` | numero_ot | AUTO_REQUIRED | EMPRESA | F2 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_DOCUMENT | no | no | import | OT | 6 | 20 |
| `sls_cotizacion` | numero_cotizacion | AUTO_REQUIRED | EMPRESA | F2 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_DOCUMENT | no | no | import | COT | 6 | 20 |
| `sls_pedido` | numero_pedido | AUTO_REQUIRED | EMPRESA | F2 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_DOCUMENT | no | no | import | PED | 6 | 20 |
| `crm_oportunidad` | numero_oportunidad | AUTO_REQUIRED | EMPRESA | F2 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_DOCUMENT | no | no | import | OPO | 6 | 20 |
| `pos_venta` | numero_venta | AUTO_REQUIRED | EMPRESA | F2 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_DOCUMENT | no | no | import | VTA | 6 | 20 |
| `hcm_contrato` | numero_contrato | AUTO_REQUIRED | EMPRESA | F2 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_DOCUMENT | no | no | import | CTR | 6 | 20 |
| `hcm_planilla` | numero_planilla | AUTO_REQUIRED | EMPRESA | F2 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_DOCUMENT | no | no | import | PLA | 6 | 20 |
| `hcm_prestamo` | numero_prestamo | AUTO_REQUIRED | EMPRESA | F2 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_DOCUMENT | no | no | import | PRE | 6 | 20 |
| `fin_asiento_contable` | numero_asiento | AUTO_REQUIRED | EMPRESA | F2 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_DOCUMENT | no | no | import | AS | 6 | 20 |
| `qms_inspeccion` | numero_inspeccion | AUTO_REQUIRED | EMPRESA | F2 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_DOCUMENT | no | no | import | INS | 6 | 20 |
| `qms_no_conformidad` | numero_nc | AUTO_REQUIRED | EMPRESA | F2 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_DOCUMENT | no | no | import | NC | 6 | 20 |
| `svc_orden_servicio` | numero_os | AUTO_REQUIRED | EMPRESA | F2 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_DOCUMENT | no | no | import | OS | 6 | 20 |
| `tkt_ticket` | numero_ticket | AUTO_REQUIRED | EMPRESA | F2 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_DOCUMENT | no | no | import | TKT | 6 | 20 |
| `wms_tarea` | numero_tarea | AUTO_REQUIRED | ALMACEN | F4 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_DOCUMENT | no | no | import | TAR | 6 | 20 |

**Columna align en documentos:** `import` = high-water solo en modo importación/implantación (F15A excepción), no en allocate normal.

---

## 5. F5 — POS turno (AUTO_REQUIRED)

| sequence_key | code_column | policy | scope | family | store | fmt | par | val | preview | manual | align | prefix | pad | max_len |
|--------------|-------------|--------|-------|--------|-------|-----|-----|-----|---------|--------|-------|--------|-----|---------|
| `pos_turno_caja` | numero_turno | AUTO_REQUIRED | PUNTO_VENTA | F5 | CFG | FMT_STANDARD | PAR_PREFIX_NUM | VAL_DOCUMENT | no | no | import | TUR | 4 | 20 |

---

## 6. F3 — Fiscal emisión (AUTO_REQUIRED)

| sequence_key | code_column | policy | scope | family | store | fmt | par | val | preview | manual | align | prefix | pad | max_len |
|--------------|-------------|--------|-------|--------|-------|-----|-----|-----|---------|--------|-------|--------|-----|---------|
| `invbill_comprobante` | numero | AUTO_REQUIRED | SERIE_FISCAL | F3 | FISCAL | FMT_FISCAL_8 | PAR_NONE | VAL_FISCAL_NUM | no | no | no | — | 8 | 10 |
| `log_guia_remision` | numero | AUTO_REQUIRED | SERIE_FISCAL | F3 | FISCAL | FMT_FISCAL_8 | PAR_NONE | VAL_FISCAL_NUM | no | no | no | — | 8 | 10 |

**Nota:** `serie` es MANUAL_ONLY en alta de maestro serie; no tiene entrada allocate. Emisión usa `serie_id` en contexto.

---

## 7. Verificación de consistencia

| Verificación | Resultado |
|--------------|-----------|
| Todas las entradas F15 grupo B AUTO_DEFAULT motor | ✅ 38 maestros (36 F1 + 2 F4) |
| Todas las entradas F15 grupo C AUTO_REQUIRED | ✅ 22 F2/F4 + 1 F5 + 2 F3 = 25 |
| Total entradas activas | ✅ 63 |
| Scope vs F16 `13` | ✅ Alineado |
| Policy vs F15A `08` | ✅ Alineado |
| Familia vs F16 `19` | ✅ Alineado |
| `inv_categoria` seed legacy | ✅ Corregido a `inv_categoria_producto` |

---

## 8. Apéndice — Exclusiones declaradas (sin entrada en catálogo)

| Tabla / campo | Política F15A | Motivo exclusión |
|---------------|---------------|------------------|
| `cat_*` | EXTERNAL | Catálogo global plataforma |
| `cliente.codigo_cliente` (V020) | EXTERNAL | SaaS provisioning |
| `numero_documento` terceros | EXTERNAL | RUC/DNI legal |
| `inv_producto.codigo_barra` | MANUAL_ONLY | EAN externo |
| `inv_producto.codigo_interno` | MANUAL_ONLY | Alias opcional |
| `inv_producto.codigo_fabricante` | EXTERNAL | Part number |
| `org_parametro_sistema` | MANUAL_ONLY | Config técnica |
| `invbill_serie_comprobante.serie` | MANUAL_ONLY | Alta serie SUNAT |
| `dms_documento.codigo_documento` | MANUAL_ONLY | Opcional; sin secuencia |
| `prc_promocion.codigo_cupon` | MANUAL_ONLY | Cupón campaña |
| `codigo_hash`, `codigo_qr`, `codigo_respuesta_sunat` | EXTERNAL | Artefactos OSE |
| `numero_serie` (lote/trazabilidad) | MANUAL_ONLY / EXTERNAL | No correlativo |

---

## 9. Apéndice — Módulo por sequence_key

| modulo_codigo | Cantidad entradas |
|---------------|-------------------|
| ORG | 5 |
| INV | 5 |
| WMS | 3 |
| PUR | 5 |
| SLS | 2 |
| LOG | 3 |
| MFG | 5 |
| MNT | 2 |
| MRP | 1 |
| MPS | 1 |
| CRM | 1 |
| PRC | 2 |
| FIN | 2 |
| HCM | 4 |
| QMS | 4 |
| POS | 2 |
| INVBILL | 2 |
| BDG | 1 |
| CST | 1 |
| PM | 1 |
| BI | 1 |
| WFL | 1 |
| SVC | 1 |
| TKT | 1 |

---

*Gobernanza en `22`. Resumen en `23`.*
