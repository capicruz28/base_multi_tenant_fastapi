# 04 — Consistency Report

**Etapa:** 6.0 — Repository Readiness  
**Fecha:** 2026-06-25  
**Alcance:** BL-1.0 ↔ IP-1.0 ↔ Repositorio real  
**Acción:** Reportar únicamente — **sin corrección**

---

## 1. Resumen

| Dimensión | BL-1.0 | IP-1.0 | Repo | Consistente |
|-----------|--------|--------|------|-------------|
| Alcance fases | F0–F3 | F0–F3 | N/A | ✅ |
| Whitelist infra files | 9 | 9 | 9 exist | ✅ |
| execute_* API | Documentada | Referenciada | Presente | ✅ |
| UnitOfWork | Documentado | Referenciado | Presente | ✅ |
| Tests hybrid | N/A | Planificados | Ausentes | ✅ (F0 crea) |
| database_type L5 | G-10 | F3 3 archivos | ~15 archivos | ⚠️ **GAP** |
| WP/PR counts IP | N/A | Interno inconsistente | N/A | ⚠️ |
| ERP modules | No tocar | 0 | 32 routers | ✅ |

---

## 2. Inconsistencias documentales IP-1.0 (internas)

### IP-INC-01 — Conteo Work Packages

| Documento | Valor declarado | Valor real (conteo headers) |
|-----------|-----------------|-------------------------------|
| `01_IMPLEMENTATION_EXECUTION_PLAN.md` §2 | **22 WPs** | — |
| `02_WORK_PACKAGES.md` §6 tabla | **20 WPs** | 20 (F0:5 + F1:9 + F2:2 + F3:4) |
| `02_WORK_PACKAGES.md` §7 conclusión | **22 WPs** | Contradice §6 |
| `10_EXECUTIVE_SUMMARY.md` §3 | **20 WPs** | Alineado con tabla |

**Interpretación:** 01 confunde **24 pasos ordenados** (incluye 4 gates) con 22 WPs. WPs reales = **20**.

**Impacto F0:** Ninguno — conteo operativo usar **20 WPs / 20 PRs** (`03`, `10`).

---

### IP-INC-02 — Conteo Pull Requests

| Documento | Valor |
|-----------|-------|
| `01` §2 | **18 PRs** |
| `01` §12 conclusión | **18 PRs** |
| `02` §6 nota | 18 PRs si merge F0-04/F0-05 |
| `03_PULL_REQUEST_PLAN.md` | **20 PRs** (tabla completa) |
| `10_EXECUTIVE_SUMMARY.md` | **20 PRs** |

**Interpretación:** 18 = escenario consolidado opcional; 20 = plan nominal atómico.

**Impacto F0:** Ninguno — ejecutar **20 PRs** salvo acuerdo explícito merge F0-04+05.

---

### IP-INC-03 — Pasos vs WPs vs PRs

| Concepto | Count | Fuente |
|----------|-------|--------|
| Pasos ordenados (incl. gates) | 24 | `01` §4 |
| Work packages | 20 | `02` §6 |
| Pull requests | 20 | `03` |
| Gates | 4 | G-F0..G-F3 |

**Consistente** si se distingue pasos ≠ WPs.

---

## 3. BL-1.0 ↔ IP-1.0

| Check | Resultado |
|-------|-----------|
| Fases autorizadas BL = IP | ✅ F0–F3 |
| Whitelist archivos BL = IP F1/F3 targets | ✅ |
| G-09 gateway = IP F1 scope | ✅ |
| G-10 database_type = IP F3 scope | ⚠️ IP subestima archivos |
| ADR-011 catálogos dedicated | ✅ IP no contradice |
| F4 bloqueado BL = IP | ✅ |
| OpenAPI sin cambios BL = IP | ✅ |

**Sin conflicto arquitectónico.** IP F3 scope **incompleto** vs deuda real repo.

---

## 4. IP-1.0 ↔ Repositorio

### 4.1 Rutas archivos WP — verificadas

| WP | Path IP | Existe |
|----|---------|--------|
| F1-WP01 | `app/main.py` | ✅ |
| F1-WP02 | `app/core/tenant/cache.py` | ✅ |
| F1-WP03–04 | `app/core/tenant/routing.py` | ✅ |
| F1-WP05 | `app/infrastructure/database/query_helpers.py` | ✅ |
| F1-WP06 | `app/infrastructure/database/queries_async.py` | ✅ |
| F1-WP09 | `app/infrastructure/database/repositories/` | ✅ (3 files) |
| F3-WP01 | `app/core/tenant/middleware.py` | ✅ |
| F3-WP02 | `app/core/auth/user_context.py` | ✅ |
| F3-WP03 | `app/modules/rbac/application/services/rol_service.py` | ✅ |

**Veredicto rutas:** ✅ **PASS**

---

### 4.2 Tests planificados vs repo

| Test IP | Existe | Esperado |
|---------|--------|----------|
| `conftest_hybrid.py` | ❌ | F0 crea |
| `test_hybrid_wrong_route.py` | ❌ | F0 crea |
| `test_hybrid_tenant_isolation.py` | ❌ | F0 crea |
| `test_hybrid_impersonation_harness.py` | ❌ | F0 crea |
| CI hybrid job | ❌ | F0-WP05 |

**Veredicto:** ✅ Consistente — ausencia es pre-implementación.

---

### 4.3 CI gates planificados vs repo

| Gate IP | En `.github/workflows/ci.yml` | Esperado |
|---------|-------------------------------|----------|
| hybrid tests job | ❌ | F0 |
| shared-regression required | ❌ | F2 |
| erp-guard script | ❌ | F0/F2 |
| database_type grep | ❌ | F3 |
| openapi diff | ❌ | F2 |

**Veredicto:** ✅ Consistente pre-F0.

---

## 5. BL-1.0 ↔ Repositorio

### 5.1 Supuestos AS-IS validados

| Supuesto BL/E0 | Repo actual | OK |
|----------------|-------------|-----|
| Single async engine factory | ✅ connection_async only | ✅ |
| No ORM SessionLocal | ✅ 0 matches | ✅ |
| Gateway execute_* central | ✅ ~99% queries | ⚠️ 2 SLS |
| UoW pattern | ✅ intact | ✅ |
| database_type L5 debt | ✅ presente ampliada | ✅ |
| close_all_async_engines gap | ✅ no shutdown hook | ✅ |

### 5.2 Desviación no modelada en IP F3

Archivos L5 con `database_type` **no listados** en F3 WPs:

```
app/modules/auth/application/services/auth_service.py
app/modules/users/application/services/user_service.py
app/core/auth/user_builder.py
app/modules/rbac/application/services/permisos_negocio_service.py
app/modules/rbac/application/services/permisos_usuario_service.py
app/modules/auth/presentation/endpoints.py
app/core/tenant/empresa_preference.py
app/core/authorization/permission_resolver.py
app/core/authorization/menu_resolver.py
app/api/deps.py
app/core/auth/impersonation_rbac.py
app/modules/superadmin/application/services/superadmin_usuario_service.py
app/modules/superadmin/application/services/audit_service.py
app/modules/auth/application/services/refresh_token_cleanup_job.py
```

**Clasificación:** Gap planificación F3 — **no invalida BL-1.0** (mismo objetivo G-10).

---

## 6. Gates y fases — alineación

| Gate | Criterio IP | Repo ready |
|------|-------------|------------|
| G-F0 | 5 PRs tests + CI stub | ⏳ Post-F0 |
| G-F1 | 9 PRs infra | ⏳ Post-F1 |
| G-F2 | Benchmark + CI required | ⏳ Post-F2 |
| G-F3 | L5 cleanup + grep gate | ⏳ Post-F3; scope ampliar |

---

## 7. Nomenclatura PR/WP

| ID serie | Consistente IP-1.0 | En repo branches |
|----------|-------------------|------------------|
| PR-F0-01..05 | ✅ | N/A pre-F0 |
| PR-F1-01..09 | ✅ | N/A |
| hybrid/f0-harness branch | `07_GIT_BRANCHING` | ❌ No existe aún |

---

## 8. Matriz conflicto BL / IP / Repo

| ID | Conflicto | Severidad | Bloquea F0 |
|----|-----------|-----------|------------|
| C-01 | IP WP count 20 vs 22 | Doc | No |
| C-02 | IP PR count 18 vs 20 | Doc | No |
| C-03 | F3 scope < database_type real | Plan | No |
| C-04 | 2 SLS queries bypass gateway | Code debt | No |
| C-05 | Tests hybrid missing | Expected | No |
| C-06 | CI gates missing | Expected | No |

**Conflictos CRITICAL:** **0**

---

## 9. Conclusión

BL-1.0, IP-1.0 y repositorio son **consistentes para iniciar F0**. Inconsistencias son:

1. **Internas IP** (conteos 18/20/22) — resolver en IP-1.1 doc-only opcional
2. **F3 scope subestimado** — ampliar durante ejecución F3 sin cambiar BL
3. **2 archivos SLS** — evaluar F1-WP09

**No se requiere modificar BL-1.0 ni IP-1.0 para autorizar PR-F0-01.**
