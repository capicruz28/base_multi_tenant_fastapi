# Responsabilidades por capa — Baseline V1

---

## 1. Matriz de responsabilidades

| Capa | Debe | No debe |
|------|------|---------|
| **Gateway** (`CodigoGeneracionGateway`) | `allocate`, `preview`, `validate_manual`, `align_counter`; resolver policy/scope; propagar errores de dominio | Conocer routers ERP; RBAC; decidir edición de entidad; connections BD por su cuenta |
| **Motor** (formatter, parser, validator, stores, coordinator, catalog) | Formato, parseo, validación, incremento/aceptación, high-water, definición estática por `sequence_key` | CRUD de maestros ERP; mutar códigos en UPDATE; lógica de negocio de módulo |
| **Adapter módulo** (ej. `OrgCodigoGenerationService`) | Construir `GenerationContext`; delegar al Gateway; API delgada reutilizable | Duplicar PolicyResolver; conocer más de una entidad de la necesaria (key + dims) |
| **Services** (`create_*` / `update_*`) | UoW CREATE; UNIQUE pre-check manual; mapear código al payload; UPDATE **sin** lógica de código | Invocar Gateway en UPDATE; “reinventar” correlativos; bypasear Gateway |
| **Schemas** | Create: campo según policy; Update: **sin** código Motor; Read: código required | Exponer código editable en Update; hacer required el código en AUTO_DEFAULT Create |
| **Queries** | INSERT/UPDATE/SELECT con `cliente_id` (+ `empresa_id`); `get_by_codigo` para CREATE; dual-path session | Asumir que UPDATE recibe código; generar códigos en SQL |
| **OpenAPI** | Reflejar schemas; PUT → `*Update` sin código; POST → Create optional/required correcto | Documentar legacy “código editable en PUT” |
| **Presentation / routers** | RBAC; session deps; mapear `CustomException` | Lógica de allocate; armar códigos |

---

## 2. Detalle por capa

### 2.1 Gateway

- Única fachada pública del Motor para ERP.
- Firma estable; ORG/INV solo pasan `sequence_key` + context + `session`.

### 2.2 Motor (`app/core/codigo`)

- **Congelado** como producto: no se modifica por olas de módulo.
- Incluye SequenceCatalog, PolicyResolver, ScopeResolver, stores CFG/FISCAL.

### 2.3 Services

- **CREATE:** dueño del ciclo “pre-check → allocate → insert”.
- **UPDATE:** dueño de campos de negocio **distintos** del código Motor.
- Soft-delete / reactivar: no tocan código.

### 2.4 Schemas

Patrón Golden Reference ORG:

```text
*Create  → codigo?: Optional[str]   # AUTO_DEFAULT
*Update  → (campo código Motor omitido)
*Read    → codigo: str
```

Validators `normalize_upper` en Create; en Update, validators de código con `check_fields=False` si el mixin es compartido.

### 2.5 Queries

- Conservan `get_*_by_codigo` para unicidad en CREATE.
- `update_*` acepta dict; el service **no** incluye la clave código.

### 2.6 OpenAPI

- Contrato vivo = schemas.
- Snapshot `app/docs/openapi_snapshot.json` debe regenerarse al cerrar el contrato del módulo.

---

## 3. Responsabilidades que NO pertenecen al Motor

| Responsabilidad | Dueño correcto |
|-----------------|----------------|
| RBAC / permisos | Presentation + IAM |
| Session scope / empresa activa | `session_scope` / deps módulo |
| Workflow documental (borrador→procesado) | Servicio de dominio transaccional |
| Soft-delete / reactivar | Service ERP |
| Unicidad de RUC / DNI / campos EXTERNAL | Service ERP |
| Hash/QR SUNAT | Integración fiscal |
| Decisión de UI (ocultar input código) | Frontend (guiado por contrato) |
| Prefijos tenant (admin cfg) | Módulo CFG futuro — no Motor core |
| Re-maestro / rename excepcional | Proceso BR-IMM-05 / migración |
| Paginación / sort listados | Shared pagination + queries |
| Impersonación / tenant operativo | JWT + session deps |

---

*Checklists: [`04_CHECKLISTS.md`](04_CHECKLISTS.md)*
