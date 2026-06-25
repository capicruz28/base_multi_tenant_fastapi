# Especificación Técnica — Reset Administrativo de Contraseña

**Documento:** `ADMIN_PASSWORD_RESET_TECHNICAL_SPEC.md`  
**Fecha:** 2026-06-24  
**Modo:** Especificación técnica (READ ONLY — sin implementación)  
**Fuente normativa:** `app/docs/arquitectura/ADMIN_PASSWORD_RESET_FUNCTIONAL_SPEC.md` (dictamen **A — aprobado**)  
**Estado:** Propuesta técnica para implementación

---

## 0. Resumen ejecutivo

Esta especificación define el contrato HTTP y las decisiones técnicas de Backend para implementar el **Reset Administrativo de Contraseña** dentro del módulo **Gestión de Usuarios**, reutilizando la infraestructura IAM existente (FORCE PASSWORD CHANGE, revocación de sesiones, auditoría auth).

| Decisión clave | Valor |
|----------------|-------|
| **Método** | `POST` |
| **Ruta canónica** | `POST /api/v1/usuarios/{usuario_id}/reset-password/` |
| **Body** | **No requerido** (operación sin entrada de credenciales) |
| **Contraseña temporal** | Autogenerada Backend (12 chars, paridad onboarding) |
| **Permiso RBAC** | `admin.usuario.reset_password` (recomendado) + `require_admin` |
| **Código HTTP éxito** | `200 OK` |

---

## 1. Endpoint canónico

### 1.1 Definición

| Atributo | Valor |
|----------|-------|
| **Método HTTP** | `POST` |
| **Ruta canónica** | `/api/v1/usuarios/{usuario_id}/reset-password/` |
| **Prefijo API** | `settings.API_V1_STR` = `/api/v1` |
| **Router padre** | `app/modules/users/presentation/endpoints.py` |
| **Montaje** | `app/api/v1/api.py` → `prefix="/usuarios"` |
| **Ruta completa** | `POST /api/v1/usuarios/{usuario_id}/reset-password/` |
| **Código HTTP éxito** | `200 OK` |
| **`operationId` sugerido** | `reset_usuario_password_admin` |

### 1.2 Justificación del método HTTP

| Opción evaluada | Decisión |
|-----------------|----------|
| `PUT` / `PATCH` sobre `UsuarioUpdate` | **Descartado** — el schema de actualización no expone `contrasena`; mezclar reset con edición de perfil viola separación de responsabilidades |
| `POST` en `/auth/password/reset-admin/` | **Descartado** — el namespace `/auth` es para operaciones del **usuario autenticado sobre sí mismo** (`password/change`, `logout`); el reset es acción administrativa sobre un tercero |
| `POST` sub-recurso bajo `/usuarios/{id}/` | **Adoptado** — patrón ya usado en `POST /usuarios/{usuario_id}/reactivate/` y asignación de roles |

`POST` es semánticamente correcto: la operación **no es idempotente en efecto** (cada invocación genera una contraseña temporal nueva y revoca sesiones), aunque sea funcionalmente tolerante a reintentos.

### 1.3 Justificación de la ruta

| Criterio | Coherencia |
|----------|------------|
| **Gestión de Usuarios** | Misma colección REST `/usuarios`; acción sobre instancia `{usuario_id}` |
| **Convención existente** | Paridad con `POST /usuarios/{usuario_id}/reactivate/` (verbo-kebab en sub-recurso) |
| **Estándar ERP V4 rutas de proceso** | `POST /{recurso}/{id}/{accion}` — alineado con INV (`/procesar`) y usuarios (`/reactivate`) |
| **IAM / Auth** | Separación clara: `/auth/password/change/` = autoservicio; `/usuarios/.../reset-password/` = admin |
| **OpenAPI / operationId** | Único por path completo (FastAPI incorpora prefijo) |

### 1.4 Alias y variantes descartadas

| Ruta | Estado |
|------|--------|
| `POST /api/v1/usuarios/{usuario_id}/reset-password` (sin slash) | Opcional como alias `include_in_schema=False` (patrón logout) |
| `POST /api/v1/usuarios/{usuario_id}/password/reset/` | Descartado — menor consistencia con `reactivate` |
| `POST /api/v1/admin/usuarios/{usuario_id}/reset-password/` | Descartado — prefijo `/admin` no existe en router usuarios actual |

### 1.5 Ubicación de implementación (orientación, no código)

| Capa | Ubicación sugerida |
|------|-------------------|
| Endpoint | `app/modules/users/presentation/endpoints.py` |
| Schema response | `app/modules/users/presentation/schemas.py` |
| Servicio orquestador | `app/modules/users/application/services/admin_password_reset_service.py` (nuevo, delgado) |
| Delegación sesiones | `SessionRevocationService` / `RefreshTokenService` (auth, existente) |
| Generación contraseña | Reutilizar algoritmo `_generar_contrasena_segura` de `cliente_onboarding_service.py` |

---

## 2. Contrato HTTP

### 2.1 Autenticación y contexto

| Requisito | Detalle |
|-----------|---------|
| **Autenticación** | JWT Bearer obligatorio (`Authorization: Bearer <access_token>`) |
| **Usuario llamante** | Administrador activo del tenant (`get_current_active_user`) |
| **Tenant operativo** | `cliente_id` del JWT del administrador — **única fuente** para filtrar el usuario objetivo |
| **Resolución de tenant** | `TenantMiddleware` por subdominio/Host (sin `cliente_id` en body) |
| **Impersonación** | Permitida si el operador impersonado tiene rol Administrador y permiso RBAC en el tenant impersonado; el `cliente_id` operativo es el del JWT de impersonación |

### 2.2 Headers

| Header | Requerido | Notas |
|--------|-----------|-------|
| `Authorization` | ✅ Sí | Bearer access token |
| `Content-Type` | ❌ No | Solo si se envía body vacío `{}` |
| `X-Client-Type` | ❌ No | No aplica — no emite tokens al administrador |
| `Host` / subdominio | ✅ Implícito | Resolución tenant vía middleware |

### 2.3 Parámetros de ruta

| Parámetro | Tipo | Requerido | Validación |
|-----------|------|-----------|------------|
| `usuario_id` | `UUID` v4 | ✅ Sí | Formato UUID; 422 si inválido (validación FastAPI) |

### 2.4 Query parameters

**Ninguno.** La operación no admite parámetros opcionales en v1.

### 2.5 Body

| Decisión | **Body no requerido** |
|----------|----------------------|
| Motivo | La contraseña es autogenerada (spec funcional §5.3 Opción A); no hay entrada del administrador |
| Forma HTTP | `POST` sin body, o body JSON vacío `{}` aceptado por tolerancia |
| Prohibido | Campos `contrasena`, `password`, `new_password` en body — si se envían, **ignorar** en v1 (no 422) para evitar falsa expectativa de Opción B |

**Justificación:** alineación con onboarding (`POST /clientes/` no recibe contraseña del operador) y eliminación de superficie de ataque (admin no puede imponer contraseñas débiles).

---

## 3. Request

### 3.1 Schema request (especificación futura)

**No se define schema Pydantic de request** — la operación es sin payload.

Si en implementación se desea explicitar en OpenAPI:

```json
null
```

o omitir `requestBody` del decorador FastAPI.

### 3.2 Ejemplo HTTP

```http
POST /api/v1/usuarios/3fa85f64-5717-4562-b3fc-2c963f66afa6/reset-password/ HTTP/1.1
Host: tenant.ejemplo.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

---

## 4. Response

### 4.1 Código HTTP

| Resultado | Código |
|-----------|--------|
| Reset exitoso | `200 OK` |
| Error validación UUID | `422 Unprocessable Entity` |
| Error de negocio | Según tabla §5 |

> **Nota:** `201 Created` se descarta — no se crea un recurso nuevo; se muta credencial de usuario existente (paridad `reactivate` → `200`).

### 4.2 Schema response (especificación futura)

Nombre sugerido: **`AdminPasswordResetResponse`**

| Campo | Tipo | Required | Descripción |
|-------|------|----------|-------------|
| `success` | `boolean` | ✅ | Siempre `true` en 200 |
| `message` | `string` | ✅ | Mensaje operativo en español |
| `usuario_id` | `UUID` | ✅ | ID del usuario afectado |
| `credenciales_temporales` | `CredencialesTemporalesRead` | ✅ | Bloque de entrega única |
| `sesiones_revocadas` | `integer` | ✅ | Cantidad de sesiones invalidadas (`≥ 0`) |

#### Objeto anidado `CredencialesTemporalesRead`

Paridad estructural con `CredencialesInicialesRead` (`app/modules/tenant/presentation/schemas.py`):

| Campo | Tipo | Required | Descripción |
|-------|------|----------|-------------|
| `nombre_usuario` | `string` | ✅ | Login del usuario afectado |
| `contrasena` | `string` | ✅ | Contraseña temporal en texto plano — **solo en esta respuesta** |
| `requiere_cambio` | `boolean` | ✅ | Siempre `true` |

### 4.3 Ejemplo de respuesta exitosa

```json
{
  "success": true,
  "message": "Contraseña restablecida exitosamente. La contraseña temporal solo se muestra una vez; el usuario deberá cambiarla en su próximo acceso.",
  "usuario_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "credenciales_temporales": {
    "nombre_usuario": "jperez",
    "contrasena": "Kx9#mP2vLq4n",
    "requiere_cambio": true
  },
  "sesiones_revocadas": 3
}
```

### 4.4 Información que SÍ debe devolverse

| Dato | Motivo |
|------|--------|
| `nombre_usuario` | El administrador debe comunicar credencial de login al usuario |
| `contrasena` (plano, una vez) | Único canal de entrega (paridad onboarding) |
| `requiere_cambio: true` | Señal explícita de que aplica FORCE PASSWORD CHANGE |
| `usuario_id` | Correlación con UI de Gestión de Usuarios |
| `sesiones_revocadas` | Transparencia operativa para el administrador |
| `message` | Confirmación y advertencia de no reconsulta |

### 4.5 Información que NUNCA debe devolverse

| Dato | Motivo |
|------|--------|
| Hash bcrypt (`contrasena` almacenada) | Secreto irreversible |
| Contraseña anterior (plano o hash) | Sin utilidad; riesgo de exposición |
| Access / refresh tokens del usuario afectado | No corresponde al flujo admin |
| JWT del administrador renovado | La operación no afecta sesión del admin |
| `fecha_ultimo_cambio_contrasena` | No se actualiza en reset (solo en cambio obligatorio del usuario) |
| Roles, permisos o perfil completo | Fuera de alcance; usar `GET /usuarios/{id}/` |
| Metadata de auditoría interna | Solo en `auth_audit_log` |

### 4.6 Persistencia vs respuesta

| Ubicación | Contenido |
|-----------|-----------|
| Base de datos | Solo `hash bcrypt` en `usuario.contrasena` |
| Respuesta HTTP | Solo texto plano en `credenciales_temporales.contrasena` |
| Logs aplicación | `usuario_id`, `admin_usuario_id`, `sesiones_revocadas` — **sin contraseña** |
| `auth_audit_log` | Evento `admin_password_reset` — **sin contraseña ni hash** |

---

## 5. Errores

### 5.1 Formato de error

Patrón existente vía handler global de `CustomException`:

```json
{
  "detail": "Mensaje en español para el cliente",
  "error_code": "INTERNAL_CODE"
}
```

> `error_code` = `internal_code` de la excepción (convención certificada en `AUTH_FRONTEND_CONTRACT_CERTIFICATION.md`).

### 5.2 Catálogo completo

| # | Condición | HTTP | `error_code` | `detail` (español, plantilla) | ¿Efecto en BD? |
|---|-----------|------|--------------|-------------------------------|----------------|
| E1 | Sin token / token inválido | `401` | `AUTH_ERROR` | Según auth deps | No |
| E2 | Usuario llamante inactivo | `401` / `403` | Según deps | Según deps | No |
| E3 | Sin rol «Administrador» | `403` | `AUTHZ_ERROR` | Acceso denegado | No |
| E4 | Sin permiso RBAC | `403` | `AUTHZ_ERROR` | No tiene permiso para esta operación | No |
| E5 | `usuario_id` UUID inválido | `422` | `VALIDATION_ERROR` | Validación FastAPI path | No |
| E6 | Usuario no existe en tenant | `404` | `USER_NOT_FOUND` | Usuario no encontrado en este cliente | No |
| E7 | Usuario eliminado (`es_eliminado = 1`) | `404` | `USER_NOT_FOUND` | Usuario no encontrado en este cliente | No |
| E8 | Cross-tenant (UUID de otro cliente) | `404` | `USER_NOT_FOUND` | Usuario no encontrado en este cliente | No |
| E9 | Usuario SSO (`proveedor_autenticacion ≠ local`) | `400` | `USER_SSO_PASSWORD_NOT_MANAGED` | El restablecimiento de contraseña no está disponible para usuarios SSO externos | No |
| E10 | Auto-reset (`usuario_id == current_user.usuario_id`) | `400` | `SELF_PASSWORD_RESET_NOT_ALLOWED` | No puede restablecer su propia contraseña por esta vía. Use el cambio de contraseña o solicítelo a otro administrador | No |
| E11 | Usuario inactivo (`es_activo = 0`) | — | — | **No es error** — reset permitido (spec funcional §7.2) | Sí (si pasa validaciones) |
| E12 | Fallo persistencia / BD | `500` | `PASSWORD_RESET_FAILED` | Error interno (sin SQL expuesto) | Rollback |
| E13 | Fallo revocación sesiones post-persistencia | `500` | `PASSWORD_RESET_SESSION_REVOKE_FAILED` | Error interno al invalidar sesiones | Ver §7.4 |

### 5.3 Reglas de mapeo HTTP

| Regla ERP V4 | Aplicación |
|--------------|------------|
| Cross-scope → **404** | E6, E7, E8 — nunca `403` que revele existencia en otro tenant |
| Estado inválido de negocio → **400** | E9, E10 — reglas de dominio IAM |
| Sin permiso → **403** | E3, E4 — `AuthorizationError` |
| No encontrado → **404** | E6, E7, E8 — `NotFoundError` |

### 5.4 Errores explícitamente NO aplicables

| Condición | Motivo |
|-----------|--------|
| Usuario con `requiere_cambio_contrasena` ya activo | Re-reset permitido (nueva temporal) |
| Usuario bloqueado (`fecha_bloqueo`) | Reset permitido; bloqueo se normaliza |
| Segundo reset consecutivo | Permitido — no `409` |

### 5.5 Auditoría de intentos fallidos

| Condición | Auditar `admin_password_reset` con `exito=false` |
|-----------|--------------------------------------------------|
| E4, E9, E10 | ✅ Recomendado |
| E6, E7, E8 | ✅ Recomendado (`usuario_id` objetivo si resoluble) |
| E1, E2 | Opcional (login/auth ya audita) |

---

## 6. Seguridad

### 6.1 RBAC

| Capa | Requisito |
|------|-----------|
| **Rol** | `RoleChecker(["Administrador"])` — `require_admin` |
| **Permiso API** | **`admin.usuario.reset_password`** (recomendado) |
| **Dependencias endpoint** | `Depends(require_admin)`, `Depends(require_permission("admin.usuario.reset_password"))`, `Depends(get_current_active_user)` |

#### Decisión de permiso

| Opción | Evaluación |
|--------|------------|
| **`admin.usuario.reset_password` (dedicado)** | ✅ **Recomendado** — acción de seguridad destructiva; permite otorgar reset sin `actualizar` genérico; trazabilidad RBAC fina |
| `admin.usuario.actualizar` (reutilizado) | Aceptable mínimo — paridad con `reactivate`; mezcla edición de perfil con reset de credencial |

**Implementación RBAC:** registrar permiso en sync de startup (`permission_startup`) y asignar al rol `ADMIN_TENANT` en bootstrap RBAC del tenant (mismo patrón que `admin.usuario.eliminar`).

### 6.2 Validaciones tenant

| Validación | Mecanismo |
|------------|-----------|
| Aislamiento `cliente_id` | Toda query con `WHERE cliente_id = :cliente_id_admin` |
| Usuario objetivo en tenant | `execute_*` con `client_id=cliente_id` (BD dedicada) o filtro explícito (BD compartida) |
| Anti cross-tenant | Si `usuario.cliente_id ≠ current_user.cliente_id` → E8 (`404`) |
| Sin `cliente_id` en body/query | Prohibido como fuente de autorización (estándar session scope) |

### 6.3 Validaciones de negocio (orden de ejecución)

```
1. RBAC (deps — antes del servicio)
2. usuario_id ≠ current_user.usuario_id        → E10
3. SELECT usuario por (cliente_id, usuario_id)
4. No existe o es_eliminado=1                  → E6/E7/E8
5. proveedor_autenticacion != 'local'          → E9
6. Generar contraseña + persistir
7. Revocar sesiones
8. Auditar éxito
9. Responder con temporal
```

### 6.4 Efectos en `usuario` (UPDATE atómico)

| Columna | Valor tras reset |
|---------|------------------|
| `contrasena` | Hash bcrypt de temporal nueva |
| `requiere_cambio_contrasena` | `1` (`true`) |
| `intentos_fallidos` | `0` |
| `fecha_bloqueo` | `NULL` |
| `fecha_ultimo_cambio_contrasena` | **Sin cambio** |
| `fecha_actualizacion` | `GETDATE()` |
| `es_activo` | **Sin cambio** |
| `es_eliminado` | **Sin cambio** |

### 6.5 Revocación de sesiones

| Modo sesiones | Componente a invocar |
|---------------|---------------------|
| **IAM V2** (`is_session_v2_enabled(cliente_id)`) | `SessionRevocationService.revoke_due_to_password_change(usuario_id, cliente_id, ip_address, user_agent)` |
| **Legacy V1** | `RefreshTokenService.blacklist_access_for_user_active_sessions` + `RefreshTokenService.revoke_all_user_tokens(..., revoked_reason=RevokedReason.PASSWORD_CHANGE)` |

**Motivo de revocación:** `RevokedReason.PASSWORD_CHANGE` → mapeo `password_reset` en tablas de sesión (V2).

**Alcance:** todas las sesiones del usuario afectado — no las del administrador.

### 6.6 Auditoría

| Evento | `evento` | `exito` | `usuario_id` | Metadata mínima |
|--------|----------|---------|--------------|-----------------|
| Reset exitoso | `admin_password_reset` | `true` | Usuario **afectado** | `admin_usuario_id`, `target_usuario_id`, `target_nombre_usuario`, `initiator=admin`, `sessions_revoked_count` |
| Reset rechazado | `admin_password_reset` | `false` | Afectado o `null` | `admin_usuario_id`, `codigo_error` / `rejection_reason` |
| Revocación sesiones (colateral) | `password_change` (SessionAuditEmitter) | `true` | Afectado | `sessions_revoked_count` — vía emisor existente si aplica |

**Writer:** `AuditService.registrar_auth_event` — fail-soft (no revierte reset).

**Prohibido en metadata:** `contrasena`, hash, tokens.

### 6.7 Rate limiting (recomendación técnica)

No implementado hoy en módulo usuarios. Se recomienda en implementación:

| Límite sugerido | Valor inicial |
|-----------------|---------------|
| Por administrador | 10 resets / hora / tenant |
| Por usuario objetivo | 3 resets / hora |

Implementación futura: middleware o contador Redis — fuera de alcance v1 pero documentado como hardening.

### 6.8 Logging

| Permitido | Prohibido |
|-----------|-----------|
| `admin_usuario_id`, `target_usuario_id`, `cliente_id`, `sesiones_revocadas`, duración ms | Contraseña temporal, hash, tokens |

Patrón: `[ADMIN_PASSWORD_RESET] admin={} target={} cliente={} sesiones={}`

---

## 7. Integración IAM

### 7.1 Componentes existentes — mapa de reutilización

| Componente | Archivo | Uso en reset |
|------------|---------|--------------|
| Generación contraseña | `cliente_onboarding_service._generar_contrasena_segura(12)` | Invocar misma función o extraer a `app/core/security/password_generator.py` |
| Hash | `get_password_hash()` | `app/core/security/password.py` |
| Revocación V2 | `SessionRevocationService.revoke_due_to_password_change` | `session_revocation_service.py` |
| Revocación V1 | `RefreshTokenService.revoke_all_user_tokens` | `refresh_token_service.py` |
| Feature flag V2 | `is_session_v2_enabled(cliente_id)` | `session_v2_feature.py` |
| Motivo revocación | `RevokedReason.PASSWORD_CHANGE` | `revoked_reason.py` |
| Auditoría auth | `AuditService.registrar_auth_event` | `audit_service.py` |
| Auditoría sesión V2 | `SessionAuditEmitter` | Emisión colateral post-revoke |
| Enforcement post-login | `password_change_enforcement.py` | **Sin cambios** — actúa tras login del afectado |
| Cambio obligatorio | `PasswordChangeService.change_password` | **Sin cambios** — resolución por el usuario |
| Lectura flag | `AuthService.resolve_requires_password_change` | **Sin cambios** |
| Excepciones | `NotFoundError`, `ValidationError`, `AuthorizationError` | `app/core/exceptions.py` |
| Patrón revoke en lifecycle | `UsuarioService._revoke_user_sessions_after_lifecycle` | **Referencia** — usar `PASSWORD_CHANGE`, no `USER_DELETED` |

### 7.2 Componentes que NO se crean

| Evitar | Motivo |
|--------|--------|
| Nuevo enforcement de cambio obligatorio | Ya existe |
| Nuevo endpoint de cambio de contraseña | Ya existe en `/auth` |
| Nueva columna BD | Campos suficientes en `usuario` |
| Nuevo motivo de revocación | `PASSWORD_CHANGE` cubre semántica `password_reset` |
| Servicio duplicado de hash/verify | Reutilizar `password.py` |

### 7.3 Orquestación y transaccionalidad

```mermaid
flowchart TD
    A[POST reset-password] --> B[Validar RBAC y reglas]
    B --> C[Generar contraseña temporal]
    C --> D[UPDATE usuario en transacción SQL]
    D --> E{is_session_v2_enabled?}
    E -->|Sí| F[SessionRevocationService.revoke_due_to_password_change]
    E -->|No| G[RefreshTokenService revoke PASSWORD_CHANGE]
    F --> H[AuditService admin_password_reset]
    G --> H
    H --> I[200 + credenciales_temporales]
```

| Fase | Transaccionalidad |
|------|-------------------|
| UPDATE `usuario` | **Atómico** — commit único |
| Revocación sesiones | Post-commit; si falla → E13 (`500`); credencial ya cambiada — estado inconsistente temporal requiere reintento admin o job de limpieza |
| Auditoría | Fail-soft post-éxito |

> **Decisión técnica:** la revocación de sesiones es **post-persistencia de credencial** (mismo orden que `PasswordChangeService`). Un fallo en revocación deja contraseña reseteada pero sesiones activas — se trata como error `500` y se audita; el administrador puede reintentar (genera nueva temporal e invalida sesiones).

### 7.4 Secuencia post-reset (sin cambios en auth)

El usuario afectado utiliza flujos **ya implementados**:

1. `POST /api/v1/auth/login/` → `requires_password_change: true`
2. `POST /api/v1/auth/password/change/` → `current_password` = temporal
3. Acceso ERP normal

---

## 8. OpenAPI esperado

> **No modificar OpenAPI en esta fase.** Especificación para implementación futura.

### 8.1 Metadatos del endpoint

| Campo OpenAPI | Valor |
|---------------|-------|
| `tags` | `["Usuarios"]` |
| `summary` | `Restablecer contraseña de un usuario (administrativo)` |
| `operationId` | `reset_usuario_password_admin` |
| `security` | `[{"OAuth2PasswordBearer": []}]` |
| `response_model` | `AdminPasswordResetResponse` |
| `status_code` | `200` |

### 8.2 Documentación de respuesta sensible

En descripción de `credenciales_temporales.contrasena`:

> «Contraseña temporal en texto plano. **Solo se devuelve en esta respuesta.** No se almacena ni puede recuperarse posteriormente. El usuario deberá cambiarla en el primer acceso.»

Paridad con `CredencialesInicialesRead.contrasena` en OpenAPI de tenant.

### 8.3 Responses documentadas

| Código | Schema | Descripción |
|--------|--------|-------------|
| `200` | `AdminPasswordResetResponse` | Reset exitoso |
| `400` | `HTTPError` | SSO, auto-reset |
| `401` | `HTTPError` | No autenticado |
| `403` | `HTTPError` | Sin permiso |
| `404` | `HTTPError` | Usuario no encontrado en tenant |
| `422` | `ValidationError` | UUID inválido |
| `500` | `HTTPError` | Error interno |

### 8.4 Permisos en descripción OpenAPI

```text
Permisos requeridos:
- Rol 'Administrador'
- Permiso 'admin.usuario.reset_password'
```

---

## 9. Compatibilidad

### 9.1 Onboarding tenant (`POST /clientes/`)

| Aspecto | Compatibilidad |
|---------|----------------|
| Algoritmo de generación | ✅ Mismo (`_generar_contrasena_segura(12)`) |
| Estructura credenciales | ✅ `CredencialesTemporalesRead` ≈ `CredencialesInicialesRead` |
| Entrega única | ✅ Misma semántica |
| Coexistencia | ✅ Sin interferencia — onboarding crea; reset muta existente |

### 9.2 FORCE PASSWORD CHANGE

| Aspecto | Compatibilidad |
|---------|----------------|
| `requiere_cambio_contrasena = 1` | ✅ Activa enforcement existente |
| `PASSWORD_CHANGE_REQUIRED` | ✅ Sin cambios en deps |
| Whitelist auth | ✅ Sin cambios |
| JWT claim | ✅ Propagado en login del afectado |

### 9.3 `POST /auth/password/change/`

| Aspecto | Relación |
|---------|----------|
| Resolución del flag | Usuario afectado desactiva flag al cambiar |
| Validación `current_password` | Temporal emitida en reset es la `current_password` |
| Revocación sesiones en cambio | Segunda revocación al completar cambio — coherente |

### 9.4 Session Management V2

| Aspecto | Compatibilidad |
|---------|----------------|
| `revoke_due_to_password_change` | ✅ Reutilizar directamente |
| Motivo `password_reset` en BD | ✅ Mapeo existente |
| `SessionAuditEmitter.password_change` | ✅ Colateral |
| Feature flag por tenant | ✅ Ramificar V1/V2 como `PasswordChangeService` |

### 9.5 Gestión de Usuarios

| Endpoint existente | Relación |
|--------------------|----------|
| `GET /usuarios/{id}/` | Consulta estado; puede mostrar `requiere_cambio_contrasena: true` post-reset |
| `PUT /usuarios/{id}/` | No modifica contraseña — sin conflicto |
| `POST /usuarios/{id}/reactivate/` | Complementario — admin puede resetear → reactivar → usuario ingresa |
| `DELETE /usuarios/{id}/` | Usuario eliminado no admite reset (E7) |

### 9.6 Alta de usuario (`POST /usuarios/`)

| Aspecto | Distinción |
|---------|------------|
| Contraseña en alta | Definida por admin; `requiere_cambio_contrasena` default `false` |
| Reset | Autogenerada; `requiere_cambio_contrasena` forzado `true` |
| Coexistencia | ✅ Casos de uso distintos |

---

## 10. Riesgos

| ID | Riesgo | Severidad | Mitigación técnica |
|----|--------|-----------|-------------------|
| R1 | Contraseña temporal en logs HTTP / APM | **Alta** | Prohibir log de response body; filtro en middleware de logging |
| R2 | Contraseña en evidencia QA commitada | **Alta** | Tests con mocks; no persistir response en JSON de evidencia |
| R3 | Revocación de sesiones falla post-UPDATE | **Media** | E13 + auditoría; reintento idempotente; monitoreo |
| R4 | Admin malicioso resetea masivamente | **Media** | RBAC dedicado + rate limiting (§6.7) + auditoría de fallos |
| R5 | Exposición cross-tenant vía enumeración UUID | **Baja** | 404 uniforme (E6–E8) |
| R6 | Race: usuario logueado durante reset | **Baja** | Revocación post-UPDATE invalida tokens; ventana mínima |
| R7 | Re-reset invalida temporal anterior sin aviso | **Baja** | Documentar en `message`; comportamiento esperado (spec funcional P6) |
| R8 | Impersonación + reset en tenant ajeno | **Media** | `cliente_id` del JWT impersonado; permisos del rol impersonado |
| R9 | Duplicar lógica de generación de contraseña | **Baja** | Extraer helper compartido con onboarding en implementación |
| R10 | Permiso no asignado en tenants existentes | **Media** | Migración RBAC / script de grant en bootstrap; fallback temporal a `admin.usuario.actualizar` documentado |

---

## 11. Recomendaciones

### 11.1 Implementación

| # | Recomendación |
|---|---------------|
| I1 | Implementar en `users/presentation/endpoints.py` — no en auth router |
| I2 | Servicio orquestador delgado `AdminPasswordResetService` que delegue sesiones a auth |
| I3 | Extraer `_generar_contrasena_segura` a módulo compartido `core/security` para DRY con onboarding |
| I4 | Registrar permiso `admin.usuario.reset_password` en RBAC sync |
| I5 | Tests unitarios: E6–E10, éxito con mock de revocación, verificar UPDATE campos |
| I6 | Test integración: reset → login afectado → `requires_password_change` → change password → ERP |

### 11.2 Contrato

| # | Recomendación |
|---|---------------|
| C1 | Mantener `CredencialesTemporalesRead` alineado con `CredencialesInicialesRead` |
| C2 | Incluir advertencia de entrega única en `message` y OpenAPI |
| C3 | Publicar contrato Frontend en documento separado post-implementación (no en esta fase) |

### 11.3 Seguridad

| # | Recomendación |
|---|---------------|
| S1 | No aceptar contraseña en body en v1 |
| S2 | Auditar rechazos E9 y E10 |
| S3 | Planificar rate limiting en v1.1 |

---

## 12. Dictamen

### 12.1 Evaluación de la especificación técnica

| Criterio | Resultado |
|----------|-----------|
| Traslada fielmente la spec funcional aprobada | ✅ |
| Ruta coherente con Gestión de Usuarios e IAM | ✅ |
| Reutiliza componentes existentes sin duplicar enforcement | ✅ |
| Contrato request/response completamente definido | ✅ |
| Catálogo de errores con códigos y HTTP | ✅ |
| Seguridad RBAC, tenant, auditoría, sesiones | ✅ |
| OpenAPI especificado sin modificarlo | ✅ |
| Compatibilidad con onboarding, FPC, auth/change, V2 | ✅ |
| Riesgos identificados con mitigaciones | ✅ |

### 12.2 Observaciones menores (no bloqueantes)

| # | Observación |
|---|-------------|
| O1 | Confirmar en implementación si se crea `admin.usuario.reset_password` o se reutiliza `admin.usuario.actualizar` |
| O2 | Evaluar extracción de generador de contraseña a `core/security` en el mismo PR |
| O3 | E13 (fallo revocación post-UPDATE) requiere runbook operativo |

### 12.3 Dictamen final

## **A) Especificación técnica aprobada**

El contrato `POST /api/v1/usuarios/{usuario_id}/reset-password/` con body vacío, respuesta `AdminPasswordResetResponse` con entrega única de `credenciales_temporales`, permiso `admin.usuario.reset_password`, reutilización de `SessionRevocationService` / `RefreshTokenService` con `PASSWORD_CHANGE`, y auditoría `admin_password_reset`, es **técnicamente coherente, implementable y alineado con la arquitectura Backend V4 e IAM existente**.

---

*Documento generado en modo READ ONLY. No modifica código, OpenAPI, contratos existentes ni otros documentos del repositorio.*
