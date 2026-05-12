# Implementacion Modulo WFL - Motor de Flujos (Workflow)

## Resumen

Modulo cerrado para la tabla `wfl_flujo_trabajo`, filtrada desde `docs/bd/WFL_TABLAS.sql`.

Tipo de modulo: maestro.

Tabla implementada/auditada:

| Tabla | Tipo | Estado |
|---|---|---|
| `wfl_flujo_trabajo` | Maestro | CRUD maestro completado con baja logica |

## Archivos modificados o creados

| Archivo | Tipo de cambio |
|---|---|
| `app/docs/modulos/AUDITORIA_WFL.md` | Creado en Fase 2 con brechas funcionales y tecnicas |
| `app/infrastructure/database/queries/wfl/flujo_trabajo_queries.py` | Actualizado para validar `empresa_id` opcional en GET/PUT por ID |
| `app/modules/wfl/application/services/flujo_trabajo_service.py` | Actualizado para propagar `empresa_id` opcional en GET/PUT por ID |
| `app/modules/wfl/presentation/endpoints_flujo_trabajo.py` | Actualizado con validacion `empresa_id`, baja logica y reactivacion |
| `app/docs/database/SEED_PERMISOS_RBAC_WFL.sql` | Creado con permisos RBAC requeridos para `wfl.flujo.*` |
| `app/docs/modulos/WFL_IMPLEMENTACION.md` | Documento final de cierre |

## Endpoints finales

Base del modulo: `/wfl`

Recurso: `/flujos-trabajo`

| Metodo | Ruta | Accion | cliente_id | empresa_id | RBAC |
|---|---|---|---|---|---|
| `GET` | `/wfl/flujos-trabajo` | Listar flujos | Si, desde usuario autenticado | Si, query opcional | `wfl.flujo.leer` |
| `GET` | `/wfl/flujos-trabajo/{flujo_id}` | Obtener detalle | Si, desde usuario autenticado | Si, query opcional | `wfl.flujo.leer` |
| `POST` | `/wfl/flujos-trabajo` | Crear flujo | Si, desde usuario autenticado | Si, body `empresa_id` | `wfl.flujo.crear` |
| `PUT` | `/wfl/flujos-trabajo/{flujo_id}` | Actualizar flujo | Si, desde usuario autenticado | Si, query opcional | `wfl.flujo.actualizar` |
| `DELETE` | `/wfl/flujos-trabajo/{flujo_id}` | Desactivar flujo (`es_activo = 0`) | Si, desde usuario autenticado | Si, query opcional | `wfl.flujo.eliminar` |
| `POST` | `/wfl/flujos-trabajo/{flujo_id}/reactivar` | Reactivar flujo (`es_activo = 1`) | Si, desde usuario autenticado | Si, query opcional | `wfl.flujo.actualizar` |

## Verificacion de contratos

- No se eliminaron endpoints existentes.
- No se cambiaron rutas existentes.
- No se cambiaron metodos HTTP existentes.
- No se modifico la estructura de response de endpoints existentes.
- Los nuevos endpoints siguen el patron de modulo maestro con baja logica.
- No se modifico estructura de base de datos.
- No se eliminaron registros fisicamente; la baja usa `es_activo = 0`.

## Verificacion multi-tenant

- Todas las queries mantienen filtro por `cliente_id`.
- `GET` por ID soporta filtro adicional por `empresa_id`.
- `PUT` por ID soporta filtro adicional por `empresa_id`.
- `DELETE` por ID reutiliza la actualizacion con filtro por `cliente_id` y `empresa_id` opcional.
- `POST /reactivar` reutiliza la actualizacion con filtro por `cliente_id` y `empresa_id` opcional.

## Verificacion RBAC

Permisos usados por el backend:

| Permiso | Estado |
|---|---|
| `wfl.flujo.leer` | Agregado en seed |
| `wfl.flujo.crear` | Agregado en seed |
| `wfl.flujo.actualizar` | Agregado en seed |
| `wfl.flujo.eliminar` | Agregado en seed |

Seed creado:

`app/docs/database/SEED_PERMISOS_RBAC_WFL.sql`

El seed usa `MERGE` por `codigo`, es seguro para multiples ejecuciones y reactiva permisos existentes si estaban inactivos.

## Verificacion tecnica

- `app/modules/wfl/presentation/schemas.py`: sin cambios necesarios.
- `app/infrastructure/database/queries/wfl/flujo_trabajo_queries.py`: GET/PUT por ID validan `empresa_id` cuando se proporciona.
- `app/modules/wfl/application/services/flujo_trabajo_service.py`: service propaga `empresa_id` opcional.
- `app/modules/wfl/presentation/endpoints_flujo_trabajo.py`: endpoints protegidos por RBAC y tenant.
- Linter revisado en archivos Python modificados: sin errores reportados.

## Estado final

Modulo `WFL` cerrado para Fase 3 y documentado para Fase 4.
