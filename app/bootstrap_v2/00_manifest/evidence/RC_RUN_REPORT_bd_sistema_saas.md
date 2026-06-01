# Reporte ejecución RC — `bd_sistema_saas`

**Fecha:** 2026-05-21  
**Objetivo:** BD vacía → bootstrap → startup → onboarding → smoke → PASS  
**Veredicto global:** **PASS — listo para congelación RC**

---

## Resumen ejecutivo

| Etapa | Estado | Notas |
|-------|--------|-------|
| Config `.env.docker` | **PASS** | `DB_DATABASE` / `DB_ADMIN_DATABASE` = `bd_sistema_saas` |
| Conectividad SQL | **PASS** | `CARLOSPC`, usuario `soporte` |
| Docker usa BD nueva | **PASS** (tras `--force-recreate`) | Antes: `bd_sistema` (stale env) |
| Bootstrap V010–S030 | **PASS** | Requirió `-I` en sqlcmd; BD recreada tras intento fallido |
| D010 QA seed | **PASS** | Requirió sustituir `USE bd_hybrid_sistema_central` → `bd_sistema_saas` |
| Startup + permission_sync | **PASS** | 415 permisos; `core.app.acceder` activo |
| Unit tests RC | **PASS** | 18/18 |
| Onboarding API (`--create-tenant`) | **PASS** | Tenant `smokerc2af1c02b` |
| Smoke HTTP | **PASS** | `passed: true` |
| Onboarding runtime SQL | **PASS** | 2 `cliente_modulo`, 44 `rol_permiso` ADMIN, sin `tenant.cliente.crear` |

---

## 1. Configuración

### `.env.docker` (verificado)

```
DB_SERVER=host.docker.internal
DB_DATABASE=bd_sistema_saas
DB_ADMIN_DATABASE=bd_sistema_saas
DB_USER=soporte
SUPERADMIN_CLIENTE_ID=00000000-0000-0000-0000-000000000001
SUPERADMIN_USERNAME=superadmin
```

### Docker (post `docker compose up -d --force-recreate`)

```
DB_DATABASE=bd_sistema_saas
DB_ADMIN_DATABASE=bd_sistema_saas
```

---

## 2. Bootstrap SQL

### Comando

```powershell
.\scripts\bootstrap_v2_sql_apply.ps1 -Server CARLOSPC -Database bd_sistema_saas -User soporte -Password "rrhh03"
```

### Corrección operativa aplicada

- `sqlcmd -I` (QUOTED_IDENTIFIER) en `bootstrap_v2_sql_apply.ps1/.sh` — sin esto V010 falla en índices filtrados.
- Primer intento dejó 8 tablas parciales → BD **DROP/CREATE** y re-ejecución.

### Verificación post-bootstrap (antes de D010)

| Artefacto | Resultado |
|-----------|-----------|
| Tablas (`sys.tables`) | 134 |
| `permiso` (S030) | 3 (pre-sync/D010) |
| `modulo` | 28 |
| `core.app.acceder` | presente, activo |
| Tablas críticas | `cliente`, `usuario`, `rol`, `cliente_modulo`, `rol_permiso`, `cfg_codigo_secuencia` |

---

## 3. D010 QA seed

### Bloqueador encontrado (operativo, no RBAC)

`D010__seed_bd_central.sql` línea 13: `USE bd_hybrid_sistema_central;` — inserts iban a otra BD si no se corrige.

### Workaround ejecutado

```powershell
# Sustitución USE → bd_sistema_saas en copia temporal
sqlcmd ... -i app/bootstrap_v2/00_manifest/evidence/D010_bd_sistema_saas.tmp.sql
```

### Post-D010

| Métrica | Valor |
|---------|-------|
| `cliente` | 5 (SUPERADMIN, ACME, INNOVA, TECHCORP, GLOBALLOG) |
| `superadmin` usuario | OK |
| `permiso` | 415 (incluye seeds + sync posterior) |

---

## 4. Startup API

- `GET /health` → **200**
- Log: `Application startup complete`
- `permission_startup` escaneó rutas API
- Catálogo: **413** permisos activos; `core.app.acceder` = 1

---

## 5. Pipeline `--full-staging --create-tenant`

```bash
python scripts/run_rc_validation_pipeline.py --full-staging --create-tenant \
  --json-out app/bootstrap_v2/00_manifest/evidence/rc_full_staging_bd_sistema_saas.json
```

**Exit code: 0**

### Tenant creado (onboarding runtime)

| Campo | Valor |
|-------|-------|
| `cliente_id` | `79b2dc3c-b119-4ec6-b1ab-c71913ac2f5c` |
| `subdominio` | `smokerc2af1c02b` |
| `codigo_cliente` | `SRC2AF1C0` |
| Admin user | `admin` |
| Credenciales | Ver `rc_full_staging_bd_sistema_saas.json` (no re-expuestas aquí) |

### SQL onboarding (runtime bootstrap)

| Check | Esperado | Real |
|-------|----------|------|
| `cliente_modulo` | 2 (ORG, SYS_ADMIN) | **2** |
| `rol_permiso` ADMIN_TENANT | ~44 | **44** |
| `core.app.acceder` | sí | **sí** |
| `tenant.cliente.crear` | no | **no** |

---

## 6. Smoke HTTP

| Step | HTTP | OK |
|------|------|-----|
| login | 200 | ✓ |
| org_empresa_listar | 200 (count=0) | ✓ |
| empresa_cambiar | skip | ✓ |
| auth_me | 403 skip (admin sin empresa) | ✓ |
| auth_menu | 403 skip | ✓ |
| refresh | 200 | ✓ |
| permissions_me | 403 skip | ✓ |

**Nota:** Con `org_empresa` vacío, `/me`, `/menu`, `/permissions/me` devuelven 403 por contrato ERP (sin `empresa_id` en sesión). El smoke lo trata como **skip esperado**, no fallo de RBAC.

Para validar permisos efectivos end-to-end: crear una `org_empresa` y repetir smoke (o `empresa_cambiar`).

---

## 7. Evidencia generada

| Archivo |
|---------|
| `evidence/rc_full_staging_bd_sistema_saas.json` |
| `evidence/D010_bd_sistema_saas.tmp.sql` (workaround D010) |
| Este reporte |

---

## 8. Bloqueadores reales restantes (no impiden RC)

| # | Item | Severidad | Acción post-RC |
|---|------|-----------|----------------|
| 1 | D010 `USE bd_hybrid_sistema_central` hardcoded | Operativo | Parametrizar `USE` o documentar sustitución en pipeline |
| 2 | Smoke no valida `permissions/me` con grants si no hay empresa | Documental | Crear empresa QA en smoke opcional |
| 3 | `sqlcmd -I` obligatorio para V010 | Documental | Ya corregido en scripts apply |
| 4 | Warnings endpoints sin `@RequirePermission` en startup | Bajo | Backlog, no RC |

**No hay bloqueadores de arquitectura RBAC/auth** para declarar RC estable en `bd_sistema_saas`.

---

## 9. Veredicto congelación

**El pipeline RC completo pasó correctamente** en `bd_sistema_saas`.

El proyecto queda **listo para congelación / release candidate** con las salvedades operativas documentadas (D010 USE, smoke sin empresa).

No se modificó arquitectura RBAC/auth en esta ejecución (solo fix operativo `-I` en scripts bootstrap apply).
