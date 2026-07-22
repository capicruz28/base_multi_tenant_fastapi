# Comparación propuestas Claude A vs B y fusión CORE V2

**Documento:** 05  
**Fuentes:** `script_core_v2_claudeA.sql`, `script_core_v2_claudeB.sql`  
**Principio:** ninguna es correcta por defecto.

---

## 1. Inventario

### Tablas nuevas comunes (12)

`cfg_vertical_empresa`, `inv_lote`, `inv_producto_variante`, `wms_oleada`, `mfg_calendario_capacidad`, `mes_ejecucion_operacion`, `mes_parada_maquina`, `aps_escenario`, `alr_regla_alerta`, `alr_alerta_generada`, `rpt_metrica`, `rpt_dimension`

### Solo A

`aps_carga_centro_trabajo`, `aps_secuencia_operacion`, `aps_simulacion_impacto`

### Solo B

`mes_motivo_parada`, `aps_tarea_programada`, `aps_restriccion_recurso`

### Tablas modificadas (ambas)

`inv_almacen`, `wms_ubicacion`, `wms_tarea`, `inv_movimiento_detalle`, `wms_stock_ubicacion`, `qms_inspeccion`, `qms_no_conformidad`, `pur_recepcion_detalle`, `mfg_consumo_materiales`, `invbill_comprobante_detalle`

---

## 2. Matriz por capacidad → decisión CORE V2

| Capacidad | Mejor fuente | Decisión | Notas |
|-----------|--------------|----------|-------|
| Verticales CFG | **A** | Adoptar A | Descartar JSON/plan de B |
| `inv_lote` | **B** (+ soft-delete A) | Adoptar mejorado | Cantidades + FEFO; sin QC circular; `es_activo` |
| Variantes | **Híbrido** | Adoptar | SKU FK (A) + ejes (ambos); sin `referencia_id` vertical |
| Estrategia salida | **A** | Adoptar | CHECK + casing único; default configurable (no FEFO ciego global) |
| Oleada WMS | **B** | Adoptar | Avance / criterio |
| QMS `lote_id` | Empate | Adoptar | Vínculo direccional a lote |
| MES | **B** | Adoptar | Incluye `mes_motivo_parada` |
| Calendario / PLN | **B** | Adoptar bajo PLN | Eficiencia / no productivas |
| APS | Ninguno entero | **Diferir físico** | Solo ADR-09 |
| ALR | Híbrido | Rediseñar sobre EVT | No ALR-as-bus |
| RPT | Ninguno listo | **Diferir físico** | Prohibir SQL libre (B) |

---

## 3. Dónde A es superior (técnico)

1. CFG vertical con CHECK de códigos y sin spillover JSON.
2. Integridad de estrategia WMS (CHECK).
3. Naming compatible con V010 (`lote` no renombrado a `lote_codigo`).
4. APS de impacto/carga (útil *cuando* exista motor — ahora prematuro).
5. Variante ligada a `inv_producto` existente.
6. Script coherente (FKs en CREATE; B contradice “no ALTER” con ALTER de FKs).

---

## 4. Dónde B es superior (técnico)

1. Lote operativo (reservado/bloqueado, FEFO index, costo, almacén).
2. MES/OEE con catálogo de motivos.
3. Ejecución MES anclada a CT/OP/HCM.
4. Oleada con avance y criterio de agrupación.
5. APS con restricciones/tareas (mejor *forma* futura, aún prematuro).
6. Calendario de capacidad real (eficiencia).
7. ALR con scheduling de evaluación / anti-spam.

---

## 5. Riesgos compartidos a no repetir

| Riesgo | Evidencia | Mitigación CORE V2 |
|--------|-----------|-------------------|
| Spillover vertical | B `configuracion_json`, `referencia_id` | CFG limpio; variantes sin FK vertical |
| APS prematuro | Ambas | Sin tablas `aps_*` ahora |
| RPT peligroso | B SQL WHERE | Diferir; AST/JSON schema después |
| JSON como lógica | Ambas | ADR-10 |
| Polimorfismo sin FK | B APS `recurso_id` | Rechazar patrón |
| Stock no lotificado | Ninguna resuelve del todo | Rediseñar `inv_stock` en fase tablas |
| Event Bus ausente | Ambas (solo ALR) | ADR-03 |

---

## 6. Capacidad faltante en A y B (propia del CORE V2)

1. **Event Bus / outbox** como infraestructura.
2. **Stock lotificado** explícito (`inv_stock` por lote).
3. **Separación documental PLN** (módulo, no solo tabla bajo MFG).
4. Corrección **MRP `empresa_id`**.
5. Política clara **serie** (si aplica) como AR hermano de lote — mencionada en flags V010, no formalizada en A/B.
6. Contrato de **idempotencia / correlation** para alertas e integraciones.

---

## 7. Regla de fusión oficial

```
CORE V2 = V010 (preservar)
        + selectivo(A, B) según matriz §2
        + ADR propios (Event Bus, PLN, diferir APS/RPT)
        − spillover vertical
        − sobre-modelado prematuro
```
