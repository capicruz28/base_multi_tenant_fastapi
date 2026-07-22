# INV Ola 1 — Certificación de Categoría como Golden Reference

**Fase:** Auditoría arquitectónica independiente — **solo lectura, sin modificar código**
**Fecha:** 2026-07-17
**Entidad auditada:** `inv_categoria_producto` (Categoría de Producto)
**Referencia Golden:** ORG `org_cargo` · **Backend Code Generation Baseline V1**
**Motor:** `app/core/codigo` (congelado)

---

## 1. Propósito

Verificar, de forma **independiente de la implementación**, que la integración del Motor de
Códigos en Categoría (Fase A) es una **copia fiel** del patrón certificado de ORG Cargo y que
cumple **completamente** el Backend Code Generation Baseline V1, de modo que Categoría pueda
declararse **Golden Reference del módulo INV** y usarse como plantilla para Unidad de Medida y
las demás entidades de la ola.

---

## 2. Veredicto

### **B) Categoría requiere correcciones antes de continuar con Unidad de Medida.**

La implementación del **código productivo** es una **copia fiel y conforme** al patrón ORG y a
Baseline V1: adapter delgado, UoW dual-path, uso correcto del Gateway, `GenerationContext`,
BR-IMM en Update, contrato de schemas y mapeo de excepciones. **No** se modificó Motor, Gateway,
SequenceCatalog ni ORG.

Sin embargo, la certificación como Golden Reference **no puede otorgarse todavía** por un motivo
objetivo y acotado: **existen pruebas preexistentes específicas de Categoría que quedaron rojas
como consecuencia directa del cambio a UoW**, y una plantilla Golden debe tener su suite de
entidad **completamente verde**. Propagar Categoría como plantilla sin reconciliar esas pruebas
propagaría el mismo defecto de test a las 6 entidades restantes.

| Bloqueante | Descripción | Severidad |
|------------|-------------|-----------|
| **C-01** | `test_inv_audit_usuario.py::test_a10_create_categoria_servicio_persiste_usuario_creacion_id` falla: el mock no contempla `get_connection_for_tenant` + Gateway (abre sesión real). | Alta (gate) |
| **C-02** | `test_inv_audit_usuario.py::test_a17_create_categoria_servicio_sin_usuario_id_deja_usuario_creacion_none` falla por la misma causa. | Alta (gate) |

Ambos son de **corrección mecánica y acotada** (alinear los mocks al patrón UoW, tal como se hizo
en la suite de auditoría ORG). No hay defecto en el código productivo de Categoría.

---

## 3. Resumen de cumplimiento (los 23 puntos requeridos)

| # | Área | Resultado |
|---|------|-----------|
| 1 | Arquitectura general | ✅ Conforme |
| 2 | `InvCodigoGenerationService` | ✅ Copia fiel |
| 3 | Queries dual-path | ✅ Conforme |
| 4 | Unit of Work | ✅ Conforme (un solo `session.begin()`) |
| 5 | Session handling | ✅ Conforme |
| 6 | `GenerationContext` | ✅ Uso correcto vía adapter |
| 7 | Uso del Gateway | ✅ Único punto de entrada (`allocate`) |
| 8 | BR-IMM | ✅ Conforme (schema + service) |
| 9 | Schemas Create/Update/Read | ✅ Conforme al contrato |
| 10 | OpenAPI vivo esperado | ✅ Conforme; snapshot **no** regenerado (por instrucción) |
| 11 | Manejo de excepciones | ✅ Conforme (⚠ PUT no captura `CustomException`, ver 01) |
| 12 | Dedicated DB | ✅ Compatible (dual-path) |
| 13 | Shared DB | ✅ Compatible (dual-path) |
| 14 | Baseline V1 | ✅ Conforme |
| 15 | vs ORG Cargo | ✅ Fiel (3 desviaciones justificadas, ver 02) |
| 16 | vs Blueprint | ✅ Conforme |
| 17 | vs Plan Técnico | ✅ Conforme (orden Fase 1→6) |
| 18 | Calidad de pruebas | ⚠ 24 nuevas verdes; 2 preexistentes rojas (C-01/C-02) |
| 19 | Riesgos arquitectónicos | ✅ Bajos (ver 01 §Riesgos) |
| 20 | Deuda técnica | ⚠ Menor (logging/observabilidad, post-assert) |
| 21 | Oportunidades de simplificación | ℹ Identificadas (ver 01) |
| 22 | Desviaciones vs ORG | ⚠ 3, todas justificadas o menores |
| 23 | Congelados no modificados | ✅ Verificado (Motor/Gateway/Catalog/ORG) |

---

## 4. Condición de cierre

Categoría quedará **certificada como Golden Reference INV** en cuanto se reconcilien **C-01** y
**C-02** y la suite específica de Categoría quede 100% verde. La corrección está fuera del
alcance de esta auditoría (instrucción explícita: *no corregir nada todavía*).

---

## 5. Documentos de esta certificación

| Doc | Contenido |
|-----|-----------|
| `00_EXECUTIVE_SUMMARY.md` | Este documento — veredicto y resumen |
| `01_IMPLEMENTATION_AUDIT.md` | Auditoría técnica punto por punto (1–23) |
| `02_PATTERN_COMPARISON.md` | Comparación línea a línea vs ORG Cargo / Blueprint / Plan |
| `03_TEST_AUDIT.md` | Auditoría de pruebas y cobertura |
| `04_CERTIFICATION_REPORT.md` | Dictamen formal y checklist de gate |
