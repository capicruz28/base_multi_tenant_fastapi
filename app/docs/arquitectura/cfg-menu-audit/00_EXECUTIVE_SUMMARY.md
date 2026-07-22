# Auditoría del menú dinámico ERP — Resumen ejecutivo (CFG)

**Rol:** Arquitecto Revisor Senior — Backend ERP  
**Fecha:** 2026-07-18  
**Alcance:** Solo lectura. Sin implementación, sin seeds, sin migraciones, sin registro de CFG en menú.  
**Contexto:** Frontend CFG certificado bajo `/api/v1/cfg/*`. Esta auditoría explica cómo el Backend decide qué módulos/menús devuelve al FE.

---

## 1. Veredicto

| Pregunta | Hallazgo |
|----------|----------|
| ¿De dónde sale el menú FE? | Canónico: **`GET /api/v1/auth/menu`** |
| ¿Modelo de visibilidad? | **`cliente_modulo` ∩ `rol_menu_permiso.puede_ver`** (Modelo Owner). Elevación solo `is_super_admin`. |
| ¿Separación `/app` `/admin` `/super-admin`? | **Sí, data-driven** (rutas + códigos `modulo`/`seccion`/`menu`). El Backend **no** emite un campo `contexto` / plano sidebar. |
| ¿CFG ya aparece en menú? | **No.** Existen permisos API (`S068`); **no** hay `modulo`/`modulo_menu`/`rol_menu_permiso` de catálogo para CFG. |
| ¿`cfg.ver`? | **No existe** en Backend ni en seeds. |

---

## 2. Flujo canónico (AS-IS)

```text
GET /api/v1/auth/menu
  → require_erp_session + require_full_session_payload
  → resolve_menu_cliente_id_for_session / resolve_empresa_id_for_rbac
  → MenuResolverService.get_menu_for_user
       → PermissionResolver.get_effective_permissions  (códigos; hoy no ocultan ítems)
       → ModuloMenuService.obtener_menu_usuario
            Q1: modulo ⋈ modulo_menu ⋈ cliente_modulo (+ seccion)
            Q2: rol_menu_permiso ⋈ usuario_rol  [omitido si is_super_admin]
       → transformar_sp_menu_usuario + normalize_menu_ruta_for_fe
  → resolve_required_permissions_for_menu_tree (anota required_permission; no filtra)
  → MenuUsuarioResponse
```

---

## 3. Índice del paquete

| Doc | Contenido (preguntas) |
|-----|------------------------|
| [`01_ENDPOINT_AND_LAYERS.md`](01_ENDPOINT_AND_LAYERS.md) | §1 Capas: router, endpoint, service, queries |
| [`02_TABLES_FILTERS_AND_PLANES.md`](02_TABLES_FILTERS_AND_PLANES.md) | §2–§5 Tablas, filtros, planos `/app`/`admin`/`super-admin`, Tenant Admin |
| [`03_FE_CHAIN_AND_REQUIRED_RECORDS.md`](03_FE_CHAIN_AND_REQUIRED_RECORDS.md) | §6–§7 Cadena FE↔BE; registros necesarios para CFG |
| [`04_MODULE_COMPARISON_AND_VISIBILITY.md`](04_MODULE_COMPARISON_AND_VISIBILITY.md) | §8–§10 ORG/IAM/INV vs CFG; permisos navegación; visibilidad |

---

## 4. Gap CFG (estado factual, sin remediar)

| Capa | Estado CFG |
|------|------------|
| API `/cfg/secuencias` | Certificada |
| `permiso` + `rol_permiso` (`cfg.secuencias.*`) | Sembrado (`S068`) → `ADMIN_TENANT` |
| `modulo` / `modulo_seccion` / `modulo_menu` | **Ausente** |
| `cliente_modulo` para módulo CFG | **Ausente** (si se crea módulo comercial) |
| `rol_menu_permiso` para pantallas CFG | **Ausente** |
| Entrada en `GET /auth/menu` | **No aparece** |

La navegación FE actual de CFG (si existe) **no** puede depender del menú dinámico Backend hasta que existan registros de catálogo + RMP; hoy solo puede apoyarse en rutas hardcodeadas + `GET /auth/permissions/me`.

---

## 5. Fuentes canónicas leídas

- `app/modules/auth/presentation/endpoints.py` — `GET /auth/menu`
- `app/core/authorization/menu_resolver.py`
- `app/modules/modulos/application/services/modulo_menu_service.py`
- `app/core/menu/menu_route_normalizer.py`
- `app/bootstrap_v2/02_catalog/S010__seed_modulo_menu_completo.sql`
- `app/bootstrap_v2/02_catalog/S020__seed_admin_menu.sql`
- `app/bootstrap_v2/02_catalog/S021__menu_routes_saas_alignment.sql`
- `app/bootstrap_v2/02_catalog/permisos_rbac/S068__permisos_rbac_cfg.sql`
- `app/modules/tenant/application/services/owner_sync_service.py`
- Contratos FE: `app/docs/frontend-contracts/cfg/04_RBAC.md`
- Decisión dominio: `app/docs/arquitectura/code-generation/cfg-platform-architecture/00_EXECUTIVE_SUMMARY.md`
