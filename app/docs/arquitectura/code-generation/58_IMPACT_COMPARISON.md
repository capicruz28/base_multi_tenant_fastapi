# 58 — F17L: Análisis de impacto por alternativa (Fase 2)

> Fase F17L. Solo documentación. Impacto estimado contra el código existente.

## 1. Tabla de impacto por eje

Leyenda impacto: **—** ninguno · **▲** bajo · **▲▲** medio · **▲▲▲** alto.

| Eje | A (reorden orquestador) | B (sacar transición) | C (finalize_success) | D (atómico state svc) |
|---|---|---|---|---|
| **Archivos** | 1 | 2 | 2-3 | 3 |
| **Líneas aprox.** | ~8-12 | ~25-30 | ~35-45 | ~50-60 |
| **Clases** | `DedicatedProvisioningOrchestrator` | Orchestrator + `DedicatedActivationService` | Orchestrator + Activation (+host de método) | `TenantProvisioningStateService` + Orchestrator + Activation |
| **Métodos** | `_handle_job_inner` (bucle) | `_handle_job_inner`, `mark_ready` | `_handle_job_inner`, `mark_ready`, `finalize_success` (nuevo) | nuevo `finalize_run_success`, `_handle_job_inner`, `mark_ready` |
| **Contratos (API/UI)** | — | — | — | — |
| **Shared impact** | — (Shared no usa saga) | — | — | — |
| **Dedicated impact** | ▲▲ (semántica S10) | ▲ | ▲ | ▲ |
| **Retry impact** | ▲▲ (riesgo stuck PROVISIONING) | ▲ (auto-sanable post-bucle) | ▲ | ▲ |
| **Compensation impact** | — | — | — | — |
| **Metrics impact** | — | — | — | — |
| **API impact** | — | — | — | — |
| **UI impact** | — | — | — | — |
| **Test impact** | ▲ (orquestador S10) | ▲▲ (orquestador + activation) | ▲▲ | ▲▲ |
| **Riesgo de regresión** | Medio-Alto | Bajo | Bajo-Medio | Bajo (estado) / Medio (patrón nuevo) |
| **Complejidad** | S | S | M | M-L |

## 2. Detalle por alternativa

### A — Reordenar en el Orchestrator
- **Afecta:** `dedicated_provisioning_orchestrator.py` bucle `:284-304` (caso especial
  MARK_READY: completar antes de ejecutar).
- **No toca:** activation, state service, DDL, contratos.
- **Shared:** N/A (Shared no ejecuta la saga; `orchestrator._handle_job_inner`
  guard `DEDICATED_ENABLED` + tipo dedicated).
- **Retry/Redispatch:** ▲▲ — introduce ventana "step COMPLETED + run PROVISIONING";
  si la transición falla luego, el redispatch omite el step y el run queda en
  PROVISIONING sin transición (ver `59` R-A1).
- **Tests:** `test_f4_08_dedicated_orchestrator.py`, `test_f4_09_orchestrator_activation.py`.

### B — Mover `transition_run_to_ready` al Orchestrator (post-bucle)
- **Afecta:**
  - `dedicated_activation_service.py`: quitar transición de `mark_ready` (`:129-151`),
    conservar idempotencia+marker.
  - `dedicated_provisioning_orchestrator.py`: transición terminal tras el bucle
    (`:306`), simétrica con `_fail_step_and_run:685`.
- **No toca:** state service (guard intacto), DDL, contratos, compensación, métricas.
- **Shared:** N/A.
- **Retry/Redispatch:** ▲ — auto-sanable: crash pre-transición → redispatch omite
  steps completed y ejecuta transición post-bucle → READY.
- **Tests:** `test_f4_08`, `test_f4_09_orchestrator_activation`, `test_f4_09_dedicated_activation`
  (mark_ready ya no transiciona), `test_hybrid_provisioning_e2e`, harness.

### C — `finalize_success()`
- **Afecta:** como B + un método nuevo `finalize_success` (host: orquestador o
  servicio). El orquestador deja de usar `mark_step_completed` genérico (`:299`) para
  MARK_READY.
- **No toca:** DDL, contratos, compensación, métricas.
- **Retry:** ▲ (si dos commits) / ▲ (si una UoW → converge con D).
- **Tests:** como B + tests del método nuevo.

### D — Atómico en `TenantProvisioningStateService`
- **Afecta:**
  - `tenant_provisioning_state_service.py`: método atómico nuevo
    `finalize_run_success` (una UoW: lock → close step → run READY → cliente READY).
  - `dedicated_provisioning_orchestrator.py`: usar el método atómico para el step
    terminal (saltar el `mark_step_completed` genérico `:299`).
  - `dedicated_activation_service.py`: quitar transición de `mark_ready`.
- **No toca:** DDL, contratos, compensación, métricas.
- **Retry/Redispatch:** ▲ (estado consistente; sin ventana). Pero requiere manejar el
  redispatch con MARK_READY en estado RUNNING (ver `59` R-D2).
- **Tests:** state service (`test_f4_02`), orquestador (`test_f4_08/09`), activation,
  e2e, harness → mayor superficie.

## 3. Comunes a TODAS (A/B/C/D)

| Eje | Resultado | Evidencia |
|---|---|---|
| Contrato API §9.1 (10 códigos) | **Intacto** | MARK_READY se conserva como step |
| Contrato UI "10 steps" | **Intacto** | `steps[]` sigue con 10 entradas |
| Migraciones/DDL | **Ninguna** | No se toca `V032`/`tables.py`; `CK_tps_step_code` intacto |
| Shared onboarding | **Sin impacto** | La saga es exclusiva de Dedicated |
| Compensación | **Sin cambio funcional** | `_COMPENSATION_STEP_ORDER` sigue igual; rama no-op (`compensation:210-212`) |
| Métricas | **Sin cambio** | `ready`/`step.completed` siguen aplicando; sin emisor en código |
| `ready_at` | **Preservado** | Sigue seteándose en `transition_run_to_ready:292-300` |
| `current_step_code` | **Preservado** | `=MARK_READY` en la transición (`:298`) |

Conclusión de impacto: ninguna alternativa toca contratos, DDL, Shared, compensación
ni métricas. La diferencia está en **archivos tocados**, **ventana de consistencia**
y **superficie de test**. Validación formal y riesgos en `59`.
