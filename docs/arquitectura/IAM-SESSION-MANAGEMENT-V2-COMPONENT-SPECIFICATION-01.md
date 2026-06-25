# IAM Session Management V2 — Especificación Técnica de Componentes

**Ticket:** IAM-BE-COMPONENT-SPEC-01  
**Versión:** 1.0.0  
**Estado:** Especificación oficial (pre-implementación)  
**Fecha:** 2026-06-22  
**Audiencia:** Backend, QA, arquitectura  

**Documentos normativos de entrada:**

| Documento | Rol |
|-----------|-----|
| `IAM-SESSION-MANAGEMENT-V2-IMPACT-ANALYSIS-01.md` | Análisis de impacto |
| `IAM-SESSION-MANAGEMENT-V2-DESIGN-01.md` | Diseño arquitectónico |
| `tables_session_management_new.sql` (v3) | Modelo de datos inmutable |

**Restricción:** Este documento es especificación funcional y técnica. Sin código, sin migraciones, sin cambios en archivos del proyecto.

---

## Índice

1. [Convenciones de especificación](#1-convenciones-de-especificación)
2. [Catálogo de componentes](#2-catálogo-de-componentes)
3. [Servicios de comando (writes)](#3-servicios-de-comando-writes)
4. [Servicios de consulta (reads)](#4-servicios-de-consulta-reads)
5. [Servicios de orquestación e infraestructura adyacente](#5-servicios-de-orquestación-e-infraestructura-adyacente)
6. [Capa de queries (infrastructure)](#6-capa-de-queries-infrastructure)
7. [Tipos de dominio ligero y mappers](#7-tipos-de-dominio-ligero-y-mappers)
8. [Matriz global de responsabilidades](#8-matriz-global-de-responsabilidades)

---

## 1. Convenciones de especificación

Cada componente documenta **20 atributos** obligatorios:

| # | Atributo | Descripción |
|---|----------|-------------|
| 1 | Objetivo | Propósito del componente |
| 2 | Responsabilidad | Qué hace y qué no hace |
| 3 | Alcance | Límites funcionales |
| 4 | Entradas | Parámetros, DTOs, contexto |
| 5 | Salidas | Resultados, efectos |
| 6 | Dependencias | Componentes externos requeridos |
| 7 | Queries utilizadas | Funciones `*_core` / transacciones |
| 8 | Servicios que consume | Capa application |
| 9 | Servicios que lo consumen | Callers |
| 10 | Redis utilizado | Claves y operaciones |
| 11 | Auditoría generada | Eventos `auth_audit_log` |
| 12 | Transacciones requeridas | UoW sí/no; detalle |
| 13 | Eventos de negocio | Semántica dominio |
| 14 | Excepciones | Clases de `app/core/exceptions.py` |
| 15 | Restricciones | Reglas técnicas inviolables |
| 16 | Reglas de negocio | Lógica funcional |
| 17 | Casos borde | Escenarios límite |
| 18 | Casos de concurrencia | Locks, carreras |
| 19 | Casos de seguridad | Amenazas mitigadas |
| 20 | Casos de prueba mínimos | Cobertura QA obligatoria |

**Valores estándar cuando no aplica:**

- Redis: `N/A`
- Auditoría: `N/A` (delegada a caller o `SessionAuditEmitter`)
- UoW: `No` para reads puros

---

## 2. Catálogo de componentes

| ID | Componente | Capa | Tipo |
|----|------------|------|------|
| C01 | `SessionCreationService` | Application | Command |
| C02 | `SessionRotationService` | Application | Command |
| C03 | `SessionRevocationService` | Application | Command |
| C04 | `SessionPolicyService` | Application | Command/Policy |
| C05 | `BusinessActivityService` | Application | Command (light) |
| C06 | `SessionRedisBridge` | Application | Infra bridge |
| C07 | `SessionAuditEmitter` | Application | Infra bridge |
| C08 | `SessionQueryService` | Application | Query |
| C09 | `ActiveSessionsReadService` | Application | Query |
| C10 | `SessionProbeService` | Application | Query |
| C11 | `auth_service` (alcance sesión) | Application | Orchestrator |
| C12 | `password_change_service` (alcance sesión) | Application | Orchestrator |
| C13 | `impersonation_service` (integración sesión) | Application | Orchestrator |
| C14 | `refresh_token_cleanup_job` | Application | Job |
| C15 | `user_session_queries_core` | Infrastructure | Queries |
| C16 | `token_family_queries_core` | Infrastructure | Queries |
| C17 | `refresh_token_queries_core` | Infrastructure | Queries |
| C18 | `session_transaction_core` | Infrastructure | Transactions |
| C19 | `SessionDomainTypes` | Application | Types/Enums |
| C20 | `SessionReadMapper` | Application | Mapper |
| C21 | `active_session_read_columns` | Application | Config |

---

## 3. Servicios de comando (writes)

### C01 — SessionCreationService

**Ruta objetivo:** `app/modules/auth/application/services/session_creation_service.py`

#### 1. Objetivo
Crear una sesión lógica completa en login o post-cambio de contraseña: `user_session` + `token_family` + primer `refresh_token`, de forma atómica.

#### 2. Responsabilidad
- Orquestar `create_session_with_token_tx`.
- Calcular `expires_at` de sesión según `remember_me` y `cliente_auth_config`.
- Persistir metadata dispositivo en `user_session`.
- Actualizar `empresa_id` y `selection_token_completed` en flujo selección empresa.
- **No** emite JWT (delegado a `auth_service`).
- **No** aplica session limit (delegado a `SessionPolicyService` pre-call).

#### 3. Alcance
- `create(...)` — login, password change.
- `update_empresa(...)` — post `selection_token`.
- Excluye rotación RTR y revocación.

#### 4. Entradas

| Método | Entrada |
|--------|---------|
| `create` | `usuario_id`, `cliente_id`, `empresa_id?`, `login_method`, `device_context` (platform, device_name, device_id, fingerprint, user_agent, login_ip), `remember_me`, `token_hash`, `token_expires_at`, `refresh_token_days` |
| `update_empresa` | `session_id`, `cliente_id`, `empresa_id`, `selection_token_completed`, opcional `token_id` para sync empresa en token vigente |

#### 5. Salidas
- `SessionCreationResult`: `session_id`, `family_id`, `token_id`, `expires_at`.
- `update_empresa`: void.

#### 6. Dependencias
- `session_transaction_core.create_session_with_token_tx`
- `user_session_queries_core.update_session_empresa_core` (update_empresa sin rotación)
- `auth_config_service` (TTL)
- `UnitOfWork`

#### 7. Queries utilizadas
- `create_session_with_token_tx` (compone insert session, family, token, update current_token_id)
- `update_session_empresa_core`

#### 8. Servicios que consume
- Ninguno de aplicación (solo infra + config).

#### 9. Servicios que lo consumen
- `auth_service` (login, empresa/seleccionar)
- `password_change_service`

#### 10. Redis utilizado
N/A (caller hace `link_access` post-JWT).

#### 11. Auditoría generada
N/A directamente — `auth_service` emite `login_success` vía `SessionAuditEmitter`.

#### 12. Transacciones requeridas
**Sí — obligatorio** `UnitOfWork` en `create` vía `create_session_with_token_tx`.  
`update_empresa` sin rotación: UoW si actualiza sesión + token en una operación; single UPDATE aceptable sin UoW si solo sesión.

#### 13. Eventos de negocio
- `SessionCreated` — nueva sesión lógica.
- `SessionEmpresaUpdated` — empresa asignada post-selection.

#### 14. Excepciones que puede producir
- `DatabaseError` — fallo tx.
- `ValidationError` — device_context incompleto, TTL inválido.

#### 15. Restricciones
- Siempre `cliente_id` en tx.
- `login_ip` inmutable post-create.
- Un `token_family` por sesión en creación.
- `parent_token_id=NULL` en primer token.

#### 16. Reglas de negocio
- `platform` ∈ {web, mobile, desktop, api}.
- `login_method` ∈ {password, sso, 2fa, api_key}.
- `selection_token_completed=0` si empresa asignada en login directo.
- `empresa_id` nullable si multi-empresa pendiente selección.

#### 17. Casos borde
- `empresa_id=NULL` en create — válido (multi-empresa).
- `device_id=NULL` — permitido; sin reuso dispositivo.
- `remember_me=false` — `expires_at` = now + session_timeout_minutes.
- Fallo después de INSERT session pero antes de token — rollback total.

#### 18. Casos de concurrencia
- Dos logins simultáneos mismo usuario: cada uno crea sesión independiente; session limit manejado antes por C04.

#### 19. Casos de seguridad
- `token_hash` nunca almacenado en claro.
- `device_fingerprint` almacena hash SHA-256, no JSON crudo.

#### 20. Casos de prueba mínimos
- Create atómico: 3 filas creadas + `current_token_id` poblado.
- Rollback si falla insert token.
- `update_empresa` setea `selection_token_completed=1`.
- TTL remember_me vs session_timeout.
- `login_ip` no cambia en update posterior.

---

### C02 — SessionRotationService

**Ruta objetivo:** `app/modules/auth/application/services/session_rotation_service.py`

#### 1. Objetivo
Ejecutar Refresh Token Rotation (RTR) atómico y manejar detección de replay attacks.

#### 2. Responsabilidad
- Pre-validar vía `SessionQueryService` + `SessionPolicyService`.
- Ejecutar `rotate_refresh_token_tx` o `handle_replay_attack_tx`.
- Actualizar actividad sesión (`last_refresh_at`, `last_seen_ip`).
- Propagar `empresa_id` en rotación por cambio empresa.
- **No** emite JWT.
- **No** evalúa credenciales login.

#### 3. Alcance
- `rotate(...)` — refresh, cambiar empresa.
- `handle_replay(...)` — compromiso familia.

#### 4. Entradas
`token_hash`, `cliente_id`, `usuario_id` (validación), `new_token_hash`, `new_token_expires_at`, `request_ip`, `empresa_id?` (cambio empresa), contexto idle desde config.

#### 5. Salidas
- `RotateResult`: `outcome`, `session_id`, `family_id`, `old_token_id`, `new_token_id`, `success`.
- `ReplayDetectionResult` en replay.

#### 6. Dependencias
- `session_transaction_core.rotate_refresh_token_tx`, `handle_replay_attack_tx`
- `SessionQueryService`, `SessionPolicyService`
- `SessionRedisBridge`, `SessionAuditEmitter` (vía caller o interno en replay)
- `UnitOfWork`

#### 7. Queries utilizadas
- `rotate_refresh_token_tx` (LOCK, INSERT, UPDATE family, MARK used, UPDATE session)
- `handle_replay_attack_tx`
- `revoke_session_tx` (idle path — o delegado a C03)

#### 8. Servicios que consume
- `SessionQueryService`, `SessionPolicyService`
- Opcional `SessionRevocationService` para idle revoke

#### 9. Servicios que lo consumen
- `auth_service` (refresh, empresa/cambiar)

#### 10. Redis utilizado
Indirecto: caller invoca `blacklist_session` en replay; `link_access` post-rotate.

#### 11. Auditoría generada
- `refresh_success` (caller).
- `replay_detected` (en `handle_replay`).
- `idle_timeout` si revoca por idle.

#### 12. Transacciones requeridas
**Sí — obligatorio** UoW para rotate y replay. Una tx por operación.

#### 13. Eventos de negocio
- `RefreshTokenRotated`
- `ReplayAttackDetected`
- `SessionIdleExpired`

#### 14. Excepciones que puede producir
- `AuthenticationError` — token inválido, replay, idle, expirado (401).
- `DatabaseError` — fallo tx.
- Outcomes no excepción: `RotateOutcome.NOT_FOUND`, `EXPIRED`, `ALREADY_USED` mapeados a 401 por caller.

#### 15. Restricciones
- `UPDLOCK, ROWLOCK` en token por hash dentro de tx.
- Orden: INSERT nuevo → UPDATE `current_token_id` → MARK old `is_used=1`.
- `current_token_id` solo actualizable dentro de rotate tx.
- Impersonación refresh: bloqueado en `auth_service` (403) — no entra aquí.

#### 16. Reglas de negocio
- Token vigente: `is_used=0`, `is_revoked=0`, `expires_at>now`.
- Familia: `is_compromised=0`.
- Sesión: `is_active=1`, `expires_at>now`.
- Token `is_used=1` presentado → replay (no rotación).
- Idle sobre `last_refresh_at` (o `created_at` si null).

#### 17. Casos borde
- Primer refresh tras login (`last_refresh_at` null) — idle usa `created_at`.
- Token expirado pero sesión activa — rechazar rotate.
- Sesión expirada TTL absoluto — rechazar antes de rotate.
- `empresa_id` cambia en rotate — actualizar sesión + nuevo token.
- Refresh con mismo hash dos veces seguidas — segundo es replay.

#### 18. Casos de concurrencia
- **Dos refresh concurrentes mismo token:** segundo bajo lock ve `is_used=1` → `handle_replay_attack_tx`.
- **Refresh concurrente tras rotación exitosa:** primero rota; segundo con old hash → replay.

#### 19. Casos de seguridad
- Replay cierra solo sesión comprometida, no todas del usuario.
- Mensaje cliente genérico en replay (no revelar `is_used`).
- No emitir token si tx incompleta.

#### 20. Casos de prueba mínimos
- Rotación exitosa: new token, old `is_used=1`, `current_token_id` actualizado.
- Replay: `is_compromised=1`, sesión cerrada, tokens revocados.
- Concurrencia doble refresh → replay en segundo.
- Idle expired → sesión cerrada, 401.
- USER_MISMATCH si `usuario_id` no coincide.
- Cambio `empresa_id` en rotate.

---

### C03 — SessionRevocationService

**Ruta objetivo:** `app/modules/auth/application/services/session_revocation_service.py`

#### 1. Objetivo
Cerrar sesiones lógicas: logout, logout all, self-revoke, admin revoke, evicción por session limit.

#### 2. Responsabilidad
- Ejecutar `revoke_session_tx` y `revoke_all_user_sessions_tx`.
- Resolver `session_id` desde `token_hash` o path param (con alias `token_id` transitorio).
- Idempotencia en logout/self-revoke.
- Coordinar blacklist Redis post-revoke.
- **No** detecta replay (C02).
- **No** crea sesiones.

#### 3. Alcance
- `revoke_current(token_hash)`
- `revoke_by_session_id(session_id, initiator)`
- `revoke_all_for_user(usuario_id)`
- `revoke_for_limit(session_id)` — evicción

#### 4. Entradas
`cliente_id`, `usuario_id` (ownership), `session_id` o `token_hash`, `RevokedReason`, `initiator` (user|admin|system), metadata request (IP, UA).

#### 5. Salidas
- `RevokeResult`: `session_id`, `was_active`, `already_revoked`.
- `revoke_all`: `int` count.

#### 6. Dependencias
- `session_transaction_core.revoke_session_tx`, `revoke_all_user_sessions_tx`
- `SessionQueryService` (resolver hash → session)
- `SessionRedisBridge`
- `SessionAuditEmitter`
- `UnitOfWork`

#### 7. Queries utilizadas
- `revoke_session_tx` (close session, invalidate family, revoke tokens)
- `revoke_all_user_sessions_tx`
- `get_refresh_token_by_hash_any_state_core` (resolver)

#### 8. Servicios que consume
- `SessionQueryService`, `SessionRedisBridge`, `SessionAuditEmitter`

#### 9. Servicios que lo consumen
- `auth_service` (logout, logout_all)
- `endpoints` (self-revoke, admin revoke)
- `SessionPolicyService` (evicción)
- `password_change_service`
- `user_service` (deactivate/delete)
- `SessionRotationService` (idle revoke)

#### 10. Redis utilizado
- `SessionRedisBridge.blacklist_session(session_id)`
- `blacklist_all_user_sessions(usuario_id)`

#### 11. Auditoría generada
- `logout`, `logout_all`, `session_revoked`, `session_admin_revoked`, `session_limit_evicted`, `idle_timeout`, `session_expired`

#### 12. Transacciones requeridas
**Sí** — UoW por `revoke_session_tx`.  
Logout all: UoW única si sesiones < 20; chunks si más (D-08 design).

#### 13. Eventos de negocio
- `SessionRevoked`
- `AllSessionsRevoked`

#### 14. Excepciones que puede producir
- `NotFoundError` — sesión inexistente o cross-tenant (404).
- `AuthorizationError` — self-revoke sesión ajena (403) — validado en endpoint.
- `DatabaseError` — fallo tx.
- Logout: **no** lanza si ya revocada (idempotente → éxito silencioso).

#### 15. Restricciones
- Filtrar `cliente_id` siempre.
- Self-revoke: ownership `usuario_id` debe coincidir.
- Admin revoke: sesión ya cerrada → 404 (no idempotente admin).
- Self-revoke RC1: ya cerrada mismo usuario → 200 idempotente.

#### 16. Reglas de negocio
- Cerrar sesión → `is_active=0`, `revoked_reason` según mapping §C07.
- Familia → `invalidation_reason='session_revoked'` o equivalente.
- Tokens activos de sesión → `is_revoked=1`.

#### 17. Casos borde
- Logout sin refresh cookie — 200 idempotente.
- Revoke por `token_id` alias cuando FE envía token_id vigente — resolver a `session_id`.
- Usuario sin sesiones activas en logout_all — count=0, 200.
- Revoke sesión ya expirada por TTL — idempotente user / 404 admin.

#### 18. Casos de concurrencia
- Doble logout concurrente: segunda idempotente.
- Logout mientras refresh en vuelo: uno gana; el otro falla o idempotente.

#### 19. Casos de seguridad
- Cross-tenant revoke → 404 (no 403).
- No exponer existencia sesión otro usuario en self-revoke.

#### 20. Casos de prueba mínimos
- Logout idempotente.
- Self-revoke ownership 404 ajeno.
- Admin revoke 404 sesión cerrada.
- Logout all cierra N sesiones.
- Redis blacklist invocado.
- Audit eventos correctos.
- Evicción session limit.

---

### C04 — SessionPolicyService

**Ruta objetivo:** `app/modules/auth/application/services/session_policy_service.py`

#### 1. Objetivo
Aplicar políticas configurables por tenant: session limit e idle timeout de autenticación.

#### 2. Responsabilidad
- `enforce_limit` pre-login.
- `check_idle` pre-rotate.
- `check_absolute_ttl` — validación expiración sesión.
- Leer políticas desde `auth_config_service`.
- **No** persiste tokens directamente (delega revoke a C03).

#### 3. Alcance
Políticas de `cliente_auth_config`: `max_active_sessions`, `session_idle_timeout_minutes`. No gestiona `refresh_token_days` (C01/C02).

#### 4. Entradas
`usuario_id`, `cliente_id`, `session_row` (para idle), `last_refresh_at`, `expires_at`.

#### 5. Salidas
- `enforce_limit`: `int` evicted count.
- `check_idle`: `bool` expired.
- `check_absolute_ttl`: `bool` expired.

#### 6. Dependencias
- `user_session_queries_core` (count, list oldest)
- `auth_config_service`
- `SessionRevocationService` (evicción)

#### 7. Queries utilizadas
- `count_active_sessions_core`
- `list_active_sessions_oldest_first_core`
- `is_session_idle_expired_core`
- `is_session_absolute_expired_core`

#### 8. Servicios que consume
- `SessionRevocationService`, `auth_config_service`

#### 9. Servicios que lo consumen
- `auth_service` (pre-login)
- `SessionRotationService` (pre-rotate)

#### 10. Redis utilizado
Indirecto vía C03 en evicción: `blacklist_session`.

#### 11. Auditoría generada
- `session_limit_evicted` por cada sesión evictada (vía C03/C07).

#### 12. Transacciones requeridas
No directamente — cada evicción usa UoW de C03. `enforce_limit` puede ejecutar N transacciones secuenciales.

#### 13. Eventos de negocio
- `SessionLimitEnforced`
- `SessionIdleExpired`

#### 14. Excepciones que puede producir
- `DatabaseError` en queries.
- No lanza 401 — caller interpreta idle/TTL.

#### 15. Restricciones
- `max_active_sessions` null → sin límite (o default 3 según config).
- `session_idle_timeout_minutes` null o ≤0 → idle deshabilitado.

#### 16. Reglas de negocio
- Cuenta sesiones con `is_active=1` y `expires_at>now`.
- Evict oldest first (`created_at ASC`).
- Idle: `DATEDIFF(minute, COALESCE(last_refresh_at, created_at), now) > policy`.

#### 17. Casos borde
- `max_active_sessions=0` o negativo — tratar como sin límite o ValidationError (definir en impl: usar default 3).
- Usuario con exactamente N sesiones, login N+1 — evict 1.
- Idle deshabilitado — `check_idle` siempre false.

#### 18. Casos de concurrencia
- Dos logins simultáneos cerca del límite — pueden evictar de más temporalmente; aceptable.

#### 19. Casos de seguridad
- Evicción cierra sesión completa (no solo token).

#### 20. Casos de prueba mínimos
- Limit evicts oldest.
- No evict si bajo límite.
- Idle true/false según `last_refresh_at`.
- Absolute TTL expired.
- Config null handling.

---

### C05 — BusinessActivityService

**Ruta objetivo:** `app/modules/auth/application/services/business_activity_service.py`

#### 1. Objetivo
Actualizar `last_business_activity_at` con throttle de 5 minutos en requests ERP autenticados.

#### 2. Responsabilidad
- `touch(session_id, cliente_id)` fail-soft.
- Evaluar throttle antes de WRITE.
- **No** revoca sesiones.
- **No** actualiza `last_refresh_at`.

#### 3. Alcance
Solo invocado desde `deps.py` `get_current_user` cuando access JWT incluye claim `sid`.

#### 4. Entradas
`session_id` (UUID), `cliente_id`, opcional `last_business_activity_at` cacheada.

#### 5. Salidas
void — sin retorno funcional.

#### 6. Dependencias
- `touch_business_activity_core`
- Contexto tenant

#### 7. Queries utilizadas
- `touch_business_activity_core`
- Lectura previa opcional: `get_active_session_by_id_core` (solo si no hay cache)

#### 8. Servicios que consume
Ninguno.

#### 9. Servicios que lo consumen
- `app/api/deps.py`

#### 10. Redis utilizado
N/A

#### 11. Auditoría generada
N/A

#### 12. Transacciones requeridas
**No** — autocommit single UPDATE.

#### 13. Eventos de negocio
- `BusinessActivityRecorded` (interno, no audit log V2 inicial)

#### 14. Excepciones que puede producir
Ninguna hacia caller — fail-soft, log warning.

#### 15. Restricciones
- Throttle mínimo 5 minutos entre writes.
- No ejecutar en refresh/login endpoints.
- No bloquear request si falla.

#### 16. Reglas de negocio
- Solo sesiones `is_active=1`.
- Claim `sid` ausente → no-op.

#### 17. Casos borde
- `session_id` inválido — no-op.
- Sesión cerrada — no-op silencioso.
- Primer touch (`last_business_activity_at` null) — siempre write.

#### 18. Casos de concurrencia
- Múltiples requests simultáneos — varios writes posibles en ventana; aceptable (last-write-wins).

#### 19. Casos de seguridad
- No usar para autorización — solo telemetría UI.

#### 20. Casos de prueba mínimos
- Throttle 5 min no escribe dos veces.
- Fail-soft no propaga excepción.
- No-op sin claim sid.
- Write cuando null last activity.

---

### C06 — SessionRedisBridge

**Ruta objetivo:** `app/modules/auth/application/services/session_redis_bridge.py`

#### 1. Objetivo
Centralizar operaciones Redis de sesión: mapping access jti y blacklist por sesión.

#### 2. Responsabilidad
- `link_access(session_id, jti, exp, token_id?)`
- `blacklist_session(session_id)` — lee mapping, blacklist jti(s)
- `blacklist_all_user_sessions(usuario_id, cliente_id)` — iterar sesiones activas
- `get_session_access_mapping(session_id)` — lectura interna
- Fail-soft en todas las escrituras.

#### 3. Alcance
Claves `session:access_jti:{session_id}` y `blacklist:token:{jti}`. No gestiona impersonation ni selection_token.

#### 4. Entradas
`session_id`, `jti`, `exp` unix, `token_id` opcional, listas sesiones para bulk.

#### 5. Salidas
`bool` éxito (informativo; caller no debe fallar por false).

#### 6. Dependencias
- `app/infrastructure/redis/client.py` (`RedisService`)

#### 7. Queries utilizadas
N/A — puede consultar `list active sessions` vía C09 para bulk blacklist.

#### 8. Servicios que consume
- `ActiveSessionsReadService` o query directa para `blacklist_all_user_sessions`

#### 9. Servicios que lo consumen
- `auth_service`, `SessionRevocationService`, `SessionRotationService` (replay), `password_change_service`

#### 10. Redis utilizado

| Operación | Clave |
|-----------|-------|
| SET mapping | `session:access_jti:{session_id}` → JSON `{"jti","exp","token_id"}` |
| GET mapping | Idem |
| SET blacklist | `blacklist:token:{jti}` |
| TTL | Hasta `exp` access (mín 60s) |

#### 11. Auditoría generada
N/A

#### 12. Transacciones requeridas
No

#### 13. Eventos de negocio
N/A — efecto técnico invalidación access.

#### 14. Excepciones que puede producir
Ninguna hacia caller — captura interna, log.

#### 15. Restricciones
- Key normalizada lowercase UUID string.
- Sobrescribir mapping en cada link_access (rotación).

#### 16. Reglas de negocio
- Blacklist jti anterior opcional al rotar si estaba en mapping previo.
- Redis down → operación continúa sin blacklist.

#### 17. Casos borde
- Mapping inexistente en blacklist_session — no-op éxito.
- TTL expirado — no blacklist si ya expiró naturalmente.

#### 18. Casos de concurrencia
- link_access concurrente — last write wins en mapping.

#### 19. Casos de seguridad
- No almacenar refresh token en Redis.
- JSON mapping sin datos sensibles extra.

#### 20. Casos de prueba mínimos
- link_access set key correcta.
- blacklist_session lee y blacklist jti.
- Fail-soft Redis down.
- Key casing consistente.
- Bulk blacklist N sesiones.

---

### C07 — SessionAuditEmitter

**Ruta objetivo:** `app/modules/auth/application/services/session_audit_emitter.py`

#### 1. Objetivo
Wrapper tipado para registrar eventos de sesión en `auth_audit_log` vía `audit_service`.

#### 2. Responsabilidad
- Métodos por evento: `emit_login_success`, `emit_replay_detected`, etc.
- Construir `metadata_json` con `session_id`, `family_id`, `token_id`.
- **No** contiene lógica de negocio de sesión.

#### 3. Alcance
Catálogo completo DESIGN-01 §10.2.

#### 4. Entradas
`cliente_id`, `usuario_id`, `empresa_id?`, `evento`, `exito`, `ip`, `user_agent`, `metadata` dict.

#### 5. Salidas
void

#### 6. Dependencias
- `audit_service.registrar_auth_event` / `audit_queries`

#### 7. Queries utilizadas
- INSERT `auth_audit_log` (vía audit module)

#### 8. Servicios que consume
- `audit_service`

#### 9. Servicios que lo consumen
- Todos los command services y orchestrators

#### 10. Redis utilizado
N/A

#### 11. Auditoría generada
Todos los eventos §10.2 DESIGN-01.

#### 12. Transacciones requeridas
No — audit post-commit (post-acción). No dentro de UoW sesión (evitar rollback audit).

#### 13. Eventos de negocio
Es el publicador de eventos persistidos.

#### 14. Excepciones que puede producir
Fail-soft — log error, no propagar a caller (audit no debe romper auth).

#### 15. Restricciones
- Post-commit únicamente.
- `metadata_json` tamaño ≤ 500 chars campos principales.

#### 16. Reglas de negocio
- `replay_detected` siempre `exito=false`.
- Incluir `session_id` cuando exista.

#### 17. Casos borde
- Audit BD down — log, continuar.

#### 18. Casos de concurrencia
N/A

#### 19. Casos de seguridad
- No incluir token hash ni refresh en metadata.

#### 20. Casos de prueba mínimos
- Cada evento llama audit con campos correctos.
- Fail-soft no rompe login.
- metadata_json schema válido.

---

## 4. Servicios de consulta (reads)

### C08 — SessionQueryService

**Ruta objetivo:** `app/modules/auth/application/services/session_query_service.py`

#### 1. Objetivo
Resolver tokens y sesiones desde BD sin efectos secundarios. Incluye utilidad `hash_token`.

#### 2. Responsabilidad
- `get_by_hash`, `get_by_hash_any_state`
- `get_session`, `get_token_context` (join session+family+token)
- `validate_for_rotation` — checks sin mutación
- `hash_token(plaintext)` — SHA-256 estático
- **No** revoca por idle.
- **No** modifica estado.

#### 3. Alcance
Hot path read para refresh, logout resolve, probe interno.

#### 4. Entradas
`token_hash`, `session_id`, `cliente_id`, `token_id`

#### 5. Salidas
- `TokenContext` | None
- `SessionRow` | None
- `ValidationResult` para rotation

#### 6. Dependencias
- C15, C16, C17 query modules

#### 7. Queries utilizadas
- `get_refresh_token_by_hash_core`
- `get_refresh_token_by_hash_any_state_core`
- `get_active_session_by_id_core`
- `get_family_by_session_id_core`
- `get_family_by_id_core`

#### 8. Servicios que consume
Ninguno.

#### 9. Servicios que lo consumen
- C02, C03, C10, C11, C13

#### 10–12. Redis / Auditoría / UoW
N/A / N/A / No

#### 13. Eventos de negocio
N/A (read-only)

#### 14. Excepciones
No lanza en reads normales — retorna None. `ValidationError` si hash vacío.

#### 15. Restricciones
- Siempre filtrar `cliente_id`.
- `get_by_hash` solo tokens elegibles para operación activa.

#### 16. Reglas de negocio
- `validate_for_rotation` compone: token + family + session checks.
- Cross-tenant → None (caller → 404).

#### 17. Casos borde
- Hash desconocido → None.
- Token usado → contexto con `is_used=1` en any_state.

#### 18. Casos de concurrencia
Read sin lock — estado puede cambiar antes de tx; rotate re-valida bajo lock.

#### 19. Casos de seguridad
- No loguear hash completo en producción.

#### 20. Casos de prueba mínimos
- hash_token determinístico.
- get_by_hash filtra tenant.
- validate_for_rotation detecta compromised family.
- any_state incluye revocados.

---

### C09 — ActiveSessionsReadService

**Ruta objetivo:** `app/modules/auth/application/services/active_sessions_read_service.py` (refactor)

#### 1. Objetivo
Listados escalables de sesiones activas para usuario y admin con DTO enriquecido.

#### 2. Responsabilidad
- `list_user_sessions`, `list_admin_sessions`
- Paginación, sort, search (admin)
- Delegar mapping a C20
- Resolver `is_current` comparando `session_id` o `token_id` vigente
- **No** revoca.
- **No** SQL en presentation.

#### 3. Alcance
GET `/sessions/`, GET `/sessions/admin/`. Reemplaza superadmin SQL ad-hoc (consumidor externo delega aquí).

#### 4. Entradas
`cliente_id`, `usuario_id`, `current_session_id?`, filtros admin (page, limit, search, sort, client_type/platform, usuario_id).

#### 5. Salidas
- `list[UserSessionRead]`
- `PaginatedAdminSessionsResponse`

#### 6. Dependencias
- C15 queries + JOIN C16, C17
- C20 SessionReadMapper
- `shared/pagination/`

#### 7. Queries utilizadas
- SELECT compuesto: `user_session` JOIN `token_family` ON session_id JOIN `refresh_tokens` ON `current_token_id`
- Filtros: `is_active=1`, `expires_at>now`, `is_compromised=0`
- COUNT para paginación admin

#### 8. Servicios que consume
- `SessionReadMapper`

#### 9. Servicios que lo consumen
- `endpoints.py`
- `superadmin_usuario_service` (refactor delegación)
- C06 (bulk blacklist — list sessions)

#### 10–12. Redis / Auditoría / UoW
N/A / N/A / No

#### 13. Eventos de negocio
N/A

#### 14. Excepciones
- `CustomException` 422 `INVALID_SORT_COLUMN` — sort inválido admin.
- `DatabaseError`

#### 15. Restricciones
- Whitelist columnas C21.
- Sin `page` → modo legacy lista completa.
- `buscar` en SQL ILIKE, no in-memory.

#### 16. Reglas de negocio
- Orden default user: `last_refresh_at DESC`.
- `is_current` si `session_id == current_session_id`.
- DTO incluye `session_id` + `token_id` vigente + alias legacy.

#### 17. Casos borde
- Sesión sin `current_token_id` — no listar (estado inconsistente — no debería ocurrir).
- `empresa_id` null — mostrar null en DTO.

#### 18. Casos de concurrencia
Listado eventualmente consistente.

#### 19. Casos de seguridad
- User list solo propias sesiones.
- Admin filtrado por tenant.

#### 20. Casos de prueba mínimos
- User list ownership.
- Admin pagination envelope dual.
- is_current true/false.
- Sort invalid 422.
- Search por device_name, IP.
- Mapper delegation.
- session_id presente en DTO.

---

### C10 — SessionProbeService

**Ruta objetivo:** `app/modules/auth/application/services/session_probe_service.py`

#### 1. Objetivo
Resolver contexto de sesión read-only para `GET /me/` sin side effects.

#### 2. Responsabilidad
- `resolve_context(refresh_token?, access_sid?, cliente_id)`
- Retornar `current_session_id`, `current_token_id`, `is_active`
- **No** revoca idle.
- **No** actualiza activity.

#### 3. Alcance
Solo probe `/me/` y diagnósticos internos.

#### 4. Entradas
Refresh JWT string opcional, claim `sid` opcional, `cliente_id`.

#### 5. Salidas
`SessionProbeResult` — puede tener ids null (fail-soft).

#### 6. Dependencias
- C08 SessionQueryService

#### 7. Queries utilizadas
- `get_refresh_token_by_hash_any_state_core` (si hay refresh)
- `get_active_session_by_id_core` (si hay sid)

#### 8. Servicios que consume
- C08

#### 9. Servicios que lo consumen
- `endpoints` GET `/me/`

#### 10–12. Redis / Auditoría / UoW
N/A / N/A / No

#### 13–20. (Resumen)
Fail-soft siempre; retorna None fields no error. Preferir refresh hash sobre sid si ambos. Tests: me con refresh válido, revocado aún expone token_id, sin refresh retorna null, no llama revoke.

---

## 5. Servicios de orquestación e infraestructura adyacente

### C11 — auth_service (alcance sesión V2)

**Ruta:** `app/modules/auth/application/services/auth_service.py` (refactor parcial)

#### 1. Objetivo
Orquestar flujos auth end-to-end coordinando command/query services y emisión JWT.

#### 2. Responsabilidad (sesión)
- Login → C04 enforce → C01 create → JWT → C06 link → C07 audit
- Refresh → C02 rotate → JWT → C06 link → C07
- Logout → C03 revoke → C07
- Empresa seleccionar/cambiar → C01 update / C02 rotate
- Bloquear refresh impersonación (403)
- **No** SQL directo a tablas sesión.

#### 3–5. Entradas/Salidas
Endpoints existentes `Token`, `MeResponse` — sin cambio de contrato HTTP en esta spec.

#### 6. Dependencias
C01–C07, C08, C10, `jwt.py`, `auth_config_service`

#### 7. Queries
Ninguna directa — solo vía services.

#### 8–9. Consume C01-C07; consumido por endpoints.

#### 10. Redis
Selection token blacklist (existente, fuera C06); C06 para sesión.

#### 11. Auditoría
Coordina C07 para todos los flujos auth.

#### 12. UoW
Indirecto vía C01/C02/C03.

#### 13. Eventos
Orquestación de todos los eventos sesión.

#### 14. Excepciones
`AuthenticationError`, `AuthorizationError`, `ValidationError`, `NotFoundError` — según flujo.

#### 15–19. (Resumen)
Mantiene fail-soft Redis; impersonation sin refresh; empresa multi-flujo; concurrencia delegada a C02.

#### 20. Casos de prueba mínimos
- Login end-to-end mock services.
- Refresh 401 replay.
- Impersonation refresh 403.
- Empresa seleccionar actualiza sesión.
- Logout idempotente.

---

### C12 — password_change_service (alcance sesión)

#### 1. Objetivo
Cambio de contraseña con revocación total de sesiones y nueva sesión dispositivo actual.

#### 2. Responsabilidad
C03 revoke all → C06 blacklist all → C01 create → JWT → C07 audit.

#### 3–9. Alcance / entradas / dependencias
Flujo §7.6 DESIGN-01. Consume C01, C03, C06, C07.

#### 10–20. (Resumen)
UoW vía C03+C01. Audit `password_change`. Tests: all revoked, new session created, old refresh invalid.

---

### C13 — impersonation_service (integración sesión)

#### 1. Objetivo
Impersonación sin sesión BD impersonada; validar parent refresh operador en modelo V2.

#### 2. Responsabilidad
- Redis parent refresh (sin cambio).
- Al end impersonation: C08 validar parent session activa.
- **No** crear user_session impersonada.

#### 6–9. Consume C08; consumido por endpoints impersonate.

#### 10. Redis
`impersonation:parent:*` — sin cambio.

#### 12. UoW
No para impersonation; sí validación read C08.

#### 20. Tests: parent refresh válido restore; parent sesión cerrada → error; no crea filas sesión.

---

### C14 — refresh_token_cleanup_job

#### 1. Objetivo
Purga periódica multi-tabla con retención forense (90 días tokens usados/revocados recomendado).

#### 2. Responsabilidad
- Iterar tenants activos.
- `purge_expired_tokens_core` + purga sesiones/familias huérfanas según política.
- Endpoint admin trigger existente.

#### 7. Queries
- `purge_expired_tokens_core` (C17)
- Purga sesiones inactivas expiradas > retención (C15 — función nueva `purge_closed_sessions_core`)

#### 9. Consumido por endpoint admin cleanup.

#### 12. UoW
**Sí** por batch tenant.

#### 16. Reglas
No DELETE sesiones comprometidas < 1 año (SIEM). Tokens `is_used=1` retener 90d.

#### 20. Tests: multi-tenant iteration, retention respeta fechas, stats returned.

---

## 6. Capa de queries (infrastructure)

### C15 — user_session_queries_core

**Ruta:** `app/infrastructure/database/queries/auth/session/user_session_queries_core.py`

| Atributo | Especificación |
|----------|----------------|
| **1. Objetivo** | Persistencia CRUD tabla `user_session` |
| **2. Responsabilidad** | Funciones atómicas SQL por operación; sin orquestación multi-tabla |
| **3. Alcance** | Tabla `user_session` únicamente |
| **4–5. Entradas/Salidas** | Parámetros columnas tabla v3; retorna rows dict o affected count |
| **6. Dependencias** | `UserSessionTable`, `execute_query` / UoW session |
| **7. Funciones** | Ver DESIGN-01 §5.3: insert, update_empresa, update_on_refresh, touch_business_activity, close, close_all, get_active, count, list_oldest, is_idle_expired, is_absolute_expired, find_by_device |
| **8–9. Consumido por** | C18, C04, C05, C09; no consume services |
| **10–11. Redis/Audit** | N/A |
| **12. UoW** | Participa en tx C18; autocommit en touch_business_activity |
| **13. Eventos** | N/A |
| **14. Excepciones** | `DatabaseError` propagada |
| **15. Restricciones** | `cliente_id` en todo WHERE; CHECK reasons respetados |
| **16. Reglas** | `close_session` setea `is_active=0`; `login_ip` no en UPDATE |
| **17. Borde** | close ya cerrada → affected 0 |
| **18. Concurrencia** | close concurrente idempotente |
| **19. Seguridad** | Parametrized queries |
| **20. Tests** | Unit por función con mock DB; tenant filter; CHECK reason values |

---

### C16 — token_family_queries_core

**Ruta:** `app/infrastructure/database/queries/auth/session/token_family_queries_core.py`

| Atributo | Especificación |
|----------|----------------|
| **1. Objetivo** | Persistencia tabla `token_family` |
| **2. Responsabilidad** | Familia, `current_token_id`, compromiso |
| **7. Funciones** | insert, update_current_token_id, mark_compromised, get_by_id, get_by_session_id, get_by_current_token_id |
| **9. Consumido por** | C18, C08, C09 |
| **12. UoW** | update_current solo dentro C18 rotate tx |
| **16. Reglas** | `mark_compromised` irreversible |
| **17. Borde** | `current_token_id` NULL en familia recién creada |
| **18. Concurrencia** | mark_compromised idempotente (ya compromised → 0 rows ok) |
| **20. Tests** | insert, compromise, get by session, current_token lookup |

---

### C17 — refresh_token_queries_core

**Ruta:** `app/infrastructure/database/queries/auth/session/refresh_token_queries_core.py`

| Atributo | Especificación |
|----------|----------------|
| **1. Objetivo** | Persistencia credencial `refresh_tokens` v3 |
| **2. Responsabilidad** | Token individual; sin device columns |
| **7. Funciones** | insert, get_by_hash, get_by_hash_any_state, mark_used, revoke, revoke_by_session, purge_expired |
| **9. Consumido por** | C18, C08, C14 |
| **15. Restricciones** | UNIQUE token_hash; estados is_used/is_revoked |
| **16. Reglas** | get_by_hash excluye used/revoked/expired |
| **17. Borde** | mark_used en ya usado → 0 rows → señal replay |
| **18. Concurrencia** | get + mark bajo lock en C18 |
| **20. Tests** | hash lookup, mark_used, purge retention, parent_token_id chain |

---

### C18 — session_transaction_core

**Ruta:** `app/infrastructure/database/queries/auth/session/session_transaction_core.py`

| Atributo | Especificación |
|----------|----------------|
| **1. Objetivo** | Operaciones multi-tabla atómicas en UoW |
| **2. Responsabilidad** | Orquestar C15+C16+C17 en una tx; único lugar con UPDLOCK rotate |
| **3. Alcance** | create_session_with_token_tx, rotate_refresh_token_tx, revoke_session_tx, revoke_all_user_sessions_tx, handle_replay_attack_tx |
| **4. Entradas** | `UnitOfWork` instance + parámetros operación |
| **5. Salidas** | IDs creados, rows affected, flags replay |
| **6. Dependencias** | UnitOfWork, C15, C16, C17 |
| **8–9. Consumido por** | C01, C02, C03, C14; no consume application services |
| **12. UoW** | **Sí — siempre** recibe `uow` como primer parámetro |
| **14. Excepciones** | `DatabaseError`; `RuntimeError` si revoke rotation inconsistent → rollback |
| **15. Restricciones** | Orden RTR §9.2 DESIGN-01; no commit parcial |
| **16. Reglas** | Replay tx: compromise + close session + revoke all family tokens |
| **17. Borde** | rotate con 0 rows revoke old → rollback |
| **18. Concurrencia** | UPDLOCK hash; replay tx serializa compromiso |
| **19. Seguridad** | Transacción replay atómica — no estado intermedio comprometido sin cierre |
| **20. Tests** | Integration: create 3 tables; rotate atomic; replay; rollback on failure; lock contention |

#### Detalle transacciones

| Función | Crea | Modifica | Elimina |
|---------|------|----------|---------|
| `create_session_with_token_tx` | session, family, token | family.current_token_id | — |
| `rotate_refresh_token_tx` | token | family, old token, session activity | — |
| `revoke_session_tx` | — | session, family, tokens | — |
| `revoke_all_user_sessions_tx` | — | bulk 3 tablas | — |
| `handle_replay_attack_tx` | — | family compromise, session close, tokens revoke | — |

---

## 7. Tipos de dominio ligero y mappers

### C19 — SessionDomainTypes

**Ruta:** `app/modules/auth/application/session/`

| Archivo | Contenido |
|---------|-----------|
| `revoked_reason.py` | Enum + mappers a CHECK DB v3 |
| `rotate_result.py` | `RotateOutcome`, `RotateResult` |
| `session_creation_result.py` | IDs post-create |
| `session_probe_result.py` | Contexto /me |
| `token_context.py` | Agregado lectura |
| `replay_detection_result.py` | Post replay |
| `revoke_result.py` | Post revoke |

| Atributo | Especificación |
|----------|----------------|
| **1. Objetivo** | Tipos compartidos sin lógica de persistencia |
| **2. Responsabilidad** | DTOs, enums, outcomes — sin I/O |
| **14. Excepciones** | Ninguna |
| **15. Restricciones** | Inmutables preferidos (dataclasses frozen) |
| **16. Reglas** | `RotateOutcome.COMPROMISED` nuevo; eliminar `SESSION_ROTATED`, `TOKEN_REUSE` |
| **20. Tests** | Enum mapping; RotateResult.success solo on ROTATED |

---

### C20 — SessionReadMapper

**Ruta:** `app/modules/auth/application/session/session_read_mapper.py`

| Atributo | Especificación |
|----------|----------------|
| **1. Objetivo** | Transformar row JOIN → `UserSessionRead` / `AdminSessionRead` |
| **2. Responsabilidad** | UA parsing, `device_label`, `is_current`, alias legacy, `status` expiring_soon |
| **4. Entradas** | Row dict (C21 columns), `current_session_id?` |
| **5. Salidas** | DTO pydantic |
| **9. Consumido por** | C09 |
| **16. Reglas** | `issued_at` = session.created_at; `last_refresh_at` = session.last_refresh_at; `platform` → `client_type` alias |
| **20. Tests** | is_current; device enrichment; null device_name; expiring_soon <24h |

---

### C21 — active_session_read_columns

**Ruta:** `app/modules/auth/application/session/active_session_read_columns.py`

| Atributo | Especificación |
|----------|----------------|
| **1. Objetivo** | Whitelist columnas SQL listados |
| **2. Responsabilidad** | Constantes tuple columnas user_session + token vigente + empresa nombre |
| **15. Restricciones** | Solo columnas en whitelist para sort admin |
| **20. Tests** | sort_by inválido no en whitelist |

---

## 8. Matriz global de responsabilidades

Leyenda: ● = sí directamente | ○ = indirecto/vía delegación | — = no aplica

### 8.1 Matriz principal

| ID | Componente | Crea | Modifica | Consulta | Elimina | Publica | Auditoría | Redis | UoW |
|----|------------|:----:|:--------:|:--------:|:-------:|:-------:|:---------:|:-----:|:---:|
| C01 | SessionCreationService | ● session, family, token | ● empresa sesión | ○ | — | — | ○ | — | ● |
| C02 | SessionRotationService | ● token (rotate) | ● token, family, session | ○ | — | — | ● | ○ | ● |
| C03 | SessionRevocationService | — | ● session, family, tokens | ○ | — | — | ● | ● | ● |
| C04 | SessionPolicyService | — | ○ vía C03 | ● | — | — | ○ | ○ | ○ |
| C05 | BusinessActivityService | — | ● last_business_activity | ○ | — | — | — | — | — |
| C06 | SessionRedisBridge | — | — | ● mapping | — | — | — | ● | — |
| C07 | SessionAuditEmitter | ● audit rows | — | — | — | — | ● | — | — |
| C08 | SessionQueryService | — | — | ● | — | — | — | — | — |
| C09 | ActiveSessionsReadService | — | — | ● | — | — | — | — | — |
| C10 | SessionProbeService | — | — | ● | — | — | — | — | — |
| C11 | auth_service | ○ | ○ | ○ | — | ● JWT | ● | ● | ○ |
| C12 | password_change_service | ○ | ○ | — | — | ● JWT | ● | ● | ○ |
| C13 | impersonation_service | — | — | ○ | — | ● JWT imp | ○ | ● | — |
| C14 | refresh_token_cleanup_job | — | — | ○ | ● purge | — | — | — | ● |
| C15 | user_session_queries_core | ● insert | ● updates | ● selects | ○ purge | — | — | — | ○ |
| C16 | token_family_queries_core | ● insert | ● updates | ● selects | — | — | — | — | ○ |
| C17 | refresh_token_queries_core | ● insert | ● updates | ● selects | ● purge | — | — | — | ○ |
| C18 | session_transaction_core | ● compuesto | ● compuesto | ○ lock | — | — | — | — | ● |
| C19 | SessionDomainTypes | — | — | — | — | — | — | — | — |
| C20 | SessionReadMapper | — | — | — | — | — | — | — | — |
| C21 | active_session_read_columns | — | — | — | — | — | — | — | — |

### 8.2 Detalle «Qué crea»

| Componente | Objetos creados |
|------------|-----------------|
| C01 / C18 create | `user_session`, `token_family`, `refresh_tokens` (primero) |
| C02 / C18 rotate | `refresh_tokens` (sucesor) |
| C07 | Filas `auth_audit_log` |
| C11 / C12 / C13 | JWT access/refresh (memoria, no BD) |
| C14 | Ninguno — solo elimina según retención |

### 8.3 Detalle «Qué modifica»

| Componente | Campos / tablas |
|------------|-----------------|
| C01 | `user_session.empresa_id`, `selection_token_completed` |
| C02 | `refresh_tokens.is_used`, `token_family.current_token_id`, `user_session.last_refresh_at`, `last_seen_ip`, `empresa_id` |
| C03 | `user_session.is_active`, `revoked_*`, `token_family` invalidation, `refresh_tokens.is_revoked` |
| C05 | `user_session.last_business_activity_at` |
| C06 | Claves Redis |

### 8.4 Detalle «Qué consulta»

| Componente | Datos |
|------------|-------|
| C08 | Token por hash, sesión por id, TokenContext compuesto |
| C09 | JOIN sesiones activas + empresa nombre |
| C10 | Contexto probe /me |
| C04 | Count sesiones, oldest list, idle checks |

### 8.5 Detalle «Qué elimina»

| Componente | Política |
|------------|----------|
| C14 / C17 | DELETE `refresh_tokens` expirados/usados post-retención 90d |
| C14 / C15 (futuro) | DELETE `user_session` / `token_family` cerradas post-retención |

### 8.6 Detalle «Qué publica»

| Componente | Publicación |
|------------|-------------|
| C11, C12, C13 | JWT tokens al cliente HTTP |
| C07 | Eventos persistidos audit (no message bus V2) |

### 8.7 Detalle «Auditoría»

| Evento | Emisor primario |
|--------|-----------------|
| `login_success` | C11 → C07 |
| `refresh_success` | C11 → C07 |
| `replay_detected` | C02 → C07 |
| `logout` / `logout_all` | C11 → C07 |
| `session_revoked` / `session_admin_revoked` | C03 → C07 |
| `password_change` | C12 → C07 |
| `session_limit_evicted` | C04 → C03 → C07 |
| `idle_timeout` / `session_expired` | C02/C03 → C07 |
| `empresa_selected` / `empresa_changed` | C11 → C07 |

### 8.8 Detalle «Redis»

| Operación | Componente |
|-----------|------------|
| `session:access_jti:{session_id}` SET | C06 ← C11, C12 |
| `blacklist:token:{jti}` SET | C06 ← C03, C11 |
| Bulk blacklist usuario | C06 ← C03, C12 |
| Impersonation parent | C13 (fuera C06) |
| Selection token blacklist | C11 (fuera C06) |

### 8.9 Detalle «UnitOfWork»

| Requiere UoW | Componente / operación |
|:------------:|------------------------|
| ● | C01 create, C02 rotate/replay, C03 revoke, C18 todas, C14 purge batch |
| ○ | C04 evicción (N × C03), C11 orquestación |
| — | C05, C06, C07, C08, C09, C10, C19, C20, C21 |

---

## Anexo A — Mapeo Command → Componente

| Command (DESIGN-01 §6.2) | Handler |
|--------------------------|---------|
| CreateSessionCommand | C01 |
| RotateRefreshTokenCommand | C02 |
| RevokeSessionCommand | C03.revoke_by_session_id |
| RevokeCurrentSessionCommand | C03.revoke_current |
| RevokeAllSessionsCommand | C03.revoke_all_for_user |
| CompromiseFamilyCommand | C02.handle_replay |
| EnforceSessionLimitCommand | C04 |
| UpdateSessionEmpresaCommand | C01.update_empresa |
| TouchBusinessActivityCommand | C05 |
| PurgeExpiredSessionsCommand | C14 |

## Anexo B — Mapeo Query → Componente

| Query | Handler |
|-------|---------|
| GetTokenByHashQuery | C08 |
| GetSessionByIdQuery | C08 |
| ListUserActiveSessionsQuery | C09 |
| ListAdminActiveSessionsQuery | C09 |
| ResolveSessionContextQuery | C10 |
| ValidateSessionForRotationQuery | C08 |

## Anexo C — Tablas BD por componente write

| Tabla | C01 | C02 | C03 | C05 | C14 |
|-------|:---:|:---:|:---:|:---:|:---:|
| user_session | C/R/U | U | U | U | D |
| token_family | C/U | U | U | — | D |
| refresh_tokens | C | C/U | U | — | D |
| auth_audit_log | — | — | — | — | — |

*C=crear, R=leer, U=actualizar, D=eliminar (purge)*

---

**Fin del documento — IAM-BE-COMPONENT-SPEC-01**

**Próximo artefacto:** Plan de implementación (`IAM-SESSION-MANAGEMENT-V2-IMPLEMENTATION-PLAN-01`) con fases, tickets y orden de entrega por componente.
