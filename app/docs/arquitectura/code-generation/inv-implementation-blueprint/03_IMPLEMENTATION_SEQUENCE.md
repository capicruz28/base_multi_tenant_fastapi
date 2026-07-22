# Secuencia de implementación, tests y riesgos

---

## 1. Orden exacto de las siete entidades

| Orden | Entidad | sequence_key | Campo | Policy | Gate de cierre |
|-------|---------|--------------|-------|--------|----------------|
| **0** | Adapter | — | — | — | `InvCodigoGenerationService` + test unitario delege Gateway |
| **1** | Categoría | `inv_categoria_producto` | `codigo` | AUTO_DEFAULT | Piloto completo (schemas+queries+service+tests) |
| **2** | Unidad medida | `inv_unidad_medida` | `codigo` | AUTO_DEFAULT | Copia mecánica de (1) |
| **3** | Tipo movimiento | `inv_tipo_movimiento` | `codigo` | AUTO_DEFAULT | Copia mecánica |
| **4** | Almacén | `inv_almacen` | `codigo` | AUTO_DEFAULT | + validar FK sucursal/CC sin tocar Motor |
| **5** | Producto | `inv_producto` | `codigo_sku` | AUTO_DEFAULT | Campo ≠ `codigo`; no mutar barra/interno/fabricante |
| **6** | Movimiento | `inv_movimiento` | `numero_movimiento` | AUTO_REQUIRED | Create sin manual; estorno → allocate |
| **7** | Inventario físico | `inv_inventario_fisico` | `numero_inventario` | AUTO_REQUIRED | Create sin manual; aprobación sin timestamp |

```text
0 Adapter
  → 1 Categoría (piloto / plantilla INV)
    → 2 UM → 3 TipoMov → 4 Almacén → 5 Producto
      → 6 Movimiento (+ estorno/ajuste)
        → 7 Inventario físico
          → OpenAPI snapshot + certificación
```

**Regla:** no iniciar entidad N+1 hasta gate verde de N (salvo adapter+categoría en el mismo PR fundacional).

---

## 2. Pasos mecánicos por entidad F1 (plantilla Categoría)

Para cada maestro AUTO_DEFAULT, en este orden de archivos:

1. **Queries:** `get_*_by_codigo` + dual-path `session` en create/get_by_codigo  
2. **Schemas:** Create optional; Update sin campo Motor; mixin `check_fields=False`  
3. **Service CREATE:** UoW + adapter + ConflictError manual  
4. **Service UPDATE:** asegurar cero lógica de código  
5. **Tests:** motor integration + IMM  
6. **No** cambiar endpoints/rutas/RBAC salvo que el body schema lo exija  

### Producto — delta único

| Paso | Especial |
|------|----------|
| Campo | `codigo_sku` en Create/Update/Read |
| `_SEQUENCE_KEY` | `"inv_producto"` |
| Update | Quitar solo `codigo_sku`; dejar `codigo_barra`, etc. |
| Create dup | `get_producto_by_sku` (ya existe AS-IS) + session |

### Movimiento / IF — delta F2

| Paso | Especial |
|------|----------|
| Create | No aceptar manual (`manual_code=None`) |
| Schema Create | Quitar required del número (preferible omitir del body) |
| Proceso | Reemplazar `gen_numero_movimiento_estorno` / `_gen_numero_movimiento` por allocate |
| UoW | Cabecera (+ detalle embebido) + allocate en **un** begin |

---

## 3. Tests a replicar

### 3.1 Origen Golden Reference

| Suite ORG | Propósito |
|-----------|-----------|
| `tests/unit/test_org_cargo_motor_integration.py` | CREATE auto / manual / dup / cfg missing / UoW |
| `tests/unit/test_org_br_imm_update_immutability.py` | Schema Update sin campo; UPDATE no pasa código; Motor no llamado |

### 3.2 Suites INV objetivo (nombres propuestos)

| Archivo | Cobertura |
|---------|-----------|
| `test_inv_codigo_generation_service.py` | Adapter delega Gateway (mock) |
| `test_inv_categoria_motor_integration.py` | Espejo cargo |
| `test_inv_unidad_medida_motor_integration.py` | Espejo |
| `test_inv_tipo_movimiento_motor_integration.py` | Espejo |
| `test_inv_almacen_motor_integration.py` | Espejo |
| `test_inv_producto_motor_integration.py` | Espejo + `codigo_sku` |
| `test_inv_movimiento_motor_integration.py` | AUTO_REQUIRED + UoW con detalle si aplica |
| `test_inv_inventario_fisico_motor_integration.py` | AUTO_REQUIRED |
| `test_inv_br_imm_update_immutability.py` | Parametrizado × entidades F1/F2 |

### 3.3 Casos mínimos por entidad F1 (copiar asserts ORG)

| ID | Caso |
|----|------|
| INV-C01 | Create sin código → allocate → código en insert |
| INV-C02 | Create manual → accept |
| INV-C03 | Manual duplicado → 409; allocate no llamado |
| INV-C04 | cfg missing → NotFound; no insert |
| INV-C05 | Un solo `session.begin` |
| INV-U01 | Update solo nombre → código intacto; `"codigo" not in payload` |
| INV-U02 | Schema Update sin campo Motor |
| INV-U03 | Motor / `get_*_by_codigo` no llamados en Update |

### 3.4 Casos F2 adicionales

| ID | Caso |
|----|------|
| INV-D01 | Create sin número → auto |
| INV-D02 | Body con número → ignorado o 422 según decisión de implementación (preferir ignore + allocate; documentar en PR) |
| INV-D03 | Estorno/ajuste → allocate; **no** string timestamp |
| INV-D04 | `procesar` no cambia número |

---

## 4. Riesgos de implementación

| ID | Riesgo | Severidad | Mitigación Blueprint |
|----|--------|-----------|----------------------|
| I-01 | Queries sin dual-path rompen UoW Dedicated | Alta | Paso 1 obligatorio antes de service |
| I-02 | Olvidar `get_*_by_codigo` | Media | Checklist DoR |
| I-03 | Importar `OrgCodigoGenerationService` desde INV | Alta | Prohibido; adapter propio |
| I-04 | Producto: quitar `codigo_barra` por error | Alta | Diff review campo a campo |
| I-05 | Movimiento: allocate fuera de TX con detalle | Alta | Un begin |
| I-06 | Dejar gens timestamp “para después” | Alta | Gate entidad 6/7 no cierra sin reemplazo |
| I-07 | Tocar SequenceCatalog por padding SKU=5 | Alta | Prohibido Baseline |
| I-08 | Update schema con `extra=forbid` rompe FE | Baja | Default ignore extras; FE omitirá luego |
| I-09 | Regresión paginación categoría | Baja | No tocar list/get |
| I-10 | Confundir plantilla con `empresa_service` TENANT | Media | Solo cargo/sucursal EMPRESA |

---

## 5. Parallelismo permitido

| Paralelo OK | Secuencial obligatorio |
|-------------|------------------------|
| Tests de entidad N mientras se documenta N+1 | Adapter antes de cualquier service |
| UM / TipoMov / Almacén tras Categoría verde (PRs separados) | Producto después de Cat+UM si se validan FKs en create |
| OpenAPI snapshot al final de fase F1 y otra vez tras F2 | Estorno junto con Movimiento |

---

*Ready / certificación: [`04_READY_AND_CERTIFICATION.md`](04_READY_AND_CERTIFICATION.md)*
