# 60 — F17L: Decisión técnica de implementación (Fase 5)

> Fase F17L. Solo documentación. **No se implementó ninguna solución.**
> Respuestas basadas únicamente en evidencia (`57`, `58`, `59`).

## Fase 5 — Respuestas puntuales

**1. ¿Cuál alternativa modifica MENOS archivos?**
**A** (1 archivo: `dedicated_provisioning_orchestrator.py`). B = 2, C = 2-3, D = 3.

**2. ¿Cuál mantiene completamente el contrato actual?**
**Todas (A, B, C, D).** Ninguna toca contratos API/UI ni el conjunto de 10 códigos;
MARK_READY se conserva como step (`57`/`58 §3`).

**3. ¿Cuál conserva los 10 steps?**
**Todas.** `SAGA_STEP_ORDER` y `CK_tps_step_code` intactos en las 4.

**4. ¿Cuál NO requiere cambios en Frontend?**
**Todas.** La UI lee `steps[]` y `provisioning_state`; ninguna altera esos contratos.

**5. ¿Cuál NO requiere cambios en API?**
**Todas.** Sin cambios en endpoints, DTOs ni `provisioning_status_read`.

**6. ¿Cuál NO requiere migraciones?**
**Todas.** No se toca `V032`, `tables.py` ni `CK_tps_step_code`.

**7. ¿Cuál tiene menor riesgo de regresión?**
Por consistencia de estado pura: **D** (atómico, sin ventana). Por balance
riesgo/superficie y por **reutilizar un patrón ya aceptado**: **B**. **A** es la de
**mayor** riesgo (rompe Retry/Redispatch — `59` R-A1) pese a tocar menos archivos.

**8. ¿Cuál respeta completamente la arquitectura actual?**
**B.** El orquestador ya es dueño de la transición terminal del RUN en el **path de
fallo** (`_fail_step_and_run:685`). B hace **simétrico** el éxito: el orquestador
también posee `transition_run_to_ready`. No añade patrones nuevos ni toca el servicio
de estado. D respeta las reglas pero **introduce** un patrón atómico step+run que hoy
no existe (el fallo son dos commits).

**9. ¿Cuál recomendarías implementar?**
### ✅ Recomendación: **OPCIÓN B**

Mover `transition_run_to_ready()` fuera de `DedicatedActivationService.mark_ready`
(`:129-151`) y ejecutarla en el orquestador como **acto terminal después del bucle**
(`_handle_job_inner`, tras `:306`), simétrico con `_fail_step_and_run:685`.

Justificación (evidencia):
- **Corrige la causa raíz** (F17I): MARK_READY se cierra con `run=PROVISIONING`
  (guard `state:485-491` satisfecho) y la transición ocurre después.
- **Respeta todos los invariantes** (`59` Fase 3: 14/14, con la única no-atomicidad ya
  aceptada en el path de fallo).
- **Auto-sanable / idempotente**: crash pre-transición → redispatch (guard `:201`)
  omite steps completed y ejecuta la transición post-bucle → READY
  (`transition_run_to_ready:290` maneja NOOP).
- **Arquitectura simétrica**: orquestador dueño de READY y FAILED.
- **Superficie mínima**: 2 archivos, guard del servicio de estado **intacto**, sin
  contratos/DDL/Shared/compensación/métricas.
- Preserva `ready_at` (`:292-300`) y `current_step_code=MARK_READY` (`:298`).

**10. ¿Por qué descartar las demás?**
- **A — descartada:** aunque toca 1 solo archivo, marca el step `COMPLETED` **antes**
  de ejecutar su trabajo; si la transición falla, el run queda **atascado en
  PROVISIONING** silenciosamente (rompe Retry/Redispatch/Idempotencia — `59` R-A1).
  Menos archivos, **mayor** riesgo.
- **C — descartada (redundante):** si es secuencial, es funcionalmente igual a B pero
  con un método extra (más superficie sin beneficio); si usa una sola UoW, converge
  con D. No aporta sobre B.
- **D — no recomendada ahora (reserva):** es la más segura contra la ventana de
  consistencia, pero **introduce un patrón atómico step+run inexistente** en el
  sistema (el fallo no es atómico), toca el servicio de estado (autoridad del guard) y
  añade la rama de reentrada R-D2. Mayor complejidad/superficie para eliminar una
  ventana que hoy ya se acepta como benigna en el path de fallo. Queda como
  **alternativa** si se exige atomicidad estricta step+run.

## Resumen ejecutivo

| Ítem | Valor |
|---|---|
| **Alternativa recomendada** | **Opción B** (transición terminal al orquestador, post-bucle) |
| **Archivos que cambiaría** | **2** (`dedicated_activation_service.py`, `dedicated_provisioning_orchestrator.py`) |
| **Líneas aprox. modificadas** | **~25-30** netas |
| **Riesgo** | **Bajo** |
| **Complejidad** | **S** (Small) |
| **Contratos API/UI** | Sin cambios |
| **Migraciones** | Ninguna |
| **10 steps / MARK_READY** | Conservados |
| **Shared / Compensación / Métricas** | Sin impacto |
| **Alternativa de reserva** | **Opción D** (atomicidad estricta), si se prioriza eliminar la ventana benigna |

## Confirmación

**Aún NO se implementó ninguna solución.** No se modificó código, SQL, bootstrap,
onboarding, tests, manifests, contratos ni documentación existente. Esta fase solo
generó documentación nueva: `57`, `58`, `59`, `60`.
