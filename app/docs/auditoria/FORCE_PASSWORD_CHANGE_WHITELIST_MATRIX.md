# Matriz final — Whitelist efectiva FORCE PASSWORD CHANGE (O5)

**Fecha:** 2026-06-08  
**Estrategia:** Enforcement en `get_current_active_user` + whitelist por `request.method` + `request.url.path`  
**Módulo:** `app/core/auth/password_change_enforcement.py`

---

## 1. Rutas explícitamente permitidas (sin bloqueo 403)

| # | Método | Path efectivo | Router | Dependencia auth | Motivo |
|---|--------|---------------|--------|------------------|--------|
| W1 | `POST` | `/api/v1/auth/password/change/` | `endpoints.py` | `get_current_active_user` (whitelist) | Ejecuta el cambio de contraseña |
| W2 | `GET` | `/api/v1/auth/me/` | `endpoints.py` | `get_current_active_user` (whitelist) | Frontend lee estado del flag |
| W3 | `POST` | `/api/v1/auth/logout/` | `endpoints.py` | **Ninguna** (público con refresh) | Cerrar sesión |
| W4 | `POST` | `/api/v1/auth/logout` | `endpoints.py` | **Ninguna** | Alias sin trailing slash |
| W5 | `POST` | `/api/v1/auth/refresh/` | `endpoints.py` | `get_current_user_from_refresh` | Rotar tokens; re-lee BD |
| W6 | `POST` | `/api/v1/auth/empresa/seleccionar/` | `endpoints.py` | `require_selection_token_payload` | Completar multi-empresa |
| W7 | `POST` | `/api/v1/auth/impersonate/{cliente_id}/` | `endpoints.py` | `require_super_admin` + `get_current_user_data` | Iniciar impersonación |
| W8 | `POST` | `/api/v1/auth/impersonate/end/` | `endpoints.py` | `get_current_user_data` | Finalizar impersonación |

**Regla W7:** Cualquier `POST` cuyo path normalizado empiece con `/api/v1/auth/impersonate/` (incluye UUID en path).

---

## 2. Rutas auth sin JWT / fuera de `get_current_active_user`

| Ruta | ¿Pasa enforcement? | Comportamiento |
|------|-------------------|----------------|
| `POST /api/v1/auth/login/` | **No** | Login exitoso emite JWT con `requires_password_change=true` |
| `POST /api/v1/auth/refresh/` | **No** | Usa `get_current_user_from_refresh`; re-lee BD |
| `POST /api/v1/auth/logout/` | **No** | Sin `get_current_active_user` |
| `POST /api/v1/auth/sso/*` | **No** | Routers SSO separados; usuarios externos excluidos por proveedor |

---

## 3. Rutas auth bloqueadas si `requiere_cambio_contrasena=1`

Todas usan `get_current_active_user` (directa o vía `require_permission` / `require_erp_session`):

| Ruta | Ejemplo | Notas |
|------|---------|-------|
| `POST /api/v1/auth/empresa/cambiar/` | Cambio empresa | Añadido `Depends(get_current_active_user)` |
| `GET /api/v1/auth/permissions/me` | Permisos | vía `require_erp_session` |
| `GET /api/v1/auth/menu` | Menú ERP | vía `require_erp_session` |
| `GET /api/v1/auth/sessions/` | Sesiones activas | `get_current_active_user` |
| Resto módulos ERP (~733 endpoints) | FIN, PUR, INV, … | `get_current_active_user` + RBAC |

---

## 4. Exclusiones (nunca bloquear aunque flag=1)

| Condición | Fuente | Aplica a |
|-----------|--------|----------|
| `is_impersonation=true` | JWT payload | Operador soporte plataforma |
| `user_type=platform_admin` | JWT / usuario | Bootstrap plataforma |
| `es_superadmin=true` | JWT | Superadmin plataforma |
| `is_super_admin=true` + operador plataforma | JWT / usuario | Sesiones SYSTEM |
| `proveedor_autenticacion != 'local'` | BD (`usuario`) | SSO Azure/Google/LDAP |
| Username reservado `SUPERADMIN_USERNAME` | settings | Bootstrap plataforma |

---

## 5. Normalización de path (matching)

```text
request.url.path
  → strip
  → colapsar // 
  → sin query string
  → comparar exacto O prefijo impersonate
```

Variantes cubiertas:

| Entrada | Normalizado | Match |
|---------|-------------|-------|
| `/api/v1/auth/me/` | `/api/v1/auth/me/` | W2 |
| `/api/v1/auth/me` | `/api/v1/auth/me` | W2 (exacto en set) |
| `/api/v1/auth/impersonate/550e8400-…/` | prefijo impersonate | W7 |
| `/api/v1/auth/impersonate/end/` | prefijo impersonate | W8 |

---

## 6. Respuesta de bloqueo

| Campo | Valor |
|-------|-------|
| HTTP | `403` |
| `detail` | Mensaje en español (cambio obligatorio) |
| `error_code` | `PASSWORD_CHANGE_REQUIRED` |

> El handler global de `CustomException` serializa `internal_code` como `error_code` en JSON (convención existente del backend).

---

## 7. Cobertura verificada

| Capa | Endpoints | Enforcement |
|------|-----------|-------------|
| `get_current_active_user` | ~733 | ✅ Principal |
| `require_erp_session` | INV + menu + permissions | ✅ (comparte dep) |
| `require_org_*` | ORG sub-routers | ✅ (comparte dep) |
| Solo `get_current_user_data` | `empresa/cambiar` | ✅ (dep añadida) |
| Sin JWT | login, refresh, logout | ✅ Excluidos por diseño |
