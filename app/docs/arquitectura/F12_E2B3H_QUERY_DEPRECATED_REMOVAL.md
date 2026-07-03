# F12-E2B3H — QUERY DEPRECATED Removal

**Fecha:** 2026-06-28  
**Referencia:** F12-E2B3E (L-90 `[QUERY] DEPRECATED` ~1×/menu tenant)  
**Alcance:** Migración de consumidores legacy `execute_query(str)` → `sqlalchemy.text()`  
**Sin cambios:** `queries_async.py` (warning conservado), contratos HTTP, lógica funcional

---

## 1. Resumen ejecutivo

| Métrica | Antes (F12-E2B3E) | Después (F12-E2B3H) |
|---------|-------------------|---------------------|
| `[QUERY] DEPRECATED` / smoke Shared (`GET /auth/menu`) | **~1** | **0** |
| `[QUERY] DEPRECATED` / smoke extendido Platform + Shared | **≥1** | **0** |
| HTTP smoke (login, me, menu, permissions, org/empresa, usuarios, roles, refresh) | 200 | **200** (idéntico) |
| Dedicated runtime | no smoke credencial | sin cambio (paridad código) |

Se eliminó la deuda en los **callers** identificados en runtime normal; el warning en `queries_async.py` permanece como guardia para SQL string residual no migrado.

---

## 2. Causa raíz

`execute_query()` acepta tres formas: SQLAlchemy Core `select()`, `TextClause` (`text().bindparams()`), y **string SQL legacy** (`str`). El branch `isinstance(query, str)` emite:

```text
[QUERY] DEPRECATED: execute_query() recibió string SQL. Migrar a SQLAlchemy Core.
```

En runtime con flags OFF (F12-E2B3E), el único emisor en flujos normales era **`ModuloMenuService.obtener_menu_usuario`** — QUERY 2 permisos (`rol_menu_permiso`) construida como f-string + `params` tupla con `?`.

Smoke extendido (roles/usuarios) detectó además **`RolService.get_min_required_access_level`** vía `RoleChecker(["Administrador"])` en dependencias admin — misma anti‑patrón.

---

## 3. Inventario de callers migrados

| ID | Archivo | Función / contexto | Trigger HTTP |
|----|---------|-------------------|--------------|
| Q-01 | `modulo_menu_service.py` | `obtener_menu_usuario` — rama `permisos_rol_id` (impersonación/admin_rol) | `GET /auth/menu` |
| Q-02 | `modulo_menu_service.py` | `obtener_menu_usuario` — rama usuario normal (`usuario_rol` ⋈ `rol_menu_permiso`) | `GET /auth/menu` |
| Q-03 | `rol_service.py` | `get_min_required_access_level` | `RoleChecker` en `require_admin` (roles, usuarios, …) |
| Q-04 | `rol_service.py` | `_verificar_nombre_rol_unico` | mutaciones rol (preventivo) |
| Q-05 | `rol_service.py` | `get_all_active_roles` | `GET /roles/all-active/` (preventivo) |

---

## 4. SQL anterior vs equivalente SQLAlchemy Core

### Q-01 / Q-02 — Permisos menú (`modulo_menu_service.py`)

**Antes (string + `?`):**

```sql
-- Rama impersonación
WHERE p.rol_id = ? AND p.cliente_id = ? AND p.menu_id IN (?,?,...)

-- Rama usuario
WHERE ur.usuario_id = ? AND ur.cliente_id = ? … AND p.cliente_id = ?
  AND (ur.empresa_id IS NULL OR ur.empresa_id = ?)  -- si empresa scope
```

**Después (`text()` + bindparams nombrados):**

```sql
WHERE p.rol_id = :rol_id AND p.cliente_id = :cliente_id
  AND p.menu_id IN (:menu_id_0, :menu_id_1, …)

WHERE ur.usuario_id = :usuario_id AND ur.cliente_id = :cliente_id
  AND (ur.empresa_id IS NULL OR ur.empresa_id = :empresa_id)  -- sql_empresa_filter_usuario_rol
  AND p.cliente_id = :p_cliente_id
  AND p.menu_id IN (:menu_id_0, …)
```

Filtro empresa: migrado de `sql_empresa_filter_usuario_rol_qmark` → `sql_empresa_filter_usuario_rol` (`:empresa_id`).

### Q-03 — Nivel mínimo rol (`get_min_required_access_level`)

**Antes:**

```sql
WHERE nombre IN (?,?,…) AND es_activo = 1 AND (cliente_id = ? OR cliente_id IS NULL)
```

**Después:**

```sql
WHERE nombre IN (:role_0, :role_1, …) AND es_activo = 1
  AND (cliente_id = :cliente_id OR cliente_id IS NULL)
```

### Q-04 — Unicidad nombre rol

**Antes:** `cliente_id = ? AND LOWER(nombre) = LOWER(?)`  
**Después:** `:cliente_id`, `:nombre`, `:rol_id_excluir` (opcional)

### Q-05 — Roles activos

**Antes:** `cliente_id = ? OR cliente_id IS NULL`  
**Después:** `:cliente_id`

---

## 5. Validación

### 5.1 Unit tests

```text
tests/unit/test_menu_empresa_scope.py — 6 passed (asserts actualizados :empresa_id)
tests/unit/test_menu_usuario_logging_f12_e2b3c.py — 2 passed
```

### 5.2 Smoke HTTP extendido (`LOG_LEVEL=INFO`, flags OFF)

| Plano | Endpoints | Resultado |
|-------|-----------|-----------|
| **Platform** | login, me, menu, permissions, refresh | **200** |
| **Shared (`acme`)** | login, me, menu, permissions, org/empresa, **usuarios**, **roles**, refresh | **200** |
| **Dedicated** | — | credencial smoke 401 (limitación E2B3E) |

### 5.3 Conteo `[QUERY] DEPRECATED`

| Escenario | Antes | Después |
|-----------|------:|--------:|
| `GET /auth/menu` (acme) | **1** | **0** |
| `GET /roles/?page=1` (acme) | **1** | **0** |
| Ciclo extendido Platform + Shared | **≥1** | **0** |

Verificación: `docker logs fastapi_backend --since 30s | grep DEPRECATED` → **vacío** post-smoke.

### 5.4 Regresión funcional

- Menú Shared: `modulos_count=3` (ORG, INV, SYS_ADMIN) — sin cambio.
- Listados usuarios/roles: HTTP 200, mismos contratos paginados.
- Session scope / empresa: sin alteración (solo capa SQL).

---

## 6. Riesgos

| Riesgo | Nivel | Mitigación |
|--------|-------|------------|
| IN clause dinámica mal bindada | Medio | Patrón `:menu_id_N` / `:role_N` probado en unit + smoke |
| `RoleChecker` LBAC | Bajo | Misma SQL semántica; smoke admin OK |
| Callers legacy no migrados (otros módulos) | Medio | Warning conservado; inventario §8 |
| Dedicated no smokeado | Bajo | Mismos servicios; credencial pendiente |

---

## 7. Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `app/modules/modulos/application/services/modulo_menu_service.py` | Q-01, Q-02 → `text().bindparams()` |
| `app/modules/rbac/application/services/rol_service.py` | Q-03, Q-04, Q-05 → `text().bindparams()`; import `text` |
| `tests/unit/test_menu_empresa_scope.py` | Asserts `:empresa_id` vs `?` |
| `app/docs/arquitectura/F12_E2B3H_QUERY_DEPRECATED_REMOVAL.md` | Este informe |

**No modificado:** `app/infrastructure/database/queries_async.py` (warning intentional).

---

## 8. Fuera de alcance — SQL legacy residual (no emitido en smoke validado)

Consumidores `execute_query(str, tuple)` aún presentes en codebase; **no ejecutados** en el smoke F12-E2B3H:

| Módulo | Ejemplos |
|--------|----------|
| `user_service.py` | `obtener_usuario_por_id`, `check_query` eliminación |
| `area_service.py` / `menu_service.py` | constantes `GET_*_QUERY` en `queries.py` |
| `permiso_service.py` | queries tupla `?` |
| `tenant_service.py`, `cliente_service.py` | lookups subdominio |
| `superadmin_usuario_service.py` | queries admin tupla |

Recomendación: fase posterior migrando módulo a módulo; mientras tanto el warning detecta cualquier reintroducción.

---

## 9. Conclusión

Runtime normal (Platform + Shared, flujos auth/admin validados) ya **no emite `[QUERY] DEPRECATED`**. La deuda identificada en F12-E2B3E queda cerrada en los paths de ejecución normal; el guard en `queries_async.py` sigue activo para SQL string residual fuera de alcance.
