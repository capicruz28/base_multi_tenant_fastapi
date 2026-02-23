# Administración del catálogo de permisos (`permiso`)

## Cómo funciona el modelo (resumen)

| Tabla | Qué es | Quién la llena |
|-------|--------|----------------|
| **permiso** | Catálogo **global** de todos los permisos de negocio posibles (admin.usuario.leer, mfg.orden_produccion.crear, org.area.leer, etc.). Una sola vez en BD central. | **SuperAdmin / equipo técnico**: por seed SQL o por una pantalla de administración del catálogo. |
| **cliente_modulo** | Qué **módulos** tiene contratados/habilitados cada cliente (ORG, LOG, MFG, etc.). | **SuperAdmin** (o proceso comercial): al activar un módulo para un cliente. |
| **rol_permiso** | Qué permisos del catálogo tiene asignados **cada rol** (por tenant). | **Admin del tenant** (o SuperAdmin): desde la pantalla “Permisos de negocio” del rol. |

**Importante:** Al **habilitar un módulo para un cliente** solo se inserta/actualiza **cliente_modulo**. **No** se crean filas nuevas en **permiso**. Los permisos de ese módulo ya deben existir en el catálogo (por seed o por administración).

---

## ¿Qué tienes que hacer al habilitar un módulo para un cliente?

Solo esto:

1. **Activar el módulo para el cliente**  
   Insertar o actualizar en **cliente_modulo** (cliente_id, modulo_id, esta_activo, fecha_vencimiento, etc.). Eso ya lo haces desde tu flujo de “activar módulo” (SuperAdmin o API de cliente-modulo).

2. **No tocar la tabla permiso**  
   No hace falta crear permisos al habilitar el módulo. El catálogo **permiso** ya debe contener todos los permisos de todos los módulos (por ejemplo mediante el seed `SEED_PERMISOS_RBAC.sql`). El backend filtra por prefijo del código (org., log., mfg., etc.) y por los módulos que el cliente tiene en **cliente_modulo**, y el front solo muestra esos.

Resumen: **habilitar módulo = solo cliente_modulo**. La tabla **permiso** no se llena en ese momento.

---

## ¿Cómo se llena la tabla permiso?

La tabla **permiso** es un catálogo previo. Se puede llenar y mantener de dos maneras.

### Opción A: Solo scripts SQL (actual)

- **Primera carga:** ejecutar **SEED_PERMISOS_RBAC.sql** en la BD central. Eso inserta todos los permisos por módulo (admin, modulos, mfg, bi, org, log, etc.) con MERGE para no duplicar por código.
- **Nuevos permisos o nuevo módulo:**  
  - Añadir un nuevo bloque en `SEED_PERMISOS_RBAC.sql` (o un script nuevo) con MERGE/INSERT de los nuevos códigos (convención: `modulo.recurso.accion`).  
  - Ejecutar el script en central cuando se agregue un módulo o nuevas acciones.
- **Ventaja:** simple, versionado, sin pantallas.  
- **Desventaja:** cualquier cambio exige script + despliegue/ejecución en BD.

### Opción B: Administración (SuperAdmin) del catálogo

- **Pantalla “Catálogo de permisos”** (solo SuperAdmin):
  - **Listar** todos los registros de **permiso** (con filtro opcional por módulo si se usa `modulo_id`).
  - **Crear** permiso: codigo (único), nombre, descripcion, recurso, accion, modulo_id (opcional), es_activo.
  - **Editar** nombre, descripcion, es_activo (y opcionalmente modulo_id).
  - **Desactivar** (es_activo = 0) en lugar de borrar.
- **API necesaria (backend):**
  - GET /api/v1/permisos-catalogo-admin/ (listado completo, sin filtro por tenant; solo SuperAdmin).
  - POST /api/v1/permisos-catalogo-admin/ (crear).
  - PUT /api/v1/permisos-catalogo-admin/{permiso_id} (actualizar).
  - PATCH o PUT para desactivar (es_activo).
- **Ventaja:** no hace falta tocar SQL para nuevos permisos o nuevos módulos.  
- **Desventaja:** hay que construir y mantener esta pantalla y los endpoints.

---

## Flujo recomendado según tu caso

1. **Solo necesitas que, al habilitar ORG/LOG/etc., el tenant vea y asigne permisos de ese módulo**  
   → No hace falta “llenar permiso” al habilitar. Solo asegúrate de que el seed (o el catálogo) ya tenga los permisos de esos módulos (org.*, log.*, etc.) y de que el backend filtre por **cliente_modulo** (ya implementado). Al habilitar un módulo, solo se actualiza **cliente_modulo**.

2. **Quieres añadir nuevos permisos o un módulo nuevo sin tocar SQL**  
   → Implementar la **Opción B**: administración del catálogo **permiso** (CRUD SuperAdmin + endpoints anteriores). Los permisos “se crean” desde esa pantalla (o API), no al habilitar el módulo.

3. **Te basta con scripts SQL**  
   → Mantener **Opción A**: al agregar un módulo nuevo, añadir un bloque en `SEED_PERMISOS_RBAC.sql` (o script aparte) con los permisos del módulo y ejecutarlo en central. Opcionalmente rellenar **permiso.modulo_id** con el `modulo_id` del módulo para que el filtro por módulo sea también por BD y no solo por prefijo de código.

---

## Resumen en una frase

**Al habilitar un módulo para un cliente solo se usa cliente_modulo; la tabla permiso no se llena en ese momento.** El catálogo **permiso** se llena antes (por seed o por una administración SuperAdmin de “Catálogo de permisos”), y el sistema solo decide qué permisos del catálogo puede ver/asignar cada tenant según sus módulos en **cliente_modulo**.
