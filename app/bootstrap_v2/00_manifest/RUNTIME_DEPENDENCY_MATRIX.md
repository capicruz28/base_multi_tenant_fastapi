# RUNTIME DEPENDENCY MATRIX

Matrices de dependencia **real** (imports, invocaciones, FK lógicas). Solo RBAC/onboarding/runtime auditado.

---

## A. Matriz script bootstrap → tablas → consumidor backend

| Script | Tablas escritas | Consumido por (runtime) | ¿Necesario si onboarding+sync completos? |
|--------|-----------------|-------------------------|----------------------------------------|
| **S010** | `modulo`, `modulo_seccion`, `modulo_menu` | `ModuloMenuService`, `ClienteModuloService`, `permission_sync` (`modulo_id`) | **SÍ** (catálogo producto) |
| **S020** §1–4 | `modulo` SYS_ADMIN, menús | `ModuloMenuService`, menú `/admin/*` | **SÍ** (estructura) |
| **S020** §5–6 | `permiso` admin.tenant/platform, `rol_permiso` | Desalineado: API usa otros códigos | **NO** (deprecar) |
| **S030** | `permiso` core.app.acceder | R010; no usado en `require_permission` | **NO** (reemplazar registry) |
| **S040–S066** | `permiso` ~377 códigos | `permisos_usuario_service` si `rol_permiso` existe; sync solapa 93 | **NO** en PROD |
| **S067** | — | — | **SKIP** |
| **R010** | `rol_permiso` → core.app.acceder | No validado en API | **NO** (onboarding grant) |
| **R020** | `cliente_modulo` SYS_ADMIN | `ModuloMenuService` JOIN | **NO** (onboarding activación) |

---

## B. Matriz servicio backend → tablas → depende de bootstrap

| Servicio / componente | Lee | Escribe | Depende de SQL bootstrap |
|----------------------|-----|---------|--------------------------|
| `ClienteOnboardingService` | — | `cliente`, `rol`, `usuario`, `usuario_rol`, `cliente_auth_config`, `cfg_codigo_secuencia` | Solo schema V020/V010 |
| `ClienteModuloService.activar_*` | `modulo`, `cliente_modulo` | `cliente_modulo`, roles vía plantillas | **S010** (catálogo modulo_id) |
| `aplicar_plantillas_roles` | `modulo_rol_plantilla`, `modulo_menu` | `rol`, **`rol_menu_permiso`** | S010; plantillas en BD |
| `permission_sync_service.sync` | `modulo`, `permiso` | `permiso` INSERT/UPDATE/deactivate | V030; opcional S010 para `modulo_id` |
| `permisos_usuario_service` | `usuario_rol`, **`rol_permiso`**, `permiso`, `cliente_modulo` | — | V030 + grants (R010/onboarding) |
| `permisos_negocio_service` | `permiso`, `rol_permiso` | `rol_permiso` | V030 + sync |
| `PermisoService` (rbac) | `rol_menu_permiso` | **`rol_menu_permiso`** | V020 menú |
| `ModuloMenuService.obtener_menu_usuario` | `cliente_modulo`, `modulo_menu`, **`rol_menu_permiso`** | — | **S010**, **R020** o onboarding CM |
| `MenuResolverService` | vía arriba + `PermissionResolver` | — (menú in-memory `required_permission`) | Igual |
| `has_permission` / `require_permission` | `user.permisos` (rol_permiso) | — | sync + grants |
| `user_builder` | `permisos_usuario_service` o resolver | — | grants |

---

## C. Matriz permisos: código vs SQL vs sync

| Código permiso | En `require_permission` | En S040–S066 | Creado por sync | Desactivado por sync si solo SQL |
|----------------|---------------------------|--------------|-----------------|----------------------------------|
| `org.empresa.leer` | ✅ | ✅ | ✅ | No |
| `admin.usuario.leer` | ✅ | ❌ | ✅ | N/A |
| `tenant.cliente.leer` | ✅ | ❌ | ✅ | N/A |
| `modulos.menu.leer` | ✅ | ❌ | ✅ | N/A |
| `core.app.acceder` | ❌ | ❌ (S030) | ❌ | **Sí** (si solo S030) |
| `admin.tenant.access` | ❌ | ❌ (S020) | ❌ | **Sí** |
| `fin.asiento.registrar` (ej.) | ❌ | ✅ | ❌ | **Sí** |

**Conteos medidos (repo actual):**

| Métrica | Valor |
|---------|------:|
| Códigos únicos en API | 113 |
| Códigos únicos en SQL catálogo | 377 |
| Solo API (sync los inserta) | 20 |
| Solo SQL (sync desactiva tras startup) | 284 |
| Intersección | 93 |

---

## D. Matriz flujo tenant nuevo (estado actual vs objetivo)

| Paso | Hoy (solo API) | Hoy (+ R010 R020 S030 S040…) | Objetivo (plan) |
|------|----------------|------------------------------|-----------------|
| 1 Crear cliente | ✅ | ✅ | ✅ onboarding |
| 2 Roles ADMIN_TENANT | ✅ | ✅ | ✅ |
| 3 Usuario admin | ✅ | ✅ | ✅ |
| 4 Tabla `permiso` poblada | ❌ hasta startup | ✅ S030+S040+sync | ✅ startup |
| 5 `rol_permiso` admin | ❌ | ⚠️ R010 core only; S020 códigos wrong | ✅ onboarding grants |
| 6 `cliente_modulo` SYS_ADMIN | ❌ | ✅ R020 | ✅ onboarding |
| 7 `cliente_modulo` ORG | ❌ | ❌ manual | ✅ onboarding |
| 8 Login sin empresa | ✅ | ✅ | ✅ |
| 9 API admin.usuario.* | ❌ | ❌ (salvo asignación manual UI) | ✅ |
| 10 Menú SYS_ADMIN | ❌ | ✅ (R020 + as_tenant_admin) | ✅ |

---

## E. Matriz startup (`run_rbac_startup`)

| Paso | Función | Efecto BD | Reemplaza script |
|------|---------|-----------|------------------|
| 1 | `ensure_registry_from_routes` | — (memoria) | — |
| 2 | `apply_rbac_enforcement` | — | — |
| 3 | `sync_permissions` | `permiso` upsert + deactivate | **S040–S066** (parcial, 113 vs 377) |
| 4 | audit/warn | — | — |
| — | **NO** `MenuPermissionBinder` | — | FIX SQL binder (no usado) |

**Config:**

| Variable | Default | Efecto |
|----------|---------|--------|
| `RBAC_PERMISSION_SYNC_ENABLED` | true | Sin sync, tabla `permiso` vacía → grants fallan |
| `USE_PERMISSION_RESOLVER` | false | `user_builder` usa SQL directo `permisos_usuario_service` |

---

## F. Matriz `rol_menu_permiso` vs `rol_permiso`

| Aspecto | `rol_permiso` | `rol_menu_permiso` |
|---------|---------------|-------------------|
| Tabla | V030 | V020 |
| Usado en API HTTP | **Sí** (`has_permission`) | **No** |
| Usado en menú UI | No (futuro con `effective_permission_codes`) | **Sí** (query ModuloMenuService) |
| Poblado por | R010, S020§6, `permisos_negocio_service`, (futuro onboarding) | `PermisoService`, plantillas activación módulo |
| Seeds bootstrap 02_catalog | No directo | No directo |

**Conclusión:** eliminar S040–S066 **no** elimina necesidad de `rol_menu_permiso`; son subsistemas paralelos.

---

## G. Matriz MenuPermissionBinder vs menu_permission_resolver

| | MenuPermissionBinder | menu_permission_resolver |
|--|---------------------|---------------------------|
| Invocado en startup | **No** | **Sí** (desde `MenuResolverService`) |
| Persiste en BD | Sí (`permiso_codigo_requerido`) | **No** (setattr en memoria) |
| Columna en V020 | **No existe** | N/A |
| Reemplazo funcional | N/A | **Sí** (resolver activo) |

**Hueco:** menús sin permiso `leer` en BD → warning en resolver; no bloquea API.

---

## H. Responsabilidades a mover (SQL → runtime)

| Responsabilidad | De (hoy) | A (objetivo) | Prioridad |
|-----------------|----------|--------------|-----------|
| Catálogo `permiso` negocio | S040–S066 | `permission_sync_service` | P0 |
| `core.app.acceder` en `permiso` | S030 | Registry + sync whitelist | P1 |
| `rol_permiso` core + admin + tenant + modulos | R010, S020§6 | `ClienteOnboardingService` grant | P0 |
| `cliente_modulo` SYS_ADMIN | R020 | Onboarding activación módulo | P0 |
| `cliente_modulo` ORG | manual / QA | Onboarding activación módulo | P1 |
| Menús ERP + SYS_ADMIN | S010, S020 | **Permanecer SQL** | — |
| `rol_menu_permiso` plantillas | SQL JSON plantillas | `aplicar_plantillas_roles` (mantener) | P2 |
| Reparación tenants legacy | R010, R020 batch | Job Python idempotente | P2 |

---

## I. Qué permanece en SQL (bootstrap permanente)

| Artefacto | Script | Motivo |
|-----------|--------|--------|
| Schema central + ERP + RBAC | V010, V020, V030 | DDL |
| 27 módulos + menús ERP | S010 | Sin generador código |
| SYS_ADMIN estructura menú | S020 §1–4 | Producto |
| QA/demo | `04_qa/` (fuera de alcance) | No PROD |

---

## J. Qué deprecar / eliminar de pipeline PROD

| Item | Acción |
|------|--------|
| S030 | Deprecar |
| S040–S066 | Deprecar → `_legacy/` |
| S067 | Omitir |
| R010 | Deprecar → onboarding |
| R020 | Deprecar → onboarding |
| S020 §5–6 | Deprecar (permisos/assignments) |
| Ejecutar S040 + startup sin whitelist | **Anti-patrón** (284 desactivaciones) |

---

## K. Referencia rápida: imports startup

```text
main.py
  └─ rbac_lifespan
       └─ permission_startup.run_rbac_startup
            ├─ ensure_registry_from_routes
            ├─ apply_rbac_enforcement
            ├─ sync_permissions → permission_sync_service.sync
            └─ audit_routes_permissions / warn_routes_without_permission

MenuResolverService (request-time, no startup)
  └─ ModuloMenuService.obtener_menu_usuario
  └─ resolve_required_permissions_for_menu_tree
```

```text
ClienteService.crear_cliente
  └─ ClienteOnboardingService.crear_cliente_con_onboarding
       (sin ClienteModuloService, sin rol_permiso)

ClienteModuloService.activar_modulo_cliente
  └─ aplicar_plantillas_roles → PermisoService → rol_menu_permiso
```
