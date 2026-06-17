# Gap platform QA bootstrap — fix mínimo (post-RC)

## Diagnóstico (confirmado en `bd_sistema_saas`)

| Elemento | Estado antes del repair |
|----------|-------------------------|
| Rol `ADMIN_PLATFORM` (D010) | Existe |
| `usuario` `superadmin` → `usuario_rol` → ADMIN_PLATFORM | OK |
| `rol_permiso` ADMIN_PLATFORM | **0 filas** |
| `cliente_modulo` cliente SYSTEM | **0** (D010 usó UUIDs módulo inexistentes) |
| `permiso.admin.platform.access` en catálogo | Sí, pero `es_activo=0` tras sync (sin ruta HTTP) |

### Causa raíz

1. **Orden bootstrap:** `S020` asigna `rol_permiso` solo a roles que **ya existen**; `D010` crea `ADMIN_PLATFORM` **después**.
2. **D010** no inserta `rol_permiso` para roles platform.
3. **Menú vacío:** `MenuResolver` filtra por `cliente_modulo`; sin `SYS_ADMIN` activo no hay módulos admin.
4. **Permisos FE:** usuarios con rol ADMIN_PLATFORM (sin bypass `is_super_admin`) resolvían **0** códigos vía `rol_permiso`.

El runtime onboarding **ADMIN_TENANT** no aplica al cliente SYSTEM — por diseño.

---

## Fix implementado (backend only)

| Artefacto | Función |
|-----------|---------|
| `platform_rbac_bootstrap_service.py` | Activa `SYS_ADMIN` + grants idempotentes ADMIN_PLATFORM |
| `repair_platform_rbac.py` | CLI legacy (deprecado → `bootstrap_platform.py`) |
| `bootstrap_platform.py` | CLI oficial `--audit-only` / `--apply` / `--rbac-only` |
| `core_permissions.py` | `admin.platform.access` en `PROTECTED_PERMISSION_CODIGOS` + registro estático |
| `http_smoke_platform_rbac.py` | Smoke superadmin + Origin `platform.app.local` |

### Grants ADMIN_PLATFORM (prefijos)

- `core.app.acceder`
- `admin.platform.access`
- `admin.usuario.%`
- `admin.rol.%`
- `tenant.%` (incluye `tenant.cliente.crear` en plataforma)
- `modulos.%`

---

## Operación

Tras **D010** + **startup** (permission_sync):

```bash
python scripts/repair_platform_rbac.py --audit-only
python scripts/repair_platform_rbac.py --apply
python scripts/http_smoke_platform_rbac.py --json-out app/bootstrap_v2/00_manifest/evidence/smoke_platform_last.json
```

En Docker:

```bash
docker exec -w /app -e PYTHONPATH=/app fastapi_backend python scripts/repair_platform_rbac.py --apply
```

---

## Evidencia `bd_sistema_saas` (2026-05-21)

- Before: `rol_permiso` = 0, `cliente_modulo` = 0  
- After: `rol_permiso` = **22**, `cliente_modulo` = **1** (SYS_ADMIN)  
- Smoke: **PASS** — `/auth/me` `platform_admin`, `/auth/menu` 1 módulo, `/auth/permissions/me` 414 códigos  

Ver [`evidence/PLATFORM_RBAC_REPAIR_EVIDENCE.json`](evidence/PLATFORM_RBAC_REPAIR_EVIDENCE.json).

---

## Fuera de alcance (no modificado)

- Frontend
- JWT / auth flows
- `OnboardingRbacService` tenant
- `permission_sync_service` lógica (solo extensión `core_permissions` protegidos)

---

## Pipeline staging actualizado

`D010` → sustituir `USE bd_sistema_saas` → startup → **`repair_platform_rbac.py --apply`** → onboarding tenant / smoke.
