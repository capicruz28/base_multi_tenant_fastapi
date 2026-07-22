# 52 — F17J: Veredicto arquitectónico final

> Fase F17J. Solo auditoría. **No** se implementa nada. Este documento consolida el
> veredicto único a partir de `49`, `50` y `51`.

## 1. Veredicto único

> **El fallo de S10 (MARK_READY) NO es un bug puntual de orden de líneas: es la
> manifestación de un defecto de diseño de la máquina de estados — la
> "readiness" está representada por partida doble (estado terminal del RUN
> `provisioning_state='ready'` y STEP `mark_ready`), y el paso `mark_ready` realiza
> la transición terminal del RUN dentro del cuerpo de un step, violando el
> invariante correcto "los steps sólo mutan si run=PROVISIONING"
> (`tenant_provisioning_state_service.py:485-491`). El orden de llamadas es sólo el
> síntoma; la causa es el modelo.**

## 2. Respuestas consolidadas

| # | Pregunta | Respuesta |
|---|---|---|
| 1 | ¿READY es Step o estado final del Run? | **Estado final del RUN (B).** `V032:18,40-42` + `ready_at :27`; enum `TERMINAL_PROVISIONING_STATES` (`provisioning_state.py:17-19`); contrato v1 a nivel run. |
| 2 | ¿Tiene sentido un Step MARK_READY? | **No con su semántica actual:** es el único step sin trabajo propio; su efecto ES la transición terminal del RUN. Debe ser transición de RUN, no un step que se auto-completa. |
| 3 | ¿Mezcla de responsabilidades? | **Sí:** `DedicatedActivationService.mark_ready` (worker de paso) ejecuta una transición de ciclo de vida del RUN (`:130`), mientras el Orchestrator cierra el step por separado y en orden inválido. `TenantProvisioningStateService` es el único con responsabilidad intacta. |
| 4 | Flujo ideal | Ver `51` §1: S1..último cierran STEP con run=PROVISIONING; `transition_run_to_ready` como acto terminal posterior. |
| 5 | ¿Cuándo `transition_run_to_ready()`? | **Después** de cerrar el último step (demostrado por `_transition_step:485` + terminalidad de READY). Nunca "durante". |
| 6 | ¿Otro step muta el RUN en su cuerpo? | **NO.** Sólo S10 MARK_READY (`51`/`49` §5). |
| 7 | ¿Dónde puede reaparecer? | En cualquier step futuro cuyo cuerpo mute `run.status`; y ya se manifiesta como estado irrecuperable (RUN=READY + step RUNNING; retry exige FAILED). Ver `49` §6. |
| 8 | ¿Bug puntual (A) o diseño (B)? | **B — diseño incorrecto**, con manifestación acotada a 1 step. |
| 9 | Diagrama correcto | Ver `51` §2. |
| 10 | ¿Punto de corrección? | **Orchestrator + ActivationService** (dónde/cuándo se dispara la transición terminal del RUN) + **decisión de modelo** sobre el step `mark_ready`. **NO** el guard de `TenantProvisioningStateService` ni los enums/reglas. |

## 3. Naturaleza exacta del defecto de diseño

1. **Doble fuente de verdad para "ready"** (`49` §1, §3):
   - RUN: `tenant_provisioning_run.provisioning_state='ready'` (autoritativo,
     contrato v1, denormalizado a `cliente`).
   - STEP: `tenant_provisioning_step[step_code='mark_ready'].step_status='completed'`
     (redundante).
2. **Un STEP cuyo cuerpo es una transición de RUN** (`49` §4): `mark_ready` no aporta
   trabajo propio; su ejecución ES `transition_run_to_ready`.
3. **Un invariante correcto que expone la contradicción** (`50` §2): "steps sólo
   mutan si run=PROVISIONING". El invariante debe conservarse; es el modelo del step
   `mark_ready` el que no encaja.

Estos tres hechos, combinados, garantizan que el step `mark_ready` **nunca** puede
alcanzar COMPLETED con el diseño actual: es estructural, no un caso borde.

## 4. Qué NO se debe tocar (para no enmascarar el problema)

- **`_transition_step` guard (`:485-491`)**: es el invariante correcto. Relajarlo
  para permitir cerrar `mark_ready` con run=READY ocultaría el defecto y abriría la
  puerta a mutar steps sobre runs terminales.
- **Enums** (`provisioning_state.py`, `provisioning_step_status.py`) y **reglas de
  transición** (`provisioning_transition_rules.py`, `provisioning_step_transition_rules.py`):
  son individualmente coherentes.
- **Esquema V032**: los CHECK y columnas son correctos; el problema es de uso, no de
  DDL. (La duplicación `mark_ready` step vs `ready` run es de modelo lógico, no un
  error de tabla.)

## 5. Dirección de la corrección (identificación, sin implementar)

La decisión arquitectónica de fondo (a resolver antes de codificar) es **una** de:

- **Opción de modelo T1 — conservar `mark_ready` como STEP observacional:** su cierre
  (`mark_step_completed`) debe ocurrir con run=PROVISIONING y la transición
  `transition_run_to_ready` debe ejecutarse **después**, orquestada como acto
  terminal (no dentro del cuerpo del step). Locus: `DedicatedProvisioningOrchestrator`
  (secuencia terminal) + sacar la transición de RUN de
  `DedicatedActivationService.mark_ready`.
- **Opción de modelo T2 — degradar `mark_ready` a transición pura del RUN:** eliminar
  su rol de step ejecutable; el último step real pasa a ser S9, y tras cerrarlo el
  Orchestrator dispara `transition_run_to_ready` como acto terminal. Locus:
  `DedicatedProvisioningOrchestrator` + `DedicatedActivationService`.
- **Opción atómica (compatible con T1):** que `transition_run_to_ready`
  (`TenantProvisioningStateService`) cierre además el step `mark_ready` en la
  **misma** UoW, antes de dejar el RUN en READY, y que el Orchestrator no invoque
  `mark_step_completed(mark_ready)`. Añade una operación de "finalize" cohesiva sin
  tocar el guard.

En los tres casos el eje de corrección es **orquestación + límites de
responsabilidad**, no el motor de estados. La elección entre T1/T2/atómica es la
que debe aprobarse en la siguiente fase (no en F17J).

## 6. Conclusión

- **Es diseño (B), no bug puntual (A).**
- **Causa:** doble representación de "ready" + step que ejecuta la transición
  terminal del RUN.
- **Invariante correcto** que no debe tocarse: `_transition_step` guard.
- **Punto de corrección real:** frontera `DedicatedProvisioningOrchestrator` ↔
  `DedicatedActivationService`, condicionada por la decisión de modelo sobre el step
  `mark_ready`.
- La corrección **no** es debilitar `TenantProvisioningStateService`.
