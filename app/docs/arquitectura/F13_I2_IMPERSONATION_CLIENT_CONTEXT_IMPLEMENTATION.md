# F13-I2 — Implementación del overlay de `current_user.cliente_id` en impersonación

**Fecha:** 2026-06-25  
**Decisión implementada:** [`F13_I1_IMPERSONATION_CLIENT_CONTEXT_DECISION.md`](F13_I1_IMPERSONATION_CLIENT_CONTEXT_DECISION.md)  
**Alcance:** un único archivo productivo modificado.

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `app/api/deps.py` | Overlay de `usuario_completo.cliente_id` en `get_current_active_user()` bajo guard impersonación tenant-effective |

**Sin modificar (según restricciones):** `user_builder.py`, `user_context.py`, `IdentityGateway`, OSR, routing, `execute_query`, query_helpers, frontend, OpenAPI, tests productivos.

---

## Diff arquitectónico

### Antes (F13-H2 / pre-I2)

```
build_user_with_roles(request_cliente_id=SYSTEM)
  → current_user.cliente_id = SYSTEM (fila operador)
JWT overlay nivel (access_level, user_type)
apply_impersonation_effective_permissions_to_user(cliente_id=SYSTEM → re-resuelve JWT internamente solo para permisos)
yield current_user  → endpoints IAM leen SYSTEM
```

### Después (F13-I2)

```
build_user_with_roles(request_cliente_id=SYSTEM)
  → current_user.cliente_id = SYSTEM (sin cambio en builder)
JWT overlay nivel
► if is_impersonation_effective_tenant_session(payload):
      current_user.cliente_id = resolve_impersonation_tenant_cliente_id(...)  ← NUEVO
apply_impersonation_effective_permissions_to_user(cliente_id=current_user.cliente_id)  ← ya alineado post-overlay
yield current_user  → endpoints IAM leen tenant JWT
```

### Código insertado (`deps.py` L319–331)

```python
from app.core.auth.impersonation_rbac import (
    apply_impersonation_effective_permissions_to_user,
    clear_impersonation_rbac_context,
    is_impersonation_effective_tenant_session,
    resolve_impersonation_tenant_cliente_id,
)

if is_impersonation_effective_tenant_session(payload):
    usuario_completo.cliente_id = resolve_impersonation_tenant_cliente_id(
        payload,
        user_cliente_id=usuario_completo.cliente_id,
        request_cliente_id=request_cliente_id,
    )
    tenant_context = try_get_tenant_context()
    ...
    await apply_impersonation_effective_permissions_to_user(...)
```

**Propiedades del cambio:**

- Reutiliza funciones existentes; sin helpers, ContextVars ni campos nuevos.
- Guard idéntico al bloque `apply_impersonation_effective_permissions_to_user` preexistente.
- Ubicación: después del overlay JWT de nivel (~L304–317), antes de `apply_impersonation_effective_permissions_to_user`.

---

## Validaciones obligatorias — resultados

### 1–3. Escenarios sin overlay (regresión)

| # | Escenario | Resultado | Evidencia |
|---|-----------|-----------|-----------|
| 1 | Platform normal | `current_user.cliente_id == SYSTEM` | Mock `get_current_active_user`: payload sin `is_impersonation` → `00000000-0000-0000-0000-000000000001` |
| 2 | Tenant Admin Shared | Sin cambio | Mock: payload tenant, `request_cliente_id=ACMEE`, fila ACMEE → overlay no altera valor |
| 3 | Tenant Admin Dedicated | Sin cambio | Docker: `pre_overlay == post_overlay == 8B0D7BD1-…`, permisos=18, monedas=0 |

### 4–5. Impersonación platform

| # | Escenario | Resultado | Evidencia |
|---|-----------|-----------|-----------|
| 4 | Platform impersonando Shared | `current_user.cliente_id == JWT target` | Mock deps: SYSTEM pre-build → `8B0D7BD1-…` post-overlay |
| 5 | Platform impersonando Dedicated (acmee) | Idem | Docker: `pre_overlay=SYSTEM`, `post_overlay=8B0D7BD1-…` |

### 6–10. Paridad datos IAM (Docker acmee CLI019)

Tenant Admin baseline: **permisos=18**, **monedas=0**.

| # | Dominio | Impersonación post-overlay | Paridad con Tenant Admin |
|---|---------|----------------------------|--------------------------|
| 6 | Roles | No ejecutado E2E HTTP en F13-I2; overlay corrige `cliente_id` en deps | Pendiente E2E; unit deps OK |
| 7 | Permisos rol (EP1) | **0** en trace servicio aislado | **Parcial** — ver residual abajo |
| 8 | Usuarios | Overlay alinea `cliente_id` argumento servicio | Mejora vs F13-H1; E2E no ejecutado |
| 9 | Catálogos (monedas) | **0** (store acmee) | **Sí** — coincide tenant admin (antes Imp-B devolvía 2) |
| 10 | Menús | Sin regresión en suite impersonación auth | Tests unitarios impersonación OK |

**Residual EP1 permisos (fuera de alcance F13-I2):** `PermisoService.obtener_permisos_por_rol` invoca `RolService.obtener_rol_por_id` sin `client_id`; esa query usa `TenantContext` del middleware (SYSTEM @ platform host). El overlay en deps corrige el parámetro `cliente_id` del endpoint pero no el pre-check de rol. Requiere ticket separado (no autorizado en F13-I2).

---

## Pruebas ejecutadas

### Suite pytest (host)

| Comando / suite | Resultado |
|-----------------|-----------|
| `tests/unit/test_impersonation_auth.py` | **19 passed** |
| `tests/integration/test_hybrid_impersonation_harness.py` | **4 passed** |
| `tests/unit/test_org_session_scope.py` | **5 passed** |
| `tests/unit/test_inv_session_scope.py` | **2 passed** |
| `tests/integration/test_empresa_context_request_scope.py` | **8 passed** |
| `tests/unit/test_iam_me_session_probe_dep.py` | **6 passed** |
| **Total focal F13-I2** | **44 passed** |

### Verificación unitaria directa de `get_current_active_user` (mock)

```
imp_platform     → cliente_id = 8b0d7bd1-764c-4bc5-adb4-c2d4a26195cd
platform_normal  → cliente_id = 00000000-0000-0000-0000-000000000001
tenant_admin     → cliente_id = 8b0d7bd1-764c-4bc5-adb4-c2d4a26195cd
```

### Runtime Docker (overlay + servicios, acmee Dedicated)

```json
{
  "tenant_admin": {
    "pre_overlay": "8b0d7bd1-764c-4bc5-adb4-c2d4a26195cd",
    "post_overlay": "8b0d7bd1-764c-4bc5-adb4-c2d4a26195cd",
    "permisos": 18,
    "monedas": 0
  },
  "imp_platform_overlay": {
    "pre_overlay": "00000000-0000-0000-0000-000000000001",
    "post_overlay": "8b0d7bd1-764c-4bc5-adb4-c2d4a26195cd",
    "permisos": 0,
    "monedas": 0
  },
  "platform_normal": {
    "post_overlay": "00000000-0000-0000-0000-000000000001",
    "monedas": 2
  }
}
```

### Regresiones preexistentes (no introducidas por F13-I2)

| Suite | Resultado | Nota |
|-------|-----------|------|
| `tests/unit/test_iam_me_current_token_id.py` | 4 failed / 7 passed | Fallos en cookie/`current_token_id`; no tocan `cliente_id` overlay en deps |

---

## Riesgos

| Riesgo | Estado post-I2 |
|--------|----------------|
| Platform normal pierde SYSTEM en `current_user` | **Mitigado** — guard impersonación evita overlay |
| Tenant admin alterado | **Mitigado** — sin `is_impersonation_effective_tenant_session` |
| Divergencia overlay vs `require_session_cliente_id` | **Bajo** — mismo resolver `resolve_impersonation_tenant_cliente_id` |
| EP1 permisos vacíos por `obtener_rol_por_id` + TenantContext | **Persiste** — fuera de alcance; ver residual |
| Imp-A (host tenant, operador ausente DP) | **Sin cambio** — auth falla antes del overlay |

---

## Regresiones verificadas

| Área | Verificación |
|------|--------------|
| Session scope ORG/INV | Tests hybrid harness + org/inv session scope: **pass** |
| JWT claims / emisión | Sin cambio de emisión |
| `apply_impersonation_effective_permissions_to_user` | Recibe `cliente_id` ya overlayed; orden preservado |
| Platform catálogos sin impersonar | Docker: monedas=2 en store SYSTEM intacto |
| Identidad operador | `usuario_id`, `sub`, `impersonated_by` en JWT sin modificar |

---

## Cierre F13-I2

Implementación conforme a F13-I1: **un bloque en `deps.py`**, **Opción A** (`current_user.cliente_id` in-place), resolvers existentes, sin ampliación de alcance.

**Siguiente fase (no iniciada):** ticket separado para pre-check `RolService.obtener_rol_por_id` bajo impersonación @ platform host si se exige paridad EP1 al 100%.

**Sin commits** en este entregable.

---

**Fin F13-I2.**
