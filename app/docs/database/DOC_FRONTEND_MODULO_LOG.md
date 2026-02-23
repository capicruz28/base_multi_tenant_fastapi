# Documentación Frontend — Módulo LOG (Logística y Distribución)

**Versión:** 1.0  
**Fecha:** 2026-02-18  
**Módulo:** LOG - Logística y Distribución ERP

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
/api/v1/log
```

### Dependencias
- **Módulo ORG:** Requiere tener empresas y sucursales configuradas.
- **Módulo INV:** Requiere tener productos y unidades de medida configuradas.
- **Módulo SLS:** Opcional, para vincular guías de remisión a ventas.
- **Orden recomendado:** Configurar primero ORG e INV, luego LOG.

---

## 🔐 Autenticación

Todos los endpoints requieren autenticación mediante JWT token en el header:

```http
Authorization: Bearer <token>
```

El `cliente_id` se obtiene automáticamente del token, **nunca debe enviarse en el body**.

---

## 📡 Endpoints

### 1. Transportistas

#### Listar Transportistas
```http
GET /api/v1/log/transportistas
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `solo_activos` (boolean, default: true): Solo transportistas activos
- `buscar` (string, opcional): Búsqueda por razón social, código o documento

**Response:** `200 OK`
```json
[
  {
    "transportista_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "codigo_transportista": "TRANS001",
    "razon_social": "Transportes ABC S.A.C.",
    "nombre_comercial": "Transportes ABC",
    "tipo_documento": "RUC",
    "numero_documento": "20123456789",
    "numero_mtc": "MTC-12345",
    "telefono": "+51 987654321",
    "email": "contacto@transabc.com",
    "direccion": "Av. Principal 123",
    "tarifa_km": 2.50,
    "tarifa_hora": 50.00,
    "moneda_tarifa": "PEN",
    "calificacion": 4.5,
    "es_activo": true,
    "fecha_creacion": "2025-01-01T10:00:00",
    "usuario_creacion_id": "uuid"
  }
]
```

#### Obtener Transportista por ID
```http
GET /api/v1/log/transportistas/{transportista_id}
```

#### Crear Transportista
```http
POST /api/v1/log/transportistas
```

**Request Body:**
```json
{
  "empresa_id": "uuid",
  "codigo_transportista": "TRANS001",
  "razon_social": "Transportes ABC S.A.C.",
  "numero_documento": "20123456789",
  "tarifa_km": 2.50,
  "tarifa_hora": 50.00
}
```

#### Actualizar Transportista
```http
PUT /api/v1/log/transportistas/{transportista_id}
```

---

### 2. Vehículos

#### Listar Vehículos
```http
GET /api/v1/log/vehiculos
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `transportista_id` (UUID, opcional): Filtrar por transportista
- `tipo_propiedad` (string, opcional): 'propio' o 'tercero'
- `estado_vehiculo` (string, opcional): 'disponible', 'en_ruta', 'mantenimiento', 'inactivo'
- `solo_activos` (boolean, default: true)
- `buscar` (string, opcional): Búsqueda por placa, marca o modelo

**Response:** `200 OK`
```json
[
  {
    "vehiculo_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "placa": "ABC-123",
    "marca": "Mercedes-Benz",
    "modelo": "Sprinter",
    "año": 2023,
    "tipo_vehiculo": "camioneta",
    "categoria_vehiculo": "mediano",
    "capacidad_kg": 3500.00,
    "capacidad_m3": 15.00,
    "tipo_propiedad": "propio",
    "transportista_id": null,
    "conductor_nombre": "Juan Pérez",
    "conductor_licencia": "A2B",
    "soat_numero": "SOAT-12345",
    "soat_vencimiento": "2025-12-31",
    "tiene_gps": true,
    "codigo_gps": "GPS-001",
    "estado_vehiculo": "disponible",
    "es_activo": true
  }
]
```

#### Crear Vehículo
```http
POST /api/v1/log/vehiculos
```

**Request Body:**
```json
{
  "empresa_id": "uuid",
  "placa": "ABC-123",
  "marca": "Mercedes-Benz",
  "modelo": "Sprinter",
  "tipo_vehiculo": "camioneta",
  "tipo_propiedad": "propio",
  "capacidad_kg": 3500.00
}
```

---

### 3. Rutas

#### Listar Rutas
```http
GET /api/v1/log/rutas
```

**Query Parameters:**
- `empresa_id` (UUID, opcional)
- `origen_sucursal_id` (UUID, opcional)
- `solo_activos` (boolean, default: true)
- `buscar` (string, opcional)

**Response:** `200 OK`
```json
[
  {
    "ruta_id": "uuid",
    "codigo_ruta": "RUTA001",
    "nombre_ruta": "Lima - Trujillo",
    "origen_sucursal_id": "uuid",
    "destino_descripcion": "Trujillo, La Libertad",
    "distancia_km": 560.00,
    "tiempo_estimado_horas": 8.50,
    "costo_estimado": 1400.00,
    "cantidad_peajes": 3,
    "costo_peajes": 45.00,
    "es_activo": true
  }
]
```

---

### 4. Guías de Remisión

#### Listar Guías de Remisión
```http
GET /api/v1/log/guias-remision
```

**Query Parameters:**
- `empresa_id` (UUID, opcional)
- `estado` (string, opcional): 'borrador', 'emitida', 'en_transito', 'entregada', 'anulada'
- `motivo_traslado` (string, opcional): 'venta', 'compra', 'transferencia', 'consignacion', 'devolucion'
- `transportista_id` (UUID, opcional)
- `fecha_desde` (date, opcional)
- `fecha_hasta` (date, opcional)
- `buscar` (string, opcional)

**Response:** `200 OK`
```json
[
  {
    "guia_remision_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "serie": "T001",
    "numero": "000001",
    "fecha_emision": "2025-02-18",
    "fecha_traslado": "2025-02-19",
    "tipo_guia": "remitente",
    "motivo_traslado": "venta",
    "remitente_razon_social": "Mi Empresa S.A.C.",
    "remitente_ruc": "20123456789",
    "destinatario_razon_social": "Cliente XYZ S.A.C.",
    "punto_partida": "Lima, Lima",
    "punto_llegada": "Trujillo, La Libertad",
    "modalidad_transporte": "privado",
    "vehiculo_id": "uuid",
    "vehiculo_placa": "ABC-123",
    "conductor_nombre": "Juan Pérez",
    "total_bultos": 10,
    "peso_total_kg": 500.00,
    "estado": "emitida",
    "codigo_hash": "abc123...",
    "codigo_qr": "data:image/png;base64,..."
  }
]
```

#### Crear Guía de Remisión
```http
POST /api/v1/log/guias-remision
```

**Request Body:**
```json
{
  "empresa_id": "uuid",
  "serie": "T001",
  "numero": "000001",
  "fecha_traslado": "2025-02-19",
  "tipo_guia": "remitente",
  "motivo_traslado": "venta",
  "remitente_razon_social": "Mi Empresa S.A.C.",
  "remitente_ruc": "20123456789",
  "destinatario_razon_social": "Cliente XYZ S.A.C.",
  "punto_partida": "Lima, Lima",
  "punto_llegada": "Trujillo, La Libertad",
  "modalidad_transporte": "privado",
  "vehiculo_id": "uuid"
}
```

#### Detalles de Guía de Remisión
```http
GET /api/v1/log/guias-remision/{guia_remision_id}/detalles
POST /api/v1/log/guias-remision/{guia_remision_id}/detalles
```

**Request Body (POST detalle):**
```json
{
  "producto_id": "uuid",
  "cantidad": 10.00,
  "unidad_medida_id": "uuid",
  "peso_kg": 50.00
}
```

---

### 5. Despachos

#### Listar Despachos
```http
GET /api/v1/log/despachos
```

**Query Parameters:**
- `empresa_id` (UUID, opcional)
- `estado` (string, opcional): 'planificado', 'en_ruta', 'completado', 'cancelado'
- `ruta_id` (UUID, opcional)
- `vehiculo_id` (UUID, opcional)
- `fecha_desde` (date, opcional)
- `fecha_hasta` (date, opcional)
- `buscar` (string, opcional)

**Response:** `200 OK`
```json
[
  {
    "despacho_id": "uuid",
    "numero_despacho": "DESP-001",
    "fecha_programada": "2025-02-19",
    "hora_salida_programada": "08:00:00",
    "ruta_id": "uuid",
    "vehiculo_id": "uuid",
    "conductor_nombre": "Juan Pérez",
    "fecha_salida_real": "2025-02-19T08:15:00",
    "km_inicial": 1000.00,
    "km_final": 1560.00,
    "total_guias": 5,
    "total_peso_kg": 2500.00,
    "costo_combustible": 350.00,
    "costo_peajes": 45.00,
    "estado": "en_ruta"
  }
]
```

#### Crear Despacho
```http
POST /api/v1/log/despachos
```

**Request Body:**
```json
{
  "empresa_id": "uuid",
  "numero_despacho": "DESP-001",
  "fecha_programada": "2025-02-19",
  "hora_salida_programada": "08:00:00",
  "ruta_id": "uuid",
  "vehiculo_id": "uuid",
  "conductor_nombre": "Juan Pérez"
}
```

#### Guías de un Despacho
```http
GET /api/v1/log/despachos/{despacho_id}/guias
POST /api/v1/log/despachos/{despacho_id}/guias
```

**Request Body (POST):**
```json
{
  "guia_remision_id": "uuid",
  "orden_entrega": 1,
  "estado_entrega": "pendiente"
}
```

---

## 📝 Schemas TypeScript

### Transportista
```typescript
interface Transportista {
  transportista_id: string;
  cliente_id: string;
  empresa_id: string;
  codigo_transportista: string;
  razon_social: string;
  nombre_comercial?: string;
  tipo_documento: string;
  numero_documento: string;
  tarifa_km?: number;
  tarifa_hora?: number;
  calificacion?: number;
  es_activo: boolean;
}
```

### Vehiculo
```typescript
interface Vehiculo {
  vehiculo_id: string;
  placa: string;
  marca?: string;
  modelo?: string;
  tipo_vehiculo: 'camion' | 'camioneta' | 'furgon' | 'moto' | 'trailer';
  tipo_propiedad: 'propio' | 'tercero';
  capacidad_kg?: number;
  estado_vehiculo: 'disponible' | 'en_ruta' | 'mantenimiento' | 'inactivo';
  es_activo: boolean;
}
```

### GuiaRemision
```typescript
interface GuiaRemision {
  guia_remision_id: string;
  serie: string;
  numero: string;
  fecha_emision: string;
  fecha_traslado: string;
  tipo_guia: 'remitente' | 'transportista';
  motivo_traslado: 'venta' | 'compra' | 'transferencia' | 'consignacion' | 'devolucion';
  remitente_razon_social: string;
  destinatario_razon_social: string;
  punto_partida: string;
  punto_llegada: string;
  modalidad_transporte: 'publico' | 'privado';
  vehiculo_id?: string;
  estado: 'borrador' | 'emitida' | 'en_transito' | 'entregada' | 'anulada';
}
```

### Despacho
```typescript
interface Despacho {
  despacho_id: string;
  numero_despacho: string;
  fecha_programada: string;
  ruta_id?: string;
  vehiculo_id?: string;
  conductor_nombre?: string;
  fecha_salida_real?: string;
  fecha_retorno?: string;
  km_inicial?: number;
  km_final?: number;
  total_guias: number;
  estado: 'planificado' | 'en_ruta' | 'completado' | 'cancelado';
}
```

---

## ⚠️ Códigos de Error

| Código | Descripción |
|--------|-------------|
| `400` | Bad Request - Datos inválidos |
| `401` | Unauthorized - Token inválido |
| `404` | Not Found - Recurso no encontrado |
| `422` | Unprocessable Entity - Error de validación |
| `500` | Internal Server Error |

---

## 🗺️ Rutas SPA Recomendadas

```
/log
  /transportistas
    /listado
    /nuevo
    /:id
    /:id/editar
  /vehiculos
    /listado
    /nuevo
    /:id
    /:id/editar
  /rutas
    /listado
    /nuevo
    /:id
    /:id/editar
  /guias-remision
    /listado
    /nuevo
    /:id
    /:id/editar
    /:id/detalles
  /despachos
    /listado
    /nuevo
    /:id
    /:id/editar
    /:id/guias
```

---

## 🚀 Flujo de Implementación Recomendado

### Fase 1: Configuración Base
1. **Crear Transportistas**
   - Registrar empresas transportistas (propias o terceros)
   - Configurar tarifas y datos de contacto

2. **Registrar Vehículos**
   - Registrar flota propia o de transportistas
   - Configurar documentos (SOAT, revisión técnica)
   - Asignar conductores habituales

3. **Definir Rutas**
   - Crear rutas frecuentes origen-destino
   - Configurar distancias, tiempos y costos

### Fase 2: Operaciones de Transporte
1. **Crear Guías de Remisión**
   - Emitir guías para ventas/compras/transferencias
   - Vincular a pedidos de venta o movimientos de inventario
   - Agregar productos y cantidades en detalles

2. **Planificar Despachos**
   - Crear despachos agrupando múltiples guías
   - Asignar ruta, vehículo y conductor
   - Programar fecha y hora de salida

3. **Ejecutar Despachos**
   - Registrar salida real (fecha, km inicial)
   - Actualizar estado de guías durante el recorrido
   - Registrar entregas (fecha, receptor, observaciones)
   - Registrar retorno (fecha, km final, costos)

### Fase 3: Seguimiento y Control
1. **Monitoreo en Tiempo Real**
   - Seguimiento GPS de vehículos (si aplica)
   - Actualización de estados de guías
   - Registro de incidencias

2. **Cierre de Despacho**
   - Verificar todas las guías entregadas
   - Registrar costos finales
   - Marcar despacho como completado

---

## 📌 Notas Importantes

1. **Multi-tenancy:** Todos los endpoints filtran automáticamente por `cliente_id` del token.

2. **Estados de Guía:**
   - `'borrador'`: En creación, aún no emitida
   - `'emitida'`: Guía emitida, lista para traslado
   - `'en_transito'`: En camino al destino
   - `'entregada'`: Entregada al destinatario
   - `'anulada'`: Anulada (con motivo)

3. **Estados de Despacho:**
   - `'planificado'`: Creado pero aún no iniciado
   - `'en_ruta'`: En ejecución
   - `'completado'`: Finalizado exitosamente
   - `'cancelado'`: Cancelado

4. **Estados de Vehículo:**
   - `'disponible'`: Listo para usar
   - `'en_ruta'`: En viaje
   - `'mantenimiento'`: En mantenimiento
   - `'inactivo'`: No disponible

5. **Guías de Remisión:**
   - Se vinculan a ventas (pedidos) o movimientos de inventario
   - Requieren documento sustento (factura, boleta, orden de compra)
   - Pueden tener códigos SUNAT (hash, QR) para integración electrónica

6. **Despachos:**
   - Agrupan múltiples guías para optimizar rutas
   - Permiten control de costos (combustible, peajes, otros)
   - Registran km recorrido para mantenimiento de vehículos

7. **Integración con SLS:**
   - Las guías de remisión pueden vincularse a pedidos de venta
   - Los despachos agrupan guías de múltiples pedidos

8. **Integración con INV_BILL:**
   - Las guías de remisión pueden vincularse a comprobantes electrónicos
   - Campo `guia_remision_id` en comprobantes

---

**Fin de la documentación**
