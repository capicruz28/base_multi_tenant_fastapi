# F12-G1 — Dedicated DDL Root Cause Audit

**Fecha:** 2026-06-28  
**Modo:** Solo auditoría — sin correcciones, sin DDL, sin cambios de código  
**Pregunta:** ¿Por qué un tenant Dedicated recién provisionado no contiene `auth_audit_log` si el onboarding Dedicated se declaró funcional?

---

## 1. Conclusión (causa raíz)

**`auth_audit_log` no falta por un fallo de ejecución del pipeline F4.** Falta porque **no forma parte del catálogo DDL oficial del Data Plane Dedicated** (`dedicated_schema_v2` / perfil DTSP).

El onboarding Dedicated se considera “completo” cuando la saga S1–S10 crea la BD, aplica el manifiesto registrado (3 scripts), valida **solo** las tablas DTSP + `rol_permiso`, ejecuta seeds S6–S7 y marca el tenant READY. Esa verificación **no incluye** `auth_audit_log`.

Existe una **desalineación arquitectónica** entre:

| Capa | Expectativa sobre `auth_audit_log` en Dedicated |
|------|--------------------------------------------------|
| **Catálogo provisioning oficial (F4-05b / DTSP)** | **No incluida** — subset deliberado de identidad/RBAC/menú |
| **Runtime (`audit_service`)** | **Sí incluida** — insert en BD tenant cuando `database_type == "multi"` |
| **Legacy referencial (`TABLAS_BD_DEDICADA.sql`)** | **Sí incluida** — documento histórico **no cableado** al manifiesto v2 |
| **Shared CP (`V020__tablas_bd_central.sql`)** | **Sí incluida** — bootstrap central, **no ejecutado** en BD dedicada |

**Causa raíz:** omisión **por diseño del catálogo DTSP**, no por script omitido/erróneo en runtime. El onboarding reporta éxito porque su gate de integridad schema **no exige** paridad con tablas auth/audit del plano Shared.

---

## 2. Dónde se define oficialmente `auth_audit_log`

| Fuente | Ruta | Rol |
|--------|------|-----|
| Bootstrap Shared (canónico v2) | `app/bootstrap_v2/01_schema/V020__tablas_bd_central.sql` (L542+) | DDL oficial **Control Plane / Shared** |
| Legacy central | `app/docs/database/tablas_bd_central.sql` | Referencia legacy (mapeada en `SOURCE_MAP.json`) |
| Legacy dedicated (referencia) | `app/docs/database/TABLAS_BD_DEDICADA.sql` (L129+) | **Documentación histórica** — incluye `auth_audit_log` + `refresh_tokens` |
| Migración UUID | `app/docs/database/migrations/FASE3_MIGRACION_UUID_COMPLETO.sql` | Evolución schema existente, no provisioning Dedicated |
| IAM Session v3 | `app/bootstrap_v2/01_schema/V031__iam_session_management_v3.sql` | Tablas sesión (`user_session`, `token_family`, `refresh_tokens`) — **solo ruta Shared** en manifiesto central |
| **Dedicated DTSP** | `app/bootstrap_v2/05_dedicated/V020__tenant_identity_rbac_store.sql` | **No contiene** `auth_audit_log` |

**Única definición DDL ejecutable en provisioning Dedicated:** ninguna. La tabla **no está en ningún script** del manifiesto `dedicated_schema_v2`.

---

## 3. ¿Pertenece al catálogo oficial del Data Plane Dedicated?

**No**, según la documentación normativa implementada:

- `app/docs/arquitectura/hybrid-platform/provisioning/DTSP_DEDICATED_TENANT_STORE_PROFILE.md` §3 enumera **9 tablas** DTSP (`modulo`, `modulo_seccion`, `modulo_menu`, `permiso`, `rol`, `rol_menu_permiso`, `usuario`, `usuario_rol`, `cliente_modulo`) + `rol_permiso` vía script aparte.
- **`auth_audit_log` no aparece** en DTSP ni en `DTSP_REQUIRED_TABLES` (`script_manifest.py` L49–73).
- `BOOTSTRAP_ORDER.md` Fase 6 define exactamente: `V010` ERP + `V020__tenant_identity_rbac_store` + `V010__rbac_tablas_dedicated`. **No** incluye `V020__tablas_bd_central.sql`.
- `BOOTSTRAP_GAPS.md` G-042 confirma que seeds/scripts legacy dedicated (`SEED_BD_DEDICADA_*`) están **excluidos** de bootstrap_v2.

La baseline híbrida (`architecture-baseline/03_RUNTIME_DECISION_STATUS.md`) clasifica `auth_audit_log` como **`tenant_data`** con routing según mode — decisión **runtime**, no reflejada en el catálogo DDL Dedicated actual.

---

## 4. Pipeline Dedicated — trazabilidad completa

```
ClienteService / onboarding API
        ↓
ProvisioningJobDispatcher          app/modules/tenant/application/services/provisioning_job_dispatcher.py
        ↓
DedicatedProvisioningOrchestrator    app/modules/tenant/application/services/dedicated_provisioning_orchestrator.py
   S2  StorageAllocationService      → nombre BD (ej. erp_cli017)
   S3  DedicatedDatabaseExecutor      → CREATE DATABASE + login (master)
   S4/S5 BootstrapScriptRunner       → manifiesto dedicated_schema_v2
   S6  DedicatedCatalogSeedService    → seeds 02_catalog/
   S7  DedicatedTenantSeedService     → seed tenant admin
   S8–S10 DedicatedActivationService → cliente_conexion + routing + MARK_READY
```

### 4.1 Script Manifest (`dedicated_schema_v2`)

Implementación: `app/infrastructure/provisioning/script_manifest.py` — `DEDICATED_SCHEMA_MANIFEST_V2`

| Orden | script_code | Archivo | step saga |
|------:|-------------|---------|-----------|
| 1 | `apply_schema_erp_v010` | `01_schema/V010__tablas_bd_erp_completo.sql` | S4 |
| 2 | `apply_schema_tenant_store_v020` | `05_dedicated/V020__tenant_identity_rbac_store.sql` | S5 |
| 3 | `apply_schema_rbac_v010` | `05_dedicated/V010__rbac_tablas_dedicated.sql` | S5 |

### 4.2 DDL Executor

- `DedicatedDatabaseExecutor.provision_physical_database` — solo crea BD/login en `master`; **no aplica DDL de tablas de negocio/auth**.
- `BootstrapScriptRunner.run_dedicated_schema_bootstrap` — descubre entradas del manifiesto, valida checksum, ejecuta batches, registra `bootstrap_applied`, verifica DTSP.

### 4.3 Descubrimiento / registro / ejecución de `auth_audit_log`

| Pregunta | Respuesta |
|----------|-----------|
| ¿Existe script con `CREATE TABLE auth_audit_log` aplicable a Dedicated? | **No** en `05_dedicated/` ni en manifiesto v2 |
| ¿Está registrado en manifiesto? | **No** |
| ¿Fue descubierto por `discover_manifest_entries`? | **No** — fuera del manifiesto |
| ¿Fue ejecutado? | **No** |
| ¿Fue omitido (skipped) por idempotencia? | **No** — nunca entró al loop de ejecución |
| ¿Por qué? | **No es entrada del catálogo oficial Dedicated** |

---

## 5. Verificación post-bootstrap (por qué el onboarding “pasa”)

`BootstrapScriptRunner._verify_dtsp_schema` (`bootstrap_script_runner.py` L140–160) exige únicamente:

```text
DTSP_REQUIRED_TABLES ∪ { rol_permiso }
```

**Sin** `auth_audit_log`, **sin** `user_session` / `token_family` / `refresh_tokens`, **sin** `log_sincronizacion_usuario`.

`DedicatedTenantSeedService.verify_tenant_seed_prerequisites` valida solo `permiso` (`core.app.acceder`) y filas en `modulo` — tampoco audit.

Por tanto, un tenant Dedicated recién creado puede llegar a **MARK_READY** con schema “incompleto” respecto a expectativas runtime auth/IAM, pero **completo** respecto al contrato DTSP F4-05b.

---

## 6. Comparativa Shared vs Dedicated (evidencia runtime read-only)

Entorno: Docker `fastapi_backend`, BD admin `bd_caxis_saas`, tenants Dedicated con `cliente_conexion.nombre_bd`.

### 6.1 Tablas auth / sesión / audit

| Objeto | Shared `bd_caxis_saas` | `erp_cli017` (acces) | `erp_cli013` (acmec) | `erp_cli016` (acce) |
|--------|:----------------------:|:--------------------:|:--------------------:|:-------------------:|
| `auth_audit_log` | ✅ | ❌ | ❌ | ✅ * |
| `user_session` | ✅ | ❌ | ❌ | ❌ |
| `token_family` | ✅ | ❌ | ❌ | ❌ |
| `refresh_tokens` | ✅ | ❌ | ❌ | ❌ |
| `log_sincronizacion_usuario` | ✅ | ❌ | ❌ | ❌ |

\* **Outlier `acce`:** presencia de `auth_audit_log` sin tablas IAM v3 sugiere origen **fuera del manifiesto v2 estándar** (DDL manual, provisioning legacy o reparación puntual). No invalida la causa raíz del catálogo: tenants creados solo vía saga F4 v2 **no** reciben la tabla.

### 6.2 ¿Es `auth_audit_log` el único objeto faltante?

**No.** En tenants Dedicated provisionados con manifiesto v2 faltan, como mínimo, todo el bloque **auth/sesión/audit** presente en Shared vía `V020` + `V031`:

| Grupo | Tablas ausentes en Dedicated (típico F4 v2) |
|-------|---------------------------------------------|
| Auditoría auth | `auth_audit_log` |
| IAM Session v3 | `user_session`, `token_family`, `refresh_tokens` |
| Sync | `log_sincronizacion_usuario` |
| Control Plane (intencional) | `cliente`, `cliente_conexion`, `cliente_auth_config`, `federacion_identidad`, … |

El Dedicated **sí** contiene el bloque DTSP + ERP (`V010`) + `rol_permiso` + `bootstrap_applied` tras onboarding exitoso.

### 6.3 Conteo orientativo

- Shared CP: **138** tablas `dbo` (medición audit).
- Dedicated F4: ERP completo + ~10 tablas DTSP/RBAC — **sin** bloque central de auth/audit.

---

## 7. ¿El onboarding Dedicated usa el mismo catálogo DDL que producción?

**Sí, para el pipeline F4 implementado** — y ese catálogo **no es** el de `TABLAS_BD_DEDICADA.sql` ni el subset auth de `V020__tablas_bd_central.sql`.

| Catálogo | ¿Usado en onboarding Dedicated F4? |
|----------|-----------------------------------|
| `DEDICATED_SCHEMA_MANIFEST_V2` (3 scripts) | **Sí** — único path saga S4/S5 |
| `V020__tablas_bd_central.sql` | **No** — solo Shared / CP |
| `V031__iam_session_management_v3.sql` | **No** — no registrado en manifiesto Dedicated |
| `TABLAS_BD_DEDICADA.sql` / `SEED_BD_DEDICADA_*` | **No** — legacy; G-042 excluido de v2 |

Producción Shared sigue `BOOTSTRAP_ORDER` Fases 1–4 (V010→V020→V030 + catálogo + runtime). Producción Dedicated sigue Fase 6 (A1/A1b/A2) — **subconjunto distinto**.

---

## 8. Impacto runtime (contexto, sin proponer fix)

`AuditService.registrar_auth_event` (`audit_service.py` L123–167) asume:

> «auth_audit_log existe tanto en BD central como en BD dedicada»

Para Dedicated enruta a `DatabaseConnection.DEFAULT` (BD tenant). Si la tabla no existe, el insert falla; el servicio es **fail-soft** (log ERROR, no bloquea login). El tenant puede operar “funcionalmente” en smoke HTTP aunque la auditoría auth no persista en DP.

IAM Session Management v2/v3 requiere `user_session` / `token_family` / `refresh_tokens` en el store del tenant — también **ausentes** del catálogo DTSP (gap relacionado, no limitado a `auth_audit_log`).

---

## 9. Inventario de logs clasificados (pipeline provisioning)

Solo referencia — no es bug de logging RBAC; documenta por qué no hay error visible en saga:

| Evento | Nivel | Clasificación |
|--------|-------|---------------|
| `Bootstrap script applied … apply_schema_tenant_store_v020` | INFO | Operacional — script DTSP ejecutado correctamente |
| `_verify_dtsp_schema` OK | *(silencio)* | Operacional — gate pasado sin auth_audit_log |
| `Saga completed S1–S10` | INFO | Operacional — onboarding declarado completo |
| `[AUDIT] Error registrando auth_audit_log` post-login Dedicated | ERROR | Síntoma downstream — tabla inexistente |

---

## 10. Respuestas directas al checklist F12-G1

| # | Pregunta | Respuesta |
|---|----------|-----------|
| 1 | Definición oficial | `V020__tablas_bd_central.sql` (Shared); referencia legacy `TABLAS_BD_DEDICADA.sql` **no ejecutada** |
| 2 | ¿Catálogo DP Dedicated? | **No pertenece** al DTSP oficial |
| 3 | Pipeline | Dispatcher → Orchestrator → Executor (BD) → Manifest (3 scripts) → Runner → verificación DTSP |
| 4 | Script auth_audit_log | Existe en Shared; **no registrado ni ejecutado** en Dedicated |
| 5 | ¿Omitido? | **No omitido** — **excluido del manifiesto** |
| 6 | ¿Solo auth_audit_log? | **No** — faltan también tablas IAM session v3 y `log_sincronizacion_usuario` |
| 7 | ¿Mismo catálogo que prod? | Dedicated usa manifiesto v2 **distinto** de Shared; onboarding alineado a ese manifiesto, no a legacy dedicated SQL |

---

## 11. Referencias

| Documento / código |
|--------------------|
| `app/infrastructure/provisioning/script_manifest.py` |
| `app/infrastructure/provisioning/bootstrap_script_runner.py` |
| `app/modules/tenant/application/services/dedicated_provisioning_orchestrator.py` |
| `app/docs/arquitectura/hybrid-platform/provisioning/DTSP_DEDICATED_TENANT_STORE_PROFILE.md` |
| `app/bootstrap_v2/00_manifest/BOOTSTRAP_ORDER.md` (Fase 6) |
| `app/bootstrap_v2/00_manifest/BOOTSTRAP_GAPS.md` (G-042) |
| `app/modules/superadmin/application/services/audit_service.py` |
| `app/docs/arquitectura/hybrid-platform/architecture-baseline/03_RUNTIME_DECISION_STATUS.md` (C-04) |

**F12-G1 Dedicated DDL Root Cause Audit cerrado.** Sin propuesta de remediación (alcance explícito).
