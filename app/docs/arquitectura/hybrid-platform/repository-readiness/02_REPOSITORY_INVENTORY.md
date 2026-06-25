# 02 — Repository Inventory

**Etapa:** 6.0 — Repository Readiness  
**Fecha:** 2026-06-25  
**Tipo:** Inventario AS-IS verificado en disco

---

## 1. Whitelist BL-1.0 — archivos infra (§9)

| Archivo BL | Path repo | Existe | Líneas aprox | Fase IP |
|------------|-----------|--------|--------------|---------|
| connection_async | `app/infrastructure/database/connection_async.py` | ✅ | ~350 | F1 |
| routing | `app/core/tenant/routing.py` | ✅ | ~870 | F1 |
| queries_async | `app/infrastructure/database/queries_async.py` | ✅ | ~1050 | F1 |
| query_helpers | `app/infrastructure/database/query_helpers.py` | ✅ | ~200 | F1 |
| cache | `app/core/tenant/cache.py` | ✅ | ~150 | F1 |
| middleware | `app/core/tenant/middleware.py` | ✅ | ~500 | F3 |
| user_context | `app/core/auth/user_context.py` | ✅ | ~200 | F3 |
| rol_service | `app/modules/rbac/application/services/rol_service.py` | ✅ | ~1300 | F3 |
| main shutdown | `app/main.py` | ✅ | ~456 | F1 |

**Resultado:** 9/9 ✅

---

## 2. Archivos tenant core relacionados

| Archivo | Path | Existe | Notas |
|---------|------|--------|-------|
| context | `app/core/tenant/context.py` | ✅ | Expone `database_type` — F3 scope |
| session_scope | `app/core/tenant/session_scope.py` | ✅ | Protegido |
| routing metadata | `app/core/tenant/routing.py` | ✅ | Whitelist infra |

---

## 3. Unit of Work

| Archivo | Path | Existe |
|---------|------|--------|
| unit_of_work | `app/core/application/unit_of_work.py` | ✅ |

**API verificada:**
- `__init__(client_id=None, connection_type=DEFAULT)`
- `async with UnitOfWork(...) as uow`
- `await uow.execute(query)`
- Commit/rollback automático en `__aexit__`

---

## 4. execute_* — punto central

| Función | Archivo | Firma verificada |
|---------|---------|------------------|
| execute_query | queries_async.py | `(query, params=None, connection_type=DEFAULT, client_id=None, skip_tenant_validation=False)` |
| execute_insert | queries_async.py | `(query, params=None, connection_type=DEFAULT, client_id=None)` |
| execute_update | queries_async.py | `(query, params=None, connection_type=DEFAULT, client_id=None)` |

**Legacy deprecated:** `app/infrastructure/database/queries.py` (sync) — no usado en path canónico.

---

## 5. Repositories legacy

| Archivo | Path | Existe |
|---------|------|--------|
| base_repository | `app/infrastructure/database/repositories/base_repository.py` | ✅ |
| cfg_codigo_secuencia | `.../cfg_codigo_secuencia_repository.py` | ✅ |
| __init__ | `.../repositories/__init__.py` | ✅ |

**Total:** 3 archivos — alineado E5 doc 09.

---

## 6. Módulos ERP (presentation endpoints)

**Count verificado:** 32 módulos con `presentation/endpoints.py`

| Código | Presente |
|--------|----------|
| org, inv, pur, sls, auth, rbac, users | ✅ |
| fin, hcm, mnt, mrp, pos, tkt, wfl, ... | ✅ (32 total) |

Consistente con auditoría E0 (~35 módulos incluyendo tenant/superadmin sin endpoints ERP estándar).

---

## 7. Tests — estado vs IP-1.0

### 7.1 Referenciados IP — **NO existen (F0 los crea)**

| Test planificado IP | Existe | Acción F0 |
|---------------------|--------|-----------|
| `tests/integration/conftest_hybrid.py` | ❌ | PR-F0-01 |
| `tests/integration/helpers/hybrid_mock_metadata.py` | ❌ | PR-F0-01 |
| `test_hybrid_wrong_route.py` | ❌ | PR-F0-02 |
| `test_hybrid_tenant_isolation.py` | ❌ | PR-F0-03 |
| `test_hybrid_impersonation_harness.py` | ❌ | PR-F0-04 |
| `test_hybrid_gateway_*.py` | ❌ | PR-F1-08 |

### 7.2 Existentes reutilizables

| Test | Path | Reutilizable |
|------|------|--------------|
| IAM sessions v2 harness | `tests/integration/conftest_iam_sessions_v2.py` | Parcial |
| Tenant isolation | `tests/security/test_tenant_isolation_comprehensive.py` | ✅ F0 reference |
| Tenant isolation unit | `tests/unit/test_tenant_isolation.py` | ✅ |
| ERP session contract | `tests/integration/test_erp_session_contract.py` | ✅ |
| UoW unit | `tests/unit/test_unit_of_work.py` | ✅ F1 |

---

## 8. CI / workflows

| Item IP | Existe | Fase creación |
|---------|--------|---------------|
| `.github/workflows/ci.yml` | ✅ | — |
| Job hybrid tests | ❌ | F0-05 |
| Job shared-regression required | ❌ | F2-02 |
| Script erp-guard | ❌ | F0/F2 |
| Script database_type whitelist | ❌ | F3-04 |
| OpenAPI diff gate | ❌ | F2 |

---

## 9. Config / feature flags

| Setting IP | Existe en config | Notas |
|------------|------------------|-------|
| `DEDICATED_ENABLED` | ❌ | Crear F1 opcional per IP |
| `DB_*` pool settings | ✅ | TD-04 |
| Metadata TTL setting | ⚠️ Parcial | cache.py existe; TTL formal F1-WP02 |

---

## 10. OpenAPI

| Artefacto | Path | Existe |
|-----------|------|--------|
| Snapshot | `app/docs/openapi_snapshot.json` | ✅ |

Baseline para diff CI — gate por implementar F2.

---

## 11. Scripts raíz (fuera scope F0–F3)

Archivos `validacion_*.py`, `test_*.py` en raíz — scripts ad-hoc; no afectan F0.

---

## 12. Conclusión

Inventario confirma **targets F1–F3 existen**. Tests hybrid **pendientes de creación** — comportamiento esperado pre-F0.
