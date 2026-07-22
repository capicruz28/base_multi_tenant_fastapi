# Inmutabilidad del código — Resumen ejecutivo

**Etapa:** Decisión arquitectónica — **Fase 1 normativa CERRADA**  
**Fecha:** 2026-07-13  
**Estado:** **APROBADA** — lista para iniciar implementación runtime (Fase 2)  
**Alcance:** Regla oficial del Motor de Códigos — todos los módulos actuales y futuros (ORG, INV, LOG, COM, POS, …)  
**Informe de cierre:** [`07_NORMATIVE_APPROVAL.md`](07_NORMATIVE_APPROVAL.md)

---

## 1. Decisión bajo auditoría

> El código funcional de cualquier entidad administrada por el Motor de Códigos es **INMUTABLE** después de la creación del registro.

Implicaciones normativas:

| Afirmación | Valor |
|------------|-------|
| `generation_policy` aplica solo a | **CREATE** (e IMPORT histórico controlado) |
| El Motor participa solo en | **CREATE** / IMPORT / PREVIEW / ALIGN |
| UPDATE | **Nunca** modifica el código |
| UPDATE | **Nunca** invoca el Motor |
| El código pasa a ser | Identidad funcional del registro |

---

## 2. Veredicto

| Pregunta | Respuesta |
|----------|-----------|
| ¿La decisión es consistente con ERP empresariales? | **Sí** — SAP, Dynamics, Oracle/NetSuite tienden a tratar el ID de negocio como estable; muchos bloquean edición tras creación o tras publicación |
| ¿Es consistente con el Motor AS-IS? | **Parcialmente** — el Motor **ya no tiene** `GenerationOperation.UPDATE`; ORG Update **sí** permite mutar código **sin** Motor |
| ¿Contradice documentación vigente? | **Resuelto en Fase 1** — BR-IMM oficial; BR-M-30/31 superseded/deprecated |
| ¿Bloquea Ola 1 INV? | **No**, si se aprueba e implementa la regla **antes** o **como prerequisito contractual** de INV; no bloquear INV CREATE |
| ¿Conviene implementar ahora? | **Sí, tras aprobación** — evitar que INV heredé el anti-patrón “código editable en UPDATE” |

**Veredicto arquitectónico:** La decisión es **sólida y recomendable**. El gap real está en la capa ERP (schemas Update + services Update + contrato Frontend), no en el core del Motor.

---

## 3. Hallazgo crítico AS-IS

```
CREATE ORG  → OrgCodigoGenerationService → Gateway.allocate  ✅
UPDATE ORG  → update_*_servicio puede mutar codigo/codigo_empresa  ⚠️ SIN Motor
Motor enums → GenerationOperation = CREATE | IMPORT | PREVIEW | ALIGN  (sin UPDATE) ✅
```

| Capa | ¿Código inmutable hoy? |
|------|------------------------|
| Gateway / PolicyResolver | N/A — no hay operación UPDATE |
| OrgCodigoGenerationService | Solo CREATE |
| ORG Update services (5 maestros) | **No** — permiten cambio con pre-check UNIQUE |
| `ParametroUpdate` | **Sí** (ya excluye `codigo_parametro`) |
| INV `ProductoUpdate.codigo_sku` | **No** — editable (aún sin motor) |
| Frontend contract Ola 1 ORG | Documenta código **editable** en UPDATE |

---

## 4. Impacto por severidad

| Severidad | Componentes |
|-----------|-------------|
| **Alta** | 5 services UPDATE ORG; 5 schemas Update ORG; contrato Frontend wave1; BR-M-30/31 y `08_CODE_POLICIES.md` |
| **Media** | OpenAPI generado; tests Update si existen; docs wave1 (`04_FUNCTIONAL_CONTRACT`, org-* audits); INV producto (preemptivo Ola 1 INV) |
| **Baja / nula** | Gateway, SequenceCatalog, OrgCodigoGenerationService, queries (siguen pudiendo SET codigo en SQL pero service no debe enviarlo), Read schemas |

---

## 5. Documentos de este paquete

| # | Documento | Contenido |
|---|-----------|-----------|
| 00 | Este archivo | Resumen y veredicto |
| 01 | [`01_ARCHITECTURAL_DECISION.md`](01_ARCHITECTURAL_DECISION.md) | ADR, SAP/Oracle/Dynamics, nueva regla oficial |
| 02 | [`02_IMPACT_ANALYSIS.md`](02_IMPACT_ANALYSIS.md) | Inventario por componente |
| 03 | [`03_BACKWARD_COMPATIBILITY.md`](03_BACKWARD_COMPATIBILITY.md) | Compatibilidad y Breaking Change |
| 04 | [`04_IMPLEMENTATION_STRATEGY.md`](04_IMPLEMENTATION_STRATEGY.md) | Fases, riesgos, rollback |
| 05 | [`05_OPENAPI_CONTRACT_IMPACT.md`](05_OPENAPI_CONTRACT_IMPACT.md) | Contrato FE |
| 06 | [`06_TESTING_STRATEGY.md`](06_TESTING_STRATEGY.md) | Casos nuevos / regresión |
| 07 | [`07_NORMATIVE_APPROVAL.md`](07_NORMATIVE_APPROVAL.md) | **Cierre Fase 1 — arquitectura aprobada** |

---

## 6. Relación con BR existente (propuesta documental)

| Regla actual | Destino propuesto (post-aprobación) |
|--------------|-------------------------------------|
| **BR-M-30** (inmutable tras referencias) | **SUPERSEDED** por **BR-M-30-IMM** (inmutable desde CREATE) |
| **BR-M-31** (editable sin referencias) | **DEPRECATED / eliminada** para entidades Motor |
| **BR-M-33** (migración asistida) | Se mantiene — único camino excepcional de “cambio” de código (fuera API UPDATE estándar) |
| Documentos (BR-D-03) | Ya alineado (“correlativo de por vida”) |

El ID oficial sugerido: **BR-IMM-01** (ver `01`).

---

## 7. Próximo paso

1. ~~Aprobar esta auditoría~~ → **Hecho** (Fase 1 normativa — ver [`07_NORMATIVE_APPROVAL.md`](07_NORMATIVE_APPROVAL.md)).  
2. Fase de **implementación runtime** (Fase 2): ORG schemas Update → services → tests → contrato FE OpenAPI.  
3. **No** iniciar Ola 1 INV Create con Update mutable; plantilla INV nace con BR-IMM.

---

*Ubicación canónica:* `app/docs/arquitectura/code-generation/code-immutability/` (regla oficial Motor).
