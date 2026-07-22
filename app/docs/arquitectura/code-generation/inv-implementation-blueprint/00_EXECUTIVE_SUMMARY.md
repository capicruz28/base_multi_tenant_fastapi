# INV Implementation Blueprint — Resumen ejecutivo

**Versión:** 1.0  
**Fecha:** 2026-07-16  
**Estado:** **OFICIAL** — guía definitiva de implementación INV Ola 1  
**Golden Reference:** ORG (Baseline V1)  
**Piloto:** `inv_categoria_producto` (Categoría de Producto)

---

## 1. Declaración

Este Blueprint traduce el patrón certificado de ORG en un plan **mecánico y repetible** para INV.

| Congelado (no tocar) | Adoptar sin rediseño |
|----------------------|----------------------|
| Motor (`app/core/codigo`) | Adapter `InvCodigoGenerationService` |
| Gateway | UoW CREATE (allocate + insert) |
| SequenceCatalog | Schemas Create optional / Update sin código |
| BR-IMM / Baseline V1 | Tests espejo ORG |
| ORG como Golden Reference | Queries dual-path + `get_*_by_codigo` |

**Principio rector:** *copiar el patrón ORG; cambiar solo nombres de entidad, `sequence_key` y campo código.*

---

## 2. Veredicto

| Pregunta | Respuesta |
|----------|-----------|
| ¿La implementación puede ser mecánica? | **Sí** — tras este Blueprint |
| ¿Se reutiliza el Motor? | **Sí** — vía Gateway, sin modificarlo |
| ¿Primera entidad? | **Categoría** (`inv_categoria_producto`) |
| ¿Qué cambia vs ORG cargo? | Nombres, key, audit INV, queries dual-path (gap AS-IS) |
| ¿Cuándo está INV certificado? | DoD Baseline V1 + 7 entidades + gens timestamp eliminados |

---

## 3. Índice del paquete

| # | Documento | Contenido |
|---|-----------|-----------|
| 00 | Este archivo | Resumen y veredicto |
| 01 | [`01_ORG_VS_INV_COMPARISON.md`](01_ORG_VS_INV_COMPARISON.md) | Comparación ORG vs Categoría + archivos equivalentes |
| 02 | [`02_ADAPTER_AND_FLOWS.md`](02_ADAPTER_AND_FLOWS.md) | Adapter, CREATE, UPDATE, OpenAPI |
| 03 | [`03_IMPLEMENTATION_SEQUENCE.md`](03_IMPLEMENTATION_SEQUENCE.md) | Orden de 7 entidades, tests, riesgos |
| 04 | [`04_READY_AND_CERTIFICATION.md`](04_READY_AND_CERTIFICATION.md) | Checklist pre-código, DoR, certificación |

---

## 4. Referencias obligatorias

- `code-generation/baseline-v1/` — Baseline V1  
- `code-generation/inv-wave1-audit/` — Alcance y matriz Motor  
- ORG: `org_codigo_generation_service.py`, `cargo_service.py` (patrón EMPRESA canónico)  
- Tests: `test_org_cargo_motor_integration.py`, `test_org_br_imm_update_immutability.py`

---

*Sin implementación en esta fase. Código solo tras checklist §04.*
