# F13-M2 — Refactor interno KPI / Listado global (sin cambio de contrato)

**Fecha:** 2026-06-25  
**Prerequisito:** F13-M1 (`F13_M1_KPI_ENRICHMENT_ARCHITECTURE.md`)  
**Estado:** **IMPLEMENTADO** — Fase 1 del plan M1; **sin endpoint `/stats`**, **sin cambio OpenAPI/FE**  
**Alcance:** `SuperadminUsuarioService` — extracción COUNT-only + reutilización en listado enriquecido.

---

## 0. Veredicto

| Criterio | Resultado |
|----------|-----------|
| Contrato HTTP / JSON | **Sin cambio** — `GET /superadmin/usuarios/` idéntico |
| J2 fail-soft | **Preservado** — bucle enriquecimiento intacto |
| OSR / reachability en listado | **Sin cambio** |
| Nuevo endpoint `/stats` | **No implementado** (Fase M1-2 pendiente) |
| Tests | **11 passed** — 6 M2 + 5 J2 regresión |

---

## 1. Métodos extraídos / añadidos

**Archivo:** `app/modules/superadmin/application/services/superadmin_usuario_service.py`

| Método | Visibilidad | Responsabilidad |
|--------|-------------|-----------------|
| `_build_usuarios_globales_where(...)` | privado estático | WHERE, params base, `order_field`, `order_dir` |
| `_resolve_usuarios_globales_query_kwargs(cliente_id)` | privado estático | `kwargs_platform_global_read()` vs `resolve_platform_tenant_data_execute_kwargs()` |
| `_resolve_usuarios_globales_cliente_context(cliente_id)` | privado estático | Resolución `ClienteInfo` + `database_type` (helper interno M2) |
| `count_usuarios_globales(...)` | **público** estático | COUNT-only → `int` |
| `get_usuarios_globales(...)` | público | Delega total a `count_usuarios_globales`; conserva SELECT + J2 |

### 1.1 `_build_usuarios_globales_where`

**Entrada:** `cliente_id`, `database_type`, filtros (`search`, `es_activo`, `proveedor_autenticacion`), ordenamiento.

**Salida:** `(where_clause, params, order_field, order_dir)`.

**Contenido (sin alteración lógica):**

- `u.es_eliminado = 0`
- Filtro `cliente_id` solo si `database_type == "single"`
- Filtros búsqueda / activo / proveedor
- Whitelist `ordenar_por` + dirección ASC/DESC

### 1.2 `_resolve_usuarios_globales_query_kwargs`

```python
if cliente_id:
    return await resolve_platform_tenant_data_execute_kwargs(cliente_id)
return kwargs_platform_global_read()
```

Centraliza la decisión global vs mono-tenant routing.

### 1.3 `count_usuarios_globales`

**Ejecuta:** resolución contexto → `_build_usuarios_globales_where` → `_resolve_usuarios_globales_query_kwargs` → `SELECT COUNT(*)`.

**No ejecuta:** SELECT paginado, reachability, `_obtener_roles_usuario`, `get_user_level_info`, `is_super_admin`.

**Retorno:** `int` (`total_usuarios`).

**Filtros soportados:** mismos que listado excepto `page`/`limit` (no aplican a COUNT).

### 1.4 `get_usuarios_globales` (refactor)

Flujo post-M2:

```text
validar page/limit
→ _resolve_usuarios_globales_cliente_context
→ count_usuarios_globales(...)           ← total
→ _build_usuarios_globales_where         ← SELECT
→ _resolve_usuarios_globales_query_kwargs
→ execute_query(SELECT … OFFSET/FETCH)
→ bucle enriquecimiento J2 (sin cambios)
→ return { usuarios, total_usuarios, pagina_actual, total_paginas }
```

---

## 2. Diagrama de responsabilidades

```text
                    count_usuarios_globales
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
_resolve_cliente_context  _build_where    _resolve_query_kwargs
         │                    │                    │
         └────────────────────┴────────────────────┘
                              │
                         COUNT(*) only


                    get_usuarios_globales
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
    count_usuarios_globales  _build_where   SELECT + bucle J2
         (total)              (mismos filtros)  (enriquecimiento)
```

---

## 3. Tests

**Archivo:** `tests/unit/test_f13_m2_count_usuarios_globales_parity.py`

| Test | Verifica |
|------|----------|
| `test_count_equals_list_total_global` | `count_usuarios_globales() == get_usuarios_globales()["total_usuarios"]` |
| `test_count_and_list_share_where_builder` | Mismos kwargs al builder y kwargs resolver con filtros |
| `test_count_shared_mono_tenant_uses_cliente_id_filter` | Shared: WHERE incluye filtro `cliente_id` |
| `test_count_dedicated_mono_tenant_no_cliente_id_in_where` | Dedicated: sin filtro `cliente_id`; OSR invocado |
| `test_count_does_not_invoke_enrichment` | Sin reachability / roles / level_info |
| `test_count_executes_only_count_query` | Una sola query SQL; sin OFFSET/FETCH |

**Regresión J2:** `tests/unit/test_f13_j2_platform_fail_soft_superadmin_usuarios.py` — **5 passed**.

```bash
python -m pytest tests/unit/test_f13_m2_count_usuarios_globales_parity.py \
  tests/unit/test_f13_j2_platform_fail_soft_superadmin_usuarios.py -v
```

---

## 4. Lo que NO cambió

| Área | Estado |
|------|--------|
| Endpoints / OpenAPI | Sin cambio |
| `PaginatedUsuarioSuperadminResponse` | Sin cambio |
| Frontend / contrato dashboard | Sin cambio |
| Fail-soft J2 (L434–472) | Lógica idéntica |
| J3 / `ClienteService.obtener_estadisticas` | Sin cambio |
| RI-39 / routing / OSR | Sin cambio |

---

## 5. Nota de implementación

### Resolución duplicada en `get_usuarios_globales`

Cuando `cliente_id` está presente, `get_usuarios_globales` resuelve contexto cliente y `count_usuarios_globales` lo resuelve de nuevo internamente. **JSON y errores observables son idénticos**; hay una segunda consulta CP/OSR por request mono-tenant. Optimización diferida a fase `/stats` o parámetro opcional de contexto pre-resuelto.

### Próximo paso (F13-M3 / M1 Fase 2)

Exponer `count_usuarios_globales` vía `GET /superadmin/usuarios/stats` y migrar FE W12 — elimina RI-39 en bootstrap KPI sin tocar listado enriquecido.

---

## 6. Referencias

| Documento | Relación |
|-----------|----------|
| `F13_M1_KPI_ENRICHMENT_ARCHITECTURE.md` | Diseño A/B |
| `F13_L2_PLATFORM_BOOTSTRAP_RUNTIME_AUDIT.md` | Síntoma bootstrap |
| `F13_J2_PLATFORM_FAIL_SOFT_SUPERADMIN_USUARIOS.md` | Fail-soft listado |

---

**Fin F13-M2 — sin commits.**
