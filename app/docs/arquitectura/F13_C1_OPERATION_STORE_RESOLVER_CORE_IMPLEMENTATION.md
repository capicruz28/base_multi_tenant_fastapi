# F13-C1 — OperationStoreResolver Core Implementation

**Fecha:** 2026-06-28  
**Fase:** F13-1 (infraestructura pura — sin wire-up)  
**Referencias:** F13-A1 §8, F13-B1 §10, F13-B2  
**Estado:** Completado

---

## 1. Resumen

Se implementó el núcleo normativo `OperationStoreResolver` + tipos asociados según F13-A1 §8.3 y F13-B1 §10.4. **Cero cambios en runtime productivo**: ningún servicio, endpoint, middleware ni catalog store importa el resolver.

---

## 2. Archivos creados

| Archivo | Rol |
|---------|-----|
| `app/core/tenant/operation_store_types.py` | `OperationPlane`, `SessionKind`, `EngineKind`, `OperationDescriptor`, `InstallationProfile`, `ExecuteQueryIntent`; `InstallationProfile.from_metadata()` delega RI-39 en `routing._validate_dedicated_route_metadata` |
| `app/core/tenant/operation_store_resolver.py` | `resolve_operation_store()`, `OperationStoreResolver`, `get_installation_profile()`, `resolve_database_type()` |
| `tests/unit/test_operation_store_resolver.py` | Matriz F13-B1 §10.5 (14 tests) |

### Archivos de producción existentes modificados

**Ninguno** (cumple restricciones F13-C1).

---

## 3. Algoritmo implementado

Alineado a F13-A1 §8.3 / F13-B1 §10.4:

| Paso | Comportamiento |
|------|----------------|
| 1 | Validar `session_target_cliente_id == target_cliente_id` cuando está presente → `ValidationError` (`IMPERSONATION_TARGET_MISMATCH`) |
| 2 | `operation_plane == control_plane` → `ADMIN`, `client_id=None`, `ENGINE_SCOPED`, `operation_class=control_plane` **sin** llamar metadata |
| 3 | `tenant_data` → `meta = await get_connection_metadata_async(target, OPERATION_CLASS_TENANT_DATA)` |
| 4 | `InstallationProfile.from_metadata(target, meta)` — validación RI-39 vía routing |
| 5 | `shared_single` → `DEFAULT`, `ROW_SCOPED`, `client_id=target`, `database_type=single` |
| 6 | `dedicated_multi` → `DEFAULT`, `ENGINE_SCOPED`, `client_id=target`, `database_type=multi` |
| 7 | Metadata dedicated incompleta → `DatabaseError` (`DEDICATED_ROUTE_FAIL_CLOSED`) |

**Delegación (sin duplicar routing):**

- `get_connection_metadata_async`
- `_validate_dedicated_route_metadata`
- `OPERATION_CLASS_*`, `DEDICATED_ROUTE_FAIL_CLOSED`, `DEFAULT_DATABASE_TYPE`

---

## 4. Cobertura de tests

### Ejecución

```text
pytest tests/unit/test_operation_store_resolver.py -v
→ 14 passed
```

### Matriz F13-B1 (V-01…V-09)

| ID | Test | Resultado |
|----|------|-----------|
| V-01 | Algoritmo §8.3 | ✅ T-01…T-03 |
| V-02 | CP → ADMIN, ENGINE_SCOPED | ✅ `test_t01_*`, `test_control_plane_golden_parity_*` |
| V-03 | Shared tenant_data → DEFAULT, ROW_SCOPED | ✅ `test_t02_*` |
| V-04 | Dedicated tenant_data → DEFAULT, ENGINE_SCOPED | ✅ `test_t03_*` |
| V-05 | Dedicated incompleta → fail-closed | ✅ `test_t04_*` |
| V-06 | Golden shared (F13-A1 vs catálogo metadata) | ✅ `test_t06_*` |
| V-07 | Golden dedicated = catálogo metadata | ✅ `test_t07_*` |
| V-08 | `to_execute_query_kwargs()` keys | ✅ `test_t08_*` |
| V-09 | Impersonation mismatch | ✅ `test_t05_*`, `test_impersonation_matching_*` |

### Tests adicionales

| Test | Propósito |
|------|-----------|
| `test_control_plane_skips_metadata_lookup` | CP no invoca `get_connection_metadata_async` |
| `test_operation_store_resolver_class_resolve` | Fachada `OperationStoreResolver.resolve` |
| `test_get_installation_profile_delegates_metadata` | Helper F13-3 |
| `test_resolve_database_type_shared_single` | Legacy `single`/`multi` para RBAC |

**Fixtures:** `build_shared_metadata` / `build_dedicated_metadata` de `tests/integration/helpers/hybrid_mock_metadata.py`.

---

## 5. Validación cero wire-up

### Grep producción (`.py` en `app/`)

```text
OperationStoreResolver | operation_store_resolver | resolve_operation_store | operation_store_types
```

**Resultado:** solo en:

- `app/core/tenant/operation_store_types.py`
- `app/core/tenant/operation_store_resolver.py`

**No** aparece en servicios, endpoints, catalog stores, `platform_global_query_intent`, auth, middleware.

### Grep tests

Solo `tests/unit/test_operation_store_resolver.py`.

---

## 6. Validación cero cambios funcionales

| Verificación | Estado |
|--------------|--------|
| `routing.py` sin diff | ✅ |
| `queries_async.py`, `query_helpers.py` sin diff | ✅ |
| Catalog stores sin diff | ✅ |
| Superadmin / tenant services sin diff | ✅ |
| Endpoints / OpenAPI sin diff | ✅ |
| Resolver no importado fuera de `app/core/tenant/` | ✅ |
| CP branch no consulta metadata (sin side effects routing) | ✅ test |

**Comportamiento HTTP / UX:** idéntico al pre-F13-1. El resolver existe pero **nadie lo invoca** en producción.

---

## 7. Suite existente

| Alcance | Resultado | Notas |
|---------|-----------|-------|
| `tests/unit/test_operation_store_resolver.py` | **14/14 passed** | F13-1 |
| `tests/unit/` completo | 1285 passed, 69 failed | Fallos **preexistentes** (IAM, tenant isolation, INV, superadmin auditoría, etc.) — **ninguno** referencia `operation_store_*` |
| Suite completa `tests/` | 1393 passed, 94 failed, 48 skipped | Misma situación; **sin regresión atribuible a F13-1** |

F13-1 no modifica código productivo existente; los fallos de suite son ajenos a esta fase.

---

## 8. Riesgos

| ID | Riesgo | Mitigación F13-1 | Residual F13-2+ |
|----|--------|------------------|-----------------|
| R-C1-01 | Deriva vs `routing.py` | `from_metadata` delega `_validate_dedicated_route_metadata`; golden dedicated T-07 | Revisar en wire-up F13-2 |
| R-C1-02 | Shared tenant_data (DEFAULT) vs catálogo legacy (ADMIN) | T-06 documenta divergencia intencional F13-A1; F13-2 unificará catalog | **Medio** hasta F13-2 |
| R-C1-03 | Wire-up prematuro en mismo PR | Grep gate + 0 imports productivos | Gate review F13-2 |
| R-C1-04 | Coexistencia con `platform_global_query_intent` | Sin wire-up; F13-6 debe absorber kwargs | Duplicación temporal |
| R-C1-05 | `InstallationProfile.from_metadata` importa routing privado | Patrón ya usado en codebase; sin ciclo resolver↔routing | Bajo |

---

## 9. Siguiente fase — F13-2

**Primer wire-up productivo permitido** (post-merge F13-1):

1. Reimplementar `menu_catalog_store.resolve_menu_catalog_query1_target` como delegación:

   ```text
   intent = await resolve_operation_store(
     OperationDescriptor(target_cliente_id=cliente_id, operation_plane=tenant_data)
   )
   return intent.connection_type, intent.client_id
   ```

2. Idem `permission_catalog_store.resolve_permission_catalog_target`.

3. Smoke HTTP Shared + Dedicated (menú impersonation @ platform Origin).

4. **No** iniciar F13-2 en el mismo PR que F13-1.

---

## 10. Definition of Done F13-1

| Criterio F13-B1 | Cumplido |
|-----------------|:--------:|
| E1 `operation_store_types.py` | ✅ |
| E2 `operation_store_resolver.py` | ✅ |
| E3 unit tests V-01…V-09 | ✅ |
| V-10 cero wire-up | ✅ |
| V-11 pytest resolver verde | ✅ |
| V-12 suite sin regresión F13-1 | ✅ (sin cambios productivos) |
| Sin commits (instrucción usuario) | ✅ |

---

*Implementación F13-C1 / F13-1. Detener aquí — F13-2 no iniciado.*
