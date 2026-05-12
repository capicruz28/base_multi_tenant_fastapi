# Auditoria Modulo WFL - Motor de Flujos (Workflow)

## Tablas detectadas y tipo

| Tabla | Tipo | CRUD esperado | Observaciones |
|---|---|---|---|
| `wfl_flujo_trabajo` | Maestro | Crear, listar, detalle, actualizar, activar/desactivar | Configura flujos de trabajo por `cliente_id` y `empresa_id`. Tiene baja logica con `es_activo`. |

### Campos de `wfl_flujo_trabajo`

| Campo | Tipo BD | Observacion |
|---|---|---|
| `flujo_id` | `UNIQUEIDENTIFIER` | PK, default `NEWID()` |
| `cliente_id` | `UNIQUEIDENTIFIER` | Obligatorio, tenant cliente |
| `empresa_id` | `UNIQUEIDENTIFIER` | Obligatorio, tenant empresa |
| `codigo_flujo` | `NVARCHAR(20)` | Obligatorio, unico por cliente/empresa |
| `nombre` | `NVARCHAR(150)` | Obligatorio |
| `descripcion` | `NVARCHAR(500)` | Opcional |
| `tipo_flujo` | `NVARCHAR(30)` | Obligatorio |
| `modulo_aplicable` | `NVARCHAR(10)` | Opcional |
| `definicion_pasos` | `NVARCHAR(MAX)` | Opcional, JSON |
| `es_activo` | `BIT` | Obligatorio, default `1` |
| `fecha_creacion` | `DATETIME` | Obligatorio, default `GETDATE()` |

### Claves foraneas

| Campo | Referencia |
|---|---|
| `empresa_id` | `org_empresa(empresa_id)` |

## Endpoints existentes

Base registrada: `/wfl`

Router del recurso: `/flujos-trabajo`

| Ruta | Metodo | Entidad | Tiene tenant? | Tiene RBAC? | Observacion |
|---|---|---|---|---|---|
| `/wfl/flujos-trabajo` | `GET` | `wfl_flujo_trabajo` | Parcial | Si, `wfl.flujo.leer` | Filtra por `cliente_id` y acepta `empresa_id` opcional. |
| `/wfl/flujos-trabajo/{flujo_id}` | `GET` | `wfl_flujo_trabajo` | Parcial | Si, `wfl.flujo.leer` | Filtra por `cliente_id`, pero no recibe ni valida `empresa_id`. |
| `/wfl/flujos-trabajo` | `POST` | `wfl_flujo_trabajo` | Si | Si, `wfl.flujo.crear` | Usa `cliente_id` del usuario y `empresa_id` del body. |
| `/wfl/flujos-trabajo/{flujo_id}` | `PUT` | `wfl_flujo_trabajo` | Parcial | Si, `wfl.flujo.actualizar` | Filtra por `cliente_id`, pero no recibe ni valida `empresa_id`. |

## Endpoints faltantes

Como `wfl_flujo_trabajo` es tabla maestra con `es_activo`, faltan endpoints de baja logica y reactivacion.

| Ruta sugerida | Metodo | Entidad | Permiso sugerido | Motivo |
|---|---|---|---|---|
| `/wfl/flujos-trabajo/{flujo_id}` | `DELETE` | `wfl_flujo_trabajo` | `wfl.flujo.eliminar` | Desactivar con `es_activo = 0`, sin borrado fisico. |
| `/wfl/flujos-trabajo/{flujo_id}/reactivar` | `POST` | `wfl_flujo_trabajo` | `wfl.flujo.actualizar` | Reactivar con `es_activo = 1`. |

## Campos faltantes en schemas

No se detectan campos funcionales de BD ausentes en `FlujoTrabajoRead`; contiene todos los campos reales de `wfl_flujo_trabajo`.

`FlujoTrabajoCreate` incluye los campos necesarios para crear el recurso:

- `empresa_id`
- `codigo_flujo`
- `nombre`
- `descripcion`
- `tipo_flujo`
- `modulo_aplicable`
- `definicion_pasos`
- `es_activo`

Campos omitidos correctamente en `Create` porque los aporta el sistema o la BD:

- `flujo_id`
- `cliente_id`
- `fecha_creacion`

`FlujoTrabajoUpdate` permite actualizar los campos editables principales:

- `codigo_flujo`
- `nombre`
- `descripcion`
- `tipo_flujo`
- `modulo_aplicable`
- `definicion_pasos`
- `es_activo`

Observacion: `empresa_id` no esta en `FlujoTrabajoUpdate`; para mantener el patron multi-tenant, la validacion de empresa debe hacerse como parametro/filtro del endpoint y query, no necesariamente como campo editable del schema.

## Problemas de tenant o RBAC

### Tenant

- `GET /wfl/flujos-trabajo` valida `cliente_id` y permite filtrar por `empresa_id`.
- `POST /wfl/flujos-trabajo` asigna `cliente_id` desde el usuario autenticado y recibe `empresa_id` en el body.
- `GET /wfl/flujos-trabajo/{flujo_id}` no valida `empresa_id`, aunque la tabla tiene `empresa_id`.
- `PUT /wfl/flujos-trabajo/{flujo_id}` no valida `empresa_id`, aunque la tabla tiene `empresa_id`.
- Las queries `get_flujo_trabajo_by_id` y `update_flujo_trabajo` filtran solo por `cliente_id` + `flujo_id`; deben soportar filtro opcional/obligatorio de `empresa_id` segun el patron del modulo de referencia.

### RBAC

- Los endpoints existentes tienen RBAC.
- El patron usado es `wfl.flujo.accion`.
- Faltan permisos/endpoints para baja logica y reactivacion:
  - `wfl.flujo.eliminar`
  - `wfl.flujo.actualizar` para reactivar, si se mantiene el patron de modulos maestros.

## Codigo marcado como obsoleto o incorrecto

No se debe eliminar codigo existente. Se marcan ajustes necesarios:

- `app/modules/wfl/presentation/endpoints_flujo_trabajo.py`: detalle y actualizacion deben recibir/validar `empresa_id` porque la tabla lo tiene.
- `app/modules/wfl/application/services/flujo_trabajo_service.py`: `get_flujo_trabajo_by_id` y `update_flujo_trabajo` deben aceptar `empresa_id`.
- `app/infrastructure/database/queries/wfl/flujo_trabajo_queries.py`: `get_flujo_trabajo_by_id` y `update_flujo_trabajo` deben filtrar tambien por `empresa_id` cuando se proporcione.
- Faltan funciones de servicio/query para desactivar y reactivar con baja logica, o reutilizar `update_flujo_trabajo` con `es_activo`.

## Resumen de brechas

| Brecha | Severidad | Fase sugerida |
|---|---|---|
| Falta endpoint de desactivar (`es_activo = 0`) | Media | Fase 3 |
| Falta endpoint de reactivar (`es_activo = 1`) | Media | Fase 3 |
| Detalle no valida `empresa_id` | Alta | Fase 3 |
| Actualizacion no valida `empresa_id` | Alta | Fase 3 |
| Queries de detalle/actualizacion no filtran por `empresa_id` | Alta | Fase 3 |

## Detencion obligatoria

Fase 2 completada. Esperar confirmacion antes de iniciar Fase 3.
