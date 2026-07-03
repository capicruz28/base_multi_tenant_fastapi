# F13-I5 — Implementación de paridad: `GET /roles/{rol_id}/permisos-negocio/`

**Fecha:** 2026-06-25  
**Prerequisitos:** F13-I3 (RolService + `cliente_id`), F13-I2 (overlay `current_user`), F13-I4 (trace 404).  
**Estado:** **IMPLEMENTADO** — propagación `cliente_id` en los dos lookups de rol del flujo permisos-negocio.

---

## Objetivo

Aplicar el mismo patrón F13-I3 al endpoint que el frontend consume para permisos de negocio, eliminando el 404 bajo impersonación Platform causado por lookup de rol en store SYSTEM.

---

## Archivos modificados (alcance F13-I5)

| Archivo | Cambio F13-I5 |
|---------|----------------|
| `app/modules/rbac/presentation/endpoints.py` | `get_permisos_negocio_rol` — 1.er `obtener_rol_por_id` con `cliente_id=current_user.cliente_id` |
| `app/modules/rbac/application/services/permisos_negocio_service.py` | `get_permisos_negocio_by_rol` — 2.º `obtener_rol_por_id` con `cliente_id=cliente_id` |

**Sin modificar:** SQL, `execute_query`, routing, OSR core, `deps.py`, `impersonation_rbac`, `RolService` (ya corregido en I3).

---

## Diff arquitectónico (F13-I5 únicamente)

### Antes

```
get_permisos_negocio_rol
  └─ RolService.obtener_rol_por_id(rol_id)           → TenantContext Host (SYSTEM) → None → HTTP 404

(get_permisos_negocio_by_rol no se alcanzaba)
```

### Después

```
get_permisos_negocio_rol
  └─ RolService.obtener_rol_por_id(rol_id, cliente_id=current_user.cliente_id)  ← F13-I2 overlay
       └─ resolve_platform_tenant_data_execute_kwargs → erp_cliNNN → rol OK
  └─ get_permisos_negocio_by_rol(rol_id, cliente_id)
       └─ RolService.obtener_rol_por_id(..., cliente_id=cliente_id)             ← 2.º lookup
       └─ _permisos_negocio_rol_dedicated → rol_permiso + catálogo permiso
  └─ HTTP 200 + PermisosNegocioResponse
```

---

## Diff de código

### 1. `endpoints.py` — `get_permisos_negocio_rol` (~L747–749)

**Antes:**

```python
rol = await RolService.obtener_rol_por_id(rol_id=rol_id, incluir_inactivos=True)
```

**Después:**

```python
rol = await RolService.obtener_rol_por_id(
    rol_id=rol_id, incluir_inactivos=True, cliente_id=current_user.cliente_id
)
```

### 2. `permisos_negocio_service.py` — `get_permisos_negocio_by_rol` (~L124–126)

**Antes:**

```python
rol = await RolService.obtener_rol_por_id(rol_id=rol_id, incluir_inactivos=True)
```

**Después:**

```python
rol = await RolService.obtener_rol_por_id(
    rol_id=rol_id, incluir_inactivos=True, cliente_id=cliente_id
)
```

---

## Motivo del cambio

F13-I4 demostró que ambos lookups invocaban `obtener_rol_por_id` **sin** `cliente_id`, por lo que F13-I3 no aplicaba. Con F13-I2 el endpoint ya tenía `current_user.cliente_id` correcto, pero el pre-check seguía consultando SYSTEM → `404 Rol no encontrado`.

La corrección reutiliza **exactamente** el parámetro opcional añadido en F13-I3; no hay algoritmo nuevo.

---

## Validaciones obligatorias

### Smoke Docker (acmee CLI019, rol `ADMIN_TENANT`, Host SYSTEM simulado para impersonación)

| Escenario | Lookup 1 | Lookup 2 (vía `get_permisos_negocio_by_rol`) | Permisos | Equivalente Tenant Admin |
|-----------|----------|-----------------------------------------------|----------|------------------------|
| Tenant Admin (`cliente_id=ACMEE`) | ✅ Administrador | ✅ | **83** | baseline |
| Platform impersonando (`query_cid=ACMEE`, Host=SYSTEM) | ✅ Administrador | ✅ | **83** | **Sí** |

Muestra (primeros códigos):

```json
["admin.platform.access", "admin.rol.actualizar", "admin.rol.asignar"]
```

**Antes F13-I5 (impersonación):** lookup 1 → `None` → **HTTP 404** — “Rol con ID … no encontrado”.  
**Después F13-I5:** lookup 1 y 2 → rol encontrado → **200** con 83 permisos (misma cuenta que tenant admin).

### Checklist requerido

| # | Validación | Resultado |
|---|------------|-----------|
| 1 | Tenant Admin → GET permisos-negocio → 200 | ✅ 83 permisos |
| 2 | Platform impersonando → 200 | ✅ 83 permisos |
| 3 | Primer lookup encuentra el mismo rol | ✅ `Administrador` |
| 4 | Segundo lookup encuentra el mismo rol | ✅ (sin `NotFoundError`) |
| 5 | Mismos permisos que Tenant Admin | ✅ count=83, mismos códigos muestra |
| 6 | Menús / catálogos / permisos efectivos | Sin cambios en esos módulos (no tocados) |
| 7 | Shared | Path con `cliente_id` explícito; legacy sin param intacto en otros callers |

---

## Riesgos residuales

| Riesgo | Nota |
|--------|------|
| `PUT /roles/{id}/permisos-negocio/` | Sigue con 1.er lookup **sin** `cliente_id` en handler (fuera de alcance F13-I5); puede 404 bajo impersonación en escritura |
| Otros endpoints RBAC con `obtener_rol_por_id` sin `cliente_id` | Mismo patrón legacy; no corregidos en I5 |
| `set_permisos_negocio_rol` lookup interno | Sin `cliente_id` en I5 (solo GET corregido) |

---

## Definición de terminado

- [x] Propagación `cliente_id` en 1.er lookup (`get_permisos_negocio_rol`).
- [x] Propagación `cliente_id` en 2.º lookup (`get_permisos_negocio_by_rol`).
- [x] Reutiliza `RolService.obtener_rol_por_id` + F13-I3 / `resolve_platform_tenant_data_execute_kwargs`.
- [x] Paridad demostrada: 83 permisos tenant vs impersonación.
- [x] Documentación F13-I5.
- [ ] Commit — **fuera de alcance**.

---

**Fin F13-I5.** Sin commits.
