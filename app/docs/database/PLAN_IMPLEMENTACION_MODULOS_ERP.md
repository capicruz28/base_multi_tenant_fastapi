# Plan de Implementación — Módulos ERP (Fase 1)

**Objetivo:** Implementar los 5 módulos básicos (ORG, INV, PUR, SLS, INV_BILL) de forma ordenada, sin romper nada y con filtro de tenant estricto.

**Criterios:**
- Un módulo a la vez; probar antes de seguir.
- Filtro de tenant exacto en todas las capas (queries, servicios, endpoints).
- Frontend puede consumir todo lo necesario (endpoints REST, schemas claros).

---

## Orden de implementación y dependencias

| # | Módulo    | Dependencias | Estado   | Pruebas antes de seguir |
|---|-----------|--------------|----------|--------------------------|
| 1 | **ORG**   | Ninguna      | **Completado** | Sí                       |
| 2 | **INV**   | ORG          | **Completado** | Sí                       |
| 3 | **PUR**   | ORG, INV     | **Completado** | Sí                       |
| 4 | **SLS**   | ORG, INV     | **Completado** | Sí                       |
| 5 | **INV_BILL** | SLS       | **Completado** | Sí                       |

---

## Módulo 1: ORG — Organización

### 1.1 Alcance

- **Tablas (TABLAS_BD_ERP_COMPLETO):** org_empresa, org_centro_costo, org_sucursal, org_departamento, org_cargo, org_parametro_sistema.
- **Menú (MENU_NAVEGACION):** Mi Empresa, Sucursales, Departamentos, Cargos, Centros de Costo, Parámetros del Sistema.

### 1.2 Tareas

1. **BD / Tablas**
   - [x] Crear `app/infrastructure/database/tables_erp/__init__.py`.
   - [x] Crear `tables_erp/tables_org.py` con tablas SQLAlchemy Core (sin FK a `cliente` para compatibilidad BD dedicada).
   - [ ] Script SQL para crear tablas ORG en BD: usar sección ORG de `TABLAS_BD_ERP_COMPLETO.sql` (tablas org_empresa, org_centro_costo, org_sucursal, org_departamento, org_cargo, org_parametro_sistema).

2. **Queries**
   - [x] Crear `app/infrastructure/database/queries/org/__init__.py`.
   - [x] Queries por entidad (empresa_queries, centro_costo_queries, sucursal_queries, departamento_queries, cargo_queries, parametro_queries) con SQLAlchemy Core.
   - [x] Todas las ejecuciones con `client_id` obligatorio; filtro explícito en WHERE (cliente_id + id de recurso).

3. **Módulo app**
   - [x] `app/modules/org/` con: `application/services/`, `domain/`, `presentation/`.
   - [x] Servicios: empresa_service, centro_costo_service, sucursal_service, departamento_service, cargo_service, parametro_service.
   - [x] Cada método de servicio recibe `client_id` pasado desde el endpoint (current_user.cliente_id); nunca desde body.
   - [x] Schemas Pydantic (Create, Update, Read) por entidad en `presentation/schemas.py`.
   - [x] Endpoints: empresa, sucursales, centros-costo, departamentos, cargos, parametros (CRUD completo).

4. **API**
   - [x] Registrar routers ORG en `app/api/v1/api.py` con prefijo `/org` y tags.

5. **Tenant**
   - [x] Listados/filtros usan `client_id` de `get_current_active_user().cliente_id`.
   - [x] Creaciones/actualizaciones fuerzan `cliente_id` en capa de queries; no se acepta en body.

### 1.3 Endpoints ORG (para frontend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET    | /org/empresa | Listar empresas del tenant (1 por cliente en muchos casos). |
| GET    | /org/empresa/{id} | Detalle de empresa. |
| POST   | /org/empresa | Crear empresa (cliente_id desde contexto). |
| PUT    | /org/empresa/{id} | Actualizar empresa. |
| GET    | /org/sucursales | Listar sucursales (filtro por empresa_id opcional). |
| GET    | /org/sucursales/{id} | Detalle sucursal. |
| POST   | /org/sucursales | Crear sucursal. |
| PUT    | /org/sucursales/{id} | Actualizar sucursal. |
| GET    | /org/centros-costo | Listar centros de costo. |
| GET    | /org/centros-costo/{id} | Detalle centro de costo. |
| POST   | /org/centros-costo | Crear centro de costo. |
| PUT    | /org/centros-costo/{id} | Actualizar centro de costo. |
| GET    | /org/departamentos | Listar departamentos. |
| GET    | /org/departamentos/{id} | Detalle departamento. |
| POST   | /org/departamentos | Crear departamento. |
| PUT    | /org/departamentos/{id} | Actualizar departamento. |
| GET    | /org/cargos | Listar cargos. |
| GET    | /org/cargos/{id} | Detalle cargo. |
| POST   | /org/cargos | Crear cargo. |
| PUT    | /org/cargos/{id} | Actualizar cargo. |
| GET    | /org/parametros | Listar parámetros (por modulo_codigo opcional). |
| GET    | /org/parametros/{id} | Detalle parámetro. |
| POST   | /org/parametros | Crear parámetro. |
| PUT    | /org/parametros/{id} | Actualizar parámetro. |

---

## Módulo 2: INV — Inventarios (Completado)

### 2.1 Alcance

- **Tablas:** inv_categoria_producto, inv_unidad_medida, inv_producto, inv_almacen, inv_stock, inv_tipo_movimiento, inv_movimiento, inv_movimiento_detalle, inv_inventario_fisico, inv_inventario_fisico_detalle.
- **Menú:** Productos, Categorías, Unidades de Medida, Almacenes, Consulta de Stock, Tipos de Movimiento, Movimientos de Inventario, Inventario Físico.

### 2.2 Tareas

1. **BD / Tablas**
   - [x] Crear `app/infrastructure/database/tables_erp/tables_inv.py` con todas las tablas INV (10 tablas).
   - [x] Actualizar `tables_erp/__init__.py` para exportar tablas INV.

2. **Queries**
   - [x] Crear `app/infrastructure/database/queries/inv/__init__.py`.
   - [x] Queries por entidad: categoria_queries, unidad_medida_queries, producto_queries, almacen_queries, stock_queries, tipo_movimiento_queries, movimiento_queries, inventario_fisico_queries.
   - [x] Todas las ejecuciones con `client_id` obligatorio; filtro explícito en WHERE.

3. **Módulo app**
   - [x] `app/modules/inv/` con: `application/services/`, `domain/`, `presentation/`.
   - [x] Servicios: categoria_service, unidad_medida_service, producto_service, almacen_service, stock_service, tipo_movimiento_service, movimiento_service, inventario_fisico_service.
   - [x] Cada método de servicio recibe `client_id` pasado desde el endpoint (current_user.cliente_id); nunca desde body.
   - [x] Schemas Pydantic (Create, Update, Read) por entidad en `presentation/schemas.py` con **TODOS los campos esenciales incluidos desde el inicio**.
   - [x] Endpoints: categorias, unidades-medida, productos, almacenes, stock, tipos-movimiento, movimientos, inventario-fisico (CRUD completo).

4. **API**
   - [x] Registrar routers INV en `app/api/v1/api.py` con prefijo `/inv` y tags.

5. **Tenant**
   - [x] Listados/filtros usan `client_id` de `get_current_active_user().cliente_id`.
   - [x] Creaciones/actualizaciones fuerzan `cliente_id` en capa de queries; no se acepta en body.

### 2.3 Endpoints INV (para frontend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET    | /inv/categorias | Listar categorías del tenant. |
| GET    | /inv/categorias/{id} | Detalle de categoría. |
| POST   | /inv/categorias | Crear categoría (cliente_id desde contexto). |
| PUT    | /inv/categorias/{id} | Actualizar categoría. |
| GET    | /inv/unidades-medida | Listar unidades de medida. |
| GET    | /inv/unidades-medida/{id} | Detalle unidad de medida. |
| POST   | /inv/unidades-medida | Crear unidad de medida. |
| PUT    | /inv/unidades-medida/{id} | Actualizar unidad de medida. |
| GET    | /inv/productos | Listar productos (con filtros: empresa_id, categoria_id, tipo_producto, buscar). |
| GET    | /inv/productos/{id} | Detalle producto. |
| POST   | /inv/productos | Crear producto. |
| PUT    | /inv/productos/{id} | Actualizar producto. |
| GET    | /inv/almacenes | Listar almacenes (con filtros: empresa_id, sucursal_id). |
| GET    | /inv/almacenes/{id} | Detalle almacén. |
| POST   | /inv/almacenes | Crear almacén. |
| PUT    | /inv/almacenes/{id} | Actualizar almacén. |
| GET    | /inv/stock | Listar stocks (con filtros: empresa_id, producto_id, almacen_id). |
| GET    | /inv/stock/{id} | Detalle stock. |
| GET    | /inv/stock/producto/{producto_id}/almacen/{almacen_id} | Stock por producto y almacén. |
| POST   | /inv/stock | Crear stock. |
| PUT    | /inv/stock/{id} | Actualizar stock. |
| GET    | /inv/tipos-movimiento | Listar tipos de movimiento. |
| GET    | /inv/tipos-movimiento/{id} | Detalle tipo de movimiento. |
| POST   | /inv/tipos-movimiento | Crear tipo de movimiento. |
| PUT    | /inv/tipos-movimiento/{id} | Actualizar tipo de movimiento. |
| GET    | /inv/movimientos | Listar movimientos (con filtros: empresa_id, tipo_movimiento_id, almacen_id, estado, fecha_desde, fecha_hasta). |
| GET    | /inv/movimientos/{id} | Detalle movimiento. |
| POST   | /inv/movimientos | Crear movimiento. |
| PUT    | /inv/movimientos/{id} | Actualizar movimiento. |
| GET    | /inv/inventario-fisico | Listar inventarios físicos (con filtros: empresa_id, almacen_id, estado, fecha_desde, fecha_hasta). |
| GET    | /inv/inventario-fisico/{id} | Detalle inventario físico. |
| POST   | /inv/inventario-fisico | Crear inventario físico. |
| PUT    | /inv/inventario-fisico/{id} | Actualizar inventario físico. |

### 2.4 Notas importantes

- ✅ **Todos los campos esenciales incluidos desde el inicio** en los schemas Read, Create y Update.
- ✅ El módulo INV depende de ORG (usa org_empresa, org_sucursal, org_centro_costo).
- ✅ Producto incluye campos completos: identificación (SKU, código de barras), clasificación, unidades de medida, características físicas, configuración de inventario, costos, precios, tributario, imágenes.
- ✅ Stock incluye cantidad_actual, cantidad_reservada, cantidad_disponible (calculado), costo_promedio, valor_total (calculado).
- ✅ Movimientos incluyen referencia a documentos origen (PUR, SLS, MFG), terceros, almacenes origen/destino.

---

## Módulo 3: PUR — Compras (Completado)

### 3.1 Alcance

- **Tablas:** pur_proveedor, pur_proveedor_contacto, pur_producto_proveedor, pur_solicitud_compra, pur_solicitud_compra_detalle, pur_cotizacion, pur_cotizacion_detalle, pur_orden_compra, pur_orden_compra_detalle, pur_recepcion, pur_recepcion_detalle.
- **Menú:** Proveedores, Contactos de Proveedor, Productos por Proveedor, Solicitudes de Compra, Cotizaciones, Órdenes de Compra, Recepción de Mercadería.

### 3.2 Tareas

1. **BD / Tablas**
   - [x] Crear `app/infrastructure/database/tables_erp/tables_pur.py` con todas las tablas PUR (11 tablas).
   - [x] Actualizar `tables_erp/__init__.py` para exportar tablas PUR.

2. **Queries**
   - [x] Crear `app/infrastructure/database/queries/pur/__init__.py`.
   - [x] Queries por entidad: proveedor_queries, contacto_queries, producto_proveedor_queries, solicitud_queries, cotizacion_queries, orden_compra_queries, recepcion_queries.
   - [x] Todas las ejecuciones con `client_id` obligatorio; filtro explícito en WHERE.

3. **Módulo app**
   - [x] `app/modules/pur/` con: `application/services/`, `domain/`, `presentation/`.
   - [x] Servicios: proveedor_service, contacto_service, producto_proveedor_service, solicitud_service, cotizacion_service, orden_compra_service, recepcion_service.
   - [x] Cada método de servicio recibe `client_id` pasado desde el endpoint (current_user.cliente_id); nunca desde body.
   - [x] Schemas Pydantic (Create, Update, Read) por entidad en `presentation/schemas.py` con **TODOS los campos esenciales incluidos desde el inicio**.
   - [x] Endpoints: proveedores, contactos, productos-proveedor, solicitudes, cotizaciones, ordenes-compra, recepciones (CRUD completo).

4. **API**
   - [x] Registrar routers PUR en `app/api/v1/api.py` con prefijo `/pur` y tags.

5. **Tenant**
   - [x] Listados/filtros usan `client_id` de `get_current_active_user().cliente_id`.
   - [x] Creaciones/actualizaciones fuerzan `cliente_id` en capa de queries; no se acepta en body.

### 3.3 Endpoints PUR (para frontend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET    | /pur/proveedores | Listar proveedores del tenant (con búsqueda). |
| GET    | /pur/proveedores/{id} | Detalle de proveedor. |
| POST   | /pur/proveedores | Crear proveedor (cliente_id desde contexto). |
| PUT    | /pur/proveedores/{id} | Actualizar proveedor. |
| GET    | /pur/contactos | Listar contactos (filtro por proveedor_id opcional). |
| GET    | /pur/contactos/{id} | Detalle contacto. |
| POST   | /pur/contactos | Crear contacto. |
| PUT    | /pur/contactos/{id} | Actualizar contacto. |
| GET    | /pur/productos-proveedor | Listar productos por proveedor. |
| GET    | /pur/productos-proveedor/{id} | Detalle producto por proveedor. |
| POST   | /pur/productos-proveedor | Crear producto por proveedor. |
| PUT    | /pur/productos-proveedor/{id} | Actualizar producto por proveedor. |
| GET    | /pur/solicitudes | Listar solicitudes de compra (con filtros: empresa_id, estado, fechas). |
| GET    | /pur/solicitudes/{id} | Detalle solicitud. |
| POST   | /pur/solicitudes | Crear solicitud. |
| PUT    | /pur/solicitudes/{id} | Actualizar solicitud. |
| GET    | /pur/cotizaciones | Listar cotizaciones (con filtros: empresa_id, proveedor_id, solicitud_compra_id, estado, fechas). |
| GET    | /pur/cotizaciones/{id} | Detalle cotización. |
| POST   | /pur/cotizaciones | Crear cotización. |
| PUT    | /pur/cotizaciones/{id} | Actualizar cotización. |
| GET    | /pur/ordenes-compra | Listar órdenes de compra (con filtros: empresa_id, proveedor_id, solicitud_compra_id, estado, fechas). |
| GET    | /pur/ordenes-compra/{id} | Detalle orden de compra. |
| POST   | /pur/ordenes-compra | Crear orden de compra. |
| PUT    | /pur/ordenes-compra/{id} | Actualizar orden de compra. |
| GET    | /pur/recepciones | Listar recepciones (con filtros: empresa_id, orden_compra_id, proveedor_id, almacen_id, estado, fechas). |
| GET    | /pur/recepciones/{id} | Detalle recepción. |
| POST   | /pur/recepciones | Crear recepción. |
| PUT    | /pur/recepciones/{id} | Actualizar recepción. |

### 3.4 Notas importantes

- ✅ **Todos los campos esenciales incluidos desde el inicio** en los schemas Read, Create y Update.
- ✅ El módulo PUR depende de ORG (usa org_empresa, org_departamento, org_centro_costo) e INV (usa inv_producto, inv_almacen, inv_unidad_medida).
- ✅ Proveedor incluye campos completos: identificación, dirección fiscal, contacto principal, condiciones comerciales, datos bancarios, calificación, límites de crédito.
- ✅ Solicitud de compra incluye: solicitante, destino (almacén/centro de costo), tipo y motivo, aprobación.
- ✅ Cotización incluye: proveedor, referencia a solicitud, condiciones comerciales, totales (subtotal, descuento, IGV, total).
- ✅ Orden de compra incluye: proveedor, referencias (solicitud, cotización), condiciones comerciales, control de recepción (items_recepcionados, porcentaje_recepcion).
- ✅ Recepción incluye: orden de compra, proveedor, almacén, guía de remisión, transporte, movimiento de inventario generado.

---

## Módulo 4: SLS — Ventas

### 4.1 Alcance

- **Tablas (TABLAS_BD_ERP_COMPLETO):** sls_cliente, sls_cliente_contacto, sls_cliente_direccion, sls_cotizacion, sls_cotizacion_detalle, sls_pedido, sls_pedido_detalle.
- **Menú (MENU_NAVEGACION):** Clientes, Contactos de Cliente, Direcciones de Entrega, Cotizaciones, Pedidos de Venta.

### 4.2 Tareas

1. **BD / Tablas**
   - [x] Crear `app/infrastructure/database/tables_erp/tables_sls.py` con tablas SQLAlchemy Core (sin FK a `cliente` para compatibilidad BD dedicada).
   - [x] Tablas: sls_cliente, sls_cliente_contacto, sls_cliente_direccion, sls_cotizacion, sls_cotizacion_detalle, sls_pedido, sls_pedido_detalle.
   - [x] Todas las tablas incluyen `cliente_id` y ForeignKeys a ORG (org_empresa) e INV (inv_producto, inv_unidad_medida, inv_almacen).

2. **Queries**
   - [x] Crear `app/infrastructure/database/queries/sls/__init__.py`.
   - [x] Queries por entidad (cliente_queries, contacto_queries, direccion_queries, cotizacion_queries, pedido_queries) con SQLAlchemy Core.
   - [x] Todas las ejecuciones con `client_id` obligatorio; filtro explícito en WHERE (cliente_id + id de recurso).
   - [x] Parámetros de filtrado adicionales: empresa_id, cliente_venta_id, vendedor_usuario_id, estado, fechas.

3. **Módulo app**
   - [x] `app/modules/sls/` con: `application/services/`, `presentation/`.
   - [x] Servicios: cliente_service, contacto_service, direccion_service, cotizacion_service, pedido_service.
   - [x] Cada método de servicio recibe `client_id` pasado desde el endpoint (current_user.cliente_id); nunca desde body.
   - [x] Schemas Pydantic (Create, Update, Read) por entidad en `presentation/schemas.py`.
   - [x] **Todos los campos esenciales incluidos desde el inicio** en los schemas Read, Create y Update.
   - [x] Endpoints: clientes, contactos, direcciones, cotizaciones, pedidos (CRUD completo).

4. **API**
   - [x] Registrar router en `app/api/v1/api.py` con prefijo `/sls` y tags `["SLS - Ventas"]`.

### 4.3 Endpoints SLS (para frontend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET    | /sls/clientes | Listar clientes del tenant (con búsqueda, filtro por empresa, vendedor). |
| GET    | /sls/clientes/{id} | Detalle de cliente. |
| POST   | /sls/clientes | Crear cliente (cliente_id desde contexto). |
| PUT    | /sls/clientes/{id} | Actualizar cliente. |
| GET    | /sls/contactos | Listar contactos (filtro por cliente_venta_id opcional). |
| GET    | /sls/contactos/{id} | Detalle contacto. |
| POST   | /sls/contactos | Crear contacto. |
| PUT    | /sls/contactos/{id} | Actualizar contacto. |
| GET    | /sls/direcciones | Listar direcciones (filtro por cliente_venta_id opcional). |
| GET    | /sls/direcciones/{id} | Detalle direccion. |
| POST   | /sls/direcciones | Crear direccion. |
| PUT    | /sls/direcciones/{id} | Actualizar direccion. |
| GET    | /sls/cotizaciones | Listar cotizaciones (con filtros: empresa_id, cliente_venta_id, vendedor, estado, fechas). |
| GET    | /sls/cotizaciones/{id} | Detalle cotización. |
| POST   | /sls/cotizaciones | Crear cotización. |
| PUT    | /sls/cotizaciones/{id} | Actualizar cotización. |
| GET    | /sls/pedidos | Listar pedidos (con filtros: empresa_id, cliente_venta_id, vendedor, cotizacion_id, estado, fechas). |
| GET    | /sls/pedidos/{id} | Detalle pedido. |
| POST   | /sls/pedidos | Crear pedido. |
| PUT    | /sls/pedidos/{id} | Actualizar pedido. |

### 4.4 Notas importantes

- ✅ **Todos los campos esenciales incluidos desde el inicio** en los schemas Read, Create y Update.
- ✅ El módulo SLS depende de ORG (usa org_empresa, org_centro_costo) e INV (usa inv_producto, inv_unidad_medida, inv_almacen).
- ✅ Cliente incluye campos completos: identificación, dirección fiscal, contacto principal, condiciones comerciales, límites de crédito, vendedor asignado, calificación, nivel de riesgo.
- ✅ Cotización incluye: cliente, vendedor, condiciones comerciales, totales (subtotal, descuento, IGV, total), estado (borrador, enviada, aceptada, rechazada, vencida, convertida), conversión a pedido.
- ✅ Pedido incluye: cliente, dirección de entrega, referencia a cotización, condiciones comerciales, control de despacho (items_despachados, porcentaje_despacho), estado (borrador, confirmado, aprobado, parcial, completo, facturado, anulado), prioridad, centro de costo.

---

## Módulo 5: INV_BILL — Facturación Electrónica

### 5.1 Alcance

- **Tablas (TABLAS_BD_ERP_COMPLETO):** invbill_serie_comprobante, invbill_comprobante, invbill_comprobante_detalle.
- **Menú (MENU_NAVEGACION):** Series de Comprobantes, Comprobantes, Registro de Ventas.

### 5.2 Tareas

1. **BD / Tablas**
   - [x] Crear `app/infrastructure/database/tables_erp/tables_invbill.py` con tablas SQLAlchemy Core (sin FK a `cliente` para compatibilidad BD dedicada).
   - [x] Tablas: invbill_serie_comprobante, invbill_comprobante, invbill_comprobante_detalle.
   - [x] Todas las tablas incluyen `cliente_id` y ForeignKeys a ORG (org_empresa, org_sucursal), SLS (sls_cliente, sls_pedido) e INV (inv_producto, inv_unidad_medida).

2. **Queries**
   - [x] Crear `app/infrastructure/database/queries/invbill/__init__.py`.
   - [x] Queries por entidad (serie_queries, comprobante_queries, comprobante_detalle_queries) con SQLAlchemy Core.
   - [x] Todas las ejecuciones con `client_id` obligatorio; filtro explícito en WHERE (cliente_id + id de recurso).
   - [x] Parámetros de filtrado adicionales: empresa_id, tipo_comprobante, cliente_venta_id, pedido_id, estado, estado_sunat, fechas.

3. **Módulo app**
   - [x] `app/modules/invbill/` con: `application/services/`, `presentation/`.
   - [x] Servicios: serie_service, comprobante_service, comprobante_detalle_service.
   - [x] Cada método de servicio recibe `client_id` pasado desde el endpoint (current_user.cliente_id); nunca desde body.
   - [x] Schemas Pydantic (Create, Update, Read) por entidad en `presentation/schemas.py`.
   - [x] **Todos los campos esenciales incluidos desde el inicio** en los schemas Read, Create y Update.
   - [x] Endpoints: series, comprobantes, comprobantes-detalles (CRUD completo).

4. **API**
   - [x] Registrar router en `app/api/v1/api.py` con prefijo `/inv-bill` y tags `["INV_BILL - Facturación Electrónica"]`.

### 5.3 Endpoints INV_BILL (para frontend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET    | /inv-bill/series | Listar series de comprobantes (con filtros: empresa_id, tipo_comprobante, solo_activos). |
| GET    | /inv-bill/series/{id} | Detalle de serie. |
| POST   | /inv-bill/series | Crear serie (cliente_id desde contexto). |
| PUT    | /inv-bill/series/{id} | Actualizar serie. |
| GET    | /inv-bill/comprobantes | Listar comprobantes (con filtros: empresa_id, tipo_comprobante, cliente_venta_id, pedido_id, estado, estado_sunat, fechas). |
| GET    | /inv-bill/comprobantes/{id} | Detalle comprobante. |
| POST   | /inv-bill/comprobantes | Crear comprobante. |
| PUT    | /inv-bill/comprobantes/{id} | Actualizar comprobante. |
| GET    | /inv-bill/comprobantes-detalles | Listar detalles (filtro por comprobante_id opcional). |
| GET    | /inv-bill/comprobantes-detalles/{id} | Detalle de detalle. |
| POST   | /inv-bill/comprobantes-detalles | Crear detalle. |
| PUT    | /inv-bill/comprobantes-detalles/{id} | Actualizar detalle. |

### 5.4 Notas importantes

- ✅ **Todos los campos esenciales incluidos desde el inicio** en los schemas Read, Create y Update.
- ✅ El módulo INV_BILL depende de ORG (usa org_empresa, org_sucursal), SLS (usa sls_cliente, sls_pedido) e INV (usa inv_producto, inv_unidad_medida).
- ✅ Serie de comprobante incluye: tipo_comprobante ('01'=Factura, '03'=Boleta, '07'=NC, '08'=ND), serie, numeración (actual, inicial, final), configuración electrónica y autorización SUNAT.
- ✅ Comprobante incluye: identificación (tipo, serie, número), cliente, montos (subtotales gravado/exonerado/inafecto/gratuito, descuento, IGV, total), detracción/retención/percepción, campos para integración SUNAT (codigo_hash, firma_digital, codigo_qr, estado_sunat, cdr_xml, xml_comprobante, pdf_url).
- ✅ Comprobante detalle incluye: producto, cantidad, unidad de medida (código SUNAT), precios, tipo de afectación IGV, código producto SUNAT, lote.
- ⚠️ **Nota:** Esta implementación NO incluye integración directa con SUNAT. Los campos están preparados para que un servicio externo o módulo futuro complete la integración (generación XML, firma digital, envío a SUNAT, procesamiento CDR).

---

## Módulo 6: PRC — Gestión de Precios y Promociones (Completado)

### 6.1 Alcance

- **Tablas (TABLAS_BD_ERP_COMPLETO):** prc_lista_precio, prc_lista_precio_detalle, prc_promocion.
- **Menú (MENU_NAVEGACION):** Listas de Precio, Promociones.
- **Dependencias:** ORG (org_empresa), INV (inv_producto, inv_categoria_producto, inv_unidad_medida).
- **Usado por:** SLS (cotizaciones, pedidos), POS.

### 6.2 Tareas Completadas

- [x] Crear `app/infrastructure/database/tables_erp/tables_prc.py` con las 3 tablas PRC.
- [x] Actualizar `app/infrastructure/database/tables_erp/__init__.py` para exportar tablas PRC.
- [x] Crear `app/infrastructure/database/queries/prc/lista_precio_queries.py` con CRUD para listas y detalles.
- [x] Crear `app/infrastructure/database/queries/prc/promocion_queries.py` con CRUD para promociones.
- [x] Crear `app/infrastructure/database/queries/prc/__init__.py` para exportar queries.
- [x] Crear `app/modules/prc/presentation/schemas.py` con schemas Create/Update/Read completos (todos los campos esenciales).
- [x] Crear `app/modules/prc/application/services/lista_precio_service.py` con lógica de negocio.
- [x] Crear `app/modules/prc/application/services/promocion_service.py` con lógica de negocio.
- [x] Crear `app/modules/prc/application/services/__init__.py` para exportar servicios.
- [x] Crear `app/modules/prc/presentation/endpoints_listas_precio.py` con endpoints REST.
- [x] Crear `app/modules/prc/presentation/endpoints_promociones.py` con endpoints REST.
- [x] Crear `app/modules/prc/presentation/endpoints.py` como router principal.
- [x] Registrar router en `app/api/v1/api.py` con prefijo `/prc` y tags `["PRC - Precios y Promociones"]`.

### 6.3 Endpoints PRC (para frontend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET    | /prc/listas-precio | Listar listas de precio (con filtros: empresa_id, tipo_lista, solo_activos, solo_vigentes, buscar). |
| GET    | /prc/listas-precio/{id} | Detalle de lista de precio. |
| POST   | /prc/listas-precio | Crear lista de precio (cliente_id desde contexto). |
| PUT    | /prc/listas-precio/{id} | Actualizar lista de precio. |
| GET    | /prc/listas-precio/{id}/detalles | Listar detalles de una lista (filtro por producto_id opcional). |
| POST   | /prc/listas-precio/{id}/detalles | Crear detalle de lista (agregar producto con precio). |
| GET    | /prc/listas-precio/detalles/{id} | Detalle de detalle. |
| PUT    | /prc/listas-precio/detalles/{id} | Actualizar detalle. |
| GET    | /prc/promociones | Listar promociones (con filtros: empresa_id, tipo_promocion, aplica_a, producto_id, categoria_id, solo_activos, solo_vigentes, buscar). |
| GET    | /prc/promociones/{id} | Detalle de promoción. |
| POST   | /prc/promociones | Crear promoción (cliente_id desde contexto). |
| PUT    | /prc/promociones/{id} | Actualizar promoción. |

### 6.4 Notas importantes

- ✅ **Todos los campos esenciales incluidos desde el inicio** en los schemas Read, Create y Update.
- ✅ El módulo PRC depende de ORG (usa org_empresa) e INV (usa inv_producto, inv_categoria_producto, inv_unidad_medida).
- ✅ Lista de precio incluye: código, nombre, tipo ('general', 'mayorista', 'minorista', 'distribuidor', 'corporativo'), moneda, vigencia, configuración de IGV y descuentos, lista por defecto.
- ✅ Detalle de lista incluye: producto, precio unitario, unidad de medida, precios escalonados (cantidad mínima/máxima), descuento máximo por producto, vigencia específica.
- ✅ Promoción incluye: código, nombre, tipo ('descuento_porcentaje', 'descuento_monto', '2x1', '3x2', 'producto_gratis'), aplicabilidad ('producto', 'categoria', 'marca', 'toda_venta'), descuentos, reglas de aplicación (JSON), vigencia, límites de uso, combinabilidad, canales de venta (JSON), códigos de cupón.
- ✅ **Uso:** Las listas de precio se asignan a clientes en SLS y se usan al crear cotizaciones/pedidos. Las promociones se aplican automáticamente según reglas de negocio.

---

## Módulo 7: LOG — Logística y Distribución (Completado)

### 7.1 Alcance

- **Tablas (TABLAS_BD_ERP_COMPLETO):** log_transportista, log_vehiculo, log_ruta, log_guia_remision, log_guia_remision_detalle, log_despacho, log_despacho_guia.
- **Menú (MENU_NAVEGACION):** Transportistas, Vehículos, Rutas, Guías de Remisión, Despachos.
- **Dependencias:** ORG (org_empresa, org_sucursal), INV (inv_producto, inv_unidad_medida).
- **Usado por:** SLS (ventas con despacho), INV_BILL (guías relacionadas a comprobantes).

### 7.2 Tareas Completadas

- [x] Crear `app/infrastructure/database/tables_erp/tables_log.py` con las 7 tablas LOG.
- [x] Actualizar `app/infrastructure/database/tables_erp/__init__.py` para exportar tablas LOG.
- [x] Crear `app/infrastructure/database/queries/log/transportista_queries.py` con CRUD para transportistas.
- [x] Crear `app/infrastructure/database/queries/log/vehiculo_queries.py` con CRUD para vehículos.
- [x] Crear `app/infrastructure/database/queries/log/ruta_queries.py` con CRUD para rutas.
- [x] Crear `app/infrastructure/database/queries/log/guia_remision_queries.py` con CRUD para guías y detalles.
- [x] Crear `app/infrastructure/database/queries/log/despacho_queries.py` con CRUD para despachos y despacho-guía.
- [x] Crear `app/infrastructure/database/queries/log/__init__.py` para exportar queries.
- [x] Crear `app/modules/log/presentation/schemas.py` con schemas Create/Update/Read completos (todos los campos esenciales).
- [x] Crear `app/modules/log/application/services/*.py` (5 archivos) con lógica de negocio.
- [x] Crear `app/modules/log/presentation/endpoints_*.py` (5 archivos) con endpoints REST.
- [x] Crear `app/modules/log/presentation/endpoints.py` como router principal.
- [x] Registrar router en `app/api/v1/api.py` con prefijo `/log` y tags `["LOG - Logística y Distribución"]`.

### 7.3 Endpoints LOG (para frontend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET    | /log/transportistas | Listar transportistas (con filtros: empresa_id, solo_activos, buscar). |
| GET    | /log/transportistas/{id} | Detalle de transportista. |
| POST   | /log/transportistas | Crear transportista (cliente_id desde contexto). |
| PUT    | /log/transportistas/{id} | Actualizar transportista. |
| GET    | /log/vehiculos | Listar vehículos (con filtros: empresa_id, transportista_id, tipo_propiedad, estado_vehiculo, solo_activos, buscar). |
| GET    | /log/vehiculos/{id} | Detalle de vehículo. |
| POST   | /log/vehiculos | Crear vehículo (cliente_id desde contexto). |
| PUT    | /log/vehiculos/{id} | Actualizar vehículo. |
| GET    | /log/rutas | Listar rutas (con filtros: empresa_id, origen_sucursal_id, solo_activos, buscar). |
| GET    | /log/rutas/{id} | Detalle de ruta. |
| POST   | /log/rutas | Crear ruta (cliente_id desde contexto). |
| PUT    | /log/rutas/{id} | Actualizar ruta. |
| GET    | /log/guias-remision | Listar guías de remisión (con filtros: empresa_id, estado, motivo_traslado, transportista_id, fechas, buscar). |
| GET    | /log/guias-remision/{id} | Detalle de guía. |
| POST   | /log/guias-remision | Crear guía (cliente_id desde contexto). |
| PUT    | /log/guias-remision/{id} | Actualizar guía. |
| GET    | /log/guias-remision/{id}/detalles | Listar detalles de guía. |
| POST   | /log/guias-remision/{id}/detalles | Crear detalle de guía. |
| GET    | /log/guias-remision/detalles/{id} | Detalle de detalle. |
| PUT    | /log/guias-remision/detalles/{id} | Actualizar detalle. |
| GET    | /log/despachos | Listar despachos (con filtros: empresa_id, estado, ruta_id, vehiculo_id, fechas, buscar). |
| GET    | /log/despachos/{id} | Detalle de despacho. |
| POST   | /log/despachos | Crear despacho (cliente_id desde contexto). |
| PUT    | /log/despachos/{id} | Actualizar despacho. |
| GET    | /log/despachos/{id}/guias | Listar guías de un despacho. |
| POST   | /log/despachos/{id}/guias | Crear relación despacho-guía. |
| GET    | /log/despachos/guias/{id} | Detalle de relación despacho-guía. |
| PUT    | /log/despachos/guias/{id} | Actualizar relación despacho-guía. |

### 7.4 Notas importantes

- ✅ **Todos los campos esenciales incluidos desde el inicio** en los schemas Read, Create y Update.
- ✅ El módulo LOG depende de ORG (usa org_empresa, org_sucursal) e INV (usa inv_producto, inv_unidad_medida).
- ✅ Transportista incluye: código, razón social, documentos (RUC, MTC), tarifas (por km/hora), calificación.
- ✅ Vehículo incluye: placa, marca, modelo, tipo ('camion', 'camioneta', 'furgon', 'moto', 'trailer'), capacidad, propiedad ('propio', 'tercero'), documentos (SOAT, revisión técnica), GPS, estado ('disponible', 'en_ruta', 'mantenimiento', 'inactivo').
- ✅ Ruta incluye: código, nombre, origen-destino, distancia, tiempo estimado, costos, peajes, puntos intermedios (JSON).
- ✅ Guía de remisión incluye: serie-número, fechas (emisión, traslado), tipo ('remitente', 'transportista'), motivo ('venta', 'compra', 'transferencia', 'consignacion', 'devolucion'), remitente/destinatario, puntos de partida/llegada, transporte (modalidad, transportista, vehículo, conductor), bultos/peso, documento sustento, estado ('borrador', 'emitida', 'en_transito', 'entregada', 'anulada'), códigos SUNAT (hash, QR).
- ✅ Despacho incluye: número, fecha programada, ruta, vehículo/conductor, ejecución (fechas salida/retorno, km inicial/final), totales (guías, peso, bultos), costos (combustible, peajes, otros), estado ('planificado', 'en_ruta', 'completado', 'cancelado'), incidencias.
- ✅ Despacho-Guía vincula despachos con guías de remisión, incluye orden de entrega, fecha de entrega, estado de entrega, receptor.
- ✅ **Uso:** Las guías de remisión se vinculan a ventas/compras/transferencias. Los despachos agrupan múltiples guías para optimizar rutas y controlar entregas.

---

## Módulo 8: FIN — Finanzas y Contabilidad (Completado)

### 8.1 Alcance

- **Tablas (TABLAS_BD_ERP_COMPLETO):** fin_plan_cuentas, fin_periodo_contable, fin_asiento_contable, fin_asiento_detalle.
- **Menú (MENU_NAVEGACION):** Plan de Cuentas, Periodos Contables, Asientos Contables.
- **Dependencias:** ORG (org_empresa, org_centro_costo).
- **Usado por:** Todos los módulos operativos generan movimientos contables automáticos.

### 8.2 Tareas Completadas

- [x] Crear `app/infrastructure/database/tables_erp/tables_fin.py` con las 4 tablas FIN.
- [x] Actualizar `app/infrastructure/database/tables_erp/__init__.py` para exportar tablas FIN.
- [x] Crear `app/infrastructure/database/queries/fin/plan_cuentas_queries.py` con CRUD para plan de cuentas.
- [x] Crear `app/infrastructure/database/queries/fin/periodo_contable_queries.py` con CRUD para periodos.
- [x] Crear `app/infrastructure/database/queries/fin/asiento_contable_queries.py` con CRUD para asientos y detalles.
- [x] Crear `app/infrastructure/database/queries/fin/__init__.py` para exportar queries.
- [x] Crear `app/modules/fin/presentation/schemas.py` con schemas Create/Update/Read completos (todos los campos esenciales).
- [x] Crear `app/modules/fin/application/services/*.py` (3 archivos) con lógica de negocio.
- [x] Crear `app/modules/fin/presentation/endpoints_*.py` (3 archivos) con endpoints REST.
- [x] Crear `app/modules/fin/presentation/endpoints.py` como router principal.
- [x] Registrar router en `app/api/v1/api.py` con prefijo `/fin` y tags `["FIN - Finanzas y Contabilidad"]`.

### 8.3 Endpoints FIN (para frontend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET    | /fin/plan-cuentas | Listar plan de cuentas (con filtros: empresa_id, cuenta_padre_id, tipo_cuenta, nivel, solo_activos, buscar). |
| GET    | /fin/plan-cuentas/{id} | Detalle de cuenta. |
| POST   | /fin/plan-cuentas | Crear cuenta (cliente_id desde contexto). |
| PUT    | /fin/plan-cuentas/{id} | Actualizar cuenta. |
| GET    | /fin/periodos | Listar periodos contables (con filtros: empresa_id, año, mes, estado). |
| GET    | /fin/periodos/{id} | Detalle de periodo. |
| POST   | /fin/periodos | Crear periodo (cliente_id desde contexto). |
| PUT    | /fin/periodos/{id} | Actualizar periodo. |
| GET    | /fin/asientos | Listar asientos contables (con filtros: empresa_id, periodo_id, tipo_asiento, estado, modulo_origen, fechas, buscar). |
| GET    | /fin/asientos/{id} | Detalle de asiento. |
| POST   | /fin/asientos | Crear asiento (cliente_id desde contexto). |
| PUT    | /fin/asientos/{id} | Actualizar asiento. |
| GET    | /fin/asientos/{id}/detalles | Listar detalles de un asiento. |
| POST   | /fin/asientos/{id}/detalles | Crear detalle de asiento. |
| GET    | /fin/asientos/detalles/{id} | Detalle de detalle. |
| PUT    | /fin/asientos/detalles/{id} | Actualizar detalle. |

### 8.4 Notas importantes

- ✅ **Todos los campos esenciales incluidos desde el inicio** en los schemas Read, Create y Update.
- ✅ El módulo FIN depende de ORG (usa org_empresa, org_centro_costo).
- ✅ Plan de cuentas incluye: código, nombre, jerarquía (cuenta_padre, nivel, ruta_jerarquica), clasificación (tipo: 'activo', 'pasivo', 'patrimonio', 'ingreso', 'gasto'), naturaleza ('deudora', 'acreedora'), configuración (acepta_movimientos, requiere_centro_costo, requiere_documento_referencia, requiere_tercero), moneda extranjera, estados financieros (balance, P&G), código SUNAT.
- ✅ Periodo contable incluye: año, mes, fechas (inicio, fin), estado ('abierto', 'cerrado', 'bloqueado'), fecha de cierre, usuario que cerró.
- ✅ Asiento contable incluye: número, fecha, periodo, tipo ('apertura', 'diario', 'ajuste', 'cierre', 'provision'), origen (módulo, documento), glosa, montos (total_debe, total_haber), validación de cuadre, estado ('borrador', 'registrado', 'aprobado', 'anulado'), aprobación, anulación.
- ✅ Asiento detalle incluye: item, cuenta, montos (debe, haber, debe_me, haber_me para moneda extranjera), glosa específica, centro de costo, documento referencia, tercero (tipo, id, nombre, documento), fecha de vencimiento.
- ✅ **Uso:** Los módulos operativos (PUR, SLS, INV, etc.) generan asientos contables automáticos. Los asientos manuales se crean desde el módulo FIN. Los periodos controlan qué periodos están abiertos para contabilizar.

---

## Módulo 9: WMS — Gestión de Almacenes (Completado)

### 9.1 Alcance

- **Tablas (TABLAS_BD_ERP_COMPLETO):** wms_zona_almacen, wms_ubicacion, wms_stock_ubicacion, wms_tarea.
- **Menú (MENU_NAVEGACION):** Zonas de Almacén, Ubicaciones, Stock por Ubicación, Tareas de Almacén.
- **Dependencias:** ORG (org_empresa), INV (inv_almacen, inv_producto, inv_unidad_medida).
- **Usado por:** Módulos que requieren control granular de ubicaciones (PUR recepción, SLS despacho, MFG producción).

### 9.2 Tareas Completadas

- [x] Crear `app/infrastructure/database/tables_erp/tables_wms.py` con las 4 tablas WMS.
- [x] Actualizar `app/infrastructure/database/tables_erp/__init__.py` para exportar tablas WMS.
- [x] Crear `app/infrastructure/database/queries/wms/zona_almacen_queries.py` con CRUD para zonas.
- [x] Crear `app/infrastructure/database/queries/wms/ubicacion_queries.py` con CRUD para ubicaciones.
- [x] Crear `app/infrastructure/database/queries/wms/stock_ubicacion_queries.py` con CRUD para stock por ubicación.
- [x] Crear `app/infrastructure/database/queries/wms/tarea_queries.py` con CRUD para tareas.
- [x] Crear `app/infrastructure/database/queries/wms/__init__.py` para exportar queries.
- [x] Crear `app/modules/wms/presentation/schemas.py` con schemas Create/Update/Read completos (todos los campos esenciales).
- [x] Crear `app/modules/wms/application/services/*.py` (4 archivos) con lógica de negocio.
- [x] Crear `app/modules/wms/presentation/endpoints_*.py` (4 archivos) con endpoints REST.
- [x] Crear `app/modules/wms/presentation/endpoints.py` como router principal.
- [x] Registrar router en `app/api/v1/api.py` con prefijo `/wms` y tags `["WMS - Gestión de Almacenes"]`.

### 9.3 Endpoints WMS (para frontend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET    | /wms/zonas | Listar zonas de almacén (con filtros: almacen_id, tipo_zona, solo_activos, buscar). |
| GET    | /wms/zonas/{id} | Detalle de zona. |
| POST   | /wms/zonas | Crear zona (cliente_id desde contexto). |
| PUT    | /wms/zonas/{id} | Actualizar zona. |
| GET    | /wms/ubicaciones | Listar ubicaciones (con filtros: almacen_id, zona_id, tipo_ubicacion, estado_ubicacion, es_ubicacion_picking, solo_activos, buscar). |
| GET    | /wms/ubicaciones/{id} | Detalle de ubicación. |
| POST   | /wms/ubicaciones | Crear ubicación (cliente_id desde contexto). |
| PUT    | /wms/ubicaciones/{id} | Actualizar ubicación. |
| GET    | /wms/stock-ubicacion | Listar stock por ubicación (con filtros: almacen_id, ubicacion_id, producto_id, estado_stock, lote). |
| GET    | /wms/stock-ubicacion/{id} | Detalle de stock por ubicación. |
| POST   | /wms/stock-ubicacion | Crear stock por ubicación (cliente_id desde contexto). |
| PUT    | /wms/stock-ubicacion/{id} | Actualizar stock por ubicación. |
| GET    | /wms/tareas | Listar tareas (con filtros: almacen_id, tipo_tarea, estado, asignado_usuario_id, producto_id, buscar). |
| GET    | /wms/tareas/{id} | Detalle de tarea. |
| POST   | /wms/tareas | Crear tarea (cliente_id desde contexto). |
| PUT    | /wms/tareas/{id} | Actualizar tarea. |

### 9.4 Notas importantes

- ✅ **Todos los campos esenciales incluidos desde el inicio** en los schemas Read, Create y Update.
- ✅ El módulo WMS depende de ORG (usa org_empresa) e INV (usa inv_almacen, inv_producto, inv_unidad_medida).
- ✅ Zonas de almacén incluyen: código, nombre, tipo ('recepcion', 'almacenaje', 'picking', 'despacho', 'cuarentena', 'merma'), control de temperatura (min/max), capacidades (m3, kg), estado.
- ✅ Ubicaciones incluyen: código jerárquico (pasillo-rack-nivel-posición), tipo ('rack', 'piso', 'estanteria', 'caja', 'pallet'), capacidades físicas (kg, m3, pallets, dimensiones), configuración (permite múltiples productos/lotes, es picking), estado ('disponible', 'ocupada', 'bloqueada', 'mantenimiento').
- ✅ Stock por ubicación incluye: cantidad, unidad de medida, lote, número de serie, fecha de vencimiento, estado ('disponible', 'reservado', 'bloqueado', 'cuarentena'), motivo de bloqueo, fechas de ingreso/actualización.
- ✅ Tareas incluyen: número, tipo ('picking', 'putaway', 'reabastecimiento', 'conteo', 'reubicacion'), prioridad (1-4), ubicaciones origen/destino, producto, cantidades (planeada/completada), referencia a documento origen, asignación (usuario, nombre, fecha), estado ('pendiente', 'asignada', 'en_proceso', 'completada', 'cancelada'), fechas (inicio, completado), instrucciones, observaciones.
- ✅ **Uso:** WMS extiende INV con control granular de ubicaciones físicas. Las zonas segmentan el almacén lógicamente. Las ubicaciones permiten saber exactamente dónde está cada producto. El stock por ubicación rastrea lotes/series por ubicación. Las tareas gestionan operaciones de almacén (picking para despachos, putaway para recepciones, reabastecimiento entre zonas).

---

## Módulo 10: QMS — Control de Calidad (Completado)

### 10.1 Alcance

- **Tablas (TABLAS_BD_ERP_COMPLETO):** qms_parametro_calidad, qms_plan_inspeccion, qms_plan_inspeccion_detalle, qms_inspeccion, qms_inspeccion_detalle, qms_no_conformidad.
- **Menú (MENU_NAVEGACION):** Parámetros de Calidad, Planes de Inspección, Inspecciones, No Conformidades.
- **Dependencias:** ORG (org_empresa), INV (inv_producto, inv_categoria_producto, inv_unidad_medida, inv_almacen).
- **Usado por:** PUR (inspección entrada), MFG (inspección producción), SLS (inspección salida).

### 10.2 Tareas Completadas

- [x] Crear `app/infrastructure/database/tables_erp/tables_qms.py` con las 6 tablas QMS.
- [x] Actualizar `app/infrastructure/database/tables_erp/__init__.py` para exportar tablas QMS.
- [x] Crear `app/infrastructure/database/queries/qms/parametro_calidad_queries.py` con CRUD para parámetros.
- [x] Crear `app/infrastructure/database/queries/qms/plan_inspeccion_queries.py` con CRUD para planes y detalles.
- [x] Crear `app/infrastructure/database/queries/qms/inspeccion_queries.py` con CRUD para inspecciones y detalles.
- [x] Crear `app/infrastructure/database/queries/qms/no_conformidad_queries.py` con CRUD para no conformidades.
- [x] Crear `app/infrastructure/database/queries/qms/__init__.py` para exportar queries.
- [x] Crear `app/modules/qms/presentation/schemas.py` con schemas Create/Update/Read completos (todos los campos esenciales).
- [x] Crear `app/modules/qms/application/services/*.py` (4 archivos) con lógica de negocio.
- [x] Crear `app/modules/qms/presentation/endpoints_*.py` (4 archivos) con endpoints REST.
- [x] Crear `app/modules/qms/presentation/endpoints.py` como router principal.
- [x] Registrar router en `app/api/v1/api.py` con prefijo `/qms` y tags `["QMS - Control de Calidad"]`.

### 10.3 Endpoints QMS (para frontend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET    | /qms/parametros-calidad | Listar parámetros de calidad (con filtros: empresa_id, tipo_parametro, solo_activos, buscar). |
| GET    | /qms/parametros-calidad/{id} | Detalle de parámetro. |
| POST   | /qms/parametros-calidad | Crear parámetro (cliente_id desde contexto). |
| PUT    | /qms/parametros-calidad/{id} | Actualizar parámetro. |
| GET    | /qms/planes-inspeccion | Listar planes de inspección (con filtros: empresa_id, producto_id, categoria_id, tipo_inspeccion, solo_activos, buscar). |
| GET    | /qms/planes-inspeccion/{id} | Detalle de plan. |
| POST   | /qms/planes-inspeccion | Crear plan (cliente_id desde contexto). |
| PUT    | /qms/planes-inspeccion/{id} | Actualizar plan. |
| GET    | /qms/planes-inspeccion/{id}/detalles | Listar detalles de un plan. |
| POST   | /qms/planes-inspeccion/{id}/detalles | Crear detalle de plan. |
| GET    | /qms/planes-inspeccion/detalles/{id} | Detalle de detalle. |
| PUT    | /qms/planes-inspeccion/detalles/{id} | Actualizar detalle. |
| GET    | /qms/inspecciones | Listar inspecciones (con filtros: empresa_id, producto_id, plan_inspeccion_id, resultado, lote, fechas, buscar). |
| GET    | /qms/inspecciones/{id} | Detalle de inspección. |
| POST   | /qms/inspecciones | Crear inspección (cliente_id desde contexto). |
| PUT    | /qms/inspecciones/{id} | Actualizar inspección. |
| GET    | /qms/inspecciones/{id}/detalles | Listar detalles de una inspección. |
| POST   | /qms/inspecciones/{id}/detalles | Crear detalle de inspección. |
| GET    | /qms/inspecciones/detalles/{id} | Detalle de detalle. |
| PUT    | /qms/inspecciones/detalles/{id} | Actualizar detalle. |
| GET    | /qms/no-conformidades | Listar no conformidades (con filtros: empresa_id, producto_id, origen, tipo_nc, estado, fechas, buscar). |
| GET    | /qms/no-conformidades/{id} | Detalle de no conformidad. |
| POST   | /qms/no-conformidades | Crear no conformidad (cliente_id desde contexto). |
| PUT    | /qms/no-conformidades/{id} | Actualizar no conformidad. |

### 10.4 Notas importantes

- ✅ **Todos los campos esenciales incluidos desde el inicio** en los schemas Read, Create y Update.
- ✅ El módulo QMS depende de ORG (usa org_empresa) e INV (usa inv_producto, inv_categoria_producto, inv_unidad_medida, inv_almacen).
- ✅ Parámetros de calidad incluyen: código, nombre, tipo ('cuantitativo', 'cualitativo', 'pasa_no_pasa'), valores (mínimo, máximo, objetivo), opciones permitidas (JSON), método de inspección, equipo requerido, estado.
- ✅ Planes de inspección incluyen: código, nombre, aplicabilidad ('producto', 'categoria', 'todos'), tipo ('recepcion', 'proceso', 'final', 'salida'), muestreo (tipo, porcentaje, tabla AQL), niveles de aceptación (críticos, mayores, menores), vigencia, estado.
- ✅ Plan detalle incluye: orden, obligatoriedad, criticidad, valores específicos del plan, instrucciones específicas.
- ✅ Inspecciones incluyen: número, fecha, plan aplicado, producto, lote, referencia a documento origen, almacén/ubicación, cantidades (total, inspeccionada, aprobada, rechazada, observada), defectos (críticos, mayores, menores), resultado ('aprobado', 'rechazado', 'aprobado_condicional', 'pendiente'), inspector, observaciones, acciones correctivas, aprobación.
- ✅ Inspección detalle incluye: parámetro inspeccionado, valor medido/cualitativo/pasa-no-pasa, cumplimiento de especificación, criticidad del defecto, observaciones.
- ✅ No conformidades incluyen: número, fecha de detección, origen ('inspeccion', 'reclamo_cliente', 'auditoria', 'proceso'), referencia a inspección/documento, producto/lote afectado, descripción, tipo ('critica', 'mayor', 'menor'), responsables, análisis de causa raíz, acciones (inmediata, correctiva, preventiva), fecha compromiso de cierre, estado ('abierta', 'en_analisis', 'en_accion', 'cerrada', 'cancelada'), fecha de cierre, verificación de eficacia.
- ✅ **Uso:** Los parámetros definen qué medir. Los planes definen qué inspeccionar y criterios de aceptación. Las inspecciones registran resultados. Las no conformidades gestionan problemas detectados con análisis de causa raíz y acciones correctivas/preventivas.

---

## Módulo 11: CRM — Customer Relationship Management (Completado)

### 11.1 Alcance

- **Tablas (TABLAS_BD_ERP_COMPLETO):** crm_campana, crm_lead, crm_oportunidad, crm_actividad.
- **Menú (MENU_NAVEGACION):** Campañas, Leads, Oportunidades, Actividades.
- **Dependencias:** ORG (org_empresa), SLS (sls_cliente).
- **Usado por:** SLS (pipeline de ventas, conversión de leads a clientes).

### 11.2 Tareas Completadas

- [x] Crear `app/infrastructure/database/tables_erp/tables_crm.py` con las 4 tablas CRM.
- [x] Actualizar `app/infrastructure/database/tables_erp/__init__.py` para exportar tablas CRM.
- [x] Crear `app/infrastructure/database/queries/crm/campana_queries.py` con CRUD para campañas.
- [x] Crear `app/infrastructure/database/queries/crm/lead_queries.py` con CRUD para leads.
- [x] Crear `app/infrastructure/database/queries/crm/oportunidad_queries.py` con CRUD para oportunidades.
- [x] Crear `app/infrastructure/database/queries/crm/actividad_queries.py` con CRUD para actividades.
- [x] Crear `app/infrastructure/database/queries/crm/__init__.py` para exportar queries.
- [x] Crear `app/modules/crm/presentation/schemas.py` con schemas Create/Update/Read completos (todos los campos esenciales).
- [x] Crear `app/modules/crm/application/services/*.py` (4 archivos) con lógica de negocio.
- [x] Crear `app/modules/crm/presentation/endpoints_*.py` (4 archivos) con endpoints REST.
- [x] Crear `app/modules/crm/presentation/endpoints.py` como router principal.
- [x] Registrar router en `app/api/v1/api.py` con prefijo `/crm` y tags `["CRM - Gestión de Clientes"]`.

### 11.3 Endpoints CRM (para frontend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET    | /crm/campanas | Listar campañas (con filtros: empresa_id, tipo_campana, estado, fechas, buscar). |
| GET    | /crm/campanas/{id} | Detalle de campaña. |
| POST   | /crm/campanas | Crear campaña (cliente_id desde contexto). |
| PUT    | /crm/campanas/{id} | Actualizar campaña. |
| GET    | /crm/leads | Listar leads (con filtros: empresa_id, campana_id, origen_lead, calificacion, estado, asignado_vendedor_usuario_id, buscar). |
| GET    | /crm/leads/{id} | Detalle de lead. |
| POST   | /crm/leads | Crear lead (cliente_id desde contexto). |
| PUT    | /crm/leads/{id} | Actualizar lead. |
| GET    | /crm/oportunidades | Listar oportunidades (con filtros: empresa_id, cliente_venta_id, lead_id, campana_id, vendedor_usuario_id, etapa, estado, tipo_oportunidad, fechas, buscar). |
| GET    | /crm/oportunidades/{id} | Detalle de oportunidad. |
| POST   | /crm/oportunidades | Crear oportunidad (cliente_id desde contexto). |
| PUT    | /crm/oportunidades/{id} | Actualizar oportunidad. |
| GET    | /crm/actividades | Listar actividades (con filtros: empresa_id, lead_id, oportunidad_id, cliente_venta_id, tipo_actividad, usuario_responsable_id, estado, fechas, buscar). |
| GET    | /crm/actividades/{id} | Detalle de actividad. |
| POST   | /crm/actividades | Crear actividad (cliente_id desde contexto). |
| PUT    | /crm/actividades/{id} | Actualizar actividad. |

### 11.4 Notas importantes

- ✅ **Todos los campos esenciales incluidos desde el inicio** en los schemas Read, Create y Update.
- ✅ El módulo CRM depende de ORG (usa org_empresa) y SLS (usa sls_cliente).
- ✅ Campañas incluyen: código, nombre, tipo ('email', 'telemarketing', 'evento', 'digital', 'mixta'), objetivo, periodo (fecha_inicio, fecha_fin), presupuesto (presupuesto, gasto_real, moneda), responsable, métricas (total_contactos, total_leads_generados, total_oportunidades, total_ventas_cerradas, monto_ventas_cerradas), estado ('planificada', 'activa', 'pausada', 'completada', 'cancelada'), observaciones.
- ✅ Leads incluyen: datos básicos (nombre_completo, empresa_nombre, cargo), contacto (telefono, telefono_movil, email), dirección, origen ('web', 'telefono', 'referido', 'evento', 'campana', 'redes_sociales'), campaña origen, calificación ('caliente', 'tibio', 'frio'), puntuación (0-100), asignación (vendedor, fecha_asignacion), estado ('nuevo', 'contactado', 'calificado', 'convertido', 'descartado'), fechas (primer_contacto, ultimo_contacto), conversión (convertido_cliente, cliente_venta_id, fecha_conversion), motivo_descarte, observaciones.
- ✅ Oportunidades incluyen: número, nombre, descripción, cliente/lead (cliente_venta_id, lead_id, nombre_cliente_prospecto), vendedor, campaña origen, valor estimado (monto_estimado, moneda, probabilidad_cierre, valor_ponderado calculado), fechas (apertura, cierre_estimada, cierre_real), etapa del pipeline ('calificacion', 'necesidad_analisis', 'propuesta', 'negociacion', 'cierre'), tipo ('nuevo_negocio', 'upselling', 'cross_selling', 'renovacion'), productos_interes (JSON), estado ('abierta', 'ganada', 'perdida', 'cancelada'), motivo_ganada/perdida, competidor, conversión (cotizacion_generada, cotizacion_id, pedido_generado, pedido_id), observaciones, proxima_accion, fecha_proxima_accion.
- ✅ Actividades incluyen: tipo ('llamada', 'reunion', 'email', 'visita', 'demo', 'cotizacion_enviada'), asunto, descripción, relación (lead_id, oportunidad_id, cliente_venta_id), fecha_actividad, duracion_minutos, responsable (usuario_responsable_id, responsable_nombre), resultado ('exitosa', 'sin_respuesta', 'reagendar', 'no_interesado'), seguimiento (requiere_seguimiento, fecha_seguimiento), estado ('planificada', 'completada', 'cancelada'), fecha_completado, observaciones.
- ✅ **Uso:** Las campañas organizan esfuerzos comerciales. Los leads son prospectos que se califican y pueden convertirse en clientes. Las oportunidades representan potenciales ventas con pipeline y probabilidades. Las actividades registran interacciones con leads/oportunidades/clientes. El flujo típico es: Campaña → Leads → Oportunidades → Cotización/Pedido (SLS).

---

## Módulo 12: POS — Punto de Venta (Completado)

### 12.1 Alcance

- **Tablas (TABLAS_BD_ERP_COMPLETO):** pos_punto_venta, pos_turno_caja, pos_venta, pos_venta_detalle.
- **Menú (MENU_NAVEGACION):** Puntos de Venta, Turnos de Caja, Ventas Rápidas.
- **Dependencias:** ORG (org_empresa, org_sucursal), INV (inv_almacen, inv_producto, inv_unidad_medida), SLS (sls_cliente), PRC (prc_lista_precio, prc_promocion), INV_BILL (invbill_comprobante).
- **Usado por:** Ventas al mostrador, retail, cierre de caja.

### 12.2 Tareas Completadas

- [x] Crear `app/infrastructure/database/tables_erp/tables_pos.py` con las 4 tablas POS.
- [x] Actualizar `app/infrastructure/database/tables_erp/__init__.py` para exportar tablas POS.
- [x] Crear `app/infrastructure/database/queries/pos/` (punto_venta_queries, turno_caja_queries, venta_queries, venta_detalle_queries) con CRUD y filtro por cliente_id.
- [x] Crear `app/modules/pos/presentation/schemas.py` con schemas Create/Update/Read para PuntoVenta, TurnoCaja, Venta, VentaDetalle.
- [x] Crear `app/modules/pos/application/services/*.py` (4 servicios) y `endpoints_*.py` (4 archivos) + `endpoints.py`.
- [x] Registrar router en `app/api/v1/api.py` con prefijo `/pos` y tags `["POS - Punto de Venta"]`.
- [x] Crear `app/docs/database/DOC_FRONTEND_MODULO_POS.md` para frontend.

### 12.3 Endpoints POS (para frontend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET    | /pos/puntos-venta | Listar puntos de venta (filtros: empresa_id, sucursal_id, estado, es_activo, buscar). |
| GET    | /pos/puntos-venta/{id} | Detalle de punto de venta. |
| POST   | /pos/puntos-venta | Crear punto de venta (cliente_id desde contexto). |
| PUT    | /pos/puntos-venta/{id} | Actualizar punto de venta. |
| GET    | /pos/turnos-caja | Listar turnos (filtros: punto_venta_id, estado, cajero_usuario_id, fecha_desde, fecha_hasta). |
| GET    | /pos/turnos-caja/{id} | Detalle de turno. |
| POST   | /pos/turnos-caja | Abrir turno (apertura con monto_apertura). |
| PUT    | /pos/turnos-caja/{id} | Cerrar/actualizar turno. |
| GET    | /pos/ventas | Listar ventas (filtros: punto_venta_id, turno_caja_id, estado, fecha_desde, fecha_hasta). |
| GET    | /pos/ventas/{id} | Detalle de venta. |
| POST   | /pos/ventas | Crear venta (cliente_id desde contexto). |
| PUT    | /pos/ventas/{id} | Actualizar venta (ej. anulación). |
| GET    | /pos/ventas-detalle | Listar detalles (filtro opcional: venta_id). |
| GET    | /pos/ventas-detalle/{id} | Detalle de línea. |
| POST   | /pos/ventas-detalle | Crear línea de venta. |
| PUT    | /pos/ventas-detalle/{id} | Actualizar línea. |

### 12.4 Notas importantes

- ✅ Punto de venta: código único por empresa, sucursal, almacén opcional, lista de precios opcional, medios de pago (efectivo, tarjeta, transferencia, yape/plin), estado (abierto/cerrado/bloqueado).
- ✅ Turno de caja: número único por punto de venta, cajero, monto apertura, cierre con monto esperado/real y totales por forma de pago y por tipo de comprobante.
- ✅ Venta: número único por punto de venta, turno, vendedor, cliente opcional, totales (subtotal, descuento, igv, total, redondeo), forma de pago y desglose, comprobante opcional, estado (borrador/completada/anulada).
- ✅ Venta detalle: item, producto, cantidad, unidad, precio, descuento %, promoción opcional, lote opcional. Subtotal/IGV/total por línea pueden calcularse en frontend o en BD (columnas calculadas).
- ✅ **Uso:** Configurar puntos de venta por sucursal; abrir turnos con fondo; registrar ventas y líneas; cerrar turno con arqueo. Integrar con INV_BILL para emitir comprobantes.

---

## Módulo 13: HCM — Human Capital Management (Planillas y RRHH) (Completado)

### 13.1 Alcance

- **Tablas (TABLAS_BD_ERP_COMPLETO):** hcm_empleado, hcm_contrato, hcm_concepto_planilla, hcm_planilla, hcm_planilla_empleado, hcm_planilla_detalle, hcm_asistencia, hcm_vacaciones, hcm_prestamo.
- **Menú (MENU_NAVEGACION):** Empleados, Contratos, Conceptos de Planilla, Planillas, Asistencia, Vacaciones, Préstamos.
- **Dependencias:** ORG (org_empresa, org_departamento, org_cargo, org_sucursal, org_centro_costo).
- **Usado por:** FIN (contabilidad de planilla), costos laborales.

### 13.2 Tareas Completadas

- [x] Crear `app/infrastructure/database/tables_erp/tables_hcm.py` con las 9 tablas HCM.
- [x] Actualizar `tables_erp/__init__.py` para exportar tablas HCM.
- [x] Crear `app/infrastructure/database/queries/hcm/` (empleado, contrato, concepto_planilla, planilla, planilla_empleado, planilla_detalle, asistencia, vacaciones, prestamo) con CRUD y filtro por cliente_id.
- [x] Crear `app/modules/hcm/presentation/schemas.py` con Create/Update/Read para las 9 entidades.
- [x] Crear `app/modules/hcm/application/services/*.py` (9 servicios) y `presentation/endpoints_*.py` (9 archivos) + `endpoints.py`.
- [x] Registrar router en `app/api/v1/api.py` con prefijo `/hcm` y tags `["HCM - Planillas y RRHH"]`.
- [x] Crear `app/docs/database/DOC_FRONTEND_MODULO_HCM.md` para frontend.

### 13.3 Endpoints HCM (para frontend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET/POST/PUT | /hcm/empleados, /{id} | CRUD empleados (filtros: empresa_id, estado_empleado, es_activo, departamento_id, cargo_id, buscar). |
| GET/POST/PUT | /hcm/contratos, /{id} | CRUD contratos (filtros: empresa_id, empleado_id, estado_contrato, es_contrato_vigente). |
| GET/POST/PUT | /hcm/conceptos-planilla, /{id} | CRUD conceptos (filtros: empresa_id, tipo_concepto, es_activo, buscar). |
| GET/POST/PUT | /hcm/planillas, /{id} | CRUD planillas (filtros: empresa_id, tipo_planilla, estado, año, mes). |
| GET/POST/PUT | /hcm/planilla-empleados, /{id} | CRUD planilla-empleados (filtros: planilla_id, empleado_id). |
| GET/POST/PUT | /hcm/planilla-detalle, /{id} | CRUD detalle conceptos (filtros: planilla_empleado_id, tipo_concepto). |
| GET/POST/PUT | /hcm/asistencia, /{id} | CRUD asistencia (filtros: empresa_id, empleado_id, fecha_desde, fecha_hasta, tipo_asistencia). |
| GET/POST/PUT | /hcm/vacaciones, /{id} | CRUD vacaciones (filtros: empresa_id, empleado_id, estado, año_periodo). |
| GET/POST/PUT | /hcm/prestamos, /{id} | CRUD préstamos (filtros: empresa_id, empleado_id, estado). |

### 13.4 Notas importantes

- ✅ Empleado: datos personales, documento, AFP/ONP, banco, cargo, departamento, sucursal, centro de costo, jefe directo, estado (activo/inactivo/cesado).
- ✅ Contrato: tipo (plazo indeterminado, plazo fijo, part-time, etc.), vigencia, remuneración, periodo de prueba, CTS, gratificación, estado (vigente/vencido/rescindido).
- ✅ Concepto planilla: tipo (ingreso, descuento, aporte_empleador), monto fijo o porcentaje, base de cálculo, afectaciones (renta 5ta, ESSALUD, CTS, gratificación, vacaciones), código PLAME.
- ✅ Planilla: periodo (año, mes), tipo (mensual, quincenal, gratificación, CTS, utilidades), totales, estado (borrador → calculada → aprobada → pagada → cerrada), integración PLAME y asiento contable opcional.
- ✅ Planilla empleado: resumen por empleado (días, horas, remuneración base, totales, neto a pagar, pagado). Planilla detalle: líneas de concepto por empleado (concepto_id, monto).
- ✅ Asistencia: un registro por (empleado, fecha); marcaciones entrada/salida, horas trabajadas/extras, tipo (presente, falta, tardanza, licencia, vacaciones), justificación.
- ✅ Vacaciones: por empleado y año periodo; días ganados/tomados, programación y estado (pendiente, programada, aprobada, en_curso, completada, vencida).
- ✅ Préstamo: tipo (adelanto sueldo, préstamo, adelanto gratificación), monto, cuotas, estado (activo, pagado, cancelado); descuento en planilla vía conceptos.
- ✅ **Uso:** Maestro de empleados y contratos; catálogo de conceptos; generación de planillas mensuales/gratificación/CTS; control de asistencia; control de vacaciones y préstamos con descuento en planilla.

---

## Módulo 14: MFG — Manufactura y Producción (Completado)

### 14.1 Alcance

- **Tablas (TABLAS_BD_ERP_COMPLETO):** mfg_centro_trabajo, mfg_operacion, mfg_lista_materiales, mfg_lista_materiales_detalle, mfg_ruta_fabricacion, mfg_ruta_fabricacion_detalle, mfg_orden_produccion, mfg_orden_produccion_operacion, mfg_consumo_materiales.
- **Menú (MENU_NAVEGACION):** Centros de Trabajo, Operaciones, Lista de Materiales (BOM), Rutas de Fabricación, Órdenes de Producción, Consumo de Materiales, Operaciones de OP.
- **Dependencias:** ORG (empresa, sucursal, centro_costo), INV (producto, unidad_medida, almacen).
- **Usado por:** MRP (explosión BOM), WMS (salidas por consumo), FIN (costos de producción).

### 14.2 Tareas Completadas

- [x] Crear `app/infrastructure/database/tables_erp/tables_mfg.py` con las 9 tablas MFG.
- [x] Actualizar `tables_erp/__init__.py` para exportar tablas MFG.
- [x] Crear `app/infrastructure/database/queries/mfg/` (centro_trabajo, operacion, lista_materiales, lista_materiales_detalle, ruta_fabricacion, ruta_fabricacion_detalle, orden_produccion, orden_produccion_operacion, consumo_materiales) con CRUD y filtro por cliente_id.
- [x] Crear `app/modules/mfg/presentation/schemas.py` con Create/Update/Read para las 9 entidades.
- [x] Crear `app/modules/mfg/application/services/*.py` (9 servicios) y `presentation/endpoints_*.py` (9 archivos) + `endpoints.py`.
- [x] Registrar router en `app/api/v1/api.py` con prefijo `/mfg` y tags `["MFG - Manufactura y Producción"]`.
- [x] Crear `app/docs/database/DOC_FRONTEND_MODULO_MFG.md` para frontend.

### 14.3 Endpoints MFG (para frontend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET/POST/PUT | /mfg/centros-trabajo, /{id} | CRUD centros de trabajo (filtros: empresa_id, estado_centro, es_activo, buscar). |
| GET/POST/PUT | /mfg/operaciones, /{id} | CRUD operaciones (filtros: empresa_id, centro_trabajo_id, es_activo, buscar). |
| GET/POST/PUT | /mfg/listas-materiales, /{id} | CRUD listas de materiales / BOM (filtros: empresa_id, producto_id, es_bom_activa, estado, buscar). |
| GET/POST/PUT | /mfg/lista-materiales-detalle, /{id} | CRUD detalle BOM (filtro: bom_id). |
| GET/POST/PUT | /mfg/rutas-fabricacion, /{id} | CRUD rutas de fabricación (filtros: empresa_id, producto_id, es_ruta_activa, estado, buscar). |
| GET/POST/PUT | /mfg/ruta-fabricacion-detalle, /{id} | CRUD detalle ruta (filtro: ruta_id). |
| GET/POST/PUT | /mfg/ordenes-produccion, /{id} | CRUD órdenes de producción (filtros: empresa_id, producto_id, estado, fecha_desde, fecha_hasta). |
| GET/POST/PUT | /mfg/orden-produccion-operaciones, /{id} | CRUD operaciones por OP (filtros: orden_produccion_id, centro_trabajo_id, estado). |
| GET/POST/PUT | /mfg/consumo-materiales, /{id} | CRUD consumo de materiales (filtros: orden_produccion_id, producto_id). |

### 14.4 Notas importantes

- ✅ Centros de trabajo: máquinas/estaciones (tipo_centro, capacidad, eficiencia, costo_hora, estado_centro: disponible/mantenimiento/ocupado).
- ✅ Operaciones: procesos (corte, armado, empaque) vinculados a centro de trabajo; tiempos setup y operación.
- ✅ BOM: producto padre, versión, vigencia, cantidad_base, tipo_bom (produccion/ingenieria); detalle con componentes, cantidad, tipo_componente (material/semielaborado).
- ✅ Ruta de fabricación: secuencia de operaciones por producto; detalle con operacion_id, centro_trabajo_id, tiempos, secuencia.
- ✅ Orden de producción: numero_op, fechas programadas/reales, producto, BOM, ruta, cantidades (planeada/producida/defectuosa), costos (materiales, MO, CIF), estado (borrador/liberada/en_proceso/terminada).
- ✅ Operaciones de OP: avance por operación (tiempos reales, cantidad procesada/aprobada/rechazada, operario, estado).
- ✅ Consumo materiales: materiales consumidos por OP (cantidad planificada/consumida, movimiento inventario opcional).
- ✅ **Uso:** Configurar centros y operaciones; definir BOM y rutas; emitir y ejecutar órdenes de producción; registrar consumo y avance por operación.

---

## Módulo 15: MRP — Planeamiento de Materiales (Completado)

### 15.1 Alcance

- **Tablas (TABLAS_BD_ERP_COMPLETO):** mrp_plan_maestro, mrp_necesidad_bruta, mrp_explosion_materiales, mrp_orden_sugerida.
- **Menú (MENU_NAVEGACION):** Plan Maestro MRP, Necesidades Brutas, Explosión de Materiales, Órdenes Sugeridas.
- **Dependencias:** ORG (empresa), INV (producto, unidad_medida), MFG (BOM para explosión), PUR (proveedor opcional en orden sugerida).
- **Usado por:** Conversión de órdenes sugeridas en OC o OP; integración con MPS (pronósticos como entrada).

### 15.2 Tareas Completadas

- [x] Crear `app/infrastructure/database/tables_erp/tables_mrp.py` con las 4 tablas MRP.
- [x] Actualizar `tables_erp/__init__.py` para exportar tablas MRP.
- [x] Crear `app/infrastructure/database/queries/mrp/` (plan_maestro, necesidad_bruta, explosion_materiales, orden_sugerida) con CRUD y filtro por cliente_id.
- [x] Crear `app/modules/mrp/presentation/schemas.py` con Create/Update/Read para las 4 entidades.
- [x] Crear `app/modules/mrp/application/services/*.py` (4 servicios) y `presentation/endpoints_*.py` (4 archivos) + `endpoints.py`.
- [x] Registrar router en `app/api/v1/api.py` con prefijo `/mrp` y tags `["MRP - Planeamiento de Materiales"]`.
- [x] Crear `app/docs/database/DOC_FRONTEND_MODULO_MRP.md` para frontend.

### 15.3 Endpoints MRP (para frontend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET/POST/PUT | /mrp/plan-maestro, /{id} | CRUD plan maestro (filtros: empresa_id, estado, buscar). |
| GET/POST/PUT | /mrp/necesidades-brutas, /{id} | CRUD necesidades brutas (filtros: plan_maestro_id, producto_id, origen). |
| GET/POST/PUT | /mrp/explosion-materiales, /{id} | CRUD explosión materiales (filtros: plan_maestro_id, producto_componente_id, nivel_bom). |
| GET/POST/PUT | /mrp/ordenes-sugeridas, /{id} | CRUD órdenes sugeridas (filtros: plan_maestro_id, producto_id, estado, tipo_orden). |

### 15.4 Notas importantes

- ✅ Plan maestro: horizonte de planificación (fecha_inicio, fecha_fin), tipo_periodo (diario, semanal, mensual), estado (borrador, calculado, aprobado, ejecutado, cerrado), totales (productos planificados, requisiciones, órdenes sugeridas).
- ✅ Necesidad bruta: entrada al MRP por plan (producto, fecha_requerida, cantidad), origen (pedido_venta, pronostico, stock_seguridad, orden_produccion), documento_origen opcional.
- ✅ Explosión materiales: resultado de explosión BOM (producto_padre, producto_componente, nivel_bom, cantidad_necesaria, stock_actual/reservado/tránsito); la API devuelve stock_disponible y cantidad_a_ordenar calculados.
- ✅ Orden sugerida: tipo_orden (compra, produccion, transferencia), cantidad_sugerida, fechas, proveedor_sugerido_id, estado (sugerida, aprobada, convertida, rechazada), documento_generado_tipo/id al convertir.
- ✅ **Uso:** Crear plan maestro; cargar necesidades brutas (manual o desde MPS/pedidos); ejecutar explosión (proceso batch típico); listar órdenes sugeridas y convertirlas en OC o OP.

---

## Módulo 16: MPS — Plan Maestro de Producción (Completado)

### 16.1 Alcance

- **Tablas (TABLAS_BD_ERP_COMPLETO):** mps_pronostico_demanda, mps_plan_produccion, mps_plan_produccion_detalle.
- **Menú (MENU_NAVEGACION):** Pronóstico de Demanda, Plan de Producción (y detalle por producto/periodo).
- **Dependencias:** ORG (empresa), INV (producto, unidad_medida).
- **Usado por:** MRP (necesidades brutas desde pronóstico); entrada para planificación agregada.

### 16.2 Tareas Completadas

- [x] Crear `app/infrastructure/database/tables_erp/tables_mps.py` con las 3 tablas MPS.
- [x] Actualizar `tables_erp/__init__.py` para exportar tablas MPS.
- [x] Crear `app/infrastructure/database/queries/mps/` (pronostico_demanda, plan_produccion, plan_produccion_detalle) con CRUD y filtro por cliente_id.
- [x] Crear `app/modules/mps/presentation/schemas.py` con Create/Update/Read para las 3 entidades (API usa `anio`; BD usa `año`).
- [x] Crear `app/modules/mps/application/services/*.py` (3 servicios) y `presentation/endpoints_*.py` (3 archivos) + `endpoints.py`.
- [x] Registrar router en `app/api/v1/api.py` con prefijo `/mps` y tags `["MPS - Plan Maestro de Producción"]`.
- [x] Crear `app/docs/database/DOC_FRONTEND_MODULO_MPS.md` para frontend.

### 16.3 Endpoints MPS (para frontend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET/POST/PUT | /mps/pronostico-demanda, /{id} | CRUD pronóstico demanda (filtros: empresa_id, producto_id, anio, mes). |
| GET/POST/PUT | /mps/plan-produccion, /{id} | CRUD plan de producción (filtros: empresa_id, estado, buscar). |
| GET/POST/PUT | /mps/plan-produccion-detalle, /{id} | CRUD detalle plan por producto/periodo (filtros: plan_produccion_id, producto_id). |

### 16.4 Notas importantes

- ✅ Pronóstico demanda: producto, periodo (año, mes, semana, fecha_inicio/fin), cantidad_pronosticada, metodo_pronostico (historico, tendencia, estacional, manual), confiabilidad_porcentaje; cantidad_real y desviación para análisis. En la API el año se envía/recibe como `anio`.
- ✅ Plan producción: codigo_plan, nombre, fecha_inicio/fin, estado (borrador, aprobado, ejecutado, cerrado), aprobado_por_usuario_id.
- ✅ Plan detalle: por plan y producto, fechas, pronostico_demanda, pedidos_firmes, stock_inicial, stock_seguridad, cantidad_planificada, cantidad_producida, capacidad_disponible; la API devuelve porcentaje_uso_capacidad calculado.
- ✅ **Uso:** Registrar pronósticos por producto/periodo; crear planes de producción y su detalle; alimentar MRP con necesidades desde pronóstico.

---

## Módulo 17: MNT — Mantenimiento de Activos (Completado)

### 17.1 Alcance

- **Tablas (TABLAS_BD_ERP_COMPLETO):** mnt_activo, mnt_plan_mantenimiento, mnt_orden_trabajo, mnt_historial_mantenimiento.
- **Menú (MENU_NAVEGACION):** Activos, Planes de Mantenimiento, Órdenes de Trabajo, Historial de Mantenimiento.
- **Dependencias:** ORG (empresa, sucursal), MFG (centro_trabajo opcional), LOG (vehiculo opcional), PUR (proveedor opcional).
- **Usado por:** Control de disponibilidad de equipos; trazabilidad de intervenciones.

### 17.2 Tareas Completadas

- [x] Crear `app/infrastructure/database/tables_erp/tables_mnt.py` con las 4 tablas MNT.
- [x] Actualizar `tables_erp/__init__.py` para exportar tablas MNT.
- [x] Crear `app/infrastructure/database/queries/mnt/` (activo, plan_mantenimiento, orden_trabajo, historial_mantenimiento) con CRUD y filtro por cliente_id.
- [x] Crear `app/modules/mnt/presentation/schemas.py` con Create/Update/Read para las 4 entidades (API usa `anio_fabricacion` en activo).
- [x] Crear `app/modules/mnt/application/services/*.py` (4 servicios) y `presentation/endpoints_*.py` (4 archivos) + `endpoints.py`.
- [x] Registrar router en `app/api/v1/api.py` con prefijo `/mnt` y tags `["MNT - Mantenimiento"]`.
- [x] Crear `app/docs/database/DOC_FRONTEND_MODULO_MNT.md` para frontend.

### 17.3 Endpoints MNT (para frontend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET/POST/PUT | /mnt/activos, /{id} | CRUD activos (filtros: empresa_id, tipo_activo, estado_activo, criticidad, es_activo, buscar). |
| GET/POST/PUT | /mnt/planes-mantenimiento, /{id} | CRUD planes (filtros: activo_id, tipo_mantenimiento, es_activo, buscar). |
| GET/POST/PUT | /mnt/ordenes-trabajo, /{id} | CRUD órdenes de trabajo (filtros: empresa_id, activo_id, estado, tipo_mantenimiento, buscar). |
| GET/POST/PUT | /mnt/historial-mantenimiento, /{id} | CRUD historial (filtros: activo_id, orden_trabajo_id, tipo_mantenimiento). |

### 17.4 Notas importantes

- ✅ Activo: codigo_activo, nombre, tipo_activo (maquinaria, vehiculo, equipo, instalacion, herramienta), centro_trabajo_id (MFG), vehiculo_id (LOG), criticidad (critica, alta, media, baja), estado_activo (operativo, mantenimiento, averiado, baja). En API el año de fabricación se envía/recibe como `anio_fabricacion`.
- ✅ Plan mantenimiento: por activo, tipo (preventivo, predictivo), frecuencia_tipo (dias, horas_uso, kilometros, ciclos), frecuencia_valor, fecha_proximo_mantenimiento, tareas_mantenimiento (JSON/texto).
- ✅ Orden trabajo: numero_ot, activo, plan_mantenimiento_id opcional, tipo (preventivo, correctivo, predictivo, modificacion), prioridad, trabajo_a_realizar, tecnico, fechas programada/inicio_real/fin_real; la API devuelve duracion_horas y costo_total calculados.
- ✅ Historial: por activo, orden_trabajo_id opcional, fecha_mantenimiento, tipo, descripcion_trabajo, costo_total.
- ✅ **Uso:** Maestro de activos; planes preventivos/predictivos; programar y ejecutar OT; registrar historial de intervenciones.

---

## Módulo 18: CST — Costeo de Productos (Completado)

### 18.1 Alcance

- **Tablas (TABLAS_BD_ERP_COMPLETO):** cst_centro_costo_tipo, cst_producto_costo.
- **Menú (MENU_NAVEGACION):** Tipos de Centro de Costo, Costo de Productos, Análisis de Variaciones (los dos primeros con tabla; análisis puede ser solo lógica/UI).
- **Dependencias:** ORG (empresa), INV (producto). Opcional: MFG (orden_produccion_id).
- **Usado por:** Clasificación de centros de costo; costeo por producto/año/mes (material directo, mano de obra, CIF); costo unitario y total calculados en servicio.

### 18.2 Tareas Completadas

- [x] Crear `app/infrastructure/database/tables_erp/tables_cst.py` con las 2 tablas CST.
- [x] Actualizar `tables_erp/__init__.py` para exportar tablas CST.
- [x] Crear `app/infrastructure/database/queries/cst/` (centro_costo_tipo, producto_costo) con CRUD y filtro por cliente_id.
- [x] Crear `app/modules/cst/presentation/schemas.py` con Create/Update/Read para ambas entidades (API usa `anio` en producto_costo; Read incluye costo_total y costo_unitario calculados).
- [x] Crear `app/modules/cst/application/services/*.py` (2 servicios) y `presentation/endpoints_*.py` + `endpoints.py`.
- [x] Registrar router en `app/api/v1/api.py` con prefijo `/cst` y tags `["CST - Costeo de Productos"]`.
- [x] Crear `app/docs/database/DOC_FRONTEND_MODULO_CST.md` para frontend.

### 18.3 Endpoints CST (para frontend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET/POST/PUT | /cst/tipos-centro-costo, /{cc_tipo_id} | CRUD tipos centro costo (filtros: empresa_id, tipo_clasificacion, es_activo, buscar). |
| GET/POST/PUT | /cst/producto-costo, /{producto_costo_id} | CRUD costo de productos (filtros: empresa_id, producto_id, anio, mes, metodo_costeo). Año en API: `anio`; respuesta incluye costo_total y costo_unitario. |

### 18.4 Notas importantes

- ✅ Centro costo tipo: codigo, nombre, tipo_clasificacion (productivo, servicio, administrativo), base_distribucion (horas_hombre, unidades_producidas, ventas, area_m2), es_activo.
- ✅ Producto costo: producto_id, **anio**, mes (API usa `anio`; BD columna `año`), costo_material_directo, costo_mano_obra_directa, costo_indirecto_fabricacion, cantidad_producida, orden_produccion_id (opcional), metodo_costeo (real, estandar, promedio), observaciones. La API devuelve **costo_total** (suma de los 3 costos) y **costo_unitario** (costo_total/cantidad_producida) calculados.
- ✅ **Uso:** Maestro de tipos de centro de costo; registro de costos por producto/periodo; análisis de variaciones (real vs estándar) puede consumir estos datos desde frontend.

---

## Módulo 19: TAX — Libros Electrónicos / PLE SUNAT (Completado)

### 19.1 Alcance

- **Tablas (TABLAS_BD_ERP_COMPLETO):** tax_libro_electronico.
- **Menú (MENU_NAVEGACION):** PLE SUNAT (generar TXT, registro compras/ventas).
- **Dependencias:** ORG (empresa), FIN (periodo_contable).
- **Usado por:** Generación de libros para PLE SUNAT; estado de envío y respuesta SUNAT.

### 19.2 Tareas Completadas

- [x] Crear `app/infrastructure/database/tables_erp/tables_tax.py` con la tabla tax_libro_electronico.
- [x] Actualizar `tables_erp/__init__.py` para exportar TaxLibroElectronicoTable.
- [x] Crear `app/infrastructure/database/queries/tax/libro_electronico_queries.py` con CRUD y filtro por cliente_id.
- [x] Crear `app/modules/tax/presentation/schemas.py` con Create/Update/Read (API usa `anio`; BD columna `año`).
- [x] Crear `app/modules/tax/application/services/libro_electronico_service.py` y `presentation/endpoints_libro_electronico.py` + `endpoints.py`.
- [x] Registrar router en `app/api/v1/api.py` con prefijo `/tax` y tags `["TAX - Libros Electrónicos"]`.
- [x] Crear `app/docs/database/DOC_FRONTEND_MODULO_TAX.md` para frontend.

### 19.3 Endpoints TAX (para frontend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET/POST/PUT | /tax/libros-electronicos, /{libro_id} | CRUD libros electrónicos (filtros: empresa_id, tipo_libro, anio, mes, estado). Año en API: `anio`. |

### 19.4 Notas importantes

- ✅ Libro electrónico: tipo_libro (ventas, compras, diario, mayor, inventarios), periodo_id (FK fin_periodo_contable), **anio**, mes, nombre_archivo, ruta_archivo, estado (generado, enviado, aceptado, rechazado), fecha_envio_sunat, codigo_respuesta_sunat, total_registros, observaciones, generado_por_usuario_id.
- ✅ **Uso:** Registrar generación de libros PLE; actualizar estado tras envío a SUNAT; listar por empresa/periodo/tipo para pantalla PLE SUNAT.

---

## Módulo 20: BDG — Presupuestos (Completado)

### 20.1 Alcance

- **Tablas (TABLAS_BD_ERP_COMPLETO):** bdg_presupuesto, bdg_presupuesto_detalle.
- **Menú (MENU_NAVEGACION):** Presupuestos, Ejecución Presupuestal (real vs presupuestado, alertas).
- **Dependencias:** ORG (empresa, centro_costo), FIN (plan_cuentas).
- **Usado por:** Control presupuestario; detalle por cuenta y centro de costo; comparativa real vs presupuestado.

### 20.2 Tareas Completadas

- [x] Crear `app/infrastructure/database/tables_erp/tables_bdg.py` con las 2 tablas BDG.
- [x] Actualizar `tables_erp/__init__.py` para exportar BdgPresupuestoTable y BdgPresupuestoDetalleTable.
- [x] Crear `app/infrastructure/database/queries/bdg/` (presupuesto, presupuesto_detalle) con CRUD y filtro por cliente_id.
- [x] Crear `app/modules/bdg/presentation/schemas.py` con Create/Update/Read para ambas entidades (API usa `anio` en presupuesto; Read incluye porcentaje_ejecucion y monto_disponible calculados).
- [x] Crear servicios y endpoints (presupuesto, presupuesto_detalle); registrar router en `app/api/v1/api.py` con prefijo `/bdg`.
- [x] Crear `app/docs/database/DOC_FRONTEND_MODULO_BDG.md` para frontend.

### 20.3 Endpoints BDG (para frontend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET/POST/PUT | /bdg/presupuestos, /{presupuesto_id} | CRUD presupuesto cabecera (filtros: empresa_id, anio, tipo_presupuesto, estado, buscar). Respuesta: porcentaje_ejecucion. |
| GET/POST/PUT | /bdg/presupuesto-detalle, /{presupuesto_detalle_id} | CRUD detalle por cuenta/centro de costo/mes (filtros: presupuesto_id, cuenta_id, centro_costo_id, mes). Respuesta: monto_disponible. |

### 20.4 Notas importantes

- ✅ Presupuesto: codigo_presupuesto, nombre, **anio**, tipo_presupuesto (anual, mensual, trimestral), monto_total_presupuestado, monto_total_ejecutado, estado (borrador, aprobado, vigente, cerrado), fecha_aprobacion. La API devuelve **porcentaje_ejecucion** calculado (monto_total_ejecutado/monto_total_presupuestado*100).
- ✅ Presupuesto detalle: presupuesto_id, cuenta_id (FIN), centro_costo_id (ORG, opcional), mes (opcional; NULL si anual consolidado), monto_presupuestado, monto_ejecutado. La API devuelve **monto_disponible** (monto_presupuestado - monto_ejecutado).
- ✅ **Uso:** Crear presupuestos anuales/mensuales; cargar detalle por cuenta y centro de costo; pantalla Ejecución Presupuestal con real vs presupuestado y alertas de sobregiro.

---

## Módulo 21: PM — Gestión de Proyectos (Completado)

### 21.1 Alcance

- **Tablas (TABLAS_BD_ERP_COMPLETO):** pm_proyecto.
- **Menú (MENU_NAVEGACION):** Proyectos (crear con presupuesto, vincular gastos reales), Seguimiento (presupuesto vs costo real, % avance).
- **Dependencias:** ORG (empresa). Opcional: SLS (cliente_venta_id).
- **Usado por:** Control de proyectos; presupuesto vs costo real; seguimiento por estado.

### 21.2 Tareas Completadas

- [x] Crear `app/infrastructure/database/tables_erp/tables_pm.py` con la tabla pm_proyecto.
- [x] Actualizar `tables_erp/__init__.py` para exportar PmProyectoTable.
- [x] Crear `app/infrastructure/database/queries/pm/proyecto_queries.py` con CRUD y filtro por cliente_id.
- [x] Crear `app/modules/pm/presentation/schemas.py` con Create/Update/Read para proyecto.
- [x] Crear servicio y endpoints; registrar router en `app/api/v1/api.py` con prefijo `/pm`.
- [x] Crear `app/docs/database/DOC_FRONTEND_MODULO_PM.md` para frontend.

### 21.3 Endpoints PM (para frontend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET/POST/PUT | /pm/proyectos, /{proyecto_id} | CRUD proyectos (filtros: empresa_id, estado, cliente_venta_id, buscar). |

### 21.4 Notas importantes

- ✅ Proyecto: codigo_proyecto, nombre, descripcion, cliente_venta_id (opcional), fecha_inicio, fecha_fin_estimada, fecha_fin_real, presupuesto, costo_real, responsable_usuario_id, estado (planificado, en_curso, pausado, completado, cancelado).
- ✅ **Uso:** Crear proyectos con presupuesto; actualizar costo_real desde otros módulos o manualmente; pantalla Seguimiento comparando presupuesto vs real y % avance (calcular en frontend: costo_real/presupuesto*100 si presupuesto > 0).

---

## Módulo 22: SVC — Órdenes de Servicio (Completado)

### 22.1 Alcance

- **Tablas (TABLAS_BD_ERP_COMPLETO):** svc_orden_servicio.
- **Menú (MENU_NAVEGACION):** Órdenes de Servicio (internos/postventa, externos/talleres), Envío a Talleres, Stock en Terceros (estos dos pueden ser UI que consumen órdenes u otros endpoints futuros).
- **Dependencias:** ORG (empresa). Opcional: SLS (cliente_venta_id).
- **Usado por:** Servicios internos y externos; seguimiento por estado; monto de servicio.

### 22.2 Tareas Completadas

- [x] Crear `app/infrastructure/database/tables_erp/tables_svc.py` con la tabla svc_orden_servicio.
- [x] Actualizar `tables_erp/__init__.py` para exportar SvcOrdenServicioTable.
- [x] Crear `app/infrastructure/database/queries/svc/orden_servicio_queries.py` con CRUD y filtro por cliente_id.
- [x] Crear `app/modules/svc/presentation/schemas.py` con Create/Update/Read para orden de servicio.
- [x] Crear servicio y endpoints; registrar router en `app/api/v1/api.py` con prefijo `/svc`.
- [x] Crear `app/docs/database/DOC_FRONTEND_MODULO_SVC.md` para frontend.

### 22.3 Endpoints SVC (para frontend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET/POST/PUT | /svc/ordenes-servicio, /{orden_servicio_id} | CRUD órdenes de servicio (filtros: empresa_id, estado, cliente_venta_id, tipo_servicio, buscar). |

### 22.4 Notas importantes

- ✅ Orden servicio: numero_os, fecha_solicitud, cliente_venta_id (opcional), tipo_servicio, descripcion_servicio, tecnico_asignado_usuario_id, fecha_inicio_programada, fecha_inicio_real, fecha_fin_real, estado (solicitada, asignada, en_proceso, completada, cancelada), monto_servicio.
- ✅ **Uso:** Crear y seguir órdenes de servicio (postventa, talleres, tercerización); actualizar estado y fechas reales; pantallas Envío a Talleres y Stock en Terceros pueden consumir estos datos o extenderse con tablas propias en el futuro.

---

## Módulo 23: TKT — Mesa de Ayuda / Ticketing (Completado)

### 23.1 Alcance

- **Tablas (TABLAS_BD_ERP_COMPLETO):** tkt_ticket.
- **Menú (MENU_NAVEGACION):** Tickets (crear, prioridad, SLA, tiempo de resolución).
- **Dependencias:** ORG (empresa).
- **Usado por:** Soporte interno; prioridades y categorías; tiempo de resolución calculado.

### 23.2 Tareas Completadas

- [x] Crear `app/infrastructure/database/tables_erp/tables_tkt.py` con la tabla tkt_ticket.
- [x] Actualizar `tables_erp/__init__.py` para exportar TktTicketTable (import + __all__).
- [x] Crear `app/infrastructure/database/queries/tkt/ticket_queries.py` con CRUD y filtro por cliente_id.
- [x] Crear `app/modules/tkt/presentation/schemas.py` con Create/Update/Read (Read incluye tiempo_resolucion_horas calculado).
- [x] Crear servicio y endpoints; registrar router en `app/api/v1/api.py` con prefijo `/tkt`.
- [x] Crear `app/docs/database/DOC_FRONTEND_MODULO_TKT.md` para frontend.

### 23.3 Endpoints TKT (para frontend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET/POST/PUT | /tkt/tickets, /{ticket_id} | CRUD tickets (filtros: empresa_id, estado, prioridad, categoria, asignado_usuario_id, buscar). Respuesta: tiempo_resolucion_horas (calculado). |

### 23.4 Notas importantes

- ✅ Ticket: numero_ticket, solicitante_*, asunto, descripcion, categoria (soporte_tecnico, consulta, incidencia, requerimiento), prioridad (urgente, alta, media, baja), asignado_usuario_id, fecha_asignacion, estado (abierto, asignado, en_proceso, resuelto, cerrado), fecha_resolucion, solucion. La API devuelve **tiempo_resolucion_horas** calculado (diferencia en horas entre fecha_creacion y fecha_resolucion cuando existe fecha_resolucion).
- ✅ **Uso:** Crear tickets de soporte; asignar y cambiar estado; registrar solución y fecha_resolucion; SLA/tiempo de resolución para reportes.

---

## Módulo 24: DMS — Gestión Documental (Completado)

### 24.1 Alcance

- **Tablas (TABLAS_BD_ERP_COMPLETO):** dms_documento.
- **Menú (MENU_NAVEGACION):** Documentos (subir, versionamiento, control acceso), Búsqueda (nombre, tipo, fecha, etiquetas).
- **Dependencias:** ORG (empresa).
- **Usado por:** Almacenamiento de metadatos de documentos; versionamiento (documento_padre_id); vinculación a entidades (entidad_tipo, entidad_id); nivel de acceso.

### 24.2 Tareas Completadas

- [x] Crear `app/infrastructure/database/tables_erp/tables_dms.py` con la tabla dms_documento (incl. FK self documento_padre_id).
- [x] Actualizar `tables_erp/__init__.py` para importar y exportar DmsDocumentoTable.
- [x] Crear `app/infrastructure/database/queries/dms/documento_queries.py` con CRUD y filtro por cliente_id.
- [x] Crear schemas con Create/Update/Read (API usa `tamano_bytes`; BD columna `tamaño_bytes`; conversión en servicio).
- [x] Crear servicio y endpoints; registrar router en `app/api/v1/api.py` con prefijo `/dms`.
- [x] Crear `app/docs/database/DOC_FRONTEND_MODULO_DMS.md` para frontend.

### 24.3 Endpoints DMS (para frontend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET/POST/PUT | /dms/documentos, /{documento_id} | CRUD documentos (filtros: empresa_id, tipo_documento, categoria, estado, entidad_tipo, entidad_id, carpeta, buscar). API: tamano_bytes. |

### 24.4 Notas importantes

- ✅ Documento: codigo_documento, nombre_archivo, descripcion, tipo_documento, categoria, ruta_archivo, **tamano_bytes** (API) / tamaño_bytes (BD), extension, mime_type, carpeta, tags (JSON), entidad_tipo, entidad_id, version, documento_padre_id (versionamiento), es_confidencial, nivel_acceso (publico, general, restringido, confidencial), estado (activo, archivado, eliminado), subido_por_usuario_id.
- ✅ **Uso:** Registrar metadatos de documentos (el archivo físico se sube por otro medio; ruta_archivo indica ubicación); versionamiento vía documento_padre_id; búsqueda por tipo, categoría, carpeta, etiquetas.

---

## Módulo 25: WFL — Flujos de Trabajo (Completado)

### 25.1 Alcance

- **Tablas (TABLAS_BD_ERP_COMPLETO):** wfl_flujo_trabajo.
- **Menú (MENU_NAVEGACION):** Workflows (definir flujos de aprobación, configuración JSON), Seguimiento (estado de aprobaciones pendientes).
- **Dependencias:** ORG (empresa).
- **Usado por:** Definición de flujos de aprobación/revisión/notificación; definicion_pasos en JSON; módulo donde aplica.

### 25.2 Tareas Completadas

- [x] Crear `app/infrastructure/database/tables_erp/tables_wfl.py` con la tabla wfl_flujo_trabajo.
- [x] Actualizar `tables_erp/__init__.py` para importar y exportar WflFlujoTrabajoTable.
- [x] Crear `app/infrastructure/database/queries/wfl/flujo_trabajo_queries.py` con CRUD y filtro por cliente_id.
- [x] Crear schemas y servicio; registrar router en `app/api/v1/api.py` con prefijo `/wfl`.
- [x] Crear `app/docs/database/DOC_FRONTEND_MODULO_WFL.md` para frontend.

### 25.3 Endpoints WFL (para frontend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET/POST/PUT | /wfl/flujos-trabajo, /{flujo_id} | CRUD flujos de trabajo (filtros: empresa_id, tipo_flujo, modulo_aplicable, es_activo, buscar). |

### 25.4 Notas importantes

- ✅ Flujo trabajo: codigo_flujo, nombre, descripcion, tipo_flujo (aprobacion, revision, notificacion), modulo_aplicable (código módulo donde aplica), definicion_pasos (JSON con pasos del workflow), es_activo.
- ✅ **Uso:** Definir flujos de aprobación personalizados (ej. OC > Gerente > Finanzas); definicion_pasos en JSON; pantalla Seguimiento consume estos flujos y/o instancias de aprobación (si se implementan en el futuro).

---

## Módulo 26: BI — Reportes & Analytics (Completado)

### 26.1 Alcance

- **Tablas (TABLAS_BD_ERP_COMPLETO):** bi_reporte.
- **Menú (MENU_NAVEGACION):** Reportes configurables (SQL, filtros, gráficos), Dashboards (KPIs, gráficos interactivos).
- **Dependencias:** ORG (empresa).
- **Usado por:** Reportes personalizados (query_sql, configuracion_json), categorías (ventas, inventarios, finanzas), tipo_reporte (sql, olap, dashboard).

### 26.2 Tareas Completadas

- [x] Crear `app/infrastructure/database/tables_erp/tables_bi.py` con la tabla bi_reporte.
- [x] Actualizar `tables_erp/__init__.py` para importar y exportar BiReporteTable.
- [x] Crear `app/infrastructure/database/queries/bi/reporte_queries.py` con CRUD y filtro por cliente_id.
- [x] Crear schemas y servicio; registrar router en `app/api/v1/api.py` con prefijo `/bi`.
- [x] Crear `app/docs/database/DOC_FRONTEND_MODULO_BI.md` para frontend.

### 26.3 Endpoints BI (para frontend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET/POST/PUT | /bi/reportes, /{reporte_id} | CRUD reportes (filtros: empresa_id, tipo_reporte, modulo_origen, categoria, es_activo, es_publico, buscar). |

### 26.4 Notas importantes

- ✅ Reporte: codigo_reporte, nombre, descripcion, modulo_origen, categoria, tipo_reporte (sql, olap, dashboard), query_sql, configuracion_json (gráficos, filtros), es_publico, creado_por_usuario_id, es_activo.
- ✅ **Uso:** Definir reportes personalizados con SQL; guardar configuración de gráficos y filtros en configuracion_json; dashboards y KPIs en tiempo real según implementación frontend.

---

## Módulo 27: AUD — Auditoría y Trazabilidad (Completado)

### 27.1 Alcance

- **Tablas (TABLAS_BD_ERP_COMPLETO):** aud_log_auditoria.
- **Menú (MENU_NAVEGACION):** Log de Auditoría (registro automático de cambios: quién, cuándo, qué tabla, valor anterior/nuevo), Reportes de Trazabilidad (rastrear cambios en documentos críticos, cumplimiento normativo).
- **Dependencias:** ORG (empresa).
- **Usado por:** Registro inmutable de acciones (INSERT, UPDATE, DELETE, SELECT); modulo, tabla, accion; valores_anteriores/valores_nuevos (JSON); ip_address, user_agent.

### 27.2 Tareas Completadas

- [x] Crear `app/infrastructure/database/tables_erp/tables_aud.py` con la tabla aud_log_auditoria.
- [x] Actualizar `tables_erp/__init__.py` para importar y exportar AudLogAuditoriaTable.
- [x] Crear `app/infrastructure/database/queries/aud/log_auditoria_queries.py` con list, get_by_id, create (sin update/delete); filtro por cliente_id.
- [x] Crear schemas (Create, Read) y servicio; registrar router en `app/api/v1/api.py` con prefijo `/aud`.
- [x] Crear `app/docs/database/DOC_FRONTEND_MODULO_AUD.md` para frontend.

### 27.3 Endpoints AUD (para frontend)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /aud/log-auditoria | Listar logs (filtros: empresa_id, modulo, tabla, accion, usuario_id, fecha_desde, fecha_hasta, registro_id, buscar, limit). |
| GET | /aud/log-auditoria/{log_id} | Detalle de un log. |
| POST | /aud/log-auditoria | Registrar entrada de auditoría (uso típico: sistema/middleware). |

### 27.4 Notas importantes

- ✅ Log es **inmutable**: no hay PUT ni DELETE. Solo consulta (GET) y registro (POST).
- ✅ accion: 'INSERT', 'UPDATE', 'DELETE', 'SELECT'. valores_anteriores y valores_nuevos son JSON (string).
- ✅ **Uso:** Pantalla "Log de Auditoría" con filtros por módulo, tabla, usuario, rango de fechas; "Reportes de Trazabilidad" reutilizando los mismos filtros o por registro_id para rastrear un documento/entidad.

---

## Reglas de tenant (todos los módulos)

1. **Contexto:** Obtener `client_id` con `get_current_client_id()` (o equivalente) en capa de presentación; pasar a servicios o resolver en servicios desde contexto.
2. **Queries:** Siempre filtrar por `cliente_id` (y `empresa_id` cuando aplique). Usar SQLAlchemy Core con condición explícita o helpers que inyecten el filtro.
3. **Inserciones:** Nunca aceptar `cliente_id` desde el body; asignar desde contexto.
4. **Actualizaciones/eliminaciones:** Verificar que el registro pertenezca al tenant antes de modificar (por ejemplo, leyendo primero con filtro cliente_id).
5. **Listados:** Siempre filtrar por `cliente_id` (y opcionalmente empresa_id).

---

## Checklist por módulo antes de dar por cerrado

- [ ] Tablas ERP creadas (SQLAlchemy) y script SQL disponible.
- [ ] Queries con filtro tenant en todas las operaciones.
- [ ] Servicios validan/obtienen client_id y no confían en input del cliente para tenant.
- [ ] Endpoints documentados (tags, modelos de respuesta).
- [ ] Pruebas manuales o automáticas: otro tenant no ve/modifica datos del primero.
