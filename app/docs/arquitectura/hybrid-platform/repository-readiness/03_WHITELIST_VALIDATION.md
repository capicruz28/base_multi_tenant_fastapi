# 03 — Whitelist Validation

**Etapa:** 6.0 — Repository Readiness  
**Fecha:** 2026-06-25  
**Referencias:** BL-1.0 §9, G-10, IP F3-WP04

---

## 1. Whitelist infraestructura BL-1.0 (archivos modificables)

| # | Path | Existe | Hash estado | Validación |
|---|------|--------|-------------|------------|
| W-01 | `app/infrastructure/database/connection_async.py` | ✅ | presente | OK F1 |
| W-02 | `app/core/tenant/routing.py` | ✅ | presente | OK F1 |
| W-03 | `app/infrastructure/database/queries_async.py` | ✅ | presente | OK F1 |
| W-04 | `app/infrastructure/database/query_helpers.py` | ✅ | presente | OK F1 |
| W-05 | `app/core/tenant/cache.py` | ✅ | presente | OK F1 |
| W-06 | `app/core/tenant/middleware.py` | ✅ | presente | OK F3 |
| W-07 | `app/core/auth/user_context.py` | ✅ | presente | OK F3 |
| W-08 | `app/modules/rbac/application/services/rol_service.py` | ✅ | presente | OK F3 |
| W-09 | `app/main.py` | ✅ | presente | OK F1 |

**Veredicto whitelist archivos:** ✅ **100% PASS**

---

## 2. Whitelist G-10 — `database_type` permitido (infra)

| Archivo | En G-10 whitelist | En repo | OK |
|---------|-------------------|---------|-----|
| connection_async.py | ✅ | ✅ usa metadata | ✅ |
| routing.py | ✅ | ✅ extenso | ✅ |
| queries_async.py | ✅ | ⚠️ indirecto vía routing | ✅ |
| query_helpers.py | ✅ | ❌ no usa | ✅ |
| cache.py | ✅ | ✅ en docs | ✅ |
| provisioning (futuro) | ✅ | N/A | — |

---

## 3. `database_type` — auditoría completa repo

### 3.1 Infra whitelist (PERMITIDO)

| Archivo | Ocurrencias aprox | Veredicto |
|---------|-------------------|-----------|
| `core/tenant/routing.py` | 40+ | ✅ Permitido |
| `infrastructure/database/connection_async.py` | 3 | ✅ Permitido |
| `core/tenant/middleware.py` | 15+ | ✅ Permitido (F3 cleanup) |
| `core/tenant/context.py` | 15+ | ✅ Infra context (F3) |
| `core/tenant/cache.py` | 1 | ✅ Permitido |

### 3.2 L5 — PROHIBIDO post-F3 (deuda AS-IS)

| Archivo | Ocurrencias | En IP F3 plan | Veredicto |
|---------|-------------|---------------|-----------|
| `core/auth/user_context.py` | 4 | ✅ F3-WP02 | ⚠️ Deuda conocida |
| `modules/rbac/.../rol_service.py` | 17 | ✅ F3-WP03 | ⚠️ Deuda conocida |
| `modules/auth/.../auth_service.py` | 22 | ❌ **No en IP** | ⚠️ **GAP** |
| `modules/users/.../user_service.py` | 15 | ❌ | ⚠️ **GAP** |
| `core/auth/user_builder.py` | 8 | ❌ | ⚠️ **GAP** |
| `modules/rbac/.../permisos_negocio_service.py` | 3 | ❌ | ⚠️ **GAP** |
| `modules/rbac/.../permisos_usuario_service.py` | 2 | ❌ | ⚠️ **GAP** |
| `modules/auth/presentation/endpoints.py` | 8 | ❌ | ⚠️ **GAP** |
| `core/tenant/empresa_preference.py` | 4 | ❌ | ⚠️ **GAP** |
| `core/authorization/permission_resolver.py` | 3 | ❌ | ⚠️ **GAP** |
| `core/authorization/menu_resolver.py` | 2 | ❌ | ⚠️ **GAP** |
| `api/deps.py` | 3 | ❌ | ⚠️ **GAP** |
| `core/auth/impersonation_rbac.py` | 4 | ❌ | ⚠️ **GAP** |
| `modules/superadmin/.../superadmin_usuario_service.py` | 9 | ❌ | Platform |
| `modules/superadmin/.../audit_service.py` | 1 | ❌ | Platform |
| `modules/auth/.../refresh_token_cleanup_job.py` | 3 | ❌ | IAM job |

### 3.3 Tests / scripts (excluidos de gate producción)

| Zona | Veredicto |
|------|-----------|
| `tests/**` | ✅ Excluido gate F3 |
| `validacion_*.py`, `test_*.py` raíz | ✅ Excluido |
| `queries.py` legacy | ⚠️ Legacy |

**Conteo producción L5 con database_type:** **~15 archivos** (IP F3 planifica 3)

---

## 4. `create_async_engine`

| Ubicación | Count |
|-----------|-------|
| `connection_async.py` | 1 (import + 1 call) |
| Resto repo `.py` | **0** |

**Veredicto:** ✅ **PASS** — G-09 compliant

---

## 5. SessionLocal / Depends(get_db) / scoped_session

| Pattern | Count repo |
|---------|------------|
| SessionLocal | 0 |
| Depends(get_db) | 0 |
| scoped_session | 0 |

**Veredicto:** ✅ **PASS** — G-17 compliant

---

## 6. Conexiones SQL fuera gateway canónico

### 6.1 Permitido (platform/scripts)

| Categoría | Ejemplos | Veredicto |
|-----------|----------|-----------|
| Platform onboarding | `cliente_onboarding_service.py` | ✅ ADR pattern |
| Scripts ops | `scripts/repair_*.py` | ✅ Fuera F0–F3 |
| Repositories | `base_repository.py` | ⚠️ F1-WP09 |
| main.py health | `get_db_connection()` | ✅ Existente |

### 6.2 Desviación — queries ERP direct routing

| Archivo | Patrón | Veredicto |
|---------|--------|-----------|
| `queries/sls/pedido_detalle_queries.py` | `get_connection_for_tenant` | ⚠️ **VIOLATION G-09** parcial |
| `queries/sls/cotizacion_detalle_queries.py` | Idem | ⚠️ **VIOLATION G-09** parcial |

**Nota:** Resto ~100+ query files usan `execute_*` — 2 excepciones SLS (0.02%).

### 6.3 rol_service direct connection

| Archivo | Línea ~1244 | `get_db_connection()` directo |
|---------|-------------|-------------------------------|
| rol_service.py | 1 bloque | ⚠️ F3-WP03 scope |

---

## 7. execute_* signature stability

Comparado con E5 doc 08 y AS-IS audit:

| Parámetro execute_query | Presente | Cambio |
|-------------------------|----------|--------|
| query | ✅ | None |
| params | ✅ | None |
| connection_type | ✅ | None |
| client_id | ✅ | None |
| skip_tenant_validation | ✅ | None |

**Veredicto:** ✅ **PASS** — G-07

---

## 8. Resumen whitelist validation

| Check | Result |
|-------|--------|
| BL file whitelist exists | ✅ PASS |
| create_async_engine centralized | ✅ PASS |
| No SessionLocal/get_db | ✅ PASS |
| execute_* stable | ✅ PASS |
| database_type only infra | ❌ **FAIL** — 15 L5 files (known debt) |
| All SQL via gateway | ⚠️ **PARTIAL** — 2 SLS queries |

---

## 9. Impacto en fases

| Fase | Bloqueado |
|------|-----------|
| F0 | No |
| F1 | No |
| F2 | No |
| F3 | No — pero **ampliar scope** vs IP |

---

## 10. Conclusión

Whitelist **archivos BL: PASS**. Validación **semántica database_type: FAIL parcial** — consistente con auditoría E0 ampliada, no sorpresa para F0.
