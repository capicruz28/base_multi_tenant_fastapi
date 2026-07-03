# F13-L2 — Auditoría del Bootstrap Platform Admin post-login

**Fecha:** 2026-06-25  
**Modo:** Solo auditoría de ejecución — **sin implementación, sin commits, sin cambios de logging**  
**Síntoma:** Tras login Platform Admin, todos los endpoints responden HTTP 200; el mensaje **RI-39** aparece **únicamente** durante la carga inicial de la consola y **no** al navegar entre módulos.  
**Referencias:** F13-I/J/K, F13-E2 (innovas), F13-J2/J3/J4, F12-E2B3V, `PLATFORM_DASHBOARD_FRONTEND_CONTRACT.md`, `logs/app.log.2` (sesión 2026-06-08 10:28:49–10:28:51, `platform.app.local`).

---

## 0. Veredicto ejecutivo

| Pregunta | Respuesta |
|----------|-----------|
| ¿El RI-39 post-login proviene del bootstrap y no de la navegación normal? | **Sí** — el único camino bootstrap que resuelve metadata **cross-tenant** es `GET /superadmin/usuarios/` **sin** `cliente_id` (KPI + tabla dashboard). |
| ¿Qué endpoint dispara la resolución metadata del Dedicated incompleto? | **`GET /api/v1/superadmin/usuarios/?page=1&limit=1`** (primero cronológicamente) o **`limit=100`** (misma oleada, mayor superficie de tenants). |
| ¿Está protegido por F13-J2? | **Sí para HTTP** — J2 captura el `DatabaseError` del preflight y degrada la fila. **No suprime** la llamada a `get_connection_metadata_async` ni el texto RI-39 en routing. |
| ¿Participa F13-J3 (`/clientes/{id}/estadisticas/`)? | **No en bootstrap** — ese endpoint no aparece en la traza de carga inicial del dashboard. |
| ¿Es esperado / evitable? | **Esperado y redundante en logs** — efecto colateral normativo del preflight J2 durante KPI bootstrap; **evitable** solo si el FE deja de invocar listado global enriquecido al cargar (p. ej. KPI solo con `total_usuarios` sin bucle de reachability, o BFF agregado). |

---

## 1. Inventario cronológico — endpoints automáticos post-login

Evidencia principal: `logs/app.log.2` líneas 5688–6100 (`POST /auth/login/` T₀ = **10:28:50.240** → último request dashboard **10:28:51.196**).

| # | T₀ relativo | Método | Endpoint | Query / notas | Fase |
|---|-------------|--------|----------|---------------|------|
| 1 | +0 ms | POST | `/api/v1/auth/login/` | credenciales superadmin | **A) Auth bootstrap** |
| 2 | +11 ms | GET | `/api/v1/auth/me/` | — | **A) Auth bootstrap** |
| 3 | +16 ms | GET | `/api/v1/auth/permissions/me` | paralelo con /me | **A) Auth bootstrap** |
| 4 | +147 ms | GET | `/api/v1/auth/menu` | menú elevado super_admin | **A) Auth bootstrap** |
| 5 | +302 ms | GET | `/api/v1/clientes/tenant/branding` | shell UI | **A) Auth bootstrap** |
| 6 | +586 ms | GET | `/api/v1/clientes/` | `skip=0&limit=1&solo_activos=true` | **B) Dashboard KPI** |
| 7 | +586 ms | GET | `/api/v1/superadmin/usuarios/` | `page=1&limit=1` (**sin** `cliente_id`) | **B+D) Dashboard KPI + listado global** |
| 8 | +586 ms | GET | `/api/v1/superadmin/auditoria/autenticacion/` | `page=1` | **C) Auditoría dashboard** |
| 9 | +586 ms | GET | `/api/v1/clientes/` | `limit=1000&solo_activos=false` | **B) Dashboard — selector tenants** |
| 10 | +586 ms | GET | `/api/v1/modulos-v2/` | `limit=1` | **B) Dashboard KPI módulos** |
| 11 | +586 ms | GET | `/api/v1/clientes/` | `limit=1&solo_activos=false` | **B) Dashboard KPI** |
| 12 | +785 ms | GET | `/api/v1/superadmin/auditoria/estadisticas/` | — | **C) Auditoría dashboard** |
| 13 | +785 ms | GET | `/api/v1/superadmin/auditoria/sincronizacion/` | `page=1` | **C) Auditoría dashboard** |
| 14 | +785 ms | GET | `/api/v1/superadmin/usuarios/` | `cliente_id=SYSTEM&limit=50` | **B) Widget usuarios platform** |
| 15 | +785 ms | GET | `/api/v1/superadmin/usuarios/` | `page=1&limit=100` (**sin** `cliente_id`) | **B+D) Tabla usuarios recientes dashboard** |

**Fin de bootstrap dashboard:** ~**956 ms** tras login (10:28:51.196).  
**Post-bootstrap (navegación):** a partir de 10:28:54 solo `GET /clientes/?limit=10` y `GET /modulos-v2/` — **sin** nuevas invocaciones a `GET /superadmin/usuarios/` global.

Contrato FE que explica la oleada: `PLATFORM_DASHBOARD_FRONTEND_CONTRACT.md` §2 (KPIs) y §W1–W12 — widgets W12 (`/superadmin/usuarios/?limit=1`) y tabla usuarios recientes (`limit=100`).

---

## 2. Matriz por endpoint — plano, OSR, metadata, RI-39

Leyenda: **CP** = Control Plane (`DatabaseConnection.ADMIN` / `kwargs_control_plane_read`). **TD** = tenant_data (`resolve_platform_tenant_data_*` / OSR). **RI-39 posible** = solo si existe tenant `tipo_instalacion=dedicated` sin Storage Endpoint válido en la página o en el target resuelto.

| Endpoint | Servicio | Método | Solo CP | Consulta TD | OSR | `get_connection_metadata_async` | `check_platform_tenant_reachability` | RI-39 posible |
|----------|----------|--------|---------|-------------|-----|--------------------------------|--------------------------------------|---------------|
| POST `/auth/login/` | `AuthService` | `login` / `authenticate_user` | ✅ (ADMIN, SYSTEM) | ❌ | ❌ | ❌ (middleware SYSTEM ya resuelto) | ❌ | ❌ |
| GET `/auth/me/` | `UserService` | `obtener_usuario_completo_por_id` | parcial | ✅ target **SYSTEM** | ✅ vía `resolve_platform_tenant_data_database_type(SYSTEM)` L360 | ✅ solo SYSTEM | ❌ | ❌ (SYSTEM = shared/single) |
| GET `/auth/permissions/me` | RBAC / `user_builder` | permisos catálogo | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| GET `/auth/menu` | `ModuloMenuService` | `obtener_menu_usuario` | ✅ (elevado super_admin) | ❌ | ❌ | ❌ | ❌ | ❌ |
| GET `/clientes/tenant/branding` | `ClienteService` | `obtener_branding_por_cliente_id` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| GET `/clientes/` | `ClienteService` | `listar_clientes` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| GET `/modulos-v2/` | `ModuloService` | `obtener_modulos` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| GET `/superadmin/auditoria/autenticacion/` | `SuperadminAuditoriaService` | `obtener_logs_autenticacion` | ✅ (`kwargs_platform_global_read`) | ❌ | ❌ | ❌ | ❌ | ❌ |
| GET `/superadmin/auditoria/estadisticas/` | `SuperadminAuditoriaService` | `obtener_estadisticas_auditoria` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| GET `/superadmin/auditoria/sincronizacion/` | `SuperadminAuditoriaService` | `obtener_logs_sincronizacion` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| GET `/superadmin/usuarios/?limit=1\|100` **sin** `cliente_id` | `SuperadminUsuarioService` | `get_usuarios_globales` | ✅ fase A (listado `dbo.usuario` ENGINE_SCOPED) | ✅ fase B enriquecimiento por fila | ✅ solo si REACHABLE post-preflight | ✅ **preflight J2 por tenant único en página** | ✅ **L434–438** | **✅ SÍ** |
| GET `/superadmin/usuarios/?cliente_id=SYSTEM&limit=50` | `SuperadminUsuarioService` | `get_usuarios_globales` | parcial | ✅ mono-tenant SYSTEM | ✅ L300 `resolve_platform_tenant_data_database_type` | ✅ SYSTEM only | ❌ (`use_fail_soft_enrichment=False`) | ❌ |
| GET `/clientes/{id}/estadisticas/` | `ClienteService` | `obtener_estadisticas` | parcial | condicional post-J3 | condicional | ✅ vía J3 preflight L653 | ✅ L653 | ✅ **pero no invocado en bootstrap** |

---

## 3. Call graph — `POST /auth/login` → primer RI-39

Escenario normativo: CP contiene tenant Dedicated incompleto (p. ej. **innovas** `7333EFB6-…`, F13-E2) y al menos un usuario en `dbo.usuario` global con `cliente_id` de ese tenant (o cualquier otro dedicated sin `cliente_conexion`).

```text
POST /api/v1/auth/login/  (T₀)
│  AuthService.login → ADMIN/SYSTEM only
│  Sin metadata cross-tenant
│
├─ GET /auth/me/ + GET /auth/permissions/me  (paralelo)
│     UserService.obtener_usuario_completo_por_id(SYSTEM)
│     └─ resolve_platform_tenant_data_database_type(SYSTEM) → metadata SYSTEM (single)
│     Sin reachability cross-tenant
│
├─ GET /auth/menu
│     ModuloMenuService → CP catálogo (super_admin elevado)
│
├─ GET /clientes/tenant/branding
│     ClienteService → CP
│
└─ [Oleada dashboard ~T₀+586ms — paralelo]
      │
      ├─ GET /clientes/?limit=1 …           → ClienteService.listar_clientes (CP)
      ├─ GET /modulos-v2/?limit=1           → ModuloService (CP)
      ├─ GET /superadmin/auditoria/*        → SuperadminAuditoriaService (CP global)
      │
      └─ ★ GET /superadmin/usuarios/?page=1&limit=1  [cliente_id=None]
            │  endpoints_usuarios.py:73  list_usuarios_global()
            │  └─ L94: SuperadminUsuarioService.get_usuarios_globales(cliente_id=None, limit=1)
            │
            └─ superadmin_usuario_service.py:238  get_usuarios_globales()
                  │
                  ├─ [FASE A] L362–410
                  │     tenant_query_kwargs = kwargs_platform_global_read()  L365
                  │     execute_query COUNT + SELECT page en dbo.usuario (ENGINE_SCOPED)
                  │     **Sin OSR, sin metadata por target tenant**
                  │
                  └─ [FASE B] L415–472  use_fail_soft_enrichment = True
                        for usuario_row in usuarios_raw:
                        │
                        ├─ _resolve_cliente_info_for_usuario()  L427–431
                        │     kwargs_control_plane_read() → CP (cliente embebido)
                        │
                        └─ ★ PRIMER RI-39 (primer tenant dedicated roto en la página)
                              L435–438: _get_reachability_for_global_enrichment()
                              L149: check_platform_tenant_reachability(usuario_cliente_id)
                              platform_tenant_reachability.py L88:
                                    metadata = await get_connection_metadata_async(cliente_id, TENANT_DATA)
                              routing.py L326 → _resolve_connection_metadata_uncached()
                              Dedicated sin cliente_conexion válida:
                              routing.py L552–556:
                                    _raise_dedicated_route_fail_closed(
                                        client_id,
                                        "Storage Endpoint ausente o credenciales inválidas en cliente_conexion.",
                                    )
                              → DatabaseError internal_code=DEDICATED_ROUTE_FAIL_CLOSED (detail RI-39)
                              platform_tenant_reachability.py L94–108: captura → NOT_CONFIGURED
                              superadmin_usuario_service.py L439–450: proyección degradada + continue
                              **HTTP 200** — sin OSR post-preflight para ese tenant
```

**Segunda oportunidad RI-39 en la misma sesión bootstrap:** `GET /superadmin/usuarios/?limit=100` (T₀+785 ms) — mismo grafo, hasta N tenants únicos en la página (cache reachability por request en L414).

**No participan en el primer RI-39:** login, /me, /menu, branding, clientes list, auditoría, `usuarios?cliente_id=SYSTEM` (STRICT mono-tenant, sin preflight J2).

---

## 4. Punto exacto de disparo — endpoint, servicio, método, línea

| Campo | Valor |
|-------|-------|
| **Endpoint HTTP** | `GET /api/v1/superadmin/usuarios/?page=1&limit=1` (primero cronológico en bootstrap con `cliente_id=None`) |
| **Presentation** | `app/modules/superadmin/presentation/endpoints_usuarios.py` — `list_usuarios_global()` L73–94 |
| **Servicio** | `SuperadminUsuarioService.get_usuarios_globales()` |
| **Archivo servicio** | `app/modules/superadmin/application/services/superadmin_usuario_service.py` |
| **Invocación preflight** | L435–438 → `_get_reachability_for_global_enrichment()` L144–150 |
| **Reachability** | `check_platform_tenant_reachability()` — `platform_tenant_reachability.py` **L88** |
| **Resolución metadata (RI-39)** | `get_connection_metadata_async()` — `routing.py` **L326** → `_raise_dedicated_route_fail_closed()` **L552–556** |
| **Tenant ejemplo (F13-E2)** | `7333EFB6-CBCA-4559-88C9-BFB85A187A0A` (innovas, `tipo_instalacion=dedicated`, 0 filas `cliente_conexion`) |

**Condición de activación:** la primera fila devuelta por el SELECT global (orden default `fecha_creacion DESC`) cuyo `usuario.cliente_id` apunte a un dedicated incompleto, **o** cualquier fila equivalente en la misma request al iterar el bucle.

**Nota sobre evidencia log local (2026-06-08):** en esa sesión `total_usuarios=1` (solo usuario SYSTEM) — **no se observó texto RI-39** en `app.log.2` porque el preflight nunca targeteó un dedicated roto. El grafo anterior es traza **estática** validada contra código post-F13-J2 y escenario multi-tenant documentado en F13-E2/J4.

---

## 5. Clasificación de la llamada

| Categoría | ¿Aplica? | Detalle |
|-----------|----------|---------|
| **A) Bootstrap obligatorio del login** | Parcial | `/auth/me`, `/auth/permissions/me`, `/auth/menu`, branding — **no** provocan RI-39 |
| **B) Dashboard** | **Sí (primario)** | Oleada widgets ~586 ms post-login; contrato FE W12 + tabla usuarios |
| **C) Auditoría** | No para RI-39 | Endpoints auditoría son CP-only |
| **D) Listado global** | **Sí (mecanismo)** | `get_usuarios_globales(cliente_id=None)` + preflight J2 |
| **E) Otra inicialización** | — | No aplica |

**Clasificación compuesta:** **B + D** — el frontend compone el dashboard invocando el listado global de usuarios para KPI (`limit=1`) y preview (`limit=100`); la resolución metadata cross-tenant es consecuencia del **enriquecimiento fail-soft J2**, no del login en sí.

---

## 6. Protección F13-J2 / F13-J3 — ¿ocurre antes o después del fail-soft?

| Remediación | ¿Invocada en bootstrap? | Relación con RI-39 observado |
|-------------|-------------------------|------------------------------|
| **F13-J2** (`SuperadminUsuarioService` global) | **Sí** — único consumidor productivo de `check_platform_tenant_reachability` en bootstrap | RI-39 **es el interior del preflight J2**, no un bypass posterior. J2 convierte el fail en `ReachabilityResult NOT_CONFIGURED` y **no** llama OSR/enriquecimiento DP (L439–450 `continue`). HTTP permanece 200. |
| **F13-J3** (`ClienteService.obtener_estadisticas`) | **No** en traza bootstrap | Podría emitir RI-39 en drill-down explícito `GET /clientes/{id}/estadisticas/`; **no forma parte** de la carga inicial observada. |

**Conclusión protección:** la llamada **está dentro** del fail-soft J2; no ocurre "antes" de J2 ni como fallo no capturado. Lo que persiste es el **efecto colateral en routing/logging** al evaluar metadata — comportamiento documentado en F13-J4 §0.

---

## 7. Por qué solo al login y no al navegar módulos

| Momento | Patrón FE | ¿`GET /superadmin/usuarios/` global? | ¿Preflight metadata cross-tenant? |
|---------|-----------|--------------------------------------|-----------------------------------|
| **Carga dashboard (bootstrap)** | Paraleliza KPIs + widgets (`PLATFORM_DASHBOARD_FRONTEND_CONTRACT.md` §796–803) | **Sí** — `limit=1`, `limit=100` | **Sí** |
| **Navegación módulos (post-carga)** | Rutas de módulo / listados filtrados | **No** (evidencia log: solo `/clientes/`, `/modulos-v2/` tras 10:28:51) | **No** en la misma forma |

El RI-39 **no reaparece** porque la navegación entre módulos **no re-ejecuta** el widget de listado global enriquecido; los endpoints de módulo operativos consultan CP o scopes mono-tenant sin el bucle J2 cross-tenant del dashboard.

---

## 8. Conclusión — naturaleza del RI-39 observado

| Clasificación | Veredicto |
|---------------|-----------|
| **Esperado** | **Sí** — dedicated incompleto + preflight J2 debe evaluar metadata (RI-39 fail-closed normativo en `routing.py`). |
| **Redundante (logs)** | **Sí** — el mensaje RI-39 en routing es el mismo evento que J2 ya clasifica; HTTP y respuesta API están degradados correctamente. |
| **Evitable** | **Parcialmente** — evitable a nivel producto si bootstrap no requiere enriquecimiento cross-tenant (KPI solo COUNT sin reachability, BFF agregado, o diferir listado hasta módulo Usuarios). No es bug de bypass fail-soft. |
| **Síntoma de llamada innecesaria** | **Parcialmente** — el KPI `total_usuarios` podría obtenerse del COUNT de fase A **sin** entrar al bucle B; hoy el servicio **siempre** enriquece filas aunque `limit=1` solo necesite el total. Eso convierte un KPI en **sonda de reachability** para cada tenant visible. |

---

## 9. Referencias de código

| Artefacto | Ubicación |
|-----------|-----------|
| Listado global + J2 | `app/modules/superadmin/application/services/superadmin_usuario_service.py` L238–472, L144–150 |
| Preflight reachability | `app/core/tenant/platform_tenant_reachability.py` L72–108 |
| RI-39 fail-closed | `app/core/tenant/routing.py` L326–369, L552–556 |
| OSR wrapper | `app/core/tenant/platform_tenant_data_store.py` L20–55 |
| Intent global CP | `app/modules/superadmin/application/platform_global_query_intent.py` |
| J3 estadísticas | `app/modules/tenant/application/services/cliente_service.py` L631–653 |
| Contrato dashboard FE | `app/docs/auditoria/PLATFORM_DASHBOARD_FRONTEND_CONTRACT.md` |
| Traza runtime previa | `app/docs/arquitectura/F13_J4_FAIL_SOFT_RUNTIME_TRACE.md` |

---

**Fin F13-L2 — sin modificaciones de código, sin commits.**
