# INV — Auditoría Funcional de Persistencia

**Fecha:** 2026-06-12  
**Fuente de verdad:** `docs/bd/INV_TABLAS.sql`  
**Alcance contrastado:** tablas físicas (bootstrap V010 + `tables_inv.py`), schemas Pydantic, queries, servicios, endpoints, workflows vigentes.  
**Tipo:** Solo descubrimiento y documentación — sin cambios de código.

---

## 1. Resumen ejecutivo

El módulo INV tiene **10 tablas** definidas en el modelo canónico y **las 10 están implementadas** a nivel de queries, schemas y endpoints. La arquitectura multi-tenant (`cliente_id`) y multi-empresa (`empresa_id` desde sesión JWT) está aplicada de forma consistente en servicios y queries.

### Hallazgos principales

| Área | Estado | Observación |
|------|--------|-------------|
| Maestros (categoría, UM, producto, almacén, tipo movimiento) | **Implementados** | CRUD completo + soft delete (`es_activo=0`) + reactivar |
| Stock (`inv_stock`) | **Parcial** | Lectura y alertas OK; escritura directa **deprecated** pero aún expuesta; mutación real solo vía `procesar_movimiento` (cantidad) |
| Movimientos | **Implementado con brechas** | Workflow borrador → autorizado → procesado → anulado operativo; **costo de stock no se actualiza** al procesar |
| Inventario físico | **Implementado con brechas** | Workflow en_proceso → finalizado → ajustado operativo; `cantidad_sistema` manual; `valor_diferencias` nunca calculado |
| Auditoría empresarial | **Sub implementada** | `usuario_creacion_id` / `usuario_actualizacion_id` casi nunca se pueblan desde sesión |
| Columnas computadas BD | **Correctas en BD, ausentes en ORM** | `cantidad_disponible`, `valor_total`, `costo_total`, `diferencia`, `valor_diferencia` existen en SQL pero no en `tables_inv.py` |
| Integración futura (PUR, SLS, MFG, FIN, CST) | **Preparado en esquema, no en runtime** | Campos de referencia, costeo contable y reservas sin lógica activa |

### Severidad agregada

- **Crítico (4):** costo de stock ignorado al procesar; stock editable por API deprecated; sin reversión de stock al anular procesado; auditoría de usuario inexistente en altas/ediciones.
- **Medio (8):** campos de workflow no automáticos (`cantidad_sistema`, `valor_diferencias`, fechas stock); validaciones FK incompletas; totales parciales en aprobación IF.
- **Menor (6):** jerarquía categoría manual; campos WMS/lotes/series sin enforcement; discrepancia nullable `moneda_id` en ORM vs NOT NULL en SQL.

---

## 2. Inventario de tablas (Fase 1)

| Tabla | Propósito funcional | Flujo de negocio | Implementada | Parcial | No usada |
|-------|---------------------|------------------|:------------:|:-------:|:--------:|
| `inv_categoria_producto` | Clasificación jerárquica de productos | Maestro → producto → reportes/CST | ✓ | | |
| `inv_unidad_medida` | Catálogo UM y conversiones | Maestro → producto, movimiento detalle, PUR/SLS (futuro) | ✓ | | |
| `inv_producto` | Catálogo maestro de artículos | Base de stock, movimientos, IF, PUR/SLS/MFG | ✓ | | |
| `inv_almacen` | Ubicaciones físicas de inventario | Stock, movimientos, inventario físico | ✓ | | |
| `inv_stock` | Saldo analítico producto×almacén | Consulta; actualización vía movimiento procesado | | ✓ | |
| `inv_tipo_movimiento` | Catálogo de clases de movimiento | Movimiento, kardex, aprobación IF | ✓ | | |
| `inv_movimiento` | Cabecera transaccional de inventario | Entradas/salidas/transferencias/ajustes | ✓ | | |
| `inv_movimiento_detalle` | Líneas de movimiento | Proceso de stock, kardex | ✓ | | |
| `inv_inventario_fisico` | Cabecera de conteo físico | Conteo → finalizar → aprobar → movimiento ajuste | ✓ | | |
| `inv_inventario_fisico_detalle` | Líneas de conteo | Comparación sistema vs físico | ✓ | | |

### Mapa de implementación por capa

| Tabla | Queries | Schemas | Servicio | Endpoints activos | Endpoints deprecated |
|-------|---------|---------|----------|-------------------|---------------------|
| `inv_categoria_producto` | `categoria_queries` | Create/Update/Read | `categoria_service` | CRUD + delete + reactivar | — |
| `inv_unidad_medida` | `unidad_medida_queries` | Create/Update/Read | `unidad_medida_service` | CRUD + delete + reactivar | — |
| `inv_producto` | `producto_queries` | Create/Update/Read | `producto_service` | CRUD + delete + reactivar | — |
| `inv_almacen` | `almacen_queries` | Create/Update/Read | `almacen_service` | CRUD + delete + reactivar | — |
| `inv_stock` | `stock_queries` | Create/Update/Read | `stock_service` + `movimiento_proceso_service` | GET, alertas | POST/PUT directo |
| `inv_tipo_movimiento` | `tipo_movimiento_queries` | Create/Update/Read | `tipo_movimiento_service` | CRUD + delete + reactivar | — |
| `inv_movimiento` | `movimiento_queries` | Create/Update/Read + ConDetalle | `movimiento_service` + proceso | CRUD + con-detalle + proceso | — |
| `inv_movimiento_detalle` | `movimiento_detalle_queries` | Create/Update/Read + embebido | `movimiento_service` + detalle | Embebido en movimiento | POST/PUT standalone |
| `inv_inventario_fisico` | `inventario_fisico_queries` | Create/Update/Read + ConDetalle | `inventario_fisico_service` + aprobación | CRUD + con-detalle + finalizar/anular/aprobar | — |
| `inv_inventario_fisico_detalle` | `inventario_fisico_detalle_queries` | Create/Update/Read + embebido | `inventario_fisico_service` + detalle | Embebido en IF | POST/PUT standalone |

**Consulta derivada (no tabla):** Kardex — lectura sobre `inv_movimiento` + `inv_movimiento_detalle` (`kardex_queries`, `kardex_service`).

---

## 3. Inventario de campos por tabla

Conteo de columnas según `INV_TABLAS.sql`:

| Tabla | Columnas físicas | En `tables_inv.py` | En schemas Read | Columnas solo BD (computadas) |
|-------|-----------------|-------------------|-----------------|------------------------------|
| `inv_categoria_producto` | 16 | 16 | 16 | — |
| `inv_unidad_medida` | 15 | 15 | 15 | — |
| `inv_producto` | 70 | 70 | 70 | — |
| `inv_almacen` | 22 | 22 | 22 | — |
| `inv_stock` | 19 | 17 | 19 (Read incluye computadas) | `cantidad_disponible`, `valor_total` |
| `inv_tipo_movimiento` | 18 | 18 | 18 | — |
| `inv_movimiento` | 31 | 31 | 31 | — |
| `inv_movimiento_detalle` | 16 | 15 | 16 (Read incluye `costo_total`) | `costo_total` |
| `inv_inventario_fisico` | 22 | 22 | 22 | — |
| `inv_inventario_fisico_detalle` | 19 | 17 | 19 (Read incluye computadas) | `diferencia`, `valor_diferencia` |

**Nota ORM vs SQL:** `InvMovimientoTable.moneda_id` es `nullable=True` en SQLAlchemy pero `NOT NULL` en `INV_TABLAS.sql`.

---

## 4. Matriz de clasificación funcional de campos (Fase 2)

**Leyenda de clasificación:**

| Código | Significado |
|--------|-------------|
| **A** | Obligatorio — requerido para validez del proceso |
| **B** | Auditoría — trazabilidad histórica |
| **C** | Derivable — recalculable desde otros datos |
| **D** | Contextual — aplica solo en escenarios específicos |
| **E** | Futuro — diseñado, sin uso runtime observable |
| **F** | Obsoleto — sin uso real o contradice el workflow vigente |

### 4.1 `inv_categoria_producto`

| Campo | Tipo | Clas. | Justificación |
|-------|------|-------|---------------|
| `categoria_id` | UNIQUEIDENTIFIER PK | A | Identificador |
| `cliente_id` | UNIQUEIDENTIFIER | A | Scope tenant — sesión |
| `empresa_id` | UNIQUEIDENTIFIER | A | Scope empresa — sesión |
| `codigo` | NVARCHAR(20) | A | Unicidad operativa |
| `nombre` | NVARCHAR(100) | A | Identificación |
| `descripcion` | NVARCHAR(255) | D | Opcional |
| `categoria_padre_id` | UNIQUEIDENTIFIER | D | Solo si jerarquía |
| `nivel` | INT | C | Derivable de padre |
| `ruta_jerarquica` | NVARCHAR(500) | C | Derivable de árbol |
| `cuenta_contable_inventario` | NVARCHAR(20) | E | FIN/CST no integrado |
| `cuenta_contable_costo_venta` | NVARCHAR(20) | E | FIN/CST no integrado |
| `metodo_costeo_defecto` | NVARCHAR(20) | D | Herencia a producto |
| `es_activo` | BIT | A | Soft delete |
| `fecha_creacion` | DATETIME | B | Default BD |
| `fecha_actualizacion` | DATETIME | B | Query layer en UPDATE |
| `usuario_creacion_id` | UNIQUEIDENTIFIER | B | **Nunca poblado** |

### 4.2 `inv_unidad_medida`

| Campo | Tipo | Clas. | Justificación |
|-------|------|-------|---------------|
| `unidad_medida_id` | PK | A | Identificador |
| `cliente_id` | UNIQUEIDENTIFIER | A | Tenant |
| `empresa_id` | UNIQUEIDENTIFIER | A | Empresa |
| `codigo` | NVARCHAR(10) | A | Unicidad |
| `nombre` | NVARCHAR(50) | A | Display |
| `simbolo` | NVARCHAR(10) | D | UI/reportes |
| `tipo_unidad` | NVARCHAR(20) | A | Clasificación conversión |
| `es_unidad_base` | BIT | D | Conversiones |
| `factor_conversion_base` | DECIMAL | D | Conversiones |
| `decimales_permitidos` | INT | D | Validación cantidades |
| `es_activo` | BIT | A | Soft delete |
| `fecha_creacion` | DATETIME | B | Default BD |
| `fecha_actualizacion` | DATETIME | B | Auto en UPDATE query |
| `usuario_creacion_id` | UNIQUEIDENTIFIER | B | **Nunca poblado** |

### 4.3 `inv_producto` (agrupado por dominio)

| Campo | Tipo | Clas. | Justificación |
|-------|------|-------|---------------|
| `producto_id`, `cliente_id`, `empresa_id` | UUID | A | Identidad y scope |
| `codigo_sku`, `nombre`, `tipo_producto` | NVARCHAR | A | Identificación mínima |
| `unidad_medida_base_id`, `moneda_costo`, `moneda_venta` | UUID | A | FK obligatorias |
| `codigo_barra`, `codigo_interno`, `codigo_fabricante` | NVARCHAR | D | Identificación alternativa |
| `nombre_corto`, `descripcion`, `descripcion_corta` | NVARCHAR | D | Comercial |
| `categoria_id` | UUID | D | Clasificación — validada en servicio |
| `subcategoria_id` | UUID | D | **Sin validación FK** en servicio |
| `marca`, `modelo`, `linea_producto` | NVARCHAR | D | Atributos |
| `subtipo_producto` | NVARCHAR | D | Industria |
| `unidad_medida_compra_id`, `unidad_medida_venta_id` | UUID | D | Multi-UM |
| `factor_conversion_compra`, `factor_conversion_venta` | DECIMAL | D | Conversión — no auto-aplicada en movimiento |
| `peso_kg`, `volumen_m3`, `largo_cm`, `ancho_cm`, `alto_cm` | DECIMAL | D | Logística |
| `color`, `talla` | NVARCHAR | D | Retail |
| `atributos_personalizados`, `especificaciones_tecnicas` | NVARCHAR(MAX) | D | JSON flexible |
| `maneja_inventario` | BIT | A | Control stock |
| `maneja_lotes`, `maneja_series`, `maneja_vencimiento` | BIT | D | **Flags sin enforcement** en movimiento/IF |
| `dias_vida_util`, `requiere_refrigeracion`, `es_perecible` | diversos | D/E | Cadena frío — sin lógica |
| `stock_minimo`, `stock_maximo`, `punto_reorden` | DECIMAL | D | Alertas a nivel producto |
| `es_comprable`, `tiempo_entrega_dias`, `cantidad_minima_compra`, `multiplo_compra` | diversos | E | PUR no integrado |
| `es_vendible`, `requiere_autorizacion_venta` | BIT | E | SLS no integrado |
| `es_fabricable`, `tiene_lista_materiales` | BIT | E | MFG no integrado |
| `metodo_costeo` | NVARCHAR | D | CST — no aplicado en procesar |
| `costo_estandar`, `costo_ultima_compra`, `costo_promedio` | DECIMAL | C/E | Costos — no actualizados por movimiento |
| `precio_base_venta`, `afecto_igv`, `porcentaje_igv` | diversos | E | PRC — maestro comercial |
| `codigo_sunat`, `tipo_afectacion_igv` | NVARCHAR | E | TAX/Facturación |
| `imagen_principal_url`, `imagenes_adicionales`, `ficha_tecnica_url` | NVARCHAR | D | Assets |
| `proveedor_habitual_id` | UUID | E | PUR — sin FK validation |
| `estado`, `es_activo` | NVARCHAR/BIT | A | Ciclo de vida |
| `fecha_creacion`, `fecha_actualizacion` | DATETIME | B | Query auto en UPDATE |
| `usuario_creacion_id`, `usuario_actualizacion_id` | UUID | B | **Nunca poblados** |
| `observaciones` | NVARCHAR(MAX) | D | Texto libre |

### 4.4 `inv_almacen`

| Campo | Tipo | Clas. | Justificación |
|-------|------|-------|---------------|
| `almacen_id`, `cliente_id`, `empresa_id` | UUID | A | Identidad y scope |
| `codigo`, `nombre`, `tipo_almacen` | NVARCHAR | A | Identificación |
| `sucursal_id` | UUID | D | Vinculación ORG — opcional |
| `descripcion`, `direccion` | NVARCHAR | D | Metadata |
| `responsable_usuario_id`, `responsable_nombre` | UUID/NVARCHAR | D | **Manual** — no desde sesión |
| `es_almacen_principal` | BIT | D | Configuración |
| `permite_ventas`, `permite_compras`, `permite_produccion` | BIT | D/E | Sin enforcement en movimiento |
| `capacidad_m3`, `capacidad_kg`, `capacidad_unidades` | diversos | E | WMS — sin validación |
| `centro_costo_id` | UUID | E | FIN — sin uso |
| `es_activo` | BIT | A | Soft delete |
| `fecha_creacion`, `fecha_actualizacion` | DATETIME | B | Query layer |
| `usuario_creacion_id` | UUID | B | **Nunca poblado** |

### 4.5 `inv_stock`

| Campo | Tipo | Clas. | Justificación |
|-------|------|-------|---------------|
| `stock_id`, `cliente_id`, `empresa_id`, `producto_id`, `almacen_id` | UUID | A | Clave natural UQ(prod,alm) |
| `cantidad_actual` | DECIMAL | A | Saldo físico — mutado por `procesar_movimiento` |
| `cantidad_reservada` | DECIMAL | E | Reservas SLS/MFG — **nunca actualizado** |
| `cantidad_disponible` | COMPUTED | C | BD: actual − reservada |
| `cantidad_transito` | DECIMAL | E | PUR — **nunca actualizado** |
| `costo_promedio` | DECIMAL | A/C | Debería actualizarse al procesar — **no ocurre** |
| `valor_total` | COMPUTED | C | BD: actual × costo_promedio |
| `moneda_id` | UUID | A | Moneda del saldo |
| `stock_minimo`, `stock_maximo`, `punto_reorden` | DECIMAL | D | Override por almacén — alertas |
| `ubicacion_almacen` | NVARCHAR | D | WMS |
| `fecha_ultimo_movimiento` | DATETIME | B | Poblado en `procesar_movimiento` |
| `fecha_ultima_compra`, `fecha_ultima_venta` | DATETIME | E | **Nunca pobladas** |
| `fecha_actualizacion` | DATETIME | B | Auto en UPDATE |

### 4.6 `inv_tipo_movimiento`

| Campo | Tipo | Clas. | Justificación |
|-------|------|-------|---------------|
| `tipo_movimiento_id`, `cliente_id`, `empresa_id` | UUID | A | Identidad |
| `codigo`, `nombre`, `clase_movimiento` | NVARCHAR | A | `clase_movimiento` dirige delta stock |
| `descripcion` | NVARCHAR | D | Metadata |
| `afecta_costo` | BIT | A | **Ignorado** en `procesar_movimiento` |
| `requiere_autorizacion` | BIT | A | Validado en proceso |
| `genera_asiento_contable` | BIT | E | FIN no integrado |
| `cuenta_contable_debito`, `cuenta_contable_credito` | NVARCHAR | E | FIN |
| `requiere_documento_referencia`, `tipo_documento_referencia` | BIT/NVARCHAR | E | Sin validación |
| `es_activo`, `es_tipo_sistema` | BIT | A/D | Catálogo |
| `fecha_creacion`, `fecha_actualizacion` | DATETIME | B | Query layer |
| `usuario_creacion_id` | UUID | B | **Nunca poblado** |

### 4.7 `inv_movimiento`

| Campo | Tipo | Clas. | Justificación |
|-------|------|-------|---------------|
| `movimiento_id`, `cliente_id`, `empresa_id` | UUID | A | Identidad |
| `numero_movimiento` | NVARCHAR(20) | A | Correlativo único |
| `tipo_movimiento_id` | UUID | A | Clase y reglas |
| `fecha_movimiento`, `fecha_contable` | DATETIME/DATE | A | Contabilización |
| `almacen_origen_id`, `almacen_destino_id` | UUID | D | Según clase |
| `modulo_origen`, `documento_referencia_*` | NVARCHAR/UUID | D | Trazabilidad cross-módulo |
| `tercero_tipo`, `tercero_id`, `tercero_nombre` | diversos | D | PUR/SLS |
| `total_items`, `total_cantidad`, `total_costo` | diversos | C | Recalculados en con-detalle; parcial en aprobación IF |
| `moneda_id` | UUID | A | Resuelto desde body o PEN |
| `estado` | NVARCHAR | A | Máquina de estados |
| `requiere_autorizacion` | BIT | D | Puede venir de tipo o body |
| `autorizado_por_usuario_id`, `fecha_autorizacion` | UUID/DATETIME | B | Workflow autorizar |
| `observaciones`, `motivo_anulacion` | NVARCHAR | D | Texto |
| `centro_costo_id` | UUID | E | FIN |
| `fecha_creacion` | DATETIME | B | Default BD |
| `fecha_actualizacion` | DATETIME | B | Servicio/query |
| `fecha_procesado` | DATETIME | B | Workflow procesar |
| `usuario_creacion_id` | UUID | B | Solo en aprobación IF → movimiento |
| `usuario_procesado_id` | UUID | B | Workflow procesar — desde sesión |

### 4.8 `inv_movimiento_detalle`

| Campo | Tipo | Clas. | Justificación |
|-------|------|-------|---------------|
| `movimiento_detalle_id`, `cliente_id`, `empresa_id`, `movimiento_id`, `producto_id` | UUID | A | Identidad |
| `cantidad`, `unidad_medida_id`, `cantidad_base` | DECIMAL/UUID | A | `cantidad_base` usada en proceso |
| `costo_unitario` | DECIMAL | A | Afecta `total_costo` cabecera — no stock |
| `costo_total` | COMPUTED | C | BD |
| `moneda_id` | UUID | A | Línea |
| `lote`, `fecha_vencimiento`, `numero_serie` | diversos | D | **Sin validación** vs flags producto |
| `ubicacion_almacen` | NVARCHAR | D | WMS |
| `observaciones` | NVARCHAR | D | Texto |
| `fecha_creacion` | DATETIME | B | Default BD |

### 4.9 `inv_inventario_fisico`

| Campo | Tipo | Clas. | Justificación |
|-------|------|-------|---------------|
| `inventario_fisico_id`, `cliente_id`, `empresa_id` | UUID | A | Identidad |
| `numero_inventario`, `fecha_inventario`, `almacen_id`, `tipo_inventario` | diversos | A | Cabecera mínima |
| `descripcion` | NVARCHAR | D | Metadata |
| `categoria_id`, `ubicacion_almacen` | UUID/NVARCHAR | D | Filtro selectivo — sin auto-filtrado en detalle |
| `estado` | NVARCHAR | A | Máquina de estados |
| `supervisor_usuario_id`, `supervisor_nombre` | UUID/NVARCHAR | D/B | **Manual** — no desde sesión |
| `total_productos_contados`, `total_diferencias` | INT | C | Recalculados en aprobar |
| `valor_diferencias` | DECIMAL | C | **Nunca calculado** |
| `movimiento_ajuste_id` | UUID | B | Poblado en aprobar |
| `observaciones` | NVARCHAR | D | Texto |
| `fecha_creacion` | DATETIME | B | Default BD |
| `fecha_finalizacion` | DATETIME | B | Finalizar + sobrescrito en aprobar |
| `fecha_ajuste` | DATETIME | B | Aprobar |
| `usuario_creacion_id` | UUID | B | **Nunca poblado** |

### 4.10 `inv_inventario_fisico_detalle`

| Campo | Tipo | Clas. | Justificación |
|-------|------|-------|---------------|
| `inventario_fisico_detalle_id`, `cliente_id`, `empresa_id`, `inventario_fisico_id`, `producto_id` | UUID | A | Identidad |
| `cantidad_sistema` | DECIMAL | A | Debería venir de stock — **manual hoy** |
| `cantidad_contada` | DECIMAL | A | Conteo físico |
| `diferencia` | COMPUTED | C | BD |
| `lote`, `fecha_vencimiento` | diversos | D | Sin enforcement |
| `ubicacion_almacen` | NVARCHAR | D | WMS |
| `costo_unitario` | DECIMAL | A | Usado en ajuste y valor_diferencia |
| `valor_diferencia` | COMPUTED | C | BD — no agregado a cabecera |
| `estado_conteo` | NVARCHAR | D | Default `pendiente` — sin transiciones automáticas |
| `contador_usuario_id`, `contador_nombre`, `fecha_conteo` | diversos | B/D | **Manual** — no desde sesión al contar |
| `observaciones`, `motivo_diferencia` | NVARCHAR | D | Texto |
| `fecha_creacion` | DATETIME | B | Default BD |

---

## 5. Matriz de persistencia real (Fase 3)

Valores: **Sí** | **Parcialmente** | **Nunca**

### 5.1 Campos transversales (todas las tablas maestras)

| Campo | Se llena | Dónde | Cuándo |
|-------|----------|-------|--------|
| `cliente_id` | Sí | Todas las queries INSERT | Siempre desde `current_user.cliente_id` |
| `empresa_id` | Sí | Servicios create | Body validado vs sesión JWT |
| `fecha_creacion` | Parcialmente | Default SQL `GETDATE()` | No explícito en servicios |
| `fecha_actualizacion` | Parcialmente | `update_*_queries` (maestros) | Solo en UPDATE vía query layer |
| `usuario_creacion_id` | Nunca | — | No asignado en ningún CRUD maestro |
| `usuario_actualizacion_id` | Nunca | — | Solo existe en `inv_producto` |

### 5.2 `inv_stock` — campos críticos

| Campo | Se llena | Dónde | Cuándo |
|-------|----------|-------|--------|
| `cantidad_actual` | Sí | `procesar_movimiento_servicio` | Procesar movimiento (±delta) |
| `cantidad_actual` | Parcialmente | `create_stock_servicio` (deprecated) | POST directo — anti-patrón |
| `costo_promedio` | Parcialmente | `create_stock_servicio` | Solo en alta manual; **0 en auto-create** |
| `costo_promedio` | Nunca | `procesar_movimiento` | No actualiza aunque `afecta_costo=1` |
| `cantidad_reservada` | Nunca | — | Sin módulo reservas |
| `cantidad_transito` | Nunca | — | Sin PUR |
| `fecha_ultimo_movimiento` | Sí | `procesar_movimiento` | Cada procesamiento |
| `fecha_ultima_compra` | Nunca | — | — |
| `fecha_ultima_venta` | Nunca | — | — |
| `cantidad_disponible` | Sí | BD computed | Automático SQL Server |
| `valor_total` | Sí | BD computed | Automático SQL Server |

### 5.3 `inv_movimiento` — workflow

| Campo | Se llena | Dónde | Cuándo |
|-------|----------|-------|--------|
| `estado` | Sí | create / autorizar / procesar / anular | Transiciones workflow |
| `total_items`, `total_cantidad`, `total_costo` | Sí | `create_movimiento_con_detalles` | Al crear con detalle |
| `total_costo` | Parcialmente | Aprobación IF | No incluye costo en totales cabecera |
| `usuario_procesado_id` | Sí | `procesar_movimiento` | Desde `current_user` |
| `autorizado_por_usuario_id` | Sí | `autorizar_movimiento` | Desde `current_user` |
| `usuario_creacion_id` | Parcialmente | `aprobar_inventario_fisico` | Solo movimiento generado por IF |
| `usuario_creacion_id` | Nunca | `create_movimiento*` | Alta manual |

### 5.4 `inv_inventario_fisico` — workflow

| Campo | Se llena | Dónde | Cuándo |
|-------|----------|-------|--------|
| `estado` | Sí | create / finalizar / anular / aprobar | Transiciones |
| `fecha_finalizacion` | Sí | `finalizar_inventario_fisico` | Al finalizar conteo |
| `fecha_finalizacion` | Parcialmente | `aprobar_inventario_fisico` | **Sobrescribe** con `now` en aprobar |
| `fecha_ajuste` | Sí | `aprobar_inventario_fisico` | Al ajustar |
| `movimiento_ajuste_id` | Sí | `aprobar_inventario_fisico` | Al ajustar |
| `total_productos_contados` | Parcialmente | `aprobar_inventario_fisico` | Solo en aprobar, no en finalizar |
| `total_diferencias` | Parcialmente | `aprobar_inventario_fisico` | Cuenta líneas con diff ≠ 0 |
| `valor_diferencias` | Nunca | — | Campo expuesto en schema pero sin cálculo |
| `supervisor_usuario_id` | Parcialmente | Body create/update | Manual — no sesión |
| `cantidad_sistema` (detalle) | Parcialmente | Body cliente | **No se lee de `inv_stock`** |

---

## 6. Brechas funcionales (Fase 4)

| Campo / Comportamiento | Severidad | Problema |
|------------------------|-----------|----------|
| `inv_stock.costo_promedio` al procesar | **Crítico** | `procesar_movimiento` solo muta `cantidad_actual`; ignora `afecta_costo` del tipo y `costo_unitario` del detalle |
| POST/PUT `/stock` (deprecated) | **Crítico** | Permite alterar tabla derivada fuera del workflow transaccional |
| Anular movimiento procesado | **Crítico** | Bloqueado sin reversión — stock queda inconsistente si se anula fuera del sistema |
| `usuario_creacion_id` / `usuario_actualizacion_id` | **Crítico** | Auditoría empresarial inexistente en altas/ediciones de maestros y movimientos manuales |
| `cantidad_sistema` en IF detalle | **Medio** | Debería poblarse desde `inv_stock` al crear líneas; hoy es responsabilidad del cliente |
| `valor_diferencias` en IF cabecera | **Medio** | Debería ser Σ\|valor_diferencia\| al finalizar/aprobar; permanece en 0 |
| `total_costo` en movimiento IF | **Medio** | Aprobación no calcula costo total del movimiento de ajuste |
| `fecha_finalizacion` sobrescrita en aprobar | **Medio** | Pierde timestamp real de finalización del conteo |
| `contador_usuario_id` / `supervisor_usuario_id` | **Medio** | Deberían provenir de sesión en operaciones de conteo/aprobación |
| `cantidad_reservada`, `cantidad_transito` | **Medio** | Diseñados para SLS/PUR — sin población ni validación de disponible real |
| Flags `maneja_lotes/series/vencimiento` | **Medio** | Producto los expone; movimiento/IF no exigen lote/serie cuando aplica |
| `subcategoria_id` en producto | **Medio** | Sin validación de existencia ni coherencia con `categoria_id` |
| `nivel`, `ruta_jerarquica` en categoría | **Menor** | Deberían ser automáticos al asignar padre |
| `fecha_actualizacion` en IF con-detalle update | **Menor** | Servicio intenta asignar campo **inexistente** en tabla — filtrado silenciosamente |
| `moneda` en detalle movimiento (insert) | **Menor** | Servicio asigna columna inexistente en tabla — ignorada |
| Columnas computadas ausentes en ORM | **Menor** | Lectura depende de `select(Table)` en BD real; alertas calculan disponible en Python |

---

## 7. Workflow — transiciones y campos (Fase 5)

### 7.1 Producto (`inv_producto`)

| Transición | Endpoint | Campos que deberían poblarse | Campos que se pueblan | Faltantes |
|------------|----------|------------------------------|----------------------|-----------|
| **Crear** | POST `/productos` | SKU, nombre, tipo, UM base, monedas, tenant | Body completo + `cliente_id` PK | `usuario_creacion_id` |
| **Actualizar** | PUT `/productos/{id}` | Campos enviados + auditoría | Body parcial + `fecha_actualizacion` | `usuario_actualizacion_id` |
| **Desactivar** | DELETE `/productos/{id}` | `es_activo=0` | Sí | — |
| **Reactivar** | POST `.../reactivar` | `es_activo=1` | Sí | — |
| Finalizar / Aprobar / Anular | N/A | — | — | — |

### 7.2 Almacén (`inv_almacen`)

| Transición | Campos esperados | Poblados | Faltantes |
|------------|------------------|----------|-----------|
| **Crear** | codigo, nombre, tipo, empresa | Body + scope | `usuario_creacion_id` |
| **Actualizar** | parcial | Body + `fecha_actualizacion` | auditoría usuario |
| **Desactivar/Reactivar** | `es_activo` | Sí | — |

### 7.3 Stock (`inv_stock`) — tabla derivada

| Transición | Campos esperados | Poblados | Faltantes |
|------------|------------------|----------|-----------|
| **Crear** (anti-patrón) | producto, almacén, cantidades | Deprecated POST | No debería existir escritura directa |
| **Actualizar** (anti-patrón) | cantidades, costos | Deprecated PUT | — |
| **Procesar movimiento** | `cantidad_actual` ±δ, `fecha_ultimo_movimiento` | Sí (cantidad) | `costo_promedio`, fechas compra/venta |
| **Consulta** | todos | GET, alertas | `valor_total` solo si BD devuelve computed |

### 7.4 Movimiento (`inv_movimiento` + detalle)

```
borrador ──autorizar──► autorizado ──procesar──► procesado
    │                      │                        │
    └──────anular──────────┴───────anular──────────┘ (bloqueado si procesado)
```

| Transición | Endpoint | Campos workflow | Poblados | Faltantes |
|------------|----------|-----------------|----------|-----------|
| **Crear** (cabecera) | POST `/movimientos` | estado=borrador, moneda | Body + resolución moneda | `usuario_creacion_id` |
| **Crear con detalle** | POST `/movimientos/con-detalle` | + totales, líneas | Sí (totales calculados) | `usuario_creacion_id` |
| **Actualizar** | PUT (solo borrador) | cabecera ± detalle replace | Sí con guards | auditoría |
| **Autorizar** | POST `.../autorizar` | estado, autorizado_por, fecha_auth | Sí desde sesión | — |
| **Procesar** | POST `.../procesar` | estado, fecha_proc, usuario_proc, stock | Cantidad stock | costo stock, validación lotes |
| **Anular** | POST `.../anular` | estado, motivo | Sí (pre-procesado) | reversión stock si procesado |

### 7.5 Inventario físico (`inv_inventario_fisico` + detalle)

```
en_proceso ──finalizar──► finalizado ──aprobar──► ajustado
     │                         │                      │
     └────────anular───────────┴──────────────────────┘ (bloqueado si ajustado)
```

| Transición | Endpoint | Campos workflow | Poblados | Faltantes |
|------------|----------|-----------------|----------|-----------|
| **Crear** | POST `/inventario-fisico` o `/con-detalle` | estado=en_proceso | Cabecera + líneas opcionales | `usuario_creacion_id`, `cantidad_sistema` auto |
| **Actualizar** | PUT / `con-detalle` | líneas, conteos | Replace detalle si provisto | `contador_*` desde sesión |
| **Finalizar** | POST `.../finalizar` | estado, fecha_finalizacion | Sí — valida contadas NOT NULL | totales resumen |
| **Aprobar** | POST `.../aprobar` | estado, movimiento_ajuste, fechas, totales | Movimiento + procesar + enlace | `valor_diferencias`, `total_costo` mov |
| **Anular** | POST `.../anular` | estado=anulado | Sí (pre-ajustado) | — |

**Flujo canónico vigente (recomendado por implementación):**

1. `POST /inventario-fisico/con-detalle` — crear con líneas (cantidad_sistema manual).
2. `PUT /inventario-fisico/{id}/con-detalle` — registrar conteos (`cantidad_contada`).
3. `POST /inventario-fisico/{id}/finalizar` — cerrar conteo.
4. `POST /inventario-fisico/{id}/aprobar` — genera movimiento ajuste y procesa stock.

---

## 8. Evaluación SaaS moderno (Fase 6)

| Tabla | Evaluación | Justificación |
|-------|------------|---------------|
| `inv_categoria_producto` | **Correcta** | Tenant + empresa + soft delete + unicidad código |
| `inv_unidad_medida` | **Correcta** | Mismo patrón; conversiones preparadas |
| `inv_producto` | **Sobre diseñada** | 70 campos para integraciones futuras (PUR/SLS/MFG/TAX); runtime usa ~30 |
| `inv_almacen` | **Correcta** | Multi-sucursal, flags operativos; capacidad WMS sin uso |
| `inv_stock` | **Sub diseñada** en runtime | Esquema rico (reservas, tránsito, costo); implementación solo cantidad |
| `inv_tipo_movimiento` | **Correcta** | Extensible por empresa; `es_tipo_sistema` para seed |
| `inv_movimiento` | **Correcta** | Documento transaccional completo; referencias cross-módulo |
| `inv_movimiento_detalle` | **Correcta** | Cabecera-detalle V4; lote/serie sin enforcement |
| `inv_inventario_fisico` | **Correcta** | Workflow explícito; totales deberían ser derivados |
| `inv_inventario_fisico_detalle` | **Correcta** | Computed columns en BD; falta auto-snapshot de stock |

### Criterios SaaS evaluados

| Criterio | Calificación | Detalle |
|----------|--------------|---------|
| Multi-tenant | ✅ Fuerte | `cliente_id` forzado en queries, nunca en body para auth |
| Multi-empresa | ✅ Fuerte | `empresa_id` desde JWT; cross-scope → 404 |
| Auditoría empresarial | ⚠️ Débil | Timestamps parciales; usuarios casi nulos |
| Escalabilidad | ✅ Aceptable | Índices alineados; kardex paginable por filtros |
| Integridad transaccional | ⚠️ Media | UoW en con-detalle y aprobación; stock costo fuera de transacción lógica |
| Separación maestro/transaccional/derivado | ⚠️ Media | Stock writable (deprecated); resto OK |

---

## 9. Riesgos

| ID | Riesgo | Impacto | Probabilidad |
|----|--------|---------|--------------|
| R1 | Valorización de inventario incorrecta (costo_promedio=0) | Financiero / reportes CST | Alta — cada procesamiento |
| R2 | Escritura directa de stock vía API deprecated | Integridad cantidades | Media — depende de consumo frontend |
| R3 | Conteo físico con cantidad_sistema desactualizada | Ajustes incorrectos | Alta — flujo actual |
| R4 | Sin trazabilidad de usuario en maestros | Compliance / auditoría | Alta — sistemático |
| R5 | Lotes/series ignorados con productos flaggeados | Trazabilidad regulatoria | Media — industrias reguladas |
| R6 | Anulación post-proceso imposible sin herramienta de reversión | Operaciones bloqueadas | Media |
| R7 | Discrepancia ORM/SQL columnas computadas | Errores al migrar o usar otro driver | Baja |

---

## 10. Recomendaciones (sin implementación)

### 10.1 Persistencia y workflow

1. **Stock solo lectura:** Retirar del contrato activo POST/PUT stock; mantener deprecated hasta migración frontend.
2. **Costo en procesar:** Al procesar, si `afecta_costo=1`, recalcular `costo_promedio` del stock con método definido en producto/tipo (promedio ponderado mínimo).
3. **Snapshot en inventario físico:** Al insertar líneas, leer `inv_stock.cantidad_actual` (y `costo_promedio`) para `cantidad_sistema` / `costo_unitario` automáticos.
4. **Totales IF:** Calcular `valor_diferencias` y totales de cabecera en `finalizar` o `aprobar`.
5. **Auditoría desde sesión:** Poblar `usuario_creacion_id` en CREATE y `usuario_actualizacion_id` en UPDATE de todos los maestros y documentos.

### 10.2 Contratos y modelo

6. Alinear `tables_inv.py` con columnas computadas (solo lectura) para documentación y tipado.
7. Corregir nullable `moneda_id` en ORM vs NOT NULL en SQL canónico.
8. Eliminar asignaciones a columnas inexistentes (`fecha_actualizacion` en IF detalle update, `moneda` en mov detalle).

### 10.3 Validaciones de negocio

9. Enforce lote/serie/vencimiento cuando `maneja_*` del producto es true.
10. Validar `subcategoria_id` ⊆ árbol de `categoria_id`.
11. Auto-calcular `nivel` y `ruta_jerarquica` en categorías.

### 10.4 Integraciones futuras (preparación)

12. Reservar endpoints/eventos para PUR→`cantidad_transito`, SLS→`cantidad_reservada` sin alterar esquema.
13. Documentar que campos FIN (`genera_asiento_contable`, cuentas) están en **fase diseño**.

---

## 11. Plan de corrección priorizado

| Prioridad | Ítem | Esfuerzo estimado | Dependencias |
|-----------|------|-------------------|--------------|
| **P0** | Costo de stock al procesar movimiento | Alto | Definición método costeo |
| **P0** | Deshabilitar escritura stock en producción (solo deprecated) | Bajo | Frontend |
| **P1** | Auditoría usuario en CRUD maestros y movimientos | Medio | Patrón sesión ORG |
| **P1** | Auto `cantidad_sistema` desde stock en IF | Medio | — |
| **P1** | Calcular `valor_diferencias` y `total_costo` en aprobación IF | Medio | P0 costo |
| **P2** | No sobrescribir `fecha_finalizacion` en aprobar | Bajo | — |
| **P2** | `contador_usuario_id` / `supervisor_usuario_id` desde sesión | Bajo | — |
| **P2** | Validación lotes/series según producto | Medio | — |
| **P3** | Jerarquía categoría automática | Bajo | — |
| **P3** | Alinear ORM con columnas computadas | Bajo | — |
| **P3** | Movimiento de reversión para anular procesados | Alto | Diseño contable |

---

## 12. Anexos

### A. Endpoints vigentes por entidad

| Prefijo | Métodos activos | Deprecated |
|---------|-----------------|------------|
| `/categorias` | GET, POST, PUT, DELETE, reactivar | — |
| `/unidades-medida` | GET, POST, PUT, DELETE, reactivar | — |
| `/productos` | GET, POST, PUT, DELETE, reactivar | — |
| `/almacenes` | GET, POST, PUT, DELETE, reactivar | — |
| `/stock` | GET, by-producto-almacen | POST, PUT |
| `/stock/alertas` | GET bajo mínimo | — |
| `/tipos-movimiento` | GET, POST, PUT, DELETE, reactivar | — |
| `/movimientos` | CRUD + con-detalle | — |
| `/movimientos/{id}/procesar\|autorizar\|anular` | POST proceso | — |
| `/movimientos-detalle` | GET | POST, PUT |
| `/inventario-fisico` | CRUD + con-detalle + finalizar + anular | — |
| `/inventario-fisico/{id}/aprobar` | POST | — |
| `/inventario-fisico-detalle` | GET | POST, PUT |
| `/kardex` | GET | — |

### B. Patrón técnico de persistencia

- **Queries:** INSERT/UPDATE dinámicos filtrados por `_COLUMNS` desde `tables_inv.py`.
- **Servicios:** Payload desde Pydantic `model_dump()`; `cliente_id` nunca del body.
- **Transacciones:** `unit_of_work` en operaciones cabecera+detalle y aprobación IF.
- **Columnas computadas:** Mantenidas por SQL Server; aplicación no las escribe.

### C. Archivos fuente revisados

- `docs/bd/INV_TABLAS.sql`
- `app/infrastructure/database/tables_erp/tables_inv.py`
- `app/infrastructure/database/queries/inv/*.py` (11 archivos)
- `app/modules/inv/application/services/*.py` (13 archivos)
- `app/modules/inv/presentation/schemas.py`, `schemas_proceso.py`
- `app/modules/inv/presentation/endpoints*.py` (14 routers)

---

*Documento generado como entregable de auditoría. No incluye cambios de código ni propuestas de parches.*
