# IAM Session Management — Documentación Oficial V2

**Ticket:** IAM-BE-DOCS-SESSION-V2-01  
**Versión arquitectónica:** V2 (post P1-04)  
**Estado del dominio:** Production Ready (alcance certificado P1-01 → P1-04 + HOTFIX-01 + CLEANUP-01)  
**Fecha:** 2026-06-17  
**Fase del proyecto:** IAM Session Management — cierre P1-04  
**Audiencia:** Frontend, integradores, soporte técnico  

> Este documento describe **únicamente** el comportamiento implementado en el código actual.  
> No incluye TRACE, implementaciones temporales ni código eliminado.

---

## Índice

1. [Introducción](#1-introducción)
2. [Arquitectura general](#2-arquitectura-general)
3. [Componentes del dominio](#3-componentes-del-dominio)
4. [Flujo Login](#4-flujo-login)
5. [Flujo Refresh](#5-flujo-refresh)
6. [Flujo Logout](#6-flujo-logout)
7. [Logout All](#7-logout-all)
8. [Password Change](#8-password-change)
9. [Cambiar Empresa](#9-cambiar-empresa)
10. [Seleccionar Empresa](#10-seleccionar-empresa)
11. [Session Limit](#11-session-limit)
12. [Idle Timeout](#12-idle-timeout)
13. [Token Reuse](#13-token-reuse)
14. [Redis](#14-redis)
15. [Refresh Tokens — estados y transiciones](#15-refresh-tokens--estados-y-transiciones)
16. [Concurrencia](#16-concurrencia)
17. [Garantías](#17-garantías)
18. [Limitaciones conocidas](#18-limitaciones-conocidas)
19. [Contrato para Frontend](#19-contrato-para-frontend)
20. [Diagramas](#20-diagramas)
21. [Glosario](#21-glosario)
22. [Estado del dominio](#22-estado-del-dominio)

---

## 1. Introducción

### Objetivo

El dominio **Session Management** del backend IAM gestiona el ciclo de vida completo de las sesiones de usuario en el ERP multi-tenant:

- Emisión de tokens JWT (access y refresh).
- Persistencia y revocación de refresh tokens en SQL Server (`refresh_tokens`).
- Rotación atómica de refresh en operaciones sensibles.
- Control de inactividad (idle timeout), límite de sesiones simultáneas y detección de reutilización maliciosa.
- Revocación de access tokens vía Redis (blacklist + session access mapping).

### Problemas que resuelve

| Problema | Mecanismo |
|----------|-----------|
| Sesiones persistentes sin re-login | Refresh token en BD + cookie/body |
| Robo de refresh token | Rotación atómica + detección TOKEN_REUSE |
| Sesiones zombie | Idle timeout + revocación en BD |
| Demasiados dispositivos conectados | Session limit (`max_active_sessions`) |
| Access token robado tras logout | Blacklist Redis por `jti` |
| Cambio de empresa sin re-login | Rotación atómica con nuevo `empresa_id` |

### Qué garantiza

- **Fuente de verdad de sesión refresh:** tabla `refresh_tokens` (estado `is_revoked`, `revoked_reason`, `expires_at`).
- **Rotación atómica** en `POST /auth/refresh/` y `POST /auth/empresa/cambiar/` (cuando hay refresh previo): INSERT del nuevo token + UPDATE del anterior con `SESSION_ROTATED` en una única transacción bajo `UPDLOCK`.
- **Rollback completo** si la revocación del token antiguo falla durante la rotación.
- **Idempotencia de logout:** siempre HTTP 200; revocación best-effort.
- **Filtrado por tenant:** todas las operaciones de refresh usan `cliente_id` del JWT refresh o del contexto validado.

### Qué NO garantiza

- Sincronización instantánea entre access JWT, refresh JWT, Redis y cookies en todos los escenarios concurrentes.
- Invalidación inmediata del access token actual tras `logout_all` (el access sigue válido hasta expirar).
- Blacklist de access cuando Redis no está disponible (fail-soft: el access puede seguir siendo aceptado).
- Una única fila activa por dispositivo lógico en el fallback legacy de cambiar empresa sin refresh.
- Refresh de sesiones de impersonación (explícitamente bloqueado con HTTP 403).

---

## 2. Arquitectura general

### Componentes

| Componente | Rol | Ubicación principal |
|------------|-----|---------------------|
| **JWT Access** | Autenticación de requests API; corta duración; incluye `jti`, `empresa_id`, claims de nivel | `app/core/security/jwt.py` → `create_access_token` |
| **JWT Refresh** | Renovación de sesión; larga duración; incluye `cliente_id`, `sub` | `create_refresh_token` |
| **Refresh Tokens (BD)** | Fuente de verdad del estado de sesión refresh | Tabla `refresh_tokens` |
| **Redis — Blacklist** | Revocación de access por `jti` | `RedisService.set_token_blacklist` / `is_token_blacklisted` |
| **Redis — Session Access Mapping** | Vincula `token_id` (BD) → `{jti, exp}` del access emitido | `RefreshTokenService.link_session_access_jti` |
| **UnitOfWork** | Transacción SQL única para rotación | `app/core/application/unit_of_work.py` |
| **UPDLOCK, ROWLOCK** | Bloqueo de fila en rotación concurrente | `SQL_LOCK_REFRESH_TOKEN_BY_HASH` |

### Diagrama ASCII — arquitectura

```
┌─────────────┐     Bearer access      ┌──────────────────┐
│   Frontend  │ ─────────────────────► │  API (deps.py)   │
│  Web/Mobile │                        │  JWT decode      │
└──────┬──────┘                        │  + blacklist     │
       │                               └────────┬─────────┘
       │ cookie/body refresh                    │
       ▼                                        ▼
┌──────────────────────────────────────────────────────────────┐
│              POST /api/v1/auth/refresh/                         │
│  Depends: get_current_user_from_refresh                       │
│    → validate_refresh_token (BD)                              │
│    → rotate_refresh_token_service (UoW + UPDLOCK)             │
└───────────────┬──────────────────────────────┬───────────────┘
                │                              │
                ▼                              ▼
     ┌────────────────────┐         ┌─────────────────────┐
     │  SQL Server        │         │  Redis              │
     │  refresh_tokens    │         │  blacklist:jti      │
     │  (is_revoked,      │         │  session:access_jti │
     │   revoked_reason)  │         │  :{token_id}        │
     └────────────────────┘         └─────────────────────┘
```

### Prefijo API

Todos los endpoints de sesión documentados viven bajo **`/api/v1/auth/`**, salvo configuración SSO admin en `/api/v1/sso/` (gestión de proveedores, no login de sesión).

---

## 3. Componentes del dominio

### RefreshTokenService

**Archivo:** `app/modules/auth/application/services/refresh_token_service.py`

| Responsabilidad | Métodos clave |
|-----------------|---------------|
| Almacenar refresh en BD | `store_refresh_token` |
| Validar refresh contra BD | `validate_refresh_token` |
| Revocar refresh específico | `revoke_token` |
| Revocar todas las sesiones del usuario | `revoke_all_user_tokens` |
| Revocar por ID (admin) | `revoke_refresh_token_by_id` |
| Session limit | `enforce_max_active_sessions` |
| Session access mapping | `link_session_access_jti`, `blacklist_access_for_token_id`, `blacklist_access_for_user_active_sessions` |
| Detección reuse | `is_revoked_refresh_reuse_candidate`, `handle_revoked_refresh_reuse` |
| Hash de token | `hash_token` |

### rotate_refresh_token_service

**Archivo:** `app/modules/auth/application/services/rotate_refresh_token_service.py`

Orquesta la rotación atómica: abre `UnitOfWork`, invoca `rotate_refresh_token_core`, construye `RotateResult`. Lee idle timeout desde `cliente_auth_config` si no se pasa explícitamente. **No aplica session limit** (equivalente al comportamiento legacy `store(is_rotation=True)`).

### rotate_refresh_token_core

**Archivo:** `app/infrastructure/database/queries/auth/refresh_token_rotate_queries_core.py`

Ejecuta dentro de una UoW ya abierta:

1. `SELECT ... WITH (UPDLOCK, ROWLOCK)` por `token_hash` + `cliente_id`
2. Validaciones: usuario, revocado, expirado, idle
3. `UPDATE` activity (`last_used_at`, `uso_count`)
4. `INSERT` nuevo refresh token
5. `UPDATE` anterior → `is_revoked=1`, `revoked_reason=SESSION_ROTATED`

Si el paso 5 no afecta filas → `RuntimeError` → rollback UoW.

### RotateResult / RotateOutcome

**Archivo:** `app/modules/auth/application/session/rotate_result.py`

```python
class RotateOutcome(StrEnum):
    ROTATED = "rotated"
    IDLE_TIMEOUT = "idle_timeout"
    NOT_FOUND = "not_found"
    EXPIRED = "expired"
    ALREADY_REVOKED = "already_revoked"
    ALREADY_ROTATED = "already_rotated"
    USER_MISMATCH = "user_mismatch"
```

`RotateResult.success` es `True` solo cuando `outcome == ROTATED`.

### Session Access Mapping

Clave Redis: `session:access_jti:{token_id}`  
Valor JSON: `{"jti": "<access_jti>", "exp": <unix_timestamp>}`  
TTL: derivado de `exp` del access o `access_expire_minutes` (mínimo 60 s).

Permite blacklistear el access asociado a una sesión refresh al hacer logout admin, password change o token reuse, sin consultar al cliente.

**Fail-soft:** si Redis falla al vincular, la sesión refresh sigue siendo válida; el access no queda mapeado.

### Blacklist

Clave Redis: `blacklist:token:{jti}`  
Verificación en cada request autenticado: `get_current_user_data` (`app/api/deps.py`).

### Idle Timeout

Configuración por tenant: `cliente_auth_config.session_idle_timeout_minutes` (BD ADMIN).  
Si NULL o ≤ 0 → deshabilitado.

Aplicado en:
- `validate_refresh_token` (pre-rotate, fuera de txn rotate)
- `rotate_refresh_token_core` (dentro de txn, con `GETDATE()`)

### Session Limit

Configuración: `cliente_auth_config.max_active_sessions`.  
Aplicado solo en `store_refresh_token(is_rotation=False)`.

### Token Reuse

Si un refresh **revocado** con motivo `SESSION_ROTATED` (o `revoked_reason` NULL legacy) se reutiliza → `handle_revoked_refresh_reuse`:
- Auditoría `token_reuse_detected`
- Blacklist access de sesiones activas del usuario
- `revoke_all_user_tokens` con `TOKEN_REUSE`
- `AuthenticationError` → HTTP 401

**Excepción:** endpoint refresh con `suppress_session_rotated_reuse=True` (F5 concurrente post-rotación).

### Auditoría

Eventos registrados vía `AuditService.registrar_auth_event` (fail-soft, no bloquean flujo):

| Evento | Flujo |
|--------|-------|
| `login_success` / `login_failed` | Login |
| `token_refresh` | Refresh exitoso |
| `token_invalid_or_revoked` | Refresh con JWT válido pero BD inválida |
| `token_reuse_detected` | Reuse malicioso |
| `logout` | Logout |
| `logout_forced` | Logout all |
| `empresa_seleccionada` | Seleccionar empresa |
| `empresa_cambiada` | Cambiar empresa |

---

## 4. Flujo Login

**Endpoint:** `POST /api/v1/auth/login/`

### Pasos

```
1. Autenticar credenciales (cliente_id / subdominio)
2. Resolver empresa activa o devolver LoginEmpresaSelectionResponse (selection_token)
3. create_access_token + create_refresh_token
4. store_refresh_token(is_rotation=False)
      → enforce_max_active_sessions (si configurado)
      → INSERT refresh_tokens
5. link_session_access_jti(token_id, access_jti)  [si store OK]
6. Web: Set-Cookie refresh_token HttpOnly
   Mobile: refresh_token en JSON body
7. Auditoría login_success
```

### Tablas modificadas

| Tabla | Operación |
|-------|-----------|
| `refresh_tokens` | INSERT (nueva sesión) |
| `refresh_tokens` | UPDATE revocado (session limit, si aplica) |

### Redis

- `session:access_jti:{token_id}` → vincula access emitido (si store retorna `token_id`).

### Comportamiento especial — multi-empresa

Si el usuario debe elegir empresa → respuesta `LoginEmpresaSelectionResponse` con `selection_token` (access JWT con `empresa_selection_pending: true`). **No se emite refresh** en este paso.

### Comportamiento fail-soft

Si `store_refresh_token` falla, el login **no falla**: se emite access (y refresh JWT/cookie) pero puede no existir fila en BD. El frontend recibirá tokens que no podrán renovarse.

### SSO (Azure / Google)

**Endpoints:** `POST /api/v1/auth/sso/azure/`, `POST /api/v1/auth/sso/google/`

Flujo equivalente a login directo: `store_refresh_token(is_rotation=False)` + cookie/body.  
**Diferencia actual:** no invoca `link_session_access_jti` (el login password sí lo hace).

---

## 5. Flujo Refresh

**Endpoint:** `POST /api/v1/auth/refresh/`

### Depends — get_current_user_for_refresh_endpoint

Wrapper de `AuthService.get_current_user_from_refresh` con **`suppress_session_rotated_reuse=True`**.

Secuencia del Depends:

1. Leer refresh: cookie `refresh_token` (web) o body JSON (mobile, header `X-Client-Type: mobile`).
2. `decode_refresh_token` — validar firma JWT.
3. `validate_refresh_token(token, cliente_id=token_cliente_id del JWT)`:
   - Fila activa: `is_revoked=0` AND `expires_at > GETDATE()`
   - Idle check → revoke IDLE_TIMEOUT si aplica
   - Activity tracking (`record_refresh_token_activity_core`)
4. Cargar usuario; resolver `empresa_id` desde **BD** (`refresh_tokens.empresa_id`), JWT como fallback.
5. Si BD inválida y token revocado SESSION_ROTATED + suppress → **no** dispara TOKEN_REUSE.

### Handler — rotación atómica

Tras Depends exitoso:

1. Re-leer refresh antiguo (cookie/body).
2. Bloquear refresh en sesiones de impersonación → **403**.
3. Emitir nuevo access + refresh JWT (`create_access_token`, `create_refresh_token`).
4. `rotate_refresh_token_service(old, new, cliente_id, usuario_id, ...)`
5. Según `RotateOutcome`:

| Outcome | HTTP | Cookie/body refresh | Access |
|---------|------|---------------------|--------|
| `ROTATED` | 200 | **Actualiza** (web cookie / mobile body) | Nuevo |
| `ALREADY_ROTATED` | 200 | **NO actualiza** | Nuevo |
| `IDLE_TIMEOUT` | 401 | — | — |
| `NOT_FOUND`, `EXPIRED`, `ALREADY_REVOKED`, `USER_MISMATCH` | 401 | — | — |

Mensaje 401 unificado:
> "Sesión expirada o cerrada remotamente. Por favor, vuelva a iniciar sesión."

En `ROTATED`: `link_session_access_jti(new_token_id, new_access_jti)`.

### Diagrama — Refresh

```
Cliente                    Depends                         Handler
  │                          │                               │
  │ POST /refresh/           │                               │
  ├─────────────────────────►│ decode_refresh_token          │
  │                          │ validate_refresh_token (BD)   │
  │                          │ idle + activity               │
  │◄─────────────────────────┤ 401 si inválido               │
  │                          │                               │
  │                          ├──────────────────────────────►│ create new JWTs
  │                          │                               │ rotate_refresh_token_service
  │                          │                               │   UPDLOCK → INSERT → UPDATE SESSION_ROTATED
  │◄─────────────────────────────────────────────────────────┤ 200 + access (+ refresh si ROTATED)
```

### Detalle transaccional (UPDLOCK)

```sql
-- Paso 1: lock
SELECT ... FROM refresh_tokens WITH (UPDLOCK, ROWLOCK)
WHERE token_hash = :token_hash AND cliente_id = :cliente_id

-- Paso 4: insert nuevo
INSERT INTO refresh_tokens (...) OUTPUT INSERTED.token_id ...

-- Paso 5: revocar anterior
UPDATE refresh_tokens SET is_revoked=1, revoked_reason='SESSION_ROTATED'
WHERE token_hash = :old_token_hash AND cliente_id = :cliente_id AND is_revoked=0
```

---

## 6. Flujo Logout

**Endpoint:** `POST /api/v1/auth/logout/` (también `/logout` sin schema)

Siempre retorna **HTTP 200** (idempotente).

### Pasos — perform_logout

```
1. Extraer refresh: cookie (web) o body.refresh_token (mobile)
2. Si hay refresh:
   a. decode_refresh_token → token_cliente_id
   b. validate_refresh_token (sin activity — detectado por stack perform_logout)
   c. revoke_token → revoked_reason USER_LOGOUT
      (fallback: revoke_refresh_token_core si no hay usuario_id)
   d. Auditoría logout
3. Si Authorization Bearer presente:
   blacklist_access_token_jti(jti del access)  [fail-soft]
4. Response: delete_cookie refresh_token (+ access_token)
```

### Qué NO requiere logout

- Access token válido (opcional para blacklist).
- Que el refresh siga activo (revocación idempotente si ya estaba revocado).

---

## 7. Logout All

**Endpoint:** `POST /api/v1/auth/logout_all/`

**Autenticación:** Bearer access token requerido.

### Pasos

```
1. blacklist_access_for_user_active_sessions(cliente_id, usuario_id)
2. blacklist_access_token_jti(jti del access actual)
3. revoke_all_user_tokens → revoked_reason LOGOUT_ALL (default del servicio)
4. Auditoría logout_forced
5. HTTP 200 + mensaje con cantidad revocada
```

### Comportamiento del access actual

El access token usado en la llamada **sigue siendo válido hasta su expiración natural** (documentado en el endpoint). El frontend debe redirigir a login inmediatamente y no confiar en poder refrescar.

---

## 8. Password Change

**Endpoint:** `POST /api/v1/auth/password/change/`

**Autenticación:** Bearer access (accesible con `requires_password_change=true`).

### Pasos — PasswordChangeService.change_password

```
1. Validar contraseña actual (solo proveedor local)
2. UPDATE usuario.contrasena, requiere_cambio_contrasena=false
3. blacklist_access_for_user_active_sessions
4. revoke_all_user_tokens → PASSWORD_CHANGE
5. revoke_token(old_refresh) redundante si presente
6. blacklist_access_token_jti(access_jti actual)
7. emitir_sesion_completa_con_empresa → nuevos JWT
8. store_refresh_token(is_rotation=False) → nueva sesión única
9. link_session_access_jti
10. Response vía _session_token_http_response (cookie/body refresh)
```

---

## 9. Cambiar Empresa

**Endpoint:** `POST /api/v1/auth/empresa/cambiar/`

**Autenticación:** Bearer access de sesión normal (no selection token).

**Body:** `{ "empresa_id": "<uuid>", "refresh_token": "..." }` — `refresh_token` solo mobile.

### Con refresh token (camino principal)

```
1. Validar tenant, usuario, empresa destino
2. emitir_sesion_completa_con_empresa (nuevo access + refresh JWT con empresa_id nueva)
3. rotate_refresh_token_service(old_refresh, new_refresh, request_cliente_id, ...)
4. Outcomes:
   - ROTATED → link_session_access_jti + 200 + cookie/body con nuevo refresh
   - ALREADY_ROTATED → 200 + cookie/body con nuevo refresh JWT (**sin** link_session_access_jti)
   - IDLE_TIMEOUT / otros → 401
5. persist_usuario_empresa_default_id
6. Auditoría empresa_cambiada
```

### Sin refresh token (fallback legacy)

```
1. emitir_sesion_completa_con_empresa
2. store_refresh_token(is_rotation=True)  ← NO revoca el refresh anterior
3. link_session_access_jti si store OK
4. 200 + cookie/body
```

**Web:** el refresh se lee de cookie HttpOnly. Si la cookie no viaja, entra en fallback legacy.

### Empresa activa — fuente de verdad

- En refresh: `refresh_tokens.empresa_id` (BD) > claim JWT.
- En cambiar: el nuevo JWT y la fila insertada/rotada llevan el `empresa_id` nuevo.

### Impersonación

`POST /empresa/cambiar/` retorna **403** durante impersonación.

---

## 10. Seleccionar Empresa

**Endpoint:** `POST /api/v1/auth/empresa/seleccionar/`

**Autenticación:** Bearer con `selection_token` del login multi-empresa (`require_selection_token_payload`).

### Pasos — seleccionar_empresa_post_login

```
1. Validar empresa asignada al usuario
2. emitir_sesion_completa_con_empresa
3. store_refresh_token(is_rotation=False)
4. link_session_access_jti
5. blacklist_access_token_jti(selection_jti)  ← invalida selection token
6. persist_usuario_empresa_default_id
7. Auditoría empresa_seleccionada
8. _session_token_http_response
```

---

## 11. Session Limit

### enforce_max_active_sessions

Invocado **solo** cuando `store_refresh_token(is_rotation=False)`.

```
1. Leer max_active_sessions de cliente_auth_config
2. Si NULL o ≤ 0 → no hace nada
3. Listar sesiones activas ordenadas por created_at ASC
4. Revocar las más antiguas hasta cumplir límite
   → revoked_reason SESSION_LIMIT
```

### Cuándo aplica

| Flujo | Session limit |
|-------|---------------|
| Login | ✓ |
| Seleccionar empresa | ✓ |
| Password change (nueva sesión) | ✓ |
| SSO Azure/Google | ✓ |
| Refresh (rotación) | ✗ |
| Cambiar empresa (rotate o store is_rotation=True) | ✗ |

---

## 12. Idle Timeout

### Validación previa — validate_refresh_token

Fuera de la transacción de rotación. Usa `is_refresh_token_session_idle_expired_core` comparando `last_used_at` (o `created_at`) con el límite en minutos.

Si idle → `revoke_token(IDLE_TIMEOUT)` → retorna `None` → Depends responde 401.

**Excluido en contexto logout** (detectado por stack `perform_logout`).

### Validación en transacción — rotate_refresh_token_core

Calcula `idle_expired` en el SELECT con `GETDATE()` bajo UPDLOCK. Si idle → `SQL_REVOKE_IDLE_IN_TX` → outcome `IDLE_TIMEOUT` (commit de la revocación idle).

### Motivo del doble control

- **Depends:** rechazo temprano antes de emitir nuevos JWT.
- **Core:** revalidación bajo lock para cerrar ventana de carrera entre validate y rotate en requests concurrentes.

---

## 13. Token Reuse

### TOKEN_REUSE

Disparado por `handle_revoked_refresh_reuse` cuando:
- El refresh JWT es válido en firma.
- Existe fila en BD con `is_revoked=1`.
- `is_revoked_refresh_reuse_candidate(row)` es True:
  - `revoked_reason == SESSION_ROTATED`, o
  - `revoked_reason IS NULL` (legacy)

Acción: revocar **todas** las sesiones del usuario + blacklist access + auditoría + 401.

### SESSION_ROTATED

Motivo escrito **únicamente** por `SQL_REVOKE_OLD_FOR_ROTATION` dentro de `rotate_refresh_token_core`. Indica rotación legítima completada; el token antiguo no debe reutilizarse (salvo suppress en refresh).

### suppress_session_rotated_reuse

Parámetro de `get_current_user_from_refresh` activado **solo** en `get_current_user_for_refresh_endpoint`.

**Por qué existe:** en F5 concurrente, el perdedor llega con el refresh ya marcado SESSION_ROTATED. Sin suppress, se interpretaría como ataque TOKEN_REUSE y se cerrarían todas las sesiones del usuario.

Con suppress: Depends falla con 401 limpio; el handler puede retornar `ALREADY_ROTATED` con access nuevo sin actualizar cookie.

---

## 14. Redis

### session_access_jti

| Propiedad | Valor |
|-----------|-------|
| Prefijo | `session:access_jti:` |
| Clave completa | `session:access_jti:{token_id}` |
| Valor | JSON `{"jti": "...", "exp": <int\|null>}` |
| TTL | Hasta expiración del access (mín. 60 s) |
| Escritura | fail-soft (warning en log) |
| Lectura blacklist | fail-soft |

### Blacklist

| Propiedad | Valor |
|-----------|-------|
| Prefijo | `blacklist:token:` |
| Clave completa | `blacklist:token:{jti}` |
| Valor | `"revoked"` |
| TTL | `max(exp - now, 60)` segundos; default 900 s si sin exp |
| Lectura en deps | fail-soft → token **no** considerado revocado |

### Si Redis no está disponible

| Operación | Comportamiento |
|-----------|----------------|
| `is_token_blacklisted` | Retorna `False` → access sigue válido |
| `set_token_blacklist` | Log warning, no lanza excepción |
| `link_session_access_jti` | Log warning, sesión refresh OK sin mapping |
| `blacklist_access_for_*` | Retorna 0 / False, revocación refresh en BD sigue |

Redis se activa con `ENABLE_REDIS_CACHE=true` en configuración.

---

## 15. Refresh Tokens — estados y transiciones

### Campos relevantes

| Campo | Descripción |
|-------|-------------|
| `is_revoked` | 0 = activo, 1 = revocado |
| `revoked_reason` | Motivo canónico (`RevokedReason`) |
| `expires_at` | Expiración absoluta del refresh |
| `last_used_at` | Última actividad (idle) |
| `token_hash` | SHA-256 del JWT refresh (no se almacena el JWT) |

### Motivos de revocación (RevokedReason)

| Valor | Origen en código |
|-------|------------------|
| `USER_LOGOUT` | `perform_logout` |
| `LOGOUT_ALL` | `revoke_all_user_tokens` (default) |
| `ADMIN_REVOKE` | `revoke_refresh_token_by_id` |
| `PASSWORD_CHANGE` | `PasswordChangeService` |
| `USER_DEACTIVATED` | `user_service` al desactivar usuario |
| `USER_DELETED` | `user_service` al eliminar usuario |
| `TOKEN_REUSE` | `handle_revoked_refresh_reuse` |
| `SESSION_ROTATED` | `rotate_refresh_token_core` |
| `IDLE_TIMEOUT` | `validate_refresh_token` o rotate core |
| `SESSION_LIMIT` | `enforce_max_active_sessions` |

### Diagrama de transiciones

```
                    ┌─────────────┐
         login/     │   ACTIVO    │◄── store(is_rotation=False)
         seleccionar │ is_revoked=0│
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
  SESSION_ROTATED   USER_LOGOUT      IDLE_TIMEOUT
  (rotate core)     LOGOUT_ALL       TOKEN_REUSE
                    PASSWORD_CHANGE  SESSION_LIMIT
                    ADMIN_REVOKE     EXPIRED (expires_at)
                    USER_DEACTIVATED
                    USER_DELETED
         │                 │                 │
         └─────────────────┴─────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  REVOCADO   │
                    │ is_revoked=1│
                    └─────────────┘
```

### Múltiples refresh activos

**Permitido por diseño:** un usuario puede tener N filas activas (multi-dispositivo), acotado por `max_active_sessions` en login/nueva sesión.

---

## 16. Concurrencia

### UPDLOCK + UnitOfWork

Garantiza que dos requests de rotación sobre el mismo `token_hash` se serialicen. El primero completa INSERT+REVOKE; el segundo encuentra `is_revoked=1` + `SESSION_ROTATED` → `ALREADY_ROTATED`.

### F5 concurrente (refresh)

| Request | Depends | Rotate | Cookie refresh | Access |
|---------|---------|--------|----------------|--------|
| Ganador | OK | ROTATED | Actualizada | Nuevo |
| Perdedor | OK (suppress) | ALREADY_ROTATED | **Sin cambio** | Nuevo |

El perdedor puede usar el access hasta expirar; el siguiente refresh con cookie antigua → 401.

### Refresh simultáneo (N requests)

Mismo comportamiento: 1× ROTATED, (N-1)× ALREADY_ROTATED. Tests: `test_concurrent_refresh_only_one_rotation_commits_refresh`.

### Cambio empresa simultáneo

Rotate compartido con refresh (mismo UPDLOCK por hash). **Diferencia:** perdedores ALREADY_ROTATED reciben **cookie con refresh JWT no persistido** vía `_session_token_http_response` (asimetría documentada en limitaciones).

### Logout mientras refresh

Logout revoca refresh; refresh en vuelo → `ALREADY_REVOKED` o `NOT_FOUND` → 401.

### Password mientras refresh

`revoke_all` invalida todos los refresh; refresh concurrente falla post-revoke.

---

## 17. Garantías

| # | Garantía |
|---|----------|
| ✓ | Rotación atómica: INSERT + REVOKE SESSION_ROTATED en una UoW |
| ✓ | No INSERT sin REVOKE en rotación atómica (RuntimeError + rollback si revoke falla) |
| ✓ | UPDLOCK serializa rotaciones concurrentes sobre el mismo token |
| ✓ | Filtrado `cliente_id` en todas las queries de refresh_tokens |
| ✓ | Refresh inválido/revocado en BD → 401 (no emite tokens nuevos en Depends) |
| ✓ | TOKEN_REUSE cierra todas las sesiones del usuario ante reuse malicioso |
| ✓ | suppress_session_rotated_reuse evita falso TOKEN_REUSE en F5 |
| ✓ | Logout idempotente HTTP 200 |
| ✓ | Idle timeout revoca con motivo IDLE_TIMEOUT persistido |
| ✓ | Session limit revoca sesiones más antiguas antes de insertar nueva |
| ✓ | Password change deja una sola sesión refresh activa |
| ✓ | empresa_id en refresh tomada de BD como fuente de verdad |
| ✓ | Impersonación bloqueada en refresh (403) y cambiar empresa (403) |

---

## 18. Limitaciones conocidas

Solo deudas certificadas en código. **Sin propuestas de solución.**

### P1

| ID | Descripción |
|----|-------------|
| L-01 | En `POST /auth/refresh/`, `rotate_refresh_token_service` usa `cliente_id` de `current_user` (tabla usuario/contexto), mientras `validate_refresh_token` en Depends usa `token_cliente_id` del JWT. En `database_type=="multi"` puede divergir → outcome `NOT_FOUND` tras Depends exitoso. |
| L-02 | En `POST /auth/empresa/cambiar/`, outcome `ALREADY_ROTATED` retorna 200 con refresh JWT en cookie/body **sin** haberlo persistido en BD (a diferencia de refresh, que no actualiza cookie). Próximo refresh puede fallar con 401. |

### P2

| ID | Descripción |
|----|-------------|
| L-03 | Fallback cambiar empresa sin `old_refresh_token`: `store(is_rotation=True)` inserta nuevo refresh **sin revocar** el anterior → pueden coexistir dos refresh activos para la misma sesión lógica. |
| L-04 | SSO Azure/Google no invoca `link_session_access_jti`; logout/password/admin no blacklistean access vía mapping Redis para esas sesiones. |
| L-05 | Activity tracking duplicado en refresh: `validate_refresh_token` incrementa `uso_count` y `rotate_refresh_token_core` lo vuelve a incrementar en la misma operación. |

### P3

| ID | Descripción |
|----|-------------|
| L-06 | Login/SSO: fallo en `store_refresh_token` no aborta login (access emitido sin fila BD). |
| L-07 | Redis fail-soft: access blacklisteado puede seguir aceptándose si Redis cae en lectura. |
| L-08 | `logout_all`: access actual válido hasta expiración natural. |
| L-09 | Perdedor F5 en refresh: access temporal sin refresh renovado → sesión termina al expirar access. |

---

## 19. Contrato para Frontend

### Identificación de cliente

| Header | Valor | Efecto |
|--------|-------|--------|
| `X-Client-Type` | `web` (default) | Refresh en cookie HttpOnly |
| `X-Client-Type` | `mobile` | Refresh en JSON body |

Cookie refresh: nombre `refresh_token` (`settings.REFRESH_COOKIE_NAME`).  
Atributos: `HttpOnly`, `Secure`, `SameSite` según entorno, `domain` configurable.

### Access token

- Enviar en **`Authorization: Bearer <access_token>`** en todas las llamadas autenticadas.
- No almacenar en cookie para API calls (salvo convención propia del frontend).
- Tras refresh exitoso (`ROTATED`): **reemplazar** access en memoria/storage inmediatamente.
- Tras `ALREADY_ROTATED`: usar el **nuevo access** de la respuesta; **no** asumir que el refresh cambió (web: cookie intacta; mobile: body sin refresh nuevo).

### Refresh

- **Web:** `POST /api/v1/auth/refresh/` con cookie; no enviar refresh en body salvo fallback.
- **Mobile:** incluir `refresh_token` en body JSON.
- Ante **401** con mensaje de sesión expirada → redirigir a login; **no** reintentar refresh en bucle.
- Ante **403** en refresh (impersonación) → finalizar impersonación o reiniciar flujo soporte.
- **No** disparar múltiples refresh en paralelo intencionalmente; si ocurre (F5), aceptar que solo uno rota; los demás reciben access sin refresh nuevo.

### Logout

- `POST /api/v1/auth/logout/` — siempre tratar como éxito (200).
- Enviar cookie refresh (web) o body refresh (mobile).
- Opcional: enviar Bearer access para blacklist inmediato.
- Limpiar access y refresh en el cliente aunque el backend ya borró cookies.

### Logout All

- `POST /api/v1/auth/logout_all/` con Bearer access.
- Tras 200: **redirigir a login inmediatamente**; el access actual aún funciona hasta expirar — no confiar en él para operaciones prolongadas.

### Cambio Empresa

- `POST /api/v1/auth/empresa/cambiar/` con Bearer access + `empresa_id`.
- **Web:** asegurar que la cookie refresh viaja (same-site, dominio).
- **Mobile:** enviar `refresh_token` en body.
- Tras 200: reemplazar access, user_data y refresh (web actualiza cookie automáticamente).
- Si 401 → sesión inválida; login completo.
- No llamar si `empresa_selection_pending=true` (409) — completar selección primero.

### Seleccionar Empresa

- Usar `selection_token` del login multi-empresa, **no** access de sesión normal.
- Tras 200: transición a sesión completa con refresh.

### Session Expired / Idle Timeout / 401

Mensaje típico refresh:
> "Sesión expirada o cerrada remotamente. Por favor, vuelva a iniciar sesión."

Acción frontend:
1. Limpiar tokens locales.
2. Redirigir a login.
3. No reintentar la operación fallida con el mismo refresh.

Idle timeout es transparente para el frontend (mismo 401); no hay header específico de idle.

### TOKEN_REUSE

Si el backend detecta reuse malicioso → 401 con mensaje de seguridad; **todas** las sesiones del usuario quedan revocadas. Frontend debe forzar login en todos los dispositivos.

### Reintentos

| Situación | Reintento |
|-----------|-----------|
| Refresh 401 | No — login |
| Refresh 500 | Máx. 1 retry con backoff; luego login |
| Logout | Idempotente — safe retry |
| ALREADY_ROTATED | No retry refresh inmediato — usar access recibido |

### 403 vs 401

| Código | Significado típico |
|--------|-------------------|
| 401 | Sesión inválida, expirada, revocada, reuse |
| 403 | Impersonación sin refresh; token de otro tenant; cambiar empresa en impersonación |

---

## 20. Diagramas

### Login (sesión directa)

```
[Usuario] → POST /login/
              │
              ├─► Validar credenciales
              ├─► create_access_token + create_refresh_token
              ├─► INSERT refresh_tokens (+ session limit)
              ├─► Redis link session:access_jti
              ├─► Set-Cookie (web) / body refresh (mobile)
              └─► 200 Token + user_data
```

### Refresh

```
[Cliente] → POST /refresh/
              │
              ├─► Depends: validate_refresh_token
              │       ├─ idle? → revoke → 401
              │       └─ OK → activity
              │
              ├─► create new access + refresh JWT
              ├─► UoW: UPDLOCK → INSERT → UPDATE SESSION_ROTATED
              │
              ├─► ROTATED → cookie/body + link Redis
              ├─► ALREADY_ROTATED → access only
              └─► otros → 401
```

### Logout

```
[Cliente] → POST /logout/
              │
              ├─► revoke refresh (USER_LOGOUT)
              ├─► blacklist access (opcional)
              ├─► delete cookies
              └─► 200 siempre
```

### Password Change

```
[Cliente] → POST /password/change/ + Bearer
              │
              ├─► revoke_all PASSWORD_CHANGE
              ├─► blacklist all access
              ├─► nueva sesión (access + refresh)
              ├─► INSERT refresh_tokens
              └─► 200 Token
```

### Cambio Empresa

```
[Cliente] → POST /empresa/cambiar/ + Bearer + refresh
              │
              ├─► emitir tokens con empresa_id nueva
              │
              ├─► [con refresh] rotate_refresh_token_service
              │       ├─ ROTATED → OK + cookie
              │       ├─ ALREADY_ROTATED → 200 (ver L-02)
              │       └─ error → 401
              │
              └─► [sin refresh] store(is_rotation=True) → 200
```

### Session Lifecycle

```
┌────────┐   login/seleccionar   ┌────────┐   refresh (rotate)   ┌────────┐
│  none  │ ───────────────────► │ ACTIVO │ ──────────────────► │ ACTIVO │
└────────┘                      └───┬────┘   (nuevo token_id)   └────┬───┘
                                    │                                 │
                         logout / idle / reuse / password / admin     │
                                    ▼                                 │
                               ┌─────────┐                            │
                               │REVOCADO │◄───────────────────────────┘
                               └─────────┘         (token anterior
                                                    SESSION_ROTATED)
```

---

## 21. Glosario

| Término | Definición |
|---------|------------|
| **Refresh** | JWT de larga duración almacenado en BD por hash; renueva la sesión vía `POST /auth/refresh/` |
| **Rotation** | Sustitución atómica de un refresh activo por uno nuevo; el anterior queda `SESSION_ROTATED` |
| **Reuse** | Reenvío de un refresh ya revocado; tratado como incidente de seguridad (`TOKEN_REUSE`) salvo suppress |
| **Idle** | Inactividad superior a `session_idle_timeout_minutes` sin uso del refresh |
| **Blacklist** | Entrada Redis que invalida un access `jti` antes de su expiración natural |
| **UPDLOCK** | Hint SQL Server de bloqueo de fila durante rotación concurrente |
| **Session** | Fila en `refresh_tokens` + JWT access/refresh asociados |
| **Token Mapping** | Redis `session:access_jti:{token_id}` → access `jti` vigente |
| **JTI** | JWT ID único por token; usado para revocación de access |
| **Selection token** | Access JWT temporal post-login multi-empresa con `empresa_selection_pending` |
| **UnitOfWork** | Contexto transaccional SQL; commit único o rollback completo |
| **Fail-soft** | Fallo en Redis no aborta operación principal |
| **cliente_id** | UUID del tenant; filtra todas las operaciones de sesión |
| **empresa_id** | Empresa activa en la sesión; en refresh prevalece BD sobre JWT |

---

## 22. Estado del dominio

| Atributo | Valor |
|----------|-------|
| **Versión arquitectónica** | IAM Session Management V2 |
| **Estado** | Production Ready (P1-04 cerrado) |
| **Fases implementadas** | P1-01 (reuse), P1-02 (idle), P1-03 (session limit), P1-04 (rotación atómica), HOTFIX-01 (USER_MISMATCH UUID), CLEANUP-01 (eliminación TRACE) |
| **Fecha documento** | 2026-06-17 |
| **Fuente de verdad código** | `app/modules/auth/`, `app/infrastructure/database/queries/auth/`, `app/api/deps.py` |
| **Tests de referencia** | `tests/unit/test_iam_sessions_p*.py`, `test_iam_sessions_pa001.py` |

Esta documentación corresponde al **estado posterior a P1-04** y refleja exclusivamente el comportamiento del código desplegado en el repositorio al momento de su generación.

---

*Generado bajo IAM-BE-DOCS-SESSION-V2-01 — DOCUMENTATION ONLY.*
