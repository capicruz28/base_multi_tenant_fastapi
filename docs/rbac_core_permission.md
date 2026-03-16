## Permiso CORE de acceso a la aplicación

### Qué es `core.app.acceder`

- **Código:** `core.app.acceder`
- **Nombre:** Acceder a la aplicación
- **Descripción:** Permite iniciar sesión y acceder al sistema ERP.
- **Recurso:** `app`
- **Acción:** `acceder`
- **Módulo:** ORG (`modulo_id = E1000001-0000-4000-8000-000000000001`, es_core = 1).

Este permiso representa el **derecho base** para poder usar la aplicación a nivel de ERP, independiente de los permisos de negocio de cada módulo.

### Cómo se crea (seed CORE)

- El permiso se inserta en la tabla `permiso` mediante el script:
  - `app/docs/database/SEED_PERMISOS_CORE.sql`
- Características del script:
  - Usa `MERGE` contra `permiso` **por `codigo`**.
  - Es **idempotente** (se puede ejecutar varias veces sin duplicar registros).
  - No depende de endpoints ni del auto-registro; es un permiso **de catálogo base**.

### Diferencia entre permisos CORE y permisos auto-registrados

- **Permisos CORE (seed)**:
  - Se definen explícitamente en scripts SQL (`SEED_PERMISOS_CORE.sql`, `SEED_PERMISOS_RBAC.sql`).
  - No dependen de decoradores en endpoints.
  - Representan capacidades **globales** o de plataforma (ej. `core.app.acceder`).
  - Siempre existen en la tabla `permiso` tras ejecutar los seeds.

- **Permisos auto-registrados por endpoints**:
  - Se descubren en runtime recorriendo los endpoints FastAPI.
  - Se basan en dependencias `Depends(require_permission("modulo.entidad.accion"))` o en el patrón A (`MODULE_CODE` / `RESOURCE_CODE`).
  - Representan acciones de **negocio** asociadas a rutas concretas de la API.
  - Se sincronizan al catálogo de `permiso` en el startup mediante el servicio de sync.

### Uso previsto de `core.app.acceder`

- Este permiso se utilizará en la capa de autenticación/autorización para:
  - Diferenciar entre usuarios que **solo tienen credenciales** y usuarios que, además, están **autorizados a acceder al ERP**.
  - Permitir políticas como:
    - "Usuario bloqueado para el ERP pero con acceso a otros servicios".
    - "Rol mínimo requerido para entrar en la aplicación".
- El backend y los roles aún **no se han modificado** para usar este permiso; este documento solo define la base RBAC y el seed correspondiente.

