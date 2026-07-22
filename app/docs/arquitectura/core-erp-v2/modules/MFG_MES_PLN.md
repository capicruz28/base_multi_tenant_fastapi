# Auditoría modular — MFG / MES / PLN

**Módulos:** MFG, MES (nuevo), PLN (nuevo)  
**Prioridad global:** P1

---

## Estado actual (V010)

**MFG básico:** CT, operación, BOM, ruta, OP, consumo (lote string).  
**MES:** ausente.  
**PLN:** ausente (capacidad estática en CT / número en MPS).

## Fortalezas

- Modelo clásico manufactura discreta (BOM + routing + OP).
- Consumo de materiales ya existe como punto de extensión de lote.

## Debilidades

- Sin ejecución de piso / OEE.
- Sin calendario de capacidad.
- Sustitutos BOM en JSON.
- Propuestas A/B meten APS prematuro junto a estas capas.

## Cambios recomendados

### MFG
- Conservar tablas V010.
- `lote_id` en `mfg_consumo_materiales`.
- No crecer con OEE ni scheduling.

### MES (nuevo, ADR-02)
- `mes_ejecucion_operacion`
- `mes_parada_maquina`
- `mes_motivo_parada` (OEE: disponibilidad/rendimiento/calidad) — modelo B
- Anclar CT, OP, operario (HCM)

### PLN (nuevo, ADR-01)
- Calendario de capacidad por CT/fecha/turno (preferir B: eficiencia, no productivas)
- Excepciones laborable/feriado/mantenimiento
- **No** tablas APS

## Justificación

Separación MFG/MES/PLN es estándar industrial y prepara APS futuro sin implementarlo.

## Prioridad

**P1**

## Impacto

Alto para cualquier vertical manufacturero; habilita OEE y CRP.

## Riesgos

- Duplicar consumo MFG vs eventos MES.
- Meter APS “de contrabando” en PLN.
- Motivos de parada demasiado específicos de un rubro (mantener genéricos OEE).
