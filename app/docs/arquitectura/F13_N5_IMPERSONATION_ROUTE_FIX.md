# F13-N5 — Corrección colisión de rutas `POST /auth/impersonate/end/`

**Fecha:** 2026-06-29  
**Ticket:** Implementación (post F13-N4)  
**Alcance:** Solo enrutamiento — sin cambios de negocio, RBAC, JWT, Redis ni servicios.

---

## Resumen

| Item | Detalle |
|------|---------|
| **Problema** | `POST /api/v1/auth/impersonate/end/` hacía match con `/impersonate/{cliente_id}/` (`cliente_id="end"`) y ejecutaba `iniciar_impersonacion` + `require_super_admin()` → HTTP 403 |
| **Corrección** | Registrar `/impersonate/end/` **antes** de `/impersonate/{cliente_id}/` |
| **Archivo modificado** | `app/modules/auth/presentation/endpoints.py` |
| **Tests nuevos** | `tests/unit/test_f13_n5_impersonation_route_order.py` |

---

## Cambio realizado

### Archivo

`app/modules/auth/presentation/endpoints.py`

### Líneas afectadas

| Cambio | Líneas (post-fix) |
|--------|-------------------|
| Comentario F13-N5 (motivo del orden) | **726–727** |
| `POST /impersonate/end/` → `finalizar_impersonacion` | **729–778** |
| `POST /impersonate/{cliente_id}/` → `iniciar_impersonacion` | **781–849** |

**Antes (F13-N4):** `iniciar_impersonacion` (~L727) → `finalizar_impersonacion` (~L798).  
**Después (F13-N5):** `finalizar_impersonacion` (L729) → `iniciar_impersonacion` (L781).

No se modificó el cuerpo de ningún handler, dependencia, schema, servicio ni montaje del router.

---

## Motivo

Starlette/FastAPI resuelve rutas en **orden de registro**. Con la ruta paramétrica primero, el path `/impersonate/end/` capturaba `cliente_id="end"` y despachaba al handler de **inicio**, que exige `require_super_admin()`. El JWT de impersonación (`user_type=tenant_admin`, `is_super_admin=false`) fallaba ese check antes de que `finalizar_impersonacion` pudiera ejecutarse.

La corrección mínima conforme al ticket: **invertir el orden de registro** para que la ruta estática tenga prioridad.

---

## Evidencia

### 1. Orden de registro (router auth)

```
/impersonate/end/           → finalizar_impersonacion   (1º)
/impersonate/{cliente_id}/  → iniciar_impersonacion     (2º)
```

### 2. Primer match Starlette para `POST /impersonate/end/`

```
finalizar_impersonacion   ← gana (antes: iniciar_impersonacion)
```

### 3. Regresión F13-N4 — JWT de impersonación en `/end/`

**Antes del fix (producido en F13-N4):**

```
POST /api/v1/auth/impersonate/end/
→ HTTP 403
→ "Se requieren privilegios de Super Administrador para acceder a este recurso"
→ Log: Intento de acceso no autorizado a endpoint Super Admin por: superadmin
```

**Después del fix (test ASGI con mock de servicio):**

```
POST /api/v1/auth/impersonate/end/
→ HTTP 200
→ {"access_token":"parent-access-token","token_type":"bearer"}
→ ImpersonationService.finalizar_impersonacion invocado
→ Sin mensaje "Super Administrador" en respuesta
```

### 4. Ruta paramétrica intacta

Para `POST /impersonate/{uuid}/`, el único match FULL sigue siendo `iniciar_impersonacion` (la ruta `/impersonate/end/` no captura UUIDs).

---

## Validaciones obligatorias

| # | Validación | Resultado |
|---|------------|-----------|
| 1 | `POST /auth/impersonate/end/` ejecuta `finalizar_impersonacion` | ✅ `mock_finalizar.assert_awaited_once()` en test ASGI |
| 2 | No aparece log Super Admin al salir de impersonación | ✅ Respuesta 200 sin texto "Super Administrador" |
| 3 | No HTTP 403 en fin de impersonación (con servicio mockeado) | ✅ `test_post_impersonate_end_no_super_admin_403` |
| 4 | Flujo Platform → impersonar → `/end/` → restaurar → 200 | ✅ Handler correcto + 200 con payload `access_token` (E2E completo con Redis/BD no ejecutado en CI unitario; contrato del handler verificado) |
| 5 | `POST /auth/impersonate/{cliente_id}/` sin cambio funcional | ✅ Match Starlette sigue siendo `iniciar_impersonacion`; regresión `test_impersonation_auth.py` (19 tests) OK |

---

## Pruebas ejecutadas

### Comando

```bash
python -m pytest tests/unit/test_f13_n5_impersonation_route_order.py tests/unit/test_impersonation_auth.py -v --tb=short
```

### Resultado

```
24 passed in 8.74s
```

Desglose F13-N5 (5 tests):

| Test | Propósito |
|------|-----------|
| `test_impersonate_end_route_registered_before_parametric` | Orden de registro en router |
| `test_starlette_first_match_for_impersonate_end_is_finalizar` | Match Starlette correcto |
| `test_starlette_parametric_route_still_matches_uuid_cliente_id` | Sin regresión en ruta UUID |
| `test_post_impersonate_end_dispatches_to_finalizar_handler` | HTTP 200 + servicio finalizar invocado |
| `test_post_impersonate_end_no_super_admin_403` | Regresión F13-N4 (no 403 Super Admin) |

---

## Validación del flujo completo (esperado en runtime)

```
Platform Admin (JWT platform)
    ↓
POST /auth/impersonate/{cliente_id}/     → iniciar_impersonacion (require_super_admin) — sin cambio
    ↓
Operación tenant (JWT is_impersonation=true)
    ↓
POST /auth/impersonate/end/              → finalizar_impersonacion (get_current_user_data) — fix F13-N5
    ↓
HTTP 200 + access_token padre (+ refresh cookie web si aplica)
    ↓
Sesión Platform restaurada
```

---

## Lo que NO se modificó

- `ImpersonationService`
- Lógica de handlers (solo reordenamiento)
- JWT / refresh / cookies / RBAC / Session Manager
- Contratos HTTP request/response
- OpenAPI paths
- Frontend

---

**Fin F13-N5 — Sin commits.**
