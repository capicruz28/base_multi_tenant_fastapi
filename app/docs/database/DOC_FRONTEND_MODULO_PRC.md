# Documentación Frontend — Módulo PRC (Gestión de Precios y Promociones)

**Versión:** 1.0  
**Fecha:** 2026-02-18  
**Módulo:** PRC - Gestión de Precios y Promociones ERP

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
/api/v1/prc
```

### Dependencias
- **Módulo ORG:** Requiere tener empresas configuradas.
- **Módulo INV:** Requiere tener productos, categorías y unidades de medida configuradas.
- **Módulo SLS:** Opcional, para asignar listas de precios a clientes.
- **Orden recomendado:** Configurar primero ORG e INV, luego PRC.

---

## 🔐 Autenticación

Todos los endpoints requieren autenticación mediante JWT token en el header:

```http
Authorization: Bearer <token>
```

El `cliente_id` se obtiene automáticamente del token, **nunca debe enviarse en el body**.

---

## 📡 Endpoints

### 1. Listas de Precio

#### Listar Listas de Precio
```http
GET /api/v1/prc/listas-precio
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `tipo_lista` (string, opcional): Filtrar por tipo ('general', 'mayorista', 'minorista', 'distribuidor', 'corporativo')
- `solo_activos` (boolean, default: true): Solo listas activas
- `solo_vigentes` (boolean, default: false): Solo listas vigentes (fecha actual dentro del rango)
- `buscar` (string, opcional): Búsqueda por nombre o código

**Response:** `200 OK`
```json
[
  {
    "lista_precio_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "codigo_lista": "LP001",
    "nombre": "Lista Mayorista",
    "descripcion": "Lista de precios para clientes mayoristas",
    "tipo_lista": "mayorista",
    "moneda": "PEN",
    "fecha_vigencia_desde": "2025-01-01",
    "fecha_vigencia_hasta": "2025-12-31",
    "incluye_igv": true,
    "permite_descuentos": true,
    "descuento_maximo_porcentaje": 15.00,
    "es_lista_defecto": false,
    "es_activo": true,
    "observaciones": "Aplicable a clientes con compras mayores a S/ 10,000",
    "fecha_creacion": "2025-01-01T10:00:00",
    "fecha_actualizacion": null,
    "usuario_creacion_id": "uuid"
  }
]
```

#### Obtener Lista de Precio por ID
```http
GET /api/v1/prc/listas-precio/{lista_precio_id}
```

**Response:** `200 OK` (mismo schema que listar)

#### Crear Lista de Precio
```http
POST /api/v1/prc/listas-precio
```

**Request Body:**
```json
{
  "empresa_id": "uuid",
  "codigo_lista": "LP001",
  "nombre": "Lista Mayorista",
  "descripcion": "Lista de precios para clientes mayoristas",
  "tipo_lista": "mayorista",
  "moneda": "PEN",
  "fecha_vigencia_desde": "2025-01-01",
  "fecha_vigencia_hasta": "2025-12-31",
  "incluye_igv": true,
  "permite_descuentos": true,
  "descuento_maximo_porcentaje": 15.00,
  "es_lista_defecto": false,
  "es_activo": true,
  "observaciones": "Aplicable a clientes con compras mayores a S/ 10,000"
}
```

**Response:** `201 Created` (mismo schema que listar)

#### Actualizar Lista de Precio
```http
PUT /api/v1/prc/listas-precio/{lista_precio_id}
```

**Request Body:** (todos los campos opcionales)
```json
{
  "nombre": "Lista Mayorista Actualizada",
  "descuento_maximo_porcentaje": 20.00
}
```

**Response:** `200 OK` (mismo schema que listar)

---

### 2. Detalles de Lista de Precio

#### Listar Detalles de una Lista de Precio
```http
GET /api/v1/prc/listas-precio/{lista_precio_id}/detalles
```

**Query Parameters:**
- `producto_id` (UUID, opcional): Filtrar por producto
- `solo_activos` (boolean, default: true): Solo detalles activos

**Response:** `200 OK`
```json
[
  {
    "lista_precio_detalle_id": "uuid",
    "cliente_id": "uuid",
    "lista_precio_id": "uuid",
    "producto_id": "uuid",
    "precio_unitario": 150.00,
    "unidad_medida_id": "uuid",
    "cantidad_minima": 1.00,
    "cantidad_maxima": 10.00,
    "descuento_maximo_porcentaje": 5.00,
    "fecha_vigencia_desde": null,
    "fecha_vigencia_hasta": null,
    "es_activo": true,
    "fecha_creacion": "2025-01-01T10:00:00",
    "fecha_actualizacion": null
  }
]
```

#### Crear Detalle de Lista de Precio
```http
POST /api/v1/prc/listas-precio/{lista_precio_id}/detalles
```

**Request Body:**
```json
{
  "producto_id": "uuid",
  "precio_unitario": 150.00,
  "unidad_medida_id": "uuid",
  "cantidad_minima": 1.00,
  "cantidad_maxima": 10.00,
  "descuento_maximo_porcentaje": 5.00,
  "fecha_vigencia_desde": null,
  "fecha_vigencia_hasta": null,
  "es_activo": true
}
```

**Nota:** El `lista_precio_id` se toma del path, no es necesario enviarlo en el body.

**Response:** `201 Created` (mismo schema que listar)

#### Obtener Detalle por ID
```http
GET /api/v1/prc/listas-precio/detalles/{lista_precio_detalle_id}
```

**Response:** `200 OK` (mismo schema que listar)

#### Actualizar Detalle
```http
PUT /api/v1/prc/listas-precio/detalles/{lista_precio_detalle_id}
```

**Request Body:** (todos los campos opcionales)
```json
{
  "precio_unitario": 160.00,
  "cantidad_maxima": 20.00
}
```

**Response:** `200 OK` (mismo schema que listar)

---

### 3. Promociones

#### Listar Promociones
```http
GET /api/v1/prc/promociones
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `tipo_promocion` (string, opcional): Filtrar por tipo ('descuento_porcentaje', 'descuento_monto', '2x1', '3x2', 'producto_gratis')
- `aplica_a` (string, opcional): Filtrar por aplicabilidad ('producto', 'categoria', 'marca', 'toda_venta')
- `producto_id` (UUID, opcional): Filtrar por producto
- `categoria_id` (UUID, opcional): Filtrar por categoría
- `solo_activos` (boolean, default: true): Solo promociones activas
- `solo_vigentes` (boolean, default: false): Solo promociones vigentes (fecha actual dentro del rango)
- `buscar` (string, opcional): Búsqueda por nombre o código

**Response:** `200 OK`
```json
[
  {
    "promocion_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "codigo_promocion": "PROMO001",
    "nombre": "Descuento 20% en Categoría A",
    "descripcion": "Descuento del 20% en todos los productos de la categoría A",
    "tipo_promocion": "descuento_porcentaje",
    "aplica_a": "categoria",
    "producto_id": null,
    "categoria_id": "uuid",
    "marca": null,
    "descuento_porcentaje": 20.00,
    "descuento_monto": null,
    "reglas_aplicacion": "{\"cantidad_minima\": 3}",
    "fecha_inicio": "2025-02-01",
    "fecha_fin": "2025-02-28",
    "cantidad_maxima_usos": 1000,
    "cantidad_usos_actuales": 150,
    "monto_maximo_descuento": null,
    "es_combinable": false,
    "aplica_canal_venta": "[\"tienda\", \"online\"]",
    "es_activo": true,
    "requiere_codigo_cupon": false,
    "codigo_cupon": null,
    "observaciones": "Promoción válida solo en febrero",
    "fecha_creacion": "2025-01-15T10:00:00",
    "usuario_creacion_id": "uuid"
  }
]
```

#### Obtener Promoción por ID
```http
GET /api/v1/prc/promociones/{promocion_id}
```

**Response:** `200 OK` (mismo schema que listar)

#### Crear Promoción
```http
POST /api/v1/prc/promociones
```

**Request Body:**
```json
{
  "empresa_id": "uuid",
  "codigo_promocion": "PROMO001",
  "nombre": "Descuento 20% en Categoría A",
  "descripcion": "Descuento del 20% en todos los productos de la categoría A",
  "tipo_promocion": "descuento_porcentaje",
  "aplica_a": "categoria",
  "categoria_id": "uuid",
  "descuento_porcentaje": 20.00,
  "reglas_aplicacion": "{\"cantidad_minima\": 3}",
  "fecha_inicio": "2025-02-01",
  "fecha_fin": "2025-02-28",
  "cantidad_maxima_usos": 1000,
  "es_combinable": false,
  "aplica_canal_venta": "[\"tienda\", \"online\"]",
  "es_activo": true,
  "requiere_codigo_cupon": false,
  "observaciones": "Promoción válida solo en febrero"
}
```

**Response:** `201 Created` (mismo schema que listar)

#### Actualizar Promoción
```http
PUT /api/v1/prc/promociones/{promocion_id}
```

**Request Body:** (todos los campos opcionales)
```json
{
  "cantidad_usos_actuales": 200,
  "es_activo": true
}
```

**Response:** `200 OK` (mismo schema que listar)

---

## 📝 Schemas TypeScript

### ListaPrecio
```typescript
interface ListaPrecio {
  lista_precio_id: string;
  cliente_id: string;
  empresa_id: string;
  codigo_lista: string;
  nombre: string;
  descripcion?: string;
  tipo_lista: 'general' | 'mayorista' | 'minorista' | 'distribuidor' | 'corporativo';
  moneda: string;
  fecha_vigencia_desde: string;
  fecha_vigencia_hasta?: string;
  incluye_igv: boolean;
  permite_descuentos: boolean;
  descuento_maximo_porcentaje: number;
  es_lista_defecto: boolean;
  es_activo: boolean;
  observaciones?: string;
  fecha_creacion: string;
  fecha_actualizacion?: string;
  usuario_creacion_id?: string;
}
```

### ListaPrecioDetalle
```typescript
interface ListaPrecioDetalle {
  lista_precio_detalle_id: string;
  cliente_id: string;
  lista_precio_id: string;
  producto_id: string;
  precio_unitario: number;
  unidad_medida_id: string;
  cantidad_minima: number;
  cantidad_maxima?: number;
  descuento_maximo_porcentaje?: number;
  fecha_vigencia_desde?: string;
  fecha_vigencia_hasta?: string;
  es_activo: boolean;
  fecha_creacion: string;
  fecha_actualizacion?: string;
}
```

### Promocion
```typescript
interface Promocion {
  promocion_id: string;
  cliente_id: string;
  empresa_id: string;
  codigo_promocion: string;
  nombre: string;
  descripcion?: string;
  tipo_promocion: 'descuento_porcentaje' | 'descuento_monto' | '2x1' | '3x2' | 'producto_gratis';
  aplica_a: 'producto' | 'categoria' | 'marca' | 'toda_venta';
  producto_id?: string;
  categoria_id?: string;
  marca?: string;
  descuento_porcentaje?: number;
  descuento_monto?: number;
  reglas_aplicacion?: string; // JSON string
  fecha_inicio: string;
  fecha_fin: string;
  cantidad_maxima_usos?: number;
  cantidad_usos_actuales: number;
  monto_maximo_descuento?: number;
  es_combinable: boolean;
  aplica_canal_venta?: string; // JSON string
  es_activo: boolean;
  requiere_codigo_cupon: boolean;
  codigo_cupon?: string;
  observaciones?: string;
  fecha_creacion: string;
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
/prc
  /listas-precio
    /listado          # Lista de listas de precio
    /nuevo            # Formulario crear lista
    /:id              # Detalle lista
    /:id/editar       # Formulario editar lista
    /:id/detalles     # Detalles de la lista (precios por producto)
    /:id/detalles/nuevo  # Agregar producto a lista
  /promociones
    /listado          # Lista de promociones
    /nuevo            # Formulario crear promoción
    /:id              # Detalle promoción
    /:id/editar       # Formulario editar promoción
```

---

## 🚀 Flujo de Implementación Recomendado

### Fase 1: Configuración de Listas de Precio
1. **Crear Listas de Precio**
   - Crear listas por tipo de cliente (mayorista, minorista, distribuidor)
   - Configurar vigencia y descuentos máximos
   - Marcar lista por defecto si aplica

2. **Agregar Precios por Producto**
   - Para cada lista, agregar productos con sus precios
   - Configurar precios escalonados por cantidad (opcional)
   - Configurar descuentos máximos por producto

### Fase 2: Gestión de Promociones
1. **Crear Promociones**
   - Definir tipo de promoción (descuento porcentaje, monto, 2x1, etc.)
   - Configurar aplicabilidad (producto, categoría, marca, toda venta)
   - Establecer vigencia y límites de uso

2. **Validar Promociones**
   - Verificar que las promociones estén vigentes
   - Validar límites de uso antes de aplicar
   - Verificar combinabilidad con otras promociones

### Fase 3: Integración con Otros Módulos
1. **Con SLS (Ventas):**
   - Asignar lista de precios a cliente
   - Aplicar precios de la lista al crear cotización/pedido
   - Aplicar promociones vigentes automáticamente

2. **Con POS:**
   - Usar lista de precios del punto de venta
   - Aplicar promociones según canal de venta
   - Validar códigos de cupón si aplica

---

## 📌 Notas Importantes

1. **Multi-tenancy:** Todos los endpoints filtran automáticamente por `cliente_id` del token. No enviar `cliente_id` en el body.

2. **Dependencias:**
   - Requiere módulo ORG (empresas)
   - Requiere módulo INV (productos, categorías, unidades de medida)
   - Opcional módulo SLS (para asignar listas a clientes)

3. **Tipos de Lista:**
   - `'general'`: Lista estándar
   - `'mayorista'`: Para clientes mayoristas
   - `'minorista'`: Para clientes minoristas
   - `'distribuidor'`: Para distribuidores
   - `'corporativo'`: Para clientes corporativos

4. **Tipos de Promoción:**
   - `'descuento_porcentaje'`: Descuento por porcentaje (ej: 20%)
   - `'descuento_monto'`: Descuento por monto fijo (ej: S/ 50)
   - `'2x1'`: Lleva 2 paga 1
   - `'3x2'`: Lleva 3 paga 2
   - `'producto_gratis'`: Producto gratis al cumplir condiciones

5. **Aplicabilidad de Promociones:**
   - `'producto'`: Aplica a un producto específico
   - `'categoria'`: Aplica a todos los productos de una categoría
   - `'marca'`: Aplica a todos los productos de una marca
   - `'toda_venta'`: Aplica a toda la venta (descuento global)

6. **Precios Escalonados:**
   - Los detalles de lista de precio pueden tener `cantidad_minima` y `cantidad_maxima`
   - Permite definir diferentes precios según la cantidad comprada
   - Ejemplo: 1-10 unidades = S/ 100, 11-50 unidades = S/ 90, 51+ unidades = S/ 80

7. **Vigencia:**
   - Las listas y promociones tienen fechas de vigencia
   - Usar `solo_vigentes=true` para filtrar solo las vigentes en la fecha actual
   - Los detalles de lista pueden tener vigencia independiente de la lista

8. **Reglas de Aplicación (JSON):**
   - El campo `reglas_aplicacion` almacena JSON con reglas complejas
   - Ejemplo: `{"cantidad_minima": 3, "producto_gratis_id": "uuid"}`
   - El frontend debe parsear y validar estas reglas

9. **Canales de Venta (JSON):**
   - El campo `aplica_canal_venta` almacena JSON con canales
   - Ejemplo: `["tienda", "online", "telefono"]`
   - Validar que el canal de venta esté en la lista antes de aplicar promoción

10. **Lista por Defecto:**
    - Solo una lista puede ser marcada como `es_lista_defecto=true` por empresa
    - Se usa cuando un cliente no tiene lista asignada
    - Validar que solo haya una lista por defecto activa

---

**Fin de la documentación**
