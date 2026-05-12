# Auditoría SVC — Gestión de Servicios

Documento generado en **Fase 2** del prompt maestro. Referencia BD filtrada: `docs/bd/SVC_TABLAS.sql` (tabla `svc_orden_servicio`).

---

## 1. Tablas detectadas y tipo

| Tabla               | Tipo (Fase 1)              | Notas breves                                                |
|--------------------|----------------------------|-------------------------------------------------------------|
| `svc_orden_servicio` | Transaccional (ciclo de vida) | `estado` con valores documentados en comentarios SQL (`solicitada`, `asignada`, `en_proceso`, `completada`, `cancelada`). Sin `es_activo`. |

---

## 2. Implementación actual (archivos)

| Capa / rol            | Rutas relativas                                                                              |
|-----------------------|----------------------------------------------------------------------------------------------|
| Routers incluidos     | `app/modules/svc/presentation/endpoints.py`, `endpoints_orden_servicio.py`                   |
| Schemas               | `app/modules/svc/presentation/schemas.py`                                                    |
| Servicios aplicación  | `app/modules/svc/application/services/orden_servicio_service.py`, `services/__init__.py`       |
| Persistencia SQL (Core) | `app/infrastructure/database/queries/svc/orden_servicio_queries.py`, `tables_erp/tables_svc.py` |
| Repositories dedicados | **No existe** capa `*repository*`; el servicio delega en `orden_servicio_queries`.          |
| Montaje API v1        | `app/api/v1/api.py`: `svc_endpoints.router` con `prefix="/svc"`                               |

Prefijo OpenAPI efectivo asumiendo `settings.API_V1_STR` habitual (`/api/v1`): base **`/api/v1/svc`**, recurso órdenes **`/ordenes-servicio`**.

---

## 3. Endpoints existentes

| Ruta completa efectiva\* | Método | Entidad           | Tenant (`cliente_id`) | RBAC declarado                                      |
|--------------------------|--------|-------------------|------------------------|-----------------------------------------------------|
| `/api/v1/svc/ordenes-servicio` | `GET`  | `svc_orden_servicio` | Sí (`current_user.cliente_id` → queries) | `Depends(require_permission("svc.orden_servicio.leer"))` |
| `/api/v1/svc/ordenes-servicio/{orden_servicio_id}` | `GET` | `svc_orden_servicio` | Sí (`WHERE cliente_id`)                  | `svc.orden_servicio.leer`                            |
| `/api/v1/svc/ordenes-servicio` | `POST` | `svc_orden_servicio` | Sí (`cliente_id` forzado en insert)      | `svc.orden_servicio.crear`                         |
| `/api/v1/svc/ordenes-servicio/{orden_servicio_id}` | `PUT` | `svc_orden_servicio` | Sí (`WHERE cliente_id`)                  | `svc.orden_servicio.actualizar`                    |

\*Ruta efectiva relativa al host: `{API_V1_STR}/svc/ordenes-servicio`.

Notas **`empresa_id`**:

- **Listado (`GET` colección):** filtro opcional por query `empresa_id` en servicio/query.
- **Detalle (`GET` por id) y actualización (`PUT`):** sólo garantizan pertenencia al **tenant (`cliente_id`)**. No reciben `empresa_id` en query/path para acotar a una empresa dentro del mismo cliente (riesgo dentro de cliente multi-empresa si se adivina/el UUID cruza empresa).
- **Crear (`POST`):** `empresa_id` obligatorio en body (`OrdenServicioCreate`).

Notas **`get_current_active_user`:**

- Todas las rutas usan `Depends(get_current_active_user)` y además `require_permission`; patrón explícito y coherente con otros módulos.

---

## 4. Brechas funcionales vs patrón maestro / transaccional / derivado

### 4.1 Transaccional (plantilla prompt maestro: borrador, aprobar, procesar, anular, listar, detalle)

| Esperado                                      | Estado actual                                                                 |
|-----------------------------------------------|-------------------------------------------------------------------------------|
| Crear (“borrador” / estado inicial editable) | **Parcial:** `POST` crea orden; estado inicial típico **solicitada** permitido desde body (`OrdenServicioCreate.estado` opcional, default solicitada). No hay modelo “borrador” separado en BD adjunta |
| Actualizar sólo estados editables (“borrador”) | **Falta / desalineación:** `PUT` no restringe por `estado`; **cualquier** estado puede modificarse mediante campos opcionales. No garantiza ciclo solicitada → … → cancelada/completada de forma guiada |
| Aprobar                                      | **Falta** endpoint dedicado o transición específica (no hay columna de aprobación en script SVC adjunto)
| Procesar                                     | **Falta** endpoint dedicado o transiciones atómicas (p.ej. iniciar trabajo, cerrar orden)
| Anular                                       | **Parcial informal:** sólo si el cliente usa `PUT` con `estado=cancelada` sin reglas centralizadas
| Listar / detalle                             | **Cubierto** (`GET`)

### 4.2 Patrón maestro (activar/desactivar, `es_activo`)

- **No aplica literalmente:** `svc_orden_servicio` en `docs/bd/SVC_TABLAS.sql` **no define** `es_activo`. La cancelación/anulación funcional debe apoyarse en **`estado`** (p. ej. `cancelada`) con reglas explícitas vía endpoints o negocio en servicio.

### 4.3 Tablas derivadas / analíticas

Ninguna en alcance `SVC_TABLAS.sql` (prefijo `svc_` único objeto).

---

## 5. Campos BD vs schemas (Brecha de exposición)

Columnas **`svc_orden_servicio`** (`docs/bd/SVC_TABLAS.sql`):  
`orden_servicio_id`, `cliente_id`, `empresa_id`, `numero_os`, `fecha_solicitud`, `cliente_venta_id`, `tipo_servicio`, `descripcion_servicio`, `tecnico_asignado_usuario_id`, `fecha_inicio_programada`, `fecha_inicio_real`, `fecha_fin_real`, `estado`, `monto_servicio`, `fecha_creacion`.

### Por schema

| Schema              | Coincidencia respecto BD | Campos que existen en BD y **no** están en el schema (impacto práctico)                          |
|---------------------|--------------------------|---------------------------------------------------------------------------------------------------|
| `OrdenServicioRead` | Cubre todas las columnas listadas para respuesta cliente | **Ninguno** faltante en alcance tabla adjunta                                                       |
| `OrdenServicioCreate` | Omite PK, `cliente_id`, `fecha_creacion` (correcto) | N/A                                                                             |
| `OrdenServicioUpdate` | Parcial opcional (`exclude_none`) | **`empresa_id`**: existe en BD; **no está** en `OrdenServicioUpdate` → no hay forma oficial vía PUT de reasignar/mover orden a otra empresa (puede ser decisión válida si la empresa es inmutable) |

No hay en BD otros campos de la tabla objetivo omitidos por `OrdenServicioRead` dentro del alcance declarado del script adjunto.

---

## 6. Permisos RBAC y seeds

Códigos usados en rutas:

- `svc.orden_servicio.leer`
- `svc.orden_servicio.crear`
- `svc.orden_servicio.actualizar`

**Hallazgo:** en `app/docs/database/` **no se localizaron** líneas ni script dedicado (p. ej. `SEED_PERMISOS_RBAC_SVC.sql`) que inserten códigos con prefijo `svc.` tras búsqueda en los `SEED_PERMISOS*.sql` del repositorio. **Riesgo:** roles estándar podrían no tener estos permisos asignados (según proceso de instalación del tenant).

**Sugerencia Fase 3:** añadir seeds alineados con `[modulo].[recurso].[accion]` y cualquier permiso adicional necesario si se exponen nuevas transiciones (p. ej. `svc.orden_servicio.anular`), sin romper rutas/contratos actuales hasta acuerdo funcional explícito.

---

## 7. Problemas / observaciones (sin eliminar código)

| Tema                                                             | Severidad | Comentario                                                                 |
|------------------------------------------------------------------|-----------|----------------------------------------------------------------------------|
| Validación opcional/forzosa de `empresa_id` en GET/PUT por id   | Media     | Tabla tiene `empresa_id`; reglas internas piden validar empresa cuando aplique |
| Actualización abierta cualquier estado                          | Media     | Esperable en transacciones con ciclo cerrar ordenes con reglas por `estado` |
| Seeds RBAC SVC                                                   | Media     | Permisos referenciados en código pueden no estar sembrados en BD          |
| Transacciones SQL cabecera+detalle                              | Baja / N/A| En alcance sólo tabla cabecera; no hay tabla detalle en `SVC_TABLAS.sql`  |
| Capa “repository”                                                | Baja      | Igual que otros módulos: servicio + `*_queries`                          |

No se marca código como **obsoleto para borrar** conforme prompt maestro: **no eliminar** código en esta fase.

---

## 8. Endpoints sugeridos (solo si negocio / Fase 3 lo aprueba)

Las rutas y métodos existentes deben mantener contrato estable; los siguientes son **complementarios** sólo tras definición funcional:

| Ruta sugerida (relativa tras `/api/v1/svc`) | Método     | Motivo                                                                 |
|-------------------------------------------|------------|------------------------------------------------------------------------|
| `/ordenes-servicio/{id}`                  | `GET`, `PUT` | Incluir `empresa_id` opcional/obligatorio en query para auditar empresa dentro del tenant |
| `/ordenes-servicio/{id}/cancelar` (o `/anular`) | `POST`     | Encapsular cambio seguro de estado a cancelada/anulación lógica         |
| `/ordenes-servicio/{id}/...`               | `POST` / `PATCH` | Transiciones explícitas: asignar técnico, iniciar proceso, completar, según modelo de estado SQL |

\*Nombres y verbos sólo ejemplares; debe alinearse con OpenAPI futuro sin romper rutas vigentes hasta acuerdo.

---

## 9. Resumen ejecutivo

- **Tablas `svc_*` en alcance BD adjunta:** 1 (`svc_orden_servicio`).
- **Operaciones presentes:** listar (`GET`), detalle (`GET` id), crear (`POST`), actualizar (`PUT`) con **`cliente_id`** en filtros/create y **`require_permission`** en todas las rutas auditadas.
- **Gaps principales:** ciclo **transaccional** no modelado como en plantilla prompt (aprobar/procesar/anular explícitos, updates condicionados por estado); **`empresa_id`** no aplicado uniformemente en detalle/update por id; **seeds RBAC SVC** no localizados en scripts SQL revisados del repo; **`empresa_id`** ausente en **`OrdenServicioUpdate`** (evitar cambio empresa o exponer deliberadamente en Fase 3).

---

*Fin del informe Fase 2.*

⛔ **Detente aquí hasta confirmación** para iniciar **Fase 3** (implementación según alcance aprobado).
