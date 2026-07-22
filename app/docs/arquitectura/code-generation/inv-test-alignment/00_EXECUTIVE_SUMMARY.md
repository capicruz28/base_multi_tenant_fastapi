# Alineación de tests C-01 / C-02 — Resumen ejecutivo

**Fase:** Plan técnico — **sin modificar código ni tests**
**Fecha:** 2026-07-17
**Alcance:** únicamente `tests/unit/test_inv_audit_usuario.py` · tests **C-01** (`test_a10`) y **C-02** (`test_a17`)
**Objetivo:** desbloquear dictamen **B → A** (Golden Reference Categoría)
**Prohibido:** Motor, Gateway, SequenceCatalog, ORG, Baseline V1, código productivo INV

---

## 1. Veredicto técnico

### La corrección consiste **únicamente en adaptar los mocks** de C-01 y C-02.

**No existe ningún problema real del código productivo** de Categoría. El fallo es un
**desfase de fixtures** respecto al nuevo flujo CREATE (UoW + Gateway). El service
`create_categoria_servicio` es correcto; los tests A10/A17 aún asumían el CREATE
pre-Motor (sin `get_connection_for_tenant` ni allocate).

| Pregunta | Respuesta |
|----------|-----------|
| ¿Bug en `categoria_service`? | **No** |
| ¿Bug en Gateway / Motor? | **No** |
| ¿Bug en `apply_create_audit`? | **No** |
| ¿Tests inválidos por mocks incompletos? | **Sí** |
| ¿Se necesita cambiar asserts de `usuario_creacion_id`? | **No** — deben permanecer |
| ¿Se necesita ampliar asserts UoW? | **Sí** — mínimamente, para no ocultar regresiones |

---

## 2. Causa raíz en una frase

A10/A17 mockeaban solo `ensure_empresa_in_tenant` + `create_categoria`. Tras Fase A, el
CREATE abre UoW real y llama al adapter/Gateway **antes** del INSERT; al no mockear esa
capa, el test sale del aislamiento unitario, consulta BD y falla.

---

## 3. Alcance aprobado del plan

| Incluido | Excluido |
|----------|----------|
| Helpers locales `_session_context_manager` / `_make_uow_session` | Cualquier `app/modules/**` productivo |
| Ajuste de mocks en `test_a10` y `test_a17` | Tests de producto / movimiento / IF en el mismo archivo |
| Asserts originales de auditoría + asserts UoW mínimos | Regenerar OpenAPI, tocar ORG, Motor |
| Re-ejecución de A10/A17 + suite Categoría | Corregir `test_inv_company_isolation` (fuera de gate) |

---

## 4. Estado observado del working tree (informativo)

Al momento de este plan, `git status` muestra `M tests/unit/test_inv_audit_usuario.py` con
una **alineación ya aplicada en disco** (no commit) que hace pasar A10/A17. Ese diff
**anticipa** la solución aquí documentada, pero **no sustituye la aprobación formal** de
este plan. La implementación oficial solo procede tras aprobación explícita, y el alcance
de commit debe limitarse a C-01/C-02 (+ helpers necesarios), sin arrastrar cambios de
otras entidades del mismo archivo salvo decisión aparte.

---

## 5. Documentos

| Doc | Contenido |
|-----|-----------|
| `00_EXECUTIVE_SUMMARY.md` | Este documento |
| `01_ROOT_CAUSE_ANALYSIS.md` | Qué asumían, qué cambió, mocks faltantes |
| `02_TEST_ALIGNMENT_PLAN.md` | Qué mockear / no mockear, asserts, riesgos |
| `03_IMPLEMENTATION_GUIDE.md` | Pasos exactos de implementación post-aprobación |

---

## 6. Condición de cierre hacia dictamen A

1. Plan aprobado.
2. A10 y A17 verdes con mocks UoW + assert de auditoría intacto.
3. Suite Fase A Categoría (24 tests) sigue verde.
4. Re-auditoría breve confirma gate de suite 100% verde → dictamen **A**.
