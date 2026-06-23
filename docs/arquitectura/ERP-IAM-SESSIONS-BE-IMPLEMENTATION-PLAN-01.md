# ERP-IAM-SESSIONS-BE-IMPLEMENTATION-PLAN-01

**Ticket:** ERP-IAM-SESSIONS-BE-IMPLEMENTATION-PLAN-01  
**Versión:** V1 Enterprise — Sprint único  
**Estado:** Plan definitivo (pre-implementación)  
**Fecha:** 2026-06-21  
**Entradas:** BE-AUDIT-01, BE-DESIGN-01, BE-DESIGN-REVIEW-01  

---

## 1. Resumen ejecutivo

Este documento define **un único plan de implementación** para ejecutar en **un solo sprint**, consolidando el MVP Enterprise V1 acordado en DESIGN-REVIEW-01.

**Alcance:** enriquecer el módulo **Sesiones Activas** exclusivamente en **capa de lectura** + **un endpoint nuevo** (self-revoke) + **auditoría aditiva** post-acción.  
**Fuera de alcance:** migraciones SQL, cambios en tabla `refresh_tokens`, modificaciones a login, refresh/rotación, logout, logout_all o lógica interna de revoke admin.

**Principio rector:** *Máxima mejora funcional con el mínimo cambio arquitectónico.*

**Entregable del sprint:** Frontend puede listar sesiones (usuario y admin) con device enriquecido, expiración, empresa, sesión actual e identificador estable `token_id`; usuario puede revocar sesiones propias remotas; admin mantiene revoke existente con evento de auditoría adicional.

---

## 2. Endpoints canónicos

| Endpoint | Rol | Audiencia | Servicio único |
|----------|-----|-----------|----------------|
| `GET /api/v1/auth/sessions/` | **Canónico usuario** | Usuario autenticado — sus sesiones activas | `ActiveSessionsReadService` |
| `GET /api/v1/auth/sessions/admin/` | **Canónico admin** | Administrador tenant — todas las sesiones activas | `ActiveSessionsReadService` |

**Regla anti-divergencia:** ambos endpoints delegan en **`ActiveSessionsReadService`**. Prohibido mantener dos mappers, dos parsers UA o dos shapes de sesión independientes.

```
GET /sessions/          ──┐
                          ├──► ActiveSessionsReadService
GET /sessions/admin/    ──┘         │
                                    ├── SessionReadMapper (único)
                                    ├── UserAgentParser (único)
                                    └── queries (lectura alineada)
```

**Endpoint adicional (nuevo, no altera revoke admin):**

| Endpoint | Rol |
|----------|-----|
| `POST /api/v1/auth/sessions/{token_id}/revoke/` | Self-revoke — usuario cierra sesión propia por `token_id` |

**Endpoints intocables (cero cambios de lógica):**

- `POST /api/v1/auth/login/`
- `POST /api/v1/auth/refresh/`
- `POST /api/v1/auth/logout/`
- `POST /api/v1/auth/logout_all/`
- `POST /api/v1/auth/sessions/{token_id}/revoke_admin/`

---

## 3. Compatibilidad con Frontend existente

| Cambio | ¿Breaking? | Mitigación |
|--------|:----------:|------------|
| `GET /sessions/` pasa de `List[Dict]` a DTO tipado | No funcional | JSON es **superset** de campos actuales + alias legacy |
| Campos existentes admin (`created_at`, `last_used_at`, etc.) | No | **Conservar nombres**; añadir alias documentados |
| Envelope paginado admin | No | Añadir `items`/`total` **sin eliminar** `sessions`/`total_sesiones` |
| Nuevo POST self-revoke | No | Aditivo |
| Audit post admin revoke | No | Aditivo; respuesta HTTP igual |
| `/me` → `current_token_id` | No | Sin cambios |

**Alias legacy obligatorios en DTO (V1):**

| Campo legacy (FE/consumidor actual) | Campo enriquecido | Notas |
|-------------------------------------|-------------------|-------|
| `created_at` | `issued_at` (mismo valor) | Ambos presentes en respuesta |
| `last_used_at` | `last_refresh_at` (mismo valor) | Ambos presentes |
| `device_name` | `device.device_label` (derivado) | `device_name` puede ser null; FE migra a `device.device_label` |
| `user_agent` (admin) | Oculto en user; admin mantiene opcional | User list no expone UA crudo |

**Semántica documentada (ACCEPTED DEVIATION AD-R01/R02):**

- `issued_at` / `created_at` = emisión del refresh **vigente** (no inicio de sesión lógica pre-rotación).
- `last_refresh_at` / `last_used_at` = última renovación refresh, **no** actividad API.

---

## 4. Arquitectura objetivo V1 (capas)

```
presentation/endpoints.py
    └── ActiveSessionsReadService          ← servicio único
            ├── list_user_sessions()
            ├── list_admin_sessions()
            └── map_row_to_session_read()  ← delega a SessionReadMapper
                    └── UserAgentParser
            queries (solo SELECT):
            ├── get_active_sessions_by_user_core()   [ampliado]
            └── admin query vía AdminSessionsService   [ampliado, delegado]
```

**`AdminSessionsService`:** se mantiene como módulo de **consulta admin** (paginación, filtros, sort). En V1 se refactoriza para que **solo retorne filas SQL** y delegue el mapeo a `ActiveSessionsReadService` / `SessionReadMapper`. No duplica lógica de enriquecimiento.

---

## 5. Modelo de datos de lectura (sin migración)

Columnas leídas de `refresh_tokens` (existentes):

`token_id`, `usuario_id`, `cliente_id`, `empresa_id`, `created_at`, `last_used_at`, `expires_at`, `device_name`, `device_id`, `ip_address`, `user_agent`, `client_type`

Columnas **derivadas en mapper** (no persistidas):

`device.browser`, `device.browser_version`, `device.os`, `device.platform`, `device.device_label`, `is_current`, `status`, `duration_seconds`, `empresa_nombre` (JOIN)

---

## 6. Plan de sprint — fases internas A→G

### Resumen de fases

| Fase | Nombre | Duración relativa |
|------|--------|-------------------|
| A | DTOs y contratos | 15% |
| B | Queries de lectura | 15% |
| C | User-Agent mapping | 10% |
| D | Servicio unificado + Endpoints | 25% |
| E | Auditoría aditiva | 10% |
| F | OpenAPI y documentación | 10% |
| G | Tests y validación | 15% |

---

### Fase A — DTOs

**Objetivo:** definir contratos tipados compartidos usuario/admin, backward compatible.

**Archivos afectados:**

| Archivo | Acción |
|---------|--------|
| `app/modules/auth/presentation/schemas_sessions.py` | **CREAR** — `SessionDeviceRead`, `SessionReadBase`, `UserSessionRead` |
| `app/modules/auth/presentation/schemas_admin_sessions.py` | **MODIFICAR** — `AdminSessionRead` extiende base; `PaginatedAdminSessionsResponse` con alias dual |
| `app/modules/auth/presentation/endpoints.py` | **MODIFICAR** — imports (sin lógica aún) |

**Contenido DTO:**

```text
SessionDeviceRead:
  client_type, browser, browser_version, os, platform,
  device_label, ip_address, device_id (nullable)

SessionReadBase (compartido):
  token_id, usuario_id, cliente_id, empresa_id, empresa_nombre?,
  issued_at, created_at (alias), last_refresh_at, last_used_at (alias),
  expires_at, is_current, status, duration_seconds, device,
  client_type, device_name (legacy nullable), device_id (legacy nullable)

UserSessionRead extends SessionReadBase

AdminSessionRead extends SessionReadBase +
  nombre_usuario, nombre, apellido, user_agent? (admin diagnóstico opcional)

PaginatedAdminSessionsResponse:
  items, total, sessions, total_sesiones,
  pagina_actual, total_paginas, limit
```

**Dependencias:** ninguna.

**Riesgos:**

| Riesgo | Mitigación |
|--------|------------|
| Pydantic rechace filas con campos extra | `model_config = ConfigDict(extra="ignore")` en base |
| FE espera keys exactas del dict previo | Alias duplicados (`created_at`, `last_used_at`) |

**Estrategia de pruebas:** unit tests de validación schema con fixtures dict (Fase G).

**Rollback:** revertir archivos schema; sin impacto runtime.

**Criterio Done:**

- [ ] Schemas importables sin error
- [ ] `AdminSessionRead` es superset del schema actual
- [ ] Alias legacy presentes en modelo
- [ ] Envelope dual definido

---

### Fase B — Queries de lectura

**Objetivo:** alinear columnas SELECT usuario/admin sin tocar INSERT/UPDATE/DELETE.

**Archivos afectados:**

| Archivo | Acción |
|---------|--------|
| `app/infrastructure/database/queries/auth/refresh_token_queries_core.py` | **MODIFICAR** — ampliar `select()` en `get_active_sessions_by_user_core` |
| `app/modules/auth/application/services/admin_sessions_service.py` | **MODIFICAR** — ampliar `_select_columns()`, JOIN `org_empresa` para `empresa_nombre` |
| `app/infrastructure/database/tables.py` | **SOLO LECTURA** — referencia `OrgEmpresa` / tabla empresa si existe alias |

**Columnas a añadir en user query:**

`expires_at`, `user_agent`, `empresa_id`, `device_name`, `device_id` (algunas ya parcialmente presentes; unificar set idéntico al admin base)

**Admin query — JOIN:**

```text
LEFT JOIN org_empresa ON refresh_tokens.empresa_id = org_empresa.empresa_id
→ razon_social o nombre_comercial como empresa_nombre
```

**Dependencias:** Fase A (tipos esperados).

**Riesgos:**

| Riesgo | Mitigación |
|--------|------------|
| JOIN empresa cross-tenant | Filtrar `cliente_id` en WHERE (ya existente) |
| Performance JOIN admin | LEFT JOIN; índice existente `IDX_refresh_token_empresa` |

**Estrategia de pruebas:** unit tests con mock `execute_query`; verificar SQL compilado incluye columnas.

**Rollback:** revertir SELECT a versión anterior; respuestas pierden campos nuevos pero no rompen.

**Criterio Done:**

- [ ] User y admin queries retornan **mismo conjunto base** de columnas refresh_tokens
- [ ] Admin incluye `empresa_nombre`
- [ ] Cero cambios en funciones write de `refresh_token_queries_core.py`

---

### Fase C — User-Agent mapping

**Objetivo:** parser fail-soft y mapper único de fila → DTO enriquecido.

**Archivos afectados:**

| Archivo | Acción |
|---------|--------|
| `app/modules/auth/application/session/user_agent_parser.py` | **CREAR** |
| `app/modules/auth/application/session/session_read_mapper.py` | **CREAR** |
| `app/modules/auth/application/session/__init__.py` | **MODIFICAR** — exports |

**Reglas parser:**

- Entrada: `user_agent: str | None`, `client_type: str`
- Salida: `browser`, `browser_version`, `os`, `platform`, `device_label`
- Fallback: `"Desconocido"` / `platform=unknown`
- Sin dependencias externas pesadas en V1: regex/heurística mínima **o** librería ya presente en `requirements` (evaluar en IMPL; preferir stdlib/regex si no hay dependencia)
- **Fail-soft:** nunca lanzar excepción por UA inválido

**Reglas mapper:**

- `issued_at` ← `created_at`
- `last_refresh_at` ← `last_used_at`
- `duration_seconds` ← `(utcnow - created_at).total_seconds()` clamp ≥ 0
- `status` ← derivado de `expires_at` (`active` | `expiring_soon` si < 24h)
- `is_current` ← parámetro `current_token_id` comparado con `token_id`
- `device.device_label` ← parser; si null y `device_name` en BD → usar `device_name`

**Dependencias:** Fase A.

**Riesgos:**

| Riesgo | Mitigación |
|--------|------------|
| UA vacío masivo | device_label = "{client_type} client" |
| Parser impreciso | Documentar; V2 puede mejorar |

**Estrategia de pruebas:** table-driven tests con UA reales (Chrome, Firefox, Safari iOS, okhttp).

**Rollback:** eliminar módulos; servicio retorna filas sin enriquecer (fallback temporal no deseado — rollback completo del sprint).

**Criterio Done:**

- [ ] Parser cubre web + mobile UA comunes
- [ ] Mapper produce `UserSessionRead` y `AdminSessionRead` desde misma función base
- [ ] Tests unitarios parser + mapper verdes

---

### Fase D — Servicio unificado + Endpoints

**Objetivo:** un solo servicio de lectura; cableado endpoints; self-revoke nuevo.

**Archivos afectados:**

| Archivo | Acción |
|---------|--------|
| `app/modules/auth/application/services/active_sessions_read_service.py` | **CREAR** |
| `app/modules/auth/application/services/admin_sessions_service.py` | **MODIFICAR** — delegar mapeo a servicio unificado |
| `app/modules/auth/application/services/refresh_token_service.py` | **MODIFICAR mínimo** — `get_active_sessions()` delega a `ActiveSessionsReadService` (thin wrapper) **o** endpoint llama directo al nuevo servicio |
| `app/modules/auth/presentation/endpoints.py` | **MODIFICAR** — wire GET sessions, GET admin, POST self-revoke |

**`ActiveSessionsReadService` — API interna:**

```text
async def list_user_sessions(
    cliente_id, usuario_id, *, current_token_id: UUID | None
) -> list[UserSessionRead]

async def list_admin_sessions(
    cliente_id, *, pagination, search, sort_by, sort_order,
    client_type, usuario_id
) -> list[AdminSessionRead] | PaginatedAdminSessionsResponse
```

**`GET /auth/sessions/` — cambios:**

1. Resolver `current_token_id` vía cookie/body refresh (misma lógica que `/me`, extraída a helper **reutilizable** en presentation o servicio — sin modificar `/me` behavior).
2. `response_model=list[UserSessionRead]`
3. Delegar a `ActiveSessionsReadService.list_user_sessions`

**`GET /auth/sessions/admin/` — cambios:**

1. Delegar a `ActiveSessionsReadService.list_admin_sessions`
2. Mantener firma query params existente
3. Envelope dual en respuesta paginada

**`POST /auth/sessions/{token_id}/revoke/` — NUEVO:**

1. Auth: `get_current_active_user`
2. Verificar fila activa: `token_id` + `cliente_id` + `usuario_id == current_user`
3. Cross-owner → **404** (no 403, per ERP cross-scope)
4. Invocar **`RefreshTokenService.blacklist_access_for_token_id`** + **`revoke_refresh_token_by_id`** con `RevokedReason.USER_LOGOUT` (misma primitives que admin; **sin modificar** `revoke_admin` endpoint)
5. Idempotente: ya revocada → 200 con mensaje
6. Response: `{"message": "...", "token_id": "..."}`

**Dependencias:** Fases A, B, C.

**Riesgos:**

| Riesgo | Mitigación |
|--------|------------|
| Duplicar lógica `current_token_id` | Helper compartido read-only |
| Self-revoke confundido con admin | Rutas distintas; permisos distintos |
| Regresión admin paginación | Tests pa001 extendidos |

**Estrategia de pruebas:** unit + integration endpoints (Fase G).

**Rollback:** revertir servicio/endpoints; self-revoke desaparece; GET vuelve a dict legacy.

**Criterio Done:**

- [ ] Un solo mapper en producción
- [ ] User y admin list funcionan
- [ ] Self-revoke operativo con ownership check
- [ ] Cero cambios en endpoints IAM certificados
- [ ] `RefreshTokenService.get_active_sessions` no contiene lógica de enriquecimiento duplicada

---

### Fase E — Auditoría aditiva

**Objetivo:** registrar eventos **después** de acciones exitosas, sin alterar flujos certificados.

**Archivos afectados:**

| Archivo | Acción |
|---------|--------|
| `app/modules/auth/presentation/endpoints.py` | **MODIFICAR** — bloques try/except post-revoke |

**Eventos V1:**

| Evento | Trigger | Ubicación |
|--------|---------|-----------|
| `session_admin_revoked` | Tras revoke admin exitoso | Final de `admin_revoke_session_by_id` — **después** de `revoked == True` |
| `session_self_revoked` | Tras self-revoke exitoso | Nuevo endpoint |

**Metadata JSON estándar:**

```json
{
  "token_id": "uuid",
  "client_type": "web|mobile|null",
  "device_label": "string|null",
  "ip_address": "string|null",
  "empresa_id": "uuid|null",
  "actor_usuario_id": "uuid",
  "actor_type": "admin|self"
}
```

**`device_info` en audit:** poblar con `device_label` del mapper si disponible (requiere pasar contexto request al audit).

**NO implementar en V1:** audit idle, limit, refresh, login, logout (flujos prohibidos).

**Dependencias:** Fase D.

**Riesgos:**

| Riesgo | Mitigación |
|--------|------------|
| Audit falla bloquea revoke | try/except fail-soft (patrón existente) |

**Estrategia de pruebas:** mock `AuditService.registrar_auth_event`; assert llamado con evento correcto.

**Rollback:** eliminar bloques audit; revoke sigue funcionando.

**Criterio Done:**

- [ ] Admin revoke responde igual que antes
- [ ] Eventos registrados fail-soft
- [ ] Metadata incluye `token_id`

---

### Fase F — OpenAPI y documentación

**Objetivo:** contrato OpenAPI preciso; sin breaking documentado.

**Archivos afectados:**

| Archivo | Acción |
|---------|--------|
| `app/modules/auth/presentation/endpoints.py` | **MODIFICAR** — descriptions, response_model, ejemplos |
| `docs/arquitectura/IAM_SESSION_MANAGEMENT_V2.md` | **MODIFICAR** — sección contrato sesiones V1 (aditiva) |
| `docs/arquitectura/ERP-IAM-SESSIONS-BE-IMPLEMENTATION-PLAN-01.md` | Este documento (referencia) |

**Correcciones OpenAPI:**

- `token_id`: UUID (corregir texto "numérico" en revoke_admin)
- Documentar alias `created_at`/`issued_at`
- Documentar semántica `last_refresh_at`
- Documentar envelope dual paginado
- Documentar nuevo self-revoke

**Dependencias:** Fases A, D.

**Riesgos:** ninguno runtime.

**Estrategia de pruebas:** generar schema OpenAPI en test; snapshot campos requeridos.

**Rollback:** revertir docstrings.

**Criterio Done:**

- [ ] Swagger muestra schemas tipados en GET sessions
- [ ] Nuevo endpoint visible en OpenAPI
- [ ] IAM_SESSION_MANAGEMENT_V2 actualizado (sección sesiones activas V1)

---

### Fase G — Tests y validación

**Objetivo:** cobertura regresión + contrato V1.

**Archivos afectados:**

| Archivo | Acción |
|---------|--------|
| `tests/unit/test_iam_sessions_v1_enterprise.py` | **CREAR** |
| `tests/unit/test_iam_sessions_pa001.py` | **MODIFICAR** — envelope dual, campos nuevos |
| `tests/unit/test_iam_me_current_token_id.py` | **SOLO LECTURA** — no modificar behavior /me |
| `tests/integration/test_iam_sessions_v1_enterprise.py` | **CREAR** (opcional si hay DB test) |

**Casos obligatorios:**

| # | Caso |
|---|------|
| T1 | Mapper: UA Chrome Windows → device_label esperado |
| T2 | Mapper: `is_current=True` cuando token_id coincide |
| T3 | Mapper: `status=expiring_soon` cuando expires_at < 24h |
| T4 | User list retorna superset keys legacy |
| T5 | Admin paginado incluye `items` y `sessions` con mismo contenido |
| T6 | Admin incluye `empresa_id`, `empresa_nombre` |
| T7 | Self-revoke propio → 200 |
| T8 | Self-revoke ajeno → 404 |
| T9 | Self-revoke ya revocado → 200 idempotente |
| T10 | Admin revoke audit mock invocado |
| T11 | Regresión: tests P1 existentes (`test_iam_sessions_p*.py`) verdes |
| T12 | OpenAPI: `/auth/sessions/` schema != generic dict |

**Dependencias:** Fases A–F completas.

**Riesgos:**

| Riesgo | Mitigación |
|--------|------------|
| Tests P1 frágiles | No modificar tests rotación/logout |

**Rollback:** N/A (tests no afectan prod).

**Criterio Done:**

- [ ] `pytest tests/unit/test_iam_sessions_v1_enterprise.py` verde
- [ ] Suite IAM sessions existente verde
- [ ] Checklist compatibilidad FE firmada (manual QA)

---

## 7. Verificación de restricciones obligatorias

| Restricción | Cumplimiento |
|-------------|:------------:|
| No modificar Login | ✓ |
| No modificar Refresh Token Rotation | ✓ |
| No modificar Logout / Logout All | ✓ |
| No modificar lógica Revoke Admin | ✓ (solo audit post) |
| No migraciones SQL | ✓ |
| No modificar tabla refresh_tokens | ✓ |
| No modificar write queries refresh_tokens | ✓ |
| Cambios aditivos | ✓ |
| Enriquecimiento solo lectura | ✓ (excepto self-revoke = endpoint nuevo usando primitives existentes) |
| Compatibilidad FE | ✓ (alias legacy) |

---

## 8. Riesgos globales del sprint

| ID | Riesgo | Prob. | Impacto | Mitigación |
|----|--------|-------|---------|------------|
| RG1 | FE dependía de forma exacta dict sin tipos | Baja | Medio | Alias legacy |
| RG2 | `is_current` null en mobile sin cookie en GET | Media | Bajo | Documentar: mobile debe enviar refresh en GET o usar `/me` |
| RG3 | Divergencia user/admin si no se unifica mapper | Media | Alto | Gate review Fase D |
| RG4 | JOIN empresa incorrecto multi-tenant | Baja | Alto | Tests + filtro cliente_id |

---

## 9. Rollback del sprint

**Estrategia:** revert único PR/commit del sprint.

| Componente | Rollback |
|------------|----------|
| BD | No aplica — sin migración |
| Redis | No aplica |
| Endpoints legacy | Restauran behavior previo |
| Self-revoke | Desaparece (nuevo) |
| Audit aditivo | Desaparece — revoke sigue |

**Tiempo estimado rollback:** < 15 min (revert deploy).

---

## 10. Definition of Done — Sprint completo

- [ ] `GET /auth/sessions/` retorna `list[UserSessionRead]` con device, expires, empresa, is_current
- [ ] `GET /auth/sessions/admin/` retorna admin enriquecido + envelope dual
- [ ] Un solo `SessionReadMapper` y un solo `ActiveSessionsReadService`
- [ ] `POST /auth/sessions/{token_id}/revoke/` self-revoke funcional
- [ ] Audit `session_admin_revoked` y `session_self_revoked`
- [ ] Cero cambios en flujos IAM certificados
- [ ] Cero migraciones SQL
- [ ] Tests V1 + regresión IAM verdes
- [ ] OpenAPI actualizado
- [ ] QA manual: FE existente sigue consumiendo campos legacy

---

## 11. Secuencia exacta de ejecución A → G

```
┌─────────────────────────────────────────────────────────────────┐
│  A — DTOs                                                       │
│  schemas_sessions.py (NEW)                                      │
│  schemas_admin_sessions.py (MOD)                                │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  B — Queries lectura                                            │
│  refresh_token_queries_core.py (SELECT user)                    │
│  admin_sessions_service.py (SELECT + JOIN empresa)              │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  C — User-Agent mapping                                         │
│  user_agent_parser.py (NEW)                                     │
│  session_read_mapper.py (NEW)                                   │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  D — Servicio unificado + Endpoints                             │
│  active_sessions_read_service.py (NEW)                          │
│  admin_sessions_service.py (delegación mapper)                    │
│  endpoints.py (GET user, GET admin, POST self-revoke)           │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  E — Auditoría aditiva                                          │
│  endpoints.py (post-revoke audit blocks)                        │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  F — OpenAPI + docs                                             │
│  endpoints.py (descriptions)                                    │
│  IAM_SESSION_MANAGEMENT_V2.md (sección V1)                      │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  G — Tests                                                      │
│  test_iam_sessions_v1_enterprise.py (NEW)                       │
│  test_iam_sessions_pa001.py (MOD)                               │
│  Regresión suite IAM sessions                                   │
└─────────────────────────────────────────────────────────────────┘
                             ▼
                    QA + merge sprint
```

**Orden estricto:** **A → B → C → D → E → F → G** (secuencial; no paralelizar fases que dependen de contratos previos).

**Dentro de cada fase:** implementar → test local → commit atómico interno al sprint (un solo PR final recomendado).

---

## 12. Inventario de archivos del sprint

| Archivo | Fases |
|---------|-------|
| `app/modules/auth/presentation/schemas_sessions.py` | A |
| `app/modules/auth/presentation/schemas_admin_sessions.py` | A, F |
| `app/infrastructure/database/queries/auth/refresh_token_queries_core.py` | B |
| `app/modules/auth/application/services/admin_sessions_service.py` | B, D |
| `app/modules/auth/application/session/user_agent_parser.py` | C |
| `app/modules/auth/application/session/session_read_mapper.py` | C |
| `app/modules/auth/application/session/__init__.py` | C |
| `app/modules/auth/application/services/active_sessions_read_service.py` | D |
| `app/modules/auth/application/services/refresh_token_service.py` | D (thin delegate, opcional) |
| `app/modules/auth/presentation/endpoints.py` | D, E, F |
| `docs/arquitectura/IAM_SESSION_MANAGEMENT_V2.md` | F |
| `tests/unit/test_iam_sessions_v1_enterprise.py` | G |
| `tests/unit/test_iam_sessions_pa001.py` | G |

**Archivos explícitamente PROHIBIDOS de modificar:**

- `app/modules/auth/application/services/auth_service.py` (login/logout/refresh)
- `app/modules/auth/application/services/rotate_refresh_token_service.py`
- `app/infrastructure/database/queries/auth/refresh_token_rotate_queries_core.py`
- `app/bootstrap_v2/**`
- Cualquier migración SQL

---

## 13. Referencias

- ERP-IAM-SESSIONS-BE-AUDIT-01
- ERP-IAM-SESSIONS-BE-DESIGN-01
- ERP-IAM-SESSIONS-BE-DESIGN-REVIEW-01
- `docs/arquitectura/IAM_SESSION_MANAGEMENT_V2.md`

---

**Estado:** Aprobación pendiente → inicio sprint V1-IMPL.
