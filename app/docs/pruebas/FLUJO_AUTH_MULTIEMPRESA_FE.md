# Flujo auth multi-empresa (contrato FE)

## Pasos

| Paso | Método | Path | Cuándo |
|------|--------|------|--------|
| Login | POST | `/api/v1/auth/login/` | Siempre |
| Selección | POST | `/api/v1/auth/empresa/seleccionar/` | Tras `requiere_seleccion_empresa` |
| Cambio | POST | `/api/v1/auth/empresa/cambiar/` | Usuario operativo con sesión |
| Perfil | GET | `/api/v1/auth/me/` | Bootstrap (incluye `empresa_activa`) |
| Permisos | GET | `/api/v1/auth/permissions/me` | Tras sesión con `empresa_id` |
| Menú | GET | `/api/v1/auth/menu` | Tras sesión con `empresa_id` |

JWT tras sesión completa: `empresa_id` presente salvo admin sin empresa (onboarding); nunca `empresa_selection_pending`.

OpenAPI en vivo: `GET /openapi.json` (incluye schemas `LoginEmpresaSelectionResponse`, `EmpresaIdRequest`, `Token`).

## POST seleccionar

```http
POST /api/v1/auth/empresa/seleccionar/
Authorization: Bearer <selection_token>
Content-Type: application/json
X-Client-Type: web

{"empresa_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"}
```

**200 (login con selección):** solo `selection_token` en raíz (no `access_token`). `user_data` es perfil sin `empresas_disponibles` ni `requiere_seleccion_empresa` (esos van en la raíz del response).

```json
{
  "requiere_seleccion_empresa": true,
  "empresas_disponibles": [
    {
      "empresa_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
      "razon_social": "ACME EMPRESA A",
      "nombre_comercial": "ACME A"
    },
    {
      "empresa_id": "bbbbbbbb-cccc-dddd-eeee-ffffffffffff",
      "razon_social": "ACME EMPRESA B",
      "nombre_comercial": null
    }
  ],
  "selection_token": "eyJ...",
  "token_type": "bearer",
  "user_data": { "...": "..." }
}
```

**200 (sesión completa, web):**

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user_data": {
    "nombre_usuario": "jperez",
    "empresa_activa": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "es_admin_cliente": false,
    "roles": ["Usuario"]
  }
}
```

Refresh en cookie HttpOnly (mismo nombre que login). **409** si el Bearer no es selection token.

## POST cambiar

```http
POST /api/v1/auth/empresa/cambiar/
Authorization: Bearer <access_token_sesion>
Content-Type: application/json
X-Client-Type: mobile

{
  "empresa_id": "bbbbbbbb-cccc-dddd-eeee-ffffffffffff",
  "refresh_token": "<refresh_actual>"
}
```

**200:** mismo shape que seleccionar; nuevo access + refresh (JSON en mobile).

**400:** empresa no asignada. **403:** empresa de otro tenant/inactiva. **409:** token con `empresa_selection_pending`.

## GET /me

Respuesta **plana** (sin `user_data` anidado):

```json
{
  "usuario_id": "550e8400-e29b-41d4-a716-446655440000",
  "nombre_usuario": "admin",
  "correo": "admin@empresa.com",
  "nombre": "Admin",
  "apellido": "Sistema",
  "es_activo": true,
  "roles": ["Administrador"],
  "access_level": 5,
  "is_super_admin": false,
  "user_type": "tenant_admin",
  "cliente_id": "660e8400-e29b-41d4-a716-446655440001",
  "es_admin_cliente": true,
  "empresa_activa": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
  "requiere_seleccion_empresa": false,
  "empresas_disponibles": null
}
```

`access_level`, `user_type` e `is_super_admin` provienen del JWT si están en el token; si no, del usuario cargado.
`empresa_activa` es el `empresa_id` del JWT (`null` si no hay empresa en sesión).
Admin sin `empresa_id` en JWT pero con empresas en `org_empresa`: `requiere_seleccion_empresa: true` y `empresas_disponibles` con `empresa_id`, `razon_social` y `nombre_comercial`.
Con **selection token** → **409** (no usar `/me`; ir a `POST .../empresa/seleccionar/`).

## Breaking changes

Ninguno en login/refresh existentes. Nuevos campos opcionales en `UserDataWithRoles` (`requiere_seleccion_empresa`). Menú y permisos devuelven **409** si se llaman con selection token.
