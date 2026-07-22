# Reglas inviolables y patrones prohibidos — Baseline V1

---

## 1. Reglas que ningún módulo podrá romper

| ID | Regla |
|----|-------|
| **R-01** | Solo el Gateway asigna/acepta códigos Motor en CREATE/IMPORT. |
| **R-02** | UPDATE nunca muta el campo código Motor (**BR-IMM-01…04**). |
| **R-03** | No existe `GenerationOperation.UPDATE` ni se inventará para ERP. |
| **R-04** | Allocate + INSERT en la misma unidad de trabajo. |
| **R-05** | Siempre filtrar `cliente_id`; y `empresa_id` cuando la tabla lo tenga. |
| **R-06** | Policies base del catálogo no se “parchean” por módulo en runtime. |
| **R-07** | Duplicado de código → `ConflictError` 409 (no 422). |
| **R-08** | Cross-tenant / cross-empresa → 404, no 403. |
| **R-09** | Documentos AUTO_REQUIRED: el cliente no inventa correlativo. |
| **R-10** | Estorno / compensación: **nuevo** correlativo; no reutilizar el del original. |
| **R-11** | ORG Golden Reference: desviaciones requieren ADR que superseda Baseline V1. |
| **R-12** | Motor/Gateway/SequenceCatalog no se modifican en olas de módulo. |

---

## 2. Patrones prohibidos

| ID | Anti-patrón | Por qué |
|----|-------------|---------|
| **X-01** | Generar correlativo en service con `MAX()+1` | Carreras; bypass Motor |
| **X-02** | Generar código en Frontend y persistir sin Motor | Drift de contador |
| **X-03** | `codigo` en schema `*Update` (entidad Motor) | Viola BR-IMM |
| **X-04** | `get_*_by_codigo` + cambio de código en UPDATE | Legado ORG pre-IMM |
| **X-05** | Llamar Gateway en UPDATE “por si cambió el código” | Prohibido |
| **X-06** | Segundo catálogo / tabla de secuencias por módulo | Fragmentación |
| **X-07** | Concatenar IDs/timestamps como “código de negocio” | No auditable |
| **X-08** | Reiniciar secuencias en flujo operativo normal | Colisiones |
| **X-09** | Mezclar store CFG y serie fiscal | Riesgo legal |
| **X-10** | Tratar preview como reserva de número | BR preview |
| **X-11** | Usar `current_user.cliente_id` platform en queries ERP | Rompe impersonación |
| **X-12** | “Editable sin referencias” (BR-M-31) | **DEPRECATED** — reemplazado por BR-IMM |
| **X-13** | Rediseñar Gateway para INV “porque productos son distintos” | Baseline lo prohíbe |
| **X-14** | Commit del INSERT antes del allocate | Huérfanos / huecos mal gobernados |

---

## 3. Excepciones permitidas (estrechas)

| Caso | Condición |
|------|-----------|
| IMPORT histórico | `GenerationOperation.IMPORT` + rol implantación + align |
| Re-maestro | BR-IMM-05 — proceso fuera de PUT estándar |
| Campos EXTERNAL (RUC, ISO moneda, …) | Fuera Motor secuencial; reglas propias |
| Admin cfg (prefijos) | Módulo CFG futuro; no altera códigos ya emitidos |

Toda excepción nueva = **ADR** + actualización normativa; no “atajo de sprint”.

---

*Definition of Done: [`06_DEFINITION_OF_DONE.md`](06_DEFINITION_OF_DONE.md)*
