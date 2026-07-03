# F12-E2B3G — ORG Session Scope Logging Cleanup

**Fecha:** 2026-06-28  
**Referencia:** F12-E2B1 (política opt-in diagnóstico), F12-E2B3E (L-70–L-73, §5.3)  
**Alcance:** Solo `app/core/tenant/session_scope.py` + tests unitarios  
**Sin cambios:** resolución session scope, tenant/empresa context, JWT, IAM, auth, RBAC, contratos HTTP, OpenAPI, BD, Redis

---

## 1. Resumen ejecutivo

| Métrica | Antes (F12-E2B3E) | Después (F12-E2B3G) |
|---------|-------------------|---------------------|
| Líneas `[ORG-*]` por `GET /org/empresa` (Shared) | **~5** | **0** (flag OFF) |
| Líneas `[ORG-*]` ciclo smoke Shared completo | **~5** | **0** (flag OFF) |
| Líneas `[ORG-*]` con `ENABLE_AUTH_VERBOSE=true` | N/A (emitía por `ENVIRONMENT=development`) | **5** (mismos mensajes) |
| HTTP smoke Platform + Shared | 200 | **200** (sin cambios) |
| Session scope / empresa resolution | baseline | **idéntico** |

Se reemplazó el gate `ENVIRONMENT=development` por **`ENABLE_AUTH_VERBOSE`** (flag existente F12-E2B1). Toda la telemetría ORG queda opt-in; ningún evento operacional obligatorio se eliminó (no existían en este módulo).

---

## 2. Inventario completo

Todos los emisores viven en `app/core/tenant/session_scope.py`.

| ID | Función | Prefijo | Nivel | Trigger típico | Clasificación |
|----|---------|---------|-------|----------------|---------------|
| O-01 | `_log_org_session_scope` | `[ORG-SESSION-SCOPE]` | INFO | `require_session_cliente_id` (deps ORG/INV) | **C** Diagnóstico |
| O-02 | `_log_org_scope_policy` | `[ORG-SCOPE-POLICY]` | INFO | `require_company_scope_if_needed` | **C** Diagnóstico |
| O-03 | `log_org_erp_session` | `[ORG-ERP-SESSION]` | INFO | `org_deps.py` tras validación router ERP | **C** Diagnóstico |
| O-04 | `log_org_session_empresa` | `[ORG-SESSION-EMPRESA]` | INFO | services company-scoped (sucursal, cargo, …) | **C** Diagnóstico |
| O-05 | `log_org_company_scope` | `[ORG-COMPANY-SCOPE]` | INFO | services company-scoped + `company_scope.py` | **C** Diagnóstico |
| O-06 | `log_org_tenant_scope` | `[ORG-TENANT-SCOPE]` | INFO | `empresa_service` list/create tenant-wide | **C** Diagnóstico |
| O-07 | `log_org_assert_tenant` | `[ORG-ASSERT-TENANT]` | INFO | defensa cross-tenant post-query | **C** Diagnóstico |
| O-08 | `log_org_empresa_scope` | `[ORG-EMPRESA-SCOPE]` | INFO | CRUD/detalle `org_empresa` | **C** Diagnóstico |
| O-09 | `log_org_assert_empresa` | `[ORG-ASSERT-EMPRESA]` | INFO | defensa en profundidad post-query | **C** Diagnóstico |
| O-10 | `log_org_hybrid_scope` | `[ORG-HYBRID-SCOPE]` | INFO | lectura híbrida parámetros | **C** Diagnóstico |
| O-11 | `log_org_param_precedence` | `[ORG-PARAM-PRECEDENCE]` | INFO | merge global + override parámetros | **C** Diagnóstico |
| O-12 | `log_org_param_global` | `[ORG-PARAM-GLOBAL]` | INFO | parámetro tenant-wide | **C** Diagnóstico |
| O-13 | `log_org_param_empresa` | `[ORG-PARAM-EMPRESA]` | INFO | override parámetro por empresa | **C** Diagnóstico |

**Callers externos (sin modificar):** `org_deps.py`, `empresa_service.py`, `sucursal_service.py`, `departamento_service.py`, `cargo_service.py`, `centro_costo_service.py`, `parametro_service.py`, `company_scope.py`.

**Eventos operacionales INFO en este módulo:** ninguno — todas las entradas son telemetría de depuración session scope introducida en Etapa A ORG/INV.

---

## 3. Clasificación y política aplicada

### 3.1 Gate anterior (pre-fix)

```python
if settings.ENVIRONMENT != "development":
    return
```

Emitía INFO en **todo** runtime `development` con flags diagnósticas OFF → incumplía política F12-E2B1 (“toda traza diagnóstica opt-in”).

### 3.2 Gate nuevo (F12-E2B3G)

```python
def _org_scope_diag_enabled() -> bool:
    return settings.ENABLE_AUTH_VERBOSE
```

Cada función O-01…O-13:

```python
if not _org_scope_diag_enabled():
    return
# logger.info(...) — sin cambios en mensaje, formato ni parámetros
```

### 3.3 Justificación de flag

| Flag candidata | Decisión |
|----------------|----------|
| `ENABLE_AUTH_VERBOSE` | **Reutilizada** — telemetría de contexto de sesión/autenticación ERP |
| `ENABLE_MIDDLEWARE_TRACE` | Descartada — orientada a TenantMiddleware/host |
| `ENABLE_ORG_SCOPE_TRACE` (sugerida E2B3E) | **No creada** — instrucción explícita de no añadir flags innecesarias |

### 3.4 Matriz de emisión

| `ENABLE_AUTH_VERBOSE` | O-01…O-13 |
|----------------------|-----------|
| `false` (default `.env.docker`) | **silencio** |
| `true` | INFO (texto idéntico pre-fix en development) |

Nivel de log: **INFO** cuando se emite (sin degradar a DEBUG). Solo cambia **cuándo** se emite.

---

## 4. Diff de comportamiento

| Aspecto | Antes | Después |
|---------|-------|---------|
| Condición emisión | `ENVIRONMENT == development` | `ENABLE_AUTH_VERBOSE == true` |
| Prod (`ENVIRONMENT=production`) | 0 líneas ORG | 0 líneas ORG |
| Dev + flags OFF | **~5/ciclo** (ruido) | **0** |
| Dev + `ENABLE_AUTH_VERBOSE=true` | ~5/ciclo | **~5/ciclo** (igual) |
| Lógica `resolve_session_cliente_id` | sin cambio | sin cambio |
| Lógica `require_company_scope_if_needed` | sin cambio | sin cambio |
| HTTP / JWT / empresa activa | sin cambio | sin cambio |

---

## 5. Validación obligatoria

### 5.1 Unit tests

```text
tests/unit/test_org_session_scope_logging_f12_e2b3g.py — 6 passed
tests/unit/test_org_session_scope.py — 5 passed (regresión funcional)
```

| Test | Resultado |
|------|-----------|
| O-01/O-02/O-03/O-06 sin log con verbose OFF | PASS |
| O-01/O-06 emiten INFO con verbose ON | PASS |
| Resolución impersonation / company scope | PASS (sin regresión) |

### 5.2 Smoke HTTP (`LOG_LEVEL=INFO`, flags diagnósticas OFF)

| Plano | Script | Resultado |
|-------|--------|-----------|
| **Platform** | `http_smoke_platform_rbac.py` | **passed** — login, me, menu, permissions, refresh |
| **Shared** | `http_smoke_tenant_rbac.py` (`acme`) | **passed** — login, org/empresa, empresa/cambiar, me, menu, refresh, permissions |
| **Dedicated** | `http_smoke_tenant_rbac.py` (`acce`) | **401** login — credencial smoke (limitación E2B3E); paridad código |

Flujos verificados en Platform + Shared: login, auth/me, auth/menu, permissions/me, org/empresa, empresa/cambiar, refresh.

### 5.3 Conteo `[ORG-*]`

| Escenario | Ventana | Conteo |
|-----------|---------|-------:|
| **Antes** — dev + verbose OFF (F12-E2B3E) | smoke Shared + `GET /org/empresa` | **~5** |
| **Después** — dev + verbose OFF | mismo smoke | **0** |
| **Después** — dev + `ENABLE_AUTH_VERBOSE=true` | solo `GET /org/empresa` (acme) | **5** |

Detalle flag ON (5 líneas, formato idéntico al baseline):

1. `[ORG-SESSION-SCOPE]` (deps — 1ª resolución)  
2. `[ORG-SCOPE-POLICY]`  
3. `[ORG-ERP-SESSION]`  
4. `[ORG-SESSION-SCOPE]` (2ª resolución — dup pre-existente en pipeline)  
5. `[ORG-TENANT-SCOPE]` operation=list  

**Reducción runtime default:** **100%** de telemetría ORG en dev con flags OFF (−5 líneas/ciclo smoke Shared vs E2B3E).

### 5.4 Regresión funcional

| Verificación | Resultado |
|--------------|-----------|
| HTTP status smoke | Sin cambios |
| `org_empresa_listar` count=1 | OK |
| `empresa_cambiar` 400 already_active | OK (esperado) |
| Permisos / menú | Idénticos |

---

## 6. Riesgos

| Riesgo | Nivel | Mitigación |
|--------|-------|------------|
| Depuración session scope sin flag | Bajo | `ENABLE_AUTH_VERBOSE=true` en entorno local |
| Pérdida de trazas en prod | Ninguno | Pre-fix ya silenciaba prod vía `ENVIRONMENT` |
| Confusión AUTH vs ORG scope | Bajo | Documentado; flag compartida es coherente (contexto sesión) |
| Dedicated no smokeado runtime | Bajo | Mismos helpers; credencial onboarding pendiente |

---

## 7. Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `app/core/tenant/session_scope.py` | Helper `_org_scope_diag_enabled()` + gate en O-01…O-13 |
| `tests/unit/test_org_session_scope_logging_f12_e2b3g.py` | **Nuevo** — política verbose ON/OFF |
| `app/docs/arquitectura/F12_E2B3G_ORG_SESSION_SCOPE_LOGGING_CLEANUP.md` | **Nuevo** — este informe |

---

## 8. Fuera de alcance (documentado, no corregido)

| Familia | Origen | Notas |
|---------|--------|-------|
| AUTH narrativo | `auth_service.py`, `endpoints.py` | `[AUTH]`, `[LOGIN-V2]`, `[REFRESH-MOBILE]` |
| `[IMPERSONATION-TRACE]` | cerrado F12-E2B3F | gate `ENABLE_IMPERSONATE_DIAG` |
| `[QUERY] DEPRECATED` | `queries_async.py` | deuda migración SQL |
| `[MENU_USUARIO]` Inicio/Fin | E2B3C | 2 INFO/menu aceptado |
| `[ROLES-PAGINADOS]` | listados admin | futura fase |
| `Niveles calculados` dup | auth + identity_gateway | futura fase |
| Duplicado `[ORG-SESSION-SCOPE]`×2 | pipeline deps pre-existente | no refactor (alcance logging only) |

---

## 9. Conclusión

Session Scope deja de emitir telemetría diagnóstica permanente en `development` con flags OFF. Queda alineado con F12-E2B1 reutilizando `ENABLE_AUTH_VERBOSE`. Cero regresión funcional observada en smoke Platform + Shared.
