# Ola 1.2 — org_cargo: Pruebas y riesgos de regresión

**Estado:** Auditoría — sin implementación  
**Fecha:** 2026-07-11

---

## 12. Pruebas unitarias existentes

### 12.1 Directamente relacionadas con cargo

| Archivo | Cobertura | Gap |
|---------|-----------|-----|
| `tests/unit/test_org_codigo_generation_service.py` | `sequence_key="org_cargo"`, allocate mock | No prueba `cargo_service` |
| `tests/unit/test_codigo_engine_ola0.py` | Gateway tests con `"org_cargo"` + cfg mock | Motor aislado |
| `tests/unit/test_org_buscar_sql.py` | `cargo_service.list_cargos_servicio` | Solo listado SQL |

### 12.2 ORG general (aplicables indirectamente)

| Archivo | Relevancia cargo |
|---------|------------------|
| `test_org_company_scope.py` | `enforce_body_empresa_matches_session` |
| `test_org_session_scope.py` | Sesión company |
| `test_org_sort.py` / `test_org_pagination.py` | Listados — no create |
| `test_org_empresa_uow.py` | **Patrón referencia UoW** — replicar para cargo |

### 12.3 Ausentes hoy

| Área | Estado |
|------|--------|
| `create_cargo_servicio` | **Sin tests** |
| `cargo_queries.create_cargo` dual-path | **Sin tests** |
| POST integración cargo + motor | **Sin tests** |
| Duplicidad 409 cargo | **Sin tests** |

---

## 13. Pruebas nuevas requeridas

### 13.1 Queries (`test_org_cargo_uow.py` — propuesto)

| Test | Criterio |
|------|----------|
| `get_cargo_by_codigo` con session | Usa `session.execute`, no `execute_query` |
| `get_cargo_by_codigo` sin session | Legacy path intacto |
| `create_cargo` con session | Usa `session.execute`, no `execute_insert` |
| `create_cargo` sin session | Legacy path intacto |

### 13.2 Service (`test_org_cargo_motor_integration.py` — propuesto)

| Test | Criterio |
|------|----------|
| Create sin `codigo` | Mock OCG → código asignado; INSERT con ese código |
| Create con manual válido | OCG ACCEPT_MANUAL; 201 |
| Create manual duplicado | 409 ConflictError |
| Create sin cfg (mock NotFoundError) | Propaga error motor |
| TX rollback | allocate OK + INSERT falla → no commit (mock) |
| `session.begin()` invocado | Una TX por create |

### 13.3 Schema (opcional)

| Test | Criterio |
|------|----------|
| `CargoCreate` sin codigo | Valida Pydantic OK |
| `CargoCreate` codigo upper | normalize_upper preservado |

### 13.4 Regresión listados

| Test | Criterio |
|------|----------|
| `list_cargos_servicio` | Sin cambio comportamiento |

---

## 14. Riesgos de regresión

| ID | Riesgo | Severidad | Mitigación |
|----|--------|-----------|------------|
| R-C01 | **Drift contador** — allocate sin rollback | **Alta** | UoW obligatorio |
| R-C02 | cfg `org_cargo` ausente por empresa | Alta | Verificar EBS V1; test 404 CFG |
| R-C03 | Frontend legacy envía codigo + auto | Media | AUTO_DEFAULT acepta manual |
| R-C04 | Race UNIQUE concurrente | Media | Pre-check + catch SQL 409 |
| R-C05 | `empresa_id` body ≠ sesión | Baja | Ya bloqueado por scope |
| R-C06 | Impersonación client_id | Baja | Patrón ORG existente |
| R-C07 | Dedicated vs Shared connection | Media | `get_connection_for_tenant(tenant_data)` |
| R-C08 | UPDATE cambia codigo sin motor | Baja | Fuera alcance Ola 1.2 create |
| R-C09 | Listado / sort / buscar | Baja | No tocar queries list |
| R-C10 | OpenAPI breaking strict clients | Media | Fase T1 convivencia optional |

---

## Matriz impacto componentes

| Componente | Modificar Ola 1.2 | Congelado |
|------------|-------------------|-----------|
| `endpoints_cargos.py` | No (salvo docstring) | — |
| `cargo_service.py` | **Sí** | — |
| `cargo_queries.py` | **Sí** (dual-path) | — |
| `schemas.py` CargoCreate | **Sí** (optional codigo) | — |
| `OrgCodigoGenerationService` | No | ✅ |
| `app/core/codigo/**` | No | ✅ |
| Bootstrap | No | ✅ |
