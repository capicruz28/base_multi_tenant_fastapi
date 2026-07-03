# F13-K2-P0 — Remediación TD-08 CRITICAL

**Fecha:** 2026-06-25  
**Prerequisitos:** F13-K1 (auditoría global), F13-D2 (patrón canónico)  
**Estado:** **IMPLEMENTADO** — solo hallazgos P0; MEDIUM/LOW sin tocar.

---

## Objetivo

Eliminar los casos que podían producir `SecurityError` TD-08 en Dedicated por consultas `tenant_data` sin predicado `cliente_id = :cliente_id` detectable por `_has_tenant_filter()`.

**Patrón aplicado (F13-D2):**

```python
await execute_query(
    text("... WHERE ... cliente_id = :cliente_id ...").bindparams(
        cliente_id=cliente_id,
        ...,
    ),
    client_id=cliente_id,
)
```

**Sin modificar:** `query_helpers.py`, `routing.py`, OSR, `_has_tenant_filter`, `qmark_sql_text`, OpenAPI.

---

## Resumen de cambios

| # | K1 ID | Archivo | Método | Por qué P0 |
|---|-------|---------|--------|------------|
| 1 | U-01 | `user_service.py` | `obtener_usuario_completo_por_id` (rama `multi`) | WHERE solo `usuario_id` → TD-08 fail-closed Dedicated |
| 2 | U-04 | `user_service.py` | `_fetch_usuario_rol_by_id` (nuevo) + 3 call sites | PK-only `usuario_rol_id = :p0` sin tenant |
| 3 | S-U-05 | `superadmin_usuario_service.py` | `obtener_usuario_completo` | Drill-down TD sin `cliente_id` en SQL |
| 4 | S-U-06 | `superadmin_usuario_service.py` | `obtener_actividad_usuario` | `usuario` + `auth_audit_log` sin `cliente_id` |
| 5 | — | `auth_queries.py` + `user_service.py` | `IS_USER_SUPER_ADMIN` / `is_super_admin` | Sin filtro `ur.cliente_id` |
| 6 | P-02 | `permiso_service.py` | `asignar_o_actualizar_permiso` get-by-id L294 | `permiso_id` only en `rol_menu_permiso` |

---

## Diff arquitectónico por cambio

### 1. `UserService.obtener_usuario_completo_por_id` (Dedicated)

**Antes:**

```
qmark_sql_text(..., (usuario_id,))
WHERE u.usuario_id = ?
→ :p0 → _has_tenant_filter FAIL → SecurityError Dedicated
```

**Después:**

```
text(...).bindparams(usuario_id=, cliente_id=)
WHERE u.usuario_id = :usuario_id
  AND (u.cliente_id = :cliente_id OR u.cliente_id IS NULL)
→ TD-08 satisfied
```

**Shared:** rama `else` intacta (`qmark_sql_text`) — sin cambio observable.

**Dedicated NULL `cliente_id`:** preservado vía `OR u.cliente_id IS NULL`.

---

### 2. `UserService._fetch_usuario_rol_by_id`

**Antes:**

```
SELECT ... FROM usuario_rol WHERE usuario_rol_id = ?
```

**Después:**

```
WHERE usuario_rol_id = :usuario_rol_id AND cliente_id = :cliente_id
```

Reemplaza 3 usos en `asignar_rol_a_usuario` y `revocar_rol_de_usuario`.

---

### 3. `SuperadminUsuarioService.obtener_usuario_completo`

**Antes:**

```
qmark: WHERE u.usuario_id = ?
+ resolve_platform_tenant_data_execute_kwargs
```

**Después:**

```
text().bindparams(usuario_id=, cliente_id=)
WHERE ... AND (u.cliente_id = :cliente_id OR u.cliente_id IS NULL)
```

Lookups CP (`kwargs_platform_global_user_lookup`, `kwargs_control_plane_read`) **sin cambio**.

---

### 4. `SuperadminUsuarioService.obtener_actividad_usuario`

**Antes:**

```
usuario: WHERE usuario_id = ?
audit: WHERE a.usuario_id = ?
```

**Después:**

```
usuario: + (cliente_id = :cliente_id OR NULL)
audit: a.usuario_id = :usuario_id AND a.cliente_id = :cliente_id
TOP (:limite) con bindparams nombrados
```

---

### 5. `IS_USER_SUPER_ADMIN` + `is_super_admin`

**Antes (`auth_queries`):**

```sql
WHERE ur.usuario_id = :usuario_id  -- sin ur.cliente_id
```

**Después:**

```sql
WHERE ur.usuario_id = :usuario_id
  AND ur.cliente_id = :cliente_id
```

`is_super_admin(usuario_id, cliente_id)` usa `execute_query` + `client_id=cliente_id`.  
`get_user_level_info` propaga `cliente_id`.

---

### 6. `PermisoService` get-by-id (sin cambios en payload)

**Antes:**

```sql
FROM rol_menu_permiso WHERE permiso_id = ?
```

**Después:**

```sql
WHERE permiso_id = :permiso_id AND cliente_id = :cliente_id
```

Rama «sin cambios en permisos» del PUT/assign path.

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `app/modules/users/application/services/user_service.py` | Dedicated query, `_fetch_usuario_rol_by_id`, `is_super_admin` |
| `app/modules/superadmin/application/services/superadmin_usuario_service.py` | `obtener_usuario_completo`, `obtener_actividad_usuario` |
| `app/infrastructure/database/queries/auth/auth_queries.py` | `IS_USER_SUPER_ADMIN` |
| `app/modules/rbac/application/services/permiso_service.py` | get-by-id L294 |
| `tests/unit/test_f13_k2_p0_critical_td08.py` | Golden TD-08 P0 |

---

## Validación

### Pytest

```bash
python -m pytest tests/unit/test_f13_k2_p0_critical_td08.py -v
python -m pytest tests/unit/test_defensive_tenant_filter.py tests/unit/test_text_clause_bindparams_preservation.py -v
python -m pytest tests/unit/test_f13_j1_platform_tenant_reachability.py tests/unit/test_f13_j2_platform_fail_soft_superadmin_usuarios.py tests/unit/test_f13_j3_platform_fail_soft_dashboard.py -v
```

**Resultado:** 25 + 21 tests relacionados — **all passed**.

### Criterios TD-08 Dedicated

| Query P0 | `_has_tenant_filter` | `apply_tenant_filter_to_text_clause` Dedicated |
|----------|:--------------------:|:----------------------------------------------:|
| usuario dedicated | ✅ | ✅ sin SecurityError |
| usuario_rol PK | ✅ | ✅ |
| rol_menu_permiso | ✅ | ✅ |
| auth_audit_log | ✅ | ✅ |
| IS_USER_SUPER_ADMIN | ✅ | ✅ |

### Smoke conceptual

| Modo | Verificación |
|------|--------------|
| **Dedicated** | Queries P0 pasan filtro defensivo sin `SecurityError` |
| **Shared** | Rama `obtener_usuario_completo_por_id` sin modificar (qmark) |
| **Platform** | Superadmin drill-down usa `:cliente_id`; fail-soft J2/J3 intacto |

---

## Deuda residual (fuera P0 — F13-K2-P1+)

| Categoría | Ejemplos | Estado |
|-----------|----------|--------|
| MEDIUM qmark con filtro semántico `:p0` | `user_service` CRUD restante, `_obtener_roles_usuario` | Pendiente |
| LOW ENGINE_SCOPED | `superadmin_auditoria_service` qmark | Pendiente |
| MEDIUM permiso check L264, específico L486 | `PermisoService` | Pendiente |

---

## Restricciones de este entregable

- Sin commits.
- Sin remediación masiva.
- Detenido tras P0.

**Estado:** F13-K2-P0 completado.
