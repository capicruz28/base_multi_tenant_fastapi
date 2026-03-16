## RBAC Wave 2 – Contrato de permisos de negocio

### 1. Alcance y estándar

- **Fuente**: `docs/rbac_permission_coverage_report.md` (Wave 2 – endpoints sin `require_permission`).
- **Objetivo**: Definir el **contrato oficial** de permisos antes de decorar endpoints.
- **Patrón de permiso**:  
  - Forma general: `<modulo>.<recurso>.<accion>`  
  - `modulo`: identificador lógico en `snake_case` (ej. `mfg`, `tenant`, `wms`, `admin`).  
  - `recurso`: nombre de recurso de negocio en `snake_case`, preferentemente **singular** (`cliente`, `lista_materiales`, `centro_trabajo`).  
  - `accion`: una de **`leer`**, **`crear`**, **`actualizar`**, **`eliminar`**.
- **Excepciones controladas**:
  - `core.app.acceder`: permiso **CORE** que representa “acceso global al ERP”. No es CRUD puro, se mantiene como excepción explícita.

Las listas siguientes ya incorporan la **normalización decidida** (singular/plural, naming consistente y resolución de duplicados semánticos).

---

### 2. Permisos CORE / Auth

#### 2.1. Permiso CORE de acceso

- `core.app.acceder`  
  - **Tipo**: permiso CORE especial (no CRUD).  
  - **Uso**: condición mínima de acceso al ERP (`/auth/me`).  
  - **Estado**: ya definido en `SEED_PERMISOS_CORE.sql`, se mantiene tal cual.

#### 2.2. Auth – Gestión de permisos y menú

- **Módulo**: `auth`
- **Recursos y acciones**:
  - `auth.permission.leer`  
    - Lectura de permisos efectivos del usuario (ej. `/auth/permissions/me`).
  - `auth.menu.leer`  
    - Lectura del menú/autorización de navegación del usuario (ej. `/auth/menu`).

> **Decisión de normalización**:  
> - En el reporte aparecía alternativamente `auth.permission.leer` **o** `core.app.acceder` para `/permissions/me`.  
>   - Se fija **`auth.permission.leer`** como permiso específico de lectura de permisos.  
>   - `core.app.acceder` se mantiene como permiso de acceso base, no de listado.  
> - Para menú se proponía `auth.menu.leer` o `modulos.menu.leer`.  
>   - Se fija **`auth.menu.leer`** como permiso de lectura de menú para el endpoint de Auth.  
>   - `modulos.menu.leer` y `modulos.menu.administrar` existen ya como permisos de administración de catálogo de menú; se mantienen para backend de configuración, no para `/auth/menu`.

#### 2.3. Auth – Debug

- **Módulo**: `auth`
- **Recurso**: `debug`
- **Acciones**:
  - `auth.debug.leer`  
    - Acceso a endpoints de debug como `/clientes/debug/user-info` y `/clientes/debug/access-levels` (solo roles de soporte / entornos no productivos).

---

### 3. Módulo Tenant – Clientes y branding

#### 3.1. Clientes (`tenant.cliente.*`)

- `tenant.cliente.crear`
- `tenant.cliente.leer`
- `tenant.cliente.actualizar`
- `tenant.cliente.eliminar`

Usos previstos:
- Crear, listar y leer detalle de clientes (`/clientes/`).
- Actualizar, suspender y activar clientes (todas las variantes mapean a `actualizar`).

#### 3.2. Branding (`tenant.branding.*`)

- `tenant.branding.leer`  
  - Lectura de branding del tenant (`/clientes/tenant/branding`).

---

### 4. Módulo Tenant – Conexiones (`tenant.conexion.*`)

Permisos para gestión de conexiones de BD/híbridas:

- `tenant.conexion.leer`
- `tenant.conexion.crear`
- `tenant.conexion.actualizar`
- `tenant.conexion.eliminar`

Usos previstos:
- Listar conexiones de un cliente, obtener conexión principal.  
- Crear nuevas conexiones, actualizar y desactivar/eliminar conexiones.

---

### 5. Módulo WMS

#### 5.1. Zonas de almacén (`wms.zona.*`)

- `wms.zona.crear`

Usos previstos:
- Creación de zonas de almacén (`POST /wms/zonas`).

> **Nota**: Para Wave 2 solo se introduce `crear`.  
> Lecturas/actualizaciones ya tienen otros permisos en uso; extensiones (`leer`, `actualizar`, `eliminar`) se podrán añadir si se alinean más endpoints en fases posteriores.

#### 5.2. Ubicaciones (`wms.ubicacion.*`)

- `wms.ubicacion.crear`

Usos previstos:
- Creación de ubicaciones (`POST /wms/ubicaciones`).

---

### 6. Módulo MFG (Manufactura)

Todos los recursos usan nombres en **singular**, en `snake_case`, aunque las rutas puedan estar en plural.

#### 6.1. Orden de producción – operaciones (`mfg.orden_produccion_operacion.*`)

- `mfg.orden_produccion_operacion.leer`
- `mfg.orden_produccion_operacion.crear`
- `mfg.orden_produccion_operacion.actualizar`

#### 6.2. Consumo de materiales (`mfg.consumo_material.*`)

- `mfg.consumo_material.leer`
- `mfg.consumo_material.crear`
- `mfg.consumo_material.actualizar`

> **Normalización**:  
> - El recurso se escribe en singular `consumo_material` aunque la ruta sea `/consumo-materiales`.  
> - Se mantiene este criterio para coherencia con el resto de MFG.

#### 6.3. Ruta de fabricación – detalle (`mfg.ruta_fabricacion_detalle.*`)

- `mfg.ruta_fabricacion_detalle.leer`
- `mfg.ruta_fabricacion_detalle.crear`
- `mfg.ruta_fabricacion_detalle.actualizar`

#### 6.4. Rutas de fabricación (`mfg.ruta_fabricacion.*`)

- `mfg.ruta_fabricacion.leer`
- `mfg.ruta_fabricacion.crear`
- `mfg.ruta_fabricacion.actualizar`

> **Relación semántica**:  
> - `ruta_fabricacion` y `ruta_fabricacion_detalle` se consideran recursos distintos: cabecera vs detalle.  
> - No se fusionan en un único recurso para mantener granularidad en permisos.

#### 6.5. Lista de materiales – detalle (`mfg.lista_materiales_detalle.*`)

- `mfg.lista_materiales_detalle.leer`
- `mfg.lista_materiales_detalle.crear`
- `mfg.lista_materiales_detalle.actualizar`

#### 6.6. Listas de materiales (BOM) (`mfg.lista_materiales.*`)

- `mfg.lista_materiales.leer`
- `mfg.lista_materiales.crear`
- `mfg.lista_materiales.actualizar`

> **Normalización**:
> - Se usa `lista_materiales` (singular compuesto) tanto para cabecera como para detalle (`lista_materiales_detalle`).  
> - No se crea un recurso alternativo tipo `bom` para evitar duplicados semánticos.

#### 6.7. Operaciones (`mfg.operacion.*`)

- `mfg.operacion.leer`
- `mfg.operacion.crear`
- `mfg.operacion.actualizar`

#### 6.8. Centros de trabajo (`mfg.centro_trabajo.*`)

- `mfg.centro_trabajo.leer`
- `mfg.centro_trabajo.crear`
- `mfg.centro_trabajo.actualizar`

---

### 7. Módulo Users / Administración (`admin.*`)

Permisos orientados a administración de usuarios y roles (no al módulo `users` en sí):

- `admin.usuario.leer`  
  - Lectura de usuarios (más allá del self-service) – `/usuarios/{id}/`.
- `admin.rol.leer`  
  - Lectura de roles de un usuario – `/usuarios/{id}/roles/`.

> **Normalización**:  
> - Se usa el módulo lógico `admin` para operaciones de administración, manteniendo `usuario` y `rol` en singular.  
> - En el código ya se usan estos mismos códigos en llamadas a `has_permission`, por lo que se consolidan como oficiales.

---

### 8. Módulo Superadmin (`superadmin.*`)

Permiso global para vistas de usuarios en contexto de superadministración:

- `superadmin.usuario.leer`

Cobertura:
- Listado global de usuarios.  
- Detalle de usuario.  
- Actividad y sesiones.  
- Listado de usuarios por cliente.

> **Criterio**:  
> - Todas las vistas de usuarios en `/superadmin/usuarios/...` comparten el mismo permiso `superadmin.usuario.leer`, pues el filtro funcional se hace por tipo de vista, no por capacidades diferentes de negocio.

---

### 9. Resumen de permisos normalizados (Wave 2)

Lista consolidada (sin duplicados):

- **CORE/Auth**
  - `core.app.acceder` *(excepción no CRUD)*
  - `auth.permission.leer`
  - `auth.menu.leer`
  - `auth.debug.leer`
- **Tenant**
  - `tenant.cliente.crear`
  - `tenant.cliente.leer`
  - `tenant.cliente.actualizar`
  - `tenant.cliente.eliminar`
  - `tenant.branding.leer`
  - `tenant.conexion.leer`
  - `tenant.conexion.crear`
  - `tenant.conexion.actualizar`
  - `tenant.conexion.eliminar`
- **WMS**
  - `wms.zona.crear`
  - `wms.ubicacion.crear`
- **MFG**
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
- **Admin / Superadmin**
  - `admin.usuario.leer`
  - `admin.rol.leer`
  - `superadmin.usuario.leer`

Este documento sirve como **contrato de referencia** para Wave 2: cualquier nueva decoración con `require_permission(...)` en los endpoints auditados deberá usar exactamente estos códigos, salvo decisión explícita de cambio futuro documentado en una nueva versión del contrato.

