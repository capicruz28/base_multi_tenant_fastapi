# F13-K2-P2A — Auditoría quirúrgica del warning TD-08 residual

**Fecha:** 2026-06-25  
**Modo:** Solo auditoría — **sin implementación, sin commits, sin cambios de código**  
**Síntoma observado:**

```text
[TENANT_FILTER] No se pudo aplicar filtro automático a TextClause:
This text() construct doesn't define a bound parameter named 'cliente_id'.
```

**Request de evidencia:**

```http
GET /api/v1/superadmin/usuarios/?page=1&limit=50&cliente_id=00000000-0000-0000-0000-000000000001
```

**Prerequisitos:** F13-K1, F13-K2-P0, F13-K2-P1, F13-M2 (refactor COUNT interno).

---

## 0. Veredicto ejecutivo

| Pregunta | Respuesta |
|----------|-----------|
| ¿Qué consulta produce el warning? | **S-U-02** — `COUNT` y/o `SELECT` paginado en `count_usuarios_globales` / `get_usuarios_globales` vía `qmark_sql_text()` |
| ¿Es enriquecimiento (roles/level)? | **No** — roles (`_obtener_roles_usuario`) y `is_super_admin` fueron remediados en P0/P1 |
| ¿Por qué sobrevivió a K2-P1? | **Exclusión explícita S-U-02** en P1 + rama **`cliente_id != None`** usa `ROW_SCOPED` (no `ENGINE_SCOPED`) |
| ¿Cuántas consultas PENDIENTE en este flujo? | **2** por request (COUNT + SELECT principal); **0** en enriquecimiento post-P1 |
| Prioridad | **MEDIUM** (WARNING Shared; filtro semántico presente vía `:p0`) |

---

## 1. Origen exacto del warning

### 1.1 Emisor del log (infraestructura)

| Campo | Valor |
|-------|-------|
| **Archivo** | `app/infrastructure/database/query_helpers.py` |
| **Función** | `apply_tenant_filter_to_text_clause` |
| **Líneas** | **528–531** (`except Exception` tras fallo de `text(...).bindparams(...)`) |

```528:531:app/infrastructure/database/query_helpers.py
        logger.warning(
            f"[TENANT_FILTER] No se pudo aplicar filtro automático a TextClause: {e}. "
            f"Query: {query_str[:200]}..."
        )
```

**Mecanismo:** `_has_tenant_filter()` no reconoce `u.cliente_id = :p0` (solo `:cliente_id` / `:client_id` nombrados). El inyector intenta añadir `AND cliente_id = :cliente_id` y reconstruir `bindparams`; SQLAlchemy lanza `This text() construct doesn't define a bound parameter named 'cliente_id'` → WARNING (Shared).

### 1.2 Call site productivo (aplicación)

| Campo | Valor |
|-------|-------|
| **Archivo** | `app/modules/superadmin/application/services/superadmin_usuario_service.py` |
| **Consulta A — COUNT** | `count_usuarios_globales` **L369–371** |
| **Consulta B — SELECT** | `get_usuarios_globales` **L476–478** |
| **Helper SQL** | `qmark_sql_text()` → `query_helpers.py` **L659–677** (`?` → `:p0`, `:p1`, …) |
| **Gateway** | `queries_async.execute_query` → `_prepare_text_clause_for_gateway` **L354–360** |

**Demostración — COUNT (consulta responsable tipo A):**

```361:371:app/modules/superadmin/application/services/superadmin_usuario_service.py
        count_query = f"""
        SELECT COUNT(*) as total
        FROM dbo.usuario u
        WHERE {where_clause}
        """
        tenant_query_kwargs = await SuperadminUsuarioService._resolve_usuarios_globales_query_kwargs(
            cliente_id
        )
        count_result = await execute_query(
            qmark_sql_text(count_query, tuple(params)),
            **tenant_query_kwargs,
        )
```

**Demostración — SELECT paginado (consulta responsable tipo B):**

```442:478:app/modules/superadmin/application/services/superadmin_usuario_service.py
        data_query = f"""
        SELECT 
            u.usuario_id,
            ...
        FROM dbo.usuario u
        WHERE {where_clause}
        ORDER BY {order_field} {order_dir}
        OFFSET ? ROWS
        FETCH NEXT ? ROWS ONLY
        """
        params.extend([offset, limit])
        tenant_query_kwargs = await SuperadminUsuarioService._resolve_usuarios_globales_query_kwargs(
            cliente_id
        )
        usuarios_raw = await execute_query(
            qmark_sql_text(data_query, tuple(params)),
            **tenant_query_kwargs,
        )
```

### 1.3 SQL real (request sin filtros `search` / `es_activo`)

**WHERE construido** (`_build_usuarios_globales_where` L253–255) para `cliente_id=SYSTEM` y `database_type=single`:

```sql
u.es_eliminado = 0 AND u.cliente_id = ?
```

**COUNT — SQL fuente (antes de `qmark_sql_text`):**

```sql
        SELECT COUNT(*) as total
        FROM dbo.usuario u
        WHERE u.es_eliminado = 0 AND u.cliente_id = ?
```

**Tras `qmark_sql_text` (parámetros nombrados):**

```sql
        SELECT COUNT(*) as total
        FROM dbo.usuario u
        WHERE u.es_eliminado = 0 AND u.cliente_id = :p0
```

| Elemento | Presente |
|----------|----------|
| `?` | Sí (fuente) → `:p0` |
| `:p0` | Sí (post-qmark) |
| `:p1`, `:p2` | No en COUNT |
| `:cliente_id` | **No** (causa TD-08) |
| `bindparams()` | Sí — `qmark_sql_text` → `text(...).bindparams(p0=UUID)` |
| `client_id=` en `execute_query` | Sí — vía `resolve_platform_tenant_data_execute_kwargs(SYSTEM)` → `client_id=SYSTEM`, `identity_scope=ROW_SCOPED` |

**SELECT — SQL fuente (mismo WHERE + paginación):**

```sql
        SELECT 
            u.usuario_id,
            u.cliente_id,
            ...
        FROM dbo.usuario u
        WHERE u.es_eliminado = 0 AND u.cliente_id = ?
        ORDER BY u.fecha_creacion DESC
        OFFSET ? ROWS
        FETCH NEXT ? ROWS ONLY
```

**Tras `qmark_sql_text` (params = `[SYSTEM, offset, limit]`):**

```sql
        ...
        WHERE u.es_eliminado = 0 AND u.cliente_id = :p0
        ORDER BY u.fecha_creacion DESC
        OFFSET :p1 ROWS
        FETCH NEXT :p2 ROWS ONLY
```

---

## 2. Call graph completo

**Request:** `GET /api/v1/superadmin/usuarios/?page=1&limit=50&cliente_id=00000000-0000-0000-0000-000000000001`

```text
HTTP GET /api/v1/superadmin/usuarios/
│
├─ app/modules/superadmin/presentation/endpoints_usuarios.py
│     list_usuarios_global()                          L73–103
│     └─ SuperadminUsuarioService.get_usuarios_globales(
│           cliente_id=SYSTEM, page=1, limit=50)      L94
│
└─ app/modules/superadmin/application/services/superadmin_usuario_service.py
      get_usuarios_globales()                         L377–548
      │
      ├─ [PRE-1] _resolve_usuarios_globales_cliente_context(SYSTEM)   L417–418
      │     └─ ClienteService.obtener_cliente_por_id(SYSTEM)          L314
      │           execute_query(text(...).bindparams(cliente_id=), ADMIN, client_id=None)
      │           → CP; sin tenant filter (effective_client_id=None)   ✅ OK
      │
      ├─ resolve_platform_tenant_data_database_type(SYSTEM)           L328
      │     └─ get_connection_metadata_async (OSR/routing)            ✅ OK (metadata)
      │
      ├─ [TOTAL] count_usuarios_globales(...)                         L421–427
      │     ├─ _resolve_usuarios_globales_cliente_context (2ª vez)    L347–348
      │     ├─ _build_usuarios_globales_where(...)                    L351–358
      │     ├─ _resolve_usuarios_globales_query_kwargs(SYSTEM)         L366–367
      │     │     └─ resolve_platform_tenant_data_execute_kwargs
      │     │           → ROW_SCOPED + client_id=SYSTEM                 ⚠️ activa tenant filter
      │     └─ execute_query(qmark_sql_text(COUNT), **kwargs)         L369–371
      │           queries_async.execute_query TextClause branch         L353–360
      │           _prepare_text_clause_for_gateway                      L177–206
      │           apply_tenant_filter_to_text_clause                    L407–531
      │           ★ WARNING TD-08 si bindparams falla                   L528–531
      │
      ├─ [LIST] _build_usuarios_globales_where (2ª vez)                 L431–438
      ├─ _resolve_usuarios_globales_query_kwargs(SYSTEM)              L473–474
      └─ execute_query(qmark_sql_text(SELECT…OFFSET), **kwargs)       L476–478
            ★ mismo pipeline TD-08 que COUNT                            L528–531
      │
      └─ [ENRICH] bucle por fila (use_fail_soft_enrichment=False)       L484–537
            │
            ├─ _resolve_cliente_info_for_usuario
            │     filtered_cliente_info=cliente_info → sin CP fetch      ✅ OK
            │
            ├─ (sin reachability — cliente_id≠None)                      ✅ OK
            │
            ├─ _obtener_roles_usuario                                  L522–525
            │     text(...).bindparams(usuario_id=, cliente_id=)        L576–581
            │     ur.cliente_id = :cliente_id → _has_tenant_filter PASS ✅ OK (P1)
            │
            └─ UsuarioService.get_user_level_info                        L528–530
                  ├─ get_user_access_level                             user_service L178
                  │     execute_auth_query(?, ?) — sin tenant filter    ✅ OK
                  └─ is_super_admin                                    user_service L224–229
                        text(IS_USER_SUPER_ADMIN).bindparams(...)       ✅ OK (P0)
```

### 2.1 Tabla de métodos que invocan `execute_query`

| Orden | Método | `text()` | `qmark_sql_text()` | SQL dinámico | TD-08 |
|------:|--------|:--------:|:------------------:|:------------:|:-----:|
| 1 | `ClienteService.obtener_cliente_por_id` | ✅ `:cliente_id` | — | — | OK |
| 2 | `count_usuarios_globales` | — | ✅ COUNT | f-string WHERE | **PENDIENTE** |
| 3 | `get_usuarios_globales` (SELECT) | — | ✅ DATA | f-string WHERE + ORDER | **PENDIENTE** |
| 4 | `_obtener_roles_usuario` | ✅ nombrado | — | — | OK |
| 5 | `UsuarioService.is_super_admin` | ✅ nombrado | — | — | OK |
| — | `get_user_access_level` | — | — | `execute_auth_query` (sin filter) | OK |

---

## 3. Clasificación de la consulta responsable

| Pregunta | Respuesta |
|----------|-----------|
| ¿Consulta principal? | **Sí** — COUNT (fase total) y SELECT (fase listado) |
| ¿Enriquecimiento? | **No** |
| ¿Roles? | **No** — remediado P1 (`S-U-03`) |
| ¿access_level? | **No** — `execute_auth_query`; pipeline distinto |
| ¿is_super_admin? | **No** — remediado P0 (`IS_USER_SUPER_ADMIN` + `:cliente_id`) |
| ¿fetch usuario auxiliar? | **No** en este flujo (`cliente_info` reutilizado) |
| ¿lookup empresa? | **No** |
| ¿auditoría? | **No** |

**Primera emisión cronológica en el request:** `count_usuarios_globales` → **L369–371** (COUNT).  
**Segunda emisión:** `get_usuarios_globales` → **L476–478** (SELECT).

Si el operador reporta **un solo** warning visible, corresponde a **una de las dos** consultas S-U-02 idénticas en patrón; el request completo puede emitir **hasta 2** warnings del mismo texto.

---

## 4. Por qué sobrevivió a F13-K2-P1

| Causa | Evidencia |
|-------|-----------|
| **Exclusión explícita en P1** | `F13_K2_P1_MEDIUM_IMPLEMENTATION.md` L31: «`get_usuarios_globales` COUNT/DATA (S-U-02)» excluido |
| **Razonamiento P1 incompleto para esta rama** | Exclusión documentada para listado **global sin `cliente_id`** (`kwargs_platform_global_read` → `ENGINE_SCOPED`). El request observado lleva **`cliente_id=SYSTEM`** |
| **Rama `cliente_id != None`** | `_resolve_usuarios_globales_query_kwargs` → `resolve_platform_tenant_data_execute_kwargs` → `IdentityScope.ROW_SCOPED` (`operation_store_resolver.py` L70–77) |
| **Patrón qmark residual** | `_build_usuarios_globales_where` L254: `u.cliente_id = ?` → `qmark_sql_text` → `:p0`; invisible a `_has_tenant_filter()` |
| **No es llamada indirecta oculta** | Es el path documentado K1 **S-U-02**; F13-M2 extrajo COUNT pero **no migró** el patrón SQL |
| **K1 ya lo catalogó** | `F13_K1_GLOBAL_TD08_AUDIT.md` S-U-02 — MEDIUM; remediación planificada **K2-P2** (4× qmark Superadmin TD) |

**Conclusión:** No es regresión de P1 ni bypass de J2/M2. Es **deuda MEDIUM deliberadamente diferida** que se manifiesta en el **drill-down mono-tenant** (`cliente_id=SYSTEM`), no en el listado global sin filtro.

---

## 5. Inventario completo del flujo — clasificación TD-08

**Alcance:** `GET /superadmin/usuarios/` con `cliente_id=SYSTEM`, `page=1`, `limit=50`, sin filtros opcionales.

| # | Fase | Consulta / operación | Archivo:Línea | TD-08 | Prioridad |
|---|------|----------------------|---------------|:-----:|:---------:|
| 1 | Pre | `SELECT … FROM cliente WHERE cliente_id = :cliente_id` | `cliente_service.py:217` | **OK** | — |
| 2 | Pre | `get_connection_metadata_async(SYSTEM)` | `operation_store_resolver.py:122` | **OK** | — |
| 3 | Pre | `resolve_platform_tenant_data_execute_kwargs` | `platform_tenant_data_store.py:50` | **OK** | — |
| 4 | Total | **COUNT `dbo.usuario`** (`qmark`, `u.cliente_id = :p0`) | `superadmin_usuario_service.py:369` | **PENDIENTE** | **MEDIUM** |
| 5 | List | **SELECT paginado `dbo.usuario`** (`qmark`, `:p0`…`:p2`) | `superadmin_usuario_service.py:476` | **PENDIENTE** | **MEDIUM** |
| 6 | Enrich ×N | `_resolve_cliente_info` (cache `cliente_info`) | `superadmin_usuario_service.py:496` | **OK** | — |
| 7 | Enrich ×N | reachability J2 | — | **OK** (no invocado) | — |
| 8 | Enrich ×N | `_obtener_roles_usuario` (`:cliente_id` nombrado) | `superadmin_usuario_service.py:576` | **OK** | — |
| 9 | Enrich ×N | `get_user_access_level` (`execute_auth_query`) | `user_service.py:178` | **OK** | — |
| 10 | Enrich ×N | `is_super_admin` (`IS_USER_SUPER_ADMIN`) | `user_service.py:224` | **OK** | — |

**N = filas devueltas** (≤ `limit=50`). Enriquecimiento: **0 warnings** post-P0/P1.

### 5.1 Variantes del mismo endpoint (referencia)

| Query params | COUNT/SELECT kwargs | S-U-02 TD-08 |
|--------------|---------------------|:------------:|
| `cliente_id=None` (global) | `kwargs_platform_global_read()` → ENGINE_SCOPED | **OK** |
| `cliente_id=SYSTEM` (observado) | `resolve_platform_tenant_data_execute_kwargs` → ROW_SCOPED | **PENDIENTE ×2** |
| `cliente_id=<dedicated>` | ENGINE_SCOPED si `multi`; WHERE sin `cliente_id` en SQL | **PENDIENTE** en COUNT/SELECT† |

† Dedicated: mismo patrón qmark; riesgo escala a CRITICAL solo si filtro semántico ausente — aquí el listado es engine-scoped por tenant.

---

## 6. ¿Es el único warning restante?

### 6.1 En este request específico

| Clasificación | Cantidad |
|---------------|----------:|
| Consultas **PENDIENTE TD-08** | **2** (COUNT + SELECT) |
| Consultas **OK** | **8 + 3×N** (N ≤ 50) |

**No es una sola consulta pendiente** — son **dos** call sites del mismo hallazgo **S-U-02** (migración K2-P2 pendiente).

### 6.2 En el bootstrap Platform completo (contexto)

Otros endpoints del dashboard pueden emitir TD-08 en flujos distintos (p. ej. listado global sin `cliente_id` con enriquecimiento ya silenciado en roles). **Fuera del alcance exacto de este request**, la deuda K1 global (`qmark_sql_text` residual en otros módulos) **no está cerrada** — ver `F13_K1_GLOBAL_TD08_AUDIT.md`.

---

## 7. Clasificación y remediación futura (solo referencia — sin implementar)

| ID | Consulta | Estado | Prioridad | Remediación mínima (K2-P2) |
|----|----------|--------|:---------:|--------------------------|
| **S-U-02a** | COUNT `count_usuarios_globales` | PENDIENTE | **MEDIUM** | `text(...).bindparams(cliente_id=)` + `u.cliente_id = :cliente_id` cuando `database_type=single` |
| **S-U-02b** | SELECT `get_usuarios_globales` | PENDIENTE | **MEDIUM** | Idem + `offset`/`limit` nombrados |
| S-U-03 | `_obtener_roles_usuario` | **OK** | — | Hecho en P1 |
| P0 `is_super_admin` | `IS_USER_SUPER_ADMIN` | **OK** | — | Hecho en P0 |

**Patrón normativo (F13-D2):**

```python
await execute_query(
    text("""
        SELECT COUNT(*) AS total
        FROM dbo.usuario u
        WHERE u.es_eliminado = 0 AND u.cliente_id = :cliente_id
    """).bindparams(cliente_id=cliente_id),
    **await resolve_platform_tenant_data_execute_kwargs(cliente_id),
)
```

Para listado **global sin `cliente_id`**, mantener `kwargs_platform_global_read()` (ENGINE_SCOPED) sin migración obligatoria.

---

## 8. Referencias

| Documento | Relación |
|-----------|----------|
| `F13_K1_GLOBAL_TD08_AUDIT.md` | S-U-02 catalogado MEDIUM |
| `F13_K2_P1_MEDIUM_IMPLEMENTATION.md` | Exclusión S-U-02; P1 roles OK |
| `F13_K2_P0_CRITICAL_IMPLEMENTATION.md` | `is_super_admin` OK |
| `F13_M2_INTERNAL_REFACTOR.md` | COUNT extraído; patrón qmark sin cambio |
| `F13_L2_PLATFORM_BOOTSTRAP_RUNTIME_AUDIT.md` | Request `cliente_id=SYSTEM` en bootstrap |

---

**Fin F13-K2-P2A — sin modificaciones de código, sin commits.**
