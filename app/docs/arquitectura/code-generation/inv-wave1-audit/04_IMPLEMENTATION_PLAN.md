# Plan de implementación Ola 1 INV — por fases

**Modo:** Adopción Baseline V1 · Golden Reference ORG  
**Prohibido:** tocar `app/core/codigo`, Gateway, SequenceCatalog, BR-IMM normativa

---

## 1. Orden óptimo

```text
Fase 0  Auditoría (ESTE PAQUETE)           ✅
Fase A  Fundación INV adapter + 1 piloto
Fase B  Maestros F1 restantes (×4)
Fase C  Documentos F2 + eliminar gen timestamp
Fase D  OpenAPI snapshot + contrato FE INV
Fase E  Certificación DoD Baseline V1
```

**Piloto recomendado Fase A:** `inv_almacen` o `inv_categoria_producto` (menor acoplamiento que producto).  
**Producto (`codigo_sku`)** justo después de categoría + UM (deps de create).

Orden maestros sugerido:

1. `inv_categoria_producto`  
2. `inv_unidad_medida`  
3. `inv_tipo_movimiento`  
4. `inv_almacen`  
5. `inv_producto`  

Documentos:

6. `inv_movimiento` (+ estorno/ajuste allocate)  
7. `inv_inventario_fisico`  

---

## 2. Detalle por fases

### Fase A — Fundación

| Entregable | Notas |
|------------|-------|
| `InvCodigoGenerationService` | Copia delgada del patrón ORG |
| Primera entidad F1 + BR-IMM Update | Schemas + service UoW + tests |
| Gate | CREATE auto/manual; UPDATE sin código; Motor no invocado en UPDATE |

### Fase B — Maestros F1 completos

| Entregable | Notas |
|------------|-------|
| 4 maestros restantes | Mismo patrón |
| Producto | Cuidado: `codigo_barra` etc. **permanecen** opcionales/manual |
| Tests | Suite por entidad + regresión stock write policy intacta |

### Fase C — Documentos F2

| Entregable | Notas |
|------------|-------|
| `numero_movimiento` AUTO_REQUIRED | Quitar required del Create; strip si FE envía |
| `numero_inventario` AUTO_REQUIRED | Idem |
| Estorno / aprobación IF | Reemplazar timestamp gens por Gateway.allocate |
| BR-IMM | Quitar números de Update schemas |
| Workflow | No renumerar en `procesar` |

### Fase D — Contrato

| Entregable | Notas |
|------------|-------|
| Regenerar OpenAPI snapshot | Tras cierre schemas |
| Doc FE INV (contrato) | Parallel a wave1 ORG frontend-contract |

### Fase E — Certificación

Checklist Baseline [`baseline-v1/04_CHECKLISTS.md`](../baseline-v1/04_CHECKLISTS.md) §2 INV + DoD [`06_DEFINITION_OF_DONE.md`](../baseline-v1/06_DEFINITION_OF_DONE.md).

---

## 3. Trabajo por entidad (plantilla)

Para cada `sequence_key`:

1. Schema Create → optional / omit número si AUTO_REQUIRED  
2. Schema Update → eliminar campo Motor  
3. `create_*_servicio` → UoW + `InvCodigoGenerationService`  
4. `update_*_servicio` → eliminar UNIQUE/código  
5. Tests CREATE + IMM  
6. No tocar queries salvo dual-path session si falta  

---

## 4. Fuera de Ola 1 INV

| Ítem | Motivo |
|------|--------|
| Módulo admin CFG | Etapa propia |
| Series fiscales INVBILL | Store FISCAL; otro stream |
| Ubicaciones WMS / POS | Otros módulos / keys |
| Rediseño workflow INV | Ya existe; solo numeración |
| Frontend implementación | Tras BE certificado por fase |

---

## 5. Riesgos del plan (consolidado)

| Fase | Riesgo principal | Mitigación |
|------|------------------|------------|
| A/B | Olvidar BR-IMM en Update | Checklist + test IMM obligatorio |
| C | Numeración dual timestamp vs MOV | Un solo path allocate; tests estorno |
| C | Breaking FE movimientos | Comunicación: número solo en response |
| Global | Presión a “parchar” Catalog | Rechazo; Baseline V1 |

---

## 6. Recomendación final Ola 1 INV

| Dimensión | Decisión |
|-----------|----------|
| **Enfoque** | Adopción Baseline V1 · clonar patrón ORG |
| **Alcance mínimo certificable** | 5 maestros F1 con BR-IMM |
| **Alcance completo Ola 1** | Maestros F1 + documentos F2 + eliminación gens ad hoc |
| **Motor** | **Congelado** — cero cambios |
| **INV es siguiente Golden prácticum** | Pero **ORG permanece** la Golden Reference normativa |

### Veredicto de planificación

> La Ola 1 de INV está **completamente diseñable** con el catálogo actual y el Baseline V1.  
> **No** se requiere rediseño del Motor de Códigos.  
> El mayor cuidado técnico es la **fase documental** (reemplazar generadores por timestamp) y aplicar **BR-IMM** a `codigo_sku` / números desde el primer PR de cada entidad.

**Próximo paso tras aprobación de esta auditoría:** Fase A implementación (adapter + primera entidad) — fuera de esta fase documental.

---

## 7. Matriz rápida de respuesta a las 15 preguntas

| # | Pregunta | Respuesta corta |
|---|----------|-----------------|
| 1 | Inventario | §01 — 11 superficies; 7 con Motor |
| 2 | Requieren Motor | 5 F1 + 2 F2 |
| 3 | No Motor | Stock, kardex, detalles, códigos aux producto, workflow |
| 4 | sequence_key | Matriz §02 (ya en Catalog) |
| 5 | ScopeType | **EMPRESA** en todas las keys Ola 1 |
| 6 | Policy | F1 AUTO_DEFAULT · F2 AUTO_REQUIRED |
| 7 | Campo físico | `codigo` / `codigo_sku` / `numero_*` según matriz |
| 8 | Migración | Align high-water; formatos legacy; M-01…M-06 |
| 9 | ORG | Sesión empresa; FKs opcionales; patrón Golden — no shared adapter |
| 10 | CFG | Seed EMPRESA existente; admin CFG fuera de ola |
| 11 | OpenAPI | Create optional; Update sin código; snapshot al cierre |
| 12 | Frontend | Quitar required; Update RO; docs sin input número |
| 13 | Orden | Cat→UM→TM→Alm→Prod→Mov→IF |
| 14 | Riesgos arch | A-01…A-07 + gens timestamp |
| 15 | Recomendación | Ola 1 = F1 luego F2; Motor intacto |

---

*Índice: [`00_EXECUTIVE_SUMMARY.md`](00_EXECUTIVE_SUMMARY.md)*
