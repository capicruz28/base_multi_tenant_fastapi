# F17E — Opciones de remediación (SIN IMPLEMENTAR — requiere aprobación)

**Fase:** F17E (READ-ONLY). **Fecha:** 2026-07-03.
**Estado:** este documento **no** aplica ningún cambio. No se modificó código, V010, manifest, bootstrap ni onboarding. Enumera opciones y puntos de decisión para una fase posterior (p.ej. F17F) que requerirá **aprobación explícita**.

> Alineado con la instrucción de F17E: *no proponer/asumir soluciones todavía*. Aquí se documentan **candidatos** de remediación con sus compensaciones para que el usuario decida; **ninguno** se ejecuta en esta fase.

---

## 1. Qué debe resolver la remediación

De `34_ROOT_CAUSE_ANALYSIS.md`:

- **P-1 (causa raíz):** el SHA-256 real de `V010` (con la tabla `cfg_codigo_secuencia` remodelada por F17) ya no coincide con el checksum congelado `_V010_ERP_SHA256`.
- **P-2 (orden/observabilidad):** el fallo de integridad ocurre antes de crear `bootstrap_applied`, y la reconciliación lee esa tabla inexistente, enmascarando el error real.
- **P-3 (sistémico):** `V010` cumple doble rol (esquema ERP evolutivo + artefacto de checksum congelado); toda evolución de esquema ERP romperá el manifiesto Dedicated si no hay proceso de recálculo.

Una solución completa debería atender **P-1** (desbloquea el onboarding) y, deseablemente, **P-2** y **P-3** (evita reincidencia y mejora el diagnóstico).

---

## 2. Opciones para P-1 (checksum divergente)

| Opción | Descripción | Pros | Contras / Riesgos |
|--------|-------------|------|-------------------|
| **A — Recalcular el checksum congelado** | Recalcular `SHA-256(V010 actual)` y actualizar `_V010_ERP_SHA256` (y validar con el test de manifiesto). | Mínimo cambio; restaura el invariante manifiesto↔archivo; alineado con el mecanismo existente. | Debe hacerse cada vez que V010 cambie; requiere disciplina/proceso (P-3). Congela el estado **actual** de V010, incluyendo cambios aún sin commitear. |
| **B — Commitear V010 y regenerar checksum en el mismo cambio** | Incluir la edición de V010 y el recálculo del checksum como una unidad atómica revisable. | Mantiene coherencia repo↔manifiesto; deja trazabilidad en un solo commit. | Igual que A respecto a P-3; exige que la edición de V010 esté finalizada. |
| **C — Derivar el checksum en runtime desde una fuente confiable** | Reemplazar el valor congelado por un checksum calculado/publicado por el pipeline de build. | Elimina el drift manual. | Cambio de diseño del manifiesto; contradice la política "checksum congelado" (F4-05b); mayor alcance. |

> **P-1 es la única imprescindible para desbloquear** el onboarding Dedicated. A/B son de bajo alcance; C es un rediseño.

---

## 3. Opciones para P-2 (orden / enmascaramiento)

| Opción | Descripción | Pros | Contras |
|--------|-------------|------|---------|
| **D — Reconciliar solo si la tabla existe** | En `_reconcile_bootstrap_failure`, comprobar existencia de `bootstrap_applied` antes de leerla (o capturar el error de objeto inexistente) y, si no existe, propagar el error original. | El operador vería el error real (checksum) en lugar del síntoma. | Cambia lógica del orquestador; requiere pruebas. |
| **E — Crear `bootstrap_applied` antes de validar** | Invertir el orden: `_ensure_bootstrap_applied_table` antes de `validate_manifest_integrity`. | La reconciliación por markers funcionaría siempre. | Crea la tabla aun cuando el esquema no se aplicará; puede dejar BD a medias; discutible semánticamente. |
| **F — No tocar el orden; mejorar el log** | Dejar el pipeline igual y asegurar que el error de checksum se registre/propague sin ser reemplazado. | Cambio mínimo; preserva invariantes. | No elimina el síntoma en primera instancia, solo mejora diagnóstico. |

> P-2 es **calidad/observabilidad**, no bloqueante. Recomendable abordarla junto a P-1 para evitar futuros diagnósticos engañosos, pero es decisión del usuario.

---

## 4. Opciones para P-3 (doble rol de V010)

| Opción | Descripción | Pros | Contras |
|--------|-------------|------|---------|
| **G — Guardia de CI que recalcula/verifica checksums** | Test/hook que falle el build si `SHA-256(V010) ≠ _V010_ERP_SHA256`. | Convierte el drift en error temprano, no en fallo de onboarding en producción. | Requiere que el equipo actualice el congelado deliberadamente en cada cambio de esquema. |
| **H — Separar "esquema ERP" de "artefacto bootstrap"** | Versionar el DDL Dedicated de forma independiente del V010 ERP monolítico. | Elimina el acoplamiento de fondo. | Alcance grande; cambia la arquitectura de bootstrap. |
| **I — Documentar el procedimiento de recálculo** | Runbook: "al cambiar V010, recalcular y actualizar `_V010_ERP_SHA256`". | Costo casi nulo; formaliza la disciplina. | No previene el error por sí solo (depende de cumplimiento). |

---

## 5. Combinaciones sugeridas (para discusión, no elegidas)

- **Mínima (desbloqueo):** A (o B) — restaura el checksum. Resuelve el incidente.
- **Robusta:** A/B + D + G — desbloquea, deja de enmascarar el error y previene reincidencia en CI.
- **Estratégica:** además H — desacopla esquema ERP de artefacto bootstrap (proyecto aparte).

**No se recomienda** una opción concreta en esta fase: la elección depende de la política de gobernanza de `bootstrap_v2` y del apetito de alcance del usuario.

---

## 6. Puntos de decisión para el usuario

1. ¿La edición de `V010` (remodelación de `cfg_codigo_secuencia` del Motor) está **finalizada** y debe **commitearse** antes de recalcular el checksum? (afecta A vs B)
2. ¿Se desea además corregir el **enmascaramiento** del error (P-2), o basta con desbloquear (P-1)?
3. ¿Se añadirá una **guardia de CI** (P-3) para que futuros cambios de esquema no rompan el onboarding en producción?
4. ¿Debe abrirse una fase separada para el **desacople** de V010 (opción H), o queda fuera de alcance?

---

## 7. Restricciones respetadas en F17E

- No se modificó código, V010, bootstrap, manifests ni onboarding.
- No se crearon tablas ni migraciones.
- No se eligió ni implementó ninguna solución.
- Solo se generó documentación (33–36).

---

*Evidencia en `33_DEDICATED_REGRESSION_AUDIT.md`. Causa raíz en `34_ROOT_CAUSE_ANALYSIS.md`. Flujo en `35_FLOW_COMPARISON_BEFORE_AFTER.md`.*
