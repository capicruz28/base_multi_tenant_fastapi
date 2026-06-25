# ERP-IAM-SESSIONS-API-CONTRACT-V2

**Versión:** 2.0.0  
**Fecha:** 2026-06-22  
**Ticket:** IAM-BE-F0-API-CONTRACT-01  
**Audiencia:** Proyecto Frontend (consumo vía OpenAPI + este documento)  
**Estado:** En implementación — wiring backend desde F10+  
**Supersedes:** Parcialmente `ERP-IAM-SESSIONS-API-CONTRACT-V1.md` (paths inalterados)  

**Referencias:** `IAM-SESSION-MANAGEMENT-V2-DESIGN-01.md` (D-01, D-03), `IAM-SESSION-MANAGEMENT-V2-F0-EXECUTION-PLAN.md` §7.

---

## 1. Objetivo

Documentar el contrato **aditivo** de Session Management V2 para consumidores Frontend y QA. Los endpoints permanecen bajo `/api/v1/auth/*`. El JSON de respuesta es **superset** del contrato V1: ningún campo V1 se elimina en V2.

**Identificador canónico de sesión en V2:** `session_id` (UUID, PK de `user_session`).  
**Identificador del refresh vigente:** `token_id` (UUID, PK de `refresh_tokens` activo).

---

## 2. Principios de compatibilidad

1. **Mismos endpoints** que V1 bajo `/api/v1/auth/`.
2. **JSON superset** — todos los campos V1 permanecen en respuestas V2.
3. **Campos nuevos** son opcionales para FE legacy (ignorar si no se consumen).
4. **Sin eliminación** de campos V1 hasta F15+ y acuerdo explícito con FE.
5. **Feature flag** `IAM_SESSION_MANAGEMENT_V2_ENABLED` controla el backend; FE no envía este flag. Mientras el flag esté OFF, las respuestas siguen el contrato V1.

---

## 3. Cambios de semántica documentados

| Campo V1 | Semántica V1 | Semántica V2 |
|----------|--------------|--------------|
| `token_id` en listado | ID de sesión (único identificador) | ID del **refresh token vigente** (cambia en rotación RTR) |
| `session_id` | — (no existía) | **ID canónico de sesión** (`user_session.session_id`) — **nuevo** |
| `issued_at` | Emisión del refresh vigente | Inicio de sesión lógica (`user_session.created_at`) — estable en la vida de la sesión |
| `last_refresh_at` | Alias de `last_used_at` | Último `POST /refresh` exitoso (`user_session.last_refresh_at`) |
| `expires_at` | Expiración del refresh vigente | Expiración **absoluta de la sesión** (`user_session.expires_at`) |
| `client_type` | Tipo de cliente (`web` \| `mobile`) | Alias de `platform` — **ambos** presentes en V2 |
| `ip_address` (raíz listado) | IP del token | `last_seen_ip` de la sesión (última IP conocida) |
| `login_ip` | — | IP del login original — **nuevo**, inmutable, solo auditoría |

---

## 4. Endpoints

Base URL API: `/api/v1/auth`

### 4.1 GET `/sessions/`

| Atributo | Valor |
|----------|-------|
| **Autenticación** | Bearer JWT |
| **Autorización** | Usuario autenticado |
| **Response** | `200` → `UserSessionRead[]` |
| **Errores** | `401`, `500` |

**Delta V2:** cada ítem incluye `session_id`, `platform`, `login_ip` además de todos los campos V1.

Orden: `last_refresh_at DESC` (equivalente semántico a `last_used_at DESC` en V1).

---

### 4.2 GET `/sessions/admin/`

| Atributo | Valor |
|----------|-------|
| **Autenticación** | Bearer JWT |
| **Autorización** | Administrador tenant + permisos IAM |
| **Response** | `200` → `AdminSessionRead[]` **o** `PaginatedAdminSessionsResponse` |
| **Errores** | `401`, `403`, `422` (`INVALID_SORT_COLUMN`), `500` |

**Query params:** iguales a V1 (`page`, `limit`, `search`, `sort_by`, `sort_order`, `client_type`, `usuario_id`).

**Delta V2:** ítems con `session_id`, `platform`, `login_ip`. Whitelist `sort_by` ampliada (§7).

---

### 4.3 POST `/sessions/{id}/revoke/`

| Atributo | Valor |
|----------|-------|
| **Autorización** | Usuario autenticado — solo sesiones propias |
| **Path** | `{id}` — UUID |
| **Response** | `200` → `{ "message": string, "token_id": string }` (V1); V2 puede incluir `session_id` aditivo |
| **Errores** | `404`, `401` |

**Delta V2 — resolución de `{id}`:**

- Acepta `session_id` (**preferido**).
- Acepta `token_id` del refresh vigente (**alias** compatibilidad V1).
- Semántica idempotente self-revoke conservada (RC1).

---

### 4.4 POST `/sessions/{id}/revoke_admin/`

| Atributo | Valor |
|----------|-------|
| **Autorización** | Administrador |
| **Path** | `{id}` — UUID (`session_id` o `token_id` vigente) |
| **Response** | `200` → `{ "message": string }` |
| **Errores** | `404`, `403`, `500` |

**Delta V2:** misma resolución dual de path que self-revoke.

---

### 4.5 GET `/me/` (delta V2)

| Campo nuevo | Tipo | Descripción |
|-------------|------|-------------|
| `current_session_id` | `UUID` | Sesión del access token actual — disponible F12+ |
| `current_token_id` | `UUID` | Conservado (V1) — refresh vigente del request |

FE debe preferir `current_session_id` para `is_current` cuando esté presente.

---

## 5. DTO `UserSessionRead` — campos V2 aditivos

Todos los campos V1 permanecen. Adiciones:

| Campo | Tipo | Descripción | Semántica V2 |
|-------|------|-------------|--------------|
| `session_id` | `UUID` | Identificador canónico | PK `user_session` — estable hasta revocación |
| `platform` | `string` | Plataforma sesión | `web` \| `mobile` — fuente `user_session.platform` |
| `login_ip` | `string \| null` | IP login | Inmutable; no usar para display de “última actividad” |

**Campos V1 con semántica actualizada en V2:** ver §3 (`issued_at`, `last_refresh_at`, `expires_at`, `token_id`, `ip_address`).

`SessionDeviceRead` sin cambios estructurales; `device.ip_address` refleja `last_seen_ip` en V2.

---

## 6. DTO `AdminSessionRead`

Extiende `UserSessionRead` con campos admin V1 (`nombre_usuario`, `nombre`, `apellido`, `user_agent`) más los campos V2 aditivos de §5.

---

## 7. Whitelist `sort_by` (admin) — V2

**V1 (conservados):** `created_at`, `last_used_at`, `expires_at`, `ip_address`, `device_name`, `client_type`, `nombre_usuario`, `token_id`

**V2 (aditivos):** `session_id`, `platform`, `login_ip`, `last_refresh_at`

Inválido → HTTP `422`, código `INVALID_SORT_COLUMN`.

---

## 8. JWT access — claim `sid`

| Claim | Tipo | Descripción | Disponibilidad |
|-------|------|-------------|----------------|
| `sid` | UUID string | `session_id` de la sesión autenticada | F13+ |

El FE **no debe** depender de `sid` hasta despliegue coordinado F13+. Mientras tanto, usar `current_token_id` / cookies refresh como en V1.

---

## 9. Comportamiento post-cutover F14

1. Tras activar `IAM_SESSION_MANAGEMENT_V2_ENABLED=true` en producción, **re-login obligatorio** en todos los dispositivos.
2. Sesiones V1 (modelo monolítico `refresh_tokens` legacy) quedan invalidadas en entornos migrados.
3. Comunicación usuario: ver `IAM-SESSION-MANAGEMENT-V2-F14-CUTOVER-TICKET.md`.

---

## 10. Matriz FE — acciones recomendadas

| Prioridad | Campo / acción FE | Acción |
|:---------:|-------------------|--------|
| P0 | `is_current` | Comparar `current_session_id` cuando exista; fallback `current_token_id` |
| P1 | Revoke remoto | Enviar `session_id` en path cuando esté disponible en listado |
| P2 | Device display | `device.device_label` (sin cambio respecto V1) |
| P3 | `platform` vs `client_type` | Migrar lectura a `platform` cuando conveniente; `client_type` se mantiene |

---

## 11. Reglas de compatibilidad (resumen)

### El Frontend puede asumir (V2)

- Respuestas con flag V2 ON son superset JSON de V1.
- `session_id` es estable mientras la sesión esté activa (no cambia en rotación RTR).
- `token_id` puede cambiar tras cada rotación de refresh.
- Path revoke acepta `session_id` o `token_id` vigente.

### El Frontend nunca debe asumir

- Que `token_id` sea el identificador de sesión en V2 (usar `session_id`).
- Que `issued_at` cambie en cada refresh en V2 (es inicio de sesión).
- Que `last_refresh_at` refleje actividad de negocio API (solo refresh OAuth).
- Presencia de `sid` en JWT antes de F13.
- Idempotencia en `revoke_admin` (solo self-revoke).

---

## 12. Ejemplo JSON `UserSessionRead` (V2)

```json
{
  "session_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "token_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "usuario_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "cliente_id": "e4c8e906-0e64-4f4e-a04d-8daee57dc7f8",
  "empresa_id": "550e8400-e29b-41d4-a716-446655440000",
  "empresa_nombre": "ACME SA",
  "issued_at": "2026-06-18T10:00:00",
  "created_at": "2026-06-18T10:00:00",
  "last_refresh_at": "2026-06-21T08:30:00",
  "last_used_at": "2026-06-21T08:30:00",
  "expires_at": "2026-07-18T10:00:00",
  "is_current": true,
  "status": "active",
  "duration_seconds": 259200,
  "platform": "web",
  "login_ip": "192.168.1.5",
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

---

## 13. Referencias cruzadas

| Documento | Relación |
|-----------|----------|
| `ERP-IAM-SESSIONS-API-CONTRACT-V1.md` | Contrato base RC1 — vigente con flag OFF |
| `IAM-SESSION-MANAGEMENT-V2-DECISIONS-LOG.md` | D-01, D-03 ACCEPTED |
| `IAM-SESSION-MANAGEMENT-V2-DESIGN-01.md` | Modelo `user_session` + RTR |

---

**Fin del documento — ERP-IAM-SESSIONS-API-CONTRACT-V2 v2.0.0**
