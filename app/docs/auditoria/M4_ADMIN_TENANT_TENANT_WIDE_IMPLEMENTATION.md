# M4 — ADMIN_TENANT tenant-wide (Modelo B)

**Referencia:** [ADMIN_TENANT_SCOPE_MODEL.md](./ADMIN_TENANT_SCOPE_MODEL.md)  
**Fecha:** 2026-05-31  
**Alcance:** Alinear `ADMIN_TENANT` con Modelo B — `usuario_rol.empresa_id IS NULL`.

---

## 1. Análisis de impacto (pre-implementación)

### 1.1 Problema resuelto

| Antes (Modelo A híbrido) | Después (Modelo B) |
|--------------------------|-------------------|
| Onboarding: `usuario_rol.empresa_id = EMP001` | `usuario_rol.empresa_id = NULL` |
| Admin crea EMP002 → sin acceso selector | Elegibles = todas `org_empresa` |
| Cambiar sesión → riesgo L-07 (pérdida `tenant_admin`) | ADMIN siempre en filtro `(NULL OR sesión)` |

### 1.2 Componentes tocados vs intactos

| Componente | Cambio |
|------------|--------|
| `ClienteOnboardingService._insertar_usuario_admin` | ✅ INSERT `usuario_rol` con `NULL` |
| `MinimalErpTenantBootstrapService.vincular_admin_empresa` | ✅ Solo preferida + UR NULL |
| `scripts/repair_admin_tenant_tenant_wide.py` | ✅ Nuevo — migración idempotente |
| `scripts/repair_minimal_erp_tenant.py` | ✅ Audit `needs_repair` invertido para M4 |
| `AuthService.get_empresa_activa_para_login` | ❌ Sin cambio (ya soporta admin global M1) |
| `OwnerSyncService` / RoleGrantSync | ❌ Sin cambio |
| `MANAGER_TENANT` / `USER_TENANT` | ❌ Sin cambio |
| Platform admin | ❌ Sin cambio |
| Frontend | ❌ Sin cambio |
| Filtro ERP company-scoped | ❌ Sin cambio — JWT `empresa_id` obligatorio |

### 1.3 Seguridad confirmada

- **Datos ERP** (INV, sucursales, producción, etc.): siguen filtrando por `JWT empresa_id` + `assert_row_empresa`.
- **Permisos/menú admin**: grants del rol (tenant-wide); filtro `usuario_rol` incluye global NULL en cualquier sesión.
- **Assign operativos**: `resolve_role_assign_target` sin cambio — scoped por sesión.
- **No** se introducen bypass por `access_level`.

### 1.4 Riesgos residuales

| Riesgo | Mitigación |
|--------|------------|
| Tenants existentes scoped | Script repair `--apply` |
| `empresa_default_id` NULL post-migración | Repair minimal ERP o login Caso C |
| Auditoría “admin por empresa” | Ya no aplica — admin es del tenant |

---

## 2. Cambios implementados

### 2.1 Onboarding

```text
ensure_empresa_inicial → EMP001
_insertar_usuario_admin:
  usuario.empresa_default_id = EMP001   (preferencia M1)
  usuario_rol.empresa_id = NULL         (M4)
vincular_admin_empresa:
  refuerza default + UR NULL (idempotente)
```

### 2.2 Repair

```bash
# Dry-run (todos los tenants)
python scripts/repair_admin_tenant_tenant_wide.py --all

# Aplicar en un tenant
python scripts/repair_admin_tenant_tenant_wide.py --subdominio prueba --apply

# Evidencia JSON
python scripts/repair_admin_tenant_tenant_wide.py --all --apply \
  --output app/bootstrap_v2/00_manifest/evidence/M4_REPAIR_REPORT.json
```

**SQL efectivo:**

```sql
UPDATE usuario_rol SET empresa_id = NULL
WHERE usuario_rol_id IN (
  SELECT ur.usuario_rol_id FROM usuario_rol ur
  JOIN rol r ON r.rol_id = ur.rol_id
  WHERE r.codigo_rol = 'ADMIN_TENANT'
    AND ur.es_activo = 1
    AND ur.empresa_id IS NOT NULL
);
```

Solo `ADMIN_TENANT`. MANAGER/USER no afectados.

---

## 3. Validación

### 3.1 Tests unitarios

```bash
pytest tests/unit/test_m4_admin_tenant_wide.py \
       tests/unit/test_multiempresa_m1.py \
       tests/unit/test_empresa_sesion_auth.py \
       tests/unit/test_assign_role_empresa_scope.py -v
```

| Criterio | Test / mecanismo |
|----------|------------------|
| Onboarding UR NULL | `test_vincular_admin_empresa_sets_null_scope_m4` |
| Login admin multi-org | `test_admin_tenant_wide_login_elegibles_from_org` |
| Login admin 1 org | `test_admin_tenant_wide_single_org_direct_session` |
| Compat M1 seleccionar/cambiar | `test_multiempresa_m1.py` |
| MANAGER assign scoped | `test_assign_role_empresa_scope.py` |
| Filtro RBAC global | `test_sql_empresa_filter_includes_global_roles` |

### 3.2 Validación HTTP (staging)

Reutilizar patrón `scripts/run_m1_m2_staging_integration.py` tras repair:

1. Tenant nuevo → login admin → `GET /auth/me`, `/auth/menu`, `/permissions/me`
2. Tenant migrado → crear EMP002 → selector incluye ambas
3. `POST /auth/empresa/cambiar` → refresh mantiene contexto

---

## 4. Reglas R-ADMIN aplicadas

| ID | Estado |
|----|--------|
| R-ADMIN-01 | ✅ Admin = tenant |
| R-ADMIN-02 | ✅ UR NULL en onboarding + repair |
| R-ADMIN-03 | ✅ OwnerSync sin cambio |
| R-ADMIN-04 | ✅ Sesión ERP company-scoped |
| R-ADMIN-05 | ✅ ORG tenant-wide sin assign extra |
| R-ADMIN-06 | ✅ MANAGER/USER scoped |
| R-ADMIN-08 | ✅ `empresa_default_id` = preferencia |

---

## 5. Archivos modificados

| Archivo | Acción |
|---------|--------|
| `cliente_onboarding_service.py` | INSERT UR NULL |
| `minimal_erp_tenant_bootstrap_service.py` | vincular tenant-wide |
| `scripts/repair_admin_tenant_tenant_wide.py` | Nuevo |
| `scripts/repair_minimal_erp_tenant.py` | Audit M4 |
| `tests/unit/test_m4_admin_tenant_wide.py` | Nuevo |

Evidencia: `app/bootstrap_v2/00_manifest/evidence/M4_ADMIN_TENANT_TENANT_WIDE_VALIDATION.json`
