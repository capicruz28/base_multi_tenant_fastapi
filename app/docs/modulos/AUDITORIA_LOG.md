# AUDITORIA — Módulo LOG (Logística y Distribución)

Fecha: 2026-05-07

Este documento audita **implementación backend** del módulo `LOG` contra la BD del módulo en `docs/bd/LOG_TABLAS.sql`.

Reglas auditadas (del prompt maestro):
- No cambiar contratos existentes.
- Multi-tenant: **siempre** validar `cliente_id` y `empresa_id` cuando aplique.
- RBAC: permiso con patrón `log.<recurso>.<accion>`.
- Maestros: crear/listar/detalle/actualizar + activar/desactivar (baja lógica `es_activo=0`).
- Transaccionales: crear(borrador), actualizar(solo borrador), aprobar/procesar/anular (según aplique), listar/detalle.

---

## 1) Tablas detectadas y tipo

Fuente: `docs/bd/LOG_TABLAS.sql` (prefijo `LOG_` / `log_`)

### Maestros
- `log_transportista` (tiene `cliente_id`, `empresa_id`, `es_activo`)
- `log_vehiculo` (tiene `cliente_id`, `empresa_id`, `es_activo`)
- `log_ruta` (tiene `cliente_id`, `empresa_id`, `es_activo`)

### Transaccionales (cabecera/detalle)
- `log_guia_remision` (tiene `cliente_id`, `empresa_id`, **sin** `es_activo`, usa `estado`)
- `log_guia_remision_detalle` (detalle; tiene `cliente_id`, `empresa_id`)
- `log_despacho` (tiene `cliente_id`, `empresa_id`, **sin** `es_activo`, usa `estado`)
- `log_despacho_guia` (tabla puente; tiene `cliente_id`, `empresa_id`)

---

## 2) Endpoints existentes (routers)

Router principal: `app/modules/log/presentation/endpoints.py`

> Nota: rutas listadas relativas al router del módulo; los prefijos se incluyen en el router principal.

### Transportistas (`/transportistas`)
Archivo: `app/modules/log/presentation/endpoints_transportistas.py`
- `GET /transportistas`
  - Tenant: ✅ usa `current_user.cliente_id`
  - Empresa: ⚠️ `empresa_id` es opcional (ok para listar)
  - RBAC: ✅ `log.transportista.leer`
- `GET /transportistas/{transportista_id}`
  - Tenant: ✅
  - Empresa: ❌ no valida `empresa_id` aunque la tabla lo tiene
  - RBAC: ✅ `log.transportista.leer`
- `POST /transportistas`
  - Tenant: ✅ (cliente_id desde contexto)
  - Empresa: ✅ viene en body (`empresa_id`)
  - RBAC: ✅ `log.transportista.crear`
- `PUT /transportistas/{transportista_id}`
  - Tenant: ✅
  - Empresa: ❌ no valida `empresa_id` aunque la tabla lo tiene
  - RBAC: ✅ `log.transportista.actualizar`

### Vehículos (`/vehiculos`)
Archivo: `app/modules/log/presentation/endpoints_vehiculos.py`
- `GET /vehiculos` (filtros: `empresa_id`, `transportista_id`, `tipo_propiedad`, `estado_vehiculo`, `solo_activos`, `buscar`)
  - Tenant: ✅
  - Empresa: ⚠️ opcional (ok para listar)
  - RBAC: ✅ `log.vehiculo.leer`
- `GET /vehiculos/{vehiculo_id}`
  - Tenant: ✅
  - Empresa: ❌ no valida `empresa_id`
  - RBAC: ✅ `log.vehiculo.leer`
- `POST /vehiculos`
  - Tenant: ✅
  - Empresa: ✅ en body
  - RBAC: ✅ `log.vehiculo.crear`
- `PUT /vehiculos/{vehiculo_id}`
  - Tenant: ✅
  - Empresa: ❌ no valida `empresa_id`
  - RBAC: ✅ `log.vehiculo.actualizar`

### Rutas (`/rutas`)
Archivo: `app/modules/log/presentation/endpoints_rutas.py`
- `GET /rutas` (filtros: `empresa_id`, `origen_sucursal_id`, `solo_activos`, `buscar`)
  - Tenant: ✅
  - Empresa: ⚠️ opcional (ok para listar)
  - RBAC: ✅ `log.ruta.leer`
- `GET /rutas/{ruta_id}`
  - Tenant: ✅
  - Empresa: ❌ no valida `empresa_id`
  - RBAC: ✅ `log.ruta.leer`
- `POST /rutas`
  - Tenant: ✅
  - Empresa: ✅ en body
  - RBAC: ✅ `log.ruta.crear`
- `PUT /rutas/{ruta_id}`
  - Tenant: ✅
  - Empresa: ❌ no valida `empresa_id`
  - RBAC: ✅ `log.ruta.actualizar`

### Guías de remisión (`/guias-remision`)
Archivo: `app/modules/log/presentation/endpoints_guias_remision.py`
- `GET /guias-remision` (filtros: `empresa_id`, `estado`, `motivo_traslado`, `transportista_id`, `fecha_desde`, `fecha_hasta`, `buscar`)
  - Tenant: ✅
  - Empresa: ⚠️ opcional (ok para listar)
  - RBAC: ✅ `log.guia_remision.leer`
- `GET /guias-remision/{guia_remision_id}`
  - Tenant: ✅
  - Empresa: ❌ no valida `empresa_id`
  - RBAC: ✅ `log.guia_remision.leer`
- `POST /guias-remision`
  - Tenant: ✅
  - Empresa: ✅ en body
  - RBAC: ✅ `log.guia_remision.crear`
- `PUT /guias-remision/{guia_remision_id}`
  - Tenant: ✅
  - Empresa: ❌ no valida `empresa_id`
  - RBAC: ✅ `log.guia_remision.actualizar`

#### Detalle de guía (bajo `/guias-remision`)
- `GET /guias-remision/{guia_remision_id}/detalles`
  - Tenant: ✅
  - Empresa: ⚠️ implícita por `guia_remision_id` (no se valida explícitamente en endpoint)
  - RBAC: ✅ `log.guia_remision_detalle.leer`
- `POST /guias-remision/{guia_remision_id}/detalles`
  - Tenant: ✅
  - Empresa: ⚠️ se deriva en query desde cabecera (ver `create_guia_remision_detalle`)
  - RBAC: ✅ `log.guia_remision_detalle.crear`
- `GET /guias-remision/detalles/{guia_detalle_id}`
  - Tenant: ✅
  - Empresa: ❌ no valida `empresa_id`
  - RBAC: ✅ `log.guia_remision_detalle.leer`
- `PUT /guias-remision/detalles/{guia_detalle_id}`
  - Tenant: ✅
  - Empresa: ❌ no valida `empresa_id`
  - RBAC: ✅ `log.guia_remision_detalle.actualizar`

### Despachos (`/despachos`)
Archivo: `app/modules/log/presentation/endpoints_despachos.py`
- `GET /despachos` (filtros: `empresa_id`, `estado`, `ruta_id`, `vehiculo_id`, `fecha_desde`, `fecha_hasta`, `buscar`)
  - Tenant: ✅
  - Empresa: ⚠️ opcional (ok para listar)
  - RBAC: ✅ `log.despacho.leer`
- `GET /despachos/{despacho_id}`
  - Tenant: ✅
  - Empresa: ❌ no valida `empresa_id`
  - RBAC: ✅ `log.despacho.leer`
- `POST /despachos`
  - Tenant: ✅
  - Empresa: ✅ en body
  - RBAC: ✅ `log.despacho.crear`
- `PUT /despachos/{despacho_id}`
  - Tenant: ✅
  - Empresa: ❌ no valida `empresa_id`
  - RBAC: ✅ `log.despacho.actualizar`

#### Despacho-Guía (bajo `/despachos`)
- `GET /despachos/{despacho_id}/guias`
  - Tenant: ✅
  - Empresa: ⚠️ implícita por `despacho_id` (no se valida explícitamente en endpoint)
  - RBAC: ✅ `log.despacho_guia.leer`
- `POST /despachos/{despacho_id}/guias`
  - Tenant: ✅
  - Empresa: ⚠️ se deriva en query desde cabecera (ver `create_despacho_guia`)
  - RBAC: ✅ `log.despacho_guia.crear`
- `GET /despachos/guias/{despacho_guia_id}`
  - Tenant: ✅
  - Empresa: ❌ no valida `empresa_id`
  - RBAC: ✅ `log.despacho_guia.leer`
- `PUT /despachos/guias/{despacho_guia_id}`
  - Tenant: ✅
  - Empresa: ❌ no valida `empresa_id`
  - RBAC: ✅ `log.despacho_guia.actualizar`

---

## 3) Endpoints faltantes (brechas funcionales)

### Maestros (deberían tener activar/desactivar y baja lógica)
Para `log_transportista`, `log_vehiculo`, `log_ruta` faltan (no existen endpoints):
- `DELETE /<recurso>/{id}` para baja lógica (`es_activo = 0`) con RBAC `log.<recurso>.eliminar`
- `POST /<recurso>/{id}/reactivar` para reactivar (`es_activo = 1`) con RBAC `log.<recurso>.actualizar`

Además, en operaciones por ID (`GET /{id}`, `PUT /{id}`):
- Falta **scope `empresa_id`** (la tabla tiene `empresa_id`).

### Transaccionales (estado)
Para `log_guia_remision` y `log_despacho` (tabla con campo `estado`):
- Actualmente solo existen: listar/detalle/crear/actualizar.
- Faltan endpoints típicos de transacción según patrón del prompt:
  - **anular** (y setear `fecha_anulacion` si aplica en guía)
  - **cambiar estado / procesar / completar** (según flujo que se defina)
- Falta restricción explícita: **actualizar solo en estado permitido** (ej. “borrador”) si ese es el estándar del ERP.

### Tablas puente / detalle (no deberían exponer CRUD “plano”)
Observación:
- Existen endpoints directos por ID para `log_guia_remision_detalle` y `log_despacho_guia`.
- Esto no es necesariamente incorrecto, pero en el patrón del prompt suelen administrarse **como detalle embebido** de cabecera.

---

## 4) Campos faltantes o inconsistencias (BD vs schemas/ORM)

### A) Inconsistencias entre `docs/bd/LOG_TABLAS.sql` y `app/infrastructure/database/tables_erp/tables_log.py`

Estas diferencias son críticas porque pueden romper escritura/lectura si la BD real sigue el SQL del módulo:

- `log_transportista.moneda_tarifa`
  - BD (SQL): `UNIQUEIDENTIFIER NOT NULL` con FK a `cat_moneda(moneda_id)`
  - ORM (`tables_log.py`): `String(3) nullable` con default `"PEN"`
  - Schemas (`TransportistaCreate/Update/Read`): `moneda_tarifa: Optional[str]`

- `log_ruta.moneda_id`
  - BD (SQL): `moneda_id UNIQUEIDENTIFIER NOT NULL` con FK a `cat_moneda(moneda_id)`
  - ORM (`tables_log.py`): `moneda: String(3)` (nombre distinto y tipo distinto)
  - Schemas (`RutaCreate/Update/Read`): `moneda: Optional[str]`

- Columnas calculadas/persistidas en BD (SQL) que no aparecen en ORM/schemas:
  - `log_guia_remision.numero_completo AS (serie + '-' + numero) PERSISTED`
  - `log_despacho.km_recorrido AS (km_final - km_inicial) PERSISTED`
  - `log_despacho.costo_total AS (...) PERSISTED`

### B) Campos presentes en tablas (según ORM) que no están expuestos en schemas de lectura

Independiente del SQL, comparando contra `tables_log.py`:
- `log_guia_remision_detalle.empresa_id` está en ORM pero **no** está en `GuiaRemisionDetalleRead`
- `log_despacho_guia.empresa_id` está en ORM pero **no** está en `DespachoGuiaRead`

> Esto puede causar respuestas incompletas o inconsistentes con “lo que realmente hay en BD”.

---

## 5) Problemas de tenant o RBAC

### Tenant
- `cliente_id`: ✅ se aplica en endpoints (vía `current_user.cliente_id`) y en queries (WHERE por `cliente_id`).
- `empresa_id`:
  - ✅ en listados suele venir como filtro opcional.
  - ❌ en operaciones por ID (detalle/actualizar) **no se exige ni se filtra** por `empresa_id` aunque las tablas la tienen.
  - ⚠️ en “detalle” de tablas puente/detalle se deriva `empresa_id` desde cabecera en el `create_*`, pero no se valida explícitamente como scope en endpoints.

### RBAC
- ✅ Todos los endpoints revisados tienen `require_permission(...)` con patrón `log.<recurso>.<accion>`.
- ⚠️ No se encontró seed específico para LOG en `app/docs/database/SEED_PERMISOS*LOG*.sql` (puede existir en otro seed global).

---

## 6) Código marcado como obsoleto o incorrecto (NO eliminar)

No se marca código obsoleto; sí se marcan riesgos/inconsistencias:
- Diferencias de tipos/nombres entre BD del módulo (`LOG_TABLAS.sql`) y ORM/schemas (`tables_log.py`, `schemas.py`) en campos de moneda.
- Falta de scope `empresa_id` en endpoints por ID para tablas con `empresa_id`.
- Falta de endpoints de baja lógica (maestros) y transiciones de estado (transaccionales).

