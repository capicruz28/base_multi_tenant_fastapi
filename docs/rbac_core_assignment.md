## Asignación del permiso CORE `core.app.acceder` a roles

### Objetivo del permiso base

El permiso `core.app.acceder` representa el **derecho mínimo** para poder acceder al ERP:

- **Código:** `core.app.acceder`
- **Significado:** el rol que lo tenga puede iniciar sesión y acceder a la aplicación.
- **Alcance:** independiente de los permisos de negocio de cada módulo (ORG, INV, CRM, etc.).

Este permiso se crea mediante el seed `app/docs/database/SEED_PERMISOS_CORE.sql`.

### Asignación por rol (no por usuario)

- El modelo RBAC central es:
  - `usuario` → `rol` → `rol_permiso` → `permiso`.
- Por consistencia y mantenibilidad:
  - **Las capacidades se definen a nivel de rol**, no de usuario individual.
  - Asignar `core.app.acceder` directamente a usuarios rompería la abstracción y complicaría la gestión.
- Por eso, el seed `SEED_ASIGNAR_CORE_APP_A_ROLES.sql`:
  - Busca el `permiso_id` de `core.app.acceder`.
  - Inserta en `rol_permiso` una fila por cada rol activo que aún no tenga ese permiso.

### Cómo funciona el seed de asignación CORE

Script: `app/docs/database/SEED_ASIGNAR_CORE_APP_A_ROLES.sql`

- **Paso 1:** localizar `permiso_id` de `core.app.acceder` en `permiso`.
- **Paso 2:** para cada rol activo con `cliente_id IS NOT NULL`:
  - Inserta `(cliente_id, rol_id, permiso_id)` en `rol_permiso` si no existe todavía.
- **Paso 3:** para roles de sistema (`cliente_id IS NULL`):
  - Cruza con todos los `cliente` y asigna el permiso por cada combinación `(cliente_id, rol_id)` que no lo tenga.
- El script es:
  - **Idempotente** (usa `NOT EXISTS` sobre `(cliente_id, rol_id, permiso_id)`).
  - Seguro frente a múltiples ejecuciones.

### Eliminación de la dependencia de accessLevel

- Anteriormente, el acceso global al ERP podía depender de:
  - Flags como `accessLevel`, `is_admin`, o reglas implícitas en código.
- Con `core.app.acceder`:
  - El derecho a entrar al ERP se **expresa como un permiso estándar** en la tabla `permiso`.
  - Los roles que deben poder acceder al sistema simplemente **incluyen este permiso**.
  - La lógica de autenticación podrá comprobar en el futuro:
    - “¿El usuario tiene algún rol con `core.app.acceder` activo en este tenant?”
- Esto alinea el acceso global con el mismo modelo que el resto de permisos de negocio.

### Uso futuro en backend (aún no aplicado)

- El backend todavía **no ha sido modificado** para usar `core.app.acceder`.
- Próximos pasos típicos (fuera de este documento):
  - En la capa de autenticación/autorización, añadir una verificación temprana de este permiso tras el login.
  - Opcionalmente, exponerlo en la UI de administración de roles como “Acceder a la aplicación”.

En resumen, la combinación de:

- `SEED_PERMISOS_CORE.sql` (crea el permiso),
- y `SEED_ASIGNAR_CORE_APP_A_ROLES.sql` (lo asigna a todos los roles activos),

prepara la base de datos para que el control de acceso global al ERP esté plenamente integrado en el modelo RBAC existente.

