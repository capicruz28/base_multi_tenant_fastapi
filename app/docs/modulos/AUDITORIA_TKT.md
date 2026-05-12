# Auditoría TKT — Mesa de Ayuda (Ticketing)

Documento generado en **Fase 2** del prompt maestro. Referencia BD filtrada: `docs/bd/TKT_TABLAS.sql` (tabla `tkt_ticket`).

---

## 1. Tablas detectadas y tipo

| Tabla         | Tipo (Fase 1)                    | Notas breves |
|--------------|----------------------------------|-------------|
| `tkt_ticket` | Transaccional (ciclo de vida)    | `estado`, asignación (`asignado_usuario_id`/`fecha_asignacion`), resolución (`fecha_resolucion`/`solucion`). Sin `es_activo`. `tiempo_resolucion_horas` es **columna calculada** en BD. |

---

## 2. Implementación actual (archivos)

| Capa / rol              | Rutas relativas |
|-------------------------|-----------------|
| Routers incluidos       | `app/modules/tkt/presentation/endpoints.py`, `endpoints_ticket.py` |
| Schemas                 | `app/modules/tkt/presentation/schemas.py` |
| Servicios aplicación    | `app/modules/tkt/application/services/ticket_service.py`, `services/__init__.py` |
| Persistencia SQL (Core) | `app/infrastructure/database/queries/tkt/ticket_queries.py`, `tables_erp/tables_tkt.py` |
| Repositories dedicados  | **No existe** capa `*repository*`; el servicio delega en `ticket_queries`. |
| Montaje API v1          | `app/api/v1/api.py`: `tkt_endpoints.router` con `prefix="/tkt"` |

Prefijo OpenAPI efectivo asumiendo `settings.API_V1_STR` habitual (`/api/v1`): base **`/api/v1/tkt`**, recurso tickets **`/tickets`**.

---

## 3. Endpoints existentes

| Ruta completa efectiva\* | Método | Entidad       | Tenant (`cliente_id`) | Tenant (`empresa_id`) | RBAC declarado |
|--------------------------|--------|---------------|------------------------|------------------------|---------------|
| `/api/v1/tkt/tickets` | `GET` | `tkt_ticket` | Sí (`current_user.cliente_id` → queries) | **Opcional** (`empresa_id` query param, aplicado en `list_ticket`) | `Depends(require_permission("tkt.ticket.leer"))` |
| `/api/v1/tkt/tickets/{ticket_id}` | `GET` | `tkt_ticket` | Sí (`WHERE cliente_id`) | **No** (no recibe `empresa_id`, query no filtra por empresa) | `tkt.ticket.leer` |
| `/api/v1/tkt/tickets` | `POST` | `tkt_ticket` | Sí (`cliente_id` forzado en insert) | **Sí** (obligatorio en body `TicketCreate.empresa_id`) | `tkt.ticket.crear` |
| `/api/v1/tkt/tickets/{ticket_id}` | `PUT` | `tkt_ticket` | Sí (`WHERE cliente_id`) | **No** (no recibe `empresa_id`, query no filtra por empresa) | `tkt.ticket.actualizar` |

\*Ruta efectiva relativa al host: `{API_V1_STR}/tkt/tickets`.

Notas **`empresa_id`**:

- **Listado (`GET` colección):** filtro opcional por query `empresa_id` en endpoint → service → query.
- **Detalle (`GET` por id) y actualización (`PUT`):** solo garantizan pertenencia al **tenant (`cliente_id`)**; no acotan por **`empresa_id`** a pesar de existir en tabla (`tkt_ticket.empresa_id`).

---

## 4. Brechas funcionales vs patrón maestro / transaccional / derivado

### 4.1 Transaccional (plantilla prompt maestro: borrador, aprobar, procesar, anular, listar, detalle)

| Esperado (plantilla) | Estado actual |
|----------------------|--------------|
| Crear (“borrador” / estado inicial controlado) | **Parcial:** existe `POST`; pero `TicketCreate.estado` permite enviar estado arbitrario (default `abierto`) sin reglas. |
| Actualizar solo estados editables | **Falta:** `PUT` no valida `estado` (ni restringe por estado) y `TicketUpdate` permite modificar `estado`, `fecha_resolucion`, `solucion`, `fecha_asignacion`, `asignado_usuario_id` sin transición dedicada. |
| Aprobar / procesar (transiciones explícitas) | **Falta** endpoints de transición (p. ej. asignar/en_proceso/resolver/cerrar) pese a existir columnas para ciclo de vida. |
| Anular | **Falta** transición dedicada (en BD no hay `es_activo`; se esperaría anulación por `estado`). |
| Listar / detalle | **Cubierto** (`GET`) |

### 4.2 Patrón maestro (activar/desactivar, `es_activo`)

- **No aplica literalmente:** `tkt_ticket` no tiene `es_activo`; el “cierre/cancelación” debería expresarse por `estado` (y reglas de transición), no por borrado físico.

### 4.3 Tablas derivadas / analíticas

- No hay tablas derivadas separadas en `TKT_TABLAS.sql`.  
- Sí existe **columna calculada** `tiempo_resolucion_horas` en BD; no debería tener escritura directa.

---

## 5. Campos BD vs schemas (Brecha de exposición)

Columnas **`tkt_ticket`** (`docs/bd/TKT_TABLAS.sql`):  
`ticket_id`, `cliente_id`, `empresa_id`, `numero_ticket`, `fecha_creacion`, `solicitante_usuario_id`, `solicitante_nombre`, `solicitante_email`, `asunto`, `descripcion`, `categoria`, `prioridad`, `asignado_usuario_id`, `fecha_asignacion`, `estado`, `fecha_resolucion`, `tiempo_resolucion_horas` (calculada), `solucion`.

### Por schema

| Schema | Coincidencia respecto BD | Campos que existen en BD y **no** están en el schema (impacto práctico) |
|--------|--------------------------|--------------------------------------------|
| `TicketRead` | Cubre todas las columnas **excepto** que `tiempo_resolucion_horas` se expone como `float` y se calcula en servicio | N/A |
| `TicketCreate` | Omite PK, `cliente_id`, `fecha_creacion` (correcto) | N/A |
| `TicketUpdate` | Permite actualización parcial de la mayoría de campos | N/A |

**Observación importante** (`tiempo_resolucion_horas`):

- En BD es **columna calculada** persistida; en `tables_erp/tables_tkt.py` no aparece como columna, y en servicio se **recalcula** a partir de fechas para poblar `TicketRead.tiempo_resolucion_horas`. Esto funciona para la API, pero queda **desalineado** respecto a la definición exacta de BD (DATEDIFF en horas vs cálculo en horas con decimales redondeado).

---

## 6. Permisos RBAC y seeds

Códigos usados en rutas:

- `tkt.ticket.leer`
- `tkt.ticket.crear`
- `tkt.ticket.actualizar`

**Hallazgo:** no se localizaron scripts `SEED_PERMISOS_RBAC_TKT*.sql` ni referencias a `tkt.ticket.*` en los seeds de permisos del repo (búsqueda por `tkt.`).  
**Riesgo:** los permisos declarados en endpoints podrían no estar asignados a roles por defecto, dependiendo del proceso de instalación.

---

## 7. Problemas / observaciones (sin eliminar código)

| Tema | Severidad | Comentario |
|------|-----------|------------|
| Validación de `empresa_id` en `GET /{ticket_id}` y `PUT /{ticket_id}` | Media | La tabla tiene `empresa_id`, pero el detalle/update solo filtran por `cliente_id`. En cliente multi-empresa puede permitir acceso cruzado dentro del mismo `cliente_id` si se conoce el UUID del ticket. |
| Ciclo de vida no encapsulado en transiciones | Media | `estado` es editable por `POST`/`PUT` sin reglas; faltan endpoints de transición si se desea controlar el flujo (`abierto` → `asignado` → `en_proceso` → `resuelto` → `cerrado`). |
| Cálculo `tiempo_resolucion_horas` (BD vs API) | Baja | API calcula decimal redondeado; BD calcula entero por DATEDIFF(HOUR). Puede causar discrepancias si se compara con reporte directo BD. |
| Soft delete (`es_activo`) | N/A | No existe en BD; no corresponde “desactivar” por bandera. |

No se marca código como **obsoleto para borrar** conforme prompt maestro: **no eliminar** código en esta fase.

---

## 8. Endpoints sugeridos (solo si negocio / Fase 3 lo aprueba)

Los endpoints existentes deben mantener contrato estable; los siguientes son **complementarios** sólo tras definición funcional:

| Ruta sugerida (relativa tras `/api/v1/tkt`) | Método | Motivo |
|--------------------------------------------|--------|--------|
| `/tickets/{ticket_id}` (ajuste interno) | `GET`, `PUT` | Aceptar `empresa_id` opcional/obligatorio y filtrar por empresa en queries para reforzar multi-empresa dentro del tenant |
| `/tickets/{ticket_id}/asignar` | `POST` | Encapsular asignación (`asignado_usuario_id`, `fecha_asignacion`) como transición |
| `/tickets/{ticket_id}/iniciar` | `POST` | Transición a `en_proceso` |
| `/tickets/{ticket_id}/resolver` | `POST` | Set `fecha_resolucion`/`solucion` y transición a `resuelto` |
| `/tickets/{ticket_id}/cerrar` | `POST` | Transición final a `cerrado` |

---

## 9. Resumen ejecutivo

- **Tablas `tkt_*` en alcance BD adjunta:** 1 (`tkt_ticket`).
- **Operaciones presentes:** listar (`GET`), detalle (`GET` id), crear (`POST`), actualizar (`PUT`) con **`cliente_id`** en filtros/insert y **`require_permission`** en todas las rutas auditadas.
- **Gaps principales:** validación **`empresa_id`** no aplicada en detalle/update; falta encapsular ciclo transaccional con transiciones; discrepancia menor en cálculo de `tiempo_resolucion_horas` (BD vs API); seeds RBAC TKT no localizados.

---

*Fin del informe Fase 2.*

⛔ **Detente aquí hasta confirmación** para iniciar **Fase 3** (implementación según alcance aprobado).

