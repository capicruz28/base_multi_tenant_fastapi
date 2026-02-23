# Documentación Frontend — Módulo AUD (Auditoría y Trazabilidad)

**Versión:** 1.0  
**Fecha:** 2026-02-18  
**Módulo:** AUD - Auditoría

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
/api/v1/aud
```

### Dependencias

- **Módulo ORG:** Empresa (obligatorio para filtrar por empresa).
- **Uso:** Consultar el log de auditoría (quién, cuándo, qué tabla, acción, valores anterior/nuevo) y opcionalmente registrar entradas desde middleware o integraciones.

### Alcance (CATALOGO_MODULOS / MENU_NAVEGACION)

- **Log de Auditoría:** Registro automático de todos los cambios; quién, cuándo, qué tabla, valor anterior/nuevo.
- **Reportes de Trazabilidad:** Rastrear cambios en documentos críticos; cumplimiento normativo.

---

## Autenticación

Todos los endpoints requieren JWT en el header:

```http
Authorization: Bearer <token>
```

El `cliente_id` se obtiene del token; **no enviar en el body** en las consultas.

---

## Endpoints

### 1. Log de Auditoría

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/aud/log-auditoria | Listar logs (empresa_id, modulo, tabla, accion, usuario_id, fecha_desde, fecha_hasta, registro_id, buscar, limit) |
| GET | /api/v1/aud/log-auditoria/{log_id} | Detalle de un log |
| POST | /api/v1/aud/log-auditoria | Registrar entrada de auditoría (uso típico: sistema/middleware) |

**No hay PUT ni DELETE:** el log es inmutable.

**Filtros de listado (query params):**

- `empresa_id` (UUID): filtrar por empresa.
- `modulo` (string): código del módulo (ej. INV, PUR, SLS, FIN).
- `tabla` (string): nombre de tabla afectada.
- `accion` (string): 'INSERT', 'UPDATE', 'DELETE', 'SELECT'.
- `usuario_id` (UUID): usuario que realizó la acción.
- `fecha_desde` (datetime/ISO): inicio del rango de fechas.
- `fecha_hasta` (datetime/ISO): fin del rango de fechas.
- `registro_id` (UUID): ID del registro afectado (trazabilidad de un documento/entidad).
- `buscar` (string): búsqueda en usuario_nombre, registro_descripcion, observaciones.
- `limit` (number, 1–1000): cantidad máxima de resultados (por defecto sin límite; se recomienda paginar en frontend).

**Campos al crear (POST):** empresa_id, usuario_id, usuario_nombre, modulo, tabla, accion, registro_id, registro_descripcion, valores_anteriores (JSON string), valores_nuevos (JSON string), ip_address, user_agent, observaciones.

---

## Schemas TypeScript

### Log de Auditoría

```typescript
interface LogAuditoriaCreate {
  empresa_id: string;
  usuario_id?: string;
  usuario_nombre?: string;
  modulo: string;        // ej. 'INV', 'PUR', 'SLS'
  tabla: string;         // nombre de la tabla
  accion: 'INSERT' | 'UPDATE' | 'DELETE' | 'SELECT';
  registro_id?: string;
  registro_descripcion?: string;
  valores_anteriores?: string;  // JSON string
  valores_nuevos?: string;      // JSON string
  ip_address?: string;
  user_agent?: string;
  observaciones?: string;
}

interface LogAuditoriaRead extends LogAuditoriaCreate {
  log_id: string;
  cliente_id: string;
  fecha_evento: string;  // ISO datetime
}
```

---

## Códigos de Error

| Código | Descripción |
|--------|-------------|
| 401 | No autenticado |
| 403 | Sin permisos |
| 404 | Log de auditoría no encontrado |
| 422 | Error de validación (body o query) |
| 500 | Error interno |

---

## Rutas SPA Recomendadas

```
/aud
  /log-auditoria
    /list          # Filtros: modulo, tabla, accion, usuario, fechas, registro_id
    /:log_id       # Detalle de un evento
  /trazabilidad
    # Misma API con filtro por registro_id para rastrear un documento/entidad
```

---

## Flujo de Implementación Recomendado

### 1. Pantalla Log de Auditoría

- GET /aud/log-auditoria con filtros (empresa_id, modulo, tabla, accion, usuario_id, fecha_desde, fecha_hasta, limit).
- Mostrar tabla con columnas: fecha_evento, usuario_nombre, modulo, tabla, accion, registro_descripcion; en detalle mostrar valores_anteriores y valores_nuevos (parsear JSON si es necesario).
- Opción de abrir detalle: GET /aud/log-auditoria/{log_id}.

### 2. Reportes de Trazabilidad

- Para rastrear un documento/entidad concreta: GET /aud/log-auditoria?registro_id={uuid} (y opcionalmente modulo/tabla si se conoce).
- Mostrar línea de tiempo o lista ordenada por fecha_evento.

### 3. Registro desde el frontend (opcional)

- Si se necesita registrar eventos desde la app (ej. acciones que no pasan por el backend que ya escribe en aud): POST /aud/log-auditoria con LogAuditoriaCreate. Restringir por rol si solo debe usarse desde middleware/backend.

---

## Notas Importantes

1. **Multi-tenancy:** Todo se filtra por `cliente_id` del token. No enviar `cliente_id` en el body.

2. **Inmutabilidad:** Los registros del log **no se editan ni se eliminan**. Solo consulta (GET) y creación (POST).

3. **valores_anteriores / valores_nuevos:** Son strings que contienen JSON. El backend no valida la estructura. Parsear con `JSON.parse()` en el frontend para mostrar diff o detalle. Si el backend es quien escribe el log (middleware), conviene acordar un formato (ej. objeto con claves = nombres de campo y valores = valor anterior o nuevo).

4. **accion:** 'INSERT', 'UPDATE', 'DELETE', 'SELECT'. Útil para filtrar y para iconos/etiquetas en la UI.

5. **IDs en URLs:** log_id es UUID.

6. **limit:** Se recomienda usar `limit` (ej. 100–500) y paginación en frontend para no sobrecargar la respuesta.

7. **Registro automático:** En muchos escenarios el backend (middleware o servicios) es quien escribe en aud_log_auditoria; el frontend solo consulta. El endpoint POST queda disponible para integraciones o para que el propio backend registre eventos de forma centralizada.

8. **registro_id:** Permite "trazabilidad de un registro": todos los eventos que afectaron a ese ID (documento, pedido, etc.). Muy útil para la pantalla "Reportes de Trazabilidad".

---

**Fin de la documentación del módulo AUD**
