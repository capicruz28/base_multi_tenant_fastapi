# Documentación Frontend — Módulo TKT (Mesa de Ayuda / Ticketing)

**Versión:** 1.0  
**Fecha:** 2026-02-18  
**Módulo:** TKT - Mesa de Ayuda

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
/api/v1/tkt
```

### Dependencias

- **Módulo ORG:** Empresa (obligatorio).
- **Orden recomendado:** Configurar ORG; luego crear y gestionar tickets.

---

## Autenticación

Todos los endpoints requieren JWT en el header:

```http
Authorization: Bearer <token>
```

El `cliente_id` se obtiene del token; **no enviar en el body**.

---

## Endpoints

### 1. Tickets

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/tkt/tickets | Listar (empresa_id, estado, prioridad, categoria, asignado_usuario_id, buscar) |
| GET | /api/v1/tkt/tickets/{ticket_id} | Detalle |
| POST | /api/v1/tkt/tickets | Crear ticket |
| PUT | /api/v1/tkt/tickets/{ticket_id} | Actualizar |

**Campos principales en creación:** empresa_id, numero_ticket, solicitante_usuario_id, solicitante_nombre, solicitante_email, asunto, descripcion, categoria (soporte_tecnico, consulta, incidencia, requerimiento), prioridad (urgente, alta, media, baja), asignado_usuario_id, fecha_asignacion, estado (abierto, asignado, en_proceso, resuelto, cerrado), fecha_resolucion, solucion.

**En la respuesta (Read):** La API devuelve además **tiempo_resolucion_horas** (horas entre fecha_creacion y fecha_resolucion cuando existe fecha_resolucion), calculado en backend. Útil para SLA y reportes.

---

## Schemas TypeScript

### Ticket

```typescript
interface TicketCreate {
  empresa_id: string;
  numero_ticket: string;
  solicitante_usuario_id?: string;
  solicitante_nombre?: string;
  solicitante_email?: string;
  asunto: string;
  descripcion?: string;
  categoria?: 'soporte_tecnico' | 'consulta' | 'incidencia' | 'requerimiento';
  prioridad?: 'urgente' | 'alta' | 'media' | 'baja';
  asignado_usuario_id?: string;
  fecha_asignacion?: string;
  estado?: 'abierto' | 'asignado' | 'en_proceso' | 'resuelto' | 'cerrado';
  fecha_resolucion?: string;
  solucion?: string;
}

interface TicketUpdate {
  numero_ticket?: string;
  solicitante_usuario_id?: string;
  solicitante_nombre?: string;
  solicitante_email?: string;
  asunto?: string;
  descripcion?: string;
  categoria?: string;
  prioridad?: string;
  asignado_usuario_id?: string;
  fecha_asignacion?: string;
  estado?: string;
  fecha_resolucion?: string;
  solucion?: string;
}

interface TicketRead extends TicketCreate {
  ticket_id: string;
  cliente_id: string;
  fecha_creacion: string;
  tiempo_resolucion_horas?: number;  // Calculado: horas entre fecha_creacion y fecha_resolucion
}
```

---

## Códigos de Error

| Código | Descripción |
|--------|-------------|
| 401 | No autenticado |
| 403 | Sin permisos |
| 404 | Ticket no encontrado |
| 422 | Error de validación (body o query) |
| 500 | Error interno |

---

## Rutas SPA Recomendadas

```
/tkt
  /tickets
    /list
    /create
    /:ticket_id/edit
    /:ticket_id
```

---

## Flujo de Implementación Recomendado

### 1. Configuración previa

- Tener ORG (empresa) configurado.

### 2. Tickets

- Crear ticket: POST /tkt/tickets (empresa_id, numero_ticket, asunto, descripcion, categoria, prioridad, estado: "abierto").
- Listar por empresa_id, estado, prioridad o asignado_usuario_id para mesas de ayuda y filtros.
- Asignar: PUT (asignado_usuario_id, fecha_asignacion, estado: "asignado").
- En curso / resolver: PUT (estado: "en_proceso" o "resuelto", fecha_resolucion, solucion).
- Usar **tiempo_resolucion_horas** en listados y detalle para SLA y reportes.

---

## Notas Importantes

1. **Multi-tenancy:** Todo se filtra por `cliente_id` del token. No enviar `cliente_id` en el body.

2. **Fechas:** Enviar y recibir en formato ISO datetime para fecha_asignacion y fecha_resolucion.

3. **tiempo_resolucion_horas:** Calculado en backend (diferencia en horas entre fecha_creacion y fecha_resolucion cuando fecha_resolucion existe). No recalcular en frontend.

4. **numero_ticket:** Debe ser único por (cliente_id, empresa_id). El backend no genera número; el frontend puede proponer secuencia o dejar que el usuario ingrese.

5. **Estados:** abierto → asignado → en_proceso → resuelto → cerrado. Ajustar flujo según reglas de negocio (ej. permitir cerrar sin “resuelto”).

6. **IDs en URLs:** ticket_id es UUID.

7. **Categoría y prioridad:** Valores sugeridos en schemas; se pueden usar como combos fijos en frontend para consistencia.

---

**Fin de la documentación del módulo TKT**
