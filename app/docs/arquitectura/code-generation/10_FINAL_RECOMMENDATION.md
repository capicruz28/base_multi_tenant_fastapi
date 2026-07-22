# F15A — Recomendación oficial: Estándar de generación de códigos CAXIS ERP

**Fase:** F15A — Política funcional (cierre normativo)  
**Fecha:** 2026-07-02  
**Estado:** **APROBADO PARA FASE 2** (diseño DDL + gateway)  
**Jerarquía:** Complementa F15 (`01`–`06`); junto con `07`–`09` forma el estándar funcional completo.

---

## 1. Declaración de estándar

El **Estándar Oficial de Generación de Códigos CAXIS ERP V1** establece que:

1. Todo código de negocio obedece una de cuatro políticas: **AUTO_REQUIRED**, **AUTO_DEFAULT**, **MANUAL_ONLY**, **EXTERNAL** (`08_CODE_POLICIES.md`).
2. El **scope de unicidad** se deriva del UNIQUE de V010, no de preferencia de módulo (`03_SEQUENCE_SCOPE.md`).
3. Los **documentos de proceso** son AUTO_REQUIRED sin excepción en operación normal.
4. Los **maestros operativos** son AUTO_DEFAULT en operación normal.
5. La **numeración fiscal** es un dominio regulado aparte, con AUTO_REQUIRED en emisión y MANUAL_ONLY en alta de serie.
6. Los códigos gobernados por el Motor son **inmutables desde CREATE** (**BR-IMM-01**; ADR `code-immutability/`).

Este estándar es **vinculante** para nuevos módulos ERP y para la Fase 2 de implementación del motor.

---

## 2. Decisiones oficiales por tema

### 2.1 Políticas de generación

| Decisión ID | Decisión |
|-------------|----------|
| **STD-01** | AUTO_REQUIRED para los 24 tipos documentales grupo C de F15. |
| **STD-02** | AUTO_DEFAULT para los maestros grupo B salvo campos explícitamente MANUAL_ONLY o EXTERNAL en `08`. |
| **STD-03** | EXTERNAL para catálogos `cat_*`, identidad legal, artefactos SUNAT, `cliente.codigo_cliente` SaaS. |
| **STD-04** | Prohibido introducir nuevos patrones ad hoc (`timestamp`, concatenación inter-módulo) en código de negocio. |

### 2.2 Maestros

| Decisión ID | Decisión |
|-------------|----------|
| **STD-M-01** | Autogenerar si el usuario omite código en Create. |
| **STD-M-02** | Aceptar manual si cumple formato, longitud y unicidad. |
| **STD-M-03** | Bloquear edición de código con referencias operativas. |
| **STD-M-04** | Migración: preservar códigos legados; alinear contador al máximo existente. |

### 2.3 Documentos

| Decisión ID | Decisión |
|-------------|----------|
| **STD-D-01** | El usuario no envía correlativo en API estándar de creación. |
| **STD-D-02** | Asignar correlativo al crear en estado inicial (`borrador` o equivalente). |
| **STD-D-03** | Estornos y compensaciones: nuevo correlativo + referencia al original. |
| **STD-D-04** | Cada módulo consume su secuencia; prohibida identidad derivada del documento origen. |

### 2.4 Fiscal

| Decisión ID | Decisión |
|-------------|----------|
| **STD-F-01** | Emisión: siguiente número de serie activa; usuario no elige. |
| **STD-F-02** | Serie inactiva o agotada bloquea emisión. |
| **STD-F-03** | Huecos por anulación aceptados; sin reutilización de número emitido. |
| **STD-F-04** | Hash/QR/respuesta SUNAT fuera del motor de códigos internos. |

### 2.5 Importación masiva

| Decisión ID | Decisión |
|-------------|----------|
| **STD-I-01** | Código presente y único → persistir y alinear contador. |
| **STD-I-02** | Código ausente en maestro → AUTO_DEFAULT. |
| **STD-I-03** | Código ausente en documento histórico → rechazo salvo modo implantación explícito. |
| **STD-I-04** | Duplicado en lote o BD → rechazo de fila, no sustitución silenciosa. |

### 2.6 Concurrencia

| Decisión ID | Decisión |
|-------------|----------|
| **STD-C-01** | Dos altas simultáneas sin código → dos códigos distintos consecutivos. |
| **STD-C-02** | Dos altas con mismo código manual → una exitosa, una con error de duplicado. |
| **STD-C-03** | Expectativa de idempotencia en reintentos de red (un correlativo por intención de negocio). |

### 2.7 Preview

| Decisión ID | Decisión |
|-------------|----------|
| **STD-P-01** | Preview opcional solo para maestros AUTO_DEFAULT. |
| **STD-P-02** | Preview nunca consume secuencia ni constituye reserva. |
| **STD-P-03** | UI debe etiquetar como estimado; no usar en documentos fiscales impresos. |

### 2.8 Inmutabilidad del código (BR-IMM)

| Decisión ID | Decisión |
|-------------|----------|
| **STD-E-01** | **SUPERSEDED** — “Sin referencias: edición permitida” (**BR-M-31**) → **prohibido**. Ver **BR-IMM-01**. |
| **STD-E-02** | El código es **inmutable desde CREATE**. Cambio solo por proceso excepcional de re-maestro (**BR-IMM-05** / BR-M-33). |
| **STD-E-03** | Sin ventana temporal ni ventana “antes del primer uso”. |
| **STD-E-04** | UPDATE nunca invoca el Motor (**BR-IMM-04**). `generation_policy` solo en CREATE/IMPORT (**BR-IMM-02**). |

Fuente oficial: `07_BUSINESS_RULES.md` §3.4 · `code-immutability/01_ARCHITECTURAL_DECISION.md`.

### 2.9 Reinicio de secuencias

| Decisión ID | Decisión |
|-------------|----------|
| **STD-R-01** | Sin reinicio automático anual por defecto. |
| **STD-R-02** | Reinicio manual: acción administrativa excepcional, auditada, anti-colisión. |
| **STD-R-03** | Fiscal: solo según normativa y autorización. |

### 2.10 Prefijos

| Decisión ID | Decisión |
|-------------|----------|
| **STD-X-01** | Prefijos configurables por entidad y scope; no retroactivos. |
| **STD-X-02** | Separador configurable por entidad. |
| **STD-X-03** | Series fiscales: MANUAL_ONLY en alta; no son prefijos libres del motor genérico. |

---

## 3. Compatibilidad multi-tenant y hybrid platform

| Dimensión | Estándar |
|-----------|----------|
| **Shared DB** | Políticas idénticas; contadores aislados por `cliente_id`. |
| **Dedicated DB** | Políticas idénticas; contadores en store del tenant. |
| **Multiempresa** | Secuencias independientes por `empresa_id` excepto `org_empresa` (tenant). |
| **Multi-tenant** | Prohibido compartir o inferir secuencias entre tenants. |

La implementación futura debe enrutar al **mismo store operativo** que los datos ERP (patrón F13); las reglas de negocio no cambian entre modos.

---

## 4. Riesgos si se desvía del estándar

| Desviación | Impacto |
|------------|---------|
| Documentos MANUAL_ONLY | Duplicados, fraude, auditoría inviable |
| Omitir scope empresa en secuencia | Colisiones multiempresa |
| Edición libre de códigos usados | Pérdida trazabilidad INV/FIN/fiscal |
| Preview como reserva | Conflictos entre usuarios |
| Reinicio sin control | Duplicados catastróficos |
| Fiscal en cfg genérica | Incumplimiento SUNAT |
| Ignorar import alignment | Colisiones post-migración |

---

## 5. Roadmap funcional (sin implementación)

| Ola | Alcance | Política dominante |
|-----|---------|-------------------|
| **Ola 0** | Estándar F15 + F15A | Documentación — **completado** |
| **Ola 1** | INV movimiento, inventario físico | AUTO_REQUIRED |
| **Ola 2** | PUR (OC, recepción, solicitud) | AUTO_REQUIRED |
| **Ola 3** | SLS (cotización, pedido) | AUTO_REQUIRED |
| **Ola 4** | invbill + guía remisión | AUTO_REQUIRED fiscal |
| **Ola 5** | Maestros ORG/INV | AUTO_DEFAULT |
| **Ola 6** | WMS, POS, resto módulos | Según matrices `08` |

---

## 6. Criterios de aceptación para Fase 2 (diseño técnico)

La Fase 2 podrá iniciarse cuando el diseño técnico demuestre cumplimiento de:

- [ ] Catálogo `entidad_logica` 1:1 con matrices de `08_CODE_POLICIES.md`
- [ ] Scope dimensions T1–T5 de `03_SEQUENCE_SCOPE.md`
- [ ] AUTO_REQUIRED sin campo obligatorio en Create de documentos
- [ ] AUTO_DEFAULT con campo opcional en Create de maestros
- [ ] Transacción atómica asignación + persistencia entidad
- [ ] Alineación contador post-importación (BR-M-41)
- [ ] Exclusión explícita de grupo A y D del motor
- [ ] Submotor fiscal separado para F3

**No reabrir** debate sobre políticas AUTO_* salvo cambio normativo legal o decisión de producto documentada.

---

## 7. Mapa documental F15 + F15A

```
F15 — Auditoría arquitectónica
├── 01_CODE_FIELDS_INVENTORY.md    … qué campos existen
├── 02_ENTITY_CLASSIFICATION.md    … A/B/C/D
├── 03_SEQUENCE_SCOPE.md           … tenant / empresa / almacén / serie
├── 04_CURRENT_STATE_AND_RISKS.md  … AS-IS
├── 05_PROPOSED_ARCHITECTURE.md    … dónde vive el motor (conceptual)
└── 06_EXECUTIVE_SUMMARY.md

F15A — Política funcional  ← ESTÁNDAR DE NEGOCIO
├── 07_BUSINESS_RULES.md           … reglas transversales
├── 08_CODE_POLICIES.md            … AUTO_* / MANUAL / EXTERNAL por entidad
├── 09_ERP_BEST_PRACTICES.md       … validación mercado
└── 10_FINAL_RECOMMENDATION.md     … este documento (cierre normativo)
```

---

## 8. Resumen en una página

| Pregunta | Respuesta oficial CAXIS |
|----------|-------------------------|
| ¿Usuario envía número de OC? | **No** (AUTO_REQUIRED) |
| ¿Usuario puede omitir código de sucursal? | **Sí** — sistema genera (AUTO_DEFAULT) |
| ¿Se puede cambiar SKU / código maestro tras CREATE? | **No** (**BR-IMM-01** — inmutable desde CREATE) |
| ¿Se reinicia secuencia cada año? | **No** por defecto |
| ¿Preview reserva número? | **No** |
| ¿RUC del proveedor lo genera el motor? | **No** (EXTERNAL / legal) |
| ¿Factura usa misma secuencia que movimiento INV? | **No** — serie fiscal aparte |
| ¿Migración trae códigos viejos? | **Sí**, con alineación de contador |
| ¿`PED-{cotización}` es válido? | **No** en estándar objetivo |

---

## 9. Aprobación y mantenimiento

- **Versión:** 1.1 (F15A + **BR-IMM** 2026-07-13)
- **Próxima revisión:** solo ante cambio normativo SUNAT, nuevo módulo ERP con entidades de código no previstas en V010, o decisión explícita de arquitectura.
- **Cambios a políticas base:** requieren actualización de `07`, `08` y este documento en la misma entrega.
- **Inmutabilidad:** cualquier cambio a BR-IMM exige ADR en `code-immutability/` + actualización de `07` §3.4.

---

*Estándar listo para enforcement runtime de BR-IMM (schemas/services Update) sin reabrir la decisión de inmutabilidad.*
