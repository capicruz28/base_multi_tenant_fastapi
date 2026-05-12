# AUDITORÍA — Módulo BI (Business Intelligence)

Fuente BD: `docs/bd/BI_TABLAS.sql`  
Fecha: 2026-05-08

## Tablas detectadas y su tipo

### `bi_reporte` (MAESTRO)

- **Descripción**: Reportes personalizados / configuración BI.
- **Multi-tenant**: tiene `cliente_id` y `empresa_id`.
- **Soft delete**: tiene `es_activo`.
- **Campos (BD)**:
  - `reporte_id` (UNIQUEIDENTIFIER, PK)
  - `cliente_id` (UNIQUEIDENTIFIER, NOT NULL)
  - `empresa_id` (UNIQUEIDENTIFIER, NOT NULL) → FK `org_empresa(empresa_id)`
  - `codigo_reporte` (NVARCHAR(20), NOT NULL) — UQ (`cliente_id`,`empresa_id`,`codigo_reporte`)
  - `nombre` (NVARCHAR(150), NOT NULL)
  - `descripcion` (NVARCHAR(500), NULL)
  - `modulo_origen` (NVARCHAR(10), NULL)
  - `categoria` (NVARCHAR(50), NULL)
  - `tipo_reporte` (NVARCHAR(20), DEFAULT 'sql')
  - `query_sql` (NVARCHAR(MAX), NULL)
  - `configuracion_json` (NVARCHAR(MAX), NULL)
  - `es_publico` (BIT, DEFAULT 0)
  - `creado_por_usuario_id` (UNIQUEIDENTIFIER, NULL)
  - `es_activo` (BIT, DEFAULT 1, NOT NULL)
  - `fecha_creacion` (DATETIME, DEFAULT GETDATE(), NOT NULL)

## Endpoints existentes

Entidad: `reporte` (tabla `bi_reporte`)  
Router: `app/modules/bi/presentation/endpoints.py` + `endpoints_reporte.py`

| Ruta | Método | Entidad | Tiene tenant? | Tiene RBAC? |
|---|---|---|---|---|
| `/bi/reportes` | GET | Reporte | Sí (usa `current_user.cliente_id`; `empresa_id` es filtro opcional) | Sí (`bi.reporte.leer`) |
| `/bi/reportes/{reporte_id}` | GET | Reporte | Parcial (solo filtra por `cliente_id`, no valida `empresa_id`) | Sí (`bi.reporte.leer`) |
| `/bi/reportes` | POST | Reporte | Parcial (fuerza `cliente_id`; `empresa_id` viene en body) | Sí (`bi.reporte.crear`) |
| `/bi/reportes/{reporte_id}` | PUT | Reporte | Parcial (solo filtra por `cliente_id`, no valida `empresa_id`) | Sí, pero permiso parece incorrecto (`bi.reporte.crear`) |

## Endpoints faltantes (con ruta sugerida y método)

Tabla `bi_reporte` es **MAESTRO**, por estándar debe tener: crear, listar, detalle, actualizar, activar/desactivar.

- **Faltante (activación/desactivación dedicada)**:
  - `PATCH /bi/reportes/{reporte_id}/activar`
  - `PATCH /bi/reportes/{reporte_id}/desactivar`
  - Alternativa aceptable: mantener solo `PUT` pero exigir RBAC `bi.reporte.actualizar` y exponer operación explícita para `es_activo` (según convención del proyecto).

## Campos faltantes en schemas

Comparación BD vs `app/modules/bi/presentation/schemas.py`:

- **`ReporteCreate`**: cubre campos de inserción; `cliente_id` se deriva del usuario (correcto). Incluye `empresa_id`.
- **`ReporteUpdate`**: cubre campos actualizables.
- **`ReporteRead`**: incluye todos los campos relevantes de BD, incluyendo `fecha_creacion`.

**Resultado**: no se detectan campos faltantes evidentes en schemas para `bi_reporte` respecto al SQL provisto.

## Problemas de tenant o RBAC

- **Tenant (`empresa_id`) no validado en detalle/actualización**:
  - `get_reporte_by_id` y `update_reporte` filtran solo por (`cliente_id`, `reporte_id`).
  - Regla del proyecto: “validar `empresa_id` cuando la tabla lo tenga”. Aquí queda **parcial**.
- **RBAC en actualización**:
  - `PUT /bi/reportes/{reporte_id}` usa `require_permission("bi.reporte.crear")` (probable inconsistencia; debería ser algo como `bi.reporte.actualizar`).

## Código marcado como obsoleto o incorrecto (NO eliminarlo)

- No se marca código obsoleto. Solo se registran las brechas anteriores (RBAC y validación de `empresa_id`).

