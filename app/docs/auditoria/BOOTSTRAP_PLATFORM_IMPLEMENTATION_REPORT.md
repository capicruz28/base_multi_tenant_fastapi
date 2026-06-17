# Bootstrap plataforma — Informe de implementación

**Fecha:** 2026-06-08  
**Plan base:** [`BOOTSTRAP_PLATFORM_IMPLEMENTATION_PLAN.md`](BOOTSTRAP_PLATFORM_IMPLEMENTATION_PLAN.md) §13  
**Estado:** Implementado

---

## Resumen

Se reemplazó el flujo manual **D010 bloques A–E + `repair_platform_rbac.py`** por el CLI oficial **`scripts/bootstrap_platform.py`**, con identidad idempotente (`uuid4()` para rol/usuario) y RBAC vía `PlatformRbacBootstrapService` existente.

---

## Archivos creados

| Archivo | Propósito |
|---------|-----------|
| `app/modules/tenant/application/services/platform_bootstrap_constants.py` | Defaults semánticos (desacoplados de D010) |
| `app/modules/tenant/application/services/platform_identity_bootstrap_service.py` | Bootstrap identidad A–E idempotente |
| `app/modules/tenant/application/services/platform_bootstrap_audit.py` | Snapshot audit compartido |
| `app/modules/tenant/application/services/platform_bootstrap_service.py` | Orquestador transaccional |
| `scripts/bootstrap_platform.py` | CLI oficial (`--audit-only`, `--dry-run`, `--apply`, `--rbac-only`) |
| `tests/unit/test_platform_identity_bootstrap.py` | Tests identidad (mocks) |
| `tests/unit/test_platform_bootstrap_audit.py` | Tests flags `needs_*` |
| `tests/unit/test_platform_bootstrap_orchestrator.py` | Tests orden fases |

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `app/core/config.py` | `PLATFORM_BOOTSTRAP_INITIAL_PASSWORD`, `PLATFORM_BOOTSTRAP_CONTACT_EMAIL`, `PLATFORM_BOOTSTRAP_RAZON_SOCIAL` |
| `.env.docker` | Variables bootstrap documentadas |
| `.env.example` | Mismas variables + comentarios |
| `app/modules/tenant/application/services/platform_rbac_bootstrap_service.py` | Mensaje error → `bootstrap_platform.py` |
| `scripts/repair_platform_rbac.py` | Deprecación fase 1; delega en orquestador `--rbac-only` |
| `app/docs/PLATFORM_FIRST_BOOT.md` | Obsoleto; redirige a nuevo flujo |
| `app/docs/DEPLOYMENT_FIRST_INSTALL_GUIDE.md` | Fase 4 → `bootstrap_platform.py` |
| `app/bootstrap_v2/00_manifest/PLATFORM_RBAC_GAP_FIX.md` | Nota superseded |

### Sin modificar (confirmado)

- `scripts/bootstrap_v2_sql_apply.ps1`
- Startup FastAPI / `permission_sync` / onboarding tenant
- `ClienteOnboardingService`, scripts SQL `bootstrap_v2/`, `D010__seed_bd_central.sql`

---

## Resultado de tests unitarios

```
tests/unit/test_platform_identity_bootstrap.py .... 4 passed
tests/unit/test_platform_bootstrap_audit.py ........ 2 passed
tests/unit/test_platform_bootstrap_orchestrator.py . 3 passed
────────────────────────────────────────────────────────────
TOTAL: 9 passed
```

---

## Resultado instalación limpia

| Paso | Resultado | Notas |
|------|-----------|-------|
| `DROP/CREATE DATABASE bd_sistema_saas` | **PASS** | BD vacía |
| `bootstrap_v2_sql_apply.ps1` (V010→V030, S010→S030) | **PASS** | `sqlcmd` localhost / `bd_sistema_saas` |
| `docker compose up -d` | **SKIP** | Docker Desktop daemon no disponible en sesión de validación |
| `permission_sync` (equivalente: `run_rbac_startup(app)`) | **PASS** | Ejecutado vía import `app.main` |
| `bootstrap_platform.py --apply` | **PASS** | Identidad creada; RBAC parcial sin catálogo sync |
| `bootstrap_platform.py --rbac-only` (post-sync) | **PASS** | 22 `rol_permiso`, `tenant.cliente.crear` OK |
| Re-ejecución `--apply` (password distinta en env) | **PASS** | `success: true`, sin recrear entidades |

**Comando oficial Docker (documentado, no ejecutado en esta sesión):**

```powershell
docker exec -w /app -e PYTHONPATH=/app `
  -e PLATFORM_BOOTSTRAP_INITIAL_PASSWORD='admin123' `
  fastapi_backend python scripts/bootstrap_platform.py --apply
```

**Orden operativo validado:** `bootstrap_v2_sql` → **startup/permission_sync** → `bootstrap_platform --apply` (o `--rbac-only` si identidad ya existe).

---

## Resultado smoke test

```text
scripts/http_smoke_platform_rbac.py --base-url http://127.0.0.1:8000
passed: true
login: 200 (has_access)
auth_me: platform_admin
auth_menu: modulos_count=1
permissions_me: admin.platform.access, tenant.cliente.crear OK
```

Contraseña usada: `admin123` (`PLATFORM_BOOTSTRAP_INITIAL_PASSWORD`).

---

## Riesgos encontrados

| # | Riesgo | Severidad | Estado |
|---|--------|-----------|--------|
| R1 | Docker daemon apagado impide validar `docker exec` canónico | Media | Documentado; validación local equivalente |
| R3 | `--apply` antes de `permission_sync` deja RBAC incompleto (`rp_count<5`) | Alta | **Esperado** — plan §10 R3; requiere startup previo |
| R6 | `Unclosed connection` warning aioodbc al cerrar CLI | Baja | Cosmético; no afecta transacción |
| R13 | SQL inicial usaba columnas incorrectas (`es_sistema`, `hash_contrasena`) | Alta | **Corregido** — alineado a V020 (`es_rol_sistema`, `contrasena`, `correo`) |

---

## Cambios respecto al plan original

| Aspecto | Plan | Implementación |
|---------|------|----------------|
| Import password | `app.core.auth.password` | `app.core.security.password` (ruta real del proyecto) |
| INSERT `rol` / `usuario` | Equivalencia D010 genérica | Alineado a esquema **V020** y patrones `ClienteOnboardingService` |
| `cliente_auth_config` | IF NOT EXISTS | Mismo patrón onboarding: `INSERT (cliente_id)` condicional |
| Validación E2E Docker | `docker compose up -d` | Sustituido por uvicorn local + `run_rbac_startup` (mismo efecto permission_sync) |
| Desviación SQL schema | No prevista en plan | Corregida en implementación; sin cambiar scripts SQL bootstrap_v2 |

---

## Veredicto

| Criterio | Cumple |
|----------|:------:|
| CLI explícito (`--audit-only`, `--apply`, `--rbac-only`) | ✅ |
| Idempotencia total (no recrea, no cambia password) | ✅ |
| `SUPERADMIN_CLIENTE_ID` fuente oficial cliente | ✅ |
| `uuid4()` rol/usuario | ✅ |
| Sustituye D010 A–E + repair | ✅ |
| Restricciones § obligatorias | ✅ |
| Tests unitarios nuevos | ✅ 9/9 |
| Smoke plataforma post-bootstrap | ✅ |

**Listo para uso operativo** siguiendo [`DEPLOYMENT_FIRST_INSTALL_GUIDE.md`](../DEPLOYMENT_FIRST_INSTALL_GUIDE.md) Fase 4.
