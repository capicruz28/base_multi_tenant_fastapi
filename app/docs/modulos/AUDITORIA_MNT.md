# AUDITORIA — Módulo MNT (Mantenimiento de Activos)

Fecha: 2026-05-07
Alcance: backend FastAPI (routers / services / queries / schemas / tablas SQLAlchemy).
Reglas auditadas (del prompt maestro):
- ❌ No modificar tablas ni estructura de BD
- ❌ No eliminar código existente
- ❌ No romper endpoints actuales ni cambiar sus contratos
- ✅ Multi-tenant: `cliente_id` obligatorio; `empresa_id` cuando la tabla lo tenga
- ✅ RBAC con patrón `mnt.<recurso>.<accion>`
- Maestros: crear / listar / detalle / actualizar + activar / desactivar (baja lógica `es_activo=0`)
- Transaccionales: crear (borrador), actualizar (solo en borrador), aprobar / procesar / anular, listar / detalle
- Derivadas / analíticas: **solo lectura**

Módulo en BD: `E100000A-0000-4000-8000-00000000000A` (origen `4.- SEED_MODULO_MENU_COMPLETO.sql`).

---

## 1) Tablas detectadas y su tipo

Fuente: `docs/bd/MNT_TABLAS.sql` (prefijo `mnt_`).

| Tabla | Tipo | `cliente_id` | `empresa_id` | `es_activo` | Notas |
|---|---|---|---|---|---|
| `mnt_activo` | **Maestro** | ✅ | ✅ | ✅ | Activos físicos (maquinaria, vehículos, equipos, instalaciones, herramientas). |
| `mnt_plan_mantenimiento` | **Maestro** | ✅ | ✅ | ✅ | Programa preventivo/predictivo por activo. |
| `mnt_orden_trabajo` | **Transaccional** | ✅ | ✅ | ❌ (usa `estado`) | Workflow `solicitada→programada→en_proceso→pausada→completada→cerrada/cancelada`. Tiene columnas calculadas `duracion_horas` y `costo_total` (PERSISTED). |
| `mnt_historial_mantenimiento` | **Derivada (bitácora)** | ✅ | ✅ | ❌ (registro inmutable) | Alimentada desde OT al cerrarse. Solo debería exponer **lectura**. |

---

## 2) Implementación actual — archivos del módulo

- Router agregador: `app/modules/mnt/presentation/endpoints.py`
- Routers por entidad:
  - `app/modules/mnt/presentation/endpoints_activo.py`
  - `app/modules/mnt/presentation/endpoints_plan_mantenimiento.py`
  - `app/modules/mnt/presentation/endpoints_orden_trabajo.py`
  - `app/modules/mnt/presentation/endpoints_historial_mantenimiento.py`
- Schemas: `app/modules/mnt/presentation/schemas.py`
- Services: `app/modules/mnt/application/services/{activo,plan_mantenimiento,orden_trabajo,historial_mantenimiento}_service.py`
- Queries: `app/infrastructure/database/queries/mnt/{activo,plan_mantenimiento,orden_trabajo,historial_mantenimiento}_queries.py`
- Tablas SQLAlchemy: `app/infrastructure/database/tables_erp/tables_mnt.py`
- Seeds RBAC: **NO existe** `SEED_PERMISOS_RBAC_MNT.sql` ⚠

### Endpoints existentes (rutas relativas al prefijo del router del módulo)

| Ruta (relativa) | Método | Entidad | ¿Tenant? | ¿RBAC? |
|---|---:|---|---|---|
| `/activos` | GET | Activo | ✅ `current_user.cliente_id` | ✅ `mnt.activo.leer` |
| `/activos/{activo_id}` | GET | Activo | ✅ | ✅ `mnt.activo.leer` |
| `/activos` | POST | Activo | ✅ (cliente_id ctx, `empresa_id` en body) | ✅ `mnt.activo.crear` |
| `/activos/{activo_id}` | PUT | Activo | ✅ | ✅ `mnt.activo.actualizar` |
| `/planes-mantenimiento` | GET | PlanMantenimiento | ✅ | ✅ `mnt.plan_mantenimiento.leer` |
| `/planes-mantenimiento/{plan_mantenimiento_id}` | GET | PlanMantenimiento | ✅ | ✅ `mnt.plan_mantenimiento.leer` |
| `/planes-mantenimiento` | POST | PlanMantenimiento | ✅ (cliente_id ctx, `empresa_id` derivado del activo) | ✅ `mnt.plan_mantenimiento.crear` |
| `/planes-mantenimiento/{plan_mantenimiento_id}` | PUT | PlanMantenimiento | ✅ | ✅ `mnt.plan_mantenimiento.actualizar` |
| `/ordenes-trabajo` | GET | OrdenTrabajo | ✅ | ✅ `mnt.orden_trabajo.leer` |
| `/ordenes-trabajo/{orden_trabajo_id}` | GET | OrdenTrabajo | ✅ | ✅ `mnt.orden_trabajo.leer` |
| `/ordenes-trabajo` | POST | OrdenTrabajo | ✅ (cliente_id ctx, `empresa_id` en body) | ✅ `mnt.orden_trabajo.crear` |
| `/ordenes-trabajo/{orden_trabajo_id}` | PUT | OrdenTrabajo | ✅ | ✅ `mnt.orden_trabajo.actualizar` |
| `/historial-mantenimiento` | GET | HistorialMantenimiento | ✅ | ✅ `mnt.historial_mantenimiento.leer` |
| `/historial-mantenimiento/{historial_id}` | GET | HistorialMantenimiento | ✅ | ✅ `mnt.historial_mantenimiento.leer` |
| `/historial-mantenimiento` | POST | HistorialMantenimiento | ✅ | ⚠ `mnt.historial_mantenimiento.crear` — **incorrecto para tabla derivada** |
| `/historial-mantenimiento/{historial_id}` | PUT | HistorialMantenimiento | ✅ | ⚠ `mnt.historial_mantenimiento.actualizar` — **incorrecto para tabla derivada** |

> **No se han modificado** los endpoints listados; quedan como están. Las marcas ⚠ se documentan pero **el código existente NO se elimina**.

---

## 3) Brechas funcionales (Paso 2.2)

### 3.1 `mnt_activo` — MAESTRO

- ✅ Existe: crear, listar, detalle, actualizar.
- ❌ **Falta**: endpoints **activar / desactivar** (baja lógica `es_activo`).
  - Ruta sugerida: `PATCH /activos/{activo_id}/activar` → permiso `mnt.activo.activar`
  - Ruta sugerida: `PATCH /activos/{activo_id}/desactivar` → permiso `mnt.activo.desactivar`
- ⚠ Validación de unicidad `(cliente_id, empresa_id, codigo_activo)` en service: **no se observa explícita** (la BD la garantiza, pero la API no devuelve mensaje amigable previo).

### 3.2 `mnt_plan_mantenimiento` — MAESTRO

- ✅ Existe: crear, listar, detalle, actualizar.
- ❌ **Falta**: endpoints **activar / desactivar**.
  - Ruta sugerida: `PATCH /planes-mantenimiento/{plan_mantenimiento_id}/activar` → permiso `mnt.plan_mantenimiento.activar`
  - Ruta sugerida: `PATCH /planes-mantenimiento/{plan_mantenimiento_id}/desactivar` → permiso `mnt.plan_mantenimiento.desactivar`
- ⚠ `empresa_id` no se acepta en `Create` (se deriva del activo) ni se expone en `Read` ni se permite filtrar en `List` — ver §4.2.
- ⚠ Falta filtro de listado por `fecha_proximo_mantenimiento` (rango), útil para tablero de planificación.
  - Ruta sugerida: `GET /planes-mantenimiento?vence_desde=&vence_hasta=` (extender `list_plan_mantenimiento`).

### 3.3 `mnt_orden_trabajo` — TRANSACCIONAL

- ✅ Existe: crear, listar, detalle, actualizar.
- ⚠ El `PUT /ordenes-trabajo/{id}` **permite cambiar `estado` libremente** y modificar campos de cualquier estado — incumple regla "actualizar solo en borrador". Patrón maestro establece estados por tabla; no debe alterarse el contrato existente, pero sí complementarse con endpoints de transición.
- ❌ **Faltan transiciones de estado** (workflow):
  - `PATCH /ordenes-trabajo/{id}/programar` (`solicitada → programada`) → `mnt.orden_trabajo.programar`
  - `PATCH /ordenes-trabajo/{id}/iniciar` (`programada → en_proceso`, fija `fecha_inicio_real`) → `mnt.orden_trabajo.iniciar`
  - `PATCH /ordenes-trabajo/{id}/pausar` (`en_proceso → pausada`) → `mnt.orden_trabajo.pausar`
  - `PATCH /ordenes-trabajo/{id}/reanudar` (`pausada → en_proceso`) → `mnt.orden_trabajo.reanudar`
  - `PATCH /ordenes-trabajo/{id}/completar` (`en_proceso → completada`, fija `fecha_fin_real`) → `mnt.orden_trabajo.completar`
  - `PATCH /ordenes-trabajo/{id}/cerrar` (`completada → cerrada`, fija `fecha_cierre`, `cerrado_por_usuario_id`, `calificacion_trabajo`) → `mnt.orden_trabajo.cerrar`
  - `PATCH /ordenes-trabajo/{id}/cancelar` (cualquiera salvo `cerrada` → `cancelada`) → `mnt.orden_trabajo.cancelar`
- ❌ **Falta** auto-generación de `mnt_historial_mantenimiento` al **cerrar** la OT (regla bitácora derivada). Debe insertarse desde el service de cierre, dentro de transacción.
- ❌ **Falta** actualización de `mnt_plan_mantenimiento.fecha_ultimo_mantenimiento` / `fecha_proximo_mantenimiento` al cerrar OT preventiva (cuando `plan_mantenimiento_id` no es nulo).
- ⚠ `costo_total` y `duracion_horas` están en BD como columnas **PERSISTED**, pero el service los recalcula en Python. Se mantiene tal cual (no romper contratos), pero el `Read` debería preferir el valor de BD.

### 3.4 `mnt_historial_mantenimiento` — DERIVADA (solo lectura)

- ✅ Existe: listar, detalle.
- ⚠ **Incorrecto**: existe `POST /historial-mantenimiento` y `PUT /historial-mantenimiento/{id}` — una tabla derivada no debe exponer escritura desde la API. **NO se elimina** (regla); se marca como obsoleto.
- ❌ **Falta**: filtro de listado por rango de fecha y por `empresa_id`.
  - Ruta sugerida: `GET /historial-mantenimiento?empresa_id=&fecha_desde=&fecha_hasta=` (extender `list_historial_mantenimiento`).
- ❌ **Falta** un endpoint de bitácora consolidada por activo:
  - Ruta sugerida: `GET /activos/{activo_id}/historial` → permiso `mnt.historial_mantenimiento.leer` (ya existe el equivalente vía filtro `?activo_id=`, pero el path nesteado mejora UX y trazabilidad).

---

## 4) Campos faltantes / inconsistentes en schemas (Paso 2.3)

> Comparación BD (`docs/bd/MNT_TABLAS.sql`) vs `app/modules/mnt/presentation/schemas.py` y `tables_mnt.py`.

### 4.1 Inconsistencia crítica `moneda_id` (UUID FK) vs `moneda` (str(3))

En **las cuatro tablas** del módulo MNT, la BD especifica:

```sql
moneda_id UNIQUEIDENTIFIER NOT NULL,
CONSTRAINT FK_*_moneda FOREIGN KEY (moneda_id) REFERENCES cat_moneda(moneda_id) ...
```

Sin embargo, la implementación actual usa:

- `tables_mnt.py`: `Column("moneda", String(3), nullable=True, server_default="PEN")`
- `schemas.py`: `moneda: Optional[str] = Field("PEN", max_length=3)`

Esto significa que **la columna `moneda_id` (FK) NO está modelada** en código y **`moneda` (str) NO existe en la BD especificada**. Es la misma divergencia ya reportada en `AUDITORIA_MFG.md` para `mfg_orden_produccion`.

- 📌 **Decisión**: regla absoluta dice "no asumir campos que no existan en BD" y "no modificar BD". Para no romper contratos, **se mantiene el campo `moneda` actual**. Documentar la divergencia y, en Fase 3, **incluir `moneda_id: Optional[UUID]` adicional en los schemas** (sin remover `moneda`) para empezar a alinear sin romper clientes existentes.

### 4.2 `mnt_plan_mantenimiento`

| Campo BD | ¿En `Create`? | ¿En `Update`? | ¿En `Read`? | Comentario |
|---|---|---|---|---|
| `empresa_id` (NOT NULL) | ❌ no aceptado | ❌ no aceptado | ❌ **no expuesto** | Se deriva del activo en query; debe **exponerse en `Read`**. |
| `moneda_id` (NOT NULL) | ❌ ver §4.1 | ❌ | ❌ | Divergencia estructural. |

### 4.3 `mnt_historial_mantenimiento`

| Campo BD | ¿En `Create`? | ¿En `Update`? | ¿En `Read`? | Comentario |
|---|---|---|---|---|
| `empresa_id` (NOT NULL) | ❌ no aceptado | ❌ no aceptado | ❌ **no expuesto** | Debe **exponerse en `Read`**. |
| `moneda_id` (NOT NULL) | ❌ ver §4.1 | ❌ | ❌ | Divergencia estructural. |

### 4.4 `mnt_orden_trabajo`

| Campo BD | ¿En `Create`? | ¿En `Update`? | ¿En `Read`? | Comentario |
|---|---|---|---|---|
| `moneda_id` (NOT NULL) | ❌ ver §4.1 | ❌ | ❌ | Divergencia estructural. |
| `duracion_horas` (computed PERSISTED) | n/a | n/a | ✅ (calculado en service) | OK como derivado; debería preferir valor BD si está disponible. |
| `costo_total` (computed PERSISTED) | n/a | n/a | ✅ (calculado en service) | OK como derivado; idem. |

### 4.5 `mnt_activo`

| Campo BD | ¿En `Create`? | ¿En `Update`? | ¿En `Read`? | Comentario |
|---|---|---|---|---|
| `año_fabricacion` (con ñ) | ✅ vía alias `anio_fabricacion` | ✅ idem | ✅ idem | Conversión correcta en `activo_service._row_to_read` / `_dump_to_db`. |
| `vida_util_años` (con ñ) | ✅ tal cual | ✅ tal cual | ✅ tal cual | Funcional pero **expone ñ** en API; no se cambia (no romper contrato). Se podría agregar alias `vida_util_anios` en Fase 3 (opcional, sin remover el actual). |
| `moneda_id` | ❌ ver §4.1 | ❌ | ❌ | Divergencia estructural. |

---

## 5) Problemas de tenant o RBAC

### 5.1 Tenant (`cliente_id`)

- ✅ Todos los endpoints usan `current_user.cliente_id` y lo propagan hasta el query.
- ✅ Todas las queries filtran `WHERE cliente_id = :client_id`.

### 5.2 Tenant (`empresa_id`)

| Recurso | Create acepta | Read expone | List filtra | Estado |
|---|---|---|---|---|
| `mnt_activo` | ✅ | ✅ | ✅ | OK |
| `mnt_plan_mantenimiento` | ❌ (deriva del activo) | ❌ | ❌ | **Brecha** |
| `mnt_orden_trabajo` | ✅ | ✅ | ✅ | OK |
| `mnt_historial_mantenimiento` | ❌ (deriva del activo) | ❌ | ❌ | **Brecha** |

> **Acción Fase 3**: agregar `empresa_id` a los `Read` de `PlanMantenimiento` e `Historial`, y permitir filtrar por `empresa_id` en sus listados. **Sin modificar** los `Create` (mantener derivación implícita para no romper contrato existente).

### 5.3 RBAC

- ✅ Todos los endpoints aplican `require_permission("mnt.<recurso>.<accion>")`.
- ❌ **No existe** `app/docs/database/SEED_PERMISOS_RBAC_MNT.sql`. Hay que crearlo.
- 📌 Permisos que ya se referencian en código y deben existir como seeds:
  - `mnt.activo.leer`, `mnt.activo.crear`, `mnt.activo.actualizar`
  - `mnt.plan_mantenimiento.leer`, `mnt.plan_mantenimiento.crear`, `mnt.plan_mantenimiento.actualizar`
  - `mnt.orden_trabajo.leer`, `mnt.orden_trabajo.crear`, `mnt.orden_trabajo.actualizar`
  - `mnt.historial_mantenimiento.leer`, `mnt.historial_mantenimiento.crear` *(legacy)*, `mnt.historial_mantenimiento.actualizar` *(legacy)*
- 📌 Permisos **a agregar** (Fase 3) según brechas:
  - `mnt.activo.activar`, `mnt.activo.desactivar`
  - `mnt.plan_mantenimiento.activar`, `mnt.plan_mantenimiento.desactivar`
  - `mnt.orden_trabajo.programar`, `mnt.orden_trabajo.iniciar`, `mnt.orden_trabajo.pausar`, `mnt.orden_trabajo.reanudar`, `mnt.orden_trabajo.completar`, `mnt.orden_trabajo.cerrar`, `mnt.orden_trabajo.cancelar`

---

## 6) Endpoints faltantes — propuesta consolidada (Fase 3)

| Ruta sugerida | Método | Entidad | Permiso RBAC | Comentario |
|---|---:|---|---|---|
| `/activos/{activo_id}/activar` | PATCH | Activo | `mnt.activo.activar` | Baja lógica `es_activo=1`. |
| `/activos/{activo_id}/desactivar` | PATCH | Activo | `mnt.activo.desactivar` | Baja lógica `es_activo=0`. |
| `/planes-mantenimiento/{plan_mantenimiento_id}/activar` | PATCH | PlanMantenimiento | `mnt.plan_mantenimiento.activar` | |
| `/planes-mantenimiento/{plan_mantenimiento_id}/desactivar` | PATCH | PlanMantenimiento | `mnt.plan_mantenimiento.desactivar` | |
| `/ordenes-trabajo/{orden_trabajo_id}/programar` | PATCH | OrdenTrabajo | `mnt.orden_trabajo.programar` | `solicitada → programada`. |
| `/ordenes-trabajo/{orden_trabajo_id}/iniciar` | PATCH | OrdenTrabajo | `mnt.orden_trabajo.iniciar` | `programada → en_proceso`; setea `fecha_inicio_real`. |
| `/ordenes-trabajo/{orden_trabajo_id}/pausar` | PATCH | OrdenTrabajo | `mnt.orden_trabajo.pausar` | `en_proceso → pausada`. |
| `/ordenes-trabajo/{orden_trabajo_id}/reanudar` | PATCH | OrdenTrabajo | `mnt.orden_trabajo.reanudar` | `pausada → en_proceso`. |
| `/ordenes-trabajo/{orden_trabajo_id}/completar` | PATCH | OrdenTrabajo | `mnt.orden_trabajo.completar` | `en_proceso → completada`; setea `fecha_fin_real`. |
| `/ordenes-trabajo/{orden_trabajo_id}/cerrar` | PATCH | OrdenTrabajo | `mnt.orden_trabajo.cerrar` | `completada → cerrada`; **TX**: setea `fecha_cierre`, `cerrado_por_usuario_id`, `calificacion_trabajo`, **inserta** en `mnt_historial_mantenimiento`, actualiza `mnt_plan_mantenimiento` si aplica. |
| `/ordenes-trabajo/{orden_trabajo_id}/cancelar` | PATCH | OrdenTrabajo | `mnt.orden_trabajo.cancelar` | Cualquiera salvo `cerrada` → `cancelada`. |

Filtros adicionales (sin nuevas rutas, solo nuevos query params en endpoints existentes):
- `GET /planes-mantenimiento?empresa_id=&vence_desde=&vence_hasta=`
- `GET /historial-mantenimiento?empresa_id=&fecha_desde=&fecha_hasta=`

---

## 7) Código existente marcado como obsoleto / incorrecto (NO eliminar)

> Se documenta solo. Por regla, **no se elimina** ningún archivo ni función.

| Archivo | Símbolo | Motivo |
|---|---|---|
| `app/modules/mnt/presentation/endpoints_historial_mantenimiento.py` | `post_historial_mantenimiento`, `put_historial_mantenimiento` | `mnt_historial_mantenimiento` es bitácora derivada — no debería tener escritura por API. Reemplazar por inserción interna desde `cerrar OT`. |
| `app/modules/mnt/application/services/historial_mantenimiento_service.py` | `create_historial_mantenimiento`, `update_historial_mantenimiento` | Idem. Mantener como utilidad interna; quitar de la superficie pública futura (no en esta auditoría). |
| `app/infrastructure/database/queries/mnt/historial_mantenimiento_queries.py` | `create_historial_mantenimiento`, `update_historial_mantenimiento` | Pueden seguir existiendo como helpers; las usaremos en Fase 3 desde el service de cierre de OT. |
| `app/modules/mnt/presentation/endpoints_orden_trabajo.py` | `put_orden_trabajo` (permite cambiar `estado` libremente) | Debería restringirse a campos editables y solo cuando `estado in {solicitada, programada}`. **No se altera el contrato existente**; se complementa con endpoints de transición. |

---

## 8) Resumen ejecutivo

- **Tablas detectadas**: 4 (2 maestros, 1 transaccional, 1 derivada).
- **CRUD básico** ya existe para las 4 entidades.
- **Brechas principales**:
  1. Falta workflow de estados en `mnt_orden_trabajo` (7 transiciones) + cierre transaccional con auto-bitácora y actualización de plan.
  2. Falta activar/desactivar en `mnt_activo` y `mnt_plan_mantenimiento`.
  3. Schemas de `PlanMantenimiento` e `Historial` no exponen `empresa_id` en `Read` y no permiten filtrar listados por `empresa_id`.
  4. Divergencia estructural `moneda_id (UUID FK)` ↔ `moneda (str)` en BD vs implementación — se documenta y se planifica alineación gradual sin romper contratos.
  5. **Endpoints de escritura** sobre `mnt_historial_mantenimiento` permanecen por compatibilidad pero quedan marcados como **obsoletos** (no se eliminan).
  6. **Falta seed RBAC**: `app/docs/database/SEED_PERMISOS_RBAC_MNT.sql` no existe; debe crearse en Fase 3 con permisos legacy + nuevos (activar/desactivar + workflow OT).

⛔ **DETENIDO al final de Fase 2.** Espera confirmación para iniciar Fase 3 — Implementación.
