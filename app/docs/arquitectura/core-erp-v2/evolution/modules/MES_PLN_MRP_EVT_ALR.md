# Evolución modular — MES / PLN / MRP / MPS / EVT / ALR

**Fase D1 · modules**

---

## MES (nuevo BC)

| Campo | Contenido |
|-------|-----------|
| Estado V1 | Ausente |
| Conservar | N/A |
| Extender | N/A (no existe qué extender sin contaminar MFG) |
| Rediseñar | — |
| Tablas nuevas | `mes_ejecucion_operacion` (C2+C1), `mes_parada_maquina` (C4), `mes_motivo_parada` (C4) |
| Justificación | ADR-02; OEE no cabe en extensión de OP |
| Impacto código | Código **nuevo** (`app/modules/mes`); MFG intacto |
| Prioridad | **P1** |

---

## PLN (nuevo BC)

| Campo | Contenido |
|-------|-----------|
| Estado V1 | Ausente como módulo |
| Conservar | Capacidad estática en `mfg_centro_trabajo` como dato auxiliar (no elimina calendario) |
| Extender | Opcional: nada obligatorio en CT |
| Rediseñar | — |
| Tablas nuevas | **`pln_calendario_capacidad`** (C2+C3) — nombre final D1.1 |
| Justificación | Serie temporal de capacidad; no es campo de CT |
| Impacto código | Módulo/servicios nuevos; MFG solo lectura de CT |
| Prioridad | **P1** |

**Prohibido:** tablas APS.

---

## MRP

| Campo | Contenido |
|-------|-----------|
| Estado V1 | Medio |
| Conservar | `mrp_plan_maestro`, `mrp_orden_sugerida` (estructura) |
| Extender | `mrp_necesidad_bruta`, `mrp_explosion_materiales` ← **`empresa_id`** (corrección Fase 4) |
| Rediseñar | — |
| Tablas nuevas | — |
| Justificación | Integridad multiempresa; no nueva capacidad |
| Impacto código | Medio (queries/services) |
| Prioridad | **P1** |

---

## MPS

| Campo | Contenido |
|-------|-----------|
| Estado V1 | Medio |
| Conservar | Pronóstico, plan, detalle |
| Extender | — en ola industrial |
| Rediseñar | — |
| Tablas nuevas | — |
| Justificación | Capacidad agregada numérica basta hasta que PLN alimente mejor |
| Impacto código | Bajo |
| Prioridad | P2 |

---

## EVT (nuevo BC infra)

| Campo | Contenido |
|-------|-----------|
| Estado V1 | Ausente |
| Conservar | — |
| Extender | **No** reutilizar `aud_log_auditoria` como bus |
| Rediseñar | — |
| Tablas nuevas | Mínimo outbox/evento (C2) — detalle en D1.1 |
| Justificación | Domain Events ≠ auditoría técnica |
| Impacto código | Infra nueva (`app/core` o módulo); productores V1 emiten de forma aditiva |
| Prioridad | **P1** |

---

## ALR (nuevo BC)

| Campo | Contenido |
|-------|-----------|
| Estado V1 | Ausente |
| Conservar | — |
| Extender | — |
| Rediseñar | — |
| Tablas nuevas | `alr_regla_alerta`, `alr_alerta_generada` (C2) |
| Justificación | Consumidor de EVT; no es CFG ni AUD |
| Impacto código | Módulo nuevo |
| Prioridad | **P1** |

---

## APS / RPT

| Campo | Contenido |
|-------|-----------|
| Tablas nuevas | **Ninguna** |
| Justificación | ADR-08/09 + principio de evolución mínima |
| Prioridad | Diferir |
