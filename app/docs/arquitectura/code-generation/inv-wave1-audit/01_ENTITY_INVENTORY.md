# Inventario completo de entidades INV

**Fuente AS-IS:** `app/modules/inv/` · schemas · services · routers  
**Catálogo Motor:** `SequenceCatalog` (congelado)

---

## 1. Entidades operativas con superficie API

| # | Recurso API | Tabla / concepto | Service CREATE | ¿Código/número en Create? | En SequenceCatalog |
|---|-------------|------------------|----------------|---------------------------|-------------------|
| 1 | `/inv/categorias` | `inv_categoria_producto` | `create_categoria_servicio` | `codigo` **required** | ✅ `inv_categoria_producto` |
| 2 | `/inv/unidades-medida` | `inv_unidad_medida` | `create_unidad_medida_servicio` | `codigo` **required** | ✅ `inv_unidad_medida` |
| 3 | `/inv/productos` | `inv_producto` | `create_producto_servicio` | `codigo_sku` **required** | ✅ `inv_producto` |
| 4 | `/inv/almacenes` | `inv_almacen` | `create_almacen_servicio` | `codigo` **required** | ✅ `inv_almacen` |
| 5 | `/inv/tipos-movimiento` | `inv_tipo_movimiento` | `create_tipo_movimiento_servicio` | `codigo` **required** | ✅ `inv_tipo_movimiento` |
| 6 | `/inv/movimientos` | `inv_movimiento` | `create_movimiento_*` | `numero_movimiento` **required** | ✅ `inv_movimiento` |
| 7 | `/inv/inventario-fisico` | `inv_inventario_fisico` | `create_inventario_fisico_*` | `numero_inventario` **required** | ✅ `inv_inventario_fisico` |
| 8 | `/inv/stock` | `inv_stock` | `create_stock_servicio` | Sin código de negocio Motor | ❌ |
| 9 | `/inv/kardex` | vista / líneas kardex | solo lectura | N/A | ❌ |
| 10 | detalle movimiento | `inv_movimiento_detalle` | embebido / deprecated standalone | N/A | ❌ |
| 11 | detalle inv. físico | `inv_inventario_fisico_detalle` | embebido / deprecated | N/A | ❌ |

---

## 2. Campos de código en `inv_producto` (no confundir)

| Campo | ¿Motor F1? | Política F15A | Notas |
|-------|------------|---------------|-------|
| `codigo_sku` | **Sí** | AUTO_DEFAULT | Identidad operativa producto |
| `codigo_barra` | No | MANUAL_ONLY | EAN / GTIN |
| `codigo_interno` | No | MANUAL_ONLY | Alias opcional |
| `codigo_fabricante` | No | EXTERNAL | Part number proveedor |
| `codigo_sunat` | No | EXTERNAL | Catálogo tributario |

---

## 3. Clasificación Motor vs no-Motor

### 3.1 Deben consumir el Motor (Ola 1)

| Entidad | Motivo |
|---------|--------|
| Categoría producto | Maestro F1; UNIQUE empresa; hoy manual obligatorio |
| Unidad de medida | Maestro F1; dependencia de producto |
| Producto (`codigo_sku`) | Maestro núcleo INV; UPDATE aún mutable (gap BR-IMM) |
| Almacén | Maestro F1; FK en stock/movimientos |
| Tipo movimiento | Maestro F1; FK en movimientos |
| Movimiento (`numero_movimiento`) | Documento F2 AUTO_REQUIRED; hoy manual + **gen ad hoc** en estorno |
| Inventario físico (`numero_inventario`) | Documento F2; hoy manual; aprobación genera MOV con timestamp |

### 3.2 NO deben usar el Motor

| Entidad / campo | Por qué |
|-----------------|---------|
| `inv_stock` | Tabla **derivada**; escritura solo por proceso (`inv_stock_write_policy`) |
| Kardex | Consulta / proyección de movimientos |
| Detalles cabecera-detalle | Líneas embebidas; sin correlativo propio de negocio |
| `codigo_barra` / interno / fabricante / sunat | No son secuencias CFG del Motor F1 `codigo_sku` |
| Campos workflow (`estado`, fechas autorización, …) | Enforcement de proceso; no códigos |
| Endpoints detalle standalone deprecated | Fuera de contrato FE moderno |

---

## 4. Estado AS-IS vs Baseline V1

| Entidad Motor | Create código | Update código | Gateway | Anti-patrón |
|---------------|---------------|---------------|---------|-------------|
| 5 maestros | Manual **required** | Editable (producto confirmado; resto típico) | No | Pre-Motor |
| Movimiento | Manual **required** | Presente en Update schema | No | + `gen_numero_movimiento_estorno` timestamp |
| Inv. físico | Manual **required** | `numero_inventario` en Update | No | + `_gen_numero_movimiento` en aprobación |

---

## 5. Dependencias entre entidades INV (orden lógico)

```text
categoria, unidad_medida, tipo_movimiento, almacen
        \________ producto (categoria, UM)
                      \
                       movimiento / inventario_fisico
                            \
                             stock / kardex (derivados)
```

---

*Matriz Motor: [`02_MOTOR_MATRIX.md`](02_MOTOR_MATRIX.md)*
