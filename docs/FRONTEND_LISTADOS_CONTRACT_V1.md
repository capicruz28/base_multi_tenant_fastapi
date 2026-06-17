# Contrato de consumo Frontend — Listados escalables v1 (ORG + INV)

**Documento:** Puente oficial Backend → Frontend  
**Versión:** v1 · 2026-06-15  
**Módulos:** ORG, INV  
**Prefijos API:** `/api/v1/org`, `/api/v1/inv`  
**Fuente de verdad:** Implementación congelada P0 + P1 + P2-001 · OpenAPI (`/api/v1/openapi.json`)

Este documento es **autocontenido** para implementar listas PERF en Frontend. No requiere consultar código backend ni auditorías internas.

**Documentación canónica relacionada:**

- `app/docs/arquitectura/ERP_BACKEND_STANDARDS_V4.md` §10
- `app/docs/auditoria/P0_P1_P2_ORG_INV_LISTADOS_FINAL_AUDIT.md`
- `docs/INV_FRONTEND_CONSUMPTION_RC1.md` (workflow INV, no listados)

---

## 1. Contrato común de listados

Todos los listados operativos ORG/INV comparten estos query params (donde el endpoint los expone):

| Parámetro | Tipo | Default | Regla |
|-----------|------|---------|-------|
| `page` | int ≥ 1 | — (ausente) | **Opt-in.** Si se envía → respuesta envelope paginado. Si no → `list[]` legacy |
| `limit` | int 1–100 | 50 | **Solo aplica con `page`.** Sin `page` se ignora por completo |
| `buscar` | string | — | Filtro SQL `ILIKE` en columnas del recurso (ver tabla §4). No filtrar in-memory |
| `sort_by` | string | — | Columna de whitelist del recurso. Sin valor → orden legacy del backend |
| `sort_dir` | `asc` \| `desc` | — | Solo aplica con `sort_by`. Sin `sort_by` → **ignorado** |

### Parámetros transversales frecuentes

| Parámetro | Default | Uso |
|-----------|---------|-----|
| `solo_activos` | `true` | Maestros ORG/INV con soft delete |

### Reglas de composición

```
GET /{modulo}/{recurso}?{filtros_recurso}&buscar=...&sort_by=...&sort_dir=...&page=1&limit=50
```

| Combinación | Comportamiento |
|-------------|----------------|
| Sin `page` | Respuesta `list[EntityRead]` — dataset completo filtrado |
| Con `page` | Respuesta `Paginated{Entity}Response` — COUNT + OFFSET server-side |
| `limit` sin `page` | Ignorado (compatibilidad) |
| `sort_dir` sin `sort_by` | Ignorado |
| `sort_by` inválido | **422** con `error_code: "INVALID_SORT_COLUMN"` |
| Filtros + `buscar` + `sort` + `page` | Se combinan (AND lógico en SQL) |

### Autenticación y sesión

| Módulo | Requisito |
|--------|-----------|
| **ORG** | JWT + sesión ERP. `empresa` usa sesión tenant; resto usa sesión con empresa activa |
| **INV** | JWT + `require_erp_session` + `empresa_id` en sesión |

`cliente_id` **nunca** se envía para autorización — solo desde sesión.

---

## 2. Modos de respuesta

El backend devuelve **uno de dos shapes** según presencia de `page`:

### Modo A — Legacy `list[]`

**Condición:** query sin `page`.

```json
[
  { "categoria_id": "...", "codigo": "CAT01", "nombre": "General", "es_activo": true }
]
```

**Cuándo usar en Frontend:**

- Tier A (maestros volumen bajo): combos, selects, pantallas con pocos registros
- Compatibilidad con clientes existentes

### Modo B — Envelope paginado

**Condición:** query con `page` (entero ≥ 1).

```json
{
  "items": [ { "categoria_id": "...", "codigo": "CAT01", "nombre": "General" } ],
  "total": 42,
  "pagina_actual": 1,
  "total_paginas": 1,
  "limit": 50
}
```

**Detección en cliente TypeScript:**

```typescript
function isPaginated<T>(data: T[] | PaginatedResponse<T>): data is PaginatedResponse<T> {
  return data !== null && typeof data === "object" && !Array.isArray(data) && "items" in data;
}
```

### Metadatos NO disponibles (v1)

`has_next` y `has_prev` **no existen** en contrato v1. Derivar navegación:

```typescript
const hasNext = pagina_actual < total_paginas;
const hasPrev = pagina_actual > 1;
```

---

## 3. Estructura exacta de `ErpPaginatedResponse`

Definición backend (`app/shared/pagination/schemas.py`):

```python
class ErpPaginatedResponse(BaseModel, Generic[T]):
    items: list[T]           # Registros de la página actual
    total: int               # Total que coincide con filtros (≥ 0)
    pagina_actual: int       # Página solicitada (≥ 1)
    total_paginas: int       # ceil(total / limit); total=0 → 0
    limit: int               # Tamaño de página efectivo (1–100)
```

Cada recurso expone un alias tipado en OpenAPI:

| Recurso | Schema paginado |
|---------|-----------------|
| Centros de costo | `PaginatedCentroCostoResponse` |
| Parámetros | `PaginatedParametroResponse` |
| Categorías | `PaginatedCategoriaResponse` |
| Unidades medida | `PaginatedUnidadMedidaResponse` |
| Almacenes | `PaginatedAlmacenResponse` |
| Tipos movimiento | `PaginatedTipoMovimientoResponse` |
| Productos | `PaginatedProductoResponse` |
| Movimientos | `PaginatedMovimientoResponse` |
| Kardex | `PaginatedKardexResponse` |
| Inventario físico | `PaginatedInventarioFisicoResponse` |
| Stock | `PaginatedStockResponse` |
| Stock alertas | `PaginatedStockResponse` (mismo schema) |

Todos extienden `ErpPaginatedResponse[{Entity}Read]` sin campos adicionales.

---

## 4. Tabla endpoint por endpoint

### Convenciones de la tabla

- **page:** el endpoint expone `page`/`limit` en OpenAPI
- **buscar:** filtro `buscar` SQL disponible
- **sort:** `sort_by`/`sort_dir` con whitelist
- **Tier:** perfil de listado (ver §5)

### ORG — 6 endpoints

| URL | Tier | Filtros específicos | page | buscar | sort | Columnas `sort_by` |
|-----|------|---------------------|:----:|:------:|:----:|---------------------|
| `GET /api/v1/org/empresa` | A | `solo_activos` | — | ✅ | ✅ | `codigo_empresa`, `razon_social`, `nombre_comercial`, `ruc`, `fecha_creacion` |
| `GET /api/v1/org/sucursales` | A | `solo_activos` | — | ✅ | ✅ | `codigo`, `nombre`, `tipo_sucursal`, `fecha_creacion` |
| `GET /api/v1/org/departamentos` | A | `solo_activos` | — | ✅ | ✅ | `codigo`, `nombre`, `nivel`, `fecha_creacion` |
| `GET /api/v1/org/cargos` | A | `solo_activos` | — | ✅ | ✅ | `codigo`, `nombre`, `nivel_jerarquico`, `fecha_creacion` |
| `GET /api/v1/org/centros-costo` | B | `solo_activos` | ✅ | ✅ | ✅ | `codigo`, `nombre`, `tipo_centro_costo`, `nivel`, `fecha_creacion` |
| `GET /api/v1/org/parametros` | B | `modulo_codigo`, `solo_activos` | ✅ | ✅ | ✅¹ | `modulo_codigo`, `codigo_parametro`, `nombre_parametro`, `fecha_creacion`, `fecha_actualizacion` |

¹ **Parámetros (híbrido):** merge global + override en service; sort post-merge (`apply_memory_sort`), luego slice paginado.

**Campos `buscar` por recurso ORG:**

| Recurso | Columnas ILIKE |
|---------|----------------|
| empresa | `codigo_empresa`, `razon_social`, `nombre_comercial` |
| sucursales, departamentos, cargos, centros-costo | `codigo`, `nombre` |
| parámetros | `modulo_codigo`, `codigo_parametro`, `nombre_parametro` |

### INV — 10 endpoints operativos

| URL | Tier | Filtros específicos | page | buscar | sort | Columnas `sort_by` |
|-----|------|---------------------|:----:|:------:|:----:|---------------------|
| `GET /api/v1/inv/categorias` | B | `solo_activos` | ✅ | ✅ | ✅ | `codigo`, `nombre`, `nivel`, `fecha_creacion` |
| `GET /api/v1/inv/unidades-medida` | B | `solo_activos` | ✅ | ✅ | ✅ | `codigo`, `nombre`, `tipo_unidad`, `fecha_creacion` |
| `GET /api/v1/inv/almacenes` | B | `sucursal_id`, `solo_activos` | ✅ | ✅ | ✅ | `codigo`, `nombre`, `tipo_almacen`, `fecha_creacion` |
| `GET /api/v1/inv/tipos-movimiento` | B | `solo_activos` | ✅ | ✅ | ✅ | `codigo`, `nombre`, `clase_movimiento`, `fecha_creacion` |
| `GET /api/v1/inv/productos` | B | `categoria_id`, `tipo_producto`, `solo_activos` | ✅ | ✅ | ✅ | `codigo_sku`, `nombre`, `tipo_producto`, `fecha_creacion`, `fecha_actualizacion` |
| `GET /api/v1/inv/movimientos` | C | `tipo_movimiento_id`, `almacen_id`, `estado`, `fecha_desde`, `fecha_hasta` | ✅ | — | ✅ | `numero_movimiento`, `fecha_movimiento`, `fecha_contable`, `estado`, `fecha_creacion` |
| `GET /api/v1/inv/kardex` | C | **`producto_id` (obligatorio)**, `almacen_id`, `fecha_desde`, `fecha_hasta` | ✅ | — | ✅ | `fecha_movimiento`, `cantidad_base`, `costo_unitario` |
| `GET /api/v1/inv/inventario-fisico` | C | `almacen_id`, `estado`, `fecha_desde`, `fecha_hasta` | ✅ | — | ✅ | `numero_inventario`, `fecha_inventario`, `estado`, `fecha_creacion` |
| `GET /api/v1/inv/stock` | C | `producto_id`, `almacen_id` | ✅ | — | ✅ | `cantidad_actual`, `stock_minimo`, `fecha_actualizacion` |
| `GET /api/v1/inv/stock/alertas` | C | `almacen_id` | ✅ | — | ✅ | `cantidad_actual`, `stock_minimo`, `fecha_actualizacion` |

**Campos `buscar` por recurso INV (maestros):**

| Recurso | Columnas ILIKE |
|---------|----------------|
| categorías, unidades-medida, almacenes, tipos-movimiento | `codigo`, `nombre` |
| productos | `nombre`, `codigo_sku`, `codigo_barra` |

### Endpoints excluidos (no consumir en listas nuevas)

| URL | Motivo |
|-----|--------|
| `GET /api/v1/inv/movimientos-detalle` | `deprecated=True` — detalle solo bajo cabecera |
| `GET /api/v1/inv/inventario-fisico-detalle` | `deprecated=True` — detalle solo bajo cabecera |

### Orden legacy (sin `sort_by`)

Cuando no se envía `sort_by`, el backend conserva el ORDER BY preexistente del recurso. Referencias conocidas:

| Recurso | Orden default |
|---------|---------------|
| movimientos | `fecha_movimiento DESC` |
| Resto maestros | Típicamente `codigo ASC` o `nombre ASC` + tie-breaker PK |

Al enviar `sort_by` sin `sort_dir`, el default por columna es `asc`, salvo `fecha_movimiento` → `desc`.

---

## 5. Perfiles Tier A / Tier B / Tier C

| Perfil | Recursos | Paginación | Response model | Uso Frontend recomendado |
|--------|----------|------------|----------------|--------------------------|
| **Tier A** — volumen bajo | ORG: empresa, sucursales, departamentos, cargos | No expuesto | `list[Read]` | Selects, modales, árboles pequeños. **Siempre** enviar `page` solo si el volumen crece |
| **Tier B** — escalable opt-in | ORG: centros-costo, parámetros; INV: maestros P1 | Opt-in con `page` | `Union[list, Paginated*]` | Tablas de mantenimiento. **Usar `page=1&limit=50`** en grillas |
| **Tier C** — transaccional/histórico | INV: movimientos, kardex, stock, inventario-fisico, alertas | Opt-in recomendado | `Union[list, Paginated*]` | **Obligatorio `page`** en producción. Nunca cargar dataset completo |

### Matriz de decisión Frontend

```
¿Es Tier C o lista con > 50 filas esperadas?
  SÍ → siempre page=1&limit=50 (o 25 en móvil)
  NO → ¿Es Tier A?
    SÍ → list[] sin page (con sort/buscar si aplica)
    NO (Tier B) → page opt-in; preferir paginado en tablas
```

---

## 6. Ejemplos reales request/response

Evidencia staging tenant `innova` — `P2_ORG_INV_SORT_VALIDATION.json`.

### 6.1 Legacy sin paginación (INV categorías)

**Request:**

```http
GET /api/v1/inv/categorias?solo_activos=true
Authorization: Bearer {token}
```

**Response 200:**

```json
[
  {
    "categoria_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "cliente_id": "...",
    "empresa_id": "...",
    "codigo": "GEN",
    "nombre": "General",
    "es_activo": true
  }
]
```

### 6.2 Sort server-side sin paginación

**Request:**

```http
GET /api/v1/inv/categorias?sort_by=nombre&sort_dir=asc
```

**Response 200:** `list[]` ordenado por `nombre ASC` (+ tie-breaker PK).

### 6.3 Paginación + sort (INV categorías)

**Request:**

```http
GET /api/v1/inv/categorias?page=1&limit=10&sort_by=codigo&sort_dir=asc
```

**Response 200:**

```json
{
  "items": [
    { "categoria_id": "...", "codigo": "GEN", "nombre": "General", "es_activo": true }
  ],
  "total": 3,
  "pagina_actual": 1,
  "total_paginas": 1,
  "limit": 10
}
```

### 6.4 Movimientos paginados (Tier C)

**Request:**

```http
GET /api/v1/inv/movimientos?page=1&limit=5&sort_by=fecha_movimiento&sort_dir=desc&estado=procesado
```

**Response 200:**

```json
{
  "items": [ /* 5 MovimientoRead */ ],
  "total": 14,
  "pagina_actual": 1,
  "total_paginas": 3,
  "limit": 5
}
```

### 6.5 Sort inválido → 422

**Request:**

```http
GET /api/v1/inv/categorias?sort_by=invalid_col
```

**Response 422:**

```json
{
  "detail": "sort_by 'invalid_col' no es una columna ordenable válida.",
  "error_code": "INVALID_SORT_COLUMN"
}
```

### 6.6 `sort_dir` sin `sort_by` → ignorado

**Request:**

```http
GET /api/v1/inv/categorias?sort_dir=desc
```

**Response 200:** `list[]` con orden legacy (equivalente a sin sort).

### 6.7 ORG empresa — Tier A con sort

**Request:**

```http
GET /api/v1/org/empresa?buscar=innova&sort_by=razon_social&sort_dir=asc
```

**Response 200:** `list[EmpresaRead]` (sin envelope).

### 6.8 Kardex — `producto_id` obligatorio

**Request válido:**

```http
GET /api/v1/inv/kardex?producto_id=3fa85f64-5717-4562-b3fc-2c963f66afa6&page=1&limit=50&sort_by=fecha_movimiento&sort_dir=desc
```

**Request inválido (sin producto_id):**

```http
GET /api/v1/inv/kardex?page=1
```

**Response 422** (validación FastAPI — campo requerido).

---

## 7. Recomendaciones Frontend

### 7.1 Debounce (`buscar`)

| Contexto | Debounce recomendado | Notas |
|----------|---------------------|-------|
| Campo búsqueda toolbar | **300–400 ms** | Cancelar request anterior (AbortController) |
| Búsqueda en modal/select | **200 ms** | Volumen menor |
| Tier C sin `buscar` | N/A | Usar filtros específicos del recurso |

El backend **no implementa debounce** — es responsabilidad exclusiva del cliente.

### 7.2 Tamaño de página (`limit`)

| Contexto | `limit` recomendado |
|----------|---------------------|
| Tabla desktop estándar | **50** (default backend) |
| Tabla compacta / móvil | **25** |
| Preview / widget | **10–20** |
| Máximo permitido | **100** |

Siempre enviar `page` explícito al paginar. No asumir `page=1` implícito.

### 7.3 Comportamiento de toolbar

Patrón recomendado para tablas Tier B/C:

```
[ buscar (debounced) ] [ filtros recurso ] [ solo_activos toggle ] [ refrescar ]
```

| Acción | Query params afectados |
|--------|------------------------|
| Escribir en buscar | `buscar` → reset `page=1` |
| Cambiar filtro | filtros recurso → reset `page=1` |
| Cambiar página | solo `page` |
| Cambiar tamaño página | `limit` + reset `page=1` |
| Limpiar filtros | quitar params opcionales + `page=1` |

**Estado en URL:** persistir `page`, `limit`, `buscar`, `sort_by`, `sort_dir` y filtros en query string de la ruta para deep-linking.

### 7.4 Comportamiento de sorting

| Regla | Implementación UI |
|-------|-------------------|
| Click columna ordenable | toggle `sort_by` + `sort_dir`; reset `page=1` |
| Columna no en whitelist | no mostrar indicador sort; no enviar al backend |
| Tercer click (opcional) | quitar `sort_by` → restaurar orden legacy |
| Error 422 sort | toast + revertir a último sort válido |
| Indicador visual | solo en columnas de la whitelist §4 |

**No ordenar in-memory** sobre `items` recibidos — el sort es server-side.

### 7.5 Tablas reutilizables (componente base)

Contrato sugerido para `<ErpDataTable>`:

```typescript
interface ErpListQuery {
  page?: number;
  limit?: number;
  buscar?: string;
  sort_by?: string;
  sort_dir?: "asc" | "desc";
  [filter: string]: string | number | boolean | undefined;
}

interface ErpDataTableProps<T> {
  endpoint: string;
  tier: "A" | "B" | "C";
  sortableColumns: string[];
  filters?: FilterConfig[];
  defaultSort?: { sort_by: string; sort_dir: "asc" | "desc" };
  defaultLimit?: number;
  forcePagination?: boolean; // true para Tier C
}
```

**Flujo interno:**

1. Construir query desde estado toolbar + paginación + sort
2. `GET` con AbortController
3. Si `Array.isArray(data)` → `{ items: data, total: data.length, pagina_actual: 1, total_paginas: 1, limit: data.length }` (normalizar para UI)
4. Si envelope → usar directamente
5. Paginador: `total_paginas`, `pagina_actual` (no `has_next`)

---

## 8. Breaking changes documentados

| Cambio | Impacto Frontend | Mitigación |
|--------|------------------|------------|
| **Kardex requiere `producto_id`** | `GET /inv/kardex` sin `producto_id` → 422 | Pantalla kardex: selector de producto obligatorio antes de cargar tabla. No implementar kardex global multi-producto |
| Paginación opt-in | Sin `page` → `list[]` (no envelope) | Detectar tipo respuesta; Tier C siempre enviar `page` |
| `limit` sin `page` ignorado | Enviar `limit` solo con `page` | Acoplar params en hook de listado |
| `sort_by` inválido → 422 (no 400) | Manejar `error_code: INVALID_SORT_COLUMN` | Whitelist local sincronizada con §4 |
| Sin `has_next`/`has_prev` | Paginadores que esperaban esos campos | Calcular desde `pagina_actual` / `total_paginas` |

### No son breaking (compatibilidad preservada)

- Llamadas legacy sin `page`/`sort` siguen funcionando
- Tier A sin paginación sigue siendo conforme
- Filtros existentes (`estado`, `fecha_desde`, etc.) sin cambio de semántica

---

## 9. Checklist PERF — implementación Frontend

### PERF-01 — Paginación server-side

| # | Tarea | Tier | Estado backend |
|---|-------|------|----------------|
| 1.1 | Hook `useErpList` con `page`/`limit` opt-in | B, C | ✅ Listo |
| 1.2 | Normalizar `list[]` vs envelope en capa API | A, B, C | ✅ Listo |
| 1.3 | Paginador UI con `pagina_actual`/`total_paginas`/`total` | B, C | ⏳ Frontend |
| 1.4 | Tier C: forzar `page=1` en mount | C | ⏳ Frontend |
| 1.5 | No asumir `has_next`/`has_prev` | B, C | ⏳ Frontend |

### PERF-02 — Búsqueda con debounce

| # | Tarea | Tier | Estado backend |
|---|-------|------|----------------|
| 2.1 | Input `buscar` en toolbar maestros | A, B | ✅ SQL ILIKE listo |
| 2.2 | Debounce 300–400 ms + abort previo | A, B | ⏳ Frontend |
| 2.3 | Reset `page=1` al buscar | B | ⏳ Frontend |
| 2.4 | Placeholder contextual por recurso | A, B | ⏳ Frontend |

### PERF-03 — Filtros toolbar

| # | Tarea | Recursos | Estado backend |
|---|-------|----------|----------------|
| 3.1 | Filtro `solo_activos` (default true) | Maestros | ✅ Listo |
| 3.2 | Filtros UUID: `categoria_id`, `almacen_id`, `tipo_movimiento_id`, etc. | B, C | ✅ Listo |
| 3.3 | Filtros fecha: `fecha_desde`, `fecha_hasta` | movimientos, kardex, inventario-fisico | ✅ Listo |
| 3.4 | Filtro `modulo_codigo` | parámetros ORG | ✅ Listo |
| 3.5 | Filtro `estado` | movimientos, inventario-fisico | ✅ Listo |
| 3.6 | Filtro `tipo_producto` | productos | ✅ Listo |
| 3.7 | Chips de filtros activos + limpiar | Todos | ⏳ Frontend |

### PERF-04 — Sort server-side

| # | Tarea | Tier | Estado backend |
|---|-------|------|----------------|
| 4.1 | Cabeceras clickables solo en whitelist §4 | A, B, C | ✅ Listo |
| 4.2 | Enviar `sort_by` + `sort_dir`; reset `page=1` | A, B, C | ⏳ Frontend |
| 4.3 | Manejar 422 `INVALID_SORT_COLUMN` | A, B, C | ✅ Listo |
| 4.4 | Ignorar `sort_dir` si no hay `sort_by` activo | A, B, C | ⏳ Frontend |
| 4.5 | Default sort movimientos: `fecha_movimiento desc` | C | ✅ Listo |

### PERF-05 — Componentes UI reutilizables

| # | Tarea | Estado |
|---|-------|--------|
| 5.1 | `<ErpDataTable>` genérico con slots toolbar/filtros | ⏳ Frontend |
| 5.2 | `<ErpSearchInput>` con debounce integrado | ⏳ Frontend |
| 5.3 | `<ErpPagination>` sin `has_next` | ⏳ Frontend |
| 5.4 | `<ErpSortableHeader>` con whitelist | ⏳ Frontend |
| 5.5 | Storybook/documentación de componentes | ⏳ Frontend |

> PERF-05 es **100% Frontend** — backend no bloquea.

### PERF-06 — Estrategia escalabilidad (cierre)

| # | Criterio | Backend | Frontend |
|---|----------|---------|----------|
| 6.1 | Sin sort in-memory en datasets grandes | ✅ | ⏳ Verificar en tablas Tier C |
| 6.2 | Sin filtrar in-memory post-fetch | ✅ | ⏳ Verificar hooks |
| 6.3 | Tier C siempre paginado en producción | ✅ disponible | ⏳ Implementar |
| 6.4 | Contrato único ORG/INV documentado | ✅ | ⏳ Este documento |
| 6.5 | OpenAPI como segunda fuente de verdad | ✅ | ⏳ Generar tipos desde OpenAPI |

---

## Apéndice A — Permisos RBAC por listado

| Endpoint | Permiso |
|----------|---------|
| `/org/empresa` | `org.empresa.leer` |
| `/org/sucursales` | `org.sucursal.leer` |
| `/org/departamentos` | `org.departamento.leer` |
| `/org/cargos` | `org.cargo.leer` |
| `/org/centros-costo` | `org.centro_costo.leer` |
| `/org/parametros` | `org.parametro.leer` |
| `/inv/categorias` | `inv.categoria.leer` |
| `/inv/unidades-medida` | `inv.unidad_medida.leer` |
| `/inv/almacenes` | `inv.almacen.leer` |
| `/inv/tipos-movimiento` | `inv.tipo_movimiento.leer` |
| `/inv/productos` | `inv.producto.leer` |
| `/inv/movimientos` | `inv.movimiento.leer` |
| `/inv/kardex` | `inv.movimiento.leer` |
| `/inv/inventario-fisico` | `inv.inventario_fisico.leer` |
| `/inv/stock` | `inv.stock.leer` |
| `/inv/stock/alertas` | `inv.stock.leer` |

---

## Apéndice B — Evidencia backend

| Artefacto | Ruta |
|-----------|------|
| Auditoría consolidada | `app/docs/auditoria/P0_P1_P2_ORG_INV_LISTADOS_FINAL_AUDIT.md` |
| Validación sort staging | `app/bootstrap_v2/00_manifest/evidence/P2_ORG_INV_SORT_VALIDATION.json` |
| Estándar congelado | `app/docs/arquitectura/ERP_BACKEND_STANDARDS_V4.md` §10 |

---

*CAXIS ERP — Frontend Listados Contract v1 — 2026-06-15 — Basado en implementación congelada P0+P1+P2-001*
