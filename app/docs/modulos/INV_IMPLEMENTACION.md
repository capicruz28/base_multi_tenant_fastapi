# INV — Implementación y verificación final (Inventarios y Almacenes)

Módulo: **Inventarios y Almacenes** (`INV`)  
Alcance: cierre de **Fase 3–4** según `docs/prompts/PROMPT_MODULO_MAESTRO.md` y `docs/bd/INV_TABLAS.sql`.

---

## 1) Archivos creados o modificados

### Creados

- `app/docs/modulos/AUDITORIA_INV.md` — auditoría Fase 2 (referencia).
- `app/infrastructure/database/queries/inv/moneda_queries.py` — resolución de `moneda_id` por código ISO (`cat_moneda.codigo`).

### Modificados

- `app/modules/inv/presentation/schemas.py` — `moneda_id` en movimiento/detalle; compatibilidad legacy con `moneda` (string).
- `app/infrastructure/database/queries/inv/__init__.py` — export de `get_moneda_by_codigo`.
- `app/modules/inv/application/services/movimiento_service.py` — resolución/persistencia de `moneda_id`.
- `app/modules/inv/application/services/movimiento_detalle_service.py` — resolución/persistencia de `moneda_id`.
- `app/modules/inv/application/services/movimiento_proceso_service.py` — `autorizar_movimiento_servicio`; **procesamiento atómico** (transacción) y operación de stock con `moneda_id`.
- `app/modules/inv/application/services/inventario_fisico_aprobacion_service.py` — aprobación **atómica** (transacción) generando movimientos con `moneda_id`.
- `app/modules/inv/application/services/inventario_fisico_service.py` — `anular_inventario_fisico_servicio` y validaciones de estado en update.
- `app/modules/inv/presentation/endpoints_categorias.py` — `DELETE` + `reactivar`.
- `app/modules/inv/presentation/endpoints_unidades_medida.py` — `DELETE` + `reactivar`.
- `app/modules/inv/presentation/endpoints_productos.py` — `DELETE` + `reactivar`.
- `app/modules/inv/presentation/endpoints_almacenes.py` — `DELETE` + `reactivar`.
- `app/modules/inv/presentation/endpoints_tipos_movimiento.py` — `DELETE` + `reactivar`.
- `app/modules/inv/presentation/endpoints_movimientos_proceso.py` — `POST .../autorizar`.
- `app/modules/inv/presentation/endpoints_inventario_fisico.py` — `POST .../anular`.
- `app/modules/inv/presentation/endpoints_stock.py` — `POST`/`PUT` marcados como **internos** (`deprecated=True` en OpenAPI; mismas rutas/métodos/response).
- `app/docs/database/SEED_PERMISOS_INV.sql` — seeds RBAC: permisos `inv.<recurso>.eliminar` para bajas lógicas.
- `app/docs/database/SEED_PERMISOS_RBAC_INV_FASE4.sql` — seeds RBAC: mismos permisos `inv.<recurso>.eliminar` (script alterno / fase 4).

---

## 2) Endpoints nuevos — tenant (`cliente_id`), `empresa_id` y RBAC

Convención del módulo: `client_id = current_user.cliente_id` en todos los handlers; permisos con `require_permission("inv.<recurso>.<accion>")`.

| Ruta (prefijo `/inv`) | Método | RBAC | `cliente_id` | `empresa_id` (validación) |
|---|---|---|---|---|
| `/categorias/{id}` | DELETE | `inv.categoria.eliminar` | Sí (token → service → queries) | No aplica en path; el registro ya tiene `empresa_id` en BD; no se altera ownership en este endpoint |
| `/categorias/{id}/reactivar` | POST | `inv.categoria.actualizar` | Sí | Igual que arriba |
| `/unidades-medida/{id}` | DELETE | `inv.unidad_medida.eliminar` | Sí | Igual |
| `/unidades-medida/{id}/reactivar` | POST | `inv.unidad_medida.actualizar` | Sí | Igual |
| `/productos/{id}` | DELETE | `inv.producto.eliminar` | Sí | Igual |
| `/productos/{id}/reactivar` | POST | `inv.producto.actualizar` | Sí | Igual |
| `/almacenes/{id}` | DELETE | `inv.almacen.eliminar` | Sí | Igual |
| `/almacenes/{id}/reactivar` | POST | `inv.almacen.actualizar` | Sí | Igual |
| `/tipos-movimiento/{id}` | DELETE | `inv.tipo_movimiento.eliminar` | Sí | Igual |
| `/tipos-movimiento/{id}/reactivar` | POST | `inv.tipo_movimiento.actualizar` | Sí | Igual |
| `/movimientos/{movimiento_id}/autorizar` | POST | `inv.movimiento.actualizar` | Sí | No aplica en path; la cabecera valida existencia dentro del tenant vía queries |
| `/inventario-fisico/{inventario_fisico_id}/anular` | POST | `inv.inventario_fisico.actualizar` | Sí | No aplica en path; la cabecera valida existencia dentro del tenant vía queries |

Notas:

- **Moneda (`moneda_id`)**: en creación/actualización de movimiento y detalle, si no viene `moneda_id`, se intenta resolver por `moneda` legacy (default `"PEN"`) contra `cat_moneda`.
- **Stock interno**: `POST /stock` y `PUT /stock/{stock_id}` permanecen; se documentan como **uso interno** y quedan marcados como `deprecated` en OpenAPI (no cambian método/ruta/response).

---

## 3) Verificación de contratos (endpoints existentes)

- **Rutas y métodos** de endpoints ya existentes de `INV` no se renombraron ni se eliminaron.
- **Estructura de response** de endpoints existentes se mantiene en los mismos `response_model`.
- Cambios observables en OpenAPI:
  - Esquemas de **request/response** de movimiento/detalle incluyen **`moneda_id`** además del campo legacy `moneda` (compatibilidad).
  - `POST/PUT` de stock figuran como **deprecated** (metadato OpenAPI).

---

## 4) Reglas de lifecycle y transacciones (brechas cerradas)

### Lifecycle (validaciones de estado)

- **Movimientos (`inv_movimiento`)**:
  - Si `requiere_autorizacion = 1`, **no se permite procesar** si el `estado != "autorizado"` (conflict 409).
  - **No se permite editar** (`PUT`) si el `estado != "borrador"` (conflict 409).
- **Movimiento detalle (`inv_movimiento_detalle`)**:
  - **No se permite editar** si la cabecera (`inv_movimiento`) no está en `estado="borrador"` (conflict 409).
- **Inventario físico (`inv_inventario_fisico`)**:
  - **No se permite editar** si `estado ∈ {"ajustado","anulado"}` (conflict 409).
  - **Anulación** disponible vía endpoint dedicado (no elimina físicamente; cambia estado).

### Transacciones (atomicidad / rollback)

- **Procesamiento de movimiento** (`procesar_movimiento_servicio`): opera dentro de una **transacción** (Unit of Work). Si falla cualquier ajuste de stock o el marcado final de estado, se revierte todo.
- **Aprobación de inventario físico** (`aprobar_inventario_fisico_servicio`): todo el flujo (crear movimiento, crear detalle, procesar stock, cerrar inventario) corre dentro de **una sola transacción**, evitando estados intermedios inconsistentes.

---

## 5) Cierre del módulo (estado)

- **INV queda cerrado** respecto al alcance acordado: moneda alineada a BD con compatibilidad legacy, autorización obligatoria antes de procesar cuando aplica, anulación de inventario físico, baja lógica/reactivación en maestros, escritura de stock marcada como interna, validaciones de estado y transacciones para operaciones multi-tabla.

Si en el futuro se requiere endurecer reglas (por ejemplo: exigir `moneda_id` obligatorio y eliminar `moneda` legacy del contrato), debe planificarse como cambio de contrato explícito y coordinación con clientes.
