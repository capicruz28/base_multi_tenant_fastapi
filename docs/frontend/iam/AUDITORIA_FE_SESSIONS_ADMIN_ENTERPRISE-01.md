# Auditoría funcional Frontend — GET `/api/v1/auth/sessions/admin/`

**Versión:** 1.0.0  
**Fecha:** 2026-06-22  
**Tipo:** Auditoría READ ONLY (sin cambios de Backend)  
**Audiencia:** Equipo Frontend — rediseño Enterprise «Sesiones Activas»  
**Alcance:** Un único endpoint de listado administrativo  

**Referencias de código (Backend, solo lectura):**

| Área | Archivo |
|------|---------|
| Router | `app/modules/auth/presentation/endpoints.py` (`admin_list_all_active_sessions`) |
| Schemas | `app/modules/auth/presentation/schemas_admin_sessions.py`, `schemas_sessions.py` |
| Servicio | `app/modules/auth/application/services/active_sessions_read_service.py` |
| Mapper | `app/modules/auth/application/session/session_read_mapper.py` |
| Whitelist sort/search | `app/modules/auth/application/session/active_session_read_columns.py` |
| Contrato normativo | `docs/arquitectura/ERP-IAM-SESSIONS-API-CONTRACT-V2.md` |
| Tablas ORM | `app/infrastructure/database/tables.py` (`user_session`, `token_family`, `refresh_tokens`, `usuario`) |

---

## 1. Resumen ejecutivo

El endpoint **GET `/api/v1/auth/sessions/admin/`** devuelve las **sesiones activas del tenant** del administrador autenticado, enriquecidas con datos de usuario, empresa y dispositivo. Es el contrato principal para una pantalla Enterprise de auditoría y cierre remoto de sesiones.

**Veredicto:** el contrato actual **es suficiente** para construir una pantalla Enterprise de sesiones **activas** (listado paginado, búsqueda, ordenamiento, filtros, revocación admin vía endpoint hermano) **sin modificar Backend**, asumiendo **Session Management V2 activo** (`IAM_SESSION_MANAGEMENT_V2_ENABLED=true`).

**Limitaciones inherentes al contrato (no bugs):**

- Solo sesiones **activas**; no hay historial de sesiones revocadas/expiradas en este endpoint.
- `is_current` **siempre es `false`** en el listado admin (el Backend no compara con la sesión del admin que consulta).
- `revoked_at` / `revoked_reason` están en el DTO pero **siempre serán `null`** en este listado (filtro `is_active = 1`).
- `last_refresh_at` refleja **rotación OAuth/refresh**, no actividad de negocio ERP.
- El filtro `client_type` solo acepta `web` \| `mobile`; sesiones `desktop` \| `api` existen en BD pero no se filtran por ese parámetro.

**Gaps opcionales** (mejorarían UX Enterprise pero no bloquean MVP): ver §10.

---

## 2. Contrato HTTP

### 2.1 Request

| Atributo | Valor |
|----------|-------|
| **Método / ruta** | `GET /api/v1/auth/sessions/admin/` |
| **Autenticación** | Bearer JWT |
| **Autorización (código real)** | Rol **`Administrador`** vía `RoleChecker(["Administrador"])` — **no** hay `require_permission` adicional en el endpoint |
| **Scope de datos** | `cliente_id` del usuario autenticado (tenant operativo del admin) |

**Query parameters:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `page` | int, opcional | Si presente → respuesta paginada; si ausente → array legacy |
| `limit` | int, default 50, max 100 | Solo efectivo con `page` |
| `search` | string 1–100 | `LIKE` server-side (campos §8) |
| `sort_by` | string | Whitelist server-side (§8); inválido → **422** `INVALID_SORT_COLUMN` |
| `sort_order` | `asc` \| `desc` | Solo aplica si hay `sort_by` |
| `client_type` | `web` \| `mobile` | Filtra `user_session.platform` (V2) o equivalente V1 |
| `usuario_id` | UUID | Filtra sesiones de un usuario |

### 2.2 Response

**Modo legacy** (sin `page`): `200` → `AdminSessionRead[]`

**Modo paginado** (con `page`): `200` → `PaginatedAdminSessionsResponse`

Envelope dual (compatibilidad ERP + legacy FE):

| Campo envelope | Equivalente | Notas |
|----------------|-------------|-------|
| `items` | — | Estándar ERP |
| `total` | — | Total post-filtros |
| `sessions` | = `items` | Legacy |
| `total_sesiones` | = `total` | Legacy |
| `pagina_actual` | — | Página devuelta |
| `total_paginas` | — | Calculado server-side |
| `limit` | — | Tamaño de página efectivo |

**Errores:** `401`, `403`, `422` (sort inválido), `500` (mensaje genérico).

### 2.3 Motor de lectura (V1 vs V2)

El Backend elige motor según feature flag por tenant:

| Flag OFF (V1) | Flag ON (V2) |
|---------------|--------------|
| Fuente principal: `refresh_tokens` vigente | Fuente canónica: `user_session` + `token_family` + refresh vigente |
| JOIN outer a `user_session` | JOIN inner; familias comprometidas **excluidas** |
| Sin `session_id` en payload mapper | `session_id`, `family_id`, `login_ip`, etc. presentes |
| `expires_at` = expiración del **refresh token** | `expires_at` = expiración **absoluta de sesión** |
| `issued_at` = creación del refresh vigente | `issued_at` = inicio de sesión (`user_session.created_at`) |

**Recomendación FE Enterprise:** diseñar para **V2**; tratar V1 como legado pre-cutover.

---

## 3. Inventario completo de campos devueltos

Cada ítem es un **`AdminSessionRead`**: extiende `SessionReadBase` + campos admin.

### 3.1 Tabla maestra — campo → origen → semántica

| Campo JSON | Tipo | Tabla / origen BD | Columna / derivación | Semántica en admin |
|------------|------|-------------------|----------------------|--------------------|
| **Identidad de sesión** |
| `session_id` | UUID \| null | `user_session` | `session_id` | PK sesión lógica (**V2**). Estable hasta revocación. **Preferir para revoke y deep-link.** |
| `token_id` | UUID | `refresh_tokens` | `token_id` (vía `token_family.current_token_id`) | Refresh vigente; **cambia en cada rotación RTR**. Alias revoke V1. |
| `family_id` | UUID \| null | `token_family` | `family_id` | Familia RTR (**V2**). Diagnóstico técnico. |
| **Usuario** |
| `usuario_id` | UUID | `user_session` / `refresh_tokens` | `usuario_id` | Propietario de la sesión. Enlace a ficha usuario. |
| `nombre_usuario` | string \| null | `usuario` | `nombre_usuario` | Login (username). |
| `nombre` | string \| null | `usuario` | `nombre` | Nombre pila. |
| `apellido` | string \| null | `usuario` | `apellido` | Apellido. |
| **Tenant / contexto ERP** |
| `cliente_id` | UUID | `user_session` / `refresh_tokens` | `cliente_id` | Tenant. **Redundante** para admin tenant (siempre el mismo). |
| `empresa_id` | UUID \| null | `user_session` / `refresh_tokens` | `empresa_id` | Empresa activa al login/selección. |
| `empresa_nombre` | string \| null | `org_empresa` | `COALESCE(nombre_comercial, razon_social)` | Nombre legible de empresa. |
| **Temporalidad** |
| `issued_at` | datetime | Derivado | V2: `user_session.created_at`; V1: `refresh_tokens.created_at` | **Inicio de sesión** (V2) o emisión refresh (V1). |
| `created_at` | datetime | Idem `issued_at` | Alias legacy | Misma fecha que `issued_at`. |
| `last_refresh_at` | datetime \| null | `user_session` | `last_refresh_at` | Último `POST /refresh` exitoso. |
| `last_used_at` | datetime \| null | Alias | V2: = `last_refresh_at`; V1: `refresh_tokens.last_used_at` | Legacy; no usar como «última actividad ERP». |
| `expires_at` | datetime | `user_session` / `refresh_tokens` | `expires_at` | V2: fin de vida **sesión**; V1: fin refresh vigente. |
| `duration_seconds` | int | **Calculado** | `now - issued_at` (segundos ≥ 0) | Antigüedad de sesión desde inicio. |
| `status` | `"active"` \| `"expiring_soon"` | **Calculado** | Si `expires_at - now ≤ 24h` → `expiring_soon` | No distingue idle vs activa. |
| **Red / autenticación** |
| `login_ip` | string \| null | `user_session` | `login_ip` | IP del login original (**inmutable**). V2. |
| `last_seen_ip` | string \| null | `user_session` | `last_seen_ip` | Última IP en refresh. V2. |
| `ip_address` | string \| null | Alias | V2: `last_seen_ip` \|\| `login_ip`; V1: `last_seen_ip` | Legacy raíz; preferir `last_seen_ip` en V2. |
| `login_method` | string \| null | `user_session` | `login_method` | `password` \| `sso` \| `2fa` \| `api_key`. V2. |
| `platform` | string \| null | `user_session` | `platform` | `web` \| `mobile` \| `desktop` \| `api`. V2. |
| `client_type` | string | Alias | = `platform` en V2 | Legacy; valores típicos `web` \| `mobile`. |
| **Dispositivo (columnas planas)** |
| `device_name` | string \| null | `user_session` | `device_name` | Nombre amigable si el cliente lo envió. |
| `device_id` | string \| null | `user_session` | `device_id` | ID dispositivo (mobile). |
| `user_agent` | string \| null | `user_session` | `user_agent` | UA crudo — **solo admin**, diagnóstico. |
| **Dispositivo (objeto enriquecido)** |
| `device` | object | **Derivado** | Ver §3.2 | Presentación UX principal. |
| **Estado / revocación (en listado activo)** |
| `is_current` | bool | **Calculado** | Comparación con sesión del request | **Siempre `false`** en admin (no se pasa contexto). |
| `revoked_at` | datetime \| null | `user_session` | `revoked_at` | **Siempre `null`** en este listado (solo activas). |
| `revoked_reason` | string \| null | `user_session` | `revoked_reason` | **Siempre `null`** en activas. |

### 3.2 Objeto `device` (`SessionDeviceRead`)

| Campo | Origen |
|-------|--------|
| `client_type` | `platform` / `client_type` de fila |
| `browser` | Parseo heurístico de `user_agent` |
| `browser_version` | Parseo heurístico de `user_agent` |
| `os` | Parseo heurístico de `user_agent` |
| `platform` | Parseo: `desktop` \| `mobile` \| `tablet` \| `unknown` (≠ `user_session.platform`) |
| `device_label` | `device_name` si existe; si no, `"{browser} {version} en {os}"` |
| `ip_address` | Mismo valor que `ip_address` raíz |
| `device_id` | `user_session.device_id` |

**Nota UX:** `device.platform` (derivado UA) y `platform` raíz (BD) pueden **divergir** (ej. `platform=web` en BD pero `device.platform=desktop` por UA de navegador de escritorio).

---

## 4. Campos en BD no expuestos por el endpoint

### 4.1 `user_session`

| Columna BD | ¿En respuesta? | Utilidad Enterprise | Recomendación FE |
|------------|----------------|---------------------|------------------|
| `selection_token_completed` | No | Saber si la sesión quedó a medias (post-login, pre-selección empresa) | Gap **P2** — útil badge «Selección pendiente» |
| `last_business_activity_at` | No | **Última actividad ERP real** (API autenticada) | Gap **P1** — diferencia idle vs «solo refresh» |
| `device_fingerprint` | No | Correlación antifraude | **No mostrar**; posible gap Backend P3 seguridad |
| `is_active` | No (implícito) | Siempre `true` en este listado | No necesario en lista |
| `user_agent` | Sí (admin) | — | Panel detalle / soporte |

### 4.2 `token_family`

| Columna BD | ¿En respuesta? | Notas |
|------------|----------------|-------|
| `is_compromised` | No | Familias comprometidas **no aparecen** en listado |
| `compromised_at` | No | — |
| `invalidation_reason` | No | — |
| `current_token_id` | No (solo `token_id` resultante) | — |
| `created_at` | No | — |

### 4.3 `refresh_tokens` (token vigente)

| Columna BD | ¿En respuesta? | Notas |
|------------|----------------|-------|
| `token_hash` | **Nunca** | Secreto — correcto omitir |
| `expires_at` (token) | No separado | V2 usa `user_session.expires_at` en DTO |
| `parent_token_id` | No | Cadena RTR — solo forense |
| `is_used`, `used_at` | No | Filtrado (`is_used = 0`) |
| `is_revoked`, `revoked_at`, `revoked_reason` (token) | No | Filtrado (`is_revoked = 0`) |
| `created_at` (token) | No | V2 usa `user_session.created_at` como `issued_at` |

### 4.4 `usuario` (campos no joinados)

| Columna BD | Utilidad | Gap |
|------------|----------|-----|
| `correo` | Identificación admin | **P2** — username puede no bastar |
| `telefono`, `dni` | Identificación | P3 |
| `proveedor_autenticacion` | SSO futuro | P3 (Out of Scope SSO actual) |
| `es_activo` | Usuario deshabilitado con sesión viva | **P2** — alerta seguridad |

### 4.5 Otras fuentes

- **`cliente`**: sin datos de tenant en ítem (admin ya conoce su tenant).
- **`AuthAuditLog`**: eventos de login/revoke — **otro dominio**, no incluido.
- **Impersonación**: no hay flag en `user_session`; no deducible del DTO.

---

## 5. Clasificación: operativo vs técnico

### 5.1 Datos operativos (valor para administrador de tenant)

| Campo | Uso Enterprise |
|-------|----------------|
| `nombre_usuario`, `nombre`, `apellido` | Quién tiene la sesión |
| `empresa_nombre` / `empresa_id` | Contexto multiempresa |
| `device.device_label`, `platform` | Dónde está conectado |
| `last_refresh_at` | Última señal de vida (token) |
| `expires_at`, `status` | Riesgo de expiración / ventana de acción |
| `last_seen_ip`, `login_ip` | Geolocalización aproximada / detección anomalías |
| `login_method` | Tipo de acceso |
| `duration_seconds` | Antigüedad de sesión |
| Acción **Cerrar sesión** | `POST .../revoke_admin/` con `session_id` (V2) |

### 5.2 Datos técnicos (soporte L2 / diagnóstico)

| Campo | Uso |
|-------|-----|
| `session_id` | Identificador estable para tickets y revoke |
| `token_id` | Rotación RTR; cambia — copiar con advertencia |
| `family_id` | Trazabilidad RTR |
| `user_agent` | Diagnóstico UA no parseado |
| `device_id` | Correlación mobile |
| `device.browser`, `device.browser_version`, `device.os` | Desglose técnico |
| `cliente_id` | UUID tenant (redundante en UI tenant-scoped) |

### 5.3 Datos sin valor en listado admin

| Campo | Motivo |
|-------|--------|
| `is_current` | Siempre `false` — **no mostrar** columna «Sesión actual» |
| `revoked_at`, `revoked_reason` | Siempre `null` en activas |
| `created_at` | Duplicado de `issued_at` |
| `last_used_at` | Duplicado de `last_refresh_at` en V2 |

---

## 6. Recomendaciones de presentación UX

### 6.1 Mostrar siempre en tabla / lista (columnas Enterprise)

| Columna UI sugerida | Campo(s) API | Formato |
|---------------------|--------------|---------|
| Usuario | `nombre_usuario` + `nombre` `apellido` | «jperez — Juan Pérez» |
| Empresa | `empresa_nombre` | Texto; «—» si null |
| Dispositivo | `device.device_label` | Icono por `platform` |
| Plataforma | `platform` | Badge web / mobile / desktop / api |
| Última actividad (token) | `last_refresh_at` | Relativo + absoluto tooltip |
| Expira | `expires_at` + `status` | Fecha; badge si `expiring_soon` |
| IP actual | `last_seen_ip` | Texto; tooltip con `login_ip` «IP login» |
| Método | `login_method` | Badge password / 2fa / … |
| Acciones | — | Cerrar sesión → `revoke_admin` |

**Orden default Backend:** `last_refresh_at DESC` (V2) — alineado con «más recientes primero».

### 6.2 Panel de detalle (drawer / modal)

| Sección | Campos |
|---------|--------|
| Usuario | `usuario_id`, `nombre_usuario`, `nombre`, `apellido` |
| Contexto | `empresa_id`, `empresa_nombre`, `login_method` |
| Sesión | `session_id`, `issued_at`, `duration_seconds`, `expires_at`, `status` |
| Red | `login_ip`, `last_seen_ip`, comparación si difieren |
| Dispositivo | `device.*`, `device_name`, `device_id`, `user_agent` (colapsable) |
| Técnico | `token_id`, `family_id` (copiar UUID con disclaimer de rotación) |

### 6.3 No mostrar al usuario final / ocultar por defecto

| Dato | Motivo |
|------|--------|
| `token_hash` | Secreto (no está en API — mantener así) |
| `device_fingerprint` | Huella sensible |
| `is_current` | Engañoso en admin |
| `cliente_id` | Ruido en UI tenant |
| `revoked_*` en listado activo | Sin valor |
| UA completo en tabla | Ruido; solo detalle |

---

## 7. Capacidades FE soportadas sin cambios Backend

### 7.1 Paginación

Usar **`page` + `limit`** en producción Enterprise (evitar modo legacy sin `page` — carga full tenant).

### 7.2 Búsqueda (`search`)

Campos efectivos en SQL (V2):

- `usuario.nombre_usuario`, `nombre`, `apellido`
- `user_session.login_ip`, `last_seen_ip`, `device_name`, `platform`

**No busca:** email, `session_id`, `device_id` (aunque `device_id` está en whitelist documental C21, el `OR` del servicio V2 **no** incluye `device_id` en runtime — divergencia menor doc/código).

### 7.3 Ordenamiento (`sort_by`)

**V1:** `created_at`, `last_used_at`, `expires_at`, `ip_address`, `device_name`, `client_type`, `nombre_usuario`, `token_id`

**V2 (aditivos + alias):** `session_id`, `platform`, `login_ip`, `last_refresh_at`, `last_seen_ip`, `login_method`, `family_id`  
Alias automáticos: `last_used_at` → `last_refresh_at`; `ip_address` → `last_seen_ip`; `client_type` → `platform`

### 7.4 Filtros

| Filtro | Uso FE |
|--------|--------|
| `usuario_id` | Vista «sesiones de este usuario» desde ficha usuario |
| `client_type=web\|mobile` | Tabs Web / Mobile — **no** cubre desktop/api |

### 7.5 Acción complementaria obligatoria

| Acción | Endpoint | Path param |
|--------|----------|------------|
| Cerrar sesión (admin) | `POST /api/v1/auth/sessions/{id}/revoke_admin/` | **`session_id` preferido (V2)**; acepta `token_id` |

El listado **no** incluye permisos granulares RBAC; solo rol Administrador.

---

## 8. Ejemplo JSON (V2, ítem admin)

```json
{
  "session_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "token_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "family_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "usuario_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "cliente_id": "e4c8e906-0e64-4f4e-a04d-8daee57dc7f8",
  "empresa_id": "550e8400-e29b-41d4-a716-446655440000",
  "empresa_nombre": "ACME SA",
  "nombre_usuario": "jperez",
  "nombre": "Juan",
  "apellido": "Pérez",
  "issued_at": "2026-06-18T10:00:00",
  "created_at": "2026-06-18T10:00:00",
  "last_refresh_at": "2026-06-21T08:30:00",
  "last_used_at": "2026-06-21T08:30:00",
  "expires_at": "2026-07-18T10:00:00",
  "is_current": false,
  "status": "active",
  "duration_seconds": 259200,
  "platform": "web",
  "login_method": "password",
  "login_ip": "192.168.1.5",
  "last_seen_ip": "192.168.1.10",
  "ip_address": "192.168.1.10",
  "device_name": null,
  "device_id": null,
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
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
  "revoked_at": null,
  "revoked_reason": null
}
```

---

## 9. ¿Es suficiente el contrato para Enterprise sin tocar Backend?

### 9.1 Sí — cubierto hoy

| Capacidad Enterprise | Soporte |
|----------------------|---------|
| Listado multi-usuario tenant | Sí |
| Paginación escalable | Sí (`page`, `limit`, `total`, `total_paginas`) |
| Búsqueda por usuario / IP / dispositivo | Sí (`search`) |
| Ordenamiento server-side | Sí (`sort_by`, whitelist) |
| Filtro por usuario | Sí (`usuario_id`) |
| Filtro web/mobile | Parcial (`client_type`) |
| Identificación usuario + empresa | Sí |
| Dispositivo legible | Sí (`device.device_label`) |
| Señales de riesgo temporal | Parcial (`status`, `expires_at`, IPs) |
| Cierre remoto | Sí (endpoint hermano + `session_id`) |
| Diagnóstico L2 | Sí (`user_agent`, UUIDs en detalle) |

### 9.2 No cubierto (fuera de alcance de este GET)

| Necesidad | Estado |
|-----------|--------|
| Historial sesiones cerradas / revocadas | **No** — requeriría otro endpoint |
| Timeline de eventos (login, refresh, revoke) | **No** — `AuthAuditLog` no expuesto aquí |
| «Última actividad en ERP» | **No** — falta `last_business_activity_at` |
| Sesiones de familias comprometidas | **Ocultas** por diseño (filtro `is_compromised = 0`) |
| Agregados (N sesiones por usuario) | FE puede calcular en página o pedir otro contrato |
| RBAC fino (`iam.sesiones.leer`) | Solo rol Administrador |

---

## 10. Gaps recomendados (solo si se prioriza post-MVP Backend)

Prioridad para evolución de contrato — **ninguno bloquea** el rediseño FE inicial.

| ID | Campo / capacidad | Justificación técnica | Prioridad |
|----|-------------------|----------------------|-----------|
| GAP-01 | `last_business_activity_at` | `last_refresh_at` solo se actualiza en refresh OAuth; un usuario puede estar «activo en ERP» sin refrescar token. Campo ya existe en `user_session`, alimentado por pipeline de actividad. | **P1** |
| GAP-02 | `usuario.correo` (read-only) | Admins identifican personas por email cuando `nombre_usuario` es opaco o duplicado en display. | **P2** |
| GAP-03 | `selection_token_completed` | Sesión en estado intermedio post-login; evita falsos positivos «sesión activa» sin contexto empresa. | **P2** |
| GAP-04 | Filtro `platform` completo | `desktop` y `api` existen en CK BD pero `client_type` query solo acepta web/mobile. | **P2** |
| GAP-05 | Flag `usuario.es_activo` | Sesión activa de usuario deshabilitado — señal de incidente. | **P2** |
| GAP-06 | Endpoint historial / revocadas | Compliance y forense Enterprise — imposible con solo activas. | **P1** (nuevo endpoint) |
| GAP-07 | Indicador familia comprometida | Hoy excluidas del listado; admin no ve sesiones bajo investigación RTR. | **P3** (producto seguridad) |

---

## 11. Checklist diseño Frontend Enterprise

- [ ] Consumir modo **paginado** (`page=1`, `limit=50`).
- [ ] Preferir **`session_id`** para revoke y referencias internas.
- [ ] No usar **`token_id`** como ID de fila estable (rotación RTR).
- [ ] Ignorar **`is_current`** en vista admin.
- [ ] Mostrar **`last_refresh_at`** como «Última conexión (token)», no «Última actividad ERP».
- [ ] Tooltip **`login_ip`** vs **`last_seen_ip`** para auditoría de movimiento.
- [ ] Usar **`device.device_label`** en tabla; **`user_agent`** solo en detalle.
- [ ] Badge **`status=expiring_soon`** cuando `< 24h` a `expires_at`.
- [ ] Confirmación modal antes de **`revoke_admin`**.
- [ ] Manejar envelope dual: leer `items`/`total` (ignorar duplicado `sessions` salvo legacy).
- [ ] Detectar V2 por presencia de **`session_id`** non-null en ítems.
- [ ] Empty state + error **`INVALID_SORT_COLUMN`** en columnas ordenables.

---

## 12. Declaración de cierre

Esta auditoría describe el comportamiento **actual del código** en repositorio a 2026-06-22. No implica cambios de Backend, commits ni PR. Sirve como base única de verdad para el rediseño Frontend Enterprise de «Sesiones Activas».

**Documentos relacionados:**

- `docs/arquitectura/ERP-IAM-SESSIONS-API-CONTRACT-V2.md`
- `app/docs/iam/IAM_SESSION_MANAGEMENT_V2_BACKEND_SPECIFICATION.md`
