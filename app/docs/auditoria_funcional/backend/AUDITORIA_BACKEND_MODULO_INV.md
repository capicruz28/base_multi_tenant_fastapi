# Auditoría funcional backend — Módulo INV (Inventarios)

**Fecha:** 2026-03-14  
**Alcance:** Análisis exclusivo. Sin modificación de código.  
**Objetivo:** Verificar cobertura funcional del backend INV frente a documentación oficial y estructura de BD; detectar brechas (GAPs).

---

## 1. Resumen del módulo

El módulo **INV — Gestión de Inventarios** es uno de los módulos base del ERP (paquete Starter según `CATALOGO_MODULOS.md`). Su objetivo es:

- **Control de stock en tiempo real**
- **Múltiples almacenes** (físicos y virtuales)
- **Kardex valorizado**
- **Alertas de stock mínimo**

Según `MENU_NAVEGACION.md` y `MANUAL_USUARIO.md` (sección 2.2), el módulo cubre:

- **Productos:** Catálogo con SKU, código de barras, categoría, precio, atributos personalizados.
- **Categorías:** Organización jerárquica de productos.
- **Unidades de Medida:** UND, KG, MT, LT con factores de conversión.
- **Almacenes:** Configuración de almacenes físicos y virtuales.
- **Consulta de Stock:** Stock actual, reservado y disponible por almacén; alertas mínimo/máximo.
- **Tipos de Movimiento:** Compra, venta, ajuste, transferencia, etc.
- **Movimientos de Inventario:** Entradas, salidas, transferencias; Kardex valorizado.
- **Inventario Físico:** Toma de inventario y ajuste de diferencias.

**Implementación backend detectada:**

- **Router:** `app/modules/inv/presentation/endpoints.py` agrupa sub-routers bajo prefijo `/inv` (incluido en `api.py` como `/api/v1/inv`).
- **Endpoints por recurso:** categorías, unidades-medida, productos, almacenes, stock, tipos-movimiento, movimientos, inventario-fisico.
- **Servicios:** `app/modules/inv/application/services/` (categoria, unidad_medida, producto, almacen, stock, tipo_movimiento, movimiento, inventario_fisico).
- **Queries:** `app/infrastructure/database/queries/inv/` con filtro estricto por `cliente_id`.
- **Modelos BD:** `app/infrastructure/database/tables_erp/tables_inv.py` alineado con `3.- TABLAS_BD_ERP_COMPLETO_FASE4.sql`.

**Conclusión de alto nivel:** La implementación cubre las entidades principales del módulo y mantiene aislamiento por `cliente_id`. Existen brechas importantes en: detalle de movimientos e inventario físico, procesamiento de movimientos (actualización de stock/kardex), permisos RBAC en catálogo y en un endpoint de listado, validación de `empresa_id` frente al cliente, y ausencia de paginación/ordenamiento explícito en varios listados.

---

## 2. Funcionalidades definidas en documentación

### 2.1 CATALOGO_MODULOS.md

- INV — Gestión de Inventarios: control de stock, múltiples almacenes, kardex valorizado, alertas de stock mínimo.

### 2.2 MENU_NAVEGACION.md

| Opción | Descripción |
|--------|-------------|
| Productos | Catálogo con SKU, código de barras, categoría, precio; atributos personalizados (color, talla, composición). |
| Categorías | Organizar productos en categorías/subcategorías. |
| Unidades de Medida | UND, KG, MT, LT con factores de conversión. |
| Almacenes | Configurar almacenes físicos y virtuales. |
| Consulta de Stock | Stock actual, reservado y disponible por almacén; alertas mínimo y máximo. |
| Tipos de Movimiento | Tipos: compra, venta, ajuste, transferencia, etc. |
| Movimientos de Inventario | Registrar entradas, salidas, transferencias; Kardex valorizado automático. |
| Inventario Físico | Toma de inventario y ajuste de diferencias. |

### 2.3 MANUAL_USUARIO.md — 2.2 Módulo INV

- **Paso 1:** Configurar categorías (jerarquía, códigos).
- **Paso 2:** Crear unidades de medida (factores de conversión).
- **Paso 3:** Crear almacenes (tipo, sucursal, responsable, control stock).
- **Paso 4:** Registrar productos (SKU, categoría, tipo, UM, costos, stock min/max, atributos).
- **Paso 5:** Configurar tipos de movimiento (clase, afecta costo).
- **Paso 6:** Stock inicial vía Inventario Físico: crear toma → imprimir conteo → ingresar cantidades contadas → aprobar → genera ajustes.

Flujos esperados:

- Movimientos con **detalle (líneas)** por producto (cantidad, costo, lote, etc.).
- Inventario físico con **detalle por producto** (cantidad sistema vs contada, diferencias, aprobar y generar ajustes).
- **Kardex valorizado** automático al procesar movimientos.

---

## 3. Entidades detectadas en base de datos

Según `3.- TABLAS_BD_ERP_COMPLETO_FASE4.sql`:

| Tabla | Descripción | Relaciones |
|-------|-------------|------------|
| inv_categoria_producto | Categorías jerárquicas | inv_producto.categoria_id |
| inv_unidad_medida | Unidades y conversiones | inv_producto (base, compra, venta) |
| inv_producto | Catálogo maestro | categoria, unidad_medida, proveedor_habitual (PUR) |
| inv_almacen | Almacenes | org_sucursal, org_centro_costo |
| inv_stock | Stock por producto-almacén | inv_producto, inv_almacen |
| inv_tipo_movimiento | Tipos de movimiento | inv_movimiento |
| inv_movimiento | Cabecera de movimientos | tipo_movimiento, almacen_origen/destino |
| inv_movimiento_detalle | Líneas del movimiento | inv_movimiento, inv_producto, inv_unidad_medida |
| inv_inventario_fisico | Cabecera toma física | inv_almacen, inv_categoria_producto |
| inv_inventario_fisico_detalle | Líneas de conteo | inv_inventario_fisico, inv_producto |

Campos relevantes no expuestos o parcialmente cubiertos en API (resumen para sección 8):

- **inv_categoria_producto:** Todos los campos de cabecera están en schemas.
- **inv_producto:** Campos amplios en schemas; `subcategoria_id` existe en BD y en schemas.
- **inv_movimiento:** Cabecera expuesta; **no hay API para inv_movimiento_detalle** (líneas).
- **inv_inventario_fisico:** Cabecera expuesta; **no hay API para inv_inventario_fisico_detalle** (líneas de conteo).
- **inv_stock:** `cantidad_disponible` y `valor_total` son columnas calculadas en BD; se exponen en StockRead.

---

## 4. Implementación actual detectada

### 4.1 Routing

- **api.py:** `api_router.include_router(inv_endpoints.router, prefix="/inv", tags=["INV - Inventarios"])`.
- **endpoints.py (INV):** Incluye 8 sub-routers con prefijos: `/categorias`, `/unidades-medida`, `/productos`, `/almacenes`, `/stock`, `/tipos-movimiento`, `/movimientos`, `/inventario-fisico`.

### 4.2 Capas

- **Presentación:** `endpoints_categorias.py`, `endpoints_unidades_medida.py`, `endpoints_productos.py`, `endpoints_almacenes.py`, `endpoints_stock.py`, `endpoints_tipos_movimiento.py`, `endpoints_movimientos.py`, `endpoints_inventario_fisico.py`.
- **Servicios:** `categoria_service`, `unidad_medida_service`, `producto_service`, `almacen_service`, `stock_service`, `tipo_movimiento_service`, `movimiento_service`, `inventario_fisico_service`.
- **Queries:** `categoria_queries`, `unidad_medida_queries`, `producto_queries`, `almacen_queries`, `stock_queries`, `tipo_movimiento_queries`, `movimiento_queries`, `inventario_fisico_queries`. No existen queries para `inv_movimiento_detalle` ni `inv_inventario_fisico_detalle`.
- **Modelos:** `tables_inv.py` define todas las tablas INV incluidas `InvMovimientoDetalleTable` e `InvInventarioFisicoDetalleTable`, pero no hay capa de aplicación ni endpoints para esos detalles.

### 4.3 Patrones de seguridad

- `client_id` se toma de `current_user.cliente_id` en todos los endpoints; no se acepta en el body.
- Todos los Create incluyen `empresa_id` en el body (obligatorio en schemas); no se ha detectado validación explícita de que `empresa_id` pertenezca al `cliente_id` del usuario.
- Queries: todas las operaciones filtran por `cliente_id`; listados aceptan filtro opcional `empresa_id`.

---

## 5. Endpoints detectados

| Recurso | Método | Ruta | Función | Permiso | Archivo |
|---------|--------|------|--------|---------|---------|
| Categorías | GET | /inv/categorias | listar_categorias | inv.categoria.leer | endpoints_categorias.py |
| Categorías | GET | /inv/categorias/{id} | detalle_categoria | inv.categoria.leer | endpoints_categorias.py |
| Categorías | POST | /inv/categorias | crear_categoria | inv.categoria.crear | endpoints_categorias.py |
| Categorías | PUT | /inv/categorias/{id} | actualizar_categoria | inv.categoria.actualizar | endpoints_categorias.py |
| Unidades medida | GET | /inv/unidades-medida | listar_unidades_medida | inv.unidad_medida.leer | endpoints_unidades_medida.py |
| Unidades medida | GET | /inv/unidades-medida/{id} | detalle_unidad_medida | inv.unidad_medida.leer | endpoints_unidades_medida.py |
| Unidades medida | POST | /inv/unidades-medida | crear_unidad_medida | inv.unidad_medida.crear | endpoints_unidades_medida.py |
| Unidades medida | PUT | /inv/unidades-medida/{id} | actualizar_unidad_medida | inv.unidad_medida.actualizar | endpoints_unidades_medida.py |
| Productos | GET | /inv/productos | listar_productos | inv.producto.leer | endpoints_productos.py |
| Productos | GET | /inv/productos/{id} | detalle_producto | inv.producto.leer | endpoints_productos.py |
| Productos | POST | /inv/productos | crear_producto | inv.producto.crear | endpoints_productos.py |
| Productos | PUT | /inv/productos/{id} | actualizar_producto | inv.producto.actualizar | endpoints_productos.py |
| Almacenes | GET | /inv/almacenes | listar_almacenes | inv.almacen.leer | endpoints_almacenes.py |
| Almacenes | GET | /inv/almacenes/{id} | detalle_almacen | inv.almacen.leer | endpoints_almacenes.py |
| Almacenes | POST | /inv/almacenes | crear_almacen | inv.almacen.crear | endpoints_almacenes.py |
| Almacenes | PUT | /inv/almacenes/{id} | actualizar_almacen | inv.almacen.actualizar | endpoints_almacenes.py |
| Stock | GET | /inv/stock | listar_stocks | inv.stock.leer | endpoints_stock.py |
| Stock | GET | /inv/stock/{id} | detalle_stock | inv.stock.leer | endpoints_stock.py |
| Stock | GET | /inv/stock/producto/{pid}/almacen/{aid} | stock_por_producto_almacen | inv.stock.leer | endpoints_stock.py |
| Stock | POST | /inv/stock | crear_stock | inv.stock.crear | endpoints_stock.py |
| Stock | PUT | /inv/stock/{id} | actualizar_stock | inv.stock.actualizar | endpoints_stock.py |
| Tipos movimiento | GET | /inv/tipos-movimiento | listar_tipos_movimiento | inv.tipo_movimiento.leer | endpoints_tipos_movimiento.py |
| Tipos movimiento | GET | /inv/tipos-movimiento/{id} | detalle_tipo_movimiento | inv.tipo_movimiento.leer | endpoints_tipos_movimiento.py |
| Tipos movimiento | POST | /inv/tipos-movimiento | crear_tipo_movimiento | inv.tipo_movimiento.crear | endpoints_tipos_movimiento.py |
| Tipos movimiento | PUT | /inv/tipos-movimiento/{id} | actualizar_tipo_movimiento | inv.tipo_movimiento.actualizar | endpoints_tipos_movimiento.py |
| Movimientos | GET | /inv/movimientos | listar_movimientos | **(ninguno)** | endpoints_movimientos.py |
| Movimientos | GET | /inv/movimientos/{id} | detalle_movimiento | inv.movimiento.leer | endpoints_movimientos.py |
| Movimientos | POST | /inv/movimientos | crear_movimiento | inv.movimiento.crear | endpoints_movimientos.py |
| Movimientos | PUT | /inv/movimientos/{id} | actualizar_movimiento | inv.movimiento.actualizar | endpoints_movimientos.py |
| Inventario físico | GET | /inv/inventario-fisico | listar_inventarios_fisicos | inv.inventario_fisico.leer | endpoints_inventario_fisico.py |
| Inventario físico | GET | /inv/inventario-fisico/{id} | detalle_inventario_fisico | inv.inventario_fisico.leer | endpoints_inventario_fisico.py |
| Inventario físico | POST | /inv/inventario-fisico | crear_inventario_fisico | inv.inventario_fisico.crear | endpoints_inventario_fisico.py |
| Inventario físico | PUT | /inv/inventario-fisico/{id} | actualizar_inventario_fisico | inv.inventario_fisico.actualizar | endpoints_inventario_fisico.py |

- **Validación cliente_id:** En todos los endpoints se usa `current_user.cliente_id` y se pasa a servicios/queries.
- **Validación empresa_id:** No se valida que el `empresa_id` enviado en el body pertenezca al `cliente_id` del usuario en operaciones de creación/actualización que lo usen.

---

## 6. Matriz funcionalidad vs implementación

| Funcionalidad (doc) | Endpoint / Recurso | Implementación | Estado |
|---------------------|--------------------|----------------|--------|
| Catálogo Productos (CRUD + búsqueda) | GET/POST/PUT /inv/productos | Listar, detalle, crear, actualizar; filtros empresa, categoría, tipo, buscar (nombre/SKU/código barras) | ✔ Implementado |
| Categorías jerárquicas | GET/POST/PUT /inv/categorias | CRUD; filtro empresa, solo_activos | ✔ Implementado |
| Unidades de medida con conversión | GET/POST/PUT /inv/unidades-medida | CRUD; filtro empresa, solo_activos | ✔ Implementado |
| Almacenes físicos/virtuales | GET/POST/PUT /inv/almacenes | CRUD; filtro empresa, sucursal, solo_activos | ✔ Implementado |
| Consulta de stock por almacén/producto | GET /inv/stock, GET por producto/almacén | Listar, detalle, stock por producto+almacén; filtros empresa, producto, almacén | ✔ Implementado |
| Alertas stock mínimo/máximo | Datos en StockRead (stock_minimo, stock_maximo) | Campos expuestos; no hay endpoint específico “alertas” | ⚠ Parcial |
| Tipos de movimiento | GET/POST/PUT /inv/tipos-movimiento | CRUD; filtro empresa, solo_activos | ✔ Implementado |
| Registrar movimientos (entradas/salidas/transferencias) | POST/PUT /inv/movimientos | Solo cabecera; sin líneas (detalle) ni procesamiento que actualice stock | ⚠ Parcial |
| Kardex valorizado | — | No hay procesamiento de movimiento que actualice inv_stock ni kardex | ✖ No implementado |
| Detalle de movimiento (líneas) | — | No existe recurso inv_movimiento_detalle en API | ✖ No implementado |
| Inventario físico (toma y ajuste) | GET/POST/PUT /inv/inventario-fisico | Solo cabecera; sin líneas de conteo ni “aprobar y generar ajustes” | ⚠ Parcial |
| Detalle inventario físico (contado vs sistema) | — | No existe recurso inv_inventario_fisico_detalle en API | ✖ No implementado |
| Aprobar inventario físico y generar ajustes | — | No hay endpoint de aprobación ni generación de movimiento de ajuste | ✖ No implementado |
| Listar movimientos con permiso | GET /inv/movimientos | Falta require_permission en listar_movimientos | ⚠ Parcial |

---

## 7. CRUD funcional por entidad

| Entidad | Crear | Listar | Detalle | Actualizar | Eliminar | Activar/Desactivar |
|---------|-------|--------|---------|------------|----------|--------------------|
| Categoría | ✔ POST | ✔ GET | ✔ GET /{id} | ✔ PUT | ✖ No | ⚠ vía es_activo en PUT |
| Unidad medida | ✔ POST | ✔ GET | ✔ GET /{id} | ✔ PUT | ✖ No | ⚠ vía es_activo en PUT |
| Producto | ✔ POST | ✔ GET | ✔ GET /{id} | ✔ PUT | ✖ No | ⚠ vía es_activo en PUT |
| Almacén | ✔ POST | ✔ GET | ✔ GET /{id} | ✔ PUT | ✖ No | ⚠ vía es_activo en PUT |
| Stock | ✔ POST | ✔ GET | ✔ GET /{id} + por producto/almacén | ✔ PUT | ✖ No | N/A |
| Tipo movimiento | ✔ POST | ✔ GET | ✔ GET /{id} | ✔ PUT | ✖ No | ⚠ vía es_activo en PUT |
| Movimiento | ✔ POST | ✔ GET | ✔ GET /{id} | ✔ PUT | ✖ No | ⚠ vía estado (ej. anulado) en PUT |
| Movimiento detalle | ✖ No | ✖ No | ✖ No | ✖ No | ✖ No | N/A |
| Inventario físico | ✔ POST | ✔ GET | ✔ GET /{id} | ✔ PUT | ✖ No | ⚠ vía estado en PUT |
| Inventario físico detalle | ✖ No | ✖ No | ✖ No | ✖ No | ✖ No | N/A |

- **Eliminar:** En ninguna entidad hay endpoint DELETE; la documentación apunta a baja lógica (es_activo / estado), coherente con el resto del ERP.
- **Operaciones faltantes:** Endpoints para movimiento_detalle e inventario_fisico_detalle (CRUD o al menos lectura/alta); proceso “aprobar inventario físico y generar ajustes”; proceso “procesar movimiento” (actualizar stock/kardex).

---

## 8. Campos faltantes en endpoints

- **Movimiento (cabecera):** Los schemas MovimientoCreate/Update/Read están alineados con la tabla inv_movimiento; no faltan campos de cabecera. Falta exponer el **detalle** (líneas) en el modelo de lectura y en la API.
- **Inventario físico (cabecera):** InventarioFisicoCreate/Update/Read alineados con inv_inventario_fisico. Falta exponer el **detalle** (líneas de conteo).
- **Movimiento detalle (tabla inv_movimiento_detalle):** No expuesto. Campos que deberían estar disponibles para el frontend: movimiento_id, producto_id, cantidad, unidad_medida_id, cantidad_base, costo_unitario, moneda, lote, fecha_vencimiento, numero_serie, ubicacion_almacen, observaciones.
- **Inventario físico detalle (inv_inventario_fisico_detalle):** No expuesto. Campos: inventario_fisico_id, producto_id, cantidad_sistema, cantidad_contada, diferencia (calculada), lote, fecha_vencimiento, ubicacion_almacen, costo_unitario, valor_diferencia, estado_conteo, contador_usuario_id, contador_nombre, fecha_conteo, observaciones, motivo_diferencia.
- **Producto / Categoría / Almacén / etc.:** Los schemas actuales cubren los campos de las tablas correspondientes en el SQL de referencia. No se identifican campos obligatorios para formularios que falten en los schemas existentes.
- **Paginación y ordenamiento:** No hay parámetros `page`, `page_size`, `sort_by`, `order` en ningún listado; todos devuelven listas completas. Para grandes volúmenes (productos, movimientos, stock) se recomienda añadir paginación y ordenamiento.

---

## 9. Endpoints faltantes

| Funcionalidad | Endpoint sugerido | Método | Entidad | Motivo |
|---------------|------------------|--------|---------|--------|
| Detalle de movimiento (líneas) | /inv/movimientos/{movimiento_id}/detalle | GET | inv_movimiento_detalle | Mostrar/editar líneas del movimiento |
| Alta de líneas de movimiento | /inv/movimientos/{movimiento_id}/detalle | POST | inv_movimiento_detalle | Añadir líneas al crear/editar movimiento |
| Actualizar línea de movimiento | /inv/movimientos/{movimiento_id}/detalle/{detalle_id} | PUT | inv_movimiento_detalle | Editar cantidad, costo, lote, etc. |
| Eliminar línea de movimiento | /inv/movimientos/{movimiento_id}/detalle/{detalle_id} | DELETE | inv_movimiento_detalle | Quitar línea (según reglas de negocio) |
| Detalle de inventario físico (conteos) | /inv/inventario-fisico/{id}/detalle | GET | inv_inventario_fisico_detalle | Ver cantidades sistema vs contadas y diferencias |
| Alta/actualización de líneas de conteo | /inv/inventario-fisico/{id}/detalle | POST / PUT | inv_inventario_fisico_detalle | Cargar cantidades contadas por producto |
| Aprobar inventario físico y generar ajustes | /inv/inventario-fisico/{id}/aprobar | POST | inv_inventario_fisico + inv_movimiento | Flujo documentado: generar movimientos de ajuste |
| Procesar movimiento (actualizar stock) | /inv/movimientos/{id}/procesar | POST | inv_movimiento + inv_stock | Kardex valorizado y actualización de inv_stock |
| Anular movimiento | /inv/movimientos/{id}/anular | POST | inv_movimiento | Cambio de estado + eventual reversión de stock |
| Alertas de stock (productos bajo mínimo) | /inv/stock/alertas | GET | inv_stock / inv_producto | Consulta de productos con stock &lt; stock_minimo |
| Kardex por producto/almacén | /inv/kardex | GET | inv_movimiento_detalle + inv_movimiento | Listado valorizado para un producto (y opcionalmente almacén) |

---

## 10. Endpoints incompletos

- **GET /inv/movimientos (listar):** No exige permiso `inv.movimiento.leer`; solo autenticación. Debe protegerse con `require_permission("inv.movimiento.leer")`.
- **Movimientos:** Crear/actualizar solo cabecera; no se pueden enviar ni editar líneas (detalle). El flujo funcional requiere movimientos con ítems para entradas/salidas/transferencias.
- **Inventario físico:** Crear/actualizar solo cabecera; no hay forma de cargar cantidades contadas por producto ni de ejecutar “aprobar y generar ajustes”.
- **Listados (todos):** Sin paginación ni ordenamiento configurable; pueden ser insuficientes para muchos productos, movimientos o líneas de stock.
- **Validación empresa_id:** En todos los Create que reciben `empresa_id` no se valida que la empresa pertenezca al `cliente_id` del usuario; se recomienda validar contra org_empresa (cliente_id, empresa_id) antes de insertar.

---

## 11. Validación multi-tenant

- **Filtro por cliente_id:** Todas las queries usan `cliente_id` pasado desde el contexto (token). No se detecta uso de `cliente_id` desde el body. Correcto.
- **Filtro por empresa_id:** Los listados permiten filtrar por `empresa_id` opcional; las tablas INV tienen `empresa_id` y FK a org_empresa. La BD no fuerza que org_empresa.cliente_id coincida con el cliente del usuario en el mismo insert; si en org_empresa cada empresa tiene cliente_id, un usuario podría enviar un empresa_id de otro cliente y la FK solo validaría que la empresa exista. **Riesgo:** Inserción con empresa_id ajeno al tenant si no se valida pertenencia empresa–cliente.
- **Recomendación:** En todos los endpoints que reciban `empresa_id` (en body o query), validar que exista un registro en org_empresa con (empresa_id, cliente_id = current_user.cliente_id) antes de crear o filtrar.

No se detectan fugas directas de datos entre tenants por omisión de cliente_id en queries; el riesgo identificado es la posible asociación incorrecta a una empresa de otro cliente si no se valida pertenencia.

---

## 12. Validación de permisos

- **Catálogo de permisos (SEED_PERMISOS_RBAC.sql):** Para INV solo se definen:
  - inv.producto.leer, inv.producto.crear, inv.producto.actualizar, inv.producto.eliminar  
  No existen en el seed: inv.categoria.*, inv.unidad_medida.*, inv.almacen.*, inv.stock.*, inv.tipo_movimiento.*, inv.movimiento.*, inv.inventario_fisico.*.

- **Uso en endpoints:** Los endpoints INV utilizan:
  - inv.categoria.leer/crear/actualizar
  - inv.unidad_medida.leer/crear/actualizar
  - inv.producto.leer/crear/actualizar
  - inv.almacen.leer/crear/actualizar
  - inv.stock.leer/crear/actualizar
  - inv.tipo_movimiento.leer/crear/actualizar
  - inv.movimiento.leer/crear/actualizar (en detalle, crear, actualizar; **no en listar**)
  - inv.inventario_fisico.leer/crear/actualizar

- **Inconsistencias:**
  1. **Permisos faltantes en catálogo:** Los permisos inv.categoria, inv.unidad_medida, inv.almacen, inv.stock, inv.tipo_movimiento, inv.movimiento, inv.inventario_fisico no están en SEED_PERMISOS_RBAC.sql. Si el sistema exige que el permiso exista en la tabla permiso para autorizar, las comprobaciones para esos recursos pueden fallar o depender de configuración adicional.
  2. **Listar movimientos sin permiso:** GET /inv/movimientos no usa require_permission; cualquier usuario autenticado del tenant podría listar movimientos.

Recomendación: Añadir en el catálogo de permisos (tabla permiso) todos los recurso.accion usados por INV (categoria, unidad_medida, almacen, stock, tipo_movimiento, movimiento, inventario_fisico) con acciones leer, crear, actualizar (y eliminar donde aplique) y proteger GET /inv/movimientos con inv.movimiento.leer.

---

## 13. Brechas funcionales detectadas

1. **Detalle de movimientos (inv_movimiento_detalle):** Sin API para consultar, crear o editar líneas de movimiento. El frontend no puede armar movimientos con ítems ni mostrar kardex por línea.
2. **Procesamiento de movimientos:** No existe lógica que, al “procesar” o confirmar un movimiento, actualice inv_stock ni registre kardex (inv_movimiento_detalle ya existe en BD). El flujo “Kardex valorizado automático” no está implementado.
3. **Detalle de inventario físico (inv_inventario_fisico_detalle):** Sin API para cargar cantidades contadas por producto ni para consultar diferencias. No se puede completar el flujo de toma física.
4. **Aprobar inventario físico y generar ajustes:** No hay endpoint ni lógica que cierre la toma, calcule diferencias y genere movimientos de ajuste (por ejemplo ENT-AJUS/SAL-AJUS) ni que actualice inv_stock.
5. **Permiso en listar movimientos:** GET /inv/movimientos no requiere permiso inv.movimiento.leer.
6. **Permisos INV en catálogo RBAC:** Faltan en SEED_PERMISOS_RBAC.sql los permisos para categoria, unidad_medida, almacen, stock, tipo_movimiento, movimiento, inventario_fisico.
7. **Validación empresa_id:** No se valida que empresa_id pertenezca al cliente del usuario en operaciones de creación/actualización.
8. **Paginación y ordenamiento:** Ningún listado ofrece page, page_size, sort_by, order; pueden ser insuficientes para listas grandes.
9. **Eliminación / anulación:** No hay DELETE ni endpoints semánticos (ej. anular movimiento, desactivar producto/categoría/almacén) documentados; la baja se hace vía actualización de es_activo/estado cuando está permitido en el schema.
10. **Alertas de stock:** No hay endpoint dedicado para “productos con stock por debajo del mínimo” (o por almacén); los datos están en stock/producto pero no agrupados como alertas.

---

## 14. Propuesta de mejoras

- **Endpoints que deberían existir:** Ver sección 9 (detalle de movimientos, detalle de inventario físico, aprobar inventario físico, procesar movimiento, anular movimiento, alertas de stock, kardex).
- **Campos a exponer:** Incluir en las respuestas de movimiento e inventario físico los detalles (líneas) correspondientes; schemas para movimiento_detalle e inventario_fisico_detalle (lectura y escritura).
- **Validaciones:** Validar en backend que empresa_id pertenezca al cliente del usuario (consulta a org_empresa por cliente_id y empresa_id) en todos los Create/Update que usen empresa_id.
- **Permisos:** Añadir en el catálogo RBAC (script de seed) todos los permisos inv.* usados por los endpoints (categoria, unidad_medida, almacen, stock, tipo_movimiento, movimiento, inventario_fisico) y proteger GET /inv/movimientos con inv.movimiento.leer.
- **Paginación y ordenamiento:** Añadir parámetros opcionales de paginación (page, page_size) y ordenamiento (sort_by, order) en listados de productos, movimientos, stock, inventarios físicos (y en futuros kardex/detalles si aplica).
- **Seguridad multi-tenant:** Centralizar validación empresa–cliente (servicio o dependencia) y usarla en todos los flujos INV que reciban empresa_id.

---

## 15. Plan de implementación

### Prioridad alta

- Añadir permiso `inv.movimiento.leer` al endpoint GET /inv/movimientos.
- Completar catálogo de permisos INV en BD (inv.categoria, inv.unidad_medida, inv.almacen, inv.stock, inv.tipo_movimiento, inv.movimiento, inv.inventario_fisico con leer/crear/actualizar y eliminar donde aplique).
- Validar en backend que empresa_id pertenezca al cliente del usuario en todas las operaciones que usen empresa_id.
- Implementar API de detalle de movimientos: GET/POST/PUT (y opcionalmente DELETE) para inv_movimiento_detalle asociado a un movimiento_id, con schemas y queries propias.
- Implementar lógica de “procesar movimiento” (o confirmar): al procesar, actualizar inv_stock e insertar/actualizar líneas de kardex según tipo de movimiento y almacén origen/destino.

### Prioridad media

- API de detalle de inventario físico: GET/POST/PUT para inv_inventario_fisico_detalle (cantidades sistema/contadas, diferencias).
- Endpoint “aprobar inventario físico”: calcular diferencias, generar movimiento(s) de ajuste y actualizar inv_stock e inv_inventario_fisico (estado, movimiento_ajuste_id).
- Incluir en respuestas de GET movimiento e inventario físico (opcionalmente con query param) las líneas de detalle para que el frontend pueda mostrar formularios completos sin llamadas adicionales.
- Paginación y ordenamiento en listados de productos, movimientos, stock e inventarios físicos.

### Prioridad baja

- Endpoint GET /inv/stock/alertas (productos con stock por debajo del mínimo, por empresa/almacén).
- Endpoint GET /inv/kardex (por producto y opcionalmente almacén, con filtros de fecha).
- Endpoints semánticos de anulación (movimiento) o desactivación (producto, categoría, almacén, etc.) si se desea exponer explícitamente en la API.

---

**Fin del documento.**

¿Deseas que proceda con la implementación de las mejoras recomendadas para el módulo INV?
