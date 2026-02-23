# Documentación Frontend — Módulo MNT (Mantenimiento de Activos)

**Versión:** 1.0  
**Fecha:** 2026-02-18  
**Módulo:** MNT - Mantenimiento de Activos

---

## Índice

1. [Información General](#información-general)
2. [Autenticación](#autenticación)
3. [Endpoints](#endpoints)
4. [Schemas TypeScript](#schemas-typescript)
5. [Códigos de Error](#códigos-de-error)
6. [Rutas SPA Recomendadas](#rutas-spa-recomendadas)
7. [Flujo de Implementación Recomendado](#flujo-de-implementación-recomendado)

---

## Información General

### Base URL

```
/api/v1/mnt
```

### Dependencias

- **Módulo ORG:** Empresa, sucursal (obligatorio).
- **Módulo MFG:** Centros de trabajo (opcional; para vincular activos de producción).
- **Módulo LOG:** Vehículos (opcional; para vincular activo a un vehículo).
- **Módulo PUR:** Proveedor (opcional; para fabricante/proveedor del activo).
- **Orden recomendado:** Configurar ORG; MFG y LOG si se vinculan activos a centros o vehículos.

---

## Autenticación

Todos los endpoints requieren JWT en el header:

```http
Authorization: Bearer <token>
```

El `cliente_id` se obtiene del token; **no enviar en el body**.

---

## Endpoints

### 1. Activos

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/mnt/activos | Listar (empresa_id, tipo_activo, estado_activo, criticidad, es_activo, buscar) |
| GET | /api/v1/mnt/activos/{activo_id} | Detalle |
| POST | /api/v1/mnt/activos | Crear activo |
| PUT | /api/v1/mnt/activos/{activo_id} | Actualizar |

Campos principales en creación: empresa_id, codigo_activo, nombre, descripcion, tipo_activo (maquinaria, vehiculo, equipo, instalacion, herramienta), categoria, marca, modelo, numero_serie, **anio_fabricacion** (número), sucursal_id, centro_trabajo_id, ubicacion_detalle, vehiculo_id, especificaciones_tecnicas, capacidad, potencia, fabricante, proveedor_id, fecha_adquisicion, fecha_puesta_operacion, vida_util_años, criticidad (critica, alta, media, baja), valor_adquisicion, valor_actual, moneda, estado_activo (operativo, mantenimiento, averiado, baja), observaciones, es_activo.

### 2. Planes de Mantenimiento

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/mnt/planes-mantenimiento | Listar (activo_id, tipo_mantenimiento, es_activo, buscar) |
| GET | /api/v1/mnt/planes-mantenimiento/{plan_mantenimiento_id} | Detalle |
| POST | /api/v1/mnt/planes-mantenimiento | Crear plan |
| PUT | /api/v1/mnt/planes-mantenimiento/{plan_mantenimiento_id} | Actualizar |

Campos principales: activo_id, codigo_plan, nombre, descripcion, tipo_mantenimiento (preventivo, predictivo), frecuencia_tipo (dias, horas_uso, kilometros, ciclos), frecuencia_valor, fecha_ultimo_mantenimiento, fecha_proximo_mantenimiento, horas_uso_ultimo, horas_uso_proximo, responsable_usuario_id, responsable_nombre, tareas_mantenimiento (JSON o texto), costo_estimado, moneda, es_activo.

### 3. Órdenes de Trabajo

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/mnt/ordenes-trabajo | Listar (empresa_id, activo_id, estado, tipo_mantenimiento, buscar) |
| GET | /api/v1/mnt/ordenes-trabajo/{orden_trabajo_id} | Detalle |
| POST | /api/v1/mnt/ordenes-trabajo | Crear OT |
| PUT | /api/v1/mnt/ordenes-trabajo/{orden_trabajo_id} | Actualizar (avance, cierre, costos) |

Campos principales: empresa_id, numero_ot, activo_id, plan_mantenimiento_id (opcional), tipo_mantenimiento (preventivo, correctivo, predictivo, modificacion), prioridad (urgente, alta, media, baja), problema_detectado, trabajo_a_realizar, tecnico_asignado_usuario_id, tecnico_nombre, fecha_programada, fecha_inicio_real, fecha_fin_real, trabajo_realizado, repuestos_utilizados (JSON/texto), costo_mano_obra, costo_repuestos, costo_servicios_terceros, moneda, estado (solicitada, programada, en_proceso, pausada, completada, cerrada, cancelada), fecha_cierre, cerrado_por_usuario_id, calificacion_trabajo (1-5), observaciones. La respuesta incluye **duracion_horas** y **costo_total** calculados.

### 4. Historial de Mantenimiento

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/mnt/historial-mantenimiento | Listar (activo_id, orden_trabajo_id, tipo_mantenimiento) |
| GET | /api/v1/mnt/historial-mantenimiento/{historial_id} | Detalle |
| POST | /api/v1/mnt/historial-mantenimiento | Registrar entrada de historial |
| PUT | /api/v1/mnt/historial-mantenimiento/{historial_id} | Actualizar |

Campos principales: activo_id, orden_trabajo_id (opcional), fecha_mantenimiento, tipo_mantenimiento, descripcion_trabajo, tecnico_nombre, horas_uso_activo, kilometraje, costo_total, moneda, observaciones.

---

## Schemas TypeScript

### Activo

```typescript
interface ActivoCreate {
  empresa_id: string;
  codigo_activo: string;
  nombre: string;
  descripcion?: string;
  tipo_activo: 'maquinaria' | 'vehiculo' | 'equipo' | 'instalacion' | 'herramienta';
  categoria?: string;
  marca?: string;
  modelo?: string;
  numero_serie?: string;
  anio_fabricacion?: number;  // En API se usa "anio_fabricacion"
  sucursal_id?: string;
  centro_trabajo_id?: string;
  ubicacion_detalle?: string;
  vehiculo_id?: string;
  especificaciones_tecnicas?: string;
  capacidad?: string;
  potencia?: string;
  fabricante?: string;
  proveedor_id?: string;
  fecha_adquisicion?: string;
  fecha_puesta_operacion?: string;
  vida_util_años?: number;
  criticidad?: 'critica' | 'alta' | 'media' | 'baja';
  valor_adquisicion?: number;
  valor_actual?: number;
  moneda?: string;
  estado_activo?: 'operativo' | 'mantenimiento' | 'averiado' | 'baja';
  observaciones?: string;
  es_activo?: boolean;
}

interface ActivoRead extends ActivoCreate {
  activo_id: string;
  cliente_id: string;
  fecha_creacion: string;
  usuario_creacion_id?: string;
}
```

### Plan Mantenimiento

```typescript
interface PlanMantenimientoCreate {
  activo_id: string;
  codigo_plan: string;
  nombre: string;
  descripcion?: string;
  tipo_mantenimiento: 'preventivo' | 'predictivo';
  frecuencia_tipo: 'dias' | 'horas_uso' | 'kilometros' | 'ciclos';
  frecuencia_valor: number;
  fecha_ultimo_mantenimiento?: string;
  fecha_proximo_mantenimiento?: string;
  horas_uso_ultimo?: number;
  horas_uso_proximo?: number;
  responsable_usuario_id?: string;
  responsable_nombre?: string;
  tareas_mantenimiento?: string;
  costo_estimado?: number;
  moneda?: string;
  es_activo?: boolean;
}

interface PlanMantenimientoRead extends PlanMantenimientoCreate {
  plan_mantenimiento_id: string;
  cliente_id: string;
  fecha_creacion: string;
  usuario_creacion_id?: string;
}
```

### Orden Trabajo

```typescript
interface OrdenTrabajoCreate {
  empresa_id: string;
  numero_ot: string;
  activo_id: string;
  plan_mantenimiento_id?: string;
  tipo_mantenimiento: string;
  prioridad?: 'urgente' | 'alta' | 'media' | 'baja';
  problema_detectado?: string;
  trabajo_a_realizar: string;
  tecnico_asignado_usuario_id?: string;
  tecnico_nombre?: string;
  fecha_programada?: string;
  fecha_inicio_real?: string;
  fecha_fin_real?: string;
  trabajo_realizado?: string;
  repuestos_utilizados?: string;
  costo_mano_obra?: number;
  costo_repuestos?: number;
  costo_servicios_terceros?: number;
  moneda?: string;
  estado?: string;
  fecha_cierre?: string;
  cerrado_por_usuario_id?: string;
  calificacion_trabajo?: number;
  observaciones?: string;
}

interface OrdenTrabajoRead extends OrdenTrabajoCreate {
  orden_trabajo_id: string;
  cliente_id: string;
  fecha_solicitud: string;
  duracion_horas?: number;   // calculado
  costo_total?: number;      // calculado
  fecha_creacion: string;
  usuario_creacion_id?: string;
}
```

### Historial Mantenimiento

```typescript
interface HistorialMantenimientoCreate {
  activo_id: string;
  orden_trabajo_id?: string;
  fecha_mantenimiento: string;
  tipo_mantenimiento: string;
  descripcion_trabajo?: string;
  tecnico_nombre?: string;
  horas_uso_activo?: number;
  kilometraje?: number;
  costo_total?: number;
  moneda?: string;
  observaciones?: string;
}

interface HistorialMantenimientoRead extends HistorialMantenimientoCreate {
  historial_id: string;
  cliente_id: string;
  fecha_creacion: string;
}
```

---

## Códigos de Error

| Código | Descripción |
|--------|-------------|
| 401 | No autenticado |
| 403 | Sin permisos |
| 404 | Recurso no encontrado (activo, plan, OT, historial) |
| 422 | Error de validación (body o query) |
| 500 | Error interno |

---

## Rutas SPA Recomendadas

```
/mnt
  /activos
    /list
    /create
    /:id/edit
    /:id/planes        # Planes (planes-mantenimiento?activo_id=)
    /:id/ordenes      # OT (ordenes-trabajo?activo_id=)
    /:id/historial     # Historial (historial-mantenimiento?activo_id=)
  /planes-mantenimiento
    /list
    /create
    /:id/edit
  /ordenes-trabajo
    /list
    /create
    /:id/edit
  /historial-mantenimiento
    /list
    /create
    /:id/edit
```

---

## Flujo de Implementación Recomendado

### 1. Configuración previa

- Tener ORG (empresa, sucursales); opcionalmente MFG (centros de trabajo) y LOG (vehículos).

### 2. Maestro de activos

- Crear activos: POST /mnt/activos (codigo_activo, nombre, tipo_activo, centro_trabajo_id si aplica, vehiculo_id si aplica, criticidad, estado_activo).
- Listar por empresa, tipo, estado o criticidad para dashboards y filtros.

### 3. Planes de mantenimiento

- Por cada activo crítico o importante: POST /mnt/planes-mantenimiento (activo_id, codigo_plan, nombre, tipo_mantenimiento, frecuencia_tipo, frecuencia_valor, fecha_proximo_mantenimiento, tareas_mantenimiento).
- Listar por activo_id para ver próximos mantenimientos; actualizar fecha_ultimo y fecha_proximo al ejecutar una OT.

### 4. Órdenes de trabajo

- Crear OT: POST /mnt/ordenes-trabajo (empresa_id, numero_ot, activo_id, plan_mantenimiento_id si preventivo, tipo_mantenimiento, prioridad, trabajo_a_realizar, tecnico_nombre, fecha_programada).
- Seguimiento: PUT para actualizar estado (programada → en_proceso → completada/cerrada), fecha_inicio_real, fecha_fin_real, trabajo_realizado, repuestos_utilizados, costos.
- La API devuelve duracion_horas y costo_total; usar para reportes.

### 5. Historial

- Registrar entradas en historial: POST /mnt/historial-mantenimiento (activo_id, orden_trabajo_id si viene de una OT, fecha_mantenimiento, tipo_mantenimiento, descripcion_trabajo, costo_total).
- Listar por activo_id para ver trazabilidad completa del activo.

---

## Notas Importantes

1. **Multi-tenancy:** Todo se filtra por `cliente_id` del token. No enviar `cliente_id` en el body.

2. **Campo año de fabricación:** En la API se usa **anio_fabricacion** (sin ñ) en JSON. Enviar y leer como número (ej. 2020).

3. **Orden de trabajo – duración y costo:** Se calculan en backend: duracion_horas a partir de fecha_inicio_real y fecha_fin_real; costo_total = costo_mano_obra + costo_repuestos + costo_servicios_terceros.

4. **Estados OT:** solicitada → programada → en_proceso → pausada → completada → cerrada (o cancelada). Ajustar flujo en frontend según reglas de negocio.

5. **IDs en URLs:** activo_id, plan_mantenimiento_id, orden_trabajo_id, historial_id; todos son UUID.

6. **Vínculos:** centro_trabajo_id (MFG) y vehiculo_id (LOG) permiten asociar el activo a un centro de trabajo o a un vehículo; usar listas de MFG/LOG para selects en el formulario de activo.

---

**Fin de la documentación del módulo MNT**
