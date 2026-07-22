# Errores HTTP y flujo runtime

**Audiencia:** Frontend + QA  
**Alcance:** CREATE con motor de códigos — 5 entidades ORG Ola 1

---

## 1. Catálogo de errores HTTP

### 1.1 Éxito

| Status | Cuándo | Body |
|--------|--------|------|
| **201 Created** | Alta exitosa | `{Entity}Read` con código asignado |

### 1.2 Errores cliente / negocio

| Status | Excepción | Cuándo | Acción Frontend |
|--------|-----------|--------|-----------------|
| **400** | `ValidationError` / motor | Código manual formato inválido | Mostrar `detail` en campo código |
| **403** | `AuthorizationError` | Sin permiso RBAC | Mensaje permiso |
| **403** | `AuthorizationError` (`EMPRESA_MISMATCH`) | `empresa_id` body ≠ sesión | Refrescar contexto empresa / corregir payload |
| **404** | `NotFoundError` | cfg secuencia ausente (`CFG_SEQUENCE_NOT_FOUND`) | Error técnico — contactar soporte |
| **409** | `ConflictError` | Código duplicado en scope | Mostrar mensaje unicidad en campo código |
| **409** | `ConflictError` | RUC duplicado (solo empresa) | Mostrar en campo RUC |
| **422** | `RequestValidationError` (FastAPI) | Schema Pydantic (campos required) | Errores por campo estándar |

### 1.3 Formato error API

```json
{
  "detail": "Ya existe un cargo con el código 'CAR001' en esta empresa."
}
```

Errores Pydantic 422:

```json
{
  "detail": [
    { "loc": ["body", "nombre"], "msg": "Field required", "type": "missing" }
  ]
}
```

### 1.4 Mapeo ConflictError por entidad

| Entidad | Mensaje 409 código |
|---------|-------------------|
| Empresa | `Ya existe una empresa con el código '{codigo}' en este tenant.` |
| Sucursal | `Ya existe una sucursal con el código '{codigo}' en esta empresa.` |
| Departamento | `Ya existe un departamento con el código '{codigo}' en esta empresa.` |
| Centro costo | `Ya existe un centro de costo con el código '{codigo}' en esta empresa.` |
| Cargo | `Ya existe un cargo con el código '{codigo}' en esta empresa.` |

---

## 2. Flujo completo Frontend → Backend → Motor → BD → Response

### 2.1 Diagrama general (company-scoped)

```mermaid
sequenceDiagram
    participant FE as React Form
    participant API as FastAPI ORG
    participant SVC as *_service
    participant GW as CodigoGeneracionGateway
    participant CFG as cfg_codigo_secuencia
    participant BD as Tabla org_*

    FE->>API: POST /org/{recurso} JSON (codigo opcional)
    API->>API: RBAC + session scope
    API->>SVC: create_*_servicio(client_id, data)
    SVC->>SVC: enforce_body_empresa_matches_session
    SVC->>SVC: ensure_empresa_in_tenant
    SVC->>SVC: session.begin()
    alt manual codigo presente
        SVC->>BD: get_*_by_codigo (dup check)
        BD-->>SVC: row | null
        alt duplicado
            SVC-->>API: ConflictError 409
            API-->>FE: 409 detail
        end
    end
    SVC->>GW: allocate(sequence_key, context, session)
    GW->>CFG: lock/read cfg row EMPRESA
    alt codigo omitido
        GW->>CFG: increment ultimo_numero
        GW->>GW: format code (SUC001)
    else codigo manual
        GW->>GW: validate + align counter
    end
    GW-->>SVC: GenerationResult.code
    SVC->>BD: INSERT org_*
    SVC->>SVC: commit
    SVC-->>API: EntityRead
    API-->>FE: 201 + codigo asignado
```

### 2.2 Flujo org_empresa (tenant-scoped)

```mermaid
sequenceDiagram
    participant FE as React Form
    participant API as FastAPI
    participant SVC as empresa_service
    participant GW as Gateway
    participant BD as org_empresa
    participant BOOT as EmpresaBootstrapService

    FE->>API: POST /org/empresa (codigo_empresa opcional)
    API->>SVC: create_empresa_servicio
    SVC->>SVC: session.begin()
    opt manual
        SVC->>BD: get_empresa_by_codigo
    end
    SVC->>BD: get_empresa_by_ruc
    SVC->>GW: allocate org_empresa TENANT
    GW-->>SVC: EMP002
    SVC->>BD: INSERT org_empresa
    SVC->>BOOT: insertar_secuencias_codigo(empresa_id)
    SVC->>SVC: commit
    SVC-->>FE: 201 EmpresaRead
```

### 2.3 Puntos clave para Frontend

| Punto | Implicación |
|-------|-------------|
| Código se conoce **después** del 201 | No pre-calcular en FE salvo preview futuro |
| Transacción atómica | Si 409/404, **no** se creó registro |
| Normalización UPPER en Backend | FE puede enviar minúsculas |
| `""` ≡ omitido | Limpiar input vacío antes de enviar (opcional) |

---

## 3. Sesión ERP requerida

| Entidad | Gate router | Requisito sesión |
|---------|-------------|------------------|
| Empresa | `require_org_tenant_erp_session` | JWT tenant; lista todas empresas |
| Sucursal, Depto, CC, Cargo | `require_org_company_erp_session` | JWT con `empresa_id` operativa |

**Frontend:** formularios company-scoped deben ejecutarse con empresa activa seleccionada en sesión; `empresa_id` del body = empresa activa.

---

## 4. UPDATE — inmutabilidad BR-IMM

| Operación | Motor interviene | Código en UPDATE |
|-----------|------------------|------------------|
| CREATE | ✅ Sí | Asignación / aceptación manual |
| UPDATE | ❌ Nunca (**BR-IMM-04**) | **Inmutable** (**BR-IMM-01**) |
| DELETE (soft) | ❌ No | Intact |

**Normativa:** aprobada 2026-07-13. **Runtime:** enforcement schemas/services = fase implementación pendiente.  
FE objetivo: no enviar código en PUT; campo solo lectura. Error futuro: `422 CODE_IMMUTABLE`.

---

## 5. Casos transversales QA

| ID | Escenario | Entidades | Esperado |
|----|-----------|-----------|----------|
| X-01 | CREATE sin código | Todas | 201 + auto |
| X-02 | CREATE manual único | Todas | 201 + manual |
| X-03 | CREATE manual dup | Todas | 409 antes motor |
| X-04 | Dos CREATE auto seguidos | Todas | Códigos correlativos distintos |
| X-05 | Cambio empresa sesión | Company-scoped | Contador independiente por empresa |
| X-06 | Impersonación tenant | Todas | client_id operativo JWT, no platform |
| X-07 | UPDATE con intento de cambio de código | Todas | Post-enforcement: inmutable / 422 |

---

*Estrategia migración FE: [`04_FRONTEND_MIGRATION_STRATEGY.md`](04_FRONTEND_MIGRATION_STRATEGY.md)*
