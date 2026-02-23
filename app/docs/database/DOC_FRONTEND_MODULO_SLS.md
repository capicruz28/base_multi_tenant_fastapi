# Documentación Frontend — Módulo SLS (Ventas)

**Versión:** 1.0  
**Fecha:** 2026-02-18  
**Módulo:** SLS - Ventas ERP

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
/api/v1/sls
```

### Dependencias
- **Módulo ORG:** Requiere tener empresas y centros de costo configurados.
- **Módulo INV:** Requiere tener productos, almacenes y unidades de medida configurados.
- **Orden recomendado:** Configurar primero ORG e INV, luego SLS.

---

## 🔐 Autenticación

Todos los endpoints requieren autenticación mediante JWT token en el header:

```http
Authorization: Bearer <token>
```

El `cliente_id` se obtiene automáticamente del token, **nunca debe enviarse en el body**.

---

## 📡 Endpoints

### 1. Clientes

#### Listar Clientes
```http
GET /api/v1/sls/clientes
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `solo_activos` (boolean, default: true): Solo clientes activos
- `buscar` (string, opcional): Búsqueda por razón social, RUC o código
- `vendedor_usuario_id` (UUID, opcional): Filtrar por vendedor asignado

**Response:** `200 OK`
```json
[
  {
    "cliente_venta_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "codigo_cliente": "CLI001",
    "tipo_cliente": "empresa",
    "razon_social": "Cliente ABC S.A.C.",
    "nombre_comercial": "ABC",
    "tipo_documento": "RUC",
    "numero_documento": "20123456789",
    "categoria_cliente": "mayorista",
    "segmento": "A",
    "canal_venta": "directo",
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
    "email_principal": "contacto@clienteabc.com",
    "email_facturacion": "facturacion@clienteabc.com",
    "sitio_web": "https://www.clienteabc.com",
    "condicion_pago_defecto": "30_dias",
    "dias_credito_defecto": 30,
    "moneda_preferida": "PEN",
    "lista_precio_id": null,
    "limite_credito": 100000.00,
    "saldo_pendiente": 25000.00,
    "saldo_vencido": 0.00,
    "vendedor_usuario_id": "uuid",
    "vendedor_nombre": "María González",
    "banco": "Banco de Crédito",
    "numero_cuenta": "1234567890",
    "calificacion": 4.5,
    "nivel_riesgo": "bajo",
    "estado": "activo",
    "motivo_bloqueo": null,
    "es_activo": true,
    "observaciones": "Cliente preferencial",
    "fecha_creacion": "2025-01-15T10:30:00",
    "fecha_actualizacion": "2025-02-10T14:20:00",
    "fecha_primera_compra": "2025-01-20",
    "fecha_ultima_compra": "2025-02-15",
    "usuario_creacion_id": "uuid"
  }
]
```

#### Obtener Cliente por ID
```http
GET /api/v1/sls/clientes/{cliente_venta_id}
```

**Response:** `200 OK` (mismo schema que listar)

#### Crear Cliente
```http
POST /api/v1/sls/clientes
```

**Request Body:**
```json
{
  "empresa_id": "uuid",
  "codigo_cliente": "CLI001",
  "tipo_cliente": "empresa",
  "razon_social": "Cliente ABC S.A.C.",
  "nombre_comercial": "ABC",
  "tipo_documento": "RUC",
  "numero_documento": "20123456789",
  "categoria_cliente": "mayorista",
  "segmento": "A",
  "canal_venta": "directo",
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
  "email_principal": "contacto@clienteabc.com",
  "email_facturacion": "facturacion@clienteabc.com",
  "sitio_web": "https://www.clienteabc.com",
  "condicion_pago_defecto": "30_dias",
  "dias_credito_defecto": 30,
  "moneda_preferida": "PEN",
  "limite_credito": 100000.00,
  "vendedor_usuario_id": "uuid",
  "vendedor_nombre": "María González",
  "banco": "Banco de Crédito",
  "numero_cuenta": "1234567890",
  "calificacion": 4.5,
  "nivel_riesgo": "bajo",
  "estado": "activo",
  "es_activo": true,
  "observaciones": "Cliente preferencial"
}
```

**Response:** `201 Created` (mismo schema que listar)

#### Actualizar Cliente
```http
PUT /api/v1/sls/clientes/{cliente_venta_id}
```

**Request Body:** (todos los campos opcionales, solo enviar los que se desean actualizar)
```json
{
  "razon_social": "Cliente ABC S.A.C. Actualizado",
  "telefono_principal": "+51 1 2345679",
  "limite_credito": 150000.00
}
```

**Response:** `200 OK` (mismo schema que listar)

---

### 2. Contactos de Cliente

#### Listar Contactos
```http
GET /api/v1/sls/contactos
```

**Query Parameters:**
- `cliente_venta_id` (UUID, opcional): Filtrar por cliente
- `solo_activos` (boolean, default: true): Solo contactos activos

**Response:** `200 OK`
```json
[
  {
    "contacto_id": "uuid",
    "cliente_id": "uuid",
    "cliente_venta_id": "uuid",
    "nombre_completo": "Juan Pérez",
    "cargo": "Gerente Comercial",
    "area": "Ventas",
    "telefono": "+51 1 2345678",
    "telefono_movil": "+51 987654321",
    "email": "juan.perez@clienteabc.com",
    "es_contacto_principal": true,
    "es_contacto_comercial": true,
    "es_contacto_cobranzas": false,
    "fecha_nacimiento": "1985-05-15",
    "observaciones": "Contacto principal para negociaciones",
    "es_activo": true,
    "fecha_creacion": "2025-01-15T10:30:00"
  }
]
```

#### Crear Contacto
```http
POST /api/v1/sls/contactos
```

**Request Body:**
```json
{
  "cliente_venta_id": "uuid",
  "nombre_completo": "Juan Pérez",
  "cargo": "Gerente Comercial",
  "area": "Ventas",
  "telefono": "+51 1 2345678",
  "telefono_movil": "+51 987654321",
  "email": "juan.perez@clienteabc.com",
  "es_contacto_principal": true,
  "es_contacto_comercial": true,
  "es_contacto_cobranzas": false,
  "fecha_nacimiento": "1985-05-15",
  "observaciones": "Contacto principal para negociaciones",
  "es_activo": true
}
```

---

### 3. Direcciones de Cliente

#### Listar Direcciones
```http
GET /api/v1/sls/direcciones
```

**Query Parameters:**
- `cliente_venta_id` (UUID, opcional): Filtrar por cliente
- `solo_activos` (boolean, default: true): Solo direcciones activas

**Response:** `200 OK`
```json
[
  {
    "direccion_id": "uuid",
    "cliente_id": "uuid",
    "cliente_venta_id": "uuid",
    "codigo_direccion": "DIR001",
    "nombre_direccion": "Almacén Principal",
    "direccion": "Av. Principal 123",
    "referencia": "Frente al parque",
    "pais": "Perú",
    "departamento": "Lima",
    "provincia": "Lima",
    "distrito": "San Isidro",
    "ubigeo": "150131",
    "codigo_postal": "15073",
    "contacto_nombre": "Juan Pérez",
    "contacto_telefono": "+51 987654321",
    "es_direccion_fiscal": true,
    "es_direccion_entrega_defecto": true,
    "es_activo": true,
    "fecha_creacion": "2025-01-15T10:30:00"
  }
]
```

#### Crear Dirección
```http
POST /api/v1/sls/direcciones
```

**Request Body:**
```json
{
  "cliente_venta_id": "uuid",
  "codigo_direccion": "DIR001",
  "nombre_direccion": "Almacén Principal",
  "direccion": "Av. Principal 123",
  "referencia": "Frente al parque",
  "pais": "Perú",
  "departamento": "Lima",
  "provincia": "Lima",
  "distrito": "San Isidro",
  "ubigeo": "150131",
  "codigo_postal": "15073",
  "contacto_nombre": "Juan Pérez",
  "contacto_telefono": "+51 987654321",
  "es_direccion_fiscal": true,
  "es_direccion_entrega_defecto": true,
  "es_activo": true
}
```

---

### 4. Cotizaciones

#### Listar Cotizaciones
```http
GET /api/v1/sls/cotizaciones
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `cliente_venta_id` (UUID, opcional): Filtrar por cliente
- `vendedor_usuario_id` (UUID, opcional): Filtrar por vendedor
- `estado` (string, opcional): Filtrar por estado (borrador, enviada, aceptada, rechazada, vencida, convertida)
- `fecha_desde` (date, opcional): Filtrar desde fecha
- `fecha_hasta` (date, opcional): Filtrar hasta fecha

**Response:** `200 OK`
```json
[
  {
    "cotizacion_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "numero_cotizacion": "COT-2025-001",
    "fecha_cotizacion": "2025-02-15",
    "fecha_vencimiento": "2025-03-15",
    "cliente_venta_id": "uuid",
    "cliente_razon_social": "Cliente ABC S.A.C.",
    "cliente_ruc": "20123456789",
    "contacto_nombre": "Juan Pérez",
    "vendedor_usuario_id": "uuid",
    "vendedor_nombre": "María González",
    "oportunidad_id": null,
    "condicion_pago": "30_dias",
    "dias_credito": 30,
    "tiempo_entrega_dias": 15,
    "moneda": "PEN",
    "tipo_cambio": 1.0000,
    "subtotal": 10000.00,
    "descuento_global": 500.00,
    "igv": 1710.00,
    "total": 11210.00,
    "estado": "enviada",
    "fecha_envio": "2025-02-16T10:00:00",
    "fecha_respuesta": null,
    "motivo_rechazo": null,
    "convertida_pedido": false,
    "pedido_venta_id": null,
    "fecha_conversion": null,
    "observaciones": "Cotización válida por 30 días",
    "terminos_condiciones": "Pago a 30 días, entrega en almacén del cliente",
    "fecha_creacion": "2025-02-15T10:30:00",
    "fecha_actualizacion": "2025-02-16T10:00:00",
    "usuario_creacion_id": "uuid"
  }
]
```

#### Crear Cotización
```http
POST /api/v1/sls/cotizaciones
```

**Request Body:**
```json
{
  "empresa_id": "uuid",
  "numero_cotizacion": "COT-2025-001",
  "fecha_cotizacion": "2025-02-15",
  "fecha_vencimiento": "2025-03-15",
  "cliente_venta_id": "uuid",
  "cliente_razon_social": "Cliente ABC S.A.C.",
  "cliente_ruc": "20123456789",
  "contacto_nombre": "Juan Pérez",
  "vendedor_usuario_id": "uuid",
  "vendedor_nombre": "María González",
  "condicion_pago": "30_dias",
  "dias_credito": 30,
  "tiempo_entrega_dias": 15,
  "moneda": "PEN",
  "tipo_cambio": 1.0000,
  "subtotal": 10000.00,
  "descuento_global": 500.00,
  "igv": 1710.00,
  "total": 11210.00,
  "estado": "borrador",
  "observaciones": "Cotización válida por 30 días",
  "terminos_condiciones": "Pago a 30 días, entrega en almacén del cliente"
}
```

---

### 5. Pedidos

#### Listar Pedidos
```http
GET /api/v1/sls/pedidos
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `cliente_venta_id` (UUID, opcional): Filtrar por cliente
- `vendedor_usuario_id` (UUID, opcional): Filtrar por vendedor
- `cotizacion_id` (UUID, opcional): Filtrar por cotización origen
- `estado` (string, opcional): Filtrar por estado (borrador, confirmado, aprobado, parcial, completo, facturado, anulado)
- `fecha_desde` (date, opcional): Filtrar desde fecha
- `fecha_hasta` (date, opcional): Filtrar hasta fecha

**Response:** `200 OK`
```json
[
  {
    "pedido_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "numero_pedido": "PED-2025-001",
    "fecha_pedido": "2025-02-20",
    "fecha_entrega_prometida": "2025-03-05",
    "cliente_venta_id": "uuid",
    "cliente_razon_social": "Cliente ABC S.A.C.",
    "cliente_ruc": "20123456789",
    "direccion_entrega_id": "uuid",
    "direccion_entrega_texto": "Av. Principal 123, San Isidro",
    "cotizacion_id": "uuid",
    "orden_compra_cliente": "OC-2025-001",
    "vendedor_usuario_id": "uuid",
    "vendedor_nombre": "María González",
    "condicion_pago": "30_dias",
    "dias_credito": 30,
    "moneda": "PEN",
    "tipo_cambio": 1.0000,
    "subtotal": 10000.00,
    "descuento_global": 500.00,
    "igv": 1710.00,
    "total": 11210.00,
    "total_items": 5,
    "items_despachados": 0,
    "porcentaje_despacho": 0.00,
    "estado": "confirmado",
    "requiere_aprobacion": false,
    "aprobado_por_usuario_id": null,
    "fecha_aprobacion": null,
    "prioridad": 3,
    "centro_costo_id": "uuid",
    "observaciones": "Pedido confirmado por cliente",
    "instrucciones_despacho": "Entregar en horario de oficina",
    "motivo_anulacion": null,
    "fecha_creacion": "2025-02-20T10:30:00",
    "fecha_actualizacion": "2025-02-20T11:00:00",
    "fecha_anulacion": null,
    "usuario_creacion_id": "uuid"
  }
]
```

#### Crear Pedido
```http
POST /api/v1/sls/pedidos
```

**Request Body:**
```json
{
  "empresa_id": "uuid",
  "numero_pedido": "PED-2025-001",
  "fecha_pedido": "2025-02-20",
  "fecha_entrega_prometida": "2025-03-05",
  "cliente_venta_id": "uuid",
  "cliente_razon_social": "Cliente ABC S.A.C.",
  "cliente_ruc": "20123456789",
  "direccion_entrega_id": "uuid",
  "direccion_entrega_texto": "Av. Principal 123, San Isidro",
  "cotizacion_id": "uuid",
  "orden_compra_cliente": "OC-2025-001",
  "vendedor_usuario_id": "uuid",
  "vendedor_nombre": "María González",
  "condicion_pago": "30_dias",
  "dias_credito": 30,
  "moneda": "PEN",
  "tipo_cambio": 1.0000,
  "subtotal": 10000.00,
  "descuento_global": 500.00,
  "igv": 1710.00,
  "total": 11210.00,
  "total_items": 5,
  "items_despachados": 0,
  "porcentaje_despacho": 0.00,
  "estado": "borrador",
  "requiere_aprobacion": false,
  "prioridad": 3,
  "centro_costo_id": "uuid",
  "observaciones": "Pedido generado desde cotización",
  "instrucciones_despacho": "Entregar en horario de oficina"
}
```

---

## 📝 Schemas TypeScript

### Cliente
```typescript
interface Cliente {
  cliente_venta_id: string;
  cliente_id: string;
  empresa_id: string;
  codigo_cliente: string;
  tipo_cliente: 'empresa' | 'persona';
  razon_social: string;
  nombre_comercial?: string;
  tipo_documento: 'RUC' | 'DNI' | 'CE' | 'PASAPORTE';
  numero_documento: string;
  categoria_cliente?: string;
  segmento?: string;
  canal_venta?: string;
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
  email_facturacion?: string;
  sitio_web?: string;
  condicion_pago_defecto?: string;
  dias_credito_defecto: number;
  moneda_preferida: string;
  lista_precio_id?: string;
  limite_credito?: number;
  saldo_pendiente: number;
  saldo_vencido: number;
  vendedor_usuario_id?: string;
  vendedor_nombre?: string;
  banco?: string;
  numero_cuenta?: string;
  calificacion?: number;
  nivel_riesgo: 'bajo' | 'medio' | 'alto';
  estado: 'prospecto' | 'activo' | 'inactivo' | 'bloqueado';
  motivo_bloqueo?: string;
  es_activo: boolean;
  observaciones?: string;
  fecha_creacion: string;
  fecha_actualizacion?: string;
  fecha_primera_compra?: string;
  fecha_ultima_compra?: string;
  usuario_creacion_id?: string;
}
```

### Cotización
```typescript
interface Cotizacion {
  cotizacion_id: string;
  cliente_id: string;
  empresa_id: string;
  numero_cotizacion: string;
  fecha_cotizacion: string;
  fecha_vencimiento: string;
  cliente_venta_id: string;
  cliente_razon_social?: string;
  cliente_ruc?: string;
  contacto_nombre?: string;
  vendedor_usuario_id?: string;
  vendedor_nombre?: string;
  oportunidad_id?: string;
  condicion_pago: string;
  dias_credito: number;
  tiempo_entrega_dias?: number;
  moneda: string;
  tipo_cambio: number;
  subtotal: number;
  descuento_global: number;
  igv: number;
  total: number;
  estado: 'borrador' | 'enviada' | 'aceptada' | 'rechazada' | 'vencida' | 'convertida';
  fecha_envio?: string;
  fecha_respuesta?: string;
  motivo_rechazo?: string;
  convertida_pedido: boolean;
  pedido_venta_id?: string;
  fecha_conversion?: string;
  observaciones?: string;
  terminos_condiciones?: string;
  fecha_creacion: string;
  fecha_actualizacion?: string;
  usuario_creacion_id?: string;
}
```

### Pedido
```typescript
interface Pedido {
  pedido_id: string;
  cliente_id: string;
  empresa_id: string;
  numero_pedido: string;
  fecha_pedido: string;
  fecha_entrega_prometida: string;
  cliente_venta_id: string;
  cliente_razon_social?: string;
  cliente_ruc?: string;
  direccion_entrega_id?: string;
  direccion_entrega_texto?: string;
  cotizacion_id?: string;
  orden_compra_cliente?: string;
  vendedor_usuario_id?: string;
  vendedor_nombre?: string;
  condicion_pago: string;
  dias_credito: number;
  moneda: string;
  tipo_cambio: number;
  subtotal: number;
  descuento_global: number;
  igv: number;
  total: number;
  total_items: number;
  items_despachados: number;
  porcentaje_despacho: number;
  estado: 'borrador' | 'confirmado' | 'aprobado' | 'parcial' | 'completo' | 'facturado' | 'anulado';
  requiere_aprobacion: boolean;
  aprobado_por_usuario_id?: string;
  fecha_aprobacion?: string;
  prioridad: 1 | 2 | 3 | 4; // 1=Urgente, 2=Alta, 3=Normal, 4=Baja
  centro_costo_id?: string;
  observaciones?: string;
  instrucciones_despacho?: string;
  motivo_anulacion?: string;
  fecha_creacion: string;
  fecha_actualizacion?: string;
  fecha_anulacion?: string;
  usuario_creacion_id?: string;
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
/sls
  /clientes
    /listado          # Lista de clientes
    /nuevo            # Formulario crear cliente
    /:id              # Detalle cliente
    /:id/editar       # Formulario editar cliente
    /:id/contactos    # Contactos del cliente
    /:id/direcciones  # Direcciones del cliente
  /cotizaciones
    /listado          # Lista de cotizaciones
    /nuevo            # Formulario crear cotización
    /:id              # Detalle cotización
    /:id/editar       # Formulario editar cotización
  /pedidos
    /listado          # Lista de pedidos
    /nuevo            # Formulario crear pedido
    /:id              # Detalle pedido
    /:id/editar       # Formulario editar pedido
```

---

## 🚀 Flujo de Implementación Recomendado

### Fase 1: Maestros
1. **Clientes**
   - Implementar CRUD completo de clientes
   - Validar campos obligatorios (razon_social, numero_documento)
   - Implementar búsqueda y filtros

2. **Contactos y Direcciones**
   - Implementar gestión de contactos por cliente
   - Implementar gestión de direcciones por cliente
   - Marcar contacto/dirección principal

### Fase 2: Proceso de Venta
1. **Cotizaciones**
   - Crear cotización desde cliente
   - Agregar items (productos) a cotización
   - Calcular totales (subtotal, descuento, IGV, total)
   - Cambiar estado (borrador → enviada → aceptada/rechazada)
   - Convertir cotización a pedido

2. **Pedidos**
   - Crear pedido desde cotización o manualmente
   - Agregar items (productos) a pedido
   - Calcular totales
   - Cambiar estado (borrador → confirmado → aprobado → parcial → completo → facturado)
   - Control de despacho (items_despachados, porcentaje_despacho)

### Fase 3: Integración con Otros Módulos
1. **Con INV:**
   - Validar stock disponible al crear pedido
   - Reservar stock al confirmar pedido
   - Generar salida de inventario al despachar

2. **Con ORG:**
   - Filtrar por empresa
   - Asignar centro de costo al pedido

---

## 📌 Notas Importantes

1. **Multi-tenancy:** Todos los endpoints filtran automáticamente por `cliente_id` del token. No enviar `cliente_id` en el body.

2. **Dependencias:**
   - Requiere módulo ORG (empresas, centros de costo)
   - Requiere módulo INV (productos, almacenes, unidades de medida)

3. **Estados de Documentos:**
   - **Cotización:** borrador → enviada → aceptada/rechazada/vencida → convertida
   - **Pedido:** borrador → confirmado → aprobado → parcial → completo → facturado → anulado

4. **Campos Calculados:**
   - Los totales (subtotal, IGV, total) pueden calcularse en frontend o backend
   - El porcentaje de despacho se calcula: `(items_despachados / total_items) * 100`

5. **Conversión Cotización → Pedido:**
   - Al convertir una cotización a pedido, se debe actualizar el campo `convertida_pedido` y `pedido_venta_id` en la cotización
   - El pedido debe referenciar la cotización en `cotizacion_id`

6. **Validaciones Recomendadas:**
   - Validar límite de crédito del cliente antes de crear pedido
   - Validar stock disponible antes de confirmar pedido
   - Validar que el cliente esté activo antes de crear cotización/pedido

---

**Fin de la documentación**
