# Reporte de implementación — FORCE PASSWORD CHANGE

**Fecha:** 2026-06-08  
**Estrategia:** O5 (enforcement centralizado + whitelist auth)  
**Relacionado:**
- [`FORCE_PASSWORD_CHANGE_AUDIT.md`](FORCE_PASSWORD_CHANGE_AUDIT.md)
- [`FORCE_PASSWORD_CHANGE_IMPACT_MATRIX.md`](FORCE_PASSWORD_CHANGE_IMPACT_MATRIX.md)
- [`FORCE_PASSWORD_CHANGE_WHITELIST_MATRIX.md`](FORCE_PASSWORD_CHANGE_WHITELIST_MATRIX.md)

---

## 1. Resumen ejecutivo

Implementación completada sin modificar `ClienteOnboardingService`, `bootstrap_platform`, onboarding plataforma ni `TenantMiddleware`.

| Componente | Estado |
|------------|--------|
| Enforcement O5 en `get_current_active_user` | ✅ |
| Whitelist auth explícita | ✅ |
| Claim JWT `requires_password_change` | ✅ |
| Login no bloqueado | ✅ |
| Refresh re-lee BD | ✅ |
| `POST /api/v1/auth/password/change/` | ✅ |
| Error 403 `PASSWORD_CHANGE_REQUIRED` | ✅ |
| OpenAPI aditivo | ✅ |

---

## 2. Archivos modificados / creados

### Nuevos

| Archivo | Rol |
|---------|-----|
| `app/core/auth/password_change_enforcement.py` | Whitelist, exclusiones, enforcement 403 |
| `app/modules/auth/application/services/password_change_service.py` | Orquestación cambio contraseña |
| `app/docs/auditoria/FORCE_PASSWORD_CHANGE_WHITELIST_MATRIX.md` | Matriz whitelist pre-código |
| `tests/unit/test_force_password_change.py` | 18 tests unitarios |

### Modificados

| Archivo | Cambio |
|---------|--------|
| `app/api/deps.py` | Llama `enforce_password_change_policy` en `get_current_active_user` |
| `app/modules/auth/application/services/auth_service.py` | SELECT flag BD, helpers, tokens en sesión empresa |
| `app/modules/auth/presentation/schemas.py` | `requires_password_change`, `PasswordChangeRequest` |
| `app/modules/auth/presentation/endpoints.py` | Login, refresh, `/me`, `password/change`, `empresa/cambiar` |

### No modificados (confirmado)

- `cliente_onboarding_service.py`
- `platform_identity_bootstrap_service.py` / `bootstrap_platform.py`
- `TenantMiddleware`

---

## 3. Contrato técnico

### 3.1 JWT

Nuevo claim opcional en access y refresh:

```json
"requires_password_change": true
```

### 3.2 DTOs (aditivos)

- `UserDataWithRoles.requires_password_change: bool = false`
- `MeResponse` hereda el campo
- `Token.user_data` incluye el flag tras login / change password

### 3.3 Error de bloqueo ERP

```json
HTTP 403
{
  "detail": "Debe cambiar su contraseña antes de acceder a este recurso.",
  "error_code": "PASSWORD_CHANGE_REQUIRED"
}
```

> El handler global de `CustomException` serializa `internal_code` como `error_code` (convención existente).

### 3.4 Endpoint nuevo

`POST /api/v1/auth/password/change/`

**Request:**
```json
{
  "current_password": "...",
  "new_password": "...",
  "refresh_token": "..." 
}
```
(`refresh_token` solo móvil)

**Efectos:**
1. Valida contraseña actual (bcrypt)
2. `requiere_cambio_contrasena = 0`
3. `fecha_ultimo_cambio_contrasena = GETDATE()`
4. Revoca todos los refresh del usuario
5. Blacklist access token actual (`jti`)
6. Emite nuevos access + refresh con `requires_password_change=false`

---

## 4. Flujos críticos — comportamiento

| Flujo | Comportamiento post-implementación |
|-------|-----------------------------------|
| **Login web** | 200 + JWT + `user_data.requires_password_change`; refresh en cookie |
| **Login mobile** | 200 + access + refresh JSON + flag en `user_data` |
| **Refresh** | Re-lee `requiere_cambio_contrasena` de BD (`_fetch_user_row_for_refresh`); **no** copia claim anterior |
| **Logout** | Sin cambio; siempre 200 idempotente |
| **GET /me** | Whitelist; expone `requires_password_change` desde BD |
| **Selección empresa** | Whitelist; propaga flag en nuevos tokens vía `emitir_sesion_completa_con_empresa` |
| **Cambio empresa** | Bloqueado si flag activo (`get_current_active_user` añadido como dep) |
| **Impersonación** | Excluida (`is_impersonation`); rutas `/impersonate/*` en whitelist |
| **Onboarding tenant** | Sin cambio en servicio; primer login del `admin` recibe flag=true |
| **Onboarding plataforma** | Excluido (`platform_admin` / `es_superadmin`) |
| **ERP (INV, FIN, …)** | 403 `PASSWORD_CHANGE_REQUIRED` vía `get_current_active_user` |

---

## 5. Pruebas — evidencia

### 5.1 Unitarias nuevas

```text
tests/unit/test_force_password_change.py — 18 passed
```

Cobertura:
- Whitelist (10 rutas)
- Exclusiones impersonación / platform / SSO
- Enforcement 403 en ruta ERP
- Whitelist `/me` permitido
- `resolve_requires_password_change` (BIT/bool)
- Refresh token_data desde BD (no claim legacy)
- Schema `UserDataWithRoles`
- Validación fortaleza `PasswordChangeRequest`

### 5.2 Regresión auth relacionada

```text
tests/unit/test_impersonation_auth.py      — 19 passed
tests/unit/test_login_user_data_serialization.py — 5 passed
tests/unit/test_empresa_sesion_auth.py     — 19 passed
```

**Total verificado en esta entrega:** 61 tests passed.

### 5.3 Integración E2E

No ejecutada en este entorno (requiere BD + tenant activo). Checklist manual para QA:

- [ ] Login admin onboarding → `requires_password_change=true`
- [ ] `GET /inv/...` → 403 `PASSWORD_CHANGE_REQUIRED`
- [ ] `GET /auth/me` → 200 con flag true
- [ ] `POST /auth/password/change/` → 200 + tokens sin flag
- [ ] ERP accesible tras cambio
- [ ] Impersonación en tenant con admin pendiente → sin bloqueo
- [ ] Refresh tras cambio manual en BD → refleja flag actualizado

---

## 6. OpenAPI — compatibilidad

| Cambio | ¿Rompe contrato? |
|--------|------------------|
| Campo opcional `requires_password_change` en responses | No (aditivo) |
| Nuevo endpoint `POST /password/change/` | No (aditivo) |
| 403 nuevo en rutas ERP | Cambio de **comportamiento**, no de schema |
| Login / refresh response models | Sin cambio estructural (`Union` intacto) |

---

## 7. Coordinación Frontend (pendiente)

El backend está listo. El FE debe:

1. Leer `user_data.requires_password_change` tras login (web y mobile)
2. Tras 403, leer `error_code === "PASSWORD_CHANGE_REQUIRED"`
3. Redirigir a pantalla de cambio → `POST /auth/password/change/`
4. Tras éxito, usar nuevos tokens y continuar flujo ERP (empresa selection si aplica)

---

## 8. Comandos de reproducción

```powershell
Set-Location d:\base_multi_tenant_fastapi
.\venv\Scripts\python.exe -m pytest tests/unit/test_force_password_change.py -q
.\venv\Scripts\python.exe -m pytest tests/unit/test_impersonation_auth.py tests/unit/test_login_user_data_serialization.py tests/unit/test_empresa_sesion_auth.py -q
```
