# F12-E2B3K — Residual Query Migration (Phase 1)

**Fecha:** 2026-06-28  
**Referencia:** F12-E2B3H (menu/roles smoke), navegación real Platform Admin  
**Alcance:** Migrar callers activos `execute_query(str)` → `TextClause` — sin cambios de arquitectura, contratos HTTP ni lógica de negocio

---

## 1. Resumen ejecutivo

Durante navegación Platform Admin (`superadmin` / tenant list / auditoría) se observaban **31 warnings** `[QUERY] DEPRECATED` por ciclo. Tras Phase 1:

| Métrica | Antes | Después |
|---------|------:|--------:|
| `[QUERY] DEPRECATED` — Platform Admin smoke | **31** | **0** |
| `[QUERY] DEPRECATED` — Tenant Admin (`usuarios`, `roles`) | **0–2** | **0** |
| `[QUERY] DEPRECATED` — smoke extendido Platform + Shared | — | **0** |
| Callers migrados (Phase 1) | — | **47** |

**Patrón aplicado:** helper `qmark_sql_text()` en `query_helpers.py` — convierte SQL legacy con `?` a `sqlalchemy.text().bindparams()` (`TextClause`), equivalente al branch string de `execute_query` **sin** emitir warning.

**No modificado:** `queries_async.py`, Connection Resolver, Database Router, repositorios ya en Core/`text()`.

---

## 2. Inventario previo (callers activos en smoke)

### 2.1 Platform Admin — emisores confirmados en runtime

| ID | Archivo | Función / trigger HTTP | Warnings/ciclo |
|----|---------|------------------------|---------------:|
| QK-01 | `superadmin_usuario_service.py` | `GET /superadmin/usuarios/` (count + data + N×roles + N×cliente ADMIN) | **~22** |
| QK-02 | `superadmin_auditoria_service.py` | `GET /superadmin/auditoria/autenticacion/` | **~2–24*** |
| QK-03 | `superadmin_auditoria_service.py` | `GET /superadmin/auditoria/sincronizacion/` | **~4** |
| QK-04 | `superadmin_auditoria_service.py` | `GET /superadmin/auditoria/estadisticas/` | **~6** |
| QK-05 | `cliente_service.py` | `GET /clientes/` (unicidad subdominio/código en otros flujos) | **~4** |

\*Ventana de logs acumulativa; tras migración: **0** por endpoint aislado.

### 2.2 Tenant Admin — emisores en smoke Shared

| ID | Archivo | Trigger HTTP | Estado pre |
|----|---------|--------------|------------|
| QK-10 | `user_service.py` | `GET /usuarios/`, mutaciones rol, lookups `?` | string residual |
| QK-11 | `permiso_service.py` | `PUT /permisos/roles/{rol}/menus/{menu}/` | string |
| QK-12 | `rol_service.py` | `GET /roles/` | **ya `text()`** (E2B3H) |

### 2.3 Onboarding / Dedicated provisioning

| Área | Estado pre-smoke |
|------|------------------|
| `tenant_provisioning_repository.py` | **Stmt Core** — sin warning |
| `dedicated_provisioning_orchestrator.py` | **ya `text()`** |
| Onboarding services | Sin `execute_query(str)` en paths smoke |

### 2.4 Residual fuera de Phase 1 (no emitido en smoke validado)

| Módulo | ~call sites string | Notas |
|--------|-------------------:|-------|
| `modulos/*_service.py` | ~32 | Catálogo `/modulos-v2` — mayoría ya `text()`/`select()` |
| `menus/menu_service.py`, `area_service.py` | ~17 | Constantes `sql_constants` — Phase 2 |
| `core/auth/*`, `permission_*` | ~10 | Startup / no request-path smoke |
| `active_sessions_read_service.py` | ~10 | IAM V2 — revisar Phase 2 |
| ERP queries (`inv/*`, etc.) | >200 | Fuera alcance admin |

---

## 3. Clasificación por módulo (impacto Phase 1)

| Módulo | Callers migrados | Impacto warnings |
|--------|----------------:|------------------|
| Superadmin usuarios | 14 | **P0** — listado global |
| Superadmin auditoría | 10 | **P0** — auth/sync/stats |
| Users (tenant) | 14 | **P1** — admin tenant |
| RBAC permiso | 4 | **P2** — mutación permisos menú |
| Tenant cliente | 2 | **P1** — unicidad + onboarding adjacente |
| Tenant config | 3 | **P2** — config tenant |
| **Infra helper** | 1 función | Habilitador |
| **Total** | **47** | — |

---

## 4. Implementación

### 4.1 Helper (única adición infra)

```python
# app/infrastructure/database/query_helpers.py
def qmark_sql_text(sql: str, params: Optional[Union[tuple, list]] = None) -> TextClause
```

Convierte `?` → `:p0`, `:p1`, … y retorna `text(...).bindparams(...)`.

### 4.2 Archivos modificados

| Archivo | Callers migrados |
|---------|----------------:|
| `app/infrastructure/database/query_helpers.py` | +`qmark_sql_text` |
| `app/modules/superadmin/application/services/superadmin_usuario_service.py` | 14 |
| `app/modules/superadmin/application/services/superadmin_auditoria_service.py` | 10 |
| `app/modules/users/application/services/user_service.py` | 14 |
| `app/modules/rbac/application/services/permiso_service.py` | 4 |
| `app/modules/tenant/application/services/cliente_service.py` | 2 |
| `app/modules/tenant/application/services/tenant_service.py` | 3 |
| `tests/unit/test_superadmin_auditoria_datetime_sql.py` | mocks TextClause |
| `tests/unit/test_qmark_sql_text_f12_e2b3k.py` | nuevo |

---

## 5. Validación

### 5.1 Smoke HTTP

| Plano | Flujos | HTTP | `[QUERY] DEPRECATED` |
|-------|--------|:----:|:--------------------:|
| Platform | login, me, menu, superadmin/usuarios, auditoría (auth/sync/stats), clientes | 200 | **0** |
| Shared (Tenant Admin) | login, me, menu, permissions, org, branding, usuarios, roles, sessions, refresh, logout | 200 | **0** |

### 5.2 Tests unitarios

```
tests/unit/test_qmark_sql_text_f12_e2b3k.py           2 passed
tests/unit/test_superadmin_auditoria_datetime_sql.py  8 passed
tests/unit/test_menu_empresa_scope.py                 6 passed (regresión E2B3H)
```

---

## 6. Riesgos identificados

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| Tests que mockean `execute_query(query, params)` con `str` | Baja | Actualizado auditoría datetime SQL |
| SQL dinámico con conteo variable de `?` | Baja | Mismo algoritmo que branch legacy en `queries_async` |
| Residual `modulos/` / `menus/` en rutas no smokeadas | Media | Phase 2 — catálogo platform |
| `execute_auth_query(str)` no emite `[QUERY] DEPRECATED` | Info | Fuera alcance (otro entry point) |

---

## 7. Conclusión

Phase 1 elimina **100%** de los warnings `[QUERY] DEPRECATED` observados en navegación real Platform Admin y Tenant Admin validada. El guard en `queries_async.py` se mantiene para deuda residual ERP/catálogo no ejecutada en este smoke.

**Phase 2 (fuera de alcance):** `modulo_*_service`, `menu_service`, `area_service`, `active_sessions_read_service`, queries ERP.

**Detenido** según instrucción — sin continuar automáticamente.
