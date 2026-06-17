# Informe de implementación P1 — Listados ORG/INV

**Fecha:** 2026-06-15  
**Fase:** P1 (post-cierre P0 APTO)  
**Alcance:** ORG + INV únicamente. Sin cambios en estándares oficiales ni frontend.

---

## Resumen ejecutivo

P1 completado según plan aprobado. Se migró `buscar` de in-memory a SQL en 10 listados, se añadió paginación opt-in en 7 maestros adicionales, y se marcó `deprecated` en 2 listas globales de detalle INV.

**Veredicto:** APTO para auditoría consolidada P0+P1.

---

## Entregables P1

| ID | Entregable | Estado |
|----|------------|--------|
| P1-INV-06 | `buscar` SQL maestros INV (4) | ✅ |
| P1-ORG-01 | `buscar` SQL ORG (6) | ✅ |
| P1-INV-07 | Paginación opt-in maestros INV (5) | ✅ |
| P1-ORG-02 | Paginación centros-costo + parámetros | ✅ |
| P1-INV-08 | `deprecated` listas detalle global | ✅ |

---

## Detalle por bloque

### P1-INV-06 + P1-INV-07 — Maestros INV

Patrón P0 replicado: `_build_*_conditions` + `count_*` + `list_*` + servicio con early-return legacy.

| Endpoint | buscar SQL | Paginación opt-in |
|----------|------------|-------------------|
| `GET /inv/categorias` | nombre, codigo | ✅ |
| `GET /inv/unidades-medida` | nombre, codigo | ✅ |
| `GET /inv/almacenes` | nombre, codigo | ✅ |
| `GET /inv/tipos-movimiento` | nombre, codigo | ✅ |
| `GET /inv/productos` | (P0) nombre, SKU, barra | ✅ verificado buscar+page |

### P1-ORG-01 — buscar SQL ORG

Filtro in-memory eliminado de todos los services. SQL `ilike` en queries.

| Endpoint | Campos buscar |
|----------|---------------|
| `GET /org/empresa` | codigo_empresa, razon_social, nombre_comercial |
| `GET /org/cargos` | codigo, nombre |
| `GET /org/sucursales` | codigo, nombre |
| `GET /org/departamentos` | codigo, nombre |
| `GET /org/centros-costo` | codigo, nombre |
| `GET /org/parametros` | modulo_codigo, codigo_parametro, nombre_parametro (pre-merge SQL) |

### P1-ORG-02 — Paginación ORG

| Endpoint | Estrategia COUNT |
|----------|------------------|
| `GET /org/centros-costo` | SQL `count_centros_costo` |
| `GET /org/parametros` | Post-merge híbrido `len(merged)` + slice in-memory |

### P1-INV-08 — Deprecated OpenAPI

| Endpoint | Cambio |
|----------|--------|
| `GET /inv/movimientos-detalle` | `deprecated=True` en list GET |
| `GET /inv/inventario-fisico-detalle` | `deprecated=True` en list GET |

Sin cambio de lógica ni rutas.

---

## Tests

**Suite P0+P1:** 51 passed

```
test_erp_pagination_shared.py          (8)
test_inv_*pagination*.py               (15)
test_inv_stock_alertas_routing_http.py (7)
test_inv_maestros_buscar_sql.py        (4)  NEW
test_inv_maestros_pagination.py        (3)  NEW
test_inv_detalle_list_deprecated.py      (2)  NEW
test_org_buscar_sql.py                 (4)  NEW
test_org_pagination.py                   (3)  NEW
test_org_empresa_tenant_scope.py       (3)
test_org_parametro_hybrid.py           (4)
```

---

## Validación staging

Evidencia: `app/bootstrap_v2/00_manifest/evidence/P1_ORG_INV_PAGINATION_VALIDATION.json`  
Tenant: `innova` / empresa `c441e6e8-7552-46a2-8c43-6eccebbb38c4`

| Área | Resultado |
|------|-----------|
| INV maestros legacy + paginado | 200 ✅ |
| ORG buscar SQL (empresa "innova" → 1) | 200 ✅ |
| ORG centros-costo paginado + buscar | 200 ✅ |
| ORG parámetros paginado híbrido | 200 ✅ |
| Regresión P0 (movimientos, kardex, stock/alertas) | 200 ✅ |
| OpenAPI Union + deprecated detalle | ✅ |

---

## Restricciones respetadas

- ✅ Mismo patrón P0 (`page` opt-in, envelope ERP, legacy intacto)
- ✅ Sin modificar `ERP_BACKEND_STANDARDS_V4.md`
- ✅ Sin modificar `ERP_BACKEND_RULES_V4.md`
- ✅ Sin modificar prompts maestros
- ✅ Solo ORG + INV
- ✅ Sin P2 (sort, has_next/prev)
- ✅ Sin P3
- ✅ Sin frontend

---

## Riesgos residuales (no bloqueantes)

1. Parámetros híbridos: paginación post-merge (volumen <500 aceptado en plan).
2. Filtros FK cross-scope en listados (ej. `categoria_id` productos → 200 vacío).
3. ORG empresa/sucursales/cargos/departamentos sin paginación (deferido P2+).

---

## Próximo paso recomendado

Auditoría consolidada P0+P1 → decisión sobre actualización de estándares oficiales y guía de migración frontend.
