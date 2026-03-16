## RBAC Wave 1 — Endpoints solo autenticados (MFG + WMS)

### Endpoints modificados

- **MFG — Orden producción operaciones** (`endpoints_orden_produccion_operaciones.py`, prefijo `/mfg/orden-produccion-operaciones`)
  - GET `` → permiso `mfg.orden_produccion_operacion.leer`
  - GET `/{op_operacion_id}` → permiso `mfg.orden_produccion_operacion.leer`
  - POST `` → permiso `mfg.orden_produccion_operacion.crear`
  - PUT `/{op_operacion_id}` → permiso `mfg.orden_produccion_operacion.actualizar`

- **MFG — Consumo materiales** (`endpoints_consumo_materiales.py`, prefijo `/mfg/consumo-materiales`)
  - GET `` → permiso `mfg.consumo_material.leer`
  - GET `/{consumo_id}` → permiso `mfg.consumo_material.leer`
  - POST `` → permiso `mfg.consumo_material.crear`
  - PUT `/{consumo_id}` → permiso `mfg.consumo_material.actualizar`

- **MFG — Ruta fabricación detalle** (`endpoints_ruta_fabricacion_detalle.py`, prefijo `/mfg/ruta-fabricacion-detalle`)
  - GET `` → permiso `mfg.ruta_fabricacion_detalle.leer`
  - GET `/{ruta_detalle_id}` → permiso `mfg.ruta_fabricacion_detalle.leer`
  - POST `` → permiso `mfg.ruta_fabricacion_detalle.crear`
  - PUT `/{ruta_detalle_id}` → permiso `mfg.ruta_fabricacion_detalle.actualizar`

- **MFG — Rutas fabricación** (`endpoints_rutas_fabricacion.py`, prefijo `/mfg/rutas-fabricacion`)
  - GET `` → permiso `mfg.ruta_fabricacion.leer`
  - GET `/{ruta_id}` → permiso `mfg.ruta_fabricacion.leer`
  - POST `` → permiso `mfg.ruta_fabricacion.crear`
  - PUT `/{ruta_id}` → permiso `mfg.ruta_fabricacion.actualizar`

- **MFG — Lista materiales detalle** (`endpoints_lista_materiales_detalle.py`, prefijo `/mfg/lista-materiales-detalle`)
  - GET `` → permiso `mfg.lista_materiales_detalle.leer`
  - GET `/{bom_detalle_id}` → permiso `mfg.lista_materiales_detalle.leer`
  - POST `` → permiso `mfg.lista_materiales_detalle.crear`
  - PUT `/{bom_detalle_id}` → permiso `mfg.lista_materiales_detalle.actualizar`

- **MFG — Listas materiales (BOM)** (`endpoints_listas_materiales.py`, prefijo `/mfg/listas-materiales`)
  - GET `` → permiso `mfg.lista_materiales.leer`
  - GET `/{bom_id}` → permiso `mfg.lista_materiales.leer`
  - POST `` → permiso `mfg.lista_materiales.crear`
  - PUT `/{bom_id}` → permiso `mfg.lista_materiales.actualizar`

- **MFG — Operaciones** (`endpoints_operaciones.py`, prefijo `/mfg/operaciones`)
  - GET `` → permiso `mfg.operacion.leer`
  - GET `/{operacion_id}` → permiso `mfg.operacion.leer`
  - POST `` → permiso `mfg.operacion.crear`
  - PUT `/{operacion_id}` → permiso `mfg.operacion.actualizar`

- **MFG — Centros de trabajo** (`endpoints_centros_trabajo.py`, prefijo `/mfg/centros-trabajo`)
  - GET `` → permiso `mfg.centro_trabajo.leer`
  - GET `/{centro_trabajo_id}` → permiso `mfg.centro_trabajo.leer`
  - POST `` → permiso `mfg.centro_trabajo.crear`
  - PUT `/{centro_trabajo_id}` → permiso `mfg.centro_trabajo.actualizar`

- **WMS — Zonas almacén** (`endpoints_zonas.py`, prefijo `/wms/zonas`)
  - POST `` → permiso `wms.zona.crear`

- **WMS — Ubicaciones** (`endpoints_ubicaciones.py`, prefijo `/wms/ubicaciones`)
  - POST `` → permiso `wms.ubicacion.crear`

### Permisos agregados (para autoregistro RBAC)

- `mfg.orden_produccion_operacion.leer`
- `mfg.orden_produccion_operacion.crear`
- `mfg.orden_produccion_operacion.actualizar`
- `mfg.consumo_material.leer`
- `mfg.consumo_material.crear`
- `mfg.consumo_material.actualizar`
- `mfg.ruta_fabricacion_detalle.leer`
- `mfg.ruta_fabricacion_detalle.crear`
- `mfg.ruta_fabricacion_detalle.actualizar`
- `mfg.ruta_fabricacion.leer`
- `mfg.ruta_fabricacion.crear`
- `mfg.ruta_fabricacion.actualizar`
- `mfg.lista_materiales_detalle.leer`
- `mfg.lista_materiales_detalle.crear`
- `mfg.lista_materiales_detalle.actualizar`
- `mfg.lista_materiales.leer`
- `mfg.lista_materiales.crear`
- `mfg.lista_materiales.actualizar`
- `mfg.operacion.leer`
- `mfg.operacion.crear`
- `mfg.operacion.actualizar`
- `mfg.centro_trabajo.leer`
- `mfg.centro_trabajo.crear`
- `mfg.centro_trabajo.actualizar`
- `wms.zona.crear`
- `wms.ubicacion.crear`

> Nota: si alguno de estos permisos aún no existe en la tabla `permiso`, la nueva decoración con `require_permission` permitirá que el mecanismo de autoregistro RBAC los detecte y registre.

### Riesgos detectados

- **Cambio de comportamiento esperado:** todos los endpoints anteriores pasan de estar protegidos solo por autenticación a requerir permiso RBAC explícito.
  - Riesgo **ALTO** si los roles actuales de negocio aún no tienen asignados estos permisos, ya que podrían perder acceso hasta que se ajusten las asignaciones.
- **Mitigación recomendada:**
  - Mapear los roles existentes a estos nuevos permisos siguiendo el reporte `rbac_permission_coverage_report.md`.
  - Validar en un entorno de staging que los roles clave (operaciones, planificación, almacén, etc.) tienen los permisos adecuados antes de desplegar a producción.

