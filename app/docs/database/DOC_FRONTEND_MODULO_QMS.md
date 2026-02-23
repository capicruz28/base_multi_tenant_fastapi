# Documentación Frontend — Módulo QMS (Quality Management System)

**Versión:** 1.0  
**Fecha:** 2026-02-18  
**Módulo:** QMS - Control de Calidad ERP

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
/api/v1/qms
```

### Dependencias
- **Módulo ORG:** Requiere tener empresas configuradas.
- **Módulo INV:** Requiere tener productos, categorías, unidades de medida y almacenes configurados.
- **Orden recomendado:** Configurar primero ORG e INV, luego QMS.

---

## 🔐 Autenticación

Todos los endpoints requieren autenticación mediante JWT token en el header:

```http
Authorization: Bearer <token>
```

El `cliente_id` se obtiene automáticamente del token, **nunca debe enviarse en el body**.

---

## 📡 Endpoints

### 1. Parámetros de Calidad

#### Listar Parámetros de Calidad
```http
GET /api/v1/qms/parametros-calidad
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `tipo_parametro` (string, opcional): Filtrar por tipo ('cuantitativo', 'cualitativo', 'pasa_no_pasa')
- `solo_activos` (boolean, default: true): Solo parámetros activos
- `buscar` (string, opcional): Búsqueda por nombre o código

**Response:** `200 OK`
```json
[
  {
    "parametro_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "codigo": "PESO",
    "nombre": "Peso",
    "descripcion": "Peso del producto en kg",
    "tipo_parametro": "cuantitativo",
    "unidad_medida_id": "uuid",
    "valor_minimo": 0.5,
    "valor_maximo": 1.5,
    "valor_objetivo": 1.0,
    "opciones_permitidas": null,
    "metodo_inspeccion": "Usar balanza calibrada",
    "requiere_equipo": "Balanza",
    "es_activo": true,
    "fecha_creacion": "2026-02-18T10:00:00",
    "usuario_creacion_id": "uuid"
  }
]
```

#### Crear Parámetro
```http
POST /api/v1/qms/parametros-calidad
```

**Request Body:**
```json
{
  "empresa_id": "uuid",
  "codigo": "PESO",
  "nombre": "Peso",
  "tipo_parametro": "cuantitativo",
  "unidad_medida_id": "uuid",
  "valor_minimo": 0.5,
  "valor_maximo": 1.5,
  "valor_objetivo": 1.0,
  "metodo_inspeccion": "Usar balanza calibrada",
  "requiere_equipo": "Balanza"
}
```

---

### 2. Planes de Inspección

#### Listar Planes de Inspección
```http
GET /api/v1/qms/planes-inspeccion
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `producto_id` (UUID, opcional): Filtrar por producto
- `categoria_id` (UUID, opcional): Filtrar por categoría
- `tipo_inspeccion` (string, opcional): Filtrar por tipo ('recepcion', 'proceso', 'final', 'salida')
- `solo_activos` (boolean, default: true): Solo planes activos
- `buscar` (string, opcional): Búsqueda por nombre o código

**Response:** `200 OK`
```json
[
  {
    "plan_inspeccion_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "codigo": "PLAN-REC-001",
    "nombre": "Plan Inspección Recepción",
    "descripcion": "Plan para inspeccionar productos recibidos",
    "aplica_a": "producto",
    "producto_id": "uuid",
    "categoria_id": null,
    "tipo_inspeccion": "recepcion",
    "tipo_muestreo": "aleatorio",
    "porcentaje_muestreo": 10.00,
    "tabla_muestreo": "AQL",
    "nivel_aceptacion_criticos": 0.00,
    "nivel_aceptacion_mayores": 2.50,
    "nivel_aceptacion_menores": 4.00,
    "es_activo": true,
    "fecha_vigencia_desde": "2026-01-01",
    "fecha_vigencia_hasta": null,
    "fecha_creacion": "2026-02-18T10:00:00",
    "usuario_creacion_id": "uuid"
  }
]
```

#### Crear Plan
```http
POST /api/v1/qms/planes-inspeccion
```

**Request Body:**
```json
{
  "empresa_id": "uuid",
  "codigo": "PLAN-REC-001",
  "nombre": "Plan Inspección Recepción",
  "aplica_a": "producto",
  "producto_id": "uuid",
  "tipo_inspeccion": "recepcion",
  "tipo_muestreo": "aleatorio",
  "porcentaje_muestreo": 10.00,
  "nivel_aceptacion_mayores": 2.50,
  "nivel_aceptacion_menores": 4.00
}
```

#### Listar Detalles de un Plan
```http
GET /api/v1/qms/planes-inspeccion/{plan_inspeccion_id}/detalles
```

**Response:** `200 OK`
```json
[
  {
    "plan_detalle_id": "uuid",
    "cliente_id": "uuid",
    "plan_inspeccion_id": "uuid",
    "parametro_calidad_id": "uuid",
    "orden": 1,
    "es_obligatorio": true,
    "criticidad": "mayor",
    "valor_minimo_plan": 0.5,
    "valor_maximo_plan": 1.5,
    "instrucciones_especificas": "Verificar peso con balanza calibrada",
    "fecha_creacion": "2026-02-18T10:00:00"
  }
]
```

#### Crear Detalle de Plan
```http
POST /api/v1/qms/planes-inspeccion/{plan_inspeccion_id}/detalles
```

**Request Body:**
```json
{
  "parametro_calidad_id": "uuid",
  "orden": 1,
  "es_obligatorio": true,
  "criticidad": "mayor",
  "valor_minimo_plan": 0.5,
  "valor_maximo_plan": 1.5,
  "instrucciones_especificas": "Verificar peso con balanza calibrada"
}
```

---

### 3. Inspecciones

#### Listar Inspecciones
```http
GET /api/v1/qms/inspecciones
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `producto_id` (UUID, opcional): Filtrar por producto
- `plan_inspeccion_id` (UUID, opcional): Filtrar por plan
- `resultado` (string, opcional): Filtrar por resultado ('aprobado', 'rechazado', 'aprobado_condicional', 'pendiente')
- `lote` (string, opcional): Filtrar por lote
- `fecha_desde` (datetime, opcional): Filtrar desde fecha
- `fecha_hasta` (datetime, opcional): Filtrar hasta fecha
- `buscar` (string, opcional): Búsqueda por número o observaciones

**Response:** `200 OK`
```json
[
  {
    "inspeccion_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "numero_inspeccion": "INS-2026-001",
    "fecha_inspeccion": "2026-02-18T10:00:00",
    "plan_inspeccion_id": "uuid",
    "producto_id": "uuid",
    "lote": "LOT-2026-001",
    "tipo_documento_origen": "orden_compra",
    "documento_origen_id": "uuid",
    "almacen_id": "uuid",
    "cantidad_total": 100.00,
    "cantidad_inspeccionada": 10.00,
    "unidad_medida_id": "uuid",
    "cantidad_aprobada": 9.50,
    "cantidad_rechazada": 0.50,
    "cantidad_observada": 0.00,
    "defectos_criticos": 0,
    "defectos_mayores": 1,
    "defectos_menores": 0,
    "resultado": "aprobado",
    "inspector_usuario_id": "uuid",
    "inspector_nombre": "Juan Pérez",
    "observaciones": "Producto aceptado con observaciones menores",
    "fecha_creacion": "2026-02-18T10:00:00"
  }
]
```

#### Crear Inspección
```http
POST /api/v1/qms/inspecciones
```

**Request Body:**
```json
{
  "empresa_id": "uuid",
  "numero_inspeccion": "INS-2026-001",
  "plan_inspeccion_id": "uuid",
  "producto_id": "uuid",
  "lote": "LOT-2026-001",
  "tipo_documento_origen": "orden_compra",
  "documento_origen_id": "uuid",
  "almacen_id": "uuid",
  "cantidad_total": 100.00,
  "cantidad_inspeccionada": 10.00,
  "unidad_medida_id": "uuid",
  "resultado": "pendiente",
  "inspector_usuario_id": "uuid",
  "inspector_nombre": "Juan Pérez"
}
```

#### Listar Detalles de una Inspección
```http
GET /api/v1/qms/inspecciones/{inspeccion_id}/detalles
```

**Response:** `200 OK`
```json
[
  {
    "inspeccion_detalle_id": "uuid",
    "cliente_id": "uuid",
    "inspeccion_id": "uuid",
    "parametro_calidad_id": "uuid",
    "valor_medido": 1.0,
    "valor_cualitativo": null,
    "resultado_pasa_no_pasa": null,
    "cumple_especificacion": true,
    "criticidad_defecto": null,
    "observaciones": "Peso dentro de especificación",
    "fecha_creacion": "2026-02-18T10:00:00"
  }
]
```

#### Crear Detalle de Inspección
```http
POST /api/v1/qms/inspecciones/{inspeccion_id}/detalles
```

**Request Body:**
```json
{
  "parametro_calidad_id": "uuid",
  "valor_medido": 1.0,
  "cumple_especificacion": true,
  "observaciones": "Peso dentro de especificación"
}
```

---

### 4. No Conformidades

#### Listar No Conformidades
```http
GET /api/v1/qms/no-conformidades
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `producto_id` (UUID, opcional): Filtrar por producto
- `origen` (string, opcional): Filtrar por origen ('inspeccion', 'reclamo_cliente', 'auditoria', 'proceso')
- `tipo_nc` (string, opcional): Filtrar por tipo ('critica', 'mayor', 'menor')
- `estado` (string, opcional): Filtrar por estado ('abierta', 'en_analisis', 'en_accion', 'cerrada', 'cancelada')
- `fecha_desde` (datetime, opcional): Filtrar desde fecha
- `fecha_hasta` (datetime, opcional): Filtrar hasta fecha
- `buscar` (string, opcional): Búsqueda por número o descripción

**Response:** `200 OK`
```json
[
  {
    "no_conformidad_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "numero_nc": "NC-2026-001",
    "fecha_deteccion": "2026-02-18T10:00:00",
    "origen": "inspeccion",
    "inspeccion_id": "uuid",
    "producto_id": "uuid",
    "lote": "LOT-2026-001",
    "cantidad_afectada": 0.50,
    "descripcion_nc": "Producto con peso fuera de especificación",
    "tipo_nc": "mayor",
    "area_responsable": "Calidad",
    "responsable_usuario_id": "uuid",
    "analisis_causa_raiz": "Análisis de causa raíz realizado",
    "causa_raiz_identificada": "Calibración incorrecta de balanza",
    "accion_inmediata": "Aislar producto afectado",
    "accion_correctiva": "Recalibrar balanza y capacitar operarios",
    "accion_preventiva": "Implementar verificación diaria de calibración",
    "responsable_accion_usuario_id": "uuid",
    "fecha_compromiso_cierre": "2026-02-25",
    "estado": "en_accion",
    "fecha_cierre": null,
    "fecha_creacion": "2026-02-18T10:00:00"
  }
]
```

#### Crear No Conformidad
```http
POST /api/v1/qms/no-conformidades
```

**Request Body:**
```json
{
  "empresa_id": "uuid",
  "numero_nc": "NC-2026-001",
  "origen": "inspeccion",
  "inspeccion_id": "uuid",
  "producto_id": "uuid",
  "lote": "LOT-2026-001",
  "cantidad_afectada": 0.50,
  "descripcion_nc": "Producto con peso fuera de especificación",
  "tipo_nc": "mayor",
  "area_responsable": "Calidad",
  "estado": "abierta"
}
```

---

## 📝 Schemas TypeScript

### ParametroCalidad
```typescript
interface ParametroCalidadCreate {
  empresa_id: string;
  codigo: string;
  nombre: string;
  descripcion?: string;
  tipo_parametro: 'cuantitativo' | 'cualitativo' | 'pasa_no_pasa';
  unidad_medida_id?: string;
  valor_minimo?: number;
  valor_maximo?: number;
  valor_objetivo?: number;
  opciones_permitidas?: string; // JSON string
  metodo_inspeccion?: string;
  requiere_equipo?: string;
  es_activo?: boolean;
}

interface ParametroCalidadRead {
  parametro_id: string;
  cliente_id: string;
  empresa_id: string;
  codigo: string;
  nombre: string;
  descripcion?: string;
  tipo_parametro: string;
  unidad_medida_id?: string;
  valor_minimo?: number;
  valor_maximo?: number;
  valor_objetivo?: number;
  opciones_permitidas?: string;
  metodo_inspeccion?: string;
  requiere_equipo?: string;
  es_activo: boolean;
  fecha_creacion: string;
  usuario_creacion_id?: string;
}
```

### PlanInspeccion
```typescript
interface PlanInspeccionCreate {
  empresa_id: string;
  codigo: string;
  nombre: string;
  descripcion?: string;
  aplica_a: 'producto' | 'categoria' | 'todos';
  producto_id?: string;
  categoria_id?: string;
  tipo_inspeccion: 'recepcion' | 'proceso' | 'final' | 'salida';
  tipo_muestreo?: 'total' | 'aleatorio' | 'estadistico';
  porcentaje_muestreo?: number;
  tabla_muestreo?: string;
  nivel_aceptacion_criticos?: number;
  nivel_aceptacion_mayores?: number;
  nivel_aceptacion_menores?: number;
  es_activo?: boolean;
  fecha_vigencia_desde?: string;
  fecha_vigencia_hasta?: string;
}

interface PlanInspeccionRead {
  plan_inspeccion_id: string;
  cliente_id: string;
  empresa_id: string;
  codigo: string;
  nombre: string;
  descripcion?: string;
  aplica_a: string;
  producto_id?: string;
  categoria_id?: string;
  tipo_inspeccion: string;
  tipo_muestreo?: string;
  porcentaje_muestreo?: number;
  tabla_muestreo?: string;
  nivel_aceptacion_criticos?: number;
  nivel_aceptacion_mayores?: number;
  nivel_aceptacion_menores?: number;
  es_activo: boolean;
  fecha_vigencia_desde?: string;
  fecha_vigencia_hasta?: string;
  fecha_creacion: string;
  usuario_creacion_id?: string;
}
```

### PlanInspeccionDetalle
```typescript
interface PlanInspeccionDetalleCreate {
  plan_inspeccion_id: string;
  parametro_calidad_id: string;
  orden?: number;
  es_obligatorio?: boolean;
  criticidad?: 'critico' | 'mayor' | 'menor';
  valor_minimo_plan?: number;
  valor_maximo_plan?: number;
  valor_objetivo_plan?: number;
  instrucciones_especificas?: string;
}

interface PlanInspeccionDetalleRead {
  plan_detalle_id: string;
  cliente_id: string;
  plan_inspeccion_id: string;
  parametro_calidad_id: string;
  orden?: number;
  es_obligatorio?: boolean;
  criticidad?: string;
  valor_minimo_plan?: number;
  valor_maximo_plan?: number;
  valor_objetivo_plan?: number;
  instrucciones_especificas?: string;
  fecha_creacion: string;
}
```

### Inspeccion
```typescript
interface InspeccionCreate {
  empresa_id: string;
  numero_inspeccion: string;
  fecha_inspeccion?: string;
  plan_inspeccion_id: string;
  producto_id: string;
  lote?: string;
  tipo_documento_origen?: string;
  documento_origen_id?: string;
  almacen_id?: string;
  ubicacion_almacen?: string;
  cantidad_total: number;
  cantidad_inspeccionada: number;
  unidad_medida_id: string;
  cantidad_aprobada?: number;
  cantidad_rechazada?: number;
  cantidad_observada?: number;
  defectos_criticos?: number;
  defectos_mayores?: number;
  defectos_menores?: number;
  resultado?: 'aprobado' | 'rechazado' | 'aprobado_condicional' | 'pendiente';
  inspector_usuario_id?: string;
  inspector_nombre?: string;
  observaciones?: string;
  acciones_correctivas?: string;
}

interface InspeccionRead {
  inspeccion_id: string;
  cliente_id: string;
  empresa_id: string;
  numero_inspeccion: string;
  fecha_inspeccion: string;
  plan_inspeccion_id: string;
  producto_id: string;
  lote?: string;
  tipo_documento_origen?: string;
  documento_origen_id?: string;
  almacen_id?: string;
  ubicacion_almacen?: string;
  cantidad_total: number;
  cantidad_inspeccionada: number;
  unidad_medida_id: string;
  cantidad_aprobada?: number;
  cantidad_rechazada?: number;
  cantidad_observada?: number;
  defectos_criticos?: number;
  defectos_mayores?: number;
  defectos_menores?: number;
  resultado?: string;
  inspector_usuario_id?: string;
  inspector_nombre?: string;
  observaciones?: string;
  acciones_correctivas?: string;
  aprobado_por_usuario_id?: string;
  fecha_aprobacion?: string;
  fecha_creacion: string;
  usuario_creacion_id?: string;
}
```

### InspeccionDetalle
```typescript
interface InspeccionDetalleCreate {
  inspeccion_id: string;
  parametro_calidad_id: string;
  valor_medido?: number;
  valor_cualitativo?: string;
  resultado_pasa_no_pasa?: boolean;
  cumple_especificacion?: boolean;
  criticidad_defecto?: 'critico' | 'mayor' | 'menor';
  observaciones?: string;
}

interface InspeccionDetalleRead {
  inspeccion_detalle_id: string;
  cliente_id: string;
  inspeccion_id: string;
  parametro_calidad_id: string;
  valor_medido?: number;
  valor_cualitativo?: string;
  resultado_pasa_no_pasa?: boolean;
  cumple_especificacion?: boolean;
  criticidad_defecto?: string;
  observaciones?: string;
  fecha_creacion: string;
}
```

### NoConformidad
```typescript
interface NoConformidadCreate {
  empresa_id: string;
  numero_nc: string;
  fecha_deteccion?: string;
  origen: 'inspeccion' | 'reclamo_cliente' | 'auditoria' | 'proceso';
  inspeccion_id?: string;
  documento_referencia?: string;
  producto_id?: string;
  lote?: string;
  cantidad_afectada?: number;
  descripcion_nc: string;
  tipo_nc: 'critica' | 'mayor' | 'menor';
  area_responsable?: string;
  responsable_usuario_id?: string;
  analisis_causa_raiz?: string;
  causa_raiz_identificada?: string;
  accion_inmediata?: string;
  accion_correctiva?: string;
  accion_preventiva?: string;
  responsable_accion_usuario_id?: string;
  fecha_compromiso_cierre?: string;
  estado?: 'abierta' | 'en_analisis' | 'en_accion' | 'cerrada' | 'cancelada';
}

interface NoConformidadRead {
  no_conformidad_id: string;
  cliente_id: string;
  empresa_id: string;
  numero_nc: string;
  fecha_deteccion: string;
  origen: string;
  inspeccion_id?: string;
  documento_referencia?: string;
  producto_id?: string;
  lote?: string;
  cantidad_afectada?: number;
  descripcion_nc: string;
  tipo_nc: string;
  area_responsable?: string;
  responsable_usuario_id?: string;
  analisis_causa_raiz?: string;
  causa_raiz_identificada?: string;
  accion_inmediata?: string;
  accion_correctiva?: string;
  accion_preventiva?: string;
  responsable_accion_usuario_id?: string;
  fecha_compromiso_cierre?: string;
  estado?: string;
  fecha_cierre?: string;
  cerrado_por_usuario_id?: string;
  verificacion_eficacia?: string;
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
  "detail": "Parámetro de calidad {uuid} no encontrado"
}
```

---

## 🗺️ Rutas SPA Recomendadas

```
/qms
  /parametros-calidad
    /list                    # Lista de parámetros
    /create                  # Crear parámetro
    /:id/edit                # Editar parámetro
  /planes-inspeccion
    /list                    # Lista de planes
    /create                  # Crear plan
    /:id/edit                # Editar plan
    /:id/detalles            # Ver/editar detalles del plan
  /inspecciones
    /list                    # Lista de inspecciones
    /create                  # Crear inspección
    /:id/edit                # Editar inspección
    /:id/detalles            # Ver/editar detalles de inspección
  /no-conformidades
    /list                    # Lista de no conformidades
    /create                  # Crear no conformidad
    /:id/edit                # Editar no conformidad
    /:id/cerrar              # Cerrar no conformidad
```

---

## 🔄 Flujo de Implementación Recomendado

### 1. Configuración Inicial
1. **Parámetros de Calidad:** Crear parámetros que se van a medir (peso, dimensiones, color, etc.)
2. **Planes de Inspección:** Crear planes que definan qué inspeccionar y criterios de aceptación
3. **Detalles de Plan:** Agregar parámetros al plan con orden, criticidad y valores específicos

### 2. Operaciones Diarias
1. **Crear Inspección:** Al recibir mercadería (PUR) o producir (MFG), crear inspección con plan aplicable
2. **Registrar Detalles:** Para cada parámetro del plan, registrar valores medidos/observados
3. **Evaluar Resultado:** Calcular cantidades aprobadas/rechazadas y determinar resultado final
4. **Aprobar Inspección:** Si corresponde, aprobar la inspección

### 3. Gestión de No Conformidades
1. **Crear NC:** Desde inspección rechazada o reclamo, crear no conformidad
2. **Análisis de Causa Raíz:** Realizar análisis (5 Porqués, Ishikawa, etc.)
3. **Definir Acciones:** Establecer acciones inmediatas, correctivas y preventivas
4. **Seguimiento:** Actualizar estado conforme se ejecutan las acciones
5. **Cerrar NC:** Verificar eficacia y cerrar la no conformidad

### 4. Consultas y Reportes
1. **Inspecciones por Producto:** Ver historial de inspecciones de un producto
2. **No Conformidades Abiertas:** Ver NC pendientes de cierre
3. **Estadísticas de Calidad:** Analizar tasas de aprobación/rechazo por producto/plan

---

## 📌 Notas Importantes

1. **Multi-tenancy:** Todos los datos están filtrados automáticamente por `cliente_id` del token. No enviar `cliente_id` en el body.

2. **Dependencias:** QMS requiere que ORG e INV estén configurados previamente (empresas, productos, categorías, unidades de medida, almacenes).

3. **Tipos de Parámetros:** 
   - **Cuantitativo:** Requiere unidad_medida_id y valores mínimo/máximo/objetivo
   - **Cualitativo:** Requiere opciones_permitidas (JSON con opciones)
   - **Pasa/No Pasa:** Solo requiere resultado booleano

4. **Planes de Inspección:** Pueden aplicarse a un producto específico, una categoría, o todos los productos. Los detalles del plan definen qué parámetros inspeccionar y en qué orden.

5. **Inspecciones:** Se vinculan a un plan y registran resultados. Los detalles capturan valores por cada parámetro. El resultado final se calcula según niveles de aceptación del plan.

6. **No Conformidades:** Pueden originarse de inspecciones, reclamos de clientes, auditorías o procesos. Incluyen análisis de causa raíz y acciones correctivas/preventivas.

7. **Estados:** Usar estados consistentes para inspecciones ('pendiente', 'aprobado', 'rechazado', 'aprobado_condicional') y no conformidades ('abierta', 'en_analisis', 'en_accion', 'cerrada', 'cancelada').

---

**Fin de la documentación del módulo QMS**
