# Auditoría modular — Placeholders (PM / SVC / TKT / BI / DMS / WFL / AUD)

**Prioridad global:** P3 — preservar, no expandir ahora

---

## Estado actual

Una tabla (o mínima) por módulo:

| Módulo | Tabla | Madurez |
|--------|-------|---------|
| PM | `pm_proyecto` | Embrionario |
| SVC | `svc_orden_servicio` | Embrionario |
| TKT | `tkt_ticket` | Embrionario |
| BI | `bi_reporte` | Embrionario (SQL libre = riesgo) |
| DMS | `dms_documento` | Embrionario |
| WFL | `wfl_flujo_trabajo` | Embrionario (definición JSON sin runtime) |
| AUD | `aud_log_auditoria` | Básico |

## Fortalezas

- Reservas de namespace / mapa de producto.
- AUD genérico útil.

## Debilidades

- Placeholders pueden confundirse con módulos listos.
- BI/WFL con JSON/SQL libre violan ADR-10 si se usan en serio.

## Cambios recomendados

1. **No expandir** en la ola CORE V2 industrial.
2. Marcar en documentación de producto como *stub*.
3. WFL futuro debe consumir Event Bus (instancias reales, no solo JSON de definición).
4. BI/RPT convergen en ADR-08 (capa semántica diferida).
5. AUD: mantener; particionado/retención = infra, no modelo de negocio.

## Justificación

Expandir stubs ahora diluye el foco y genera semántica incompleta. El Core industrial P0/P1 no depende de ellos.

## Prioridad

**P3**

## Impacto

Bajo inmediato; medio si se venden como features.

## Riesgos

- Scope creep.
- WFL/BI inseguros en producción.
