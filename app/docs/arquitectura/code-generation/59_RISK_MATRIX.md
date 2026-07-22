# 59 — F17L: Validación contra el código y matriz de riesgos (Fases 3 y 4)

> Fase F17L. Solo documentación. Ninguna alternativa se acepta sin demostrar
> cumplimiento de los invariantes existentes.

## FASE 3 — Validación de cada alternativa contra los invariantes

Leyenda: ✓ cumple · ✓* cumple con condición · ✗ no cumple.

| Invariante (evidencia) | A | B | C | D |
|---|---|---|---|---|
| `_transition_step` guard run=PROVISIONING (`state:485-491`) | ✓* | ✓ | ✓ | ✓ |
| `ProvisioningTransitionRules` (`:12-16`, READY terminal) | ✓ | ✓ | ✓ | ✓ |
| `ProvisioningStepTransitionRules` (`:15-17` RUNNING→COMPLETED) | ✓* | ✓ | ✓ | ✓ |
| Retry (`begin_retry_from_failed:176`; `_first_incomplete:553`) | ✗ | ✓ | ✓ | ✓* |
| Compensation (`_COMPENSATION_STEP_ORDER:59`; no-op `:210-212`) | ✓ | ✓ | ✓ | ✓ |
| Idempotencia (`mark_ready:112-127`; `transition:290 NOOP`) | ✓* | ✓ | ✓ | ✓ |
| Saga (orden `SAGA_STEP_ORDER`; bucle `:229`) | ✓ | ✓ | ✓ | ✓ |
| UoW (`UnitOfWork` por transición) | ✓ | ✓ | ✓ | ✓ |
| Atomicidad step+run | ✗ (2 commits) | ✗ (2 commits) | ✗ (2 commits) | ✓ (1 UoW) |
| READY terminal (`:16`) | ✓ | ✓ | ✓ | ✓ |
| FAILED (`transition_run_to_failed:322`) | ✓* | ✓ | ✓ | ✓ |
| Redispatch (guard `:201`) | ✗ | ✓ | ✓ | ✓* |
| `current_step_code` (`transition:298`) | ✓ | ✓ | ✓ | ✓ |
| `ready_at` (`transition:292-300`) | ✓ | ✓ | ✓ | ✓ |

Notas de las condiciones:
- **A ✓\* / ✗:** cierra el step antes de ejecutar → cumple el guard **por orden
  invertido**, pero rompe la semántica "completed = trabajo hecho" y **falla Retry y
  Redispatch** (ver R-A1): si la transición falla tras el COMPLETED, el redispatch
  omite el step y el run queda PROVISIONING sin READY.
- **B/C ✓:** cierran el step con run=PROVISIONING (natural) y transicionan después.
  Retry/Redispatch auto-sanables si la transición va **post-bucle** (B).
- **D ✓ / ✓\*:** atómico, sin ventana; el `✓*` de Retry/Redispatch: debe contemplar
  reentrada con MARK_READY en RUNNING (ver R-D2).

## FASE 4 — Riesgos (incluye problemas aún no manifestados)

### Riesgos por alternativa

| ID | Riesgo | A | B | C | D |
|---|---|---|---|---|---|
| R1 | Ventana inconsistente (step completed, run no-ready) | Sí | Sí (breve, benigna) | Sí | **No** |
| R2 | Doble commit | Sí | Sí | Sí | No |
| R3 | Doble READY | No¹ | No¹ | No¹ | No¹ |
| R4 | Step completed pero run failed | Posible² | Posible² | Posible² | No |
| R5 | Run ready pero step pending/running | No | No | No | No³ |
| R6 | Pérdida de idempotencia | Sí (R-A1) | No | No | No |
| R7 | Retry imposible | Sí (R-A1) | No | No | No |
| R8 | Rollback parcial | Sí | Sí | Sí | No (1 UoW) |
| R9 | Compensación inválida | No | No | No | No |
| R10 | Carrera (concurrencia) | Igual base⁴ | Igual base⁴ | Igual base⁴ | Igual base⁴ |
| R11 | Deadlock | No⁵ | No⁵ | No⁵ | Bajo⁶ |
| R12 | Side effects | No | No | No | No |

Aclaraciones:
1. **R3 (doble ready):** protegido por `transition_run_to_ready:290`
   (`assert_provisioning_state_transition` → `PROVISIONING_STATE_NOOP` si ya READY) y
   guard de handle_job `:201`. Ninguna alternativa lo introduce.
2. **R4:** ventana entre "step completed" y transición; si en ese punto ocurre un
   fallo que dispare `_fail_step_and_run`, se intentaría `transition_run_to_failed`
   con el step ya COMPLETED → estado mixto (step completed + run failed). En B, al
   colocar la transición **post-bucle** y como último acto, la superficie es mínima;
   en D **no existe** (atómico). Es un riesgo teórico de A/B/C, nulo en D.
3. **R5 en D (✓\*):** con atómico no puede haber "run ready + step pending". Pero si
   un crash deja MARK_READY en RUNNING (transición atómica no ejecutada), el
   redispatch debe reintentar; `mark_step_running` sobre RUNNING daría
   `PROVISIONING_STEP_NOOP` (`step_rules:28-34`) → hay que preverlo (R-D2).
4. **R10:** `UQ_tpr_cliente_current` + `lock_provisioning_run_tx` (`state:278/475`)
   ya serializan por run; ninguna alternativa cambia el modelo de concurrencia base.
5. **R11:** transiciones sobre un único run bajo un solo lock; sin adquisición
   cruzada de locks → sin deadlock nuevo.
6. **R11 en D:** al hacer step+run en una UoW se toman más bloqueos en la misma
   transacción, pero sobre las mismas filas del mismo run (bajo el lock de run) →
   riesgo bajo, no cero.

### Riesgos detallados clave

**R-A1 (crítico de A):** con "completar antes de ejecutar", si `mark_ready` falla
tras el `COMPLETED`, en redispatch el bucle omite MARK_READY (`:240-249`) y finaliza
**sin** transicionar a READY → run atascado en PROVISIONING de forma silenciosa
(no hay error, no hay READY). Rompe Retry (requiere FAILED) y Redispatch. Este riesgo
convierte a A en la peor opción pese a ser la de menos archivos.

**R-B1 (menor de B):** ventana benigna "MARK_READY completed + run PROVISIONING". La
lectura de estado (`provisioning_status_read`) podría ver momentáneamente 10/10 steps
completed con run aún `provisioning`; la UI decide "ready" por `provisioning_state`
(`UI_CONTRACT:419`), así que sólo muestra "provisioning" un instante más → benigno.
**Idéntico patrón** al ya aceptado en el path de fallo (`mark_step_failed:678` +
`transition_run_to_failed:685`, dos commits).

**R-D2 (de D):** reentrada tras crash con MARK_READY=RUNNING. El método atómico o el
orquestador deben tolerar reejecutar el finalize cuando el step está RUNNING (no
volver a `mark_step_running`). Es un caso de diseño resoluble, pero añade una rama.

## Conclusión de validación

- **A:** descartable — falla Retry/Redispatch/Idempotencia (R-A1).
- **B:** cumple todos los invariantes; única "no-atomicidad" es la **misma** ya
  aceptada en el path de fallo; auto-sanable post-bucle.
- **C:** equivalente a B (o a D si usa una UoW); añade un método sin ganancia clara
  sobre B salvo nombre explícito.
- **D:** máxima consistencia (atómico), pero introduce patrón nuevo en el servicio de
  estado y una rama de reentrada (R-D2); más archivos y superficie de test.

Decisión final en `60`.
