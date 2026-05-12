# Implementación — Módulo MFG (Manufactura y Producción)

Fecha: 2026-05-07  
Código: `MFG`  
Stack: FastAPI + SQL Server (multi-tenant)  
Arquitectura mantenida: `presentation → application/services → infrastructure/database/queries`  

## 1) Alcance (tablas `mfg_*`)

Fuente BD: `docs/bd/MFG_TABLAS.sql`.

- `mfg_centro_trabajo` (maestro)
- `mfg_operacion` (maestro)
- `mfg_lista_materiales` (BOM, cabecera con `estado`)
- `mfg_lista_materiales_detalle` (BOM detalle)
- `mfg_ruta_fabricacion` (cabecera con `estado`)
- `mfg_ruta_fabricacion_detalle` (detalle)
- `mfg_orden_produccion` (cabecera con `estado`)
- `mfg_orden_produccion_operacion` (seguimiento)
- `mfg_consumo_materiales` (consumo)

## 2) Endpoints del módulo

Nota: los paths siguientes son relativos al prefijo del módulo (p.ej. `/api/v1/mfg`).

### 2.1 Maestros

Centros de trabajo:
- **GET** `/centros-trabajo` (RBAC `mfg.centro_trabajo.leer`)
- **GET** `/centros-trabajo/{id}` (RBAC `mfg.centro_trabajo.leer`)
- **POST** `/centros-trabajo` (RBAC `mfg.centro_trabajo.crear`)
- **PUT** `/centros-trabajo/{id}` (RBAC `mfg.centro_trabajo.actualizar`)
- **POST** `/centros-trabajo/{id}/activar` (RBAC `mfg.centro_trabajo.activar`)
- **POST** `/centros-trabajo/{id}/desactivar` (RBAC `mfg.centro_trabajo.desactivar`)

Operaciones:
- **GET** `/operaciones` (RBAC `mfg.operacion.leer`)
- **GET** `/operaciones/{id}` (RBAC `mfg.operacion.leer`)
- **POST** `/operaciones` (RBAC `mfg.operacion.crear`)
- **PUT** `/operaciones/{id}` (RBAC `mfg.operacion.actualizar`)
- **POST** `/operaciones/{id}/activar` (RBAC `mfg.operacion.activar`)
- **POST** `/operaciones/{id}/desactivar` (RBAC `mfg.operacion.desactivar`)

### 2.2 BOM (Lista de materiales)

Cabecera:
- **GET** `/listas-materiales` (RBAC `mfg.lista_materiales.leer`)
- **GET** `/listas-materiales/{bom_id}` (RBAC `mfg.lista_materiales.leer`)
- **POST** `/listas-materiales` (RBAC `mfg.lista_materiales.crear`)
- **PUT** `/listas-materiales/{bom_id}` (RBAC `mfg.lista_materiales.actualizar`) — **solo en `borrador`**

Workflow:
- **POST** `/listas-materiales/{bom_id}/aprobar` (RBAC `mfg.lista_materiales.aprobar`)
- **POST** `/listas-materiales/{bom_id}/anular` (RBAC `mfg.lista_materiales.anular`)

Detalle:
- **GET** `/lista-materiales-detalle` (RBAC `mfg.lista_materiales_detalle.leer`)
- **GET** `/lista-materiales-detalle/{bom_detalle_id}` (RBAC `mfg.lista_materiales_detalle.leer`)
- **POST** `/lista-materiales-detalle` (RBAC `mfg.lista_materiales_detalle.crear`) — **solo si BOM cabecera está en `borrador`**
- **PUT** `/lista-materiales-detalle/{bom_detalle_id}` (RBAC `mfg.lista_materiales_detalle.actualizar`) — **solo si BOM cabecera está en `borrador`**

### 2.3 Rutas de fabricación

Cabecera:
- **GET** `/rutas-fabricacion` (RBAC `mfg.ruta_fabricacion.leer`)
- **GET** `/rutas-fabricacion/{ruta_id}` (RBAC `mfg.ruta_fabricacion.leer`)
- **POST** `/rutas-fabricacion` (RBAC `mfg.ruta_fabricacion.crear`)
- **PUT** `/rutas-fabricacion/{ruta_id}` (RBAC `mfg.ruta_fabricacion.actualizar`) — **solo en `borrador`**

Workflow:
- **POST** `/rutas-fabricacion/{ruta_id}/aprobar` (RBAC `mfg.ruta_fabricacion.aprobar`)
- **POST** `/rutas-fabricacion/{ruta_id}/anular` (RBAC `mfg.ruta_fabricacion.anular`)

Detalle:
- **GET** `/ruta-fabricacion-detalle` (RBAC `mfg.ruta_fabricacion_detalle.leer`)
- **GET** `/ruta-fabricacion-detalle/{ruta_detalle_id}` (RBAC `mfg.ruta_fabricacion_detalle.leer`)
- **POST** `/ruta-fabricacion-detalle` (RBAC `mfg.ruta_fabricacion_detalle.crear`) — **solo si ruta cabecera está en `borrador`**
- **PUT** `/ruta-fabricacion-detalle/{ruta_detalle_id}` (RBAC `mfg.ruta_fabricacion_detalle.actualizar`) — **solo si ruta cabecera está en `borrador`**

### 2.4 Órdenes de producción (OP)

Cabecera:
- **GET** `/ordenes-produccion` (RBAC `mfg.orden_produccion.leer`)
- **GET** `/ordenes-produccion/{orden_produccion_id}` (RBAC `mfg.orden_produccion.leer`)
- **POST** `/ordenes-produccion` (RBAC `mfg.orden_produccion.crear`)
- **PUT** `/ordenes-produccion/{orden_produccion_id}` (RBAC `mfg.orden_produccion.actualizar`) — **solo en `borrador`**

Workflow:
- **POST** `/ordenes-produccion/{id}/liberar` (RBAC `mfg.orden_produccion.liberar`)
- **POST** `/ordenes-produccion/{id}/iniciar` (RBAC `mfg.orden_produccion.iniciar`)
- **POST** `/ordenes-produccion/{id}/finalizar` (RBAC `mfg.orden_produccion.finalizar`)
- **POST** `/ordenes-produccion/{id}/cerrar` (RBAC `mfg.orden_produccion.cerrar`)
- **POST** `/ordenes-produccion/{id}/anular` (RBAC `mfg.orden_produccion.anular`)

Seguimiento (operaciones de OP):
- **GET** `/orden-produccion-operaciones` (RBAC `mfg.orden_produccion_operacion.leer`)
- **GET** `/orden-produccion-operaciones/{op_operacion_id}` (RBAC `mfg.orden_produccion_operacion.leer`)
- **POST** `/orden-produccion-operaciones` (RBAC `mfg.orden_produccion_operacion.crear`) — **solo si OP cabecera está en `borrador`**
- **PUT** `/orden-produccion-operaciones/{op_operacion_id}` (RBAC `mfg.orden_produccion_operacion.actualizar`) — **solo si OP cabecera está en `borrador`**

Consumo de materiales:
- **GET** `/consumo-materiales` (RBAC `mfg.consumo_material.leer`)
- **GET** `/consumo-materiales/{consumo_id}` (RBAC `mfg.consumo_material.leer`)
- **POST** `/consumo-materiales` (RBAC `mfg.consumo_material.crear`) — **solo si OP cabecera está en `borrador`**
- **PUT** `/consumo-materiales/{consumo_id}` (RBAC `mfg.consumo_material.actualizar`) — **solo si OP cabecera está en `borrador`**

## 3) Reglas implementadas (tenant + workflow)

### 3.1 Multi-tenant (cliente_id / empresa_id)

- **cliente_id**: siempre proviene de `current_user.cliente_id` (no se toma desde body).
- **empresa_id**:
  - en listados/creaciones de tablas con `empresa_id`, se valida pertenencia tenant vía `get_empresa_servicio(client_id, empresa_id)`.
  - en detalles/seguimiento, `empresa_id` se **deriva desde la cabecera** (queries) y además se valida que la cabecera exista para el tenant.

### 3.2 Workflow y edición por estado (cabeceras)

- **PUT** de `mfg_lista_materiales`, `mfg_ruta_fabricacion`, `mfg_orden_produccion`:
  - permitido **solo** en estado `borrador`
  - se bloquea cambio de `estado` por `PUT` (el estado se cambia por acciones explícitas)

Transiciones implementadas:

- **BOM** (`mfg_lista_materiales`):
  - `borrador → aprobada`
  - `borrador|aprobada → obsoleta`
- **Ruta** (`mfg_ruta_fabricacion`):
  - `borrador → aprobada`
  - `borrador|aprobada → obsoleta`
- **OP** (`mfg_orden_produccion`):
  - `borrador → liberada → en_proceso → completada → cerrada`
  - `anulada` permitido desde `borrador|liberada`

### 3.3 Endurecimiento detalle/seguimiento

Se bloquea `POST/PUT` cuando la cabecera no está en `borrador` para:
- BOM detalle
- Ruta detalle
- OP operaciones
- Consumo de materiales

## 4) Alineación BD ↔ ORM ↔ Schemas

### 4.1 `moneda_id` en orden de producción

Se alineó `mfg_orden_produccion` a la BD de referencia:
- Schemas: `OrdenProduccion*` usan `moneda_id: UUID`
- ORM: `tables_mfg.py` usa `moneda_id` como FK a `cat_moneda(moneda_id)`

**Nota de compatibilidad:** este cambio reemplaza `moneda` (string) por `moneda_id` (UUID) en el contrato de MFG para OP.

### 4.2 Campos calculados / derivados (solo lectura)

Expuestos en `Read` (opcionales):
- `OrdenProduccionRead`: `cantidad_pendiente`, `costo_total`
- `ConsumoMaterialesRead`: `diferencia`, `costo_total`

## 5) RBAC (permisos) — Seed

Script idempotente (MERGE por código):
- `app/docs/database/SEED_PERMISOS_RBAC_MFG.sql`

Incluye acciones nuevas:
- `mfg.centro_trabajo.{activar,desactivar}`
- `mfg.operacion.{activar,desactivar}`
- `mfg.lista_materiales.{aprobar,anular}`
- `mfg.ruta_fabricacion.{aprobar,anular}`
- `mfg.orden_produccion.{liberar,iniciar,finalizar,cerrar,anular}`

## 6) Archivos principales modificados/creados (MFG)

- **Schemas**: `app/modules/mfg/presentation/schemas.py`
- **Routers**:
  - `app/modules/mfg/presentation/endpoints_centros_trabajo.py`
  - `app/modules/mfg/presentation/endpoints_operaciones.py`
  - `app/modules/mfg/presentation/endpoints_listas_materiales.py`
  - `app/modules/mfg/presentation/endpoints_rutas_fabricacion.py`
  - `app/modules/mfg/presentation/endpoints_ordenes_produccion.py`
- **Services**:
  - `app/modules/mfg/application/services/*_service.py`
  - `app/modules/mfg/application/services/__init__.py`
- **Queries/ORM**:
  - `app/infrastructure/database/tables_erp/tables_mfg.py`
- **Docs/Seeds**:
  - `app/docs/modulos/AUDITORIA_MFG.md`
  - `app/docs/modulos/MFG_IMPLEMENTACION.md` (este documento)
  - `app/docs/database/SEED_PERMISOS_RBAC_MFG.sql`

## 7) Test plan (manual)

- **BOM**:
  - Crear BOM (`POST`) → estado `borrador`
  - Editar BOM (`PUT`) solo en `borrador`
  - `POST /{id}/aprobar` (borrador→aprobada)
  - Intentar `PUT` o editar detalle tras aprobar → **409**
- **Ruta**:
  - Crear/editar solo en `borrador`, aprobar/anular con validación de transición.
- **OP**:
  - Crear OP en `borrador`
  - `POST /{id}/liberar` → `liberada`
  - `POST /{id}/iniciar` → `en_proceso`
  - `POST /{id}/finalizar` → `completada`
  - `POST /{id}/cerrar` → `cerrada`
  - `POST /{id}/anular` permitido solo desde `borrador|liberada`
  - Crear/editar `consumo-materiales` y `orden-produccion-operaciones` solo mientras OP esté en `borrador`

---

## 8) Cierre del módulo

El módulo **MFG queda cerrado** para este alcance: schemas alineados a BD, multi-tenant endurecido, workflow explícito en cabeceras, bloqueo de detalle/seguimiento por estado, endpoints nuevos sin eliminar los existentes y seed RBAC para permisos faltantes.

