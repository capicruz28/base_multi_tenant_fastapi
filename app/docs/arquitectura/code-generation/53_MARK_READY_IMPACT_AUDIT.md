# 53 — F17K: Auditoría de impacto de eliminar el Step MARK_READY

> Fase **F17K**. 100% auditoría de impacto. **No** se modificó ningún archivo del
> proyecto (código, SQL, bootstrap, onboarding, manifests, tests, docs existentes).
> **No** se propone implementación. Toda afirmación cita `archivo:línea`.

## 0. Metodología

Búsqueda exhaustiva (case-insensitive) en todo el repositorio de:
`MARK_READY`, `mark_ready`, `ProvisioningStepCode.MARK_READY`,
`transition_run_to_ready`, `ready_at`, `ProvisioningState.READY`, `SAGA_STEP_ORDER`,
lógica de progreso/conteo de steps y emisión de métricas/eventos.

Superficies revisadas: Backend, Bootstrap/DDL, Provisioning, APIs, DTOs/Responses,
Queries, Repositorios, Contratos UI, Auditoría, Logging, Métricas, Eventos,
Redispatch/Retry, Compensación, Documentación técnica.

## 1. Mapa de dependencias de MARK_READY (dónde vive el concepto)

### 1.1 Fuente de verdad (enum + orden)
- `app/modules/tenant/application/provisioning/provisioning_step_code.py`
  - `ProvisioningStepCode.MARK_READY = "mark_ready"` (`:15`)
  - `SAGA_STEP_ORDER` incluye MARK_READY como paso 10 (`:32`)
  - `SAGA_ORDER_BY_CODE` (`:35-37`) deriva de lo anterior.

### 1.2 Orquestación / activación / compensación (lógica)
- `dedicated_provisioning_orchestrator.py`: ruta MARK_READY (`:394-395`),
  `_step_activation` → `mark_ready` (`:655-656`), mapa de error (`:745`), y el
  bucle genérico (`:284,290,299`).
- `dedicated_activation_service.py`: método `mark_ready` (`:108-162`), `step_code`
  en resultados (`:124,137,159`), `_S10_MARKER_PREFIX="ready_run"` (`:40`).
- `dedicated_provisioning_compensation_service.py`: `_COMPENSATION_STEP_ORDER`
  incluye MARK_READY (`:60`) y una rama **no-op** (`:210-212`).
- `tenant_provisioning_state_service.py`: `transition_run_to_ready` fija
  `current_step_code = MARK_READY.value` (`:298`).

### 1.3 Derivados (sin lógica propia)
- `tenant_provisioning_step_queries_core.py`: `build_initial_step_rows` genera las
  filas **desde `SAGA_STEP_ORDER`** (`:33-51`, docstring "los 10 steps").
- `provisioning_status_read.py`: DTO `DedicatedProvisioningStatusSnapshot` con
  `steps: List[...]`, `current_step`, `ready_at` (`:22-40`) — **no** cuenta ni
  calcula progreso; expone la lista tal cual.

### 1.4 Persistencia (BD)
- `app/bootstrap_v2/01_schema/V032__tenant_provisioning_state.sql`:
  `CK_tps_step_code` incluye `'mark_ready'` (`:90-102`); comentario "S1–S10"
  (`:56`). Columna `ready_at` en el RUN (`:27`).
- `app/infrastructure/database/tables.py`: espejo ORM del CHECK con `'mark_ready'`
  (`:155`) y columna `ready_at` (`:111`).

### 1.5 Contratos públicos (consumidores externos)
- `docs/contracts/DEDICATED_PROVISIONING_API_CONTRACT.md`: §9.1 expone
  `mark_ready | S10 | Tenant Ready` (`:305`); flujo "S10 Mark tenant Ready"
  (`:63`); evento `dedicated.provisioning.ready | S10` (`:518`).
- `docs/contracts/PLATFORM_ADMIN_TENANT_ONBOARDING_UI_CONTRACT.md`: §5 tabla de
  steps incluye `mark_ready` (`:156`); §8.3 "Timeline steps | **10 steps**"
  (`:354`); §7.5 "Progreso | Todos los steps `completed`" (`:299`); §7.4
  "Renderizar `steps[]` … resaltar `current_step`" (`:287`).

### 1.6 Observabilidad (spec, no runtime)
- `docs/implementation/HYBRID_F4_PROVISIONING_METRICS_MANIFEST.json`:
  `dedicated.provisioning.ready` "when: S10 mark_ready" (`:22-23`);
  `dedicated.provisioning.step.completed` por step (`:14-19`).
- **No existe emisión real en `app/`**: grep de `dedicated.provisioning.ready` /
  `provisioning.step.completed` en `app/` → **0 coincidencias**. El manifiesto es
  especificación, no código emisor.

### 1.7 Tests / scripts
- `tests/unit/test_f4_01_provisioning_domain_types.py`
- `tests/unit/test_f4_02_provisioning_state_service.py`
- `tests/unit/test_f4_08_dedicated_orchestrator.py`
- `tests/unit/test_f4_09_orchestrator_activation.py`
- `tests/unit/test_f4_09_dedicated_activation.py`
- `tests/integration/test_hybrid_provisioning_e2e.py`
- `tests/integration/helpers/provisioning_e2e_harness.py`
- `scripts/validate_f4_provisioning_e2e.py`

## 2. Respuesta 4 — ¿Lógica que calcula progreso por número de steps?

- **Backend:** **NO.** No existe cálculo numérico tipo "8/10". El grep de
  `total_steps|completed_steps|step_count|progress|/ 10|len(...STEP)` en `app/` no
  arroja lógica de progreso de provisioning (solo falsos positivos de fórmulas
  ERP). `provisioning_status_read.py` expone `steps[]` sin contarlos.
- **Contrato Frontend:** **SÍ (declarativo).** UI contract §7.5 (`:299`)
  "Progreso: todos los steps `completed`" y §8.3 (`:354`) "10 steps". El progreso
  es responsabilidad del FE sobre `steps[]`/`current_step`, no un contador backend.
- **Nota de estado actual:** por el defecto F17I (`mark_ready` queda RUNNING), el
  criterio FE "todos los steps completed" **hoy nunca se cumple** aunque el run esté
  READY → inconsistencia preexistente del indicador de progreso.

## 3. Respuesta 10 — Archivos a modificar si MARK_READY desapareciera (clasificados)

### Alto impacto (fuente de verdad + contratos públicos + persistencia)
| Archivo | Motivo |
|---|---|
| `provisioning_step_code.py` | Enum `MARK_READY` + `SAGA_STEP_ORDER` (fuente de verdad) |
| `V032__tenant_provisioning_state.sql` | `CK_tps_step_code` incluye `'mark_ready'`; datos existentes con fila `mark_ready` |
| `tables.py` | Espejo ORM del CHECK (`:155`) |
| `DEDICATED_PROVISIONING_API_CONTRACT.md` | §9.1 (código expuesto), §5, eventos — contrato **v1 público** |
| `PLATFORM_ADMIN_TENANT_ONBOARDING_UI_CONTRACT.md` | §5, §8.3 "10 steps", §7.5 progreso — consumido por FE |

### Medio impacto (lógica de orquestación/activación/compensación + métricas)
| Archivo | Motivo |
|---|---|
| `dedicated_provisioning_orchestrator.py` | `_execute_step`/`_step_activation`/mapa de error |
| `dedicated_activation_service.py` | `mark_ready` pasaría de "step" a transición terminal |
| `dedicated_provisioning_compensation_service.py` | `_COMPENSATION_STEP_ORDER` + rama no-op |
| `tenant_provisioning_state_service.py` | `current_step_code=MARK_READY` en `transition_run_to_ready` |
| `HYBRID_F4_PROVISIONING_METRICS_MANIFEST.json` | Evento/serie por step |

### Bajo impacto (derivados / tests / scripts)
| Archivo | Motivo |
|---|---|
| `tenant_provisioning_step_queries_core.py` | Auto-deriva de `SAGA_STEP_ORDER` (solo docstring "10 steps") |
| `provisioning_status_read.py` | Dinámico; sin cambios estructurales |
| `test_f4_01/02/08/09_*`, `test_hybrid_provisioning_e2e.py`, `provisioning_e2e_harness.py`, `scripts/validate_f4_provisioning_e2e.py` | Aserciones sobre 10 steps / mark_ready |

## 4. Respuesta 11 — ¿Refactor local (A) o cambio transversal (B)?

**B — cambio transversal.** Evidencia: la eliminación toca simultáneamente
(1) la fuente de verdad (`provisioning_step_code.py`), (2) la persistencia/DDL
(`V032` CHECK + filas existentes) y su espejo ORM (`tables.py`), (3) **dos**
contratos públicos v1 (API §9.1 + UI "10 steps"), (4) la especificación de
métricas, (5) lógica de orquestación/activación/compensación/estado, y (6) ~8
archivos de tests/harness/scripts. Abarca backend + persistencia + contratos +
frontend + observabilidad + tests. No es aislable a un único módulo.

Detalle de consumidores en `54`; compatibilidad en `55`; veredicto en `56`.
