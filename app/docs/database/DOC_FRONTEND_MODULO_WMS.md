# Documentación Frontend — Módulo WMS (Warehouse Management System)

**Versión:** 1.0  
**Fecha:** 2026-02-18  
**Módulo:** WMS - Gestión de Almacenes ERP

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
/api/v1/wms
```

### Dependencias
- **Módulo ORG:** Requiere tener empresas configuradas.
- **Módulo INV:** Requiere tener almacenes, productos y unidades de medida configurados.
- **Orden recomendado:** Configurar primero ORG e INV, luego WMS.

---

## 🔐 Autenticación

Todos los endpoints requieren autenticación mediante JWT token en el header:

```http
Authorization: Bearer <token>
```

El `cliente_id` se obtiene automáticamente del token, **nunca debe enviarse en el body**.

---

## 📡 Endpoints

### 1. Zonas de Almacén

#### Listar Zonas de Almacén
```http
GET /api/v1/wms/zonas
```

**Query Parameters:**
- `almacen_id` (UUID, opcional): Filtrar por almacén
- `tipo_zona` (string, opcional): Filtrar por tipo ('recepcion', 'almacenaje', 'picking', 'despacho', 'cuarentena', 'merma')
- `solo_activos` (boolean, default: true): Solo zonas activas
- `buscar` (string, opcional): Búsqueda por nombre o código

**Response:** `200 OK`
```json
[
  {
    "zona_id": "uuid",
    "cliente_id": "uuid",
    "almacen_id": "uuid",
    "codigo": "REC-01",
    "nombre": "Zona de Recepción",
    "descripcion": "Zona para recepción de mercadería",
    "tipo_zona": "recepcion",
    "temperatura_min": null,
    "temperatura_max": null,
    "requiere_control_temperatura": false,
    "capacidad_m3": 1000.00,
    "capacidad_kg": 5000.00,
    "es_activo": true,
    "fecha_creacion": "2026-02-18T10:00:00",
    "usuario_creacion_id": "uuid"
  }
]
```

#### Crear Zona
```http
POST /api/v1/wms/zonas
```

**Request Body:**
```json
{
  "almacen_id": "uuid",
  "codigo": "REC-01",
  "nombre": "Zona de Recepción",
  "descripcion": "Zona para recepción de mercadería",
  "tipo_zona": "recepcion",
  "capacidad_m3": 1000.00,
  "capacidad_kg": 5000.00,
  "es_activo": true
}
```

**Response:** `201 Created`
```json
{
  "zona_id": "uuid",
  "cliente_id": "uuid",
  "almacen_id": "uuid",
  "codigo": "REC-01",
  "nombre": "Zona de Recepción",
  ...
}
```

#### Actualizar Zona
```http
PUT /api/v1/wms/zonas/{zona_id}
```

**Request Body:** (campos opcionales)
```json
{
  "nombre": "Zona de Recepción Actualizada",
  "capacidad_m3": 1200.00
}
```

---

### 2. Ubicaciones

#### Listar Ubicaciones
```http
GET /api/v1/wms/ubicaciones
```

**Query Parameters:**
- `almacen_id` (UUID, opcional): Filtrar por almacén
- `zona_id` (UUID, opcional): Filtrar por zona
- `tipo_ubicacion` (string, opcional): Filtrar por tipo ('rack', 'piso', 'estanteria', 'caja', 'pallet')
- `estado_ubicacion` (string, opcional): Filtrar por estado ('disponible', 'ocupada', 'bloqueada', 'mantenimiento')
- `es_ubicacion_picking` (boolean, opcional): Solo ubicaciones de picking
- `solo_activos` (boolean, default: true): Solo ubicaciones activas
- `buscar` (string, opcional): Búsqueda por código, nombre o pasillo

**Response:** `200 OK`
```json
[
  {
    "ubicacion_id": "uuid",
    "cliente_id": "uuid",
    "almacen_id": "uuid",
    "zona_id": "uuid",
    "codigo_ubicacion": "A-01-03",
    "pasillo": "A",
    "rack": "01",
    "nivel": 3,
    "posicion": null,
    "nombre": "Rack A-01 Nivel 3",
    "tipo_ubicacion": "rack",
    "capacidad_kg": 500.00,
    "capacidad_m3": 2.50,
    "capacidad_pallets": 1,
    "alto_cm": 200.00,
    "ancho_cm": 100.00,
    "profundidad_cm": 120.00,
    "permite_multiples_productos": true,
    "permite_multiples_lotes": true,
    "es_ubicacion_picking": false,
    "estado_ubicacion": "disponible",
    "es_activo": true,
    "fecha_creacion": "2026-02-18T10:00:00",
    "usuario_creacion_id": "uuid"
  }
]
```

#### Crear Ubicación
```http
POST /api/v1/wms/ubicaciones
```

**Request Body:**
```json
{
  "almacen_id": "uuid",
  "zona_id": "uuid",
  "codigo_ubicacion": "A-01-03",
  "pasillo": "A",
  "rack": "01",
  "nivel": 3,
  "tipo_ubicacion": "rack",
  "capacidad_kg": 500.00,
  "capacidad_m3": 2.50,
  "es_activo": true
}
```

---

### 3. Stock por Ubicación

#### Listar Stock por Ubicación
```http
GET /api/v1/wms/stock-ubicacion
```

**Query Parameters:**
- `almacen_id` (UUID, opcional): Filtrar por almacén
- `ubicacion_id` (UUID, opcional): Filtrar por ubicación
- `producto_id` (UUID, opcional): Filtrar por producto
- `estado_stock` (string, opcional): Filtrar por estado ('disponible', 'reservado', 'bloqueado', 'cuarentena')
- `lote` (string, opcional): Filtrar por lote

**Response:** `200 OK`
```json
[
  {
    "stock_ubicacion_id": "uuid",
    "cliente_id": "uuid",
    "almacen_id": "uuid",
    "ubicacion_id": "uuid",
    "producto_id": "uuid",
    "cantidad": 50.00,
    "unidad_medida_id": "uuid",
    "lote": "LOT-2026-001",
    "numero_serie": null,
    "fecha_vencimiento": "2027-12-31",
    "estado_stock": "disponible",
    "motivo_bloqueo": null,
    "fecha_ingreso": "2026-02-18T10:00:00",
    "fecha_actualizacion": null
  }
]
```

#### Crear Stock por Ubicación
```http
POST /api/v1/wms/stock-ubicacion
```

**Request Body:**
```json
{
  "almacen_id": "uuid",
  "ubicacion_id": "uuid",
  "producto_id": "uuid",
  "cantidad": 50.00,
  "unidad_medida_id": "uuid",
  "lote": "LOT-2026-001",
  "fecha_vencimiento": "2027-12-31",
  "estado_stock": "disponible"
}
```

---

### 4. Tareas

#### Listar Tareas
```http
GET /api/v1/wms/tareas
```

**Query Parameters:**
- `almacen_id` (UUID, opcional): Filtrar por almacén
- `tipo_tarea` (string, opcional): Filtrar por tipo ('picking', 'putaway', 'reabastecimiento', 'conteo', 'reubicacion')
- `estado` (string, opcional): Filtrar por estado ('pendiente', 'asignada', 'en_proceso', 'completada', 'cancelada')
- `asignado_usuario_id` (UUID, opcional): Filtrar por usuario asignado
- `producto_id` (UUID, opcional): Filtrar por producto
- `buscar` (string, opcional): Búsqueda por número o instrucciones

**Response:** `200 OK`
```json
[
  {
    "tarea_id": "uuid",
    "cliente_id": "uuid",
    "almacen_id": "uuid",
    "numero_tarea": "TAR-2026-001",
    "tipo_tarea": "picking",
    "prioridad": 2,
    "ubicacion_origen_id": "uuid",
    "ubicacion_destino_id": null,
    "producto_id": "uuid",
    "cantidad_planeada": 10.00,
    "cantidad_completada": 0.00,
    "unidad_medida_id": "uuid",
    "documento_referencia_tipo": "orden_venta",
    "documento_referencia_id": "uuid",
    "asignado_usuario_id": "uuid",
    "asignado_nombre": "Juan Pérez",
    "fecha_asignacion": "2026-02-18T10:00:00",
    "estado": "asignada",
    "fecha_inicio": null,
    "fecha_completado": null,
    "instrucciones": "Recoger producto de ubicación A-01-03",
    "observaciones": null,
    "fecha_creacion": "2026-02-18T10:00:00",
    "usuario_creacion_id": "uuid"
  }
]
```

#### Crear Tarea
```http
POST /api/v1/wms/tareas
```

**Request Body:**
```json
{
  "almacen_id": "uuid",
  "numero_tarea": "TAR-2026-001",
  "tipo_tarea": "picking",
  "prioridad": 2,
  "ubicacion_origen_id": "uuid",
  "producto_id": "uuid",
  "cantidad_planeada": 10.00,
  "unidad_medida_id": "uuid",
  "documento_referencia_tipo": "orden_venta",
  "documento_referencia_id": "uuid",
  "estado": "pendiente",
  "instrucciones": "Recoger producto de ubicación A-01-03"
}
```

---

## 📝 Schemas TypeScript

### ZonaAlmacen
```typescript
interface ZonaAlmacenCreate {
  almacen_id: string;
  codigo: string;
  nombre: string;
  descripcion?: string;
  tipo_zona: 'recepcion' | 'almacenaje' | 'picking' | 'despacho' | 'cuarentena' | 'merma';
  temperatura_min?: number;
  temperatura_max?: number;
  requiere_control_temperatura?: boolean;
  capacidad_m3?: number;
  capacidad_kg?: number;
  es_activo?: boolean;
}

interface ZonaAlmacenRead {
  zona_id: string;
  cliente_id: string;
  almacen_id: string;
  codigo: string;
  nombre: string;
  descripcion?: string;
  tipo_zona: string;
  temperatura_min?: number;
  temperatura_max?: number;
  requiere_control_temperatura?: boolean;
  capacidad_m3?: number;
  capacidad_kg?: number;
  es_activo: boolean;
  fecha_creacion: string;
  usuario_creacion_id?: string;
}
```

### Ubicacion
```typescript
interface UbicacionCreate {
  almacen_id: string;
  zona_id?: string;
  codigo_ubicacion: string;
  pasillo?: string;
  rack?: string;
  nivel?: number;
  posicion?: string;
  nombre?: string;
  tipo_ubicacion?: 'rack' | 'piso' | 'estanteria' | 'caja' | 'pallet';
  capacidad_kg?: number;
  capacidad_m3?: number;
  capacidad_pallets?: number;
  alto_cm?: number;
  ancho_cm?: number;
  profundidad_cm?: number;
  permite_multiples_productos?: boolean;
  permite_multiples_lotes?: boolean;
  es_ubicacion_picking?: boolean;
  estado_ubicacion?: 'disponible' | 'ocupada' | 'bloqueada' | 'mantenimiento';
  es_activo?: boolean;
}

interface UbicacionRead {
  ubicacion_id: string;
  cliente_id: string;
  almacen_id: string;
  zona_id?: string;
  codigo_ubicacion: string;
  pasillo?: string;
  rack?: string;
  nivel?: number;
  posicion?: string;
  nombre?: string;
  tipo_ubicacion?: string;
  capacidad_kg?: number;
  capacidad_m3?: number;
  capacidad_pallets?: number;
  alto_cm?: number;
  ancho_cm?: number;
  profundidad_cm?: number;
  permite_multiples_productos?: boolean;
  permite_multiples_lotes?: boolean;
  es_ubicacion_picking?: boolean;
  estado_ubicacion?: string;
  es_activo: boolean;
  fecha_creacion: string;
  usuario_creacion_id?: string;
}
```

### StockUbicacion
```typescript
interface StockUbicacionCreate {
  almacen_id: string;
  ubicacion_id: string;
  producto_id: string;
  cantidad: number;
  unidad_medida_id: string;
  lote?: string;
  numero_serie?: string;
  fecha_vencimiento?: string;
  estado_stock?: 'disponible' | 'reservado' | 'bloqueado' | 'cuarentena';
  motivo_bloqueo?: string;
}

interface StockUbicacionRead {
  stock_ubicacion_id: string;
  cliente_id: string;
  almacen_id: string;
  ubicacion_id: string;
  producto_id: string;
  cantidad: number;
  unidad_medida_id: string;
  lote?: string;
  numero_serie?: string;
  fecha_vencimiento?: string;
  estado_stock?: string;
  motivo_bloqueo?: string;
  fecha_ingreso: string;
  fecha_actualizacion?: string;
}
```

### Tarea
```typescript
interface TareaCreate {
  almacen_id: string;
  numero_tarea: string;
  tipo_tarea: 'picking' | 'putaway' | 'reabastecimiento' | 'conteo' | 'reubicacion';
  prioridad?: number; // 1=Urgente, 2=Alta, 3=Normal, 4=Baja
  ubicacion_origen_id?: string;
  ubicacion_destino_id?: string;
  producto_id?: string;
  cantidad_planeada?: number;
  cantidad_completada?: number;
  unidad_medida_id?: string;
  documento_referencia_tipo?: string;
  documento_referencia_id?: string;
  asignado_usuario_id?: string;
  asignado_nombre?: string;
  estado?: 'pendiente' | 'asignada' | 'en_proceso' | 'completada' | 'cancelada';
  instrucciones?: string;
  observaciones?: string;
}

interface TareaRead {
  tarea_id: string;
  cliente_id: string;
  almacen_id: string;
  numero_tarea: string;
  tipo_tarea: string;
  prioridad?: number;
  ubicacion_origen_id?: string;
  ubicacion_destino_id?: string;
  producto_id?: string;
  cantidad_planeada?: number;
  cantidad_completada?: number;
  unidad_medida_id?: string;
  documento_referencia_tipo?: string;
  documento_referencia_id?: string;
  asignado_usuario_id?: string;
  asignado_nombre?: string;
  fecha_asignacion?: string;
  estado: string;
  fecha_inicio?: string;
  fecha_completado?: string;
  instrucciones?: string;
  observaciones?: string;
  fecha_creacion: string;
  usuario_creacion_id?: string;
}
```

---

## ⚠️ Códigos de Error

| Código | Descripción |
|--------|-------------|
| `401` | No autenticado |
| `403` | Sin permisos |
| `404` | Recurso no encontrado |
| `422` | Error de validación |
| `500` | Error interno del servidor |

**Ejemplo de error:**
```json
{
  "detail": "Zona de almacén {uuid} no encontrada"
}
```

---

## 🗺️ Rutas SPA Recomendadas

```
/wms
  /zonas
    /list                    # Lista de zonas
    /create                  # Crear zona
    /:id/edit                # Editar zona
  /ubicaciones
    /list                    # Lista de ubicaciones
    /create                  # Crear ubicación
    /:id/edit                # Editar ubicación
  /stock-ubicacion
    /list                    # Lista de stock por ubicación
    /create                  # Crear stock por ubicación
    /:id/edit                # Editar stock por ubicación
  /tareas
    /list                    # Lista de tareas
    /create                  # Crear tarea
    /:id/edit                # Editar tarea
    /:id/asignar             # Asignar tarea a usuario
```

---

## 🔄 Flujo de Implementación Recomendado

### 1. Configuración Inicial
1. **Zonas de Almacén:** Crear zonas dentro de cada almacén (recepción, picking, despacho, etc.)
2. **Ubicaciones:** Definir ubicaciones físicas (pasillo-rack-nivel) dentro de cada zona

### 2. Operaciones Diarias
1. **Putaway (Almacenar):** Al recibir mercadería (PUR), crear tarea de putaway y registrar stock por ubicación
2. **Stock por Ubicación:** Mantener registro actualizado de qué productos están en cada ubicación
3. **Picking (Recoger):** Al despachar (SLS), crear tarea de picking y actualizar stock por ubicación
4. **Reabastecimiento:** Mover productos de zonas de almacenaje a zonas de picking cuando sea necesario

### 3. Gestión de Tareas
1. **Crear Tareas:** Automáticamente desde módulos operativos (SLS, PUR) o manualmente
2. **Asignar Tareas:** Asignar tareas a operadores de almacén
3. **Seguimiento:** Actualizar estado y cantidades completadas conforme se ejecutan las tareas
4. **Completar:** Marcar tareas como completadas cuando se terminen

### 4. Consultas y Reportes
1. **Stock por Ubicación:** Consultar qué productos hay en cada ubicación específica
2. **Tareas Pendientes:** Ver tareas pendientes o en proceso por almacén/usuario
3. **Trazabilidad:** Rastrear movimientos de productos entre ubicaciones mediante tareas

---

## 📌 Notas Importantes

1. **Multi-tenancy:** Todos los datos están filtrados automáticamente por `cliente_id` del token. No enviar `cliente_id` en el body.

2. **Dependencias:** WMS requiere que ORG e INV estén configurados previamente (almacenes, productos, unidades de medida).

3. **Integración con INV:** WMS extiende el módulo INV con control granular de ubicaciones. El stock por ubicación complementa el stock general de INV.

4. **Tareas Automáticas:** Las tareas pueden generarse automáticamente desde otros módulos (ej: picking desde órdenes de venta, putaway desde recepciones de compra).

5. **Estados:** Usar estados consistentes para ubicaciones ('disponible', 'ocupada', 'bloqueada', 'mantenimiento') y tareas ('pendiente', 'asignada', 'en_proceso', 'completada', 'cancelada').

6. **Prioridades:** Las tareas tienen prioridad numérica (1=Urgente, 2=Alta, 3=Normal, 4=Baja). Ordenar listados por prioridad y fecha de creación.

---

**Fin de la documentación del módulo WMS**
