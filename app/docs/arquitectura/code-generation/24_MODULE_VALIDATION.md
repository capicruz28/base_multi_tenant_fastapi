# F16B — Validación módulo por módulo del SequenceCatalog

**Fase:** F16B — Auditoría final de validación  
**Fecha:** 2026-07-03  
**Base:** F15, F15A, F16, F16A (congelado)  
**Método:** Contrastar cada `sequence_key` de `catalog/21` contra `08`, `13`, `19`, V010 UNIQUE y clasificación F15 `02`.

---

## 1. Criterios de validación

| Dimensión | Fuente autoritativa |
|-----------|---------------------|
| **policy** | F15A `08` |
| **scope** | F16 `13` + UNIQUE V010 |
| **family** | F16A `19` |
| **store** | F16 `11`, `14` |
| **Perfiles fmt/par/val** | F16A `20`, `21` |

**Leyenda resultado:** ✅ conforme | ⚠️ observación (no bloqueante) | ❌ inconsistencia real

---

## 2. ORG (5 entradas)

| sequence_key | policy | scope | family | store | Resultado | Notas |
|--------------|--------|-------|--------|-------|-----------|-------|
| `org_empresa` | AUTO_DEFAULT | TENANT | F1 | CFG | ✅ | UNIQUE V010 `(cliente_id, codigo_empresa)` |
| `org_sucursal` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ | |
| `org_centro_costo` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ | |
| `org_departamento` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ | |
| `org_cargo` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ | |

**Exclusiones correctas:** ninguna entidad ORG fuera del catálogo salvo `org_parametro_sistema` (MANUAL_ONLY, grupo D).

---

## 3. INV (7 entradas)

| sequence_key | policy | scope | family | store | Resultado | Notas |
|--------------|--------|-------|--------|-------|-----------|-------|
| `inv_categoria_producto` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ | Corregido vs seed legacy `inv_categoria` |
| `inv_unidad_medida` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ | |
| `inv_producto` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ | Solo `codigo_sku`; barra/interno excluidos |
| `inv_almacen` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ | |
| `inv_tipo_movimiento` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ | BR-M-03: implantación puede exigir manual |
| `inv_movimiento` | AUTO_REQUIRED | EMPRESA | F2 | CFG | ✅ | Piloto Ola 1 |
| `inv_inventario_fisico` | AUTO_REQUIRED | EMPRESA | F2 | CFG | ✅ | |

**Exclusiones correctas:** `codigo_barra`, `codigo_interno`, `codigo_fabricante`, `codigo_sunat`, `numero_serie` detalle.

---

## 4. WMS (3 entradas)

| sequence_key | policy | scope | family | store | Resultado | Notas |
|--------------|--------|-------|--------|-------|-----------|-------|
| `wms_zona_almacen` | AUTO_DEFAULT | ALMACEN | F4 | CFG | ✅ | UNIQUE `(cliente_id, almacen_id, codigo)` |
| `wms_ubicacion` | AUTO_DEFAULT | ALMACEN | F4 | CFG | ✅ | `align=partial`; VAL_UBICACION |
| `wms_tarea` | AUTO_REQUIRED | ALMACEN | F4 | CFG | ✅ | UNIQUE `(cliente_id, almacen_id, numero_tarea)` |

---

## 5. PUR (5 entradas)

| sequence_key | policy | scope | family | store | Resultado | Notas |
|--------------|--------|-------|--------|-------|-----------|-------|
| `pur_proveedor` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ | |
| `pur_solicitud_compra` | AUTO_REQUIRED | EMPRESA | F2 | CFG | ✅ | |
| `pur_cotizacion` | AUTO_REQUIRED | EMPRESA | F2 | CFG | ✅ | Prefijo CC ≠ conflicto UNIQUE |
| `pur_orden_compra` | AUTO_REQUIRED | EMPRESA | F2 | CFG | ✅ | |
| `pur_recepcion` | AUTO_REQUIRED | EMPRESA | F2 | CFG | ✅ | |

---

## 6. SLS (3 entradas)

| sequence_key | policy | scope | family | store | Resultado | Notas |
|--------------|--------|-------|--------|-------|-----------|-------|
| `sls_cliente` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ | |
| `sls_cotizacion` | AUTO_REQUIRED | EMPRESA | F2 | CFG | ✅ | |
| `sls_pedido` | AUTO_REQUIRED | EMPRESA | F2 | CFG | ✅ | Sustituye patrón `PED-{cot}` |

---

## 7. LOG (4 entradas)

| sequence_key | policy | scope | family | store | Resultado | Notas |
|--------------|--------|-------|--------|-------|-----------|-------|
| `log_transportista` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ | |
| `log_ruta` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ | |
| `log_despacho` | AUTO_REQUIRED | EMPRESA | F2 | CFG | ✅ | |
| `log_guia_remision` | AUTO_REQUIRED | SERIE_FISCAL | F3 | FISCAL | ⚠️ | Ver GAP-02 en `26`: sin tabla serie dedicada en V010 |

---

## 8. MFG (5 entradas)

| sequence_key | policy | scope | family | store | Resultado | Notas |
|--------------|--------|-------|--------|-------|-----------|-------|
| `mfg_centro_trabajo` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ | |
| `mfg_operacion` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ⚠️ | Prefijo OP compartido con `mfg_orden_produccion` (UX, no técnico) |
| `mfg_lista_materiales` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ | |
| `mfg_ruta_fabricacion` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ | |
| `mfg_orden_produccion` | AUTO_REQUIRED | EMPRESA | F2 | CFG | ⚠️ | Prefijo OP compartido con maestro operación |

---

## 9. MNT (3 entradas)

| sequence_key | policy | scope | family | store | Resultado | Notas |
|--------------|--------|-------|--------|-------|-----------|-------|
| `mnt_activo` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ | |
| `mnt_plan_mantenimiento` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ | |
| `mnt_orden_trabajo` | AUTO_REQUIRED | EMPRESA | F2 | CFG | ✅ | |

---

## 10. MRP / MPS (2 entradas)

| sequence_key | policy | scope | family | store | Resultado |
|--------------|--------|-------|--------|-------|-----------|
| `mrp_plan_maestro` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ |
| `mps_plan_produccion` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ |

---

## 11. CRM (2 entradas)

| sequence_key | policy | scope | family | store | Resultado |
|--------------|--------|-------|--------|-------|-----------|
| `crm_campana` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ |
| `crm_oportunidad` | AUTO_REQUIRED | EMPRESA | F2 | CFG | ✅ |

---

## 12. PRC (2 entradas)

| sequence_key | policy | scope | family | store | Resultado | Notas |
|--------------|--------|-------|--------|-------|-----------|-------|
| `prc_lista_precio` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ | |
| `prc_promocion` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ | `codigo_cupon` excluido (MANUAL_ONLY) |

---

## 13. FIN (2 entradas)

| sequence_key | policy | scope | family | store | Resultado | Notas |
|--------------|--------|-------|--------|-------|-----------|-------|
| `fin_plan_cuentas` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ⚠️ | Sin prefijo; códigos jerárquicos — ver `25` |
| `fin_asiento_contable` | AUTO_REQUIRED | EMPRESA | F2 | CFG | ✅ | |

---

## 14. HCM (5 entradas)

| sequence_key | policy | scope | family | store | Resultado | Notas |
|--------------|--------|-------|--------|-------|-----------|-------|
| `hcm_empleado` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ⚠️ | Prefijo EMP compartido con `org_empresa` (scopes distintos) |
| `hcm_concepto_planilla` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ | `codigo_plame` es EXTERNAL aparte |
| `hcm_contrato` | AUTO_REQUIRED | EMPRESA | F2 | CFG | ✅ | |
| `hcm_planilla` | AUTO_REQUIRED | EMPRESA | F2 | CFG | ✅ | |
| `hcm_prestamo` | AUTO_REQUIRED | EMPRESA | F2 | CFG | ⚠️ | Prefijo PRE compartido con `bdg_presupuesto` |

---

## 15. QMS (4 entradas)

| sequence_key | policy | scope | family | store | Resultado |
|--------------|--------|-------|--------|-------|-----------|
| `qms_parametro_calidad` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ |
| `qms_plan_inspeccion` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ |
| `qms_inspeccion` | AUTO_REQUIRED | EMPRESA | F2 | CFG | ✅ |
| `qms_no_conformidad` | AUTO_REQUIRED | EMPRESA | F2 | CFG | ✅ |

---

## 16. POS (3 entradas)

| sequence_key | policy | scope | family | store | Resultado | Notas |
|--------------|--------|-------|--------|-------|-----------|-------|
| `pos_punto_venta` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ | |
| `pos_turno_caja` | AUTO_REQUIRED | PUNTO_VENTA | F5 | CFG | ✅ | UNIQUE incluye `punto_venta_id` |
| `pos_venta` | AUTO_REQUIRED | EMPRESA | F2 | CFG | ⚠️ | V010 UNIQUE incluye `punto_venta_id`; diseño F16 usa scope empresa — ver GAP-03 |

---

## 17. INVBILL (1 entrada activa)

| sequence_key | policy | scope | family | store | Resultado | Notas |
|--------------|--------|-------|--------|-------|-----------|-------|
| `invbill_comprobante` | AUTO_REQUIRED | SERIE_FISCAL | F3 | FISCAL | ✅ | Store `invbill_serie_comprobante` existe |

**Exclusión correcta:** `invbill_serie_comprobante.serie` — MANUAL_ONLY en alta.

---

## 18. BDG / CST / PM / BI / WFL / SVC / TKT (6 entradas)

| sequence_key | policy | scope | family | store | Resultado |
|--------------|--------|-------|--------|-------|-----------|
| `bdg_presupuesto` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ |
| `cst_centro_costo_tipo` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ |
| `pm_proyecto` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ |
| `bi_reporte` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ |
| `wfl_flujo_trabajo` | AUTO_DEFAULT | EMPRESA | F1 | CFG | ✅ |
| `svc_orden_servicio` | AUTO_REQUIRED | EMPRESA | F2 | CFG | ✅ |
| `tkt_ticket` | AUTO_REQUIRED | EMPRESA | F2 | CFG | ✅ |

---

## 19. Exclusiones verificadas (fuera del motor)

| Entidad / campo | Política F15A | ¿Correctamente excluida? |
|-----------------|---------------|--------------------------|
| `cat_*` | EXTERNAL | ✅ |
| `dms_documento.codigo_documento` | MANUAL_ONLY | ✅ (F16 `13` aún la lista; catálogo prevalece) |
| `inv_producto.codigo_barra` | MANUAL_ONLY | ✅ |
| `invbill_serie_comprobante.serie` | MANUAL_ONLY | ✅ |
| `cliente.codigo_cliente` V020 | EXTERNAL | ✅ |
| `numero_documento` terceros | EXTERNAL | ✅ |
| Artefactos SUNAT hash/qr | EXTERNAL | ✅ |

---

## 20. Resumen de validación por dimensión

| Dimensión | Entradas revisadas | Conformes | Con observación |
|-----------|-------------------|-----------|-----------------|
| policy | 63 | 63 | 0 |
| scope | 63 | 61 | 2 (`log_guia_remision`, `pos_venta`) |
| family | 63 | 63 | 0 |
| store | 63 | 62 | 1 (`log_guia_remision`) |
| Perfiles | 63 | 63 | 0 |

**Conclusión módulo:** Ninguna entidad del grupo B/C motor falta en el catálogo. Ninguna entidad EXTERNAL/MANUAL_ONLY está incorrectamente incluida. Las observaciones son acotadas y documentadas en `26_GAP_ANALYSIS.md`.

---

*Excepciones en `25`. Gaps en `26`. Veredicto en `27`.*
