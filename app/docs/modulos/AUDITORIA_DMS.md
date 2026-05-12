# Auditoría de Módulo — Gestión Documental (DMS)

Fecha: 2026-05-08  
Módulo: **Gestión Documental**  
Código: **DMS**

---

## Tablas detectadas y su tipo

Fuente: `docs/bd/DMS_TABLAS.sql` (filtrado por prefijo `DMS_` / `dms_`).

- **`dms_documento`**
  - **Tipo**: transaccional (gestión de documentos con metadata, seguridad, versionado y estado)
  - **Multi-tenant**: tiene `cliente_id` y `empresa_id`
  - **Soft delete**: **no** tiene `es_activo`; usa `estado` (`activo/archivado/eliminado`)
  - **FKs**:
    - `empresa_id` → `org_empresa(empresa_id)`
    - `documento_padre_id` → `dms_documento(documento_id)`

---

## Endpoints existentes

Fuente: `app/modules/dms/presentation/endpoints.py`, `app/modules/dms/presentation/endpoints_documento.py`

Base path (API v1): `GET/POST/PUT /dms/...` (registrado en `app/api/v1/api.py`).

Entidad: **Documento** (`dms_documento`)

- **Ruta**: `GET /dms/documentos`
  - **Método**: GET
  - **Entidad**: Documento
  - **Tenant**: **sí** (usa `current_user.cliente_id` y filtra en query)
  - **Empresa**: **parcial** (filtro `empresa_id` es opcional vía querystring)
  - **RBAC**: **sí** `dms.documento.leer`

- **Ruta**: `GET /dms/documentos/{documento_id}`
  - **Método**: GET
  - **Entidad**: Documento
  - **Tenant**: **sí** (filtro por `cliente_id` + `documento_id`)
  - **Empresa**: **no** (no valida `empresa_id` aunque la tabla lo tiene)
  - **RBAC**: **sí** `dms.documento.leer`

- **Ruta**: `POST /dms/documentos`
  - **Método**: POST
  - **Entidad**: Documento
  - **Tenant**: **sí** (inserta `cliente_id` desde `current_user.cliente_id`)
  - **Empresa**: **sí** (schema requiere `empresa_id`)
  - **RBAC**: **sí** `dms.documento.crear`

- **Ruta**: `PUT /dms/documentos/{documento_id}`
  - **Método**: PUT
  - **Entidad**: Documento
  - **Tenant**: **sí** (update por `cliente_id` + `documento_id`)
  - **Empresa**: **no** (no valida `empresa_id` aunque la tabla lo tiene)
  - **RBAC**: **sí** `dms.documento.actualizar`

---

## Endpoints faltantes (según patrón esperado)

> Referencia de patrón del prompt maestro:
> - **Maestros**: crear/listar/detalle/actualizar/activar-desactivar.
> - **Transaccionales**: crear borrador/actualizar (solo borrador)/aprobar/procesar/anular/listar/detalle.

Para `dms_documento`, hoy existe CRUD parcial (listar/detalle/crear/actualizar). No se observa un flujo de estados “borrador/aprobado/procesado/anulado”.

- **Faltante**: operación explícita de **cambio de estado** (mínimo)
  - **Sugerencia**: endpoints de transición para `estado` (p.ej. archivar / restaurar / marcar eliminado), manteniendo el contrato existente.
  - **Motivo**: la tabla usa `estado` como mecanismo principal de ciclo de vida y “no borrado físico”.

- **Faltante**: endpoint de **desactivación/soft-delete** alineado a reglas del proyecto
  - **Sugerencia**: en este módulo el equivalente sería **actualizar `estado`** (no hay `es_activo`).

---

## Campos faltantes en schemas (vs BD)

Comparación BD (`dms_documento`) vs schemas (`DocumentoCreate`, `DocumentoUpdate`, `DocumentoRead`):

- **No se detectan campos faltantes** en schemas para lectura/escritura respecto a lo definido en el SQL provisto.
- **Nota técnica**: BD usa `tamaño_bytes` (con `ñ`) y API usa `tamano_bytes`; el servicio implementa mapeo `tamano_bytes` ↔ `tamaño_bytes`.

---

## Problemas de tenant o RBAC

- **Tenant (`cliente_id`)**: OK (aplicado en list/get/update/create a nivel de query).
- **Empresa (`empresa_id`)**: **⚠ parcial/inconsistente**
  - `GET by id` y `PUT` no validan `empresa_id` aunque la tabla lo tiene.
  - `GET list` permite omitir `empresa_id`, lo cual puede ser válido si el diseño permite listar por cliente; pero contradice la regla “validar empresa_id cuando la tabla lo tenga” si se interpreta como obligatorio en toda operación.
- **RBAC**: OK (aplicado en endpoints con `require_permission`).

---

## Código marcado como obsoleto o incorrecto (NO eliminar)

- No se marca código obsoleto; pero se recomienda revisar la **validación de `empresa_id`** en endpoints `GET /{id}` y `PUT /{id}` para alinearse a regla multi-tenant por empresa.

---

## Resumen de brechas

- **Brecha principal**: faltan endpoints/operaciones de **ciclo de vida por `estado`** (archivar/eliminar lógico/restaurar), coherentes con “no eliminar físicamente”.
- **Brecha de tenant**: falta **enforcement** de `empresa_id` en operaciones por `documento_id` (lectura/actualización).

