# F13-H2 — Root Cause Verification (`current_user.cliente_id`)

**Fecha:** 2026-06-25  
**Alcance:** cadena auth exclusiva JWT → `current_user` en impersonación (host SYSTEM / platform).  
**Restricciones:** verificación en código; sin propuestas de solución; sin cambios de código.

**Escenario verificado (Imp-B, F13-H1):** JWT impersonación con `cliente_id` = tenant target (p. ej. acmee); middleware `request_cliente_id` = SYSTEM; `sub` = operador platform (`superadmin`).

---

## Cadena analizada

```
JWT (payload)
  ↓ get_current_user_data()          [deps.py]
  ↓ get_current_active_user()        [deps.py]
  ↓ get_user_auth_context()          [user_context.py]
  ↓ IdentityGateway.lookup_user_for_auth_context()  [identity_gateway.py]
  ↓ build_user_with_roles()          [user_builder.py]
  ↓ _resolve_cliente_id()            [user_builder.py]
  ↓ current_user (UsuarioReadWithRoles)
```

**Observación transversal:** el claim JWT `cliente_id` (tenant impersonado) **permanece en `payload`** durante toda la cadena. **Ningún eslabón de esta cadena lo asigna a `current_user.cliente_id`.** El valor SYSTEM proviene de la **fila del operador** en BD platform, propagada por `_resolve_cliente_id`.

---

## Respuestas (8 puntos)

### 1. ¿Quién recibe primero el `cliente_id` correcto del JWT?

**`get_current_user_data()`** — `app/api/deps.py` L93–97.

Decodifica el Bearer token y expone el payload completo, incluido `cliente_id` del tenant impersonado emitido por `ImpersonationService._emitir_access_impersonacion` (`cliente_id` target en `token_data`, `impersonation_service.py` L214–216).

`get_current_active_user` recibe ese `payload` vía `Depends(get_current_user_data)` (L173), pero **no usa `payload["cliente_id"]`** para construir identidad de datos; solo consume claims de nivel (`access_level`, `user_type`, `is_super_admin`, L294–308) y flags de impersonación para RBAC auxiliar (L325–336).

---

### 2. ¿Quién lo reemplaza por SYSTEM?

Dos pasos encadenados (no hay asignación explícita “JWT → SYSTEM”; hay **omisión del JWT** + **prioridad de fila usuario**):

| Orden | Componente | Qué ocurre |
|-------|------------|------------|
| A | `IdentityGateway.lookup_user_for_auth_context` | Con `request_cliente_id` = SYSTEM, entra rama platform (`is_system_request_client`) y devuelve la fila del operador con `cliente_id` = SYSTEM en el dict (`identity_gateway.py` L560–564 → `get_platform_user_by_username`). |
| B | `_resolve_cliente_id` / `_resolve_cliente_id_from_user_row` | Si la fila trae `cliente_id` no nulo, **devuelve ese valor** (SYSTEM) y **no consulta** el JWT. |

El mismo criterio se aplica dos veces en la cadena: en `get_user_auth_context` (`user_context.py` L113 → `_resolve_cliente_id_from_user_row` L60–61) y en `build_user_with_roles` (`user_builder.py` L116 → `_resolve_cliente_id`).

---

### 3. ¿En qué línea exacta ocurre?

**Línea decisiva (valor final SYSTEM en `current_user`):**

```82:88:app/core/auth/user_builder.py
def _resolve_cliente_id(
    user_result: Dict[str, Any],
    request_cliente_id: Optional[UUID],
) -> Optional[UUID]:
    user_cliente_id = _normalize_cliente_id(user_result.get("cliente_id"))
    if user_cliente_id:
        return user_cliente_id
```

Para el operador platform, `user_result["cliente_id"]` ya es SYSTEM tras el lookup; **L87–88** fijan `cliente_id = SYSTEM`.

**Propagación a `current_user`:**

| Línea | Archivo | Acción |
|-------|---------|--------|
| L116 | `user_builder.py` | `cliente_id = _resolve_cliente_id(user_result, request_cliente_id)` |
| L255–257 | `user_builder.py` | `_prepare_usuario_read_dict(..., cliente_id=cliente_id)` → `prepared["cliente_id"] = cliente_id` (L63) |
| L262–266 | `user_builder.py` | `return UsuarioReadWithRoles(**usuario_dict, ...)` |

**Entrada a la rama platform (origen de la fila SYSTEM):**

```560:564:app/core/identity/identity_gateway.py
        if is_system_request_client(request_cliente_id) and request_cliente_id:
            return await IdentityGateway.get_platform_user_by_username(
                username,
                platform_cliente_id=request_cliente_id,
            )
```

**`request_cliente_id` = SYSTEM proviene del middleware**, no del JWT:

```206:208:app/api/deps.py
        from app.core.tenant.context import get_current_client_id
        try:
            request_cliente_id = get_current_client_id()
```

**Duplicado en contexto mínimo (misma regla, no es `current_user` final):** `user_context.py` L60–61 (`_resolve_cliente_id_from_user_row`).

**Post-build en deps:** L304–308 sobreescriben `access_level`, `user_type`, `is_super_admin` desde JWT; **`cliente_id` no se modifica**. L330–336 (`apply_impersonation_effective_permissions_to_user`) resuelve tenant JWT **solo para la lista `user.permisos`**, no para `user.cliente_id` (`impersonation_rbac.py` L221–231).

---

### 4. ¿Es un comportamiento intencional?

**Parcialmente sí — por diseño de identidad platform; no como target tenant en `current_user`.**

Evidencia en código:

| Evidencia | Interpretación factual |
|-----------|----------------------|
| `_resolve_cliente_id` prioriza `user_result.cliente_id` sobre `request_cliente_id` | Patrón estable para Dedicated (`normalize_user_cliente_id`, `identity_gateway.py` L114–135) y para operadores cuya fila lleva SYSTEM. |
| `platform_user_lookup.py` L4–6 | Operadores platform viven con `cliente_id` SYSTEM en la misma BD. |
| `impersonation_rbac.py` L59–61 | Docstring explícito: permisos/menú impersonados usan JWT tenant, **no** `current_user.cliente_id` (operador SYSTEM). |
| `deps.py` L239 | Comentario: impersonación y JWT tenant aplican a **omitir** `validate_tenant_access` (L240), no a reescribir `cliente_id` del usuario. |
| `ERP_BACKEND_STANDARDS_V4.md` §3.4 / §5 | Datos operativos ERP deben usar `require_session_cliente_id`; anti-patrón documentado: `current_user.cliente_id` en presentation. |

Conclusión: mantener SYSTEM en la fila del operador y priorizarla en `_resolve_cliente_id` es **coherente con platform sin impersonación**. La cadena **no implementa** overlay del JWT tenant sobre `current_user.cliente_id`; otros mecanismos (`resolve_impersonation_tenant_cliente_id`, `require_session_cliente_id`, `get_rbac_session_client_id`) cubren impersonación **fuera** de este objeto.

---

### 5. ¿Qué contratos dependen actualmente de ese comportamiento?

**A. Contratos que dependen de `current_user.cliente_id` = fila usuario (SYSTEM para operador platform):**

- Endpoints IAM/RBAC/catálogos que pasan `current_user.cliente_id` a servicios (p. ej. `endpoints_permisos.py` L198, `catalogos/endpoints.py` L25, `users/endpoints.py` L806) — patrón extendido a módulos ERP (AUD, FIN, HCM, BI, etc.).
- `build_user_with_roles`: carga de permisos RBAC del operador vía `cliente_id` resuelto (L210–211, L232–233, L242–244) — en impersonación SYSTEM antes del overlay parcial de `apply_impersonation_effective_permissions_to_user`.
- `determine_user_type` / rama `platform_admin` cuando `is_system_request_client(request_cliente_id)` (`user_builder.py` L190–191).
- `validate_tenant_access`: superadmin bypass usando `context.cliente_id` (`user_context.py` L200–201).
- Auditoría cross-tenant: `AuditService.registrar_tenant_access` con `token_cliente_id=context.cliente_id` (`deps.py` L259–262).

**B. Contratos que ya **no** usan `current_user.cliente_id` para tenant impersonado (dependen del JWT vía otros resolvers):**

- Permisos efectivos impersonados: `resolve_impersonation_tenant_cliente_id` (`impersonation_rbac.py` L50–82).
- Menú auth: `resolve_menu_cliente_id_for_session` (L235–260).
- Session scope ERP: `require_session_cliente_id` / `get_rbac_session_cliente_id` (estándar V4; referencia `rbac_deps.py`, `org_deps.py`, `inv_deps.py`).

**C. Contrato de entrada a la cadena:**

- `get_current_active_user` pasa **`request_cliente_id` del middleware** a `get_user_auth_context` y `build_user_with_roles` (L219, L275), no `payload["cliente_id"]`.

---

### 6. ¿Cambiar ese punto afectaría Tenant Admin?

**Tenant Admin normal: no**, en condiciones actuales.

Motivo factual: usuario tenant en host propio → `request_cliente_id` = tenant JWT; fila usuario trae el **mismo** `cliente_id`; `_resolve_cliente_id` L87–88 devuelve el valor de la fila, que coincide con el JWT. No hay sustitución SYSTEM.

Riesgo solo si el cambio fuera **global** (p. ej. preferir JWT sobre fila siempre): usuarios Dedicated con `cliente_id` NULL/nulo en fila dependen de `_resolve_cliente_id` / `normalize_user_cliente_id` para tomar contexto tenant (`identity_gateway.py` L128–129).

---

### 7. ¿Cambiar ese punto afectaría Shared?

**Shared tenant (sin impersonación): no** — misma coincidencia fila ≈ JWT ≈ `request_cliente_id` que Tenant Admin.

**Shared + impersonación platform (host SYSTEM): sí** — mismo mecanismo que Dedicated Imp-B: operador SYSTEM, JWT tenant distinto; endpoints con `current_user.cliente_id` consultarían store incorrecto (F13-H1).

Un cambio **acotado a impersonación** (overlay JWT tenant solo cuando `is_impersonation` + sesión tenant efectiva) alinearía Shared impersonado con el contrato ya usado por `resolve_impersonation_tenant_cliente_id`, sin alterar login tenant directo.

---

### 8. ¿Cambiar ese punto afectaría Platform sin impersonación?

**Sí, si el cambio es global** (priorizar JWT o `request_cliente_id` impersonado sobre fila usuario).

Platform sin impersonación **requiere** `current_user.cliente_id` = SYSTEM:

- Identidad del operador en CP (`platform_user_lookup.py`, fila `usuario.cliente_id = SYSTEM`).
- Detección `platform_admin` (`user_builder.py` L190–191, `user_context.py` L229–230).
- Endpoints superadmin/platform que asumen operador SYSTEM.

Un overlay JWT tenant sobre `current_user.cliente_id` **fuera** de impersonación rompería ese contrato. La documentación de `resolve_impersonation_tenant_cliente_id` (L59–61) delimita el tenant JWT a RBAC/menú/session scope, **no** a redefinir identidad platform en sesión normal.

---

## Diagrama de flujo (Imp-B)

```
JWT payload.cliente_id = ACMEE          ──►  NO entra a build_user_with_roles
        │
        ▼
get_current_active_user
        │
        ├─ request_cliente_id = SYSTEM     ◄── TenantMiddleware (Host platform)
        │
        ├─ get_user_auth_context(SYSTEM)
        │     └─ lookup → fila superadmin.cliente_id = SYSTEM
        │     └─ _resolve_cliente_id_from_user_row → SYSTEM
        │
        ├─ build_user_with_roles(SYSTEM)
        │     └─ lookup → misma fila
        │     └─ _resolve_cliente_id L87-88 → SYSTEM   ◄── primer fijado en builder
        │     └─ UsuarioReadWithRoles.cliente_id = SYSTEM
        │
        ├─ deps: JWT → user_type, access_level (NO cliente_id)
        │
        └─ apply_impersonation_effective_permissions_to_user
              └─ resolve_impersonation_tenant_cliente_id(payload) → ACMEE
              └─ solo user.permisos (ContextVar); cliente_id del objeto intacto
```

---

## Tabla resumen

| # | Pregunta | Respuesta corta |
|---|----------|-----------------|
| 1 | Primer receptor JWT correcto | `get_current_user_data()` → `payload["cliente_id"]` |
| 2 | Quién fija SYSTEM | `IdentityGateway.lookup` (fila platform) + `_resolve_cliente_id` (prioriza fila) |
| 3 | Línea exacta | **`user_builder.py` L87–88** (retorno SYSTEM); propagación L116, L63, L262 |
| 4 | ¿Intencional? | Sí para identidad platform/fila; no como carrier del tenant impersonado en `current_user` |
| 5 | Contratos | Amplio uso `current_user.cliente_id` en presentation; impersonación RBAC/menú/ERP scope usan resolvers paralelos |
| 6 | Tenant Admin | No afectado (fila = JWT) |
| 7 | Shared | No en login directo; sí en impersonación platform |
| 8 | Platform sin impersonación | Sí afectado si cambio global — SYSTEM en `current_user` es requerido |

---

**Fin F13-H2.** Sin implementación. Sin commits.
