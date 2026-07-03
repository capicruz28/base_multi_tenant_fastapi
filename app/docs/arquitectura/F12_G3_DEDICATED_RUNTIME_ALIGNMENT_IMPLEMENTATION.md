# F12-G3 — Dedicated Runtime Alignment Implementation

**Fecha:** 2026-06-28  
**Referencias:** [F12-G1](./F12_G1_DEDICATED_DDL_ROOT_CAUSE.md), [F12-G2](./F12_G2_DEDICATED_RUNTIME_DDL_ALIGNMENT.md)  
**Estado:** Implementado

---

## 1. Resumen ejecutivo

Se alineó el catálogo oficial **`dedicated_schema_v2` (manifiesto v2.1.0)** con el runtime vigente incorporando **`auth_audit_log`** al pipeline automático de onboarding Dedicated y ampliando el gate post-bootstrap a **`DEDICATED_RUNTIME_REQUIRED_TABLES`**.

Tras esta implementación, un tenant Dedicated recién provisionado recibe la tabla de auditoría auth **sin scripts manuales**. El onboarding no puede declarar bootstrap completo si faltan tablas runtime obligatorias.

**No se modificaron:** Frontend, RBAC, IAM, PermissionResolver, MenuResolver, runtime Auth, Session Store, Dispatcher, Saga, OpenAPI.

---

## 2. Cambios realizados

### 2.1 Nuevo script DDL Dedicated

| Artefacto | Ruta |
|-----------|------|
| DDL | `app/bootstrap_v2/05_dedicated/V030__auth_audit_log_dedicated.sql` |
| Script code | `apply_schema_auth_audit_v030` |
| Orden saga | 4 (tras ERP + DTSP + `rol_permiso`) |

Características:

- Paridad columnas con `V020__tablas_bd_central.sql` §auth_audit_log
- **Sin FK → `cliente`** (Control Plane ausente en DP)
- FK → `usuario`, `org_empresa` (prerequisitos DTSP + V010 ERP)
- Idempotente (`IF NOT EXISTS` tabla + índices)
- SHA256 congelado: `ad1fb3c6c28e26c5766282c09bbd498ce9b774e20a26ab07d350a7a2f91612a8`

### 2.2 Manifiesto (`script_manifest.py`)

- Versión manifiesto: **2.0.0 → 2.1.0** (perfil `dedicated_schema_v2` sin renombrar)
- Cuarta entrada: `apply_schema_auth_audit_v030`
- Nueva constante **`DEDICATED_RUNTIME_EXTRA_TABLES`**: `auth_audit_log`, `cfg_codigo_secuencia`, `org_empresa`
- Nueva constante **`DEDICATED_RUNTIME_REQUIRED_TABLES`**: DTSP (9) + `rol_permiso` + extras runtime

### 2.3 BootstrapScriptRunner

- `_verify_dtsp_schema` reemplazado por **`_verify_runtime_schema`**
- Valida **`DEDICATED_RUNTIME_REQUIRED_TABLES`** (13 tablas) antes de retornar éxito en perfil v2
- Código error: `PROVISIONING_SCHEMA_FAILED` (sin cambio)

### 2.4 Documentación oficial

| Documento | Cambio |
|-----------|--------|
| `BOOTSTRAP_ORDER.md` | Paso A2b + nota F12-G3 |
| `BOOTSTRAP_MANIFEST.md` | Inventario `V030` dedicated |
| `SOURCE_MAP.json` | Entrada `V030__auth_audit_log_dedicated.sql` |
| `DTSP_DEDICATED_TENANT_STORE_PROFILE.md` | v1.1.0 — runtime gate + audit store |

### 2.5 Tests

| Archivo | Cobertura |
|---------|-----------|
| `tests/unit/test_f12_g3_dedicated_runtime_alignment.py` | Manifiesto, checksum, runtime tables, exclusión session store |
| `tests/unit/test_f4_05b_dtsp_manifest.py` | 4 entradas manifiesto |
| `tests/unit/test_f4_05_bootstrap_script_runner.py` | Secuencia 4 scripts, idempotencia, gate runtime |

### 2.6 Script de validación Docker

| Script | Propósito |
|--------|-----------|
| `scripts/f12_g3_validate_dedicated_e2e.py` | BD efímera + bootstrap completo + probe tablas (no tenants legacy) |

---

## 3. Nuevo catálogo Dedicated (`dedicated_schema_v2` v2.1.0)

| Orden | Script code | Archivo | Tablas principales |
|------:|-------------|---------|-------------------|
| 1 | `apply_schema_erp_v010` | `01_schema/V010__tablas_bd_erp_completo.sql` | ~100 ERP incl. `org_empresa`, `cfg_codigo_secuencia` |
| 2 | `apply_schema_tenant_store_v020` | `05_dedicated/V020__tenant_identity_rbac_store.sql` | 9 tablas DTSP |
| 3 | `apply_schema_rbac_v010` | `05_dedicated/V010__rbac_tablas_dedicated.sql` | `rol_permiso` |
| 4 | `apply_schema_auth_audit_v030` | `05_dedicated/V030__auth_audit_log_dedicated.sql` | **`auth_audit_log`** |

**Total tablas DDL manifiesto:** 110 + `bootstrap_applied` (runtime).

---

## 4. Tablas runtime obligatorias (`DEDICATED_RUNTIME_REQUIRED_TABLES`)

Gate READY / post-bootstrap — **13 tablas**:

| Grupo | Tablas |
|-------|--------|
| DTSP | `modulo`, `modulo_seccion`, `modulo_menu`, `permiso`, `rol`, `usuario`, `usuario_rol`, `cliente_modulo`, `rol_menu_permiso` |
| RBAC grants | `rol_permiso` |
| ERP mínimo auth | `org_empresa`, `cfg_codigo_secuencia` |
| Audit tenant | **`auth_audit_log`** |

**Excluidas deliberadamente (Control Plane — ADR-002-A MVP):**

- `user_session`, `token_family`, `refresh_tokens`

---

## 5. Decisión arquitectónica: `log_sincronizacion_usuario`

### Veredicto: **B — Permanece Control Plane**

| Criterio | Evidencia |
|----------|-----------|
| Naturaleza del dominio | Sincronización **cross-tenant** entre instalaciones (origen/destino) |
| FK estructural | `cliente_origen_id`, `cliente_destino_id` → **`cliente(cliente_id)`** — tabla CP inexistente en DP |
| Uso runtime actual | **Cero callers** de `registrar_log_sincronizacion_usuario` fuera de `AuditService` |
| Flujos Dedicated hoy | No ejecutan sync cross-installation |
| Alternativa descartada (A) | Requeriría réplica DP **sin FK cliente** + enmienda routing — fuera de alcance F12-G3 |

**Implicación:** no se incorpora al manifiesto Dedicated. Cuando el producto active sync en Dedicated, la decisión será: routing explícito a CP **o** DDL DP adaptado (sin FK) en PR dedicado.

---

## 6. Validaciones ejecutadas

### 6.1 Unit tests

```text
pytest tests/unit/test_f12_g3_dedicated_runtime_alignment.py
     tests/unit/test_f4_05b_dtsp_manifest.py
     tests/unit/test_f4_05_bootstrap_script_runner.py
→ 30 passed
```

### 6.2 Docker — bootstrap autosuficiente (BD nueva, sin acce/acces/acmec)

Entorno: `fastapi_backend` + SQL Server host (`PROVISIONING_DDL_EXECUTOR_ENABLED=true`)

```text
python scripts/f12_g3_validate_dedicated_e2e.py

database=erp_f12g3_20260628043106_54704f
manifest=2.1.0
Bootstrap executed: (
  apply_schema_erp_v010,
  apply_schema_tenant_store_v020,
  apply_schema_rbac_v010,
  apply_schema_auth_audit_v030,
)
auth_audit_log exists: True
user_session / token_family / refresh_tokens in DP: False (esperado)
PASS all DEDICATED_RUNTIME_REQUIRED_TABLES present
```

### 6.3 Checklist funcional post-onboarding completo (S1–S10)

| Verificación | Estado | Notas |
|--------------|--------|-------|
| Bootstrap completo 4 scripts | ✅ | Validado Docker |
| Gate runtime 13 tablas | ✅ | `_verify_runtime_schema` |
| `auth_audit_log` en DP | ✅ | Probe SQL |
| Session store **no** en DP | ✅ | ADR-002-A preservado |
| Login / Refresh / Logout / auth/me | ⚠️ Requiere saga S6–S10 | Seeds + usuario admin vía onboarding API; bootstrap S4–S5 validado |
| Auditoría auth persiste | ✅ Diseño | `AuditService` → DP; tabla ahora existe post-bootstrap |

> **Nota operativa:** tenants Dedicated creados **antes** de F12-G3 (p. ej. `acces`, `acmec`) carecen de `auth_audit_log` hasta reprovision/repair DDL. Tenants nuevos post-deploy reciben la tabla automáticamente.

---

## 7. Riesgos residuales

| ID | Riesgo | Mitigación |
|----|--------|------------|
| R-G3-01 | Tenants legacy sin `auth_audit_log` | Utility repair / reprovision documentada (F12-F); no automático |
| R-G3-02 | Manifiesto checksum drift | CI `validate_manifest_integrity` + tests F12-G3 |
| R-G3-03 | `log_sincronizacion` invocado futuro en DP sin tabla | Decisión B documentada; PR routing/DDL cuando exista feature |
| R-G3-04 | Session-in-DP post-MVP | Fuera alcance; perfil v3 futuro (BL-PEND-04) |

---

## 8. Archivos modificados / creados

**Creados:**

- `app/bootstrap_v2/05_dedicated/V030__auth_audit_log_dedicated.sql`
- `tests/unit/test_f12_g3_dedicated_runtime_alignment.py`
- `scripts/f12_g3_validate_dedicated_e2e.py`
- `app/docs/arquitectura/F12_G3_DEDICATED_RUNTIME_ALIGNMENT_IMPLEMENTATION.md`

**Modificados:**

- `app/infrastructure/provisioning/script_manifest.py`
- `app/infrastructure/provisioning/bootstrap_script_runner.py`
- `app/bootstrap_v2/00_manifest/BOOTSTRAP_ORDER.md`
- `app/bootstrap_v2/00_manifest/BOOTSTRAP_MANIFEST.md`
- `app/bootstrap_v2/00_manifest/SOURCE_MAP.json`
- `app/docs/arquitectura/hybrid-platform/provisioning/DTSP_DEDICATED_TENANT_STORE_PROFILE.md`
- `tests/unit/test_f4_05b_dtsp_manifest.py`
- `tests/unit/test_f4_05_bootstrap_script_runner.py`

---

## 9. Veredicto final

| Pregunta | Respuesta |
|----------|-----------|
| ¿Onboarding Dedicated autosuficiente para audit auth? | **Sí** — post F12-G3 |
| ¿Gate READY exige runtime completo? | **Sí** — 13 tablas |
| ¿Session store en DP? | **No** — sin cambio ADR-002-A |
| ¿`log_sincronizacion_usuario` en DP? | **No** — CP by design |
| ¿Pasos manuales post-bootstrap? | **No** para `auth_audit_log` en tenants nuevos |

**Resultado:** `dedicated_schema_v2` v2.1.0 representa el conjunto mínimo correcto de tablas DP para el runtime actual (ERP + DTSP + audit tenant), alineado con BL-1.0 RD-07.
