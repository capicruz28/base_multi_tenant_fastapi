# ADR — Inmutabilidad del código post-CREATE

**Tipo:** Architectural Decision Record  
**Estado:** **APROBADO** — Fase 1 normativa cerrada (2026-07-13)  
**Fecha:** 2026-07-13  
**Aplica a:** Entidades gobernadas por el Motor de Códigos (`SequenceCatalog` / store CFG o FISCAL)  
**Runtime:** Enforcement en schemas/services Update = **fase 2 pendiente** (sin cambios de código en Fase 1)

---

## 1. Contexto

CAXIS ERP ya opera con:

- Motor congelado en `app/core/codigo` (`CodigoGeneracionGateway`).
- Ola 1 ORG cerrada: CREATE usa `OrgCodigoGenerationService` → `allocate`.
- Documentación F15A con **BR-M-30 / BR-M-31**: el código maestro es inmutable **después del primer uso operativo**, y editable **antes** con permiso.

La operación real ORG UPDATE **sí permite** cambiar `codigo` / `codigo_empresa` sin invocar el Motor ni alinear contadores, lo que abre drift y contradice la identidad estable de maestros en ERP SaaS.

Decisión de negocio/arquitectura bajo revisión: **código inmutable desde el instante de CREATE**.

---

## 2. Decisión

### 2.1 Regla oficial propuesta — **BR-IMM-01**

| ID | Regla |
|----|-------|
| **BR-IMM-01** | El código funcional asignado (auto o manual) en CREATE es **inmutable** durante toda la vida del registro. |
| **BR-IMM-02** | `generation_policy` (`AUTO_*`, `MANUAL_ONLY`) aplica **exclusivamente** a operaciones de creación / importación histórica controlada. |
| **BR-IMM-03** | UPDATE de entidad de negocio **nunca** incluye mutación del campo código gobernado por el Motor. |
| **BR-IMM-04** | UPDATE **nunca** invoca `CodigoGeneracionGateway` ni `OrgCodigoGenerationService` (ni equivalentes futuros por módulo). |
| **BR-IMM-05** | El único camino excepcional para “cambiar” un código es proceso de **re-maestro / migración asistida** (BR-M-33), fuera del UPDATE estándar API. |

### 2.2 Qué NO cambia

| Aspecto | Comportamiento |
|---------|----------------|
| CREATE AUTO_DEFAULT | Omisión → auto; valor → manual + align |
| CREATE AUTO_REQUIRED | Siempre auto |
| CREATE MANUAL_ONLY | Siempre manual |
| PREVIEW / ALIGN | Operaciones admin/mantenimiento — no son UPDATE de entidad |
| Soft-delete / reactivar | No tocan código |
| Códigos EXTERNAL (RUC, CIIU, ubigeo) | Reglas propias; fuera del Motor secuencial |
| Claves no-Motor (`codigo_parametro`, `codigo_barra` no catálogo, etc.) | Evaluación caso a caso; esta ADR cubre **campos del SequenceCatalog** |

---

## 3. Justificación

1. **Identidad funcional:** El código es el identificador que usuarios, reportes, integraciones y FKs lógicas usan cotidianamente. Mutarlo rompe trazabilidad histórica aunque el UUID interno no cambie.
2. **Separación de responsabilidades:** El Motor gestiona *asignación*; el ERP no debe reinventar renumeración en UPDATE.
3. **Simplificación:** Elimina la necesidad de “detectar referencias operativas” (costoso, incompleto, propenso a fugas) antes de permitir edición.
4. **Consistencia multi-módulo:** Misma regla ORG → INV → LOG → POS sin matices por “aún no hay movimientos”.
5. **SaaS multi-tenant:** Reduce soporte por “alguien renombró el código y se desalineó el contador”.
6. **Alineación con el Motor AS-IS:** `GenerationOperation` **no incluye UPDATE** — la ADR completa el contrato que el core ya asume.

---

## 4. Comparación con ERP empresariales

| Sistema | Patrón típico | Relación con BR-IMM |
|---------|---------------|---------------------|
| **SAP Business One / S/4** | Item Code / CardCode estables; cambios de código son procesos excepcionales (DTW, migraciones), no edición casual | Muy alineado |
| **Microsoft Dynamics 365 BC** | No. / Code de maestros tratados como clave de negocio; renumeración limitada / herramientas especiales | Muy alineado |
| **Oracle NetSuite** | IDs / numbering publicados; cambios de identificadores clave restringidos tras posting | Alineado (umbral “publicado” ≈ CREATE en maestros ligeros) |
| **Odoo** | `default_code` / secuencias; editar referencia es posible pero riesgoso; documentos no se renumeran | BR-IMM es **más estricta** (correcto para SaaS ERP) |
| **CAXIS F15A actual** | Inmutable **tras uso** (BR-M-30) + editable sin uso (BR-M-31) | **Más laxo** que la nueva decisión |

### 4.1 Lectura de mercado

Los ERP maduros priorizan **estabilidad del identificador de negocio**. La ventana “editable mientras no haya referencias” existe en paper, pero:

- Es difícil de implementar de forma completa (qué cuenta como referencia).
- Invita a “corregir” códigos en producción creando deuda.
- Colisiona con reportes, barcodes, etiquetas e integraciones ya emitidas **antes** del primer documento formal.

**Decisión CAXIS:** cerrar la ventana. Corrección de error tipográfico → **anular (soft) + crear de nuevo**, o migración asistida.

---

## 5. Alternativas consideradas

| Opción | Descripción | Veredicto |
|--------|-------------|-----------|
| **A — Status quo BR-M-30/31** | Editable sin referencias | Rechazada para Motor entities — compleja y frágil |
| **B — Inmutable solo tras primer documento** | Implementar detector de referencias | Rechazada como default; puede vivir solo en tools de migración |
| **C — Inmutable desde CREATE (esta ADR)** | UPDATE no acepta campo código | **Elegida** |
| **D — Soft lock con rol superadmin** | PATCH código con permiso especial | Diferida; si se necesita, va bajo BR-M-33 (no UPDATE estándar) |

---

## 6. Consecuencias

### Positivas

- Contrato API simple: Create opcional / auto; Update sin código.
- Frontend: input código solo lectura en edición.
- Sin drift contador ↔ código manual en UPDATE.
- Plantilla clara para Ola 1 INV.

### Negativas / trade-offs

- Breaking soft hacia clientes que YA envían `codigo` en PUT (ver `03`).
- Error tipográfico en CREATE exige soft-delete + recreate (o import tool).
- Documentación normativa a actualizar (BR-M-31 out).

---

## 7. Relación con documentos supersedidos (cumplido Fase 1 normativa)

Tras aprobación Fase 1, actualizados:

| Documento | Acción |
|-----------|--------|
| `07_BUSINESS_RULES.md` §3.4 | **BR-IMM-01…05**; BR-M-31 DEPRECATED |
| `08_CODE_POLICIES.md` | Edición AUTO_DEFAULT → prohibida post-CREATE |
| `09_ERP_BEST_PRACTICES.md` | Inmutabilidad post-CREATE |
| `10_FINAL_RECOMMENDATION.md` | STD-E-* → BR-IMM |
| `12_GATEWAY_DESIGN.md` | Update = servicio ERP, no Gateway |
| `catalog/18_SEQUENCE_DEFINITION_MODEL.md` | `editable_*=false` |
| `codigo-generation-wave1/frontend-contract/*` | Objetivo UPDATE solo lectura |

Informe: [`07_NORMATIVE_APPROVAL.md`](07_NORMATIVE_APPROVAL.md).

---

## 8. Criterio de aceptación de la decisión

La decisión se considera **oficial** cuando:

1. ~~Arquitectura + Producto aprueben este ADR por escrito.~~ → **Cumplido** (Fase 1 — [`07_NORMATIVE_APPROVAL.md`](07_NORMATIVE_APPROVAL.md)).
2. ~~BR-IMM-01 quede registrado en `07_BUSINESS_RULES.md`.~~ → **Cumplido**.
3. Al menos ORG 5 maestros implementen enforcement en Update → **Fase 2 runtime (pendiente)**.

**Estado ADR:** **APROBADO** (normativa). Runtime: pendiente.

---

*Impacto técnico: [`02_IMPACT_ANALYSIS.md`](02_IMPACT_ANALYSIS.md)*
