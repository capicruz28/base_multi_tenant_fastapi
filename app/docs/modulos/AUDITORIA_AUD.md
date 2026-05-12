# Auditoría de módulo: AUD — Auditoría y Trazabilidad

## Tablas detectadas y su tipo

### `aud_log_auditoria` (transaccional / log)
- **Propósito**: registro de eventos de auditoría (trazabilidad de acciones por módulo/tabla/registro).
- **Tenant**:
  - **cliente_id**: sí (obligatorio)
  - **empresa_id**: sí (obligatorio)
  - **es_activo**: no aplica (tabla de log)
- **Campos (BD)**:
  - `log_id` `UNIQUEIDENTIFIER` (PK)
  - `cliente_id` `UNIQUEIDENTIFIER` (NOT NULL)
  - `empresa_id` `UNIQUEIDENTIFIER` (NOT NULL, FK a `org_empresa.empresa_id`)
  - `fecha_evento` `DATETIME` (NOT NULL, default `GETDATE()`)
  - `usuario_id` `UNIQUEIDENTIFIER` (NULL)
  - `usuario_nombre` `NVARCHAR(150)` (NULL)
  - `modulo` `NVARCHAR(10)` (NOT NULL)
  - `tabla` `NVARCHAR(100)` (NOT NULL)
  - `accion` `NVARCHAR(20)` (NOT NULL)
  - `registro_id` `UNIQUEIDENTIFIER` (NULL)
  - `registro_descripcion` `NVARCHAR(255)` (NULL)
  - `valores_anteriores` `NVARCHAR(MAX)` (NULL, JSON)
  - `valores_nuevos` `NVARCHAR(MAX)` (NULL, JSON)
  - `ip_address` `NVARCHAR(45)` (NULL)
  - `user_agent` `NVARCHAR(500)` (NULL)
  - `observaciones` `NVARCHAR(500)` (NULL)

## Endpoints existentes

Archivo principal de inclusión de router:
- `app/modules/aud/presentation/endpoints.py` incluye `prefix="/log-auditoria"` con tag `"AUD - Log de Auditoría"`.

Tabla de endpoints detectados:

| Ruta | Método | Entidad | Tiene tenant? | Tiene RBAC? |
|------|--------|---------|---------------|-------------|
| `/log-auditoria` | GET | `aud_log_auditoria` | Sí (`current_user.cliente_id` + filtros opcionales `empresa_id`, etc.) | Sí (`aud.log.leer`) |
| `/log-auditoria/{log_id}` | GET | `aud_log_auditoria` | Sí (`current_user.cliente_id`) | Sí (`aud.log.leer`) |
| `/log-auditoria` | POST | `aud_log_auditoria` | Sí (`current_user.cliente_id` en insert) | Sí (actual: `aud.log.leer`) |

Notas técnicas observadas:
- **Capa service** (`app/modules/aud/application/services/log_auditoria_service.py`) delega a queries y mapea filas a `LogAuditoriaRead`.
- **Capa queries** (`app/infrastructure/database/queries/aud/log_auditoria_queries.py`) aplica filtro **obligatorio** `cliente_id` y filtro opcional `empresa_id`.
- **Operaciones soportadas**: `list`, `get_by_id`, `create`. No existen `update/delete` (correcto para un log).

## Endpoints faltantes (con ruta sugerida y método)

Para una tabla tipo log/analítica, el patrón correcto es **solo lectura** (y escritura interna si aplica). Con la BD actual, no se identifican endpoints “obligatorios” faltantes.

Sugerencias (no obligatorias) si se decide ampliar lectura, sin cambiar contratos existentes:
- Filtros adicionales (si se requieren) deben ser **query params** y siempre mantener `cliente_id` por contexto.

## Campos faltantes en schemas

Comparación `aud_log_auditoria` (BD) vs schemas (`app/modules/aud/presentation/schemas.py`):
- **`LogAuditoriaRead`**: contiene todos los campos de la tabla.
- **`LogAuditoriaCreate`**: incluye los campos de inserción esperados; **no incluye** `cliente_id`, `log_id`, `fecha_evento` porque:
  - `cliente_id` se setea por contexto tenant (current_user)
  - `log_id` se genera en server (uuid) si no viene
  - `fecha_evento` tiene default en BD

✅ **No se detectan campos existentes en BD que falten en schemas actuales.**

## Problemas de tenant o RBAC

### Tenant
- ✅ `cliente_id` se valida/inyecta por contexto (`current_user.cliente_id`) y se aplica siempre en queries.
- ✅ `empresa_id` se filtra cuando se envía como parámetro; la tabla lo tiene y se expone como filtro en listado.

### RBAC
- ✅ Los endpoints exigen RBAC vía `Depends(require_permission(...))`.
- ⚠️ Observación: el endpoint **POST** usa el mismo permiso `aud.log.leer`. Si el catálogo RBAC define acciones separadas (p.ej. `aud.log.crear`), esto podría ser una brecha de permisos; **no se cambia** aquí (solo auditoría).

## Código marcado como obsoleto o incorrecto (NO eliminarlo)

- No se detecta código obsoleto evidente en el módulo `aud` para el alcance de `aud_log_auditoria`.

