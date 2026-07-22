# INV Wave 1 — Auditoría arquitectónica Motor de Códigos

**Fecha:** 2026-07-14  
**Tipo:** Auditoría de diseño — **sin implementación**  
**Prerequisito:** Backend Code Generation Baseline V1 · ORG Golden Reference  
**Estado:** Listo para aprobación de alcance Ola 1 INV  
**Prohibido en esta fase:** modificar Motor, Gateway, SequenceCatalog, código INV, OpenAPI

---

## 1. Veredicto final

| Pregunta | Respuesta |
|----------|-----------|
| ¿INV puede adoptar Baseline V1 sin rediseñar el Motor? | **Sí** |
| ¿El catálogo ya define las keys INV? | **Sí** — 5 maestros F1 + 2 documentos F2 |
| ¿Alcance recomendado Ola 1 INV? | **Primero 5 maestros F1**; documentos F2 en **Ola 1B** inmediata o misma ola por fases |
| ¿Hay anti-patrones AS-IS críticos? | **Sí** — correlativos ad hoc por timestamp en estorno/ajuste; Create exige códigos manuales |
| ¿Bloqueadores de Motor/Gateway? | **Ninguno** — solo trabajo de módulo |

**Recomendación:** ejecutar Ola 1 INV como **adopción mecánica del patrón ORG** (adapter + schemas + services + BR-IMM + tests), **sin** tocar `app/core/codigo`.

---

## 2. Documentos del paquete

| # | Archivo | Contenido |
|---|---------|-----------|
| 00 | Este archivo | Veredicto, alcance, índice |
| 01 | [`01_ENTITY_INVENTORY.md`](01_ENTITY_INVENTORY.md) | Inventario completo INV |
| 02 | [`02_MOTOR_MATRIX.md`](02_MOTOR_MATRIX.md) | Matriz sequence_key / scope / policy / campo |
| 03 | [`03_DEPENDENCIES_AND_IMPACT.md`](03_DEPENDENCIES_AND_IMPACT.md) | ORG, CFG, OpenAPI, Frontend |
| 04 | [`04_IMPLEMENTATION_PLAN.md`](04_IMPLEMENTATION_PLAN.md) | Fases, orden, riesgos, DoD |

---

## 3. Alcance propuesto Ola 1 INV (resumen)

### Incluir (Motor)

| Familia | Entidades |
|---------|-----------|
| **F1 Maestros** | categoría, unidad medida, producto (`codigo_sku`), almacén, tipo movimiento |
| **F2 Documentos** (fase B) | movimiento (`numero_movimiento`), inventario físico (`numero_inventario`) + eliminar gen timestamp |

### Excluir del Motor

Stock, kardex, detalles, códigos EXTERNAL/MANUAL auxiliares del producto, campos de workflow, endpoints deprecated de detalle standalone.

---

## 4. Confirmaciones Baseline V1

| Regla Baseline | Aplicación INV |
|----------------|----------------|
| No rediseñar Motor/Gateway/Catalog/BR-IMM | **Obligatorio** |
| CREATE vía Gateway + UoW | Igual ORG |
| UPDATE sin campo código Motor | Igual ORG |
| Adapter delgado tipo `OrgCodigoGenerationService` | Proponer `InvCodigoGenerationService` |

---

*Inventario: [`01_ENTITY_INVENTORY.md`](01_ENTITY_INVENTORY.md)*
