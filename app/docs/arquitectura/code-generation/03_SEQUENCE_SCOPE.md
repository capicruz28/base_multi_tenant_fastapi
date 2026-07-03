# F15 — Alcance de secuencia (scope de numeración)

**Fase:** F15 — Auditoría arquitectónica  
**Fecha:** 2026-07-02  
**Propósito:** Definir, por entidad candidata al motor, si la numeración debe ser **global por cliente (tenant)** o **independiente por empresa**, y dimensiones adicionales cuando aplique.

---

## 1. Dimensiones de scope en el modelo actual

El DDL V010 revela **cinco patrones** de unicidad que determinan el scope real:

| Dimensión | Clave UNIQUE típica | Significado |
|-----------|---------------------|-------------|
| **T1 — Tenant** | `(cliente_id, codigo*)` | Secuencia compartida por todas las empresas del tenant. |
| **T2 — Empresa** | `(cliente_id, empresa_id, codigo*\|numero_*)` | Secuencia independiente por empresa operativa. |
| **T3 — Almacén** | `(cliente_id, almacen_id, codigo*\|numero_*)` | Secuencia por almacén (WMS). |
| **T4 — Punto de venta** | `(cliente_id, empresa_id, punto_venta_id, numero_*)` | Secuencia por terminal POS. |
| **T5 — Serie fiscal** | `(cliente_id, empresa_id, tipo_comprobante, serie, numero)` | Correlativo legal por serie autorizada. |

La tabla `cfg_codigo_secuencia` hoy solo modela `(cliente_id, empresa_id NULL\|UUID, entidad)` — **insuficiente** para T3–T5 sin extensión conceptual (Fase 2).

---

## 2. Decisión por entidad candidata al motor

Leyenda: **Cliente** = global por tenant | **Empresa** = por `empresa_id` | **Almacén** / **PV** / **Serie** = dimensión adicional.

### 2.1 Maestros (grupo B)

| Entidad | Campo | Scope recomendado | Justificación |
|---------|-------|-------------------|---------------|
| `org_empresa` | `codigo_empresa` | **Cliente** | UNIQUE solo en `cliente_id`; la empresa es entidad raíz del tenant, no hija de otra empresa. |
| `org_sucursal` | `codigo` | **Empresa** | UNIQUE incluye `empresa_id`; sucursal pertenece a una empresa. |
| `org_centro_costo` | `codigo` | **Empresa** | Imputación contable por empresa. |
| `org_departamento` | `codigo` | **Empresa** | Estructura organizacional por empresa. |
| `org_cargo` | `codigo` | **Empresa** | Idem. |
| `inv_categoria_producto` | `codigo` | **Empresa** | Catálogo de productos por empresa (multiempresa). |
| `inv_unidad_medida` | `codigo` | **Empresa** | Permite UM distintas por empresa si se requiere. |
| `inv_producto` | `codigo_sku` | **Empresa** | UNIQUE por empresa; misma SKU puede repetirse entre empresas del tenant. |
| `inv_almacen` | `codigo` | **Empresa** | Almacén declarado a nivel empresa. |
| `inv_tipo_movimiento` | `codigo` | **Empresa** | Configuración operativa INV por empresa. |
| `wms_zona_almacen` | `codigo` | **Almacén** | UNIQUE usa `almacen_id`, no `empresa_id`. |
| `wms_ubicacion` | `codigo_ubicacion` | **Almacén** | Idem. |
| `pur_proveedor` | `codigo_proveedor` | **Empresa** | Proveedor operativo por empresa (RUC puede repetir lógica distinta). |
| `sls_cliente` | `codigo_cliente` | **Empresa** | Cliente de ventas por empresa. |
| `hcm_empleado` | `codigo_empleado` | **Empresa** | Nómina por empresa legal. |
| `log_transportista` | `codigo_transportista` | **Empresa** | Operación logística por empresa. |
| `log_ruta` | `codigo_ruta` | **Empresa** | Idem. |
| `mfg_centro_trabajo` | `codigo` | **Empresa** | Planta por empresa. |
| `mfg_operacion` | `codigo` | **Empresa** | Idem. |
| `mfg_lista_materiales` | `codigo_bom` | **Empresa** | BOM por empresa. |
| `mfg_ruta_fabricacion` | `codigo_ruta` | **Empresa** | Idem. |
| `mnt_activo` | `codigo_activo` | **Empresa** | Activo contable/operativo por empresa. |
| `mnt_plan_mantenimiento` | `codigo_plan` | **Empresa** | Idem. |
| `mrp_plan_maestro` | `codigo_plan` | **Empresa** | Planificación por empresa. |
| `mps_plan_produccion` | `codigo_plan` | **Empresa** | Idem. |
| `crm_campana` | `codigo_campana` | **Empresa** | Campaña comercial por empresa. |
| `prc_lista_precio` | `codigo_lista` | **Empresa** | Política de precios por empresa. |
| `prc_promocion` | `codigo_promocion` | **Empresa** | Idem. |
| `fin_plan_cuentas` | `codigo_cuenta` | **Empresa** | Plan contable por empresa (multiempresa es estándar en ERP). |
| `hcm_concepto_planilla` | `codigo_concepto` | **Empresa** | Conceptos de nómina por empresa. |
| `qms_parametro_calidad` | `codigo` | **Empresa** | Calidad por empresa. |
| `qms_plan_inspeccion` | `codigo` | **Empresa** | Idem. |
| `pos_punto_venta` | `codigo_punto_venta` | **Empresa** | Terminal por empresa (FK sucursal). |
| `invbill_serie_comprobante` | `serie` | **Empresa** + tipo | Serie fiscal asignada por empresa y tipo de comprobante. |
| `bdg_presupuesto` | `codigo_presupuesto` | **Empresa** | Presupuesto por empresa. |
| `cst_centro_costo_tipo` | `codigo` | **Empresa** | Costos por empresa. |
| `pm_proyecto` | `codigo_proyecto` | **Empresa** | Proyecto por empresa. |
| `bi_reporte` | `codigo_reporte` | **Empresa** | Reporte configurable por empresa. |
| `wfl_flujo_trabajo` | `codigo_flujo` | **Empresa** | Flujo por empresa. |
| `dms_documento` | `codigo_documento` | **Empresa** | Gestión documental por empresa. |

### 2.2 Documentos (grupo C)

| Entidad | Campo(s) | Scope recomendado | Justificación |
|---------|----------|-------------------|---------------|
| `inv_movimiento` | `numero_movimiento` | **Empresa** | UNIQUE por empresa; kardex y stock son empresa-scoped. |
| `inv_inventario_fisico` | `numero_inventario` | **Empresa** | Conteo por empresa (aunque ocurre en un almacén). |
| `pur_solicitud_compra` | `numero_solicitud` | **Empresa** | Proceso de compras por empresa. |
| `pur_cotizacion` | `numero_cotizacion` | **Empresa** | Idem. |
| `pur_orden_compra` | `numero_oc` | **Empresa** | OC legalmente emitida por empresa. |
| `pur_recepcion` | `numero_recepcion` | **Empresa** | Idem. |
| `log_guia_remision` | `serie`, `numero` | **Empresa** + **Serie** | Correlativo SUNAT por serie de guía. |
| `log_despacho` | `numero_despacho` | **Empresa** | Operación logística. |
| `mfg_orden_produccion` | `numero_op` | **Empresa** | OP por planta/empresa. |
| `mnt_orden_trabajo` | `numero_ot` | **Empresa** | OT por empresa. |
| `sls_cotizacion` | `numero_cotizacion` | **Empresa** | Ventas por empresa. |
| `sls_pedido` | `numero_pedido` | **Empresa** | Idem. |
| `crm_oportunidad` | `numero_oportunidad` | **Empresa** | Pipeline comercial por empresa. |
| `invbill_comprobante` | `serie`, `numero` | **Empresa** + **Serie** | Numeración fiscal; `invbill_serie_comprobante.numero_actual`. |
| `pos_turno_caja` | `numero_turno` | **Punto de venta** | UNIQUE incluye `punto_venta_id`. |
| `pos_venta` | `numero_venta` | **Empresa** (o PV*) | UNIQUE solo empresa; *evaluar extensión por PV en alto volumen retail. |
| `hcm_contrato` | `numero_contrato` | **Empresa** | Contrato laboral por empleador. |
| `hcm_planilla` | `numero_planilla` | **Empresa** | Periodo de nómina por empresa. |
| `hcm_prestamo` | `numero_prestamo` | **Empresa** | Idem. |
| `fin_asiento_contable` | `numero_asiento` | **Empresa** | Asiento por libro de empresa. |
| `qms_inspeccion` | `numero_inspeccion` | **Empresa** | Calidad por empresa. |
| `qms_no_conformidad` | `numero_nc` | **Empresa** | Idem. |
| `wms_tarea` | `numero_tarea` | **Almacén** | UNIQUE por `almacen_id`. |
| `svc_orden_servicio` | `numero_os` | **Empresa** | Servicio post-venta. |
| `tkt_ticket` | `numero_ticket` | **Empresa** | Soporte por empresa. |

---

## 3. Entidades que NO deben usar el motor centralizado

| Entidad | Motivo |
|---------|--------|
| Catálogos `cat_*` | Datos globales; sin secuencia tenant. |
| `numero_documento` (terceros) | Asignado por SUNAT/RENiec, no secuencial interno. |
| `numero_serie` (lote/trazabilidad) | Identificador de fabricación o lote; no correlativo. |
| `codigo_barra`, `codigo_fabricante` | Estándares externos. |
| `codigo_hash`, `codigo_qr`, `codigo_respuesta_sunat` | Generados por OSE/SUNAT o algoritmos fiscales. |
| `org_parametro_sistema` | Clave-valor de configuración. |
| `cliente.codigo_cliente` (V020) | Provisioning SaaS; manual en onboarding. |
| `prc_promocion.codigo_cupon` | Puede ser aleatorio de campaña; política distinta. |

---

## 4. Desalineación detectada: onboarding vs. modelo

El seed actual `SECUENCIAS_CODIGO` en `cliente_onboarding_service.py` inserta **9 entidades** con `empresa_id = NULL` (scope tenant):

```
org_empresa, org_sucursal, org_departamento, org_cargo, org_centro_costo,
inv_almacen, inv_producto, inv_categoria, inv_movimiento
```

| Entidad seed | Scope en SECUENCIAS_CODIGO | Scope real en UNIQUE V010 | ¿Alineado? |
|--------------|---------------------------|---------------------------|------------|
| `org_empresa` | Cliente (NULL) | Cliente | ✅ |
| `org_sucursal` | Cliente (NULL) | Empresa | ❌ |
| `org_departamento` | Cliente (NULL) | Empresa | ❌ |
| `org_cargo` | Cliente (NULL) | Empresa | ❌ |
| `org_centro_costo` | Cliente (NULL) | Empresa | ❌ |
| `inv_almacen` | Cliente (NULL) | Empresa | ❌ |
| `inv_producto` | Cliente (NULL) | Empresa | ❌ |
| `inv_categoria` | Cliente (NULL) | Empresa | ❌ |
| `inv_movimiento` | Cliente (NULL) | Empresa | ❌ |

**Conclusión F15:** el estándar de secuencia debe declarar que **solo `org_empresa` es tenant-scoped** entre las entidades seed actuales. El resto requiere `empresa_id` en la configuración de secuencia (o secuencia lazy al crear la primera empresa).

---

## 5. Reglas normativas propuestas (estándar F15)

1. **Regla R-SEC-01:** El scope de secuencia debe derivarse del constraint UNIQUE de la entidad, no de convención de nombres.
2. **Regla R-SEC-02:** Correlativos documentales son siempre **por empresa** salvo excepción explícita documentada.
3. **Regla R-SEC-03:** Entidades WMS con UNIQUE por `almacen_id` requieren dimensión `almacen_id` en el motor (Fase 2).
4. **Regla R-SEC-04:** Documentos fiscales requieren dimensión `serie_id` o `(tipo_comprobante, serie)` y sincronización con `invbill_serie_comprobante.numero_actual`.
5. **Regla R-SEC-05:** `pos_turno_caja` requiere dimensión `punto_venta_id`.
6. **Regla R-SEC-06:** Multiempresa dentro de un tenant implica secuencias **aisladas por empresa**; no reutilizar el mismo número en empresas distintas salvo política corporativa explícita (fuera de scope V010).

---

## 6. Matriz resumen scope

| Scope | # Maestros | # Documentos | Ejemplo |
|-------|------------|--------------|---------|
| Cliente (tenant) | 1 | 0 | `org_empresa.codigo_empresa` |
| Empresa | 35 | 22 | `numero_oc`, `codigo_sku` |
| Almacén | 2 | 1 | `wms_ubicacion`, `wms_tarea` |
| Punto de venta | 0 | 1 | `pos_turno_caja` |
| Empresa + Serie fiscal | 1 | 2 | `invbill_comprobante`, `log_guia_remision` |

---

*Estado actual y riesgos: `04_CURRENT_STATE_AND_RISKS.md`.*
