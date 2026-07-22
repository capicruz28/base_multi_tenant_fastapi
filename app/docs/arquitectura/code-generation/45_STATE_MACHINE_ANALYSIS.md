# 45 — F17I: State Machine Analysis (run + step)

> Fase F17I. Solo lectura. No se implementa nada.

## 1. Dos máquinas de estados acopladas

### 1.1 Estado del RUN (`provisioning_run.provisioning_state`)

`provisioning_transition_rules.py:9-17`:

```
(none) ──init──▶ PROVISIONING
PROVISIONING ──▶ READY   (terminal)
PROVISIONING ──▶ FAILED
FAILED ──────▶ PROVISIONING   (retry)
READY ───────▶ ∅   (terminal, sin salidas)
```

Mutadores del run:
| Método | Transición | Archivo:línea |
|---|---|---|
| `initialize_provisioning_run` | ∅→PROVISIONING | `tenant_provisioning_state_service.py:145,155` |
| `transition_run_to_ready` | PROVISIONING→READY | `:292,306` |
| `transition_run_to_failed` | PROVISIONING→FAILED | `:353,371` |
| `begin_retry_from_failed` | FAILED→PROVISIONING | `:235,247` |

### 1.2 Estado del STEP (`provisioning_step.step_status`)

Mutado **exclusivamente** por `_transition_step`
(`tenant_provisioning_state_service.py:457-550`), vía:
`mark_step_running` (:387), `mark_step_completed` (:403), `mark_step_failed`
(:421), `mark_step_skipped` (:441).

## 2. El invariante duro: los steps solo mutan si el run está en PROVISIONING

`_transition_step` **antes** de tocar cualquier step valida el estado del RUN
(`:485-491`):

```
if run_state != PROVISIONING:
    raise ConflictError("No se puede mutar steps cuando el run no está en provisioning.",
                        internal_code="PROVISIONING_RUN_NOT_ACTIVE")
```

Consecuencia lógica **inevitable**: una vez el run entra en READY (terminal),
**ningún** step puede volver a mutar — ni siquiera para marcarse COMPLETED.

## 3. El conflicto de diseño

El paso S10 `MARK_READY` tiene una doble naturaleza contradictoria bajo este
invariante:

1. Como **step** de la saga, el orquestador lo trata igual que a los demás:
   `mark_step_running` → ejecutar → `mark_step_completed`
   (`orchestrator.py:284,290,299`). Las dos mutaciones de step exigen
   run=PROVISIONING.
2. Como **acción**, su cuerpo (`mark_ready` → `transition_run_to_ready`) **saca**
   al run de PROVISIONING hacia READY (`activation:130`).

Es decir: el propio cuerpo del step destruye la precondición que el bucle
necesita para poder **cerrar** ese mismo step. El orden temporal es:

```
mark_step_running(MARK_READY)   [run=PROVISIONING]  ✅
   ↓
transition_run_to_ready()       [run: PROVISIONING→READY]  ✅ (commit)
   ↓
mark_step_completed(MARK_READY) [run=READY]  ❌ guard :485 → ConflictError
```

## 4. ¿Por qué S1–S9 no fallan y S10 sí?

Para S1–S9, el cuerpo del step **no** cambia `run.status`; el run permanece en
PROVISIONING durante `mark_step_running` y `mark_step_completed`. Solo S10 muta el
run dentro de su propio cuerpo. Por eso el fallo es **específico y determinista**
del último step. (S4/S5 usan la rama bootstrap `_run_bootstrap_block` /
`_mark_bootstrap_saga_steps`, que también cierra sus steps con run=PROVISIONING —
`orchestrator.py:531-569` — sin tocar el estado del run.)

## 5. Determinismo

No depende de datos, concurrencia ni del error `FK_permiso_menu`. Siempre que la
saga **alcance** S10:
- `transition_run_to_ready` deja el run en READY (commiteado, `state:292-300`,
  `affected==1`).
- El `mark_step_completed(MARK_READY)` inmediatamente posterior lee run=READY
  (lock en `_transition_step:475`) y falla en `:485`.

Por tanto el step `MARK_READY` **nunca** puede alcanzar `COMPLETED` con el código
actual: es un fallo estructural, no un caso borde.
