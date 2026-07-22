# F17A — Plan de generación del seed oficial de `cfg_codigo_secuencia`

**Fase:** F17A — Bootstrap oficial (planificación del seed)
**Fecha:** 2026-07-03
**Base:** `01`/`02`/`03` de esta fase; F17 Ola 0 (código existente)

> **Este documento NO genera SQL ni INSERTs.** Especifica *cómo* se construye el seed programático derivado del catálogo.

> **Estado F17D (2026-07-03):** el alcance del seed eager quedó **resuelto e implementado**. Criterio oficial: el onboarding siembra **todas** las secuencias CFG con scope resoluble (TENANT/EMPRESA), **derivadas automáticamente** del `SequenceCatalog` (sin lista manual ni conteo fijo). Las de scope ALMACEN/PUNTO_VENTA quedan lazy. Las secciones §5 y §8 (que planteaban elegir un subconjunto A/B/C) quedan **superadas** por este criterio.

---

## 1. Puerta de aprobación

| Precondición | Estado |
|--------------|--------|
| Configuración oficial de 63 entradas aprobada (`01`) | ⏳ Pendiente de aprobación del usuario |
| Estándar de prefijos aprobado (`02`) | ⏳ |
| Reglas de bootstrap aprobadas (`03`) | ⏳ |
| **Recién entonces:** generar seed | ⛔ Bloqueado hasta aprobación |

**Regla SEED-GATE-01:** no se escribe seed (Python/SQL) hasta que `01`–`03` estén aprobados. Si un default cambia en la aprobación, se ajusta el catálogo (gobernanza `22`) **antes** de generar el seed.

---

## 2. Fuente única de verdad

| Elemento | Fuente |
|----------|--------|
| Metadatos (prefijo, padding, scope, policy, family) | `SequenceCatalog` (`app/core/codigo/sequence_catalog.py`) |
| Subconjunto eager de onboarding | `ONBOARDING_SEQUENCE_SEEDS` (`app/core/codigo/onboarding_seed.py`) — **derivado** del catálogo (store CFG + scope TENANT/EMPRESA), sin lista manual |
| Cálculo de fingerprint | `compute_scope_fingerprint` (`app/core/codigo/scope_fingerprint.py`) |
| Persistencia | `CfgCodigoSecuenciaRepository.insert_secuencia` (ya adaptado en F17) |

**Regla SEED-SRC-01:** el seed **deriva** del catálogo; **prohibido** duplicar los valores de configuración en el script. El seed itera sobre el catálogo/seed-subset, no re-declara prefijos.

---

## 3. Arquitectura del seed (dos capas)

### 3.1 Capa eager (onboarding) — ya existente

Implementado en F17 Ola 0 y ampliado en F17D:

- Origen: `ONBOARDING_SEQUENCE_SEEDS`, **derivado** del catálogo = todas las CFG con scope TENANT/EMPRESA (57 filas para una empresa: 1 TENANT + 56 EMPRESA).
- Ejecución Shared: `ClienteOnboardingService._insertar_secuencias_codigo(session, cliente_id, empresa_id)`.
- Ejecución Dedicated: paso `seed_codigo_secuencias` en `dedicated_tenant_seed_adapters`.
- Idempotente por `(cliente_id, sequence_key, scope_fingerprint)`.

**No requiere edición manual al crecer el catálogo:** una CFG nueva con scope TENANT/EMPRESA se incorpora al eager automáticamente.

### 3.2 Capa lazy — ya existente

- `AllocationCoordinator.ensure_row` crea la fila faltante con defaults del catálogo.
- Cubre las secuencias CFG de scope ALMACEN/PUNTO_VENTA (4) y las EMPRESA-scoped de empresas/almacenes/PV creados después del onboarding.

**Conclusión:** el "seed oficial" está **operativo** vía eager (todas las CFG resolubles) + lazy (ALMACEN/PV y entidades posteriores).

---

## 4. Especificación del generador (cuando se apruebe)

Si se decide un seed explícito/ampliado, deberá cumplir:

| Requisito | Detalle |
|-----------|---------|
| **Entrada** | `cliente_id`, `empresa_id` (sede), lista de `sequence_key` a sembrar |
| **Iteración** | Sobre `SequenceCatalog.all_definitions()` filtrando `store_type == CFG` |
| **Filtro fiscal** | Excluir `store_type == FISCAL` (2 entradas) |
| **Scope → columnas** | TENANT: `empresa_id=NULL`; EMPRESA: `empresa_id` sede; ALMACEN/PV: **no** en seed eager (lazy) |
| **Fingerprint** | `compute_scope_fingerprint(scope_type, empresa_id=…)` |
| **Valores** | `prefijo=default_prefix`, `separador=default_separator`, `longitud_numero=default_padding`, `numero_inicial`, `ultimo_numero=0` (**`ultimo_numero=1` para `org_empresa` TENANT**; BR-BOOT-04), `es_activo=1` |
| **Idempotencia** | `insert_secuencia` es no-op si la fila ya existe |
| **Transacción** | Misma UoW del onboarding (rollback total si falla) |
| **Modo** | Idéntico Shared/Dedicated (solo cambia el store) |

**Regla SEED-GEN-01:** el generador **no** siembra ALMACEN ni PUNTO_VENTA en onboarding (no existen aún almacenes/PV al crear el tenant); esas quedan lazy.

**Regla SEED-GEN-02:** el generador **no** siembra secuencias EMPRESA para empresas que aún no existen; una empresa nueva dispara su propio sub-seed o lazy.

---

## 5. Alcance del seed eager — RESUELTO (F17D)

> Las opciones A/B/C que planteaba esta sección quedaron **superadas**. F17D fijó un criterio determinista basado en el scope, no en un subconjunto elegido a mano.

**Criterio oficial (F17D):** el seed eager cubre **todas** las secuencias CFG cuyo `scope_fingerprint` se resuelve en onboarding — scope **TENANT** o **EMPRESA**. La selección se **deriva** del catálogo; no hay lista manual ni conteo fijo.

| Grupo | Poblado | Filas (empresa sede) |
|-------|---------|----------------------|
| CFG scope TENANT | Eager | 1 |
| CFG scope EMPRESA | Eager | 56 |
| CFG scope ALMACEN/PUNTO_VENTA | Lazy (`ensure_row`) | 0 en onboarding |
| FISCAL | No en cfg | 0 |

**Total eager para una empresa = 57** (derivado). Motivo del criterio: no se pueden sembrar ALMACEN/PUNTO_VENTA en onboarding porque su fingerprint requiere un almacén/punto de venta inexistente en esa fase; forzarlas con `almacen_id`/`punto_venta_id = NULL` generaría filas huérfanas y rompería la semántica de scopes.

**Regla SEED-SCOPE-01 (F17D):** el eager = catálogo filtrado por `store_type == CFG` y `scope_type ∈ {TENANT, EMPRESA}`. Agregar una CFG resoluble al catálogo la incorpora al seed automáticamente; agregar una ALMACEN/PV la deja lazy. **Sin** edición manual de listas.

**Regla SEED-SCOPE-02 (F17D):** `row_expectations` en `tenant_seed_profiles` se deriva de `len(EAGER_SEQUENCE_KEYS)`; no se mantiene un número a mano.

---

## 6. Formato de entrega del seed (futuro)

**No** se generará SQL con INSERT literales. El seed oficial se mantiene **programático** (derivado del catálogo), por estas razones:

| Motivo | Detalle |
|--------|---------|
| Fuente única | El SQL literal duplicaría prefijos/padding → riesgo de divergencia |
| Fingerprint | Debe calcularse con la función oficial, no hardcodearse |
| Multiempresa | El `empresa_id` es dinámico por tenant/empresa |
| Idempotencia | El repositorio ya la garantiza |

**Regla SEED-FMT-01:** el "seed oficial" = ejecución programática sobre el catálogo dentro del onboarding, **no** un archivo `.sql` de INSERTs. Si se requiere un dump SQL para inspección, será **generado** desde el catálogo, no mantenido a mano.

---

## 7. Validaciones a incluir cuando se genere/expanda el seed

| Test | Objetivo |
|------|----------|
| Conteo eager | Filas cfg tras onboarding = tamaño de `ONBOARDING_SEQUENCE_SEEDS` |
| Scope correcto | `org_empresa` TENANT; resto EMPRESA con `empresa_id` sede |
| Contador `org_empresa` | Tras onboarding: `ultimo_numero = 1`; primer `allocate` → `EMP002` |
| Sin fiscal | Ninguna fila con `sequence_key` F3 en cfg |
| Idempotencia | Re-ejecutar seed no duplica |
| Fingerprint | `scope_fingerprint` coincide con `compute_scope_fingerprint` |
| Paridad Shared/Dedicated | Mismas filas en ambos modos |
| Lazy | Primer `allocate` de entidad no sembrada crea fila con defaults del catálogo |

**Regla SEED-TEST-01:** los tests de F17 Ola 0 (`test_codigo_engine_ola0.py`) ya cubren catálogo, fingerprint y seed subset; una eventual ampliación del seed debe extender estos tests, no crear un framework nuevo.

---

## 8. Secuencia de trabajo posterior a la aprobación

| Paso | Acción | Estado |
|------|--------|--------|
| 1 | Aprobar `01`–`03` (configuración oficial) | ✅ |
| 2 | Fijar criterio de alcance eager (scope resoluble) | ✅ F17D |
| 3 | Derivar `ONBOARDING_SEQUENCE_SEEDS` + `row_expectations` del catálogo | ✅ F17D |
| 4 | Extender tests de conteo/scope (57, excluye ALMACEN/PV/FISCAL) | ✅ F17D |
| 5 | (Opcional) generador de dump SQL desde catálogo | ⛔ (no requerido) |
| 6 | Validar onboarding Shared y Dedicated end-to-end | ✅ tests unitarios |

---

## 9. Confirmaciones de alcance de esta fase

| Restricción | Cumplido |
|-------------|----------|
| No se generó SQL | ✅ |
| No se generaron INSERTs | ✅ |
| No se modificó código | ✅ |
| No se modificó el `SequenceCatalog` | ✅ |
| No se modificó V010 | ✅ |
| No se modificó el Gateway | ✅ |
| No se crearon commits | ✅ |
| Solo documentación técnica | ✅ |

---

## 10. Resultado

El seed oficial está **implementado** (F17D): derivado del `SequenceCatalog`, dos capas (eager = todas las CFG con scope TENANT/EMPRESA; lazy = ALMACEN/PV y entidades posteriores), idéntico en Shared y Dedicated, idempotente, sin SQL literal. El alcance eager ya **no** depende de una elección manual: se determina por scope resoluble (§5).

---

*Configuración en `01`. Prefijos en `02`. Reglas de poblado en `03`.*
