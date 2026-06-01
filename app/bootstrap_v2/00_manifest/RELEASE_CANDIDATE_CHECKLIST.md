# Release candidate checklist — RBAC runtime bootstrap

**Estado base aceptado:** onboarding runtime, login tenant nuevo, permission sync, RBAC runtime, multiempresa, menú, refresh.

Scripts **R010, R020, S030, S040–S066** permanecen en repo como **deprecated / recovery** (no eliminar).

---

## Pre-deploy

- [ ] `RBAC_PERMISSION_SYNC_ENABLED=true` en entorno destino
- [ ] App arrancada ≥1 vez (`permiso` activos > 0, `core.app.acceder` presente)
- [ ] Catálogo módulos S010/S020 aplicado (`modulo` con ORG, SYS_ADMIN)
- [ ] V020/V030 schema OK en BD central

## Legacy repair (antes o justo después del deploy)

- [ ] `python scripts/repair_legacy_tenant_rbac.py --audit-only` → revisar candidatos
- [ ] `--dry-run` en staging → validar reporte before/after simulado
- [ ] `--apply` solo en ventana acordada (backup `cliente_modulo`, `rol_permiso`)
- [ ] Smoke login + menú en tenant reparado (`prueba`, `techcorp`, `global`)

## Smoke automatizado (CI / local)

- [ ] `python scripts/run_rc_validation_pipeline.py --unit-only` (CI job `rc-validation`)
- [ ] Staging: `STAGING_VALIDATION_PIPELINE.md` (BD → startup → onboarding → smoke)
- [ ] `python scripts/staging_reset_tenant_admin.py --subdominio <tenant> --password admin123`
- [ ] `python scripts/http_smoke_tenant_rbac.py` → JSON `passed: true`
- [ ] (Opcional) `pytest tests/smoke/ -m smoke` con `SMOKE_*` env

## Post-deploy tenant nuevo

- [ ] `POST /clientes/` → credenciales + sin ejecutar R010/R020
- [ ] SQL: 2 `cliente_modulo` (ORG, SYS_ADMIN), N `rol_permiso` ADMIN
- [ ] Login admin → 200, sin `tenant.cliente.crear` en grants runtime

## Operativo / hardening

- [ ] Runbook: `LEGACY_TENANT_REPAIR_PLAN.md` + script `repair_legacy_tenant_rbac.py`
- [ ] Monitoreo: logs `[RBAC] Permission sync` al startup
- [ ] Alerta si `ONBOARDING_PERMISSO_CATALOG_EMPTY` en onboarding
- [ ] Documentar que R010/R020 son fallback manual, no pipeline tenant nuevo

## No hacer en RC1

- [ ] No eliminar scripts bootstrap legacy
- [ ] No MenuPermissionBinder masivo
- [ ] No refactor auth/RBAC salvo P0
