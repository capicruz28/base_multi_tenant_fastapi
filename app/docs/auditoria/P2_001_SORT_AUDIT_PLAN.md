# Auditoría y plan de ejecución P2-001 — `sort_by` / `sort_dir` ORG/INV

**Fecha:** 2026-06-15  
**Estado:** Auditoría pre-implementación — **NO autorizado implementar aún**  
**Objetivo:** Cerrar PERF-04 (backend) y completar PERF-06 (backend) antes de congelar estándares oficiales.

---

## Veredicto de factibilidad

| Criterio | Resultado |
|----------|-----------|
| ¿Factible reutilizando infra P0/P1? | **Sí** |
| ¿Bloqueos técnicos? | **Ninguno** |
| ¿Caso especial? | **Parámetros híbridos** (sort post-merge) |
| Esfuerzo vs P0/P1 | **~35–45% de P1** (~20–25% de P0+P1 combinados) |
| Tras P2-001, PERF-04 backend | **COMPLETADO** |
| Tras P2-001, PERF-06 backend ORG/INV | **COMPLETADO** (PERF-05 sigue en frontend) |

---

## 1. Diseño detallado de implementación

### 1.1 Principios (alineados a P0/P1)

| Regla | Valor |
|-------|-------|
| Parámetros API | `sort_by` (opcional), `sort_dir` (opcional: `asc` \| `desc`) |
| Sin `sort_by` | Conservar ORDER BY fijo actual (backward compat) |
| Con `sort_by` inválido | **422** `ValidationError` (recomendado ERP; PUR ignora silenciosamente — no replicar) |
| Con `sort_by` sin `sort_dir` | Default `asc`, salvo default de recurso documentado (ej. movimientos → `desc` en `fecha_movimiento`) |
| `sort_dir` sin `sort_by` | **Ignorar** (simétrico a `limit` sin `page`) |
| Whitelist | Solo columnas SQL reales del `*Table.c` — nunca input libre |
| Tie-breaker | Siempre añadir PK del recurso como segundo criterio (orden estable entre páginas) |
| Paginación | `ORDER BY` **antes** de `OFFSET/FETCH` |
| Legacy (sin `page`) | Sort aplica igual en SQL (lista completa ordenada) |

**Nota nomenclatura:** PUR legacy usa `order`; ORG/INV P2-001 usará `sort_dir` según plan de escalabilidad aprobado. No unificar PUR en este alcance.

### 1.2 Infraestructura compartida (nueva capa en `app/shared/pagination/`)

```
app/shared/pagination/
  sort.py              # NEW — ErpSortParams, erp_sort_params(), apply_erp_sort()
  params.py            # EXT — ErpListParams o composición sort + pagination
  query_helpers.py     # EXT — apply_erp_sort(query, table.c, whitelist, sort_by, sort_dir, default)
```

**`ErpSortParams`** (dataclass):
```python
@dataclass(frozen=True)
class ErpSortParams:
    sort_by: Optional[str]
    sort_dir: str  # "asc" | "desc", effective after normalization
```

**`erp_sort_params()`** (FastAPI dependency):
```python
sort_by: Optional[str] = Query(None, description="Columna whitelist para ordenar")
sort_dir: Optional[Literal["asc", "desc"]] = Query(None)
```

**`apply_erp_sort()`** (SQLAlchemy Core):
- Entrada: `query`, `column_map: dict[str, Column]`, `sort_by`, `sort_dir`, `default_column`, `default_dir`, `tie_breaker_column`
- Si `sort_by` presente y no en whitelist → raise `ValidationError` 422
- `getattr(Table.c, sort_by)` solo desde mapa predefinido (no `getattr` dinámico sobre input)
- Retorna `query.order_by(primary, tie_breaker)`

**Composición en endpoints:**
```python
async def listar_x(
    ...,
    pagination: ErpPaginationParams = Depends(erp_pagination_params),
    sort: ErpSortParams = Depends(erp_sort_params),
):
```

Alternativa: unificar en `erp_list_params()` que devuelve paginación + sort — reduce boilerplate en 16 endpoints.

### 1.3 Patrón por capa (replicable ×16)

```
[1] queries/{cod}_queries.py
    _SORT_COLUMNS_{RECURSO}: frozenset[str]
    _SORT_COLUMN_MAP: dict[str, Column]  # sort_by → Table.c.col
    _DEFAULT_SORT = ("nombre", "asc")  # o el actual fijo
    list_*(): añadir sort_by, sort_dir; reemplazar .order_by() fijo por apply_erp_sort()
    count_*(): sin sort (COUNT no requiere ORDER BY)

[2] services/{cod}_service.py
    list_*_servicio(): propagar sort_by/sort_dir a queries
    Parametros: sort post-merge en memoria (ver §1.4)

[3] endpoints_{cod}.py
    Query params sort_by/sort_dir vía Depends(erp_sort_params)
    OpenAPI: documentar whitelist en description

[4] tests
    sort válido → query recibe sort
    sort inválido → 422
    default preservado sin sort_by
    paginado + sort → envelope coherente
```

### 1.4 Caso especial: `GET /org/parametros` (híbrido)

Flujo actual P1: SQL candidatos → `apply_parametro_precedence()` → slice paginado.

**P2-001 propuesto:**
1. SQL `buscar` en candidatos (ya P1)
2. Merge/precedencia (sin cambio)
3. **Sort post-merge** en Python sobre `List[ParametroRead]`:
   - Whitelist: `modulo_codigo`, `codigo_parametro`, `nombre_parametro`, `fecha_creacion`, `fecha_actualizacion`
   - `sort_dir` aplicado con `sorted(key=..., reverse=...)`
4. Paginación post-sort (igual que P1)

**Justificación:** precedencia híbrida impide ORDER BY SQL único correcto sin duplicar lógica de override. Volumen <500 (plan P1 aceptado).

### 1.5 Orden de implementación sugerido

```
P2-INFRA     sort.py + query_helpers + tests shared
P2-INV-01    maestros (categorias, unidades, almacenes, tipos) — patrón simple
P2-INV-02    productos, stock, stock/alertas
P2-INV-03    movimientos, kardex, inventario-fisico — transaccionales
P2-ORG-01    empresa, cargos, sucursales, departamentos — buscar ya SQL
P2-ORG-02    centros-costo — paginado + sort SQL
P2-ORG-03    parametros — híbrido post-merge
P2-CIERRE    pytest P0+P1+P2 + staging + informe
```

---

## 2. Inventario exacto de endpoints afectados

### Incluidos (16) — listados operativos ORG/INV

| # | Método | Ruta | Módulo | Paginación P0/P1 | Sort P2 |
|---|--------|------|--------|------------------|---------|
| 1 | GET | `/api/v1/org/empresa` | ORG | — | SQL |
| 2 | GET | `/api/v1/org/sucursales` | ORG | — | SQL |
| 3 | GET | `/api/v1/org/departamentos` | ORG | — | SQL |
| 4 | GET | `/api/v1/org/cargos` | ORG | — | SQL |
| 5 | GET | `/api/v1/org/centros-costo` | ORG | ✅ P1 | SQL |
| 6 | GET | `/api/v1/org/parametros` | ORG | ✅ P1 híbrido | **Post-merge** |
| 7 | GET | `/api/v1/inv/categorias` | INV | ✅ P1 | SQL |
| 8 | GET | `/api/v1/inv/unidades-medida` | INV | ✅ P1 | SQL |
| 9 | GET | `/api/v1/inv/almacenes` | INV | ✅ P1 | SQL |
| 10 | GET | `/api/v1/inv/tipos-movimiento` | INV | ✅ P1 | SQL |
| 11 | GET | `/api/v1/inv/productos` | INV | ✅ P0 | SQL |
| 12 | GET | `/api/v1/inv/movimientos` | INV | ✅ P0 | SQL |
| 13 | GET | `/api/v1/inv/kardex` | INV | ✅ P0 | SQL |
| 14 | GET | `/api/v1/inv/inventario-fisico` | INV | ✅ P0 | SQL |
| 15 | GET | `/api/v1/inv/stock` | INV | ✅ P0 | SQL |
| 16 | GET | `/api/v1/inv/stock/alertas` | INV | ✅ P0 | SQL |

### Excluidos (2) — deprecated, sin consumo FE

| Ruta | Motivo |
|------|--------|
| `GET /api/v1/inv/movimientos-detalle` | deprecated P1-INV-08 |
| `GET /api/v1/inv/inventario-fisico-detalle` | deprecated P1-INV-08 |

---

## 3. Whitelist de columnas ordenables por recurso

Criterio: columnas expuestas en `*Read` + útiles en UI de tabla + existentes en tabla SQL. Máximo ~6 por recurso (toolbar).

### ORG

| Recurso | `sort_by` permitidos | Default (sin sort_by) | Tie-breaker |
|---------|----------------------|------------------------|-------------|
| **empresa** | `codigo_empresa`, `razon_social`, `nombre_comercial`, `ruc`, `fecha_creacion` | `razon_social` asc | `empresa_id` |
| **sucursales** | `codigo`, `nombre`, `tipo_sucursal`, `fecha_creacion` | `codigo` asc | `sucursal_id` |
| **departamentos** | `codigo`, `nombre`, `nivel`, `fecha_creacion` | `codigo` asc | `departamento_id` |
| **cargos** | `codigo`, `nombre`, `nivel_jerarquico`, `fecha_creacion` | `codigo` asc | `cargo_id` |
| **centros-costo** | `codigo`, `nombre`, `tipo_centro_costo`, `nivel`, `fecha_creacion` | `codigo` asc | `centro_costo_id` |
| **parametros** | `modulo_codigo`, `codigo_parametro`, `nombre_parametro`, `fecha_creacion`, `fecha_actualizacion` | `modulo_codigo`, `codigo_parametro` asc | `parametro_id` |

### INV

| Recurso | `sort_by` permitidos | Default (sin sort_by) | Tie-breaker |
|---------|----------------------|------------------------|-------------|
| **categorias** | `codigo`, `nombre`, `nivel`, `fecha_creacion` | `nombre` asc | `categoria_id` |
| **unidades-medida** | `codigo`, `nombre`, `tipo_unidad`, `fecha_creacion` | `nombre` asc | `unidad_medida_id` |
| **almacenes** | `codigo`, `nombre`, `tipo_almacen`, `fecha_creacion` | `nombre` asc | `almacen_id` |
| **tipos-movimiento** | `codigo`, `nombre`, `clase_movimiento`, `fecha_creacion` | `nombre` asc | `tipo_movimiento_id` |
| **productos** | `codigo_sku`, `nombre`, `tipo_producto`, `fecha_creacion`, `fecha_actualizacion` | `nombre` asc | `producto_id` |
| **movimientos** | `numero_movimiento`, `fecha_movimiento`, `fecha_contable`, `estado`, `fecha_creacion` | `fecha_movimiento` **desc** | `movimiento_id` |
| **kardex** | `fecha_movimiento`, `cantidad_base`, `costo_unitario` | `fecha_movimiento` **desc** | `movimiento_detalle_id` |
| **inventario-fisico** | `numero_inventario`, `fecha_inventario`, `estado`, `fecha_creacion` | `fecha_inventario` **desc** | `inventario_fisico_id` |
| **stock** | `cantidad_actual`, `cantidad_disponible`, `stock_minimo`, `fecha_actualizacion` | `producto_id` asc, `almacen_id` asc | `stock_id` |
| **stock/alertas** | *(misma whitelist que stock)* | igual stock | `stock_id` |

**Excluidos de whitelist intencionalmente:** UUIDs de FK (`producto_id`, `almacen_id`) como sort primario en stock salvo necesidad FE explícita — ordenar por UUID no aporta UX; se mantienen como tie-breaker.

---

## 4. Riesgos de compatibilidad

| ID | Riesgo | Severidad | Mitigación |
|----|--------|-----------|------------|
| R1 | Cliente legacy dependía de orden implícito fijo | Baja | Sin `sort_by` → mismo default actual |
| R2 | `sort_by` inválido — PUR ignora, ERP propone 422 | Media | Documentar en guía migración; tests 422 |
| R3 | Orden inestable entre páginas sin tie-breaker | Alta | PK obligatorio como segundo criterio |
| R4 | `sort_dir` sin `sort_by` — comportamiento | Baja | Ignorar (regla simétrica a `limit` sin `page`) |
| R5 | Parametros: sort post-merge ≠ sort SQL | Media | Documentar en OpenAPI; volumen acotado |
| R6 | Divergencia PUR (`order`) vs ORG/INV (`sort_dir`) | Baja | Fuera de alcance; nota en estándares futuros |
| R7 | Performance: ORDER BY + COUNT en tablas grandes | Media | Índices existentes; monitoreo staging (mismo riesgo P0) |
| R8 | OpenAPI: más query params en Union existente | Baja | Añadir a description; sin cambio de response shape |

**Sin breaking changes** si no se envía `sort_by`. Contrato additive.

---

## 5. Esfuerzo estimado vs P0/P1

| Fase | Endpoints | Tests | Archivos ~ | Esfuerza relativa |
|------|-----------|-------|------------|-------------------|
| **P0** | 6 críticos INV + infra | 28 | ~25 | 100% (base) |
| **P1** | 10 adicionales + buscar ORG | 23 | ~40 | ~80–90% de P0 |
| **P2-001** | 16 sort (reuso queries/services) | ~18–22 | ~35–38 | **~35–45% de P1** |

**Desglose P2-001:**

| Tarea | Estimación |
|-------|------------|
| Infra `sort.py` + helpers + 6 tests shared | 0.5 día |
| 10 queries INV + services + endpoints | 1 día |
| 6 queries ORG + services + endpoints | 0.75 día |
| Parametros híbrido sort | 0.25 día |
| Tests unitarios P2 (~16) | 0.5 día |
| Staging + informe cierre | 0.25 día |
| **Total** | **~3–3.5 días dev** |

Menor que P1 porque: no nuevo envelope, no `buscar` nuevo, no COUNT nuevo, patrón mecánico por recurso. Mayor riesgo concentrado en parametros y validación whitelist.

---

## 6. Confirmación PERF-04 / PERF-06 post P2-001

### Mapa PERF backend ORG/INV tras P2-001

| ID | Objetivo | Post P2-001 |
|----|----------|-------------|
| **PERF-01** Paginación server-side | ✅ Completado (P0+P1) |
| **PERF-02** Debounce búsquedas | ✅ Backend habilitado (`buscar` SQL P1); debounce = FE |
| **PERF-03** Toolbar filtros | ✅ Backend habilitado (query params); toolbar = FE |
| **PERF-04** Sorting escalable | ✅ **Completado** con `sort_by`/`sort_dir` server-side |
| **PERF-05** Componentes listas | ⏳ Frontend (fuera de alcance backend) |
| **PERF-06** Estrategia escalabilidad | ✅ **Completado en backend ORG/INV** |

### Conclusión explícita

Tras implementar y validar P2-001:

- **PERF-04:** `COMPLETADO` (backend ORG/INV)
- **PERF-06:** `COMPLETADO` (backend ORG/INV) — la estrategia backend paginación + búsqueda SQL + sort server-side queda cerrada
- **PERF-05** permanece pendiente en frontend
- **`has_next`/`has_prev`** y paginación ORG maestros pequeños siguen fuera de P2-001 (no bloquean PERF-04/06)

**Recomendación:** Autorizar implementación P2-001 → validación staging → **entonces** congelar `ERP_BACKEND_STANDARDS_V4` / `RULES` con contrato listados v1 completo (page, limit, buscar, sort_by, sort_dir).

---

## Archivos estimados a modificar (inventario P2-001)

### Nuevos (~6)
- `app/shared/pagination/sort.py`
- `tests/unit/test_erp_sort_shared.py`
- `tests/unit/test_inv_sort_pagination.py`
- `tests/unit/test_org_sort.py`
- `app/docs/auditoria/P2_001_SORT_IMPLEMENTATION_REPORT.md` (post-ejecución)

### Modificados (~32)
- `app/shared/pagination/__init__.py`, `query_helpers.py` (opcional `params.py`)
- 10× `app/infrastructure/database/queries/inv/*_queries.py`
- 6× `app/infrastructure/database/queries/org/*_queries.py`
- 10× `app/modules/inv/application/services/*_service.py`
- 6× `app/modules/org/application/services/*_service.py`
- 10× `app/modules/inv/presentation/endpoints_*.py`
- 6× `app/modules/org/presentation/endpoints_*.py`

**Sin tocar:** estándares oficiales, prompts, frontend, módulos fuera ORG/INV.
