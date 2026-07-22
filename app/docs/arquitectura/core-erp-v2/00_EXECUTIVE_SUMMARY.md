# CORE ERP V2 — Resumen Ejecutivo de Auditoría Arquitectónica

**Estado:** Auditoría oficial (diseño cerrado a nivel conceptual)  
**Fecha:** 2026-07-22  
**Alcance:** Evaluación de `V010` + propuestas `script_core_v2_claudeA.sql` / `script_core_v2_claudeB.sql`  
**Restricción:** Sin SQL, sin migraciones, sin ALTER. Prioridad = mejor diseño posible.

---

## Veredicto en una frase

El Core V010 es un **mapa amplio y agnóstico** de ERP industrial SaaS, sólido en patrones multi-tenant/multiempresa, pero **no enterprise-ready** en lotes, variantes, WMS, calidad, ejecución de piso ni planificación. Las propuestas A y B aciertan en el diagnóstico; **ninguna debe adoptarse íntegra**. El CORE V2 debe ser un **híbrido selectivo** + decisiones propias (Event Bus, PLN, diferir APS físico).

---

## Fuentes evaluadas

| Fuente | Rol | Hallazgo |
|--------|-----|----------|
| `V010__tablas_bd_erp_completo.sql` | Baseline actual (~116 tablas, 27 módulos) | Cobertura amplia; profundidad desigual; lote como `NVARCHAR`; sin MES/APS/ALR/RPT/verticales |
| `script_core_v2_claudeA.sql` | Propuesta A (~15 nuevas + 10 modificadas) | Mejor control-plane vertical + integridad CHECK; APS orientado a resultado/impacto; compatible con naming V010 |
| `script_core_v2_claudeB.sql` | Propuesta B (~15 nuevas + 10 modificadas) | Mejor lote operativo + MES/OEE + oleada + calendario; spillover JSON vertical; APS más ejecutable pero prematuro; RPT con SQL libre (riesgo) |

---

## Regla aplicada (obligatoria)

> Si una capacidad la usa la **mayoría de industrias manufactureras** → **Core**.  
> Si representa conocimiento específico de una industria → **Vertical**.

Aplicación rigurosa: color/talla como ejes genéricos de variante = Core; galgas textiles / 4 puntos / catálogos TXT = Vertical.

---

## Decisiones preliminares — resultado

| # | Idea | Decisión CORE V2 |
|---|------|------------------|
| 1 | PLN como módulo Core | **Aprobado** (capa de capacidad/calendario; no APS) |
| 2 | MFG separado de MES | **Aprobado** |
| 3 | Event Bus Core; ALR = consumidor | **Aprobado** (ALR no es el bus) |
| 4 | `inv_lote` Aggregate Root | **Aprobado** |
| 5 | Variantes de producto genéricas | **Aprobado** (modelo híbrido A+B) |
| 6 | WMS Enterprise | **Aprobado en fases** (oleada + estrategia ahora; slotting/putaway después) |
| 7 | QMS Enterprise | **Aprobado en fases** (`lote_id` ahora; CAPA/enterprise después) |
| 8 | RPT capa semántica | **Diferido** (contrato conceptual sí; tablas físicas no todavía) |
| 9 | APS solo arquitectura preparada | **Aprobado** — **sin tablas APS físicas ahora** |
| 10 | JSON solo atributos altamente variables | **Aprobado** como principio normativo |

Detalle: `03_PRELIMINARY_ADR_DECISIONS.md`.

---

## Qué adoptar / descartar / mejorar / diferir

### Adoptar (Core-válido, prioridad alta)

- Formalizar **`inv_lote`** + `lote_id` en movimiento, stock ubicación, recepción, consumo MFG, QMS, factura.
- **Estrategia de salida** (FIFO/FEFO/LEFO/MANUAL) en almacén → override ubicación, con CHECK.
- **`wms_oleada`** + vínculo en `wms_tarea`.
- **`cfg_vertical_empresa`** como control-plane limpio (estilo A: sin JSON de vertical).
- **MES** (`mes_ejecucion_operacion`, `mes_parada_maquina`, catálogo `mes_motivo_parada`).
- **`mfg_calendario_capacidad`** bajo módulo **PLN** (capacidad finita básica).
- **Event Bus interno** + **ALR** como consumidor (no ALR como bus).
- **Variantes genéricas** (`inv_producto_variante`) con ejes tipados + SKU integrado a `inv_producto`.

### Mejorar respecto a A/B

| Capacidad | Preferir de | Ajuste CORE V2 |
|-----------|-------------|----------------|
| Verticales | A | Sin `configuracion_json` / `modulos_activos` verticales |
| Lote | B | Cantidades reservada/bloqueada + FEFO; sin FK circular QC incompleta; mantener `es_activo` |
| Variantes | Híbrido | Ejes tipados + FK a producto SKU (A); sin `referencia_id` a catálogos verticales |
| Estrategia WMS | A | CHECK + convención casing única (`fifo`/`fefo`/…) |
| Oleada | B | Avance / criterio agrupación |
| MES | B | Motivos OEE + CT/OP anclados |
| Calendario | B | Eficiencia / no productivas |
| ALR | Híbrido | Tipado de condiciones (A) + scheduling/anti-spam (B), sobre Event Bus |

### Descartar (no entrar al Core físico V2)

- APS completo (escenarios, Gantt, restricciones, simulación de impacto) como tablas ahora.
- `configuracion_json` / ejemplos TXT en CFG vertical.
- `atributo_N_referencia_id` hacia catálogos de vertical desde Core.
- RPT con `filtro_base` = SQL libre (B).
- Renombrar `lote` → `lote_codigo` como breaking innecesario (diseño limpio: `lote_id` + `codigo_lote` en aggregate; texto legado solo si se mantiene dual temporal — en greenfield: solo `lote_id`).

### Diferir (arquitectura sí, implementación física no)

- APS (dejar extensiones PLN/MES listas).
- RPT semántica autoservicio.
- WMS slotting / putaway rules / cross-dock enterprise.
- QMS CAPA / SPC enterprise.
- FIN CxC/CxP/bancos (gap real, pero fuera del foco de esta oleada de “fortalecimiento industrial”; documentado como deuda Core).

---

## Definición CORE V2 (capa conceptual)

El CORE V2 es la plataforma ERP Industrial SaaS multi-tenant/multiempresa que:

1. Conserva el mapa V010 de módulos operativos.
2. Eleva a enterprise las capacidades transversales manufactureras: **lote, variantes, WMS oleada/estrategia, QMS trazable, MES, PLN capacidad, Event Bus + ALR**.
3. Introduce **control-plane de verticales** sin semántica de industria en el Core.
4. Separa **MFG (planificación/definición)** de **MES (ejecución de piso)**.
5. Deja **APS y RPT semántica** como extensiones preparadas, no como esquema físico inmediato.
6. Mantiene JSON solo para atributos altamente variables, nunca para lógica de negocio estructurada.

Documento canónico: `90_CORE_V2_DEFINITION.md`.

---

## Priorización de ola de diseño (sin SQL aún)

| Prioridad | Capacidad | Impacto |
|-----------|-----------|---------|
| P0 | `inv_lote` Aggregate Root + FKs | Desbloquea trazabilidad multi-rubro |
| P0 | Estrategia salida + FEFO operativo | Inventario real en alimentos/farma/distribución |
| P0 | Variantes genéricas | SKU multi-eje sin spillover textil |
| P1 | WMS oleada | Productividad almacén |
| P1 | MES + motivos parada | OEE transversal manufactura |
| P1 | PLN calendario capacidad | Base para CRP; prepara APS futuro |
| P1 | Event Bus + ALR consumidor | Infra transversal |
| P1 | `cfg_vertical_empresa` limpio | Gobernanza multi-vertical |
| P2 | QMS endurecido (CAPA/ligazón lote↔inspección) | Calidad enterprise |
| P3 | APS (solo ADR + puntos de extensión) | Evitar sobre-modelado |
| P3 | RPT semántica (contrato) | Evitar SQL dinámico prematuro |

---

## Riesgos globales

1. **Sobre-modelar APS/RPT** antes de tener consumidores → tablas huérfanas.
2. **Meter vertical en Core** vía JSON/CFG → destruye agnosticismo 10–15 años.
3. **Lote sin stock lotificado** (`inv_stock` sigue agregado) → aggregate incompleto si no se redefine stock.
4. **Event Bus mal implementado como solo ALR** → alertas sin integración entre módulos.
5. **Variantes duplicando maestro producto** sin política clara SKU → doble verdad.

---

## Lectura recomendada

1. `01_METHODOLOGY_AND_SOURCES.md`
2. `02_CORE_VS_VERTICAL_CLASSIFICATION.md`
3. `03_PRELIMINARY_ADR_DECISIONS.md`
4. `04_V010_BASELINE.md`
5. `05_PROPOSAL_A_VS_B.md`
6. `modules/*` (auditoría por módulo)
7. `90_CORE_V2_DEFINITION.md`
8. `91_DESIGN_ROADMAP.md`

**Siguiente paso autorizado tras cierre de esta auditoría:** diseño de modelo de datos definitivo (tablas) — aún no scripts SQL de bootstrap.
