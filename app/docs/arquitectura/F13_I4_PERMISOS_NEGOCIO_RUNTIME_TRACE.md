# F13-I4 — Runtime Trace: `GET /roles/{rol_id}/permisos-negocio/` (404 residual)

**Fecha:** 2026-06-25  
**Contexto:** Tras F13-I2 (overlay `current_user.cliente_id`) e F13-I3 (pre-check rol en `PermisoService`),  
`GET /api/v1/permisos/roles/{rol}/permisos/` → **200**, pero  
`GET /api/v1/roles/{rol}/permisos-negocio/` → **404**.  
**Alcance:** auditoría en código actual; sin implementación ni propuestas de fix.

**Tenant de referencia (evidencia previa F13-H1):** acmee / CLI019 Dedicated; rol admin `D9A6D685-59B1-4DE3-9E66-6CB9C1D77585`.

---

## Respuestas (7 puntos)

### 1. ¿Cuál es el router exacto que atiende ese endpoint?

| Campo | Valor |
|-------|-------|
| **Ruta HTTP completa** | `GET /api/v1/roles/{rol_id}/permisos-negocio/` |
| **Montaje** | `app/api/v1/api.py` L149–152 — `include_router(rbac_endpoints.router, prefix="/roles")` |
| **Archivo handler** | `app/modules/rbac/presentation/endpoints.py` |
| **Función** | `get_permisos_negocio_rol` (L741–768) |
| **Decorador** | `@router.get("/{rol_id}/permisos-negocio/", …)` (L728–739) |

---

### 2. ¿Qué dependencias FastAPI ejecuta? (en orden)

```
1. TenantMiddleware                    [app/core/tenant/middleware.py]
   → TenantContext (request_cliente_id = Host: SYSTEM @ platform o tenant @ acmee)

2. OAuth2 Bearer                       [get_current_user_data — app/api/deps.py]
   → payload JWT (impersonación: cliente_id = tenant target)

3. get_current_active_user             [app/api/deps.py — vía require_permission]
   → build_user_with_roles
   → F13-I2 overlay cliente_id (impersonación)
   → apply_impersonation_effective_permissions_to_user

4. require_permission("admin.rol.leer") [app/core/authorization/rbac.py L417–473]
   → has_permission(current_user, "admin.rol.leer")
   → router dependency L739

5. get_current_active_user             [parámetro handler L743 — misma instancia cacheada FastAPI]

6. get_permisos_negocio_rol(rol_id, current_user)
```

**Nota:** Este endpoint **no** usa `require_admin` ni `get_rbac_session_client_id` (a diferencia de listados RBAC en `rbac_deps.py`).

---

### 3. ¿Qué servicios invoca? (orden exacto)

Dentro de `get_permisos_negocio_rol`:

| Orden | Servicio / función | Invocación |
|-------|-------------------|------------|
| 1 | `RolService.obtener_rol_por_id` | L747 — `rol_id`, `incluir_inactivos=True`, **sin `cliente_id`** |
| 2 | *(si rol is None → 404; cadena aborta)* | |
| 3 | `get_permisos_negocio_by_rol` | L756 — `permisos_negocio_service.py` |

Si el paso 1 devolviera rol, `get_permisos_negocio_by_rol` ejecutaría:

| Orden | Servicio / función | Invocación |
|-------|-------------------|------------|
| 3a | `resolve_platform_tenant_data_database_type` | L120 |
| 3b | `RolService.obtener_rol_por_id` | L124 — **otra vez sin `cliente_id`** |
| 3c | `_permisos_negocio_rol_dedicated` o `_permisos_negocio_rol_single` | L136–138 |
| 3d | `execute_query` sobre `rol_permiso` + `permiso` (catálogo vía `resolve_permission_catalog_target`) | L154–180 |

**No participan en esta cadena:** `PermisoService`, `PermisoService.obtener_permisos_por_rol`, ni delegación al endpoint `/permisos/roles/{id}/permisos/`.

---

### 4. ¿En qué función se genera el 404?

| Campo | Valor |
|-------|-------|
| **Archivo** | `app/modules/rbac/presentation/endpoints.py` |
| **Función** | `get_permisos_negocio_rol` |
| **Líneas** | **L748–749** |

```747:749:app/modules/rbac/presentation/endpoints.py
        rol = await RolService.obtener_rol_por_id(rol_id=rol_id, incluir_inactivos=True)
        if rol is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rol con ID {rol_id} no encontrado.")
```

**Causa inmediata:** `obtener_rol_por_id` sin `cliente_id` → `execute_query(query)` usa **TenantContext del Host (SYSTEM)** → rol no existe en `bd_caxis_saas` → retorna `None`.

**404 alternativo (no alcanzado si falla en L747):** `get_permisos_negocio_by_rol` L124–126 lanza `NotFoundError` → capturado L760–762 como `CustomException` → `HTTPException(status_code=404)`.

---

### 5. ¿Ese 404 proviene de…?

| Origen | ¿Es el generador? |
|--------|-------------------|
| **HTTPException** | **Sí** — L749 (primario en impersonación @ platform host) |
| CustomException / NotFoundError | Posible vía L760–762 si pasara el pre-check del handler |
| RolService | **Indirecto** — `obtener_rol_por_id` retorna `None` (no lanza 404) |
| PermisoService | **No** |
| PermisosNegocioService | **No** en el 404 observado (no se llega a L756 si L747 falla) |
| Otro | **No** |

Clasificación: **HTTPException explícita en presentation**, disparada por lookup de rol fallido en store incorrecto.

---

### 6. ¿El RolService modificado en F13-I3 participa realmente en esta cadena?

**Sí**, pero **sin el parámetro `cliente_id` que F13-I3 introdujo**.

| Evidencia | Detalle |
|-----------|---------|
| Participación | L747 y (si continuara) L124 llaman `RolService.obtener_rol_por_id` |
| F13-I3 | Solo aplica cuando `cliente_id is not None` → routing OSR / `resolve_platform_tenant_data_execute_kwargs` |
| Llamada actual | `obtener_rol_por_id(rol_id=rol_id, incluir_inactivos=True)` — **sin `cliente_id`** |
| Comportamiento efectivo | Rama **legacy** L403–404 `execute_query(query)` → TenantContext Host = SYSTEM |
| Contraste F13-I3 corregido | `PermisoService.obtener_permisos_por_rol` L407: `obtener_rol_por_id(rol_id, cliente_id=cliente_id)` ✅ |

**Conclusión:** F13-I3 **no cubre** este endpoint porque el handler y `get_permisos_negocio_by_rol` no propagan `cliente_id` al lookup de rol.

---

### 7. ¿Usa `GET /permisos/roles/{id}/permisos/` internamente o lógica distinta?

**Lógica completamente distinta.** No hay import, redirect ni llamada HTTP/servicio cruzada.

| Aspecto | `GET /permisos/roles/{rol_id}/permisos/` | `GET /roles/{rol_id}/permisos-negocio/` |
|---------|------------------------------------------|----------------------------------------|
| Router | `endpoints_permisos.py` → `get_permissions_for_role` | `endpoints.py` → `get_permisos_negocio_rol` |
| Prefijo API | `/api/v1/permisos/...` | `/api/v1/roles/...` |
| Servicio | `PermisoService.obtener_permisos_por_rol` | `get_permisos_negocio_by_rol` |
| Tablas | `rol_menu_permiso` ⋈ `modulo_menu` | `rol_permiso` ⋈ `permiso` (catálogo RBAC) |
| Semántica | Permisos de **menú** (acciones UI) | Permisos de **negocio** (códigos `org.*`, `admin.*`, etc.) |
| Pre-check rol F13-I3 | ✅ `cliente_id=current_user.cliente_id` | ❌ sin `cliente_id` |
| Respuesta vacía vs 404 | Pre-check fallido → **200 []** (PermisoService L409–410) | Pre-check fallido → **404** (endpoints L748–749) |

---

## Diagrama completo de ejecución (impersonación @ platform host)

```mermaid
flowchart TD
    REQ[GET /api/v1/roles/{rol_id}/permisos-negocio/]
    MW[TenantMiddleware → request_cliente_id=SYSTEM]
    JWT[get_current_user_data → JWT cliente_id=ACMEE]
    DEPS[get_current_active_user → F13-I2 overlay current_user.cliente_id=ACMEE]
    RBAC[require_permission admin.rol.leer]
    H[get_permisos_negocio_rol]

    REQ --> MW --> JWT --> DEPS --> RBAC --> H

    H --> R1[RolService.obtener_rol_por_id SIN cliente_id]
    R1 --> CTX[execute_query → TenantContext SYSTEM]
    CTX --> NF[rol NOT in bd_caxis_saas → None]
    NF --> E404[HTTPException 404 L749]

    H -.->|si rol existiera| PNG[get_permisos_negocio_by_rol]
    PNG --> R2[RolService.obtener_rol_por_id SIN cliente_id otra vez]
    PNG --> RP[rol_permiso + permiso catalog]

    EP1[GET /permisos/roles/{id}/permisos/]
    EP1 --> PS[PermisoService.obtener_permisos_por_rol]
    PS --> R3[RolService.obtener_rol_por_id CON cliente_id F13-I3]
    PS --> RMP[rol_menu_permiso → 200 18 items]

    style E404 fill:#f99
    style EP1 fill:#9f9
    style H fill:#ff9
```

### Cadena ASCII comparativa

```
IMPERSONACIÓN @ PLATFORM HOST
══════════════════════════════════════════════════════════════════

A) GET /api/v1/permisos/roles/{rol}/permisos/     [200 ✅]
   endpoints_permisos.get_permissions_for_role
   └─ PermisoService.obtener_permisos_por_rol(cliente_id=current_user.cliente_id)  ← F13-I2
      └─ RolService.obtener_rol_por_id(rol_id, cliente_id=cliente_id)               ← F13-I3
      └─ SQL rol_menu_permiso (client_id=ACMEE)

B) GET /api/v1/roles/{rol}/permisos-negocio/      [404 ❌]
   endpoints.get_permisos_negocio_rol
   └─ RolService.obtener_rol_por_id(rol_id)  ← SIN cliente_id
      └─ execute_query → store SYSTEM → None
   └─ HTTPException 404 L749
   (get_permisos_negocio_by_rol NO se ejecuta)
```

---

## Resumen ejecutivo

| Pregunta | Respuesta |
|----------|-----------|
| Handler | `endpoints.py` → `get_permisos_negocio_rol` |
| 404 | `HTTPException` L749 — rol `None` tras lookup en store Host |
| F13-I3 en cadena | Sí, pero **sin** `cliente_id` → fix I3 **no aplica** |
| vs `/permisos/roles/.../permisos/` | **Flujo distinto** (rol_permiso vs rol_menu_permiso) |
| Por qué FE sigue fallando | FE invoca `/roles/{id}/permisos-negocio/`, no el endpoint corregido por I3 |

---

**Fin F13-I4.** Sin implementación. Sin commits.
