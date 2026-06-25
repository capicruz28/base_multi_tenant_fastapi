# Certificación de Contrato Auth — Frontend

**Documento:** `AUTH_FRONTEND_CONTRACT_CERTIFICATION.md`  
**Fecha:** 2026-06-24  
**Modo:** Auditoría READ ONLY (sin cambios de código, OpenAPI ni contratos)  
**Alcance:** Cambio de contraseña, Logout, Logout All  
**Excluido:** Active Sessions, Refresh Token interno, Session Management V2, arquitectura IAM

---

## 1. Objetivo

Certificar qué contratos HTTP del dominio Auth están **listos para consumo por Frontend** en tres flujos operativos:

- Cambio de contraseña
- Cierre de sesión (logout)
- Cierre de todas las sesiones (logout global)

Este documento es la **única fuente de verdad** para que Frontend implemente esos flujos. Describe el contrato observable (ruta, método, schemas, errores, reglas), no la arquitectura interna de sesiones.

---

## 2. Alcance

### 2.1 Incluido

| Área auditada | Evidencia principal |
|---------------|---------------------|
| Router / rutas | `app/modules/auth/presentation/endpoints.py` |
| Montaje API | `app/api/v1/api.py` → prefijo `/auth` bajo `/api/v1` |
| Schemas | `app/modules/auth/presentation/schemas.py` |
| Servicios | `password_change_service.py`, `auth_service.perform_logout` |
| Dependencias JWT | `app/api/deps.py`, `app/core/auth/password_change_enforcement.py` |
| Manejo de errores | `app/core/exceptions.py`, handlers globales |
| OpenAPI | Metadatos de decoradores FastAPI en endpoints |
| Tests | `tests/unit/test_force_password_change.py`, `tests/integration/test_iam_sessions_v2_e2e_smoke.py` |

### 2.2 Excluido (por diseño)

- Listado/revocación admin de sesiones activas
- Rotación interna de refresh, replay detection, Redis, tablas `token_family` / `user_sessions`
- Documentación IAM Session Management V2

### 2.3 Nota sobre nomenclatura de rutas

El brief de auditoría referencia rutas simplificadas (`/auth/change-password`, `/auth/logout-all`). **Las rutas canónicas implementadas difieren.** Frontend debe usar exclusivamente las rutas de la sección 3.

---

## 3. Endpoints auditados

| # | Ruta canónica | Método | Handler | OpenAPI |
|---|---------------|--------|---------|---------|
| 1 | `POST /api/v1/auth/password/change/` | POST | `change_password` | ✅ Incluido (`response_model=Token`) |
| 2 | `POST /api/v1/auth/logout/` | POST | `logout` | ✅ Incluido |
| 3 | `POST /api/v1/auth/logout_all/` | POST | `logout_all_sessions` | ✅ Incluido |

**Alias adicionales (sin impacto FE salvo URL exacta):**

- `POST /api/v1/auth/logout` (sin slash final) — `include_in_schema=False`
- `POST /api/v1/auth/password/change` (sin slash) — reconocido en whitelist interna

**Prefijo API:** `settings.API_V1_STR` = `/api/v1`

---

## 4. Contrato Change Password

### 4.1 Identificación

| Campo | Valor |
|-------|-------|
| **Ruta exacta** | `POST /api/v1/auth/password/change/` |
| **Método HTTP** | `POST` |
| **Estado certificación** | **B) CERTIFIED WITH OBSERVATIONS** |
| **¿Implementable directamente?** | **Sí** |

### 4.2 Request Schema — `PasswordChangeRequest`

| Campo | Tipo | Required | Validación | Notas FE |
|-------|------|----------|------------|----------|
| `current_password` | `string` | ✅ Sí | `min_length=1` | Contraseña actual |
| `new_password` | `string` | ✅ Sí | `min_length=8` + complejidad | Ver reglas §4.7 |
| `refresh_token` | `string \| null` | ❌ No | — | **Solo móvil.** Web: cookie HttpOnly |

**Reglas de `new_password` (Pydantic `@field_validator`):**

- Mínimo 8 caracteres
- Al menos una mayúscula, una minúscula y un número
- Error 422 con mensaje descriptivo si falla validación de schema

### 4.3 Response Schema — `Token`

| Campo | Tipo | Required (respuesta) | Notas FE |
|-------|------|----------------------|----------|
| `access_token` | `string` | ✅ Sí | Nuevo JWT; `requires_password_change: false` |
| `token_type` | `string` | ✅ Sí | Siempre `"bearer"` |
| `user_data` | `UserDataWithRoles \| null` | Opcional | Perfil actualizado; incluye `requires_password_change` |
| `refresh_token` | `string \| null` | Condicional | **Presente solo si `X-Client-Type: mobile`**. Web: cookie HttpOnly |

**Campos relevantes en `user_data` post-cambio:**

- `requires_password_change`: `false`
- `empresa_activa`, `cliente_id`, roles, `access_level` — conservados según sesión previa

### 4.4 Status Codes

| Código | Condición | Formato respuesta |
|--------|-----------|-------------------|
| **200** | Cambio exitoso; nuevos tokens emitidos | Body `Token` (+ cookie refresh en web) |
| **401** | JWT inválido/ausente; contraseña actual incorrecta | `{"detail": "..."}` (HTTPException) |
| **403** | Usuario inactivo; token revocado (blacklist) | `{"detail": "..."}` |
| **400** | Usuario SSO; contraseña nueva = actual; tenant inválido | `{"detail": "..."}` |
| **404** | Usuario no encontrado en BD | `{"detail": "Usuario no encontrado"}` |
| **422** | Validación Pydantic (`new_password` débil, campos faltantes) | `{"detail": "...", "error_code": "VALIDATION_ERROR"}` |
| **500** | Error no mapeado | `{"detail": "Error al cambiar la contraseña"}` |

### 4.5 Posibles errores (mensajes exactos verificados)

| HTTP | `detail` (texto) | Origen |
|------|------------------|--------|
| 401 | `"No se pudieron validar las credenciales"` | JWT ausente/inválido (`oauth2_scheme`) |
| 401 | `"La contraseña actual no es correcta"` | Contraseña actual incorrecta |
| 401 | `"Token revocado"` | Access en blacklist Redis |
| 400 | `"El cambio de contraseña no está disponible para usuarios SSO externos"` | `proveedor_autenticacion != local` |
| 400 | `"La nueva contraseña debe ser diferente a la actual"` | Misma contraseña |
| 400 | `"Contexto de tenant inválido para cambio de contraseña"` | Sin `cliente_id` |
| 403 | `"Usuario inactivo"` | Usuario desactivado |
| 403 | `"Acceso denegado: token no válido para este tenant"` | Cross-tenant no permitido |

### 4.6 Reglas funcionales

1. Valida contraseña actual contra hash en BD.
2. Persiste nuevo hash, fuerza `requiere_cambio_contrasena = false`, actualiza `fecha_ultimo_cambio_contrasena`.
3. Revoca todas las sesiones refresh previas del usuario y emite sesión nueva (access + refresh).
4. Conserva `empresa_id` del JWT access actual al reemitir sesión.
5. Accesible con `requires_password_change=true` — **ruta en whitelist** de enforcement (§4.8).
6. Solo usuarios `proveedor_autenticacion = local`.

### 4.7 Reglas de seguridad

| Regla | Detalle |
|-------|---------|
| JWT requerido | ✅ Sí — `Depends(get_current_active_user)` + `Depends(get_current_user_data)` |
| RBAC / permiso explícito | ❌ No — cualquier usuario autenticado local |
| `require_erp_session` | ❌ No — funciona con selection token |
| Revocación previa | Todas las sesiones refresh del usuario se invalidan antes de emitir la nueva |
| Blacklist access actual | Sí — blacklistea `jti` del access usado en la petición |
| Tenant isolation | Opera sobre `current_user.cliente_id` del contexto tenant |

### 4.8 Headers requeridos

| Header | Web | Mobile | Obligatorio |
|--------|-----|--------|-------------|
| `Authorization: Bearer <access_token>` | ✅ | ✅ | **Sí** |
| `X-Client-Type` | `web` (default) | `mobile` | Recomendado |
| Cookie `refresh_token` | ✅ (HttpOnly) | ❌ | Web: enviar con `credentials: 'include'` |
| Body `refresh_token` | ❌ | ✅ | Mobile: recomendado para revocación limpia |

### 4.9 Compatibilidad

| Dimensión | Compatible | Observación |
|-----------|------------|-------------|
| **Impersonación** | ✅ Sí | Enforcement de force-password **excluye** impersonación |
| **Multiempresa** | ✅ Sí | Reemite sesión con `empresa_id` del JWT; compatible con selection token |
| **Session Scope ERP** | ✅ Parcial | No exige sesión ERP completa; no requiere `empresa_id` en JWT |
| **Force Password Change** | ✅ Sí | Whitelist explícita en `password_change_enforcement.py` |

### 4.10 Eventos de auditoría

| Escenario backend | Evento registrado |
|-------------------|-------------------|
| Tenant con session V2 habilitado | `password_change` (vía emisor de auditoría de sesión) |
| Tenant legacy (V1) | **No hay evento auth explícito** en `PasswordChangeService` |

> Frontend no consume auditoría; evento relevante solo para trazabilidad operativa.

### 4.11 OpenAPI

- `summary`: "Cambiar contraseña del usuario autenticado"
- `response_model=Token` — **consistente** con respuesta real
- Request body: `PasswordChangeRequest` — **consistente**

### 4.12 ¿Frontend necesita lógica especial?

**Sí:**

1. Tras 200: reemplazar access token en memoria/storage; en web confiar en cookie refresh actualizada; en mobile guardar nuevo `refresh_token`.
2. Actualizar `requires_password_change = false` en AuthContext desde `user_data` o decodificando el nuevo access.
3. Interceptor 403 `PASSWORD_CHANGE_REQUIRED` **no debe bloquear** esta ruta (está en whitelist).
4. Validar complejidad de contraseña en FE antes de llamar (misma regla que backend) para UX.
5. Usuarios SSO: ocultar/deshabilitar UI de cambio de contraseña (`400` si intentan).

### 4.13 Ambigüedades detectadas

| ID | Ambigüedad | Impacto FE |
|----|------------|------------|
| A1 | Nombre de ruta ≠ `/auth/change-password` | Usar `/auth/password/change/` |
| A2 | Errores 401/400 vía `HTTPException` no incluyen `error_code`; 422 sí | FE debe leer `detail` (string o array) |
| A3 | Sin evento audit en rama legacy | Ninguno para FE |

### 4.14 ¿Requiere cambios Backend?

**No** para consumo FE. Observaciones menores (A2, audit legacy) no bloquean implementación.

---

## 5. Contrato Logout

### 5.1 Identificación

| Campo | Valor |
|-------|-------|
| **Ruta exacta** | `POST /api/v1/auth/logout/` |
| **Método HTTP** | `POST` |
| **Estado certificación** | **A) CERTIFIED** |
| **¿Implementable directamente?** | **Sí** |

### 5.2 Request Schema

**No hay schema Pydantic declarado en OpenAPI.**

| Origen refresh | Web | Mobile |
|----------------|-----|--------|
| Cookie HttpOnly `refresh_token` | ✅ Automático | ❌ |
| Body JSON `{ "refresh_token": "<token>" }` | ❌ | ✅ |

**Body vacío `{}` es válido** si no hay refresh (logout sigue retornando 200).

### 5.3 Response Schema

**Sin `response_model` en OpenAPI.** Respuesta real verificada:

```json
{
  "message": "Logout successful"
}
```

| Campo | Tipo | Required |
|-------|------|----------|
| `message` | `string` | ✅ Sí — valor fijo `"Logout successful"` |

**Efectos colaterales HTTP (web):**

- Elimina cookies `access_token` y `refresh_token` (path `/`, domain según `COOKIE_DOMAIN`)

### 5.4 Status Codes

| Código | Condición |
|--------|-----------|
| **200** | **Siempre** — idempotente, fail-soft |
| *(otros)* | No se propagan al cliente — errores internos se tragan |

### 5.5 Posibles errores

**Ninguno expuesto al cliente.** El endpoint garantiza 200 incluso si:

- No hay refresh token
- Refresh JWT inválido o ya revocado
- Falla revocación en BD
- Falla limpieza de cookies

### 5.6 Reglas funcionales

1. **Idempotente:** múltiples llamadas → siempre 200.
2. Revoca refresh token en BD si está presente y es válido.
3. Si envía `Authorization: Bearer <access>`, blacklistea `jti` del access (opcional).
4. Limpia cookies de sesión en respuesta web.
5. **No requiere access token** para completar logout (revocación refresh es independiente).

### 5.7 Reglas de seguridad

| Regla | Detalle |
|-------|---------|
| JWT requerido | ❌ **No** — sin `Depends(oauth2_scheme)` |
| RBAC | ❌ No |
| Tenant | `cliente_id` extraído del **JWT refresh**, no del Host |
| Fail-soft | Errores de revocación no impiden 200 |

### 5.8 Headers requeridos

| Header | Web | Mobile |
|--------|-----|--------|
| `X-Client-Type` | `web` (default) | `mobile` |
| Cookie refresh | Recomendado | N/A |
| `Authorization` | Opcional (blacklist access) | Opcional |
| Body `refresh_token` | No | Recomendado |

### 5.9 Compatibilidad

| Dimensión | Compatible | Observación |
|-----------|------------|-------------|
| **Impersonación** | ✅ Sí | Revoca sesión del refresh presente |
| **Multiempresa** | ✅ Sí | Tenant desde refresh JWT |
| **Session Scope** | ✅ N/A | No depende de sesión ERP |
| **Force Password Change** | ✅ Sí | Whitelist — siempre accesible |

### 5.10 Eventos de auditoría

Se registra evento `logout` cuando la revocación legacy se ejecuta con contexto de usuario resuelto. Fail-soft — no afecta respuesta 200.

### 5.11 OpenAPI

- Documentado con descripción detallada de comportamiento idempotente
- **Gap:** no declara request body para mobile (`refresh_token`)
- **Gap:** no declara `response_model`

### 5.12 ¿Frontend necesita lógica especial?

**Sí:**

1. Tras llamada (independiente del body de respuesta): **limpiar AuthContext local** (access, user_data, flags).
2. Web: usar `credentials: 'include'` para enviar cookie refresh.
3. Mobile: enviar `refresh_token` en body JSON.
4. No tratar errores HTTP — esperar siempre 200; redirigir a login.
5. Opcional: enviar Bearer access para invalidación inmediata en Redis.
6. Whitelist force-password: incluir en rutas no interceptadas.

### 5.13 Ambigüedades

| ID | Ambigüedad | Impacto FE |
|----|------------|------------|
| L1 | OpenAPI sin schema de request mobile | Documentar en FE: body `{ refresh_token }` |
| L2 | OpenAPI sin response schema | Usar contrato fijo `{ message: string }` verificado en código |

### 5.14 ¿Requiere cambios Backend?

**No** para consumo FE. Gaps OpenAPI son documentales.

---

## 6. Contrato Logout All

### 6.1 Identificación

| Campo | Valor |
|-------|-------|
| **Ruta exacta** | `POST /api/v1/auth/logout_all/` |
| **Método HTTP** | `POST` |
| **Estado certificación** | **B) CERTIFIED WITH OBSERVATIONS** |
| **¿Implementable directamente?** | **Sí**, con observaciones §6.13 |

> **Nota nomenclatura:** ruta usa `logout_all` (underscore), no `logout-all`.

### 6.2 Request Schema

**Sin body.** Petición vacía.

### 6.3 Response Schema

**Sin `response_model` en OpenAPI.** Respuesta real:

```json
{
  "message": "Se han cerrado {N} sesiones activas para el usuario {username}."
}
```

| Campo | Tipo | Notas |
|-------|------|-------|
| `message` | `string` | Texto libre en español; **no hay campo numérico estructurado** |

### 6.4 Status Codes

| Código | Condición |
|--------|-----------|
| **200** | Revocación global exitosa |
| **401** | JWT inválido/ausente/expirado/revocado |
| **403** | Usuario inactivo; cross-tenant; **force password change activo** (§6.13) |
| **500** | Error no mapeado — `"Error al cerrar todas las sesiones"` |

### 6.5 Posibles errores

| HTTP | `detail` | Condición |
|------|----------|-----------|
| 401 | `"No se pudieron validar las credenciales"` | Sin Bearer |
| 401 | `"Token revocado"` | Access blacklisted |
| 403 | `"Usuario inactivo"` | |
| 403 | `"Acceso denegado: token no válido para este tenant"` | Cross-tenant |
| 403 | `"Debe cambiar su contraseña antes de acceder a este recurso."` + `error_code: "PASSWORD_CHANGE_REQUIRED"` | Force password — **no está en whitelist** |
| 500 | `"Error al cerrar todas las sesiones"` | Excepción no controlada |

### 6.6 Reglas funcionales

1. Requiere access token válido del usuario autenticado.
2. Blacklistea `jti` del access token usado en la petición.
3. Revoca **todos** los refresh tokens / sesiones activas del usuario en el tenant.
4. Retorna mensaje con conteo de sesiones cerradas (`rows_affected`).
5. **El access token actual sigue válido hasta expirar naturalmente**, pero no podrá renovarse (sin refresh vigente).

### 6.7 Reglas de seguridad

| Regla | Detalle |
|-------|---------|
| JWT requerido | ✅ Sí — `Depends(get_current_active_user)` |
| RBAC / permiso | ❌ No — cualquier usuario autenticado puede cerrar **sus propias** sesiones |
| Scope | Solo sesiones del `usuario_id` + `cliente_id` del usuario autenticado |
| `require_erp_session` | ❌ No |

### 6.8 Headers requeridos

| Header | Obligatorio |
|--------|-------------|
| `Authorization: Bearer <access_token>` | **Sí** |
| `X-Client-Type` | Opcional (no afecta lógica de logout_all) |

### 6.9 Compatibilidad

| Dimensión | Compatible | Observación |
|-----------|------------|-------------|
| **Impersonación** | ⚠️ Parcial | Revoca sesiones del usuario impersonado (`sub` del JWT), no del operador |
| **Multiempresa** | ✅ Sí | Scope tenant del contexto |
| **Session Scope** | ✅ Parcial | No exige sesión ERP completa |
| **Force Password Change** | ❌ **Bloqueado** | No está en whitelist — retorna 403 `PASSWORD_CHANGE_REQUIRED` |

### 6.10 Eventos de auditoría

| Rama backend | Evento |
|--------------|--------|
| Session V2 habilitado | `logout_all` |
| Legacy V1 | `logout_forced` |

### 6.11 OpenAPI

- Descripción advierte que access sigue válido hasta expirar — **consistente con código**
- **Gap:** sin `response_model`
- **Gap:** no documenta bloqueo por force-password

### 6.12 ¿Frontend necesita lógica especial?

**Sí:**

1. Tras 200: **limpiar AuthContext y redirigir a login inmediatamente** (access aún usable unos minutos).
2. No parsear conteo desde `message` — tratarlo como confirmación UX opcional.
3. Durante flujo force-password: **no usar logout_all**; usar `POST /auth/logout/` (whitelist) o completar cambio de contraseña primero.
4. Mostrar confirmación modal antes de ejecutar (acción destructiva multi-dispositivo).

### 6.13 Ambigüedades

| ID | Ambigüedad | Severidad |
|----|------------|-----------|
| G1 | Ruta `logout_all` vs `logout-all` | Baja — usar underscore |
| G2 | Respuesta `message` no estructurada | Media — no hay `sessions_closed: number` |
| G3 | **logout_all bloqueado con force-password** mientras logout simple sí funciona | **Media** — FE debe evitar logout_all en ese estado |
| G4 | OpenAPI no refleja G3 | Baja |

### 6.14 ¿Requiere cambios Backend?

**No bloqueante** para MVP FE si se documenta G3.  
**Mejora recomendada (opcional):** añadir `POST /auth/logout_all/` a whitelist force-password o retornar schema estructurado — ver §10.

---

## 7. Compatibilidad Frontend

### 7.1 AuthContext — contrato esperado

| Acción FE | Endpoint | Actualización AuthContext |
|-----------|----------|---------------------------|
| Cambiar contraseña | `POST /auth/password/change/` | Reemplazar tokens; `requires_password_change=false`; actualizar `user_data` |
| Logout dispositivo actual | `POST /auth/logout/` | Wipe completo; redirect login |
| Logout todos los dispositivos | `POST /auth/logout_all/` | Wipe completo; redirect login; no confiar en access residual |

### 7.2 Matriz cliente Web vs Mobile

| Concern | Web | Mobile |
|---------|-----|--------|
| Access token | Header `Authorization` | Header `Authorization` |
| Refresh token | Cookie HttpOnly (auto) | Body JSON en logout/change |
| Header tipo cliente | Omitir o `X-Client-Type: web` | `X-Client-Type: mobile` |
| Fetch credentials | `credentials: 'include'` | Default |
| Post-login storage | Access en memoria/storage; refresh en cookie | Ambos tokens en secure storage |

### 7.3 Integración con Force Password Change

Whitelist verificada en `password_change_enforcement.py`:

| Ruta | Permitida con `requires_password_change=true` |
|------|-----------------------------------------------|
| `POST /auth/password/change/` | ✅ |
| `POST /auth/logout/` | ✅ |
| `POST /auth/logout_all/` | ❌ |
| `GET /auth/me/` | ✅ |
| `POST /auth/refresh/` | ✅ |
| `POST /auth/empresa/seleccionar/` | ✅ |

Interceptor FE debe excluir rutas whitelist del redirect a pantalla de cambio de contraseña.

### 7.4 Formato de errores — consistencia

| Origen | Formato |
|--------|---------|
| `CustomException` (403 password, etc.) | `{ "detail": string, "error_code": string }` |
| `HTTPException` (401 contraseña incorrecta, etc.) | `{ "detail": string }` — **sin `error_code`** |
| `RequestValidationError` (422) | `{ "detail": string \| string[], "error_code": "VALIDATION_ERROR" }` |

Frontend debe normalizar leyendo `detail` como string primario; usar `error_code === "PASSWORD_CHANGE_REQUIRED"` solo cuando exista.

---

## 8. Casos borde

| # | Caso | Endpoint | Comportamiento esperado | Acción FE |
|---|------|----------|-------------------------|-----------|
| E1 | Sin refresh en logout | logout | 200, cookies limpiadas | Limpiar estado local |
| E2 | Refresh ya revocado | logout | 200 idempotente | Limpiar estado local |
| E3 | Access expirado, refresh válido | logout | 200, revoca refresh | Limpiar estado local |
| E4 | Contraseña temporal incorrecta | change | 401 | Mostrar error |
| E5 | Usuario SSO intenta cambiar | change | 400 | Ocultar feature |
| E6 | Force-password + logout_all | logout_all | 403 PASSWORD_CHANGE_REQUIRED | Usar logout simple |
| E7 | Force-password + change OK | change | 200, flag false | Continuar flujo ERP |
| E8 | Selection token sin empresa | change | 200, sesión reemitida sin empresa | Redirigir a selección empresa si aplica |
| E9 | Impersonación activa | change / logout_all | Opera sobre usuario impersonado | UI debe indicar contexto |
| E10 | logout_all con 0 sesiones activas | logout_all | 200, `"Se han cerrado 0 sesiones..."` | Tratar como éxito |
| E11 | Redis caído durante logout | logout | 200 fail-soft | Limpiar estado local igualmente |
| E12 | Access enviado en logout | logout | Blacklist jti adicional | Enviar Bearer recomendado |

---

## 9. Riesgos

| ID | Riesgo | Probabilidad | Impacto | Mitigación FE |
|----|--------|--------------|---------|---------------|
| R1 | Access sigue válido post-logout_all | Alta (by design) | Medio | Redirect login + wipe local inmediato |
| R2 | logout_all bloqueado en force-password | Media | Bajo | Usar logout simple en ese flujo |
| R3 | Errores sin `error_code` uniforme | Alta | Bajo | Parsear `detail` textual |
| R4 | Conteo sesiones solo en string | Media | Bajo | No depender del número en `message` |
| R5 | Rutas con nomenclatura distinta al brief | Alta | Alto | Usar rutas §3 exclusivamente |
| R6 | OpenAPI incompleto en logout/logout_all | Media | Bajo | Este documento como fuente de verdad |

---

## 10. Recomendaciones

### 10.1 Frontend (implementación inmediata)

1. Centralizar constantes de ruta con paths exactos de §3.
2. Implementar normalizador de errores auth (`detail` + `error_code` opcional).
3. En force-password: permitir logout y change; **no** logout_all.
4. Post-change: actualizar AuthContext desde response `Token`, no requerir `/me`.
5. Post-logout/logout_all: wipe agresivo de storage + redirect login.

### 10.2 Backend (mejoras futuras — fuera de alcance actual)

| Prioridad | Mejora |
|-----------|--------|
| P2 | Añadir `response_model` tipado para logout y logout_all |
| P2 | Documentar body mobile en OpenAPI de logout |
| P3 | Incluir `logout_all` en whitelist force-password **o** documentar intencionalidad |
| P3 | Retornar `{ "message": "...", "sessions_closed": N }` estructurado |
| P3 | Unificar errores auth bajo `CustomException` con `error_code` |

---

## 11. Checklist para Frontend

### Cambio de contraseña

- [ ] Ruta: `POST /api/v1/auth/password/change/`
- [ ] Header `Authorization: Bearer <access>`
- [ ] Web: `credentials: 'include'`; mobile: `X-Client-Type: mobile` + `refresh_token` en body
- [ ] Body: `{ current_password, new_password }` (+ `refresh_token` mobile)
- [ ] Validar complejidad en FE (8+, mayúscula, minúscula, número)
- [ ] Manejar 401 contraseña incorrecta, 400 SSO, 422 validación
- [ ] Tras 200: reemplazar tokens; `requires_password_change = false`
- [ ] Excluir ruta del interceptor force-password

### Logout

- [ ] Ruta: `POST /api/v1/auth/logout/`
- [ ] Web: cookie refresh automática + `credentials: 'include'`
- [ ] Mobile: body `{ "refresh_token": "..." }`
- [ ] Opcional: Bearer access para blacklist inmediato
- [ ] Esperar siempre 200; limpiar AuthContext; redirect login
- [ ] Excluir ruta del interceptor force-password

### Logout All

- [ ] Ruta: `POST /api/v1/auth/logout_all/` (underscore)
- [ ] Header `Authorization: Bearer <access>` obligatorio
- [ ] Confirmación UX previa (multi-dispositivo)
- [ ] Tras 200: wipe AuthContext + redirect login (no esperar expiración access)
- [ ] **No invocar** si `requires_password_change=true` — usar logout simple
- [ ] Manejar 401/403/500

### AuthContext global

- [ ] Interceptor 403: detectar `error_code === "PASSWORD_CHANGE_REQUIRED"`
- [ ] Whitelist rutas §7.3 en interceptor
- [ ] SSO: ocultar cambio de contraseña
- [ ] Impersonación: mostrar contexto; operaciones afectan usuario impersonado

---

## 12. Dictamen Final

### 12.1 Resumen por endpoint

| Endpoint | Estado | Veredicto |
|----------|--------|-----------|
| `POST /api/v1/auth/password/change/` | **B) CERTIFIED WITH OBSERVATIONS** | Implementable ya |
| `POST /api/v1/auth/logout/` | **A) CERTIFIED** | Implementable ya |
| `POST /api/v1/auth/logout_all/` | **B) CERTIFIED WITH OBSERVATIONS** | Implementable ya (evitar en force-password) |

### 12.2 Verificación de contratos

| Criterio | Resultado |
|----------|-----------|
| Nombres de campos request/response | ✅ Consistente schemas ↔ código |
| Required / optional | ✅ Documentado §4–§6 |
| Formatos y validaciones | ✅ Alineado Pydantic ↔ servicios |
| Enums | N/A en estos endpoints |
| Mensajes de error | ⚠️ Consistentes en texto; formato JSON mixto |
| Códigos HTTP | ✅ Verificados en código |
| OpenAPI ↔ código | ⚠️ change OK; logout/logout_all sin response_model |
| ERP_BACKEND_STANDARDS_V4 | ✅ Sin violaciones ERP (dominio auth) |
| ERP_BACKEND_RULES_V4 | ✅ Errores mapeados; sin DELETE físico; tenant filtrado |

### 12.3 Dictamen global

# **B) READY WITH OBSERVATIONS**

Los tres endpoints están **funcionalmente listos** para consumo Frontend. No se identificaron bloqueos que impidan implementación inmediata.

**Observaciones que no impiden go-live:**

1. Rutas canónicas difieren del naming simplificado del brief (`password/change/`, `logout_all/`).
2. Gaps menores en OpenAPI (response/request schemas de logout).
3. Formato de error heterogéneo (`HTTPException` vs `CustomException`).
4. `logout_all` bloqueado durante force-password (workaround: logout simple).
5. Respuesta logout_all sin campo numérico estructurado.

**No se requiere cambio Backend previo** para que Frontend implemente los tres flujos conforme a este contrato.

---

*Documento generado por auditoría READ ONLY — 2026-06-24.*  
*Evidencia: código fuente en `app/modules/auth/`, `app/api/deps.py`, `app/core/auth/password_change_enforcement.py`.*
