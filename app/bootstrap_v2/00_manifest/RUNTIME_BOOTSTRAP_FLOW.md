# Flujo bootstrap RBAC runtime (Fase 2)

Documentación operativa: qué reemplaza scripts `03_runtime` y cuándo dejar de ejecutarlos en PROD.

## Resumen

| Script legacy | Qué hacía | Reemplazo runtime |
|---------------|-----------|-------------------|
| **R010** `asignar_core_app_a_roles.sql` | `INSERT rol_permiso` con `core.app.acceder` para roles del tenant | `OnboardingRbacService.asignar_permisos_admin_tenant()` al crear cliente |
| **R020** `relacion_sys_admin_cliente_modulo.sql` | `INSERT cliente_modulo` SYS_ADMIN (y similares) | `OnboardingRbacService.activar_modulos_base_cliente()` (ORG + SYS_ADMIN por `modulo.codigo`) |
| **S030** | Seed `core.app.acceder` en `permiso` | `core_permissions.register_core_permissions()` + `permission_sync_service` al startup |
| **S040–S066** | Seeds masivos `permiso` / `rol_permiso` | **No usar** — fuente oficial: rutas `require_permission` + `permission_sync` |

Los scripts **no se eliminan** del repo (compatibilidad, entornos legacy, reparación manual).

## Orden en `ClienteOnboardingService` (misma transacción)

1. `INSERT cliente`
2. `INSERT rol` (ADMIN_TENANT, MANAGER_TENANT, USER_TENANT)
3. `INSERT usuario` admin + `INSERT usuario_rol`
4. **`OnboardingRbacService.bootstrap_cliente_rbac`** (misma `AsyncSession`)
5. `cliente_auth_config`, `cfg_codigo_secuencia`
6. `commit`

## `bootstrap_cliente_rbac`

1. Valida que exista al menos un `permiso` activo (requiere startup previo con sync).
2. `activar_modulos_base_cliente`: módulos `ORG`, `SYS_ADMIN` vía `modulo.codigo`; `cliente_modulo` idempotente.
3. `asignar_permisos_admin_tenant`: rol `ADMIN_TENANT`; grants desde tabla `permiso` activos:
   - `core.app.acceder`
   - `admin.%`
   - `modulos.%`
   - `org.%`
   - `tenant.%` **excepto** `tenant.cliente.crear`
   - Solo `INSERT rol_permiso` si no existe (no crea permisos).

## Startup (catálogo permisos)

1. `register_core_permissions()` — whitelist estática (`core.app.acceder`).
2. `ensure_registry_from_routes()` — permisos desde endpoints.
3. `permission_sync_service.sync()` — upsert en `permiso`; desactiva obsoletos **excepto** `PROTECTED_PERMISSION_CODIGOS`.

## Scripts deprecated en PROD (nuevo tenant)

Tras desplegar este flujo, **no son necesarios** para tenants creados por API:

- `03_runtime/R010__asignar_core_app_a_roles.sql`
- `03_runtime/R020__relacion_sys_admin_cliente_modulo.sql`
- `02_catalog/S030__*` (si solo insertaba `core.app.acceder`)
- `02_catalog/S040` … `S066` (grants por rol/permiso)

Siguen siendo útiles:

- `01_schema/V010`, `V020`, `V030` — esquema
- `02_catalog/S010`, `S020` — menús y catálogo `modulo`
- Reparación batch de tenants legacy (job idempotente, no implementado aquí)

## Riesgos pendientes

| Riesgo | Mitigación |
|--------|------------|
| Onboarding sin startup previo → catálogo `permiso` vacío | Error `ONBOARDING_PERMISSO_CATALOG_EMPTY`; arrancar app una vez antes de crear tenants |
| Tenants legacy sin `cliente_modulo` / `rol_permiso` | Ejecutar R010/R020 una vez o job de reparación |
| Menú vs API (`rol_menu_permiso` vs `rol_permiso`) | Fuera de alcance; MenuPermissionBinder no implementado |
| Permisos nuevos en rutas no asignados a ADMIN_TENANT existente | Re-onboarding manual o job de re-grant por prefijos |
| `MANAGER_TENANT` / `USER_TENANT` sin bundle | Solo ADMIN_TENANT recibe grants en v1 |

## Referencias de código

- `app/core/authorization/core_permissions.py`
- `app/core/authorization/permission_sync_service.py`
- `app/modules/tenant/application/services/onboarding_rbac_service.py`
- `app/modules/tenant/application/services/cliente_onboarding_service.py`
