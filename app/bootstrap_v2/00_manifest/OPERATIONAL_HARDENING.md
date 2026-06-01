# Hardening operativo — RBAC runtime (post-RC)

## Monitoreo

| Señal | Acción |
|-------|--------|
| Log `[RBAC] Permission sync` ausente tras deploy | Verificar `RBAC_PERMISSION_SYNC_ENABLED` y arranque completo |
| `ONBOARDING_PERMISSO_CATALOG_EMPTY` en crear cliente | Arrancar app antes del primer onboarding |
| Tenants sin ORG en menú | Ejecutar `repair_legacy_tenant_rbac.py --audit-only` |

## Runbooks

1. **Tenant nuevo:** solo API + startup (sin R010/R020).
2. **Legacy incompleto:** `repair_legacy_tenant_rbac.py` (dry-run → apply).
3. **Recovery manual:** R010/R020/S040 en repo `bootstrap_v2` (deprecated, no pipeline).

## Backups antes de `--apply`

```sql
SELECT * INTO cliente_modulo_backup_YYYYMMDD FROM cliente_modulo;
SELECT * INTO rol_permiso_backup_YYYYMMDD FROM rol_permiso;
```

## Rollback

- Reparación solo **inserta** (`IF NOT EXISTS`); rollback = delete filas insertadas por `fecha_creacion` reciente o restore backup.
- No desactiva permisos legacy existentes.

## CI smoke (mínimo)

```bash
python scripts/run_rc_validation_pipeline.py --unit-only
```

## Smoke HTTP (staging, API en marcha)

```bash
# Reset credencial admin conocida
python scripts/staging_reset_tenant_admin.py --subdominio prueba --password admin123

# Smoke tenant
python scripts/http_smoke_tenant_rbac.py \
  --base-url http://localhost:8000 \
  --subdominio prueba --username admin --password admin123 \
  --json-out app/bootstrap_v2/00_manifest/evidence/smoke_prueba_last.json
```

Pipeline completo: `STAGING_VALIDATION_PIPELINE.md`
