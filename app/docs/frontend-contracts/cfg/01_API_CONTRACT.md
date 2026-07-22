# CFG — Contrato de API (consumo Frontend)

**Versión:** 1.0  
**Base:** `/api/v1/cfg/secuencias`  
**OpenAPI:** `app/docs/openapi_snapshot.json`

Este documento describe **cómo llamar** la API. Los schemas detallados viven en OpenAPI; aquí solo lo necesario para integrar.

Todas las llamadas requieren sesión ERP autenticada (JWT / sesión tenant activa). El tenant operativo lo resuelve el Backend; **no** enviar `cliente_id` en body ni query para autorización.

---

## 1. Listar secuencias

| | |
|--|--|
| **Método** | `GET` |
| **Path** | `/api/v1/cfg/secuencias` |
| **operationId** | `list_cfg_codigo_secuencias` |
| **Permiso** | `cfg.secuencias.consultar` |

### Query parameters

| Param | Tipo | Obligatorio | Notas de consumo |
|-------|------|:-----------:|------------------|
| `empresa_id` | uuid | No | Filtra por empresa |
| `scope_type` | string | No | `TENANT` \| `EMPRESA` \| `ALMACEN` \| `PUNTO_VENTA` |
| `sequence_key` | string | No | Igualdad exacta |
| `es_activo` | boolean | No | Activas / inactivas |
| `modulo_codigo` | string | No | Ej. `ORG`, `INV` |
| `buscar` | string | No | Busca en `sequence_key` / `prefijo` |
| `page` | int | No | Si se envía → respuesta paginada |
| `limit` | int | No | Default 50, máx. 100; **ignorado si no hay `page`** |
| `sort_by` | string | No | Whitelist (ver abajo) |
| `sort_dir` | string | No | `asc` \| `desc`; **ignorado sin `sort_by`** |

**`sort_by` permitido:** `sequence_key`, `scope_type`, `prefijo`, `ultimo_numero`, `es_activo`, `fecha_creacion`, `fecha_actualizacion`.

### Responses

| HTTP | Body |
|------|------|
| **200** sin `page` | Array `CodigoSecuenciaRead[]` |
| **200** con `page` | Envelope: `{ items, total, pagina_actual, total_paginas, limit }` |
| **403** | Sin permiso `consultar` |
| **422** | `sort_by` inválido (`INVALID_SORT_COLUMN`) |

---

## 2. Obtener detalle

| | |
|--|--|
| **Método** | `GET` |
| **Path** | `/api/v1/cfg/secuencias/{secuencia_id}` |
| **operationId** | `get_cfg_codigo_secuencia` |
| **Permiso** | `cfg.secuencias.consultar` |

### Path

| Param | Tipo |
|-------|------|
| `secuencia_id` | uuid |

### Responses

| HTTP | Body |
|------|------|
| **200** | `CodigoSecuenciaRead` |
| **403** | Sin permiso |
| **404** | No existe o no visible en el tenant |

---

## 3. Actualizar configuración (formato)

| | |
|--|--|
| **Método** | `PATCH` |
| **Path** | `/api/v1/cfg/secuencias/{secuencia_id}` |
| **operationId** | `update_cfg_codigo_secuencia` |
| **Permiso** | `cfg.secuencias.actualizar` |

### Request body (`CodigoSecuenciaUpdate`)

Todos opcionales; **al menos un campo**. Campos extra → rechazo 422.

| Campo | Tipo | Reglas de envío |
|-------|------|-----------------|
| `prefijo` | string | Se normaliza a mayúsculas; máx. 10 |
| `separador` | string | Solo `""` o `"-"` |
| `longitud_numero` | int | ≥ 1 |
| `numero_inicial` | int | ≥ 1 |

**No enviar:** `es_activo`, `ultimo_numero`, `generation_policy`, identity/scope, ni otros campos.

### Responses

| HTTP | Body / significado |
|------|--------------------|
| **200** | `CodigoSecuenciaRead` actualizado |
| **403** | Sin permiso `actualizar` |
| **404** | No encontrada |
| **422** | Validación o secuencia bloqueada (`org_empresa`) |

---

## 4. Desactivar (soft)

| | |
|--|--|
| **Método** | `DELETE` |
| **Path** | `/api/v1/cfg/secuencias/{secuencia_id}` |
| **operationId** | `desactivar_cfg_codigo_secuencia` |
| **Permiso** | `cfg.secuencias.actualizar` |
| **Body** | Ninguno |

Efecto: `es_activo = false`. **No** elimina el registro.

Idempotente: si ya está inactiva → **200**.

### Responses

| HTTP | Significado |
|------|-------------|
| **200** | `CodigoSecuenciaRead` con `es_activo=false` |
| **403** | Sin permiso |
| **404** | No encontrada |
| **422** | Bloqueada (`org_empresa`) |

---

## 5. Reactivar

| | |
|--|--|
| **Método** | `POST` |
| **Path** | `/api/v1/cfg/secuencias/{secuencia_id}/reactivar` |
| **operationId** | `reactivar_cfg_codigo_secuencia` |
| **Permiso** | `cfg.secuencias.actualizar` |
| **Body** | Ninguno (o vacío) |

Efecto: `es_activo = true`.

Idempotente: si ya está activa → **200**.

### Responses

| HTTP | Significado |
|------|-------------|
| **200** | `CodigoSecuenciaRead` con `es_activo=true` |
| **403** | Sin permiso |
| **404** | No encontrada |

---

## 6. Preview (estimación)

| | |
|--|--|
| **Método** | `POST` |
| **Path** | `/api/v1/cfg/secuencias/{secuencia_id}/preview` |
| **operationId** | `preview_cfg_codigo_secuencia` |
| **Permiso** | `cfg.secuencias.consultar` |
| **Body** | Vacío |

### Response 200 (`CodigoSecuenciaPreviewResponse`)

Campos principales:

| Campo | Notas para UI |
|-------|---------------|
| `codigo_estimado` | Valor a mostrar como estimación |
| `ultimo_numero_actual` | Contador actual (no cambia por el preview) |
| `numero_inicial` | Configurado en la secuencia |
| `consume_contador` | Siempre `false` |
| `es_activo` | Puede ser `false`; preview sigue siendo válido |
| `disclaimer` | Mostrar siempre al usuario |

### Responses

| HTTP | Significado |
|------|-------------|
| **200** | Estimación (también si la secuencia está inactiva) |
| **403** | Sin permiso |
| **404** | No encontrada |
| **422** | Preview no permitido para esa secuencia |

---

## 7. Campos clave en `CodigoSecuenciaRead` (lectura UI)

Usar OpenAPI para el schema completo. Campos especialmente útiles en pantalla:

| Campo | Uso UI |
|-------|--------|
| `secuencia_id` | ID de ruta y keys de lista |
| `sequence_key` | Identificador de negocio |
| `prefijo`, `separador`, `longitud_numero`, `numero_inicial` | Editables (si no locked) |
| `ultimo_numero` | Solo lectura |
| `es_activo` | Estado activo/inactivo |
| `generation_policy` | Solo lectura |
| `modulo_codigo` | Filtro / etiqueta |
| `config_locked` | Si `true` → no editar ni desactivar |
| `policy_drift` | Indicador informativo (drift de política) |
| `supports_preview` | Si `false` → ocultar/deshabilitar Preview |

`cliente_id` **no** viene en la respuesta.

---

## 8. Códigos HTTP (resumen)

| Código | Cuándo |
|--------|--------|
| 200 | Éxito |
| 403 | Falta permiso RBAC |
| 404 | Recurso no visible / no existe |
| 422 | Validación de negocio o schema / sort inválido |
