# Documentación Frontend — Módulo SVC (Órdenes de Servicio)

**Versión:** 1.0  
**Fecha:** 2026-02-18  
**Módulo:** SVC - Órdenes de Servicio

---

## Índice

1. [Información General](#información-general)
2. [Autenticación](#autenticación)
3. [Endpoints](#endpoints)
4. [Schemas TypeScript](#schemas-typescript)
5. [Códigos de Error](#códigos-de-error)
6. [Rutas SPA Recomendadas](#rutas-spa-recomendadas)
7. [Flujo de Implementación Recomendado](#flujo-de-implementación-recomendado)
8. [Notas Importantes](#notas-importantes)

---

## Información General

### Base URL

```
/api/v1/svc
```

### Dependencias

- **Módulo ORG:** Empresa (obligatorio).
- **Módulo SLS:** Cliente de venta (opcional; para vincular orden a un cliente).
- **Orden recomendado:** Configurar ORG; opcionalmente SLS si se asocian órdenes a clientes.

---

## Autenticación

Todos los endpoints requieren JWT en el header:

```http
Authorization: Bearer <token>
```

El `cliente_id` se obtiene del token; **no enviar en el body**.

---

## Endpoints

### 1. Órdenes de Servicio

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/svc/ordenes-servicio | Listar (empresa_id, estado, cliente_venta_id, tipo_servicio, buscar) |
| GET | /api/v1/svc/ordenes-servicio/{orden_servicio_id} | Detalle |
| POST | /api/v1/svc/ordenes-servicio | Crear orden de servicio |
| PUT | /api/v1/svc/ordenes-servicio/{orden_servicio_id} | Actualizar |

**Campos principales en creación:** empresa_id, numero_os, fecha_solicitud (opcional; default ahora), cliente_venta_id (opcional), tipo_servicio, descripcion_servicio, tecnico_asignado_usuario_id, fecha_inicio_programada, fecha_inicio_real, fecha_fin_real, estado (solicitada, asignada, en_proceso, completada, cancelada), monto_servicio.

**En actualización:** Asignar técnico, actualizar fechas reales, estado y monto al cerrar o avanzar la orden.

### 2. Envío a Talleres / Stock en Terceros (UI)

El menú incluye "Envío a Talleres" y "Stock en Terceros". Por ahora no hay endpoints específicos; pueden listar/filtrar órdenes de servicio por estado o tipo (ej. externo/taller) y mostrar detalle. Si en el futuro se añaden tablas de materiales enviados o stock en terceros, se documentarán en esta misma base.

---

## Schemas TypeScript

### Orden de Servicio

```typescript
interface OrdenServicioCreate {
  empresa_id: string;
  numero_os: string;
  fecha_solicitud?: string;   // ISO datetime; si no se envía, backend usa ahora
  cliente_venta_id?: string;
  tipo_servicio: string;
  descripcion_servicio?: string;
  tecnico_asignado_usuario_id?: string;
  fecha_inicio_programada?: string;
  fecha_inicio_real?: string;
  fecha_fin_real?: string;
  estado?: 'solicitada' | 'asignada' | 'en_proceso' | 'completada' | 'cancelada';
  monto_servicio?: number;
}

interface OrdenServicioUpdate {
  numero_os?: string;
  fecha_solicitud?: string;
  cliente_venta_id?: string;
  tipo_servicio?: string;
  descripcion_servicio?: string;
  tecnico_asignado_usuario_id?: string;
  fecha_inicio_programada?: string;
  fecha_inicio_real?: string;
  fecha_fin_real?: string;
  estado?: string;
  monto_servicio?: number;
}

interface OrdenServicioRead extends OrdenServicioCreate {
  orden_servicio_id: string;
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
| 404 | Orden de servicio no encontrada |
| 422 | Error de validación (body o query) |
| 500 | Error interno |

---

## Rutas SPA Recomendadas

```
/svc
  /ordenes-servicio
    /list
    /create
    /:orden_servicio_id/edit
    /:orden_servicio_id
  /envio-talleres
    # Lista/filtro de órdenes (ej. tipo externo/taller)
  /stock-terceros
    # Vista de material en poder de talleres (si se implementa)
```

---

## Flujo de Implementación Recomendado

### 1. Configuración previa

- Tener ORG (empresa); opcionalmente SLS (clientes) para asociar orden a cliente.

### 2. Órdenes de Servicio

- Crear orden: POST /svc/ordenes-servicio (empresa_id, numero_os, tipo_servicio, descripcion_servicio, estado: "solicitada", cliente_venta_id si aplica).
- Listar por empresa_id, estado o tipo_servicio para dashboards y filtros.
- Asignar técnico y programar: PUT (tecnico_asignado_usuario_id, fecha_inicio_programada, estado: "asignada").
- En curso / completar: PUT (fecha_inicio_real, fecha_fin_real, estado: "en_proceso" o "completada", monto_servicio).

### 3. Envío a Talleres / Stock en Terceros

- Usar listado de órdenes con filtros (tipo_servicio, estado) para pantallas específicas; extender con tablas de detalle (materiales enviados, retornos) cuando existan en backend.

---

## Notas Importantes

1. **Multi-tenancy:** Todo se filtra por `cliente_id` del token. No enviar `cliente_id` en el body.

2. **Fechas:** Enviar y recibir en formato ISO datetime para fecha_solicitud, fecha_inicio_programada, fecha_inicio_real, fecha_fin_real.

3. **numero_os:** Debe ser único por (cliente_id, empresa_id). El backend no genera número automático; el frontend puede proponer una secuencia o dejar que el usuario ingrese el número.

4. **cliente_venta_id:** Opcional; vincula la orden a un cliente (módulo SLS). Usar listado de clientes SLS para el combo.

5. **Estados:** solicitada → asignada → en_proceso → completada (o cancelada). Ajustar flujo en frontend según reglas de negocio.

6. **IDs en URLs:** orden_servicio_id es UUID.

7. **tipo_servicio:** Texto libre (ej. "postventa", "soporte", "taller_externo", "tercerización"). Se puede mantener un catálogo en frontend o en otro módulo si se requiere.

---

**Fin de la documentación del módulo SVC**
