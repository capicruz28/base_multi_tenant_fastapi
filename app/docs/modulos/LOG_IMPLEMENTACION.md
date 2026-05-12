# IMPLEMENTACIÓN — LOG (Logística y Distribución)

Fecha: 2026-05-07

Este documento describe la implementación realizada para el módulo **LOG** siguiendo el patrón del repositorio, **sin modificar estructura de BD** ni romper contratos existentes.

## Alcance

Tablas del módulo (`log_*`) según `docs/bd/LOG_TABLAS.sql`:
- **Maestros**
  - `log_transportista`
  - `log_vehiculo`
  - `log_ruta`
- **Transaccionales**
  - `log_guia_remision` (cabecera)
  - `log_guia_remision_detalle` (detalle)
  - `log_despacho` (cabecera)
  - `log_despacho_guia` (relación)

## Arquitectura aplicada (patrón del repo)

- **Routers**: `app/modules/log/presentation/endpoints_*.py`
- **Services**: `app/modules/log/application/services/*_service.py`
- **Queries**: `app/infrastructure/database/queries/log/*_queries.py`
- **Tenant**: `cliente_id` proviene de `current_user.cliente_id` y se filtra en queries.
- **Empresa (scope)**: `empresa_id` se admite como query param opcional en operaciones por ID y se filtra cuando se informa.
- **RBAC**: `require_permission("log.<recurso>.<accion>")`
- **Baja lógica**: se usa `es_activo = 0` en tablas maestro.

## Cambios realizados (resumen)

### 1) Schemas + ORM (alineación con BD)

- **Moneda como UUID (no string)**:
  - `log_transportista.moneda_tarifa` se alinea a **UUID** en:
    - `app/modules/log/presentation/schemas.py`
    - `app/infrastructure/database/tables_erp/tables_log.py` (UNIQUEIDENTIFIER + FK a `cat_moneda.moneda_id`)
  - `log_ruta.moneda_id` se alinea a **UUID** en:
    - `app/modules/log/presentation/schemas.py`
    - `app/infrastructure/database/tables_erp/tables_log.py` (columna `moneda_id` + FK a `cat_moneda.moneda_id`)

- **Columnas calculadas expuestas en Read**:
  - `GuiaRemisionRead.numero_completo`
  - `DespachoRead.km_recorrido`
  - `DespachoRead.costo_total`

- **`empresa_id` expuesto en reads de detalle**:
  - `GuiaRemisionDetalleRead.empresa_id`
  - `DespachoGuiaRead.empresa_id`

### 2) Endurecimiento multi-tenant por empresa (opcional) en GET/PUT por ID

Se agregó soporte de `empresa_id` **opcional** para filtrar por scope en:
- `transportista`: `GET /transportistas/{id}`, `PUT /transportistas/{id}`
- `vehiculo`: `GET /vehiculos/{id}`, `PUT /vehiculos/{id}`
- `ruta`: `GET /rutas/{id}`, `PUT /rutas/{id}`
- `guia_remision`: `GET /guias-remision/{id}`, `PUT /guias-remision/{id}`
- `despacho`: `GET /despachos/{id}`, `PUT /despachos/{id}`

Implementación:
- En **queries**, los `WHERE` incluyen `empresa_id` solo si se envía.
- En **services/endpoints**, se propaga el parámetro sin alterar rutas existentes.

### 3) Validación de estado (solo editable en `borrador`)

Se restringió `PUT` para cabeceras transaccionales:
- `PUT /guias-remision/{id}` solo permite edición si `estado == "borrador"`.
- `PUT /despachos/{id}` solo permite edición si `estado == "borrador"`.

### 4) Endpoints nuevos (sin modificar los existentes)

#### Maestros — baja lógica + reactivar

Se agregaron endpoints con baja lógica (`es_activo = 0`) y reactivación:
- `DELETE /transportistas/{id}` (permiso `log.transportista.eliminar`)
- `POST /transportistas/{id}/reactivar` (permiso `log.transportista.actualizar`)

- `DELETE /vehiculos/{id}` (permiso `log.vehiculo.eliminar`)
- `POST /vehiculos/{id}/reactivar` (permiso `log.vehiculo.actualizar`)

- `DELETE /rutas/{id}` (permiso `log.ruta.eliminar`)
- `POST /rutas/{id}/reactivar` (permiso `log.ruta.actualizar`)

#### Transaccionales — transiciones explícitas

Se agregaron acciones explícitas (manteniendo `PUT` con validación de `borrador`):
- `POST /guias-remision/{id}/anular` (permiso `log.guia_remision.actualizar`)
- `POST /despachos/{id}/completar` (permiso `log.despacho.actualizar`)
- `POST /despachos/{id}/anular` (permiso `log.despacho.actualizar`)

Estados aplicados:
- Guía: `estado = "anulada"` y `fecha_anulacion` se setea al anular.
- Despacho:
  - completar: `estado = "completado"`
  - anular: `estado = "cancelado"`

## RBAC (permisos) — Seed

Se agregó el script:
- `app/docs/database/SEED_PERMISOS_RBAC_LOG.sql`

Incluye (y asegura) el set usado por el backend:
- `log.transportista.{leer,crear,actualizar,eliminar}`
- `log.vehiculo.{leer,crear,actualizar,eliminar}`
- `log.ruta.{leer,crear,actualizar,eliminar}`
- `log.guia_remision.{leer,crear,actualizar}`
- `log.despacho.{leer,crear,actualizar}`
- sub-recursos:
  - `log.guia_remision_detalle.{leer,crear,actualizar}`
  - `log.despacho_guia.{leer,crear,actualizar}`

## Archivos principales modificados/creados

- **Schemas/ORM**
  - `app/modules/log/presentation/schemas.py`
  - `app/infrastructure/database/tables_erp/tables_log.py`
- **Queries**
  - `app/infrastructure/database/queries/log/transportista_queries.py`
  - `app/infrastructure/database/queries/log/vehiculo_queries.py`
  - `app/infrastructure/database/queries/log/ruta_queries.py`
  - `app/infrastructure/database/queries/log/guia_remision_queries.py`
  - `app/infrastructure/database/queries/log/despacho_queries.py`
  - `app/infrastructure/database/queries/log/__init__.py`
- **Services**
  - `app/modules/log/application/services/transportista_service.py`
  - `app/modules/log/application/services/vehiculo_service.py`
  - `app/modules/log/application/services/ruta_service.py`
  - `app/modules/log/application/services/guia_remision_service.py`
  - `app/modules/log/application/services/despacho_service.py`
  - `app/modules/log/application/services/__init__.py`
- **Routers**
  - `app/modules/log/presentation/endpoints_transportistas.py`
  - `app/modules/log/presentation/endpoints_vehiculos.py`
  - `app/modules/log/presentation/endpoints_rutas.py`
  - `app/modules/log/presentation/endpoints_guias_remision.py`
  - `app/modules/log/presentation/endpoints_despachos.py`
- **Seeds**
  - `app/docs/database/SEED_PERMISOS_RBAC_LOG.sql` (**nuevo**)
- **Docs**
  - `app/docs/modulos/AUDITORIA_LOG.md`
  - `app/docs/modulos/LOG_IMPLEMENTACION.md` (**este documento**)

## Notas finales

- No se modificó el DDL de la BD; solo se alinearon schemas/ORM a los tipos/campos del SQL del módulo.
- No se eliminaron ni cambiaron rutas existentes; las rutas nuevas son aditivas.
- Todas las queries filtran por `cliente_id`; `empresa_id` se aplica como scope **cuando se informa**.

