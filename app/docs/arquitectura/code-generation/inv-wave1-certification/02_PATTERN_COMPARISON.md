# 02 — Comparación de patrón: Categoría vs ORG Cargo / Blueprint / Plan

---

## 1. Comparación contra ORG Cargo (Golden Reference certificado)

### 1.1 Adapter

| Aspecto | ORG `OrgCodigoGenerationService` | INV `InvCodigoGenerationService` | Resultado |
|--------|----------------------------------|----------------------------------|-----------|
| `_normalize_manual_input` | ✅ | ✅ idéntico | Fiel |
| `build_tenant_context` | ✅ | ✅ | Fiel |
| `build_empresa_context` | ✅ | ✅ | Fiel |
| `build_context` | ✅ | ✅ | Fiel |
| `resolve_codigo_for_create` (firma) | `(sequence_key, *, session, client_id, empresa_id, manual_code, operation)` | idéntica | Fiel |
| Delegación única a `Gateway.allocate` | ✅ | ✅ | Fiel |
| Imports desde otro módulo | No | No | Fiel |

**Diferencia:** solo nombre de clase y docstrings. **Copia fiel.**

### 1.2 Queries

| Query | ORG (`cargo_queries`) | INV (`categoria_queries`) | Resultado |
|-------|-----------------------|---------------------------|-----------|
| `_row_to_dict` | ✅ | ✅ idéntico | Fiel |
| `get_*_by_id(..., session=None)` dual-path | ✅ | ✅ | Fiel |
| `get_*_by_codigo(..., exclude_id=None, session=None)` | ✅ | ✅ | Fiel |
| `create_*(..., *, session=None)` dual-path | ✅ | ✅ | Fiel |
| `update_*` (sin dual-path; WHERE empresa-scoped) | ✅ | ✅ | Fiel |
| Guard `RuntimeError` tras INSERT en sesión | ✅ | ✅ | Fiel |

### 1.3 Service CREATE (flujo)

| Paso | ORG cargo | INV categoría | Resultado |
|------|-----------|---------------|-----------|
| `enforce_body_empresa_matches_session` | ✅ | ✅ | Fiel |
| `ensure_empresa_in_tenant` | ✅ | ✅ | Fiel |
| `_normalize_manual_codigo` | ✅ | ✅ | Fiel |
| `get_connection_for_tenant(... TENANT_DATA)` | ✅ | ✅ | Fiel |
| `session.begin()` único | ✅ | ✅ | Fiel |
| pre-check `get_*_by_codigo` + `ConflictError` | ✅ | ✅ | Fiel |
| `resolve_codigo_for_create` | ✅ | ✅ | Fiel |
| `payload["codigo"] = codigo` | ✅ | ✅ | Fiel |
| `apply_create_audit(payload, usuario_id)` | ❌ (ORG no audita usuario aquí) | ✅ | **D-1 (justificada)** |
| `create_*(..., session=session)` | ✅ | ✅ | Fiel |
| `assert_row_empresa(row)` post-CREATE | ✅ | ❌ | **D-2 (menor)** |
| `log_org_company_scope` | ✅ | ❌ | **D-2b (deuda menor)** |

### 1.4 Service UPDATE (BR-IMM)

| Paso | ORG cargo | INV categoría | Resultado |
|------|-----------|---------------|-----------|
| `require_session_empresa_id` | ✅ | ✅ | Fiel |
| `get_*_by_id` | ✅ | ✅ | Fiel |
| control cross-scope | `assert_row_empresa` | `if not row: NotFoundError` | Equivalente funcional |
| `model_dump(exclude_unset=True)` | ✅ | ✅ | Fiel |
| sin lógica de código | ✅ | ✅ | Fiel |

### 1.5 Schemas

| Schema | ORG | INV | Resultado |
|--------|-----|-----|-----------|
| Create código optional | ✅ | ✅ | Fiel |
| Update sin campo código | ✅ | ✅ | Fiel |
| Read código required | ✅ | ✅ | Fiel |
| Mixin `check_fields=False` | ✅ | ✅ | Fiel |

### 1.6 Endpoints

| Endpoint | ORG cargo | INV categoría | Resultado |
|----------|-----------|---------------|-----------|
| POST catch | `(AuthorizationError, CustomException)` | `(AuthorizationError, CustomException)` | Fiel |
| PUT catch | `(NotFoundError, CustomException)` | `NotFoundError` | **D-3 (menor)** |
| Rutas / RBAC | sin cambios | sin cambios | Fiel |

---

## 2. Comparación contra el Blueprint aprobado (`inv-implementation-blueprint/`)

| Requisito Blueprint | Evidencia implementación | Resultado |
|---------------------|--------------------------|-----------|
| Adapter en `application/services/inv_codigo_generation_service.py` | Existe | ✅ |
| `build_tenant_context` opcional | Presente (por simetría) | ✅ |
| Flujo CREATE §2 (espejo cargo) | Coincide paso a paso | ✅ |
| `apply_create_audit` conservado | Presente | ✅ |
| Query `get_categoria_by_codigo` creada | Sí | ✅ |
| `create_categoria(..., session=)` | Sí | ✅ |
| UPDATE sin ramas de código | Sí | ✅ |
| Contrato OpenAPI §4.1 (Create opt / Update ausente / Read req) | Coincide | ✅ |
| Snapshot diferido a tarea dedicada | Respetado | ✅ |
| `sequence_key = inv_categoria_producto` | Correcto (catálogo:119) | ✅ |

**Conforme al Blueprint.**

---

## 3. Comparación contra el Plan Técnico aprobado

| Fase Plan | Entregable | Estado |
|-----------|------------|--------|
| Fase 1 | `InvCodigoGenerationService` + tests | ✅ |
| Fase 2 | `categoria_queries` + `get_categoria_by_codigo` + dual-path + export `__init__` | ✅ |
| Fase 3 | `CategoriaCreate` (opt), `CategoriaUpdate` (sin código), `CategoriaRead` intacto, validators patrón ORG | ✅ |
| Fase 4 | `categoria_service` CREATE UoW + Gateway vía adapter + BR-IMM Update | ✅ |
| Fase 5 | Endpoints: solo manejo de excepciones de dominio | ✅ (⚠ D-3 en PUT) |
| Fase 6 | Pruebas del Plan | ⚠ 24 nuevas verdes; 2 preexistentes rojas (C-01/C-02) |
| Restricción | No Motor/Gateway/Catalog/ORG/OpenAPI | ✅ |
| Restricción | Solo Categoría | ✅ |

**Orden y alcance conformes.** Único desvío al cierre: suite de entidad no 100% verde (Fase 6).

---

## 4. Catálogo de desviaciones

| ID | Desviación | Naturaleza | Veredicto |
|----|------------|------------|-----------|
| **D-1** | CREATE aplica `apply_create_audit(usuario_id)` | Estándar INV-P0-004 (auditoría usuario). ORG Cargo no lo hace. | **Justificada** — requerida por INV |
| **D-2** | CREATE no ejecuta `assert_row_empresa` post-INSERT | Defensa redundante en ORG; la fila se lee con filtro empresa dentro de la UoW | **Aceptable** (menor) |
| **D-2b** | Sin logging `log_*_company_scope` | Observabilidad ORG-específica | **Deuda menor** |
| **D-3** | PUT/detalle/delete capturan solo `NotFoundError` | ORG añade `CustomException` por defensa | **Menor recomendada** |

Ninguna desviación afecta corrección funcional, integridad multi-tenant, BR-IMM ni el uso del Motor.
