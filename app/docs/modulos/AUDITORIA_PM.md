# Auditoría PM — Gestión de Proyectos

Documento generado en **Fase 2** del prompt maestro. Referencia BD: `docs/bd/PM_TABLAS.sql` (tabla `pm_proyecto`).

---

## 1. Tablas detectadas y tipo

| Tabla        | Tipo (Fase 1) | Notas breves |
|-------------|-----------------|--------------|
| `pm_proyecto` | Maestro con estado operativo | Sin columnas típicas de documento borrador/aprobación. Sin `es_activo` en el script adjunto PM. |

---

## 2. Implementación actual (archivos)

| Capa / rol | Rutas relativas |
|------------|-----------------|
| Routers agregados | `app/modules/pm/presentation/endpoints.py`, `endpoints_proyecto.py` |
| Schemas | `app/modules/pm/presentation/schemas.py` |
| Servicios aplicación | `app/modules/pm/application/services/proyecto_service.py` |
| Persistencia SQL (Core) | `app/infrastructure/database/queries/pm/proyecto_queries.py`, `tables_erp/tables_pm.py` |
| Repositories dedicados | **No existe** capa `*repository*`; el servicio delega directamente en `proyecto_queries`. |

Prefijo OpenAPI efectivo asumiendo `settings.API_V1_STR` habitual (`/api/v1`): base **`/api/v1/pm`**, recurso proyectos **`/proyectos`**.

---

## 3. Endpoints existentes

| Ruta | Método | Entidad | Tenant (`cliente_id`) | `empresa_id` en operación | RBAC declarado |
|------|--------|---------|------------------------|----------------------------|----------------|
| `/api/v1/pm/proyectos` | `GET` | `pm_proyecto` | Sí (`current_user.cliente_id` → queries) | Filtro opcional en query (`empresa_id`) | `Depends(require_permission("pm.proyecto.leer"))` |
| `/api/v1/pm/proyectos/{proyecto_id}` | `GET` | `pm_proyecto` | Sí (`cliente_id` + `proyecto_id`) | No se envía ni valida | `pm.proyecto.leer` |
| `/api/v1/pm/proyectos` | `POST` | `pm_proyecto` | Sí (`cliente_id` forzado en insert) | En body obligatorio (`ProyectoCreate.empresa_id`) | `pm.proyecto.crear` |
| `/api/v1/pm/proyectos/{proyecto_id}` | `PUT` | `pm_proyecto` | Sí (`WHERE cliente_id`) | No en path/query; cambio solo si llega en body (vide schemas §5) | `pm.proyecto.actualizar` |

Notas tenant:

- **Listado:** coherente con filtro opcional por `empresa_id`.
- **Detalle y PUT:** sólo garantizan pertenencia al **tenant (cliente)**. No aplican **`empresa_id` como segundo criterio** en `get`/`update` como hacen otros módulos maestros (p. ej. ORG con query opcional de empresa). Riesgo: dentro de un cliente multi-empresa, un proyecto de otra empresa del mismo cliente sería visible/actualizable si se conoce el UUID (`proyecto_id`).

---

## 4. Brechas funcionales vs patrón maestro/transaccional/derivado

### 4.1 `pm_proyecto` (maestro según Fase 1)

| Esperado (maestro) | Estado |
|-------------------|--------|
| Crear | Cubierto (`POST`) |
| Listar | Cubierto (`GET` colección + filtros) |
| Detalle | Cubierto (`GET` por id) |
| Actualizar | Cubierto (`PUT`) |
| Activar / desactivar | **No aplicable literalmente**: la tabla en `docs/bd/PM_TABLAS.sql` **no define** `es_activo`. Opciones futuras sin tocar BD: endpoints que alteren sólo **`estado`** (p. ej. flujos “pausado/cancelado”) o convenio de negocio documentado |
| Eliminar físico | No implementado (**correcto** respecto reglas del proyecto / soft-delete habituales)

### 4.2 Transaccional estándar (borrador, aprobar, procesar, anular)

**No corresponde** al modelo actual de `pm_proyecto` según SQL adjunto PM.

### 4.3 Tablas derivadas / analíticas

Ninguna en `PM_TABLAS.sql`.

---

## 5. Campos BD vs schemas (Brecha de exposición)

Columnas **`pm_proyecto`** (`docs/bd/PM_TABLAS.sql`):  
`proyecto_id`, `cliente_id`, `empresa_id`, `codigo_proyecto`, `nombre`, `descripcion`, `cliente_venta_id`, `fecha_inicio`, `fecha_fin_estimada`, `fecha_fin_real`, `presupuesto`, `costo_real`, `responsable_usuario_id`, `estado`, `fecha_creacion`.

### Por schema

| Schema | Coincidencia | Campos que existen en BD y **no** están en el schema (o no pueden enviarse) |
|--------|----------------|---------------------------------------------------------------------------|
| `ProyectoRead` | Completo para lectura respecto columnas tabuladas arriba | Ninguno faltante |
| `ProyectoCreate` | Correcto omitir PK y `cliente_id`/`fecha_creacion` | N/A |
| `ProyectoUpdate` | Parcial opcional válido (`exclude_none` en update) | **`empresa_id`**: existe en BD; **no está** en `ProyectoUpdate` → no hay forma oficial de cambiar empresa vía schema actual (solo si algún proceso lo hiciera fuera del contrato) |

No se reportan otros campos de BD ausentes en `ProyectoRead` dentro del alcance de `PM_TABLAS.sql`.

---

## 6. Permisos RBAC y seeds

Códigos usados en rutas:

- `pm.proyecto.leer`
- `pm.proyecto.crear`
- `pm.proyecto.actualizar`

**Hallazgo:** en `app/docs/database/` no se localizó un script dedicado tipo `SEED_PERMISOS_RBAC_PM.sql` ni entradas obvias en los `SEED_PERMISOS_RBAC*.sql` revisados que inserten estos códigos. **Riesgo:** roles sin permisos explícitos podrían no poder usar el módulo (según cómo se gestione `has_permission` y administradores de tenant).

**Sugerencia Fase 3:** añadir seeds alineados con otros módulos (`[modulo].[recurso].[accion]`) y documentar en implementación.

---

## 7. Problemas / observaciones (sin eliminar código)

| Tema | Severidad | Comentario |
|------|-----------|------------|
| Alcance `empresa_id` en GET/PUT por id | Media | Reglas del proyecto piden validar `empresa_id` cuando la tabla lo tiene; detalle/actualización no lo reciben ni filtran |
| Seed permisos PM | Media | Permisos referenciados en código podrían no existir en datos sembrados |
| Capa “repository” | Baja | Patrón actual = servicio + `*_queries`; coherente con partes del monolito pero distinto del esquema teórico “router → service → repository” |
| Activar/desactivar maestro | Baja/N/A | Condicionado a ausencia de `es_activo` en BD adjunta |

No se marca código como “obsoleto” para borrado: **no aplicar eliminaciones** en esta auditoría.

---

## 8. Endpoints sugeridos (solo si negocio / Fase 3 lo aprueban)

| Ruta sugerida | Método | Motivo |
|---------------|--------|--------|
| Mismo GET/PUT con `empresa_id` opcional (query) igual que otros maestros | `GET`, `PUT` | Alinear validación multi-empresa dentro del mismo `cliente_id` |
| Variante sólo estado (si se desea “activar/desactivar” semántico) | `PATCH` o `POST` bajo recurso proyecto | Solo si conviene mapear a `estado` sin `es_activo` |

Rutas y métodos anteriores **no sustituyen** los existentes; serían complementos tras definición funcional explícita.

---

## 9. Resumen ejecutivo

- **Tablas PM (`pm_*`) en alcance BD adjunta:** 1 (`pm_proyecto`).
- **CRUD básico** de proyecto: presente (`GET` lista/detalle, `POST`, `PUT`).
- **Gaps:** validación opcional/forzosa de **`empresa_id`** en lectura y actualización por id; **`empresa_id`** no exponible en `ProyectoUpdate`; **seeds RBAC PM** no localizados; **activar/desactivar** clásicos sin columna **`es_activo`** en script PM.

---

*Fin del informe Fase 2.*
