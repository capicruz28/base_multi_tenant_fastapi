# Estrategia de pruebas — Inmutabilidad del código

**Fecha:** 2026-07-13  
**Alcance:** Backend unit/integration; guía e2e FE  
**Sin ejecutar ni escribir tests en esta auditoría**

---

## 1. Objetivos de prueba

1. Demostrar que **UPDATE no muta** el código persistido.
2. Demostrar que **UPDATE no invoca** el Motor.
3. Demostrar que **CREATE** (auto y manual) **no regresa**.
4. Cubrir las **5 entidades ORG** de forma homogénea.
5. Dejar plantilla reutilizable para **INV**.

---

## 2. Casos nuevos (obligatorios Backend)

### 2.1 Por entidad (plantilla)

Entidades: `empresa`, `sucursal`, `departamento`, `centro_costo`, `cargo`.

| ID | Caso | Arrange | Act | Assert |
|----|------|---------|-----|--------|
| IMM-01 | Update sin campo código | Registro con código `X` | PUT solo `nombre` | 200; código sigue `X` |
| IMM-02 | Update intenta otro código | Registro `X` | PUT con código `Y` | Strip: código `X` **o** 422 `CODE_IMMUTABLE` (según fase) |
| IMM-03 | Update código igual | Registro `X` | PUT código `X` + nombre | Código `X`; Motor **no** llamado |
| IMM-04 | Motor no se llama en Update | Spy `OrgCodigoGenerationService` / Gateway | Update cualquier | `resolve` / `allocate` **not awaited** |
| IMM-05 | Schema Update sin campo | Instanciar `*Update` | `model_fields` | `codigo` / `codigo_empresa` **absent** |

### 2.2 Empresa-específico

| ID | Caso | Assert |
|----|------|--------|
| IMM-E01 | Update RUC permitido | RUC cambia; `codigo_empresa` intacto |
| IMM-E02 | Update no toca bootstrap cfg | Sin side effects secuencias |

### 2.3 Company-scoped

| ID | Caso | Assert |
|----|------|--------|
| IMM-C01 | Update con sesión empresa OK | 200 |
| IMM-C02 | Cross-empresa | 404 (sin cambio vs hoy) |

---

## 3. Casos de regresión CREATE (obligatorios)

Reutilizar / no degradar suites:

- `tests/unit/test_org_empresa_motor_integration.py`
- `tests/unit/test_org_sucursal_motor_integration.py`
- `tests/unit/test_org_departamento_motor_integration.py`
- `tests/unit/test_org_centro_costo_motor_integration.py`
- `tests/unit/test_org_cargo_motor_integration.py`

| ID | Caso | Assert |
|----|------|--------|
| REG-01 | Auto without código | 201 + allocate |
| REG-02 | Manual accepted | 201 |
| REG-03 | Manual duplicate | 409 |
| REG-04 | cfg missing | NotFound propagates |
| REG-05 | UoW single begin | Invariante |

---

## 4. Casos eliminados / obsoletos

| Caso legacy (si existiera) | Acción |
|----------------------------|--------|
| “Update cambia código con UNIQUE OK” | **Eliminar** o convertir a IMM-02 |
| “Update realinea contador al cambiar código” | **Eliminar** (nunca implementar) |
| “validate_manual en UPDATE” | **No añadir** |

**Nota:** Hoy las suites motor **no** cubren Update de código; el riesgo es ausencia de red de seguridad, no tests contradictores.

---

## 5. Pruebas OpenAPI / schema (unit ligeras)

| ID | Caso |
|----|------|
| SCH-01 | `CargoUpdate.model_fields.keys()` no contiene `codigo` |
| SCH-02 | `EmpresaUpdate` no contiene `codigo_empresa` |
| SCH-03 | `CargoCreate` sí contiene `codigo` Optional |
| SCH-04 | `CargoRead.codigo` annotation `str` (required) |

---

## 6. Pruebas Motor core

| Suite | Acción |
|-------|--------|
| `test_codigo_engine_*` | **No cambio** — sin UPDATE |
| PolicyResolver | **No** añadir rama UPDATE |

---

## 7. E2E / Frontend (guía)

| ID | Caso | Esperado |
|----|------|----------|
| FE-IMM-01 | Editar nombre cargo | Éxito; código UI invariante |
| FE-IMM-02 | Campo código disabled en edit | No editable |
| FE-IMM-03 | DevTools fuerza PUT con código nuevo | BE strip/422; UI refresca código original |
| FE-IMM-04 | Create sin código | Sin regresión Ola 1 |

---

## 8. Matriz de cobertura mínima gate

Antes de merge implementación:

| Gate | Criterio |
|------|----------|
| G1 | IMM-01..05 × ≥1 entidad + parametrize resto |
| G2 | REG-01..05 verdes (5 entidades) |
| G3 | SCH-01..04 |
| G4 | Diff `app/core/codigo/**` vacío (salvo docs si aplica) |
| G5 | Contrato FE doc actualizado en mismo epic |

---

## 9. Riesgos de prueba

| Riesgo | Mitigación |
|--------|------------|
| Solo testear strip y no schema | Incluir SCH-* |
| Mock excesivo oculta query UPDATE código | Assert en payload pasado a `update_*` query: sin key código |
| Olvidar empresa (`codigo_empresa`) | Checklist nombres de campo |

### Assert recomendado en service test

```text
update_fn.await_args.kwargs["data"]  →  "codigo" not in data
Gateway.allocate  →  not called
```

---

## 10. Plantilla INV (futuro)

Al migrar `inv_producto.codigo_sku`:

| Reutilizar | IMM-* IDs con prefijo `INV-IMM-` |
| CREATE | Suite motor INV dedicada |
| UPDATE | Misma política BR-IMM |

---

*Índice del paquete: [`00_EXECUTIVE_SUMMARY.md`](00_EXECUTIVE_SUMMARY.md)*
