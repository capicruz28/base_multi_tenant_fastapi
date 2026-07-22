# F17E — Comparación de flujo Dedicated: ANTES de F17 → DESPUÉS de F17

**Fase:** F17E (READ-ONLY).
**Fecha:** 2026-07-03
**Complementa:** `33_DEDICATED_REGRESSION_AUDIT.md`, `34_ROOT_CAUSE_ANALYSIS.md`.

Objetivo: mostrar el flujo del bootstrap Dedicated **antes** y **después** del cambio de V010 de F17, señalando el punto exacto de divergencia.

---

## 1. Punto de divergencia (resumen)

| | ANTES de F17 | DESPUÉS de F17 |
|--|--------------|----------------|
| Contenido V010 (`cfg_codigo_secuencia`) | forma previa (sin `sequence_key`/`scope_fingerprint`) | remodelada por el Motor (+`sequence_key`, +`scope_fingerprint`, +`UQ_cfg_scope`, +índices) |
| SHA-256(V010) | `78733886…1237` | `5f81e8c3…0cb5` |
| `_V010_ERP_SHA256` (congelado) | `78733886…1237` | `78733886…1237` (sin recalcular) |
| `validate_manifest_integrity` | **PASA** | **FALLA** (`BOOTSTRAP_MANIFEST_INTEGRITY_FAILED`) |
| `_ensure_bootstrap_applied_table` | se ejecuta → tabla creada | **no se ejecuta** → tabla ausente |
| Resultado | bootstrap OK → S6/S7 → READY | aborta S4 → reconciliación lee tabla ausente → `Invalid object name 'bootstrap_applied'` |

**La divergencia ocurre en `bootstrap_script_runner.py`, línea 81 (`validate_manifest_integrity`), dentro del step S4 `APPLY_SCHEMA_ERP`.**

---

## 2. Flujo ANTES de F17 (funcionaba)

```
Saga Dedicated (DedicatedProvisioningOrchestrator._handle_job_inner)
  S1 REGISTRY
  S2 STORAGE_ALLOCATION
  S3 CREATE_DATABASE  ........................ BD dedicada vacía creada
  S4/S5 APPLY_SCHEMA_ERP / APPLY_SCHEMA_RBAC → _run_bootstrap_block
        └─ BootstrapScriptRunner.run_dedicated_schema_bootstrap
             80  load_dedicated_schema_manifest()
             81  validate_manifest_integrity()   →  SHA(V010)=78733886 == congelado  ✔ PASA
             83  _ensure_bootstrap_applied_table() → CREATE TABLE bootstrap_applied   ✔ CREADA
             94+ por cada script: _is_script_applied → execute → _record_script_applied
             128 _verify_runtime_schema()  ✔ tablas runtime presentes
        └─ _mark_bootstrap_saga_steps() marca ERP + RBAC completed
  S6 APPLY_CATALOGS ........................... catálogos sembrados
  S7 SEED_TENANT → DedicatedTenantSeedService.run_tenant_seed
        └─ por cada step: _is_step_applied (SELECT bootstrap_applied)  ✔ tabla existe
        └─ execute_tenant_seed_step → _record_step_applied (INSERT bootstrap_applied)
        └─ _verify_row_expectations  ✔
  S8–S10 REGISTER_METADATA / ACTIVATE_ROUTING / MARK_READY
  → Cliente Dedicated READY
```

Clave: en la línea 81 el checksum coincide, así que la línea 83 crea `bootstrap_applied`. Todos los lectores posteriores la encuentran.

---

## 3. Flujo DESPUÉS de F17 (falla)

```
Saga Dedicated (DedicatedProvisioningOrchestrator._handle_job_inner)
  S1 REGISTRY
  S2 STORAGE_ALLOCATION
  S3 CREATE_DATABASE  ........................ BD dedicada vacía creada
  S4/S5 APPLY_SCHEMA_ERP / APPLY_SCHEMA_RBAC → _run_bootstrap_block
        └─ BootstrapScriptRunner.run_dedicated_schema_bootstrap
             80  load_dedicated_schema_manifest()
             81  validate_manifest_integrity()
                    SHA(V010)=5f81e8c3  ≠  congelado 78733886
                    → raise ValidationError(BOOTSTRAP_MANIFEST_INTEGRITY_FAILED)   ✘ ABORTA
             83  _ensure_bootstrap_applied_table()   ← NUNCA SE EJECUTA (tabla NO creada)
        └─ except Exception as exc (orchestrator línea 503)
             504  _reconcile_bootstrap_failure()
                    580  BootstrapAppliedReader.list_applied_script_codes(db)
                           42  SELECT checksum_sha256 FROM bootstrap_applied …
                               → SQL Server: Invalid object name 'bootstrap_applied'
                    → DedicatedDdlClient.scalar_str: logger.exception + raise DatabaseError from exc
        └─ la NUEVA excepción se propaga y reemplaza al error de checksum
  handle_job → logger.exception("excepcion_completa") → re-raise
  → El operador ve: Invalid object name 'bootstrap_applied'
     (el error real —checksum divergente— queda solo en la causa encadenada del traceback)
  S6/S7/S8–S10  ← NUNCA SE ALCANZAN
```

---

## 4. Diagrama de decisión (dónde se bifurca)

```
                 run_dedicated_schema_bootstrap()
                             │
             ┌───────────────┴───────────────┐
             │  validate_manifest_integrity   │  (línea 81)
             │  SHA(V010) == _V010_ERP_SHA256 ?
             └───────────────┬───────────────┘
              SÍ (ANTES)      │      NO (DESPUÉS de F17)
        ┌───────────────┐    │    ┌──────────────────────────────┐
        │ crea tabla    │    │    │ ValidationError (checksum)     │
        │ bootstrap_    │    │    │ → tabla NO creada              │
        │ applied (L83) │    │    │ → _reconcile_bootstrap_failure │
        │ → S6/S7 → OK  │    │    │ → SELECT bootstrap_applied     │
        └───────────────┘    │    │ → Invalid object name          │
                             ▼    └──────────────────────────────┘
                     (mismo código; solo cambió el
                      contenido de V010 y no el checksum)
```

**El código del pipeline es idéntico antes y después.** Lo único que cambió es un dato: los bytes de `V010` (por la remodelación F17 de `cfg_codigo_secuencia`) frente a un checksum congelado no actualizado.

---

## 5. Contraste con el onboarding Shared (por qué Shared no falla)

| Aspecto | Dedicated | Shared |
|--------|-----------|--------|
| Aplica esquema desde V010 en runtime | **Sí** (BD por tenant) | No (BD compartida ya existe) |
| Ejecuta `validate_manifest_integrity` | **Sí** | No |
| Usa `bootstrap_applied` | **Sí** (markers Data Plane) | No |
| Siembra secuencias | `DedicatedTenantSeedService` (S7) | `ClienteOnboardingService._insertar_secuencias_codigo` (una TX ADMIN) |
| Impacto del checksum de V010 | **Bloqueante** | Ninguno |

Por eso la regresión es exclusiva de Dedicated: solo ese camino valida el checksum congelado de V010 y solo ahí se materializa `bootstrap_applied`.

---

*Causa raíz en `34_ROOT_CAUSE_ANALYSIS.md`. Opciones de remediación (sin implementar) en `36_IMPLEMENTATION_RECOMMENDATION.md`.*
