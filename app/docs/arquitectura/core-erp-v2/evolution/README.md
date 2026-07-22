# Fase D1 — Auditoría de evolución CORE V1 → CORE V2

**Estado:** Completada (mapa de evolución)  
**Siguiente gate:** D1.1 diseño físico de columnas — solo ítems P0 de este mapa  
**No incluye:** SQL, columnas, scripts

D0 y Etapa 0.5 permanecen **congelados**. Esta carpeta no los modifica.

---

## Principio vigente

> CORE V2 = evolución mínima y controlada del CORE V1.  
> Extender primero. Tabla nueva solo con criterios C1–C4.

---

## Documentos

| Doc | Descripción |
|-----|-------------|
| [00_PRINCIPLES_AND_SCOPE.md](./00_PRINCIPLES_AND_SCOPE.md) | Principio, criterios C1–C4, alcance |
| [01_EXECUTIVE_EVOLUTION_MAP.md](./01_EXECUTIVE_EVOLUTION_MAP.md) | Mapa ejecutivo V1→V2 |
| [02_MANDATORY_NEW_TABLES.md](./02_MANDATORY_NEW_TABLES.md) | Tablas nuevas justificadas |
| [03_CODE_IMPACT_SUMMARY.md](./03_CODE_IMPACT_SUMMARY.md) | Impacto en código V1 |

### Por módulo

| Archivo | Alcance |
|---------|---------|
| [modules/PLATFORM_ORG_CFG.md](./modules/PLATFORM_ORG_CFG.md) | IAM, CFG, ORG, CAT |
| [modules/INV.md](./modules/INV.md) | Inventarios (P0) |
| [modules/WMS_QMS_PUR_MFG.md](./modules/WMS_QMS_PUR_MFG.md) | WMS, QMS, PUR, MFG |
| [modules/MES_PLN_MRP_EVT_ALR.md](./modules/MES_PLN_MRP_EVT_ALR.md) | MES, PLN, MRP, EVT, ALR |
| [modules/COMMERCIAL_AND_REST.md](./modules/COMMERCIAL_AND_REST.md) | SLS, LOG, BILL, stubs, finanzas |

---

## Resumen numérico

| Categoría | Orientación |
|-----------|-------------|
| Tablas V1 a conservar | ~70%+ |
| Extensiones | ~15–20 tablas |
| Rediseño importante | `inv_stock` (+ contratos lote en INV) |
| Nuevas obligatorias | ~10–12 |
| Variante como tabla nueva | Condicional (preferir extensión producto) |
| Diferidas | APS, RPT, Series, CAPA, slotting, CxC/CxP |
