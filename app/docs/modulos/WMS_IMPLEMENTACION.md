# WMS — Implementación cerrada (Warehouse Management System)

**Código de módulo:** WMS  
**Alcance:** Fases 1–4 según `docs/prompts/PROMPT_MODULO_MAESTRO.md` y `docs/bd/WMS_TABLAS.sql` (tablas `wms_*`).  
**Fecha de cierre:** documento de verificación final del módulo.

---

## 1. Archivos tocados en la implementación

| Archivo | Rol |
|---------|-----|
| `app/modules/wms/presentation/schemas.py` | `empresa_id` en Create/Update/Read + request para acción `asignar` |
| `app/infrastructure/database/queries/wms/zona_almacen_queries.py` | Filtro estricto `cliente_id + empresa_id` + validación de pertenencia de empresa en insert/update |
| `app/infrastructure/database/queries/wms/ubicacion_queries.py` | Idem |
| `app/infrastructure/database/queries/wms/stock_ubicacion_queries.py` | Idem + `fecha_actualizacion` |
| `app/infrastructure/database/queries/wms/tarea_queries.py` | Idem |
| `app/modules/wms/application/services/zona_almacen_service.py` | Propagación `empresa_id` a queries (list/get/update) |
| `app/modules/wms/application/services/ubicacion_service.py` | Idem |
| `app/modules/wms/application/services/stock_ubicacion_service.py` | Idem |
| `app/modules/wms/application/services/tarea_service.py` | Validación de edición por estado + workflow (asignar/iniciar/completar/cancelar) |
| `app/modules/wms/application/services/__init__.py` | Exporta funciones de workflow de tareas |
| `app/modules/wms/presentation/endpoints_zonas.py` | `empresa_id` requerido en list/detalle; activar/desactivar |
| `app/modules/wms/presentation/endpoints_ubicaciones.py` | `empresa_id` requerido en list/detalle; activar/desactivar |
| `app/modules/wms/presentation/endpoints_stock.py` | `empresa_id` requerido en list/detalle; POST/PUT marcados `deprecated=True` (uso interno) |
| `app/modules/wms/presentation/endpoints_tareas.py` | `empresa_id` requerido; RBAC faltante corregido; endpoints de workflow |
| `app/docs/modulos/AUDITORIA_WMS.md` | Auditoría Fase 2 actualizada con decisión “stock derivado” |
| `app/docs/database/SEED_PERMISOS_RBAC_WMS.sql` | Seed idempotente de permisos `wms.*.*` |

---

## 2. Endpoints nuevos — checklist de seguridad

Prefijo API: `/wms` (más el prefijo global de la API v1, p. ej. `/api/v1` según despliegue).

| Ruta (relativa a `/wms`) | Método | `cliente_id` (tenant) | `empresa_id` | RBAC |
|--------------------------|--------|------------------------|--------------|------|
| `/zonas/{id}/activar` | POST | Sí (`current_user.cliente_id`) | Query **requerido** | `wms.zona.actualizar` |
| `/zonas/{id}/desactivar` | POST | Sí | Query **requerido** | `wms.zona.actualizar` |
| `/ubicaciones/{id}/activar` | POST | Sí | Query **requerido** | `wms.ubicacion.actualizar` |
| `/ubicaciones/{id}/desactivar` | POST | Sí | Query **requerido** | `wms.ubicacion.actualizar` |
| `/tareas/{id}/asignar` | POST | Sí | Query **requerido** | `wms.tarea.actualizar` |
| `/tareas/{id}/iniciar` | POST | Sí | Query **requerido** | `wms.tarea.actualizar` |
| `/tareas/{id}/completar` | POST | Sí | Query **requerido** | `wms.tarea.actualizar` |
| `/tareas/{id}/cancelar` | POST | Sí | Query **requerido** | `wms.tarea.actualizar` |

**Corrección de seguridad aplicada:**

- `GET /wms/tareas/{tarea_id}` ahora exige `require_permission("wms.tarea.leer")`.

---

## 3. Compatibilidad con endpoints existentes

| Verificación | Estado |
|--------------|--------|
| No se eliminaron rutas ni se cambiaron métodos HTTP existentes | OK |
| Se mantuvieron `POST/PUT` de `stock-ubicacion` | OK |
| `POST/PUT` de `stock-ubicacion` marcados como internos | `deprecated=True` (backward compatible) |

**Cambio de comportamiento intencional (multi-empresa):**

- Para recursos WMS (todas las tablas tienen `empresa_id` NOT NULL), ahora las operaciones **requieren scope** de empresa y las queries filtran por `cliente_id + empresa_id`.
- La pertenencia de `empresa_id` al tenant se valida contra `org_empresa` (activa) antes de crear/actualizar.

---

## 4. Reglas de negocio implementadas (tareas)

- **Edición por PUT**: `PUT /tareas/{id}` solo permite cambios si la tarea está en estado **`pendiente`** o **`borrador`**.
- **Workflow explícito**:
  - `pendiente/borrador → asignada` (`/asignar`)
  - `asignada → en_proceso` (`/iniciar`)
  - `en_proceso → completada` (`/completar`)
  - `pendiente/borrador/asignada/en_proceso → cancelada` (`/cancelar`)
- Se bloquea cambio directo de `estado` y timestamps de workflow vía `PUT` (usar endpoints de workflow).

---

## 5. Seeds RBAC (permisos de negocio)

Archivo agregado: `app/docs/database/SEED_PERMISOS_RBAC_WMS.sql`

Permisos cubiertos:

- `wms.zona.{leer,crear,actualizar}`
- `wms.ubicacion.{leer,crear,actualizar}`
- `wms.stock_ubicacion.{leer,crear,actualizar}`
- `wms.tarea.{leer,crear,actualizar}`

---

## 6. Referencias

- Auditoría: `app/docs/modulos/AUDITORIA_WMS.md`
- Modelo de datos: `docs/bd/WMS_TABLAS.sql`
- Prompt maestro: `docs/prompts/PROMPT_MODULO_MAESTRO.md`

---

**Estado del módulo WMS (esta entrega):** implementación cerrada según el alcance acordado (bloques Fase 3 + seeds).  
