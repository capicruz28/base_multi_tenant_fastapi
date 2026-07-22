# 48 — F17I: Remediation Plan (SIN implementar)

> Fase F17I. Solo lectura. Este documento **describe** qué habría que modificar.
> **No** contiene parches, **no** se ha tocado código, SQL, tests ni manifests.

## FASE 6 — Validar el orden correcto (Opción A vs Opción B)

- **Opción A:** `mark_step_completed(last_step)` → luego `mark_ready()` (run→READY).
- **Opción B:** `mark_ready()` (run→READY) → luego `mark_step_completed(last_step)`.

El código **actual** implementa **Opción B** de facto: el cuerpo del step
`MARK_READY` transiciona el run a READY (`dedicated_activation_service.py:130`) y
después el orquestador cierra el step (`dedicated_provisioning_orchestrator.py:299`).

**La máquina de estados existente solo admite la Opción A.** Justificación con el
código existente:
- `_transition_step` exige `run == PROVISIONING` para **cualquier** mutación de
  step (`tenant_provisioning_state_service.py:485-491`).
- `READY` es **terminal** (`provisioning_transition_rules.py:16`).
- Por tanto, el cierre del último step (`mark_step_completed(MARK_READY)`) **debe**
  ocurrir mientras `run == PROVISIONING`, y la transición `PROVISIONING→READY`
  debe ser la **última** acción de la saga.

Conclusión Fase 6: **Opción A** es la única consistente con la máquina de estados.

## Causa raíz exacta

| Campo | Valor |
|---|---|
| **Causa** | El step S10 muta `run.status` a READY dentro de su cuerpo y luego el bucle intenta cerrar el step; el guard de `_transition_step` rechaza mutar steps con run≠PROVISIONING. |
| **Archivo (llamada que falla)** | `app/modules/tenant/application/services/dedicated_provisioning_orchestrator.py` |
| **Método** | `DedicatedProvisioningOrchestrator._handle_job_inner` (bucle genérico) |
| **Línea** | `299` (`await self._state.mark_step_completed(... MARK_READY ...)`) |
| **Archivo (transición prematura)** | `app/infrastructure/provisioning/dedicated_activation_service.py` |
| **Método / línea** | `DedicatedActivationService.mark_ready` → `:130` (`transition_run_to_ready`) |
| **Archivo (guard que lanza)** | `app/modules/tenant/application/services/tenant_provisioning_state_service.py` |
| **Método / línea** | `TenantProvisioningStateService._transition_step` → `:485-491` |
| **internal_code** | `PROVISIONING_RUN_NOT_ACTIVE` |
| **Fase** | Defecto **pre-F17** de la saga S10 (PR-F4-09); independiente del `FK_permiso_menu`. Expuesto al alcanzar S10. |

## Por qué ocurre (resumen)

El orquestador aplica un patrón uniforme `running → ejecutar → completed` a todos
los steps (`orchestrator.py:284,290,299`), asumiendo que el cuerpo del step **no**
altera el estado del run. Esa asunción se rompe únicamente en S10, cuyo cuerpo
(`mark_ready`) es precisamente la transición del run a READY. El resultado es que
el paso destruye su propia precondición de cierre.

## Qué habría que modificar (opciones — NO implementar aquí)

Ordenadas por afinidad con la máquina de estados existente:

1. **Reordenar S10 (Opción A).** Que el step `MARK_READY` se cierre
   (`mark_step_completed`) **mientras** el run está en PROVISIONING, y que la
   transición `transition_run_to_ready` sea la acción **final** posterior al cierre
   del último step. Requiere tratar el último step como caso especial en el bucle
   (`orchestrator.py:284-304`) o mover la transición fuera del cuerpo del step.

2. **Atomizar cierre+transición.** Que `transition_run_to_ready`
   (`state_service:264-320`) cierre además el step `MARK_READY` a COMPLETED dentro
   de la **misma** `UnitOfWork` (antes de dejar el run en READY), y que el
   orquestador **no** invoque `mark_step_completed(MARK_READY)` para ese step.

3. **Exención puntual del guard** (menos limpia). Permitir en `_transition_step`
   (`:485-491`) que el step `MARK_READY` pase a COMPLETED cuando el run acaba de
   entrar en READY. Rompe el invariante general "steps solo mutan en PROVISIONING",
   por lo que es la opción menos recomendable.

Recomendación (solo criterio, sin código): **Opción 1 o 2**, porque preservan el
invariante "los steps solo mutan mientras el run está en PROVISIONING" y dejan la
transición a READY como acción terminal única.

## Nota de verificación previa a cualquier fix (fuera de F17I)

Como el defecto deja `provisioning_run.status = READY` con
`step[mark_ready] = RUNNING`, una corrección deberá contemplar además la
**reconciliación** de runs ya afectados (step atascado en RUNNING sobre run READY).
No forma parte de esta auditoría; se documenta solo como dependencia.
