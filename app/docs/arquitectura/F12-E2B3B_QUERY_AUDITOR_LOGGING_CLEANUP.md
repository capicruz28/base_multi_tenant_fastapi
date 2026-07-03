# F12-E2B3B — QueryAuditor Logging Cleanup

**Fecha:** 2026-06-28  
**Referencia:** F12-E2B3A (52× `[QUERY_AUDITOR]` WARNING en sesión normal)  
**Alcance:** Solo `app/core/security/query_auditor.py` — emisión de logs  
**Sin cambios:** validación multi-tenant, TD-08, IdentityScope, filtros, bloqueos producción, contratos HTTP

---

## 1. Resumen ejecutivo

| Métrica | Antes (F12-E2B3A) | Después (F12-E2B3B) |
|---------|-------------------|---------------------|
| `[QUERY_AUDITOR]` WARNING / sesión smoke | **~52** | **0** |
| `[QUERY_AUDITOR]` DEBUG / sesión smoke | 0 | 0 (flag OFF) |
| HTTP smoke Platform + Shared + Dedicated | 200 | **200** (sin cambios) |
| `SecurityError` en producción (query sin filtro) | Bloquea | **Bloquea** (sin cambios) |

Se cableó `ENABLE_QUERY_AUDITOR_VERBOSE` al emisor. Los falsos positivos **ENGINE_SCOPED** ya no generan WARNING.

---

## 2. Inventario de logs (pre-cambio)

| # | Línea | Nivel | Mensaje (patrón) | Clasificación |
|---|------:|-------|------------------|---------------|
| L1 | 94–96 | ERROR | `skip_validation sin ALLOW_TENANT_FILTER_BYPASS` | **A** Seguridad real |
| L2 | 102–104 | WARNING | `Validación omitida (ALLOW_TENANT_FILTER_BYPASS=True)` | **A** Seguridad real |
| L3 | 109 | DEBUG | Tabla global, omitiendo validación | **B** Diagnóstico |
| L4 | 120–122 | ERROR | Sin contexto tenant en producción | **A** Seguridad real |
| L5 | 128–130 | WARNING | Sin contexto tenant (desarrollo) | **B** Diagnóstico |
| L6 | 141–143 | WARNING | Tipo de query no reconocido | **B** Diagnóstico |
| L7 | 173–175 | DEBUG | Query Core por PK permitida | **B** Diagnóstico |
| L8 | 188–190 | DEBUG | Query Core con filtro tenant | **B** Diagnóstico |
| L9 | 194–197 | WARNING | Query Core **sin filtro explícito cliente_id** | **C** FP ENGINE_SCOPED / **B** ROW_SCOPED |
| L10 | 212–215 | WARNING | Query Core sin WHERE clause | **C** / **B** |
| L11 | 231–234 | ERROR | Error validando SQLAlchemy Core | **A** Seguridad real |
| L12 | 256–258 | ERROR | Error validando TextClause | **A** Seguridad real |
| L13 | 285–287 | DEBUG | Query string por PK permitida | **B** Diagnóstico |
| L14 | 302–304 | DEBUG | Query string con filtro tenant | **B** Diagnóstico |
| L15 | 308–311 | WARNING | Query string sin filtro explícito | **C** / **B** |
| L16 | 326–329 | WARNING | Query string sin WHERE clause | **C** / **B** |
| L17 | 369 | DEBUG | Error extrayendo nombre de tabla | **D** Ruido bajo |

**Volumen observado F12-E2B3A:** L9 + L15 dominantes (~42+22 líneas) en login/auth/deps sobre `usuario` / `usuario_rol` en Dedicated (ENGINE_SCOPED) y Shared.

---

## 3. Política implementada

### 3.1 Helpers (solo logging)

```python
_query_auditor_verbose()          → settings.ENABLE_QUERY_AUDITOR_VERBOSE
_is_engine_scoped_identity()      → IdentityGateway.resolve_identity_scope() == ENGINE_SCOPED
_log_query_auditor_diagnostic()   → logger.warning si verbose
_log_engine_scoped_expected()     → logger.debug si verbose (nunca WARNING)
```

### 3.2 Matriz de emisión

| Evento | Flag OFF | Flag ON (`ENABLE_QUERY_AUDITOR_VERBOSE=true`) |
|--------|----------|-----------------------------------------------|
| **A** ERROR bypass / prod sin contexto / error validación | ERROR | ERROR |
| **A** WARNING `ALLOW_TENANT_FILTER_BYPASS` | WARNING | WARNING |
| **B** Sin contexto dev, tipo desconocido, missing filter **ROW_SCOPED** | Silencio | WARNING |
| **C** Missing filter / sin WHERE **ENGINE_SCOPED** | Silencio | DEBUG (`ENGINE_SCOPED (esperado)`) |
| **B** DEBUG éxito (PK, filtro OK, tabla global) | DEBUG | DEBUG |

### 3.3 Sin cambios funcionales

- `return True` / `raise SecurityError` — **idénticos**
- `GLOBAL_TABLES`, `PK_LOOKUP_TABLES`, detección WHERE — **idénticos**
- Producción + `ENABLE_QUERY_TENANT_VALIDATION` — **sigue bloqueando**

---

## 4. Validación obligatoria

### 4.1 Unit tests

```
tests/unit/test_query_auditor_logging_f12_e2b3b.py — 6 passed
```

Casos: silencio default, WARNING verbose ROW_SCOPED, DEBUG verbose ENGINE_SCOPED, bloqueo producción intacto, bypass WARNING siempre.

### 4.2 Smoke runtime (`fastapi_backend`, flags default OFF)

| Plano | Endpoints | HTTP |
|-------|-----------|------|
| Platform | login → me → menu → permissions/me → logout | **200** |
| Shared `acme` | + usuarios + roles | **200** |
| Dedicated `acce` | + usuarios + roles | **200** |

### 4.3 Conteo `[QUERY_AUDITOR]` (ventana smoke ~4 s)

| Nivel | F12-E2B3A | F12-E2B3B |
|-------|-----------|-----------|
| WARNING | **52** | **0** |
| DEBUG | 0 | 0 |

Otros WARNING de la sesión (`queries_async DEPRECATED`, `menu_permission_resolver`, etc.) **fuera de alcance** E2B3B.

---

## 5. Activación diagnóstico (desarrollo)

En `.env.docker` / entorno local:

```env
ENABLE_QUERY_AUDITOR_VERBOSE=true
```

- **Shared (ROW_SCOPED):** reaparecen WARNING de queries sin `cliente_id` explícito.
- **Dedicated (ENGINE_SCOPED):** solo DEBUG con prefijo `ENGINE_SCOPED (esperado)` — nunca WARNING.

---

## 6. Clasificación post-implementación

| Clase | Tratamiento |
|-------|-------------|
| **A — Seguridad real** | Sin cambio (ERROR/WARNING permanentes) |
| **B — Diagnóstico** | WARNING solo si `ENABLE_QUERY_AUDITOR_VERBOSE=true` |
| **C — Falso positivo ENGINE_SCOPED** | DEBUG solo si verbose; silencio en operación normal |
| **D — Ruido** | DEBUG existente sin cambio |

---

## 7. Referencias

- F12-E2B1 — infraestructura flags
- F12-E2B2.2 — default flags `false`
- F12-E2B3A — auditoría residual (`R-29`)

**F12-E2B3B QueryAuditor Logging Cleanup cerrado.**
