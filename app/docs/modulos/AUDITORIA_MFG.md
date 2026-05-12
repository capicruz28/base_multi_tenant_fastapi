# AUDITORIA — MFG (Manufactura y Producción)

Fecha: 2026-05-07  
Alcance: backend FastAPI (routers/services/queries/schemas).  
Reglas: **no** se modifican contratos existentes; multi-tenant por `cliente_id` (y `empresa_id` cuando aplique); RBAC patrón `mfg.<recurso>.<accion>`.

## Tablas detectadas (BD)

Fuente: `docs/bd/MFG_TABLAS.sql` (prefijo `mfg_`).

- **`mfg_centro_trabajo`**: maestro (tiene `es_activo`)
- **`mfg_operacion`**: maestro (tiene `es_activo`)
- **`mfg_lista_materiales`**: transaccional cabecera (BOM) (usa `es_bom_activa` + `estado`)
- **`mfg_lista_materiales_detalle`**: transaccional detalle (BOM)
- **`mfg_ruta_fabricacion`**: transaccional cabecera (usa `es_ruta_activa` + `estado`)
- **`mfg_ruta_fabricacion_detalle`**: transaccional detalle
- **`mfg_orden_produccion`**: transaccional cabecera OP (estado: `borrador/liberada/en_proceso/.../anulada`)
- **`mfg_orden_produccion_operacion`**: transaccional seguimiento de operaciones de OP
- **`mfg_consumo_materiales`**: transaccional registro de consumo

## Implementación actual (routers/services/queries/schemas)

### Archivos del módulo

- **Routers**: `app/modules/mfg/presentation/endpoints*.py` + agregador `app/modules/mfg/presentation/endpoints.py`
- **Services**: `app/modules/mfg/application/services/*_service.py`
- **Queries**: `app/infrastructure/database/queries/mfg/*_queries.py`
- **Schemas**: `app/modules/mfg/presentation/schemas.py`

### Endpoints existentes (Paso 2.1)

Nota: las rutas base dependen de dónde se incluya `app/modules/mfg/presentation/endpoints.py` en el router principal de la API. Aquí se listan los **paths relativos** al prefix del módulo.

| Ruta (relativa) | Método | Entidad | ¿Tenant? | ¿RBAC? |
|---|---:|---|---|---|
| `/centros-trabajo` | GET | CentroTrabajo | Sí (`current_user.cliente_id`) | Sí `mfg.centro_trabajo.leer` |
| `/centros-trabajo/{centro_trabajo_id}` | GET | CentroTrabajo | Sí | Sí `mfg.centro_trabajo.leer` |
| `/centros-trabajo` | POST | CentroTrabajo | Sí | Sí `mfg.centro_trabajo.crear` |
| `/centros-trabajo/{centro_trabajo_id}` | PUT | CentroTrabajo | Sí | Sí `mfg.centro_trabajo.actualizar` |
| `/operaciones` | GET | Operacion | Sí | Sí `mfg.operacion.leer` |
| `/operaciones/{operacion_id}` | GET | Operacion | Sí | Sí `mfg.operacion.leer` |
| `/operaciones` | POST | Operacion | Sí | Sí `mfg.operacion.crear` |
| `/operaciones/{operacion_id}` | PUT | Operacion | Sí | Sí `mfg.operacion.actualizar` |
| `/listas-materiales` | GET | ListaMateriales (BOM) | Sí | Sí `mfg.lista_materiales.leer` |
| `/listas-materiales/{bom_id}` | GET | ListaMateriales (BOM) | Sí | Sí `mfg.lista_materiales.leer` |
| `/listas-materiales` | POST | ListaMateriales (BOM) | Sí | Sí `mfg.lista_materiales.crear` |
| `/listas-materiales/{bom_id}` | PUT | ListaMateriales (BOM) | Sí | Sí `mfg.lista_materiales.actualizar` |
| `/lista-materiales-detalle` | GET | ListaMaterialesDetalle | Sí | Sí `mfg.lista_materiales_detalle.leer` |
| `/lista-materiales-detalle/{bom_detalle_id}` | GET | ListaMaterialesDetalle | Sí | Sí `mfg.lista_materiales_detalle.leer` |
| `/lista-materiales-detalle` | POST | ListaMaterialesDetalle | Sí | Sí `mfg.lista_materiales_detalle.crear` |
| `/lista-materiales-detalle/{bom_detalle_id}` | PUT | ListaMaterialesDetalle | Sí | Sí `mfg.lista_materiales_detalle.actualizar` |
| `/rutas-fabricacion` | GET | RutaFabricacion | Sí | Sí `mfg.ruta_fabricacion.leer` |
| `/rutas-fabricacion/{ruta_id}` | GET | RutaFabricacion | Sí | Sí `mfg.ruta_fabricacion.leer` |
| `/rutas-fabricacion` | POST | RutaFabricacion | Sí | Sí `mfg.ruta_fabricacion.crear` |
| `/rutas-fabricacion/{ruta_id}` | PUT | RutaFabricacion | Sí | Sí `mfg.ruta_fabricacion.actualizar` |
| `/ruta-fabricacion-detalle` | GET | RutaFabricacionDetalle | Sí | Sí `mfg.ruta_fabricacion_detalle.leer` |
| `/ruta-fabricacion-detalle/{ruta_detalle_id}` | GET | RutaFabricacionDetalle | Sí | Sí `mfg.ruta_fabricacion_detalle.leer` |
| `/ruta-fabricacion-detalle` | POST | RutaFabricacionDetalle | Sí | Sí `mfg.ruta_fabricacion_detalle.crear` |
| `/ruta-fabricacion-detalle/{ruta_detalle_id}` | PUT | RutaFabricacionDetalle | Sí | Sí `mfg.ruta_fabricacion_detalle.actualizar` |
| `/ordenes-produccion` | GET | OrdenProduccion | Sí | Sí `mfg.orden_produccion.leer` |
| `/ordenes-produccion/{orden_produccion_id}` | GET | OrdenProduccion | Sí | Sí `mfg.orden_produccion.leer` |
| `/ordenes-produccion` | POST | OrdenProduccion | Sí | Sí `mfg.orden_produccion.crear` |
| `/ordenes-produccion/{orden_produccion_id}` | PUT | OrdenProduccion | Sí | Sí `mfg.orden_produccion.actualizar` |
| `/orden-produccion-operaciones` | GET | OrdenProduccionOperacion | Sí | Sí `mfg.orden_produccion_operacion.leer` |
| `/orden-produccion-operaciones/{op_operacion_id}` | GET | OrdenProduccionOperacion | Sí | Sí `mfg.orden_produccion_operacion.leer` |
| `/orden-produccion-operaciones` | POST | OrdenProduccionOperacion | Sí | Sí `mfg.orden_produccion_operacion.crear` |
| `/orden-produccion-operaciones/{op_operacion_id}` | PUT | OrdenProduccionOperacion | Sí | Sí `mfg.orden_produccion_operacion.actualizar` |
| `/consumo-materiales` | GET | ConsumoMateriales | Sí | Sí `mfg.consumo_material.leer` |
| `/consumo-materiales/{consumo_id}` | GET | ConsumoMateriales | Sí | Sí `mfg.consumo_material.leer` |
| `/consumo-materiales` | POST | ConsumoMateriales | Sí | Sí `mfg.consumo_material.crear` |
| `/consumo-materiales/{consumo_id}` | PUT | ConsumoMateriales | Sí | Sí `mfg.consumo_material.actualizar` |

## Brechas funcionales (Paso 2.2)

### Maestros

- **`mfg_centro_trabajo`**
  - Existe: **crear/listar/detalle/actualizar**
  - Falta (patrón maestro esperado): **activar/desactivar** (baja lógica) como endpoints explícitos (ej. `DELETE` o `/reactivar`)
- **`mfg_operacion`**
  - Existe: **crear/listar/detalle/actualizar**
  - Falta: **activar/desactivar**

### Transaccionales

En el repo, las entidades transaccionales de MFG hoy tienen CRUD básico (GET/POST/PUT) pero **no** exponen flujo de estados.

- **`mfg_lista_materiales` / `mfg_ruta_fabricacion` / `mfg_orden_produccion`**
  - Existe: **crear/listar/detalle/actualizar**
  - Falta (patrón transaccional esperado por prompt maestro): endpoints de **aprobar/procesar/anular** (y/o “liberar”, “iniciar”, “cerrar” según el estado real de la tabla).  
  - Falta: reglas de negocio visibles en API (ej. “solo actualizar cuando estado=borrador”) — no se observan endpoints específicos para transición de estado.

- **Detalles/seguimiento**
  - `mfg_lista_materiales_detalle`, `mfg_ruta_fabricacion_detalle`, `mfg_orden_produccion_operacion`, `mfg_consumo_materiales`
  - Existe: **crear/listar/detalle/actualizar**
  - Falta: operaciones de control transaccional (p.ej. manejo embebido cabecera+detalle o endpoints para batch/replace del detalle).

## Campos faltantes en schemas (Paso 2.3)

Comparación contra `docs/bd/MFG_TABLAS.sql` (solo campos claramente divergentes).

### Inconsistencias críticas de tipos / nombres

- **`mfg_orden_produccion.moneda_id (UUID)`**  
  - En BD: `moneda_id UNIQUEIDENTIFIER NOT NULL` (FK `cat_moneda`)  
  - En schemas: `OrdenProduccionCreate/Read` usan `moneda: str` (p.ej. `"PEN"`)  
  - Impacto: el schema **no representa** el campo real de BD.

### Campos omitidos en schemas `Read` (pero existen en BD)

En BD, **todas** las tablas MFG incluyen `empresa_id`. En varios `Read` no está presente:

- `ListaMaterialesDetalleRead`: falta `empresa_id`
- `RutaFabricacionDetalleRead`: falta `empresa_id`
- `OrdenProduccionOperacionRead`: falta `empresa_id`
- `ConsumoMaterialesRead`: falta `empresa_id`

### Campos de BD no modelados (cálculo/derivados)

- `mfg_orden_produccion.cantidad_pendiente` (computed, `PERSISTED`)
- `mfg_orden_produccion.costo_total` (computed, `PERSISTED`)
- `mfg_consumo_materiales.diferencia` (computed, `PERSISTED`)
- `mfg_consumo_materiales.costo_total` (computed, `PERSISTED`)

Nota: se puede decidir si deben exponerse en `Read` (lectura) aunque no sean parte de `Create/Update`.

## Problemas de tenant o RBAC (Paso 2.4)

- **Tenant (`cliente_id`)**: ✅ en endpoints se deriva de `current_user.cliente_id` y se pasa a services/queries; en queries se observa filtro por `cliente_id`.
- **`empresa_id`**: ⚠ la BD tiene `empresa_id` en todas las tablas; varios schemas `Read` no lo exponen (ver brecha). En queries puede derivarse (ej. detalle de BOM deriva `empresa_id` desde cabecera), pero a nivel de contrato de response hoy puede haber desalineación.
- **RBAC**: ✅ todos los endpoints MFG encontrados requieren `require_permission("mfg.<recurso>.<accion>")`.

## Recomendación de implementación (para Fase 3, no ejecutar aún)

- Completar endpoints faltantes según patrón:
  - Maestros: activar/desactivar.
  - Transaccionales: transiciones de estado (aprobar/liberar/procesar/anular) alineadas a valores de `estado` en BD.
- Corregir schemas para reflejar BD (sin romper contratos existentes: versionar cuidadosamente si ya hay clientes).

