# F13-H1 — Runtime Trace de Impersonation (Focused)

**Fecha:** 2026-06-25  
**Alcance:** trace runtime paso a paso (17 puntos) de tres endpoints tenant, comparando **Tenant Admin Dedicated** vs **Platform Admin impersonando** el mismo tenant.  
**Restricciones:** solo evidencia observada en código + ejecución Docker; sin propuestas de solución.

**Tenant de referencia (Docker):**

| Campo | Valor |
|-------|-------|
| Subdominio | `acmee` |
| `cliente_id` | `8B0D7BD1-764C-4BC5-ADB4-C2D4A26195CD` |
| Código | `CLI019` |
| `tipo_instalacion` | `dedicated` |
| `database_type` | `multi` |
| BD física tenant | `erp_cli019` @ `host.docker.internal` |
| Rol admin | `D9A6D685-59B1-4DE3-9E66-6CB9C1D77585` (`ADMIN_TENANT`) |
| Usuario tenant `admin` | `B901A140-4B77-46A7-A488-CC50B03601B0` |
| `rol_menu_permiso` (admin, DP acmee) | **18** filas |
| `cat_moneda` activas (DP acmee) | **0** filas |
| `usuario_rol` activas (`admin`, filtro empresa) | **1** fila |
| `superadmin` en DP acmee | **0** filas |
| Store SYSTEM (`bd_caxis_saas`) | `superadmin`: **1** fila; `cat_moneda` activas: **2** filas |
| SYSTEM `cliente_id` | `00000000-0000-0000-0000-000000000001` |

**Endpoints analizados:**

| # | Método y ruta | Uso |
|---|---------------|-----|
| EP1 | `GET /api/v1/permisos/roles/{rol_id}/permisos/` | Permisos del rol en pantalla RBAC |
| EP2 | `GET /api/v1/catalogos/monedas` | Representativo de todos los `cat_*` tenant |
| EP3 | `GET /api/v1/usuarios/{usuario_id}/roles/` | Modal **Editar usuario** — perfiles asignados |

**Metodología runtime:** scripts temporales `_f13_h1_host_trace.py` y `_f13_h1_trace.py` ejecutados dentro del contenedor `fastapi_backend`, más consultas SQL directas con `resolve_platform_tenant_data_execute_kwargs` / `execute_query`. Los scripts simulan la cadena `TenantContext` → `build_user_with_roles` → servicios con JWT sintéticos equivalentes a login tenant e impersonación (`impersonation_effective_level_info()`).

**Nota sobre host HTTP:** el middleware resuelve `request_cliente_id` desde el **subdominio del Host**, no desde el JWT. En impersonación coexisten dos hosts observables en runtime:

| Escenario | Host (subdominio) | `request_cliente_id` middleware |
|-----------|-------------------|----------------------------------|
| **Tenant Admin** | `acmee.*` | acmee |
| **Imp-A** | `acmee.*` + JWT impersonación | acmee |
| **Imp-B** | `platform` / SYSTEM + JWT impersonación | SYSTEM |

Imp-A e Imp-B son el mismo operador Platform impersonando; divergen **antes** de EP1/EP2/EP3 en Imp-A (auth), y **en el paso de `cliente_id` de datos** en Imp-B.

---

## Cadena común de autenticación (pasos 1–7)

Aplica a los tres endpoints vía `Depends(get_current_active_user)`.

### Tenant Admin (`admin` @ host acmee)

| Paso | Campo | Valor observado |
|------|-------|-----------------|
| 1 | JWT recibido | Bearer access token emitido en login tenant |
| 2 | Payload JWT | `sub=admin`, `cliente_id=8B0D7BD1-…`, `access_level=4`, `user_type=tenant_admin`, `is_super_admin=false`, `is_impersonation` ausente, `empresa_id` según sesión ERP |
| 3 | `current_user` construido | `build_user_with_roles("admin", request_cliente_id=acmee)` → `UsuarioReadWithRoles`; `usuario_id=B901A140-…`, `cliente_id=8B0D7BD1-…`, roles desde DP acmee |
| 4 | `cliente_id` utilizado (datos en endpoint) | **`current_user.cliente_id` = acmee** — ninguno de los tres endpoints usa `require_session_cliente_id` |
| 5 | `empresa_id` utilizada | Claim JWT / ContextVar `empresa_context` (p. ej. `0F70BE0D-332A-41BA-B008-05406C2CCD89` en acmee) |
| 6 | `is_impersonation` | `false` |
| 7 | Endpoint que entra | EP1 / EP2 / EP3 según ruta |

### Platform Admin impersonando — Imp-A (host acmee)

| Paso | Campo | Valor observado |
|------|-------|-----------------|
| 1 | JWT recibido | Bearer token post-`ImpersonationService.iniciar_impersonacion` |
| 2 | Payload JWT | `sub=superadmin`, `cliente_id=8B0D7BD1-…` (tenant objetivo), `is_impersonation=true`, `access_level=4`, `user_type=tenant_admin`, `is_super_admin=false`, `effective_scope=tenant` |
| 3 | `current_user` construido | **`None`** — `IdentityGateway.lookup_user_for_auth_context("superadmin", request_cliente_id=acmee)` → usuario no existe en DP acmee (conteo runtime: 0 filas) |
| 4–7 | — | **No alcanza el endpoint.** `get_current_active_user` → `get_user_auth_context` retorna `None` → HTTP 401 (`credentials_exception`) **antes** de EP1/EP2/EP3 |

`resolve_session_cliente_id` con este JWT devolvería `cliente_id=acmee`, `source=jwt_impersonation`, pero **ningún endpoint trazado consume ese resolver**.

### Platform Admin impersonando — Imp-B (host SYSTEM / platform)

| Paso | Campo | Valor observado |
|------|-------|-----------------|
| 1 | JWT recibido | Mismo token impersonación que Imp-A |
| 2 | Payload JWT | Igual que Imp-A: `cliente_id` JWT = acmee, `is_impersonation=true` |
| 3 | `current_user` construido | `IdentityGateway.lookup_user_for_auth_context` → rama `is_system_request_client` → `get_platform_user_by_username("superadmin")` → fila SYSTEM; `_resolve_cliente_id(user_result, request_cliente_id=SYSTEM)` → **`cliente_id=00000000-0000-0000-0000-000000000001`**; `usuario_id=8E5D0E3A-8E77-4022-8BF6-E73E98A2A132` |
| 4 | `cliente_id` utilizado (datos en endpoint) | **`current_user.cliente_id` = SYSTEM** — distinto del `cliente_id` del JWT (acmee) y de `resolve_session_cliente_id` → acmee |
| 5 | `empresa_id` utilizada | Claim JWT si empresa ya seleccionada en flujo impersonación; si ausente, EP3 falla en `resolve_role_list_scope` con `MISSING_SESSION_EMPRESA` |
| 6 | `is_impersonation` | `true`; `is_impersonation_effective_tenant_session(payload)` → omite `validate_tenant_access` |
| 7 | Endpoint que entra | EP1 / EP2 / EP3 (auth OK) |

**Primer paso exacto donde Imp-B deja de ser idéntico a Tenant Admin (común a EP1–EP3):** paso **4** — el endpoint recibe `current_user.cliente_id=SYSTEM` mientras Tenant Admin recibe `acmee`. El JWT impersonado y `resolve_session_cliente_id` ya apuntan a acmee en paso 2, pero **no participan** en la lectura de datos de estos handlers.

---

## EP1 — `GET /api/v1/permisos/roles/{rol_id}/permisos/`

**Handler:** `get_permissions_for_role` — `endpoints_permisos.py` L178–200  
**Parámetro de ruta en trace:** `rol_id=D9A6D685-59B1-4DE3-9E66-6CB9C1D77585`

### Trace completo — Tenant Admin

| Paso | Detalle |
|------|---------|
| 8 | Servicio: `PermisoService` |
| 9 | Método: `obtener_permisos_por_rol(cliente_id=current_user.cliente_id, rol_id=rol_id)` |
| 10 | **OperationStoreResolver:** no invocado por `PermisoService`. Routing indirecto vía `execute_query(..., client_id=cliente_id)` |
| 11 | `execute_query` ×2: (a) `RolService.obtener_rol_por_id(rol_id)` sin `client_id` explícito → contexto tenant acmee; (b) query permisos con `client_id=acmee` |
| 12 | `connection_type` | `DatabaseConnection.DEFAULT` |
| 13 | `database_type` | `multi` (Dedicated) |
| 14 | BD física | `erp_cli019` @ `host.docker.internal` |
| 15 | SQL (permisos, tras validar rol) | `SELECT … FROM rol_menu_permiso p INNER JOIN modulo_menu m … WHERE p.cliente_id = :cliente_id AND p.rol_id = :rol_id ORDER BY m.orden` con `:cliente_id=8B0D7BD1-…`, `:rol_id=D9A6D685-…` |
| 16 | Respuesta | **200**, lista con **18** permisos (`permisos_count=18` en `_f13_h1_host_trace.py`) |
| 17 | vs Imp-B | Idéntico hasta paso 7; diverge en paso 4 (`cliente_id`) y pasos 11–16 |

### Trace completo — Imp-B (único caso Imp que alcanza EP1)

| Paso | Detalle |
|------|---------|
| 8–9 | Igual servicio/método; **`cliente_id=SYSTEM`** |
| 10 | OSR no invocado; `execute_query(..., client_id=SYSTEM)` |
| 11 | (a) `obtener_rol_por_id` consulta store SYSTEM → rol `D9A6D685-…` **no existe** en `bd_caxis_saas`; log runtime: *"Intento de obtener permisos para rol inexistente"* → retorna `[]` **sin ejecutar** SQL de permisos |
| 12–14 | `DEFAULT` → `bd_caxis_saas` (store SYSTEM), no `erp_cli019` |
| 15 | SQL permisos: **no ejecutado** (early return por rol ausente) |
| 16 | Respuesta | **200**, lista **vacía** (`permisos_count=0`) |
| 17 | Comparación | Tenant: 18 filas desde `erp_cli019` filtrando `cliente_id=acmee`. Imp-B: 0 filas — primera divergencia de datos en **`RolService.obtener_rol_por_id`** (paso 11), causada por `cliente_id`/contexto SYSTEM del paso 4 |

### Imp-A

No alcanza pasos 8–16 (401 en deps).

---

## EP2 — `GET /api/v1/catalogos/monedas`

**Handler:** `list_monedas` — `catalogos/endpoints.py` L20–25

### Trace completo — Tenant Admin

| Paso | Detalle |
|------|---------|
| 8 | Servicio: `CatalogosService` |
| 9 | Método: `list_monedas(client_id=current_user.cliente_id, solo_activos=True)` |
| 10 | OSR: no invocado; routing vía `execute_query(q, client_id=acmee)` |
| 11 | `execute_query(select(CatMonedaTable)…)` |
| 12 | `connection_type` | `DatabaseConnection.DEFAULT` |
| 13 | `database_type` | `multi` |
| 14 | BD física | `erp_cli019` |
| 15 | SQL | `SELECT … FROM cat_moneda WHERE es_activo = 1 ORDER BY codigo` (SQLAlchemy Core) |
| 16 | Respuesta | **200**, **`[]`** — 0 monedas en DP acmee (conteo directo y `monedas_count=0` en trace) |
| 17 | vs Imp-B | Misma ruta de código; diverge en paso 4 y store físico consultado |

### Trace completo — Imp-B

| Paso | Detalle |
|------|---------|
| 8–9 | `CatalogosService.list_monedas(client_id=SYSTEM, …)` |
| 10 | OSR no invocado; `client_id=SYSTEM` |
| 11–14 | `execute_query` → **`bd_caxis_saas`**, no `erp_cli019` |
| 15 | Misma forma SQL sobre `cat_moneda` |
| 16 | Respuesta | **200**, **2** monedas (`monedas_count=2` en trace) |
| 17 | Comparación | Tenant e Imp-B **no son idénticos**: Tenant vacío (DP acmee sin seed); Imp-B devuelve catálogo del store SYSTEM. Primer paso divergente: **paso 4** (`client_id=SYSTEM` → paso 14 BD distinta) |

### Imp-A

401 antes del endpoint.

**Nota factual EP2:** en acmee el tenant admin también obtiene 0 monedas; la paridad “vacío” solo coincide si Imp-B consultara acmee. Con host SYSTEM la respuesta deja de ser vacía.

---

## EP3 — `GET /api/v1/usuarios/{usuario_id}/roles/`

**Handler:** `read_usuario_roles` — `users/presentation/endpoints.py` L756–809  
**Parámetro en trace:** `usuario_id=B901A140-4B77-46A7-A488-CC50B03601B0` (usuario `admin`)

### Trace completo — Tenant Admin

| Paso | Detalle |
|------|---------|
| 8 | Servicio: `UsuarioService` |
| 9 | Método: `obtener_roles_de_usuario(cliente_id=current_user.cliente_id, usuario_id=…, list_scope=…)` |
| 10 | OSR: no invocado |
| 11 | `execute_query(qmark_sql_text(...))` **sin** `client_id=` explícito → `client_id` efectivo desde **TenantContext middleware** (acmee) + filtro `ur.cliente_id = ?` con tupla `(usuario_id, cliente_id)` |
| 12 | `connection_type` | `DatabaseConnection.DEFAULT` |
| 13 | `database_type` | `multi` |
| 14 | BD física | `erp_cli019` |
| 15 | SQL | `SELECT r.rol_id, … FROM dbo.rol r INNER JOIN dbo.usuario_rol ur … WHERE ur.usuario_id = ? AND ur.cliente_id = ? AND ur.es_activo = 1 AND r.es_activo = 1 {empresa_sql} ORDER BY r.nombre` |
| — | `list_scope` | `resolve_role_list_scope`: `is_impersonation` → `is_platform_operator=false`; con `empresa_id` en JWT → `RoleListScope(tenant_wide=false, empresa_id=<empresa JWT>)` |
| 16 | Respuesta | **200**, **1** rol activo para `admin` en acmee (conteo SQL directo con `cliente_id=acmee`, `empresa_id=0F70BE0D-…`) |
| 17 | vs Imp-B | Diverge paso 4 y parámetro `cliente_id` en SQL |

### Trace completo — Imp-B

| Paso | Detalle |
|------|---------|
| 4 | `current_user.cliente_id=SYSTEM`; JWT `cliente_id=acmee` |
| — | `resolve_role_list_scope`: `is_impersonation=true` → **`is_platform_operator` retorna `false`** (`company_scope.py` L206–207) — mismo branch tenant que Impersonation pretende simular, no branch platform |
| 8–9 | `obtener_roles_de_usuario(cliente_id=SYSTEM, usuario_id=B901A140-…, list_scope=tenant_wide=false + empresa JWT)` |
| 11 | `execute_query` sin `client_id` → TenantContext **SYSTEM**; WHERE incluye `ur.cliente_id = SYSTEM` |
| 14 | BD física | `bd_caxis_saas` |
| 15 | Misma plantilla SQL; `:cliente_id` en tupla = SYSTEM UUID |
| 16 | Respuesta | **200**, **0** roles — no existe `usuario_rol` para `B901A140-…` con `cliente_id=SYSTEM` en store platform |
| 17 | Comparación | Tenant: 1 rol desde `erp_cli019`. Imp-B: 0 roles. Primer paso divergente: **paso 4** (`cliente_id=SYSTEM` en argumento de servicio y en cláusula SQL) |

### Imp-A

401 antes del endpoint.

### Imp-B sin `empresa_id` en JWT

`resolve_role_list_scope` → `AuthorizationError` *"No hay empresa activa en la sesión"* (`MISSING_SESSION_EMPRESA`) — observado en trace aislado antes de invocar servicio. Tenant Admin con mismo JWT incompleto fallaría igual en paso de scope; con empresa seleccionada, Tenant Admin continúa e Imp-B diverge solo en `cliente_id`.

---

## OperationStoreResolver — evidencia para target acmee

Invocado explícitamente solo en auditoría (`_f13_h1_trace.py`), **no** en `PermisoService`, `CatalogosService` ni `UsuarioService.obtener_roles_de_usuario`:

```json
{
  "connection_type": "DatabaseConnection.DEFAULT",
  "client_id": "8b0d7bd1-764c-4bc5-adb4-c2d4a26195cd",
  "database_type_legacy": "multi",
  "identity_scope": "IdentityScope.ENGINE_SCOPED",
  "operation_class": "tenant_data"
}
```

Si Imp-B pasara `client_id=acmee` a `execute_query`, OSR/metadata de acmee resolverían `erp_cli019`. Los endpoints trazados pasan **`current_user.cliente_id` (SYSTEM)** o contexto middleware SYSTEM, no el target JWT.

---

## Resumen — primer punto de divergencia por endpoint

| Endpoint | Tenant Admin (acmee) | Imp-A (acmee host) | Imp-B (SYSTEM host) | **Primer paso donde deja de ser idéntico a Tenant Admin** |
|----------|----------------------|--------------------|---------------------|-------------------------------------------------------------|
| EP1 permisos | 18 permisos | 401 (sin endpoint) | 0 permisos | **Imp-A:** paso 3 (`get_user_auth_context` → usuario no en DP). **Imp-B:** paso **4** (`current_user.cliente_id`); manifestación de datos en paso **11** (`obtener_rol_por_id` en store SYSTEM) |
| EP2 monedas | 0 monedas | 401 | 2 monedas | **Imp-A:** paso 3. **Imp-B:** paso **4** → paso **14** (BD `bd_caxis_saas` vs `erp_cli019`) |
| EP3 roles usuario | 1 rol | 401 | 0 roles | **Imp-A:** paso 3. **Imp-B:** paso **4** (`cliente_id=SYSTEM` en servicio y SQL) |

**Hecho transversal:** los tres handlers leen **`current_user.cliente_id`**, no `require_session_cliente_id` ni `resolve_session_cliente_id`. En impersonación, JWT y session scope ya resuelven acmee (paso 2), pero el paso 4 de datos usa la fila del operador platform (SYSTEM) cuando el host es SYSTEM (Imp-B).

**Evidencia runtime consolidada (`_f13_h1_host_trace.py`):**

```json
[
  {"label": "tenant_admin@acmee_host", "permisos_count": 18, "monedas_count": 0, "current_user_cliente_id": "8b0d7bd1-764c-4bc5-adb4-c2d4a26195cd"},
  {"label": "impersonation@acmee_host", "user_found": false},
  {"label": "impersonation@platform_host", "permisos_count": 0, "monedas_count": 2, "current_user_cliente_id": "00000000-0000-0000-0000-000000000001", "session_cliente_id": "8b0d7bd1-764c-4bc5-adb4-c2d4a26195cd"}
]
```

---

## Referencias de código (puntos de lectura del trace)

| Paso | Ubicación |
|------|-----------|
| Middleware → `request_cliente_id` | `app/core/tenant/middleware.py` |
| JWT / deps | `app/api/deps.py` (`get_current_active_user`, L171+) |
| Lookup impersonación SYSTEM vs tenant | `app/core/identity/identity_gateway.py` L552–574 |
| `_resolve_cliente_id` (prioriza fila usuario) | `app/core/auth/user_builder.py` L82–93 |
| Session scope JWT impersonación (no usado en EP1–3) | `app/core/tenant/session_scope.py` L66–87 |
| EP1 `cliente_id` | `app/modules/rbac/presentation/endpoints_permisos.py` L197–199 |
| EP2 `client_id` | `app/modules/catalogos/presentation/endpoints.py` L25 |
| EP3 `cliente_id` + scope | `app/modules/users/presentation/endpoints.py` L800–808 |
| `is_platform_operator` + impersonación | `app/core/tenant/company_scope.py` L194–214 |
| SQL permisos | `app/modules/rbac/application/services/permiso_service.py` L412–431 |
| SQL catálogos | `app/modules/catalogos/application/services/catalogos_service.py` L25–30 |
| SQL roles usuario | `app/modules/users/application/services/user_service.py` L1839–1852 |

---

**Fin F13-H1.** Sin implementación. Sin commits.
