# 04 — Dictamen de certificación (Categoría / INV Golden Reference)

**Fecha:** 2026-07-17
**Auditoría:** independiente, solo lectura
**Base normativa:** ORG Cargo (Golden Reference) · Backend Code Generation Baseline V1 · Blueprint INV · Plan Técnico Fase A

---

## 1. Dictamen

### **B) Categoría requiere correcciones antes de continuar con Unidad de Medida.**

El **código productivo** de Categoría es una **copia fiel** del patrón ORG Cargo y **cumple
completamente** el Baseline V1. El bloqueo para la certificación como Golden Reference es
**exclusivamente** el estado no-verde de la suite de pruebas específica de la entidad
(`C-01`/`C-02`), condición indispensable para que Categoría sirva de plantilla replicable.

---

## 2. Checklist de gate Golden Reference

| Criterio | Requerido | Estado |
|----------|-----------|--------|
| Adapter delgado propio (`InvCodigoGenerationService`) | Sí | ✅ |
| Uso exclusivo del Gateway (`allocate`) | Sí | ✅ |
| `GenerationContext` correcto | Sí | ✅ |
| Queries dual-path + `get_by_codigo` | Sí | ✅ |
| CREATE en UoW única (`session.begin()`) | Sí | ✅ |
| Pre-check UNIQUE manual → `ConflictError` | Sí | ✅ |
| BR-IMM en schema Update | Sí | ✅ |
| BR-IMM en service Update (sin lógica de código) | Sí | ✅ |
| Contrato schemas Create/Update/Read | Sí | ✅ |
| Mapeo de excepciones de dominio en POST | Sí | ✅ |
| Compatibilidad Dedicated + Shared | Sí | ✅ |
| Motor / Gateway / SequenceCatalog / ORG intactos | Sí | ✅ |
| OpenAPI snapshot no regenerado (por instrucción) | Sí | ✅ |
| Alcance limitado a Categoría | Sí | ✅ |
| Pruebas nuevas verdes | Sí | ✅ (24/24) |
| **Suite específica de la entidad 100% verde** | **Sí** | ❌ **C-01/C-02** |

**15/16 criterios cumplidos.** El único criterio fallido es el gate de suite verde.

---

## 3. Acciones requeridas para pasar a A) (fuera de esta auditoría)

| # | Acción | Archivo | Tipo |
|---|--------|---------|------|
| 1 | Alinear mock de `test_a10` al flujo UoW (parchear `get_connection_for_tenant` + `InvCodigoGenerationService.resolve_codigo_for_create`) | `tests/unit/test_inv_audit_usuario.py` | Test |
| 2 | Alinear mock de `test_a17` idéntico | `tests/unit/test_inv_audit_usuario.py` | Test |
| 3 | (Recomendado, no bloqueante) PUT/detalle/delete: capturar `(NotFoundError, CustomException)` para simetría ORG (D-3) | `endpoints_categorias.py` | Código |
| 4 | (Opcional) Añadir `assert_row_empresa` post-CREATE (D-2) y/o logging de scope (D-2b) | `categoria_service.py` | Código |

> Acciones 1–2 son **obligatorias** para el gate. 3–4 son mejoras de paridad, no bloqueantes.

---

## 4. Evidencia de no modificación de componentes congelados

| Componente | Evidencia |
|------------|-----------|
| **Motor** (`app/core/codigo/`) | `git diff --name-only -- app/core/codigo/` ⇒ vacío |
| **Gateway** | `codigo_generacion_gateway.py` sin cambios; INV solo llama `allocate` |
| **SequenceCatalog** | `sequence_catalog.py:119` ya contenía `inv_categoria_producto` (CAT, AUTO_DEFAULT, EMPRESA) antes de Fase A |
| **ORG** | Ningún archivo `app/modules/org/**` escrito en Fase A |
| **OpenAPI snapshot** | No regenerado en esta fase |

---

## 5. Riesgos residuales al momento del dictamen

| ID | Riesgo | Sev. | Mitigación |
|----|--------|------|-----------|
| R-1 | C-01/C-02 rojos | Alta | Acciones 1–2 |
| R-2 | D-3 (PUT sin `CustomException`) | Baja | Acción 3 |
| R-5 | Entorno local sin columna `generation_policy` | Media | Provisionar cfg en entorno de test/integración |
| R-4 | Snapshot OpenAPI desalineado | Baja | Regeneración diferida (tarea dedicada) |

---

## 6. Conclusión

Categoría está **arquitectónicamente lista** y es fiel al Golden Reference ORG, pero **no queda
certificada** en este dictamen por el gate de suite verde. Tras ejecutar las acciones 1–2 (y
verificar la suite específica de Categoría 100% verde), Categoría podrá **re-someterse** y
obtener el dictamen **A) Golden Reference INV**, habilitando su uso como plantilla para Unidad de
Medida y el resto de la ola.

**No avanzar a Unidad de Medida hasta obtener el dictamen A).**
