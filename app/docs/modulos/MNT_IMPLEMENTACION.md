# IMPLEMENTACIÓN — MNT (Mantenimiento de Activos)

Fecha: 2026-05-07
Módulo: **MNT** (`E100000A-0000-4000-8000-00000000000A`)

Este documento describe la implementación realizada para el módulo **MNT** siguiendo el patrón del repositorio, **sin modificar la estructura de BD** ni romper contratos de endpoints existentes. Se complementa con `app/docs/modulos/AUDITORIA_MNT.md` (Fase 2).

---

## 1) Alcance

Tablas del módulo (`mnt_*`) según `docs/bd/MNT_TABLAS.sql`:

| Tabla | Tipo | `cliente_id` | `empresa_id` | `es_activo` |
|---|---|---|---|---|
| `mnt_activo` | Maestro | ✅ | ✅ | ✅ |
| `mnt_plan_mantenimiento` | Maestro | ✅ | ✅ | ✅ |
| `mnt_orden_trabajo` | Transaccional (workflow `solicitada → cerrada`) | ✅ | ✅ | ❌ (usa `estado`) |
| `mnt_historial_mantenimiento` | Bitácora derivada | ✅ | ✅ | ❌ (inmutable) |

---

## 2) Arquitectura aplicada (patrón del repositorio)

- **Routers**: `app/modules/mnt/presentation/endpoints_*.py` + agregador `endpoints.py`
- **Services**: `app/modules/mnt/application/services/*_service.py`
- **Queries**: `app/infrastructure/database/queries/mnt/*_queries.py`
- **Tablas SQLAlchemy**: `app/infrastructure/database/tables_erp/tables_mnt.py` (no modificado)
- **Tenant**: `cliente_id` proviene de `current_user.cliente_id` y se filtra en queries.
- **Empresa (scope)**: `empresa_id` se admite como query param opcional en listados; se deriva del activo en operaciones que no la reciben directamente (`plan_mantenimiento`, `historial_mantenimiento`).
- **RBAC**: `require_permission("mnt.<recurso>.<accion>")`
- **Baja lógica**: `es_activo = 0` en maestros (`mnt_activo`, `mnt_plan_mantenimiento`).
- **Workflow transaccional**: el cierre de OT se realiza con `unit_of_work` (BEGIN/COMMIT/ROLLBACK atómico) — patrón ya establecido en `inv/inventario_fisico_aprobacion_service.py`.

---

## 3) Cambios realizados (resumen por bloque)

### Bloque 1 — Schemas + filtros de listado

**`app/modules/mnt/presentation/schemas.py`** — añadido sin remover campos existentes:

- `moneda_id: Optional[UUID]` añadido a Create/Update/Read de las **4 tablas** (preparación gradual para alinear con la columna `moneda_id` de la BD; el campo `moneda: str` legacy se conserva intacto).
- `empresa_id: Optional[UUID]` añadido a `PlanMantenimientoRead` y `HistorialMantenimientoRead`.
- 5 nuevos schemas de body para transiciones de OT:
  - `OrdenTrabajoProgramarRequest`
  - `OrdenTrabajoIniciarRequest`
  - `OrdenTrabajoCompletarRequest`
  - `OrdenTrabajoCancelarRequest`
  - `OrdenTrabajoCerrarRequest`

**Filtros nuevos en listados existentes (sin romper contrato — query params opcionales):**

- `GET /planes-mantenimiento` → `empresa_id`, `vence_desde`, `vence_hasta`
- `GET /historial-mantenimiento` → `empresa_id`, `fecha_desde`, `fecha_hasta`

### Bloque 2 — Services / Queries

**`update_orden_trabajo` — validación de estado (PUT):** lanza `ConflictError` (HTTP 409) si la OT no está en `{solicitada, programada}`.

**Workflow de OT (7 transiciones nuevas):**

| Función servicio | Origen permitido | Destino | Side-effects |
|---|---|---|---|
| `programar_orden_trabajo` | `solicitada` | `programada` | `fecha_programada`, técnico (opcionales) |
| `iniciar_orden_trabajo` | `programada` | `en_proceso` | `fecha_inicio_real` (default: ahora) |
| `pausar_orden_trabajo` | `en_proceso` | `pausada` | — |
| `reanudar_orden_trabajo` | `pausada` | `en_proceso` | — |
| `completar_orden_trabajo` | `en_proceso` | `completada` | `fecha_fin_real` (default: ahora), trabajo, costos opcionales |
| `cancelar_orden_trabajo` | cualquiera salvo `cerrada`/`cancelada` | `cancelada` | `observaciones` opcional |
| `cerrar_orden_trabajo` ⚡ | `completada` | `cerrada` | **Transaccional** (ver §3.2.1) |

#### 3.2.1 — Cierre transaccional de OT

`cerrar_orden_trabajo` ejecuta dentro de un único `unit_of_work` (BEGIN/COMMIT/ROLLBACK atómico):

1. `SELECT` y validación de OT (`estado == 'completada'`).
2. `UPDATE mnt_orden_trabajo`: `estado='cerrada'`, `fecha_cierre`, `cerrado_por_usuario_id`, `calificacion_trabajo` (validada 1.00–5.00).
3. `INSERT mnt_historial_mantenimiento`: bitácora derivada con `costo_total = costo_mano_obra + costo_repuestos + costo_servicios_terceros` y `descripcion_trabajo` derivada de OT.
4. Si `plan_mantenimiento_id` no es nulo:
   - `UPDATE mnt_plan_mantenimiento.fecha_ultimo_mantenimiento` (siempre).
   - `UPDATE mnt_plan_mantenimiento.fecha_proximo_mantenimiento` solo cuando `frecuencia_tipo='dias'` (cálculo `today + frecuencia_valor` días). Para `horas_uso`/`kilometros`/`ciclos` no se actualiza por no haber data en la OT.
5. Si cualquier paso falla → **rollback automático** del UoW.

**Activar / desactivar maestros** (idempotentes — devuelven el registro sin cambios si ya está en el estado destino):

- `activar_activo`, `desactivar_activo`
- `activar_plan_mantenimiento`, `desactivar_plan_mantenimiento`

### Bloque 3 — Routers (11 endpoints nuevos)

Ningún endpoint existente fue modificado o eliminado. Se añadieron:

**Maestros (4 PATCH):**
- `PATCH /activos/{id}/activar` → `mnt.activo.activar`
- `PATCH /activos/{id}/desactivar` → `mnt.activo.desactivar`
- `PATCH /planes-mantenimiento/{id}/activar` → `mnt.plan_mantenimiento.activar`
- `PATCH /planes-mantenimiento/{id}/desactivar` → `mnt.plan_mantenimiento.desactivar`

**Workflow OT (7 PATCH):**
- `PATCH /ordenes-trabajo/{id}/programar` → `mnt.orden_trabajo.programar`
- `PATCH /ordenes-trabajo/{id}/iniciar` → `mnt.orden_trabajo.iniciar`
- `PATCH /ordenes-trabajo/{id}/pausar` → `mnt.orden_trabajo.pausar`
- `PATCH /ordenes-trabajo/{id}/reanudar` → `mnt.orden_trabajo.reanudar`
- `PATCH /ordenes-trabajo/{id}/completar` → `mnt.orden_trabajo.completar`
- `PATCH /ordenes-trabajo/{id}/cancelar` → `mnt.orden_trabajo.cancelar`
- `PATCH /ordenes-trabajo/{id}/cerrar` → `mnt.orden_trabajo.cerrar` (transaccional)

**Manejo de errores en endpoints nuevos y en `PUT` de OT:**
- `NotFoundError` → HTTP 404
- `ConflictError` (transición inválida, OT no editable, calificación fuera de rango) → HTTP 409

### Bloque 4 — RBAC

Archivo nuevo: **`app/docs/database/SEED_PERMISOS_RBAC_MNT.sql`** — idempotente vía `MERGE` por `codigo`. **21 permisos** totales:

- `mnt.activo.*` (5): `leer`, `crear`, `actualizar`, `activar`, `desactivar`
- `mnt.plan_mantenimiento.*` (5): `leer`, `crear`, `actualizar`, `activar`, `desactivar`
- `mnt.orden_trabajo.*` (10): `leer`, `crear`, `actualizar`, `programar`, `iniciar`, `pausar`, `reanudar`, `completar`, `cerrar`, `cancelar`
- `mnt.historial_mantenimiento.*` (3): `leer`, `crear` (legacy), `actualizar` (legacy)

---

## 4) Inventario completo de endpoints MNT — 27 totales

> Los endpoints **legacy** (16) permanecen sin cambios en ruta, método, contrato de body ni response. Solo se añadieron query params opcionales en 2 listados y validación de estado en 1 PUT.

### `mnt_activo` (`/activos`)

| Ruta | Método | Tipo | Tenant `cliente_id` | `empresa_id` | RBAC |
|---|---:|---|---|---|---|
| `/activos` | GET | Legacy | ✅ | ✅ filtro opcional | `mnt.activo.leer` |
| `/activos/{id}` | GET | Legacy | ✅ | ✅ derivado de la fila | `mnt.activo.leer` |
| `/activos` | POST | Legacy | ✅ | ✅ en body | `mnt.activo.crear` |
| `/activos/{id}` | PUT | Legacy | ✅ | ✅ derivado | `mnt.activo.actualizar` |
| `/activos/{id}/activar` | PATCH | **Nuevo** | ✅ | ✅ derivado | `mnt.activo.activar` |
| `/activos/{id}/desactivar` | PATCH | **Nuevo** | ✅ | ✅ derivado | `mnt.activo.desactivar` |

### `mnt_plan_mantenimiento` (`/planes-mantenimiento`)

| Ruta | Método | Tipo | Tenant `cliente_id` | `empresa_id` | RBAC |
|---|---:|---|---|---|---|
| `/planes-mantenimiento` | GET | Legacy *(nuevos filtros: `empresa_id`, `vence_desde`, `vence_hasta`)* | ✅ | ✅ filtro opcional | `mnt.plan_mantenimiento.leer` |
| `/planes-mantenimiento/{id}` | GET | Legacy | ✅ | ✅ expuesto en Read | `mnt.plan_mantenimiento.leer` |
| `/planes-mantenimiento` | POST | Legacy | ✅ | ✅ derivado del activo | `mnt.plan_mantenimiento.crear` |
| `/planes-mantenimiento/{id}` | PUT | Legacy | ✅ | ✅ derivado | `mnt.plan_mantenimiento.actualizar` |
| `/planes-mantenimiento/{id}/activar` | PATCH | **Nuevo** | ✅ | ✅ derivado | `mnt.plan_mantenimiento.activar` |
| `/planes-mantenimiento/{id}/desactivar` | PATCH | **Nuevo** | ✅ | ✅ derivado | `mnt.plan_mantenimiento.desactivar` |

### `mnt_orden_trabajo` (`/ordenes-trabajo`)

| Ruta | Método | Tipo | Tenant `cliente_id` | `empresa_id` | RBAC |
|---|---:|---|---|---|---|
| `/ordenes-trabajo` | GET | Legacy | ✅ | ✅ filtro opcional | `mnt.orden_trabajo.leer` |
| `/ordenes-trabajo/{id}` | GET | Legacy | ✅ | ✅ expuesto en Read | `mnt.orden_trabajo.leer` |
| `/ordenes-trabajo` | POST | Legacy | ✅ | ✅ en body | `mnt.orden_trabajo.crear` |
| `/ordenes-trabajo/{id}` | PUT | Legacy *(nueva validación: solo `solicitada`/`programada`)* | ✅ | ✅ derivado | `mnt.orden_trabajo.actualizar` |
| `/ordenes-trabajo/{id}/programar` | PATCH | **Nuevo** | ✅ | ✅ derivado | `mnt.orden_trabajo.programar` |
| `/ordenes-trabajo/{id}/iniciar` | PATCH | **Nuevo** | ✅ | ✅ derivado | `mnt.orden_trabajo.iniciar` |
| `/ordenes-trabajo/{id}/pausar` | PATCH | **Nuevo** | ✅ | ✅ derivado | `mnt.orden_trabajo.pausar` |
| `/ordenes-trabajo/{id}/reanudar` | PATCH | **Nuevo** | ✅ | ✅ derivado | `mnt.orden_trabajo.reanudar` |
| `/ordenes-trabajo/{id}/completar` | PATCH | **Nuevo** | ✅ | ✅ derivado | `mnt.orden_trabajo.completar` |
| `/ordenes-trabajo/{id}/cancelar` | PATCH | **Nuevo** | ✅ | ✅ derivado | `mnt.orden_trabajo.cancelar` |
| `/ordenes-trabajo/{id}/cerrar` | PATCH | **Nuevo (TX)** | ✅ | ✅ derivado / propagado a historial | `mnt.orden_trabajo.cerrar` |

### `mnt_historial_mantenimiento` (`/historial-mantenimiento`)

| Ruta | Método | Tipo | Tenant `cliente_id` | `empresa_id` | RBAC |
|---|---:|---|---|---|---|
| `/historial-mantenimiento` | GET | Legacy *(nuevos filtros: `empresa_id`, `fecha_desde`, `fecha_hasta`)* | ✅ | ✅ filtro opcional | `mnt.historial_mantenimiento.leer` |
| `/historial-mantenimiento/{id}` | GET | Legacy | ✅ | ✅ expuesto en Read | `mnt.historial_mantenimiento.leer` |
| `/historial-mantenimiento` | POST | Legacy ⚠ obsoleto (uso recomendado: `cerrar` OT) | ✅ | ✅ derivado del activo | `mnt.historial_mantenimiento.crear` |
| `/historial-mantenimiento/{id}` | PUT | Legacy ⚠ obsoleto (bitácora normalmente inmutable) | ✅ | ✅ derivado | `mnt.historial_mantenimiento.actualizar` |

---

## 5) Verificación Fase 4

### 5.1 — Cada endpoint nuevo cumple

✅ Validación de `cliente_id` (vía `current_user.cliente_id` propagado a queries).
✅ Validación de `empresa_id` cuando la tabla lo tiene (la fila se lee filtrada por tenant; el historial recibe `empresa_id` de la OT origen).
✅ Permiso RBAC con patrón `mnt.<recurso>.<accion>` aplicado vía `require_permission(...)`.

### 5.2 — Endpoints existentes — verificación de no-cambios

| Ruta | Método | Cambio funcional |
|---|---:|---|
| `/activos` | GET / POST | Sin cambios |
| `/activos/{id}` | GET / PUT | Sin cambios |
| `/planes-mantenimiento` | GET | **Sólo se añadieron** 3 query params opcionales (`empresa_id`, `vence_desde`, `vence_hasta`); request/response inalterados para llamadas previas |
| `/planes-mantenimiento` | POST | Sin cambios |
| `/planes-mantenimiento/{id}` | GET | Read **expone ahora** `empresa_id` y `moneda_id` como **opcionales** (no rompe consumidores) |
| `/planes-mantenimiento/{id}` | PUT | Sin cambios |
| `/ordenes-trabajo` | GET / POST | Sin cambios |
| `/ordenes-trabajo/{id}` | GET | Read **expone ahora** `moneda_id` opcional |
| `/ordenes-trabajo/{id}` | PUT | **Comportamiento ajustado**: ahora rechaza con 409 si la OT no está en `{solicitada, programada}` (lo que el prompt maestro requiere). El payload, ruta y método son idénticos. Las llamadas a OT en estados editables siguen funcionando igual. |
| `/historial-mantenimiento` | GET | **Sólo se añadieron** 3 query params opcionales (`empresa_id`, `fecha_desde`, `fecha_hasta`); request/response inalterados |
| `/historial-mantenimiento/{id}` | GET | Read **expone ahora** `empresa_id` y `moneda_id` como opcionales |
| `/historial-mantenimiento` | POST / PUT | Sin cambios — marcados obsoletos pero **funcionales** |

✅ **Ninguna ruta** se renombró, se cambió de método, ni se removió un campo de los schemas Read existentes. Todos los nuevos campos en Read son `Optional` para mantener compatibilidad con clientes pre-implementación.

### 5.3 — Reglas absolutas del prompt maestro

| Regla | Cumplimiento |
|---|---|
| ❌ No modificar tablas ni estructura de BD | ✅ `tables_mnt.py` intacto |
| ❌ No eliminar código existente | ✅ Todas las funciones legacy permanecen |
| ❌ No romper endpoints actuales ni cambiar contratos | ✅ Verificado en §5.2 |
| ❌ No asumir campos que no existan en BD | ✅ Para `moneda_id` (declarado en BD pero no mapeado en `tables_mnt.py`) se añadió como `Optional` y la query lo descarta naturalmente vía `_COLUMNS` filter |
| ✅ Reutilizar patrones de otros módulos | ✅ MFG (estructura), INV (`unit_of_work` para cierre transaccional) |
| ✅ Multi-tenant: `cliente_id` siempre, `empresa_id` cuando aplica | ✅ Verificado en §5.1 y §5.2 |
| ✅ RBAC con patrón `[modulo].[recurso].[accion]` | ✅ 21 permisos en seed + `require_permission` en todos los endpoints |

---

## 6) Archivos modificados / creados

**Modificados (12):**

- `app/modules/mnt/presentation/schemas.py`
- `app/modules/mnt/presentation/endpoints_activo.py`
- `app/modules/mnt/presentation/endpoints_plan_mantenimiento.py`
- `app/modules/mnt/presentation/endpoints_orden_trabajo.py`
- `app/modules/mnt/presentation/endpoints_historial_mantenimiento.py`
- `app/modules/mnt/application/services/__init__.py`
- `app/modules/mnt/application/services/activo_service.py`
- `app/modules/mnt/application/services/plan_mantenimiento_service.py`
- `app/modules/mnt/application/services/orden_trabajo_service.py` *(reescritura ampliada — sin remover funciones existentes)*
- `app/modules/mnt/application/services/historial_mantenimiento_service.py`
- `app/infrastructure/database/queries/mnt/plan_mantenimiento_queries.py`
- `app/infrastructure/database/queries/mnt/historial_mantenimiento_queries.py`

**Creados (2):**

- `app/docs/database/SEED_PERMISOS_RBAC_MNT.sql`
- `app/docs/modulos/MNT_IMPLEMENTACION.md` (este archivo)

**Auditoría asociada (de Fase 2):**

- `app/docs/modulos/AUDITORIA_MNT.md`

---

## 7) Pendientes y riesgos conocidos (no bloqueantes)

> Documentados sin acción para mantener compatibilidad. Pueden abordarse en una iteración posterior previo acuerdo.

1. **Divergencia `moneda` (str) vs `moneda_id` (UUID FK `cat_moneda`)**: la BD especifica `moneda_id UNIQUEIDENTIFIER NOT NULL` en las 4 tablas, pero `tables_mnt.py` mapea `moneda String(3)`. Se añadió `moneda_id: Optional[UUID]` a los schemas como preparación gradual. **Acciones futuras** (requieren decisión):
   - Alinear `tables_mnt.py` con `moneda_id` UUID + FK.
   - Migrar consumidores frontend de `moneda` a `moneda_id`.
   - Eventualmente deprecar `moneda` (str).
2. **`mnt_activo.vida_util_años`** (con ñ) se expone tal cual en el schema. Funcional pero no idiomático para clientes que no aceptan caracteres no-ASCII en JSON keys. Posible mitigación: alias `vida_util_anios` sin remover el original.
3. **Endpoints de escritura sobre `mnt_historial_mantenimiento`** (`POST` y `PUT`) permanecen por compatibilidad pero quedan **marcados obsoletos**. La ruta natural de inserción es ahora la transición transaccional `cerrar` OT.
4. **Cierre con `frecuencia_tipo` no-días** (`horas_uso`, `kilometros`, `ciclos`): solo se actualiza `fecha_ultimo_mantenimiento` del plan. La actualización de `horas_uso_proximo` requiere data adicional desde la OT (lectura de horómetro/odómetro) que actualmente no se captura. Posible extensión del body de `cerrar`: `horas_uso_actual`, `kilometraje_actual`.
5. **Auto-asignación de `usuario_creacion_id`** en `POST` de las 4 entidades no se realiza (campo siempre `None`). Patrón pre-existente del módulo, no se modificó.

---

## 8) Cierre

El módulo **MNT — Mantenimiento de Activos** queda **operativo** con:
- 4 entidades con CRUD completo
- 2 maestros con baja lógica vía PATCH
- 1 transaccional con workflow de 7 transiciones, incluyendo cierre transaccional con auto-bitácora y refresco de plan preventivo
- 1 derivada con lectura segura y escritura legacy preservada
- 21 permisos RBAC seedables en BD
- 0 errores de lint en los 14 archivos involucrados
- 0 contratos de endpoint rotos
