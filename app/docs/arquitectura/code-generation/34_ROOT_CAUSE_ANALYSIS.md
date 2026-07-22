# F17E — Análisis de causa raíz (RCA) de la regresión Dedicated

**Fase:** F17E — RCA (READ-ONLY).
**Fecha:** 2026-07-03
**Complementa:** `33_DEDICATED_REGRESSION_AUDIT.md` (evidencia) y `35_FLOW_COMPARISON_BEFORE_AFTER.md` (flujo).

---

## 1. Enunciado de la causa raíz

> **La modificación de F17 al DDL de `cfg_codigo_secuencia` dentro de `V010__tablas_bd_erp_completo.sql` cambió el contenido del archivo y, por tanto, su SHA-256; el checksum congelado del manifiesto Dedicated (`_V010_ERP_SHA256`) no fue recalculado. En consecuencia, `validate_manifest_integrity` falla al inicio del bootstrap del Data Plane, ANTES de que se cree la tabla de markers `bootstrap_applied`. El manejador de fallo del orquestador lee entonces `bootstrap_applied` en una BD donde nunca se creó, produciendo `Invalid object name 'bootstrap_applied'`, que enmascara el error real (checksum divergente).**

El error **no** es una tabla faltante por diseño ni una migración olvidada: es una **regresión de integridad de checksum** provocada por un cambio de contenido en un artefacto con checksum congelado, más un **orden de operaciones** que convierte ese fallo en un síntoma engañoso.

---

## 2. Clasificación

| Dimensión | Valor |
|-----------|-------|
| Tipo | Regresión por drift de checksum (artefacto congelado modificado) |
| Categoría del síntoma | Error secundario que enmascara el error primario |
| ¿Tabla faltante por diseño? | **No** — `bootstrap_applied` se crea programáticamente en S4/S5 |
| ¿Introducido por F17? | Sí, indirectamente: F17 editó V010 (esquema del Motor) |
| ¿Dependencia nueva de F17 sobre `bootstrap_applied`? | **No** — la tabla es de F4/F12 |
| Alcance | Solo onboarding **Dedicated** (Shared no valida manifiesto ni usa `bootstrap_applied`) |

---

## 3. Cadena causal (determinista)

```
[1] F17 (Motor de Códigos) reescribe la tabla cfg_codigo_secuencia en
    app/bootstrap_v2/01_schema/V010__tablas_bd_erp_completo.sql
    (+sequence_key, +scope_fingerprint, +UQ_cfg_scope, +2 índices) — SIN commitear
        │
        ▼
[2] SHA-256(V010 working) = 5f81e8c3…   ≠   _V010_ERP_SHA256 congelado = 78733886…
        │   (el congelado sigue = HEAD committed, que NO tiene esas columnas)
        ▼
[3] Nuevo cliente Dedicated → saga S4 (APPLY_SCHEMA_ERP)
    → BootstrapScriptRunner.run_dedicated_schema_bootstrap()
        │
        ▼
[4] línea 81: validate_manifest_integrity(manifest)
    → compute_file_sha256(V010) = 5f81e8c3…  ≠  expected 78733886…
    → raise ValidationError(BOOTSTRAP_MANIFEST_INTEGRITY_FAILED)
        │   (la línea 83 _ensure_bootstrap_applied_table NUNCA se ejecuta)
        ▼
[5] _run_bootstrap_block: except Exception as exc (línea 503)
    → _reconcile_bootstrap_failure() (línea 504)
        │
        ▼
[6] BootstrapAppliedReader.list_applied_script_codes(database)
    → SELECT checksum_sha256 FROM bootstrap_applied WHERE …
        │   (la tabla no existe en la BD nueva)
        ▼
[7] SQL Server: "Invalid object name 'bootstrap_applied'"
    → DedicatedDdlClient.scalar_str: logger.exception + raise DatabaseError from exc
        │
        ▼
[8] La nueva excepción se propaga (reemplaza al error de checksum)
    → el usuario ve "Invalid object name 'bootstrap_applied'"
```

---

## 4. Los "5 porqués"

1. **¿Por qué aparece `Invalid object name 'bootstrap_applied'`?**
   Porque el manejador de fallo del bootstrap lee esa tabla en una BD donde no existe.
2. **¿Por qué no existe la tabla?**
   Porque `_ensure_bootstrap_applied_table` (línea 83) nunca se ejecutó: el bootstrap abortó en la línea 81.
3. **¿Por qué abortó en la línea 81?**
   Porque `validate_manifest_integrity` detectó que el SHA-256 real de V010 no coincide con el congelado.
4. **¿Por qué no coincide el checksum?**
   Porque F17 modificó `cfg_codigo_secuencia` en V010 y el valor congelado `_V010_ERP_SHA256` no se recalculó.
5. **¿Por qué no se recalculó?**
   Porque el manifiesto trata a V010 como artefacto de checksum congelado ("recalcular … prohibido F4-05b"), y el flujo de trabajo de F17 (esquema del Motor) no incluyó ese recálculo controlado ni una prueba de guardia que lo forzara.

**Causa raíz sistémica:** V010 cumple doble rol — es el **esquema ERP evolutivo** (Shared) y un **artefacto de bootstrap con checksum congelado** (Dedicated). Cualquier evolución legítima del esquema ERP rompe el manifiesto Dedicated salvo recálculo explícito. F17 fue el primer cambio de esquema tras congelar el checksum.

---

## 5. Localización exacta (archivo · clase · método · línea)

| Rol | Archivo | Clase | Método | Línea aprox. |
|-----|---------|-------|--------|--------------|
| **Disparador (valor)** | `app/infrastructure/provisioning/script_manifest.py` | — | `_V010_ERP_SHA256` (constante) | 27–29 |
| **Disparador (chequeo)** | `app/infrastructure/provisioning/script_manifest.py` | — | `validate_manifest_integrity` (raise) | 401 / 441–455 |
| **Contenido modificado** | `app/bootstrap_v2/01_schema/V010__tablas_bd_erp_completo.sql` | — | `CREATE TABLE cfg_codigo_secuencia` (+cols) | 6809–6845 |
| **Aborto por orden** | `app/infrastructure/provisioning/bootstrap_script_runner.py` | `BootstrapScriptRunner` | `run_dedicated_schema_bootstrap` | 81 (valida) vs 83 (crea) |
| **Creación no alcanzada** | `app/infrastructure/provisioning/bootstrap_script_runner.py` | `BootstrapScriptRunner` | `_ensure_bootstrap_applied_table` | 161–171 |
| **Lectura que falla (síntoma)** | `app/infrastructure/provisioning/bootstrap_applied_reader.py` | `BootstrapAppliedReader` | `list_applied_script_codes` | 38 / 42–46 |
| **Invocación del lector** | `app/modules/tenant/application/services/dedicated_provisioning_orchestrator.py` | `DedicatedProvisioningOrchestrator` | `_reconcile_bootstrap_failure` | 571 / 580 |
| **Contexto del except** | `app/modules/tenant/application/services/dedicated_provisioning_orchestrator.py` | `DedicatedProvisioningOrchestrator` | `_run_bootstrap_block` | 503–504 |
| **Enmascaramiento** | `app/infrastructure/provisioning/dedicated_ddl_client.py` | `AioOdbcDedicatedDdlClient` | `scalar_str` | 167–178 |

**Línea única que origina el problema (punto de disparo):** `bootstrap_script_runner.py:81` (`validate_manifest_integrity`) al evaluar V010 modificado por F17 contra `script_manifest.py:27` (`_V010_ERP_SHA256`).

---

## 6. Confirmación negativa (lo que NO es la causa)

- **No** es una migración de `bootstrap_applied` olvidada: la tabla nunca estuvo en SQL; se crea en runtime.
- **No** es finales de línea: `V010` working y su normalización LF dan el mismo hash `5f81e8c3…`; `HEAD` LF es exactamente el congelado.
- **No** es el paso S7 (`DedicatedTenantSeedService`): la saga aborta en S4, S7 no se alcanza.
- **No** es el acoplamiento `tenant_seed_profiles → EAGER_SEQUENCE_KEYS`: no interviene en la ruta del error.
- **No** afecta al onboarding **Shared**: Shared no ejecuta `validate_manifest_integrity` ni usa `bootstrap_applied` (usa `bootstrap_applied`/markers solo el Data Plane Dedicated; Shared corre `_insertar_secuencias_codigo` en una única TX ADMIN).

---

## 7. Predicción falsable

Si la causa raíz es correcta, entonces:

1. Recalcular `SHA-256(V010 actual) = 5f81e8c3…` y ponerlo como `_V010_ERP_SHA256` haría pasar `validate_manifest_integrity`, se crearía `bootstrap_applied`, y el error desaparecería. *(No se aplica en esta fase — solo se enuncia como prueba lógica.)*
2. El test `tests/unit/test_f4_05b_dtsp_manifest.py::test_f4_05b_manifest_integrity_includes_dtsp` debe estar **fallando hoy** con `Checksum bootstrap divergente para 01_schema/V010…` — lo cual coincide con lo observado en la corrida de F17D.

Ambas predicciones son consistentes con la evidencia recogida.

---

*Comparación de flujo antes/después en `35_FLOW_COMPARISON_BEFORE_AFTER.md`. Opciones de remediación (sin implementar) en `36_IMPLEMENTATION_RECOMMENDATION.md`.*
