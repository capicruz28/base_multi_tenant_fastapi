# Informe de cierre — Fase 1 normativa BR-IMM

**Fecha:** 2026-07-13  
**Tipo:** Aprobación oficial de arquitectura (solo documentación)  
**Resultado:** **APROBADO** — decisión de inmutabilidad del código **cerrada**  
**Siguiente fase:** Implementación runtime (schemas Update + services) — **aún no iniciada**

---

## 1. Declaración oficial

La decisión arquitectónica:

> El código funcional de cualquier entidad administrada por el Motor de Códigos es **INMUTABLE** después de la creación del registro.

queda **oficialmente aprobada** como regla del Motor de Códigos bajo los IDs:

| ID | Enunciado |
|----|-----------|
| **BR-IMM-01** | Código inmutable desde CREATE |
| **BR-IMM-02** | `generation_policy` solo CREATE / IMPORT |
| **BR-IMM-03** | UPDATE nunca modifica el código |
| **BR-IMM-04** | UPDATE nunca invoca el Motor |
| **BR-IMM-05** | Re-maestro / migración = único escape excepcional |

Registro canónico: [`../07_BUSINESS_RULES.md`](../07_BUSINESS_RULES.md) §3.4  
ADR: [`01_ARCHITECTURAL_DECISION.md`](01_ARCHITECTURAL_DECISION.md) — estado **APROBADO**

---

## 2. Relación con reglas legacy

| Regla | Estado oficial |
|-------|----------------|
| **BR-M-30** | **SUPERSEDED** por BR-IMM-01 |
| **BR-M-31** | **DEPRECATED** |
| **BR-M-32** | **SUPERSEDED** por BR-IMM-01 |
| **BR-M-33** | **VIGENTE** (aclarada; alineada a BR-IMM-05) |

**BR-IMM es la única fuente oficial** sobre inmutabilidad del código del Motor. Referencias a “editable sin referencias” o “inmutable tras uso” se consideran obsoletas.

---

## 3. Documentos actualizados en esta Fase 1

### Normativa Motor (`code-generation/`)

| Documento | Cambio |
|-----------|--------|
| `07_BUSINESS_RULES.md` | §3.4 BR-IMM-01…05; BR-M-31 DEPRECATED; jerarquía + referencias |
| `08_CODE_POLICIES.md` | Edición AUTO_* / permisos; quitar “cambiar sin referencias” |
| `09_ERP_BEST_PRACTICES.md` | Benchmark post-CREATE + BR-IMM |
| `10_FINAL_RECOMMENDATION.md` | STD-E-* → BR-IMM; FAQ; versión 1.1 |
| `12_GATEWAY_DESIGN.md` | Update fuera del Gateway; BR-IMM en servicio ERP |
| `catalog/18_SEQUENCE_DEFINITION_MODEL.md` | `editable_*=false`; SC-DEF-05 rev. |
| `bootstrap/02_PREFIX_STANDARD.md` | PFX-09 → BR-IMM-01 |
| `code-immutability/00` + `01` | Estado **APROBADO** |

### Cross-refs Wave1 / Frontend

| Documento | Cambio |
|-----------|--------|
| `codigo-generation-wave1/04_FUNCTIONAL_CONTRACT.md` | UPDATE inmutable BR-IMM |
| `frontend-contract/00` · `01` · `02` · `03` · `04` | Contrato objetivo alineado a BR-IMM; gap runtime documentado |

### Este informe

| Documento | Rol |
|-----------|-----|
| `07_NORMATIVE_APPROVAL.md` | Cierre Fase 1 |

---

## 4. Qué NO se modificó (garantía Fase 1)

| Ámbito | Estado |
|--------|--------|
| Código Python / servicios | **Sin cambios** |
| Schemas Pydantic | **Sin cambios** |
| OpenAPI generado | **Sin cambios** |
| `app/core/codigo/**` | **Sin cambios** |
| Base de datos / V010 | **Sin cambios** |
| Frontend React | **Sin cambios** |
| Pull Requests | **No generados** |

El runtime AS-IS **aún permite** mutar código en UPDATE ORG. Eso es el **gap documentado** a cerrar en Fase 2 — no invalida la norma.

---

## 5. Gate de readiness para Fase 2 (runtime)

| Criterio | Estado |
|----------|--------|
| ADR aprobado | ✅ |
| BR-IMM en `07_BUSINESS_RULES.md` | ✅ |
| BR-M-31 DEPRECATED | ✅ |
| Políticas / recomendación / gateway / catálogo | ✅ |
| Contrato FE actualizado (objetivo) | ✅ |
| Schemas Update sin campo código | ⏸ Fase 2 |
| Services Update sin rama código | ⏸ Fase 2 |
| Tests IMM-* | ⏸ Fase 2 |

---

## 6. Orden recomendado de Fase 2 (recordatorio)

1. Schemas `*Update` ORG ×5 — quitar `codigo` / `codigo_empresa`  
2. Services `update_*` — eliminar mutación + UNIQUE de código  
3. Tests IMM + regresión CREATE  
4. Regenerar OpenAPI / alinear FE PUT  
5. Plantilla INV nace con BR-IMM  

Detalle: [`04_IMPLEMENTATION_STRATEGY.md`](04_IMPLEMENTATION_STRATEGY.md)

---

## 7. Veredicto final

| Pregunta | Respuesta |
|----------|-----------|
| ¿La arquitectura de inmutabilidad está oficialmente aprobada? | **Sí** |
| ¿Se puede iniciar la implementación runtime? | **Sí** |
| ¿Se puede iniciar Ola 1 INV sin BR-IMM en Update? | **No recomendado** — plantilla INV debe nacer inmutable |
| ¿Hay riesgo de reabrir la decisión? | Solo con nuevo ADR |

---

*Fase 1 normativa — cerrada. Sin modificación funcional. Listo para Fase 2 runtime bajo aprobación operativa.*
