# Documentación Frontend — Módulo DMS (Gestión Documental)

**Versión:** 1.0  
**Fecha:** 2026-02-18  
**Módulo:** DMS - Gestión Documental

---

## Índice

1. [Información General](#información-general)
2. [Autenticación](#autenticación)
3. [Endpoints](#endpoints)
4. [Schemas TypeScript](#schemas-typescript)
5. [Códigos de Error](#códigos-de-error)
6. [Rutas SPA Recomendadas](#rutas-spa-recomendadas)
7. [Flujo de Implementación Recomendado](#flujo-de-implementación-recomendado)
8. [Notas Importantes](#notas-importantes)

---

## Información General

### Base URL

```
/api/v1/dms
```

### Dependencias

- **Módulo ORG:** Empresa (obligatorio).
- **Orden recomendado:** Configurar ORG; luego registrar y buscar documentos (metadatos; la subida del archivo físico puede hacerse por otro endpoint o almacenamiento).

---

## Autenticación

Todos los endpoints requieren JWT en el header:

```http
Authorization: Bearer <token>
```

El `cliente_id` se obtiene del token; **no enviar en el body**.

---

## Endpoints

### 1. Documentos

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/dms/documentos | Listar (empresa_id, tipo_documento, categoria, estado, entidad_tipo, entidad_id, carpeta, buscar) |
| GET | /api/v1/dms/documentos/{documento_id} | Detalle |
| POST | /api/v1/dms/documentos | Crear registro de documento (metadatos) |
| PUT | /api/v1/dms/documentos/{documento_id} | Actualizar metadatos |

**Campos principales en creación:** empresa_id, codigo_documento, nombre_archivo, descripcion, tipo_documento (contrato, factura, reporte, certificado, etc.), categoria, ruta_archivo, **tamano_bytes**, extension, mime_type, carpeta, tags (JSON array como string), entidad_tipo, entidad_id, version (ej. 1.0), documento_padre_id (para versionamiento), es_confidencial, nivel_acceso (publico, general, restringido, confidencial), estado (activo, archivado, eliminado), subido_por_usuario_id.

**Nota:** La API usa **tamano_bytes** (sin ñ). En base de datos la columna es `tamaño_bytes`; el backend realiza la conversión.

---

### 2. Búsqueda (UI)

El menú incluye "Búsqueda" por nombre, tipo, fecha, etiquetas. Usar GET /dms/documentos con query params: buscar, tipo_documento, categoria, carpeta. Filtrar por fecha en frontend si se desea (fecha_creacion en la respuesta).

---

## Schemas TypeScript

### Documento

```typescript
interface DocumentoCreate {
  empresa_id: string;
  codigo_documento?: string;
  nombre_archivo: string;
  descripcion?: string;
  tipo_documento: string;
  categoria?: string;
  ruta_archivo: string;
  tamano_bytes?: number;   // En API se usa "tamano_bytes" (sin ñ)
  extension?: string;
  mime_type?: string;
  carpeta?: string;
  tags?: string;           // JSON array como string, ej. '["tag1","tag2"]'
  entidad_tipo?: string;
  entidad_id?: string;
  version?: string;
  documento_padre_id?: string;
  es_confidencial?: boolean;
  nivel_acceso?: 'publico' | 'general' | 'restringido' | 'confidencial';
  estado?: 'activo' | 'archivado' | 'eliminado';
  subido_por_usuario_id?: string;
}

interface DocumentoUpdate {
  codigo_documento?: string;
  nombre_archivo?: string;
  descripcion?: string;
  tipo_documento?: string;
  categoria?: string;
  ruta_archivo?: string;
  tamano_bytes?: number;
  extension?: string;
  mime_type?: string;
  carpeta?: string;
  tags?: string;
  entidad_tipo?: string;
  entidad_id?: string;
  version?: string;
  documento_padre_id?: string;
  es_confidencial?: boolean;
  nivel_acceso?: string;
  estado?: string;
  subido_por_usuario_id?: string;
}

interface DocumentoRead extends DocumentoCreate {
  documento_id: string;
  cliente_id: string;
  fecha_creacion: string;
  fecha_modificacion?: string;
}
```

---

## Códigos de Error

| Código | Descripción |
|--------|-------------|
| 401 | No autenticado |
| 403 | Sin permisos |
| 404 | Documento no encontrado |
| 422 | Error de validación (body o query) |
| 500 | Error interno |

---

## Rutas SPA Recomendadas

```
/dms
  /documentos
    /list
    /create
    /:documento_id/edit
    /:documento_id
  /busqueda
    # Filtros: nombre, tipo, categoria, carpeta, etiquetas
```

---

## Flujo de Implementación Recomendado

### 1. Configuración previa

- Tener ORG (empresa) configurado.

### 2. Documentos (metadatos)

- Tras subir el archivo a almacenamiento (blob/storage), crear registro: POST /dms/documentos (empresa_id, nombre_archivo, tipo_documento, ruta_archivo, tamano_bytes, extension, mime_type, carpeta, nivel_acceso, estado: "activo", subido_por_usuario_id).
- Listar por empresa_id, tipo_documento, categoria o carpeta para biblioteca de documentos.
- Actualizar metadatos (PUT) para descripcion, tags, estado (archivado/eliminado), o nueva version (documento_padre_id).

### 3. Versionamiento

- Al subir una nueva versión del mismo documento: crear otro registro con documento_padre_id = documento_id del original; version = "1.1" o "2.0" según criterio.

### 4. Búsqueda

- GET /dms/documentos?buscar=...&tipo_documento=...&categoria=...&carpeta=... para pantalla de búsqueda.

---

## Notas Importantes

1. **Multi-tenancy:** Todo se filtra por `cliente_id` del token. No enviar `cliente_id` en el body.

2. **tamano_bytes:** En la API se usa **tamano_bytes** (sin ñ). En BD la columna es `tamaño_bytes`; el backend convierte automáticamente.

3. **Archivo físico:** Este módulo gestiona **metadatos** del documento. La subida/descarga del archivo (ruta_archivo, almacenamiento) puede implementarse en otro endpoint o servicio de almacenamiento; aquí solo se guarda ruta_archivo y datos asociados.

4. **tags:** Se almacenan como string (por ejemplo JSON array: `["tag1","tag2"]`). El frontend puede parsear/stringify al mostrar o editar.

5. **entidad_tipo / entidad_id:** Permiten vincular el documento a una entidad (cliente, empleado, producto, proyecto). Valores sugeridos para entidad_tipo: 'cliente', 'empleado', 'producto', 'proyecto'.

6. **nivel_acceso:** publico, general, restringido, confidencial. Validar en frontend/backend según permisos antes de mostrar o permitir descarga.

7. **IDs en URLs:** documento_id es UUID.

8. **Versionamiento:** documento_padre_id apunta al documento anterior; version es texto (ej. "1.0", "1.1", "2.0").

---

**Fin de la documentación del módulo DMS**
