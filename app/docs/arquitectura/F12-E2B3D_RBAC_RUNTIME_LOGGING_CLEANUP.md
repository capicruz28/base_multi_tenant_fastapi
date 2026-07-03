# F12-E2B3D — RBAC Runtime Logging Cleanup

**Fecha:** 2026-06-28  
**Referencia:** F12-E2B3A (R-14–R-16; ~24 INFO `rbac` por sesión smoke tenant)  
**Alcance:** Solo emisión de logs en `app/core/authorization/rbac.py`  
**Sin cambios:** RBAC, PermissionResolver, PermissionCatalog, Permission Sync, `AuthorizationError`, lógica de `require_permission()`, contratos HTTP, OpenAPI, Session Management, permisos, roles

---

## 1. Resumen ejecutivo

| Métrica | Antes (F12-E2B3A) | Después (F12-E2B3D) |
|---------|-------------------|---------------------|
| `rbac` INFO `Validando permiso…` / sesión smoke tenant | **~8×** | **0** |
| `rbac` INFO `Permiso … autorizado` | **~8×** | **0** |
| `rbac` INFO `detectado como SUPER/TENANT ADMIN` | **~8×** | **0** |
| `rbac` INFO total (runtime request) | **~24+** | **0** |
| `rbac` WARNING acceso denegado (403 real) | según flujo | **sin cambio semántico** |
| HTTP smoke Platform + Shared + Dedicated | 200 | **200** (sin cambios) |
| Permisos / menú / respuestas | baseline | **idénticos** |

Se introdujeron helpers de política y se cableó `ENABLE_AUTH_VERBOSE` para diagnóstico. Ninguna validación de permisos ni respuesta HTTP fue alterada.

---

## 2. Inventario de logs (pre-cambio)

### 2.1 `get_user_type()`

| # | Nivel | Mensaje (patrón) | Clasificación |
|---|-------|------------------|---------------|
| R1 | DEBUG | Detectando tipo / sin roles | **B** Diagnóstico |
| R2 | INFO | `detectado como SUPER ADMIN` | **C** Ruido (×N por check) |
| R3 | INFO | `detectado como TENANT ADMIN` | **C** Ruido |
| R4 | INFO | `detectado como USUARIO NORMAL` | **C** Ruido |

### 2.2 `has_permission()`

| # | Nivel | Mensaje | Clasificación |
|---|-------|---------|---------------|
| R5 | DEBUG | Super Admin acceso completo / permiso explícito | **B** |
| R6 | WARNING | `[RBAC_DEBUG]` (flag `ENABLE_RBAC_TRACE`) | **B** (ya gateado) |
| R7 | WARNING | `NO tiene permiso` | **C** Ruido (duplica denegación en dependency) |

### 2.3 Dependencies (`require_permission`, `RequirePermission`, etc.)

| # | Nivel | Mensaje | Clasificación |
|---|-------|---------|---------------|
| R8 | INFO | `Validando permiso '…'` | **C** Ruido (~1×/endpoint protegido) |
| R9 | WARNING | `Intento de acceso sin permiso` | **A** Acceso denegado |
| R10 | INFO | `Permiso '…' autorizado` | **C** Ruido |
| R11 | INFO | `Validando Super/Tenant Admin` / autorizado | **B/C** |
| R12 | WARNING | Super/Tenant Admin denegado | **A** |

### 2.4 Startup (`initialize_authorization_system`)

| # | Nivel | Mensaje | Tratamiento |
|---|-------|---------|-------------|
| R13 | INFO | Inicialización autorización | **Sin cambio** (una vez al arranque) |
| R14 | ERROR | Config inválida | **A** Sin cambio |

**Volumen F12-E2B3A:** por endpoint con `require_permission` (~usuarios, roles): **3 INFO** (`Validando` + `detectado` + `autorizado`) → **~10–12 líneas** en `GET /usuarios/` y `GET /roles/`.

---

## 3. Política implementada

### 3.1 Helpers (solo logging)

```python
_rbac_auth_verbose()   → settings.ENABLE_AUTH_VERBOSE
_rbac_log_diagnostic() → logger.info si verbose (elevación super/tenant admin, detección tipo)
_rbac_log_check()      → logger.debug (validación/autorización exitosa, checks repetitivos)
_rbac_log_denied()     → logger.warning (acceso denegado — permanente)
```

### 3.2 Matriz de emisión (runtime, `LOG_LEVEL=INFO`, verbose OFF)

| Evento | Emisión |
|--------|---------|
| **A** `Intento de acceso sin permiso` / Super-Tenant Admin denegado | **WARNING** |
| **A** ERROR configuración / excepción | **ERROR** (sin cambio) |
| **B** Detección SUPER/TENANT ADMIN, acceso Super Admin OK | INFO solo si `ENABLE_AUTH_VERBOSE=true` |
| **C** `Validando permiso…`, `Permiso autorizado`, `NO tiene permiso` interno | **DEBUG** (silencio en INFO) |
| **C** `detectado como USUARIO NORMAL` | **DEBUG** |
| `[RBAC_DEBUG]` | Sin cambio — `ENABLE_RBAC_TRACE` |
| `[IMPERSONATE-AUTH]` en `require_super_admin` | Sin cambio — `ENABLE_IMPERSONATE_DIAG` |
| Startup `initialize_authorization_system` | INFO una vez — fuera de alcance runtime |

### 3.3 Sin cambios funcionales

- `has_permission`, `get_user_type`, `require_permission`, `AuthorizationError` — **misma lógica y mismos HTTP 403**
- `ENABLE_RBAC_TRACE` — **sin cambio**
- Otros módulos RBAC (`permission_startup`, `permission_sync`, `menu_permission_resolver`) — **fuera de alcance**

---

## 4. Validación obligatoria

### 4.1 Unit tests

```
tests/unit/test_rbac_runtime_logging_f12_e2b3d.py — 3 passed
```

Casos: éxito sin INFO; denegación solo WARNING; detección SUPER ADMIN con verbose ON.

### 4.2 Smoke runtime (`fastapi_backend`, flags default OFF)

Endpoints verificados por plano:

| Plano | login | me | menu | permissions/me | usuarios | roles | HTTP |
|-------|------:|---:|-----:|---------------:|---------:|------:|------|
| **Platform** | 200 | 200 | 200 | 200 | — | — | OK |
| **Shared `acme`** | 200 | 200 | 200 | 200 | **200** | **200** | OK |
| **Dedicated `acce`** | 200 | 200 | 200 | 200 | **200** | **200** | OK |

Permisos smoke tenant: `org.empresa.leer`, `core.app.acceder` presentes; `tenant.cliente.crear` ausente. Menú: 3 módulos (ORG, INV, SYS_ADMIN).

### 4.3 Conteo logs `authorization.rbac` (ventana smoke extendido)

| Patrón | F12-E2B3A (tenant, sesión) | F12-E2B3D |
|--------|---------------------------|-----------|
| INFO `Validando permiso` | ~8 | **0** |
| INFO `autorizado` | ~8 | **0** |
| INFO `detectado como` | ~8 | **0** |
| WARNING `Intento de acceso` (403 real en smoke) | 0 | **0** |
| INFO total runtime | ~24+ | **0** |

Con `LOG_LEVEL=INFO`, trazas DEBUG de checks exitosos **no aparecen** (comportamiento esperado). Con `LOG_LEVEL=DEBUG` reaparecen sin elevar ruido operacional.

---

## 5. Activación diagnóstico (desarrollo)

```env
ENABLE_AUTH_VERBOSE=true
# opcional para ver checks exitosos por request:
LOG_LEVEL=DEBUG
```

- **Verbose ON:** INFO de detección SUPER/TENANT ADMIN y acceso Super Admin autorizado.
- **DEBUG ON:** además `Validando permiso`, `Permiso autorizado`, `NO tiene permiso` interno.
- **Denegaciones reales:** siempre WARNING con verbose OFF.

`ENABLE_RBAC_TRACE=true` sigue activando `[RBAC_DEBUG]` en `has_permission` (sin cambio).

---

## 6. Clasificación post-implementación

| Clase | Tratamiento |
|-------|-------------|
| **A — Operacional obligatorio** | WARNING denegación; ERROR sin cambio |
| **B — Diagnóstico** | INFO solo si `ENABLE_AUTH_VERBOSE=true` |
| **C — Ruido repetitivo** | DEBUG (`_rbac_log_check`) |

---

## 7. Referencias

- F12-E2B1 — infraestructura flags
- F12-E2B3A — auditoría residual (R-14–R-16, G-6 RBAC)
- F12-E2B3B — QueryAuditor cleanup
- F12-E2B3C — Menu logging cleanup

**F12-E2B3D RBAC Runtime Logging Cleanup cerrado.** No se continúa con ORG_SESSION_SCOPE ni IMPERSONATION_TRACE.
