# Decisiones preliminares (ADR de diseño CORE V2)

**Documento:** 03  
**Serie:** CORE ERP V2 — Auditoría arquitectónica oficial  
**Estado:** Aprobadas a nivel de arquitectura (pre-SQL)

---

## ADR-01 — PLN como módulo Core

### Contexto
V010 tiene MFG (BOM/ruta/OP), MRP y MPS, pero **no** un módulo de capacidad/calendario. A y B proponen `mfg_calendario_capacidad` bajo MFG/PLN implícito.

### Decisión
**PLN es módulo Core** separado conceptualmente:

- Responsabilidad: capacidad disponible, calendarios de recursos (CT), excepciones (feriados, paradas programadas), inputs a CRP.
- No incluye scheduling avanzado (eso es APS).
- `mfg_calendario_capacidad` (o rename futuro `pln_calendario_capacidad`) vive bajo PLN.

### Justificación
Toda planta manufacturera necesita saber cuántas horas tiene un centro de trabajo por día. Es Core, no Vertical. Colocar calendarios solo como campo en `mfg_centro_trabajo` es insuficiente.

### Consecuencias
- Índice/documentación: nuevo módulo PLN.
- MFG se enfoca en definición y órdenes; MES en ejecución; PLN en capacidad.
- APS futuro consume PLN, no lo reemplaza.

---

## ADR-02 — MFG separado de MES

### Contexto
V010 mezcla “definición + OP” en MFG y no modela shop-floor. A y B introducen MES.

### Decisión
**Separar MFG y MES:**

| Módulo | Responsabilidad |
|--------|-----------------|
| MFG | CT, operaciones, BOM, rutas, OP, consumo planificado/registrado de materiales |
| MES | Ejecución real de operaciones, eventos de piso, paradas, motivos OEE, tiempos reales |

### Justificación
Es el estándar industrial (ISA-95 / práctica ERP+MES). Mezclar ejecución OEE dentro de MFG acopla planificación con telemetría de piso y complica verticales (IoT, scrap, etc.).

### Consecuencias
- Prefijo de tablas `mes_*`.
- MFG no debe crecer con tablas de OEE.
- Consumo de materiales puede permanecer en MFG o emitirse desde MES vía Event Bus — decisión de diseño de tablas posterior; arquitectura: **una sola verdad de consumo**.

---

## ADR-03 — Event Bus interno Core; ALR es consumidor

### Contexto
A y B proponen `alr_regla_alerta` / `alr_alerta_generada` como “motor de alertas”. Eso es insuficiente como integración entre módulos.

### Decisión
Introducir **Event Bus interno** como infraestructura Core:

1. Productores: INV, WMS, QMS, MFG, MES, PUR, SLS, LOG, FIN, … emiten eventos de dominio.
2. Contrato: tipo de evento, aggregate, tenant/empresa, payload versionado, timestamp, correlation id.
3. **ALR** es **un consumidor** (reglas → notificaciones/bandeja).
4. Otros consumidores futuros: WFL, RPT projections, verticales, integraciones.

### Justificación
En SaaS industrial 10–15 años, el acoplamiento síncrono entre módulos no escala. Alertas sin bus generan polling ad-hoc y duplicación. El bus es infraestructura; ALR es producto.

### Consecuencias
- Diseño físico posterior: `evt_evento` / outbox (o equivalente) + suscripciones.
- Tablas ALR de A/B se rediseñan para suscribirse a tipos de evento, no solo a “umbrales sobre tablas”.
- Prohibido: que ALR sea el único mecanismo de integración.

### Nota
El detalle de tablas del bus se define en la fase de diseño de datos, no en esta auditoría. Aquí queda **mandatorio a nivel arquitectura**.

---

## ADR-04 — `inv_lote` como Aggregate Root

### Contexto
V010 usa `lote NVARCHAR(50)` en ≥9 tablas. Stock (`inv_stock`) no dimensiona por lote. A y B formalizan `inv_lote`.

### Decisión
**`inv_lote` es Aggregate Root** de trazabilidad de partida/lote:

- Identidad: `(cliente_id, empresa_id, producto_id, codigo_lote)` (o equivalente).
- Estado de ciclo de vida: disponible / cuarentena / bloqueado / vencido / agotado / rechazado.
- Cantidades: inicial, disponible, reservada, bloqueada (estilo B).
- Origen tipado (compra, producción, devolución, apertura, ajuste) con referencias documentales.
- Todas las tablas operativas referencian `lote_id` (FK), no strings sueltos.
- En greenfield: **eliminar** dependencia de `lote` NVARCHAR como verdad; opcionalmente conservar código denormalizado de solo lectura.

### Justificación
Sin aggregate, no hay FEFO real, ni QC de ingreso, ni recall, ni WMS lotificado. Es la capacidad #1 faltante del Core industrial.

### Consecuencias
- `inv_stock` debe evolucionar a stock por (producto, almacén, **lote**[, ubicación vía WMS]) — decisión de modelo en fase tablas.
- QMS/WMS/PUR/MFG/INV_BILL dependen del AR.
- `atributos_lote` JSON solo para atributos variables no transaccionales.

---

## ADR-05 — Modelo genérico de variantes de producto

### Contexto
V010 tiene `color`/`talla` planos + JSON. A: dimensiones + FK a SKU producto. B: variante como SKU propio + `referencia_id` vertical.

### Decisión
**Variantes genéricas en Core:**

- Tabla `inv_producto_variante` (o política “cada variante ES un `inv_producto` hijo” — ver definición CORE V2).
- Hasta N ejes tipados (`atributo_k_nombre` / `atributo_k_valor`) + JSON `atributos_extra` para rarezas.
- Integración obligatoria con maestro stockeable (`inv_producto`).
- **Prohibido** en Core: FKs/referencias a catálogos de Vertical.

### Justificación
Color/talla/voltaje/envase son multi-industria. Matrices textiles rígidas o NDC farma son Vertical.

### Consecuencias
- Deprecar semánticamente `color`/`talla` fijos a largo plazo (migración conceptual → ejes).
- Pricing: preferir PRC; evitar duplicar precio solo en variante salvo snapshot.

---

## ADR-06 — WMS Enterprise (faseado)

### Contexto
V010: zonas, ubicaciones, stock ubicación, tareas. Sin oleadas ni estrategia salida. A/B añaden ambos.

### Decisión
**WMS Enterprise en fases:**

| Fase | Alcance |
|------|---------|
| V2.0 (ahora, diseño) | Estrategia salida almacén/ubicación + `wms_oleada` + `lote_id` en stock ubicación/tarea |
| V2.1 | Putaway rules, reabastecimiento, task interleaving |
| V2.2 | Slotting, yard, cross-dock, labor management |

### Justificación
Oleada + FEFO son el mínimo enterprise multi-rubro. Slotting/yard no bloquean el Core V2 inicial.

---

## ADR-07 — QMS Enterprise (faseado)

### Contexto
V010 tiene plan/inspección/NC con lote string. A/B añaden `lote_id`.

### Decisión
**Fase 1:** `lote_id` en inspección y NC; estados QC del lote en el AR.  
**Fase 2:** CAPA estructurada, muestreo, SPC, certificaciones.  
Evitar FK circular incompleta lote↔inspección (problema B); modelar vínculo explícito y direccional.

### Justificación
Trazabilidad lote↔calidad es Core. SPC/CAPA enterprise no deben bloquear V2.0.

---

## ADR-08 — RPT con capa semántica

### Contexto
A: métricas/dimensiones con filtros JSON. B: filtros como SQL WHERE. V010 `bi_reporte` es placeholder peligroso (SQL libre).

### Decisión
- **Aprobar el concepto** de capa semántica RPT.
- **No implementar tablas físicas** en la primera oleada de diseño Core V2.
- Prohibir SQL libre en metadatos.
- Cuando se implemente: métricas/dimensiones versionadas, filtros estructurados (AST/JSON schema), scope tenant/empresa consistente.

### Justificación
Sin gobierno semántico, RPT se convierte en vector de inyección y deuda. Prematuro frente a P0 industriales.

---

## ADR-09 — APS: arquitectura preparada, sin físico aún

### Contexto
A modela resultados (carga, secuencia, impacto). B modela motor (tareas, restricciones). Ambos prematuros.

### Decisión
**No crear tablas `aps_*` ahora.**

Preparar arquitectura:

- PLN (capacidad) + MES (tiempos reales) + MFG (OP/ruta) como inputs futuros.
- ADR APS futuro: escenarios, restricciones tipadas (no `recurso_id` polimórfico sin FK), precedencias relacionales o grafo versionado.
- Extensibilidad: no pintar campos “APS” en MFG que contaminen el Core.

### Justificación
Sin motor ni consumidores, APS es sobre-modelado. El usuario lo pidió explícitamente; se confirma.

---

## ADR-10 — JSON solo para atributos altamente variables

### Contexto
V010 y A/B abusan de JSON para sustitutos BOM, workflow, promo, config vertical, predecessores APS, filtros RPT.

### Decisión
**Norma:**

| Permitido JSON | Prohibido JSON |
|----------------|----------------|
| Atributos descriptivos variables por industria (`atributos_lote`, specs) | Estados, transiciones, cantidades, FKs |
| Config UI no transaccional | Reglas de negocio evaluadas en transacciones |
| Payloads de evento versionados (con schema) | Grafos de precedencia / listas de IDs como única verdad |

Toda lista de IDs o regla que participe en integridad → **tabla relacional**.

### Justificación
JSON escondiendo lógica destruye validación, RBAC fino, reporting e integridad multi-tenant.

---

## Resumen de votación

| ADR | Decisión |
|-----|----------|
| 01 PLN Core | Aprobado |
| 02 MFG ≠ MES | Aprobado |
| 03 Event Bus + ALR consumidor | Aprobado |
| 04 inv_lote AR | Aprobado |
| 05 Variantes genéricas | Aprobado |
| 06 WMS Enterprise faseado | Aprobado |
| 07 QMS Enterprise faseado | Aprobado |
| 08 RPT semántica | Concepto sí / físico diferido |
| 09 APS | Solo arquitectura / sin tablas |
| 10 JSON disciplinado | Aprobado |
