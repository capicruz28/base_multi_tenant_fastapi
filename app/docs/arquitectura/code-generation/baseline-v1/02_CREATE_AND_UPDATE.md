# Flujo CREATE y regla BR-IMM (UPDATE) — Baseline V1

**Golden Reference:** ORG (`OrgCodigoGenerationService` + services `create_*` / `update_*`)

---

## 1. Flujo oficial CREATE

```text
POST /{modulo}/{recurso}
  → RBAC + session scope (cliente_id / empresa_id)
  → normalize manual_code (None / strip vacío → omitido)
  → session.begin()  [misma UoW que el INSERT]
       → [si manual] pre-check UNIQUE negocio (ConflictError 409)
       → [si otras reglas] p.ej. RUC duplicado
       → CodigoGeneracionGateway.allocate(sequence_key, context, session)
            via adapter módulo (ORG: OrgCodigoGenerationService.resolve_codigo_for_create)
       → payload[campo_codigo] = result.code
       → create_*(..., session=session)
       → [side effects bootstrap si aplica, p.ej. empresa → cfg EMPRESA]
  → commit / rollback
  → 201 + *Read (código siempre presente)
```

### 1.1 Comportamiento según política (CREATE)

| Policy | Body omitido / null / `""` | Body con valor |
|--------|----------------------------|----------------|
| **AUTO_DEFAULT** | Auto-generate | Accept manual + align si aplica |
| **AUTO_REQUIRED** | Auto-generate | Rechazar manual (policy) |
| **MANUAL_ONLY** | Rechazar | Accept si válido/único |
| **EXTERNAL** | Fuera del Motor secuencial | Regla propia del campo |

### 1.2 Contexto mínimo

| Campo context | Uso |
|---------------|-----|
| `client_id` | Obligatorio |
| `empresa_id` | Si `ScopeType.EMPRESA` (o superior) |
| `manual_code` | Opcional según policy |
| `operation` | `CREATE` (default) |

**Referencia ORG:**

- TENANT: `org_empresa` → `empresa_id=None`
- EMPRESA: `org_sucursal`, `org_departamento`, `org_centro_costo`, `org_cargo` → `empresa_id` de sesión

---

## 2. Regla oficial BR-IMM (UPDATE)

Norma canónica: `07_BUSINESS_RULES.md` §3.4 · `code-immutability/`.

| ID | Regla operativa Baseline |
|----|--------------------------|
| **BR-IMM-01** | Código asignado en CREATE es inmutable de por vida del registro |
| **BR-IMM-02** | `generation_policy` no aplica a UPDATE |
| **BR-IMM-03** | Schema `*Update` **no** incluye el campo código Motor |
| **BR-IMM-04** | Service `update_*` **no** valida UNIQUE de código ni llama Gateway |
| **BR-IMM-05** | Cambio excepcional solo por re-maestro / migración (fuera PUT estándar) |

### 2.1 Flujo oficial UPDATE

```text
PUT /{modulo}/{recurso}/{id}
  → RBAC + session scope
  → *Update schema (sin campo código Motor)
  → model_dump(exclude_unset=True)  # nunca contiene código Motor
  → update_* query (resto de campos)
  → 200 + *Read (código original intacto)
```

**Motor:** no participa.

---

## 3. OpenAPI (contrato)

| Schema | Campo código Motor |
|--------|-------------------|
| `*Create` | Presente; `required` según policy (AUTO_* → optional salvo MANUAL_ONLY) |
| `*Update` | **Ausente** |
| `*Read` | Presente; **required** |

Snapshot oficial: `app/docs/openapi_snapshot.json` (debe regenerarse tras cambios de contrato de módulo).

---

*Responsabilidades por capa: [`03_LAYER_RESPONSIBILITIES.md`](03_LAYER_RESPONSIBILITIES.md)*
