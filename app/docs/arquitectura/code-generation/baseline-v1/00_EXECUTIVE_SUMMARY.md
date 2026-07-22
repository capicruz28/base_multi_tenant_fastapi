# Backend Code Generation Baseline V1 — Resumen ejecutivo

**Versión:** 1.0  
**Fecha:** 2026-07-14  
**Estado:** **OFICIAL — CONGELADO**  
**Golden Reference Backend:** módulo **ORG** (Ola 1 cerrada)  
**Autoridad:** Este paquete es la referencia obligatoria para todo módulo ERP futuro que consuma el Motor de Códigos

---

## 1. Declaración oficial

A partir de esta fecha, la arquitectura de consumo del Motor de Códigos en Backend queda **congelada** sobre el patrón implementado y certificado en **ORG Ola 1**.

Quedan cerrados y aprobados en ORG:

| Área | Estado |
|------|--------|
| Motor de Códigos (`app/core/codigo`) | Congelado |
| Gateway | Congelado |
| Policies / SequenceCatalog | Congelados |
| CREATE vía Motor | Certificado |
| BR-IMM (UPDATE inmutable) | Normativa + runtime certificado |
| OpenAPI vivo + `openapi_snapshot.json` | Alineados |
| Tests CREATE + BR-IMM | Verdes |
| Documentación normativa (BR-IMM, F15A) | Oficial |

**ORG es la Golden Reference Backend.** Ningún módulo futuro (INV, LOG, COM, POS, …) podrá rediseñar el Motor ni introducir un patrón distinto de consumo sin un ADR que **expresamente** superseda este Baseline.

---

## 2. Veredicto final

| Pregunta | Respuesta |
|----------|-----------|
| ¿ORG queda oficialmente congelado como Golden Reference? | **Sí** |
| ¿Se permiten más cambios de arquitectura sobre ORG por el Motor? | **No** (salvo defectos críticos de producción con ADR) |
| ¿INV debe implementar usando este Baseline? | **Sí — sin rediseñar el Motor** |
| ¿El Motor / Gateway se reabre para INV? | **No** |

---

## 3. Confirmación explícita para INV

> **INV deberá implementarse utilizando exclusivamente este Backend Code Generation Baseline V1.**  
> **Queda prohibido rediseñar el Motor de Códigos, el Gateway, SequenceCatalog o las reglas BR-IMM.**  
> INV solo adapta el patrón ORG (adapter de módulo + schemas + services + UoW) a sus entidades.

---

## 4. Índice del paquete

| # | Documento | Contenido |
|---|-----------|-----------|
| 00 | Este archivo | Resumen, veredicto, congelación ORG |
| 01 | [`01_ARCHITECTURAL_PRINCIPLES.md`](01_ARCHITECTURAL_PRINCIPLES.md) | Principios obligatorios |
| 02 | [`02_CREATE_AND_UPDATE.md`](02_CREATE_AND_UPDATE.md) | Flujo CREATE + BR-IMM UPDATE |
| 03 | [`03_LAYER_RESPONSIBILITIES.md`](03_LAYER_RESPONSIBILITIES.md) | Capas: qué hace / qué no |
| 04 | [`04_CHECKLISTS.md`](04_CHECKLISTS.md) | Checklist módulo genérico + INV |
| 05 | [`05_RULES_AND_PROHIBITIONS.md`](05_RULES_AND_PROHIBITIONS.md) | Reglas inviolables + patrones prohibidos |
| 06 | [`06_DEFINITION_OF_DONE.md`](06_DEFINITION_OF_DONE.md) | Criterios de certificación de módulo |

---

## 5. Referencias normativas (no reemplazadas)

Este Baseline **consolida** el patrón operativo; la norma de negocio permanece en:

- `code-generation/07_BUSINESS_RULES.md` (BR-IMM-01…05)
- `code-generation/08_CODE_POLICIES.md`
- `code-generation/code-immutability/`
- `codigo-generation-wave1/frontend-contract/` (contrato FE ORG)

---

*Baseline V1 — sin implementación adicional. INV parte de aquí.*
