# API — especificación oficial v1.0

**Paquete:** `cfg-implementation-spec`  
**Base path:** `/api/v1/cfg/secuencias`  
**Versión contrato:** 1.0

---

## 1. Endpoints

### 1.1 GET `/cfg/secuencias`

- **operationId:** `list_cfg_codigo_secuencias`
- **RBAC:** `cfg.secuencias.consultar`

**Query params:**

| Param | Tipo | Notas |
|-------|------|-------|
| `empresa_id` | uuid | Opcional |
| `scope_type` | enum | TENANT \| EMPRESA \| ALMACEN \| PUNTO_VENTA |
| `sequence_key` | string | Igualdad |
| `es_activo` | bool | Opcional |
| `modulo_codigo` | string | Filtro **post-enrich** (G-04) |
| `buscar` | string | LIKE `sequence_key` / `prefijo` |
| `page` | int | Opt-in paginación |
| `limit` | int | Default 50, max 100; ignorado sin `page` |
| `sort_by` | string | Whitelist |
| `sort_dir` | asc\|desc | Ignorado sin `sort_by` |

**Pipeline listado (G-04 opción A — oficial):**

```text
1. SQL: filtros nativos + cliente_id (SIN apply_erp_pagination en SQL)
2. Enrich Catalog cada fila
3. Filtro modulo_codigo in-memory (si viene)
4. Sort in-memory (whitelist) o SQL sort antes de enrich si no hay modulo filter —
   Oficial: sort in-memory tras enrich para un solo camino
5. Si page: slice + total = len(filtrado) → PaginatedCodigoSecuenciaResponse
6. Si no page: list[CodigoSecuenciaRead] completa filtrada
```

**Sort whitelist:** `sequence_key`, `scope_type`, `prefijo`, `ultimo_numero`, `es_activo`, `fecha_creacion`, `fecha_actualizacion` + tie-breaker `secuencia_id`.  
Inválido → 422 `INVALID_SORT_COLUMN`.

**Response 200:** `list[CodigoSecuenciaRead]` \| `PaginatedCodigoSecuenciaResponse`

---

### 1.2 GET `/cfg/secuencias/{secuencia_id}`

- **operationId:** `get_cfg_codigo_secuencia`
- **RBAC:** `cfg.secuencias.consultar`
- **200:** `CodigoSecuenciaRead`
- **404:** no existe / otro tenant

---

### 1.3 PATCH `/cfg/secuencias/{secuencia_id}`

- **operationId:** `update_cfg_codigo_secuencia`
- **RBAC:** `cfg.secuencias.actualizar`
- **Body:** `CodigoSecuenciaUpdate` (todos optional; ≥1 campo)
- **200:** `CodigoSecuenciaRead`
- **422:** validación / `ORG_EMPRESA_CFG_LOCKED`
- **404:** no encontrada

`es_activo` **no** forma parte del PATCH.

---

### 1.4 DELETE `/cfg/secuencias/{secuencia_id}` (G-01)

- **operationId:** `desactivar_cfg_codigo_secuencia`
- **RBAC:** `cfg.secuencias.actualizar`
- **Efecto:** `es_activo = false` (soft; **no** DELETE físico)
- **200:** `CodigoSecuenciaRead`
- **422:** `ORG_EMPRESA_CFG_LOCKED` si `sequence_key == org_empresa`
- **404:** no encontrada  
Idempotente si ya inactiva → 200.

---

### 1.5 POST `/cfg/secuencias/{secuencia_id}/reactivar` (G-01)

- **operationId:** `reactivar_cfg_codigo_secuencia`
- **RBAC:** `cfg.secuencias.actualizar`
- **Efecto:** `es_activo = true`
- **200:** `CodigoSecuenciaRead`  
Idempotente si ya activa → 200.

---

### 1.6 POST `/cfg/secuencias/{secuencia_id}/preview`

- **operationId:** `preview_cfg_codigo_secuencia`
- **RBAC:** `cfg.secuencias.consultar`
- **Body:** vacío
- **200:** `CodigoSecuenciaPreviewResponse` aunque `es_activo=false` (**G-05**)
- **422:** `PREVIEW_NOT_ALLOWED` si Catalog `supports_preview=false`
- **404:** fila no encontrada / scope no resoluble

`consume_contador` siempre `false`. No llama allocate.

---

## 2. Fuera de contrato MVP

No implementar: POST create, DELETE físico, align, diagnóstico, validar-manual, validar-config, PATCH de `ultimo_numero` / `generation_policy` / scope / key.

---

## 3. Schemas

### 3.1 `CodigoSecuenciaRead`

| Campo | Tipo | Notas |
|-------|------|-------|
| `secuencia_id` | uuid | |
| `sequence_key` | string | |
| `scope_type` | string | |
| `scope_fingerprint` | string | |
| `empresa_id` | uuid\|null | |
| `almacen_id` | uuid\|null | |
| `punto_venta_id` | uuid\|null | |
| `prefijo` | string | |
| `separador` | string | |
| `longitud_numero` | int | |
| `numero_inicial` | int | |
| `ultimo_numero` | int | solo lectura |
| `es_activo` | bool | |
| `generation_policy` | string | solo lectura |
| `fecha_creacion` | datetime | |
| `fecha_actualizacion` | datetime\|null | |
| `usuario_actualizacion_id` | uuid\|null | |
| `entity_table` | string\|null | Catalog |
| `code_column` | string\|null | Catalog |
| `modulo_codigo` | string\|null | Catalog |
| `catalog_policy` | string\|null | Catalog |
| `supports_preview` | bool\|null | Catalog |
| `allow_manual` | bool\|null | Catalog |
| `sequence_family` | string\|null | Catalog |
| `default_prefix` | string\|null | Catalog |
| `default_separator` | string\|null | Catalog |
| `default_padding` | int\|null | Catalog |
| `config_locked` | bool | `true` si `org_empresa` |
| `policy_drift` | bool | cfg policy ≠ catalog |

**Omitir:** `cliente_id` en response.

### 3.2 `CodigoSecuenciaUpdate`

| Campo | Tipo | Notas |
|-------|------|-------|
| `prefijo` | string\|omit | normalize_upper; max 10 |
| `separador` | string\|omit | solo `""` o `"-"` |
| `longitud_numero` | int\|omit | ≥ 1 |
| `numero_inicial` | int\|omit | ≥ 1 (**G-03**) |

`model_config`: `extra='forbid'`.

### 3.3 `PaginatedCodigoSecuenciaResponse`

`ErpPaginatedResponse[CodigoSecuenciaRead]`: `items`, `total`, `pagina_actual`, `total_paginas`, `limit`.

### 3.4 `CodigoSecuenciaPreviewResponse`

| Campo | Tipo |
|-------|------|
| `secuencia_id` | uuid |
| `sequence_key` | string |
| `codigo_estimado` | string |
| `ultimo_numero_actual` | int |
| `numero_inicial` | int |
| `consume_contador` | bool (= false) |
| `es_activo` | bool |
| `disclaimer` | string (desde `PreviewResult`) |

---

## 4. Errores estables

| internal_code | HTTP | Uso |
|---------------|------|-----|
| (NotFound) | 404 | Fila / cross-tenant |
| `ORG_EMPRESA_CFG_LOCKED` | 422 | PATCH o DELETE soft sobre `org_empresa` |
| `CFG_PREFIX_INVALID` | 422 | Prefijo |
| `CFG_PADDING_INVALID` | 422 | Padding |
| `CFG_SEPARATOR_INVALID` | 422 | Separador |
| `CFG_NUMERO_INICIAL_INVALID` | 422 | `numero_inicial < 1` |
| `PREVIEW_NOT_ALLOWED` | 422 | Catalog |
| `INVALID_SORT_COLUMN` | 422 | sort_by |
| (Authorization) | 403 | Sin permiso |

**No usar en MVP:** `CFG_FORMAT_COLLISION`, `CFG_NUMERO_INICIAL_CONFLICT`, `SEQUENCE_INACTIVE` en preview admin, `IMMUTABLE_FIELD` (cubierto por `extra='forbid'`).
