# F13-K2-P2 — Implementación final TD-08 residual (S-U-02)

**Fecha:** 2026-06-25  
**Prerequisitos:** F13-K2-P2A (auditoría quirúrgica), F13-K2-P1, F13-M2  
**Estado:** **IMPLEMENTADO** — remediación S-U-02a/S-U-02b únicamente  
**Alcance:** `count_usuarios_globales` + `get_usuarios_globales` (COUNT + SELECT)

---

## Objetivo

Eliminar el warning TD-08 en:

```http
GET /api/v1/superadmin/usuarios/?cliente_id=00000000-0000-0000-0000-000000000001&page=1&limit=50
```

sin alterar contrato HTTP, enriquecimiento J2, ni arquitectura OSR/routing.

---

## Cambios realizados

**Archivo único de producción:** `app/modules/superadmin/application/services/superadmin_usuario_service.py`

| Elemento | Descripción |
|----------|-------------|
| `_usuarios_globales_where_to_named()` | Convierte WHERE posicional del builder (`?`) a nombres F13-D2 (`:cliente_id`, `:search`, `:es_activo`, `:proveedor_autenticacion`) **sin modificar** `_build_usuarios_globales_where` |
| `count_usuarios_globales` L369–377 | `qmark_sql_text` → `text(...).bindparams(**bind_params)` |
| `get_usuarios_globales` L476–484 | Idem + `OFFSET :offset` / `FETCH NEXT :limit` |

### Patrón aplicado (F13-D2)

**Antes (P2A — WARNING):**

```text
qmark_sql_text(COUNT/SELECT, tuple(params))
→ u.cliente_id = :p0
→ _has_tenant_filter FAIL
→ [TENANT_FILTER] WARNING
```

**Después (P2):**

```python
named_where, bind_params = _usuarios_globales_where_to_named(where_clause, params)
text(f"... WHERE {named_where}").bindparams(**bind_params)
# SELECT añade bind_params["offset"], bind_params["limit"]
```

**SQL mono-tenant shared (`database_type=single`, `cliente_id=SYSTEM`):**

```sql
SELECT COUNT(*) AS total
FROM dbo.usuario u
WHERE u.es_eliminado = 0 AND u.cliente_id = :cliente_id
```

```sql
SELECT u.usuario_id, ...
FROM dbo.usuario u
WHERE u.es_eliminado = 0 AND u.cliente_id = :cliente_id
ORDER BY u.fecha_creacion DESC
OFFSET :offset ROWS
FETCH NEXT :limit ROWS ONLY
```

---

## Sin modificar (confirmado)

| Área | Estado |
|------|--------|
| `_build_usuarios_globales_where` | Sin cambio (sigue `?` posicionales) |
| Filtros / orden / paginación semántica | Sin cambio |
| Enriquecimiento J2 | Sin cambio |
| M2 count/list parity | Preservado |
| `query_helpers.py` | Sin cambio |
| `execute_query` / routing / OSR | Sin cambio |
| OpenAPI / Frontend | Sin cambio |
| Otros `qmark_sql_text` en el mismo archivo | Sin cambio (S-U-04, S-U-07, etc.) |

---

## Tests

**Nuevo:** `tests/unit/test_f13_k2_p2_su02_td08.py` (7 tests)

| Test | Valida |
|------|--------|
| `test_su02_count_has_tenant_filter_named_cliente_id` | `_has_tenant_filter` PASS |
| `test_su02_select_has_tenant_filter_named_cliente_id` | Idem SELECT |
| `test_su02_count_apply_tenant_filter_shared_no_warning` | Sin `[TENANT_FILTER]` WARNING |
| `test_su02_count_apply_tenant_filter_dedicated_no_security_error` | Sin `SecurityError` Dedicated |
| `test_su02_select_apply_tenant_filter_dedicated_no_security_error` | Idem SELECT |
| `test_count_uses_named_bindparams_not_qmark` | Runtime usa `:cliente_id`, no `:p0` |
| `test_get_list_uses_named_offset_limit` | `:offset`, `:limit` nombrados |

**Regresión ejecutada:**

```bash
python -m pytest \
  tests/unit/test_f13_k2_p2_su02_td08.py \
  tests/unit/test_f13_m2_count_usuarios_globales_parity.py \
  tests/unit/test_f13_j2_platform_fail_soft_superadmin_usuarios.py \
  tests/unit/test_f13_k2_p1_medium_td08.py \
  tests/unit/test_f13_k2_p0_critical_td08.py \
  -v
```

**Resultado:** **48 passed**

---

## Validaciones obligatorias (checklist)

| # | Criterio | Evidencia |
|---|----------|-----------|
| 1 | `GET /superadmin/usuarios/?cliente_id=SYSTEM` sin WARNING TD-08 | Tests P2 `apply_tenant_filter` + named bindparams |
| 2 | `GET /superadmin/usuarios/` global sin regresión | J2 tests 5/5; global usa ENGINE_SCOPED (sin `:cliente_id` en WHERE) |
| 3 | Tenant Admin sin regresión | P0/P1 suites green |
| 4 | Dedicated sin `SecurityError` | P2 dedicated + P0 critical |
| 5 | Shared sin cambio funcional | M2 parity + P1 shared |
| 6 | `count_usuarios_globales == total_usuarios` | M2 `test_count_equals_list_total_global` |
| 7 | Warning eliminado en ambos call sites | P2 unit + P2A call sites migrados |

---

## Notas

- Listado **global sin `cliente_id`** no tenía WARNING S-U-02 (ENGINE_SCOPED); comportamiento idéntico.
- Rama **Dedicated `database_type=multi`** (sin `u.cliente_id` en WHERE) no fue objetivo de P2A; sigue ENGINE_SCOPED vía OSR — fuera del síntoma `cliente_id=SYSTEM`.
- `_usuarios_globales_where_to_named` es adaptador interno P2; migración futura opcional: nombrar directamente en el builder (fuera de alcance).

---

## Referencias

| Documento | Relación |
|-----------|----------|
| `F13_K2_P2A_RESIDUAL_TD08_AUDIT.md` | Origen exacto S-U-02 |
| `F13_K2_P1_MEDIUM_IMPLEMENTATION.md` | Exclusión previa S-U-02 |
| `F13_M2_INTERNAL_REFACTOR.md` | Paridad count/list |

---

**Fin F13-K2-P2 — sin commits.**
