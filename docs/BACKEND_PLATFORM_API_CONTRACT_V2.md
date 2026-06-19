# BACKEND_PLATFORM_API_CONTRACT_V2.md

**Programa:** A — Backend  
**Versión:** 2.0  
**Fecha:** 2026-06-17  
**Audiencia:** Equipo Frontend (repositorio independiente)  
**Alcance:** Contrato HTTP vigente de los listados administrativos del Programa A

> Este documento describe **únicamente el contrato HTTP**. No incluye implementación interna, SQL, arquitectura ni decisiones de diseño Backend.

---

## Tabla resumen — Endpoints del Programa A

| ID | Método | Ruta | Cambio Programa A | Tipo de cambio |
|----|--------|------|-------------------|----------------|
| PA-001 | `GET` | `/api/v1/usuarios/` | Corrección paginación server-side | **Sin cambio de contrato HTTP** |
| IAM-PA-001 | `GET` | `/api/v1/usuarios/` | Filtros vigencia (`solo_activos`, `solo_inactivos`) | **Aditivo** |
| IAM-PA-001 | `POST` | `/api/v1/usuarios/{usuario_id}/reactivate/` | Reactivación canónica | **Aditivo** |
| IAM-BE-02 | `PUT` | `/api/v1/usuarios/{usuario_id}/` | Semántica ciclo de vida documentada (sin cambio HTTP) | **Sin cambio** |
| IAM-BE-02 | `DELETE` | `/api/v1/usuarios/{usuario_id}/` | Semántica soft delete documentada (sin cambio HTTP) | **Sin cambio** |
| IAM-SESSIONS-PA-001 | `GET` | `/api/v1/auth/sessions/admin/` | Paginación, búsqueda, sort y filtros | **Aditivo** |
| PA-002 | `GET` | `/api/v1/permisos-catalogo` | Sin implementación Backend | **Sin cambio** |
| IAM-PA-001 | `GET` | `/api/v1/roles/` | Filtros vigencia (`solo_activos`, `solo_inactivos`) | **Aditivo** |
| — | `GET` | `/api/v1/roles/` | Sin ítem PA (referencia vigente) | **Sin cambio** |
| PA-003 | `GET` | `/api/v1/modulos-v2/` | Búsqueda server-side | **Aditivo** (`buscar`) |
| PA-004 | `GET` | `/api/v1/clientes/` | Filtro solo inactivos | **Aditivo** (`solo_inactivos`) |
| PA-005 | `GET` | `/api/v1/catalogos-globales/monedas` | Listado escalable | **Breaking change** |
| PA-005 | `GET` | `/api/v1/catalogos-globales/paises` | Listado escalable | **Breaking change** |
| PA-005 | `GET` | `/api/v1/catalogos-globales/departamentos` | Listado escalable | **Breaking change** |
| PA-005 | `GET` | `/api/v1/catalogos-globales/provincias` | Listado escalable | **Breaking change** |
| PA-005 | `GET` | `/api/v1/catalogos-globales/distritos` | Listado escalable | **Breaking change** |

**Base URL:** `{API_BASE}/api/v1`  
**Autenticación global:** Header `Authorization: Bearer {JWT}` en todos los endpoints.

---

# 1. GET /api/v1/usuarios/

**Programa A:** PA-001 + IAM-PA-001  
**Breaking change:** No (cambio aditivo IAM-PA-001)

## ANTES / DESPUÉS

| Aspecto | ANTES | DESPUÉS |
|---------|-------|---------|
| Shape HTTP 200 | `PaginatedUsuarioResponse` | **Igual** |
| Parámetros Query | `page`, `limit`, `search` | **+ `solo_activos`, `solo_inactivos`** |
| Comportamiento paginación | Bug: páginas inconsistentes con multi-rol | **Corregido:** paginación sobre usuarios distintos |
| Filtro vigencia | Implícito inconsistente | **`solo_activos` / `solo_inactivos` (PA-004)** |

> El envelope HTTP no cambia. Los params `page`, `limit` y `search` se mantienen.

## Contrato vigente

| Campo | Valor |
|-------|-------|
| **Método** | `GET` |
| **Ruta** | `/api/v1/usuarios/` |
| **Autorización** | JWT + rol Administrador + permiso `admin.usuario.leer` |
| **Path params** | — |
| **Request body** | — |

### Query params

| Param | Tipo | Default | Validación | Descripción |
|-------|------|---------|------------|-------------|
| `page` | `integer` | `1` | `≥ 1` | Número de página (base 1) |
| `limit` | `integer` | `10` | `1–100` | Usuarios por página |
| `search` | `string` | — | opcional; `min_length=1`, `max_length=50` | Búsqueda en nombre, apellido, correo, nombre_usuario |
| `solo_activos` | `boolean` | `true` | — | Solo usuarios activos (`es_activo=1`, `es_eliminado=0`) |
| `solo_inactivos` | `boolean` | `false` | — | Solo usuarios inactivos (`es_activo=0`, `es_eliminado=0`); precedencia sobre `solo_activos` |

**Precedencia filtro vigencia (PA-004):**

```
si solo_inactivos = true  →  es_activo = 0 AND es_eliminado = 0
si no, si solo_activos = true  →  es_activo = 1 AND es_eliminado = 0
si no  →  es_eliminado = 0 (activos + inactivos, sin eliminados lógicos)
```

Los usuarios con `es_eliminado=1` **nunca** aparecen en el listado; usar `POST .../reactivate/` para restaurarlos.

### Response 200

**Response model:** `PaginatedUsuarioResponse`

**Envelope:** Sí — campos en raíz (sin wrapper `success`/`data`).

| Campo envelope | Tipo | Descripción |
|----------------|------|-------------|
| `usuarios` | `UsuarioReadWithRoles[]` | Página actual |
| `total_usuarios` | `integer ≥ 0` | Total post-filtro |
| `pagina_actual` | `integer ≥ 1` | Página devuelta |
| `total_paginas` | `integer ≥ 0` | Total de páginas |

**Objeto de negocio `UsuarioReadWithRoles`** (campos principales):

| Campo | Tipo |
|-------|------|
| `usuario_id` | `UUID` |
| `nombre_usuario` | `string` |
| `correo` | `string \| null` |
| `nombre` | `string \| null` |
| `apellido` | `string \| null` |
| `es_activo` | `boolean` |
| `fecha_creacion` | `datetime` (ISO 8601) |
| `roles` | `RolRead[]` |
| `access_level` | `integer` (1–5) |
| `is_super_admin` | `boolean` |
| `user_type` | `string` |
| `permisos` | `string[]` |

### Paginación

Modelo **`page` + `limit`** (no `skip`).

```
total_paginas = ceil(total_usuarios / limit)
pagina_actual = page solicitado
```

### Búsqueda

Param **`search`** — server-side. Si se omite, no hay filtro textual.

### Filtros

Solo usuarios del **cliente del JWT**. Vigencia vía `solo_activos` / `solo_inactivos` (ver precedencia arriba). Siempre `es_eliminado=0` en listado.

### Ordenamiento

Fijo server-side por `usuario_id` ASC (no parametrizable).

### Errores HTTP

| Código | Cuándo |
|--------|--------|
| `401` | Token inválido o ausente |
| `403` | Sin permiso `admin.usuario.leer` |
| `422` | Params inválidos (`page`, `limit`, `search`) |
| `500` | Error interno |

### Compatibilidad

Requests sin `solo_inactivos` mantienen default `solo_activos=true` (solo activos no eliminados). Envelope sin cambios.

---

# 1b. POST /api/v1/usuarios/{usuario_id}/reactivate/

**Programa A:** IAM-PA-001  
**Breaking change:** No (endpoint aditivo)

## Contrato vigente

| Campo | Valor |
|-------|-------|
| **Método** | `POST` |
| **Ruta** | `/api/v1/usuarios/{usuario_id}/reactivate/` |
| **Autorización** | JWT + rol Administrador + permiso `admin.usuario.actualizar` |
| **Path params** | `usuario_id` (UUID) |
| **Request body** | — |

### Efecto

Establece `es_eliminado=false` y `es_activo=true` para el usuario del tenant.

### Response 200

**Response model:** `UsuarioRead`

### Errores HTTP

| Código | Cuándo |
|--------|--------|
| `403` | Usuario de otro cliente |
| `404` | Usuario no encontrado |
| `500` | Error interno |

### Compatibilidad

No altera endpoints existentes. Complementa `DELETE /usuarios/{id}/` (eliminación lógica) y `PUT /usuarios/{id}/` (actualización parcial incl. `es_activo`).

---

# 1c. Ciclo de vida de Usuario — Modelo de dominio (IAM-BE-02)

**Breaking change:** No (consolidación de reglas; contratos HTTP sin cambio)

## Estados válidos

| Estado | `es_activo` | `es_eliminado` | Visible en listado GET |
|--------|-------------|----------------|------------------------|
| Activo | `true` | `false` | Sí (default / `solo_activos=true`) |
| Inactivo | `false` | `false` | Sí (`solo_inactivos=true`) |
| Eliminado (soft delete) | `false` | `true` | **No** (excluido siempre del listado) |

Estado **inválido** (nunca debe persistir): `es_activo=true` AND `es_eliminado=true`.

## Acciones oficiales

### Editar — `PUT /api/v1/usuarios/{usuario_id}/`

| Aspecto | Regla |
|---------|-------|
| **Finalidad** | Actualización parcial de datos maestros |
| **Modifica `es_activo`** | Solo si el cliente envía `es_activo` en el body |
| **Modifica `es_eliminado`** | **Nunca** (campo no editable vía PUT) |
| **Precondición** | Usuario con `es_eliminado=false` |

### Desactivar — `PUT /api/v1/usuarios/{usuario_id}/` con `{ "es_activo": false }`

| Aspecto | Regla |
|---------|-------|
| **Finalidad** | Suspensión operativa (usuario inactivo, recuperable) |
| **`es_activo`** | → `false` |
| **`es_eliminado`** | **Sin cambio** (permanece `false`) |
| **Desactivar ≠ Eliminar** | DELETE no debe usarse para desactivar |

**Acceso:** login, refresh y requests autenticados rechazan usuarios con `es_activo=false` (reglas auth existentes).

### Reactivar — `POST /api/v1/usuarios/{usuario_id}/reactivate/`

| Aspecto | Regla |
|---------|-------|
| **Finalidad** | Restaurar usuario inactivo o eliminado lógicamente |
| **`es_activo`** | → `true` |
| **`es_eliminado`** | → `false` |
| **Estado resultante** | Siempre Activo (`true` / `false`); corrige estados inconsistentes previos |

No existe endpoint `/restore/` separado.

### Eliminar — `DELETE /api/v1/usuarios/{usuario_id}/`

| Aspecto | Regla |
|---------|-------|
| **Finalidad** | Soft delete (baja lógica) |
| **`es_activo`** | → `false` |
| **`es_eliminado`** | → `true` |
| **Efectos colaterales** | Desactiva asignaciones `usuario_rol`; invalida permission cache (comportamiento existente) |

**Acceso:** usuario excluido de autenticación (`es_eliminado=0` en queries auth).

## Compatibilidad IAM-BE-02

Rutas, métodos, request/response models y códigos HTTP sin cambio. Solo se documenta y endurece la semántica de negocio en Backend.

---

# 1d. GET /api/v1/auth/sessions/admin/

**Programa A:** IAM-SESSIONS-PA-001  
**Breaking change:** No (cambio aditivo)

## ANTES / DESPUÉS

| Aspecto | ANTES | DESPUÉS |
|---------|-------|---------|
| Shape HTTP 200 (sin `page`) | `AdminSessionRead[]` | **Igual** (array legacy) |
| Shape HTTP 200 (con `page`) | — | **`PaginatedAdminSessionsResponse`** |
| Paginación | Full-load implícito | **`page` + `limit` opt-in** |
| Búsqueda | No | **`search` server-side** |
| Orden | Fijo `last_used_at DESC` | **`sort_by` + `sort_order` (whitelist)** |
| Filtros | No | **`client_type`, `usuario_id`** |
| Campos sesión | Subconjunto | **+ `expires_at`, `user_agent`, datos usuario** |

> `POST /auth/sessions/{token_id}/revoke_admin/` — **sin cambio**.

## Contrato vigente

| Campo | Valor |
|-------|-------|
| **Método** | `GET` |
| **Ruta** | `/api/v1/auth/sessions/admin/` |
| **Autorización** | JWT + rol Administrador |
| **Alcance** | Sesiones activas del **tenant del JWT** (`cliente_id` sesión) |

### Query params

| Param | Tipo | Default | Validación | Descripción |
|-------|------|---------|------------|-------------|
| `page` | `integer` | — | `≥ 1` | Activa envelope paginado |
| `limit` | `integer` | `50` | `1–100` | Solo con `page` |
| `search` | `string` | — | opcional; `1–100` chars | ILIKE en `nombre_usuario`, `nombre`, `apellido`, `ip_address`, `device_name` |
| `sort_by` | `string` | — | whitelist | Ver tabla abajo |
| `sort_order` | `string` | — | `asc` \| `desc` | Solo con `sort_by` |
| `client_type` | `string` | — | `web` \| `mobile` | Filtro tipo cliente |
| `usuario_id` | `UUID` | — | opcional | Filtro por usuario |

**Whitelist `sort_by`:** `created_at`, `last_used_at`, `expires_at`, `ip_address`, `device_name`, `client_type`, `nombre_usuario`, `token_id`

Sin `sort_by` → orden legacy: `last_used_at DESC`, `token_id ASC`.

`sort_by` inválido → **422** (`INVALID_SORT_COLUMN`).

### Modos de respuesta

| Condición | Shape |
|-----------|-------|
| Sin `page` | `AdminSessionRead[]` (legacy) |
| Con `page` | `PaginatedAdminSessionsResponse` |

**Envelope paginado:**

| Campo | Tipo |
|-------|------|
| `sessions` | `AdminSessionRead[]` |
| `total_sesiones` | `integer ≥ 0` |
| `pagina_actual` | `integer ≥ 1` |
| `limit` | `integer 1–100` |
| `total_paginas` | `integer ≥ 0` |

**Objeto `AdminSessionRead`:**

| Campo | Tipo |
|-------|------|
| `token_id` | `UUID` |
| `usuario_id` | `UUID` |
| `cliente_id` | `UUID` |
| `created_at` | `datetime` |
| `last_used_at` | `datetime \| null` |
| `expires_at` | `datetime` |
| `device_name` | `string \| null` |
| `device_id` | `string \| null` |
| `ip_address` | `string \| null` |
| `user_agent` | `string \| null` |
| `client_type` | `string` |
| `nombre_usuario` | `string \| null` |
| `nombre` | `string \| null` |
| `apellido` | `string \| null` |

### Compatibilidad

Request sin `page` (ni params nuevos) → array completo filtrado solo por tenant; orden `last_used_at DESC`. Campos adicionales en cada ítem son **aditivos** (JSON backward compatible).

`limit` sin `page` → **ignorado**.

---

# 2. GET /api/v1/roles/

**Programa A:** IAM-PA-001 (filtros vigencia)  
**Breaking change:** No (cambio aditivo)

## ANTES / DESPUÉS

| Aspecto | ANTES | DESPUÉS |
|---------|-------|---------|
| Query params | `page`, `limit`, `search` | **+ `solo_activos`, `solo_inactivos`** |
| Listado default | Solo roles activos (implícito en SQL) | **`solo_activos=true` explícito (igual comportamiento default)** |
| Listado inactivos / todos | No disponible | **`solo_inactivos=true` o ambos false** |

## Contrato vigente

| Campo | Valor |
|-------|-------|
| **Método** | `GET` |
| **Ruta** | `/api/v1/roles/` |
| **Autorización** | JWT + rol Administrador + permiso `admin.rol.leer` |
| **Path params** | — |
| **Request body** | — |

### Query params

| Param | Tipo | Default | Validación | Descripción |
|-------|------|---------|------------|-------------|
| `page` | `integer` | `1` | `≥ 1` | Número de página |
| `limit` | `integer` | `10` | `1–100` | Roles por página |
| `search` | `string` | — | opcional | Búsqueda en nombre o descripción |
| `solo_activos` | `boolean` | `true` | — | Solo roles activos |
| `solo_inactivos` | `boolean` | `false` | — | Solo roles inactivos; precedencia sobre `solo_activos` |

**Precedencia filtro vigencia (PA-004):**

```
si solo_inactivos = true  →  es_activo = 0
si no, si solo_activos = true  →  es_activo = 1
si no  →  sin filtro de vigencia (activos + inactivos)
```

### Response 200

**Response model:** `PaginatedRolResponse` (shape en raíz)

| Campo envelope | Tipo | Descripción |
|----------------|------|-------------|
| `roles` | `RolRead[]` | Página actual |
| `total_roles` | `integer ≥ 0` | Total post-filtro |
| `pagina_actual` | `integer ≥ 1` | Página devuelta |
| `total_paginas` | `integer ≥ 0` | Total de páginas |

**Objeto de negocio `RolRead`** (campos principales):

| Campo | Tipo |
|-------|------|
| `rol_id` | `UUID` |
| `cliente_id` | `UUID \| null` |
| `codigo_rol` | `string \| null` |
| `nombre` | `string` |
| `descripcion` | `string \| null` |
| `es_activo` | `boolean` |
| `fecha_creacion` | `datetime` |
| `es_eliminado` | `boolean` |
| `asignacion_empresa_id` | `UUID \| null` |

### Paginación

Modelo **`page` + `limit`**.

### Búsqueda

Param **`search`** — server-side opcional.

### Filtros

Roles del tenant de sesión + roles de sistema. Vigencia vía `solo_activos` / `solo_inactivos`.

**Reactivación de roles:** `POST /api/v1/roles/{rol_id}/reactivate/` (existente, sin cambio IAM-PA-001).

### Ordenamiento

Fijo server-side (no parametrizable).

### Errores HTTP

| Código | Cuándo |
|--------|--------|
| `400` | Contexto de cliente no disponible |
| `401` / `403` | Auth / permiso |
| `422` | Params inválidos |
| `500` | Error interno |

---

# 3. GET /api/v1/permisos-catalogo

**Programa A:** PA-002 (cerrado sin implementación Backend)  
**Breaking change:** No

## ANTES / DESPUÉS

Sin cambios. Sigue devolviendo array plano full-load.

## Contrato vigente

| Campo | Valor |
|-------|-------|
| **Método** | `GET` |
| **Ruta** | `/api/v1/permisos-catalogo` o `/api/v1/permisos-catalogo/` |
| **Autorización** | JWT + permiso `admin.rol.leer` |
| **Path params** | — |
| **Query params** | — |
| **Request body** | — |

### Response 200

**Response model:** `PermisoCatalogoRead[]` (**array plano**, sin envelope)

| Campo objeto | Tipo |
|--------------|------|
| `permiso_id` | `UUID` |
| `codigo` | `string` |
| `nombre` | `string \| null` |
| `descripcion` | `string \| null` |
| `recurso` | `string \| null` |
| `accion` | `string \| null` |
| `modulo_id` | `UUID \| null` |
| `es_activo` | `boolean` |

### Paginación

**No disponible.** Full-load filtrado por módulos habilitados del tenant.

### Búsqueda

**No disponible** server-side. Si el Frontend necesita acotar, debe filtrar en cliente (deuda conocida PA-002).

### Errores HTTP

| Código | Cuándo |
|--------|--------|
| `401` / `403` | Auth / permiso |
| `500` | Error interno |

---

# 4. GET /api/v1/modulos-v2/

**Programa A:** PA-003  
**Breaking change:** No (cambio aditivo)

## ANTES / DESPUÉS

| Aspecto | ANTES | DESPUÉS |
|---------|-------|---------|
| Shape HTTP 200 | `PaginatedModuloResponse` | **Igual** |
| Query params | `skip`, `limit`, `solo_activos`, `categoria` | **+ `buscar`** |
| Búsqueda server-side | No disponible | **`buscar` disponible** |

## Contrato vigente

| Campo | Valor |
|-------|-------|
| **Método** | `GET` |
| **Ruta** | `/api/v1/modulos-v2/` |
| **Autorización** | JWT + permiso `modulos.menu.leer` |
| **Path params** | — |
| **Request body** | — |

### Query params

| Param | Tipo | Default | Validación | Descripción |
|-------|------|---------|------------|-------------|
| `skip` | `integer` | `0` | `≥ 0` | Offset |
| `limit` | `integer` | `100` | `1–1000` | Tamaño de página |
| `solo_activos` | `boolean` | `false` | — | `true` = solo activos; `false` = todos |
| `categoria` | `string` | — | opcional | Filtro exacto por categoría |
| `buscar` | `string` | — | opcional; `max_length=100` | Búsqueda en `codigo`, `nombre`, `descripcion` |

### Response 200

**Response model:** `PaginatedModuloResponse`

**Envelope:** Sí — wrapper con metadata anidada.

```json
{
  "success": true,
  "message": "Catálogo de módulos recuperado exitosamente.",
  "data": [ /* ModuloRead[] */ ],
  "pagination": {
    "total": 0,
    "skip": 0,
    "limit": 100,
    "total_pages": 0,
    "current_page": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

| Campo envelope | Tipo | Descripción |
|----------------|------|-------------|
| `success` | `boolean` | Siempre `true` en 200 |
| `message` | `string` | Mensaje descriptivo |
| `data` | `ModuloRead[]` | Página actual |
| `pagination.total` | `integer` | Total post-filtro — **usar para paginación** |
| `pagination.skip` | `integer` | Offset aplicado |
| `pagination.limit` | `integer` | Límite aplicado |
| `pagination.total_pages` | `integer` | Total páginas |
| `pagination.current_page` | `integer` | Página actual |
| `pagination.has_next` | `boolean` | Hay página siguiente |
| `pagination.has_prev` | `boolean` | Hay página anterior |

**Objeto de negocio `ModuloRead`** (campos principales):

| Campo | Tipo |
|-------|------|
| `modulo_id` | `UUID` |
| `codigo` | `string` |
| `nombre` | `string` |
| `descripcion` | `string \| null` |
| `categoria` | `string` |
| `es_core` | `boolean` |
| `requiere_licencia` | `boolean` |
| `orden` | `integer` |
| `es_activo` | `boolean` |
| `fecha_creacion` | `datetime` |
| `fecha_actualizacion` | `datetime \| null` |

### Paginación

Modelo **`skip` + `limit`**. Usar `pagination.total` (no contar `data.length`).

### Búsqueda

Param **`buscar`** — server-side, case-insensitive, parcial (`LIKE`).  
Si se omite o es solo espacios → sin filtro textual.  
Caracteres `%` y `_` se interpretan como metacaracteres SQL LIKE.

### Ordenamiento

Fijo server-side: `orden ASC`, `nombre ASC`.

### Errores HTTP

| Código | Cuándo |
|--------|--------|
| `401` / `403` | Auth / permiso |
| `422` | Params inválidos |
| `500` | Error interno |

---

# 5. GET /api/v1/clientes/

**Programa A:** PA-004  
**Breaking change:** No (cambio aditivo)

## ANTES / DESPUÉS

| Aspecto | ANTES | DESPUÉS |
|---------|-------|---------|
| Shape HTTP 200 | `PaginatedClienteResponse` | **Igual** |
| Query params | `skip`, `limit`, `solo_activos`, `buscar` | **+ `solo_inactivos`** |
| Filtro solo inactivos | No disponible (`solo_activos=false` devolvía todos) | **`solo_inactivos=true` → `es_activo=0`** |

## Contrato vigente

| Campo | Valor |
|-------|-------|
| **Método** | `GET` |
| **Ruta** | `/api/v1/clientes/` |
| **Autorización** | JWT + Super Admin + permiso `tenant.cliente.leer` |
| **Path params** | — |
| **Request body** | — |

### Query params

| Param | Tipo | Default | Validación | Descripción |
|-------|------|---------|------------|-------------|
| `skip` | `integer` | `0` | `≥ 0` | Offset |
| `limit` | `integer` | `100` | `1–1000` | Tamaño de página |
| `solo_activos` | `boolean` | `true` | — | Solo clientes activos |
| `solo_inactivos` | `boolean` | `false` | — | Solo clientes inactivos (`es_activo=0`) |
| `buscar` | `string` | — | opcional | Búsqueda en razón social, nombre comercial, código, subdominio |

**Precedencia filtro vigencia:**

```
si solo_inactivos = true  →  es_activo = 0
si no, si solo_activos = true  →  es_activo = 1
si no  →  sin filtro de vigencia (activos + inactivos + suspendidos)
```

### Response 200

**Response model:** `PaginatedClienteResponse`

| Campo envelope | Tipo | Descripción |
|----------------|------|-------------|
| `clientes` | `ClienteRead[]` | Página actual |
| `total_clientes` | `integer ≥ 0` | Total post-filtro |
| `pagina_actual` | `integer ≥ 1` | `(skip // limit) + 1` |
| `total_paginas` | `integer ≥ 0` | `ceil(total_clientes / limit)` |
| `items_por_pagina` | `integer ≥ 1` | Valor de `limit` aplicado |

**Objeto de negocio `ClienteRead`** (campos principales):

| Campo | Tipo |
|-------|------|
| `cliente_id` | `UUID` |
| `codigo_cliente` | `string` |
| `subdominio` | `string` |
| `razon_social` | `string` |
| `nombre_comercial` | `string \| null` |
| `ruc` | `string \| null` |
| `plan_suscripcion` | `string` |
| `estado_suscripcion` | `string` |
| `es_activo` | `boolean` |
| `fecha_creacion` | `datetime` |
| `fecha_actualizacion` | `datetime \| null` |

### Paginación

Modelo **`skip` + `limit`**. Usar **`total_clientes`** para calcular páginas.

### Búsqueda

Param **`buscar`** — server-side, parcial.

### Ordenamiento

Fijo server-side (no parametrizable).

### Errores HTTP

| Código | Cuándo |
|--------|--------|
| `403` | No es Super Admin |
| `422` | Params inválidos |
| `500` | Error interno |

### Compatibilidad

Requests existentes sin `solo_inactivos` mantienen comportamiento previo (`solo_activos=true` default).

---

# 6. GET /api/v1/catalogos-globales/monedas

**Programa A:** PA-005  
**Breaking change:** **Sí**

## ANTES / DESPUÉS

| Aspecto | ANTES | DESPUÉS |
|---------|-------|---------|
| Shape HTTP 200 | `CatMonedaRead[]` (array plano) | **`PaginatedCatMonedaResponse`** (envelope) |
| Paginación | Full-load | **`skip` + `limit`** (default `0`/`100`) |
| Búsqueda | No disponible | **`buscar`** server-side |
| Total | No disponible | **`total_monedas`** |

## Contrato vigente

| Campo | Valor |
|-------|-------|
| **Método** | `GET` |
| **Ruta** | `/api/v1/catalogos-globales/monedas` |
| **Autorización** | JWT + Super Admin |
| **Path params** | — |
| **Request body** | — |

### Query params

| Param | Tipo | Default | Validación | Descripción |
|-------|------|---------|------------|-------------|
| `skip` | `integer` | `0` | `≥ 0` | Offset |
| `limit` | `integer` | `100` | `1–1000` | Tamaño de página |
| `solo_activos` | `boolean` | `true` | — | Ver regla vigencia abajo |
| `buscar` | `string` | — | opcional; `max_length=100` | Búsqueda en `codigo`, `nombre`, `simbolo` |
| `cliente_id` | `UUID` | — | opcional | Target tenant (Super Admin) |

**Regla `solo_activos`:**

- `true` (default) → solo registros activos
- `false` → activos **e** inactivos (sin filtro de vigencia)

### Response 200

**Response model:** `PaginatedCatMonedaResponse`

| Campo envelope | Tipo |
|----------------|------|
| `monedas` | `CatMonedaRead[]` |
| `total_monedas` | `integer ≥ 0` |
| `pagina_actual` | `integer ≥ 1` |
| `total_paginas` | `integer ≥ 0` |
| `items_por_pagina` | `integer ≥ 1` |

**Objeto `CatMonedaRead`:**

| Campo | Tipo |
|-------|------|
| `moneda_id` | `UUID` |
| `codigo` | `string` (3 chars) |
| `nombre` | `string` |
| `simbolo` | `string` |
| `decimales` | `integer` |
| `es_activo` | `boolean` |

### Paginación

Siempre activa. Sin params explícitos → máximo **100** registros por request.

### Búsqueda

Param **`buscar`** — server-side, case-insensitive, OR sobre whitelist.

### Ordenamiento

Fijo: `codigo ASC`.

### Errores HTTP

| Código | Cuándo |
|--------|--------|
| `400` | `cliente_id` requerido no resuelto |
| `403` | No es Super Admin |
| `422` | Params inválidos |
| `500` | Error interno |

---

# 7. GET /api/v1/catalogos-globales/paises

**Programa A:** PA-005  
**Breaking change:** **Sí**

## ANTES / DESPUÉS

| Aspecto | ANTES | DESPUÉS |
|---------|-------|---------|
| Shape HTTP 200 | `CatPaisRead[]` | **`PaginatedCatPaisResponse`** |
| Paginación | Full-load | **`skip` + `limit`** |
| Búsqueda | No | **`buscar`** |

## Contrato vigente

| Campo | Valor |
|-------|-------|
| **Método** | `GET` |
| **Ruta** | `/api/v1/catalogos-globales/paises` |
| **Autorización** | JWT + Super Admin |

### Query params

Igual que monedas (§6): `skip`, `limit`, `solo_activos`, `buscar`, `cliente_id`.

### Response 200

**Response model:** `PaginatedCatPaisResponse`

| Campo envelope | Tipo |
|----------------|------|
| `paises` | `CatPaisRead[]` |
| `total_paises` | `integer ≥ 0` |
| `pagina_actual` | `integer ≥ 1` |
| `total_paginas` | `integer ≥ 0` |
| `items_por_pagina` | `integer ≥ 1` |

**Objeto `CatPaisRead`:**

| Campo | Tipo |
|-------|------|
| `pais_id` | `UUID` |
| `codigo_iso2` | `string` (2) |
| `codigo_iso3` | `string` (3) |
| `nombre` | `string` |
| `es_activo` | `boolean` |

### Búsqueda whitelist

`codigo_iso2`, `codigo_iso3`, `nombre`.

### Ordenamiento

Fijo: `nombre ASC`.

---

# 8. GET /api/v1/catalogos-globales/departamentos

**Programa A:** PA-005  
**Breaking change:** **Sí**

## ANTES / DESPUÉS

| Aspecto | ANTES | DESPUÉS |
|---------|-------|---------|
| Shape HTTP 200 | `CatDepartamentoRead[]` | **`PaginatedCatDepartamentoResponse`** |
| Paginación | Full-load | **`skip` + `limit`** |
| Búsqueda | No | **`buscar`** |

## Contrato vigente

| Campo | Valor |
|-------|-------|
| **Método** | `GET` |
| **Ruta** | `/api/v1/catalogos-globales/departamentos` |
| **Autorización** | JWT + Super Admin |

### Query params

| Param | Tipo | Default | Descripción |
|-------|------|---------|-------------|
| `skip` | `integer` | `0` | Offset |
| `limit` | `integer` | `100` | `1–1000` |
| `solo_activos` | `boolean` | `true` | Filtro vigencia |
| `pais_id` | `UUID` | — | Filtro exacto por país |
| `buscar` | `string` | — | Búsqueda en `codigo`, `nombre` |
| `cliente_id` | `UUID` | — | Target tenant |

### Response 200

**Response model:** `PaginatedCatDepartamentoResponse`

| Campo envelope | Tipo |
|----------------|------|
| `departamentos` | `CatDepartamentoRead[]` |
| `total_departamentos` | `integer ≥ 0` |
| `pagina_actual` | `integer ≥ 1` |
| `total_paginas` | `integer ≥ 0` |
| `items_por_pagina` | `integer ≥ 1` |

**Objeto `CatDepartamentoRead`:**

| Campo | Tipo |
|-------|------|
| `departamento_id` | `UUID` |
| `pais_id` | `UUID` |
| `codigo` | `string` |
| `nombre` | `string` |
| `es_activo` | `boolean` |

### Ordenamiento

Fijo: `nombre ASC`.

---

# 9. GET /api/v1/catalogos-globales/provincias

**Programa A:** PA-005  
**Breaking change:** **Sí**

## ANTES / DESPUÉS

| Aspecto | ANTES | DESPUÉS |
|---------|-------|---------|
| Shape HTTP 200 | `CatProvinciaRead[]` | **`PaginatedCatProvinciaResponse`** |
| Paginación | Full-load | **`skip` + `limit`** |
| Búsqueda | No | **`buscar`** |

## Contrato vigente

| Campo | Valor |
|-------|-------|
| **Método** | `GET` |
| **Ruta** | `/api/v1/catalogos-globales/provincias` |
| **Autorización** | JWT + Super Admin |

### Query params

| Param | Tipo | Default | Descripción |
|-------|------|---------|-------------|
| `skip` | `integer` | `0` | Offset |
| `limit` | `integer` | `100` | `1–1000` |
| `solo_activos` | `boolean` | `true` | Filtro vigencia |
| `departamento_id` | `UUID` | — | Filtro exacto por departamento |
| `buscar` | `string` | — | Búsqueda en `codigo`, `nombre` |
| `cliente_id` | `UUID` | — | Target tenant |

### Response 200

**Response model:** `PaginatedCatProvinciaResponse`

| Campo envelope | Tipo |
|----------------|------|
| `provincias` | `CatProvinciaRead[]` |
| `total_provincias` | `integer ≥ 0` |
| `pagina_actual` | `integer ≥ 1` |
| `total_paginas` | `integer ≥ 0` |
| `items_por_pagina` | `integer ≥ 1` |

**Objeto `CatProvinciaRead`:**

| Campo | Tipo |
|-------|------|
| `provincia_id` | `UUID` |
| `departamento_id` | `UUID` |
| `codigo` | `string` |
| `nombre` | `string` |
| `es_activo` | `boolean` |

### Ordenamiento

Fijo: `nombre ASC`.

---

# 10. GET /api/v1/catalogos-globales/distritos

**Programa A:** PA-005  
**Breaking change:** **Sí**

## ANTES / DESPUÉS

| Aspecto | ANTES | DESPUÉS |
|---------|-------|---------|
| Shape HTTP 200 | `CatDistritoRead[]` | **`PaginatedCatDistritoResponse`** |
| Paginación | Full-load (~1800+ registros) | **`skip` + `limit`** (default 100) |
| Búsqueda | No | **`buscar`** |

## Contrato vigente

| Campo | Valor |
|-------|-------|
| **Método** | `GET` |
| **Ruta** | `/api/v1/catalogos-globales/distritos` |
| **Autorización** | JWT + Super Admin |

### Query params

| Param | Tipo | Default | Validación | Descripción |
|-------|------|---------|------------|-------------|
| `skip` | `integer` | `0` | `≥ 0` | Offset |
| `limit` | `integer` | `100` | `1–1000` | Tamaño de página |
| `solo_activos` | `boolean` | `true` | — | Filtro vigencia |
| `provincia_id` | `UUID` | — | opcional | Filtro exacto |
| `ubigeo` | `string` | — | opcional; `min_length=1`, `max_length=6` | Filtro exacto por ubigeo |
| `buscar` | `string` | — | opcional; `max_length=100` | Búsqueda en `codigo`, `nombre`, `ubigeo` |
| `cliente_id` | `UUID` | — | opcional | Target tenant |

> `ubigeo` (exacto) y `buscar` (parcial sobre ubigeo) pueden combinarse — ambos aplican por AND.

### Response 200

**Response model:** `PaginatedCatDistritoResponse`

| Campo envelope | Tipo |
|----------------|------|
| `distritos` | `CatDistritoRead[]` |
| `total_distritos` | `integer ≥ 0` |
| `pagina_actual` | `integer ≥ 1` |
| `total_paginas` | `integer ≥ 0` |
| `items_por_pagina` | `integer ≥ 1` |

**Objeto `CatDistritoRead`:**

| Campo | Tipo |
|-------|------|
| `distrito_id` | `UUID` |
| `provincia_id` | `UUID` |
| `codigo` | `string` |
| `nombre` | `string` |
| `ubigeo` | `string` (6) |
| `es_activo` | `boolean` |

### Ordenamiento

Fijo: `nombre ASC`.

---

# Patrones de envelope — referencia rápida

El Frontend debe identificar **tres familias** de respuesta paginada en Platform Admin:

## Familia A — Envelope plano (raíz)

Usado por: **usuarios**, **roles**, **clientes**, **catálogos globales**.

```
{
  "{entidad}": [...],
  "total_{entidad}": N,
  "pagina_actual": P,
  "total_paginas": T,
  "items_por_pagina": L   // solo clientes y catálogos globales
}
```

| Endpoint | Array | Total |
|----------|-------|-------|
| `/usuarios/` | `usuarios` | `total_usuarios` |
| `/roles/` | `roles` | `total_roles` |
| `/clientes/` | `clientes` | `total_clientes` |
| `/catalogos-globales/monedas` | `monedas` | `total_monedas` |
| `/catalogos-globales/paises` | `paises` | `total_paises` |
| `/catalogos-globales/departamentos` | `departamentos` | `total_departamentos` |
| `/catalogos-globales/provincias` | `provincias` | `total_provincias` |
| `/catalogos-globales/distritos` | `distritos` | `total_distritos` |

## Familia B — Envelope wrapper (modulos-v2)

```
{
  "success": true,
  "message": "...",
  "data": [...],
  "pagination": { "total", "skip", "limit", "total_pages", "current_page", "has_next", "has_prev" }
}
```

## Familia C — Array plano (sin paginación)

Usado por: **`/permisos-catalogo`** → `PermisoCatalogoRead[]`

---

# Modelos de paginación

| Endpoint | Modelo | Params |
|----------|--------|--------|
| `/usuarios/` | `page` + `limit` | base 1 |
| `/roles/` | `page` + `limit` | base 1 |
| `/auth/sessions/admin/` | `page` + `limit` (opt-in) | base 1 |
| `/modulos-v2/` | `skip` + `limit` | offset 0 |
| `/clientes/` | `skip` + `limit` | offset 0 |
| `/catalogos-globales/*` | `skip` + `limit` | offset 0 |

---

# Contratos eliminados

Los siguientes contratos **ya no deben utilizarse** por el Frontend:

| Contrato obsoleto | Reemplazo vigente |
|-------------------|-------------------|
| `GET /catalogos-globales/monedas` → `CatMonedaRead[]` | `PaginatedCatMonedaResponse` |
| `GET /catalogos-globales/paises` → `CatPaisRead[]` | `PaginatedCatPaisResponse` |
| `GET /catalogos-globales/departamentos` → `CatDepartamentoRead[]` | `PaginatedCatDepartamentoResponse` |
| `GET /catalogos-globales/provincias` → `CatProvinciaRead[]` | `PaginatedCatProvinciaResponse` |
| `GET /catalogos-globales/distritos` → `CatDistritoRead[]` | `PaginatedCatDistritoResponse` |
| Asumir full-load de catálogos globales en un solo request | Paginar con `skip`/`limit`; usar `total_*` |
| Usar `solo_activos=false` en `/clientes/` para listar solo inactivos | Usar **`solo_inactivos=true`** |
| Filtrar módulos solo en cliente cuando se necesita búsqueda textual | Usar param **`buscar`** en `/modulos-v2/` |
| Parsear respuesta 200 de catálogos globales como array JSON en raíz | Parsear envelope con campo `{entidad}[]` + `total_{entidad}` |

> **Nota:** `GET /api/v1/catalogos/*` (módulo tenant ERP) **no forma parte del Programa A** y sigue devolviendo arrays planos full-load. No confundir con `/catalogos-globales/*`.

---

# Contratos vigentes

**Este documento (`BACKEND_PLATFORM_API_CONTRACT_V2.md`) reemplaza cualquier contrato anterior del Programa A**, incluyendo:

- Suposiciones de array plano en catálogos globales Super Admin
- Documentación informal o auditorías previas al cierre PA-005
- Contratos Frontend basados en full-load para `/catalogos-globales/*`

La referencia canónica Backend → Frontend para listados administrativos del Programa A es **exclusivamente este documento V2**.

---

# Reglas obligatorias para Frontend

1. **No asumir arrays cuando exista envelope.** Verificar el shape antes de iterar (`Array.isArray(response)` fallará en catálogos globales post-PA-005).

2. **Utilizar siempre `total_*` (o `pagination.total` en modulos-v2) para paginación.** No inferir totales desde `items.length`.

3. **Utilizar `skip` y `limit`** en clientes, modulos-v2 y catálogos globales. Utilizar **`page` y `limit`** en usuarios y roles.

4. **Utilizar `buscar`** (o `search` en usuarios/roles) para búsquedas server-side cuando el endpoint lo exponga. No replicar filtros textuales en cliente si el Backend ya los soporta.

5. **No realizar paginación client-side** cuando el endpoint expone paginación server-side (catálogos globales, clientes, modulos-v2, usuarios, roles).

6. **Respetar los defaults Backend:**
   - Catálogos globales: `limit=100` → un request sin params devuelve como máximo 100 registros
   - Clientes: `solo_activos=true` por default
   - Modulos-v2: `solo_activos=false` por default (devuelve todos)

7. **No utilizar contratos obsoletos** listados en la sección «Contratos eliminados».

8. **Breaking change PA-005:** desplegar Frontend alineado al envelope **antes o simultáneamente** al Backend PA-005 en producción.

9. **Filtro clientes inactivos:** usar `solo_inactivos=true`; no interpretar `solo_activos=false` como «solo inactivos».

10. **Filtro IAM usuarios/roles inactivos:** mismo patrón PA-004 — `solo_inactivos=true` para tab inactivos; `solo_activos=false` y `solo_inactivos=false` para ver todos (usuarios: siempre excluye `es_eliminado=1`).

11. **Reactivación usuarios:** `POST /usuarios/{id}/reactivate/` (usuarios eliminados o inactivos). **Reactivación roles:** `POST /roles/{id}/reactivate/`.

12. **Ciclo de vida usuarios (IAM-BE-02):** Desactivar = `PUT` con `es_activo=false` (no toca `es_eliminado`). Eliminar = `DELETE` (soft delete). **Desactivar ≠ Eliminar.**

13. **Sesiones activas admin:** `GET /auth/sessions/admin/` — sin `page` → array legacy; con `page` → envelope `PaginatedAdminSessionsResponse`. Revocar: `POST /auth/sessions/{token_id}/revoke_admin/` (sin cambio).

14. **Identificar familia de envelope** (plano, wrapper, array) por endpoint — no unificar parsers sin verificar.

15. **Catálogos globales jerárquicos:** combinar filtros de scope (`pais_id`, `departamento_id`, `provincia_id`, `ubigeo`) con `buscar` y paginación en la misma request.

16. **Metadatos de paginación:** usar `pagina_actual` y `total_paginas` del envelope cuando estén disponibles; no recalcular si el Backend ya los entrega.

---

**Fin del documento — BACKEND_PLATFORM_API_CONTRACT_V2**
