# F17B — Ajustes de implementación recomendados

**Fase:** F17B (documentación de plan). Complementa `28`, `29`, `30`.
**Naturaleza:** recomendaciones **no bloqueantes** para robustez e higiene antes/durante la integración ORG–INV.

Prioridad: **P1** = hacer antes de ORG/INV · **P2** = durante ORG/INV · **P3** = evolución futura.

> **Estado F17C (2026-07-03):** los ajustes **P1 (ADJ-01, ADJ-03, ADJ-05, ADJ-06) están IMPLEMENTADOS**. Los P2/P3 permanecen como plan. Detalle por ítem abajo.

> **Estado F17D (2026-07-03):** el subconjunto eager dejó de ser una lista manual. Ahora se **deriva** del `SequenceCatalog`: todas las CFG con scope resoluble en onboarding (TENANT/EMPRESA) = 57 filas para una empresa. Las ALMACEN/PUNTO_VENTA quedan lazy. Esto **refuerza** ADJ-01 y ADJ-05 (ver notas F17D en cada uno).

---

## ADJ-01 — Derivar `onboarding_seed` del `SequenceCatalog` (P1) — ✅ IMPLEMENTADO F17C

**Problema:** `onboarding_seed.py` re-declaraba `prefijo`, `longitud_numero`, `separador`, `scope_type`, que ya viven en el `SequenceCatalog`. Riesgo de drift (dos fuentes de verdad para el mismo prefijo).

**Implementación F17C:** `onboarding_seed.py` deriva cada `OnboardingSequenceSeed` del catálogo vía `OnboardingSequenceSeed.from_definition(...)`. Para romper el ciclo de import, `CATALOG_VERSION` se define ahora en `sequence_catalog.py` (fuente natural) y se re-exporta desde `onboarding_seed.py`.

**Refuerzo F17D:** se eliminó incluso la lista manual de keys. El subconjunto eager se **calcula** filtrando el catálogo (store CFG + scope TENANT/EMPRESA); `EAGER_SEQUENCE_KEYS` pasa a ser una **vista derivada** (no una tupla mantenida a mano).

```python
def _onboarding_definitions():
    return tuple(
        d for d in SequenceCatalog.all_definitions()
        if d.store_type == StoreType.CFG
        and d.scope_type in ONBOARDING_RESOLVABLE_SCOPES  # {TENANT, EMPRESA}
    )

ONBOARDING_SEQUENCE_SEEDS = tuple(
    OnboardingSequenceSeed.from_definition(d) for d in _onboarding_definitions()
)
EAGER_SEQUENCE_KEYS = tuple(s.sequence_key for s in ONBOARDING_SEQUENCE_SEEDS)
```

**Resultado:** una sola fuente de verdad; imposible que seed y runtime usen prefijos distintos, y sin lista de keys mantenida a mano. Cubierto por `test_codigo_engine_p1_consolidation.py::TestAdj01*` y `test_codigo_engine_f17d_full_cfg_seed.py`.
**Owner:** Motor.

---

## ADJ-02 — Converger la vía de escritura del seed con `ensure_row` (P2)

**Problema:** existen dos rutas de inserción a `cfg_codigo_secuencia` (repo en seed, store en runtime). Consistentes hoy, pero mantenidas por separado.

**Ajuste propuesto:** que `_insertar_secuencias_codigo` delegue en `CfgSequenceStore.ensure_row(session, scope_key, defn)` por cada key eager, en lugar de `CfgCodigoSecuenciaRepository.insert_secuencia`.

**Beneficio:** una única lógica de creación (fingerprint + defaults) para seed y runtime.
**Riesgo:** `ensure_row` debe ser idempotente y aceptar la sesión del onboarding (ya lo es). Validar comportamiento en TX Shared y en pasos Dedicated.
**Owner:** Motor + Bootstrap.

---

## ADJ-03 — Blindar `CfgCodigoSecuenciaRepository` para Dedicated (P1, INC-09) — ✅ IMPLEMENTADO F17C

**Problema:** la ruta **sin `session`** del repositorio usaba `DatabaseConnection.ADMIN`. En Dedicated eso apunta al control-plane, que no contiene el cfg del tenant.

**Implementación F17C:** las tres operaciones de **escritura** (`insert_secuencia`, `update_ultimo_numero`, `update_secuencia`) exigen ahora `session` explícita vía `_assert_write_session(...)` → `ServiceError` (`CFG_SECUENCIA_WRITE_REQUIRES_SESSION`) si es `None`. Se eliminaron las ramas de escritura vía `execute_insert/execute_update` con ADMIN (imports retirados). Las **lecturas** conservan la ruta ADMIN sin sesión para listados administrativos del control-plane (comportamiento y tests existentes intactos). El runtime del motor escribe solo vía `CfgSequenceStore` (session-driven).

**Resultado:** Dedicated no puede escribir accidentalmente en el Control Plane; onboarding sigue con sesión explícita. Cubierto por `test_codigo_engine_p1_consolidation.py::TestAdj03*` y `test_repository_has_no_adminless_write_path`.
**Owner:** Infra/Bootstrap.

---

## ADJ-04 — Alta de empresa posterior al onboarding (P2)

**Problema:** el seed eager solo cubre la **empresa sede** (`EMP001`). Al crear una segunda empresa, sus secuencias EMPRESA-scoped no existen hasta el primer uso.

**Ajuste propuesto:** confiar en **lazy creation** (ya cubre el caso) y documentarlo explícitamente; opcionalmente, un hook de provisioning "crear empresa" que invoque el mismo subconjunto eager para la nueva empresa (paridad de UX con la sede).

**Beneficio:** consistencia multi-empresa sin sorpresas.
**Owner:** Bootstrap (hook) / Motor (lazy).

---

## ADJ-05 — Centralizar la lista eager (P1) — ✅ IMPLEMENTADO F17C

**Problema:** ampliar el eager exigía tocar 3 lugares: `onboarding_seed.py`, `row_expectations` (`tenant_seed_profiles`) y los tests.

**Implementación F17C:** `EAGER_SEQUENCE_KEYS` (en `onboarding_seed.py`) es la **única** definición del subconjunto eager. `ONBOARDING_SEQUENCE_SEEDS` y `SECUENCIAS_CODIGO` derivan de ella.

**Refuerzo F17D:** ya **no hay que editar ninguna lista** para ampliar el eager. La selección se deriva del catálogo por scope: una CFG nueva con scope TENANT/EMPRESA entra al eager automáticamente; una ALMACEN/PUNTO_VENTA queda lazy. `EAGER_SEQUENCE_KEYS` es ahora una vista derivada.

**Resultado:** cero puntos de edición manual para el conjunto eager. Cubierto por `test_codigo_engine_p1_consolidation.py::TestAdj05*` y `test_codigo_engine_f17d_full_cfg_seed.py`.
**Owner:** Bootstrap + Motor.

---

## ADJ-06 — Consistencia del conteo de verificación Dedicated (P1) — ✅ IMPLEMENTADO F17C

**Problema/observación:** `row_expectations` usaba `("cfg_codigo_secuencia", len(SECUENCIAS_CODIGO))`, con un número acoplado indirectamente.

**Implementación F17C:** `tenant_seed_profiles._row_expectations_for_profile` importa `EAGER_SEQUENCE_KEYS` y usa `len(EAGER_SEQUENCE_KEYS)`; el test dedicado (`test_f4_07_*`) también deriva de esa constante. Sin números hardcodeados. Cubierto por `test_codigo_engine_p1_consolidation.py::test_adj06_row_expectations_derive_from_eager_keys`.
**Owner:** Bootstrap.

---

## ADJ-07 — Paridad de `auth_config` Shared vs Dedicated (P2, fuera del motor)

**Observación:** el onboarding Shared ejecuta `_insertar_auth_config_si_no_existe` (paso 7); el perfil de seed Dedicated **no** lista un paso equivalente. Verificar que `cliente_auth_config` se cree en Dedicated en otra etapa (S6/provisioning) para no dejar tenants Dedicated sin auth config.

**Nota:** no afecta al Motor de Códigos; se registra por completitud de la auditoría del onboarding.
**Owner:** Bootstrap/Auth.

---

## Resumen y secuencia sugerida

| ID | Prioridad | Owner | Estado |
|----|-----------|-------|--------|
| ADJ-01 | P1 | Motor | ✅ Implementado F17C |
| ADJ-03 | P1 | Infra | ✅ Implementado F17C |
| ADJ-05 | P1 | Bootstrap+Motor | ✅ Implementado F17C |
| ADJ-06 | P1 | Bootstrap | ✅ Implementado F17C |
| ADJ-02 | P2 | Motor+Bootstrap | Pendiente (durante ORG/INV) |
| ADJ-04 | P2 | Bootstrap+Motor | Pendiente (durante ORG/INV) |
| ADJ-07 | P2 | Bootstrap/Auth | Pendiente (fuera del motor) |

**Los P1 quedan consolidados en F17C.** El motor tiene una única fuente de verdad (`SequenceCatalog` + `EAGER_SEQUENCE_KEYS`) y las escrituras a `cfg_codigo_secuencia` están blindadas. Queda listo para iniciar la integración ORG. Los P2/P3 se abordarán durante ORG/INV.

---

*Aprobación ejecutiva en `32`.*
