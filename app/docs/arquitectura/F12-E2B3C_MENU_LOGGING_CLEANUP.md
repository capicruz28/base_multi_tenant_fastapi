# F12-E2B3C — Menu Logging Cleanup

**Fecha:** 2026-06-28  
**Referencia:** F12-E2B3A (R-20–R-23; ~35–45 líneas INFO por `GET /auth/menu` tenant)  
**Alcance:** Solo emisión de logs en:

- `app/modules/modulos/application/services/modulo_menu_service.py` (`obtener_menu_usuario`, `obtener_menu_impersonacion_tenant`)
- `app/modules/modulos/application/helpers/menu_transformer.py`

**Sin cambios:** permisos, RBAC, MenuResolver, PermissionResolver, contratos HTTP, OpenAPI, SQL, estructura del menú, frontend.

---

## 1. Resumen ejecutivo

| Métrica | Antes (F12-E2B3A) | Después (F12-E2B3C) |
|---------|-------------------|---------------------|
| `[MENU_USUARIO]` INFO / `GET /auth/menu` (tenant) | **~35–45** | **2** (Inicio + Fin) |
| `[MENU_USUARIO]` INFO / `GET /auth/menu` (platform elevated) | **~12** | **2** |
| `[MENU_USUARIO] … INCLUIDO` INFO por ítem | **~18×** | **0** (→ DEBUG) |
| `menu_transformer` INFO «Transformación completada» | **1×** | **0** (→ DEBUG) |
| HTTP smoke Platform + Shared + Dedicated | 200 | **200** (sin cambios) |
| Menú (`modulos_count`, códigos módulo) | baseline | **idéntico** |

Se introdujeron helpers de política de logging y se cableó `ENABLE_AUTH_VERBOSE` para diagnóstico. Ningún cálculo, query ni filtro de permisos fue alterado.

---

## 2. Inventario de logs MENU_USUARIO (pre-cambio)

### 2.1 `modulo_menu_service.py` — flujo `obtener_menu_usuario`

| # | Ubicación (aprox.) | Nivel previo | Mensaje (patrón) | Clasificación |
|---|-------------------|--------------|------------------|---------------|
| M1 | entrada | INFO | `Obteniendo menú para usuario …` | **C** Ruido (duplica inicio) |
| M2 | contexto | INFO | `Contexto is_super_admin=…` | **B** Diagnóstico |
| M3 | super_admin | INFO | `Elevado super_admin: N ítems` | **B** Diagnóstico |
| M4 | query permisos | INFO | `Ejecutando query de permisos …` | **B** Diagnóstico |
| M5 | query RAW | INFO | `Query RAW SQL generada / retornó …` | **B** Diagnóstico |
| M6 | permisos vacíos | WARNING | `No se encontraron permisos …` | **B** Diagnóstico |
| M7 | permisos | INFO | `Query de permisos retornó …` / `Permisos procesados …` | **B** Diagnóstico |
| M8 | roles | INFO | `Usuario … tiene N roles activos` | **B** Diagnóstico |
| M9 | por ítem | INFO | `Menú … INCLUIDO` / `excluido` / IDs inválidos | **C** Ruido (~18×/llamada) |
| M10 | resumen | INFO | `Resumen: X incluidos, Y excluidos` | **B** Diagnóstico |
| M11 | salida | INFO | `Menú obtenido: N módulos` | **C** Ruido (duplica fin) |
| M12 | impersonación | WARNING | `ADMIN_TENANT no encontrado` | **B** Diagnóstico |
| — | errores BD | ERROR | `Error de BD / inesperado` | **A** Operacional obligatorio |

### 2.2 `menu_transformer.py`

| # | Nivel previo | Mensaje | Clasificación |
|---|--------------|---------|---------------|
| T1 | INFO | `Transformación completada: N módulos` | **C** Ruido |
| T2 | *(ausente)* | `SP sin resultados` / fila sin IDs | **B** → DEBUG |
| T3 | *(ausente)* | `Fila sin modulo_id / menu_id` | **B** → DEBUG |

### 2.3 Volumen observado F12-E2B3A

- **~40 líneas** logger aplicación por llamada tenant a `/auth/menu`.
- **~18 líneas INFO** adicionales por cada ítem incluido (`INCLUIDO`).
- Platform (elevated): **~12 líneas** (sin bucle por ítem RBAC).

---

## 3. Política implementada

### 3.1 Helpers (solo logging)

```python
_menu_usuario_auth_verbose()           → settings.ENABLE_AUTH_VERBOSE
_menu_usuario_log_diagnostic()         → logger.info si verbose
_menu_usuario_log_diagnostic_warning() → logger.warning si verbose
_menu_usuario_log_item()               → logger.debug (siempre)
_menu_usuario_log_start()              → logger.info Inicio + monotonic()
_menu_usuario_log_finish()             → logger.info Fin modulos=N duracion_ms=X [modo=…]
```

### 3.2 Matriz de emisión (flags default OFF)

| Evento | `LOG_LEVEL=INFO`, verbose OFF | `ENABLE_AUTH_VERBOSE=true` |
|--------|-------------------------------|----------------------------|
| **A** Inicio proceso | INFO `[MENU_USUARIO] Inicio …` | INFO |
| **A** Fin proceso + módulos + `duracion_ms` + `modo` | INFO `[MENU_USUARIO] Fin …` | INFO |
| **B** Contexto, queries, roles, resumen, elevación | Silencio | INFO |
| **B** WARNING permisos/ADMIN_TENANT | Silencio | WARNING |
| **C** Por ítem (INCLUIDO/excluido/IDs) | Silencio | DEBUG (`LOG_LEVEL=DEBUG`) |
| **C** `menu_transformer` transformación | Silencio | DEBUG |
| **A** ERROR BD / excepción | ERROR / exception | Sin cambio |

Valores de `modo` en fin: `elevated`, `permisos`, `sin_catalogo`, `sin_menu_ids`, `sin_permisos`.

### 3.3 Sin cambios funcionales

- Queries SQLAlchemy / RAW, joins `rol_menu_permiso`, filtro `puede_ver`, elevación `is_super_admin`, transformación jerárquica — **idénticos**.
- Se eliminó código muerto redundante (`if not menu_ids` duplicado tras early return) — **solo rama inalcanzable**, sin efecto en runtime.

---

## 4. Validación obligatoria

### 4.1 Unit tests

```
tests/unit/test_menu_usuario_logging_f12_e2b3c.py — 2 passed
tests/unit/test_menu_transformer.py — 3 passed
```

Casos: solo Inicio+Fin con verbose OFF; mensaje diagnóstico `Contexto is_super_admin` con `ENABLE_AUTH_VERBOSE=true`.

### 4.2 Smoke runtime (`fastapi_backend`, flags default OFF)

Contenedor reiniciado; `LOG_LEVEL=INFO`, `ENABLE_AUTH_VERBOSE=False`.

| Plano | Smoke | `GET /auth/menu` | Menú |
|-------|-------|------------------|------|
| **Platform** | `run_platform_smoke` | **200**, `modulos_count=1` | OK |
| **Shared `acme`** | `run_tenant_smoke` | **200**, `modulos_count=3` (ORG, INV, SYS_ADMIN) | OK |
| **Dedicated `acce`** | `run_tenant_smoke` | **200**, `modulos_count=3` (ORG, INV, SYS_ADMIN) | OK |

Checks tenant (`ORG`, `SYS_ADMIN`, rutas `/app/org/…`, sin menús platform) — **todos OK**.

### 4.3 Conteo logs por llamada menú (ventana `--since` por smoke)

| Marcador | F12-E2B3A (tenant) | F12-E2B3C |
|----------|-------------------|-----------|
| `[MENU_USUARIO]` INFO | ~35–45 | **2** |
| `[MENU_USUARIO] INCLUIDO` | ~18 | **0** |
| `menu_transformer` INFO | 1 | **0** |
| Platform `[MENU_USUARIO]` INFO | ~12 | **2** |

Otros WARNING de la sesión (`menu_permission_resolver` SYS_ADMIN.* en Dedicated) — **fuera de alcance** E2B3C.

---

## 5. Activación diagnóstico (desarrollo)

En `.env.docker` / entorno local:

```env
ENABLE_AUTH_VERBOSE=true
# opcional para ver trazas por ítem:
LOG_LEVEL=DEBUG
```

- Reaparecen INFO de queries, roles, resumen y elevación.
- Por ítem (`INCLUIDO`, normalización IDs) solo en **DEBUG**.
- `menu_transformer` «Transformación completada» solo en **DEBUG**.

---

## 6. Clasificación post-implementación

| Clase | Tratamiento |
|-------|-------------|
| **A — Operacional obligatorio** | INFO Inicio/Fin; ERROR sin cambio |
| **B — Diagnóstico** | INFO/WARNING solo si `ENABLE_AUTH_VERBOSE=true` |
| **C — Ruido** | DEBUG (`_menu_usuario_log_item`, `menu_transformer`) |

---

## 7. Referencias

- F12-E2B1 — infraestructura flags
- F12-E2B2.2 — default flags `false`
- F12-E2B3A — auditoría residual (R-20–R-23, G-6 menú)
- F12-E2B3B — QueryAuditor cleanup (cerrado)

**F12-E2B3C Menu Logging Cleanup cerrado.** No se continúa con RBAC ni ORG_SESSION_SCOPE.
