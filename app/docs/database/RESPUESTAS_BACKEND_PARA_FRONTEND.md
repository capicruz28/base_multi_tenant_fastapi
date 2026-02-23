# Respuestas del backend para la auditoría de frontend

Este documento responde las preguntas que el frontend necesita para resolver los riesgos identificados en su auditoría (login/tenant, API central vs tenant, permisos).

---

## Riesgo 1 – Login y tenant

### ¿El login exige subdominio o cliente_id en el body, o el tenant se deduce del Host (u otro)?

**El tenant se deduce del Host. No se envía en el body.**

- El backend **no** exige `subdominio` ni `cliente_id` en el body del login.
- El login usa **solo** el estándar OAuth2: `application/x-www-form-urlencoded` con:
  - `username` (string): nombre de usuario o email.
  - `password` (string): contraseña.

El tenant se resuelve así:

1. **Middleware:** antes del login, el `TenantMiddleware` lee el header **Host** (ej. `acme.midominio.com`, `techcorp.app.local`).
2. Se extrae el **subdominio** (ej. `acme`, `techcorp`).
3. Con ese subdominio se busca en BD el `cliente_id` y se establece el contexto del tenant para toda la request.

Por tanto, el frontend debe:

- Llamar al login **siempre contra la URL del tenant** (mismo host que la app).
- Ejemplos:
  - App en `https://acme.midominio.com` → login a `https://acme.midominio.com/api/v1/auth/login/`.
  - App en `http://techcorp.app.local:5173` → API en `http://techcorp.app.local:8000` → login a `http://techcorp.app.local:8000/api/v1/auth/login/`.

No hay que mandar en el body ningún campo extra de tenant. Si el Host no tiene un subdominio válido (o no está en BD), el backend responde 401 con mensaje tipo: *"Cliente ID no disponible. El subdominio no pudo ser resuelto por el middleware."*.

**Resumen:**

| Pregunta                         | Respuesta                                                                 |
|----------------------------------|---------------------------------------------------------------------------|
| ¿Subdominio o cliente_id en body?| **No.** No enviar ni `subdominio` ni `cliente_id` en el body.            |
| ¿Nombre y formato del campo?     | **N/A.** Solo body: `username` + `password` (form-urlencoded).          |
| ¿Cómo se determina el tenant?    | Por el **Host** de la request (subdominio → `cliente_id` en backend).   |

---

## Riesgos 3 y 4 – API central vs tenant y permisos

### ¿Qué endpoints son “siempre central” y cuáles en on‑premise/hybrid deben ir al servidor del cliente?

En este backend **no hay dos bases URL distintas** (central vs tenant) para el frontend.

- **Una sola base URL por tenant:** la que corresponde al subdominio (o al servidor del cliente en on‑premise).
- **Todos** los endpoints que el frontend usa (auth, roles, permisos, menús, usuarios, etc.) se llaman **a esa misma base URL**.
- El backend decide por dentro si usa BD central (shared) o BD del cliente (dedicated) según el `cliente_id` ya resuelto por el Host.

Por tanto:

- **Auth (login, refresh, logout, /me):** misma URL del tenant. No hay “API central” separada para auth.
- **Roles:** `GET/POST /api/v1/roles/`, `GET/PUT/DELETE /api/v1/roles/{id}/`, etc. → misma URL del tenant.
- **Permisos:** `GET/PUT /api/v1/permisos/roles/{rol_id}/permisos/`, etc. → misma URL del tenant.
- **Menús:** `GET /api/v1/menus/getmenu/`, `GET /api/v1/menus/all-structured/`, etc. → misma URL del tenant.

En **on‑premise/hybrid**: el frontend apunta al servidor del cliente (ej. `https://api.cliente-acme.com`). Esa misma base URL sirve para auth, roles, permisos y menús; no hay que cambiar de “central” a “tenant” según el endpoint.

**Resumen:**

| Tipo de despliegue | Base URL que usa el frontend | Auth, roles, permisos, menús |
|--------------------|------------------------------|------------------------------|
| Cloud (multi-tenant) | `https://{subdominio}.midominio.com` (ej. acme, techcorp) | Todos en esa misma URL |
| On‑premise / híbrido | URL del servidor del cliente (ej. `https://api.cliente.com`) | Todos en esa misma URL |

No existe un conjunto de endpoints “solo central” que el frontend deba llamar a otra base URL; lo “central” es interno al backend (BD y routing).

---

### ¿/roles/{id}/permisos/ y menús viven en central, en el servidor del tenant o en ambos?

- **Lógicamente:** viven “en el tenant” (datos del cliente).
- **Para el frontend:** tanto roles/permisos como menús se **consumen desde la misma API** que ya es la del tenant (misma base URL que el login).
- **En el backend:**  
  - En modelo **shared (single-DB)** los datos están en la BD central, filtrados por `cliente_id`.  
  - En modelo **dedicated** los datos están en la BD del cliente.  
  El backend enruta solo; el frontend no distingue y no debe cambiar de URL.

**Rutas concretas:**

- **Permisos de un rol:**  
  - `GET /api/v1/roles/{rol_id}/permisos/`  
  - `PUT /api/v1/roles/{rol_id}/permisos/`  
  (y variantes bajo `/permisos/roles/...` según el router).
- **Menú del usuario:**  
  - `GET /api/v1/menus/getmenu/`  
- **Menú completo (admin):**  
  - `GET /api/v1/menus/all-structured/`

Todas esas rutas se llaman a la **misma base URL** que el login (Host del tenant o URL del servidor del cliente en on‑premise).

---

### ¿Existe algo tipo GET /auth/me/permisos/ que debería entregar al frontend para resolver riesgos 3 y 4?

**No existe hoy un endpoint `GET /auth/me/permisos/`.**

Lo que sí existe:

1. **`GET /api/v1/auth/me/`**  
   Devuelve el usuario actual con:
   - `usuario_id`, `cliente_id`, `nombre_usuario`, roles (nombres), `access_level`, `is_super_admin`, `user_type`, `modulos_activos`, `cliente` (info del tenant), etc.  
   **No** incluye la lista de permisos por menú (puede_ver, puede_editar, etc.).

2. **`GET /api/v1/menus/getmenu/`**  
   Devuelve el árbol de menús **ya filtrado** por permisos del usuario (solo ítems que puede ver).  
   Los ítems del árbol (`MenuItem`) **no incluyen** en la respuesta actual los flags de permiso por ítem (`puede_editar`, `puede_eliminar`, `puede_exportar`, etc.), aunque el SP interno sí los calcula.

Para que el frontend pueda:

- Mostrar/ocultar botones (editar, eliminar, exportar, etc.) por pantalla, y  
- Resolver bien los riesgos 3 y 4 sin adivinar permisos,

el backend podría:

**Opción A (recomendada):** Añadir **`GET /api/v1/auth/me/permisos/`** que devuelva algo como:

```json
{
  "permisos_por_menu": {
    "menu-uuid-1": {
      "puede_ver": true,
      "puede_crear": false,
      "puede_editar": true,
      "puede_eliminar": false,
      "puede_exportar": true,
      "puede_imprimir": false,
      "puede_aprobar": false
    }
  }
}
```

(por cada `menu_id` al que el usuario tiene al menos un permiso).

**Opción B:** Extender la respuesta de **`GET /api/v1/menus/getmenu/`** para que cada `MenuItem` incluya esos mismos flags (`puede_ver`, `puede_editar`, etc.) y el frontend los use desde ahí.

Con una de estas dos (o ambas), el frontend puede implementar la resolución de permisos por menú/pantalla de forma clara y alineada con el backend.

---

## Resumen rápido para el frontend

| Tema | Respuesta |
|------|-----------|
| **Login y tenant** | Tenant por **Host** (subdominio). Body solo `username` + `password`. No enviar `cliente_id` ni `subdominio` en el body. |
| **Base URL** | Una sola base URL por tenant (o por servidor en on‑premise). Auth, roles, permisos y menús van todos a esa URL. |
| **Roles y permisos** | Misma API del tenant: `/api/v1/roles/`, `/api/v1/roles/{id}/permisos/`, `/api/v1/permisos/...`. |
| **Menús** | Misma API del tenant: `/api/v1/menus/getmenu/`, `/api/v1/menus/all-structured/`. |
| **Permisos del usuario actual** | No hay `GET /auth/me/permisos/`. Recomendado añadirlo (o incluir permisos por ítem en `getmenu/`) para que el frontend resuelva riesgos 3 y 4. |

Si quieres, en un siguiente paso se puede bajar al detalle del contrato (schemas) de `GET /auth/me/permisos/` o de la extensión de `getmenu/` con permisos por ítem.

---

## Respuestas en formato del documento de requisitos del frontend

Esta sección responde **en el mismo formato** del documento «Requisitos al backend para correcciones críticas (frontend)» para poder pasar la respuesta tal cual al equipo de frontend.

---

### 1. Login multi-tenant: identificación del cliente

**Preguntas:**

1. ¿El backend **exige** hoy en día `cliente_id` o `subdominio` en el body del login para multi-tenant?
   - [ ] Sí, es obligatorio (sin uno de los dos el login falla o no sabe el tenant).
   - [x] **No; el tenant se deduce de otra forma (header `Host`, subdominio en la URL).**

2. Si debe ir en el body, indicar:
   - **No aplica.** El backend no requiere `subdominio` ni `cliente_id` en el body. Body solo: `username` (string) y `password` (string), form-urlencoded.

3. En entornos con subdominio (ej. `acme.tuapp.com`), ¿el backend espera que el frontend envíe ese subdominio en el login o lo infiere del `Host` de la petición?
   - **Lo infiere del `Host`.** El frontend no debe enviar el subdominio en el body. Debe llamar al login contra la URL del tenant (ej. `https://acme.tuapp.com/api/v1/auth/login/`); el backend obtiene el subdominio del header `Host` y resuelve el `cliente_id` internamente.

**Acción frontend según respuesta:**  
No es necesario enviar `subdominio` ni `cliente_id` en el body. Basta con que el frontend use como base URL de la API la misma del tenant (subdominio en la URL o `servidor_api_local` en on-premise). El backend deduce el tenant por el `Host` de cada petición.

---

### 2. Endpoints: servidor central vs servidor del tenant

**Modelo del backend:** No hay dos “servidores” distintos que el frontend deba elegir por tipo de endpoint. Hay **una sola base URL por tenant**: en cloud es la URL del subdominio; en on-premise/híbrido es la URL del servidor del cliente (`servidor_api_local` o equivalente). **Todos** los endpoints (auth, roles, permisos, menús, branding, negocio) se llaman a esa misma base URL.

Tabla respondida:

| Endpoint(s) / grupo | ¿Siempre central? | ¿Puede ir a servidor local del cliente? |
|---------------------|--------------------|----------------------------------------|
| `POST /auth/login/`, `POST /auth/refresh/`, `POST /auth/logout/`, `GET /auth/me/` | No hay “solo central”. Van a la **misma URL del tenant** (subdominio en cloud, o servidor local en on-premise). | **Sí.** En on-premise/híbrido la base URL del tenant **es** el servidor local; auth se llama ahí. |
| `GET /roles/{rol_id}/permisos/` (y resto de roles/permisos) | Misma URL del tenant (no hay servidor central separado). | **Sí.** Misma base URL que auth; en on-premise es el servidor local. |
| `GET /menus/getmenu/`, `GET /modulos-menus/usuario/{id}/`, y resto de menús | Misma URL del tenant. | **Sí.** Idem. |
| Branding del tenant (ej. `GET/POST` sobre configuración del cliente) | Misma URL del tenant. | **Sí.** Idem. |
| Resto de APIs de negocio (planillas, reportes, etc.) | Misma URL del tenant. | **Sí.** Idem. |

**Convención backend:**  
- No existe “siempre central” en el sentido de otra base URL: la única base URL que usa el frontend es la del tenant (subdominio o `servidor_api_local`).  
- En on-premise/híbrido, **todos** los endpoints pueden (y deben) ir al servidor local del cliente, porque esa es la única base URL del tenant en ese despliegue.

**Acción frontend:**  
Refactorizar para usar una única base URL por tenant (`getApiInstance(clienteInfo)` o equivalente). En cloud = URL del subdominio; en on-premise = `servidor_api_local`. No hace falta bifurcar por tipo de endpoint (auth vs menús vs permisos).

---

### 3. Permisos granulares (`GET /roles/{rol_id}/permisos/`)

**Preguntas:**

1. En instalación **on-premise**: ¿ese endpoint existe en el servidor local del cliente o solo en el servidor central?  
   - **Existe en la misma API del tenant.** En on-premise esa API es el servidor local; no hay “central” separado. Por tanto el endpoint se llama al servidor local del cliente (misma base URL que login/me/menús).

2. Si solo existiera en central: ¿el JWT o la cookie llevan suficiente contexto para que el central devuelva permisos del tenant correcto?  
   - **No aplica** con el modelo actual: el endpoint va a la misma URL del tenant y el JWT ya incluye `cliente_id`; el backend usa ese contexto para devolver los permisos del tenant correcto.

3. ¿Existe o se planea un endpoint tipo `GET /auth/me/permisos/` que devuelva todos los permisos del usuario actual en una sola llamada?  
   - **No existe hoy.** Está recomendado añadirlo (o extender `GET /menus/getmenu/` con flags de permiso por ítem) para que el frontend no tenga que hacer N llamadas por rol. Cuando exista, se documentará aquí.

**Acción frontend según respuesta:**  
- Usar la misma instancia de API del tenant (subdominio o servidor local) para `GET /roles/{rol_id}/permisos/`; no hace falta llamar a un “central” distinto.  
- Mientras no exista `GET /auth/me/permisos/`, seguir usando los permisos por rol (o, si el backend extiende `getmenu/` con permisos por ítem, usar eso para botones por pantalla).

---

### Resumen de respuestas esperadas (checklist)

| # | Tema | Respuesta |
|---|------|-----------|
| 1 | **Login** | Tenant por **Host**; no enviar `subdominio` ni `cliente_id` en el body. Body solo: `username`, `password` (form-urlencoded). |
| 2 | **Central vs tenant** | Una sola base URL por tenant. Todos los endpoints (auth, roles, permisos, menús, branding, negocio) van a esa URL. En on-premise esa URL es el servidor local. |
| 3 | **Permisos** | `GET /roles/{id}/permisos/` se llama a la misma API del tenant (servidor local en on-premise). No existe aún `GET /auth/me/permisos/`; recomendado para una sola llamada. |
