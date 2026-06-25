# CAXIS ERP — Backend Standards V4

**Versión:** 4.0  
**Fecha:** 2026-06-03  
**Revisión:** 2026-06-24 — patch gobernanza documental post auditoría V2 (H-01, H-02, H-03, F-01, jerarquía); rev. previa 2026-06-16 post ORG+INV session scope e impersonación consolidados (rev. previa 2026-06-15 listados P0+P1+P2-001 + INV Fase 0 RC1.1)  
**Estado:** Oficial — gobierna todas las refactorizaciones ERP futuras  
**Fuente:** `ERP_BACKEND_ARCHITECTURE_ALIGNMENT_AUDIT.md`  
**Referencias de código:** ORG + INV (transaccional + listados escalables)

---

## 1. Propósito

Este documento define el **estándar técnico oficial** del backend CAXIS ERP para módulos operativos (Compras, Ventas, Producción, RRHH, etc.).

El estándar V4 **no es teórico**: ya está implementado en los módulos **ORG** e **INV**. Toda refactorización futura debe **expandir** ese patrón, no replicar users/rbac/tenant ni DDD de cuatro capas completas.

---

## 2. Arquitectura oficial

### 2.1 Modelo: monolito modular

```
app/
├── api/                              # deps.py, deps_auth.py, v1/api.py
├── core/                             # tenant, auth, authorization, exceptions
├── infrastructure/database/
│   ├── queries/{codigo}/             # SQLAlchemy Core — capa de datos ERP
│   ├── queries_async.py              # execute_query con routing tenant
│   ├── tables/                       # tablas SaaS central
│   ├── tables_erp/                   # tablas ERP por módulo
│   └── repositories/                 # BaseRepository — SOLO identidad/RBAC
├── modules/{codigo}/
│   ├── presentation/
│   ├── application/services/
│   └── (sin domain/, sin infrastructure/)
└── shared/
    ├── validators.py
    └── pagination/                   # Infra listados escalables ORG/INV (PERF backend)
```

Routers montados desde `app/api/v1/api.py` bajo `/api/v1/{prefijo}/`.

### 2.2 Estructura oficial de módulo ERP

```
app/modules/{codigo}/
├── presentation/
│   ├── endpoints.py                  # Router agregador + require_erp_session
│   ├── endpoints_{entidad}.py        # Un archivo por entidad o grupo
│   ├── schemas.py                    # Create / Update / Read + validator mixins
│   └── {codigo}_deps.py              # Obligatorio en todo módulo ERP (resolución cliente_id); gates TENANT/COMPANY si scope mixto
├── application/services/
│   └── {entidad}_service.py          # Funciones async *_servicio
└── (prohibido: domain/, infrastructure/ por módulo)

app/infrastructure/database/queries/{codigo}/
└── {entidad}_queries.py              # SQLAlchemy Core parametrizado
```

### 2.3 Capas oficiales

| Capa | Ubicación | Responsabilidad | Convención |
|------|-----------|-----------------|------------|
| **Presentation** | `modules/{cod}/presentation/` | Routers, schemas, deps locales | `endpoints_{entidad}.py`, `schemas.py` |
| **Application** | `modules/{cod}/application/services/` | Lógica de negocio, orquestación | Funciones `async def *_servicio(...)` |
| **Queries** | `infrastructure/database/queries/{cod}/` | SQL parametrizado, filtros scope | `{entidad}_queries.py` |
| **Domain** | — | **No usar en módulos ERP nuevos** | Reservado a users/rbac/auth |
| **Repositories** | — | **No usar en módulos ERP nuevos** | Reservado a identidad/RBAC |

### 2.4 Patrones prohibidos en módulos ERP

| Patrón | Estado | Motivo |
|--------|--------|--------|
| Class-based services con staticmethods | Legacy | Usar funciones en application layer |
| Repositories por módulo ERP | Legacy | Usar queries centralizadas |
| SQL inline en presentation | Prohibido | Queries en infrastructure |
| SQL string concatenado con input | Prohibido | Solo queries parametrizadas |
| domain/entities en ERP | Prohibido | Sin valor demostrado en ORG/INV |
| Use Cases no cableados | Evitar | Orquestar en services |

### 2.5 Referencias oficiales

| Módulo | Referencia para | Archivos clave |
|--------|-----------------|----------------|
| **ORG** | Session scope, políticas TENANT/COMPANY/HYBRID, resolución `cliente_id` operativo, maestros, **listados escalables** | `org_deps.py`, `app/core/tenant/session_scope.py`, `endpoints_empresa.py`, `endpoints_parametros.py`, `parametro_service.py`, `queries/org/`, `shared/pagination/` |
| **INV** | `require_erp_session`, resolución `cliente_id` operativo (`inv_deps.py`), transaccionales, cabecera-detalle, derivadas, workflow enforcement, write policy, rutas proceso, reversión compensatoria, **listados escalables** | `inv_deps.py`, `endpoints.py`, `endpoints_movimientos.py`, `endpoints_categorias.py`, `inv_workflow_enforcement.py`, `inv_stock_write_policy.py`, `queries/inv/`, `shared/pagination/` |

---

## 3. Multi-tenant

### 3.1 Componentes

| Componente | Archivo | Función |
|------------|---------|---------|
| `TenantContext` | `app/core/tenant/context.py` | ContextVar: cliente_id, subdominio, database_type |
| `TenantMiddleware` | `app/core/tenant/middleware.py` | Resuelve tenant por subdominio vía ADMIN |
| `get_current_client_id()` | `context.py` | Lectura del contexto activo |
| Routing | `app/core/tenant/routing.py` | Resolución de conexión por tenant |

### 3.2 Flujo de request

```
Request → TenantMiddleware → lookup cliente (ADMIN) → set TenantContext → endpoint → reset
```

### 3.3 Reglas de `cliente_id`

| Regla | Detalle |
|-------|---------|
| Toda query ERP filtra `cliente_id` | Obligatorio en capa queries |
| Prohibido body/query para autorización | Usar `reject_legacy_cliente_query` |
| Impersonación usa tenant del JWT | No el cliente SYSTEM del operador |
| Platform opera sin tenant | `client_id=None` explícito con ADMIN |

### 3.4 Prioridad de resolución (referencia ORG + INV — `session_scope.py`)

Implementación canónica: `require_session_cliente_id` en `app/core/tenant/session_scope.py`, invocada desde `get_{codigo}_session_client_id` en `{codigo}_deps.py` (patrones: `org_deps.py`, `inv_deps.py`).

Orden de prioridad para el **contexto operativo de datos**:

1. JWT `cliente_id` si `is_impersonation` (tenant impersonado)
2. `request.state.cliente_id` (si el middleware lo poblara explícitamente)
3. ContextVar tenant (`TenantMiddleware` → `get_current_client_id()`)
4. `current_user.cliente_id` (legacy — **prohibido** en presentation para operaciones de datos ERP; ver §3.7)

**Estándar V4 para código nuevo:** dependency `get_{codigo}_session_client_id` en `{codigo}_deps.py` — obligatoria en **todo** módulo ERP operativo, no solo scope mixto.

### 3.5 Tenant SYSTEM (platform)

- Cliente reservado: `SUPERADMIN_CLIENTE_ID` / subdominio `platform`
- Usuario platform: `user_type=platform_admin`, `access_level=5`
- Operaciones cross-tenant: solo LBAC level 5, auditadas via `AuditService.registrar_tenant_access`

### 3.6 Impersonación

| Aspecto | Comportamiento |
|---------|----------------|
| Inicio | `POST /auth/impersonate/{cliente_id}/` |
| Token | 120 min, sin refresh; claims `is_impersonation`, `impersonated_by` |
| Privilegios platform | Suprimidos (`suppress_platform_privileges`) |
| RBAC efectivo | Rol ADMIN_TENANT filtrado por `cliente_modulo` |
| Sesión padre | Redis — restauración en `/impersonate/end/` |
| Anidación | Prohibida (409) |

### 3.7 Identidad autenticada vs contexto operativo ERP

Durante impersonación (y en general en sesión ERP), existen **dos contextos distintos** que no deben confundirse:

| Concepto | Fuente | Uso |
|----------|--------|-----|
| **Identidad autenticada** | `current_user` (JWT + `build_user_with_roles`) | Auditoría de operador, metadatos de sesión, claims de impersonación |
| **Contexto operativo ERP** | `get_{codigo}_session_client_id` → `require_session_cliente_id` | Filtros `cliente_id` en queries, autorización de datos por tenant |

**Regla:** Para consultas y mutaciones ERP sobre datos de tenant, el `cliente_id` operativo **nunca** se obtiene directamente de `current_user.cliente_id` en presentation.

**Motivo (impersonación):** En impersonación, `current_user.cliente_id` puede apuntar al cliente **SYSTEM** del operador platform, mientras el JWT incluye el `cliente_id` del tenant impersonado. ORG ya resolvía correctamente vía `get_org_session_client_id`; INV y listados RBAC fueron alineados al mismo patrón (`inv_deps.py`, `rbac_deps.py`).

**Anti-patrón explícito (presentation):**

```python
# PROHIBIDO para operaciones de datos ERP
client_id = current_user.cliente_id
```

**Patrón correcto (presentation):**

```python
client_id: UUID = Depends(get_{codigo}_session_client_id)
```

**RBAC durante impersonación:** La autorización efectiva (permisos, menú) puede resolverse por ramas específicas de impersonación (ContextVar / claims). Eso **no sustituye** la resolución de `cliente_id` para datos — ambas vías son independientes. Ver §6.4.

**Referencia cruzada:** Reglas ejecutables R19, R22–R25, R110–R112 en `ERP_BACKEND_RULES_V4.md`; implementación §5.5.

---

## 4. Multiempresa

### 4.1 Componentes

| Componente | Archivo | Función |
|------------|---------|---------|
| JWT claim `empresa_id` | `app/core/security/jwt.py` | Empresa seleccionada post-login |
| `empresa_context` | `app/core/tenant/empresa_context.py` | ContextVar poblado en deps |
| `require_session_empresa_id()` | `app/core/tenant/company_scope.py` | 403 si no hay empresa activa |
| Login multi-paso | `auth_service.py` | `empresa_selection_pending` → token temporal |

### 4.2 Flujo de contexto empresa

```
JWT empresa_id → deps.set_current_empresa_id → ContextVar → service.require_session_empresa_id()
```

### 4.3 Reglas de `empresa_id`

| Regla | Detalle |
|-------|---------|
| Tablas con columna `empresa_id` | Filtro obligatorio en queries |
| Body no puede override sesión | `enforce_body_empresa_matches_session` |
| Cross-company | Responder **404**, no 403 (`assert_row_empresa`) |
| RBAC por empresa | Roles globales (`empresa_id IS NULL`) o scoped por empresa |

---

## 5. Session scope

### 5.1 Gate ERP obligatorio: `require_erp_session`

Ubicación: `app/api/deps_auth.py`

Aplicación: **router padre** del módulo ERP:

```python
router = APIRouter(dependencies=[Depends(require_erp_session)])
```

Comportamiento:

- Rechaza `empresa_selection_pending` (salvo impersonación documentada)
- Exige `empresa_id` en JWT para usuarios operativos
- Referencia: `app/modules/inv/presentation/endpoints.py`

### 5.2 Políticas de scope por entidad

Clasificar **cada entidad** antes de implementar:

| Política | Significado | Gate | Ejemplo ORG |
|----------|-------------|------|-------------|
| **TENANT** | Datos del cliente, no requieren empresa activa | `require_org_tenant_erp_session` | Empresa |
| **COMPANY** | Datos de la empresa activa en sesión | `require_org_company_erp_session` | Departamento, cargo |
| **HYBRID** | Según operación específica | Evaluar por endpoint | Centro de costo |

Implementación scope mixto: `{codigo}_deps.py` con enum de política (patrón `OrgScopePolicy`). Resolución `cliente_id` operativo: siempre en `{codigo}_deps.py` — ver §5.5.

### 5.3 Rechazo de scope legacy

| Helper | Acción |
|--------|--------|
| `reject_legacy_cliente_query` | Query param `cliente_id` oculto → 403 |
| `reject_legacy_empresa_query` | Query param `empresa_id` oculto → 403 |
| `reject_client_empresa_scope_override` | Body override → 403 (`SecurityError`) |

### 5.4 Aislamiento en services

```python
# Company-scoped (referencia INV)
empresa_id = require_session_empresa_id()
enforce_body_empresa_matches_session(data.empresa_id)
```

### 5.5 Resolución operativa de `cliente_id` — patrón oficial ORG + INV

Todo módulo ERP operativo (PUR, SLS, FIN, CRM, HCM, etc.) debe replicar el patrón validado en **ORG** e **INV**.

#### Componentes

| Componente | Ubicación | Función |
|------------|-----------|---------|
| `require_session_cliente_id` | `app/core/tenant/session_scope.py` | Resuelve `cliente_id` operativo con prioridad §3.4 |
| `get_{codigo}_session_client_id` | `modules/{codigo}/presentation/{codigo}_deps.py` | Dependency FastAPI por módulo; delega en `require_session_cliente_id` |
| `get_org_session_client_id` | `modules/org/presentation/org_deps.py` | Referencia TENANT/COMPANY gates + resolución cliente |
| `get_inv_session_client_id` | `modules/inv/presentation/inv_deps.py` | Referencia módulo transaccional company-scoped |
| `get_rbac_session_client_id` | `modules/rbac/presentation/rbac_deps.py` | Referencia listados RBAC bajo impersonación |

#### Esqueleto canónico (`{codigo}_deps.py`)

```python
async def get_{codigo}_session_client_id(
    request: Request,
    payload: dict = Depends(get_token_payload),
    current_user: User = Depends(get_current_active_user),
) -> UUID:
    return require_session_cliente_id(
        payload=payload,
        user_cliente_id=getattr(current_user, "cliente_id", None),
        request_cliente_id=_request_cliente_id(request),
        endpoint=_endpoint_label(request),
    )
```

Ajustar imports según módulo; la lógica de prioridad vive **solo** en `session_scope.py`.

#### Obligatoriedad de `{codigo}_deps.py`

| Escenario | `{codigo}_deps.py` |
|-----------|-------------------|
| Cualquier módulo ERP operativo | **Obligatorio** — al menos `get_{codigo}_session_client_id` |
| Scope mixto TENANT / COMPANY / HYBRID | Además: enum de política + gates (patrón `OrgScopePolicy` en ORG) |

INV demostró que incluso módulos **solo COMPANY-scoped** requieren `{codigo}_deps.py` para impersonación correcta; no es exclusivo de scope mixto.

#### Uso en endpoints

```python
@router.get("/")
async def listar(
    client_id: UUID = Depends(get_{codigo}_session_client_id),
    ...
):
    return await listar_servicio(client_id=client_id, ...)
```

Services reciben `client_id` como parámetro explícito desde presentation; **no** leen `current_user.cliente_id`.

#### Anti-patrones

| Anti-patrón | Consecuencia | Acción |
|-------------|--------------|--------|
| `current_user.cliente_id` en presentation para datos | Listados vacíos / datos del tenant SYSTEM en impersonación | Reemplazar por `Depends(get_{codigo}_session_client_id)` |
| `cliente_id` en query/body para autorización | Bypass de scope | `reject_legacy_cliente_query` + R19 |
| Duplicar lógica de prioridad impersonación en cada módulo | Deriva inconsistente | Centralizar en `require_session_cliente_id` |

**Referencia cruzada:** §3.7 (identidad vs operativo), `ERP_BACKEND_RULES_V4.md` R23–R25, R110–R112, `ERP_BACKEND_MASTER_PROMPT_V4.md` Fase 1.2–1.3 y Paso 2.5.

---

## 6. RBAC

### 6.1 Patrón de permiso

```
{modulo}.{recurso}.{accion}
```

Ejemplos: `inv.producto.crear`, `org.empresa.leer`, `pur.orden_compra.aprobar`

### 6.2 Aplicación en endpoints

```python
current_user: UsuarioReadWithRoles = Depends(require_permission("inv.producto.leer"))
```

### 6.3 Resolución de permisos

```
usuario_rol → rol_permiso → permiso
```

Filtrado por módulos suscritos (`cliente_modulo` lookup en ADMIN).

### 6.4 Reglas

| Regla | Detalle |
|-------|---------|
| Cada endpoint ERP | `require_permission` obligatorio |
| Super admin | Bypass total **excepto** durante impersonación |
| Impersonación — RBAC vs datos | RBAC efectivo puede resolverse por rama impersonation (ContextVar/claims); **independiente** de `cliente_id` operativo para queries — ver §3.7 |
| Listados RBAC bajo impersonación | Usar `get_rbac_session_client_id` (referencia `rbac_deps.py`), no `current_user.cliente_id` |
| Seeds RBAC | Obligatorios antes de merge de refactorización |
| Code-first | `RequirePermission(PermissionMetadata(...))` permitido en startup |

### 6.5 Permisos por operación estándar

| Operación | Acción RBAC |
|-----------|-------------|
| Listar / detalle | `leer` |
| Crear | `crear` |
| Actualizar | `actualizar` |
| Desactivar (DELETE) | `eliminar` |
| Reactivar | `actualizar` (no `eliminar`) |
| Aprobar / procesar / anular | `{accion_especifica}` |
| Estornar / finalizar (ciclo de vida) | `{accion_especifica}` — nunca reutilizar solo `actualizar` |

---

## 7. LBAC

### 7.1 Niveles de acceso

| Nivel | Rol típico | Gate |
|-------|------------|------|
| 5 | SuperAdministrador / platform_admin | `require_super_admin()` |
| 4 | AdministradorTenant | `require_tenant_admin()` |
| 1–3 | Usuario operativo | `RoleChecker` en deps |

### 7.2 Ámbito de aplicación

LBAC aplica a **Platform Administration**, no a módulos ERP operativos.

Módulos ERP operativos usan exclusivamente **RBAC** (`require_permission`).

### 7.3 Dual gate platform (mutaciones)

Combinar LBAC + RBAC en operaciones platform:

```python
@require_super_admin()
async def crear_cliente(
    ...,
    _: User = Depends(require_permission("tenant.cliente.crear")),
):
```

Referencia: `endpoints_clientes.py`, `endpoints_conexiones.py`

### 7.4 Deuda documentada

Existen dos implementaciones de `require_super_admin` (LBAC decorator vs RBAC Depends). Código nuevo platform debe preferir **RBAC Depends**. Unificación planificada como deuda técnica D03.

---

## 8. Auditoría

### 8.1 Dos capas

| Capa | Tabla | Writer | Ámbito |
|------|-------|--------|--------|
| **Auth/Security** | `auth_audit_log` | `AuditService.registrar_auth_event` | Login, logout, refresh, impersonación, cross-tenant |
| **ERP Business** | `aud_log_auditoria` | Helper en service layer | Mutaciones CRUD críticas |

### 8.2 Estándares obligatorios V4

| Evento | Acción |
|--------|--------|
| Auth events | Siempre `AuditService.registrar_auth_event` — no negociable |
| ERP mutations críticas | Helper `registrar_auditoria_erp(modulo, tabla, accion, ...)` en services |
| Platform CRUD | Eventos `platform_{recurso}_{accion}` en `auth_audit_log` |
| Impersonación | Incluir `impersonated_by` en metadata de todo evento durante sesión impersonada |

### 8.3 Routing de auth audit

| Tipo tenant | Conexión |
|-------------|----------|
| Shared DB | `DatabaseConnection.ADMIN` |
| Dedicated DB | `DatabaseConnection.DEFAULT` |

**Fail-safe:** errores de audit nunca rompen flujo de negocio.

### 8.4 Reader platform

`SuperadminAuditoriaService` — `/api/v1/superadmin/auditoria/`

### 8.5 Auditoría usuario en mutaciones ERP (company-scoped)

| Campo | Origen | Regla |
|-------|--------|-------|
| `usuario_creacion_id` | Sesión (`usuario_id` del JWT) | Asignar en CREATE; ignorar valor del body |
| `usuario_actualizacion_id` | Sesión | Asignar en UPDATE cuando hay usuario activo |

Patrón: helper `{mod}_audit_context.py` con `apply_create_audit` / `apply_update_audit`.  
Referencia: `app/modules/inv/application/services/inv_audit_context.py` (INV-P0-004).

---

## 9. Soft delete

### 9.1 Patrón oficial

| Operación | Implementación |
|-----------|----------------|
| Desactivar | `DELETE /{id}` → `es_activo = False` |
| Reactivar | `POST /{id}/reactivar` → `es_activo = True` |
| Listados | `solo_activos: bool = True` por defecto |
| Permiso reactivar | RBAC `actualizar` |

### 9.2 Prohibiciones

- DELETE físico de registros
- Columnas `deleted_at` / tombstone (no existen en el modelo actual)
- Permiso `eliminar` para reactivar

### 9.3 Referencias

- ORG: `POST /{id}/reactivar` en cargos, departamentos
- INV: `POST /{id}/reactivar` en productos, categorías

---

## 10. Listados escalables (contrato v1)

Implementado y validado en ORG/INV. Estrategia PERF backend cerrada (paginación + búsqueda SQL + sort server-side).

### 10.1 Infraestructura compartida

Ubicación: `app/shared/pagination/`

| Archivo | Responsabilidad |
|---------|-----------------|
| `params.py` | `ErpPaginationParams`, `erp_pagination_params()` |
| `sort.py` | `ErpSortParams`, `erp_sort_params()` |
| `schemas.py` | `ErpPaginatedResponse[T]` |
| `builder.py` | `build_paginated_response()`, `calc_total_paginas()` |
| `query_helpers.py` | `apply_erp_pagination()`, `apply_erp_sort()`, `apply_memory_sort()` |

### 10.2 Paginación opt-in

| Parámetro | Valor |
|-----------|-------|
| `page` | Entero 1-based, **opcional**. Si ausente → modo legacy `list[Read]` |
| `limit` | Entero (default: **50**, máximo: 100). **Solo aplica con `page`**; sin `page` se ignora |

**Modos de respuesta:**

| Condición | Response |
|-----------|----------|
| Sin `page` | `list[{Entity}Read]` |
| Con `page` | `Paginated{Entity}Response` (extiende `ErpPaginatedResponse`) |

Endpoints que exponen `page` deben usar `response_model=Union[list[Read], Paginated{Entity}Response]`.

### 10.3 Schema de respuesta paginada

```python
class ErpPaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    pagina_actual: int
    total_paginas: int
    limit: int

class Paginated{Entity}Response(ErpPaginatedResponse[{Entity}Read]):
    pass
```

### 10.4 SQL Server

```sql
OFFSET :skip ROWS FETCH NEXT :limit ROWS ONLY
```

Donde `skip = (page - 1) * limit` (variable interna). Aplicar **solo** cuando `page` está presente.  
`ORDER BY` debe ejecutarse **antes** de `OFFSET/FETCH`.

### 10.5 Búsqueda `buscar`

| Regla | Valor |
|-------|-------|
| Implementación | SQL `ILIKE`/`LIKE` en capa queries |
| Prohibido | Filtrar in-memory post-fetch (salvo caso híbrido documentado) |
| Compatibilidad | Funciona con y sin `page` |

### 10.6 Ordenamiento server-side (`sort_by` / `sort_dir`)

| Parámetro | Valor |
|-----------|-------|
| `sort_by` | Opcional. Columna de whitelist definida por recurso |
| `sort_dir` | Opcional: `asc` \| `desc`. Solo aplica con `sort_by` |
| Sin `sort_by` | Conservar `ORDER BY` fijo preexistente del recurso |
| `sort_by` inválido | `CustomException` 422, `internal_code=INVALID_SORT_COLUMN` |
| Tie-breaker | PK del recurso como segundo criterio (orden estable entre páginas) |

**Caso especial HYBRID:** `GET /org/parametros` — sort post-merge (`apply_memory_sort`) tras precedencia, antes del slice paginado.

**Nota PUR:** módulos legacy (ej. PUR) pueden usar `order`; ORG/INV v1 usan `sort_dir`. No unificar sin auditoría explícita.

### 10.7 Perfiles de listado por volumen

| Perfil | Recursos referencia | page/limit | response_model | buscar | sort |
|--------|---------------------|------------|----------------|--------|------|
| **Tier A** — volumen bajo | ORG: empresa, sucursales, departamentos, cargos | No expuesto | `list[Read]` | ✅ SQL | ✅ |
| **Tier B** — escalable opt-in | ORG: centros-costo, parámetros; INV: categorías, productos, maestros P1 | Opt-in con `page` | `Union[list, Paginated*]` | ✅ | ✅ |
| **Tier C** — transaccional/histórico | INV: movimientos, kardex, stock, inventario-fisico | Opt-in recomendado | `Union[list, Paginated*]` | Filtros recurso | ✅ |

### 10.8 Estilos legacy a eliminar en refactorización

| Estilo legacy | Reemplazo V4 |
|---------------|--------------|
| `skip`, `limit` (query params API) | `page`, `limit` |
| `page`, `page_size` | `page`, `limit` |
| Paginación siempre activa | Paginación opt-in con `page` |
| `limit` default 20 | `limit` default **50** (con `page`) |
| Sort in-memory en listas paginadas | `sort_by`/`sort_dir` server-side |
| PUR `order` | ORG/INV usan `sort_dir` (no unificar sin auditoría) |

### 10.9 Metadatos de paginación extendidos (futuro)

`has_next` y `has_prev` **no están implementados** en contrato v1 (P0–P2). Reservados para evolución futura.  
El frontend debe derivar navegación de `pagina_actual`, `total_paginas` y `total`.

---

## 11. UUID

### 11.1 Reglas

- IDs expuestos como **UUID v4** en paths y schemas
- Path params: `{entidad}_id: UUID`
- Coerción defensiva en scope helpers
- Handler global mejora mensajes 422 para UUID inválido

### 11.2 Prohibiciones

- IDs numéricos autoincrementales expuestos en API
- Strings libres como identificadores de entidad

---

## 12. Errores HTTP

### 12.1 Jerarquía canónica

Archivo: `app/core/exceptions.py`

| Excepción | HTTP | Uso |
|-----------|------|-----|
| `ValidationError` | 400 | Entrada / regla de formato |
| `AuthenticationError` | 401 | Token / credenciales |
| `AuthorizationError` | 403 | Permisos / sesión incompleta |
| `NotFoundError` | 404 | Recurso inexistente (incl. cross-scope) |
| `ConflictError` | 409 | Duplicados / unicidad |
| `CustomException` (`INVALID_SORT_COLUMN`) | 422 | `sort_by` inválido en listado |
| `DatabaseError` | 500 | Errores de BD |
| `ServiceError` | 500 | Fallos de servicio |

Handler global retorna: `{ "detail": "...", "error_code": "..." }`

En producción: detalles 5xx enmascarados.

### 12.2 Patrones en presentation

**Preferido — propagar al handler global:**

```python
# Sin try/except — CustomException llega al handler
return await entidad_service.get_servicio(...)
```

**Aceptado — mapeo explícito:**

```python
except (NotFoundError, ConflictError, CustomException) as e:
    raise HTTPException(status_code=e.status_code, detail=e.detail) from e
```

**Prohibido:**

```python
except Exception:
    raise HTTPException(status_code=500, detail="Error interno")
```

### 12.3 Reglas por tipo de entidad

| Tipo | Regla de error |
|------|----------------|
| **Maestros — unicidad** | Pre-check SELECT + catch SQL UNIQUE → `ConflictError` 409. Mensaje: `"Ya existe [entidad] con [campo] '[valor]' en este tenant."` |
| **Transaccionales — estado** | Verificar estado antes de aprobar/procesar/anular → 422. Mensaje: `"Esta operación solo está permitida en estado [requerido]. Estado actual: [actual]."` |
| **Transaccionales — terminal / doble operación** | `ConflictError` 409 (ej. ya revertido, escritura derivada bloqueada, doble estorno) |
| **Cross-scope** | 404 (no revelar existencia en otro tenant/empresa) |
| **SQL Server** | Nunca exponer error SQL al cliente como 500 genérico sin mapear |

### 12.4 Mensajes

- Siempre en **español**
- Siempre **específicos** (entidad, campo, valor, estado)
- Campo `detail` siempre string

---

## 13. Cabecera-detalle

### 13.1 Regla fundamental

Las tablas detalle **nunca** se operan de forma independiente desde el frontend.

Identificación:

- FK obligatoria hacia cabecera
- Nombre suele incluir `_detalle`
- Semánticamente: no tiene sentido crear detalle sin cabecera

### 13.2 Patrón correcto

| Operación | Implementación |
|-----------|----------------|
| Crear | `POST /cabeceras` con `List[DetalleCreate]` embebido en body |
| Actualizar | `PUT /cabeceras/{id}` con detalle embebido (solo en borrador) |
| Leer detalle | `GET /cabeceras/{id}/detalle` — permitido |
| Escritura detalle standalone | **DEPRECATED** — `deprecated=True` |

### 13.3 Schemas

```python
class CabeceraCreate(BaseModel):
    ...
    detalles: list[DetalleCreate]          # Obligatorio en create

class CabeceraUpdate(BaseModel):
    ...
    detalles: list[DetalleUpdate] | None   # Opcional en update

class CabeceraRead(BaseModel):
    ...
    detalles: list[DetalleRead]
```

### 13.4 Transacciones

Operaciones cabecera + detalle: transacción SQL explícita (BEGIN/COMMIT/ROLLBACK) en service layer.

### 13.5 Referencia INV

| Endpoint | Estado |
|----------|--------|
| `POST /inv/movimientos` con `MovimientoConDetalleCreate` | ✅ Correcto |
| `PUT /inv/movimientos/{id}` con detalle embebido | ✅ Correcto |
| `POST /inv/movimientos-detalle` | 🔴 Deprecated |
| `PUT /inv/movimientos-detalle/{id}` | 🔴 Deprecated |

### 13.6 Workflow transaccional — enforcement en servicio

| Operación | Regla |
|-----------|-------|
| CREATE cabecera transaccional | Forzar estado inicial del dominio; eliminar campos de proceso del payload |
| UPDATE cabecera | Rechazar `estado` y campos de proceso → 422 |
| Procesar / autorizar idempotente | Detectar estados fantasma sin evidencia → 409 |
| Terminales | Bloquear transiciones inválidas según máquina de estados del dominio |

La restricción es **obligatoria en service layer**. Readonly solo en schema OpenAPI no es suficiente.  
Referencia: `inv_workflow_enforcement.py` (INV-P0-006).

### 13.7 Reversión post-proceso (patrón compensatorio)

Aplicable cuando una operación ya aplicó efectos colaterales y no puede corregirse con anulación pre-efecto:

1. Diferenciar semánticamente **anulación previa al efecto** vs **reversión posterior al efecto** (nombres de estado a criterio del dominio; INV usa `estornado` solo como ejemplo de implementación).
2. Crear documento compensatorio espejo.
3. Ejecutar el pipeline de proceso canónico (`procesar_*_servicio(..., uow=...)`) dentro de la **misma UoW**.
4. Marcar el original en estado terminal de reversión del dominio.
5. Trazabilidad: `documento_referencia_tipo` + `documento_referencia_id`.
6. Procesos concurrentes: locking apropiado para la persistencia (ej. SQL Server INV: `WITH (UPDLOCK, ROWLOCK)` en cabecera original).

Referencia implementación: INV-P0-003. Reglas espejo por `clase_movimiento` → dominio INV (`inv_estorno_proceso.py`).

---

## 14. Tablas derivadas

### 14.1 Identificación

- Columnas calculadas persistidas (`AS ... PERSISTED` en SQL Server)
- Descripción indica "snapshot" o "estado actual"
- Contenido actualizado por procesos del sistema, no por el usuario

### 14.2 Patrón correcto

| Operación | Estado |
|-----------|--------|
| GET (listar / detalle) | ✅ Permitido |
| POST / PUT / DELETE directo | 🔴 Deprecated |
| Escritura | Solo internamente desde services de otros procesos |

### 14.3 Referencia INV

| Tabla / Endpoint | Estado |
|------------------|--------|
| `inv_stock` — GET | ✅ Correcto |
| `POST /inv/stock` | 🔴 Deprecated |
| `PUT /inv/stock/{id}` | 🔴 Deprecated |

### 14.4 Política de escritura sobre tablas derivadas

| Capa | Responsabilidad |
|------|-----------------|
| OpenAPI | POST/PUT marcados `deprecated=True` |
| Service | `assert_*_direct_write_allowed()` → `ConflictError` 409 por defecto |
| Config ops | Flag env explícito (`false` en producción) para bypass temporal |
| Pipeline canónico | Único mutador operativo: proceso transaccional interno |

Referencia: `inv_stock_write_policy.py`, `stock_service.py` (INV-P0-002). Costeo al procesar cuando el dominio lo requiera: helpers dedicados en service layer (INV-P0-001/005: `inv_costeo_proceso.py`).

---

## 15. Conexiones ADMIN vs DEFAULT

### 15.1 Enum oficial

```python
class DatabaseConnection(Enum):
    DEFAULT = "default"   # Tenant-aware (ERP operacional)
    ADMIN = "admin"       # BD central SaaS
```

**No existe `DatabaseConnection.ERP`.** "ERP" es concepto: datos operacionales vía `DEFAULT`.

### 15.2 Reglas de uso

| Conexión | Destino | Tablas / operaciones |
|----------|---------|----------------------|
| **ADMIN** | BD central (`DB_ADMIN_*`) | `cliente`, `cliente_conexion`, `cliente_modulo`, `modulo`, seeds, auth config |
| **DEFAULT** | Shared o BD dedicada tenant | `org_*`, `inv_*`, `usuario`, `rol`, ERP completo |

### 15.3 Routing DEFAULT

```
execute_query(..., client_id=UUID)
  → get_connection_for_tenant(cliente_id)
      ├── database_type = "single" → BD compartida
      └── database_type = "multi"  → credenciales cliente_conexion
```

### 15.4 Casos híbridos

| Operación | Conexión |
|-----------|----------|
| `auth_audit_log` tenant shared | ADMIN |
| `auth_audit_log` tenant dedicado | DEFAULT |
| Permisos suscritos (`cliente_modulo`) | ADMIN |
| Permisos efectivos (`usuario_rol`) | DEFAULT |
| TenantMiddleware lookup | ADMIN |
| Queries ERP (`org_*`, `inv_*`, `{cod}_*`) | DEFAULT + `client_id=` |

### 15.5 Prohibiciones

- Usar ADMIN para datos ERP operacionales
- Omitir `client_id=` en queries DEFAULT
- Inventar un tercer tipo de conexión

---

## 16. Schemas y validators

### 16.1 Transformación de texto

Archivo: `app/shared/validators.py`

Funciones: `normalize_upper`, `normalize_lower`, `normalize_strip`

| Tipo de campo | Función | Campos típicos |
|---------------|---------|----------------|
| Código interno | `normalize_upper` | codigo, codigo_* |
| Dato legal/tributario | `normalize_upper` | ruc, dni, razon_social, ubigeo |
| Email | `normalize_lower` | email, *_email |
| URL / subdominio | `normalize_lower` | subdominio, *_url |
| Nombre libre | `normalize_strip` | nombre_comercial, contacto_nombre |
| Texto largo | `normalize_strip` | observaciones, descripcion, notas |

### 16.2 Aplicación

- Solo en schemas **Create** y **Update**
- `@field_validator(..., mode="before")` — mode="before" obligatorio
- Mixins siguiendo patrón `app/modules/org/presentation/schemas.py`
- Nunca en schemas Read

---

## 17. Endpoints estándar por tipo de entidad

| Tipo | Operaciones | Scope |
|------|-------------|-------|
| **MAESTRO tenant** | listar, detalle, crear, actualizar, DELETE (soft), reactivar | TENANT |
| **MAESTRO company** | listar, detalle, crear, actualizar, DELETE (soft), reactivar | COMPANY |
| **TRANSACCIONAL cabecera** | listar, detalle, crear-con-detalle, actualizar-con-detalle (borrador), aprobar, procesar, anular, estornar/reversar (si aplica) | COMPANY |
| **DETALLE embebido** | lectura opcional bajo cabecera | N/A |
| **DERIVADA** | listar, detalle (solo GET) | COMPANY |

### 17.1 Rutas CRUD estándar

```
GET    ""                    → listar
GET    "/{id}"               → detalle
POST   ""                    → crear
PUT    "/{id}"               → actualizar
DELETE "/{id}"               → desactivar (soft delete)
POST   "/{id}/reactivar"     → reactivar
```

### 17.2 Rutas de proceso transaccional (canónicas)

Montaje obligatorio bajo el router del recurso transaccional:

```
POST /{prefijo_modulo}/{recurso}/{id}/procesar
POST /{prefijo_modulo}/{recurso}/{id}/autorizar
POST /{prefijo_modulo}/{recurso}/{id}/anular
POST /{prefijo_modulo}/{recurso}/{id}/estornar    # si el dominio soporta reversión post-proceso
POST /{prefijo_modulo}/{recurso}/{id}/aprobar     # si aplica
POST /{prefijo_modulo}/{recurso}/{id}/finalizar   # si aplica
```

**Prohibido** montar acciones de proceso en la raíz del módulo (`/{id}/procesar`).

#### Período alias (migración sin breaking change — RC1.1)

Cuando existan rutas legacy incorrectas, publicar ambas sin duplicar handlers:

```python
# Canónico (preferido para Frontend y OpenAPI nuevo)
router.include_router(proceso_router, prefix="/{recurso}", tags=["..."])
# Legacy temporal (misma instancia de router — mismos handlers)
router.include_router(proceso_router, tags=["..."])
```

Reglas del alias:

- Mismos handlers, mismos servicios, mismos permisos RBAC, mismos schemas y códigos HTTP.
- Sin `deprecated=True` en el período alias salvo decisión explícita de cierre.
- Validar OpenAPI: cada ruta genera `operationId` único (FastAPI ≥ 0.100 incorpora el path completo).
- Deprecar rutas legacy solo tras migración confirmada del consumidor Frontend.

Referencia: INV RC1.1 — `endpoints.py` doble `include_router` de `movimientos_proceso_router`.

---

## 18. Evaluación de contratos existentes

Los endpoints existentes **no** son automáticamente correctos.

Evaluar antes de proteger:

1. ¿Tiene sentido funcional para ERP SaaS?
2. ¿Es tabla detalle que debería estar embebida en cabecera?
3. ¿Es escritura sobre tabla derivada/analítica?

Si cualquiera → marcar **DEPRECATED**:

- Agregar `deprecated=True` en decorator
- NO modificar lógica interna
- NO cambiar ruta ni response_model
- Documentar en auditoría del módulo
- Frontend NO debe consumir

---

## 19. Orden de prioridad en conflictos

1. Integridad de datos (tenant, transacciones)
2. Corrección funcional del módulo ERP
3. Compatibilidad con contratos existentes correctos
4. Preservación de código existente

Si preservar código incorrecto entra en conflicto con corrección funcional → **corrección funcional gana** → código incorrecto se marca DEPRECATED.

---

## 20. Alcance de implementación

El alcance lo define la **BD real**, no el mapa funcional ideal.

- Entidad en mapa ideal que NO existe en BD → ignorar completamente
- No crear tablas, no sugerir migraciones
- Tablas en BD no anticipadas → clasificar según tipo (maestro, detalle, derivada)

---

## 21. Platform Administration (caso especial)

Los módulos platform (tenant, superadmin, modulos) **no siguen** la estructura ERP V4 completa.

Los módulos **auth/IAM** (`app/modules/auth/`) **no siguen** el checklist ERP operativo completo de este documento. Su documentación normativa reside en `docs/arquitectura/IAM-*`.

| Aspecto | Platform | ERP operativo |
|---------|----------|---------------|
| Services | Class-based aceptable | Funciones obligatorio |
| Conexión | Siempre ADMIN | Siempre DEFAULT |
| Auth | LBAC + RBAC dual gate | Solo RBAC |
| Paginación | page + limit | page + limit (ERP: opt-in con `page`) |

Platform debe converger en: dual gate, audit events, exception handling V4.

Dashboard BFF `/superadmin/dashboard/` — pendiente de implementación.

---

## 22. Documentos relacionados

### 22.1 Jerarquía documental oficial

Cadena normativa (mayor → menor autoridad):

1. `ERP_BACKEND_STANDARDS_V4.md` — norma técnica (este documento)
2. `ERP_BACKEND_RULES_V4.md` — reglas ejecutables R01–R112
3. `.cursorrules` — resumen operativo Cursor
4. `docs/prompts/PROMPT_BACKEND_MAESTRO.md` — punto de entrada operativo
5. `app/docs/arquitectura/ERP_BACKEND_MASTER_PROMPT_V4.md` — proceso de refactorización por módulo

### 22.2 Documentos de soporte

| Documento | Rol |
|-----------|-----|
| `ERP_BACKEND_RULES_V4.md` | Reglas operativas numeradas |
| `ERP_BACKEND_MASTER_PROMPT_V4.md` | Prompt de refactorización por módulo |
| `ERP_BACKEND_ARCHITECTURE_ALIGNMENT_AUDIT.md` | Auditoría origen |
| `app/docs/auditoria/BACKEND_EXCEPTION_HANDLING_STANDARD_AUDIT.md` | Evidencia excepciones |
| `app/docs/auditoria/P0_P1_P2_ORG_INV_LISTADOS_FINAL_AUDIT.md` | Evidencia listados ORG/INV |

---

*CAXIS ERP Backend Standards V4 — Oficial — 2026-06-03 (rev. 2026-06-24 patch gobernanza documental post auditoría V2; rev. previa 2026-06-16 post ORG+INV session scope e impersonación)*
