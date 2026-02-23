# Documentación Frontend — Módulo CRM (Customer Relationship Management)

**Versión:** 1.0  
**Fecha:** 2026-02-18  
**Módulo:** CRM - Gestión de Clientes ERP

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
/api/v1/crm
```

### Dependencias
- **Módulo ORG:** Requiere tener empresas configuradas.
- **Módulo SLS:** Requiere tener clientes configurados (para vincular leads convertidos y oportunidades).
- **Orden recomendado:** Configurar primero ORG y SLS, luego CRM.

---

## 🔐 Autenticación

Todos los endpoints requieren autenticación mediante JWT token en el header:

```http
Authorization: Bearer <token>
```

El `cliente_id` se obtiene automáticamente del token, **nunca debe enviarse en el body**.

---

## 📡 Endpoints

### 1. Campañas

#### Listar Campañas
```http
GET /api/v1/crm/campanas
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `tipo_campana` (string, opcional): Filtrar por tipo ('email', 'telemarketing', 'evento', 'digital', 'mixta')
- `estado` (string, opcional): Filtrar por estado ('planificada', 'activa', 'pausada', 'completada', 'cancelada')
- `fecha_desde` (date, opcional): Filtrar desde fecha de inicio
- `fecha_hasta` (date, opcional): Filtrar hasta fecha de inicio
- `buscar` (string, opcional): Búsqueda por nombre o código

**Response:** `200 OK`
```json
[
  {
    "campana_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "codigo_campana": "CAMP-2026-001",
    "nombre": "Campaña Q1 2026",
    "descripcion": "Campaña de lanzamiento de nuevos productos",
    "tipo_campana": "mixta",
    "objetivo": "Generar 100 leads calificados",
    "fecha_inicio": "2026-01-01",
    "fecha_fin": "2026-03-31",
    "presupuesto": 50000.00,
    "gasto_real": 35000.00,
    "moneda": "PEN",
    "responsable_usuario_id": "uuid",
    "responsable_nombre": "María González",
    "total_contactos": 500,
    "total_leads_generados": 120,
    "total_oportunidades": 45,
    "total_ventas_cerradas": 12,
    "monto_ventas_cerradas": 150000.00,
    "estado": "activa",
    "observaciones": "Campaña en curso",
    "fecha_creacion": "2026-01-01T10:00:00",
    "usuario_creacion_id": "uuid"
  }
]
```

#### Crear Campaña
```http
POST /api/v1/crm/campanas
```

**Request Body:**
```json
{
  "empresa_id": "uuid",
  "codigo_campana": "CAMP-2026-001",
  "nombre": "Campaña Q1 2026",
  "descripcion": "Campaña de lanzamiento de nuevos productos",
  "tipo_campana": "mixta",
  "objetivo": "Generar 100 leads calificados",
  "fecha_inicio": "2026-01-01",
  "fecha_fin": "2026-03-31",
  "presupuesto": 50000.00,
  "moneda": "PEN",
  "responsable_usuario_id": "uuid",
  "responsable_nombre": "María González",
  "estado": "planificada"
}
```

---

### 2. Leads

#### Listar Leads
```http
GET /api/v1/crm/leads
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `campana_id` (UUID, opcional): Filtrar por campaña
- `origen_lead` (string, opcional): Filtrar por origen ('web', 'telefono', 'referido', 'evento', 'campana', 'redes_sociales')
- `calificacion` (string, opcional): Filtrar por calificación ('caliente', 'tibio', 'frio')
- `estado` (string, opcional): Filtrar por estado ('nuevo', 'contactado', 'calificado', 'convertido', 'descartado')
- `asignado_vendedor_usuario_id` (UUID, opcional): Filtrar por vendedor asignado
- `buscar` (string, opcional): Búsqueda por nombre, empresa o email

**Response:** `200 OK`
```json
[
  {
    "lead_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "nombre_completo": "Juan Pérez",
    "empresa_nombre": "Empresa ABC S.A.C.",
    "cargo": "Gerente de Compras",
    "telefono": "01-2345678",
    "telefono_movil": "987654321",
    "email": "juan.perez@empresaabc.com",
    "direccion": "Av. Principal 123",
    "ciudad": "Lima",
    "pais": "Perú",
    "origen_lead": "web",
    "campana_id": "uuid",
    "referido_por": null,
    "calificacion": "caliente",
    "puntuacion": 85,
    "asignado_vendedor_usuario_id": "uuid",
    "asignado_vendedor_nombre": "Carlos Rodríguez",
    "fecha_asignacion": "2026-02-18T10:00:00",
    "estado": "calificado",
    "fecha_primer_contacto": "2026-02-15T09:00:00",
    "fecha_ultimo_contacto": "2026-02-18T10:00:00",
    "convertido_cliente": false,
    "cliente_venta_id": null,
    "fecha_conversion": null,
    "motivo_descarte": null,
    "observaciones": "Interesado en productos de línea premium",
    "fecha_creacion": "2026-02-15T09:00:00",
    "usuario_creacion_id": "uuid"
  }
]
```

#### Crear Lead
```http
POST /api/v1/crm/leads
```

**Request Body:**
```json
{
  "empresa_id": "uuid",
  "nombre_completo": "Juan Pérez",
  "empresa_nombre": "Empresa ABC S.A.C.",
  "cargo": "Gerente de Compras",
  "telefono": "01-2345678",
  "telefono_movil": "987654321",
  "email": "juan.perez@empresaabc.com",
  "origen_lead": "web",
  "campana_id": "uuid",
  "calificacion": "caliente",
  "puntuacion": 85,
  "estado": "nuevo"
}
```

#### Convertir Lead a Cliente
```http
PUT /api/v1/crm/leads/{lead_id}
```

**Request Body:**
```json
{
  "convertido_cliente": true,
  "cliente_venta_id": "uuid",
  "fecha_conversion": "2026-02-18T10:00:00",
  "estado": "convertido"
}
```

---

### 3. Oportunidades

#### Listar Oportunidades
```http
GET /api/v1/crm/oportunidades
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `cliente_venta_id` (UUID, opcional): Filtrar por cliente
- `lead_id` (UUID, opcional): Filtrar por lead
- `campana_id` (UUID, opcional): Filtrar por campaña
- `vendedor_usuario_id` (UUID, opcional): Filtrar por vendedor
- `etapa` (string, opcional): Filtrar por etapa ('calificacion', 'necesidad_analisis', 'propuesta', 'negociacion', 'cierre')
- `estado` (string, opcional): Filtrar por estado ('abierta', 'ganada', 'perdida', 'cancelada')
- `tipo_oportunidad` (string, opcional): Filtrar por tipo ('nuevo_negocio', 'upselling', 'cross_selling', 'renovacion')
- `fecha_cierre_desde` (date, opcional): Filtrar desde fecha de cierre estimada
- `fecha_cierre_hasta` (date, opcional): Filtrar hasta fecha de cierre estimada
- `buscar` (string, opcional): Búsqueda por nombre, número o cliente

**Response:** `200 OK`
```json
[
  {
    "oportunidad_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "numero_oportunidad": "OP-2026-001",
    "nombre": "Venta de productos línea premium",
    "descripcion": "Oportunidad para vender productos de línea premium a nuevo cliente",
    "cliente_venta_id": "uuid",
    "lead_id": "uuid",
    "nombre_cliente_prospecto": null,
    "vendedor_usuario_id": "uuid",
    "vendedor_nombre": "Carlos Rodríguez",
    "campana_id": "uuid",
    "monto_estimado": 50000.00,
    "moneda": "PEN",
    "probabilidad_cierre": 75.00,
    "fecha_apertura": "2026-02-01",
    "fecha_cierre_estimada": "2026-03-15",
    "fecha_cierre_real": null,
    "etapa": "negociacion",
    "etapa_anterior": "propuesta",
    "fecha_cambio_etapa": "2026-02-15T10:00:00",
    "tipo_oportunidad": "nuevo_negocio",
    "productos_interes": "[{\"producto_id\":\"uuid\",\"nombre\":\"Producto A\",\"cantidad\":10}]",
    "estado": "abierta",
    "motivo_ganada": null,
    "motivo_perdida": null,
    "competidor": null,
    "cotizacion_generada": false,
    "cotizacion_id": null,
    "pedido_generado": false,
    "pedido_id": null,
    "observaciones": "Cliente interesado, esperando aprobación presupuestaria",
    "proxima_accion": "Enviar propuesta comercial detallada",
    "fecha_proxima_accion": "2026-02-20",
    "fecha_creacion": "2026-02-01T10:00:00",
    "fecha_actualizacion": "2026-02-15T10:00:00",
    "usuario_creacion_id": "uuid"
  }
]
```

#### Crear Oportunidad
```http
POST /api/v1/crm/oportunidades
```

**Request Body:**
```json
{
  "empresa_id": "uuid",
  "numero_oportunidad": "OP-2026-001",
  "nombre": "Venta de productos línea premium",
  "cliente_venta_id": "uuid",
  "lead_id": "uuid",
  "vendedor_usuario_id": "uuid",
  "vendedor_nombre": "Carlos Rodríguez",
  "campana_id": "uuid",
  "monto_estimado": 50000.00,
  "moneda": "PEN",
  "probabilidad_cierre": 75.00,
  "fecha_apertura": "2026-02-01",
  "fecha_cierre_estimada": "2026-03-15",
  "etapa": "calificacion",
  "tipo_oportunidad": "nuevo_negocio",
  "estado": "abierta",
  "proxima_accion": "Contactar cliente para reunión inicial",
  "fecha_proxima_accion": "2026-02-05"
}
```

#### Avanzar Etapa de Oportunidad
```http
PUT /api/v1/crm/oportunidades/{oportunidad_id}
```

**Request Body:**
```json
{
  "etapa": "propuesta",
  "etapa_anterior": "necesidad_analisis",
  "fecha_cambio_etapa": "2026-02-15T10:00:00",
  "proxima_accion": "Enviar propuesta comercial",
  "fecha_proxima_accion": "2026-02-20"
}
```

#### Cerrar Oportunidad como Ganada
```http
PUT /api/v1/crm/oportunidades/{oportunidad_id}
```

**Request Body:**
```json
{
  "estado": "ganada",
  "fecha_cierre_real": "2026-03-10",
  "motivo_ganada": "Cliente aceptó propuesta comercial",
  "cotizacion_generada": true,
  "cotizacion_id": "uuid",
  "pedido_generado": true,
  "pedido_id": "uuid"
}
```

---

### 4. Actividades

#### Listar Actividades
```http
GET /api/v1/crm/actividades
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `lead_id` (UUID, opcional): Filtrar por lead
- `oportunidad_id` (UUID, opcional): Filtrar por oportunidad
- `cliente_venta_id` (UUID, opcional): Filtrar por cliente
- `tipo_actividad` (string, opcional): Filtrar por tipo ('llamada', 'reunion', 'email', 'visita', 'demo', 'cotizacion_enviada')
- `usuario_responsable_id` (UUID, opcional): Filtrar por responsable
- `estado` (string, opcional): Filtrar por estado ('planificada', 'completada', 'cancelada')
- `fecha_desde` (datetime, opcional): Filtrar desde fecha de actividad
- `fecha_hasta` (datetime, opcional): Filtrar hasta fecha de actividad
- `buscar` (string, opcional): Búsqueda por asunto o descripción

**Response:** `200 OK`
```json
[
  {
    "actividad_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "tipo_actividad": "reunion",
    "asunto": "Reunión de presentación de productos",
    "descripcion": "Reunión para presentar línea premium de productos",
    "lead_id": "uuid",
    "oportunidad_id": "uuid",
    "cliente_venta_id": null,
    "fecha_actividad": "2026-02-20T14:00:00",
    "duracion_minutos": 60,
    "usuario_responsable_id": "uuid",
    "responsable_nombre": "Carlos Rodríguez",
    "resultado": "exitosa",
    "requiere_seguimiento": true,
    "fecha_seguimiento": "2026-02-25",
    "estado": "completada",
    "fecha_completado": "2026-02-20T15:00:00",
    "observaciones": "Cliente muy interesado, solicita propuesta comercial",
    "fecha_creacion": "2026-02-18T10:00:00",
    "usuario_creacion_id": "uuid"
  }
]
```

#### Crear Actividad
```http
POST /api/v1/crm/actividades
```

**Request Body:**
```json
{
  "empresa_id": "uuid",
  "tipo_actividad": "reunion",
  "asunto": "Reunión de presentación de productos",
  "descripcion": "Reunión para presentar línea premium de productos",
  "oportunidad_id": "uuid",
  "fecha_actividad": "2026-02-20T14:00:00",
  "duracion_minutos": 60,
  "usuario_responsable_id": "uuid",
  "responsable_nombre": "Carlos Rodríguez",
  "estado": "planificada",
  "requiere_seguimiento": true,
  "fecha_seguimiento": "2026-02-25"
}
```

#### Completar Actividad
```http
PUT /api/v1/crm/actividades/{actividad_id}
```

**Request Body:**
```json
{
  "estado": "completada",
  "fecha_completado": "2026-02-20T15:00:00",
  "resultado": "exitosa",
  "observaciones": "Cliente muy interesado, solicita propuesta comercial"
}
```

---

## 📝 Schemas TypeScript

### Campana
```typescript
interface CampanaCreate {
  empresa_id: string;
  codigo_campana: string;
  nombre: string;
  descripcion?: string;
  tipo_campana: 'email' | 'telemarketing' | 'evento' | 'digital' | 'mixta';
  objetivo?: string;
  fecha_inicio: string;
  fecha_fin?: string;
  presupuesto?: number;
  gasto_real?: number;
  moneda?: string;
  responsable_usuario_id?: string;
  responsable_nombre?: string;
  estado?: 'planificada' | 'activa' | 'pausada' | 'completada' | 'cancelada';
  observaciones?: string;
}

interface CampanaRead {
  campana_id: string;
  cliente_id: string;
  empresa_id: string;
  codigo_campana: string;
  nombre: string;
  descripcion?: string;
  tipo_campana: string;
  objetivo?: string;
  fecha_inicio: string;
  fecha_fin?: string;
  presupuesto?: number;
  gasto_real?: number;
  moneda?: string;
  responsable_usuario_id?: string;
  responsable_nombre?: string;
  total_contactos?: number;
  total_leads_generados?: number;
  total_oportunidades?: number;
  total_ventas_cerradas?: number;
  monto_ventas_cerradas?: number;
  estado?: string;
  observaciones?: string;
  fecha_creacion: string;
  usuario_creacion_id?: string;
}
```

### Lead
```typescript
interface LeadCreate {
  empresa_id: string;
  nombre_completo: string;
  empresa_nombre?: string;
  cargo?: string;
  telefono?: string;
  telefono_movil?: string;
  email?: string;
  direccion?: string;
  ciudad?: string;
  pais?: string;
  origen_lead: 'web' | 'telefono' | 'referido' | 'evento' | 'campana' | 'redes_sociales';
  campana_id?: string;
  referido_por?: string;
  calificacion?: 'caliente' | 'tibio' | 'frio';
  puntuacion?: number; // 0-100
  asignado_vendedor_usuario_id?: string;
  asignado_vendedor_nombre?: string;
  estado?: 'nuevo' | 'contactado' | 'calificado' | 'convertido' | 'descartado';
  observaciones?: string;
}

interface LeadRead {
  lead_id: string;
  cliente_id: string;
  empresa_id: string;
  nombre_completo: string;
  empresa_nombre?: string;
  cargo?: string;
  telefono?: string;
  telefono_movil?: string;
  email?: string;
  direccion?: string;
  ciudad?: string;
  pais?: string;
  origen_lead: string;
  campana_id?: string;
  referido_por?: string;
  calificacion?: string;
  puntuacion?: number;
  asignado_vendedor_usuario_id?: string;
  asignado_vendedor_nombre?: string;
  fecha_asignacion?: string;
  estado?: string;
  fecha_primer_contacto?: string;
  fecha_ultimo_contacto?: string;
  convertido_cliente?: boolean;
  cliente_venta_id?: string;
  fecha_conversion?: string;
  motivo_descarte?: string;
  observaciones?: string;
  fecha_creacion: string;
  usuario_creacion_id?: string;
}
```

### Oportunidad
```typescript
interface OportunidadCreate {
  empresa_id: string;
  numero_oportunidad: string;
  nombre: string;
  descripcion?: string;
  cliente_venta_id?: string;
  lead_id?: string;
  nombre_cliente_prospecto?: string;
  vendedor_usuario_id: string;
  vendedor_nombre?: string;
  campana_id?: string;
  monto_estimado: number;
  moneda?: string;
  probabilidad_cierre?: number; // 0-100
  fecha_apertura?: string;
  fecha_cierre_estimada?: string;
  etapa: 'calificacion' | 'necesidad_analisis' | 'propuesta' | 'negociacion' | 'cierre';
  tipo_oportunidad?: 'nuevo_negocio' | 'upselling' | 'cross_selling' | 'renovacion';
  productos_interes?: string; // JSON string
  estado?: 'abierta' | 'ganada' | 'perdida' | 'cancelada';
  observaciones?: string;
  proxima_accion?: string;
  fecha_proxima_accion?: string;
}

interface OportunidadRead {
  oportunidad_id: string;
  cliente_id: string;
  empresa_id: string;
  numero_oportunidad: string;
  nombre: string;
  descripcion?: string;
  cliente_venta_id?: string;
  lead_id?: string;
  nombre_cliente_prospecto?: string;
  vendedor_usuario_id: string;
  vendedor_nombre?: string;
  campana_id?: string;
  monto_estimado: number;
  moneda?: string;
  probabilidad_cierre?: number;
  fecha_apertura: string;
  fecha_cierre_estimada?: string;
  fecha_cierre_real?: string;
  etapa: string;
  etapa_anterior?: string;
  fecha_cambio_etapa?: string;
  tipo_oportunidad?: string;
  productos_interes?: string;
  estado?: string;
  motivo_ganada?: string;
  motivo_perdida?: string;
  competidor?: string;
  cotizacion_generada?: boolean;
  cotizacion_id?: string;
  pedido_generado?: boolean;
  pedido_id?: string;
  observaciones?: string;
  proxima_accion?: string;
  fecha_proxima_accion?: string;
  fecha_creacion: string;
  fecha_actualizacion?: string;
  usuario_creacion_id?: string;
}
```

### Actividad
```typescript
interface ActividadCreate {
  empresa_id: string;
  tipo_actividad: 'llamada' | 'reunion' | 'email' | 'visita' | 'demo' | 'cotizacion_enviada';
  asunto: string;
  descripcion?: string;
  lead_id?: string;
  oportunidad_id?: string;
  cliente_venta_id?: string;
  fecha_actividad: string;
  duracion_minutos?: number;
  usuario_responsable_id: string;
  responsable_nombre?: string;
  resultado?: 'exitosa' | 'sin_respuesta' | 'reagendar' | 'no_interesado';
  requiere_seguimiento?: boolean;
  fecha_seguimiento?: string;
  estado?: 'planificada' | 'completada' | 'cancelada';
  observaciones?: string;
}

interface ActividadRead {
  actividad_id: string;
  cliente_id: string;
  empresa_id: string;
  tipo_actividad: string;
  asunto: string;
  descripcion?: string;
  lead_id?: string;
  oportunidad_id?: string;
  cliente_venta_id?: string;
  fecha_actividad: string;
  duracion_minutos?: number;
  usuario_responsable_id: string;
  responsable_nombre?: string;
  resultado?: string;
  requiere_seguimiento?: boolean;
  fecha_seguimiento?: string;
  estado?: string;
  fecha_completado?: string;
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
  "detail": "Campaña {uuid} no encontrada"
}
```

---

## 🗺️ Rutas SPA Recomendadas

```
/crm
  /campanas
    /list                    # Lista de campañas
    /create                  # Crear campaña
    /:id/edit                # Editar campaña
    /:id/metricas            # Ver métricas de campaña
  /leads
    /list                    # Lista de leads
    /create                  # Crear lead
    /:id/edit                # Editar lead
    /:id/convertir           # Convertir lead a cliente
  /oportunidades
    /list                    # Lista de oportunidades (pipeline)
    /create                  # Crear oportunidad
    /:id/edit                # Editar oportunidad
    /:id/avanzar-etapa       # Avanzar etapa del pipeline
    /:id/cerrar              # Cerrar oportunidad (ganada/perdida)
    /pipeline                # Vista de pipeline por etapas
  /actividades
    /list                    # Lista de actividades
    /create                  # Crear actividad
    /:id/edit                # Editar actividad
    /:id/completar           # Completar actividad
    /calendario              # Vista de calendario de actividades
```

---

## 🔄 Flujo de Implementación Recomendado

### 1. Configuración Inicial
1. **Campañas:** Crear campañas de marketing/ventas con objetivos y presupuesto
2. **Leads:** Captar prospectos desde diferentes orígenes (web, eventos, referidos, etc.)

### 2. Gestión de Leads
1. **Calificar Leads:** Asignar calificación (caliente/tibio/frío) y puntuación (0-100)
2. **Asignar Vendedores:** Asignar leads a vendedores para seguimiento
3. **Contactar:** Registrar actividades de contacto (llamadas, emails, reuniones)
4. **Convertir:** Cuando el lead está listo, convertirlo a cliente (vinculando con SLS)

### 3. Pipeline de Oportunidades
1. **Crear Oportunidad:** Desde lead calificado o cliente existente
2. **Seguir Etapas:** Avanzar por las etapas del pipeline (calificación → necesidad_analisis → propuesta → negociación → cierre)
3. **Registrar Actividades:** Documentar todas las interacciones (llamadas, reuniones, emails)
4. **Generar Cotización:** Cuando corresponde, generar cotización desde SLS y vincularla
5. **Cerrar Oportunidad:** Marcar como ganada (vinculando pedido) o perdida (con motivo)

### 4. Actividades de Seguimiento
1. **Planificar Actividades:** Programar llamadas, reuniones, visitas relacionadas con leads/oportunidades
2. **Ejecutar:** Realizar la actividad y registrar resultado
3. **Seguimiento:** Si requiere seguimiento, programar próxima actividad

### 5. Reportes y Métricas
1. **Métricas de Campaña:** Ver leads generados, oportunidades creadas, ventas cerradas por campaña
2. **Pipeline por Etapa:** Visualizar oportunidades agrupadas por etapa del pipeline
3. **Actividades por Vendedor:** Ver actividades planificadas y completadas por vendedor
4. **Tasa de Conversión:** Analizar conversión de leads a oportunidades y de oportunidades a ventas

---

## 📌 Notas Importantes

1. **Multi-tenancy:** Todos los datos están filtrados automáticamente por `cliente_id` del token. No enviar `cliente_id` en el body.

2. **Dependencias:** CRM requiere que ORG y SLS estén configurados previamente (empresas, clientes).

3. **Flujo de Conversión:** 
   - **Lead → Cliente:** Cuando un lead se convierte, se vincula con `sls_cliente` mediante `cliente_venta_id`
   - **Oportunidad → Cotización/Pedido:** Las oportunidades pueden generar cotizaciones y pedidos en SLS, vinculados mediante `cotizacion_id` y `pedido_id`

4. **Pipeline de Ventas:** Las oportunidades avanzan por etapas. Cada cambio de etapa debe actualizar `etapa_anterior`, `etapa`, y `fecha_cambio_etapa`.

5. **Lead Scoring:** La puntuación (0-100) ayuda a priorizar leads. Se puede calcular automáticamente según criterios (origen, empresa, cargo, interacciones, etc.).

6. **Actividades:** Pueden estar vinculadas a leads, oportunidades o clientes directamente. Son fundamentales para el seguimiento comercial.

7. **Estados:** Usar estados consistentes para campañas ('planificada', 'activa', 'pausada', 'completada', 'cancelada'), leads ('nuevo', 'contactado', 'calificado', 'convertido', 'descartado'), oportunidades ('abierta', 'ganada', 'perdida', 'cancelada'), y actividades ('planificada', 'completada', 'cancelada').

8. **Valor Ponderado:** En oportunidades, el valor ponderado se calcula automáticamente como `monto_estimado * probabilidad_cierre / 100`. Útil para pronósticos de ventas.

---

**Fin de la documentación del módulo CRM**
