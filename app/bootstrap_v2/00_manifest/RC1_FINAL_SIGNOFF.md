# RC1 — Sign-off final consolidado

**Fecha:** 2026-05-21  
**Base de datos:** `bd_sistema_saas`  
**API:** `http://localhost:8000` (Docker, `.env.docker`)  
**Veredicto:** **RC1 CERRADO — PASS consolidado**

---

## 1. Alcance validado (sin refactors nuevos)

| Capa | Estado | Evidencia |
|------|--------|-----------|
| Bootstrap SQL Fase A (V010–V030, S010–S030) | PASS (sesión previa BD vacía) | `RC_RUN_REPORT_bd_sistema_saas.md` |
| Startup + `permission_sync` | PASS | 414 permisos activos; `core.app.acceder` + `admin.platform.access` activos |
| Platform bootstrap (`repair_platform_rbac`) | PASS | 22 `rol_permiso` ADMIN_PLATFORM; SYS_ADMIN en `cliente_modulo` |
| Onboarding tenant + RBAC runtime | PASS | 2 módulos, 45 `rol_permiso` ADMIN |
| Minimal ERP tenant bootstrap | PASS | `org_empresa` EMP001 + vínculo admin automático |
| Smoke tenant HTTP | PASS | Ver §3 |
| Smoke platform HTTP | PASS | Ver §4 |
| Unit tests RC (22) | PASS | exit 0 |

---

## 2. Rerun ejecutado hoy

### 2.1 Pre-check

```
DB_DATABASE=bd_sistema_saas
GET /health → 200 healthy
permisos activos: 414
platform rol_permiso: 22
org_empresa (total BD): 2+
```

### 2.2 Pipeline

```bash
python scripts/run_rc_validation_pipeline.py --unit-only
# → 22 passed

python scripts/run_rc_validation_pipeline.py --full-staging --create-tenant
# → health OK, onboarding 201, smoke tenant PASS

python scripts/http_smoke_platform_rbac.py
# → smoke platform PASS
```

**Tenant de prueba RC1 final:** `smokerc69929718`  
**Evidencia JSON:** [`evidence/RC1_FINAL_CONSOLIDATED.json`](evidence/RC1_FINAL_CONSOLIDATED.json)

### 2.3 SQL post-onboarding (tenant nuevo)

| Métrica | Valor |
|---------|-------|
| `org_empresa` | 1 |
| `cliente_modulo` (ORG+SYS_ADMIN) | 2 |
| `rol_permiso` ADMIN_TENANT | 45 |
| `usuario.empresa_default_id` | set |

---

## 3. Smoke tenant — PASS

| Step | HTTP | OK |
|------|------|-----|
| login | 200 | ✓ |
| org_empresa listar | 200 (count=1) | ✓ |
| empresa_cambiar | 400 already active | ✓ |
| auth/me | 200 | ✓ |
| auth/menu | 200 | ✓ |
| refresh | 200 | ✓ |
| permissions/me | 200 — 45 permisos; `org.empresa.leer`, `core.app.acceder`; sin `tenant.cliente.crear` | ✓ |

---

## 4. Smoke platform — PASS

| Step | HTTP | OK |
|------|------|-----|
| login superadmin | 200 | ✓ |
| auth/me | 200 — `platform_admin` | ✓ |
| auth/menu | 200 — 1 módulo | ✓ |
| permissions/me | 200 — 414 códigos; `admin.platform.access`, `tenant.cliente.crear` | ✓ |
| refresh | 200 | ✓ |

Evidencia: [`evidence/smoke_platform_RC1_final.json`](evidence/smoke_platform_RC1_final.json)

---

## 5. Flujo extremo a extremo (oficial)

```text
BD vacía
  → bootstrap_v2_sql_apply (V010–S030, S010–S030)     [validado sesión RC]
  → D010 (USE bd_sistema_saas) + repair_platform_rbac
  → docker up + permission_sync
  → POST /clientes/ (onboarding)
       ├─ OnboardingRbacService (ORG, SYS_ADMIN, rol_permiso)
       └─ MinimalErpTenantBootstrap (org_empresa + admin link)
  → login tenant → JWT con empresa_id
  → /auth/me, /auth/menu, /permissions/me, /org/empresa  → 200
  → login platform (superadmin) → menú + permisos platform → 200
```

---

## 6. Capacidades declaradas RC1

| # | Capacidad | PASS |
|---|-----------|------|
| 1 | Bootstrap automático desde BD vacía | ✓ |
| 2 | Startup runtime (`permission_sync`) | ✓ |
| 3 | Onboarding tenant completamente funcional | ✓ |
| 4 | ERP mínimo operativo automático | ✓ |
| 5 | Platform admin funcional | ✓ |
| 6 | Tenants legacy reparables (scripts) | ✓ |
| 7 | Smoke PASS consolidado | ✓ |

---

## 7. Backlog no bloqueante (post-RC1)

| Item | Severidad | Notas |
|------|-----------|-------|
| D010 `USE bd_hybrid_sistema_central` hardcoded | Ops | Sustituir `USE` al aplicar en BD nueva |
| `repair_*` CLI: warning "Unclosed connection" | Cosmético | No afecta commit |
| 2 tenants legacy candidatos RBAC (`repair_legacy` audit) | Ops | techcorp/global u otros; no bloquea tenant nuevo |
| `cfg_codigo_secuencia` en onboarding (pre-existente) | Doc | Fuera de “minimal ERP”; no ampliar en RC1 |
| Warnings endpoints sin `@RequirePermission` | Bajo | Backlog seguridad documental |
| Impersonación + Origin en dev local | Bajo | Validar en staging FE |
| Parametrizar D010 en manifest (sin `USE` fijo) | Mejora | RC2 |
| Sucursal / almacén / plan contable auto | RC2+ | Explícitamente fuera de RC1 |

**Ningún item bloquea cierre RC1.**

---

## 8. Congelación arquitectura

A partir de este sign-off:

- **No** refactors RBAC/auth/JWT/onboarding_rbac
- **Solo** P0: bugs críticos, seguridad, corrupción permisos, inconsistencias multiempresa
- Scripts legacy y SQL deprecated **permanecen** en repo

---

## 9. Referencias

| Documento |
|-----------|
| `FINAL_RUNTIME_STATE.md` |
| `RC_RUN_REPORT_bd_sistema_saas.md` |
| `PLATFORM_RBAC_GAP_FIX.md` |
| `MINIMAL_ERP_TENANT_BOOTSTRAP_AUDIT.md` |
| `STAGING_VALIDATION_PIPELINE.md` |
| `RELEASE_CANDIDATE_CHECKLIST.md` |

---

**Firmado por validación automatizada:** pipeline + smoke HTTP + SQL — **RC1 COMPLETAMENTE CERRADO.**
