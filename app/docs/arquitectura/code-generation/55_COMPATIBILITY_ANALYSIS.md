# 55 — F17K: Análisis de compatibilidad

> Fase F17K. Solo auditoría. Responde Q5, Q6, Q7, Q8, Q9. Determina qué se rompería
> si MARK_READY se eliminara completamente.

## 1. Respuesta 5 — Persistencia que depende de MARK_READY

| Elemento | ¿Depende? | Evidencia |
|---|---|---|
| Tabla `tenant_provisioning_step` | Sí (filas) | Cada run materializa una fila `step_code='mark_ready'` (`build_initial_step_rows` :33-51) |
| CHECK `CK_tps_step_code` | Sí | `V032:90-102` lista `'mark_ready'` entre los valores permitidos |
| Espejo ORM del CHECK | Sí | `tables.py:155` |
| FK sobre `step_code` | No | No hay FK sobre step_code (solo FK a run/cliente, `V032:77-85`) |
| Índices sobre `step_code` | No | Índices por `(run_id, saga_order)` y `cliente_id` (`V032:108-112`); ninguno por step_code |
| Consultas | Sí (por código) | `select_step_by_code_stmt` (:79-90); orquestador usa `steps_by_code[...]` |
| Reportes | No encontrados | Sin reportes/vistas específicos de mark_ready |

**Efecto de eliminar:** dejar de insertar la fila (quitando de `SAGA_STEP_ORDER`) no
rompe el CHECK (que **permite** pero no **exige** mark_ready). Las filas históricas
seguirían conteniendo `mark_ready`. No hay FK/índice que se rompa. Un CHECK más
estricto o limpieza de datos serían opcionales, no obligatorios para operar.

## 2. Respuesta 6 — Auditoría/logging específico del step

- Log de negocio "Tenant dedicated ready" (`dedicated_activation_service.py:153`) —
  está ligado a la **transición del RUN a READY**, no al cierre del step; sobrevive
  aunque el step desaparezca.
- Logging genérico de steps (mark_step_* / diagnósticos `[F4-DIAG]`) no es específico
  de mark_ready.
- **No** existe tabla/registro de auditoría dedicado a `mark_ready`.

Conclusión: no hay auditoría/logging que **dependa** del step como tal; el único log
semánticamente "ready" pertenece a la transición del RUN.

## 3. Respuesta 7 — Retry que espera ese step

- `begin_retry_from_failed` (`tenant_provisioning_state_service.py:176-262`) y
  `_first_incomplete_saga_order` (`:553-561`) operan **genéricamente** sobre
  `SAGA_STEP_ORDER`; no codifican mark_ready explícitamente. Requieren estado
  `FAILED` para reanudar (`:208-212`).
- Compensación: `_COMPENSATION_STEP_ORDER` (`compensation:59-68`) **incluye**
  MARK_READY como primer elemento (orden inverso), pero su rama es **no-op**
  (`:210-212`: sólo lo registra en `compensated`, sin acción física — porque marcar
  ready no tiene efecto colateral reversible).

**Efecto de eliminar:** el retry genérico no se rompe (deriva de SAGA_STEP_ORDER);
`_COMPENSATION_STEP_ORDER` requeriría quitar la entrada mark_ready (impacto bajo, es
no-op). Ningún flujo de retry/compensación **requiere** que el step exista.

## 4. Respuesta 8 — Monitoreo que espera ese step

- `HYBRID_F4_PROVISIONING_METRICS_MANIFEST.json`:
  - `dedicated.provisioning.ready` "when: S10 mark_ready" (`:22-23`) — es el evento
    de **READY del RUN**; conceptualmente sobrevive a la eliminación del step.
  - `dedicated.provisioning.step.completed` por step (`:14-19`) — pasaría de 10 a 9
    emisiones/serie.
- **No hay emisor real en `app/`** (grep de nombres de evento → 0). El manifiesto es
  **especificación**, no runtime.

**Efecto de eliminar:** documental (actualizar manifiesto). No hay dashboards/alertas
en código que se rompan.

## 5. Respuesta 9 — Documentación oficial que asume exactamente 10 pasos

**SI.** Referencias que fijan "10 pasos / S1–S10":
- `PLATFORM_ADMIN_TENANT_ONBOARDING_UI_CONTRACT.md` §8.3 (`:354`) "10 steps"; §5
  tabla S1–S10 (`:145-156`); §5 "saga S1…S10" (`:133`).
- `DEDICATED_PROVISIONING_API_CONTRACT.md` §9.1 (10 códigos, `:296-305`); §5
  "S1–S10"; múltiples referencias "S10".
- `V032__tenant_provisioning_state.sql:56` comentario "markers por paso saga (S1–S10)".
- `tenant_provisioning_step_queries_core.py:38` docstring "los 10 steps saga".
- Contratos aguas arriba referenciados: "BL-F4-1.0 §5 Saga S1–S10".

## 6. Matriz de compatibilidad si MARK_READY se elimina

| Superficie | ¿Se rompe? | Naturaleza |
|---|---|---|
| Enum/SAGA_STEP_ORDER | Cambia | Fuente de verdad (edición obligada) |
| Inserción inicial de steps | Auto | Deriva de SAGA_STEP_ORDER (sin edición lógica) |
| CHECK `CK_tps_step_code` | No rompe | Permite pero no exige; edición opcional |
| Datos históricos | Persisten | Filas antiguas conservan mark_ready |
| Contrato API §9.1 | **Rompe (documental)** | v1 público lista mark_ready → revisión |
| Contrato UI "10 steps" | **Rompe (documental)** | pasa a 9; FE render dinámico no rompe funcional |
| Progreso FE "todos completed" | Mejora | 9/9 se cumple (hoy 10 nunca por bug F17I) |
| Retry genérico | No rompe | Deriva de SAGA_STEP_ORDER |
| Compensación | Edición menor | Quitar entrada no-op |
| Métricas (manifiesto) | Documental | `ready` sobrevive; `step.completed` 10→9 |
| Emisor de métricas en código | N/A | No existe |
| Logging "ready" | No rompe | Ligado a transición del RUN |
| Tests/harness/scripts | Rompen | ~8 archivos asumen 10 steps/mark_ready |

Conclusión de compatibilidad: la eliminación es **funcionalmente viable** (el
concepto "ready" autoritativo es el estado del RUN, no el step; sin FK/emisor/reporte
que dependa del step), pero **impacta contratos públicos v1 (API + UI) y ~8 tests**,
por lo que no es transparente para consumidores externos. Veredicto en `56`.
