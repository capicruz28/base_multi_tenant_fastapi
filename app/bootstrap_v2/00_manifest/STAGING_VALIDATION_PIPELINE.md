# Pipeline de validación staging — Release Candidate

**Objetivo:** `BD vacía → bootstrap SQL → startup (permission_sync) → onboarding → smoke HTTP → PASS`

Sin refactors RBAC/auth. Legacy SQL y fallback jobs **permanecen** en repo.

---

## Fase A — BD vacía (schema + catálogo)

Ejecutar en orden (`BOOTSTRAP_ORDER.md`):

| # | Script |
|---|--------|
| 1 | `01_schema/V010__tablas_bd_erp_completo.sql` |
| 2 | `01_schema/V020__tablas_bd_central.sql` |
| 3 | `01_schema/V030__rbac_tablas_central.sql` |
| 4 | `02_catalog/S010__seed_modulo_menu_completo.sql` |
| 5 | `02_catalog/S020__seed_admin_menu.sql` |
| 6 | `02_catalog/S030__seed_permisos_core.sql` |

**No ejecutar en tenants nuevos:** R010, R020, S040–S066.

Opcional QA (solo dev): `04_qa/D010__seed_bd_central.sql` (superadmin `admin` / `admin123`).

Helper (si `sqlcmd` disponible):

```powershell
.\scripts\bootstrap_v2_sql_apply.ps1 -Server localhost -Database bd_sistema -User sa -Password '<pwd>'
```

```bash
./scripts/bootstrap_v2_sql_apply.sh localhost bd_sistema_saas soporte '<pwd>'
```

Los scripts usan `sqlcmd -I` (QUOTED_IDENTIFIER requerido por V010).

---

## Fase B — Startup app

```bash
docker compose up -d   # o uvicorn local
```

Verificar:

- `GET http://localhost:8000/health` → 200
- Log `[RBAC] Permission sync` (catálogo `permiso` > 0)

---

## Fase C — QA plataforma (D010 + repair platform)

**Importante — D010:** el archivo `04_qa/D010__seed_bd_central.sql` contiene `USE bd_hybrid_sistema_central;`. Para `bd_sistema_saas`, sustituir `USE` antes de ejecutar (ver `RC_RUN_REPORT_bd_sistema_saas.md`).

Tras D010 y startup, **obligatorio** para menú/permisos platform:

```bash
python scripts/repair_platform_rbac.py --apply
python scripts/http_smoke_platform_rbac.py
```

Ver `PLATFORM_RBAC_GAP_FIX.md`.

## Fase D — Onboarding tenant (+ ERP mínimo)

Tras crear tenant, el onboarding incluye automáticamente:

- `org_empresa` inicial (`EMP001`)
- `usuario.empresa_default_id` + `usuario_rol.empresa_id` + `es_empresa_default=1`

Tenants legacy sin empresa:

```bash
python scripts/repair_minimal_erp_tenant.py --subdominio <tenant> --apply
```

Ver `MINIMAL_ERP_TENANT_BOOTSTRAP_AUDIT.md`.

**Opción 1 — API (recomendado, runtime oficial):**

```bash
python scripts/run_rc_validation_pipeline.py --full-staging --create-tenant --json-out app/bootstrap_v2/00_manifest/evidence/smoke_onboarding_last.json
```

Crea tenant `smokerc*` y ejecuta smoke con credenciales devueltas en la respuesta.

**Opción 2 — Manual:** `POST /api/v1/clientes/` con token superadmin (`Origin: http://platform.app.local:5173`).

---

## Fase E — Smoke HTTP tenant (sesión con empresa)

### Reset admin (staging / tenant legacy)

```bash
python scripts/staging_reset_tenant_admin.py --subdominio prueba --password admin123
```

### Smoke solo HTTP

```bash
export SMOKE_BASE_URL=http://localhost:8000
export SMOKE_SUBDOMINIO=prueba
export SMOKE_USERNAME=admin
export SMOKE_PASSWORD=admin123

python scripts/http_smoke_tenant_rbac.py --json-out app/bootstrap_v2/00_manifest/evidence/smoke_prueba_last.json
```

Pasos validados: login, org.empresa listar, empresa cambiar/seleccionar (si hay empresas), `/auth/me`, `/auth/menu`, refresh, `permissions/me` (checks `org.empresa.leer`, `core.app.acceder`, ausencia `tenant.cliente.crear`).

**Nota:** admin sin empresa en BD → menu/permissions pueden devolver 403/409; el smoke lo marca como **skip esperado** hasta crear/seleccionar empresa.

---

## Fase F — Pipeline mínimo (local / CI)

| Comando | Alcance |
|---------|---------|
| `python scripts/run_rc_validation_pipeline.py --unit-only` | pytest RC (siempre) |
| `python scripts/run_rc_validation_pipeline.py --http-smoke --subdominio X --password Y` | smoke HTTP |
| `python scripts/run_rc_validation_pipeline.py --full-staging --create-tenant` | unit + health + onboarding + smoke |
| `pytest tests/smoke/ -m smoke` | smoke vía env `SMOKE_*` |

### CI (GitHub Actions)

Job `rc-validation`: unit tests obligatorios. Smoke HTTP **no** en CI por defecto (requiere SQL Server + API).

---

## Criterio PASS

1. `pytest` unitarios RC → exit 0  
2. Health API → 200  
3. Onboarding tenant nuevo → 201 + credenciales  
4. Smoke HTTP → `"passed": true` en JSON  

Evidencia: guardar JSON en `app/bootstrap_v2/00_manifest/evidence/`.

---

## Referencias

- `FINAL_RUNTIME_STATE.md` — arquitectura congelada RC  
- `RELEASE_CANDIDATE_CHECKLIST.md`  
- `OPERATIONAL_HARDENING.md`  
- `RUNTIME_BOOTSTRAP_FLOW.md`
