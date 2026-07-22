# CORE ERP V2 — Documentación arquitectónica oficial

## A. Auditoría (cerrada y aprobada)

| Doc | Descripción |
|-----|-------------|
| [00_EXECUTIVE_SUMMARY.md](./00_EXECUTIVE_SUMMARY.md) | Veredicto y priorización |
| [01_METHODOLOGY_AND_SOURCES.md](./01_METHODOLOGY_AND_SOURCES.md) | Método y fuentes |
| [02_CORE_VS_VERTICAL_CLASSIFICATION.md](./02_CORE_VS_VERTICAL_CLASSIFICATION.md) | Regla Core vs Vertical |
| [03_PRELIMINARY_ADR_DECISIONS.md](./03_PRELIMINARY_ADR_DECISIONS.md) | ADRs 01–10 |
| [04_V010_BASELINE.md](./04_V010_BASELINE.md) | Estado actual V010 |
| [05_PROPOSAL_A_VS_B.md](./05_PROPOSAL_A_VS_B.md) | Comparación y fusión A/B |
| [90_CORE_V2_DEFINITION.md](./90_CORE_V2_DEFINITION.md) | Definición oficial CORE V2 |
| [91_DESIGN_ROADMAP.md](./91_DESIGN_ROADMAP.md) | Roadmap de diseño (sin SQL) |

### Auditorías por módulo

| Archivo | Alcance |
|---------|---------|
| [modules/INV.md](./modules/INV.md) | Inventarios, lote, variantes |
| [modules/WMS.md](./modules/WMS.md) | Almacén, oleadas, FEFO |
| [modules/QMS.md](./modules/QMS.md) | Calidad |
| [modules/MFG_MES_PLN.md](./modules/MFG_MES_PLN.md) | Manufactura / ejecución / capacidad |
| [modules/CFG_EVT_ALR_RPT_APS.md](./modules/CFG_EVT_ALR_RPT_APS.md) | Verticales, bus, alertas, RPT, APS |
| [modules/COMMERCIAL_ORG.md](./modules/COMMERCIAL_ORG.md) | ORG, PUR, SLS, LOG, facturación, POS |
| [modules/PLANNING_FINANCE_HCM.md](./modules/PLANNING_FINANCE_HCM.md) | MRP/MPS, FIN, HCM, MNT |
| [modules/PLACEHOLDERS.md](./modules/PLACEHOLDERS.md) | PM, SVC, TKT, BI, DMS, WFL, AUD |

## B. Modelo conceptual — Etapa 0.5 (cerrada / congelada)

Índice: [conceptual/README.md](./conceptual/README.md)

| Doc | Descripción |
|-----|-------------|
| [conceptual/01_CORE_DOMAIN_MODEL.md](./conceptual/01_CORE_DOMAIN_MODEL.md) | Dominios del Core |
| [conceptual/02_BOUNDED_CONTEXTS.md](./conceptual/02_BOUNDED_CONTEXTS.md) | Bounded Contexts |
| [conceptual/03_AGGREGATE_ROOTS.md](./conceptual/03_AGGREGATE_ROOTS.md) | Aggregate Roots |
| [conceptual/04_DOMAIN_EVENTS.md](./conceptual/04_DOMAIN_EVENTS.md) | Eventos de dominio |
| [conceptual/05_UBIQUITOUS_LANGUAGE.md](./conceptual/05_UBIQUITOUS_LANGUAGE.md) | Lenguaje ubicuo |
| [conceptual/06_EXTENSION_POINTS.md](./conceptual/06_EXTENSION_POINTS.md) | Extensión por Verticales |

## C. Evolución V1→V2 — Fase D1 (mapa de evolución)

Índice: [evolution/README.md](./evolution/README.md)

| Doc | Descripción |
|-----|-------------|
| [evolution/00_PRINCIPLES_AND_SCOPE.md](./evolution/00_PRINCIPLES_AND_SCOPE.md) | Extender primero; criterios C1–C4 |
| [evolution/01_EXECUTIVE_EVOLUTION_MAP.md](./evolution/01_EXECUTIVE_EVOLUTION_MAP.md) | Mapa ejecutivo |
| [evolution/02_MANDATORY_NEW_TABLES.md](./evolution/02_MANDATORY_NEW_TABLES.md) | Tablas nuevas justificadas |
| [evolution/03_CODE_IMPACT_SUMMARY.md](./evolution/03_CODE_IMPACT_SUMMARY.md) | Impacto en código V1 |

**Principio vigente:** CORE V2 = evolución mínima del CORE V1.

**Restricción vigente:** no diseñar columnas ni generar SQL hasta aprobar el mapa de evolución y abrir D1.1.
