# 44 — F17I: Runtime State Trace (flujo completo S1–S10)

> Fase **F17I**. Auditoría 100% de solo lectura. **No** se modificó código, SQL,
> bootstrap, onboarding, tests ni manifests. **No** se implementa corrección.
> Toda afirmación cita `archivo:línea`.

## 0. Alcance

Reconstrucción determinista, derivada **solo del código**, del flujo desde
`DedicatedProvisioningOrchestrator.handle_job()` hasta el log
`"Tenant dedicated ready"` y el `ConflictError` posterior
(`PROVISIONING_RUN_NOT_ACTIVE`, "No se puede mutar steps cuando el run no está en
provisioning.").

Archivos del flujo:
- `app/modules/tenant/application/services/dedicated_provisioning_orchestrator.py`
- `app/infrastructure/provisioning/dedicated_activation_service.py`
- `app/modules/tenant/application/services/tenant_provisioning_state_service.py`
- `app/modules/tenant/application/provisioning/provisioning_step_code.py`
- `app/modules/tenant/application/provisioning/provisioning_transition_rules.py`

## 1. Orden de la saga (fuente única)

`provisioning_step_code.py:22-33` — `SAGA_STEP_ORDER` (S1→S10):

```
S1 registry
S2 storage_allocation
S3 create_database
S4 apply_schema_erp
S5 apply_schema_rbac
S6 apply_catalogs
S7 seed_tenant
S8 register_metadata
S9 activate_routing
S10 mark_ready        ← ÚLTIMO step
```

## 2. Bucle genérico por step (el patrón que causa el fallo)

`dedicated_provisioning_orchestrator.py:229-304`. Para **cada** step (excepto el
bloque bootstrap S4/S5 que tiene rama propia):

```
284  await self._state.mark_step_running(step_code)      # exige run=PROVISIONING
289  try:
290      marker = await self._execute_step(step_code)     # cuerpo del step
295  except Exception as exc:
296      await self._fail_step_and_run(...); return
299  await self._state.mark_step_completed(step_code, marker)  # exige run=PROVISIONING
```

Puntos críticos:
- `mark_step_running` (284) y `mark_step_completed` (299) pasan **ambos** por el
  guard de run=PROVISIONING (ver §4).
- La línea **299 está FUERA del `try/except`** de 289-297 (que solo envuelve
  `_execute_step` en 290). Por tanto, una excepción de `mark_step_completed` **no**
  la captura `_fail_step_and_run`: se propaga a `handle_job` y se re-lanza
  (`:154-162`).

## 3. Qué hace el cuerpo del step MARK_READY (S10)

- `_execute_step` enruta MARK_READY a `_step_activation`
  (`orchestrator.py:394-395`).
- `_step_activation` (MARK_READY) llama `self._activation.mark_ready(request)`
  (`orchestrator.py:655-657`).
- `DedicatedActivationService.mark_ready` (`dedicated_activation_service.py:108-162`):
  1. Idempotencia: si el run ya está READY con el mismo run_id → skip
     (`:112-127`). En la primera pasada NO aplica (run=PROVISIONING).
  2. `self._state.transition_run_to_ready(...)` (`:130`) → **transiciona el run a
     READY** (mutación de `provisioning_run.status` y del cliente).
  3. `logger.info("Tenant dedicated ready ...")` (`:153-157`).
  4. Devuelve `DedicatedActivationStepResult(step_code=MARK_READY, ...)` (`:158-162`).

> El cuerpo del step **NO** cierra el step; solo transiciona el run y loguea. El
> cierre del step (`mark_step_completed`) lo hace el bucle en `orchestrator.py:299`
> **después**.

## 4. La máquina de estados que gobierna las mutaciones

`tenant_provisioning_state_service._transition_step` (`:457-550`) — usado por
`mark_step_running/completed/failed/skipped`. Guard duro (`:485-491`):

```
485  if self._parse_run_state(locked) != ProvisioningState.PROVISIONING:
486      raise ConflictError(
488          detail="No se puede mutar steps cuando el run no está en provisioning.",
490          internal_code="PROVISIONING_RUN_NOT_ACTIVE",
491      )
```

`transition_run_to_ready` (`:264-320`): dentro de su propia `UnitOfWork` hace
`update_run_state(... target=READY ...)` (`:292-300`) y
`update_cliente_provisioning_state(READY)` (`:306-312`) y **COMMITEA**. No toca la
tabla de steps.

Reglas de estado del run (`provisioning_transition_rules.py:9-17`):
- `PROVISIONING → {READY, FAILED}`
- `READY → {}`  (**terminal**)
- `FAILED → {PROVISIONING}`

## 5. Traza de estados (S9 → S10 → error)

| Momento | Acción (archivo:línea) | run.status | step MARK_READY |
|---|---|---|---|
| tras S9 | `mark_step_completed(ACTIVATE_ROUTING)` (orch:299) | PROVISIONING | PENDING |
| T1 | `mark_step_running(MARK_READY)` (orch:284 → `_transition_step` RUNNING) — guard OK | PROVISIONING | PENDING→RUNNING |
| T2 | `_execute_step(MARK_READY)` (orch:290 → 656) | PROVISIONING | RUNNING |
| T3 | `transition_run_to_ready` (activation:130 → state:292/306) — **COMMIT** | **PROVISIONING→READY** | RUNNING |
| T4 | `logger.info("Tenant dedicated ready")` (activation:153) | READY | RUNNING |
| T5 | `mark_step_completed(MARK_READY)` (orch:299 → `_transition_step` COMPLETED) — guard **:485** ve READY≠PROVISIONING | READY | RUNNING (no cambia) |
| T6 | **ConflictError PROVISIONING_RUN_NOT_ACTIVE** propaga (orch:299 fuera del try) → handle_job re-lanza (:162) | READY | RUNNING (atascado) |

## 6. Estado final observable

- `provisioning_run.status = READY` (commiteado en T3) — **terminal**.
- `provisioning_step[mark_ready].step_status = RUNNING` (nunca llega a COMPLETED).
- El cliente queda `provisioning_state = READY` (funcional).
- El job lanza `ConflictError`; **después** del log "Tenant dedicated ready".
- Un redispatch posterior: `handle_job` guard `:201` ve run=READY≠PROVISIONING →
  early-return "Saga noop" (`:208-213`). El step MARK_READY queda RUNNING de forma
  permanente (no hay auto-reparación).

Diagrama en `46_CALL_SEQUENCE.md`; análisis de la máquina de estados en
`45_STATE_MACHINE_ANALYSIS.md`; causa raíz en `47_ROOT_CAUSE_RUNTIME.md`.
