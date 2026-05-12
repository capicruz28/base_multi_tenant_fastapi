# QMS — Implementación cerrada (Gestión de Calidad)

**Código de módulo:** QMS  
**Alcance:** Fases 1–4 según `docs/prompts/PROMPT_MODULO_MAESTRO.md` y `docs/bd/QMS_TABLAS.sql` (tablas `qms_*`).  
**Fecha de cierre:** 2026-05-07

---

## 1. Archivos tocados en la implementación

| Archivo | Rol |
|---------|-----|
| `app/modules/qms/presentation/schemas.py` | `empresa_id` agregado en Create/Read de tablas detalle (`*_detalle`) sin tomarlo del body |
| `app/infrastructure/database/queries/qms/plan_inspeccion_queries.py` | Insert y filtros de `qms_plan_inspeccion_detalle` con `empresa_id` (derivado desde cabecera) + endurecimiento de update (no permitir cambiar `empresa_id`) |
| `app/infrastructure/database/queries/qms/inspeccion_queries.py` | Insert y filtros de `qms_inspeccion_detalle` con `empresa_id` (derivado desde cabecera) + endurecimiento de update (no permitir cambiar `empresa_id`) |
| `app/modules/qms/application/services/plan_inspeccion_service.py` | Propaga `empresa_id` desde cabecera a detalle + bloquea edición de detalle si el plan está inactivo |
| `app/modules/qms/application/services/inspeccion_service.py` | Validación de edición por estado + transiciones (`aprobar/procesar/anular`) + bloqueo de edición de detalle cuando cabecera no es editable |
| `app/modules/qms/application/services/no_conformidad_service.py` | Transiciones (`cerrar/cancelar`) + bloqueo de cierre/cancelación vía `PUT` genérico |
| `app/modules/qms/application/services/__init__.py` | Exporta funciones nuevas de transiciones para uso en routers |
| `app/modules/qms/presentation/endpoints_inspecciones.py` | Nuevos endpoints `POST` de transiciones de inspección (sin modificar rutas existentes) |
| `app/modules/qms/presentation/endpoints_no_conformidades.py` | Nuevos endpoints `POST` de cierre/cancelación (sin modificar rutas existentes) |
| `app/modules/qms/presentation/endpoints_parametros.py` | Nuevos endpoints `POST` activar/desactivar (borrado lógico) |
| `app/modules/qms/presentation/endpoints_planes.py` | Nuevos endpoints `POST` activar/desactivar (borrado lógico) |
| `app/docs/modulos/AUDITORIA_QMS.md` | Reporte de brechas y campos faltantes (Fase 2) |
| `app/docs/database/SEED_PERMISOS_RBAC_QMS.sql` | Seed idempotente (MERGE) de permisos `qms.*.*` incluyendo acciones nuevas |

---

## 2. Endpoints nuevos — checklist de seguridad

Prefijo API: `/qms` (más el prefijo global de la API, p. ej. `/api/v1` según despliegue).

| Ruta (relativa a `/qms`) | Método | `cliente_id` (tenant) | `empresa_id` | RBAC |
|--------------------------|--------|------------------------|--------------|------|
| `/inspecciones/{id}/aprobar` | POST | Sí (`current_user.cliente_id`) | Por cabecera `qms_inspeccion` | `qms.inspeccion.aprobar` |
| `/inspecciones/{id}/procesar` | POST | Sí | Por cabecera `qms_inspeccion` | `qms.inspeccion.procesar` |
| `/inspecciones/{id}/anular` | POST | Sí | Por cabecera `qms_inspeccion` | `qms.inspeccion.anular` |
| `/no-conformidades/{id}/cerrar` | POST | Sí | N/A (se persiste en tabla) | `qms.no_conformidad.cerrar` |
| `/no-conformidades/{id}/cancelar` | POST | Sí | N/A (se persiste en tabla) | `qms.no_conformidad.cancelar` |
| `/parametros-calidad/{id}/activar` | POST | Sí | N/A | `qms.parametro_calidad.activar` |
| `/parametros-calidad/{id}/desactivar` | POST | Sí | N/A | `qms.parametro_calidad.desactivar` |
| `/planes-inspeccion/{id}/activar` | POST | Sí | N/A | `qms.plan_inspeccion.activar` |
| `/planes-inspeccion/{id}/desactivar` | POST | Sí | N/A | `qms.plan_inspeccion.desactivar` |

---

## 3. Compatibilidad con endpoints existentes

| Verificación | Estado |
|--------------|--------|
| No se eliminaron rutas ni se cambiaron métodos HTTP existentes | OK |
| No se cambió contrato de request/response de endpoints existentes | OK |

**Cambios de comportamiento intencionales (seguridad/estado):**

- `PUT /qms/inspecciones/{id}` ahora **solo** permite editar si `resultado == "pendiente"`.
- Se bloquea modificar por `PUT` genérico campos de transición en inspección:
  - `resultado`
  - `aprobado_por_usuario_id`
  - `fecha_aprobacion`
- Se bloquea editar/crear detalles de inspección (`/inspecciones/.../detalles`) si la cabecera ya no es editable.
- `PUT /qms/no-conformidades/{id}` ya **no permite** `cerrar/cancelar` (se fuerza a usar endpoints de transición).

---

## 4. Multi-tenant y multi-empresa (empresa_id desde contexto)

### 4.1 Regla aplicada

- Para tablas detalle `qms_plan_inspeccion_detalle` y `qms_inspeccion_detalle` (ambas con `empresa_id NOT NULL`):
  - `empresa_id` **no se toma del body**.
  - Se **deriva desde la cabecera**:
    - Detalle de plan: desde `qms_plan_inspeccion.empresa_id`
    - Detalle de inspección: desde `qms_inspeccion.empresa_id`

### 4.2 Endurecimiento de queries

- En queries de detalle se añadió filtro opcional por `empresa_id` (cuando se conoce por cabecera), para reforzar aislamiento dentro del tenant.
- En updates de detalle se evita aceptar cambios de `empresa_id`.

---

## 5. Reglas de negocio implementadas (transiciones)

### 5.1 Inspección (`qms_inspeccion`)

- **Editable por PUT**: solo en `resultado = "pendiente"`.
- **Workflow explícito**:
  - `pendiente → aprobado` (`POST /inspecciones/{id}/aprobar`)
    - Setea `aprobado_por_usuario_id = current_user.usuario_id`
    - Setea `fecha_aprobacion` automáticamente (si no se envía)
  - `aprobado → procesado` (`POST /inspecciones/{id}/procesar`)
  - `pendiente/aprobado → anulado` (`POST /inspecciones/{id}/anular`)
  - Se bloquea anulación si ya está `procesado` o `anulado`.

### 5.2 No conformidad (`qms_no_conformidad`)

- **Cierre** (`POST /no-conformidades/{id}/cerrar`):
  - Setea `estado = "cerrada"`
  - Setea `cerrado_por_usuario_id = current_user.usuario_id`
  - Setea `fecha_cierre` automáticamente (si no se envía)
- **Cancelación** (`POST /no-conformidades/{id}/cancelar`):
  - Setea `estado = "cancelada"`
  - Setea `cerrado_por_usuario_id = current_user.usuario_id`
  - Setea `fecha_cierre` automáticamente (si no se envía)
- Se impide cerrar/cancelar por `PUT` genérico (usar transiciones).

---

## 6. Seeds RBAC (permisos de negocio)

Archivo agregado: `app/docs/database/SEED_PERMISOS_RBAC_QMS.sql`

Permisos cubiertos:

- `qms.parametro_calidad.{leer,crear,actualizar,activar,desactivar}`
- `qms.plan_inspeccion.{leer,crear,actualizar,activar,desactivar}`
- `qms.inspeccion.{leer,crear,actualizar,aprobar,procesar,anular}`
- `qms.no_conformidad.{leer,crear,actualizar,cerrar,cancelar}`

---

## 7. Referencias

- Auditoría: `app/docs/modulos/AUDITORIA_QMS.md`
- Modelo de datos: `docs/bd/QMS_TABLAS.sql`
- Prompt maestro: `docs/prompts/PROMPT_MODULO_MAESTRO.md`

---

**Estado del módulo QMS (esta entrega):** implementación cerrada según el alcance acordado (Fases 1–4 + endpoints de transición + seeds RBAC).  

