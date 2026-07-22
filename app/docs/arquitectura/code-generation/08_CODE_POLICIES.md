# F15A — Políticas oficiales de generación de códigos

**Fase:** F15A — Política funcional  
**Fecha:** 2026-07-02  
**Base:** F15 clasificación aprobada (`02_ENTITY_CLASSIFICATION.md`)

---

## 1. Las cuatro políticas oficiales

### 1.1 AUTO_REQUIRED

**Definición:** El sistema **siempre** asigna el código/correlativo. El cliente o usuario **no puede** enviarlo en la operación estándar de creación.

| Criterio | Detalle |
|----------|---------|
| **Cuándo aplica** | Documentos de proceso (grupo C); numeración fiscal en emisión; cualquier entidad donde la integridad correlativa es crítica o legalmente regulada. |
| **Entrada API (futuro)** | Campo omitido o ignorado si se envía; respuesta Read siempre incluye valor asignado. |
| **Unicidad** | Garantizada por motor dentro del scope. |
| **Edición** | **Prohibida post-CREATE** (**BR-IMM-01**). El Motor no participa en UPDATE. |
| **Migración** | Excepción controlada: importación histórica con correlativo explícito bajo rol de implantación. |

**Ejemplos CAXIS:** `numero_movimiento`, `numero_oc`, `numero_pedido`, `numero_recepcion`, `numero_asiento`, `invbill_comprobante.numero` (en emisión), `pos_venta.numero_venta`.

---

### 1.2 AUTO_DEFAULT

**Definición:** Si el usuario **omite** el código, el sistema lo genera. Si el usuario **lo proporciona** y es válido y único, se acepta.

| Criterio | Detalle |
|----------|---------|
| **Cuándo aplica** | Maestros ERP (grupo B) en operación normal; fase de convivencia con datos legados; importaciones con huecos. |
| **Entrada API (futuro)** | Campo opcional en Create; obligatorio en Read tras persistir. |
| **Unicidad** | Validación explícita en manual; motor garantiza en automático. |
| **Edición** | **Prohibida post-CREATE** (**BR-IMM-01…05**). `generation_policy` aplica solo a CREATE/IMPORT. Antes BR-M-30/31 — **superseded**. |
| **Migración** | Política por defecto para maestros sin código en archivo fuente. |

**Ejemplos CAXIS:** `org_sucursal.codigo`, `inv_producto.codigo_sku`, `pur_proveedor.codigo_proveedor`, `sls_cliente.codigo_cliente`, `hcm_empleado.codigo_empleado`.

---

### 1.3 MANUAL_ONLY

**Definición:** El usuario u operación **debe** proporcionar el valor. El motor **no** genera.

| Criterio | Detalle |
|----------|---------|
| **Cuándo aplica** | Identificadores con semántica externa o decisión humana deliberada; catálogos de configuración que no son secuenciales; series fiscales en **alta** de maestro serie. |
| **Entrada API** | Campo obligatorio en Create. |
| **Unicidad** | Validación de duplicados obligatoria. |
| **Edición** | Campo código Motor: **inmutable** post-CREATE (**BR-IMM**). Otros campos del maestro según reglas propias. |
| **Migración** | Valor debe venir en archivo o ingresarse en UI. |

**Ejemplos CAXIS:** `inv_producto.codigo_barra`, `invbill_serie_comprobante.serie` (alta), `org_parametro_sistema.codigo_parametro`, `prc_promocion.codigo_cupon` (opcional promocional), `dms_documento.codigo_documento` (si se usa).

---

### 1.4 EXTERNAL

**Definición:** El valor **proviene de un sistema o norma externa**. El motor ERP interno no secuencia ni redefine.

| Criterio | Detalle |
|----------|---------|
| **Cuándo aplica** | Identidad legal, catálogos globales, respuestas de autoridad fiscal, identificadores de plataforma SaaS. |
| **Entrada API** | Obligatorio o poblado por integración; validación de formato según norma externa. |
| **Unicidad** | Según regla externa + UNIQUE de BD cuando aplique. |
| **Edición** | Solo si cambia situación legal real (ej. corrección RUC); no es “código interno”. |
| **Migración** | Debe traerse del sistema origen. |

**Ejemplos CAXIS:** `numero_documento` (RUC/DNI), `cat_moneda.codigo`, `cat_pais.codigo_iso2`, `codigo_hash`/`codigo_qr` SUNAT, `cliente.codigo_cliente` (V020 SaaS), `hcm_concepto_planilla.codigo_plame`.

---

## 2. Diagrama de decisión (negocio)

```
¿Es catálogo global o identidad legal externa?
  └─ Sí → EXTERNAL
  └─ No → ¿Es documento de proceso o correlativo fiscal en emisión?
        └─ Sí → AUTO_REQUIRED
        └─ No → ¿Debe el usuario aportar siempre un valor externo/deliberado?
              └─ Sí → MANUAL_ONLY
              └─ No → AUTO_DEFAULT (maestro ERP estándar)
```

---

## 3. Matriz política — Maestros (grupo B)

| Entidad | Campo | Política | Notas |
|---------|-------|----------|-------|
| `org_empresa` | `codigo_empresa` | AUTO_DEFAULT | Scope tenant; bootstrap sede `EMP001` (sin motor); cfg TENANT con `ultimo_numero=1` (BR-BOOT-04); primer auto runtime = `EMP002` |
| `org_sucursal` | `codigo` | AUTO_DEFAULT | |
| `org_centro_costo` | `codigo` | AUTO_DEFAULT | |
| `org_departamento` | `codigo` | AUTO_DEFAULT | |
| `org_cargo` | `codigo` | AUTO_DEFAULT | |
| `inv_categoria_producto` | `codigo` | AUTO_DEFAULT | |
| `inv_unidad_medida` | `codigo` | AUTO_DEFAULT | |
| `inv_producto` | `codigo_sku` | AUTO_DEFAULT | |
| `inv_producto` | `codigo_interno` | MANUAL_ONLY | Opcional |
| `inv_producto` | `codigo_barra` | MANUAL_ONLY | EAN/UPC |
| `inv_almacen` | `codigo` | AUTO_DEFAULT | |
| `inv_tipo_movimiento` | `codigo` | AUTO_DEFAULT | Configuración; puede requerir manual por gobernanza |
| `wms_zona_almacen` | `codigo` | AUTO_DEFAULT | Scope almacén |
| `wms_ubicacion` | `codigo_ubicacion` | AUTO_DEFAULT | Scope almacén; a menudo semántica pasillo-rack |
| `pur_proveedor` | `codigo_proveedor` | AUTO_DEFAULT | |
| `sls_cliente` | `codigo_cliente` | AUTO_DEFAULT | |
| `hcm_empleado` | `codigo_empleado` | AUTO_DEFAULT | |
| `log_transportista` | `codigo_transportista` | AUTO_DEFAULT | |
| `log_ruta` | `codigo_ruta` | AUTO_DEFAULT | |
| `mfg_centro_trabajo` | `codigo` | AUTO_DEFAULT | |
| `mfg_operacion` | `codigo` | AUTO_DEFAULT | |
| `mfg_lista_materiales` | `codigo_bom` | AUTO_DEFAULT | |
| `mfg_ruta_fabricacion` | `codigo_ruta` | AUTO_DEFAULT | |
| `mnt_activo` | `codigo_activo` | AUTO_DEFAULT | |
| `mnt_plan_mantenimiento` | `codigo_plan` | AUTO_DEFAULT | |
| `mrp_plan_maestro` | `codigo_plan` | AUTO_DEFAULT | |
| `mps_plan_produccion` | `codigo_plan` | AUTO_DEFAULT | |
| `crm_campana` | `codigo_campana` | AUTO_DEFAULT | |
| `prc_lista_precio` | `codigo_lista` | AUTO_DEFAULT | |
| `prc_promocion` | `codigo_promocion` | AUTO_DEFAULT | |
| `fin_plan_cuentas` | `codigo_cuenta` | AUTO_DEFAULT | Plan contable puede exigir manual en implantación |
| `hcm_concepto_planilla` | `codigo_concepto` | AUTO_DEFAULT | |
| `qms_parametro_calidad` | `codigo` | AUTO_DEFAULT | |
| `qms_plan_inspeccion` | `codigo` | AUTO_DEFAULT | |
| `pos_punto_venta` | `codigo_punto_venta` | AUTO_DEFAULT | |
| `invbill_serie_comprobante` | `serie` | MANUAL_ONLY | Alta de serie autorizada |
| `bdg_presupuesto` | `codigo_presupuesto` | AUTO_DEFAULT | |
| `cst_centro_costo_tipo` | `codigo` | AUTO_DEFAULT | |
| `pm_proyecto` | `codigo_proyecto` | AUTO_DEFAULT | |
| `bi_reporte` | `codigo_reporte` | AUTO_DEFAULT | |
| `wfl_flujo_trabajo` | `codigo_flujo` | AUTO_DEFAULT | |
| `dms_documento` | `codigo_documento` | MANUAL_ONLY | Nullable en BD; si se usa, manual |

---

## 4. Matriz política — Documentos (grupo C)

| Entidad | Campo(s) | Política | Scope negocio |
|---------|----------|----------|---------------|
| `inv_movimiento` | `numero_movimiento` | AUTO_REQUIRED | Empresa |
| `inv_inventario_fisico` | `numero_inventario` | AUTO_REQUIRED | Empresa |
| `pur_solicitud_compra` | `numero_solicitud` | AUTO_REQUIRED | Empresa |
| `pur_cotizacion` | `numero_cotizacion` | AUTO_REQUIRED | Empresa |
| `pur_orden_compra` | `numero_oc` | AUTO_REQUIRED | Empresa |
| `pur_recepcion` | `numero_recepcion` | AUTO_REQUIRED | Empresa |
| `log_guia_remision` | `serie`, `numero` | AUTO_REQUIRED (emisión) | Empresa + serie |
| `log_despacho` | `numero_despacho` | AUTO_REQUIRED | Empresa |
| `mfg_orden_produccion` | `numero_op` | AUTO_REQUIRED | Empresa |
| `mnt_orden_trabajo` | `numero_ot` | AUTO_REQUIRED | Empresa |
| `sls_cotizacion` | `numero_cotizacion` | AUTO_REQUIRED | Empresa |
| `sls_pedido` | `numero_pedido` | AUTO_REQUIRED | Empresa |
| `crm_oportunidad` | `numero_oportunidad` | AUTO_REQUIRED | Empresa |
| `invbill_comprobante` | `serie`, `numero` | AUTO_REQUIRED (emisión) | Empresa + serie fiscal |
| `pos_turno_caja` | `numero_turno` | AUTO_REQUIRED | Punto de venta |
| `pos_venta` | `numero_venta` | AUTO_REQUIRED | Empresa |
| `hcm_contrato` | `numero_contrato` | AUTO_REQUIRED | Empresa |
| `hcm_planilla` | `numero_planilla` | AUTO_REQUIRED | Empresa |
| `hcm_prestamo` | `numero_prestamo` | AUTO_REQUIRED | Empresa |
| `fin_asiento_contable` | `numero_asiento` | AUTO_REQUIRED | Empresa |
| `qms_inspeccion` | `numero_inspeccion` | AUTO_REQUIRED | Empresa |
| `qms_no_conformidad` | `numero_nc` | AUTO_REQUIRED | Empresa |
| `wms_tarea` | `numero_tarea` | AUTO_REQUIRED | Almacén |
| `svc_orden_servicio` | `numero_os` | AUTO_REQUIRED | Empresa |
| `tkt_ticket` | `numero_ticket` | AUTO_REQUIRED | Empresa |

---

## 5. Matriz política — Excluidos del motor (grupo A y D)

| Entidad / campo | Política | Motor |
|-----------------|----------|-------|
| `cat_*` | EXTERNAL | No |
| `numero_documento` terceros | EXTERNAL | No |
| `codigo_sunat`, `codigo_plame` | EXTERNAL | No |
| `codigo_hash`, `codigo_qr`, `codigo_respuesta_sunat` | EXTERNAL | No |
| `org_parametro_sistema` | MANUAL_ONLY | No |
| `cliente.codigo_cliente` (V020) | EXTERNAL / manual SaaS | No |
| `numero_serie` (lote/trazabilidad) | MANUAL_ONLY o EXTERNAL | No |

---

## 6. Transición desde estado actual (F15)

| Estado actual (AS-IS) | Política objetivo (TO-BE) | Transición |
|-----------------------|---------------------------|------------|
| `numero_movimiento` manual en API | AUTO_REQUIRED | Contrato API: campo opcional → ignorado; fase de advertencia deprecación |
| Maestros ORG manuales | AUTO_DEFAULT | Campo opcional; autogenerar si vacío |
| Estorno INV por timestamp | AUTO_REQUIRED | Nuevo correlativo de familia documento, no string temporal |
| `PED-{cotización}` | AUTO_REQUIRED | Pedido con secuencia propia |
| Seed `cfg` sin uso | N/A | Activar alineado a scope F15 |

---

## 7. Permisos funcionales (conceptual)

| Acción | Permiso típico | Política |
|--------|----------------|----------|
| Crear maestro sin código | `{mod}.{recurso}.crear` | AUTO_DEFAULT |
| Forzar código manual en maestro | Mismo | AUTO_DEFAULT |
| Crear documento | `{mod}.{recurso}.crear` | AUTO_REQUIRED — sin override |
| Importar con códigos históricos | `{mod}.{recurso}.importar` o rol implantación | Excepción migración |
| ~~Cambiar código maestro sin referencias~~ | — | **Prohibido** — **BR-IMM-01**; BR-M-31 DEPRECATED |
| Re-maestro / migración de código | Rol implantación (proceso excepcional) | **BR-IMM-05** / BR-M-33 — no UPDATE estándar |
| Cambiar prefijo de secuencia | `cfg.secuencias.actualizar` (futuro) | Administración |
| Reiniciar secuencia | `cfg.secuencias.administrar` (futuro) | Excepcional |
| Preview próximo código | `{mod}.{recurso}.crear` o consulta | Sin consumo |

---

## 8. Formato funcional (sin algoritmo)

| Regla | Descripción |
|-------|-------------|
| **FP-01** | Códigos maestros: mayúsculas normalizadas, sin espacios leading/trailing. |
| **FP-02** | Longitud máxima la de la columna V010; rechazo 422 si excede. |
| **FP-03** | Correlativos documentales: componente numérico con padding configurable por tenant; prefijo alfanumérico corto. |
| **FP-04** | Fiscal: `numero` con padding legal (8 dígitos en comprobante); `serie` según autorización. |
| **FP-05** | Caracteres permitidos en manual: alfanumérico + `-` `_` salvo restricción por entidad. |

---

## 9. Resumen ejecutivo de políticas

| Política | % entidades motor (aprox.) | Regla de oro |
|----------|----------------------------|--------------|
| AUTO_REQUIRED | ~24 documentos + emisión fiscal | El usuario nunca inventa el correlativo |
| AUTO_DEFAULT | ~38 maestros | Automático por defecto; manual permitido |
| MANUAL_ONLY | ~8 campos | Valor humano o externo deliberado |
| EXTERNAL | Catálogos + legales + fiscal respuesta | Fuera del motor secuencial |

---

*Complementa `07_BUSINESS_RULES.md` (**BR-IMM** §3.4). Estándar consolidado en `10_FINAL_RECOMMENDATION.md`.*
