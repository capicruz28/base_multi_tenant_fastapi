# 46 — F17I: Call Sequence (Fase 2 + Fase 3)

> Fase F17I. Solo lectura.

## FASE 2 — Inventario de TODAS las llamadas que mutan estado

### 2.1 Mutaciones de STEP (pasan por `_transition_step`, guard run=PROVISIONING)

| # | Llamada | Archivo | Clase / método | Línea | step antes→después | requiere run |
|---|---|---|---|---|---|---|
| 1 | `mark_step_running` (bucle genérico) | orchestrator | `DedicatedProvisioningOrchestrator._handle_job_inner` | **284** | PENDING→RUNNING | PROVISIONING |
| 2 | `mark_step_completed` (bucle genérico) | orchestrator | `._handle_job_inner` | **299** | RUNNING→COMPLETED | PROVISIONING |
| 3 | `mark_step_running` (bootstrap) | orchestrator | `._run_bootstrap_block` | 477 | PENDING→RUNNING | PROVISIONING |
| 4 | `mark_step_running` (ERP) | orchestrator | `._mark_bootstrap_saga_steps` | 532 | PENDING→RUNNING | PROVISIONING |
| 5 | `mark_step_completed` (ERP) | orchestrator | `._mark_bootstrap_saga_steps` | 541 | RUNNING→COMPLETED | PROVISIONING |
| 6 | `mark_step_running` (RBAC) | orchestrator | `._mark_bootstrap_saga_steps` | 553 | PENDING→RUNNING | PROVISIONING |
| 7 | `mark_step_completed` (RBAC) | orchestrator | `._mark_bootstrap_saga_steps` | 562 | RUNNING→COMPLETED | PROVISIONING |
| 8 | `mark_step_failed` | orchestrator | `._fail_step_and_run` | 678 | RUNNING→FAILED | PROVISIONING |
| 9 | `_transition_step` (impl. + guard) | state_service | `TenantProvisioningStateService._transition_step` | 457-550 (guard **485-491**) | — | PROVISIONING |

### 2.2 Mutaciones de RUN

| # | Llamada | Archivo | Clase / método | Línea | run antes→después |
|---|---|---|---|---|---|
| 10 | `transition_run_to_ready` (invocación) | activation | `DedicatedActivationService.mark_ready` | **130** | PROVISIONING→READY |
| 11 | `transition_run_to_ready` (impl.) | state_service | `TenantProvisioningStateService.transition_run_to_ready` | 264-320 (update **292**, cliente **306**) | PROVISIONING→READY |
| 12 | `transition_run_to_failed` (invocación) | orchestrator | `._fail_step_and_run` | 685 | PROVISIONING→FAILED |
| 13 | `transition_run_to_failed` (impl.) | state_service | `.transition_run_to_failed` | 322-385 (update 353) | PROVISIONING→FAILED |
| 14 | `initialize_provisioning_run` | state_service | `.initialize_provisioning_run` | 86-174 (145/155) | ∅→PROVISIONING |
| 15 | `begin_retry_from_failed` | state_service | `.begin_retry_from_failed` | 176-262 (235/247) | FAILED→PROVISIONING |

### 2.3 Log "Tenant dedicated ready"

`dedicated_activation_service.py:153-157` — dentro de `mark_ready`, **después** de
`transition_run_to_ready` (:130) y **antes** de que el orquestador cierre el step
(orchestrator:299).

> No existen métodos `mark_ready`/`activate`/`complete_run`/`set_ready` fuera de los
> anteriores. `DedicatedActivationService.mark_ready` es el único trigger de READY;
> `TenantProvisioningStateService.transition_run_to_ready` es la única mutación real.

## FASE 3 — Timeline exacto (derivado solo del código)

```
run=PROVISIONING ; step[mark_ready]=PENDING           (tras cerrar S9)
        │
        ▼   orchestrator.py:284
mark_step_running(MARK_READY)
        │   _transition_step:485 guard → run=PROVISIONING ✅
        ▼
run=PROVISIONING ; step[mark_ready]=RUNNING
        │
        ▼   orchestrator.py:290 → 655-657
_execute_step(MARK_READY) → _step_activation → activation.mark_ready()
        │
        ▼   dedicated_activation_service.py:130 → state_service:292/306 (COMMIT)
transition_run_to_ready()
        │
        ▼
run=READY ; step[mark_ready]=RUNNING
        │
        ▼   dedicated_activation_service.py:153
LOG "Tenant dedicated ready"          ◀── aparece en el log
        │
        ▼   orchestrator.py:299   (FUERA del try/except 289-297)
mark_step_completed(MARK_READY)
        │   _transition_step:485 guard → run=READY ≠ PROVISIONING ❌
        ▼
ConflictError PROVISIONING_RUN_NOT_ACTIVE
"No se puede mutar steps cuando el run no está en provisioning."
        │
        ▼   propaga a handle_job:154-162 (re-raise) → dispatcher
run=READY (terminal) ; step[mark_ready]=RUNNING (atascado)
```
