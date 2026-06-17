# Informe de implementación P2-001 — `sort_by` / `sort_dir` ORG/INV

**Fecha:** 2026-06-15  
**Estado:** COMPLETADO  
**Alcance:** 16 endpoints listados operativos ORG/INV

---

## Resumen ejecutivo

P2-001 implementa ordenamiento server-side escalable reutilizando infraestructura P0/P1. Sin breaking changes. Contrato additive: `sort_by` + `sort_dir`.

| Entregable | Estado |
|------------|--------|
| Infra `app/shared/pagination/sort.py` | ✅ |
| Helpers `apply_erp_sort` / `apply_memory_sort` | ✅ |
| 10 endpoints INV | ✅ |
| 6 endpoints ORG (incl. parámetros híbrido) | ✅ |
| Tests P2 (17 nuevos) | ✅ |
| Suite P0+P1+P2 (53 passed) | ✅ |
| Staging tenant `innova` | ✅ |

---

## Infraestructura

```
app/shared/pagination/
  sort.py           # ErpSortParams, erp_sort_params()
  query_helpers.py  # apply_erp_sort(), apply_memory_sort()
  __init__.py       # exports ErpSortParams, erp_sort_params
```

### Reglas implementadas

| Regla | Implementación |
|-------|----------------|
| Sin `sort_by` | `default_order` idéntico al ORDER BY pre-P2 |
| `sort_by` inválido | `CustomException` 422 (`INVALID_SORT_COLUMN`) |
| `sort_dir` sin `sort_by` | Ignorado en `erp_sort_params()` |
| Tie-breaker | PK del recurso como segundo criterio (SQL) |
| Parámetros híbridos | `apply_memory_sort` post-merge, pre-slice |

**Nota:** Se usa `CustomException(422)` en lugar de `ValidationError` (400 del proyecto) para cumplir contrato P2.

---

## Endpoints modificados (16)

### INV (10)
- `/api/v1/inv/categorias`
- `/api/v1/inv/unidades-medida`
- `/api/v1/inv/almacenes`
- `/api/v1/inv/tipos-movimiento`
- `/api/v1/inv/productos`
- `/api/v1/inv/movimientos`
- `/api/v1/inv/kardex`
- `/api/v1/inv/inventario-fisico`
- `/api/v1/inv/stock`
- `/api/v1/inv/stock/alertas`

### ORG (6)
- `/api/v1/org/empresa`
- `/api/v1/org/sucursales`
- `/api/v1/org/departamentos`
- `/api/v1/org/cargos`
- `/api/v1/org/centros-costo`
- `/api/v1/org/parametros` (sort post-merge)

### Excluidos (sin cambio)
- `/api/v1/inv/movimientos-detalle` (deprecated)
- `/api/v1/inv/inventario-fisico-detalle` (deprecated)

---

## Tests

| Archivo | Tests |
|---------|-------|
| `test_erp_sort_shared.py` | 8 |
| `test_inv_sort_pagination.py` | 5 |
| `test_org_sort.py` | 6 |
| Suite P0+P1+P2 | **53 passed** |

---

## Evidencia staging

- Script: `scripts/validate_p2_sort_staging.py`
- JSON: `app/bootstrap_v2/00_manifest/evidence/P2_ORG_INV_SORT_VALIDATION.json`
- Tenant: `innova`
- Casos: legacy sin sort, sort válido, sort inválido 422, sort_dir ignorado, paginado+sort, ORG+INV

---

## Fuera de alcance (confirmado)

- `has_next` / `has_prev`
- `page=1` implícito
- Eliminación modo legacy
- Cambios P3
- Documentos oficiales / prompts / `.cursorrules`
