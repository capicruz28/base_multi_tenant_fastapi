# IAM Session Management V2 — Análisis de Impacto Técnico

**Ticket:** IAM-BE-IMPACT-ANALYSIS-01  
**Versión:** 1.0.0  
**Estado:** Auditoría completa (pre-implementación)  
**Fecha:** 2026-06-22  
**Alcance:** Backend completo — impacto de migración de modelo monolítico `refresh_tokens` a arquitectura de tres entidades (`user_session`, `token_family`, `refresh_tokens`)  
**Referencias normativas:**

- Esquema actual: `app/bootstrap_v2/01_schema/V020__tablas_bd_central.sql`
- Esquema objetivo (definitivo, no rediseñar): `tables_session_management_new.sql` (v3)
- Comportamiento actual documentado: `docs/arquitectura/IAM_SESSION_MANAGEMENT_V2.md`
- Contrato API V1 congelado: `docs/arquitectura/ERP-IAM-SESSIONS-API-CONTRACT-V1.md`
- Plan V1 Enterprise (lectura): `docs/arquitectura/ERP-IAM-SESSIONS-BE-IMPLEMENTATION-PLAN-01.md`

**Restricción de esta fase:** Este documento identifica impacto real. No contiene implementación, código ni diseño de migración SQL detallado.

---

## Índice

1. [Estado actual](#1-estado-actual)
2. [Arquitectura actual](#2-arquitectura-actual)
3. [Nueva arquitectura objetivo](#3-nueva-arquitectura-objetivo)
4. [Inventario completo de componentes afectados](#4-inventario-completo-de-componentes-afectados)
5. [Componentes no afectados](#5-componentes-no-afectados)
6. [Dependencias](#6-dependencias)
7. [Riesgos técnicos](#7-riesgos-técnicos)
8. [Riesgos funcionales](#8-riesgos-funcionales)
9. [Riesgos de compatibilidad](#9-riesgos-de-compatibilidad)
10. [Estrategia de migración recomendada](#10-estrategia-de-migración-recomendada)
11. [Orden recomendado de implementación](#11-orden-recomendado-de-implementación)
12. [Estimación de complejidad](#12-estimación-de-complejidad)
13. [Riesgos críticos](#13-riesgos-críticos)
14. [Recomendaciones](#14-recomendaciones)
15. [Veredicto final](#15-veredicto-final)

---

## 1. Estado actual

### 1.1 Modelo de persistencia

El backend IAM Session Management opera sobre **una única tabla** en SQL Server:

| Tabla | Ubicación DDL | Rol |
|-------|---------------|-----|
| `refresh_tokens` | `V020__tablas_bd_central.sql` (L414–440) | Fuente de verdad de sesión refresh |

**No existen** en el código runtime ni en el bootstrap actual:

- Tabla `user_session`
- Tabla `token_family`
- Vistas SQL sobre sesiones
- Modelos SQLAlchemy para las entidades anteriores

La propuesta v3 en `tables_session_management_new.sql` está **aprobada como objetivo** pero **no desplegada**.

### 1.2 Semántica operativa actual

| Concepto | Implementación actual |
|----------|----------------------|
| Sesión lógica | **1 fila `refresh_tokens` = 1 sesión** |
| Identificador de sesión en API | `token_id` (PK de `refresh_tokens`) |
| Rotación refresh | INSERT nueva fila + UPDATE anterior `is_revoked=1`, `revoked_reason=SESSION_ROTATED` |
| Detección de reuse | Token revocado con `SESSION_ROTATED` reutilizado → `TOKEN_REUSE` → revoke all |
| Metadata dispositivo | Columnas en `refresh_tokens`: `client_type`, `device_name`, `device_id`, `ip_address`, `user_agent` |
| Idle timeout | Evaluado sobre `last_used_at` / `created_at` de la fila token |
| Session limit | Cuenta filas activas en `refresh_tokens` por usuario |
| Activity tracking | `uso_count`, `last_used_at` en cada refresh |
| Cleanup | DELETE físico de filas expiradas + revocadas |
| Access token blacklist | Redis `blacklist:token:{jti}` |
| Vínculo access ↔ sesión | Redis `session:access_jti:{token_id}` |

### 1.3 Madurez del dominio

El dominio actual está certificado como **Production Ready** (P1-01 → P1-04 + HOTFIX-01 + CLEANUP-01) según `IAM_SESSION_MANAGEMENT_V2.md`. Incluye:

- Rotación atómica con `UPDLOCK, ROWLOCK` y `UnitOfWork`
- Idle timeout configurable por tenant (`cliente_auth_config.session_idle_timeout_minutes`)
- Session limit (`max_active_sessions`)
- Detección TOKEN_REUSE (no RTR con `is_used` / `token_family.is_compromised`)
- Módulo Sesiones Activas V1 Enterprise (lectura enriquecida, self-revoke, admin list)

### 1.4 Trabajo reciente en progreso (rama actual)

Existen cambios no mergeados orientados a **V1 Enterprise de lectura** (no al modelo de tres tablas):

| Archivo (estado git) | Naturaleza |
|----------------------|------------|
| `active_sessions_read_service.py` (nuevo) | Lectura sobre `RefreshTokensTable` |
| `session_read_mapper.py` (nuevo) | Mapper fila token → DTO |
| `active_session_read_columns.py` (nuevo) | Whitelist columnas lectura |
| `schemas_sessions.py` (nuevo) | DTOs `UserSessionRead` |
| `endpoints.py`, `admin_sessions_service.py` (modificado) | Endpoints sesiones V1 |
| `refresh_token_queries_core.py` (modificado) | Queries lectura ampliadas |
| Tests `test_iam_sessions_v1_enterprise.py`, `test_iam_sessions_rc1.py` (nuevo) | Cobertura V1 |

**Impacto:** Este trabajo queda **obsoleto en su premisa de datos** (sesión = fila token) y requerirá reescritura al migrar, aunque los contratos API y la estructura de capas son reutilizables.

---

## 2. Arquitectura actual

### 2.1 Diagrama de capas

```
┌─────────────────────────────────────────────────────────────────┐
│  presentation/endpoints.py                                       │
│  schemas.py | schemas_sessions.py | schemas_admin_sessions.py   │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│  application/services/                                           │
│  auth_service.py          ← orquestación login/refresh/logout   │
│  refresh_token_service.py ← CRUD tokens, validación, revoke     │
│  rotate_refresh_token_service.py ← rotación atómica             │
│  active_sessions_read_service.py ← listados sesión (V1)         │
│  password_change_service.py                                       │
│  refresh_token_cleanup_job.py                                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│  application/session/                                            │
│  rotate_result.py | revoked_reason.py | session_read_mapper.py   │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│  infrastructure/database/queries/auth/                           │
│  refresh_token_queries_core.py                                   │
│  refresh_token_rotate_queries_core.py                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│  infrastructure/database/tables.py → RefreshTokensTable          │
│  SQL Server → refresh_tokens (monolítica)                        │
└─────────────────────────────────────────────────────────────────┘

Adyacentes (sin tabla propia):
  app/core/security/jwt.py          — emisión/validación JWT
  app/infrastructure/redis/         — blacklist + session:access_jti
  app/api/deps.py                   — get_current_user + blacklist check
  app/api/deps_auth.py              — require_erp_session, selection_token
  cliente_auth_config               — políticas por tenant
  auth_audit_log                    — eventos de auditoría
```

### 2.2 Columnas `refresh_tokens` (V020) y uso en código

| Columna | Tipo actual | Consumidores principales |
|---------|-------------|--------------------------|
| `token_id` | PK UUID | API paths, Redis key, `current_token_id`, ownership revoke |
| `cliente_id` | UUID NOT NULL | Filtro tenant obligatorio en todas las queries |
| `empresa_id` | UUID NULL | Contexto multi-empresa post-selección; refresh rota con nuevo valor |
| `usuario_id` | UUID NOT NULL | Ownership, session limit, revoke all |
| `token_hash` | VARCHAR(255) UNIQUE | Lookup hot path login/refresh/logout |
| `expires_at` | DATETIME | Validación activa, listados, cleanup |
| `is_revoked` | BIT | Estado sesión; filtro activos |
| `revoked_at` | DATETIME | Auditoría |
| `revoked_reason` | NVARCHAR(100) libre | Enum app `RevokedReason` (10 valores) |
| `client_type` | VARCHAR(10) | Insert login/rotate; filtros admin; DTO device |
| `device_name` | NVARCHAR(100) | Insert; listados; mapper |
| `device_id` | NVARCHAR(100) | Insert; índice `IDX_refresh_token_device` |
| `ip_address` | VARCHAR(45) | Insert; listados; búsqueda admin |
| `user_agent` | VARCHAR(500) | Insert; parser UA en lectura |
| `created_at` | DATETIME | Sort, session limit (oldest), `issued_at` DTO |
| `last_used_at` | DATETIME | Idle timeout, activity, sort, `last_refresh_at` DTO |
| `uso_count` | INT | Activity tracking en refresh |

### 2.3 Índices actuales (V020)

| Índice | Columnas | Propósito |
|--------|----------|-----------|
| `UQ` implícito | `token_hash` UNIQUE | Lookup O(1) por hash |
| `IDX_refresh_token_usuario_cliente` | `(usuario_id, cliente_id)` | Sesiones por usuario/tenant |
| `IDX_refresh_token_active` | `(usuario_id, is_revoked, expires_at)` | Sesiones activas |
| `IDX_refresh_token_cleanup` | `(expires_at, is_revoked)` | Job cleanup |
| `IDX_refresh_token_device` | `(device_id) WHERE device_id IS NOT NULL` | Device lookup |
| `IDX_refresh_token_empresa` | `(empresa_id) WHERE empresa_id IS NOT NULL` | Filtro empresa |

### 2.4 Constraints actuales

| Constraint | Tabla | Notas |
|------------|-------|-------|
| `PK` | `token_id` | — |
| `FK_refresh_token_cliente` | → `cliente` ON DELETE CASCADE | — |
| `FK_refresh_token_usuario` | → `usuario` ON DELETE NO ACTION | Revocación explícita en código |
| `FK_refresh_token_empresa` | → `org_empresa` ON DELETE NO ACTION | — |
| `UQ token_hash` | UNIQUE | — |
| CHECK constraints | **Ninguno** en `revoked_reason` | Valores libres + enum app |

### 2.5 Flujos auth y archivos responsables

| Flujo | Endpoint(s) | Servicios / queries |
|-------|-------------|---------------------|
| Login | `POST /auth/login/` | `auth_service` → `store_refresh_token` → `insert_refresh_token_core` |
| Selección empresa | `POST /auth/empresa/seleccionar/` | `auth_service` → `store_refresh_token` (nueva fila) |
| Refresh | `POST /auth/refresh/` | `rotate_refresh_token_service` → `rotate_refresh_token_core` |
| Cambiar empresa | `POST /auth/empresa/cambiar/` | Rotación o store según refresh previo |
| Logout | `POST /auth/logout/` | `revoke_token` → `revoke_refresh_token_core` |
| Logout all | `POST /auth/logout_all/` | `revoke_all_user_tokens` |
| Self-revoke | `POST /auth/sessions/{token_id}/revoke/` | `revoke_refresh_token_by_id` |
| Admin revoke | `POST /auth/sessions/{token_id}/revoke_admin/` | Idem + audit |
| List user sessions | `GET /auth/sessions/` | `ActiveSessionsReadService` |
| List admin sessions | `GET /auth/sessions/admin/` | `ActiveSessionsReadService` |
| Current session | `GET /auth/me/` → `current_token_id` | `resolve_current_token_id_from_refresh` |
| Password change | `POST /auth/password/change/` | `revoke_all` + `store_refresh_token` nueva sesión |
| User deactivate/delete | users module | `revoke_all_user_tokens` + blacklist |
| Impersonation | `POST /auth/impersonate/` | Redis parent refresh; sin fila BD impersonación |
| Cleanup | `POST /auth/admin/cleanup-expired-tokens/` | `RefreshTokenCleanupJob` → `delete_expired_tokens_core` |
| Replay detection | Interno en refresh | `is_revoked` + `SESSION_ROTATED` → `handle_revoked_refresh_reuse` |

### 2.6 Enum `RevokedReason` actual

Archivo: `app/modules/auth/application/session/revoked_reason.py`

```
USER_LOGOUT | LOGOUT_ALL | ADMIN_REVOKE | PASSWORD_CHANGE | USER_DEACTIVATED |
USER_DELETED | TOKEN_REUSE | SESSION_ROTATED | IDLE_TIMEOUT | SESSION_LIMIT
```

Almacenado en `refresh_tokens.revoked_reason` (NVARCHAR libre, sin CHECK DB).

---

## 3. Nueva arquitectura objetivo

### 3.1 Modelo de tres entidades (definitivo — `tables_session_management_new.sql` v3)

```
usuario ──< user_session ──< token_family ──< refresh_tokens
                │                                    │
                └──────── session_id (desnorm.) ────┘
```

| Entidad | Rol | Campos clave nuevos |
|---------|-----|---------------------|
| `user_session` | Sesión lógica por dispositivo | `session_id`, `login_method`, `selection_token_completed`, `platform`, `device_fingerprint`, `login_ip`, `last_seen_ip`, `is_active`, `last_refresh_at`, `last_business_activity_at`, `expires_at` |
| `token_family` | Cadena de rotación RTR | `family_id`, `session_id`, `current_token_id`, `is_compromised`, `compromised_at`, `invalidation_reason` |
| `refresh_tokens` | Credencial criptográfica individual | `family_id`, `session_id`, `parent_token_id`, `is_used`, `used_at` (+ columnas tenant desnormalizadas) |

### 3.2 Cambios estructurales respecto al modelo actual

| Aspecto | Actual (V020) | Objetivo (v3) |
|---------|---------------|---------------|
| Sesión lógica | Fila `refresh_tokens` | Fila `user_session` |
| Rotación | Nueva fila + revocar anterior | `is_used=1` + INSERT hijo + UPDATE `current_token_id` |
| Replay attack | Reuse de `SESSION_ROTATED` | Token `is_used=1` presentado → `token_family.is_compromised=1` → cierre sesión |
| Device metadata | En `refresh_tokens` | En `user_session` |
| IP | `ip_address` única | `login_ip` (inmutable) + `last_seen_ip` (refresh) |
| Activity negocio | No existe | `last_business_activity_at` (throttle 5 min en deps) |
| `client_type` | En token | `platform` en sesión (`web\|mobile\|desktop\|api`) |
| `uso_count` | Incremento por refresh | **Eliminado** — RTR: uso 0 o 1 |
| `revoked_reason` | Texto libre | CHECK constraints en sesión y token |
| Cleanup | DELETE físico | Retención forense; purga selectiva |
| Deploy | — | **Invalida todas las sesiones activas** (re-login obligatorio) |

### 3.3 Índices objetivo (resumen)

**`user_session`:** 7 índices (`IDX_session_usuario_activo`, `_cliente`, `_device_usuario`, `_expires`, `_empresa`, `_login_method`, `_last_seen_ip`, `_business_activity`)

**`token_family`:** 5 índices (`IDX_family_session`, `_comprometida`, `_usuario`, `_cliente`, `_current_token`)

**`refresh_tokens`:** 7 índices (`IDX_token_hash_activo`, `_family_estado`, `_session_activo`, `_parent`, `_usuario_cliente`, `_cleanup`, `_used_activo`)

### 3.4 Semántica de estados objetivo

**Token (`refresh_tokens`):**

| is_used | is_revoked | Significado |
|---------|------------|-------------|
| 0 | 0 | Vigente |
| 1 | 0 | Consumido en rotación normal |
| 0 | 1 | Invalidado forzosamente |
| 1 | 1 | Violación (no debería ocurrir) |

**Familia:** `is_compromised=1` invalida todos los tokens de la familia.

**Sesión:** `is_active=0` cierra sesión lógica; cascade a familias.

### 3.5 Gaps entre objetivo y código actual

| Capacidad objetivo | Estado en código |
|--------------------|------------------|
| `user_session` CRUD | **Inexistente** |
| `token_family` CRUD | **Inexistente** |
| RTR con `is_used` / `parent_token_id` | **Inexistente** — rotación revoca fila |
| `is_compromised` replay | **Inexistente** — usa `TOKEN_REUSE` + revoke all |
| `current_token_id` O(1) | **Inexistente** |
| `last_business_activity_at` | **Inexistente** |
| `device_fingerprint` | **Inexistente** |
| `login_method` / `selection_token_completed` | **Inexistente** en BD |
| CHECK `revoked_reason` | **Inexistente** en BD |
| Retención forense tokens | **Inexistente** — DELETE cleanup |

---

## 4. Inventario completo de componentes afectados

### 4.1 Base de datos

| Componente | Ruta | Impacto | Tipo cambio |
|------------|------|---------|-------------|
| DDL bootstrap producción | `app/bootstrap_v2/01_schema/V020__tablas_bd_central.sql` | **CRÍTICO** | Nueva migración bootstrap; alterar/reemplazar `refresh_tokens`; crear 2 tablas |
| SQL propuesta objetivo | `tables_session_management_new.sql` | Referencia | Ya definido — no rediseñar |
| Copias documentación SQL | `app/docs/database/1.- TABLAS_BD_CENTRAL.sql`, `TABLAS_BD_CENTRAL_ORI.sql`, `TABLAS_BD_DEDICADA.sql` | Medio | Actualizar documentación post-migración |
| Migraciones históricas | `app/docs/database/migrations/FASE2_INDICES_COMPUESTOS.sql`, `FASE3_MIGRACION_UUID*.sql` | Bajo | Referencia histórica; índices obsoletos |
| Vistas SQL | — | **N/A** | No existen vistas sobre `refresh_tokens` |
| Índices V020 | 5 índices + UNIQUE `token_hash` | **CRÍTICO** | Reemplazados por 19 índices en modelo v3 |
| Constraints V020 | 3 FK + PK + UNIQUE | **CRÍTICO** | Nuevas FK inter-tabla; CHECK constraints; self-ref `parent_token_id` |

### 4.2 SQLAlchemy

| Componente | Ruta | Impacto | Detalle |
|------------|------|---------|---------|
| `RefreshTokensTable` | `app/infrastructure/database/tables.py` L264–306 | **CRÍTICO** | Redefinir columnas: +`family_id`, `session_id`, `parent_token_id`, `is_used`, `used_at`; −device columns, `uso_count`, `client_type`, `ip_address`, `user_agent` |
| `UserSessionTable` | — | **CRÍTICO** | **CREAR** — 20+ columnas |
| `TokenFamilyTable` | — | **CRÍTICO** | **CREAR** — 10 columnas |
| `ClienteAuthConfigTable` | `tables.py` | Parcial | Políticas siguen; semántica idle puede referenciar `user_session` |
| `AuthAuditLogTable` | `tables.py` | Parcial | Nuevos eventos posibles (`replay_detected`, `family_compromised`) |
| Repositories ORM | `app/modules/auth/infrastructure/repositories/usuario_repository.py` | **NO** | No toca tokens |

### 4.3 Queries (infraestructura)

| Función / archivo | Operaciones actuales | Impacto |
|-------------------|---------------------|---------|
| `refresh_token_queries_core.py` | 11 funciones async sobre `RefreshTokensTable` | **REESCRITURA TOTAL** |
| `record_refresh_token_activity_core` | UPDATE `uso_count`, `last_used_at` | Eliminar o redirigir a `user_session.last_refresh_at` |
| `is_refresh_token_session_idle_expired_core` | SQL raw idle sobre token row | Mover a `user_session.last_refresh_at` |
| `get_refresh_token_by_hash_any_state_core` | SELECT parcial | Ampliar JOIN familia/sesión; validar `is_compromised` |
| `get_refresh_token_by_hash_core` | SELECT activo | Idem + estados `is_used` |
| `insert_refresh_token_core` | INSERT monolítico con device | Transacción: session + family + token |
| `revoke_refresh_token_core` | UPDATE `is_revoked` | Revocar token + posible cierre sesión/familia |
| `revoke_all_user_tokens_core` | UPDATE masivo por usuario | UPDATE `user_session.is_active=0` + familias + tokens |
| `get_active_sessions_by_user_core` | SELECT tokens activos | JOIN `user_session` + token vigente |
| `get_active_sessions_by_user_oldest_first_core` | SELECT oldest (session limit) | Contar `user_session.is_active` |
| `delete_expired_tokens_core` | DELETE físico | Rediseñar purga multi-tabla con retención |
| `revoke_refresh_token_by_id_core` | UPDATE por `token_id` | Revocar por `session_id` o resolver token→sesión |
| `refresh_token_rotate_queries_core.py` | UoW: lock, activity, insert, revoke | **REESCRITURA TOTAL** — RTR: `is_used`, `parent_token_id`, `current_token_id`, replay |
| `auth_queries.py` | RBAC niveles acceso | **NO** |
| `queries/auth/__init__.py` | Re-exports | Actualizar exports |

### 4.4 Dominio / application layer

| Componente | Ruta | Impacto |
|------------|------|---------|
| `RevokedReason` | `session/revoked_reason.py` | **ALTO** — alinear con CHECK DB v3 (`logout`, `replay_detected`, etc.) |
| `RotateOutcome` / `RotateResult` | `session/rotate_result.py` | **ALTO** — añadir `COMPROMISED`, `FAMILY_INVALID`; campos `session_id`, `family_id` |
| `SessionReadMapper` | `session/session_read_mapper.py` | **ALTO** — fuente datos pasa de fila token a JOIN sesión+token |
| `active_session_read_columns.py` | Whitelist columnas | **ALTO** — columnas desde `user_session` |
| `RefreshTokenService` | `services/refresh_token_service.py` (~900 LOC) | **CRÍTICO** — núcleo del cambio |
| `rotate_refresh_token_service.py` | Orquestación UoW | **CRÍTICO** |
| `auth_service.py` | Login, refresh, logout, empresa, impersonation restore | **CRÍTICO** (~1300+ LOC con lógica tokens) |
| `active_sessions_read_service.py` | Listados V1 | **CRÍTICO** — queries JOIN multi-tabla |
| `admin_sessions_service.py` | Wrapper deprecated | **MEDIO** |
| `password_change_service.py` | Revoke all + nueva sesión | **ALTO** |
| `refresh_token_cleanup_job.py` | Job multi-tenant | **ALTO** — purga 3 tablas |
| `auth_config_service.py` | Políticas tenant | **BAJO** — config sin cambio estructural |
| `impersonation_service.py` | Redis parent refresh | **BAJO** — sin BD; parent refresh sigue siendo string JWT |
| `login_use_case.py` | Use case login | **BAJO** — delega a auth_service |
| `domain/entities/usuario.py` | Entidad usuario | **NO** |

### 4.5 Presentación / OpenAPI

| Componente | Ruta | Impacto |
|------------|------|---------|
| `endpoints.py` | Router auth completo | **CRÍTICO** — 20+ endpoints; lógica interna de 12 flujos sesión |
| `schemas_sessions.py` | `UserSessionRead`, `SessionDeviceRead` | **ALTO** — añadir `session_id`; `token_id` = vigente; nuevos campos IP dual |
| `schemas_admin_sessions.py` | Admin DTOs + paginación | **ALTO** |
| `schemas.py` | `Token`, `MeResponse.current_token_id`, auth config | **MEDIO** — evolución identificadores |
| `endpoints_auth_config.py` | CRUD config | **NO** directo |
| `endpoints_sso.py` | SSO providers | **NO** |

**Endpoints con dependencia directa de modelo token-monolítico:**

| Método | Ruta | Impacto |
|--------|------|---------|
| POST | `/auth/login/` | Crear sesión+familia+token |
| POST | `/auth/empresa/seleccionar/` | Actualizar `user_session.empresa_id` + token |
| POST | `/auth/empresa/cambiar/` | Rotación RTR con nuevo `empresa_id` |
| POST | `/auth/refresh/` | Rotación RTR completa |
| POST | `/auth/logout/` | Cerrar sesión lógica |
| POST | `/auth/logout_all/` | Cerrar todas las sesiones |
| GET | `/auth/sessions/` | Listado desde `user_session` |
| GET | `/auth/sessions/admin/` | Idem admin |
| POST | `/auth/sessions/{token_id}/revoke/` | Resolver session; posible path `{session_id}` |
| POST | `/auth/sessions/{token_id}/revoke_admin/` | Idem |
| GET | `/auth/me/` | `current_token_id` / evolución |
| POST | `/auth/admin/cleanup-expired-tokens/` | Cleanup multi-tabla |
| POST | `/auth/password/change/` | Revoke sesiones + nueva |

### 4.6 Autenticación — desglose por capacidad

| Capacidad | Archivos afectados | Naturaleza del impacto |
|-----------|-------------------|----------------------|
| Login | `auth_service`, `refresh_token_service`, `insert_refresh_token_core`, `endpoints` | Creación transaccional 3 entidades |
| Refresh | `rotate_refresh_token_service`, `rotate_queries_core`, `endpoints` | RTR completo vs revocar+insertar |
| Logout | `refresh_token_service.revoke_token`, queries | Cierre sesión + familia |
| Logout all | `revoke_all_user_tokens_core` | Bulk `user_session.is_active=0` |
| Revoke session | `revoke_refresh_token_by_id_core`, endpoints | Identificador puede cambiar |
| Revoke all sessions | password_change, user_service | Bulk multi-tabla |
| Replay detection | `refresh_token_service.handle_revoked_refresh_reuse`, rotate core | **Cambio de algoritmo** — `is_compromised` vs `TOKEN_REUSE` |
| Selection token | `jwt.py`, `deps_auth.py`, `auth_service` | Actualizar `user_session.selection_token_completed` + `empresa_id` |
| Impersonation | `impersonation.py`, `impersonation_service`, `auth_service` | Parent refresh string; sin fila BD |
| Current user | `deps.py` | Sin BD tokens |
| Middleware / deps | `deps_auth.py`, `session_scope.py` | **Nuevo:** throttle `last_business_activity_at` |
| Session probe | `get_refresh_token_by_hash_any_state_core` | Validar familia no comprometida |

### 4.7 Seguridad

| Mecanismo | Estado actual | Impacto migración |
|-----------|---------------|-------------------|
| Refresh Token Rotation | Revocar anterior + INSERT | RTR con `is_used` + cadena `parent_token_id` |
| Replay Attack Detection | `SESSION_ROTATED` reuse → revoke all | `is_used=1` reuse → `is_compromised` → cierre sesión |
| Session Validation | `is_revoked=0` + `expires_at` | + `user_session.is_active` + `!is_compromised` |
| Session Probe | Hash lookup | + checks familia/sesión |
| Auditoría | `auth_audit_log` vía `audit_service` | Nuevos eventos; metadata con `session_id`, `family_id` |
| Redis blacklist | `blacklist:token:{jti}` | Sin cambio estructural |
| Redis session mapping | `session:access_jti:{token_id}` | **Decisión requerida:** key por `session_id` vs `token_id` vigente |
| UPDLOCK concurrencia | Por `token_hash` | Mantener; posible lock adicional en `token_family` |

### 4.8 Módulos externos al auth

| Componente | Ruta | Impacto |
|------------|------|---------|
| `user_service.py` | `app/modules/users/application/services/` | **ALTO** — `revoke_all_user_tokens` en deactivate/delete |
| `superadmin_usuario_service.py` | SQL ad-hoc L721–738 `FROM dbo.refresh_tokens` | **ALTO** — duplica lógica; reescribir o delegar a read service |
| `superadmin/presentation/schemas.py` | `RefreshTokenInfo`, `UsuarioSesionesResponse` | **ALTO** — alinear con nuevo DTO |

### 4.9 Testing

| Archivo | Cobertura actual | Impacto |
|---------|------------------|---------|
| `test_iam_sessions_p0_01.py` | Reuse, blacklist, deactivate | **REESCRITURA** |
| `test_iam_sessions_p1_01.py` | Activity, `uso_count`, revoked_reason | **REESCRITURA** — sin `uso_count` |
| `test_iam_sessions_p1_02.py` | Idle timeout SQL | **REESCRITURA** — idle en sesión |
| `test_iam_sessions_p1_02_hotfix.py` | Hotfix idle | **REESCRITURA** |
| `test_iam_sessions_p1_03.py` | Session limit | **REESCRITURA** — contar sesiones |
| `test_iam_sessions_p1_04_rotate.py` | Core rotate UoW SQL | **REESCRITURA CRÍTICA** — asserts SQL actuales inválidos |
| `test_iam_sessions_p1_04_hotfix_01.py` | User mismatch rotate | **REESCRITURA** |
| `test_iam_sessions_p1_04_refresh_endpoint.py` | POST refresh | **REESCRITURA** |
| `test_iam_sessions_p1_04_empresa_cambiar.py` | Cambio empresa | **REESCRITURA** |
| `test_iam_sessions_pa001.py` | Admin list | **REESCRITURA** |
| `test_iam_sessions_rc1.py` | Self-revoke RC1 | **REESCRITURA** |
| `test_iam_sessions_v1_enterprise.py` | Mapper, read service, OpenAPI | **REESCRITURA** |
| `test_iam_me_current_token_id.py` | `/me/` token_id | **REESCRITURA** |
| `test_iam_session_access_redis_key_casing.py` | Redis key casing | **REVISIÓN** |
| `test_iam_arch02_path_a_migration.py` | Endpoints sesión RBAC | **REVISIÓN** contratos |
| `test_impersonation_auth.py` | Impersonation | **PARCIAL** |
| `test_empresa_sesion_auth.py` | Selección empresa | **REESCRITURA** mocks store |
| `test_multiempresa_m1.py` | Multiempresa M1 | **REESCRITURA** mocks |
| `test_tenant_isolation.py` | Aislamiento tenant queries | **REESCRITURA** |
| `tests/integration/test_iam_me_current_token_id.py` | Integración `/me/` | **REESCRITURA** |

**Total tests directamente afectados:** ~18 archivos, ~150+ casos estimados.

### 4.10 Scripts y herramientas

| Archivo | Impacto |
|---------|---------|
| `scripts/audit_text_queries.py` | Referencia tabla — actualizar post-migración |
| Scripts integración staging (`run_m*_*.py`, `validate_p2_*.py`) | **PARCIAL** — flujos login dependen de sesiones válidas |

### 4.11 Documentación

| Documento | Impacto |
|-----------|---------|
| `IAM_SESSION_MANAGEMENT_V2.md` | **OBSOLETO** post-migración — describe modelo monolítico |
| `ERP-IAM-SESSIONS-API-CONTRACT-V1.md` | **REVISIÓN** — `token_id` como ID sesión vs `session_id` |
| `ERP-IAM-SESSIONS-BE-IMPLEMENTATION-PLAN-01.md` | **OBSOLETO** — premisa "sin migración SQL" |
| Auditorías en `app/docs/auditoria/AUDITORIA_AUTH_LOGIN.md`, etc. | Actualizar referencias |

### 4.12 Resumen cuantitativo de afectación

| Categoría | Archivos afectados (directos) | Severidad |
|-----------|------------------------------|-----------|
| Base de datos / DDL | 1 bootstrap + 1 migración nueva + 4 docs SQL | CRÍTICA |
| SQLAlchemy tables | 1 modificar + 2 crear | CRÍTICA |
| Queries auth | 2 archivos (~650 LOC) | CRÍTICA |
| Services auth | 7 archivos (~2500+ LOC) | CRÍTICA |
| Session helpers | 4 archivos | ALTA |
| Presentation | 4 archivos | ALTA |
| Módulos externos | 3 archivos | ALTA |
| Tests | ~18 archivos | ALTA |
| Core auth/security | 2 archivos (parcial) | MEDIA |
| **Total estimado** | **~42 archivos Python + DDL** | — |

---

## 5. Componentes no afectados

### 5.1 Sin dependencia de `refresh_tokens` (confirmado por inspección)

| Componente | Ruta | Notas |
|------------|------|-------|
| JWT access token | `app/core/security/jwt.py` (`create_access_token`, `decode_access_token`) | Sin persistencia BD |
| Selection token JWT | `jwt.py`, `deps_auth.py` | Stateless; blacklist Redis por jti |
| ERP session scope | `app/api/deps_auth.py`, `app/core/tenant/session_scope.py` | JWT operativo; no lee BD sesiones |
| `get_current_user` | `app/api/deps.py` | Blacklist Redis; no BD tokens |
| Password change enforcement | `app/core/auth/password_change_enforcement.py` | Whitelist rutas |
| User builder / context | `app/core/auth/user_builder.py`, `user_context.py` | Sin tokens |
| Platform user lookup | `app/core/auth/platform_user_lookup.py` | Sin tokens |
| Impersonation RBAC | `app/core/auth/impersonation_rbac.py` | JWT claims |
| RBAC queries | `auth_queries.py` | Permisos usuario/rol |
| SSO endpoints | `endpoints_sso.py` | Proveedores SSO |
| Auth config CRUD | `endpoints_auth_config.py`, `auth_config_service.py` | Tabla `cliente_auth_config` |
| Audit INSERT | `audit_queries.py` | Tabla `auth_audit_log` |
| Redis client | `app/infrastructure/redis/client.py` | Infraestructura genérica |
| Config global | `app/core/config.py` | `REFRESH_SECRET_KEY`, cookie name |
| Usuario repository | `usuario_repository.py` | CRUD usuario |
| Entidad dominio usuario | `domain/entities/usuario.py` | Sin sesiones |
| Módulos ERP (ORG, INV, etc.) | — | Dependen de JWT access, no de refresh BD |
| Vistas SQL | — | No existen |

### 5.2 Afectación indirecta (perímetro — revisar en integración)

| Componente | Por qué revisar |
|------------|-----------------|
| `impersonation.py` | Parent refresh token sigue siendo JWT string |
| `jwt.py` `create_refresh_token` | Posibles claims `session_id` en JWT |
| `cliente_auth_config` | Políticas idle/TTL aplican a `user_session` |
| Scripts E2E staging | Re-login masivo post-deploy invalidará sesiones |

---

## 6. Dependencias

### 6.1 Dependencias internas (grafo simplificado)

```
V020 refresh_tokens (BD)
    └── RefreshTokensTable (SQLAlchemy)
            ├── refresh_token_queries_core.py
            ├── refresh_token_rotate_queries_core.py
            │       └── UnitOfWork
            ├── RefreshTokenService
            │       ├── Redis (session:access_jti, blacklist)
            │       └── cliente_auth_config (idle, max_sessions, refresh_days)
            ├── rotate_refresh_token_service
            ├── auth_service
            │       ├── jwt.py (create/decode refresh)
            │       ├── impersonation (Redis)
            │       └── audit_service → auth_audit_log
            ├── active_sessions_read_service
            │       └── session_read_mapper → schemas_sessions
            ├── password_change_service
            ├── refresh_token_cleanup_job
            ├── endpoints.py (presentation)
            ├── user_service (revoke on deactivate)
            └── superadmin_usuario_service (SQL ad-hoc)
```

### 6.2 Dependencias externas

| Dependencia | Relación |
|-------------|----------|
| SQL Server | Motor persistencia; UPDLOCK; CHECK constraints nuevos |
| Redis | Blacklist + session mapping (fail-soft) |
| `cliente`, `usuario`, `org_empresa` | FK en las 3 tablas nuevas |
| Frontend | Consume API sesiones; identificadores `token_id` |
| Superadmin panel | Lista sesiones vía endpoint/schema propio |
| Flyway/bootstrap_v2 | Pipeline DDL |

### 6.3 Dependencias de despliegue

| Prerequisito | Bloqueante para |
|--------------|-----------------|
| Migración DDL aprobada y ejecutada | Todo el código nuevo |
| Invalidación sesiones activas | Deploy coordinado con FE/comunicación usuarios |
| Actualización contrato API acordada con FE | Paths revoke, DTOs |

### 6.4 Orden de dependencia técnica

```
1. DDL (user_session, token_family, refresh_tokens v3)
2. tables.py (SQLAlchemy)
3. Queries (insert, rotate, read, revoke, cleanup)
4. RefreshTokenService / SessionService
5. auth_service (orquestación)
6. Presentation (endpoints, schemas)
7. Módulos externos (users, superadmin)
8. Tests
9. Documentación
```

---

## 7. Riesgos técnicos

| ID | Riesgo | Probabilidad | Impacto | Descripción |
|----|--------|:------------:|:-------:|-------------|
| RT-01 | Condiciones de carrera en RTR | Media | Crítico | Rotación requiere transacción atómica en 3 tablas; más superficie que modelo actual |
| RT-02 | Lock contention | Media | Alto | UPDLOCK en token + posible lock familia bajo carga concurrente refresh |
| RT-03 | Integridad `current_token_id` | Media | Crítico | Sin FK circular; integridad solo en app layer — desincronización posible |
| RT-04 | Performance hot path | Baja | Alto | Validación refresh añade checks `is_compromised`, `is_active` — mitigable con desnormalización |
| RT-05 | Redis key semantics | Media | Medio | `session:access_jti:{token_id}` vs `{session_id}` — tokens rotados invalidan mapping |
| RT-06 | Cleanup multi-tabla | Media | Medio | DELETE actual simple; retención forense complica purga y espacio BD |
| RT-07 | Multi-DB tenant routing | Baja | Alto | Cada tenant en BD dedicada — migración DDL debe ejecutarse en N bases |
| RT-08 | SQLAlchemy schema drift | Media | Medio | 3 tablas nuevas — riesgo desalineación ORM vs DDL |
| RT-09 | Tests insuficientes post-RTR | Alta | Alto | Algoritmo replay cambia — suite actual no cubre `is_compromised` |
| RT-10 | Código duplicado superadmin | Alta | Medio | SQL ad-hoc no migrado automáticamente con auth module |

---

## 8. Riesgos funcionales

| ID | Riesgo | Descripción |
|----|--------|-------------|
| RF-01 | Pérdida sesiones activas en deploy | Nota explícita en DDL objetivo: invalidación total — todos re-login |
| RF-02 | Semántica session limit cambia | Actual: N filas token; objetivo: N sesiones lógicas (dispositivos) — comportamiento puede diferir si rotación creaba múltiples filas |
| RF-03 | Idle timeout cambia de referencia | De `last_used_at` token a `last_refresh_at` sesión — usuarios activos en API pero sin refresh podrían expirar diferente |
| RF-04 | `last_business_activity_at` nuevo | Throttle 5 min en deps — escrituras adicionales; comportamiento idle dual (auth vs negocio) |
| RF-05 | Replay handling más agresivo | `is_compromised` cierra sesión completa incluyendo token legítimo del usuario real |
| RF-06 | Cambio empresa | Flujo rotación debe actualizar `empresa_id` en sesión + token vigente |
| RF-07 | Selection token flow | Flag `selection_token_completed` debe sincronizarse con flujo JWT stateless |
| RF-08 | Impersonation restore | Parent refresh del operador debe seguir válido tras migración |
| RF-09 | Remember me / TTL | `user_session.expires_at` vs `refresh_tokens.expires_at` — dos niveles TTL |
| RF-10 | Device reuse | Índice `IDX_session_device_usuario` permite reusar sesión existente — lógica no implementada actualmente |

---

## 9. Riesgos de compatibilidad

| ID | Riesgo | Severidad | Detalle |
|----|--------|:---------:|---------|
| RC-01 | API `token_id` como ID sesión | **ALTA** | Contrato V1 congelado define `token_id` = PK refresh = sesión. Objetivo separa `session_id` y `token_id` vigente |
| RC-02 | Campos DTO legacy | Media | `client_type` → `platform`; `ip_address` → `login_ip`/`last_seen_ip`; alias documentados en V1 |
| RC-03 | Paths revoke `{token_id}` | **ALTA** | Self-revoke y admin revoke usan path param `token_id` |
| RC-04 | `/me/` `current_token_id` | Media | FE usa para marcar `is_current` en listado sesiones |
| RC-05 | Superadmin `RefreshTokenInfo` | Media | Schema expone columnas eliminadas del token (`uso_count`, `device_*`) |
| RC-06 | OpenAPI congelado | Media | `ERP-IAM-SESSIONS-API-CONTRACT-V1.md` declara backend congelado hasta V2 |
| RC-07 | Frontend sin cambios | **ALTA** | Re-login obligatorio + posibles cambios DTO |
| RC-08 | Integraciones API externas | Media | Cualquier consumidor de endpoints sesión |
| RC-09 | Datos históricos | Baja | Tokens existentes no migrables al modelo RTR — solo invalidación |
| RC-10 | Trabajo V1 Enterprise en rama | Media | Read service/mapper recién creados sobre premisa incorrecta |

### 9.1 Matriz de campos: actual → objetivo

| Campo API/DTO actual | Fuente actual | Fuente objetivo |
|---------------------|---------------|-----------------|
| `token_id` | `refresh_tokens.token_id` | `refresh_tokens.token_id` (vigente) — **ya no es ID sesión** |
| — (no expuesto) | — | `user_session.session_id` (**nuevo**) |
| `issued_at` | `refresh_tokens.created_at` | `user_session.created_at` o token vigente |
| `last_refresh_at` | `refresh_tokens.last_used_at` | `user_session.last_refresh_at` |
| `expires_at` | `refresh_tokens.expires_at` | `user_session.expires_at` (TTL sesión) |
| `device.*` | Columnas token | Columnas `user_session` |
| `client_type` | `refresh_tokens.client_type` | `user_session.platform` |
| `ip_address` | `refresh_tokens.ip_address` | `user_session.last_seen_ip` (listado) / `login_ip` (auditoría) |
| `is_current` | Compare `token_id` | Compare `session_id` o token vigente |

---

## 10. Estrategia de migración recomendada

> **Nota:** Esta sección describe enfoque de alto nivel derivado del análisis de impacto. No incluye diseño de implementación ni scripts.

### 10.1 Principios

1. **Big bang de datos:** El DDL objetivo invalida sesiones activas — no es viable migración incremental de filas `refresh_tokens` al modelo RTR.
2. **Coordinación deploy:** Backend + DDL + comunicación usuarios en ventana controlada.
3. **Contrato API:** Definir estrategia de compatibilidad `token_id` vs `session_id` **antes** de codificar (ver RC-01).
4. **Sin dual-write prolongado:** El modelo actual y el objetivo son semánticamente incompatibles — dual-write añadiría complejidad sin beneficio.

### 10.2 Fases de alto nivel

| Fase | Alcance | Prerequisito |
|------|---------|--------------|
| **A — Gobernanza** | Aprobar DDL v3, contrato API V2, plan invalidación sesiones | Este documento |
| **B — DDL** | Ejecutar `tables_session_management_new.sql` en central + tenants dedicados | Ventana mantenimiento |
| **C — Infraestructura** | `tables.py` + queries nuevas | Fase B |
| **D — Dominio write** | Login, refresh RTR, logout, revoke, replay | Fase C |
| **E — Dominio read** | Listados, `/me/`, superadmin | Fase D |
| **F — Adyacentes** | Cleanup, password change, user deactivate, deps throttle | Fase D |
| **G — Tests + docs** | Suite completa + actualización documentación | Fases D–F |
| **H — Deploy** | Release coordinado | G completa |

### 10.3 Decisiones pendientes (bloqueantes)

| # | Decisión | Opciones identificadas |
|---|----------|------------------------|
| D-01 | Identificador API sesión | Mantener `token_id` como alias de `session_id`; exponer ambos; breaking change a `session_id` |
| D-02 | Redis session mapping key | `{token_id}` vigente vs `{session_id}` |
| D-03 | Compatibilidad FE | Versión API `/v2/auth/sessions` vs extensión V1 |
| D-04 | Retención forense | TTL purga tokens usados/revocados |
| D-05 | `RevokedReason` mapping | Mapeo enum app ↔ CHECK DB v3 |

---

## 11. Orden recomendado de implementación

Orden derivado del grafo de dependencias (Sección 6) y criticidad de flujos:

| Orden | Workstream | Componentes | Justificación |
|:-----:|------------|-------------|---------------|
| 1 | DDL + SQLAlchemy | Bootstrap migration, `tables.py` | Fundamento — todo depende de esto |
| 2 | Queries write — creación | Insert session+family+token (login) | Desbloquea login en dev/staging |
| 3 | Queries write — rotación | `rotate_*` RTR + replay | Hot path crítico |
| 4 | Queries write — revocación | Revoke token/session/all | Logout flows |
| 5 | RefreshTokenService refactor | Servicio central | Orquesta queries |
| 6 | auth_service adaptación | Login, refresh, logout, empresa | Integración flujos |
| 7 | Queries read + mapper | ActiveSessionsReadService | Listados |
| 8 | Presentation | Endpoints, schemas, OpenAPI | Contrato externo |
| 9 | Adyacentes | password_change, user_service, superadmin, cleanup | Flujos secundarios |
| 10 | deps throttle | `last_business_activity_at` | Feature nueva v3 |
| 11 | Tests | Suite iam_sessions completa | Validación |
| 12 | Documentación | Reemplazar IAM_SESSION_MANAGEMENT_V2 | Operaciones |

---

## 12. Estimación de complejidad

### 12.1 Por capa (escala: S / M / L / XL)

| Capa | Tamaño | LOC afectado est. | Esfuerzo relativo |
|------|:------:|:-----------------:|:-----------------:|
| DDL / migración | L | ~570 SQL nuevo | 3–5 días (incl. multi-DB, validación) |
| SQLAlchemy tables | M | ~200 | 1–2 días |
| Queries auth | **XL** | ~650 existente → ~1200+ nuevo | 8–12 días |
| Services auth | **XL** | ~2500+ | 10–15 días |
| Presentation | L | ~500 | 4–6 días |
| Módulos externos | M | ~200 | 2–3 días |
| Tests | **XL** | ~18 archivos | 8–10 días |
| Documentación | M | — | 2–3 días |
| Integración / QA | L | — | 5–7 días |

### 12.2 Estimación global

| Métrica | Valor |
|---------|-------|
| **Esfuerzo total estimado** | **40–55 días-persona** (1 dev senior backend) |
| **Esfuerzo calendario (1 dev)** | **8–11 semanas** |
| **Esfuerzo calendario (2 devs paralelo)** | **5–7 semanas** |
| **Archivos Python tocados** | ~42 |
| **Funciones query a reescribir/crear** | ~25+ |
| **Endpoints con lógica interna cambiante** | 12 |
| **Tests a reescribir** | ~18 archivos |

### 12.3 Factores de complejidad

| Factor | Peso |
|--------|------|
| Cambio algoritmo replay (nuevo paradigma) | +30% |
| Transacciones 3-tabla en hot path | +25% |
| Invalidación sesiones (no hay rollback de UX) | +15% |
| Compatibilidad API V1 vs V2 | +20% si dual contract; +5% si breaking acordado |
| Trabajo V1 Enterprise reciente a rehacer | +10% |

---

## 13. Riesgos críticos

Los siguientes riesgos requieren mitigación **antes** de iniciar implementación:

| Prioridad | ID | Riesgo | Consecuencia si no se mitiga |
|:---------:|-----|--------|------------------------------|
| **P0** | RC-01 | Identificador sesión API | FE/superadmin roto; revoke paths incorrectos |
| **P0** | RF-01 | Invalidación sesiones en deploy | Incidente operacional masivo sin comunicación |
| **P0** | RT-01 | Atomicidad RTR 3 tablas | Tokens huérfanos; sesiones inconsistentes; bypass seguridad |
| **P0** | RT-03 | Integridad `current_token_id` | Lookup token vigente falla; refresh roto |
| **P1** | RF-05 | Replay más agresivo | Usuarios legítimos forzados a re-login en escenarios edge |
| **P1** | RT-05 | Redis key post-rotación | Access no blacklisteado tras logout de sesión rotada |
| **P1** | RT-07 | Multi-DB migration | Tenants dedicados sin migrar quedan inoperantes |
| **P1** | RT-09 | Cobertura tests replay RTR | Regresión de seguridad no detectada |
| **P2** | RC-10 | Trabajo V1 Enterprise obsoleto | Esfuerzo duplicado si no se replantea antes de continuar |
| **P2** | RT-10 | SQL duplicado superadmin | Divergencia funcional admin vs auth module |

---

## 14. Recomendaciones

### 14.1 Previas a implementación (obligatorias)

1. **Congelar** el trabajo V1 Enterprise de lectura en rama actual hasta definir estrategia — evitar merge de código sobre premisa `sesión = fila token`.
2. **Resolver decisión D-01** (identificador API) con Frontend y documentar en contrato API V2 antes de escribir queries read/revoke.
3. **Aprobar formalmente** el DDL v3 (`tables_session_management_new.sql`) como migración bootstrap (nuevo V0XX) — sin rediseño.
4. **Planificar ventana de deploy** con invalidación de sesiones y comunicación a usuarios/tenants.
5. **Inventariar tenants Multi-DB** para estimar alcance DDL en bases dedicadas.

### 14.2 Durante implementación

6. **Unificar** superadmin sesiones con `ActiveSessionsReadService` — eliminar SQL ad-hoc en `superadmin_usuario_service.py`.
7. **Mantener** patrón `UnitOfWork` + `UPDLOCK` — extender, no reemplazar.
8. **Implementar tests de replay RTR** antes de conectar endpoints — TDD en rotate core.
9. **Documentar mapping** enum `RevokedReason` ↔ CHECK constraints v3 en capa aplicación.
10. **Evaluar** claims JWT refresh (`session_id`, `family_id`) para reducir JOINs en validación.

### 14.3 Post-implementación

11. **Deprecar** documentación obsoleta (`IAM_SESSION_MANAGEMENT_V2.md` monolítico) tras nuevo doc operativo.
12. **Monitorear** métricas: familias comprometidas (`IDX_family_comprometida`), sesiones activas por tenant, latencia refresh.
13. **Revisar** job cleanup — política retención vs espacio BD.

### 14.4 Qué NO hacer

- No intentar migrar filas `refresh_tokens` existentes al modelo RTR — semánticamente incompatible.
- No mantener dual-write entre modelos — complejidad sin beneficio.
- No mergear V1 Enterprise read service sin replantear queries sobre `user_session`.
- No modificar estructura DDL v3 aprobada.

---

## 15. Veredicto final

### 15.1 Conclusión

La refactorización de IAM Session Management hacia el modelo de tres entidades (`user_session`, `token_family`, `refresh_tokens` v3) es un **cambio arquitectónico mayor**, no una evolución incremental del módulo actual.

**Alcance real:**

- **~42 archivos Python** requieren modificación directa.
- **100% de la capa queries auth** de sesiones requiere reescritura.
- **El servicio central `RefreshTokenService` y `auth_service`** son el núcleo crítico (~60% del esfuerzo).
- **~18 archivos de tests** quedan invalidados en su totalidad o parcialmente.
- **Cero componentes** del modelo objetivo existen hoy en código runtime.
- **Deploy invalidará todas las sesiones activas** — impacto operacional inmediato en todos los usuarios.

### 15.2 Nivel de impacto global

| Dimensión | Nivel |
|-----------|:-----:|
| Base de datos | **CRÍTICO** |
| Infraestructura queries | **CRÍTICO** |
| Servicios aplicación | **CRÍTICO** |
| API / contratos | **ALTO** |
| Seguridad (replay/RTR) | **CRÍTICO** (cambio algoritmo) |
| Testing | **ALTO** |
| Compatibilidad FE | **ALTO** |
| Módulos ERP | **NULO** |
| Módulos adyacentes (users, superadmin) | **MEDIO** |

### 15.3 Viabilidad

**VIABLE** con planificación adecuada, decisión de contrato API previa, ventana de deploy coordinada y estimación realista de **8–11 semanas** (1 dev senior).

**NO VIABLE** como quick fix o sprint único — la incompatibilidad semántica entre modelos, el cambio de algoritmo de replay y la invalidación de sesiones lo impiden.

### 15.4 Próximo paso oficial

Tras aprobación de este análisis:

1. Resolver decisiones bloqueantes D-01 a D-05.
2. Elaborar plan de implementación detallado (fase diseño — ticket posterior).
3. Definir contrato API V2 sesiones.
4. Solo entonces iniciar Fase B (DDL) e implementación por capas según Sección 11.

---

## Anexos

### Anexo A — Checklist archivos Python con dependencia directa

```
app/infrastructure/database/tables.py
app/infrastructure/database/queries/auth/refresh_token_queries_core.py
app/infrastructure/database/queries/auth/refresh_token_rotate_queries_core.py
app/infrastructure/database/queries/auth/__init__.py
app/modules/auth/application/services/refresh_token_service.py
app/modules/auth/application/services/rotate_refresh_token_service.py
app/modules/auth/application/services/active_sessions_read_service.py
app/modules/auth/application/services/admin_sessions_service.py
app/modules/auth/application/services/auth_service.py
app/modules/auth/application/services/password_change_service.py
app/modules/auth/application/services/refresh_token_cleanup_job.py
app/modules/auth/application/session/active_session_read_columns.py
app/modules/auth/application/session/session_read_mapper.py
app/modules/auth/application/session/revoked_reason.py
app/modules/auth/application/session/rotate_result.py
app/modules/auth/presentation/endpoints.py
app/modules/auth/presentation/schemas_sessions.py
app/modules/auth/presentation/schemas_admin_sessions.py
app/modules/auth/presentation/schemas.py (parcial)
app/modules/users/application/services/user_service.py
app/modules/superadmin/application/services/superadmin_usuario_service.py
app/modules/superadmin/presentation/schemas.py (parcial)
tests/test_tenant_isolation.py
tests/unit/test_iam_sessions_p0_01.py
tests/unit/test_iam_sessions_p1_01.py
tests/unit/test_iam_sessions_p1_02.py
tests/unit/test_iam_sessions_p1_02_hotfix.py
tests/unit/test_iam_sessions_p1_03.py
tests/unit/test_iam_sessions_p1_04_rotate.py
tests/unit/test_iam_sessions_p1_04_hotfix_01.py
tests/unit/test_iam_sessions_p1_04_refresh_endpoint.py
tests/unit/test_iam_sessions_p1_04_empresa_cambiar.py
tests/unit/test_iam_sessions_pa001.py
tests/unit/test_iam_sessions_rc1.py
tests/unit/test_iam_sessions_v1_enterprise.py
tests/unit/test_iam_me_current_token_id.py
tests/integration/test_iam_me_current_token_id.py
tests/unit/test_iam_session_access_redis_key_casing.py
tests/unit/test_empresa_sesion_auth.py
tests/unit/test_multiempresa_m1.py
tests/unit/test_iam_arch02_path_a_migration.py
```

### Anexo B — Funciones query actuales (`refresh_token_queries_core.py`)

| Función | Operación SQL |
|---------|---------------|
| `record_refresh_token_activity_core` | UPDATE activity |
| `is_refresh_token_session_idle_expired_core` | SELECT idle check |
| `get_refresh_token_by_hash_any_state_core` | SELECT any state |
| `get_refresh_token_by_hash_core` | SELECT active |
| `insert_refresh_token_core` | INSERT |
| `revoke_refresh_token_core` | UPDATE revoke |
| `revoke_all_user_tokens_core` | UPDATE bulk |
| `get_active_sessions_by_user_core` | SELECT list |
| `get_active_sessions_by_user_oldest_first_core` | SELECT oldest |
| `delete_expired_tokens_core` | DELETE |
| `revoke_refresh_token_by_id_core` | UPDATE by id |

### Anexo C — Comparativa `RevokedReason` app vs CHECK v3

| App (`RevokedReason`) | Sesión v3 CHECK | Token v3 CHECK |
|-----------------------|-----------------|----------------|
| `USER_LOGOUT` | `logout` | `logout` |
| `LOGOUT_ALL` | `logout` | `logout` |
| `ADMIN_REVOKE` | `admin_force` | `admin_force` |
| `PASSWORD_CHANGE` | `password_reset` | `password_reset` |
| `USER_DEACTIVATED` | `admin_force` ? | — |
| `USER_DELETED` | — (cascade FK) | — |
| `TOKEN_REUSE` | `security` | `replay_detected` |
| `SESSION_ROTATED` | — (no aplica en RTR) | — (usa `is_used`) |
| `IDLE_TIMEOUT` | `expired` ? | — |
| `SESSION_LIMIT` | `admin_force` ? | — |
| — | `security` | `family_compromised` |

*Mapping exacto requiere decisión en fase diseño (D-05).*

---

**Fin del documento — IAM-BE-IMPACT-ANALYSIS-01**
