# Matriz Motor INV — sequence_key / scope / policy / campo

**Fuente autoritativa keys:** `app/core/codigo/sequence_catalog.py` (congelado)  
**Baseline:** no inventar keys nuevas en Ola 1

---

## 1. Matriz entidad → Motor (oficial catálogo)

| Entidad | sequence_key | Campo físico | ScopeType | generation_policy | Family | Prefijo | Padding | max_len | Store |
|----------|--------------|--------------|-----------|-------------------|--------|---------|---------|---------|-------|
| Categoría | `inv_categoria_producto` | `codigo` | EMPRESA | AUTO_DEFAULT | F1 | CAT | 3 | 20 | CFG |
| Unidad medida | `inv_unidad_medida` | `codigo` | EMPRESA | AUTO_DEFAULT | F1 | UM | 3 | 10 | CFG |
| Producto | `inv_producto` | `codigo_sku` | EMPRESA | AUTO_DEFAULT | F1 | P | **5** | 50 | CFG |
| Almacén | `inv_almacen` | `codigo` | EMPRESA | AUTO_DEFAULT | F1 | ALM | 3 | 20 | CFG |
| Tipo movimiento | `inv_tipo_movimiento` | `codigo` | EMPRESA | AUTO_DEFAULT | F1 | TM | 3 | 20 | CFG |
| Movimiento | `inv_movimiento` | `numero_movimiento` | EMPRESA | **AUTO_REQUIRED** | F2 | MOV | 6 | 20 | CFG |
| Inventario físico | `inv_inventario_fisico` | `numero_inventario` | EMPRESA | **AUTO_REQUIRED** | F2 | IF | 5 | 20 | CFG |

**Context CREATE (todos):** `client_id` + `empresa_id` (sesión COMPANY) + `manual_code` solo si política lo permite.

---

## 2. Comportamiento CREATE esperado (Baseline)

| sequence_key | Omisión código/número | Envío manual | BR-IMM Update |
|--------------|----------------------|--------------|---------------|
| 5× F1 | Auto (p.ej. `P00001`, `ALM001`) | Aceptar si válido/único | Campo **ausente** en `*Update` |
| `inv_movimiento` | Auto obligatorio | **Rechazar** (AUTO_REQUIRED) | `numero_movimiento` **ausente** en Update |
| `inv_inventario_fisico` | Auto obligatorio | **Rechazar** | `numero_inventario` **ausente** en Update |

---

## 3. Ejemplos de formato (defaults catálogo)

| Key | Ejemplo auto |
|-----|--------------|
| `inv_categoria_producto` | `CAT001` |
| `inv_unidad_medida` | `UM001` |
| `inv_producto` | `P00001` |
| `inv_almacen` | `ALM001` |
| `inv_tipo_movimiento` | `TM001` |
| `inv_movimiento` | `MOV000001` |
| `inv_inventario_fisico` | `IF00001` |

Prefijos/padding efectivos: fila `cfg_codigo_secuencia` del scope EMPRESA (seed bootstrap al crear empresa).

---

## 4. Entidades fuera de matriz Motor (explícito)

| Elemento | sequence_key | Motivo |
|----------|--------------|--------|
| Stock | — | Derivada |
| Kardex | — | Lectura |
| Movimiento detalle | — | Línea embebida |
| Inv. físico detalle | — | Línea embebida |
| `codigo_barra` etc. | — | MANUAL/EXTERNAL; no F1 sku |

---

## 5. GenerationContext INV (propuesta adapter)

```text
InvCodigoGenerationService.resolve_codigo_for_create(
    sequence_key,
    session=session,
    client_id=...,
    empresa_id=...,          # siempre Scope EMPRESA
    manual_code=...,         # None si omitido / AUTO_REQUIRED
)
```

Misma firma conceptual que ORG; **sin** cambiar Gateway.

---

## 6. Riesgos de migración / datos existentes

| ID | Riesgo | Severidad | Mitigación |
|----|--------|-----------|------------|
| M-01 | SKUs / códigos libres históricos no parseables | Media | Import + `align_counter`; no forzar reescritura |
| M-02 | Contador cfg en 0 con datos legacy | Alta | Align high-water post-import / al primer allocate (lazy ensure ya en Motor) |
| M-03 | `numero_movimiento` legacy y timestamp (`INV-EST-…`) | Alta | Fase docs: alinear contador; no colisionar formato MOV* |
| M-04 | Tenants greenfield | Baja | Seed EMPRESA al crear empresa ya incluye keys CFG catálogo |
| M-05 | Producto Update aún muta SKU en producción | Alta | BR-IMM en misma PR de CREATE producto |
| M-06 | Estorno sigue usando timestamp tras Ola F2 incompleta | Alta | Incluir reemplazo gen ad hoc en fase documentos |

---

*Dependencias e impacto: [`03_DEPENDENCIES_AND_IMPACT.md`](03_DEPENDENCIES_AND_IMPACT.md)*
