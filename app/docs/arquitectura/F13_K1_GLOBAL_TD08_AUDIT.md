# F13-K1 — Auditoría global de deuda residual TD-08

**Fecha:** 2026-06-25  
**Modo:** Solo auditoría — **sin cambios de código, sin commits**  
**Prerequisitos:** F13-D1/D2 (rol_menu_permiso), F13-I3/I5 (RBAC Platform), F12-E2B3K/L (TextClause + tenant filter), F13-J1–J3 (fail-soft Platform)  
**Síntoma:** Warnings repetitivos en runtime / CI:

```text
[TENANT_FILTER] No se pudo aplicar filtro automático a TextClause: ...
This text() construct doesn't define a bound parameter named 'cliente_id'
```

---

## 1. Resumen ejecutivo

| Métrica | Valor |
|---------|------:|
| Call sites `qmark_sql_text()` en `app/modules/` | **41** (excl. definición en `query_helpers.py`) |
| Call sites `text().bindparams()` riesgo TD-08 (Platform/IAM revisados) | **~15** adicionales |
| Patrones **CRITICAL** (Dedicated → `SecurityError` TD-08 posible) | **7** call sites / **5** métodos |
| Patrones **HIGH** (WARNING + riesgo funcional en drill-down Platform) | **6** |
| Patrones **MEDIUM** (WARNING ruido; filtro semántico vía `:p0` pero detector ciego) | **~24** |
| Patrones **LOW** (GLOBAL_TABLES / ENGINE_SCOPED / CP-only) | **~18** |
| Fixes F13 ya aplicados (no re-auditar como deuda abierta) | **3** rutas RBAC |

**Veredicto:** La deuda TD-08 **no está cerrada**. F13-D2/I3/I5 corrigieron rutas RBAC de lectura de permisos menú/negocio, pero persisten **41 usos de `qmark_sql_text`** que producen parámetros `:p0`/`:p1` invisibles para `_has_tenant_filter()`. Tras F13-J3, los warnings más visibles siguen originándose en **Superadmin** (listado global + enriquecimiento por fila) y **`UserService`** (Tenant ERP/IAM), no en `ClienteService.obtener_estadisticas` (J3 ya usa `:cliente_id` nombrado).

**Causa raíz (sin cambio desde F12-E2B3L):**

1. `qmark_sql_text()` renombra `?` → `:p0`, `:p1`, …  
2. `_has_tenant_filter()` solo reconoce `cliente_id = :cliente_id` o `:client_id` (regex literal).  
3. Si no detecta filtro y el contexto **no** es `ENGINE_SCOPED`, `apply_tenant_filter_to_text_clause` intenta inyectar `:cliente_id` y reconstruir bindparams → fallo SQLAlchemy → **WARNING** (Shared) o **`SecurityError`** (Dedicated).

---

## 2. Mecanismo TD-08 (referencia)

| Componente | Rol |
|------------|-----|
| `queries_async.execute_query(TextClause)` | Invoca `_prepare_text_clause_for_gateway` |
| `query_helpers.apply_tenant_filter_to_text_clause` | Inyección defensiva / validación |
| `query_helpers._has_tenant_filter` | Detección por substring regex |
| `IdentityScope.ENGINE_SCOPED` | Omite filtro (Platform global CP — F12-E2B3N) |
| `GLOBAL_TABLES` | Omite filtro (`cliente`, `permiso`, catálogos globales, etc.) |

**Mensaje exacto:** capturado en `except` de reconstrucción `text(...).bindparams(**existing_params, cliente_id=…)` cuando el SQL modificado **no** declara placeholder `:cliente_id`.

---

## 3. Fixes F13 ya aplicados (fuera de alcance K1)

| Ticket | Archivo / método | Patrón corregido | Estado |
|--------|------------------|------------------|--------|
| **F13-D2** | `PermisoService.obtener_permisos_por_rol` | `text().bindparams(cliente_id=, rol_id=)` | ✅ Conforme |
| **F13-I3** | `RolService.obtener_rol_por_id` + callers | `cliente_id` explícito + OSR | ✅ Conforme (lookup) |
| **F13-I5** | `get_permisos_negocio_rol` + `get_permisos_negocio_by_rol` | Propagación `cliente_id` | ✅ Conforme (GET) |
| **F13-J3** | `ClienteService.obtener_estadisticas` | `text(...).bindparams(cliente_id=)` en KPIs TD | ✅ Conforme |

**Deuda abierta en el mismo dominio RBAC:**

| Ruta | Estado |
|------|--------|
| `PermisoService.asignar_o_actualizar_permiso` (check L264, get L294, específico L486) | ❌ qmark residual |
| PUT `/roles/{id}/permisos-negocio/` | ❌ No cubierto por I5 |

---

## 4. Inventario cuantitativo `qmark_sql_text`

| Módulo | Call sites | CRITICAL | HIGH | MEDIUM | LOW |
|--------|----------:|:--------:|:----:|:------:|:---:|
| `superadmin_usuario_service.py` | 13 | 0 | 4 | 3 | 6 |
| `superadmin_auditoria_service.py` | 8 | 0 | 0* | 0* | 8 |
| `user_service.py` | 13 | 4 | 0 | 9 | 0 |
| `permiso_service.py` | 3 | 1 | 0 | 2 | 0 |
| `tenant_service.py` | 3 | 0 | 0 | 2 | 1 |
| `cliente_service.py` | 2 | 0 | 0 | 0 | 2 |
| **Total** | **41** | **5** | **4** | **16** | **16** |

\* Auditoría: todos usan `kwargs_platform_global_read` / `kwargs_control_plane_read` → `ENGINE_SCOPED`. Generan **0 WARNING TD-08** en condiciones normales; clasificados LOW para deuda de estilo/migración.

---

## 5. Hallazgos Platform / IAM (prioridad)

### 5.1 `SuperadminUsuarioService` — 13 qmark

| # | Método | Tabla(s) | Plano | `_has_tenant_filter` | Crit | TD-08 WARN | TD-08 ERR | Platform | Tenant | Shared | Dedicated | Recomendación mínima |
|---|--------|----------|-------|----------------------|:----:|:----------:|:---------:|:--------:|:------:|:------:|:---------:|----------------------|
| S-U-01 | `_fetch_cliente_info_from_admin` | `cliente` | CP | N/A (GLOBAL) | LOW | No | No | Sí | No | Sí | Sí | Mantener; opcional migrar a `text().bindparams(cliente_id=)` + ADMIN |
| S-U-02 | `get_usuarios_globales` count/data | `usuario` | TD | FAIL (`:pN`) | **MEDIUM** | **Sí**† | Raro | Sí | No | Sí | Sí | Migrar a `:cliente_id` nombrado; global sin filtro → `ENGINE_SCOPED` explícito |
| S-U-03 | `_obtener_roles_usuario` | `rol`, `usuario_rol` | TD | FAIL (presente `:p1`) | MEDIUM | **Sí**† | Raro | Sí | No | Sí | Sí | `ur.cliente_id = :cliente_id AND ur.usuario_id = :usuario_id` + `client_id=` |
| S-U-04 | `obtener_usuario_completo` CP lookup | `usuario` (ADMIN) | CP/TD identity | FAIL | LOW | No‡ | No | Sí | No | Sí | Sí | OK con `kwargs_platform_global_user_lookup` (ENGINE_SCOPED) |
| S-U-05 | `obtener_usuario_completo` body | `usuario` | TD | **FAIL (sin filtro)** | **HIGH** | Sí | **Sí** | Sí | No | Parcial | **Sí** | Añadir `AND u.cliente_id = :cliente_id` o ENGINE_SCOPED documentado |
| S-U-06 | `obtener_actividad_usuario` audit | `auth_audit_log` | TD | FAIL (solo `usuario_id`) | **HIGH** | Sí | **Sí** | Sí | No | Parcial | **Sí** | Named params + filtro tenant explícito |
| S-U-07 | `obtener_sesiones_usuario` V1/V2 | `refresh_tokens` / session store | TD | FAIL | LOW | No‡ | No | Sí | No | Sí | Sí | Session store path usa scope dedicado |
| S-U-08 | Enriquecimiento post-J2 | — | TD | — | — | — | — | Sí | No | Sí | Sí | J2 evita RI-39; **no elimina** WARNING qmark en filas reachable |

† WARNING proporcional a filas (`2 + 2×limit` en listado global — F12-E2B3L).  
‡ ENGINE_SCOPED en kwargs de lookup.

---

### 5.2 `SuperadminAuditoriaService` — 8 qmark

| # | Método | Tabla(s) | Plano | Crit | TD-08 WARN | Platform | Recomendación mínima |
|---|--------|----------|-------|:----:|:----------:|:--------:|----------------------|
| S-A-01 | `get_logs_autenticacion` count/data | `auth_audit_log` | CP‡ | LOW | No‡ | Sí | Migración estética a named params (opcional) |
| S-A-02 | `get_logs_sincronizacion` count/data | `log_sincronizacion_usuario` | CP‡ | LOW | No‡ | Sí | Idem; tabla CP sin columna `cliente_id` — **nunca** inyectar filtro tenant |
| S-A-03 | `obtener_estadisticas` auth/sync/top | `auth_audit_log`, `log_sincronizacion_usuario` | CP‡ | LOW | No‡ | Sí | Idem |

‡ Todos con `kwargs_platform_global_read` / `kwargs_control_plane_read` → **`identity_scope=ENGINE_SCOPED`**.

**Nota histórica F12-E2B3L:** sync listado HTTP 500 por inyección errónea en CP **previa** a E2B3N; con ENGINE_SCOPED actual el síntoma principal es **ruido potencial**, no bloqueo Platform.

---

### 5.3 `ClienteService` — 2 qmark + J3

| # | Método | Tabla(s) | Plano | Crit | TD-08 | Platform | Recomendación |
|---|--------|----------|-------|:----:|:-----:|:--------:|---------------|
| C-01 | `_validar_subdominio_cliente` | `cliente` | CP | LOW | No | Sí | Opcional: `text().bindparams(subdominio=)` |
| C-02 | `_validar_codigo_cliente` | `cliente` | CP | LOW | No | Sí | Idem |
| C-03 | `obtener_estadisticas` (J3) | `usuario`, `cliente_modulo`, `cliente_conexion` | TD+CP | **OK** | No | Sí | **Sin acción** — `:cliente_id` nombrado |

---

### 5.4 `TenantService` — 3 qmark

| # | Método | Tabla(s) | Plano | Crit | TD-08 WARN | Platform | Tenant | Recomendación |
|---|--------|----------|-------|:----:|:----------:|:--------:|:------:|---------------|
| T-01 | `obtener_configuracion_tenant` | `cliente` | CP | LOW | No | Parcial | Sí | Migrar `:cliente_id` |
| T-02 | same SSO | `federacion_identidad` | TD | MEDIUM | Sí | Parcial | Sí | `WHERE cliente_id = :cliente_id` nombrado |
| T-03 | `obtener_modulos_activos` | `cliente_modulo`+`modulo` | TD | MEDIUM | Sí | Parcial | Sí | `cma.cliente_id = :cliente_id` nombrado |

---

### 5.5 `PermisoService` — 3 qmark (deuda post-D2)

| # | Método | Línea | Tabla(s) | Plano | Crit | TD-08 ERR (Dedicated) | Recomendación |
|---|--------|------:|----------|-------|:----:|:---------------------:|---------------|
| P-01 | `asignar_o_actualizar_permiso` check | 264 | `rol_menu_permiso` | TD | MEDIUM | Raro | Patrón F13-D2 |
| P-02 | `asignar_o_actualizar_permiso` get-by-id | **294** | `rol_menu_permiso` | TD | **CRITICAL** | **Sí** | `WHERE permiso_id = :permiso_id AND cliente_id = :cliente_id` |
| P-03 | `obtener_permiso_especifico` | 486 | `rol_menu_permiso` | TD | MEDIUM | Raro | Patrón F13-D2 |

**Conforme (no deuda):** `obtener_permisos_por_rol` (F13-D2), lecturas con `text().bindparams(cliente_id=)`.

---

### 5.6 `UserService` — 13 qmark (Tenant + Platform indirecto)

| # | Método | Tabla(s) | Crit | TD-08 ERR | Shared WARN | Dedicated | Recomendación |
|---|--------|----------|:----:|:---------:|:-----------:|:---------:|---------------|
| U-01 | `obtener_usuario_completo_por_id` rama **multi** | `usuario`, `usuario_rol`, `rol` | **CRITICAL** | **Sí** | Sí | **Sí** | Añadir `u.cliente_id = :cliente_id` en WHERE dedicated |
| U-02 | `obtener_usuario_completo_por_id` rama shared | idem | MEDIUM | No | Sí | N/A | Named `:cliente_id` |
| U-03 | `obtener_usuario_por_id`, `verificar_*`, `eliminar_*`, etc. | `usuario` / `usuario_rol` | MEDIUM | Raro | Sí | Sí | Batch F13-D2 pattern |
| U-04 | `asignar_rol_a_usuario` / `revocar_rol` fetch by PK | `usuario_rol` | **CRITICAL** | **Sí** | Sí | **Sí** | `WHERE usuario_rol_id = :id AND cliente_id = :cliente_id` |
| U-05 | `listar_roles_usuario` | `usuario_rol`, `rol` | MEDIUM | Raro | Sí | Sí | Named params |

---

### 5.7 RBAC / Auth — `text()` sin qmark (muestra)

| Archivo | Método | Tabla(s) | Plano | `_has_tenant_filter` | Crit | Recomendación |
|---------|--------|----------|-------|----------------------|:----:|---------------|
| `permisos_negocio_service` | `_permisos_negocio_rol_*` | `rol_permiso`, `permiso` | TD+CP | **PASS** | LOW | Sin acción GET |
| `permisos_usuario_service` | permisos efectivos | `usuario_rol`, `rol_permiso` | TD | **PASS** | LOW | Sin acción |
| `impersonation_rbac` | `_impersonation_permisos_*` | `rol`, `rol_permiso` | TD | **PASS** | LOW | Sin acción |
| `rol_service` | paginate / deactivate | `rol` | TD | **PASS** | LOW | Sin acción |
| `auth_queries.IS_USER_SUPER_ADMIN` | vía `UsuarioService` | `usuario_rol`, `rol` | TD | **FAIL** | **HIGH** | Añadir `ur.cliente_id = :cliente_id` |
| `permiso_repository.find_permisos_by_rol` | legacy | `rol_permiso`, `permiso` | TD | **FAIL** | **HIGH** | Solo `rp.rol_id = :rol_id` — migrar o deprecar |
| `rol_repository.find_with_permisos` | legacy | idem | TD | **FAIL** | **HIGH** | Idem |

---

### 5.8 Otros servicios Platform revisados

| Servicio | Patrón | TD-08 residual | Notas |
|----------|--------|:--------------:|-------|
| `catalogos_globales_service` | SQLAlchemy Core `Select` | No | Sin TextClause |
| `cliente_modulo_service` | Core / named | No | — |
| `conexion_service` | `text().bindparams(cliente_id=)` | No | CP `cliente_conexion` |
| `active_sessions_read_service` | session store Core | No | — |
| `menu_service` / `area_service` | **string SQL** legacy `(?, …)` | No† | Emite `[QUERY] DEPRECATED`, **no** pipeline TextClause TD-08 |
| `modulo_menu_service` | mix `:cliente_id` / `:p_cliente_id` | Parcial | Detección OK si existe `ur.cliente_id = :cliente_id` en la misma query |

† Deuda distinta (migración E2B3K pendiente en menús).

---

## 6. Infraestructura / ERP (resumen)

| Área | `text()` en `infrastructure/database/queries/**` | `qmark_sql_text` | Riesgo TD-08 |
|------|--------------------------------------------------|------------------|:------------:|
| Módulos ERP (`inv`, `org`, `sls`, …) | ~160+ archivos Core `Select` | **0** | Bajo — path Core usa `_select_has_explicit_tenant_predicate` |
| `auth/session/*_core.py` | 7 `text()` | 0 | Medio — revisar si falta `:cliente_id` en V2 session |
| `auth/auth_queries.py` | 3 constantes | 0 | **HIGH** solo `IS_USER_SUPER_ADMIN` |
| `refresh_token_queries_core.py` | legacy V1 | 0 | Medio |

**Recomendación ERP:** no abrir remediación masiva; aplicar patrón F13-D2 solo en rutas IAM compartidas con Platform (`UserService`, auth queries).

---

## 7. Mapa de warnings post-F13-J3

Tras J3, `GET /clientes/{id}/estadisticas/` **no** debería emitir `[TENANT_FILTER]` (queries J3 conformes). Warnings residuales observables en smoke Platform:

| Endpoint / flujo | Origen probable | Warnings estimados |
|------------------|-----------------|-------------------:|
| `GET /superadmin/usuarios/` global | S-U-02, S-U-03 por fila | `2 + 2×limit` |
| `GET /superadmin/usuarios/{id}` | S-U-05 | 1–2 |
| `GET /superadmin/auditoria/autenticacion/` | S-A-01 | 0 (ENGINE_SCOPED) |
| `GET /superadmin/auditoria/estadisticas/` | S-A-03 | 0 (ENGINE_SCOPED) |
| Tenant admin Dedicated → usuarios/RBAC | U-*, P-02 | Variable; **CRITICAL** en mutaciones permiso |

---

## 8. Matriz de impacto por modo de instalación

| Crit | Shared | Dedicated | Platform | Tenant ERP |
|:----:|:------:|:---------:|:--------:|:----------:|
| CRITICAL | WARN + datos OK† | **SecurityError** | Drill-down SA + permiso write | User/rol PK lookups |
| HIGH | WARN | ERR/WARN | SA mono-usuario, superadmin check | Auth superadmin query |
| MEDIUM | WARN ruido | WARN/ERR | Listados SA enrichment | CRUD usuario qmark |
| LOW | — | — | CP catalog, auditoría ENGINE_SCOPED | Validaciones cliente |

† Filtro semántico often presente vía `:p0` aunque detector falle.

---

## 9. Recomendación mínima por fases (sin implementar)

| Fase | Alcance | Esfuerzo | Impacto |
|:----:|---------|:--------:|---------|
| **K2-P0** | P-02, U-01, U-04, S-U-05/06, `IS_USER_SUPER_ADMIN` | Pequeño (~7 sites) | Elimina **SecurityError** Dedicated en rutas activas |
| **K2-P1** | Migrar 13× `user_service` qmark → `:cliente_id` | Medio | Silencia mayoría WARNING Tenant |
| **K2-P2** | Migrar 4× `superadmin_usuario_service` TD qmark | Medio | Silencia WARNING listado global post-J2 |
| **K2-P3** | `permiso_service` check/específico + PUT permisos-negocio | Pequeño | Cierra deuda RBAC write |
| **K2-P4** (opcional) | Extender `_has_tenant_filter` para `:pN` cuando columna es `cliente_id` | Alto | Fix estructural; requiere golden tests |

**Plantilla normativa (F13-D2):**

```python
await execute_query(
    text("... WHERE t.cliente_id = :cliente_id AND t.id = :id").bindparams(
        cliente_id=cliente_id,
        id=entity_id,
    ),
    client_id=cliente_id,
)
```

---

## 10. Apéndice — Registro completo `qmark_sql_text` (41)

| Archivo | Líneas | Funciones aproximadas |
|---------|--------|------------------------|
| `cliente_service.py` | 86, 107 | validaciones unicidad |
| `tenant_service.py` | 55, 76, 112 | config tenant, SSO, módulos |
| `permiso_service.py` | 264, 294, 486 | asignar permiso menú |
| `superadmin_usuario_service.py` | 95, 366, 406, 509, 558, 579, 598, 704, 733, 779, 815, 860, 942 | global, roles, drill-down |
| `superadmin_auditoria_service.py` | 189, 224, 785, 812, 1004, 1051, 1083, 1109 | auth/sync/stats |
| `user_service.py` | 463, 689, 744, 932, 1089, 1197, 1340, 1467, 1525, 1722, 1748, 1772, 1852 | CRUD + roles |

---

## 11. Relación con documentos F13

| Documento | Relación |
|-----------|----------|
| **F13-D1/D2** | Caso canónico TD-08; D2 no agotó `PermisoService` |
| **F12-E2B3L** | Smoke warnings Platform; fórmula usuarios global |
| **F13-J2/J3** | Fail-soft RI-39; **no** sustituye remediación TD-08 |
| **F13-K2** *(futuro)* | Implementación P0/P1 sugerida |

---

## 12. Restricciones de este entregable

- Sin modificación de código productivo.
- Sin commits.
- Sin fixes.
- Detenido tras generación de este documento.

**Estado:** F13-K1 completado — auditoría global TD-08 entregada.
