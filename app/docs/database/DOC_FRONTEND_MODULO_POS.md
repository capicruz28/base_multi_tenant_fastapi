# Documentación Frontend — Módulo POS (Punto de Venta)

**Versión:** 1.0  
**Fecha:** 2026-02-18  
**Módulo:** POS - Punto de Venta ERP

---

## 📋 Índice

1. [Información General](#información-general)
2. [Autenticación](#autenticación)
3. [Endpoints](#endpoints)
4. [Schemas](#schemas)
5. [Códigos de Error](#códigos-de-error)
6. [Rutas SPA Recomendadas](#rutas-spa-recomendadas)
7. [Flujo de Implementación Recomendado](#flujo-de-implementación-recomendado)

---

## 🔑 Información General

### Base URL
```
/api/v1/pos
```

### Dependencias
- **Módulo ORG:** Empresas y sucursales (puntos de venta se ubican en sucursales).
- **Módulo INV:** Almacenes, productos, unidades de medida (ventas y stock).
- **Módulo SLS:** Clientes (venta con documento opcional).
- **Módulo PRC:** Listas de precios y promociones.
- **Módulo INV_BILL:** Series y comprobantes (factura, boleta, nota de crédito).
- **Orden recomendado:** Configurar ORG → INV → SLS → PRC → INV_BILL, luego POS.

---

## 🔐 Autenticación

Todos los endpoints requieren autenticación mediante JWT token en el header:

```http
Authorization: Bearer <token>
```

El `cliente_id` se obtiene automáticamente del token, **nunca debe enviarse en el body**.

---

## 📡 Endpoints

### 1. Puntos de Venta

#### Listar Puntos de Venta
```http
GET /api/v1/pos/puntos-venta
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `sucursal_id` (UUID, opcional): Filtrar por sucursal
- `estado` (string, opcional): 'abierto', 'cerrado', 'bloqueado'
- `es_activo` (boolean, opcional): true/false
- `buscar` (string, opcional): Búsqueda por nombre o código

**Response:** `200 OK`
```json
[
  {
    "punto_venta_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "codigo_punto_venta": "PV01",
    "nombre": "Caja 1 - Principal",
    "sucursal_id": "uuid",
    "ubicacion_fisica": "Caja 1",
    "tipo_punto_venta": "caja",
    "almacen_id": "uuid",
    "lista_precio_id": "uuid",
    "acepta_efectivo": true,
    "acepta_tarjeta": true,
    "acepta_transferencia": true,
    "acepta_yape_plin": false,
    "estado": "cerrado",
    "es_activo": true,
    "fecha_creacion": "2026-02-18T10:00:00",
    "usuario_creacion_id": "uuid"
  }
]
```

#### Obtener Punto de Venta por ID
```http
GET /api/v1/pos/puntos-venta/{punto_venta_id}
```

#### Crear Punto de Venta
```http
POST /api/v1/pos/puntos-venta
```

**Request Body:**
```json
{
  "empresa_id": "uuid",
  "codigo_punto_venta": "PV01",
  "nombre": "Caja 1 - Principal",
  "sucursal_id": "uuid",
  "ubicacion_fisica": "Caja 1",
  "tipo_punto_venta": "caja",
  "almacen_id": "uuid",
  "lista_precio_id": "uuid",
  "acepta_efectivo": true,
  "acepta_tarjeta": true,
  "acepta_transferencia": true,
  "acepta_yape_plin": false,
  "estado": "cerrado",
  "es_activo": true
}
```

#### Actualizar Punto de Venta
```http
PUT /api/v1/pos/puntos-venta/{punto_venta_id}
```

---

### 2. Turnos de Caja

#### Listar Turnos de Caja
```http
GET /api/v1/pos/turnos-caja
```

**Query Parameters:**
- `punto_venta_id` (UUID, opcional): Filtrar por punto de venta
- `estado` (string, opcional): 'abierto', 'cerrado'
- `cajero_usuario_id` (UUID, opcional): Filtrar por cajero
- `fecha_desde` (datetime, opcional): Desde fecha de apertura
- `fecha_hasta` (datetime, opcional): Hasta fecha de apertura

**Response:** `200 OK`
```json
[
  {
    "turno_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "punto_venta_id": "uuid",
    "numero_turno": "T-20260218-001",
    "cajero_usuario_id": "uuid",
    "cajero_nombre": "María López",
    "fecha_apertura": "2026-02-18T08:00:00",
    "monto_apertura": 200.00,
    "fecha_cierre": null,
    "monto_cierre_esperado": null,
    "monto_cierre_real": null,
    "total_ventas": 0,
    "total_ventas_efectivo": 0,
    "total_ventas_tarjeta": 0,
    "total_ventas_transferencia": 0,
    "total_ventas_otros": 0,
    "total_egresos": 0,
    "total_facturas": 0,
    "total_boletas": 0,
    "total_notas_credito": 0,
    "estado": "abierto",
    "observaciones_apertura": null,
    "observaciones_cierre": null,
    "fecha_creacion": "2026-02-18T08:00:00",
    "cerrado_por_usuario_id": null
  }
]
```

#### Abrir Turno (Crear)
```http
POST /api/v1/pos/turnos-caja
```

**Request Body:**
```json
{
  "empresa_id": "uuid",
  "punto_venta_id": "uuid",
  "numero_turno": "T-20260218-001",
  "cajero_usuario_id": "uuid",
  "cajero_nombre": "María López",
  "monto_apertura": 200.00,
  "observaciones_apertura": "Fondo inicial",
  "estado": "abierto"
}
```

#### Cerrar Turno (Actualizar)
```http
PUT /api/v1/pos/turnos-caja/{turno_id}
```

**Request Body:**
```json
{
  "fecha_cierre": "2026-02-18T18:00:00",
  "monto_cierre_esperado": 5250.50,
  "monto_cierre_real": 5250.50,
  "total_ventas": 45,
  "total_ventas_efectivo": 3200.00,
  "total_ventas_tarjeta": 2050.50,
  "total_ventas_transferencia": 0,
  "total_ventas_otros": 0,
  "total_egresos": 50.00,
  "total_facturas": 10,
  "total_boletas": 35,
  "total_notas_credito": 0,
  "estado": "cerrado",
  "observaciones_cierre": "Cierre normal",
  "cerrado_por_usuario_id": "uuid"
}
```

---

### 3. Ventas POS

#### Listar Ventas
```http
GET /api/v1/pos/ventas
```

**Query Parameters:**
- `punto_venta_id` (UUID, opcional): Filtrar por punto de venta
- `turno_caja_id` (UUID, opcional): Filtrar por turno
- `estado` (string, opcional): 'borrador', 'completada', 'anulada'
- `fecha_desde` (datetime, opcional): Desde fecha de venta
- `fecha_hasta` (datetime, opcional): Hasta fecha de venta

**Response:** `200 OK`
```json
[
  {
    "venta_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "numero_venta": "V-001",
    "fecha_venta": "2026-02-18T14:30:00",
    "punto_venta_id": "uuid",
    "turno_caja_id": "uuid",
    "vendedor_usuario_id": "uuid",
    "vendedor_nombre": "María López",
    "cliente_venta_id": null,
    "cliente_nombre": "Cliente genérico",
    "cliente_documento_tipo": "DNI",
    "cliente_documento_numero": "12345678",
    "moneda": "PEN",
    "subtotal": 84.75,
    "descuento_global": 0,
    "igv": 15.26,
    "total": 100.00,
    "redondeo": 0,
    "forma_pago": "efectivo",
    "monto_efectivo": 100.00,
    "monto_tarjeta": 0,
    "monto_transferencia": 0,
    "monto_otros": 0,
    "monto_recibido": 100.00,
    "comprobante_id": null,
    "tipo_comprobante": null,
    "numero_comprobante": null,
    "estado": "completada",
    "fecha_anulacion": null,
    "motivo_anulacion": null,
    "observaciones": null,
    "fecha_creacion": "2026-02-18T14:30:00",
    "usuario_creacion_id": "uuid"
  }
]
```

#### Crear Venta
```http
POST /api/v1/pos/ventas
```

**Request Body:**
```json
{
  "empresa_id": "uuid",
  "numero_venta": "V-001",
  "punto_venta_id": "uuid",
  "turno_caja_id": "uuid",
  "vendedor_usuario_id": "uuid",
  "vendedor_nombre": "María López",
  "cliente_venta_id": null,
  "cliente_nombre": "Cliente genérico",
  "cliente_documento_tipo": "DNI",
  "cliente_documento_numero": "12345678",
  "moneda": "PEN",
  "subtotal": 84.75,
  "descuento_global": 0,
  "igv": 15.26,
  "total": 100.00,
  "redondeo": 0,
  "forma_pago": "efectivo",
  "monto_efectivo": 100.00,
  "monto_tarjeta": 0,
  "monto_transferencia": 0,
  "monto_otros": 0,
  "monto_recibido": 100.00,
  "estado": "completada",
  "observaciones": null
}
```

#### Anular Venta
```http
PUT /api/v1/pos/ventas/{venta_id}
```

**Request Body:**
```json
{
  "estado": "anulada",
  "fecha_anulacion": "2026-02-18T15:00:00",
  "motivo_anulacion": "Error en items, cliente solicitó anulación"
}
```

---

### 4. Detalle de Ventas (Items)

#### Listar Detalles de Venta
```http
GET /api/v1/pos/ventas-detalle?venta_id={venta_id}
```

**Query Parameters:**
- `venta_id` (UUID, opcional): Filtrar por venta (si no se envía, lista todos los detalles del tenant)

**Response:** `200 OK`
```json
[
  {
    "venta_detalle_id": "uuid",
    "cliente_id": "uuid",
    "venta_id": "uuid",
    "item": 1,
    "producto_id": "uuid",
    "descripcion": "Producto A",
    "cantidad": 2,
    "unidad_medida_id": "uuid",
    "precio_unitario": 50.00,
    "descuento_porcentaje": 0,
    "promocion_id": null,
    "lote": null,
    "fecha_creacion": "2026-02-18T14:30:00"
  }
]
```

#### Crear Detalle (agregar línea a una venta)
```http
POST /api/v1/pos/ventas-detalle
```

**Request Body:**
```json
{
  "venta_id": "uuid",
  "item": 1,
  "producto_id": "uuid",
  "descripcion": "Producto A",
  "cantidad": 2,
  "unidad_medida_id": "uuid",
  "precio_unitario": 50.00,
  "descuento_porcentaje": 0,
  "promocion_id": null,
  "lote": null
}
```

#### Actualizar Detalle
```http
PUT /api/v1/pos/ventas-detalle/{venta_detalle_id}
```

---

## 📝 Schemas TypeScript

### PuntoVenta
```typescript
interface PuntoVentaCreate {
  empresa_id: string;
  codigo_punto_venta: string;
  nombre: string;
  sucursal_id: string;
  ubicacion_fisica?: string;
  tipo_punto_venta?: 'caja' | 'autoservicio' | 'movil';
  serie_factura_id?: string;
  serie_boleta_id?: string;
  serie_nota_credito_id?: string;
  almacen_id?: string;
  lista_precio_id?: string;
  acepta_efectivo?: boolean;
  acepta_tarjeta?: boolean;
  acepta_transferencia?: boolean;
  acepta_yape_plin?: boolean;
  codigo_terminal?: string;
  ip_terminal?: string;
  estado?: 'abierto' | 'cerrado' | 'bloqueado';
  es_activo?: boolean;
}

interface PuntoVentaRead {
  punto_venta_id: string;
  cliente_id: string;
  empresa_id: string;
  codigo_punto_venta: string;
  nombre: string;
  sucursal_id: string;
  ubicacion_fisica?: string;
  tipo_punto_venta?: string;
  serie_factura_id?: string;
  serie_boleta_id?: string;
  serie_nota_credito_id?: string;
  almacen_id?: string;
  lista_precio_id?: string;
  acepta_efectivo?: boolean;
  acepta_tarjeta?: boolean;
  acepta_transferencia?: boolean;
  acepta_yape_plin?: boolean;
  codigo_terminal?: string;
  ip_terminal?: string;
  estado?: string;
  es_activo?: boolean;
  fecha_creacion: string;
  usuario_creacion_id?: string;
}
```

### TurnoCaja
```typescript
interface TurnoCajaCreate {
  empresa_id: string;
  punto_venta_id: string;
  numero_turno: string;
  cajero_usuario_id: string;
  cajero_nombre?: string;
  monto_apertura: number;
  observaciones_apertura?: string;
  estado?: 'abierto' | 'cerrado';
}

interface TurnoCajaRead {
  turno_id: string;
  cliente_id: string;
  empresa_id: string;
  punto_venta_id: string;
  numero_turno: string;
  cajero_usuario_id: string;
  cajero_nombre?: string;
  fecha_apertura: string;
  monto_apertura: number;
  fecha_cierre?: string;
  monto_cierre_esperado?: number;
  monto_cierre_real?: number;
  total_ventas?: number;
  total_ventas_efectivo?: number;
  total_ventas_tarjeta?: number;
  total_ventas_transferencia?: number;
  total_ventas_otros?: number;
  total_egresos?: number;
  total_facturas?: number;
  total_boletas?: number;
  total_notas_credito?: number;
  estado?: string;
  observaciones_apertura?: string;
  observaciones_cierre?: string;
  fecha_creacion: string;
  cerrado_por_usuario_id?: string;
}
```

### Venta
```typescript
interface VentaCreate {
  empresa_id: string;
  numero_venta: string;
  punto_venta_id: string;
  turno_caja_id: string;
  vendedor_usuario_id: string;
  vendedor_nombre?: string;
  cliente_venta_id?: string;
  cliente_nombre?: string;
  cliente_documento_tipo?: string;
  cliente_documento_numero?: string;
  moneda?: string;
  subtotal: number;
  descuento_global?: number;
  igv: number;
  total: number;
  redondeo?: number;
  forma_pago: 'efectivo' | 'tarjeta' | 'transferencia' | 'mixto';
  monto_efectivo?: number;
  monto_tarjeta?: number;
  monto_transferencia?: number;
  monto_otros?: number;
  monto_recibido?: number;
  estado?: 'borrador' | 'completada' | 'anulada';
  observaciones?: string;
}

interface VentaRead {
  venta_id: string;
  cliente_id: string;
  empresa_id: string;
  numero_venta: string;
  fecha_venta: string;
  punto_venta_id: string;
  turno_caja_id: string;
  vendedor_usuario_id: string;
  vendedor_nombre?: string;
  cliente_venta_id?: string;
  cliente_nombre?: string;
  cliente_documento_tipo?: string;
  cliente_documento_numero?: string;
  moneda?: string;
  subtotal?: number;
  descuento_global?: number;
  igv?: number;
  total?: number;
  redondeo?: number;
  forma_pago: string;
  monto_efectivo?: number;
  monto_tarjeta?: number;
  monto_transferencia?: number;
  monto_otros?: number;
  monto_recibido?: number;
  comprobante_id?: string;
  tipo_comprobante?: string;
  numero_comprobante?: string;
  estado?: string;
  fecha_anulacion?: string;
  motivo_anulacion?: string;
  observaciones?: string;
  fecha_creacion: string;
  usuario_creacion_id?: string;
}
```

### VentaDetalle
```typescript
interface VentaDetalleCreate {
  venta_id: string;
  item: number;
  producto_id: string;
  descripcion?: string;
  cantidad: number;
  unidad_medida_id: string;
  precio_unitario: number;
  descuento_porcentaje?: number;
  promocion_id?: string;
  lote?: string;
}

interface VentaDetalleRead {
  venta_detalle_id: string;
  cliente_id: string;
  venta_id: string;
  item: number;
  producto_id: string;
  descripcion?: string;
  cantidad: number;
  unidad_medida_id: string;
  precio_unitario: number;
  descuento_porcentaje?: number;
  promocion_id?: string;
  lote?: string;
  fecha_creacion: string;
}
```

---

## ⚠️ Códigos de Error

| Código | Descripción |
|--------|-------------|
| `401` | No autenticado |
| `403` | Sin permisos |
| `404` | Recurso no encontrado (punto de venta, turno, venta o detalle) |
| `422` | Error de validación |
| `500` | Error interno del servidor |

**Ejemplo de error:**
```json
{
  "detail": "Punto de venta {uuid} no encontrado"
}
```

---

## 🗺️ Rutas SPA Recomendadas

```
/pos
  /puntos-venta
    /list                    # Lista de puntos de venta (cajas)
    /create                  # Crear punto de venta
    /:id/edit                # Editar punto de venta
  /turnos-caja
    /list                    # Lista de turnos (por PV, cajero, fechas)
    /abrir                   # Abrir turno (apertura con fondo)
    /:id/cerrar               # Cerrar turno (arqueo)
    /:id/detalle             # Detalle de turno con ventas
  /ventas
    /list                    # Lista de ventas (por PV, turno, fechas)
    /nueva                   # Nueva venta (interfaz POS)
    /:id/detalle             # Ver venta con items
    /:id/anular               # Anular venta
  /ventas-detalle
    (usado dentro de /ventas/nueva y /ventas/:id/detalle para líneas)
```

---

## 🔄 Flujo de Implementación Recomendado

### 1. Configuración de Puntos de Venta
1. Crear sucursales (ORG) y almacenes (INV) si no existen.
2. Crear listas de precios (PRC) y series de comprobantes (INV_BILL).
3. Crear puntos de venta (POS) por sucursal: código, nombre, ubicación, almacén, lista de precios, medios de pago aceptados.

### 2. Flujo Diario por Caja
1. **Apertura:** El cajero abre turno (POST turnos-caja) con número de turno y monto de apertura (fondo inicial).
2. **Ventas:** Por cada venta:
   - Crear cabecera de venta (POST ventas) con punto_venta_id, turno_caja_id, vendedor, totales, forma de pago.
   - Crear líneas (POST ventas-detalle) por cada item: producto, cantidad, precio, descuento.
   - Opcional: vincular comprobante (INV_BILL) y actualizar estado de venta.
3. **Cierre:** Al cerrar turno, actualizar turno (PUT turnos-caja/{id}) con fecha_cierre, monto_cierre_real, totales por forma de pago, estado "cerrado".

### 3. Ventas Rápidas (UI POS)
1. Seleccionar punto de venta y turno abierto.
2. Búsqueda de productos (INV) con precios desde lista (PRC).
3. Agregar items al carrito (crear venta en borrador o completada según flujo).
4. Aplicar descuentos por línea o global.
5. Seleccionar forma de pago (efectivo/tarjeta/mixto) y monto recibido si es efectivo (calcular cambio en frontend).
6. Completar venta; opcionalmente emitir comprobante (INV_BILL) y asociar comprobante_id a la venta.

### 4. Anulaciones y Reportes
1. Anular venta: PUT ventas/{id} con estado "anulada", fecha_anulacion y motivo_anulacion.
2. Reportes por turno: listar ventas por turno_caja_id; totales ya vienen en el turno (total_ventas_efectivo, total_ventas_tarjeta, etc.).
3. Reportes por punto de venta y rango de fechas: listar ventas con filtros fecha_desde/fecha_hasta y punto_venta_id.

---

## 📌 Notas Importantes

1. **Multi-tenancy:** Todos los datos están filtrados por `cliente_id` del token. No enviar `cliente_id` en el body.

2. **Dependencias:** POS requiere ORG (empresa, sucursal), INV (almacén, producto, unidad de medida), SLS (cliente opcional), PRC (lista de precios, promociones), INV_BILL (series y comprobantes).

3. **Turno abierto:** Solo debe haber un turno abierto por punto de venta a la vez. La lógica de “hay turno abierto” puede hacerse en frontend listando turnos con estado=abierto y punto_venta_id, o con un endpoint auxiliar si se implementa.

4. **Número de venta:** Debe ser único por punto de venta (y tenant). El backend valida con UQ_posvta_numero (cliente_id, empresa_id, punto_venta_id, numero_venta). El frontend puede generar secuencial (V-001, V-002, …) por punto de venta.

5. **Totales y redondeo:** subtotal, igv, total pueden calcularse en frontend (subtotal = suma de líneas, igv = 18%, total = subtotal + igv). Redondeo es opcional (común en efectivo). total_cobrar en BD es total + redondeo (columna calculada en BD; si no se devuelve, calcular en frontend).

6. **Forma de pago:** Valores típicos: 'efectivo', 'tarjeta', 'transferencia', 'mixto'. En mixto, usar monto_efectivo, monto_tarjeta, monto_transferencia, monto_otros para desglose.

7. **Comprobante:** Tras emitir factura/boleta por INV_BILL, actualizar la venta con comprobante_id, tipo_comprobante y numero_comprobante (PUT ventas/{id}).

8. **Estados:** Punto de venta: 'abierto', 'cerrado', 'bloqueado'. Turno: 'abierto', 'cerrado'. Venta: 'borrador', 'completada', 'anulada'.

---

**Fin de la documentación del módulo POS**
