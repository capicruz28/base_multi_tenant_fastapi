# Auditoría Arquitectónica Global — Alineación del Backend ERP

**Fecha:** 2026-06-03  
**Alcance:** Backend completo (`app/`) — arquitectura transversal, no módulo específico  
**Modo:** Solo lectura — sin generación ni modificación de código de aplicación  
**Fuentes:** código real, auditorías previas, `.cursorrules`, `docs/prompts/PROMPT_BACKEND_MAESTRO.md`

---

## Respuesta directa

> **Si mañana empezamos a refactorizar Compras (PUR), Ventas (SLS), Producción (MFG/MPS) y RRHH (HCM), ¿cuál debe ser el estándar oficial del backend?**

El estándar oficial debe ser el **patrón ERP consolidado ORG + INV (Fase 4)**, no el patrón legacy de users/rbac/tenant ni la estructura DDD teórica de cuatro capas completas.

| Dimensión | Estándar oficial V4 |
|-----------|---------------------|
| **Capas** | `presentation/` → `application/services/` (funciones `*_servicio`) → `app/infrastructure/database/queries/{mod}/` |
| **Sin** | `domain/entities` ni `infrastructure/repositories` por módulo ERP (salvo identidad/RBAC) |
| **Tenant** | `cliente_id` siempre desde sesión; nunca desde body/query para autorización |
| **Empresa** | `empresa_id` desde JWT → `empresa_context`; gate `require_erp_session` en router padre |
| **RBAC** | `Depends(require_permission("mod.recurso.accion"))` en cada endpoint |
| **Platform** | `@require_super_admin()` (LBAC) + `require_permission("tenant.*")` en mutaciones |
| **BD** | `DatabaseConnection.ADMIN` (SaaS) vs `DEFAULT` (ERP tenant); no existe enum `ERP` |
| **Errores** | `CustomException` propagada al handler global; nunca `except Exception → 500` |
| **Soft delete** | `es_activo = 0`; endpoints `DELETE` + `POST /{id}/reactivar` |
| **Cabecera-detalle** | Detalle embebido en body; escritura independiente → `deprecated=True` |
| **Paginación** | `page` + `limit` con `Paginated*Response` para listas grandes; maestros pequeños pueden listar completo |
| **Auditoría auth** | `AuditService.registrar_auth_event` (obligatorio en auth/platform) |
| **Auditoría ERP** | `aud_log_auditoria` vía servicio helper en operaciones críticas (nuevo estándar) |

Los módulos PUR, SLS, MFG, HCM existen hoy con patrones heterogéneos (repositories locales, sin `require_erp_session`, paginación mixta). La refactorización debe **converger hacia ORG/INV**, no replicar users/rbac ni tenant.

---

## 1. Arquitectura actual real

### 1.1 Estado del monolito modular

El backend es un **monolito modular** bajo `app/modules/{codigo}/` montado desde `app/api/v1/api.py`. La arquitectura documentada (presentation → application → domain → infrastructure por módulo) **solo se cumple parcialmente**.

```
app/
├── api/                    # deps.py, deps_auth.py, v1/api.py
├── core/                   # tenant, auth, authorization, exceptions, security
├── infrastructure/database/
│   ├── queries/{mod}/      # SQLAlchemy Core — capa de datos ERP
│   ├── queries_async.py    # execute_query con routing tenant
│   ├── tables/             # tablas SaaS central
│   ├── tables_erp/         # tablas ERP por módulo
│   └── repositories/       # BaseRepository — solo identidad/RBAC
├── modules/{mod}/
│   ├── presentation/       # endpoints_*.py, schemas.py, *_deps.py
│   ├── application/services/
│   ├── domain/             # vacío o mínimo en ERP
│   └── infrastructure/     # ausente en ERP; presente en users/rbac/auth
└── shared/                 # validators.py, value_objects (uso limitado)
```

### 1.2 Tres patrones coexistiendo

| Patrón | Módulos | Presentation | Application | Datos |
|--------|---------|--------------|-------------|-------|
| **A — ERP moderno** | ORG, INV | `endpoints_*.py`, schemas con validators | Funciones `*_servicio` | `queries/{mod}/` centralizadas |
| **B — Plataforma/identidad** | users, rbac, auth | Class services | `BaseService`, use_cases (auth, parcial) | Repositories + SQL inline |
| **C — Admin SaaS** | tenant, superadmin, modulos | Class services monolíticos | SQL embebido | Siempre `ADMIN` |

**Referencia para refactorización futura:** Patrón A (ORG/INV).

### 1.3 Capas — uso real

| Capa | Rol real | Convención de archivos |
|------|----------|------------------------|
| **presentation** | Routers FastAPI, schemas Pydantic, deps locales (`org_deps.py`) | `endpoints_{entidad}.py`, `schemas.py`, router agregador `endpoints.py` |
| **application** | Lógica de negocio, orquestación, validaciones de dominio | `services/{entidad}_service.py` con funciones async |
| **domain** | Entidades de negocio | Solo en users/rbac/auth; **vacío en ORG/INV** |
| **infrastructure (módulo)** | Persistencia | **No usado en ERP**; queries viven en `app/infrastructure/` global |
| **queries** | SQL parametrizado, filtros tenant/empresa | `{mod}/{entidad}_queries.py` |
| **repositories** | CRUD genérico con soft delete | `BaseRepository` — users, rbac, auth únicamente |
| **services (nombre)** | En docs = application layer; no confundir con microservicios | Sufijo `_servicio` o `_service.py` |

### 1.4 Patterns utilizados realmente

| Pattern | Dónde | Estado |
|---------|-------|--------|
| **Dependency Injection (FastAPI Depends)** | Universal | ✅ Estándar |
| **ContextVar (tenant, empresa)** | `context.py`, `empresa_context.py` | ✅ Estándar ERP |
| **Router-level session gate** | INV (`require_erp_session`) | ✅ Obligatorio ERP |
| **Module-level deps** | ORG (`org_deps.py`, `OrgScopePolicy`) | ✅ Referencia multi-política |
| **Functional application services** | ORG, INV | ✅ Referencia |
| **Class-based services + staticmethods** | tenant, superadmin, users | ⚠ Legacy — no replicar |
| **Repository pattern** | users, rbac | ⚠ Solo identidad |
| **Unit of Work** | `core/application/unit_of_work.py` | ⚠ Existe pero poco usado en ERP |
| **Use Cases** | auth (`LoginUseCase`) | ⚠ No cableado; auth usa `AuthService` directo |
| **Code-first RBAC** | `RequirePermission(metadata)` | ⚠ Emergente (LOG); convive con strings |
| **Deprecated endpoints** | INV (detalle, stock) | ✅ Patrón correcto para deuda |

### 1.5 Inconsistencias arquitectónicas globales

1. **Capas duplicadas:** ERP usa queries globales; users/rbac usan repositories por módulo.
2. **Dos estilos de servicio:** funciones vs clases — sin criterio documentado hasta esta auditoría.
3. **Session gate desigual:** INV lo aplica en router padre; PUR/SLS/MFG/HCM no.
4. **Resolución de `cliente_id`:** ORG usa `get_org_session_client_id`; INV usa `current_user.cliente_id`.
5. **Exception handling:** ORG/INV sanos; tenant/users/superadmin con anti-patrón `except Exception → 500`.
6. **Paginación:** tres estilos (`skip/limit`, `page/limit`, sin paginación).
7. **Headers de archivo obsoletos:** rutas `# app/services/...` indican migración incompleta.

---

## 2. Multi-tenant

### 2.1 Tenant context

| Componente | Archivo | Función |
|------------|---------|---------|
| `TenantContext` | `app/core/tenant/context.py` | ContextVar: `cliente_id`, subdominio, `database_type`, credenciales |
| `TenantMiddleware` | `app/core/tenant/middleware.py` | Resuelve tenant por subdominio vía `ADMIN` |
| `get_current_client_id()` | `context.py` | Lectura del contexto activo |
| Routing | `app/core/tenant/routing.py` | Resolución de conexión por tenant |

**Flujo:**

```
Request → TenantMiddleware → lookup cliente (ADMIN) → set TenantContext → endpoint → reset
```

### 2.2 `cliente_id` — reglas reales

| Regla | Implementación |
|-------|----------------|
| Toda query ERP filtra `cliente_id` | Queries en `queries/{mod}/` |
| No aceptar `cliente_id` en query/body para autorización | `reject_legacy_cliente_query`, `reject_client_empresa_scope_override` |
| Impersonación usa tenant del JWT, no SYSTEM | `session_scope.resolve_session_cliente_id` |
| Platform opera sobre ADMIN sin tenant | `client_id=None` explícito |

**Prioridad ORG (referencia más completa):**

1. JWT `cliente_id` si `is_impersonation`
2. `request.state.cliente_id` (middleware)
3. ContextVar tenant
4. `current_user.cliente_id` (legacy)

### 2.3 Tenant SYSTEM (platform)

- Cliente reservado `SUPERADMIN_CLIENTE_ID` / subdominio `platform`
- Usuario platform: `user_type=platform_admin`, `access_level=5`
- Operaciones cross-tenant solo con LBAC level 5
- Cross-tenant access auditado: `AuditService.registrar_tenant_access`

### 2.4 Impersonación

| Aspecto | Comportamiento |
|---------|----------------|
| Inicio | `POST /auth/impersonate/{cliente_id}/` — RBAC `require_super_admin()` |
| Token | 120 min, sin refresh; claims `is_impersonation`, `impersonated_by` |
| Identidad JWT | `sub` = SYSTEM user, no el operador |
| Privilegios platform | Suprimidos (`suppress_platform_privileges`) |
| RBAC efectivo | Rol `ADMIN_TENANT` filtrado por `cliente_modulo` |
| Sesión padre | Redis — restauración en `/impersonate/end/` |
| Multi-empresa | Puede emitir `selection_token` igual que login normal |

### 2.5 Aislamiento de datos

| Mecanismo | Cobertura |
|-----------|-----------|
| Filtro SQL `cliente_id` | ERP moderno ✅ |
| Validación en `execute_query` | `queries_async.py` ✅ |
| Cross-tenant superadmin | Permitido con audit ✅ |
| Impersonación | Tenant del JWT, no SYSTEM ✅ |
| Legacy modules | Cobertura irregular ⚠ |

---

## 3. Multiempresa

### 3.1 Empresa activa

| Componente | Archivo | Función |
|------------|---------|---------|
| JWT claim `empresa_id` | `jwt.py` | Empresa seleccionada post-login |
| `empresa_context` | `empresa_context.py` | ContextVar poblado en `deps.get_current_active_user` |
| `require_session_empresa_id()` | `company_scope.py` | 403 si no hay empresa |
| Login multi-paso | `auth_service.py` | `empresa_selection_pending` → token temporal |

### 3.2 `empresa_id` — reglas reales

| Regla | Detalle |
|-------|---------|
| Tablas con `empresa_id` | Filtro obligatorio en queries |
| Body no puede override sesión | `enforce_body_empresa_matches_session` |
| Cross-company → 404, no 403 | `assert_row_empresa` (no revelar existencia) |
| RBAC por empresa | `sql_empresa_filter_usuario_rol` — roles globales (`empresa_id IS NULL`) o scoped |

### 3.3 Contexto empresa

```
JWT empresa_id → deps.set_current_empresa_id → ContextVar → service.require_session_empresa_id()
```

### 3.4 Gate de sesión ERP (I1)

`require_erp_session` (`deps_auth.py`):

- Rechaza `empresa_selection_pending` (salvo impersonación documentada)
- Exige `empresa_id` en JWT para usuarios operativos
- Aplicado en router INV completo
- ORG usa políticas granulares (`OrgScopePolicy.TENANT | COMPANY | HYBRID`)

### 3.5 Aislamiento empresa — matriz ORG

| Recurso ORG | Política | Gate |
|-------------|----------|------|
| Empresa | TENANT | No exige empresa activa (admin multi-empresa) |
| Departamento, cargo, sucursal | COMPANY | `require_org_company_erp_session` |
| Centro costo | HYBRID | Según endpoint |

**Estándar V4:** Clasificar cada entidad del módulo como TENANT/COMPANY/HYBRID antes de implementar.

---

## 4. Seguridad

### 4.1 JWT

| Claim | Uso |
|-------|-----|
| `sub`, `cliente_id`, `empresa_id` | Identidad y scope |
| `access_level` (1–5) | LBAC |
| `is_super_admin`, `user_type` | Platform vs tenant |
| `type`, `jti` | access/refresh + revocación Redis |
| `is_impersonation`, `impersonated_by` | Impersonación |

Secrets separados: `SECRET_KEY` (access) / `REFRESH_SECRET_KEY` (refresh).

### 4.2 RBAC

- Patrón permiso: `{modulo}.{recurso}.{accion}` (ej. `inv.producto.crear`)
- Dependency: `Depends(require_permission("..."))`
- Resolución: `usuario_rol → rol_permiso → permiso`, filtrado por `cliente_modulo` (ADMIN lookup)
- Super admin: bypass total **excepto** durante impersonación
- Registro code-first: `RequirePermission(PermissionMetadata(...))` en startup

### 4.3 LBAC

| Nivel | Rol típico | Gate |
|-------|------------|------|
| 5 | SuperAdministrador / platform_admin | `@require_super_admin()` |
| 4 | AdministradorTenant | `@require_tenant_admin()` |
| 1–3 | Usuario operativo | `RoleChecker` en deps |

**Dual gate platform:** LBAC decorator + RBAC permission en clientes/conexiones/modulos.

### 4.4 `require_permission` vs `require_super_admin`

| Mecanismo | Forma | Usado en |
|-----------|-------|----------|
| `require_permission` | FastAPI Depends | ERP modules, tenant CRUD |
| `@require_super_admin()` LBAC | Decorator | superadmin, tenant, modulos, auth-config |
| `require_super_admin()` RBAC | Depends | Solo impersonation endpoint |

**Inconsistencia crítica:** Dos implementaciones de `require_super_admin` con criterios ligeramente distintos (`platform_admin` explícito solo en RBAC).

### 4.5 Impersonación — seguridad

- Sin impersonación anidada (409)
- Redis obligatorio para sesión padre (503 si caído)
- Permisos = ADMIN_TENANT del tenant impersonado, no del operador
- Menú filtrado por prefijos de permiso efectivo

### 4.6 Riesgos documentados

1. Redis fail-soft en blacklist → tokens revocados pueden aceptarse
2. Superadmin endpoints sin RBAC granular (solo LBAC)
3. Dos clases `AuthorizationError` (HTTPException vs CustomException)

---

## 5. Base de datos

### 5.1 Enum real (no existe `ERP`)

```python
class DatabaseConnection(Enum):
    DEFAULT = "default"   # Tenant-aware (ERP operacional)
    ADMIN = "admin"       # BD central SaaS
```

`DatabaseConnection.ERP` **no existe**. "ERP" es concepto: datos operacionales vía `DEFAULT`.

### 5.2 Reglas de uso observadas

| Conexión | Destino físico | Tablas / operaciones |
|----------|----------------|----------------------|
| **ADMIN** | BD central (`DB_ADMIN_*`) | `cliente`, `cliente_conexion`, `cliente_modulo`, `modulo`, `modulo_menu`, seeds, auth config |
| **DEFAULT** | Shared `bd_sistema` o BD dedicada tenant | `org_*`, `inv_*`, `usuario`, `rol`, `usuario_rol`, ERP completo |

### 5.3 Routing DEFAULT

```
execute_query(..., client_id=UUID) → get_connection_for_tenant(cliente_id)
  ├── database_type = "single" → misma BD compartida
  └── database_type = "multi"  → credenciales de cliente_conexion
```

### 5.4 Casos híbridos

| Operación | Conexión |
|-----------|----------|
| `auth_audit_log` tenant shared | ADMIN |
| `auth_audit_log` tenant dedicado | DEFAULT |
| Permisos suscritos (`cliente_modulo`) | ADMIN |
| Permisos efectivos (`usuario_rol`) | DEFAULT |
| TenantMiddleware lookup | ADMIN |

### 5.5 Inconsistencias

1. Documentación externa menciona `ERP` como tercer tipo — **incorrecto**
2. SQL inline en tenant/superadmin vs queries centralizadas en ERP
3. Sync `connection.py` legacy coexiste con `connection_async.py`
4. Repositories rbac con llamadas sync a métodos async (`find_all` sin await)

---

## 6. Contratos API

### 6.1 Paginación — tres estilos coexistiendo

| Estilo | Parámetros | Response | Módulos |
|--------|------------|----------|---------|
| **A** | `skip`, `limit` | `total`, items | tenant/clientes |
| **B** | `page`, `limit` | `pagina_actual`, `total_paginas` | users, superadmin auditoría, rbac |
| **C** | Sin paginación | `list[Read]` | ORG, INV maestros |
| **D** | `page`, `page_size` | custom | PUR cotizaciones |

**Estándar V4:** `page` (1-based) + `limit` (default 20, max 100) con schema `Paginated{Entity}Response`.

### 6.2 Filtros

| Filtro | Uso |
|--------|-----|
| `solo_activos: bool = True` | Universal en listados |
| `buscar: Optional[str]` | ORG: in-memory post-fetch; INV: SQL ILIKE — **unificar a SQL** |
| FK filters | `categoria_id`, `estado`, rangos fecha |
| Legacy rejection | Query params `cliente_id`/`empresa_id` ocultos → 403 |

### 6.3 UUID

- IDs expuestos como UUID v4 en paths y schemas
- Handler global mejora mensajes 422 para UUID inválido
- Coerción defensiva en scope helpers (`_coerce_cliente_id`)

### 6.4 Soft delete

| Operación | Patrón |
|-----------|--------|
| Desactivar | `DELETE /{id}` → `es_activo = False` (no DELETE físico) |
| Reactivar | `POST /{id}/reactivar` → `es_activo = True` |
| Permiso reactivar | `actualizar` (no `eliminar`) |
| Listados | `solo_activos=True` por defecto |

No se usa `deleted_at` / tombstone.

### 6.5 Activar / reactivar

- ORG: endpoints dedicados `/reactivar` en cargos, departamentos, etc.
- Tenant clientes: `/activar/`, `/suspender/`
- INV: `POST /{id}/reactivar` en productos, categorías, etc.

### 6.6 Errores HTTP

**Jerarquía canónica** (`app/core/exceptions.py`):

| Excepción | HTTP | Cuándo |
|-----------|------|--------|
| `ValidationError` | 400 | Entrada inválida |
| `AuthenticationError` | 401 | Token/credenciales |
| `AuthorizationError` | 403 | Permisos / sesión incompleta |
| `NotFoundError` | 404 | Recurso inexistente (incl. cross-scope) |
| `ConflictError` | 409 | Duplicados / unicidad |
| `DatabaseError` / `ServiceError` | 500 | Fallos internos |

**Handler global:** `{detail, error_code}` — en producción enmascara 5xx.

**Anti-patrón detectado:** `except Exception → HTTPException(500)` en tenant (108 bloques), users, superadmin — traga `ConflictError` y devuelve 500.

**Patrón sano (ORG/INV):**

```python
except (NotFoundError, ConflictError, CustomException) as e:
    raise HTTPException(status_code=e.status_code, detail=e.detail) from e
# o simplemente: dejar propagar CustomException al handler global
```

**Regla unicidad maestros:** validar antes de INSERT/UPDATE + red de seguridad SQL UNIQUE → 409.

**Regla estado transaccional:** operación de ciclo de vida → verificar estado → 422 con mensaje en español.

---

## 7. Auditoría

### 7.1 Modelo actual — dos capas

| Capa | Tabla | Writer | Reader | Cobertura |
|------|-------|--------|--------|-----------|
| **Auth/Security** | `auth_audit_log` | `AuditService` | `SuperadminAuditoriaService` | Login, logout, refresh, impersonación, cross-tenant |
| **ERP Business** | `aud_log_auditoria` | Manual POST | `/aud/log-auditoria` | Opt-in — sin hooks automáticos |

### 7.2 Routing auth audit

- Tenant shared DB → `ADMIN`
- Tenant dedicated DB → `DEFAULT`
- Fail-safe: errores de audit no rompen flujo de negocio

### 7.3 Cobertura real

| Evento | Auditado |
|--------|----------|
| Login/logout/refresh | ✅ |
| Impersonación start/end | ✅ |
| Cross-tenant superadmin | ✅ |
| CRUD clientes/conexiones | ❌ |
| CRUD ERP (productos, empresas, etc.) | ❌ automático |
| Cambios RBAC | ❌ automático |

### 7.4 Estándares obligatorios V4

1. **Auth events:** siempre `AuditService.registrar_auth_event` — no negociable
2. **ERP mutations críticas:** helper `registrar_auditoria_erp(modulo, tabla, accion, ...)` en services — nuevo estándar
3. **Platform CRUD:** auditar en `auth_audit_log` con eventos `platform_{recurso}_{accion}`
4. **Impersonación:** incluir `impersonated_by` en metadata de cualquier audit durante sesión impersonada

---

## 8. ORG — patrones consolidados

### 8.1 Estructura

```
org/presentation/
  endpoints.py          # Router agregador
  endpoints_empresa.py  # Por entidad
  endpoints_departamentos.py, endpoints_cargos.py, ...
  org_deps.py           # Session deps + OrgScopePolicy
  schemas.py            # Create/Update/Read + validators
org/application/services/
  empresa_service.py    # Funciones *_servicio
app/infrastructure/database/queries/org/
  empresa_queries.py
```

### 8.2 Patrones obligatorios ORG

| Patrón | Implementación |
|--------|----------------|
| Session client | `get_org_session_client_id` (impersonación-safe) |
| Scope policy | `OrgScopePolicy` por sub-router |
| Legacy rejection | `reject_legacy_cliente_query`, `reject_legacy_empresa_query` |
| RBAC | `require_permission("org.{recurso}.{accion}")` |
| Tenant-wide resources | `/org/empresa` — sin empresa activa requerida |
| Company resources | `/org/departamentos`, cargos — `require_org_company_erp_session` |
| Soft delete + reactivar | DELETE + POST reactivar |
| Validators | Mixins con `normalize_upper/lower/strip` en Create/Update |
| Exceptions | Mapeo explícito Conflict/NotFound → HTTPException |
| Queries | SQLAlchemy Core, filtro `cliente_id` (+ `empresa_id` si aplica) |

### 8.3 Referencia de endpoints

- `GET ""` → list (tenant o company scoped)
- `GET /{id}` → detail
- `POST ""` → create (client_id de sesión)
- `PUT /{id}` → update
- `DELETE /{id}` → soft delete
- `POST /{id}/reactivar` → reactivate

---

## 9. INV — patrones consolidados

### 9.1 Estructura

```
inv/presentation/
  endpoints.py              # Router padre + require_erp_session
  endpoints_productos.py
  endpoints_movimientos.py
  endpoints_movimientos_detalle.py  # deprecated escritura
  schemas.py, schemas_movimiento.py
inv/application/services/
  producto_service.py
  movimiento_service.py
app/infrastructure/database/queries/inv/
  producto_queries.py
  movimiento_queries.py
```

### 9.2 Patrones obligatorios INV

| Patrón | Implementación |
|--------|----------------|
| ERP session gate | `APIRouter(dependencies=[Depends(require_erp_session)])` en router padre |
| Empresa scope | `require_session_empresa_id()` en services |
| Body empresa | `enforce_body_empresa_matches_session` |
| client_id | `current_user.cliente_id` (con gate ERP garantiza coherencia) |
| RBAC | `require_permission("inv.{recurso}.{accion}")` |
| Maestros | CRUD + soft delete + reactivar |
| Transaccionales | Movimiento con detalle embebido (`MovimientoConDetalleCreate`) |
| Detalle standalone | Escritura `deprecated=True` |
| Derivadas (stock) | Solo GET; POST/PUT deprecated |
| Referencias | Validar FKs en misma empresa antes de persistir |
| Filtros SQL | ILIKE en query layer (preferible a in-memory) |

### 9.3 Cabecera-detalle — referencia INV

- `POST /inv/movimientos` con `MovimientoConDetalleCreate` ✅
- `PUT /inv/movimientos/{id}` con detalle embebido (borrador) ✅
- `POST /inv/movimientos-detalle` → **deprecated** ✅
- Transacciones SQL en service para cabecera + detalle

---

## 10. Platform Administration — patrones consolidados

### 10.1 Módulos y rutas

| Área | Prefijo API | Módulo | Auth |
|------|-------------|--------|------|
| Clientes tenant | `/clientes/` | tenant | LBAC + `tenant.cliente.*` |
| Conexiones BD | `/conexiones/` | tenant | LBAC + `tenant.conexion.*` |
| Auth config | `/auth-config/` | auth | LBAC only |
| Módulos/menús | `/modulos/` | modulos | LBAC + RBAC |
| Superadmin usuarios | `/superadmin/usuarios/` | superadmin | LBAC only |
| Superadmin auditoría | `/superadmin/auditoria/` | superadmin | LBAC only |
| Catálogos globales CRUD | `/catalogos-globales/` | superadmin | LBAC only |
| Catálogos tenant read | `/catalogos/` | catalogos | JWT normal |
| Impersonación | `/auth/impersonate/` | auth | RBAC Depends |

### 10.2 Patrones platform

| Patrón | Detalle |
|--------|---------|
| Conexión | Siempre `DatabaseConnection.ADMIN` |
| Cross-tenant query | Param `cliente_id` opcional en superadmin |
| Paginación | `page` + `limit` |
| Servicios | Class-based (`ClienteService`, `CatalogosGlobalesService`) — legacy aceptable en platform |
| Onboarding | `ClienteOnboardingService` — bootstrap tenant |
| Conexiones | Credenciales encriptadas (`encryption.py`) |
| Dashboard BFF | **No implementado** — frontend compone endpoints |

### 10.3 Catálogos globales

- Lectura tenant: `/catalogos/` — scoped a `current_user.cliente_id`
- CRUD platform: `/catalogos-globales/` — superadmin, target tenant via query param
- Tablas: `cat_*` en BD ERP del tenant

### 10.4 Brecha dashboard

Documentado en `PLATFORM_DASHBOARD_*` audits pero **sin código**. V4 debe definir BFF `/superadmin/dashboard/` antes de frontend platform v2.

---

## 11. Reglas obsoletas en `.cursorrules` y `PROMPT_BACKEND_MAESTRO.md`

### 11.1 Reglas que ya no representan el estándar actual

| Regla documentada | Realidad actual | Veredicto |
|-------------------|-----------------|-----------|
| "Orden: schemas → repositories → services → routers" | ERP usa queries, no repositories | **Actualizar** |
| "Trabaja con PROMPT_MODULO_MAESTRO_v3.md" | Archivo no referenciado en repo | **Actualizar** |
| "Implementa un bloque a la vez y confirma antes de continuar" | Fase 0 del prompt dice ejecutar completa sin parar; conflicto interno | **Actualizar** |
| "Fase 0 Paso 0.3 — DETENTE, espera confirmación" vs "ejecuta Fase 0 completa sin detenerse" | Contradicción en el mismo prompt | **Actualizar** |
| Arquitectura implícita DDD 4 capas completas | domain/infrastructure vacíos en ERP | **Actualizar** |
| `DatabaseConnection.ERP` (implícito en docs) | Solo DEFAULT + ADMIN | **Eliminar** referencias |
| "409 si no existe excepción → HTTPException 422" para duplicados | Existe `ConflictError` → 409 | **Actualizar** |
| Repository como capa estándar | Solo identidad/RBAC | **Actualizar** |
| INV usa `current_user.cliente_id`; regla genérica "validar cliente_id" | ORG usa deps más robustos | **Actualizar** con prioridad ORG |
| Paginación no especificada | Tres estilos coexisten | **Nueva regla** |
| `require_erp_session` no mencionado | Obligatorio en INV, ausente en otros ERP | **Nueva regla** |
| OrgScopePolicy no mencionado | Necesario para recursos tenant vs company | **Nueva regla** |
| Exception anti-pattern no documentado | Crítico en tenant | **Nueva regla** |
| Dual require_super_admin no documentado | Inconsistencia real | **Nueva regla** |
| Auditoría ERP opt-in no documentada | Brecha de cobertura | **Nueva regla** |
| Dashboard BFF pendiente | Documentado pero no implementado | **Nueva regla** |

### 11.2 Reglas que SÍ siguen vigentes

| Regla | Estado |
|-------|--------|
| NUNCA modificar estructura BD | ✅ Mantener |
| NUNCA eliminar código (deprecated) | ✅ Mantener |
| NUNCA asumir campos inexistentes | ✅ Mantener |
| Validar cliente_id en queries | ✅ Mantener |
| Validar empresa_id cuando tabla lo tenga | ✅ Mantener |
| RBAC `{modulo}.{recurso}.{accion}` | ✅ Mantener |
| Soft delete `es_activo = 0` | ✅ Mantener |
| Cabecera-detalle embebido | ✅ Mantener (INV lo demuestra) |
| Tablas derivadas solo lectura | ✅ Mantener |
| Endpoints incorrectos → deprecated | ✅ Mantener |
| Validators normalize_upper/lower/strip | ✅ Mantener |
| Unicidad maestros antes INSERT/UPDATE | ✅ Mantener |
| Estado transaccional → 422 | ✅ Mantener |
| NUNCA SQL Server error → 500 al cliente | ✅ Mantener (pero violado en tenant) |
| Alcance definido por BD real, no mapa ideal | ✅ Mantener |
| Corrección funcional > preservar código incorrecto | ✅ Mantener |

---

## 12. Propuestas V4

### 12.1 ERP_BACKEND_STANDARDS_V4

Documento de estándares técnicos oficiales para módulos ERP.

#### A. Arquitectura de módulo ERP

```
app/modules/{codigo}/
├── presentation/
│   ├── endpoints.py                 # Router agregador + require_erp_session
│   ├── endpoints_{entidad}.py
│   ├── schemas.py                   # Create/Update/Read + validator mixins
│   └── {codigo}_deps.py             # Si política scope != simple company
├── application/services/
│   └── {entidad}_service.py         # Funciones async *_servicio
└── (sin domain/, sin infrastructure/)

app/infrastructure/database/queries/{codigo}/
└── {entidad}_queries.py             # SQLAlchemy Core
```

#### B. Scope y sesión

1. Router padre: `dependencies=[Depends(require_erp_session)]`
2. `cliente_id`: dependency module-specific o `get_org_session_client_id` pattern
3. `empresa_id`: solo desde `require_session_empresa_id()` en services
4. Clasificar entidades: TENANT | COMPANY | HYBRID antes de codificar
5. Rechazar query/body override de scope → 403 (`SecurityError`)

#### C. Autorización

1. Cada endpoint: `Depends(require_permission("{cod}.{recurso}.{accion}"))`
2. Seeds RBAC obligatorios antes de merge
3. Platform: LBAC + RBAC dual gate en mutaciones

#### D. Persistencia

1. `DatabaseConnection.DEFAULT` + `client_id=` para ERP
2. `DatabaseConnection.ADMIN` solo platform/SaaS
3. Queries parametrizadas — prohibido SQL string concatenado con input
4. Transacciones explícitas en cabecera+detalle

#### E. API contract

1. UUID en paths
2. Paginación: `page`, `limit`, `Paginated{Entity}Response`
3. Filtros: `solo_activos`, `buscar` (SQL), filtros FK
4. Soft delete + `POST /{id}/reactivar`
5. Response models explícitos en decorators

#### F. Errores

1. Services lanzan `CustomException` subclasses
2. Endpoints: propagar o mapear — **prohibido** `except Exception → 500`
3. Mensajes `detail` en español, específicos
4. Unicidad → 409; estado inválido → 422; cross-scope → 404

#### G. Schemas

1. Validators `mode="before"` en Create/Update
2. Clasificación UPPER/LOWER/STRIP según tabla en `.cursorrules`
3. Nunca validators en Read schemas

#### H. Auditoría

1. Auth: `AuditService.registrar_auth_event`
2. ERP crítico: helper de audit en service layer (nuevo)
3. Impersonación: metadata `impersonated_by` en todos los eventos

---

### 12.2 ERP_BACKEND_RULES_V4

Reglas operativas para agentes/desarrolladores — reemplazo de `.cursorrules`.

#### Reglas absolutas

| ID | Regla | Clasificación |
|----|-------|---------------|
| R01 | NUNCA modificar estructura de BD | Mantener |
| R02 | NUNCA eliminar código — marcar `deprecated=True` | Mantener |
| R03 | NUNCA asumir campos no presentes en BD | Mantener |
| R04 | SIEMPRE filtrar `cliente_id` en queries ERP | Mantener |
| R05 | SIEMPRE filtrar `empresa_id` si columna existe | Mantener |
| R06 | SIEMPRE `require_permission` en endpoints ERP | Mantener |
| R07 | SIEMPRE soft delete via `es_activo` | Mantener |
| R08 | NUNCA SQL error → HTTP 500 al cliente | Mantener |
| R09 | Detalle embebido en cabecera — no endpoints escritura detalle | Mantener |
| R10 | Tablas derivadas — solo GET | Mantener |
| R11 | Alcance = BD real, no mapa ideal | Mantener |
| R12 | Corrección funcional > preservar endpoint incorrecto | Mantener |
| R13 | Validators UPPER/LOWER/STRIP en Create/Update | Mantener |
| R14 | Unicidad maestros: pre-check + catch UNIQUE | Mantener |
| R15 | Estado transaccional: validar antes de ciclo de vida | Mantener |
| R16 | Orden implementación: schemas → queries → services → routers | **Actualizar** (era repositories) |
| R17 | `require_erp_session` en router padre de módulos ERP operativos | **Nueva** |
| R18 | Clasificar scope TENANT/COMPANY/HYBRID por entidad | **Nueva** |
| R19 | `cliente_id` desde sesión — prohibido en body/query para authz | **Nueva** |
| R20 | Paginación estándar `page`+`limit` en listas >50 registros | **Nueva** |
| R21 | Prohibido `except Exception → HTTPException(500)` | **Nueva** |
| R22 | Usar `ConflictError` (409) — no fallback 422 para duplicados | **Actualizar** |
| R23 | Platform mutaciones: LBAC + RBAC dual gate | **Nueva** |
| R24 | Auth events via `AuditService` — obligatorio | **Nueva** |
| R25 | ERP audit helper en operaciones CRUD críticas | **Nueva** |
| R26 | `DatabaseConnection.DEFAULT` para ERP — no inventar tipo ERP | **Actualizar** |
| R27 | No crear `domain/` ni `infrastructure/` en módulos ERP nuevos | **Nueva** |
| R28 | Buscar en SQL query layer, no in-memory post-fetch | **Nueva** |
| R29 | Unificar `require_super_admin` a RBAC Depends | **Nueva** (deuda técnica) |
| R30 | Referencia módulo: ORG (scope) + INV (ERP session, transaccional) | **Actualizar** |
| R31 | "Confirma antes de continuar" en implementación automática | **Eliminar** |
| R32 | Repository pattern como capa ERP estándar | **Eliminar** |
| R33 | Referencia PROMPT_MODULO_MAESTRO_v3 | **Eliminar** |

---

### 12.3 ERP_BACKEND_MASTER_PROMPT_V4

Estructura del prompt maestro de módulo — reemplazo de `PROMPT_BACKEND_MAESTRO.md`.

#### Cambios respecto a v3

| Aspecto | v3 | v4 |
|---------|----|----|
| Referencia arquitectónica | Genérica "buscar módulo existente" | **ORG + INV explícitos** |
| Capa datos | repositories | **queries en infrastructure** |
| Fase 0 | Contradicción detener/continuar | Ejecutar 0.1→0.3 completa; **detener solo post-0.3** |
| Fase 1 referencia | Cualquier módulo | ORG (scope) + INV (transaccional) |
| Checkpoint RBAC | Inventario permisos | + verificar `require_erp_session` |
| Fase 2 | Auditoría endpoints | + auditoría exception handling + scope policy |
| Fase 3 orden | schemas → repos → services | schemas → **queries** → services → routers |
| Fase 3 gate | No mencionado | Crear `{codigo}_deps.py` si scope mixto |
| Fase 4 verificación | tenant/RBAC básico | + exception propagation test + paginación |
| Errores duplicados | "409 o 422 fallback" | Solo `ConflictError` 409 |
| Platform | No cubierto | Anexo separado `PROMPT_PLATFORM_V4.md` |

#### Fases V4 (resumen)

```
FASE 0 — Mapa ideal + BD real + contraste (detener post 0.3)
FASE 1 — Patrón ORG/INV: estructura, deps, queries (detener post 1.2)
FASE 2 — Auditoría: endpoints, scope, RBAC, exceptions, campos (detener post 2.5)
FASE 3 — Implementación: deprecated → schemas → queries → services → routers
FASE 4 — Verificación: scope, RBAC, exceptions, paginación, evidencia JSON
```

#### Anexo obligatorio por tipo de entidad

| Tipo | Operaciones | Gate |
|------|-------------|------|
| MAESTRO tenant | CRUD + desactivar + reactivar | TENANT scope |
| MAESTRO company | CRUD + desactivar + reactivar | COMPANY scope |
| TRANSACCIONAL | CRUD embebido + aprobar/procesar/anular | COMPANY + estado |
| DETALLE | Embebido — lectura opcional | N/A |
| DERIVADA | GET only | COMPANY |

---

## 13. Matriz de convergencia para módulos futuros

| Módulo | Estado actual estimado | Prioridad refactor | Referencia |
|--------|------------------------|-------------------|------------|
| **PUR** (Compras) | Mixto — algunos endpoints transaccionales, paginación propia | Alta | INV movimientos + ORG maestros |
| **SLS** (Ventas) | Legacy — detalle separado posible | Alta | INV cabecera-detalle |
| **MFG/MPS** (Producción) | Legacy — sin session gate | Alta | INV transaccional |
| **HCM** (RRHH) | Legacy — class services | Media-Alta | ORG maestros + INV scope |

### Orden de refactorización recomendado (post-estándar V4)

1. Adoptar V4 como documento oficial — **este audit**
2. Crear `{mod}_deps.py` + `require_erp_session` en router padre
3. Migrar services a funciones + queries centralizadas
4. Normalizar exception handling
5. Marcar deprecated endpoints detalle/derivados
6. Seeds RBAC
7. Paginación estándar
8. ERP audit helper en CRUD crítico

---

## 14. Deuda técnica transversal (no bloqueante para estándar, sí para calidad)

| ID | Deuda | Impacto | Acción futura |
|----|-------|---------|---------------|
| D01 | `except Exception → 500` en tenant | ConflictError → 500 | Remediar presentation tenant |
| D02 | Dual `AuthorizationError` | Confusión catch | Unificar en `CustomException` |
| D03 | Dual `require_super_admin` | Platform gate inconsistente | Migrar a RBAC Depends |
| D04 | rbac repositories sync/async | Runtime errors potenciales | Fix repositories |
| D05 | LoginUseCase no cableado | Código muerto | Eliminar o cablear |
| D06 | Dashboard BFF ausente | Frontend compone | Implementar `/superadmin/dashboard/` |
| D07 | ERP audit sin hooks | Sin trazabilidad negocio | Helper + integración gradual |
| D08 | INV client_id vs ORG deps | Impersonación edge cases | Unificar a pattern ORG |
| D09 | Paginación 3 estilos | Contrato frontend inconsistente | Migración gradual |
| D10 | Platform CRUD sin audit | Compliance gap | Eventos platform_* |

---

## 15. Documentos relacionados

| Documento | Relación |
|-----------|----------|
| `app/docs/auditoria/BACKEND_EXCEPTION_HANDLING_STANDARD_AUDIT.md` | Evidencia anti-patrón exceptions |
| `app/docs/auditoria/PLATFORM_DASHBOARD_*` | Contrato dashboard pendiente |
| `app/docs/auditoria/CLIENTES_EXCEPTION_MAPPING_AUDIT.md` | Caso origen ConflictError→500 |
| `.cursorrules` | Reglas actuales — parcialmente obsoletas |
| `docs/prompts/PROMPT_BACKEND_MAESTRO.md` | Prompt v3 — reemplazar por V4 |

---

## 16. Conclusión

El backend CAXIS ERP está en **migración activa Fase 4**. La frontera entre legacy y moderno es clara:

- **Moderno (estándar oficial):** ORG + INV — queries centralizadas, session scope robusto, RBAC string permissions, exception mapping sano, deprecated pattern para deuda.
- **Legacy (converger, no replicar):** tenant, superadmin, users, rbac — class services, SQL inline, dual LBAC/RBAC, exception anti-patterns.
- **Platform (caso especial):** Mantener class services aceptable; exigir dual gate + audit; implementar dashboard BFF.

**El estándar V4 no es teórico — ya existe en código en ORG e INV.** La refactorización de Compras, Ventas, Producción y RRHH debe ser una **expansión del patrón ORG/INV**, no una reescritura desde cero ni una copia del patrón users/rbac.

---

*Generado por auditoría arquitectónica global — 2026-06-03. Sin modificación de código de aplicación.*
