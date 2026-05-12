# Auditoria Modulo BDG - Presupuestos

## 1. Tablas detectadas y tipo

Fuente: `docs/bd/BDG_TABLAS.sql`. Se filtraron unicamente tablas con prefijo `bdg_`.

| Tabla | Tipo | CRUD esperado | Observaciones |
|---|---|---|---|
| `bdg_presupuesto` | Transaccional, cabecera | Crear borrador, listar, detalle, actualizar solo borrador, aprobar, procesar, anular | Tiene `cliente_id` y `empresa_id`. No tiene `es_activo`. |
| `bdg_presupuesto_detalle` | Transaccional, detalle | Debe manejarse embebido en cabecera para operaciones transaccionales | Tiene `cliente_id` y `empresa_id`. No tiene `es_activo`. |

### `bdg_presupuesto`

Campos BD:

- `presupuesto_id UNIQUEIDENTIFIER`
- `cliente_id UNIQUEIDENTIFIER`
- `empresa_id UNIQUEIDENTIFIER`
- `codigo_presupuesto NVARCHAR(20)`
- `nombre NVARCHAR(100)`
- `año INT`
- `tipo_presupuesto NVARCHAR(20)`
- `monto_total_presupuestado DECIMAL(18,2)`
- `monto_total_ejecutado DECIMAL(18,2)`
- `porcentaje_ejecucion` calculado persistido
- `estado NVARCHAR(20)`
- `fecha_aprobacion DATETIME`
- `observaciones NVARCHAR(MAX)`
- `fecha_creacion DATETIME`
- `usuario_creacion_id UNIQUEIDENTIFIER`

Claves foraneas:

- `empresa_id` -> `org_empresa(empresa_id)`

Restricciones:

- `UQ_bdg_codigo UNIQUE(cliente_id, empresa_id, codigo_presupuesto)`

### `bdg_presupuesto_detalle`

Campos BD:

- `presupuesto_detalle_id UNIQUEIDENTIFIER`
- `cliente_id UNIQUEIDENTIFIER`
- `empresa_id UNIQUEIDENTIFIER`
- `presupuesto_id UNIQUEIDENTIFIER`
- `cuenta_id UNIQUEIDENTIFIER`
- `centro_costo_id UNIQUEIDENTIFIER`
- `mes INT`
- `monto_presupuestado DECIMAL(18,2)`
- `monto_ejecutado DECIMAL(18,2)`
- `monto_disponible` calculado persistido
- `observaciones NVARCHAR(255)`
- `fecha_creacion DATETIME`

Claves foraneas:

- `empresa_id` -> `org_empresa(empresa_id)`
- `presupuesto_id` -> `bdg_presupuesto(presupuesto_id)`
- `cuenta_id` -> `fin_plan_cuentas(cuenta_id)`
- `centro_costo_id` -> `org_centro_costo(centro_costo_id)`

## 2. Endpoints existentes

Prefijo global: `/bdg`.

| Ruta | Metodo | Entidad | Tiene tenant? | Tiene RBAC? |
|---|---|---|---|---|
| `/bdg/presupuestos` | GET | `bdg_presupuesto` | Parcial: usa `cliente_id`; `empresa_id` es opcional | Si: `bdg.presupuesto.leer` |
| `/bdg/presupuestos/{presupuesto_id}` | GET | `bdg_presupuesto` | Parcial: usa `cliente_id`; no valida `empresa_id` | Si: `bdg.presupuesto.leer` |
| `/bdg/presupuestos` | POST | `bdg_presupuesto` | Parcial: fuerza `cliente_id`; recibe `empresa_id` en body | Si: `bdg.presupuesto.crear` |
| `/bdg/presupuestos/{presupuesto_id}` | PUT | `bdg_presupuesto` | Parcial: usa `cliente_id`; no valida `empresa_id` | Si: `bdg.presupuesto.actualizar` |
| `/bdg/presupuesto-detalle` | GET | `bdg_presupuesto_detalle` | Parcial: usa `cliente_id`; no filtra `empresa_id` | Si: `bdg.presupuesto_detalle.leer` |
| `/bdg/presupuesto-detalle/{presupuesto_detalle_id}` | GET | `bdg_presupuesto_detalle` | Parcial: usa `cliente_id`; no valida `empresa_id` | Si: `bdg.presupuesto_detalle.leer` |
| `/bdg/presupuesto-detalle` | POST | `bdg_presupuesto_detalle` | Parcial: fuerza `cliente_id`; deriva `empresa_id` desde cabecera | Si: `bdg.presupuesto_detalle.crear` |
| `/bdg/presupuesto-detalle/{presupuesto_detalle_id}` | PUT | `bdg_presupuesto_detalle` | Parcial: usa `cliente_id`; no valida `empresa_id` | Si: `bdg.presupuesto_detalle.actualizar` |

## 3. Endpoints faltantes

### `bdg_presupuesto`

| Ruta sugerida | Metodo | Accion | Permiso RBAC sugerido | Motivo |
|---|---|---|---|---|
| `/bdg/presupuestos/{presupuesto_id}/aprobar` | POST | Aprobar | `bdg.presupuesto.aprobar` | Requerido para modulo transaccional. Debe cambiar `estado` de `borrador` a `aprobado` y setear `fecha_aprobacion`. |
| `/bdg/presupuestos/{presupuesto_id}/procesar` | POST | Procesar / poner vigente | `bdg.presupuesto.procesar` | Requerido para modulo transaccional. En BD el estado funcional equivalente seria `vigente`. |
| `/bdg/presupuestos/{presupuesto_id}/anular` | POST | Anular | `bdg.presupuesto.anular` | Requerido por prompt maestro para transaccionales. La BD no declara `anulado` en comentario de estado, por lo que debe definirse el comportamiento antes de implementar. |

### `bdg_presupuesto_detalle`

No se recomiendan endpoints transaccionales independientes de aprobar/procesar/anular para el detalle. El prompt maestro indica que, en modulos transaccionales, el detalle debe manejarse embebido en la cabecera.

Endpoint estructural sugerido para alinear cabecera/detalle:

| Ruta sugerida | Metodo | Accion | Permiso RBAC sugerido | Motivo |
|---|---|---|---|---|
| `/bdg/presupuestos/{presupuesto_id}/detalles` | GET | Listar detalle de presupuesto | `bdg.presupuesto_detalle.leer` | Ruta mas consistente con patron cabecera/detalle usado en FIN. Actualmente existe `/bdg/presupuesto-detalle`. |
| `/bdg/presupuestos/{presupuesto_id}/detalles` | POST | Crear detalle dentro de cabecera | `bdg.presupuesto_detalle.crear` | Permite derivar y validar `empresa_id` desde la cabecera. |
| `/bdg/presupuestos/detalles/{presupuesto_detalle_id}` | GET | Ver detalle | `bdg.presupuesto_detalle.leer` | Mantiene acceso por id sin ambiguedad con rutas de cabecera. |
| `/bdg/presupuestos/detalles/{presupuesto_detalle_id}` | PUT | Actualizar detalle | `bdg.presupuesto_detalle.actualizar` | Debe validar que la cabecera este en `borrador`. |

Nota: los endpoints existentes no deben eliminarse ni romper contratos. Si se implementan rutas nuevas, deben convivir o reemplazarse solo bajo confirmacion explicita.

## 4. Brechas funcionales

### `bdg_presupuesto`

- Falta endpoint de aprobar.
- Falta endpoint de procesar / poner vigente.
- Falta endpoint de anular.
- `PUT /bdg/presupuestos/{presupuesto_id}` no valida que el presupuesto este en `borrador`.
- `POST /bdg/presupuestos` permite recibir `estado`, `monto_total_ejecutado`, `fecha_aprobacion` y `usuario_creacion_id` desde el body; para crear borrador deberia controlarse desde backend.
- No se observa validacion de unicidad funcional previa para `codigo_presupuesto` dentro de `(cliente_id, empresa_id)`; existe restriccion BD, pero el servicio no anticipa error de negocio.
- No hay operacion atomica cabecera + detalle. Para un transaccional, el detalle deberia poder manejarse embebido en la cabecera cuando aplique.

### `bdg_presupuesto_detalle`

- El detalle tiene CRUD independiente; para operaciones transaccionales debe estar subordinado a la cabecera.
- `PUT /bdg/presupuesto-detalle/{presupuesto_detalle_id}` no valida que el presupuesto cabecera este en `borrador`.
- `POST /bdg/presupuesto-detalle` deriva `empresa_id` desde cabecera, pero si no encuentra cabecera no se observa error explicito antes del insert.
- `GET /bdg/presupuesto-detalle` no filtra por `empresa_id` pese a que la tabla lo tiene.
- No hay validacion explicita de que `cuenta_id` y `centro_costo_id` pertenezcan al mismo tenant/empresa.

## 5. Campos faltantes en schemas

### `PresupuestoCreate`

Campos BD cubiertos:

- Cubre `empresa_id`, `codigo_presupuesto`, `nombre`, `año` como `anio`, `tipo_presupuesto`, `monto_total_presupuestado`, `monto_total_ejecutado`, `estado`, `fecha_aprobacion`, `observaciones`, `usuario_creacion_id`.

Campos BD no expuestos por diseno correcto:

- `presupuesto_id`, `cliente_id`, `fecha_creacion`.

Campos calculados:

- `porcentaje_ejecucion` no debe recibirse en Create.

Observacion:

- Aunque no falta campo, `Create` expone campos que deberian ser controlados por backend en una creacion de borrador: `estado`, `monto_total_ejecutado`, `fecha_aprobacion`, `usuario_creacion_id`.

### `PresupuestoUpdate`

Campos BD faltantes o no actualizables:

- `empresa_id` no esta en Update. Puede ser correcto si no se permite mover presupuestos entre empresas.
- `año` / `anio` no esta en Update. Si se permite editar borrador, falta exponerlo.
- `usuario_creacion_id` no esta en Update. Correcto: no deberia editarse.
- `fecha_creacion` no esta en Update. Correcto.

Observacion:

- `estado` y `fecha_aprobacion` aparecen en Update, pero deberian moverse a acciones dedicadas (`aprobar`, `procesar`, `anular`) para no alterar estados por PUT generico.

### `PresupuestoRead`

Campos BD faltantes:

- No faltan campos reales relevantes. `año` se expone como `anio`.

Campos calculados:

- `porcentaje_ejecucion` esta incluido y se calcula en servicio.

### `PresupuestoDetalleCreate`

Campos BD cubiertos:

- Cubre `presupuesto_id`, `cuenta_id`, `centro_costo_id`, `mes`, `monto_presupuestado`, `monto_ejecutado`, `observaciones`.

Campos BD faltantes:

- `empresa_id` no esta en Create. Actualmente se deriva desde `bdg_presupuesto`, lo cual es correcto si se valida la cabecera.

Campos BD no expuestos por diseno correcto:

- `presupuesto_detalle_id`, `cliente_id`, `fecha_creacion`.

Campos calculados:

- `monto_disponible` no debe recibirse en Create.

### `PresupuestoDetalleUpdate`

Campos BD faltantes o no actualizables:

- `empresa_id` no esta en Update. Correcto si se deriva desde cabecera y no se permite cambiar empresa.
- `presupuesto_id` no esta en Update. Correcto si no se permite mover detalle entre cabeceras.
- `fecha_creacion` no esta en Update. Correcto.

### `PresupuestoDetalleRead`

Campos BD faltantes:

- `empresa_id` falta en `PresupuestoDetalleRead`, aunque existe en `bdg_presupuesto_detalle`.

Campos calculados:

- `monto_disponible` esta incluido y se calcula en servicio.

## 6. Problemas de tenant o RBAC

### Tenant

- Todas las queries filtran por `cliente_id`.
- Varias operaciones no validan `empresa_id` aunque ambas tablas lo tienen:
  - `GET /bdg/presupuestos/{presupuesto_id}`
  - `PUT /bdg/presupuestos/{presupuesto_id}`
  - `GET /bdg/presupuesto-detalle`
  - `GET /bdg/presupuesto-detalle/{presupuesto_detalle_id}`
  - `PUT /bdg/presupuesto-detalle/{presupuesto_detalle_id}`
- `GET /bdg/presupuestos` acepta `empresa_id` opcional; si el contexto del usuario requiere empresa activa, deberia validarse contra dicho contexto.
- `POST /bdg/presupuesto-detalle` deriva `empresa_id` desde la cabecera, pero debe fallar explicitamente si `presupuesto_id` no existe para el `cliente_id`.

### RBAC

- Los endpoints existentes usan `require_permission`.
- Permisos existentes en codigo:
  - `bdg.presupuesto.leer`
  - `bdg.presupuesto.crear`
  - `bdg.presupuesto.actualizar`
  - `bdg.presupuesto_detalle.leer`
  - `bdg.presupuesto_detalle.crear`
  - `bdg.presupuesto_detalle.actualizar`
- Faltan permisos para acciones transaccionales:
  - `bdg.presupuesto.aprobar`
  - `bdg.presupuesto.procesar`
  - `bdg.presupuesto.anular`

## 7. Codigo marcado como obsoleto o incorrecto

No se debe eliminar codigo existente. Se marca para correccion o convivencia controlada:

- `PUT /bdg/presupuestos/{presupuesto_id}` permite cambios sin validar estado `borrador`.
- `PUT /bdg/presupuesto-detalle/{presupuesto_detalle_id}` permite cambios sin validar estado `borrador` de la cabecera.
- CRUD independiente de detalle en `/bdg/presupuesto-detalle` no sigue el patron transaccional recomendado de detalle embebido en cabecera.
- `PresupuestoDetalleRead` no incluye `empresa_id`.
- El modelo SQLAlchemy usa `ondelete="SET NULL"` para `centro_costo_id`, mientras el DDL del modulo indica `ON DELETE NO ACTION`.

## 8. Alcance recomendado para Fase 3

Orden sugerido, respetando el prompt maestro:

1. Schemas:
   - Agregar `empresa_id` a `PresupuestoDetalleRead`.
   - Revisar si `anio` debe permitirse en `PresupuestoUpdate`.
   - Retirar de flujo generico o ignorar en servicio los campos de estado controlado por acciones.
2. Models/ORM:
   - Alinear FK de `centro_costo_id` con `ON DELETE NO ACTION` segun DDL, sin modificar estructura de BD.
3. Repositories/queries:
   - Agregar validacion/filtro de `empresa_id` cuando aplique.
   - Agregar queries para transiciones de estado.
   - Validar cabecera antes de insertar detalle.
4. Services:
   - Enforce `borrador` para update de cabecera/detalle.
   - Implementar `aprobar`, `procesar` y `anular`.
   - Controlar campos que no deben venir del body en creacion/actualizacion.
5. Routers:
   - Agregar endpoints transaccionales faltantes.
   - Considerar rutas anidadas para detalles sin romper las existentes.
6. Seeds RBAC:
   - Agregar permisos faltantes de acciones transaccionales si no existen.

## 9. Estado de Fase 2

Fase 2 completada. Detener aqui y esperar confirmacion antes de implementar Fase 3.
