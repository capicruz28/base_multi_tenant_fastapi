# F12-E2B3F — Impersonation Trace Flag Alignment

**Fecha:** 2026-06-28  
**Referencia:** F12-E2B1 (política opt-in diagnóstico), F12-E2B3E (auditoría P1 L-80/L-81)  
**Alcance:** Solo `app/core/auth/impersonation_trace_diag.py` + tests unitarios  
**Sin cambios:** AuthService, refresh, logout, login, IAM, Session Management, RBAC, PermissionResolver, MenuResolver, QueryAuditor, frontend, OpenAPI, contratos REST, respuestas HTTP, BD, Redis, JWT, impersonation funcional, `impersonate_auth_diag.py`

---

## 1. Resumen ejecutivo

| Métrica | Antes (F12-E2B3E) | Después (F12-E2B3F) |
|---------|-------------------|---------------------|
| `[IMPERSONATION-TRACE]` con `ENABLE_IMPERSONATE_DIAG=false` | **~6** / ciclo Platform+Shared | **0** |
| `[IMPERSONATION-TRACE]` con `ENABLE_IMPERSONATE_DIAG=true` | N/A (flag ignorado) | **6** (mismos mensajes) |
| HTTP smoke Platform + Shared | 200 | **200** (sin cambios) |
| HTTP smoke Dedicated | 401 credencial | **401** (sin cambio — credencial smoke) |

Se añadió gate opt-in idéntico al patrón de `impersonate_auth_diag.py`. Mensajes, formato y parámetros de log **sin cambio**.

---

## 2. Causa raíz

`impersonation_trace_diag.py` fue introducido en RC2 como módulo de trazas `[IMPERSONATION-TRACE]` para flujos `POST /auth/refresh/` y `POST /auth/empresa/cambiar/`.

Desde F12-E2B1 la política oficial exige que **toda traza diagnóstica sea opt-in** vía flags de entorno. `impersonate_auth_diag.py` y el resto de flags (`HTTP_TRACE`, `REDIS_TRACE`, etc.) ya cumplían; **`impersonation_trace_diag.py` emitía `logger.info` incondicionalmente**, ignorando `settings.ENABLE_IMPERSONATE_DIAG`.

F12-E2B3E clasificó esto como **bug arquitectónico P1** (L-80, L-81): ruido INFO en runtime con todas las flags OFF.

---

## 3. Inventario de logs afectados

| ID | Función | Nivel | Prefijo | Trigger HTTP | Mensaje (patrón) |
|----|---------|-------|---------|--------------|------------------|
| T-01 | `log_impersonation_trace_request` | INFO | `[IMPERSONATION-TRACE]` | refresh, empresa/cambiar | `REQUEST endpoint=%s jwt_kind=%s http_status=pending is_impersonation=%s …` |
| T-02 | `log_impersonation_trace_response` | INFO | `[IMPERSONATION-TRACE]` | refresh, empresa/cambiar | `RESPONSE endpoint=%s http_status=%s request_is_impersonation=%s … emission_reason=%s` |

**Callers (sin modificar):** `app/modules/auth/presentation/endpoints.py` — refresh mobile, empresa/cambiar, refresh V2.

**Funciones auxiliares no gateadas (sin emisión):** `_claims_summary`, `decode_access_token_claims` — solo usadas cuando el flag está activo (early return antes de invocarlas en las funciones de log).

---

## 4. Diff de comportamiento

### 4.1 Implementación

```python
def _impersonate_trace_diag_enabled() -> bool:
    return settings.ENABLE_IMPERSONATE_DIAG

def log_impersonation_trace_request(...):
    if not _impersonate_trace_diag_enabled():
        return
    # … logger.info sin cambios …

def log_impersonation_trace_response(...):
    if not _impersonate_trace_diag_enabled():
        return
    # … logger.info sin cambios …
```

Patrón alineado con `impersonate_auth_diag.py` (`if not settings.ENABLE_IMPERSONATE_DIAG: return`). **No** se unificó código entre módulos.

### 4.2 Matriz de emisión

| `ENABLE_IMPERSONATE_DIAG` | T-01 REQUEST | T-02 RESPONSE |
|---------------------------|--------------|---------------|
| `false` (default) | **silencio** | **silencio** |
| `true` | INFO (texto idéntico pre-fix) | INFO (texto idéntico pre-fix) |

**Sin cambio funcional:** endpoints, status codes, tokens, JWT claims, impersonation, refresh rotation, logout.

---

## 5. Validación obligatoria

### 5.1 Unit tests

```text
tests/unit/test_impersonation_trace_diag_f12_e2b3f.py — 4 passed
```

| Test | Resultado |
|------|-----------|
| `test_request_no_log_when_flag_off` | PASS — `logger.info` no invocado |
| `test_response_no_log_when_flag_off` | PASS |
| `test_request_emits_info_when_flag_on` | PASS — prefijo `[IMPERSONATION-TRACE]` en args |
| `test_response_emits_info_when_flag_on` | PASS |

### 5.2 Smoke HTTP (`LOG_LEVEL=INFO`, ventana ~15 s post-smoke)

| Plano | Script | Credencial | Resultado |
|-------|--------|------------|-----------|
| **Platform** | `http_smoke_platform_rbac.py` | `superadmin` / `admin123` | **passed** — login, me, menu, permissions, refresh |
| **Shared** | `http_smoke_tenant_rbac.py` | `acme` / `admin123` | **passed** — login, org/empresa, empresa/cambiar, me, menu, refresh, permissions |
| **Dedicated** | `http_smoke_tenant_rbac.py` | `acce` / `admin123` | **login 401** — credencial distinta al seed (misma limitación F12-E2B3E); paridad de código confirma mismos call sites |

Flujos cubiertos en Platform + Shared: **login**, **me**, **menu**, **permissions**, **refresh**, **empresa/cambiar** (400 already_active — esperado).

### 5.3 Conteo `[IMPERSONATION-TRACE]`

Condiciones: `fastapi_backend`, `ENVIRONMENT=development`, resto flags diagnósticas OFF.

| Escenario | Ciclo smoke | Conteo |
|-----------|-------------|-------:|
| **Antes** — `ENABLE_IMPERSONATE_DIAG=false` (F12-E2B3E) | Platform + Shared | **~6** |
| **Después** — `ENABLE_IMPERSONATE_DIAG=false` | Platform + Shared | **0** |
| **Después** — `ENABLE_IMPERSONATE_DIAG=true` (override temporal runtime) | Platform + Shared | **6** |

Detalle flag ON (6 líneas, formato idéntico al baseline E2B3E):

1. Platform refresh REQUEST  
2. Platform refresh RESPONSE (`emission_reason=refresh_token_rotation`)  
3. Shared empresa/cambiar REQUEST  
4. Shared empresa/cambiar RESPONSE (`http_status=400`, `rejected:La empresa indicada ya es…`)  
5. Shared refresh REQUEST  
6. Shared refresh RESPONSE  

### 5.4 Regresión funcional

| Área | Verificación |
|------|--------------|
| HTTP status smoke | Todos los steps OK en Platform y Shared |
| OpenAPI / contratos | Sin cambios de código en presentation |
| JWT / refresh / logout | Smoke refresh 200 en ambos planos |
| Impersonation funcional | Sin cambios — solo gate de log |

---

## 6. Riesgos

| Riesgo | Nivel | Mitigación |
|--------|-------|------------|
| Depuración RC impersonation sin flag | Bajo | Activar `ENABLE_IMPERSONATE_DIAG=true` en entorno de diagnóstico |
| Pérdida accidental de trazas en prod | Ninguno | Comportamiento deseado — prod default `false` |
| Regresión auth/refresh | Muy bajo | Early return antes de log; sin alteración de flujo HTTP |
| Dedicated no smokeado en runtime | Bajo | Mismos call sites vía `endpoints.py`; credencial onboarding pendiente |

---

## 7. Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `app/core/auth/impersonation_trace_diag.py` | Gate `_impersonate_trace_diag_enabled()` + early return en T-01/T-02 |
| `tests/unit/test_impersonation_trace_diag_f12_e2b3f.py` | **Nuevo** — política flag ON/OFF |
| `app/docs/arquitectura/F12_E2B3F_IMPERSONATION_TRACE_ALIGNMENT.md` | **Nuevo** — este informe |

---

## 8. Fuera de alcance (documentado, no corregido)

Residuales identificados en F12-E2B3E — **sin cambio en esta tarea**:

| Familia | Ejemplo | Flag sugerido |
|---------|---------|---------------|
| AUTH narrativo | `[AUTH] Intento de login`, `[LOGIN-V2]` | `ENABLE_AUTH_VERBOSE` / futura limpieza |
| ORG session scope | `[ORG-*]` INFO | `ENVIRONMENT=development` |
| SQL legacy | `[QUERY] DEPRECATED` | Migración queries_async |
| Listados admin | `[ROLES-PAGINADOS]` | Futura fase |
| Niveles duplicados | `Niveles calculados` auth + gateway | Futura fase |
| Menu residual | `[MENU_USUARIO] Inicio/Fin` | Aceptado post E2B3C |

---

## 9. Conclusión

`impersonation_trace_diag.py` queda alineado con la política F12-E2B1: **cero trazas `[IMPERSONATION-TRACE]` con flag OFF**; trazas completas e idénticas con `ENABLE_IMPERSONATE_DIAG=true`. Bug P1 de F12-E2B3E cerrado.
