# Flujo de autenticación y autorización base (CORE RBAC)

## Diferencia entre autenticación y autorización base

- **Autenticación:** verifica *quién* es el usuario (credenciales, JWT, refresh). Responde: “¿es un usuario válido del sistema?”.
- **Autorización base (CORE):** verifica *si ese usuario tiene derecho a usar el ERP*. Responde: “¿puede este usuario acceder a la aplicación?”.

Un usuario puede estar **autenticado** (token válido) pero **no autorizado** para acceder al sistema si no tiene el permiso `core.app.acceder`. En ese caso, el endpoint `GET /auth/me/` devuelve **403** con el mensaje *"Usuario sin acceso al sistema"*, de modo que el frontend puede redirigir a una pantalla de “sin acceso” en lugar de reconstruir la sesión como si tuviera acceso.

## Por qué `core.app.acceder` reemplaza a `accessLevel`

- **Problema con `accessLevel`:**
  - Era un número o flag en el token o en lógica dispersa (super_admin, tenant_admin, user).
  - La decisión de “¿puede entrar al ERP?” dependía de ese valor en varios sitios, lo que generaba:
    - Sesión que “pierde” nivel al refrescar (F5).
    - Redirecciones inconsistentes a `/unauthorized`.
    - Reglas duplicadas entre backend y frontend.

- **Ventaja de `core.app.acceder`:**
  - El derecho a **acceder al sistema** es un **permiso RBAC** más, almacenado en `permiso` y asignado a roles en `rol_permiso`.
  - Se evalúa con la misma función que el resto de permisos: `has_permission(current_user, "core.app.acceder")`.
  - Una sola comprobación en un solo sitio: **GET /auth/me/** (reconstrucción de sesión). Si el usuario no tiene el permiso → 403 y mensaje claro.
  - Deja de ser necesario depender de `accessLevel` para decidir “¿puede entrar?”; el permiso CORE es la fuente de verdad.

## Cómo unifica superadmin, admin y usuario tenant

- **Superadministrador:** tiene todos los permisos (bypass en `has_permission`). Por tanto tiene implícitamente `core.app.acceder` y pasa el chequeo en `/me/`.
- **Administrador (tenant):** su rol “Administrador” tiene asignado `core.app.acceder` (vía `SEED_ASIGNAR_CORE_APP_A_ROLES.sql`). Sus permisos efectivos incluyen ese código → pasa el chequeo.
- **Usuario tenant (rol normal):** cualquier rol activo al que se le haya asignado `core.app.acceder` tendrá acceso; si un rol no lo tiene, ese usuario recibirá 403 en `/me/` y no podrá “entrar” al ERP.

Así, la regla “¿puede acceder al sistema?” es la misma para todos los tipos de usuario: **¿tiene el permiso `core.app.acceder`?** No hay ramas especiales por `accessLevel` ni por tipo de usuario para esta decisión.

## Dónde se aplica la validación

- **Endpoint:** `GET /api/v1/auth/me/`
- **Momento:** justo después de resolver al usuario con `get_current_active_user` (usuario con roles y permisos cargados).
- **Lógica:**  
  `if not has_permission(current_user, "core.app.acceder"):`  
  → `HTTPException(status_code=403, detail="Usuario sin acceso al sistema")`.
- **No se modifica:** login, refresh, JWT, decoradores RBAC existentes ni endpoints de negocio; solo se añade esta comprobación en `/me/`.

## Resumen

| Concepto | Descripción |
|----------|-------------|
| **Permiso** | `core.app.acceder` (seed en `SEED_PERMISOS_CORE.sql`) |
| **Asignación** | A todos los roles activos vía `SEED_ASIGNAR_CORE_APP_A_ROLES.sql` |
| **Validación** | En `GET /auth/me/` con `has_permission(current_user, "core.app.acceder")` |
| **Efecto** | Usuario sin permiso → 403 "Usuario sin acceso al sistema" |
| **Objetivo** | Unificar la decisión de acceso global al ERP y eliminar la dependencia de `accessLevel` para esa decisión. |
