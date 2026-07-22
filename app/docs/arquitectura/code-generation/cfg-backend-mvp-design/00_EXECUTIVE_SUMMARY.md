# CFG Backend MVP — Blueprint técnico

**Etapa:** Diseño técnico MVP Backend — **sin implementación**  
**Fecha:** 2026-07-17  
**Precondiciones aprobadas:**  
- ADR-CFG-ADMIN-LOC-001 (módulo ERP `cfg`)  
- Diseño funcional `cfg-functional-design/`  
- Auditoría AS-IS `cfg-admin-audit/`  

---

## 1. Dictamen

Este paquete es el **blueprint técnico definitivo** del MVP Backend del Administrador del Motor de Códigos.

| Pregunta | Respuesta |
|----------|-----------|
| ¿Qué se implementará? | Módulo ERP V4 `cfg` — lectura, PATCH B, activar/desactivar, preview |
| ¿Qué no se implementará en MVP? | Align, diagnóstico, validar-manual, validar-config, fiscal, Frontend |
| ¿Se toca el Motor? | **No** (Gateway/Catalog/Store frozen) |
| ¿Se toca ORG/INV? | **No** |
| ¿Extensiones permitidas? | `queries/cfg/`, módulo `cfg`, seed RBAC; Repo: `numero_inicial` + audit columns en update |
| ¿Estado del blueprint? | **Completo — listo para autorizar implementación** |

> Esta etapa **no** autoriza escribir código. La implementación requiere autorización explícita posterior.

---

## 2. Endpoints MVP (definitivos)

| Método | Ruta | RBAC |
|--------|------|------|
| GET | `/cfg/secuencias` | `cfg.secuencias.consultar` |
| GET | `/cfg/secuencias/{secuencia_id}` | `cfg.secuencias.consultar` |
| PATCH | `/cfg/secuencias/{secuencia_id}` | `cfg.secuencias.actualizar` |
| POST | `/cfg/secuencias/{secuencia_id}/activar` | `cfg.secuencias.actualizar` |
| POST | `/cfg/secuencias/{secuencia_id}/desactivar` | `cfg.secuencias.actualizar` |
| POST | `/cfg/secuencias/{secuencia_id}/preview` | `cfg.secuencias.consultar` |

Prefijo montaje: `/api/v1/cfg` → router `secuencias`.

---

## 3. Principios técnicos no negociables

1. `cliente_id` solo desde `get_cfg_session_client_id` (impersonación-safe).  
2. Escrituras siempre con `get_connection_for_tenant` + `session.begin()` (ADJ-03).  
3. Preview solo vía `CodigoGeneracionGateway.preview`.  
4. Enrich read-only vía `SequenceCatalog.get`.  
5. Rechazar campos A/C/D en PATCH; lock `org_empresa`.  
6. Soft-disable únicamente (`es_activo`); sin DELETE/POST create.  
7. Errores con `CustomException` existentes (`ValidationError`, `NotFoundError`, `ConflictError`, `AuthorizationError`).

---

## 4. Índice del paquete

| Doc | Contenido |
|-----|-----------|
| `00_EXECUTIVE_SUMMARY.md` | Este documento |
| `01_MODULE_ARCHITECTURE.md` | Carpetas, deps, services, queries, validaciones |
| `02_OPENAPI_DESIGN.md` | Contratos REST + schemas |
| `03_DATA_FLOW.md` | Flujos Shared/Dedicated, Gateway, Repo, Catalog |
| `04_IMPLEMENTATION_PLAN.md` | Orden exacto de implementación + riesgos |
| `05_TEST_PLAN.md` | Unitarias + integración |
| `06_CERTIFICATION_CRITERIA.md` | Gate de certificación MVP Backend |

---

## 5. Trazabilidad

| Fuente | Aporte |
|--------|--------|
| `cfg-functional-design/` | CU MVP, campos, UX rules |
| `codigo-generation-admin/03` | Base REST (recortada a MVP) |
| ORG `org_deps` / cargo UoW | Patrones session + `get_connection_for_tenant` |
| Gateway `preview` / `PreviewResult` | Contrato preview AS-IS |

---

*Sin cambios de código. Siguiente paso: autorización explícita para implementar según `04_IMPLEMENTATION_PLAN.md`.*
