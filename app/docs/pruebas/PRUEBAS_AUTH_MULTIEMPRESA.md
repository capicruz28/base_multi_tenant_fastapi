# Guía de pruebas manuales — Auth multi-empresa (Bloques 1–6)

Verificación manual vía **Swagger UI** de login, JWT, refresh y filtrado de permisos por `empresa_id`.

**Swagger:** `http://localhost:8000/docs` (Docker: puerto `8000` del `docker-compose`).

**Tenant de prueba recomendado:** cliente **ACME** (`subdominio = acme`, `cliente_id = 11111111-1111-1111-1111-111111111111`).

---

## 0. Configuración previa (obligatoria)

### 0.1 Resolver el tenant en desarrollo

El login **no** recibe `cliente_id` en el body. El `TenantMiddleware` resuelve el cliente desde el **subdominio** (`acme` → `BASE_DOMAIN=app.local`).

En **Swagger**, cada request debe incluir el header:

| Header | Valor (ACME) |
|--------|----------------|
| `Origin` | `http://acme.app.local:8000` |

> Alternativa: `Referer: http://acme.app.local:8000/docs`  
> En producción solo se usa `Host`; en `ENVIRONMENT=development` se acepta `Origin`/`Referer` cuando `Host` es `localhost`.

**Comprobar resolución de tenant** (opcional):

```sql
SELECT cliente_id, subdominio, es_activo
FROM cliente
WHERE subdominio = 'acme';
```

Resultado esperado: `cliente_id = 11111111-1111-1111-1111-111111111111`, `es_activo = 1`.

### 0.2 Headers comunes en todos los escenarios

| Header | Valor | Cuándo |
|--------|--------|--------|
| `Origin` | `http://acme.app.local:8000` | Siempre en login/refresh/permissions |
| `X-Client-Type` | `mobile` | Recomendado: refresh en JSON (Swagger no gestiona bien cookies) |
| `X-Client-Type` | `web` | Solo si prueba cookie HttpOnly (navegador externo) |
| `Authorization` | `Bearer <access_token>` | Después del login (escenarios 4 y 5) |
| `Content-Type` | `application/x-www-form-urlencoded` | Solo en `POST /login/` |

### 0.3 Decodificar el JWT (payload)

1. Copiar `access_token` o `selection_token` de la respuesta.
2. Pegar en [jwt.io](https://jwt.io) (solo payload; no hace falta la clave para leer claims).
3. Verificar claims relevantes:

| Claim | Escenario 1 | Escenario 2 | Escenario 3 |
|-------|-------------|-------------|-------------|
| `empresa_id` | UUID string presente | **ausente** | **ausente** (selection token) |
| `es_admin_cliente` | `false` (usuario normal) | `true` | según rol |
| `empresa_selection_pending` | ausente | ausente | `true` (solo selection token) |
| `cliente_id` | UUID del tenant | UUID del tenant | UUID del tenant |
| `sub` | nombre de usuario | nombre de usuario | nombre de usuario |

### 0.4 Base de datos

- BD según `.env.docker`: típicamente `bd_sistema` (ajustar `USE` en los scripts).
- Tablas clave: `org_empresa`, `usuario`, `usuario_rol`, `rol`, `refresh_tokens`, `permiso`, `rol_permiso`.
- El seed base (`2.- SEED_BD_CENTRAL.sql`) **no** trae `empresa_id` en `usuario_rol` ni empresas ORG: hay que ejecutar el **setup SQL** de cada escenario antes de probar.

### 0.5 Usuarios de referencia (ACME, contraseñas del seed)

| Usuario | Contraseña | Uso sugerido |
|---------|------------|--------------|
| `user` | `user123` | Escenario 1 (tras setup una empresa) |
| `admin` | `admin123` | Escenario 2 (tras setup admin sin empresa) |
| `multi_emp` | `Test123!` | Escenario 3 (crear en setup) |
| `perm_test` | `Test123!` | Escenario 5 (crear en setup) |

---

## Escenario 1 — Login usuario normal con una sola empresa

### Objetivo

- JWT incluye `empresa_id`.
- JWT incluye `es_admin_cliente` (esperado `false`).
- `refresh_tokens.empresa_id` persistido en BD.

### 1.A Setup SQL (ejecutar una vez)

```sql
USE bd_sistema;  -- ajustar nombre de BD
GO

DECLARE @cliente_id UNIQUEIDENTIFIER = '11111111-1111-1111-1111-111111111111';
DECLARE @empresa_id UNIQUEIDENTIFIER = 'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA';
DECLARE @usuario_id UNIQUEIDENTIFIER = '11111111-1111-1111-1111-111111111300'; -- user@acme
DECLARE @rol_user_id UNIQUEIDENTIFIER = '11111111-1111-1111-1111-111111111130';

-- Empresa única
IF NOT EXISTS (SELECT 1 FROM org_empresa WHERE empresa_id = @empresa_id)
INSERT INTO org_empresa (
    empresa_id, cliente_id, codigo_empresa, razon_social, ruc, es_activo
) VALUES (
    @empresa_id, @cliente_id, 'EMP-A', 'ACME Empresa Lima', '20123456701', 1
);

-- Rol sin flag admin cliente
UPDATE rol SET es_admin_cliente = 0 WHERE rol_id = @rol_user_id;

-- Una sola asignación con empresa
DELETE FROM usuario_rol
WHERE usuario_id = @usuario_id AND cliente_id = @cliente_id;

INSERT INTO usuario_rol (usuario_rol_id, usuario_id, rol_id, cliente_id, empresa_id, es_activo)
VALUES (NEWID(), @usuario_id, @rol_user_id, @cliente_id, @empresa_id, 1);

-- Default alineado (evita selección multi-empresa)
UPDATE usuario
SET empresa_default_id = @empresa_id
WHERE usuario_id = @usuario_id AND cliente_id = @cliente_id;
```

**Verificación previa:**

```sql
SELECT ur.empresa_id, r.es_admin_cliente, u.empresa_default_id
FROM usuario_rol ur
INNER JOIN rol r ON r.rol_id = ur.rol_id
INNER JOIN usuario u ON u.usuario_id = ur.usuario_id
WHERE ur.usuario_id = '11111111-1111-1111-1111-111111111300'
  AND ur.cliente_id = '11111111-1111-1111-1111-111111111111'
  AND ur.es_activo = 1;
```

Esperado: **1 fila**, `empresa_id = AAAAAAAA-...`, `es_admin_cliente = 0`.

### 1.B Request Swagger

| Campo | Valor |
|-------|--------|
| **Método y URL** | `POST /api/v1/auth/login/` |
| **Headers** | `Origin: http://acme.app.local:8000` |
| | `X-Client-Type: mobile` |
| **Body** (`application/x-www-form-urlencoded`) | |

```
username=user
password=user123
grant_type=password
```

### 1.C Response — qué verificar

| Campo | Valor esperado |
|-------|----------------|
| HTTP status | `200` |
| Tipo de schema | `Token` (no `LoginEmpresaSelectionResponse`) |
| `access_token` | Presente (JWT) |
| `token_type` | `"bearer"` |
| `refresh_token` | Presente (porque `X-Client-Type: mobile`) |
| `user_data.empresa_activa` | `"AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA"` |
| `user_data.es_admin_cliente` | `false` |
| `requiere_seleccion_empresa` | **No debe aparecer** (no es ese modelo) |

**JWT (decodificar `access_token`):**

| Claim | Esperado |
|-------|----------|
| `empresa_id` | `"AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA"` |
| `es_admin_cliente` | `false` |

### 1.D SQL — `refresh_tokens` tras login

Sustituir `<HASH_NO_APLICA>`: la API guarda **hash**, no el JWT en claro. Filtrar por usuario y el registro más reciente:

```sql
SELECT TOP 1
    rt.token_id,
    rt.cliente_id,
    rt.usuario_id,
    rt.empresa_id,
    rt.is_revoked,
    rt.expires_at,
    rt.created_at,
    rt.client_type
FROM refresh_tokens rt
WHERE rt.usuario_id = '11111111-1111-1111-1111-111111111300'
  AND rt.cliente_id = '11111111-1111-1111-1111-111111111111'
  AND rt.is_revoked = 0
ORDER BY rt.created_at DESC;
```

| Columna | Esperado |
|---------|----------|
| `empresa_id` | `AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA` |
| `client_type` | `mobile` |
| `is_revoked` | `0` |

---

## Escenario 2 — Login admin cliente sin empresa

### Objetivo

- JWT **sin** claim `empresa_id`.
- JWT con `es_admin_cliente = true`.
- Rol en `usuario_rol` con `empresa_id IS NULL`.

### 2.A Setup SQL

```sql
USE bd_sistema;
GO

DECLARE @cliente_id UNIQUEIDENTIFIER = '11111111-1111-1111-1111-111111111111';
DECLARE @usuario_id UNIQUEIDENTIFIER = '11111111-1111-1111-1111-111111111100'; -- admin@acme
DECLARE @rol_admin_id UNIQUEIDENTIFIER = '11111111-1111-1111-1111-111111111110';

UPDATE rol
SET es_admin_cliente = 1
WHERE rol_id = @rol_admin_id;

-- Sin empresas en roles (solo asignación global)
DELETE FROM usuario_rol
WHERE usuario_id = @usuario_id AND cliente_id = @cliente_id;

INSERT INTO usuario_rol (usuario_rol_id, usuario_id, rol_id, cliente_id, empresa_id, es_activo)
VALUES (NEWID(), @usuario_id, @rol_admin_id, @cliente_id, NULL, 1);

-- Sin empresas ORG asignadas al usuario
-- (no insertar filas usuario_rol con empresa_id NOT NULL para este usuario)
```

**Verificación previa:**

```sql
SELECT ur.empresa_id, r.es_admin_cliente, COUNT(*) OVER() AS filas
FROM usuario_rol ur
INNER JOIN rol r ON r.rol_id = ur.rol_id
WHERE ur.usuario_id = '11111111-1111-1111-1111-111111111100'
  AND ur.cliente_id = '11111111-1111-1111-1111-111111111111'
  AND ur.es_activo = 1;
```

Esperado: `empresa_id IS NULL`, `es_admin_cliente = 1`.

### 2.B Request Swagger

| Campo | Valor |
|-------|--------|
| **Método y URL** | `POST /api/v1/auth/login/` |
| **Headers** | `Origin: http://acme.app.local:8000`, `X-Client-Type: mobile` |
| **Body** | `username=admin` / `password=admin123` / `grant_type=password` |

### 2.C Response — qué verificar

| Campo | Esperado |
|-------|----------|
| HTTP status | `200` |
| Schema | `Token` |
| `user_data.es_admin_cliente` | `true` |
| `user_data.empresa_activa` | **ausente** o `null` |

**JWT:**

| Claim | Esperado |
|-------|----------|
| `empresa_id` | **No presente** en el payload |
| `es_admin_cliente` | `true` |

### 2.D SQL — refresh token (opcional)

```sql
SELECT TOP 1 empresa_id, is_revoked, created_at
FROM refresh_tokens
WHERE usuario_id = '11111111-1111-1111-1111-111111111100'
  AND cliente_id = '11111111-1111-1111-1111-111111111111'
ORDER BY created_at DESC;
```

Esperado: `empresa_id IS NULL`.

---

## Escenario 3 — Múltiples empresas sin `empresa_default_id`

### Objetivo

- Respuesta tipo `LoginEmpresaSelectionResponse`.
- Lista `empresas_disponibles` con ≥ 2 UUIDs.
- **Sin** `refresh_token` ni cookie de refresh.

### 3.A Setup SQL

```sql
USE bd_sistema;
GO

DECLARE @cliente_id UNIQUEIDENTIFIER = '11111111-1111-1111-1111-111111111111';
DECLARE @empresa_a UNIQUEIDENTIFIER = 'BBBBBBBB-BBBB-BBBB-BBBB-BBBBBBBBBBBB';
DECLARE @empresa_b UNIQUEIDENTIFIER = 'CCCCCCCC-CCCC-CCCC-CCCC-CCCCCCCCCCCC';
DECLARE @usuario_id UNIQUEIDENTIFIER = 'EEEEEEEE-EEEE-EEEE-EEEE-EEEEEEEEEEEE';
DECLARE @rol_user_id UNIQUEIDENTIFIER = '11111111-1111-1111-1111-111111111130';

-- Empresas
IF NOT EXISTS (SELECT 1 FROM org_empresa WHERE empresa_id = @empresa_a)
INSERT INTO org_empresa (empresa_id, cliente_id, codigo_empresa, razon_social, ruc, es_activo)
VALUES (@empresa_a, @cliente_id, 'EMP-B', 'ACME Norte', '20123456702', 1);

IF NOT EXISTS (SELECT 1 FROM org_empresa WHERE empresa_id = @empresa_b)
INSERT INTO org_empresa (empresa_id, cliente_id, codigo_empresa, razon_social, ruc, es_activo)
VALUES (@empresa_b, @cliente_id, 'EMP-C', 'ACME Sur', '20123456703', 1);

-- Usuario de prueba
IF NOT EXISTS (SELECT 1 FROM usuario WHERE usuario_id = @usuario_id)
INSERT INTO usuario (
    usuario_id, cliente_id, nombre_usuario, contrasena,
    nombre, apellido, correo, es_activo, correo_confirmado, empresa_default_id
) VALUES (
    @usuario_id, @cliente_id, 'multi_emp',
    '$2b$12$6J/bWiSYNFHFblxoVot4Je2HyWGU.QyFxtPdpsAMP2hz4fGid5WQu', -- admin123
    'Multi', 'Empresa', 'multi@acme.com', 1, 1,
    @empresa_a  -- valor temporal; se anula abajo
);

-- Sin default efectivo (requiere_seleccion)
UPDATE usuario SET empresa_default_id = NULL
WHERE usuario_id = @usuario_id;

-- Si la columna es NOT NULL en su BD, ejecutar antes:
-- ALTER TABLE usuario ALTER COLUMN empresa_default_id UNIQUEIDENTIFIER NULL;

UPDATE rol SET es_admin_cliente = 0 WHERE rol_id = @rol_user_id;

DELETE FROM usuario_rol WHERE usuario_id = @usuario_id AND cliente_id = @cliente_id;

INSERT INTO usuario_rol (usuario_rol_id, usuario_id, rol_id, cliente_id, empresa_id, es_activo)
VALUES
    (NEWID(), @usuario_id, @rol_user_id, @cliente_id, @empresa_a, 1),
    (NEWID(), @usuario_id, @rol_user_id, @cliente_id, @empresa_b, 1);
```

**Verificación previa:**

```sql
SELECT COUNT(DISTINCT ur.empresa_id) AS num_empresas, u.empresa_default_id
FROM usuario u
LEFT JOIN usuario_rol ur ON ur.usuario_id = u.usuario_id
    AND ur.cliente_id = u.cliente_id AND ur.es_activo = 1 AND ur.empresa_id IS NOT NULL
WHERE u.nombre_usuario = 'multi_emp'
  AND u.cliente_id = '11111111-1111-1111-1111-111111111111'
GROUP BY u.empresa_default_id;
```

Esperado: `num_empresas = 2`, `empresa_default_id IS NULL`.

### 3.B Request Swagger

| Campo | Valor |
|-------|--------|
| **Método y URL** | `POST /api/v1/auth/login/` |
| **Headers** | `Origin: http://acme.app.local:8000`, `X-Client-Type: mobile` |
| **Body** | `username=multi_emp` / `password=admin123` / `grant_type=password` |

### 3.C Response — qué verificar

| Campo | Esperado |
|-------|----------|
| HTTP status | `200` |
| `requiere_seleccion_empresa` | `true` |
| `empresas_disponibles` | Array con **2** UUIDs: `BBBBBBBB-...` y `CCCCCCCC-...` (orden puede variar) |
| `selection_token` | JWT presente |
| `token_type` | `"bearer"` |
| `access_token` | **No debe existir** en este schema |
| `refresh_token` | **No debe existir** (mobile) |

**JWT (`selection_token`):**

| Claim | Esperado |
|-------|----------|
| `empresa_selection_pending` | `true` |
| `empresa_id` | ausente |
| `cliente_id` | UUID ACME |

### 3.D SQL — no debe crearse refresh

```sql
SELECT COUNT(*) AS tokens_recientes
FROM refresh_tokens
WHERE usuario_id = 'EEEEEEEE-EEEE-EEEE-EEEE-EEEEEEEEEEEE'
  AND created_at > DATEADD(MINUTE, -5, GETDATE());
```

Esperado: `tokens_recientes = 0` inmediatamente después del login de selección.

---

## Escenario 4 — Refresh token

### Objetivo

- Tras refresh, el nuevo access JWT mantiene el mismo `empresa_id`.
- El nuevo registro en `refresh_tokens` conserva `empresa_id`.

**Prerrequisito:** completar **Escenario 1** y conservar el `refresh_token` de la respuesta (modo `mobile`).

### 4.A Request Swagger — refresh

| Campo | Valor |
|-------|--------|
| **Método y URL** | `POST /api/v1/auth/refresh/` |
| **Headers** | `Origin: http://acme.app.local:8000` |
| | `X-Client-Type: mobile` |
| **Body** (`application/json`) | |

```json
{
  "refresh_token": "<PEGAR_refresh_token_DEL_ESCENARIO_1>"
}
```

> **Web (`X-Client-Type: web`):** no enviar body; el refresh se lee de la cookie `refresh_token`. Swagger no persiste cookies entre requests — usar **mobile** para esta prueba.

### 4.B Response — qué verificar

| Campo | Esperado |
|-------|----------|
| HTTP status | `200` |
| `access_token` | Nuevo JWT (distinto al anterior) |
| `refresh_token` | Nuevo string (rotación) |
| `token_type` | `"bearer"` |

**JWT nuevo (`access_token`):**

| Claim | Esperado |
|-------|----------|
| `empresa_id` | `"AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA"` (igual que antes del refresh) |
| `es_admin_cliente` | `false` |
| `sub` | `"user"` |

### 4.C SQL — rotación y `empresa_id`

```sql
-- Últimos 2 tokens del usuario (rotación: el anterior debería quedar revocado)
SELECT TOP 2
    token_id,
    empresa_id,
    is_revoked,
    created_at,
    revoked_at
FROM refresh_tokens
WHERE usuario_id = '11111111-1111-1111-1111-111111111300'
  AND cliente_id = '11111111-1111-1111-1111-111111111111'
ORDER BY created_at DESC;
```

| Fila | Esperado |
|------|----------|
| Más reciente (`TOP 1`) | `empresa_id = AAAAAAAA-...`, `is_revoked = 0` |
| Anterior (`TOP 2`) | `is_revoked = 1` (si la rotación revocó el token previo) |

---

## Escenario 5 — Permisos filtrados por `empresa_id`

### Objetivo

Con token de **empresa A**, `GET /auth/permissions/me` no debe incluir permisos exclusivos de **empresa B**.

### 5.A Setup SQL

Usa dos códigos de permiso distintos existentes en `permiso`. Ejemplo (ajustar si no existen en su BD):

```sql
USE bd_sistema;
GO

DECLARE @cliente_id UNIQUEIDENTIFIER = '11111111-1111-1111-1111-111111111111';
DECLARE @empresa_a UNIQUEIDENTIFIER = 'DDDDDDDD-DDDD-DDDD-DDDD-DDDDDDDDDDDD';
DECLARE @empresa_b UNIQUEIDENTIFIER = 'FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF';
DECLARE @usuario_id UNIQUEIDENTIFIER = '99999999-9999-9999-9999-999999999999';
DECLARE @rol_a_id UNIQUEIDENTIFIER = '11111111-1111-1111-1111-111111111120'; -- MANAGER
DECLARE @rol_b_id UNIQUEIDENTIFIER = '11111111-1111-1111-1111-111111111130'; -- USER

-- Obtener dos permisos distintos (anotar codigo y permiso_id)
SELECT TOP 2 permiso_id, codigo
FROM permiso
WHERE es_activo = 1
ORDER BY codigo;
-- Ejemplo anotado:
DECLARE @perm_a_id UNIQUEIDENTIFIER = '<permiso_id_1>';
DECLARE @perm_b_id UNIQUEIDENTIFIER = '<permiso_id_2>';
-- DECLARE @codigo_a NVARCHAR(100) = '<codigo_1>';
-- DECLARE @codigo_b NVARCHAR(100) = '<codigo_2>';

-- Empresas
IF NOT EXISTS (SELECT 1 FROM org_empresa WHERE empresa_id = @empresa_a)
INSERT INTO org_empresa (empresa_id, cliente_id, codigo_empresa, razon_social, ruc, es_activo)
VALUES (@empresa_a, @cliente_id, 'EMP-D', 'ACME Perm A', '20123456704', 1);

IF NOT EXISTS (SELECT 1 FROM org_empresa WHERE empresa_id = @empresa_b)
INSERT INTO org_empresa (empresa_id, cliente_id, codigo_empresa, razon_social, ruc, es_activo)
VALUES (@empresa_b, @cliente_id, 'EMP-E', 'ACME Perm B', '20123456705', 1);

-- Usuario
IF NOT EXISTS (SELECT 1 FROM usuario WHERE usuario_id = @usuario_id)
INSERT INTO usuario (
    usuario_id, cliente_id, nombre_usuario, contrasena,
    nombre, apellido, correo, es_activo, correo_confirmado, empresa_default_id
) VALUES (
    @usuario_id, @cliente_id, 'perm_test',
    '$2b$12$6J/bWiSYNFHFblxoVot4Je2HyWGU.QyFxtPdpsAMP2hz4fGid5WQu',
    'Perm', 'Test', 'perm@acme.com', 1, 1, @empresa_a
);

UPDATE rol SET es_admin_cliente = 0 WHERE rol_id IN (@rol_a_id, @rol_b_id);

-- Solo permiso A al rol MANAGER, solo permiso B al rol USER (limpiar y reasignar)
DELETE FROM rol_permiso
WHERE cliente_id = @cliente_id AND rol_id IN (@rol_a_id, @rol_b_id);

INSERT INTO rol_permiso (rol_permiso_id, cliente_id, rol_id, permiso_id)
VALUES (NEWID(), @cliente_id, @rol_a_id, @perm_a_id);

INSERT INTO rol_permiso (rol_permiso_id, cliente_id, rol_id, permiso_id)
VALUES (NEWID(), @cliente_id, @rol_b_id, @perm_b_id);

-- Usuario: empresa A -> MANAGER (perm A), empresa B -> USER (perm B)
DELETE FROM usuario_rol WHERE usuario_id = @usuario_id AND cliente_id = @cliente_id;

INSERT INTO usuario_rol (usuario_rol_id, usuario_id, rol_id, cliente_id, empresa_id, es_activo)
VALUES (NEWID(), @usuario_id, @rol_a_id, @cliente_id, @empresa_a, 1);

INSERT INTO usuario_rol (usuario_rol_id, usuario_id, rol_id, cliente_id, empresa_id, es_activo)
VALUES (NEWID(), @usuario_id, @rol_b_id, @cliente_id, @empresa_b, 1);
```

**Verificación previa (permisos por empresa en SQL):**

```sql
DECLARE @usuario_id UNIQUEIDENTIFIER = '99999999-9999-9999-9999-999999999999';
DECLARE @cliente_id UNIQUEIDENTIFIER = '11111111-1111-1111-1111-111111111111';
DECLARE @empresa_a UNIQUEIDENTIFIER = 'DDDDDDDD-DDDD-DDDD-DDDD-DDDDDDDDDDDD';

SELECT DISTINCT p.codigo, ur.empresa_id
FROM usuario_rol ur
INNER JOIN rol_permiso rp ON rp.rol_id = ur.rol_id AND rp.cliente_id = ur.cliente_id
INNER JOIN permiso p ON p.permiso_id = rp.permiso_id
WHERE ur.usuario_id = @usuario_id
  AND ur.cliente_id = @cliente_id
  AND ur.es_activo = 1
  AND (ur.empresa_id IS NULL OR ur.empresa_id = @empresa_a);
```

Anotar `@codigo_a` esperado en el resultado; **no** debe aparecer `@codigo_b`.

> Si `PERMISSION_RESOLVER_CACHE_ENABLED=true`, tras cambiar `rol_permiso` reiniciar Redis o esperar TTL (`PERMISSION_RESOLVER_CACHE_TTL`, default 300 s).

### 5.B Paso 1 — Login en empresa A

| Campo | Valor |
|-------|--------|
| **Método y URL** | `POST /api/v1/auth/login/` |
| **Headers** | `Origin: http://acme.app.local:8000`, `X-Client-Type: mobile` |
| **Body** | `username=perm_test` / `password=admin123` / `grant_type=password` |

Verificar JWT: `empresa_id = "DDDDDDDD-DDDD-DDDD-DDDD-DDDDDDDDDDDD"` (empresa A; con `empresa_default_id` configurado a A, login elige A).

### 5.C Paso 2 — Permisos con token empresa A

| Campo | Valor |
|-------|--------|
| **Método y URL** | `GET /api/v1/auth/permissions/me` |
| **Headers** | `Origin: http://acme.app.local:8000` |
| | `Authorization: Bearer <access_token_empresa_A>` |

**En Swagger:** botón **Authorize** → pegar solo el token (sin prefijo `Bearer` si Swagger lo añade solo).

### 5.D Response — qué verificar

```json
{
  "permissions": ["<codigo_permiso_A>", "..."]
}
```

| Verificación | Esperado |
|--------------|----------|
| `permissions` contiene `<codigo_permiso_A>` | **Sí** |
| `permissions` contiene `<codigo_permiso_B>` | **No** |
| HTTP status | `200` |

### 5.E SQL — referencia cruzada

```sql
-- Permisos efectivos solo para contexto empresa A (misma lógica que el resolver)
DECLARE @usuario_id UNIQUEIDENTIFIER = '99999999-9999-9999-9999-999999999999';
DECLARE @cliente_id UNIQUEIDENTIFIER = '11111111-1111-1111-1111-111111111111';
DECLARE @empresa_a UNIQUEIDENTIFIER = 'DDDDDDDD-DDDD-DDDD-DDDD-DDDDDDDDDDDD';

SELECT DISTINCT p.codigo
FROM usuario_rol ur
INNER JOIN rol_permiso rp ON rp.rol_id = ur.rol_id AND rp.cliente_id = ur.cliente_id
INNER JOIN permiso p ON p.permiso_id = rp.permiso_id AND p.es_activo = 1
WHERE ur.usuario_id = @usuario_id
  AND ur.cliente_id = @cliente_id
  AND ur.es_activo = 1
  AND (ur.empresa_id IS NULL OR ur.empresa_id = @empresa_a)
ORDER BY p.codigo;
```

La lista devuelta por la API debe coincidir con esta query (mismos códigos, sin los de empresa B).

### 5.F Control negativo (opcional)

Repetir login forzando empresa B: `UPDATE usuario SET empresa_default_id = 'FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF' WHERE nombre_usuario = 'perm_test'`, login de nuevo, `GET /permissions/me` debe incluir `<codigo_permiso_B>` y **no** `<codigo_permiso_A>`.

---

## Orden recomendado de ejecución

1. Escenario **1** (base para refresh).
2. Escenario **4** (usa refresh del 1).
3. Escenario **2** (independiente; restaurar datos de `admin` si hace falta).
4. Escenario **3** (usuario `multi_emp` dedicado).
5. Escenario **5** (usuario `perm_test` dedicado).

---

## Checklist rápido (bloques 1–6)

| # | Bloque | Comprobación manual |
|---|--------|---------------------|
| 1 | ORM `refresh_tokens.empresa_id` | SQL escenario 1.D |
| 2 | Resolución empresa en login | Escenarios 1, 2, 3 |
| 3 | Claims JWT | Decodificar tokens en 1, 2, 3 |
| 4 | Filtro roles/permisos | Escenario 5 |
| 5 | Refresh restaura `empresa_id` | Escenario 4 |
| 6 | Expiración `cliente_auth_config` | Opcional: `UPDATE cliente_auth_config SET access_token_minutes = 5 WHERE cliente_id = ...` y comprobar `exp` del JWT (~5 min) |

---

## Problemas frecuentes

| Síntoma | Causa probable | Acción |
|---------|----------------|--------|
| `401` "Cliente ID no disponible" | Falta `Origin` con subdominio | Añadir `Origin: http://acme.app.local:8000` |
| Login sin `empresa_id` en escenario 1 | `usuario_rol` sin `empresa_id` o varias empresas | Re-ejecutar setup 1.A |
| Escenario 3 no pide selección | `empresa_default_id` definido o una sola empresa | SQL 3.A + `empresa_default_id NULL` |
| Refresh `401` en Swagger | Modo web sin cookie | Usar `X-Client-Type: mobile` + body JSON |
| Permisos iguales en A y B | Cache Redis o `rol_permiso` compartido | Limpiar cache / revisar setup 5.A |

---

## Referencias

- Auditoría: `app/docs/auditoria/AUDITORIA_AUTH_LOGIN.md`
- Endpoints: `app/modules/auth/presentation/endpoints.py`
- Resolución empresa: `AuthService.get_empresa_activa_para_login`
- Expiración tenant: `leer_expiracion_tokens_cliente` en `auth_config_service.py`
