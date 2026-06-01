# CHANGELOG — RBAC V1

**Versión:** RBAC_V1 (Release Candidate → Stable)  
**Fecha cierre:** 2026-05-31  
**Documento maestro:** [`RBAC_V1_FINAL.md`](./RBAC_V1_FINAL.md)  
**Estado:** Pendiente congelación `RBAC_V1_STABLE` (sin commit en esta entrega)

---

## Resumen

RBAC V1 cierra el modelo oficial de autorización multi-tenant CAXIS en cinco fases validadas:

| Fase | Entrega | Rol / alcance |
|:----:|---------|---------------|
| **M1** | Multiempresa sesión + preferencias | `empresa_default_id`, login A–D, persistencia selección |
| **M4** | ADMIN_TENANT tenant-wide | `usuario_rol.empresa_id = NULL` para admin |
| **T1** | BASE_OPERATIVE | Permisos transversales MANAGER/USER (3 RP) |
| **T2** | MANAGER_STANDARD | Bundle operativo ORG+INV (47 RP + 14 RMP) |
| **T3** | USER_STANDARD | Bundle lectura ORG+INV (16 RP + 14 RMP) |

**Bundles oficiales:** `OWNER_FULL` · `BASE_OPERATIVE` · `MANAGER_STANDARD` · `USER_STANDARD`

**Roles oficiales:** `ADMIN_PLATFORM` (PLATFORM_ADMIN) · `ADMIN_TENANT` · `MANAGER_TENANT` · `USER_TENANT`

---

## 1. Cambios por fase

### M1 — Multiempresa

**Objetivo:** Unificar empresa activa (JWT), preferencia login (`empresa_default_id`) y scope de rol (`usuario_rol.empresa_id`).

| ID | Cambio | Archivo(s) |
|----|--------|------------|
| M1.1 | Persistir `empresa_default_id` en `POST /auth/empresa/seleccionar/` | `auth_service.py` |
| M1.2 | Persistir en `POST /auth/empresa/cambiar/` | `auth_service.py` |
| M1.3 | Auto-set default tras assign rol mono-empresa | `user_service.py` → `_maybe_set_empresa_default_after_role_assign` |
| M1.4 | Admin global: reglas login A/B/C sin forzar selección | `auth_service.py` → `get_empresa_activa_para_login` |
| M1.5 | Rechazar login operativo sin empresas (`USER_WITHOUT_COMPANY`) | `auth_service.py`, `endpoints.py` |
| M1.6 | Limpiar default inválida en login | `empresa_preference.py`, `auth_service.py` |
| M1.7 | Tests unitarios casos A–D | `test_multiempresa_m1.py`, `test_empresa_sesion_auth.py` |
| M1.8 | Decisión UQ `usuario_rol` documentada | `MULTIEMPRESA_M1_IMPLEMENTATION.md` |

**Módulo nuevo:** `app/core/tenant/empresa_preference.py`

**Impacto funcional:**

- Usuario selecciona empresa → preferencia persistida para próximo login.
- Operativo sin empresas elegibles → 403 (no login silencioso).
- Admin tenant-wide accede a todas las org del tenant.

---

### M4 — ADMIN_TENANT tenant-wide

**Objetivo:** Alinear `ADMIN_TENANT` con Modelo B — administrador del tenant, no scoped a EMP001.

| Cambio | Archivo(s) |
|--------|------------|
| Onboarding: `usuario_rol.empresa_id = NULL` para admin | `cliente_onboarding_service.py` |
| `vincular_admin_empresa`: refuerza UR NULL + `empresa_default_id` | `minimal_erp_tenant_bootstrap_service.py` |
| Script repair idempotente scoped → NULL | `scripts/repair_admin_tenant_tenant_wide.py` |
| Audit repair minimal ERP invertido para M4 | `scripts/repair_minimal_erp_tenant.py` |

**Impacto funcional:**

- Admin crea EMP002 → acceso automático vía selector (elegibles = todas org).
- Elimina riesgo L-07 (pérdida `tenant_admin` al cambiar sesión).
- MANAGER/USER **no afectados** — siguen company-scoped.

---

### T1 — BASE_OPERATIVE

**Objetivo:** Provisionar permisos transversales del shell ERP para roles operativos.

| Cambio | Archivo(s) |
|--------|------------|
| Constantes bundle (3 códigos) | `base_operative_constants.py` |
| Servicio idempotente `rol_permiso` | `base_operative_service.py` |
| Integración onboarding | `onboarding_rbac_service.py` |
| Hook assign/reactivate | `user_service.py` → `_ensure_base_operative_for_operative_role` |
| Repair script | `scripts/repair_base_operative.py` |
| Tests unitarios | `tests/unit/test_base_operative_t1.py` |
| Integración E2E | `scripts/run_t1_base_operative_integration.py` |

**Permisos provisionados:**

```
core.app.acceder
tenant.branding.leer
org.empresa.leer
```

**Impacto funcional:**

- MANAGER/USER pueden cargar branding post-login sin 403.
- Solo `rol_permiso` — **no** menú (T2/T3 resuelven RMP).

---

### T2 — MANAGER_STANDARD

**Objetivo:** Bundle operativo ORG+INV para `MANAGER_TENANT` con menú visible.

| Cambio | Archivo(s) |
|--------|------------|
| Diseño funcional | `MANAGER_STANDARD_BUNDLE_DESIGN.md` |
| Diagnóstico menú vacío | `MANAGER_EMPTY_MENU_ROOT_CAUSE.md` |
| Constantes (47 RP + 14 RMP) | `manager_standard_constants.py` |
| Servicio idempotente RP + RMP | `manager_standard_service.py` |
| Integración onboarding | `onboarding_rbac_service.py` |
| Hook assign/reactivate (non-blocking) | `user_service.py` |
| Repair script | `scripts/repair_manager_standard.py` |
| Tests unitarios | `tests/unit/test_manager_standard_t2.py` |
| Integración E2E | `scripts/run_t2_manager_standard_integration.py` |

**Restricciones funcionales aprobadas:**

- Sin `*.eliminar` ORG/INV.
- Sin administración empresas (`org.empresa` solo leer).
- Sin SYS_ADMIN / admin.* / tenant.* (excepto branding vía BASE).

**Impacto funcional:**

- `GET /auth/menu` MANAGER → ORG + INV (14 menús).
- UI: crear/editar sí; eliminar no.
- API: operación ORG/INV sin eliminar.

---

### T3 — USER_STANDARD

**Objetivo:** Bundle lectura ORG+INV para `USER_TENANT`.

| Cambio | Archivo(s) |
|--------|------------|
| Diseño funcional | `USER_STANDARD_BUNDLE_DESIGN.md` |
| Constantes (16 RP + 14 RMP) | `user_standard_constants.py` |
| Servicio idempotente RP + RMP | `user_standard_service.py` |
| Integración onboarding | `onboarding_rbac_service.py` |
| Hook assign/reactivate (non-blocking) | `user_service.py` |
| Repair script | `scripts/repair_user_standard.py` |
| Tests unitarios | `tests/unit/test_user_standard_t3.py` |
| Integración E2E | `scripts/run_t3_user_standard_integration.py` |

**Impacto funcional:**

- `GET /auth/menu` USER → ORG + INV (solo ver + exportar).
- Sin permisos crear/editar/eliminar/aprobar.
- Sin SYS_ADMIN.

---

## 2. Scripts repair

Todos idempotentes; soportan `--dry-run` / `--apply` y filtro por `--subdominio`, `--cliente-id` o `--all`.

### 2.1 Repairs RBAC V1 (prioritarios)

| Script | Fase | Target | Acción |
|--------|:----:|--------|--------|
| [`scripts/repair_base_operative.py`](../../scripts/repair_base_operative.py) | T1 | MANAGER + USER | Inserta 3 permisos BASE en `rol_permiso` |
| [`scripts/repair_manager_standard.py`](../../scripts/repair_manager_standard.py) | T2 | MANAGER_TENANT | Inserta 47 RP + 14 RMP |
| [`scripts/repair_user_standard.py`](../../scripts/repair_user_standard.py) | T3 | USER_TENANT | Inserta 16 RP + 14 RMP |
| [`scripts/repair_admin_tenant_tenant_wide.py`](../../scripts/repair_admin_tenant_tenant_wide.py) | M4 | ADMIN_TENANT | `UPDATE usuario_rol SET empresa_id = NULL` |

**Uso:**

```bash
python scripts/repair_base_operative.py --dry-run --all
python scripts/repair_manager_standard.py --subdominio mi-tenant --apply
python scripts/repair_user_standard.py --cliente-id <UUID> --apply
python scripts/repair_admin_tenant_tenant_wide.py --all --apply
```

### 2.2 Repairs complementarios

| Script | Propósito |
|--------|-----------|
| [`scripts/repair_legacy_tenant_rbac.py`](../../scripts/repair_legacy_tenant_rbac.py) | Bootstrap RBAC legacy (equivalente R010+R020 + OwnerSync) |
| [`scripts/repair_platform_rbac.py`](../../scripts/repair_platform_rbac.py) | RBAC cliente plataforma (`ADMIN_PLATFORM`) |
| [`scripts/repair_tenant_menu_grants.py`](../../scripts/repair_tenant_menu_grants.py) | RMP admin tenant (menú SYS_ADMIN sidebar) |
| [`scripts/repair_minimal_erp_tenant.py`](../../scripts/repair_minimal_erp_tenant.py) | ERP mínimo: org_empresa + vínculo admin |

### 2.3 Orden recomendado (tenants legacy)

```
1. repair_admin_tenant_tenant_wide.py   (M4)
2. repair_legacy_tenant_rbac.py        (módulos + OWNER_FULL)
3. repair_base_operative.py            (T1)
4. repair_manager_standard.py          (T2)
5. repair_user_standard.py             (T3)
6. repair_tenant_menu_grants.py        (si admin sin menú)
```

---

## 3. Evidencias QA

### 3.1 Evidencias por fase

| Fase | Archivo | Resultado |
|:----:|---------|:---------:|
| M1 | `app/bootstrap_v2/00_manifest/evidence/MULTIEMPRESA_M1_VALIDATION.json` | PASS (31 tests) |
| M4 | `app/bootstrap_v2/00_manifest/evidence/M4_ADMIN_TENANT_TENANT_WIDE_VALIDATION.json` | PASS (35 tests) |
| T1 | `app/bootstrap_v2/00_manifest/evidence/T1_BASE_OPERATIVE_INTEGRATION_VALIDATION.json` | PASS (sin repair) |
| T2 | `app/bootstrap_v2/00_manifest/evidence/T2_MANAGER_STANDARD_INTEGRATION_VALIDATION.json` | PASS (47 RP, 14 RMP, menú ORG+INV) |
| T3 | `app/bootstrap_v2/00_manifest/evidence/T3_USER_STANDARD_INTEGRATION_VALIDATION.json` | PASS (16 RP, 14 RMP, solo lectura) |

### 3.2 Evidencias complementarias RC1

| Archivo | Contenido |
|---------|-----------|
| `M1_M2_STAGING_INTEGRATION_VALIDATION.json` | OwnerSync + staging |
| `M1_M2_TRIAL_OWNER_SYNC_MENU_VALIDATION.json` | Menú owner trial |
| `RC1_FINAL_CONSOLIDATED.json` | Smoke consolidado RC1 |
| `PRUEBA_REPAIR_EVIDENCE.json` | Repair tenant prueba |
| `PLATFORM_RBAC_REPAIR_EVIDENCE.json` | Platform RBAC |

### 3.3 Validaciones clave por integración

**T1 — post-onboarding sin repair:**

- MANAGER y USER tienen los 3 códigos BASE.
- ADMIN incluye BASE como superconjunto.

**T2 — post-onboarding:**

- `rol_permiso` MANAGER = 47.
- `rol_menu_permiso` ver = 14.
- `/auth/menu` → ORG + INV; `any_eliminar_true = false`.

**T3 — post-onboarding:**

- `rol_permiso` USER = 16.
- `rol_menu_permiso` ver = 14.
- `/auth/menu` → ORG + INV; sin crear/editar/eliminar; sin SYS_ADMIN.

---

## 4. Pruebas

### 4.1 Tests unitarios

```bash
# M1 Multiempresa
pytest tests/unit/test_multiempresa_m1.py tests/unit/test_empresa_sesion_auth.py -v

# M4 Admin tenant-wide
pytest tests/unit/test_m4_admin_tenant_wide.py -v

# T1 BASE_OPERATIVE
pytest tests/unit/test_base_operative_t1.py -v

# T2 MANAGER_STANDARD
pytest tests/unit/test_manager_standard_t2.py -v

# T3 USER_STANDARD
pytest tests/unit/test_user_standard_t3.py -v

# Assign role scope
pytest tests/unit/test_assign_role_empresa_scope.py -v
```

### 4.2 Integración runtime (Docker)

```bash
docker compose up -d --build backend
# Esperar startup + permission_sync

python scripts/run_t1_base_operative_integration.py
python scripts/run_t2_manager_standard_integration.py
python scripts/run_t3_user_standard_integration.py
```

### 4.3 Pipeline RC (referencia)

```bash
python scripts/run_rc_validation_pipeline.py --unit-only
python scripts/http_smoke_tenant_rbac.py
```

---

## 5. Impactos funcionales

### 5.1 Por rol (post RBAC V1)

| Rol | Antes | Después RBAC V1 |
|-----|-------|-----------------|
| **ADMIN_TENANT** | Scoped EMP001 en onboarding; menú OK | Tenant-wide (M4); OWNER_FULL; acceso todas org |
| **MANAGER_TENANT** | Cascara vacía; menú `[]`; 403 branding | BASE + MANAGER_STANDARD; menú ORG+INV; sin eliminar |
| **USER_TENANT** | Cascara vacía; menú `[]` | BASE + USER_STANDARD; menú ORG+INV lectura |
| **PLATFORM_ADMIN** | Gap D010/S020 | `repair_platform_rbac.py` (sin cambio en fases M/T) |

### 5.2 Flujos afectados

| Flujo | Cambio |
|-------|--------|
| **Onboarding tenant** | Provisiona T1+T2+T3 automáticamente además de OWNER_FULL |
| **Assign role** | Hooks ensure bundles (non-blocking) + M1 default |
| **Reactivación rol** | Mismos hooks que assign |
| **Login multiempresa** | Persistencia default; admin global elegibles = todas org |
| **GET /auth/menu** | MANAGER/USER ya no retornan `modulos: []` |
| **GET /clientes/tenant/branding** | MANAGER/USER pasan con `tenant.branding.leer` |

### 5.3 Sin cambio (explícito)

| Área | Estado |
|------|--------|
| Frontend | Sin modificaciones en M1–T3 |
| OwnerSyncService | Sin cambio estructural (OWNER_FULL) |
| Permission sync startup | Sin cambio |
| Filtro ERP company-scoped | JWT `empresa_id` obligatorio para datos |
| Scripts legacy R010/R020 | Deprecated pero conservados |

### 5.4 Conteos bundle (trial ORG+INV+SYS_ADMIN)

| Bundle | Rol | `rol_permiso` | `rol_menu_permiso` (ver) |
|--------|-----|:-------------:|:------------------------:|
| BASE_OPERATIVE | MGR, USER | 3 | 0 |
| MANAGER_STANDARD | MANAGER | 47 | 14 |
| USER_STANDARD | USER | 16 | 14 |
| OWNER_FULL | ADMIN | ~70–75 | ~18 |

---

## 6. Documentación generada

| Documento | Propósito |
|-----------|-----------|
| [`RBAC_V1_FINAL.md`](./RBAC_V1_FINAL.md) | Documentación oficial consolidada |
| [`BOOTSTRAP_SYSTEM_AUDIT.md`](./BOOTSTRAP_SYSTEM_AUDIT.md) | Auditoría instalación limpia |
| [`MULTIEMPRESA_M1_IMPLEMENTATION.md`](./MULTIEMPRESA_M1_IMPLEMENTATION.md) | Detalle M1 |
| [`M4_ADMIN_TENANT_TENANT_WIDE_IMPLEMENTATION.md`](./M4_ADMIN_TENANT_TENANT_WIDE_IMPLEMENTATION.md) | Detalle M4 |
| [`BASE_OPERATIVE_T1_IMPLEMENTATION.md`](./BASE_OPERATIVE_T1_IMPLEMENTATION.md) | Detalle T1 |
| [`MANAGER_STANDARD_BUNDLE_DESIGN.md`](./MANAGER_STANDARD_BUNDLE_DESIGN.md) | Diseño T2 |
| [`USER_STANDARD_BUNDLE_DESIGN.md`](./USER_STANDARD_BUNDLE_DESIGN.md) | Diseño T3 |
| [`MANAGER_EMPTY_MENU_ROOT_CAUSE.md`](./MANAGER_EMPTY_MENU_ROOT_CAUSE.md) | Diagnóstico previo T2 |

---

## 7. Archivos de código principales (referencia)

### Servicios nuevos

```
app/modules/tenant/application/services/base_operative_constants.py
app/modules/tenant/application/services/base_operative_service.py
app/modules/tenant/application/services/manager_standard_constants.py
app/modules/tenant/application/services/manager_standard_service.py
app/modules/tenant/application/services/user_standard_constants.py
app/modules/tenant/application/services/user_standard_service.py
app/core/tenant/empresa_preference.py
```

### Servicios modificados

```
app/modules/tenant/application/services/onboarding_rbac_service.py
app/modules/tenant/application/services/cliente_onboarding_service.py
app/modules/tenant/application/services/minimal_erp_tenant_bootstrap_service.py
app/modules/users/application/services/user_service.py
app/modules/auth/application/services/auth_service.py  (M1)
```

### Scripts repair nuevos

```
scripts/repair_base_operative.py
scripts/repair_manager_standard.py
scripts/repair_user_standard.py
scripts/repair_admin_tenant_tenant_wide.py
scripts/run_t1_base_operative_integration.py
scripts/run_t2_manager_standard_integration.py
scripts/run_t3_user_standard_integration.py
```

---

## 8. Breaking changes / migración

| Escenario | Acción requerida |
|-----------|------------------|
| Tenant nuevo post-RBAC V1 | Ninguna — onboarding provisiona todo |
| Tenant legacy sin bundles | Ejecutar repairs §2.3 |
| Admin scoped a EMP001 | `repair_admin_tenant_tenant_wide.py --apply` |
| MANAGER menú vacío | `repair_manager_standard.py --apply` |
| USER menú vacío / 403 branding | `repair_user_standard.py` + `repair_base_operative.py` |
| Platform sin ADMIN_PLATFORM grants | `repair_platform_rbac.py --apply` |

**No breaking API:** endpoints existentes sin cambio de contrato en fases M1–T3.

---

## 9. Criterios congelación RBAC_V1_STABLE

Checklist previo a tag/commit stable:

- [x] M1, M4, T1, T2, T3 validados con evidencia JSON
- [x] `RBAC_V1_FINAL.md` aprobado
- [x] `BOOTSTRAP_SYSTEM_AUDIT.md` generado
- [x] `CHANGELOG_RBAC_V1.md` generado
- [ ] Revisión usuario de ambos documentos
- [ ] Commit + tag `RBAC_V1_STABLE` (pendiente autorización)
- [ ] Smoke final en staging post-congelación

---

## 10. Fuera de alcance RBAC V1

No incluido en esta versión (no desarrollar sin nueva fase):

- M2 / M3 multiempresa (DDL UQ, multi-rol multi-empresa)
- MenuPermissionBinder wiring startup
- Bundles para módulos futuros (SLS, FIN, …) en MANAGER/USER
- Deprecación física scripts SQL legacy
- Migraciones Flyway/Alembic automatizadas
- Cambios frontend PermissionGuard

---

**Fin CHANGELOG RBAC V1**
