# 47 — F17I: Root Cause Runtime (Fase 4 + Fase 5 + causa raíz)

> Fase F17I. Solo lectura. Determinista, derivado del código. Sin hipótesis.

## FASE 4 — ¿Quién cambia el run a READY?

**Dos capas, un único punto de mutación:**

1. **Trigger:** `DedicatedActivationService.mark_ready`
   → `app/infrastructure/provisioning/dedicated_activation_service.py:130`
   ```python
   await self._state.transition_run_to_ready(
       cliente_id=request.cliente_id,
       provisioning_run_id=request.provisioning_run_id,
   )
   ```
   (invocado por el orquestador en `_step_activation`,
   `dedicated_provisioning_orchestrator.py:655-657`, durante el cuerpo del step
   S10).

2. **Mutación real en BD:** `TenantProvisioningStateService.transition_run_to_ready`
   → `app/modules/tenant/application/services/tenant_provisioning_state_service.py:292`
   (`update_run_state(... target_state=READY ...)`) y `:306`
   (`update_cliente_provisioning_state(READY)`), commiteado en su propia
   `UnitOfWork` (`:274-312`).

**Respuesta directa:** NO es `DedicatedProvisioningOrchestrator` quien pone READY,
ni `mark_step_completed`. Es `DedicatedActivationService.mark_ready`
(`:130`) delegando en `TenantProvisioningStateService.transition_run_to_ready`
(`:292/306`). El log "Tenant dedicated ready" se emite en
`dedicated_activation_service.py:153`.

## FASE 5 — ¿Doble llamada? (SI/NO con evidencia)

- **¿Doble `mark_step_completed(MARK_READY)`?** → **NO.** Solo hay una:
  `orchestrator.py:299`. `mark_ready` (activation) **no** llama
  `mark_step_completed`.
- **¿`mark_step_completed()` DESPUÉS de `mark_ready()` (run→READY)?** → **SÍ.**
  Evidencia de orden en el bucle:
  - `orchestrator.py:290` `_execute_step(MARK_READY)` ⇒ `mark_ready` ⇒
    `transition_run_to_ready` (run→READY).
  - `orchestrator.py:299` `mark_step_completed(MARK_READY)` — ejecuta **después**.
- **¿`mark_ready()` ANTES de cerrar el último step?** → **SÍ.** `mark_ready`
  corre dentro de `_execute_step` (cuerpo del step), y el cierre del step
  (`mark_step_completed`) ocurre a continuación en `:299`. El run se marca READY
  **antes** de cerrar el step MARK_READY.

## Causa raíz única (determinista)

> **El paso S10 `MARK_READY` transiciona el run a `READY` dentro de su propio
> cuerpo de ejecución (`DedicatedActivationService.mark_ready` →
> `transition_run_to_ready`, `dedicated_activation_service.py:130`), y a
> continuación el bucle genérico del orquestador ejecuta
> `mark_step_completed(MARK_READY)` (`dedicated_provisioning_orchestrator.py:299`).
> Como `_transition_step` exige `run == PROVISIONING`
> (`tenant_provisioning_state_service.py:485-491`) y el run ya está en `READY`
> (estado terminal), el cierre del step falla con
> `ConflictError PROVISIONING_RUN_NOT_ACTIVE`
> ("No se puede mutar steps cuando el run no está en provisioning."), justo
> después del log "Tenant dedicated ready".**

Cadena causal mínima (todo commiteado, sin concurrencia):
`mark_step_running(MARK_READY)` [PROVISIONING ✅] → `transition_run_to_ready`
[run→READY, commit] → log "Tenant dedicated ready" → `mark_step_completed(MARK_READY)`
[READY ❌ guard :485] → ConflictError.

## ¿Es consecuencia del `FK_permiso_menu` (F17H) o un bug independiente?

**Bug INDEPENDIENTE.** Evidencia:

1. El disparo de este `ConflictError` no requiere ningún error previo: basta con
   que la saga **alcance** S10. Es un defecto de **orden** entre `mark_ready` y
   `mark_step_completed`, no de datos.
2. El log presenta "Tenant dedicated ready" **antes** del error → el run llegó a
   READY (S10 se ejecutó), lo que es incompatible con el escenario de F17H (donde
   el FK aborta en S7 y el run va a FAILED, nunca a READY).
3. El `internal_code` `PROVISIONING_RUN_NOT_ACTIVE` es el mismo mensaje en dos
   situaciones **distintas** (mismo guard `:485-491`):
   - **(A) F17I / este caso:** run en **READY** + `mark_step_completed(MARK_READY)`
     → defecto de orden S10 (determinista).
   - **(B) F17H / contexto FK:** run en **FAILED** + mutación de step por
     retry/redispatch → consecuencia del FK.
   La evidencia "Tenant dedicated ready" precedente prueba que **esta** instancia
   es la (A).

> Corrección al cierre de F17H: en F17H se clasificó "run no está en provisioning"
> como puramente consecuencia del FK. Con la nueva evidencia de runtime
> ("Tenant dedicated ready" → ConflictError), queda demostrado que existe además un
> **segundo trigger independiente** del mismo mensaje: el defecto de orden en S10.
> Son dos causas que comparten el mismo `internal_code`.

## Impacto observable

- El tenant queda **funcionalmente READY** (run y cliente commiteados a READY).
- El step `mark_ready` queda **atascado en RUNNING** (nunca COMPLETED).
- El job **lanza excepción** (la ConflictError se propaga: `:299` está fuera del
  `try/except` de `:289-297`; y `_fail_step_and_run` tampoco podría marcar FAILED
  porque `READY→FAILED` no está permitido, `provisioning_transition_rules.py:16`).
- Redispatch posterior → `handle_job` guard `:201` → "Saga noop" (no repara el
  step). El desalineamiento step/run persiste indefinidamente.
