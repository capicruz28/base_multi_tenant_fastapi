# AUDITORÍA — Módulo Gestión de Calidad (QMS)

Fecha: 2026-05-07  
Módulo: **Gestión de Calidad**  
Código: **QMS**

## 1) Tablas detectadas (prefijo `QMS_` / `qms_`)

- **Maestros / Configuración**
  - `qms_parametro_calidad` (maestro)
  - `qms_plan_inspeccion` (maestro / configuración)
  - `qms_plan_inspeccion_detalle` (detalle de configuración; derivada del plan)

- **Transaccionales**
  - `qms_inspeccion` (cabecera transaccional)
  - `qms_inspeccion_detalle` (detalle transaccional)
  - `qms_no_conformidad` (gestión de casos; transaccional)

## 2) Implementación actual detectada (routers/services/queries/schemas)

### 2.1 Estructura encontrada

- **Routers**
  - `app/modules/qms/presentation/endpoints.py` (router agregador)
  - `app/modules/qms/presentation/endpoints_parametros.py`
  - `app/modules/qms/presentation/endpoints_planes.py`
  - `app/modules/qms/presentation/endpoints_inspecciones.py`
  - `app/modules/qms/presentation/endpoints_no_conformidades.py`

- **Services**
  - `app/modules/qms/application/services/*_service.py` (funciones `list/get/create/update` por entidad)

- **Queries**
  - `app/infrastructure/database/queries/qms/*_queries.py` (SQLAlchemy Core)

- **Schemas**
  - `app/modules/qms/presentation/schemas.py`

### 2.2 Patrones de tenant y RBAC observados

- **Tenant**
  - En endpoints se usa `current_user.cliente_id` y se pasa como `client_id` hacia services/queries.
  - En queries, el filtro por tenant es estricto: `...Table.c.cliente_id == client_id`.
  - Cuando aplica, se filtra también por `empresa_id` (si viene en query params).

- **RBAC**
  - Se aplica `require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.accion")`.
  - Patrón observado por recurso:
    - `qms.parametro_calidad.{leer|crear|actualizar}`
    - `qms.plan_inspeccion.{leer|crear|actualizar}`
    - `qms.inspeccion.{leer|crear|actualizar}`
    - `qms.no_conformidad.{leer|crear|actualizar}`

## 3) Endpoints existentes (con ruta sugerida dentro del módulo)

Nota: las rutas base vienen de `app/modules/qms/presentation/endpoints.py`:
- `/parametros-calidad`
- `/planes-inspeccion`
- `/inspecciones`
- `/no-conformidades`

En todos los endpoints listados abajo:
- **Tenant**: Sí (depende de `get_current_active_user` y usa `current_user.cliente_id`)
- **RBAC**: Sí (usa `require_permission(...)`)

### 3.1 Parámetros de calidad (`qms_parametro_calidad`)

- **GET** `/parametros-calidad`
  - Query params: `empresa_id`, `tipo_parametro`, `solo_activos`, `buscar`
  - Permiso: `qms.parametro_calidad.leer`
- **GET** `/parametros-calidad/{parametro_id}`
  - Permiso: `qms.parametro_calidad.leer`
- **POST** `/parametros-calidad`
  - Permiso: `qms.parametro_calidad.crear`
- **PUT** `/parametros-calidad/{parametro_id}`
  - Permiso: `qms.parametro_calidad.actualizar`

### 3.2 Planes de inspección (`qms_plan_inspeccion` + `qms_plan_inspeccion_detalle`)

- **GET** `/planes-inspeccion`
  - Query params: `empresa_id`, `producto_id`, `categoria_id`, `tipo_inspeccion`, `solo_activos`, `buscar`
  - Permiso: `qms.plan_inspeccion.leer`
- **GET** `/planes-inspeccion/{plan_inspeccion_id}`
  - Permiso: `qms.plan_inspeccion.leer`
- **POST** `/planes-inspeccion`
  - Permiso: `qms.plan_inspeccion.crear`
- **PUT** `/planes-inspeccion/{plan_inspeccion_id}`
  - Permiso: `qms.plan_inspeccion.actualizar`

**Detalle (endpoints dedicados):**
- **GET** `/planes-inspeccion/{plan_inspeccion_id}/detalles`
  - Permiso: `qms.plan_inspeccion.leer`
- **POST** `/planes-inspeccion/{plan_inspeccion_id}/detalles`
  - Permiso: `qms.plan_inspeccion.crear`
  - Nota: el endpoint fuerza `data.plan_inspeccion_id = {plan_inspeccion_id}`
- **GET** `/planes-inspeccion/detalles/{plan_detalle_id}`
  - Permiso: `qms.plan_inspeccion.leer`
- **PUT** `/planes-inspeccion/detalles/{plan_detalle_id}`
  - Permiso: `qms.plan_inspeccion.actualizar`

### 3.3 Inspecciones (`qms_inspeccion` + `qms_inspeccion_detalle`)

- **GET** `/inspecciones`
  - Query params: `empresa_id`, `producto_id`, `plan_inspeccion_id`, `resultado`, `lote`, `fecha_desde`, `fecha_hasta`, `buscar`
  - Permiso: `qms.inspeccion.leer`
- **GET** `/inspecciones/{inspeccion_id}`
  - Permiso: `qms.inspeccion.leer`
- **POST** `/inspecciones`
  - Permiso: `qms.inspeccion.crear`
- **PUT** `/inspecciones/{inspeccion_id}`
  - Permiso: `qms.inspeccion.actualizar`

**Detalle (endpoints dedicados):**
- **GET** `/inspecciones/{inspeccion_id}/detalles`
  - Permiso: `qms.inspeccion.leer`
- **POST** `/inspecciones/{inspeccion_id}/detalles`
  - Permiso: `qms.inspeccion.crear`
  - Nota: el endpoint fuerza `data.inspeccion_id = {inspeccion_id}`
- **GET** `/inspecciones/detalles/{inspeccion_detalle_id}`
  - Permiso: `qms.inspeccion.leer`
- **PUT** `/inspecciones/detalles/{inspeccion_detalle_id}`
  - Permiso: `qms.inspeccion.actualizar`

### 3.4 No conformidades (`qms_no_conformidad`)

- **GET** `/no-conformidades`
  - Query params: `empresa_id`, `producto_id`, `origen`, `tipo_nc`, `estado`, `fecha_desde`, `fecha_hasta`, `buscar`
  - Permiso: `qms.no_conformidad.leer`
- **GET** `/no-conformidades/{no_conformidad_id}`
  - Permiso: `qms.no_conformidad.leer`
- **POST** `/no-conformidades`
  - Permiso: `qms.no_conformidad.crear`
- **PUT** `/no-conformidades/{no_conformidad_id}`
  - Permiso: `qms.no_conformidad.actualizar`

## 4) Brechas funcionales (contra el criterio del prompt maestro)

### 4.1 Tablas MAESTRO — endpoints esperados vs existentes

Para maestros, el estándar esperado es: **crear, listar, detalle, actualizar, activar/desactivar**.

- **`qms_parametro_calidad`**
  - Existe: listar/detalle/crear/actualizar
  - Falta: endpoint explícito de **activar/desactivar**
    - Observación: hoy se puede “simular” vía `PUT` usando `es_activo`, pero no existe acción dedicada.

- **`qms_plan_inspeccion`**
  - Existe: listar/detalle/crear/actualizar
  - Falta: endpoint explícito de **activar/desactivar**
    - Observación: igual que arriba, el `PUT` incluye `es_activo`.

### 4.2 Tablas TRANSACCIONALES — endpoints esperados vs existentes

Para transaccionales, el estándar esperado es: **crear (borrador), actualizar (solo borrador), aprobar, procesar, anular, listar, detalle**.

- **`qms_inspeccion`**
  - Existe: listar/detalle/crear/actualizar + CRUD de detalle separado
  - Falta: acciones de estado (p.ej. **aprobar/anular/procesar**) y control de “solo editable en borrador”
  - Nota: en la BD existe `resultado` y campos de aprobación (`aprobado_por_usuario_id`, `fecha_aprobacion`) pero no hay endpoints de transición.

- **`qms_no_conformidad`**
  - Existe: listar/detalle/crear/actualizar
  - Falta: acciones de flujo (p.ej. **cerrar/cancelar**) alineadas a `estado`, `fecha_cierre`, `cerrado_por_usuario_id`, y validaciones asociadas.

### 4.3 Tablas derivadas/detalle que NO deberían tener CRUD “independiente”

- **`qms_plan_inspeccion_detalle`** y **`qms_inspeccion_detalle`**
  - Observación: ya están implementadas con endpoints dedicados (por id) y endpoints anidados en la cabecera.
  - Recomendación (a validar en Fase 3): priorizar manejo embebido/anidado (cabecera → detalle) para evitar inconsistencias y mantener transacciones cuando aplique.

## 5) Campos faltantes en schemas (comparado con BD)

### 5.1 `qms_plan_inspeccion_detalle`

En BD, la tabla exige `empresa_id NOT NULL`.

- **Faltantes en `PlanInspeccionDetalleCreate`** (requeridos por BD):
  - `empresa_id: UUID` (**NOT NULL** en BD)
- **Faltantes en `PlanInspeccionDetalleRead`** (existen en BD, no se exponen):
  - `empresa_id: UUID`

Impacto probable: el insert/lectura del detalle queda incompleto respecto a la tabla y puede fallar al crear por `NOT NULL`.

### 5.2 `qms_inspeccion_detalle`

En BD, la tabla exige `empresa_id NOT NULL`.

- **Faltantes en `InspeccionDetalleCreate`** (requeridos por BD):
  - `empresa_id: UUID` (**NOT NULL** en BD)
- **Faltantes en `InspeccionDetalleRead`** (existen en BD, no se exponen):
  - `empresa_id: UUID`

Impacto probable: el insert del detalle puede fallar al crear por `NOT NULL`.

### 5.3 Resto de entidades

- `ParametroCalidad*`, `PlanInspeccion*`, `Inspeccion*`, `NoConformidad*`:
  - A nivel de *Read*, los campos principales de BD están representados.
  - `cliente_id` se expone en *Read* y se omite en *Create/Update* (se setea desde contexto), lo cual está alineado al patrón observado.

## 6) Problemas de tenant o RBAC

- **Tenant**: No se detectan omisiones de `cliente_id` en queries (filtro tenant estricto presente).
- **Empresa**:
  - Se filtra por `empresa_id` en listados cuando se envía como query param.
  - **Riesgo**: en tablas de detalle (`*_detalle`) el schema Create no incluye `empresa_id` pese a que la BD lo requiere.
- **RBAC**: todos los endpoints revisados declaran `require_permission(...)` con el patrón `qms.<recurso>.<accion>`.

## 7) Código potencialmente incorrecto/obsoleto (NO eliminar)

- **Schemas de detalle**:
  - `PlanInspeccionDetalleCreate` e `InspeccionDetalleCreate` no incluyen `empresa_id` (requerido por BD).
  - `PlanInspeccionDetalleRead` e `InspeccionDetalleRead` no exponen `empresa_id` pese a existir en BD.

Esto debe corregirse en Fase 3 (sin cambiar contratos existentes; agregando campos faltantes de forma compatible).

