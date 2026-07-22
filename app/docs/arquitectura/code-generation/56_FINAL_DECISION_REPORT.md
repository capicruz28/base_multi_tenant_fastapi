# 56 — F17K: Informe final de decisión (eliminar MARK_READY)

> Fase F17K. Solo auditoría. Veredicto fundamentado exclusivamente en la evidencia
> de `53`, `54`, `55`. No se propone implementación.

## 1. Respuesta 11 — ¿Refactor local (A) o cambio transversal (B)?

**B — cambio transversal.** Evidencia consolidada (todas verificadas):

| Eje afectado | Evidencia |
|---|---|
| Fuente de verdad | `provisioning_step_code.py:15,32` |
| Persistencia/DDL | `V032:90-102` (CHECK) + filas históricas |
| ORM | `tables.py:155` |
| Contrato API v1 público | `DEDICATED_PROVISIONING_API_CONTRACT.md:305` §9.1 |
| Contrato UI (frontend) | `PLATFORM_ADMIN_TENANT_ONBOARDING_UI_CONTRACT.md:354` "10 steps" |
| Lógica saga/activación/compensación/estado | orchestrator, activation, compensation, state_service |
| Observabilidad (spec) | `HYBRID_F4_PROVISIONING_METRICS_MANIFEST.json:22-23` |
| Tests/scripts | ~8 archivos |

Abarca backend + persistencia + 2 contratos públicos + frontend + observabilidad +
tests. No es aislable → **transversal**.

## 2. Respuesta 12 — ¿Es arquitectónicamente recomendable eliminar COMPLETAMENTE MARK_READY?

# NO

Justificación **exclusivamente por evidencia**:

1. **Está expuesto en contratos públicos v1** que hay que romper para eliminarlo:
   - API `DEDICATED_PROVISIONING_API_CONTRACT.md` §9.1 (`:305`) enumera `mark_ready`
     como código de step del contrato **canónico** v1.
   - UI `PLATFORM_ADMIN_TENANT_ONBOARDING_UI_CONTRACT.md` §8.3 (`:354`) fija
     explícitamente "**10 steps**" y §5 (`:156`) lista `mark_ready`.
   → Eliminarlo obliga a revisar contratos públicos y coordinar con el Frontend
   (consumidor externo). No es transparente.

2. **Es un cambio transversal (Q11=B)**, no un refactor local: toca fuente de verdad,
   DDL + datos existentes, ORM, 2 contratos, métricas, 4 servicios y ~8 tests (`53`).

3. **La eliminación NO es necesaria para corregir el defecto** encontrado en F17J/F17I:
   - El defecto es de **orden/acoplamiento** (`47`, `52`): el cuerpo del step realiza
     la transición terminal del RUN antes de cerrar el step.
   - Es **corregible sin eliminar** el step (F17J opciones T1/atómica): mantener
     `mark_ready` como marker de observabilidad y (a) cerrarlo con run=PROVISIONING y
     transicionar el RUN después, o (b) cerrar el step atómicamente dentro de
     `transition_run_to_ready`. Ambas preservan el contrato de 10 pasos.
   → Existiendo una corrección de menor blast radius que respeta los contratos, la
   eliminación completa es desproporcionada.

4. **La eliminación tampoco es imprescindible funcionalmente**: la autoridad de
   "ready" ya es el estado del RUN (`49`), y ningún FK, índice, emisor de métricas ni
   reporte **depende** del step (`55`). Es decir, el step es prescindible en efecto,
   pero su prescindibilidad **no obliga** a removerlo; sólo confirma que puede
   degradarse a marker sin efectos colaterales.

**Contra-evidencia registrada (transparencia):** existen argumentos a favor de
eliminar —duplicación conceptual de "ready" (`49`/`52`), ausencia de efecto colateral
(compensación no-op `compensation:210-212`), y que hoy el criterio FE "todos los steps
completed" nunca se cumple por el bug (`55` §1)—. Pero esa evidencia sustenta
**corregir/degradar** el step, no necesariamente **eliminarlo completamente** rompiendo
contratos v1.

**Conclusión del veredicto:** **NO** eliminar completamente MARK_READY. La dirección
respaldada por la evidencia es **conservarlo como marker observacional** y corregir el
acoplamiento de orden (decisión de diseño T1/atómica de `52`), manteniendo el contrato
público de 10 pasos. Si en el futuro se aprueba una **revisión del contrato v1** (API +
UI) con coordinación de Frontend, la eliminación pasaría a ser viable, pero seguiría
siendo un **cambio transversal**, no un refactor local.

## 3. Respuestas consolidadas F17K

| # | Pregunta | Respuesta |
|---|---|---|
| 1 | Consumidores | Ver `54` §1 (enum, orquestador, activation, compensación, state, ORM, DDL, API+UI contract, métricas spec, ~8 tests) |
| 2 | ¿API espera 10 steps? | **SI** (API §9.1 `:305`; UI §8.3 `:354`; DTO `steps[]`) |
| 3 | ¿UI renderiza 10 steps? | **SI** (UI §7.4/§8.3/§5; render dinámico de `steps[]`) |
| 4 | ¿Progreso por conteo de steps? | Backend **NO**; contrato FE **SÍ** (§7.5 "todos completed") |
| 5 | ¿Persistencia depende? | CHECK + filas + queries por código; sin FK/índice por step_code |
| 6 | ¿Auditoría/logging específico? | No del step; sólo log "ready" ligado a transición del RUN |
| 7 | ¿Retry lo espera? | Retry genérico (SAGA_STEP_ORDER); compensación lo lista como no-op |
| 8 | ¿Monitoreo lo espera? | Sólo manifiesto (spec); sin emisor en código |
| 9 | ¿Docs asumen 10 pasos? | **SI** (API §9.1, UI §8.3, V032 comment, docstring) |
| 10 | Archivos a modificar | Alto/Medio/Bajo en `53` §3 |
| 11 | ¿Local o transversal? | **B — transversal** |
| 12 | ¿Eliminar por completo? | **NO** (romper contratos v1 + transversal + corregible sin eliminar) |
