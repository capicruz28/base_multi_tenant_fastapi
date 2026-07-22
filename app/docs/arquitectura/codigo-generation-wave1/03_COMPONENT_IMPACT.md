# Motor de Códigos — Impacto por componente (policy → cfg)

**Estado:** Diseño — sin implementación  
**Fecha:** 2026-07-11

---

## 1. Resumen de dependencias AS-IS

### 1.1 ¿Quién usa PolicyResolver hoy?

| Componente | Uso | Input policy |
|------------|-----|--------------|
| **`CodigoGeneracionGateway.allocate`** | Decide AUTO vs manual | `defn.policy` vía PolicyResolver |
| **`CodigoGeneracionGateway.preview`** | Valida contexto (modo no usado) | `defn.policy` |
| **`CodigoGeneracionGateway.validate_manual`** | Valida manual permitido | `defn.policy` |
| **Tests `test_codigo_engine_ola0`** | Unit PolicyResolver | `SequenceCatalog.get(...).policy` |

**No hay otros callers** de PolicyResolver en producción.

### 1.2 ¿Quién depende de `SequenceDefinition.policy`?

| Componente | Uso |
|------------|-----|
| `PolicyResolver.resolve(defn, ...)` | **Directo** — lectura principal |
| `SequenceDefinition.consumes_counter_on_allocate` | Property `@property` |
| `sequence_catalog._def()` | Deriva `allow_manual`, `supports_import` |
| `onboarding_seed.OnboardingSequenceSeed.from_definition` | **No** copia policy hoy |
| Documentación F15A / matriz catálogo | Referencia |

### 1.3 ¿Quién NO usa policy directamente?

| Componente | Depende de |
|------------|------------|
| `AllocationCoordinator` | `defn` store_type, formatter; **no policy** |
| `ScopeResolver` | `defn.scope_type` |
| `CodeValidator` | `defn.validator_profile` |
| `CodeFormatter` | perfiles catálogo |
| `CfgSequenceStore` | defaults catálogo en ensure_row |
| `CounterAlignmentService` | alignment catálogo |
| `OrgCodigoGenerationService` | gateway opaco — **sin policy** |

---

## 2. Matriz de cambio por componente

| Componente | Cambio | Severidad | Fase |
|------------|--------|-----------|------|
| **`cfg_codigo_secuencia` (DDL)** | ADD `generation_policy` + CHECK | Alta | P0 |
| **`CfgCodigoSecuenciaTable`** | Columna ORM | Alta | P0 |
| **`CfgSequenceRow`** | Campo `generation_policy` | Alta | P0 |
| **`CfgSequenceStore`** | ensure_row, from_dict, lazy INSERT | Alta | P1 |
| **`CfgCodigoSecuenciaRepository.insert_secuencia`** | Param + INSERT | Alta | P1 |
| **`OnboardingSequenceSeed`** | Campo `generation_policy` | Media | P1 |
| **`onboarding_seed.from_definition`** | Copiar default del catálogo | Media | P1 |
| **`cfg_codigo_onboarding_seed`** | Propagar a repo | Media | P1 |
| **`PolicyResolver`** | Firma `(policy, context)` | Alta | P2 |
| **`CodigoGeneracionGateway`** | Cargar cfg antes de resolve | **Alta** | P2 |
| **`SequenceDefinition`** | Rename `policy` → `default_generation_policy` | Media | P2 |
| **`SequenceCatalog`** | Renombre en `_def()` | Media | P2 |
| **`AllocationCoordinator`** | Opcional: recibir cfg_row para format | Baja | P3 |
| **`PreviewReader`** | Sin cambio lógico | Baja | — |
| **`OrgCodigoGenerationService`** | **Sin cambio** | Nula | — |
| **Servicios ORG** | **Sin cambio** hasta Ola 1.2 | Nula | — |
| **Bootstrap V2 Python** | Seed explícito policy | Media | P1 |
| **Repair script (nuevo)** | Backfill tenants existentes | Alta | P1 |

---

## 3. CodigoGeneracionGateway — cambios conceptuales

### AS-IS

```python
defn = catalog.get(key)
mode = PolicyResolver.resolve(defn, context)
scope = ScopeResolver.resolve(defn, context)
# allocate branch...
```

### TO-BE

```python
defn = catalog.get(key)
scope = ScopeResolver.resolve(defn, context)
cfg_row = await CfgSequenceStore.get_by_scope(session, scope)
if cfg_row is None:
    # steady-state: error; lazy paths: ensure_row with catalog default policy
cfg_row = _require_active(cfg_row)
mode = PolicyResolver.resolve(cfg_row.generation_policy, context)
# allocate branch uses cfg_row for format params (already via increment_and_get)
```

**`validate_manual`:** cargar cfg (o recibir policy explícita) antes de resolve.

**Impacto API pública gateway:** **Sin cambio de firma** — cambio interno.

---

## 4. AllocationCoordinator — cambios conceptuales

| Aspecto | Cambio |
|---------|--------|
| Firma `allocate_next` | **Sin cambio obligatorio** |
| Lógica policy | **Ninguna** — gateway elige rama antes de llamar |
| Formato código | Ya usa `row.prefijo` de cfg en CFG path |
| `accept_manual` | Sin cambio |
| Property `consumes_counter_on_allocate` | Mover decisión a gateway usando cfg policy |

**Veredicto:** AllocationCoordinator **casi sin cambios** — policy es responsabilidad del gateway.

---

## 5. PolicyResolver — transformación

| Pregunta | Respuesta |
|----------|-----------|
| ¿Desaparece? | **No** |
| ¿Se transforma? | **Sí** — desacoplar de `SequenceDefinition` |
| ¿Delega? | Gateway delega; resolver puro sin I/O |

**Nueva firma propuesta:**

```python
PolicyResolver.resolve(
    generation_policy: CodePolicy,
    context: GenerationContext,
) -> PolicyMode
```

**Compatibilidad transitoria:**

```python
def resolve_from_definition(defn, context):
    # deprecated — solo tests migración
    return PolicyResolver.resolve(defn.default_generation_policy, context)
```

---

## 6. SequenceCatalog — qué permanece vs qué evoluciona

### Permanece dependiendo del catálogo (runtime)

| Consumidor | Campo |
|------------|-------|
| Gateway | `sequence_key` exists |
| ScopeResolver | `scope_type` |
| AllocationCoordinator | `store_type`, formatter/parser profiles |
| CodeValidator | `validator_profile`, `max_output_length` |
| Lazy ensure | `default_prefix`, `default_padding`, `default_separator`, `numero_inicial` |
| Preview | `supports_preview` |

### Deja de usarse en runtime allocate (steady-state)

| Campo | Reemplazo |
|-------|-----------|
| `policy` / `default_generation_policy` | `cfg.generation_policy` |
| `allow_manual` (derivado) | derivar de cfg policy |
| `supports_import` (derivado) | derivar de cfg policy + alignment |

---

## 7. Impacto tests

| Suite | Impacto |
|-------|---------|
| `test_codigo_engine_ola0.py` | PolicyResolver tests → pasar `CodePolicy` directo |
| `test_codigo_engine_f17d_full_cfg_seed.py` | Assert seed incluye policy |
| `test_org_codigo_generation_service.py` | **Sin cambio** (mock gateway) |
| Tests integración onboarding | Row count + column policy |
| Nuevos tests | Gateway lee cfg policy; backfill; MANUAL_ONLY |

---

## 8. Impacto repair scripts

| Escenario | Acción |
|-----------|--------|
| Tenants con cfg sin columna | Migración DDL + UPDATE backfill |
| Drift policy vs catálogo | Script `repair_cfg_generation_policy` idempotente |
| EMP001 / onboarding legacy | Backfill por `sequence_key` desde catálogo default |

**No modificar** `legacy_tenant_rbac_repair` — script cfg dedicado.

---

## 9. Impacto ORG / INV futuro

| Área | Impacto |
|------|---------|
| **ORG Ola 1.1** (`OrgCodigoGenerationService`) | Ninguno — ya implementado |
| **ORG Ola 1.2+ cargo** | Allocate usará cfg policy automáticamente vía gateway |
| **INV Ola futura** | Documentos AUTO_REQUIRED leen cfg — tenant podría teóricamente relajar (gobernanza prohibida) |
| **OpenAPI ORG** | Sin cambio |
| **Contrato funcional 04** | Sigue válido — semántica AUTO_DEFAULT por entidad |

---

## 10. Veredicto impacto

Cambio **concentrado** en: DDL, seed/bootstrap, `CfgSequenceStore`, `PolicyResolver`, `CodigoGeneracionGateway`.  
**AllocationCoordinator** y **ORG infra** permanecen estables.
