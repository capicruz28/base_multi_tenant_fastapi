# Documentación Frontend — Módulo ORG (Organización)

Documento para que el equipo frontend implemente el consumo del módulo **ORG** (Organización) del backend. Incluye base URL, autenticación, endpoints, schemas y ejemplos.

---

## 1. Base URL y autenticación

- **Base URL:** La misma que el login (tenant por Host). Ejemplo: `https://acme.tudominio.com` o `http://localhost:8000` en desarrollo.
- **Prefijo API:** Todas las rutas ORG están bajo `/api/v1/org/`.
- **Autenticación:** Todas las peticiones requieren **Bearer token** en el header:
  ```http
  Authorization: Bearer <access_token>
  ```
- **Tenant:** No se envía `cliente_id` ni `subdominio` en el body. El backend obtiene el tenant del token (y del Host en el login). El frontend solo debe llamar a la URL del tenant y enviar el token.

---

## 2. Endpoints del módulo ORG

Todos los endpoints exigen usuario autenticado. Los datos devueltos/creados pertenecen siempre al tenant del usuario.

### Empresa

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/org/empresa` | Listar empresas del tenant |
| GET | `/api/v1/org/empresa/{empresa_id}` | Detalle de una empresa |
| POST | `/api/v1/org/empresa` | Crear empresa |
| PUT | `/api/v1/org/empresa/{empresa_id}` | Actualizar empresa |
| DELETE | `/api/v1/org/empresa/{empresa_id}` | Eliminar (baja lógica, marca `es_activo = false`) |
| POST | `/api/v1/org/empresa/{empresa_id}/reactivar` | Reactivar empresa (marca `es_activo = true`) |

**Query params (GET list):**  
- `solo_activos` (opcional, boolean, default `true`)  
- `buscar` (opcional, string) — filtra por `codigo_empresa` o `razon_social`

---

### Catálogos globales (solo lectura para ORG)

ORG ya **no administra monedas**. La moneda base se elige desde el catálogo global `cat_moneda`.
Los catálogos de ubigeo (país/departamento/provincia/distrito) también se consumen desde endpoints globales.

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/catalogos/monedas` | Listar `cat_moneda` (para seleccionar `moneda_base_id`) |
| GET | `/api/v1/catalogos/paises` | Listar `cat_pais` |
| GET | `/api/v1/catalogos/departamentos?pais_id=...` | Listar `cat_departamento` |
| GET | `/api/v1/catalogos/provincias?departamento_id=...` | Listar `cat_provincia` |
| GET | `/api/v1/catalogos/distritos?provincia_id=...` | Listar `cat_distrito` |

**Administración (solo Superadmin):**  
Los CRUD viven en `/api/v1/catalogos-globales/*` y se exponen en el panel `/super-admin/*` (ver seed `6.- SEED_ADMIN_MENU.sql`).

---

### Sucursales

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/org/sucursales` | Listar sucursales |
| GET | `/api/v1/org/sucursales/{sucursal_id}` | Detalle sucursal |
| POST | `/api/v1/org/sucursales` | Crear sucursal |
| PUT | `/api/v1/org/sucursales/{sucursal_id}` | Actualizar sucursal |
| DELETE | `/api/v1/org/sucursales/{sucursal_id}` | Eliminar (baja lógica, `es_activo = false`) |

**Query params (GET list):**  
- `empresa_id` (opcional, UUID) — Filtrar por empresa  
- `solo_activos` (opcional, boolean, default `true`)  
- `buscar` (opcional, string) — filtra por código o nombre

---

### Centros de costo

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/org/centros-costo` | Listar centros de costo |
| GET | `/api/v1/org/centros-costo/{centro_costo_id}` | Detalle centro de costo |
| POST | `/api/v1/org/centros-costo` | Crear centro de costo |
| PUT | `/api/v1/org/centros-costo/{centro_costo_id}` | Actualizar centro de costo |
| DELETE | `/api/v1/org/centros-costo/{centro_costo_id}` | Eliminar (baja lógica, `es_activo = false`) |

**Query params (GET list):**  
- `empresa_id` (opcional, UUID)  
- `solo_activos` (opcional, boolean, default `true`)  
- `buscar` (opcional, string) — filtra por código o nombre

---

### Departamentos

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/org/departamentos` | Listar departamentos |
| GET | `/api/v1/org/departamentos/{departamento_id}` | Detalle departamento |
| POST | `/api/v1/org/departamentos` | Crear departamento |
| PUT | `/api/v1/org/departamentos/{departamento_id}` | Actualizar departamento |
| DELETE | `/api/v1/org/departamentos/{departamento_id}` | Eliminar (baja lógica, `es_activo = false`) |

**Query params (GET list):**  
- `empresa_id` (opcional, UUID)  
- `solo_activos` (opcional, boolean, default `true`)  
- `buscar` (opcional, string) — filtra por código o nombre

---

### Cargos

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/org/cargos` | Listar cargos |
| GET | `/api/v1/org/cargos/{cargo_id}` | Detalle cargo |
| POST | `/api/v1/org/cargos` | Crear cargo |
| PUT | `/api/v1/org/cargos/{cargo_id}` | Actualizar cargo |
| DELETE | `/api/v1/org/cargos/{cargo_id}` | Eliminar (baja lógica, `es_activo = false`) |

**Query params (GET list):**  
- `empresa_id` (opcional, UUID)  
- `solo_activos` (opcional, boolean, default `true`)  
- `buscar` (opcional, string) — filtra por código o nombre

---

### Parámetros del sistema

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/org/parametros` | Listar parámetros |
| GET | `/api/v1/org/parametros/{parametro_id}` | Detalle parámetro |
| POST | `/api/v1/org/parametros` | Crear parámetro |
| PUT | `/api/v1/org/parametros/{parametro_id}` | Actualizar parámetro |
| DELETE | `/api/v1/org/parametros/{parametro_id}` | Eliminar (baja lógica, `es_activo = false`) |

**Query params (GET list):**  
- `empresa_id` (opcional, UUID)  
- `modulo_codigo` (opcional, string) — Ej: `"ORG"`, `"INV"`  
- `solo_activos` (opcional, boolean, default `true`)  
- `buscar` (opcional, string) — filtra por módulo, código o nombre de parámetro

---

## 3. Schemas (tipos para frontend)

Los IDs son **UUID** (string). Las fechas vienen en ISO 8601 (ej. `"2025-02-18T10:00:00"`).

### Empresa

**Crear (POST):**  
- Obligatorios: `codigo_empresa`, `razon_social`, `ruc`  
- Opcionales: `nombre_comercial`, `tipo_documento_tributario`, `direccion_fiscal`, `pais`, `departamento`, `provincia`, `distrito`, `telefono_principal`, `email_principal`, `moneda_base_id` (UUID de moneda del catálogo), `maneja_multimoneda` (boolean), `zona_horaria`, `es_activo`, etc.  
- **No enviar:** `cliente_id` ni `empresa_id` (el backend los asigna).

**Actualizar (PUT):**  
- Todos los campos opcionales; solo enviar los que se modifican. Incluye `moneda_base_id` y `maneja_multimoneda` para configurar multi-moneda.

**Respuesta (Read):**  
- `empresa_id`, `cliente_id`, `codigo_empresa`, `razon_social`, `nombre_comercial`, `ruc`, `tipo_documento_tributario`, `direccion_fiscal`, `pais`, `departamento`, `provincia`, `distrito`, `telefono_principal`, `email_principal`, `moneda_base_id`, `maneja_multimoneda`, `zona_horaria`, `es_activo`, `fecha_creacion`, `fecha_actualizacion`.

---

### Moneda

**Crear (POST):**  
- Obligatorios: `empresa_id`, `codigo`, `nombre`, `simbolo`  
- Opcionales: `decimales` (default 2), `es_moneda_base` (default false), `es_activo` (default true).  

**Actualizar (PUT):**  
- Todos opcionales; solo enviar los que se modifican.

**Respuesta (Read):**  
- `moneda_id`, `cliente_id`, `empresa_id`, `codigo`, `nombre`, `simbolo`, `decimales`, `es_moneda_base`, `es_activo`, `fecha_creacion`.

---

### Sucursal

**Crear (POST):**  
- Obligatorios: `empresa_id`, `codigo`, `nombre`  
- Opcionales: `descripcion`, `tipo_sucursal`, `direccion`, `pais_id`, `departamento_id`, `provincia_id`, `distrito_id`, `telefono`, `email`, `es_casa_matriz`, `es_punto_venta`, `es_almacen`, `responsable_nombre`, `centro_costo_id`, `es_activo`, etc.

**Respuesta (Read):**  
- `sucursal_id`, `cliente_id`, `empresa_id`, `codigo`, `nombre`, `descripcion`, `tipo_sucursal`, `direccion`, `pais_id`, `departamento_id`, `provincia_id`, `distrito_id`, `telefono`, `email`, `es_casa_matriz`, `es_punto_venta`, `es_almacen`, `es_activo`, `fecha_creacion`, etc.

---

### Centro de costo

**Crear (POST):**  
- Obligatorios: `empresa_id`, `codigo`, `nombre`, `tipo_centro_costo`  
- Opcionales: `descripcion`, `centro_costo_padre_id`, `nivel`, `categoria`, `tiene_presupuesto`, `permite_imputacion_directa`, `responsable_nombre`, `es_activo`, etc.

---

### Departamento

**Crear (POST):**  
- Obligatorios: `empresa_id`, `codigo`, `nombre`  
- Opcionales: `descripcion`, `departamento_padre_id`, `nivel`, `tipo_departamento`, `jefe_nombre`, `centro_costo_id`, `sucursal_id`, `es_activo`.

---

### Cargo

**Crear (POST):**  
- Obligatorios: `empresa_id`, `codigo`, `nombre`  
- Opcionales: `descripcion`, `nivel_jerarquico`, `categoria`, `area_funcional`, `departamento_id`, `cargo_jefe_id`, `rango_salarial_min`, `rango_salarial_max`, `moneda_salarial`, `es_activo`, etc.

---

### Parámetro

**Crear (POST):**  
- Obligatorios: `modulo_codigo`, `codigo_parametro`, `nombre_parametro`, `tipo_dato`  
- Opcionales: `empresa_id`, `descripcion`, `valor_texto`, `valor_numerico`, `valor_booleano`, `valor_fecha`, `valor_json`, `valor_defecto`, `es_editable`, `es_obligatorio`, `es_activo`.

---

## 4. Ejemplos de request/response

### Listar empresas

```http
GET /api/v1/org/empresa?solo_activos=true
Authorization: Bearer <token>
```

**Respuesta 200:**  
```json
[
  {
    "empresa_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "cliente_id": "11111111-1111-1111-1111-111111111111",
    "codigo_empresa": "EMP01",
    "razon_social": "Mi Empresa S.A.C.",
    "nombre_comercial": "Mi Empresa",
    "ruc": "20123456789",
    "direccion_fiscal": "Av. Principal 123",
    "pais": "Perú",
    "departamento": "Lima",
    "provincia": "Lima",
    "distrito": "Miraflores",
    "telefono_principal": "014567890",
    "email_principal": "contacto@miempresa.com",
    "moneda_base_id": "<UUID de cat_moneda>",
    "maneja_multimoneda": false,
    "zona_horaria": "America/Lima",
    "es_activo": true,
    "fecha_creacion": "2025-02-18T10:00:00",
    "fecha_actualizacion": null
  }
]
```

### Crear empresa

```http
POST /api/v1/org/empresa
Authorization: Bearer <token>
Content-Type: application/json

{
  "codigo_empresa": "EMP01",
  "razon_social": "Mi Empresa S.A.C.",
  "nombre_comercial": "Mi Empresa",
  "ruc": "20123456789",
  "direccion_fiscal": "Av. Principal 123",
  "pais": "Perú",
  "departamento": "Lima",
  "provincia": "Lima",
  "distrito": "Miraflores",
  "telefono_principal": "014567890",
  "email_principal": "contacto@miempresa.com",
  "moneda_base_id": "<UUID de cat_moneda>",
  "maneja_multimoneda": false,
  "zona_horaria": "America/Lima",
  "es_activo": true
}
```

**Respuesta 201:**  
Objeto completo de empresa (mismo formato que un ítem de la lista), incluyendo `empresa_id` y `cliente_id` asignados por el backend.

### Crear sucursal

```http
POST /api/v1/org/sucursales
Authorization: Bearer <token>
Content-Type: application/json

{
  "empresa_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "codigo": "SUC01",
  "nombre": "Casa Matriz",
  "tipo_sucursal": "sede",
  "direccion": "Av. Principal 123",
  "es_casa_matriz": true,
  "es_activo": true
}
```

---

## 5. Códigos de error

| Código | Significado |
|--------|-------------|
| 401 | No autenticado o token inválido/expirado. Incluir header `Authorization: Bearer <token>` o renovar token. |
| 403 | Sin permiso para el tenant o recurso. |
| 404 | Recurso no encontrado (ej. empresa_id o sucursal_id inexistente o de otro tenant). |
| 422 | Error de validación (campos requeridos faltantes o formato incorrecto). |
| 500 | Error interno del servidor. |

En 404 el body suele ser: `{"detail": "Empresa no encontrada"}` (o mensaje equivalente por recurso).

---

## 6. Rutas del menú (SPA)

Para construir el menú lateral del módulo ORG (según `MENU_NAVEGACION.md` y seed de menú), usar estas rutas en el frontend:

| Opción de menú | Ruta SPA sugerida |
|----------------|-------------------|
| Mi Empresa | `/org/empresa` |
| Sucursales | `/org/sucursales` |
| Departamentos | `/org/departamentos` |
| Cargos | `/org/cargos` |
| Centros de Costo | `/org/centros-costo` |
| Parámetros del Sistema | `/org/parametros` |

El backend ya expone estas rutas en `modulo_menu` (script `SEED_MODULO_MENU_COMPLETO.sql`). El menú dinámico se puede obtener con `GET /api/v1/menus/getmenu/` (filtrado por permisos del usuario).

---

## 7. Flujo recomendado para la implementación

1. **Login** con la URL del tenant y guardar el `access_token`.
2. **Obtener menú** con `GET /api/v1/menus/getmenu/` para mostrar solo las opciones ORG a las que el usuario tiene acceso.
3. **Pantalla Mi Empresa:**  
   - Listar: `GET /api/v1/org/empresa`.  
   - Si hay una sola empresa, redirigir o mostrar directamente el detalle.  
   - Crear: `POST /api/v1/org/empresa` (si el tenant no tiene empresa).  
   - Editar: `PUT /api/v1/org/empresa/{empresa_id}`.  
   - Para **moneda base**: enviar `moneda_base_id` (UUID de la moneda elegida del catálogo).  
   - Para **multi-moneda**: enviar `maneja_multimoneda: true/false`.
4. **Pantalla Sucursales:**  
   - Listar: `GET /api/v1/org/sucursales` (opcional: `?empresa_id=...`).  
   - Crear: `POST /api/v1/org/sucursales` (incluir `empresa_id`).  
   - Editar: `PUT /api/v1/org/sucursales/{sucursal_id}`.
5. **Resto de pantallas (Departamentos, Cargos, Centros de costo, Parámetros):**  
   - Mismo patrón: GET list, GET by id, POST, PUT.  
   - En listados, usar `empresa_id` en query cuando la pantalla esté asociada a una empresa seleccionada.
6. **Selectores:**  
   - Para “Empresa” en formularios de Sucursal, Departamento, Cargo o Centro de costo, poblar con `GET /api/v1/org/empresa`.  
   - Para “Moneda base” en Mi Empresa, poblar con `GET /api/v1/catalogos/monedas`.

---

## 8. Resumen de archivos de referencia

- **Plan de implementación backend:** `app/docs/database/PLAN_IMPLEMENTACION_MODULOS_ERP.md`
- **Estructura de módulos ERP:** `app/docs/database/ESTRUCTURA_MODULOS_ERP.md`
- **Login y tenant (riesgos 1, 3 y 4):** `app/docs/database/RESPUESTAS_BACKEND_PARA_FRONTEND.md`
- **Seed del menú (modulo, modulo_seccion, modulo_menu):** `app/docs/database/SEED_MODULO_MENU_COMPLETO.sql`

Si necesitan tipos TypeScript/Interfaces generados a partir de los schemas, se pueden derivar de las secciones 3 y 4 de este documento o del OpenAPI (`/docs` o `/openapi.json`) del backend.
