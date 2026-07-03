# F13-N4 — Trazabilidad RBAC del 403 en `POST /auth/impersonate/end/`

**Fecha:** 2026-06-29  
**Alcance:** `POST /api/v1/auth/impersonate/end/` — solo pipeline de autorización  
**Modo:** Investigación puntual — **sin implementación, commits ni cambios de código**  
**Evidencia runtime:** JWT con `is_impersonation=true`, `user_type=tenant_admin`, `is_super_admin=false`, `access_level=4`, `effective_scope=tenant`; respuesta 403 con `"Se requieren privilegios de Super Administrador para acceder a este recurso"`; log `"Intento de acceso no autorizado a endpoint Super Admin por: superadmin"`.

---

## Respuestas al entregable

### 1. ¿Quién genera exactamente el 403?

La dependencia **`require_super_admin()`** del handler **`iniciar_impersonacion`** (no del handler `finalizar_impersonacion`).

Cadena concreta:

1. `require_super_admin()` → función interna `dependency` (`rbac.py`)
2. Evalúa claims del JWT de impersonación vía `get_current_active_user` (upstream)
3. Determina que el usuario **no** es Super Admin (`user_type=tenant_admin`, `is_super_admin=false`, `access_level=4`)
4. Registra el warning vía `_rbac_log_denied`
5. Lanza `AuthorizationError` (subclase local de `HTTPException` en `rbac.py`) → **HTTP 403**

El servicio `ImpersonationService.finalizar_impersonacion` **no se ejecuta**; el handler `finalizar_impersonacion` **no se alcanza**.

---

### 2. ¿En qué archivo y línea?

| Elemento | Ubicación |
|----------|-----------|
| Mensaje HTTP `"Se requieren privilegios de Super Administrador para acceder a este recurso"` | `app/core/authorization/rbac.py` **L345** |
| Log `"Intento de acceso no autorizado a endpoint Super Admin por: %s"` | `app/core/authorization/rbac.py` **L340–343** (`_rbac_log_denied`) |
| Función que lanza la excepción | `require_super_admin()` → closure `dependency`, `rbac.py` **L291–347** |
| Handler que declara esa dependencia | `iniciar_impersonacion`, `app/modules/auth/presentation/endpoints.py` **L743–746** |

---

### 3. ¿Por qué `/impersonate/end` entra a esa validación?

**Colisión de rutas en Starlette/FastAPI por orden de registro.**

En `endpoints.py` las rutas están registradas en este orden:

1. `POST /impersonate/{cliente_id}/` → `iniciar_impersonacion` (**L727**) — incluye `Depends(require_super_admin())`
2. `POST /impersonate/end/` → `finalizar_impersonacion` (**L798**) — solo `Depends(get_current_user_data)`

Para la URL `POST /api/v1/auth/impersonate/end/`:

- El segmento `end` coincide con el path param `{cliente_id}` de la **primera** ruta.
- Starlette devuelve `Match.FULL` para **ambas** rutas, pero selecciona la **primera** registrada.
- La request se enruta a **`iniciar_impersonacion`**, no a **`finalizar_impersonacion`**.
- Se ejecuta `require_super_admin()` con el Bearer de impersonación (claims tenant, no platform).
- La validación UUID de `cliente_id="end"` **no impide** el 403: las dependencias de seguridad se resuelven y fallan **antes** de que la conversión `UUID` rechace el valor `"end"`.

**Verificación reproducible (ASGI, sin modificar código):**

```
POST /api/v1/auth/impersonate/end/
Authorization: Bearer <JWT is_impersonation=true, user_type=tenant_admin, sub=superadmin>

→ HTTP 403
→ {"detail":"Se requieren privilegios de Super Administrador para acceder a este recurso"}
→ Log: Intento de acceso no autorizado a endpoint Super Admin por: superadmin
```

**Matching en el router auth (orden de iteración):**

```
Match.FULL /impersonate/{cliente_id}/ -> iniciar_impersonacion   ← gana (primera)
Match.FULL /impersonate/end/         -> finalizar_impersonacion  ← nunca alcanzada
```

---

### 4. ¿Es comportamiento esperado o un defecto de implementación?

**Defecto de implementación** — no es el contrato funcional de `/impersonate/end/`.

El diseño documentado (p. ej. `FORCE_PASSWORD_CHANGE_WHITELIST_MATRIX.md`, F13-N1) distingue explícitamente:

| Ruta | RBAC esperado |
|------|---------------|
| `POST /impersonate/{cliente_id}/` | `require_super_admin()` — operador Platform |
| `POST /impersonate/end/` | Solo `get_current_user_data` — Bearer de impersonación |

El 403 observado es coherente con el RBAC de **inicio** de impersonación aplicado por error a una URL de **fin**, debido al orden de registro de rutas.

---

### 5. ¿Cuál es la causa raíz exacta?

**Registro de la ruta estática `/impersonate/end/` después de la ruta paramétrica `/impersonate/{cliente_id}/`.**

Starlette resuelve `POST …/impersonate/end/` contra la ruta paramétrica con `cliente_id="end"`, invoca `iniciar_impersonacion` y su dependencia `require_super_admin()`. El JWT de impersonación no cumple el criterio Super Admin (`rbac.py` L321–330), se emite `AuthorizationError` L344–347, y el cliente recibe 403 con el mensaje y log reportados.

**Nota sobre F13-N1:** la auditoría N1 concluyó que el handler `finalizar_impersonacion` no emite 403 (correcto en código estático), pero **asumió implícitamente** que la request llegaba a ese handler. F13-N4 demuestra que, en runtime, la request **no llega** a `finalizar_impersonacion`.

---

## Investigación paso a paso (orden solicitado)

### Paso 1 — Endpoint exacto

| Campo | Valor |
|-------|-------|
| **Ruta HTTP** | `POST /api/v1/auth/impersonate/end/` |
| **Handler diseñado para esta URL** | `finalizar_impersonacion` |
| **Archivo** | `app/modules/auth/presentation/endpoints.py` **L809–839** |
| **Router** | `router = APIRouter()` — mismo módulo, **L89** |
| **Montaje** | `app/api/v1/api.py` **L68–72** → `api_router.include_router(auth_endpoints.router, prefix="/auth", …)` |
| **Handler que recibe la request en runtime** | `iniciar_impersonacion` — **L743–795** (colisión de rutas) |

---

### Paso 2 — ¿Dependencias Super Admin en el handler `finalizar_impersonacion`?

**NO.**

```python
async def finalizar_impersonacion(
    request: Request,
    response: Response,
    payload: Dict = Depends(get_current_user_data),
):
```

No usa `@require_super_admin`, `Depends(require_super_admin())`, `get_current_active_super_admin`, ni equivalentes.

---

### Paso 3 — ¿Dependencias heredadas en el APIRouter padre?

**NO** hay dependencias globales en el router auth.

```python
router = APIRouter()  # endpoints.py L89 — sin dependencies=[...]
```

Montaje en `api.py` tampoco añade `dependencies=` al `include_router` de auth.

**Conclusión:** el 403 no proviene de una dependencia heredada del router; proviene de la dependencia del **handler equivocado** (`iniciar_impersonacion`).

---

### Paso 4 — Origen del mensaje exacto

| Campo | Valor |
|-------|-------|
| **Texto** | `"Se requieren privilegios de Super Administrador para acceder a este recurso"` |
| **Definición** | `app/core/authorization/rbac.py` **L345** |
| **Función** | `require_super_admin()` → `dependency()` interna, **L291–347** |
| **Invocación para esta URL** | FastAPI resuelve dependencias de `iniciar_impersonacion` porque esa ruta gana el matching |

Criterio de rechazo (`rbac.py` L321–330): el JWT de impersonación tiene `user_type=tenant_admin`, `is_super_admin=false`, `access_level=4` → `is_super = False`.

---

### Paso 5 — Búsqueda literal del texto

| Pregunta | Respuesta |
|----------|-----------|
| ¿Dónde está definido? | `app/core/authorization/rbac.py` **L345** (también variante acortada L653 en decorador `@super_admin_required`, no usado aquí) |
| ¿Qué función lo lanza? | Closure `dependency` dentro de `require_super_admin()` |
| ¿Quién la invoca para este endpoint? | Dependencia FastAPI de `iniciar_impersonacion` (`endpoints.py` **L746**: `current_user=Depends(require_super_admin())`), activada por colisión de rutas |

---

### Paso 6 — Call graph real

```
HTTP POST /api/v1/auth/impersonate/end/
    ↓
main.py — middleware (CORS, TenantMiddleware, ImpersonateAuthDiagMiddleware)
    ↓  [sin check Super Admin]
FastAPI / Starlette routing
    ↓  Primera ruta Match.FULL: /auth/impersonate/{cliente_id}/  (cliente_id="end")
    ↓  Handler seleccionado: iniciar_impersonacion  (NO finalizar_impersonacion)
Dependencia: require_super_admin()  [rbac.py L276]
    ↓
Dependencia upstream: get_current_active_user  [deps.py L171]
    ↓
Dependencia upstream: get_current_user_data  [deps.py L66]
    ↓  Decodifica JWT impersonación (sub=superadmin, user_type=tenant_admin, …)
    ↓  get_user_auth_context + build_user_with_roles + impersonation_rbac
Evaluación is_super  [rbac.py L321–330] → False
    ↓
_rbac_log_denied  [rbac.py L340–343]
    ↓
AuthorizationError(detail="Se requieren privilegios…")  [rbac.py L344–347]
    ↓
HTTP 403 Forbidden
```

**Call graph del handler diseñado (nunca alcanzado en el escenario reportado):**

```
POST /api/v1/auth/impersonate/end/
    ↓
finalizar_impersonacion  [endpoints.py L809]
    ↓
get_current_user_data only  [deps.py L66]
    ↓
ImpersonationService.finalizar_impersonacion  [impersonation_service.py L404]
    ↓
200 / 400 / 401 / 410 / 500  (sin 403 Super Admin en servicio)
```

---

## Tabla comparativa de handlers

| | `iniciar_impersonacion` (recibe la request hoy) | `finalizar_impersonacion` (contrato de `/end`) |
|--|--|--|
| Ruta | `/impersonate/{cliente_id}/` | `/impersonate/end/` |
| Orden registro | 1º | 2º |
| Super Admin RBAC | **Sí** — `Depends(require_super_admin())` | **No** |
| Auth mínima | `get_current_user_data` (2ª dependencia) | `get_current_user_data` |
| Emite 403 Super Admin | **Sí** | **No** |

---

## Reconciliación con síntoma runtime

| Evidencia | Interpretación |
|-----------|----------------|
| JWT: `is_impersonation=true`, `user_type=tenant_admin` | Token correcto para **fin** de impersonación |
| Log: `… endpoint Super Admin por: superadmin` | `sub` del JWT es el operador; el check es el de **inicio** |
| 403 + mensaje Super Admin | `require_super_admin()` en `iniciar_impersonacion` |
| `/me`, `/permissions/me`, `/menu` OK tras el fallo | Recuperación vía refresh cookie padre (F13-N1); independiente del 403 en `/end` |

---

**Fin del documento — F13-N4. Sin propuesta de corrección ni cambios de código.**
