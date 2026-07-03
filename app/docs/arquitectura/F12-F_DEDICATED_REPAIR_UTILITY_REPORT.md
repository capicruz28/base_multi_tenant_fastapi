# F12-F — Dedicated Repair Utility (Development Only)

**Fecha:** 2026-06-28  
**Referencia:** F12-C (`f12c_repair_acmec.py`) generalizado  
**Alcance:** Utilidad de reparación para tenants Dedicated existentes — **solo desarrollo**

---

## Resumen

Se implementó una utilidad oficial que replica el pipeline F12-C sin hardcodear tenant:

| Artefacto | Ruta |
|-----------|------|
| CLI | `scripts/repair_dedicated_tenant_permissions.py` |
| Librería | `scripts/lib/dedicated_tenant_permission_repair.py` |

**Entrada:** `--cliente-id <UUID>` **o** `--subdominio <slug>`  
**Modos:** `--dry-run` | `--apply`  
**Validación HTTP opcional:** `--validate-http --password <pwd>`

No se modificaron: RBAC core, PermissionResolver, MenuResolver, onboarding, provisioning saga, Shared, Platform ni migraciones.

---

## Pipeline (idéntico F12-C)

```mermaid
flowchart LR
    A[Resolver tenant Dedicated] --> B[DedicatedPermissionCatalogSync]
    B --> C[bootstrap_global_grants_admin_tenant]
    C --> D[invalidate PermissionResolver cache]
    D --> E[invalidate connection metadata cache]
    E --> F[Reporte JSON]
    F --> G[Opcional: HTTP smoke]
```

1. **DedicatedPermissionCatalogSync** — `DedicatedPermissionCatalogSyncService.run_sync()`
2. **bootstrap_global_grants_admin_tenant** — `OnboardingRbacService.bootstrap_global_grants_admin_tenant()`
3. **Invalidación caches** — `get_permission_resolver().invalidate_for_tenant()` + `invalidate_client_connection_cache()`
4. **Reporte** — JSON stdout con tenant, contadores, duración, resultado

---

## Modo `--dry-run`

Informa sin escribir:

| Sección | Contenido |
|---------|-----------|
| `dry_run_diff.before` | Snapshot SQL: permisos `admin.*`, grants ADMIN_TENANT, marker sync |
| `dry_run_diff.catalog` | Permisos faltantes, actualizaciones estimadas, desactivaciones, `sync_would_skip` |
| `dry_run_diff.grants` | Grants globales faltantes (`modulo_id IS NULL`, patrones F12-C) |

---

## Salida del reporte

| Campo | Descripción |
|-------|-------------|
| `tenant` | `cliente_id`, `subdominio`, `codigo_cliente`, `database_name` |
| `catalog_sync.permisos_creados` | Insertados por sync (apply) |
| `catalog_sync.permisos_actualizados` | Actualizados por sync |
| `grants.grants_agregados` | Nuevos `rol_permiso` globales |
| `grants.grants_existentes` | Total grants ADMIN_TENANT tras repair |
| `duration_sec` | Tiempo total |
| `result` | `success` \| `success_with_gaps` \| `dry_run_ok` \| `failed` |
| `validation` | Resultado HTTP si `--validate-http` |

---

## Requisitos de entorno

Ejecutar **dentro del contenedor dev** (o entorno con variables equivalentes a `.env.docker`):

- `PROVISIONING_DDL_EXECUTOR_ENABLED=true`
- `PROVISIONING_DDL_SERVER`, `PROVISIONING_DDL_USER`, `PROVISIONING_DDL_PASSWORD`
- `DEDICATED_PERMISSION_CATALOG_SYNC_ENABLED=true` (default)

Desde el host sin esas variables, `provisioning_dedicated_session` falla con `PROVISIONING_DDL_EXECUTOR_ENABLED=false`.

**Ejemplo:**

```bash
docker exec fastapi_backend python scripts/repair_dedicated_tenant_permissions.py \
  --subdominio acce --dry-run

docker exec fastapi_backend python scripts/repair_dedicated_tenant_permissions.py \
  --subdominio acce --apply --validate-http --password 'Admin123!'
```

---

## Validación tenant `acce` (RC-06 follow-up)

### Pre-repair (`--dry-run`)

| Métrica | Valor |
|---------|-------|
| Tenant | `acce` / `5176fbd6-69f0-4793-9f96-8cc6ddd347c8` |
| BD dedicada | `erp_cli016` (Dedicated) |
| Permisos `admin.*` faltantes | **10** (`admin.usuario.leer`, `admin.rol.leer`, …) |
| Grants faltantes (SQL) | **0** *(permisos aún no existían en `permiso`)* |
| `admin.usuario.leer` en grants | **No** |

### Post-repair (`--apply` + HTTP)

| Check | Resultado |
|-------|-----------|
| Sync marker `permission_catalog_sync` | Registrado |
| `admin_permiso_count` | **12** (incl. `admin.usuario.leer`, `admin.rol.leer`) |
| `admin_rol_permiso_count` | **12** |
| Grants totales ADMIN_TENANT | **83** (antes ~64) |
| `GET /auth/permissions/me` | **200** — `admin.usuario.leer` ✅, `admin.rol.leer` ✅ |
| `GET /api/v1/usuarios/?page=1&limit=10` | **200** |
| `GET /api/v1/roles/?page=1&limit=10` | **200** |
| `perm_count` | **83** |
| Duración apply idempotente | **~18 s** |
| `result` | **`success`** |

### Idempotencia

Segunda ejecución `--apply`:

- `catalog_sync.status`: **`skipped`** (marker hash coincide)
- `grants.grants_agregados`: **0**
- HTTP validation: **passed**

---

## Clasificación

| Dimensión | Valor |
|-----------|-------|
| Tipo | Utilidad operativa dev — reparación RBAC Dedicated |
| Riesgo producción | **N/A** — documentada solo para desarrollo/staging |
| Relación RC-06 | Corrige el gap `acce` que causaba 403 en Gestión de Usuarios |

---

## Recomendación operativa

1. Ejecutar `--dry-run` antes de `--apply` en cualquier tenant Dedicated legacy.
2. Tras `--apply`, usar `--validate-http` con la contraseña real del admin tenant (no asumir `admin123`).
3. Para batch futuro: iterar tenants `tipo_instalacion=dedicated` desde ADMIN — fuera de alcance F12-F (solo utilidad single-tenant).

---

**F12-F Dedicated Repair Utility — implementación y validación cerradas.**
