# Principios arquitectónicos obligatorios — Baseline V1

**Estado:** Obligatorio para todo módulo ERP que use el Motor  
**Golden Reference:** ORG Ola 1

---

## 1. Principios

| ID | Principio |
|----|-----------|
| **P-01** | Una sola puerta de asignación: `CodigoGeneracionGateway` (vía adapter de módulo). |
| **P-02** | El Motor **no** conoce entidades ERP concretas (cargo, producto, OC, …); solo `sequence_key` + `GenerationContext`. |
| **P-03** | `generation_policy` aplica **solo** a CREATE (e IMPORT histórico controlado). |
| **P-04** | El código es **identidad funcional** del registro: **inmutable** desde CREATE (**BR-IMM**). |
| **P-05** | UPDATE **nunca** modifica el código ni invoca el Motor. |
| **P-06** | CREATE auto/manual según política del catálogo (`AUTO_REQUIRED` / `AUTO_DEFAULT` / `MANUAL_ONLY`). |
| **P-07** | Scope de unicidad = UNIQUE de V010 + `ScopeType` del catálogo (tenant / empresa / almacén / PV / serie fiscal). |
| **P-08** | ALLOCATE y persistencia de la entidad de negocio en la **misma transacción** (`session.begin`). |
| **P-09** | Dedicated / Shared: escrituras tenant con `get_connection_for_tenant` + session (ADJ-03). |
| **P-10** | OpenAPI refleja schemas: Create optional/manual según política; Update **sin** campo código Motor; Read **con** código. |
| **P-11** | ORG es Golden Reference: copiar el patrón, no reinventarlo. |
| **P-12** | Cambios al Motor / Gateway / catálogo requieren ADR separado — **fuera** del alcance de un módulo ERP. |

---

## 2. Separación de responsabilidades (una frase)

| Rol | Frase |
|-----|-------|
| **Motor** | Formatea, valida, reserva/acepta correlativo, alinea high-water. |
| **Gateway** | Orquesta allocate / preview / validate_manual / align. |
| **Módulo ERP** | Decide *cuándo* pedir código en CREATE; nunca en UPDATE; persiste la fila. |
| **Frontend** | Omite código en Create estándar; no envía código en Update. |

---

## 3. Stack de referencia ORG (no alterable como patrón)

```
presentation/schemas   → Create (código opcional|obligatorio según policy)
                       → Update (SIN código Motor)
                       → Read   (código requerido)
application/services   → create_* : resolve → insert (UoW)
                       → update_* : sin ramas de código
adapter módulo         → OrgCodigoGenerationService (delgado → Gateway)
app/core/codigo        → CONGELADO
```

Módulos futuros: `{Mod}CodigoGenerationService` equivalente, o reutilizar el mismo estilo de delegación.

---

*CREATE y UPDATE: [`02_CREATE_AND_UPDATE.md`](02_CREATE_AND_UPDATE.md)*
