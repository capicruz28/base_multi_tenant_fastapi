# CAXIS ERP — Backend Rules V4

**Versión:** 4.0  
**Fecha:** 2026-06-03  
**Revisión:** 2026-06-16 — post ORG+INV session scope e impersonación consolidados (rev. previa 2026-06-15 listados P0+P1+P2-001 + INV Fase 0 RC1.1)  
**Estado:** Oficial — reemplazo definitivo de `.cursorrules` para trabajo ERP  
**Fuente:** `ERP_BACKEND_ARCHITECTURE_ALIGNMENT_AUDIT.md`  
**Estándar técnico:** `ERP_BACKEND_STANDARDS_V4.md`

---

## Propósito

Reglas operativas numeradas para desarrolladores y agentes de IA. Toda refactorización ERP futura debe cumplir estas reglas.

**Stack:** FastAPI + SQL Server + Python  
**Arquitectura:** Multi-tenant SaaS modular  
**Referencia de código:** ORG + INV (session scope unificado, transaccional, listados)

---

## Categoría A — Integridad absoluta

Reglas que **nunca** se negocian.

| ID | Regla |
|----|-------|
| **R01** | NUNCA modificar estructura de base de datos (tablas, columnas, constraints, índices). |
| **R02** | NUNCA eliminar código existente. Si es incorrecto → marcar `deprecated=True`. |
| **R03** | NUNCA asumir campos que no existan en la BD real. |
| **R04** | SIEMPRE filtrar `cliente_id` en toda query ERP. |
| **R05** | SIEMPRE filtrar `empresa_id` cuando la tabla tenga esa columna. |
| **R06** | SIEMPRE aplicar RBAC con patrón `{modulo}.{recurso}.{accion}` via `require_permission`. |
| **R07** | SIEMPRE usar soft delete: `es_activo = 0`. NUNCA DELETE físico. |
| **R08** | NUNCA dejar que un error SQL Server llegue al cliente como HTTP 500 sin mapear. |

---

## Categoría B — Arquitectura de módulo

| ID | Regla |
|----|-------|
| **R09** | Módulos ERP nuevos: `presentation/` → `application/services/` (funciones) → `infrastructure/database/queries/{cod}/`. |
| **R10** | PROHIBIDO crear `domain/` ni `infrastructure/` dentro de módulos ERP nuevos. |
| **R11** | PROHIBIDO usar Repository pattern en módulos ERP. Reservado a users/rbac/auth. |
| **R12** | PROHIBIDO SQL inline en presentation. Toda SQL va en capa queries. |
| **R13** | PROHIBIDO concatenar input de usuario en strings SQL. Solo queries parametrizadas. |
| **R14** | Orden de implementación: **schemas → queries → services → routers**. |
| **R15** | Referencia obligatoria: ORG + INV para session scope (`get_{cod}_session_client_id`, `{codigo}_deps.py`); ORG para políticas TENANT/COMPANY/HYBRID; INV para transaccional, cabecera-detalle y listados. Ver `ERP_BACKEND_STANDARDS_V4.md` §3.7, §5.5. |
| **R16** | PROHIBIDO replicar patrones legacy de tenant/superadmin/users (class services, SQL embebido). |

---

## Categoría C — Session scope y multi-tenant

| ID | Regla |
|----|-------|
| **R17** | Router padre de módulos ERP operativos: `dependencies=[Depends(require_erp_session)]`. |
| **R18** | Clasificar cada entidad como TENANT, COMPANY o HYBRID **antes** de codificar. |
| **R19** | `cliente_id` solo desde sesión (dependency). PROHIBIDO en body/query para autorización. |
| **R20** | `empresa_id` solo desde `require_session_empresa_id()` en services. PROHIBIDO override en body. |
| **R21** | Cross-tenant / cross-company fuera de scope → responder **404**, no 403. |
| **R22** | Impersonación: contexto operativo de datos desde tenant del JWT (`require_session_cliente_id`), no cliente SYSTEM del operador. Ver STANDARDS §3.4, §3.7. |
| **R23** | Crear `{codigo}_deps.py` en **todo** módulo ERP operativo con `get_{codigo}_session_client_id`. Si scope mixto TENANT/COMPANY/HYBRID: además enum de política + gates (patrón ORG `OrgScopePolicy`). |
| **R24** | Resolución de `cliente_id` operativo en presentation: `Depends(get_{cod}_session_client_id)` → `require_session_cliente_id` — patrón ORG **e INV** (STANDARDS §5.5). |
| **R25** | Rechazar query params legacy de scope: `reject_legacy_cliente_query`, `reject_legacy_empresa_query`. |
| **R110** | PROHIBIDO usar `current_user.cliente_id` en presentation para consultas o mutaciones de datos ERP. Anti-patrón: falla en impersonación. |
| **R111** | Separar identidad autenticada (`current_user`) de contexto operativo ERP (`get_{cod}_session_client_id`). Definición: STANDARDS §3.7. |
| **R112** | No duplicar lógica de prioridad impersonación por módulo; centralizar en `require_session_cliente_id` (`session_scope.py`). |

---

## Categoría D — Autorización (RBAC / LBAC)

| ID | Regla |
|----|-------|
| **R26** | Cada endpoint ERP: `Depends(require_permission("mod.recurso.accion"))`. |
| **R27** | Seeds RBAC obligatorios para permisos nuevos antes de merge. |
| **R28** | Reactivar entidad: permiso `actualizar`, no `eliminar`. |
| **R29** | Super admin: bypass RBAC excepto durante impersonación. |
| **R30** | Platform mutaciones: dual gate LBAC (`@require_super_admin()`) + RBAC (`require_permission`). |
| **R31** | Módulos ERP operativos: solo RBAC. LBAC no aplica. |
| **R92** | Acciones de ciclo de vida (`procesar`, `autorizar`, `anular`, `estornar`, `aprobar`, `finalizar`, etc.) requieren permiso `{mod}.{recurso}.{accion}`. |
| **R93** | PROHIBIDO usar solo `actualizar` para acciones de ciclo de vida con efectos colaterales. |

---

## Categoría E — Base de datos

| ID | Regla |
|----|-------|
| **R32** | ERP operacional: `DatabaseConnection.DEFAULT` + parámetro `client_id=`. |
| **R33** | Platform / SaaS: `DatabaseConnection.ADMIN`. |
| **R34** | PROHIBIDO referenciar o inventar `DatabaseConnection.ERP` — no existe. |
| **R35** | Transacciones cabecera + detalle: BEGIN/COMMIT/ROLLBACK explícito en service. |
| **R36** | Evitar N+1: usar JOINs o carga batch en queries. |

---

## Categoría F — Contratos API

| ID | Regla |
|----|-------|
| **R37** | IDs en paths y schemas: UUID v4. |
| **R38** | Paginación opt-in: sin `page` → `list[Read]` legacy; con `page` → `Paginated{Entity}Response` (`ErpPaginatedResponse`). `limit` default 50, max 100; ignorado sin `page`. Infra: `app/shared/pagination/`. |
| **R39** | Maestros con volumen < 50: `list[Read]` sin `page` permitido. Listas grandes: consumo con `page` recomendado (no breaking). |
| **R40** | Filtro universal: `solo_activos: bool = True` en listados. |
| **R41** | Búsqueda `buscar`: implementar en SQL (ILIKE/LIKE), no in-memory post-fetch. |
| **R42** | Soft delete: `DELETE /{id}` desactiva; `POST /{id}/reactivar` reactiva. |
| **R43** | Response models explícitos en decorators de router. |

---

## Categoría F-bis — Listados escalables (PERF backend)

| ID | Regla |
|----|-------|
| **R105** | Ordenamiento server-side: `sort_by` + `sort_dir` (`asc`\|`desc`) con whitelist por recurso en queries. |
| **R106** | Sin `sort_by` → conservar ORDER BY fijo del recurso. `sort_dir` sin `sort_by` → ignorar. |
| **R107** | `sort_by` fuera de whitelist → `CustomException` 422 (`INVALID_SORT_COLUMN`). |
| **R108** | Listados híbridos con merge en service (ej. ORG parámetros): sort post-merge via `apply_memory_sort`, luego paginar. |
| **R109** | Metadatos `has_next`/`has_prev`: fuera de contrato v1 (P0–P2). Reservados para evolución futura; no implementar hasta autorización explícita. |

---

## Categoría G — Cabecera-detalle y tablas derivadas

| ID | Regla |
|----|-------|
| **R44** | Detalle SIEMPRE embebido en body de cabecera (Create/Update). |
| **R45** | PROHIBIDO endpoints POST/PUT/DELETE independientes para tablas detalle. |
| **R46** | Endpoints detalle standalone existentes → marcar `deprecated=True`. |
| **R47** | Lectura de detalle bajo cabecera (`GET /cabeceras/{id}/detalle`) permitida. |
| **R48** | Tablas derivadas/calculadas: solo GET. Escritura directa → deprecated. |
| **R49** | Escritura en derivadas: solo desde services internos de otros procesos. |

---

## Categoría H — Manejo de errores HTTP

| ID | Regla |
|----|-------|
| **R50** | Services lanzan subclases de `CustomException` (`app/core/exceptions.py`). |
| **R51** | PROHIBIDO `except Exception → HTTPException(500)` en presentation. |
| **R52** | Preferido: dejar propagar `CustomException` al handler global. |
| **R53** | Aceptado: mapeo explícito `HTTPException(status_code=e.status_code, detail=e.detail)`. |
| **R54** | Duplicados / UNIQUE constraint → `ConflictError` (409). PROHIBIDO fallback 422. |
| **R55** | Mensaje duplicado: `"Ya existe [entidad] con [campo] '[valor]' en este tenant."` |
| **R56** | Estado transaccional inválido → 422. Mensaje: `"Esta operación solo está permitida en estado [requerido]. Estado actual: [actual]."` Estados terminales, doble operación prohibida y escritura derivada bloqueada → preferir `ConflictError` (409). |
| **R57** | Unicidad maestros: pre-check SELECT antes de INSERT/UPDATE + catch SQL UNIQUE como red de seguridad. |
| **R58** | Campo `detail` siempre string claro y específico en **español**. |
| **R59** | Antes de crear excepciones nuevas: verificar clases existentes en `app/core/exceptions.py`. |

---

## Categoría I — Schemas y validators

| ID | Regla |
|----|-------|
| **R60** | Validators de texto solo en schemas Create y Update, nunca en Read. |
| **R61** | Usar funciones de `app/shared/validators.py`: `normalize_upper`, `normalize_lower`, `normalize_strip`. |
| **R62** | `@field_validator(..., mode="before")` obligatorio para normalización. |
| **R63** | Aplicar via mixins siguiendo patrón `app/modules/org/presentation/schemas.py`. |
| **R64** | Clasificar cada campo de texto según tabla de tipos (UPPER/LOWER/STRIP) antes de implementar. |

---

## Categoría J — Auditoría

| ID | Regla |
|----|-------|
| **R65** | Auth events: siempre `AuditService.registrar_auth_event` — no negociable. |
| **R66** | ERP mutations críticas: invocar helper de auditoría en service layer. |
| **R67** | Platform CRUD: registrar eventos `platform_{recurso}_{accion}` en `auth_audit_log`. |
| **R68** | Durante impersonación: incluir `impersonated_by` en metadata de todo evento de audit. |
| **R69** | Errores de audit nunca deben romper flujo de negocio (fail-safe). |
| **R94** | `usuario_creacion_id` / `usuario_actualizacion_id` solo desde sesión; ignorar valores del body. |
| **R95** | Helper de auditoría usuario centralizado por módulo (`{cod}_audit_context`) en mutaciones CRUD críticas. |

---

## Categoría K — Evaluación de contratos y alcance

| ID | Regla |
|----|-------|
| **R70** | Endpoints existentes NO son automáticamente correctos — evaluar antes de proteger. |
| **R71** | Endpoint incorrecto → `deprecated=True`. NO modificar lógica, ruta ni response_model. |
| **R72** | PROHIBIDO crear tests para endpoints deprecated. |
| **R73** | PROHIBIDO agregar campos a schemas de endpoints deprecated. |
| **R74** | Alcance de implementación = BD real. Entidades ideales ausentes en BD → ignorar. |
| **R75** | Corrección funcional > preservar código incorrecto. |
| **R76** | PROHIBIDO proteger endpoint incorrecto solo porque ya existe. |

---

## Categoría L — Proceso de refactorización

| ID | Regla |
|----|-------|
| **R77** | Auditoría obligatoria (Fase 2 del Master Prompt) **antes** de escribir código. |
| **R78** | Generar `app/docs/modulos/AUDITORIA_{CODIGO}.md` antes de implementar. |
| **R79** | Fase 3 solo tras confirmación explícita post-auditoría. |
| **R80** | Responder en español en mensajes de error y documentación generada. |
| **R81** | Usar `ERP_BACKEND_MASTER_PROMPT_V4.md` como guía de refactorización por módulo. |

---

## Categoría M — Política de escritura en tablas derivadas

| ID | Regla |
|----|-------|
| **R82** | Tabla derivada expuesta en API: POST/PUT/DELETE → `deprecated=True` en OpenAPI. |
| **R83** | Service de escritura derivada debe invocar política de bloqueo; default → `ConflictError` 409. |
| **R84** | Mutación canónica de derivada solo vía pipeline de proceso del módulo (ej. `procesar_*_servicio`). |
| **R85** | Bypass de política solo vía flag de configuración explícito; `false` en producción. |

---

## Categoría N — Workflow transaccional

| ID | Regla |
|----|-------|
| **R86** | Campos de workflow prohibidos en CREATE/UPDATE vía API; enforcement obligatorio en service layer. |
| **R87** | CREATE transaccional fuerza estado inicial del dominio (`borrador` o equivalente). |
| **R88** | UPDATE transaccional solo en estado editable; rechazar payload con `estado` → 422. |
| **R89** | Transiciones de ciclo de vida solo vía endpoints POST `/{recurso}/{id}/{accion}`. |
| **R90** | Estados fantasma (marcados procesados/autorizados sin evidencia de proceso) → 409 en acciones de proceso. |
| **R91** | Idempotencia: definir explícitamente retorno OK vs 409 por acción (documentar en auditoría del módulo). |

---

## Categoría O — Reversión y atomicidad

| ID | Regla |
|----|-------|
| **R96** | Dominios con reversión post-proceso: documento compensatorio + mismo pipeline de proceso en UoW única. |
| **R97** | Diferenciar semánticamente anulación previa al efecto vs reversión posterior al efecto; el nombre del estado terminal de reversión es decisión del dominio. |
| **R98** | Trazabilidad obligatoria `documento_referencia_tipo` + `documento_referencia_id` en documentos compensatorios. |
| **R99** | Procesos concurrentes sobre la misma entidad: mecanismos de locking apropiados para la tecnología de persistencia (ej. SQL Server INV: `WITH (UPDLOCK, ROWLOCK)`). |
| **R103** | Pre-validar edge cases del dominio antes de invocar pipeline canónico (evitar fallos internos no mapeados al cliente). |

---

## Categoría P — Montaje de routers y OpenAPI

| ID | Regla |
|----|-------|
| **R100** | Acciones de proceso montadas bajo `/{recurso}/{id}/{accion}`, no en raíz del módulo. |
| **R101** | Migración de rutas incorrectas: doble `include_router` del mismo router (alias legacy + canónico) sin duplicar handlers ni lógica. |
| **R102** | Tras alias de rutas: verificar OpenAPI sin colisión de `operationId`. |
| **R104** | Gate RC antes de freeze para Frontend: suite de regresión del módulo 100% verde + auditoría de contratos API cerrada. |

---

## Reglas eliminadas respecto a v3 (.cursorrules)

Las siguientes reglas **ya no aplican** y deben ignorarse si aparecen en documentos anteriores:

| Regla v3 eliminada | Motivo |
|--------------------|--------|
| Orden: schemas → **repositories** → services → routers | Reemplazado por queries (R14) |
| Repository pattern como capa ERP estándar | Solo identidad (R11) |
| Referencia a `PROMPT_MODULO_MAESTRO_v3.md` | Reemplazado por Master Prompt V4 (R81) |
| "Implementa un bloque a la vez y confirma antes de continuar" | Conflicto con flujo de auditoría; reemplazado por fases con checkpoints (R77–R79) |
| Fallback 422 para duplicados si no hay excepción 409 | Existe `ConflictError` (R54) |
| Arquitectura DDD 4 capas completas por módulo | No refleja realidad ORG/INV (R10) |
| Referencia genérica "cualquier módulo existente" | Reemplazado por ORG + INV (R15) |
| `DatabaseConnection.ERP` | No existe (R34) |

---

## Orden de prioridad en conflictos

Cuando dos reglas entren en tensión, aplicar en este orden:

1. **Integridad de datos** (tenant, transacciones) — R01–R08, R17–R25, R110–R112, R32–R35
2. **Corrección funcional ERP** — R44–R49, R70–R76
3. **Compatibilidad con contratos correctos existentes**
4. **Preservación de código existente** — R02 (deprecated, no eliminar)

---

## Referencia rápida: mapeo excepción → HTTP

| Situación | Excepción | HTTP |
|-----------|-----------|------|
| Entrada inválida | `ValidationError` | 400 |
| Token inválido | `AuthenticationError` | 401 |
| Sin permiso / sesión incompleta | `AuthorizationError` | 403 |
| Recurso no encontrado / cross-scope | `NotFoundError` | 404 |
| Duplicado / UNIQUE | `ConflictError` | 409 |
| Validación Pydantic | `RequestValidationError` | 422 |
| `sort_by` inválido en listado | `CustomException` (`INVALID_SORT_COLUMN`) | 422 |
| Estado transaccional inválido | HTTPException o ValidationError | 422 |
| Estado terminal / doble operación / escritura derivada bloqueada | `ConflictError` | 409 |
| Error interno | `DatabaseError` / `ServiceError` | 500 |

---

## Documentos relacionados

| Documento | Rol |
|-----------|-----|
| `ERP_BACKEND_STANDARDS_V4.md` | Estándar técnico detallado |
| `ERP_BACKEND_MASTER_PROMPT_V4.md` | Flujo de refactorización por módulo |
| `ERP_BACKEND_ARCHITECTURE_ALIGNMENT_AUDIT.md` | Auditoría origen |

---

*CAXIS ERP Backend Rules V4 — Oficial — 2026-06-03 (rev. 2026-06-16 post ORG+INV session scope e impersonación)*
