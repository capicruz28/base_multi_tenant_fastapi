# Implementación SVC — Gestión de Servicios

Documento final generado tras completar **Fase 3** del módulo **SVC**.

Referencia BD: `docs/bd/SVC_TABLAS.sql` (tabla `svc_orden_servicio`).

---

## 1. Alcance implementado

- **Entidad**: `svc_orden_servicio`
- **Objetivo**:
  - Mantener rutas existentes sin romper contrato.
  - Endurecer reglas de negocio en actualización (PUT) por estado.
  - Implementar **transiciones de estado** por endpoints dedicados:
    - **asignar**: `solicitada` → `asignada` (setea `tecnico_asignado_usuario_id`)
    - **iniciar**: `asignada` → `en_proceso` (setea `fecha_inicio_real`)
    - **completar**: `en_proceso` → `completada` (setea `fecha_fin_real`)
    - **cancelar**: `solicitada` o `asignada` → `cancelada`
  - Agregar validación **opcional** por `empresa_id` en **GET/PUT por ID** (scope multi-empresa dentro del mismo `cliente_id`).

---

## 2. Endpoints (API v1)

Base router: `/api/v1/svc` (según `settings.API_V1_STR` y `app/api/v1/api.py`).

### 2.1 Endpoints existentes (se mantienen)

- `GET /ordenes-servicio`
  - **Tenant**: filtra por `cliente_id` del usuario autenticado.
  - **Empresa**: filtro opcional `empresa_id` (query param).
  - **RBAC**: `svc.orden_servicio.leer`.

- `GET /ordenes-servicio/{orden_servicio_id}`
  - **Empresa**: `empresa_id` opcional (query param) para acotar el recurso.
  - **RBAC**: `svc.orden_servicio.leer`.

- `POST /ordenes-servicio`
  - **Tenant**: `cliente_id` forzado desde el usuario autenticado.
  - **Empresa**: `empresa_id` en body (schema existente).
  - **RBAC**: `svc.orden_servicio.crear`.

- `PUT /ordenes-servicio/{orden_servicio_id}`
  - **Empresa**: `empresa_id` opcional (query param) para acotar el recurso.
  - **Regla de estado**: **solo editable** si `estado` actual es `solicitada` o `asignada`.
  - **Cambio de estado**: bloqueado en `PUT` (debe hacerse con endpoints de transición).
  - **RBAC**: `svc.orden_servicio.actualizar`.

### 2.2 Endpoints nuevos (transiciones de estado)

- `POST /ordenes-servicio/{orden_servicio_id}/asignar`
  - Body: `tecnico_asignado_usuario_id`
  - Transición: `solicitada` → `asignada`
  - **RBAC**: `svc.orden_servicio.actualizar`

- `POST /ordenes-servicio/{orden_servicio_id}/iniciar`
  - Transición: `asignada` → `en_proceso`
  - Set: `fecha_inicio_real = utcnow`
  - **RBAC**: `svc.orden_servicio.actualizar`

- `POST /ordenes-servicio/{orden_servicio_id}/completar`
  - Transición: `en_proceso` → `completada`
  - Set: `fecha_fin_real = utcnow`
  - **RBAC**: `svc.orden_servicio.actualizar`

- `POST /ordenes-servicio/{orden_servicio_id}/cancelar`
  - Transición: `solicitada|asignada` → `cancelada`
  - **RBAC**: `svc.orden_servicio.cancelar`

Notas:
- Las transiciones fueron implementadas de forma **idempotente** para el estado objetivo (si ya está en el estado final, responde el recurso actual).
- En operaciones que fallan por regla de negocio, se responde con error de validación (400) usando el esquema de excepciones del proyecto.

---

## 3. Multi-tenant (cliente/empresa)

- **cliente_id**:
  - Se usa en todas las operaciones (lectura/creación/actualización) como criterio de aislamiento tenant.
  - Proviene del usuario autenticado (`current_user.cliente_id`).

- **empresa_id**:
  - `GET /ordenes-servicio`: filtro opcional existente.
  - `GET/PUT/transiciones por ID`: se agregó soporte de filtro opcional por `empresa_id` (query param).

---

## 4. RBAC

Permisos utilizados por el módulo:

- `svc.orden_servicio.leer`
- `svc.orden_servicio.crear`
- `svc.orden_servicio.actualizar`
- `svc.orden_servicio.cancelar`

Seed agregado:
- `app/docs/database/SEED_PERMISOS_RBAC_SVC.sql` (idempotente vía `MERGE`, módulo SVC id `E1000016-0000-4000-8000-000000000016`).

---

## 5. Archivos modificados/creados

### Modificados

- `app/infrastructure/database/queries/svc/orden_servicio_queries.py`
- `app/infrastructure/database/queries/svc/__init__.py`
- `app/modules/svc/application/services/orden_servicio_service.py`
- `app/modules/svc/application/services/__init__.py`
- `app/modules/svc/presentation/endpoints_orden_servicio.py`

### Creados

- `app/docs/database/SEED_PERMISOS_RBAC_SVC.sql`
- `app/docs/modulos/SVC_IMPLEMENTACION.md`

---

## 6. Verificación final (checklist)

Para cada endpoint nuevo/ajustado (GET/PUT por ID + transiciones) se verifica:

- **Tenant**:
  - `cliente_id` aplicado en queries/updates.
- **Empresa**:
  - `empresa_id` validado cuando se proporciona (query param).
- **RBAC**:
  - `require_permission(...)` aplicado:
    - leer/crear/actualizar/cancelar según corresponda.
- **Compatibilidad**:
  - No se eliminaron rutas existentes ni se cambiaron métodos.

---

*Fin del documento de implementación SVC.*

