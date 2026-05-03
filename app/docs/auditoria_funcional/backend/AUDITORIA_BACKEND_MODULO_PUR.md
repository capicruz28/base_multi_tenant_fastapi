## Auditoría funcional backend — Módulo PUR (Compras)

**Fecha:** 2026-03-16  
**Alcance:** Análisis exclusivo. Sin modificación de código.  
**Objetivo:** Verificar cobertura funcional del backend PUR frente a documentación oficial y estructura de BD; detectar brechas (GAPs).

---

## 1. Resumen del módulo

El módulo **PUR — Gestión de Compras** es uno de los módulos base del ERP (paquete Starter según `CATALOGO_MODULOS.md`). Su objetivo es:

- **Gestión de proveedores y contactos**
- **Productos por proveedor y condiciones de compra**
- **Solicitudes internas de compra**
- **Cotizaciones a proveedores y evaluación**
- **Órdenes de compra**
- **Recepción de mercadería e integración con inventarios**

Según `MENU_NAVEGACION.md` (sección 05. MÓDULO PUR — COMPRAS) y `DOC_FRONTEND_MODULO_PUR.md`, el módulo cubre:

- **Proveedores:** Catálogo con RUC, razón social, contactos, condiciones de pago, datos bancarios, límites de crédito, homologación.
- **Contactos de Proveedor:** Múltiples contactos por proveedor con roles (principal, cotizaciones, cobranzas).
- **Productos por Proveedor:** Catálogo de productos que vende cada proveedor con precios, unidades de medida, cantidades mínimas, tiempos de entrega, proveedor preferido.
- **Solicitudes de Compra:** Requisiciones internas por empresa, departamento, almacén y centro de costo; flujo de aprobación.
- **Cotizaciones:** Solicitudes de precios a proveedores, evaluación, selección de cotización ganadora.
- **Órdenes de Compra:** Generación de órdenes desde solicitudes y/o cotizaciones, control de estados, seguimiento de recepción.
- **Recepciones:** Registro de mercadería recibida vinculada a orden de compra, con impacto en inventarios (INV).

**Implementación backend detectada (alto nivel):**

- **Router principal PUR:** `app/modules/pur/presentation/endpoints.py`, incluido en `app/api/v1/api.py` con prefijo `/api/v1/pur` y tag `["PUR - Compras"]`.
- **Sub-routers PUR:** `endpoints_proveedores`, `endpoints_contactos`, `endpoints_productos_proveedor`, `endpoints_solicitudes`, `endpoints_cotizaciones`, `endpoints_ordenes_compra`, `endpoints_recepciones`.
- **Servicios:** `app/modules/pur/application/services/*.py` (proveedor, contacto, producto_proveedor, solicitud, cotizacion, orden_compra, recepcion).
- **Queries:** `app/infrastructure/database/queries/pur/*.py` con filtro estricto por `cliente_id`.
- **Modelos BD:** `app/infrastructure/database/tables_erp/tables_pur.py` alineado en gran medida con `3.- TABLAS_BD_ERP_COMPLETO_FASE4.sql` sección PUR, salvo diferencias puntuales (ej. manejo de moneda en cotización).
- **RBAC:** Todos los endpoints PUR usan `require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.accion")` con `MODULE_CODE = "pur"` y recursos: `proveedor`, `contacto`, `producto_proveedor`, `solicitud`, `cotizacion`, `orden_compra`, `recepcion`.

**Conclusión de alto nivel:** La implementación backend cubre las entidades principales y la mayoría de operaciones CRUD básicas (listar, detalle, crear, actualizar) para PUR, con un patrón consistente de multi-tenancy (`cliente_id` desde token) y RBAC declarativo. Sin embargo, se detectan brechas en: ausencia de endpoints de eliminación/activación explícitos, falta de endpoints de acciones de negocio (aprobar/rechazar solicitudes y órdenes, marcar cotización ganadora, generar orden desde solicitud/cotización, procesar recepción con integración explícita a INV), ausencia de paginación y ordenamiento generalizados, así como posibles inconsistencias entre el catálogo RBAC de base y los permisos usados por el backend.

---

## 2. Funcionalidades definidas en documentación

### 2.1 CATALOGO_MODULOS.md

- **PUR — Gestión de Compras:**
  - Proveedores y cotizaciones
  - Órdenes de compra
  - Recepción de mercadería
  - Control de pagos (mencionado a nivel de módulo, pero no detallado en la documentación PUR específica analizada).

### 2.2 MENU_NAVEGACION.md — 05. MÓDULO PUR — COMPRAS

- **Proveedores**
  - Catálogo con RUC, contactos, condiciones de pago.
- **Contactos de Proveedor**
  - Gestión de vendedores y contactos del proveedor.
- **Productos por Proveedor**
  - Qué productos vende cada proveedor con sus precios.
- **Solicitudes de Compra**
  - Requisiciones internas (departamento solicita materiales).
- **Cotizaciones**
  - Solicitar cotizaciones a varios proveedores.
- **Órdenes de Compra**
  - Generar OC con numeración automática.
  - Control de estados (borrador, aprobada, enviada).
- **Recepción de Mercadería**
  - Registrar cantidades recibidas vs ordenadas.
  - Genera movimiento de inventario automático (integración con INV).

### 2.3 DOC_FRONTEND_MODULO_PUR.md

El documento frontend explicita la API esperada para el módulo PUR (base `/api/v1/pur`) y los campos necesarios para el frontend.

- **1. Proveedores**
  - Endpoints:
    - `GET /proveedores` (listar con filtros `empresa_id`, `solo_activos`, `buscar`).
    - `GET /proveedores/{proveedor_id}` (detalle).
    - `POST /proveedores` (crear).
    - `PUT /proveedores/{proveedor_id}` (actualizar).
  - Campos clave (simplificado):
    - Identificación: `proveedor_id`, `cliente_id`, `empresa_id`, `codigo_proveedor`, `razon_social`, `tipo_documento`, `numero_documento`, `tipo_proveedor`, `categoria_proveedor`.
    - Dirección: `direccion`, `pais`, `departamento`, `provincia`, `distrito`, `ubigeo`.
    - Contacto principal: `contacto_nombre`, `contacto_cargo`, teléfonos, correos.
    - Finanzas: `condicion_pago_defecto`, `dias_credito_defecto`, `moneda_preferida`, datos bancarios, `limite_credito`, `saldo_pendiente`.
    - Gestión: `estado`, `es_proveedor_homologado`, `fecha_homologacion`, `es_activo`, `observaciones`, auditoría (fechas, usuarios).

- **2. Contactos de Proveedor**
  - Endpoints:
    - `GET /contactos` (listar con filtros `proveedor_id`, `solo_activos`).
    - `GET /contactos/{contacto_id}` (detalle).
    - `POST /contactos` (crear).
    - `PUT /contactos/{contacto_id}` (actualizar).
  - Campos clave:
    - Identificación: `contacto_id`, `cliente_id`, `proveedor_id`.
    - Datos: `nombre_completo`, `cargo`, `area`, teléfonos, correo.
    - Roles: `es_contacto_principal`, `es_contacto_cotizaciones`, `es_contacto_cobranzas`.
    - Estado: `es_activo`, `fecha_creacion`.

- **3. Productos por Proveedor**
  - Endpoints:
    - `GET /productos-proveedor` (filtros `proveedor_id`, `producto_id`, `solo_activos`).
    - `GET /productos-proveedor/{producto_proveedor_id}` (detalle).
    - `POST /productos-proveedor` (crear).
    - `PUT /productos-proveedor/{producto_proveedor_id}` (actualizar).
  - Campos clave:
    - Identificación: `producto_proveedor_id`, `cliente_id`, `proveedor_id`, `producto_id`.
    - Condiciones: `codigo_proveedor`, `descripcion_proveedor`, `precio_unitario`, `moneda`, `unidad_medida_id`, `cantidad_minima`, `multiplo_compra`, `tiempo_entrega_dias`, vigencias, `es_proveedor_preferido`, `prioridad`, `es_activo`.

- **4. Solicitudes de Compra**
  - Endpoints:
    - `GET /solicitudes` (filtros `empresa_id`, `estado`, `fecha_desde`, `fecha_hasta`).
    - `GET /solicitudes/{solicitud_id}` (detalle).
    - `POST /solicitudes` (crear).
    - `PUT /solicitudes/{solicitud_id}` (actualizar).
  - Campos clave:
    - Identificación y flujo: `solicitud_id`, `cliente_id`, `empresa_id`, `numero_solicitud`, fechas, departamento, usuario y nombre del solicitante.
    - Ubicación y costo: `almacen_destino_id`, `centro_costo_id`, `tipo_solicitud`, `motivo_solicitud`, `total_items`, `total_estimado`, `moneda`.
    - Estado y aprobación: `estado` (borrador, pendiente_aprobacion, aprobada, rechazada, procesada, anulada), `requiere_aprobacion`, `aprobado_por_usuario_id`, `fecha_aprobacion`, `orden_compra_generada`, `motivo_rechazo`.

- **5. Cotizaciones**
  - Endpoints:
    - `GET /cotizaciones` (filtros `empresa_id`, `proveedor_id`, `solicitud_compra_id`, `estado`, `fecha_desde`, `fecha_hasta`).
    - `GET /cotizaciones/{cotizacion_id}` (detalle).
    - `POST /cotizaciones` (crear).
    - `PUT /cotizaciones/{cotizacion_id}` (actualizar).
  - Campos clave:
    - Identificación: `cotizacion_id`, `cliente_id`, `empresa_id`, `numero_cotizacion`, fechas.
    - Relación: `proveedor_id`, `solicitud_compra_id`.
    - Condiciones económicas: `condicion_pago`, `dias_credito`, `tiempo_entrega_dias`, `lugar_entrega`, `moneda`, `subtotal`, `descuento`, `igv`, `total`.
    - Estado y evaluación: `estado`, `es_ganadora`, `observaciones`, `motivo_rechazo`.

- **6. Órdenes de Compra**
  - Endpoints:
    - `GET /ordenes-compra` (filtros `empresa_id`, `proveedor_id`, `solicitud_compra_id`, `estado`, `fecha_desde`, `fecha_hasta`).
    - `GET /ordenes-compra/{orden_compra_id}` (detalle).
    - `POST /ordenes-compra` (crear).
    - `PUT /ordenes-compra/{orden_compra_id}` (actualizar).
  - Campos clave:
    - Identificación: `orden_compra_id`, `cliente_id`, `empresa_id`, `numero_oc`, fechas.
    - Relaciones: `proveedor_id`, `almacen_destino_id`, `solicitud_compra_id`, `cotizacion_id`, `centro_costo_id`.
    - Datos de proveedor: razón social, RUC.
    - Económicos: `condicion_pago`, `dias_credito`, `moneda`, `tipo_cambio`, `subtotal`, `descuento_global`, `igv`, `total`, `total_items`.
    - Seguimiento de recepción: `items_recepcionados`, `porcentaje_recepcion`.
    - Estado y aprobación: `estado` (borrador, emitida, aprobada, parcial, completa, anulada), `requiere_aprobacion`, `aprobado_por_usuario_id`, `fecha_aprobacion`, `motivo_anulacion`, `fecha_anulacion`.

- **7. Recepciones**
  - Endpoints:
    - `GET /recepciones` (filtros `empresa_id`, `orden_compra_id`, `proveedor_id`, `almacen_id`, `estado`, `fecha_desde`, `fecha_hasta`).
    - `GET /recepciones/{recepcion_id}` (detalle).
    - `POST /recepciones` (crear).
    - `PUT /recepciones/{recepcion_id}` (actualizar).
  - Campos clave:
    - Identificación: `recepcion_id`, `cliente_id`, `empresa_id`, `numero_recepcion`, `fecha_recepcion`.
    - Relaciones: `orden_compra_id`, `proveedor_id`, `almacen_id`.
    - Logística: datos de guía de remisión, transportista, placa vehículo.
    - Control: `total_items`, `total_cantidad`, `estado`, `requiere_inspeccion`, `inspeccion_id`, `movimiento_inventario_id`, observaciones, incidencias.

- **Notas funcionales clave:**
  - Todos los endpoints asumen **multi-tenant estricto:** `cliente_id` se obtiene del token y **no debe** ir en el body.
  - Flujos completos esperan acciones de aprobación y cambio de estado (solicitudes, cotizaciones, órdenes, recepciones), aunque no siempre se detallan endpoints de acciones dedicadas.

---

## 3. Entidades detectadas en base de datos

Según `3.- TABLAS_BD_ERP_COMPLETO_FASE4.sql` (sección PUR) y sus relaciones:

- **Tablas PUR principales:**
  - `pur_proveedor`  
    - Catálogo de proveedores.  
    - Campos alineados con los de `ProveedorCreate/Read` (identificación, dirección, contacto, finanzas, límites de crédito, estado, auditoría).  
    - Relaciones de uso: órdenes de compra, cotizaciones, productos por proveedor, recepciones.

  - `pur_proveedor_contacto`  
    - Contactos adicionales por proveedor.  
    - Campos alineados con `ContactoProveedorCreate/Read`.  
    - FK a `pur_proveedor`.

  - `pur_producto_proveedor`  
    - Relación producto–proveedor con precios y condiciones.  
    - Campos alineados con `ProductoProveedorCreate/Read`.  
    - FK a `pur_proveedor` y `inv_producto`.

  - `pur_solicitud_compra`  
    - Cabecera de solicitudes de compra.  
    - Campos alineados con `SolicitudCompraCreate/Read` (empresa, fechas, solicitante, almacén, centro de costo, totales, moneda, estado, aprobación, orden_compra_generada).

  - `pur_solicitud_compra_detalle`  
    - Detalle de items solicitados por solicitud (producto, cantidad, unidad, precio referencial, observaciones).  
    - Relación: `solicitud_id` → `pur_solicitud_compra`.  
    - **No hay endpoints/servicios/queries específicos para esta tabla en el backend PUR.**

  - `pur_cotizacion`  
    - Cabecera de cotizaciones enviadas por proveedores.  
    - Incluye relaciones a empresa, proveedor, solicitud de compra, condición de pago, montos, estado, es_ganadora.  
    - En el script SQL la tabla tiene una columna `moneda_id` (FK a `cat_moneda`) además de otros campos económicos; en `tables_pur.py` se modela la moneda como `moneda` (string) sin FK explícita a `cat_moneda`, lo que introduce una **diferencia estructural** respecto al SQL (sección 10).

  - `pur_cotizacion_detalle`  
    - Items cotizados: producto, cantidad, unidad de medida, precio unitario, descuento, tiempo de entrega, observaciones.  
    - Relación: `cotizacion_id` → `pur_cotizacion`.  
    - **No hay endpoints ni servicios que expongan este detalle en la API.**

  - `pur_orden_compra`  
    - Cabecera de orden de compra.  
    - Campos alineados con `OrdenCompraCreate/Read` (número, fechas, proveedor, datos de entrega, vinculación a solicitud/cotización, montos, estado, aprobación, seguimiento de recepción).

  - `pur_orden_compra_detalle`  
    - Items de la orden de compra: producto, cantidades, unidad, precio, cantidades recepcionadas, observaciones/especificaciones.  
    - Relación: `orden_compra_id` → `pur_orden_compra`.  
    - **No hay endpoints/servicios/queries dedicados que permitan gestionar o leer este detalle desde el módulo PUR.**

  - `pur_recepcion`  
    - Cabecera de recepciones de mercadería.  
    - Campos alineados con `RecepcionCreate/Read` (OC, proveedor, almacén, guía de remisión, transportista, totales, estado, integración con inventario).

  - `pur_recepcion_detalle`  
    - Detalle de ítems recepcionados: producto, cantidades, unidad, lote, fecha de vencimiento, precio, ubicaciones, motivo de diferencias.  
    - Relación: `recepcion_id` → `pur_recepcion`, `orden_compra_detalle_id` → `pur_orden_compra_detalle`.  
    - **No hay endpoints ni servicios que expongan este nivel de detalle.**

- **Relaciones relevantes con otros módulos:**
  - `pur_proveedor` se utiliza como **proveedor habitual** en `inv_producto` y en tablas de MRP y MNT (ej. `ord_sugerida`, activos con proveedor).
  - `pur_orden_compra` y `pur_recepcion` se relacionan con `inv_almacen` y, según los comentarios del SQL, deben **generar movimientos de inventario** (vía INV) al recepcionar.

**Conclusión estructural:** La capa de modelos `tables_pur.py` cubre las tablas PUR principales (incluyendo sus tablas de detalle), pero la API sólo expone las **cabeceras** (proveedor, contacto, producto_proveedor, solicitud, cotización, orden_compra, recepcion). Ninguna de las tablas de detalle (`pur_solicitud_compra_detalle`, `pur_cotizacion_detalle`, `pur_orden_compra_detalle`, `pur_recepcion_detalle`) está expuesta vía endpoints o servicios dedicados.

---

## 4. Implementación actual detectada

### 4.1 Routing

- `app/api/v1/api.py`:
  - `api_router.include_router(pur_endpoints.router, prefix="/pur", tags=["PUR - Compras"])`

- `app/modules/pur/presentation/endpoints.py` agrupa:
  - `/proveedores` → `endpoints_proveedores`
  - `/contactos` → `endpoints_contactos`
  - `/productos-proveedor` → `endpoints_productos_proveedor`
  - `/solicitudes` → `endpoints_solicitudes`
  - `/cotizaciones` → `endpoints_cotizaciones`
  - `/ordenes-compra` → `endpoints_ordenes_compra`
  - `/recepciones` → `endpoints_recepciones`

### 4.2 Capas

- **Presentación (`app/modules/pur/presentation`):**
  - `endpoints_proveedores.py`
  - `endpoints_contactos.py`
  - `endpoints_productos_proveedor.py`
  - `endpoints_solicitudes.py`
  - `endpoints_cotizaciones.py`
  - `endpoints_ordenes_compra.py`
  - `endpoints_recepciones.py`
  - `schemas.py` con todos los schemas `Create/Update/Read` para cada entidad de cabecera.

- **Servicios (`app/modules/pur/application/services`):**
  - `proveedor_service.py`
  - `contacto_service.py`
  - `producto_proveedor_service.py`
  - `solicitud_service.py`
  - `cotizacion_service.py`
  - `orden_compra_service.py`
  - `recepcion_service.py`
  - `__init__.py` re-exporta todas las funciones y módulos.

- **Queries (`app/infrastructure/database/queries/pur`):**
  - `proveedor_queries.py`
  - `contacto_queries.py`
  - `producto_proveedor_queries.py`
  - `solicitud_queries.py`
  - `cotizacion_queries.py`
  - `orden_compra_queries.py`
  - `recepcion_queries.py`
  - Todas las queries filtran explícitamente por `cliente_id` y aceptan filtros por `empresa_id` y otros campos, pero **no manejan las tablas de detalle**.

- **Modelos BD (`app/infrastructure/database/tables_erp/tables_pur.py`):**
  - Define todas las tablas PUR, incluyendo las de detalle.  
  - Los schemas sólo cubren las tablas de cabecera, no las de detalle.

### 4.3 Patrones de seguridad y multi-tenant

- En todos los endpoints PUR:
  - Se usa `current_user: UsuarioReadWithRoles = Depends(get_current_active_user)`.
  - Se obtiene `client_id = current_user.cliente_id`.
  - Se pasa `client_id` a servicios y queries, que filtran por `Pur*Table.c.cliente_id == client_id`.
  - `cliente_id` **no aparece** en los bodies de los schemas de creación/actualización.

- `empresa_id`:
  - Aparece en los bodies de `ProveedorCreate`, `SolicitudCompraCreate`, `CotizacionCreate`, `OrdenCompraCreate`, `RecepcionCreate`.  
  - No se ve en el código de servicios/queries una validación explícita de que ese `empresa_id` pertenezca al `cliente_id` actual (es decir, que exista una fila en `org_empresa` con ese `empresa_id` y `cliente_id` igual al del usuario).

### 4.4 RBAC en endpoints

- Cada archivo de endpoints define:
  - `MODULE_CODE = "pur"`
  - `RESOURCE_CODE` específico: `"proveedor"`, `"contacto"`, `"producto_proveedor"`, `"solicitud"`, `"cotizacion"`, `"orden_compra"`, `"recepcion"`.
  - Uso de `require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer|crear|actualizar")` en **todos** los endpoints (listar, detalle, crear, actualizar).

- Esto implica que el catálogo de permisos RBAC debe contener, al menos:
  - `pur.proveedor.leer|crear|actualizar`
  - `pur.contacto.leer|crear|actualizar`
  - `pur.producto_proveedor.leer|crear|actualizar`
  - `pur.solicitud.leer|crear|actualizar`
  - `pur.cotizacion.leer|crear|actualizar`
  - `pur.orden_compra.leer|crear|actualizar`
  - `pur.recepcion.leer|crear|actualizar`

El script `5.- SCRIPT_RBAC_TABLAS_CENTRAL.sql` define sólo la estructura de tablas `permiso` y `rol_permiso`, no los registros (códigos) de permisos; las seeds de permisos PUR **no están presentes** en `SEED_PERMISOS_RBAC.sql` (archivo vacío), lo que indica una brecha potencial a nivel de inicialización del catálogo de permisos.

---

## 5. Endpoints detectados

Para cada entidad se resumen los endpoints del backend PUR, enlazando ruta, método, función, servicio, permisos y multi-tenant.

### 5.1 Proveedores

- **Listar proveedores**
  - **Método/Ruta:** `GET /api/v1/pur/proveedores`
  - **Archivo:** `endpoints_proveedores.py`
  - **Función:** `listar_proveedores`
  - **Servicio:** `proveedor_service.list_proveedores_servicio`
  - **Entidad BD:** `pur_proveedor`
  - **Permiso:** `pur.proveedor.leer`
  - **Multi-tenant:** `client_id` desde `current_user.cliente_id`, queries filtran `PurProveedorTable.c.cliente_id == client_id`. Filtro opcional `empresa_id`.

- **Detalle proveedor**
  - `GET /api/v1/pur/proveedores/{proveedor_id}`  
  - `detalle_proveedor` → `get_proveedor_servicio` → `get_proveedor_by_id`  
  - Permiso: `pur.proveedor.leer`  
  - Multi-tenant estricto por `cliente_id`.

- **Crear proveedor**
  - `POST /api/v1/pur/proveedores`  
  - `crear_proveedor` → `create_proveedor_servicio` → `create_proveedor`  
  - Permiso: `pur.proveedor.crear`  
  - `empresa_id` se recibe en el body; se fuerza `cliente_id` en la query.

- **Actualizar proveedor**
  - `PUT /api/v1/pur/proveedores/{proveedor_id}`  
  - `actualizar_proveedor` → `update_proveedor_servicio` → `update_proveedor`  
  - Permiso: `pur.proveedor.actualizar`  
  - Validación multi-tenant: se obtiene primero por `cliente_id`+`proveedor_id`. No se valida empresa–cliente.

### 5.2 Contactos de Proveedor

- **Listar contactos**
  - `GET /api/v1/pur/contactos`  
  - Función: `listar_contactos` → `list_contactos_servicio` → `list_contactos`  
  - Permiso: `pur.contacto.leer`  
  - Multi-tenant: `cliente_id` desde token; filtros `proveedor_id`, `solo_activos`.

- **Detalle contacto**
  - `GET /api/v1/pur/contactos/{contacto_id}`  
  - `detalle_contacto` → `get_contacto_servicio` → `get_contacto_by_id`  
  - Permiso: `pur.contacto.leer`

- **Crear contacto**
  - `POST /api/v1/pur/contactos`  
  - `crear_contacto` → `create_contacto_servicio` → `create_contacto`  
  - Permiso: `pur.contacto.crear`  
  - `cliente_id` se fuerza en BD.

- **Actualizar contacto**
  - `PUT /api/v1/pur/contactos/{contacto_id}`  
  - `actualizar_contacto` → `update_contacto_servicio` → `update_contacto`  
  - Permiso: `pur.contacto.actualizar`

### 5.3 Productos por Proveedor

- **Listar productos por proveedor**
  - `GET /api/v1/pur/productos-proveedor`  
  - `listar_productos_proveedor` → `list_productos_proveedor_servicio` → `list_productos_proveedor`  
  - Permiso: `pur.producto_proveedor.leer`  
  - Multi-tenant: filtro estricto por `cliente_id`; filtros opcionales `proveedor_id`, `producto_id`, `solo_activos`.

- **Detalle producto por proveedor**
  - `GET /api/v1/pur/productos-proveedor/{producto_proveedor_id}`  
  - Permiso: `pur.producto_proveedor.leer`

- **Crear producto por proveedor**
  - `POST /api/v1/pur/productos-proveedor`  
  - Permiso: `pur.producto_proveedor.crear`

- **Actualizar producto por proveedor**
  - `PUT /api/v1/pur/productos-proveedor/{producto_proveedor_id}`  
  - Permiso: `pur.producto_proveedor.actualizar`

### 5.4 Solicitudes de Compra

- **Listar solicitudes**
  - `GET /api/v1/pur/solicitudes`  
  - `listar_solicitudes` → `list_solicitudes_servicio` → `list_solicitudes`  
  - Filtros: `empresa_id`, `estado`, `fecha_desde`, `fecha_hasta`  
  - Permiso: `pur.solicitud.leer`  
  - Multi-tenant: filtro `cliente_id`, opción `empresa_id`.

- **Detalle solicitud**
  - `GET /api/v1/pur/solicitudes/{solicitud_id}`  
  - Permiso: `pur.solicitud.leer`

- **Crear solicitud**
  - `POST /api/v1/pur/solicitudes`  
  - Permiso: `pur.solicitud.crear`  
  - `empresa_id` en body; `cliente_id` forzado; **no se exponen ni gestionan los detalles (líneas) en esta capa.**

- **Actualizar solicitud**
  - `PUT /api/v1/pur/solicitudes/{solicitud_id}`  
  - Permiso: `pur.solicitud.actualizar`

### 5.5 Cotizaciones

- **Listar cotizaciones**
  - `GET /api/v1/pur/cotizaciones`  
  - `listar_cotizaciones` → `list_cotizaciones_servicio` → `list_cotizaciones`  
  - Filtros: `empresa_id`, `proveedor_id`, `solicitud_compra_id`, `estado`, `fecha_desde`, `fecha_hasta`  
  - Permiso: `pur.cotizacion.leer`

- **Detalle cotización**
  - `GET /api/v1/pur/cotizaciones/{cotizacion_id}`  
  - Permiso: `pur.cotizacion.leer`

- **Crear cotización**
  - `POST /api/v1/pur/cotizaciones`  
  - Permiso: `pur.cotizacion.crear`

- **Actualizar cotización**
  - `PUT /api/v1/pur/cotizaciones/{cotizacion_id}`  
  - Permiso: `pur.cotizacion.actualizar`

### 5.6 Órdenes de Compra

- **Listar órdenes de compra**
  - `GET /api/v1/pur/ordenes-compra`  
  - `listar_ordenes_compra` → `list_ordenes_compra_servicio` → `list_ordenes_compra`  
  - Filtros: `empresa_id`, `proveedor_id`, `solicitud_compra_id`, `estado`, `fecha_desde`, `fecha_hasta`  
  - Permiso: `pur.orden_compra.leer`

- **Detalle orden de compra**
  - `GET /api/v1/pur/ordenes-compra/{orden_compra_id}`  
  - Permiso: `pur.orden_compra.leer`

- **Crear orden de compra**
  - `POST /api/v1/pur/ordenes-compra`  
  - Permiso: `pur.orden_compra.crear`  
  - No hay endpoint dedicado para “generar OC desde solicitud/cotización” (se espera construir el payload en frontend).

- **Actualizar orden de compra**
  - `PUT /api/v1/pur/ordenes-compra/{orden_compra_id}`  
  - Permiso: `pur.orden_compra.actualizar`  
  - Tampoco hay endpoints específicos para “aprobar”, “anular” o actualizar campos de seguimiento de recepción de forma semántica (sólo vía PUT genérico).

### 5.7 Recepciones

- **Listar recepciones**
  - `GET /api/v1/pur/recepciones`  
  - `listar_recepciones` → `list_recepciones_servicio` → `list_recepciones`  
  - Filtros: `empresa_id`, `orden_compra_id`, `proveedor_id`, `almacen_id`, `estado`, `fecha_desde`, `fecha_hasta`  
  - Permiso: `pur.recepcion.leer`

- **Detalle recepción**
  - `GET /api/v1/pur/recepciones/{recepcion_id}`  
  - Permiso: `pur.recepcion.leer`

- **Crear recepción**
  - `POST /api/v1/pur/recepciones`  
  - Permiso: `pur.recepcion.crear`  
  - El campo `movimiento_inventario_id` se maneja como UUID opcional; no hay endpoint ni servicio que ejecute explícitamente la integración con INV como parte del flujo.

- **Actualizar recepción**
  - `PUT /api/v1/pur/recepciones/{recepcion_id}`  
  - Permiso: `pur.recepcion.actualizar`

---

## 6. Matriz funcionalidad vs implementación

| Funcionalidad (doc) | Endpoint / Recurso | Implementación backend actual | Estado |
|---------------------|--------------------|-------------------------------|--------|
| Catálogo de Proveedores (CRUD + búsqueda) | `/proveedores` | Listar con filtros `empresa_id`, `solo_activos`, `buscar`; detalle; crear; actualizar. Campos alineados con BD y doc frontend. | ✔ Implementado |
| Contactos de Proveedor (CRUD) | `/contactos` | Listar por proveedor, detalle, crear, actualizar; campos alineados con BD. | ✔ Implementado |
| Productos por Proveedor (CRUD) | `/productos-proveedor` | Listar (filtros por proveedor/producto), detalle, crear, actualizar; campos alineados con BD. | ✔ Implementado |
| Solicitudes de Compra (cabecera) | `/solicitudes` | Listar con filtros por empresa, estado, rango de fechas; detalle, crear, actualizar; **no se exponen ni gestionan detalles de solicitud**. | ⚠ Parcial |
| Detalle de Solicitudes de Compra (líneas) | — | No existen endpoints/servicios para `pur_solicitud_compra_detalle`. | ✖ No implementado |
| Cotizaciones (cabecera) | `/cotizaciones` | Listar por empresa, proveedor, solicitud, estado, fechas; detalle, crear, actualizar; estado y es_ganadora presentes. | ✔ Implementado (cabecera) |
| Detalle de Cotizaciones (items) | — | No hay API para `pur_cotizacion_detalle`. | ✖ No implementado |
| Seleccionar Cotización Ganadora | `/cotizaciones` (PUT genérico) | Campo `es_ganadora` existe en schema y tabla, se puede actualizar vía PUT, pero no hay endpoint semántico dedicado ni lógica de exclusividad por solicitud. | ⚠ Parcial |
| Órdenes de Compra (cabecera) | `/ordenes-compra` | Listar por empresa, proveedor, solicitud, estado, fechas; detalle, crear, actualizar; incluye campos de seguimiento de recepción. | ✔ Implementado (cabecera) |
| Detalle de Órdenes de Compra (items) | — | No hay endpoints para `pur_orden_compra_detalle`. | ✖ No implementado |
| Control de estados de OC (borrador, aprobada, enviada, parcial, completa, anulada) | `/ordenes-compra` (PUT) | Campos de estado presentes y actualizables vía PUT; no hay endpoints semánticos (`aprobar`, `emitir`, `anular`) ni validaciones de reglas de negocio en servicios. | ⚠ Parcial |
| Recepción de Mercadería (cabecera) | `/recepciones` | Listar, detalle, crear, actualizar; campos alineados con BD (incluye `movimiento_inventario_id`, `requiere_inspeccion`, etc.). | ✔ Implementado (cabecera) |
| Detalle de Recepciones (items) | — | No hay endpoints para `pur_recepcion_detalle`. | ✖ No implementado |
| Integración con INV (movimiento de inventario automático) | Esperado en Recepciones y quizás en OC | BD soporta `movimiento_inventario_id` y relaciones con INV; no hay lógica explícita en servicios PUR que cree movimientos INV ni actualice stock; tampoco endpoints dedicados de “procesar recepción”. | ✖ No implementado |
| Control de pagos (a nivel PUR) | — | No se detectan entidades/endpoints de pagos de proveedores dentro de PUR; probablemente se delega a FIN. | ⚠ Parcial / Fuera de alcance PUR backend actual |
| Multi-tenant estricto | Todos los recursos PUR | Todas las queries PUR filtran por `cliente_id` y no aceptan `cliente_id` en bodies. | ✔ Implementado |
| Validación empresa–cliente | Create/Update con `empresa_id` | Se recibe `empresa_id` y se usa en inserts/updates; **no hay validación explícita** de que `empresa_id` pertenezca al `cliente_id` del usuario. | ⚠ Parcial |
| Permisos RBAC por recurso/acción | Todos los endpoints PUR | Todos los endpoints PUR usan `require_permission("pur.recurso.accion")`; el catálogo de permisos base no incluye seeds PUR. | ⚠ Parcial |

---

## 7. CRUD funcional por entidad

| Entidad | Crear | Listar | Detalle | Actualizar | Eliminar | Activar/Desactivar |
|---------|-------|--------|---------|------------|----------|--------------------|
| Proveedor | ✔ `POST /proveedores` | ✔ `GET /proveedores` | ✔ `GET /proveedores/{id}` | ✔ `PUT /proveedores/{id}` | ✖ No | ⚠ Mediante campo `es_activo` vía PUT (no endpoint semántico) |
| Contacto de Proveedor | ✔ `POST /contactos` | ✔ `GET /contactos` | ✔ `GET /contactos/{id}` | ✔ `PUT /contactos/{id}` | ✖ No | ⚠ Mediante `es_activo` en PUT |
| Producto por Proveedor | ✔ `POST /productos-proveedor` | ✔ `GET /productos-proveedor` | ✔ `GET /productos-proveedor/{id}` | ✔ `PUT /productos-proveedor/{id}` | ✖ No | ⚠ Mediante `es_activo` en PUT |
| Solicitud de Compra (cabecera) | ✔ `POST /solicitudes` | ✔ `GET /solicitudes` | ✔ `GET /solicitudes/{id}` | ✔ `PUT /solicitudes/{id}` | ✖ No | ⚠ Vía campo `estado` (ej. `anulada`) pero sin endpoints semánticos |
| Solicitud de Compra Detalle | ✖ No | ✖ No | ✖ No | ✖ No | ✖ No | N/A |
| Cotización (cabecera) | ✔ `POST /cotizaciones` | ✔ `GET /cotizaciones` | ✔ `GET /cotizaciones/{id}` | ✔ `PUT /cotizaciones/{id}` | ✖ No | ⚠ Vía `estado` y `es_ganadora` en PUT |
| Cotización Detalle | ✖ No | ✖ No | ✖ No | ✖ No | ✖ No | N/A |
| Orden de Compra (cabecera) | ✔ `POST /ordenes-compra` | ✔ `GET /ordenes-compra` | ✔ `GET /ordenes-compra/{id}` | ✔ `PUT /ordenes-compra/{id}` | ✖ No | ⚠ Vía `estado` en PUT (incluyendo anulación) |
| Orden de Compra Detalle | ✖ No | ✖ No | ✖ No | ✖ No | ✖ No | N/A |
| Recepción (cabecera) | ✔ `POST /recepciones` | ✔ `GET /recepciones` | ✔ `GET /recepciones/{id}` | ✔ `PUT /recepciones/{id}` | ✖ No | ⚠ Vía `estado` (ej. `anulada`) en PUT |
| Recepción Detalle | ✖ No | ✖ No | ✖ No | ✖ No | ✖ No | N/A |

**Observaciones CRUD:**

- No se expone ningún endpoint DELETE; la baja es lógica (a través de campos `es_activo` o `estado`). Esto es consistente con la filosofía del ERP, pero se podrían añadir endpoints semánticos (`desactivar`, `anular`) para claridad.
- Todos los recursos de detalle (solicitud, cotización, orden de compra, recepción) no tienen endpoints propios; el frontend no puede gestionar líneas desde la API PUR actual.

---

## 8. Campos faltantes en endpoints

En términos de **alineación entre BD y schemas/endpoints**:

- **Proveedores, Contactos, Productos por Proveedor:**  
  - `PurProveedorTable`, `PurProveedorContactoTable`, `PurProductoProveedorTable` y sus respectivos schemas (`*Create`, `*Read`) están bien alineados; todos los campos funcionales relevantes presentes en la documentación están expuestos o al menos representados de forma compatible (incluyendo `limite_credito`, `saldo_pendiente`, `es_proveedor_homologado`, `prioridad`, etc.). No se detectan campos críticos de BD no expuestos que sean necesarios para formularios funcionales.

- **Solicitudes de Compra (cabecera):**  
  - `PurSolicitudCompraTable` vs `SolicitudCompraCreate/Read` muestra una alineación buena en cabecera.  
  - **Campos de detalle (`pur_solicitud_compra_detalle`) no están representados en ningún schema PUR**, por lo que el frontend no puede construir formularios completos de líneas de solicitud: producto, cantidades, unidad de medida, precio referencial, observaciones.

- **Cotizaciones (cabecera):**  
  - Cabecera en `PurCotizacionTable` y `CotizacionCreate/Read` alineadas en términos de negocio.  
  - Diferencia estructural relevante: el SQL indica una columna `moneda_id` (FK a `cat_moneda`), mientras que el backend trabaja con un campo `moneda` (string) sin FK. Esto puede ser intencional (normalización diferente en la capa de aplicación), pero implica que **el backend no expone ni utiliza `moneda_id` como clave de catálogo**, lo que puede limitar validaciones de integridad contra catálogos de moneda.
  - **Detalle (`pur_cotizacion_detalle`) no está expuesto**: faltan campos como producto, cantidad, unidad, precio por línea, descuentos por línea, etc.

- **Órdenes de Compra (cabecera):**  
  - `PurOrdenCompraTable` y `OrdenCompraCreate/Read` cubren todos los campos de cabecera requeridos en la documentación (proveedor, OC, montos, estados, recepción, centro de costo).  
  - `items_recepcionados` y `porcentaje_recepcion` están presentes y expuestos.
  - **Detalle (`pur_orden_compra_detalle`) no está expuesto:** campos como `cantidad_ordenada`, `cantidad_recepcionada`, `especificaciones` no están accesibles desde la API PUR actual.

- **Recepciones (cabecera):**
  - `PurRecepcionTable` y `RecepcionCreate/Read` están alineados (incluyendo `movimiento_inventario_id`, integración potencial con INV).  
  - **Detalle (`pur_recepcion_detalle`) no está expuesto:** no se exponen campos de línea como `cantidad_ordenada`, `cantidad_recepcionada`, `lote`, `fecha_vencimiento`, `precio_unitario`, `motivo_diferencia`.

- **Filtros, búsqueda, paginación y ordenamiento:**
  - **Búsqueda textual** sólo está implementada en `listar_proveedores` (`buscar` por razón social, RUC, código).  
  - **Filtros**: la mayoría de listados permiten filtrar por `empresa_id` y algunas relaciones (proveedor, solicitud, estado, fechas).  
  - **Paginación**: ningún endpoint PUR implementa parámetros de paginación (`page`, `page_size`) ni ordenamiento flexible (`sort_by`, `order`); el orden está codificado (por fecha o por razón social).

**Conclusión de campos:** La API cubre bien los campos de **cabecera** pero **no expone las estructuras de detalle** definidas en la BD, lo que impide construir formularios completos para ítems de solicitud, cotización, orden de compra y recepción. Asimismo, se podría enriquecer la API con parámetros de búsqueda avanzada, paginación y ordenamiento generalizados.

---

## 9. Endpoints faltantes

Basado en la documentación funcional y en la estructura de la BD, se identifican los siguientes endpoints que **deberían existir** para cubrir completamente el módulo PUR.

### 9.1 Detalles de Solicitudes, Cotizaciones, Órdenes y Recepciones

| Funcionalidad | Endpoint sugerido | Método | Entidad BD | Motivo funcional |
|---------------|-------------------|--------|------------|------------------|
| Consultar líneas de una solicitud de compra | `/api/v1/pur/solicitudes/{solicitud_id}/detalle` | GET | `pur_solicitud_compra_detalle` | Permitir al frontend mostrar los productos solicitados, cantidades, unidades, precios referenciales. |
| Alta de líneas de solicitud | `/api/v1/pur/solicitudes/{solicitud_id}/detalle` | POST | `pur_solicitud_compra_detalle` | Crear items de solicitud desde el formulario de detalle. |
| Actualizar línea de solicitud | `/api/v1/pur/solicitudes/{solicitud_id}/detalle/{solicitud_detalle_id}` | PUT | `pur_solicitud_compra_detalle` | Editar cantidades, productos, unidades o precios. |
| Eliminar línea de solicitud | `/api/v1/pur/solicitudes/{solicitud_id}/detalle/{solicitud_detalle_id}` | DELETE | `pur_solicitud_compra_detalle` | Quitar ítems antes de aprobación. |
| Consultar detalle de cotización | `/api/v1/pur/cotizaciones/{cotizacion_id}/detalle` | GET | `pur_cotizacion_detalle` | Ver los productos y precios ofertados por proveedor, por línea. |
| Gestionar líneas de cotización | `/api/v1/pur/cotizaciones/{cotizacion_id}/detalle` | POST/PUT/DELETE | `pur_cotizacion_detalle` | Permitir al usuario cargar y ajustar ítems cotizados. |
| Consultar detalle de orden de compra | `/api/v1/pur/ordenes-compra/{orden_compra_id}/detalle` | GET | `pur_orden_compra_detalle` | Ver los productos, cantidades y precios incluidos en la OC. |
| Gestionar líneas de orden de compra | `/api/v1/pur/ordenes-compra/{orden_compra_id}/detalle` | POST/PUT/DELETE | `pur_orden_compra_detalle` | Crear y editar líneas en el flujo de creación/edición de OC. |
| Consultar detalle de recepción | `/api/v1/pur/recepciones/{recepcion_id}/detalle` | GET | `pur_recepcion_detalle` | Ver productos efectivamente recepcionados por línea. |
| Gestionar líneas de recepción | `/api/v1/pur/recepciones/{recepcion_id}/detalle` | POST/PUT/DELETE | `pur_recepcion_detalle` | Registrar cantidades recepcionadas, lotes, fechas de vencimiento y diferencias. |

### 9.2 Acciones de negocio (aprobaciones, estados, integración INV)

| Funcionalidad | Endpoint sugerido | Método | Entidad afectada | Motivo funcional |
|---------------|-------------------|--------|------------------|------------------|
| Aprobar solicitud de compra | `/api/v1/pur/solicitudes/{solicitud_id}/aprobar` | POST | `pur_solicitud_compra` | Formalizar la aprobación, registrar aprobador y fecha, cambiar estado a `aprobada`. |
| Rechazar solicitud de compra | `/api/v1/pur/solicitudes/{solicitud_id}/rechazar` | POST | `pur_solicitud_compra` | Registrar motivo de rechazo y cambiar estado a `rechazada`. |
| Marcar solicitud como procesada (se generó OC) | `/api/v1/pur/solicitudes/{solicitud_id}/marcar-procesada` | POST | `pur_solicitud_compra` | Ajustar campos `estado` y `orden_compra_generada`. |
| Marcar cotización ganadora | `/api/v1/pur/cotizaciones/{cotizacion_id}/marcar-ganadora` | POST | `pur_cotizacion` | Asegurar que dentro de una solicitud sólo exista una ganadora y reflejarlo claramente. |
| Aprobar orden de compra | `/api/v1/pur/ordenes-compra/{orden_compra_id}/aprobar` | POST | `pur_orden_compra` | Controlar flujo de aprobación de compras (WFL puede integrarse). |
| Anular orden de compra | `/api/v1/pur/ordenes-compra/{orden_compra_id}/anular` | POST | `pur_orden_compra` | Permitir anulación con motivo concreto, sin depender de un PUT genérico. |
| Procesar recepción con integración a inventario | `/api/v1/pur/recepciones/{recepcion_id}/procesar` | POST | `pur_recepcion` + tablas INV | Ejecutar: validar cantidades, generar movimiento de inventario en INV, actualizar `movimiento_inventario_id`, cambiar estado a `procesada`. |
| Enviar recepción a inspección de calidad | `/api/v1/pur/recepciones/{recepcion_id}/enviar-inspeccion` | POST | `pur_recepcion` + QMS | Flujos donde `requiere_inspeccion = true`: vincular con módulo QMS. |

### 9.3 Paginación, búsqueda avanzada y ordenamiento

| Funcionalidad | Endpoint sugerido | Método | Entidad | Motivo funcional |
|---------------|-------------------|--------|---------|------------------|
| Paginación general | Añadir `page`, `page_size` en todos los listados PUR | GET | Todas las entidades de listados | Manejar grandes volúmenes de datos (proveedores, solicitudes, OC, recepciones). |
| Ordenamiento configurable | Añadir `sort_by`, `order` en listados | GET | Proveedores, solicitudes, cotizaciones, OC, recepciones | Permitir ordenar por fecha, proveedor, estado, total, etc. |
| Búsqueda avanzada de proveedores | Parámetros adicionales (ej. `tipo_proveedor`, `categoria_proveedor`, `estado`) | GET `/proveedores` | `pur_proveedor` | Filtros más ricos, de acuerdo con la documentación de categorización y homologación. |

---

## 10. Endpoints incompletos

Se consideran **endpoints incompletos** aquellos que existen pero no cubren todas las necesidades funcionales esperadas.

- **Solicitudes de Compra (`/solicitudes`)**
  - Sólo gestionan cabecera: no hay forma de crear/editar/ver líneas asociadas a una solicitud.  
  - Estados (`borrador`, `pendiente_aprobacion`, `aprobada`, `rechazada`, `procesada`, `anulada`) están presentes como texto, pero no hay endpoints semánticos que regulen el cambio de estado ni reglas de negocio validadas por backend.

- **Cotizaciones (`/cotizaciones`)**
  - Lógica de “evaluar” y “marcar ganadora” se reduce a actualizar `estado` y `es_ganadora` a través de PUT genérico.  
  - No existe API para manejar items de cotización; el frontend no puede visualizar ni registrar las líneas que originan los totales.

- **Órdenes de Compra (`/ordenes-compra`)**
  - Campos para seguimiento de recepción (`items_recepcionados`, `porcentaje_recepcion`) existen en la cabecera, pero **no hay API** para gestionar el detalle de OC ni para mantener consistentes esos campos con lo efectivamente recepcionado.  
  - No hay endpoints semánticos `aprobar`, `emitir`, `anular`; todo se hace por PUT genérico.

- **Recepciones (`/recepciones`)**
  - No se gestionan líneas de recepción (detalles).  
  - `movimiento_inventario_id` se maneja como simple campo; no hay endpoint que dispare explícitamente la creación del movimiento de inventario en INV ni garantice su coherencia.  
  - Estados `borrador`, `procesada`, `inspeccion`, `aprobada`, `anulada` se gestionan vía PUT sin reglas explícitas ni endpoints semánticos.

- **Filtros y paginación**
  - Listados carecen de paginación y ordenamiento configurable; esto puede ser insuficiente para entornos productivos con grandes volúmenes.

---

## 11. Validación multi-tenant

**Aspectos positivos:**

- Todas las queries en `app/infrastructure/database/queries/pur/*.py`:
  - Reciben `client_id` como argumento.
  - Filtran por `Pur*Table.c.cliente_id == client_id` en selects, updates e inserts (añadiendo `cliente_id` a los payloads).  
  - No permiten pasar `cliente_id` desde el body de la request.  
  - Esto evita acceso cross-tenant por ID de entidad.

**Riesgos detectados:**

- **Validación de `empresa_id`:**
  - En todos los Create/Update que aceptan `empresa_id` (proveedores, solicitudes, cotizaciones, órdenes, recepciones), **no se valida** que la empresa pertenezca al `cliente_id` del usuario.  
  - El SQL modela `org_empresa` como tabla organizacional que debería estar ligada a un cliente; sin una validación explícita, un usuario podría enviar un `empresa_id` de otra empresa/cliente siempre que pase la FK de BD (si la BD centralizada no fuerza este vínculo).  
  - Este patrón es similar al detectado en otros módulos: correcto filtro por `cliente_id` en datos del módulo, pero sin validar relaciones cruzadas con ORG.

**Conclusión multi-tenant:**

- La capa PUR es **sólida** en el filtrado por `cliente_id`, reduciendo fuertemente el riesgo de lecturas o escrituras cross-tenant en sus propias tablas.  
- La brecha está en la **pertenencia de `empresa_id` al cliente**; esto puede permitir que se asocien registros PUR a empresas incorrectas (de otro tenant) si la BD y la capa ORG no bloquean ese escenario de forma global.

---

## 12. Validación de permisos

### 12.1 Estructura RBAC

- `5.- SCRIPT_RBAC_TABLAS_CENTRAL.sql` define:
  - Tabla `permiso` con campos: `permiso_id`, `codigo`, `nombre`, `descripcion`, `modulo_id`, `recurso`, `accion`, `es_activo`, etc.
  - Tabla `rol_permiso` con claves: `rol_permiso_id`, `cliente_id`, `rol_id`, `permiso_id` y llave única `(cliente_id, rol_id, permiso_id)`.

- No define los registros de permisos; se espera que se carguen vía scripts de seed (`SEED_PERMISOS_RBAC*.sql`).  
  - En el repo actual, `SEED_PERMISOS_RBAC.sql` está vacío y no existe un seed específico para PUR con códigos `pur.*`.

### 12.2 Uso en backend PUR

- Todos los endpoints PUR utilizan `require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.accion")`.  
  - Esto requiere que exista en la tabla `permiso` un registro con `codigo = "pur.recurso.accion"`.

- Recursos/acciones usados:
  - `pur.proveedor.leer/crear/actualizar`
  - `pur.contacto.leer/crear/actualizar`
  - `pur.producto_proveedor.leer/crear/actualizar`
  - `pur.solicitud.leer/crear/actualizar`
  - `pur.cotizacion.leer/crear/actualizar`
  - `pur.orden_compra.leer/crear/actualizar`
  - `pur.recepcion.leer/crear/actualizar`

### 12.3 GAP RBAC

- **Catálogo de permisos PUR no inicializado:**  
  - La ausencia de entries en `SEED_PERMISOS_RBAC.sql` para `pur.*` implica que, sin scripts adicionales, estos permisos **no existirían** en la tabla `permiso` tras una instalación limpia.  
  - Esto puede causar:
    - Que las verificaciones de permiso fallen siempre (si el sistema considera que permisos inexistentes son denegados).  
    - O que se requiera configuración manual posterior, lo que debilita la reproducibilidad y la coherencia en entornos nuevos.

- **Acciones faltantes:**  
  - Sólo se utilizan `leer`, `crear`, `actualizar`.  
  - No se prevén explícitamente permisos para `eliminar` o para acciones de negocio (`aprobar`, `rechazar`, `procesar`, `anular`) porque dichos endpoints aún no existen.

**Conclusión RBAC:**  

- El diseño del backend PUR está listo para un **RBAC fino por recurso**, pero el catálogo base (`permiso`) no incluye las entradas necesarias documentadas en este backend. Esto es una brecha entre la estructura RBAC central y el módulo PUR que debe cerrarse con scripts de seed y alineación de nomenclatura.

---

## 13. Brechas funcionales detectadas (GAPS)

1. **Ausencia de endpoints para detalles de documentos PUR**  
   - BD tiene tablas de detalle (`pur_solicitud_compra_detalle`, `pur_cotizacion_detalle`, `pur_orden_compra_detalle`, `pur_recepcion_detalle`), pero **no hay endpoints ni servicios** para gestionarlas.  
   - Impacto: El frontend no puede construir ni visualizar formularios completos de ítems de solicitud, cotización, orden de compra y recepción; sólo puede ver/editar cabeceras.

2. **Acciones de negocio incompletas para flujos de aprobación**  
   - Estados y campos (`requiere_aprobacion`, `aprobado_por_usuario_id`, `fecha_aprobacion`, `motivo_rechazo`, `orden_compra_generada`, `es_ganadora`) existen en BD y schemas, pero **no hay endpoints semánticos** que gestionen el flujo de aprobación/rechazo de solicitudes, cotizaciones y órdenes de compra.  
   - Impacto: Lógica de aprobación queda en la UI o en llamadas PUT genéricas, sin reglas centralizadas ni auditoría clara de transiciones.

3. **Integración con INV no está implementada explícitamente**  
   - Documentación indica que la recepción de mercadería **genera movimientos de inventario automáticos**.  
   - Aunque `recepcion` tiene campo `movimiento_inventario_id` y se relaciona con INV, **no hay servicio ni endpoint PUR** que cree o actualice estos movimientos en INV de forma orquestada.  
   - Impacto: Inconsistencias posibles entre compras y stock real; se rompe la trazabilidad `OC → Recepción → Movimiento INV` si eso se deja fuera del módulo.

4. **Validación de `empresa_id` respecto de `cliente_id`**  
   - Se recibe `empresa_id` en la mayoría de Create/Update, pero no hay validación explícita de que la empresa pertenezca al cliente del usuario.  
   - Impacto: Riesgo potencial de asociar registros PUR a empresas de otro tenant si la BD central no protege esta relación a nivel de FK multi-tenant.

5. **RBAC PUR sin catálogo inicial coherente**  
   - Backend espera permisos `pur.*` pero `SEED_PERMISOS_RBAC.sql` está vacío.  
   - Impacto: En despliegues nuevos, PUR puede quedar inoperante o expuesto con configuraciones manuales inconsistentes.

6. **Falta de paginación y ordenamiento configurables**  
   - Listados de proveedores, solicitudes, cotizaciones, OC y recepciones no tienen paginación ni ordenamiento dinámico.  
   - Impacto: Problemas de rendimiento y UX en empresas con muchos registros.

7. **Acciones de anulación y cambio de estado no estandarizadas**  
   - Aunque hay campos `estado` y `motivo_anulacion`, no hay endpoints dedicados para `anular` documentos ni para transiciones específicas.  
   - Impacto: Lógica de transición de estados dispersa, sin control claro y con alto riesgo de estados inválidos establecidos por errores de integración.

8. **Diferencia estructural en manejo de moneda en Cotizaciones**  
   - SQL define `moneda_id` como FK; backend trabaja con `moneda` (string) sin FK.  
   - Impacto: Se pierde integridad referencial con catálogo de monedas desde PUR; pueden existir valores de moneda inválidos o inconsistentes.

---

## 14. Propuesta de mejoras

Las siguientes mejoras están enfocadas en alinear completamente el backend PUR con la documentación funcional y la estructura de BD.

### 14.1 Endpoints y modelos para detalles de documentos

- **Añadir endpoints y schemas para:**
  - `pur_solicitud_compra_detalle`
  - `pur_cotizacion_detalle`
  - `pur_orden_compra_detalle`
  - `pur_recepcion_detalle`
- **Exponer en la API:**
  - Listado de líneas por documento (GET).  
  - Creación, actualización y eliminación de líneas (POST/PUT/DELETE), respetando reglas de negocio (ej. no editar si documento está aprobado/anulado).  
  - Opcionalmente, incluir un parámetro `incluir_detalle=true` en los endpoints de detalle de cabecera para obtener cabecera + detalle en una sola llamada.

### 14.2 Endpoints de acciones de negocio (aprobación, rechazo, generación de OC, etc.)

- **Solicitudes de Compra**  
  - Endpoints dedicados para aprobar, rechazar y marcar como procesada.  
  - Validar que sólo ciertos roles (según RBAC) puedan aprobar o rechazar.  
  - Registrar `aprobado_por_usuario_id`, `fecha_aprobacion` y `motivo_rechazo` de forma controlada.

- **Cotizaciones**  
  - Endpoint para marcar una cotización como ganadora y, si aplica, desmarcar otras cotizaciones asociadas a la misma solicitud.  
  - Control de estados (`pendiente`, `recibida`, `evaluada`, `aceptada`, `rechazada`, `vencida`) mediante acciones semánticas.

- **Órdenes de Compra**  
  - Endpoints para aprobar, emitir y anular OCs con controles de negocio (por ejemplo, no anular si ya hay recepciones completas).  
  - Flujo para generar órdenes de compra a partir de una solicitud y/o cotización (puede ser un endpoint `POST /ordenes-compra/desde-solicitud` o lógica interna documentada).

### 14.3 Integración explícita con INV desde Recepciones

- **Implementar un endpoint de “procesar recepción”**, que:
  - Valide las líneas de recepción frente a `pur_orden_compra_detalle` (cantidades ordenadas vs recepcionadas).  
  - Genere un movimiento de inventario en INV (cabecera + detalle) apropiado para el tipo de recepción.  
  - Actualice `movimiento_inventario_id` en `pur_recepcion` y los campos de avance en `pur_orden_compra` (`items_recepcionados`, `porcentaje_recepcion`, `estado`).  
  - Integre con QMS cuando `requiere_inspeccion` sea `true` (enviando a inspección y actualizando estados).

### 14.4 Validaciones multi-tenant reforzadas

- Añadir una validación de pertenencia `empresa_id`–`cliente_id` a un nivel común (servicio compartido o dependencia) y reutilizarla en:
  - Creación/actualización de proveedores, solicitudes, cotizaciones, órdenes y recepciones.  
  - Filtros por `empresa_id` en listados.
- Esto garantiza que un usuario de un tenant no pueda referenciar empresas de otro tenant aunque conozca sus IDs.

### 14.5 Mejoras en RBAC PUR

- **Crear un script de seed de permisos para PUR** que incluya al menos:
  - `pur.proveedor.leer/crear/actualizar`
  - `pur.contacto.leer/crear/actualizar`
  - `pur.producto_proveedor.leer/crear/actualizar`
  - `pur.solicitud.leer/crear/actualizar`
  - `pur.cotizacion.leer/crear/actualizar`
  - `pur.orden_compra.leer/crear/actualizar`
  - `pur.recepcion.leer/crear/actualizar`
- **Extender el modelo de permisos** para futuras acciones de negocio:
  - `pur.solicitud.aprobar/rechazar`
  - `pur.cotizacion.marcar_ganadora`
  - `pur.orden_compra.aprobar/anular`
  - `pur.recepcion.procesar/enviar_inspeccion`

### 14.6 Paginación, ordenamiento y búsqueda avanzada

- Añadir soporte de **paginación y ordenamiento** a todos los listados PUR:  
  - Parámetros sugeridos: `page`, `page_size`, `sort_by`, `order`.  
  - Asegurar índices adecuados en BD para los campos más usados en filtros/ordenamientos.
- Ampliar filtros en proveedores, solicitudes, cotizaciones, órdenes y recepciones según necesidades de UX (por ejemplo, por `tipo_proveedor`, `categoria_proveedor`, `estado` compuesto, rangos de importe).

### 14.7 Alineación moneda–catálogo en Cotizaciones

- Definir una estrategia clara para manejar moneda en cotizaciones:
  - O bien **usar `moneda_id`** (FK a `cat_moneda`) conforme al SQL y exponerlo en schemas/endpoints.  
  - O bien actualizar el SQL de referencia para reflejar el uso de `moneda` como string, alineándolo con otros módulos.
- En ambos casos documentar la decisión y asegurar integridad con el módulo de catálogos monetarios.

---

## 15. Plan de implementación

### Prioridad Alta

- **Implementar endpoints para detalles de documentos PUR:**  
  - CRUD básico de `pur_solicitud_compra_detalle`, `pur_cotizacion_detalle`, `pur_orden_compra_detalle`, `pur_recepcion_detalle`.  
  - Actualizar schemas y servicios para que los formularios de frontend puedan gestionar líneas de documentos.

- **Refuerzo multi-tenant en `empresa_id`:**  
  - Agregar validación de pertenencia empresa–cliente en todos los Create/Update y listados que reciban `empresa_id`.  
  - Impacto: reduce riesgos de datos cross-tenant y asegura coherencia organizacional.

- **Seed de permisos RBAC para PUR:**  
  - Crear un script de inicialización de permisos `pur.*` alineado con los endpoints actuales (leer/crear/actualizar).  
  - Impacto: hace operativo el módulo en entornos nuevos sin intervención manual y garantiza coherencia de seguridad.

### Prioridad Media

- **Endpoints semánticos para flujos de aprobación:**  
  - Implementar acciones `aprobar`, `rechazar`, `marcar-procesada` para solicitudes; `marcar-ganadora` para cotizaciones; `aprobar/anular` para órdenes.  
  - Añadir permisos específicos (`pur.solicitud.aprobar`, etc.) y reglas de negocio claras.

- **Integración explícita con INV en Recepciones:**  
  - Endpoint `procesar` para generar movimientos de inventario y actualizar estados en OC y Recepciones.  
  - Impacto: cierra el ciclo funcional PUR–INV y garantiza stock correcto.

- **Paginación y ordenamiento en listados:**  
  - Incorporar `page`, `page_size`, `sort_by`, `order` en listados de proveedores, solicitudes, cotizaciones, órdenes y recepciones.  
  - Ajustar queries e índices según el patrón de uso.

### Prioridad Baja

- **Endpoints de anulación y desactivación explícitos:**  
  - Por ejemplo, `DELETE` lógico o `POST /{id}/anular` para entidades que lo requieran, con campos `motivo_anulacion` y `estado` controlados.  
  - Esto mejora la claridad de la API y facilita auditoría funcional.

- **Mejoras de búsqueda avanzada y reporting parcial:**  
  - Filtros enriquecidos por tipo/categoría de proveedor, montos de documentos, estados combinados, etc.  
  - Endpoints de apoyo para dashboards de compras (ej. resumen de OC por estado o proveedor).

- **Alineación final moneda–catálogo:**  
  - Ajustar definitivamente el manejo de moneda (`moneda_id` vs `moneda`) tanto en SQL como en backend PUR y otros módulos relacionados, asegurando consistencia en todo el ERP.

---

**Fin del documento.**

¿Deseas que proceda con la implementación de las mejoras recomendadas para el módulo PUR?
