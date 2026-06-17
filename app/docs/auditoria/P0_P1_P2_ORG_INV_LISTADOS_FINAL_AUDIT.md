# Auditoría consolidada final — ORG/INV listados (P0 + P1 + P2-001)

**Fecha:** 2026-06-15  
**Estado:** APTO para decisión de congelamiento documental  
**Módulos:** ORG, INV  
**Estrategia:** PERF (backend)

---

## Veredicto global

ORG e INV quedan como **módulos de referencia backend** para consumo frontend bajo estrategia PERF. No existen requisitos backend pendientes para habilitar listados escalables en estos módulos.

| Fase | Estado | Tests |
|------|--------|-------|
| P0 — Paginación crítica INV | ✅ COMPLETADO | 28 |
| P1 — buscar SQL + paginación maestros | ✅ COMPLETADO | 23 |
| P2-001 — sort_by/sort_dir | ✅ COMPLETADO | 17 |
| **Total suite** | **✅ 53 passed** | |

---

## Respuestas explícitas PERF

### ¿PERF-01 completado?

**SÍ — COMPLETADO (backend ORG/INV)**

- Contrato opt-in: `page` activa envelope `{ items, total, pagina_actual, total_paginas, limit }`
- Sin `page` → legacy `list[]`
- 13 endpoints paginados + 3 legacy full-list con sort
- Evidencia: P0+P1 staging + tests

### ¿PERF-02 habilitado?

**SÍ — HABILITADO (backend)**

- Parámetro `buscar` con filtro SQL (`ILIKE`) en 10 maestros ORG/INV
- Debounce = responsabilidad frontend
- Backend listo para recibir búsquedas post-debounce

### ¿PERF-03 habilitado?

**SÍ — HABILITADO (backend)**

- Filtros por query params por recurso (ej. `estado`, `tipo_producto`, `modulo_codigo`, `fecha_desde/hasta`)
- Toolbar filtros = frontend; backend expone contrato

### ¿PERF-04 completado?

**SÍ — COMPLETADO (backend ORG/INV)**

- `sort_by` + `sort_dir` en 16 endpoints operativos
- Whitelist por recurso; inválido → 422
- `sort_dir` sin `sort_by` → ignorado
- Sin `sort_by` → orden legacy preservado
- Evidencia: `P2_ORG_INV_SORT_VALIDATION.json`

### ¿PERF-05 completado?

**NO — FRONTEND (fuera de alcance backend)**

- Componentes listas, toolbar UI, debounce client-side
- Backend no bloquea; contrato listo

### ¿PERF-06 completado?

**SÍ — COMPLETADO (backend ORG/INV)**

Estrategia escalabilidad backend cerrada:

| Capacidad | Estado |
|-----------|--------|
| Paginación server-side | ✅ |
| Búsqueda SQL | ✅ |
| Filtros query params | ✅ |
| Sort server-side | ✅ P2-001 |

Frontend puede consumir listados grandes sin ordenar/filtrar en memoria sobre dataset completo.

### ¿Existe algún requisito backend pendiente para frontend?

**NO — para listados ORG/INV bajo PERF**

Requisitos backend entregados:

```
page, limit, buscar, sort_by, sort_dir + filtros por recurso
```

**Pendientes conscientemente fuera de alcance (no bloquean PERF):**

| Item | Motivo |
|------|--------|
| `has_next` / `has_prev` | P3+ — no autorizado |
| Paginación maestros ORG pequeños (empresa, sucursales, etc.) | Volumen bajo; sort ya disponible |
| PERF-05 componentes UI | Frontend |
| Unificación `order` PUR vs `sort_dir` ORG/INV | Otro módulo / estándares futuros |

---

## Matriz consolidada — 18 list endpoints

| Endpoint | buscar SQL | Paginación | Sort P2 | Notas |
|----------|------------|------------|---------|-------|
| `/org/empresa` | ✅ | — | ✅ | Tenant scope |
| `/org/sucursales` | ✅ | — | ✅ | |
| `/org/departamentos` | ✅ | — | ✅ | |
| `/org/cargos` | ✅ | — | ✅ | |
| `/org/centros-costo` | ✅ | ✅ | ✅ | |
| `/org/parametros` | ✅ | ✅ híbrido | ✅ post-merge | |
| `/inv/categorias` | ✅ | ✅ | ✅ | |
| `/inv/unidades-medida` | ✅ | ✅ | ✅ | |
| `/inv/almacenes` | ✅ | ✅ | ✅ | |
| `/inv/tipos-movimiento` | ✅ | ✅ | ✅ | |
| `/inv/productos` | ✅ | ✅ | ✅ | |
| `/inv/movimientos` | — | ✅ | ✅ | P0 |
| `/inv/kardex` | — | ✅ | ✅ | `producto_id` obligatorio |
| `/inv/inventario-fisico` | — | ✅ | ✅ | P0 |
| `/inv/stock` | — | ✅ | ✅ | P0 |
| `/inv/stock/alertas` | — | ✅ | ✅ | BLK-001 cerrado |
| `/inv/movimientos-detalle` | — | — | — | deprecated |
| `/inv/inventario-fisico-detalle` | — | — | — | deprecated |

---

## Compatibilidad verificada

| Escenario | Resultado staging |
|-----------|-------------------|
| Legacy sin sort | 200, orden preservado |
| `sort_by` válido | 200 |
| `sort_by` inválido | 422 |
| `sort_dir` sin `sort_by` | 200 (ignorado) |
| `page` + `sort_by` | 200 envelope |
| P0 regresión movimientos/kardex/stock | 200 |

---

## Evidencia

| Artefacto | Ruta |
|-----------|------|
| P0 BLK-001 | `evidence/P0_BLK001_CLOSURE_VALIDATION.json` |
| P1 paginación | `evidence/P1_ORG_INV_PAGINATION_VALIDATION.json` |
| P2 sort | `evidence/P2_ORG_INV_SORT_VALIDATION.json` |
| Plan P2 | `auditoria/P2_001_SORT_AUDIT_PLAN.md` |
| Informe P2 | `auditoria/P2_001_SORT_IMPLEMENTATION_REPORT.md` |
| Auditoría P0+P1 | `auditoria/P0_P1_ORG_INV_LISTADOS_CONSOLIDATED_AUDIT.md` |

---

## Recomendación para congelamiento documental

Tras esta auditoría, **se recomienda autorizar** actualización de:

1. `.cursorrules` — contrato listados v1 (`page`, `limit`, `buscar`, `sort_by`, `sort_dir`)
2. `docs/prompts/PROMPT_BACKEND_MAESTRO.md`
3. `app/docs/arquitectura/ERP_BACKEND_STANDARDS_V4.md`
4. `app/docs/arquitectura/ERP_BACKEND_RULES_V4.md`
5. `app/docs/arquitectura/ERP_BACKEND_MASTER_PROMPT_V4.md`

**Condición:** decisión explícita del equipo post-revisión de este informe.

---

## Contrato listados v1 (propuesta para estándares)

```
GET /{modulo}/{recurso}
  ?page=1          # opt-in paginación
  &limit=50        # solo con page (default 50, max 100)
  &buscar=texto    # SQL ILIKE donde aplique
  &sort_by=col     # whitelist por recurso
  &sort_dir=asc|desc  # solo con sort_by
  &{filtros_recurso}

Sin page  → list[]
Con page  → { items, total, pagina_actual, total_paginas, limit }
sort_by inválido → 422 INVALID_SORT_COLUMN
sort_dir sin sort_by → ignorado
```
