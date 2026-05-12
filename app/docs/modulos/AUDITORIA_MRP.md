# AUDITORIA — MRP (Planeamiento de Materiales)

Fecha: 2026-05-07

## Tablas detectadas y su tipo

- **`mrp_plan_maestro`**: **Transaccional** (tiene `estado`, `fecha_calculo`, `fecha_aprobacion`)
  - **Tenant**: `cliente_id`, `empresa_id`
- **`mrp_necesidad_bruta`**: **Transaccional** (entrada/demanda del MRP)
  - **Tenant**: `cliente_id` (no tiene `empresa_id` en la tabla)
- **`mrp_explosion_materiales`**: **Derivada/Analítica** (resultado de explosión BOM; columnas calculadas en BD)
  - **Tenant**: `cliente_id` (no tiene `empresa_id` en la tabla)
- **`mrp_orden_sugerida`**: **Derivada/Operacional** (salida del MRP; sugerencias de compra/producción)
  - **Tenant**: `cliente_id` (no tiene `empresa_id` en la tabla)

## Endpoints existentes

**Router base**: se incluye en API v1 con prefijo **`/mrp`** (`app/api/v1/api.py`).

| Ruta (v1) | Método | Entidad | Tiene tenant? | Tiene RBAC? |
|---|---:|---|---:|---:|
| `/mrp/plan-maestro` | GET | `mrp_plan_maestro` | Sí (`current_user.cliente_id`; `empresa_id` opcional) | Sí (`mrp.plan_maestro.leer`) |
| `/mrp/plan-maestro/{plan_maestro_id}` | GET | `mrp_plan_maestro` | Sí | Sí (`mrp.plan_maestro.leer`) |
| `/mrp/plan-maestro` | POST | `mrp_plan_maestro` | Sí | Sí (`mrp.plan_maestro.crear`) |
| `/mrp/plan-maestro/{plan_maestro_id}` | PUT | `mrp_plan_maestro` | Sí | Sí (`mrp.plan_maestro.actualizar`) |
| `/mrp/necesidades-brutas` | GET | `mrp_necesidad_bruta` | Sí | Sí (`mrp.necesidad_bruta.leer`) |
| `/mrp/necesidades-brutas/{necesidad_id}` | GET | `mrp_necesidad_bruta` | Sí | Sí (`mrp.necesidad_bruta.leer`) |
| `/mrp/necesidades-brutas` | POST | `mrp_necesidad_bruta` | Sí | Sí (`mrp.necesidad_bruta.crear`) |
| `/mrp/necesidades-brutas/{necesidad_id}` | PUT | `mrp_necesidad_bruta` | Sí | Sí (`mrp.necesidad_bruta.actualizar`) |
| `/mrp/explosion-materiales` | GET | `mrp_explosion_materiales` | Sí | Sí (`mrp.explosion_materiales.leer`) |
| `/mrp/explosion-materiales/{explosion_id}` | GET | `mrp_explosion_materiales` | Sí | Sí (`mrp.explosion_materiales.leer`) |
| `/mrp/explosion-materiales` | POST | `mrp_explosion_materiales` | Sí | Sí (`mrp.explosion_materiales.crear`) |
| `/mrp/explosion-materiales/{explosion_id}` | PUT | `mrp_explosion_materiales` | Sí | Sí (`mrp.explosion_materiales.actualizar`) |
| `/mrp/ordenes-sugeridas` | GET | `mrp_orden_sugerida` | Sí | Sí (`mrp.orden_sugerida.leer`) |
| `/mrp/ordenes-sugeridas/{orden_sugerida_id}` | GET | `mrp_orden_sugerida` | Sí | Sí (`mrp.orden_sugerida.leer`) |
| `/mrp/ordenes-sugeridas` | POST | `mrp_orden_sugerida` | Sí | Sí (`mrp.orden_sugerida.crear`) |
| `/mrp/ordenes-sugeridas/{orden_sugerida_id}` | PUT | `mrp_orden_sugerida` | Sí | Sí (`mrp.orden_sugerida.actualizar`) |

## Endpoints faltantes (con ruta sugerida y método)

### Para tablas **transaccionales** (deberían tener flujo: borrador → aprobar/procesar/anular)

- **`mrp_plan_maestro`**
  - **Faltan**:
    - `POST /mrp/plan-maestro/{plan_maestro_id}/aprobar` (permiso sugerido: `mrp.plan_maestro.aprobar`)
    - `POST /mrp/plan-maestro/{plan_maestro_id}/calcular` (permiso sugerido: `mrp.plan_maestro.calcular`)
    - `POST /mrp/plan-maestro/{plan_maestro_id}/ejecutar` (permiso sugerido: `mrp.plan_maestro.ejecutar`)
    - `POST /mrp/plan-maestro/{plan_maestro_id}/cerrar` (permiso sugerido: `mrp.plan_maestro.cerrar`)
    - `POST /mrp/plan-maestro/{plan_maestro_id}/anular` (permiso sugerido: `mrp.plan_maestro.anular`)
  - **Nota**: actualmente existe `PUT` sin validación visible de “solo borrador” (la regla se debería garantizar en service).

- **`mrp_necesidad_bruta`**
  - **Faltan** (si se trata como transaccional con estados; en BD no hay `estado`):
    - No hay endpoints de **anulación** lógica (no existe `es_activo` ni `estado` en tabla).
  - **Riesgo funcional**: al no existir `es_activo`/`estado`, no hay mecanismo estándar para “anular” sin borrar.

### Para tablas **derivadas** (solo lectura)

- **`mrp_explosion_materiales`**
  - **Debería ser solo lectura**.
  - **Endpoints existentes de escritura (⚠ potencialmente incorrecto)**:
    - `POST /mrp/explosion-materiales`
    - `PUT /mrp/explosion-materiales/{explosion_id}`

- **`mrp_orden_sugerida`**
  - **Debería ser principalmente lectura** (y cambios controlados por flujo: aprobar/rechazar/convertir).
  - **Endpoints existentes de escritura (⚠ potencialmente incorrecto)**:
    - `POST /mrp/ordenes-sugeridas`
    - `PUT /mrp/ordenes-sugeridas/{orden_sugerida_id}`
  - **Faltan** (si se maneja por workflow):
    - `POST /mrp/ordenes-sugeridas/{orden_sugerida_id}/aprobar` (permiso sugerido: `mrp.orden_sugerida.aprobar`)
    - `POST /mrp/ordenes-sugeridas/{orden_sugerida_id}/rechazar` (permiso sugerido: `mrp.orden_sugerida.rechazar`)
    - `POST /mrp/ordenes-sugeridas/{orden_sugerida_id}/convertir` (permiso sugerido: `mrp.orden_sugerida.convertir`)

## Campos faltantes en schemas (BD vs Schemas)

Revisión contra `docs/bd/MRP_TABLAS.sql`:

- **`mrp_plan_maestro`**: sin brechas evidentes en `PlanMaestroRead`. `Create/Update` omiten campos auditables (`cliente_id`, `fecha_creacion`) como corresponde.
- **`mrp_necesidad_bruta`**: sin brechas evidentes en `NecesidadBrutaRead`.
- **`mrp_explosion_materiales`**:
  - BD define `stock_disponible` y `cantidad_a_ordenar` como columnas calculadas; el schema `ExplosionMaterialesRead` las expone como opcionales y el service las calcula: **OK**.
- **`mrp_orden_sugerida`**: sin brechas evidentes en `OrdenSugeridaRead` (incluye `documento_generado_*` y `fecha_conversion`).

## Problemas de tenant o RBAC

- **Tenant**:
  - En endpoints y queries se filtra por **`cliente_id`** consistentemente: **OK**.
  - `empresa_id` se filtra donde existe en tabla (`mrp_plan_maestro`): **OK**.
- **RBAC**:
  - Todos los endpoints revisados exigen permiso con patrón `mrp.<recurso>.<accion>`: **OK**.
  - Acciones específicas de workflow (aprobar/calcular/convertir/etc.) aún no existen (ver “Endpoints faltantes”).

## Código marcado como obsoleto o incorrecto (NO eliminarlo)

- **⚠ Escritura en tablas derivadas**:
  - `mrp_explosion_materiales`: existe `POST/PUT` (debería ser derivada/resultado).
  - `mrp_orden_sugerida`: existe `POST/PUT` (debería controlarse por workflow, no CRUD libre).

