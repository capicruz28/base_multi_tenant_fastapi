# Estrategia de implementación — Inmutabilidad del código

**Fecha:** 2026-07-13  
**Prerequisito:** Aprobación de [`01_ARCHITECTURAL_DECISION.md`](01_ARCHITECTURAL_DECISION.md)  
**Esta fase de auditoría:** **no implementa**

---

## 1. Principios de la implementación futura

1. **Core Motor congelado** salvo docs: no añadir `UPDATE` a `GenerationOperation`.
2. **Enforcement en frontera ERP** (schemas + services), no en Gateway.
3. **ORG primero** (5 entidades), plantilla para INV.
4. **Docs + contrato FE** en el mismo PR de comportamiento o PR documental inmediato anterior.
5. **Sin cambio de BD / V010**.

---

## 2. Plan por fases

### Fase 0 — Aprobación (actual)

| Entregable | Dueño |
|------------|-------|
| ADR + impacto aprobados | Arquitectura / Producto |
| Congelar alcance: solo campos SequenceCatalog | Arquitectura |

**Gate:** “Go” escrito. Sin código.

### Fase 1 — Normativa documental

| Trabajo | Archivos |
|---------|----------|
| Registrar BR-IMM-01..05 | `07_BUSINESS_RULES.md` |
| Actualizar políticas edición | `08_CODE_POLICIES.md`, `09`, `10`, `12`, catalog `18` |
| Actualizar contrato FE wave1 | `codigo-generation-wave1/frontend-contract/*` |
| Marcar BR-M-31 deprecated | `07` |

**Gate:** Docs consistentes; sin runtime change aún (opcional PR docs-only).

### Fase 2 — ORG enforcement (runtime)

Orden recomendado por archivo (schemas → services → tests):

| Paso | Artefacto |
|------|-----------|
| 2.1 | Quitar `codigo` / `codigo_empresa` de `*Update` schemas |
| 2.2 | Eliminar ramas dup-check código en `update_*_servicio` |
| 2.3 | (Opcional defensa) helper `reject_code_mutation(payload, field)` |
| 2.4 | Tests: UPDATE con código → inmutable / strip / 422 |
| 2.5 | Regresión CREATE motor (suite Ola 1) |

**Entidades:** empresa → cargo → sucursal → departamento → centro_costo (orden indiferente; paralelo OK).

**Gate:** Tests verdes; CREATE invariable.

### Fase 3 — Comunicación Frontend

| Trabajo | Detalle |
|---------|---------|
| Regenerar tipos OpenAPI | Campo ausente en Update |
| Forms UPDATE | Input código `readOnly` / disabled |
| Omitir clave en PUT | No enviar código |
| Mensaje UX | Tooltip BR-IMM |

**Gate:** Staging FE+BE juntos.

### Fase 4 — INV plantilla (pre Ola 1 INV)

| Trabajo | Detalle |
|---------|---------|
| ADR reference en plan INV | Producto `codigo_sku` inmutable en Update |
| No migrar INV motor aún | Solo no introducir anti-patrón |

### Fase 5 — Hardening (opcional)

| Trabajo | Detalle |
|---------|---------|
| Query whitelist | `update_*` no acepta columna código aunque venga en dict |
| Audit log | Intento de mutación |
| Strict 422 | Si se usó strip en Fase 2 |

---

## 3. Orden recomendado (checklist implementación)

```text
[ ] Aprobación ADR
[ ] Docs BR-IMM (Fase 1)
[ ] Schemas Update ORG ×5
[ ] Services Update ORG ×5
[ ] Tests inmutabilidad ×5 + regresión CREATE
[ ] Actualizar frontend-contract
[ ] FE Update (coordenado)
[ ] Gate INV: plantilla inmutabilidad
```

---

## 4. Riesgos de implementación

| ID | Riesgo | Mitigación |
|----|--------|------------|
| RI-01 | FE PUT full-object incluye código → strip silencioso confunde | UI readOnly + doc |
| RI-02 | Olvidar una entidad ORG | Checklist ×5 + test parametrizado |
| RI-03 | Tocar `app/core/codigo` innecesariamente | Code review: diff core vacío |
| RI-04 | Mezclar con Ola INV en el mismo PR | PRs separados |
| RI-05 | 409 vs 422 inconsistente | Usar 422 CODE_IMMUTABLE |

---

## 5. Rollback

| Escenario | Acción |
|-----------|--------|
| FE no listo | Revert PR BE schemas/services; restaurar campos Update |
| Solo docs | Revert docs; ADR queda “propuesto” |
| Post-prod incidente | Hotfix: reintroducir campo Update **solo** con flag feature `ORG_ALLOW_CODE_UPDATE=false` default |

**Rollback BD:** no aplica.

**Datos:** no hay migración que revertir.

---

## 6. Estimación relativa

| Fase | Esfuerzo relativo |
|------|-------------------|
| Docs | S |
| ORG schemas+services+tests | M (repetitivo) |
| FE Update | S–M |
| INV plantilla | S |

---

## 7. Fuera de alcance de la implementación BR-IMM

- Módulo admin cfg (`/cfg/secuencias`)
- Align / Preview
- Soft-delete políticas
- Cambio de RUC / códigos EXTERNAL
- Re-maestro tool (BR-M-33) — backlog separado

---

*Tests: [`06_TESTING_STRATEGY.md`](06_TESTING_STRATEGY.md)*
