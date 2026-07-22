# 50 — F17J: Análisis de responsabilidades en runtime

> Fase F17J. Solo auditoría. No se propone implementación; se identifica el punto
> de corrección (Q3, Q5, Q10).

## 1. Respuesta 3 — Mezcla de responsabilidades

### 1.1 Responsabilidad esperada de cada componente

| Componente | Responsabilidad conceptual |
|---|---|
| `DedicatedProvisioningOrchestrator` | Conducir la saga: secuenciar S1→S10, gobernar el **ciclo de vida del STEP** (running→completed/failed), y el ciclo de vida terminal del RUN (ready/failed) como acto de la saga. Compensación/retry. |
| `DedicatedActivationService` | Ejecutar el **trabajo** de activación S8–S10: metadata CP (S8), invalidación cache + smoke routing (S9), y "dejar listo" (S10). Es un *worker de paso*, no dueño del ciclo de vida del RUN. |
| `TenantProvisioningStateService` | **Autoridad única** de la máquina de estados: guards + persistencia de transiciones de RUN y STEP. No orquesta. |

### 1.2 Lo que ocurre realmente (fuga de responsabilidad)

- El **Orchestrator** cierra los STEPs con el patrón genérico
  `mark_step_running → _execute_step → mark_step_completed`
  (`orchestrator.py:284,290,299`) y transiciona el RUN a FAILED en el manejador de
  error (`_fail_step_and_run:685`). **Pero NO transiciona el RUN a READY**: delega
  esa transición terminal en el worker de paso.
- El **ActivationService**, dentro de un método de *ejecución de paso*
  (`mark_ready`), invoca `transition_run_to_ready` (`dedicated_activation_service.py:130`)
  — es decir, ejecuta una **transición del ciclo de vida del RUN** (concern de
  orquestación/máquina de estados) desde una capa que debería limitarse al trabajo
  del paso. Además emite el log de negocio "Tenant dedicated ready" (`:153`).
- Resultado: para el **mismo** step S10, **dos** responsabilidades quedan repartidas
  y descoordinadas:
  - transición terminal del RUN → la hace ActivationService (dentro del cuerpo).
  - cierre del STEP (`mark_step_completed`) → lo hace el Orchestrator (después).
  Y se ejecutan en el **orden inválido** (RUN→READY antes de cerrar el STEP), que el
  guard `_transition_step:485` prohíbe.

**Diagnóstico Q3:** SÍ existe mezcla de responsabilidades. La transición terminal
del RUN (concern del Orchestrator / máquina de estados) está **incrustada dentro de
un worker de paso** (`DedicatedActivationService.mark_ready`), mientras el cierre
del propio step lo realiza el Orchestrator por separado. `TenantProvisioningStateService`
es el único que mantiene su responsabilidad intacta (y es quien, correctamente,
detecta la incoherencia vía el guard).

## 2. Respuesta 5 — ¿Cuándo debe ocurrir `transition_run_to_ready()`?

**DESPUÉS del cierre del último STEP real** (no "durante", no "antes de cerrar el
step dentro de su cuerpo"). Demostración únicamente con la máquina de estados
existente:

1. Cualquier `mark_step_*` exige `run == PROVISIONING`
   (`tenant_provisioning_state_service.py:485-491`).
2. Los STEPs sólo alcanzan estado terminal COMPLETED **mientras** el RUN está en
   PROVISIONING (corolario de (1); `provisioning_step_transition_rules.py:15-19`).
3. READY es terminal del RUN y no admite salidas
   (`provisioning_transition_rules.py:16`); una vez en READY no se puede volver a
   PROVISIONING salvo pasando por FAILED (`:15`), que no aplica en éxito.

De (1)+(2)+(3): **todos los cierres de STEP deben preceder** a la transición
`PROVISIONING→READY`. Por tanto la única ubicación válida de
`transition_run_to_ready` es **al final, tras cerrar el último step**, como acto
terminal de la saga.

- "Durante" (dentro del cuerpo del step MARK_READY, como hoy) → **inválido**
  (prueba: F17I / `47_ROOT_CAUSE_RUNTIME.md`; produce `PROVISIONING_RUN_NOT_ACTIVE`).
- "Antes de cerrar el step" → mismo caso inválido.
- "Después de cerrar el último step" → **único orden compatible**.

> Matiz de modelado: si `mark_ready` se mantiene como STEP, entonces su cierre
> (`COMPLETED`) es el "último step" que debe ocurrir mientras run=PROVISIONING, y la
> transición del RUN va inmediatamente **después**. Si `mark_ready` se elimina como
> STEP, el "último step" pasa a ser S9 (activate_routing) y la transición del RUN va
> tras cerrar S9. Ambas variantes respetan la regla (1)-(3). La elección entre ellas
> es la decisión arquitectónica de fondo (ver `52`).

## 3. Respuesta 10 — ¿Cuál es el verdadero punto de corrección?

**NO** es `TenantProvisioningStateService`: su guard (`:485-491`) es correcto y
constituye el invariante que se quiere preservar; debilitarlo enmascararía el
problema.

El verdadero punto de corrección está en el **seam Orchestrator ↔ ActivationService**,
concretamente en **quién** realiza la transición terminal del RUN y **cuándo**,
respecto del cierre del step:

| Candidato | ¿Es el punto de corrección? | Motivo |
|---|---|---|
| `TenantProvisioningStateService` | **No** (no tocar el guard) | El invariante es correcto; la incoherencia la introduce el consumidor. |
| `DedicatedActivationService.mark_ready` | **Sí, en parte** | Aloja una transición de ciclo de vida del RUN dentro de un worker de paso; esa responsabilidad debe salir de aquí o coordinarse. |
| `DedicatedProvisioningOrchestrator` | **Sí, principal** | Es quien debe orquestar el orden terminal (cerrar último step con run=PROVISIONING y luego transicionar el RUN a READY), en lugar de tratar S10 como un step genérico cuyo cuerpo muta el RUN. |
| Arquitectura de la State Machine | **Sí, decisión de modelo** | Debe resolverse la doble representación de "ready" (¿`mark_ready` sigue siendo STEP?). Es una decisión, no un cambio de reglas/enums (que son correctos). |

**Conclusión Q10:** el punto de corrección real es **arquitectónico/orquestación**:
recae en la frontera **Orchestrator + ActivationService** (dónde y cuándo se dispara
la transición terminal del RUN), condicionado por una **decisión de modelo** sobre
el step `mark_ready`. **No** recae en el `TenantProvisioningStateService` (no debe
tocarse el guard) ni en los enums/reglas de transición (son correctos). El detalle
de la decisión y su justificación en `52_FINAL_ARCHITECTURAL_VERDICT.md`.
