# Documentación frontend: Administración de permisos RBAC (permisos de negocio)

Guía para implementar en el frontend la administración de **permisos de negocio** (RBAC): quién administra qué, dónde mostrarlo y qué API usar. Incluye criterios UX/UI para no confundir con los **permisos de menú** (rol–menú) que ya existen.

---

## 1. Dos tipos de “permisos” en el sistema

En el backend hay **dos modelos** distintos. El frontend debe tratarlos por separado para un buen diseño.

| Concepto | Tablas | Qué controla | Quién lo administra en UI |
|----------|--------|----------------|---------------------------|
| **Permisos de menú** | `rol_menu_permiso`, `modulo_menu` | Qué ítems de menú ve el usuario y con qué acciones (ver, crear, editar, eliminar por pantalla). | **Admin tenant** (y SuperAdmin). Ya existe en tu app (pantallas de “Permisos” por rol sobre menús). |
| **Permisos de negocio (RBAC)** | `permiso`, `rol_permiso` | Qué **acciones de API** puede ejecutar el usuario (ej. `admin.usuario.crear`, `mfg.orden_produccion.leer`). Protegen endpoints. | **Admin tenant** asigna permisos a **sus** roles. **SuperAdmin** puede, además, gestionar el **catálogo** global de permisos (si se implementa). |

Resumen para UX:

- **Permisos de menú:** “Qué ve y qué puede hacer en cada pantalla” (sidebar, botones por menú). Ya lo administras.
- **Permisos de negocio (RBAC):** “Qué puede hacer en el sistema a nivel de API” (quién puede crear usuarios, ver reportes, etc.). Es lo que debes administrar en la nueva pantalla.

---

## 2. Quién administra qué (SuperAdmin vs Admin tenant)

### 2.1 Matriz de responsabilidades

| Acción | SuperAdmin | Admin tenant |
|--------|------------|--------------|
| **Catálogo de permisos** (`permiso`: listar, crear, editar, desactivar) | ✅ Sí (si se implementa gestión de catálogo). | ❌ No. Solo **lectura** del catálogo para poder asignar. |
| **Asignar / quitar permisos a roles de su tenant** (`rol_permiso`) | ✅ Sí (en el tenant que esté gestionando). | ✅ Sí, solo sobre **roles de su propio cliente**. |
| **Crear / editar / eliminar roles de su tenant** | ✅ Sí. | ✅ Sí (roles del cliente). |
| **Asignar roles a usuarios de su tenant** | ✅ Sí. | ✅ Sí. |
| **Permisos de menú (rol–menú)** | ✅ Sí. | ✅ Sí. |
| **Gestionar otros clientes / otros tenants** | ✅ Sí. | ❌ No. |

En la práctica:

- **SuperAdmin:** puede hacer todo en cualquier tenant y, si se implementa, mantener el **catálogo global** de permisos (`permiso`).
- **Admin tenant:** administra **solo su tenant**: roles, usuarios, **asignación de permisos de negocio a sus roles** (desde un catálogo de solo lectura), y permisos de menú como hasta ahora.

### 2.2 Quién es “el encargado” en cada pantalla

- **Pantalla “Permisos de negocio” por rol (asignar permisos a un rol):**  
  **Admin tenant** y **SuperAdmin**.  
  El encargado es el **administrador del cliente** (Admin tenant); SuperAdmin puede hacer lo mismo en cualquier cliente.

- **Pantalla “Catálogo de permisos” (crear/editar/desactivar permisos del sistema):**  
  Solo **SuperAdmin** (si se ofrece esta gestión).  
  El encargado es el **administrador de la plataforma**, no el del cliente.

Para un buen diseño UX/UI:

- Mostrar “Permisos de negocio” (asignar a roles) en el **flujo de Roles** o en **Configuración / Seguridad** del tenant, visible para **Admin tenant** y SuperAdmin.
- Mostrar “Catálogo de permisos” (si existe) solo en un área **SuperAdmin** (ej. Configuración global o “Permisos del sistema”), no en el menú normal del tenant.

---

## 3. Dónde colocar la administración en el menú (UX/UI)

### 3.1 Opción recomendada: dentro de “Roles”

- **Ruta sugerida:** Seguridad (o Administración) → **Roles** → al editar/ver un rol, pestaña o sección **“Permisos de negocio”** (o “Permisos API”).
- **Flujo:** Lista de roles → elegir rol → en el detalle del rol, dos bloques (o pestañas):
  - **Permisos de menú** (actual): qué menús ve y qué puede hacer en cada uno.
  - **Permisos de negocio (nuevo):** checklist o selector múltiple de permisos del catálogo (ej. `admin.usuario.leer`, `mfg.orden_produccion.crear`) que se asignan a ese rol.
- **Ventaja:** El usuario entiende que “un rol tiene permisos de menú y permisos de negocio”; todo está en un solo lugar por rol.

### 3.2 Alternativa: sección “Permisos” separada

- **Ruta:** Seguridad → **Permisos** → sub-opción “Permisos por rol” o “Asignar permisos a roles”.
- Misma idea: elegir rol y luego marcar/desmarcar permisos de negocio para ese rol.

### 3.3 Quién ve qué en el menú

- **Admin tenant:** Ve “Roles” (y dentro, permisos de menú y permisos de negocio). **No** ve “Catálogo de permisos” (solo SuperAdmin, si se implementa).
- **SuperAdmin:** Ve lo mismo que Admin tenant en el tenant actual y, además, puede ver “Catálogo de permisos” en un área global (por ejemplo bajo “Configuración sistema” o “SuperAdmin”).
- **Usuario normal:** No ve pantallas de administración de roles ni de permisos.

Recomendación: usar el **mismo ítem de menú “Roles”** para ambos (Admin tenant y SuperAdmin) y, dentro del detalle de un rol, mostrar siempre la sección “Permisos de negocio” si el usuario tiene permiso `admin.rol.leer` (y `admin.rol.actualizar` para guardar). Así evitas duplicar entradas y aclaras que los permisos de negocio son “de este rol”.

---

## 4. Flujos de pantalla sugeridos

### 4.1 Asignar permisos de negocio a un rol (Admin tenant / SuperAdmin)

1. Usuario entra a **Roles** (lista de roles del tenant).
2. Elige un rol (ej. “Vendedor”) y abre el detalle o “Editar”.
3. En el detalle del rol ve:
   - Datos del rol (nombre, descripción, etc.).
   - **Permisos de menú** (actual): matriz o lista menú ↔ acciones (ver, crear, editar, eliminar).
   - **Permisos de negocio:** lista de permisos disponibles (catálogo) con checkbox o switch por permiso; los asignados al rol aparecen marcados.
4. Marca/desmarca permisos de negocio y pulsa “Guardar”.
5. El frontend llama a `PUT /api/v1/roles/{rol_id}/permisos-negocio/` con la lista de `permiso_id` (o `codigo`) que debe tener el rol.

Texto corto para la UI:

- Título de sección: **“Permisos de negocio (API)”** o **“Permisos que protegen el sistema”**.
- Descripción: “Estos permisos definen qué acciones puede realizar este rol en el sistema (usuarios, reportes, producción, etc.). Los permisos de menú definen qué pantallas ve.”

### 4.2 Catálogo de permisos (solo SuperAdmin, si se implementa)

1. Menú global / SuperAdmin → “Catálogo de permisos” o “Permisos del sistema”.
2. Lista de permisos: `codigo`, `nombre`, `recurso`, `accion`, `es_activo`.
3. Crear / editar / desactivar permisos (alta/baja en el sistema, no por tenant).

---

## 5. API necesaria para el frontend

### 5.1 Endpoints que ya existen (roles y permisos de menú)

- **Listar roles del tenant:** `GET /api/v1/roles/` (paginado) y `GET /api/v1/roles/all-active/`.
- **Detalle de un rol:** `GET /api/v1/roles/{rol_id}/`.
- **Permisos de menú de un rol:**  
  - `GET /api/v1/roles/{rol_id}/permisos/` → permisos **menú** (rol_menu_permiso).  
  - `PUT /api/v1/roles/{rol_id}/permisos/` → actualizar permisos **menú** (payload según PermisoUpdatePayload actual).

Esos endpoints siguen siendo para **permisos de menú**, no para permisos de negocio (RBAC).

### 5.2 Endpoints de permisos de negocio (RBAC) — Implementados

Base URL de la API: **`/api/v1`**. Todas las peticiones requieren cabecera **`Authorization: Bearer <token>`**.

---

#### A) Catálogo de permisos (solo lectura para Admin tenant)

| Método | Path | Descripción |
|--------|------|-------------|
| **GET** | `/api/v1/permisos-catalogo/` | Lista permisos del catálogo **filtrados por los módulos habilitados del tenant** (`cliente_modulo`). |

**Headers:** `Authorization: Bearer <access_token>`

**Autorización:** Rol **Administrador** y permiso **`admin.rol.leer`**. SuperAdmin siempre.

**Filtro por tenant:** La lista devuelta solo incluye:
- Permisos **admin.*** y **modulos.*** (siempre visibles).
- Permisos cuyo prefijo coincide con el **código** de un módulo activo en `cliente_modulo` para el cliente del usuario (ej. si el tenant tiene ORG y LOG, verá permisos `org.*` y `log.*`; no verá `mfg.*`, `bi.*`, etc.).

**Respuesta:** `200 OK` — Array de objetos permiso.

**Esquema de cada ítem:**

| Campo        | Tipo     | Descripción |
|-------------|----------|-------------|
| `permiso_id`| UUID     | ID único del permiso. |
| `codigo`    | string   | Código único (ej. `admin.usuario.leer`). |
| `nombre`    | string \| null | Nombre legible. |
| `descripcion` | string \| null | Descripción del permiso. |
| `recurso`   | string \| null | Recurso asociado. |
| `accion`    | string \| null | Acción asociada. |
| `modulo_id` | UUID \| null | ID del módulo si aplica. |
| `es_activo` | boolean  | Siempre `true` en esta lista (solo activos). |

**Ejemplo de respuesta:**

```json
[
  {
    "permiso_id": "550e8400-e29b-41d4-a716-446655440000",
    "codigo": "admin.usuario.leer",
    "nombre": "Leer usuarios",
    "descripcion": "Listar y ver usuarios",
    "recurso": "usuario",
    "accion": "leer",
    "modulo_id": null,
    "es_activo": true
  },
  {
    "permiso_id": "550e8400-e29b-41d4-a716-446655440001",
    "codigo": "mfg.orden_produccion.crear",
    "nombre": "Crear órdenes de producción",
    "descripcion": null,
    "recurso": "orden_produccion",
    "accion": "crear",
    "modulo_id": "660e8400-e29b-41d4-a716-446655440002",
    "es_activo": true
  }
]
```

**Uso en frontend:** Rellenar la lista/checklist de “Permisos de negocio” al editar un rol. Mostrar `nombre` y opcionalmente `codigo`; usar `permiso_id` para el body del PUT.

**Códigos de error:** `401 Unauthorized`, `403 Forbidden`, `500 Internal Server Error`.

---

#### B) Permisos de negocio asignados a un rol

| Método | Path | Descripción |
|--------|------|-------------|
| **GET** | `/api/v1/roles/{rol_id}/permisos-negocio/` | Devuelve los permisos de negocio asignados al rol. |
| **PUT** | `/api/v1/roles/{rol_id}/permisos-negocio/` | Reemplaza la asignación de permisos de negocio del rol. |

**Headers:** `Authorization: Bearer <access_token>`

**Path parameters:** `rol_id` (UUID) — ID del rol.

**Autorización:**
- **GET:** Rol Administrador y permiso **`admin.rol.leer`**.
- **PUT:** Rol Administrador y permiso **`admin.rol.actualizar`**.

En ambos casos el rol debe pertenecer al tenant del usuario, o ser rol del sistema (el admin del tenant puede leer/editar permisos de negocio del rol "Administrador" global para su propio cliente).

---

**GET /api/v1/roles/{rol_id}/permisos-negocio/**

**Respuesta:** `200 OK` — Objeto con `rol_id` y lista `permisos` (los que **ya tiene asignados** ese rol para el cliente del usuario).

**Importante para la UI:** El frontend debe marcar como **checked** exactamente los permisos cuyo `permiso_id` aparezca en `response.permisos`. Si no se hace esta asociación, la pantalla mostrará todos desmarcados aunque en BD estén asignados.

**Esquema:**

| Campo      | Tipo     | Descripción |
|-----------|----------|-------------|
| `rol_id`  | UUID     | ID del rol. |
| `permisos`| array    | Lista de permisos asignados. |

Cada elemento de `permisos`:

| Campo       | Tipo   | Descripción |
|------------|--------|-------------|
| `permiso_id` | UUID | ID del permiso. |
| `codigo`   | string | Código del permiso. |
| `nombre`   | string \| null | Nombre legible. |

**Ejemplo de respuesta:**

```json
{
  "rol_id": "770e8400-e29b-41d4-a716-446655440003",
  "permisos": [
    {
      "permiso_id": "550e8400-e29b-41d4-a716-446655440000",
      "codigo": "admin.usuario.leer",
      "nombre": "Leer usuarios"
    },
    {
      "permiso_id": "550e8400-e29b-41d4-a716-446655440001",
      "codigo": "mfg.orden_produccion.crear",
      "nombre": "Crear órdenes de producción"
    }
  ]
}
```

**Códigos de error:** `404 Rol no encontrado`, `403 El rol no pertenece a su cliente`, `401`, `500`.

---

**PUT /api/v1/roles/{rol_id}/permisos-negocio/**

**Body (JSON):**

| Campo         | Tipo       | Descripción |
|---------------|------------|-------------|
| `permiso_ids` | array UUID | Lista de IDs de permisos a asignar. Reemplaza la asignación actual. Lista vacía `[]` para quitar todos. |

**Ejemplo de body:**

```json
{
  "permiso_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440001"
  ]
}
```

**Respuesta:** `204 No Content` (sin cuerpo).

**Códigos de error:** `400 Bad Request` (validación), `404 Rol no encontrado`, `403 El rol no pertenece a su cliente`, `422 Unprocessable Entity` (esquema body), `401`, `500`.

---

Con estos tres endpoints el frontend puede:
1. Cargar el catálogo completo con **GET /api/v1/permisos-catalogo/** (lista de permisos con checkbox).
2. Cargar los permisos **ya asignados** al rol con **GET /api/v1/roles/{rol_id}/permisos-negocio/** y marcar como **checked** los que aparezcan en `response.permisos` (por `permiso_id`). Si no se hace este paso, todos aparecerán desmarcados aunque en BD estén asignados.
3. Guardar cambios con **PUT /api/v1/roles/{rol_id}/permisos-negocio/** (body `{ "permiso_ids": [ ... ] }`). El backend **reemplaza** la asignación: borra las filas actuales de `rol_permiso` para ese rol y cliente e **inserta** una fila por cada `permiso_id` enviado. Por tanto, al habilitar un permiso nuevo se inserta el registro en `rol_permiso`; al desmarcar, se elimina.

### 5.3 Usuario actual y permisos

- **GET** `/api/v1/auth/me/` (o el endpoint que devuelva el usuario actual con sus roles y permisos).
  - El objeto usuario debe incluir **`permisos`**: lista de códigos de permiso de negocio (ej. `["admin.usuario.leer", "mfg.orden_produccion.crear"]`).
  - Así el frontend puede ocultar o deshabilitar acciones según `usuario.permisos` (y opcionalmente mostrar la misma lista en “Mi perfil” o “Mis permisos”).

---

## 6. Resumen para diseño UX/UI

| Pregunta | Respuesta |
|----------|-----------|
| **¿Quién administra la asignación de permisos de negocio a roles?** | **Admin tenant** (y SuperAdmin en cualquier tenant). El “encargado” en la empresa es el administrador del cliente. |
| **¿Quién administra el catálogo global de permisos (crear/editar permisos del sistema)?** | Solo **SuperAdmin** (si se implementa esa pantalla). |
| **¿Dónde poner la pantalla “Permisos de negocio”?** | Dentro del **detalle de un rol** (pestaña o sección “Permisos de negocio” o “Permisos API”), junto a “Permisos de menú”. |
| **¿Quién ve la opción “Permisos de negocio” en el menú?** | Quien tenga acceso a **Roles** (Admin tenant y SuperAdmin). No hace falta un ítem de menú aparte; va dentro de Roles. |
| **¿Cómo no confundir con permisos de menú?** | Usar dos bloques o pestañas claras: “Permisos de menú” (qué ve en el menú) y “Permisos de negocio” (qué puede hacer en el sistema). Etiquetar bien y reutilizar los mismos términos que en esta doc. |
| **¿Qué API usar para permisos de negocio?** | `GET /api/v1/permisos-catalogo/`, `GET /api/v1/roles/{rol_id}/permisos-negocio/`, `PUT /api/v1/roles/{rol_id}/permisos-negocio/`. Detalle en sección 5.2. |

Con esto puedes diseñar e implementar en el frontend la administración de permisos RBAC (permisos de negocio) con un encargado claro por pantalla y una UX coherente con el modelo del backend.

---

## 7. Estado de los endpoints de permisos de negocio

| Endpoint | Estado | Notas |
|----------|--------|--------|
| `GET /api/v1/permisos-catalogo/` | **Implementado** | Lista catálogo `permiso` (BD central). Requiere `admin.rol.leer`. |
| `GET /api/v1/roles/{rol_id}/permisos-negocio/` | **Implementado** | Lista permisos asignados al rol (`rol_permiso`). Requiere `admin.rol.leer`. |
| `PUT /api/v1/roles/{rol_id}/permisos-negocio/` | **Implementado** | Asigna/reemplaza permisos del rol. Body: `{ "permiso_ids": [ ... ] }`. Requiere `admin.rol.actualizar`. |
| `GET /api/v1/auth/me/` (o equivalente) con `permisos` | **Implementado** | El usuario ya incluye `permisos: string[]` (códigos). |

El backend expone los tres endpoints anteriores. La documentación detallada (método, path, headers, body, esquemas de respuesta y ejemplos) está en la **sección 5.2** de este documento.
