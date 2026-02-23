# Documentación para frontend: Menú de navegación (sidebar)

Uso correcto del endpoint de menú de navegación para construir el sidebar. Incluye el nuevo **GET /me/** y el comportamiento por tipo de usuario (usuario normal, admin tenant, SuperAdmin).

---

## 1. Endpoint recomendado: GET /me/

**URL:** `GET /api/v1/modulos-menus/me/`

**Uso:** Una sola petición para obtener el árbol completo de menú del **usuario autenticado** en el **tenant actual**. No se envía ningún ID en la URL; el backend usa el token (usuario + tenant).

**Autenticación:** Header `Authorization: Bearer <access_token>` (JWT).

**Respuesta:** `200 OK` con cuerpo en JSON según el esquema siguiente.

### Por qué usar /me/

- No hay que pasar `usuario_id` ni `cliente_id`; se evitan errores y el frontend no depende de tener esos IDs antes de llamar.
- El backend diferencia automáticamente:
  - **Usuario normal:** solo módulos contratados y menús según permisos por rol (`rol_menu_permiso`).
  - **Admin tenant:** usuario con `access_level >= 4` (ej. rol Administrador): ve **todos** los menús de los módulos contratados del tenant con permisos completos, sin depender de filas en `rol_menu_permiso`.
  - **SuperAdmin:** todos los menús de los módulos contratados del tenant con permisos completos.

---

## 2. Esquema de la respuesta (MenuUsuarioResponse)

```ts
// Tipo raíz
interface MenuUsuarioResponse {
  modulos: ModuloMenuResponse[];
}

interface ModuloMenuResponse {
  modulo_id: string;   // UUID
  codigo: string;
  nombre: string;
  icono: string | null;
  color: string;
  categoria: string;
  orden: number;
  secciones: SeccionMenu[];
}

interface SeccionMenu {
  seccion_id: string;  // UUID
  codigo: string;
  nombre: string;
  icono: string | null;
  orden: number;
  menus: MenuItem[];
}

interface MenuItem {
  menu_id: string;     // UUID
  codigo: string | null;
  nombre: string;
  icono: string | null;
  ruta: string | null;  // Ruta de navegación (ej. "/reportes/ventas")
  nivel: number;
  tipo_menu: string;
  orden: number;
  permisos: PermisosMenu;
  submenus: MenuItem[]; // Recursivo
}

interface PermisosMenu {
  ver: boolean;
  crear: boolean;
  editar: boolean;
  eliminar: boolean;
  exportar: boolean;
  imprimir: boolean;
  aprobar: boolean;
}
```

**Ejemplo mínimo de respuesta:**

```json
{
  "modulos": [
    {
      "modulo_id": "uuid-del-modulo",
      "codigo": "ERP",
      "nombre": "ERP",
      "icono": "business",
      "color": "#1976D2",
      "categoria": "operaciones",
      "orden": 1,
      "secciones": [
        {
          "seccion_id": "uuid-seccion",
          "codigo": "VENTAS",
          "nombre": "Ventas",
          "icono": null,
          "orden": 1,
          "menus": [
            {
              "menu_id": "uuid-menu",
              "codigo": "rep-ventas",
              "nombre": "Reporte de ventas",
              "icono": "chart",
              "ruta": "/reportes/ventas",
              "nivel": 1,
              "tipo_menu": "pantalla",
              "orden": 1,
              "permisos": {
                "ver": true,
                "crear": false,
                "editar": false,
                "eliminar": false,
                "exportar": true,
                "imprimir": true,
                "aprobar": false
              },
              "submenus": []
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 3. Comportamiento por tipo de usuario

| Tipo de usuario   | Qué ve en el menú |
|-------------------|-------------------|
| **Usuario normal** | Solo módulos contratados por el tenant y solo menús donde tiene permiso **ver** (según `rol_menu_permiso`). |
| **Admin tenant**   | Usuario con nivel de acceso ≥ 4 (ej. rol Administrador): **todos** los menús de los módulos contratados del tenant, con todos los permisos en `true`. No depende de tener cada menú en `rol_menu_permiso`. |
| **SuperAdmin**     | Todos los menús de los **módulos contratados** del tenant actual, con todos los permisos en `true`. |

En todos los casos el tenant es el del token (Host / contexto); no se puede ver menú de otro tenant.

---

## 4. Uso en el frontend

### 4.1 Cuándo llamar

- Tras el login (o tras obtener el usuario con `GET /auth/me/`), llamar **una vez** a `GET /api/v1/modulos-menus/me/` para construir el sidebar.
- No hace falta pasar `usuario_id` ni `cliente_id`; la base URL del API ya identifica el tenant (subdominio o servidor del cliente).

### 4.2 Ejemplo de petición (fetch)

```js
const response = await fetch(`${API_BASE_URL}/api/v1/modulos-menus/me/`, {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json',
  },
  credentials: 'include', // si usas cookies
});
const menuData = await response.json(); // MenuUsuarioResponse
```

### 4.3 Renderizar el sidebar

- Recorrer `menuData.modulos` → por cada módulo, sus `secciones` → por cada sección, sus `menus`.
- Cada `MenuItem` tiene `ruta` para navegación y `permisos` para mostrar/ocultar botones (crear, editar, eliminar, exportar, etc.).
- Los ítems con `submenus.length > 0` se pueden mostrar como submenú colapsable/expandible.

### 4.4 Errores

- **401 Unauthorized:** Token ausente o inválido. Redirigir a login.
- **500 Internal Server Error:** Error en el servidor. Mostrar mensaje genérico y reintentar o cachear la última respuesta válida si la hay.

---

## 5. Endpoint alternativo (por ID de usuario)

Si en algún flujo de admin necesitas el menú de **otro** usuario (mismo tenant):

**URL:** `GET /api/v1/modulos-menus/usuario/{usuario_id}/`

- Requiere `usuario_id` (UUID) en la URL.
- El tenant sigue siendo el del token.
- Si el solicitante es **SuperAdmin** y `usuario_id` es el **propio** usuario, la respuesta es la misma que con `/me/` (menú completo con permisos totales). En el resto de casos se aplica el filtro por permisos de ese usuario.

Para el **sidebar del usuario actual**, se recomienda usar siempre **GET /me/** y no este endpoint.

---

## 6. Resumen

| Tema | Recomendación |
|------|----------------|
| **Endpoint para el sidebar** | `GET /api/v1/modulos-menus/me/` |
| **Autenticación** | Header `Authorization: Bearer <access_token>` |
| **Parámetros en URL** | Ninguno |
| **Frecuencia** | Una vez por sesión (o tras login); se puede cachear y refrescar al cerrar sesión o cada X minutos. |
| **Estructura** | `modulos[]` → `secciones[]` → `menus[]` (cada menú con `permisos` y `submenus[]`). |
| **Permisos por ítem** | Usar `permisos.ver`, `permisos.editar`, `permisos.eliminar`, etc. para mostrar/ocultar acciones en la UI. |

Con esto el frontend puede consumir el menú de navegación de forma correcta y consistente para usuario normal, admin tenant y SuperAdmin.
