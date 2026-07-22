# F17E — Auditoría forense de regresión Dedicated (`Invalid object name 'bootstrap_applied'`)

**Fase:** F17E — Investigación forense (READ-ONLY, sin modificar código).
**Fecha:** 2026-07-03
**Naturaleza:** auditoría técnica para localizar la causa raíz de una regresión en el onboarding Dedicated.
**Restricción cumplida:** no se modificó código, V010, bootstrap, manifests ni onboarding. Solo se generó documentación (33–36).

> **Síntoma reportado:** al crear un nuevo cliente **Dedicated** aparece `Invalid object name 'bootstrap_applied'`. Hasta antes de la implementación del Motor de Generación de Códigos (F17), el onboarding Dedicated funcionaba.

---

## 1. Método de investigación

1. Mapeo estático de todas las referencias a `bootstrap_applied` (lecturas, escrituras, DDL).
2. Lectura completa de los componentes del pipeline Dedicated S1–S10.
3. Determinación del punto exacto donde se crea la tabla `bootstrap_applied` y del orden de operaciones.
4. Reproducción documental del checksum del manifiesto (SHA-256 real vs congelado).
5. Arqueología git (blame/log/blob) para fechar el cambio y descartar hipótesis.
6. Comprobación de la variable de finales de línea (LF/CRLF) para descartar falsos positivos.

**Nota metodológica (importante):** los primeros cálculos de SHA vía *pipe* de PowerShell (`git show … | python`) resultaron **corruptos** porque PowerShell re-codifica el flujo de texto. Todos los hashes de este informe se recalcularon con `subprocess.run(..., capture_output=True).stdout` (bytes crudos). Los valores válidos son los de §4.

---

## 2. Componentes auditados

| Componente | Archivo | Rol en el flujo |
|-----------|---------|-----------------|
| `BootstrapScriptRunner` | `app/infrastructure/provisioning/bootstrap_script_runner.py` | S4/S5 — aplica scripts de esquema + **crea** `bootstrap_applied` |
| `BootstrapAppliedReader` | `app/infrastructure/provisioning/bootstrap_applied_reader.py` | Lee `bootstrap_applied` (reconciliación) |
| `DedicatedTenantSeedService` | `app/infrastructure/provisioning/dedicated_tenant_seed_service.py` | S7 — lee/escribe markers en `bootstrap_applied` |
| `DedicatedProvisioningOrchestrator` | `app/modules/tenant/application/services/dedicated_provisioning_orchestrator.py` | Saga S1–S10; maneja fallo de bootstrap |
| `script_manifest` | `app/infrastructure/provisioning/script_manifest.py` | Checksums congelados + `validate_manifest_integrity` |
| `DedicatedDdlClient` | `app/infrastructure/provisioning/dedicated_ddl_client.py` | Ejecuta SQL sobre la BD dedicada; propaga error pyodbc |
| `tenant_seed_profiles` | `app/infrastructure/provisioning/tenant_seed_profiles.py` | Perfil S7 (row_expectations) |
| Esquema ERP | `app/bootstrap_v2/01_schema/V010__tablas_bd_erp_completo.sql` | DDL aplicado en la BD dedicada |

---

## 3. ¿Quién crea y quién lee `bootstrap_applied`?

### 3.1 Creación — es PROGRAMÁTICA, no está en ningún `.sql`

`bootstrap_applied` **no** se crea en V010 ni en ninguna migración. La búsqueda global de `bootstrap_applied` no arroja ningún archivo `.sql`. Se crea en código, con `IF NOT EXISTS`, dentro del runner:

```
# bootstrap_script_runner.py (líneas 40–55)
_BOOTSTRAP_APPLIED_DDL = """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'bootstrap_applied')
BEGIN
    CREATE TABLE bootstrap_applied ( ... );
END
"""
```

Se ejecuta en `_ensure_bootstrap_applied_table` (línea 161), invocado por `run_dedicated_schema_bootstrap`.

### 3.2 Orden crítico dentro de `run_dedicated_schema_bootstrap`

```
# bootstrap_script_runner.py (run_dedicated_schema_bootstrap)
80:  manifest = load_dedicated_schema_manifest(profile=request.profile)
81:  validate_manifest_integrity(manifest, bootstrap_root=self._bootstrap_root)   # ← valida checksum PRIMERO
83:  await self._ensure_bootstrap_applied_table(request.database_name)            # ← crea la tabla DESPUÉS
```

**Consecuencia:** si `validate_manifest_integrity` (línea 81) lanza, la línea 83 **nunca se ejecuta** → `bootstrap_applied` **no se crea** en la BD dedicada nueva.

### 3.3 Primera LECTURA de `bootstrap_applied` en el flujo Dedicated

Hay tres lectores; el que dispara el síntoma es el de **reconciliación de fallo** del orquestador:

| Orden | Lector | Ubicación | Cuándo |
|-------|--------|-----------|--------|
| 1 (síntoma) | `BootstrapAppliedReader.list_applied_script_codes` | `bootstrap_applied_reader.py` líneas 42–46 | En el **handler de excepción** del bloque bootstrap |
| 2 | `BootstrapScriptRunner._is_script_applied` | `bootstrap_script_runner.py` líneas 179–184 | Durante el bootstrap (tras crear la tabla) |
| 3 | `DedicatedTenantSeedService._is_step_applied` | `dedicated_tenant_seed_service.py` líneas 158–162 | En S7 (nunca se alcanza si S4 aborta) |

El lector nº1 se invoca desde el orquestador:

```
# dedicated_provisioning_orchestrator.py (_run_bootstrap_block)
484:  result = await self._bootstrap.run_dedicated_schema_bootstrap(...)   # lanza ValidationError (checksum)
503:  except Exception as exc:
504:      await self._reconcile_bootstrap_failure(job=job, runtime=runtime) # ← lee bootstrap_applied inexistente
```

```
# dedicated_provisioning_orchestrator.py (_reconcile_bootstrap_failure)
580:  applied = await self._bootstrap_reader.list_applied_script_codes(allocation.database_name)
```

```
# bootstrap_applied_reader.py (list_applied_script_codes)
42:  stored = await self._client().scalar_str(
43:      f"SELECT checksum_sha256 FROM bootstrap_applied "
44:      f"WHERE script_code = N'{escaped}'", database=database_name)
```

Sobre una BD recién creada donde el bootstrap abortó antes de la línea 83, ese `SELECT` produce `Invalid object name 'bootstrap_applied'`.

### 3.4 Por qué el error se ve “crudo”

`DedicatedDdlClient.scalar_str` envuelve el error como `DatabaseError` genérico **pero** registra y encadena el mensaje pyodbc original:

```
# dedicated_ddl_client.py (scalar_str)
173:  except Exception as exc:
174:      logger.exception("Error DDL scalar_str database=%s", database)   # deja el mensaje pyodbc en el log
175:      raise DatabaseError(..., internal_code="DDL_SCALAR_FAILED") from exc  # encadena la causa
```

El texto `Invalid object name 'bootstrap_applied'` aparece en el traceback/log (causa encadenada), **enmascarando** el error real de checksum. Además, como `_reconcile_bootstrap_failure` se ejecuta dentro del `except`, la nueva excepción reemplaza a la original de checksum al propagarse por `handle_job`.

---

## 4. Evidencia dura — checksum del manifiesto vs V010

El manifiesto congela el checksum de V010 (recalcular está marcado como prohibido sin proceso):

```
# script_manifest.py
25:  # Checksums congelados — recalcular solo si cambia contenido bootstrap_v2 (prohibido F4-05b).
27:  _V010_ERP_SHA256 = "78733886529a88af139bde57af5e44a663d417cb5cab0835f7a45b87adda1237"
```

`validate_manifest_integrity` compara el SHA-256 real del archivo contra ese valor (línea 439–455) y lanza `BOOTSTRAP_MANIFEST_INTEGRITY_FAILED` si difieren.

### 4.1 Tabla de hashes SHA-256 de `V010` (bytes crudos)

| Estado | Commit / origen | SHA-256 de V010 | ¿== congelado? | `sequence_key` en cfg |
|--------|-----------------|-----------------|----------------|------------------------|
| Histórico | `469af23` (2026-05-31) | `82538aa9…0fe4` | No (esquema previo) | — |
| Histórico | `57eb83a` (2026-06-05) | `82538aa9…0fe4` | No (esquema previo) | — |
| **Committed** | `ecb640d` (2026-06-17) | `78733886…1237` | **SÍ** | **No** |
| **Committed HEAD** | `72ebaa1` (2026-07-03) | `78733886…1237` | **SÍ** | **No** |
| **Working tree (actual)** | sin commitear | `5f81e8c3…0cb5` | **NO — DIVERGE** | **Sí** |

- **Congelado en manifiesto:** `78733886…1237`.
- **Committed HEAD coincide exactamente** con el congelado → en el repo commiteado, `validate_manifest_integrity` **pasa**.
- El **working tree** (lo que corre el desarrollador) tiene una modificación **sin commitear** que cambia el hash a `5f81e8c3…` → `validate_manifest_integrity` **falla**.

### 4.2 Qué contiene la modificación no commiteada de V010

`git diff --numstat` sobre V010 = **35 inserciones / 10 borrados**. Las líneas añadidas son exactamente el esquema del Motor de Generación de Códigos:

```
+    sequence_key              NVARCHAR(64)     NOT NULL,
+    scope_fingerprint         CHAR(64)         NOT NULL,
+    CONSTRAINT UQ_cfg_scope UNIQUE (cliente_id, sequence_key, scope_fingerprint),
+CREATE INDEX IDX_cfg_empresa ON cfg_codigo_secuencia(cliente_id, empresa_id, sequence_key);
+CREATE INDEX IDX_cfg_almacen ON cfg_codigo_secuencia(cliente_id, almacen_id, sequence_key);
```

Verificación de contenido:
- `HEAD` committed V010: `sequence_key` presente = **False**, `scope_fingerprint` = **False** (tabla `cfg_codigo_secuencia` en su forma antigua).
- `WORKING` V010: `sequence_key` = **True**, `scope_fingerprint` = **True** (tabla remodelada por F17).

**Conclusión de §4:** la única diferencia entre “funciona” y “falla” es la reescritura F17 de `cfg_codigo_secuencia` en V010 (working tree), que rompe el checksum congelado. No es un problema de finales de línea: `WORK` y `WORK` normalizado a LF dan el mismo hash `5f81e8c3…`; y `HEAD` en LF es exactamente el congelado.

---

## 5. ¿`bootstrap_applied` es diseño original o artefacto F17?

**Es diseño original del provisioning Dedicated (fases F4/F12), NO un artefacto de F17.** Evidencia:

- Docstrings de procedencia: `bootstrap_script_runner.py` → “PR-F4-05 / F4-05b / F12-G3”; `bootstrap_applied_reader.py` → “PR-F4-08 / H-02”; `dedicated_tenant_seed_service.py` → “PR-F4-07”. Todas son fases **anteriores** a F15–F17.
- git: `script_manifest.py`, `bootstrap_script_runner.py` y `bootstrap_applied_reader.py` fueron consolidados juntos (commit `72ebaa1` “bd shared/dedicated completado”) como parte del stack de provisioning Dedicated, independiente del Motor de Códigos.
- Documentación histórica que ya menciona `bootstrap_applied`: `F12_G1/G2/G3`, `F13_A1`, `catalog-sync/*`, `hybrid-platform/…/DTSP_*`, `IP-2.0_F4_IMPLEMENTATION_PLAN.md`.

F17 **no** introdujo `bootstrap_applied`; tampoco lee esa tabla desde el Motor. El único acoplamiento nuevo de F17 hacia el provisioning es `tenant_seed_profiles.py` línea 8 (`from app.core.codigo.onboarding_seed import EAGER_SEQUENCE_KEYS`), que **no** interviene en el error.

---

## 6. Respuestas directas al cuestionario (A–E)

**A) ¿`bootstrap_applied` forma parte del diseño original?** → **SÍ.** Es la tabla de markers del bootstrap Dedicated (F4/F12), creada programáticamente por `BootstrapScriptRunner._ensure_bootstrap_applied_table`. Evidencia en §3.1 y §5.

**B) N/A** (sí forma parte del diseño).

**C) ¿Por qué antes funcionaba y qué regresión introdujo F17?**
- Antes de F17: el V010 commiteado coincide byte a byte con el checksum congelado (`78733886…`) → `validate_manifest_integrity` pasa → se crea `bootstrap_applied` → el seed la lee sin problema.
- F17 modificó `cfg_codigo_secuencia` en V010 (añadió `sequence_key`, `scope_fingerprint`, `UQ_cfg_scope` + índices) **sin recalcular** el checksum congelado. Ahora la validación falla **antes** de crear la tabla, y la ruta de reconciliación lee una tabla inexistente. Detalle en §4 y en `34_ROOT_CAUSE_ANALYSIS.md`.

**D) Ubicación exacta** (ver §3 y §4; ampliado en `34`):
- **Disparador real:** `script_manifest.py::validate_manifest_integrity` (raise líneas 441–455) usando `_V010_ERP_SHA256` (líneas 27–29), contra `V010__tablas_bd_erp_completo.sql` modificado (working tree).
- **Punto de aborto (orden):** `bootstrap_script_runner.py::BootstrapScriptRunner.run_dedicated_schema_bootstrap` — validación en línea 81 **antes** de crear la tabla en línea 83.
- **Origen del síntoma:** `bootstrap_applied_reader.py::BootstrapAppliedReader.list_applied_script_codes` líneas 42–46, invocado desde `dedicated_provisioning_orchestrator.py::_reconcile_bootstrap_failure` línea 580 (dentro del `except` de `_run_bootstrap_block` línea 503–504).

**E) Flujo antes/después:** ver `35_FLOW_COMPARISON_BEFORE_AFTER.md`.

---

## 7. Hallazgos secundarios (no son la causa raíz)

- **H-SEC-01 (enmascaramiento):** la reconciliación de fallo lee `bootstrap_applied` sin garantizar que exista; ante cualquier fallo previo a su creación, el error real queda oculto tras `Invalid object name`. Es un problema de observabilidad, no la causa.
- **H-SEC-02 (orden):** `validate_manifest_integrity` corre antes de `_ensure_bootstrap_applied_table`; ambos legítimos, pero el orden hace que un fallo de integridad impida diagnosticar por markers.
- **H-SEC-03 (acoplamiento F17→provisioning):** `tenant_seed_profiles` importa `EAGER_SEQUENCE_KEYS` del Motor; no afecta a este bug, pero es una dependencia nueva a vigilar.
- **H-SEC-04 (política de checksum):** V010 es simultáneamente el esquema ERP que evoluciona y un artefacto con checksum congelado; toda evolución de esquema ERP rompe el manifiesto Dedicated salvo recálculo explícito.

---

*Análisis de causa raíz en `34_ROOT_CAUSE_ANALYSIS.md`. Comparación de flujo en `35_FLOW_COMPARISON_BEFORE_AFTER.md`. Opciones de remediación (sin implementar) en `36_IMPLEMENTATION_RECOMMENDATION.md`.*
