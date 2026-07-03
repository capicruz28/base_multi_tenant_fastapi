# F12-E2A — Runtime Logging Audit (READ ONLY)

**Ticket:** F12-E2A — Auditoría del sistema de logging del backend  
**Fecha:** 2026-06-25  
**Alcance:** Todo el proyecto `app/` (+ configuración Docker/uvicorn)  
**Modo:** Solo lectura — **sin cambios implementados**  
**Siguiente fase:** F12-E2B — implementación del plan de limpieza  

**Referencias:** RC-05A (ruido runtime post RC-04), F12-E1 (único ERROR real resuelto: `IllegalStateChangeError`)

---

## 10. Resumen ejecutivo

El backend tiene **~1.596 llamadas a `logger.*`** en **128 archivos Python** bajo `app/`, más **4 `print()` activos en runtime** (RBAC startup + lifespan). La infraestructura de logging está **parcialmente desconectada de la configuración**:

| Mecanismo | Estado actual | Impacto |
|-----------|---------------|---------|
| `settings.LOG_LEVEL` | Definido en `config.py` (default `INFO`) | **No aplicado** en `setup_logging()` — hardcode `logging.INFO` |
| Docker `CMD uvicorn` | `--log-level info` fijo en `Dockerfile` | No respeta `.env` |
| Flags `ENABLE_*_TRACE` | **No existen** | Diagnósticos (`REDIS-TRACE-01`, `RBAC_DEBUG`, etc.) emiten en **WARNING/INFO** siempre |
| `ENVIRONMENT` | `development` \| `production` | Algunos logs condicionados; la mayoría del ruido **no** |

**Distribución por nivel (inventario estático):**

| Nivel | Count | % |
|-------|------:|--:|
| INFO | 589 | 37% |
| WARNING | 367 | 23% |
| DEBUG | 250 | 16% |
| ERROR | 220 | 14% |
| exception (via `logger.exception`) | 165 | 10% |
| CRITICAL | 5 | <1% |

**Conclusión:** El runtime es **funcionalmente estable** (F12-E1), pero **no tiene calidad productiva de logs**. El volumen y nivel de mensajes diagnósticos en INFO/WARNING generan ruido que oculta eventos reales, aumenta I/O y expone datos sensibles en trazas.

**Prioridad F12-E2B (preview):**

1. **P0 — Ruido crítico por request:** Redis trace, RBAC debug, duplicate HTTP logging, QueryAuditor FP.
2. **P1 — Gobernanza:** Conectar `LOG_LEVEL`, introducir flags de diagnóstico, gatear middleware impersonate.
3. **P2 — ERP/modules:** Reducir INFO genérico en presentation/services (user, rbac, modulos, menus).
4. **P3 — Hardening GDPR:** Claims JWT, listas de permisos, fragmentos SQL.

---

## 9. Flags y mecanismos existentes

### 9.1 Variables de entorno relevantes

| Flag / variable | Ubicación | Default | Uso logging |
|-----------------|-----------|---------|-------------|
| `LOG_LEVEL` | `app/core/config.py` | `INFO` | Solo `uvicorn.run()` en `main.__main__`; **no** en `setup_logging()` |
| `ENVIRONMENT` | `config.py` | `development` | Condiciona QueryAuditor, session_scope, middleware producción |
| `ENABLE_QUERY_TENANT_VALIDATION` | `config.py` | `true` | QueryAuditor bloquea/warn en prod |
| `ALLOW_TENANT_FILTER_BYPASS` | `config.py` | `false` | Log WARNING si bypass |
| `ENABLE_REDIS_CACHE` | `config.py` | `true` | Redis client/cache init logs |
| `RBAC_PERMISSION_SYNC_ENABLED` | `config.py` | `true` | Startup RBAC sync |
| `USE_PERMISSION_RESOLVER` | `config.py` | `false` | Permission resolver (pocos logs) |
| `IAM_SESSION_MANAGEMENT_V2_ENABLED` | `config.py` | `false` | Warning si true en prod |
| `PROVISIONING_DISPATCHER_*` | `config.py` | varios | Logs provisioning orchestrator |

### 9.2 Flags **NO existentes** (gap — propuesta F12-E2B)

| Flag propuesto | Cubriría |
|----------------|----------|
| `ENABLE_REDIS_TRACE` | `[REDIS-TRACE-01]`, `[REDIS-RUNTIME-FINAL]`, `[BLACKLIST-DIAG]` |
| `ENABLE_RBAC_TRACE` | `[RBAC_DEBUG]`, `print("[RBAC DEBUG]")` |
| `ENABLE_QUERY_AUDITOR_VERBOSE` | WARNING con SQL truncado en dev |
| `ENABLE_HTTP_TRACE` | Middleware `log_requests` en `main.py` |
| `ENABLE_MIDDLEWARE_TRACE` | `[TENANT]`, `[HOST_DETECTION]` INFO por request |
| `ENABLE_IMPERSONATE_DIAG` | `ImpersonateAuthDiagMiddleware` + `[IMPERSONATE-AUTH]` |
| `ENABLE_AUTH_VERBOSE` | `[ME]`, login/refresh INFO detallado |
| `IS_DEV` / derivado de `ENVIRONMENT` | Gate centralizado |

### 9.3 Infraestructura de logging

| Componente | Archivo | Observación |
|------------|---------|-------------|
| Setup global | `app/core/logging_config.py` | `basicConfig(level=logging.INFO)` fijo; handlers: `logs/app.log` rotativo + stdout |
| Formato | idem | `%(asctime)s - %(name)s - %(levelname)s - %(message)s` |
| Uvicorn | `Dockerfile` L54 | `--log-level info` hardcoded |
| FastAPI lifespan | `main.py` | RBAC startup + shutdown pool/engine |

---

## 1. Inventario completo de logs

### 1.1 Métricas globales

- **Total `logger.*`:** 1.596 invocaciones
- **Archivos con logging:** 128
- **`print()` en runtime (código ejecutable, no docstrings):** 4
  - `app/main.py:255` — `[RBAC] Lifespan executing. Routes: N`
  - `app/core/authorization/permission_startup.py:60,216,441` — `[RBAC DEBUG] ...`
- **`traceback.print_exc()` en `app/`:** 1 (`refresh_token_service.py` — import para diag, no siempre activo)
- **Middleware HTTP custom:** 3 capas con logs (`TenantMiddleware`, `log_requests`, `ImpersonateAuthDiagMiddleware`)

### 1.2 Top 20 archivos por volumen

| # | Archivo | Calls | Dominio |
|---|---------|------:|---------|
| 1 | `modules/users/application/services/user_service.py` | 87 | Users |
| 2 | `modules/rbac/application/services/rol_service.py` | 68 | RBAC |
| 3 | `modules/modulos/application/services/modulo_menu_service.py` | 59 | Menu/Modules |
| 4 | `modules/auth/presentation/endpoints.py` | 57 | Auth API |
| 5 | `modules/auth/application/services/refresh_token_service.py` | 56 | Session/Redis |
| 6 | `core/tenant/middleware.py` | 55 | Tenant |
| 7 | `modules/rbac/presentation/endpoints.py` | 50 | RBAC API |
| 8 | `modules/auth/application/services/auth_service.py` | 50 | Auth |
| 9 | `core/tenant/routing.py` | 42 | Routing |
| 10 | `modules/users/presentation/endpoints.py` | 41 | Users API |
| 11 | `core/authorization/rbac.py` | 38 | RBAC core |
| 12 | `modules/menus/application/services/menu_service.py` | 36 | Menu |
| 13 | `superadmin/.../superadmin_auditoria_service.py` | 33 | Platform audit |
| 14 | `infrastructure/database/queries_async.py` | 31 | DB gateway |
| 15 | `infrastructure/redis/client.py` | 31 | Redis |
| 16 | `menus/presentation/endpoints*.py` | ~61 | Menu API |
| 17 | `infrastructure/database/connection_pool.py` | 28 | DB pool |
| 18 | `api/deps.py` | 26 | Auth deps / `/me` |
| 19 | `tenant/.../cliente_service.py` | 22 | Tenant |
| 20 | `core/security/query_auditor.py` | 17 | Query auditor |

### 1.3 Inventario por subsistema

#### Auth / IAM / Session Store

| Archivo / prefijo | Niveles | Count aprox. | Clasificación dominante |
|-------------------|---------|-------------:|-------------------------|
| `auth_service.py` — `[AUTH]`, `[LOGIN]`, `[REFRESH]` | INFO/WARNING/ERROR | 50 | **A** operaciones + **C** redis trace |
| `endpoints.py` — login, refresh, logout, `/me` | INFO | 57 | **A** eventos + **C** `[ME]` verbose |
| `refresh_token_service.py` — `[REDIS-TRACE-01]`, `[BLACKLIST-DIAG]` | WARNING | 56 | **C/D** — alto impacto performance |
| `session_*_service.py` (creation, rotation, revocation) | WARNING/INFO | ~10 | **B** operacional |
| `session_audit_emitter.py` | ERROR | 1 | **A** auditoría IAM |
| `refresh_token_cleanup_job.py` — `[CLEANUP_JOB]` | INFO/ERROR | 11 | **B/A** |
| `deps.py` — `[ME-ENDPOINT]`, `[IMPERSONATE-AUTH]` | ERROR/INFO/WARNING | 26 | **C** diag + **A** errores |
| `user_builder.py` — `[ME-ENDPOINT]` | ERROR | 4 | **C** payload fields |
| `impersonate_auth_diag.py` | WARNING/INFO | 9 | **C** — JWT claims |
| `impersonation_trace_diag.py` | INFO | 2 | **C** |
| `jwt.py` | ERROR | 2 | **A** |

#### Tenant / Company Gateway / Routing

| Archivo / prefijo | Clasificación |
|-------------------|---------------|
| `middleware.py` — `[TENANT]`, `[HOST_DETECTION]`, `[SECURITY]` | **B** resolución + **C** host debug + **A** security reject |
| `routing.py` — metadata dedicated/shared | **B/C** — 42 calls, muchos DEBUG |
| `context.py` — `[TENANT_CTX]` | **B** DEBUG |
| `session_scope.py` — gates `ENVIRONMENT != development` | **C** — solo dev (13 INFO condicionados) |
| `cache.py` — connection metadata | **B** DEBUG |
| `query_helpers.py` — `[TENANT_FILTER]` | **C/D** — verbose en hot path queries |

#### RBAC / Permission / Menu Resolver

| Archivo / prefijo | Clasificación |
|-------------------|---------------|
| `permission_startup.py` — `[RBAC]`, `print(RBAC DEBUG)` | **A** resumen startup + **D/C** prints por ruta |
| `rbac.py` — `[RBAC_DEBUG]`, deny permiso | **C/D** — WARNING con lista completa permisos |
| `permission_sync_service.py` — `[RBAC]` | **B/A** startup sync |
| `permission_resolver.py` — `[PERMISSION_RESOLVER]` | **B** WARNING fallback |
| `menu_resolver.py`, `menu_permission_*` | **B** DEBUG |
| `rol_service.py`, `permiso_service.py` | **D** — INFO excesivo CRUD (68+28) |

#### Query Auditor / DB

| Archivo | Clasificación |
|---------|---------------|
| `query_auditor.py` — `[QUERY_AUDITOR]` | **A** SecurityError path + **C/D** WARNING con SQL truncado (FP frecuente identity ENGINE_SCOPED) |
| `queries_async.py` — `[GATEWAY]`, errors | **A** errors + **B** DEBUG gateway |
| `connection_async.py`, `connection_pool.py` | **B/A** init + **A** errors |
| `unit_of_work.py` — `[UOW]` | **B** DEBUG commit/rollback |

#### Redis / Session Store (Redis)

| Archivo / prefijo | Clasificación |
|-------------------|---------------|
| `redis/client.py` — `[REDIS-TRACE-01]`, `[REDIS_BLACKLIST]` | **A** connect error + **C** trace en **cada** get/set |
| `redis_cache.py` — `[REDIS_CACHE]` | **B** init + **A** errors |
| `session_redis_bridge.py` | **B** WARNING fail-soft |

#### Identity Gateway

| Archivo | Clasificación |
|---------|---------------|
| `identity_gateway.py` — `[IDENTITY]` | **B** DEBUG login lookup (username en claro) |

#### Platform / Superadmin / Provisioning / Dedicated

| Área | Clasificación |
|------|---------------|
| `superadmin_auditoria_service.py` | **A/B** — auditoría plataforma |
| `audit_service.py` — cross-tenant | **A** — seguridad |
| `dedicated_provisioning_orchestrator.py` | **A/B** — saga estados |
| `provisioning_job_dispatcher.py` | **B** WARNING jobs |
| `bootstrap_script_runner.py` | **A/B** migraciones |

#### Startup / Shutdown / Uvicorn

| Evento | Ubicación | Clasificación |
|--------|-----------|---------------|
| RBAC lifespan + sync | `permission_startup.py`, `main.py` | **A** resumen + **D** prints DEBUG |
| Rate limiting init | `main.py` | **B** INFO |
| Pool/engine close | `main.py` shutdown | **A** INFO |
| Health check error | `main.py` `/health` | **D** — healthcheck ruido si poll frecuente |
| Uvicorn access log | uvicorn (externo) | **D** duplica `log_requests` |

#### ERP modules (ORG, INV, etc.)

Patrón repetido en decenas de módulos: `logger.info("Solicitud GET ...")` + `logger.info("... exitoso")` en presentation, `logger.error` en services. Clasificación mayoritaria **D** en presentation, **A** solo en errors SQL mapeados.

---

## 2. Clasificación A / B / C / D

### 2.1 Categoría A — PRODUCTION REQUIRED (~220–280 calls efectivos)

Deben permanecer en INFO/WARNING/ERROR en producción:

| Evento | Ejemplos / ubicación |
|--------|---------------------|
| Auth lifecycle | Login fallido credenciales, logout, refresh rotación, lockout (`auth_service`, `endpoints`) |
| Errores HTTP/SQL no mapeados | `queries_async` ERROR, `exceptions` handler |
| Redis/DB indisponible | `[REDIS_BLACKLIST] Error conectando`, pool errors |
| Seguridad tenant | `[SECURITY] Request sin subdominio`, token tenant mismatch |
| Startup/shutdown crítico | RBAC sync resumen (3 líneas INFO), engines closed |
| Auditoría crítica | `session_audit_emitter`, `AuditService.registrar_tenant_access`, superadmin auditoría |
| Provisioning estado terminal | dedicated orchestrator ERROR/fail |
| Rate limit exceeded | slowapi handler (uvicorn) |
| IAM V2 replay/revoke failures | `session_rotation_service` WARNING |

### 2.2 Categoría B — OPERATIONAL (~350–450 calls)

Útiles soporte; mantener en DEBUG o INFO con flag:

| Evento | Ubicación |
|--------|-----------|
| Tenant resuelto (sin duplicar) | Una línea por request max |
| Session creada/revocada | IAM V2 services |
| Cache hit/miss metadata | `tenant/cache.py`, `permission_cache` |
| Identity lookup scope | `[IDENTITY]` DEBUG |
| UOW commit/rollback | `[UOW]` DEBUG |
| Cleanup job progreso | `[CLEANUP_JOB]` INFO |
| Provisioning job dispatched | dispatcher INFO |

### 2.3 Categoría C — DIAGNOSTIC (~180–250 calls)

Temporales; **no deben aparecer en prod** sin flag:

| Prefijo / patrón | Archivo(s) | Nivel actual | Problema |
|------------------|------------|--------------|----------|
| `[REDIS-TRACE-01]` | `redis/client.py`, `refresh_token_service.py`, `auth_service.py` | WARNING | Ejecuta SCAN/KEYS/INFO en **cada blacklist** |
| `[REDIS-RUNTIME-FINAL]` | `refresh_token_service.py` | WARNING | Dump Redis state |
| `[BLACKLIST-DIAG]` | `refresh_token_service.py` | WARNING | token_id + keys |
| `[RBAC_DEBUG]` | `rbac.py` | WARNING | Lista completa permisos usuario |
| `[RBAC DEBUG] print` | `permission_startup.py` | stdout | Por cada ruta al startup |
| `[HOST_DETECTION]` | `middleware.py` | DEBUG/WARNING | Headers, origin, referer |
| `[ME-ENDPOINT]` | `deps.py`, `user_builder.py` | ERROR | Claims JWT en error path |
| `[ME]` payload | `endpoints.py` | INFO | Cada `/auth/me/` |
| `[IMPERSONATE-AUTH]` | `deps.py`, `rbac.py`, `impersonate_auth_diag.py` | INFO/WARNING | Claims + headers; middleware **siempre activo** |
| `[QUERY_AUDITOR]` FP | `query_auditor.py` | WARNING | SQL truncado en queries identity ENGINE_SCOPED |
| `[TENANT_FILTER]` verbose | `query_helpers.py` | DEBUG/WARNING | Por query |
| `[RBAC_DEBUG] impersonation` | `rbac.py` | INFO | Solo diag requests |

### 2.4 Categoría D — NOISE (~700–850 calls)

Redundantes o de bajo valor en prod:

| Patrón | Ubicación | Motivo |
|--------|-----------|--------|
| **Doble log HTTP** | `main.log_requests` + `TenantMiddleware` CONTEXTO + uvicorn access | 3 líneas/request mínimo |
| `Solicitud GET/POST ... recibida` | presentation layer (users, rbac, menus, modulos, tenant, auth) | Duplica access log |
| `... exitoso` / `... recuperada` | idem | Sin valor operativo |
| `[TENANT] Cliente resuelto` + `CONTEXTO ESTABLECIDO` | middleware | Redundante |
| `[RBAC] rbac_permission_sync_startup delegado` | `main.py` | Mensaje vacío post-lifespan |
| Health `/health` ERROR log | `main.py` | Poll Docker cada N seg |
| `logger.warning` permiso denegado **antes** de 403 | `rbac.py` L223 | Un WARNING por RBAC check fallido |
| ERP module INFO genérico | ~40+ módulos | Escalabilidad: miles líneas/día |

---

## 3. Duplicados

| # | Duplicación | Capas involucradas | Recomendación F12-E2B |
|---|-------------|-------------------|------------------------|
| D1 | Request HTTP | uvicorn access + `main.log_requests` (2 INFO) + `[TENANT] CONTEXTO ESTABLECIDO` (INFO) | Consolidar en **una** línea structured (request_id, tenant, path, status, ms) |
| D2 | Tenant resuelto | `[TENANT] Cliente resuelto` + `CONTEXTO ESTABLECIDO` | Una sola INFO o DEBUG |
| D3 | Login exitoso | `auth_service` + `endpoints` + posible `[AUTH]` | Un evento **A** con correlation id |
| D4 | RBAC startup | `print` lifespan + `logger.info` delegado + `audit_routes_permissions` | Eliminar print; un resumen **A** |
| D5 | Refresh/logout | `auth_service` + `endpoints` + `refresh_token_service` trace | Operacional en un solo servicio |
| D6 | Query tenant filter | `[QUERY_AUDITOR]` + `[TENANT_FILTER]` | Un mecanismo, un log |
| D7 | Redis connect | `[REDIS_BLACKLIST]` INFO + `[REDIS-TRACE-01]` WARNING | Solo **A** en connect; trace gated |

---

## 4. Logs peligrosos (seguridad / GDPR)

| ID | Riesgo | Evidencia | Severidad |
|----|--------|-----------|-----------|
| S1 | **JWT claims en logs** | `impersonate_auth_diag.log_impersonate_token_claims` decodifica JWT (`sub`, `cliente_id`, `jti`, `exp`, …) | **Alta** |
| S2 | **Lista completa de permisos** | `rbac.py` `[RBAC_DEBUG] ... against=%s` con `permisos_usuario` | **Media** — reconocimiento privilegios |
| S3 | **Fragmentos SQL** | `[QUERY_AUDITOR] Query: {str(query)[:200]}` — puede incluir PII en WHERE | **Media** |
| S4 | **Redis key values** | `[REDIS-RUNTIME-FINAL] get(key=...)=%r` — puede contener JTI/session data | **Media** |
| S5 | **Username en cada identity lookup** | `[IDENTITY] ... username=%r` DEBUG | **Baja** — operacional aceptable en DEBUG gated |
| S6 | **IP + user-agent** | Auth session, audit cross-tenant | **Baja** — necesario auditoría **A**; retención policy |
| S7 | **Authorization header prefix** | `_safe_token_prefix` 24 chars | **Media** — parcial token |
| S8 | **Emails** | No se loguean emails directamente en auth hot path (OK) | — |
| S9 | **Contraseñas** | No encontrado logging de `contrasena`/hash en auth flow (OK) | — |

**Nota GDPR:** Retención `logs/app.log` (5 backups × 1MB) no define política de borrado; F12-E2B debe alinear con retención compliance.

---

## 5. Logs innecesarios (candidatos eliminación o DEBUG)

| Prioridad | Item | Acción F12-E2B sugerida |
|-----------|------|-------------------------|
| P0 | `[REDIS-TRACE-01]` / `[REDIS-RUNTIME-FINAL]` (15+ WARNING por logout) | Eliminar o `ENABLE_REDIS_TRACE=false` default |
| P0 | `[RBAC_DEBUG]` WARNING en `has_permission` | → DEBUG + flag; nunca WARNING |
| P0 | `print("[RBAC DEBUG]")` × N rutas startup | Eliminar |
| P0 | `ImpersonateAuthDiagMiddleware` siempre montado | Opt-in flag; default off prod |
| P1 | `[ME] Datos completos enviados` cada `/me/` | Eliminar o DEBUG |
| P1 | `[QUERY_AUDITOR]` FP identity ENGINE_SCOPED | Allowlist tablas/queries; downgrade DEBUG |
| P1 | `log_requests` middleware duplicado | Desactivar o merge con tenant log |
| P2 | Presentation "Solicitud recibida" (~200+ calls) | Eliminar batch |
| P2 | `[HOST_DETECTION]` en dev default | DEBUG only |
| P3 | ERP modules INFO CRUD | Política: ERROR/WARNING only en presentation |

---

## 6. Logs imprescindibles (no tocar en F12-E2B)

1. **Errores mapeados** propagados a `CustomException` handler (sin SQL crudo al cliente; log interno OK).
2. **Auth denegado** — credenciales incorrectas, usuario inactivo (sin password).
3. **Session IAM** — replay detectado, familia revocada, logout_all (audit trail).
4. **Cross-tenant superadmin** — `AuditService.registrar_tenant_access`.
5. **Security rejects** — subdominio inválido prod, host inválido, tenant token mismatch.
6. **DB/Redis fail-soft/fail-closed** — ERROR con `exc_info` en fallos reales.
7. **Dedicated provisioning** — transiciones saga ERROR (onboarding).
8. **Startup RBAC** — resumen 3 líneas (total/with/missing routes) — no el dump por ruta.

---

## 7. Logs de seguridad

| Tipo | Prefijo / servicio | Nivel | Mantener |
|------|-------------------|-------|----------|
| Tenant isolation reject | `[SECURITY]`, `[TENANT]` error subdominio | ERROR | Sí |
| Query missing tenant filter | `[QUERY_AUDITOR]` → SecurityError prod | ERROR/WARNING | Sí (tune FP) |
| RBAC deny | `Usuario X NO tiene permiso` | WARNING hoy | → DEBUG o audit event estructurado |
| Rate limiting | slowapi | INFO uvicorn | Sí |
| Impersonation | `ImpersonationService`, audit | INFO/A | Sí — sin JWT dump |
| Password change enforce | vía HTTP 403 | Sin log excesivo | OK |
| Encryption key gen | `encryption.py` CRITICAL/WARNING | Sí | Sí — nunca log key value |

---

## 8. Logs de auditoría (negocio / compliance)

| Fuente | Evento | Clasificación |
|--------|--------|---------------|
| `session_audit_emitter.py` | IAM session events → `auth_audit_log` | **A** — persistido, no solo log |
| `AuditService` / superadmin | Cross-tenant access | **A** |
| `superadmin_auditoria_service.py` | Platform audit reads | **A/B** |
| Auth endpoints admin | Session list, revoke | **B** INFO |
| Logs filesystem | `logs/app.log` | No es audit trail legal por sí solo |

**Gap:** Distinguir **application log** vs **audit table** en documentación operativa.

---

## 9 (detalle). Logs de rendimiento

| Hot path | Problema | Impacto estimado |
|----------|----------|------------------|
| `refresh_token_service.blacklist_access_for_token_id` | 10+ WARNING + Redis SCAN/KEYS/INFO por call | **Alto** — I/O Redis + log I/O en logout/refresh |
| `redis/client.get_json` | WARNING trace cada read | **Alto** en auth caliente |
| `TenantMiddleware` | 2–4 logs INFO + DEBUG por request | **Medio** — todo tráfico API |
| `main.log_requests` | 2 INFO por request | **Medio** |
| `rbac.has_permission` | WARNING debug + deny WARNING | **Medio** — por endpoint protegido |
| `query_auditor` + `query_helpers` | WARNING en queries identity | **Medio** — login path |
| `permission_startup` print per route | Startup O(routes) stdout | **Bajo** — solo boot |
| Loops ERP listados | INFO en services | **Bajo** — según uso |

---

## 11. Plan recomendado para F12-E2B

### Fase B0 — Gobernanza (prerrequisito)

1. Conectar `settings.LOG_LEVEL` en `setup_logging()` y propagar a uvicorn/Docker vía env.
2. Introducir flags (mínimo): `ENABLE_REDIS_TRACE`, `ENABLE_RBAC_TRACE`, `ENABLE_HTTP_TRACE`, `ENABLE_MIDDLEWARE_TRACE`, `ENABLE_IMPERSONATE_DIAG`, `ENABLE_QUERY_AUDITOR_VERBOSE` — **default false en production**.
3. Documentar matriz env en `.env.example` (sin cambiar comportamiento prod hasta B1).

### Fase B1 — P0 Ruido runtime (RC-05A carryover)

| # | Cambio | Archivos |
|---|--------|----------|
| B1.1 | Gate/remove `[REDIS-TRACE-01]`, `[REDIS-RUNTIME-FINAL]`, `[BLACKLIST-DIAG]` | `redis/client.py`, `refresh_token_service.py`, `auth_service.py` |
| B1.2 | `[RBAC_DEBUG]` → DEBUG + flag; remove startup `print` | `rbac.py`, `permission_startup.py`, `main.py` |
| B1.3 | Desmontar o gate `ImpersonateAuthDiagMiddleware` | `main.py`, `impersonate_auth_diag.py` |
| B1.4 | Consolidar HTTP logging (1 línea/request) | `main.py`, `middleware.py` |
| B1.5 | QueryAuditor: allowlist ENGINE_SCOPED identity; FP → DEBUG | `query_auditor.py`, `query_helpers.py` |

**Criterio aceptación:** Smoke auth (login/refresh/logout/me) Shared+Dedicated+Platform — **0 WARNING** diagnósticos en log default prod profile.

### Fase B2 — P1 Auth/IAM cleanup

| # | Cambio |
|---|--------|
| B2.1 | `/me` — eliminar `[ME] Datos completos` INFO; mantener ERROR paths sin payload JWT |
| B2.2 | Unificar login/refresh success en un log **A** estructurado |
| B2.3 | `[ME-ENDPOINT]` — solo internal_code + username; no `payload_user_type` dump |

### Fase B3 — P2 Presentation layer policy

- Regla: **presentation/** solo log ERROR + audit events; eliminar "Solicitud recibida" batch (users, rbac, menus, modulos, tenant).
- Excepción: superadmin audit endpoints (reducir a DEBUG).

### Fase B4 — P3 ERP modules (incremental)

- Aplicar política por módulo certificado (ORG/INV referencia).
- No bloqueante para certificación IAM/Auth.

### Fase B5 — Verificación

1. Repetir RC-05A log scan: 0 `[REDIS-TRACE]`, 0 `[RBAC DEBUG]`, 0 QueryAuditor FP en login.
2. `LOG_LEVEL=WARNING` en staging — operaciones **A** aún visibles.
3. `LOG_LEVEL=DEBUG` + flags — diagnósticos recuperables soporte.
4. Regresión: no tocar QueryAuditor enforcement prod, middleware security rejects, audit tables.

### Entregable F12-E2B

- `F12-E2B-RUNTIME-LOGGING-CLEANUP-REPORT.md`
- Diff acotado por fase (PRs separables B1/B2/B3)

---

## Anexo A — Mapa de prefijos diagnósticos

```
[REDIS-TRACE-01]     refresh_token_service, redis/client, auth_service     → C
[REDIS-RUNTIME-FINAL] refresh_token_service                               → C
[BLACKLIST-DIAG]     refresh_token_service                               → C
[RBAC_DEBUG]         rbac.py                                             → C
[RBAC DEBUG]         permission_startup print                            → D
[RBAC]               permission_startup, sync, registry                  → A/B
[QUERY_AUDITOR]      query_auditor.py, queries_async.py                  → A/C
[TENANT_FILTER]      query_helpers.py                                    → C
[TENANT]             middleware.py                                       → B/D
[TENANT_CTX]         context.py                                          → B
[HOST_DETECTION]     middleware.py                                       → C
[ME] / [ME-ENDPOINT] endpoints.py, deps.py, user_builder.py             → C
[IMPERSONATE-AUTH]   deps, rbac, endpoints, impersonate_auth_diag       → C
[IDENTITY]           identity_gateway.py                                 → B
[UOW]                unit_of_work.py                                     → B
[GATEWAY]            queries_async.py                                    → B
[AUTH]/[LOGIN]/[REFRESH]/[LOGOUT]  auth_service, endpoints               → A/B
[CLEANUP_JOB]        refresh_token_cleanup_job.py                        → B
[SESSION-ACCESS]     refresh_token_service                               → B
[REDIS_CACHE]        redis_cache.py                                      → B
[REDIS_BLACKLIST]    redis/client.py                                     → A/B
[PERMISSION_RESOLVER] permission_resolver.py                             → B
[AUDIT]              deps.py cross-tenant                                → A
```

---

## Anexo B — `print()` y traceback activos

| Ubicación | Tipo | Clasificación |
|-----------|------|---------------|
| `main.py:255` | print lifespan RBAC | D |
| `permission_startup.py:60,216,441` | print RBAC DEBUG | C/D |
| `context.py:15`, `routing.py:903`, `cache.py`, `encryption.py` | print en docstring ejemplos | N/A (no runtime) |
| `refresh_token_queries_core.py` | print en docstring Example | N/A |
| `refresh_token_service.py:280` | `traceback.format_exc()` en string log | C — evitar en prod |

---

## Anexo C — Uvicorn vs aplicación

| Fuente | Qué loguea |
|--------|------------|
| Uvicorn access | `GET /path HTTP/1.1" 200` |
| `main.log_requests` | `[cliente_id] ip -> METHOD path` y response + ms |
| TenantMiddleware | `[TENANT] CONTEXTO ESTABLECIDO: cliente_id=... path=...` |
| FastAPI (errors) | Stack en 500 no capturados |

**Recomendación:** En prod, dejar **uvicorn access** O **log_requests** estructurado, no ambos + tenant INFO.

---

*Documento generado en auditoría READ ONLY — F12-E2A. Sin modificaciones al código.*
