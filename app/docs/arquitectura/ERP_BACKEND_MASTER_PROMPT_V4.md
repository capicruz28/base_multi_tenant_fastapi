# CAXIS ERP — Prompt Maestro V4

**Versión:** 4.0  
**Fecha:** 2026-06-03  
**Revisión:** 2026-06-24 — patch gobernanza documental post auditoría V2 (H-01, H-02, H-03, F-01, jerarquía); rev. previa 2026-06-16 post ORG+INV session scope e impersonación consolidados (rev. previa 2026-06-15 listados P0+P1+P2-001 + INV Fase 0 RC1.1)  
**Estado:** Oficial — proceso canónico de refactorización por módulo; `PROMPT_BACKEND_MAESTRO.md` es punto de entrada operativo  
**Fuente:** `ERP_BACKEND_ARCHITECTURE_ALIGNMENT_AUDIT.md`  
**Estándares:** `ERP_BACKEND_STANDARDS_V4.md` · **Reglas:** `ERP_BACKEND_RULES_V4.md`

---

# CONTEXTO

Sistema SaaS ERP multi-tenant.  
Stack: FastAPI + SQL Server + Python.  
El sistema ya tiene: autenticación JWT, RBAC, LBAC, impersonación, arquitectura modular.

**Módulo objetivo:** [MODULO] — [CODIGO]

**Referencias de código obligatorias:**

| Referencia | Usar para |
|------------|-----------|
| **ORG** | Session scope, políticas TENANT/COMPANY/HYBRID, `get_org_session_client_id`, maestros, listados escalables, `{codigo}_deps.py` |
| **INV** | `require_erp_session`, `get_inv_session_client_id` (`inv_deps.py`), transaccionales, cabecera-detalle embebido, tablas derivadas, listados escalables |
| **shared/pagination** | Infra listados: `erp_pagination_params`, `erp_sort_params`, `apply_erp_sort` |

**Arquitectura oficial V4:**

```
presentation/ → application/services/ (funciones *_servicio) → infrastructure/database/queries/{cod}/
```

**NO usar:** repositories por módulo ERP, domain/entities, SQL inline en presentation.

---

# REGLAS ABSOLUTAS (leer primero)

Consultar `ERP_BACKEND_RULES_V4.md` para el listado completo. Resumen crítico:

❌ NO modificar tablas ni estructura de BD  
❌ NO eliminar código existente (marcar `deprecated=True` si es incorrecto)  
❌ NO asumir campos que no existan en la BD  
❌ NO usar Repository pattern en módulos ERP  
❌ NO usar `except Exception → HTTPException(500)`  
❌ NO aceptar `cliente_id` / `empresa_id` en body/query para autorización  

✅ Reutilizar patrones ORG + INV (session scope: §3.7 y §5.5 STANDARDS)  
✅ Validar `cliente_id` operativo via `get_{cod}_session_client_id`; `empresa_id` desde sesión  
✅ RBAC: `{modulo}.{recurso}.{accion}` via `require_permission`  
✅ `require_erp_session` en router padre del módulo  
✅ Queries en `app/infrastructure/database/queries/{cod}/`  
✅ Soft delete via `es_activo = 0`  
✅ Duplicados → `ConflictError` (409), nunca fallback 422  

⚠ **CONTRATOS EXISTENTES:** Los endpoints existentes NO son automáticamente correctos.  
Evaluar diseño arquitectónico ERP SaaS. Si es incorrecto → `deprecated=True`.  
No modificar lógica, ruta ni response_model. Frontend NO debe consumir deprecated.

---

# FLUJO DE FASES

```
FASE 0 — Análisis funcional + contraste BD     → DETENER post 0.3
FASE 1 — Patrón ORG/INV                        → DETENER post 1.2
FASE 2 — Auditoría obligatoria (sin código)    → DETENER post 2.5
FASE 3 — Implementación (solo tras confirmación)
FASE 4 — Verificación final
```

**Regla de checkpoints:** Ejecutar todos los pasos **dentro** de una fase sin detenerse.  
Detenerse **solo** al final de cada fase, esperando confirmación explícita.

---

# FASE 0 — ANÁLISIS FUNCIONAL + CONTRASTE CON BD REAL

Ejecutar Pasos 0.1 → 0.2 → 0.3 en secuencia continua. No detenerse entre ellos.

## Paso 0.1 — Mapa funcional ideal (sin leer BD ni código)

Basándote exclusivamente en conocimiento del dominio ERP SaaS, define cómo debería funcionar el módulo [MODULO] ([CODIGO]):

1. ¿Cuáles son las entidades principales?
2. ¿Qué entidades son maestros (catálogos)?
3. ¿Qué entidades son transaccionales con ciclo de vida (estados)?
4. ¿Qué entidades son cabecera-detalle (nunca operar por separado)?
5. ¿Qué entidades son derivadas/analíticas (solo lectura, calculadas)?
6. ¿Cuáles son los flujos de negocio principales?
7. ¿Qué integraciones tiene con otros módulos?

Para cada entidad del mapa ideal, define:

| Campo | Valor |
|-------|-------|
| Tipo | maestro-tenant · maestro-company · transaccional-cabecera · detalle-embebido · derivada |
| Scope | TENANT · COMPANY · HYBRID |
| Operaciones esperadas | según tipo |
| ¿Endpoints propios? | Sí / No (embebida) |

## Paso 0.2 — Leer la BD real del módulo

Leer el archivo SQL adjunto. Filtrar **únicamente** tablas con prefijo `[CODIGO]_`.

Para cada tabla:

| Campo | Detalle |
|-------|---------|
| Nombre exacto | |
| Campos principales | nombre + tipo |
| Claves foráneas | especialmente intra-módulo |
| Scope columns | `es_activo`, `cliente_id`, `empresa_id` |
| Columnas calculadas | `AS ... PERSISTED` → candidata DERIVADA |

## Paso 0.3 — Tabla de contraste: ideal vs BD real

| Entidad ideal | ¿Existe en BD? | Tabla real | Tipo confirmado | Scope | Observación |
|---|---|---|---|---|---|
| ... | ✅ / ❌ | ... | maestro/cabecera/detalle/derivada | TENANT/COMPANY/HYBRID | ... |

Responder explícitamente:

**A.** Entidades del mapa ideal que SÍ existen → se implementarán  
**B.** Entidades del mapa ideal que NO existen → "fuera de scope actual", ignorar completamente  
**C.** Tablas en BD no anticipadas → clasificar por tipo y scope  
**D.** Relaciones cabecera-detalle por FK → detalle SIN endpoints de escritura propios  

⚠ El alcance lo define la BD real, no el mapa ideal.  
No se crean tablas. No se sugieren migraciones.

⛔ **DETENTE AQUÍ.** Espera confirmación del contraste antes de Fase 1.

---

# FASE 1 — PATRÓN TÉCNICO ORG + INV

No releer la BD. Extraer estructura y patrones técnicos, no contenido funcional.

## Paso 1.1 — Análisis de referencia ORG

Revisar y documentar:

| Aspecto | Archivo ORG | Qué extraer |
|---------|-------------|-------------|
| Router agregador | `modules/org/presentation/endpoints.py` | Prefijos, tags, sub-routers |
| Session deps | `modules/org/presentation/org_deps.py` | `get_org_session_client_id`, `OrgScopePolicy`, delegación a `require_session_cliente_id` |
| Scope gates | `org_deps.py` | `require_org_tenant_erp_session`, `require_org_company_erp_session` |
| Legacy rejection | `org_deps.py` | `reject_legacy_cliente_query`, `reject_legacy_empresa_query` |
| Endpoints maestro | `endpoints_empresa.py` | CRUD, soft delete, reactivar, RBAC |
| Service funcional | `application/services/empresa_service.py` | Patrón `*_servicio` |
| Queries | `infrastructure/database/queries/org/` | Filtro `cliente_id` |
| Schemas + validators | `presentation/schemas.py` | Mixins normalize_upper/lower/strip |
| Exception handling | endpoints | Mapeo Conflict/NotFound → HTTPException |

## Paso 1.2 — Análisis de referencia INV

Revisar y documentar:

| Aspecto | Archivo INV | Qué extraer |
|---------|-------------|-------------|
| ERP session gate | `modules/inv/presentation/endpoints.py` | `require_erp_session` en router padre |
| Session deps | `modules/inv/presentation/inv_deps.py` | `get_inv_session_client_id` → `require_session_cliente_id` (patrón obligatorio todo módulo ERP) |
| Endpoints con client_id | `endpoints_categorias.py`, `endpoints_productos.py` | `Depends(get_inv_session_client_id)` — **no** `current_user.cliente_id` |
| Company scope | `producto_service.py` | `require_session_empresa_id`, `enforce_body_empresa_matches_session` |
| Transaccional | `endpoints_movimientos.py` | Cabecera-detalle embebido |
| Workflow enforcement | `inv_workflow_enforcement.py` | Campos proceso no editables; estado inicial forzado |
| Write policy derivada | `inv_stock_write_policy.py` | Bloqueo escritura directa 409 |
| Rutas proceso | `endpoints.py` + `endpoints_movimientos_proceso.py` | Montaje canónico bajo `/movimientos/{id}/*`; alias RC1.1 |
| Reversión compensatoria | `inv_estorno_proceso.py` + `estornar_movimiento_servicio` | Patrón post-proceso en UoW |
| Auditoría usuario | `inv_audit_context.py` | `usuario_creacion_id` / `usuario_actualizacion_id` desde sesión |
| Deprecated | `endpoints_movimientos_detalle.py`, `endpoints_stock.py` | Patrón `deprecated=True` |
| Queries | `infrastructure/database/queries/inv/` | Filtro `cliente_id` + `empresa_id`, ILIKE |
| RBAC | endpoints | `require_permission("inv.{recurso}.{accion}")` |

## Paso 1.3 — Plan de estructura para [CODIGO]

Definir la estructura objetivo:

```
app/modules/[codigo]/
├── presentation/
│   ├── endpoints.py                  # + require_erp_session
│   ├── endpoints_{entidad}.py
│   ├── schemas.py
│   └── [codigo]_deps.py              # Obligatorio: get_{cod}_session_client_id; + gates si scope mixto
├── application/services/
│   └── {entidad}_service.py
app/infrastructure/database/queries/[codigo]/
└── {entidad}_queries.py
```

Clasificar cada entidad confirmada (Fase 0) con scope policy:

| Entidad | Tipo | Scope | Gate | Referencia |
|---------|------|-------|------|------------|
| ... | maestro | TENANT/COMPANY | ... | ORG/INV |

## Paso 1.4 — Checkpoint

Responder únicamente:

1. ¿Qué aspectos tomarás de ORG y cuáles de INV para [CODIGO]?
2. ¿Implementarás `[codigo]_deps.py` con `get_{cod}_session_client_id`? (obligatorio — STANDARDS §5.5). ¿Qué políticas TENANT/COMPANY adicionales aplican?
3. ¿Hay entidades cabecera-detalle? ¿Cuál es la referencia INV?
4. ¿Hay tablas derivadas? ¿Cuáles endpoints deben deprecarse?
5. ¿Algún endpoint legacy usa `current_user.cliente_id` para datos? → migrar en Fase 3 (R110).

⛔ **DETENTE AQUÍ.** Espera confirmación antes de Fase 2.

---

# FASE 2 — AUDITORÍA (NO escribir código)

Con base en contraste confirmado (Fase 0) y patrón técnico (Fase 1).

## Paso 2.1 — Diagnóstico de salud

Semáforo:

| Estado | Criterio |
|--------|----------|
| 🟢 SALUDABLE | Flujos principales correctos. Ajustes menores. |
| 🟡 AJUSTES | Brechas de integridad, scope, RBAC o diseño de endpoints. |
| 🔴 PROBLEMAS | Errores de diseño que impiden operación SaaS correcta. |

Justificación: 3–5 líneas concretas.

### Tablas críticas faltantes (solo si aplica)

Solo si: (a) no existe en BD Y (b) bloquea flujo principal.  
Si no hay → omitir sección. No sugerir tablas "útiles".

## Paso 2.2 — Inventario de endpoints

Buscar archivos del módulo [CODIGO]: routers, services, queries, schemas.

Clasificar cada endpoint:

| Clasificación | Criterio |
|---------------|----------|
| ✅ CORRECTO | Mapa funcional + tenant/empresa scope + RBAC + diseño válido |
| ⚠ INCOMPLETO | Existe pero falta scope, RBAC, campos NOT NULL, detalle embebido, paginación |
| 🔴 DEPRECATED | Escritura detalle standalone, escritura derivada, diseño inválido ERP |
| 🔁 REEMPLAZAR | Incorrecto con versión correcta planificada |

Tabla obligatoria:

| Ruta | Método | Entidad | Scope ✅/❌ | RBAC ✅/❌ | ERP Session ✅/❌ | Exceptions ✅/❌ | Clasificación | Motivo |

## Paso 2.3 — Brechas funcionales por entidad

| Tipo | Operaciones a verificar |
|------|------------------------|
| MAESTRO tenant | listar, detalle, crear, actualizar, desactivar, reactivar |
| MAESTRO company | listar, detalle, crear, actualizar, desactivar, reactivar |
| TRANSACCIONAL | listar, detalle, crear-con-detalle, actualizar-con-detalle (borrador), aprobar, procesar, anular |
| TRANSACCIONAL (post-proceso) | estornar / reversar — si el dominio muta efectos no revertibles con anular |
| DETALLE | embebido — lectura opcional |
| DERIVADA | listar, detalle (solo GET) |

Para cabecera-detalle verificar **ambos**:
- POST recibe `List[DetalleCreate]` embebido → si no: ⚠ INCOMPLETO
- PUT recibe `List[DetalleUpdate]` opcional embebido → si no: ⚠ INCOMPLETO

Marca: ✅ correcto | ⚠ incompleto | ❌ falta

## Paso 2.4 — Campos faltantes en schemas

Solo para ✅ CORRECTO y ⚠ INCOMPLETO.

| Prioridad | Criterio |
|-----------|----------|
| 🔴 CRÍTICO | NOT NULL sin default, ausente en Create → falla runtime |
| ⚠ IMPORTANTE | Opcional con valor funcional para frontend |
| ➕ MENOR | Auditoría o interno — documentar, no tocar |

## Paso 2.5 — Auditoría de scope y sesión

Verificar para cada endpoint:

| Check | Detalle |
|-------|---------|
| `require_erp_session` | ¿Router padre lo tiene? |
| `cliente_id` operativo | ¿`Depends(get_{cod}_session_client_id)` — no body/query, no `current_user.cliente_id`? (R110) |
| Impersonación | ¿Resolución vía `require_session_cliente_id` (STANDARDS §3.4)? |
| Identidad vs operativo | ¿Presentation separa `current_user` de `client_id` de datos? (§3.7) |
| `empresa_id` | ¿Desde sesión si tabla lo requiere? |
| Scope policy | ¿TENANT/COMPANY/HYBRID correcto? |
| `{codigo}_deps.py` | ¿Existe con `get_{cod}_session_client_id`? |
| Cross-scope | ¿404 en lugar de 403? |
| Workflow forgeable | ¿CREATE/UPDATE aceptan `estado` o campos de proceso? → ⚠ |
| Rutas proceso | ¿Montadas bajo `/{recurso}/{id}/` o incorrectamente en raíz del módulo? → ⚠ |
| Derivadas | ¿POST/PUT activos sin política de bloqueo runtime? → 🔴 |
| Permisos lifecycle | ¿Acciones de proceso usan permiso específico o solo `actualizar`? → ⚠ |

## Paso 2.6 — Auditoría de exception handling

Verificar en cada archivo presentation:

| Patrón | Estado |
|--------|--------|
| Propaga `CustomException` al handler global | ✅ |
| Mapeo explícito por tipo (Conflict, NotFound) | ✅ |
| `except Exception → 500` | 🔴 Anti-patrón — corregir en Fase 3 |

## Paso 2.7 — Auditoría de listados escalables

| Check | Estándar V4 |
|-------|-------------|
| Paginación opt-in | Sin `page` → `list[Read]`; con `page` → envelope |
| `limit` | Default 50, max 100; ignorado sin `page` |
| `buscar` | SQL ILIKE/LIKE en queries — no in-memory |
| Estilos legacy (`skip/limit`, `page_size`) | ⚠ Migrar |
| Union response | `Union[list[Read], Paginated*Response]` si endpoint expone `page` |

## Paso 2.10 — Auditoría de ordenamiento (sort)

| Check | Estándar V4 |
|-------|-------------|
| `sort_by` + `sort_dir` en listados operativos | Whitelist por recurso |
| Sin `sort_by` | ORDER BY legacy preservado |
| `sort_by` inválido | 422 `INVALID_SORT_COLUMN` |
| Tie-breaker PK | Segundo criterio en SQL |
| Híbrido con merge | Sort post-merge (ej. ORG parámetros) |
| Detalle global standalone | `deprecated=True` si aplica (P1-INV-08) |

## Paso 2.8 — Auditoría de auditoría (meta)

| Check | Estándar V4 |
|-------|-------------|
| Operaciones CRUD críticas | ¿Invocan helper de audit ERP? |
| Auth-related | ¿Usan `AuditService`? |

## Paso 2.9 — Reporte de auditoría

Generar: `app/docs/modulos/AUDITORIA_[CODIGO].md`

Estructura exacta:

```markdown
### DIAGNÓSTICO GENERAL
[Semáforo + justificación + "El módulo cubre X de Y flujos principales"]

### TABLAS CRÍTICAS FALTANTES
[Solo si hay — si no: "Ninguna. La BD cubre todos los flujos principales."]

### ENTIDADES Y CLASIFICACIÓN
[entidad | tipo | scope | tabla BD | endpoints propios S/N]

### ENDPOINTS EXISTENTES
[Tabla completa ✅/⚠/🔴/🔁 con scope, RBAC, session, exceptions]

### ENDPOINTS A DEPRECAR
[ruta | motivo | reemplazo]

### ENDPOINTS FALTANTES A IMPLEMENTAR
[ruta | método | entidad | descripción]

### CAMPOS FALTANTES EN SCHEMAS
[por entidad: 🔴/⚠/➕]

### PROBLEMAS DE SCOPE, TENANT O RBAC
[lista concreta]

### PROBLEMAS DE EXCEPTION HANDLING
[archivo | anti-patrón | excepciones tragadas]

### SEEDS RBAC FALTANTES
[modulo.recurso.accion]

### PLAN DE ESTRUCTURA V4
[archivos a crear/modificar según patrón ORG/INV]
```

⛔ **DETENTE AQUÍ.** Espera confirmación antes de Fase 3.

---

# FASE 3 — IMPLEMENTACIÓN (solo tras confirmación explícita)

## Orden obligatorio

```
1. Marcar DEPRECATED (solo deprecated=True — nada más)
2. Schemas (+ validators UPPER/LOWER/STRIP)
3. Queries (app/infrastructure/database/queries/[codigo]/)
4. Services (funciones *_servicio)
5. Routers (endpoints nuevos + deps)
6. Seeds RBAC
```

**NO hay paso de Repositories.** Las queries reemplazan esa capa.

## Paso 3.1 — Deprecar endpoints

Solo agregar `deprecated=True` en el decorator.  
NO modificar lógica, services ni queries existentes.

## Paso 3.2 — Schemas

- Campos faltantes 🔴 CRÍTICO
- Validators `mode="before"` via mixins (`app/modules/org/presentation/schemas.py`)
- Funciones: `normalize_upper`, `normalize_lower`, `normalize_strip` de `app/shared/validators.py`
- Cabecera-detalle: `CabeceraCreate` con `detalles: list[DetalleCreate]`, etc.
- Solo Create/Update — nunca Read

## Paso 3.3 — Queries

Ubicación: `app/infrastructure/database/queries/[codigo]/{entidad}_queries.py`

Obligatorio en cada query:

- Filtro `cliente_id`
- Filtro `empresa_id` si columna existe
- Parámetros nombrados — nunca concatenar input
- `execute_query(..., client_id=UUID, connection_type=DEFAULT)`
- Funciones lookup para unicidad con `exclude_id` opcional
- Búsqueda `buscar` via SQL ILIKE/LIKE
- Paginación: `apply_erp_pagination` — solo si `page` presente
- Sort: `apply_erp_sort` con whitelist + tie-breaker PK
- Híbrido: `apply_memory_sort` post-merge cuando aplique

## Paso 3.4 — Services

Ubicación: `app/modules/[codigo]/application/services/{entidad}_service.py`

Patrón: funciones async `*_servicio` (referencia ORG/INV).

Obligatorio:

```python
empresa_id = require_session_empresa_id()          # si company-scoped
enforce_body_empresa_matches_session(...)         # si body tiene empresa_id
```

- Validación unicidad antes INSERT/UPDATE → `ConflictError`
- Validación estado transaccional → 422
- Transacciones cabecera+detalle: BEGIN/COMMIT/ROLLBACK
- Helper auditoría ERP en operaciones CRUD críticas
- Auditoría usuario: `{cod}_audit_context` — campos solo desde sesión
- Política derivadas: `assert_*_direct_write_allowed` en writes legacy
- Lanzar subclases de `CustomException` — nunca HTTPException en services

## Paso 3.5 — Routers

- Router padre: `dependencies=[Depends(require_erp_session)]`
- Crear `[codigo]_deps.py` con `get_{cod}_session_client_id` (**obligatorio**); gates TENANT/COMPANY si scope mixto (patrón ORG)
- Cada endpoint: `Depends(require_permission("[cod].[recurso].[accion]"))`
- `client_id: UUID = Depends(get_{cod}_session_client_id)` — patrón ORG **e INV** (STANDARDS §5.5); PROHIBIDO `current_user.cliente_id` para datos (R110)
- Exception handling V4 — PROHIBIDO `except Exception → 500`
- Detalle embebido en router de cabecera — NO routers detalle escritura
- Rutas proceso bajo `/{recurso}/{id}/{accion}` — NO en raíz del módulo
- Período alias: doble `include_router` del mismo router proceso (legacy + canónico) sin duplicar lógica
- Listados: `Depends(erp_pagination_params)` + `Depends(erp_sort_params)`
- `response_model=Union[list[Read], Paginated*Response]` solo si el endpoint expone `page`
- `response_model=list[Read]` válido en maestros Tier A sin `page` (referencia ORG empresa)

## Paso 3.6 — Seeds RBAC

Registrar permisos faltantes identificados en Fase 2.9.

## Reglas por tipo de entidad

### MAESTROS

- Soft delete: `es_activo = 0`
- Reactivar: `POST /{id}/reactivar` con permiso `actualizar`
- Unicidad: pre-check + catch UNIQUE → `ConflictError` 409
- Scope: TENANT o COMPANY según clasificación Fase 0

### TRANSACCIONALES

- Detalle embebido en POST/PUT cabecera
- Actualizar solo en estado borrador (o equivalente editable del dominio)
- Validar estado antes de aprobar/procesar/anular → 422; terminales / doble operación → 409
- Transacción SQL cabecera + detalle
- Workflow: `sanitize_*_create_payload` / `reject_*_workflow_in_update` en service layer
- Reversión post-proceso (si aplica): compensatorio + pipeline canónico en UoW única; diferenciar anulación pre-efecto vs reversión post-efecto

### DERIVADAS

- Solo GET
- POST/PUT existentes → deprecated (si no hecho en 3.1)

## Manejo de errores V4

Antes de implementar: leer `app/core/exceptions.py`. Usar clases existentes.

| Situación | Acción |
|-----------|--------|
| Duplicado / UNIQUE | `ConflictError` 409 — `"Ya existe [entidad] con [campo] '[valor]' en este tenant."` |
| No encontrado / cross-scope | `NotFoundError` 404 |
| Sin permiso / sesión | `AuthorizationError` 403 |
| Estado inválido | 422 — `"Esta operación solo está permitida en estado [requerido]. Estado actual: [actual]."` |
| Terminal / doble operación / derivada bloqueada | `ConflictError` 409 |
| SQL Server error | Capturar y mapear — nunca 500 genérico al cliente |

En presentation: propagar `CustomException` o mapear explícitamente.  
**PROHIBIDO:** `except Exception → HTTPException(500)`.

## Auditoría V4

| Evento | Acción |
|--------|--------|
| CRUD crítico ERP | Invocar helper auditoría en service |
| Operación auth-related | `AuditService.registrar_auth_event` |
| Durante impersonación | Metadata `impersonated_by` en todo evento |

---

# FASE 4 — VERIFICACIÓN FINAL

Al terminar Fase 3:

## 4.1 — Inventario de cambios

1. Listar todos los archivos creados o modificados
2. Listar endpoints DEPRECATED con ruta exacta

## 4.2 — Checklist por endpoint NUEVO

| Check | ✅/❌ |
|-------|------|
| `require_erp_session` en router padre | |
| `cliente_id` via `get_{cod}_session_client_id` (no `current_user.cliente_id`) | |
| `{codigo}_deps.py` presente | |
| `empresa_id` desde sesión (si aplica) | |
| Scope policy correcto (TENANT/COMPANY/HYBRID) | |
| RBAC `require_permission` | |
| Exception handling V4 (sin anti-patrón) | |
| Paginación opt-in (`page` activa envelope) | |
| `buscar` SQL (si aplica) | |
| `sort_by`/`sort_dir` con whitelist (si listado operativo) | |
| Soft delete + reactivar | |
| Auditoría en operaciones críticas | |

## 4.3 — Checklist cabecera-detalle

| Check | ✅/❌ |
|-------|------|
| Detalle embebido en body POST | |
| Detalle embebido en body PUT | |
| Transacción cubre cabecera + detalle | |
| Escritura detalle standalone deprecated | |

## 4.4 — Checklist queries

| Check | ✅/❌ |
|-------|------|
| Filtro `cliente_id` | |
| Filtro `empresa_id` (si aplica) | |
| Queries parametrizadas | |
| `DatabaseConnection.DEFAULT` + `client_id=` | |
| Lookup unicidad con exclude_id | |
| `buscar` en SQL (si aplica) | |
| `apply_erp_sort` con whitelist (si listado) | |

## 4.5 — Regresión

Verificar que ningún endpoint ✅ CORRECTO haya cambiado ruta, método o response_model.

## 4.6 — Documentación final

Generar: `app/docs/modulos/[CODIGO]_IMPLEMENTACION.md`

Incluir: archivos modificados, deprecated, checklist completo, evidencia de tests si existen.

Opcional: `app/bootstrap_v2/00_manifest/evidence/[CODIGO]_VALIDATION.json`

## 4.7 — Gate RC (Release Candidate)

Antes de declarar el módulo listo para consumo Frontend:

| Check | ✅/❌ |
|-------|------|
| Suite de regresión acumulada del módulo 100% verde | |
| OpenAPI revisado (rutas canónicas, sin colisión `operationId`) | |
| Auditoría de contratos API del módulo cerrada | |
| Rutas proceso bajo `/{recurso}/{id}/` (alias legacy documentado si aplica) | |

Referencia gate INV: 202 tests (196 baseline P0 + extensiones RC1.1).

---

# ANEXO A — OPERACIONES POR TIPO DE ENTIDAD

| Tipo | Operaciones | Scope | Gate | Referencia |
|------|-------------|-------|------|------------|
| MAESTRO tenant | CRUD + desactivar + reactivar | TENANT | tenant ERP session | ORG empresa |
| MAESTRO company | CRUD + desactivar + reactivar | COMPANY | company ERP session | INV productos |
| TRANSACCIONAL | CRUD embebido + ciclo de vida + reversión (si aplica) | COMPANY | require_erp_session | INV movimientos |
| DETALLE | Embebido; lectura opcional | — | — | INV movimientos |
| DERIVADA | GET only | COMPANY | require_erp_session | INV stock |

---

# ANEXO B — PLATFORM ADMINISTRATION

Este prompt cubre módulos **ERP operativos**. Para Platform Administration (clientes, conexiones, superadmin, catálogos globales):

- Mantener class services (legacy aceptable)
- Siempre `DatabaseConnection.ADMIN`
- Dual gate: LBAC + RBAC en mutaciones
- Audit events obligatorios
- Exception handling V4

Prompt dedicado futuro: `PROMPT_PLATFORM_V4.md` (pendiente).

---

# ANEXO C — Checklist transaccional (heredado INV Fase 0)

Patrones validados en INV que deben evaluarse en todo módulo con entidades transaccionales y derivadas:

| Check | Referencia INV | Regla V4 |
|-------|----------------|----------|
| Derivada solo GET + policy 409 | P0-002 | R82–R85, §14.4 |
| Workflow no forgeable | P0-006 | R86–R91, §13.6 |
| Permisos lifecycle en seed RBAC | S042 | R92–R93 |
| Rutas proceso bajo recurso | RC1.1 | R100–R102, §17.2 |
| Reversión compensatoria UoW | P0-003 | R96–R99, §13.7 |
| Anulación vs reversión semántica distinta | P0-003 | R97 |
| Auditoría usuario en CRUD | P0-004 | R94–R95, §8.5 |
| Costeo vía proceso (si aplica) | P0-001/005 | Helpers dominio en service layer |
| Gate RC antes de freeze FE | RC1 | R104, §4.7 |

---

# INICIO

Comienza por **Fase 0 completa** (Pasos 0.1 → 0.2 → 0.3) sin detenerte entre pasos.  
Detente solo al final del Paso 0.3 y espera confirmación.

El alcance lo define la BD real.  
Entidades del mapa ideal ausentes en BD → ignorar completamente.

---

# MATRIZ DE TRANSICIÓN V3 → V4

## Arquitectura

| Tema | V3 | V4 | Acción |
|------|----|----|--------|
| Referencia arquitectónica | "Buscar cualquier módulo existente" | ORG + INV explícitos | **Cambia** |
| Capa de datos | repositories | queries en `infrastructure/database/queries/` | **Cambia** |
| Estructura módulo ERP | presentation → application → domain → infrastructure | presentation → application → queries (sin domain/infra) | **Cambia** |
| Orden implementación | schemas → repositories → services → routers | schemas → queries → services → routers | **Cambia** |
| Class-based services | No especificado | Prohibido en ERP; funciones `*_servicio` | **Agrega** |
| Unit of Work / Use Cases | No mencionado | No usar en ERP (existen pero no cableados) | **Agrega** |

## Session scope

| Tema | V3 | V4 | Acción |
|------|----|----|--------|
| `require_erp_session` | No mencionado | Obligatorio en router padre ERP | **Agrega** |
| Scope policy TENANT/COMPANY/HYBRID | No mencionado | Clasificación obligatoria por entidad | **Agrega** |
| `{codigo}_deps.py` | No mencionado | Obligatorio en todo módulo ERP (`get_{cod}_session_client_id`); gates adicionales si scope mixto | **Cambia** |
| `cliente_id` desde sesión | "Validar siempre" (genérico) | `Depends(get_{cod}_session_client_id)`; prohibido body/query y `current_user.cliente_id` en presentation | **Cambia** |
| Resolución impersonación | No mencionado | `require_session_cliente_id`: JWT impersonation → request.state → ContextVar → user legacy | **Agrega** |
| Identidad vs contexto operativo | No mencionado | Separación explícita §3.7 STANDARDS; ORG + INV co-referencia | **Agrega** |
| Anti-patrón `current_user.cliente_id` | No mencionado | R110 — listados vacíos en impersonación | **Agrega** |
| Cross-scope → 404 | No mencionado | 404, no 403 | **Agrega** |

## Seguridad

| Tema | V3 | V4 | Acción |
|------|----|----|--------|
| RBAC `{mod}.{recurso}.{accion}` | Sí | Sí | **Mantiene** |
| LBAC | No cubierto en prompt | Documentado: solo platform, no ERP | **Agrega** |
| Dual gate platform | No mencionado | LBAC + RBAC en mutaciones platform | **Agrega** |
| Impersonación | No cubierto | Reglas de scope y audit documentadas | **Agrega** |

## Base de datos

| Tema | V3 | V4 | Acción |
|------|----|----|--------|
| `DatabaseConnection.ERP` | Implícito en docs externos | No existe; usar DEFAULT | **Elimina** |
| ADMIN vs DEFAULT | No especificado | Reglas explícitas por tipo de dato | **Agrega** |
| SQL parametrizado | Implícito | Prohibición explícita de concatenación | **Agrega** |

## Contratos API

| Tema | V3 | V4 | Acción |
|------|----|----|--------|
| Paginación | No especificada | Opt-in: `page` + `limit` + envelope | **Agrega** (ref. ORG/INV 2026-06-15) |
| Soft delete + reactivar | Sí (`es_activo = 0`) | Sí + permiso `actualizar` para reactivar | **Mantiene** + refina |
| UUID | Implícito | Explícito como estándar | **Agrega** |
| Búsqueda `buscar` | No especificada | SQL ILIKE, no in-memory | **Agrega** |
| Sort server-side | No especificada | `sort_by` + `sort_dir`, whitelist, 422 | **Agrega** (P2-001) |
| Cabecera-detalle embebido | Sí | Sí, con referencia INV explícita | **Mantiene** |
| Tablas derivadas solo GET | Sí | Sí, con referencia INV stock | **Mantiene** |
| Endpoints deprecated | Sí | Sí | **Mantiene** |
| Rutas proceso bajo `/{recurso}/{id}/` | No especificado | Canónico V4; alias legacy vía doble include (RC1.1) | **Agrega** (rev. 2026-06-12) |
| Permisos lifecycle granulares | Genérico `actualizar` | `{mod}.{recurso}.{accion}` por acción de proceso | **Agrega** (rev. 2026-06-12) |

## Transaccional y derivadas (rev. 2026-06-12 — post INV Fase 0)

| Tema | V4 base (2026-06-03) | V4 extendido (2026-06-12) | Acción |
|------|----------------------|---------------------------|--------|
| Write policy derivadas | Solo deprecated OpenAPI | + bloqueo runtime 409 + flag ops | **Agrega** |
| Workflow enforcement | Implícito en transaccional | Service layer obligatorio (R86–R91) | **Agrega** |
| Reversión post-proceso | No documentado | Patrón compensatorio + UoW; semántica anulación vs reversión (R96–R99) | **Agrega** |
| Auditoría usuario CRUD | Genérico R66 | Campos solo desde sesión (R94–R95) | **Refina** |
| Gate RC pre-Frontend | No documentado | Suite regresión + OpenAPI (R104, §4.7) | **Agrega** |
| Locking concurrente | No documentado | Mecanismo apropiado por tecnología; ej. SQL Server INV | **Agrega** |

## Errores HTTP

| Tema | V3 | V4 | Acción |
|------|----|----|--------|
| Clases CustomException | Sí | Sí | **Mantiene** |
| Duplicados → 409 | "409 o fallback 422" | Solo `ConflictError` 409 | **Cambia** |
| Anti-patrón `except Exception → 500` | No documentado | Prohibido explícitamente | **Agrega** |
| Auditoría exception handling | No incluida | Fase 2.6 obligatoria | **Agrega** |
| SQL error → 500 | Prohibido | Prohibido (reforzado) | **Mantiene** |
| Mensajes en español | Sí | Sí | **Mantiene** |

## Auditoría

| Tema | V3 | V4 | Acción |
|------|----|----|--------|
| Auth audit | No en prompt v3 | `AuditService.registrar_auth_event` obligatorio | **Agrega** |
| ERP business audit | No en prompt v3 | Helper en services para CRUD crítico | **Agrega** |
| Platform CRUD audit | No en prompt v3 | Eventos `platform_{recurso}_{accion}` | **Agrega** |
| Impersonación metadata | No en prompt v3 | `impersonated_by` en todo evento | **Agrega** |
| Auditoría pre-implementación | Sí (Fase 2) | Sí, ampliada (scope, exceptions, paginación) | **Mantiene** + expande |

## Proceso y flujo

| Tema | V3 | V4 | Acción |
|------|----|----|--------|
| Fase 0 sin detenerse | "Ejecuta completa sin detenerse" + "detente post 0.3" | Igual, sin contradicción: continua 0.1→0.3, detén post 0.3 | **Cambia** (elimina contradicción) |
| Fase 0 + Fase 1 seguidas | "Ejecuta ambas en secuencia" | Separadas con checkpoint post 0.3 | **Cambia** |
| "Confirma antes de continuar" genérico | Sí, ambiguo | Checkpoints solo al final de cada fase | **Cambia** |
| Referencia PROMPT_MODULO_MAESTRO_v3 | Sí | Eliminada — este documento es la referencia | **Elimina** |
| Fase 1 referencia | Cualquier módulo | ORG + INV con pasos 1.1/1.2 separados | **Cambia** |
| Fase 2 scope audit | No incluida | Pasos 2.5–2.8 nuevos | **Agrega** |
| Fase 4 verificación | tenant/RBAC básico | + exceptions, paginación, queries, auditoría | **Agrega** |
| Platform administration | No cubierto | Anexo B + prompt futuro | **Agrega** |

## Reglas absolutas

| Tema | V3 | V4 | Acción |
|------|----|----|--------|
| NO modificar BD | Sí | Sí | **Mantiene** |
| NO eliminar código | Sí | Sí | **Mantiene** |
| NO asumir campos | Sí | Sí | **Mantiene** |
| Alcance = BD real | Sí | Sí | **Mantiene** |
| Corrección > preservar incorrecto | Sí | Sí | **Mantiene** |
| Validators UPPER/LOWER/STRIP | Sí | Sí | **Mantiene** |
| Repository pattern ERP | Implícito en orden de capas | Explícitamente prohibido | **Elimina** |
| Reutilizar patrones existentes | Genérico | ORG + INV específico | **Cambia** |

## Documentación generada

| Artefacto | V3 | V4 | Acción |
|-----------|----|----|--------|
| `AUDITORIA_{CODIGO}.md` | Sí | Sí, con secciones ampliadas | **Mantiene** + expande |
| `{CODIGO}_IMPLEMENTACION.md` | Sí | Sí, con checklist ampliado | **Mantiene** + expande |
| Evidencia JSON | No | Opcional en bootstrap_v2 | **Agrega** |
| `ERP_BACKEND_STANDARDS_V4.md` | No existía | Estándar técnico oficial | **Agrega** |
| `ERP_BACKEND_RULES_V4.md` | No existía | Reemplazo .cursorrules | **Agrega** |

---

*CAXIS ERP Prompt Maestro V4 — Oficial — 2026-06-03 (rev. 2026-06-24 patch gobernanza documental post auditoría V2; rev. previa 2026-06-16 post ORG+INV session scope e impersonación)*
