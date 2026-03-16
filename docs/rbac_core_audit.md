## Auditoría RBAC CORE — Estado actual y validaciones

**Fecha:** 2026-02-18  
**Objetivo:** Validar que el sistema de autorización esté basado en RBAC (permisos) y que `core.app.acceder` sea la condición oficial de acceso al ERP, sin dependencias legacy de niveles (`access_level`).

---

## Alcance y metodología

Se revisó el backend buscando patrones en código:

- Uso de `access_level` / `nivel_acceso` / `accessLevel` en condiciones (`if`, `>=`, validadores).
- Dependencias de autorización:
  - `require_permission(...)`
  - `has_permission(...)`
  - LBAC legacy: `require_super_admin`, `require_access_level`, `RoleChecker`.
- Endpoints en `app/modules/**/presentation/` y `app/modules/auth/presentation/endpoints.py` (login y `/auth/me/`).

---

## Validaciones solicitadas (PASS/FAIL)

### 1) Ningún endpoint usa `access_level` para autorización

**Resultado: FAIL**

**Evidencia (autorización por niveles activa):**

- `app/api/deps.py` define `RoleChecker` que calcula nivel mínimo requerido y **bloquea por `access_level`**:

```216:260:app/api/deps.py
class RoleChecker:
    async def __call__(self,
        current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
    ):
        from app.modules.rbac.application.services.rol_service import RolService
        min_required_level = await RolService.get_min_required_access_level(...)
        if current_user.access_level < min_required_level:
            raise HTTPException(status_code=403, detail=...)
```

- `app/core/authorization/lbac.py` aplica autorización por nivel (LBAC) y también considera `access_level >= 5` como superadmin:

```41:116:app/core/authorization/lbac.py
def require_access_level(min_level: int):
    user_access_level = getattr(current_user, 'access_level', 1)
    if user_access_level < min_level:
        raise InsufficientAccessLevelError(...)

def require_super_admin():
    is_super_admin = getattr(current_user, 'is_super_admin', False)
    access_level = getattr(current_user, 'access_level', 0)
    if not (is_super_admin or access_level >= 5 or has_super_admin_role):
        raise SuperAdminRequiredError()
```

- Ejemplo adicional: `app/modules/modulos/presentation/endpoints_menus.py` calcula `as_tenant_admin = access_level >= 4` y cambia comportamiento.

**Riesgo:** Mientras exista LBAC activo, el comportamiento de autorización no depende solo de permisos RBAC; pueden existir rutas que permitan/denieguen por nivel, incluso si el catálogo de permisos indica otra cosa.

---

### 2) Todos los endpoints protegidos usan `require_permission()`

**Resultado: FAIL**

**Evidencia (protección sin `require_permission`):**

- Endpoints protegidos por decoradores LBAC (ej. SuperAdmin) en vez de permisos:
  - `app/modules/tenant/presentation/endpoints_clientes.py`:

```25:63:app/modules/tenant/presentation/endpoints_clientes.py
from app.core.authorization.lbac import require_super_admin
...
@require_super_admin()
async def crear_cliente(...):
    ...
```

Esto protege el endpoint, pero **no** mediante `require_permission(...)`.

**Evidencia (endpoints autenticados sin permiso explícito):**

- Ejemplo concreto detectado: `POST` sin `require_permission` en WMS zonas:

```63:70:app/modules/wms/presentation/endpoints_zonas.py
@router.post("", ...)
async def post_zona_almacen(
    data: ZonaAlmacenCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await create_zona_almacen(...)
```

**Riesgo:** La cobertura RBAC puede ser incompleta o inconsistente (algunas rutas quedan solo “autenticadas” o se protegen por LBAC en vez de permisos de negocio).

---

### 3) Superadmin bypass funciona solo vía `is_super_admin`

**Resultado: FAIL**

**Evidencia:**

- `has_permission` hace bypass por `get_user_type(user) == "super_admin"`; y `get_user_type` considera:
  - `is_super_admin=True`, **o**
  - presencia del rol `SuperAdministrador` en `user.roles`.

```74:123:app/core/authorization/rbac.py
if hasattr(user, 'is_super_admin') and user.is_super_admin:
    return "super_admin"
...
if SUPER_ADMIN_ROLE in nombres_roles:
    return "super_admin"
```

- En LBAC (`require_super_admin`) también hay bypass por `access_level >= 5` y por rol, además del flag.

**Riesgo:** Existen múltiples caminos para “ser superadmin” (flag, rol, nivel). Esto puede ser válido por diseño, pero **no cumple** el criterio “solo vía is_super_admin” y puede complicar el hardening del flujo de autorización.

---

### 4) Login valida acceso usando permisos y no niveles

**Resultado: FAIL (actualmente)**

**Evidencia:**

- En `POST /login/` se calcula `level_info = get_user_access_level_info(...)` y se inserta en el token.
- No se observa una validación tipo `has_permission(..., "core.app.acceder")` ni un bloqueo basado en permisos RBAC en el login.

```150:216:app/modules/auth/presentation/endpoints.py
user_base_data = await authenticate_user(...)
...
level_info = await get_user_access_level_info(user_id, target_cliente_id)
token_data = {"sub": ..., "cliente_id": ..., "level_info": level_info}
access_token = create_access_token(...)
```

**Nota:** Por requerimiento de Fase 3, la validación CORE se integró en **`GET /auth/me/`** (reconstrucción de sesión), no en login.

**Riesgo:** Un usuario puede autenticarse (token válido) pero ser bloqueado al reconstruir sesión (`/me/`) si no tiene `core.app.acceder`. Esto es coherente con el diseño “autenticación vs autorización base”, pero no cumple el criterio “login valida acceso por permisos”.

---

### 5) No existen checks legacy activos

**Resultado: FAIL**

**Evidencia (checks legacy activos):**

- Módulo LBAC completo activo: `app/core/authorization/lbac.py`.
- `RoleChecker` en `app/api/deps.py` valida por `access_level`.
- Endpoints con `@require_super_admin()` (tenant/superadmin/modulos), que operan por LBAC.

**Riesgo:** Mientras coexistian LBAC y RBAC, se mantiene superficie de inconsistencia: diferentes endpoints pueden estar gobernados por diferentes “fuentes de verdad” (niveles vs permisos).

---

## Estado de `core.app.acceder` en autenticación (Fase 3)

**Implementado en `GET /auth/me/`:**

- Si no tiene `core.app.acceder` → **403** con `detail="Usuario sin acceso al sistema"`.
- Si lo tiene → respuesta normal (sin cambios funcionales).

Esto convierte `core.app.acceder` en la condición oficial para “acceso global al ERP” al reconstruir sesión.

---

## Hallazgos clave y riesgos (resumen ejecutivo)

- **Hallazgo A — LBAC sigue activo:** hay autorizaciones basadas en `access_level` (`RoleChecker`, `require_access_level`, `require_super_admin`).
  - **Riesgo:** autorizaciones inconsistentes, difícil auditoría, decisiones no trazables solo por catálogo RBAC.

- **Hallazgo B — Cobertura RBAC no uniforme:** existen endpoints autenticados sin `require_permission` (ej. `POST` WMS zonas) y endpoints protegidos por LBAC.
  - **Riesgo:** rutas “abiertas” a usuarios autenticados o rutas que no aparecen en el catálogo de permisos.

- **Hallazgo C — Superadmin bypass múltiple:** bypass no solo por flag `is_super_admin` (también por rol y/o `access_level`).
  - **Riesgo:** complejidad adicional y posibilidad de configuraciones inesperadas que otorguen bypass.

- **Hallazgo D — Login no valida por permisos:** el control CORE está en `/me/`, no en login.
  - **Riesgo:** sesiones que “parecen válidas” tras login pero se rompen al refrescar si el frontend depende de `/me/` para reconstrucción.

---

## Recomendaciones (no aplicadas en esta auditoría)

1. **Plan de eliminación LBAC (gradual):**
   - Reemplazar `RoleChecker` y `require_access_level/require_super_admin` por `require_permission(...)` con permisos explícitos (ej. `core.cliente.crear`, `admin.*`, etc.) o por `core.app.acceder` + permisos específicos.

2. **Cerrar huecos de endpoints autenticados sin permiso:**
   - Revisar archivos con `Depends(get_current_active_user)` y confirmar que cada handler tiene el `Depends(require_permission(...))` correspondiente.

3. **Definir “fuente única” de superadmin:**
   - Si el estándar requerido es “solo `is_super_admin`”, ajustar `get_user_type`/LBAC para no inferir superadmin por rol/nivel (o al menos documentarlo como diseño).

4. **(Opcional) Mover validación CORE al login/refresh cuando se habilite:**
   - Aunque no se cambió por requerimiento, es el lugar más temprano para bloquear acceso y evitar sesiones “válidas” que fallan luego en `/me/`.

