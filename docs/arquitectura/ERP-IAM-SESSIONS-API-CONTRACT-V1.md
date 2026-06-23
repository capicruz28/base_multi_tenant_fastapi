# ERP-IAM-SESSIONS-API-CONTRACT-V1

**Versión:** 1.0.0 (RC1)  
**Fecha:** 2026-06-21  
**Ticket:** ERP-IAM-SESSIONS-BE-RC1-STABILIZATION  
**Audiencia:** Proyecto Frontend (consumo exclusivo vía OpenAPI)  
**Estado Backend:** Congelado — no se prevén cambios funcionales en este módulo hasta V2.

---

## 1. Objetivo

El módulo **Sesiones Activas** permite a un usuario autenticado:

- Ver sus sesiones activas (refresh tokens vigentes) con información de dispositivo enriquecida.
- Identificar cuál es la sesión actual del request (`is_current`).
- Cerrar remotamente una sesión propia por `token_id` (self-revoke).

Permite a un administrador del tenant:

- Listar todas las sesiones activas del tenant (modo legacy o paginado).
- Revocar cualquier sesión activa por `token_id`.

El Backend **no** expone lógica de UI. El Frontend consume únicamente los DTOs documentados aquí y en OpenAPI (`/openapi.json`).

**Identificador estable de sesión en V1:** `token_id` (UUID, PK de `refresh_tokens`).

---

## 2. Endpoints

Base URL API: `/api/v1/auth`

### 2.1 GET `/sessions/`

| Atributo | Valor |
|----------|-------|
| **Autenticación** | Bearer JWT (access token válido) |
| **Autorización** | Usuario autenticado (PATH A) |
| **Response** | `200` → `UserSessionRead[]` |
| **Errores** | `401` token inválido/expirado; `500` error interno |

Lista sesiones activas del usuario autenticado. Orden: `last_used_at DESC`.

---

### 2.2 GET `/sessions/admin/`

| Atributo | Valor |
|----------|-------|
| **Autenticación** | Bearer JWT |
| **Autorización** | Rol Administrador + permisos IAM admin |
| **Response** | `200` → `AdminSessionRead[]` **o** `PaginatedAdminSessionsResponse` |
| **Errores** | `401`, `403`, `422` (`INVALID_SORT_COLUMN`), `500` |

#### Query params

| Param | Tipo | Default | Descripción |
|-------|------|---------|-------------|
| `page` | `integer ≥ 1` | — | Si presente → envelope paginado |
| `limit` | `integer 1–100` | `50` | Solo con `page` |
| `search` | `string` | — | ILIKE en usuario, IP, device_name |
| `sort_by` | `string` | — | Whitelist (ver §7) |
| `sort_order` | `asc` \| `desc` | — | Solo con `sort_by` |
| `client_type` | `web` \| `mobile` | — | Filtro |
| `usuario_id` | `UUID` | — | Filtro por usuario |

**Modos:**

- Sin `page` → array legacy completo (`AdminSessionRead[]`).
- Con `page` → `PaginatedAdminSessionsResponse` (dual envelope).

---

### 2.3 POST `/sessions/{token_id}/revoke/`

| Atributo | Valor |
|----------|-------|
| **Autorización** | Usuario autenticado — solo sesiones propias |
| **Path** | `token_id` — UUID del refresh token |
| **Response** | `200` → `{ "message": string, "token_id": string }` |
| **Errores** | `404` sesión inexistente o no pertenece al usuario; `401` |

**Semántica idempotente (RC1):**

- Primera revocación activa → `200` + mensaje de éxito + audit interno.
- Segunda llamada sobre sesión ya cerrada (revocada/expirada) del mismo usuario → `200` + mensaje "ya estaba cerrada".
- Token de otro usuario o inexistente en tenant → `404`.

---

### 2.4 POST `/sessions/{token_id}/revoke_admin/`

| Atributo | Valor |
|----------|-------|
| **Autorización** | Administrador |
| **Response** | `200` → `{ "message": string }` |
| **Errores** | `404` token no activo; `403`; `500` |

Sin cambios en RC1. No idempotente: sesión ya revocada → `404`.

Audit aditivo interno: `session_admin_revoked` (no expuesto en response).

---

## 3. DTO `UserSessionRead`

| Campo | Tipo | Descripción | Semántica |
|-------|------|-------------|-----------|
| `token_id` | `UUID` | Identificador de sesión | PK refresh token vigente |
| `usuario_id` | `UUID` | Propietario | Usuario de la sesión |
| `cliente_id` | `UUID` | Tenant | Siempre filtrado por tenant |
| `empresa_id` | `UUID \| null` | Empresa activa | Contexto ERP de la sesión |
| `empresa_nombre` | `string \| null` | Nombre empresa | JOIN lectura |
| `issued_at` | `datetime` | Emisión refresh vigente | Puede cambiar tras rotación |
| `created_at` | `datetime` | **Legacy alias** | Mismo valor que `issued_at` |
| `last_refresh_at` | `datetime \| null` | Último refresh | No es actividad API |
| `last_used_at` | `datetime \| null` | **Legacy alias** | Mismo valor que `last_refresh_at` |
| `expires_at` | `datetime` | Expiración refresh | |
| `is_current` | `boolean` | Sesión del request | `true` si coincide con refresh del cookie/header |
| `status` | `"active" \| "expiring_soon"` | Estado derivado | `expiring_soon` si expira en < 24 h |
| `duration_seconds` | `integer ≥ 0` | Duración | Segundos desde `issued_at` hasta ahora |
| `device` | `SessionDeviceRead` | Dispositivo enriquecido | Ver §5 |
| `client_type` | `string` | `web` \| `mobile` | Columna BD |
| `ip_address` | `string \| null` | **Legacy alias** | Mismo valor que `device.ip_address` |
| `device_name` | `string \| null` | **Legacy** | Columna BD (puede ser null) |
| `device_id` | `string \| null` | **Legacy** | Columna BD (puede ser null) |

---

## 4. DTO `AdminSessionRead`

Extiende todos los campos de `UserSessionRead` más:

| Campo | Tipo | Descripción | Semántica |
|-------|------|-------------|-----------|
| `nombre_usuario` | `string \| null` | Login | Identificación admin |
| `nombre` | `string \| null` | Nombre | |
| `apellido` | `string \| null` | Apellido | |
| `user_agent` | `string \| null` | UA crudo | Solo admin — diagnóstico; no mostrar en UI usuario |

---

## 5. DTO `SessionDeviceRead`

| Campo | Tipo | Descripción | Semántica |
|-------|------|-------------|-----------|
| `client_type` | `string` | Tipo cliente | `web` \| `mobile` |
| `browser` | `string` | Navegador/cliente | Derivado UA; ej. Chrome, Firefox |
| `browser_version` | `string \| null` | Versión | Puede ser null |
| `os` | `string` | Sistema operativo | ej. Windows, Android |
| `platform` | `string` | Plataforma | `desktop`, `mobile`, `tablet`, `unknown` |
| `device_label` | `string` | Etiqueta display | Texto listo para UI; preferir sobre `device_name` |
| `ip_address` | `string \| null` | IP conocida | Última IP registrada en refresh |
| `device_id` | `string \| null` | ID dispositivo | Puede ser null (V2 persistirá) |

---

## 6. Alias legacy

| Campo legacy | Campo canónico / equivalente | Motivo | Deprecación prevista |
|--------------|------------------------------|--------|----------------------|
| `created_at` | `issued_at` | Contrato admin/user previo | Mantener en V1; evaluar V2 |
| `last_used_at` | `last_refresh_at` | Nombre histórico en BD/API | Mantener en V1 |
| `ip_address` (raíz) | `device.ip_address` | Listados legacy exponían IP en raíz | Mantener ambos RC1; FE nuevo usa `device.ip_address` |
| `device_name` | `device.device_label` | Columna BD a menudo vacía | FE migra a `device_label` |
| `device_id` (raíz) | `device.device_id` | Duplicado raíz/objeto | Mantener V1 |
| `sessions` | `items` | Envelope paginado admin | Mantener ambos |
| `total_sesiones` | `total` | Envelope paginado admin | Mantener ambos |

**Nota RC1 (QA-A01):** `ip_address` en raíz fue restaurado como alias explícito. No eliminar en consumidores legacy.

**Campo no restaurado en V1:** `uso_count` en listado usuario (no consumido en contrato documentado; fuera de alcance RC1).

---

## 7. Reglas de compatibilidad

### El Frontend puede asumir

- Respuestas JSON son **superset** del contrato anterior: campos nuevos son aditivos.
- `token_id` es estable mientras la sesión esté activa; cambia tras rotación de refresh (nueva fila).
- `is_current` es calculado server-side comparando refresh del request.
- `device.device_label` es el texto recomendado para UI.
- Self-revoke es idempotente: reintentos seguros → `200`.
- Admin paginado expone **simultáneamente** `items`/`total` y `sessions`/`total_sesiones` con mismos datos.

### El Frontend nunca debe asumir

- Que `issued_at` sea el inicio de sesión del login original (cambia con rotación).
- Que `last_refresh_at` refleje clicks o requests API recientes.
- Que `device_name` esté poblado.
- Que exista `session_id`, `session_started_at` o `last_activity_at` (V2).
- Idempotencia en `revoke_admin` (solo en self-revoke).
- Orden estable sin `sort_by` en admin paginado más allá del default documentado.

### Whitelist `sort_by` (admin)

`created_at`, `last_used_at`, `expires_at`, `ip_address`, `device_name`, `client_type`, `nombre_usuario`, `token_id`

Inválido → HTTP `422`, código `INVALID_SORT_COLUMN`.

---

## 8. Ejemplos JSON

### 8.1 `UserSessionRead`

```json
{
  "token_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "usuario_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "cliente_id": "e4c8e906-0e64-4f4e-a04d-8daee57dc7f8",
  "empresa_id": "550e8400-e29b-41d4-a716-446655440000",
  "empresa_nombre": "ACME SA",
  "issued_at": "2026-06-18T10:00:00",
  "created_at": "2026-06-18T10:00:00",
  "last_refresh_at": "2026-06-21T08:30:00",
  "last_used_at": "2026-06-21T08:30:00",
  "expires_at": "2026-06-25T10:00:00",
  "is_current": true,
  "status": "active",
  "duration_seconds": 259200,
  "device": {
    "client_type": "web",
    "browser": "Chrome",
    "browser_version": "120.0.0.0",
    "os": "Windows",
    "platform": "desktop",
    "device_label": "Chrome 120.0.0.0 en Windows",
    "ip_address": "192.168.1.10",
    "device_id": null
  },
  "client_type": "web",
  "ip_address": "192.168.1.10",
  "device_name": null,
  "device_id": null
}
```

### 8.2 `AdminSessionRead`

```json
{
  "token_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "usuario_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "cliente_id": "e4c8e906-0e64-4f4e-a04d-8daee57dc7f8",
  "empresa_id": "550e8400-e29b-41d4-a716-446655440000",
  "empresa_nombre": "ACME SA",
  "issued_at": "2026-06-18T10:00:00",
  "created_at": "2026-06-18T10:00:00",
  "last_refresh_at": "2026-06-21T08:30:00",
  "last_used_at": "2026-06-21T08:30:00",
  "expires_at": "2026-06-25T10:00:00",
  "is_current": false,
  "status": "expiring_soon",
  "duration_seconds": 259200,
  "device": {
    "client_type": "mobile",
    "browser": "Mobile App",
    "browser_version": null,
    "os": "Android",
    "platform": "mobile",
    "device_label": "Mobile App en Android",
    "ip_address": "10.0.0.5",
    "device_id": "dev-abc"
  },
  "client_type": "mobile",
  "ip_address": "10.0.0.5",
  "device_name": "Pixel 7",
  "device_id": "dev-abc",
  "nombre_usuario": "jperez",
  "nombre": "Juan",
  "apellido": "Pérez",
  "user_agent": "MyApp/1.0 (Android 14)"
}
```

### 8.3 Respuesta paginada admin

```json
{
  "items": [ { "...": "AdminSessionRead" } ],
  "total": 42,
  "sessions": [ { "...": "AdminSessionRead" } ],
  "total_sesiones": 42,
  "pagina_actual": 1,
  "total_paginas": 5,
  "limit": 10
}
```

### 8.4 `SessionDeviceRead` (aislado)

```json
{
  "client_type": "web",
  "browser": "Firefox",
  "browser_version": "115.0",
  "os": "Linux",
  "platform": "desktop",
  "device_label": "Firefox 115.0 en Linux",
  "ip_address": "203.0.113.50",
  "device_id": null
}
```

### 8.5 Self-revoke — éxito / idempotente

```json
{
  "message": "Sesión (Token ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890) revocada exitosamente.",
  "token_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

```json
{
  "message": "Sesión (Token ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890) ya estaba cerrada.",
  "token_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

## 9. Reglas para Frontend

### Obligatorio — consumir del Backend

- `device.device_label` para mostrar dispositivo.
- `device.browser`, `device.os`, `device.platform` para iconografía o filtros.
- `is_current` para marcar sesión actual.
- `status` para alertas de expiración próxima.
- `empresa_nombre` / `empresa_id` para contexto multi-empresa.
- `token_id` como clave de fila y parámetro de revoke.

### Prohibido en Frontend

El Frontend **NO debe**:

- Parsear `user_agent` para inferir browser/OS (excepto admin diagnóstico crudo si se muestra literal).
- Calcular `device`, `browser`, `os` o `platform` localmente.
- Derivar `device_label` concatenando strings de UA.
- Asumir que `created_at` es fecha de login.
- Asumir que `last_used_at` es última actividad en la app.
- Implementar lógica de idempotencia distinta a confiar en HTTP `200` del self-revoke.

Todo enriquecimiento de dispositivo es responsabilidad exclusiva del Backend (`session_read_mapper.py`).

---

## 10. Changelog V1 (respecto al contrato anterior)

| Área | Antes | V1 Enterprise RC1 |
|------|-------|-------------------|
| `GET /sessions/` | `List[Dict]` sin tipado | `UserSessionRead[]` enriquecido |
| Dispositivo | `device_name` a menudo null | Objeto `device` con browser/OS/platform/label |
| Fechas semánticas | Solo `created_at`, `last_used_at` | + `issued_at`, `last_refresh_at` (alias legacy conservados) |
| Sesión actual | No expuesto | `is_current` |
| Estado | No expuesto | `status`, `duration_seconds` |
| Empresa | Solo `empresa_id` | + `empresa_nombre` |
| IP | Raíz `ip_address` | Raíz **y** `device.ip_address` (alias RC1) |
| Admin listado | Campos planos | `AdminSessionRead` enriquecido + `user_agent` admin |
| Admin paginado | `sessions` / `total_sesiones` | + `items` / `total` (dual) |
| Revocación usuario | No existía | `POST /sessions/{token_id}/revoke/` idempotente |
| Audit | Sin eventos sesión | `session_self_revoked`, `session_admin_revoked` (interno) |
| Login / Refresh / Logout | — | **Sin cambios** |
| BD / Redis | — | **Sin migraciones** |

---

## Referencias

- OpenAPI en runtime: `GET /openapi.json` (schemas `UserSessionRead`, `AdminSessionRead`, `SessionDeviceRead`, `PaginatedAdminSessionsResponse`).
- Arquitectura IAM: `docs/arquitectura/IAM_SESSION_MANAGEMENT_V2.md` §22.
- Plan implementación: `docs/arquitectura/ERP-IAM-SESSIONS-BE-IMPLEMENTATION-PLAN-01.md`.

---

*Documento generado bajo ERP-IAM-SESSIONS-BE-RC1-STABILIZATION — única referencia oficial Backend → Frontend para Sesiones Activas V1.*
