# Contrato Backend → Frontend — FORCE PASSWORD CHANGE

**Versión:** 1.0 (definitiva)  
**Fecha:** 2026-06-08  
**Estado Backend:** Aprobado — sin más cambios de código previstos  
**Base API:** `/api/v1`  
**Relacionado:**
- [`FORCE_PASSWORD_CHANGE_IMPLEMENTATION_REPORT.md`](FORCE_PASSWORD_CHANGE_IMPLEMENTATION_REPORT.md)
- [`FORCE_PASSWORD_CHANGE_WHITELIST_MATRIX.md`](FORCE_PASSWORD_CHANGE_WHITELIST_MATRIX.md)

---

## 0. Resumen para Frontend

Cuando un usuario local (`proveedor_autenticacion = 'local'`) tiene `requiere_cambio_contrasena = 1` en BD:

1. **Login siempre es exitoso** (200) si las credenciales son válidas.
2. El backend devuelve `requires_password_change: true` en `user_data` y en el JWT.
3. **Todas las rutas ERP** devuelven `403` con `error_code: "PASSWORD_CHANGE_REQUIRED"`.
4. Rutas auth permitidas sin cambio previo: ver sección 6 (whitelist).
5. Tras `POST /auth/password/change/` exitoso, el flag pasa a `false` y se emiten tokens nuevos.

**Fuente de verdad recomendada para el flag en UI:**

| Prioridad | Origen |
|-----------|--------|
| 1 | `user_data.requires_password_change` (login / change password) |
| 2 | `GET /auth/me` → `requires_password_change` |
| 3 | JWT decodificado → claim `requires_password_change` (opcional, no sustituye BD tras refresh) |

---

## 1. Login

### 1.1 Endpoint

```
POST /api/v1/auth/login/
```

### 1.2 Request completo

| Aspecto | Valor |
|---------|-------|
| Content-Type | `application/x-www-form-urlencoded` |
| Tenant | Resuelto por **subdominio/Host** (`TenantMiddleware`). No va en el body. |
| Auth | OAuth2 password flow (no JSON body) |

**Headers obligatorios / recomendados:**

| Header | Valor | Notas |
|--------|-------|-------|
| `X-Client-Type` | `web` (default) o `mobile` | Define dónde va el refresh token |
| `Content-Type` | `application/x-www-form-urlencoded` | Requerido |

**Body (form-urlencoded):**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `username` | string | Sí | Nombre de usuario |
| `password` | string | Sí | Contraseña |

**Ejemplo request (web):**

```http
POST /api/v1/auth/login/ HTTP/1.1
Host: acme.tu-dominio.com
Content-Type: application/x-www-form-urlencoded
X-Client-Type: web

username=admin&password=TempPass123!
```

**Ejemplo request (mobile):**

```http
POST /api/v1/auth/login/ HTTP/1.1
Host: acme.tu-dominio.com
Content-Type: application/x-www-form-urlencoded
X-Client-Type: mobile

username=admin&password=TempPass123!
```

### 1.3 Response — variantes

`response_model`: `Union[Token, LoginEmpresaSelectionResponse]`

#### A) Login exitoso — sesión completa (`Token`)

**Web:** `access_token` en JSON; `refresh_token` en cookie HttpOnly `refresh_token`.

**Mobile:** `access_token` + `refresh_token` en JSON.

#### B) Login exitoso — requiere selección empresa (`LoginEmpresaSelectionResponse`)

Sin refresh; solo `selection_token` (JWT temporal con `empresa_selection_pending: true`).

### 1.4 Ubicación exacta de `requires_password_change`

| Ubicación | Presente | Notas |
|-----------|----------|-------|
| `response.user_data.requires_password_change` | **Sí** | **Principal para FE** |
| JWT `access_token` (claim) | **Sí** | Claim `requires_password_change: boolean` |
| JWT `refresh_token` (claim) | **Sí** | Mismo claim; refresh re-lee BD al rotar |
| Raíz del response | **No** | Solo dentro de `user_data` |
| Cookie | **No** | — |

### 1.5 Ejemplo JSON real — login admin onboarding (web, sesión completa)

**Escenario:** Tenant recién creado; usuario `admin` con contraseña temporal; una sola empresa o admin sin selección.

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_data": {
    "usuario_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "nombre_usuario": "admin",
    "correo": "admin@tenant-demo.test",
    "nombre": "Administrador",
    "apellido": "Tenant Demo S A",
    "es_activo": true,
    "roles": ["Administrador"],
    "access_level": 4,
    "is_super_admin": false,
    "user_type": "tenant_admin",
    "cliente_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "es_admin_cliente": true,
    "empresa_activa": null,
    "requires_password_change": true
  }
}
```

> En **web** no aparece `refresh_token` en JSON; se establece cookie `refresh_token` (HttpOnly).

### 1.6 Ejemplo JSON real — login multi-empresa (selección pendiente)

```json
{
  "requiere_seleccion_empresa": true,
  "empresas_disponibles": [
    {
      "empresa_id": "11111111-1111-1111-1111-111111111111",
      "razon_social": "Empresa Alpha S.A.C.",
      "nombre_comercial": "Alpha"
    },
    {
      "empresa_id": "22222222-2222-2222-2222-222222222222",
      "razon_social": "Empresa Beta S.A.C.",
      "nombre_comercial": "Beta"
    }
  ],
  "selection_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_data": {
    "usuario_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "nombre_usuario": "admin",
    "correo": "admin@tenant-demo.test",
    "nombre": "Administrador",
    "apellido": null,
    "es_activo": true,
    "roles": ["Administrador"],
    "access_level": 4,
    "is_super_admin": false,
    "user_type": "tenant_admin",
    "cliente_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "es_admin_cliente": true,
    "requires_password_change": true
  }
}
```

### 1.7 Comportamiento Frontend tras login

| `requires_password_change` | Acción FE |
|---------------------------|-----------|
| `true` | Redirigir a pantalla **Cambio de contraseña obligatorio** antes de ERP |
| `false` | Flujo normal (empresa selection si aplica, luego ERP) |

**Importante:** El login **nunca** devuelve `403 PASSWORD_CHANGE_REQUIRED`. El bloqueo ocurre en llamadas posteriores a APIs ERP.

---

## 2. GET /auth/me

### 2.1 Endpoint

```
GET /api/v1/auth/me/
```

### 2.2 Request

| Aspecto | Valor |
|---------|-------|
| Authorization | `Bearer <access_token>` |
| Whitelist | Sí — accesible aunque `requires_password_change=true` |

### 2.3 Response schema (`MeResponse`)

Extiende `UserDataWithRoles` + campos de sesión:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| *(hereda UserDataWithRoles)* | — | Incluye **`requires_password_change`** |
| `requiere_seleccion_empresa` | boolean | Multi-empresa pendiente |
| `empresas_disponibles` | array \| null | Lista `EmpresaDisponible` |
| `is_impersonation` | boolean | Sesión de soporte |
| `impersonated_by` | string \| null | UUID operador |
| `impersonated_by_username` | string \| null | Username operador |

### 2.4 Ejemplo JSON real

```json
{
  "usuario_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "nombre_usuario": "admin",
  "correo": "admin@tenant-demo.test",
  "nombre": "Administrador",
  "apellido": "Tenant Demo S A",
  "es_activo": true,
  "roles": ["Administrador"],
  "access_level": 4,
  "is_super_admin": false,
  "user_type": "tenant_admin",
  "cliente_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "es_admin_cliente": true,
  "empresa_activa": null,
  "requires_password_change": true,
  "requiere_seleccion_empresa": false,
  "empresas_disponibles": null,
  "is_impersonation": false,
  "impersonated_by": null,
  "impersonated_by_username": null
}
```

### 2.5 Uso recomendado en Frontend

- Llamar `/me` al **iniciar app** con sesión existente para sincronizar `requires_password_change`.
- Llamar tras **refresh** si el FE no decodifica JWT (ver sección 4).
- No usar `/me` como único gate de ERP si ya se conoce el flag del login; es complementario.

---

## 3. POST /auth/password/change

### 3.1 Endpoint

```
POST /api/v1/auth/password/change/
```

### 3.2 Request schema (`PasswordChangeRequest`)

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `current_password` | string | Sí | Contraseña actual (mín. 1 carácter) |
| `new_password` | string | Sí | Nueva contraseña (ver reglas abajo) |
| `refresh_token` | string \| null | No | **Solo mobile.** En web va en cookie HttpOnly |

**Reglas `new_password`:**

- Mínimo 8 caracteres
- Al menos una letra mayúscula
- Al menos una letra minúscula
- Al menos un número

**Headers:**

| Header | Valor |
|--------|-------|
| `Authorization` | `Bearer <access_token>` |
| `Content-Type` | `application/json` |
| `X-Client-Type` | `web` o `mobile` |

**Ejemplo request (web):**

```json
{
  "current_password": "TempPass123!",
  "new_password": "NuevaSegura2026!"
}
```

**Ejemplo request (mobile):**

```json
{
  "current_password": "TempPass123!",
  "new_password": "NuevaSegura2026!",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 3.3 Response schema (éxito)

`response_model`: `Token` (igual que login exitoso)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `access_token` | string | Nuevo JWT (`requires_password_change: false`) |
| `token_type` | string | `"bearer"` |
| `user_data` | object | Perfil actualizado con `requires_password_change: false` |
| `refresh_token` | string \| omitido | Solo en JSON si `X-Client-Type: mobile` |

### 3.4 Ejemplo éxito (web)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_data": {
    "usuario_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "nombre_usuario": "admin",
    "correo": "admin@tenant-demo.test",
    "nombre": "Administrador",
    "apellido": "Tenant Demo S A",
    "es_activo": true,
    "roles": ["Administrador"],
    "access_level": 4,
    "is_super_admin": false,
    "user_type": "tenant_admin",
    "cliente_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "es_admin_cliente": true,
    "empresa_activa": null,
    "requires_password_change": false
  }
}
```

**Efectos colaterales (transparentes para FE):**

- `requiere_cambio_contrasena = 0` en BD
- `fecha_ultimo_cambio_contrasena` actualizada
- Todos los refresh tokens anteriores revocados
- Access token anterior blacklisteado (`jti`)
- Nueva cookie refresh en web

### 3.5 Ejemplo error — contraseña actual incorrecta

**HTTP 401**

```json
{
  "detail": "La contraseña actual no es correcta"
}
```

> Este error usa el formato estándar FastAPI (`HTTPException`). **No incluye `error_code`.**

### 3.6 Ejemplo error — validación de nueva contraseña

**HTTP 422**

```json
{
  "detail": "body.new_password: La contraseña no cumple con los requisitos de seguridad. Debe contener: al menos una letra mayúscula, al menos un número.",
  "error_code": "VALIDATION_ERROR"
}
```

### 3.7 Otros errores relevantes

| HTTP | detail | error_code | Cuándo |
|------|--------|------------|--------|
| 400 | `"La nueva contraseña debe ser diferente a la actual"` | — | Misma contraseña |
| 400 | `"El cambio de contraseña no está disponible para usuarios SSO externos"` | — | `proveedor_autenticacion != local` |
| 401 | `"No se pudieron validar las credenciales"` | — | Token inválido/ausente |
| 500 | `"Error al cambiar la contraseña"` | — | Error interno |

---

## 4. Refresh

### 4.1 Endpoint

```
POST /api/v1/auth/refresh/
```

### 4.2 Request

| Cliente | Refresh token |
|---------|---------------|
| **Web** (`X-Client-Type: web`) | Cookie HttpOnly `refresh_token` |
| **Mobile** (`X-Client-Type: mobile`) | JSON body `{ "refresh_token": "..." }` |

### 4.3 Response actual

`response_model`: `Token`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_data": null
}
```

| Campo | Valor tras refresh |
|-------|------------------|
| `access_token` | Nuevo JWT |
| `user_data` | **`null`** (sin cambio de contrato) |
| `refresh_token` | Solo mobile en JSON; web en cookie |

### 4.4 Cómo se actualiza `requires_password_change`

1. El backend **re-lee BD** (`usuario.requiere_cambio_contrasena`) al validar refresh.
2. **No copia** el claim del refresh token anterior.
3. El nuevo `access_token` incluye claim `requires_password_change` actualizado.
4. El nuevo `refresh_token` también lleva el claim actualizado.

### 4.5 ¿Debe el Frontend llamar `/auth/me` tras refresh?

| Escenario | Recomendación |
|-----------|---------------|
| FE decodifica JWT access | Leer `requires_password_change` del nuevo access token → **no obligatorio** llamar `/me` |
| FE no decodifica JWT | **Sí**, llamar `GET /auth/me` tras refresh para sincronizar flag |
| Tras `password/change` exitoso | Usar `user_data` del response → **no obligatorio** `/me` |
| App idle + refresh automático | Si flag puede haber cambiado en BD, `/me` o decode JWT |

**Resumen:** `/me` no es obligatorio si el FE lee el claim del nuevo `access_token` o el `user_data` de login/change. Es la vía de respaldo recomendada.

---

## 5. Error `PASSWORD_CHANGE_REQUIRED`

Emitido cuando un usuario con `requires_password_change=true` llama cualquier endpoint que pasa por `get_current_active_user`, **excepto** rutas en whitelist auth.

### 5.1 Contrato exacto

| Campo | Valor |
|-------|-------|
| **HTTP status** | `403` |
| **error_code** | `"PASSWORD_CHANGE_REQUIRED"` |
| **detail** | `"Debe cambiar su contraseña antes de acceder a este recurso."` |

### 5.2 Estructura JSON completa

```json
{
  "detail": "Debe cambiar su contraseña antes de acceder a este recurso.",
  "error_code": "PASSWORD_CHANGE_REQUIRED"
}
```

### 5.3 Ejemplo real — bloqueo en menú ERP

```http
GET /api/v1/auth/menu HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**

```http
HTTP/1.1 403 Forbidden
Content-Type: application/json
```

```json
{
  "detail": "Debe cambiar su contraseña antes de acceder a este recurso.",
  "error_code": "PASSWORD_CHANGE_REQUIRED"
}
```

### 5.4 Detección en Frontend

```typescript
// Pseudocódigo — no implementar aquí
if (response.status === 403 && body.error_code === 'PASSWORD_CHANGE_REQUIRED') {
  redirectToForcePasswordChange();
}
```

**Nota:** El backend serializa `internal_code` como **`error_code`** en JSON (convención global `CustomException`). No buscar campo `internal_code` en la respuesta HTTP.

### 5.5 Rutas que NO devuelven este error (whitelist)

Accesibles con `requires_password_change=true`:

| Método | Ruta |
|--------|------|
| POST | `/api/v1/auth/password/change/` |
| GET | `/api/v1/auth/me/` |
| POST | `/api/v1/auth/logout/` |
| POST | `/api/v1/auth/refresh/` |
| POST | `/api/v1/auth/empresa/seleccionar/` |
| POST | `/api/v1/auth/impersonate/*` |
| POST | `/api/v1/auth/impersonate/end/` |

**Bloqueadas** (ejemplos): `/auth/menu`, `/auth/permissions/me`, `/auth/empresa/cambiar/`, cualquier módulo ERP (`/inv/`, `/fin/`, etc.).

---

## 6. Casos de uso oficiales

### 6.1 Tenant recién creado

| Paso | Actor | Backend | Frontend |
|------|-------|---------|----------|
| 1 | Superadmin crea tenant | `POST /clientes/` → `credenciales_iniciales` con contraseña temporal | Guardar/mostrar credenciales una sola vez |
| 2 | — | BD: `requiere_cambio_contrasena=1` para `admin` | — |
| 3 | Admin abre URL tenant | — | Pantalla login |

### 6.2 Primer login admin

| Paso | Request | Response clave |
|------|---------|----------------|
| 1 | `POST /auth/login/` | `user_data.requires_password_change: true` |
| 2 | — | FE: pantalla cambio contraseña (no ERP) |
| 3 | Intento `GET /auth/menu` | `403 PASSWORD_CHANGE_REQUIRED` |

### 6.3 Cambio obligatorio

| Paso | Request | Resultado |
|------|---------|-----------|
| 1 | `POST /auth/password/change/` con contraseña temporal + nueva | `200 Token`, `requires_password_change: false` |
| 2 | Tokens reemplazados en memoria/cookie | Sesión limpia |
| 3 | `GET /auth/menu` | `200` (si permisos OK) |

**Orden vs multi-empresa:** Tanto `password/change` como `empresa/seleccionar` están en whitelist. El FE puede:

- **Opción A (recomendada):** Cambio contraseña → selección empresa → ERP
- **Opción B:** Selección empresa → cambio contraseña → ERP

En ambos casos el flag permanece `true` hasta completar `password/change`.

### 6.4 Acceso normal ERP

| Condición | Comportamiento |
|-----------|----------------|
| `requires_password_change: false` | Flujo ERP estándar sin interceptores |
| Cualquier API ERP | Sin `403 PASSWORD_CHANGE_REQUIRED` |

### 6.5 Refresh token

| Escenario | Comportamiento |
|-----------|----------------|
| Flag activo en BD | Nuevo access con `requires_password_change: true` |
| Tras change password | Refresh anterior revocado; usar tokens del response change |
| `user_data` en refresh | Siempre `null` — usar JWT o `/me` |

### 6.6 Logout

| Aspecto | Comportamiento |
|---------|----------------|
| `POST /auth/logout/` | Siempre `200` idempotente |
| Enforcement | No aplica (sin `get_current_active_user`) |
| FE con pantalla cambio password | Logout disponible para abandonar sesión |

### 6.7 Impersonación

| Aspecto | Comportamiento |
|---------|----------------|
| Operador plataforma impersona tenant | **Excluido** del enforcement (`is_impersonation=true`) |
| Admin tenant con flag pendiente | Operador **no** ve `PASSWORD_CHANGE_REQUIRED` |
| Rutas `/impersonate/*` | Whitelist para operador |

### 6.8 Superadmin plataforma

| Aspecto | Comportamiento |
|---------|----------------|
| Login `SUPERADMIN_USERNAME` | Excluido (`platform_admin`, `es_superadmin`) |
| Bootstrap plataforma | Sin force password change |
| Panel superadmin | Sin interceptores de esta funcionalidad |

---

## 7. OpenAPI

### 7.1 Schemas modificados (aditivos)

| Schema | Campo nuevo | Default |
|--------|-------------|---------|
| `UserDataWithRoles` | `requires_password_change: boolean` | `false` |
| `MeResponse` | hereda `requires_password_change` | `false` |
| `Token.user_data` | incluye campo vía `UserDataWithRoles` | — |
| `LoginEmpresaSelectionResponse.user_data` | incluye campo vía `UserDataWithRoles` | — |

### 7.2 Schemas nuevos

| Schema | Uso |
|--------|-----|
| `PasswordChangeRequest` | Body `POST /auth/password/change/` |

### 7.3 Endpoint nuevo

| Método | Ruta | Request | Response |
|--------|------|---------|----------|
| `POST` | `/api/v1/auth/password/change/` | `PasswordChangeRequest` | `Token` |

### 7.4 Sin cambios estructurales

- `Union[Token, LoginEmpresaSelectionResponse]` en login — intacto
- Login sigue siendo `application/x-www-form-urlencoded`
- Refresh response shape — intacto (`user_data: null`)

---

## 8. Compatibilidad

### 8.1 Web

| Tema | Compatible | Notas |
|------|------------|-------|
| Login | ✅ | `user_data.requires_password_change`; refresh en cookie |
| Change password | ✅ | Sin `refresh_token` en body; cookie enviada automáticamente |
| Refresh | ✅ | Cookie `refresh_token` |
| Interceptor 403 | ✅ | Global en cliente HTTP |
| Pantalla dedicada | ✅ | Bloquear router ERP si flag true |

### 8.2 Mobile

| Tema | Compatible | Notas |
|------|------------|-------|
| Login | ✅ | `refresh_token` en JSON |
| Change password | ✅ | Incluir `refresh_token` en body |
| Refresh | ✅ | Body `{ refresh_token }` |
| Flag tras refresh | ✅ | Decodificar access o llamar `/me` |

### 8.3 SSO

| Tema | Compatible | Notas |
|------|------------|-------|
| Azure AD / Google | ✅ | Usuarios SSO **excluidos** del enforcement |
| `requires_password_change` | N/A | No aplica a `proveedor_autenticacion != local` |
| `POST /password/change/` | ❌ | `400` si usuario SSO intenta cambiar |

### 8.4 Impersonación

| Tema | Compatible | Notas |
|------|------------|-------|
| Soporte en tenant con admin pendiente | ✅ | Sin bloqueo ERP para operador |
| `is_impersonation` en `/me` | ✅ | FE soporte: ignorar flag tenant |
| Pantalla cambio password | N/A | No mostrar al operador impersonando |

### 8.5 Multiempresa

| Tema | Compatible | Notas |
|------|------------|-------|
| `LoginEmpresaSelectionResponse` | ✅ | `user_data.requires_password_change` presente |
| `POST /empresa/seleccionar/` | ✅ | Whitelist — permitido con flag true |
| `POST /empresa/cambiar/` | ❌ bloqueado | `403 PASSWORD_CHANGE_REQUIRED` si flag true |
| Tras selección empresa | ✅ | Nuevos tokens conservan flag hasta change password |

### 8.6 Retrocompatibilidad clientes antiguos

| Aspecto | Impacto |
|---------|---------|
| Campo nuevo opcional con default `false` | Clientes que ignoran el campo siguen parseando OK |
| Nuevo 403 en ERP | **Breaking behavior** solo si admin onboarding entra al ERP sin cambiar password — debe manejarse en FE |

---

## 9. Checklist Frontend

### 9.1 Modelos / tipos

- [ ] Añadir `requires_password_change: boolean` a tipo `UserData` / `UserDataWithRoles`
- [ ] Añadir `requires_password_change` a tipo `MeResponse`
- [ ] Crear tipo `PasswordChangeRequest` (`current_password`, `new_password`, `refresh_token?`)
- [ ] Crear constante `ERROR_CODE_PASSWORD_CHANGE_REQUIRED = 'PASSWORD_CHANGE_REQUIRED'`

### 9.2 Login

- [ ] Tras login exitoso, leer `response.user_data.requires_password_change`
- [ ] Si `true` → navegar a ruta `/force-password-change` (o equivalente)
- [ ] No llamar APIs ERP (menu, permissions, módulos) antes del cambio
- [ ] Manejar variante `LoginEmpresaSelectionResponse` (flag también en `user_data`)

### 9.3 Pantalla cambio contraseña obligatorio

- [ ] Formulario: contraseña actual + nueva + confirmación (confirmación solo FE)
- [ ] Validación local alineada con backend (8 chars, mayúscula, minúscula, número)
- [ ] `POST /api/v1/auth/password/change/` con Bearer access token
- [ ] Web: no enviar `refresh_token` en body (cookie automática)
- [ ] Mobile: incluir `refresh_token` en body
- [ ] Tras 200: reemplazar `access_token` (y `refresh_token` en mobile)
- [ ] Actualizar estado global `requires_password_change = false`
- [ ] Redirigir a selección empresa si `requiere_seleccion_empresa` o al dashboard ERP

### 9.4 Interceptor HTTP global

- [ ] Si `status === 403` y `error_code === 'PASSWORD_CHANGE_REQUIRED'` → redirect pantalla cambio
- [ ] Evitar bucles: no interceptar rutas whitelist (`/auth/me`, `/auth/password/change`, `/auth/logout`, `/auth/refresh`, `/auth/empresa/seleccionar`)
- [ ] Diferenciar de otros 403 (`PERMISSION_DENIED`, etc.)

### 9.5 Bootstrap / sesión existente

- [ ] Al cargar app con token guardado: `GET /auth/me` y leer `requires_password_change`
- [ ] Si `true` → pantalla cambio antes de renderizar layout ERP

### 9.6 Refresh

- [ ] Tras refresh exitoso: actualizar flag desde JWT decode **o** llamar `/me`
- [ ] No asumir `user_data` en response refresh (es `null`)

### 9.7 Multiempresa

- [ ] Permitir `POST /empresa/seleccionar/` con flag true
- [ ] No exponer selector cambio empresa (`/empresa/cambiar/`) hasta flag false
- [ ] Definir orden UX: cambio password vs selección empresa (recomendado: password primero)

### 9.8 Impersonación y superadmin

- [ ] No mostrar pantalla force password si `is_impersonation === true` en `/me`
- [ ] No aplicar interceptor a flujos de operador `platform_admin`

### 9.9 SSO

- [ ] No mostrar cambio contraseña local a usuarios SSO
- [ ] Ocultar ruta si `proveedor_autenticacion !== 'local'` (dato disponible en perfil usuario si se carga)

### 9.10 Errores UX

- [ ] 401 en change → mensaje "Contraseña actual incorrecta"
- [ ] 422 → mostrar `detail` (validación fortaleza)
- [ ] 400 misma contraseña / SSO → mensajes específicos

### 9.11 Logout

- [ ] Mantener botón "Cerrar sesión" visible en pantalla cambio obligatorio

---

## 10. Diagrama de flujo (referencia UX)

```text
[Login OK]
    │
    ├─ requires_password_change = true
    │       │
    │       ├─ [Pantalla cambio password] ──POST /password/change/──► tokens nuevos
    │       │                                      │
    │       │                                      ├─ requiere_seleccion_empresa?
    │       │                                      │     └─ POST /empresa/seleccionar/
    │       │                                      └─ [ERP normal]
    │       │
    │       └─ (cualquier API ERP sin cambio) ──► 403 PASSWORD_CHANGE_REQUIRED
    │
    └─ requires_password_change = false
            └─ [Flujo normal ERP]
```

---

## 11. Referencias de implementación Backend

| Artefacto | Ruta |
|-----------|------|
| Enforcement | `app/core/auth/password_change_enforcement.py` |
| Schemas | `app/modules/auth/presentation/schemas.py` |
| Endpoints | `app/modules/auth/presentation/endpoints.py` |
| Servicio cambio | `app/modules/auth/application/services/password_change_service.py` |

---

**Fin del contrato.** Documento listo para consumo del equipo Frontend sin cambios adicionales de Backend.
