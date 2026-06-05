# CAXIS ERP — Backend Standards V4

**Versión:** 4.0  
**Fecha:** 2026-06-03  
**Estado:** Oficial — gobierna todas las refactorizaciones ERP futuras  
**Fuente:** `ERP_BACKEND_ARCHITECTURE_ALIGNMENT_AUDIT.md`  
**Referencias de código:** ORG + INV (Fase 4)

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
└── shared/validators.py
```

Routers montados desde `app/api/v1/api.py` bajo `/api/v1/{prefijo}/`.

### 2.2 Estructura oficial de módulo ERP

```
app/modules/{codigo}/
├── presentation/
│   ├── endpoints.py                  # Router agregador + require_erp_session
│   ├── endpoints_{entidad}.py        # Un archivo por entidad o grupo
│   ├── schemas.py                    # Create / Update / Read + validator mixins
│   └── {codigo}_deps.py              # Obligatorio si scope mixto TENANT/COMPANY/HYBRID
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
| **ORG** | Session scope, políticas TENANT/COMPANY/HYBRID, maestros tenant-wide | `org_deps.py`, `endpoints_empresa.py`, `empresa_service.py`, `queries/org/` |
| **INV** | `require_erp_session`, transaccionales, cabecera-detalle, derivadas | `endpoints.py`, `endpoints_movimientos.py`, `producto_service.py`, `queries/inv/` |

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

### 3.4 Prioridad de resolución (referencia ORG)

1. JWT `cliente_id` si `is_impersonation`
2. `request.state.cliente_id` (middleware)
3. ContextVar tenant
4. `current_user.cliente_id` (legacy — evitar en código nuevo)

**Estándar V4 para código nuevo:** dependency tipo `get_{codigo}_session_client_id` siguiendo patrón ORG.

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

Implementación: `{codigo}_deps.py` con enum de política (patrón `OrgScopePolicy`).

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

## 10. Paginación

### 10.1 Estándar oficial

| Parámetro | Valor |
|-----------|-------|
| `page` | Entero 1-based (default: 1) |
| `limit` | Entero (default: 20, máximo: 100) |

### 10.2 Schema de respuesta

```python
class Paginated{Entity}Response(BaseModel):
    items: list[{Entity}Read]
    total: int
    pagina_actual: int
    total_paginas: int
    limit: int
```

### 10.3 SQL Server

```sql
OFFSET :skip ROWS FETCH NEXT :limit ROWS ONLY
```

Donde `skip = (page - 1) * limit`.

### 10.4 Excepción: maestros pequeños

Listas de catálogos acotados (ORG empresas, INV categorías) pueden retornar `list[Read]` sin paginación si el volumen esperado es < 50 registros.

Listas transaccionales o históricas: **paginación obligatoria**.

### 10.5 Estilos legacy a eliminar en refactorización

| Estilo legacy | Reemplazo V4 |
|---------------|--------------|
| `skip`, `limit` | `page`, `limit` |
| `page`, `page_size` | `page`, `limit` |
| Sin paginación en listas grandes | `Paginated*Response` |

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
| **TRANSACCIONAL cabecera** | listar, detalle, crear-con-detalle, actualizar-con-detalle (borrador), aprobar, procesar, anular | COMPANY |
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

| Aspecto | Platform | ERP operativo |
|---------|----------|---------------|
| Services | Class-based aceptable | Funciones obligatorio |
| Conexión | Siempre ADMIN | Siempre DEFAULT |
| Auth | LBAC + RBAC dual gate | Solo RBAC |
| Paginación | page + limit | page + limit |

Platform debe converger en: dual gate, audit events, exception handling V4.

Dashboard BFF `/superadmin/dashboard/` — pendiente de implementación.

---

## 22. Documentos relacionados

| Documento | Rol |
|-----------|-----|
| `ERP_BACKEND_RULES_V4.md` | Reglas operativas numeradas |
| `ERP_BACKEND_MASTER_PROMPT_V4.md` | Prompt de refactorización por módulo |
| `ERP_BACKEND_ARCHITECTURE_ALIGNMENT_AUDIT.md` | Auditoría origen |
| `app/docs/auditoria/BACKEND_EXCEPTION_HANDLING_STANDARD_AUDIT.md` | Evidencia excepciones |

---

*CAXIS ERP Backend Standards V4 — Oficial — 2026-06-03*
