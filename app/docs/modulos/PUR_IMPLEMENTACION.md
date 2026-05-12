# PUR — Implementación y verificación final (Compras y Abastecimiento)

Módulo: **Compras y Abastecimiento** (`PUR`)  
Alcance: cierre **Fase 3–4** según `docs/prompts/PROMPT_MODULO_MAESTRO.md`, `docs/bd/PUR_TABLAS.sql`, `app/docs/modulos/AUDITORIA_PUR.md` y ajustes posteriores de reglas de negocio (anulación de solicitud).

---

## 1) Archivos creados o modificados

### Creados

- `app/docs/modulos/AUDITORIA_PUR.md` — auditoría Fase 2 (referencia histórica).

### Modificados

**Metadatos ORM (columnas calculadas alineadas a BD)**

- `app/infrastructure/database/tables_erp/tables_pur.py` — columnas `Computed(..., persisted=True)` en detalles: `pur_solicitud_compra_detalle`, `pur_cotizacion_detalle`, `pur_orden_compra_detalle`, `pur_recepcion_detalle`.

**Queries**

- `app/infrastructure/database/queries/pur/solicitud_queries.py` — `update_solicitud_anular` (`UPDATE` condicional por estados anulables).
- `app/infrastructure/database/queries/pur/solicitud_detalle_queries.py`, `cotizacion_detalle_queries.py`, `orden_compra_detalle_queries.py`, `recepcion_detalle_queries.py` — exclusión de columnas computadas en escritura (`_WRITABLE_COLUMNS`).
- `app/infrastructure/database/queries/pur/__init__.py` — export de `update_solicitud_anular`.

**Servicios**

- `app/modules/pur/application/services/solicitud_service.py` — validación de `PUT` por estado; `marcar_procesada` solo desde `aprobada`; `anular_solicitud_servicio` con lista blanca de estados + verificación post-`UPDATE`; uso de `update_solicitud_anular`.
- `app/modules/pur/application/services/cotizacion_service.py` — `PUT` solo en `pendiente`; `aceptar_cotizacion_servicio`, `rechazar_cotizacion_servicio`.
- `app/modules/pur/application/services/orden_compra_service.py` — `PUT` solo en `borrador`; `anular` con restricción de estados y `fecha_anulacion`; `emitir_orden_compra_servicio`; `aprobar` desde `borrador` o `emitida`.
- `app/modules/pur/application/services/recepcion_service.py` — `PUT` solo en `borrador`; `procesar` solo en `borrador`; `anular_recepcion_servicio`, `aprobar_recepcion_servicio`.
- `app/modules/pur/application/services/proveedor_service.py`, `contacto_service.py`, `producto_proveedor_service.py` — `reactivar_*_servicio`.

**Presentation**

- `app/modules/pur/presentation/schemas.py` — bodies tipados (`PurMotivoRechazoBody`, `PurMotivoAnulacionBody`, `SolicitudAnularBody`); campos opcionales de columnas calculadas en `*Read` de detalles.
- `app/modules/pur/presentation/endpoints_solicitudes.py` — `POST …/anular`; bodies tipados; `GET /{id}` al final; manejo `ValueError` en `PUT` y `marcar-procesada`.
- `app/modules/pur/presentation/endpoints_ordenes_compra.py` — `POST …/emitir`; body tipado en `anular`; `GET /{id}` al final; `ValueError` en `PUT`.
- `app/modules/pur/presentation/endpoints_recepciones.py` — `POST …/anular`, `POST …/aprobar`; `GET /{id}` al final; `ValueError` en `PUT` y `procesar`.
- `app/modules/pur/presentation/endpoints_cotizaciones.py` — `POST …/aceptar`, `POST …/rechazar`; `GET /{id}` al final; `ValueError` en `PUT`.
- `app/modules/pur/presentation/endpoints_proveedores.py`, `endpoints_contactos.py`, `endpoints_productos_proveedor.py` — `POST …/reactivar`.

**Seeds / documentación SQL**

- `app/docs/database/SEED_PERMISOS_RBAC_PUR.sql` — nota aclarando que rutas nuevas reutilizan permisos `pur.*` ya sembrados.

---

## 2) Endpoints nuevos — `cliente_id`, `empresa_id` y RBAC

Convención: `client_id = current_user.cliente_id` en todos los handlers; permisos con `require_permission("pur.<recurso>.<accion>")`.  
Las cabeceras y detalles que tienen `empresa_id` en tabla siguen validándose en servicios/queries según el patrón ya existente (body o filtros de listado).

| Ruta (prefijo `/pur`) | Método | RBAC | `cliente_id` | `empresa_id` |
|---|---|---|---|---|
| `/solicitudes/{id}/anular` | POST | `pur.solicitud.actualizar` | Sí (servicio → queries) | Coherente con fila (cabecera con `empresa_id` en BD) |
| `/ordenes-compra/{id}/emitir` | POST | `pur.orden_compra.actualizar` | Sí | Idem cabecera OC |
| `/recepciones/{id}/anular` | POST | `pur.recepcion.actualizar` | Sí | Idem cabecera recepción |
| `/recepciones/{id}/aprobar` | POST | `pur.recepcion.actualizar` | Sí | Idem |
| `/cotizaciones/{id}/aceptar` | POST | `pur.cotizacion.actualizar` | Sí | Idem cabecera cotización |
| `/cotizaciones/{id}/rechazar` | POST | `pur.cotizacion.actualizar` | Sí | Idem |
| `/proveedores/{id}/reactivar` | POST | `pur.proveedor.actualizar` | Sí | Tabla con `empresa_id` en fila |
| `/contactos/{id}/reactivar` | POST | `pur.contacto.actualizar` | Sí | Detalle de proveedor (sin `empresa_id` en tabla contacto) |
| `/productos-proveedor/{id}/reactivar` | POST | `pur.producto_proveedor.actualizar` | Sí | Tabla sin `empresa_id`; tenant por `cliente_id` |

**Endpoints existentes reforzados (misma ruta y método HTTP):**

- Cuerpos **tipados** en lugar de `dict` libre donde aplica: `rechazar` solicitud (`PurMotivoRechazoBody`), `anular` OC (`PurMotivoAnulacionBody`). JSON `{}` sigue siendo válido (valores por defecto).
- Validaciones de **estado** en `PUT` de cabeceras y en acciones (`aprobar`, `anular`, `marcar-procesada`, `emitir`, `procesar`, etc.) sin cambiar paths ni verbos.

---

## 3) Verificación de contratos (OpenAPI / clientes)

- **Rutas y métodos** de los endpoints que ya existían se mantienen (mismos paths y verbos para CRUD y acciones previas).
- **Reordenación de rutas:** los `GET /{id}` de solicitudes, cotizaciones, órdenes de compra y recepciones se declararon **al final** del router para no interferir con subrutas (`/aprobar`, `/transaccional`, etc.). El contrato de URL no cambia.
- **Cambios intencionados compatibles hacia atrás:**
  - Bodies de **rechazar solicitud** y **anular OC** pasan a modelos Pydantic con `extra="ignore"` y campos opcionales por defecto; los clientes que enviaban el mismo JSON siguen funcionando.
  - **Responses** de detalle pueden incluir **columnas calculadas** (`total_referencial`, `precio_neto`, etc.) cuando la BD y el `SELECT` las devuelven (metadatos `tables_pur` + queries con `select(Tabla)`).

No se eliminó código de endpoints anteriores; solo se añadieron rutas y reglas en servicios.

---

## 4) RBAC — permisos y despliegue

Códigos usados por el backend (sin nuevos códigos para las rutas POST añadidas):

- `pur.proveedor.*` | `pur.contacto.*` | `pur.producto_proveedor.*`
- `pur.solicitud.*` | `pur.cotizacion.*` | `pur.orden_compra.*` | `pur.recepcion.*`

Ejecutar en la **BD central de RBAC** el script `app/docs/database/SEED_PERMISOS_RBAC_PUR.sql` (tras existir el módulo PUR con `modulo_id` `E1000005-0000-4000-8000-000000000005`). Las rutas nuevas usan los mismos `*.actualizar` / `*.crear` ya definidos en ese seed.

---

## 5) Reglas de negocio destacadas (cierre técnico)

| Área | Comportamiento |
|------|------------------|
| **Solicitud — anular** | Solo desde estados `borrador`, `pendiente_aprobacion`, `aprobada`. Bloqueado si `procesada`, `rechazada` o `anulada`. `UPDATE` atómico con `WHERE LOWER(estado) IN (...)` y comprobación de que la fila quedó en `anulada`. |
| **Solicitud — PUT** | Solo editable en `borrador` o `pendiente_aprobacion`. |
| **Solicitud — marcar procesada** | Solo si estado `aprobada`. |
| **Cotización — PUT** | Solo si estado `pendiente`. |
| **Cotización — lifecycle ampliado** | Se implementó `POST /cotizaciones/{id}/aceptar` y `POST /cotizaciones/{id}/rechazar`. Los estados `recibida`, `evaluada` y `vencida` existen en `PUR_TABLAS.sql` y en validaciones de creación transaccional, pero **no tienen uso real adicional en el backend** (no hay endpoints/servicios dedicados que los transicionen). Por decisión técnica, el lifecycle expuesto queda **intencionalmente acotado** a `pendiente → aceptada/rechazada` (más `marcar-ganadora` cuando aplica). |
| **OC — PUT** | Solo en `borrador`. |
| **OC — emitir / aprobar** | Emitir: solo desde `borrador`. Aprobar: desde `borrador` o `emitida`. |
| **OC — anular** | No si `completa` o `anulada`; se registra `fecha_anulacion`. |
| **Recepción — PUT / procesar** | Solo en `borrador` para edición y proceso. |
| **Recepción — anular / aprobar** | Anular: no si `procesada` o `anulada`. Aprobar: solo desde `inspeccion`. |
| **Maestros** | `POST …/reactivar` para proveedor, contacto y producto-proveedor (`es_activo`, y `estado` operativo en proveedor). |
| **Detalle (líneas) — estado cabecera** | Para evitar inconsistencia documental, `CREATE/UPDATE` de líneas queda bloqueado cuando la cabecera no está editable: solicitud (`borrador|pendiente_aprobacion`), cotización (`pendiente`), OC (`borrador`), recepción (`borrador`). |

---

## 6) Cierre del módulo (estado)

- **PUR queda cerrado** para el alcance acordado en esta iteración: consistencia transaccional en cabeceras, anulación segura de solicitud (servicio + query), endpoints nuevos mínimos, bodies tipados, columnas calculadas en metadatos y lecturas de detalle, reactivación de maestros, seeds RBAC documentados y auditoría previa en `AUDITORIA_PUR.md`.
- **Prerequisito de BD:** las tablas de detalle deben coincidir con `docs/bd/PUR_TABLAS.sql` (incluidas columnas **persistidas calculadas**). Si una base aún no las tiene, alinear DDL fuera de este repositorio antes de desplegar la versión de API que asume esas columnas en el `SELECT`.

Para ampliaciones futuras (p. ej. bloquear anulación de solicitud **aprobada** si ya existe OC no anulada, o máquina de estados de cotización más estricta), conviene nueva iteración explícita de análisis y contrato con front/consumidores.
