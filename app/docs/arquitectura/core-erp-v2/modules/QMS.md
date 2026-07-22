# Auditoría modular — QMS

**Módulo:** QMS  
**Prioridad global:** P1 (lote_id P0 acoplado a INV)

---

## Estado actual (V010)

Básico. Plan de inspección, inspección cabecera-detalle, no conformidad. Lote textual.

## Fortalezas

- Estructura inspección + NC usable multi-rubro.
- Estados y trazabilidad documental básica.

## Debilidades

- Sin FK a lote formal.
- Opciones de parámetro en JSON.
- Sin CAPA/SPC enterprise.
- Riesgo de FK circular lote↔inspección (propuesta B).

## Cambios recomendados

1. `lote_id` en `qms_inspeccion` y `qms_no_conformidad`.
2. QC de ingreso actualiza estado del AR `inv_lote` (dirección única: inspección → lote).
3. Diferir CAPA/SPC a fase QMS Enterprise (ADR-07).

## Justificación

Calidad sin lote formal no sirve para recall ni cuarentena.

## Prioridad

**P0** vínculo lote / **P2** CAPA enterprise

## Impacto

Alto en industrias reguladas; medio en resto.

## Riesgos

- Acoplar QMS a verticales vía parámetros hardcodeados.
- Circularidad de FKs.
