# Menu Resolver — Flujo y arquitectura

**Objetivo:** Menú centralizado en backend filtrado por tenant, módulos contratados y permisos efectivos.

---

## 1. Flujo: Tenant → Modules → Permissions → Menu

```
Tenant (cliente_id)
    │
    ▼
Modules: cliente_modulo (módulos activos del tenant; esta_activo, fecha_vencimiento)
    │
    ▼
Permissions: Permission Resolver (permisos efectivos del usuario; cache reutilizado)
    │
    ▼
Menu: ModuloMenuService (modulo_menu + rol_menu_permiso; estructura jerárquica)
```

1. **Tenant:** El `cliente_id` del token/contexto identifica el tenant. Todo el menú es scope a ese tenant.
2. **Modules:** Solo se incluyen módulos que el tenant tiene contratados y vigentes (`cliente_modulo`: `esta_activo = 1`, `fecha_vencimiento` vigente o NULL). La query de menú ya hace JOIN con `cliente_modulo`.
3. **Permissions:** Los permisos efectivos del usuario se obtienen del **Permission Resolver** (única fuente de verdad; filtrados por módulos contratados y por rol). Se reutiliza la cache del resolver.
4. **Menu:** El **ModuloMenuService** construye la estructura (módulos → secciones → menús → submenús) y aplica permisos por ítem desde `rol_menu_permiso`. Recibe opcionalmente la lista de permisos efectivos para futura filtración por `permiso_requerido_id` en ítems.

---

## 2. Tablas de menú existentes

| Tabla            | Uso |
|------------------|-----|
| **modulo**       | Catálogo de módulos ERP (global). |
| **modulo_seccion** | Secciones dentro de un módulo. |
| **modulo_menu**  | Ítems de menú (pantallas, rutas). Jerarquía vía `menu_padre_id`. |
| **cliente_modulo** | Módulos contratados por tenant (billing). |
| **rol_menu_permiso** | Permisos por ítem de menú (puede_ver, puede_crear, etc.) por rol. |

No existe hoy `modulo_menu.permiso_requerido_id`. Cuando se añada, el Menu Resolver podrá filtrar ítems por “usuario tiene el permiso X” además de `rol_menu_permiso`.

---

## 3. Endpoint GET /auth/menu

- **Ruta:** `GET /api/v1/auth/menu`
- **Autenticación:** Bearer (mismo que el resto de /auth).
- **Respuesta:** Misma estructura que `GET /api/v1/modulos-menus/me/` (`MenuUsuarioResponse`: `modulos` → `secciones` → `menus` → `permisos`, `submenus`).
- **Comportamiento:** Usa el **Menu Resolver**, que a su vez usa el Permission Resolver (cache) y el ModuloMenuService. No reemplaza ni modifica `GET /modulos-menus/me/`.

---

## 4. Menu Resolver (MenuResolverService)

- **Ubicación:** `app/core/authorization/menu_resolver.py`
- **Método:** `get_menu_for_user(usuario_id, cliente_id, database_type, is_super_admin, as_tenant_admin)`
- **Pasos:**
  1. Obtener permisos efectivos del Permission Resolver (`get_effective_permissions`).
  2. Llamar `ModuloMenuService.obtener_menu_usuario(..., effective_permission_codes=permission_codes)`.
  3. Devolver `MenuUsuarioResponse`.

Cache: se reutiliza la del Permission Resolver; no se añade una cache adicional del menú en esta fase.

---

## 5. Compatibilidad

- **GET /modulos-menus/me/:** Sin cambios; sigue disponible y con la misma lógica.
- **Autenticación:** GET /auth/menu usa `get_current_active_user` como el resto de /auth.
- **Frontend:** Puede migrar a GET /auth/menu para obtener el menú desde el Menu Resolver sin cambiar la estructura de la respuesta.
