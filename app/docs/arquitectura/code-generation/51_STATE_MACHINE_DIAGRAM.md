# 51 — F17J: Diagrama y flujo ideal de la saga

> Fase F17J. Solo auditoría/documentación. El "flujo ideal" describe el
> comportamiento correcto según la máquina de estados **ya existente**; no es un
> parche ni implica cambios de reglas/enums.

## 1. Respuesta 4 — Flujo ideal de la saga (Run / Step / Estado / Transición / Commit)

Premisa (probada en `50` §2): todas las mutaciones de STEP ocurren con
`run=PROVISIONING`; la transición `PROVISIONING→READY` es el **acto terminal** tras
cerrar el último step.

Leyenda: RUN = estado del run tras la fila · STEP = estado del step tras la fila.

| # | Paso | Acción (worker) | STEP transición | RUN transición | Commit | RUN | STEP |
|---|---|---|---|---|---|---|---|
| 0 | init | `initialize_provisioning_run` | crea 10 steps PENDING | ∅→PROVISIONING | UoW init | PROVISIONING | (todos PENDING) |
| S1 | registry | validar snapshot | PENDING→RUNNING→COMPLETED | — | 2 UoW (running, completed) | PROVISIONING | COMPLETED |
| S2 | storage_allocation | asignar storage | RUNNING→COMPLETED | — | idem | PROVISIONING | COMPLETED |
| S3 | create_database | crear BD física | RUNNING→COMPLETED | — | idem | PROVISIONING | COMPLETED |
| S4 | apply_schema_erp | DDL V010 | RUNNING→COMPLETED | — | idem | PROVISIONING | COMPLETED |
| S5 | apply_schema_rbac | DDL V020/RBAC | RUNNING→COMPLETED | — | idem | PROVISIONING | COMPLETED |
| S6 | apply_catalogs | seeds catálogo | RUNNING→COMPLETED | — | idem | PROVISIONING | COMPLETED |
| S7 | seed_tenant | seed tenant + RBAC runtime | RUNNING→COMPLETED | — | idem | PROVISIONING | COMPLETED |
| S8 | register_metadata | metadata CP conexión | RUNNING→COMPLETED | — | idem | PROVISIONING | COMPLETED |
| S9 | activate_routing | invalidar cache + smoke | RUNNING→COMPLETED | — | idem | PROVISIONING | COMPLETED |
| **T** | **terminal** | cerrar último step **y luego** transicionar run | (último step)→COMPLETED **primero** | **PROVISIONING→READY** (después) | cierre step (run=PROVISIONING) → transición run | **READY** | COMPLETED |

Dos variantes válidas del bloque terminal **T** (la elección es la decisión de
modelo — ver `52`):

- **Variante T1 (mark_ready se mantiene como STEP):**
  `mark_step_running(mark_ready)` [PROVISIONING] → `mark_step_completed(mark_ready)`
  [PROVISIONING] → `transition_run_to_ready` [→READY]. El cuerpo del step **no**
  transiciona el run; la transición es posterior y separada.
- **Variante T2 (mark_ready deja de ser STEP):** el último step es S9; tras cerrarlo
  con run=PROVISIONING, `transition_run_to_ready` [→READY] como único acto terminal.

En ambas, el orden respeta: **cerrar step(s) con run=PROVISIONING → transicionar run
a READY**.

### Contraste con el flujo ACTUAL (defectuoso, S10)

| # | Acción | RUN | STEP mark_ready | Resultado |
|---|---|---|---|---|
| 1 | `mark_step_running(mark_ready)` (orch:284) | PROVISIONING | RUNNING | OK |
| 2 | `transition_run_to_ready` **dentro** del cuerpo (activation:130) | **READY** | RUNNING | commit READY |
| 3 | log "Tenant dedicated ready" (activation:153) | READY | RUNNING | — |
| 4 | `mark_step_completed(mark_ready)` (orch:299) | READY | RUNNING | **ConflictError** (guard :485) |

## 2. Respuesta 9 — Diagrama completo (flujo correcto)

```
                         ┌──────────────────────────────────────────┐
                         │   RUN provisioning_run.provisioning_state │
                         └──────────────────────────────────────────┘

     initialize_provisioning_run
                 │  (∅ → PROVISIONING, crea 10 steps PENDING)
                 ▼
        ┌───────────────────┐
        │  RUN = PROVISIONING │◀───────────────────────────┐ (retry: FAILED→PROVISIONING)
        └───────────────────┘                              │
                 │                                          │
                 │  por cada step S1..Sn (n = último):      │
                 ▼                                          │
      ┌───────────────────────────────┐                    │
      │ STEP: PENDING                  │                    │
      │   → RUNNING   (mark_step_running, run=PROVISIONING) │
      │   → [trabajo del step]         │                    │
      │   → COMPLETED (mark_step_completed, run=PROVISIONING)│
      │        │ (si falla: RUNNING→FAILED + RUN→FAILED)────┘ (→ compensación/retry)
      └────────┼──────────────────────┘
               │  (todos los steps COMPLETED, RUN aún = PROVISIONING)
               ▼
   ┌──────────────────────────────────────────────┐
   │ ACTO TERMINAL (único, tras cerrar último step)│
   │   transition_run_to_ready()                    │
   │   PROVISIONING → READY  (ready_at, cliente)    │
   └──────────────────────────────────────────────┘
               │
               ▼
        ┌──────────────┐
        │  RUN = READY  │  (terminal — "Finished": tenant operativo)
        └──────────────┘
```

Mapa Run ↓ Step ↓ Running ↓ Completed ↓ Ready ↓ Finished (pedido en Q9):

```
RUN(PROVISIONING)
   └─ STEP(PENDING) ─▶ RUNNING ─▶ COMPLETED   [se repite S1..último, run=PROVISIONING]
        (último STEP COMPLETED, aún run=PROVISIONING)
RUN: PROVISIONING ─▶ READY        [transición terminal, DESPUÉS del último COMPLETED]
RUN(READY) = "Finished"           [terminal, sin salidas]
```

Invariante que el diagrama preserva (y que el flujo actual viola):
**"Ready" del RUN se alcanza sólo cuando todos los STEPs ya están en estado
terminal COMPLETED, nunca antes ni durante el cierre del último step.**
