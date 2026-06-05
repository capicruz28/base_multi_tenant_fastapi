# CAXIS ERP — Backend Rules V4

**Versión:** 4.0  
**Fecha:** 2026-06-03  
**Estado:** Oficial — reemplazo definitivo de `.cursorrules` para trabajo ERP  
**Fuente:** `ERP_BACKEND_ARCHITECTURE_ALIGNMENT_AUDIT.md`  
**Estándar técnico:** `ERP_BACKEND_STANDARDS_V4.md`

---

## Propósito

Reglas operativas numeradas para desarrolladores y agentes de IA. Toda refactorización ERP futura debe cumplir estas reglas.

**Stack:** FastAPI + SQL Server + Python  
**Arquitectura:** Multi-tenant SaaS modular  
**Referencia de código:** ORG (scope) + INV (sesión ERP, transaccional)

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
| **R15** | Referencia obligatoria: ORG para scope/session; INV para transaccional y cabecera-detalle. |
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
| **R22** | Impersonación: usar tenant del JWT, no cliente SYSTEM del operador. |
| **R23** | Crear `{codigo}_deps.py` cuando el módulo tenga políticas de scope mixtas. |
| **R24** | Resolución de `cliente_id` en código nuevo: patrón ORG (`get_{cod}_session_client_id`). |
| **R25** | Rechazar query params legacy de scope: `reject_legacy_cliente_query`, `reject_legacy_empresa_query`. |

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
| **R38** | Paginación estándar: `page` (1-based) + `limit` (default 20, max 100) con `Paginated{Entity}Response`. |
| **R39** | Maestros con volumen < 50 registros: list completo permitido. Listas grandes: paginación obligatoria. |
| **R40** | Filtro universal: `solo_activos: bool = True` en listados. |
| **R41** | Búsqueda `buscar`: implementar en SQL (ILIKE/LIKE), no in-memory post-fetch. |
| **R42** | Soft delete: `DELETE /{id}` desactiva; `POST /{id}/reactivar` reactiva. |
| **R43** | Response models explícitos en decorators de router. |

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
| **R56** | Estado transaccional inválido → 422. Mensaje: `"Esta operación solo está permitida en estado [requerido]. Estado actual: [actual]."` |
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

1. **Integridad de datos** (tenant, transacciones) — R01–R08, R17–R25, R32–R35
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
| Estado transaccional inválido | HTTPException o ValidationError | 422 |
| Error interno | `DatabaseError` / `ServiceError` | 500 |

---

## Documentos relacionados

| Documento | Rol |
|-----------|-----|
| `ERP_BACKEND_STANDARDS_V4.md` | Estándar técnico detallado |
| `ERP_BACKEND_MASTER_PROMPT_V4.md` | Flujo de refactorización por módulo |
| `ERP_BACKEND_ARCHITECTURE_ALIGNMENT_AUDIT.md` | Auditoría origen |

---

*CAXIS ERP Backend Rules V4 — Oficial — 2026-06-03*
