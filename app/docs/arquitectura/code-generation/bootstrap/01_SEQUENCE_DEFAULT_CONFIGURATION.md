# F17A — Configuración inicial oficial de `cfg_codigo_secuencia`

**Fase:** F17A — Bootstrap oficial (consolidación, no arquitectura, no implementación)
**Fecha:** 2026-07-03
**Fuente única de metadatos:** `SequenceCatalog` v1.0.0 (63 entradas) — `app/core/codigo/sequence_catalog.py`
**Base congelada:** F15, F15A, F16, F16A, F16B, F17 Ola 0

> Este documento **no modifica** el catálogo ni V010. Documenta y valida la configuración por defecto que ya vive en el catálogo, para que sirva de estándar oficial del onboarding de cualquier cliente Shared o Dedicated.

---

## 1. Alcance del bootstrap

| Store | Entradas | Se puebla en `cfg_codigo_secuencia` |
|-------|----------|-------------------------------------|
| **CFG** | 61 | ✅ Sí — onboarding **eager** las de scope resoluble (TENANT/EMPRESA); **lazy** las de scope ALMACEN/PUNTO_VENTA |
| **FISCAL** | 2 (`invbill_comprobante`, `log_guia_remision`) | ❌ No — usan `invbill_serie_comprobante` / store fiscal; alta de serie es **MANUAL_ONLY** (F15A BR-M-05) |
| **Total catálogo** | **63** | 61 en cfg + 2 fiscal fuera de cfg |

**Conclusión (criterio F17D):** el universo CFG es de **61 secuencias**. El onboarding **no** crea un número fijo: siembra eager **todas** las CFG cuyo `scope_fingerprint` se resuelve en onboarding (scope TENANT/EMPRESA), y deja **lazy** las de scope ALMACEN/PUNTO_VENTA (requieren un almacén/punto de venta que aún no existe). Las 2 fiscales se gobiernan por `invbill_serie_comprobante` (ver `03_BOOTSTRAP_RULES.md` §7). El detalle del criterio y del reparto eager/lazy está en `03` §2.

---

## 2. Semántica de columnas de configuración

| Campo | Significado | Regla de bootstrap |
|-------|-------------|--------------------|
| `prefijo` | Prefijo alfanumérico del código | Del catálogo; editable por cliente (admin futuro) |
| `longitud_numero` (padding) | Dígitos de la parte numérica | Del catálogo; editable |
| `separador` | Separador prefijo↔número | Default `∅` (vacío) en todo el estándar V1 |
| `numero_inicial` | Primer número a asignar | `1` en todas las entradas |
| `ultimo_numero` | Contador consumido inicial | `0` en seed genérico (primer emitido = `numero_inicial`); **`1` para `org_empresa` TENANT** tras bootstrap EMP001 (BR-BOOT-04) |
| `scope_type` | Ámbito de unicidad | Del catálogo; **no editable** |
| `policy` | AUTO_REQUIRED / AUTO_DEFAULT | Del catálogo; **no editable** |
| `sequence_family` | F1–F5 | Del catálogo; **no editable** |
| `preview` | Estimación sin consumo | Derivado de policy; **no editable** |
| `manual` | Permite código manual | Derivado de policy; **no editable** |
| `high-water` | Alineación por manual/import | Derivado de familia/parser; **no editable** |

> **Regla oficial de separador (BS-CFG-01):** `separador = ∅` para las 61 entradas. Códigos compactos tipo `MOV000001`, `CLI0001`. El cliente puede activar `-` (ej. `MOV-000001`) por configuración, sin cambiar la arquitectura.

> **Regla oficial de arranque (BS-CFG-02):** `numero_inicial = 1`, `ultimo_numero = 0` en toda fila cfg recién sembrada **salvo** `org_empresa` TENANT post-bootstrap EMP001, donde `ultimo_numero = 1` (excepción BR-BOOT-04 / BR-M-02). No hay reinicio por periodo/año (excluido en F16 `14` §2.2).

---

## 3. F1 — Maestros (AUTO_DEFAULT · store CFG)

| # | sequence_key | code_column | scope | prefijo | pad | sep | nº inicial | preview | manual | high-water | primer código | max_len |
|---|--------------|-------------|-------|---------|-----|-----|-----------|---------|--------|------------|---------------|---------|
| 1 | `org_empresa` | codigo_empresa | TENANT | `EMP` | 3 | ∅ | 1 | Sí | Sí | Sí | `EMP001`¹ | 20 |

> ¹ **Bootstrap sede:** `EMP001` se inserta en onboarding antes del seed cfg. La fila cfg TENANT se siembra con **`ultimo_numero = 1`**; el primer `allocate` runtime emite **`EMP002`**. Ver `03_BOOTSTRAP_RULES.md` §2.1 (BR-BOOT-04).
| 2 | `org_sucursal` | codigo | EMPRESA | `SUC` | 3 | ∅ | 1 | Sí | Sí | Sí | `SUC001` | 20 |
| 3 | `org_centro_costo` | codigo | EMPRESA | `CC` | 3 | ∅ | 1 | Sí | Sí | Sí | `CC001` | 20 |
| 4 | `org_departamento` | codigo | EMPRESA | `DEP` | 3 | ∅ | 1 | Sí | Sí | Sí | `DEP001` | 20 |
| 5 | `org_cargo` | codigo | EMPRESA | `CAR` | 3 | ∅ | 1 | Sí | Sí | Sí | `CAR001` | 20 |
| 6 | `inv_categoria_producto` | codigo | EMPRESA | `CAT` | 3 | ∅ | 1 | Sí | Sí | Sí | `CAT001` | 20 |
| 7 | `inv_unidad_medida` | codigo | EMPRESA | `UM` | 3 | ∅ | 1 | Sí | Sí | Sí | `UM001` | 10 |
| 8 | `inv_producto` | codigo_sku | EMPRESA | `P` | 5 | ∅ | 1 | Sí | Sí | Sí | `P00001` | 50 |
| 9 | `inv_almacen` | codigo | EMPRESA | `ALM` | 3 | ∅ | 1 | Sí | Sí | Sí | `ALM001` | 20 |
| 10 | `inv_tipo_movimiento` | codigo | EMPRESA | `TM` | 3 | ∅ | 1 | Sí | Sí | Sí | `TM001` | 20 |
| 11 | `pur_proveedor` | codigo_proveedor | EMPRESA | `PROV` | 4 | ∅ | 1 | Sí | Sí | Sí | `PROV0001` | 20 |
| 12 | `sls_cliente` | codigo_cliente | EMPRESA | `CLI` | 4 | ∅ | 1 | Sí | Sí | Sí | `CLI0001` | 20 |
| 13 | `hcm_empleado` | codigo_empleado | EMPRESA | `EMP` | 4 | ∅ | 1 | Sí | Sí | Sí | `EMP0001` | 20 |
| 14 | `log_transportista` | codigo_transportista | EMPRESA | `TR` | 4 | ∅ | 1 | Sí | Sí | Sí | `TR0001` | 20 |
| 15 | `log_ruta` | codigo_ruta | EMPRESA | `RUT` | 4 | ∅ | 1 | Sí | Sí | Sí | `RUT0001` | 20 |
| 16 | `mfg_centro_trabajo` | codigo | EMPRESA | `CT` | 3 | ∅ | 1 | Sí | Sí | Sí | `CT001` | 20 |
| 17 | `mfg_operacion` | codigo | EMPRESA | `OP` | 3 | ∅ | 1 | Sí | Sí | Sí | `OP001` | 20 |
| 18 | `mfg_lista_materiales` | codigo_bom | EMPRESA | `BOM` | 4 | ∅ | 1 | Sí | Sí | Sí | `BOM0001` | 20 |
| 19 | `mfg_ruta_fabricacion` | codigo_ruta | EMPRESA | `RF` | 4 | ∅ | 1 | Sí | Sí | Sí | `RF0001` | 20 |
| 20 | `mnt_activo` | codigo_activo | EMPRESA | `ACT` | 4 | ∅ | 1 | Sí | Sí | Sí | `ACT0001` | 20 |
| 21 | `mnt_plan_mantenimiento` | codigo_plan | EMPRESA | `PM` | 4 | ∅ | 1 | Sí | Sí | Sí | `PM0001` | 20 |
| 22 | `mrp_plan_maestro` | codigo_plan | EMPRESA | `MRP` | 4 | ∅ | 1 | Sí | Sí | Sí | `MRP0001` | 20 |
| 23 | `mps_plan_produccion` | codigo_plan | EMPRESA | `MPS` | 4 | ∅ | 1 | Sí | Sí | Sí | `MPS0001` | 20 |
| 24 | `crm_campana` | codigo_campana | EMPRESA | `CMP` | 4 | ∅ | 1 | Sí | Sí | Sí | `CMP0001` | 20 |
| 25 | `prc_lista_precio` | codigo_lista | EMPRESA | `LP` | 4 | ∅ | 1 | Sí | Sí | Sí | `LP0001` | 20 |
| 26 | `prc_promocion` | codigo_promocion | EMPRESA | `PRM` | 4 | ∅ | 1 | Sí | Sí | Sí | `PRM0001` | 20 |
| 27 | `fin_plan_cuentas` | codigo_cuenta | EMPRESA | `∅` | 6 | ∅ | 1 | Sí | Sí | Sí | `000001` | 20 |
| 28 | `hcm_concepto_planilla` | codigo_concepto | EMPRESA | `CON` | 4 | ∅ | 1 | Sí | Sí | Sí | `CON0001` | 20 |
| 29 | `qms_parametro_calidad` | codigo | EMPRESA | `QMP` | 4 | ∅ | 1 | Sí | Sí | Sí | `QMP0001` | 20 |
| 30 | `qms_plan_inspeccion` | codigo | EMPRESA | `QPL` | 4 | ∅ | 1 | Sí | Sí | Sí | `QPL0001` | 20 |
| 31 | `pos_punto_venta` | codigo_punto_venta | EMPRESA | `PV` | 3 | ∅ | 1 | Sí | Sí | Sí | `PV001` | 20 |
| 32 | `bdg_presupuesto` | codigo_presupuesto | EMPRESA | `PRE` | 4 | ∅ | 1 | Sí | Sí | Sí | `PRE0001` | 20 |
| 33 | `cst_centro_costo_tipo` | codigo | EMPRESA | `CCT` | 3 | ∅ | 1 | Sí | Sí | Sí | `CCT001` | 20 |
| 34 | `pm_proyecto` | codigo_proyecto | EMPRESA | `PRY` | 4 | ∅ | 1 | Sí | Sí | Sí | `PRY0001` | 20 |
| 35 | `bi_reporte` | codigo_reporte | EMPRESA | `RPT` | 4 | ∅ | 1 | Sí | Sí | Sí | `RPT0001` | 20 |
| 36 | `wfl_flujo_trabajo` | codigo_flujo | EMPRESA | `WFL` | 4 | ∅ | 1 | Sí | Sí | Sí | `WFL0001` | 20 |

**Justificaciones de excepción F1:**

- **`inv_producto` (pad 5, max 50):** SKU es el maestro de mayor cardinalidad en textil (variantes talla/color); 5 dígitos → 99 999 SKU por empresa antes de expandir. `max_len` 50 permite SKU semánticos manuales largos.
- **`inv_unidad_medida` (max 10):** columna V010 corta; padding 3 suficiente.
- **`fin_plan_cuentas` (prefijo ∅, pad 6):** el plan contable usa códigos jerárquicos numéricos (`101`, `4011`, `60111`); un prefijo alfabético rompería la convención PCGE. Autogenerado solo como respaldo; en implantación domina el ingreso manual (BR-M-03).

---

## 4. F4 — Maestros WMS (AUTO_DEFAULT · scope ALMACEN · store CFG)

| # | sequence_key | code_column | scope | prefijo | pad | sep | nº inicial | preview | manual | high-water | primer código | max_len |
|---|--------------|-------------|-------|---------|-----|-----|-----------|---------|--------|------------|---------------|---------|
| 37 | `wms_zona_almacen` | codigo | ALMACEN | `ZON` | 3 | ∅ | 1 | Sí | Sí | Sí | `ZON001` | 20 |
| 38 | `wms_ubicacion` | codigo_ubicacion | ALMACEN | `∅` | 3 | ∅ | 1 | Sí | Sí | Parcial | `001` / `A-01-03`* | 30 |

**Justificación `wms_ubicacion`:** predominan códigos semánticos pasillo-rack-nivel (`A-01-03`) ingresados manualmente; el autogenerado numérico es respaldo. `high-water = Parcial`: solo alinea si el código manual termina en dígitos parseables (`VAL_UBICACION`, parser partial). `max_len` 30 para nomenclaturas físicas extensas.

---

## 5. F2 — Documentos (AUTO_REQUIRED · store CFG)

| # | sequence_key | code_column | scope | prefijo | pad | sep | nº inicial | preview | manual | high-water | primer código | max_len |
|---|--------------|-------------|-------|---------|-----|-----|-----------|---------|--------|------------|---------------|---------|
| 39 | `inv_movimiento` | numero_movimiento | EMPRESA | `MOV` | 6 | ∅ | 1 | No | No | Solo import | `MOV000001` | 20 |
| 40 | `inv_inventario_fisico` | numero_inventario | EMPRESA | `IF` | 5 | ∅ | 1 | No | No | Solo import | `IF00001` | 20 |
| 41 | `pur_solicitud_compra` | numero_solicitud | EMPRESA | `SC` | 6 | ∅ | 1 | No | No | Solo import | `SC000001` | 20 |
| 42 | `pur_cotizacion` | numero_cotizacion | EMPRESA | `CC` | 6 | ∅ | 1 | No | No | Solo import | `CC000001` | 20 |
| 43 | `pur_orden_compra` | numero_oc | EMPRESA | `OC` | 6 | ∅ | 1 | No | No | Solo import | `OC000001` | 20 |
| 44 | `pur_recepcion` | numero_recepcion | EMPRESA | `REC` | 6 | ∅ | 1 | No | No | Solo import | `REC000001` | 20 |
| 45 | `log_despacho` | numero_despacho | EMPRESA | `DES` | 6 | ∅ | 1 | No | No | Solo import | `DES000001` | 20 |
| 46 | `mfg_orden_produccion` | numero_op | EMPRESA | `OP` | 6 | ∅ | 1 | No | No | Solo import | `OP000001` | 20 |
| 47 | `mnt_orden_trabajo` | numero_ot | EMPRESA | `OT` | 6 | ∅ | 1 | No | No | Solo import | `OT000001` | 20 |
| 48 | `sls_cotizacion` | numero_cotizacion | EMPRESA | `COT` | 6 | ∅ | 1 | No | No | Solo import | `COT000001` | 20 |
| 49 | `sls_pedido` | numero_pedido | EMPRESA | `PED` | 6 | ∅ | 1 | No | No | Solo import | `PED000001` | 20 |
| 50 | `crm_oportunidad` | numero_oportunidad | EMPRESA | `OPO` | 6 | ∅ | 1 | No | No | Solo import | `OPO000001` | 20 |
| 51 | `pos_venta` | numero_venta | EMPRESA | `VTA` | 6 | ∅ | 1 | No | No | Solo import | `VTA000001` | 20 |
| 52 | `hcm_contrato` | numero_contrato | EMPRESA | `CTR` | 6 | ∅ | 1 | No | No | Solo import | `CTR000001` | 20 |
| 53 | `hcm_planilla` | numero_planilla | EMPRESA | `PLA` | 6 | ∅ | 1 | No | No | Solo import | `PLA000001` | 20 |
| 54 | `hcm_prestamo` | numero_prestamo | EMPRESA | `PRE` | 6 | ∅ | 1 | No | No | Solo import | `PRE000001` | 20 |
| 55 | `fin_asiento_contable` | numero_asiento | EMPRESA | `AS` | 6 | ∅ | 1 | No | No | Solo import | `AS000001` | 20 |
| 56 | `qms_inspeccion` | numero_inspeccion | EMPRESA | `INS` | 6 | ∅ | 1 | No | No | Solo import | `INS000001` | 20 |
| 57 | `qms_no_conformidad` | numero_nc | EMPRESA | `NC` | 6 | ∅ | 1 | No | No | Solo import | `NC000001` | 20 |
| 58 | `svc_orden_servicio` | numero_os | EMPRESA | `OS` | 6 | ∅ | 1 | No | No | Solo import | `OS000001` | 20 |
| 59 | `tkt_ticket` | numero_ticket | EMPRESA | `TKT` | 6 | ∅ | 1 | No | No | Solo import | `TKT000001` | 20 |
| 60 | `wms_tarea` | numero_tarea | ALMACEN (F4) | `TAR` | 6 | ∅ | 1 | No | No | Solo import | `TAR000001` | 20 |

**Justificaciones de excepción F2:**

- **Padding 6 estándar documental:** 999 999 documentos por empresa/año-vida antes de expandir; suficiente para volumen ERP típico y alto (textil).
- **`inv_inventario_fisico` (pad 5):** conteos físicos tienen frecuencia baja (mensual/anual); 5 dígitos sobran.
- **`preview = No`, `manual = No`:** política AUTO_REQUIRED — el usuario nunca inventa correlativos (F15A). `high-water = Solo import` = se alinea únicamente en importación histórica (rol implantación), no en allocate normal.

---

## 6. F5 — POS turno (AUTO_REQUIRED · scope PUNTO_VENTA · store CFG)

| # | sequence_key | code_column | scope | prefijo | pad | sep | nº inicial | preview | manual | high-water | primer código | max_len |
|---|--------------|-------------|-------|---------|-----|-----|-----------|---------|--------|------------|---------------|---------|
| 61 | `pos_turno_caja` | numero_turno | PUNTO_VENTA | `TUR` | 4 | ∅ | 1 | No | No | Solo import | `TUR0001` | 20 |

**Justificación:** padding 4 (9 999 turnos por punto de venta) — un PV rara vez supera pocos miles de turnos en su vida útil; scope por `punto_venta_id` distribuye contención.

---

## 7. F3 — Fiscal (AUTO_REQUIRED · scope SERIE_FISCAL · store FISCAL) — **fuera de cfg**

| # | sequence_key | code_column | scope | formato | pad | preview | manual | high-water | primer nº | max_len |
|---|--------------|-------------|-------|---------|-----|---------|--------|------------|-----------|---------|
| 62 | `invbill_comprobante` | numero | SERIE_FISCAL | FMT_FISCAL_8 | 8 | No | No | No | `00000001` | 10 |
| 63 | `log_guia_remision` | numero | SERIE_FISCAL | FMT_FISCAL_8 | 8 | No | No | No | `00000001` | 10 |

**No se seedean en `cfg_codigo_secuencia`.** El contador vive en `invbill_serie_comprobante.numero_actual` por `serie_id`. La **serie** (`F001`, `B001`, `T001`) es MANUAL_ONLY: el cliente la registra según autorización SUNAT. Numeración legal a 8 dígitos sin prefijo; el `numero_completo` (`F001-00000001`) es campo calculado en V010. Detalle en `03_BOOTSTRAP_RULES.md` §7.

> **Pendiente conocido (INC-10 / GAP-P1-01):** `log_guia_remision` no tiene tabla de serie dedicada en V010; su store fiscal se resuelve en Ola 4. No afecta el bootstrap de cfg.

---

## 8. Resumen cuantitativo del bootstrap

| Categoría | Entradas | Seed en cfg |
|-----------|----------|-------------|
| F1 Maestros | 36 | ✅ |
| F4 Maestros WMS | 2 | ✅ |
| F2 Documentos | 21 (20 EMPRESA + 1 F4 `wms_tarea`) | ✅ |
| F5 POS turno | 1 | ✅ |
| **Subtotal CFG** | **61** | ✅ |
| F3 Fiscal | 2 | ❌ (serie fiscal) |
| **Total catálogo** | **63** | — |

**Distribución de scope (CFG) y reparto eager/lazy (F17D):**

| scope_type | Entradas CFG | Poblado |
|------------|--------------|---------|
| TENANT | 1 (`org_empresa`) | **Eager** (onboarding) |
| EMPRESA | 56 | **Eager** (onboarding, empresa sede) |
| ALMACEN | 3 (`wms_zona_almacen`, `wms_ubicacion`, `wms_tarea`) | **Lazy** (`ensure_row` al existir almacén) |
| PUNTO_VENTA | 1 (`pos_turno_caja`) | **Lazy** (`ensure_row` al existir punto de venta) |
| SERIE_FISCAL | 0 en cfg (2 en store fiscal) | — |

> **Eager en onboarding = 57 filas para una empresa** (1 TENANT + 56 EMPRESA de la sede). No es un número fijo del código: se **deriva** del catálogo (store CFG + scope ∈ {TENANT, EMPRESA}). Multiempresa: +56 EMPRESA por cada empresa adicional (lazy). Las 4 de scope ALMACEN/PUNTO_VENTA se crean lazy por entidad.

---

## 9. Validación de consistencia contra el catálogo

| Verificación | Resultado |
|--------------|-----------|
| Prefijos = catálogo v1.0.0 | ✅ Idénticos |
| Padding = catálogo | ✅ Idéntico |
| Separador = ∅ en 61 entradas | ✅ |
| numero_inicial = 1 | ✅ |
| `org_empresa` TENANT: `ultimo_numero = 1` post-EMP001 (BR-BOOT-04) | ✅ |
| policy/scope/family = catálogo | ✅ (no editados) |
| preview/manual/high-water derivados | ✅ |
| 61 CFG + 2 FISCAL = 63 | ✅ |

**Sin discrepancias.** Esta configuración es un espejo documental del `SequenceCatalog`; cualquier ajuste futuro de defaults se hace en el catálogo (con gobernanza `22`), no aquí.

---

*Estándar de prefijos en `02_PREFIX_STANDARD.md`. Reglas de poblado en `03_BOOTSTRAP_RULES.md`. Plan de seed en `04_SEED_GENERATION_PLAN.md`.*
