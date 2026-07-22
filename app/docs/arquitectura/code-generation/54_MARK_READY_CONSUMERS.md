# 54 — F17K: Consumidores de MARK_READY

> Fase F17K. Solo auditoría. Responde Q1, Q2, Q3.

## 1. Respuesta 1 — Inventario COMPLETO de consumidores de MARK_READY

Clasificados por tipo. Cada uno con `archivo:línea` y forma de consumo.

### A. Definición / fuente de verdad
| Consumidor | Línea | Uso |
|---|---|---|
| `provisioning_step_code.py` | :15 | Define `ProvisioningStepCode.MARK_READY = "mark_ready"` |
| `provisioning_step_code.py` | :32 | Lo incluye en `SAGA_STEP_ORDER` (paso 10) |
| `provisioning/__init__.py` | :23,67 | Re-exporta `SAGA_STEP_ORDER` |

### B. Lógica de saga / activación / estado
| Consumidor | Línea | Uso |
|---|---|---|
| `dedicated_provisioning_orchestrator.py` | :394-395 | Ruta el step MARK_READY a `_step_activation` |
| `dedicated_provisioning_orchestrator.py` | :655-656 | `_step_activation` invoca `activation.mark_ready()` |
| `dedicated_provisioning_orchestrator.py` | :745 | Mapa de error `MARK_READY → PROVISIONING_ACTIVATION_FAILED` |
| `dedicated_provisioning_orchestrator.py` | :284,290,299 | Bucle genérico (running/execute/completed) que lo cierra |
| `dedicated_activation_service.py` | :108-162 | Método `mark_ready` (idempotencia, transición, log) |
| `dedicated_activation_service.py` | :124,137,159 | Devuelve `step_code=MARK_READY` en resultados |
| `dedicated_activation_service.py` | :40 | `_S10_MARKER_PREFIX = "ready_run"` (marker idempotencia) |
| `tenant_provisioning_state_service.py` | :298 | `transition_run_to_ready` fija `current_step_code=MARK_READY` |

### C. Compensación / retry
| Consumidor | Línea | Uso |
|---|---|---|
| `dedicated_provisioning_compensation_service.py` | :60 | `_COMPENSATION_STEP_ORDER` lista MARK_READY (primero, orden inverso) |
| `dedicated_provisioning_compensation_service.py` | :210-212 | Rama de compensación **no-op** (solo registra; sin acción física) |

### D. Derivados (sin lógica propia; auto-generados desde SAGA_STEP_ORDER)
| Consumidor | Línea | Uso |
|---|---|---|
| `tenant_provisioning_step_queries_core.py` | :33-51 | `build_initial_step_rows` genera la fila mark_ready al iterar `SAGA_STEP_ORDER` |
| `provisioning_status_read.py` | :22-40 | DTO expone `steps[]`/`current_step` (incluye mark_ready si existe) |

### E. Persistencia
| Consumidor | Línea | Uso |
|---|---|---|
| `V032__tenant_provisioning_state.sql` | :101 | `CK_tps_step_code` permite `'mark_ready'` |
| `tables.py` | :155 | Espejo ORM del CHECK |
| (datos) | — | Filas `tenant_provisioning_step` existentes con `step_code='mark_ready'` |

### F. Contratos públicos (consumidores externos / FE)
| Consumidor | Línea | Uso |
|---|---|---|
| `DEDICATED_PROVISIONING_API_CONTRACT.md` | :305 | §9.1 expone código `mark_ready` (S10) |
| `DEDICATED_PROVISIONING_API_CONTRACT.md` | :63,251,503,518 | Flujo S10, transición, evento ready |
| `PLATFORM_ADMIN_TENANT_ONBOARDING_UI_CONTRACT.md` | :156 | §5 etiqueta UI "Tenant Ready" |
| `PLATFORM_ADMIN_TENANT_ONBOARDING_UI_CONTRACT.md` | :354 | §8.3 "Timeline steps | 10 steps" |
| `PLATFORM_ADMIN_TENANT_ONBOARDING_UI_CONTRACT.md` | :287,299 | Render `steps[]`; progreso = todos completed |

### G. Observabilidad (especificación, sin emisor en código)
| Consumidor | Línea | Uso |
|---|---|---|
| `HYBRID_F4_PROVISIONING_METRICS_MANIFEST.json` | :22-23 | `dedicated.provisioning.ready` "when S10 mark_ready" |
| `HYBRID_F4_PROVISIONING_METRICS_MANIFEST.json` | :14-19 | `dedicated.provisioning.step.completed` por step |
| (código emisor) | — | **NO existe** en `app/` (0 coincidencias del nombre de evento) |

### H. Tests / scripts
`test_f4_01_provisioning_domain_types.py`, `test_f4_02_provisioning_state_service.py`,
`test_f4_08_dedicated_orchestrator.py`, `test_f4_09_orchestrator_activation.py`,
`test_f4_09_dedicated_activation.py`, `test_hybrid_provisioning_e2e.py`,
`provisioning_e2e_harness.py`, `scripts/validate_f4_provisioning_e2e.py`.

## 2. Respuesta 2 — ¿API pública que espera exactamente 10 steps? SI/NO

**SI.**
- **Contrato:** `DEDICATED_PROVISIONING_API_CONTRACT.md` §9.1 (`:296-305`) enumera
  **10 códigos de step** (S1…S10) incluyendo `mark_ready`; objeto `step` (`:307-314`).
- **DTO:** `DedicatedProvisioningStatusSnapshot` (`provisioning_status_read.py:22-40`)
  expone `steps: List[ProvisioningStepStatusRead]` + `current_step` (shape alineado
  a §9 del contrato).
- **Endpoint:** `GET .../provisioning-status` devuelve ese snapshot con la lista de
  steps.
- **Frontend:** Platform Admin (contrato UI, ver Q3).
- **Cuantía exacta "10":** declarada en UI contract §8.3 (`:354` "10 steps") y en la
  docstring `build_initial_step_rows` (`:38` "los 10 steps saga").

## 3. Respuesta 3 — ¿UI que renderiza los 10 steps? SI/NO

**SI.** Evidencia en `PLATFORM_ADMIN_TENANT_ONBOARDING_UI_CONTRACT.md`:
- §7.4 (`:287`): "Barra progreso / steps — Renderizar `steps[]` del status;
  resaltar `current_step`".
- §8.3 (`:354`): "Timeline steps — **10 steps** §5 — estados
  `pending/running/completed/failed/skipped`".
- §5 (`:145-156`): tabla de 10 steps con etiquetas UI, incluida `mark_ready` →
  "Tenant Ready".
- §7.5 (`:299`): "Progreso — Todos los steps `completed`".

> Matiz: el render es **dinámico** sobre `steps[]` (no una lista fija de 10 en el
> cliente), pero el contrato **documenta** explícitamente 10 pasos e incluye
> `mark_ready` como uno de ellos. La navegación a "Ready" se decide por
> `provisioning_state=ready` (`:419`), no por el step.
