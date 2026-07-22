# §1 — Inventario de capas del menú dinámico

**Pregunta:** ¿Desde qué endpoint se construye el menú? Router / Endpoint / Service / Queries / Repositories.

---

## 1. Endpoint canónico (recomendado para FE)

| Capa | Valor |
|------|--------|
| **Mount** | `app/api/v1/api.py` → `prefix="/auth"` |
| **Router** | `app/modules/auth/presentation/endpoints.py` |
| **Endpoint** | `GET /api/v1/auth/menu` |
| **Handler** | `get_menu` |
| **Deps** | `require_erp_session`, `require_full_session_payload` |
| **Resolver** | `MenuResolverService.get_menu_for_user` — `app/core/authorization/menu_resolver.py` |
| **Factory** | `get_menu_resolver()` |
| **Service de estructura** | `ModuloMenuService.obtener_menu_usuario` — `app/modules/modulos/application/services/modulo_menu_service.py` |
| **Impersonación** | `ModuloMenuService.obtener_menu_impersonacion_tenant` (RMP de `ADMIN_TENANT` sin `usuario_rol` del operador) |
| **Transform** | `transformar_sp_menu_usuario` — `app/modules/modulos/application/helpers/menu_transformer.py` |
| **Normalización ruta** | `normalize_menu_ruta_for_fe` — `app/core/menu/menu_route_normalizer.py` |
| **Enriquecimiento** | `resolve_required_permissions_for_menu_tree` — `app/core/authorization/menu_permission_resolver.py` |
| **Store catálogo Q1** | `resolve_menu_catalog_query1_target` — `app/core/authorization/menu_catalog_store.py` |
| **Tenant menú** | `resolve_menu_cliente_id_for_session` — `app/core/auth/impersonation_rbac.py` |

**Response model:** `MenuUsuarioResponse` (`modulos[]` → `secciones[]` → `menus[]` + flags UI) — `app/modules/modulos/presentation/schemas.py`.

---

## 2. Endpoint alterno / legacy (mismo service)

| Endpoint | Archivo | Notas |
|----------|---------|--------|
| `GET /api/v1/modulos-menus/me/` | `app/modules/modulos/presentation/endpoints_menus.py` | Misma `ModuloMenuService`; exige permiso `modulos.menu.leer` |
| `GET /api/v1/modulos-menus/usuario/{id}/` | mismo | Consulta admin por usuario |
| CRUD `/modulos-menus/...` | mismo | Gestión de catálogo, no sidebar FE |

**Normativa de auditoría RBAC:** el FE debe preferir `/auth/menu` sobre `/modulos-menus/me/` (evita dependencia de `modulos.menu.leer` en roles BASE).

---

## 3. Endpoint legacy distinto (no es el menú ERP SaaS)

| Endpoint | Archivo | Notas |
|----------|---------|--------|
| `GET /api/v1/menus/...` | `app/modules/menus/presentation/endpoints.py` | Modelo legacy `area_menu` / `menu` vía `MenuService` + `queries/menus/` |

**No** es la fuente del sidebar ERP moderno (`modulo` / `modulo_menu`).

---

## 4. Queries y “Repositories”

| Concepto | Realidad AS-IS |
|----------|----------------|
| **Queries dedicadas tipo ERP** | **No** hay `infrastructure/database/queries/...` para el menú dinámico canónico |
| **SQL** | Embebido en `ModuloMenuService.obtener_menu_usuario`: SQLAlchemy Core (Q1) + raw SQL (Q2 `rol_menu_permiso`) vía `execute_query` |
| **Repository pattern** | **No aplica** al menú dinámico (alineado con estándares ERP V4: sin Repository en módulos ERP; aquí el service concentra el SQL) |
| **Legacy** | `app/infrastructure/database/queries/menus/menu_queries.py` — solo área legacy |

### Query 1 (catálogo + suscripción)

- Tablas: `modulo_menu` ⋈ `modulo` ⋈ `cliente_modulo` (+ outer `modulo_seccion`)
- Conexión: resuelta por `resolve_menu_catalog_query1_target(cliente_id)` (ADMIN shared / DEFAULT dedicated según modo instalación)

### Query 2 (visibilidad UI)

- Tablas: `rol_menu_permiso` ⋈ `usuario_rol` (o `rol_id` directo en impersonación)
- Conexión: `DatabaseConnection.DEFAULT` + `client_id=cliente_id`

---

## 5. Permisos efectivos (paralelo al menú)

| Endpoint | Rol |
|----------|-----|
| `GET /api/v1/auth/permissions/me` | Lista códigos efectivos (`PermissionResolver`) — gate de `PermissionGuard` / `usePermission()` en FE |

El `MenuResolver` **sí** obtiene `effective_permission_codes` y los pasa a `obtener_menu_usuario`, pero en el cuerpo del service esos códigos **no se usan para ocultar** ítems. La ocultación es **solo** Q1 ∩ Q2 (o elevación super_admin).

---

## 6. Diagrama de capas

```text
Presentation          auth/endpoints.py          GET /auth/menu
        │
Core resolver         menu_resolver.py           MenuResolverService
        │             ├─ permission_resolver     (códigos; no filtran árbol)
        │             └─ modulo_menu_service     (árbol + RMP)
        │
Helpers               menu_transformer.py
                      menu_route_normalizer.py
                      menu_permission_resolver.py  (required_permission anotado)
        │
Persistencia          execute_query + SQL en service
                      (sin repository de menú)
```
