# Auditoría post-implementación consolidada P0 + P1 — Listados ORG/INV

**Fecha:** 2026-06-15  
**Veredicto consolidado:** **APTO** para decisión sobre actualización de estándares y preparación frontend.

---

## Matriz consolidada — 18 list endpoints

| # | Endpoint | Fase | buscar | Paginación opt-in | Union OpenAPI | Notas |
|---|----------|------|--------|-------------------|---------------|-------|
| 1 | `GET /org/empresa` | P1 | SQL ✅ | — (maestro pequeño) | list only | Tenant scope |
| 2 | `GET /org/sucursales` | P1 | SQL ✅ | — | list only | |
| 3 | `GET /org/departamentos` | P1 | SQL ✅ | — | list only | |
| 4 | `GET /org/cargos` | P1 | SQL ✅ | — | list only | |
| 5 | `GET /org/centros-costo` | P1 | SQL ✅ | ✅ | anyOf ✅ | |
| 6 | `GET /org/parametros` | P1 | SQL ✅ | ✅ híbrido | anyOf ✅ | COUNT post-merge |
| 7 | `GET /inv/categorias` | P1 | SQL ✅ | ✅ | anyOf ✅ | |
| 8 | `GET /inv/unidades-medida` | P1 | SQL ✅ | ✅ | anyOf ✅ | |
| 9 | `GET /inv/almacenes` | P1 | SQL ✅ | ✅ | anyOf ✅ | |
| 10 | `GET /inv/tipos-movimiento` | P1 | SQL ✅ | ✅ | anyOf ✅ | |
| 11 | `GET /inv/productos` | P0+P1 | SQL ✅ | ✅ | anyOf ✅ | buscar+page combinados |
| 12 | `GET /inv/movimientos` | P0 | — | ✅ | anyOf ✅ | |
| 13 | `GET /inv/kardex` | P0 | — | ✅ | anyOf ✅ | producto_id obligatorio |
| 14 | `GET /inv/inventario-fisico` | P0 | — | ✅ | anyOf ✅ | |
| 15 | `GET /inv/stock` | P0 | — | ✅ | anyOf ✅ | |
| 16 | `GET /inv/stock/alertas` | P0 | — | ✅ | anyOf ✅ | BLK-001 cerrado |
| 17 | `GET /inv/movimientos-detalle` | P1 | — | — | list | **deprecated** list GET |
| 18 | `GET /inv/inventario-fisico-detalle` | P1 | — | — | list | **deprecated** list GET |

---

## Conformidad con decisiones arquitectónicas

| Decisión | P0 | P1 | Estado |
|----------|----|----|--------|
| Opt-in por `page` | ✅ | ✅ | Conforme |
| `limit` default 50, max 100 | ✅ | ✅ | Conforme |
| Envelope `{items,total,pagina_actual,total_paginas,limit}` | ✅ | ✅ | Conforme |
| Legacy sin `page` intacto | ✅ | ✅ | Staging verificado |
| `limit` sin `page` ignorado | ✅ | ✅ | Conforme |
| Kardex `producto_id` obligatorio | ✅ | — | Breaking controlado |
| Sin has_next/has_prev (P2) | ✅ | ✅ | No implementado |
| Sin sort_by (P2) | ✅ | ✅ | No implementado |

---

## Hallazgos post-implementación

### Cerrados en P0
- BLK-001 routing `/inv/stock/alertas` — resuelto

### Aceptados / diferidos
- Parámetros ORG: paginación híbrida post-merge (deuda documentada, volumen bajo)
- ORG maestros pequeños sin paginación (empresa, cargos, etc.) — deferido
- Filtros FK cross-scope → 200 vacío en algunos listados (preexistente)

### Sin regresiones detectadas
- Suite 51/51 PASS
- Staging P0 endpoints post-P1: 200
- OpenAPI Union en todos los listados paginados

---

## Evidencias

| Artefacto | Ruta |
|-----------|------|
| P0 funcional | `evidence/P0_BLK001_CLOSURE_VALIDATION.json` |
| P1 funcional | `evidence/P1_ORG_INV_PAGINATION_VALIDATION.json` |
| Informe P1 | `app/docs/auditoria/P1_ORG_INV_LISTADOS_IMPLEMENTATION_REPORT.md` |

---

## Recomendación

**Proceder** con:
1. Actualización de `ERP_BACKEND_STANDARDS_V4` / `RULES` (contrato listados v1 consolidado)
2. Elaboración de guía de migración frontend (`page` opt-in, envelope, kardex breaking)
3. Planificación P2 (sort, has_next/prev, paginación ORG maestros restantes) — fuera de alcance actual
