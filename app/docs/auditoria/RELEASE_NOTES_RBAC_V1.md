# Release Notes — RBAC V1 STABLE

**Tag:** `RBAC_V1_STABLE`  
**Fecha:** 2026-05-31  
**Alcance validado:** Multiempresa M1 · ADMIN tenant-wide M4 · Bundles T1/T2/T3 · Onboarding runtime · ORG + INV trial

---

## Resumen

RBAC V1 establece el modelo oficial de autorización multi-tenant en CAXIS SaaS:

- **Cuatro roles operativos:** `ADMIN_PLATFORM`, `ADMIN_TENANT`, `MANAGER_TENANT`, `USER_TENANT`
- **Cuatro bundles:** `OWNER_FULL`, `BASE_OPERATIVE`, `MANAGER_STANDARD`, `USER_STANDARD`
- **Doble capa RBAC:** `rol_permiso` (API) + `rol_menu_permiso` (UI)
- **Multiempresa:** sesión JWT `empresa_id`, preferencia `empresa_default_id`, scope `usuario_rol.empresa_id`
- **Provisionamiento automático** en onboarding, assign role y reactivación
- **Repairs idempotentes** para tenants legacy

Documentación maestra: [`RBAC_V1_FINAL.md`](./RBAC_V1_FINAL.md)

---

## Entregas por fase

### M1 — Multiempresa

- Persistencia `empresa_default_id` en seleccionar/cambiar empresa y assign rol mono-empresa
- Login casos A–D; rechazo `USER_WITHOUT_COMPANY` para operativos sin empresas
- Admin global: elegibles desde todas las `org_empresa`
- Módulo `empresa_preference.py`

### M4 — ADMIN_TENANT tenant-wide

- Onboarding: `usuario_rol.empresa_id = NULL` para admin
- `repair_admin_tenant_tenant_wide.py` para migración legacy
- Admin accede a todas las empresas del tenant vía selector de sesión

### T1 — BASE_OPERATIVE

- 3 permisos transversales para MANAGER/USER: `core.app.acceder`, `tenant.branding.leer`, `org.empresa.leer`
- `BaseOperativeService` + `repair_base_operative.py`

### T2 — MANAGER_STANDARD

- 47 `rol_permiso` + 14 `rol_menu_permiso` para MANAGER_TENANT
- ORG+INV operativo (sin eliminar; empresa solo lectura)
- Menú visible ORG+INV; resuelve menú vacío pre-T2

### T3 — USER_STANDARD

- 16 `rol_permiso` + 14 `rol_menu_permiso` para USER_TENANT
- Predominantemente lectura ORG+INV

### Runtime e infraestructura

- `OnboardingRbacService` — reemplaza R010/R020 para tenants nuevos
- `OwnerSyncService` — OWNER_FULL para ADMIN_TENANT
- `permission_sync_service` — catálogo `permiso` code-first al startup
- `PermissionResolver` / `MenuResolver` — `/auth/permissions/me`, `/auth/menu`
- `require_erp_session` — gate sesión ERP (INV router)
- ORG session deps — tenant/company/hybrid scope
- INV/ORG queries — aislamiento `cliente_id` + `empresa_id`

---

## Bundles — conteos trial (ORG+INV)

| Bundle | Rol | `rol_permiso` | `rol_menu_permiso` (ver) |
|--------|-----|:-------------:|:------------------------:|
| BASE_OPERATIVE | MANAGER, USER | 3 | 0 |
| MANAGER_STANDARD | MANAGER_TENANT | 47 | 14 |
| USER_STANDARD | USER_TENANT | 16 | 14 |
| OWNER_FULL | ADMIN_TENANT | ~70–75 | ~18 |

---

## Scripts repair

| Script | Fase |
|--------|------|
| `repair_base_operative.py` | T1 |
| `repair_manager_standard.py` | T2 |
| `repair_user_standard.py` | T3 |
| `repair_admin_tenant_tenant_wide.py` | M4 |
| `repair_legacy_tenant_rbac.py` | Legacy bootstrap |
| `repair_platform_rbac.py` | Platform ADMIN |
| `repair_tenant_menu_grants.py` | Menú admin |
| `repair_minimal_erp_tenant.py` | ERP mínimo |

Orden recomendado legacy: M4 → legacy_rbac → T1 → T2 → T3 → menu_grants

---

## Bootstrap limpio (producción)

```text
V010 → V020 → V030 → S010 → S020 → [startup FastAPI] → POST /clientes/
```

**No requerido** para tenants nuevos: R010, R020, S030, S040–S066

Ver: [`BOOTSTRAP_SYSTEM_AUDIT.md`](./BOOTSTRAP_SYSTEM_AUDIT.md)

---

## Evidencias QA

| Fase | Archivo |
|------|---------|
| M1 | `app/bootstrap_v2/00_manifest/evidence/MULTIEMPRESA_M1_VALIDATION.json` |
| M4 | `app/bootstrap_v2/00_manifest/evidence/M4_ADMIN_TENANT_TENANT_WIDE_VALIDATION.json` |
| T1 | `app/bootstrap_v2/00_manifest/evidence/T1_BASE_OPERATIVE_INTEGRATION_VALIDATION.json` |
| T2 | `app/bootstrap_v2/00_manifest/evidence/T2_MANAGER_STANDARD_INTEGRATION_VALIDATION.json` |
| T3 | `app/bootstrap_v2/00_manifest/evidence/T3_USER_STANDARD_INTEGRATION_VALIDATION.json` |

---

## Tests

```bash
pytest tests/unit/test_multiempresa_m1.py tests/unit/test_m4_admin_tenant_wide.py -v
pytest tests/unit/test_base_operative_t1.py tests/unit/test_manager_standard_t2.py tests/unit/test_user_standard_t3.py -v
python scripts/run_t1_base_operative_integration.py
python scripts/run_t2_manager_standard_integration.py
python scripts/run_t3_user_standard_integration.py
```

---

## Documentación incluida

| Documento | Contenido |
|-----------|-----------|
| `RBAC_V1_FINAL.md` | Arquitectura y modelo oficial |
| `CHANGELOG_RBAC_V1.md` | Detalle de cambios por fase |
| `BOOTSTRAP_SYSTEM_AUDIT.md` | Instalación limpia BD |
| `RBAC_SECURITY_HARDENING_AUDIT.md` | Auditoría pre-STABLE |
| `BACKLOG_POST_RBAC_V1.md` | Deuda técnica post-V1 |
| Diseños T2/T3, auditorías M1/M4 | `app/docs/auditoria/` |

---

## Deuda técnica (no bloquea V1)

Los hallazgos P0/P1/P2 de hardening (IDOR modulos, WMS/SLS multiempresa, debug endpoints, etc.) quedan registrados en [`BACKLOG_POST_RBAC_V1.md`](./BACKLOG_POST_RBAC_V1.md) para fase posterior.

**Alcance congelado:** ORG + INV trial · roles oficiales · onboarding/repair validados.

---

## Upgrade / migración

### Tenant nuevo

1. Bootstrap SQL mínimo (schema + S010/S020)
2. Arrancar app (permission_sync)
3. `POST /api/v1/clientes/` — provisioning automático completo

### Tenant legacy

```bash
python scripts/repair_admin_tenant_tenant_wide.py --all --dry-run
python scripts/repair_legacy_tenant_rbac.py --audit-only
python scripts/repair_base_operative.py --all --apply
python scripts/repair_manager_standard.py --all --apply
python scripts/repair_user_standard.py --all --apply
```

---

## Referencias

- [`RBAC_V1_FINAL.md`](./RBAC_V1_FINAL.md)
- [`CHANGELOG_RBAC_V1.md`](./CHANGELOG_RBAC_V1.md)
- [`app/bootstrap_v2/README_BOOTSTRAP.md`](../../bootstrap_v2/README_BOOTSTRAP.md)
