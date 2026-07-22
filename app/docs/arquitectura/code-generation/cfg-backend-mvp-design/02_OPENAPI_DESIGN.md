# Diseño OpenAPI y contratos (MVP)

**Paquete:** `cfg-backend-mvp-design`  
**Fecha:** 2026-07-17  
**Base path:** `/api/v1/cfg/secuencias`  
**Nota:** Contratos de diseño — **no** se modifica el snapshot OpenAPI hasta la implementación.

---

## 1. Endpoints REST definitivos

### 1.1 GET `/cfg/secuencias`

**Summary:** Listar secuencias de código del tenant  
**OperationId:** `list_cfg_codigo_secuencias`  
**RBAC:** `cfg.secuencias.consultar`

**Query parameters:**

| Nombre | Tipo | Required | Descripción |
|--------|------|----------|-------------|
| `empresa_id` | uuid | no | Filtrar por empresa |
| `scope_type` | string enum | no | `TENANT` \| `EMPRESA` \| `ALMACEN` \| `PUNTO_VENTA` |
| `sequence_key` | string | no | Igualdad exacta |
| `es_activo` | boolean | no | Filtro estado |
| `modulo_codigo` | string | no | Filtro post-enrich (ORG, INV, …) |
| `buscar` | string | no | LIKE key/prefijo |
| `page` | int | no | Opt-in paginación |
| `limit` | int | no | Default 50, max 100; ignorado sin `page` |
| `sort_by` | string | no | Whitelist |
| `sort_dir` | `asc`\|`desc` | no | Ignorado sin `sort_by` |

**Responses:**

| Código | Body |
|--------|------|
| 200 | `CodigoSecuenciaRead[]` **o** `PaginatedCodigoSecuenciaResponse` si `page` |
| 403 | Sin permiso |
| 422 | `sort_by` inválido (`INVALID_SORT_COLUMN`) |

---

### 1.2 GET `/cfg/secuencias/{secuencia_id}`

**OperationId:** `get_cfg_codigo_secuencia`  
**RBAC:** `cfg.secuencias.consultar`  
**Path:** `secuencia_id` uuid

| Código | Body |
|--------|------|
| 200 | `CodigoSecuenciaRead` |
| 404 | No encontrada / cross-tenant |
| 403 | Sin permiso |

---

### 1.3 PATCH `/cfg/secuencias/{secuencia_id}`

**OperationId:** `update_cfg_codigo_secuencia`  
**RBAC:** `cfg.secuencias.actualizar`  
**Body:** `CodigoSecuenciaUpdate` (todos optional; al menos un campo)

| Código | Body |
|--------|------|
| 200 | `CodigoSecuenciaRead` |
| 404 | No encontrada |
| 409 | `CFG_FORMAT_COLLISION` |
| 422 | Validación / `ORG_EMPRESA_CFG_LOCKED` / `IMMUTABLE_FIELD` |
| 403 | Sin permiso |

---

### 1.4 POST `/cfg/secuencias/{secuencia_id}/activar`

**OperationId:** `activar_cfg_codigo_secuencia`  
**RBAC:** `cfg.secuencias.actualizar`  
**Body:** vacío

| Código | Body |
|--------|------|
| 200 | `CodigoSecuenciaRead` (`es_activo=true`) |
| 404 / 403 | estándar |

Idempotente si ya activa.

---

### 1.5 POST `/cfg/secuencias/{secuencia_id}/desactivar`

**OperationId:** `desactivar_cfg_codigo_secuencia`  
**RBAC:** `cfg.secuencias.actualizar`  
**Body:** vacío

| Código | Body |
|--------|------|
| 200 | `CodigoSecuenciaRead` (`es_activo=false`) |
| 422 | `ORG_EMPRESA_CFG_LOCKED` |
| 404 / 403 | estándar |

---

### 1.6 POST `/cfg/secuencias/{secuencia_id}/preview`

**OperationId:** `preview_cfg_codigo_secuencia`  
**RBAC:** `cfg.secuencias.consultar`  
**Body:** vacío (scope desde fila)

| Código | Body |
|--------|------|
| 200 | `CodigoSecuenciaPreviewResponse` |
| 404 | Fila o cfg scope no resoluble |
| 409 | Conflictos Motor si aplican |
| 403 | Sin permiso |

---

## 2. Endpoints explícitamente fuera de MVP (no diseñar implementación)

| Ruta | Motivo |
|------|--------|
| POST `/cfg/secuencias` | Create admin prohibido |
| DELETE `/cfg/secuencias/{id}` | Soft-disable only |
| POST `.../align` | Fase v1.1 |
| GET `.../diagnostico` | Fase v1.2 |
| POST `.../validar-config` | Post-MVP |
| POST `/cfg/secuencias/validar-manual` | Post-MVP |
| PATCH `ultimo_numero` / `generation_policy` | Prohibido |

---

## 3. Schemas Request / Response

### 3.1 `CodigoSecuenciaRead`

```json
{
  "secuencia_id": "uuid",
  "sequence_key": "org_sucursal",
  "scope_type": "EMPRESA",
  "scope_fingerprint": "…",
  "empresa_id": "uuid|null",
  "almacen_id": "uuid|null",
  "punto_venta_id": "uuid|null",
  "prefijo": "SUC",
  "separador": "",
  "longitud_numero": 3,
  "numero_inicial": 1,
  "ultimo_numero": 41,
  "es_activo": true,
  "generation_policy": "AUTO_DEFAULT",
  "fecha_creacion": "datetime",
  "fecha_actualizacion": "datetime|null",
  "usuario_actualizacion_id": "uuid|null",
  "entity_table": "org_sucursal",
  "code_column": "codigo",
  "modulo_codigo": "ORG",
  "catalog_policy": "AUTO_DEFAULT",
  "supports_preview": true,
  "allow_manual": true,
  "sequence_family": "F1",
  "default_prefix": "SUC",
  "default_separator": "",
  "default_padding": 3,
  "config_locked": false,
  "policy_drift": false
}
```

| Campo enrich | Origen |
|--------------|--------|
| `entity_table` … `default_padding` | `SequenceCatalog` |
| `config_locked` | `true` si `sequence_key == org_empresa` |
| `policy_drift` | `generation_policy != catalog_policy` |

**No incluir en Read público MVP:** `cliente_id` (redundante/sesión). Opcional en panel técnico — **omitir**.

### 3.2 `CodigoSecuenciaUpdate`

```json
{
  "prefijo": "SUC",
  "separador": "",
  "longitud_numero": 4,
  "numero_inicial": 1
}
```

Todos `Optional`. Extra fields (`ultimo_numero`, `generation_policy`, …) → **forbid** (`model_config extra='forbid'`) → 422.

Validators before: `normalize_upper(prefijo)`, strip separador.

**Nota:** `es_activo` **no** va en PATCH; solo vía activar/desactivar (diseño funcional).

### 3.3 `PaginatedCodigoSecuenciaResponse`

Extiende `ErpPaginatedResponse[CodigoSecuenciaRead]`:

```json
{
  "items": [],
  "total": 0,
  "pagina_actual": 1,
  "total_paginas": 1,
  "limit": 50
}
```

### 3.4 `CodigoSecuenciaPreviewResponse`

```json
{
  "secuencia_id": "uuid",
  "sequence_key": "org_sucursal",
  "codigo_estimado": "SUC042",
  "ultimo_numero_actual": 41,
  "numero_inicial": 1,
  "consume_contador": false,
  "es_activo": true,
  "disclaimer": "Estimación no vinculante. El código definitivo se asigna al crear el registro."
}
```

`disclaimer` preferir el de `PreviewResult` del Gateway (fuente única).

---

## 4. Códigos de error estables (OpenAPI/docs)

| internal_code | HTTP | Cuándo |
|---------------|------|--------|
| `CFG_SEQUENCE_NOT_FOUND` / NotFound estándar | 404 | Detalle/patch/preview |
| `ORG_EMPRESA_CFG_LOCKED` | 422 | PATCH/desactivar org_empresa |
| `IMMUTABLE_FIELD` | 422 | Campos A/C/D |
| `CFG_PREFIX_INVALID` | 422 | Prefijo |
| `CFG_PADDING_INVALID` | 422 | Padding |
| `CFG_SEPARATOR_INVALID` | 422 | Separador |
| `CFG_NUMERO_INICIAL_INVALID` | 422 | Piso |
| `CFG_NUMERO_INICIAL_CONFLICT` | 422 | Piso vs contador |
| `CFG_FORMAT_COLLISION` | 409 | Colisión formato entre keys |
| `INVALID_SORT_COLUMN` | 422 | sort_by |
| `SEQUENCE_INACTIVE` | 409 | Si Gateway lo emite en preview |
| `CFG_SEQUENCE_NOT_FOUND` | 404 | Motor sin fila en preview |

---

## 5. Response model Union (listado)

```text
response_model=Union[list[CodigoSecuenciaRead], PaginatedCodigoSecuenciaResponse]
```

Sin `page` → lista legacy; con `page` → envelope. Alineado ORG/INV.

---

## 6. Seguridad en contrato

- Sin `cliente_id` en query/body para autorización.  
- Path UUID v4.  
- `deprecated=False` en todos los endpoints MVP (recursos nuevos).
