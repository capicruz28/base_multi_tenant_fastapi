# AUDITORÍA — Módulo INV (Inventarios y Almacenes)

Repositorio: `base_multi_tenant_fastapi`  
Alcance: **Fase 2** (auditoría de implementación actual vs BD)  
Reglas respetadas: **no cambiar contratos**, **no modificar BD**, **no eliminar código**.

---

## 1) Tablas detectadas (prefijo `inv_`) y tipo

Fuente: `docs/bd/INV_TABLAS.sql`

- **Maestros**
  - `inv_categoria_producto`
  - `inv_unidad_medida`
  - `inv_producto`
  - `inv_almacen`
  - `inv_tipo_movimiento`
- **Transaccionales**
  - `inv_movimiento` (cabecera)
  - `inv_movimiento_detalle` (detalle)
  - `inv_inventario_fisico` (cabecera)
  - `inv_inventario_fisico_detalle` (detalle)
- **Derivadas / analíticas (solo lectura esperada)**
  - `inv_stock` (snapshot de stock actual, con columnas calculadas persistidas)

---

## 2) Endpoints existentes (rutas, métodos, entidad, tenant, RBAC)

Router principal: `app/modules/inv/presentation/endpoints.py`  
Convención observada:

- **Tenant**: `client_id` se toma desde `current_user.cliente_id` y se propaga a services/queries.
- **RBAC**: dependency `require_permission("<modulo>.<recurso>.<accion>")`.
- **Empresa**: varios endpoints aceptan `empresa_id` como filtro; validaciones de pertenencia suelen hacerse en services.

### 2.1 Categorías (`inv_categoria_producto`)

Base path: `/inv/categorias`

- **GET** `` -> `inv.categoria.leer` (**tenant** sí, **RBAC** sí)
- **GET** `/{categoria_id}` -> `inv.categoria.leer` (**tenant** sí, **RBAC** sí)
- **POST** `` -> `inv.categoria.crear` (**tenant** sí, **RBAC** sí)
- **PUT** `/{categoria_id}` -> `inv.categoria.actualizar` (**tenant** sí, **RBAC** sí)

### 2.2 Unidades de medida (`inv_unidad_medida`)

Base path: `/inv/unidades-medida`

- **GET** `` -> `inv.unidad_medida.leer` (**tenant** sí, **RBAC** sí)
- **GET** `/{unidad_medida_id}` -> `inv.unidad_medida.leer` (**tenant** sí, **RBAC** sí)
- **POST** `` -> `inv.unidad_medida.crear` (**tenant** sí, **RBAC** sí)
- **PUT** `/{unidad_medida_id}` -> `inv.unidad_medida.actualizar` (**tenant** sí, **RBAC** sí)

### 2.3 Productos (`inv_producto`)

Base path: `/inv/productos`

- **GET** `` -> `inv.producto.leer` (**tenant** sí, **RBAC** sí)
- **GET** `/{producto_id}` -> `inv.producto.leer` (**tenant** sí, **RBAC** sí)
- **POST** `` -> `inv.producto.crear` (**tenant** sí, **RBAC** sí)
- **PUT** `/{producto_id}` -> `inv.producto.actualizar` (**tenant** sí, **RBAC** sí)

### 2.4 Almacenes (`inv_almacen`)

Base path: `/inv/almacenes`

- **GET** `` -> `inv.almacen.leer` (**tenant** sí, **RBAC** sí)
- **GET** `/{almacen_id}` -> `inv.almacen.leer` (**tenant** sí, **RBAC** sí)
- **POST** `` -> `inv.almacen.crear` (**tenant** sí, **RBAC** sí)
- **PUT** `/{almacen_id}` -> `inv.almacen.actualizar` (**tenant** sí, **RBAC** sí)

### 2.5 Stock (`inv_stock`)

Base path: `/inv/stock`

- **GET** `` -> `inv.stock.leer` (**tenant** sí, **RBAC** sí)
- **GET** `/{stock_id}` -> `inv.stock.leer` (**tenant** sí, **RBAC** sí)
- **GET** `/producto/{producto_id}/almacen/{almacen_id}` -> `inv.stock.leer` (**tenant** sí, **RBAC** sí)
- **POST** `` -> `inv.stock.crear` (**tenant** sí, **RBAC** sí)
- **PUT** `/{stock_id}` -> `inv.stock.actualizar` (**tenant** sí, **RBAC** sí)

### 2.6 Alertas de stock (consulta)

Base path: `/inv/stock/alertas`

- **GET** `` -> `inv.stock.leer` (**tenant** sí, **RBAC** sí)

### 2.7 Tipos de movimiento (`inv_tipo_movimiento`)

Base path: `/inv/tipos-movimiento`

- **GET** `` -> `inv.tipo_movimiento.leer` (**tenant** sí, **RBAC** sí)
- **GET** `/{tipo_movimiento_id}` -> `inv.tipo_movimiento.leer` (**tenant** sí, **RBAC** sí)
- **POST** `` -> `inv.tipo_movimiento.crear` (**tenant** sí, **RBAC** sí)
- **PUT** `/{tipo_movimiento_id}` -> `inv.tipo_movimiento.actualizar` (**tenant** sí, **RBAC** sí)

### 2.8 Movimientos (`inv_movimiento`)

Base path: `/inv/movimientos`

- **GET** `` -> `inv.movimiento.leer` (**tenant** sí, **RBAC** sí)
- **GET** `/{movimiento_id}` -> `inv.movimiento.leer` (**tenant** sí, **RBAC** sí)
- **POST** `` -> `inv.movimiento.crear` (**tenant** sí, **RBAC** sí)
- **PUT** `/{movimiento_id}` -> `inv.movimiento.actualizar` (**tenant** sí, **RBAC** sí)

### 2.9 Movimientos — Detalle (`inv_movimiento_detalle`)

Base path: `/inv/movimientos-detalle`

- **GET** `` -> `inv.movimiento.leer` (**tenant** sí, **RBAC** sí)
- **GET** `/{movimiento_detalle_id}` -> `inv.movimiento.leer` (**tenant** sí, **RBAC** sí)
- **POST** `` -> `inv.movimiento.crear` (**tenant** sí, **RBAC** sí)
- **PUT** `/{movimiento_detalle_id}` -> `inv.movimiento.actualizar` (**tenant** sí, **RBAC** sí)

### 2.10 Movimientos — Proceso

Sin prefix adicional (se incluye directo; rutas bajo `/inv` con path de movimiento).

- **POST** `/movimientos/{movimiento_id}/procesar` -> `inv.movimiento.actualizar` (**tenant** sí, **RBAC** sí)
- **POST** `/movimientos/{movimiento_id}/anular` -> `inv.movimiento.actualizar` (**tenant** sí, **RBAC** sí)

### 2.11 Inventario físico (`inv_inventario_fisico`)

Base path: `/inv/inventario-fisico`

- **GET** `` -> `inv.inventario_fisico.leer` (**tenant** sí, **RBAC** sí)
- **GET** `/{inventario_fisico_id}` -> `inv.inventario_fisico.leer` (**tenant** sí, **RBAC** sí)
- **POST** `` -> `inv.inventario_fisico.crear` (**tenant** sí, **RBAC** sí)
- **PUT** `/{inventario_fisico_id}` -> `inv.inventario_fisico.actualizar` (**tenant** sí, **RBAC** sí)
- **POST** `/{inventario_fisico_id}/aprobar` -> `inv.inventario_fisico.actualizar` (**tenant** sí, **RBAC** sí)

### 2.12 Inventario físico — Detalle (`inv_inventario_fisico_detalle`)

Base path: `/inv/inventario-fisico-detalle`

- **GET** `` -> `inv.inventario_fisico.leer` (**tenant** sí, **RBAC** sí)
- **GET** `/{inventario_fisico_detalle_id}` -> `inv.inventario_fisico.leer` (**tenant** sí, **RBAC** sí)
- **POST** `` -> `inv.inventario_fisico.crear` (**tenant** sí, **RBAC** sí)
- **PUT** `/{inventario_fisico_detalle_id}` -> `inv.inventario_fisico.actualizar` (**tenant** sí, **RBAC** sí)

### 2.13 Kardex (consulta)

Base path: `/inv/kardex`

- **GET** `` -> `inv.movimiento.leer` (**tenant** sí, **RBAC** sí)

---

## 3) Brechas funcionales vs patrón esperado

### 3.1 Tablas MAESTRAS (deberían tener: crear, listar, detalle, actualizar, activar/desactivar)

Estado actual:

- `inv_categoria_producto`: **faltan** endpoints de **baja lógica** (`es_activo=0`) y **reactivar**
- `inv_unidad_medida`: **faltan** endpoints de **baja lógica** y **reactivar**
- `inv_producto`: **faltan** endpoints de **baja lógica** y **reactivar**
- `inv_almacen`: **faltan** endpoints de **baja lógica** y **reactivar**
- `inv_tipo_movimiento`: **faltan** endpoints de **baja lógica** y **reactivar**

Sugerencia de rutas (sin implementar aún):

- `DELETE /inv/<recurso>/{id}` (soft delete: `es_activo = 0`)
- `POST /inv/<recurso>/{id}/reactivar`

### 3.2 Tablas TRANSACCIONALES (patrón: borrador → aprobar → procesar → anular)

Estado actual:

- `inv_movimiento`:
  - **existe**: crear (borrador), actualizar, listar/detalle
  - **existe**: `procesar`, `anular`
  - **falta**: endpoint explícito de **aprobar/autorización** (el esquema de BD incluye campos `requiere_autorizacion`, `autorizado_por_usuario_id`, `fecha_autorizacion`)
- `inv_inventario_fisico`:
  - **existe**: crear, actualizar, listar/detalle
  - **existe**: `aprobar` (proceso)
  - (no se observó endpoint de “anular” explícito; la tabla maneja `estado` incluyendo `anulado`)

### 3.3 Tablas DERIVADAS (solo lectura)

- `inv_stock`:
  - ⚠ **riesgo**: existen endpoints de **POST/PUT** para una tabla que el diseño describe como “stock actual” actualizado por movimientos.
  - ⚠ Además, la tabla tiene columnas calculadas persistidas (`cantidad_disponible`, `valor_total`), lo que suele indicar que es **snapshot/derivada**.
  - **Conclusión**: debería ser **solo lectura**; la escritura directa debería evitarse (mantenerse solo para procesos internos si existieran, no para CRUD público).

---

## 4) Campos faltantes o inconsistencias en schemas (BD vs API)

Fuente principal de schemas: `app/modules/inv/presentation/schemas.py`

Hallazgos de alto impacto:

- **`inv_movimiento.moneda_id` (BD)** vs **`MovimientoCreate/Update.moneda: str` (API)**  
  - En BD: `inv_movimiento.moneda_id UNIQUEIDENTIFIER NOT NULL` (FK a `cat_moneda`)
  - En schema: `MovimientoCreate.moneda: Optional[str] = "PEN"` (y `MovimientoUpdate.moneda`)
  - ⚠ Inconsistencia: el contrato actual del API usa “código de moneda” (string), mientras la BD exige `moneda_id` (UUID).  
  - Esto requiere auditoría adicional en queries/services para ver cómo se traduce (si hay mapeo interno) o si hay bug.

- **`inv_movimiento_detalle.moneda_id` (BD)** vs **`MovimientoDetalleBase.moneda: Optional[str]` (API)**  
  - Mismo patrón: BD usa UUID; schema usa string.

Nota: no se listan aquí todos los campos menores; el foco es en campos que pueden romper persistencia o integridad.

---

## 5) Problemas de tenant o RBAC

- **Tenant (`cliente_id`)**: en los endpoints revisados, **sí** se usa `current_user.cliente_id` y se pasa a servicios/queries.
- **Empresa (`empresa_id`)**: se usa como filtro en lectura; en escritura, se observa patrón de validación por pertenencia en services (ej. movimiento valida empresa vía ORG).
- **RBAC**: todos los endpoints revisados tienen `require_permission(...)` con patrón `inv.<recurso>.<accion>`.
  - Nota: en varios endpoints se separa `get_current_active_user` (para obtener `current_user`) y `require_permission` (para enforcement), lo cual es consistente con el estilo del repo.

---

## 6) Código marcado como obsoleto o incorrecto (NO eliminar)

- **`inv_stock` con POST/PUT**: potencialmente incorrecto para un snapshot derivado “actualizado por movimientos”; revisar si estos endpoints se usan solo para inicialización/migración o si deben restringirse.
- **Schemas de moneda en movimientos/detalle**: riesgo de inconsistencia con BD (`moneda_id` UUID) que puede provocar errores o lógica “implícita” no documentada.

