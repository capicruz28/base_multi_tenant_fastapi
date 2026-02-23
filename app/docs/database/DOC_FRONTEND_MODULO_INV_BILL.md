# Documentación Frontend — Módulo INV_BILL (Facturación Electrónica)

**Versión:** 1.0  
**Fecha:** 2026-02-18  
**Módulo:** INV_BILL - Facturación Electrónica ERP

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
9. [Notas Importantes sobre Integración SUNAT](#notas-importantes-sobre-integración-sunat)

---

## 🔑 Información General

### Base URL
```
/api/v1/inv-bill
```

### Dependencias
- **Módulo ORG:** Requiere tener empresas y sucursales configuradas.
- **Módulo SLS:** Requiere tener clientes y pedidos configurados.
- **Módulo INV:** Requiere tener productos y unidades de medida configurados.
- **Orden recomendado:** Configurar primero ORG, INV y SLS, luego INV_BILL.

---

## 🔐 Autenticación

Todos los endpoints requieren autenticación mediante JWT token en el header:

```http
Authorization: Bearer <token>
```

El `cliente_id` se obtiene automáticamente del token, **nunca debe enviarse en el body**.

---

## 📡 Endpoints

### 1. Series de Comprobantes

#### Listar Series
```http
GET /api/v1/inv-bill/series
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `tipo_comprobante` (string, opcional): Filtrar por tipo ('01'=Factura, '03'=Boleta, '07'=NC, '08'=ND)
- `solo_activos` (boolean, default: true): Solo series activas

**Response:** `200 OK`
```json
[
  {
    "serie_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "tipo_comprobante": "01",
    "serie": "F001",
    "numero_actual": 1250,
    "numero_inicial": 1,
    "numero_final": null,
    "sucursal_id": "uuid",
    "punto_venta_id": null,
    "es_electronica": true,
    "requiere_autorizacion_sunat": true,
    "es_activo": true,
    "fecha_activacion": "2025-01-15",
    "fecha_baja": null,
    "motivo_baja": null,
    "fecha_creacion": "2025-01-15T10:30:00",
    "usuario_creacion_id": "uuid"
  }
]
```

#### Obtener Serie por ID
```http
GET /api/v1/inv-bill/series/{serie_id}
```

**Response:** `200 OK` (mismo schema que listar)

#### Crear Serie
```http
POST /api/v1/inv-bill/series
```

**Request Body:**
```json
{
  "empresa_id": "uuid",
  "tipo_comprobante": "01",
  "serie": "F001",
  "numero_actual": 0,
  "numero_inicial": 1,
  "numero_final": null,
  "sucursal_id": "uuid",
  "punto_venta_id": null,
  "es_electronica": true,
  "requiere_autorizacion_sunat": true,
  "es_activo": true,
  "fecha_activacion": "2025-01-15"
}
```

**Response:** `201 Created` (mismo schema que listar)

#### Actualizar Serie
```http
PUT /api/v1/inv-bill/series/{serie_id}
```

**Request Body:** (todos los campos opcionales)
```json
{
  "numero_actual": 1251,
  "es_activo": true
}
```

**Response:** `200 OK` (mismo schema que listar)

---

### 2. Comprobantes

#### Listar Comprobantes
```http
GET /api/v1/inv-bill/comprobantes
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `tipo_comprobante` (string, opcional): Filtrar por tipo ('01', '03', '07', '08')
- `cliente_venta_id` (UUID, opcional): Filtrar por cliente
- `pedido_id` (UUID, opcional): Filtrar por pedido
- `estado` (string, opcional): Filtrar por estado ('borrador', 'emitido', 'anulado', 'dado_baja')
- `estado_sunat` (string, opcional): Filtrar por estado SUNAT ('pendiente', 'aceptado', 'rechazado', 'baja')
- `fecha_desde` (date, opcional): Filtrar desde fecha
- `fecha_hasta` (date, opcional): Filtrar hasta fecha

**Response:** `200 OK`
```json
[
  {
    "comprobante_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "tipo_comprobante": "01",
    "serie": "F001",
    "numero": "00001250",
    "fecha_emision": "2025-02-18",
    "fecha_vencimiento": "2025-03-20",
    "hora_emision": "10:30:00",
    "cliente_venta_id": "uuid",
    "cliente_tipo_documento": "6",
    "cliente_numero_documento": "20123456789",
    "cliente_razon_social": "Cliente ABC S.A.C.",
    "cliente_direccion": "Av. Principal 123, San Isidro",
    "pedido_id": "uuid",
    "venta_id": null,
    "guia_remision_id": null,
    "comprobante_referencia_id": null,
    "tipo_nota": null,
    "motivo_nota": null,
    "moneda": "PEN",
    "tipo_cambio": 1.0000,
    "subtotal_gravado": 10000.00,
    "subtotal_exonerado": 0.00,
    "subtotal_inafecto": 0.00,
    "subtotal_gratuito": 0.00,
    "descuento_global": 500.00,
    "igv": 1710.00,
    "total": 11210.00,
    "aplica_detraccion": false,
    "porcentaje_detraccion": null,
    "monto_detraccion": null,
    "aplica_retencion": false,
    "monto_retencion": null,
    "aplica_percepcion": false,
    "monto_percepcion": null,
    "condicion_pago": "30_dias",
    "forma_pago": "credito",
    "codigo_hash": null,
    "firma_digital": null,
    "codigo_qr": null,
    "estado_sunat": "pendiente",
    "codigo_respuesta_sunat": null,
    "mensaje_respuesta_sunat": null,
    "fecha_envio_sunat": null,
    "fecha_respuesta_sunat": null,
    "cdr_xml": null,
    "cdr_fecha": null,
    "xml_comprobante": null,
    "pdf_url": null,
    "estado": "emitido",
    "fecha_anulacion": null,
    "motivo_anulacion": null,
    "observaciones": "Factura generada desde pedido PED-2025-001",
    "vendedor_usuario_id": "uuid",
    "vendedor_nombre": "María González",
    "fecha_creacion": "2025-02-18T10:30:00",
    "usuario_creacion_id": "uuid"
  }
]
```

#### Obtener Comprobante por ID
```http
GET /api/v1/inv-bill/comprobantes/{comprobante_id}
```

**Response:** `200 OK` (mismo schema que listar)

#### Crear Comprobante
```http
POST /api/v1/inv-bill/comprobantes
```

**Request Body:**
```json
{
  "empresa_id": "uuid",
  "tipo_comprobante": "01",
  "serie": "F001",
  "numero": "00001250",
  "fecha_emision": "2025-02-18",
  "fecha_vencimiento": "2025-03-20",
  "hora_emision": "10:30:00",
  "cliente_venta_id": "uuid",
  "cliente_tipo_documento": "6",
  "cliente_numero_documento": "20123456789",
  "cliente_razon_social": "Cliente ABC S.A.C.",
  "cliente_direccion": "Av. Principal 123, San Isidro",
  "pedido_id": "uuid",
  "moneda": "PEN",
  "tipo_cambio": 1.0000,
  "subtotal_gravado": 10000.00,
  "subtotal_exonerado": 0.00,
  "subtotal_inafecto": 0.00,
  "subtotal_gratuito": 0.00,
  "descuento_global": 500.00,
  "igv": 1710.00,
  "total": 11210.00,
  "condicion_pago": "30_dias",
  "forma_pago": "credito",
  "estado": "borrador",
  "observaciones": "Factura generada desde pedido",
  "vendedor_usuario_id": "uuid",
  "vendedor_nombre": "María González"
}
```

**Response:** `201 Created` (mismo schema que listar)

#### Actualizar Comprobante
```http
PUT /api/v1/inv-bill/comprobantes/{comprobante_id}
```

**Request Body:** (todos los campos opcionales)
```json
{
  "estado": "emitido",
  "estado_sunat": "pendiente",
  "codigo_hash": "abc123...",
  "xml_comprobante": "<?xml version=\"1.0\"?>..."
}
```

**Response:** `200 OK` (mismo schema que listar)

---

### 3. Detalles de Comprobantes

#### Listar Detalles
```http
GET /api/v1/inv-bill/comprobantes-detalles
```

**Query Parameters:**
- `comprobante_id` (UUID, opcional): Filtrar por comprobante

**Response:** `200 OK`
```json
[
  {
    "comprobante_detalle_id": "uuid",
    "cliente_id": "uuid",
    "comprobante_id": "uuid",
    "item": 1,
    "producto_id": "uuid",
    "codigo_producto": "PROD001",
    "descripcion": "Producto ABC - Descripción completa",
    "cantidad": 10.00,
    "unidad_medida_codigo": "NIU",
    "unidad_medida_id": "uuid",
    "precio_unitario": 1000.00,
    "descuento_unitario": 50.00,
    "tipo_afectacion_igv": "10",
    "porcentaje_igv": 18.00,
    "codigo_producto_sunat": "10000000",
    "lote": null,
    "fecha_creacion": "2025-02-18T10:30:00"
  }
]
```

#### Crear Detalle
```http
POST /api/v1/inv-bill/comprobantes-detalles
```

**Request Body:**
```json
{
  "comprobante_id": "uuid",
  "item": 1,
  "producto_id": "uuid",
  "codigo_producto": "PROD001",
  "descripcion": "Producto ABC - Descripción completa",
  "cantidad": 10.00,
  "unidad_medida_codigo": "NIU",
  "unidad_medida_id": "uuid",
  "precio_unitario": 1000.00,
  "descuento_unitario": 50.00,
  "tipo_afectacion_igv": "10",
  "porcentaje_igv": 18.00,
  "codigo_producto_sunat": "10000000",
  "lote": null
}
```

**Response:** `201 Created` (mismo schema que listar)

#### Actualizar Detalle
```http
PUT /api/v1/inv-bill/comprobantes-detalles/{comprobante_detalle_id}
```

**Request Body:** (todos los campos opcionales)
```json
{
  "cantidad": 12.00,
  "precio_unitario": 1050.00
}
```

**Response:** `200 OK` (mismo schema que listar)

---

## 📝 Schemas TypeScript

### SerieComprobante
```typescript
interface SerieComprobante {
  serie_id: string;
  cliente_id: string;
  empresa_id: string;
  tipo_comprobante: '01' | '03' | '07' | '08'; // '01'=Factura, '03'=Boleta, '07'=NC, '08'=ND
  serie: string; // 'F001', 'B001', etc
  numero_actual: number;
  numero_inicial: number;
  numero_final?: number;
  sucursal_id?: string;
  punto_venta_id?: string;
  es_electronica: boolean;
  requiere_autorizacion_sunat: boolean;
  es_activo: boolean;
  fecha_activacion?: string;
  fecha_baja?: string;
  motivo_baja?: string;
  fecha_creacion: string;
  usuario_creacion_id?: string;
}
```

### Comprobante
```typescript
interface Comprobante {
  comprobante_id: string;
  cliente_id: string;
  empresa_id: string;
  tipo_comprobante: '01' | '03' | '07' | '08';
  serie: string;
  numero: string;
  fecha_emision: string;
  fecha_vencimiento?: string;
  hora_emision?: string;
  cliente_venta_id?: string;
  cliente_tipo_documento: string; // '6'=RUC, '1'=DNI, etc
  cliente_numero_documento: string;
  cliente_razon_social: string;
  cliente_direccion?: string;
  pedido_id?: string;
  venta_id?: string;
  guia_remision_id?: string;
  comprobante_referencia_id?: string;
  tipo_nota?: string;
  motivo_nota?: string;
  moneda: string;
  tipo_cambio: number;
  subtotal_gravado: number;
  subtotal_exonerado: number;
  subtotal_inafecto: number;
  subtotal_gratuito: number;
  descuento_global: number;
  igv: number;
  total: number;
  aplica_detraccion: boolean;
  porcentaje_detraccion?: number;
  monto_detraccion?: number;
  aplica_retencion: boolean;
  monto_retencion?: number;
  aplica_percepcion: boolean;
  monto_percepcion?: number;
  condicion_pago?: string;
  forma_pago: 'contado' | 'credito';
  codigo_hash?: string;
  firma_digital?: string;
  codigo_qr?: string;
  estado_sunat: 'pendiente' | 'aceptado' | 'rechazado' | 'baja';
  codigo_respuesta_sunat?: string;
  mensaje_respuesta_sunat?: string;
  fecha_envio_sunat?: string;
  fecha_respuesta_sunat?: string;
  cdr_xml?: string;
  cdr_fecha?: string;
  xml_comprobante?: string;
  pdf_url?: string;
  estado: 'borrador' | 'emitido' | 'anulado' | 'dado_baja';
  fecha_anulacion?: string;
  motivo_anulacion?: string;
  observaciones?: string;
  vendedor_usuario_id?: string;
  vendedor_nombre?: string;
  fecha_creacion: string;
  usuario_creacion_id?: string;
}
```

### ComprobanteDetalle
```typescript
interface ComprobanteDetalle {
  comprobante_detalle_id: string;
  cliente_id: string;
  comprobante_id: string;
  item: number;
  producto_id?: string;
  codigo_producto?: string;
  descripcion: string;
  cantidad: number;
  unidad_medida_codigo: string; // Código SUNAT: 'NIU', 'ZZ', etc
  unidad_medida_id?: string;
  precio_unitario: number;
  descuento_unitario: number;
  tipo_afectacion_igv: string; // '10'=Gravado, '20'=Exonerado, etc
  porcentaje_igv: number;
  codigo_producto_sunat?: string;
  lote?: string;
  fecha_creacion: string;
}
```

---

## ⚠️ Códigos de Error

| Código | Descripción |
|--------|-------------|
| `400` | Bad Request - Datos inválidos en el request |
| `401` | Unauthorized - Token inválido o expirado |
| `404` | Not Found - Recurso no encontrado |
| `422` | Unprocessable Entity - Error de validación |
| `500` | Internal Server Error - Error del servidor |

---

## 🗺️ Rutas SPA Recomendadas

```
/inv-bill
  /series
    /listado          # Lista de series
    /nuevo            # Formulario crear serie
    /:id              # Detalle serie
    /:id/editar       # Formulario editar serie
  /comprobantes
    /listado          # Lista de comprobantes
    /nuevo            # Formulario crear comprobante
    /:id              # Detalle comprobante
    /:id/editar       # Formulario editar comprobante
    /:id/detalles     # Detalles del comprobante
```

---

## 🚀 Flujo de Implementación Recomendado

### Fase 1: Configuración
1. **Series de Comprobantes**
   - Crear series por tipo de comprobante (Factura, Boleta, NC, ND)
   - Configurar numeración inicial y límites
   - Asociar series a sucursales o puntos de venta

### Fase 2: Emisión de Comprobantes
1. **Crear Comprobante**
   - Seleccionar serie y tipo de comprobante
   - Obtener número siguiente de la serie
   - Seleccionar cliente (desde módulo SLS)
   - Opcionalmente vincular a pedido de venta
   - Agregar detalles (productos)
   - Calcular totales (subtotales, IGV, total)

2. **Gestión de Detalles**
   - Agregar items al comprobante
   - Seleccionar producto (desde módulo INV)
   - Configurar cantidad, precio, descuento
   - Seleccionar tipo de afectación IGV
   - Calcular totales por item

### Fase 3: Estados y Validaciones
1. **Estados del Comprobante**
   - `borrador`: En edición, aún no emitido
   - `emitido`: Comprobante finalizado, listo para enviar a SUNAT
   - `anulado`: Comprobante anulado (requiere motivo)
   - `dado_baja`: Comprobante dado de baja en SUNAT

2. **Estados SUNAT**
   - `pendiente`: Aún no enviado a SUNAT
   - `aceptado`: Aceptado por SUNAT (tiene CDR)
   - `rechazado`: Rechazado por SUNAT (tiene código y mensaje de error)
   - `baja`: Dado de baja en SUNAT

### Fase 4: Integración con Otros Módulos
1. **Con SLS:**
   - Crear comprobante desde pedido de venta
   - Copiar datos del cliente y items del pedido
   - Actualizar estado del pedido a "facturado"

2. **Con INV:**
   - Validar stock disponible antes de emitir
   - Generar salida de inventario al emitir comprobante

---

## 📌 Notas Importantes

1. **Multi-tenancy:** Todos los endpoints filtran automáticamente por `cliente_id` del token. No enviar `cliente_id` en el body.

2. **Dependencias:**
   - Requiere módulo ORG (empresas, sucursales)
   - Requiere módulo SLS (clientes, pedidos)
   - Requiere módulo INV (productos, unidades de medida)

3. **Tipos de Comprobante:**
   - `'01'`: Factura
   - `'03'`: Boleta de Venta
   - `'07'`: Nota de Crédito
   - `'08'`: Nota de Débito

4. **Tipos de Afectación IGV (en detalles):**
   - `'10'`: Gravado - Operación Onerosa
   - `'20'`: Exonerado - Operación Onerosa
   - `'30'`: Inafecto - Operación Onerosa
   - `'40'`: Por exportación
   - `'11'`: Gravado - Retiro por premio
   - `'12'`: Gravado - Retiro por donación
   - `'13'`: Gravado - Retiro
   - `'14'`: Gravado - Retiro por publicidad
   - `'15'`: Gravado - Bonificaciones
   - `'16'`: Gravado - Retiro por entrega a trabajadores
   - `'17'`: Gravado - IVAP

5. **Unidades de Medida SUNAT:**
   - `'NIU'`: Unidad
   - `'ZZ'`: Servicio
   - `'KG'`: Kilogramo
   - `'MTR'`: Metro
   - Ver catálogo completo en SUNAT

6. **Numeración de Comprobantes:**
   - El número debe ser secuencial según la serie
   - Al crear un comprobante, se debe incrementar `numero_actual` de la serie
   - Validar que el número no exceda `numero_final` (si está definido)

---

## 🔗 Notas Importantes sobre Integración SUNAT

### ⚠️ IMPORTANTE: Esta implementación NO incluye integración directa con SUNAT

El módulo INV_BILL proporciona la estructura de datos y endpoints para gestionar comprobantes, pero **NO incluye**:

- ❌ Generación de XML según formato SUNAT
- ❌ Firma digital del comprobante
- ❌ Envío a SUNAT
- ❌ Procesamiento de CDR (Constancia de Recepción)
- ❌ Generación de PDF

### Campos Preparados para Integración

Los siguientes campos están disponibles en el schema `Comprobante` para que un servicio externo o módulo futuro complete la integración:

#### Para Firma Digital:
- `codigo_hash`: Hash del comprobante para firma
- `firma_digital`: Firma digital del comprobante
- `codigo_qr`: Código QR del comprobante

#### Para Estado SUNAT:
- `estado_sunat`: Estado del comprobante en SUNAT ('pendiente', 'aceptado', 'rechazado', 'baja')
- `codigo_respuesta_sunat`: Código de respuesta de SUNAT
- `mensaje_respuesta_sunat`: Mensaje de respuesta de SUNAT
- `fecha_envio_sunat`: Fecha de envío a SUNAT
- `fecha_respuesta_sunat`: Fecha de respuesta de SUNAT

#### Para Archivos:
- `xml_comprobante`: XML del comprobante generado
- `cdr_xml`: XML del CDR recibido de SUNAT
- `cdr_fecha`: Fecha del CDR
- `pdf_url`: URL del PDF generado

### Flujo Recomendado para Integración

1. **Crear Comprobante en Borrador:**
   ```http
   POST /api/v1/inv-bill/comprobantes
   ```
   - Estado inicial: `"estado": "borrador"`

2. **Agregar Detalles:**
   ```http
   POST /api/v1/inv-bill/comprobantes-detalles
   ```
   - Agregar todos los items del comprobante

3. **Emitir Comprobante:**
   ```http
   PUT /api/v1/inv-bill/comprobantes/{id}
   ```
   - Cambiar estado a `"estado": "emitido"`
   - Incrementar `numero_actual` de la serie

4. **Integración Externa (Servicio/Módulo separado):**
   - Leer comprobante con `estado_sunat: "pendiente"`
   - Generar XML según formato SUNAT
   - Firmar XML con certificado digital
   - Enviar a SUNAT
   - Procesar respuesta (CDR)
   - Actualizar comprobante con:
     - `estado_sunat`: 'aceptado' o 'rechazado'
     - `codigo_respuesta_sunat`: Código de respuesta
     - `mensaje_respuesta_sunat`: Mensaje de respuesta
     - `cdr_xml`: XML del CDR recibido
     - `xml_comprobante`: XML del comprobante generado
     - `pdf_url`: URL del PDF generado

5. **Actualizar Comprobante con Resultado:**
   ```http
   PUT /api/v1/inv-bill/comprobantes/{id}
   ```
   - Actualizar campos de SUNAT con la respuesta

### Proveedores de Facturación Electrónica Recomendados

Para integrar con SUNAT, puedes usar servicios como:
- Nubefact
- Facturador Electrónico
- Ocelot
- Otros proveedores que ofrecen API REST

Estos servicios generalmente requieren:
- Certificado digital (.pfx)
- Usuario y contraseña SOL
- Configuración de empresa y series autorizadas

---

**Fin de la documentación**
