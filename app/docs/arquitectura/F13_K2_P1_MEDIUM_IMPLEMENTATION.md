# F13-K2-P1 — Remediación TD-08 MEDIUM

**Fecha:** 2026-06-25  
**Prerequisitos:** F13-K1 (auditoría global), F13-K2-P0 (CRITICAL), F13-D2 (patrón canónico)  
**Estado:** **IMPLEMENTADO** — solo hallazgos MEDIUM tenant_data; LOW sin tocar.

---

## Objetivo

Silenciar warnings `[TENANT_FILTER] No se pudo aplicar filtro automático a TextClause` en consultas **tenant_data** que ya filtraban semánticamente por tenant vía `:p0`/`:p1` pero eran invisibles para `_has_tenant_filter()`.

**Patrón aplicado (F13-D2):**

```python
await execute_query(
    text("... WHERE t.cliente_id = :cliente_id AND ...").bindparams(
        cliente_id=cliente_id,
        ...,
    ),
    client_id=cliente_id,
)
```

**Sin modificar:** `routing.py`, `OperationStoreResolver`, `platform_tenant_reachability`, `query_helpers.py`, `execute_query()`, F13-J1/J2/J3, OSR, middleware.

**Exclusiones explícitas (K1 / instrucción K2-P1):**

| Exclusión | Motivo |
|-----------|--------|
| `get_usuarios_globales` COUNT/DATA (S-U-02) | Shared global — `kwargs_platform_global_read()` ENGINE_SCOPED |
| Lookups CP Superadmin (`_fetch_cliente_info`, `kwargs_control_plane_read`) | Control Plane |
| `superadmin_auditoria_service` (8× qmark) | ENGINE_SCOPED — LOW |
| `cliente_service` validaciones unicidad | CP — LOW |
| `tenant_service.obtener_configuracion_tenant` query `cliente` (T-01) | CP catálogo — LOW |
| Sesiones V1 `refresh_tokens` (S-U-07) | ENGINE_SCOPED session store |

---

## Resumen de cambios

| # | K1 ID | Archivo | Método | Consulta |
|---|-------|---------|--------|----------|
| 1 | U-02 | `user_service.py` | `obtener_usuario_completo_por_id` (rama shared) | SELECT usuario + roles LEFT JOIN |
| 2 | U-03 | `user_service.py` | `obtener_usuario_por_id` | SELECT usuario by PK |
| 3 | U-03 | `user_service.py` | `verificar_duplicados_usuario` | SELECT conflicto nombre/correo |
| 4 | U-03 | `user_service.py` | `actualizar_usuario` | verify duplicados pre-update |
| 5 | U-03 | `user_service.py` | `eliminar_usuario` | check es_eliminado |
| 6 | U-03 | `user_service.py` | `obtener_usuario_incluyendo_eliminados` | SELECT incl. eliminados |
| 7 | U-03 | `user_service.py` | `_maybe_set_empresa_default_after_role_assign` | SELECT empresa_default_id |
| 8 | U-03 | `user_service.py` | `asignar_rol_a_usuario` | check asignación existente |
| 9 | U-03 | `user_service.py` | `revocar_rol_de_usuario` | check asignación existente |
| 10 | U-05 | `user_service.py` | `obtener_roles_de_usuario` | listado roles activos |
| 11 | S-U-03 | `superadmin_usuario_service.py` | `_obtener_roles_usuario` | rol ⋈ usuario_rol |
| 12 | S-U-06† | `superadmin_usuario_service.py` | `obtener_actividad_usuario` | COUNT auth_audit_log (residual P0) |
| 13 | P-01 | `permiso_service.py` | `asignar_o_actualizar_permiso` | check rol_menu_permiso |
| 14 | P-03 | `permiso_service.py` | `obtener_permiso_especifico` | get by cliente/rol/menu |
| 15 | T-02 | `tenant_service.py` | `obtener_configuracion_tenant` | federacion_identidad |
| 16 | T-03 | `tenant_service.py` | `obtener_modulos_activos` | cliente_modulo_activo ⋈ modulo |

† Query principal de actividad ya migrada en K2-P0; P1 completa el COUNT con `:cliente_id` nombrado.

**Total call sites corregidos:** 16 (10 en `UserService`, 2 Superadmin TD, 2 Permiso, 2 Tenant).

---

## Diff arquitectónico (representativo)

### Antes (MEDIUM — WARNING TD-08)

```text
qmark_sql_text("... WHERE ur.usuario_id = ? AND ur.cliente_id = ?", (uid, cid))
  → :p0, :p1
  → _has_tenant_filter() FAIL
  → [TENANT_FILTER] WARNING (Shared) / intento inyección fallida
```

### Después (F13-D2)

```text
text("... WHERE ur.usuario_id = :usuario_id AND ur.cliente_id = :cliente_id")
  .bindparams(usuario_id=..., cliente_id=...)
  + client_id=cliente_id en execute_query
  → _has_tenant_filter() PASS
  → sin WARNING
```

**Comportamiento SQL:** idéntico — mismo predicado tenant, mismos valores bind.

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `app/modules/users/application/services/user_service.py` | 10 consultas qmark → `text().bindparams` + `client_id=` |
| `app/modules/superadmin/application/services/superadmin_usuario_service.py` | `_obtener_roles_usuario`, COUNT actividad |
| `app/modules/rbac/application/services/permiso_service.py` | check + get específico menú |
| `app/modules/tenant/application/services/tenant_service.py` | SSO + módulos activos |
| `tests/unit/test_f13_k2_p1_medium_td08.py` | Golden tests P1 |

---

## Consultas pendientes LOW (fuera alcance P1)

| K1 ID | Archivo | Método / área | Clasificación | Notas |
|-------|---------|---------------|---------------|-------|
| S-U-01 | `superadmin_usuario_service.py` | `_fetch_cliente_info_from_admin` | LOW | CP `cliente` + `kwargs_control_plane_read` |
| S-U-02 | `superadmin_usuario_service.py` | `get_usuarios_globales` COUNT/DATA | MEDIUM‡ | Excluido P1 — global ENGINE_SCOPED; drill-down con `?` dinámico pendiente K2-P2 |
| S-U-04 | idem | CP lookup usuario | LOW | `kwargs_platform_global_user_lookup` |
| S-U-07 | idem | sesiones refresh_tokens | LOW | ENGINE_SCOPED session store |
| S-A-01..03 | `superadmin_auditoria_service.py` | 8× listados/stats | LOW | ENGINE_SCOPED |
| C-01, C-02 | `cliente_service.py` | validaciones subdominio/código | LOW | CP |
| T-01 | `tenant_service.py` | query catálogo `cliente` | LOW | GLOBAL_TABLES / CP |
| — | `menu_service` / `area_service` | string SQL legacy | LOW† | Deuda E2B3K distinta |

‡ K2-P2 sugerido en K1 para silenciar enriquecimiento listado global filtrado.  
† No pipeline TextClause TD-08.

---

## Validación

### Pytest

```bash
python -m pytest tests/unit/test_f13_k2_p1_medium_td08.py -v
python -m pytest tests/unit/test_f13_k2_p0_critical_td08.py -v
python -m pytest tests/unit/test_defensive_tenant_filter.py -v
python -m pytest tests/unit/test_f13_j2_platform_fail_soft_superadmin_usuarios.py -v
python -m pytest tests/unit/test_f13_j3_platform_fail_soft_dashboard.py -v
```

**Resultado (2026-06-25):** **46 passed** (18 P1 + 12 P0 + 6 defensive + 5 J2 + 5 J3).

### Criterios TD-08

| Grupo P1 | `_has_tenant_filter` | Dedicated `apply_tenant_filter` |
|----------|:--------------------:|:-------------------------------:|
| usuario / usuario_rol | ✅ | ✅ sin SecurityError |
| rol_menu_permiso | ✅ | ✅ |
| superadmin roles | ✅ | ✅ |
| tenant SSO / módulos | ✅ | ✅ |

### Regresiones verificadas

| Área | Tests | Estado |
|------|-------|--------|
| K2-P0 CRITICAL | `test_f13_k2_p0_critical_td08.py` | ✅ 12/12 |
| Filtro defensivo Dedicated | `test_defensive_tenant_filter.py` | ✅ 6/6 |
| Fail-soft J2 usuarios global | `test_f13_j2_platform_fail_soft_superadmin_usuarios.py` | ✅ 5/5 |
| Fail-soft J3 dashboard stats | `test_f13_j3_platform_fail_soft_dashboard.py` | ✅ 5/5 |

---

## Impacto esperado en warnings Platform

| Flujo | Antes P1 | Después P1 |
|-------|----------|------------|
| Enriquecimiento roles por fila (`_obtener_roles_usuario`) | 1 WARNING/fila reachable | 0 |
| CRUD usuario Tenant / Platform indirecto | WARNING por operación qmark | 0 en rutas migradas |
| Listado global sin `cliente_id` (S-U-02) | Sin cambio | Sin cambio (excluido) |
| Permiso menú check/get | WARNING en mutaciones | 0 |

---

## Restricciones de este entregable

- Sin commits.
- Sin cambios arquitectónicos (OSR, routing, reachability, middleware).
- Detenido tras P1 MEDIUM.

**Estado:** F13-K2-P1 completado.
