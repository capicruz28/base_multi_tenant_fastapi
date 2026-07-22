# 49 — F17J: Auditoría de la máquina de estados del Provisioning

> Fase **F17J**. 100% auditoría arquitectónica. **No** se modificó código, SQL,
> tests, bootstrap, onboarding ni manifests. **No** se propone solución (eso se
> reserva; aquí solo se valida el modelo). Toda afirmación cita `archivo:línea`.

## 0. Artefactos analizados

| Componente | Archivo |
|---|---|
| Orchestrator | `app/modules/tenant/application/services/dedicated_provisioning_orchestrator.py` |
| State service | `app/modules/tenant/application/services/tenant_provisioning_state_service.py` |
| Activation service | `app/infrastructure/provisioning/dedicated_activation_service.py` |
| Reglas run | `app/modules/tenant/application/provisioning/provisioning_transition_rules.py` |
| Reglas step | `app/modules/tenant/application/provisioning/provisioning_step_transition_rules.py` |
| Enum run | `app/modules/tenant/application/provisioning/provisioning_state.py` |
| Enum step | `app/modules/tenant/application/provisioning/provisioning_step_status.py` |
| Códigos step | `app/modules/tenant/application/provisioning/provisioning_step_code.py` |
| Esquema BD | `app/bootstrap_v2/01_schema/V032__tenant_provisioning_state.sql` |

## 1. El modelo persistido (fuente de verdad = BD)

`V032__tenant_provisioning_state.sql`:

### 1.1 `tenant_provisioning_run` — el RUN (agregado saga)
- `provisioning_state NVARCHAR(20)` con `CK_tpr_provisioning_state CHECK IN
  ('provisioning','ready','failed')` (`:18,40-42`).
- Columnas de outcome del RUN: `ready_at` (`:27`), `failed_at` (`:28`),
  `last_error_code/message` (`:30-31`), `current_step_code` (`:23`).

### 1.2 `tenant_provisioning_step` — el STEP (marker por paso)
- `step_status NVARCHAR(20)` con `CK_tps_step_status CHECK IN
  ('pending','running','completed','failed','skipped')` (`:104-105`).
- `step_code` con `CK_tps_step_code` que incluye **`'mark_ready'`** como paso
  válido (`:90-102`).

### 1.3 Denormalización en `cliente`
- `cliente.provisioning_state` refleja el estado del RUN (`:117-125`).

**Lectura estructural:** hay **dos** ejes de estado (RUN y STEP) y — clave — el
concepto "ready" aparece **duplicado**: como estado terminal del RUN
(`provisioning_state='ready'` + `ready_at`) y como un STEP (`step_code='mark_ready'`).

## 2. Las dos máquinas de estados (a nivel código)

### 2.1 RUN (`provisioning_transition_rules.py:9-17`)
```
PROVISIONING → { READY, FAILED }
FAILED       → { PROVISIONING }
READY        → { }        (terminal)
```
Enum: `TERMINAL_PROVISIONING_STATES = {READY, FAILED}`,
`NON_TERMINAL = {PROVISIONING}` (`provisioning_state.py:17-23`).

### 2.2 STEP (`provisioning_step_transition_rules.py:9-21`)
```
PENDING   → { RUNNING, SKIPPED }
RUNNING   → { COMPLETED, FAILED }
FAILED    → { RUNNING }
COMPLETED → { }   (terminal)
SKIPPED   → { }   (terminal)
```
Enum: `TERMINAL_STEP_STATUSES = {COMPLETED, FAILED, SKIPPED}`
(`provisioning_step_status.py:17-23`).

### 2.3 El acoplamiento duro entre ambas
`tenant_provisioning_state_service._transition_step:485-491`: **cualquier** mutación
de STEP exige `run == PROVISIONING`. Por tanto: **RUN no-terminal ⇒ condición
necesaria para tocar STEPs**. En cuanto el RUN entra en READY (terminal), los STEPs
quedan congelados para siempre.

## 3. Respuesta 1 — ¿READY es un Step o un estado final del Run?

**READY es un estado FINAL del RUN (Opción B).** Evidencia:
- Columna `provisioning_state` y `CK_tpr_provisioning_state` viven en la tabla
  **RUN** (`V032:18,40-42`); `ready_at` es del RUN (`V032:27`).
- Enum `ProvisioningState.READY` con `TERMINAL_PROVISIONING_STATES`
  (`provisioning_state.py:9,17-19`).
- `provisioning_transition_rules.py:16` — READY es terminal del RUN.
- El contrato público v1 (docstring `provisioning_state.py:6`,
  "DEDICATED_PROVISIONING_API_CONTRACT §7") expone el estado a nivel RUN.
- La denormalización `cliente.provisioning_state` (`V032:117-125`) refleja el RUN.

`mark_ready` **también** existe como STEP (`V032:101`, `SAGA_STEP_ORDER`
`provisioning_step_code.py:32`), pero eso es una **proyección redundante** del mismo
hecho ("tenant listo") sobre el eje STEP. La autoridad conceptual de "ready" es el
RUN; el step `mark_ready` es una duplicación del mismo estado en otro eje.

## 4. Respuesta 2 — ¿Tiene sentido un Step MARK_READY?

**No con su semántica actual.** Análisis por naturaleza de cada paso:

| Step | ¿Efecto colateral propio distinto del estado del run? |
|---|---|
| S1 registry | Sí (validación snapshot) |
| S2 storage_allocation | Sí (asigna storage) |
| S3 create_database | Sí (crea BD física) |
| S4 apply_schema_erp | Sí (DDL V010) |
| S5 apply_schema_rbac | Sí (DDL V020/RBAC) |
| S6 apply_catalogs | Sí (seeds catálogo) |
| S7 seed_tenant | Sí (seed tenant + RBAC runtime) |
| S8 register_metadata | Sí (metadata CP de conexión) |
| S9 activate_routing | Sí (invalida cache + smoke routing) |
| **S10 mark_ready** | **No: su único efecto es la transición terminal del RUN** |

S1–S9 son pasos legítimos con trabajo propio. **S10 no ejecuta trabajo propio**:
su cuerpo (`dedicated_activation_service.mark_ready:130`) sólo llama
`transition_run_to_ready`, que es una transición de la máquina de estados del RUN.
Modelar la transición terminal del RUN como un STEP que además debe "completarse"
(mientras el RUN sigue no-terminal) es **auto-contradictorio**: el propio cuerpo del
step destruye la precondición (`run=PROVISIONING`) que el cierre del step necesita
(`_transition_step:485`).

Conclusión: READY debería ser exclusivamente una transición de estado del RUN
(disparada tras el último paso real, S9). Un marker `mark_ready` sólo tendría
sentido si su **cierre** estuviera desacoplado de **realizar** la transición del RUN.

## 5. Respuesta 6 — ¿Algún OTRO step cambia el estado del RUN dentro de su ejecución?

**NO.** Recorrido de todos los ejecutores de step
(`dedicated_provisioning_orchestrator.py`):

| Ejecutor | ¿Muta `run.status`? | Evidencia |
|---|---|---|
| `_step_registry` | No | 402-413 |
| `_step_storage_allocation` | No | 415-428 |
| `_step_create_database` | No | 430-448 |
| `_run_bootstrap_block` / `_mark_bootstrap_saga_steps` | No (sólo STEPs) | 450-569 |
| `_step_apply_catalogs` | No | 585-600 |
| `_step_seed_tenant` | No | 602-626 |
| `_step_activation` (REGISTER_METADATA) | No | 649-651 |
| `_step_activation` (ACTIVATE_ROUTING) | No | 652-654 |
| **`_step_activation` (MARK_READY)** | **Sí** → `transition_run_to_ready` | 655-657 → activation:130 |

Único caso: **S10 MARK_READY**. (Aparte, `_fail_step_and_run:685` transiciona el
RUN a FAILED, pero es el **manejador de fallo**, no el cuerpo normal de un step.)

## 6. Respuesta 7 — ¿Dónde podría reaparecer el mismo problema?

El defecto pertenece a una **clase** de problema: "el cuerpo de un step muta el
estado del RUN y luego el bucle genérico intenta cerrar ese step". Hoy sólo lo
provoca S10, pero la superficie de riesgo es:

1. **El bucle genérico asume que ningún cuerpo de step toca `run.status`**
   (`orchestrator.py:284→290→299`). Cualquier step futuro que llame
   `transition_run_to_ready` / `transition_run_to_failed` / `begin_retry` dentro de
   su cuerpo reproducirá el conflicto `PROVISIONING_RUN_NOT_ACTIVE`.
2. **Ruta de recuperación rota:** tras el fallo, el RUN queda READY y
   `step[mark_ready]=RUNNING`. `begin_retry_from_failed` exige estado FAILED
   (`state:208-212`), no READY, así que no puede recuperar; el redispatch hace
   "Saga noop" (`orchestrator:201-213`). El step queda RUNNING de forma permanente
   → segundo punto de manifestación (inconsistencia irreparable por los flujos
   existentes).
3. **`_first_incomplete_saga_order`** (`state:553-561`) consideraría `mark_ready`
   incompleto, pero sólo se usa desde retry (que requiere FAILED) → inalcanzable.

## 7. Respuesta 8 — ¿Bug puntual (A) o diseño incorrecto (B)?

**B — consecuencia de un diseño incorrecto de la máquina de estados**, con
manifestación puntual en S10. Justificación con evidencia:

- Existe **doble representación** del mismo hecho "ready": `run.state=READY`
  (`V032:18,40-42`) y `step[mark_ready]=COMPLETED` (`V032:101`). Dos ejes intentan
  codificar lo mismo.
- El invariante "los steps sólo mutan si run=PROVISIONING"
  (`_transition_step:485`) es **correcto y deseable**, pero es **incompatible** con
  modelar la transición terminal del RUN como un STEP cuyo cuerpo realiza esa
  transición. La contradicción es de modelo, no de una línea.
- No es un simple "orden de líneas mal puesto": incluso reordenar exige **decidir
  qué significa** cerrar el step `mark_ready` respecto de la transición del RUN
  (¿el step se cierra antes de que el run esté realmente ready? ¿la transición del
  run cierra el step?). Eso es una decisión de modelado, no un swap mecánico.
- La manifestación, sin embargo, está **acotada a un único punto** (S10), por lo que
  el radio de impacto es pequeño.

Veredicto de esta sección: **defecto de diseño (B) con blast radius de 1 step.**

Continúa en `50_RUNTIME_RESPONSIBILITY_ANALYSIS.md` (responsabilidades, timing,
punto de corrección), `51_STATE_MACHINE_DIAGRAM.md` (flujo ideal + diagrama) y
`52_FINAL_ARCHITECTURAL_VERDICT.md` (veredicto único).
