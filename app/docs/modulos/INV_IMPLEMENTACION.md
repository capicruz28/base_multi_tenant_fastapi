# INV — Inventarios y Almacenes: Informe de Implementación

> Generado en Fase 4 del ciclo PROMPT_BACKEND_MAESTRO.
> Módulo: `INV` · Prefijo API: `/inv` · Base: `/api/v1/inv`

---

## 1. Archivos modificados

### Bloque 1 — Endpoints marcados DEPRECATED
| Archivo | Cambio |
|---|---|
| `app/modules/inv/presentation/endpoints_movimientos_detalle.py` | `deprecated=True` en POST y PUT |
| `app/modules/inv/presentation/endpoints_inventario_fisico_detalle.py` | `deprecated=True` en POST y PUT |

### Bloque 2 — Schemas
| Archivo | Cambio |
|---|---|
| `app/modules/inv/presentation/schemas.py` | `costo_total` en `MovimientoDetalleRead`; `diferencia` y `valor_diferencia` en `InventarioFisicoDetalleRead`; 8 schemas nuevos de cabecera+detalle embebido |

### Bloque 3 — Queries
| Archivo | Cambio |
|---|---|
| `app/infrastructure/database/queries/inv/movimiento_queries.py` | Nueva función `get_movimiento_con_detalles`; import `InvMovimientoDetalleTable` |
| `app/infrastructure/database/queries/inv/inventario_fisico_queries.py` | Nueva función `get_inventario_fisico_con_detalles`; import `InvInventarioFisicoDetalleTable` |
| `app/infrastructure/database/queries/inv/__init__.py` | Exporta las 2 funciones nuevas |

### Bloque 4 — Services
| Archivo | Cambio |
|---|---|
| `app/modules/inv/application/services/movimiento_service.py` | 3 funciones nuevas: `get/create/update_movimiento_con_detalles_servicio`; imports UoW + tablas |
| `app/modules/inv/application/services/inventario_fisico_service.py` | 4 funciones nuevas: `finalizar_inventario_fisico_servicio` + `get/create/update_inventario_fisico_con_detalles_servicio`; imports UoW + tablas |
| `app/modules/inv/application/services/__init__.py` | Exporta las 7 funciones nuevas + `autorizar_movimiento_servicio` (que existía pero no estaba exportada) |

### Bloque 5 — Routers
| Archivo | Cambio |
|---|---|
| `app/modules/inv/presentation/endpoints_movimientos_proceso.py` | RBAC corregido en 3 endpoints lifecycle: `procesar`, `autorizar`, `anular` |
| `app/modules/inv/presentation/endpoints_movimientos.py` | 3 endpoints nuevos con-detalle + imports schemas nuevos |
| `app/modules/inv/presentation/endpoints_inventario_fisico.py` | RBAC corregido en `anular`; nuevo endpoint `finalizar`; 3 endpoints nuevos con-detalle + imports schemas nuevos |
| `app/modules/inv/presentation/endpoints_inventario_fisico_aprobar.py` | RBAC corregido en `aprobar` |

### Bloque 6 — Seeds RBAC (archivo nuevo)
| Archivo | Cambio |
|---|---|
| `app/docs/database/SEED_PERMISOS_RBAC_INV_LIFECYCLE.sql` | **Nuevo.** 6 permisos lifecycle granulares (MERGE idempotente) |

---

## 2. Endpoints marcados DEPRECATED

| Ruta completa | Método | Motivo | Reemplazado por |
|---|---|---|---|
| `/inv/movimientos-detalle` | POST | Anti-patrón: escritura directa sobre tabla detalle-embebido | `POST /inv/movimientos/con-detalle` |
| `/inv/movimientos-detalle/{id}` | PUT | Anti-patrón: edición directa sobre tabla detalle-embebido | `PUT /inv/movimientos/{id}/con-detalle` |
| `/inv/inventario-fisico-detalle` | POST | Anti-patrón: escritura directa sobre tabla detalle-embebido | `POST /inv/inventario-fisico/con-detalle` |
| `/inv/inventario-fisico-detalle/{id}` | PUT | Anti-patrón: edición directa sobre tabla detalle-embebido | `PUT /inv/inventario-fisico/{id}/con-detalle` |

> Los endpoints GET de estas rutas **no** fueron deprecados: el frontend puede
> necesitarlos para consultas de líneas específicas.

---

## 3. Nuevos endpoints — checklist de seguridad

### 3.1 Movimientos con detalle embebido

| Endpoint | `client_id` | `empresa_id` | RBAC |
|---|---|---|---|
| `GET /inv/movimientos/{id}/con-detalle` | ✅ `current_user.cliente_id` | N/A (solo lectura) | ✅ `inv.movimiento.leer` |
| `POST /inv/movimientos/con-detalle` | ✅ `current_user.cliente_id` | ✅ en body, validado vs tenant | ✅ `inv.movimiento.crear` |
| `PUT /inv/movimientos/{id}/con-detalle` | ✅ `current_user.cliente_id` | ✅ validado si se incluye | ✅ `inv.movimiento.actualizar` |

### 3.2 Inventario físico — nuevo lifecycle

| Endpoint | `client_id` | `empresa_id` | RBAC |
|---|---|---|---|
| `POST /inv/inventario-fisico/{id}/finalizar` | ✅ `current_user.cliente_id` | N/A | ✅ `inv.inventario_fisico.finalizar` |

### 3.3 Inventario físico con detalle embebido

| Endpoint | `client_id` | `empresa_id` | RBAC |
|---|---|---|---|
| `GET /inv/inventario-fisico/{id}/con-detalle` | ✅ `current_user.cliente_id` | N/A (solo lectura) | ✅ `inv.inventario_fisico.leer` |
| `POST /inv/inventario-fisico/con-detalle` | ✅ `current_user.cliente_id` | ✅ en body, validado vs tenant | ✅ `inv.inventario_fisico.crear` |
| `PUT /inv/inventario-fisico/{id}/con-detalle` | ✅ `current_user.cliente_id` | ✅ validado si se incluye | ✅ `inv.inventario_fisico.actualizar` |

### 3.4 RBAC corregido en lifecycle existentes (no son rutas nuevas)

| Endpoint | RBAC anterior | RBAC nuevo |
|---|---|---|
| `POST /inv/{id}/procesar` | `inv.movimiento.actualizar` | ✅ `inv.movimiento.procesar` |
| `POST /inv/{id}/autorizar` | `inv.movimiento.actualizar` | ✅ `inv.movimiento.autorizar` |
| `POST /inv/{id}/anular` | `inv.movimiento.actualizar` | ✅ `inv.movimiento.anular` |
| `POST /inv/inventario-fisico/{id}/anular` | `inv.inventario_fisico.actualizar` | ✅ `inv.inventario_fisico.anular` |
| `POST /inv/inventario-fisico/{id}/aprobar` | `inv.inventario_fisico.actualizar` | ✅ `inv.inventario_fisico.aprobar` |

---

## 4. Endpoints cabecera+detalle — integridad transaccional

| Endpoint | Detalle embebido en body | Transacción atómica (cabecera + detalle) |
|---|---|---|
| `POST /inv/movimientos/con-detalle` | ✅ `detalles: List[MovimientoDetalleCreateEmbebido]` (min 1) | ✅ `unit_of_work`: INSERT cabecera → INSERT detalles → SELECT de vuelta |
| `PUT /inv/movimientos/{id}/con-detalle` | ✅ `detalles: Optional[List[...]]` (replace-all si se provee) | ✅ `unit_of_work`: DELETE detalles → INSERT nuevos → UPDATE cabecera → SELECT |
| `POST /inv/inventario-fisico/con-detalle` | ✅ `detalles: List[InventarioFisicoDetalleCreateEmbebido]` (opcional) | ✅ `unit_of_work`: INSERT cabecera → INSERT detalles → SELECT de vuelta |
| `PUT /inv/inventario-fisico/{id}/con-detalle` | ✅ `detalles: Optional[List[...]]` (replace-all si se provee) | ✅ `unit_of_work`: DELETE detalles → INSERT nuevos → UPDATE cabecera → SELECT |

---

## 5. Verificación — endpoints CORRECTO sin cambios

Los siguientes endpoints existentes **no** tuvieron cambios en ruta, método ni estructura de respuesta:

| Grupo | Endpoints sin cambios |
|---|---|
| Categorías | GET list, GET by id, POST, PUT |
| Unidades de medida | GET list, GET by id, POST, PUT |
| Productos | GET list, GET by id, POST, PUT |
| Almacenes | GET list, GET by id, POST, PUT |
| Stock | GET list, GET by id, GET by producto+almacén, POST, PUT |
| Stock alertas | GET alertas bajo mínimo |
| Tipos de movimiento | GET list, GET by id, POST, PUT |
| Movimientos | GET list, GET by id, POST (simple), PUT (simple) |
| Movimientos detalle (lectura) | GET list, GET by id |
| Movimientos proceso | POST procesar, POST autorizar, POST anular *(solo RBAC corregido)* |
| Inventario físico | GET list, GET by id, POST (simple), PUT (simple) |
| Inventario físico proceso | POST aprobar *(solo RBAC corregido)*, POST anular *(solo RBAC corregido)* |
| Inventario físico detalle (lectura) | GET list, GET by id |
| Kardex | GET list |

---

## 6. Seeds RBAC — permisos agregados

Archivo: `app/docs/database/SEED_PERMISOS_RBAC_INV_LIFECYCLE.sql`

| Código permiso | Recurso | Acción | Descripción |
|---|---|---|---|
| `inv.movimiento.procesar` | movimiento | procesar | Ejecutar procesamiento y aplicar impacto en stock |
| `inv.movimiento.autorizar` | movimiento | autorizar | Autorizar movimiento antes de procesar |
| `inv.movimiento.anular` | movimiento | anular | Anular movimiento (solo si no está procesado) |
| `inv.inventario_fisico.finalizar` | inventario_fisico | finalizar | Cerrar conteo (en_proceso → finalizado) |
| `inv.inventario_fisico.aprobar` | inventario_fisico | aprobar | Aprobar + generar ajuste de stock |
| `inv.inventario_fisico.anular` | inventario_fisico | anular | Anular (no permitido si ya está ajustado) |

> **Acción requerida:** ejecutar el script SQL en cada base de datos de tenant
> **después** de `SEED_PERMISOS_RBAC_INV_FASE4.sql` y asignar los permisos a los
> roles correspondientes en la tabla `rol_permiso`.

---

## 7. Notas de arquitectura

### Patrón header-detail con UnitOfWork
Las operaciones de escritura con detalle embebido usan el patrón `unit_of_work`
heredado de `movimiento_proceso_service.py`. Dentro de la transacción:
- Se ejecutan `INSERT/DELETE` vía `uow.execute(insert(...))` / `uow.execute(delete(...))`
- Se lee el resultado dentro de la misma sesión (antes del commit) para obtener
  columnas `PERSISTED` calculadas por SQL Server
- El rollback es automático ante cualquier excepción

### Replace-all para actualizaciones de detalle
Cuando el body del PUT incluye el campo `detalles` (aunque sea lista vacía),
se eliminan **todas** las líneas existentes y se insertan las nuevas. Si `detalles`
no se incluye en el body, la cabecera se actualiza sin tocar el detalle.

### Rutas de proceso de movimientos
Los endpoints `procesar`, `autorizar` y `anular` de movimientos están montados
**sin prefijo `/movimientos/`** en el router INV (diseño heredado):
- `POST /api/v1/inv/{movimiento_id}/procesar`
- `POST /api/v1/inv/{movimiento_id}/autorizar`
- `POST /api/v1/inv/{movimiento_id}/anular`

Este diseño no se modificó para no romper integraciones existentes.
