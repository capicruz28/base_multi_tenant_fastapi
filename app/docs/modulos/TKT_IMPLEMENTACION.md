# Implementación TKT — Mesa de Ayuda (Ticketing)

Documento final generado tras completar **Fase 3** del módulo **TKT**.

Referencia BD: `docs/bd/TKT_TABLAS.sql` (tabla `tkt_ticket`).

---

## 1. Alcance implementado

- **Entidad**: `tkt_ticket`
- **Objetivo**:
  - Mantener rutas existentes sin romper contrato.
  - Endurecer reglas de negocio en actualización (PUT) por estado.
  - Implementar **transiciones de estado** por endpoints dedicados:
    - **asignar**: `abierto` → `asignado` (setea `asignado_usuario_id`, `fecha_asignacion`)
    - **iniciar**: `asignado` → `en_proceso`
    - **resolver**: `en_proceso` → `resuelto` (setea `fecha_resolucion`, `solucion`)
    - **cerrar**: `resuelto` → `cerrado`
  - Agregar soporte de filtro **opcional** por `empresa_id` en **GET/PUT por ID** (scope multi-empresa dentro del mismo `cliente_id`).

---

## 2. Endpoints (API v1)

Base router: `/api/v1/tkt` (según `settings.API_V1_STR` y `app/api/v1/api.py`).

### 2.1 Endpoints existentes (se mantienen)

- `GET /tickets`
  - **Tenant**: filtra por `cliente_id` del usuario autenticado.
  - **Empresa**: filtro opcional `empresa_id` (query param).
  - **RBAC**: `tkt.ticket.leer`.

- `GET /tickets/{ticket_id}`
  - **Empresa**: `empresa_id` opcional (query param) para acotar el recurso.
  - **RBAC**: `tkt.ticket.leer`.

- `POST /tickets`
  - **Tenant**: `cliente_id` forzado desde el usuario autenticado.
  - **Empresa**: `empresa_id` en body (schema existente).
  - **RBAC**: `tkt.ticket.crear`.

- `PUT /tickets/{ticket_id}`
  - **Empresa**: `empresa_id` opcional (query param) para acotar el recurso.
  - **Regla de estado**: **solo editable** si `estado` actual es `abierto` o `asignado`.
  - **Cambio de estado**: bloqueado en `PUT` (debe hacerse con endpoints de transición).
  - **RBAC**: `tkt.ticket.actualizar`.

### 2.2 Endpoints nuevos (transiciones de estado)

- `POST /tickets/{ticket_id}/asignar`
  - Body: `asignado_usuario_id`
  - Transición: `abierto` → `asignado`
  - Set: `fecha_asignacion = utcnow`
  - **RBAC**: `tkt.ticket.asignar`

- `POST /tickets/{ticket_id}/iniciar`
  - Transición: `asignado` → `en_proceso`
  - **RBAC**: `tkt.ticket.actualizar`

- `POST /tickets/{ticket_id}/resolver`
  - Body: `solucion`
  - Transición: `en_proceso` → `resuelto`
  - Set: `fecha_resolucion = utcnow`
  - **RBAC**: `tkt.ticket.resolver`

- `POST /tickets/{ticket_id}/cerrar`
  - Transición: `resuelto` → `cerrado`
  - **RBAC**: `tkt.ticket.cerrar`

Notas:
- Las transiciones se implementan con actualización condicionada por estado (evita cambios inválidos) y devuelven el recurso actualizado.
- Los errores de regla de negocio se reportan como validación (HTTP 400) con `ValidationError` del proyecto.

---

## 3. Multi-tenant (cliente/empresa)

- **cliente_id**:
  - Se usa en todas las operaciones (lectura/creación/actualización/transiciones) como criterio de aislamiento tenant.
  - Proviene del usuario autenticado (`current_user.cliente_id`).

- **empresa_id**:
  - `GET /tickets`: filtro opcional existente.
  - `GET/PUT/transiciones por ID`: soporte de filtro opcional por `empresa_id` (query param). Si se envía, el recurso se busca/actualiza con `cliente_id + ticket_id + empresa_id`.

---

## 4. RBAC

Permisos utilizados por el módulo:

- `tkt.ticket.leer`
- `tkt.ticket.crear`
- `tkt.ticket.actualizar`
- `tkt.ticket.asignar`
- `tkt.ticket.resolver`
- `tkt.ticket.cerrar`

Seed agregado:
- `app/docs/database/SEED_PERMISOS_RBAC_TKT.sql` (idempotente vía `MERGE`, módulo TKT id `E1000017-0000-4000-8000-000000000017`).

---

## 5. Archivos modificados/creados

### Modificados

- `app/infrastructure/database/queries/tkt/ticket_queries.py`
- `app/infrastructure/database/queries/tkt/__init__.py`
- `app/modules/tkt/application/services/ticket_service.py`
- `app/modules/tkt/application/services/__init__.py`
- `app/modules/tkt/presentation/endpoints_ticket.py`

### Creados

- `app/docs/database/SEED_PERMISOS_RBAC_TKT.sql`
- `app/docs/modulos/TKT_IMPLEMENTACION.md`

---

## 6. Verificación final (checklist)

Para cada endpoint nuevo/ajustado (GET/PUT por ID + transiciones) se verifica:

- **Tenant**:
  - `cliente_id` aplicado en queries/updates.
- **Empresa**:
  - `empresa_id` validado cuando se proporciona (query param).
- **RBAC**:
  - `require_permission(...)` aplicado según ruta:
    - leer/crear/actualizar/asignar/resolver/cerrar.
- **Compatibilidad**:
  - No se eliminaron rutas existentes ni se cambiaron métodos.

---

*Fin del documento de implementación TKT.*

