# 41 — F17 Remediation Options (Opciones de remediación)

> Fase **F17G**. Solo lectura. Este documento **enumera** opciones; **no**
> implementa, corrige ni modifica código. La decisión y ejecución serían una fase
> posterior explícita.

Contexto (de `40_F17_ROOT_CAUSE.md`):

- La corrección F17F (checksum V010) es **correcta** y debe conservarse.
- Tras F17F quedan expuestos dos fallos del tramo S6→S7 cuyo código es **previo a
  F17**: `FK_permiso_menu` (S7 RBAC) y `PROVISIONING_RUN_NOT_ACTIVE` (cascada/retry).

---

## 0. Paso previo imprescindible: capturar evidencia de runtime

Antes de decidir, obtener (sin cambiar código) sobre **una BD dedicada recién
creada** que llegue a S7:

1. `SELECT COUNT(*) FROM modulo_menu;` inmediatamente **después de S6**.
2. El `menu_id` exacto de la fila `rol_menu_permiso` que dispara `FK_permiso_menu`
   (log del bundle: `OwnerSync` / `BaseOperative`).
3. Estado del `provisioning_run` (`provisioning_state`) y de sus `provisioning_step`
   cuando aparece `PROVISIONING_RUN_NOT_ACTIVE`.

Esto distingue los dos sub‑orígenes del Fallo #1:
**(a)** déficit real de `modulo_menu` en BD limpia (defecto de acoplamiento), vs.
**(b)** estado sucio de runs previos (S6 saltado por marker sin filas).

---

## 1. `FK_permiso_menu`

### Opción 1A — Verificar `modulo_menu` en S6 (fail‑fast)
Añadir `("modulo_menu", N)` a `catalog_profiles._row_expectations_for_plan` para
que un déficit falle en S6 con diagnóstico claro, en vez de reventar en S7.
- **Pro:** convierte un FK opaco en un error de catálogo explícito y temprano.
- **Contra:** requiere fijar el mínimo `N`; no arregla el origen del déficit.
- **Toca:** `catalog_profiles.py` (código previo a F17).

### Opción 1B — Auditar acoplamiento catálogo↔bundle
Comparar los `menu_id` que usan `owner_sync` / `base_operative` /
`manager_standard` / `user_standard` contra los sembrados por `S010`/`S020`.
- **Pro:** encuentra la fuente exacta del déficit (menús faltantes/renombrados).
- **Contra:** análisis de datos; puede derivar en corrección de catálogo o bundle.
- **Toca:** solo lectura para auditar; corrección posterior en catálogo o bundle.

### Opción 1C — Higiene de estado (si el origen es (b) estado sucio)
Recrear el cliente Dedicated desde cero (BD nueva + run nuevo) evitando reusar
runs/markers de intentos fallidos de la ventana F17E.
- **Pro:** elimina falsos negativos por markers de S6 sin filas.
- **Contra:** no corrige un defecto real de acoplamiento si existiera (a).
- **Toca:** operación, no código.

---

## 2. "run no está en provisioning" (`PROVISIONING_RUN_NOT_ACTIVE`)

### Opción 2A — Limpiar/compensar runs no‑terminales heredados de F17E
Identificar runs dejados en estado inconsistente durante la ventana F17E y
llevarlos a un estado terminal antes de reintentar (usar la vía de compensación
existente).
- **Pro:** elimina la fuente de cascada por redispatch de runs viejos.
- **Contra:** requiere inventariar runs afectados.
- **Toca:** operación / servicio de compensación existente.

### Opción 2B — Endurecer la reconciliación del bootstrap (defensivo)
Que `_reconcile_bootstrap_failure` tolere `bootstrap_applied` ausente para no
saltarse `_fail_step_and_run` (`orchestrator:504` vs `:512`), de modo que un fallo
temprano deje el run en `FAILED` limpio y reintetable.
- **Pro:** evita runs "colgados" en `PROVISIONING`; hace idempotente el retry.
- **Contra:** cambia manejo de errores del orquestador (código previo a F17);
  fuera del alcance de F17G y debe evaluarse aparte.
- **Toca:** `dedicated_provisioning_orchestrator.py` / `bootstrap_applied_reader.py`.

### Opción 2C — No hacer nada en 2 hasta resolver 1
Dado que el guard es **secundario** al fallo primario de S7, resolver `FK_permiso_menu`
(sección 1) puede eliminar la cascada por completo.
- **Pro:** mínimo cambio; ataca la causa aguas arriba.
- **Contra:** persistiría el riesgo de cascada por concurrencia/redispatch bajo
  otros fallos futuros.

---

## 3. Secuencia recomendada (no vinculante)

1. **§0** capturar evidencia de runtime (COUNT `modulo_menu`, `menu_id`, estado del run).
2. Según (a)/(b): **1B** (acoplamiento) o **1C** (estado). Considerar **1A** como
   red de seguridad de diagnóstico.
3. **2A** para higienizar runs heredados; evaluar **2B** como endurecimiento
   posterior e independiente.

---

## 4. Qué NO tocar

- **No** revertir F17F: el checksum realineado es correcto y es lo que permite que
  Dedicated pase S4.
- **No** modificar el Motor de Generación de Códigos ni `cfg_codigo_secuencia`:
  son ortogonales a `FK_permiso_menu`.
- Cualquier cambio en RBAC/catálogos/orquestador/state service excede F17G y
  requeriría una fase de implementación explícita con su propia validación.
