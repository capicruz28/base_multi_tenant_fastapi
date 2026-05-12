# Implementación de Módulo — Gestión Documental (DMS)

Fecha: 2026-05-08  
Módulo: **Gestión Documental**  
Código: **DMS**

---

## Alcance implementado

Con base en `docs/bd/DMS_TABLAS.sql` (tabla `dms_documento`) y el reporte `app/docs/modulos/AUDITORIA_DMS.md`, se implementó:

- **Validación opcional de `empresa_id`** en operaciones por ID (lectura/actualización y transiciones).
- **Transiciones de estado** (soft delete por `estado`):
  - **archivar**: `activo → archivado`
  - **restaurar**: `archivado → activo`
  - **eliminar**: `activo|archivado → eliminado` (**sin borrado físico**)
- **Nuevos endpoints** para ejecutar dichas transiciones, sin eliminar ni modificar rutas existentes.
- **Seed RBAC** faltante para permisos `dms.documento.*`.

> Nota: No se modificó la estructura de BD.

---

## Archivos modificados o creados

### Documentación
- **Creado**: `app/docs/modulos/AUDITORIA_DMS.md`
- **Creado**: `app/docs/modulos/DMS_IMPLEMENTACION.md`

### Backend (DMS)
- **Modificado**: `app/infrastructure/database/queries/dms/documento_queries.py`
- **Modificado**: `app/infrastructure/database/queries/dms/__init__.py`
- **Modificado**: `app/modules/dms/application/services/documento_service.py`
- **Modificado**: `app/modules/dms/application/services/__init__.py`
- **Modificado**: `app/modules/dms/presentation/endpoints_documento.py`

### RBAC seeds
- **Creado**: `app/docs/database/SEED_PERMISOS_RBAC_DMS.sql`

---

## Endpoints (rutas nuevas y existentes)

### Existentes (no se eliminaron ni cambiaron de ruta/método)

- `GET /dms/documentos` (listar)
- `GET /dms/documentos/{documento_id}` (detalle)  
  - **Cambio no disruptivo**: se agregó query param opcional `empresa_id` para filtrar/validar por empresa cuando aplique.
- `POST /dms/documentos` (crear)
- `PUT /dms/documentos/{documento_id}` (actualizar)  
  - **Cambio no disruptivo**: se agregó query param opcional `empresa_id` para filtrar/validar por empresa cuando aplique.

### Nuevos

- `POST /dms/documentos/{documento_id}/archivar`  
  - **Efecto**: `estado: activo → archivado`
  - **Permiso**: `dms.documento.actualizar`
  - **Tenant**: siempre por `cliente_id`; `empresa_id` opcional por query

- `POST /dms/documentos/{documento_id}/restaurar`  
  - **Efecto**: `estado: archivado → activo`
  - **Permiso**: `dms.documento.actualizar`
  - **Tenant**: siempre por `cliente_id`; `empresa_id` opcional por query

- `DELETE /dms/documentos/{documento_id}`  
  - **Efecto**: soft delete, `estado: activo|archivado → eliminado`
  - **Permiso**: `dms.documento.eliminar`
  - **Tenant**: siempre por `cliente_id`; `empresa_id` opcional por query

---

## Verificaciones de tenant y RBAC (Fase 4)

Para **todos los endpoints nuevos**:
- **cliente_id**: se toma desde `current_user.cliente_id` y se aplica en queries (aislamiento multi-tenant).
- **empresa_id**: si se envía como query param, se aplica como filtro adicional en operaciones por `documento_id`.
- **RBAC**: se aplica con `require_permission`:
  - `dms.documento.leer` (GET)
  - `dms.documento.crear` (POST create)
  - `dms.documento.actualizar` (PUT + archivar/restaurar)
  - `dms.documento.eliminar` (DELETE soft delete)

---

## Seeds RBAC

Archivo agregado:
- `app/docs/database/SEED_PERMISOS_RBAC_DMS.sql`

Permisos sembrados:
- `dms.documento.leer`
- `dms.documento.crear`
- `dms.documento.actualizar`
- `dms.documento.eliminar`

---

## Notas técnicas relevantes

- La BD usa columna `tamaño_bytes` y la API expone `tamano_bytes`; el servicio hace el mapeo correspondiente.
- Las transiciones están implementadas como **updates con control de estado de origen**, para evitar cambios inválidos.

