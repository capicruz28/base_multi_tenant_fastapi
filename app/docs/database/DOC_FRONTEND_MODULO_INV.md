# Documentación Frontend — Módulo INV (Inventarios)

**Versión:** 1.0  
**Fecha:** 2026-02-18  
**Módulo:** INV - Inventarios ERP

---

## 📋 Índice

1. [Información General](#información-general)
2. [Autenticación](#autenticación)
3. [Endpoints](#endpoints)
4. [Schemas](#schemas)
5. [Ejemplos de Uso](#ejemplos-de-uso)
6. [Códigos de Error](#códigos-de-error)
7. [Rutas SPA Recomendadas](#rutas-spa-recomendadas)
8. [Flujo de Implementación Recomendado](#flujo-de-implementación-recomendado)

---

## 🔑 Información General

### Base URL
```
/api/v1/inv
```

### Dependencias
- **Módulo ORG:** Requiere tener empresas, sucursales y centros de costo configurados.
- **Orden recomendado:** Configurar primero ORG, luego INV.

---

## 🔐 Autenticación

Todos los endpoints requieren autenticación mediante JWT token en el header:

```http
Authorization: Bearer <token>
```

El `cliente_id` se obtiene automáticamente del token, **nunca debe enviarse en el body**.

---

## 📡 Endpoints

### 1. Categorías de Producto

#### Listar Categorías
```http
GET /api/v1/inv/categorias
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `solo_activos` (boolean, default: true): Solo categorías activas

**Response:** `200 OK`
```json
[
  {
    "categoria_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "codigo": "CAT001",
    "nombre": "Electrónica",
    "descripcion": "Productos electrónicos",
    "categoria_padre_id": null,
    "nivel": 1,
    "ruta_jerarquica": "Electrónica",
    "cuenta_contable_inventario": null,
    "cuenta_contable_costo_venta": null,
    "metodo_costeo_defecto": "promedio",
    "es_activo": true,
    "fecha_creacion": "2026-02-18T10:00:00Z",
    "fecha_actualizacion": null,
    "usuario_creacion_id": null
  }
]
```

#### Detalle de Categoría
```http
GET /api/v1/inv/categorias/{categoria_id}
```

**Response:** `200 OK` (mismo schema que listar)

#### Crear Categoría
```http
POST /api/v1/inv/categorias
```

**Body:**
```json
{
  "empresa_id": "uuid",
  "codigo": "CAT001",
  "nombre": "Electrónica",
  "descripcion": "Productos electrónicos",
  "categoria_padre_id": null,
  "nivel": 1,
  "ruta_jerarquica": "Electrónica",
  "cuenta_contable_inventario": null,
  "cuenta_contable_costo_venta": null,
  "metodo_costeo_defecto": "promedio",
  "es_activo": true
}
```

**Response:** `201 Created` (schema completo)

#### Actualizar Categoría
```http
PUT /api/v1/inv/categorias/{categoria_id}
```

**Body:** (todos los campos opcionales)
```json
{
  "nombre": "Electrónica Actualizada",
  "descripcion": "Nueva descripción"
}
```

**Response:** `200 OK` (schema completo)

---

### 2. Unidades de Medida

#### Listar Unidades de Medida
```http
GET /api/v1/inv/unidades-medida
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `solo_activos` (boolean, default: true): Solo unidades activas

**Response:** `200 OK`
```json
[
  {
    "unidad_medida_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "codigo": "UN",
    "nombre": "Unidad",
    "simbolo": "und",
    "tipo_unidad": "cantidad",
    "es_unidad_base": true,
    "factor_conversion_base": null,
    "decimales_permitidos": 2,
    "es_activo": true,
    "fecha_creacion": "2026-02-18T10:00:00Z",
    "fecha_actualizacion": null,
    "usuario_creacion_id": null
  }
]
```

#### Detalle de Unidad de Medida
```http
GET /api/v1/inv/unidades-medida/{unidad_medida_id}
```

#### Crear Unidad de Medida
```http
POST /api/v1/inv/unidades-medida
```

**Body:**
```json
{
  "empresa_id": "uuid",
  "codigo": "KG",
  "nombre": "Kilogramo",
  "simbolo": "kg",
  "tipo_unidad": "peso",
  "es_unidad_base": true,
  "factor_conversion_base": null,
  "decimales_permitidos": 2,
  "es_activo": true
}
```

#### Actualizar Unidad de Medida
```http
PUT /api/v1/inv/unidades-medida/{unidad_medida_id}
```

---

### 3. Productos

#### Listar Productos
```http
GET /api/v1/inv/productos
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `categoria_id` (UUID, opcional): Filtrar por categoría
- `tipo_producto` (string, opcional): Filtrar por tipo ('bien', 'servicio', 'materia_prima', etc.)
- `solo_activos` (boolean, default: true): Solo productos activos
- `buscar` (string, opcional): Búsqueda por nombre, SKU o código de barras

**Response:** `200 OK`
```json
[
  {
    "producto_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "codigo_sku": "PROD001",
    "codigo_barra": "1234567890123",
    "codigo_interno": "INT001",
    "codigo_fabricante": "FAB001",
    "nombre": "Laptop Dell XPS 15",
    "nombre_corto": "XPS 15",
    "descripcion": "Laptop Dell XPS 15, 16GB RAM, 512GB SSD",
    "descripcion_corta": "Laptop Dell XPS 15",
    "categoria_id": "uuid",
    "subcategoria_id": null,
    "marca": "Dell",
    "modelo": "XPS 15",
    "linea_producto": "Premium",
    "tipo_producto": "bien",
    "subtipo_producto": null,
    "unidad_medida_base_id": "uuid",
    "unidad_medida_compra_id": null,
    "unidad_medida_venta_id": null,
    "factor_conversion_compra": 1.0,
    "factor_conversion_venta": 1.0,
    "peso_kg": 2.5,
    "volumen_m3": 0.001,
    "largo_cm": 35.0,
    "ancho_cm": 23.0,
    "alto_cm": 1.8,
    "color": "Negro",
    "talla": null,
    "atributos_personalizados": null,
    "especificaciones_tecnicas": null,
    "maneja_inventario": true,
    "maneja_lotes": false,
    "maneja_series": true,
    "maneja_vencimiento": false,
    "dias_vida_util": null,
    "requiere_refrigeracion": false,
    "es_perecible": false,
    "stock_minimo": 10.0,
    "stock_maximo": 100.0,
    "punto_reorden": 20.0,
    "es_comprable": true,
    "tiempo_entrega_dias": 7,
    "cantidad_minima_compra": 1.0,
    "multiplo_compra": 1.0,
    "es_vendible": true,
    "requiere_autorizacion_venta": false,
    "es_fabricable": false,
    "tiene_lista_materiales": false,
    "metodo_costeo": "promedio",
    "costo_estandar": 1500.00,
    "costo_ultima_compra": 1450.00,
    "costo_promedio": 1475.00,
    "moneda_costo": "PEN",
    "precio_base_venta": 2000.00,
    "moneda_venta": "PEN",
    "afecto_igv": true,
    "porcentaje_igv": 18.00,
    "codigo_sunat": null,
    "tipo_afectacion_igv": "10",
    "imagen_principal_url": "https://example.com/images/product.jpg",
    "imagenes_adicionales": null,
    "ficha_tecnica_url": null,
    "proveedor_habitual_id": null,
    "estado": "activo",
    "es_activo": true,
    "fecha_creacion": "2026-02-18T10:00:00Z",
    "fecha_actualizacion": null,
    "usuario_creacion_id": null,
    "usuario_actualizacion_id": null,
    "observaciones": null
  }
]
```

#### Detalle de Producto
```http
GET /api/v1/inv/productos/{producto_id}
```

#### Crear Producto
```http
POST /api/v1/inv/productos
```

**Body (campos mínimos requeridos):**
```json
{
  "empresa_id": "uuid",
  "codigo_sku": "PROD001",
  "nombre": "Laptop Dell XPS 15",
  "tipo_producto": "bien",
  "unidad_medida_base_id": "uuid"
}
```

**Body (completo con todos los campos):**
```json
{
  "empresa_id": "uuid",
  "codigo_sku": "PROD001",
  "codigo_barra": "1234567890123",
  "codigo_interno": "INT001",
  "codigo_fabricante": "FAB001",
  "nombre": "Laptop Dell XPS 15",
  "nombre_corto": "XPS 15",
  "descripcion": "Laptop Dell XPS 15, 16GB RAM, 512GB SSD",
  "descripcion_corta": "Laptop Dell XPS 15",
  "categoria_id": "uuid",
  "subcategoria_id": null,
  "marca": "Dell",
  "modelo": "XPS 15",
  "linea_producto": "Premium",
  "tipo_producto": "bien",
  "subtipo_producto": null,
  "unidad_medida_base_id": "uuid",
  "unidad_medida_compra_id": null,
  "unidad_medida_venta_id": null,
  "factor_conversion_compra": 1.0,
  "factor_conversion_venta": 1.0,
  "peso_kg": 2.5,
  "volumen_m3": 0.001,
  "largo_cm": 35.0,
  "ancho_cm": 23.0,
  "alto_cm": 1.8,
  "color": "Negro",
  "talla": null,
  "atributos_personalizados": null,
  "especificaciones_tecnicas": null,
  "maneja_inventario": true,
  "maneja_lotes": false,
  "maneja_series": true,
  "maneja_vencimiento": false,
  "dias_vida_util": null,
  "requiere_refrigeracion": false,
  "es_perecible": false,
  "stock_minimo": 10.0,
  "stock_maximo": 100.0,
  "punto_reorden": 20.0,
  "es_comprable": true,
  "tiempo_entrega_dias": 7,
  "cantidad_minima_compra": 1.0,
  "multiplo_compra": 1.0,
  "es_vendible": true,
  "requiere_autorizacion_venta": false,
  "es_fabricable": false,
  "tiene_lista_materiales": false,
  "metodo_costeo": "promedio",
  "costo_estandar": 1500.00,
  "costo_ultima_compra": null,
  "costo_promedio": null,
  "moneda_costo": "PEN",
  "precio_base_venta": 2000.00,
  "moneda_venta": "PEN",
  "afecto_igv": true,
  "porcentaje_igv": 18.00,
  "codigo_sunat": null,
  "tipo_afectacion_igv": "10",
  "imagen_principal_url": null,
  "imagenes_adicionales": null,
  "ficha_tecnica_url": null,
  "proveedor_habitual_id": null,
  "estado": "activo",
  "es_activo": true,
  "observaciones": null
}
```

#### Actualizar Producto
```http
PUT /api/v1/inv/productos/{producto_id}
```

**Body:** (todos los campos opcionales, solo enviar los que se desean actualizar)

---

### 4. Almacenes

#### Listar Almacenes
```http
GET /api/v1/inv/almacenes
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `sucursal_id` (UUID, opcional): Filtrar por sucursal
- `solo_activos` (boolean, default: true): Solo almacenes activos

**Response:** `200 OK`
```json
[
  {
    "almacen_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "sucursal_id": "uuid",
    "codigo": "ALM001",
    "nombre": "Almacén Principal",
    "descripcion": "Almacén principal de la empresa",
    "tipo_almacen": "general",
    "direccion": "Av. Principal 123",
    "responsable_usuario_id": null,
    "responsable_nombre": "Juan Pérez",
    "es_almacen_principal": true,
    "permite_ventas": true,
    "permite_compras": true,
    "permite_produccion": false,
    "capacidad_m3": 1000.0,
    "capacidad_kg": 50000.0,
    "capacidad_unidades": 10000,
    "centro_costo_id": "uuid",
    "es_activo": true,
    "fecha_creacion": "2026-02-18T10:00:00Z",
    "fecha_actualizacion": null,
    "usuario_creacion_id": null
  }
]
```

#### Detalle de Almacén
```http
GET /api/v1/inv/almacenes/{almacen_id}
```

#### Crear Almacén
```http
POST /api/v1/inv/almacenes
```

**Body:**
```json
{
  "empresa_id": "uuid",
  "sucursal_id": "uuid",
  "codigo": "ALM001",
  "nombre": "Almacén Principal",
  "descripcion": "Almacén principal de la empresa",
  "tipo_almacen": "general",
  "direccion": "Av. Principal 123",
  "responsable_usuario_id": null,
  "responsable_nombre": "Juan Pérez",
  "es_almacen_principal": true,
  "permite_ventas": true,
  "permite_compras": true,
  "permite_produccion": false,
  "capacidad_m3": 1000.0,
  "capacidad_kg": 50000.0,
  "capacidad_unidades": 10000,
  "centro_costo_id": "uuid",
  "es_activo": true
}
```

#### Actualizar Almacén
```http
PUT /api/v1/inv/almacenes/{almacen_id}
```

---

### 5. Stock

#### Listar Stocks
```http
GET /api/v1/inv/stock
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `producto_id` (UUID, opcional): Filtrar por producto
- `almacen_id` (UUID, opcional): Filtrar por almacén

**Response:** `200 OK`
```json
[
  {
    "stock_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "producto_id": "uuid",
    "almacen_id": "uuid",
    "cantidad_actual": 50.0,
    "cantidad_reservada": 10.0,
    "cantidad_disponible": 40.0,
    "cantidad_transito": 5.0,
    "costo_promedio": 1475.00,
    "valor_total": 73750.00,
    "moneda": "PEN",
    "stock_minimo": 10.0,
    "stock_maximo": 100.0,
    "punto_reorden": 20.0,
    "ubicacion_almacen": "Pasillo 3-Rack A-Nivel 2",
    "fecha_ultimo_movimiento": "2026-02-18T10:00:00Z",
    "fecha_ultima_compra": "2026-02-15T10:00:00Z",
    "fecha_ultima_venta": "2026-02-17T10:00:00Z",
    "fecha_actualizacion": "2026-02-18T10:00:00Z"
  }
]
```

#### Detalle de Stock
```http
GET /api/v1/inv/stock/{stock_id}
```

#### Stock por Producto y Almacén (Consulta Rápida)
```http
GET /api/v1/inv/stock/producto/{producto_id}/almacen/{almacen_id}
```

**Response:** `200 OK` (schema de Stock) o `null` si no existe

#### Crear Stock
```http
POST /api/v1/inv/stock
```

**Body:**
```json
{
  "empresa_id": "uuid",
  "producto_id": "uuid",
  "almacen_id": "uuid",
  "cantidad_actual": 50.0,
  "cantidad_reservada": 0.0,
  "cantidad_transito": 0.0,
  "costo_promedio": 1475.00,
  "moneda": "PEN",
  "stock_minimo": 10.0,
  "stock_maximo": 100.0,
  "punto_reorden": 20.0,
  "ubicacion_almacen": "Pasillo 3-Rack A-Nivel 2"
}
```

#### Actualizar Stock
```http
PUT /api/v1/inv/stock/{stock_id}
```

---

### 6. Tipos de Movimiento

#### Listar Tipos de Movimiento
```http
GET /api/v1/inv/tipos-movimiento
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `solo_activos` (boolean, default: true): Solo tipos activos

**Response:** `200 OK`
```json
[
  {
    "tipo_movimiento_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "codigo": "COMP",
    "nombre": "Compra",
    "descripcion": "Movimiento por compra",
    "clase_movimiento": "entrada",
    "afecta_costo": true,
    "requiere_autorizacion": false,
    "genera_asiento_contable": true,
    "cuenta_contable_debito": "601",
    "cuenta_contable_credito": "201",
    "requiere_documento_referencia": true,
    "tipo_documento_referencia": "orden_compra",
    "es_activo": true,
    "es_tipo_sistema": false,
    "fecha_creacion": "2026-02-18T10:00:00Z",
    "fecha_actualizacion": null,
    "usuario_creacion_id": null
  }
]
```

#### Detalle de Tipo de Movimiento
```http
GET /api/v1/inv/tipos-movimiento/{tipo_movimiento_id}
```

#### Crear Tipo de Movimiento
```http
POST /api/v1/inv/tipos-movimiento
```

**Body:**
```json
{
  "empresa_id": "uuid",
  "codigo": "COMP",
  "nombre": "Compra",
  "descripcion": "Movimiento por compra",
  "clase_movimiento": "entrada",
  "afecta_costo": true,
  "requiere_autorizacion": false,
  "genera_asiento_contable": true,
  "cuenta_contable_debito": "601",
  "cuenta_contable_credito": "201",
  "requiere_documento_referencia": true,
  "tipo_documento_referencia": "orden_compra",
  "es_activo": true,
  "es_tipo_sistema": false
}
```

#### Actualizar Tipo de Movimiento
```http
PUT /api/v1/inv/tipos-movimiento/{tipo_movimiento_id}
```

---

### 7. Movimientos

#### Listar Movimientos
```http
GET /api/v1/inv/movimientos
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `tipo_movimiento_id` (UUID, opcional): Filtrar por tipo de movimiento
- `almacen_id` (UUID, opcional): Filtrar por almacén (origen o destino)
- `estado` (string, opcional): Filtrar por estado ('borrador', 'autorizado', 'procesado', 'anulado')
- `fecha_desde` (date, opcional): Fecha desde (formato: YYYY-MM-DD)
- `fecha_hasta` (date, opcional): Fecha hasta (formato: YYYY-MM-DD)

**Response:** `200 OK`
```json
[
  {
    "movimiento_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "numero_movimiento": "MOV-001",
    "tipo_movimiento_id": "uuid",
    "fecha_movimiento": "2026-02-18T10:00:00Z",
    "fecha_contable": "2026-02-18",
    "almacen_origen_id": null,
    "almacen_destino_id": "uuid",
    "modulo_origen": "PUR",
    "documento_referencia_tipo": "orden_compra",
    "documento_referencia_id": "uuid",
    "documento_referencia_numero": "OC-001",
    "tercero_tipo": "proveedor",
    "tercero_id": "uuid",
    "tercero_nombre": "Proveedor ABC",
    "total_items": 5,
    "total_cantidad": 100.0,
    "total_costo": 147500.00,
    "moneda": "PEN",
    "estado": "procesado",
    "requiere_autorizacion": false,
    "autorizado_por_usuario_id": null,
    "fecha_autorizacion": null,
    "observaciones": "Movimiento de compra",
    "motivo_anulacion": null,
    "centro_costo_id": "uuid",
    "fecha_creacion": "2026-02-18T10:00:00Z",
    "fecha_actualizacion": null,
    "fecha_procesado": "2026-02-18T10:05:00Z",
    "usuario_creacion_id": "uuid",
    "usuario_procesado_id": "uuid"
  }
]
```

#### Detalle de Movimiento
```http
GET /api/v1/inv/movimientos/{movimiento_id}
```

#### Crear Movimiento
```http
POST /api/v1/inv/movimientos
```

**Body:**
```json
{
  "empresa_id": "uuid",
  "numero_movimiento": "MOV-001",
  "tipo_movimiento_id": "uuid",
  "fecha_movimiento": "2026-02-18T10:00:00Z",
  "fecha_contable": "2026-02-18",
  "almacen_origen_id": null,
  "almacen_destino_id": "uuid",
  "modulo_origen": "PUR",
  "documento_referencia_tipo": "orden_compra",
  "documento_referencia_id": "uuid",
  "documento_referencia_numero": "OC-001",
  "tercero_tipo": "proveedor",
  "tercero_id": "uuid",
  "tercero_nombre": "Proveedor ABC",
  "total_items": 5,
  "total_cantidad": 100.0,
  "total_costo": 147500.00,
  "moneda": "PEN",
  "estado": "borrador",
  "requiere_autorizacion": false,
  "observaciones": "Movimiento de compra",
  "centro_costo_id": "uuid"
}
```

#### Actualizar Movimiento
```http
PUT /api/v1/inv/movimientos/{movimiento_id}
```

---

### 8. Inventario Físico

#### Listar Inventarios Físicos
```http
GET /api/v1/inv/inventario-fisico
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `almacen_id` (UUID, opcional): Filtrar por almacén
- `estado` (string, opcional): Filtrar por estado ('en_proceso', 'finalizado', 'ajustado', 'anulado')
- `fecha_desde` (date, opcional): Fecha desde (formato: YYYY-MM-DD)
- `fecha_hasta` (date, opcional): Fecha hasta (formato: YYYY-MM-DD)

**Response:** `200 OK`
```json
[
  {
    "inventario_fisico_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "numero_inventario": "INV-001",
    "fecha_inventario": "2026-02-18",
    "almacen_id": "uuid",
    "tipo_inventario": "total",
    "descripcion": "Inventario físico mensual",
    "categoria_id": null,
    "ubicacion_almacen": null,
    "estado": "en_proceso",
    "supervisor_usuario_id": "uuid",
    "supervisor_nombre": "Juan Pérez",
    "total_productos_contados": 0,
    "total_diferencias": 0,
    "valor_diferencias": 0.0,
    "movimiento_ajuste_id": null,
    "observaciones": null,
    "fecha_creacion": "2026-02-18T10:00:00Z",
    "fecha_finalizacion": null,
    "fecha_ajuste": null,
    "usuario_creacion_id": "uuid"
  }
]
```

#### Detalle de Inventario Físico
```http
GET /api/v1/inv/inventario-fisico/{inventario_fisico_id}
```

#### Crear Inventario Físico
```http
POST /api/v1/inv/inventario-fisico
```

**Body:**
```json
{
  "empresa_id": "uuid",
  "numero_inventario": "INV-001",
  "fecha_inventario": "2026-02-18",
  "almacen_id": "uuid",
  "tipo_inventario": "total",
  "descripcion": "Inventario físico mensual",
  "categoria_id": null,
  "ubicacion_almacen": null,
  "estado": "en_proceso",
  "supervisor_usuario_id": "uuid",
  "supervisor_nombre": "Juan Pérez",
  "observaciones": null
}
```

#### Actualizar Inventario Físico
```http
PUT /api/v1/inv/inventario-fisico/{inventario_fisico_id}
```

---

## 📋 Schemas TypeScript (Ejemplo)

```typescript
// Categoría
interface Categoria {
  categoria_id: string;
  cliente_id: string;
  empresa_id: string;
  codigo: string;
  nombre: string;
  descripcion?: string;
  categoria_padre_id?: string;
  nivel?: number;
  ruta_jerarquica?: string;
  cuenta_contable_inventario?: string;
  cuenta_contable_costo_venta?: string;
  metodo_costeo_defecto?: string;
  es_activo: boolean;
  fecha_creacion?: string;
  fecha_actualizacion?: string;
  usuario_creacion_id?: string;
}

// Producto
interface Producto {
  producto_id: string;
  cliente_id: string;
  empresa_id: string;
  codigo_sku: string;
  codigo_barra?: string;
  codigo_interno?: string;
  codigo_fabricante?: string;
  nombre: string;
  nombre_corto?: string;
  descripcion?: string;
  descripcion_corta?: string;
  categoria_id?: string;
  subcategoria_id?: string;
  marca?: string;
  modelo?: string;
  linea_producto?: string;
  tipo_producto: string;
  subtipo_producto?: string;
  unidad_medida_base_id: string;
  unidad_medida_compra_id?: string;
  unidad_medida_venta_id?: string;
  factor_conversion_compra?: number;
  factor_conversion_venta?: number;
  peso_kg?: number;
  volumen_m3?: number;
  largo_cm?: number;
  ancho_cm?: number;
  alto_cm?: number;
  color?: string;
  talla?: string;
  atributos_personalizados?: string;
  especificaciones_tecnicas?: string;
  maneja_inventario?: boolean;
  maneja_lotes?: boolean;
  maneja_series?: boolean;
  maneja_vencimiento?: boolean;
  dias_vida_util?: number;
  requiere_refrigeracion?: boolean;
  es_perecible?: boolean;
  stock_minimo?: number;
  stock_maximo?: number;
  punto_reorden?: number;
  es_comprable?: boolean;
  tiempo_entrega_dias?: number;
  cantidad_minima_compra?: number;
  multiplo_compra?: number;
  es_vendible?: boolean;
  requiere_autorizacion_venta?: boolean;
  es_fabricable?: boolean;
  tiene_lista_materiales?: boolean;
  metodo_costeo?: string;
  costo_estandar?: number;
  costo_ultima_compra?: number;
  costo_promedio?: number;
  moneda_costo?: string;
  precio_base_venta?: number;
  moneda_venta?: string;
  afecto_igv?: boolean;
  porcentaje_igv?: number;
  codigo_sunat?: string;
  tipo_afectacion_igv?: string;
  imagen_principal_url?: string;
  imagenes_adicionales?: string;
  ficha_tecnica_url?: string;
  proveedor_habitual_id?: string;
  estado?: string;
  es_activo: boolean;
  fecha_creacion?: string;
  fecha_actualizacion?: string;
  usuario_creacion_id?: string;
  usuario_actualizacion_id?: string;
  observaciones?: string;
}

// Stock
interface Stock {
  stock_id: string;
  cliente_id: string;
  empresa_id: string;
  producto_id: string;
  almacen_id: string;
  cantidad_actual: number;
  cantidad_reservada?: number;
  cantidad_disponible?: number;
  cantidad_transito?: number;
  costo_promedio?: number;
  valor_total?: number;
  moneda?: string;
  stock_minimo?: number;
  stock_maximo?: number;
  punto_reorden?: number;
  ubicacion_almacen?: string;
  fecha_ultimo_movimiento?: string;
  fecha_ultima_compra?: string;
  fecha_ultima_venta?: string;
  fecha_actualizacion?: string;
}
```

---

## ⚠️ Códigos de Error

| Código | Descripción |
|--------|-------------|
| `400` | Bad Request - Datos inválidos |
| `401` | Unauthorized - Token inválido o expirado |
| `403` | Forbidden - Sin permisos |
| `404` | Not Found - Recurso no encontrado |
| `422` | Unprocessable Entity - Error de validación |
| `500` | Internal Server Error - Error del servidor |

**Ejemplo de Error:**
```json
{
  "detail": "Producto no encontrado"
}
```

---

## 🗺️ Rutas SPA Recomendadas

```
/inventarios
├── /categorias
│   ├── /listar
│   ├── /crear
│   └── /editar/:id
├── /unidades-medida
│   ├── /listar
│   ├── /crear
│   └── /editar/:id
├── /productos
│   ├── /listar
│   ├── /crear
│   ├── /editar/:id
│   └── /detalle/:id
├── /almacenes
│   ├── /listar
│   ├── /crear
│   └── /editar/:id
├── /stock
│   ├── /consulta
│   └── /producto/:productoId/almacen/:almacenId
├── /tipos-movimiento
│   ├── /listar
│   ├── /crear
│   └── /editar/:id
├── /movimientos
│   ├── /listar
│   ├── /crear
│   └── /detalle/:id
└── /inventario-fisico
    ├── /listar
    ├── /crear
    └── /detalle/:id
```

---

## 🚀 Flujo de Implementación Recomendado

### Fase 1: Configuración Base
1. **Unidades de Medida** - Crear unidades básicas (UN, KG, MT, LT)
2. **Categorías** - Crear estructura de categorías
3. **Almacenes** - Configurar almacenes principales

### Fase 2: Catálogo de Productos
1. **Productos** - Crear catálogo completo
   - Formulario completo con todos los campos esenciales
   - Búsqueda por nombre, SKU o código de barras
   - Vista de detalle completa

### Fase 3: Gestión de Stock
1. **Stock** - Consulta y gestión
   - Vista de stock por almacén
   - Alertas de stock mínimo
   - Consulta rápida por producto/almacén

### Fase 4: Movimientos
1. **Tipos de Movimiento** - Configurar tipos básicos
2. **Movimientos** - Registrar movimientos de inventario
   - Entradas (compras)
   - Salidas (ventas)
   - Transferencias
   - Ajustes

### Fase 5: Inventario Físico
1. **Inventario Físico** - Toma de inventario
   - Crear inventario físico
   - Registrar conteos
   - Generar ajustes

---

## 📝 Notas Importantes

1. **Multi-tenancy:** Todos los endpoints filtran automáticamente por `cliente_id` del token. No enviar `cliente_id` en el body.

2. **Dependencias:** El módulo INV requiere:
   - Empresas configuradas (módulo ORG)
   - Sucursales (opcional, para almacenes)
   - Centros de costo (opcional, para almacenes)

3. **Campos Calculados:** 
   - `cantidad_disponible` en Stock se calcula automáticamente (actual - reservada)
   - `valor_total` en Stock se calcula automáticamente (cantidad_actual × costo_promedio)

4. **Búsqueda de Productos:** El parámetro `buscar` busca en nombre, SKU y código de barras simultáneamente.

5. **Estados de Movimiento:** 
   - `borrador` - En edición
   - `autorizado` - Autorizado pero no procesado
   - `procesado` - Procesado y afecta stock
   - `anulado` - Anulado

6. **Tipos de Inventario Físico:**
   - `total` - Todo el almacén
   - `ciclico` - Por rotación
   - `selectivo` - Por categoría/ubicación

---

## 🔗 Referencias

- **Módulo ORG:** Ver `DOC_FRONTEND_MODULO_ORG.md` para empresas, sucursales, etc.
- **API Base:** `/api/v1/`
- **Documentación Swagger:** `/docs` (cuando el servidor esté corriendo)

---

**Última actualización:** 2026-02-18
