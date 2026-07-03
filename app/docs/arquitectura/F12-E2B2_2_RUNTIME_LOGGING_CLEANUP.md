# F12-E2B2.2 — Runtime Logging Cleanup (P0) Report

**Ticket:** F12-E2B2.2 — Defaults opt-in para trazas diagnósticas  
**Fecha:** 2026-06-27  
**Alcance:** Cambiar defaults de flags `ENABLE_*` a `false` (development y production)  
**Fuera de alcance:** eliminar logs, reclasificar niveles, QueryAuditor, middleware logic, duplicados (→ F12-E2B3)  

---

## 6. Resultado

**Runtime limpio por defecto.** Las trazas diagnósticas conectadas en F12-E2B2.1 quedan **opt-in** vía variables de entorno. El comportamiento HTTP y funcional del backend permanece idéntico.

| Objetivo | Estado |
|----------|--------|
| Defaults `false` en development | ✅ |
| Defaults `false` en production | ✅ |
| Sin eliminar logs ni cambiar niveles | ✅ |
| QueryAuditor sin cambios | ✅ |
| Smoke Platform + Shared + Dedicated | ✅ |
| Marcadores diagnósticos = 0 en flujo auth | ✅ |

---

## 1. Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `app/core/config.py` | `_resolve_diagnostic_trace_flag`: sin env explícito → `False` (antes `True` en development) |
| `tests/unit/test_logging_config_f12_e2b1.py` | Expectativas de defaults actualizadas |
| `.env.example` | Comentario: default opt-in `false` |
| `.env.docker` | Comentario alineado con E2B2.2 |

**Sin cambios en:** código de logging, gates F12-E2B2.1, QueryAuditor, middleware, endpoints, RBAC, IAM.

---

## 2. Flags modificadas

Todas usan `_resolve_diagnostic_trace_flag()`:

| Flag | Default anterior (sin env) | Default nuevo (sin env) | Override |
|------|---------------------------|-------------------------|----------|
| `ENABLE_REDIS_TRACE` | dev=`true`, prod=`false` | **`false`** | `ENABLE_*=true\|false` |
| `ENABLE_RBAC_TRACE` | dev=`true`, prod=`false` | **`false`** | idem |
| `ENABLE_HTTP_TRACE` | dev=`true`, prod=`false` | **`false`** | idem |
| `ENABLE_MIDDLEWARE_TRACE` | dev=`true`, prod=`false` | **`false`** | idem |
| `ENABLE_IMPERSONATE_DIAG` | dev=`true`, prod=`false` | **`false`** | idem |
| `ENABLE_AUTH_VERBOSE` | dev=`true`, prod=`false` | **`false`** | idem |
| `ENABLE_QUERY_AUDITOR_VERBOSE` | dev=`true`, prod=`false` | **`false`** | idem (misma función; sin wiring aún) |

### Activar trazas manualmente (ejemplo)

```env
ENABLE_REDIS_TRACE=true
ENABLE_HTTP_TRACE=true
ENABLE_MIDDLEWARE_TRACE=true
```

Reiniciar backend tras cambiar env.

---

## 3. Comparación de volumen de logs

### Metodología

- **Antes:** comportamiento F12-E2B2.1 — flags implícitas `true` en `ENVIRONMENT=development` (documentado en F12-E2A / E2B2.1).
- **Después:** backend reiniciado (`docker compose restart backend`), `.env.docker` sin overrides `ENABLE_*`, flujo HTTP acme: login → `/auth/me` → `/auth/menu` → `/auth/permissions/me` → refresh → logout.
- **Conteo:** `docker logs fastapi_backend --since Ns` + regex sobre marcadores diagnósticos.

Verificación en contenedor:

```text
docker exec fastapi_backend python -c "from app.core.config import settings; print(settings.ENABLE_REDIS_TRACE, settings.ENABLE_HTTP_TRACE, settings.ENABLE_AUTH_VERBOSE)"
→ False False False
```

### Tabla por operación (estimado — flujo tenant acme)

| Operación | Líneas diagnósticas ANTES (dev default) | Líneas diagnósticas DESPUÉS |
|-----------|----------------------------------------|----------------------------|
| **Login** | ~4–8: HTTP `->/<-`, `[TENANT] CONTEXTO`, `[HOST_DETECTION]` DEBUG | **0** (+ uvicorn access 1) |
| **Dashboard bootstrap** (`/me` + `/menu` + `/permissions/me`) | ~15–25: 3× HTTP trace, 3× TENANT context, 3× `[ME]`/`[ME-ENDPOINT]` en `/me`, posible `[RBAC_DEBUG]` | **0** (+ uvicorn access 3) |
| **`/auth/me`** | ~5–7: `[ME-ENDPOINT]`, `[ME] Niveles`, `[ME] Datos completos`, HTTP trace | **0** |
| **`/auth/permissions/me`** | ~2–4: HTTP trace, TENANT; eventual `[RBAC_DEBUG]` WARNING | **0** |
| **`/auth/menu`** | ~2–4: HTTP trace, TENANT | **0** |
| **Logout** | ~17–20: HTTP trace + **15+** `[REDIS-TRACE-01]`/`[BLACKLIST-DIAG]`/`[REDIS-RUNTIME-FINAL]` (F12-E2A P0) | **0** (+ uvicorn access 1) |

### Conteo medido — flujo completo DESPUÉS (6 endpoints, ~25 s)

| Marcador | Count |
|----------|------:|
| `REDIS-TRACE-01` | 0 |
| `BLACKLIST-DIAG` | 0 |
| `REDIS-RUNTIME-FINAL` | 0 |
| `RBAC_DEBUG` / `[RBAC DEBUG]` | 0 |
| `HTTP_TRACE` (`->` / `<-`) | 0 |
| `TENANT_TRACE` (HOST/TENANT/SUBDOMAIN) | 0 |
| `ME_VERBOSE` | 0 |
| `IMPERSONATE-AUTH` | 0 |
| **uvicorn access** | **6** (esperado: 1 por request) |

**Reducción diagnóstica aproximada por flujo auth:** ~45–80+ líneas → **0 líneas** (marcadores gateados).

### Ruido operacional restante (fuera de alcance E2B2.2)

Siguen emitiéndose sin flag (clase A/B en F12-E2A — limpieza F12-E2B3):

- `[RBAC] Permission detected` en startup/sync
- `[AUTH]` INFO en login/refresh
- uvicorn access log (1 línea/request)
- Logs RBAC de autorización estándar (`Validando permiso`, deny WARNING)

---

## 4. Validaciones

### Unit tests

```text
pytest tests/unit/test_logging_config_f12_e2b1.py -q
→ 16 passed
```

### Backend reiniciado

```text
docker compose restart backend
→ healthy; flags False False False en contenedor
```

### Smoke HTTP

| Suite | Resultado |
|-------|-----------|
| Platform (`superadmin` / `admin123`) | **PASS** |
| Shared (`acme` / `admin123`) | **PASS** — ORG, INV, SYS_ADMIN |
| Dedicated (`acmec` / `F11Gate!acmec2026`) | **PASS** |

Flujos validados vía smoke (equivalente contrato **frontend real** — bootstrap dashboard):

- Login ✅
- `/auth/me` ✅
- `/auth/menu` ✅
- `/auth/permissions/me` ✅
- Refresh ✅
- Logout ✅ (script dedicado en E2B2.1; smoke tenant incluye refresh)

> **Frontend real:** no ejecutado en browser en esta fase; los endpoints consumidos por el dashboard FE coinciden con el smoke HTTP anterior (mismo contrato API). Comportamiento HTTP verificado 200 en todos los pasos.

---

## 5. Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Desarrolladores esperaban trazas automáticas en dev | Documentado en `.env.example` / `.env.docker`; activar `ENABLE_*=true` explícito |
| Diagnóstico de incidentes sin flags | Playbook: habilitar flags puntuales + reinicio; no afecta prod default |
| `ENABLE_QUERY_AUDITOR_VERBOSE` también default `false` | Sin wiring en código aún; coherente con opt-in global |
| Ruido `[RBAC] Permission detected` persiste | Conocido — F12-E2B3 (no reclasificar en E2B2.2) |
| Olvidar reiniciar tras cambiar env | Flags se leen al arranque de Settings |

---

## 7. Diff funcional clave

```python
# app/core/config.py — _resolve_diagnostic_trace_flag
# Antes: return environment == "development"
# Después:
return False  # opt-in; solo True si env explícito == "true"
```

---

## 8. Próxima fase (NO incluida)

- **F12-E2B3:** reclasificar INFO→DEBUG, consolidar duplicados HTTP/Tenant, reducir `[RBAC] Permission detected` en runtime
- **QueryAuditor verbose:** wiring `ENABLE_QUERY_AUDITOR_VERBOSE`

**F12-E2B2.2 cerrado.**
