# 57 — F17L: Alternativas de implementación del fix (diseño, NO implementado)

> Fase **F17L**. Diseño demostrado contra el código existente. **No** se modificó
> código, SQL, tests, contratos ni documentación existente. Solo documentación nueva.
> Toda referencia cita `archivo:línea`.

## 0. Punto de partida (defecto probado en F17I/F17J)

Bucle genérico del orquestador (`dedicated_provisioning_orchestrator.py:284-304`):
```
284  mark_step_running(step)      # exige run=PROVISIONING (_transition_step:485)
290  marker = _execute_step(step) # cuerpo del step
299  mark_step_completed(step)    # exige run=PROVISIONING
```
Para S10, `_execute_step` → `_step_activation` (`:655-657`) → `activation.mark_ready`
(`dedicated_activation_service.py:108-162`) → `transition_run_to_ready` (`:130`)
deja **run=READY** antes de la línea 299 → `mark_step_completed` falla en el guard
(`tenant_provisioning_state_service.py:485-491`).

Patrón terminal **ya existente** en el path de fallo
(`orchestrator._fail_step_and_run:663-696`):
```
678  mark_step_failed(step)             # step RUNNING→FAILED (run=PROVISIONING)
685  transition_run_to_failed(...)      # run PROVISIONING→FAILED  (propiedad del orquestador)
```
→ El orquestador **ya es dueño** de la transición terminal del RUN en el fallo. El
éxito es asimétrico: hoy delega la transición terminal en el worker de paso.

Invariantes a respetar (todas verificadas en F17J):
- `_transition_step` exige `run=PROVISIONING` (`:485-491`).
- Run: `PROVISIONING→{READY,FAILED}`; `READY` terminal (`provisioning_transition_rules.py:12-16`).
- Step: `RUNNING→{COMPLETED,FAILED}` (`provisioning_step_transition_rules.py:15-17`).

---

## OPCIÓN A — Reordenar SOLO dentro del Orchestrator (MARK_READY intacto)

**Idea:** el orquestador cierra el step MARK_READY **antes** de ejecutar su cuerpo
(que hace la transición). Es decir, para el último step invertir 299↔290.

**Diseño contra el código:**
- En el bucle (`:284-304`), caso especial `step_code == MARK_READY`:
  `mark_step_running` → `mark_step_completed` (con run=PROVISIONING) → `_execute_step`
  (que ejecuta `mark_ready`→`transition_run_to_ready`).
- `DedicatedActivationService` queda **exactamente igual**.

**Archivos:** `dedicated_provisioning_orchestrator.py` (1 archivo, ~8-12 líneas).

**Problema de diseño (documentado, no bloqueante de la propuesta):** marca el step
`COMPLETED` **antes** de realizar su trabajo. Si `mark_ready` falla tras el
`COMPLETED`, queda `step=COMPLETED` + `run=PROVISIONING`; en redispatch el step se
omite (`:240-249`) y el bucle termina **sin** transicionar a READY → run atascado en
PROVISIONING silenciosamente (nuevo modo de fallo). Ver `59`.

---

## OPCIÓN B — Mover `transition_run_to_ready()` fuera de ActivationService (MARK_READY sigue siendo Step)

**Idea:** el worker deja de transicionar el RUN; el **orquestador** ejecuta la
transición terminal **después** de cerrar todos los steps — **simétrico** con
`_fail_step_and_run`.

**Diseño contra el código:**
- `dedicated_activation_service.mark_ready` (`:108-162`): **quitar** el bloque
  `transition_run_to_ready` (`:129-151`); conserva la validación idempotente y
  devuelve el marker `ready_run:{run_id}` (`:158-162`). El step S10 sigue teniendo
  cuerpo (validación/marker), pero ya no muta el RUN.
- `dedicated_provisioning_orchestrator._handle_job_inner`: **después** del bucle
  (tras `:306` "Saga completed"), invocar
  `self._state.transition_run_to_ready(cliente_id, provisioning_run_id)` como acto
  terminal.
- El bucle cierra `MARK_READY` normalmente con run=PROVISIONING (guard OK).

**Por qué es auto-sanable/idempotente:** si hay crash entre "MARK_READY completed" y
la transición, el redispatch entra (guard `:201` ve PROVISIONING), el bucle omite
todos los steps completed (`:240-249`) y ejecuta la transición terminal post-bucle →
READY. `transition_run_to_ready` ya maneja NOOP si ya está READY (`:290` +
`PROVISIONING_STATE_NOOP`).

**Archivos:** `dedicated_activation_service.py` + `dedicated_provisioning_orchestrator.py`
(2 archivos, ~25-30 líneas netas).

**Simetría arquitectónica:** el orquestador pasa a ser dueño de **ambas**
transiciones terminales (READY y FAILED), igual que ya lo es de FAILED (`:685`).

---

## OPCIÓN C — Método `finalize_success()` que cierra el último Step y luego marca READY

**Idea:** encapsular "cerrar último step + marcar READY" en un método nombrado
(secuencial, no atómico).

**Diseño contra el código:**
- Nuevo método `finalize_success(cliente_id, run_id)` (ubicación candidata:
  `DedicatedProvisioningOrchestrator` o un servicio de activación) que hace:
  `mark_step_completed(MARK_READY)` (run=PROVISIONING) → `transition_run_to_ready`.
- `mark_ready` en activation deja de transicionar (igual que B).
- El orquestador, en el caso MARK_READY, **no** usa el `mark_step_completed` genérico
  (`:299`) sino `finalize_success()`.

**Archivos:** `dedicated_activation_service.py` + `dedicated_provisioning_orchestrator.py`
(+ el método nuevo donde resida). 2-3 archivos, ~35-45 líneas.

**Diferencia con B:** B pone la transición post-bucle (auto-sanable). C la agrupa en
un método específico para el step; sigue siendo **dos commits** (misma ventana que B)
salvo que el método use una sola UoW (entonces converge con D).

---

## OPCIÓN D — Operación atómica en `TenantProvisioningStateService` (NO implementar)

**Idea:** un único método en el servicio de estado que, en **una sola UoW**, cierre
el step MARK_READY (RUNNING→COMPLETED) **y** transicione el RUN
(PROVISIONING→READY), commit único. Sin ventana intermedia.

**Diseño contra el código:**
- Nuevo `finalize_run_success(cliente_id, run_id, step_code=MARK_READY, marker)` en
  `tenant_provisioning_state_service.py`, dentro de una `UnitOfWork`
  (`connection_type=ADMIN`):
  1. `lock_provisioning_run_tx` (como `:475/278`).
  2. Validar `run==PROVISIONING` (reutiliza el invariante `:485`).
  3. `update_step_status` MARK_READY RUNNING→COMPLETED (`:508`).
  4. `update_run_state` PROVISIONING→READY con `ready_at` + `current_step_code=MARK_READY`
     (`:292-300`).
  5. `update_cliente_provisioning_state(READY)` (`:306`).
  6. commit único.
- `mark_ready` en activation deja de transicionar; el orquestador llama al método
  atómico para el step terminal (no usa el `mark_step_completed` genérico `:299`).

**Archivos:** `tenant_provisioning_state_service.py` + `dedicated_provisioning_orchestrator.py`
+ `dedicated_activation_service.py` (3 archivos, ~50-60 líneas).

**Nota:** **No** debilita el guard `_transition_step:485` (lo respeta dentro de la
UoW). Introduce un patrón atómico step+run **nuevo** (el path de fallo NO es atómico:
`:678` y `:685` son dos commits), por lo que se aparta del patrón vigente.

---

## Resumen de las 4 alternativas

| Opción | Idea | MARK_READY | Dónde vive la transición | Commits | Archivos |
|---|---|---|---|---|---|
| A | Reordenar en orquestador | intacto | dentro del cuerpo del step (igual) | 2 | 1 |
| B | Sacar transición a orquestador (post-bucle) | step sin mutar run | orquestador (terminal) | 2 | 2 |
| C | `finalize_success()` secuencial | step sin mutar run | método nombrado | 2 | 2-3 |
| D | Atómico en state service | step sin mutar run | state service (1 UoW) | 1 | 3 |

Impacto detallado en `58`; validación e riesgos en `59`; decisión en `60`.
