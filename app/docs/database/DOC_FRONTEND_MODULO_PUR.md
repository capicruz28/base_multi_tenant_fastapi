# Documentación Frontend — Módulo PUR (Compras)

**Versión:** 1.0  
**Fecha:** 2026-02-18  
**Módulo:** PUR - Compras ERP

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
/api/v1/pur
```

### Dependencias
- **Módulo ORG:** Requiere tener empresas, departamentos y centros de costo configurados.
- **Módulo INV:** Requiere tener productos, almacenes y unidades de medida configurados.
- **Orden recomendado:** Configurar primero ORG e INV, luego PUR.

---

## 🔐 Autenticación

Todos los endpoints requieren autenticación mediante JWT token en el header:

```http
Authorization: Bearer <token>
```

El `cliente_id` se obtiene automáticamente del token, **nunca debe enviarse en el body**.

---

## 📡 Endpoints

### 1. Proveedores

#### Listar Proveedores
```http
GET /api/v1/pur/proveedores
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `solo_activos` (boolean, default: true): Solo proveedores activos
- `buscar` (string, opcional): Búsqueda por razón social, RUC o código

**Response:** `200 OK`
```json
[
  {
    "proveedor_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "codigo_proveedor": "PROV001",
    "razon_social": "Proveedor ABC S.A.C.",
    "nombre_comercial": "ABC",
    "tipo_documento": "RUC",
    "numero_documento": "20123456789",
    "tipo_proveedor": "bienes",
    "categoria_proveedor": "materia_prima",
    "direccion": "Av. Principal 123",
    "pais": "Perú",
    "departamento": "Lima",
    "provincia": "Lima",
    "distrito": "San Isidro",
    "ubigeo": "150131",
    "contacto_nombre": "Juan Pérez",
    "contacto_cargo": "Gerente Comercial",
    "telefono_principal": "+51 1 2345678",
    "telefono_secundario": "+51 987654321",
    "email_principal": "contacto@proveedorabc.com",
    "email_cotizaciones": "cotizaciones@proveedorabc.com",
    "sitio_web": "https://www.proveedorabc.com",
    "condicion_pago_defecto": "30_dias",
    "dias_credito_defecto": 30,
    "moneda_preferida": "PEN",
    "banco": "Banco de Crédito",
    "numero_cuenta": "1234567890",
    "tipo_cuenta": "corriente",
    "cci": "00312300123456789012",
    "calificacion": 4.5,
    "nivel_confianza": "alto",
    "es_proveedor_homologado": true,
    "fecha_homologacion": "2025-01-15",
    "limite_credito": 100000.00,
    "saldo_pendiente": 25000.00,
    "estado": "activo",
    "motivo_bloqueo": null,
    "es_activo": true,
    "observaciones": null,
    "fecha_creacion": "2026-02-18T10:00:00Z",
    "fecha_actualizacion": null,
    "usuario_creacion_id": null,
    "usuario_actualizacion_id": null
  }
]
```

#### Detalle de Proveedor
```http
GET /api/v1/pur/proveedores/{proveedor_id}
```

#### Crear Proveedor
```http
POST /api/v1/pur/proveedores
```

**Body:**
```json
{
  "empresa_id": "uuid",
  "codigo_proveedor": "PROV001",
  "razon_social": "Proveedor ABC S.A.C.",
  "nombre_comercial": "ABC",
  "tipo_documento": "RUC",
  "numero_documento": "20123456789",
  "tipo_proveedor": "bienes",
  "categoria_proveedor": "materia_prima",
  "direccion": "Av. Principal 123",
  "pais": "Perú",
  "departamento": "Lima",
  "provincia": "Lima",
  "distrito": "San Isidro",
  "ubigeo": "150131",
  "contacto_nombre": "Juan Pérez",
  "contacto_cargo": "Gerente Comercial",
  "telefono_principal": "+51 1 2345678",
  "telefono_secundario": "+51 987654321",
  "email_principal": "contacto@proveedorabc.com",
  "email_cotizaciones": "cotizaciones@proveedorabc.com",
  "sitio_web": "https://www.proveedorabc.com",
  "condicion_pago_defecto": "30_dias",
  "dias_credito_defecto": 30,
  "moneda_preferida": "PEN",
  "banco": "Banco de Crédito",
  "numero_cuenta": "1234567890",
  "tipo_cuenta": "corriente",
  "cci": "00312300123456789012",
  "calificacion": 4.5,
  "nivel_confianza": "alto",
  "es_proveedor_homologado": true,
  "fecha_homologacion": "2025-01-15",
  "limite_credito": 100000.00,
  "saldo_pendiente": 0.00,
  "estado": "activo",
  "es_activo": true,
  "observaciones": null
}
```

#### Actualizar Proveedor
```http
PUT /api/v1/pur/proveedores/{proveedor_id}
```

---

### 2. Contactos de Proveedor

#### Listar Contactos
```http
GET /api/v1/pur/contactos
```

**Query Parameters:**
- `proveedor_id` (UUID, opcional): Filtrar por proveedor
- `solo_activos` (boolean, default: true): Solo contactos activos

**Response:** `200 OK`
```json
[
  {
    "contacto_id": "uuid",
    "cliente_id": "uuid",
    "proveedor_id": "uuid",
    "nombre_completo": "Juan Pérez",
    "cargo": "Gerente Comercial",
    "area": "Ventas",
    "telefono": "+51 1 2345678",
    "telefono_movil": "+51 987654321",
    "email": "jperez@proveedorabc.com",
    "es_contacto_principal": true,
    "es_contacto_cotizaciones": true,
    "es_contacto_cobranzas": false,
    "es_activo": true,
    "fecha_creacion": "2026-02-18T10:00:00Z"
  }
]
```

#### Detalle de Contacto
```http
GET /api/v1/pur/contactos/{contacto_id}
```

#### Crear Contacto
```http
POST /api/v1/pur/contactos
```

**Body:**
```json
{
  "proveedor_id": "uuid",
  "nombre_completo": "Juan Pérez",
  "cargo": "Gerente Comercial",
  "area": "Ventas",
  "telefono": "+51 1 2345678",
  "telefono_movil": "+51 987654321",
  "email": "jperez@proveedorabc.com",
  "es_contacto_principal": true,
  "es_contacto_cotizaciones": true,
  "es_contacto_cobranzas": false,
  "es_activo": true
}
```

#### Actualizar Contacto
```http
PUT /api/v1/pur/contactos/{contacto_id}
```

---

### 3. Productos por Proveedor

#### Listar Productos por Proveedor
```http
GET /api/v1/pur/productos-proveedor
```

**Query Parameters:**
- `proveedor_id` (UUID, opcional): Filtrar por proveedor
- `producto_id` (UUID, opcional): Filtrar por producto
- `solo_activos` (boolean, default: true): Solo productos activos

**Response:** `200 OK`
```json
[
  {
    "producto_proveedor_id": "uuid",
    "cliente_id": "uuid",
    "proveedor_id": "uuid",
    "producto_id": "uuid",
    "codigo_proveedor": "ABC-PROD001",
    "descripcion_proveedor": "Producto según catálogo del proveedor",
    "precio_unitario": 1500.00,
    "moneda": "PEN",
    "unidad_medida_id": "uuid",
    "cantidad_minima": 10.0,
    "multiplo_compra": 5.0,
    "tiempo_entrega_dias": 7,
    "fecha_vigencia_desde": "2026-01-01",
    "fecha_vigencia_hasta": "2026-12-31",
    "es_proveedor_preferido": true,
    "prioridad": 1,
    "es_activo": true,
    "fecha_creacion": "2026-02-18T10:00:00Z",
    "fecha_actualizacion": null
  }
]
```

#### Detalle de Producto por Proveedor
```http
GET /api/v1/pur/productos-proveedor/{producto_proveedor_id}
```

#### Crear Producto por Proveedor
```http
POST /api/v1/pur/productos-proveedor
```

**Body:**
```json
{
  "proveedor_id": "uuid",
  "producto_id": "uuid",
  "codigo_proveedor": "ABC-PROD001",
  "descripcion_proveedor": "Producto según catálogo del proveedor",
  "precio_unitario": 1500.00,
  "moneda": "PEN",
  "unidad_medida_id": "uuid",
  "cantidad_minima": 10.0,
  "multiplo_compra": 5.0,
  "tiempo_entrega_dias": 7,
  "fecha_vigencia_desde": "2026-01-01",
  "fecha_vigencia_hasta": "2026-12-31",
  "es_proveedor_preferido": true,
  "prioridad": 1,
  "es_activo": true
}
```

#### Actualizar Producto por Proveedor
```http
PUT /api/v1/pur/productos-proveedor/{producto_proveedor_id}
```

---

### 4. Solicitudes de Compra

#### Listar Solicitudes
```http
GET /api/v1/pur/solicitudes
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `estado` (string, opcional): Filtrar por estado ('borrador', 'pendiente_aprobacion', 'aprobada', 'rechazada', 'procesada', 'anulada')
- `fecha_desde` (date, opcional): Fecha desde (formato: YYYY-MM-DD)
- `fecha_hasta` (date, opcional): Fecha hasta (formato: YYYY-MM-DD)

**Response:** `200 OK`
```json
[
  {
    "solicitud_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "numero_solicitud": "SOL-001",
    "fecha_solicitud": "2026-02-18",
    "fecha_requerida": "2026-02-25",
    "departamento_solicitante_id": "uuid",
    "usuario_solicitante_id": "uuid",
    "solicitante_nombre": "Juan Pérez",
    "almacen_destino_id": "uuid",
    "centro_costo_id": "uuid",
    "tipo_solicitud": "normal",
    "motivo_solicitud": "reposicion",
    "total_items": 5,
    "total_estimado": 15000.00,
    "moneda": "PEN",
    "estado": "pendiente_aprobacion",
    "requiere_aprobacion": true,
    "aprobado_por_usuario_id": null,
    "fecha_aprobacion": null,
    "orden_compra_generada": false,
    "observaciones": "Solicitud de reposición de stock",
    "motivo_rechazo": null,
    "fecha_creacion": "2026-02-18T10:00:00Z",
    "fecha_actualizacion": null,
    "usuario_creacion_id": "uuid"
  }
]
```

#### Detalle de Solicitud
```http
GET /api/v1/pur/solicitudes/{solicitud_id}
```

#### Crear Solicitud
```http
POST /api/v1/pur/solicitudes
```

**Body:**
```json
{
  "empresa_id": "uuid",
  "numero_solicitud": "SOL-001",
  "fecha_solicitud": "2026-02-18",
  "fecha_requerida": "2026-02-25",
  "departamento_solicitante_id": "uuid",
  "usuario_solicitante_id": "uuid",
  "solicitante_nombre": "Juan Pérez",
  "almacen_destino_id": "uuid",
  "centro_costo_id": "uuid",
  "tipo_solicitud": "normal",
  "motivo_solicitud": "reposicion",
  "total_items": 5,
  "total_estimado": 15000.00,
  "moneda": "PEN",
  "estado": "borrador",
  "requiere_aprobacion": true,
  "observaciones": "Solicitud de reposición de stock"
}
```

#### Actualizar Solicitud
```http
PUT /api/v1/pur/solicitudes/{solicitud_id}
```

---

### 5. Cotizaciones

#### Listar Cotizaciones
```http
GET /api/v1/pur/cotizaciones
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `proveedor_id` (UUID, opcional): Filtrar por proveedor
- `solicitud_compra_id` (UUID, opcional): Filtrar por solicitud de compra
- `estado` (string, opcional): Filtrar por estado ('pendiente', 'recibida', 'evaluada', 'aceptada', 'rechazada', 'vencida')
- `fecha_desde` (date, opcional): Fecha desde (formato: YYYY-MM-DD)
- `fecha_hasta` (date, opcional): Fecha hasta (formato: YYYY-MM-DD)

**Response:** `200 OK`
```json
[
  {
    "cotizacion_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "numero_cotizacion": "COT-001",
    "fecha_cotizacion": "2026-02-18",
    "fecha_vencimiento": "2026-02-25",
    "proveedor_id": "uuid",
    "solicitud_compra_id": "uuid",
    "condicion_pago": "30_dias",
    "dias_credito": 30,
    "tiempo_entrega_dias": 7,
    "lugar_entrega": "Almacén Principal",
    "moneda": "PEN",
    "subtotal": 15000.00,
    "descuento": 500.00,
    "igv": 2610.00,
    "total": 17110.00,
    "estado": "recibida",
    "es_ganadora": false,
    "observaciones": null,
    "motivo_rechazo": null,
    "fecha_creacion": "2026-02-18T10:00:00Z",
    "fecha_actualizacion": null,
    "usuario_creacion_id": "uuid"
  }
]
```

#### Detalle de Cotización
```http
GET /api/v1/pur/cotizaciones/{cotizacion_id}
```

#### Crear Cotización
```http
POST /api/v1/pur/cotizaciones
```

**Body:**
```json
{
  "empresa_id": "uuid",
  "numero_cotizacion": "COT-001",
  "fecha_cotizacion": "2026-02-18",
  "fecha_vencimiento": "2026-02-25",
  "proveedor_id": "uuid",
  "solicitud_compra_id": "uuid",
  "condicion_pago": "30_dias",
  "dias_credito": 30,
  "tiempo_entrega_dias": 7,
  "lugar_entrega": "Almacén Principal",
  "moneda": "PEN",
  "subtotal": 15000.00,
  "descuento": 500.00,
  "igv": 2610.00,
  "total": 17110.00,
  "estado": "pendiente",
  "es_ganadora": false,
  "observaciones": null
}
```

#### Actualizar Cotización
```http
PUT /api/v1/pur/cotizaciones/{cotizacion_id}
```

---

### 6. Órdenes de Compra

#### Listar Órdenes de Compra
```http
GET /api/v1/pur/ordenes-compra
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `proveedor_id` (UUID, opcional): Filtrar por proveedor
- `solicitud_compra_id` (UUID, opcional): Filtrar por solicitud de compra
- `estado` (string, opcional): Filtrar por estado ('borrador', 'emitida', 'aprobada', 'parcial', 'completa', 'anulada')
- `fecha_desde` (date, opcional): Fecha desde (formato: YYYY-MM-DD)
- `fecha_hasta` (date, opcional): Fecha hasta (formato: YYYY-MM-DD)

**Response:** `200 OK`
```json
[
  {
    "orden_compra_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "numero_oc": "OC-001",
    "fecha_emision": "2026-02-18",
    "fecha_requerida": "2026-02-25",
    "proveedor_id": "uuid",
    "proveedor_razon_social": "Proveedor ABC S.A.C.",
    "proveedor_ruc": "20123456789",
    "almacen_destino_id": "uuid",
    "direccion_entrega": "Almacén Principal",
    "solicitud_compra_id": "uuid",
    "cotizacion_id": "uuid",
    "condicion_pago": "30_dias",
    "dias_credito": 30,
    "moneda": "PEN",
    "tipo_cambio": 1.0,
    "subtotal": 15000.00,
    "descuento_global": 500.00,
    "igv": 2610.00,
    "total": 17110.00,
    "total_items": 5,
    "items_recepcionados": 0,
    "porcentaje_recepcion": 0.0,
    "estado": "emitida",
    "requiere_aprobacion": true,
    "aprobado_por_usuario_id": "uuid",
    "fecha_aprobacion": "2026-02-18T10:05:00Z",
    "centro_costo_id": "uuid",
    "observaciones": null,
    "terminos_condiciones": null,
    "motivo_anulacion": null,
    "fecha_creacion": "2026-02-18T10:00:00Z",
    "fecha_actualizacion": null,
    "fecha_anulacion": null,
    "usuario_creacion_id": "uuid",
    "usuario_aprobacion_id": "uuid"
  }
]
```

#### Detalle de Orden de Compra
```http
GET /api/v1/pur/ordenes-compra/{orden_compra_id}
```

#### Crear Orden de Compra
```http
POST /api/v1/pur/ordenes-compra
```

**Body:**
```json
{
  "empresa_id": "uuid",
  "numero_oc": "OC-001",
  "fecha_emision": "2026-02-18",
  "fecha_requerida": "2026-02-25",
  "proveedor_id": "uuid",
  "proveedor_razon_social": "Proveedor ABC S.A.C.",
  "proveedor_ruc": "20123456789",
  "almacen_destino_id": "uuid",
  "direccion_entrega": "Almacén Principal",
  "solicitud_compra_id": "uuid",
  "cotizacion_id": "uuid",
  "condicion_pago": "30_dias",
  "dias_credito": 30,
  "moneda": "PEN",
  "tipo_cambio": 1.0,
  "subtotal": 15000.00,
  "descuento_global": 500.00,
  "igv": 2610.00,
  "total": 17110.00,
  "total_items": 5,
  "estado": "borrador",
  "requiere_aprobacion": true,
  "centro_costo_id": "uuid",
  "observaciones": null,
  "terminos_condiciones": null
}
```

#### Actualizar Orden de Compra
```http
PUT /api/v1/pur/ordenes-compra/{orden_compra_id}
```

---

### 7. Recepciones

#### Listar Recepciones
```http
GET /api/v1/pur/recepciones
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `orden_compra_id` (UUID, opcional): Filtrar por orden de compra
- `proveedor_id` (UUID, opcional): Filtrar por proveedor
- `almacen_id` (UUID, opcional): Filtrar por almacén
- `estado` (string, opcional): Filtrar por estado ('borrador', 'procesada', 'inspeccion', 'aprobada', 'anulada')
- `fecha_desde` (date, opcional): Fecha desde (formato: YYYY-MM-DD)
- `fecha_hasta` (date, opcional): Fecha hasta (formato: YYYY-MM-DD)

**Response:** `200 OK`
```json
[
  {
    "recepcion_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "numero_recepcion": "REC-001",
    "fecha_recepcion": "2026-02-20T10:00:00Z",
    "orden_compra_id": "uuid",
    "proveedor_id": "uuid",
    "almacen_id": "uuid",
    "guia_remision_numero": "T001-00012345",
    "guia_remision_fecha": "2026-02-20",
    "transportista": "Transportes XYZ",
    "placa_vehiculo": "ABC-123",
    "recepcionado_por_usuario_id": "uuid",
    "recepcionado_por_nombre": "Juan Pérez",
    "total_items": 5,
    "total_cantidad": 100.0,
    "estado": "procesada",
    "requiere_inspeccion": false,
    "inspeccion_id": null,
    "movimiento_inventario_id": "uuid",
    "observaciones": null,
    "incidencias": null,
    "fecha_creacion": "2026-02-20T10:00:00Z",
    "fecha_procesado": "2026-02-20T10:05:00Z",
    "usuario_creacion_id": "uuid",
    "usuario_procesado_id": "uuid"
  }
]
```

#### Detalle de Recepción
```http
GET /api/v1/pur/recepciones/{recepcion_id}
```

#### Crear Recepción
```http
POST /api/v1/pur/recepciones
```

**Body:**
```json
{
  "empresa_id": "uuid",
  "numero_recepcion": "REC-001",
  "fecha_recepcion": "2026-02-20T10:00:00Z",
  "orden_compra_id": "uuid",
  "proveedor_id": "uuid",
  "almacen_id": "uuid",
  "guia_remision_numero": "T001-00012345",
  "guia_remision_fecha": "2026-02-20",
  "transportista": "Transportes XYZ",
  "placa_vehiculo": "ABC-123",
  "recepcionado_por_usuario_id": "uuid",
  "recepcionado_por_nombre": "Juan Pérez",
  "total_items": 5,
  "total_cantidad": 100.0,
  "estado": "borrador",
  "requiere_inspeccion": false,
  "observaciones": null,
  "incidencias": null
}
```

#### Actualizar Recepción
```http
PUT /api/v1/pur/recepciones/{recepcion_id}
```

---

## 📋 Schemas TypeScript (Ejemplo)

```typescript
// Proveedor
interface Proveedor {
  proveedor_id: string;
  cliente_id: string;
  empresa_id: string;
  codigo_proveedor: string;
  razon_social: string;
  nombre_comercial?: string;
  tipo_documento?: string;
  numero_documento: string;
  tipo_proveedor?: string;
  categoria_proveedor?: string;
  direccion?: string;
  pais?: string;
  departamento?: string;
  provincia?: string;
  distrito?: string;
  ubigeo?: string;
  contacto_nombre?: string;
  contacto_cargo?: string;
  telefono_principal?: string;
  telefono_secundario?: string;
  email_principal?: string;
  email_cotizaciones?: string;
  sitio_web?: string;
  condicion_pago_defecto?: string;
  dias_credito_defecto?: number;
  moneda_preferida?: string;
  banco?: string;
  numero_cuenta?: string;
  tipo_cuenta?: string;
  cci?: string;
  calificacion?: number;
  nivel_confianza?: string;
  es_proveedor_homologado?: boolean;
  fecha_homologacion?: string;
  limite_credito?: number;
  saldo_pendiente?: number;
  estado?: string;
  motivo_bloqueo?: string;
  es_activo: boolean;
  observaciones?: string;
  fecha_creacion?: string;
  fecha_actualizacion?: string;
  usuario_creacion_id?: string;
  usuario_actualizacion_id?: string;
}

// Orden de Compra
interface OrdenCompra {
  orden_compra_id: string;
  cliente_id: string;
  empresa_id: string;
  numero_oc: string;
  fecha_emision: string;
  fecha_requerida: string;
  proveedor_id: string;
  proveedor_razon_social?: string;
  proveedor_ruc?: string;
  almacen_destino_id?: string;
  direccion_entrega?: string;
  solicitud_compra_id?: string;
  cotizacion_id?: string;
  condicion_pago: string;
  dias_credito?: number;
  moneda?: string;
  tipo_cambio?: number;
  subtotal?: number;
  descuento_global?: number;
  igv?: number;
  total?: number;
  total_items?: number;
  items_recepcionados?: number;
  porcentaje_recepcion?: number;
  estado: string;
  requiere_aprobacion?: boolean;
  aprobado_por_usuario_id?: string;
  fecha_aprobacion?: string;
  centro_costo_id?: string;
  observaciones?: string;
  terminos_condiciones?: string;
  motivo_anulacion?: string;
  fecha_creacion?: string;
  fecha_actualizacion?: string;
  fecha_anulacion?: string;
  usuario_creacion_id?: string;
  usuario_aprobacion_id?: string;
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
  "detail": "Proveedor no encontrado"
}
```

---

## 🗺️ Rutas SPA Recomendadas

```
/compras
├── /proveedores
│   ├── /listar
│   ├── /crear
│   ├── /editar/:id
│   └── /detalle/:id
├── /contactos
│   ├── /listar
│   ├── /crear
│   └── /editar/:id
├── /productos-proveedor
│   ├── /listar
│   ├── /crear
│   └── /editar/:id
├── /solicitudes
│   ├── /listar
│   ├── /crear
│   ├── /editar/:id
│   └── /detalle/:id
├── /cotizaciones
│   ├── /listar
│   ├── /crear
│   ├── /editar/:id
│   └── /detalle/:id
├── /ordenes-compra
│   ├── /listar
│   ├── /crear
│   ├── /editar/:id
│   └── /detalle/:id
└── /recepciones
    ├── /listar
    ├── /crear
    ├── /editar/:id
    └── /detalle/:id
```

---

## 🚀 Flujo de Implementación Recomendado

### Fase 1: Maestros
1. **Proveedores** - Crear catálogo completo de proveedores
   - Formulario completo con todos los campos esenciales
   - Búsqueda por razón social, RUC o código
   - Vista de detalle completa

2. **Contactos de Proveedor** - Gestionar contactos por proveedor
   - Lista de contactos por proveedor
   - Crear/editar contactos

3. **Productos por Proveedor** - Catálogo de productos que ofrece cada proveedor
   - Lista de productos por proveedor
   - Precios y condiciones de compra
   - Proveedor preferido por producto

### Fase 2: Proceso de Compra
1. **Solicitudes de Compra** - Requisiciones internas
   - Crear solicitud de compra
   - Aprobación de solicitudes
   - Vista de solicitudes pendientes

2. **Cotizaciones** - Comparación de precios
   - Solicitar cotizaciones a proveedores
   - Recibir y evaluar cotizaciones
   - Marcar cotización ganadora

3. **Órdenes de Compra** - Formalización de compra
   - Crear orden de compra desde solicitud/cotización
   - Aprobación de órdenes
   - Seguimiento de recepción (items_recepcionados, porcentaje_recepcion)

### Fase 3: Recepción
1. **Recepciones** - Entrada de mercadería
   - Crear recepción desde orden de compra
   - Registrar productos recibidos
   - Generar movimiento de inventario (integración con INV)

---

## 📝 Notas Importantes

1. **Multi-tenancy:** Todos los endpoints filtran automáticamente por `cliente_id` del token. No enviar `cliente_id` en el body.

2. **Dependencias:** El módulo PUR requiere:
   - Empresas configuradas (módulo ORG)
   - Departamentos (para solicitudes)
   - Centros de costo (para solicitudes y órdenes)
   - Productos configurados (módulo INV)
   - Almacenes (para solicitudes y recepciones)
   - Unidades de medida (para productos por proveedor)

3. **Estados de Solicitud:**
   - `borrador` - En edición
   - `pendiente_aprobacion` - Esperando aprobación
   - `aprobada` - Aprobada, lista para generar OC
   - `rechazada` - Rechazada
   - `procesada` - Ya se generó orden de compra
   - `anulada` - Anulada

4. **Estados de Cotización:**
   - `pendiente` - Solicitada, esperando respuesta
   - `recibida` - Recibida del proveedor
   - `evaluada` - En evaluación
   - `aceptada` - Aceptada (puede generar OC)
   - `rechazada` - Rechazada
   - `vencida` - Vencida

5. **Estados de Orden de Compra:**
   - `borrador` - En edición
   - `emitida` - Emitida al proveedor
   - `aprobada` - Aprobada
   - `parcial` - Parcialmente recepcionada
   - `completa` - Completamente recepcionada
   - `anulada` - Anulada

6. **Estados de Recepción:**
   - `borrador` - En edición
   - `procesada` - Procesada y afecta stock
   - `inspeccion` - En inspección de calidad (QMS)
   - `aprobada` - Aprobada después de inspección
   - `anulada` - Anulada

7. **Control de Recepción:** La orden de compra incluye campos `items_recepcionados` y `porcentaje_recepcion` para seguimiento del avance de recepción.

8. **Integración con INV:** Las recepciones generan movimientos de inventario (campo `movimiento_inventario_id`) que actualizan el stock.

---

## 🔗 Referencias

- **Módulo ORG:** Ver `DOC_FRONTEND_MODULO_ORG.md` para empresas, departamentos, centros de costo.
- **Módulo INV:** Ver `DOC_FRONTEND_MODULO_INV.md` para productos, almacenes, unidades de medida.
- **API Base:** `/api/v1/`
- **Documentación Swagger:** `/docs` (cuando el servidor esté corriendo)

---

**Última actualización:** 2026-02-18
