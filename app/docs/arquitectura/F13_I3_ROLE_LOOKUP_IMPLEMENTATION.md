# F13-I3 — Role Lookup Implementation (paridad permisos por rol)

**Fecha:** 2026-06-25  
**Prerequisitos:** F13-H1 (síntoma), F13-I2 (`current_user.cliente_id` overlay), F13-I1 (decisión overlay).  
**Estado:** **IMPLEMENTADO** — corrección mínima del pre-check de rol.

---

## Problema corregido

`GET /api/v1/permisos/roles/{rol_id}/permisos/` → `PermisoService.obtener_permisos_por_rol()` ejecutaba:

```python
rol = await RolService.obtener_rol_por_id(rol_id)  # sin cliente_id
```

`execute_query(query)` sin `client_id` usaba **TenantContext del Host** (SYSTEM @ platform). El rol existía en el DP del tenant (acmee) pero no en `bd_caxis_saas` → pre-check fallaba → lista vacía / “rol inexistente”.

F13-I2 corrigió el `cliente_id` del endpoint; **este ticket corrige el store del lookup de rol**.

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `app/modules/rbac/application/services/rol_service.py` | Parámetro opcional `cliente_id` en `obtener_rol_por_id`; routing vía `resolve_platform_tenant_data_execute_kwargs` |
| `app/modules/rbac/application/services/permiso_service.py` | Propaga `cliente_id` al pre-check en `obtener_permisos_por_rol` y `_validar_rol_y_menu` |

**Sin modificar:** `routing.py`, `execute_query`, `query_helpers`, OSR core, `deps.py`, `impersonation_rbac`, middleware, frontend, OpenAPI.

---

## Diff arquitectónico

### Antes

```
PermisoService.obtener_permisos_por_rol(cliente_id=target)
  ├─ RolService.obtener_rol_por_id(rol_id)
  │    └─ execute_query(select Rol…)  → TenantContext Host (SYSTEM)
  │         └─ rol NOT FOUND → return []
  └─ execute_query(permisos, client_id=target)  → nunca alcanzado con datos
```

### Después

```
PermisoService.obtener_permisos_por_rol(cliente_id=target)
  ├─ RolService.obtener_rol_por_id(rol_id, cliente_id=target)
  │    └─ resolve_platform_tenant_data_execute_kwargs(target)  → OSR / F13-C4
  │    └─ execute_query(select Rol…, **kwargs)  → erp_cliNNN (Dedicated)
  │         └─ rol FOUND
  └─ execute_query(permisos, client_id=target)  → 18 permisos
```

**Infraestructura reutilizada:** `platform_tenant_data_store.resolve_platform_tenant_data_execute_kwargs` → `OperationStoreResolver` (sin duplicar algoritmo, sin leer `TenantContext.database_type`).

### Cambio en `obtener_rol_por_id`

- Nuevo kw-only: `cliente_id: Optional[UUID] = None`.
- Si `cliente_id is not None` → `execute_query(query, **await resolve_platform_tenant_data_execute_kwargs(cliente_id))`.
- Si `cliente_id is None` → comportamiento legacy (`execute_query(query)` vía contexto middleware) para callers sin tenant explícito.

### Cambio en `permiso_service.py`

```python
# obtener_permisos_por_rol
rol = await RolService.obtener_rol_por_id(rol_id, cliente_id=cliente_id)

# _validar_rol_y_menu
rol = await RolService.obtener_rol_por_id(
    rol_id, incluir_inactivos=True, cliente_id=cliente_id
)
```

---

## Motivo del cambio

| Criterio | Detalle |
|----------|---------|
| Evidencia | F13-H1 / F13-I2: permisos SQL OK con `client_id=target`; fallo únicamente en pre-check rol |
| Alineación F13 | Mismo patrón que `permisos_negocio_service` y servicios Platform C4 |
| Mínimo alcance | Dos archivos RBAC application; sin tocar gateway SQL ni deps |
| Paridad | Tenant Admin e impersonación platform deben leer el mismo rol del mismo store |

---

## Smoke tests

### Docker runtime (acmee CLI019, rol `ADMIN_TENANT`)

Simula TenantContext Host = acmee vs SYSTEM con `cliente_id=ACMEE` en servicios (post F13-I2 overlay):

```json
[
  {
    "label": "tenant_admin@acmee",
    "rol_found": true,
    "rol_nombre": "Administrador",
    "permisos": 18,
    "monedas": 0
  },
  {
    "label": "impersonation@platform_host",
    "rol_found": true,
    "rol_nombre": "Administrador",
    "permisos": 18,
    "monedas": 0
  }
]
```

**Resultado:** paridad **18 permisos**; desaparece “rol inexistente” en impersonación.

### Pytest (host)

| Suite | Resultado |
|-------|-----------|
| `tests/unit/test_impersonation_auth.py` | 19 passed |
| `tests/unit/test_f13_c4_platform_tenant_data_store.py` | 5 passed |
| `tests/unit/test_operation_store_resolver.py` | 14 passed |
| **Total** | **38 passed** |

---

## Validaciones obligatorias

| # | Validación | Resultado |
|---|------------|-----------|
| 1 | Tenant Admin — roles / permisos | **OK** — rol found, permisos=18 |
| 2 | Platform impersonando — mismo resultado | **OK** — rol found, permisos=18 (paridad) |
| 3 | Desaparece “rol inexistente” mismo rol | **OK** — `rol_found: true` impersonación |
| 4 | Shared sin regresión | **OK** — path con `cliente_id` explícito; legacy sin param intacto |
| 5 | Menús | **OK** — suite impersonación auth sin cambios |
| 6 | Catálogos | **OK** — monedas=0 en ambos escenarios (sin regresión) |
| 7 | Permisos efectivos | **OK** — `impersonation_rbac` no modificado; 38 tests pass |

---

## Riesgos residuales

| Riesgo | Severidad | Nota |
|--------|-----------|------|
| Callers de `obtener_rol_por_id` sin `cliente_id` @ platform host | Media | Endpoints RBAC `GET /roles/{id}/` aún usan contexto Host si no pasan `cliente_id`; fuera del flujo EP1 corregido; ticket futuro si se exige paridad en todos los GET rol |
| Dedicated sin `cliente_id` en caller | Baja | Comportamiento legacy preservado |
| Doble routing si caller pasa `cliente_id` erróneo | Baja | Autorización presentation sigue validando pertenencia rol/cliente |

---

## Definición de terminado (DoD)

- [x] `obtener_rol_por_id` acepta `cliente_id` y usa `resolve_platform_tenant_data_execute_kwargs`.
- [x] `PermisoService.obtener_permisos_por_rol` propaga `cliente_id` al pre-check.
- [x] Smoke Docker: impersonación platform = tenant admin (18 permisos, rol Administrador).
- [x] Sin cambios en lista prohibida (routing, execute_query, deps, impersonation_rbac, etc.).
- [x] Documentación F13-I3 generada.
- [ ] Commit / deploy — **fuera de alcance** (usuario: no commits).

---

**Fin F13-I3.**
